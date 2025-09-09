---
layout: post
title: "Using mod_wsgi-express with Django."
author: "Graham Dumpleton"
date: "2015-04-05"
url: "http://blog.dscpl.com.au/2015/04/using-modwsgi-express-with-django.html"
post_id: "4032251770976665978"
blog_id: "2363643920942057324"
tags: ['apache', 'django', 'mod_wsgi', 'python', 'wsgi']
comments: 25
published_timestamp: "2015-04-05T23:22:00+10:00"
blog_title: "Graham Dumpleton"
---

In my [last post](/posts/2015/04/introducing-modwsgi-express/) I finally officially introduced [mod\_wsgi-express](https://pypi.python.org/pypi/mod_wsgi), an extension to mod\_wsgi that I have been working on over the past year and a half. The purpose of mod\_wsgi-express is to radically simplify the steps required to deploy a Python WSGI application using Apache and mod\_wsgi. In that post I introduced some of the basic functionality of mod\_wsgi-express. As Django is the most popular Python web framework, in this post I want to explain what is involved in using mod\_wsgi-express with Django.

# The structure of a Django project

When starting a new Django project the ‘startproject’ command is supplied to the ‘django-admin’ script to create the initial project structure. The directories and files created in the directory where the command is run is:

```
    mysite/manage.py  
    mysite/mysite/__init__.py  
    mysite/mysite/settings.py  
    mysite/mysite/urls.py  
    mysite/mysite/wsgi.py
```

The immediate subdirectory created below where the ‘startproject’ command was run, and which contains the ‘manage.py’ script, is referred to as the base directory. The name of the base directory is whatever you called the name of your project.

The ‘manage.py’ file contained in the base directory is a site specific variant of the ‘django-admin’ script, which provides a means of executing various builtin Django admin commands against your site, as well as any admin commands which may later be added to the site by associating add-on applications with it.

In addition to the ‘manage.py’ script a further subdirectory, with the same name as the base directory, will have been created. This directory will contain the actual code for your site. Worth noting is that this directory actually contains an ‘\_\_init\_\_.py’ file. This is important as it actually marks the directory as a Python package, rather than just a collection of Python modules.

This directory also contains two other files which are important and come into play when aiming to deploy your site. These are the ‘settings.py’ file, which is used to customise the capabilities of your site and how it may be made available, plus the ‘wsgi.py’ file, which contains the WSGI application entry point which any WSGI server needs to know about. It is the function or other callable object specified as the WSGI application entry point to which the details of each request received by the WSGI server will be passed to have your Django application serve the request.

As far as now using mod\_wsgi-express with such a Django project, there are two main things that mod\_wsgi-express needs to be told. These are the location of the base directory and the full name of the module containing the WSGI application entry point.

The location of the base directory is important because it is the parent directory for the Python package containing the code for your site. This directory will need to be added to the Python module search path so the Python package containing your site code can be found. In particular we need it to be able to find the ‘wsgi.py’ file when referring to it via its full module name.

So if we were still located in the top level directory where the ‘startproject’ command was run, one above the base directory, we would run ‘mod\_wsgi-express’ as:

```
    mod_wsgi-express start-server --working-directory mysite --application-type module mysite.wsgi
```

If we had instead run mod\_wsgi-express inside of the base directory, we could have used just:

```
    mod_wsgi-express start-server --application-type module mysite.wsgi
```

The later still works because the working directory will be set to be the current directory if none is explicitly supplied.

For a simple hello world program that returns plain text, this is all that is required. If however you also have static media files for CSS stylesheets, Javascript and images, then this is not sufficient. This is readily apparent if you were to visit the ‘/admin’ URL of your site as no styling will be applied to what is displayed in the browser.

To have such styling applied for the ‘/admin’ URL, we also need to tell mod\_wsgi-express about the location of any static media files and at what sub URL they need to be made available so that they can be found by any HTTP client.

# Hosting of static media files

When using Django’s own builtin development server, it will automatically make available any static media files at the required sub URL. When you use a separate WSGI server however, that automatic mapping and hosting of the static media files will not occur.

It is possible to configure Django to host these static media files itself even in a production setting, but this is sub optimal and not recommended. Instead such static media files should be hosted by a proper web server.

In the case of mod\_wsgi-express, because it is actually using Apache underneath, then we already have a true web server available which can be used to host the static media files in a production setting.

Before we can make use of that capability though, we first need to setup the Django project to allow us to easily collect together all the static media files together in the one location. This is necessary as normally such static media files are spread out across different locations, including as part of Django itself, or any installed add-on applications.

The first thing we therefore need to do is modify the ‘settings.py’ file and add the setting:

```
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```

This is best placed at the end of the ‘settings.py’ file immediately after the existing setting for ‘STATIC\_URL’.

What the ‘STATIC\_ROOT’ setting does is say that all static media files are to be placed into a directory called ‘static’ located within the base directory.

To actually get the files copied into that location we now need to run:

```
    python manage.py collectstatic
```

Note that although we run this initially, this command must be run every time any update is made to static media files located within any add-on applications, or were Django itself updated to a newer version

After having run this command, this will now leave us with:

```
    mysite/manage.py  
    mysite/mysite/__init__.py  
    mysite/mysite/settings.py  
    mysite/mysite/urls.py  
    mysite/mysite/wsgi.py  
    mysite/static/admin/css/...  
    mysite/static/admin/img/...  
    mysite/static/admin/js/...
```

So the ‘static’ subdirectory has been created, with a further subdirectory containing the static media files for the admin component of Django implementing the ‘/admin’ sub URL.

Now running mod\_wsgi-express from within the base directory we would use:

```
    mod_wsgi-express start-server --url-alias /static static --application-type module mysite.wsgi
```

The new option in this command is ‘—url-alias’. This option takes two arguments. The first is the sub URL where the static media files are to be made available. This should match the value which the ‘STATIC\_URL’ setting had been set to. The second argument is the location of the directory where the static media files were copied. As we are running this command in the base directory and the location of the static media files is an immediate subdirectory, we can specify this as just the name of the subdirectory.

We should now have a working Django site using Apache/mod\_wsgi. We have though had to duplicate certain information on the command line which is actually available in the Django settings file. The next step therefore is to eliminate that requirement by integrating mod\_wsgi-express into the Django site itself as a Django admin management command. I will cover how that is done in the next blog post about this topic.

---

## Comments

### Unknown - April 7, 2015 at 10:47 PM

I am currently in the process of deploying my first django project into our prod env. I'm amazed that this seemingly easy method of deployment with python/django is only 2\(\!\) days old. What has the python community been up to until now? Is this a reliable way to go forward with our deployment or should I look elsewhere for a more tried and tested source?

### Graham Dumpleton - April 8, 2015 at 8:53 AM

The pip installable mod\_wsgi with mod\_wsgi-express has been available for a year and has been working/usable during that whole time. Also remember it is based on mod\_wsgi which is 8 years old.  
  
Been too busy working on new stuff to bother announcing mod\_wsgi-express on my blog. I have talked about it at conferences though.  
  
As far as using it in production, what is lacking is the documentation of the best way of doing that. Will be blogging about that in coming weeks.

### Mayank - June 4, 2016 at 8:45 PM

This was an extremely useful post. With some difficulty with static files I was able to get this going.  
  
I was wondering what do we do about media files and protected files with mod\_wsgi-express. Do we have separate option or can we use --url-alias itself.  
  
Kindly advise.  
  
Thanks in advance,  
Mayank

### Graham Dumpleton - June 7, 2016 at 10:15 AM

@Dodo Best to post your question on the mod\_wsgi mailing list. It depends on what you mean by protected.

### Mayank - June 7, 2016 at 9:07 PM

Sorry. Missed updating here. I had to use an extra --url-alias /media /path/to/media for the user uploaded media files. Protected was for those files that are visible only to specific users. I realized that those don't need a mention on the command line. Now the setup works beautifully.  
  
I am struggling to make the debugger work as per a comment on your other post with mod\_wsgi-express. Will post there if still stuck.  
  
Thanks,  
Mayank

### Unknown - June 9, 2016 at 1:12 PM

Graham hello am with my first project with django and I tell you that I have 2 days trying to run it on apache .. I started doing it by installing and configuring apache mod\_wgsi in the same apache to run my django project which unfortunately fails to do this morning in my I see this other method work mod\_wgsi express just get home started in an attempt to ride I think ye come a long way since achieving install everything according to parameters set in my virtual environment where I stayed in my project .... but right now I an error that I can not solve ... run my server with the following command \(mod\_wsgi start-server-express --application-type module yarv1.wsgi\) the server starts without any warning or apparent problem ... but when I try to access \(http://127.0.0.1:8000/home/\) skips a 500 error page not found and when I see in the log out the following \(Exception occurred processing WSGI script '/ tmp / mod\_wsgi-localhost: 8000: 1000 / htdocs /home'. \) You think I have something misconfigured could help in this case I remain attentive greetings  
  
pd: sorry if my English is bad'm using a translator

### Graham Dumpleton - June 9, 2016 at 1:15 PM

If you need help, please use the mod\_wsgi mailing list, or if you can't use that, the issue tracker on github for mod\_wsgi.  
  
http://modwsgi.readthedocs.io/en/develop/finding-help.html  
  
Comments on a blog post is not a suitable place to discuss problems in any depth.

### SiD - October 19, 2016 at 3:15 PM

HI when setting up django using python manage.py runmodwsgi --setup-only option, the apachectl script that gets generated does not contain the path to apache shared libraries. SHLIBPATH is empty string. As a result apache complains about not finding .so files.  
  
I had to manually point the SHLIBPATH to "~/project/venv/lib/python3.5/site-packages/mod\_wsgi\_packages/httpd/lib"  
  
Please fix this.

### Graham Dumpleton - October 19, 2016 at 3:25 PM

@SID The issue tracker for mod\_wsgi can be found at:  
  
\* https://github.com/GrahamDumpleton/mod\_wsgi/issues  
  
Please report the issue there.

### KR - February 24, 2017 at 10:33 PM

why i cannot use mod\_wsgi-express start-server  
it said i can only use commands module-config and module-location  
start-server is one invalid command

### Graham Dumpleton - February 24, 2017 at 10:39 PM

@KR Because you are using Windows. On Windows you must still configure Apache yourself. You cannot use mod\_wsgi-express start-server.  
  
On Windows you still use pip install mod\_wsgi because it is the easiest way to build mod\_wsgi on Windows now. You then need to run 'mod\_wsgi-express module-config'. This will output what you need to manually put in the Apache configuration to load mod\_wsgi. Then you need to also manually configure Apache to host your specific WSGI application.  
  
It is not know whether 'mod\_wsgi-express start-server' can ever be made to work on Windows.  
  
For more information on manual integration, see section 'Connecting into Apache installation' of:  
  
https://pypi.python.org/pypi/mod\_wsgi

### Unknown - March 24, 2017 at 6:43 PM

Hi Graham  
I use mod\_wsgi-express with django and run server like this manage.py runmodwsgi ...  
I have a question about logging.  
When python traceback appears in error\_log, mod\_wsgi add timestamp and other information to every line and it's a problem because i sent logs to logstash server and it's splited to many events. Can i somehow use python logger instead of wsgi or use both just devide logs to different files?  
Thanks in advance

### Unknown - March 24, 2017 at 6:45 PM

This comment has been removed by a blog administrator.

### Graham Dumpleton - March 24, 2017 at 7:25 PM

For questions you should use the mod\_wsgi mailing list.   
  
http://modwsgi.readthedocs.io/en/develop/finding-help.html  
  
Anyway, best you might do is use the --error-log-format option to change the log format to drop the timestamps etc. I don't think this will help you though, because the real issue is probably going to be that each traceback stack frame is output on a separate line. If that is true, using the logging module isn't going to help you either.

### Artemedu - August 12, 2017 at 8:08 AM

Hello Graham\!  
Please explain at a high level how the mod\_wsgi\_express works. Does it create a new independent virtual Apache server running my application\(s\)? And if so, is it secure to stop principal Apache server, i.e. will my python/Django-based app still be working in mod\_wsgi/apache if I close the principal Apache server? Thanks in advance.

### Graham Dumpleton - August 12, 2017 at 8:50 AM

@Artemedu For some context, watch https://www.youtube.com/watch?v=H6Q3l11fjU0  
  
You must still have Apache runtime and dev packages installed for system, but does not need to be enabled. Uses separate configuration files.

### Artemedu - August 13, 2017 at 4:19 AM

Graham, thank you\! This is exactly what I wanted to know. BTW, I have already installed mod\_wsgi-express server and my app works good with it. But my IT manager asked me to stop \(not uninstall, just stop\) Apache server for security reason, so that it doesn't use another port. And I was wondering if my app will still be working after that. Now I know that it should be working. Thank you\!

### Artemedu - September 12, 2017 at 10:35 PM

Hello Graham\! Is it possible to run modwsgi in another folder rather than defined one?  
Currently, I run Apache instance with modwsgi with the following command:  
python manage.py runmodwsgi  
And my apache/modwsgi instance get run in tmp/mod\_wsgi-localhost:8000:1000/  
Everything works fine one week but then it seems that operating system cleans/deletes some of files including htdocs folder since I am not an owner of this tmp/ directory.  
  
So, if there is a way to run modwsgi in another folder with a command like:  
python manage.py runmodwsgi --server-root=/full path to desired folder/  
Thank you.

### Graham Dumpleton - September 12, 2017 at 10:36 PM

Using --server-root with runmodwsgi is fine, and is shown as an example in https://pypi.python.org/pypi/mod\_wsgi

### Artemedu - September 13, 2017 at 12:18 AM

Graham, Thank you\! I saw examples shown at this link but since they refer to section named as 'running mod\_wsgi-express as root' and I don't have root privileges, I wasn't sure if this command \(--server-root\) can be used in my case.

### Graham Dumpleton - September 13, 2017 at 11:07 AM

@Artemedu As long as you have write permission to create the directory you pass to --server-root, or it already exists and you have write access, you are good.

### Roxolan - October 18, 2017 at 11:03 PM

Hello, Graham\!  
I am trying to deploy django with mod\_wsgi \(I watched your PyCone speech on youtube\).   
I've installed packages and executed:  
.env/bin/python manage.py runmodwsgi --server-root /etc/wsgi-port-80 --user www-data --group www-data --host www.example-my.com --setup-only  
Than   
/etc/wsgi-port-80/apachectl start  
and get an error  
\[Wed Oct 18 14:56:00.989197 2017\] \[core:crit\] \[pid 10141:tid 140533963185280\] \(EAI 2\)Name or service not known: AH00077: alloc\_listener: failed to set up sockaddr for www.example-my.com  
AH00526: Syntax error on line 21 of /etc/wsgi-port-80/httpd.conf:  
Listen setup failed  
As I understood, these commands create a valid httpd.conf.  
I can't unserstand what I do wrong.  
  
Thanks in advance

### Graham Dumpleton - October 18, 2017 at 11:08 PM

@Roxolan  
  
The likely reason though is that you don't need '--host www.example-my.com' unless you are going to enable secure access. Whatever you do use for that must be a valid hostname which can be mapped to an IP. Likely what you are using isn't.  
  
If you have further questions, please using the mod\_wsgi mailing list as described in:  
  
\* http://modwsgi.readthedocs.io/en/develop/finding-help.html  
  
Or if for some reason you can't use the mailing list, ask your question on StackOverflow.

### Graham Dumpleton - October 18, 2017 at 11:09 PM

@Roxolan Also, if you really did want to use port 80, you are missing the '--port 80' option.

### Roxolan - October 18, 2017 at 11:41 PM

@GrahamDumpleton  
Thank you for your answer.

