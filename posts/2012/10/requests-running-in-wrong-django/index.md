---
title: "Requests running in wrong Django instance under Apache/mod_wsgi."
author: "Graham Dumpleton"
date: "Monday, October 8, 2012"
url: "http://blog.dscpl.com.au/2012/10/requests-running-in-wrong-django.html"
post_id: "6436998120984913197"
blog_id: "2363643920942057324"
tags: ['apache', 'django', 'mod_wsgi']
comments: 17
published_timestamp: "2012-10-08T23:21:00+11:00"
blog_title: "Graham Dumpleton"
---

Configuring [Apache/mod\_wsgi](http://www.modwsgi.org/) to host multiple Django instances has always been a bit tricky for some. In practice though it should be quite straight forward. For a single Django instance mounted at the root of the web site, the WSGIScriptAlias line would be something like:  
  
WSGIScriptAlias / /some/path/project-1/wsgi.py  
  
If wanting to host a second Django instance under the same host name but at a sub URL, you would use:  
  
WSGIScriptAlias /suburl /some/path/project-2/wsgi.py  
WSGIScriptAlias / /some/path/project-1/wsgi.py  
  
If the Django instances are not under the same host, then it would instead simply be a matter of adding them to the respective VirtualHost.  
  
<VirtualHost \*:80>  
ServerName site-1.example.com  
WSGIScriptAlias /some/path/project-1/wsgi.py  
...  
</VirtualHost>  
  
<VirtualHost \*:80>  
ServerName site-2.example.com  
WSGIScriptAlias /some/path/project-2/wsgi.py  
...  
</VirtualHost>  
  
In both cases, whether under the same host name or different ones, both Django instances would run in the same process. Separation would be maintained however by virtue of mod\_wsgi running each WSGI application mounted using WSGIScriptAlias in a distinct Python sub interpreter within the processes they are running in.  
  
The directive which controls which named Python sub interpreter within the process is used is WSGIApplicationGroup. The default for this directive is %\{RESOURCE\}.  
  
For this default value of %\{RESOURCE\}the sub interpreter name will be constructed from the host name \(as specified by the ServerName directive\), the port \(if not port 80/443\) and the value of the WSGI environment variable SCRIPT\_NAME as deduced from the URL mount point set by the WSGIScriptAlias directive.  
  
So in the first instance above where both Django instances run under the same host name, the distinct named sub interpreters within the process would be called:  
  
site-1.example.com:/  
site-1.example.com:/suburl  
  
In the second instance where they run under separate host names they would be:  
  
site-1.example.com:/  
site-2.example.com:/  
  
So as long as you don't fiddle with which sub interpreter is used by specifying the WSGIApplicationGroup directive, mod\_wsgi should maintain separation between the multiple Django instances.  
  
What therefore can go wrong and why would requests get routed to the wrong Django instance?  
  


####  Ordering of WSGIScriptAlias directives.

  


The first scenario where one may see requests being handled by the wrong Django instance is where the multiple Django instances are running under the same host name and the ordering of the WSGIScriptAlias directives is wrong.

  


When using the WSGIScriptAlias multiple times under the same host name, it is important that the WSGIScriptAlias for sub URLs comes first.

  


In other words, the ordering is such that the most deeply nested URLs must come first. If you don't do that, then the shorter URL will match first and take precedence, thereby swallowing up all requests for both Django instances.

  


For example, if the directives above were instead written as:

  


WSGIScriptAlias / /some/path/project-1/wsgi.py

WSGIScriptAlias /suburl /some/path/project-2/wsgi.py

  


all requests would get routed into the first Django instance, even those for '/suburl', as the shorter URL of '/' specified with the first WSGIScriptAlias directive would always match, even before attempting to match against '/suburl'.  
  
The solution if this is the cause is obviously to reorder the WSGIScriptAlias directives as appropriate to ensure the longest URLs come first.  
  


####  Leaking of process environment variables.

  
In order to specify the module that the Django applications settings are contained in, it is necessary to set the process environment variable DJANGO\_SETTINGS\_MODULE.  
  
import os  
os.environ\['DJANGO\_SETTINGS\_MODULE'\] = 'mysite.settings'  
  
import django.core.handlers.wsgi  
application = django.core.handlers.wsgi.WSGIHandler\(\)  
  
  
When using Apache/mod\_wsgi, this is done in the WSGI script file and the environment variable would be set in os.environ when the WSGI script file is loaded.  
  
As much as process environment variables and global variables have their limitations and are arguably a bad idea for specifying configuration, this has still worked okay until recently.  
  
Problems started when Django 1.4 was released however. In Django 1.4 the content of the WSGI script file was changed from what was described previously for Django 1.3 and older versions to:  
  
import os  
os.environ.setdefault\('DJANGO\_SETTINGS\_MODULE', 'mysite.settings'\)  
  
from django.core.wsgi import get\_wsgi\_application  
application = get\_wsgi\_application\(\)  
  
  
Although the differences on first glance appear to be fine, they aren't and the WSGI script file in Django 1.4 will break Apache/mod\_wsgi for hosting multiple Django instances in the same process.  
  
The key problem is what the setdefault\(\) method does when setting the environment variable DJANGO\_SETTINGS\_MODULE compared to using assignment as previously. In the case of assignment the environment variable is always updated. For setdefault\(\), it is only updated if it is not already set.  
  
You might ask why would this be a problem. It is a problem because although os.environ looks like a normal dictionary, it isn't. Instead it is actually a custom class which only looks like a dictionary. When a key/value is set in os.environ, it is also setting it at the C level by calling putenv\(\).  
  
What now happens with our multiple Django instances running in the same process is that for the first one to be loaded, DJANGO\_SETTINGS\_MODULE will not be set and so setdefault\(\) will actually set it, including it being set globally to the process. When the second Django instance is loaded, at the point the sub interpreter is created, os.environ is populated from the C level environ, thereby picking up the value of DJANGO\_SETTINGS\_MODULE set when the first Django instance was loaded. In this case setdefault\(\) will not override the value as it already sees it as being set.  
  
Technically this leakage of environment variables between Python sub interpreters within the one process would always happen, but use of setdefault\(\) instead of assignment means DJANGO\_SETTINGS\_MODULE will not get overridden to be the correct value for the second Django instance to be loaded.  
  
The end result of the leakage can be one of two things. If the name of the Django settings module used for the first Django instance doesn't exist in the context of the second Django instance, then an import failure will occur and the Django instance will fail to be initialised. In this first case an actual failure will occur with nothing working and so it will be fairly obvious.  
  
A more problematic case though is where you are using one code base and multiple Django settings modules for each of the distinct Django instances being run. In this case the Django settings module may well be found, with the result being that when attempting to load up the second Django instance, a duplicate of the first instance would be loaded instead. Where URLs are now meant to be routed to the second instance, they would instead be handled as if being sent to the first instance as the configuration for the first is still being used.  
  
There are two solutions if this is the cause. The quickest is to replace the use of setdefault\(\) to set the environment variable in the WSGI script file with more usual assignment.  
  
os.environ\['DJANGO\_SETTINGS\_MODULE'\] = 'mysite.settings'  
  
An alternative which involves a bit more work, but can have other benefits, is to switch to using daemon mode of mod\_wsgi to run the Django instances and delegate each to a separate set of processes. By running the Django instances in separate processes there can be no possibility of environment variables leaking from one to the other.  
  
WSGIDaemonProcess project-2  
WSGIScriptAlias /suburl /some/path/project-2/wsgi.py process-group=project-2  


  


WSGIDaemonProcess project-1

WSGIScriptAlias / /some/path/project-1/wsgi.py process-group=project-1

  


####  Fallback to default VirtualHost definition.

  


Apache supports hosting of sites under multiple host names by way of name based virtual hosts. These are setup with the VirtualHost directive as previously shown.

  


<VirtualHost \*:80>

ServerName site-1.example.com

ServerAlias www.site-1.example.com

WSGIScriptAlias /some/path/project-1/wsgi.py

...

</VirtualHost>

  


<VirtualHost \*:80>

ServerName site-2.example.com

WSGIScriptAlias /some/path/project-2/wsgi.py

...

</VirtualHost>

  


The ServerName directive specified within the VirtualHost gives the primary host name by which the site is identified. If the same site can be accessed by other names, the ServerAlias directive can be used to list them explicitly, or by using a wildcard pattern.

  


What is not obvious however is if there are any host names by which the server IP is addressable and they are not covered by a ServerName or ServerAlias directive, rather than Apache giving an error, it will route the request to the first VirtualHost definition it found when it read its configuration.

  


In the above example, if the host name 'www.site-2.example.com' also existed and mapped to the server IP, because that host name wasn't covered by a ServerAlias directive for the second VirtualHost, the request would actually end up being handled by the Django instance running 'site-1.example.com'.

  


To address this problem you simply need to be diligent in ensuring that you have correctly mapped all host names you wish to have directed at a site. Using mod\_wsgi daemon mode will make absolutely no difference in this situation as it is Apache that is routing the request to the wrong VirtualHost before the request even gets passed off to mod\_wsgi.

  


As a failsafe to pick up such issues and ensure that requests don't unintentionally go to the wrong site, a good practice may be to ensure that the first VirtualHost that Apache encounters when reading its configuration is actually a dummy definition which doesn't equate to an actual site.

  


<VirtualHost \_default\_:\*>

Deny from all

</VirtualHost>

  


This could then be setup to fail all requests by way of forbidding access. A custom error document could also be used to customise the error response if necessary.

---

## Comments

### Chris Adams - October 10, 2012 at 1:54 AM

In 2012, with modern Python/Apache/mod\_wsgi/etc. why would someone choose not to use WSGIDaemonProcess by default? I strongly prefer it for reliability and security \(when using a separate user, of course\) and have thought that some of the deployment questions I've seen in the Django world could be avoided if the default recommendation was to use a daemon rather than in-process instance.  
  
P.S. Is http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives\#WSGIScriptAlias out of date? It doesn't mention the "WSGIScriptAlias … process-group=" syntax but does mention the presumably equivalent WSGIProcessGroup directive.

### Graham Dumpleton - October 11, 2012 at 3:00 PM

Yes, the mod\_wsgi documentation has lots of stuff missing. And yes daemon mode is the better option for most. I'll hopefully be saying more about this in future blog post and if not at PyCon if talk gets accepted.  
  
Wish I had more time. :-\)

### Nemesis Design - November 16, 2012 at 8:32 PM

Great work Graham, thank you for all your effort. It looks like you are the only one working on this project, is it really so?  
Fed.

### Graham Dumpleton - November 16, 2012 at 8:35 PM

Yep, only one mad enough to do it. Unfortunately don't get as much time to devote to it now as I once did.

### Nemesis Design - November 17, 2012 at 12:22 AM

how come nobody else in the python community wants to help? I think it is not your fault if you can't dedicate time to it, it's open source, those who use it should contribute.  
Have you ever tried mentoring a student for the Google Summer of Code?

### Graham Dumpleton - November 17, 2012 at 9:48 AM

More a case of when I was working on this I was moving so quick was hard for anyone to catch up with what was going on so as to be able to contribute. Now it is very stable and so the need to do anything else has dropped dramatically. Delving into the C APIs of both Apache and Python also isn't going to be of interest to most people, so was always going to be a very small pool of people one could draw from.

### Unknown - February 7, 2013 at 6:10 AM

If you specify "WSGIScriptAlias … process-group=" syntax or the WSGIProcessGroup doesn't that **only** work if you are [running Apache as root](http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess)?

### Graham Dumpleton - February 7, 2013 at 1:37 PM

WSGIScriptAlias and WSGIDaemonProcess group directives can only be added into the main Apache configuration file and not in a .htaccess file. Typically the main Apache configuration will require root access to modify the configuration files. That is the only way root comes into it. The feature implemented by those directives works fine if Apache was started as a user other than root.

### Tomas Tomecek - April 2, 2013 at 6:49 AM

This is really helpful. I had problem with environment variables leakage between processes and I realized, that I hadn't been using attribute "process-group" in WSGIAlias command.

### Graham Dumpleton - April 2, 2013 at 8:04 AM

@Tomas The leakage of environment variables is between Python sub interpreters within the one process, not between separate processes.

### Unknown - September 30, 2013 at 12:24 PM

Thanks Graham, Your article clearly explained my problem and enabled me to efficiently fix it and to understand apache a little better as a bonus.

### Wilder - November 11, 2013 at 5:15 AM

Thank you for posting this Graham.  
  
I seem to have been running into your answers on a lot of Django deployment questions I've been searching lately. I appreciate the sharing\!

### hdante - May 21, 2014 at 7:56 AM

I could not confirm that using assignment on environ solves the problem when using multiple threads with apache. Two threads may call os.environ\[...\] = settings1, then settings2 in sequence and the end result will be that both will run with settings2. Can you confirm this ?  
  
I'm currently experiencing lots of invalid ALLOWED\_HOSTS errors in my dual virtual host setup and the only explanation I have right now is that the settings are being overridden by the wsgi handler. I can't confirm that the assignment is the sole problem because things are slightly more complicated since I'm using django-configurations and the racy variable is actually DJANGO\_CONFIGURATION. I also noticed that I'm creating one WGSIApplication per request, which may be also worsening the situation:  
  
http://pastebin.com/cv1ySB1Q

### Graham Dumpleton - May 21, 2014 at 9:01 AM

@hdante If you are specific help in working out an issue, please use the mod\_wsgi mailing list as mentioned at:  
  
http://code.google.com/p/modwsgi/wiki/WhereToGetHelp?tm=6\#Asking\_Your\_Questions  
  
In short though, setting os.environ to different values on a per request basis is dangerous in any multithreaded application and not just mod\_wsgi and will cause lots of issues. You should never do that. You should find a different way of achieving whatever it is you want to do. Use the mailing list to provide better information on the actual problem you are trying to solve rather than trying to debug your solution.

### hdante - May 22, 2014 at 3:19 AM

@Graham The point is that the text suggests, as solution for multiple django settings "to replace the use of setdefault\(\) to set the environment variable in the WSGI script file with more usual assignment". This is not supposed to work if apache is using worker or event MPM, because starting 2 threads would cause a race when setting the environment variable on each thread.

### Graham Dumpleton - May 22, 2014 at 9:44 AM

@hdante The use of assignment is not a race condition for the documented example given in the blog post because it is done at global scope within the WSGI script file. The WSGI script file would be loaded once and the loading is under the context of an import lock and so only one request thread can trigger the loading. There is thus no possibility for the assignment in that specific WSGI script to be done concurrently from multiple threads.  
  
If however you do the assignment within the application\(\) function as you do on a per request basis, and which I already said you shouldn't do because that whole concept is fundamentally broken if the value can change per request, then you will have problems.  
  
As I already said, use the mod\_wsgi mailing list if you want to have a discussion about this. Using the comment section of a blog post is not the proper forum for a discussion.

### Unknown - October 20, 2015 at 3:07 PM

YOU ARE AWESOME\! os.envrion.setdefault was ruining me\! Thanks\!

