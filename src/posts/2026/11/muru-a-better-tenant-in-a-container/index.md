---
title: "Muru: a better tenant in a container"
description: "What muructl serve does as a container's main process: workers set to fit the container, a guard on its memory, probes on their own port, an orderly SIGTERM, and a read-only root."
date: 2026-11-14
tags: ["python", "muru", "docker"]
---

The last two posts, on [releases](/posts/2026/11/muru-releases-not-restarts/) and [canaries](/posts/2026/11/muru-canaries-without-a-service-mesh/), were all about the Muru daemon running more than one release of an application side by side and moving traffic between them. When the application runs in a container, Muru deliberately does none of that. A container image is already a fixed release of an application, and starting new containers, moving traffic to them and putting the old ones back is the job of whatever runs the containers. Doing the same thing again inside the container would only get in its way.

So in a container Muru runs as `muructl serve`, which serves the single application held in the image. The edge, the controller, the host and its workers are all still there, as in development mode, but releases and traffic policies aren't. Instead, it concentrates on being a good main process for a container, which mostly means handling things people otherwise end up doing by hand when using gunicorn or uvicorn.

## An image

The image for this post holds a small WSGI application with a few pages which misbehave in different ways, which I will get to later. The `Dockerfile` follows the pattern from the Muru documentation:

```dockerfile
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN UV_TOOL_BIN_DIR=/usr/local/bin uv tool install muructl
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN muructl build --deployment --deps-only --no-runtime --target /app/.venv
COPY . .
RUN muructl build --deployment --target /app/.venv --runtime-dir /opt/muru

FROM python:3.13-slim
COPY --from=build /usr/local/bin/muructl /usr/local/bin/muructl
COPY --from=build /app /app
COPY --from=build /opt/muru /opt/muru
WORKDIR /app
RUN useradd --uid 10001 app && install -d -o 10001 -g 0 -m 0770 /run/muru
USER 10001
EXPOSE 8080 9090
CMD ["muructl", "serve"]
```

`muructl` is a single executable, so the final image copies just the binary. The two `muructl build` steps install the application's environment from `uv.lock`. The first installs only the dependencies, so that its layer can be reused until they change. Each says what it is running:

```
muru: building /app/.venv with uv sync --frozen --no-dev --no-build --compile-bytecode --no-install-project
...
muru: building /app/.venv with uv sync --frozen --no-dev --no-build --compile-bytecode
muru: built /app/.venv on Python 3.13.18 (cp313)
muru: fetched the runtime library muru-1.0.0-cp313-cp313-manylinux_2_28_aarch64.whl from PyPI into /opt/muru
```

The last line is the part which is specific to Muru. The runtime library which runs inside the workers has to match both the version of `muructl` and the interpreter, so it is fetched when the image is built. It is kept outside the application's environment, so the application doesn't need to list Muru as a dependency.

The important thing is that this is the only point at which anything is fetched or installed. When the container starts, `muructl serve` never builds an environment, downloads a Python or fetches the runtime library, and anything it runs gets `UV_OFFLINE=1` and `UV_PYTHON_DOWNLOADS=never` in its environment. If something is missing, it stops with a message naming the build step which would have provided it. For example, pointing it at the wrong runtime directory gives:

```
muru: error: no runtime library for /app/.venv/bin/python (cp313): build the image with muructl build --runtime-dir /nowhere, or add muru 1.0.0 to the environment
```

That matters more than it might seem. It isn't unusual to find images where an entrypoint script pip installs something, or where a missing package is quietly downloaded at start. That works until the network is unavailable or the package index changes, at which point two containers started from the same image are no longer the same.

## Telling it how many workers

Starting the image with limits of two CPUs and a gigabyte of memory, with no swap, on a Docker host with ten CPUs, I gave it the number of worker processes and the threads in each:

```
docker run --name shop --cpus 2 --memory 1g --memory-swap 1g \
  -e MURU_SERVE_PROCESSES=2 -e MURU_SERVE_THREADS=4 -p 8080:8080 -p 9090:9090 shop
```

The output says what it found and what it is running:

```
muru: container limits: 2 CPUs from cpu.max 200000 100000, memory.max 1.0GB with 128MB of headroom
...
muru.host[12]: preloaded app:application in 1 ms
muru.host[12]: app:application is served as WSGI
muru.host[12]: worker 0 started as pid 15
muru.host[12]: worker 1 started as pid 16
...
muru: serving app:application on http://0.0.0.0:8080 with 2 workers of 4 threads
...
muru: the host holds 34MB once the application is imported
```

These settings should always be supplied, chosen to suit the resources given to the container. If they are left out, Muru runs a single worker. Two processes for two CPUs suits an application whose requests mostly use the CPU, while one whose requests spend most of their time waiting on a database can use more threads in each. The memory has to fit as well. Two workers, along with the host which imported the application, leave plenty of room in a gigabyte, but an application whose workers each need 750MB would have to run a single process in a container this size, or be given a bigger container. The other examples in this post start the container with the same settings, which I leave out to keep the commands short.

Muru doesn't try to choose these numbers itself, because they can't be reliably worked out from inside the container. Asking Python how many CPUs it has, in the same container, gives:

```
docker run --rm --cpus 2 shop python3 -c "import os; print(os.cpu_count(), os.process_cpu_count())"
```

```
10 10
```

A CPU limit set with `--cpus`, or `resources.limits.cpu` in Kubernetes, is a CFS quota in the cgroup's `cpu.max` file, which neither of those functions reads. Gunicorn's default is a single worker unless `WEB_CONCURRENCY` says otherwise, and uvicorn's is the same. Gunicorn's documentation suggests `(2 x CPU cores) + 1`, and the [image the Gunicorn project publishes](https://gunicorn.org/guides/docker/) uses that formula by default, working out the count with `nproc`, which also says 10 here, so it would start 21 workers in a container allowed two CPUs. On a large Kubernetes node, with a pod limited to a couple of CPUs, it is far worse. Even a count which got the CPUs right would say nothing about how much memory each worker needs, or whether the requests use much CPU at all.

Muru does read the limits from the cgroup, as the first line of its output showed, but only to check the settings against them. Asking for four workers in the same container still starts four, but with a warning:

```
muru: warning: 4 workers is more than the 2 CPUs cpu.max allows; see https://docs.muruhq.dev/en/latest/howto/containers.html#container-limits
```

It also warns if the workers wouldn't fit in memory once each holds its own copy of what the host imported. A forked Python process tends to end up with such a copy over time, as it gradually stops sharing memory with the process it was forked from.

## Running short of memory

A Python process tends to hang on to memory it has used, whether through a cache, a leak or one unusually large request. In a container, the usual outcome of this is that the container runs out of memory and the kernel kills a process outright.

When the container has a memory limit, Muru gets in first. Every few seconds it checks how much memory is left under the limit. If that drops below a margin it keeps in reserve, which it calls the headroom, it takes the largest worker out of service and replaces it with a fresh one. The old worker finishes the requests it already has before it goes, so nobody sees an error, and its memory is given back. Nothing needs to be set for this beyond the container's memory limit.

To see it in action, I used a page of the application which holds on to another 10MB each time it is requested, and asked for it once a second:

```
muru.host[12]: worker 0 (pid 15) the container was short of memory, 102MB left under memory.max 1.0GB, less than the headroom of 128MB; it was the largest worker, uss 424MB; replacing it
muru.host[12]: worker 0 (pid 15) stops before its replacement starts: 101MB is left under the memory limit, less than its size
muru.host[12]: worker 0 started as pid 38
muru.host[12]: worker.recycled: worker 0 (pid 15) replaced by pid 38: the container was short of memory, 102MB left under memory.max 1.0GB, less than the headroom of 128MB; it was the largest worker, uss 424MB; most objects: cell 31, tuple 20, builtin_function_or_method 16, function 11, list 11
muru.host[12]: worker 0 (pid 38) is ready
...
muru.host[12]: worker 1 (pid 16) the container was short of memory, 100MB left under memory.max 1.0GB, less than the headroom of 128MB; it was the largest worker, uss 645MB; replacing it
muru.host[12]: worker 1 (pid 16) stops before its replacement starts: 100MB is left under the memory limit, less than its size
muru.host[12]: worker 1 started as pid 49
muru.host[12]: worker.recycled: worker 1 (pid 16) replaced by pid 49: the container was short of memory, 100MB left under memory.max 1.0GB, less than the headroom of 128MB; it was the largest worker, uss 645MB; most objects: cell 31, tuple 20, builtin_function_or_method 16, function 11, list 11
muru.host[12]: worker 1 (pid 49) is ready
```

Both workers had been growing at the same rate, so when the container first ran short, worker 0 was only just the larger of the two, at 424MB. Replacing it gave that memory back, which left room for worker 1 to keep growing. By the time the container ran short again, worker 1 was at 645MB, and it was replaced in turn.

Normally Muru starts the new worker before the old one leaves, so there is never a gap. Here less memory was left in the container than the old worker was using, so rather than risk two large workers at once, the old worker stopped first, finishing the requests it already had, and its replacement started once it had gone. The other worker carried on serving in the meantime, and all 150 requests succeeded.

Without this, the first anyone knows of a worker growing is when the kernel's out-of-memory killer picks a process in the container to kill, and that can just as easily be one in the middle of a perfectly good request. Neither gunicorn nor uvicorn keeps any watch on memory. The best either offers is restarting a worker after a set number of requests, however much memory it is using.

Muru calls this its memory guard. Running `muructl status` inside the container shows the limits, how much memory is used and left, and what the guard last did:

```
docker exec shop muructl status
```

```
...
cpu      2 CPUs from cpu.max
memory   memory.max 1.0GB, 402MB used, 622MB left, headroom 128MB
         workers 329MB, host 34MB
guard    watching; it last replaced shop@r1 worker 1 (pid 16) at 07:31:18 UTC
```

The guard looks at the container as a whole. If a single worker should never grow beyond a certain size, however much room is left, it can also be given a hard memory limit, such as `MURU_SERVE_MEMORY=hard_limit=300MB`. A worker which goes over that limit is replaced in the same way. The value is chosen to suit the application, and should be low enough that all the workers together still fit in the container.

Memory is only checked every five seconds, so if it grows by more than the headroom between checks, the out-of-memory killer can still strike first. A request which allocated a gigabyte all at once showed what happens then:

```
502 Bad Gateway
reason: worker_crashed
request id: 01M6TF11TNSGS7R9AW4G704V4X

The worker sent no response head.
```

```
muru.host[12]: worker.oom_killed: worker 0 (pid 15) was killed by the kernel for memory, restarting
muru.host[12]: worker 0 started as pid 47
muru.host[12]: worker 0 (pid 47) is ready
```

Each worker raises its own `oom_score_adj` as it starts, which makes the workers the processes the kernel picks first. So it was the worker which was killed, rather than the host or `muructl`, and the host started a new one. The kill is also reported for what it was, as a `worker.oom_killed` event and in the `muru_worker_exits_total` metric with the reason `oom_killed`, rather than leaving a worker which mysteriously went away.

## Probes on their own port

The output when it started also included this line:

```
muru: admin port on http://0.0.0.0:9090/
```

Port 9090 is separate from the application's port and answers the questions a container platform asks. `/livez` says whether the process is alive, `/readyz` whether enough workers are ready to take requests, and `/startupz` whether the application has finished loading. `/metrics` has the metrics in Prometheus format.

Gunicorn and uvicorn have nothing like this. The usual answer is to add a `/health` view to the application, which means the health check is served by the same workers as everything else. When the application is slow, perhaps because its database is, every worker is busy. The health check then queues behind real requests and times out, and the platform restarts containers which were doing nothing wrong, just when they are needed most.

To check that Muru doesn't suffer from this, I sent twelve requests to a page which takes six seconds to answer, more than the two workers with four threads each could handle at once, and then queried the admin port:

```
livez 200 0.001336s
readyz 200 0.001337s
```

The metrics confirmed every slot was busy, with requests queuing:

```
muru_queue_depth{app="shop",release="r1",group="default"} 4
muru_slots_busy{app="shop",release="r1",group="default",side="threads"} 8
muru_slots_total{app="shop",release="r1",group="default",side="threads"} 8
```

The probes are answered by `muructl` itself, from what it knows about the host and its workers, without a request having to go through a worker. A container whose workers are all busy is still alive, so it isn't killed for being busy. Having a port of their own also keeps the probes and metrics out of reach of the application's Ingress or load balancer.

An image without `curl`, such as one based on the slim Python images, can use `muructl` itself for a health check:

```dockerfile
HEALTHCHECK --interval=5s CMD ["muructl", "probe", "ready"]
```

## Process 1

Looking at the processes inside the container (by reading `/proc`, since the slim image has no `ps`), each of Muru's processes has set a title saying what it is:

```
    1     0 S  muructl serve
    7     1 S  muru serve shop
   11     7 S  muru relay shop@r1
   12     7 S  muru host shop@r1
   15    12 S  muru worker shop@r1 default/0
   16    12 S  muru worker shop@r1 default/1
```

Process 1 is `muructl` acting as an init, in the way `tini` or `docker run --init` would. It forwards signals to the real `muructl serve`, which is its child, and collects any process in the container which exits, so nothing is left as a zombie. Process 1 in a container has to do this, because orphaned processes are handed to it, and if it never collects them, zombies fill up the process table. Below `muructl serve` are the host and its two workers, and a log relay which passes on what they write.

The application has a page which starts a report by running a shell command, which leaves a process running in the background. That happens in real applications more often than anyone would like. Just after I requested the page three times, `muructl status --processes --all`, where `--all` adds the processes Muru didn't start itself, showed them:

```
docker exec shop muructl status --processes --all
```

```
edge  3.0 req/s  0 err/s  p50 2.1 ms  p95 4.6 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 53B/s

PID   ROLE           WHAT                         UP    CPU      RSS   REQ/S   BUSY   QUEUE      P95   GIL/LAG
7     serve          controller and edge, :8080   5s   2.3%   19.5MB
12    └─ host        app:application (r1)         5s   0.0%   34.7MB     3.0    0/8       0   4.6 ms
11       ├─ relay    output to muructl            5s   0.0%   11.4MB
15       ├─ worker   worker 0                     5s   0.0%   28.7MB     2.0    0/4           4.8 ms
16       ├─ worker   worker 1                     5s   0.0%   28.9MB     1.0    0/4           2.4 ms
54       ├─ other    sleep 1                      1s           1.5MB
56       ├─ other    sleep 1                      1s           1.5MB
58       └─ other    sleep 1                      1s           1.5MB
```

The orphaned `sleep` processes were taken over by the host, which collects any process its workers leave behind, and a couple of seconds later they were gone, with no zombies. Gunicorn does collect any child that exits, including ones it didn't start. Uvicorn doesn't, so when run as process 1 it leaves a zombie behind for each one. Neither project's documentation says anything about `tini` or `--init`. An image which uses its own init can turn off Muru's by setting `MURU_NO_INIT=1`.

## Stopping in order

When `docker stop` or Kubernetes wants a container gone, it sends SIGTERM, waits, and then sends SIGKILL. Docker waits ten seconds and Kubernetes thirty by default. For a server, what happens in between decides whether anyone sees an error.

I started four requests to the page which takes three seconds, and half a second later ran `docker stop`, while checking `/readyz` every 300 milliseconds:

```
readyz 200
readyz 503
readyz 503
readyz 503
readyz 503
```

The four requests all completed:

```
 200 3.004430s
 200 3.004411s
 200 3.004890s
 200 3.004973s
```

and `docker stop` returned after 2.76 seconds, with the container's exit status 0. On SIGTERM, readiness starts failing at once, so nothing new is sent to the container. The listener then closes, the requests in flight finish, and the workers stop. All of that has to happen within a budget, eight seconds unless `--shutdown-budget` changes it. That is less than the ten seconds `docker stop` allows, so anything still running at the end is stopped by Muru rather than killed by Docker.

Compare that with the defaults elsewhere. Gunicorn's `graceful_timeout` is 30 seconds, so under `docker stop` a slow request is cut off by SIGKILL at ten seconds and gunicorn never gets to finish shutting down. Uvicorn has no graceful shutdown timeout by default, so it waits as long as it takes, which under Docker means until the SIGKILL arrives. With either, the fix is to remember to set a timeout which fits within the platform's.

Kubernetes adds a wrinkle, as a pod can keep receiving new connections for a few seconds after SIGTERM, while the endpoints catch up. That is what `--shutdown-delay` is for, and I will come back to it in the next post.

## A read-only root and any user

A security conscious platform will run the container with a read-only root filesystem, and OpenShift will run it as an arbitrary user ID in group 0, with no entry for it in `/etc/passwd`. Everything `muructl serve` writes at run time goes under one directory, `/run/muru`. With a read-only root and nothing mounted there, it stops at once and says what it needs:

```
docker run --rm --read-only --user 123456:0 shop
```

```
muru: error: the run directory /run/muru cannot be written (Read-only file system (os error 30)); with a read-only root filesystem give it a writable volume, a tmpfs or an emptyDir mounted at /run/muru, or name another with --run-dir
```

Giving it what it asks for:

```
docker run --read-only --tmpfs /run/muru --tmpfs /tmp --user 123456:0 ... -p 8080:8080 -p 9090:9090 shop
```

it runs as normal under a user ID which doesn't exist in the image:

```
hello from pid 15
```

Gunicorn in the same situation fails at start, with `No usable temporary directory found`, as it writes a heartbeat file for each worker to the temporary directory. That can be fixed with a `tmpfs` on `/tmp`, or by pointing `--worker-tmp-dir` at `/dev/shm`, but you have to know to do it.

## Settings in layers

Every setting of `muructl serve` can be given as a command line flag. An image can also set defaults in the project's `pyproject.toml`, under `[tool.muru.serve]`, and a deployment can override any of them with an environment variable named after the flag. `--print-config` shows the settings in force and where each came from, and works inside a running container too:

```
docker run --name shop -e MURU_SERVE_PROCESSES=3 -e MURU_SERVE_LOG_FORMAT=json ... shop
docker exec shop muructl serve --print-config
```

```
processes = 3                     # MURU_SERVE_PROCESSES
...
log_format = "json"              # MURU_SERVE_LOG_FORMAT
```

`--config`, or `MURU_SERVE_CONFIG`, names a settings file to read instead of the one in the image, such as a file mounted from a ConfigMap.

## Logs a collector can use

With the JSON log format, every line is a JSON object. When the environment has `POD_NAME`, `POD_NAMESPACE` and `NODE_NAME`, which the Kubernetes Downward API can provide, each line also says where it came from. I set those by hand for this run. More useful is what happens to a traceback. The application has a page which raises an exception, and the error shows up as a single record, with the whole traceback in its `exception` field, alongside the request, release and worker it happened in:

```json
{"time":"2026-11-07T07:37:52.296Z","kind":"app","source":"muru.worker[0]","app":"shop","exception":"Traceback (most recent call last):\n  File \"/app/app.py\", line 25, in application\n    raise RuntimeError(\"something went wrong\")\nRuntimeError: something went wrong","group":"default","level":"ERROR","logger":"muru","message":"the application raised an exception","release":"r1","request_id":"01M6TF2DXFEHAEQZN1C1JEXGBE","worker":0,"pod":"shop-7d4b9c-x2k8p","namespace":"shop","node":"worker-2"}
```

Anyone who has had to piece a Python traceback back together from a log system which treated each line as a separate entry will appreciate that.

## Inside the container

Finally, the commands from [looking inside the workers](/posts/2026/11/muru-looking-inside-the-workers/) work inside the container through `docker exec`, talking to `muructl serve` over its admin socket. With a slow request under way:

```
docker exec shop muructl debug stacks
```

```
muru-app-0 in worker 0:
  serving GET /slow?seconds=4 for 1.2 s (request 01M6TF2SRXPXTHSAPPDG6MVNJQ)
  File "/opt/muru/muru/_pool.py", line 30, in serve_jobs
    serve()
  File "/app/app.py", line 15, in application
    time.sleep(seconds)
```

## What's next

None of this needs anything outside the image. There is no init to add, no health check view to write, no timeouts to line up with the platform's and no temporary directory to remember. What it does need to be told is how many workers of how many threads to run, chosen to fit the resources the container is given.

Most containers end up on Kubernetes though, and there are a few more things there where Muru can work with what the platform provides rather than around it, such as the shutdown delay in place of the usual `preStop` hook, autoscaling on how busy the workers really are rather than on CPU, and running migrations as a Job from the new image. That is the subject of the next post, working with Kubernetes, not around it.
