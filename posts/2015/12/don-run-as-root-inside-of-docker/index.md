---
title: "Don't run as root inside of Docker containers."
author: "Graham Dumpleton"
date: "Friday, December 18, 2015"
url: "http://blog.dscpl.com.au/2015/12/don-run-as-root-inside-of-docker.html"
post_id: "3912131919770047395"
blog_id: "2363643920942057324"
tags: ['docker', 'openshift']
comments: 2
published_timestamp: "2015-12-18T21:04:00+11:00"
blog_title: "Graham Dumpleton"
---

When we run any applications directly on our own computers we avoid doing so as the ‘root’ user unless absolutely necessary. Not running applications as the ‘root’ user is viewed as being a best security practice. Yet when we run applications inside of a Docker container, most people seem to have no qualms at all about running everything as the ‘root’ user.

Yes it can be argued that the application is isolated within a container and shouldn’t be able to break out, but it is still running with the privileges of ‘root’ regardless. If for some reason, be it a bug in Docker or the operating system itself, a misconfigured Docker installation or even that incorrect access rights were granted to some resource when running a specific container, running as ‘root’ is going to increase the risk of an application being able to access outside of the container, directly or indirectly, with elevated privileges.

Although there is a minor note in the [Docker best practices guide](https://docs.docker.com/engine/articles/dockerfile_best-practices/#user) about not running as ‘root’, it doesn’t get emphasised enough. This will no doubt change over time and be seen more importantly as a best practice to follow. It is therefore better now to start designing your Docker images so that they can be run as a non ‘root’ user.

Even now some hosting services based around Docker are restricting applications running inside of a Docker container from running as the ‘root’ user and forcing them to run as a non privileged user. This is the case with OpenShift 3, but as similar services around Docker seek to limit their exposure to the risk of running as the ‘root’ user, even though inside of a container, you can expect them to do the same.

It is recognised as a big enough issue that I believe there are changes in train for the introduction of new features in Docker to reduce the risk. This is coming in the form of support for user namespaces. This is where although within a container it will appear that an application runs as the ‘root’ user and with the privileges of ‘root’ within the container, when seen from outside of the container it will in reality be running as a non privileged user.

So when this becomes a part of Docker and regarded as stable, hosting services using Docker will be able to use that. In the interim, but then even with that coming down the pipeline, it is still preferable to simply not require your application to run as ‘root’ inside of a Docker container.

# Root access via the file system

Although I am sure people will suggest this is a contrived example with limited application to only certain Docker installation types, I am going to show one example where running as ‘root’ in the Docker container can lead to being able to compromise the host that the Docker service is running on.

To do this I am going to rely on the use of volume mounting. What I am going to do may well not be something that any sane person would do, but it highlights the fact that when running as the ‘root’ user within a container, it is currently truly the ‘root’ user even when seen from outside of the container.

For this demonstration I am going to use Docker Toolbox on MacOS X. The ‘docker version’ command indicates I have:

> 
>     $ docker version  
>     > Client:  
>     >  Version: 1.9.1  
>     >  API version: 1.21  
>     >  Go version: go1.4.3  
>     >  Git commit: a34a1d5  
>     >  Built: Fri Nov 20 17:56:04 UTC 2015  
>     >  OS/Arch: darwin/amd64
>     
>     
>     Server:  
>     >  Version: 1.9.1  
>     >  API version: 1.21  
>     >  Go version: go1.4.3  
>     >  Git commit: a34a1d5  
>     >  Built: Fri Nov 20 17:56:04 UTC 2015  
>     >  OS/Arch: linux/amd64

Lets start out by using the official ‘busybox’ image to fire up a shell inside of a container.

> 
>     $ docker run --rm -it busybox sh  
>     >   
>     > / # ls -las  
>     > total 44  
>     >  4 drwxr-xr-x 19 root root 4096 Dec 18 07:55 .  
>     >  4 drwxr-xr-x 19 root root 4096 Dec 18 07:55 ..  
>     >  0 -rwxr-xr-x 1 root root 0 Dec 18 07:55 .dockerenv  
>     >  0 -rwxr-xr-x 1 root root 0 Dec 18 07:55 .dockerinit  
>     >  12 drwxr-xr-x 2 root root 12288 Oct 31 17:14 bin  
>     >  0 drwxr-xr-x 5 root root 380 Dec 18 07:55 dev  
>     >  4 drwxr-xr-x 2 root root 4096 Dec 18 07:55 etc  
>     >  4 drwxr-xr-x 3 root root 4096 Oct 31 17:15 home  
>     >  0 dr-xr-xr-x 129 root root 0 Dec 18 07:55 proc  
>     >  4 drwxr-xr-x 2 root root 4096 Dec 18 07:55 root  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 07:55 sys  
>     >  4 drwxrwxrwt 2 root root 4096 Oct 31 17:15 tmp  
>     >  4 drwxr-xr-x 3 root root 4096 Oct 31 17:15 usr  
>     >  4 drwxr-xr-x 4 root root 4096 Oct 31 17:15 var

Now lets do that again, but lets mount the file system of the Docker host inside of the container.

> 
>     $ docker run --rm -it -v /:/rootfs busybox sh  
>     >   
>     > / # ls -las  
>     > total 44  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 07:56 .  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 07:56 ..  
>     >  0 -rwxr-xr-x 1 root root 0 Dec 18 07:56 .dockerenv  
>     >  0 -rwxr-xr-x 1 root root 0 Dec 18 07:56 .dockerinit  
>     >  12 drwxr-xr-x 2 root root 12288 Oct 31 17:14 bin  
>     >  0 drwxr-xr-x 5 root root 380 Dec 18 07:56 dev  
>     >  4 drwxr-xr-x 2 root root 4096 Dec 18 07:56 etc  
>     >  4 drwxr-xr-x 3 root root 4096 Oct 31 17:15 home  
>     >  0 dr-xr-xr-x 129 root root 0 Dec 18 07:56 proc  
>     >  4 drwxr-xr-x 2 root root 4096 Dec 18 07:56 root  
>     >  0 drwxr-xr-x 17 1001 staff 420 Dec 18 00:27 rootfs  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 07:56 sys  
>     >  4 drwxrwxrwt 2 root root 4096 Oct 31 17:15 tmp  
>     >  4 drwxr-xr-x 3 root root 4096 Oct 31 17:15 usr  
>     >  4 drwxr-xr-x 4 root root 4096 Oct 31 17:15 var  
>     >   
>     > / # ls -las /rootfs  
>     > total 8  
>     >  0 drwxr-xr-x 17 1001 staff 420 Dec 18 00:27 .  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 07:56 ..  
>     >  0 drwxr-xr-x 1 1000 staff 204 Nov 12 00:41 Users  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt  
>     >  0 dr-xr-xr-x 129 root root 0 Dec 18 00:26 proc  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var

When the ‘-v’ option is used with ‘docker run’ it by default mounts the file system read/write.

Using ‘-v /:/rootfs’ I have therefore mounted the root file system of the Docker host, in this case running inside of the VM started by Docker Toolbox, inside of the container at the location ‘/rootfs’.

To show that it is indeed the file system of the Docker host we can ‘ssh’ into the Docker host and create a temporary file in the root directory of the filesystem.

> 
>     $ docker-machine ssh default  
>     >  ## .  
>     >  ## ## ## ==  
>     >  ## ## ## ## ## ===  
>     >  /"""""""""""""""""\___/ ===  
>     >  ~~~ {~~ ~~~~ ~~~ ~~~~ ~~~ ~ / ===- ~~~  
>     >  \______ o __/  
>     >  \ \ __/  
>     >  \____\_______/  
>     >  _ _ ____ _ _  
>     > | |__ ___ ___ | |_|___ \ __| | ___ ___| | _____ _ __  
>     > | '_ \ / _ \ / _ \| __| __) / _` |/ _ \ / __| |/ / _ \ '__|  
>     > | |_) | (_) | (_) | |_ / __/ (_| | (_) | (__| < __/ |  
>     > |_.__/ \___/ \___/ \__|_____\__,_|\___/ \___|_|\_\___|_|  
>     > Boot2Docker version 1.9.1, build master : cef800b - Fri Nov 20 19:33:59 UTC 2015  
>     > Docker version 1.9.1, build a34a1d5  
>     >   
>     > docker@default:~$ cd /  
>     >   
>     > docker@default:/$ ls -las  
>     > total 4  
>     >  0 drwxr-xr-x 17 tc staff 420 Dec 18 08:05 ./  
>     >  0 drwxr-xr-x 17 tc staff 420 Dec 18 08:05 ../  
>     >  0 drwxr-xr-x 1 docker staff 204 Nov 12 00:41 Users/  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin/  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev/  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc/  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home/  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib/  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib/  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt/  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt/  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc/  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root/  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run/  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin/  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys/  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp/  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr/  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var/  
>     >   
>     > docker@default:/$ sudo touch FROMDOCKERHOST  
>     >   
>     > docker@default:/$ ls -las  
>     > total 4  
>     >  0 drwxr-xr-x 17 tc staff 440 Dec 18 08:06 ./  
>     >  0 drwxr-xr-x 17 tc staff 440 Dec 18 08:06 ../  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 docker staff 204 Nov 12 00:41 Users/  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin/  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev/  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc/  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home/  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib/  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib/  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt/  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt/  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc/  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root/  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run/  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin/  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys/  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp/  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr/  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var/

Switching back to our shell running inside of the container and listing what is in the mounted ‘/rootfs’ directory we can see the file which was created.

> 
>     / # ls -las /rootfs  
>     > total 8  
>     >  0 drwxr-xr-x 17 1001 staff 440 Dec 18 08:06 .  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 07:56 ..  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 1000 staff 204 Nov 12 00:41 Users  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var

Now lets try updating the same file system from within the container.

> 
>     / # touch /rootfs/FROMCONTAINER  
>     >   
>     > / # ls -las /rootfs  
>     > total 8  
>     >  0 drwxr-xr-x 17 1001 staff 460 Dec 18 08:13 .  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 08:13 ..  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:13 FROMCONTAINER  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 1000 staff 204 Nov 12 00:41 Users  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var

And finally checking that we can see the change from the Docker host.

> 
>     docker@default:/$ ls -las  
>     > total 4  
>     >  0 drwxr-xr-x 17 tc staff 460 Dec 18 08:13 ./  
>     >  0 drwxr-xr-x 17 tc staff 460 Dec 18 08:13 ../  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:13 FROMCONTAINER  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 docker staff 204 Nov 12 00:41 Users/  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin/  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev/  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc/  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home/  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib/  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib/  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt/  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt/  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc/  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root/  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run/  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin/  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys/  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp/  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr/  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var/

Take note here that the file we were able to create from the Docker container on the Docker host file system is owned by ‘root’. Thus ownership of the file at least was preserved when created.

Lets try something a bit more complicated. From inside of the Docker container, lets make a copy of the program ‘/usr/bin/whoami’ and modify the permissions of the copy so that it should run as a ‘setuid' executable.

> 
>     / # cp /rootfs/usr/bin/whoami /rootfs/whoami  
>     >   
>     > / # chmod 4711 /rootfs/whoami  
>     >   
>     > / # ls -las /rootfs  
>     > total 536  
>     >  0 drwxr-xr-x 17 1001 staff 480 Dec 18 08:17 .  
>     >  4 drwxr-xr-x 20 root root 4096 Dec 18 08:13 ..  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:13 FROMCONTAINER  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 1000 staff 204 Nov 12 00:41 Users  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var  
>     >  528 -rws--x--x 1 root root 539203 Dec 18 08:17 whoami

Note how the permissions for the user are now ‘rws’ on the copy of the ‘whoami’ executable we made.

This ’s’ indicates that it is now a ‘setuid’ executable. This means that when we run that program it should run with the privileges of the user that is the owner of the program, rather than the privileges of the user running the program.

But will that actually be what occurs if we now run the copy of the program from the Docker host given that we made the copy and set the permissions from inside of the Docker container.

> 
>     docker@default:/$ ls -las  
>     > total 532  
>     >  0 drwxr-xr-x 17 tc staff 480 Dec 18 08:17 ./  
>     >  0 drwxr-xr-x 17 tc staff 480 Dec 18 08:17 ../  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:13 FROMCONTAINER  
>     >  0 -rw-r--r-- 1 root root 0 Dec 18 08:06 FROMDOCKERHOST  
>     >  0 drwxr-xr-x 1 docker staff 204 Nov 12 00:41 Users/  
>     >  0 drwxr-xr-x 2 root root 1500 Dec 18 00:27 bin/  
>     >  0 drwxrwxr-x 14 root staff 4400 Dec 18 00:27 dev/  
>     >  0 drwxr-xr-x 12 root root 1040 Dec 18 00:27 etc/  
>     >  0 drwxrwxr-x 3 root staff 60 Dec 18 00:27 home/  
>     >  4 -rwxr-xr-x 1 root root 496 Nov 20 19:34 init  
>     >  0 drwxr-xr-x 5 root root 860 Dec 18 00:27 lib/  
>     >  0 lrwxrwxrwx 1 root root 3 Dec 18 00:27 lib64 -> lib/  
>     >  0 lrwxrwxrwx 1 root root 11 Dec 18 00:27 linuxrc -> bin/busybox  
>     >  0 drwxr-xr-x 4 root root 80 Dec 18 00:27 mnt/  
>     >  0 drwxrwsr-x 2 root staff 180 Dec 18 00:27 opt/  
>     >  0 dr-xr-xr-x 131 root root 0 Dec 18 00:26 proc/  
>     >  0 drwxrwxr-x 2 root staff 80 Dec 18 00:27 root/  
>     >  0 drwxrwxr-x 4 root staff 80 Dec 18 00:27 run/  
>     >  0 drwxrwxr-x 2 root root 1400 Dec 18 00:27 sbin/  
>     >  0 dr-xr-xr-x 13 root root 0 Dec 18 00:27 sys/  
>     >  0 lrwxrwxrwx 1 root root 13 Dec 18 00:27 tmp -> /mnt/sda1/tmp/  
>     >  0 drwxr-xr-x 7 root root 140 Dec 18 00:27 usr/  
>     >  0 drwxrwxr-x 9 root staff 200 Dec 18 00:27 var/  
>     >  528 -rws--x--x 1 root root 539203 Dec 18 08:17 whoami  
>     >   
>     > docker@default:/$ /usr/bin/whoami  
>     > docker  
>     >   
>     > docker@default:/$ /whoami  
>     > root

And yes it does.

So what we have been able to do is modify the permissions of a program on the Docker host through the volume mount.

Sure, no one should every really be mounting the root filesystem of the Docker host read/write inside of a container and so this really comes down to being a configuration issue, but if that did inadvertently happen for some reason, it means that arbitrary changes could be made to the Docker host file system.

I could have gone and replaced arbitrary executables, modified system startup scripts, or taken a copy of the ‘sh’ program and turned it into a ‘setuid’ executable so that a non ‘root' user on the Docker host could become ‘root’.

As noted I am using Docker Toolbox and it may well be the case that it isn’t locked down in as secure a manner as your typical Docker service, but it was still possible with its configuration at least. The fact that you can ‘ssh’ into the Docker host created by Docker Toolbox and then ‘sudo’ to ‘root’ also makes it a moot point as well.

Anyway, the point I am trying to illustrate is that when running as ‘root’ inside of the container you truly are ‘root’, so if you can escape the container in some way you could well be able to get elevated privileges.

So why risk it? Run your containers as a non ‘root’ user in the first place and you remove one element of risk that anyone able to access the container could somehow break out of the container with ‘root’ privileges.

# Running containers as non root user

If you are the developer of a Docker image, the first thing you can therefore do is make sure that you at least use the ‘USER’ statement to indicate what non root user an application should run as when the container is started.

In doing this you will have to be very mindful of how you set up file system permissions so that your application can write to any file system directory it might still want to have write access to.

Even then it becomes tricky as when a container is run, the user that is specified by the ‘USER’ statement can still be overridden using the ‘-u’ option to ‘docker run’. If this is done, even though you may have fixed up filesystem permission so they match the user specified by the ‘USER’ statement, then your application could still fail.

It was the overriding of the user that the container ran as that was in part the issue I described in my [last blog post](http://blog.dscpl.com.au/2015/12/running-ipython-as-docker-container.html) about trying to run the IPython Docker image called ‘jupyter/notebook’ under OpenShift. In order to prohibit applications from running as ‘root’ in a Docker container, OpenShift uses the ‘-u’ option to ‘docker run’ to override the user to be a non privileged user.

In my next blog post I will delve more into the ‘-u’ option of ‘docker run’, what it does and the complications it causes. We will also return back to our IPython example in illustrating those issues.

---

## Comments

### Unknown - November 3, 2017 at 10:52 PM

So if you explicitly mount root fs and explicitly give all permissions to write in that root fs, the one who has been given those permissions may write in that root fs because he has been given permissions to do so.  
Well that's a terrific surprise.

### Graham Dumpleton - November 4, 2017 at 10:23 AM

What you are ignoring is that when someone has root privilege from a normal user, you would still need to use 'sudo' to execute a command as root and supply a password.  
  
Where a normal user has been setup to use Docker without becoming root to use 'docker run', the method explained means that someone could indirectly still manage to do something as root via Docker without needing to supply a password, albeit it would take a few extra steps.  
  
So if you have the ability to run 'docker run' from your normal user account, and you left your screen unlocked, it is as good as having left a window open as the root user.

