---
title: "Muru: WSGI and ASGI together"
description: "Adding websockets to an existing WSGI application with Muru, by handing requests to ASGI in the same worker, plus mounting ASGI beside WSGI and serving gRPC."
date: 2026-11-11
tags: ["python", "muru", "wsgi", "asgi"]
draft: true
---

The [previous post](/posts/2026/11/muru-https-in-development/) was about serving HTTPS from a development run. This time I want to get back to something I mentioned in passing when I [first talked about Muru](/posts/2026/11/twenty-years-of-mod-wsgi/), which is that it isn't limited to WSGI, and that WSGI and ASGI can be mixed in the one application.

The case where this matters most is an existing WSGI application which now needs websockets. WSGI has no way of doing websockets, so the usual answer is to stand up a separate ASGI server beside the WSGI one, put a proxy in front to route the websocket paths to it, and then work out how the two halves are going to share things like sessions and configuration. The other answer is to port the whole application to ASGI, which for a large application is rarely something anyone wants to do just to get one feature.

With Muru, neither is necessary. The WSGI application can hand a request over to an ASGI application running in the same worker process.

## An existing WSGI application

To show how this works I will use a small Flask application, standing in for an application which has been around for years. The project has Flask installed with `uv add flask`, and the `pyproject.toml` file names the entrypoint:

```toml
[tool.muru]
entrypoint = "shop.app:app"
```

The application itself has the existing page, plus a new `/chat` view where the websocket is to live:

```python
from flask import Flask, request

from shop.chat import chat

app = Flask(__name__)


@app.route("/")
def index():
    return "Welcome to the shop\n"


@app.route("/chat")
def chat_view():
    bridge = request.environ["muru.wsgi_to_asgi"]
    if not bridge.is_websocket:
        return "websocket required\n", 426
    return bridge.handoff(chat)
```

Every WSGI request Muru passes to an application has a `muru.wsgi_to_asgi` object in the WSGI environ. This is the bridge across to the ASGI side. It can say whether the request is a websocket upgrade, and its `handoff()` method continues the request as an ASGI application. What `handoff()` returns is itself a WSGI application producing an empty response, so a Flask view can simply return it. Muru ignores whatever the WSGI side produces after a request has been handed off.

## Websockets as callbacks

What the request is handed off to, `chat`, has to be an ASGI application. You could write that as a raw ASGI coroutine, but if your application is WSGI, the people working on it are probably more at home with synchronous code. For that Muru provides `muru.asgi.websocket.Handler`, an ASGI application which turns the events of a websocket into method calls on an object of your own. Here is a minimal chat room in `shop/chat.py`, where every message received is sent on to everyone connected:

```python
from muru.asgi import websocket


class Chat:
    def __init__(self):
        self.sockets = set()

    def on_connect(self, ws):
        self.sockets.add(ws)

    def on_receive(self, ws, message):
        for peer in list(self.sockets):
            try:
                peer.send(message)
            except websocket.ConnectionClosed:
                self.sockets.discard(peer)

    def on_disconnect(self, ws, code, reason):
        self.sockets.discard(ws)


chat = websocket.Handler(Chat())
```

The methods are called on the worker's application threads, the same threads the WSGI application uses. Calls for any one socket happen one at a time and in order, while different sockets can be handled at the same time. The important part, which I will come back to, is that a socket sitting there waiting for its next message isn't holding on to a thread while it waits.

## Turning handoff on

Start this with `muructl run` and the ordinary page works, but a websocket client connecting to `/chat` is turned away. The access log shows why, with the view having answered with a 426 status:

```
426 GET /chat 19B 0.5ms queue=0.0ms app=0.5ms worker=0 id=01M6JWP0E8W9FQ721K81F9AJ9H
```

Handing requests to ASGI has to be enabled, as it means the worker needs to run an event loop beside its threads. Without the setting, a websocket upgrade is just an ordinary request, so `is_websocket` is false and the view turns it away. Enabling it is one more line in `pyproject.toml`:

```toml
[tool.muru]
entrypoint = "shop.app:app"
handoff = "asgi"
```

Run it again and the start-up output confirms the worker now has an event loop as well as its threads:

```
muru: serving shop.app:app on http://127.0.0.1:8080 with 1 worker of 4 threads and an event loop of concurrency 1000
```

To check the chat room really works, I used a small client written with the `websockets` package, installed into a separate virtual environment, which connects as two users and has each of them say something:

```python
import asyncio

from websockets.asyncio.client import connect

URL = "ws://127.0.0.1:8080/chat"


async def main():
    async with connect(URL) as alice, connect(URL) as bob:
        await alice.send("hello from alice")
        print("alice got:", await alice.recv())
        print("bob got:", await bob.recv())
        await bob.send("hi alice, bob here")
        print("alice got:", await alice.recv())
        print("bob got:", await bob.recv())


asyncio.run(main())
```

Running this the output is:

```
alice got: hello from alice
bob got: hello from alice
alice got: hi alice, bob here
bob got: hi alice, bob here
```

The access log has a line for each websocket when it is accepted, and another when it closes, recording who closed it, how, and how many messages went each way. Both are marked with `handoff=asgi` so you can tell the request was handed across:

```
101 GET /chat 0B 1.8ms queue=0.0ms app=0.5ms worker=0 handoff=asgi id=01M6JWPC691F8KMJB3TQH8CKSK
101 GET /chat 0B 0.3ms queue=0.1ms app=0.2ms worker=0 handoff=asgi id=01M6JWPC6B1F8KMJB3TQH8CKSK
101 GET /chat 34B 1.7ms websocket=closed by=client code=1000 received=1 sent=2 worker=0 handoff=asgi id=01M6JWPC6B1F8KMJB3TQH8CKSK
101 GET /chat 34B 2.9ms websocket=closed by=client code=1000 received=1 sent=2 worker=0 handoff=asgi id=01M6JWPC691F8KMJB3TQH8CKSK
```

## Sockets don't hold threads

The reason this isn't just a party trick is what happens to the thread the WSGI view ran on. Once the view hands the request off and returns, the thread goes back to the pool to handle other requests. The websocket now lives on the worker's event loop, and only borrows a thread for the brief time it takes to run one of the callback methods.

That matters, because this worker only has four threads. If each open websocket tied up a thread, the fifth person to open the chat would stop the rest of the site from responding. To check, I changed the client to open fifty websockets to `/chat`, leave them all open, and then make an ordinary request to the home page:

```
50 websockets open
GET / answered b'Welcome to the shop\n' in 6.2ms
```

Fifty open websockets on a worker with four threads, and the rest of the site carries on as normal.

## Side by side by path

Handing off in code is the right tool when the decision about which side a request goes to belongs in the application, such as wanting the Flask view to check the user is logged in before accepting the websocket. When the decision is simply about the path, Muru can instead mount an ASGI application beside the WSGI one.

Say newer parts of the shop are being written as async code under `/api`. Here is a stand-in for that in `shop/api.py`, where the sleep pretends to be waiting on some other service:

```python
import asyncio
import json


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    await asyncio.sleep(1)  # stand in for waiting on another service

    body = json.dumps({"root_path": scope["root_path"], "path": scope["path"]}).encode()
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": body})
```

Mounting it at `/api` is a table in `pyproject.toml`:

```toml
[tool.muru.mounts.api]
path = "/api"
entrypoint = "shop.api:app"
```

On start-up, Muru says what each entrypoint is being served as, and where each mount is:

```
muru.host[89570]: shop.app:app is served as WSGI
muru.host[89570]: mount api: shop.api:app is served as ASGI
...
muru: mount api serves /api from shop.api:app
```

Anything under `/api` now goes to the ASGI application, and everything else to Flask. The ASGI application sees the mount path as its `root_path`, as the ASGI specification asks:

```
curl http://127.0.0.1:8080/api/orders
```

```
{"root_path": "/api", "path": "/api/orders"}
```

Both applications run in the same worker processes, imported by the same preload, from the one project.

There was one result here which caught me out at first. I fired off twenty requests to `/api` at once, expecting them all to finish in about a second since they were just awaiting a sleep on the event loop. Instead it took five seconds. The reason is that unless told otherwise, an ASGI mount shares the worker's slots for requests with the WSGI application, and that number comes from the four WSGI threads. Twenty requests, four at a time, one second each, is five seconds.

Giving the mount a concurrency of its own fixes that. It also needs the mount explicitly declared as ASGI:

```toml
[tool.muru.mounts.api]
path = "/api"
entrypoint = "shop.api:app"
interface = "asgi"
concurrency = 500
```

With that, the same twenty requests took 1.05 seconds. There is a similar `max_connections` setting to put a limit on how many websockets an ASGI mount can hold open. The sharing is a sensible default, since it means an ASGI mount can't swamp a worker sized for its WSGI application, but it is something to know about.

## And back the other way

Handing off works in the other direction too. An ASGI application can hand a request to WSGI code, which is useful when moving an application to ASGI a piece at a time, leaving the parts not yet converted as they are. In the scope given to an ASGI application, Muru's extensions include an `asgi_to_wsgi` bridge, whose `handoff()` runs a WSGI application for the rest of the request:

```python
def legacy_report(environ, start_response):
    body = f"report generated by WSGI code for {environ['SCRIPT_NAME']}{environ['PATH_INFO']}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [body]


async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    if scope["path"].startswith("/api/reports/"):
        return scope["extensions"]["muru"]["asgi_to_wsgi"].handoff(legacy_report)

    ...
```

As before, this has to be enabled, and if you forget, the error says exactly what to add:

```
muru.HandoffNotEnabled: mount api does not enable handing requests to WSGI; set handoff = "wsgi" on the mount
```

WSGI code needs threads to run on, so as well as setting `handoff`, the mount here is given two threads of its own:

```toml
[tool.muru.mounts.api]
path = "/api"
entrypoint = "shop.api:app"
interface = "asgi"
concurrency = 500
handoff = "wsgi"
threads = 2
```

Now a request for a report goes to the old WSGI code, while everything else under `/api` stays with the ASGI application:

```
curl http://127.0.0.1:8080/api/reports/daily
```

```
report generated by WSGI code for /api/reports/daily
```

with the access log marking it with `handoff=wsgi`:

```
200 GET /api/reports/daily 53B 0.4ms queue=0.0ms app=0.4ms mount=api worker=0 handoff=wsgi id=01M6JWRJ0DQ38194C2WQX2KDCJ
```

## gRPC as well

The same mount mechanism also takes care of the third kind of service I mentioned in the first post, which is gRPC. A gRPC mount doesn't have a path. Instead, calls are recognised by their content type and service name, so gRPC and ordinary HTTP share the same port. The entrypoint is a function which registers the servicers generated by `grpcio-tools`, just as you would with a grpcio server:

```python
class Greeter(greeter_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return greeter_pb2.HelloReply(message=f"Hello {request.name}")


def register(server):
    greeter_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
```

```toml
[tool.muru.mounts.api]
interface = "grpc"
entrypoint = "svc.app:register"
```

```
muru.host[91221]: mount api: svc.app:register is served as gRPC
...
muru: mount api serves the gRPC services of svc.app:register
```

With that, a grpcio client calling `SayHello` and a browser fetching the home page can talk to the same port of the same development run, and both show up in the one access log:

```
200 GET / 30B 0.2ms queue=0.0ms app=0.2ms worker=0 id=01M6JWS8HV7NK43EP3VYEA225P
200 POST /greet.Greeter/SayHello 14B 0.9ms queue=0.0ms app=0.8ms worker=0 id=01M6JWS8KT7NK43EP3VYEA225P
```

One catch is that grpcio doesn't provide wheels for free-threaded Python, so for gRPC I had to use a regular build of Python. There is a lot more to gRPC in Muru, such as streaming calls and gRPC-Web, which I may come back to in a post of its own.

## What's next

What I like about all of this is that you don't have to make a big decision up front. An application can start as WSGI, take websockets when it needs them, grow async parts under a path, and move across to ASGI piece by piece if that ever makes sense, all without becoming more than one deployment.

That wraps up what I wanted to show of Muru in development mode. Next it is time to move on to the daemon, starting with deploying an application to a server, where the releases that a reload creates in development mode become deploys that can run side by side, take a share of the traffic, and be rolled back.
