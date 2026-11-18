---
title: "Muru: overlays on a schedule"
description: "How Muru's overlays lay temporary changes over a site's configuration, by hand or on a schedule, for backups, maintenance windows, timed cutovers and busy periods."
date: 2026-11-18
tags: ["python", "muru"]
---

The [last post](/posts/2026/11/muru-scaling-to-zero/) was about the Muru daemon taking an idle site down to nothing. This one is about something every site has to deal with eventually, which is a change that is only meant to last for a while.

The database is backed up at 2am, and the site shouldn't take orders while that happens. A schema change on Saturday night needs the site down for an hour, with a page saying when it will be back. A sale starts at 9am on Monday, and the new version of the shop should be serving it at exactly that time. None of these is a permanent change to how the site is served, but each needs the configuration to be different for a while, and then to go back to how it was.

With gunicorn or uvicorn behind nginx, the usual answer is to edit something and remember to undo it. A maintenance page is often an `if (-f /srv/shop/maintenance.html)` test in the nginx configuration, with someone touching and removing the file, or a cron job doing it for them. A read-only period is a flag the application checks, set by hand or from another cron job. A timed switch to a new version is someone awake at 9am to run the deploy. Each of these lives somewhere different, and nothing in the server knows any of them is temporary.

Muru has one mechanism for all of these, which it calls an overlay.

## An overlay is laid over the configuration

An overlay is a named piece of configuration laid over routes and applications while it is active. The configuration underneath never changes. When the overlay ends, the routes are as they were, including any change made to them while it was active, so ending an overlay can't undo something someone else did in the meantime.

Overlays are declared beside the routes they change, in the files that `muructl apply` reads. For the shop in this post, that starts with a virtual host and a route which has a name an overlay can refer to:

```toml
[host.shop]
names = ["shop.localhost"]
default = true

[[route]]
name = "shop-root"
host = "shop"
app = "shop"

[overlay.nightly-backup]
apps.shop = { mode = "read-only", deny = ["POST", "PUT", "PATCH", "DELETE"] }
trigger = { schedule = { cron = "0 2 * * *", duration = "1h", timezone = "Australia/Sydney" } }
```

The overlay makes the shop read-only for an hour from 2am Sydney time each night. While it is active the edge refuses the methods in `deny` without troubling the workers, and the application is passed the mode as `muru.mode` in the WSGI environ, so it can stop offering what the mode rules out:

```python
def application(environ, start_response):
    time.sleep(0.02)  # as if rendering from a database

    if environ["REQUEST_METHOD"] == "POST":
        start_response("303 See Other", [("Location", "/")])
        return [b""]

    read_only = environ.get("muru.mode") == "read-only"
    page = PAGE.format(actions=PAUSED if read_only else CART)

    start_response("200 OK", [("Content-Type", "text/html")])
    return [page.encode()]
```

The mode is any short word, so an application can have modes of its own. Muru doesn't interpret it beyond passing it on.

Once applied, `muructl overlay list` shows the overlay, its trigger, what it changes and when it is next due:

```
$ muructl overlay list
OVERLAY                  STATE                          TRIGGER                                  CHANGES
nightly-backup           idle from 2026-11-17T15:00:00Z cron '0 2 * * *' for 1h Australia/Sydney app shop
```

The time shown is UTC, which is 2am in Sydney. The schedule follows daylight saving in the zone it names, so a window doesn't drift by an hour twice a year, and because a cron schedule depends on the system clock, the daemon checks every ten minutes that the clock is synchronised and raises a warning event when it isn't.

`muructl overlay preview` says what activating the overlay now would change, field by field:

```
$ muructl overlay preview nightly-backup
app shop: mode (none) -> read-only
app shop: methods.deny (none) -> POST, PUT, PATCH, DELETE
```

## Turning one on by hand

A schedule is only one way to activate an overlay. Backups don't always run when they are meant to, and sometimes the read-only period is needed right now. Any overlay can be activated by hand, until it is ended, for a duration, or until a given time:

```
$ muructl overlay activate nightly-backup --for 10m
muru: overlay nightly-backup activated by hand, until 2026-11-17T06:38:03Z
```

The page now says orders are paused instead of offering the cart:

```
$ curl -s http://127.0.0.1:8080/
<!doctype html>
<title>Shop</title>
<h1>Today's offers</h1>
<p>Orders are paused for a few minutes, but you can still browse.</p>
```

and anything that would change the site is refused by the edge:

```
$ curl -si -X POST http://127.0.0.1:8080/cart
HTTP/1.1 503 Service Unavailable
content-type: text/plain; charset=utf-8
content-length: 147
cache-control: no-store
x-request-id: 01M7M31W21TJAZMK3QZF9FZD7M
date: Tue, 17 Nov 2026 06:28:03 GMT

503 Service Unavailable
reason: read_only
request id: 01M7M31W21TJAZMK3QZF9FZD7M

The site is read-only for now, and this request would change it.
```

With `answer = "method_not_allowed"` beside `deny`, the edge would answer 405 instead, with the methods still allowed in `Allow`.

The overlay list says how the overlay was activated and when it ends:

```
$ muructl overlay list
OVERLAY                  STATE                                      TRIGGER                                  CHANGES
nightly-backup           active (manual) until 2026-11-17T06:38:03Z cron '0 2 * * *' for 1h Australia/Sydney app shop
```

When something isn't behaving as expected, the question is usually what configuration is actually in force right now. `muructl config show --effective` answers that, headed by what each active overlay sets:

```
$ muructl config show shop --effective
# Muru effective state: muructl 1.0.0 on grumpys-mac-mini, 2026-11-17T06:28:03Z, state version 9.
# The active overlays set, and the routes below include:
#   app shop: methods.deny = POST, PUT, PATCH, DELETE (overlay nightly-backup)
#   app shop: mode = read-only (overlay nightly-backup)
...
```

An active overlay is part of the daemon's state rather than something held in memory. Stopping the daemon in the middle of the overlay, and starting it again:

```
$ muructl daemon stop
muru: daemon detached; hosts and the edge keep serving
$ muructl daemon start
muru: daemon started (pid 73330), serving on http://127.0.0.1:8080, log ...
$ muructl overlay list
OVERLAY                  STATE                                      TRIGGER                                  CHANGES
nightly-backup           active (manual) until 2026-11-17T06:38:03Z cron '0 2 * * *' for 1h Australia/Sydney app shop
```

the overlay was still active, and a POST was still refused. The daemon works out each second which overlays should be active from the time and what it has recorded, so a daemon restarted in the middle of a scheduled window carries on with it as well. Ending the overlay by hand put things back:

```
$ muructl overlay end nightly-backup
muru: overlay nightly-backup ended by hand
```

The POST was answered by the application again, and the overlay went back to waiting for 2am.

## A maintenance window with its own page

Some work needs the site down entirely. An overlay can turn on maintenance mode for an application, and choose the page people see while it is on:

```toml
[overlay.db-upgrade]
apps.shop = { maintenance = true }
routes.shop-root.error_pages = { "503:maintenance" = { file = "pages/maintenance.html" } }
trigger = { schedule = { start = "2026-11-17T17:31", end = "2026-11-17T17:33", timezone = "Australia/Sydney" } }
```

A `start` and an `end` give one window rather than a recurring one.

What maintenance mode lets through is part of the application's own settings, in its `pyproject.toml`, since it is something the application knows about itself:

```toml
[tool.muru.maintenance]
exempt_paths = ["/health"]
exempt_addresses = ["10.0.0.0/8"]
bypass_cookie = "muru_bypass=letmein"
retry_after = "15m"
```

When the window began, the overlay activated, and every request routed to the shop was answered by the edge with the page from the overlay and a `Retry-After` of fifteen minutes:

```
$ curl -si http://127.0.0.1:8080/
HTTP/1.1 503 Service Unavailable
content-type: text/html; charset=utf-8
content-length: 126
cache-control: no-store
retry-after: 900
x-request-id: 01M7M37BXBTJAZMK3QZF9FZD7S
date: Tue, 17 Nov 2026 06:31:03 GMT

<!doctype html>
<title>Back soon</title>
<h1>We're upgrading the shop</h1>
<p>It will be back by 10pm. Your cart is safe.</p>
```

`muructl app list` marks the application as in maintenance, and names the overlay which put it there:

```
$ muructl app list
APP                  CURRENT      PREVIOUS     USER
shop                 r1           -            - [maintenance by overlay db-upgrade]
```

The health check path was still served, so a load balancer in front doesn't decide the whole node is gone. With the bypass cookie, the real site came back:

```
$ curl -s -b muru_bypass=letmein http://127.0.0.1:8080/
<!doctype html>
<title>Shop</title>
<h1>Today's offers</h1>
<form method="post" action="/cart"><button>Add to cart</button></form>
```

That cookie is the part I find most useful. Whoever is doing the upgrade can check that the site works before anyone else sees it, and then end the maintenance early if it is done before the window is over:

```
$ muructl overlay end db-upgrade
muru: overlay db-upgrade ended by hand
$ muructl overlay list
OVERLAY                  STATE                            TRIGGER                                                       CHANGES
db-upgrade               ended until 2026-11-17T06:33:00Z from 2026-11-17T17:31 until 2026-11-17T17:33 Australia/Sydney route shop-root, app shop
...
```

A scheduled overlay ended by hand stays ended until its window is over, rather than the schedule turning it straight back on a second later. The events record what happened and why:

```
$ muructl events
...
    27 17:31:00 notice   overlay.activated    overlay db-upgrade       activated: its schedule's window began
    28 17:31:20 notice   overlay.ended        overlay db-upgrade       ended by hand
```

## Trying a schedule before letting it act

A schedule which acts on its own is only as good as the cron expression and time zone it was given, and getting either wrong means something happens at the wrong time with nobody watching. With `advisory = true`, a schedule only raises an event as each window begins, and the overlay has to be activated by hand:

```toml
[overlay.stocktake]
routes.shop-root = { mode = "read-only", deny = ["POST", "PUT", "PATCH", "DELETE"] }
trigger = { schedule = { cron = "32 17 * * *", duration = "1m", timezone = "Australia/Sydney" } }
advisory = true
```

When its window came around, the overlay list said it had been advised rather than activated:

```
stocktake                advised until 2026-11-17T06:33:00Z cron '32 17 * * *' for 1m Australia/Sydney, advisory          route shop-root
```

and the event says what would have happened:

```
    29 17:32:00 notice   overlay.would_activate overlay stocktake        would activate: its schedule's window began; it is advisory
```

The shop kept taking orders. Once the events show a schedule firing when it should, removing `advisory` lets it act.

## A timed cutover

The sale starting at 9am on Monday is a different kind of temporary change. The overlay pins the route's traffic to a new release at a given time:

```toml
[overlay.summer-sale]
routes.shop-root.traffic = { pin = "r2" }
trigger = { schedule = { start = "2026-11-17T17:35", timezone = "Australia/Sydney" } }
warm_up = { start_release = "r2", lead = "1m" }
preconditions = { release_ready = "r2", probe = "/healthz" }
```

The release is deployed ahead of time with `--hold`, so it starts but takes no traffic, as covered in the [releases, not restarts](/posts/2026/11/muru-releases-not-restarts/) post. The `warm_up` starts the release ahead of the window if it has been stopped, so the switch lands on warm workers. The `preconditions` are what stop a timed switch moving traffic to something broken. The release has to be ready, and it has to answer the probe path with a 2xx or 3xx response, asked through the edge as a preview of that release.

In my case, r2 had a bug, and its health check couldn't reach its database:

```
$ muructl deploy shop v2 --hold
muru: release shop@r2 is ready and held: not serving
$ curl -s -H "Muru-Preview: r2" http://127.0.0.1:8080/healthz
database unreachable
```

Trying the overlay out by hand ahead of time showed this straight away:

```
$ muructl overlay activate summer-sale
muru: error: overlay summer-sale was not activated: its probe of shop@r2 failed: /healthz (as a preview, at host shop) answered 503 Service Unavailable
```

Had nobody checked, the scheduled activation would have been skipped in the same way, with an `overlay.skipped` warning event saying why, and the old release would have gone on serving. That is a much better outcome at 9am on a Monday than the sale page answering with errors.

With the bug fixed and deployed as r3, also held, I changed the overlay to name r3 and applied it again:

```
$ muructl overlay preview summer-sale
route shop-root: traffic.split (none) -> r3 100%
```

A minute before the window began, the warm-up started, and at the start of the window the overlay activated:

```
    30 17:34:00 info     overlay.warming      overlay summer-sale      warming up: its window begins in 59s; starting shop@r3
    31 17:35:00 notice   overlay.activated    overlay summer-sale      activated: its schedule's window began
```

A client asking for the page every fifty milliseconds through the switch saw the old page, then the new one, and nothing else:

```
17:34:03 200 Today's offers
17:35:01 200 Summer sale
{"200 Today's offers": 739, '200 Summer sale': 424}
```

A timed switch like this is usually meant to be permanent. `muructl overlay promote` folds an active overlay's changes into the base configuration and ends the overlay. For a pin, that makes the pinned release the application's serving release, just as a deploy would:

```
$ muructl overlay promote summer-sale
muru: overlay summer-sale promoted: its changes are now the base configuration; shop@r3 serves in place of shop@r1, which is retained
muru: the next apply undoes this unless the applied files say the same: put this in them, and remove overlay summer-sale

# shop: where the files name its serving release
[app.shop]
serving = "r3"
```

The release which was serving before is kept warm for a rollback, the same as after a deploy, and the next deploy replaces r3 as usual:

```
$ muructl release list
RELEASE                  STATE      SERVING  WORKERS               DISK SOURCE
shop@r3                  ready      yes      2 (2x4)              4.9MB /Users/graham/shop/v3
shop@r2                  ready               2 (2x4)              4.9MB /Users/graham/shop/v2
                         held: not serving
shop@r1                  retained            1 (2x4)              4.9MB /Users/graham/shop/v1
                         warm until 07:05 UTC; a rollback to it is instant
```

The applied files still say what they said before, so promote prints what to put in them, here the serving release, for the next `muructl apply` to keep the switch rather than undo it. The promoted overlay should then be taken out of the files.

## Known busy periods

Overlays can also set capacity, and an application can declare schedules for load that is known in advance. A schedule on the application is an overlay by another name, written beside the application:

```toml
[[app.shop.schedule]]
name = "black-friday"
start = "2026-11-27T00:00"
end = "2026-11-30T23:59"
timezone = "America/New_York"
min_workers = 4
scale_in = "hold"
freeze_deploys = true
```

For the four days of the sale the shop keeps at least four workers, never scales in, and refuses deploys. It shows up in the overlay list as `shop.black-friday`:

```
shop.black-friday        idle from 2026-11-27T05:00:00Z from 2026-11-27T00:00 until 2026-11-30T23:59 America/New_York app shop
```

and since it is an overlay, it can be tried out by hand like any other:

```
$ muructl overlay preview shop.black-friday
app shop: group default: at least 4 workers, no scale-in
app shop: deploys and rollouts frozen
$ muructl overlay activate shop.black-friday --for 10m
muru: overlay shop.black-friday activated by hand, until 2026-11-17T06:48:17Z
```

The worker group rose to the floor, and `muructl scale status` names the overlay which set it:

```
$ muructl scale status shop
shop@r3
GROUP        WORKERS      SLOTS      IDLE    QUEUE-P95     REAPS      POLICY
default      4            0/16       4.00    under 1 ms    -          static
  scheduled: 4-4 workers, no scale-in from shop.black-friday
  workers: cpu 0%, gc 0%, gil wait p95 under 0.1 ms, loop lag p95 -
  diagnosis: within capacity
  last: scaled out to 4: raising toward the floor of 4 that shop.black-friday sets (3s ago)
```

The shop has a static count of two workers, so the floor raises that count for the window. With an autoscaling policy, as in the [scaling from what the workers report](/posts/2026/11/muru-scaling-from-what-the-workers-report/) post, the floor sets the least the autoscaler may go down to, and a `max_workers` in the schedule can raise its ceiling too.

The deploy freeze is there for the person who decides on the Friday that a small fix can't wait:

```
$ muructl deploy shop v1
muru: error: deploys of shop are frozen by overlay shop.black-friday; give --override-freeze to deploy anyway
```

When it really can't wait, `--override-freeze` lets the deploy through, and records that it did:

```
    74 17:38:23 warning  deploy.freeze_overridden shop                     deploy despite the freeze set by overlay shop.black-friday
```

Rolling back is never frozen, since a freeze that stopped someone undoing a bad deploy would be worse than no freeze at all.

## What's next

What these overlays have in common is that someone knew ahead of time when they were needed, even if the answer was "now". The backup runs at 2am, the upgrade is on Saturday night, and the sale starts at 9am. Muru holds the change, applies it at the right time, refuses to apply it when the release it depends on is broken, and takes it away again afterwards, and the base configuration is never touched in the process.

Not everything can be planned for, though. Crawlers turn up when they turn up, and a payment provider goes down without telling anyone first. The next post, noticing and responding, is about overlays which are activated by what Muru sees happening rather than by the time.
