---
title: "Developer Advocacy in 2026"
description: "What are the major forces that have reshaped developer advocacy."
date: 2026-02-01
draft: false
---

I got into developer advocacy in 2010 at New Relic, followed by a stint at Red Hat. When I moved to VMware, I expected things to continue much as before, but COVID disrupted those plans. When Broadcom acquired VMware, the writing was on the wall and though it took a while, I eventually got made redundant. That was almost 18 months ago. In the time since, I've taken an extended break with overseas travel and thoughts of early retirement. It's been a while therefore since I've done any direct developer advocacy.

One thing became clear during that time. I had no interest in returning to a 9-to-5 programming job in an office, working on some dull internal system. Ideally, I'd have found a company genuinely committed to open source where I could contribute to open source projects. But those opportunities are thin on the ground, and being based in Australia made it worse as such companies are typically in the US or Europe and rarely hire outside their own region.

Recently I've been thinking about getting back into developer advocacy. The job market makes this a difficult proposition though. Companies based in the US and Europe that might otherwise be good places to work tend to ignore the APAC region, and even when they do pay attention, they rarely maintain a local presence. They just send people out when they need to.

Despite the difficulties, I would also need to understand what I was getting myself into. How much had developer advocacy changed since I was doing it? What challenges would I face working in that space?

So I did what any sensible person does in 2026. I asked an AI to help me research the current state of the field. I started with broad questions across different topics, but one question stood out as a interesting starting point: *What are the major forces that have reshaped developer advocacy in recent years?*

This post looks at what the AI said and how it matched my own impressions.

## Catching Up: What's Changed?

The AI came back with three main themes.

### Force 1: AI Has Changed Everything

**What the AI told me:**

> The data suggests a fundamental shift in how developers work. Around 84% of developers now use AI tools on a daily basis, with more than half relying on them for core development tasks. Developers are reporting 30-60% time savings on things like boilerplate generation, debugging, documentation lookup, and testing.
>
> This has significant implications for developer advocacy. The traditional path—developer has a problem, searches Google, lands on Stack Overflow or your documentation, reads a tutorial—has been disrupted. Now, developers increasingly turn to AI assistants first. They describe their problem and get an immediate, contextual answer, often with working code included.
>
> What this means is that your content now has two audiences: humans *and* AI systems. Your documentation isn't just being read by developers—it's being ingested, processed, and used by AI to generate answers. If the AI misrepresents your product or gives incorrect guidance, you may never even know it's happening.
>
> There's even an emerging standard called llms.txt that's gaining traction. First proposed in late 2024, it's a file that tells AI systems what content to prioritise and how to interpret it. By 2026, documentation without this kind of AI-optimisation struggles to surface correctly when developers ask AI assistants for help. It's like SEO, but for language models instead of search engines.

**My take:**

Yep, no surprise here. I've seen this firsthand with my own mod_wsgi and wrapt open source projects, and it goes beyond what the AI described. In the past, people would ask questions via Stack Overflow, project-specific forums, or mailing lists if they did get stuck. These days, direct engagement is rare. Occasionally someone might raise a problem on GitHub, but those old communication channels have largely disappeared. People using your code just ask the AI instead.

As for the suggestion that I need to put in extra work to help AI systems, such as providing an llms.txt file, I'm not convinced. From what I can see, AI is already doing a good job of working things out on its own. Besides, project documentation, while supposedly authoritative, isn't the only source of information out there. I don't think an AI will give your llms.txt file any more credibility than the third-party content scattered across blogs, conference talks, and elsewhere.

Either way, AI has drastically changed things and now sits between a user and documentation for a project. It can be demoralising to write documentation when you don't know if a real person will ever actually read it anymore.

### Force 2: Content Saturation Has Reached Crisis Levels

**What the AI told me:**

> The volume of content being produced has exploded. Current estimates put global data production at over 403 million terabytes daily, and around 80% of developers report experiencing information overload. The symptoms show up in the data: lower click-through rates, shorter time-on-page, faster scrolling behaviour, declining email open rates.
>
> The root cause? AI has made content creation trivially easy. Anyone can generate a tutorial, write a blog post, or produce documentation in minutes. The result is a flood of content, much of it generic, shallow, and nearly indistinguishable from everything else.
>
> Developer communities have adapted. Developers have become sophisticated at filtering low-quality content. Generic "getting started" tutorials are largely ignored because AI can generate them on demand. Surface-level blog posts get scrolled past. The attention bar has risen significantly.
>
> This creates a dual reality. The challenge: your content competes against unprecedented noise. The opportunity: genuinely valuable content stands out more than ever, precisely because it's rare.

**My take:**

I'd have to agree with the AI here. I'm definitely feeling overwhelmed by the sheer volume of content when researching topics these days. That said, I'd qualify that observation. It's particularly acute for topics with a lot of buzz around them, AI being the obvious example. The same applies when searching for information on large software projects with broad user bases, like popular programming languages or major web frameworks. But for niche areas, I don't see this as much of an issue. People aren't going to generate content for obscure projects just for the sake of it, especially when there's no hype driving attention.

When talking about developer advocacy as a job, the focus is usually a company's own product. For most companies, especially early-stage ones, they don't have the mind share yet, so they fit into that niche category.

That said, content saturation is still a real problem. I'm tired of the endless YouTube videos on the same topics and how self-proclaimed advocates jump on trends to outdo each other. Too often, the focus is just on shipping content, which means discussions end up shallow and repetitive with little substance.

### Force 3: Platform Fragmentation Has Disrupted Communities

**What the AI told me:**

> The platform landscape has shifted significantly. When you were last active, Slack dominated developer communities, Discord was primarily for gamers, and Twitter served as the town square for tech discourse.
>
> None of that holds anymore.
>
> Discord has overtaken Slack for developer communities. The drivers were primarily economic—Slack's pricing pushed communities toward free alternatives—and feature-related, with Discord offering better moderation tools, role management, and community features. Many developers who were daily Slack users between 2015-2020 have essentially stopped using Slack and are now primarily active in Discord channels.
>
> The Twitter situation is more fragmented. Some developers moved to Mastodon, others to Bluesky, and many simply reduced their social media engagement altogether. LinkedIn has grown as a platform for technical content. There's no longer a single "town square" where developers reliably gather.
>
> The practical implication: you can't rely on any single platform for community strategy. Presence across multiple spaces, with different approaches for each, is now necessary.

**My take:**

My age is probably showing here. The AI talks about people moving from Slack to Discord and the demise of Twitter. I still miss mailing lists. Back then, I found the asynchronous nature of mailing lists to be a much better forum for discussions with users. You could take your time understanding questions and drafting thoughtful responses. These days, with real-time discussion platforms, there's pressure to provide immediate answers, which often means less effort goes into truly understanding a user's problem.

To me migrations between platforms for the purpose of providing support to users is inevitable, especially as technology changes. This doesn't mean that new platforms are going to be better though.

Of the disruptions, I felt the demise of Twitter most acutely. It provided more community interactions for me than other discussion forums. When everyone fled Twitter, I lost those connections and don't feel as close to developer communities as I once did, especially the Python community. COVID and the shutdown of conferences during that time compounded this. Overall, I don't feel as connected to the Python community as I was in the past.

## Initial Reflections

Having gone through these three forces, I'm left with mixed feelings. Nothing the AI said was really a surprise though.

The main challenge in getting back into developer advocacy is adapting to how AI has changed everything.

I don't see it as insurmountable though, especially since companies expanding their developer advocacy programs are typically niche players without a huge volume of content about their product already out there. The key is ensuring the content they do have on their own site addresses what users need, and expanding from there as necessary.

Relying solely on documentation isn't the answer either. When I've done developer advocacy in the past, I found that online interactive learning platforms could supplement documentation well. That's even more true now, as users aren't willing to spend much time reading through documentation. You need something to hook them, a way to quickly show how your product might help them. Interactive platforms where they can experiment with a product without installing it locally can make a real difference here.

## What's Next

Right now I'm not sure what that next step is. I'll almost certainly need to find some sort of job, at least for the next few years before I can think about retiring completely. I still work on my own open source projects, but they don't pay the bills.

One of those projects is actually an interactive learning platform, exactly the sort of thing I've been talking about above. I've invested significant time on it, but it's something I've never really discussed here on my blog. As I think through what comes next, it seems like time to change that.
