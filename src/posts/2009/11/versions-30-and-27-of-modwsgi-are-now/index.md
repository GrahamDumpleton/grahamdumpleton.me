---
layout: post
title: "Versions 3.0 and 2.7 of mod_wsgi are now available."
author: "Graham Dumpleton"
date: "2009-11-21"
url: "http://blog.dscpl.com.au/2009/11/versions-30-and-27-of-modwsgi-are-now.html"
post_id: "3384369215181650370"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 5
published_timestamp: "2009-11-21T22:15:00+11:00"
blog_title: "Graham Dumpleton"
---

No problems were reported with last release candidate and no one took issue with [Python 3.X support](http://code.google.com/p/modwsgi/wiki/SupportForPython3X), so have finally released [mod\_wsgi 3.0](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0300). Have also released a very minor update of 2.X branch as well in form of [mod\_wsgi 2.7](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0207). Unless significant issues come up, there will be no more releases from the 2.X branch.

---

## Comments

### Dirkjan Ochtman - November 22, 2009 at 5:10 AM

It seems 2.7 reacts weirdly to the Gentoo way of building it, at least...  
  
>>> Compiling source in /var/tmp/portage/www-apache/mod\_wsgi-2.7/work/mod\_wsgi-2.7 ...  
make -j2   
/usr/sbin/apxs2 -c -I/usr/include/python2.6 -DNDEBUG -Os -march=native -pipe mod\_wsgi.c -Wl,-O1 -L/usr/lib -L/usr/lib/python2.6/config -lpython2.6 -lpthread -ldl -lutil -lm  
apxs:Error: Unknown option: O.  
apxs:Error: Unknown option: s.  
apxs:Error: Unknown option: m.  
apxs:Error: Unknown option: r.  
apxs:Error: Unknown option: h.  
apxs:Error: Unknown option: =.

### Graham Dumpleton - November 22, 2009 at 1:08 PM

@djc: See discussion in 'http://groups.google.com/group/modwsgi/browse\_frm/thread/667933ac958d1e6b'.

### Graham Dumpleton - November 24, 2009 at 9:40 PM

Fixes in trunk for 3.1 and branch for 2.8. New versions will come out in next day or so. The changes only affect building form package distribution scripts which inject CFLAGS into configure. If you have got existing versions compiled, no need to bother with update versions when they come out. If just want the patch, see mailing list discussion.

### Graham Dumpleton - November 25, 2009 at 9:28 PM

Version 2.8 and 3.1 of mod\_wsgi are now available to address the CFLAGS issue.

### Dirkjan Ochtman - November 25, 2009 at 11:01 PM

Great, thanks. I committed a 2.8 ebuild to Gentoo's tree.

