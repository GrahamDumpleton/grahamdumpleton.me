---
title: "Muru: releases, not restarts"
description: "Deploying to the Muru daemon, where each deploy starts a new release beside the old one, rolling back is a routing change, and two releases can share a database."
date: 2026-11-12
tags: ["python", "muru", "deployment"]
---

With the [previous post](/posts/2026/11/muru-wsgi-and-asgi-together/) I finished with development mode. Something I kept coming back to in those posts was that when `muructl run` reloads after a change, it isn't restarting anything. It starts a new release beside the one serving, and only moves traffic across once the new release is ready. In [how it fits together](/posts/2026/11/muru-how-it-fits-together/) I said the same mechanism is what the daemon uses for deploying an application to a server. Time to show that.

This is where Muru departs most from how a Python web application is usually deployed. With gunicorn, deploying new code typically means putting the new code in place and sending the master process a HUP signal. Going by its own description, that reloads the configuration, starts new worker processes and gracefully shuts down the old ones, with the new workers loading the application code afresh unless `preload_app` is on, in which case the old code stays. A USR2 signal goes further, starting a second master and set of workers from the same command line beside the first, with the old master left around so a change can be backed out by sending more signals. Either way, there is one copy of the code on disk, both sets of workers share the one listening socket while they overlap, and anything more than that, such as keeping the previous version running so you can switch straight back to it, is left to a load balancer and a deploy script you write yourself. I can hardly point the finger, as mod_wsgi was no better, with a deploy there meaning a restart of Apache, or a similar mix of signals and gymnastics to get a daemon process to reload against different code.

Under the Muru daemon, each deploy is a release of its own, started beside the one serving, given traffic only once it is ready, and kept warm afterwards in case you want it back.

## Starting a daemon

The daemon runs in the background as your own user, or under systemd as a service. For trying things out, starting it as your own user is enough:

```
muructl daemon start
```

```
muru: daemon started (pid 31018), serving on http://127.0.0.1:8080, log /Users/graham/Library/Logs/muru/daemon.log
```

`muructl status --processes` shows the processes the daemon is looking after, which for now is only the edge it has started, listening on port 8080. The daemon's own row says whose daemon it is, here one run as my own user, and where it keeps its state:

```
muructl status --processes
```

```
edge  0 req/s  0 err/s  p50 0.0 ms  p95 0.0 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 0B/s

PID     ROLE      WHAT                                                    USER     UP    CPU      RSS   REQ/S   BUSY   QUEUE   P95   GIL/LAG
31018   daemon    user daemon, state ~/Library/Application Support/muru   graham   1s   0.0%   32.5MB
31019   └─ edge   listening on 127.0.0.1:8080                             graham   1s   0.0%   26.0MB       0
```

Nothing has been deployed yet, so the edge answers every request with a 503 and says why:

```
503 Service Unavailable
reason: no_workers
request id: 01M6TDFVFPFWF4JKE4TJ1G86E2

No worker is available to handle the request.
```

## A release is a directory

What gets deployed is a source directory. For this post the application is a small shop, kept in a directory per version under `releases`, as a deploy script might lay out checkouts of each tag. Each version is its own uv project with a `pyproject.toml` and a `uv.lock`, and the first version has no dependencies at all:

```toml
[project]
name = "shop"
version = "1.0"
requires-python = ">=3.15"
dependencies = []

[tool.muru]
entrypoint = "app:application"

[tool.muru.commands.migrate]
description = "Apply database migrations"
run = ["python", "migrate.py"]
exclusive = true
```

The application in `app.py` reports how many orders are in an SQLite database, and which release answered, using `muru.context()`:

```python
import os
import sqlite3

import muru

DATABASE = os.environ["SHOP_DATABASE"]


def application(environ, start_response):
    where = muru.context()
    with sqlite3.connect(DATABASE) as db:
        (count,) = db.execute("SELECT COUNT(*) FROM orders").fetchone()
    body = f"{count} orders, served by {where.app}@{where.release}\n".encode()
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [body]
```

The `migrate` command declared in `pyproject.toml` runs a small script which applies any SQL files in a `migrations` directory that haven't been applied yet. I will come back to commands later, as they matter once two releases share a database.

The first deploy names the application and the source directory, and gives the settings the release needs:

```
muructl deploy shop releases/v1 --processes 2 --env SHOP_DATABASE=/Users/graham/shop/data/shop.db
```

```
muru: release shop@r1 is ready and serving
```

The database starts out empty, so before anything else its tables need creating, by running the declared command with the release:

```
muructl command run shop migrate
```

```
applied 0001_orders.sql
```

after which the shop answers:

```
3 orders, served by shop@r1
```

There is a fair bit hidden behind that first deploy, and `muructl events` tells the story:

```
     2 18:10:12 info     release.created      shop@r1                  from /Users/graham/shop/releases/v1
     3 18:10:12 info     release.building     shop@r1                  from /Users/graham/shop/releases/v1/uv.lock
     4 18:10:12 info     release.built        shop@r1                  /Users/graham/Library/Application Support/muru/envs/shop/r1 in 0.1s from uv.lock 8c788a3a641a
     5 18:10:12 info     release.state_changed shop@r1                  fetched the runtime library muru-1.0.0-cp315-cp315t-macosx_11_0_arm64.whl from PyPI, once
     6 18:10:13 info     release.ready        shop@r1                  2 workers ready in 0.7 s
     7 18:10:13 notice   traffic.switched     shop@r1                  traffic moved to the release
     8 18:10:13 info     command.started      shop@r1                  migrate: started (pid 31050)
     9 18:10:13 info     command.finished     shop@r1                  migrate: exited with status 0 after 60ms
```

Because the source directory has a `uv.lock` and no `.venv`, the daemon built a virtual environment for the release from the lock file, in a directory belonging to that release alone. The application doesn't need to depend on Muru, as the daemon adds its own runtime library to the environment. Only once both workers were ready did traffic move to the release.

Asking for the processes again shows what the deploy added:

```
edge  0 req/s  0 err/s  p50 0.0 ms  p95 0.0 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 0B/s

PID     ROLE           WHAT                                                    USER     UP    CPU      RSS   REQ/S   BUSY   QUEUE   P95   GIL/LAG
31018   daemon         user daemon, state ~/Library/Application Support/muru   graham   2s   0.0%   38.9MB
31019   ├─ edge        listening on 127.0.0.1:8080                             graham   2s   0.0%   26.5MB       0
31045   └─ host        shop@r1 serving                                         graham   0s   0.0%   54.5MB            0/8       0
31044      ├─ relay    shop@r1 output to apps/shop/r1.log                      graham   0s   0.0%   17.5MB
31047      ├─ worker   group default, worker 0                                 graham   0s   0.0%   20.3MB            0/4
31048      └─ worker   group default, worker 1                                 graham   0s   0.0%   19.5MB            0/4
```

The release is a host process, which imported the application, with the two workers forked from it, each with four threads. The host's row also says what part the release has in routing, which for now is that it is serving. Beside the host is a log relay, which takes what the host and its workers write and puts it in the release's own log, so that a log which is slow to write never holds up a request. The relay is shown under the host it serves, although it is the daemon which starts it. The columns on the right, for requests per second, busy threads, queueing, response times and time spent waiting on the GIL, stay mostly empty until there is some traffic.

That each release gets an environment of its own is more important than it might look. If releases shared one virtual environment, installing a new dependency for the next release would change what the running release sees underneath it. Giving each release its own means a release really is fixed once started, which is what makes the rest of this work.

## A release that can't start

The second version of the shop renders its page with the `markdown` package, so where the first version returned plain text, it returns the count in bold as a line of HTML. Whoever made the change imported the package but forgot to add it to the project's dependencies, so it isn't in `uv.lock`. Deploying it:

```
muructl deploy shop releases/v2
```

```
Error: the host exited with exit status: 1 before its workers were ready: cannot load app:application: ModuleNotFoundError: No module named 'markdown'
```

The site carries on as if nothing happened, still answering from the first release:

```
3 orders, served by shop@r1
```

`muructl release list` shows the new release as failed beside the one still serving:

```
RELEASE                  STATE      SERVING  WORKERS               DISK SOURCE
shop@r2                  failed              - (2x4)              4.7MB /Users/graham/shop/releases/v2
                         the host exited with exit status: 1 before its workers were ready: cannot load app:application: ModuleNotFoundError: No module named 'markdown'
shop@r1                  ready      yes      2 (2x4)              4.7MB /Users/graham/shop/releases/v1
```

and the release's own log, from `muructl logs shop@r2`, has the same reason in context, after the lines from building its environment:

```
2026-11-07T07:10:13.431Z [build] Creating virtual environment at: /Users/graham/Library/Application Support/muru/envs/shop/r2
2026-11-07T07:10:13.478Z [build] Bytecode compiled 0 files in 42ms
2026-11-07T07:10:13.886Z muru.host[31069]: cannot load app:application: ModuleNotFoundError: No module named 'markdown'
```

The lines of a release's log carry the full time in UTC, as is usual for a log file, whereas `muructl events` gives the time of each event on the local clock.

Nor did the failed release leave anything running, with `muructl status --processes` showing the same processes as before the deploy. Had the new code been put in place over the old and the server reloaded, the new workers would have been trying to import the broken code from where the working code used to be. Here, the release that couldn't start cost nothing but the attempt.

## Moving traffic without refusing requests

The third version adds `markdown` to the project properly, with `uv add markdown`, so it ends up in the lock file.

Each deploy after the first takes what it isn't told from the release before it, so the two processes and the `SHOP_DATABASE` variable given to the first deploy carry through. A deploy with `--dry-run` shows what the deploy would do, with where each setting would come from, and changes nothing. Trimmed down a bit, that looks like:

```
muructl deploy shop releases/v3 --dry-run
```

```
muru: plan (nothing changed): release shop@r3, app:application 2x4 from /Users/graham/shop/releases/v3
  entrypoint = app:application          ([tool.muru])
  python = /Users/graham/.local/bin/python3.15t  (the previous release)
  build.when = auto                     (default)
  ...
  processes = 2                         (the previous release)
  threads = 4                           (the previous release)
  ...
  env SHOP_DATABASE (the previous release)
  ...
  settings nothing else gives come from shop@r1; --fresh takes none
  an environment would be built from the source's uv.lock
  the release would take over from shop@r1, which would stay warm for 1800s with 1 worker to a group
```

Environment variables carry across by name, which is why `SHOP_DATABASE` doesn't need to be given again. Where you would rather a deploy be described entirely by its own command line, `--fresh` ignores the previous release.

To see whether the switch refuses anything, I ran a small script which requests the page every 10 milliseconds, prints a line whenever the response changes, and counts the status codes it got back. With it running, I deployed the third version:

```
muructl deploy shop releases/v3
```

```
muru: release shop@r3 is ready and serving
```

The output of the script was:

```
18:10:14 200 3 orders, served by shop@r1
18:10:16 200 <p><strong>3 orders</strong>, served by shop@r3</p>
{200: 695}
```

Every one of the 695 requests got a 200, with the responses changing over from one release to the other without a gap. The events show the order things happened in:

```
    14 18:10:15 info     release.created      shop@r3                  from /Users/graham/shop/releases/v3
    15 18:10:15 info     release.building     shop@r3                  from /Users/graham/shop/releases/v3/uv.lock
    16 18:10:16 info     release.built        shop@r3                  /Users/graham/Library/Application Support/muru/envs/shop/r3 in 0.2s from uv.lock 62c319f2cb1f
    17 18:10:16 info     release.ready        shop@r3                  2 workers ready in 0.6 s
    18 18:10:16 notice   traffic.switched     shop@r3                  traffic moved to the release
    19 18:10:16 info     release.draining     shop@r1                  draining
    20 18:10:16 info     release.retained     shop@r1                  kept warm for 1800s with 1 worker per group
    21 18:10:17 info     worker.exited        shop@r1                  worker 1 (pid 31048) stopped: scaled in
```

The new release was built and started while the old one carried on serving. Traffic moved only once the new release was ready, and the old release then drained, finishing the requests it already had. What happened next to the old release is the interesting part. It wasn't stopped, but scaled in to a single worker and kept warm for 30 minutes, which `muructl release list` notes against it:

```
RELEASE                  STATE      SERVING  WORKERS               DISK SOURCE
shop@r3                  ready      yes      2 (2x4)              6.4MB /Users/graham/shop/releases/v3
shop@r2                  failed              - (2x4)              4.7MB /Users/graham/shop/releases/v2
                         the host exited with exit status: 1 before its workers were ready: cannot load app:application: ModuleNotFoundError: No module named 'markdown'
shop@r1                  retained            1 (2x4)              4.7MB /Users/graham/shop/releases/v1
                         warm until 07:40 UTC; a rollback to it is instant
```

The switch can also be watched as it happens, by leaving `muructl status --processes --watch` running in another terminal during the deploy. The third release's host, log relay and workers appear beside those of the first, the requests per second move across from one to the other, and the first then drops to a single worker.

## Rolling back is a routing change

Say the new page turns out to be a mistake. With the script running again:

```
muructl rollback shop
```

```
muru: rolled back to shop@r1 (ready)
```

```
18:10:24 200 <p><strong>3 orders</strong>, served by shop@r3</p>
18:10:26 200 3 orders, served by shop@r1
{200: 363}
```

The command took a fifth of a second. Nothing was deployed, built or imported. The retained release still had its host and a worker running, with the application already loaded, so rolling back was only a matter of telling the edge to send requests there instead. The events show what followed:

```
    22 18:10:26 notice   traffic.switched     shop@r1                  traffic moved to the release
    23 18:10:26 notice   app.rolled-back      shop                     rolled back to r1
    24 18:10:26 info     release.draining     shop@r3                  draining
    25 18:10:26 info     release.retained     shop@r3                  kept warm for 1800s with 1 worker per group
    26 18:10:26 info     worker.started       shop@r1                  worker 1 started as pid 31226
    27 18:10:26 info     worker.ready         shop@r1                  worker 1 (pid 31226) is ready
    28 18:10:27 info     worker.exited        shop@r3                  worker 1 (pid 31122) stopped: scaled in
```

Once it had traffic again, the first release grew back to its two workers by forking from its host, which still had the application imported, as described in [import once, fork many](/posts/2026/11/muru-import-once-fork-many/). The processes show this, with the first release's second worker only a few seconds old under a host which has been running all along, and the third release, now the retained one, down to the one worker it is kept warm with:

```
edge  0 req/s  0 err/s  p50 0.0 ms  p95 0.0 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 0B/s

PID     ROLE           WHAT                                                    USER      UP    CPU      RSS   REQ/S   BUSY   QUEUE   P95   GIL/LAG
31018   daemon         user daemon, state ~/Library/Application Support/muru   graham   17s   0.1%   40.7MB
31019   ├─ edge        listening on 127.0.0.1:8080                             graham   17s   0.0%   29.7MB       0
31045   ├─ host        shop@r1 serving                                         graham   15s   0.0%   54.5MB       0    0/8       0
31044   │  ├─ relay    shop@r1 output to apps/shop/r1.log                      graham   15s   0.0%   17.6MB
31047   │  ├─ worker   group default, worker 0                                 graham   15s   0.0%   48.8MB       0    0/4
31226   │  └─ worker   group default, worker 1                                 graham    3s   0.1%   29.4MB       0    0/4
31117   └─ host        shop@r3 retained until 07:40 UTC                        graham   13s   0.1%   56.2MB       0
31116      ├─ relay    shop@r3 output to apps/shop/r3.log                      graham   13s   0.0%   17.5MB
31121      └─ worker   group default, worker 0                                 graham   12s   0.0%   58.1MB
```

The release rolled back from is now the retained one, so running `muructl rollback shop` a second time goes forward to it again. Having decided the new page was fine after all, that is what I did, putting the third release back in front of the first:

```
muructl rollback shop
```

```
muru: rolled back to shop@r3 (ready)
```

The third release grew back to two workers in the same way, and the first went back to being the retained release with one.

Rolling back to a release which has already been stopped, because its 30 minutes are up, also works. The release then has to be started again first, with traffic moving once it is ready. When I tried that with this application, it took about a second rather than a fifth of one, which for a larger application would be however long its import takes.

## Restarting the daemon

The other thing which has to happen to a server from time to time is the hosting software itself being restarted or upgraded. As I explained in [how it fits together](/posts/2026/11/muru-how-it-fits-together/), the daemon is never on the path a request takes, which means it can go away while requests carry on. With the script running once more, I stopped the daemon:

```
muructl daemon stop
```

```
muru: daemon detached; hosts and the edge keep serving
```

With the daemon gone there is nothing for `muructl status --processes` to ask, so this time it has to be `ps`. Each of Muru's processes sets a title saying what it is, so `ps` is still readable, and shows the edge, the release hosts and their log relays are all still there, now with process 1 as their parent, and the workers still children of their hosts:

```
31019     1 muru edge user
31044     1 muru relay shop@r1
31045     1 muru host shop@r1
31047 31045 muru worker shop@r1 default/0
31116     1 muru relay shop@r3
31117     1 muru host shop@r3
31121 31117 muru worker shop@r3 default/0
31266 31117 muru worker shop@r3 default/1
```

Starting the daemon again, it finds them and takes them over:

```
    36 18:10:31 info     daemon.detached      daemon                   detached; hosts and the edge keep serving
    37 18:10:34 info     daemon.started       daemon                   serving on http://127.0.0.1:8080, admin socket /tmp/muru-501/admin.sock
    38 18:10:34 info     release.adopted      shop@r3                  re-adopted the host (pid 31117)
    39 18:10:34 info     release.adopted      shop@r1                  re-adopted the host (pid 31045)
    40 18:10:34 notice   traffic.switched     shop@r3                  traffic moved to the release
```

and `muructl status --processes` has them back in the tree under the new daemon, noting against the edge and each host it re-adopted that the operating system now has process 1 as its parent:

```
edge  0 req/s  0 err/s  p50 0.0 ms  p95 0.0 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 0B/s

PID     ROLE           WHAT                                                         USER      UP    CPU      RSS   REQ/S   BUSY   QUEUE   P95   GIL/LAG
31301   daemon         user daemon, state ~/Library/Application Support/muru        graham    1s   0.0%   35.8MB
31019   ├─ edge        listening on 127.0.0.1:8080 (re-adopted, OS parent 1)        graham   25s   8.4%   30.2MB       0
31045   ├─ host        shop@r1 retained until 07:40 UTC (re-adopted, OS parent 1)   graham   23s   0.0%   54.5MB
31044   │  ├─ relay    shop@r1 output to apps/shop/r1.log                           graham   23s   0.0%   17.6MB
31047   │  └─ worker   group default, worker 0                                      graham   23s   0.0%   48.9MB
31117   └─ host        shop@r3 serving (re-adopted, OS parent 1)                    graham   21s   0.0%   56.2MB            0/8       0          0.1 ms
31116      ├─ relay    shop@r3 output to apps/shop/r3.log                           graham   21s   0.0%   17.5MB
31121      ├─ worker   group default, worker 0                                      graham   20s   5.8%   68.5MB            0/4
31266      └─ worker   group default, worker 1                                      graham    7s   5.3%   63.1MB            0/4
```

The daemon is a second old, while everything under it has been running since before it was stopped. Meanwhile the script didn't notice anything had happened:

```
18:10:29 200 <p><strong>3 orders</strong>, served by shop@r3</p>
{200: 703}
```

Upgrading Muru works along similar lines. `muructl daemon upgrade` re-executes the daemon from the newly installed `muructl` and replaces the edge without refusing connections, while the releases keep the runtime library they started with until the next deploy replaces them.

## Two releases, one database

Being able to run two releases side by side has a consequence which is easy to overlook. While the new release is starting, and for as long as the old one is retained for a rollback, both are running against the same database. A schema change made for the new release therefore has to keep working with the code of the old one.

The usual answer is to split such a change into steps. The first step only adds things, such as a new table or a new column with a default, which the old code won't notice. Then the release which uses the new schema is deployed. Only once no release that relies on the old schema is serving or retained does a later release remove what is no longer needed. That is general advice, whatever you host with. What Muru adds is a way of running each step with the release it belongs to.

The fourth version of the shop adds a `quantity` column, in a new file `migrations/0002_quantity.sql`:

```sql
ALTER TABLE orders ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1;
```

and changes the page to report the number of items as well. If this were deployed like the others, the release would start, be ready, take all the traffic, and then fail every request because the column doesn't exist yet. Instead, it is deployed with `--hold`, which starts the release but leaves traffic where it is:

```
muructl deploy shop releases/v4 --hold
```

```
muru: release shop@r4 is ready and held: not serving
```

With the script from earlier still sending requests, the processes show the fourth release fully started and held, with its host, log relay and two workers, while every request is still going to the workers of the third:

```
edge  37 req/s  0 err/s  p50 1.8 ms  p95 2.7 ms  in flight 0  ws 0  conns 0  tls 0/s  in 0B/s  out 1.9KB/s

PID     ROLE           WHAT                                                         USER      UP    CPU      RSS   REQ/S   BUSY   QUEUE      P95   GIL/LAG
31301   daemon         user daemon, state ~/Library/Application Support/muru        graham    4s   0.0%   38.4MB
31019   ├─ edge        listening on 127.0.0.1:8080 (re-adopted, OS parent 1)        graham   28s   0.0%   30.3MB      37
31045   ├─ host        shop@r1 retained until 07:40 UTC (re-adopted, OS parent 1)   graham   27s   0.0%   54.5MB       0
31044   │  ├─ relay    shop@r1 output to apps/shop/r1.log                           graham   27s   0.0%   17.6MB
31047   │  └─ worker   group default, worker 0                                      graham   26s   0.0%   48.9MB
31117   ├─ host        shop@r3 serving (re-adopted, OS parent 1)                    graham   24s   0.0%   56.2MB      37    0/8       0   2.7 ms    0.1 ms
31116   │  ├─ relay    shop@r3 output to apps/shop/r3.log                           graham   24s   0.0%   17.5MB
31121   │  ├─ worker   group default, worker 0                                      graham   24s   0.0%   70.1MB      19    0/4           3.3 ms
31266   │  └─ worker   group default, worker 1                                      graham   11s   0.0%   63.5MB      19    0/4           2.5 ms
31345   └─ host        shop@r4 held                                                 graham    0s   0.0%   56.9MB            0/8       0
31344      ├─ relay    shop@r4 output to apps/shop/r4.log                           graham    0s   0.0%   17.4MB
31346      ├─ worker   group default, worker 0                                      graham    0s   0.0%   20.7MB            0/4
31347      └─ worker   group default, worker 1                                      graham    0s   0.0%   19.8MB            0/4
```

A held release can still be reached by naming it in a `Muru-Preview` header. Doing that now shows the problem the migration needs to fix, while ordinary requests are still served by the third release:

```
curl -H 'Muru-Preview: r4' http://127.0.0.1:8080/
```

```
500 Internal Server Error
reason: app_error
request id: 01M6TDGPENFWF4JKE4TJ1G86E2

The application raised an exception.
```

with `muructl logs shop@r4` showing why:

```
2026-11-07T07:10:40.086Z muru.worker[0]:     (count, items) = db.execute("SELECT COUNT(*), SUM(quantity) FROM orders").fetchone()
2026-11-07T07:10:40.086Z muru.worker[0]:                      ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2026-11-07T07:10:40.086Z muru.worker[0]: sqlite3.OperationalError: no such column: quantity
```

The migration is then run with the held release:

```
muructl command run shop@r4 migrate
```

```
applied 0002_quantity.sql
```

Naming the release matters here. A command runs with the release's own source directory, interpreter, environment variables and secrets, so this ran the fourth release's `migrate.py` against its own `migrations` directory, which is the only one with the new file in it. Commands are declared in the project and are part of each release, so the same command name always runs the version of the command which goes with that release's code. With `exclusive = true`, a second run of the command for the application is refused while one is under way, and `muructl command run` exits with the command's status, so a deploy script can stop at a failed migration before any traffic moves.

With the migration applied, the held release works, and the third release, which knows nothing about the new column, carries on serving ordinary requests:

```
<p><strong>3 orders</strong> for 3 items, served by shop@r4</p>
<p><strong>3 orders</strong>, served by shop@r3</p>
```

All that remains is to move the traffic:

```
muructl rollout bluegreen shop@r4
```

```
muru: release shop@r4 is ready and serving
```

The third release then becomes the one kept warm for a rollback, and the first, no longer needed for one, is stopped. Because the migration only added a column, rolling back to the third release afterwards still works against the new schema, which I checked by rolling back and forward again. The rollback doesn't touch the schema, which is the reason for doing changes like this in steps.

## What's next

With gunicorn and similar servers, all of this is something you build yourself around the server. Here it is what a deploy does.

That said, a deploy only protects you from a release which can't start. The fourth release, deployed without first holding it, would have been ready as far as Muru was concerned, and would then have failed every request it was given. The same goes for a release which starts fine but has a bug in only some of its pages. In the next post I will look at canaries, where a new release is given a small share of the traffic first and is judged against the release already serving, using what the workers report about the requests they handle, before it gets any more.
