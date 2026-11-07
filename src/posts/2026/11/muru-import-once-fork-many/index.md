---
title: "Muru: import once, fork many"
description: "How Muru imports a Python web application once and forks workers from it, checks the import is safe to fork, and how processes, threads and free-threading fit in."
date: 2026-11-09
tags: ["python", "muru"]
draft: true
---

Every time Muru has started an application in this series, starting with [a first look at Muru](/posts/2026/11/a-first-look-at-muru/), one of the first lines of output has been something like:

```
muru.host[88644]: preloaded app:application in 1 ms
```

In [how it fits together](/posts/2026/11/muru-how-it-fits-together/) I described the host as the Python process which imports the application once and forks the workers from it, but skipped over what that involves. It is time to come back to it, because how an application gets loaded into worker processes is one of those things that matters a lot for Python, and is easy to get wrong.

## Why import once

To see what is going on, here is an application which records the process ID at the point the module was imported, and then reports that along with the process ID handling each request:

```python
import os

IMPORTED_IN = os.getpid()

def application(environ, start_response):
    body = f"imported in {IMPORTED_IN}, serving from {os.getpid()}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
```

Running it with two worker processes:

```
muructl run app:application --processes 2
```

```
muru.host[88644]: preloaded app:application in 1 ms
muru.host[88644]: app:application is served as WSGI
muru.host[88644]: worker 0 started as pid 88645
muru.host[88644]: worker 1 started as pid 88646
muru.host[88644]: worker 0 (pid 88645) is ready
muru.host[88644]: worker 1 (pid 88646) is ready
muru: serving app:application on http://127.0.0.1:8080 with 2 workers of 4 threads
```

and making a few requests, the result being:

```
imported in 88644, serving from 88646
imported in 88644, serving from 88645
imported in 88644, serving from 88646
imported in 88644, serving from 88645
```

The application was imported once, in the host process, and both workers were then forked from the host. Neither worker ever imported the application itself. Each started out as a copy of the host with every module already loaded.

For a toy application this makes no difference. For a large Django application, where importing everything can take several seconds and a lot of memory, it makes a big difference. Forked workers share the memory pages holding those modules with the host, and with each other, until something writes to them. Starting a new worker, whether to replace one that crashed, to recycle one that has grown too large, or to add capacity, costs a fork rather than a full import. Muru also takes care to freeze the garbage collector's view of the preloaded objects before forking, so that collections in the workers don't go touching, and therefore copying, all those shared pages.

This was one of the things I always wanted for mod_wsgi daemon mode but couldn't have. The daemon processes in mod_wsgi are forked by the Apache parent process, and that isn't a place where it is safe to load application code. Each daemon process therefore has to import the application itself, and restarting one means paying for that import again.

## What doesn't survive a fork

Preloading isn't a new idea, and other Python WSGI servers have had an option for it for a long time. The reason it is usually an option, rather than the default, is that it can break applications in subtle ways.

Forking copies a process's memory, but some things live outside of memory. A socket is a kernel object, so after a fork both the parent and child hold the same connection, each thinking it is theirs alone. A thread exists only in the process which started it, so a background thread started during import simply doesn't exist in the workers, even though all its data structures do. A child process has one parent, so the workers can't manage a helper process the host launched.

So if importing the application opens a database connection, starts a thread to flush metrics, or launches a helper process, preloading produces workers that are quietly broken. Worse, these problems tend to be intermittent, and show up in production under load rather than on the first request you make in development.

## The import check

What Muru does differently is that it doesn't just trust you to know whether your application is safe to preload. When the host imports the application, it records any sockets, pipes, threads and child processes that were left behind by the import.

To show this, here is a module standing in for a database client which connects when it is imported, as some do:

```python
import socket

# Pretend this is a database client connecting when the module is imported.
connection = socket.create_connection(("127.0.0.1", 9340))
```

The WSGI application in `shop/wsgi.py` imports it with `from shop import db`. Running it gives:

```
muru.host[88997]: preloaded shop.wsgi:application in 2 ms
muru.host[88997]: shop.wsgi:application is served as WSGI
muru.host[88997]: preload: the import of shop.wsgi left a connected socket (fd 3, to 127.0.0.1:9340); close it in a pre_fork hook and reopen it in post_fork, or open it lazily on first use
muru.host[88997]: preload: falling back to per-worker imports, which costs slower worker replacement and no shared memory; set preload to false to silence this
muru.host[88997]: worker 0 started as pid 89031
muru.host[88997]: worker 1 started as pid 89032
muru.worker[0]: worker 0 imported shop.wsgi:application in 2 ms
muru.worker[0]: worker 0 serves shop.wsgi:application as WSGI
muru.host[88997]: worker 0 (pid 89031) is ready
muru.worker[1]: worker 1 imported shop.wsgi:application in 2 ms
muru.worker[1]: worker 1 serves shop.wsgi:application as WSGI
muru.host[88997]: worker 1 (pid 89032) is ready
```

Muru found the connected socket, said where it goes, and decided not to fork from the host. Instead it fell back to having each worker import the application itself, which is always safe. The application still works, it just loses the benefits of preloading, and the message tells you what you would need to change to get them back.

Threads are caught the same way. Here is a module which starts a background thread when imported, to periodically report how many requests have been handled:

```python
import threading
import time

counts = {"requests": 0}

def flush():
    while True:
        time.sleep(5)
        print(f"flushed {counts['requests']} requests", flush=True)

threading.Thread(target=flush, daemon=True).start()
```

Under a naive preload this thread would run in the host process, which never handles a request, and so would forever report zero. The workers doing the actual work would have no thread at all. Muru spots it:

```
muru.host[89680]: preload: the import of stats left a thread running; start it from a post_fork hook instead
muru.host[89680]: preload: falling back to per-worker imports, which costs slower worker replacement and no shared memory; set preload to false to silence this
```

## Doing things at the right time

Most things which are wrong to do at import time are perfectly fine to do a moment later, once the worker exists. For that Muru supports a hooks module, named with the `--hooks` option or with `hooks` in the `[tool.muru]` table of `pyproject.toml`. The module can define functions to be called at different points in the life of the host and its workers.

The one you will need most is `post_fork`, which is called in each worker immediately after it is forked. For the metrics thread, the module is changed to provide a function to start the thread rather than starting it on import:

```python
def start():
    threading.Thread(target=flush, daemon=True).start()
```

and a `hooks.py` calls it:

```python
import stats

def post_fork(context):
    print(f"worker {context.worker_id} starting the stats thread", flush=True)
    stats.start()
```

Each hook is passed a context object which says where it is running, including the index of the worker. Running with the hooks module and two processes:

```
muructl run app:application --hooks hooks --processes 2
```

```
muru.host[90139]: preloaded app:application in 1 ms
muru.host[90139]: app:application is served as WSGI
muru.host[90139]: worker 0 started as pid 90140
muru.host[90139]: worker 1 started as pid 90141
muru.worker[0].stdout: worker 0 starting the stats thread
muru.host[90139]: worker 0 (pid 90140) is ready
muru.worker[1].stdout: worker 1 starting the stats thread
muru.host[90139]: worker 1 (pid 90141) is ready
...
muru.worker[0].stdout: flushed 3 requests
muru.worker[1].stdout: flushed 3 requests
```

The import check passes, the host preloads, and each worker gets its own thread. Note that each worker reports its own count. The `counts` dictionary started out shared from the host, but the moment a worker writes to it, it has its own copy. Anything that needs to be shared across workers has to live somewhere else, such as a database or a metrics system.

The database connection is dealt with in the same way. The module provides a `connect()` function rather than connecting on import, and a `post_fork` hook calls it, so that each worker opens its own connection. Alternatively, the connection could be opened lazily on first use, which many database libraries already do.

Beyond `post_fork`, there is `on_load` for things to run once in the host after the import, such as warming caches that are safe to share, and `pre_fork` which runs in the host before the first fork. In the workers, `on_ready` runs just before a worker starts taking requests, `on_drain` when it has been told to stop, and `on_exit` after its last request. When the fallback to per-worker imports is in effect, `on_load` and `pre_fork` are run in each worker before `post_fork`, so the same hooks module works either way.

## Choosing how strict to be

What happens when the import check fails is controlled by the `preload` setting, which can be given as an option or set in `[tool.muru]`. The default is `auto`, which is what you have seen so far, preloading when the check passes and falling back with a warning when it doesn't.

Setting it to `true` makes a failed check an error. Going back to the version of the shop which connected on import:

```
muructl run shop.wsgi:application --preload true
```

```
muru.host[89241]: preload: the import of shop.wsgi left a connected socket (fd 3, to 127.0.0.1:9340); close it in a pre_fork hook and reopen it in post_fork, or open it lazily on first use
muru.host[89241]: preload is true, so the import check failing stops the release
Error: the host exited with exit status: 1 before its workers were ready
```

This is what you want in production. Once an application has been made safe to preload, you don't want a change by someone that breaks that to quietly fall back to per-worker imports and go unnoticed until someone wonders why memory use went up.

Setting it to `false` skips preloading and the check altogether, with each worker importing the application:

```
muru.host[89381]: worker 0 started as pid 89382
muru.host[89381]: worker 1 started as pid 89384
muru.worker[1]: worker 1 imported shop.wsgi:application in 5 ms
muru.worker[1]: worker 1 serves shop.wsgi:application as WSGI
muru.worker[0]: worker 0 imported shop.wsgi:application in 13 ms
muru.worker[0]: worker 0 serves shop.wsgi:application as WSGI
```

That is for applications which can't be made fork safe, or where you have decided it isn't worth the effort.

## Processes and threads

Preloading is about how workers come to exist. The other half of the process model is what runs inside each worker. By default a WSGI worker has four threads, each of which handles one request at a time, and you choose how many worker processes to have and how many threads each gets.

For most web applications, which spend their time waiting on databases and other services, threads work well. On a regular Python interpreter though, only one thread can be running Python code at a time because of the global interpreter lock (GIL). Waiting on a database releases the GIL so other threads can get on with things, but code that is busy computing holds it.

To show the effect, here is an application which does some pure Python computation for each request:

```python
import sys

def work(n):
    total = 0
    for i in range(n):
        total += i * i
    return total

def application(environ, start_response):
    work(10_000_000)
    gil = "enabled" if sys._is_gil_enabled() else "disabled"
    body = f"done, GIL {gil}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(body)))])
    return [body]
```

Running this on a regular build of Python 3.15, with the default of one worker and four threads, and firing off four requests at the same time, all four had finished after about 1.3 seconds. The access log shows each request taking most of that:

```
200 GET / 18B 1.19s queue=0.0ms app=1.19s worker=0 id=01M6JWV35JYRMR8K10KBMQ1H5N
200 GET / 18B 1.21s queue=0.0ms app=1.21s worker=0 id=01M6JWV35JYRMR8K10KBMQ1H5J
200 GET / 18B 1.27s queue=0.1ms app=1.27s worker=0 id=01M6JWV35JYRMR8K10KBMQ1H5K
200 GET / 18B 1.28s queue=0.1ms app=1.28s worker=0 id=01M6JWV35JYRMR8K10KBMQ1H5M
```

There were enough threads, so nothing waited in the queue, but the four threads had to take turns holding the GIL, and so each request took about four times as long as it would on its own. This is a good illustration of why the `queue` and `app` times aren't the whole story. Here the time is being charged to the application, yet the code isn't any slower, it is waiting for the GIL. Muru does keep track of time spent waiting for the GIL separately, which I will come back to in a later post.

The traditional answer for CPU bound work is to use processes rather than threads. Running the same thing with `--processes 4 --threads 1`, so each request gets a process of its own, all four requests finished in about 0.5 seconds.

## Free-threaded Python

Python 3.14 brought official support for free-threaded builds of the interpreter, where the GIL is removed and threads can run Python code in parallel. The uv tool knows them by names like `3.15t`, so a project only needs a `.python-version` file containing `3.15t` for `uv venv` to create its virtual environment from a free-threaded build of Python 3.15.

Muru supports these builds from the start. Its runtime library was written for them rather than adapted later, and it fetches the right build of the library for whichever kind of interpreter the project uses. Running the same application on the free-threaded build, again with one worker and four threads, all four requests were done in about 0.36 seconds:

```
200 GET / 19B 331ms queue=0.1ms app=331ms worker=0 id=01M6JWV8A36WZSBQEFEM4EZ7W5
200 GET / 19B 331ms queue=0.1ms app=331ms worker=0 id=01M6JWV8A36WZSBQEFEM4EZ7W7
200 GET / 19B 334ms queue=0.1ms app=334ms worker=0 id=01M6JWV8A36WZSBQEFEM4EZ7W6
200 GET / 19B 336ms queue=0.0ms app=336ms worker=0 id=01M6JWV8A36WZSBQEFEM4EZ7W4
```

The four threads ran in parallel within the one process, each request taking only as long as it would have on its own. These are rough numbers from my laptop rather than a proper benchmark, but the difference is clear enough.

This changes the trade-off between processes and threads. Processes still give you isolation, so that a crash, a memory leak or a stuck request takes down one worker rather than all of them. But you no longer need lots of processes just to make use of every CPU core, and fewer processes with more threads means sharing caches and connection pools rather than duplicating them.

One thing to watch for is that importing an extension module which hasn't declared support for free-threading causes the interpreter to turn the GIL back on. That is why the example reports whether the GIL is enabled. Your application can end up running on a free-threaded build with the GIL on and not realise it, which is something Muru keeps an eye on as well.

## What's next

Having an application imported once, with the check to make sure that is safe, and with workers forked from it, is the foundation for much of what Muru does later, such as starting new releases quickly and scaling the number of workers up and down. The next post will be a shorter one, on something a development run does which most development servers don't, which is serve HTTPS with a certificate your browser will trust.
