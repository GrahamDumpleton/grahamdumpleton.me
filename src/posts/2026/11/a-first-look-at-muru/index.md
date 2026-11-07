---
title: "A first look at Muru"
description: "Muru running for the first time, in development mode. Serving a WSGI application, what the terminal tells you, what happens when it fails, and why a reload is a release."
date: 2026-11-05
tags: ["python", "muru", "wsgi"]
---

In my [last post](/posts/2026/11/twenty-years-of-mod-wsgi/) I talked about where Muru came from and what I want it to be, but didn't show it doing anything. Time to fix that.

Muru has three ways of running an application. There is a development mode for when you are working on an application on your own machine, a daemon for hosting applications on a server, and a mode for running an application in a container. The same process model sits underneath all three, so what you see while developing is what you get in production. That makes development mode a good place to start, since it is the simplest of the three and still shows off some of what makes Muru different.

## Installing it

Muru comes as two pieces. The `muructl` command is what you install and interact with. It is a single binary written in Rust, with no Python dependencies of its own. The second piece is `muru`, a runtime library which runs inside your application's Python interpreter. You don't install that one yourself. The first time `muructl` runs an application on a particular Python version, it fetches the matching runtime library into your user cache directory. Nothing gets installed into your project.

The easiest way to install `muructl` is as a tool with `uv`:

```
uv tool install muructl
```

Using `pipx install muructl`, or `pip install muructl` into some environment, works just as well. Muru is still in alpha, with only pre-releases available, and supports Linux and macOS on CPython 3.11 or later, including the free-threaded builds.

For a project to try it with, create a directory with a virtual environment:

```
mkdir hello && cd hello
uv init --bare
uv venv
```

## A first application

Not wanting to complicate things by bringing a web framework into it just yet, we will start with a plain WSGI application. Save this as `app.py`:

```python
def application(environ, start_response):
    body = f"Hello from {environ['PATH_INFO']}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
```

To run it, give `muructl run` the module and the name of the WSGI callable within it:

```
muructl run app:application
```

There is no need to activate the virtual environment first, as `muructl` will find the `.venv` directory in the project by itself. Running this the output is:

```
muru.host[13737]: preloaded app:application in 1 ms
muru.host[13737]: app:application is served as WSGI
muru.host[13737]: worker 0 started as pid 13773
muru.host[13737]: worker 0 (pid 13773) is ready
muru: serving app:application on http://127.0.0.1:8080 with 1 worker of 4 threads
muru: development mode: error pages show tracebacks, nothing is persisted, the run reloads on change and only loopback is served; production runs under the daemon (muructl daemon start)
muru: dashboard on http://127.0.0.1:8081/
muru: admin socket /tmp/muru-501/runs/8080/admin.sock
muru: watching /Users/graham/hello for changes to **/*.py
```

Even with an application this small, there is more going on than you might expect. A host process was started which imported the application once. A worker process was then forked from the host, meaning that it starts out as a copy of the host with the application already loaded. Finally, the edge, which is the part of Muru that accepts HTTP connections, started listening for requests, passing them through to the worker.

Importing the application once and forking workers from it isn't a new idea, but doing it safely is harder than it looks. If importing the application opens a database connection or starts a background thread, that doesn't survive being forked, and what you get are mysterious problems later on. Muru checks for this when it does the import, before any workers are forked. How that check works deserves a post of its own, so I will come back to it.

Note too that development mode only listens on the loopback interface. It is not meant to be exposed to the outside world, which is what the daemon is for.

## What the access log tells you

Open `http://127.0.0.1:8080/hello` in a browser, or use `curl`, and a line is added to the terminal for the request:

```
07:50:49.268 200 GET /hello 18B 0.2ms queue=0.0ms app=0.1ms worker=0 id=01M6JRM25MKE6AS8RXBZ8AS1MG
```

Much of this is what you would expect from any access log, with the status, the method and path, the size of the response, and the total time. The parts which are a bit different are `queue` and `app`. The first is how long the request waited for a worker thread to become free to handle it, and the second is how long your code took.

On a laptop with one user these are tiny numbers and not very interesting. In production they are anything but. A request that takes a long time because your code is slow, and one that takes a long time because every thread was busy and it had to wait its turn, are very different problems. The first means you have code to fix, the second means you don't have enough capacity. If you can't tell the two apart, you will often end up fixing the wrong thing. Being able to see that distinction, right down to individual requests, is a small example of what I meant in the last post about Muru knowing what Python web applications need.

The line also says which worker handled the request, and gives the request a unique id. The same id is returned to the client in an `X-Request-ID` response header, so a response can be matched up to the log line for it. Anything the application prints is likewise tagged with the worker that wrote it, so when there are multiple workers you can tell which output came from where.

## When the application fails

Applications have bugs, so let's add one. Change `app.py` to:

```python
def application(environ, start_response):
    raise RuntimeError("not today")
```

Make a request and, because this is development mode, the error page sent back includes the traceback:

```
500 Internal Server Error
reason: app_error
request id: 01M6JRM54RKE6AS8RXBZ8AS1MG

The application raised an exception.

Traceback (most recent call last):
  File "/Users/graham/hello/app.py", line 2, in application
    raise RuntimeError("not today")
RuntimeError: not today
```

The same traceback appears in the terminal, tagged with the worker, along with an access log line showing the 500 status and `reason=app_error`.

If the client says it wants JSON, as an API client would, it instead gets back an `application/problem+json` response with the same details:

```
curl -H 'Accept: application/json' http://127.0.0.1:8080/
```

```
{"type":"about:blank","title":"Internal Server Error","status":500,"detail":"The application raised an exception.","reason":"app_error","request_id":"01M6JRM553KE6AS8RXBZ8AS1MG","traceback":"Traceback (most recent call last):\n ..."}
```

Either way, the worker itself is fine. An exception raised by your code results in a failed request, but never a dead process.

## Reloading is a release

You may have noticed that I didn't restart anything after changing `app.py`. That is because development mode watches the project directory, and when a `.py` file changes it reloads automatically. This is on by default.

Reloading on code changes is something every development server does, so on its own it isn't remarkable. What is different is how Muru does it. Rather than restarting the worker in place, a reload starts a whole new host and worker beside the existing ones. Only once the new worker is ready is traffic switched across to it, after which the old one is shut down. The terminal shows it happening:

```
muru: reloading, app.py changed
muru.host[13786]: preloaded app:application in 2 ms
muru.host[13786]: app:application is served as WSGI
muru.host[13786]: worker 0 started as pid 13787
muru.host[13786]: worker 0 (pid 13787) is ready
muru: switched to release r2
muru.host[13737]: received SIGTERM, stopping
```

Each set of host and workers is a release, numbered as they are created. Where this gets interesting is when the change you make breaks things badly enough that the application can't even be imported. Add `import nosuchmodule` to the top of `app.py` and save it:

```
muru: reloading, app.py changed
muru.host[13858]: cannot load app:application: ModuleNotFoundError: No module named 'nosuchmodule'
muru: release r3 failed to start: the host exited with exit status: 1 before its workers were ready; release r2 keeps serving
```

The new release failed to start, so traffic never moved to it, and the previous release carried on serving requests the whole time. Fix the code and save again, and the next release starts and takes over. The failed attempt still counts as a release, so this will be `r4`.

In development mode this mostly saves you from staring at a dead server after a typo. The reason I find it worth dwelling on is that it is exactly the same mechanism the daemon uses when deploying a new version of an application to a server. There, a new release starts beside the old one, traffic moves across once it is ready, and if it never becomes ready the old release just keeps serving. That is the basis of zero-downtime deploys in Muru, and of things like blue/green deploys, canaries and rolling back to a previous release. Development mode is giving you a small taste of that every time you save a file.

## Real frameworks

Nothing about this is specific to hand-written WSGI applications. For a Flask application you point `muructl run` at the Flask application object:

```
muructl run app:app
```

and for Django at the WSGI application it already generates for you:

```
DJANGO_SETTINGS_MODULE=mysite.settings muructl run mysite.wsgi:application
```

Neither framework needs to know anything about Muru.

## What's next

That covers the basics of running an application in development mode. Rather than walk through every option, the posts which follow will concentrate on the places where Muru does things differently to the other ways of hosting a Python web application, still in development mode for now, before moving on to the daemon.
