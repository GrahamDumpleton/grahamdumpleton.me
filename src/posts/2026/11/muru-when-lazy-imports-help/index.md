---
title: "Muru: when lazy imports help"
description: "Why lazy imports that speed up a command line tool can make a pre-forking web server worse, and how Muru measures imports so you can decide what to defer and what to preload."
date: 2026-11-22
tags: ["python", "muru"]
draft: true
---

Lazy imports are having a moment. Python 3.15 adds a `lazy import` statement, from [PEP 810](https://peps.python.org/pep-0810/), and a module can name imports it wants deferred in a `__lazy_modules__` list. A deferred import binds its name straight away, but the module isn't loaded until the code first uses it. Most of the excitement is about command line tools. A tool which imports everything it might ever need, just to print its `--help`, can start in a fraction of the time when most of those imports are deferred.

A web application served by a pre-forking server is a different calculation, and deferring imports there can make things worse rather than better. Whether it helps depends on the application, on how it is deployed, and on what its requests actually use, which is why Muru measures imports rather than leaving it to guesswork.

## Where import time goes under Muru

As covered in the [import once, fork many](/posts/2026/11/muru-import-once-fork-many/) post, Muru imports an application once in a host process, and forks the workers from it. Everything the host imported is shared by the workers through copy on write memory, and is paid for once.

Under the Muru daemon, a deploy starts a new release beside the one serving, as covered in the [releases, not restarts](/posts/2026/11/muru-releases-not-restarts/) post, and traffic only moves to it once it is ready. However long the new release takes to import the application, nobody visiting the site waits for it. Deferring an import doesn't save anyone any time there. What it does is move the cost into the first request in each worker which uses the module, and since each worker then loads the module itself, its memory is no longer shared.

Under `muructl serve` in a container, a new release is a new container, and the import is part of how long it takes to start. A shorter start makes a rollout or a scale-out finish sooner. Even so, as covered in the [working with Kubernetes](/posts/2026/11/muru-working-with-kubernetes-not-around-it/) post, Muru's readiness probe doesn't pass until the application is loaded and the workers are ready, so a new pod still gets no requests before it can serve them.

There are times when someone does wait for the import. A release [scaled to zero](/posts/2026/11/muru-scaling-to-zero/) with its host stopped makes the next request wait for the host to start and import the application. And `muructl run` in development loads the application again every time a file changes.

So a deferred import can help or hurt, depending on how the application is run and how often its requests use what was deferred. To decide, it helps to know what each import costs, and what the workers end up loading anyway.

## A shop with two slow imports

The example for this post is a small Flask shop with two features that need large libraries. A stock report uses pandas:

```python
# shop/reports.py
import pandas

from shop.data import BOOKS


def stock_value():
    frame = pandas.DataFrame(BOOKS, columns=["title", "author", "stock", "price"])
    frame["value"] = frame["stock"] * frame["price"]
    return frame.groupby("author")["value"].sum().to_string()
```

and a download of the stock list as a spreadsheet uses openpyxl:

```python
# shop/export.py
import io

import openpyxl

from shop.data import BOOKS


def workbook():
    book = openpyxl.Workbook()
    ...
```

Someone has already tried to keep start-up fast, so the view for the report imports `shop.reports` inside the function, while `shop.export` is imported at the top of the application's module like everything else:

```python
from flask import Flask, Response, render_template_string

from shop import export
from shop.data import BOOKS

app = Flask(__name__)

...

@app.route("/report")
def report():
    from shop import reports

    return render_template_string(REPORT, report=reports.stock_value())
```

It runs under `muructl run` with two worker processes, on Python 3.14.

## What the host's load costs

Muru can record every import the host makes while it loads the application, using the profile recorder of [unwrapt](https://unwrapt.readthedocs.io/), a package for lazy imports which I wrote alongside Muru. With unwrapt added to the project's dependencies, `import_report` turns it on:

```toml
[tool.muru]
entrypoint = "shop.app:app"
import_report = true
```

<!--
RETAKE after muruhq/muru#788 (from-imports not counted: Flask, shop.export and anything loaded by a
`from` statement are missing, so the 75.8 ms total and "most of the load was openpyxl" are understated),
#784 ("modules loaded" counts top-level packages; rows imported by importlib._bootstrap) and #786.
-->

`muructl debug imports` then prints a report of the host's load:

```
$ muructl debug imports
Import report of the host's load of shop@r1: outcome fork, Python 3.14.8, 2 workers
  75.8 ms importing, 18 modules loaded, 4096 import calls; deferring what can be deferred would save about 73.4 ms

Advice
  defer: openpyxl imported by shop.export, 65.3 ms, loading entrypoint
    paid by the host, once before the fork, shared by the 2 workers; deferred, each worker that uses it loads it on first use
    add 'openpyxl' to __lazy_modules__ in shop.export
      __lazy_modules__ = ['openpyxl']
  defer: numpy imported by openpyxl.compat.numbers, 25.3 ms, loading entrypoint
    paid by the host, once before the fork, shared by the 2 workers; deferred, each worker that uses it loads it on first use
    defer it in openpyxl.compat.numbers with an entry of [tool.unwrapt.lazy_modules]
      [tool.unwrapt.lazy_modules]
      "openpyxl.compat.numbers" = ["numpy"]

Imports that loaded a module, by cumulative time
  CUM MS SAVES MS IMPORTED        IMPORTED BY                  LOADING    3.15 UNWRAPT NOTES
    65.3     65.3 openpyxl        shop.export                  entrypoint yes  yes
    25.3     25.3 numpy           openpyxl.compat.numbers      entrypoint yes  yes
     4.9      0.0 numpy.matrixlib numpy.lib._index_tricks_impl entrypoint yes  yes
     4.7      0.0 click           flask.app                    entrypoint yes  yes
...
```

Most of the load was openpyxl, and the numpy it imports in turn. The advice for each import says what deferring it would mean, and the configuration to write. For the shop's own code, that is a `__lazy_modules__` list in the module making the import. For an import inside a package the project depends on, such as numpy here, where nobody wants to edit openpyxl's source, it is an entry of unwrapt's `[tool.unwrapt.lazy_modules]` table, naming the importing module and what to defer in it. The 3.15 and UNWRAPT columns say whether each way of deferring can defer that import as written, since Python 3.15 can defer a `from` import while unwrapt can only defer a plain `import`.

The same report comes from `muructl check --imports`, which loads the application once without serving anything, so it can be run before and after a change, or in CI.

## Deferring an import

The spreadsheet export is used rarely, so deferring openpyxl looks worthwhile. That takes two changes. The module names the import in `__lazy_modules__`, before the import itself:

```python
# shop/export.py
__lazy_modules__ = ["openpyxl"]

import io

import openpyxl
```

and the project turns on `lazy_imports`:

```toml
[tool.muru]
entrypoint = "shop.app:app"
import_report = true
lazy_imports = true
```

Python 3.15 and later act on `__lazy_modules__` by themselves. Python 3.11 to 3.14 ignore it, and with `lazy_imports` on, Muru has unwrapt defer the imports it names instead, so the same code defers on every version of Python Muru supports. The `lazy import` statement can't be used that way, since it is a syntax error before 3.15.

As the host forks, it says what was deferred, and whether anything used a deferred import before the fork anyway, in which case deferring it saved nothing:

```
muru.host[74803]: lazy_imports: 1 import deferred, none of them used before the fork
```

How much this saved needs more than one measurement, since a load's time varies from one start to the next by about as much as the difference being measured. A `muru.local.toml` beside the project overrides the project's settings for my own runs only, so `lazy_imports = false` in it turns deferral off without changing `pyproject.toml`. With `import_report = false` there as well, since recording the imports adds to the load, I started the run five times each way. The host took a median of 86 milliseconds to load the application without deferral, and 36 milliseconds with it.

The cost hasn't gone away though, it has moved. The first request for the spreadsheet in a worker now loads openpyxl, and the numpy it imports in turn:

```
server-timing: queue;dur=0.00, app;dur=75.59, import;dur=71.66, muru;desc="01M7PHGJ2M3VH05BSP37JY8X28"
```

The `import` entry in `Server-Timing` is the time the request spent loading modules for the first time in its worker. The request's Timing panel, on the dashboard here since a spreadsheet has no page for the toolbar, shows it as an "importing modules" row, and its list of the modules loaded marks the one that resolved a deferred import, with the line of code that first used it:

![The dashboard's Timing panel for the spreadsheet download, with importing modules taking most of the request, and the modules loaded on first use](deferred-timing.png)

```
  Modules loaded on first use
    openpyxl (deferred)  0.4ms  29ms  shop/export.py:11
      openpyxl.compat  0.7ms  0.4ms  openpyxl/__init__.py:5
        openpyxl.compat.numbers  0.8ms  0.1ms  openpyxl/compat/__init__.py:3
        openpyxl.compat.strings  0.9ms  0.1ms  openpyxl/compat/__init__.py:4
      openpyxl.xml  1.1ms  0.1ms  openpyxl/__init__.py:6
      openpyxl.workbook  1.3ms  25ms  openpyxl/__init__.py:7
...
```

Line 11 of `shop/export.py` is `book = openpyxl.Workbook()`, the first use of the module.

I also tried the report's second piece of advice, deferring numpy inside openpyxl with the `[tool.unwrapt.lazy_modules]` entry it gave. The list of modules for the next first download showed `numpy (deferred)` being loaded from line 16 of `openpyxl/compat/numbers.py`, while openpyxl itself was still loading. That module uses numpy at the top level, straight after importing it, to build a tuple of numeric types, so the deferred import is used the moment it is made and deferring it saves nothing. I took the entry out again. The report can only say what an import cost and whether it could be deferred, not whether the code will use it straight away, which is another reason to check a deferral against what the workers actually do.

## Asking the workers

Whether moving that cost was worth it depends on how many workers end up paying it, and that depends on the traffic. After the run had served some pages, several stock reports and one spreadsheet, the second half of `muructl debug imports` asked each worker what it had loaded for the first time since the fork:

```
Modules the 2 workers asked loaded for the first time since the fork
  MODULE                      LOADED BY FIRST REQUEST                 MS ADVICE
  shop.reports                2 of 2    01M7PH8GJ4ZX8NC4P53G6DXZFK 140.8 every worker loads it: load it before the fork with preload_modules = ["shop.reports"]
  openpyxl (deferred)         1 of 2    01M7PH8GS1ZX8NC4P53G6DXZFV  46.9 deferral pays off: only some workers load it
  encodings.idna              2 of 2    01M7PH8GHHZX8NC4P53G6DXZFJ   2.1 every worker loads it: load it before the fork with preload_modules = ["encodings.idna"]
  openpyxl.packaging.extended 1 of 2    01M7PH8GS1ZX8NC4P53G6DXZFV   0.1 loading on first use pays off: only some workers load it
```

The two features come out on opposite sides. Only one worker had needed openpyxl, so the other was spared both the time and the memory, and the deferral paid off. Every worker had needed `shop.reports`, and each loaded pandas itself, about 140 milliseconds a time, which the function level import in the view had pushed into the first report each worker served.

That first report is also worse than it looks. With three requests for the report sent at once, two of them went to the same worker on different threads, and both took 125 milliseconds. One was loading pandas, and the other was waiting on Python's import lock for it to finish. The first requests after a deploy, or after a scale-out adds workers, are exactly when that happens.

## Loading before the fork

A module that every worker loads is better loaded once, in the host, before the fork. `preload_modules` lists modules for the host to import after the application, as part of the same load:

```toml
[tool.muru]
entrypoint = "shop.app:app"
import_report = true
lazy_imports = true
preload_modules = ["shop.reports"]
```

The host's load now includes pandas, and the first reports in each worker took from one and a half to nine milliseconds, rather than more than a hundred.

`preload_modules` is also the way to undo a deferral you don't want. Once Python 3.15 is common, libraries will start using `lazy import` themselves, for their own command line tools or their own start-up time, and in a web application that may move a library's import into the first request of each worker. Listing the module in `preload_modules` loads it before the fork regardless, and the deferred import finds it already loaded when the code first uses it.

## After more traffic

The advice is only as good as the traffic the workers have seen. After a few more downloads of the spreadsheet, both workers had served one:

```
Modules the 2 workers asked loaded for the first time since the fork
  MODULE                      LOADED BY FIRST REQUEST                MS ADVICE
  openpyxl (deferred)         2 of 2    01M7PH3ZDGCR5SGD0G3G63RV6H 36.4 every worker loads it, so deferring it gains nothing: load it before the fork with preload_modules = ["openpyxl"]
  encodings.idna              2 of 2    01M7PH3ZATCR5SGD0G3G63RV68  2.0 every worker loads it: load it before the fork with preload_modules = ["encodings.idna"]
  openpyxl.packaging.extended 2 of 2    01M7PH3ZDGCR5SGD0G3G63RV6H  0.2 every worker loads it: load it before the fork with preload_modules = ["openpyxl.packaging.extended"]
```

With two workers running for a long time, a module that any request uses at all eventually ends up loaded in all of them, at which point the deferral bought nothing but a slower first request in each. With more workers, workers that are replaced after a number of requests, or an autoscaler which adds and removes workers as load changes, many workers may never get as far as needing it. Which of those describes a production deployment is something only its own traffic can say, so this is a question to ask of a running release rather than a development run. The same counts are kept as metrics, `muru_worker_modules_loaded_total` and `muru_worker_module_load_seconds_total`, so they can be watched over time.

## What's next

Lazy imports are a useful tool, but in a web application served by a pre-forking server they are a trade between the host's load, the first request in each worker, and how much memory the workers share. Muru gives you the measurements to make that trade for your own application. The `Server-Timing` header and the Timing panel show what a request paid for imports, the import report shows what the host's load costs and where to cut it, and the workers say what they ended up loading anyway. Deferral through unwrapt works the same from Python 3.11 to 3.15, and `preload_modules` puts back what shouldn't have been deferred.

The next post, working with coding agents, is about something else doing things through Muru. Coding agents are increasingly the ones running, deploying and debugging applications, and Muru gives them a way in through MCP, so an agent can deploy each change as a release, read the events, logs and worker stacks when something fails, and roll back, using everything the earlier posts covered.
