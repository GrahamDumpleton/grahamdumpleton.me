---
title: "Save on memory with mod_wsgi 3.0."
author: "Graham Dumpleton"
date: "Thursday, November 26, 2009"
url: "http://blog.dscpl.com.au/2009/11/save-on-memory-with-modwsgi-30.html"
post_id: "3167667529418787563"
blog_id: "2363643920942057324"
tags: ['mod_wsgi']
comments: 3
published_timestamp: "2009-11-26T21:54:00+11:00"
blog_title: "Graham Dumpleton"
---

Various people like to complain that Apache is a memory hog, especially when running Python web applications using [mod\_wsgi](http://www.modwsgi.org/) or mod\_python. Reality is, any excessive memory usage is usually because they just don't have a clue how to configure Apache properly for the type of application being run. In other words they only have themselves to blame.

Anyway, with mod\_wsgi 3.0 there has been some changes which affect how memory is used by mod\_wsgi. If you are only using daemon mode you can use these changes to your benefit to disable initialisation of the Python interpreter in the main Apache server child processes. The result will be that you can cut back on some of the memory which would otherwise be used. For a memory limited VPS system, every little bit can count.

In versions of mod\_wsgi prior to version 3.0 the Python interpreter was always preinitialised in the Apache parent process. This did mean that theoretically some benefit in memory usage could be derived from delayed copy on write semantics of memory inherited by child processes that was initialised in the parent. This memory wasn't significant however and was tempered by the fact that the Python interpreter when destroyed and then reinitialised in the Apache parent process on an Apache restart, would with some Python versions leak memory. This meant that if a server had many restarts performed, the Apache parent process and thus all forked child processes could grow in memory usage over time, eventually necessitating Apache be completely stopped and then restarted.

This issue of memory leaks with the Python interpreter reached an extreme with Python 3.0, where by design, various data structures would not be destroyed on the basis that it would be reused when Python interpreter was reinitialised within the same process. The problem is that when an Apache restart is performed, mod\_wsgi and the Python library are unloaded from memory, with the result that the references to that memory would be lost and so a real memory leak, of significant size and much worse that older versions of Python, would result.

As a consequence, with mod\_wsgi 3.0 and onwards, the Python interpreter is not initialised by default in the Apache parent process for any version of Python. This avoids completely the risk of cummulative memory leaks by the Python interpreter on a restart into the Apache parent process, albeit with potential for slight increases in child process memory sizes.

Although the default is now for lazy initialisation of the Python interpreters to be performed, this can be controlled using the new WSGILazyInitialization directive. So, if need be, the existing behaviour can be restored by setting the directive with the value 'Off'.

A further upside of using lazy initialisation is that if you are using daemon mode only, ie., not using embedded mode, you can completely turn off initialisation of the Python interpreter within the main Apache server child process. Unfortunately, because it isn't possible in the general case to know whether embedded mode will be needed or not, you will need to manually set the configuration to do this. This can be done by setting:
    
    
```
WSGIRestrictEmbedded On
```

The directive if used should appear at global server scope, outside of any VirtualHost definitions.

With restrictions on embedded mode enabled, any attempt to run a WSGI application in embedded mode will fail, so it will be necessary to ensure all WSGI applications are delegated to run in daemon mode. Although WSGI applications will be restricted from being run in embedded mode and the Python interpreter therefore not initialised, it will fallback to being initialised if you use any of the Python hooks for access control, authentication or authorisation providers, or WSGI application dispatch overrides.

Note that if mod\_python is being used in the same Apache installation, because mod\_python takes precedence over mod\_wsgi in initialising the Python interpreter, lazy initialisation cannot be done and so Python interpreter will continue to be preinitialised in the Apache parent process regardless of the setting of WSGILazyInitialization. Use of mod\_python will thus perpetuate the risk of memory leaks and growing memory use of Apache process. This is especially the case since mod\_python doesn't even properly destroy the Python interpreter in the Apache parent process on a restart and so all memory associated with the Python interpreter is leaked and not just that caused by the Python interpreter when it is destroyed and doesn't clean up after itself.

In summary, if only using daemon mode of mod\_wsgi and you have upgraded to mod\_wsgi 3.0, try adding the WSGIRestrictedEmbedded directive to your Apache configuration and hopefully you will see the size of the main Apache server child processes drop. Preferably you are using Apache worker MPM at this point, but if having to use Apache prefork MPM, the saving over all the Apache server child processes could be noticeable.

Oh, and if you thought you were using daemon mode and it turns out you weren't, then using this directive will also pick up that fact as your WSGI applications will start failing.

BTW, these changes only apply where daemon mode is available, so is not relevant to Apache 1.3 or Windows users.

---

## Comments

### Graham Dumpleton - November 26, 2009 at 10:33 PM

Hmmm, I kept saying mod\_wsgi 3.0. Actually, mod\_wsgi 3.1 is already available, although it was only a slight change to address a build issue. So, if already have mod\_wsgi 3.0 and it is working, no need to upgrade to 3.1 at this point.

### Dave Everitt - October 22, 2010 at 11:12 PM

I'm gradually working through the pages relevant to running Django and, for my own reference, condensing your extremely informative info to the absolutely necessary as I proceed.  
  
So, just to be crystal clear: the presumption is that **WSGILazyInitialization** must also be set at global scope, as is the case with **WSGIRestrictEmbedded**?

### Graham Dumpleton - October 23, 2010 at 7:52 AM

Yes, WSGILazyInitialization must be at server config level. See http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives\#WSGIRestrictEmbedded and http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives\#WSGILazyInitialization

