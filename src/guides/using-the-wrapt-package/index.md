---
title: "Practical uses for the wrapt package."
description: "Recipes and features of the wrapt package: stateful decorators, per-instance caches, lazy imports and patching, and how an object proxy behaves when the object resists."
tags: ["python", "wrapt", "decorators"]
draft: false
---

Posts on using [wrapt](https://github.com/GrahamDumpleton/wrapt), the Python package for
decorators, wrappers and monkey patching, are as follows. The earlier posts which work
through why the usual decorator pattern is wrong, and how wrapt came to exist, are
collected separately under [decorators and monkey patching](/guides/decorators-and-monkey-patching/).

Where wrapt fits against the pattern most people reach for first:

  * [The "Decorator Pattern" versus the Python "wrapt" package.](/posts/2018/01/the-pattern-versus-python-package/)

Release news, and the state of the package:

  * [Status of wrapt (September 2025).](/posts/2025/09/status-of-wrapt/)
  * [Wrapt version 2.0.0.](/posts/2025/10/wrapt-version-2-0-0/)

This batch of posts is a set of recipes for things decorators are asked to do, each of
which is harder than it looks without a proper object proxy underneath:

  * [Stateful decorators in wrapt.](/posts/2026/05/stateful-decorators-in-wrapt/)
  * [Per-instance lru_cache using wrapt.](/posts/2026/05/lru-cache-using-wrapt/)
  * [Reshaping decorated functions with wrapt.](/posts/2026/05/reshaping-decorated-functions-with-wrapt/)
  * [Async support for wrapt.synchronized.](/posts/2026/05/async-support-for-wrapt-synchronized/)

This batch of posts deals with deferring work until something is actually used, both for
imports and for the patches applied to them:

  * [Lazy imports using wrapt.](/posts/2025/10/lazy-imports-using-wrapt/)
  * [Use lazy module imports now.](/posts/2025/10/use-lazy-module-imports-now/)
  * [Lazy monkey patching with wrapt.](/posts/2026/05/lazy-monkey-patching-with-wrapt/)

This batch of posts looks at how an object proxy behaves when the object being wrapped
does not cooperate, and how to tell a proxy from the real thing:

  * [Wrapping immutable objects.](/posts/2025/10/wrapping-immutable-types/)
  * [Detecting object wrappers.](/posts/2025/10/detecting-object-wrappers/)

The [wrapture](/guides/testing-and-tracing-with-wrapture/) posts cover a separate package
built on top of wrapt, which applies the same machinery to unit testing and tracing.
