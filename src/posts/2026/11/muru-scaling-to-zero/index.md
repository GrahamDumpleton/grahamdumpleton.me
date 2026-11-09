---
title: "Muru: scaling to zero"
description: "How the Muru daemon takes an idle release down to no workers, then to no processes at all, what the next request pays at each stage, and how that interacts with a node's worker budget."
date: 2026-11-17
tags: ["python", "muru", "scaling"]
draft: true
---

The [last post](/posts/2026/11/muru-scaling-from-what-the-workers-report/) was about a busy release, and what the Muru daemon does when requests start to wait. The opposite problem is just as common. A server hosting a dozen small sites, a few preview deployments and a staging copy or two will spend most of its time with nearly all of them idle, and each one sitting there with its workers started is holding memory nobody is using.

Most Python web servers don't do anything about this. Gunicorn, uvicorn and granian keep the workers they started for as long as they run. mod_wsgi has long had an `inactivity-timeout` option for its daemon processes, which restarts a process once it has had no requests for a while, so its memory drops back to what it was before the application was loaded, and the next request waits while the application is loaded again. uWSGI has a cheap mode, where workers aren't spawned until the first request arrives, and an `idle` option to go back into cheap mode after a period of inactivity. Platforms such as Knative or Cloud Run scale whole containers to zero, and the next request waits for a new container to start and the application to be imported in it.

Muru does this in two stages, and the first is cheap because of how the daemon starts workers.

## No workers, but the host stays

Every release under the Muru daemon has a host process which imports the application once, and workers which are forked from it, as covered in the [import once, fork many](/posts/2026/11/muru-import-once-fork-many/) post. With a scaling policy whose `min_workers` is zero, the daemon will drain the last worker once nothing has needed it for a while, but leave the host running.

To make the difference between the stages obvious, the application for this post sleeps for three seconds when it is imported, standing in for a large application whose import is slow:

```toml
[tool.muru]
entrypoint = "app:application"
processes = 1
threads = 4

[tool.muru.scaling]
mode = "spare"
min_workers = 0
max_workers = 4
idle_reap_after = "20s"
scale_in_window = "20s"
hold_after_growth = "10s"
reap_interval = "5s"
min_lifetime = "5s"
```

As in the last post, the windows are shortened so this happens in seconds. By default `idle_reap_after` is ten minutes. Twenty seconds after the last request, the daemon took the worker away:

```
default: scale in from 1 to 0 workers: no request for 20s; diagnosis: idle
```

The release still shows as ready and serving, with no workers:

```
docs@r1
GROUP        WORKERS      SLOTS      IDLE    QUEUE-P95     REAPS      POLICY
default      0            0/0        0.00    -             1/6        spare 0-4 workers, 1-3 idle
  workers: cpu -, gc -, gil wait p95 -, loop lag p95 -
  diagnosis: idle
  last: scaled in to 0: no request for 20s (8s ago)
```

and of its processes, only the host was left. Listing the processes of one of the preview sites I come to below, which has the same policy, while serving and then at zero workers:

```
--- serving
56030 55119  46592 envs/preview-b/r1/bin/python -m muru.host --app app:applicati
56032 56030  17440 envs/preview-b/r1/bin/python -m muru.host --app app:applicati
--- zero workers
56030 55119  29392 envs/preview-b/r1/bin/python -m muru.host --app app:applicati
```

That saving is modest for one worker, and the host still holds the imported application. The point of this stage is what the next request costs. The edge holds the request as queued, the daemon forks a worker from the host, and the request is served by it:

```
default: scale out from 0 to 1 workers: a request is waiting for a group scaled to zero
```

```
docs from pid 55198
0.005145s
```

Five milliseconds, compared with a fraction of a millisecond once the worker was there. Nobody visiting a site will notice that, and it is only possible because the application was already imported in the host. A server which has to load the application again, as mod_wsgi does once its inactivity timeout has restarted the process, makes this first request wait for the import.

## No host either

For a site which might not see a request for hours, the host's memory can be given back as well. Adding `host_idle_timeout` to the release's scaling policy has the host stop once every worker group of the release has been at zero for that long:

```toml
host_idle_timeout = "30s"
```

Thirty seconds after the last worker went, the daemon stopped the host:

```
release.idle         docs@r2                  every worker group has been at zero for 30s: its host stopped, and the next request starts it again
```

The release has no processes at all now, but stays in the routing as ready, and `muructl release list` says what state it is in:

```
RELEASE                  STATE      SERVING  WORKERS          SOURCE
docs@r2                  ready      yes      - (1x4)          ...
                         idle: its host has stopped, and the next request starts it
```

This time the next request has to wait for the host to start and import the application:

```
docs from pid 55280
200 3.351380s
docs from pid 55280
200 0.000661s
```

```
release.woken        docs@r2                  a request is waiting: starting its host again
release.ready        docs@r2                  1 worker ready in 3.3 s
```

So there is a choice to make per release. Scaling to zero workers and keeping the host is nearly free for the next visitor. Stopping the host as well gives back everything, but the next visitor waits through the import. For a preview deployment nobody has looked at in a day, that is probably a fair trade. For a small site with occasional visitors, probably not.

## The queue timeout still applies

While a request waits for a worker to be forked, or for a host to start, it is in the edge's queue like any other request, and the queue timeout still applies. The default is five seconds. I set this release's to two seconds, less than its import takes:

```toml
[tool.muru]
entrypoint = "app:application"
processes = 1
threads = 4
timeouts = { queue_timeout = "2s" }
```

The request which woke the idle release got a 503 after exactly the queue timeout:

```
HTTP/1.1 503 Service Unavailable
content-type: text/plain; charset=utf-8
content-length: 155
cache-control: no-store
retry-after: 1
x-request-id: 01M6ZMF2Y40K8S7W1FVPQARCZD

503 Service Unavailable
reason: cold_start_timeout
request id: 01M6ZMF2Y40K8S7W1FVPQARCZD

No worker had started for the request within the queue timeout.
2.003713s
```

The host went on starting regardless, and a request a second and a half later was served in about a millisecond. The `Retry-After` header tells a well behaved client to come back after a second, which is the right answer. The body says no worker had started in time, and the access log records the reason `cold_start_timeout`, so this can be told apart from an overloaded release.

The lesson is that once a release's host can stop, its queue timeout has to cover its import, or the first visitor after a quiet spell gets an error.

## Many sites on one node

Scaling to zero is mostly about many applications sharing a server, and the daemon has a budget which caps what all the releases on the node hold between them. It goes in the daemon's configuration file:

```toml
[daemon.budget]
workers = 6
```

Memory and CPU can be capped the same way. I deployed four applications, each behind its own virtual host. One was a shop with the spare mode policy from the last post, and the other three were sites like the one above, two of them previews. With the three small sites idle, the budget showed only the shop's worker in use:

```
budget   1 of 6 workers
```

With sixteen clients asking for the shop's slow page, its scale-out stopped at the budget:

```
default      6            12/12      -1.50   under 250 ms  0/6        spare 1-12 workers, 1-3 idle
  ...
  last: held at 6: the node's worker budget (6 of 6 workers) (3s ago)
```

```
scaling.denied_by_budget shop@r1                  default: 1 of the 4 more workers asked for fit the node's worker budget (5 of 6 workers), at priority 0
```

That is the budget doing its job. Workers already running are never stopped to make room for another application, and when several releases want more at the same time, an application's `priority` decides which goes first. What happens to the sites scaled to zero while the budget is full is less obvious.

Neither kind of wake is held back by the workers limit. One preview had been idle long enough for its host to stop. A request for it woke it in the usual three seconds or so, with the event saying it went over the budget:

```
release.woken        preview-b@r1             a request is waiting: starting its host again, over the node's budget of 6 workers
```

```
budget   7 of 6 workers
```

The other preview still had its host, with zero workers, so it needed only a fork, and was served in six milliseconds:

```
scaling.decision     preview-a@r1             default: scale out from 0 to 1 workers: a request is waiting for a group scaled to zero, over the node's budget of 6 workers
```

A site which can't answer its first request is a worse outcome than a busy site not getting one more worker, so the node goes over its limit for the moment. Retained releases holding workers are stopped, oldest first, to bring it back under, and until then other releases' scale-out is refused. The memory limit still applies to both kinds of wake.

Deploys fit in with this too. When a new release replaces an old one, the old one is kept for half an hour so that a rollback can go back to it. For a group whose `min_workers` is zero it is kept without workers, so it holds none of the node's budget, and `muructl release list` says what a rollback to it would cost:

```
RELEASE                  STATE      SERVING  WORKERS          SOURCE
docs@r2                  ready      yes      1 (1x4)          ...
docs@r1                  retained            0 (1x4)          ...
                         host kept until 08:16 UTC; a rollback to it forks a worker
```

An explicit `--retain-workers` on the deploy keeps that many workers in every group instead.

There is one more case where scaling to zero doesn't fit. Muru matches gRPC calls by the services a worker has registered, so a release with a gRPC mount needs at least one worker running for its calls to be routed at all.

## What's next

The first stage is what makes this worthwhile. Because the host has already imported the application, getting from no workers back to one costs a fork, so a release can drop to zero workers whenever it is idle without its next visitor really paying for it. Stopping the host as well is there for when memory matters more than the first request.

The posts in this series so far have all been about Muru doing something itself. The next one, working with coding agents, is about something else doing things through Muru. Coding agents are increasingly the ones running, deploying and debugging applications, and Muru gives them a way in through MCP, so an agent can deploy each change as a release, read the events, logs and worker stacks when something fails, and roll back, using everything the earlier posts covered.
