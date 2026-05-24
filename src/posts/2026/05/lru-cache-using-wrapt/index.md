---
title: "Per-instance lru_cache using wrapt"
description: "How wrapt 2.2.0's lru_cache helper builds on top of functools.lru_cache to fix the issues with using it on instance methods."
date: 2026-05-24T14:30:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt", "decorators"]
draft: false
---

Following on from the [previous post on stateful decorators](/posts/2026/05/stateful-decorators-in-wrapt/), there is another small addition in `wrapt` 2.2.0 worth a closer look. A new `wrapt.lru_cache` helper has been added that fixes the long-standing issues with using `functools.lru_cache` on instance methods.

The thing I want to emphasise up front is that `wrapt.lru_cache` is not a replacement for `functools.lru_cache`. The actual caching is still done by the standard library implementation, all of its keyword arguments are passed straight through, and the eviction behaviour is identical. What `wrapt.lru_cache` adds is a thin layer on top, built using `wrapt`'s decorator machinery, that fixes how the underlying `functools.lru_cache` is applied when the decorated function turns out to be a method on a class.

## What lru_cache gives you

`functools.lru_cache` is a small but very useful decorator. You wrap a function with it and the function's return values are remembered, keyed on the arguments, up to some maximum cache size. Repeat calls with the same arguments skip the function body and return the cached result.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive(n):
    print("computing", n)
    return n * n

expensive(2)
expensive(2)
expensive(3)
```

Running this prints `computing 2` and `computing 3` once each. For pure functions of their arguments this is exactly what you want.

## Where it falls apart

It is when you reach for the same decorator on an instance method that things start to go wrong. The standard library implementation has no concept of the wrapped function being a method, so it treats `self` as just another argument and includes it in the cache key. That single design choice causes three distinct problems.

### Problem 1: instances share a single cache budget

```python
from functools import lru_cache

class Computer:
    @lru_cache(maxsize=2)
    def compute(self, x):
        return x * 2

a = Computer()
b = Computer()

a.compute(1)
a.compute(2)
b.compute(1)
b.compute(2)

print(a.compute.cache_info())
```

The cache is a single shared structure attached to `Computer.compute`. With `maxsize=2`, four distinct `(self, x)` pairs across the two instances are competing for two cache slots. `cache_info()` reports `hits=0, misses=4, currsize=2`. With one hundred instances and the default `maxsize=128`, each instance ends up with rather close to a single cache slot of its own.

### Problem 2: cached instances cannot be garbage collected

Because `self` is part of the cache key, the cache holds a strong reference to it. The instance can never go out of scope while there is a cached entry for one of its method calls:

```python
import gc, weakref
from functools import lru_cache

class Big:
    @lru_cache
    def compute(self, x):
        return x

b = Big()
ref = weakref.ref(b)

b.compute(1)
del b
gc.collect()

print(ref())
```

`ref()` returns the original `Big` instance rather than `None`. It is still alive, kept around by the cache, with no easy way to find or release it short of calling `Big.compute.cache_clear()` and dropping every other instance's cached results along with it.

### Problem 3: self must be hashable

Cache keys have to be hashable. The standard library implementation therefore requires that `self` is hashable too. Any class that defines `__eq__` without also defining `__hash__` is implicitly unhashable, and the decorator will fail at call time:

```python
from functools import lru_cache

class Record:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return isinstance(other, Record) and self.name == other.name

    @lru_cache
    def upper(self):
        return self.name.upper()

Record("a").upper()
```

That raises `TypeError: unhashable type: 'Record'`. None of the function's actual arguments are involved in the failure; it is purely about `self`.

## The wrapt version

The `wrapt.lru_cache` helper sidesteps all three problems by recognising when the decorated callable is being invoked as a method, and arranging for a separate `functools.lru_cache`-wrapped helper to exist for each decorated method on each instance. The helper is stored directly on the instance under an attribute named after the wrapped method, so for a method called `compute` the cache lives at `instance._lru_cache_compute`. The cache key is built from the genuine arguments only, with `self` providing the lookup of which cache to use rather than being a participant in the key.

The same three examples now look like:

```python
import wrapt

class Computer:
    @wrapt.lru_cache(maxsize=2)
    def compute(self, x):
        return x * 2

a = Computer()
b = Computer()

a.compute(1)
a.compute(2)
b.compute(1)
b.compute(2)

print(a.compute.cache_info())
```

Each instance has its own cache for `compute` with the full `maxsize=2` budget. The `cache_info()` call here returns the stats for the cache attached to `a` (`hits=0, misses=2, currsize=2`), not a shared total. Calling `b.compute.cache_info()` reports its own independent set of numbers. If `Computer` had several `@wrapt.lru_cache` methods then each would get its own per-instance cache, stored under a separate attribute (`_lru_cache_compute`, `_lru_cache_other_method`, and so on), with no contention between them.

The garbage collection case works correctly because each instance owns its own cache attributes, and when the instance is collected the caches stored on it go with it:

```python
import gc, weakref
import wrapt

class Big:
    @wrapt.lru_cache
    def compute(self, x):
        return x

b = Big()
ref = weakref.ref(b)

b.compute(1)
del b
gc.collect()

print(ref())
```

`ref()` now returns `None`.

And unhashable instances are fine, because `self` was never part of the cache key in the first place:

```python
import wrapt

class Record:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return isinstance(other, Record) and self.name == other.name

    @wrapt.lru_cache
    def upper(self):
        return self.name.upper()

print(Record("a").upper())
```

That prints `A`, with no `TypeError`.

For plain functions, class methods and static methods (where there is no per-instance state to keep separate) `wrapt.lru_cache` defers to a single shared `functools.lru_cache`, so the behaviour is indistinguishable from using `functools.lru_cache` directly:

```python
@wrapt.lru_cache(maxsize=32)
def factorial(n):
    return n * factorial(n - 1) if n else 1
```

## What is and is not new here

To restate the point at the top of the post, none of this is a new caching algorithm. The eviction strategy, the cache statistics, the keyword arguments, the `CacheInfo` tuple, the `cache_info()` / `cache_clear()` / `cache_parameters()` methods are all `functools.lru_cache`, untouched. What `wrapt.lru_cache` adds is the descriptor-protocol-aware machinery to ensure that for instance methods, the right cache is created and consulted, with no global cache pollution, no reference leaks, and no hashability requirement on the instance.

This is the kind of problem `wrapt` exists to handle. The recommended way to write a decorator with `wrapt` gives you a uniform wrapper signature that knows whether it has been called as a function, instance method, class method or static method, and the `lru_cache` helper is essentially a small, focused use of that machinery to delegate to the standard library decorator in a way that respects the calling convention.

The `lru_cache` helper is documented over on [the bundled decorators page](https://wrapt.readthedocs.io/en/master/bundled.html#lru-cache), and the full release notes for the rest of `wrapt` 2.2.0 are in [the changelog](https://wrapt.readthedocs.io/en/master/changes.html). The feature is available from 2.2.0 onwards, although as before it is worth grabbing the latest release from [PyPi](https://pypi.org/project/wrapt/) since there have been follow-up releases on the 2.2.x branch. Issues and questions go to the [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
