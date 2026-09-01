---
title: "OpenTelemetry export in wrapture"
description: "The same events that print a tree or fill a file can feed an OpenTelemetry backend while the application runs, with one trace id shared across files, headers and spans."
date: 2026-09-11
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "tracing", "opentelemetry"]
draft: true
---

Everything in the last four posts rendered a trace for a person to read or wrote it to a file for later. The other destination is a tracing backend, fed while the application runs, and OpenTelemetry is the one that the ecosystem has converged on. wrapture treats it as a first-class destination rather than something you bolt on: the `wrapture.otel` subpackage ships in every wheel, and the `otel` extra brings the SDK and the OTLP exporter with it.

```
$ pip install "wrapture[otel]"
```

A plain install pays nothing for this, since nothing in base wrapture imports the subpackage until a config asks for it.

## One table

Export is switched on by a top-level `[otel]` table in the same config file the [Flask shop](/posts/2026/09/tracing-flask-with-wrapture/) has been using. The presence of the table opts in, a service name identifies the process, and each signal's tuning nests beneath it. I shortened the metrics export interval so the demonstration would not have to wait a minute for a data point.

```toml
[otel]
service_name = "webshop"

[otel.metrics]
export_interval = 2

[[instrument]]
name = "flask"
ignore_paths = ["/health"]

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
```

Where the spans go is decided by the standard OpenTelemetry environment variables, so with a collector listening on the usual port nothing more is needed. For a look without a collector, the console exporters print the spans and metrics to standard output instead, which is what I used here:

```
$ OTEL_TRACES_EXPORTER=console OTEL_METRICS_EXPORTER=console \
    python -m wrapture -m flask --app webshop run --port 5003
```

One event becomes one span. A request becomes a SERVER span, a call or a block becomes an INTERNAL span beneath it, and the tree the printer drew is the tree the backend receives. For the quote of an item that is not in the catalog, the view's span arrives with error status and the exception recorded on it (trimmed here to the parts that matter; the real output includes the stack trace and the resource attributes):

```json
{
    "name": "quote",
    "context": {
        "trace_id": "0x02f1fd262a7817d4f8b42fb0f6a30db3",
        "span_id": "0x5b94b62db087bbc9"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0xfba0a55ab3a322f0",
    "status": {
        "status_code": "ERROR",
        "description": "KeyError"
    },
    "attributes": {
        "wrapture.path": "webshop:quote",
        "wrapture.kind": "call",
        "wrapture.arg.item": "missing"
    },
    "events": [
        {
            "name": "exception",
            "attributes": {
                "exception.type": "KeyError",
                "exception.message": "'missing'",
                "exception.escaped": "True"
            }
        }
    ]
}
```

And the request span it is parented under:

```json
{
    "name": "GET /quote/<item>",
    "context": {
        "trace_id": "0x02f1fd262a7817d4f8b42fb0f6a30db3",
        "span_id": "0xfba0a55ab3a322f0"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": null,
    "status": {
        "status_code": "ERROR"
    },
    "attributes": {
        "http.request.method": "GET",
        "url.path": "/quote/missing",
        "http.route": "/quote/<item>",
        "http.response.status_code": 500,
        "wrapture.data.endpoint": "quote",
        "wrapture.data.remote": "127.0.0.1"
    },
    "events": [
        {
            "name": "exception",
            "attributes": {
                "exception.type": "KeyError",
                "exception.message": "'missing'",
                "exception.escaped": "False"
            }
        }
    ]
}
```

A few things in there are worth pointing at. The request span is named `GET /quote/<item>`, by the route pattern rather than the URL, because the Flask instrumentation annotates the request with its matched route once routing has run, and the exporter reads that as the semantic-convention `http.route`. A backend then groups by endpoint rather than seeing every URL as a distinct operation. The captured arguments and anything added with `annotate()` become span attributes under `wrapture.arg.*` and `wrapture.data.*`, with the card number already redacted before it got anywhere near the exporter. And the `KeyError` appears on both spans, once as the exception that escaped the view and once as the one noted against the request after Flask caught it, so the request span shows the 500, the error status and the reason together rather than a status with no explanation.

## One trace across two processes

A trace within one process is only half of what a tracing backend is for. The `trace-propagation` example in the [wrapture repository](https://github.com/GrahamDumpleton/wrapture/tree/main/examples) is two processes: a client that places orders against a quote service over HTTP, and the service itself, both observed by wrapture and both writing JSON Lines files. Every tree wrapture records carries a W3C trace id, minted at its root, and on the client side an instrumentation for `urllib` puts that id into the `traceparent` header of each outbound request. On the server side the WSGI middleware parses the header at the boundary, so that process's trees join the client's trace instead of minting their own.

The join needs no backend at all. Printing the first eight characters of the trace id from every line of both files, with the file it came from:

```
0b2ad016 server.jsonl backend:app
8f19b8c6 client.jsonl frontend:fetch_quote
8f19b8c6 client.jsonl frontend:fetch_quote
8f19b8c6 client.jsonl frontend:fetch_quote
8f19b8c6 client.jsonl frontend:place_order
8f19b8c6 client.jsonl urllib.request:OpenerDirector.open
8f19b8c6 server.jsonl backend:app
8f19b8c6 server.jsonl backend:quote
b1a416b0 client.jsonl frontend:fetch_quote
b1a416b0 client.jsonl frontend:fetch_quote
b1a416b0 client.jsonl frontend:place_order
b1a416b0 client.jsonl urllib.request:OpenerDirector.open
b1a416b0 server.jsonl backend:app
b1a416b0 server.jsonl backend:quote
...
```

Each order is one id across both files, client half and server half of one distributed trace. The repeated `fetch_quote` lines are the two blocks the client marks inside that function, which record under its path, and the lone server-only line at the top is a request that arrived with no `traceparent` header, which minted an id of its own at the boundary. The whole public surface the client instrumentation needed for this was `wrapture.trace_headers()`, which returns the pairs an outbound message made right now should carry, and is empty when nothing is being recorded, so injecting it is always safe.

Switching on `[otel]` in both processes changes nothing about the ids. The exporter claims the identity wrapture minted rather than minting one of its own, so the JSON Lines files, the outbound headers and the exported spans all read the same trace id, and the server's request span is created with the arrived identity as a remote parent. In the console output from the same run, the server's `GET /quote/widget` span carries the client's trace id and names the client's `urllib.open` span as its parent:

```json
{
    "name": "GET /quote/widget",
    "context": {
        "trace_id": "0xcdde803e61b96f52e2eb3820c7004df0",
        "span_id": "0x9bb64b3bad9a6848"
    },
    "kind": "SpanKind.SERVER",
    "parent_id": "0x670e42eb0ac7690a",
    ...
}
```

```json
{
    "name": "urllib.open",
    "context": {
        "trace_id": "0xcdde803e61b96f52e2eb3820c7004df0",
        "span_id": "0x670e42eb0ac7690a"
    },
    "kind": "SpanKind.INTERNAL",
    "parent_id": "0x0e06d5674120b1db",
    ...
}
```

In a viewer, each order is one distributed trace with the service's request span attached beneath the outbound call that made it. One invariant governs the header handling and it is worth stating because it is the thing that makes this safe to switch on in a service that sits between other people's systems: never break a trace you do not understand. A header wrapture parses but nothing claims is forwarded verbatim, so an upstream product sees this service as a transparent hop, and headers wrapture does not parse are never touched at all.

## Metrics for free

The traces signal exports events individually. The metrics signal aggregates the same events instead, and both were on above since the default is all signals. Request durations go into the semantic-convention `http.server.request.duration` histogram, attributed by method, route and status code, and observed calls go into a per-path `wrapture.call.duration` histogram whose error series split out by exception type. From the same run, the attribute sets on the request histogram's data points were:

```json
{
    "http.request.method": "POST",
    "http.route": "/order",
    "http.response.status_code": 200
}
```

```json
{
    "http.request.method": "GET",
    "http.route": "/quote/<item>",
    "http.response.status_code": 500,
    "error.type": "KeyError"
}
```

So per-endpoint latency and error rate read straight off the histogram with no code involved. The reason the bound path is safe as a metric attribute where a raw URL would not be is that the config chose the bindings, so the set of values is closed; requests are attributed by route pattern for the same reason, never by URL. The design is the `Aggregate` collector from the [previous post](/posts/2026/09/finding-slow-code-with-wrapture/) with the aggregation handed to the SDK: bounded memory, no values captured, nothing retained.

## What it costs

The usual objection to instrumenting Python is the overhead, so this is worth a paragraph. Exporting through wrapture costs about the same as instrumenting with the OpenTelemetry SDK directly, and on a call that raises it costs noticeably less, because the SDK's `record_exception` formats the stack trace through `traceback.format_exception`, which on current Pythons parses each frame's source to draw caret underlines that no backend renders, and wrapture's sink formats the same frames without them. The design point behind the rest is that the sink does not use the SDK's tracer at all. Everything a span needs is known when its event closes, so the sink builds the finished span at that moment and hands it to the SDK's own processor, skipping the tracer's mutable span object with its validated attribute store and locks, which is where most of the per-span cost used to go. The measured figures, with the methodology, are in the [cost section](https://wrapture.readthedocs.io/en/latest/otel-export.html#what-it-costs) of the OpenTelemetry export page, and I would rather point there than quote numbers that will be out of date by the time anyone reads this.

## The thread from the beginning

When I [introduced wrapture](/posts/2026/08/introducing-wrapture/) I said there were two interests behind it, correctness in testing and instrumenting programs for tracing, and that underneath they wanted the same thing: a way to see the real calls as they happen. This is where the second one ends up. The three bindings on the shop have not changed since the [first testing post](/posts/2026/09/unit-testing-with-wrapture/). In a test they feed a tape and the assertions read off it. In production they feed a backend, with a request as one tree, a trace id that survives crossing to another service, and metrics aggregated from the same events. The only thing that changed along the way is who was listening.

The [OpenTelemetry export page](https://wrapture.readthedocs.io/en/latest/otel-export.html) has the rest of the table, including sampling, the logs signal and how wrapture's pipelines coexist with an application that already uses the OpenTelemetry API on its own account.
