---
title: "Sydney PyCon mod_wsgi talk slides available."
author: "Graham Dumpleton"
date: "Monday, June 28, 2010"
url: "http://blog.dscpl.com.au/2010/06/sydney-pycon-modwsgi-talk-slides.html"
post_id: "6135912323114959866"
blog_id: "2363643920942057324"
tags: ['django', 'mod_wsgi']
comments: 10
published_timestamp: "2010-06-28T09:15:00+10:00"
blog_title: "Graham Dumpleton"
---

UPDATE: Video now available at <http://blip.tv/file/3840484>.

  


[Sydney PyCon](http://au.pycon.org/) is over and my talk on [mod\_wsgi](http://www.modwsgi.org/) went okay. For those interested the slides can be downloaded from the mod\_wsgi [site](http://code.google.com/p/modwsgi/downloads/list).

  


Rather than try and explain how mod\_wsgi worked, I concentrated on showing how to setup some basic things, but in doing so deliberately hit all the common problems that some people have with setting up a WSGI application under Apache and mod\_wsgi. The slides therefore capture the details of various obscure error messages one will find in the Apache error logs when things do go wrong.

  


To illustrate issues related to the Python module search path and virtual environments I used Django as an example. The slides therefore are especially valuable if you are trying to deploy Django using mod\_wsgi.

---

## Comments

### Brandon Rhodes - June 28, 2010 at 1:25 PM

That's a great approach — focusing on common errors is so much more helpful than showing a perfect config that doesn't help the confused newcomer figure out how their config is different and why\!  
  
If you remixed the presentation as a blog post, it would be easier for people Googling to find the information, than if they have to go digging into the PDF.

### Graham Dumpleton - June 28, 2010 at 1:28 PM

The intent is, and has been for a long time, to have a wiki page which goes through all the error scenarios. Time though is something I don't have a lot of these days and there is still so much about mod\_wsgi which isn't documented properly. :-\(

### Tim Knapp - June 28, 2010 at 2:50 PM

Yeah great talk. Would be awesome if you could come across for Kiwi PyCon 2010 \(http://nz.pycon.org\) and give it again :\) The CfP should be going out later today.  
  
-Tim

### Peter Marks - June 28, 2010 at 3:08 PM

For me, the talk was spot on. Graham's sequence on all the permissions errors a new site runs in to was like "deja vu all over again".  
  
DaemonMode with the process named after the virtual host makes it easy to top and see which site is hammering cpu.

### Graham Dumpleton - June 28, 2010 at 3:22 PM

Tim. A few of us were talking about NZ conference and I was half joking about going over for it, which would make 3 PyCon's in 6 months for me. The only unknown to me was the location as is outside of the main centres. As such saw it as being a bit hard to get to. It would be good if the travel and accommodation parts of the NZ PyCon site could be updated sooner rather than later so a prospective presenter from outside of NZ can appreciate how much trouble or otherwise it may be.

### Graham Dumpleton - June 28, 2010 at 3:46 PM

Tim. One more thing. If was to do that, might consider a second talk more about how mod\_wsgi works. Just have to work out how I can incorporate into that two 15 tonne robots so satisfy cool factor and can win prize for best talk. ;-\)

### Tim Knapp - July 1, 2010 at 10:18 PM

Graham - great\! You probably saw Danny Adair's \(Conf Director\) comments re. his having updated the site as tweeted here: http://twitter.com/kiwipycon/status/17488165439. One of the organising committee members is also planning on organising a bus from Auckland to Waitangi. You could try dropping him an email here: g dot kloss at massey dot ac dot nz.

### Sandip Bhattacharya - September 7, 2010 at 8:02 PM

I was setting up wsgi in my shared hosting account the other day, and I also wanted to use my virtualenv in my account.  
  
Referencing from some sources around the web, it seems that the following at the top of the .wsgi file eliminates all the 'site' module and PYTHONPATH issues while using wsgi.  
  
INTERP = "/path/to/virtualenv/bin/python"  
if sys.executable \!= INTERP: os.execl\(INTERP, INTERP, \*sys.argv\)

### Graham Dumpleton - September 7, 2010 at 8:23 PM

@sandip For mod\_wsgi that would likely only cause the process to crash in some bad way. In future you would be better off using the mailing list to start a discussion about such a thing. Here isn't the right place.

### Johny JKJK - October 17, 2010 at 3:26 AM

Fantastic presentation which show exactly what I expect. Thanks\!

