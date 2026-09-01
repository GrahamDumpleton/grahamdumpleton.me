---
title: "Zero-code tracing with wrapture"
description: "Tracing an application you cannot or should not edit: the bindings and sink move into a TOML file next to the project, and the program runs untouched."
date: 2026-09-08
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "tracing"]
draft: true
---

The [previous post](/posts/2026/09/live-tracing-with-wrapture/) traced the shop with three bindings and a sink, all applied from the program's own entry point. That is fine when the program is yours. It is less fine when the application is one you inherited and would rather not touch, when someone else owns the deployment, or when you simply do not want observation code living inside the thing being observed. For all of those the entry point edit is one edit too many.

The same setup can live in a file next to the project instead, with nothing in the program saying so.

## The file

A `wrapture.toml` says what to observe and where the events go. For the shop from last time, with the card number redacted as before, that is one `[[observe]]` entry per method and one sink:

```toml
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

The `target` is always an exact module or `module:path`, never a pattern, and the members within it come from `name` for exact members or `match` for a glob over the target's own immediate members. That is deliberate. A pattern's blast radius is one level of one named container, stated on the line above it, so `match = "*"` on `shop:OrderService` can never accidentally wrap something in another module.

The program itself is `main.py`, and it now contains no mention of wrapture at all:

```python
import orders

orders.run()
```

The `python -m wrapture` runner applies the config and then runs the program as `__main__`, the same `-m` convention as pdb, cProfile and coverage:

```
$ python -m wrapture main.py
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
  shop:Gateway.charge(amount=500, card='<redacted>')
  shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [8us]
  shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})
  shop:Ledger.record -> 'led_ch_500' [7us]
shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [285us]
shop:OrderService.place(amount=250, card='<redacted>', tenant='globex')
  shop:Gateway.charge(amount=250, card='<redacted>')
  shop:Gateway.charge !! CardDeclined [6us]
shop:OrderService.place !! CardDeclined [90us]
shop:OrderService.place(amount=120, card='<redacted>', tenant='globex')
  shop:Gateway.charge(amount=120, card='<redacted>')
  shop:Gateway.charge -> {'id': 'ch_120', 'amount': 120} [4us]
  shop:Ledger.record(entry={'id': 'ch_120', 'amount': 120})
  shop:Ledger.record -> 'led_ch_120' [4us]
shop:OrderService.place -> {'id': 'ch_120', 'amount': 120} [115us]
```

That is the same trace as before, from a program whose source has not changed. The ordering is what makes it work. The config is applied before the target runs, but applying it imports nothing: each observe entry registers a post-import hook for its target module, and the bindings land at the moment the application itself imports `shop`, in the application's own import order. A `from shop import OrderService` somewhere in the program still picks up the observed class, because the observation is already in place when that line runs, and the program's import order is never changed by observing it.

## Keeping the trace

A printer is for watching. For a program that runs longer than you are willing to sit and look at it, the sink is a file. Swapping the `[[sink]]` entry for a JSON Lines one is the only change:

```toml
[[sink]]
type = "jsonlines"
path = "trace.jsonl"
```

Each completed event is written as one JSON object per line, when the event closes, so every line carries the outcome and the timing. The declined charge from the second order looks like this:

```json
{
  "seq": 5,
  "parent_id": 4,
  "depth": 1,
  "kind": "call",
  "path": "shop:Gateway.charge",
  "thread_id": 140704287927360,
  "thread_name": "MainThread",
  "started": 1150729.898723529,
  "duration": 0.000004197005182504654,
  "arguments": {
    "amount": 250,
    "card": "<redacted>"
  },
  "exception": {
    "type": "CardDeclined",
    "message": "card ending 0000 declined"
  },
  "trace": {
    "w3c": {
      "trace_id": "12cd461196239288a8b50e265b6a0f1a",
      "sampled": true
    }
  }
}
```

The `seq` and `parent_id` fields are enough to rebuild the tree, and a field that is absent means it was not captured, so a call that returned `None` and a call whose result was never recorded stay distinguishable. The format is the one that `jq`, pandas and most log tooling read directly, which means the questions I would otherwise have scrolled a terminal to answer become one-liners. Every call to the gateway, with what it was given and what came back:

```
$ jq -c 'select(.path | endswith("Gateway.charge")) | {seq, arguments, result, exception}' trace.jsonl
{"seq":2,"arguments":{"amount":500,"card":"<redacted>"},"result":{"id":"ch_500","amount":500},"exception":null}
{"seq":5,"arguments":{"amount":250,"card":"<redacted>"},"result":null,"exception":{"type":"CardDeclined","message":"card ending 0000 declined"}}
{"seq":7,"arguments":{"amount":120,"card":"<redacted>"},"result":{"id":"ch_120","amount":120},"exception":null}
```

And everything that raised, which shows the exception at the gateway and again at the order that let it escape:

```
$ jq -c 'select(.exception) | {path, exception}' trace.jsonl
{"path":"shop:Gateway.charge","exception":{"type":"CardDeclined","message":"card ending 0000 declined"}}
{"path":"shop:OrderService.place","exception":{"type":"CardDeclined","message":"card ending 0000 declined"}}
```

Two properties make this safe to leave running against something real. The application never waits on the file: lines go onto a bounded queue drained by a background thread, and if the queue fills the line is dropped and counted rather than making the observed call block. And the sink captures values as bounded summaries, so an unserialisable argument becomes a short description rather than an error, and no live object is retained. For a process that runs for days the path can carry a date or time variable and rotate on an interval; the [output paths section](https://wrapture.readthedocs.io/en/latest/ad-hoc-tracing.html#output-paths-and-rotation) of the documentation has that. The file is also what the exporters read afterwards, so a trace recorded overnight can be rendered for Perfetto the next morning.

## No launcher at all

The runner still owns the command line, and sometimes that is not available either. A service manager, a container entry point or a WSGI server starts the process and you do not get to put `python -m wrapture` in front of it. For that case the same config can be injected at interpreter startup through [autowrapt](https://github.com/GrahamDumpleton/autowrapt), a package of mine from some years ago that exists precisely to run registered code once site initialisation completes. Two opt-ins gate it, both outside wrapture:

```
$ pip install autowrapt
$ AUTOWRAPT_BOOTSTRAP=wrapture python main.py
```

The output is identical to the runner's. Installing autowrapt is what makes interpreter startup do anything at all, and the environment variable names wrapture as the thing to bootstrap. Absent either, the entry in wrapture's package metadata is inert, and wrapture itself has no dependency on autowrapt. Underneath, both doors lead to the same place: the post-import hook machinery in wrapt, which autowrapt was originally built on, is what lets wrapture apply a config to modules that have not been imported yet.

The positioning matters here. Injection is a development, staging and break-glass tool. The unwritten rule for autowrapt has always been that it is not installed on production systems in normal circumstances, precisely because of what it enables, and that installation gate is the feature. Production tracing is the code-level path from the previous post, or a config applied deliberately by the application at startup. Two consequences follow from the mechanism. A config that is missing, or that cannot be applied, warns and lets the process start untraced, because an error at bootstrap would be fatal to an interpreter that has not even started, and the environment variable reaches every Python process launched under it, not only the one you meant. And the bootstrap imports no application code, so bindings still land as the application imports its own modules.

## Operating a traced process

Once injected, the process is still operable. The bootstrap keeps its record of what was applied on `wrapture.bootstrap.applied`, and from a console, a debugger or a signal handler that record answers what is installed and lets you switch it off and on without a restart. Running the shop under `python -i` so the interpreter drops to a prompt afterwards:

```
$ AUTOWRAPT_BOOTSTRAP=wrapture python -i main.py
...
>>> import wrapture.bootstrap
>>> applied = wrapture.bootstrap.applied
>>> print(applied.report())
sink: Printer()
applied:
  shop:OrderService.place
  shop:Gateway.charge
  shop:Ledger.record
>>> applied.suspend()
>>> import orders; orders.run()
>>> applied.resume()
>>> orders.run()
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
  shop:Gateway.charge(amount=500, card='<redacted>')
...
```

While suspended, the wrappers stay in place and the calls pass straight through, so the second `orders.run()` printed nothing; after `resume()` the third printed the full trace again. `revert()` takes the whole intervention down, restoring the patched locations. The [config section](https://wrapture.readthedocs.io/en/latest/ad-hoc-tracing.html#configuring-from-a-file) of the ad-hoc tracing page covers everything the file can say beyond what I have used here, including capturing log messages as events beside the calls, and naming instrumentation that a package ships for a framework.

That last one is where this goes next, because the shop is not really a program that runs three orders and exits. It is a web application, and a web application has a unit of work that a plain binding cannot see.
