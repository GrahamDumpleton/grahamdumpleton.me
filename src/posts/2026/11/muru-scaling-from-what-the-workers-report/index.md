---
title: "Muru: scaling from what the workers report"
description: "How the Muru daemon decides how many workers a release needs, and the diagnosis that says when the answer isn't more workers but a change to the release."
date: 2026-11-16
tags: ["python", "muru", "scaling"]
draft: true
---

In the [Kubernetes post](/posts/2026/11/muru-working-with-kubernetes-not-around-it/) the scaling was done from outside. Muru published how busy its worker slots were, and a HorizontalPodAutoscaler added pods when the number went over a target. That works, but it can only ever add pods, and it has no idea why the slots were busy. Back on a host running the Muru daemon, Muru decides for itself how many worker processes each release has, and because it sits between the requests and the workers, it can say rather more about why requests are waiting than a single number.

Most Python web servers don't scale the number of processes at all. Gunicorn starts the number of workers it is told to, and the only way to change that while it runs is to send it SIGTTIN or SIGTTOU, which add or remove one worker. Uvicorn and granian both take a fixed `--workers` count, and mod_wsgi's daemon mode has a fixed number of processes set in the Apache configuration. The exception is uWSGI, whose cheaper subsystem can spawn and stop workers based on how many are busy, or on the backlog of connections waiting to be accepted.

So adding workers when they are all busy isn't new, and if that were all Muru did it wouldn't be worth a post. What is different is what Muru does with everything else it knows about the workers, and whether more workers is even the right answer.

## Growing and shrinking

The application for this post has a few pages which each misbehave in a different way. The first, `/orders`, sleeps for a fifth of a second as if waiting on a database. The release starts with one worker of two threads, and has a scaling policy in spare mode, which tries to keep between one and three idle workers in hand, much as Apache httpd does with spare processes or threads:

```toml
[tool.muru]
entrypoint = "app:application"
processes = 1
threads = 2

[tool.muru.scaling]
mode = "spare"
min_workers = 1
max_workers = 12
min_spare = 1
max_spare = 3
scale_in_window = "30s"
hold_after_growth = "30s"
reap_interval = "5s"
min_lifetime = "10s"
idle_reap_after = "45s"
```

The last five settings shorten windows which default to minutes, so it all happens quickly enough to watch. I deployed it to a daemon and set sixteen clients asking for `/orders` over and over for a minute. Three seconds in, `muructl scale status` showed the group to be well short:

```
shop@r1
GROUP        WORKERS      SLOTS      IDLE    QUEUE-P95     REAPS      POLICY
default      1            2/2        -7.00   under 2.5 s   0/6        spare 1-12 workers, 1-3 idle
  workers: cpu -, gc -, gil wait p95 -, loop lag p95 -
  diagnosis: waiting for the workers' first report
```

Both slots were busy, the requests waiting at the edge were counted as seven workers' worth of slots wanted, and the 95th percentile of the time requests waited for a slot was in the seconds. The workers hadn't yet sent their first report, so the diagnosis had to wait for it. Once the shortage had held for the five second scale-out window, the daemon forked more workers, at most four at a time:

```
default: scale out from 1 to 5 workers: short by 7.00 workers for 5999ms; diagnosis: waiting for the workers' first report
default: scale out from 5 to 9 workers: short by 3.00 workers for 5999ms; diagnosis: I/O bound with exhausted slots; ...
```

Each new worker is a fork of the host which already imported the application, as covered in the [import once, fork many](/posts/2026/11/muru-import-once-fork-many/) post, so the second step came only seven seconds after the first. From then on the group sat at nine workers, sixteen of eighteen slots busy and one worker in hand, and the queue wait was under a millisecond.

After the load stopped, the workers were taken away again, but slowly, one at a time:

```
default: scale in from 9 to 8 workers: at least 9.00 idle workers over the last 30s, over max_spare 3; diagnosis: idle
default: scale in from 8 to 7 workers: at least 8.00 idle workers over the last 30s, over max_spare 3; diagnosis: idle
...
default: scale in from 4 to 3 workers: at least 4.00 idle workers over the last 30s, over max_spare 3; diagnosis: idle
```

and then stopped at three, with more than it needed:

```
default      3            0/6        3.00    -             6/6 halt   spare 1-12 workers, 1-3 idle
  ...
  last: suspended: 6 workers reaped in the last hour, the churn budget; scale-in is suspended and the scale-in window doubled until it recovers (1s ago)
```

Each release has a churn budget of six reaps an hour. I had shortened every window but left that alone, so it was spent and scale-in was suspended. It is there so that a badly tuned policy can't keep a group swinging up and down all day.

## When the answer is more threads

Once the workers had reported, the status had more to say. This is from while the group was still growing:

```
default      5            10/10      -1.00   under 2.5 s   0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: I/O bound with exhausted slots; for the next release, more threads per worker, or more concurrency for an ASGI application
```

The group's slots were all busy, but its workers were using no CPU at all. That is what waiting on a database looks like, and nine processes is a costly way to hold sixteen requests that are each just waiting. The suggestion was more threads per worker, and that can't be done by the autoscaler. A release's processes and threads are fixed when it starts, so the change goes into the next release.

I deployed the same application with `threads = 8` and ran the same load. Instead of nine workers it settled at three:

```
default      3            16/24      1.00    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 1%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
```

Over the minute it served 4440 requests compared with 4007, the 99th percentile response time was 0.409 seconds where before it was 1.623, as it needed only one step to scale out rather than two, and each of the three workers had 12MB of memory of its own:

```
WORKER  PID      GROUP      UP       REQUESTS   THREADS  THREAD-OLDEST  RSS     USS     ROUTED  STATE
0       67546    default    38s      1090       6/8      0.2s           18MB    12MB    yes     ready
1       67729    default    31s      813        5/8      0.0s           17MB    12MB    yes     ready
2       67730    default    31s      790        5/8      0.2s           17MB    12MB    yes     ready
```

## When the answer is fewer threads

More threads isn't always the answer. In the import once, fork many post I showed four threads of CPU bound code running four times slower than one, because they had to take turns holding the global interpreter lock, and said Muru kept track of time spent waiting for the GIL. This is where that comes in.

The `/prices` page does about 13 milliseconds of pure Python arithmetic. With the eight thread release still serving, and running on CPython 3.15 with the GIL, eight clients asking for it gave:

```
default      3            8/24       2.00    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 100%, gc 0%, gil wait p95 under 50 ms, loop lag p95 -
  diagnosis: GIL bound; for the next release, more processes with fewer threads each
```

By the measure the autoscaler uses, there was nothing to do. Only eight of the twenty-four slots were busy and there were two idle workers in hand. Yet the three workers were each using all of the one core the GIL lets them have, and the 95th percentile of the time threads with work to run waited for their turn was put at under 50 milliseconds. A request which takes 13 milliseconds on its own had a median time of 20 milliseconds.

An autoscaler working from busy slots or a connection backlog, Muru's own or uWSGI's, can't see this. Adding threads would make it worse, and adding workers wouldn't happen because the slots aren't full. The diagnosis says what would help, which is more processes with fewer threads each. I deployed the release again with one thread per worker:

```
default      9            8/9        1.00    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 86%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: CPU bound; for the next release, more processes, up to the node's cores; more threads will not help
```

Now each request occupied a whole worker, the slots filled, and the autoscaler took the group to nine workers on this ten core machine. It served 24863 requests in the 45 seconds compared with 18626, and the median time was 13 milliseconds.

The other way around the GIL is to not have one. I deployed the eight thread release again, with nothing changed but a `.python-version` of `3.15t`, so uv built its environment with the free-threaded build of Python 3.15:

```
default      2            7/16       1.12    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 48%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
```

Two workers of eight threads served 26040 requests in the same 45 seconds, a little more than the nine single threaded processes, with nothing waiting for a GIL. The CPU figure is now a share of a core per thread, as threads on a free-threaded build really can run in parallel.

## When the answer is less garbage

The `/search` page makes short lived objects, 40,000 dictionaries per request, in pairs which refer to each other. With a release of four threads per worker and four clients:

```
default      2            4/8        1.00    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 100%, gc 73%, gil wait p95 under 5 ms, loop lag p95 -
  diagnosis: paused by garbage collection of short-lived reference cycles; for the next release, break the cycles, or use weakref for the references back
```

Close to three quarters of the workers' time was going into garbage collection. A collection stops every thread in the process, so that time is lost to every request in flight.

The diagnosis says why. A dictionary only needs the garbage collector, rather than being freed as soon as nothing refers to it, when it is part of a reference cycle, and `muructl debug memory` showed the youngest generation's collections freeing hundreds of millions of objects. Long lived objects being scanned over and over don't get freed, so this was garbage being made and collected. Removing the reference back was a one line change:

```
default      2            4/8        1.00    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 100%, gc 0%, gil wait p95 under 1 ms, loop lag p95 -
  diagnosis: CPU bound; for the next release, more processes, up to the node's cores; more threads will not help
```

The garbage collection share went to zero, and in 40 seconds the release served 73637 requests where before it had served 17977, with the median time down from 8 milliseconds to 2. The diagnosis then moved on to the next thing holding the group back, which was now plain CPU.

## When the event loop is blocked

An ASGI application has one event loop per worker rather than a pool of threads, and one blocking call in a coroutine holds up everything else on that loop. This release had an `/invoice` page calling a function which blocks for a fifth of a second, as a synchronous client library would, directly from the coroutine. With eight clients on a page which awaits for 50 milliseconds, and one client on `/invoice`:

```
default      2            9/2000     1.99    under 1 ms    0/6        spare 1-12 workers, 1-3 idle
  workers: cpu 2%, gc 0%, gil wait p95 under 0.5 ms, loop lag p95 under 500 ms
  diagnosis: event loop held by blocking code; for the next release, await blocking calls, or run them in a thread, so the loop keeps serving
```

Each worker's event loop has a heartbeat twice a second, and the lag is how late it runs. Here it was hundreds of milliseconds late. The slots barely registered, nine busy of two thousand, which is the concurrency limit of two event loops, so nothing based on slots would ever have noticed. The page which should have taken 50 milliseconds had a 95th percentile of 0.410 seconds, as it kept getting stuck behind an invoice.

Changing the one line to `body = await asyncio.to_thread(render_invoice)`, so the blocking call ran in a thread, brought the loop lag down to under 5 milliseconds and the 95th percentile back to 0.054 seconds. The eight clients got through 6064 requests in 40 seconds instead of 2960.

## When the answer is a worker group

The last case is one slow endpoint making everything else wait. Here `/reports` takes two seconds and is used in bursts, ten requests at once every six seconds, alongside two clients steadily asking for `/orders`. The release had two workers of four threads and no scaling policy, but even a static release gets a diagnosis. Every few seconds it read:

```
default      2            2/8        1.50    under 2.5 s   -          static
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: a few heavy requests; for the next release, a worker group of their own for the slow paths
```

Most of the time the slots were mostly free, but the queue wait was in the seconds, because each burst of reports took every slot and `/orders` requests arriving then waited behind them. For `/orders` the median response time was fine at 0.208 seconds, but one in a hundred requests took over two seconds.

Scaling out would help for a moment, until the next burst took all the extra slots as well. What the diagnosis suggests is separating the slow paths, so I gave them a worker group of their own, forked from the same host:

```toml
[tool.muru]
entrypoint = "app:application"
processes = 2
threads = 4

[tool.muru.groups.reports]
paths = ["/reports"]
processes = 1
threads = 12
```

Each group then gets its own line, and its own diagnosis:

```
default      2            2/8        1.50    under 1 ms    -          static
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
reports      1            10/12      0.17    -             -          static
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: I/O bound with exhausted slots; for the next release, more threads per worker, or more concurrency for an ASGI application
```

The reports now only compete with each other. For `/orders`, the slowest of the 389 requests took 0.212 seconds, where before the 99th percentile was 2.093. Each group can have its own scaling policy too, so a group like `reports` could be allowed to grow on its own when a burst arrives.

## Scaling to a target

Spare mode is about keeping idle workers in hand. The other mode, target mode, keeps the share of busy slots near a target, and can also scale on how long requests wait:

```toml
[tool.muru.scaling]
mode = "target"
min_workers = 1
max_workers = 8
slot_utilization = 0.6
queue_wait_p95 = "100ms"
```

With eight threads per worker and the same sixteen clients on `/orders`, it went straight to the count which would carry the load at the target:

```
default      4            16/32      2.00    under 1 ms    0/6        target 1-8 workers, 60% of slots busy, queue wait p95 100 ms
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
  last: scaled out to 4: 100% of slots busy, over the target of 60% for 6s (19s ago)
```

Sixteen busy slots at 60 percent needs about 27 slots, which is four workers of eight threads. This is much the same rule the HorizontalPodAutoscaler applied in the Kubernetes post, except that adding a worker here costs a fork rather than a new pod, and the diagnosis comes along with it.

## What's next

What the daemon does about the worker count is fairly conventional. Grow quickly when requests wait, shrink slowly, and don't thrash. The part I find more useful is the diagnosis, because in every case above except the first, adding workers was either not going to happen or not going to help. Whether the answer was more threads, fewer threads, a free-threaded interpreter, less garbage, a thread for a blocking call or a group of its own for a slow path, it was a change to the next release, and you only know which by measuring what the workers are actually doing.

Scaling also goes the other way. A server with many small sites, previews or staging copies doesn't want each of them holding workers while nobody is using it. The next post, scaling to zero, is about taking a release all the way down to no workers, and what it then costs for the next request to wake it up again.
