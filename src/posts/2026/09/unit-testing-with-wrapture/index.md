---
title: "Unit testing with wrapture"
description: "The same unit tests written with unittest.mock and with wrapture, focusing on the cases where wrapping the real code rather than replacing it changes what a test can say."
date: 2026-09-01
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing"]
draft: false
---

In [introducing wrapture](/posts/2026/08/introducing-wrapture/) I said the one idea everything sits on is to wrap rather than replace. That is easy to say and harder to see the point of, so this post takes a small piece of code and writes tests for it twice, once with `unittest.mock` and once with wrapture. I am not going to walk through every mock idiom and show its wrapture spelling, since a good part of the time the two are doing the same thing with different syntax, and the [comparison page](https://wrapture.readthedocs.io/en/latest/coming-from-mock.html) in the documentation already maps one onto the other. What I want to show is the handful of cases where the difference is structural, where wrapping the real code lets a test say something that substitution cannot.

## The code under test

An order service which takes a payment through a gateway, records it in a ledger, and sends a notification. If the ledger write fails, the payment is refunded and the error propagates. The collaborators can be injected through the constructor, so there is a seam for a mock to sit behind, and the payment step goes through a private method on the service itself.

```python
class Gateway:
    def charge(self, amount, currency="USD"):
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

    def place(self, amount):
        charge = self._take_payment(amount)
        try:
            self.ledger.record(charge)
        except Exception:
            self.gateway.refund(charge["id"])
            raise
        self.notifier.send(f"order {charge['id']} placed")
        return charge

    def _take_payment(self, amount):
        return self.gateway.charge(amount)
```

## Where the two look the same

Stubbing a return value is the bread and butter of both tools, and on the surface there is nothing to choose between them:

```python
from unittest.mock import patch

def test_stub_with_mock():
    with patch.object(Gateway, "charge", return_value={"id": "stub", "amount": 0}):
        assert OrderService().place(500)["id"] == "stub"
```

```python
import wrapture

def test_stub_with_wrapture():
    with wrapture.binding(Gateway, "charge").on_call.returns({"id": "stub", "amount": 0}):
        assert OrderService().place(500)["id"] == "stub"
```

Even here there is a difference under the surface. A mock only checks a stubbed call against the real signature if you asked for `autospec=True`, so without it a call that has drifted from the method's signature returns the stub happily:

```python
def test_drifted_call_with_mock():
    with patch.object(Gateway, "charge", return_value={"id": "stub"}):
        assert Gateway().charge(500, bogus=True) == {"id": "stub"}
```

That test passes. A wrapture binding is strict by default, so a call the real method would have rejected is rejected by the stub too:

```python
def test_drifted_call_with_wrapture():
    with wrapture.binding(Gateway, "charge").on_call.returns({"id": "stub"}):
        with pytest.raises(TypeError):
            Gateway().charge(500, bogus=True)
```

The error names the site and the problem:

```
TypeError: orders:Gateway.charge (stubbed): got an unexpected keyword argument 'bogus'
```

There is a `strict=False` option for the rare patch which genuinely means to accept a different shape, but the default is the direction I care about. A test which passes because the stub was more forgiving than the real code is a test that will be wrong in production.

## Calls an object makes to itself

The mock approach to testing `OrderService` is to inject a `MagicMock` as the gateway and assert on what it recorded:

```python
from unittest.mock import MagicMock

def test_self_call_with_mock():
    gateway = MagicMock()
    service = OrderService(gateway=gateway)
    service.place(500)
    gateway.charge.assert_called_once_with(500)
```

Look at what the mock actually saw, by printing `gateway.mock_calls` after the call:

```
[call.charge(500),
 call.charge().__getitem__('id'),
 call.charge().__getitem__().__str__(),
 call.charge().__getitem__('id'),
 call.charge().__getitem__().__str__()]
```

The `charge()` call is there, followed by a trail of fabricated chains as the service reached into a return value that was never a real dictionary. What is not there, and cannot be, is `_take_payment()`. The call from `place()` to `_take_payment()` never crosses the seam the mock sits behind, so as far as the test can tell the private method does not exist. If you instead reach for `patch.object(OrderService, "_take_payment")` to get at it, you have replaced it, and now the real payment logic does not run and the gateway is never charged. Either the method is invisible or it is gone.

With wrapture the binding is on the class, so a call the object makes to itself passes through the wrapper like any other:

```python
def test_self_call_with_wrapture():
    take_payment = wrapture.binding(OrderService, "_take_payment")
    charge = wrapture.binding(Gateway, "charge")

    with wrapture.timeline(take_payment, charge) as tape:
        OrderService().place(500)

        take_payment.events.with_args(amount=500).assert_once()
        assert tape.parent_of(charge.events.first) is take_payment.events.first
```

The second assertion says the charge happened inside the payment step, and `tape.tree()` shows the same thing:

```
orders:OrderService._take_payment(amount=500)  -> {'id': 'ch_500', 'amount': 500}
  orders:Gateway.charge(amount=500, currency='USD')  -> {'id': 'ch_500', 'amount': 500}
```

Real arguments, normalised against the real signature so the `currency` default appears even though the caller never passed it, and real return values, nested the way the calls actually nested.

## Running the real code while changing one thing

This is where substitution runs out of road entirely. `Mock(wraps=real)` will forward calls to the real method, but it cannot change the arguments the real method receives, and it cannot touch the result on the way back. The standard library has no way to say "run the real method, but change one thing about it".

For wrapture that is the ordinary case. Here the real `charge()` runs and only the id in its result is rewritten, which is useful when a real id would be unstable across runs but everything else about the result matters:

```python
def test_pinned_result_with_wrapture():
    charge = wrapture.binding(Gateway, "charge")
    charge.on_call.transforms_result(lambda r: {**r, "id": "ch_TEST"})

    with charge:
        assert OrderService().place(500) == {"id": "ch_TEST", "amount": 500}
```

`transforms_args()` does the same on the way in, and `validates_args()` and `validates_result()` check without changing. These are stages, and they compose, so a binding can rewrite one argument and check the result at the same time while the real code does the actual work in between.

## Asserting on what did not happen

The tests that matter most are usually on the error paths, and the interesting fact on an error path is often an absence. When the ledger write fails, the refund must be issued and the notification must not be sent. Here it is with mock, and it takes three doubles to write:

```python
def test_error_path_with_mock():
    gateway = MagicMock()
    ledger = MagicMock()
    ledger.record.side_effect = OSError("disk full")
    notifier = MagicMock()

    service = OrderService(gateway, ledger, notifier)

    with pytest.raises(OSError):
        service.place(500)

    gateway.refund.assert_called_once_with(gateway.charge.return_value["id"])
    notifier.send.assert_not_called()
```

The refund assertion is the awkward part. Because the gateway is a mock, the charge id is a fabricated `MagicMock` rather than `"ch_500"`, so the only way to assert on it is to ask the mock what it invented. The test cannot say "the refund was for the charge that was taken", only "the refund was passed whatever `charge()` returned", which is the same thing only if you trust the code you are testing. (With a plain `Mock` rather than `MagicMock` the test does not even get that far, since `charge["id"]` fails with a `TypeError` about subscripting.)

With wrapture the failure is injected at the ledger and nothing else is touched:

```python
def test_error_path_with_wrapture():
    charge = wrapture.binding(Gateway, "charge")
    refund = wrapture.binding(Gateway, "refund")
    record = wrapture.binding(Ledger, "record")
    send = wrapture.binding(Notifier, "send")

    record.on_call.raises(OSError("disk full"))

    with wrapture.timeline(charge, refund, record, send) as tape:
        with pytest.raises(OSError):
            OrderService().place(500)

        refund.events.with_args(charge_id="ch_500").assert_once()
        send.events.assert_never()
        tape.assert_order(charge, record, refund)
```

The real gateway was charged, so the refund is asserted against the real charge id. The notifier is real and was never called. And `assert_order()` says the refund came after the failed ledger write, across three different bindings. The tape shows exactly that:

```
orders:Gateway.charge(amount=500, currency='USD')  -> {'id': 'ch_500', 'amount': 500}
orders:Ledger.record(entry={'id': 'ch_500', 'amount': 500})  !! OSError (injected)
orders:Gateway.refund(charge_id='ch_500')  -> {'id': 're_ch_500'}
```

When an assertion fails, the message shows what was recorded rather than just the count that was wrong. Asserting on a refund for the wrong id gives:

```
AssertionError: expected exactly 1 event(s), got 0
<EventLog orders:Gateway.refund[charge_id='ch_999']: 0 event(s)>
    (no events)
  filtered from:
    <EventLog orders:Gateway.refund: 1 event(s)>
        orders:Gateway.refund(charge_id='ch_500')
```

The "filtered from" section is there because an over-narrowed filter producing an empty log is the easiest way to get a wrong assertion, and showing what the filter discarded is the fastest way to see it.

## How the tests are shaped

Beyond what the assertions can say, the shape of the test code changes in a few ways that are worth pointing out.

A binding declares a target without touching it. `binding()` never patches, so bindings can be created at module scope, given behaviour, and shared, with each test applying and removing them. Nothing happens until `apply()`, a `with` block, or a timeline. That separation of declaration from effect is what lets the four bindings in the error path test be declared up front and read like a cast list.

The `with` block is the primitive, and for a test that binds one or two targets around its whole body there is a decorator form that says the same thing without the nesting. The bindings arrive as keyword arguments, and expectations can be declared on the decorator and are verified when the test finishes:

```python
@wrapture.taped()
@wrapture.bound(Ledger, "record").on_call.raises(OSError("disk full"))
@wrapture.bound(Gateway, "refund").expect_once()
@wrapture.bound(Notifier, "send").expect_never()
def test_error_path_with_decorators(tape, record, refund, send):
    with pytest.raises(OSError):
        OrderService().place(500)
```

That is the same test as before with the assertions moved to the top as a contract, and a body that only performs the action. An expectation with nothing recording is an error rather than a silent pass.

Fixtures work the way you would expect, and because a fixture yields the binding a test can reconfigure it mid-flight, which is how a test walks a collaborator through failing and then recovering:

```python
@pytest.fixture
def stub_charge():
    with wrapture.binding(Gateway, "charge").on_call.returns({"id": "stub", "amount": 0}) as charge:
        yield charge


def test_gateway_recovers(stub_charge):
    stub_charge.on_call.raises(TimeoutError("down"))
    with pytest.raises(TimeoutError):
        OrderService().place(500)

    stub_charge.on_call.returns({"id": "retry", "amount": 0})
    assert OrderService().place(500)["id"] == "retry"
```

Finally there is an opt-in pytest plugin, enabled with one line in `conftest.py`, which fails any test that leaves a binding applied and attaches the tape's tree to the failure report of any test that recorded one. The leak sweep is the thing I would turn on first. A patch that leaks changes the behaviour of every test that runs after it, and I suspect plenty of people have lost hours to that without ever knowing which test was the culprit.

## Where mock still fits

Everything above follows one rule, which is to wrap the real code and record what actually flowed, with one deliberate opt-out. When the test itself must supply the thing being called, because the code under test receives a callback or a collaborator rather than importing one, `stub()` supplies a single callable and `mock(Spec)` a whole object. Both are strict, in that signatures are checked and a name the spec does not have raises, and both record onto the same tape as everything else.

What wrapture does not provide is a spec-less `MagicMock()` whose attributes exist on first touch and whose call chains all answer. That is the thing which would let a misspelled `gateway.chargee.assert_not_called()` pass silently in the tests above, and it is left out on purpose. If a test wants an object invented as it is touched, `unittest.mock` is the tool for that, and it has the other advantage of being in the standard library, on every team's common ground. The two coexist in one suite without difficulty, and the comparison page is there for translating between them.

## What's next

The error path test leaned on the timeline and the tape without much explanation of what they are or what an event holds. That is the subject of the next post, where the example is a resource leak, which is a bug nothing in a return value will ever tell you about.
