---
title: "Phased behaviour in wrapture"
description: "Testing retry logic, circuit breakers and polling loops with wrapture's phases, where a binding's behaviour changes on a count, a condition, an exhausted sequence, or a signal from elsewhere."
date: 2026-09-03
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing"]
draft: false
---

Most of what a test configures on a patch holds until the test changes it. Retry logic is the classic case where that is not enough: the code under test keeps calling, and the test needs the behaviour to change on its own as it does. Fail twice and then succeed. Hand out a sequence of canned responses. Run the real thing until it breaks and then fail fast. `unittest.mock` handles the first two of those with a list passed as `side_effect`, consumed one entry per call. wrapture models the same idea as phases, and this post is about what that buys you beyond the list.

## The code under test

A client that fetches a URL, and a function that retries on a timeout:

```python
class Client:
    def fetch(self, url):
        if "bad" in url:
            raise ConnectionError(f"cannot reach {url}")
        return {"url": url, "status": 200}


def fetch_with_retry(client, url, attempts=3):
    for attempt in range(1, attempts + 1):
        try:
            return client.fetch(url)
        except TimeoutError:
            if attempt == attempts:
                raise
```

With mock the retry test is a `side_effect` list, and it works fine:

```python
with patch.object(Client, "fetch", side_effect=[TimeoutError("busy"), TimeoutError("busy"), {"url": "/x", "status": 200}]):
    assert fetch_with_retry(Client(), "/x") == {"url": "/x", "status": 200}
```

What the list cannot say is "and then run the real code". Every entry is a fabricated outcome, so the third call is a canned dictionary rather than the real `fetch()`, and the test proves the loop retries but not that the real method is what it eventually reaches.

## Phases

In wrapture the behaviour configured on `on_call` is phase 0, and `then()` adds the phase that takes over from it, with the argument saying when the hand-over happens. Each phase is a complete behaviour of its own with the full vocabulary, and nothing is inherited between them, so a phase with no terminal runs the real operation:

```python
fetch = wrapture.binding(Client, "fetch")
fetch.on_call.raises(TimeoutError("busy"))

recovered = fetch.on_call.then(after=2)
recovered.passes_through()
```

The first two calls raise, and every call after that is real. Stating `passes_through()` on a fresh phase is optional, since that is what an empty phase does anyway, but worth writing when running the real thing is the point of the phase. Recording it shows the hand-over, and the tape marks which outcomes were injected and which were real:

```python
with wrapture.timeline(fetch) as tape:
    print(fetch_with_retry(Client(), "/orders"))
    print(tape.tree())
```

```
{'url': '/orders', 'status': 200}
__main__:Client.fetch(url='/orders')  !! TimeoutError (injected)
__main__:Client.fetch(url='/orders')  !! TimeoutError (injected)
__main__:Client.fetch(url='/orders')  -> {'url': '/orders', 'status': 200}
```

Each event carries the index of the phase that handled it, so the recording can be filtered by regime, and the binding knows which phase it is in:

```python
fetch.events.in_phase(0).assert_times(2)
fetch.events.in_phase(1).assert_once()
assert fetch.phase == 1
```

`binding.phase` is the index of the phase currently active, and `in_phase()` filters the recorded events to those a given phase handled. The two answer different questions, since a phase can be entered and left without handling a call. Phases restart at 0 on every `apply()`, so a binding handed to `timeline()` starts its script afresh in each test that uses it.

The give-up path is the same binding with a bigger count. With `then(after=3)` all three attempts raise, `fetch_with_retry()` re-raises the last one, and the tape shows three injected failures and no real call.

The verbs on a phase return the phase, so a phase can be configured in one chain, `then(after=1).validates_args(check).returns(b)`. Holding it in a variable named for what the phase is, and configuring it line by line as with `on_call`, usually reads better, and it is the style I would use in a test.

## Ending a phase on a condition

A count is one of three ways a phase can end. `then(until=fn)` ends the phase once `fn(event)` is true for a call it handled. The event is the same one a timeline would record, seen as the caller saw it, so the condition can look at the arguments, the result, or whether the call raised. That is enough to build a circuit breaker: run the real call until one fails, then fail fast without touching the remote at all.

```python
class CircuitOpen(Exception):
    pass


def failed(event):
    return event.exception is not None


fetch = wrapture.binding(Client, "fetch")
fetch.on_call.passes_through()

tripped = fetch.on_call.then(until=failed)
tripped.raises(CircuitOpen("circuit open"))
```

Fetch two good URLs, one bad one that the real `fetch()` rejects, and then another good one:

```
__main__:Client.fetch(url='/a')  -> {'url': '/a', 'status': 200}
__main__:Client.fetch(url='/b')  -> {'url': '/b', 'status': 200}
__main__:Client.fetch(url='/bad')  !! ConnectionError
__main__:Client.fetch(url='/c')  !! CircuitOpen (injected)
```

The `ConnectionError` is real, raised by the real method for a real reason, and the `CircuitOpen` after it is the binding's. A `side_effect` list has no way to express a phase whose boundary depends on what the real code did.

## Sequences

For "return the next value on each call" a phase per value would be tiresome, so `returns_from(iterable)` is a terminal that draws successive values, one per call, lazily. A generator or `itertools.cycle()` works. When the sequence runs out the phase ends and the call that found it empty is handled by the successor, so a bare `then()` after a sequence means "when it is exhausted". A polling loop is the natural example:

```python
class Job:
    def status(self):
        return "done"


def wait_for(job, polls=5):
    for _ in range(polls):
        if job.status() == "done":
            return True
    return False


status = wrapture.binding(Job, "status")
status.on_call.returns_from(["queued", "running", "running"])

settled = status.on_call.then()
settled.returns("done")
```

```
__main__:Job.status()  -> 'queued' (injected)
__main__:Job.status()  -> 'running' (injected)
__main__:Job.status()  -> 'running' (injected)
__main__:Job.status()  -> 'done' (injected)
```

This is the closest thing to mock's `side_effect` list, and the deliberate difference is that values and exceptions are kept apart. `side_effect=[a, b, Err]` becomes `returns_from([a, b])` followed by a phase that `raises(Err)`, which is more lines for the same three outcomes but each phase says what it is. Running out with no successor is a loud `SequenceExhaustedError` at the call site rather than a `StopIteration` leaking out of the code under test, and the message says to add a phase with `then()` or supply an endless sequence.

A known sequence of "random" numbers is another use, making code that jitters or samples deterministic without seeding tricks: `binding(random, "random").on_call.returns_from([0.1, 0.9, 0.5])`.

## Advancing from outside

The third way a phase ends is that something other than this binding's own calls decides it should. A bare `then()` with no condition ends only when the test calls `binding.advance()`, which also works whatever the exit condition, so a test can force the next phase early. The simplest use is a test that sits between calls:

```python
remote = wrapture.binding(Client, "fetch")
remote.on_call.raises(ConnectionError("down"))
remote.on_call.then().passes_through()

with remote:
    client = Client()

    with pytest.raises(ConnectionError):
        client.fetch("/x")

    remote.advance()
    assert client.fetch("/x")["status"] == 200
```

The more interesting use is when the trigger lives in a different binding. Here the remote stays down until a health check, itself a binding, reports it healthy, and the health check's own result stage advances the remote:

```python
class Monitor:
    def check(self):
        return "healthy"


remote = wrapture.binding(Client, "fetch")
remote.on_call.raises(ConnectionError("down"))

online = remote.on_call.then()
online.passes_through()

health = wrapture.binding(Monitor, "check")
health.on_call.returns_from(["unhealthy", "unhealthy", "healthy"])
health.on_call.then().returns("healthy")


def note_recovery(result):
    if result == "healthy":
        remote.advance()


health.on_call.validates_result(note_recovery)
```

Run code that polls the monitor and tries the client each time round, and the tape shows the two scripts interleaving:

```
__main__:Monitor.check()  -> 'unhealthy' (injected)
__main__:Client.fetch(url='/x')  !! ConnectionError (injected)
__main__:Monitor.check()  -> 'unhealthy' (injected)
__main__:Client.fetch(url='/x')  !! ConnectionError (injected)
__main__:Monitor.check()  -> 'healthy' (injected)
__main__:Client.fetch(url='/x')  -> {'url': '/x', 'status': 200}
```

Note that a stage such as `validates_result()` belongs to the phase it was configured on, which follows from phases inheriting nothing from each other. That is why `"healthy"` is the last value of the phase 0 sequence above rather than the value the successor phase returns; if the stage were on phase 0 and the triggering value only ever came from phase 1, the recovery would never be noticed. A stage that should run in every phase is configured in every phase. When the condition is visible in the binding's own calls, `then(until=...)` says it more directly than a stage calling `advance()`, and is the form to reach for first.

## Where phases fit in a test

Phases are for behaviour that must change within one call of the code under test, as it happens with a retry loop, a breaker, or a polling wait. A test that sits between calls does not need them; it reconfigures the binding in place, `on_call.returns(...)` again, and carries on. That is why the decorator form deliberately leaves `then()` out of its chain: how behaviour changes over time is the test's script, and it is configured in the body through the injected handle, where the phase markers can be given names.

The attribute channels have phases too, `on_get` in particular has `returns_from()`, so a module constant can read one way for two reads and then another, which I will come back to in the next post. And `passes_through()` on a base namespace clears phase 0 only; to drop the whole chain and start again, `on_call.reset()` is the tool.

## What's next

Everything in this series so far has been about calls. The next post is about everything a binding can name that is not a call: attribute reads and writes, a value held in a slot for the duration of a test, the whole content of a settings dict, and what happens item by item as a generator is consumed.
