---
layout: post
title: "Is PEP 3333 the final solution for WSGI on Python 3?"
author: "Graham Dumpleton"
date: "2010-10-21"
url: "http://blog.dscpl.com.au/2010/10/is-pep-3333-final-solution-for-wsgi-on.html"
post_id: "8038411731540333401"
blog_id: "2363643920942057324"
comments: 12
published_timestamp: "2010-10-21T11:11:00+11:00"
blog_title: "Graham Dumpleton"
---

While I was off on holidays PJE took [PEP 333](http://www.python.org/dev/peps/pep-0333/) for WSGI and did minor updates to it to accommodate Python 3. The result was [PEP 3333](http://www.python.org/dev/peps/pep-3333/). The response to this on the [Python WEB-SIG](http://groups.google.com/group/python-web-sig?lnk=) was pretty muted, with the only significant person giving open [support](http://groups.google.com/group/python-web-sig/browse_frm/thread/192ae2bf37f6be93) that I could find was Guido himself. Guido's comment was:

> _This is a very laudable initiative and I approve of the changes_

Is this now the end of the matter and are people going to accept this as the final solution? Or are we still going to have a problem with people offering alternate proposals for a standard web server interface for web applications under Python 3.X?

  


As far as I can see [PEP 444](http://www.python.org/dev/peps/pep-0444/) is more or less still on the table as a future alternative, albeit that it may need some more work.

  


So, what do people think? Is PEP 3333 what people are going to use, or is it going to be still born and people are going to demand something else, be that PEP 444 or otherwise?

  


Or is it all academic now given that PEP 3333 is using the WSGI name and so there can be no alternative, at least under the WSGI name, with anything else having to be called something completely different anyway?

  


I would really like to hear from the core developers from the major web frameworks and what you expect you will now do based on PEP 3333 being created. Based on that feedback, I will work out what to do with Apache/mod\_wsgi in respect of bringing it into alignment with PEP 3333.

  


Ultimately I guess if PEP 3333 doesn't get used, just means that Apache/mod\_wsgi will principally be for Python 2.X and a Python 3.X solution for Apache based on alternate specification will be a distinct package, maybe done by me, but possibly left up to someone else.

---

## Comments

### Unknown - October 21, 2010 at 8:28 PM

_Your post is not quite clear if you solicit answers from "significant" people or are throwing the question out in the wind...  
  
I'll interpret that as the latter and offer a simple view on from the point of "small WSGI app coder." I'm sure you have plenty of me-likes chiming in all the time, still..._  
  
3333 Feels like a simple, proper fix for 333's most glaring issues - bottomless wsgi.input, embrace of some HTTP/1.1 realities.   
  
The fact that 3333 tippy-toes around unicode issue in the most benign \(for app developr\) way is almost secondary, but as an WSGI app writer I am much more pleased with 3333's approach to that than 444's. 444 is almost the same in substance, but the verbiage evokes a type Nazi in me.  
As a user I would like not to care about the Latin-1 nonesense and have all environ, header etc \(except request body and response body\) be "Unicode" and have the server jump the extra hoops to decode / accommodate / raise exceptions. 3333 sifts the string type requirements down to manageable, understandable 2-3 sentences.  
  
444 and 3333 serve different goals. 3333 just patches specific, most egregious goals and is long overdue. 444 \(seeing "async" in there\) embarks on philosophical discussion of "where do we go from here?" And, i don't see much future forest for the trees in 444 at this time.   
444 can be stuffed with more stuff, later. Example: "What do you do with Trailer headers?" \(Not an important issue, but, I say push them into the same "environ" pointer, after server already passed it to the app. CherryPy has an odd-ball method on wsgi.input obj for getting Trailers after reading is done.\)  
  
One thing that seriously upsets me in 3333. wsgi.version is still \(1.0\) per spec. It needs to change, to something like \(1,1\) as handling of wsgi.input can be so fundamentally different and simple \(and possible now\) per 3333 under HTTP/1.1, Chunked.  
  
I'd switch to 3333-compatible server on the spot. CherryPy 3.2, WSGI server is essentially that already. Let's get 3333 advertise itself with \(1,1\) and roll with it.

### Graham Dumpleton - October 21, 2010 at 8:51 PM

Daniel, am after responses from both. The key players in the major web frameworks, but also anyone else who has read enough about all the proposals to understand what the issues are, such as you appear to have done.  
  
For the record, I have a preference for seeing it as 1.1 for wsgi.version as well.

### jdhardy - October 22, 2010 at 4:36 AM

My impression \(as the author of a WSGI gateway for IronPython\) is that PEP 3333 is 'good enough' for Unicode support \(and everything else, but Unicode is important to IronPython\), although my opinion may change once I actually sit down to implement it.  
  
Rewriting applications just to get proper unicode support is a no-go. I think PEP 444 is ultimately needed as well, but I'll settle for a fixed PEP 333 at this point.

### Nicholas - October 22, 2010 at 10:56 AM

PEP 3333 will allow us to let go of Python 2 and see a consolidation of energy behind Python 3.  
  
PEP 444 requires experiment, proving, and rationale. uWSGI has stepped up with a server-side implementation, but we have not seen any framework implementation behind it.  
  
3333 is the pragmatic choice, 444 is bones for bike shedders. Let's move on. Nothing excludes future development of web3.

### Graham Dumpleton - October 24, 2010 at 1:41 PM

For the record, discussion about this is on Python WEB-SIG at 'http://groups.google.com/group/python-web-sig/browse\_frm/thread/2746491c020e4e67'. The feeling expressed is that PEP 3333 is it for now. Anything else more or less deferred for time being.

### Unknown - November 7, 2010 at 7:45 AM

Scanning the conversations about PEP-3333 on Web SIG couldn't help by wonder if the effort will be still-born.  
  
The way I see it, the v3-fication of WSGI standard is mostly just a vehicle to fix WSGI 1.0 bugs that mire both, Python 2.x and 3.x.  
There was really only one thing wrong with PRP 333 - wsgi.input was bottomless, which is fatal in HTTP/1.1 Chunked world.   
  
I see conversations about making PEP 3333 somehow Python 3.x-specific because of transcoding nuances for CGI deployment scenario. Stuff like that is "throwing out the baby with the bath water."   
  
I fear that minutia about os.environ transcoding and other 3.x specific fluff will hold back the real bug fixes due for WSGI API. I'm afraid the desire to stay "compatible" with WSGI 1.0 which, likely manifested itself in wsgi.verion = 1.0 \(vs. 1.1\) in PEP 3333 will turn the WSGI App implementation into guessing and server-sensing nightmare.  
Yet, I am afraid to raise any concerns anywhere because talking about these things historically only prolonged the fixes to WSGI standard.   
  
Demn, as a developer, I am liking WSGI world less and less...

### Graham Dumpleton - November 8, 2010 at 7:52 AM

Daniel. It isn't just the WEB-SIG discussions, it when you see posts like [this](http://groups.google.com/group/pylons-discuss/browse_frm/thread/97faa18a3429a28e) where it is obvious that people are still hanging out for PEP 444. This suggests that they will not go Python 3.X with PEP 3333 as a base.

### Graham Dumpleton - November 22, 2010 at 9:34 PM

GothAlice, your trying to push forward PEP 444 at this time is just making things uncertain again when they were starting to clarify that PEP 3333 would be the way forward at this point. Please just wait until the PEP 3333 issue has been settled, or do what you are doing well away from the WEB-SIG and not refer to it as in any way connected to WSGI. You may find the latter necessary anyway, as the WEB-SIG is likely to ignore you at this point and you aren't going to get any support from anyone.

### Graham Dumpleton - November 23, 2010 at 10:20 AM

Further discussion discussion around alternatives at http://groups.google.com/group/python-web-sig/browse\_frm/thread/e5deeb88acf23b46  
  
It is that these discussions keep coming up that concerns me as far as whether the commitment to PEP 3333 will actually be there.  
  
Right now there is still no definitive public statement as to what course will be taken out of the WEB-SIG or wider Python web community. :-\(

### Graham Dumpleton - December 14, 2010 at 5:33 PM

GothAlice  
  
To say in respect of PEP 3333 that 'vagueness on certain critical issues for portability to Python 3' exist is wrong. Some people may have wanted it done differently, but as it stands it is still just as workable a solution for Python 3 as the original.  
  
To say you have been granted control going forward is also wrong. As far as getting changes done to PEP 333 there was no one person in control and that is why no final decision really came about. This has not changed and sorry to say you are deluding yourself if you think you now hold all the cards.  
  
I believe you will actually find that very few people have engaged with your discussion from the complete set of people whose input on this really matters. This is not because people trust you to come up with a better solution, but because people right now don't care and are sick of people pushing alternatives and the way that derailed the original process. I can't see therefore that you have any mandate and don't expect what you come up with to be blindly accepted. History of discussions on the WEB-SIG shows that will never happen.  
  
Your solution also still doesn't address various shortcomings in the existing specification and so it doesn't matter if you wrap it in new clothing, it is still going to have the same issues.  
  
Sorry if you think my language and dismissive is strong, but I have been working on this WSGI on Python 3 issue longer than anyone else and probably have a better understanding of it than anyone else.

### Graham Dumpleton - December 15, 2010 at 9:59 AM

GothAlice  
  
You said 'PEP 444 has been re-named WSGI 2 \(from "web3"\)' and you also said 'PEP 444, for which I have been granted control'. One can read this as meaning you believe you are setting the course of WSGI 2 which I would disagree with.  
  
FWIW, there are already a number of people out there already claiming to be implementing WSGI 2, with different ideas of what that is. You have no more mandate than them for setting what WSGI 2 is and so why making an assumption that you can label it WSGI 2 is silly. All it is going to do is just confuse matters even more because of the growing number of competing WSGI 2 implementations. It is for that reason that I will object strongly and get quite cranky about anyone saying they are implementing WSGI 2. There are already too many things claiming to be that.  
  
As to what I believe are shortcomings in the existing WSGI 1 specification and suggestions on how to resolve it, not all are really documented anywhere. Don't just assume that what you find in what I have written is everything.  
  
As to PEP 3333 compliant implementations, the Apache/mod\_wsgi support for Python 3.X has been available for something like 2 years now and is compliant with what the PEP 3333 specification documents. The only minor not is what wsgi.version is set to. The CherryPy WSGI server also has a Python 3.X implementation which should also be compliant with PEP 3333, again with perhaps wsgi.version not being 1.0 as PEP requires. That implementation has been available for perhaps year as well. Finally, I believe uWSGI has recently started claiming PEP 3333 compliance.

### Graham Dumpleton - December 15, 2010 at 11:08 AM

@GothAlice  
  
Apache/mod\_wsgi does still include Python 3.X support in the code. It has not been disabled, it just isn't highlighted because of lack of ratification on whether PEP 3333 or anything else was going to be the solution. So, it is still there for people to use if they don't care about the uncertainties over what WSGI for Python 3.X will be.  
  
See 'http://code.google.com/p/modwsgi/wiki/SupportForPython3X'.

