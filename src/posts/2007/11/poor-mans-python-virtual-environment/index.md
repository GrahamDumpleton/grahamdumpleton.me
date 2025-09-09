---
layout: post
title: "Poor man's Python virtual environment."
author: "Graham Dumpleton"
date: "2007-11-11"
url: "http://blog.dscpl.com.au/2007/11/poor-mans-python-virtual-environment.html"
post_id: "1144294031033538517"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python']
comments: 1
published_timestamp: "2007-11-11T16:13:00+11:00"
blog_title: "Graham Dumpleton"
---

There have now been a number of attempts at implementing virtual environments for Python. That is, providing a means of having multiple isolated environments for the one Python installation on a system, such that it would be possible to run different applications on the same system, but using different sets of installed Python packages. The prime standalone examples of these are [virtual-python](http://peak.telecommunity.com/DevCenter/EasyInstall#creating-a-virtual-python), [workingenv](http://cheeseshop.python.org/pypi/workingenv.py) and [virtualenv](http://pypi.python.org/pypi/virtualenv).  
  
It may well just be that I choose to use MacOS X with the older Python 2.3.5 that comes with the operating system, but even with the more recent virtualenv, it just doesn't seem to always want to work properly. Even when I have ensured that PATH includes first the 'bin' directory for the virtual environment, such that the environment specific versions of tools such as 'easy\_install' are found first, for whatever reason, some packages will still want to write back into the operating system '/Library/Python' directory when I wouldn't expect them to. I also don't seem to be alone in having such problems as evidenced by comments to Ian Bicking's [blog](http://blog.ianbicking.org/2007/10/10/workingenv-is-dead-long-live-virtualenv) where he originally announced virtualenv as a replacement for workingenv.  
  
Now, I will admit that I still haven't found time to properly dig into the internals of Python eggs and so may be missing something, but for creating Python virtual environments, what I don't understand is why simply setting the PYTHONHOME environment variable isn't sufficient to get it all working for the typical case. Yes it means that the environment variable has to always be set, as well as PATH including the 'bin' directory for the virtual environment, but it avoids the idiosyncrasies arising from the way that Python tries to work out where the installed Python library directory is.  
  
To understand what the PYTHONHOME environment variable is all about, one has to consult the source code comments in the file '[Modules/getpath.c](http://svn.python.org/view/python/trunk/Modules/getpath.c?view=auto)' of the Python source code, as any other online documentation seems to be rather lacking. Read the source code as well as the comments and you will find that Python goes through a number of steps to try and determine where the Python lib directory is located when it is run. These can be summarised as:  


  1. Look relative to argv\[0\] to determine if being run out of Python source code build directory.  

  2. Consult the PYTHONHOME environment variable for directory prefix corresponding to where Python was installed.
  3. Look relative to argv\[0\] to determine if being run out of Python installation directories. If argv\[0\] isn't an absolute path, search PATH for the executable which was used and look relative to that instead.  

  4. Look relative to directory prefix where Python was supposed to have been installed.  


The way the virtualenv appears to work is that it tries to set things up so that step 3 still applies.  
  
On MacOS X things gets a bit tricky though, as it doesn't use the method exactly as described. Instead it seems that an absolute path to the Python framework encoded into the executable itself is somehow used. This means that to get virtualenv to work, it is necessary for it copy the Python executable and then use the MacOS X 'install\_name\_tool' program to change where the Python executable is picking up the Python framework from else it will continue to use the Python lib directory from the original Python installation.  
  
Windows also doesn't follow the rules either, with the location of the Python DLL somehow determining where the Python lib directory needs to be.  
  
Either way, once Python has found what it believes is the location of the Python lib directory it will use that and will skip the subsequent steps.  
  
Now, although how step 3 works is different based on what platform you are running on, step 2 is the same. As such setting the PYTHONHOME environment seems to be a simpler and more deterministic way of specifying where the Python lib directory is located, avoiding the need to perform fixups to the Python executable on MacOS X.  
  
As to how to setup a Python virtual environment based on using the PYTHONHOME environment variable, for UNIX based systems it is just a matter of creating a parallel copy of the installed Python installation using symlinks. In some respects it is therefore quite similar to the original virtual-python, except that the Python executable itself is also just a symlink and not a copy.  
  
On MacOS X with Python 2.3 the required steps would therefore be:

```
 mkdir $HOME/pythonenv  
 cd $HOME/pythonenv  
   
 mkdir -p ENV1/bin  
 mkdir -p ENV1/include  
 mkdir -p ENV1/lib/python2.3  
   
 ln -s /usr/bin/python2.3 ENV1/bin/  
 ln -s python2.3 ENV1/bin/python  
   
 ln -s /usr/include/python2.3 ENV1/include/  
   
 for i in /usr/lib/python2.3/*; do ln -s $i ENV1/lib/python2.3/; done  
   
 rm ENV1/lib/python2.3/site-packages  
 mkdir ENV1/lib/python2.3/site-packages  
```

  
To use the virtual environment the 'bin' directory would be added to the head of your PATH and the PYTHONHOME environment variable set.

```
 PATH="$HOME/pythonenv/ENV1/bin:$PATH"  
 export PATH  
   
 PYTHONHOME="$HOME/pythonenv/ENV1"  
 export PYTHONHOME  
```

  
Note that it is the specific intent here that the 'site-packages' directory from the original Python installation is ignored. It would therefore be necessary to reinstall all required packages, including 'setuptools', once the PATH and PYTHONHOME variables had been setup.  
  
Obviously, setting PYTHONHOME has implications if you want to run scripts from one Python application which are themselves standalone Python scripts which refer to a different Python virtual environment. Other issues come up if trying to run scripts which use a completely different version of Python. As such, this poor man's version of Python virtual environments isn't going to work for everyone, but for what I am doing with web applications and [mod\_wsgi](http://www.modwsgi.org/) it works fine, not giving me the problems that virtualenv does on MacOS X.  
  
How exactly Python virtual environments, of any variety, can be used with mod\_wsgi and how mod\_wsgi version 2.0 has been enhanced to make it all reasonably simple to manage I'll cover in a subsequent blog entry. If you can't wait, then you can also check out a non sanitised version of a description about it on the [mod\_wsgi user group](http://groups.google.com/group/modwsgi/browse_frm/thread/466823f087070b5f).

---

## Comments

### Armin Ronacher - November 19, 2007 at 9:08 PM

I wondered the same. I've set up a development server for one of my projects some days ago and installed all libraries locally into a modified PYTHONHOME on a debian box.  
  
Works without a problem and was easy to set up :-\)

