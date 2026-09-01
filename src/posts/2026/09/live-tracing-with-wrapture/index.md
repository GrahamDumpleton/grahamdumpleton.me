---
title: "Live tracing with wrapture"
description: "The bindings used to test a piece of code are the same objects that trace it. Take away the timeline, register a sink, and a running program narrates itself."
date: 2026-09-07
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "tracing"]
draft: true
---

When I wrote about [unit testing with wrapture](/posts/2026/09/unit-testing-with-wrapture/) the pattern in every test was the same: create a binding on a method, open a `timeline()`, run the code, and read the recorded calls off the tape. What I did not say at the time is that nothing about a binding is specific to testing. A binding observes a call site and emits events, and what happens to those events is decided by whoever is listening. In a test the listener is a tape. Take the tape away and register something else, and the same binding narrates a running program as it goes.

That is the whole idea behind the tracing side of wrapture, and this post is the minimal version of it: the shop from the testing series, three bindings, and one sink.

## The shop

The code is the order service from the earlier posts, grown just enough to have something worth watching. A card number now travels with the order, the gateway declines cards ending in four zeros, and each order belongs to a tenant.

```python
class CardDeclined(Exception):
    pass


class Gateway:
    def charge(self, amount, card):
        if card.endswith("0000"):
            raise CardDeclined(f"card ending {card[-4:]} declined")
        return {"id": f"ch_{amount}", "amount": amount}

    def refund(self, charge_id):
        return {"id": f"re_{charge_id}"}


class Ledger:
    def record(self, entry):
        return f"led_{entry['id']}"


class Notifier:
    def send(self, message):
        return True


class OrderService:
    def __init__(self, gateway=None, ledger=None, notifier=None):
        self.gateway = Gateway() if gateway is None else gateway
        self.ledger = Ledger() if ledger is None else ledger
        self.notifier = Notifier() if notifier is None else notifier

    def place(self, amount, card, tenant):
        charge = self._take_payment(amount, card)
        try:
            self.ledger.record(charge)
        except Exception:
            self.gateway.refund(charge["id"])
            raise
        self.notifier.send(f"order {charge['id']} placed")
        return charge

    def _take_payment(self, amount, card):
        return self.gateway.charge(amount, card)
```

That lives in `shop.py`. A second module, `orders.py`, places three orders, one of which will be declined:

```python
from shop import CardDeclined, OrderService

ORDERS = [
    (500, "4111-1111-1111-1111", "acme"),
    (250, "4000-0000-0000-0000", "globex"),
    (120, "5555-4444-3333-2222", "globex"),
]


def run():
    service = OrderService()
    for amount, card, tenant in ORDERS:
        try:
            service.place(amount, card, tenant=tenant)
        except CardDeclined:
            pass
```

The question to answer is a simple one. When an order is placed, what actually happens? Which methods run, with what, and what comes back? A log line would answer that only in the places where someone had already thought to add one, and this code has none.

## Three bindings and a sink

The entry point applies a binding to each of the three methods that matter and registers a `Printer`, which is the simplest sink wrapture ships: it prints each event to standard error as it happens.

```python
import wrapture

from shop import Gateway, Ledger, OrderService
import orders

wrapture.binding(OrderService, "place").apply()
wrapture.binding(Gateway, "charge").apply()
wrapture.binding(Ledger, "record").apply()

wrapture.add_sink(wrapture.Printer())

orders.run()
```

There is no `timeline()` anywhere in that. The bindings are applied for the life of the process, the sink is registered for the life of the process, and events flow from one to the other. Running it, the output is:

```
shop:OrderService.place(amount=500, card='4111-1111-1111-1111', tenant='acme')
  shop:Gateway.charge(amount=500, card='4111-1111-1111-1111')
  shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [8us]
  shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})
  shop:Ledger.record -> 'led_ch_500' [6us]
shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [239us]
shop:OrderService.place(amount=250, card='4000-0000-0000-0000', tenant='globex')
  shop:Gateway.charge(amount=250, card='4000-0000-0000-0000')
  shop:Gateway.charge !! CardDeclined [5us]
shop:OrderService.place !! CardDeclined [60us]
shop:OrderService.place(amount=120, card='5555-4444-3333-2222', tenant='globex')
  shop:Gateway.charge(amount=120, card='5555-4444-3333-2222')
  shop:Gateway.charge -> {'id': 'ch_120', 'amount': 120} [4us]
  shop:Ledger.record(entry={'id': 'ch_120', 'amount': 120})
  shop:Ledger.record -> 'led_ch_120' [3us]
shop:OrderService.place -> {'id': 'ch_120', 'amount': 120} [104us]
```

Each operation gets a line when it begins, indented by how deeply it is nested, and a closing line with the outcome and how long it took. A `->` marks a return value and `!!` marks an exception, so the declined card is visible at a glance, and so is the fact that `Ledger.record` never ran for that order. These are the real arguments and the real results, the same `->` and `!!` markers that `tape.tree()` uses in a test, only arriving live rather than being reconstructed afterwards.

The first thing I noticed in that output is something the trace should not contain. The card numbers are in it, in full, because the bindings captured the arguments as given. The same `redact()` capture policy the testing series used for keeping secrets off a tape works here, since the binding is the same object:

```python
wrapture.binding(OrderService, "place", capture=wrapture.redact("card")).apply()
wrapture.binding(Gateway, "charge", capture=wrapture.redact("card")).apply()
```

With that in place the opening lines read `card='<redacted>'` and everything else is unchanged. I have left it on for the rest of the post, since a trace that is going to be looked at, streamed to a file, or sent anywhere, is exactly the place a card number should not be.

## What it costs when nobody is listening

The obvious worry about leaving bindings applied in a program is what they cost when nothing is being traced. The recording gate in wrapture is not "is there a timeline" but "is anything listening". A tape scoped to a test is one kind of listener, a process sink is another, and when neither is present an applied binding constructs no event at all. The wrapped method runs with only wrapt's own dispatch on top, which the documentation puts at about half a microsecond per call on the machine it was measured on. That is what makes it reasonable to bind the interesting methods once, in the entry point, and let the sink decide whether anything is recorded.

## Seeing less

Three orders is a readable trace. Three thousand is not, and the answer is rarely to bind fewer things, because the point of binding the layers is to have them there when a question comes up. The tools for narrowing sit either at the sink or at the binding.

At the sink, combinators wrap a sink and gate what reaches it. `Depth(1, ...)` forwards only the roots of each tree, which turns the trace into one opening and one closing line per order:

```python
wrapture.add_sink(wrapture.Depth(1, wrapture.Printer()))
```

```
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [149us]
shop:OrderService.place(amount=250, card='<redacted>', tenant='globex')
shop:OrderService.place !! CardDeclined [33us]
shop:OrderService.place(amount=120, card='<redacted>', tenant='globex')
shop:OrderService.place -> {'id': 'ch_120', 'amount': 120} [46us]
```

At the binding, `when=` takes a predicate that is consulted before any event exists. A falsey answer means no event is constructed, no arguments are captured and nothing is delivered, which is the cheap way to narrow a hot call site. Here it records orders for one tenant only:

```python
def acme_only(instance, args, kwargs):
    return kwargs.get("tenant") == "acme"

place = wrapture.binding(OrderService, "place", when=acme_only,
                         capture=wrapture.redact("card")).apply()
```

Running the three orders again gives this:

```
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
  shop:Gateway.charge(amount=500, card='<redacted>')
  shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [7us]
  shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})
  shop:Ledger.record -> 'led_ch_500' [6us]
shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [245us]
shop:Gateway.charge(amount=250, card='<redacted>')
shop:Gateway.charge !! CardDeclined [5us]
shop:Gateway.charge(amount=120, card='<redacted>')
shop:Gateway.charge -> {'id': 'ch_120', 'amount': 120} [4us]
shop:Ledger.record(entry={'id': 'ch_120', 'amount': 120})
shop:Ledger.record -> 'led_ch_120' [4us]
```

The globex orders are gone, but their gateway and ledger calls are not. A `when=` decline skips exactly one event, the declined operation's own, and whatever records beneath it still records, now with nothing above it, so each inner call turns up as an anonymous root with no `place` to explain it. Sometimes that is exactly what you want, since a binding whose only job is to intervene in a call should not silence what runs beneath it. When the intent is "nothing from here down", `tree=True` says so:

```python
place = wrapture.binding(OrderService, "place", when=acme_only, tree=True,
                         capture=wrapture.redact("card")).apply()
```

```
shop:OrderService.place(amount=500, card='<redacted>', tenant='acme')
  shop:Gateway.charge(amount=500, card='<redacted>')
  shop:Gateway.charge -> {'id': 'ch_500', 'amount': 500} [7us]
  shop:Ledger.record(entry={'id': 'ch_500', 'amount': 500})
  shop:Ledger.record -> 'led_ch_500' [6us]
shop:OrderService.place -> {'id': 'ch_500', 'amount': 500} [251us]
```

Now the decline covers the whole extent of the declined operation, and the trace is one tenant's orders and nothing else. The skipped calls are not simply lost, either. Each binding counts the operations it declined on `filtered_calls`, and after this run `place`, `charge` and `record` report 2, 2 and 1 respectively (the second globex order raised before reaching the ledger), so a trace shorter than expected can be explained rather than guessed at.

## Where this leaves things

The whole intervention is a few lines in the program's entry point: bind the methods that matter, register a sink, and the program describes what it is doing as it runs, with real arguments and real results, and costs next to nothing when nothing is listening. The sink protocol itself is three notifications, so a sink that counts, samples, filters, or writes somewhere of your own is a small class, and the [ad-hoc tracing page](https://wrapture.readthedocs.io/en/latest/ad-hoc-tracing.html) of the documentation covers that side, along with the other combinators and the collectors that keep numbers rather than events.

Those few lines in the entry point are still lines in the program, though. For code you cannot or would rather not edit, they can move out of the program entirely, into a file that sits next to it.
