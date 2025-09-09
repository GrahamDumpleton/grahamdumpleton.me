---
title: "Hosting PHP web applications in conjunction with mod_wsgi."
author: "Graham Dumpleton"
date: "Wednesday, September 3, 2014"
url: "http://blog.dscpl.com.au/2014/09/hosting-php-web-applications-in.html"
post_id: "6705520914492383897"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'php', 'python', 'wsgi']
comments: 6
published_timestamp: "2014-09-03T07:00:00+10:00"
blog_title: "Graham Dumpleton"
---

Yes, yes, I know. You can stop shaking your head now. It is a sad fact of life though that the need to mix both PHP web application code with Python web application code on the same Apache instance is something that some people need to do. One instance is where those PHP developers have seen the light and want to migrate their existing legacy PHP web application to Python, but are not able to do it all in one go, instead needing to do it piece meal, with the Python web application code progressively taking over from the PHP web application.

Ask around on the Internet and once you get past the 'why on earth to you want to do that' type of reactions, you will often be told it is either not possible or too hard and that you should just ditch the PHP web application entirely and just use Python. This isn't particularly helpful and is also very misleading as it is actually quite simple to allow both a PHP web application and Python web application to run concurrently on the same Apache instance.

In going this path though, there is one very important detail that you must first appreciate. That is that the typical Apache server MPM configuration for a PHP web application under Apache is generally not favourable to a Python web application. Because of this, never run your Python web application in embedded mode if you are also running a PHP web application on the same Apache server. If you do, then the performance of your overall Apache instance will be affected, having an impact on both the PHP and Python web applications.

What you want to do to mitigate such problems is run your Python web application in daemon mode of mod\_wsgi. This means that the Python web application will run in its own process and the Apache child worker process will merely act as a proxy for requests being sent to the Python web application. This ensures that the Python web application processes are not subject to the dynamic process management features of Apache for child worker processes, which is where a lot of the problems arise when running with embedded mode.

Because it is so important that embedded mode not be used, to ensure you get this right and don't actually still run your Python web application in embedded mode, you should disable embedded mode entirely.

The configuration for mod\_wsgi in the Apache configuration where running a single Python web application should therefore include something like:
    
    
    # Define a mod_wsgi daemon process group.
    
    
    WSGIDaemonProcess my-python-web-application display-name=%{GROUP}
    
    
    # Force the Python web application to run in the mod_wsgi daemon process group.
    
    
    WSGIProcessGroup my-python-web-application  
    WSGIApplicationGroup %{GLOBAL}
    
    
    # Disable embedded mode of mod_wsgi.
    
    
    WSGIRestrictEmbedded On 

Obviously if running more than one Python web application then you may need to use a more complicated configuration. Either way, ensure you aren't using embedded mode and that any Python web applications are running in daemon mode instead. All the following discussion will assume that you have got this in place.

Having dealt with that, we can now move onto trying to setup up the Apache configuration to serve both the PHP web application and the Python web application.

For this we now need to delve into the typical ways that each is hosted by Apache.

In the case of PHP, the typical approach involves having Apache handle the primary URL routing by matching a URL to actual files in the file system. So if the default Apache web server document directory contains the files:
    
    
    favicon.ico  
    index.php  
    page-1.php  
    page-2.php  
    robots.txt 

then if a request arrives which uses a URL of '/robots.txt', then Apache will return the contents of that file. If however a URL of '/page-1.php' arrives, then Apache will actually load the code in the file called 'page-1.php' and execute it as PHP code. That PHP code will then be responsible for generating the actual response content.

The 'index.php' file is generally a special file and although one could make a request against it using the URL '/index.php', what is more generally done is to tell Apache that if a request comes in for '/', which notionally maps to the directory itself, that it instead be routed to 'index.php'. 

The way things typically work for PHP then is that any PHP code files are simply dropped in the existing directory which Apache is serving up static files from. Apache does the URL routing, mapping a URL to an actual physical file on the file system. When it finds a file corresponding to a URL, it will return the contents of that file, or if the file type represents a special case, the handler for that file type will be invoked instead. For the case of PHP code files, this will result in the code being executed to generate the response.

This is all achieved by using an Apache configuration of:
    
    
    DocumentRoot /var/www/html
    
    
    <Directory /var/www/html>  
    DirectoryIndex index.php  
    AddHandler application/x-httpd-php .php  
    </Directory>

In this you can start to see why people say PHP is so easy to use as all you need to do is drop the PHP code files in the right directory and they work. In this simple configuration, there is no need for users to worry about URL routing as that is done for them by the web server.

Now you can actually do a similar thing with mod\_wsgi for Python script files by extending this to:
    
    
    DocumentRoot /var/www/html
    
    
    <Directory /var/www/html>  
    Options ExecCGI  
    DirectoryIndex index.py index.php  
    AddHandler application/x-httpd-php .php  
    AddHandler wsgi-script .py  
    </Directory>

That is, you can now simply drop Python code files with a '.py' extension into the directory and they would be executed as Python code when a URL mapped to that file. So if instead of 'index.php' you had 'index.py', accessing the URL for the directory, Apache in seeing that 'index.py' now exists, would use that to serve the request rather than 'index.php'. If the URL instead explicitly referenced a '.py' file by name, then that would be executed to handle the request instead.

Reality is that no one does things this way for Python web applications and there a few reasons why.

The first reason is that Python web applications interact with an underlying server using the web server gateway interface \(WSGI\). This is a very low level interface and quite unfriendly to new users.

This is in contrast to PHP where what is in the PHP file is no where near as low level and instead comes from the direction of being HTML with PHP code snippets interspersed. Those PHP code snippets can then access details of the request and any request content through a high level interface.

For WSGI however, there is no high level interface and you are effectively left having to work at the lowest level and process the request and any request content yourself.

WSGI therefore steers you towards needing to use a separate Python web framework or toolkit to do all that hard work and provide a simpler high level interface onto the request and for generating a response.

At this level where Apache is allowed to handle all the URL routing, then the two Python packages which would be most useful are Werkzeug and Paste. These packages focus mainly on encapsulating the request and response to make your life easier as far as processing the request and generating a response. What they don't do is dictate a URL routing mechanism and thus why they are a good match when using Apache in the way above.

There is therefore no reason why you can't use this approach similar to PHP of simply dropping Python code files a directory, but you are going to have to do more work.

A bigger problem and the second reason why people don't write Python web applications in this way is that of code reloading.

When writing a web application in PHP, every time you modify a PHP code file it will be automatically reloaded and the new code read and used. This is because ultimately, nothing is persistent for a PHP web application and everything is read in again for every request.

Well, that isn't quite true, but as far as you can tell as a user though that is the case.

The reason it isn't strictly true is that all the PHP extensions you may want to use in your web application, and a lot more you don't, are all preloaded into the process where the PHP code is to be executed. The code for these stays persistent across requests. What does get thrown away those is all the code for your application and the corresponding data.

This is in contrast to Python where all code for separate Python code modules is loaded dynamically on demand the first time it is required. Further, the Python code objects are intermingled with other data for your application. There is also no ready distinction between your application code and unchanging code from a separate third party package or a module from the Python standard library.

It is therefore not possible to throw away just your application code and data at the end of each request. Instead, what occurs for Python web applications is that all this application code and data stays persistent in the memory of the process between requests.

As far as code reloading goes this makes it much more difficult. This is because even for a trivial code change you need to kill off the persistent process and start over. The greater cost associated with Python web applications, due to the fact that nothing is preloaded, means that such a restart is expensive. If this was done on every request, the performance will drop dramatically.

Python doesn't therefore lend itself very well to what PHP users are used to of simply being able to drop code files in a directory and for all code changes to be picked up automatically.

The preferred approach in Python is therefore to use a much higher level framework providing simpler and more structured interfaces. These web frameworks provide the high level request and response object which make handling a request easier, but they also take over URL routing as well. This means that instead of relying on Apache to perform URL routing right down to the level of a resource or handler, it only needs to route down to the top level entry point for the whole WSGI application. After that point, the frameworks themselves will handle URL routing.

One can still use the above method as the gateway into a WSGI application using a high level Python web framework, but it doesn't quite work properly when you want to take over the root of the web site.

To get things to work properly, for a Python web application we can use a different type of configuration.
    
    
    Alias / /var/www/wsgi/main.py
    
    
    <Directory /var/www/wsgi>  
    Options ExecCGI  
    AddHandler wsgi-script .py  
    Order allow,deny  
    Allow from all  
    </Directory>

Specifically, the 'Alias' directive allows us to say that all requests that fall under the URL starting with '/', in this case the whole site, will be routed to the resource specified. As that resources maps to a Python code file, it will then be executed as Python code, thus providing the gateway into our WSGI application, with it being able to then perform the actual URL routing required to map a request to a specific handler function.

Because for Python web applications this will be a common idiom, mod\_wsgi provides a simpler way of doing the same thing:
    
    
    WSGIScriptAlias / /var/www/wsgi/main.py
    
    
    <Directory /var/www/wsgi>  
    Order allow,deny  
    Allow from all  
    </Directory>

Using the 'WSGIScriptAlias' directive from mod\_wsgi in this case means that we do not need to worry about setting the 'ExecCGI' option, or map that the file with a '.py' extension should be executed as a WSGI script.

Even when using 'WSGIScriptAlias', you do still need to work in conjunction with Apache access controls, it doesn't provide a back door for avoiding the access controls to ensure you are always using best security practices.

We have now what is the more typical Apache configuration for a Python web application, but how then do we use this in conjunction with an existing PHP application that may be hosted on the same site.

The primary problem if it isn't obvious is that using 'WSGIScriptAlias' for '/' means that all requests to the site are being hijacked and sent into the Python web application. In other words, it would shadow any existing PHP web application that may be hosted out of the document directory for the web server.

The simplest thing which can be done at this point is to host the Python web application at a sub URL instead of the root of the site.
    
    
    WSGIScriptAlias /suburl /var/www/wsgi/main.py

The result will be that all requests prefixed with that sub URL will then go to that Python web application. Anything else will be mapped against the document directory of the server and thus potentially to the PHP web application.

Using a sub URL however isn't always practical. It may be fine where the Python web application is actually a sub site, but if you are intending to replace the existing PHP web application, it is likely preferable that the Python web application give the appearance of being hosted at the root of the site at the same time as the PHP web application is also being hosted at the root of the site.

Is this even possible? If possible, how do we do it?

The answer is that is possible, but we have to rely on a little magic. This magic comes in the form of the mod\_rewrite module for Apache.

Our starting point in this case will be the prior example we had whereby we could drop both PHP and Python code files in the document directory for the server. To that we are going to add our mod\_rewrite rules.
    
    
    DocumentRoot /var/www/html
    
    
    <Directory /var/www/html>
    
    
    Options ExecCGI  
    DirectoryIndex index.php  
    AddHandler application/x-httpd-php .php  
    AddHandler wsgi-script .py
    
    
    RewriteEngine On  
    RewriteCond %{REQUEST_FILENAME} !-f  
    RewriteCond %{REQUEST_FILENAME} !-d  
    RewriteRule ^(.*)$ /main.py/$1 [QSA,PT,L]
    
    
    </Directory>

What this magic rewrite rule will do is look at each request as it comes in and determine if Apache was able to map the URL to a file within the document directory. If Apache was able to successfully map the URL to a file, then the request will be processed normally.

If however the URL could not be mapped to an actual physical file in the document directory, the request will be rewritten such that the request will be redirected to the resource 'main.py'.

Because though 'main.py' is being mapped to mod\_wsgi as a Python code file, the result will be that the Python web application in that file will instead be used to handle the request.

All that remains now is to create 'main.py', which will normally be the existing WSGI script file you use an entry point to your WSGI application.

In copying in the 'main.py' file, ensure that is all you copy in from your existing Python web application. Do not go placing all the source code for your existing Python web application under the server document directory. This is because with this Apache configuration, a URL would then be able to be mapped to those source code files even though it isn't intended that they be so accessible.

So keep your actual Python web application code separate. It is even better in some respects that 'main.py' not be your original WSGI script file. Preferably all it should do is import the WSGI application entry point from the original in the separate source code directory for your Python web application. This limits the danger from having source code in the server document directory, because even if you later stuff up the configuration and accidentally make it so someone can download the actual contents of 'main.py', they haven't got hold of any sensitive data.

Making 'main.py' be a simple wrapper implementing a level of indirection is actually better for another reason.

This is because when we use the mod\_rewrite rules above to trigger the internal redirect within Apache, the adjustments it makes to the URL can stuff up what URLs are then subsequently exposed to a user of your site.

This comes about because normally where your Python web application would see a URL as:
    
    
    /some/url

it will instead see it as:
    
    
    /main.py/some/url

Or more specifically, the 'SCRIPT\_NAME' variable will be passed into the WSGI environ dictionary as:
    
    
    /main.py

rather than an empty string.

The consequences of this is that when your Python web application creates a full URL for the purposes of redirection, that URL will then also have '/main.py' as part of it.

Exposing this internal detail of how we are hosting the Python web application part of the site isn't what we want to do, so we want to strip that out. That way any full URLs which are constructed will make it appear that the Python web application is still hosted at the root of the site and a user will be none the wiser.
    
    
    def _application(environ, start_response):  
     # The original application entry point.  
     ...
    
    
    import posixpath
    
    
    def application(environ, start_response):  
      # Wrapper to set SCRIPT_NAME to actual mount point.
    
    
      environ['SCRIPT_NAME'] = posixpath.dirname(environ['SCRIPT_NAME'])
    
    
      if environ['SCRIPT_NAME'] == '/':  
        environ['SCRIPT_NAME'] = ''
    
    
      return _application(environ, start_response)

Because we are hosting at the root of the site, we could have just set 'SCRIPT\_NAME' to an empty string and be done with it. I use here though a more durable solution in case the rewrite URLs were being used for a sub directory of the server document directory.

And we are done, the result being that we have one site which has both a PHP web application and a Python web application which believe they are both hosted at the root of the site. When a request comes in, Apache will map the URL to file based resources in the server document directory. If that file is a static file the contents of that file will be served immediately. If instead the URL mapped to a PHP code file, then PHP will handle the request. Finally, if the request doesn't map to any file based resource, then the request will be passed through to the Python web application, which will perform its own routing based on the URL to work out how the request should be handled.

This mechanism enables you to add a Python web application to the site and then progressively transfer the functionality of the existing PHP web application across to the Python web application. If URLs aren't changing as part of the transition, then it is a simple matter of removing the PHP code file for a specific URL and that URL will then be handled by the Python web application instead.

Otherwise, you would implement the new URL handlers in the Python web application and then change the existing PHP web application to send requests off to the new URLs.

The key URL for the root of the site will with the above configuration be handled by the 'index.php' file. When you are finally ready to cut it over, then you just need to remove the 'index.php' file, plus the second 'RewriteCond' for '%\{REQUEST\_FILENAME\} \!-d' and the URL requests for the root of the site will also be sent through to the Python web application.

So summarising, there are two things that need to be done.

The first step is changing the Apache configuration to use mod\_rewrite rules to fallback to sending requests through to the Python web application.
    
    
    # Define a mod_wsgi daemon process group.
    
    
    WSGIDaemonProcess my-python-web-application display-name=%{GROUP}
    
    
    # Force the Python web application to run in the mod_wsgi daemon process group.
    
    
    WSGIProcessGroup my-python-web-application  
    WSGIApplicationGroup %{GLOBAL}
    
    
    # Disable embedded mode of mod_wsgi.
    
    
    WSGIRestrictEmbedded On
    
    
    # Set document root and rules for access.
    
    
    DocumentRoot /var/www/html
    
    
    <Directory /var/www/html>
    
    
    Options ExecCGI  
    DirectoryIndex index.php  
    AddHandler application/x-httpd-php .php  
    AddHandler wsgi-script .py
    
    
    RewriteEngine On  
    RewriteCond %{REQUEST_FILENAME} !-f  
    RewriteCond %{REQUEST_FILENAME} !-d  
    RewriteRule ^(.*)$ /main.py/$1 [QSA,PT,L]
    
    
    </Directory>

The second step is setting up the 'main.py' file for the entry point to the Python web application, and implement the fix up for 'SCRIPT\_NAME'.
    
    
    def _application(environ, start_response):  
     # The original application entry point.  
     ...
    
    
    import posixpath
    
    
    def application(environ, start_response):  
      # Wrapper to set SCRIPT_NAME to actual mount point.
    
    
      environ['SCRIPT_NAME'] = posixpath.dirname(environ['SCRIPT_NAME'])
    
    
      if environ['SCRIPT_NAME'] == '/':  
        environ['SCRIPT_NAME'] = ''
    
    
      return _application(environ, start_response)

Overall the concept is simple, it is just the detail of the implementation which may not be obvious and why some may think it is not possible.

What was the DjangoCon US 2014 angle in all this?

The issue of how to do this came up as Collin Anderson will be presenting at talk at DjangoCon called '[Integrating Django and Wordpress can be simple](http://www.djangocon.us/schedule/presentation/35/)'. His talk is on a much broader topic, but I thought I would add a bit to explain in more detail how one can do PHP and Python site merging with Apache.

So if you are at Django and have to deal with PHP applications still, maybe drop in and watch Collin's talk.

---

## Comments

### dcm0229 - December 2, 2014 at 5:13 AM

Note that the WSGIDaemonProcess directive and corresponding features are not available on Windows or when running Apache 1.3. \(this Note is at the bottom of https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives\#WSGIDaemonProcess\). So, for Windows host OS, can you suggest the best approach? thanks

### Graham Dumpleton - December 2, 2014 at 9:48 AM

Please use the mod\_wsgi mailing list as the mod\_wsgi documentation indicates, to ask your questions. http://code.google.com/p/modwsgi/wiki/WhereToGetHelp?tm=6\#Asking\_Your\_Questions

### Unknown - September 6, 2016 at 8:27 AM

This is atclaus from Stack Overflow. I was able to solve my needs with a sub-url. Thanks for your help. Can you say some more about _configuration for mod\_wsgi in the Apache configuration_? Is this the apache.conf or the web app's .conf? Also do you have any articles on python script security? You talk about not exposing all code but I am new to python web apps and am curious about how to handle it well. Thanks\!

### Graham Dumpleton - September 6, 2016 at 9:07 AM

@Andrew If you want to have a discussion about anything relayed to mod\_wsgi, please use the Google Group for mod\_wsgi.  
  
http://modwsgi.readthedocs.io/en/develop/finding-help.html

### oliver - July 10, 2017 at 9:16 PM

Wow this is new. Is it possible to try this out on managed PHP hosting platforms, like Cloudways, where you don't get the root access?

### Graham Dumpleton - July 11, 2017 at 8:26 AM

@oliver This is not new and has always been possible. And no, it is highly unlikely you will be able to use mod\_wsgi on a traditional PHP hosting service. They don't provide level of access required.

