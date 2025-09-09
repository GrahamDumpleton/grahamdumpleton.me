---
layout: post
title: "Version 2.3 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "2008-08-25"
url: "http://blog.dscpl.com.au/2008/08/version-23-of-modwsgi-is-now-available.html"
post_id: "7712247210624304529"
blog_id: "2363643920942057324"
comments: 1
published_timestamp: "2008-08-25T17:37:00+10:00"
blog_title: "Graham Dumpleton"
---

Version 2.3 of [mod\_wsgi](http://www.modwsgi.org/) is a bug fix update. The most important of the bug fixes addresses a data truncation issue when using wsgi.file\_wrapper extension \(on Windows or Apache 1.3 on UNIX\) with file objects. Data truncation could also occur for all deployment configurations for any other file like objects used with wsgi.file\_wrapper.  
  
A number of other issues are also addressed, including a crash when using mod\_python at the same time and leakage of file descriptors in Apache parent process on graceful restart of Apache.  
  
It is highly recommended that if you are using version 2.0 or 2.1 of mod\_wsgi and applications which make use of the wsgi.file\_wrapper extension that you upgrade to this version. Trac users running on Windows, or who are using Apache 1.3 on UNIX, should in particular consider upgrading as the wsgi.file\_wrapper issue can cause truncation of data when downloading attachments with binary data containing NULL characters.  
  
Note that version 2.3 of mod\_wsgi was a quick fire release to fix issues caused in version 2.2 release which preceded 2.3 by a day or so. If you have already obtained version 2.2 of mod\_wsgi, you should ensure you upgrade to version 2.3. If not you will find that CGI scripts will fail if mod\_wsgi daemon mode is also being used.  
  
A description of changes in version 2.2/2.3 can be found in the change notes at:  
  
<http://code.google.com/p/modwsgi/wiki/ChangesInVersion0202>  
<http://code.google.com/p/modwsgi/wiki/ChangesInVersion0203>  
  
If you have any questions about mod\_wsgi or wish to provide feedback, use the Google group for mod\_wsgi found at:  
  
<http://groups.google.com/group/modwsgi>

---

## Comments

### Unknown - August 28, 2008 at 9:44 AM

Thank you so much for all your work\! mod\_wsgi is the best thing since sliced bacon.

