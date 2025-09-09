---
title: "Commodity shared hosting and mod_wsgi."
author: "Graham Dumpleton"
date: "Monday, July 30, 2007"
url: "http://blog.dscpl.com.au/2007/07/commodity-shared-hosting-and-modwsgi.html"
post_id: "3855201164690597492"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 4
published_timestamp: "2007-07-30T19:46:00+10:00"
blog_title: "Graham Dumpleton"
---

The first release candidate for mod\_wsgi has been out a little while now and so far there has not been a single complaint about its stability. The one and only bug reported has been a rather silly mistake related to decoding the optional umask for daemon processes. Although the signs are good, will web hosting companies want to use it anyway?  
  
In answering this question one has to look beyond stability concerns and look at whether the functionality provided by mod\_wsgi fits the requirements of a web hosting environment. To work this out one has to consider the different types of commercially available web hosting environments on offer.  
  
The most full featured web hosting environment is a dedicated server or virtual private server with root access. In this case the user has full access to the operating system and can install whatever they want. Because there are no real restrictions, a user would be free to install mod\_wsgi and configure it so as to run applications in embedded mode, daemon mode or a combination of both. The only issue here is whether the user feels that mod\_wsgi offers a better solution to mod\_python, mod\_fastcgi or other such solutions. The web hosting company in this case doesn't affect the actual user's decision.  
  
Cheaper options than such a full featured web hosting environment are available, but as the cost comes down, the restrictions on what the user can do also increases. The next step down of note is what I'll call advanced shared hosting. This is where many users share the same system but each user is provided with their own Apache instance running on a dedicated port. All these distinct Apache instances then sit behind a proxy of some form listening on the standard HTTP port. Because each user gets there own Apache instance, it can run as that user and therefore the user still has a reasonable measure of control over the server. As such the user could once again most likely choose to use mod\_wsgi and configure it so as to run applications in embedded mode, daemon mode or a combination of both  
  
At the lower end of the scale is commodity shared hosting. This is where applications created by many different users are hosted together using a common Apache instance. The main problem with sharing a single Apache instance in this way is that all code runs as the user that Apache runs as. The consequences of running all code as a single user is that different users applications can interfere with each other. To avoid the problems that can result from this, any hosting solution for dynamic applications must be able to separate applications so that they run in distinct processes, running as the user that is the owner of the application.  
  
When using mod\_wsgi for hosting Python applications, daemon mode can be used to create daemon processes running as distinct users, with WSGI applications being delegated to an appropriate daemon process group. Although this feature is available, in the initial version of mod\_wsgi the configuration of the daemon processes is effectively static, with the number of daemon processes and the user they would run as needing to be predetermined in advance. This would be okay for small web hosting companies who specialise in Python web hosting and who manually change the Apache configuration when each new site is added, but it becomes a problem where site configuration is more automated and restarts of Apache are avoided at all costs.  
  
One way around this problem would be to configure some number of spare daemon processes in advance, with each such spare daemon process running as a user which hasn't as yet been allocated to a specific customer. When a new customer arrives who wants to be able to run a Python site, they would be given a user id corresponding to one of the spare daemon processes. Actual mapping of any WSGI applications running under the new users site would then be performed using a rewrite map which draws data from some form of database that can be dynamically updated without restarting Apache.  
  
Although this may be viewed as a bit of a kludge, this approach would probably be quite acceptable for web hosting companies who specialise in providing hosting for Python applications. This is because it is likely that they would already have in advance worked out how many different Python application instances a machine could likely accommodate. This may be based on a general rule of thumb, or by applying strict quotas on the amount of memory that any one Python application can use, with any application process being killed off and restarted when the set memory limit is reached. That there may be some number of spare daemon processes running at any one time wouldn't be an issue as the amount of memory they use would be quite small, much less than the limit which would be imposed on a users application.  
  
Unfortunately, not all web hosting companies are going to want to specialise in providing web hosting for Python applications, nor are they going to want to dedicate specific machines to be used for just that purpose. Instead, they will want to take their existing infrastructure, most likely designed to support PHP applications, and try to use it concurrently for hosting Python applications. Their goal in doing this is will be to maintain their existing site density, thereby still retaining their existing cost structure.  
  
What such web hosting companies will want to avoid as much as possible is the need to run long lived daemon processes. This is because even if only a small percentage of the possibly thousands of sites they may host want to use Python, the overall memory requirements will increase much more significantly than if they were PHP applications. This would likely result in them having to reduce the number of sites they can host on the same hardware and increase their costs.  
  
In addition to not wanting to run long lived daemon processes, the fact that the number of daemon processes to be run, and the users they run as, currently has to be predefined would make it too hard to manage. This is because such large scale hosting will load balance a large number of sites across many machines in a cluster. As a result it would impractical to have to update and restart every Apache instance in the cluster when more daemon processes need to be added.  
  
As a result, for such large scale web hosting a more simplistic configuration mechanism is required where additional daemon processes can be added dynamically without changes needing to be made to the static configuration. Further, such daemon processes need to be able to be setup to be transient in nature. That is, they need to be able to shutdown automatically if they are idle for some, usually quite short, predefined period. By doing this, the memory used by the daemon process will be released, reducing the possibility that all of physical memory will be used up and the operating system needing to swap memory to disk.  
  
Thus, so far as commodity web hosting goes, mod\_wsgi would probably be a reasonable solution for web hosting companies who specialise in providing hosting for Python applications and who dedicate machines for this purpose. It is as yet not suitable for large web hosting companies who aren't specialists in Python web hosting, who want to maintain one homogeneous machine configuration across all their machines which is suitable for hosting varied web application frameworks and languages, and who wish to run with the highest site density possible so as to reduce costs to the maximum.  
  
Although adding support for transient daemon processes to mod\_wsgi may entice these latter type of web hosting companies to use mod\_wsgi, this goes contrary to the preferred option with Python applications of maintaining a long running daemon process. As such, if it were adopted, it would be to the detriment of the user experience due to the possibly long startup times which may be encountered if an application is infrequently used and is always having to be restarted due to being killed off.  
  
So, although the addition of support for transient daemon processes is being looked at for a future version of mod\_wsgi, it is more being added to provide additional flexibility for users of dedicated systems. If configuration can be made quite simple then large scale web hosting might well adopt it, but frankly, you may well get what you pay for as far as the user experience that people interacting with your site will have.  
  
If you are serious about providing a high quality site, you are probably better off spending a bit more money each month and get a site from a web hosting company that specialises in Python web hosting and provides true long lived daemon processes for running your site. This statement would apply equally whether it is mod\_wsgi that is used or other solutions such as mod\_fastcgi, as large scale web hosting isn't really designed to accommodate the additional demands of Python web applications, and for the time being at least, is always going to be tailored more to PHP applications.

---

## Comments

### Shane Hathaway - August 8, 2007 at 9:07 AM

Graham,  
  
It seems that for several years, the whole Python community has been searching for a way to make Python web applications as easy to host as PHP applications. I think you and the WSGI inventors may have found the solution. If everything works out, before long we'll finally see inexpensive web hosts offer WSGI support. That will be a great accomplishment\!  
  
Other than testing, do you need any help?  
  
FWIW, I intend to see what it takes to run Zope and Plone in mod\_wsgi. I know it's possible, but I don't know whether it will scale well.

### Graham Dumpleton - August 10, 2007 at 9:13 PM

Trying to get Zope/Plone to run on top of mod\_wsgi is something I haven't tried, so if you get it working please let me know via the mod\_wsgi Google group. Would love to include a recipe on the site for how to configure mod\_wsgi for Zope.  
  
As far as any help I need, that information on Zope would be good in itself. Everything else is more or less under control at this stage.

### Ahmad Alhashemi - September 6, 2007 at 2:49 AM

Can something like freezing or pickling the idle Python process make start up times faster than shutting down/starting up? I bet it won't only be faster but will put less load on the machine.

### Graham Dumpleton - September 6, 2007 at 9:05 AM

As the processes handling the WSGI application requests are persistent between requests and one wouldn't typically need to be restarting them that often, there wouldn't probably be that much benefit from trying to freeze or pickle the idle process.  
  
That said, it doesn't mean that specific WSGI applications couldn't use such techniques for data within their scope of control. But then more often that not, using something like memcached to cache data between invocations of a process would probably work better and is a more proven technology.

