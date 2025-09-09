---
title: "Debugging with pdb when using mod_wsgi."
author: "Graham Dumpleton"
date: "Tuesday, September 2, 2014"
url: "http://blog.dscpl.com.au/2014/09/debugging-with-pdb-when-using-modwsgi.html"
post_id: "6322718581692145812"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 2
published_timestamp: "2014-09-02T07:18:00+10:00"
blog_title: "Graham Dumpleton"
---

In the early days of mod\_wsgi I made a decision to impose a restriction on the use of stdin and stdout by Python WSGI web applications. My reasoning around this was that if you want to make a WSGI application portable to any WSGI deployment mechanism, then you should not be attempting to use stdin/stdout. This includes either reading or writing to these file objects, or even performing a check on them to try and determine if code is running in a process attached to a TTY device.

The restriction was generally driven by the fact that WSGI adapters for CGI relied on stdin and stdout to communicate with the web server the script was running in. Although such CGI/WSGI adapters could have saved away the original stdin and stdout for their own use and then replaced the original 'sys.stdin' and 'sys.stdout' with working alternatives so users code didn't care, the original example CGI/WSGI adapter in the WSGI specification never did that, so no one as a result thought about the issue and did something about it themselves when implementing CGI/WSGI adapters.

As to what the problem was, the issue was that if any user code decided to use 'print\(\)' to dump out debugging information so it appeared in a WSGI server log, when that WSGI application was hosted using a CGI/WSGI adapter, that debug output would end up in the HTTP response sent back to the client, as stdout is used by a CGI script to communicate with the web server.

So all well and good and I thought I was doing a good thing by encouraging people to write portable WSGI application code. This isn't how users saw things though, they didn't care about such things and because they got an exception when they tried to use stdin or stdout they blamed mod\_wsgi and not that what they were doing wasn't portable.

What happened therefore is that documentation for some Python web frameworks and various blog posts started to say that mod\_wsgi has these restrictions and/or was broken and here is how you workaround it. The Flask [documentation](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/#troubleshooting) even today still carries such a warning even though it isn't relevant to more recent mod\_wsgi versions, with the restriction removed back in mod\_wsgi 3.0, which was released on 21st November 2009, almost five years ago.

For some more background on this issue you can read my prior [blog post](/posts/2009/04/wsgi-and-printing-to-standard-output/) back in 2009 about it. In short though, if you are using:
    
    
    WSGIRestrictStdout Off

in the Apache configuration file, or using:
    
    
    import sys  
    sys.stdout = sys.stderr

in the WSGI script file, you do not need to if using mod\_wsgi version 3.0 or later. 

The reason this issue came up in my discussions with people during the hallway track of DjangoCon was because we were discussing the Django debug toolbar and Python debuggers such as pdb.

In the case of pdb, in order for it to work, it needs to have access to the original stdin and stdout attached to your console in order to provide you with an interactive session.

When you remap 'sys.stdout' to 'sys.stderr' in your WSGI script file you are replacing the original stdout with stderr where stderr is always going to be connected to the Apache error log. Any output from pdb would therefore end up in the Apache error log and would not show in your interactive console.

But wait you say, Apache/mod\_wsgi runs all the processes which run your actual WSGI application as background processes so how could it work anyway. There is no way at that point that stdin and stdout would still be connected to any console shell and since Apache is generally started as root on system startup, how is that even helpful.

What is little known is that it is in fact possible to run Apache with mod\_wsgi in a single process mode where Apache is run in the foreground and where stdin and stdout are attached to your console, allowing you to potentially interact with the process.

If using a standard Apache setup, the steps required are admittedly a bit fiddly to get this running.

The first thing you need to do is if you are using mod\_wsgi daemon mode, you have to comment out the mod\_wsgi directives which set that up. This then defaults your WSGI application back to running in embedded mode.

The next thing you need to do is if you are using the worker or event MPMs of Apache, you need to change the MPM configuration to only create a single worker thread per process.

Finally, you then need to manually start the Apache server from a shell, giving it the '-DONE\_PROCESS' or -X' option.
    
    
    /usr/sbin/httpd -X

If you are on a Linux system, it is possible you will also need to set the 'APACHE\_RUN\_USER' and 'APACHE\_RUN\_GROUP' environment variables as well. This is because on some Linux systems, the standard Apache configuration is dependent on these environment variables having been set by the 'apachectl' script. If needing to set them, they should be set to the user and group of the standard Apache user.

Do all that and you can now place in your code:
    
    
    import pdb; pdb.set_trace()

and when that code is executed you will be thrown into an interactive pdb session where you can interact with your WSGI application. To exit out of the pdb session enter 'cont' and it will continue with the request.

You can find further information about all this in the mod\_wsgi [documentation about pdb](http://code.google.com/p/modwsgi/wiki/DebuggingTechniques#Python_Interactive_Debugger). Do be warned that the WSGI middleware described there isn't strictly correct and only intercepts an exception which occurs when creating the iterable to be returned, which for a generator is even before your code gets executed. It may therefore be best to stick with 'pdb.set\_trace\(\)' for now until I fix that WSGI middleware.

So it is possible to use pdb with WSGI applications hosted using Apache/mod\_wsgi, but the steps do make it a bit onerous.

This is the point where some of the more recent work I am doing on mod\_wsgi makes this more practical.

With the newer mod\_wsgi express variant you don't have to worry about the Apache configuration, making it an ideal way to run up Apache/mod\_wsgi in a development environment.

For this specific use case of wanting to run pdb, the next version of mod\_wsgi \(4.3.0\), supports a new option for mod\_wsgi express which allows it to be run in this single process mode for you automatically, thus making it easier to use pdb to debug a WSGI application running under Apache/mod\_wsgi.

---

## Comments

### Unknown - March 21, 2015 at 3:39 AM

Thank you for this article. Your posts have been tremendously helpful to me. mod\_wsgi is great\!

### Graham Dumpleton - March 23, 2015 at 9:59 AM

If you are interesting in using pdb to debug your application, you would be much better off using mod\_wsgi-express.  
  
mod\_wsgi-express start-server script.wsgi --debug-mode --enable-debugger  
  
It worries about all the stuff for getting pdb running and can be done on the command line distinct from your main Apache.

