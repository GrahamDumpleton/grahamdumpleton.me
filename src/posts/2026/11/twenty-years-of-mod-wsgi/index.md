---
title: "Twenty years of mod_wsgi, and what comes next"
description: "Twenty years on from starting mod_wsgi, I am revisiting Python web hosting without the constraints of Apache. This is where Muru comes from and where it is going."
date: 2026-11-04
tags: ["python", "mod_wsgi", "muru", "ai"]
---

Twenty years ago, around this time, the idea for mod_wsgi was taking shape in my head. The coding started in December 2006. I had no idea back then that it would end up being something I would still be maintaining two decades later, or that it would become the thing many people in the Python community know me for.

People tend to either love mod_wsgi or hate it. Those who love it value that it is solid and has been around forever, and that it just keeps running once you have it set up. Those who hate it usually aren't really complaining about mod_wsgi itself, but about Apache httpd. Configuring Apache was never anyone's idea of fun, and mod_wsgi inherits all of that baggage simply by being an Apache module.

## Why Apache in the first place

It is easy to forget what the landscape looked like back then. The WSGI specification existed, but there was no standard, well trodden way of hosting a WSGI application in production. The options were things like CGI, FastCGI or SCGI bridges, or mod_python, which wasn't built around WSGI and came with its own set of problems. Nginx wasn't on the radar of most people outside of Russia, and Python WSGI servers like gunicorn were still years away.

What did exist was Apache, and it was everywhere. Pretty much any hosting environment you could get your hands on had Apache installed. Building on top of Apache meant that mod_wsgi could provide a standardised way of hosting Python web applications on infrastructure people already had, and that is the hole it ended up filling.

## Living within Apache's rules

The catch is that Apache httpd is even older than mod_wsgi, and its architecture was never designed with something like mod_wsgi in mind. This is particularly the case with daemon mode, where the Python web application runs in separate processes from the Apache worker processes handling incoming requests.

Apache owns the lifecycle of all its child processes. The daemon processes mod_wsgi uses are created by the Apache parent process, and so are bound by how Apache decides to start, stop and restart processes. The number of daemon processes is fixed by the configuration, and changing anything means restarting Apache. If you wanted a process manager that could make smarter decisions about the Python application, such as scaling the number of processes up or down based on load, or rolling out a new version of the application without disrupting requests in flight, you were fighting Apache to do it.

So mod_wsgi did the best it could within those constraints. Over the years there was a long list of things I would have loved to add, but which were never going to be practical while sitting inside Apache. Some of them I tried to approximate, others I simply had to let go.

## Why revisit this now

Being on sabbatical, and with full retirement looking more likely, I have the time to come back to the problem and think about how I would do it if I wasn't bound by Apache.

To be frank though, if I had to sit down and write such a system from scratch myself, I wouldn't even try. The scale of what is involved is large, and the coding is the part I find a chore these days. What makes the difference is AI coding tools. They have become good enough at taking an idea and turning it into a working implementation that the coding is no longer my problem. Instead I get to focus on the parts I actually enjoy, which is the architecture, the design, and working out which features are worth having and how they should behave.

Working at that level has turned out to be a lot of fun. I can go from an idea to seeing it work far quicker than I ever could before, and that gratification of seeing an idea come to life is, I suspect, what most of us got into this for in the first place.

## So what is Muru

With the free time to think the problem through properly, and AI tools able to take on the heavy lifting of writing the code, I decided to embark on creating a new and more modern system for hosting Python web applications. That system is called Muru.

Muru isn't an Apache module, and it isn't just another WSGI server to run behind something else. The aim is to take everything I learned from twenty years of mod_wsgi, and from watching how people actually deploy Python web applications, and build something that covers the whole job of running a Python web application, from your laptop through to production.

Despite where it comes from, Muru isn't limited to WSGI either. It can also host ASGI applications, as well as gRPC services. More than that, these can be mixed together in the one application, rather than needing to be run as separate deployments. Extensions are available to hand off requests from WSGI to ASGI and vice versa, which makes it easy to bring things like websockets to an existing WSGI application without having to rewrite it.

Beyond what it can host, part of what Muru sets out to do is simply bring in good practice. There are a lot of things that every production deployment needs, but which are left as an exercise for the user to get right. Things like how a new version of an application gets rolled out, how requests get routed to it, how it reports whether it is healthy, and how it restarts without dropping requests. Most people end up reinventing these badly, or not doing them at all. Muru tries to make them the default rather than something you have to bolt on.

The other part, and the bit I think makes Muru different, is that it is built with an intimate knowledge of what Python web applications need. A generic process manager or container platform treats your application as a black box. It can see whether the process is running and how much CPU and memory it is using, but not much more. Python web applications have their own quirks though, whether that is the GIL and how it shapes the choice between processes and threads, how long an application can take to import and become ready, or how memory use can creep up over time. Muru is designed around those realities rather than ignoring them.

That knowledge also extends to metrics. A Python web application can tell you a lot about how it is coping, such as how busy its request handler threads are, how long requests are waiting before being handled, and whether a process is getting into trouble. The idea with Muru is that these aren't just numbers to put on a dashboard after the fact, but signals that feed back into how the application is hosted, driving decisions about capacity, process management and routing.

Muru is still very much in development. I am not going to point to where it lives just yet. If you go looking and find it, that is fine, but at this stage I would rather it was only people with a real need for something like it who were poking at it.

## Where these posts are heading

Rather than try and describe everything in one go, I intend to write a series of posts working through what Muru can do. Part of the reason for doing this is to get my own ideas out there about what hosting a Python web application should involve. I am also hoping it might prompt others to share what they think is missing from the current options, because hearing about the problems other people are running into would help me work out where Muru should go next.

As for what the posts will cover, I plan to start with local development, since the same tool you use to host the application in production is also there to help while you are developing it. From there I will look at deploying to a host or virtual machine, including how Muru manages deployments of new versions and handles routing of requests. Further along there is running Muru in containers and on Kubernetes, and all the bits those platforms need from an application for it to behave well, such as health probes, metrics, and draining requests on shutdown.

## A word about AI

As has become usual for me of late, a small disclaimer. Muru is being built with heavy use of AI coding tools. I am the one deciding what it should do and how it should be structured, and I am reviewing and steering the result, but most of the code was written by an AI.

I know some people are firmly opposed to AI-written software, and I am not going to argue with that position. If AI involvement rules Muru out for you, then Muru is not for you, and that is okay.

## What comes next

Twenty years is a long time to have been working on the one problem, and it seems I am still not done with it. I am not abandoning mod_wsgi, but Muru is my chance to finally build the things I always wanted to and never could. Fingers crossed it turns out to be as useful to others as I hope it will be.
