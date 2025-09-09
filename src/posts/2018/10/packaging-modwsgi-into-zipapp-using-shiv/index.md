---
layout: post
title: "Packaging mod_wsgi into a zipapp using shiv."
author: "Graham Dumpleton"
date: "2018-10-22"
url: "http://blog.dscpl.com.au/2018/10/packaging-modwsgi-into-zipapp-using-shiv.html"
post_id: "8128449996432012923"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'shiv', 'zipapp']
comments: 0
published_timestamp: "2018-10-22T20:11:00+11:00"
blog_title: "Graham Dumpleton"
---

At the recent DjangoCon US conference, Peter Baumgartner presented a talk titled [Containerless Django: Deploying without Docker](https://2018.djangocon.us/talk/containerless-django-deploying-without/). In the talk Peter described what a zipapp \(executable Python zip archive\) is and how these could be created using the [shiv](https://shiv.readthedocs.io/) tool, the aim being to be able to create a single file executable for a complete Python application, including all its Python package dependencies. The only requirement would be that any target platform you copy the executable to, must provide a matching Python runtime.

A question which was asked after the talk was whether it would be possible to use shiv in conjunction with mod\_wsgi. My initial thinking was that yes, it should be possible. As it turned out, it wouldn't work as things were, due to how shiv set up the application so it knew where all the Python package dependencies were unpacked when the executable was run. With a bit of black magic though, I was able to get mod\_wsgi to work. This post is to highlight what what can be done in case you want to try it out for yourself.

# Goals of zipapp and shiv

The goal of the zipapp executable format is to allow a Python application, along with all its Python package dependencies, to be bundled up as a single executable file. The zipapp format and support for it has been available since Python 2.6, but probably isn't that widely known about. The format got additional support in Python 3.5 via [PEP 441](https://legacy.python.org/dev/peps/pep-0441/). It still though had limitations, including not being able to be used for Python packages with C extensions.

The shiv tool for creating zipapp executables, works around this and other issues by intercepting the entry point for the zipapp executable and unpacking files from the executable into the file system before actually running the bundled application.

As an example of what you can do, consider the [certbot](https://pypi.org/project/certbot/) tool for managing creation of certificates using Let's Encrypt.

To install certbot is easy enough and can be done with pip. The problem is, that in addition to its own code, it also depends on a number of other Python packages. Best practice would be to install certbot and those packages into their own Python virtual environment. You could do this yourself, or you could use [pipsi](https://pypi.org/project/pipsi/). Neither of these makes it easy to then copy the application to another host. This is where shiv can come into play.

For this case of certbot, to create a single executable file for certbot, you can run shiv as:
    
    
    $ shiv certbot -o certbot.pyz -c certbot
    
    

The result is a single `certbot.pyz` file, which you can run like any other executable.
    
    
    $ ./certbot.pyz --help
    
    - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
      certbot [SUBCOMMAND] [options] [-d DOMAIN] [-d DOMAIN] ...
    
    Certbot can obtain and install HTTPS/TLS/SSL certificates.  By default,
    it will attempt to use a webserver both for obtaining and installing the
    certificate. The most common SUBCOMMANDS and flags are ...
    
    

Being a single file, which includes both the code for certbot itself, and all the Python packages it depends on, it is easy to copy the file to another host. The only requirements are that it has the same version of Python installed, and the target host is the same architecture if Python packages with C extensions are used.

# Trying shiv with mod\_wsgi

Trying this with `mod_wsgi-express` things weren't quite as successful. The building of the executable file ran okay:
    
    
    $ shiv 'mod_wsgi==4.6.4' -o mod_wsgi-express.pyz -c mod_wsgi-express
    
    

But running:
    
    
    $ ./mod_wsgi-express.pyz start-server --log-to-terminal
    
    

yielded the error:
    
    
    File "/var/tmp/mod_wsgi-localhost:8000:501/handler.wsgi", line 7, in 
         import mod_wsgi.server
    ModuleNotFoundError: No module named 'mod_wsgi.server'; 'mod_wsgi' is not a package
    
    

This fails because when `mod_wsgi-express start-server` is run, it is actually performing a fork/exec of the Apache httpd server, but the directory shiv has created holding all the required Python packages, isn't known of by the Apache mod\_wsgi module when it is in turn loaded. It therefore cannot find the Python module called `mod_wsgi` which the `handler.wsgi` file for `mod_wsgi-express` uses.

The specific reason this is the case, is because the shiv bootstrap code executed when the executable file is run, only adjusts `sys.path` of the current process so that the bundled Python packages can be found. It does not set the `PYTHONPATH` environment such that it would be inherited by subprocesses. The result is that the directory is only known of by that process alone, or any direct forks. It will not be known of by any sub process created by executing a standalone program such as the Apache httpd server.

# A bit of black magic

Unfortunately, it doesn't seem that the shiv bootstrap code leaves any global state variables in a readily accessible place, which can be used to determine whether shiv was used, and what the name of the directory with the required Python packages are. The only place a variable exists with the name of the directory we want, is in a local stack frame from a prior function call.

Getting access to the directory therefore relies on a bit of black magic.
    
    
        site_packages = []
    
        if '_bootstrap' in sys.modules:
            bootstrap = sys.modules['_bootstrap']
            if 'bootstrap' in dir(bootstrap):
                frame = inspect.currentframe()
                while frame is not None:
                    code = frame.f_code
                    if (code and code.co_filename == bootstrap.__file__ and
                            code.co_name == 'bootstrap' and
                            'site_packages' in frame.f_locals):
                        site_packages.append(str(frame.f_locals['site_packages']))
                        break
                    frame = frame.f_back
    
    

This makes a guess that shiv was used by looking to see if the `_bootstrap` module had been imported and that it contained a `bootstrap()` function. If it was, we look back through the function stack looking for that function and extract the value of the `site_packages` variable from the locals of that function.

Knowing that shiv was used, and what the directory with the required Python packages was, we can use it in the generated configuration for Apache/mod\_wsgi, so the embedded Python interpreter it runs, can find them.

Sure this is a hack, but unless shiv provides a better way of knowing when it is being run and what the directory with the Python packages was, we don't have much choice. Good thing at least is you don't have to care, as this fiddle is hidden away in `mod_wsgi-express` and you just need to use the right version of the `mod_wsgi` package, which is version 4.6.5 or newer.
    
    
    $ shiv 'mod_wsgi==4.6.5' -o mod_wsgi-express.pyz -c mod_wsgi-express
    
    

# Apache httpd server

When you use shiv to create the executable zipapp file, the target host must still have Python installed as well. This is because it is only the application code and Python packages it requires that are bundled in the executable file. The Python interpreter itself is not included.

In the case of `mod_wsgi-express`, we also need the Apache httpd server. With the above command, both the host where the executable is built and the target host must have it installed, and in the same location.

Unlike with the Python interpreter, there is a way around this for the Apache httpd server, and it can instead be bundled in the executable as well. This is by virtue of a little known companion package for `mod_wsgi` called `mod_wsgi-httpd`. Like with `mod_wsgi`, the `mod_wsgi-httpd` package exists on PyPi and can be installed using `pip`. When installed, it will build the Apache httpd server from source code. When `mod_wsgi` is then subsequently installed, it will use it instead.
    
    
    $ shiv 'mod_wsgi-httpd==2.4.35.*' 'mod_wsgi==4.6.5' -o mod_wsgi-express.pyz -c mod_wsgi-express
    
    

We now have the Apache httpd server and `mod_wsgi-express` bundled in the one executable file. This can be copied to another host and the Apache httpd server doesn't need to be installed separately on either host.

# Bundling your application

The example above for `mod_wsgi-express` is only bundling it and the Apache httpd server, it isn't including your application. The shiv documentation provides a few examples of bundling your application code.

If you do that, and it is a Django application, you will want to use the Django management command integration for `mod_wsgi-express`. You can then setup the shiv entrypoint to run the `runmodwsgi` Django management command.

For other WSGI applications, you can have the shiv entrypoint import `mod_wsgi.server` and call the `start()` function within that module, passing as a list the same options as you would pass to `mod_wsgi-express start-server`.

If want more details on this, for now would suggest posting on the [mod\_wsgi mailing list](https://groups.google.com/forum/#!forum/modwsgi) and I can provide additional information.