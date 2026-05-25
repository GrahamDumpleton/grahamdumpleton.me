---
title: "Free-threading in mod_wsgi 6.0.0"
description: "mod_wsgi 6.0.0 adds WSGIFreeThreading, an opt-in directive for PEP 703 free-threaded Python. GIL-enabled mode remains the default even on free-threaded builds."
date: 2026-05-25T11:00:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/mod_wsgi"
tags: ["python", "mod_wsgi", "wsgi", "apache"]
draft: false
---

The [previous post](/posts/2026/05/per-interpreter-gil-in-mod-wsgi-6-0-0/) in this series covered the new `WSGIPerInterpreterGIL` directive in mod_wsgi 6.0.0 and the PEP 684 per-interpreter GIL feature that landed in Python 3.12. This post is about its sibling, `WSGIFreeThreading`, which targets PEP 703 free-threaded Python builds.

The two directives sit next to each other in the mod_wsgi configuration vocabulary and they both opt processes into a non-default concurrency model, but the underlying mechanisms are quite different. Per-interpreter GIL gives each sub-interpreter its own lock. Free-threading removes the lock entirely. That distinction shapes everything below.

## What free-threading actually is

Free-threading removes the GIL from CPython entirely. There is no process-wide lock to acquire and no per-interpreter lock to acquire. All threads in the process can run Python bytecode in parallel, in the same interpreter, against the same Python objects. This is fundamentally different from per-interpreter GIL, which keeps a GIL but gives each sub-interpreter its own one. Free-threading has no GIL at all.

The price for this is a special CPython build. The feature is enabled at compile time with `--disable-gil`, and on platforms that distribute it the resulting binary is typically named `python3.13t`. The "t" suffix exists precisely so the free-threaded build can coexist on a system alongside the normal CPython build. Free-threading shipped as an experimental opt-in in Python 3.13 and continues to mature in 3.14.

One useful detail to know is that a free-threaded build can still run with a GIL. The build supports both modes. What you get at runtime depends on what the embedder asks for. Which is the bridge into mod_wsgi's posture.

## mod_wsgi's posture: opt-in even on a free-threaded build

If you compile and install mod_wsgi against a free-threaded Python, the default is still GIL-enabled. Nothing about your existing application behaviour changes until you say otherwise. The free-threaded build supports the mode; mod_wsgi declines to use it without explicit instruction.

This is worth being clear about because the assumption most people will reach for is the opposite. Installing mod_wsgi against `python3.13t` does not automatically give you free-threading. It gives you the ability to opt in.

The reason for the default is the one you can guess at. The ecosystem of C extensions is nowhere near ready for everyone to be on free-threading by default. Forcing it on across the board would silently break existing deployments the moment they happened to import an extension that has not been audited for thread-safe execution. Defaulting to GIL-enabled keeps the worst case "nothing changes". You only get the new behaviour when you ask for it.

The opt-in is `WSGIFreeThreading On`. The directive is per process. Unlike `WSGIPerInterpreterGIL`, it cannot be scoped to a specific sub-interpreter inside a process. Free-threading is a property of the whole process or none of it.

## The combinatorial story

The upside of keeping the default opt-in is the flexibility it leaves you with. Compile mod_wsgi against a free-threaded Python build and you have access to three different concurrency models, and you can mix them across daemon process groups within the same Apache instance.

The three options:

- Process-wide GIL (the classic model, still the default)
- Per-interpreter GIL, where each sub-interpreter in a process holds its own GIL (covered in the previous post)
- Free-threading, where the process has no GIL at all

A single Apache instance can have one daemon process group running free-threaded for a CPU-bound numerical workload that has been audited end-to-end, another running with per-interpreter GIL for an application whose extensions support PEP 684 but not PEP 703, and embedded mode left on the classic process-wide GIL. Pick the right model per workload.

There is also an experimentation angle worth calling out. Comparing the behaviour of the same application under each of the three modes on the same machine is suddenly much easier. You can run the same WSGI application in three daemon process groups, configure each one differently, route a slice of traffic at each, and compare directly.

The constraint to be aware of: within a single process, free-threading and per-interpreter GIL are mutually exclusive. If both apply to the same process, free-threading wins and the per-interpreter GIL setting becomes a no-op. The mix-and-match is across processes, not inside one.

## How to enable

The simplest form, opting all processes into free-threading at server scope:

```
WSGIFreeThreading On
```

Selective opt-in for a specific daemon process group, using the `WSGIInterpreterOptions` container directive introduced in the previous post:

```
<WSGIInterpreterOptions process-group="cpu-bound">
    WSGIFreeThreading On
</WSGIInterpreterOptions>
```

And for the embedded mode interpreter in Apache child processes:

```
<WSGIInterpreterOptions process-group="%{GLOBAL}">
    WSGIFreeThreading On
</WSGIInterpreterOptions>
```

mod_wsgi-express has a convenience flag, `--free-threading`, that flips this on for its generated configuration.

One important contrast with `WSGIPerInterpreterGIL` to make explicit. The `application-group=` selector is not meaningful for free-threading. Per-interpreter GIL is a property of an individual sub-interpreter, so it makes sense to scope down to one. Free-threading is a property of the process. You cannot opt one sub-interpreter inside a process into free-threading while leaving another sub-interpreter in the same process with a GIL. The granularity is the process. If you write a `<WSGIInterpreterOptions>` container with an `application-group=` selector and try to put `WSGIFreeThreading` inside it, mod_wsgi will ignore the setting and log a warning.

## What this means for your Python code

In theory, a correctly written WSGI application is already thread-safe. The WSGI specification has always allowed servers to call the application from multiple threads concurrently, and mod_wsgi has been able to use threaded daemon processes for years. So strictly speaking, if you have been doing it right, you are most of the way there.

In practice, an enormous amount of WSGI code is implicitly relying on what the GIL gives you for free, in a way most developers do not even realise they are relying on. The GIL ensures that bytecode-level operations serialise against each other. Patterns like incrementing a counter with `counter += 1`, setting a key in a shared dict with `cache[key] = value`, appending to a shared list with `items.append(thing)`, or "check then set" lookups against shared state happen to be safe-ish under the GIL because the GIL boundary makes them effectively atomic in the cases that matter most. Without a GIL they are not atomic. They need explicit locks or genuinely atomic primitives.

The shapes of code that are most likely to be quietly unsafe under free-threading are not exotic. Module-level mutable state (registries, caches, in-memory counters) is the most common pattern. Lazy initialisation without locks (`if _thing is None: _thing = build()`) shows up everywhere. Shared mutable objects passed around between threads via globals, memoisation decorators that mutate shared dicts, application singletons set up at import time, the list goes on. These patterns are pervasive in real applications and they are exactly the kind of thing that "has always worked fine under a threaded server" because the GIL has been silently saving them.

This is not a mod_wsgi-specific concern. It is the general PEP 703 question that every application owner has to answer for themselves, every library author has to answer for their library, and that the ecosystem as a whole is going to spend years working through. But mod_wsgi is going to be one of the most realistic places to actually run free-threaded Python against a real workload, so it is likely to be where a lot of these latent bugs first surface.

The defensible position. If your application has been deliberately audited for true concurrent execution, with real locks where shared mutable state is touched and no implicit reliance on the GIL for serialisation, you are most of the way there. Most code, including most mature Python libraries, has not been audited that way. Free-threading is not a trap, but it is genuinely a different correctness contract than the one most Python code was written against. Treat the opt-in accordingly.

## What this means for C extensions

The previous post covered the C extension story for per-interpreter GIL in some detail. The rules for free-threading are a separate set of rules, related but distinct, and I will focus on the contrasts rather than restate the bits that overlap.

An extension opts into free-threading by declaring `Py_mod_gil = Py_MOD_GIL_NOT_USED` in its `PyModuleDef_Slot` array. That declaration is the extension author asserting "I have been audited for execution without a GIL". Without it, CPython treats the extension as untrusted for free-threading.

The interesting difference from per-interpreter GIL is the load behaviour. Per-interpreter GIL fails the import outright if an extension has not declared support. Free-threading does not. The extension loads, but as soon as it loads CPython silently re-enables the GIL for the entire process and emits a runtime warning. That is worth understanding because the failure mode is "your free-threading quietly turned off" rather than "your import broke". You may not notice for a while that everything is back to running under a GIL.

The other requirements largely match the per-interpreter GIL story. PEP 489 multi-phase module initialisation is the prerequisite. Module-level static state in C becomes a data-race risk in a way it was not under the GIL, and the right answer is to move it into module state retrieved via `PyModule_GetState`, with proper locking applied where shared state is unavoidable. Code still using the simplified `PyGILState` API needs to be reviewed for its assumptions, though for different reasons than under per-interpreter GIL.

For operators, the auditing message is the same as last time. Before turning `WSGIFreeThreading` on in any kind of production setting, work through every C extension your application pulls in, directly and transitively, and check whether each one declares free-threading support. An extension that loads under free-threading without complaint is not necessarily fine. It may just be the one that triggered the silent fallback to GIL-enabled.

## Which applications actually benefit

CPU-bound Python work that can be parallelised across threads in a single process is the clear win. Two threads inside one free-threaded process can both run Python bytecode at full speed against the same objects in the same address space. There is no within-sub-interpreter serialisation caveat to qualify it with, in contrast to per-interpreter GIL where two requests in the same sub-interpreter still compete for that sub-interpreter's GIL. Under free-threading, there is no GIL to compete for.

There are costs to be honest about. Free-threaded CPython carries a measurable single-threaded overhead compared with a normal CPython build, because the runtime has to do per-thread bookkeeping for object reference counts and various other things that the GIL was previously making free. The single-thread performance gap has been closing release-over-release, but it is still real, and the trade is parallel throughput for single-thread speed. If your workload does not have parallel Python execution to gain in the first place, enabling free-threading can leave you slower overall.

For ordinary I/O-bound WSGI applications, the practical gain remains smaller for the same reasons as in the previous post. I/O already releases the GIL on a normal CPython build, threads in a single process already overlap their waits on databases and network, and adding daemon processes remains the simpler scaling lever for most web workloads. Free-threading is most interesting where you specifically have CPU-bound Python that would benefit from running concurrently inside one process, and where you can afford both the audit work and the per-thread overhead.

## What's next

If you run mod_wsgi and the free-threading story is interesting to you, please install the 6.0.0 release candidate against a free-threaded Python build, try it against a real workload, and file issues against [the GitHub project](https://github.com/GrahamDumpleton/mod_wsgi) for anything that breaks or behaves oddly. Free-threading is genuinely new territory for embedded Python hosts, and the feedback from real deployments is what will catch the rough edges before the final release.

The next post in this concurrency series will cover `WSGISwitchInterval`. That one is not another GIL mode; it is a tuning lever for adjusting how frequently the GIL is yielded between threads, which can help reduce GIL contention in some workloads. It only applies where there is a GIL to switch, so it is a no-op under free-threading.

For reference:

- [mod_wsgi documentation](https://modwsgi.readthedocs.io/en/latest/)
- [mod_wsgi 6.0.0 release notes](https://modwsgi.readthedocs.io/en/latest/release-notes/version-6.0.0.html)
- [Per-interpreter GIL and free-threading user guide](https://modwsgi.readthedocs.io/en/latest/user-guides/gil-modes-and-free-threading.html)
- [`WSGIFreeThreading` directive documentation](https://modwsgi.readthedocs.io/en/latest/configuration-directives/WSGIFreeThreading.html)
- [PEP 703: Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [PEP 489: Multi-phase extension module initialization](https://peps.python.org/pep-0489/)
- [Previous post: Per-interpreter GIL in mod_wsgi 6.0.0](/posts/2026/05/per-interpreter-gil-in-mod-wsgi-6-0-0/)
