---
title: "Finding slow code with wrapture"
description: "One endpoint is slow and there are three layers it could be. Self time for the handful of methods you chose answers the question without a profiler and without a stopwatch in every layer."
date: 2026-09-10
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "tracing", "performance"]
draft: true
---

The `/order` endpoint of the [Flask shop](/posts/2026/09/tracing-flask-with-wrapture/) is slow. The view calls the order service, the service calls the gateway and then the ledger, and the question is which of those the time is going to. To give the question a real answer for this post I put a `time.sleep(0.03)` in `Ledger.record`, and the rest of the post pretends I did not know that.

The usual move is a stopwatch. A `perf_counter()` before and after the service call, a log line with the difference, another pair around the gateway, another around the ledger. Each of those is a code change in a layer that should not know it is being measured, the numbers arrive as separate log lines that you correlate by eye, and none of them are tied to the request they belong to, so one slow request among fast ones is invisible in the average. A profiler has the opposite problem: it sees every frame in the process, most of them framework internals, and cannot tell one request from the next.

## The tree with times on it

The config from last time already prints an elapsed time on every closing line, so the first order through the server is most of the answer:

```
POST /order (webshop.wsgi_app)
  order()
    shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
      shop:Gateway.charge(amount=500, card='<redacted>')
      shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [8us]
      shop:Ledger.record(entry="<dict {'id': 'ch_500', 'amount': 500}>")
      shop:Ledger.record -> 'led_ch_500' [35.1ms]
    shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [35.9ms]
  order -> '<Response 29 bytes [200 OK]>' [36.3ms]
webshop.wsgi_app -> '200 OK' [37.3ms, body 10us over 1 chunk]
```

Reading up from the bottom, the request took 37.3ms, the view 36.3ms, the service 35.9ms, and the ledger 35.1ms, with the gateway at 8us. The figures are from one run, and they vary, but the shape does not. The ledger accounts for essentially all of the service, which accounts for essentially all of the view. The service and the view are slow because of what they call. The ledger is slow in its own right.

That distinction, slow itself versus slow because of a child, is the one a wall-clock timer around the service call cannot express, and it has a name. Self time is an operation's duration minus the time its observed children account for, and wrapture computes it from the parent links as events close. In a test, `tape.tree(times=True)` prints both figures and `tape.self_time()` gives it for one event, so the same observation can be turned into an assertion that will catch the next regression:

```python
import wrapture

from shop import Gateway, Ledger, OrderService
from webshop import app


def test_where_the_time_goes():
    place = wrapture.binding(OrderService, "place", capture=wrapture.redact("card"))
    charge = wrapture.binding(Gateway, "charge", capture=wrapture.redact("card"))
    record = wrapture.binding(Ledger, "record")

    with wrapture.instrumentation("flask"), wrapture.timeline(place, charge, record) as tape:
        client = app.test_client()
        response = client.post("/order", json={"amount": 500, "card": "4111-1111-1111-1111", "tenant": "acme"})
        assert response.status_code == 200

        print()
        print(tape.tree(times=True))

        order = place.events.assert_once()[0]
        ledger = record.events.assert_once()[0]
        assert tape.self_time(order) < 0.1 * order.duration
        assert tape.self_time(ledger) > 0.9 * order.duration
```

The `wrapture.instrumentation("flask")` context applies the same Flask instrumentation the config file named, scoped to the block, and the timeline records what the three bindings see. Running it with `pytest -s` prints the tree:

```
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')  -> {'id': 'ch_500', 'amount': 500}  [31.0ms, self 173us]
  shop:Gateway.charge(amount=500, card='<redacted>')  -> {'id': 'ch_500', 'amount': 500}  [7us]
  shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})  -> 'led_ch_500'  [30.8ms]
```

The service spent 173us of its 31.0ms doing anything itself. No external profiler can produce that number for an arbitrary handful of methods, because a profiler only sees whole call stacks; wrapture can, because the events know their parents.

## Across many requests

One request is an anecdote. The `Aggregate` collector keeps one row per bound location, with how many operations began and completed, how many raised, and the total, self, fastest and slowest times, sorted by self time, which is the column profilers rank by. It retains no events, so its memory is bounded by the number of bindings however much traffic flows, and it asks for no argument or result values, so the recording skips capture entirely while it is the only thing listening. It can be registered as a sink in code, but the shape I wanted was a report for the whole run of the server, which is a window in the config file:

```toml
[[window]]
name = "stats"
report = "stats.txt"

[[window.collect]]
type = "aggregate"
```

A window with no trigger and no duration is one run for the whole process, opened when the config applies and closed at interpreter exit, one report. I ran the server under that config, sent it thirty requests from a loop (ten orders for one tenant, ten declined orders for another, and ten quotes), stopped it, and read the file:

```
aggregate "aggregate" run 1, 2026-09-01 14:57:29 to 14:57:31 +10:00 (1.6s), pid 87241
7 paths, 120 operations begun, 120 completed, 20 raised

calls    total     self  per-call     min     max  errors  path
   10  358.3ms  358.3ms    35.8ms  30.7ms  39.5ms          shop:Ledger.record
   30  385.2ms   11.9ms    12.8ms   534us  40.5ms          flask.app:Flask.wsgi_app
   20  369.8ms    5.7ms    18.5ms   296us  40.1ms          webshop:order
   20  364.1ms    5.7ms    18.2ms   105us  39.9ms      10  shop:OrderService.place
   10    2.2ms    2.2ms     223us    63us   1.6ms          flask:render_template
   10    3.5ms    1.3ms     354us   188us   1.8ms          webshop:quote
   20    106us    106us       5us     4us    11us      10  shop:Gateway.charge
```

The ledger is the top row by a wide margin. The `order` view and `place` have large totals and small self times, which is the same story the single tree told, now over twenty orders with a minimum and maximum attached. The `errors` column shows the ten declined cards twice, once where the gateway raised and once where the service let it escape. The same report can be produced every hour on the hour with totals reset, from the same file, by giving the window a schedule; the [scheduled tracing page](https://wrapture.readthedocs.io/en/latest/scheduled-tracing.html) covers that, and I will leave it there.

## Slow for whom

An endpoint is often slow for one tenant, one account or one request id, and the middleware cannot know which header carries that. `annotate()` merges values into the in-flight event's `data`, and it is unconditionally safe to call, doing nothing when nothing is recording, which makes it reasonable to leave in application code permanently. In the shop a `before_request` hook is the natural place, since the request event is already open by the time it runs:

```python
@app.before_request
def tag_tenant():
    wrapture.annotate(tenant=request.headers.get("X-Tenant"))
```

This is the one edit to the application in this series, and it is the same `annotate()` the testing series used to attach what the code knows to an event. The tag rides on the request event, so with a `jsonlines` sink in the config beside the printer it is in the file, and the slow requests can be sliced by who they were for:

```
$ jq -c 'select(.kind=="request" and .data.tenant=="acme") | {tenant: .data.tenant, path: .data.path, ms: ((.duration*1000*10|round)/10)}' trace.jsonl
{"tenant":"acme","path":"/order","ms":35.7}
{"tenant":"acme","path":"/order","ms":32.5}
{"tenant":"acme","path":"/order","ms":35.9}
```

The other tenant's orders were all declined at the gateway and never reached the ledger, so they sit around a millisecond. The same expression selects the request to assert on in a test, through `events.matching()`, and a `Filter` around a printer narrows the live view to one tenant's requests.

## The cheaper cousin

Everything above retained a duration. Sometimes the answer is just a number, and the `Counter` collector counts operations as they begin and keeps nothing else, which makes it cheap enough to leave running under a whole test suite. Bind a database layer's `execute` once, register a counter, and give every test a query budget in a fixture, and the classic N+1 regression fails with a number attached rather than slipping through as a test that merely got slower. The [collectors section](https://wrapture.readthedocs.io/en/latest/ad-hoc-tracing.html#counting-without-retaining) of the ad-hoc tracing page has that example in full.

So far every trace has been rendered for a person or written to a file. The remaining step is feeding the same events to a tracing backend while the shop runs.
