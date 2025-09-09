---
title: "Source code reloading with mod_wsgi on Windows."
author: "Graham Dumpleton"
date: "Thursday, February 26, 2009"
url: "http://blog.dscpl.com.au/2009/02/source-code-reloading-with-modwsgi-on.html"
post_id: "7479161341362177128"
blog_id: "2363643920942057324"
tags: ['django', 'mod_wsgi']
comments: 0
published_timestamp: "2009-02-26T09:41:00+11:00"
blog_title: "Graham Dumpleton"
---

I recently highlighted how with mod\_wsgi daemon mode one can enable full automatic source code reloading, using Django as an [example](/posts/2008/12/using-modwsgi-when-developing-django/). Because it required daemon mode however, that recipe would only work on UNIX systems. Here I'll explain though how we can go about modifying the code so that it works with Apache being run on Windows.

  


When using daemon mode on UNIX systems, the WSGI application will be running in its own set of processes distinct from the normal Apache server child processes which handle regular requests. The code provided worked by using a background thread in each daemon process to monitor for code changes and sending a SIGINT signal to itself when it detected a change. This signal would trigger the daemon process to shutdown. The Apache parent process would detect that the daemon process had shutdown and mod\_wsgi code running in the Apache parent process would then create a replacement process.

  


On Windows however, the WSGI application runs within the single Apache server child process that is created by the 'winnt' MPM used by Apache on Windows. That MPM implementation doesn't use traditional signals however for process control of the Apache server child process, so can't use that same technique. What we can however do is use a bit of magic to call an internal Apache function which sends a Windows event to the Apache parent process to trigger a restart of Apache itself.

  


Although a full restart is required, Apache on Windows only uses a single child server process and so the impact isn't as significant as on UNIX platforms, where many processes may need to be shutdown and restarted. It certainly is much better than the traditional technique used of setting the 'MaxRequestsPerChild' directive to '1' to force a restart after every request, as the restart will only occur when an actual code change is made.

  


So, what is the bit of magic that makes this work. For that you are referred to section [Restarting Windows Apache](http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode#Restarting_Windows_Apache) in the mod\_wsgi documentation. Also refer to section [Restarting Daemon Processes](http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode#Restarting_Daemon_Processes) for the original code. For how to integrate this with Django, see the [original blog post](/posts/2008/12/using-modwsgi-when-developing-django/).

  


BTW, this type of approach cannot be used for embedded mode on UNIX systems as the Apache parent process would typically run as root. As such, the Apache server child processes do not have sufficient privileges to send a signal to the Apache parent process. Problems would also arise because of there being multiple Apache server child processes rather than just one. This is because a signal would potentially be received by the Apache parent process from more than one Apache server child process. The outcome of this could be unpredictable with Apache possibly restarting multiple times.