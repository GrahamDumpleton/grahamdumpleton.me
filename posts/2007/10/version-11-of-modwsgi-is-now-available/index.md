---
title: "Version 1.1 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "Monday, October 1, 2007"
url: "http://blog.dscpl.com.au/2007/10/version-11-of-modwsgi-is-now-available.html"
post_id: "9189403782151640575"
blog_id: "2363643920942057324"
tags: ['mod_wsgi']
comments: 0
published_timestamp: "2007-10-01T13:30:00+10:00"
blog_title: "Graham Dumpleton"
---

Version 1.1 of mod\_wsgi is now available and can be downloaded from [http://www.modwsgi.org](http://www.modwsgi.org/). This is a bug fix release only and no new features are included. Two main problems addressed are possibility of processes crashing when multiple threads hit race condition on sending output via sys.stdout/sys.stderr, and conflict with the Apache mod\_logio module which would result in mod\_wsgi daemon processes crashing. A description of all changes in this version can be found in the [change notes](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0101). Updating to this version is recommended for all users.