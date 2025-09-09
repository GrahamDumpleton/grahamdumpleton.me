---
title: "Using alternative WSGI servers with OpenShift."
author: "Graham Dumpleton"
date: "Tuesday, January 6, 2015"
url: "http://blog.dscpl.com.au/2015/01/using-alternative-wsgi-servers-with.html"
post_id: "8061523232073056365"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'openshift', 'python', 'wsgi']
comments: 6
published_timestamp: "2015-01-06T23:38:00+11:00"
blog_title: "Graham Dumpleton"
---

One of the pain points with platform as a service \(PaaS\) solutions for Python is that they often impose constraints on what WSGI servers you can use. They may even go as far as only providing support for using a single WSGI server which they preconfigure and which you cannot customise. The problem with placing limitations on what WSGI servers you can use or how to configure them is that not everyone's requirements are the same. The end result is a Python WSGI hosting solution which is sub optimal and cannot be tuned, thus resulting in you not being able to make best use of the resources provided by the PaaS. This can then lead to you having to purchase more capacity than you actually need, because you are wasting what you do have but are unable to do anything about it.

In the future, Docker promises to provide a much better ecosystem which avoids many of these problems. In this blog post though I am going to look at [OpenShift](https://www.openshift.com) specifically and what one can do there. Do realise though that although I am going to focus on OpenShift, this problem isn't unique to just that service. Other services such as Heroku and AWS Elastic Beanstalk have their own issues and limitations as well.

# WSGI server choices on OpenShift

For Python users developing web applications, OpenShift provides Python language specific cartridges for Python 2.6, 2.7 and 3.3. These cartridges currently provide two ways of starting up a Python web application.

The first solution provided is for your Python web application to be hosted using Apache/mod\_wsgi. To get your WSGI application running, all you need to do is provide a WSGI script file with a specific name which contains the WSGI application entry point for your web application. You do not need to worry at all about starting up any WSGI server, as OpenShift would do all that for you. You can also provide a directory of static files which will also be served up.

Although as the author I would like to see Apache/mod\_wsgi be used more widely than it currently is, I can't say I was particularly happy about how Apache/mod\_wsgi was being setup under OpenShift. I could see various issues with the configuration and constraints it imposed and there wasn't really anything you could do to change it. You were also stuck with an out of date version of Apache and mod\_wsgi due to OpenShift only using whatever was found within the RedHat package repository for the version of RHEL being used.

In one of the updates to the Python cartridges they offered a second alternative though. What they did this time was allow you to supply an 'app.py' file. If such an 'app.py' file existed, then rather than starting up Apache/mod\_wsgi, it would run 'python' directly on that 'app.py' file, with the expectation that it would start up a Python web server of some sort, listening on the required port for web requests.

Note here that it had to be a Python code file and OpenShift would run Python on it itself. It did not allow you to provide an arbitrary application, be it a binary, a shell script or even just Python code setup as an executable script. Yes these are meant to be cartridges for running a Python web application, but it is still a somewhat annoying limitation.

What you could not for example do was provide a shell script which ran 'gunicorn', 'uwsgi', or even Apache/mod\_wsgi with a better configuration. You were instead stuck with using a pure Python HTTP or WSGI server which provided a way of running it which consisted of importing the Python module for that WSGI server and then calling a function of that module to start it.

You could for example easily import the Tornado HTTP server and run it, but if you wanted to use standalone Gunicorn, uWSGI or Apache/mod\_wsgi it wasn't readily apparent how you could achieve that.

What one therefore saw was that if someone did want to use a different standalone WSGI server, rather than use the OpenShift Python cartridges, they would use the DIY cartridge instead and try and build up a workable system from that for a Python web application. This would include you having to handle yourself the creation of a Python virtual environment, install packages etc, tasks that were all done for you with the Python cartridges.

Having to replicate all that could have presented many challenges as the Python cartridges use a lot of really strange tricks when it comes to managing the Python virtual environments in a scaled web application. I wouldn't have been surprised therefore that the use of the DIY cartridge precluded you from having a scaled web application.

# Running a WSGI server from app.py

What supplying the 'app.py' file does at least do is prevent the startup of the default Apache/mod\_wsgi installation. We can also code the 'app.py' however we want so lets see if we can simply in turn execute the WSGI server we do want to use.

As an example, imagine that we had installed 'mod\_wsgi-express' by using the pip installable version of mod\_wsgi from PyPi. We might then write the 'app.py' file as:

> 
>     import os
>     
>     
>     OPENSHIFT_REPO_DIR = os.environ['OPENSHIFT_REPO_DIR']
>     
>     
>     os.chdir(OPENSHIFT_REPO_DIR)
>     
>     
>     OPENSHIFT_PYTHON_IP = os.environ['OPENSHIFT_PYTHON_IP']  
>     > OPENSHIFT_PYTHON_PORT = os.environ['OPENSHIFT_PYTHON_PORT']
>     
>     
>     OPENSHIFT_PYTHON_DIR = os.environ['OPENSHIFT_PYTHON_DIR']
>     
>     
>     SERVER_ROOT = os.path.join(OPENSHIFT_PYTHON_DIR, 'run', 'mod_wsgi')
>     
>     
>     VIRTUAL_ENV = os.environ['VIRTUAL_ENV']
>     
>     
>     program = os.path.join(VIRTUAL_ENV, 'bin', 'mod_wsgi-express')
>     
>     
>     os.execl(program, program, 'start-server', 'wsgi.py',  
>     >         '--server-root', SERVER_ROOT, '--log-to-terminal',  
>     >         '--host', OPENSHIFT_PYTHON_IP, '--port', OPENSHIFT_PYTHON_PORT)

When we try and use this, what we find is that sometimes it appears to work and sometimes it doesn't. Most of the time though OpenShift will tell us that the Python web application didn't start up properly.

For a single gear web application, even though it says it didn't start, it may still be contactable. When we try and restart the web application though, we find that the running instance of Apache/mod\_wsgi will not shutdown properly and then the new instance will not run.

If using a scaled application we have the further problem that when OpenShift thinks that it didn't start properly, it will not add that gear to the haproxy configuration and so it will not be used to handle any web requests even if it is actually running.

The question is why does OpenShift think it isn't starting up properly most of the time.

# Changing process names on exec\(\)

The answer is pretty obscure and is tied to how the OpenShift Python cartridge manages the startup of the Python web application when an 'app.py' file is provided. To discover this one has to dig down into the OpenShift control script for the Python cartridge.

> 
>     nohup python -u app.py &> $LOGPIPE &
>     
>     
>     retries=3  
>     > while [ $retries -gt 0 ]; do  
>     >   app_pid=$(appserver_pid)  
>     >   [ -n "${app_pid}" ] && break  
>     >   sleep 1  
>     >   let retries=${retries}-1  
>     > done
>     
>     
>     sleep 2
>     
>     
>     if [ -n "${app_pid}" ]; then  
>     >   echo "$app_pid" > $OPENSHIFT_PYTHON_DIR/run/appserver.pid  
>     > else  
>     >   echo "ERROR: Application failed to start, use 'rhc tail' for more informations."  
>     > fi

The definition of the 'appserver\_pid' shell function reference by this is:

> 
>     function appserver_pid() {  
>     >   pgrep -f "python -u app.py"  
>     > }

What is therefore happening is that the control script is running the code in 'app.py' as 'python -u app.py'. Rather than capture the process ID of the process when run and check that a process exists with that process ID, it checks using 'pgrep' to see if a process exists which has the exact text of 'python -u app.py' in the full command line used to start up the process.

The reason this will not work, or at least why it will not always work is that our 'app.py' is performing an 'os.execl\(\)' call and in doing that the 'app.py' application process is actually being replaced with a new application process inheriting the same process ID. In performing this exec though, the enduring process ID will now show the command line used when the 'os.execl\(\)' was done. As a consequence, the use of 'pgrep' to look for 'python -u app.py' will fail if the check wasn't done quick enough such that it occurred before 'os.execl\(\)' was called.

Since it is checking for 'python -u app.py', lets see if we can fool it by naming the process which will persist after the 'os.execl\(\)' call using that string. This is done by changing the second argument to the 'os.execl\(\)' call.

> 
>     os.execl(program, 'mod_wsgi-express (python -u app.py)', 'start-server',  
>     >         'wsgi.py', '--server-root', SERVER_ROOT, '--log-to-terminal',  
>     >         '--host', OPENSHIFT_PYTHON_IP, '--port', OPENSHIFT_PYTHON_PORT)

Unfortunately it doesn't seem to help.

The reason this time is that the 'mod\_wsgi-express' script is itself just a Python script acting as a wrapper around Apache/mod\_wsgi. Once the 'mod\_wsgi-express' script has generated the Apache configuration based on the command line arguments, it will again use 'os.execl\(\)', this time to startup Apache with mod\_wsgi.

The name of the process therefore is pretty quickly changed once more.

Now 'mod\_wsgi-express' does actually provide a command line option called '--process-name' to allow you to override what the Apache parent process will be called when started. The intention of this was that when running multiple instances of 'mod\_wsgi-express' you could set the names of each to be different and thus more easily identify to which instance the Apache processes belonged.

We therefore try overriding the name of the process when using 'os.execl\(\)', but also tell 'mod\_wsgi-express' to do something similar when it starts Apache.

> 
>     os.execl(program, 'mod_wsgi-express (python -u app.py)', 'start-server',  
>     >        'wsgi.py', '--process-name', 'httpd (python -u app.py)',  
>     >        '--server-root', SERVER_ROOT, '--log-to-terminal',  
>     >        '--host', OPENSHIFT_PYTHON_IP, '--port', OPENSHIFT_PYTHON_PORT)

Success, and it now all appears to work okay.

There are two problems with this though. The first is that it is relying on an ability of 'mod\_wsgi-express' to rename the Apache processes and one may not have such an ability when trying to start some other WSGI server, which may itself use a wrapper script of some sort, or even if you yourself wanted to inject a wrapper script.

The second problem is that although the Apache parent process will now be named 'httpd \(python -u app.py\)' and will be matched by the 'pgrep' command, all the Apache child worker processes will also have that name.

The consequence of this is that 'pgrep' will actually return the process IDs of multiple processes.

As it turns out, the return of multiple process IDs still works with the control script, but does introduce a potential for problem.

The issue this time is that although the Apache parent process will be persistent, the Apache child worker process may be recycled over time. Thus the control script will hold on to a list of process IDs that could technically be reused. This could have consequences later on if you were attempting to shutdown or restart the web application gears, as the control script could inadvertently kill off processes now being run for something else.

Interestingly this problem already existed in the control script even before we tried the trick we are trying to use. This is because the 'app.py' script could have been executing an embedded pure Python HTTP server which itself was forking in order to create multiple web request handler processes. The rather naive way therefore of determining what the process ID of the web application was and whether it started okay, could still cause problems down the track in that scenario as well.

# Interjecting an intermediate process

If performing an 'os.execl\(\)' call and replacing the current process causes such problems, lets then consider leaving the initial Python 'app.py' process in place and instead perform a 'fork\(\)' call followed by an 'exec\(\)' call.

If we do this then we will only have the one process with the command line 'python -u app.py' and it will be our original process that the control script started. The control script shouldn't get confused and all should be okay.

If we were to do this though we have to contend with a new issue. That is that on subsequent shutdown or restart of the web application gear, the initial process has to be able to handle signals directed at it and relay those signals onto the forked child process which is running the actual web application. It also has to monitor that forked child process in case it exits before it was mean't to and then cause itself to exit.

Doing all this in a Python script quickly starts to get messy, plus we are also leaving in place a Python process which is going to be consuming a not insignificant amount of memory for such a minor task.

We could start to look at using a process manager such as supervisord but that is adding even more complexity and memory bloat.

Stepping back, what is simple to use for such a task is a shell script. A shell script is also much easier for writing small wrappers to process environment variables and work out a command line to then be used to execute a further process. In the hope that this will make our job easier, lets change the 'app.py' file to:

> 
>     import os
>     
>     
>     SCRIPT = os.path.join(os.path.dirname(__file__), 'app.sh')
>     
>     
>     os.execl('/bin/bash', 'bash (python -u app.py)', SCRIPT)

What we are therefore doing is replacing the Python process with a 'bash' process which is executing a shell script provided by 'app.sh' instead, but still overriding the process name as we did before.

Now I am not going to pretend that having a shell script properly handle relaying of signals to a sub process is trivial and doing that right is actually a bit of a challenge as well which needs a bit of explaining. I am going to skip explaining that and leave you to read this separate [post](http://veithen.github.io/2014/11/16/sigterm-propagation.html) about that issue.

Moving on then, our final 'app.sh' shell script file is:

> 
>     #!/usr/bin/env bash
>     
>     
>     trap 'kill -TERM $PID' TERM INT
>     
>     
>     mod_wsgi-express start-server \  
>     >         --server-root $OPENSHIFT_PYTHON_DIR/run/mod_wsgi \  
>     >         --log-to-terminal --host $OPENSHIFT_PYTHON_IP \  
>     >         --port $OPENSHIFT_PYTHON_PORT wsgi.py &
>     
>     
>     PID=$!  
>     > wait $PID  
>     > trap - TERM INT  
>     > wait $PID  
>     > STATUS=$?
>     
>     
>     exit $STATUS

This actually comes out as being quite clean compared to the 'app.py' when it was using 'os.execl\(\)' to execute 'mod\_wsgi-express' directly.

Now that we aren't reliant on any special process naming mechanism of anything which is in turn being run, this is also easily adapted to run other WSGI servers such as gunicorn or uWSGI.

# Is it worth all the trouble?

As far as technical challenges go, this was certainly an interesting problem to try and solve, but is it worth all the trouble.

Well based on the amount of work I have seen people putting in to try and mould the OpenShift DIY cartridge into something usable for Python web applications, I would have to say it is.

With the addition of a simple 'app.py' Python script and small 'app.sh' shell script, albeit arguably maybe non obvious in relation to signal handling, it is possible to take back control from the OpenShift Python cartridges and execute the WSGI server of your choice using the configuration that you want to be able to use.

In that respect I believe it is a win.

Now if only I could work out a way to override some aspects of how the OpenShift Python cartridges handle execution of pip to workaround bugs in how OpenShift does things. That though is a problem for another time.

---

## Comments

### Joshua - September 20, 2015 at 11:42 PM

Hi Im fairly new to web hosting and I am struggling with deploying my django project to openshift. Is there a Github repo that you have that I can observe in while reading your post? I know you did as much as you can during the post, but that still doesnt give us \(especially those new to this\) a rather clear look at how you really put this together.

### Graham Dumpleton - September 29, 2015 at 8:09 PM

The https://github.com/GrahamDumpleton/dyndns53 repo uses the script files described here. It isn't a Django application though, so extra work is required for Django. If still needing help, you are best hopping onto the mod\_wsgi mailing list and asking your question there.

### Alexander Todorov - December 1, 2015 at 7:15 AM

Hi Graham,  
have you found by any chance how to serve multiple wsgi scripts from the same cartridge ? I have two Python files which I want to access via different URLs but for some reason OpenShift doesn't allow me to specify WSGIScriptAlias in .htaccess.

### Graham Dumpleton - December 1, 2015 at 7:28 AM

@Alexander There are ways it can be done using mod\_wsgi-express when using the recipe explained in this post. If want help on that you are best dropping an email to the mod\_wsgi mailing list and can explain it there.

### Alexander Todorov - December 1, 2015 at 10:52 PM

Hi Graham,  
thanks for the hint but this looks like too much for my needs. I've found a simple workaround - just make the root wsgi.py file handle some of the URLs and redirect them to other scripts \(Python modules that is\). For those interested I've provided a quick write-up on my blog:  
  
http://atodorov.org/blog/2015/12/01/hosting-multiple-python-wsgi-scripts-on-openshift/

### Graham Dumpleton - December 4, 2015 at 8:18 AM

That will not work where the two WSGI applications cannot co exist together in the same interpreter. For example, you can't run two Django instances like that. So be careful of any conflicts on global data when doing that.

