---
layout: post
title: "Random user IDs when running Docker containers."
author: "Graham Dumpleton"
date: "2015-12-23"
url: "http://blog.dscpl.com.au/2015/12/random-user-ids-when-running-docker.html"
post_id: "6212721734777656933"
blog_id: "2363643920942057324"
tags: ['docker', 'ipython', 'openshift', 'python']
comments: 2
published_timestamp: "2015-12-23T16:39:00+11:00"
blog_title: "Graham Dumpleton"
---

At this point in our exploration of [getting IPython to work on OpenShift](/posts/2015/12/running-ipython-as-docker-container/) we have deduced that we cannot, and should not, have our Docker container be dependent on [running as the 'root' user](/posts/2015/12/don-run-as-root-inside-of-docker/). Simply setting up the Docker container to [run as a specific non ‘root’ user](/posts/2015/12/overriding-user-docker-containers-run-as/) wasn’t enough however. This is because in pursuit of a more secure environment, OpenShift actually uses a different user ID for each project when running Docker containers.

As I keep noting, user namespaces when available in Docker, should be able to transparently hide any underlying mapping to a special user ID as required by an underlying platform, allowing the Docker container to use what ever user ID it wants. We aren’t there yet, and given that user namespaces were first talked about as coming soon [well over a year ago](https://news.ycombinator.com/item?id=7909622), we could well be waiting some time yet for all the necessary pieces to fall into place to enable that.

In the mean time, the best thing you can do to ensure Docker images are portable to different hosting environments, and be as secure as possible, is design your Docker containers to run as a non ‘root’ user, but at the same time be tolerant of running as an arbitrary user ID specified at the time the Docker container is started.

# File system access permissions

In our prior post, where we got to was that when running our IPython Docker container as a random user ID, it would fail even when running some basics checks.

```
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

The problems basically boiled down to file system access permissions, this being caused by the fact that we were running as a different user ID to what we expected.

The first specific problem was that the ‘HOME’ directory environment variable wasn’t set to what was expected for the user we anticipated everything to run as. This meant that instead of the home directory ‘/home/ipython’ being used, it was trying to use ‘/‘ as the home directory.

As a first step, lets simply try overriding the ‘HOME’ directory and forcing it to be what we desired it to be by adding to the ‘Dockerfile':

```
 ENV HOME=/home/ipython
```

Starting the Docker container with an interactive shell we now get:

```
 $ docker run --rm -it -u 100000 -p 8888:8888 jupyter-notebook bash  
 I have no name!@e40f5e18f666:/notebooks$ whoami  
 whoami: cannot find name for user ID 100000  
 I have no name!@e40f5e18f666:/notebooks$ id  
 uid=100000 gid=0(root)  
 I have no name!@e40f5e18f666:/notebooks$ pwd  
 /notebooks  
 I have no name!@e40f5e18f666:/notebooks$ env | grep HOME  
 HOME=/home/ipython  
 I have no name!@e40f5e18f666:/notebooks$ touch $HOME/magic  
 touch: cannot touch ‘/home/ipython/magic’: Permission denied
```

The ‘HOME’ directory environment variable is now correct, but we still cannot create files due to the fact that the home directory is owned by the ‘ipython’ user and we are running with a different user ID.

```
 $ ls -las $HOME  
 total 24  
 4 drwxr-xr-x 3 ipython ipython 4096 Dec 22 21:53 .  
 4 drwxr-xr-x 4 root root 4096 Dec 22 21:53 ..  
 4 -rw-r--r-- 1 ipython ipython 220 Dec 22 21:53 .bash_logout  
 4 -rw-r--r-- 1 ipython ipython 3637 Dec 22 21:53 .bashrc  
 4 drwx------ 2 ipython ipython 4096 Dec 22 21:53 .jupyter  
 4 -rw-r--r-- 1 ipython ipython 675 Dec 22 21:53 .profile
```

# Using group access permissions

The solution to file system access permission problems one often sees in Docker containers which try to run as a non ‘root’ user is to simply make files and directories world writable. That is, after setting up everything in the ‘Dockerfile’ as the ‘root’ user and before switching the user using a ‘USER’ statement, the ‘chmod’ command is run recursively on any directories and files which the running application might need to update. 

I personally don’t like this approach of making everything world writable at all. To me it falls into that category of bad practices you wouldn’t use if you were installing an application direct to a host when you aren’t using Docker, so why start now. But what are the alternatives?

The more secure alternative that would normally be used to allow multiple users to update the same directories or files are UNIX groups. The big question is whether they are going to be useful in this case or not.

As it is, when the home directory for the ‘ipython’ user was created, the directories and files were created with the group ‘ipython’, being a personal group created for the ‘ipython’ user when the ‘adduser’ command was used to create the user account.

The problem with the use of a personal group as the primary group for the user and thus the directories and files created, is that it is impossible to know what the random user ID will be and so add it into the personal group in advance. Having the group of the directories and files be a personal group is therefore not going to work.

The question now is if the group would normally be set to whatever the primary group is for a named user, what group is actually going to be used when the user ID is being overridden for the container at run time.

Lets first look at the case of where we override the user ID but still use one which does have a user defined for it.

```
 $ docker run --rm -it -u 5 -p 8888:8888 jupyter-notebook bash  
 games@d0e1f5776ccb:/notebooks$ id  
 uid=5(games) gid=60(games) groups=60(games)
```

Here we specify the user ID ‘5’, which corresponds to the ‘games’ user. That user happens to have a corresponding primary group which maps to its own personal group of ‘games’. In overriding the user ID, the primary group for the user is still picked and used as the effective group. Thus the ‘id’ command shows the ‘gid’ being ’60’, corresponding to the ‘games’ group.

Do note that this is only the case where only the user ID was overridden. It so happens that the ‘-u’ option to ‘docker run’ can also be used to override the effective group used as well.

```
 $ docker run --rm -it -u 5:1 -p 8888:8888 jupyter-notebook bash  
 games@58d9074c872c:/notebooks$ id  
 uid=5(games) gid=1(daemon) groups=60(games)
```

Here we have overridden the effective group to be group ID of ‘1’, corresponding to the ‘daemon’ group.

Back to our random user ID, when we select a user ID which doesn’t have a corresponding user account we see:

```
 docker run --rm -it -u 10000 -p 8888:8888 jupyter-notebook bash  
 I have no name!@f4050457c1ee:/notebooks$ id  
 uid=10000 gid=0(root)
```

That is, the effective group is set as the ‘gid’ of ‘0’, corresponding to the group for ‘root’.

The end result is that provided that we do not override the effective group as well using the ‘-u’ option, if the user ID specified corresponds to a user account, then the primary group for that user would be used. If instead a random user ID were used for which there did not exist a corresponding user account, then the effective group would be that for the ‘gid’ of ‘0’, which is reserved for the ‘root’ user group.

Note that in a hosting service which is effectively using a randomly assigned user ID, it is assumed that it will never select one which overlaps with an existing user ID. This can’t be completely guaranteed, although so long as a hosting service uses user IDs starting at a very large number, it is a good bet it will not clash with an existing user. For OpenShift at least, it appears to allocate user IDs starting somewhere above ‘1000000000’.

As to overriding the group as well as the user ID, it is also assumed that a hosting service would not do that. Again, OpenShift at least doesn’t override the group and this is probably the most sensible thing that could be done here as overriding of the group to be some random ID as well, would make the use of UNIX groups inside of the container impossible as nothing would be predictable. In this case I would suggest any hosting service going down this path of allocating user IDs, follow OpenShift’s lead and not override the group ID as doing so would likely just cause a world of hurt.

# Using a user with effective GID of 0

What now is going to be the most workable solution if we wish to rely on group access permissions?

In light of the above observed behaviour what seems might work is to have the special user we created, and which would be the default user specified by the ‘USER’ statement of the ‘Dockerfile', have a primary group with ‘gid’ of ‘0’. That is, we match what would be the primary group used if a random user ID had been used which does not correspond to a user account.

By making such a choice for the effective group, it means that the group will be the same for both cases and we can now set up file system permissions correspondingly.

Updating our ‘Dockerfile’ based on this, we end up with:

```
 RUN adduser --disabled-password --gid 0 --gecos "IPython" ipython  
   
 RUN mkdir -m 0775 /notebooks && chown ipython:root /notebooks  
   
 VOLUME /notebooks  
 WORKDIR /notebooks  
   
 USER ipython  
   
 # Add a notebook profile.RUN mkdir -p -m 0775 ~ipython/.jupyter/ && \  
  echo "c.NotebookApp.ip = '*'" >> ~ipython/.jupyter/jupyter_notebook_config.py  
   
 RUN chmod -R u+w,g+w /home/ipython  
   
 ENV HOME=/home/ipython
```

The key changes are:

  * Add the ‘--gid 0’option to ‘adduser’ so that the primary group for user is ‘root’.
  * Create the ‘/notebooks’ directory with mode ‘0775’ so writable by group.
  * Move creation of ‘jupyter\_notebook\_config.py’ down to where we are the non ‘root’ user.
  * Change permissions on all files and directories in home directory so writable by group.



Lets now check what happens for each of the use cases we expect.

For the case where the Docker container runs as the default user as specified by the ‘USER’ statement we now get:

```
 $ docker run --rm -it -p 8888:8888 jupyter-notebook bash  
 ipython@68d5a31bcc03:/notebooks$ whoami  
 ipython  
 ipython@68d5a31bcc03:/notebooks$ id  
 uid=1000(ipython) gid=0(root) groups=0(root)  
 ipython@68d5a31bcc03:/notebooks$ pwd  
 /notebooks  
 ipython@68d5a31bcc03:/notebooks$ env | grep HOME  
 HOME=/home/ipython  
 ipython@68d5a31bcc03:/notebooks$ touch $HOME/magic  
 ipython@68d5a31bcc03:/notebooks$ touch /notebooks  
 ipython@68d5a31bcc03:/notebooks$ ls -las $HOME  
 total 24  
 4 drwxrwxr-x 4 ipython root 4096 Dec 23 02:26 .  
 4 drwxr-xr-x 6 root root 4096 Dec 23 02:26 ..  
 4 -rw-rw-r-- 1 ipython root 220 Dec 23 02:15 .bash_logout  
 4 -rw-rw-r-- 1 ipython root 3637 Dec 23 02:15 .bashrc  
 4 drwxrwxr-x 2 ipython root 4096 Dec 23 02:15 .jupyter  
 0 -rw-r--r-- 1 ipython root 0 Dec 23 02:26 magic  
 4 -rw-rw-r-- 1 ipython root 675 Dec 23 02:15 .profile
```

Everything in our checks still works okay and running up the actual Jupyter Notebook application also works fine, with us being able to create and save new notebooks.

This is what we would expect as the directories and files are owned by the ‘ipython’ user and we are also running as that user.

Of note is that you will now see that the effective group of the user is a ‘gid’ of ‘0’. All the directories and files also have that group.

If we use the ‘-u ipython’ or ‘-u 1000’ option, where ‘1000’ was the user ID allocated by the ‘adduser’ command in the ‘Dockerfile’, that all works fine as well.

For the case of overriding the user with a random user ID, we get:

```
 $ docker run --rm -it -u 10000 -p 8888:8888 jupyter-notebook bash  
 I have no name!@dbe290496d44:/notebooks$ whoami  
 whoami: cannot find name for user ID 10000  
 I have no name!@dbe290496d44:/notebooks$ id  
 uid=10000 gid=0(root)  
 I have no name!@dbe290496d44:/notebooks$ pwd  
 /notebooks  
 I have no name!@dbe290496d44:/notebooks$ env | grep HOME  
 HOME=/home/ipython  
 I have no name!@dbe290496d44:/notebooks$ touch $HOME/magic  
 I have no name!@dbe290496d44:/notebooks$ touch /notebooks/magic  
 I have no name!@dbe290496d44:/notebooks$ ls -las $HOME  
 total 24  
 4 drwxrwxr-x 4 ipython root 4096 Dec 23 02:32 .  
 4 drwxr-xr-x 6 root root 4096 Dec 23 02:32 ..  
 4 -rw-rw-r-- 1 ipython root 220 Dec 23 02:31 .bash_logout  
 4 -rw-rw-r-- 1 ipython root 3637 Dec 23 02:31 .bashrc  
 4 drwxrwxr-x 2 ipython root 4096 Dec 23 02:31 .jupyter  
 0 -rw-r--r-- 1 10000 root 0 Dec 23 02:32 magic  
 4 -rw-rw-r-- 1 ipython root 675 Dec 23 02:31 .profile
```

Unlike before when overriding with a random user ID with no corresponding user account, the attempts to create files in the file system now works okay.

What you will note though is that the file created is in this case owned by user with user ID of ‘10000’. This worked because the effective group of the random user ID was ‘root’, matching what the directory used, along with the fact that the group permissions of the directory allowed updates by anyone in the same group. Thus it didn’t matter that the user ID was different to the owner of the group.

One thing you may note is that when the file ‘magic’ was created, the resulting file wasn’t itself writable to the group. This was the case as the default ‘umask’ setup by Docker when a container is run is ‘0022’. This particular ‘umask’ disables the setting of the ‘w’ flag on the group.

Even though this is the case, this is not a problem because from this point on any code that would run, such as the actual Jupyter Notebook application, would only ever run as the same allocated user ID. There is therefore no expectation of any processes running as the original ‘ipython’ user needing to be able to update the file.

In other words, that directories and files are fixed up to be writable to group only matters for the original directories and files created as part of the Docker build as the ‘ipython’ user. What happens after that and what the ‘umask’ may be is not important.

One final check to go, will this updated version of the ‘jupyter/notebook’ Docker image work on OpenShift, and the answer is that it does indeed now start up okay and does not error out due to the problems with access permissions we had before.

If we access the running container on OpenShift we can perform the same checks as above okay.

```
 $ oc rsh ipython-3-c7oit  
 I have no name!@ipython-3-c7oit:/notebooks$ whoami  
 whoami: cannot find name for user ID 1000210000  
 I have no name!@ipython-3-c7oit:/notebooks$ id  
 uid=1000210000 gid=0(root)  
 I have no name!@ipython-3-c7oit:/notebooks$ pwd  
 /notebooks  
 I have no name!@ipython-3-c7oit:/notebooks$ env | grep HOME  
 HOME=/home/ipython  
 I have no name!@ipython-3-c7oit:/notebooks$ touch $HOME/magic  
 I have no name!@ipython-3-c7oit:/notebooks$ touch /notebooks/magic  
 I have no name!@ipython-3-c7oit:/notebooks$ ls -las $HOME  
 total 20  
 4 drwxrwxr-x. 5 ipython root 4096 Dec 23 03:20 .  
 0 drwxr-xr-x. 3 root root 20 Dec 23 03:13 ..  
 4 -rw-------. 1 1000210000 root 31 Dec 23 03:20 .bash_history  
 4 -rw-rw-r--. 1 ipython root 220 Dec 23 03:13 .bash_logout  
 4 -rw-rw-r--. 1 ipython root 3637 Dec 23 03:13 .bashrc  
 0 drwxr-xr-x. 5 1000210000 root 64 Dec 23 03:19 .ipython  
 0 drwxrwxr-x. 2 ipython root 39 Dec 23 03:14 .jupyter  
 0 drwx------. 3 1000210000 root 18 Dec 23 03:18 .local  
 0 -rw-r--r--. 1 1000210000 root 0 Dec 23 03:20 magic  
 4 -rw-rw-r--. 1 ipython root 675 Dec 23 03:13 .profile
```

# Named user vs numeric user ID

Before we go on to further verify whether the updated Docker image does in fact work properly on OpenShift, I want to revisit the use of the ‘USER’ statement in the ‘Dockerfile’.

Right now the ‘USER’ statement is specifying a default user. This user would be used if you were running the Docker image directly with Docker yourself. As we have seen, if used with OpenShift, the user given by the ‘USER’ statement is actually ignored.

The reasons that a hosting service such as OpenShift ignores the user specified by the ‘USER’ statement is that it cannot trust that the user is a non ‘root’ user when the user is specified by way of a name. But also because where a host service provides an ability to mount shared persistent volumes into containers it may want to ensure running containers owned by a specific service account, or a project within a service account, have different user IDs as part of ensuring that there is no way an application could see any data stored on a shared volume created by a different user, if a volume was mounted against the wrong container.

Now one of the possibilities I did describe in a prior post was that if a hosting service only supported 12 factor applications and didn’t support persistent data volumes, although it should really still prohibit running a container as ‘root’, it may allow a container to run as the user specified by the ‘USER’ statement so long as it knows it isn’t ‘root’. This though it can only know if a numeric user ID was defined with the ‘USER’ statement.

To cater for the possibility, rather than use a user name with the ‘USER’ statement, lets use its numeric user ID instead.

Now from the above tests we saw that the numeric user ID for the user ‘ipython’ created by ‘adduser’ was ‘1000’. We could therefore use it with the ‘USER’ statement, however, since what ‘adduser’ will use for the user ID is not technically deterministic, as it can be dependent on what other user accounts may already have been created, but also can depend on what operating system is used, we are better off being explicit and telling ‘adduser’ what user ID to use.

What exactly the [lowest recommended user ID](https://en.wikipedia.org/wiki/User_identifier) is for normal user accounts looks to be 500 on Posix and Red Hat systems, and 1000 on OpenSuSE and Debian. Lets therefore go with a number 1000 or above, but just in case an operating system image may include at least a default user account, lets skip 1000 and use 1001 instead.

Making this change we now end up with the ‘Dockerfile’ being:

```
 RUN adduser --disabled-password --uid 1001 --gid 0 --gecos "IPython" ipython

 RUN mkdir -m 0775 /notebooks && chown ipython:root /notebooks

 VOLUME /notebooks  
 WORKDIR /notebooks

 USER 1001

 # Add a notebook profile.  
 RUN mkdir -p -m 0775 ~ipython/.jupyter/ && \  
  echo "c.NotebookApp.ip = '*'" >> ~ipython/.jupyter/jupyter_notebook_config.py

 RUN chmod -R u+w,g+w /home/ipython

 ENV HOME=/home/ipython
```

All up this should give us a the most portable solution. Working where the Docker container is hosted directly on Docker, but also working on a hosting service such as OpenShift, which uses Docker under the covers, but which overrides the user ID containers run as. Using a numeric user ID for ‘USER’ also allows a hosting service to still used our preferred user if it does not want to allow containers to run as ‘root’, as will know it can trust that it will run as the user ID indicated.

# Cannot find name for user ID

It would be great to say at this point that we are done and everything works fine. That is however not the case as I will go into in the next post.

The remaining problem relates to what happens when we run the ‘whoami’ command:

```
 $ docker run --rm -it -u 10000 -p 8888:8888 jupyter-notebook bash  
 I have no name!@dbe290496d44:/notebooks$ whoami  
 whoami: cannot find name for user ID 10000
```

As we can see, ‘whoami’ isn’t able to return a valid value due to the user ID everything runs as not actually matching a user account.

In initially running up the updated Docker image this didn’t appear to prevent the IPython Notebook application running, but as we delve deeper we will see that it can actually cause problems.

---

## Comments

### Unknown - July 13, 2016 at 1:42 AM

Thanks for your article.   
Do you have any idea on how to solve this problem ?  
  
whoami: cannot find name for user ID 10000

### Graham Dumpleton - July 13, 2016 at 9:56 AM

How to solve the issue explained in this post is in the next post in this series:  
  
[/posts/2015/12/unknown-user-when-running-docker/](/posts/2015/12/unknown-user-when-running-docker/)

