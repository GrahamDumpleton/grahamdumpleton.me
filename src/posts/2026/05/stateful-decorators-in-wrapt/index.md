---
title: "Stateful decorators in wrapt"
description: "A walkthrough of the new bind_state_to_wrapper helper in wrapt 2.2.0 and how it makes stateful decorators in Python easier to write."
date: 2026-05-24T11:55:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt", "decorators"]
draft: false
---

A new version of `wrapt` was released earlier this week. Version 2.2.0 introduces a small helper that makes it noticeably easier to write decorators that need to keep state across calls. It is the kind of thing that does not look like much until you try to write the equivalent code without it, so it is worth a closer look.

The full release notes are in [the changelog](https://wrapt.readthedocs.io/en/master/changes.html). What I want to walk through here is the stateful decorator side of the release, because it touches on something that has always been a bit awkward in plain Python.

## Why a decorator might need state

The idea of a stateful decorator is straightforward enough. You attach a wrapper to a function, and the wrapper remembers something across invocations. Counting how many times the function has been called is the canonical example. Other examples include accumulating timing statistics, caching results in a way you want to inspect, tracking which arguments have been seen, or maintaining a registry of what the wrapped function has done.

The complication is not the bookkeeping itself, it is exposing the state back to the caller. If a decorator is purely passive and does its work without anyone ever needing to look at the internals, state can live in a closure and nobody is any the wiser. Once you decide that the user of the decorated function should be able to ask "how many times has this been called?", you need a way to reach into that state from the outside.

## The closure approach

The simplest pattern in plain Python is to push state onto the wrapper function as an attribute:

```python
import functools

def call_tracker(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            wrapper.call_count += 1
    wrapper.call_count = 0
    return wrapper

@call_tracker
def add(x, y):
    return x + y

add(1, 2)
add(3, 4)
print(add.call_count)
```

Running this prints `2`. That works fine for a regular function, but the moment you apply the same decorator to an instance method things get more subtle. The wrapper itself is still a function, so the descriptor protocol kicks in and `self` is passed through correctly. The state however lives on the single wrapper object that was created at class definition time, so it is shared across every instance of the class. Whether that is what you want depends on the use case, but you have no real control over it from the way the decorator is written.

## The class approach

If you want to keep both the state and the wrapper logic together, the next natural step is to write the decorator as a class:

```python
import functools

class CallTracker:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.call_count = 0

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        finally:
            self.call_count += 1

@CallTracker
def add(x, y):
    return x + y

add(1, 2)
print(add.call_count)
```

This works for plain functions. The problem appears when the same decorator is applied to a method:

```python
class Calculator:
    @CallTracker
    def add(self, x, y):
        return x + y

Calculator().add(1, 2)
```

That raises `TypeError: add() missing 1 required positional argument: 'y'`. The reason is that `Calculator.add` is now a `CallTracker` instance rather than a function. When the attribute is looked up via an instance, the descriptor protocol does not kick in, because instances of user-defined classes are not descriptors by default. The `Calculator` instance is therefore never bound to `self` in the wrapped function, and the call sees `x` as `1` with no value for `y`.

You can fix this by adding a `__get__` method to `CallTracker` to make it behave as a descriptor, but then you also need to think about whether each access creates a fresh bound version, how `classmethod` and `staticmethod` interact with it, what happens when the descriptor is accessed on the class versus the instance, and so on. There is a real amount of code involved in getting all of this right, and it is exactly the code that `wrapt` exists to provide.

## Doing it with wrapt

`wrapt` handles the descriptor machinery for you. The recommended way to write a decorator with `wrapt` is to use `@wrapt.decorator`, which gives you a uniform wrapper signature across functions, instance methods, class methods and static methods. You always get `wrapped`, `instance`, `args` and `kwargs`, with `instance` set appropriately depending on how the call was made.

Before version 2.2.0, layering state on top of that meant a little bit of manual plumbing. You had to construct the state object yourself, write the wrapper to close over it, then explicitly attach the state to the wrapper after the fact so it could be reached from outside. Something like this:

```python
import wrapt

class CallTracker:
    def __init__(self):
        self.call_count = 0

    def __call__(self, func):
        tracker = self

        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            try:
                return wrapped(*args, **kwargs)
            finally:
                tracker.call_count += 1

        wrapped_func = wrapper(func)
        wrapped_func.tracker = tracker
        return wrapped_func
```

It is not exactly painful, but it is noisy. You have to remember to assign the state attribute, you have to alias `self` so the closure captures it rather than something else, and the actual interesting code (the `try/finally`) is buried under boilerplate.

## The new helper

In `wrapt` 2.2.0 the same decorator can now be written like this:

```python
import wrapt

class CallTracker:
    def __init__(self):
        self.call_count = 0

    @wrapt.bind_state_to_wrapper(name="tracker")
    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1
```

The `__call__` method is defined directly with the standard `wrapt` decorator signature, with an extra `self` at the front so it can reach the state on the `CallTracker` instance. The `@wrapt.bind_state_to_wrapper` descriptor sits on top of `@wrapt.decorator` and takes care of two things. When `__call__` is accessed via an instance of `CallTracker`, it returns a wrapper that knows about the right `self`. And when that wrapper is applied to a function, the `CallTracker` instance is automatically attached to the resulting wrapped function under the name supplied in the `name` argument.

Using it looks like:

```python
@CallTracker()
def add(x, y):
    return x + y

add(1, 2)
add(3, 4)
print(add.tracker.call_count)
```

The output is `2`. Where the previous approaches forced a choice between keeping state with the decorator class and supporting methods correctly, `wrapt` lets you have both. Applied to an instance method, the same decorator just works:

```python
class Calculator:
    @CallTracker()
    def add(self, x, y):
        return x + y

calc = Calculator()
calc.add(1, 2)
calc.add(3, 4)
print(calc.add.tracker.call_count)
```

This also prints `2`. The wrapper handles descriptor binding correctly, `self` is passed through to the underlying method, and the state attribute remains reachable on the bound version of the wrapper because attribute lookup on a bound function wrapper now falls through to the parent function wrapper. That last bit is another small change in 2.2.0 that I won't dwell on here, but without it the cleaner syntax above would not be reachable through an instance.

## A little extra polish

One refinement worth pointing out is what to do when you want the decorator to be usable both with and without arguments. That is, the `@CallTracker` versus `@CallTracker(call_count=100)` distinction. Construction can be wrapped up in a static method on the class:

```python
class CallTracker:
    def __init__(self, call_count=0):
        self.call_count = call_count

    @wrapt.bind_state_to_wrapper(name="tracker")
    @wrapt.decorator
    def __call__(self, wrapped, instance, args, kwargs):
        try:
            return wrapped(*args, **kwargs)
        finally:
            self.call_count += 1

    @staticmethod
    def track(func=None, /, *, call_count=0):
        tracker = CallTracker(call_count=call_count)
        if func is None:
            return tracker
        return tracker(func)
```

You can now write either `@CallTracker.track` or `@CallTracker.track(call_count=100)` and get sensible behaviour in both cases. None of that is specific to `wrapt`, it is just the usual Python trick for optional-argument decorators, but it composes nicely with the rest.

## Why this matters

The reason `wrapt` exists in the first place is that writing decorators that behave correctly across functions, instance methods, class methods and static methods is harder than it looks. The descriptor protocol, `functools.wraps`, the `inspect` module, and the time-honoured Python habit of "just stick it on the function as an attribute" all interact in slightly awkward ways once you try to combine them. The uniform wrapper signature in `wrapt` removes most of that friction.

What `bind_state_to_wrapper` adds is the last missing piece for the common case of a stateful decorator. The state lives on the decorator class, the wrapper has direct access to it via `self`, and the state is exposed back to callers through a named attribute on the wrapped object with no extra plumbing. Documentation for both pieces is over in [the decorators guide](https://wrapt.readthedocs.io/en/master/decorators.html#decorators-with-state) and [the examples page](https://wrapt.readthedocs.io/en/master/examples.html#tracking-call-state) if you want to look at the full set of variations.

The feature is available in `wrapt` from version 2.2.0 onwards, although you should grab whatever the latest release is from [PyPi](https://pypi.org/project/wrapt/) since there have been follow-up releases on the 2.2.x branch since. If you are coming to this from the [Wrapt version 2.0.0](/posts/2025/10/wrapt-version-2-0-0/) announcement last year, it builds on the same `BaseObjectProxy` reshuffle that release prepared the ground for. As always, if you find any issues there is an [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
