---
title: "Per-interpreter GIL in mod_wsgi 6.0.0"
description: "mod_wsgi 6.0.0 adds WSGIPerInterpreterGIL, an opt-in directive for running sub-interpreters with their own GIL (PEP 684) for parallel Python in one process."
date: 2026-05-25T10:00:00+10:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/mod_wsgi"
tags: ["python", "mod_wsgi", "wsgi", "apache"]
draft: false
---

mod_wsgi 6.0.0 is currently available as a release candidate. You can install it from PyPI, or grab the source from the GitHub releases page. There is a significant amount of code cleanup behind this release, alongside a range of new features and operator-facing improvements that have been overdue for some time.

Rather than describe everything in one post, I am going to work through the headline changes in a short series. The most consequential set for anyone running mod_wsgi in production is the new concurrency configuration. CPython has gained two genuinely new concurrency modes over the last few releases (per-interpreter GIL in 3.12 and free-threading in 3.13), and mod_wsgi 6.0.0 exposes both as opt-in directives, along with finer-grained control over how the GIL switches between threads.

This first post covers the per-interpreter GIL story and the new `WSGIPerInterpreterGIL` directive.

## Why the GIL has always been the deployment problem

This is well-trodden ground, but worth recapping for context. CPython's Global Interpreter Lock serialises Python bytecode execution within a single process. It does not matter how many OS threads you create inside that process. Only one of them runs Python at a time.

For WSGI deployments, this has shaped the way servers like mod_wsgi scale. Threads within a single process are useful for handling I/O concurrently, since any reasonable C extension or built-in I/O call releases the GIL while it waits on the kernel, but they do not give you parallelism for CPU-bound Python work. To get that, you have always needed more processes. mod_wsgi's daemon mode is built around this assumption. You configure N daemon processes, each with its own Python interpreter and its own GIL, and you get N-way Python parallelism that way.

Sub-interpreters complicate the picture slightly. They have existed in CPython for a long time, and mod_wsgi has used them since the beginning, but until [PEP 684](https://peps.python.org/pep-0684/) landed in Python 3.12 they all shared one process-wide GIL. Adding more sub-interpreters inside a single process gave you isolation between applications, but no additional concurrency.

## What changed in Python 3.12 and 3.14

PEP 684 made per-interpreter GIL possible as an opt-in for sub-interpreters created through the C API. With it, each sub-interpreter holds its own lock, and two sub-interpreters running on different OS threads can execute Python bytecode at the same time. The main interpreter is excluded from this. It always holds the original process-wide GIL and cannot be given one of its own. That distinction matters later.

Python 3.14 then shipped [PEP 734](https://peps.python.org/pep-0734/) as `concurrent.interpreters`, the first standard-library API for working with sub-interpreters from Python code. It is a useful addition, but it does come with a deliberate restriction. Data passed between interpreters is either pickled and copied through a queue, shared through the buffer protocol, or limited to a small set of immortal immutable built-ins. Anything that wants to share mutable Python objects across interpreters has to find another way.

That data-sharing restriction is why `concurrent.interpreters` is most naturally suited to message-passing worker patterns rather than ordinary Python code which tends to lean heavily on shared mutable state. The same restriction is one of the reasons embedding hosts like mod_wsgi are well-positioned to get value out of per-interpreter GIL ahead of general Python code.

## How mod_wsgi has always used sub-interpreters

mod_wsgi has used sub-interpreters from the start, but originally for a completely different reason. The driver was isolation, not parallelism. Running multiple WSGI applications inside a single Apache process is a real operational need, and you cannot do it safely if they all share the same `sys.modules`, signal handlers, atexit handlers, and so on. Sub-interpreters give each application its own private copy of all of that.

mod_wsgi calls this an "application group". Each named application group maps to a sub-interpreter inside whichever daemon process (or embedded Apache child process) is hosting it. Until Python 3.12, that arrangement was purely about keeping applications from stepping on each other.

What changes with per-interpreter GIL is that the same sub-interpreters mod_wsgi was already creating for isolation can now hold their own locks and run Python bytecode in parallel. The application group concept does not need to change. The directive that flips this on is new, but the underlying structure is the one mod_wsgi has had all along.

There is also a happy alignment with the data-sharing constraint mentioned above. mod_wsgi routes each incoming WSGI request directly into a chosen sub-interpreter, and the WSGI contract does not ask for any shared mutable Python state to span requests. The request is the message. From an application author's point of view, there is not much new to do. The configuration changes; in most cases the application does not. The caveats, and there are always caveats, are what your C extensions will tolerate and, if your application spawns its own background threads, what their shutdown handling looks like under per-interpreter rules. More on both at the end.

## The new directive

The new directive is `WSGIPerInterpreterGIL`, with the obvious syntax:

```
WSGIPerInterpreterGIL On
```

The default is `Off`. Opt-in is deliberate; there is no scenario where it would be safe for mod_wsgi to flip this on by default. The directive is valid at server config scope and can also appear inside a `<WSGIInterpreterOptions>` container, which is what you want most of the time and which I will get to next.

Two things worth flagging up front. First, the main interpreter is excluded. If your application runs in the main interpreter, which it will if you have set `WSGIApplicationGroup %{GLOBAL}`, then enabling `WSGIPerInterpreterGIL` has no effect on it. Per-interpreter GIL only applies to sub-interpreters. Second, Python 3.12 or later is required. On older Python the directive is accepted but does nothing, with a configuration warning logged.

## Composing with daemon mode

The interesting case for `WSGIPerInterpreterGIL` is not opting an entire daemon process group into it. If you want extra parallel Python execution across separate processes, you can already get that by adding more daemon processes. The interesting case is selectively enabling per-interpreter GIL for specific sub-interpreters that already exist within a daemon process you are running.

A small example. Suppose you have a daemon process group called `localhost:8000` running a single WSGI application. You can create a named sub-interpreter inside that process and give it its own GIL, like this:

```
<WSGIInterpreterOptions process-group="localhost:8000" application-group="sub-interp-1">
    WSGIPerInterpreterGIL On
</WSGIInterpreterOptions>
```

`WSGIInterpreterOptions` is the container directive that lets you scope settings to a particular sub-interpreter. The `process-group=` selector matches a daemon process group by name, or `%{GLOBAL}` for the embedded mode interpreter in Apache child processes. The `application-group=` selector further narrows to a specific application group inside that process, which is the same thing as a specific sub-interpreter. Both selectors are optional, and the most-specific match wins.

On its own, the directive above does nothing useful. The sub-interpreter is configured to hold its own GIL but no requests are being routed into it yet. To actually use it, you can delegate a sub-URL of the existing application to that sub-interpreter using a `<Location>` block:

```
<Location /suburl>
    WSGIApplicationGroup sub-interp-1
</Location>
```

The end result is that requests to `/suburl` are dispatched into a second copy of the application running in `sub-interp-1`, which holds its own GIL, while everything else continues to run in the default application group with the process-wide GIL. Two halves of the same application can now execute Python bytecode in parallel inside one daemon process.

There is a different shape that may suit a different setup. If your Apache configuration already has multiple `WSGIScriptAlias` directives pointing at distinct WSGI applications, and you have arranged for those applications to run in separate sub-interpreters of a single daemon process (as opposed to separate daemon process groups), then `WSGIPerInterpreterGIL` lets you opt the relevant sub-interpreters into their own GILs without rearranging the process layout.

A note on cost. If the daemon process was previously hosting one sub-interpreter and you switch to hosting two, you now have two live copies of the application in that process, each with its own `sys.modules`, its own imported pure-Python modules, and its own per-interpreter C extension state. Memory use goes up. The trade is the same one you make when you add daemon processes, more memory in exchange for more parallel Python, but doing it within a single daemon process can still have advantages depending on how the application is provisioned and managed at the OS level. Whether one process with two sub-interpreters is preferable to two daemon processes with one sub-interpreter each is a judgement call about your specific deployment, not a universal answer.

One more thing before moving on. There is a separate directive coming in this series called `WSGIFreeThreading` for use with free-threaded Python builds. The two are mutually exclusive on a single process, and the next post covers it on its own terms, so I will not muddy this one with the details.

## Which applications actually benefit

The honest answer is fewer than the headline implies. Per-interpreter GIL helps for CPU-bound Python work that can be partitioned cleanly across requests, where you would otherwise be paying the cost of running additional daemon processes purely to dodge the GIL. Numerical work that is not already handled inside C code that releases the GIL, request-scoped computation, image processing, and similar.

It is also worth being clear about what the directive does not do. Giving a sub-interpreter its own GIL only buys parallelism between sub-interpreters. Two concurrent CPU-bound requests that both land in `sub-interp-1` still compete for that sub-interpreter's GIL and serialise against each other, exactly as they would have before. If all the heavy work funnels through one sub-interpreter, the directive has not bought you anything. The win comes from spreading the load across multiple sub-interpreters, each holding its own GIL. Which is why, for genuinely heavy CPU-bound throughput, scaling out with extra daemon processes is often still the cleaner answer; each daemon process gives you both an additional GIL and an additional set of OS-level resources to schedule against.

For ordinary I/O-bound web applications, the win is much smaller. I/O already releases the GIL, threads in a single process can already overlap their waits for the database or the network, and adding daemon processes remains the simpler scaling lever. Per-interpreter GIL is a precision tool. It is most useful when you specifically want more parallel Python execution inside fewer processes, or when you already have multiple sub-interpreters in one process for isolation reasons and you would now like them to run in parallel as well.

## The gotchas

A few things are worth being aware of before reaching for the directive.

Sub-interpreters do not share Python state. Each sub-interpreter has its own `sys.modules`, its own imported copies of pure-Python modules, its own module globals. Any in-memory cache or singleton sitting in a module global is per-sub-interpreter. Anything you previously assumed worked process-wide now works only interpreter-wide.

Each sub-interpreter pays its own import cost. Memory and startup time scale with the number of sub-interpreters. The point of per-interpreter GIL is parallelism within a single process; the cost is that every sub-interpreter independently imports the application and everything it depends on.

The main interpreter remains special. To repeat the point from earlier, if your application is running in the main interpreter, which happens when `WSGIApplicationGroup %{GLOBAL}` is set, often because some C extension forced your hand, `WSGIPerInterpreterGIL` does nothing for it. The main interpreter always holds the process-wide GIL.

Background threads must be non-daemon. Sub-interpreters that hold their own GIL do not allow Python code to create daemon threads. Anything your application spawns via `threading.Thread` must run as a non-daemon thread, which is the opposite of what most Python code defaults to when it wants a worker that quietly exits with the process. That restriction comes with an awkward shutdown problem. Python only runs `atexit` handlers after it has tried to join non-daemon threads during sub-interpreter teardown, so the common pattern of signalling background workers to stop from an `atexit` handler will deadlock. In a mod_wsgi context the right answer is to hook mod_wsgi's own shutdown callbacks instead, which fire early enough to let your threads drain and exit cleanly. That shutdown API is worth a post of its own. For the purposes of this one, the point is that if your WSGI application relies on daemon threads or `atexit`-driven cleanup, this is the one situation where enabling `WSGIPerInterpreterGIL` may force application-side code changes.

## What this means for C extension authors

This is the part that turns most attempts to enable `WSGIPerInterpreterGIL` into a hunt through the dependency tree, and it is the part I want extension authors to take seriously.

Restrictions on what works under sub-interpreters are not new. mod_wsgi users have been running into the rough edges of the simplified `PyGILState_Ensure` / `PyGILState_Release` API in sub-interpreters for years. The `WSGIApplicationGroup %{GLOBAL}` directive exists in part as a pragmatic answer for extensions that assume there is only one interpreter in the process. Per-interpreter GIL tightens those rules further, but it does not invent a new category of problem.

What does change is that explicit opt-in is now required. The extension must use [PEP 489](https://peps.python.org/pep-0489/) multi-phase module initialisation. Extensions still using single-phase init will not be loaded into a sub-interpreter that holds its own GIL. The extension must also declare `Py_mod_multiple_interpreters` with the value `Py_MOD_PER_INTERPRETER_GIL_SUPPORTED` in its `PyModuleDef_Slot` array, like this:

```c
static PyModuleDef_Slot module_slots[] = {
    {Py_mod_exec, module_exec},
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {0, NULL},
};
```

Without that declaration, the import fails when a sub-interpreter that holds its own GIL tries to load the module. The failure happens on first import, not at server startup, so it can take a request through a code path that has not been touched in a while to expose it.

Module state needs to be per-interpreter. Anything stashed in a C-level static (counters, caches, registered callbacks, type objects pointing at process-wide globals) breaks isolation between sub-interpreters and produces bugs that will not show up until two interpreters race over the shared state. The right answer is to move the state into module state retrieved via `PyModule_GetState`. Code still using the simplified `PyGILState` API needs to be reviewed too, or replaced with the explicit `PyThreadState`-based APIs where the assumption of a single interpreter does not hold.

For operators, the message is the unglamorous one. Before turning `WSGIPerInterpreterGIL` on in any kind of production setting, work through every C extension your application pulls in, directly and transitively. "Works on Python 3.12" is not the same as "works under per-interpreter GIL". The popular extensions are working through these requirements on their own timelines, and the situation will keep improving, but right now it is still on you to check.

## What's next

If you maintain a mod_wsgi deployment and the per-interpreter GIL story is interesting to you, please try the 6.0.0 release candidate against a real workload and file issues against [the GitHub project](https://github.com/GrahamDumpleton/mod_wsgi) for anything that breaks or behaves oddly. The whole point of the RC period is to find out what does not work before the final release goes out.

The next post in this series will cover `WSGIFreeThreading`, the second new concurrency directive in 6.0.0 and the one that targets PEP 703 free-threaded Python builds. The constraints there are different again, and worth their own treatment.

For reference:

- [mod_wsgi documentation](https://modwsgi.readthedocs.io/en/latest/)
- [mod_wsgi 6.0.0 release notes](https://modwsgi.readthedocs.io/en/latest/release-notes/version-6.0.0.html)
- [Per-interpreter GIL and free-threading user guide](https://modwsgi.readthedocs.io/en/latest/user-guides/gil-modes-and-free-threading.html)
- [`WSGIPerInterpreterGIL` directive documentation](https://modwsgi.readthedocs.io/en/latest/configuration-directives/WSGIPerInterpreterGIL.html)
- [PEP 684: A Per-Interpreter GIL](https://peps.python.org/pep-0684/)
- [PEP 734: Multiple Interpreters in the Stdlib](https://peps.python.org/pep-0734/)
- [PEP 489: Multi-phase extension module initialization](https://peps.python.org/pep-0489/)
