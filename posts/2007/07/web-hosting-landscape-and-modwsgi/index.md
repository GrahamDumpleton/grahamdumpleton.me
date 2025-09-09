---
title: "Web hosting landscape and mod_wsgi."
author: "Graham Dumpleton"
date: "Monday, July 2, 2007"
url: "http://blog.dscpl.com.au/2007/07/web-hosting-landscape-and-modwsgi.html"
post_id: "4205006781045390531"
blog_id: "2363643920942057324"
tags: ['mod_python', 'mod_wsgi', 'python']
comments: 13
published_timestamp: "2007-07-02T22:30:00+10:00"
blog_title: "Graham Dumpleton"
---

At the end of last year I described on the mod\_python mailing list various ideas I had for how one could improve the situation with Python web hosting. These ideas were detailed in:  


  * [http://www.modpython.org/pipermail/mod\_python/2006-December/022841.html](http://www.modpython.org/pipermail/mod_python/2006-December/022841.html)
  * [http://www.modpython.org/pipermail/mod\_python/2006-December/022881.html](http://www.modpython.org/pipermail/mod_python/2006-December/022881.html)

A subsequent discussion at the first SyPy meetup in January gave me the drive to follow up on the ideas and since then I have been furiously hacking away, with the result being the [mod\_wsgi](http://www.modwsgi.org/) module I spoke of in those posts.  
  
As I described in those posts I saw mod\_wsgi as only being a first step. Before considering again what one might do beyond mod\_wsgi though, it is worthwhile to look at what mod\_wsgi has become and how the result fits into the web hosting landscape. In particular, does it actually have the potential to improve the lot of Python developers by providing a compelling solution which will be attractive to companies providing commodity web hosting.  
  
To understand this, one needs to look at what features mod\_wsgi provides and specifically the two different modes of operation that have been implemented.  
  
The first mode of operation I tend to refer to as 'embedded' mode. This is where your Python web application runs in the context of the standard Apache child processes. At least in terms of how Python sub interpreters are used, this is the same as how things work with mod\_python. Thus, if you have both mod\_python and mod\_wsgi loaded, applications running under each will share the same process, although they generally would at least run in distinct Python sub interpreters. As far as sharing goes, the process may also be host to PHP or mod\_perl applications as well.  
  
Running applications in the Apache child processes would generally always result in the best performance possible when compared to other alternatives available for using Python with Apache such as mod\_fastcgi and mod\_scgi or even a second web server behind mod\_proxy. This is because the Python application is running in the same process that is accepting and performing the initial parsing of the request from a client. In other words, overhead is as low as it can be as everything is done together in the one process.  
  
In addition to the low overhead, there are also other positive benefits deriving from how Apache works when using this mode. The first is that Apache uses multiple child processes to handle requests. As a result, any contention for the Python GIL within the context of a single process is not an issue, as each process will be independent. Thus there is no impediment when using multi processor systems.  
  
That said, the GIL is not as big a deal as some people make out, even when using Apache with only one multi-threaded child process for accepting requests. This is because the code which handles accepting of requests, determines which Apache handler should process the request, along with the code for reading the request content and writing out the response content, is all written in C and is in no way linked to Python. As a consequence there are large sections of code where the GIL is not being held. On top of that, the same web server may also be serving up static files where again the GIL doesn't even come into the picture. So, more than enough opportunity for making good use of those multiple processors.  
  
The second major benefit comes from Apache's ability to scale up to meet increases in load. The way this works is that Apache will only initially create a certain number of child processes to handle requests. If however the number of requests builds up to the point that the processes wouldn't be able to keep pace, Apache will create additional child processes to meet the demand. It will keep doing this as needs be, although eventually it will stop based on whatever the maximum number of child process is set to, so as not to totally overload your system.  
  
When the number of requests finally starts to drop down once more, to recover resources Apache will start to kill off any child processes now deemed as unnecessary, eventually getting back to the starting level. So it is that Apache is able to comfortably deal with the ebb and flow of demand without unduly choking.  
  
So there is a lot of good to be had from how Apache works when using mod\_wsgi in this mode. At the same time however a number of issues also arise.  
  
The first is that the child processes generally run as a special non privileged user. This means that this user needs to be given access to the files which make up an application or which the application in turn needs to read. This user will also need to be given special access to files or directories the application needs to write any data to. Because Apache may be used to host a number of different applications, it means however that all applications can read files making up any other application and make changes to any writable directories or files used by those other applications which are writable to the user.  
  
The second problem is that although in mod\_wsgi distinct Python sub interpreters are used to keep different applications separate, this isn't fool proof. Problems can arise where different applications attempt to use different versions of a particular C extension module, as Python only loads C extensions once for the whole process and not separately for each sub interpreter. Thus, which application gets to load their version first wins out and when subsequent applications load it, they will get the correct version of any Python wrappers, but that code may not match the API provided by the C extension module itself.  
  
A third more serious problem however, is that since Python supports C extension modules, it would be possible for someone with nefarious intent to load a module which gives them access to other sub interpreters data and code thereby bypassing the firewalls put in place by mod\_wsgi. Such a module would thus allow them to spy into another application, change how it works or steal private information. A very wily hacker may take this even further and poke into the internals of Apache, possibly inserting special handler code into various phases of the request processing cycle, or modifying configuration data used by other modules.  
  
All up, what this means is that although mod\_wsgi goes to great lengths to try and ensure that applications can't interfere with each other, it can't be made completely bullet proof. As a result, 'embedded' mode of mod\_wsgi would only be suitable in situations where the owners of the web servers are also the owners of the applications running under it. At no time would it ever be recommended that 'embedded' mode would be suitable as a basis for running applications owned by different users in a web hosting environment.  
  
Do note that these problems aren't the fault of mod\_wsgi specifically. Some derive from the way Apache works and others from how Python works. Using mod\_python as an alternative will not offer anything better. In fact mod\_python actually has more problems due to the open nature of how it hooks into Apache, thus making it easier to modify the behaviour of Apache and potentially access into other applications or steal private information.  
  
Originally the intent in writing mod\_wsgi was to only target users who also controlled the web server they were using. As a consequence, these issues weren't specifically seen as being a problem that needed to be countered. During the development of mod\_wsgi however, that the existence of mod\_wsgi seemed to be raising the hopes of many that a suitable simple solution for commodity Python web hosting might not be far away, meant that it was necessary to look at how one could address the problems. The end result of this was the addition of 'daemon' mode to mod\_wsgi.  
  
The main difference between 'daemon' and 'embedded' mode is that in 'daemon' mode the actual application code is not run within the context of the Apache child processes, but within separate daemon processes able to be run as a distinct user. Although there is a performance penalty resulting from having to proxy the request through to the distinct daemon process which is to handle the request, because the application is now isolated into a separate process the problems described above for 'embedded' mode are eliminated.  
  
In the first instance, because the daemon process runs as a distinct user, only that user and not the user that the Apache child processes run as will need access to the Python code files that make up the application. The same applies to writable directories or files with them only needing to be modifiable by the user that the daemon process runs as. Thus, any actual Python code or private data pertaining to the application is protected and safe from access by other users of the system.  
  
The only files which would still need to be readable to the user that the Apache child process runs as are any static files such as HTML pages, graphics or media files. This is because the main Apache child process would still provide the service of serving up these files.  
  
The problem with C extension modules being global to a process is also eliminated with 'daemon' mode by the fact that multiple daemon processes can be created and each application assigned to their own process. This ability to isolate an application from others by assigning them to different processes, also prevents hackers from interfering with another users running application.  
  
As a consequence, although 'embedded' mode would not be suitable for a server environment where applications owned by different users need to be hosted together, 'daemon' mode has the necessary protections available to make it safe to use in such a hostile environment and thus it would be suitable for shared web hosting environments.  
  
When one looks at mod\_wsgi a whole, the result is a package which is suitable both for building both high performance web sites and for commodity web hosting. In both cases configuration is simple, with the one application script file being suitable for use in both modes. A complex Python web application may even make use of both modes at the same time. For example, application components requiring better performance could be run in 'embedded' mode, but with other application components requiring special access privileges, which are memory hungry or processor intensive, being delegated off to distinct daemon processes.  
  
In the end, this combination of abilities makes mod\_wsgi a somewhat more flexible platform than other available solutions for developing WSGI applications using Apache. At the same time, because everything is in a single package all managed through Apache, configuration is much simpler and there is no need to install or manage any distinct back end infrastructure.  
  
So, although my original plans didn't envision incorporating a 'daemon' mode, the effort in adding it has been quite worthwhile, with the elusive goal of a way of providing commodity web hosting for Python applications now perhaps being achievable after all. :-\)

---

## Comments

### trepca - July 3, 2007 at 8:58 AM

And what it the difference then between mod\_wsgi-embedded and mod\_python?

### Graham Dumpleton - July 3, 2007 at 9:07 AM

In what way are you wanting to compare mod\_wsgi-embedded to mod\_python? If your interest is in the area of performance then see:  
  
http://code.google.com/p/modwsgi/wiki/PerformanceEstimates  
  
Just realise that once you starting hosting a complex database driven application on either mod\_wsgi or mod\_python, performance is dictated more by the application and the database than the means of hosting it using Apache.

### OmahaPythonUsersGroup - July 3, 2007 at 10:53 AM

Could you speak a bit more about daemon mode, specifically, what mechanism is responsible for ensuring the wsgi app is running and restarting it when/if it dies? apache?  
  
I am quite excited about what you have accomplished so far. The dual mode capabilities is quite impressive.   
  
A second question, with regard to daemon mode, is memory considerations. What can be done to minimize memory utilizations with all of those distinct processes?

### Graham Dumpleton - July 3, 2007 at 11:30 AM

For an actual example of the configuration required to enable daemon mode versus embedded mode see the documentation for integrating Trac with mod\_wsgi:  
  
http://code.google.com/p/modwsgi/wiki/IntegrationWithTrac  
  
In those examples, it is the WSGIDaemonProcess directive which tells mod\_wsgi to start up the indicated daemon process group. The WSGIProcessGroup directive is used to delegate specific URLs to be handled by a daemon process group.  
  
The actual startup of daemon processes will occur when Apache is first started, so the processes will be there ready for when any request arrives which is to be handled by those processes. The actual loading of the WSGI application script file for a URL will only though be loaded within that process the first time a request arrives.  
  
The creation of the processes and subsequent monitoring is all done through the Apache runtime library routines for process management. As such, the main Apache process will monitor the daemon processes and restart them when they die. The main Apache process will also shutdown the processes and restart if necessary, when a 'restart' or 'stop' of Apache is performed.  
  
In respect of memory use, because the application is running in a distinct daemon process, the normal Apache child processes don't incur the memory overhead they would if embedded mode is used. This helps especially if running prefork where a server could create dozens of child processes.   
  
With daemon processes you can also configure them similar to prefork or worker modes of Apache. In other words, you can control how many processes are in a daemon process group for a particular application as well as the number of threads within each process. The number of processes is actually fixed, thus giving more control and better predictability over memory usage.  
  
As an example of using multiple daemon processes see documentation on using Karrigell with mod\_wsgi:  
  
http://code.google.com/p/modwsgi/wiki/IntegrationWithKarrigell  
  
Also check out documentation on configuration directives for other details of controlling the daemon processes, such as user they are run as:  
  
http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives

### trepca - July 3, 2007 at 5:55 PM

I was just curious what exactly makes mod\_wsgi so faster then mod\_python, because they seem very similar.   
Another question about daemon mode :\) I read that if you have users that have slow internet connections it is better to run fastcgi, because the waiting takes a lot of resources. Sounds a bit fishy to me, but what do you think?   
Also, quoting Jacob from Django team:  
"  
Running some simple benchmarks seems to imply that Django under lighttpd and FastCGI outperforms Apache/mod\_python. I need to play around with it some more, but there’s a good chance that Django just doesn’t need the overhead of Apache.  
"  
Comments on that? :\)  
  
Is it possible to use mod\_wsgi on lighttpd or other light http servers? Will it be in the future?  
  
Thanks :\)

### Graham Dumpleton - July 3, 2007 at 8:49 PM

The main reason there is less overhead with mod\_wsgi over mod\_python is that mod\_wsgi is all in C code, whereas module loading and handler dispatch is performed in Python code when using mod\_python.  
  
The claim that mod\_fastcgi is somehow better for slow internet connections sounds rather dubious to me.  
  
Both mod\_fastcgi and mod\_wsgi daemon mode have a very similar model. That is that the Apache child processes receive the request and that is then translated into an alternate request format and proxied through to a backend daemon process. The Apache child process is also involved in relaying back any response.  
  
In both cases you are still tying up a thread in the Apache child process. If you are running prefork MPM, that actually means you are tying up the whole process until the request completes. This is going to be an issue even with other proxying solutions such as using mod\_proxy to a back end web server, or the various mod\_proxy\_\* modules.  
  
There is thus no way that I can see that mod\_fastcgi would have any sort of advantage in this respect over other similar solutions or even mod\_python or mod\_wsgi.  
  
In respect of comparing Apache to lighttpd, I have never done direct comparisons so cannot give any answer which I can personally back up with data. I will say though that I have seen comments made to the effect that benchmarks put out by people in the lighttpd camp comparing it to Apache were a bit suspect in their methodology. I will admit though that this comment was made by people involved with Apache, although they were people who one would expect to be more knowledgeable on web server benchmarking than most.  
  
Anyway, the problem with web server benchmarks is that one can't base it on a single measure as different web servers, and hosting technologies built on top for specific types of applications such as WSGI, will have different strengths and weaknesses depending on the sort of traffic being received. As an example, one of the Python based web servers supporting WSGI that I looked at compared quite favourably when compared to mod\_wsgi for simple serialised requests, but when one hit it with a lot of concurrent requests it did not fare so well. The performance of the Python based web server also suffered noticeably when the WSGI application wasn't mounted at the root of the web server.  
  
The thing is though, little differences in performance in the hosting technology actually mean very little for Python web applications given that the bulk of the overhead will lie in the Python application and any database access. Thus, it is more important to come up with a solution which you find easy to configure and manage, and which gives you the sort of flexibility you might need in respect of scalability or of the need to be able to easily run your applications as a distinct user. In other words, speed isn't everything and if you base your decisions purely on that you may well just make your job harder.  
  
Finally, the implementation of mod\_wsgi is very much wedded with how Apache works and uses the Apache runtime library wherever possible. Thus, it would not be practical to even consider making it work with lighttpd as you would effectively have to start from scratch. So don't expect to see a lighttpd version of mod\_wsgi.

### Gábor - July 3, 2007 at 11:33 PM

hmm... so is there any real difference between let's say mod\_fastcgi + flup and mod\_wsgi in daemon mode?  
  
in other words: why should one use mod\_wsgi in daemon mode, and not mod\_fastcgi? :\)

### Graham Dumpleton - July 4, 2007 at 10:15 AM

In terms of mod\_wsgi being an alternative to mod\_fastcgi, the criticisms one keeps seeing about mod\_fastcgi is that it can be a pain to configure and that its process management doesn't always seem to do the correct thing, with it sometimes spawning more processes than desired or not killing off processes properly.  
  
If you already have mod\_fastcgi/flup running, haven't been having these problems and are comfortable with running it, I wouldn't be suggesting you change it.  
  
In terms of differences, mod\_fastcgi offers some things that mod\_wsgi can't, but conversely, mod\_wsgi offers some things that mod\_fastcgi can't. Thus, one needs to look at what one wants to be able to do.  
  
One benefit of mod\_fastcgi is that because the daemon processes are distinct and uses a separate infrastructure, eg., flup, it can use whatever version of Python it wants to. You could thus run two daemon processes for different applications using different versions of Python. In mod\_wsgi, all your daemon process have to use the version of Python that mod\_wsgi was compiled against. Thus, can be argued that it may be easier to upgrade applications to use a newer Python version when using mod\_fastcgi.  
  
A difference with mod\_wsgi however is that the daemon process can start up multiple sub interpreters within the same process. Thus, one could delegate multiple applications to the one daemon process. If using mod\_fastcgi you wouldn't have a choice but to use separate processes. This ability to run multiple applications in distinct sub interpreters within the same process may especially be of benefit in web hosting environments where they often restrict you as to how many long running processes you are allowed to run.  
  
With mod\_wsgi you also have this simple to use option of being able to designate applications to run either in embedded mode or daemon mode with the same application script file working for both. If using mod\_fastcgi, to be able to support this dual mode of operation you would need to have mod\_python installed as well and scripts would be have to customised for each.  
  
Other differences are that mod\_fastcgi allows remote daemon processes whereas mod\_wsgi would rely on you using mod\_proxy to a back end Apache running mod\_wsgi. Because mod\_wsgi is specifically for WSGI, it is able to setup aspects of WSGI environment automatically, such as whether multiprocess or multithread server.  
  
There are probably a few other differences as well. So, it isn't necessarily a case that one is outright better than the other as there capabilities are different.  
  
FWIW, on my performance scale where mod\_wsgi embedded mode was at 900, mod\_wsgi daemon mode at 500 and mod\_python at 400, when using mod\_fastcgi/flup the result was around 300-350. So, mod\_wsgi daemon mode performance was a bit better, but as I keep saying, these differences in performance don't actually mean much in the end given that the Python application and database access are the biggest overhead.

### Bjorn - July 4, 2007 at 12:05 PM

Just a FYI.  
  
Another important reason to run Python processes in separate processes is to enable troubleshooting performance problems by web application; we've got sites with both PHP and Python components, and it's just impossible to figure out which one is going amok when Apache2 is running at 100% CPU.  
  
Similarly goes for troubleshooting I/O bottlenecks, but in that case Linux throws in another obstacle by not letting you track I/O by process.

### Unknown - July 29, 2007 at 12:14 AM

Your mod\_wsgi stuff sounds way cool\!  
  
I was not too happy with the state of doing python stuff under apache. All stuff seemed to have the one or the other problem and for most, setup was rather complex.  
  
Because of this, we have lots of support requests for MoinMoin installation - most questions not being about MoinMoin itself, but about how to get it working with apache/mod\_python/fastcgi/...  
  
I didn't try mod\_wsgi yet, but I think I'll do soon.  
  
Hopefully, it gets stable and popular enough to have a Debian package soon \(or get part of Apache package?\). :\)  
  
Thanks for your work,  
  
Thomas Waldmann  
MoinMoin wiki project admin

### Graham Dumpleton - July 30, 2007 at 9:15 AM

Someone offered to pursue getting a debian package for mod\_wsgi built and added to the unstable tree. Hopefully this is still progressing. :-\)

### Eric - July 31, 2007 at 4:46 PM

The amount of work you have put into the documentation alone on this project is staggering. I am going through the process now of switching my sites over \(which has been extremely painless\!\)  
  
Thanks for doing this\!

### Unknown - April 25, 2008 at 8:57 PM

•Webmasters may not be able to manage large websites with problems faced on account of sharing huge bandwidth  
•Customers experience unexpected bandwidth problems encountered and are quite a costly affair.   
•Costly incurred on additional charges for lending the extra bandwidth to the customers.   
•Shutting the site causes customers to loose huge business  
palcomonline.com

