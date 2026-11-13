---
title: "Muru: canaries without a service mesh"
description: "Canary releases under the Muru daemon, where a new release gets a share of the traffic, is judged against the release already serving, and is rolled back by itself if worse."
date: 2026-11-13
tags: ["python", "muru", "deployment"]
draft: true
---

In [releases, not restarts](/posts/2026/11/muru-releases-not-restarts/) I showed the Muru daemon deploying a new release beside the one serving, and only moving traffic across once the new release was ready. That protects you from a release which can't start. It does nothing for a release which starts perfectly well and then fails some of the requests it is given, which in my experience is the more common sort of bad deploy. A health check passes, the deploy reports success, and the first you hear about it is from the people using the site.

The usual answer is a canary. The new release is given a small share of the traffic first, is compared with the release already serving, and only gets more if it holds up. Automating that is normally something added around the server rather than something the server does. On Kubernetes it means something like Argo Rollouts or Flagger, typically with a service mesh or an ingress controller doing the traffic split and Prometheus queries deciding whether the new version is healthy. Off Kubernetes it tends to mean load balancer weights and someone watching a dashboard. Gunicorn, uvicorn and the other Python servers have nothing to say about it, since none of them has any notion of two versions of an application being compared.

Under the Muru daemon, the edge already splits traffic between releases and already counts what each release does with the requests it is given, so the daemon can run the canary itself.

## A release with a bug

Since the last post the shop has gained a page for each order, deployed as release `r5` the way that post showed. The next change adds prices to those pages:

```python
PRICES = {"teapot": 45.00, "kettle": 60.00}


def order(db, order_id):
    row = db.execute("SELECT item, quantity FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return None
    item, quantity = row
    total = quantity * PRICES[item]
    return f"Order {order_id}: **{quantity} x {item}** for ${total:.2f}"
```

Someone forgot about mugs. The order pages for teapots and kettles work, the home page works, and the page for the one order of a mug raises a `KeyError`. The release starts without a problem, so a plain deploy would put it in front of everyone.

Instead it is deployed with `--hold`, which starts the release but leaves it out of traffic:

```
muructl deploy shop releases/v6 --hold
```

```
muru: release shop@r6 is ready and held: not serving
```

In the last post I used the `Muru-Preview` header to reach a held release, and doing that here would find the bug for anyone who thought to check the right page:

```
curl -H 'Muru-Preview: r6' http://127.0.0.1:8080/orders/1
curl -H 'Muru-Preview: r6' http://127.0.0.1:8080/orders/3
```

```
<p>Order 1: <strong>1 x teapot</strong> for $45.00, served by shop@r6</p>
500 Internal Server Error
reason: app_error
request id: 01M6TE1RN0DZ6YEXWKNV4W5AKN

The application raised an exception.
```

The point of a canary is not having to know which page to check.

## Running a canary

A canary is judged on real requests, so to stand in for people using the site I ran a small script with four clients, each requesting one of the home page and the three order pages at random, as fast as the shop would answer them, for 25 seconds. The script doesn't keep cookies, which matters below. With it running:

```
muructl rollout canary shop@r6 --steps 10,50 --hold 30s
muructl rollout status shop --wait
```

```
muru: rollout 1 of shop@r6 started against r5: step 1 of 2: 10% for 30s
muru: rollout 1 running step 1 of 2: 10% for 30s
muru: rollout 1 rolled_back: gate failed at 10%: 5xx rate 21.95% over the limit of 1.00% (baseline 0.00%)
```

The plan was to give the new release 10% of the requests for 30 seconds, then 50% for another 30, and then all of them. It never got past the first step. The events show how quickly it was decided:

```
    44 18:20:02 notice   rollout.started      shop@r6                  rollout 1 against r5: 10% for 30s, 50% for 30s
    45 18:20:07 warning  rollout.gate_failed  shop@r6                  step 1 at 10%: 5xx rate 21.95% over the limit of 1.00% (baseline 0.00%)
    46 18:20:07 warning  rollout.rolled_back  shop@r6                  rollout 1: gate failed at 10%: 5xx rate 21.95% over the limit of 1.00% (baseline 0.00%); the candidate is kept for inspection
```

Five seconds after the canary started, the candidate was out of traffic again. Over the run the script got this back:

```
{200: 6618, 500: 27}
```

so 27 requests failed out of 6,645. A plain deploy would have failed a quarter of the order page requests for everyone until somebody noticed and rolled back.

What decided it is what Muru calls a gate. The edge keeps counters for every release, of the requests it answered, those answered with a 5xx status, and histograms of how long requests took overall and how long they waited for a worker. During a step the daemon reads those for the candidate and for the baseline, the release serving everything else, over the same window since the step began. Once the candidate has served 100 requests in the step, the gates are checked every second, and a failing gate rolls back straight away rather than waiting for the hold to end.

Importantly, a gate only fails if the candidate is both over its limit and worse than the baseline. If the database goes away and both releases start failing, that isn't the candidate's fault, and it isn't rolled back for it. The candidate is also kept running out of traffic, so its log can still be looked at, which `muructl logs shop@r6` shows has the traceback:

```
2026-11-07T07:20:07.756Z muru.worker[0]:   File "/Users/graham/shop/releases/v6/app.py", line 22, in order
2026-11-07T07:20:07.756Z muru.worker[0]:     total = quantity * PRICES[item]
2026-11-07T07:20:07.756Z muru.worker[0]:                        ~~~~~~^^^^^^
2026-11-07T07:20:07.756Z muru.worker[0]: KeyError: 'mug'
```

## A release that passes

The next release adds the price of a mug. This time I deployed it held as before, but started the canary with shorter steps, and asked for it to wait for my approval before each step after the first:

```
muructl deploy shop releases/v7 --hold
muructl rollout canary shop@r7 --steps 10,50 --hold 20s --approve-each-step
```

```
muru: rollout 2 of shop@r7 started against r5: step 1 of 2: 10% for 20s
```

While the candidate had its 10%, I wanted to see who was getting it. The edge doesn't pick a release at random for each request. It gives each new client an anonymous id in a `muru_id` cookie, and hashes that to decide which release the client gets. Because my load script keeps no cookies, each of its requests counts as a new client, which is why it saw both releases. A browser keeps the cookie, so to see what that means I used `curl` with a cookie jar as 20 separate clients, each making five requests to the home page:

```
client 1: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
client 2: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
...
client 7: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
client 8: shop@r7 shop@r7 shop@r7 shop@r7 shop@r7
client 9: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
...
client 16: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
client 17: shop@r7 shop@r7 shop@r7 shop@r7 shop@r7
client 18: shop@r7 shop@r7 shop@r7 shop@r7 shop@r7
client 19: shop@r7 shop@r7 shop@r7 shop@r7 shop@r7
client 20: shop@r5 shop@r5 shop@r5 shop@r5 shop@r5
```

Four of the 20 clients landed on the new release, and each of them stayed on it for every request, as did everyone else on the old one. Someone clicking around the site doesn't flip between versions from one page to the next. The buckets are also laid out so that a client in the canary at 10% is still in it at 50%.

After 20 seconds with the gates passing, the rollout stopped and waited:

```
muructl rollout status shop
```

```
APP              ROLLOUT  CANDIDATE    BASELINE     STATE              TRAFFIC  MESSAGE
shop             1        r6           r5           rolled_back        0%       gate failed at 10%: 5xx rate 21.95% over the limit of 1.00% (baseline 0.00%)
shop             2        r7           r5           awaiting_approval  10%      step 2 of 2: 50% for 20s awaits approval: muructl rollout resume shop
```

Approving the next step and following the rollout to the end:

```
muructl rollout resume shop
muructl rollout status shop --wait
```

```
muru: rollout 2 running: step 2 of 2: 50% for 20s
muru: rollout 2 running step 2 of 2: 50% for 20s
muru: rollout 2 promoted: every step passed its gates
```

The last step passing promoted the new release to take all of the traffic, with the old one drained and kept warm, so `muructl rollback shop` would still put things back at once. This time the load script got nothing but 200 responses, 20,421 of them.

## When a worker gets stuck

Errors are the easy case, as they show up as 5xx responses. Some bugs never produce a response at all. Here is a release where the order page takes a lock it already holds, but only for kettles:

```python
prices_lock = threading.Lock()


def order(db, order_id):
    ...
    with prices_lock:
        if item == "kettle":
            prices_lock.acquire()  # a bug: takes the lock it already holds
        total = quantity * PRICES[item]
```

The first request for a kettle blocks forever, and every request after it which wants the lock blocks behind it. Under gunicorn's sync workers the master would eventually kill the stuck worker for not answering its heartbeat, but a threaded worker keeps answering its heartbeat while its request threads are stuck, and nothing outside the server would connect any of that to the deploy which caused it.

Muru has a hard timeout for this, which replaces a worker when one of its requests has run too long. It is off by default, so I gave this release one of three seconds when deploying it, then started a canary as before:

```
muructl deploy shop releases/v8 --hold --timeout hard=3s
muructl rollout canary shop@r8 --steps 10,50 --hold 30s
```

```
muru: rollout 3 of shop@r8 started against r7: step 1 of 2: 10% for 30s
muru: rollout 3 running step 1 of 2: 10% for 30s
muru: rollout 3 rolled_back: gate failed at 10%: 2 worker crashes and timeout kills, over the limit of 0 (baseline 0)
```

This gate doesn't wait for 100 requests. A worker which crashes or is killed by a timeout counts against the candidate as soon as it happens, and by default one more than the baseline had in the step is enough to roll it back. The events say which workers were killed, and where they were stuck, which came from the stacks the host gathered from inside the worker before replacing it:

```
    70 20:53:23 warning  worker.timeout_killed shop@r8                  worker 0 (pid 82673) replaced by pid 83393: a request has run for 3.8 s, past the hard timeout of 3 s; at app.py line 27 in order, called from app.py line 39 in application, called from _pool.py line 30 in serve_jobs
    72 20:53:23 warning  worker.timeout_killed shop@r8                  worker 1 (pid 82674) replaced by pid 83395: a request has run for 3.6 s, past the hard timeout of 3 s; at app.py line 27 in order, called from app.py line 39 in application, called from _pool.py line 30 in serve_jobs
    75 20:53:24 warning  rollout.gate_failed  shop@r8                  step 1 at 10%: 2 worker crashes and timeout kills, over the limit of 0 (baseline 0)
```

Line 27 of `app.py` is the second `acquire()`. The release log has the full stack of every thread in each worker as well, much like the `muructl debug stacks` output from [looking inside the workers](/posts/2026/11/muru-looking-inside-the-workers/).

Looking at the timestamps, the rollback was about as quick as with the errors. The hard timeout fired about four seconds into the canary, and the decision to replace a stuck worker is what counted against the candidate, so it was out of traffic within a second. The stuck workers themselves were given their drain grace and went about 15 seconds later, by which time the candidate had no traffic left to lose. The load script ended up with two 504 responses and three requests it gave up on after five seconds, out of about 9,500. That is a long way short of every kettle order hanging for everyone.

There are more gates than the two I have shown. `--max-p95` and `--max-p99` judge how long the candidate's requests take, `--max-queue-wait` judges how long they wait for a worker thread, and `--probe` names URLs the daemon requests from both releases itself every five seconds, with one failing on the candidate alone enough to roll it back.

## Sticky clients and previews

The canary above uses the anonymous `muru_id` cookie to keep each client on one release. That can be changed per route, to hash a header such as a user id set by a proxy in front, a cookie of the application's own, or the client's address. When the canary ends, though, a client on the losing side is moved across on its next request. That is usually fine, but not for an application where a session started on one release shouldn't be continued on another. For that a route can be made sticky, so the edge sets a cookie naming the release a client was given and keeps honouring it for a grace period after that release leaves the route, before it drains.

The preview header used earlier also has a cookie form, `muru_preview=r7`, which makes it easy to try a held release in a browser, and a route can give a release a share of zero, so it is reachable only by preview, for a dark launch.

## What's next

Everything in this post and the last relied on the daemon being able to run more than one release of an application and move traffic between them. When the application is in a container, Muru deliberately does none of that, since there the container is the release, and starting, replacing and rolling back containers is the orchestrator's job. Next I will look at what `muructl serve` does instead as a container's main process, and why that makes it a better tenant than the usual gunicorn or uvicorn command.
