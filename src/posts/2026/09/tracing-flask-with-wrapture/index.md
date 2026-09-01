---
title: "Tracing Flask with wrapture"
description: "One HTTP request as one tree, from a single config entry, with the failing request saying both that it answered 500 and why."
date: 2026-09-09
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "tracing", "flask"]
draft: true
---

For a web application the natural unit of tracing is the request: one HTTP request, its method, path and status, and every observed call made while handling it, as one tree. The [config file from last time](/posts/2026/09/zero-code-tracing-with-wrapture/) cannot give you that on its own, and it is worth being clear about why before showing what does.

A WSGI application looks like any other callable, but it routes the interesting facts around the return value. The status and headers travel through the `start_response` callback rather than being returned. The body is an iterable that the server consumes after the call has returned, so a streaming application does most of its work after a call event would already have closed. And when a view raises, the framework catches the exception and turns it into a 500 response before any wrapper on the application ever sees it. A binding on the application callable would record a call that returned an iterable and raised nothing, which is true and useless.

## The shop behind Flask

Here is the shop from the earlier posts behind a small Flask application. A `/quote/<item>` route renders a template, a `/order` route places an order through the `OrderService` from before, and a `/health` route exists because every deployed service has one.

```python
from flask import Flask, jsonify, render_template, request

from shop import CardDeclined, OrderService

CATALOG = {"widget": 25, "gadget": 120}

app = Flask("webshop")
service = OrderService()


@app.get("/health")
def health():
    return "ok\n"


@app.get("/quote/<item>")
def quote(item):
    price = CATALOG[item]
    return render_template("quote.html", item=item, price=price)


@app.post("/order")
def order():
    data = request.get_json()
    try:
        charge = service.place(data["amount"], data["card"], tenant=data["tenant"])
    except CardDeclined as exc:
        return jsonify(error=str(exc)), 402
    return jsonify(charge)
```

Nothing in it mentions wrapture. The `quote` view will raise a `KeyError` for an item that is not in the catalog, which Flask will turn into a 500, and that is the request I most want to see.

## One entry

The Flask knowledge lives in an instrumentation package rather than in the config. With [wrapture-instrumentation](https://github.com/GrahamDumpleton/wrapture-instrumentation) installed alongside wrapture, the config gains a single `[[instrument]]` entry naming Flask, and keeps the observe entries for the shop's own methods from last time:

```toml
[[instrument]]
name = "flask"

[[observe]]
target = "shop:OrderService"
name = "place"
redact = ["card"]

[[observe]]
target = "shop:Gateway"
name = "charge"
redact = ["card"]

[[observe]]
target = "shop:Ledger"
name = "record"

[[sink]]
type = "printer"
```

The development server runs under the runner exactly as the script did, with everything after `-m flask` belonging to Flask:

```
$ python -m wrapture -m flask --app webshop run --port 5001
```

Then from another shell, a quote, an order, a declined order and the item that does not exist:

```
$ curl http://127.0.0.1:5001/quote/widget
$ curl -X POST -H 'Content-Type: application/json' \
    -d '{"amount": 500, "card": "4111-1111-1111-1111", "tenant": "acme"}' \
    http://127.0.0.1:5001/order
$ curl -X POST -H 'Content-Type: application/json' \
    -d '{"amount": 250, "card": "4000-0000-0000-0000", "tenant": "globex"}' \
    http://127.0.0.1:5001/order
$ curl http://127.0.0.1:5001/quote/missing
```

In the server's log, interleaved with Flask's own access log lines which I have removed here, each request arrives as one tree. The quote:

```
GET /quote/widget (webshop.wsgi_app)
  quote(item='widget')
    flask:render_template(template_name_or_list='quote.html', context='<context>')
    flask:render_template -> '<17 chars>' [1.5ms]
  quote -> '<p>widget: 25</p>' [1.6ms]
webshop.wsgi_app -> '200 OK' [2.3ms, body 5us over 1 chunk]
```

The request line opens the tree, the view sits beneath it labelled by its endpoint, the template render sits beneath the view with the template's name and its context masked (it is arbitrary application data, and the render is captured only as its size), and the closing line carries the status as the request's result along with the time to the last byte of the body. The order, with the shop's own methods nesting beneath the view because their bindings fire while the request is in flight:

```
POST /order (webshop.wsgi_app)
  order()
    shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
      shop:Gateway.charge(amount=500, card='<redacted>')
      shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [7us]
      shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})
      shop:Ledger.record -> 'led_ch_500' [4us]
    shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [205us]
  order -> <Response 29 bytes [200 OK]> [471us]
webshop.wsgi_app -> '200 OK' [922us, body 4us over 1 chunk]
```

The declined card, where the view caught the exception and answered 402, so the failure is on the gateway and the service but not on the request:

```
POST /order (webshop.wsgi_app)
  order()
    shop:OrderService.place(amount=250, card='<redacted>', tenant='globex')
      shop:Gateway.charge(amount=250, card='<redacted>')
      shop:Gateway.charge !! CardDeclined [6us]
    shop:OrderService.place !! CardDeclined [74us]
  order -> (<Response 38 bytes [200 OK]>, 402) [265us]
webshop.wsgi_app -> '402 PAYMENT REQUIRED' [673us, body 4us over 1 chunk]
```

And the one I wanted:

```
GET /quote/missing (webshop.wsgi_app)
  quote(item='missing')
  quote !! KeyError [4us]
webshop.wsgi_app -> '500 INTERNAL SERVER ERROR' !! KeyError [3.2ms, body 6us over 1 chunk]
```

The request line says two things at once. It answered 500, and the `KeyError` was the reason. That second half is the part a reader would not guess, because as far as the WSGI middleware recording the request is concerned, the application returned normally. Flask caught the exception on its way out of the view and handed it to `handle_exception`, which built the 500 response and returned it, so the request completed with a status and no exception. The only place the failure can be seen is inside that handler, where the exception arrives as an argument, and that is where the instrumentation looks. A binding on `handle_exception` notes the exception against the nearest enclosing request event, using the same `note_exception()` that the testing series used for a failure the code handled itself, aimed past the handler's own call with `current_event(kind="request")`. The view's event carries the `KeyError` as the exception that escaped it, the request's event carries it as a note, and both show up on their lines because two scopes failed for the same reason.

## Keeping the noise out

Health checks and static assets make up most of the traffic on a lot of services and none of the interest. In the log above every `/health` probe printed its own tree, which after a day of a load balancer polling it is most of the file. The instrumentation takes a list of paths not to record:

```toml
[[instrument]]
name = "flask"
ignore_paths = ["/health"]
```

A matching request runs and answers as normal but records nothing at all, and the "at all" matters. Declining the request event alone would leave the view, any lifecycle callbacks and any template render it made on the trace as anonymous roots with no request above them, the same problem `tree=True` solved on a plain binding in the [first post](/posts/2026/09/live-tracing-with-wrapture/). The setting silences everything beneath an ignored request for its whole extent, so with it in place the health probe leaves only Flask's access log line behind and the next quote prints as before:

```
127.0.0.1 - - [01/Sep/2026 14:51:43] "GET /health HTTP/1.1" 200 -
GET /quote/gadget (webshop.wsgi_app)
  quote(item='gadget')
    flask:render_template(template_name_or_list='quote.html', context='<context>')
    flask:render_template -> '<18 chars>' [1.5ms]
  quote -> '<p>gadget: 120</p>' [1.7ms]
webshop.wsgi_app -> '200 OK' [2.3ms, body 5us over 1 chunk]
```

The other switch worth knowing about is `lifecycle = false`. Flask extensions register `before_request` and `after_request` callbacks liberally, for loading users, cleaning up sessions and stamping headers, and the instrumentation observes every one of them by default in the order Flask runs them. For an application with several extensions that is faithful but noisy, and switching it off leaves the callbacks running unobserved.

## What the instrumentation is

There is no magic in the `[[instrument]]` entry. It names an `Instrumentation` class whose hooks run when Flask is imported, and those hooks apply bindings to three choke points in Flask, using the same bindings as everywhere else. Constructing a `Flask` instance installs the recording WSGI middleware on its `wsgi_app` attribute, so every application the process creates is covered however it was made, application factories included. Registering a route substitutes an observed version of the view function, since Flask captures views into its dispatch table the moment `@app.route` runs, before any binding on the module could have seen them. And `handle_exception` gets the binding that notes the failure described above. The `flask-app` example in the [wrapture repository](https://github.com/GrahamDumpleton/wrapture/tree/main/examples) is that class written out in full, as a local file next to a config, for anyone who wants to do the same for a framework that has no package yet. The packaged version adds the lifecycle callbacks, error handlers, blueprints and template rendering on top.

## The request as an event

Everything the tree shows is on the request event itself, which is what a sink or a test reads. The `result` is the status line, so every existing filter and assertion that works on a return value works on a request. The `duration` is wall time from the call to the close of the body, time to last byte, with the synchronous phase and the body's own share recorded separately. The HTTP details, method, path, query string with sensitive parameters already masked, scheme, remote address and the bytes actually served, sit in the event's `data`, and the instrumentation adds the matched route pattern and endpoint once routing has run, which are the low-cardinality keys a backend groups by. The [WSGI request tracing page](https://wrapture.readthedocs.io/en/latest/wsgi-tracing.html) has the full event, the `mode="wsgi"` binding form for applications with no framework package, and the redaction rules; ASGI applications get the same treatment on the [page beside it](https://wrapture.readthedocs.io/en/latest/asgi-tracing.html).

With a request as one tree and timings on every line, the next question is the one every web application eventually asks, which is where the time is going.
