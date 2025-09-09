---
title: "Version 1.3 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "Sunday, November 18, 2007"
url: "http://blog.dscpl.com.au/2007/11/version-13-of-modwsgi-is-now-available.html"
post_id: "7312307965082826982"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 5
published_timestamp: "2007-11-18T13:51:00+11:00"
blog_title: "Graham Dumpleton"
---

Version [1.3](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0103) of [mod\_wsgi](http://www.modwsgi.org) is a bug fix only release, addressing issues with mod\_wsgi daemon processes hanging under certain conditions. It is highly recommended that users of mod\_wsgi who use daemon mode of mod\_wsgi upgrade to this new version. A third release candidate for version [2.0](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0200) is also now being made available incorporating the same fix and adding an additional feature to detect errant Python C extension modules that don't release the Python GIL when running long, potentially blocking, operations.

---

## Comments

### Unknown - February 26, 2008 at 6:05 PM

Seems like mod\_wsgi crashes as of FreeBSD 7.x pthread redux :\(  
  
Endless loop:  
  
\#0 0x285d05a9 in pthread\_join \(\) from /lib/libthr.so.3  
\#1 0x285cd304 in pthread\_self \(\) from /lib/libthr.so.3  
\#2 0x285cd610 in pthread\_rwlock\_timedwrlock \(\) from /lib/libthr.so.3  
\#3 0x285d07a9 in pthread\_join \(\) from /lib/libthr.so.3  
\#4 0x285cd304 in pthread\_self \(\) from /lib/libthr.so.3  
\#5 0x285cd610 in pthread\_rwlock\_timedwrlock \(\) from /lib/libthr.so.3  
\(...\)  
\#201 0x285d07a9 in pthread\_join \(\) from /lib/libthr.so.3  
\#202 0x285cd304 in pthread\_self \(\) from /lib/libthr.so.3  
\#203 0x285cd610 in pthread\_rwlock\_timedwrlock \(\) from /lib/libthr.so.3  
  
Thanks for looking into it.

### Unknown - February 26, 2008 at 6:07 PM

Ah yes, in the above case its mod\_wsgi 1.3, but it might affect 2.0 too.

### Graham Dumpleton - February 26, 2008 at 8:48 PM

FreeBSD threading support has given others problems as well. In part it looks to be problems in FreeBSD rather than mod\_wsgi. See:  
  
http://blag.whit537.org/2007/07/freebsd-threads-apache-and-modwsgi.html  
  
It would appear that if one doesn't sing the right magic incantation that you will hit problems.  
  
If you can provide better information about the problems then post it on the mod\_wsgi list on Google groups.

### Unknown - February 27, 2008 at 6:06 PM

Alright,to note: I'm trying to get it to run within Apache 1.3. Now this envvar file does not exist.  
  
So I tried to libmap to other threading implementations but python would not even compile with them.  
  
pthreads are now now in libthr.so, I was told, there is no longer libpthreads. Thus I think you will really have to look into it anew for FreeBSD 7.x - things have changed.

### Graham Dumpleton - February 27, 2008 at 6:55 PM

Not really up to mod\_wsgi, as it just uses apxs from Apache, so Apache's build mechanism is what needs to be setup correctly. I think though you will not be able to get Apache 1.3 to work as it doesn't have threading compiled into it anyway.

