---
title: "Muru: working with coding agents"
description: "Giving a coding agent the Muru daemon's operations over MCP, with a real Claude Code session deploying a broken change, diagnosing it from worker stacks and logs, rolling back, then fixing it."
date: 2026-11-18
tags: ["python", "muru", "ai"]
draft: true
---

When I wrote about [twenty years of mod_wsgi](/posts/2026/11/twenty-years-of-mod-wsgi/) and why I had started on Muru, part of the answer was AI coding tools. They are what made it practical for me to build something this size. The flip side is that coding agents are now often the ones running a web application while it is being worked on. They start it, poke at it, read what went wrong and change the code, and they do all of that through whatever the server gives them.

With gunicorn or uvicorn, what the server gives them is not much. An agent starts the server in the background, sends it some requests with `curl`, and reads whatever the server happened to print. If a request hangs, the agent sees a timeout and nothing else, so it goes back to reading the code and guessing. Seeing what a stuck thread is doing means reaching for something like py-spy, which may need privileges the agent doesn't have. And when it wants to try a change, it restarts the server and the old version is gone.

The earlier posts in this series covered what the Muru daemon knows while an application runs: releases, events, logs and tracebacks per release, what every worker thread is doing, and rollback as a routing change. This post is about handing all of that to a coding agent.

## The MCP server

`muructl mcp serve` speaks the Model Context Protocol on its standard input and output, and talks to the daemon over its admin socket the same way the other `muructl` commands do. For Claude Code, it goes in `.mcp.json` at the top of the project:

```json
{
  "mcpServers": {
    "muru": { "command": "muructl", "args": ["mcp", "serve", "--up"] }
  }
}
```

The `--up` option starts the user's daemon if none is answering, so the first tool call works on a fresh checkout. For this post my configuration also set environment variables pointing at a separate daemon of my own, which listened on port 18500.

The server offered 30 tools. Each one runs the `muructl` command of the same name with `--json` and returns what it prints, and each is marked for the client as either only reading or changing something. Deploying, rolling back, draining and running canary rollouts are there. Stopping or upgrading the daemon, running arbitrary code in a worker and one-off commands with `muructl exec` deliberately aren't, and `run_command` only runs the commands an application declares in its `[tool.muru]` settings.

What an agent may do can be cut down further. With `--read-only` the server lists only the 15 tools which read, so an agent can watch and diagnose but not change anything. With `--allow rollback,drain` it adds just those two. A tool left out isn't hidden by convention, it doesn't exist as far as the client is concerned. Calling `deploy` against a server started with `--read-only`:

```
{"jsonrpc": "2.0", "id": 3, "error": {"code": -32602, "message": "no tool named deploy"}}
```

## The skill

Tools let an agent operate Muru, but don't tell it what a release is, what each operation does to traffic, or what to check afterwards. That is what the skill is for. It is embedded in `muructl`, so it always matches the version being used, and is written into the project so it travels with the code:

```
muructl mcp skill install
```

```
muru: wrote the skill for muructl 0.1.0-alpha.19 to .claude/skills/muru/SKILL.md
```

It is about 130 lines. It describes applications, releases, traffic and overlays, has a table of each operation and what it does to traffic, and lays out a development loop: check the status, deploy the working tree, run the tests against the daemon's listener, and when something fails, find out why from events, logs and worker stacks before changing any code. It works through the MCP tools when the agent has them, and through `muructl --json` when it doesn't.

`muructl mcp skill status` says whether the project's copy is current, and exits with a non-zero status when it isn't, so a CI job can check it after `muructl` is upgraded. The MCP server checks as well. In a project without the skill, the instructions it gives the agent at the start of a session end with:

```
The Muru skill: the project carries no skill at .claude/skills/muru/SKILL.md; `muructl mcp skill install` writes it.
```

## An agent and a broken change

To see how this works in practice, I set up a small WSGI shop application in a git repository, with a few JSON pages over a dictionary of orders, guarded by a lock, and a `tests.py` which runs against the daemon's listener. The committed version was deployed as `shop@r1` and passed its tests.

I then made an uncommitted change of the kind a colleague might leave behind. It added an `/orders/summary` page and a test for it, and along the way changed `get_order()` to index the dictionary rather than call `.get()`. The new `summary()` function took the lock and then called `all_orders()`, which takes the same lock. A plain `threading.Lock` isn't reentrant, so that is a deadlock.

I then ran Claude Code headless in the project, with the MCP server above, the skill installed, and permission to use only the Muru tools, `python3 tests.py`, and tools for reading files. The prompt was:

> A colleague left an uncommitted change in this working tree that adds an order summary page. Deploy the working tree as a new release of the `shop` application using the muru tools, then run `python3 tests.py` against it. If tests fail, use the muru tools to find out why rather than guessing from the code alone, roll the application back to the previous release so the shop keeps working, and report what you found. Don't change any code yet.

Everything that follows comes from the session's record of tool calls and their results.

The agent loaded the muru skill, looked at the git diff, then called `status` and `list` to see which release was serving. It then deployed:

```
mcp__muru__deploy {"app": "shop", "source": ".../s7/shop"}
```

The tool waits until the release is ready or has failed, and returned the release, trimmed here:

```json
{
  "app": "shop",
  "id": "r2",
  "state": "ready",
  "message": "",
  "serving": true,
  "processes": 2,
  "threads": 4,
  "python_version": "3.15.0",
  ...
}
```

Running the tests, three of the five failed:

```
test_home (__main__.ShopTests.test_home) ... ok
test_missing_order (__main__.ShopTests.test_missing_order) ... ERROR
test_order (__main__.ShopTests.test_order) ... ok
test_orders (__main__.ShopTests.test_orders) ... ERROR
test_summary (__main__.ShopTests.test_summary) ... ERROR
```

Most of the errors were five second timeouts in the test client, which say nothing about the cause. The agent's next call was the one that mattered:

```
mcp__muru__debug {"what": "stacks", "target": "shop@r2"}
```

The result lists, for each worker, the requests in flight and the stack of every thread, with the request each thread is serving. For worker 0 it reported three requests in flight, `/orders/summary` for 29.9 seconds, `/orders/99` for 19.2 seconds and `/orders` for 14.2 seconds. The thread serving the summary, trimmed to the last of its frames:

```json
{
  "name": "muru-app-0",
  "request": {"method": "GET", "path": "/orders/summary", "elapsed_ms": 29878, ...},
  "frames": [
    ...
    {"file": ".../shop/app.py", "line": 19, "function": "application",
     "text": "return respond(start_response, \"200 OK\", orders.summary())"},
    {"file": ".../shop/orders.py", "line": 23, "function": "summary",
     "text": "orders = all_orders()"},
    {"file": ".../shop/orders.py", "line": 12, "function": "all_orders",
     "text": "with _lock:"}
  ]
}
```

The other two threads were stuck on the same lock, at `orders.py` lines 12 and 17. One request for the summary page had taken the lock and never let it go, and every other request touching orders in that worker then queued up behind it. That explained why the set of failing tests grew between the agent's two test runs, which otherwise looks like a flaky test.

It then read the release's output with `logs`, which had the traceback for the other failure:

```
muru.worker[1]: Traceback (most recent call last):
muru.worker[1]:   File ".../shop/app.py", line 21, in application
muru.worker[1]:   File ".../shop/orders.py", line 18, in get_order
muru.worker[1]: KeyError: 99
```

and `logs` with `access` set, where the same request showed up on r2 as a 500 with the reason `app_error`, where r1 had answered 404. It read the events, read `orders.py` to confirm what the stacks and traceback said, and rolled back:

```
mcp__muru__rollback {"app": "shop"}
```

which returned r1, with `"state": "ready"` and `"serving": true`, and a `list` of releases showed r2 kept warm, not serving. The agent ran the tests once more to check the rollback. The four original tests passed, and the summary test failed as you would expect, since r1 predates the page.

Its report named both defects, with the file and line for each, and pointed out that the deadlock wasn't confined to the new page, but took down every order endpoint in a worker once it happened. The session took 23 turns and about a minute and three quarters.

## Fixing it

I then resumed the same session:

> Thanks. Go ahead and fix both problems, deploy the fix as a new release, and run the tests against it. If they pass, leave the new release serving and drain the release with the deadlock, since nothing should go back to it.

This time it was allowed to edit files. It changed `get_order()` back to `.get()`, and moved the call to `all_orders()` in `summary()` out from under the lock. It deployed the result as `shop@r3`, and the tests passed:

```
test_home ... ok
test_missing_order ... ok
test_order ... ok
test_orders ... ok
test_summary ... ok

Ran 5 tests in 0.013s

OK
```

Before draining anything, it called `debug` with `status` on r3 to check that no thread was left holding a request. It then drained r2, and the releases ended up as:

```
r3 ready True
r2 stopped False superseded again
r1 retained False warm until 12:30 UTC; a rollback to it is instant
```

It also noted, without being asked, that r1 was now the instant rollback target and didn't have the summary page, which is the kind of thing worth knowing before you reach for a rollback. That took eight turns and 45 seconds.

None of what the agent did needed it to restart anything, and at every point there was a working release it could go back to. The two releases being separate is what let it look at the broken one's workers while the hang was still in progress, rather than reconstructing it from the code afterwards.

## Without MCP

An agent working through a shell, or a script, gets the same answers from `muructl` directly. Every command which reports something takes `--json` and prints exactly what the corresponding tool returns:

```
muructl release list shop --json | python3 -c 'import json,sys; [print(r["id"], r["state"], r["serving"], r["message"]) for r in json.load(sys.stdin)["releases"]]'
```

That is where the release list above came from. A failure prints an error object, with a non-zero exit status:

```
muructl rollback blog --json
```

```
{
  "error": "application blog does not exist"
}
```

and `muructl events --json --after 28` returns only the events after a given sequence number, so a script can keep up with what has happened without parsing text.

There are still a few rough edges. In the release JSON, for example, the time a retained release stays warm is only in the `message` text, while its `retained_until_unix_ms` field is 0, so a script has to parse prose to find it.

## What's next

This is the last of the posts I had planned on Muru for now. The first ones were about what is different in development mode, then the daemon with releases, canaries and scaling, then containers and Kubernetes, and this one ties it back to the reason I started. Muru was built with a coding agent, and it turns out the things that make it easier for me to see what an application is doing, such as stacks for every thread, logs and events for each release, and rollback as a routing change, are just as useful when the one looking is an agent.
