---
title: "Version 2.4 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "Saturday, April 11, 2009"
url: "http://blog.dscpl.com.au/2009/04/version-24-of-modwsgi-is-now-available.html"
post_id: "9135659301054184635"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 0
published_timestamp: "2009-04-11T21:00:00+10:00"
blog_title: "Graham Dumpleton"
---

Version 2.4 of [mod\_wsgi](http://www.modwsgi.org/) is a bug fix update. The most important of the bug fixes addresses a response data truncation issue when using wsgi.file\_wrapper extension on UNIX with keep alive enabled in Apache.  
  
A number of other issues are also addressed, including memory leaks, configuration corruption and request content truncation. A small number of other minor improvements have also been made.  
  
Because of the issue related to truncation of response data, it is highly recommended that if you are using any prior version of mod\_wsgi 2.X with a web application that make use of the wsgi.file\_wrapper extension, such as Trac, that you upgrade.  
  
A description of changes in version 2.4 can be found in the change notes at:  
  
<http://code.google.com/p/modwsgi/wiki/ChangesInVersion0204>  
  
If you have any questions about mod\_wsgi or wish to provide feedback, use the Google group for mod\_wsgi found at:  
  
<http://groups.google.com/group/modwsgi>