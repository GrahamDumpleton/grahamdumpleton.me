---
title: "Lazy monkey patching with wrapt"
description: "Deferred monkey patching has been in wrapt for years. Python 3.15's lazy imports make it the right default for instrumentation libraries."
date: 2026-05-24T16:30:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt", "decorators"]
draft: false
---

This post is for the people who write APM agents, tracers, profilers, debuggers, and anything else that instruments Python code without asking the user to change it. Everyone else is welcome along.

The reason I want to call out the audience up front is that `wrapt` was created for this kind of work, and the original purpose is sometimes obscured by how widely the project has been adopted for its decorator API. The decorator side of `wrapt` (which the recent posts on [stateful decorators](/posts/2026/05/stateful-decorators-in-wrapt/) and [per-instance lru_cache](/posts/2026/05/lru-cache-using-wrapt/) have covered) grew out of needing reliable building blocks for monkey patching, not the other way around.

There is a side of `wrapt` that, until April 2026, had no dedicated page in the official documentation. I have covered it in various conference talks over the years, but that is not the same thing as having proper docs. The mechanism for *deferred* monkey patching, registering a patch against a module that has not been imported yet, with the patch only applied when the module is later imported, has been part of `wrapt` from day one. The [monkey patching documentation page](https://wrapt.readthedocs.io/en/master/monkey.html) finally landed in the lead-up to the 2.2.0 release, which also added a small ergonomic piece. A new `?` modifier on module names closes the last awkward gap in how the deferred form composes with the convenient decorator syntax.

So this post is amplification of a pattern that has been there all along, not breaking news. The new modifier is just polish.

With Python 3.15 about to ship [PEP 810](https://peps.python.org/pep-0810/) explicit `lazy import` syntax, the timing matters. Any instrumentation library that force-imports its target modules at agent startup is now actively undoing user-level lazy imports. That has always been a little impolite for cold-start performance. With 3.15 it becomes a direct conflict with how users want to write their code.

## A monkey patching primer

The smallest useful piece of `wrapt`'s monkey patching API is `wrap_function_wrapper`. You give it a module, the dotted name of an attribute on that module, and a wrapper function. It replaces that attribute with a `FunctionWrapper` that calls your wrapper around the original.

A timing wrapper on `json.dumps` looks like this:

```python
import json
import time
import wrapt

def time_call(wrapped, instance, args, kwargs):
    start = time.perf_counter()
    try:
        return wrapped(*args, **kwargs)
    finally:
        elapsed = (time.perf_counter() - start) * 1e6
        print(f"json.dumps took {elapsed:.0f} us")

wrapt.wrap_function_wrapper("json", "dumps", time_call)

print(json.dumps({"a": 1, "b": [2, 3]}))
```

Output:

```
json.dumps took 16 us
{"a": 1, "b": [2, 3]}
```

The `wrapped, instance, args, kwargs` signature of `time_call` is the same uniform wrapper signature that `@wrapt.decorator` uses, and that the [stateful decorators post](/posts/2026/05/stateful-decorators-in-wrapt/) has already shown in the decorator context. That is not a coincidence. The decorator API in `wrapt` is built on top of this same wrapper mechanism, not the other way around, so the body you would write for a `@wrapt.decorator`-style decorator is the same body you would write for a monkey patch. Whatever you have learned about writing wrappers in the decorator context carries straight over.

The user code that calls `json.dumps` does not change. The instrumentation is added entirely by `wrap_function_wrapper`. That is the whole point. APM agents and similar tools want to add visibility to third-party code without asking the user to modify it.

## The forced-import problem

`wrap_function_wrapper` takes the module name as a string and imports the module to find the attribute to wrap. The act of registering the patch loads the target.

```python
import sys
import wrapt

def trace(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

print("before:", "xml.etree.ElementTree" in sys.modules)
wrapt.wrap_function_wrapper("xml.etree.ElementTree", "fromstring", trace)
print("after :", "xml.etree.ElementTree" in sys.modules)
```

Running this prints:

```
before: False
after : True
```

For a single module that is mildly wasteful. For an APM agent that supports, say, `requests`, `httpx`, `urllib3`, `aiohttp`, `django`, `flask`, `fastapi`, `sqlalchemy`, `psycopg`, `redis`, `pymongo` and `kafka-python`, importing the agent loads every one of those modules at agent startup, regardless of which the user's app actually uses.

The price shows up in three places. Cold start time gets a noticeable chunk added, which matters disproportionately in serverless and short-lived worker environments where the process lifetime is measured in seconds. Memory holds code that is never going to be called. And the user's own `lazy import` statements get silently undone, because by the time their code runs the modules are already loaded.

## The long-standing answer

The mechanism that solves all three problems has been in `wrapt` from the early days. The idea originally came from [PEP 369](https://peps.python.org/pep-0369/), which proposed post-import hooks for the Python standard library. That PEP was withdrawn, but `wrapt` provides its own implementation via a `sys.meta_path` finder.

The low-level entry point is `register_post_import_hook(hook, name)`. The hook is a callback that takes the module as its argument and runs once the named module is imported. If the module is already imported when the hook is registered, the hook fires immediately.

The decorator form, `when_imported(name)`, is the one most code uses:

```python
import sys
import wrapt

def trace_reader(wrapped, instance, args, kwargs):
    print("[traced csv.reader]")
    return wrapped(*args, **kwargs)

@wrapt.when_imported("csv")
def install(module):
    wrapt.wrap_function_wrapper(module, "reader", trace_reader)

print("after register:", "csv" in sys.modules)
import csv
print("after import  :", "csv" in sys.modules)
for row in csv.reader(["a,b,c"]):
    print("row:", row)
```

Output:

```
after register: False
after import  : True
[traced csv.reader]
row: ['a', 'b', 'c']
```

Two things to notice. Registering the hook does not touch `sys.modules`. The module is only loaded when the user's code does `import csv`. And the wrapping happens automatically as a side effect of that import, so the patched `csv.reader` is what the user code sees.

This is the mechanism that every reputable APM agent already uses one way or another, because they had to. It just was not very visible from the outside.

## The decorator-form gap

`wrap_function_wrapper` has a more convenient cousin called `patch_function_wrapper` which is the decorator form. It lets you keep the wrapper definition at module top level rather than nested inside a callback:

```python
@wrapt.patch_function_wrapper("html.parser", "HTMLParser.feed")
def trace_feed(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
```

This is the form you really want for a patch registry. One decorated wrapper function per supported third-party target, all at the top level of one file. Easy to read, easy to grep, no nested closures.

The catch, before `wrapt` 2.2.0, was that this decorator form force-imported its target the same way `wrap_function_wrapper` did:

```python
import sys
import wrapt

print("before:", "html.parser" in sys.modules)

@wrapt.patch_function_wrapper("html.parser", "HTMLParser.feed")
def trace_feed(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

print("after :", "html.parser" in sys.modules)
```

```
before: False
after : True
```

The lazy alternative meant restructuring into a `when_imported` callback with the wrapper defined inside it. Workable but ugly, especially repeated across a dozen targets, and you lose the clean "one decorated function per target" layout that makes a patch registry readable.

## The ? modifier in 2.2.0

`wrapt` 2.2.0 closes the gap by recognising a trailing `?` on a module name. With the `?`, both `wrap_function_wrapper` and `patch_function_wrapper` defer registration via a post-import hook when the target module is not yet loaded. If the module is already in `sys.modules`, the patch is applied immediately. Same behaviour as before, just without the side effect of forcing the import.

```python
import sys
import wrapt

def trace(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

wrapt.wrap_function_wrapper("gzip?", "compress", trace)
print("after register (with ?):", "gzip" in sys.modules)
import gzip
print("after import           :", "gzip" in sys.modules)
```

```
after register (with ?): False
after import           : True
```

And the decorator form, which is the case that actually motivated the change:

```python
import sys
import wrapt

@wrapt.patch_function_wrapper("tempfile?", "mkdtemp")
def trace_mkdtemp(wrapped, instance, args, kwargs):
    print("[traced tempfile.mkdtemp]")
    return wrapped(*args, **kwargs)

print("after register (with ?):", "tempfile" in sys.modules)
import tempfile
print("after import           :", "tempfile" in sys.modules)
print("mkdtemp:", tempfile.mkdtemp())
```

```
after register (with ?): False
after import           : True
[traced tempfile.mkdtemp]
mkdtemp: /var/folders/.../tmpktve96ix
```

Under the hood, the `?` form is genuinely just shorthand. The implementation in `wrapt`'s `patches.py` is roughly:

```python
if target.endswith("?"):
    target = target[:-1]
    if target in sys.modules:
        return wrap_object(sys.modules[target], name, FunctionWrapper, (wrapper,))
    def callback(module):
        wrap_object(module, name, FunctionWrapper, (wrapper,))
    register_post_import_hook(callback, target)
    return None
```

No new mechanism, no new dispatch path. The work is still done by the same `register_post_import_hook` that has been in `wrapt` for years. The benefit is purely the authoring style. `@patch_function_wrapper("...?", "...")` at top level is now an option that previously was not.

## Composition with PEP 810 lazy imports

Python 3.15 ships [PEP 810](https://peps.python.org/pep-0810/) explicit lazy imports. The user can write:

```python
lazy import requests
```

and the import is deferred until the name `requests` is first used. The discussion in [Lazy imports using wrapt](/posts/2025/10/lazy-imports-using-wrapt/) covers the PEP's motivation in more detail.

This raises a question that was not quite so sharp before. If a user's code uses `lazy import` for a module, and an APM agent registers a non-lazy `wrap_function_wrapper` for that module, what happens?

```python
# apm_eager.py — simulated APM patches
import wrapt
def trace(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
wrapt.wrap_function_wrapper("gzip", "compress", trace)
```

```python
# user_code.py — user's app
import sys
import apm_eager   # APM agent loaded at process startup

lazy import gzip

print("after lazy import:", "gzip" in sys.modules)
gzip.compress(b"hello")
print("after first use  :", "gzip" in sys.modules)
```

Output:

```
after lazy import: True
after first use  : True
```

The user wrote `lazy import gzip`, but `gzip` is already in `sys.modules` by the time their import statement runs. The APM agent loaded it on the user's behalf. Whatever benefit the user expected from `lazy import` has been quietly undone.

Switching the APM agent to use the `?` form fixes it:

```python
# apm_lazy.py
import wrapt
def trace(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
wrapt.wrap_function_wrapper("gzip?", "compress", trace)
```

With the same user code as before, this now prints:

```
after lazy import: False
after first use  : True
```

`gzip` is only loaded at the moment the user's code first touches it, and at that moment the patch fires too. Lazy patching and lazy imports compose correctly.

## Putting it together: a patch registry

For an APM agent or similar, the practical pattern looks like this. A single file declares all the patches as a flat list of top-level decorated functions:

```python
# my_apm_patches.py
import wrapt

@wrapt.patch_function_wrapper("xml.etree.ElementTree?", "fromstring")
def trace_fromstring(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("csv?", "reader")
def trace_reader(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("gzip?", "compress")
def trace_compress(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("html.parser?", "HTMLParser.feed")
def trace_feed(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)
```

Importing this module registers all four patches but loads none of the target modules:

```python
import sys
import my_apm_patches

targets = ["xml.etree.ElementTree", "csv", "gzip", "html.parser"]
for m in targets:
    print(f"  {m:30s} {'loaded' if m in sys.modules else 'not loaded'}")
```

Output:

```
  xml.etree.ElementTree          not loaded
  csv                            not loaded
  gzip                           not loaded
  html.parser                    not loaded
```

Whichever modules the user's code actually imports is the set that ends up getting patched. The rest stay out of memory entirely. The agent has paid no cold-start cost for the targets the user does not care about, and the user's own lazy imports continue to do what they say on the tin.

As a bonus, the test story is also better. The instrumentation library's test suite no longer needs every supported third-party package installed just to import the library, only the ones it actually exercises.

## What changed and what didn't

Strictly speaking, nothing in `wrapt` 2.2.0 enables any behaviour that was not possible before. The deferred patching mechanism is the same `register_post_import_hook` it always was. What changed is the authoring ergonomics. The `?` modifier lets you write the lazy version of a patch as concisely as the eager version, including in the decorator form that suits patch-registry files best. And the [monkey patching docs page](https://wrapt.readthedocs.io/en/master/monkey.html) that landed in April 2026 finally makes the mechanism easy to discover.

If you maintain instrumentation code that still force-imports its targets, Python 3.15 is a good prompt to refactor. The change is mechanical. Add a `?` to the module name in each `wrap_function_wrapper` and `patch_function_wrapper` call. The behaviour for already-loaded modules is unchanged, and for not-yet-loaded modules the patch now fires when (and only when) the user's code actually imports them.

The full release notes for `wrapt` 2.2.0 are in [the changelog](https://wrapt.readthedocs.io/en/master/changes.html). The latest release is on [PyPi](https://pypi.org/project/wrapt/), and issues go to the [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
