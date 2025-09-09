---
title: "Using mod_wsgi-express as a development server."
author: "Graham Dumpleton"
date: "Wednesday, May 6, 2015"
url: "http://blog.dscpl.com.au/2015/05/using-modwsgi-express-as-development.html"
post_id: "7061559565235403992"
blog_id: "2363643920942057324"
tags: ['apache', 'django', 'mod_wsgi', 'python', 'wsgi']
comments: 1
published_timestamp: "2015-05-06T10:46:00+10:00"
blog_title: "Graham Dumpleton"
---

Apache/mod\_wsgi has traditionally been seen as a deployment target only for production systems. To use it in a development environment is viewed as too difficult and not worth the trouble. The downside of not using Apache/mod\_wsgi in a development environment when ultimately deploying to it in production, and instead using a development server provided by any web framework being used, is that situations can arise where your application may work fine in development but then fail in production.

One of the main reasons is that development servers are usually single process and single threaded. This means you are not able to properly test your web application in the face of many concurrent requests. This isn’t just restricted to multithreading issues within the same process, but also the impacts of an external resource being accessed by multiple processes at the same time.

A further example of where a development server can cause problems is that the development server can load your web application differently to what a production WSGI server does. This especially occurs where a development server is actually fronted by a management script which also performs other roles. The act of loading all the management commands when working out which to execute, can result in side effects, or your web application code being loaded in a totally different way to which it is loaded in a production WSGI server. This later issue has in the past especially been a problem with the Django development server, where how the development server loaded code would mask module import cycle issues related to Django database model code.

Development servers in pure Python code can also sometimes be an issue as far as WSGI compliance. This is because they can silently allow certain types of responses which aren’t strictly compliant with what is required by the WSGI specification. The classic example of this is where Unicode objects are used instead of byte strings. Issues arise where a development server silently allows a Unicode object to be converted to a byte string using the default encoding. Run the same code on a WSGI server which more strictly adheres to the WSGI specification and you are likely to encounter a runtime error instead.

These and other reasons are why you should strive to use the same server you intend to use in production during development. As I already said though, Apache/mod\_wsgi has traditionally been seen as being too hard to run as a development server. This is no longer the case with mod\_wsgi-express however, as it provides a way of easily running up an Apache/mod\_wsgi instance from the command line on a non privileged port without you needing to configure Apache yourself. This is because mod\_wsgi-express will automatically generate an Apache configuration for mod\_wsgi and your specific web application for you and then start Apache as well.

In addition to this ability to run Apache/mod\_wsgi from the command line, mod\_wsgi-express also provides a range of other builtin features specifically to make it more useful in a development environment. These include automatic source code reloading, debugger, profiler and coverage support. It also has capabilities to record details about requests received and the responses generated. This is at the level of capturing the actual WSGI environ dictionary and HTTP response headers, along with request and response content. This in depth amount of information can come in handy when you don’t understand why a web application may be responding to the request received or when you need to validate the response.

# Reloading of source code

Python web applications when using WSGI, would nearly always use a persistent process which will handle many requests over time. That is, the source code is loaded once and if you needed to make code changes, you would need to restart the Python web application processes. This is in contrast to a PHP web application which effectively discards any loaded code at the end of a request and reloads it all again for the next request. This difference is a constant source of frustration to PHP developers who have migrated to using Python. They are used to simply making a code change and for that to be available automatically.

Such PHP converts will keep asking why Python can’t just be changed, but due to the performance issues with loading all code on every request, it simply isn’t practical, or at least not in a production environment.

In a development environment at least, to avoid the need to manually restart the WSGI server all the time, development servers will implement a code monitor such that any code files associated with modules that have been loaded into the running Python web application will be monitored for changes. If any of those files on disk change in between the time it was loaded and when the check was made, then the web application process\(es\) will be automatically shutdown and restarted. In this way, when the next request is made it will see the more recent code changes.

As mod\_wsgi-express is still primarily intended for use in production, such a feature isn’t enabled by default, but it can be enabled on the command line using the ‘—reload-on-changes’ option. So if running 'mod\_wsgi-express’ directly, one would use:

> 
>     mod_wsgi-express start-server —reload-on-changes app.wsgi

If using mod\_wsgi-express integrated with a Django project, then you would use:

> 
>     python manage.py runmodwsgi —reload-on-changes

The automatic reloading of your web application when code changes are made will work whether you are running with a single or multithreaded process, and even if you are using a multi process configuration.

# Debugging runtime exceptions

When an exception occurs in the code for your web application, what typically happens is that the exception is caught by the web framework you are using and translated to a generic HTTP 500 server error response page. No details about the exception would normally be displayed within the response. If you are lucky, you might get details of the exception logged to an error log, but various web frameworks do not even do that by default.

What you need to do to reveal information about exceptions obviously varies based on the framework being used. In the case of the Django web framework one thing you can do is enable a debug mode which will result in details of the exception being displayed within the HTTP 500 server error response page.

> 
>     # SECURITY WARNING: don't run with debug turned on in production!  
>     > DEBUG = True

This will result in the display of the exception, a stack trace, and the values of any local variables for each stack frame for the stack trace back. Obviously you don’t want to leave this enabled when deploying to a production environment.

As explained in the prior post where I detailed how to [integrate mod\_wsgi-express with Django](http://blog.dscpl.com.au/2015/04/integrating-modwsgi-express-as-django.html) as a management command, a safer option to capture at least the details of the exception and the stack trace, is to enable Django logging to log the details of the exceptions to the error log.

> 
>     LOGGING = {  
>     >     'version': 1,  
>     >     'disable_existing_loggers': False,  
>     >     'handlers': {  
>     >         'console': {  
>     >             'class': 'logging.StreamHandler',  
>     >         },  
>     >     },  
>     >     'loggers': {  
>     >         'django': {  
>     >             'handlers': ['console'],  
>     >             'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),  
>     >         },  
>     >     },  
>     > }

This avoids the need to enable Django debug mode and is better in as much as the details will be captured persistently in the error log, rather than them only appearing on a transient web browser page, which would be lost when visiting another URL.

One final option with Django is to configure it so that it will not catch the exceptions raised within your code when handling a request and convert it to a HTTP 500 server error response page itself.

> 
>     DEBUG_PROPAGATE_EXCEPTIONS = True

With this setting enabled, what will instead happen is that the exception will be allowed to propagate out from Django. Provided the Django application itself isn’t wrapped by some WSGI middleware that catches and suppresses the exception, the exception will make it all the way up to the WSGI server, which would generate its own HTTP 500 server error response page.

In the case of mod\_wsgi, when an exception does propagate all the way back to the WSGI server, the exception details will be automatically logged to the error log. This logging of exceptions by mod\_wsgi will actually occur for a number of different situations and covers situations where Django itself wouldn’t be able to log anything, such as where an exception occurred in the generator returned within a streaming HTTP response.

So we have three different options we could rely on, but which do we use?

As it turns out, all three are useful depending on what you want to do. The question then is how do we make them easier to use when mod\_wsgi-express is being used, without you needing to go in and modify the Django settings module all the time, and potentially forgetting to revert a setting like that for Django debug mode when moving to production.

# Logging of handler exceptions

Even though it isn’t the default, I would always recommend that the ‘LOGGING’ setting be configured to log to the error log when using Apache/mod\_wsgi. In this way you always have a record of exceptions, even in the case where the delivery of log messages to an offsite service failed for some reason.

If for some reason you do not want to log to the error log file all the time and only wish to do it when using mod\_wsgi-express, were it only being used in a development setting, then you can vary how the ‘LOGGING’ setting is configured by checking for the existence of the ‘MOD\_WSGI\_EXPRESS’ environment variable.

> 
>     if os.environ.get('MOD_WSGI_EXPRESS'):  
>     >     LOGGING = {  
>     >         …  
>     >     }

This environment variable will only be set when using mod\_wsgi-express and not when using a manually configured instance of Apache running mod\_wsgi.

When using mod\_wsgi-express as a development server, if having to actually go to the error log file is seen as inconvenient and you would rather see errors directly in the terminal, then you can use the ‘—log-to-terminal’ option when running mod\_wsgi-express.

# Exception debugging mode

Django has its debug mode which is enabled using the ‘DEBUG’ setting. When running mod\_wsgi-express it also has its own special debug mode. This is enabled by supplying the ‘—debug-mode’ option. 

So if running 'mod\_wsgi-express’ directly, one would use:

> 
>     mod_wsgi-express start-server —debug-mode app.wsgi

If using mod\_wsgi-express integrated with a Django project, then you would use:

> 
>     python manage.py runmodwsgi —debug-mode

Use of this option actually makes mod\_wsgi-express behave even more like traditional development servers in that it will only run with a single process and single thread. This mode also opens up access to a range of special debug features in mod\_wsgi-express as well.

Do be aware though that use of debug mode in mod\_wsgi-express will disable the automatic code reloading feature were it enabled and you will need to exit mod\_wsgi-express explicitly and restart it to pick up code changes if running in this mode. As you would only be using this mode from the command line when debugging problems in your code, this is not seen as a big issue.

The general workflow would therefore be to run mod\_wsgi-express in its default multithreaded mode with code reloading enabled as you make code changes. When a problem then occurs, you would drop down into debug mode to work out the cause of an issue.

As this debug mode of mod\_wsgi-express is a special mode, what can now be done is to trigger the enabling of Django debug mode off it being run. This will then have the effect of enabling the display of exceptions details within the browser. To do this the Django setting files would be configured as:

> 
>     # SECURITY WARNING: don't run with debug turned on in production!  
>     > if os.environ.get('MOD_WSGI_DEBUG_MODE'):  
>     >     DEBUG = True  
>     > else:  
>     >     DEBUG = False

By triggering Django debug mode off of the mod\_wsgi-express debug mode, you reduce the risk that you might accidentally leave the Django debug mode enabled as you wouldn’t need to keep changing the setting. Instead Django debug mode would be enabled as a side effect purely of the ‘—debug-mode’ option being supplied to mod\_wsgi-express.

# Post mortem debugging

Although Django debug mode enables the display of exception details, including values of local variables on the stack frames, it doesn’t allow you to interact with the Python interpreter itself beyond that. Such post mortem debugging generally requires the use of ‘pdb’ or some other debugger IDE.

In order to use ‘pdb’ to debug such a problem, one would normally have to modify your application code to introduce special code to invoke ‘pdb’ when an exception occurs.

When using debug mode of mod\_wsgi-express a simpler way is however available for performing post mortem debugging of an exception raised within your handler code.

To enable this feature if running 'mod\_wsgi-express’ directly, one would use the ‘—enable-debugger’ option in conjunction with the ‘—debug-mode’ option:

> 
>     mod_wsgi-express start-server —debug-mode —enable-debugger app.wsgi

Now when an exception occurs within your handler and that exception propagates back up to the WSGI server level, you will be automatically thrown into a ‘pdb’ debugger session.

> 
>     > /Users/graham/Testing/django-site/mysite/mysite/views.py(4)home()  
>     > -> raise RuntimeError('xxx')  
>     > (Pdb)

If using mod\_wsgi-express integrated with a Django project, then you could also use:

> 
>     python manage.py runmodwsgi —debug-mode —enable-debugger

However, as explained above, exceptions under Django will be caught and translated into a generic HTTP 500 server error response page. In order to disable this, we need to configure Django to allow exceptions to be propagated back up to the WSGI server. This is so that ‘pdb’ can catch the exception and enter debugging mode.

As we only want exceptions to be propagated back up to the WSGI server when enabling post mortem debugging, then we can qualify the configuration in the Django settings module using:

> 
>     if os.environ.get('MOD_WSGI_DEBUGGER_ENABLED'):  
>     >     DEBUG_PROPAGATE_EXCEPTIONS = True

By checking for the ‘MOD\_WSGI\_DEBUGGER\_ENABLED’ environment variable, we are ensuring again that we don’t accidentally leave this enabled when deploying to production.

Now the debugger as shown only provides the ability to perform post mortem debugging. What though if you wanted to debug from an arbitrary point in your code before the point where the exception occurred?

You could again resort to modifying your code to add in the calls to ‘pdb’ to invoke it at the desired location, but you would at least still need to force mod\_wsgi-express to run in single process mode with stdin/stdout of the process properly attached to the terminal, using the ‘—debug-mode’ option.

An alternative provided by mod\_wsgi-express to avoid needing to modify your code even in this case is available with the ‘—debugger-startup’ option.

So if running 'mod\_wsgi-express’ directly, one would also add the ‘—debugger-startup’ option:

> 
>     mod_wsgi-express start-server —debug-mode —enable-debugger —debugger-startup app.wsgi

If using mod\_wsgi-express integrated with a Django project, then you would use:

> 
>     python manage.py runmodwsgi —debug-mode —enable-debugger —debugger-startup

What this option will do is throw you into ‘pdb’ as soon as the process has been started.

> 
>     > /Users/graham/.virtualenvs/django/lib/python2.7/site-packages/mod_wsgi/server/__init__.py(1040)__init__()->None  
>     > -> self.activate_console()  
>     > (Pdb)

At the ‘pdb’ prompt you can then set breakpoints for where you want the debugger to be later triggered when handling a request and resume the debugging session.

> 
>     (Pdb) import mysite.views  
>     > (Pdb) break mysite.views.home  
>     > Breakpoint 1 at /Users/graham/Testing/django-site/mysite/mysite/views.py:3  
>     > (Pdb) cont

When a subsequent request then results in that code being executed, the ‘pdb’ prompt will once again be presented allowing you to step through the code from that point or interrogate any objects available in that context.

> 
>     (Pdb) list  
>     >   1     from django.http import HttpResponse  
>     >   2  
>     >   3 B    def home(request):  
>     >   4  ->      raise RuntimeError('xxx')  
>     >   5          #return HttpResponse('Hello world!')  
>     > [EOF]  
>     > (Pdb) locals()  
>     > {'request': <WSGIRequest: GET '/'>}

# Production capable by default

So what we ultimately have here is that mod\_wsgi-express in its default configuration is production capable, but it can optionally be setup for use in a development environment.

The first option one has is to leave it in its more production capable mode, but enable source code reloading as a convenience. The second option is to force it into a true debug mode where everything runs in the one process, with the process properly attached to the terminal so as to allow direct interaction with the process. This debug mode then permits the use of the Python debugger ‘pdb’.

In order to allow better integration with web frameworks when working in debug mode or when specific debug mode features are enabled, environment variables are set to allow the web framework or application settings to be customised automatically, thereby ensuring the best expirience is available.

As mentioned, mod\_wsgi-express also has other capabilities available once in debug mode. These include code profiling and coverage support. I will discuss those and other development centric features in subsequent posts.

---

## Comments

### Tom A - May 7, 2015 at 7:13 PM

Thanks for your work on this Graham, and for taking the time to demonstrate usage with clear examples.

