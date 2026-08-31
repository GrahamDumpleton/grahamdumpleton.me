---
title: "Introducing wrapture"
description: "wrapture is a new Python package for monkey patching, testing and tracing built on wrapt, written by an AI under my direction. What it does, why I built it, and what happens next."
date: 2026-08-31
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing", "ai"]
draft: false
---

For the best part of two decades, through [wrapt](https://github.com/GrahamDumpleton/wrapt), I have been dealing with the mechanics of monkey patching in Python. Anyone who has followed wrapt will know I am quite pedantic about correctness, to the point of caring whether a wrapper preserves every last introspectable detail of the thing it wraps. For much of that time I have wanted the same standard from the tools I use when testing code, and `unittest.mock`, which does what it does well enough, was never designed to give it. A fabricated `Mock` answers every method call and verifies nothing. A patched call records a flat list of calls, with no return values and no sense of what was called from what. The calls an object makes to itself are invisible, because the substitute never runs the real code at all. What I want a test to be sure of, that the right calls happened, in the right order, with the real code actually running, sits just outside what substitution can express.

Seeing the real calls as they happen, with the real code still doing the work, was also something I had already spent years on for a quite different purpose. I was the original author of the New Relic Python agent, written while I worked there, and that left me with a lasting interest in instrumenting Python programs. Attaching observation to code you do not control, recording what flows through it, and doing so without disturbing the program being watched, is a problem I have never really stopped thinking about.

Testing and tracing look like different problems, but from where I sat they wanted the same thing, and I had long believed that wrapt's approach of wrapping real code rather than replacing it could serve both. wrapture (the name being `wrapt` plus `capture`) is me finally getting around to finding out whether that belief held up.

## Wrap anything, capture everything

The one idea everything in wrapture sits on is to wrap rather than replace. A binding names a location in code, a method of a class or a function in a module, and when applied installs a wrapt wrapper around the real callable. Unless you tell it otherwise the wrapper is transparent. The real code runs, with wrapture in a position to watch the call, change it, or answer it instead.

Take a small call graph where an order service charges a payment gateway and then records the result in a ledger:

```python
import wrapture

class Gateway:
    def charge(self, amount, currency="USD"):
        return {"id": f"ch_{amount}", "amount": amount}

class Ledger:
    def record(self, entry):
        return f"led_{entry['id']}"

class OrderService:
    def __init__(self):
        self.gateway = Gateway()
        self.ledger = Ledger()

    def place(self, amount):
        result = self.gateway.charge(amount)
        self.ledger.record(result)
        return result
```

None of these classes import wrapture or know they are about to be observed. Bindings are created by naming the methods, and a timeline opens a recording scope in which every call through them lands on a tape:

```python
place = wrapture.binding(OrderService, "place")
charge = wrapture.binding(Gateway, "charge")
record = wrapture.binding(Ledger, "record")

with wrapture.timeline(place, charge, record) as tape:
    OrderService().place(500)

print(tape.tree())
```

Running this the output is:

```
__main__:OrderService.place(amount=500)  -> {'id': 'ch_500', 'amount': 500}
  __main__:Gateway.charge(amount=500, currency='USD')  -> {'id': 'ch_500', 'amount': 500}
  __main__:Ledger.record(entry={'id': 'ch_500', 'amount': 500})  -> 'led_ch_500'
```

That is the call graph as it actually ran. The arguments are normalised against the real signatures (so `charge(500)` and `charge(amount=500)` look the same), the return values are the real ones, and the nesting comes from what really called what. The `tape.tree()` call is a convenience for debugging and for demonstrations like this one; in a test you would query the tape instead, and outside of a test the events would be going to a sink, which I will come to.

The same bindings intervene as well as observe. The real method can be stubbed out, made to fail, or left running while one thing about the call is changed on the way in or out:

```python
gateway = Gateway()

with wrapture.binding(Gateway, "charge").on_call.raises(TimeoutError("down")):
    gateway.charge(500)
```

Inside the block the call raises `TimeoutError`, and after the block exits the original method is back exactly as it was.

## Three uses of one mechanism

That is the whole mechanism. What makes it interesting is that it serves three purposes which are usually handled by three different tools.

The first is plain monkey patching. wrapt's `wrap_object()` has always been able to patch a target, but it leaves the bookkeeping to you. wrapture adds a lifecycle and a vocabulary over the top of it. A binding declares a target without touching it, `apply()` installs the patch, `remove()` restores the original, `suspend()` makes it inert in place, and a group of bindings applies and removes as one unit. Behaviour is configured on the binding, with `returns()`, `raises()`, `transforms_args()`, `transforms_result()` and a few others, and can be scripted to change over time, so "succeed twice, then time out" is three lines rather than a hand-written counter. This layer is useful on its own with nothing else switched on.

The second is unit testing, which is where the recording comes in. Because the real code runs, a test can assert on how calls actually flowed through it, and the interesting cases are the error paths. Inject a failure at the gateway, then check that the ledger was never written:

```python
with wrapture.timeline(place, charge, record) as tape:
    charge.on_call.raises(TimeoutError("down"))

    try:
        OrderService().place(500)
    except TimeoutError:
        pass

    record.events.assert_never()

    print(tape.tree())
```

With the assertion passing, the tree shows where the failure was injected and how it propagated:

```
__main__:OrderService.place(amount=500)  !! TimeoutError
  __main__:Gateway.charge(amount=500, currency='USD')  !! TimeoutError (injected)
```

When a test must supply a stand-in, because the code under test receives a collaborator rather than importing it, wrapture provides `stub()` for a callable and `mock(Spec)` for a whole object, and these record onto the same tape as everything else. Both are strict: signatures are checked and nothing is invented on first touch. There is deliberately no spec-less `Mock()` equivalent, and the [comparison with unittest.mock](https://wrapture.readthedocs.io/en/latest/coming-from-mock.html) in the documentation explains why, alongside a mapping of each mock idiom to its wrapture counterpart. An opt-in pytest plugin sweeps each test for patches left applied and attaches recordings to failure reports.

The third use is ad-hoc tracing of a running application, including one you cannot modify or redeploy. Take the bindings, drop the test around them, and the only remaining question is where the events go. A sink answers that. In practice this is done with a `wrapture.toml` file naming the targets and the sink, and no code at all. Here is one for a slightly bigger version of the shop above, where the gateway declines some cards and the order service logs a warning when it does:

```toml
[[observe]]
target = "shop:OrderService"
name = "place"

[[observe]]
target = "shop:PaymentGateway"
match = "*"
exclude = "_*"

[[observe]]
target = "shop:Ledger"
name = "record"

[[log]]
name = "shop.*"

[[sink]]
type = "printer"
```

Running the program as `python -m wrapture main.py` applies the config before the program starts, so the patches are in place before the application imports anything, and the printer sink writes the trace to stderr as it happens:

```
shop:OrderService.place(order_id='order-1', amount=30, card='5100-0010')
  shop:PaymentGateway.charge(amount=30, card='5100-0010')
  shop:PaymentGateway.charge -> 'ch_30' [7us]
  shop:Ledger.record(order_id='order-1', amount=30)
  shop:Ledger.record -> 'ledger:order-1:30' [5us]
shop:OrderService.place -> 'ch_30' [234us]
shop:OrderService.place(order_id='order-2', amount=240, card='5100-0020')
  shop:PaymentGateway.charge(amount=240, card='5100-0020')
  shop:PaymentGateway.charge -> 'ch_240' [4us]
  shop:Ledger.record(order_id='order-2', amount=240)
  shop:Ledger.record -> 'ledger:order-2:240' [3us]
shop:OrderService.place -> 'ch_240' [105us]
shop:OrderService.place(order_id='order-3', amount=75, card='4000-0030')
  shop:PaymentGateway.charge(amount=75, card='4000-0030')
  shop:PaymentGateway.charge !! PaymentDeclinedError [4us]
  log shop.orders WARNING 'order order-3 declined'
shop:OrderService.place !! PaymentDeclinedError [260us]
```

Unlike the tidy reconstruction from `tape.tree()`, this is the live view, with an opening line as each call begins and a closing line with the outcome and how long it took. The `[[log]]` entry captures the application's ordinary `logging` calls as events too, so the warning appears nested inside the call that logged it rather than somewhere in a separate log file. With [autowrapt](https://github.com/GrahamDumpleton/autowrapt) installed, even the launcher is unnecessary: `AUTOWRAPT_BOOTSTRAP=wrapture` in the environment applies the same config at interpreter startup, so the program runs with plain `python`. That covers the case where something else owns the command line, like a container entry point or a WSGI server.

The printer is the simplest sink. Others stream events to disk as JSON lines, count without retaining, and compose with fan-out, sampling and filtering. Sitting on top of the tracing layer is [OpenTelemetry export](https://wrapture.readthedocs.io/en/latest/otel-export.html): with the `wrapture[otel]` extra installed, one `[otel]` table in the config sends the same events to any OTLP backend as spans, metrics and correlated logs. Every tree of events carries a W3C trace id, and the id arrives and leaves in `traceparent` headers, so two services both observed by wrapture join up as one distributed trace without either of them calling an OpenTelemetry API.

The point I want to land is that these are layers of one mechanism and not separate products. The binding vocabulary that stubs a method in a test is the same one that traces it in production, and the config that names methods for a printed call tree is the config that exports spans. What starts as a monkey patch or a test assertion can grow into observability without the code being rewritten along the way.

## Where it sits beside what already exists

Part of why I built this is that nothing I could find did all of it. `unittest.mock` records a flat call list with no nesting and no return values, and a patched call returns a fabricated `MagicMock` rather than running the real code. Span assertion tools such as OpenTelemetry's `InMemorySpanExporter` require the code to already be instrumented. Tools built on `sys.settrace` give you a firehose with no assertion API. APM agents are all-or-nothing products rather than toolkits, and their auto-instrumentation only covers the frameworks they already know about. wrapture needs none of that. You point at your own methods by name and a trace appears, and the same pointing is how it lands in a test, a terminal, or a backend.

Just as important is what it is not. It is not a fabrication tool, and `unittest.mock` remains the right thing for invented objects. It is not a production APM, although it is a toolkit that APM-like things could be built on. And it is not an OpenTelemetry competitor; it emits to OpenTelemetry rather than trying to replace it.

## Pre-built instrumentation

Pointing at your own methods is the core of wrapture, but for common third-party packages the pointing has already been done. The companion [wrapture-instrumentation](https://github.com/GrahamDumpleton/wrapture-instrumentation) package provides ready-made instrumentation, with Flask and Jinja2 covered so far. Each records a request or a template render as one structured tree, and enabling one is an `[[instrument]]` entry in `wrapture.toml` naming the target. Installing the package brings in wrapture and nothing else; the instrumentation for a package you do not have is inert. It is being built target by target, and the [instrumentation packages](https://wrapture.readthedocs.io/en/latest/instrumentation-packages.html) guide describes how to write one for a package not yet covered.

## Built with AI, on purpose

Every line of code and documentation in wrapture was written by an AI assistant working under my direction. I want to be upfront about that, and equally upfront about what it was not. This was not vibe coding, where a one-shot prompt produces a pile of generated code and the person driving hopes for the best because they lack the knowledge to judge what came back. Vibe coding has earned its bad reputation. I engineered wrapture carefully from the start. I have spent a long time in this particular corner of Python and knew exactly what the result needed to be, and the AI was the means of producing it rather than the source of the design.

The experiment had two halves. The first was whether an idea I had carried around for years actually held up once built. The second, and just as much the point, was whether a library of this kind could be produced this way, with an AI doing the writing and me doing the directing, to a standard I would be happy to put my name to.

The process is what makes the result worth trusting or not, so it deserves describing. The work started well before any code, with days spent on design documents setting out the goals, the scope, the shape of the API and the layers it would be built in, which the AI and I argued over before implementation began. From there it proceeded in layers, each one specified, discussed, implemented, tested and documented before the next began. Documentation grew with the code rather than after it, and every example in the docs runs as a doctest, so the docs are continually proven against the implementation. Writing them repeatedly exposed designs that read worse than they demoed. The test suite runs against every supported Python version, including the free-threaded builds, on every change. The overhead of Python instrumentation is the usual objection to it, so the recording path was also put through a performance pass, with the cost of a call observed and exported through wrapture measured against the same call instrumented directly with the OpenTelemetry SDK and in the style of its instrumentation packages. The result was comparable per call, with the figures in the [OpenTelemetry export](https://wrapture.readthedocs.io/en/latest/otel-export.html#what-it-costs) guide.

The step I would most recommend to anyone attempting something similar came late. I took the unit test suites of well-known Python packages that lean heavily on `unittest.mock` and had the AI replicate their tests using wrapture instead, side by side with the originals. Every point of friction became a decision: sometimes a documented position on why wrapture deliberately differs, and sometimes a missing feature that got specified, built and documented like everything else. Several pieces of wrapture exist only because a real test suite could not be expressed cleanly without them.

Throughout, the division of labour was consistent. The AI wrote the code, the tests and the prose. I set the direction, made the design calls, reviewed what came back, and sent plenty of it back. My experience with wrapt and with Python's darker corners is all through the result, in what was asked for as much as in what was refused.

The first commit was in the middle of August and the current release is the eleventh alpha, so this all happened in a bit over two weeks. In that time it accumulated over 1000 tests and over 150 pages of documentation. The documentation is admittedly quite dense in places and needs some work still, but it is complete in the sense that every part of the package is covered. One thing a brand new library has over an old one is coherence. Mature packages accrete features one release at a time, and there is never a moment when the whole API can be redesigned to match what was learned along the way. Because wrapture arrived in a compressed period with the whole design still in view, when validation showed a design could be better it was redesigned rather than worked around.

I know some people are firmly opposed to using AI-written software. If that is you, I understand, and I am not going to argue with your position. It is a reasonable one to hold, and this post exists so you can make the call with the facts in hand rather than discover them later. If AI involvement rules wrapture out for you then wrapture is not for you, and that does not worry me one bit. This has been about finding out whether the process works, and I now have my answer to that. The longer version of all this is on the [how wrapture was built](https://wrapture.readthedocs.io/en/latest/how-wrapture-was-built.html) page in the documentation.

## What's next

wrapture is in alpha, with pre-releases on [PyPI](https://pypi.org/project/wrapture/). Until 1.0.0 is final a plain `pip install wrapture` picks up the latest pre-release, so there is no need to pin a version. It requires Python 3.12 or later and wrapt 2.4.0 or later. The API is complete for the three uses described above and I am not expecting it to break, so code written against it today should carry forward to 1.0.0.

What it needs now is use. `unittest.mock` and OpenTelemetry's own instrumentation are the established tools for the two halves of what wrapture does, and the open question is whether an alternative that does both from one mechanism is something people want. Reports of it working, or not, on real code, and of what confused or was missing, are what will decide whether anything changes before a beta. They go to the [issue tracker](https://github.com/GrahamDumpleton/wrapture/issues).

To be clear, wrapture was never premised on anyone else using it. I built it because I wanted to see it exist, not because I had identified a gap in the market. If people find it useful and pick it up, that is great, and I will aim to support it. If there is no interest, I will keep treating it as an experiment and work on it for my own purposes. Either way the questions got answered, and getting them answered was the point.

There is a lot more in wrapture than fits in an introduction, and I expect to write about specific parts of it in follow-up posts, starting with how it can be used for unit testing, and then tracing a Flask application through to an OpenTelemetry backend without touching the application code. For now the [getting started](https://wrapture.readthedocs.io/en/latest/getting-started.html) page is the place to begin.
