---
title: "Where Muru is up to, and when to expect a release"
description: "An update on Muru: the core features are done, dogfooding starts with a proof of concept hosting app, and a rough timeline for a 0.1.0 release and a 1.0.0 for production."
date: 2026-11-24
tags: ["python", "muru", "mod_wsgi"]
draft: true
---

The posts in this series so far have worked through the main features of Muru, from development mode, to the daemon, containers and Kubernetes, scaling, and working with coding agents. This time I want to step back from the features and talk about where the project as a whole is up to, and when there might be a release you could seriously consider using.

The goal for Muru is the same as when I wrote about [twenty years of mod_wsgi](/posts/2026/11/twenty-years-of-mod-wsgi/). I want a better way of hosting Python web applications, one that carries you from local development right through to production, and which draws on everything I have learnt since I started on mod_wsgi.

## Where Muru is up to

Most of the core features I set out to build are now done, and many of them have had a post of their own in this series. That isn't to say I have run out of things to do, as the TODO list is still far from short. What is changing is what I spend my time on next.

From what I have seen so far, the core functionality holds up well for typical use cases. Where Muru will inevitably fall over is in the corner cases. These are the combinations of settings, applications and environments I haven't thought of, or which only show up once Muru is used for something real, rather than the examples I write to test it.

## Dogfooding with a hosting app

The best way I know of to find those corner cases is to use Muru myself, on something more substantial than an example. So instead of continuing to add features, I have started dogfooding Muru by writing [muru-hosting](https://github.com/muruhq/muru-hosting), a web application for managing a set of Python web sites hosted with Muru.

The idea is a control plane running on Kubernetes, with each site in a pod of its own under the Muru daemon, and new versions deployed from GitHub as Muru releases. People sign in with their GitHub account, and look after the sites they have access to either through a web interface, or through their own AI assistant over MCP, which picks up from where the post on working with coding agents left off.

To give it some concrete requirements, I have three uses in mind. The first is a person or team managing their own set of deployed applications. The second is a small hosting service for other people's sites. The third is a university course, where each student hosts an application of their own and the course's staff can see all of them.

The control plane is itself a Django application, served by Muru, so Muru gets exercised from both sides, hosting the application while also being driven by it. Django will mostly be running as a WSGI application, but where it needs async capabilities or WebSockets, those parts will run as ASGI in the same application process, as described in the [WSGI and ASGI together](/posts/2026/11/muru-wsgi-and-asgi-together/) post. In part that is to show that a Python web application doesn't have to pick between WSGI and ASGI, and can be a mix of both.

Everything the control plane does to a site goes through Muru's admin API. Where that API falls short of what a hosting service needs, the gap gets raised as an issue against Muru and fixed there.

I do want to be clear about the purpose of muru-hosting. It exists to dogfood Muru and act as a proof of concept, and it is not a product. There is no guarantee it will ever be something you can use yourself, and you shouldn't rely on it to host anything that matters. Whether it grows into more than that, we will see.

## When to expect a release

I am thinking of an official release of Muru as happening in two steps.

The first will be version 0.1.0. This will be a release you could use for local development and testing, or simply to experiment with and learn what Muru can do. It isn't intended for production use. I am hoping to have it out by the end of the year, but that depends a lot on how many problems muru-hosting turns up, whether in Muru itself or in the workflow for using it.

Version 1.0.0 will follow later, and will be the release I feel is good enough for production. Being cautious, I am aiming for around the end of March next year, which happens to be close to twenty years after mod_wsgi 1.0.0 was released. The actual date will come down to gut feel, based on how the proof of concept works out, and just as much on feedback from people who try Muru.

That last part matters. If nobody tells me Muru is working for them, I will be inclined to hold back 1.0.0 even longer, bug reports or not. An empty issue tracker means little if nobody is using the software. So when 0.1.0 does come out, I really hope people will give it a go.

## Trying it now

If you are one of the braver souls who wants to try Muru before 0.1.0, I am not going to stop you. Should you run into problems, I am happy to help you work through them so they can be fixed, and that includes jumping on a video call to talk through what you are trying to do.

I really do want to see Muru succeed. If all I hear is crickets though, it will be hard to tell whether anyone is interested in it, let alone whether it works.

## Where to find it

Muru is on PyPI, where `muructl` is the main package you need to know about. The documentation is at [docs.muruhq.dev](https://docs.muruhq.dev), and the source code is on GitHub at [muruhq/muru](https://github.com/muruhq/muru).

You will notice the repository isn't under my personal GitHub account. I have set up a separate organisation for it, as I think Muru could become significant enough that it deserves a home of its own, rather than being one more of my personal projects.

I have also moved [wrapture](https://github.com/muruhq/wrapture) and [unwrapt](https://github.com/muruhq/unwrapt), which I created earlier this year, into the same organisation. The features Muru has for tracing a web application, and for seeing what it is doing so you can fix or improve it, are built on them, so it made sense for them to live alongside Muru.

## What's next

Expect the posts to become less frequent from here. I may still write about some of Muru's features where one deserves it, but depending on how things go, I might instead talk about the ideas I have for muru-hosting, and what building it teaches me about Muru. Either way, if you do try Muru, I would love to hear how you get on.
