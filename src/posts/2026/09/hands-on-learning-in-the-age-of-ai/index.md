---
title: "Hands-on learning in the age of AI"
description: "A summary of my PyCon AU 2026 talk on whether developer workshops still matter when anyone can ask an AI, and why I released 24 wrapture workshops anyway."
date: 2026-09-14
tags: ["pycon", "educates", "wrapture"]
draft: false
---

At PyCon AU 2026 I gave a talk in the DevRel track titled "Hands-on learning in the age of AI", with the subtitle "Are developer workshops still relevant?". The [video](https://www.youtube.com/watch?v=jsHTcAAVta8) is now up on YouTube if you want to watch it. What follows is the main points I was trying to make, along with something the talk didn't cover.

That something is that a couple of weeks or so after giving the talk, I released [24 free workshops for wrapture](/posts/2026/09/trying-out-wrapture/) which anyone can run in their browser. If you watch the talk you will notice I spent the last part of it explaining why that sort of workshop is the kind most under threat from AI. I don't think the two are in conflict in this case, but it takes some explaining, so I will get to it at the end.

For most of the time I have worked on mod_wsgi and wrapt, the bulk of my effort didn't go into writing code. It went into answering the same questions over and over on mailing lists, Stack Overflow and GitHub issues. Every one of those now gets answered in seconds by an AI, and a lot of the answers it gives are probably mine, since it has read everything I ever wrote. The loss of that contact with the people using what you build is a separate topic though, and not what the talk was about. I touched on it in [Developer Advocacy in 2026](/posts/2026/02/developer-advocacy-in-2026/).

## Where AI does a better job

Before making any case for workshops, I wanted to be straight about the things AI simply does better than we do, because some of us are still putting effort into content where our time would be better spent elsewhere.

The tutorial that walks you through configuring something, the getting-started guide, the blog post that takes you through a setup step by step. I don't think we should be writing those any more. An AI will give you the version for the release you are actually running, on your operating system, in the context of your own project, at two in the morning when there is nobody around to ask. Reference documentation still needs to exist, as that is what the AI learned from, but the walkthrough where the reader is a passive observer is done.

The thing is, explaining something clearly was never the hard part. Think about the last tutorial you read that was genuinely well written. Did you come away able to do it, or just confident that you could? Unless you sat down and worked through it, probably the second. Getting someone to actually do the thing, keeping them going when it breaks, and knowing which bit will confuse them before it does, that was always the hard part. AI has got dramatically better at the explaining, but that was the half we had already worked out.

## Why doing is different from reading

So what does the doing actually give you? I argued three things, and that all three get more valuable as AI gets better, not less.

The first is that being wrong has to cost something. In a chat window, being wrong costs nothing. You ask, you get an answer, you nod, you move on, and half the time you never find out you were wrong at all. In a live environment, wrong means something is broken, and when something is broken you have to work out why, which means understanding what you actually did. Nobody gets paid to know the right answer. They get paid to work out why the thing in front of them isn't working, and you can't practise that by reading.

The second is that the struggle is the part that works. Think about something you genuinely know well, as opposed to something you have read about. My guess is you learned it because something went wrong and you had to sort it out. Nobody remembers the explanation that made sense at the time, but everybody remembers the bug that cost them a day. This is where it gets awkward, because an AI assistant exists to remove exactly that friction. That is the right thing when you are trying to get work done and the wrong thing when you are trying to learn, so the better these tools get at their job, the worse they are at teaching you anything.

The third is that you can't ask about what you don't know exists. An AI answers the question you asked, but it has no way of telling you about the thing you never thought to ask. Ask how to deploy your web application and you will get a good answer. What you won't get is a warning that your application isn't thread safe, because you didn't ask, and you had no reason to think you needed to. You find out in production six months later. In a workshop somebody else picked the steps, so you end up in front of the problem you would never have gone looking for.

## Where the work actually is

That is the case for a workshop, meaning something people do rather than read. The catch is that plenty of people won't finish it, and when they don't, it is usually not the tooling that lost them.

People give up on workshops for four reasons. One is the environment. Something didn't install, the versions don't match, and twenty minutes in they have had enough. The other three are all content. The steps are too big a jump, they are told what to type but never why, or there is no way to tell whether what they just did actually worked. The environment problem can be solved with tooling. The other three, no platform will fix for you.

Step size is the one you can't feel, because you already know the answer. Write a step that says "now put it behind nginx" and to you that is one thing. For the person doing the workshop it is four. Install it, write a config file, work out why every redirect is coming back as http instead of https, and discover that `X-Forwarded-Proto` exists, which nobody has ever told them about. That step looked reasonable when you wrote it and it looks reasonable now. The only way you find out is by watching somebody try it. It goes the other way too. If every step is trivial, people stop reading them, and when a step actually matters they have already learned not to pay attention.

How much to tell them is the second. Write "run this exact command" and they will run it, it will work, and they will learn nothing, because they were typing rather than thinking. Write "now configure the server for production" and you have lost everyone who doesn't already know what that means, which is everyone, or they wouldn't be doing your workshop. What works is in between. Give them the command, let it work, then ask them to change one thing and say what they think will happen. Start the server with four workers. Now set it to one worker, send two requests at the same time, and before you run it, what do you reckon happens? That question is the whole trick. If they are wrong they find out in about two seconds, and now they actually understand what a worker is, which no amount of me explaining would have achieved.

Verification is the third, and the one people underestimate. Picture someone on step three. They edit a config file and make a small typo. Everything still starts, nothing looks wrong, and they keep going. At step eight the login flow fails for no obvious reason. They didn't quit at step three when they made the mistake. They quit at step eight, when they can't work out what is wrong and have no way to go back and find it. The part that should bother you is that they don't conclude they made a typo. They conclude your workshop is broken. So after anything that could silently go wrong, have them verify it worked before they move on, and show them what the output should look like. It is not much work, and it is the difference between finishing and giving up.

All three of these are doing the same job. When a workshop is working there is a rhythm to it. Read a bit, do a bit, check it worked, move on. Everything above is in service of not breaking that rhythm.

## Give them somewhere to work

The environment problem is the one where tooling does solve it. Everyone has been in the room where a third of the people still aren't running forty minutes in, and the ones who did get it working are bored. Worse than the lost time, you have no idea what state anyone is in, so everything I said about checking their work goes out the window.

The answer is to host it, so every person gets a browser tab with the environment already in it, the instructions beside the terminal rather than in a separate window, an editor and a console in the same place, and all of it running before they arrive. I work on [Educates](https://educates.dev), which is open source, but Killercoda, Strigo and Instruqt do this too, and the point is the category rather than the product. What matters is that everyone starts from the same place, which is what makes the checking possible at all.

Once you are hosting it, something more interesting opens up. You can hand someone an environment that is already broken and make them work out why, which is the only practical way to teach diagnosis, since if they build it themselves they only ever meet their own mistakes. You can start them at step seven with the first six already done, so the time goes on the part worth teaching. You can give them three services and a database with realistic data in it. The setup friction was never just a tax on the workshop. It was a limit on what the workshop could be about.

## Using AI to write it

Yes, I see the irony. I spent the first part of the talk saying AI is why nobody needs our written walkthroughs, and I use AI to help write workshops. I don't think those are in conflict, but it pays to be specific about where it helps.

It is useful for getting a first draft down when the alternative is staring at an empty file, for generating variations on an exercise so you can pick the one that works, and for the tedious parts such as formatting, boilerplate and checking whether the commands you wrote three years ago still work. There is a pattern to that list. None of it requires knowing anything about the person who will do the workshop. All of it requires knowing the subject, because if you don't, you can't judge whether what comes back is right.

Where it falls down is exactly the three content problems, and for the same reason each time. It can't feel step size because, like you, it already knows the answer. It defaults to telling you exactly what to type because that is what documentation looks like, and documentation is what it learned from. It won't put checks in because the material it learned from doesn't have checks in it either. Some of that will change, since these tools move quickly, but the underlying cause doesn't. It has never watched anybody get stuck.

The way I think about it is that correct and teachable are different axes. AI is optimising for correct, meaning the commands work and the explanation is accurate. Teachable means paced for a real person who doesn't already know the answer, and nothing in how these tools are built is aiming at that. So let it draft, you shape it, and then you test it on an actual person. That third step is the one everyone skips and the only one that catches the problem, because the whole issue with AI-written material is that it reads fine. You can't catch it by rereading. You catch it by watching somebody try.

## Getting to the starting line

Everything so far assumes that someone is already sitting in front of the workshop, ready to go. You can build the best workshop in the world and none of it matters if nobody starts it, and I think getting people to start is getting harder.

Workshops mostly get used in six situations. A conference booth, a conference workshop session, online and on demand, training at a customer site, a one-on-one demo for someone evaluating a product, and running it locally on their own machine. Sort those by why the person is there. At one end are the sales demo and the customer training, where there is a business reason behind attending, and that motivation doesn't disappear because AI got good. At the other end are online self-serve and the local download, where the only thing bringing someone is their own curiosity. Curiosity is exactly what a chat window satisfies, faster and for nothing. So the pressure isn't spread evenly. It is concentrated at the voluntary end.

That end has a second problem, which is that if you are an individual rather than a company, you have no way of telling anyone the workshop exists. The blogs that used to carry this sort of thing don't get read. The forums people used to hang around in have emptied out. Social media is so full of AI slop that anything real gets lost in it. Unless you already have a YouTube following, there is no route from "I made this" to "somebody knows about it". If you work somewhere that can put money behind getting the word out, you can buy the reach an individual doesn't have. Which means these workshops don't stop existing. They end up belonging to whoever can pay to be found.

I don't know how that resolves, and this is what I have seen rather than anything I have measured, so I am not going to claim self-serve workshops are finished. But I think we have been asking the wrong question. It isn't "are workshops still relevant". It is "relevant to somebody arriving how".

## So why release 24 more

Which brings me back to wrapture. As I described in [Trying out wrapture](/posts/2026/09/trying-out-wrapture/), there are now [24 workshops](https://github.com/GrahamDumpleton/wrapture-workshops) which run in JupyterLab on [mybinder](https://mybinder.org/v2/gh/GrahamDumpleton/wrapture-workshops/main?urlpath=lab). Free, self-serve, click a link and start. That is precisely the end of the spectrum I just said is in trouble.

The difference is that wrapture is barely a month old. It isn't in any model's training data. Ask an AI how to use it and you will get either an admission that it doesn't know, or something confidently made up. The only way to get useful help from an AI is to deliberately feed it the documentation first, which you can do, since ReadTheDocs makes the complete wrapture documentation available as a [single PDF](https://wrapture.readthedocs.io/_/downloads/en/latest/pdf/). Short of that, the workshops are competing with a chat window that can't actually answer the question. That window will close as the models catch up, but it is open today, and while it is open a workshop is still the best way to learn wrapture by doing rather than by reading.

The other difference is one I glossed over in the talk. The AI will need material like these workshops to learn from. Whatever it can tell people about wrapture next year will be drawn in part from these posts and workshops, so even on the pessimistic reading, the effort isn't wasted. The value just shows up somewhere other than in people doing the workshops. That is a strange thing to be building for, but it is where things are.

There is a third reason as well, which is that creating the workshops was a way of further exploring how effective AI can be at producing hands-on material. I said in the talk that it fails at step size, at setting problems rather than regurgitating the documentation, and at adding verification, because it has never watched anybody get stuck. The question I wanted to test is whether it can be guided well enough to get those three right anyway. Whether that means being explicit about how big each step should be, insisting on the change one thing and predict what happens pattern, and requiring a check after anything that can silently go wrong. The wrapture workshops are the result of trying that, and by my own argument I can't yet say how well it worked, since the only way to find out is to watch people do them.

The discovery problem, this time, got partly solved by luck. Simon Willison wrote about wrapture [twice](https://simonwillison.net/2026/Sep/11/wrapture/), the Python Bytes podcast [covered it](https://www.youtube.com/live/4AUE4ewgN38?t=844), and the stars on GitHub jumped. That is the reach I said an individual doesn't have, borrowed rather than bought. Without it the workshops would most likely have sat there unnoticed.

What remains is the problem I have no solution for. Even when people know a workshop exists, sitting down and working through one is now seen as a chore next to asking an AI or watching a YouTube video. People have become accustomed to getting the answer without the doing. You do what you can. If people don't want to make use of what you provide, there isn't much more you can do about it.

## Four things to take away

Reading and doing are different things. That hasn't changed, and it is the part AI hasn't touched. Three of the four reasons people give up are about your content rather than your tooling, and no platform fixes those. AI will make your content correct but it won't make it teachable, and that is still you. And know which channel you are building for, because whether workshops are still relevant turns out to depend entirely on who is sitting down and why they are there.
