---
title: "Using Python virtual environments with mod_wsgi."
author: "Graham Dumpleton"
date: "Tuesday, September 2, 2014"
url: "http://blog.dscpl.com.au/2014/09/using-python-virtual-environments-with.html"
post_id: "7380232566861350496"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 7
published_timestamp: "2014-09-02T00:49:00+10:00"
blog_title: "Graham Dumpleton"
---

You should be using Python virtual environments and if you don't know why you should, maybe you should find out.

That said, the use of Python virtual environments was the next topic that came up in my hallway track discussions at DjangoCon US 2014. The pain point here is in part actually of my own creation. This is because although there are better ways of using Python virtual environments with mod\_wsgi available today than there used to be, I have never actually gone back and properly fixed up the [documentation](https://code.google.com/p/modwsgi/wiki/VirtualEnvironments) to reflect the changes.

When using mod\_wsgi embedded mode, one would use the 'WSGIPythonHome' directive, setting it to be the top level directory of the Python virtual environment you wish to use. If you don't know what that is supposed to be, then you can interrogate it using the command line Python interpreter:
    
    
```
>>> import sys  
>>> sys.prefix  
'/Users/graham/Projects/mod_wsgi/venv'
```

Most important is that this should refer to a directory. It is an all too common mistake that I see that people set the 'WSGIPythonHome' directive to be the path to the 'python' executable from the virtual environment. That is plain wrong, so please do not do it, doing so will see the setting be ignored completely and the default algorithm for finding what Python installation to use will be used instead.

If using daemon mode of mod\_wsgi and you are hosting only the one Python WSGI application, then you can again just rely on the 'WSGIPythonHome' directive, pointing it at the Python virtual environment you want to use. If you are hosting more than one WSGI application however, and you want each to use a different Python virtual environment, then you need to do a bit more work.

The mod\_wsgi documentation on this steers you towards a convoluted bit of code to include in your WSGI application to do this, explain in part why this is the safest option.
    
    
```
ALLDIRS = ['usr/local/pythonenv/PYLONS-1/lib/python2.5/site-packages']
```
    
    
```
import sys   
import site
```
    
    
```
# Remember original sys.path.  
prev_sys_path = list(sys.path)
```
    
    
```
# Add each new site-packages directory.  
for directory in ALLDIRS:  
 site.addsitedir(directory)
```
    
    
```
# Reorder sys.path so new directories at the front.  
new_sys_path = []   
for item in list(sys.path):   
 if item not in prev_sys_path:   
 new_sys_path.append(item)   
 sys.path.remove(item)   
sys.path[:0] = new_sys_path
```

Part of the reasoning behind giving that as the recipe was a distrust of the 'activate\_this.py' script that is included in a Python virtual environment and advertised as the solution to use for embedded Python environments such as mod\_wsgi.

The reason I was cool on 'activate\_this.py' was that it stomped on the value of 'sys.prefix'. In the context of mod\_wsgi, because the Python installation that mod\_wsgi was actually compiled against or using may be at a different location, I was worried about whether modifying 'sys.prefix' would cause something to break.

I therefore gave only guarded approval to using 'activate\_this.py'.

In the many years mod\_wsgi has been available though, I have to admit that no issues ever came up around 'sys.prefix' being overridden.

So, if you do not have access to make changes in the Apache configuration files for some reason, then the easiest way to activate a Python virtual environment in your WSGI script file is:
    
    
```
activate_this = '/usr/local/pythonenv/PYLONS-1/bin/activate_this.py'  
execfile(activate_this, dict(__file__=activate_this))
```

This is still a pain to have to include because you are adding to the WSGI script file knowledge of the execution environment it is being run in, which is notionally a bad idea.

The alternative to modifying the WSGI script file was to add just the 'site-packages' directory from the Python virtual environment in the Apache configuration.

For embedded mode of mod\_wsgi you would do this by using the 'WSGIPythonPath' directive:
    
    
```
WSGIPythonPath /usr/local/pythonenv/PYLONS-1/lib/python2.5/site-packages
```

If using daemon mode of mod\_wsgi you would use the 'python-path' option to the WSGIDaemonProcess directive.
    
    
```
WSGIDaemonProcess pylons python-path=/usr/local/pythonenv/PYLONS-1/lib/python2.5/site-packages
```

What was ugly about this was that you had to refer to the 'site-packages' directory where it existed down in the Python virtual environment. That directory name also included the Python version, so if you ever changed what Python version you were using, you had to remember to go change the configuration.

The good news is that since mod\_wsgi version 3.4 or later there is a better way.

Rather than fiddling with what goes into 'sys.path' using the 'WSGIPythonPath' directive or the 'python-path' option to 'WSGIDaemonProcess', you can use the 'python-home' option on the 'WSGIDaemonProcess' directive itself.
    
    
```
WSGIDaemonProcess pylons python-home=/usr/local/pythonenv/PYLONS-1
```

As when using the 'WSGIPythonHome' directive, this should be the top level directory of the Python virtual environment you wish to use. In this case the value will only be used for this specific mod\_wsgi daemon process group.

If you are therefore using a new enough mod\_wsgi version, and using mod\_wsgi daemon mode, then switch to the 'python-home' option of 'WSGIDaemonProcess'.

---

## Comments

### Kernel Kiddy - October 5, 2015 at 6:41 PM

Graham, thank you for the post\!  
This is the only place where I could finally find option python-home of WSGIDaemonProcess to set path to Python executable for my virtual host.  
  
It is very strange that this option is not mentioned in documentation: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives\#WSGIDaemonProcess

### Graham Dumpleton - October 5, 2015 at 6:45 PM

Documentation not up to date, simple as that. Has been present since mod\_wsgi 3.4  
  
http://modwsgi.readthedocs.org/en/develop/release-notes/version-3.4.html

### okyere - March 11, 2016 at 9:40 AM

Graham,  
Great post. In my current set up, I have multiple python applications hosted on multiple virtual hosts. I have created only one virtual environment that all the applications use.  
  
Outside of all the virtual hosts, I have:  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
WSGISocketPrefix /var/run/wsgi  
WSGIPythonHome /WebHA/catworld/featureanalytics-443S/webpython \#folder of my virtualenv  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
  
Then in each virtual host, I have among others:  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
DocumentRoot "/WebHA/catworld/featureanalytics-443S/workforce\_tool/"  
ServerName wpat.cat.com  
ServerAlias wpat.cat.com  
  
  
WSGIDaemonProcess wpat.cat.com user=http group=http processes=4 threads=4  
WSGIProcessGroup wpat.cat.com  
WSGIPassAuthorization On  
  
WSGIScriptAlias / /WebHA/catworld/featureanalytics-443S/workforce\_tool/workforce\_tool.wsgi  
Alias /static /WebHA/catworld/featureanalytics-443S/workforce\_tool/app/static  
  
  
Order allow,deny  
Allow from all  
  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
  
  
The corresponding wsgi file for the above virtual host is:  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
\#workforce\_tool.wsgi  
  
\#\!/WebHA/catworld/featureanalytics-443S/webpython/bin/python  
  
activate\_this = '/WebHA/catworld/featureanalytics-443S/webpython/bin/activate\_this.py'  
exec\(open\(activate\_this\).read\(\)\)  
  
import sys  
import logging  
  
logging.basicConfig\(stream=sys.stderr\)  
sys.path.insert\(0,"/WebHA/catworld/featureanalytics-443S/workforce\_tool/"\)  
  
from app import theapp as application  
application.secret\_key = 'mykey'  
\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#  
  
**Python 3.4.3**  
**mod\_wsgi 4.4.22**  
Daemon mode  
  
  
I followed a tutorial online to set things up this way.  
Due to other reasons, I have to switch to use anaconda/conda distribution of python. So I'll be creating conda environments for each app.  
  
**1\. How will the code in the wsgi file change especially about activating the python environment?**  
  
**2\. How will my set up change to use a different conda environment for each app/virtual host? I want to move away from using one environment for every python app.**

### Graham Dumpleton - March 11, 2016 at 9:42 AM

@okyere Use the mod\_wsgi mailing list. Blog posts are not a support forum. See http://modwsgi.readthedocs.org/en/develop/finding-help.html

### MAC - November 11, 2016 at 10:06 AM

What a great post \!  
Helped me solve a similar situation getting conda environment working on a standard apache + mod\_wsgi server.

### erdem - July 13, 2017 at 8:21 PM

from flask import Flask  
ImportError: No module named flask  
mod\_wsgi \(pid=5434\): Target WSGI script '/var/www/FlaskApp/flaskapp.wsgi' cannot be loaded as Python module.  
  
I'm using anaconda.When I open the browser on my ıp adress to show my flask app I take Internal Server Error   
The server encountered an internal error or misconfiguration and was unable to complete your request.  
What should I do ?

### Graham Dumpleton - July 13, 2017 at 8:47 PM

@erdem Please use the mod\_wsgi mailing list if you are having problems. A blog post is not the place to discuss it.  
  
http://modwsgi.readthedocs.io/en/develop/finding-help.html  
  
Also ensure you have read the following as information in this post is out of date:  
  
http://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html  
  
Also ensure that your mod\_wsgi was actually compiled for the Anaconda Python version you want to use. You cannot force mod\_wsgi compiled for one Python version/installation to use a different Python version/installation or virtual environment created with a different Python version/installation.

