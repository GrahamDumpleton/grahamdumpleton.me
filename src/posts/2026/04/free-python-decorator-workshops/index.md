---
title: "Free Python decorator workshops"
description: "Free interactive workshops on Python decorators hosted on the Educates training platform."
date: 2026-04-02
tags: ["python", "educates", "decorators"]
draft: false
---

I've been working on a set of interactive workshops on Python decorators and they are now available for free on the [labs](/labs/) page of this site. There are 22 workshops in total, covering everything from the fundamentals of how decorators work through to advanced topics like the descriptor protocol, async decorators and metaclasses. The workshops are hosted on the [Educates](https://educates.dev) training platform and accessed through the browser, so there is nothing to install.

## An experiment in learning

We are well into the age of AI at this point. Need to know how to write a decorator in Python? Just ask ChatGPT or Claude and you will get an answer in seconds. Want to refactor some code to use decorators? Let an AI agent do it for you. The tools are genuinely impressive and I use them myself every day.

That said, as someone who spent years as a developer advocate helping people learn, the question that keeps coming up is whether there is still an appetite for actually learning how things work. Not just getting an answer, but understanding why the answer is what it is. Understanding the mechanics well enough that when the AI gives you something subtly wrong (and it will), you can spot it and fix it yourself.

These workshops are my experiment in finding out. If people are still interested in sitting down with a guided, hands-on environment and working through a topic step by step, then this format has a future. If not, it will at least help me work out whether developer advocacy even matters anymore, and whether the years I have put into building the [Educates](https://educates.dev) platform have been worth the effort.

## What the workshops cover

The Python Decorators course starts from the ground up. The early workshops cover functions as first-class objects, closures, and the basic mechanics of how decorators work. From there the core path builds through decorator arguments, `functools.wraps`, stacking decorators, and class-based decorators.

Branching off from the core path are a set of elective workshops covering practical applications: input validation, caching and memoisation, access control, registration and plugin patterns, exception handling, deprecation warnings, and profiling. These are the kinds of things you would actually use decorators for in real projects.

The later workshops go deeper into territory that most tutorials skip over entirely. The descriptor protocol, how decorators interact with classes and inheritance, async decorators, class decoration, and metaclasses.

The aim here is to go well beyond the basics. There are plenty of introductory decorator tutorials out there already. What I wanted to create was something for people who want to genuinely broaden their Python knowledge and understand how the language works at a deeper level. If you have not completely given in to letting AI do all the thinking for you and still want to build real expertise, these workshops are for you.

If you have never experienced interactive online workshops like this before, I would recommend doing the Educates Walkthrough workshop first. It will get you familiar with how the platform works, how to navigate the workshop instructions, and how to use the integrated terminal and editor, before you jump into the Python content.

## Keeping the workshops running

The system hosting the workshops has limited resources and capacity. I am running this on modest infrastructure and I am honestly not sure how long I will be able to keep it going. It depends in part on how much interest there is, and in part on whether I can sustain any hosting costs.

The system is also engineered to only let a limited number of people in at a time, so if you get a message about being at capacity, try again later. I will be monitoring how things hold up and if possible will increase the limits.

If you try the workshops and find them useful, it would mean a lot if you considered helping out through my [GitHub Sponsors](https://github.com/sponsors/GrahamDumpleton) page. Even small contributions add up and would help keep the workshops available. If there is enough interest and support, I could move to a more capable hosting environment and handle more concurrent users. Right now capacity is limited and I am just seeing how things go.

## What comes next

If things go well and there is demand for more, I have plans for additional workshop courses. The natural successor to the Python decorators course would be one built around my [wrapt](https://github.com/GrahamDumpleton/wrapt) library, covering both its decorator utilities and its monkey patching features. After that I would look at WSGI and Python web hosting, which is another area where I have deep experience from years of working on [mod_wsgi](https://github.com/GrahamDumpleton/mod_wsgi).

The common thread is topics that go into real depth. There is no shortage of surface-level content on the internet (and AI can generate more of it on demand). What I think is harder to find is material that takes a topic seriously, works through the edge cases, and gives you a genuine understanding of what is happening under the hood. That is what I am trying to provide.

## A note on how these were made

I should be transparent about this: the workshops were created with the assistance of AI. I wrote about the process in some detail back in February, covering [the approach to using AI for content](/posts/2026/02/when-ai-content-isnt-slop/), [how I taught an AI about the Educates platform](/posts/2026/02/teaching-an-ai-about-educates/), and [how I used AI to review the workshops](/posts/2026/02/reviewing-workshops-with-ai/).

I realise there is a certain irony in using AI to create workshops that are partly motivated by the belief that people should still learn things themselves. But I see a difference between using AI as a tool to help produce quality educational content and blindly publishing whatever an AI generates. Every workshop has been reviewed, tested, and refined based on my own knowledge and experience with Python decorators going back over a decade. Hopefully the result is something genuinely useful rather than AI slop. And hopefully the use of the Educates platform itself contributes to the experience, letting people focus on actually learning rather than spending time trying to get their own computer environment set up correctly. I hope people will judge the workshops on their quality rather than dismissing them because AI was involved in making them.

Head over to the [labs](/labs/) page to get started. I would love to hear what you think.
