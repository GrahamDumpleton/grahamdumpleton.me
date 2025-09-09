---
title: "What USER should you use to run Docker images."
author: "Graham Dumpleton"
date: "Thursday, December 1, 2016"
url: "http://blog.dscpl.com.au/2016/12/what-user-should-you-use-to-run-docker.html"
post_id: "8440617873661591540"
blog_id: "2363643920942057324"
tags: ['docker', 'kubernetes', 'openshift']
comments: 2
published_timestamp: "2016-12-01T16:38:00+11:00"
blog_title: "Graham Dumpleton"
---

If you follow this blog and my rants on [Twitter](https://twitter.com/GrahamDumpleton) you will know that I often complain about the prevalence of Docker-formatted container images that will only work if run as the root user, even though there is no technical reason to run them as root. With more and more organisations moving towards containers and using these images in production, some at least are realising that running them as root is probably not a good idea after all. As such, organisations are for their own images at least, starting to create basic guidelines for their developers to follow around what user an image should run as.

A typical example of the most basic guidelines you can find are:

  1. Create a new UNIX group called ‘app’ with a group ID \(gid\) of 1001.
  2. Create a new UNIX account with user name ‘app’ with a user ID \(uid\) of 1001, with it being a member of the group ‘app’ and where the home directory of this user is the directory ‘/app’.
  3. Put all your application source code under the ‘/app’ directory.
  4. Set the working directory for any application run to the ‘/app’ directory.
  5. Set the user that the image will run as to the ‘app’ user.



All looks good, and better than running as the root user you might be thinking. Unfortunately there are still a number of problems with these guidelines, as well as things that are missing.

In this blog post I am going to look at the last guideline in that list, and issues around how you specify what user an image should run as. In subsequent posts I will pull apart the other guidelines. At the end of the posts I will summarise what I believe are a better set of basic guidelines around setting up a Docker-formatted container image.

# Skeleton for a Dockerfile

Following the above guidelines, the skeleton for the Dockerfile would look like:

```dockerfile
    FROM centos:centos7

    RUN groupadd --gid 1001 app

    RUN useradd --uid 1001 --gid app --home /app app

    COPY . /app

    WORKDIR /app

    USER app
```

If we build and then run this image and have it start up an interactive shell, we can validate that the command we have run is running as the user ‘app’ and that we are in the correct directory.

```bash
    $ docker run -it --rm best-practices  
    
    [app@ca172749cd4f ~]$ id  
    uid=1001(app) gid=1001(app) groups=1001(app)  
    
    [app@ca172749cd4f ~]$ pwd  
    /app  
    
    [app@ca172749cd4f ~]$ ls -las  
    total 24  
    4 drwx------ 2 app app 4096 Dec 1 03:15 .  
    4 drwxr-xr-x 27 root root 4096 Dec 1 03:15 ..  
    4 -rw-r--r-- 1 app app 18 Aug 2 16:00 .bash_logout  
    4 -rw-r--r-- 1 app app 193 Aug 2 16:00 .bash_profile  
    4 -rw-r--r-- 1 app app 231 Aug 2 16:00 .bashrc  
    4 -rw-r--r-- 1 root root 136 Dec 1 03:15 Dockerfile  
    
    [app@ca172749cd4f ~]$ exit
```

Seems simple enough, so why is this a problem?

# Who do you think you can trust?

The problem is the ‘USER’ statement added to the Dockerfile. This is what declares what user the container should run as.

We can see that this was the last statement in the Dockerfile, and so this should be what user is used when the image is run. That this is the case, can be validated by inspecting the meta data of the Docker-formatted image using the ‘docker inspect’ command:

```bash
    $ docker inspect --format='{{.Config.User}}' best-practices  
    app
```

This means that you could verify that an image satisfies the guideline that it runs as the ‘app’ user and not as the root user, before actually running it.

The problem is this doesn’t actually guarantee anything. This is because the value associated with the ‘.Config.User’ setting is a name. You cannot tell what UNIX user ID this really maps to inside of the container when run.

To illustrate the problem, consider the changed Dockerfile as follows:

```dockerfile
    FROM centos:centos7

    RUN groupadd --gid 1001 app

    RUN useradd --uid 1001 --gid app --home /app app

    RUN sed -i -e 's/1001/0/g' /etc/passwd

    COPY . /app

    WORKDIR /app

    USER app
```

Validating what ‘docker inspect’ says about what user the image will run as we still get the ‘app’ user:

```bash
    $ docker inspect --format='{{.Config.User}}' best-practices  
    app
```

When we do run the actual image though, that isn’t the case in practice.

```bash
    $ docker run -it --rm best-practices  
    
    [root@71150399f77f app]# id  
    uid=0(root) gid=0(root) groups=0(root)
```

So although the Dockerfile specified ‘USER app’ and ‘docker inspect’ also indicated that the image will run as ‘app’, the command actually ran as the root user.

This is because when using a name for ‘USER’, it still needs to be mapped to an actual UNIX user ID by the UNIX passwd file. As shown, we can remap the user name to the user ID ‘0’, meaning it still runs as the root user. We did this surreptitiously to indicate the problem of whether you can actually trust what you see. In this case the command to modify the passwd file was in the Dockerfile and in plain site, but it could also have been buried deep inside some script file or program that had been copied into the Dockerfile and then run during the building of the image.

Why does this matter?

If this is your own system you are running on for your own personal use, then you may not care. It is though a problem in a corporate setting, or if you are running a multi tenant hosting environment where you are allowing Docker-formatted images from potentially untrusted sources. In this case you want to be sure you aren’t going to run an image which actually runs as root. As we have seen, even if ‘USER’ is set in the Dockerfile to be a user other than ‘root’ it doesn’t mean it still isn’t running as root.

# Verifying the user is not root

How then can we be confident that a Docker-formatted image we have been supplied isn’t going to run as root? As we have seen we obviously can’t trust ‘USER’ when it is set to a name, we have to reject any such image and not allow it to be run.

The solution is not to use a name, but the actual UNIX user ID with the ‘USER’ statement. What we therefore would require is that the Dockerfile be written as:

```dockerfile
    FROM centos:centos7

    RUN groupadd --gid 1001 app

    RUN useradd --uid 1001 --gid app --home /app app

    RUN sed -i -e 's/1001/0/g' /etc/passwd

    COPY . /app

    WORKDIR /app

    USER 1001
```

Inspect the image now using ‘docker inspect’ and we get:

```bash
    $ docker inspect --format='{{.Config.User}}' best-practices  
    1001
```

Run the image and we get:

```bash
    $ docker run -it --rm best-practices  
    bash-4.2$ id  
    uid=1001 gid=0(root) groups=0(root)  
    bash-4.2$ ls -las  
    total 36  
    4 drwx------ 2 1001 app 4096 Dec 1 05:10 .  
    4 drwxr-xr-x 28 root root 4096 Dec 1 05:12 ..  
    4 -rw-r--r-- 1 1001 app 18 Aug 2 16:00 .bash_logout  
    4 -rw-r--r-- 1 1001 app 193 Aug 2 16:00 .bash_profile  
    4 -rw-r--r-- 1 1001 app 231 Aug 2 16:00 .bashrc  
    4 -rw-r--r-- 1 root root 177 Dec 1 05:10 Dockerfile
```

Thus by requiring that ‘USER’ be set to a UNIX user ID, we are able to guarantee that it will run as the user it says it is. Even if the supplier of the image had still fiddled with the passwd file it wouldn’t matter, they can’t change the fact it will run as that user ID.

# Recommended Guidelines

What then is a better guideline about what user a Docker-formatted container should be run? I would suggest the following.

```python
Do not run a Docker-formatted container image as the root user. Always override in the Dockerfile what user the image will run as. This should be done by adding the ‘USER’ statement in the Dockerfile. The value of the ‘USER’ statement must be the integer UNIX user ID of the UNIX account you want any application to run as inside of the container. It should not be the user name for the UNIX account.
```

In addition to that guideline for the author of any Docker-formatted container image, I would also add the following guideline for anyone building a system on top of the Docker service for running images.

```python
Where it is intended not to allow images to run as the root user, but you want to allow an image to run as the user it specifies, reject any Docker-formatted container image that you can't verify what UNIX user ID it will run as. Use ‘docker inspect’ to determine the user it should run as. Reject the image and do not run it if the user setting specified in the image meta data, is not an integer value greater than 0.
```

Already you will find some orchestration systems for managing containers using the Docker runtime implement this latter recommendation in certain configurations. One such example is Kubernetes and systems based around it, such as OpenShift. Because of the growth of interest in Kubernetes, especially for enterprise usage and for hosting services, adhering to the first guideline is also the first step in ensuring you will be able to deploy your images to these systems when they are set up in a secure way.

In a followup post I will look at some more aspects around what user an image should run as, whether that be the choice of the developer of the image, or whether it is a user enforced by the hosting service.

---

## Comments

### Unknown - December 5, 2016 at 8:54 AM

This is great. Any idea how to do this from docker-compose?  
  
It seems that in docker-compose you can only specify USER as a string and not a number as required for the UID 1001.

### Graham Dumpleton - December 5, 2016 at 9:39 AM

The user option in docker-compose files relates to what is passed as argument to '-u' option for 'docker run' doesn't it? This is different to what is used in the 'Dockerfile' in as much as docker-compose isn't generating the 'Dockerfile' for you. The '-u' option is just overriding what is defined in the image when run, not changing the image. So as long as 'USER' set correctly in 'Dockerfile', just don't set 'user' for docker-compose.  
  
Either way, I would be surprised if docker-compose doesn't allow you to provide an integer UID to be used with the '-u' option. If it doesn't I would regard that as a bug in docker-compose.

