---
title: "Overriding the user Docker containers run as."
author: "Graham Dumpleton"
date: "Tuesday, December 22, 2015"
url: "http://blog.dscpl.com.au/2015/12/overriding-user-docker-containers-run-as.html"
post_id: "2831100265299827336"
blog_id: "2363643920942057324"
tags: ['docker', 'ipython', 'openshift', 'python']
comments: 0
published_timestamp: "2015-12-22T07:11:00+11:00"
blog_title: "Graham Dumpleton"
---

In the [first post](/posts/2015/12/running-ipython-as-docker-container/) of this series looking at how to get IPython running on OpenShift I showed how taking the ‘jupyter/notebook’ Docker image and trying to use it results in failure. The error we encountered was:

```bash
    $ oc logs --previous notebook-1-718ce  
    /usr/local/lib/python3.4/dist-packages/IPython/paths.py:69: UserWarning: IPython parent '/' is not a writable location, using a temp directory.  
    " using a temp directory.".format(parent))  
    Traceback (most recent call last):  
    ...

    File "/usr/lib/python3.4/os.py", line 237, in makedirs  
    mkdir(name, mode)  
    PermissionError: [Errno 13] Permission denied: '/.jupyter'
```

The problem occurred because the ‘jupyter/notebook’ expects to run as the ‘root’ user, but OpenShift doesn’t permit that by default due to the increased security risks from allowing that with how Docker currently works.

Changes are supposedly coming for Docker, in the way of support for user namespaces, which would reduce the security risks, but right now, and perhaps even when support for user namespaces is available, it is simply better that you [do not run Docker containers as ‘root’](/posts/2015/12/don-run-as-root-inside-of-docker/).

Lets now dig more into the ways that a Docker container can be made to not run as the ‘root’ user.

# Specifying the user in the Dockerfile

If you are building a Docker image yourself, you can specify that it should run as a particular user by including the ‘USER’ statement in the ‘Dockerfile’. Normally you would place this towards the end of the ‘Dockerfile’ so that prior ‘RUN’ steps within the ‘Dockerfile' can still run with the default ‘root’ privileges. 

Unfortunately many images do not close out the ‘Dockerfile’ by specifying a ‘USER’ statement for a non ‘root’ user. This is either done through ignorance that one shouldn’t really run Docker containers as ‘root’ unless you genuinely have a need to, or because they anticipate that the Docker image may later possibly be used as a base image and so perhaps don’t want to make it too difficult for it to be used in that way.

Specifically, if the base image were finished up with a ‘USER’ statement for a non ‘root’ user, when creating a derived image the first thing that anyone would need to do if they wanted to make system changes would be to use ‘USER root’ to switch back to being the ‘root’ user.

One can easily see how people might think this is annoying though and so not specify the ‘USER’ in the base image. Problem is that your typical users of the base image are even less likely to understand the consequences of running as ‘root’ and why you shouldn’t and so aren’t going to revert to a non ‘root’ user in their derived image either if you haven’t provided some pointer to what best practice is.

# What user to run a container as

So if it is better to run as a non ‘root’ user, what user should that be?

The simplest course one might choose is to look at what system users an operating system pre defines in the ‘/etc/passwd’ file.

On the ‘busybox’ image, if we do that we find:

```javascript
    root:x:0:0:root:/root:/bin/sh  
    daemon:x:1:1:daemon:/usr/sbin:/bin/false  
    bin:x:2:2:bin:/bin:/bin/false  
    sys:x:3:3:sys:/dev:/bin/false  
    sync:x:4:100:sync:/bin:/bin/sync  
    mail:x:8:8:mail:/var/spool/mail:/bin/false  
    www-data:x:33:33:www-data:/var/www:/bin/false  
    operator:x:37:37:Operator:/var:/bin/false  
    ftp:x:83:83:ftp:/home/ftp:/bin/false  
    nobody:x:99:99:nobody:/home:/bin/false
```

Of these the ‘www-data’ user looks like a good candidate, this being the user that would normally be used by a web server such as Apache. The ‘www-data’ user is also typically present on all Linux operating system variants.

The problem with the ‘www-data’ user is that although the ‘/etc/passwd’ file usually defines a home directory, that home directory, depending on the Linux operating system variant, may not actually exist.

For example, on ‘busybox’ the home directory of ‘/var/www’ does exist, but on a Debian based image it may not.

```bash
    $ docker run --rm -it busybox sh  
    / # echo ~www-data  
    /var/www  
    / # touch ~www-data/magic  
    / # exit

    $ docker run --rm -it debian:jessie sh  
    # echo ~www-data  
    /var/www  
    # touch ~www-data/magic  
    touch: cannot touch '/var/www/magic': No such file or directory
```

The lack of a home directory means that even if we update the IPython Docker image to run as the ‘www-data’ user, it will still fail on startup.

```javascript
    /usr/local/lib/python3.4/dist-packages/IPython/paths.py:69: UserWarning: IPython parent '/var/www' is not a writable location, using a temp directory.  
    " using a temp directory.".format(parent))  
    Traceback (most recent call last):  
    ...  
    File "/usr/lib/python3.4/os.py", line 237, in makedirs  
    mkdir(name, mode)  
    PermissionError: [Errno 13] Permission denied: '/var/www'
```

What happened this time is that since the home directory didn’t even exist, the Python code for the application tried to create it. The user ‘www-data’ didn’t though have permissions to create a directory under ‘/var’.

More typically application code trying to write files to a home directory would assume that the home directory at least would exist, so instead it would fail when trying to create a file or subdirectory under the non existent home directory. It is unusual that the application code in this case tried to create the home directory first.

# Adding of a new user account

One could with the ‘www-data’ account simply ensure that a home directory does exist and create it with the appropriate permissions, but at that point it is probably easier and better to add a new user account to the system specifically to be used by the container when it is run.

The exact command you use to add a new user account is going to depend on the Linux operating system variant being used. If using a Debian based system you would use ‘adduser’. If using Red Hat you would use ‘useradd’.

The IPython Docker image for ‘jupyter/notebook’ is derived from Ubuntu and so is Debian based. To create a special user account called ‘ipython’ we would therefore use:

```
    adduser --disabled-password --gecos "IPython" ipython
```

The ‘--disabled-password’ option ensures that the ‘adduser’ command doesn’t attempt to prompt for a user password.

Having added our own user account, what changes would we need to make to the ‘Dockerfile’ for the ‘jupyter/notebook’ Docker image to have it use this?

Looking through it the bulk of the commands in the ‘Dockerfile’ relate to installing system or Python packages. It is only where we get to the end of the ‘Dockerfile’ that we come across anything that potentially needs to change.

```dockerfile
    # Add a notebook profile.  
    RUN mkdir -p -m 700 /root/.jupyter/ && \  
    echo "c.NotebookApp.ip = '*'" >> /root/.jupyter/jupyter_notebook_config.py

    VOLUME /notebooks  
    WORKDIR /notebooks

    EXPOSE 8888

    ENTRYPOINT ["tini", "--"]  
    CMD ["jupyter", "notebook"]
```

The first command here is creating a ‘.jupyter’ sub directory in what would be the home directory for the user, and adding to it a user configuration file for the Jupyter Notebook application. As it stands here, it is assuming that the user will be ‘root’, but we don’t want it to run as ‘root’ but the ‘ipython’ user we have created.

When we used the ‘adduser’ command it automatically created a home directory for the ‘ipython’ user at ‘/home/ipython’. We therefore need to use the home directory for the ‘ipython’ user instead of ‘/root’, which was the home directory for the ‘root’ user.

```dockerfile
    # Add a notebook profile.  
    RUN mkdir -p -m 700 ~ipython/.jupyter/ && \  
    echo "c.NotebookApp.ip = '*'" >> ~ipython/.jupyter/jupyter_notebook_config.py && \  
    chown -R ipython:ipython ~ipython/.jupyter
```

Also note that since commands are being run as root at this point in the ‘Dockerfile’, we also need to change the ownership on the ‘.jupyter’ subdirectory and the file created inside so they are owned by the ‘ipython’ user. If we do not do this and the IPython Notebook application wants to create additional files in that directory, it will fail, as the directory and files would still be owned by the ‘root’ user.

For good measure and to be consistent with normal permissions one would find on directories and files created by a user, we also ensure that the group is updated to also be that corresponding to the ‘ipython’ user.

Directory permissions also become an issue with the ‘/notebooks’ directory. This is the directory which is setup as the working directory for the IPython Notebook application and which will be where any IPython notebooks will be created.

The ‘/notebooks’ directory is actually created as a side effect of the ‘VOLUME ‘ statement. A directory created in that way will also be created with ‘root’ as the owner. We therefore need to manually create the ‘/notebooks’ directory ourselves and set the permissions appropriately, before marking it as being a volume mount point.

```dockerfile
    RUN mkdir /notebooks && chown ipython:ipython /notebooks
```

Finally, we can use the ‘USER’ statement to mark that the Docker container when run should be run as the ‘ipython’ user. The final result we end up with is:

```dockerfile
    # Add a notebook profile.  
    RUN mkdir -p -m 700 ~ipython/.jupyter/ && \  
    echo "c.NotebookApp.ip = '*'" >> ~ipython/.jupyter/jupyter_notebook_config.py && \  
    chown -R ipython:ipython ~ipython/.jupyter

    RUN mkdir /notebooks && chown ipython:ipython /notebooks

    VOLUME /notebooks  
    WORKDIR /notebooks

    EXPOSE 8888

    USER ipython

    ENTRYPOINT ["tini", "--"]  
    CMD ["jupyter", "notebook"]
```

Running the Docker image after having made these changes and executing an interactive shell within the container, we can check the environment to see if it is what we expect.

```bash
    ipython@f4665e7d63b7:/notebooks$ whoami  
    ipython  
    ipython@f4665e7d63b7:/notebooks$ id  
    uid=1000(ipython) gid=1000(ipython) groups=1000(ipython)  
    ipython@f4665e7d63b7:/notebooks$ pwd  
    /notebooks  
    ipython@f4665e7d63b7:/notebooks$ env | grep HOME  
    HOME=/home/ipython  
    ipython@f4665e7d63b7:/notebooks$ ls -las  
    total 8  
    4 drwxr-xr-x 2 ipython ipython 4096 Dec 21 03:54 .  
    4 drwxr-xr-x 58 root root 4096 Dec 21 03:54 ..
```

All looks good and from the web interface for the IPython Notebook application we can create and save notebooks.

Alas, even though we have now converted the IPython Docker image to not run as ‘root', it still will not run on OpenShift, again yielding an error message in the log output.

```bash
    $ oc logs --previous ipython-2-yo557  
    /usr/local/lib/python3.4/dist-packages/IPython/paths.py:69: UserWarning: IPython parent '/' is not a writable location, using a temp directory.  
    " using a temp directory.".format(parent))  
    Traceback (most recent call last):  
    ...  
    File "/usr/lib/python3.4/os.py", line 237, in makedirs  
    mkdir(name, mode)  
    PermissionError: [Errno 13] Permission denied: '/.jupyter'
```

# Why the user ID is overridden

The reason that the updated Docker image failed on OpenShift is that even though a ‘USER’ statement was included to indicate that a specific non ‘root’ user should be used to run the Docker image, this was still ignored.

When we look at a hosting service which wants to prohibit Docker images from running as ‘root’, there are a couple of issues that come into play in respect of what user ID a Docker image is allowed to run as, or forced to run as.

The first issue is what the ‘USER’ was actually set to, which any hosting service can determine by inspecting the Docker image to be deployed.

```bash
    $ docker inspect --format='{{.ContainerConfig.User}}’ jupyter/notebook  
    ipython
```

In our updated Docker image you can see that when inspecting the image it has been setup to run as the ‘ipython’ user.

The problem with this is that because a user name was supplied, it is not actually possible for the hosting service to readily determine what user ID that user name maps to.

Although you might think that so long as it doesn’t have ‘root’ you are good, that isn’t the case. This is because there is nothing to stop someone constructing a Docker image which has a ‘/etc/passwd’ file containing:

```
    ipython:x:0:0:root:/root:/bin/sh
```

In short, a hosting service cannot trust the user configured into a Docker image if it is not an integer user ID.

In order to try and ensure that a hosting service will actually run a Docker image as the ‘USER’ you defined, at the least, you need to provide an integer user ID for ‘USER’ and not a user name.

Unfortunately, this will probably still only work for a hosting service which only supports 12 factor applications and does not offer any persistent storage.

The second issue here now as to why the ‘USER’ would be ignored being around whether persistent storage is being offered.

The problem here is that for extra security, when providing persistent data storage volumes to applications, you do not really want the storage volumes for every user using the same user ID. As a result, where persistent storage is being offered, a separate user ID will generally be given to each user, or possibly to each project.

This is the case with OpenShift, where applications running under distinct projects, even for the same OpenShift user, are allocated different user IDs that any Docker images are then run as.

As a result, no matter what you set ‘USER’ to in the ‘Dockerfile’, OpenShift will instead force the Docker container to run as the user ID that was allocated to the project the Docker container is run in, this being to allow for better security when persistent volumes or other external resources are being used.

Now before you start thinking this is a limitation with just OpenShift, it isn’t. Any hosting service that wants to use best practice, including not running Docker images as ‘root’ and of providing applications running in different contexts with different user identities for when accessing external resources will be in the same boat.

This situation will likely only change when user namespace support is added to Docker and hosting services can transparently map any user ID within the container, to a distinct user ID outside of the container, of the hosting services choosing.

# How the user ID is overridden

So how does OpenShift override the ‘USER’ which a Docker image is configured with?

Overriding of the user that a Docker container is marked to run as, can be done by using the ‘-u’ option to ‘docker run’.

Without even using OpenShift we can therefore very quickly see if a Docker image might fail to start up where the user is being overridden by any hosting service. All we need to do is pick some random user ID which doesn’t have a corresponding user account inside of the Docker container.

Doing this for our IPython Docker image we get as we did before:

```bash
    $ docker run --rm -u 100000 -p 8888:8888 jupyter-notebook  
    /usr/local/lib/python3.4/dist-packages/IPython/paths.py:69: UserWarning: IPython parent '/' is not a writable location, using a temp directory.  
    " using a temp directory.".format(parent))  
    Traceback (most recent call last):  
    ...  
    File "/usr/lib/python3.4/os.py", line 237, in makedirs  
    mkdir(name, mode)  
    PermissionError: [Errno 13] Permission denied: '/.jupyter'
```

# Randomly assigned user ID

So the fact that the IPython Docker image was setup to run as ‘root’ wasn’t the only problem. As shown, even when we change the ‘Dockerfile’ to have the Jupyter Notebook application run as a non ‘root’ user, it would still fail to start up.

This was because even when configured to run as a non ‘root’ user, that was ignored and a random user ID was being allocated and used to run the Docker container.

The primary issue that arises from this is that there is not going to be a user account defined within the container corresponding to the user ID which is used. Further, because the user ID which is used is not going to be known in advance, it isn’t possible to add into the image at the time it is built a user account with that user ID.

The flow on consequences of this were that the ‘HOME’ directory environment variable is going to default back to being ‘/‘. The application wants to be able to write files to the home directory though and since that wasn’t the directory it was expected to be, it failed.

In addition, if our Docker image had been constructed such that the intended ‘USER’ the Docker image were to run as had special access to write to other parts of the file system, the random user ID wouldn’t be able to right to those either.

This can be seen when we override the command that is run when starting the Docker container to get access to an interactive shell and running some manual checks.

```python
    $ docker run --rm -it -u 100000 -p 8888:8888 jupyter-notebook bash  
    I have no name!@78bdfa8dba92:/notebooks$ whoami  
    whoami: cannot find name for user ID 100000  
    I have no name!@78bdfa8dba92:/notebooks$ id  
    uid=100000 gid=0(root)  
    I have no name!@78bdfa8dba92:/notebooks$ pwd  
    /notebooks  
    I have no name!@78bdfa8dba92:/notebooks$ env | grep HOME  
    HOME=/  
    I have no name!@78bdfa8dba92:/notebooks$ touch $HOME/magic  
    touch: cannot touch ‘//magic’: Permission denied  
    I have no name!@78bdfa8dba92:/notebooks$ touch /notebooks/magic  
    touch: cannot touch ‘/notebooks/magic’: Permission denied
```

We still therefore have some work to do before we can get this working.

In the next post I will start going into how to accomodate a Docker container running as a random user ID which you aren’t going to know of in advance.