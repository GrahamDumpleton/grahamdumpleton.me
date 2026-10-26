---
title: "AI slop is the new TLDR"
description: "Calling AI generated code slop often says less about the code than about our willingness to read it. Why it feels like onboarding every day, and how I cope."
date: 2026-10-27
tags: ["ai", "educates"]
---

It is hard to get through a day online at the moment without someone dismissing something as "AI slop". A pull request, a library, a whole project, all written off with two words. When the thing being dismissed is code, I have started to notice that the label usually arrives well before anyone could have actually read the code in question.

That has led me to a slightly uncomfortable conclusion. In a lot of cases, calling AI generated code slop is just a new way of saying TLDR (too long, didn't read). It isn't really a measure of whether the code is good or bad. It says more about the willingness of the person saying it to sit down and learn what the code does.

There is even slang emerging for the general version of this. Posts that are obviously AI generated are now getting the response [AI;DR](https://www.fastcompany.com/91498062/ai-didnt-read-aidr-is-the-new-tldr), as in "AI, didn't read". At least that is honest about what is going on. Slop dresses the same reaction up as a judgement of quality.

## When slop is a fair call

I should say up front that some AI generated code really is slop. Open source maintainers in particular are being buried under pull requests and bug reports where the person submitting them clearly has no idea what they are submitting. Generating that stuff costs the submitter almost nothing, while reviewing it costs the maintainer real time, and that imbalance is a legitimate thing to be angry about.

Look closely at those cases though and the failure is the same one. The person who generated the code didn't read it either. They asked for something, got something back, and passed it on without understanding it. So the TLDR problem exists on both sides. There is the person who produces code without reading it, and there is the person who dismisses code without reading it. Neither has actually engaged with what is in front of them.

One working definition I came across describes [slop as code you can't work with](https://dwyer.co.za/static/slop-is-code-you-cant-work-with.html), that is, a codebase that nobody understands well enough to work with effectively. I think that is about right, but notice what the definition hinges on. It is about understanding, and understanding is not purely a property of the code. It also depends on whether anyone has put in the effort to acquire it.

A simple test I now apply to myself is to ask whether I would have said the same thing if a new colleague had written the code. If the answer is that I would have sat down, read through it, and given proper feedback, then reaching for "slop" instead is a sign I am taking a shortcut.

## Every day is onboarding day

So why would people take that shortcut? I don't think it is simply laziness, or at least not only laziness. I think it is fatigue, and it is worth being honest about where that fatigue comes from.

Think back to the first few weeks of starting at a new organisation. You arrive and there is an existing body of software that you didn't write and don't understand. Before you can do anything meaningful you have to learn what it does, then how it does it, and then why it was built that way. It is a steep learning curve for anything you didn't already know, and it is mentally exhausting. Most people I know come home from their first week in a new job completely wiped out.

Working with AI generated code can feel a lot like that, except it doesn't stop after a few weeks. Every day there is another pile of code you didn't write, built on decisions you didn't personally make. In some respects every day becomes your first day.

It has always been harder to read code than to write it. When you write code yourself, the understanding builds up as you go, almost as a side effect. When you read someone else's code, you have to reconstruct that understanding after the fact, from whatever clues they left behind. With AI doing much of the writing, more of the job has shifted to the harder of those two activities.

There is also an old observation from the study of automation that applies here. When you automate the routine part of a job, the human is left with the part that is harder, which is monitoring what the automation is doing and stepping in when it goes wrong. And because the human is no longer doing the routine work, the hands-on skill needed to step in can quietly fade away. Supervising an AI that writes code is a textbook case of this.

The gap that builds up has been given a name, [comprehension debt](https://www.oreilly.com/radar/comprehension-debt-the-hidden-cost-of-ai-generated-code/), meaning the growing difference between how much code exists in a system and how much of it any human actually understands. Like any debt it accumulates quietly, until the day something breaks and nobody knows where to start.

Faced with all that, it is much easier to throw your hands up and declare the whole thing slop than to admit that you can't keep up, or that you haven't been willing to put in the time to learn it properly. I get the temptation. I just don't think it is an honest answer.

## Agentic engineering and the conductor

What all this points to is that what it means to be a software developer has changed. The term that seems to be sticking for the new way of working is [agentic engineering](https://www.ibm.com/think/topics/agentic-engineering), the idea being that you are mostly no longer writing the code directly, but orchestrating AI agents that do, and providing the oversight.

The analogy I keep coming back to is a conductor of an orchestra. A conductor isn't playing every instrument, but no one would suggest a conductor can get away without a deep grounding in music theory. They have to read the full score, know what each instrument is capable of, hear when a section is out of tune, and know how to fix it. For a developer working with AI, the equivalent of music theory is the fundamentals of software development, architecture and design. You may not be writing every line, but you still need to know what good looks like and recognise when something is wrong.

The analogy does break down in one telling way though. A real orchestra rehearses the same piece over and over before a performance, and the conductor builds up an intimate knowledge of it. With AI the orchestra is effectively playing a new piece every day, with no rehearsal. Which brings us right back to the onboarding problem.

It is also worth noting that reviewing and steering code you didn't write was always part of the job of a senior or lead engineer. People generally grew into that role over many years. What has changed is that everyone is now being put in that position, from day one, often without the experience to back it up. That raises an awkward question about how people new to the industry are meant to learn the music theory if they never get to play an instrument.

## I struggle with this too

I don't want to give the impression I am lecturing from on high here. I now lean on AI quite heavily for some new projects, and I struggle to keep up with the constant flow of new code and new information as much as anyone.

I have tried different approaches. For a while I used Obsidian as a knowledge base, a sort of second brain, to track design decisions and how things fitted together. For some projects that worked well. For others I got so deep into the design, and then into directing the AI to write the code, that going back to get it all into Obsidian felt like more work than it was worth. The end result was that I was back to flying by the seat of my pants and trying to keep it all in my head.

Looking back, I think the reason it failed is that the note taking was a separate chore. Anything that sits outside the actual work is the first thing to get dropped when you are in the flow of things. Whatever approach works has to be a by-product of something you would be doing anyway.

## Having the AI teach me what it built

The approach that has worked best for me so far, at least for projects that I expect other people to use, is to have the AI generate workshops.

The process goes something like this. I have the AI build the software, and keep directing it until what it has produced matches the idea I had in my head. At that point I have it generate a set of hands-on workshops teaching how to use it, which run on my [Educates](https://educates.dev) training platform or in the [JupyterLab workshop extension](https://github.com/GrahamDumpleton/jupyterlab-workshop) I wrote. Then I sit down and work through those workshops myself.

In other words, I deliberately put myself through the new employee onboarding. Rather than trying to absorb the code in bits and pieces as it flies past, I get a structured path through what the software does and how to use it, at a pace where I can actually take it in.

What I didn't expect was how good this is at exposing problems. When you work through a workshop as a user, you very quickly see where the design falls short, where the experience is clumsy, or where things just don't work. The AI also contributes here. If, when generating the workshop, I tell it to highlight problems, it will report when it couldn't get something to work, when it ran into what looks like a bug, or when the documentation doesn't match what the code actually does. So the AI generating the workshop is acting as a QA and user experience tester, and so am I when I work through it.

Because the workshops are interactive and the steps are actually executed, they also behave a bit like tests. If a step in the workshop fails, that is a real problem with the software, not just a typo in some documentation nobody will read.

And then there is the secondary benefit, which is that the workshops exist afterwards for other people. A number of them are available in the [workshops](/workshops/) area of this site. My hope is that they can also encourage people to get past the mental block of TLDR, or AI slop, or whatever they want to call it, and be prepared to sit down and learn something properly. That seems more important than ever at a time when most people will feel it is easier to just ask an AI to do it for them.

## Still working it out

I still don't have a workflow I would call good for using AI and keeping on top of what it is doing. I regard myself as fairly conservative when it comes to tools. I don't go chasing every new fad, because to be frank that usually ends up being a complete waste of time. I suspect most people are similar, and adapting is a slow, incremental process of personal experimentation to see what works for them.

The AI tools themselves, including the tooling from the AI vendors, have certainly made it easier to do a lot of this without reaching for other tools. It is still a matter of finding what works for you, though, and right now things are moving too quickly for anything to settle.

One principle I am trying to hold myself to in the meantime is to not let the AI get too far ahead of my own understanding. A new employee is given time to ramp up, and nobody expects them to be onboarding forever. If the code is arriving faster than I can understand it, the answer is to slow down and make time to learn it, not to stop reading and call it slop.

Hopefully one day I will have it sorted out. Fingers crossed.
