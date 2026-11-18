---
title: "Hosting Python web applications with Muru."
description: "Posts on Muru, a system for hosting Python web applications from a laptop through to production. Where it came from, what it does in development mode, and how it is put together."
tags: ["python", "muru", "wsgi"]
draft: false
---

Posts on Muru, the system I am building for hosting Python web applications from a laptop through to production, are as follows. The series is still being written, so this list will grow as more posts go out. The earlier work it grew out of is collected under [deploying with mod_wsgi](/guides/deploying-with-mod-wsgi/).

The starting point, on where Muru came from and what I want it to be:

  * [Twenty years of mod_wsgi, and what comes next.](/posts/2026/11/twenty-years-of-mod-wsgi/)

This batch of posts shows Muru running in development mode, from serving a first application through to finding out what the workers are doing when a request is slow:

  * [A first look at Muru.](/posts/2026/11/a-first-look-at-muru/)
  * [Muru: looking inside the workers.](/posts/2026/11/muru-looking-inside-the-workers/)

This batch of posts steps back to explain how Muru is put together, from the processes involved and the path a request takes through them, to how an application is imported once and has its workers forked from it:

  * [Muru: how it fits together.](/posts/2026/11/muru-how-it-fits-together/)
  * [Muru: import once, fork many.](/posts/2026/11/muru-import-once-fork-many/)

This batch of posts moves on to specific features of Muru, starting with serving HTTPS during development so it can be tested without a proxy in front, and then mixing WSGI and ASGI in the one application so an existing WSGI application can add websockets:

  * [Muru: HTTPS in development.](/posts/2026/11/muru-https-in-development/)
  * [Muru: WSGI and ASGI together.](/posts/2026/11/muru-wsgi-and-asgi-together/)

This batch of posts moves on to the Muru daemon, for deploying to a server, starting with how each deploy is a release of its own, started beside the one serving and kept warm afterwards, so that rolling back is a routing change, and then canary releases, where a new release is given a share of the traffic and is rolled back by itself if it does worse than the release already serving:

  * [Muru: releases, not restarts.](/posts/2026/11/muru-releases-not-restarts/)
  * [Muru: canaries without a service mesh.](/posts/2026/11/muru-canaries-without-a-service-mesh/)

This batch of posts covers running Muru in a container, where `muructl serve` serves the single application held in the image and concentrates on being a good main process for the container, and then on Kubernetes, where it fits in with what the platform already provides rather than duplicating it:

  * [Muru: a better tenant in a container.](/posts/2026/11/muru-a-better-tenant-in-a-container/)
  * [Muru: working with Kubernetes, not around it.](/posts/2026/11/muru-working-with-kubernetes-not-around-it/)

This batch of posts goes back to the Muru daemon to look at scaling, starting with how it decides how many workers a release needs, and when what the workers report says the answer is a change to the release rather than more workers, and then how an idle release is taken down to no workers, or no processes at all, and what the next request pays for it:

  * [Muru: scaling from what the workers report.](/posts/2026/11/muru-scaling-from-what-the-workers-report/)
  * [Muru: scaling to zero.](/posts/2026/11/muru-scaling-to-zero/)

This batch of posts covers overlays, the temporary changes the Muru daemon lays over a site's configuration and takes away again afterwards, starting with those turned on by hand or on a schedule, for backups, maintenance windows, timed cutovers and known busy periods:

  * [Muru: overlays on a schedule.](/posts/2026/11/muru-overlays-on-a-schedule/)
