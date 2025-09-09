---
title: "Installing mod_wsgi on MacOS X with native operating system tools."
author: "Graham Dumpleton"
date: "Tuesday, July 26, 2016"
url: "http://blog.dscpl.com.au/2016/07/installing-modwsgi-on-macos-x-with.html"
post_id: "132122468813472154"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python']
comments: 0
published_timestamp: "2016-07-26T14:15:00+10:00"
blog_title: "Graham Dumpleton"
---

Operating systems inevitably change over time, and because writing documentation is often an after thought or developers have no time, the existing instructions on how to install a piece of software can suffer bit rot and stop working. This has been the case for a while with various parts of the documentation for mod\_wsgi. This post is a first step at least in getting the documentation for installing mod\_wsgi on MacOS X brought up to date. The post will focus on installing mod\_wsgi using the native tools that the MacOS X operating system provides.

# Installing direct from source code

A precompiled binary package for mod\_wsgi is actually available from Apple as part of the Mac OS X server app available from the MacOS X App Store. The last time I looked this was a very old version of mod\_wsgi from many years ago. Unless for some reason you really need to use the version of mod\_wsgi provided with MacOS X server, I would instead recommend you install an up to date version of mod\_wsgi direct from source code.

Installation of mod\_wsgi from source code on MacOS X used to be a simple matter, but with the introduction of [System Integrity Protection](https://en.wikipedia.org/wiki/System_Integrity_Protection) in MacOS X El Capitan this has become a bit more complicated. Lets step through the normal steps for installing mod\_wsgi to see what the issue is.

After having downloaded and extracted the latest source code for mod\_wsgi, to install mod\_wsgi direct into an Apache installation involves running the traditional steps for most Open Source packages of doing a ‘configure’, ‘make’ and ‘sudo make install’.

Before you do that it is important though that you have at least installed the _Xcode command line tools_. This is an Apple supplied package for MacOS X which contains the C compiler we will need to build the mod\_wsgi source code, as well as the headers files and other support files for the Apache httpd web server.

To check that you have the Xcode command line tools you can run ‘xcode-select --install’. If you have them installed already, you should see the message below, otherwise you should be stepped through installation of the package.

```bash
    $ xcode-select --install  
    xcode-select: error: command line tools are already installed, use "Software Update" to install updates
```

Do ensure that you have run software update to get the latest version for your operating system revision if you don’t regularly update.

With the Xcode command line tools installed, you can now run the ‘configure’ script found in the mod\_wsgi source directory.

```python
    $ ./configure
    checking for apxs2... no
    checking for apxs... /usr/sbin/apxs
    checking for gcc... gcc
    checking whether the C compiler works... yes
    checking for C compiler default output file name... a.out
    checking for suffix of executables...
    checking whether we are cross compiling... no
    checking for suffix of object files... o
    checking whether we are using the GNU C compiler... yes
    checking whether gcc accepts -g... yes
    checking for gcc option to accept ISO C89... none needed
    checking for prctl... no
    checking Apache version... 2.4.18
    checking for python... /usr/bin/python
    configure: creating ./config.status
    config.status: creating Makefile
```

Important to note here is that we want the ‘apxs’ version found to be ‘/usr/sbin/apxs’ and the ‘python’ version found to be ‘/usr/bin/python’. If these aren’t the versions found then it indicates that you have a Python or Apache httpd server installation which was installed separately and is not the native versions supplied with MacOS X. I am not going to cover using separate Python or Apache httpd server installations in this post and assume you only have the native tools.

The next step is to run ‘make’.

```bash
    $ make  
    ./apxs -c -I/System/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -DENABLE_DTRACE -DMACOSX -DNDEBUG -DNDEBUG -DENABLE_DTRACE -Wc,-g -Wc,-O2 -Wc,'-arch x86_64' src/server/mod_wsgi.c src/server/wsgi_*.c -L/System/Library/Frameworks/Python.framework/Versions/2.7/lib -L/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/config -arch x86_64 -lpython2.7 -ldl -framework CoreFoundation  
    ./libtool --silent --mode=compile /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc -DDARWIN -DSIGPROCMASK_SETS_THREAD_MASK -DDARWIN_10 -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.Internal.sdk/usr/include/apr-1 -I/usr/include/apache2 -I/usr/include/apr-1 -I/usr/include/apr-1 -g -O2 -arch x86_64 -I/System/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7 -DENABLE_DTRACE -DMACOSX -DNDEBUG -DNDEBUG -DENABLE_DTRACE -c -o src/server/mod_wsgi.lo src/server/mod_wsgi.c && touch src/server/mod_wsgi.slo  
    ...  
    ./libtool --silent --mode=link /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/cc    -o src/server/mod_wsgi.la  -rpath /usr/libexec/apache2 -module -avoid-version    src/server/wsgi_validate.lo src/server/wsgi_thread.lo src/server/wsgi_stream.lo src/server/wsgi_server.lo src/server/wsgi_restrict.lo src/server/wsgi_metrics.lo src/server/wsgi_memory.lo src/server/wsgi_logger.lo src/server/wsgi_interp.lo src/server/wsgi_daemon.lo src/server/wsgi_convert.lo src/server/wsgi_buckets.lo src/server/wsgi_apache.lo src/server/mod_wsgi.lo -L/System/Library/Frameworks/Python.framework/Versions/2.7/lib -L/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/config -arch x86_64 -lpython2.7 -ldl -framework CoreFoundation
```

If you look closely you might note something strange in the output from running ‘make’. That is that rather than running ‘/usr/bin/apxs’ it is running a version of ‘apxs’ out of the directory where ‘make’ was run. Similarly, the system version of ‘libtool’ is ignored and a local copy used instead.

For those not familiar with what ‘apxs’ is, it is a tool supplied with the Apache httpd server package to assist in the compilation and installation of Apache modules. Unfortunately, every time that a new version of MacOS X comes out Apple somehow breaks the ‘apxs’ tool so that it doesn’t work. Typically this is because the ‘apxs’ tool embeds paths to a special variant of the C compiler used when Apple build their own packages. This is different to the C compiler which we as users can use when we install the Xcode command line tools. More specifically, the C compiler from the Xcode command line tools is installed in a different location to what ‘apxs’ expects and so it fails. A similar problem exists with ‘libtool’.

This issue with ‘apxs’ and ‘libtool’ being broken has been present for a number of MacOS X versions now and Apple seems to have no interest in fixing it. To get around the problem the ‘configure’ script of mod\_wsgi creates copies of the original ‘apxs’ and ‘libtool’ programs and fixes them up so correct paths are used. This is the reason why local versions of those tools are used.

With the build of mod\_wsgi now complete we just need to install it by running ‘sudo make install’. The result of this should be that the compiled ‘mod\_wsgi.so’ module will be installed into the Apache httpd server installation modules directory. Because though of the System Integrity Protection feature mentioned above, this isn’t what now occurs. Instead the installation fails.

```python
    $ sudo make install  
    Password:  
    ./apxs -i -S LIBEXECDIR=/usr/libexec/apache2 -n 'mod_wsgi' src/server/mod_wsgi.la  
    /usr/share/httpd/build/instdso.sh SH_LIBTOOL='./libtool' src/server/mod_wsgi.la /usr/libexec/apache2  
    ./libtool --mode=install install src/server/mod_wsgi.la /usr/libexec/apache2/  
    libtool: install: install src/server/.libs/mod_wsgi.so /usr/libexec/apache2/mod_wsgi.so  
    install: /usr/libexec/apache2/mod_wsgi.so: Operation not permitted  
    apxs:Error: Command failed with rc=4653056  
    .  
    make: *** [install] Error 1
```

The rather obscure error message we get when this fails is ‘Operation not permitted’. This doesn’t exactly tell us a lot and is mighty confusing to anyone installing mod\_wsgi, or any other Apache module.

The reason we get this error is that the System Integrity Protection feature means that even when running as root, it is no longer possible to copy new files into certain system directories on MacOS X. This is meant in part to protect the operating system directories from being messed up by a user, but means we are now prohibited from installing additional Apache httpd server modules into the standard modules directory of ‘/usr/libexec/apache2’.

# Creating a separate modules directory

There are a few solutions to the problem that the System Integrity Protection feature causes.

Since it is the cause of the problem, you might think about disabling the System Integrity Protection feature. Although that sounds great, you really really really do not want to do this. This is part of the feature set that MacOS X uses to protect your system from malware, so disabling it is a bad idea. Do not go there nor even contemplate doing so.

The quickest solution therefore is to install the compiled ‘mod\_wsgi.so’ module in a different location that we can write to and setup the Apache httpd server to reference it from that location. To do that we need only override the location using the ‘make’ variable ‘LIBEXECDIR’ when we run ‘sudo make install’. For this example we will use the directory ‘/usr/local/httpd/modules’ instead of the default on MacOS X of ‘/usr/libexec/apache2’.

```bash
    $ sudo make install LIBEXECDIR=/usr/local/httpd/modules  
    Password:  
    mkdir -p /usr/local/httpd/modules  
    ./apxs -i -S LIBEXECDIR=/usr/local/httpd/modules -n 'mod_wsgi' src/server/mod_wsgi.la  
    /usr/share/httpd/build/instdso.sh SH_LIBTOOL='./libtool' src/server/mod_wsgi.la /usr/local/httpd/modules  
    ./libtool --mode=install install src/server/mod_wsgi.la /usr/local/httpd/modules/  
    libtool: install: install src/server/.libs/mod_wsgi.so /usr/local/httpd/modules/mod_wsgi.so  
    libtool: install: install src/server/.libs/mod_wsgi.lai /usr/local/httpd/modules/mod_wsgi.la  
    libtool: install: install src/server/.libs/mod_wsgi.a /usr/local/httpd/modules/mod_wsgi.a  
    libtool: install: chmod 644 /usr/local/httpd/modules/mod_wsgi.a  
    libtool: install: ranlib /usr/local/httpd/modules/mod_wsgi.a  
    libtool: install: warning: remember to run `libtool --finish /usr/libexec/apache2'  
    chmod 755 /usr/local/httpd/modules/mod_wsgi.so
```

Although the output from running this command shows a warning about running ‘libtool --finish’ you can ignore it. To be honest I am not actually sure how it even still knows about the directory ‘/usr/libexec/apache2’, but for MacOS X everything still works without doing that step.

With the mod\_wsgi module installed, in the Apache httpd server configuration file you would then use:

```
    LoadModule wsgi_module /usr/local/httpd/modules/mod_wsgi.so
```

rather than the normal:

```
    LoadModule wsgi_module libexec/apache2/mod_wsgi.so
```

This gets us beyond the System Integrity Protection problem caused by using MacOS X El Capitan. You would then configure and set up the Apache httpd server and mod\_wsgi for your specific WSGI application in the same way as you normally would.

# Using mod\_wsgi during development

Do note that if you only want to run mod\_wsgi during development, and especially if only on a non privileged port instead of the standard port 80, you are better off installing and using [mod\_wsgi-express](https://pypi.python.org/pypi/mod_wsgi).

The benefit of using mod\_wsgi-express is that it is easier to install, and gives you a command line program for starting it up, with the Apache httpd server and mod\_wsgi automatically configured for you.

To install mod\_wsgi-express on MacOS X you still need to ensure you have installed the Xcode command line tools as explained above, but once you have done that it is a simple matter of running:

```
    pip install mod_wsgi
```

Rather than the mod\_wsgi module being installed into your Apache httpd server installation, the module and ‘mod\_wsgi-express’ program will be installed into your Python installation. Hosting your WSGI application with mod\_wsgi can then be as simple as running:

```
    mod_wsgi-express start-server hello.wsgi
```

That mod\_wsgi-express installs into your Python installation makes it very easy to use mod\_wsgi with different Python installations, be they different Python versions or Python virtual environments, at the same time. You can therefore much more readily run mod\_wsgi for both Python 2 and Python 3 on the same system. Each mod\_wsgi-express instance is distinct and would need to run on different ports, but you can if need be use your main Apache httpd server installation as a proxy in front of these if needing to make both available on the standard port 80 at the same time.

For more information on mod\_wsgi-express check out the documentation on PyPi for the mod\_wsgi package or read the [blog post](/posts/2015/04/introducing-modwsgi-express/) where it was introduced. I have also posted [here](/posts/2015/06/proxying-to-python-web-application/) about proxying to instances of mod\_wsgi-express as well.