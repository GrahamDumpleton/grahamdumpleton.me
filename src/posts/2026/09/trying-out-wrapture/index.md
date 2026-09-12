---
title: "Trying out wrapture"
description: "wrapture and its instrumentation packages are now at 1.0.0b1 with the API settled. A summary of the posts so far, the packages, the docs, and 24 workshops you can run in your browser on mybinder."
date: 2026-09-12
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapture"
tags: ["python", "wrapture", "testing", "tracing", "jupyter"]
draft: false
---

Since [introducing wrapture](/posts/2026/08/introducing-wrapture/) at the end of August I have been putting out a post every day or so, first working through how it is used in unit tests and then how the same bindings trace a running application. With the last of the tracing posts now done, this is the point where I wanted to stop, take stock, and pull everything together in one place for anyone who wants to try it out.

## Where things stand

The short version is that wrapture has been bumped to version 1.0.0b1. That move from alpha to beta is deliberate. I am happy with the APIs as they are and I am not seeing a need to change them, so what the beta series needs now is not more features from me but people using it on real code and reporting back. Reports of it working, or not working, on something I never thought to test, and of what confused you or what you found missing, are what will decide whether anything changes before a release candidate. They go to the [issue tracker](https://github.com/GrahamDumpleton/wrapture/issues) on GitHub.

One area where feedback would be especially useful is the OpenTelemetry export. The events wrapture records are mapped through to spans, attributes and metrics, and the intent was for that mapping to follow the OpenTelemetry [semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/). As I explained in the introductory post, the code was written by an AI under my direction rather than by me, so I cannot claim to have checked every attribute against the conventions myself, and can only say I hope the information is being mapped through okay. If you spend your days looking at traces in an OpenTelemetry backend and find that what arrives is not named or shaped the way the conventions say it should be, or the way your backend expects, I would like to hear about it while it is still cheap to change.

The companion instrumentation packages have been bumped to 1.0.0b1 at the same time. Until 1.0.0 is final a plain `pip install wrapture` picks up the latest pre-release automatically, so there is no need to pin a specific version to try it.

The links you need are:

  * [wrapture](https://github.com/GrahamDumpleton/wrapture) on GitHub, and the [documentation](https://wrapture.readthedocs.io/) on ReadTheDocs. The [getting started](https://wrapture.readthedocs.io/en/latest/getting-started.html) page is the place to begin, and if you are coming from `unittest.mock` there is a [comparison page](https://wrapture.readthedocs.io/en/latest/coming-from-mock.html) mapping each mock idiom to its wrapture counterpart.
  * [wrapture-instrumentation](https://github.com/GrahamDumpleton/wrapture-instrumentation), the core collection of packaged instrumentation. It covers the web frameworks Flask, Django, FastAPI, Starlette and aiohttp, the servers uvicorn, werkzeug and `wsgiref`, the HTTP clients requests, httpx, urllib3, aiohttp, `urllib.request` and `http.client`, XML-RPC on both ends, gRPC, SQLAlchemy and `sqlite3`, and Jinja2 templates.
  * [wrapture-instrumentation-aws](https://github.com/GrahamDumpleton/wrapture-instrumentation-aws), for the AWS SDK (boto3 and botocore), with every AWS API call recorded as one event.
  * [wrapture-instrumentation-postgresql](https://github.com/GrahamDumpleton/wrapture-instrumentation-postgresql), for the PostgreSQL drivers psycopg, psycopg2 and asyncpg.
  * [wrapture-instrumentation-mysql](https://github.com/GrahamDumpleton/wrapture-instrumentation-mysql), for the MySQL drivers PyMySQL, mysqlclient and aiomysql.

The split between the core collection and the separate packages is that the core package only covers targets which can be exercised in-process, with no backend product or service needed to test against. Anything that needs a real server to test against, which the database and AWS packages do (their test suites run the real thing in a container), lives in a package of its own with its own release cadence. I also plan to have packages for Redis and MongoDB. Beyond that it will depend on what people are interested in seeing instrumentation for, with the only other thing I can see at the moment being the LangChain packages.

## The posts so far

The posts are collected on the [testing and tracing with wrapture](/guides/testing-and-tracing-with-wrapture/) guide page, which is the list that will keep growing, but for the record the reading order is as follows. First the starting point, on what wrapture is, why I built it, and how it was written:

  * [Introducing wrapture.](/posts/2026/08/introducing-wrapture/)

Then the unit testing side, where the difference from `unittest.mock` is that the real code still runs and everything that flows through it is recorded:

  * [Unit testing with wrapture.](/posts/2026/09/unit-testing-with-wrapture/)
  * [Recording calls with wrapture.](/posts/2026/09/recording-calls-with-wrapture/)
  * [Phased behaviour in wrapture.](/posts/2026/09/phased-behaviour-in-wrapture/)
  * [Beyond callables in wrapture.](/posts/2026/09/beyond-callables-in-wrapture/)

And the tracing side, where the same bindings observe a running application instead, from a live call tree in a terminal through to spans in an OpenTelemetry backend:

  * [Live tracing with wrapture.](/posts/2026/09/live-tracing-with-wrapture/)
  * [Zero-code tracing with wrapture.](/posts/2026/09/zero-code-tracing-with-wrapture/)
  * [Tracing Flask with wrapture.](/posts/2026/09/tracing-flask-with-wrapture/)
  * [Finding slow code with wrapture.](/posts/2026/09/finding-slow-code-with-wrapture/)
  * [OpenTelemetry export in wrapture.](/posts/2026/09/opentelemetry-export-in-wrapture/)

## Learning it by doing

Reading about a library only gets you so far, so alongside the posts there is now a [wrapture-workshops](https://github.com/GrahamDumpleton/wrapture-workshops) repository on GitHub containing 24 workshops you can work through to learn wrapture in an interactive workshop format. Each takes one thing you might want to do with wrapture and walks you through doing it in a live JupyterLab session, with the instructions in a side panel whose actions drive the session and check your work as you go. The early workshops track the blog posts, one per post, and the later ones go into areas the posts have not covered yet, such as using wrapture with pytest properly, converting an existing mock based test suite, async code, patching third party libraries, distributed tracing across two processes, and writing an instrumentation package of your own.

You need nothing installed to try them. The workshops can be run in a hosted environment on [mybinder.org](https://mybinder.org/v2/gh/GrahamDumpleton/wrapture-workshops/main?urlpath=lab), a free public service that builds the repository into a temporary JupyterLab running in your browser. Building takes a minute or two. A session is discarded when it ends, so finish a workshop in the session you started it in. If you would rather run them locally, the repository README has the steps for doing that under any JupyterLab.

Each workshop installs wrapture into a virtual environment of its own inside the workshop directory, the way a project would, so nothing is left behind in the JupyterLab environment. The workshops are pinned to a released version of wrapture, so the documentation may at times describe something newer than what a workshop uses.

## Beaten to the punch

My intention was always to write this summary post once the testing and tracing posts were done, but Simon Willison got there first with [Don't sleep on wrapture](https://simonwillison.net/2026/Sep/11/wrapture/), which was his second post on wrapture after [covering the initial announcement](https://simonwillison.net/2026/Aug/31/introducing-wrapture/) back in August. I am not complaining. His reach on social media is a great deal larger than mine, so a lot more people will have seen his summary than would have seen this one, and that has been reflected in the way the number of stars on the GitHub repository jumped after his post went out. The Python Bytes team also featured wrapture on [episode 494 of their podcast](https://www.youtube.com/live/4AUE4ewgN38?t=844), which helped as well. Thanks to all of them.

Either way, this post still serves a purpose, since it is the one place with all the links, the package list and the workshops together, and it will be the post I point people at when they ask where to start.

## A side note on the workshops

I do hope people try the workshops on mybinder, and not only for what they teach about wrapture. I have worked on [Educates](https://educates.dev) for many years as a way of hosting online interactive workshops, and it remains the platform I would reach for when a workshop needs a full Kubernetes-backed environment. Being able to deliver workshops inside JupyterLab, with instructions in a side panel that drive the session and check what you have done, is something completely new which I only wrote in the past week, as a JupyterLab extension called [jupyterlab-workshop](https://github.com/GrahamDumpleton/jupyterlab-workshop). A workshop is nothing more than a directory with a manifest and some Markdown pages, and it runs wherever JupyterLab runs, so mybinder can host it with no container or cluster of my own behind it. I will do some followup posts on that in the coming week or so, since it deserves more than a paragraph at the end of a post about something else.
