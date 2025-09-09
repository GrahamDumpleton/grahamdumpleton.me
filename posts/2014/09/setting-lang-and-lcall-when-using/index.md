---
title: "Setting LANG and LC_ALL when using mod_wsgi."
author: "Graham Dumpleton"
date: "Monday, September 1, 2014"
url: "http://blog.dscpl.com.au/2014/09/setting-lang-and-lcall-when-using.html"
post_id: "923005330204443794"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 9
published_timestamp: "2014-09-01T15:26:00+10:00"
blog_title: "Graham Dumpleton"
---

So I am at DjangoCon US 2014 and one of the first pain points for using mod\_wsgi that came up in discussion at DjangoCon US was the lang and locale settings. These settings influence what the default encoding is for Python when implicitly converting Unicode to byte strings. In other words, they dictate what is going on at the Unicode/bytes boundary.

Now this should not really be an issue with WSGI at least, because you should always be explicitly specifying the encoding you want the response content to be when it is being returned from the WSGI application and that should match the 'charset' attribute specified in the 'Content-Type' response header. There are however lots of other cases where the problem can still present itself.

Take for example a simple case in a command line interpreter of printing out the value of a Unicode string into the Apache error log:
    
    
```
>>> print(u'\u292e')  
⤮
```

On a system with a sane configuration, this would display as you expect. The reason for this is that the your login shell environment would typically set an environment value such as the 'LANG' environment variable. On my MacOS X system for example I have:
    
    
```
LANG=en_AU.UTF-8
```

When I use the 'locale' module to see what Python sees, we get:
    
    
```
>>> import locale  
>>> locale.getdefaultlocale()  
('en_AU', 'UTF-8')  
>>> locale.getpreferredencoding()  
'UTF-8'
```

UTF-8 is generally the magic value that solves all problems. With that you should generally be okay.

The problem now is that when using Apache/mod\_wsgi on many Linux systems, the Apache process doesn't inherit any environment variables which override the default locale or language settings. So what the Python code running under Apache/mod\_wsgi sees is:
    
    
```
>>> import locale  
>>> locale.getdefaultlocale()  
(None, None)  
>>> locale.getpreferredencoding()  
'US-ASCII'
```

With the Python interpreter now using these values, if we try and print out a Unicode value, we can encounter problems.
    
    
```
>>> print(u'\u292e')  
Traceback (most recent call last):  
 File "<stdin>", line 1, in <module>  
UnicodeEncodeError: 'ascii' codec can't encode character u'\u292e' in position 0: ordinal not in range(128)
```

And this is the trap that people encounter when using Apache/mod\_wsgi. They will run up their Python WSGI application with a development server, such as that provided by Django, and everything will work fine. Host Apache/mod\_wsgi on a Linux system though, and if they have not ensured that encodings are always being used explicitly when converting from Unicode to bytes, they can start to get 'UnicodeEncoderError' exceptions.

What is the solution then?

As is detailed in the [Django documentation](https://code.djangoproject.com/wiki/django_apache_and_mod_wsgi#AdditionalTweaking), you can set the environment variables yourself.
    
    
```
export LANG='en_US.UTF-8'  
export LC_ALL='en_US.UTF-8'
```

The problem now is where do you set them. This is because they need to be set in the environment under which the initial Apache process starts up.

For a standard Apache Software Foundation layout for an Apache httpd installation, the file this needs to be put in is the 'envvars' file. This file would exist in the same directory as where 'apachectl' resides.

The location means though that you are modifying what is a system file. If you upgrade Apache it is quite possible, unless the package update looks for an existing file, that it will be overridden.

A further problem is that Linux systems generally do not use the Apache Software Foundation installation layout and do away with the 'envvars' file completely. In these cases you have to find the correct system init script file to add the settings in. What file this is, differs between Linux distributions.

So being able to override the value for the lang and locale can be a pain. It can differ between Linux distributions and even changing the file may not survive system package upgrades.

Is there a better solution?

If using embedded mode of mod\_wsgi to run your WSGI application with Apache the answer is currently no.

This isn't because it is technically impossible, but because Apache can be used to host more than just Python web applications at the same time and I didn't think it would be particularly friendly to provide a mod\_wsgi configuration directive which modified the lang and locale for the whole of Apache, thereby affecting other Apache modules.

Was this a wise choice, I am not sure. I am probably still open to providing such an option to override them for the whole of Apache, but certainly would need to document the dangers of using it.

The thing is though, that unless you really know what you are doing, you shouldn't be using embedded mode of mod\_wsgi on UNIX systems anyway, even though it is the default. The preferred and better configuration is to use mod\_wsgi daemon mode.

For mod\_wsgi daemon mode then, what can be done?

For this way of using mod\_wsgi what you can do is set the 'lang' and 'locale' options to the 'WSGIDaemonProcess' directive.
    
    
```
WSGIDaemonProcess my-django-site lang='en_US.UTF-8' locale='en_US.UTF-8'
```

For daemon mode of mod\_wsgi at least, that is the solution for this particular pain point.

Do note though that you must be using mod\_wsgi 3.4 or later to have access to these options of the 'WSGIDaemonProcess' directive.

---

## Comments

### MIchael - July 22, 2016 at 12:26 AM

Thanks a lot\!  
  
Spend couple of hours trying to figure out why my Django app works with runserver and SQLite and does not worl on Apache2 and MySQL.  
  
The reason was this LANG stuff...

### Unknown - March 3, 2017 at 9:42 AM

Another vote of thanks. Couldn't work out why python couldn't read a UTF-8 file \(Greek text\) on Apache, yet worked just fine on both my Mac and on the command-line of the Linux server\! Spent a couple of hours tearing my hair out. You'd think in this day and age a sensible UTF-8 environment config for Apache would be the default\!

### xbartolone - July 12, 2017 at 9:24 PM

Thanks a lot Graham\!  
  
Unfortunately setting those variables when using mod\_wsgi doesn't suffice. I'm facing the error cause sys.getdefaultencoding\(\) still says "ascii" so an upload form is failing. I'm working on x64 - CentOS 7 - 1611 Core  
  
None of the alternative methods solves even setting PYTHONIOENCODING 'utf-8' in /etc/sysconfig/httpd.

### Graham Dumpleton - July 12, 2017 at 9:36 PM

@xbartolone Use the mod\_wsgi mailing list to ask about it. If you are trying to use daemon mode, you wouldn't be the first to have the configuration wrong such that you aren't actually using daemon mode as intended. Set 'WSGIRestrictEmbedded On' outside of 'VirtualHost' and see if your requests fail. That options disables embedded mode, so you will quickly find out if you got your configuration wrong.

### xbartolone - July 12, 2017 at 9:46 PM

Nothing changed also with the directive you have suggested. Thanks anyway, trying to ask on the mailing list but I suspect those variables affect only the Locale module not the sys one...

### Graham Dumpleton - July 12, 2017 at 10:03 PM

I know of no current issues with the lang/locale settings on WSGIDaemonProcess not working as intended. How old is the mod\_wsgi version you are using?

### xbartolone - July 12, 2017 at 10:09 PM

It comes from EPEL 7.9  
  
Name : mod\_wsgi  
Arch : x86\_64  
Version : 3.4  
Release : 12.el7\_0

### Graham Dumpleton - July 12, 2017 at 10:26 PM

It would be because you are using such an old mod\_wsgi version. There were some issues with lang/locale options way back then. Any chance you can not use the system package for mod\_wsgi and use 'pip install mod\_wsgi' to install yourself and then use result of running 'mod\_wsgi-express module-config' to get configuration to use to load module installed using 'pip'. See https://pypi.python.org/pypi/mod\_wsgi

### xbartolone - July 12, 2017 at 10:42 PM

I can try with this workaround. Thanks, I'll keep you updated.

