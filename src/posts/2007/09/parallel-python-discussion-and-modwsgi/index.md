---
layout: post
title: "Parallel Python discussion and mod_wsgi."
author: "Graham Dumpleton"
date: "2007-09-12"
url: "http://blog.dscpl.com.au/2007/09/parallel-python-discussion-and-modwsgi.html"
post_id: "971657769665265196"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 3
published_timestamp: "2007-09-12T08:39:00+10:00"
blog_title: "Graham Dumpleton"
---

[](http://www.artima.com/weblogs/viewpost.jsp?thread=214325)The sad fact is that many high profile Python developers like to ignore what has been done in relation to the use of Python in conjunction with the Apache web server. I'm not sure whether this is because of a bias towards pure Python solutions, whether they just can't be bothered, or that they simply don't have the time to look properly at what is being done by others. Anyway, the latest comment which shows a lack of understanding of what already exists comes from Guido himself in his [blog](http://www.artima.com/weblogs/viewpost.jsp?thread=214325) entry made in response to Bruce Eckel's [blog](http://www.artima.com/forums/flat.jsp?forum=106&thread=214112) on Python 3K or Python 2.9.  
  
In his blog entry Guido says the following in relation to concurrency in Python:  
  
"Another route I'd like to see explored is integrating one such solution into an existing web framework \(or perhaps as WSGI middleware\) so that web applications have an easy way out without redesigning their architecture."  
  
Reality is that this ability to spread a Python based web application across multiple processes already exists with Apache when using [mod\_python](http://www.modpython.org/) or [mod\_wsgi](http://www.modwsgi.org/). This is because Apache itself \(on UNIX at least\) is implemented as a multi process web server. As such, incoming requests are distributed across the numerous Apache child processes dealing with requests. When using Apache at least, there is therefore no problem with properly utilising multiple core processors. As I have also blogged before in '[Web hosting landscape and mod\_wsgi](/posts/2007/07/web-hosting-landscape-and-modwsgi/)', the fact that a lot of other stuff is also going on in Apache at the same time, which is not implemented using Python, adds to the fact that for solutions embedding Python into Apache the GIL is not the big issue people think it is.  
  
In addition to solutions such as mod\_python and mod\_wsgi, which embed Python into the Apache child processors, there are also other solutions such as [mod\_fastcgi](http://www.fastcgi.com/) and daemon mode of [mod\_wsgi](http://www.modwsgi.org/), which are able to create multiple distinct daemon processes to which requests are proxied. This again results in requests being distributed across multiple processors.  
  
The WSGI specification even takes into consideration that such multi process web servers exist through the existence of the 'wsgi.multiprocess' flag in the WSGI environment passed to a WSGI application.  
  
Now, it may be the case that Guido more had in mind the ability within a WSGI application, using WSGI midleware, to on forward some subset of URLs to another processes. But then, even this can already be achieved using existing WSGI middleware for proxying requests to another web server. To use such a feature though means making a conscious decision and changing the code of your application, although using something like Paste Deploy may at least limit that to being a configuration change.  
  
In addition to proxy middleware, mod\_wsgi also has an ability to divide up an existing monolithic application to run across multiple processes. In the case of mod\_wsgi no changes at all need to be made to the structure of the WSGI application. Instead, the mapping of a particular subset of URLs to a distinct process is handled by mod\_wsgi even before the specific WSGI application is invoked.  
  
As an example, imagine that one was running Django and wanted all the '/admin' pages to be executed within the context of their own process. To achieve this, all that is required is for the following Apache configuration to be used:  

    
``` 
WSGIDaemonProcess django processes=3 threads=10  
WSGIDaemonProcess django-admin processes=1 threads=10  
    
WSGIProcessGroup django  
    
WSGIScriptAlias / /usr/local/django/mysite/apache/django.wsgi  
    
<Location /admin>  
WSGIProcessGroup django-admin  
</Location>
``` 

This results in the bulk of the Django application being distributed across 3 multi thread processes. Using a combination of the 'Location' and 'WSGIProcessGroup' directives, the process group to be used for '/admin' URL is then overridden. The result is that any handlers related to '/admin', and URLs underneath that point, are instead executed by a different process.  
  
So, the ability for distributing execution of a Python web application across multiple processes and thereby reducing the impact of the Python GIL already exists. Future changes to mod\_wsgi should make this even more flexible, with the introduction of transient daemon processes and an ability to anchor a user session to a specific daemon process using cookies where required.

---

## Comments

### Guido van Rossum - September 13, 2007 at 5:07 AM

This is cool \(as long as you're deploying using Apache\). But it seems the author of the "open letter" wasn't aware of this or rejected the idea. Yo might want to leave a comment there pointing to this blog entry.

### Bruce Eckel - September 18, 2007 at 5:45 AM

I am fairly ignorant of the inner workings of apache, but I find it interesting that it uses a process rather than thread approach. And that processes seem to work pretty well.

### Graham Dumpleton - September 18, 2007 at 6:47 AM

It can use both, see:  
  
http://code.google.com/p/modwsgi/wiki/ProcessesAndThreading

