---
title: "Managing the developer experience using docker."
author: "Graham Dumpleton"
date: "Friday, November 28, 2014"
url: "http://blog.dscpl.com.au/2014/11/managing-developer-experience-using.html"
post_id: "6130844825565408844"
blog_id: "2363643920942057324"
tags: ['docker', 'python']
comments: 0
published_timestamp: "2014-11-28T23:11:00+11:00"
blog_title: "Graham Dumpleton"
---

I have always found hosting Python web applications using a PaaS an exercise in frustration. The problem is that they aren't generally about providing options and flexibility. Instead they are about pigeonholing you in to working in one particular way and often with quite specific technologies they control. If you want to use something different you are usually out of luck, that or they make it so painful that it isn't worth the trouble.

Sometimes you even have to question whether the people who built the services even understand what the options are that were available, or whether they have let their own personal biases dictate what technologies you can use.

For that reason I believe docker has a lot going for it. Specifically, that as a developer one can now more readily choose the technologies you wish to work with. Which hosting service you may choose to use is now more likely going to come down to how well their service orchestration works, the general quality of their service and the price of the service, rather than whether you can use a specific technology to run the actual Python web application.

From the perspective of being a third party provider of a specific way to run Python web applications, I also see lots of benefits in the docker way of doing things.

This is because I can provide an appliance like image for running a Python web application which incorporates best practices as far as the tools used and how it is configured. I can do this without being subject to the whims of the PaaS provider and any artificial gating mechanism they may impose which restricts me from providing a solution which a developer can choose to use.

I am also no longer reliant on a developer actually going to the effort of having to work out for themselves the best way to set up and configure a solution. This is because with how docker images work, I can provide an out of the box experience which is going to be a lot better than what a developer may have been able to achieve with their own limited knowledge of the best way to set things up.

In some respects what it means is that I am able to better manage or control the developer experience in running a specific solution.

Because I can provide a superior prepackaged solution, you don't end up with the situation as it occurs now, where the issues the developers encounters in setting it up are of their own making and not that of the tool being used, yet they quite readily go off and blame the tools rather than their own lack of expertise in being able to set it up properly.

The root problem here is that developers these days are after quick solutions because they simply don't have the time to work out how to use something properly. They also have a tendency though to go off and bad mouth a solution when in their rush to get something working they do have some issue. Developers are also like sheep and will readily believe what others say, even though it can be totally wrong, and will then themselves tell everyone else the same thing even though they are woefully ignorant of what is reality.

This mindless heard like mentality is why we go through these cycles of some tool being seen as the new 'cool' thing. There is generally nothing wrong with the old tools if used properly, but the misinformation that gets out there generates a life of its own and so in the end can doom a particular solution even though it still may be just as capable as the new comer.

Docker and how it works therefore opens up this dream scenario for a provider of a solution whereby they can choose what technologies they want to use, bundling it up in a way that they can also control how it is used, but in doing so provide a superior experience for the developer who uses it.

The analogy here is any products from Apple. Sure you will get that percentage who rile against it because they feel it is locked down and they don't like that they loose some measure of control, but for the majority who don't care, they simply judge it on its merits as far as it gets the job done with a minimal amount of effort. So the provider is able to provide a better product and the end user developer is also happier.