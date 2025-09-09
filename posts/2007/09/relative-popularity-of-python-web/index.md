---
title: "Relative popularity of Python web frameworks."
author: "Graham Dumpleton"
date: "Sunday, September 2, 2007"
url: "http://blog.dscpl.com.au/2007/09/relative-popularity-of-python-web.html"
post_id: "1857107063185613217"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 3
published_timestamp: "2007-09-02T09:12:00+10:00"
blog_title: "Graham Dumpleton"
---

The battle between the different Python web frameworks over which is technically best is always interesting to watch. In watching these battles and monitoring the various discussion forums for each, one gets a pretty good feel as to which at least is winning the popularity contest. All the same it would be nice to see some actual figures to backup the assumptions one makes. One way that I can see of doing this is to look at the number of unique visits to the [mod\_wsgi ](http://www.modwsgi.org/)documentation describing how to host each framework on top of mod\_wsgi. Although there be lots of caveats, the result of doing such an analysis is pretty well what I expected, with Django coming out on top.  
  
The web frameworks \(or non frameworks as some like to call themselves\) for which instructions are currently provided for mod\_wsgi are [CherryPy](http://code.google.com/p/modwsgi/wiki/IntegrationWithCherryPy), [Django](http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango), [Karrigell](http://code.google.com/p/modwsgi/wiki/IntegrationWithKarrigell), [Pylons](http://code.google.com/p/modwsgi/wiki/IntegrationWithPylons), [TurboGears](http://code.google.com/p/modwsgi/wiki/IntegrationWithTurboGears) and [web.py](http://code.google.com/p/modwsgi/wiki/IntegrationWithWebPy). Instructions for each have all been up for more than a month on the mod\_wsgi web site, so for the analysis I have taken the statistics for the month of August. For that period, the number of unique page views against each was as follows:  
  
**Package**| **Count**  
---|---  
Django| 332  
Pylons| 96  
TurboGears| 89  
web.py| 75  
CherryPy| 71  
Karrigell| 34  
  
  
FWIW, the mod\_wsgi documentation also provides instructions for using [Trac](http://code.google.com/p/modwsgi/wiki/IntegrationWithTrac) and [MoinMoin](http://code.google.com/p/modwsgi/wiki/IntegrationWithMoinMoin) on top of mod\_wsgi. The number of unique page views for these packages was:  
  
**Package**| **Count**  
---|---  
Trac| 324  
MoinMoin| 44  
  
  
Although interesting, these results cannot tell the whole picture for a variety of reasons. These include whether or not respective packages actually reference mod\_wsgi \(or how prominently\) as a hosting solution in their own documentation and how often I have personally referred to mod\_wsgi on each packages mailing lists as an alternate solution to a particular persons problem.  
  
Beyond those issues, there are actually a number of technically related reasons as to why for a particular package there may not have been as much traffic to the mod\_wsgi web site.  
  
The main issue is that although all are capable of being hosted using Apache and mod\_wsgi, of the web frameworks only Django promotes strongly the idea that for production sites one should use Apache. At the moment the recommendation in that respect is mod\_python, but at least the idea of using Apache is not a foreign concept. Thus for Django, the builtin web server is only seen as being a practical hosting solution for a development instance of Django.  
  
For most of the other packages they instead see the builtin web server they provide as being capable enough to support a production site. Thus, although they may describe or reference other ways of hosting a site developed using the package, the only way that Apache generally factors into the equation is as a proxy to their own web server and as a means of hosting static files.  
  
As far as using a web server implemented in pure Python as opposed to hosting on top of Apache, there does also seem to be a reasonable amount of bias against using Apache. In part this appears to be due to some ignorance as to the pros and cons of using Apache and how to set it up properly, but also partly because of Python zealotry. In other words, just like every programming language, some are so strongly enamoured by Python that they simply cannot except that there are other ways of doing things.  
  
Such a pro Python only stance could actually be seen as being detrimental to the chances of Python being accepted within commodity web hosting. This is because commodity web hosting companies will not find it acceptable that they would have to setup and support pure Python back end web server applications to which they merely proxy requests.  
  
Instead, commodity web hosting want a system that can be easily integrated with their existing Apache installations \(normally setup for PHP\), yet doesn't place undue memory requirements and overhead on Apache. Above all, the ability to provide hosting for Python web applications must be very simple to configure and fit in with the large scale automated systems they have for configuring the many sites they would host using one Apache installation.  
  
Thus in some respects, packages which try to steer developers to always using the builtin web server are only going to make it harder for that package to be accepted by web hosting companies. Some thought must be given to ensuring that packages are easy to deploy and setup under Apache in a web hosting environment. If this is not done, then you will not see those packages being supported by web hosting companies and as a result people will simply move to those packages which have put in the effort to make it easy to deploy under Apache.

---

## Comments

### fumanchu - September 2, 2007 at 2:52 PM

Of course you post this the same day I add a flag for using mod\_wsgi in the CherryPy test suite. ;\) Once I track down a couple of errant bugs, I think we'll be quite happy to promote mod\_wsgi to the fullest.

### Graham Dumpleton - September 2, 2007 at 3:24 PM

Although I have a vested interest in mod\_wsgi, I am actually partly looking at this in the broader sense of packages providing good support and documentation for working with Apache no matter whether that be using mod\_scgi, mod\_fastcgi, mod\_fcgid, mod\_proxy\_ajp, mod\_proxy or mod\_wsgi.  
  
What I want to do, and have started discussions with someone else about already, is getting together a group of people who would be interested in doing a proper broad ranging comparison of all the major WSGI hosting solutions available right across Apache, lighttpd and nginx. This would include mod\_python, mod\_wsgi, fastcgi/scgi and proxying solutions.  
  
The idea is to compare and contrast the different approaches and list the pros and cons of each. Also want to come up with a broad range of benchmarking tests to compare how the hosting method affects performance of different common tasks implemented on top of WSGI.  
  
For example, straight requests, form posts and file uploads, mixed dynamic and static file requests, streaming etc. This should obviously include testing of different loadings such as serialised requests, concurrent requests at various rates etc so as to gauge issues such as scalability. The beauty of WSGI is that the exact same code can be used for each test and thus the performance of an individual framework doesn't come in to it.  
  
Other odd things which might be worth testing is the effect of high level URL mappers implemented by the web server and how much impact mounting a WSGI application at a nested URL vs the root of the web server may impact performance.  
  
Personally I think this sort of good analysis of what is available is sorely needed in the Python community as there is too much conjecture and misinformation circulating. And although some may think the aim is me trying to show whether mod\_wsgi is better than other solutions, it isn't. I already know that mod\_wsgi falls short in as much as it is missing certain functionality in key areas needed for commodity web hosting. Doesn't mean I will not use the information to try and make mod\_wsgi better, and I hope that by getting together such information it may be useful to others as well and prompt improvements to other WSGI hosting solutions as well.  
  
Anyway, I intend blogging about this whole idea another time.

### zephyr - November 17, 2007 at 4:45 AM

syea django is the best framework within the python community.  
Actually its not only good framework in python but its a great web framework ever built

