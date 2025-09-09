---
title: "Python 3.0 support in mod_wsgi to be disabled."
author: "Graham Dumpleton"
date: "Tuesday, April 28, 2009"
url: "http://blog.dscpl.com.au/2009/04/python-30-support-in-modwsgi-to-be.html"
post_id: "7324659707056875745"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 6
published_timestamp: "2009-04-28T16:40:00+10:00"
blog_title: "Graham Dumpleton"
---

I have been hanging off releasing [mod\_wsgi](http://www.modwsgi.org) [3.0](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0300) due to uncertainties in how [WSGI 1.0](http://www.python.org/dev/peps/pep-0333/) specification should be [implemented](http://www.wsgi.org/wsgi/Amendments_1.0) in Python 3.0. Despite a number of discussions on [Python WEB-SIG](http://groups.google.com/group/python-web-sig?lnk=) about it, there has never really been any final consensus on the issue. This isn't helped one bit by the fact there is no formal process for agreeing, by way of vote or otherwise, on changes or amendments to the WSGI specification. Thus, all the conversation just amounts to a lot of hot air at the end of the day as nothing ever gets agreed upon.  
  
As a result, I am going to move ahead with releasing mod\_wsgi 3.0, but am going to disable support for Python 3.0. I will not remove the code entirely, but will make it necessary to go through some hoops to allow you to build mod\_wsgi with Python 3.0, with suitable large disclaimers that if you use what is there, you will likely have to change your code at a future date when any amendments are agreed upon. In the mean time I will not be supporting the code related to Python 3.0.  
  
It has come to this as it appears that other WSGI adapters attempting to support Python 3.0 are not implementing it the same way. This isn't a complaint against the authors of those other WSGI adapters as they are in the same boat as I am. The real problem is that there is no WSGI specification which covers Python 3.0. It is already bad enough that the WSGI 1.0 specification has various areas that aren't well defined or which are too restricting, to the extent that many of the major frameworks possibly don't even adhere to it. So, one can see this as being my protest at the lack of any formal processes for the development of the WSGI specification.  
  
And before you have a go at me and say then that I should instigate such a formal process, let it be known that I have tried that already and there was no interest. So called consensus was that consensus was sufficient.  
  
Some have suggested to me that I would be effectively setting the standard with what ever I released in mod\_wsgi. Well, I don't want that to be the case. Although I wrote mod\_wsgi I don't write web applications myself and am not across all the nuances of what would or wouldn't work for Python 3.0. Thus, I rely on the experience of others in helping define what the WSGI specification should be and merely implement that specification. So, no specification, no support.

---

## Comments

### István Albert - April 29, 2009 at 12:49 AM

I think most good things come from one capable individual making wise choices \(based on other people's input\) and never via a "design by a committee" where everyone fully agrees.  
  
My suggestion: listen to people, collect feedback ... then go ahead and implement what you think is the best way. mod\_wsgi will be the standard...

### nnis - April 29, 2009 at 1:17 AM

"worse is better". Just use your judgment and release something while it is not widespread. Fix it later.

### Bill Karwin - April 29, 2009 at 2:02 AM

I think you're doing the right thing. Perhaps your move will encourage the use of proper process. If you design code based on the "consensus" of the people who are capable of emitting the most hot air, then you might as well be working on PHP. ;-\)

### René Dudfield - April 29, 2009 at 2:15 AM

Hello,  
  
Marking python3 wsgi support as experimental is wise.  
  
Very few people have even tried python3 long enough... and python3 itself is still evolving, and best practices forming. Also, I hardly think anyone belives python3 is ready for production yet?  
  
Also, I think it makes sense for a couple of people to try implementing the changes... which always leads a better understanding of the issues.   
  
Another factor, is that more people try out proper releases of software... so more people will try out the python3 support... and hopefully then more eyes will see more issues.  
  
So marking it as experimental at this time seems the best thing to do. Since there's not really many other people who have tried implementing the changes.  
  
Perhaps aim for making the proper wsgi support come out at the same time, or shortly after python3.1. wsgi ref lives in python now. It seems like maybe the pep process would be appropriate.  
  
What don't you agree with, with how cherrypy and others are doing it?  
  
It would be very handy if there was a document with your proposed changes.  
  
Do your changes match these:  
http://www.wsgi.org/wsgi/Amendments\_1.0  
  
From reading the mailing list thread, there didn't seem like much disagreement? I can't really follow what needs to be decided upon.  
  
  
cu,

### Graham Dumpleton - April 29, 2009 at 9:34 AM

@István: Part of the problem is that I don't believe the range of input is there. Comment is only coming from people associated with a small selection of the major Python web frameworks and applications. Thus it is hard to know whether the others just don't care or don't know. I'd prefer to know the stance of all the major players. Maybe it is too premature for this since they don't even have Python 3.0 on the radar as yet.  
  
@nnis: Once you put something out there you cannot take it back. So, if something is too accommodating and then you restrict it later, you just cause a lot of pain. Some of the issues are also rather fundamental and aren't just a case of whether you allow something or not, but how you actually do it.  
  
@illume: Not all discussion has been on the WEB-SIG list. For whatever reason, email to the list for at least one person whose opinion I respect, has been disappearing into some SPAM black hole and so they have not been able to readily join the conversation.  
  
Anyway, the two major issues outstanding are, whether WSGI adapter should accept string output or only bytes. Understand that Robert in CherryPy WSGI server is at the moment only allowing bytes. The much more hairy one and which has caused most of the discussion is whether variables in WSGI environment source from CGI environment equivalents, should be bytes or strings. Even though there was a leaning to them being strings, there was still some reservations on that issue, both on and off the list. I think there was enough issues with RFC 2047 that seen that WSGI adapters shouldn't bother with that.

### JasonBoiss - September 30, 2010 at 9:52 PM

WSGI needs a BDFL; not design-by-committee.  
  
You've done the most work out of anyone to create a stable and well-designed deployment method. It seems logical that the person building the main module for WSGI also dictates the spec.

