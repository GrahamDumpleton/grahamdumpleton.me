---
title: "Unknown user when running Docker container."
author: "Graham Dumpleton"
date: "Thursday, December 24, 2015"
url: "http://blog.dscpl.com.au/2015/12/unknown-user-when-running-docker.html"
post_id: "6613553346694572403"
blog_id: "2363643920942057324"
tags: ['docker', 'ipython', 'openshift', 'python']
comments: 3
published_timestamp: "2015-12-24T22:19:00+11:00"
blog_title: "Graham Dumpleton"
---

In the [last post](http://blog.dscpl.com.au/2015/12/random-user-ids-when-running-docker.html) we covered how to setup a Docker image to cope with the prospect of a random user ID being used when the Docker container was started. The discussion so far has though only dealt with the issue of ensuring file system access permissions were set correctly to allow the original default user, as well as the random user ID being used, to update files.

A remaining issue of concern was the fact that when a random user ID is used which doesn’t correspond to an actual user account, that UNIX tools such as ‘whoami’ will not return valid results.

> 
>     I have no name!@5a72c002aefb:/notebooks$ whoami  
>     > whoami: cannot find name for user ID 10000

Up to this point this didn’t actually appear to prevent our IPython Notebook application working, but it does leave the prospect that subtle problems could arise when we start actually using IPython to do more serious work.

Lets dig in and see what this failure equates to in the context of a Python application.

# Accessing user information

If we are writing Python code, there are a couple of ways using the Python standard library that we could determine the login name for the current user.

The first way is to use the ‘getuser\(\)’ function found in the ‘getpass’ module.

> 
>     import getpass  
>     > name = getpass.getuser()

If we use this from an IPython notebook when a random user ID has been assigned to the Docker container, like how ‘whoami’ fails, this will also fail.

> 
>     ---------------------------------------------------------------------------  
>     > KeyError                                  Traceback (most recent call last)  
>     > <ipython-input-3-3a0a5fbe1d4e> in <module>()  
>     >       1 import getpass  
>     > ----> 2 name = getpass.getuser()
>     
>     
>     /usr/lib/python2.7/getpass.pyc in getuser()  
>     >     156 # If this fails, the exception will "explain" why  
>     >     157 import pwd  
>     > --> 158 return pwd.getpwuid(os.getuid())[0]  
>     >     159   
>     >     160 # Bind the name getpass to the appropriate function
>     
>     
>     KeyError: 'getpwuid(): uid not found: 10000'

The error details and traceback displayed here actually indicate the second way of getting access to the login name. In fact the ‘getuser\(\)’ function is just a high level wrapper around a lower level function for accessing user information from the system user database.

We could therefore also have written:

> 
>     import pwd, os  
>     > name = pwd.getpwuid(os.getuid())[0]

Or being more verbose to make it more obvious what is going on:

> 
>     import pwd, os  
>     > name = pwd.getpwuid(os.getuid()).pw_name

Either way, this is still going to fail where the current user ID doesn’t match a valid user in the system user database.

# Environment variable overrides

You may be thinking, why bother with the ‘getuser\(\)’ function if one could use ‘pwd.getpwuid\(\)’ directly. Well it turns out that ‘getuser\(\)’ does a bit more than just act as a proxy for calling ‘pwd.getpwuid\(\)’. What it actually does is first consult various environment variables which identify the login name for the current user.

> 
>     def getuser():  
>     >     """Get the username from the environment or password database.
>     
>     
>         First try various environment variables, then the password  
>     >     database. This works on Windows as long as USERNAME is set.
>     
>     
>         """
>     
>     
>         import os
>     
>     
>         for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):  
>     >         user = os.environ.get(name)  
>     >         if user:  
>     >             return user
>     
>     
>         # If this fails, the exception will "explain" why  
>     >     import pwd  
>     >     return pwd.getpwuid(os.getuid())[0]

These environment variables such as ‘LOGNAME’ and ‘USER’ would normally be set by the login shell for a user. When using Docker though, a login shell isn’t used and so they are not set.

For the ‘getuser\(\)’ function at least, we can therefore get it working by ensuring that as part of the Docker image build, we set one or more of these environment variables. Typically both the ‘LOGNAME’ and ‘USER’ environment variables are set, so lets do that.

> 
>     ENV LOGNAME=ipython  
>     > ENV USER=ipython 

Rebuilding our Docker image with this addition to the ‘Dockerfile’ and trying ‘getuser\(\)’ again from within a IPython Notebook and it does indeed now work.

# Overriding user system wide

This change may help allow more code to execute without problems, but if code directly accesses the system user database using ‘pwd.getpwuid\(\)’, if it doesn’t catch the ‘KeyError’ exception and handle missing user information you will still have problems.

So although this is still a worthwhile change in its own right, just in case something may want to consult ‘LOGNAME’ and ‘USER’ environment variables which would normally be set by the login shell, such as ‘getuser\(\)’, it does not help with ‘pwd.getpwuid\(\)’ nor UNIX tools such as ‘whoami’.

To be able to implement a solution for this wider use case gets a bit more tricky as we need to solve the issue for UNIX tools, or for that matter, any C level application code which uses the ‘getpwuid\(\)’ function in the system C libraries.

The only way one can achieve this though is through substituting the system C libraries, or at least overriding the behaviour of key C library functions. This may sound impossible but by using a Linux capability to forcibly preload a shared library into executing processes it is actually possible and someone has even written a package we can use for this purpose.

# The nss\_wrapper library

The package in question is one called ‘[nss\_wrapper](https://cwrap.org/nss_wrapper.html)'. The library provides a wrapper for the user, group and hosts NSS API. Using nss\_wrapper it is possible to define your own ‘passwd' and ‘group' files which will then be consulted when needing to lookup user information.

One way in which this package is normally used is when doing testing and you need to run applications using a dynamic set of users and you don’t want to have to create real user accounts for them. This mirrors the situation we have where when using a random user ID we will not actually have a real user account.

The idea behind the library is that prior to starting up your application you would make copies of the system user and group database files and then edit any existing entries or add additional users as necessary. When starting your application you would then force it to preload a shared library which overrides the NSS API functions in the standard system libraries such that they consult the copies of the user and group database files.

The general steps therefore are something like:

> 
>     ipython@3d0c5ea773a3:/tmp$ whoami  
>     > ipython
>     
>     
>     ipython@3d0c5ea773a3:/tmp$ id  
>     > uid=1001(ipython) gid=0(root) groups=0(root)
>     
>     
>     ipython@3d0c5ea773a3:/tmp$ echo "magic:x:1001:0:magic gecos:/home/ipython:/bin/bash" > passwd
>     
>     
>     ipython@3d0c5ea773a3:/tmp$ LD_PRELOAD=/usr/local/lib64/libnss_wrapper.so NSS_WRAPPER_PASSWD=passwd NSS_WRAPPER_GROUP=/etc/group id  
>     > uid=1001(magic) gid=0(root) groups=0(root)
>     
>     
>     ipython@3d0c5ea773a3:/tmp$ LD_PRELOAD=/usr/local/lib64/libnss_wrapper.so NSS_WRAPPER_PASSWD=passwd NSS_WRAPPER_GROUP=/etc/group whoami  
>     > magic

To integrate the use of the ‘nss\_wrapper’ package we need to do two things. The first is install the package and the second is to add a Docker entrypoint script which can generate a modified password database file and then ensure that the ‘libnss\_wrapper.so’ shared library is forcibly preloaded for all processes subsequently run.

# Installing the nss\_wrapper library

At this point in time the ‘nss\_wrapper’ library is not available in the stable Debian package repository, still only being available in the testing repository. As we do not want in general to be pulling packages from the Debian testing repository, we are going to have to install the ’nss\_wrapper’ library from source code ourselves.

To be able to do this, we need to ensure that the system packages for ‘make’ and ‘cmake’ are available. We therefore need to add these to the list of system packages being installed.

> 
>     # Python binary and source dependencies  
>     > RUN apt-get update -qq && \  
>     >  DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \  
>     >  build-essential \  
>     >  ca-certificates \  
>     >  cmake \  
>     >  curl \  
>     >  git \  
>     >  make \  
>     >  language-pack-en \  
>     >  libcurl4-openssl-dev \  
>     >  libffi-dev \  
>     >  libsqlite3-dev \  
>     >  libzmq3-dev \  
>     >  pandoc \  
>     >  python \  
>     >  python3 \  
>     >  python-dev \  
>     >  python3-dev \  
>     >  sqlite3 \  
>     >  texlive-fonts-recommended \  
>     >  texlive-latex-base \  
>     >  texlive-latex-extra \  
>     >  zlib1g-dev && \  
>     >  apt-get clean && \  
>     >  rm -rf /var/lib/apt/lists/*

We can then later on download the source package for ‘nss\_wrapper’ and install it.

> 
>     # Install nss_wrapper.  
>     > RUN curl -SL -o nss_wrapper.tar.gz https://ftp.samba.org/pub/cwrap/nss_wrapper-1.1.2.tar.gz && \  
>     >  mkdir nss_wrapper && \  
>     >  tar -xC nss_wrapper --strip-components=1 -f nss_wrapper.tar.gz && \  
>     >  rm nss_wrapper.tar.gz && \  
>     >  mkdir nss_wrapper/obj && \  
>     >  (cd nss_wrapper/obj && \  
>     >  cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DLIB_SUFFIX=64 .. && \  
>     >  make && \  
>     >  make install) && \  
>     >  rm -rf nss_wrapper

# Updating the Docker entrypoint

At present the Docker ‘ENTRYPOINT’ and ‘CMD’ are specified in the ‘Dockerfile’ as:

> 
>     ENTRYPOINT [“tini”, “--"]  
>     > CMD ["jupyter", "notebook"]

The ‘CMD’ statement in this case is the actual command we want to run to start the Jupyter Notebook application.

We haven’t said anything about what the ‘tini’ program specified by the ‘ENTRYPOINT' is all about as yet, but it is actually quite important. If you do not use ‘tini’ as a wrapper for IPython Notebook then it will not work properly. We will cover what ‘tini’ is and why it is necessary for running IPython Notebook in a subsequent post.

Now because we do require ‘tini’, but we now also want to do some other work prior to actually running the ‘jupyter notebook’ command, we are going to substitute an entrypoint script in place of ‘tini’. We will call this ‘entrypoint.sh’, make it executable, and place it in the top level directory of the repository. After its copied into place, the ‘ENTRYPOINT’ specified in the ‘Dockerfile’ will then need to be:

> 
>     ENTRYPOINT ["/usr/src/jupyter-notebook/entrypoint.sh"]

The actual ‘entrypoint.sh’ we will specify as:

> 
>     #!/bin/sh
>     
>     
>     # Override user ID lookup to cope with being randomly assigned IDs using  
>     > # the -u option to 'docker run'.
>     
>     
>     USER_ID=$(id -u)
>     
>     
>     if [ x"$USER_ID" != x"0" -a x"$USER_ID" != x"1001" ]; then  
>     >     NSS_WRAPPER_PASSWD=/tmp/passwd.nss_wrapper  
>     >     NSS_WRAPPER_GROUP=/etc/group
>     
>     
>         cat /etc/passwd | sed -e ’s/^ipython:/builder:/' > $NSS_WRAPPER_PASSWD
>     
>     
>         echo "ipython:x:$USER_ID:0:IPython,,,:/home/ipython:/bin/bash" >> $NSS_WRAPPER_PASSWD
>     
>     
>         export NSS_WRAPPER_PASSWD  
>     >     export NSS_WRAPPER_GROUP
>     
>     
>         LD_PRELOAD=/usr/local/lib64/libnss_wrapper.so  
>     >     export LD_PRELOAD  
>     > fi
>     
>     
>     exec tini -- "$@"

Note that we still execute ‘tini’ as the last step. We do this using ‘exec’ so that its process will replace the entrypoint script and take over as process ID 1, ensuring that signals get propagated properly, as well as to ensure some details related to process management are handled correctly. We will also pass on all command line arguments given to the entrypoint script to ‘tini’. The double quotes around the arguments reference ensure that argument quoting is handled properly when passing through arguments.

What is now new compared to what was being done before is the enabling of the ‘nss\_wrapper’ library. We do not do this though when we are running as ‘root’, were that is that the Docker image was still forced to run as ‘root’ even though the aim is that it run as a non ‘root’ user. We also do not need to do it when we are run with the default user ID.

When run as a random user ID we do two things with the password database file that we will use with ‘nss\_wrapper’.

The first is that we change the login name corresponding to the existing user ID of ‘1001’. This is the default ‘ipython’ user account we created previously. We do this by simply replacing the ‘ipython’ login name in the password file when we copy it, with the name ‘builder’ instead.

The second is that we add a new password database file entry corresponding to the current user ID, that being whatever is the random user ID allocated to run the Docker container. In this case we use the login name of ‘ipython’.

The reason for swapping the login names so the current user ID uses ‘ipython’ rather than the original user ID of ‘1001’, is so that the application when run will still think it is the ‘ipython’ user. What we therefore end up with in our copy of the password database file is:

> 
>     docker run -it --rm -u 10000 -p 8888:8888 jupyter-notebook bash  
>     > ipython@0ff73693d433:/notebooks$ tail -2 /tmp/passwd.nss_wrapper  
>     > builder:x:1001:0:IPython,,,:/home/ipython:/bin/bash  
>     > ipython:x:10000:0:IPython,,,:/home/ipython:/bin/bash

Immediately you can already see that the shell prompt now looks correct. Going back and running our checks from before, we now see:

> 
>     ipython@0ff73693d433:/notebooks$ whoami  
>     > ipython  
>     > ipython@0ff73693d433:/notebooks$ id  
>     > uid=10000(ipython) gid=0(root) groups=0(root)  
>     > ipython@0ff73693d433:/notebooks$ env | grep HOME  
>     > HOME=/home/ipython  
>     > ipython@0ff73693d433:/notebooks$ touch $HOME/magic  
>     > ipython@0ff73693d433:/notebooks$ touch /notebooks/magic  
>     > ipython@0ff73693d433:/notebooks$ ls -las $HOME  
>     > total 24  
>     > 4 drwxrwxr-x 4 builder root 4096 Dec 24 10:22 .  
>     > 4 drwxr-xr-x 6 root root 4096 Dec 24 10:22 ..  
>     > 4 -rw-rw-r-- 1 builder root 220 Dec 24 10:08 .bash_logout  
>     > 4 -rw-rw-r-- 1 builder root 3637 Dec 24 10:08 .bashrc  
>     > 4 drwxrwxr-x 2 builder root 4096 Dec 24 10:08 .jupyter  
>     > 0 -rw-r--r-- 1 ipython root 0 Dec 24 10:22 magic  
>     > 4 -rw-rw-r-- 1 builder root 675 Dec 24 10:08 .profile

So even though the random user ID didn’t have an entry in the original system password database file, by using ‘nss\_wrapper’ we can trick any applications to use our modified password database file for user information. This means we can dynamically generate a valid password database file entry for the random user ID which was used.

With the way we swapped the login name for the default user ID of ‘1001’, with the random user ID, as far as any application is concerned it is still running as the ‘ipython’ user.

So we can distinguish, any files that were created during the image build as the original ‘ipython’ user will now instead show as being owned by ‘builder’, which if we look it up maps to user ID of ‘1001’.

> 
>     ipython@0ff73693d433:/notebooks$ id builder  
>     > uid=1001(builder) gid=0(root) groups=0(root)  
>     > ipython@0ff73693d433:/notebooks$ getent passwd builder  
>     > builder:x:1001:0:IPython,,,:/home/ipython:/bin/bash

# Running as another name user

Not that there strictly should be a reason for doing so, but it is possible to also force the Docker container to run as some other user ID with an entry in the password database file, but because they have their own distinct primary group assignments, you do have to override the group to be ‘0’ so that it can update any required directories.

> 
>     $ docker run -it --rm -u 5 -p 8888:8888 jupyter-notebook bash  
>     > games@36ec17b1d9c1:/notebooks$ whoami  
>     > games  
>     > games@36ec17b1d9c1:/notebooks$ id  
>     > uid=5(games) gid=60(games) groups=60(games)  
>     > games@36ec17b1d9c1:/notebooks$ env | grep HOME  
>     > HOME=/home/ipython  
>     > games@36ec17b1d9c1:/notebooks$ touch $HOME/magic  
>     > touch: cannot touch ‘/home/ipython/magic’: Permission denied  
>     > games@36ec17b1d9c1:/notebooks$ touch /notebooks/magic  
>     > touch: cannot touch ‘/notebooks/magic’: Permission denied  
>     >   
>     > $ docker run -it --rm -u 5:0 -p 8888:8888 jupyter-notebook bash  
>     > games@e2ecabedab47:/notebooks$ whoami  
>     > games  
>     > games@e2ecabedab47:/notebooks$ id  
>     > uid=5(games) gid=0(root) groups=60(games)  
>     > games@e2ecabedab47:/notebooks$ env | grep HOME  
>     > HOME=/home/ipython  
>     > games@e2ecabedab47:/notebooks$ touch $HOME/magic  
>     > games@e2ecabedab47:/notebooks$ touch /notebooks/magic  
>     > games@e2ecabedab47:/notebooks$ ls -las $HOME  
>     > total 24  
>     > 4 drwxrwxr-x 4 builder root 4096 Dec 24 10:41 .  
>     > 4 drwxr-xr-x 6 root root 4096 Dec 24 10:41 ..  
>     > 4 -rw-rw-r-- 1 builder root 220 Dec 24 10:39 .bash_logout  
>     > 4 -rw-rw-r-- 1 builder root 3637 Dec 24 10:39 .bashrc  
>     > 4 drwxrwxr-x 2 builder root 4096 Dec 24 10:39 .jupyter  
>     > 0 -rw-r--r-- 1 games root 0 Dec 24 10:41 magic  
>     > 4 -rw-rw-r-- 1 builder root 675 Dec 24 10:39 .profile

# Running as process ID 1

Finally if we startup the IPython Notebook application localy with Docker, or on OpenShift, then everything still works okay. Further, as well as the ‘getpass.getuser\(\)’ function working, use of ‘pwd.getpwuid\(os.getuid\(\)\)’ also works, this being due to the use of the ‘nss\_wrapper’ library.

So everything is now good and we shouldn’t have any issues. There was though something already present in the way that the ‘jupiter/notebook’ Docker image was set up that is worth looking at. This was the use of the ‘tini’ program as the ‘ENTRYPOINT’ in the ‘Dockerfile’. This relates to problems that can arise when running an application as process ID 1. I will look at what this is all about in the next post.

---

## Comments

### Nadia - March 22, 2018 at 5:43 AM

Hello Graham\!  
Thanks for a great article\!   
I'm trying to use this "hack" to run a container with jenkins. I use official jenkins image \(FROM jenkins/jenkins:lts\), the nss\_wrapper is installed with no problem, but how to configure entrypoint in this case?   
Thanks,  
Nadia

### Graham Dumpleton - March 22, 2018 at 9:54 AM

I wouldn't use nss\_wrapper now. It is easier to make /etc/passwd and /etc/group files writable to group root. Then in entry point script add entries directly to the files such as is done in:  
  
https://github.com/jupyter/docker-stacks/blob/master/base-notebook/start.sh\#L70  
  
This is much simpler than mucking around with the shared libraries.  
  
Updating the passwd file is even recommended way in OpenShift docs now. See 'Support arbitrary user IDs' in:  
  
https://docs.openshift.org/latest/creating\_images/guidelines.html

### Nadia - March 27, 2018 at 1:09 AM

Thanks a lot for a reference, it helps me to configure my container.   
I use this example: https://github.com/RHsyseng/container-rhel-examples/blob/master/starter-arbitrary-uid/Dockerfile.centos7 and it works perfect.

