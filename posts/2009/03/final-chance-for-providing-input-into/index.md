---
title: "Final chance for providing input into mod_wsgi 3.0."
author: "Graham Dumpleton"
date: "Sunday, March 8, 2009"
url: "http://blog.dscpl.com.au/2009/03/final-chance-for-providing-input-into.html"
post_id: "690190448619552172"
blog_id: "2363643920942057324"
tags: ['mod_wsgi']
comments: 6
published_timestamp: "2009-03-08T09:50:00+11:00"
blog_title: "Graham Dumpleton"
---

I am starting to get close to winding up development work on [mod\_wsgi](http://www.modwsgi.org) 3.0. If you had any thoughts about changes or new features you would like to see, now is your last chance.

  


If you want to know what changes have already been made for mod\_wsgi 3.0, then see:

  


<http://code.google.com/p/modwsgi/wiki/ChangesInVersion0300>

  


As well as still having to fix a few issues, am also giving consideration to X-Sendfile support for daemon mode, support for fixing up WSGI environment based on X-Forwarded-? header information, better integration with Python logging module and a few other things.

  


In respect of documentation, yes I know it still needs more work, so no need to ask for better documentation. :-\)

  


BTW, I am also slowly preparing a mod\_wsgi [2.4](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0204) release with various back ported fixes as well.

  


If you have any quick feedback, then post a comment here. If what you want is a bit more complex, then use the [mod\_wsgi](http://groups.google.com/group/modwsgi) group on Google Groups.

  


Thanks.

---

## Comments

### xndxn - March 9, 2009 at 8:34 AM

HttpRequest with chunked encoding supported by mod\_wsgi if possible \(I don't know if this task falls into this application or mod\_python\)...   
  
But this will help people a lot to use Python as a server side scripting langage for mobile devices.  
  
If you are not aware of the issue maybe this will help http://groups.google.com/group/django-users/browse\_thread/thread/dda2008ccbc8cd65/a4bbd3fd14a71311

### Graham Dumpleton - March 9, 2009 at 8:39 AM

@abki: Already included, see http://code.google.com/p/modwsgi/issues/detail?id=1  
  
Note that WSGI specification doesn't support chunked request content, so by using this ability you are stepping outside of WSGI and your application will not likely be portable to other WSGI hosting mechanisms.

### Graham Dumpleton - March 9, 2009 at 8:41 AM

@abki: Do be aware though that frameworks like Django will not be able to make use of this, as they adhere to WSGI specification of only reading what CONTENT\_LENGTH says is available. For chunked request content there is no content length and so they would believe that request content was empty.

### xndxn - March 9, 2009 at 9:01 AM

The thing is that by now, no data at all arrived through the pipe into django. One had to proxy requests to django with a php script \(which is really funny in fact\) \(or add the the right apache modules...\)  
  
I'm not into django middlewares, but one may change the request before it hit the django part which hates non-compliant-wsgi requests.

### xndxn - March 9, 2009 at 9:02 AM

sorry for not having a look to the bug tracker

### Graham Dumpleton - March 9, 2009 at 9:27 AM

Rather than try and fiddle with Django middleware, what you can do is use a WSGI middleware that wraps Django and which detects when it is a chunked request and reads input a block at a time and saves it to a file. It can then modify the WSGI environment passed to Django such that wsgi.input is replaced with reference to open file object onto the temporary file you just save to disk containing the request content. CONTENT\_LENGTH can then also be set in the WSGI environment so Django knows the length. That way Django will be oblivious to fact that it was chunked request content.  
  
Suggest you go over to the mod\_wsgi list on Google Groups and we can discuss that further and can explain how the WSGI middleware wrapper would work.

