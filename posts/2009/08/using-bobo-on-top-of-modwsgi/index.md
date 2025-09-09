---
title: "Using bobo on top of mod_wsgi."
author: "Graham Dumpleton"
date: "Thursday, August 20, 2009"
url: "http://blog.dscpl.com.au/2009/08/using-bobo-on-top-of-modwsgi.html"
post_id: "3088895753070338298"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 0
published_timestamp: "2009-08-20T12:37:00+10:00"
blog_title: "Graham Dumpleton"
---

From the little I have looked at it, I like [bobo](http://bobo.digicool.com/). I guess the reason is that it doesn't try and do too much. In that sense it has that simplicity that attracted many people to the publisher handler provided with mod\_python, and which allows one to actually create an application, handling multiple URLs, completely within one code file. And because bobo uses WSGI to interface to the web server, it can of course be used in conjunction with [mod\_wsgi](http://www.modwsgi.org/) and doing so is surprisingly easy.

  


As example, consider the simple bobo application as follows:
    
    
```
import bobo  
```
      
```
@bobo.query  
def hello():  
 return "Hello world!"  
```
    

All one has to do to turn this into a WSGI script file suitable for use with mod\_wsgi is add the single line:
    
    
```
application = bobo.Application(bobo_resources=__name__)
```

This one line creates an instance of the bobo WSGI application object and assigns it to 'application', the name of the WSGI application entry point which mod\_wsgi expects to exist.

  


The '\_\_name\_\_' variable here is the name of the Python module containing the code. In other words, you are telling bobo to map requests back onto the same code file. 

  


For normal Python modules the '\_\_name\_\_' variable, which is automatically put there by Python, would be the module name and or package path used when importing the module. For mod\_wsgi the variable doesn't have quite the same meaning, but still exists, and is still used as the key into 'sys.modules' where the loaded module is placed.

  


To map the bobo application file at a specific URL, one uses WSGIScriptAlias or AddHandler mechanisms as normal for mod\_wsgi.

  


In mod\_wsgi 3.0 there is also a new feature that one could use to define a handler script for all bobo application script files and which transparently performs the job of creating the instance of 'bobo.Application\(\)' for you. If this were used, one could place bobo application script files in a directory using a specific extension, just like with PHP, and not even have to worry about adding the line above. Any change to those files would also result in the process being reloaded if using mod\_wsgi daemon mode. I'll talk about this trick another time.