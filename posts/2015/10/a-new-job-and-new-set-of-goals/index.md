---
title: "A new job and a new set of goals."
author: "Graham Dumpleton"
date: "Thursday, October 1, 2015"
url: "http://blog.dscpl.com.au/2015/10/a-new-job-and-new-set-of-goals.html"
post_id: "5437480800702130052"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'openshift', 'python', 'red hat']
comments: 0
published_timestamp: "2015-10-01T12:53:00+10:00"
blog_title: "Graham Dumpleton"
---

Okay, it isn’t quite a new job as I have already been there for over two months, but then for most of the past month I was on an extended family holiday which had been organised long before the idea of changing jobs had arisen. Prior to the holiday I had been busy with conferences, training and the general firehouse of new information that comes with a new job. It is only now after I have got back from my holiday that I am finally getting an opportunity to find my feet and work out exactly what I have got myself in to with this new role and what that all means for the future, for work, but also my open source projects and general involvement with the Python community.

So for those who didn’t see me mention it on Twitter closer to when I actually started, or haven’t seen my [post](https://blog.openshift.com/best-breed-python-web-hosting/) about it on the company blog for the product area I am working with, I am now working for Red Hat.

This new job is something completely different for me. In prior jobs I have always been working directly on a product as a developer where everything you did was driven by having to get something out the door, often with ridiculous deadlines that only served to increase ones personal stress levels and anxiety.

At Red Hat, rather than working as a developer, I will instead be working as a developer evangelist for [OpenShift](https://www.openshift.com), Red Hat’s PaaS product.

For those in countries such as Australia where the term ‘evangelist’ can be looked on in a negative way, the role is also often referred to as being a developer advocate. Either way, if you don’t really know what a developer evangelist or advocate is all about, then I recommend having a read of the [Developer Evangelist Handbook](http://developer-evangelism.com) by Chris Heilmann. Steven Pousty, one of the amazing group of people I now get to work with has also given a great talk titled [The Identification and Husbandry of Developer Evangelists](https://www.youtube.com/watch?v=qeAJWrBVLeI) as well which puts the role in perspective against more traditional roles of sales, marketing, product management and software development.

As to how I ended up at Red Hat, that is a long story as it usually is, but in short I have been keeping a very close eye on what they have been doing with OpenShift since they first released it. Although it isn’t the first large scale PaaS out there, that it wasn’t quite as opinionated as others and provided a bit more flexibility in how you can interact with your running web applications, meant I always found it a bit more appealing than other options available. Even so, it still wasn’t compelling and I personally actually used one of the alternatives for a very long time since that is what I first tried.

Things really stepped up a notch with OpenShift 3 though when they announced the intention to completely overhaul it and rather than use the existing Linux container foundation they had been using, adopt Docker as a core component on which the PaaS product is based. The addition of Docker and also Kubernetes for handing container orchestration and scheduling turns OpenShift into an entirely different beast from what it was. In all it makes it a much more flexible deployment environment for web applications as well as other workloads. Not only can you still deploy web applications in the style of a more traditional PaaS via some builder mechanism, you can also run existing Docker images.

The potential of a more modern PaaS which didn’t tie you down to a particular way of doing things I saw as a very powerful springboard to improving deployment of Python web applications in particular. It was with that goal in mind that I specifically sought out a job at Red Hat where I might be able to take all that knowledge I have learned in the past from implementing mod\_wsgi and working with the Python web community over WSGI and the various Python web frameworks, to develop a better story for hosting Python web applications.

That is why and how I ended up at Red Hat, but what does that mean to my own open source work and community involvement?

Well, with Red Hat being an open source company at its core, one can imagine that there is obviously going to be some latitude, more so than in my previous jobs, to continue with my open source work. The synergy between my own projects such as mod\_wsgi and what OpenShift is all about can only contribute to what I can hopefully achieve.

As to what then my current set of goals are for what I now hope to be able to do in the open source space going forward, they are as follows.

  * Continue my work with [mod\_wsgi-express](https://pypi.python.org/pypi/mod_wsgi), an alternative way for installing and running mod\_wsgi which is more suited for modern container based deployments such as Docker.
  * Update the mod\_wsgi documentation, which hasn’t kept pace with all the changes made in mod\_wsgi over the years and which has become stale and hard to navigate.
  * Work on a new project I have been toying with for some years which provides a uniform way of deploying a Python web application regardless of what WSGI server is used and what hosting service may be used. The goal here being to abstract out common requirements around deployment so as to make Python web application portability across different hosting services and web servers more achievable and avoiding vendor lock in.
  * Add in capabilities to mod\_wsgi related to monitoring of the performance of Python web applications and more specifically the performance of the underlying web server, to facilitate better tuning of the web server so as to make best use of available resources and so save money on hosting services.
  * With the new builtin ASYNC features of Python 3.5, revisit the whole idea of a WSGI like interface for ASYNC web servers. This would also look at the impacts of HTTP/2 and WebSockets on the Python web space.
  * Wade more into the commentary and discussions going on around developer burnout and self care, plus the related issues of funding of open source related work.



As far as communicating about my personal projects, I expect this blog to be the main avenue through which I will talk about them. I will still be aiming to get to key conferences, especially those related to Python, and part of my role at Red Hat requires me to do exactly that.

What talks are acceptable at Python conferences has changed over the years though, with a move away from more hard core technical talks to ones which are of broader interest and more entertaining than anything else. This is something I need to adjust to as far as what talks I submit for conferences. As a result, I will instead be aiming to make use of screen casts to talk about more technical topics and host them up on YouTube or elsewhere instead.

Now I know I have traditionally worked on projects, which although people were happy to use, were in a space or used technologies which didn’t attract other developers. As a result, all my open source projects are solo efforts. If however any one does have an interest on working on any of the projects, or even if you just want to discuss them, do track me down and we can talk. At the least, if you think that these are things you want to use and so want to provide encouragement to keep me going, you can always drop me a message on Twitter so I know there is interest.