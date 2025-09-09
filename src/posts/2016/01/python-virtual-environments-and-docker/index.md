---
layout: post
title: "Python virtual environments and Docker."
author: "Graham Dumpleton"
date: "2016-01-14"
url: "http://blog.dscpl.com.au/2016/01/python-virtual-environments-and-docker.html"
post_id: "917687300411853962"
blog_id: "2363643920942057324"
tags: ['docker', 'python']
comments: 11
published_timestamp: "2016-01-14T21:46:00+11:00"
blog_title: "Graham Dumpleton"
---

When creating a Docker base image for running Python applications, you have various choices for how you can get Python installed. You can install whatever Python version is supplied by your operating system. You can use Python packages from separate repositories such as the [Software Collections](https://www.softwarecollections.org) \(SCL\) repository for CentOS, or the [dead snakes](https://launchpad.net/~fkrull/+archive/ubuntu/deadsnakes) repository for Debian. Alternatively, you could install Python from source code.

Once you have your base image constructed, you then need to work out the strategy you are going to use for installing any Python modules you require in a derived image for your Python application. You could also source these from operating system package repositories, or you could instead install them from the Python Package Index \(PyPi\).

How you go about installing Python packages can complicate things though and you might get some unexpected results.

The purpose of this blog post is to go through some of the issues that can arise, what best practices are to deal with them and whether a Python virtual environment should be used.

# Installing Python packages

There are two primary options for installing Python packages.

If you are using the operating system supplied Python installation, or are using the SCL repository for CentOS, then many Python modules may also be packaged up for those systems. You can therefore use the operating system packaging tools to install them that way.

The alternative is to install packages from PyPi using ‘pip’. So rather than coming from the operating system package repository as a pre-built package, the software for a package is pulled down from PyPi, unpacked, compiled if necessary and then installed.

Problems will arise though when these two different methods are used in the one Python installation.

To illustrate the problem, consider the scenario where you are using the SCL repository for CentOS.

```
 Installing:  
  python27 x86_64 1.1-20.el7 centos-sclo-rh 4.8 k  
 Installing for dependencies:  
  dwz x86_64 0.11-3.el7 base 99 k  
  iso-codes noarch 3.46-2.el7 base 2.7 M  
  perl-srpm-macros noarch 1-8.el7 base 4.6 k  
  python27-python x86_64 2.7.8-3.el7 centos-sclo-rh 81 k  
  python27-python-babel noarch 0.9.6-8.el7 centos-sclo-rh 1.4 M  
  python27-python-devel x86_64 2.7.8-3.el7 centos-sclo-rh 384 k  
  python27-python-docutils noarch 0.11-1.el7 centos-sclo-rh 1.5 M  
  python27-python-jinja2 noarch 2.6-11.el7 centos-sclo-rh 518 k  
  python27-python-libs x86_64 2.7.8-3.el7 centos-sclo-rh 5.6 M  
  python27-python-markupsafe x86_64 0.11-11.el7 centos-sclo-rh 25 k  
  python27-python-nose noarch 1.3.0-2.el7 centos-sclo-rh 274 k  
  python27-python-pip noarch 1.5.6-5.el7 centos-sclo-rh 1.3 M  
  python27-python-pygments noarch 1.5-2.el7 centos-sclo-rh 774 k  
  python27-python-setuptools noarch 0.9.8-5.el7 centos-sclo-rh 400 k  
  python27-python-simplejson x86_64 3.2.0-3.el7 centos-sclo-rh 173 k  
  python27-python-sphinx noarch 1.1.3-8.el7 centos-sclo-rh 1.1 M  
  python27-python-sqlalchemy x86_64 0.7.9-3.el7 centos-sclo-rh 2.0 M  
  python27-python-virtualenv noarch 1.10.1-2.el7 centos-sclo-rh 1.3 M  
  python27-python-werkzeug noarch 0.8.3-5.el7 centos-sclo-rh 534 k  
  python27-python-wheel noarch 0.24.0-2.el7 centos-sclo-rh 76 k  
  python27-runtime x86_64 1.1-20.el7 centos-sclo-rh 1.1 M  
  redhat-rpm-config noarch 9.1.0-68.el7.centos base 77 k  
  scl-utils-build x86_64 20130529-17.el7_1 base 17 k  
  xml-common noarch 0.6.3-39.el7 base 26 k  
  zip x86_64 3.0-10.el7 base 260 k
```

The only package we installed here was ‘python27’, yet because of dependencies listed for that package, Python modules for Jinja2, Werkzeug, SQLAlchemy and others, often used in Python web applications, were also installed.

The reason this can be an issue is that versions of Python software from such repositories are often not the latest and are potentially quite out of date versions.

Take ‘Jinja2' for instance, the most up to date version available at this time from PyPi is version 2.8. The version which was installed when we installed the ‘python27’ package was a much older version 2.6.

Remember now that this Docker image is intended to be used as a base image and users will install any Python modules on top. If one of the Python modules they required was ‘Jinja2’ and they installed it, they may not get what they expect.

```
 $ pip install Jinja2  
 Requirement already satisfied (use --upgrade to upgrade): Jinja2 in /opt/rh/python27/root/usr/lib/python2.7/site-packages  
 Cleaning up...
 
 
 $ pip freeze  
 Babel==0.9.6  
 Jinja2==2.6  
 MarkupSafe==0.11  
 Pygments==1.5  
 SQLAlchemy==0.7.9  
 Sphinx==1.1.3  
 Werkzeug==0.8.3  
 docutils==0.11  
 nose==1.3.0  
 simplejson==3.2.0  
 virtualenv==1.10.1  
 wheel==0.24.0  
 wsgiref==0.1.2
```

What happened was that when ‘pip’ was run, it already found that ‘Jinja2’ had been installed and so skipped installing it again.

In the end, although the user was likely expecting to get the most up to date version of ‘Jinja2’, that isn’t what happened and they were left with version 2.6.

Because the fact that installing a newer version was skipped was only a warning and doesn’t create an error, the user would likely be oblivious to what happened. They would only find out when their application is running and starts misbehaving or giving errors due to their application being coded for the API of a newer version. 

# Forced updates and pinning

One possible solution to this problem is to always ensure that you supply the ‘-U’ or ‘--upgrade’ option to ‘pip’ when it is run. This will force an update and reinstallation of the Python modules being installed to the latest version even if they are already installed.

```
 $ pip install -U Jinja2  
 Downloading/unpacking Jinja2 from https://pypi.python.org/packages/2.7/J/Jinja2/Jinja2-2.8-py2.py3-none-any.whl#md5=75acb6f1abfc46ed75f4fd392f321ac2  
  Downloading Jinja2-2.8-py2.py3-none-any.whl (263kB): 263kB downloaded  
 Downloading/unpacking MarkupSafe from https://pypi.python.org/packages/source/M/MarkupSafe/MarkupSafe-0.23.tar.gz#md5=f5ab3deee4c37cd6a922fb81e730da6e (from Jinja2)  
  Downloading MarkupSafe-0.23.tar.gz  
  Running setup.py (path:/tmp/pip-build-Sd86kU/MarkupSafe/setup.py) egg_info for package MarkupSafe
 
 
 Installing collected packages: Jinja2, MarkupSafe  
  Running setup.py install for MarkupSafe
 
 
 building 'markupsafe._speedups' extension  
 ...  
 Successfully installed Jinja2 MarkupSafe  
 Cleaning up...  
    
 $ pip freeze  
 Babel==0.9.6  
 Jinja2==2.8  
 MarkupSafe==0.23  
 Pygments==1.5  
 SQLAlchemy==0.7.9  
 Sphinx==1.1.3  
 Werkzeug==0.8.3  
 docutils==0.11  
 nose==1.3.0  
 simplejson==3.2.0  
 virtualenv==1.10.1  
 wheel==0.24.0  
 wsgiref==0.1.2
```

Although this will ensure we have the latest version, it has the potential to cause other problems.

The issue here is if a newer version of a package which was installed had a backwards incompatible change. This could cause a failure if not all other packages which used that package, which were already installed, weren’t also updated. If a command was then run which used the package that was not updated, then it would fail in trying to use the now incompatible package.

Pinning packages by specifying a specific version on the command line when running ‘pip’, or in a ‘requirements.txt’ file doesn’t really help either. This is because any update to a newer version, regardless of whether it is the latest or not, risks causing a failure of a Python module installed due to some dependency in an operating system package.

A further concern when using ‘pip’ to install a newer version of a Python module that already exists is the fact that you are replacing files which may have been installed by a package when using the system packaging tools. In general this wouldn’t be an issue when using Docker as you wouldn’t ever subsequently remove a package installed using the system packaging tools in the life of that Docker container. It is still though not ideal that you are updating the same Python module and files with different packaging tools.

The short of it is that it is simply bad practice to use ‘pip’ to install Python modules into a Python installation, setup using system packaging tools, which has the same Python modules already installed that you are trying to add.

# Per user package directory

If installing Python modules using ‘pip' into the same directory as where there is an existing version installed using the system packaging tools is a problem, what about using the per user package directory?

When using ‘pip’ this can be achieved using the ‘--user’ option. There is similarly a ‘--user’ option that can be used when running a ‘setup.py’ file for a package when installing it.

In both cases, rather than the Python modules being installed into the main ‘site-packages’ directory of the Python installation, they are installed into a special directory in the users home directory. For Linux this directory is located at:

```
 $HOME/.local/lib/pythonX.Y/site-packages
```

The ‘X.Y’ will depend on the version of Python being used.

Although this at least eliminates conflicts where ‘pip’ could replace files installed by the system packaging tools, it doesn’t resolve the issue with the version of a package being updated without again having to resort to using the ‘-U’ or ‘--update’ option to ‘pip’.

```
 $ pip install --user Jinja2  
 Requirement already satisfied (use --upgrade to upgrade): Jinja2 in /opt/rh/python27/root/usr/lib/python2.7/site-packages  
 Cleaning up...
```

Per user package directories are therefore not really a solution either.

# Python virtual environments

It is in part because of the problems arising when trying to use a single common Python installation with multiple applications, where different Python module versions were required, that the idea of an isolated Python virtual environment came about. The most popular such tool for creating an isolated Python environment is ‘virtualenv’.

Although the intent with Docker is that it would only hold and run the one application, could we still use a Python virtual environment anyway, thus avoiding the problems described.

```
 $ virtualenv venv  
 New python executable in venv/bin/python2  
 Also creating executable in venv/bin/python  
 Installing Setuptools...done.  
 Installing Pip...done.
 
 
 $ source venv/bin/activate
 
 
 (venv)$ pip install Jinja2  
 Downloading/unpacking Jinja2  
  Downloading Jinja2-2.8.tar.gz (357kB): 357kB downloaded  
  Running setup.py egg_info for package Jinja2
 
 
 Downloading/unpacking MarkupSafe (from Jinja2)  
  Downloading MarkupSafe-0.23.tar.gz  
  Running setup.py egg_info for package MarkupSafe
 
 
 Installing collected packages: Jinja2, MarkupSafe  
  Running setup.py install for Jinja2  
  Running setup.py install for MarkupSafe
 
 
 building 'markupsafe._speedups' extension  
  ...  
 Successfully installed Jinja2 MarkupSafe  
 Cleaning up...
```

And the answer is a most definite yes.

The reason that the Python virtual environment works is because it creates its own fresh ‘site-packages’ directory for installing new Python modules which is independent of the ‘site-packages’ directory of the main Python installation.

```
 $ pip freeze  
 Jinja2==2.8  
 MarkupSafe==0.23  
 wsgiref==0.1.2
```

The only Python packages that will be found in the ‘site-packages’ directory will be ‘pip’ itself, and the couple of packages it requires such as ‘setuptools’, and the additional packages that we install. There is therefore no danger of conflicts with any packages that were installed into the main Python installation by virtue of operating system packages.

Note that this wasn’t always the case. Originally the ‘virtualenv’ tool when creating a Python virtual environment would add to what was in the Python ‘site-packages’ directory, rather than overriding it. Back then it was necessary to provide the ‘--no-site-packages’ option to ‘virtualenv’ to have it work as it does now. The default was changed because the sorts of problems described here would still occur if the ‘site-packages’ directory wasn’t completely distinct.

The option does exist in ‘virtualenv’ to set up the virtual environment with the old behaviour by a command line option, but you really do not want to go there.

And if you are wondering why ‘wsgiref’ shows up in the ‘pip freeze’ above even though it wasn’t installed as a separate package. It seems that even though ‘wsgiref’ is part of the Python standard library, ‘setuptools’ still thinks it is a distinct versioned package when using Python 2.7. As much as it is a bit confusing, its presence in the output of ‘pip freeze’ can be ignored. You may want to ensure you don’t list ‘wsgiref’ in a ‘requirements.txt' file though as you might then accidentally install it from PyPi, which could be an older version of the source code than what the Python standard library contains.

# Building Python from source

So although we are only bundling up the one application in the Docker container, if using a Python version which is installed from an operating system package repository, or an associated package repository, a Python virtual environment is very much recommended to avoid problems.

What now for the case where the Python version has been installed from source code?

Well because we are compiling from source code and would be installing into a location distinct from the main system Python, there is no possibility for additional Python packages to get installed. The ‘site-packages’ directory would therefore be empty.

In order to allow further packages to be installed, we would at least install ‘pip’, but as for a Python virtual environment only ‘pip’ and what it requires such as ‘setuptools’ would be installed. Any further Python modules would also be installed using ‘pip’ and so there is no conflict with any Python modules installed via system packaging tools.

This means that strictly speaking if installing Python from source code in a Docker container, we could skip the use of a Python virtual environment. The only issue, depending on what user was used to install this Python version, would be whether file system permissions need to be fixed up to allow an arbitrary user to install subsequent Python modules during any build phase for the application in creating a derived image.

# Setting up a virtual environment

What we therefore have is that if you are using a version of Python which comes as part of the operating system packages, or which is installed from a companion repository such as SCL for CentOS, you should really always ensure that you use a Python virtual environment. Do not attempt to install Python modules using ‘pip’ into the ‘site-packages’ directory for the main Python installation and avoid using Python packages from the operating system package repository.

If you have compiled Python from source code as part of your Docker image, there is no strict need to use a Python virtual environment. Using tools like ‘pip’ to install Python modules direct into the ’site-packages’ directory of the separate Python installation should be fine.

The question now is what is the best way to set up any Python virtual environment when it is used. What file system permissions should be used to allow both ‘root’ and non ‘root’ users to install packages. How should the Python virtual environment be activated or enabled so that it is always used in the Docker container.

All these issues I will discuss in a followup to this blog post.

---

## Comments

### Gyuri - January 16, 2016 at 8:07 AM

Nice post, thanks\! But don' forget about anaconda/miniconda docker images. I think they can be used quite effectively with conda environments.

### Graham Dumpleton - January 16, 2016 at 8:13 AM

Doesn't matter what Python distribution you use, if they preinstall some Python modules for you, problems can arise if using 'pip'. If they don't use 'pip' and require some other packaging tool that you must use to install Python modules, then it might just cause its own problems. One needs to dig deeper into how different Python installations are installed, setup and how it is expected they be used. You can't just assume that everything will work smoothly.

### Rodrigo Valin - January 18, 2016 at 11:19 PM

If Python2.7 is what you need, maybe you should try another disto, one with Python 2.7 as a base. I also would like to know why CentOS is packaging Python with dependencies on something not on the standard distribution.

### Graham Dumpleton - January 20, 2016 at 3:55 PM

CentOS does have Python 2.7 as a base, but it happens to be 2.7.5. SCL is at least newer at 2.7.8. I expect that the base version with CentOS is going to be the same as packaged by the same people. Other Linux distributions could just as easily have similar issues.  
  
Overall the issue has noting to do with what distribution you use as anything where the Python version and Python modules are packaged using the operating system packaging system will suffer the same sorts of issues whether additional Python modules are installed implicitly or explicitly.  
  
So not a question of what I choose as for what I am doing with ultimately providing Docker base images for Python, I don't have luxury of making the choice as to what is used as I am not the end consumer. I have to provide Docker base images for a range of common Linux distributions because people will have their favourites, or even a requirement to use specific Linux distributions. I have to therefore come up with best practices across different Linux distributions and the point of the post is just to let people know what I am finding so you can ensure you are also applying best practices and not doing something that will cause you problems down the track.

### None - March 18, 2016 at 11:10 AM

Graham, thanks for the infromative, well-written post. Today I'm learning how to create a docker image for my Flask application, and this will set me in the right direction.  
  
One suggestion for formatting your blog post: put a "Summary" section right at the top that gets right to the point, which here is something like "in most cases, you should use a virtualenv when packaging Python applications with Docker, even if you only need one set of Python packages in a container." As a blogger myself, I want people to read my entire post with the hows and whys, but I also want people who are in a hurry to get the most important part of the message right away\!  
  
Chris Martin

### Graham Dumpleton - March 18, 2016 at 11:16 AM

@Chris Have you considered not rolling your own image and instead use someone else's base image?  
  
I have my own base image which I introduced at:  
  
\* [/posts/2014/12/hosting-python-wsgi-applications-using/](/posts/2014/12/hosting-python-wsgi-applications-using/)  
  
and also covered in subsequent blog posts.  
  
Unfortunately I do need to deprecate that image because Docker Hub registry automated builds no longer work for any Docker image which uses setcap for Linux capabilities, even though they recommend that as way of avoiding running as root in their documentation.  
  
I have a replacement image in the works which is even better and supports multiple WSGI servers, or your own scripts or even ASYNC web servers for Python. It is already available, but design of some of the internals of how it works not finalised.

### None - March 19, 2016 at 7:35 AM

Graham, I ended up rolling my own image based on Debian. So far it's just for testing/evaluation purposes so I'm using Flask's built-in WSGI server \(not a real WSGI server for production use\).

### Gavin - June 14, 2016 at 2:12 AM

Chris - you could also install python packages directly on the base image using a requirements file-  
  
pip install -r requirements.txt  
  
This would solve the problem of not upgrading a pre-installed library \(as in your example of Jinja2 above\).

### Graham Dumpleton - June 14, 2016 at 10:02 AM

@Gavin How would that solve the problem? You are going to have the same sorts of problems when installing into a system Python. If you packages aren't pinned to a specific version and a version already exists, it will not install a newer version. The only reliable solution and which is regarded as best practice is to use a Python virtual environment.

### axe - February 11, 2017 at 1:16 AM

using default   
pip install flask   
in docker container gives me error on ubuntu:14.04 base image.  
and I guess using a virtual env maybe works   
.but how could we use virtualenv in docker containter???  
could you plz post a dockerfile on github???

### Graham Dumpleton - February 12, 2017 at 4:47 PM

@axe You are better off asking on StackOverflow if you are after help on how to solve a specific issue you are having and need help debugging it.

