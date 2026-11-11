---
title: "AI as a lifestyle choice"
description: "What building software with AI looks like as I edge towards retirement, why all software starts out as mud, and why I would like to hear what you never had time to build."
date: 2026-11-11
tags: ["ai", "muru", "python"]
---

When I wrote about [twenty years of mod_wsgi](/posts/2026/11/twenty-years-of-mod-wsgi/), I mentioned that I was on sabbatical, that AI coding tools had changed what I was prepared to take on, and that I was hoping people would tell me what they think is missing from the current options for hosting Python web applications. Each of those only got a sentence or two in a post which was mostly about Apache, and I want to expand on them here.

I should start by clarifying my situation, or at least try to. I would like to call it retirement. My better half would like to see me still working. Nothing is official either way, and negotiations continue. Some people in my position would buy a caravan and head off around Australia, but I already travelled the outback a lot when I was much younger. What I seem to have chosen to do instead is spend my days building software with AI, and I am having about as much fun creating software as I have ever had.

## What the lifestyle looks like

It is only a month since I decided I would start on Muru. There were a few days of planning and thinking before any code got written, and since then I have been working on it seven days a week, days and evenings. Nobody is making me do this. I can't remember the last time something was engaging, fulfilling and fun all at the same time.

Before that sounds too alarming, it doesn't mean I am chained to a desk. AI coding tools have turned out to fit quite well around the rest of life. I can set something going, then head out for a walk, do some gardening, or deal with whatever else needs doing around the house, and come back to see how it went. When I was writing all the code myself, stepping away meant the work stopped. My better half may even be prepared to count that in my favour during the negotiations.

That is what I mean by a lifestyle choice. I said in that earlier post that the coding is the part I find a chore these days, which might seem odd coming from someone who has never really stopped creating software. The making of things was always the point though, not the typing. AI gets rid of the grunt work that can be so frustrating, and leaves me with the ideas and the satisfaction of seeing them work.

## Getting away from the meter

It took me a while to realise how much the price of these tools was affecting how I used them. When I was paying $20 a month I was always worried I would run out, and as a result I actually held back from relying on it. Moving up to $200 a month produced the opposite problem. Paying that much, I felt I had to make the most of it, and so would end up using it for a crazy number of hours just to get my money's worth. Neither is a great way to go about something you are meant to be doing for fun.

Right now I don't have that problem, because I have been accepted into the Claude for Open Source Program for a second round. I very much appreciate that, and it has made a huge difference. More than anything it has released me from worrying about the cost, and I feel free to do whatever I want without feeling constrained.

Obviously there is the question of what happens when I go back to having to pay for it, and I don't have a good answer to that yet. For now I am taking as much advantage of it as I can.

## Everything starts out as mud

I will acknowledge that AI may not always generate the best code out of the box. To be frank though, neither did I when I started on mod_wsgi. The early versions had plenty wrong with them. I made lots of mistakes and had to go back and do things differently, and it took years of fixing and rethinking to get it to where it is now.

All developers are like this when they start out on something. People seem to forget that as soon as AI is involved, and expect instant perfection of a kind they would never have been able to achieve themselves.

Writing software is an incremental process of improvement, and in some respects can be likened to making a dorodango. This is a Japanese craft where you take ordinary dirt and water and form it into a ball. It starts out as a crude lump of mud. You shape it, let it dry, add layers of fine dust and keep working at the surface, over and over, until you end up with a sphere with a shine on it that looks nothing like what it was made from.

I [wrote recently](/posts/2026/10/ai-slop-is-the-new-tldr/) about how calling something "AI slop" is often just a way of saying you didn't read it. Well, slop is more or less what a dorodango starts out as. The insult only sticks if you stop there. The AI may be doing a lot of the work on the surface, but deciding what isn't good enough yet is still down to me, and twenty years of getting things wrong with mod_wsgi turns out to be useful for that. I am prepared to put in the hard work to keep polishing Muru until it is something I would trust, and something you would too.

## Tinkering in the back room

I have been programming for over 40 years now, and have been involved in free or open source software for nearly all of that time. Even as I head towards retirement, or whatever we end up calling it, I still want to do more. The Python community has always been the most welcoming community I have ever interacted with, and Muru is my way of giving something back to it.

There are many ways of contributing to a community like that. A lot of people give their time to the PSF and to running Python conferences, and we are all better off for the work they do. It just wouldn't suit me, as bureaucracy and organising things are not where my strengths lie. Back room tinkering and creating software has always been my thing, and I expect always will be.

I also know how badly AI written code being handed to open source projects can go, with maintainers left to deal with what lands on them. The difference here, I hope, is that I am not throwing anything over the fence for someone else to look after. If Muru has problems, they are my problems.

## The things you never had time to build

I know how a month old project written largely by AI sounds. Muru is not a weekend of vibe coding that will be forgotten about by Christmas though. The code may be new, but the thinking behind it has been accumulating for twenty years. Muru is my thing for the foreseeable future, and I intend to commit to it and see how far I can take it.

I am not doing this only to see what I can achieve based on my own ideas. Part of the reason for putting it out there is so people can see those ideas and come back with their own, about what they would like to see in a system for hosting Python web applications.

A few people have already left comments on my social media posts about the series, showing an interest in specific things Muru is doing. That has been encouraging, and suggests I am at least on the right track. I would like a lot more of that feedback though, especially about what isn't there yet.

If you work with Python web applications for a living, I suspect you have a list. There will be points of friction in your day to day development work that you would love to see gone. There will be things you need to do in production which are much harder than they should be. Some of it you have wanted to fix for years, but you never had the time, or your employer wasn't interested. I know that list well, as I had one of my own for most of my working life.

That is where my situation is now different. Not having a job, I have the time. Open source has always said "patches welcome", which isn't much use when lack of time is the whole problem. So don't send me a patch, just describe the problem.

If you aren't sure where to start, think about the scripts you have written around your deployments that you wish you didn't need, or the thing you end up explaining to every new person who joins the team. Maybe there is something that keeps getting pushed down the backlog, or a production task you put off because of how painful it is. I can't promise everything will make it in, as an idea needs to fit within the overall system I am trying to develop, but if it does then I am happy to look at it.

In that earlier post I said I wasn't going to point to where Muru lives just yet. It is time to change that. To see what Muru can already do, which is a lot more than the posts so far have covered, have a look through the [documentation](https://docs.muruhq.dev/). The place to tell me what you would like to see is the [ideas section of the Muru discussions on GitHub](https://github.com/muruhq/muru/discussions/categories/ideas). I am not a huge fan of online discussion forums like this, but there don't seem to be any other good choices these days. If they aren't your thing either, then just leave a comment on one of my social media posts when something sounds like it is what you would use or need. Even that much helps me work out where to put the effort.

## Polishing in public

You will have to put up with me posting about Muru every day for a while yet. Sorry about that. The posts are actually part of the polishing process, as are the online interactive workshops I have been creating for it using the [workshop extension I wrote for JupyterLab](/posts/2026/09/introducing-jupyterlab-workshop/). If I can't write a post which explains something easily, or create a workshop which makes it usable for the people who may want to use it, then its design and implementation were bad to start with. Having to explain it is what shows me where it needs more work.

The ball is still pretty muddy in places. I have the time though, I am having fun, and whatever my better half and I end up deciding to call this, I plan to keep polishing. Fingers crossed it ends up with a shine.
