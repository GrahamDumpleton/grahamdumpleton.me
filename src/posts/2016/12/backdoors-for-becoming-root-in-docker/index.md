---
layout: post
title: "Backdoors for becoming root in a Docker container."
author: "Graham Dumpleton"
date: "2016-12-09"
url: "http://blog.dscpl.com.au/2016/12/backdoors-for-becoming-root-in-docker.html"
post_id: "6615292119161107706"
blog_id: "2363643920942057324"
tags: ['docker']
comments: 2
published_timestamp: "2016-12-09T16:22:00+11:00"
blog_title: "Graham Dumpleton"
---

In my last [post](/posts/2016/12/what-user-should-you-use-to-run-docker/), the main issue I looked at was whether you can trust what a Docker-formatted image says about the user it will run as. What we found was that if the ‘USER’ statement is used in a Dockefile, but is set to a name, you have no idea what UNIX user ID the application in the container will run as. This is because the name could be mapped to any user ID by the UNIX passwd file.

Setting up the UNIX passwd file such that a user name other than ‘root’ also mapped to the UID of 0 provided a backdoor to becoming root in the running container. By requiring that an integer UID be used with the ‘USER’ statement in a Dockerfile, we can inspect the image metadata and decide not to run the image if ‘USER’ wasn’t a non zero integer value.

Is this enough to protect us though? Are there other backdoors for becoming ‘root' in a Docker container. The answer to that is that there is, and this post will look at some of these ways.

# Creating a setuid executable

The primary path for switching from a non privileged user to the ‘root’ user on a UNIX system is a setuid executable. This is an executable that has been blessed in such a way that instead of running as the user that ran it, it runs as the user who is the owner of the executable. Such setuid executables will also work inside of a Docker container.

To illustrate how a setuid executable works, lets look at the UNIX utility called ‘id', which is normally used to display information about what user and group the invoking process runs as. If run normally in our Docker container, we might see:

```
 $ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
```

Lets create a setuid version of the executable which is owned by ‘root' and bundle that in our image.

```
 FROM centos:centos7
 
 
 RUN groupadd --gid 1001 app  
 RUN useradd --uid 1001 --gid app --home /app app
 
 
 RUN cp /usr/bin/id /usr/bin/id-setuid-root  
 RUN chmod 4711 /usr/bin/id-setuid-root
 
 
 WORKDIR /app  
 USER 1001
```

Running the original version of ‘id’ and the setuid version, we get:

```
 $ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
 
 
 $ id-setuid-root  
 uid=1001(app) gid=1001(app) euid=0(root) groups=1001(app)
```

As can be seen, the result is that although the real user ID is the same, the effective user ID is that of the ‘root’ user. This means that by using a setuid executable, we gain the rights to run something as if we are ‘root’, or at least very close to being ‘root’. I say very close to being ‘root’ as it is only the effective user ID which is ‘root’ and not the real user ID. In most cases it doesn’t matter, but it hardly matters anyway, as we could also switch our real identify to the ‘root’ user relatively easily from a custom setuid executable of our own.

# Running programs as 'root'

In the above example we took an existing executable and made it setuid as the ‘root’ user. We can’t go and do this for every executable we want to run as ‘root’, so what do we do if we want to run an arbitrary executable as ‘root’?

You might think that is simple. All we need to do is make a copy of ‘/bin/bash’ and make it setuid as the ‘root’ user. If we can then run that, we can become ‘root’ and run any program we want as the ‘root’ user.

So this time to create the image we use:

```
 FROM centos:centos7
 
 
 RUN groupadd --gid 1001 app  
 RUN useradd --uid 1001 --gid app --home /app app
 
 
 RUN cp /bin/bash /bin/bash-setuid-root  
 RUN chmod 4711 /bin/bash-setuid-root
 
 
 WORKDIR /app  
 USER 1001
```

Running our setuid version of bash though, we don’t get what we expected.

```
 bash-4.2$ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
 
 
 bash-4.2$ bash-setuid-root
 
 
 bash-setuid-root-4.2$ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
```

This doesn’t work because modern implementations of shells have checks builtin which look for the specific case of where they are executed with an effective user ID of ‘root’, but a non ‘root’ real user ID. In this case, just to make it harder to use this sort of backdoor, they will revert back to running as the real user ID for the effective user ID.

Since this doesn’t work, lets look at how we would achieve the same thing if we weren’t trying to use a backdoor.

The first method we would normally use to execute a command as the ‘root’ user when we are not a privileged user, is to use the ‘sudo’ command. An alternative is to use the ‘su’ command to login as the ‘root’ user.

Because in a Docker image we can install and configure anything we want, there is no reason why we can’t just set these up and use them.

```
 FROM centos:centos7
 
 
 RUN yum install -y sudo
 
 
 RUN groupadd --gid 1001 app  
 RUN useradd --uid 1001 --gid app --home /app app
 
 
 # Allow anyone in group 'app' to use 'sudo' without a password.  
 RUN echo '%app ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
 
 
 # Set the password for the 'root' user to be an empty string.  
 RUN echo 'root:' | chpasswd
 
 
 WORKDIR /app  
 USER 1001
```

With this we can very easily get an interactive shell as the ‘root’ user using ’sudo’, not even requiring a password.

```
 $ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
 
 
 $ sudo -s
 
 
 # id  
 uid=0(root) gid=0(root) groups=0(root)
```

We can also just login as the ‘root’ user, supplying our empty password.

```
 $ id  
 uid=1001(app) gid=1001(app) groups=1001(app)
 
 
 $ su root  
 Password:
 
 
 # id  
 uid=0(root) gid=0(root) groups=0(root)
```

In both cases the real user ID is that of the ‘root’ user and not just the effective user ID.

So we didn’t even need to fiddle with a backdoor, we can just use the existing features of the operating system. We just need to install the ‘sudo’ package and configure it, or set the ‘root’ password. As it happens, both these mechanisms rely on a setuid executable, but combine it with configuration to guard against who can access them. It is a simple matter though to enable that access given that during the build of a Docker image you can change anything.

# You can’t completely block 'root'

You might be thinking at this point that if we can become the ‘root’ user in these ways, what is the point then of using a check on what ‘USER’ specified for the image in the first place. Someone can always set it as a non ‘root’ user, using an integer UID to avoid any restriction on using the image, but then use a custom built backdoor marked as a setuid executable, or using existing system tools such as ‘sudo’, or ‘su’.

What is important to understand is that good security is based on having many layers. You don’t rely on just a single security measure to protect your system. Each extra layer you can add, acts as an obstacle to someone reaching their end goal. Not allowing images to run that don’t set ‘USER’ to a non zero integer ID, would be just one step you can take in a overall security plan.

So it isn’t a waste of time just yet. This is because, although there are ways of becoming the ‘root’ user even if ‘USER’ did not originally declare the container should run as ‘root’, we can still control what the ‘root’ user is actually able to do. This is achieved using Linux capabilities, and is the next layer of defence you should employ.

In the next blog post I will look at Linux capabilities and how to use Docker to restrict what someone could do even if they become the ‘root’ user.

---

## Comments

### JustAQuestion - February 22, 2017 at 2:21 AM

Hello,  
  
Not related to this blog, but related to debugging to debugging. I tried folowing modwsgi doc, but not successful, getting these error messages  
  
ArgsAlreadyParsedError: arguments already parsed: cannot register CLI option  
  
I couldnt find another avenue to reach out to you. Please let me know if there is a e-mail that can be used.  
  
running httpd -X and embedded mode to get to pdb shell  
  
wsgi-keystone.conf is  
  
WSGIProcessGroup %\{GLOBAL\}  
  
removed this line:WSGIDaemonProcess keystone-public processes=5 threads=1 user=keystone group=keystone  
  
Thanks,  
Ashok

### Graham Dumpleton - February 22, 2017 at 10:28 AM

For mod\_wsgi questions use the mod\_wsgi mailing list. Details at:  
  
http://modwsgi.readthedocs.io/en/develop/finding-help.html

