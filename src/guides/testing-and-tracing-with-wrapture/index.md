---
title: "Testing and tracing with wrapture."
description: "Posts on wrapture, the Python package for monkey patching, testing and tracing built on wrapt. What it is, how it is used in unit tests, and how the same bindings trace a running application."
tags: ["python", "wrapture", "testing", "tracing"]
draft: false
---

Posts on the topic of [wrapture](https://github.com/GrahamDumpleton/wrapture), a Python package for monkey patching, testing and tracing built on top of wrapt, are as follows.

The starting point, on what wrapture is, why I built it, and how it was written:

  * [Introducing wrapture.](/posts/2026/08/introducing-wrapture/)

This batch of posts covers using wrapture in unit tests, where the difference from `unittest.mock` is that the real code still runs and everything that flows through it is recorded:

  * [Unit testing with wrapture.](/posts/2026/09/unit-testing-with-wrapture/)
  * [Recording calls with wrapture.](/posts/2026/09/recording-calls-with-wrapture/)
  * [Phased behaviour in wrapture.](/posts/2026/09/phased-behaviour-in-wrapture/)
  * [Beyond callables in wrapture.](/posts/2026/09/beyond-callables-in-wrapture/)

This batch of posts covers the tracing side, where the same bindings used in tests observe a running application instead, from a live call tree in a terminal through to spans in an OpenTelemetry backend:

  * [Live tracing with wrapture.](/posts/2026/09/live-tracing-with-wrapture/)
  * [Zero-code tracing with wrapture.](/posts/2026/09/zero-code-tracing-with-wrapture/)
  * [Tracing Flask with wrapture.](/posts/2026/09/tracing-flask-with-wrapture/)
  * [Finding slow code with wrapture.](/posts/2026/09/finding-slow-code-with-wrapture/)
  * [OpenTelemetry export in wrapture.](/posts/2026/09/opentelemetry-export-in-wrapture/)

The [documentation](https://wrapture.readthedocs.io/) is the reference for everything the posts skip over, and the older posts collected under [decorators and monkey patching](/guides/decorators-and-monkey-patching/) cover wrapt, the library wrapture is built on.
