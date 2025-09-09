---
layout: post
title: "Should my next conference talk be on how web servers work?"
author: "Graham Dumpleton"
date: "2011-03-24"
url: "http://blog.dscpl.com.au/2011/03/should-my-next-conference-talk-be-on.html"
post_id: "6097649225318501254"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 7
published_timestamp: "2011-03-24T08:18:00+11:00"
blog_title: "Graham Dumpleton"
---

Last year was actually the first time I had attended a PyCon conference. This was because Australia hadn't ever hosted a PyCon conference before and everywhere else was far enough away from Australia to make it hard to justify. When Singapore announced they would be hosting their first PyCon conference however I just had to go as that part of Asia is an area I like visiting. Coincidentally Australia then announced quite late that they would also host their own PyCon a week after the Singapore PyCon. In the end I went to PyCon conferences in Singapore, Australia and New Zealand last year. This was topped off by getting the opportunity through my new job at New Relic to go to US PyCon this year.

  


Because of time constraints I didn't present any talk at Singapore PyCon, but did step up and do one in Sydney which I then gave again at New Zealand. I didn't do anything for US PyCon as I only found out I would be going a bit more than a month out from the conference.

  


The conference talk I did last year was one on getting started with mod\_wsgi. The approach the talk took was to show all the things that could go wrong and explain why those situations come about. Having now attended the US PyCon, in hindsight I probably tried to pack a bit too much into the talk and one could argue it was also perhaps too instructional for a conference talk. Most talks seem to be much more high level and along the lines of 'hey look at what I am doing' rather that being a mini tutorial intended to actually teach you a lot of stuff while you are there.

  


For that reason, rather than try and do further highly technical talks on WSGI deployment or debugging of web applications, I thought for this year that I would instead step back a bit and do a talk on the basics of how web servers work. I realise that this isn't necessarily Python specific, but what keeps coming up out there on the various forums is that many people simply don't understand how the web server they are using actually works. Most see the web server as merely an inconvenience, something that they have to install but which they never understand enough to know how to set it up properly.

  


The talk I have in mind would therefore cover the common architectures that web servers use. So, topics such as threaded vs event driven systems, single process vs multi process, as well as descriptions of the different request queuing mechanisms and use of backend daemon processes for running the dynamic parts of a web application. There obviously needs to be some Python slant to all this, so would also cover how the architecture of the web server affects the type of interface used between a Python web application and the web server, plus issues such as data sharing between different parts of the Python web application. Finally, would try and cover why you would choose one server architecture over another or when you should actually employ multiple web servers with different architectures for different parts of one overall Python web application.

  


So my question is, is a talk about such a topic something that would be of interest out there in the Python web community? I sort of feel it is an area where there isn't a great deal of good information out there about, but I could be totally wrong.

  


If not the above topic then, what would people like to hear me do a talk on? Realistically I might only have time to prepare one good talk, but if there is interest in other topics, I can always try for more. I do have to work it out soon though to get in before call for papers for Singapore and Sydney PyCon conferences closes.

---

## Comments

### Unknown - March 24, 2011 at 10:10 AM

I'd be in favour. The only thing that crosses my mind is it sounds like quite a lot of ground to cover in the time allowed.  
  
Going off topic here I was struck by your having been to four different Pycons in one year. I'd be interested to see you do a blog post which compared and contrasted the nature of the different events \(speaking as someone who's only ever been to Kiwi pycons\)

### Robert Kern - March 24, 2011 at 1:42 PM

That sounds fantastic. Yes, please give this talk.

### Tim Knapp - March 24, 2011 at 8:09 PM

I agree, sounds an excellent topic and something I'd definitely want to listen to. On a purely selfish note, I'd love to hear you give it at Kiwi PyCon 2011 :\)

### Marius Gedminas - March 25, 2011 at 1:30 AM

I haven't seen the talk itself, but I found your mod\_wsgi slides to be \*excellent\*.  
  
A generic talk about how web servers work doesn't sound that interesting -- I know the basic principles already. What I'd love to hear about would be practical consequences: how to tune your Apache/Ngnix/whatever if you're going to deploy Python WSGI apps, so you get acceptable performance/memory usage.  
  
But since I live on approximately exactly the opposite point on the globe, I'm unlikely to visit any of the conferences you're speaking at...

### Rodrigue - March 25, 2011 at 11:25 PM

That would make for a very interesting talk indeed. As soon as you try to develop a web app that does something a bit complex, you certainly need a grasp of what your web server is doing. For example, to avoid situations like: what\!? More than one requests are accessing this variable at the same time\!?  
  
Explaining a web server's design and behaviour, its implications on a web app, and then more specifically on a WSGI app would be very interesting.

### Rodrigue - March 26, 2011 at 11:50 PM

Hey Graham. I have been thinking more about your post and the talk you're thinking of giving. I am involved in organizing PyCon Ireland 2011 in Dublin. We would be delighted to have you as a guest speaker if you could be interested. I suspect we could apply for funding from the PSF to sponsor your trip to Europe.  
  
If you have any interest feel free to drop me a line rodriguealcazar at gmail dot com.

### blueskiwi - May 12, 2011 at 1:48 AM

If you wrote it as a blog post I'd read it tomorrow\!

