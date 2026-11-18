---
title: "Muru: noticing and responding"
description: "How Muru's conditions watch its own figures, such as the share of requests from AI crawlers or the health of a payment service, and trigger overlays that respond and then stop once it is over."
date: 2026-11-19
tags: ["python", "muru"]
draft: true
---

The [last post](/posts/2026/11/muru-overlays-on-a-schedule/) was about overlays, named pieces of configuration the Muru daemon lays over a site's routes for a while, activated by hand or on a schedule. Everything in it was known ahead of time. The backup runs at 2am, and the sale starts at 9am on Monday.

The things that cause the most trouble don't come with a schedule. AI crawlers turn up when they turn up, and some of them will happily take more of a site's capacity than all its real visitors put together. A payment provider goes down without telling anyone first. The usual answer is a monitoring system that notices, an alert that wakes someone up, and that person logging in to change something, which they then have to remember to change back once it is over. Automating that means a script hanging off an alerting webhook, which is one more thing to write, secure and keep working.

Muru has two pieces for this. A condition says when something holds over Muru's own figures, and an overlay can be triggered by a condition rather than by the time. Put together, Muru notices something, responds to it, and stops responding once it is over.

## Telling crawlers apart

Before anything can respond to crawlers, the edge has to know which requests are theirs. Muru gives every request a client class, worked out from rules declared beside the routes:

```toml
[host.shop]
names = ["shop.localhost"]
default = true

[[route]]
name = "shop"
host = "shop"
app = "shop"

[[client_class]]
name = "ai-crawler"
user_agent = ["GPTBot", "ClaudeBot", "CCBot"]

[rate_limit.crawlers]
match = { client_class = ["ai-crawler"] }
key = "client_class"
rate = "2/s"
burst = 2
```

Matching on the `User-Agent` is the simplest rule. Rules can also match addresses, headers, cookies or the JA4 fingerprint of a TLS connection, or check a claimed search engine crawler by looking up its address in DNS, and community lists of AI crawler user agents can be dropped in as files. A request matching no rule is class `default`. The class goes to the application as `muru.client_class` in the WSGI environ, into the access log, where `muructl logs --access` shows it as `class=ai-crawler` for anything but `default`, and onto the `client_class` label of the request metrics.

The rate limit is declared but nothing uses it yet. It gives the whole `ai-crawler` class two requests a second between them.

To have something to watch, I used a load script with two people's browsers asking for the shop's front page five times a second each for a whole run, and four crawlers, with a `GPTBot` user agent, asking as fast for the first part of it. Every five seconds it prints the answers so far, by status.

## A condition watches

A condition is declared in the same files:

```toml
[condition.crawler-surge]
when = "request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5"
for = "10s"
clear_when = "request_share{app='shop',client_class='ai-crawler'}[10s] < 0.2"
clear_for = "10s"
min_requests = 20
```

The expression is written to look like a Prometheus alerting rule, and that is deliberate, since it is the form people who run sites already know. `request_share` is the share of the shop's requests from the `ai-crawler` class, over a ten second window. The condition fires once the crawlers have been more than half the shop's requests for ten seconds, and resolves once they have been under a fifth for ten seconds. Having two thresholds with a gap between them stops a condition flapping around one value. `min_requests` is how many requests the window needs before a share counts as a figure at all, so a handful of requests can't fire it.

The windows here are short, where real ones would be minutes long. There are signals for request rates, error rates, latencies, queue depth, how busy the workers are, whether the autoscaler is at its limit, the node's memory and the health of upstream services, and terms can be joined with `and` and `or`. There is no arithmetic and no functions, which keeps a condition something you can read at a glance.

With no traffic, the share has no figure, and the condition is `unknown`:

```
$ muructl condition list
CONDITION     STATE     SINCE                 WHEN
crawler-surge unknown   -                     request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5
```

A few seconds into a run of the load script, the crawlers were two thirds of the requests, and the condition was waiting out its `for`:

```
$ muructl condition show crawler-surge
condition crawler-surge (applied)
  state       pending: when has held for 5s of 10s
  when        request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5
  for         10s
  clear_when  request_share{app='shop',client_class='ai-crawler'}[10s] < 0.2
  clear_for   10s
  min         20 requests
  term        request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5 is 0.6667
  term        request_share{app='shop',client_class='ai-crawler'}[10s] < 0.2 is 0.6667
```

Ten seconds after that, it fired:

```
  state       firing since 2026-11-17T06:29:30Z
```

When the crawlers stopped, their share dropped away, and `show` counted down the `clear_for` wait:

```
  state       firing since 2026-11-17T06:29:30Z; clear_when has held for 6s of 10s
```

before the condition resolved. Each change is an event, carrying the figures that caused it:

```
$ muructl events
...
    10 17:29:30 warning  condition.firing     crawler-surge            firing, when held for 10s; request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5: 0.6667; request_share{app='shop',client_class='ai-crawler'}[10s] < 0.2: 0.6667
    11 17:30:08 info     condition.resolved   crawler-surge            resolved, clear for 10s; request_share{app='shop',client_class='ai-crawler'}[10s] > 0.5: 0; request_share{app='shop',client_class='ai-crawler'}[10s] < 0.2: 0
```

And that was all that happened. The crawlers were served throughout:

```
 30s  people 296 x 200  crawlers 592 x 200
```

A condition does nothing by itself. That is the point of declaring one before anything acts on it, as it can be left watching real traffic, with its events going to wherever the other events go, until its thresholds and waits fire when you would actually want them to.

## Acting on it

An overlay triggered by the condition gives the crawlers a route of their own while it fires, the same as the shop's route but drawing on the rate limit:

```toml
[overlay.crawler-response]
routes.shop.client_routes.ai-crawler = { rate_limits = ["crawlers"] }
trigger = { condition = "crawler-surge" }
min_active = "20s"
cooldown = "1m"
```

Requests from everyone else carry on as before. I ran the load again, and once the condition fired, the overlay was active:

```
$ muructl overlay list
OVERLAY                  STATE              TRIGGER                            CHANGES
crawler-response         active (condition) condition crawler-surge, firing    route shop
```

and the crawlers' answers turned to 429s while the people's stayed 200s:

```
  5s  people 50 x 200  crawlers 100 x 200
 10s  people 100 x 200  crawlers 200 x 200
 15s  people 148 x 200  crawlers 296 x 200
 20s  people 198 x 200  crawlers 307 x 200, 89 x 429
 25s  people 248 x 200  crawlers 317 x 200, 179 x 429
 30s  people 296 x 200  crawlers 327 x 200, 265 x 429
```

A refused request is still counted as one of the shop's, so the crawlers stayed most of its requests and the condition kept firing for as long as they kept coming. Once they stopped, the condition resolved and the overlay ended with it. The events tell the whole story:

```
    13 17:30:34 warning  condition.firing     crawler-surge            firing, when held for 10s; ...
    14 17:30:34 notice   overlay.activated    overlay crawler-response activated: its condition crawler-surge is firing; ...
    15 17:30:35 warning  ratelimit.enforcing  rate_limit crawlers      began refusing or holding requests: 14 so far
    16 17:31:08 info     condition.resolved   crawler-surge            resolved, clear for 10s; ...
    17 17:31:08 notice   overlay.ended        overlay crawler-response ended: its condition crawler-surge resolved; ...
```

Nobody ran a command, and nothing was left for anyone to undo.

Something acting automatically needs to be kept from acting too often. `min_active` keeps the overlay active for at least a while however soon its condition resolves, five minutes by default. `cooldown` stops the condition activating it again for a while after it ends, ten minutes by default, and `max_per_hour` caps how many times it can activate in an hour. I sent another burst of crawlers straight after, inside the cooldown. The condition fired again, but the overlay stayed as it was, and the crawlers were served:

```
    18 17:31:35 warning  condition.firing     crawler-surge            firing, when held for 10s; ...
    19 17:31:35 warning  overlay.skipped      overlay crawler-response not activated though its condition crawler-surge is firing: its cooldown after it last ended lasts until 2026-11-17T06:32:08.559Z
```

## A response that hides its own cause

Rather than refusing the crawlers, an overlay could answer them from a static snapshot of the shop, which costs the application nothing at all:

```toml
[overlay.crawler-response]
routes.shop.client_routes.ai-crawler = { target = { static = "snapshot" } }
trigger = { condition = "crawler-surge" }
min_active = "20s"
cooldown = "1m"
```

This is the part of conditions I found most interesting, because it seems like an improvement and isn't. `muructl apply` accepted it, but warned:

```
muru: warning: overlay crawler-response takes shop's ai-crawler requests away from what condition crawler-surge reads, so the condition sees none of them and may resolve while they keep coming; rate-limit the class instead, or read the class's share of every request, without app
```

A request answered from a static directory isn't the application's. While the overlay is active, the crawlers vanish from the shop's figures, so their share of its requests falls to nothing, even though they are still coming. I ran it anyway, with the crawlers going for the whole run, to see what happens:

```
    24 17:33:34 notice   overlay.activated    overlay crawler-response activated: its condition crawler-surge is firing; ...
    25 17:33:53 info     condition.resolved   crawler-surge            resolved, clear for 10s; ...
    26 17:33:55 notice   overlay.ended        overlay crawler-response ended: its condition crawler-surge resolved; ...
    27 17:34:11 warning  condition.firing     crawler-surge            firing, when held for 10s; ...
    28 17:34:11 warning  overlay.skipped      overlay crawler-response not activated though its condition crawler-surge is firing: its cooldown after it last ended lasts until 2026-11-17T06:34:55.558Z
```

Twenty seconds after the overlay sent the crawlers to the snapshot, the condition saw no crawlers and resolved. The overlay ended and the crawlers were back on the shop, where the condition saw them and fired again, and only the cooldown stopped the overlay going straight back on. Without a cooldown, it would have flipped back and forth like this for as long as the crawlers kept coming.

An overlay must not take away what its own condition reads. There are two ways out. One is a condition on a figure the overlay doesn't change. Leaving `app` out of `request_share` counts every request the node takes, the snapshot's included. The other is `latch = true`, which keeps the overlay active after its condition resolves, until a person ends it:

```
$ muructl overlay list
OVERLAY                  STATE              TRIGGER                                    CHANGES
crawler-response         active (condition) condition crawler-surge, latched, resolved route shop
```

The condition resolved while the crawlers carried on, but the overlay stayed. Deciding when the crawlers have really gone is then left to a person, with `muructl overlay preview` showing the condition's figures beside what the overlay changes, and `muructl overlay end` ending it. A latch suits an overlay which responds to something going wrong, where Muru turning the response off on its own isn't wanted anyway.

## Holding capacity while a dependency is down

Overlays can set capacity as well as routes, and one of the cases where that matters is less obvious than crawlers. The shop's checkout calls out to a payment service, and when that is down, checkout fails straight away:

```python
def checkout(start_response):
    try:
        with urllib.request.urlopen(f"{PAYMENTS}/charge", timeout=2) as response:
            response.read()
    except (urllib.error.URLError, OSError):
        start_response("503 Service Unavailable", [("Content-Type", "text/plain")])
        return [b"Payments are unavailable, please try again shortly.\n"]

    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"Thank you for your order.\n"]
```

Failing fast is the right thing for the application to do, but it changes what the autoscaler sees. A checkout normally holds a worker thread while the payment goes through. When every checkout fails in a millisecond, the slots look idle, and the autoscaler does what it should with idle slots, as covered in the [scaling from what the workers report](/posts/2026/11/muru-scaling-from-what-the-workers-report/) post, and takes workers away. When the payment service comes back, the customers who were waiting all come back with it, and the shop is short of workers at exactly the wrong moment.

The shop has the same kind of spare mode policy as in that post, with its windows shortened so this happens in seconds rather than minutes, between one and four workers. I ran twelve clients doing checkouts, and the shop scaled out to four workers. Then I stopped the payment service:

```
 30s  1143 x 200
 40s  1603 x 200, 12 x 503
 50s  1603 x 200, 2189 x 503
```

and within half a minute the shop had given up half its workers:

```
    19 17:45:25 info     scaling.decision     shop@r1                  default: scale in from 4 to 3 workers: at least 3.50 idle workers over the last 20s, over max_spare 2; diagnosis: within capacity
    21 17:45:30 info     scaling.decision     shop@r1                  default: scale in from 3 to 2 workers: at least 2.75 idle workers over the last 20s, over max_spare 2; diagnosis: within capacity
```

With the payment service back, and the shop down to a single worker after a quiet spell, the next rush of checkouts had to wait on a scale-out:

```
    26 17:47:00 info     scaling.decision     shop@r1                  default: scale out from 1 to 3 workers: short by 2.00 workers for 5001ms; diagnosis: I/O bound with exhausted slots; ...
```

With a policy whose `min_workers` is zero, as in the [scaling to zero](/posts/2026/11/muru-scaling-to-zero/) post, the shop could have scaled all the way down while payments were out.

The autoscaler can't know that the idle slots are the symptom of something else. A condition can, if Muru is told about the payment service. Declaring it as an upstream with a health check gives the edge a figure for it:

```toml
[upstream.payments]
addresses = ["127.0.0.1:18540"]
health = { path = "/healthz", interval = "2s", unhealthy_after = 2, healthy_after = 2 }

[condition.payments-down]
when = "upstream_healthy{upstream='payments'} < 0.5"
for = "5s"
clear_when = "upstream_healthy{upstream='payments'} >= 1"
clear_for = "20s"
```

`upstream_healthy` is the share of the upstream's addresses in service, so the condition fires when more than half of them have failed their health checks, and resolves once all of them have been back for twenty seconds. The overlay holds the shop's capacity while it fires:

```toml
[overlay.shop-hold]
trigger = { condition = "payments-down" }
apps.shop = { min_workers = 4, scale_in = "hold" }
```

Running the same test again, the condition fired five seconds after the payment service stopped answering its health checks, and the overlay raised the floor:

```
    41 17:48:44 warning  condition.firing     payments-down            firing, when held for 5s; upstream_healthy{upstream='payments'} < 0.5: 0; upstream_healthy{upstream='payments'} >= 1: 0
    42 17:48:44 notice   overlay.activated    overlay shop-hold        activated: its condition payments-down is firing; ...
    43 17:48:45 info     scaling.decision     shop@r1                  default: scale out from 3 to 4 workers: raising toward the floor of 4 that shop-hold sets; diagnosis: within capacity
```

For the rest of the outage the shop held four workers, though every one of them was idle:

```
$ muructl scale status shop
shop@r1
GROUP        WORKERS      SLOTS      IDLE    QUEUE-P95     REAPS      POLICY
default      4            2/16       3.50    under 1 ms    5/6        spare 1-4 workers, 0-2 idle
  scheduled: 4-4 workers, no scale-in from shop-hold
  workers: cpu 1%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
  last: scaled out to 4: raising toward the floor of 4 that shop-hold sets (70s ago)
```

The health check doesn't depend on the shop's own requests, so this overlay can't hide its own cause the way the snapshot did. When the payment service came back, the condition resolved, and the overlay stayed on for the rest of its `min_active`, five minutes by default, which is time for the rush that follows an outage to arrive while the workers are still there. After that, the autoscaler goes back to deciding for itself.

The same pattern works the other way around. A cap, `cap_workers`, sets the most workers a group may have whatever its policy says, so while a struggling database is the bottleneck, a condition on its latency can stop the autoscaler adding workers that would only send it more queries at once.

## Signals from outside

Muru's figures only cover what Muru can see. A database replica falling behind, or a payment provider's status page announcing an incident, is something a monitoring system knows about first. An overlay with `trigger = { external = true }` can be activated and ended through a signed webhook, served on an address of its own given in the daemon's configuration file:

```toml
[overlay_webhook]
listen = "127.0.0.1:9466"
secret_file = "/etc/muru/overlay-webhook.key"
```

This overlay takes the shop read-only while payments are out, with a page that says so:

```toml
[overlay.payments-outage]
routes.shop.error_pages = { "503:read_only" = { template = "<h1>Checkout is paused</h1><p>Payments are down. Your cart is safe.</p>" } }
apps.shop = { mode = "read-only", deny = ["POST", "PUT", "PATCH", "DELETE"] }
trigger = { external = true }
```

A request to the webhook carries a JSON body saying what to do, and the HMAC-SHA256 of the body with the shared secret in a header, the same signing Muru uses for the events it sends out. The body includes the time it was made, which must be within five minutes of the daemon's clock, so a captured request can't be replayed later:

```
$ body='{"action": "activate", "time": "2026-11-17T06:50:36Z", "for": "2h"}'
$ signature=$(printf '%s' "$body" | openssl dgst -sha256 -hmac "$(cat /etc/muru/overlay-webhook.key)" | sed 's/^.* //')
$ curl -H "X-Muru-Signature: sha256=$signature" -d "$body" http://127.0.0.1:9466/v1/overlays/payments-outage:trigger
{"message":"activated by the webhook","overlay":"payments-outage"}
```

Sending the same request again was refused, since the overlay was already active, and one with a bad signature was turned away:

```
{"error":"refused","message":"overlay payments-outage is already active"}
{"error":"bad_signature","message":"X-Muru-Signature is not sha256= and the body's HMAC with the webhook's secret"}
```

While it was active, the overlay list showed who had activated it and for how long:

```
payments-outage          active (external) until 2026-11-17T08:50:36Z by hand or webhook                 route shop, app shop
```

and an attempt to add to the cart got the overlay's page:

```
$ curl -si -X POST http://127.0.0.1:8080/cart
HTTP/1.1 503 Service Unavailable
content-type: text/html; charset=utf-8
content-length: 71
cache-control: no-store
x-request-id: 01M7M4B4NT1VVWMGEPKW48DD5P
date: Tue, 17 Nov 2026 06:50:36 GMT

<h1>Checkout is paused</h1><p>Payments are down. Your cart is safe.</p>
```

A request with `"action": "end"` ended it again. An overlay activated by the webhook, or by hand, is only ended by the webhook or by hand, so a monitoring system that resolves its alert gets to say when the response is over.

## What's next

What I like about conditions is that the first step is only watching. A condition can sit against real traffic for a week, raising events, before anything is allowed to act on it, and when something does act, the events record what it saw, what it did, and when it stopped. The responses are the same overlays as in the last post, so everything about them, from the preview to the effective configuration, works the same whether a person, a schedule or a condition turned them on.

The overlay posts have been about the Muru daemon running a site. The next post, a toolbar on every page, goes back to development mode, and the toolbar Muru adds to each page under `muructl run`, with the timings, logs and errors of the request which produced it, and nothing changed in the application.
