---
layout: post
title: "Introducing mod_wsgi-express."
author: "Graham Dumpleton"
date: "2015-04-02"
url: "http://blog.dscpl.com.au/2015/04/introducing-modwsgi-express.html"
post_id: "557711737287645994"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 12
published_timestamp: "2015-04-02T22:56:00+11:00"
blog_title: "Graham Dumpleton"
---

The Apache/mod\_wsgi project is now over 8 years old. Long gone are the days when it was viewed as being the new cool thing to use. These days people seeking a hosting mechanism for Python WSGI applications tend to gravitate to other solutions.

That mod\_wsgi is associated with the Apache project doesn't particularly help as Apache is seen as being old and stale. Truth is that the Apache httpd server has never stopped being improved on and is quite a lot better now than it was 8 years ago around the time when mod\_wsgi was started.

Even though the Apache httpd server itself has an even longer history going back almost 20 years, it is still the workhorse of the Internet and provides a rock solid platform for hosting web sites. It can still hold its own against competing solutions and for hosting Python WSGI applications using mod\_wsgi, is a proven reliable solution.

Now of those 8 years since mod\_wsgi was started, there was actually about 3 years where very little development was done on it. This was because personally I got burnt out over the whole WSGI on Python 3 saga. I finally got myself out of that hole about a year and a half ago, and have been working away since on quite a significant number of changes to mod\_wsgi that I haven't publicly said much about to date, let alone documented.

It is therefore long overdue to formally introduce one of the projects I have been working on. This project is [mod\_wsgi-express](https://pypi.python.org/pypi/mod_wsgi).

# Setting up of mod\_wsgi

One of the major bugbears of mod\_wsgi has been the perception that it is too hard to setup, especially if building from source code yourself. The task of getting it installed was only slightly easier if you used a pre-built binary package provided by your operating system, but using such a pre-built package could in itself result in a whole host of other problems when it wasn't compiled for the particular version of Python you wanted to use.

With the module at least installed, configuring Apache was no less of a problem, especially on Linux systems which come with a set default configuration which was tailored for static file hosting or PHP.

The end result is that most people walked away with a bad experience and a production system which was operating at a level no where near what it was actually capable of. For the case of using Apache/mod\_wsgi for development, the need for rapid iteration on changes in an application and the need to therefore be constantly restarting the web server, made the use of Apache/mod\_wsgi seem all too hard.

A large part of what I have been working on for the past year and a half has therefore been about improving that experience. Key was coming up with a system which provided an out of box configuration which was much better suited for Python web applications than the standard Linux defaults, yet was still customisable as necessary to further tune it to suit the specifics of your particular Python web application.

# Installation from PyPi using pip

The first major difference with mod\_wsgi-express over the traditional path of installing mod\_wsgi is that you can install it like any other Python package. In other words you can 'pip install' it directly from PyPi. You can even list it in a 'requirements.txt' file for 'pip.

```
    pip install mod_wsgi
```

If you have a complete Apache httpd server installation on your system then that is all that is required. The resulting mod\_wsgi module for Apache will have been compiled against and will be installed as part of your Python installation or virtual environment.

There is more though to mod\_wsgi-express than just the ability to easily compile the module for Apache. In addition to compiling the module, a separate script called 'mod\_wsgi-express' is installed. It is in this script that all the magic actually occurs.

Before I get onto what exactly the 'mod\_wsgi-express' script does, I do want to point out that if for some reason you don't have a complete Apache installation, so are perhaps missing the development header files that are required to build Apache modules, or the installed Apache is not the latest recommended version, then that is also covered.

For this case where you also need to be able to install a fresh version of the Apache httpd server itself, you can do:

```
    pip install mod_wsgi-httpd  
    pip install mod_wsgi 
```

In this case we are installing two packages. We are first installing 'mod\_wsgi-httpd' and then 'mod\_wsgi'.

What installation of the 'mod\_wsgi-httpd' package from PyPi will do is actually pull down the source code for the Apache httpd server as well as other libraries it requires and automatically compile it and install it also.

The Apache httpd server is quite a big project and so this will take a little while, but it allows you to ignore the system Apache installation, with the 'mod\_wsgi' package when subsequently being installed, detecting the version of Apache installed by 'mod\_wsgi-httpd' and so using it instead.

Important to note is that install Apache using 'mod\_wsgi-httpd' will not interfere with any existing Apache installation you may have. Like the 'mod\_wsgi' package, it will be installed as part of your Python installation or virtual environment.

# Hosting the WSGI application

So we have the Apache httpd server installed and the 'mod\_wsgi' module for Apache also compiled and installed. We haven't though yet configured Apache as yet.

This is where the 'mod\_wsgi-express' script comes into play.

If we have a WSGI application defined in a WSGI script file called 'hello.wsgi', all we now need to do is run:

```
    mod_wsgi-express start-server hello.wsgi
```

Doing this will yield something like:

```
    Server URL : http://localhost:8000/  
    Server Root : /tmp/mod_wsgi-localhost:8000:502  
    Server Conf : /tmp/mod_wsgi-localhost:8000:502/httpd.conf  
    Error Log File : /tmp/mod_wsgi-localhost:8000:502/error_log (warn)  
    Request Capacity : 5 (1 process * 5 threads)  
    Request Timeout : 60 (seconds)  
    Queue Backlog : 100 (connections)  
    Queue Timeout : 45 (seconds)  
    Server Capacity : 20 (event/worker), 20 (prefork)  
    Server Backlog : 500 (connections)  
    Locale Setting : en_AU.UTF-8
```

You can then access the WSGI application on the specified URL, that by default being port 8000 on the localhost.

As to the configuration of Apache, there actually wasn't any.

The key benefit of the 'mod\_wsgi-express' script is that it does all the configuration for you, setting up a configuration purpose built for running your specific WSGI application right there on the command line.

Running Apache/mod\_wsgi has therefore become as easy as running other pure Python WSGI servers such as gunicorn.

# Alternatives to a WSGI script file

Like when using mod\_wsgi in Apache in the more traditional approach, the 'mod\_wsgi-express' script defaults to requiring a WSGI script file. There are specific reasons, deriving from how Apache works, that a script file path is used rather than a Python module name. There are however also some benefits to how a WSGI script file is used which are lacking when a module name is used.

I'll try to explain those reasons and the benefits another time, but if you really want to use a module name instead, then that is also possible. So if instead of 'hello.wsgi' you actually had 'hello.py', making it a Python module, you could instead run:

```
    mod_wsgi-express start-server --application-type module hello
```

It is also even possible to provide a Paste 'ini' file as input by specifying the 'paste' application type.

```
    mod_wsgi-express start-server --application-type paste hello.ini
```

# Hosting static file assets

Python web applications are usually never just dynamically generated pages. Instead they are generally accompanied by a bunch of static files for CSS stylesheets, Javascript and images.

This is where 'mod\_wsgi-express' being based around mod\_wsgi running under Apache brings additional value. That is that the Apache httpd server was primarily intended for service static files. Even though we are hosting a dynamic Python web application, we can still make use of that capability. This can be done in a few ways.

First up, if all static file assets are to exist at a sub URL of the site, then they can be readily mapped into place using the '--url-alias' option. The arguments to this are the sub URL and then the path to the directory containing the static files.

```
    mod_wsgi-express start-server --url-alias /static ./htdocs/static hello.wsgi
```

For any site though, there are often special static files which need to exist at the root of the site. These are files such as 'robots.txt' and 'favicon.ico'.

These could be mapped individually using '--url-alias' as it does also allow the file system path to be that of a file:

```
    mod_wsgi-express start-server --url-alias /static ./htdocs/static \  
    --url-alias /favicon.ico ./htdocs/favicon.ico \  
    --url-alias /robots.txt ./htdocs/robots.txt hello.wsgi
```

A better alternative though is to simply contain all the files in the one directory, here called 'htdocs', with the location matching the URL they should appear at, and declare that as the document root.

```
    mod_wsgi-express start-server --document-root ./htdocs hello.wsgi
```

If you are a long time mod\_wsgi user you may be familiar with the problem that mounting a WSGI application at the root of the site actually hides any static files that exist in the document root for the server. In the case of mod\_wsgi-express though, specific Apache configuration is used such that any static files in the directory will actually overlay and take precedence over the WSGI application.

Thus if a URL matches a static file in the document directory the static file will be served up, otherwise the request will be passed on as normal to the WSGI application. Addition of new static file assets is therefore as simple as dropping them into the document directory with a path matching the URL it is to be available at.

By using Apache/mod\_wsgi we therefore get the best of both worlds. A performant way of serving up static file assets as well as the dynamic Python web application.

This is something you don't get from a pure Python WSGI server such as gunicorn. For gunicorn you would have to use a Python WSGI middleware to intercept requests and map them to any static files. This is in contrast to using Apache where handling of static file assets is all done in C code by Apache below the level that the Python interpreter would even be involved.

# Hosting just static files

Since mod\_wsgi-express actually provides such a convenient way of hosting static files, there is even a mode which allows you to say that you aren't actually wanting to run a Python web application at all, and only want to host static files.

Thus instead of the quick command often used by Python users to run up a server to temporarily host some static files, of:

```
    python -m SimpleHTTPServer
```

you can with mod\_wsgi-express do:

```
    mod_wsgi-express start-server --application-type static --document-root .
```

You are therefore running a production grade server for the task rather than the Python SimpleHTTPServer implementation.

This may not seem a big deal, but can be very convenient where you also need to be able to use a secure HTTP connection, or even use client certificates to control access to the files. These are things that you cannot do with SimpleHTTPServer, but can do with mod\_wsgi-express.

# And much much more

This only starts to scratch the surface of what one can do with mod\_wsgi-express and what sort of configurability it provides. In future posts I will talk about other features of mod\_wsgi-express, including using it to run a secure HTTP server, using it as a development server, as well as how to set it up for use in production environments, taking over from the normal Apache installation.

If you want to play with mod\_wsgi-express and get a head start on what some of its other bundled capabilities are, then you can run the command:

```
    mod_wsgi-express start-server --help
```

Also check out the PyPi page for 'mod\_wsgi' at:

  * <https://pypi.python.org/pypi/mod_wsgi>



If you have any questions about mod\_wsgi-express, use the [mod\_wsgi mailing list](http://code.google.com/p/modwsgi/wiki/WhereToGetHelp?tm=6#Asking_Your_Questions) to get help.

---

## Comments

### stuaxo - April 3, 2015 at 6:53 PM

Fantastic work, this should help many projects sort out Apache related issues early, instead of panicking at deployment time.

### Unknown - February 27, 2016 at 2:27 PM

This is just amazing. Thank you so much.

### bobpx2 - January 15, 2017 at 9:23 AM

This is a game-saver for the python victims of MacOS install mangling.   
For my dev. everything worthwhile is in a py2.7 or py3.5/6 venv. Now with apache also inside - at last hope for a SOLID server env.   
I am surprised that there are not more ++ comments from MacOS users.

### Graham Dumpleton - January 15, 2017 at 10:21 AM

@bob You don't need to install 'mod\_wsgi-httpd' on MacOS X. I work around the fact that Apple always breaks it in some way, even in Sierra where they do not provide the Apache build tools. So is sufficient just to do 'pip install mod\_wsgi'. You can now also after that run 'mod\_wsgi-express module-config' and it will give you the configuration you need to load mod\_wsgi into Apache from the Python environment, if wanting to still configure Apache manually and not use 'mod\_wsgi-express start-server'.

### bobpx2 - January 20, 2017 at 4:38 AM

Yes, thanks Graham... when starting and stopping from the /tmp folder  
wondered what the virtualenv 'server' was doing \!   
Will set up the way you suggest. Good results so far from a remote iPhone on ISP static address \(port-fwd\)  
bob

### SiD - April 4, 2017 at 4:16 AM

I am running the apache server built using mod\_wsgi-httpd however, the modules installed at /site-packages/mod\_wsgi\_packages/httpd/modules don't have mod\_ssl.so binary installed. How do I get my apache server to work?

### Graham Dumpleton - April 4, 2017 at 9:52 AM

The mod\_wsgi-httpd package is not intended to provide SSL. Working out what would need to be done to automatically build in SSL support in a portable way could get messy and couldn't guarantee done correctly/securely. You should use the operating system Apache version or build Apache yourself from source code if need SSL.

### Unknown - July 6, 2017 at 9:58 AM

Hi,  
  
I'm trying to follow your instructions on Windows \(using a command window\) but I get an error. The error seems pretty much to be the use of rm in some part of the script that obviously Windowws does not support.  
  
Have you tried this on Windows? I was able to install mod\_wsgi-express, but when I run it I don't have the start-server option.  
  
Any help will be greatly appreciated. I need to prototype a small python web app that will be potentially hosted in an Apache server.  
  
Cheers, Jose

### Graham Dumpleton - July 6, 2017 at 10:07 AM

@Charango The start-server option for running up the server is not available on Windows. The ability to do pip install mod\_wsgi on Windows is only available for at least getting the module built. Once installed, run 'mod\_wsgi-express module-config' and copy the output from that into your Apache configuration file in order to have Apache load the mod\_wsgi module. You then need to follow traditional configuration steps to manually setup Apache to host your WSGI application.

### Unknown - February 10, 2018 at 11:49 AM

Thanks for your work Graham.  
I'm currently using mod\_wsgi with django, running the site with http without further problems.  
Now I want to use https, I bought the certificate and used WHM to install it on main Apache and using a simple php index page, I can see that it's correctly installed.  
Here's where the things get fuzzy for me, I'm not an expert in apache config, the thing is that as I'm using mod\_wsgi-httpd, it created a separated config apache module \(in the default /tmp\), I searched for the httpd.conf on that mod\_wsgi-localhost:443:500/ directory, found it, but found 3 places where you could put certs.. I just filled the 3 with the same cert location.  
Result:  
When open page in the browser, ERR\_SSL\_PROTOCOL\_ERROR  
When use mod\_wsgi.../apachectl status, Error loading https://localhost:443/server-status: SSL error  
When less mod\_wsgi.../error\_log, just shows the last move which is execute the command  
  
I'm pretty lost here on where should I go next to fix this, could you please give some hint?  
  
BTW, I did not know if this was the best place to put my question, I did not want to put it in the github issues tab since I'm not sure if it is an issue or I'm missing some config.  
  
Appreciate help in advance.  
  
Cheers, Karosuo

### Graham Dumpleton - February 10, 2018 at 12:59 PM

Karosuo, please use the mod\_wsgi mailing list to ask questions. This blog is not a support forum.

### Unknown - March 16, 2018 at 5:29 AM

Just a quick note of thanks, thanks very much, Mr. Dumpleton\!  
I am just a bit of a hack and I have had much success standing on your shoulders :\)

