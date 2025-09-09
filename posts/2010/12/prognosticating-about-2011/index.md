---
title: "Prognosticating about 2011."
author: "Graham Dumpleton"
date: "Friday, December 31, 2010"
url: "http://blog.dscpl.com.au/2010/12/prognosticating-about-2011.html"
post_id: "8298397335115066167"
blog_id: "2363643920942057324"
tags: ['django', 'mod_wsgi', 'pycon', 'python', 'wsgi']
comments: 0
published_timestamp: "2010-12-31T11:39:00+11:00"
blog_title: "Graham Dumpleton"
---

I don't normally sit down and really plan out what I might do in the coming year, but the coming year is looking quite rosy due to my recent change of job. This change has given me a new sense of enthusiasm, especially since I now get to do a lot more programming and on something I find interesting as well. Best of all I get to sit at home doing it, so I now have a lot more flexibility as far as organising my time. I want therefore to try and harness this revived inner spirit and try and set some goals for the coming year.

  


**My New Job**

  


Obviously the first goal is to do well in my new job. This isn't just about giving back to the company for their faith in hiring me in the first place, especially since Python is a new area for them. It is also because the end result of the work I am doing there will I feel be a great thing for the Python web community and I like being able to give back to the community. For those who don't know, my new job is with [NewRelic](http://www.newrelic.com/). If you hop over to their site, I am sure you can read between the lines as to what I am working on. :-\)

  


**Commentary On WSGI**

  


For those who follow my blog postings and the discussions on the [Python WEB-SIG](https://groups.google.com/forum/?fromgroups#!forum/python-web-sig) over the past few years you will now I have had quite a lot to say about [WSGI](http://www.wsgi.org/). Although people don't always listen to my ideas, or sometimes it takes a while to get people to appreciate some things I say, I have wanted for a while to write a proper extended commentary on the WSGI specification and all the issues and problems with it. Yes my blog posts and mailing list posts have dealt with a lot of this stuff, but I want to bring that all together, along with a lot of other thoughts I have about it, into a mini \(or maybe no so mini\) booklet which can stand as a single source of information about the WSGI specification.

  


It isn't the intention that this be a book which would be published. I see it as more of a living ongoing technical commentary which would be continually added to with additional information as required. It's main intention is to provide knowledge and wisdom about the current [PEP 333](http://www.python.org/dev/peps/pep-0333/) specification, as well as the newer [PEP 3333](http://www.python.org/dev/peps/pep-3333/) which addresses Python 3.

  


At the moment it is not the intention to be proposing as part of this commentary what any newer version of WSGI should look like. If I weigh into that argument again, I'll do it distinct from this, although obviously I would base justification for any changes on issues highlighted by this commentary. For the record, I disagree with various aspects of what has been proposed by others as future version of WSGI. I really believe that a much bigger step back needs to be taken and a fresh look made of all this, with consideration being given to the larger problem of deployment as well, rather than just focusing on the aspects of the interface itself. There are also still some basic problems with the existing WSGI interface and usage of it that the proposals aren't addressing which need to be dealt with in some way.

  


**WSGI Application Deploymen** t

  


I am not actually sure what I am going to do about the [mod\_wsgi](http://www.modwsgi.org/) module for Apache at this point. I have had many ideas of what I could do with it over the past few years, but lack of time and enthusiasm has meant that I have not got to pursue them. In the mean time, other solutions for WSGI application deployment have become available which provide features which overlap with where I have wanted to take mod\_wsgi. Because mod\_wsgi wouldn't therefore be the first to provide that functionality, the incentive has dropped some what.

  


What therefore I want to concentrate on instead in the area of WSGI application deployment is again documentation. This time I want to write a mini booklet on WSGI application deployment. This obviously would focus on Apache and mod\_wsgi, but so as to be able to contrast against alternative WSGI hosting solutions, would also want to cover in a fair detail the other main options that exist. A lot of this would draw from existing mod\_wsgi documentation, but there would also be a lot of new material, especially material for newbies who usually don't want to read documentation but instead expect a bullet point list of half a dozen steps to have everything working.

  


For those who know anything, you will realise that such an abbreviated and idealised step of instructions would more often than not be quite useless because things are never that simple, but at least it can serve as entry point into the more detailed information behind to explain better what each step is for and all the issues that can arise.

  


Because trying to cover how to handle deployment for every WSGI framework out there is just going to be too big of a job, I will however focus the documentation on just two frameworks. These will be Django and Werkzeug/Flask. Django because it is the most popular and Werkzeug/Flask because I am always really impressed with the work that [Armin Ronacher](http://lucumr.pocoo.org/) puts out and I really reckon that Werkzeug would be a great foundation for a more full stack framework.

  


**WSGI Application Debuggin** g

  


Another area of the existing document for mod\_wsgi that I would like to turn into a mini booklet is that about WSGI application debugging. What already exists in that area on the mod\_wsgi wiki only scratches the surface as far as what techniques can be used and what tools are available. I would like to take that and expand on it greatly so as to provide something one can go to when things start to go wrong after you have actually got your WSGI application deployed, or even perhaps while you are trying to get it deployed.

  


What I am working on in my new job at NewRelic obviously plays into this, but the booklet isn't intended to be an advertisement for that and it would be just one of the many tools described that one might fall back on.

  


**Python Conferences**

  


Even though I have been playing with Python since the early 90's when it first came out, 2010 was the first time I have ever been to a conference about Python. That first conference was PyCon in Singapore. Because my wife's family lives in Malaysia and Singapore and I go there frequently, it was a no brainer that would take any reason as an excuse to take the family for a trip to Singapore. For that conference I didn't present any talks, but all the same, was great to meet up with the local Python users as well as those from afar such as Steve Holden.

  


After I had already decided to go to Singapore, they also announced that the first PyCon in Australia would be held the same year in my home town of Sydney. Once again, an easy decision as to whether to go and that time I did do a presentation on mod\_wsgi.

  


Having had so much fun at those two PyCon conferences, I thought I would follow it up by going to PyCon in New Zealand late in the year and presented my mod\_wsgi talk from Sydney once again. The New Zealand PyCon was especially good as got to meet Jacob Kaplan Moss and we had a few interesting conversations which would be pertinent to what I was going to be working on at my new job, although I only found out while I was at the actual conference that had actually got the job.

  


So, all up I went to three PyCon conferences in my first year of attending them. I don't know who said it, perhaps Steve Holden when I was at Singapore PyCon, but I was warned that they become addictive. As such, I expect to again go to PyCon in Singapore in 2011 and of course that in Sydney. The one in New Zealand PyCon is still a long way away, so will see about that. May depend on who they get as keynote speakers. If it is someone from the US or Europe who I would be interested in meeting up with, then would definitely attend.

  


As to whether I do any talks, not sure at this point. I don't believe yet another talk on mod\_wsgi or WSGI deployment would be of interest. That said, the Singapore PyCon does have a tutorial day and perhaps that might be a good avenue for doing something more in depth than a basic talk. So, something more akin perhaps to a master class on WSGI application deployment which would cover a lot of the stuff which would be in the mini booklet on WSGI application deployment I want to do. In that frame, perhaps could also do a master class on WSGI application debugging. A shorter version of the latter could perhaps be done as a talk at Sydney, plus New Zealand if I get there.

  


So, definitely want to go to what PyCon conferences I can in 2011, but just not sure whether I would present. Things are going to be busy for me as it is, and doing presentations, especially tutorials requires quite a lot or preparation. I would be very much interested in feedback from people out there who might attend these PyCon conferences in the Asia/Pacific region as to what you might be interested in hearing about.

  


As well as attending PyCon, I am also eyeing off DjangoCon in Portland later in the year. This is in part because NewRelic has an office in Portland. If I am lucky, maybe I can take advantage of that and time any visit to the US for work, if I need to go, around that time.

  


**Having Fun With My Family**

  


I could sit and code and play around with stuff all day, but just so you don't think that is all I do, my family and especially my 3 year old daughter still takes a lot of my time. Ultimately that still takes priority and although the above things may be what I would like to do, you never know what is going to happen.