---
layout: post
title: "Vertically partitioning Python web applications."
author: "Graham Dumpleton"
date: "2014-02-20"
url: "http://blog.dscpl.com.au/2014/02/vertically-partitioning-python-web.html"
post_id: "8055641613914840250"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'new relic', 'python', 'wsgi']
comments: 3
published_timestamp: "2014-02-20T22:58:00+11:00"
blog_title: "Graham Dumpleton"
---

If you have managed to miss them, I have since the start of the year put out quite a number of blog posts related to [decorators](http://blog.dscpl.com.au/search/label/decorators). These posts covered material I would have covered in a talk I had submitted for PyCon US, but that talk was not accepted. There was actually a second talk I also proposed for PyCon US, but it also was not accepted. This post covers some of what that talk would have covered.

It is unlikely I will be turning the topic of that second talk into another series of posts as I have done for my decorator talk, but some of the underlying issues came up yet again in discussions in the mod\_wsgi mailing list recently, so figured I may as well turn parts of those mailing list posts into a blog post. I am going to try and be more diligent this year in converting more interesting mailing list discussions into blog posts, since mailing lists are generally the last place people go these days to actually try and find information.

# Not all URLs are equal

Now the premise of my talk was that because web application developers will simply deploy their complete web site as one process, that they are actually limiting their ability to have their web application perform optimally. This is because the overall configuration of the web server or container is ultimately going to be dictated by the worst case requirements of small parts of their web application. These parts of their web application may not even be the most frequently visited parts of their web application, but parts which are only infrequently used.

The best example of this is where the handler for a specific URL in your web application has a large transient memory requirement.

As an example, the admin pages in a Django application may not be frequently used, but they may have a requirement to process a lot of data. This could create a large transient memory requirement just for the one request, but since memory allocations from the operating system are generally never given back, this one infrequent request will blow out memory usage for the whole application. This memory once allocated will be retained by the process until the process is subsequently restarted.

Because of this, you could have a stupid situation whereby a request which is only run once every fifteen minutes, could over the course of a few hours, progressively be handled by a different process in a multiprocess web server configuration. Thus your overall memory usage will seem to jump up for no good reason until finally all processes have finally hit a plateau where they have allocated the maximum amount of memory they require to handle the worst case transient memory usage requirements for individual requests.

It can get worse though if you also have multithreading being used in each process. As the response time for a memory hungry URL gets longer and longer, you raise the odds that you could have two such memory hungry requests needing to be handled concurrently within the same process in different threads. What this means is that your worst case memory usage isn't actually just the worst case memory requirement for handling one request against that specific URL, but that multiplied by the number of request threads in the process.

As well as Django admin pages, further examples I have seen in the past where people have been hit by this are the generation of a sitemap, PDF generation and in some cases even RSS feeds where a significant amount of content is returned with each item rather than it just being a summary.

The big problem in all of this is identifying which URL has the large transient memory requirement. Tools available for this aren't good and you generally have to fallback to adhoc solutions to try and work it out. I'll leave such techniques to another time.

# Reducing the impacts

As to solving the problem when you have identified which URLs are the problem, ideally you would change how the code works to avoid the large transient memory requirement. If you cannot do that, or not straight away, then you can for some Python WSGI servers fall back on a number of different techniques to at least lesson the impact, by configuring the WSGI server or container differently.

For example, if using mod\_wsgi daemon mode, you can start using the 'inactivity-timeout' and 'maximum-requests' options to the WSGIDaemonProcess directive for the mod\_wsgi daemon process group your application is running in.

What the 'maximum-requests' option does is automatically restart a specific mod\_wsgi daemon process after that process has handled a set number of requests. If the WSGI application doesn't actually handle a steady stream of requests all the time, then the 'inactivity-timeout' can be used at the other extreme, causing a mod\_wsgi daemon process to be restarted if it is idle for more than a set period of time.

In both cases the process is reset, with the Python interpreter being reinitialised. It will now stay at that base level of memory usage until a new web request comes in for the WSGI application. When that occurs the WSGI application will once again be loaded and start to process web requests.

So the result of the two options is to allow you to reset the memory usage back to a more sensible level if you have an issue with memory growth within the process due to incorrect management of resources, or simply because of specific URLs which have high transient memory requirements which are blowing out the overall memory requirements of the whole web application.

The problem with using such options as a solution is that the requirements for a small set of URLs are still dictating the configuration for the whole application. Previously the problem was that the memory usage requirements for a small number of URLs would end up dictating how many instances of your web application you could afford to deploy within the memory constraints of the host you were using. In using these options you are just changing the sorts of problems that can occur because of the performance impacts these options can cause.

In the case of setting a maximum for the number of requests handled for the process, the problem is that you can introduce a significant amount of process churn if this is set too low relative to the overall throughput. That is, the processes will get restarted on a frequent basis, with a subsequent increase in CPU load from having to constantly reload the web application. The need to restart the process and reload the web application also means that you are temporarily reducing the overall capacity of your site, potentially resulting in longer overall response times as requests are delayed in being able to be processed.

I talked about this issue of process churn last year in my PyCon US talk '[Making Apache suck less for hosting Python web applications](http://lanyrd.com/2013/pycon/scdyzk/)'. The talk at that time didn't though deal with the problem that a web application is actually a bunch of parts that can have quite different requirements. There was an implied assumption that it was safe to treat the web application as a black box with more or less uniform behaviour across all URLs. Taking this view though is always going to end up with a sub optimal outcome.

# Partitioning your application

The better solution to this problem with not all URLs being equal and having different resource requirements, is to vertically partition your web application and spread it across multiple processes. Where each process only handles a subset of URLs. Each distinct set of processes can then be optimally configured to suit the requirements of the code which is being run in it.

Performing such partitioning with most WSGI deployment mechanism can be quite complicated. This is because the WSGI servers themselves have no means of adequately partitioning a web application and still be managed by the one WSGI container. Instead, what would be required is to run multiple distinct WSGI servers on separate ports and have them all sitting behind a front end web server such as nginx, with nginx matching URLs and performing routing as required.

If however you are using Apache/mod\_wsgi such partitioning can be quite easily managed with only minor changes to the existing configuration. This is the case because of mod\_wsgi's ability to handle multiple daemon process groups in which WSGI applications can be run. It is then possible to use builtin features of Apache for matching URLs, to dynamically delegate a subset of URLs to an alternate daemon process group to the main part of the application.

Take for example admin URLs in Django. If these are indeed infrequently used but can have a large transient memory requirement, what it is possible to do is:

```
 WSGIDaemonProcess main processes=5 threads=5  
 WSGIDaemonProcess admin processes=1 threads=3 \  
     inactivity-timeout=30 maximum-requests=20
 
 
 WSGIApplicationGroup %{GLOBAL}  
 WSGIProcessGroup main
 
 
 WSGIScriptAlias / /some/path/wsgi.py
 
 
 <Location /admin>  
 WSGIProcessGroup admin  
 </Location>
```

So what we have done is created two daemon process groups and specified that the admin pages should be handled in a distinct daemon process group of its own where we can be more aggressive with the configuration and use inactivity timeout and maximum requests to combat excessive memory use. In doing this we have left alone things for the bulk of the web application and so would not be impacting on it as far as process churn is concerned.

The end result is that we can tailor configuration settings for different parts of the application. The only requirement is that we can reasonably easily separate the the different parts of the application out based on URL by matching it with a Location or LocationMatch directive in Apache.

Now in this example we have done this specifically to separate out the misbehaving parts of an application, but the converse can also be done.

Quite often most of the traffic for a site will often hit a small number of URLs. The performance of this small number of URLs, but very frequently visited, could be impeded by having to use a more general configuration for the WSGI container to satisfy the requirements of everything else running in the web application.

What may work better is to delegate the very high trafficked URLs into their own daemon process groups with a processes/threads mix tuned for that scenario.

Because that daemon process group is only going to handle a smaller number of URLs, the actual amount of code from your application that would ever be executed within that process could potentially be much smaller. So long as your code base is setup such that it only lazily imports code for specific handlers when necessary the first time, you can keep this optimised process quite lean as far as memory usage.

So instead of having every process having to be very fat and eventually load up all parts of your application code, you can leave that for a smaller number of processes, where although they are going to serve up a greater number of different URLs, wouldn't necessarily get as much traffic and so don't have to have as much capacity.

You might therefore have the following:

```
 WSGIDaemonProcess main processes=1 threads=5  
 WSGIDaemonProcess volume processes=3 threads=5  
 WSGIDaemonProcess admin processes=1 threads=3 \  
     inactivity-timeout=30 maximum-requests=20
 
 
 WSGIApplicationGroup %{GLOBAL}  
 WSGIProcessGroup main
 
 
 WSGIScriptAlias / /some/path/wsgi.py
 
 
 <Location ~ "^/$">  
 WSGIProcessGroup volume  
 </Location>
 
 
 <Location /publications/article/>  
 WSGIProcessGroup volume  
 </Location>
 
 
 <Location /admin>  
 WSGIProcessGroup admin  
 </Location>
```

In this case we are delegating just the URLs corresponding to the home page for the site and one further sub URL into one daemon process group. As less code within the application would be required to service these requests, the process should have a lower memory footprint and so we can afford to spread the requests across a greater number of processes, each with a small number of threads, to avoid as much as possible any adverse effects of the GIL from running a high number of threads.

The admin pages would still be separated out due to our original issue with the transient memory requirements for those. Everything else would run in our main daemon process group. Because though that now handles a much lower volume of traffic, we can get away with fewer processes. Given this process will still be quite fat as it would need to still load most of the code for the web application, fewer processes means less memory usage overall.

So by juggling things like this, handling as special cases worst case URLs for transient memory usage, as well as your high traffic URLs, one can often quite dramatically control the amount of memory used as well as improve the response times for those URLs which are hit the most.

# Monitoring for success

Now the one requirement that must be satisfied for all this to be able to be done successfully is that you must have monitoring. If you have no monitoring at all then you are going to have no idea about the traffic which is hitting each part of your web application. It will as a result be impossible to tune the processes/threads mix for each daemon process group you are running to optimise the capacity utilisation and response times.

Any such monitoring will at least have to allow you to monitor separately the memory usage of each distinct daemon process group. If monitoring memory from outside of the processes this can be a problem though, as most tools will only see the processes as all belonging to Apache.

It is possible to define a 'display-name' option against each WSGIDaemonProcess directive to set a name for processes in that daemon process group. You can even ask mod\_wsgi to automatically name them based on the name of the daemon process group. For example:

```
 WSGIDaemonProcess main display-name=%{GROUP} processes=1 threads=5  
 WSGIDaemonProcess volume display-name=%{GROUP} processes=3 threads=5  
 WSGIDaemonProcess admin display-name=%{GROUP} processes=1 threads=3 \  
     inactivity-timeout=30 maximum-requests=20
```

This would result in the processes being labelled as '\(wsgi:main\)', '\(wsgi:volume\)' and '\(wsgi:admin\)'.

Such labels though are only respected by tools such as BSD derived 'ps' or 'htop'. The label may not necessarily be respected by all monitoring systems.

Trying to track request throughput and response times using a separate tool can also have its own problems. Apache can be set up to log response times in addition to the URLs accessed, but if needing live monitoring then it means that the access log has to be constantly processed to derive the information. Any such tool may not though, unless sufficiently customisable, allow you to break out throughput and response time based on the subsets of URLs being matched and delegated to the different daemon process groups.

A better solution here can be to use a monitoring system that runs within the web application processes themselves.

I am possibly a little bit biased in this opinion since I do work there and wrote the Python agent, but by far the best single package available for monitoring production Python web applications is [New Relic](http://www.newrelic.com/python).

In using New Relic though, we do have to make some additional configuration changes. This is because normally when using New Relic, the one web application would report under one application in the New Relic UI.

For the above configuration however, what we want is to be able to view the data collected separately for each daemon process group. At the same time though, it would still be useful to be able to view it collectively under one application.

One could do some tricks in the WSGI script involving selecting different environment sections from the New Relic Python agent configuration file, but the easier way is to use the Python agent's ability to set the application name being reported to dynamically for each request. Such ability to set the application name dynamically can be done through a key/value pair passed in via the WSGI environ dictionary into the WSGI application.

In the case of Apache/mod\_wsgi, WSGI environ key/value pairs can be set using the SetEnv directive in the Apache configuration file itself. What we can therefore do is:

```
 WSGIDaemonProcess main processes=1 threads=5  
 WSGIDaemonProcess volume processes=3 threads=5  
 WSGIDaemonProcess admin processes=1 threads=3 \  
     inactivity-timeout=30 maximum-requests=20
 
 
 WSGIApplicationGroup %{GLOBAL}  
 WSGIProcessGroup main
 
 
 SetEnv newrelic.app_name 'My Site (main);My Site'
 
 
 WSGIScriptAlias / /some/path/wsgi.py
 
 
 <Location ~ "^/$">  
 WSGIProcessGroup volume  
 SetEnv newrelic.app_name 'MySite (volume);My Site'  
 </Location>
 
 
 <Location /publications/article/>  
 WSGIProcessGroup volume  
 SetEnv newrelic.app_name 'MySite (volume);My Site'  
 </Location>
 
 
 <Location /admin>  
 WSGIProcessGroup admin  
 SetEnv newrelic.app_name 'MySite (admin);My Site'  
 </Location>
```

We are again are using specialisation via the Location directive. In this case we are using it to override what the application name the New Relic Python agent reports to for the different URLs.

We are also in this case using a semi colon separated list of names.

The result is that each daemon process group logs under a separate application in the New Relic UI of the form 'My Site \(XXX\)' but at the same time they also all report to 'My Site'.

This way you can still have a combined view, but you can also look at each daemon process group in isolation.

The ability to see each daemon process group in isolation is important, because you can then do the following separately for each daemon process group.

  * View response times.
  * View throughput.
  * View memory usage.
  * View CPU usage.
  * View capacity analysis report.
  * Trigger thread profiler.



If things were separated and they were all reporting only to the same application, the data presented by this would be all mixed up and for the last four items especially, could be confusing.

# Future posts and talks

Okay, so that is probably going to be a lot to digest but represents just a part of what I would have presented at PyCon US if my talk had been accepted.

Other things I would have talked about would have included dealing with request back log when overloaded due to increase traffic for certain URLs, dealing with danger of malicious POST requests with large content size and various other topics deriving from the fact that not all URLs in a web application are equal.

As I said, I can't see myself turning that talk into a series of blog posts instead due to already having a lot on my plate, but can always see what happens. One of the things I do have to do, which could be viewed as a sort of consolation prize for not getting any talks accepted for PyCon US, is that I do now need to present a vendor workshop on behalf of New Relic at PyCon US this year.

Since I don't like doing straight marketing, you can be assured this will be packed full of lots of useful technical information about monitoring performance of applications, metrics collection, instrumentation and data visualisation. Further information on this will be forthcoming, but hopefully you can reserve some time for late in the second day of tutorials before the conference proper. I'll likely post some details here later, but also keep an eye out on the [New Relic blog](http://blog.newrelic.com) for more information on that workshop.

---

## Comments

### Ross Reedstrom - February 21, 2014 at 4:25 AM

We're in the process of building and deploying a python wsgi app composed of multiple separate components. This post has me thinking. \(and thinking that I need to subscribe to the mod\_wsgi list ...\) :-\)

### Unknown - April 11, 2014 at 7:25 AM

One thing I can not find in the documentation is the balance between processes and threads, I must increase the number of processes or is it better to increase the number of threads?   
This is related to the number of elements in a dynamic page or the number of sites served on the same web server?   
  
Thank you,   
Marcelo Módolo

### Graham Dumpleton - April 11, 2014 at 1:41 PM

I suggest you watch:  
  
http://lanyrd.com/2013/pycon/scdyzk/  
http://lanyrd.com/2012/pycon/spcdg/  
  
The balance of processes/threads really depends on your application and without some sort of monitoring it isn't really possible to give general advice about what to set them to.  
  
Specifically, measures such as throughput, response time, queueing time and an analysis of how much of the capacity for a configuration is being used all come into play in determining the appropriate settings.

