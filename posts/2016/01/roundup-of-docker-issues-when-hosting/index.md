---
title: "Roundup of Docker issues when hosting IPython."
author: "Graham Dumpleton"
date: "Monday, January 4, 2016"
url: "http://blog.dscpl.com.au/2016/01/roundup-of-docker-issues-when-hosting.html"
post_id: "5905550283187646322"
blog_id: "2363643920942057324"
tags: ['docker', 'ipython', 'openshift', 'python']
images: ['image_46515.png']
comments: 0
published_timestamp: "2016-01-04T15:04:00+11:00"
blog_title: "Graham Dumpleton"
---

Over the last two weeks I have posted a total of six blog posts in a series about what I encountered when attempting to run IPython on Docker. Getting it to run wasn’t straight forward because I wanted to run it in a hosting service which doesn’t permit you to run your application as ‘root' inside of the container.

The reason for not being able to run the application as ‘root’ was because Docker at this time still does not support Linux user namespaces as a main line feature. As such, a hosting service is unable to set up Docker to remap users so that, although you would be running as ‘root’ inside of the container, you would be running as an unprivileged user on the Docker host. For a hosting service, allowing users to run as ‘root’, even if notionally restricted to the context of a container, is too big a risk where you are allowing users to run unknown and untrusted code. 

User namespace support is destined for Docker, but is only an experimental feature at this time. Even so, the initial features being added only allow user ID mapping to be performed at the daemon level. That is, it will not be possible to map user IDs differently for each container.

The inability to map user IDs at the container level will, if the hosting service provides support for persistent data volumes, likely mean that a hosting service using Docker will still not be able to make use of the feature to relax the current restrictions on running as the ‘root’ user. This is because in a multi tenant environment where you have unrelated user’s applications running, you ideally want each user to have a unique user ID range outside of the Docker container. Trying to manage a unique user ID range for each distinct user with only daemon level user ID mapping may well be impractical.

As for Docker being able to map user IDs differently for each container, this is [dependent on changes being made in the Linux kernel](http://integratedcode.us/2015/10/13/user-namespaces-have-arrived-in-docker/). As far as I know there is still no timeframe for when these changes will be ready. The sometimes slow adoption of new kernel versions by Linux variants means that even when the kernel has been updated, it may be some time after that that any new kernel version is generally available.

Although you still may be thinking that since user namespaces will eventually solve all the problems we can ignore the problem of needing to make containers run as a non privileged user, this will only be the case for now if you are only going to run your Docker image on your own infrastructure.

If you intend to run your Docker image on a hosting service, or make it available on Docker Hub registry for others to use, you really should consider updating your Docker image so it doesn’t require being run as the ‘root’ user. By doing so you will be making it usable on the most number of platforms for running Docker images. The need for this is unlikely to change soon.

So right now this is the problem I faced with trying to use IPython. The Docker image for ‘jupyter/notebook’ is designed to be run as ‘root’ and as a result is unusable on a Docker platform which prohibits running as ‘root’, such as is the case for OpenShift.

# Summary of issues encountered

Lets now do a roundup of the posts and the different issues that needed to be addressed in trying to make the IPython image run as an unprivileged user.

  * [Running IPython as a Docker container under OpenShift.](http://blog.dscpl.com.au/2015/12/running-ipython-as-docker-container.html)



> This got everything started. We had no issues with getting ‘ipython/nbviewer’, a static viewer for IPython notebooks, running on OpenShift. In looking at the most obvious candidate image for running a live IPython notebook, that is ‘ipython/ipython’, we found it was actually deprecated and that when we dug into the ‘Dockerfile’ we found it points you towards using ‘jupyter/notebook’. The information available on the Docker Hub Registry for the images is well overdue for an update as coming in via that path it wasn’t at all clear that it shouldn’t be used and what to use instead. Even when using ‘jupyter/notebook’, we found that it fails to run as a non privileged user due to file system permission issues.

  * [Don't run as root inside of Docker containers.](http://blog.dscpl.com.au/2015/12/don-run-as-root-inside-of-docker.html)



> To understand why one should run as a non privileged user in the first place, or why a hosting service may enforce it, we looked next at the dangers of running as the ‘root’ user inside of a Docker container. It was demonstrated how it was quite easy to gain root privileges in the Docker host were an untrusted user allowed to mount arbitrary volumes from the Docker host into a container. Although a hosting service may not expose the Docker API directly, via the ‘docker’ client or otherwise, and hide it behind another tool or user interface, it is still probably wiser not to allow users to run as ‘root’, especially when in nearly all cases it isn’t necessary.

  * [Overriding the user Docker containers run as.](http://blog.dscpl.com.au/2015/12/overriding-user-docker-containers-run-as.html)



> Overriding of the user that a Docker container runs as can be done from a ‘Dockerfile’, or when ‘docker run’ is used to actually start the container. The latter will even override what may be specified in the ‘Dockerfile’. A hosting service may well always override the user the Docker container runs as due to the fact that where the user is specified in the ‘Dockerfile’, if it isn’t specified as an integer user ID, then what that user is cannot be trusted. Where persistent volumes are offered by a hosting service, it may well want to enforce a specific user ID be used due to the current lack of an ability to map user IDs.

  * [Random user IDs when running Docker containers.](http://blog.dscpl.com.au/2015/12/random-user-ids-when-running-docker.html)



> Having the user ID be overridden presented further problems even where the Docker image had been setup to run as a specific non ‘root’ user. This was because the associated group for the user and the corresponding file system permissions that the Docker image was set up for, didn’t allow the user specified when overridden, to write to parts of the file system such as the home directory of the user. It was therefore necessary to override the ‘HOME’ directory in the ‘Dockerfile’ and be quite specific in how the default user account and its corresponding group were setup.

  * [Unknown user when running Docker container.](http://blog.dscpl.com.au/2015/12/unknown-user-when-running-docker.html)



> Although we could fix up things so they would run as a random user ID, a remaining problem was that the user ID didn’t have an actual entry in the system password database. This meant that attempts to look up details for the user would fail. This could cause some applications to give unexpected results or cause a web application to fail. It was necessary to use a user level library, preloaded into programs, for overriding what details were returned when programs looked up user details.

  * [Issues with running as PID 1 in a Docker container.](http://blog.dscpl.com.au/2015/12/issues-with-running-as-pid-1-in-docker.html)



> Not an issue with running on a hosting service which prohibited running as ‘root’, but a further issue which affects the IPython notebook server is that it will fail to start up IPython kernel processes when it is run as process ID ‘1’. To work around this issue it was necessary to use a minimal ‘init’ process as process ID ‘1’, which would in turn start the IPython notebook server, reaping any zombie processes and passing on signals received to the IPython notebook server process.

# Testing your own Python images

Although you yourself may not make use of a hosting service which prohibits the running of Docker containers as ‘root’, you can still test this scenario and whether your Docker images will work when forced to run as an unprivileged user.

To do this all you need to do is override the user the Docker container is run as when you invoke the ‘docker run’ command. Specifically, add the ‘-u’ option to ‘docker run’, giving it a high user ID which doesn’t have a corresponding user ID in the system user database of the Linux installation within the Docker image.

> 
>     docker run --rm -u 10000 -p 8080:8080 my-docker-image

If your application doesn’t run due to file system access permissions, or because it fails in looking for details of a non existent user at some point, you will need to make changes to your Docker image for it to work in this scenario.

In addition to checking whether your Docker image can run as a non privileged user, you should also validate whether the application can stand in properly as the ‘init’ process that would normally run as process ID ‘1’. That is, whether it will reap zombie process properly.

In a prior blog post I showed a Python WSGI application which could be used to test a Python web server. I did it as a Python WSGI application to show that it can happen within the context of an actual Python web application. There is though actually a simpler way which can be used even if you are not using Python.

To test whether whatever process is running inside of the Docker container as process ID ‘1’ is reaping zombie processes properly, all you need to do is use ‘docker exec’ to gain access to the running Docker container and run ‘sleep’ as a background process in a sub shell.

> 
>     $ docker exec -it admiring_lalande bash  
>     > root@cde42f97d683:/app# (sleep 10&)

If after waiting the 10 seconds for the ‘sleep’ to finish, you find a zombie process as child to process ID ‘1’, then whatever you are running as process ID ‘1’ is not reaping child processes correctly.

![Docker container top wsgiref sleep](image_46515.png)

These therefore are two simple tests you can do to make sure your own Docker images can run as a non privileged user and that you will not have issues due to zombie processes. Have issues and you perhaps should look through the prior blog posts as to what changes you need to look at making.