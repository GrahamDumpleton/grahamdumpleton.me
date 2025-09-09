---
title: "New Relic is not just for Apache/mod_wsgi."
author: "Graham Dumpleton"
date: "Wednesday, November 2, 2011"
url: "http://blog.dscpl.com.au/2011/11/new-relic-is-not-just-for-apachemodwsgi.html"
post_id: "8401475210345954191"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'new relic', 'python']
comments: 2
published_timestamp: "2011-11-02T17:11:00+11:00"
blog_title: "Graham Dumpleton"
---

A number of people have expressed an interest in using the Python agent with [New Relic](http://www.newrelic.com/) but they didn't want to have to use Apache/mod\_wsgi. No such restriction actually exists. The New Relic Python agent should work with any WSGI 1.0 compliant web server.

  


In addition to Apache/mod\_wsgi, we already have people using it with gunicorn, uWSGI, the Tornado WSGI container, CherryPy WSGI server and FASTCGI/flup. In the case of gunicorn you can also use eventlet and gevent modes as the Python agent will adapt and automatically detect whether threads or greenlets are being used where necessary. It is even possible to run the Python agent when using the Django development server although why you would want to do that except to prove it is possible, as I did, I am not sure.

  


The only restriction we do know of at present is when using uWSGI. uWSGI still appears that it may have some issues with multithreading when using Python sub interpreters. In the case of uWSGI therefore, in addition to needing to supply '--enable-threads' to the 'uwsgi' program to initialise threading in the Python core and so allow additional background Python threads to be created, you also need to use the '--single-interpreter' option to ensure the main Python interpreter is used. I have been conversing with the uWSGI author about this and when I get the time I will sit down and audit the uWSGI code and provide some advice about use of Python thread state objects and sub interpreters gleaned from all my work on doing the same in mod\_wsgi.

  


As far as web frameworks go the best supported is Django. We also have specific support to varying degrees for Bottle, CherryPy, Flask, Pylons and Web2py. We have users for all of those except for Web2py. Pyramid is the next on our list to add support for.

  


As well as instrumenting the frameworks themselves, a number of other Python modules for databases, memcache and template systems also have special treatment so can track time spent there. We will slowly be building out support for more and more packages as interest is expressed. The next on our list here is support for Celery.

  


If you are rolling your own web application from component libraries such as Werkzeug, Paste and WebOb, then because you will have a custom structure for URL routing and handler execution, it is not possible to automatically collect certain data we need to make the results more useful. In these cases you will need to make use of the APIs for the Python agent to perform tasks such as naming web transactions and recording exceptions which would otherwise be converted to a 500 error page response internally to your web application.

  


When it comes to Python web hosting services, we know of the Python agent being used on WebFaction, dotcloud, Heroku and ep.io. It is also possible to use the Python agent with Stackato.

  


Various documentation can be found on all of this on the [New Relic knowledge base](http://newrelic.com/docs/python/new-relic-for-python) and busy working on more which will be up soon.

---

## Comments

### MW - December 16, 2011 at 3:55 AM

Great to see you working on support for Pyramid and Celery. Can you unofficially name some dates regarding when something will be ready since this is exactly our stack.  
We've been running New Relic on it for two months now and it works great, but a bit more detail in some areas would be really welcome. The icing on the top would be support for Redis.

### Graham Dumpleton - December 16, 2011 at 10:57 AM

Celery support is available and described at http://newrelic.com/docs/python/python-agent-and-celery.  
  
Pyramid can already be used, you just miss out on better web transaction naming and capture of exceptions which framework otherwise turns into 500 error response pages rather than allowing to propagate up. Even with the limitations we have some users who use Pyramid already.

