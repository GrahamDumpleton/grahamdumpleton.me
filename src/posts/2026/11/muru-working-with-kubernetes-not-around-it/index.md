---
title: "Muru: working with Kubernetes, not around it"
description: "Running muructl serve on Kubernetes: a shutdown delay instead of a preStop hook, autoscaling on busy worker slots rather than CPU, in-place resize, and migrations as a Job."
date: 2026-11-15
tags: ["python", "muru", "kubernetes"]
draft: true
---

The [last post](/posts/2026/11/muru-a-better-tenant-in-a-container/) was about `muructl serve` as the main process of a container: sizing itself from the container's limits, answering probes on a port of its own, stopping in order on SIGTERM, and running with a read-only root under any user ID. None of that cares what runs the container. Most of these containers end up on Kubernetes though, and Kubernetes has its own way of doing several things a Python web server would otherwise need help with. Rolling out new versions, spreading traffic, scaling, running one-off tasks, all of that is done by the platform already.

So the aim with Muru on Kubernetes is to fit in with what Kubernetes provides rather than duplicate it, and to fill the gaps where what Kubernetes provides doesn't quite reach the application. For this post I ran everything on a local kind cluster, with a single node running Kubernetes 1.36, using muructl 0.1.0a19.

## The Deployment

The image is built the same way as in the last post, with a small WSGI application which has a page that waits as if on a database. I loaded it straight into the kind node rather than pushing it to a registry, which is why it has a version tag and `imagePullPolicy: IfNotPresent`. The Deployment follows the one in the Muru documentation:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop
spec:
  replicas: 2
  selector:
    matchLabels: {app: shop}
  template:
    metadata:
      labels: {app: shop}
    spec:
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: shop
          image: muru-blog-k8s:1
          imagePullPolicy: IfNotPresent
          env:
            - {name: MURU_SERVE_SHUTDOWN_DELAY, value: "5s"}
            - {name: MURU_SERVE_SHUTDOWN_BUDGET, value: "25s"}
            - {name: MURU_SERVE_LOG_FORMAT, value: "json"}
            - {name: SHOP_DATABASE, value: "postgresql://db.shop/shop"}
            - name: POD_NAME
              valueFrom: {fieldRef: {fieldPath: metadata.name}}
            - name: POD_NAMESPACE
              valueFrom: {fieldRef: {fieldPath: metadata.namespace}}
            - name: NODE_NAME
              valueFrom: {fieldRef: {fieldPath: spec.nodeName}}
          ports:
            - {name: http, containerPort: 8080}
            - {name: admin, containerPort: 9090}
          startupProbe:
            httpGet: {path: /startupz, port: admin}
            periodSeconds: 2
            failureThreshold: 60
          livenessProbe:
            httpGet: {path: /livez, port: admin}
          readinessProbe:
            httpGet: {path: /readyz, port: admin}
            periodSeconds: 2
          resources:
            requests: {cpu: 500m, memory: 512Mi}
            limits: {cpu: "2", memory: 1Gi}
          resizePolicy:
            - {resourceName: cpu, restartPolicy: RestartContainer}
            - {resourceName: memory, restartPolicy: RestartContainer}
          securityContext:
            readOnlyRootFilesystem: true
            allowPrivilegeEscalation: false
            capabilities: {drop: ["ALL"]}
          volumeMounts:
            - {name: run, mountPath: /run/muru}
            - {name: tmp, mountPath: /tmp}
      volumes:
        - name: run
          emptyDir: {sizeLimit: 2Gi}
        - name: tmp
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: shop
spec:
  selector: {app: shop}
  ports:
    - {name: http, port: 80, targetPort: http}
```

Much of this is what the last post covered, now expressed as Kubernetes configuration. All the settings come from environment variables. The probes go to the admin port, which the Service doesn't expose. The pod, namespace and node names come in through the Downward API so they end up in every JSON log record. I labelled the namespace to enforce the `restricted` Pod Security Standard and the pods were admitted without any warnings, as Muru only needs `/run/muru` and `/tmp` to be writable.

With a CPU limit of 2 and a memory limit of 1Gi, each pod sized itself as before:

```
2 processes from cpu.max 200000 100000
memory budget 896MB (memory.max 1.0GB less 128MB)
worker hard limit 431MB: the memory budget of 896MB less 34MB the host holds, over 2 workers
serving app:application on http://0.0.0.0:8080 with 2 workers of 4 threads
```

The parts which are particular to Kubernetes are the shutdown delay, the resize policy and the absence of any `preStop` hook, and those are what the rest of this post is about, along with autoscaling and migrations.

## Stopping without a preStop hook

When a pod is deleted, as happens to each old pod during a rolling update, two things start at the same time. The kubelet on the node begins shutting the pod down, which means sending SIGTERM to process 1 in each container. Separately, the control plane marks the pod's endpoint in the Service's EndpointSlices as terminating. Every kube-proxy, and any ingress controller, then has to notice that and stop sending new connections to the pod. Nothing makes the second wait for the first, so for a short while after SIGTERM a pod can still be handed new connections.

A server which closes its listening socket as soon as it gets SIGTERM, which is what gunicorn and uvicorn both do, will refuse those connections. The usual fix is a `preStop` hook which sleeps for a few seconds. The kubelet runs the hook before sending SIGTERM, so the server goes on serving during the sleep while the endpoint changes spread through the cluster. For a long time that meant an `exec` hook running `sleep`, which needs a `sleep` binary in the image. There is now also a `sleep` action, stable since Kubernetes 1.34, which the kubelet runs itself. Either way, it is something you have to know to add, and during the sleep the server has no idea it is about to be stopped. Neither gunicorn nor uvicorn has an option for this. Gunicorn's `--graceful-timeout` and uvicorn's `--timeout-graceful-shutdown` only govern what happens after the signal, by which time the listener is already closed.

Muru does this itself, with `--shutdown-delay`, set here through `MURU_SERVE_SHUTDOWN_DELAY`. On SIGTERM, `/readyz` starts failing at once. For the length of the delay the listener stays open and new connections are still served, but each response carries `Connection: close`, and idle connections are closed, so clients reconnect and land on another pod. After the delay, the listener closes, the requests in flight finish and the container exits, all within the budget, which is set below `terminationGracePeriodSeconds`.

To see what difference it makes, I ran a small Python client in a pod in the same namespace. It used eight threads, each on its own keep-alive connection to the Service, asking for a page which takes 50 milliseconds, for 40 seconds. Five seconds in I ran `kubectl rollout restart deploy/shop`. With the five second delay:

```
responses: {200: 6106}
errors: {} first at (s): {}
responses with Connection: close, by pod: {'shop-7f8f5b489f-bbnt5': 13, 'shop-7f8f5b489f-hl9zb': 5}
```

Every request succeeded, and the 18 responses which carried `Connection: close` were the client's connections being moved off the two old pods as each was stopped. Watching the EndpointSlice at the same time showed the first old pod being marked terminating:

```
shop-64df649bb5-x4hwq ready=true serving=true terminating=false
shop-7f8f5b489f-bbnt5 ready=false serving=true terminating=true
shop-7f8f5b489f-hl9zb ready=true serving=true terminating=false
```

That happened at 09:03:43.350. The last request that pod's access log recorded was at 09:03:43.455, and its host process didn't log receiving SIGTERM, which is when the workers start stopping, until 09:03:48.353, five seconds later. On a single node cluster, the endpoint changes reached kube-proxy within a fraction of a second.

So is the delay needed at all on a cluster this small? I set it to zero and ran the same test:

```
responses: {200: 6100}
errors: {'ConnectionRefusedError': 4} first at (s): {'ConnectionRefusedError': 11.4}
responses with Connection: close, by pod: {'shop-55885b469d-rxk2k': 2, 'shop-55885b469d-hftl9': 7}
```

Four requests failed because their connections were refused. I repeated both tests: four refused again with no delay, none again with the delay. Even when the endpoints catch up in a fraction of a second, there is a window where kube-proxy still routes new connections to a pod whose listener has closed. On a larger cluster, with an ingress controller in front, that window only gets longer, which is why the Muru documentation starts with five seconds.

Under Docker or Compose the delay defaults to zero, since a stopped container stops getting connections straight away. Under Kubernetes it is a single environment variable in the Deployment, and the pod spec has no `preStop` hook.

## Resizing a pod in place

As of Kubernetes 1.35 it is a stable feature that a running container's CPU and memory can be changed in place, through the pod's `resize` subresource, which a VerticalPodAutoscaler can also use. By default no restart is needed, as the kubelet just changes the container's cgroup limits. That is fine for a process which keeps checking its limits, but `muructl serve` reads them once when it starts, and both the worker count and each worker's hard memory limit come from them.

To show what goes wrong, I started a pod with the same spec but no `resizePolicy`, then raised its limits to four CPUs and 2Gi of memory:

```
kubectl patch pod resize-demo --subresource resize \
  --patch '{"spec":{"containers":[{"name":"shop","resources":{"limits":{"cpu":"4","memory":"2Gi"}}}]}}'
```

The container wasn't restarted, and the cgroup now showed the new limits:

```
400000 100000
2147483648
```

but `muructl debug status` showed Muru still running the two workers it had started with:

```
WORKER  PID      GROUP      UP       REQUESTS   THREADS  THREAD-OLDEST  RSS     USS     ROUTED  STATE
0       16       default    20s      0          0/4      -              29MB    3.5MB   yes     ready
1       17       default    20s      0          0/4      -              29MB    3.5MB   yes     ready
```

Most of the extra CPU would go unused, and each worker would still be replaced at 431MB, the share of the old limit. A memory reduction is worse, as the hard limits would then exceed what the container actually has, and the kernel could kill a worker before Muru gets to replace it.

That is why the Deployment sets `restartPolicy: RestartContainer` in its `resizePolicy`. The same CPU change to one of the Deployment's pods restarted its container, which sized itself from the new limits:

```
4 processes from cpu.max 400000 100000
```

The pod stays on the same node with the same address. Only the container restarts, and that turned out to matter.

I repeated the resize under load, this time changing the memory limit to 2Gi, with the client opening a new connection for each request. The new container came up with the larger budget:

```
memory budget 1.8GB (memory.max 2.0GB less 205MB)
worker hard limit 904MB: the memory budget of 1.8GB less 34MB the host holds, over 2 workers
```

but the client had errors:

```
responses: {200: 4448}
errors: {'ConnectionRefusedError': 10} first at (s): {'ConnectionRefusedError': 10.0}
responses with Connection: close, by pod: {'shop-5dfdbd5847-nz5bh': 180}
```

The resize went in at 09:28:23.665. Muru started its shutdown delay, the kubelet's readiness probe got a 503 from 09:28:25, and Muru sent `Connection: close` on 180 responses. But the EndpointSlice still listed the pod as ready until 09:28:29.062, by which time the old container had exited. With a rolling update the pod is deleted, so its endpoint is marked terminating at once. A container restarting in a pod which isn't going anywhere doesn't get that. The only thing taking the pod out of the Service is the readiness probe, and by default a readiness probe has to fail three times in a row. Every two seconds, three failures take up to six seconds, which is longer than the five second delay.

The fix is to have the pod taken out of the Service on the first failure:

```yaml
readinessProbe:
  httpGet: {path: /readyz, port: admin}
  periodSeconds: 2
  failureThreshold: 1
```

Under the same load, the endpoint went to not ready 1.5 seconds after the resize, and nothing failed:

```
responses: {200: 4448}
errors: {} first at (s): {}
responses with Connection: close, by pod: {'shop-567fc9d9c7-46lpz': 59}
```

A threshold of one would be a risky setting for a server which answers readiness from the same threads that serve requests, since one slow probe under load would take the pod out of the Service. With Muru, `/readyz` is answered by Muru itself and not by a worker, and as the last post showed it answers in a couple of milliseconds with every worker busy, so a failure means the pod really is stopping or has no ready workers. The Muru documentation's Deployment example uses the default threshold, so this is something I will be suggesting gets changed.

## Autoscaling on busy slots, not CPU

A HorizontalPodAutoscaler usually scales on CPU. For a Python web application which spends most of its time waiting on a database, that is close to useless. Every thread can be waiting, with requests queuing, while the CPU sits almost idle.

Muru publishes the measure that actually matters, `muru_capacity_utilisation`, the share of worker slots in use averaged over 30 seconds, on the admin port's `/metrics`. To get that to an autoscaler takes Prometheus to scrape it and the Prometheus adapter to present it as a pods metric through the custom metrics API. The kind cluster had neither, nor metrics-server for `kubectl top`, so I installed all three from their Helm charts. The pods got the usual scrape annotations:

```yaml
template:
  metadata:
    annotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "9090"
```

and the adapter got a rule for the one metric:

```yaml
rules:
  default: false
  custom:
    - seriesQuery: 'muru_capacity_utilisation{namespace!="",pod!=""}'
      resources:
        overrides:
          namespace: {resource: namespace}
          pod: {resource: pod}
      metricsQuery: 'avg(<<.Series>>{<<.LabelMatchers>>}) by (<<.GroupBy>>)'
```

The autoscaler aims to keep the average across pods at 70 percent:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: shop}
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric: {name: muru_capacity_utilisation}
        target: {type: AverageValue, averageValue: 700m}
```

For load, the client ran 24 threads for four minutes, each asking over and over for a page which waits half a second as if on a database. Each request was on a new connection, so the Service spread them across however many pods there were, much as an ingress controller balances each request. Two pods have 16 slots between them, two workers of four threads each, so 24 requests at a time can't all be served at once. Checking every ten seconds:

```
NAME   REFERENCE         TARGETS     MINPODS   MAXPODS   REPLICAS   AGE
shop   Deployment/shop   0/700m      2         10        2          40s
shop   Deployment/shop   391m/700m   2         10        2          50s
shop   Deployment/shop   853m/700m   2         10        2          61s
shop   Deployment/shop   839m/700m   2         10        3          81s
shop   Deployment/shop   754m/700m   2         10        4          91s
shop   Deployment/shop   732m/700m   2         10        4          2m1s
shop   Deployment/shop   726m/700m   2         10        4          3m2s
```

The autoscaler's events:

```
New size: 3; reason: pods metric muru_capacity_utilisation above target
New size: 4; reason: pods metric muru_capacity_utilisation above target
```

Within a minute of the load starting, the Deployment had gone from two pods to four. It then stayed at four, because 24 requests over 32 slots is 0.75, and the autoscaler ignores anything within its default tolerance of 10 percent of the target. While all that was happening, `kubectl top` showed the pods using next to no CPU:

```
shop-5dfdbd5847-d5ds9   10m   39Mi
shop-5dfdbd5847-nz5bh   10m   39Mi
shop-5dfdbd5847-pjmzj   11m   40Mi
shop-5dfdbd5847-pmfdt   10m   39Mi
```

That is about 2 percent of the 500m each pod requests. An autoscaler targeting 70 percent CPU would have left the Deployment at two pods, with a third of the requests waiting for a slot. When the load stopped, the metric dropped to zero, and the autoscaler took the Deployment back to two pods about five minutes later, its default stabilisation window for scaling in.

The other figure worth scaling on is how long requests wait for a slot, which is the `queue` phase of Muru's request duration histogram. Asking Prometheus for the 95th percentile ninety seconds into the run, with its two minute window covering the time at two pods:

```
histogram_quantile(0.95, sum by (le) (rate(muru_request_duration_seconds_bucket{namespace="muru-blog",phase="queue"}[2m])))
```

gave 0.457 seconds. A query like this is what KEDA's Prometheus trigger takes, with a threshold of, say, 100 milliseconds, if you would rather scale on how long users wait than on how busy the workers are. I didn't install KEDA for this post, but the query is the part which is Muru's.

Neither gunicorn nor uvicorn exposes anything like this. You can get at request latency through a Prometheus client in the application, but how many slots are busy and how long a request waited for one are things only the server knows.

## Migrations as a Job

In the [releases post](/posts/2026/11/muru-releases-not-restarts/), migrations ran from the new release, with `muructl command run shop@r4 migrate`, while the old release kept serving. On Kubernetes the new release is a new image, and the natural place to run something once from it before the Deployment changes is a Job. The project declares the command as before:

```toml
[tool.muru.commands.migrate]
description = "Apply database migrations"
run = ["python", "migrate.py"]
timeout = "10m"
```

and the Job runs it from the new image:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: shop-migrate-2-0
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      securityContext:
        runAsNonRoot: true
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: migrate
          image: muru-blog-k8s:2
          imagePullPolicy: IfNotPresent
          command: ["muructl", "command", "run", "migrate"]
          env:
            - {name: SHOP_DATABASE, value: "postgresql://db.shop/shop"}
          securityContext:
            allowPrivilegeEscalation: false
            capabilities: {drop: ["ALL"]}
```

With no `muructl serve` running in the Job's pod, `muructl command run` runs the command itself, using the image's interpreter, the project's environment and the command's timeout. The Deployment is then only updated once the Job has completed:

```
kubectl apply -f migrate-job-2.yaml
kubectl wait --for=condition=Complete job/shop-migrate-2-0 --timeout=120s
kubectl set image deploy/shop shop=muru-blog-k8s:2
```

```
job.batch/shop-migrate-2-0 created
job.batch/shop-migrate-2-0 condition met
deployment.apps/shop image updated
```

The migration's output is in the Job's logs:

```
connecting to postgresql://db.shop/shop
applied 0007_order_notes
applied 0008_order_notes_index
```

A failed migration fails the Job, since `muructl` exits with the command's status. Running the migration in a Job of its own without the database setting:

```
SHOP_DATABASE is not set
muru: the command exited with status 1 after 8ms
```

```
NAME             STATUS   COMPLETIONS   DURATION   AGE
shop-migrate-2   Failed   0/1           3s         3s
```

A `kubectl wait` for that Job would never see it complete, so a deploy script running the three commands above would stop there rather than update the Deployment. With `backoffLimit: 0` the Job doesn't try again, which for a migration that has failed halfway is usually what you want.

You could of course write `command: ["python", "migrate.py"]` in the Job and get much the same result with gunicorn in the image. What the declared command buys is that the Job, a `kubectl exec` into a running pod and the daemon from the releases post all run the migration the same way, from the one definition in the project, with its timeout.

## Looking inside a pod

Everything the last post did with `docker exec` works through `kubectl exec`, since `muructl` in the container finds `muructl serve` through its run directory. With a request stuck in a page which sleeps for eight seconds:

```
kubectl exec deploy/shop -- muructl requests
```

```
RELEASE              GROUP        QUEUED  QUEUED-OLDEST  THREADS  THREAD-OLDEST
app@r1               default      0       -              1/8      1.9s
```

```
kubectl exec deploy/shop -- muructl debug stacks
```

```
muru-app-2 in worker 1:
  serving GET /slow?seconds=8 for 1.9 s (request 01M6TNH4EM7EES4KX4129GEBM8)
  File "/opt/muru/muru/_pool.py", line 30, in serve_jobs
    serve()
  File "/app/app.py", line 18, in application
    time.sleep(seconds)
```

Who is allowed to do this is then up to RBAC, like any other `kubectl exec`.

## What's next

Very little in this post needed Muru to do anything Kubernetes-specific. The shutdown delay is one setting, the resize policy is part of the pod spec, the autoscaler reads a metric Muru already publishes, and the migration is a Job running a command the project already declares. The one thing I didn't expect was the resize case, where restarting a container in place doesn't take the pod out of the Service the way deleting it does, so readiness has to fail fast for the shutdown delay to do its job.

The autoscaling here works from outside, with Kubernetes adding whole pods once the workers are busy. The [next post](/posts/2026/11/muru-scaling-from-what-the-workers-report/) goes back to the daemon, where Muru decides itself how many workers a release needs, and where, because it knows why requests are waiting, it can tell whether more workers will help or whether something in the release needs changing.
