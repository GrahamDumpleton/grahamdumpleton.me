---
title: "Muru: a better tenant in a container"
description: "What muructl serve does as a container's main process: sizing from the container's limits, probes on their own port, an orderly SIGTERM, and a read-only root."
date: 2026-11-14
tags: ["python", "muru", "docker"]
draft: true
---

The last two posts, on [releases](/posts/2026/11/muru-releases-not-restarts/) and [canaries](/posts/2026/11/muru-canaries-without-a-service-mesh/), were all about the Muru daemon running more than one release of an application side by side and moving traffic between them. When the application runs in a container, Muru deliberately does none of that. A container image is already a fixed release of an application, and starting new containers, moving traffic to them and putting the old ones back is the job of whatever runs the containers. Doing it a second time inside the container would only fight with it.

So in a container Muru runs as `muructl serve`, which serves the one application the image holds, in the one process. The edge, the controller, the host and its workers are all still there, as in development mode, but releases and traffic policies aren't. What it concentrates on instead is being a good main process for a container, and most of what that involves is work people end up doing by hand around gunicorn or uvicorn.

## An image

The image for this post holds a small WSGI application with a few pages for misbehaving in different ways, which I will come to. The `Dockerfile` follows the pattern from the Muru documentation:

```dockerfile
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN UV_TOOL_BIN_DIR=/usr/local/bin uv tool install muructl==0.1.0a19
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

`muructl` is a single executable, so the final image copies just the binary. The two `muructl build` steps install the application's environment from `uv.lock`, the first doing the dependencies alone so that layer is reused until they change. Each says what it is running:

```
muru: building /app/.venv with uv sync --frozen --no-dev --no-build --compile-bytecode --no-install-project
...
muru: building /app/.venv with uv sync --frozen --no-dev --no-build --compile-bytecode
muru: built /app/.venv on Python 3.13.18 (cp313)
muru: fetched the runtime library muru-0.1.0a19-cp313-cp313-manylinux_2_28_aarch64.whl from PyPI into /opt/muru
```

The last line is the part which is specific to Muru. The runtime library which runs inside the workers has to match both the version of `muructl` and the interpreter, so it is fetched while building the image, and kept outside the application's environment so the application doesn't need to depend on Muru.

The important thing is that this is the only point at which anything is fetched or installed. When the container starts, `muructl serve` never builds an environment, downloads a Python or fetches the runtime library, and anything it runs gets `UV_OFFLINE=1` and `UV_PYTHON_DOWNLOADS=never` in its environment. If something is missing, it stops with a message naming the build step which would have provided it. Pointing it at the wrong runtime directory, for example:

```
muru: error: no runtime library for /app/.venv/bin/python (cp313): build the image with muructl build --runtime-dir /nowhere, or add muru 0.1.0a19 to the environment
```

That matters more than it might seem. It isn't unusual to find images where an entrypoint script pip installs something, or where a missing package is quietly downloaded at start. That works until the network is unavailable or the package index changes, at which point two containers started from the same image are no longer the same.

## Sizing from the container's limits

Starting the image with limits of two CPUs and a gigabyte of memory, on a Docker host with ten CPUs:

```
docker run --name shop --cpus 2 --memory 1g -p 8080:8080 -p 9090:9090 shop
```

the first lines of output say what it worked out and from what:

```
muru: 2 processes from cpu.max 200000 100000
muru: memory budget 896MB (memory.max 1.0GB less 128MB)
...
muru.host[11]: worker hard limit 431MB: the memory budget of 896MB less 34MB the host holds, over 2 workers
```

Two workers, because the container is allowed two CPUs. That sounds obvious, but it isn't what you get by asking Python. Run in the same container:

```
docker run --rm --cpus 2 shop python3 -c "import os; print(os.cpu_count(), os.process_cpu_count())"
```

```
10 10
```

A CPU limit set with `--cpus`, or `resources.limits.cpu` in Kubernetes, is a CFS quota in the cgroup's `cpu.max` file, which neither of those functions reads. Gunicorn's default is a single worker unless `WEB_CONCURRENCY` says otherwise, and uvicorn's is the same. Gunicorn's documentation suggests `(2 x CPU cores) + 1`, and its official image works that out with `nproc`, which also says 10 here, so following that advice would give 21 workers in a container allowed two CPUs. On a large Kubernetes node, with a pod limited to a couple of CPUs, it is far worse.

With no CPU limit at all, the same image starts as many workers as the container may run on:

```
muru: 10 processes from cpuset.cpus.effective, 10 CPUs
```

The memory limit is used in a similar way. Ten percent of it, at least 128MB, is set aside for `muructl` itself and the page cache, along with what the host holds once the application is imported, and the rest is divided between the workers as a hard limit for each. To see what that does I used a page of the application which keeps 25MB more each time it is requested, and asked for it once a second:

```
muru.host[11]: worker 0 (pid 12) uss 454MB is over the hard limit of 431MB; replacing it
muru.host[11]: worker 0 started as pid 35
muru.host[11]: worker 1 (pid 13) uss 454MB is over the hard limit of 431MB; replacing it
muru.host[11]: worker 1 started as pid 46
muru.host[11]: worker 0 (pid 35) is ready
muru.host[11]: worker 1 (pid 46) is ready
muru.host[11]: worker.recycled: worker 1 (pid 13) replaced by pid 46: uss 454MB is over the hard limit of 431MB; most objects: cell 30, tuple 20, builtin_function_or_method 16, function 11, list 11
muru.host[11]: worker.recycled: worker 0 (pid 12) replaced by pid 35: uss 454MB is over the hard limit of 431MB; most objects: cell 30, tuple 20, builtin_function_or_method 16, function 11, list 11
```

Each worker was replaced once it went over its share, through the same path as any other worker replacement, with a new worker forked first and the old one finishing what it had before going. Without this, the first anyone hears of a worker growing is the kernel's out-of-memory killer choosing a process in the container, which can just as easily be one in the middle of a perfectly good request. Neither gunicorn nor uvicorn looks at the memory limit at all. The best either offers is restarting a worker after a set number of requests, whatever it is using.

The check is made every five seconds, so a worker which jumps past its share between checks can still meet the out-of-memory killer. A request for a gigabyte all at once showed what happens then:

```
502 Bad Gateway
reason: worker_crashed
request id: 01M6TF11TNSGS7R9AW4G704V4X

The worker sent no response head.
```

```
muru.host[11]: worker.oom_killed: worker 0 (pid 12) was killed by the kernel for memory, restarting
muru.host[11]: worker 0 started as pid 35
muru.host[11]: worker 0 (pid 35) is ready
```

At least then the kill is reported as what it was, as a `worker.oom_killed` event and in a `muru_worker_exits_total` metric with the reason `oom_killed`, rather than a worker which mysteriously went away. I should say that in the earlier, slower test the container's own cgroup counters recorded two kills by the kernel despite the log showing only the replacements, so there is something there I still need to look into.

## Probes on their own port

The output above also included this line:

```
muru: admin port on http://0.0.0.0:9090/
```

Port 9090 is separate from the application's port and answers the questions a container platform asks. `/livez` says whether the process is alive, `/readyz` whether enough workers are ready to take requests, and `/startupz` whether the application has finished loading. `/metrics` has the metrics in Prometheus format.

Gunicorn and uvicorn have nothing like this. The usual answer is to add a `/health` view to the application, which means the health check is served by the same workers as everything else. When the application is slow, perhaps because its database is, every worker is busy, the health check queues behind real requests and times out, and the platform restarts containers which were doing nothing wrong, just when they are needed most.

To check Muru doesn't do that, I sent twelve requests to a page which takes six seconds to answer, more than the two workers with four threads each could handle at once, and then asked the admin port:

```
livez 200 0.002802s
readyz 200 0.001870s
```

The metrics confirmed every slot was busy, with requests queuing:

```
muru_queue_depth{app="app",release="r1",group="default"} 4
muru_slots_busy{app="app",release="r1",group="default",side="threads"} 8
muru_slots_total{app="app",release="r1",group="default",side="threads"} 8
```

The probes are answered by `muructl` itself, from what it knows about the host and its workers, without a request having to go through a worker. A container whose workers are all busy is alive, so it isn't killed for it. Being on a port of its own also means the probes and metrics are out of reach of the application's Ingress or load balancer.

An image which has no `curl` in it, as the slim Python images don't, can ask the same question with `muructl` itself:

```dockerfile
HEALTHCHECK --interval=5s CMD ["muructl", "probe", "ready"]
```

## Process 1

Looking at the processes inside the container (by reading `/proc`, since the slim image has no `ps`):

```
    1     0 S  muructl serve
    7     1 S  muructl serve
   11     7 S  /app/.venv/bin/python -m muru.host --app app:application --socket-dir /run/muru/release/r1
   12    11 S  /app/.venv/bin/python -m muru.host --app app:application --socket-dir /run/muru/release/r1
   13    11 S  /app/.venv/bin/python -m muru.host --app app:application --socket-dir /run/muru/release/r1
```

Process 1 is `muructl` acting as an init, in the way `tini` or `docker run --init` would. It forwards signals to the real `muructl serve`, which is its child, and collects any process in the container which exits, so nothing is left as a zombie. Process 1 in a container has to do that, as orphaned processes are handed to it, and a process which never collects them fills up the process table with zombies.

The application has a page which starts a report by running a shell command that leaves a process running in the background, the sort of thing which happens in real applications more than anyone would like. Just after requesting it three times:

```
   52    11 S  sleep 1
   54    11 S  sleep 1
   56    11 S  sleep 1
```

The orphaned `sleep` processes were taken over by the host, which collects any process its workers leave behind, and a couple of seconds later they were gone, with no zombies. Gunicorn does collect any child that exits, including ones it didn't start. Uvicorn doesn't, so run as process 1 it leaves a zombie behind for each of those. Neither project's documentation says anything about `tini` or `--init`. An image which brings its own init sets `MURU_NO_INIT=1`.

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
 200 3.002067s
 200 3.002763s
 200 3.002639s
 200 3.002324s
```

and `docker stop` returned after 2.68 seconds, with the container's exit status 0. On SIGTERM, readiness starts failing at once, so nothing new is sent to the container. The listener then closes, the requests in flight finish, and the workers stop. All of that has to fit inside a budget, eight seconds unless `--shutdown-budget` changes it, which is under the ten seconds `docker stop` allows, so anything left over is stopped by Muru rather than killed by Docker.

Compare that with the defaults elsewhere. Gunicorn's `graceful_timeout` is 30 seconds, so under `docker stop` a slow request is cut off by SIGKILL at ten seconds and gunicorn never gets to finish shutting down. Uvicorn's graceful shutdown timeout isn't set by default, which means it waits for as long as it takes, which under Docker means until the SIGKILL. With either, the fix is remembering to set a timeout which agrees with the platform's.

Under Kubernetes there is an extra wrinkle, in that a pod keeps receiving new connections for a few seconds after SIGTERM, while the endpoints catch up. That is what `--shutdown-delay` is for, and I will come back to it in the next post.

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
docker run --read-only --tmpfs /run/muru --tmpfs /tmp --user 123456:0 --cpus 2 -p 8080:8080 -p 9090:9090 shop
```

it serves as normal under a user ID which exists nowhere:

```
hello from pid 12
```

Gunicorn in the same situation fails at start, with `No usable temporary directory found`, as it writes a heartbeat file for each worker to the temporary directory. That is fixable with a `tmpfs` on `/tmp` or by pointing `--worker-tmp-dir` at `/dev/shm`, but you have to know to do it.

## Settings in layers

Every setting of `muructl serve` is a flag, but an image can set its defaults in the project's `pyproject.toml`, under `[tool.muru.serve]`, and a deployment can override any one with an environment variable named after the flag. `--print-config` shows the settings in force and where each came from, and works inside a running container too:

```
docker run --name shop -e MURU_SERVE_PROCESSES=3 -e MURU_SERVE_LOG_FORMAT=json ... shop
docker exec shop muructl serve --print-config
```

```
processes = 3                     # MURU_SERVE_PROCESSES
...
log_format = "json"              # MURU_SERVE_LOG_FORMAT
```

`--config`, or `MURU_SERVE_CONFIG`, names a settings file to read in place of the one in the image, for a file mounted from a ConfigMap.

## Logs a collector can use

With the JSON log format, every line is a JSON object, and when the environment has `POD_NAME`, `POD_NAMESPACE` and `NODE_NAME`, as the Kubernetes Downward API can provide, each line says where it came from. I set those by hand for this run. The more useful part is what happens to a traceback. The application has a page which raises an exception, and the error shows up as a single record:

```json
{"time":"2026-11-07T07:37:52.296Z","kind":"app","source":"muru.worker[1]","message":"Traceback (most recent call last):\n  File \"/app/app.py\", line 25, in application\n    raise RuntimeError(\"something went wrong\")\nRuntimeError: something went wrong","pod":"shop-7d4b9c-x2k8p","namespace":"shop","node":"worker-2"}
```

Anyone who has had to piece a Python traceback back together from a log system which treated each line as a separate entry will appreciate that.

## Inside the container

Finally, the commands from [looking inside the workers](/posts/2026/11/muru-looking-inside-the-workers/) work inside the container through `docker exec`, talking to `muructl serve` over its admin socket. With a slow request under way:

```
docker exec shop muructl debug stacks
```

```
muru-app-1 in worker 2:
  serving GET /slow?seconds=4 for 1.1 s (request 01M6TF2SRXPXTHSAPPDG6MVNJQ)
  File "/opt/muru/muru/_pool.py", line 30, in serve_jobs
    serve()
  File "/app/app.py", line 15, in application
    time.sleep(seconds)
```

## What's next

None of this needs anything outside the image. There is no init to add, no worker count to calculate, no health check view to write, no timeouts to line up with the platform's and no temporary directory to remember. Muru simply reads what the container gives it and behaves accordingly.

Most containers end up on Kubernetes though, and there are a few more things there where Muru can work with what the platform provides rather than around it, such as the shutdown delay in place of the usual `preStop` hook, autoscaling on how busy the workers really are rather than on CPU, and running migrations as a Job from the new image. That is the subject of the next post, [working with Kubernetes, not around it](/posts/2026/11/muru-working-with-kubernetes-not-around-it/).
