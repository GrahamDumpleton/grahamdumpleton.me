---
layout: post
title: "Why are you using embedded mode of mod_wsgi?"
author: "Graham Dumpleton"
date: "2012-10-13"
url: "http://blog.dscpl.com.au/2012/10/why-are-you-using-embedded-mode-of.html"
post_id: "6192669448750283967"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python']
comments: 15
published_timestamp: "2012-10-13T21:46:00+11:00"
blog_title: "Graham Dumpleton"
---

If you are using [Apache/mod\_wsgi](http://www.modwsgi.org/) and when you set it up all you cared about was getting something working, but didn't care much for understanding how things worked and how you should set it up, chances are you are running your WSGI application in embedded mode of mod\_wsgi. If you don't understand how to setup Apache, using embedded mode is nearly always a bad idea. Much more so if the Apache installation you are using is the default installation offered up by many Linux distributions, because in that case you are likely running the Apache prefork MPM, a choice which only compounds the problems you can experience.  
  
The preferred mode of running a WSGI application under mod\_wsgi if you have no idea of how to setup and tune Apache to match your specific web application, is daemon mode. Even if you reckon you do know how to setup Apache it is still safer to use daemon mode.  
  


####  If daemon mode is a better option, why isn't it the default?

  
This unfortunate situation whereby embedded mode is the default came about because in the very first incarnation of mod\_wsgi it was designed to mimic what mod\_python did. As a result, it only supported the concept of embedded mode. This is where the WSGI application runs within the actual Apache child processes, the same processes which are also handling serving of static file requests.  
  
Although daemon mode, which is more akin to how FASTCGI works with the WSGI application running in separate dedicated processes, was added later, embedded mode was already the default and it was hard to change at that point. Daemon mode also needed additional configuration whereas with embedded mode, things would at least run out of the box. Under Windows only embedded mode is supported, so having daemon mode be the default on UNIX systems but embedded mode the default on Windows was also seen as confusing.  
  


####  Why is running in embedded mode so bad?

  
The problems with embedded mode aren't so much due to the fact that the WSGI application is running in the actual Apache child processes, but that management of the processes is done by Apache and as such is subject to the general MPM settings of Apache. For the typical default Apache configuration the MPM settings are set up for serving of static files. The settings are not necessarily going to work very well for a dynamic web application with a large memory footprint that performs better when kept persistent in memory, as is the case for the majority of Python web applications.  
  
PHP gets away with running okay within the Apache child processes because of how PHP was designed to work. Specifically in PHP, any application code is effectively reloaded on each request and so it has been optimised in various ways to perform adequately under that scenario. Python being a general purpose programming language adapted to run web applications has a much larger startup cost for both the interpreter and for loading up a web application. Certain aspects of how the Python interpreter is implemented and loading of Python modules managed, also means it is not possible to use some of the techniques that PHP uses around preloading of the interpreter and code modules prior to forking of the Apache child processes. Python in Apache can simply therefore never match PHPs efficiency in this respect.  
  
The big problem therefore is simply the default configuration. If the MPM settings are properly setup and tuned for your specific Python web application running under embedded mode, then embedded mode will perform better than daemon mode. Use the default settings or don't configure it properly and you risk setting yourself up for a world of hurt.  
  


####  How should embedded mode be configured?

  


How best to configure the MPM settings of Apache when running a WSGI application in embedded mode is not the point of this post. I will deal with that another time. The point of this post is to help you identify when you are running embedded mode and show you how to setup daemon mode in its basic configuration instead. You can at least then shift away from using embedded mode if you didn't even realise you were using it and avoid causing problems for yourself.  
  


####  Determining if embedded mode is being used.

  
To determine if your WSGI application is running in embedded mode, replace its WSGI script with the test WSGI script as follows:  
  
``` 
import sys

def application(environ, start_response):
    status = '200 OK'

    name = repr(environ['mod_wsgi.process_group'])
    output = 'mod_wsgi.process_group = %s' % name

    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)

    return [output]
```  
  
  
If the configuration is such that the WSGI application is running in embedded mode, then you will see:  

```  
mod_wsgi.process_group = ''  
```  
  
That is, the process group definition will be an empty string.  
  
If instead you are already running in the preferred daemon mode, you would see a non empty string giving the name of the daemon process group.  
  


####  Identifying which Apache MPM you are using.

  


Even if your WSGI application is running in daemon mode, if the only thing you are using Apache for is to host the WSGI application and serve static files, then it is also recommended that you use worker MPM rather than prefork MPM as worker MPM will cut down on memory use by the Apache child processes.

  


To determine if you are using prefork MPM or worker MPM, you could try and work it out by looking at what operating system packages are installed, but the definitive way of doing it, is to run the Apache binary with the '-V' option.

  

```
$ /usr/sbin/httpd -V
Server version: Apache/2.2.14 (Unix)
Server built: Feb 10 2010 22:22:39
Server's Module Magic Number: 20051115:23
Server loaded: APR 1.3.8, APR-Util 1.3.9
Compiled using: APR 1.3.8, APR-Util 1.3.9
Architecture: 64-bit
Server MPM: Prefork
threaded: no
forked: yes (variable process count)
Server compiled with....
-D APACHE_MPM_DIR="server/mpm/prefork"
-D APR_HAS_SENDFILE
-D APR_HAS_MMAP
-D APR_HAVE_IPV6 (IPv4-mapped addresses enabled)
-D APR_USE_FLOCK_SERIALIZE
-D APR_USE_PTHREAD_SERIALIZE
-D SINGLE_LISTEN_UNSERIALIZED_ACCEPT
-D APR_HAS_OTHER_CHILD
-D AP_HAVE_RELIABLE_PIPED_LOGS
-D DYNAMIC_MODULE_LIMIT=128
-D HTTPD_ROOT="/usr"
-D SUEXEC_BIN="/usr/bin/suexec"
-D DEFAULT_PIDLOG="/private/var/run/httpd.pid"
-D DEFAULT_SCOREBOARD="logs/apache_runtime_status"
-D DEFAULT_LOCKFILE="/private/var/run/accept.lock"
-D DEFAULT_ERRORLOG="logs/error_log"
-D AP_TYPES_CONFIG_FILE="/private/etc/apache2/mime.types"
-D SERVER_CONFIG_FILE="/private/etc/apache2/httpd.conf"
```
  


The 'Server MPM' field will tell you which MPM your Apache has been compiled for.

  


If for some reason you can't work out which is the Apache binary, because your Linux distribution calls it something other than 'httpd', or they have modified it so it will not run unless some magic environment variables are set, then you can also guess what is running by using the following WSGI script.

  

```
import sys

def application(environ, start_response):
    status = '200 OK'
    output = 'wsgi.multithread = %s' % repr(environ['wsgi.multithread'])
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
```
  


If you get the output:

  

```
wsgi.multithread = True
```
  


you are likely running worker MPM and otherwise are running prefork MPM.

  


####  Running a WSGI application in daemon mode.

  


To force a WSGI application to run in daemon mode, the WSGIDaemonProcess and WSGIProcessGroup directives would need to be defined. For example, to setup a daemon process group containing two multithreaded processes one could use:

  

```
WSGIDaemonProcess example.com processes=2 threads=15
WSGIProcessGroup example.com
```
  


The WSGIDaemonProcess directive specifies the details of the daemon process group. The WSGIProcessGroup indicates that any WSGI application specified within the same context is to be delegated to run in that daemon process group.

  


A complete virtual host configuration for this type of setup would therefore be something like:

  

```
<VirtualHost *:80>
ServerName www.example.com
ServerAlias example.com
ServerAdmin webmaster@example.com
DocumentRoot /usr/local/www/documents
Alias /robots.txt /usr/local/www/documents/robots.txt
Alias /favicon.ico /usr/local/www/documents/favicon.ico
Alias /media/ /usr/local/www/documents/media/
<Directory /usr/local/www/documents>
Order allow,deny
Allow from all
</Directory>
WSGIDaemonProcess example.com processes=2 threads=15 display-name=%{GROUP}
WSGIProcessGroup example.com
WSGIScriptAlias / /usr/local/www/wsgi-scripts/myapp.wsgi
<Directory /usr/local/www/wsgi-scripts>
Order allow,deny
Allow from all
</Directory>
</VirtualHost>
```
  


After appropriate changes have been made Apache will need to be restarted. For this example, the URL 'http://www.example.com/' would then be used to access the the WSGI application.

  


Note that you obviously should substitute the paths and hostname with values appropriate for your system.

  


After making the changes, use the test WSGI script described before to verify the WSGI application is in fact running in daemon mode. It is a common mistake to see people use WSGIDaemonProcess but then not use WSGIProcessGroup or other configuration mechanisms to ensure that the WSGI application is in fact delegated to the daemon process group, so double check you got the configuration correct.

  


  


####  Immediate benefits of using daemon mode.

  


When you use daemon mode, the number of processes and threads is static. This is one of the immediate benefits of using daemon mode. Specifically, that process management is more predictable. One of the big problems with using embedded mode is that Apache can decide to create additional processes or kill off existing ones. For a web application with large startup costs this is not a good idea as you could suddenly see increased CPU usage due to more processes being started right at the time you don't need it such as when a throughput spike occurs. This can actually cause performance to degrade in the short term rather than improve.

  


If using embedded mode and you need to update the code for your Python web application, you have no choice but to restart the whole of Apache. If using daemon mode, you can avoid restarting the whole of Apache and can instead simply touch the WSGI script file to update its modification date. This will have the side effect of causing the daemon processes to restart on the next request. This is also convenient when using Apache/mod\_wsgi as a development environment to ensure parity with your production environment.

  


####  Additional reference documentation.

  


The information above gives a quick heads up on how to check whether you are running in embedded mode and how instead to get your WSGI application running in daemon mode. For additional information also read:

  * [Quick Configuration Guide](http://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide)
  * [Checking Your Installation](http://code.google.com/p/modwsgi/wiki/CheckingYourInstallation)
  * [Processes And Threading](http://code.google.com/p/modwsgi/wiki/ProcessesAndThreading)
  * [Reloading Source Code](http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode)



Related blog posts which would be worthwhile reading are:

  * [Save on memory with mod\_wsgi 3.0.](/posts/2009/11/save-on-memory-with-modwsgi-30/)



The most up to date version of mod\_wsgi 3.4. This was only released recently and the majority of distributions will not as yet have it as a packaged binary. You should at least aim to use mod\_wsgi 3.3. If you are on a Linux distribution which is still only supplying mod\_wsgi 2.8 or older, you really should think about upgrading to a more modern operating system distribution as 2.8 was released almost 3 years ago.

---

## Comments

### Marius Gedminas - October 15, 2012 at 8:45 PM

Speaking of WSGIProcessGroup, is the order important? In other words, if I have a WSGIScriptAlias directive above the WSGIDaemonProcess and WSGIProcessGroup directives inside the same , will they apply to that WSGIScriptAlias?

### Graham Dumpleton - October 15, 2012 at 9:10 PM

The only ordering issue is that if you have multiple WSGIProcessGroup directives in the same scope, the last one will be used. In other words, determined by scope and last one encountered for that scope is used.  
  
Further, if you have a nested scope, any defined in the nested scope overrides that in the parent scope. Thus if you have WSGIProcessGroup at VirtualHost scope and then also set WSGIProcessGroup inside of a Location or Directory context, and a specific request matches in some way that nested context, the WSGIProcessGroup from that nested context is used instead.  
  
This means for example you could have two WSGIDaemonProcess directives for different named groups. You might have default WSGIProcessGroup at VirtualHost context select one of them, but then for a specific URL subset, use Location and a nested WSGIProcessGroup to override that requests in that case go to the other daemon process group.  
  
Such a mechanism might be used if some subset of URLs used a C extension module for Python which wasn't thread safe. The default daemon process group could be default single process and multithreaded \(thus less memory\) and the second daemon process group could be a couple of single threaded processes.  
  
So have flexibility to segment parts of an application by URLs using Location directive across multiple daemon process groups, each configured differently to suite the requirements for those URLs.

### Unknown - August 9, 2013 at 11:47 AM

Just a minor point, I am using embedded mode \(I don't have the daemon directives, and I also double checked using the checking wsgi\_app given\). Nonetheless, when I change my python code, the changes are immediately visible - without restarting apache \(in the post it is asserted that you only get this behaviour in daemon mode\).

### Graham Dumpleton - August 19, 2013 at 11:20 AM

@Michael Are you sure the next request isn't just being picked up by a different Apache child worker process that hasn't loaded your code yet? Depending on your Apache MPM configuration, Apache can recycle processes that are idle and so easily give this impression. In embedded mode, mod\_wsgi by itself definitely doesn't reload the whole process automatically under any circumstances. The only way you would get it is by the separate code on mod\_wsgi site which checks for changes from a background thread and kills the processes when such changes are detected, something which I wouldn't recommend in embedded mode if other stuff is running in the same Apache, such as static file serving or PHP applications etc. Anyway, all details of how reloading works is documented in http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode

### Dan - February 26, 2014 at 2:27 PM

Hmm, I ran the daemon vs embedded test, and got a process group back, which I assume means I'm running this as a daemon \(with apache prefork, though\). However, I notice that only some changes seem to be immediately reflected upon reload of a webpage without an apache restart.   
  
For example, css changes \(in my static folder\) seem to get picked up, but changes to my templates don't \(I'm using bottle + jinja2, so I've got a views folder with templates inside it\).   
  
Is this behavior expected? I would think/hope there's a way to get these changes to be picked up. Am I just missing some other point?

### Graham Dumpleton - February 26, 2014 at 2:31 PM

Python will cache all code in the process and doesn't automatically reload code after it has changed. Whether templates are reloaded automatically can depend on the web framework being used or how you wrote your code. Read http://code.google.com/p/modwsgi/wiki/ReloadingSourceCode on details of how to trigger reloading.

### Unknown - June 17, 2014 at 5:17 PM

I'm having no luck with configured daemon mode on my prefork single threaded apache2 installation \(after several attempts\). Hence I'd like to optimize my embedded mode - you mention that this is an appropriate approach, and that you'd write about how to do it elsewhere. Is there some reference you can point me to about the best apache configuration for embedded mode? Thanks for your work\!

### Graham Dumpleton - June 17, 2014 at 5:22 PM

@Michael If you need help there is the mod\_wsgi mailing list. Comments on blog posts are not the appropriate place for debugging problems. I would very much suggest you use that list to resolve your issues with your daemon mode configuration before giving up on it.  
  
You can find details at:  
  
http://code.google.com/p/modwsgi/wiki/WhereToGetHelp?tm=6\#Asking\_Your\_Questions  
  
If you are still adamant that you want to use prefork MPM instead, then I can provide links to material for you to look through when you post on the list.

### Unknown - March 23, 2015 at 3:22 AM

I am using embedded mode of mod\_wsgi for my django application. Also i am using daemons to do some background processing for my application.  
Problem is my processes are running twice everytime.  
I have used all the directives.Please point me in the direction to solve this

### Graham Dumpleton - March 23, 2015 at 9:56 AM

@awais If you need help there is the mod\_wsgi mailing list. Comments on blog posts are not the appropriate place for debugging problems. I would very much suggest you use that list to resolve your issue.  
  
You can find details at:  
  
http://code.google.com/p/modwsgi/wiki/WhereToGetHelp?tm=6\#Asking\_Your\_Questions

### K-Z - July 3, 2015 at 5:22 PM

Awsum post...helped a lot....thank you ....:\)

### Unknown - January 10, 2017 at 7:40 AM

@Graham.  
  
Which file should I refer to while I am looking for this message   
  
"If the configuration is such that the WSGI application is running in embedded mode, then you will see:  
  
mod\_wsgi.process\_group = ''"  
  
I modified my apache2.conf and set the log level to Info but I don't see this line being printed to apache2/error.log or apache2/access.log

### Graham Dumpleton - January 10, 2017 at 7:47 AM

@kiran If you have managed to set up the WSGI script file so it is used, the message should appear in the browser when you make a request against the application. More details about this check in http://modwsgi.readthedocs.io/en/develop/user-guides/checking-your-installation.html\#embedded-or-daemon-mode  
  
BTW, if you have LogLevel at info, the error log should show messages about when WSGI script files are being loaded. These also show information about whether you are using daemon mode. The script load message would show process='' for embedded mode, bit a non empty string for daemon mode. If you aren't even see a script loading message for the test script, then Apache isn't loaded correctly  
  
Also, those scripts as shown probably will not work on Python 3. They would need to be changed.

### Unknown - February 16, 2017 at 7:47 AM

Using apache mpm\_event do you still recommend using mod\_wsgi in daemon mode?

### Graham Dumpleton - February 16, 2017 at 1:45 PM

@Aron I will always recommend daemon mode. There are a huge number of more options available to configure mod\_wsgi daemon processes to ensure a more robust application which can recover from problems. They aren't necessarily on by default though, so you still have to configure them if setting up Apache/mod\_wsgi yourself. If you use mod\_wsgi-express it provides much better defaults with all sorts of timeouts enabled so it recovers when things get stuck etc. Trying install mod\_wsgi-express by running 'pip install mod\_wsgi' and then run 'mod\_wsgi-express start-server --help' and you will see all sorts of options which come by virtue of WSGIDaemonProcess directive, and what I think are sane defaults.

