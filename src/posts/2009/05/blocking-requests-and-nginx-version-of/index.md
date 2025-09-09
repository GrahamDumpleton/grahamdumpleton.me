---
layout: post
title: "Blocking requests and nginx version of mod_wsgi."
author: "Graham Dumpleton"
date: "2009-05-08"
url: "http://blog.dscpl.com.au/2009/05/blocking-requests-and-nginx-version-of.html"
post_id: "5990274690108767033"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'nginx', 'python', 'wsgi']
comments: 14
published_timestamp: "2009-05-08T14:53:00+10:00"
blog_title: "Graham Dumpleton"
---

My own [mod\_wsgi module for Apache](http://www.modwsgi.org/) has been available in one form or another now for over two years. What many people don't know is that there is also a [mod\_wsgi module for nginx](http://hg.mperillo.ath.cx/nginx/mod_wsgi/file/tip/README), although development on it has appeared to have stalled with no changes having been made for quite some time.

  


The nginx version of mod\_wsgi borrows some code from my original Apache version, but obviously since the internals of Apache and nginx are very different, the main parts of the code which interface with the web server are unique. Although I condoned use of the source code, I do wish I had insisted from the outset that it not be called mod\_wsgi due to the confusion that has at times arisen.

  


Although development on the nginx version of mod\_wsgi appears to no longer be happening, this isn't stopping people from using it and many are quite happy with it. The question is whether they really understand anything about how nginx works and the shortcomings in how nginx and mod\_wsgi work together.

  


Admittedly the author of the mod\_wsgi module for nginx has been up front in pointing out that because nginx is asynchronous, and with WSGI not designed for such a system, that once the WSGI application is entered all other activity by the web server is blocked. The recommendation resulting from this is that static files should not be served from the same web server. Use of multiple nginx worker processes is also suggested as a way of mitigating the problem.

  


All well and good, but unfortunately there is a bit more to it than that and although people may think that by using nginx underneath they are going to get the fastest system possible, it is debatable as to whether for real world applications that is going to be the case.

  


To understand the problems with the mod\_wsgi module for nginx it is helpful to first look at how Apache works.

  


When using Apache on UNIX systems there is a choice of multiprocessing modules \(MPM\). The two main options are the [prefork](http://httpd.apache.org/docs/2.2/mod/prefork.html) and [worker](http://httpd.apache.org/docs/2.2/mod/worker.html) MPM. In both cases multiple processes are used to handle requests, but where as prefork is single threaded, worker uses multiple threads within each process to handle requests. On Windows the [winnt](http://httpd.apache.org/docs/2.2/mod/mpm_winnt.html) MPM is the only option. It is multithreaded as well, but only a single process is used.

  


The important thing about Apache, no matter which MPM is used, is that a connection is not accepted from a client until a process or thread is available to actually process and handle the request. This means that if a prefork MPM process is busy, or if all threads in a worker MPM process are busy, then that process will not accept any new connections until it is ready to. This ensures that any new connections will always be handled by another free process and you will not end up with a situation where a connection is accepted by a process, but it isn't actually able to process it at that time.

  


Because nginx is an asynchronous system based on an event driven system model, things work a bit differently. What would normally occur is that connections would be accepted regardless, although nginx does enforce an upper limit as defined by 'worker\_connections' setting. The work on processing all those concurrent requests would then be interleaved with each other by virtue of work being stopped on one and changed to another when the first would otherwise block waiting on network activity or some other event.

  


For serving of static files an asynchronous system is a good model, allowing more concurrent requests to be handled with less resources. As to mod\_wsgi for nginx however, the picture isn't so rosy.

  


The basic problem is that you are embedding within an asynchronous system a component with is synchronous. That is, the WSGI application doesn't cooperate by giving up control when it would block on waiting for some event to occur. Instead it will only hand back control when the complete request is finished. This means for example that if a request takes one second to complete, for that one second, the web server will not be able to do any processing on behalf of the concurrent requests that the process has already accepted.

  


The recommendation as mentioned above is thus to use multiple nginx worker processes by setting 'worker\_processes' in configuration and push handling of static files onto a completely different server instance. In practice this is not enough however and you still risk having some percentage of requests being blocked while some other request is being handled.

  


The reason this occurs, is that the synchronous nature of a WSGI application effectively means that mod\_wsgi for nginx is not much different to using single threaded prefork MPM with Apache. The big difference though is that nginx will greedily accept new connections when it should only really accept one at a time commensurate with how many concurrent connections it can truly process through the WSGI application at the same time.

  


End result is that all those connections which it greedily accepts between calls into the WSGI application will be processed serially and not concurrently. So, if you get a request which takes a long time, all those other requests will block.

  


The use of multiple nginx worker processes is supposed to mediate this, but in practice it may not. This is because new connections aren't going to get distributed out to the worker processes evenly. Instead you may actually see a tendency for the last active process to get precedence, as that process will already been in a running state and thus is quicker to wake up and detect that a new connection is pending. As a consequence, most of the time the new connection will be accepted by the same worker process rather than being accepted by another.

  


If you are running a finely tuned Python web application where all requests are well under one second you may not notice any delays as a result of individual requests blocking, but if the handling of some requests can take a long time, such as a large file transfer, then the effect could be quite dramatic with distinct users seeing quite noticeable delays in getting a response to their own unrelated requests.

  


Now I am sure the author of mod\_wsgi for nginx understood all this, but the very little documentation available for it doesn't really say much. In some respects one can get an impression from the documentation that only static file serving is affected by the problem, whereas any concurrent requests, including those for the WSGI application, are affected. Use of multiple nginx worker processes may help, particularly on a machine with multiple processors, but the benefit may be quite limited.

  


Overall I am not sure I would want to trust a production application to mod\_wsgi for nginx due to the unpredictability as to whether requests are going to be blocked or not. As much as Apache may have a larger memory footprint due to use of distinct processes and/or threads to handle requests, at least you are guaranteed that when a connection is accepted, that it will be processed promptly.

  


In respect of the greater memory usage of Apache, it also needs to be reiterated that the additional memory overhead of Apache is usually going to be a relatively small percentage when viewed in respect of the overall memory usage of today's even fatter Python web applications. So, anyone who likes to disparage Apache by saying it is fat, is living in a bit of fantasy land when it comes to hosting Python web applications. It simply isn't the big deal they like to make out it is. It often actually just shows they don't know how to configure Apache properly.

  


Finally, to those people searching for the elusive fastest web server in the world, I really suggest you give up. That isn't going to be where the bottleneck is in your application anyway. So, rather than wasting time trying to work out which system may be faster, just choose one, any one, and get on with actually optimising your application, database and caching systems instead. Work on those areas and you will see much more dramatic gains than the few piddly percent difference in request throughput you may get from using a different web hosting mechanism.

---

## Comments

### mike barton - May 8, 2009 at 5:46 PM

I can't figure out why anyone would use mod\_wsgi on nginx.  
  
If you add in eventlet, the model becomes a little more interesting, but it's not all that mature and it adds a fair amount of administrative and development overhead.

### andy - May 8, 2009 at 7:33 PM

I'd be particularly interested in how you think Apache and mod\_wsgi compares with a nginx and fcgi setup.   
  
In my case I'm trying to run multiple Django apps in a constrained memory shared environment so memory usage is critical. I was considering switching to the latter setup but I don't know how much difference it will make.  
  
Ironically there is a lot more info out there on fiddling with Web server configuration than there is on how to reduce Python or Django's memory usage.

### None - May 8, 2009 at 7:53 PM

Presumably phusion passenger on nginx \(which can apparently run WSGI Python applications as well, though it isn't well documented or supported yet\) works around these issues by managing its own separate set of application processes and queuing up and distributing requests between them. Is there anything concerning about that approach?

### recordus - May 8, 2009 at 9:12 PM

I am running WSGI apps with Nginx + mod\_wsgi in testing environment now, It's great to know these things.

### Laurent Debacker - May 11, 2009 at 12:33 AM

HTTP requests for dynamical content concerns only the main HTML page. The dozens or hundred of required files \(images, CSS, JS, flash, etc\) to display a web page will significantly faster to load using an efficient HTTP server. Every bit counts, and if a single bit is bad, the whole stuff will be slowed down.  
  
Regarding memory, my NGINX uses 8MB of RAM, and my Python app uses 10-14MB \(thanks Werkzung\), when idle.

### Graham Dumpleton - May 11, 2009 at 9:45 AM

@andy: Apache/mod\_wsgi daemon mode is like fastcgi in many respects. You aren't going to see a great deal of difference. As I said in the post, the web hosting mechanism isn't usually going to be the bottleneck.  
  
For reducing memory, one popular setup is to have nginx front end serving static files, proxying dynamic requests to Apache/mod\_wsgi with WSGI applications running in daemon mode.  
  
@Simon: Phusion Passenger for WSGI applications is also not much different in some respects to Apache/mod\_wsgi daemon mode in the area of process management. Also, I still need to look at the detail of Phusion Passenger, but to say it queues up requests is either marketing nonsense or they have gone and implemented it in an odd way.  
  
How such systems generally work is that all worker processes listen on the same socket. Accepting connections, if necessary, is mediated by a cross process accept mutex. This just ensures that only one process actually gets the next connection. What governs distribution across the process is merely which process manages to lock that mutex when it is given up by last process. As to the queue, this is just the fact that listener sockets have a backlog queue. That is, it is a feature of listener sockets in the operating system that pending connections will queue up until processes actually accepts connection. If this didn't occur, then most connections would get rejected as processes not likely to be ready at instant that a client connections.  
  
If Phusion Passenger has implemented some alternate queueing and load balancing system, then they would have to be implementing an extra level of proxying, which is going to act to slow down handling of new connections and potentially introduce an extra hop across which data has to be sent and received. Further investigation would need to be done, but would be surprised if they had not used the more traditional approach to this.  
  
So, a means of queueing connections isn't unique to Phusion Passenger, every hosting mechanism does it.

### Martin Aspeli - May 16, 2009 at 8:36 PM

Hi Graham,  
  
I mainly want to use nginx because it is so much simpler to configure and deploy, not necessarily for raw speed.  
  
Right now, I use nginx for virtual hosting/proxying with a separate server hosting Plone. I'm not sure if that would have the same problems with blocking or not.  
  
I had hoped that as WSGI becomes a more mainstream deployment option for Plone, something like mod\_wsgi would be a good option to simplify deployment \(no need for a separate process\), but this post made me realise that that probably is a false hope.  
  
Martin

### Graham Dumpleton - May 16, 2009 at 9:05 PM

@Martin: There is no issue with the front end nginx where it is acting as a proxy to a distinct HTTP server which runs your WSGI application. Same goes where nginx is proxying to a fastcgi process running your application.  
  
The only issue is where the distinct HTTP server is a nginx instance with nginx/mod\_wsgi and that is where your application is running as an embedded application. The problem in this case is still not with the front end nginx, but with the backend nginx running nginx/mod\_wsgi and your embedded application.  
  
Thus, using nginx as proxy front end to your application running in distinct Apache/mod\_wsgi setup is fine, as would be using nginx to proxy to your application running on top of CherryPy HTTP/WSGI server or Paste HTTP/WSGI server.

### Hongli - May 18, 2009 at 1:15 AM

@Graham: Actually Phusion Passenger does have its own queue, independent of the OS's socket backlog. We use this fact to implement good load distribution between the workers.  
  
I'm not sure whether it counts as an "extra proxy" so far the performance penalty turns out to be minimal.

### Graham Dumpleton - May 18, 2009 at 11:24 AM

@Hongli: Depends on how you have implemented it. Your use of 'queuing' just may not be the appropriate way of describing it because of the connotations of the term and really it is just a conventional load balancer and should be described as such, without a need to being up 'queuing'. I'll followup when I get a chance to look at your code and see how it is done.

### babul - September 6, 2009 at 6:23 PM

Hi Graham,  
  
Firstly thank you for the many EXCELLENT wsgi-related articles and posts you put throughout the interwebs as one often comes across your insights when searching for wsgi info and given your the project lead it's often very well thought out.  
  
Anyway my question, what are your thoughts on the Cherokee webserver? Currently you argue against nginx due to its event model and recommend Apache as it is more determinable, especially for use with python web frameworks, but what about Cherokee? Also what about Cherokee+PHP instead of python \(e.g. for running wordpress blogs\), any issues you see?

### Graham Dumpleton - September 7, 2009 at 10:33 AM

Cherokee and nginx both support fastcgi. There is nothing wrong with using fastcgi support in those two servers. I was only pointing out the issues with trying to use an embedded solution as nginx/mod\_wsgi uses, on top of an event driven system. The fastcgi model has applications run in a separate daemon process, so no issues.  
  
Only thing I would say to be careful of is grandiose claims that fastcgi on one platform or another is faster than anything else on the planet. Reality is that the web server layer is not where the bottleneck is and any difference between speeds of the base hosting mechanism is nearly always going to be swallowed up completely within the overheads of your own application, its rendering engine and any database access.  
  
So, choosing a web hosting solution based on perceived speed is stupid, you are better off just choosing whatever hosting mechanism you feel you understand best and which you find easiest to manage. By being easier to manage and configure, you can then spend your time on the real problem, which is making your application run better.

### jim - June 7, 2011 at 6:21 PM

I wonder what you think of nginx + uwsgi? I have been impressed with the simplicity of config and ease of setup, can you comment on the internals of uwsgi? I admit that i haven't read the source.  
  
Cheers\!

### Lincoln Bryant - August 31, 2011 at 3:05 AM

Great article. Like several of the commentors, I am switching over an Apache/mod\_wsgi Django app to use nginx/fastcgi. The reason for this is that the app's primary purpose is to accept file uploads, and nginx has modules to write uploaded files to disk and report there progress to the client, whereas Apache/mod\_wsgi delegates this IO to Django and makes the expensive processes last far longer. We have followed a model very similar to this excellent guide http://fightingrabbits.com/archives/210  
  
However, I prefer the familiarity of Apache and Django recommends it now. I was wondering if you know of a way to delegate the writing of uploaded files away from the WSGI application to Apache. While i greatly enjoy Django's uploaded file implementation from a code perspective, like you the bottleneck here is app-centric, and we need to prevent a memory hogging process from bring the one who writes these incoming files.

