---
layout: post
title: "Version 3.4 of mod_wsgi is now available."
author: "Graham Dumpleton"
date: "2012-08-25"
url: "http://blog.dscpl.com.au/2012/08/version-34-of-modwsgi-is-now-available.html"
post_id: "5059617264069271467"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'new relic', 'python']
comments: 0
published_timestamp: "2012-08-25T16:42:00+10:00"
blog_title: "Graham Dumpleton"
---

I know that it has been a very long time since the last mod\_wsgi release, July 2010 to be exact, but it is not deceased like its predecessor mod\_python. It really has just been 'resting'.  
  
Truth is that the previous version was proving so stable there hasn't been a great need to actually put out a new version. A couple of bugs that were actually affecting some users were finally uncovered a little while back though. That and with Apache 2.4 and Python 3.2 being released and starting to be bundled with some Linux variants now as default versions, which required some compatibility changes to be made, it is finally time to update mod\_wsgi to version 3.4.  
  
Rather than just being a compatibility and minor bug fix release though, I have gone and back ported a lot of changes from mod\_wsgi 4.0 since it seems it will be a while yet before that version sees the light of day.  
  
Full details of all the changes can be found in:  
  


  * <http://code.google.com/p/modwsgi/wiki/ChangesInVersion0304>



If wanting to download the source code for mod\_wsgi, you can find details in:

  * <http://code.google.com/p/modwsgi/wiki/DownloadTheSoftware>



  
There are probably two key new features for when using daemon mode of mod\_wsgi that are going to be of interest.  
  
The first is the addition of the 'python-home' option to the WSGIDaemonProcess directive. This allows you to specify the root of a Python virtual environment and the daemon process will be fully initialised against. This replaces the need to use the 'python-path' option whereby you actually had to refer to the 'site-packages' directory within the virtual environment. The 'python-home' option should make it more obvious as to how to setup mod\_wsgi daemon mode processes with Python virtual environments. For embedded mode, you should continue to use the WSGIPythonHome directive.  
  
The second is the addition of the 'lang' and 'locale' options to the WSGIDaemonProcess directive. The options allow you to do the equivalent of setting the 'LANG' and 'LC\_ALL' environment variables, which for Apache was a bit difficult as you had to either modify the 'envvars' file of the Apache installation if recognised, or modify the init scripts for Apache. Do note though that these options only apply to the daemon process group the directive was for, you will still need to use the environment variable approach if using embedded mode.  
  
One final change worth noting, although only of interest to users of New Relic, is that this new version of mod\_wsgi will set a special WSGI environ key called 'mod\_wsgi.queue\_start'. This will be picked up the New Relic agent and will allow automatic reporting on request queueing time within Apache/mod\_wsgi.  
  
The queueing time is the time between when Apache first accepts the socket connection for the request and when the WSGI application starts to handle it. This is an important metric to measure to determine how long requests are being delayed due to backlog when using mod\_wsgi daemon mode.  
  
The primary reason backlog may occur is that the daemon process group hasn't been provisioned with enough processes/threads and/or the daemon processes get overwhelmed by long running requests, causing starvation of available request threads for handling them. Knowing this information can therefore be very informative when trying to determine correct processes/threads settings.  
  
So enjoy this long delayed update and hopefully life will one day accommodate me being able to spend more time on mod\_wsgi than I currently am able to.