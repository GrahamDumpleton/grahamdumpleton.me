---
title: "Using mod_wsgi when developing Django sites."
author: "Graham Dumpleton"
date: "Friday, December 19, 2008"
url: "http://blog.dscpl.com.au/2008/12/using-modwsgi-when-developing-django.html"
post_id: "1212814783947719250"
blog_id: "2363643920942057324"
tags: ['django', 'mod_wsgi']
comments: 14
published_timestamp: "2008-12-19T21:24:00+11:00"
blog_title: "Graham Dumpleton"
---

If one were to ask on the Django forums or irc channels what server to use when developing a Django site, the advice generally given is to use Django's own internal development server and to only deploy it under [mod\_wsgi](http://www.modwsgi.org/) or another hosting mechanism when moving it into production. One of the main reasons given for doing this is that Django's development server will detect when you make code changes and automatically restart the Django process.

  


What seems to be not well known though is that mod\_wsgi can also be setup to automatically restart the Django processes. Yes, some know about the ability when using mod\_wsgi daemon mode to touch the WSGI script file and have the Django process restarted, but what I am talking about here is a completely automated system which will detect changes to any Python code files and restart the Django process, just like with the Django development server, and not just when a change is made to the WSGI script file. This automated system completely avoids the need to manually touch the WSGI script file after you have made any changes.

  


How this can be achieved is described in section 'Restarting Daemon Processes' of the mod\_wsgi documentation about [source code reloading](http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode#Restarting_Daemon_Processes). What I will do here though is summarise how that code recipe can be applied to a Django site.

  


Actual setup instructions for using Django with mod\_wsgi are described in the [Django integration guide](http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango) on the mod\_wsgi site. Although they contain the important information you need, it is still best to have also read the [quick configuration guide](http://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide) and [configuration guidelines](http://code.google.com/p/modwsgi/wiki/ConfigurationGuidelines). 

  


The example configuration give in the Django integration guide for using daemon mode is:
    
    
```
WSGIDaemonProcess site-1 user=user-1 group=user-1 threads=25  
WSGIProcessGroup site-1  
```
      
```
Alias /media/ /usr/local/django/mysite/media/  
```
      
```
<Directory /usr/local/django/mysite/media>  
Order deny,allow  
Allow from all  
</Directory>  
```
      
```
WSGIScriptAlias / /usr/local/django/mysite/apache/django.wsgi  
```
      
```
<Directory /usr/local/django/mysite/apache>  
Order deny,allow  
Allow from all  
</Directory>  
```
    

The corresponding example WSGI script file is:
    
    
```
import os, sys  
sys.path.append('/usr/local/django')  
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'  
```
      
```
import django.core.handlers.wsgi  
```
      
```
application = django.core.handlers.wsgi.WSGIHandler()  
```
    

It is this latter WSGI script file to which we need to make an addition. Rather than make all the changes to this file though, we will add a new Python code file into the Django site directory and put the bulk of the code in it.

  


So, in the same directory as where the 'settings.py' file is for your Django site, add a file called 'monitor.py'. In this file place the code recipe for implementing an automatic restart mechanism from the mod\_wsgi documentation on [reloading source code](http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode#Restarting_Daemon_Processes). Then go back to the WSGI script file and at the end of the file add:
    
    
```
import mysite.monitor  
mysite.monitor.start(interval=1.0)  
```
    

Obviously, the name of your site being different, you should substitute 'mysite' with the actual name of your site. Anyway, that is all that is required.

  


What will now happen is that when the WSGI script file is loaded, it will initialise the code which will monitor changes to any code files. This will have the side affect of creating a background thread which will periodically scan through all the loaded Python modules and try to determine if the corresponding file on disk has been changed since the last scan. If a change is detected, then the thread will signal the process that it needs to be shutdown. When shutdown is complete, mod\_wsgi will detect this and startup a new process in its place. Upon a subsequent request for your Django site, the WSGI script file is loaded once more and we start over.

  


Now, why develop your Django site using mod\_wsgi? There are a few reasons.

  


The first is that if mod\_wsgi is going to be your production target anyway, you are guaranteed from the start that you will have an equivalent environment and not be hit with problems often seen whereby code works with the development server but not under mod\_wsgi. Using mod\_wsgi you will know about these issues sooner and be able to ensure mod\_wsgi and your environment is configured correctly.

  


The second is that the Django development server is only single threaded. As a result, it isn't really a suitable test bed for ensuring your code is multithread safe through the whole development process.

  


A third is that Django development server is a single process web server. If using mod\_wsgi it is quite likely you would deploy with a configuration which makes use of multiple process to handle requests. One cannot simulate this type of setup easily with the development server.

  


Finally, with mod\_wsgi the setup would be close to if not the same as your deployment configuration. This means that you could do realistic tests of how well your application will perform all through the development process through running suitable benchmarks. This would allow you to identify much earlier any performance bottlenecks without having to go through a process of first having to install on a separate staging environment.

  


Just remember though when you do go to release to your production environment, or even just enable the development instance as the live site, that you disable the code monitor. The overhead may not be noticeable in the grand scheme of things, but better to avoid having processes restart when you least expect them to.

  


BTW, mod\_wsgi daemon mode requires Apache 2.X on UNIX. The feature is not available on Apache 1.3 or Windows.

---

## Comments

### Waldemar - December 20, 2008 at 2:00 PM

any chance the functionality will be available on Windows one day?

### Graham Dumpleton - December 20, 2008 at 3:11 PM

Windows doesn't support forking of processes and so cannot support daemon mode as it is currently implemented in mod\_wsgi. You will therefore not see that feature.  
  
As for the automated restarts when code changes are detected, there is an outside chance that this could be made to work now even though embedded mode is all that is supported.  
  
This is because on Windows there is only one process handling requests, and so having it signal the parent monitor process to trigger a restart is probably reasonably safe.  
  
What might thus be able to be done is to use Python ctypes module to call the Apache function ap\_signal\_parent\(\). The argument to this function should be enumeration value SIGNAL\_PARENT\_RESTART. If assigning of enumerated values follows what one would normally expect, this would be a integer value of 1.  
  
I am not a Windows person, but if you want to explore whether that can be done or not, post a message to mod\_wsgi mailing list on Google groups and can discuss it there.

### None - December 26, 2008 at 1:38 PM

I've never once used the Django dev server for local development. Previously it was apache and mod\_python, and now we all use mod\_wsgi. I simply set the max child processes value to 1 so the process constantly dies. I haven't noticed any performance issues locally with this method, my local server is fast as a bat out of hell... even when some of our dev code isn't exactly the fastest :P Any real reason to move away from this and have the process detect code changes and restart when only necessary?

### Graham Dumpleton - December 26, 2008 at 2:55 PM

Using MaxRequestsPerChild or maximum-requests, if using mod\_wsgi daemon mode, set to a value of 1 will only serve to slow things down. If you are the only user and requests are infrequent, so long as your application doesn't have large startup costs can still be okay, but seems a bit wasteful.

### None - February 10, 2009 at 1:47 PM

While on the subject of mod\_wsgi and Django, it seems that the following page needs to be updated \(towards the end in the paragraphs that involve threading issues\):  
  
http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango  
  
The link provided on that page regarding the threading issues seems to imply that threading is confirmed to work in Django 1.0 and up; the paragraphs surrounding the link, however, seem to be about Django releases prior to 1.0.  
  
Apologies if this is an inappropriate place to mention this, but I was not sure where was best to contact you.  
  
Also, thank you for the good article.

### Graham Dumpleton - February 10, 2009 at 2:39 PM

The referenced page about Django threading issues is a Django user contributed page and does not represent an official statement from the core Django developers. The core Django documentation still recommends use of prefork MPM for Apache and mod\_python, that is, single threaded environment. Until the core Django developers change their recommendation and make a clear statement that Django 1.0+ is thread safe, I'll probably continue to give more emphasis to the warnings that there may be threading issues.

### Graham Dumpleton - February 26, 2009 at 10:18 AM

See http://blog.dscpl.com.au/2009/02/source-code-reloading-with-modwsgi-on.html for how to adapt this to Windows.

### Unknown - June 22, 2009 at 8:52 PM

Hey Graham  
  
Thank you for pointing me to this wonderful post of yours \(It works like my fingers on the keyboard\! hehe\)  
  
Now I am having a problem with the trailing slashes, what to I need to do in order for http://localhost/upload to be http://localhost/upload/ since my settings.py file has APPEND\_SLASH = True but when I visit http://localhost/upload I am greeted with an **internal server error**  
Cheers and thanks again.

### Graham Dumpleton - June 22, 2009 at 9:32 PM

@Josie: You are better off taking your upload issue to django-users list on Google Groups. You will possibly need to provide a bit more detail than that, such as how you are setting up route for upload directory in urls.py etc.

### rocketmonkeys - November 12, 2009 at 8:05 AM

Hey graham, thanks so much for posting the code\! I've modified it to use it on windows, works great.  
  
http://www.rocketmonkeys.com/post.364  
  
Makes things so much nicer to develop in windows when using apache instead of the 'manage.py runserver'. Thanks again.

### Graham Dumpleton - November 12, 2009 at 8:13 AM

rocketmonkeys: Why did you modify it how you did.?The separate post at http://blog.dscpl.com.au/2009/02/source-code-reloading-with-modwsgi-on.html and the documentation on mod\_wsgi site at http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode already explain better way of doing it for Windows.

### GamesBook - March 3, 2010 at 6:20 PM

You say that "the core Django documentation still recommends use of prefork MPM for Apache and mod\_python"  
  
But on this page:  
http://docs.djangoproject.com/en/1.0/howto/deployment/  
\(which AFAIK is an official Django doc\) it reads:  
  
"If you’re new to deploying Django and/or Python, we’d recommend you try mod\_wsgi first. In most cases it’ll be the easiest, fastest, and most stable deployment choice."

### Graham Dumpleton - March 3, 2010 at 8:12 PM

GamesBook, this blog post was made over a year ago. At that time the Django documentation still recommended mod\_python.

### Unknown - December 31, 2010 at 9:01 AM

Thanks, this is a life saver

