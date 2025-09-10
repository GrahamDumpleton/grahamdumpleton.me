---
layout: post
title: "Version 2.0 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "2008-03-21"
url: "http://blog.dscpl.com.au/2008/03/version-20-of-modwsgi-is-now-available.html"
post_id: "6532290653173255554"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 7
published_timestamp: "2008-03-21T17:17:00+11:00"
blog_title: "Graham Dumpleton"
---

Due to the arrival of a baby 1.0, version 2.0 of [mod\_wsgi](http://www.modwsgi.org/) has been a bit slower in coming than originally planned, but the wait is now over and it is available for [download](http://modwsgi.googlecode.com/files/mod_wsgi-2.0.tar.gz). The major improvements in version 2.0 of mod\_wsgi are detailed below, but there are various other little goodies as well, so check out the [change notes](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0200) on the wiki.

  


# Process Reloading Mechanism

  


When using daemon mode of mod\_wsgi and the WSGI script file for your application is changed, the default behaviour is to now restart the daemon processes automatically upon receipt of the next request against that application. Thus, when making changes to any code or configuration data for your application, all you now need to do is touch the WSGI script file and the daemon processes for just that application will be automatically restarted and the application reloaded. This means that it is no longer necessary to send signals explicitly to the daemon processes, or restart the whole of Apache. This means that elevated privileges are not required by users and applications owned by other users in a shared hosting environment will not be affected when one users application is restarted.

  


# Apache Authentication Provider

  


When using Apache 2.2, mod\_wsgi provides the means to implement Apache authentication providers in Python. This means that password authentication for HTTP Basic and Digest authentication, plus other custom authentication mechanisms implemented by other Apache modules, can be delegated to your Python application. This for example can be used to implement HTTP authentication for a Trac instance against a user database maintained within a Django instance running on the same site. If using Apache 2.0 the mechanism is also available, but only in support of standard Apache HTTP Basic authentication.

  


# Python Virtual Environments

  


More integrated support for Python virtual environments such as 'virtualenv' is now provided. These changes make it possible for different daemon process groups to be easily associated with distinct Python virtual environments. Where daemon process groups are being setup for different users, or to separate different applications, the use of Python virtual environments means that each can use different versions of modules or packages and not interfere with each other.

  


# WSGI File Wrapper Extension

  


Support for 'wsgi.file\_wrapper' extension has been added with operating system mechanisms such as sendfile\(\) and mmap\(\) being used when possible to speed up sending of any data back to a client. Provided an application is written to use this optional extension, then serving up of static files by the application should be greatly improved.

  


# Daemon Mode Now Even Faster

  


Some underperforming code related to the socket used to communicate between the Apache child processes and the daemon processes has been replaced. This has result in a 40% improvement in base level performance for a simple hello world program. This means that daemon mode now performs even faster relative to competing solutions. Do remember though that the network level is usually never the bottleneck and it is the Python application and database queries where things slow down. Thus, although it is quicker, in the grander scheme of things the improvement wouldn't be noticed in most applications.

---

## Comments

### Unknown - March 21, 2008 at 10:27 PM

Congratulations, Graham. Something more to put on the pile of things to play with and use some more.

### jespern - March 21, 2008 at 11:07 PM

Nice work, Graham. I've really been enjoying your work so far.

### Unknown - March 21, 2008 at 11:38 PM

Wow, seems like some nice new features in there. Definitely need to finish my Django book and test out mod\_wsgi for it's deployment method.

### Unknown - March 22, 2008 at 1:10 PM

Congratulations Graham - Clearly mod\_wsgi 2.0 represents a lot of hard work and a major achievement\!  
  
I will be good on my promise to give it a go soon \(jetfar.com\).

### Nicolas Lehuen - March 22, 2008 at 9:12 PM

Thanks for your work, Graham, and congratulations for your baby 1.0 \!

### Max - March 24, 2008 at 1:16 AM

Thank you Graham. this is great, congratulations\! Is it compatible with version 1.0? BTW. I made the changes you suggested to web2py and it now only uses absolute paths, in fact some users are successfully using it with mod\_wsgi 1.0. Double thank you.

### MockSoul - March 29, 2008 at 12:01 AM

Very nice work. I was reading mod\_wsgi.c source and it is quite beautiful. mod\_wsgi currently is the best solution for python web apps.  
  
Great work\!  
  
The only improvement I want - docs. For me examing the source was needed to understand how several daemons will spawn for high loads. But after that whole workflow seems to be very clear. Awesome library\!

