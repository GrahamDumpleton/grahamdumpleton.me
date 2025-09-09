---
title: "Launching applications in Docker containers."
author: "Graham Dumpleton"
date: "Tuesday, December 16, 2014"
url: "http://blog.dscpl.com.au/2014/12/launching-applications-in-docker.html"
post_id: "3355522079796125873"
blog_id: "2363643920942057324"
tags: ['apache', 'docker', 'mod_wsgi', 'python', 'wsgi']
comments: 1
published_timestamp: "2014-12-16T23:33:00+11:00"
blog_title: "Graham Dumpleton"
---

So far in this current series of blog posts I [introduced](http://blog.dscpl.com.au/2014/12/hosting-python-wsgi-applications-using.html) the Docker image I have created for hosting Python WSGI applications using Apache/mod\_wsgi. I then went on to explain what happens when you [build your own image](http://blog.dscpl.com.au/2014/12/deferred-build-actions-for-docker-images.html) derived from it which incorporates your specific Python web application. In this blog post I am going to explain what happens when you run the image and how your Python web application gets started.

As shown in the previous blog posts I gave an example of the Dockerfile you would use for a simple WSGI hello world application:

> 
>     FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild
>     
>     
>     CMD [ "wsgi.py" ]

I also presented a more complicated example for a Django site. The Dockerfile for that was still only:

> 
>     FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild
>     
>     
>     CMD [ "--working-directory", "example", \  
>     >  "--url-alias", "/static", "example/htdocs", \  
>     >  "--application-type", "module", "example.wsgi" ]

In neither of these though is there anything that looks like a command to start up Apache/mod\_wsgi or any other WSGI server. So first up lets explore how an application is started up inside of a Docker container.

# Containers as an application

There are actually two different approaches one can take as to how to start up an application inside of a Docker container.

The first is to create a base image which contains the application you want to run. When you now start up the Docker container, you provide the full application command line as part of the command to launch the container.

For example, if you had created an image containing the Python interpreter and a Django web application with all dependencies installed, you could start up the Django web application using the Django development server using:

> 
>     docker run my-python-env python example/manage.py runserver

If you wanted to start up an interactive shell so you could explore the environment of the container and/or manually run up your application, you could start it with:

> 
>     docker run -it my-python-env bash

The second approach entails viewing the container itself as an application. If setup up in this way the image would be hardwired to start up a specific command when the container is launched.

For example, if when building your container you specified in the Dockerfile:

> 
>     CMD [ “python”, “example/manage.py”, “runserver” ]

when you now start the container, you do not need to provide the command to run. In other words, running:

> 
>     docker run my-python-env

would automatically start the Django development server.

You could if you wish still provide a command, but it will override the default specified by the ‘CMD’ instruction and cannot be used to extend the existing command with additional options.

If you therefore wanted to change for some reason the port the Django development server was listening on within the container, you would have to duplicate the whole command.

> 
>     docker run my-python-env python example/manage.py runserver 80

The ‘CMD’ instruction, although it allows you to supply a default command, doesn’t therefore go so far as to make the container behave like it is an application in its own right, which can accept arbitrary command line arguments when run.

To have a container behave like that, we use an alternative instruction to ‘CMD’ called ‘ENTRYPOINT'.

So we swap the ‘CMD’ instruction with ‘ENTRYPOINT’, setting it to the default command for the container.

> 
>     ENTRYPOINT [ “python”, “example/manage.py”, “runserver” ]

When we now run the container as:

> 
>     docker run my-python-env

the Django development server will again be run, but we can now supply additional command line options which will be appended to the default command.

> 
>     docker run my-python-env 80

Although we changed to the ‘ENTRYPOINT’ instruction, it and the ‘CMD’ instruction are not exclusive. You could actually write in the Dockerfile:

> 
>     ENTRYPOINT [ “python”, “example/manage.py”, “runserver” ]
>     
>     
>     CMD [ “80” ]

In this case when you start up the container, the combined command line of:

> 
>     python example/manage.py runserver 80

would be run.

Supply any command line options when starting the container in this case, and they will override those specified by the ‘CMD’ instruction, but the ‘ENTRYPOINT’ instruction will be left as is. Running:

> 
>     docker run my-python-env 8080

would therefore result in the combined command line of:

> 
>     python example/manage.py runserver 8080

Those therefore are the basic principals around how to launch an application within a container when it is started. Now lets look at what the Docker image I have created for running a Python WSGI application is using.

# Inheritance of an ENTRYPOINT

In the prior blog post I explained how the Docker image I provide isn’t just one image but a pair of images. The base image packaged up all the required tools, including Python, Apache and mod\_wsgi. The derived image was what was called an ‘onbuild’ image and controlled how your specific Python web application would be built and combined with the base image.

The other thing that the ‘onbuild’ image did was to define the process for how the web application would then be started up when the container was run. The complete Dockerfile for the ‘onbuild’ image was:

> 
>     FROM grahamdumpleton/mod-wsgi-docker:python-2.7  
>     >   
>     > WORKDIR /app  
>     >   
>     > ONBUILD COPY . /app  
>     > ONBUILD RUN mod_wsgi-docker-build  
>     >   
>     > EXPOSE 80  
>     >   
>     > ENTRYPOINT [ "mod_wsgi-docker-start" ]

As can be seen, this specified an ‘ENTRYPOINT’ instruction, which as we now know from above, will result in the ‘mod\_wsgi-docker-start’ command being run automatically when the container is started.

Remember though that to create an image with your specific Python web application you actually had to create a further image deriving from this ‘onbuild’ image. For our Django web application that was:

> 
>     FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
>     >   
>     > CMD [ "--working-directory", "example", \  
>     >  "--url-alias", "/static", "example/htdocs", \  
>     >  "--application-type", "module", "example.wsgi" ]

This final Dockerfile doesn’t itself specify an ‘ENTRYPOINT’ instruction, but it does define a ‘CMD’ instruction.

This highlights an important point. That is that an ‘ENTRYPOINT’ instruction will be inherited from a base image and will also be applied to the derived image. Thus when we startup up the container corresponding to the final image, that command will still be run.

As it turns out, a ‘CMD’ instruction will also be inherited by a derived image, but in this case the final image specified its own ‘CMD’ instruction. The final result of all this was that when the container was started up, the full command that was executed was:

> 
>     mod_wsgi-docker-start —working-directory example \  
>     >     —url-alias /static example/htdocs \  
>     >     —application-type module example.wsgi

As was the case when building the final image and the ‘mod\_wsgi-docker-build’ was being run in the context of building that image, there is various magic going on inside ‘mod\_wsgi-docker-start’ so time to delve into what it is doing.

# Preparing the environment on start up

When the image containing your Python web application was being built, the ‘mod\_wsgi-docker-build’ script allowed you to provide special hook scripts which would be run during the process of building the image. These were a ‘pre-build’ and ‘build’ hook. These allowed you to perform special actions prior to ‘pip’ being run to install any Python packages, as well as afterwards, to perform any subsequent application specific setup.

When deploying the web application and starting it up, it is common practice to again provide an ability to have special hook scripts to allow you to perform additional steps. These are sometimes called a ‘deploy’ and ‘post-deploy’ hook.

One of the first things that the ‘mod\_wsgi-docker-start’ script therefore does is execute any ‘deploy’ hook.

> 
>     if [ -x .docker/action_hooks/deploy ]; then  
>     >   echo " -----> Running .docker/action_hooks/deploy"  
>     >   .docker/action_hooks/deploy  
>     > fi

As with the hooks for the build process, this should reside in the ‘.docker/action\_hooks’ directory and the script needs to be executable.

Now normally for a web site if you have a backend database it would be persistent and the data stored in it would have a life independent of the life time of individual containers running your web application.

If however you were using Docker to create a throw away instance of a Python web application and it was paired to a transient database instance that only existed for the life of the Python web application, then one of the steps you would need to perform is that of preparing the database, creating any tables and possibly populating it with data. This would need to be done before starting the actual Python web application.

One use therefore of the ‘deploy’ hook if running a Django web application is to run inside of the hook script the ‘migrate’ Django management command.

> 
>     #!/usr/bin/env bash
>     
>     
>     python example/manage.py migrate

There is one important thing to note here which is different to what happens when hook scripts are run during the build phase. That is that during the build phase the ‘mod\_wsgi-docker-build’ script itself and any hook scripts would use:

> 
>     set -eo pipefail

The intent of this was to cause a hard failure when building the image rather than leaving the image in an inconsistent state.

What to do about errors during the actual deployment phase is a bit more problematic. If one causes a hard failure then it would cause the container to shutdown immediately. Taking such a drastic action may be undesirable as it robs you of the possibility of trying to deal with any errors and/or alerting of a problem and then running in a degraded state while someone is able to look at and rectify any issue.

It is something I don’t know what the best answer is right now so am open to suggestions of how to deal with it. For now therefore if an error does occur in a ‘deploy’ hook, the actual Python web application will be started up anyway.

# Starting up the Python web application

Having run any ‘deploy’ hooks we are now ready to start up the actual Python web application. The part of the ‘mod\_wsgi-docker-start’ script which does this is:

> 
>     SERVER_ARGS="--log-to-terminal --startup-log --port 80"
>     
>     
>     exec mod_wsgi-express start-server ${SERVER_ARGS} "$@"

The key step in this is the execution of the ‘mod\_wsgi-express’ command. I will defer to a subsequent blog post to talk more about what ‘mod\_wsgi-express' is doing, but it is enough to know right now that it is what is actually starting up Apache and loading up your Python WSGI application so that it can then handle any web requests.

In running ‘mod\_wsgi-express’ we by default supply it with the ‘—log-to-terminal’ option to have it log to stdout/stderr so that Docker can collect the logs automatically, making them available to commands such as ‘docker logs’.

When we do run ‘mod\_wsgi-express’, it is important to note that we do it via an ‘exec’. This is done so that Apache will replace the current script process and so inherit process ID 1. This is done because Docker treats process ID 1 as being special and it is that process where it delivers any signals injected into the container from outside. Having Apache run as process ID 1 therefore ensures that it receives shutdown signals for the container properly and can attempt to shutdown the Python web application in an orderly manner.

What process ID 1 should be in a Docker container is actually something that sees a bit of debate. In one corner the Docker philosophy has that a container should only run one application and so it is sufficient for that application process to run as process ID 1.

In the other corner you have others who argue that in the limited environment of a Docker container you are missing many of the things that the normal init process running in a UNIX system as process ID 1 would do such as to cleanup zombie processes and the like. You also lack the ability for an application process to be restarted if it crashes.

You therefore will see people who will run something like ‘runit’ or ‘supervisord’ inside of the container with those starting up and managing the actual application processes.

For the image I am providing I am relying on the fact that Apache is its own process supervisor for its managed child processes and has demonstrated stability and although its child process may crash, the Apache parent process is rock solid and doesn’t crash.

I did contemplate the use of ‘supervisord’ for other reasons, but a big problem with ‘supervisord' is that it still has not been ported to Python 3. This is an issue because when using Docker it is common to provide separate images for different Python versions. This is done to cut down on the amount of fat in the images. This means that for a Python 3 image there only exists Python 3. Having to install a copy of Python 2 as well just so one can run ‘supervisord’ is therefore somewhat annoying.

# The problem of ‘post-deploy’ actions

Now I mentioned previously that it is common to have both a ‘deploy’ and ‘post-deploy’ hook script, with the ‘deploy’ script as shown being run prior to starting the actual Python web application. The idea with the ‘post-deploy’ script is that it would be run after the Python web application has been started.

Such ‘post-deploy’ scripts cause a number of complications.

The first is that to satisfy the requirement that the Apache process be process ID 1, it was necessary to ‘exec’ the ‘mod\_wsgi-express’ command when run. Because an ‘exec’ was done, then nothing else can be done after that within the ‘mod\_wsgi-docker-start’ script as it is no longer running.

One might be able to support a ‘post-deploy’ script when using something like ‘runit’ or ‘supervisord’ if they allow ordering relationships to be defined for when commands are started up, and they allow for one off commands to be run rather than attempting to rerun the command if it exits straight away.

Even so, this doesn’t solve all the problems that exist with what might be run from a ‘post-deploy’ script.

To understand what these issues are we need to look at a couple of examples of what might be done in a ‘post-deploy’ script.

The first example is that you might want to use a ‘post-deploy’ script to hit your Python web application with requests against certain URLs to forcibly preload parts of the application code base before it starts handling web requests. This might be desirable with Django in particular because of the way it lazily loads view handlers in most cases only when they are accessed.

The second example is where you need to poll the Python web application to ensure that it has actually started up properly and is serving requests okay. When all is okay, you might then use some sort of notification system to announce availability of this instance of the Python web application, resulting in it being added into a server group of a front end load balancer.

In both these cases, such a script has to be tolerant of the web application being slow to start and cannot assume that it will actually be ready when the scripts run. Since this is the case and they would need to poll for availability of the Python web application, the need for having a separate ‘post-deploy’ phase is somewhat diminished. One one can instead do is start these actions as background processes during the ‘deploy’ phase instead.

So due to the requirement that Apache needs to run as process ID 1, there is at this point no distinct ‘post-deploy’ phase. To achieve the same result, these should be run as background tasks from the ‘deploy’ phase instead, polling for availability of the Python web application before then running what ever it is intended they should do.

# Starting up an interactive shell

As previously described, one of the things that one can do when ‘ENTRYPOINT’ is used, is override the actual command that would be run by a container, even when the Dockerfile for the image defined a ‘CMD’ instruction. It was thus possible to run:

> 
>     docker run -it my-python-env bash

This gives us access to an interactive shell to explore the container or run any commands manually.

When we use ‘ENTRYPOINT’ it would appear that we loose this ability.

All is not lost though, it just means we need to handle this a bit differently.

Before I show how that is done, one feature of Docker that is worth pointing out is that it is actually possible to get an interactive shell into an already running container. This is something that originally would have required running ‘sshd’ inside of the container, or required using a mechanism called ’nsenter’. Because this was a common requirement though, Docker has for a while now provided the ‘exec’ command.

What you can therefore do if you already have a running container you want to inspect is run:

> 
>     docker exec -it hungry_bardeen bash

where the name is the auto generated name for the container or one you have assigned when the container was started.

If we don’t already have a running container though, what do we do?

Normally we can supply ‘bash’ as the command and it will work because there is an implicit ‘ENTRYPOINT’ for a container of ‘bash -c’. This is what allows us to specify any command.

In our case the implicit ‘ENTRYPOINT’ has been replaced with ‘mod\_wsgi-docker-start’ and anything we supply on the command line when the container is run will be passed as options to it instead.

The first thing we have to do is work out how we can reset the value of the ‘ENTRYPOINT’ from the command line. Luckily this can be done using the ‘—entrypoint’ command.

So we can try running:

> 
>     docker run -it —entrypoint bash my-python-app

This will have the desired affect of running bash for us, but will generally fail.

The reason it will fail is that any ‘CMD’ defined within the image will be passed to the ‘bash’ command as arguments when run as the entry point.

Trying to wipe out the options specified by ‘CMD’ using:

> 
>     docker run -it —entrypoint bash my-python-app ''

doesn’t help as ‘bash’ will then look for and try to execute a script with an empty name.

To get around this problem and make things a little easier, the image I supply for hosting Python WSGI applications supplies an additional command called ‘mod\_wsgi-docker-shell’. What one would therefore run is:

> 
>     docker run -it —entrypoint mod_wsgi-docker-shell my-python-app

In this case the ‘mod\_wsgi-docker-shell’ script would be run and although what is defined by the ‘CMD’ instruction is still passed as arguments to it, they will ignored and ‘mod\_wsgi-docker-shell’ will ‘exec’ the ‘bash’ command with no arguments.

That therefore is my little backdoor. The only other way I found of getting around the issue, is the non obvious command of:

> 
>     docker run -it —entrypoint nice my-python-app bash

In this case we are relying on the fact that the ‘nice’ command will in turn execute any arguments it is supplied. I thought that ‘mod\_wsgi-docker-shell’ may be more obvious though.

# What is ‘mod\_wsgi-express’?

So what exactly is ‘mod\_wsgi-express’ then? In my next blog I will introduce what ‘mod\_wsgi-express’ is doing.

The ‘mod\_wsgi-express’ program is something that I have been working on for over a year now and has been available since early this year. Although I have commented a bit about it on Twitter, and in a conference talk I did, I haven’t as yet written any blog posts about it. My next blog post will therefore be the first proper public debut of ‘mod\_wsgi-express’ and what it can do.

---

## Comments

### Unknown - December 17, 2014 at 5:17 AM

I wish I had known about mod\_wsgi-docker-shell.   
  
It is especially useful if you're trying to setup the database for the first time such as 'python manage.py syncdb'.

