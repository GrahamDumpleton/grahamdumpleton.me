---
title: "Async support for wrapt.synchronized"
description: "How wrapt 2.2.0 extends the synchronized decorator and context manager to async functions, and why reentrancy is not supported on the async side."
date: 2026-05-24T20:00:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt", "decorators", "asyncio"]
draft: false
---

Continuing the tour through the `wrapt` 2.2.0 release, the last piece worth a closer look is the new async support in `wrapt.synchronized`. The decorator has been part of `wrapt` from the start, but until 2.2.0 it only really did the right thing for synchronous code. Applying it to an `async def` function used to give the appearance of working without actually serialising anything, and the context manager form had no async variant at all. Both are now fixed.

## A quick recap of synchronized

`wrapt.synchronized` is the bundled decorator for ensuring that a callable is only executed by one caller at a time. The lock it acquires is created lazily and attached to the right object depending on what is being decorated: a per-function lock for plain functions, a per-instance lock for instance methods, a per-class lock for class methods or when the decorator is applied to a class body, and so on. None of that bookkeeping is the caller's responsibility.

```python
import wrapt

class Counter:
    def __init__(self):
        self.value = 0

    @wrapt.synchronized
    def increment(self):
        self.value += 1
```

There is also a context manager form, where you supply the object that should own the lock. The decorator form and the context manager form share the same auto-created lock when they name the same object, so they can be mixed freely:

```python
counter = Counter()

with wrapt.synchronized(counter):
    counter.value += 1
```

The lock used in both cases is a `threading.RLock`. That choice matters and I will come back to it.

## Where it fell apart on async

Applying the same decorator to an `async def` method in `wrapt` 2.1.x looked promising at first glance. The call returned a coroutine, awaiting it ran the body, and nothing raised. It was only when you tried it under contention that the problem became visible:

```python
import asyncio
import wrapt

class Counter:
    def __init__(self):
        self.value = 0

    @wrapt.synchronized
    async def inc(self):
        cur = self.value
        await asyncio.sleep(0.01)
        self.value = cur + 1

async def main():
    c = Counter()
    await asyncio.gather(*(c.inc() for _ in range(10)))
    print(c.value)

asyncio.run(main())
```

Run under `wrapt` 2.1.2, this prints `1`. Ten tasks all read `cur = 0`, all sleep, all write `1` back. The lock attached to the instance was a `threading.RLock`, and it was acquired and released around the construction of the coroutine, not around the awaited body. By the time anything interesting happened, the lock was gone.

The context manager form did not help either. There was no `async with` support, so writing:

```python
async with wrapt.synchronized(counter):
    ...
```

failed with an `AttributeError` complaining about a missing `__aenter__`. If you wanted serialised access to a shared resource from async code, you were on your own.

## What 2.2.0 changes

In 2.2.0 the decorator inspects the wrapped function and picks a different locking primitive when it sees a coroutine function:

```python
import asyncio
import wrapt

class Counter:
    def __init__(self):
        self.value = 0

    @wrapt.synchronized
    async def inc(self):
        cur = self.value
        await asyncio.sleep(0.01)
        self.value = cur + 1

async def main():
    c = Counter()
    await asyncio.gather(*(c.inc() for _ in range(10)))
    print(c.value)

asyncio.run(main())
```

This now prints `10`. The wrapper still returns a coroutine, but the lock acquisition and release happen inside that coroutine using `await`, so the awaited body is actually serialised across tasks.

The lock attached to the instance in this case is an `asyncio.Lock`, stored under a different attribute (`_synchronized_async_lock`) than the synchronous version (`_synchronized_lock`). A class that mixes synchronous and asynchronous synchronized methods on the same instance therefore gets two distinct locks, which is what you want, because mixing `threading` and `asyncio` primitives on the same lock would not work anyway.

The context manager form has gained an async variant alongside the synchronous one. The same call now supports both spellings, picking the right behaviour based on whether you write `with` or `async with`:

```python
async with wrapt.synchronized(counter):
    counter.value += 1
```

For plain async functions, async classmethods, and any other shape that `wrapt`'s decorator machinery already knew how to dispatch on, the same rule applies. If the wrapped callable is `async def`, you get an `asyncio.Lock` and an async wrapper. If it is not, you get a `threading.RLock` and a synchronous wrapper. The choice between them is automatic.

## The reentrancy difference

There is one place where the synchronous and asynchronous paths deliberately do not match up: the synchronous lock is reentrant and the asynchronous lock is not. Calling a synchronized method from inside another synchronized method on the same instance is fine in the synchronous case, because `threading.RLock` allows the same thread to acquire the lock more than once. The async equivalent deadlocks:

```python
import asyncio
import wrapt

class A:
    @wrapt.synchronized
    async def outer(self):
        return await self.inner()

    @wrapt.synchronized
    async def inner(self):
        return "done"

async def main():
    a = A()
    try:
        result = await asyncio.wait_for(a.outer(), timeout=0.5)
        print(result)
    except asyncio.TimeoutError:
        print("deadlocked")

asyncio.run(main())
```

This prints `deadlocked`. The same `outer` then `inner` chain on synchronous methods would print `done` and move on.

The reason the async case behaves this way is that the standard library does not provide a reentrant async lock. There is no `asyncio.RLock`, only `asyncio.Lock`. Whether one ought to exist has been a recurring discussion on the Python issue tracker and on discuss.python.org for the better part of a decade, and the short version is that there is no agreement.

The case for adding one is the obvious one. Code being ported from a synchronous codebase often relies on the reentrancy of `threading.RLock` to allow public methods that take a lock to call other public methods that take the same lock. Without a reentrant async equivalent, the same restructuring work has to be done by hand.

The case against is partly about scope (every primitive in the standard library carries a maintenance cost) and partly about the conceptual mismatch between threads and tasks. `threading.RLock` is reentrant per thread, and a thread is a long-lived identity that a function can simply ask about. The analogous identity in async code is the current task, which is well defined but feels less stable to reason about: tasks are cheap, can be created mid-call, and suspend at every `await`. A reentrant lock keyed on the current task can paper over genuine design problems where one task ends up holding a lock across an `await` that gives another piece of code a chance to re-enter, in ways that are much easier to spot when the lock simply refuses to be acquired twice.

There are third-party packages that implement reentrant async locks for people who want them, but `wrapt` deliberately stays in step with the standard library here. The synchronous side uses `threading.RLock` because that is what the standard library provides; the async side uses `asyncio.Lock` for the same reason.

The practical consequence is that the usual workaround for non-reentrant locks applies on the async side. Public methods that acquire the lock should delegate to private helpers that assume the lock is already held:

```python
import asyncio
import wrapt

class Counter:
    def __init__(self):
        self.value = 0

    @wrapt.synchronized
    async def add_two(self):
        await self._incr()
        await self._incr()
        return self.value

    async def _incr(self):
        cur = self.value
        await asyncio.sleep(0.001)
        self.value = cur + 1

async def main():
    c = Counter()
    await asyncio.gather(*(c.add_two() for _ in range(5)))
    print(c.value)

asyncio.run(main())
```

That prints `10`, with the lock acquired exactly once per call to `add_two`. The pattern is a bit more disciplined than relying on reentrancy, but it makes the locking boundaries explicit, which is no bad thing in async code.

## Wrapping up

The full set of changes to `wrapt.synchronized` is in [the changelog](https://wrapt.readthedocs.io/en/master/changes.html), and the decorator itself is documented on [the bundled decorators page](https://wrapt.readthedocs.io/en/master/bundled.html#thread-synchronization). The feature is in `wrapt` from 2.2.0 onwards, with the usual recommendation to grab the latest release from [PyPi](https://pypi.org/project/wrapt/) since there have been follow-up releases on the 2.2.x branch. Issues and questions, as ever, go to the [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
