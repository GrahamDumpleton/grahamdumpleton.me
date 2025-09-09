---
layout: post
title: "Version 1.2 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "2007-10-31"
url: "http://blog.dscpl.com.au/2007/10/version-12-of-modwsgi-is-now-available.html"
post_id: "2329778612774592701"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 0
published_timestamp: "2007-10-31T20:41:00+11:00"
blog_title: "Graham Dumpleton"
---

[Mark](http://hex-dump.blogspot.com/2007/10/sneak-peek-at-modwsgi-12.html) beat me to the punch again and got word out about [mod\_wsgi 1.2](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0102) before I myself got a chance to sit down and blog about it. I'll have to start paying him as my publicist soon.  
  
Version 1.2 of mod\_wsgi is a bug fix only release, addressing issues with WSGI specification compliance, sub process invocation from Python in a mod\_wsgi daemon process and most importantly of all, an issue whereby a second sub interpreter instance could be created for each WSGI application group when targeted by a specifically formed URL.  
  
This latter issue of a second sub interpreter being created only affects users of Apache 1.3 and 2.0. Because it can have the affect of doubling the memory in use by the application, it is highly recommended that users of these Apache versions upgrade to mod\_wsgi 1.2, given that in a memory constrained environment the bug could be exploited as a form of remote denial of service attack.  
  
At the same time as mod\_wsgi 1.2 has been released, the first release candidate for [mod\_wsgi 2.0](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0200) has also been released. This version provides a number of new features including, integration with Apache authentication and authorisation mechanisms in Apache 2.2, a new process reloading option for mod\_wsgi daemon processes which makes reloading a Python application when changes are made trivial, and direct support for Python virtual environments such as workingenv and virtualenv. I'll blog about these and other new features in mod\_wsgi 2.0 in the coming weeks.  
  
If you want to discuss any of the new mod\_wsgi 2.0 features in the mean time, check out the [change notes](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0200) or pop on over to the [mod\_wsgi Google Group](http://groups.google.com/group/modwsgi).