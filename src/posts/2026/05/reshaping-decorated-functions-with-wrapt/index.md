---
title: "Reshaping decorated functions with wrapt"
description: "How wrapt 2.2.0 lets a decorator change what runtime introspection sees of a wrapped function's signature or calling convention."
date: 2026-05-24T18:00:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt", "decorators"]
draft: false
---

Most decorators leave the function's outward shape alone. The same parameters go in, the same return type comes out, and `inspect.signature` and `inspect.iscoroutinefunction` give the same answers they would have given for the undecorated function.

Sometimes you want a decorator that actively changes that shape. Adds or removes a parameter. Changes the return annotation. Turns a sync function into something that should be awaited, or runs an async function to completion so it can be called from sync code. The mechanics of doing the work in the wrapper body are usually straightforward. The harder part is making sure that downstream tools, which decide how to call or treat the function based on what introspection tells them, see the shape of the wrapper rather than the shape of the wrapped target.

`wrapt` has had a partial answer to this for a long time via the `adapter` argument on `@wrapt.decorator`. The 2.2.0 release replaced that with a cleaner standalone `with_signature` decorator and added a new piece, `mark_as_sync` / `mark_as_async`, for the calling-convention side that the existing API did not address at all. There are also a couple of convenience bridges, `async_to_sync` and `sync_to_async`, that do the bridging and the marking together for the common cases.

## What introspection is for

When this post talks about introspection, it means *runtime* introspection. Specifically, the answers given by `inspect.signature`, `inspect.iscoroutinefunction`, `inspect.isasyncgenfunction`, `inspect.isgeneratorfunction` and their friends, computed from the function object after the program has started running.

This is distinct from *static* type checking. mypy and pyright work from source-level type hints before the program runs and rely on different mechanisms (`typing.ParamSpec`, `typing.Concatenate`, properly annotated wrapper signatures and so on). The wrapt decorators in this post fix up runtime introspection. They do not, in general, satisfy a static type checker. That is a separate problem with separate tools.

The runtime side matters because a noticeable amount of modern Python ecosystem behaviour is driven by it. FastAPI inspects function signatures to build request parsing and parameter validation. ASGI frameworks ask `iscoroutinefunction` to decide whether to await a handler directly or dispatch it to a threadpool. `pytest-asyncio` decides whether to treat a test as async based on the same check. Click and Typer build their CLIs from `inspect.signature` of the command function. Sphinx and similar doc tooling pull signatures the same way. Each of these is making a real decision based on what introspection says, and if a decorator silently lies about its shape the decision goes wrong.

## The signature side: the old way

`wrapt` shipped a way to handle this from very early on, via the `adapter` argument on `@wrapt.decorator`. The argument takes a prototype function whose signature is borrowed and presented as the decorated function's:

```python
import wrapt

def _prototype(payload): pass

@wrapt.decorator(adapter=_prototype)
def inject_session(wrapped, instance, args, kwargs):
    return wrapped("session#1", *args, **kwargs)

@inject_session
def handle(session, payload):
    return f"{session} processing {payload}"

import inspect
print("call result      :", handle("hello"))
print("introspected sig :", inspect.signature(handle))
```

Output:

```
call result      : session#1 processing hello
introspected sig : (payload)
```

The user's `handle` function is defined with `(session, payload)`. The decorator hides the `session` parameter and presents the result as `(payload)`, while internally still calling the real `handle` with a session it provides. `inspect.signature` reports the shape the user actually sees, not the underlying.

The `adapter` argument also accepts an `inspect.getfullargspec()` tuple or a formatted argspec string, and there is a `wrapt.adapter_factory(...)` helper for cases where the prototype has to be generated lazily.

The catch is twofold. First, the prototype has to be specified on the decorator factory call, which separates it from the wrapper body and makes the whole thing a little harder to read. Second, the `adapter` argument is being deprecated in favour of the standalone `wrapt.with_signature` decorator described below.

## The signature side: with_signature

The 2.2.0 replacement is `wrapt.with_signature`. It is a standalone decorator that overrides what `inspect.signature` reports for a callable, without changing what the callable actually accepts when called. It takes exactly one of three keyword arguments.

The simplest form is `prototype=`, which borrows the signature from a dummy function:

```python
import inspect, wrapt

def _prototype(payload: str) -> str: pass

@wrapt.with_signature(prototype=_prototype)
def handle(*args, **kwargs):
    return f"session#1 a:{args[0]}"

print("call result :", handle("hello"))
print("signature   :", inspect.signature(handle))
```

Output:

```
call result : session#1 a:hello
signature   : (payload: str) -> str
```

The body of `handle` accepts `*args, **kwargs` because the implementation needs to be flexible (or in the decorator case, because that is what the wrapper signature is). Introspection sees the prototype's `(payload: str) -> str` instead.

The second form is `signature=`, which takes a prebuilt `inspect.Signature` object. This is useful when the parameter list has to be assembled programmatically:

```python
sig = inspect.Signature(
    parameters=[
        inspect.Parameter("payload",
                          inspect.Parameter.POSITIONAL_OR_KEYWORD,
                          annotation=str)
    ],
    return_annotation=str,
)

@wrapt.with_signature(signature=sig)
def handle(*args, **kwargs):
    return f"session#2 b:{args[0]}"
```

The third form is `factory=`, which takes a callable that receives the wrapped function and returns either a `Signature` or a prototype. This is the right choice when the presented signature is derived from the wrapped function's own signature. A factory that strips the first parameter, for instance, would let an "inject the first argument" decorator present whatever the underlying function had with the first slot removed:

```python
def strip_first(wrapped):
    s = inspect.signature(wrapped)
    return s.replace(parameters=list(s.parameters.values())[1:])

@wrapt.with_signature(factory=strip_first)
def handle(*args, **kwargs):
    return f"session#3 c:{args[0]}"
```

When used together with `@wrapt.decorator`, the stacking matters. `with_signature` applies to whatever it directly decorates, so the right place for it is at the use site (above the decorator-built decorator applied to the user's function), or baked into a custom decorator factory that applies it to the wrapped result. Stacking it above a `@wrapt.decorator`-built decorator definition does not propagate the signature override to the final wrapped result.

A clean pattern for an "inject this argument" decorator that uses `with_signature` looks like:

```python
def _prototype(payload): pass

@wrapt.decorator
def _wrap(wrapped, instance, args, kwargs):
    return wrapped("session", *args, **kwargs)

def inject_session(fn):
    return wrapt.with_signature(prototype=_prototype)(_wrap(fn))

@inject_session
def handle(session, payload):
    return f"{session} processing {payload}"
```

`inspect.signature(handle)` reports `(payload)`. The decorator is a regular function that composes `wrapt.decorator` and `wrapt.with_signature` explicitly. A bit more code than the `adapter=` form, but the pieces are more visible, and `wrapt.with_signature` is itself reusable in plenty of cases that have nothing to do with `@wrapt.decorator`.

The important property that `with_signature` only touches *argument-shape* code-object flags. The calling-convention bits are left alone. That cleanly separates this concern from the next one.

## The calling-convention side: the problem

Suppose a third-party decorator (or one you wrote a while back) takes an `async def` function and produces a sync callable that runs the coroutine to completion. The body of the decorated function is async, but the *result* is something you call without `await`. What does `inspect.iscoroutinefunction` say?

```python
import asyncio, inspect, wrapt

@wrapt.decorator
def run_to_completion(wrapped, instance, args, kwargs):
    return asyncio.run(wrapped(*args, **kwargs))

@run_to_completion
async def fetch():
    return 42

print("call result        :", fetch())
print("iscoroutinefunction:", inspect.iscoroutinefunction(fetch))
```

Output:

```
call result        : 42
iscoroutinefunction: True
```

Calling `fetch()` returns `42` because the decorator collapsed the async work to a sync call. But `inspect.iscoroutinefunction(fetch)` still returns `True`, because introspection sees the underlying `async def`. Anything that asks "is this a coroutine function?" to decide what to do with `fetch` will pick the wrong path. An ASGI framework would `await` it. `pytest-asyncio` would treat it as async. Each of those is now making a decision that does not match the actual calling convention.

The mirror case is the same shape in reverse. A plain `def` function wrapped by something that returns a coroutine reads as not-a-coroutine through introspection, but actually requires `await`.

`with_signature` does not help here. It is the wrong tool. The calling-convention bits live in different `co_flags` slots.

## mark_as_sync and mark_as_async

The 2.2.0 answer is a pair of small pass-through decorators that adjust the calling-convention bits and nothing else. They do not bridge anything. They only correct what introspection reports about a stack whose effective convention has already been changed by something else.

The async-to-sync case becomes:

```python
import asyncio, inspect, wrapt

@wrapt.decorator
def run_to_completion(wrapped, instance, args, kwargs):
    return asyncio.run(wrapped(*args, **kwargs))

@wrapt.mark_as_sync
@run_to_completion
async def fetch():
    return 42

print("call result        :", fetch())
print("iscoroutinefunction:", inspect.iscoroutinefunction(fetch))
```

Output:

```
call result        : 42
iscoroutinefunction: False
```

And the symmetric sync-to-async case:

```python
import asyncio, inspect, wrapt

@wrapt.decorator
def schedule(wrapped, instance, args, kwargs):
    async def runner():
        return wrapped(*args, **kwargs)
    return runner()

@wrapt.mark_as_async
@schedule
def compute(x, y):
    return x * y

print("iscoroutinefunction:", inspect.iscoroutinefunction(compute))
print("awaited result     :", asyncio.run(compute(6, 7)))
```

Output:

```
iscoroutinefunction: True
awaited result     : 42
```

It is worth being explicit about what the markers do *not* do. Putting `@wrapt.mark_as_sync` directly on an `async def` does not magically make it sync-callable. It only changes what `iscoroutinefunction` reports. The bridging from one convention to the other has to be done by some other piece of code in the stack. The markers exist so that introspection can be made to match the reality that something else has already established.

### Generator nuance

There are four kinds of callable when you consider the generator/coroutine axes together: plain function, sync generator, coroutine function, async generator. The markers handle all four via an optional `generator=` keyword that takes `None` (default, preserve), `True` (mark as the generator variant of the chosen convention), or `False` (mark as the non-generator variant).

For example, if an inner decorator drains an async generator into a list and presents the result as a plain sync function returning that list, `mark_as_sync(generator=False)` makes introspection see "plain sync function" rather than the underlying "async generator function". The mirror case for async iterables produced from a sync generator uses `mark_as_async(generator=True)`. Most code only needs the default form, but the option is there when both axes need to move at once.

## async_to_sync and sync_to_async

For the common case of actually bridging between conventions, 2.2.0 bundles two convenience decorators. They do the bridging *and* apply the right marker, so introspection lines up without a separate `mark_as_*` step.

`wrapt.async_to_sync` runs the coroutine to completion via `asyncio.run` on each call, and marks the result as sync:

```python
import inspect, wrapt

@wrapt.async_to_sync
async def add(a, b):
    return a + b

print("iscoroutinefunction:", inspect.iscoroutinefunction(add))
print("call result        :", add(2, 3))
```

Output:

```
iscoroutinefunction: False
call result        : 5
```

`wrapt.sync_to_async` is the mirror. It schedules a sync function onto the default executor via `loop.run_in_executor`, and marks the result as async:

```python
import asyncio, inspect, wrapt

@wrapt.sync_to_async
def mul(a, b):
    return a * b

print("iscoroutinefunction:", inspect.iscoroutinefunction(mul))
print("awaited result     :", asyncio.run(mul(4, 5)))
```

Output:

```
iscoroutinefunction: True
awaited result     : 20
```

These are the same family of utility as `asgiref.sync.sync_to_async` and `asgiref.sync.async_to_sync`, which Django leans on heavily for mixing sync and async code. The wrapt versions are smaller and pre-marked, which is the convenient thing. If you need richer behaviour, like explicit executor selection or structured concurrency through `anyio`, the third-party tools are still the right call. In that case you can apply `wrapt.mark_as_sync` or `wrapt.mark_as_async` after the third-party bridge to bring introspection into line:

```python
@wrapt.mark_as_sync
@third_party_async_to_sync
async def work(...):
    ...
```

## Composing both axes

The whole point of keeping `with_signature` and the markers as separate decorators is that they touch different parts of the function's code-object flags and can be combined freely. A decorator that changes both the parameter shape *and* the calling convention works by stacking them in the natural order:

```python
import inspect, wrapt

def _prototype(payload: str) -> int: ...

@wrapt.async_to_sync
@wrapt.with_signature(prototype=_prototype)
async def handler(*args, **kwargs):
    return len(args[0])

print("signature           :", inspect.signature(handler))
print("iscoroutinefunction :", inspect.iscoroutinefunction(handler))
print("call result         :", handler("hello"))
```

Output:

```
signature           : (payload: str) -> int
iscoroutinefunction : False
call result         : 5
```

`with_signature` overrides the signature presented by introspection. `async_to_sync` bridges the async body to a sync call and marks the result accordingly. The two concerns are completely independent and the stacking just falls out of which one needs to be closer to the function (`with_signature`) and which produces the outer wrapper (`async_to_sync`).

## Wrap up

The summary of where to reach for each piece is short.

For *signature* changes, use `wrapt.with_signature` for new code. The `adapter=` argument to `wrapt.decorator` still works and is not going away tomorrow, but it is being deprecated in favour of `with_signature`, which is the cleaner option going forward.

For *calling-convention* changes, where introspection needs to report a different sync/async/generator answer than the underlying function would suggest, use `wrapt.mark_as_sync` or `wrapt.mark_as_async` to correct what introspection reports. Remember that the markers do not bridge anything. They annotate a stack whose effective convention has already been changed.

For the common bridging cases, `wrapt.async_to_sync` and `wrapt.sync_to_async` do the bridging and the marking together. For more sophisticated async runtime needs, keep using `asgiref` or `anyio` and apply the markers afterwards.

The full set of these tools is documented across [signature changing decorators](https://wrapt.readthedocs.io/en/master/decorators.html#signature-changing-decorators), [signature override](https://wrapt.readthedocs.io/en/master/bundled.html#signature-override) and [calling convention markers and adapters](https://wrapt.readthedocs.io/en/master/bundled.html#calling-convention-markers-and-adapters). Release notes are in [the changelog](https://wrapt.readthedocs.io/en/master/changes.html), the latest release is on [PyPi](https://pypi.org/project/wrapt/), and issues go to the [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
