---
layout: post
title: "Installing a custom Python version into a Docker image."
author: "Graham Dumpleton"
date: "2015-06-26"
url: "http://blog.dscpl.com.au/2015/06/installing-custom-python-version-into.html"
post_id: "2363669552554753329"
blog_id: "2363643920942057324"
tags: ['docker', 'python']
comments: 9
published_timestamp: "2015-06-26T11:51:00+10:00"
blog_title: "Graham Dumpleton"
---

It is a growing problem with Linux distributions that many packages they ship quickly become out of date, and due to the policies of how the Linux distributions are managed, the packages do not get updates. The only hope for getting a newer version of a package is to wait for the next version of the Linux distribution and hope that they include the version of the package you do want.

In practice though, waiting for the next version of a Linux distribution is not something you can usually do, you have to go with what is available at the time, or even perhaps use an older version due to maturity or support concerns. Worse, once you do settle on a specific version of a Linux distribution, you are generally going to be stuck with it for many years to come.

The end result is that although you can be lucky and the Linux distribution may at least update a package you need with security fixes, if popular enough, you will be out of luck when it comes to getting bug fixes or general improvements to the package.

This has been a particular problem with major Python versions, the Apache web server, and also my own mod\_wsgi package for Apache.

At this time, many so called long term support \(LTS\) versions of Linux ship a version of mod\_wsgi which is in practice about 5 years old and well over 20 releases behind. That older version, although it may have received one security fix which was made available, has not had other bugs fixed which might have security implications, or which can result in excessive memory use, especially with older Apache versions.

The brave new world of Docker offers a solution to this because it makes it easier for users to install their own newer versions of packages which are important to them. It is therefore possible for example to even find official Docker images which provide Python 2.7, 3.2, 3.3 or 3.4, many more than the base Linux version itself offers.

The problem with any Docker image which builds its own version of Python however is whether when it is installed it has followed best practices as to the right way to install it which has been developed over the years for the official base Linux versions of the package. There is also the problem of whether all required libraries were installed that modules in the Python standard library actually require. If such libraries aren't present, then modules which require them will simply not be installed when compiling Python from source code, the installation of Python itself will not be aborted.

In this blog post I am going to cover some of the key requirements and configuration options which should be used when installing Python in a Docker image so as to make it align with general practice as to what is done by base Linux distributions.

Although this relates mainly to installing a custom Python version into a Docker image, what is described here is also relevant to service providers which provide hosting services for Python, as well as any specialist packages which provide a means to make installation of Python easier as part of some tool for managing Python versions and virtual environments.

I have encountered a number of service providers over the years which have had inferior Python installations which exclude certain modules or prevent the installation of certain third party modules, including the inability to install mod\_wsgi. Unfortunately not all service providers seem to care about offering options for users and are simply just wanting to make anything available so they can tick off Python from some list, but not really care how good of an experience they provide for Python users.

# Required system packages

Python is often referred to as 'batteries included'. This means that it provides a large number of Python modules in the standard library for a range of tasks. A number of these modules have a dependency on certain system packages being installed, otherwise that Python module will not be able to be installed.

This is further complicated by the fact that Linux distributions will usually split up packages into a runtime package and a developer package. For example, the base Linux system may supply the package allowing you to create a SQLite database and interact with it through a CLI, but it will not by default install the developer package which would allow you to build the 'sqlite3' package included in the Python standard library.

What the names of these required system packages are can vary based on the Linux distribution. Often people arrive at the list of what are the minimum packages which would need to be installed by a process of trial and error after seeing what Python packages from the standard library hadn't been installed when compiling Python from source code. A better way is to try and learn from what the Python version provided with the Linux distribution does.

On Debian we can do this by using the 'apt-cache show' command to list the dependencies for the Python packages. When we dig into the packages this way we find two key packages.

The first of these is the 'python2.7-stdlib' package. This lists the dependencies:

```
 Depends: libpython2.7-minimal (= 2.7.9-2),  
          mime-support,  
          libbz2-1.0,  
          libc6 (>= 2.15),  
          libdb5.3,  
          libexpat1 (>= 2.1~beta3),  
          libffi6 (>= 3.0.4),  
          libncursesw5 (>= 5.6+20070908),  
          libreadline6 (>= 6.0),  
          libsqlite3-0 (>= 3.5.9),  
          libssl1.0.0 (>= 1.0.1),  
          libtinfo5
```

Within the 'python2.7-minimal' package we also find:

```
 Depends: libpython2.7-minimal (= 2.7.9-2),  
          zlib1g (>= 1:1.2.0)
```

In these two lists it is the library packages which we are concerned with, as it is for those that we need to ensure that the corresponding developer package is installed so header files are available when compiling any Python modules which require that library.

The command we can next use to try and determine what the developer packages are is the 'apt-cache search' command. Take for example the 'zlib1g' package:

```
 # apt-cache search --names-only zlib1g  
 zlib1g - compression library - runtime  
 zlib1g-dbg - compression library - development  
 zlib1g-dev - compression library - development
```

The developer package we are interested in here is 'zlib1g-dev', which will include the header files we are looking for. We are not interested in 'zlib1g-dbg' as we do not need the debugging information for doing debugging with a C debugger, so we do not need versions of libraries including symbols.

We can therefore go through each of the library packages and see what we can find. For Debian at least, the developer packages we are after have a '-dev' suffix added to the package name in some form.

Do note though that the developer packages for some libraries may not have the version number in the package name. This is the case for the SSL libraries for example:

```
 # apt-cache search --names-only libssl  
 libssl-ocaml - OCaml bindings for OpenSSL (runtime)  
 libssl-ocaml-dev - OCaml bindings for OpenSSL  
 libssl-dev - Secure Sockets Layer toolkit - development files  
 libssl-doc - Secure Sockets Layer toolkit - development documentation  
 libssl1.0.0 - Secure Sockets Layer toolkit - shared libraries  
 libssl1.0.0-dbg - Secure Sockets Layer toolkit - debug information
```

For this we would use just 'libssl-dev'.

Running through all these packages, the list of developer packages we likely need to have installed in order to be satisfied that we can build all Python packages included as part of the Python standard library are:

```
 libbz2-1.0 ==> libbz2-dev  
 libc6 ==> libc6-dev  
 libdb5.3 => libdb-dev  
 libexpat1 ==> libexpat1-dev  
 libffi6 ==> libffi-dev  
 libncursesw5 ==> libncursesw5-dev  
 libreadline6 ==> libreadline-dev  
 libsqlite3-0 ==> libsqlite3-dev  
 libssl1.0.0 ==> libssl-dev  
 libtinfo5 ==> libtinfo-dev  
 zlib1g ==> zlib1g-dev
```

Having worked out what developer packages we will likely need for all the possible libraries that modules in the Python standard library may require, we can construct the appropriate command to install them.

```
 apt-get install -y libbz2-dev libc6-dev libdb-dev libexpat1-dev \  
     libffi-dev libncursesw5-dev libreadline-dev libsqlite3-dev libssl-dev \  
     libtinfo-dev zlib1g-dev --no-install-recommends
```

Note that we only need to list the developer packages. If the base Docker image we used for Debian didn't provide the runtime variant of the packages, the developer packages express a dependency on the runtime package and so they will also be installed. Although we want such hard dependencies, we don't want suggested related packages being installed and so we use the '--no-install-recommends' option to 'apt-get install'. This is done to cut down on the amount of unnecessary packages being installed.

Now it may be the case that not all of these may strictly be necessary as the Python module requiring them wouldn't ever be used in the types of applications that we may want to run inside of a Docker container, but once you install Python you can't add in any extra Python module from the Python standard library after the fact. The only solution would be to reinstall Python again. So it is better to err on the side of caution and add everything that the Python package provided with the Linux distribution lists as a dependency.

If you wanted to try and double check whether they are required by working out what Python modules in the standard library actually required them, you can consult the 'Modules/Setup.dist' file in the Python source code. This file lists the C based Python extension modules and what libraries they require to be available and linked to the extension module when compiled.

For example, the entry in the 'Setup.dist' file for the 'zlib' Python module, which necessitates the availability of the 'zlib1g-dev' package, is:

```
 #zlib zlibmodule.c -I$(prefix)/include -L$(exec_prefix)/lib -lz
```

# Configure script options

Having worked out what packages we need to install into the Linux operating system itself, we next need to look at what options should be supplied to the Python 'configure' script when building it from source code. For this, we could go search out where the specific Linux operating system maintains their packaging scripts for Python and look at those, but there is actually an easier way.

This is because Python itself will save away the options supplied to the 'configure' script and keep them in a file as part of the Python installation. We can either go in and look at that file, or use the 'distutils' module to interrogate the file and tell us what the options were.

You will obviously need to have Python installed in the target Linux operating system to work it out. You will also generally need to have both the runtime and developer variants of the Python packages. For Debian for example, you will need to have run:

```
 apt-get install python2.7 python2.7-dev
```

The developer package for Python is required as it is that package that contains the file in which the 'configure' args are saved away.

With both packages installed, we can now from the Python interpreter do:

```
 # python2.7  
 Python 2.7.9 (default, Mar 1 2015, 12:57:24)  
 [GCC 4.9.2] on linux2  
 Type "help", "copyright", "credits" or "license" for more information.  
 >>> from distutils.sysconfig import get_config_var  
 >>> print get_config_var('CONFIG_ARGS')
```

On Debian and Python 2.7 this yields:

```
 '--enable-shared' '--prefix=/usr' '--enable-ipv6' '--enable-unicode=ucs4'  
 '--with-dbmliborder=bdb:gdbm' '--with-system-expat' '--with-system-ffi'  
 '--with-fpectl' 'CC=x86_64-linux-gnu-gcc' 'CFLAGS=-D_FORTIFY_SOURCE=2 -g  
 -fstack-protector-strong -Wformat -Werror=format-security ' 'LDFLAGS=-Wl,-z,relro'
```

There are a couple of key options here to highlight and which need to be separately discussed. These along with their help descriptions from the 'configure' script are:

```
   --enable-shared ==>  Disable/enable building shared python library  
   --enable-unicode[=ucs[24]] ==> Enable Unicode strings (default is ucs2) 
```

# Shared Python library

When you compile Python from source code, there are three primary by products.

There are all the Python modules which are part of the standard library. These may be pure Python modules, or may be implemented as or using C extension modules. The C extension modules are dynamically loadable object files which would only be loaded into a Python application if required.

There is then the Python library, which contains all the code which makes up the core of the Python interpreter itself.

Finally, there is the Python executable itself, which is run on the main script file for your Python application or when running up an interactive interpreter.

For the majority of users, that there is a Python library is irrelevant, as that library would also be statically linked into the Python executable. That the Python library exists is only due to the needs of the subset of users who want to embed the Python interpreter into an existing application.

Now there are two ways that embedding of Python may be done.

The first is that the Python library would be linked directly with the separate application executable when it is being compiled. The second is that the Python library would be linked with a dynamically loadable object, which would then in turn be loaded dynamically into the separate application.

For the case of linking the Python library with the separate application, static linking of the library can be used. Where creating a dynamically loadable object which needs the Python library, things get a bit trickier as trying to link a library statically with a dynamically loadable object will not always work or can cause problems at runtime.

This is a problem which used to plague the mod\_python module for Apache many years ago. All Linux distributions would only ship a static variant of the Python library. Back then everything in the Linux world was 32 bit. For the 32 bit architecture at the time, static linking of the Python library into the dynamically loadable mod\_python module for Apache would work and it would run okay, but linking statically had impacts on the memory use of the Python web application process.

The issue in this case was that because it was a static library being embedded within the module and the object code also wasn't being compiled as position independent code, the linker had to do a whole lot of fix ups to allow the static code to run at whatever location it was being loaded. This had the consequence of effectively creating a separate copy of the library in memory for each process.

Even back then the static Python library was about 5-10MB in size, the result being that the web application processes were about that much bigger in their memory usage than they needed to be. This resulted in mod\_python getting a bit of a reputation of being a memory hog, when part of the problem was that the Python installation was only providing a static library.

I will grant that the memory issues with mod\_python weren't just due to this. The mod\_python module did have other design problems which caused excessive memory usage as well, plus Apache itself was causing some of it through how it was designed at the time or how some of Apache's internal APIs used by mod\_python worked.

On the latter point, mod\_wsgi as a replacement for mod\_python has learnt from all the problems mod\_python experienced around excessive memory usage and so doesn't suffer the memory usage issues that mod\_python did.

If using mod\_wsgi however, do make sure you are using the latest mod\_wsgi version. Those 5 year old versions of mod\_wsgi that some LTS variants of Linux ship, especially if Apache 2.2 is used, do have some of those same memory issues that mod\_python was effected by in certain corner cases. In short, no one should be using mod\_wsgi 3.X any more, use instead the most recent versions of mod\_wsgi 4.X and you will be much better off.

Alas, various hosting providers still use mod\_wsgi 3.X and don't offer a more modern version. If you can't make the hosting provider provide a newer version, then you really should consider moving to one of the newer Docker based deployment options where you can control what version of mod\_wsgi is installed as well as how it is configured.

Now although one could still manage with a static library back when 32 bit architectures were what was being used, this became impossible when 64 bit architectures were introduced.

I can't say I remember or understand the exact reason, but when 64 bit Linux was introduced, attempting to link a static Python library into a dynamically loadable object would fail at compilation link time. The cryptic error message you would get, suggesting some issue related to mixing of 32 and 64 bit code, would be along the lines of:

```
 libpython2.4.a(abstract.o): relocation R_X86_64_32 against `a local  
  symbol' can not be used when making a shared object; recompile with -fPIC  
  /usr/local/lib/python2.4/config/libpython2.4.a: could not read symbols: Bad value
```

This error derives from those fix ups I mentioned before to allow the static code to run in a dynamically loadable object. What was previously possible for just 32 bit object code, was now no longer possible under the 64 bit Linux systems of the time.

In more recent times with some 64 bit Linux systems, it seems that static linking of libraries into a dynamically loadable object may again be possible, or at least the linker will not complain. Even so, where I have seen it being done with 64 bit systems, the user was experiencing strange runtime crashes which went away when steps were taken to avoid static linking of the Python library.

So static linking of the Python library into a dynamically loadable object is a bad idea, causing either additional memory usage, failing at link time, or potentially crashing at run time. What therefore is the solution?

The solution here is to generate a shared version of the Python library and link that into the dynamically loadable object.

In this case all the object code in the Python library will be what is called position independent to begin with and so no fix ups are needed which cause the object code from the library to become process local. Being a proper shared library also now means that there will only be one copy of the code from the Python library in memory across the whole operating system. That is, all processes within the one Python web application will share as common memory space the object code.

That isn't all though, as any separate Python applications you start would also share that same code from the Python library in memory. The end result is a reduction in the amount of overall system memory used.

Use of a shared library for Python therefore enables applications which want to embed Python via a dynamically loadable object to actually work and has the benefits of cutting down memory usage by applications that use the Python shared library.

Although a better solution, when you compile and install Python from source code, the creation of a shared version of the Python library isn't the default, only a static Python library will be created.

In order to force the creation of a shared Python library you must supply the '--enable-shared' option to the 'configure' script for Python when it is being built. This therefore is the reason why that option was appearing in the 'CONFIG\_ARGS' variable saved away and extracted using 'distutils'.

You would think that since the providing of a shared library for Python enables the widest set of use cases for using Python, be they through running the Python executable directly, or by embedding, that this is the best solution. Even though it does work, you will find some who will deride the use of shared libraries and say it is a really bad idea.

The two main excuses I have heard from people pushing back on the suggestion of using '--enable-shared' when Python is being built are:

  * That shared libraries introduce all sorts of obscure problems and bugs for users.
  * That position independent object code from a shared library when run is slower.



The first excuse I find perplexing and actually indicates to a degree a level of ignorance about how shared libraries are used and also how to manage such things as the ability of an application to find the shared library at runtime.

I do acknowledge that if an application using a shared library isn't built properly that it may fail to find that shared library at runtime. This can come about as the shared library will only actually be linked into the application when the application is run. To do that it first needs to find the shared library.

Under normal circumstances shared libraries would be placed into special ordained directories that the operating system knows are valid locations for shared libraries. So long as this is done then the shared library will be found okay.

The problem is when a shared library is installed into a non standard directory and the application when compiled wasn't embedded with the knowledge of where that directory is, or if it was, the whole application and library where installed at a different location to where it was originally intended to reside in the file system.

Various options exist for managing this if you are trying to install Python into a non standard location, so it isn't a hard problem. Some still seem to want to make a bigger issue out of it than it is though.

As to the general complaint of shared libraries causing other obscure problems and bugs, as much as this was raised with me, they didn't offer up concrete examples to support that claim.

For the second claim, there is some technical basis to this criticism as position independent code will indeed run ever so slightly slower where it needs to involve calling of C code functions compiled as position independent code. In general the difference is going to be so minimal as not to be noticeable, only perhaps effecting heavily CPU bound code.

To also put things in context, all the Python modules in the standard library which use a C extension module will be affected by this overhead regardless, as they must be compiled as position independent code in order to be able to be dynamically loaded on demand. The only place therefore where this can be seen as an issue is in the Python interpreter core, which is what the code in the Python library implements. Thus the CPU bound code, would also need to principally be pure Python code.

When one talks about something like a Python web application however, there is going to be a fair bit of blocking I/O and the potential for code to be running in C extension modules, or even the underlying C code of an underlying WSGI server or web server, such as the case with Apache and mod\_wsgi. The difference in execution time between the position independent code of a shared library and that of a static library, in something like a web application, is going to be at the level of background noise and not noticeable.

Whether this is really an issue or just a case of premature optimisation will really depend on the use case. Either way, if you want to use Python in an embedded system where Python needs to be linked into a dynamically loadable object, you don't have a choice, you have to have a shared library available for Python.

What the issue really comes down to is what the command line Python executable does and whether it is linked with a shared or static Python library.

In the default 'configure' options for Python, it will only generate a static library so in that case everything will be static. When you do use '--enable-shared', that will generate a shared library, but it will also result in the Python executable linking to that shared library. This therefore is the contentious issue that some like to complain about.

Possibly to satisfy these arguments, what some Linux distributions do is try and satisfy both requirements. That is, they will provide a shared Python library, but still also provide a static Python library and link the static Python library with the Python executable.

On a Linux system you can verify whether the Python installation you use is using a static or shared library for the Python executable by looking at the size of the executable, but also by running 'ldd' on the executable to see what shared libraries it is dependent on. If statically linked, the Python executable will be a few MB in size and will not have a dependency on a shared version of the Python library.

```
 # ls -las /usr/bin/python2.7  
 3700 -rwxr-xr-x 1 root root 3785928 Mar 1 13:58 /usr/bin/python2.7
 
 
 # ldd /usr/bin/python2.7  
  linux-vdso.so.1 (0x00007fff84fe5000)  
  libpthread.so.0 => /lib/x86_64-linux-gnu/libpthread.so.0 (0x00007f309388d000)  
  libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f3093689000)  
  libutil.so.1 => /lib/x86_64-linux-gnu/libutil.so.1 (0x00007f3093486000)  
  libz.so.1 => /lib/x86_64-linux-gnu/libz.so.1 (0x00007f309326b000)  
  libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007f3092f6a000)  
  libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f3092bc1000)  
  /lib64/ld-linux-x86-64.so.2 (0x00007f3093aaa000)
```

Jump into the system library directory on a Debian system where using the system Python installation, we see however that a shared Python library does still exist even if the Python executable isn't using it.

```
 # ls -o libpython2.7.*  
 lrwxrwxrwx 1 root 51 Mar 1 13:58 libpython2.7.a -> ../python2.7/config-x86_64-linux-gnu/libpython2.7.a  
 lrwxrwxrwx 1 root 17 Mar 1 13:58 libpython2.7.so -> libpython2.7.so.1  
 lrwxrwxrwx 1 root 19 Mar 1 13:58 libpython2.7.so.1 -> libpython2.7.so.1.0  
 -rw-r--r-- 1 root 3614896 Mar 1 13:58 libpython2.7.so.1.0
```

Hopefully in this case then both sides of the argument are happy. The command line Python executable will run as fast as it can, yet the existence of the shared library still allows embedding.

Now in the case of Debian, they are doing all sorts of strange things to ensure that libraries are located in the specific directories they require. This is done in the Debian specific packaging scripts. The question then is whether providing both variants of the Python library can be easily done by someone compiling directly from the Python source code.

The answer is that it is possible, albeit that you will need to build Python twice. When it comes to installing Python after it has been built, you just need to be selective about what is installed.

Normally the process of building and installing Python would be to run the following in the Python source code.

```
 ./configure --enable-shared  
 make  
 make install 
```

Note that I have left out most of the 'configure' arguments just to show the steps. I have also ignored the issue of whether you have rights to install to the target location.

These commands will build and install Python but where a shared library for Python is used and where the Python executable will link the shared library.

If we want to have both a static and shared library and for the Python executable to use the static library, we can instead do:

```
 ./configure --enable-shared  
 make  
 make install  
   
 make distclean  
   
 ./configure  
 make  
 make altbininstall
```

What we are doing here is build Python twice, first with the shared library enabled and then with just the static library. In the first case we will install everything and setup a fully functional Python installation.

In the second case however, we will only trigger the 'altbininstall' target and not the 'install' target.

When the 'altbininstall' target is used, all that will be installed is the static library for Python and the Python executable linked with the static library. In doing this, the existing Python executable using the shared library will be overwritten by the static linked library.

The end result is a Python installation which is a combination of two installs. A shared library for Python for embedding, but also a statically linked Python executable for those who believe that the time difference in the execution of position independent code in the interpreter core is significant enough to be of a concern and so desire speed over anything else.

# Unicode character sets

The next option to 'configure' which needs closer inspection is the '--enable-unicode' option.

The name of the option is a bit misleading as Unicode support is these days always compiled into Python. What is being configured with this option is the number of bytes in memory which are to be used for each Unicode character. By default 2 bytes will be used for each Unicode character.

Although 2 bytes is the default, traditionally the Python installations shipped by Linux distributions will always enable the use of 4 bytes per Unicode character. This is why the option to 'configure' is actually '--enable-unicode=ucs4'.

Since Unicode will always be enabled by default, this option actually got renamed in Python 3.0 and is replaced by the '--with-wide-unicode' option. After the rename, the supplying of the option enables the use of 4 bytes, the same as if '--enable-unicode=ucs4' had been used.

The option disappears entirely in Python 3.3, as Python itself from that version will internally determine the appropriate Unicode character width to use. You can read more about that change in [PEP 393](https://www.python.org/dev/peps/pep-0393/).

Although Python can quite happily be built for either 2 or 4 byte Unicode characters prior to Python 3.3, the reason for using a Unicode character width the same as what the Python version supplied by the Linux distribution uses, is that prior to Python 3.3, what width was chosen affected the Python ABI.

Specifically, functions related to Unicode at the C code level in the Python library would be named with the character width embedded within the name. That is, the function names would embed the string 'UCS2' or 'UCS4'. Any code in an extension module would use a generic name, where the mapping to the specific function name was achieved through the generic name actually being a C preprocessor macro.

The result of this was that C extension modules had references to functions in the Python library that actually embedded the trait of how many bytes were being used for a Unicode character.

Where this can create a problem is where a binary Python wheel is created on one Python installation and then an attempt made to install it within another Python installation where the configured Unicode character width was different. The consequence of doing this would be that the Unicode functions the extension module required would not be able to be found, as they would not exist in the Python library which had been compiled with the different Unicode character width.

It is therefore important when installing Python to always define the Unicode character width to be the same as what would traditionally be used on that system for Python installations on that brand of Linux and architecture. By doing that you ensure that a binary Python wheel compiled with one Python installation, should always be able to be installed into a different Python installation of the same major/minor version on a similar Linux system.

For Linux systems, as evidenced by the default option of '--enable-unicode=ucs4' being used here with Python 2.7, wide Unicode characters are aways used. This isn't the default though, so the appropriate option does always need to be passed to 'configure' when run.

# Optional system libraries

How to determine what system packages for libraries needed to be installed was determined by looking at what packages were listed as dependencies of the system Python package. Of these there are two which technically are optional. These are the packages for the 'expat' and 'ffi' libraries.

The reason these are optional is that the Python source contains its own copies of the source code for these libraries. Unless you tell the 'configure' script by way of the '--with-system-expat' and '--with-system-ffi' options to actually use the versions of these libraries installed by the system packages, then the builtin copies will instead be compiled and used.

Once upon a time, using the copy of 'expat' bundled with the Python source code could cause a lot of problems when trying to use Python embedded within another application such as Apache. This was because Apache would link to and use the system package for the 'expat' library while Python used its own copy. Where this caused a problem was when the two copies of the 'expat' library were incompatible. The functions in the copy loaded by Apache could in some cases be used in preference to that built in to Python, with a crash of the process occurring when expected structure layouts were different between the two versions of 'expat'.

This problem came about because Python did not originally namespace all the functions exported by the 'expat' library in its copy. You therefore had two copies of the same function and which was used was dependent on how the linker resolved the symbols when everything was loaded.

This was eventually solved by way of Python adding a name prefix on all the functions exported by its copy of the 'expat' library so that it would only be used by the Python module for 'expat' which wrapped it. Apache would at the same time use the system version of the 'expat' library.

These days it is therefore safe to use the copy of the 'expat' library bundled with Python and the '--with-system-expat' option can be left out, but as the system version of 'expat' is likely going to be more up to date than that bundled with Python, using the system version would still be preferred.

The situation with the 'ffi' library is similar to the 'expat' library, in that you can either use the bundled version or the system version. I don't actually know whether the 'ffi' library has to contend with the same sorts of namespace issues. It does worry me that on a quick glance I couldn't see anything in the bundled version where an attempt was made to add a name prefix to exported functions. Even though it may not be an issue, it would still be a good idea to use the system version of the library to make sure no conflicts arise where Python is embedded in another application.

# Other remaining options

The options relating to the generation of a shared library, Unicode character width and system versions of libraries are the key options which you want to pay attention to. What other options should be used can depend a bit on what Linux variant is being used. With more recent versions of Docker now supporting IPV6, including the '--enable-ipv6' option when running 'configure' is also a good bet in case a user has a need for IPV6.

Other options may relate more to the specific compiler tool chain or hardware being used. The '--with-fpectl' option falls into this category. In cases where you don't specifically know what an option does, is probably best to include it.

Beyond getting the installation of Python itself right, being a Docker image, where space consumed by the Docker image itself is often a concern, one could also consider steps to trim a little fat from the Python installation.

If you want to go to such lengths there are two things you can consider removing from the Python installation.

The first of these is all the 'test' and 'tests' subdirectories of the Python standard library. These contain the unit test code for testing the Python standard library. It is highly unlikely you will ever need these in a production environment.

The second is the compiled byte code files with '.pyc' and '.pyo' extensions. The intent of these files is to speed up application loading, but given that a Docker image is usually going to be used to run a persistent service which stays running for the life of the Docker image, then these files only come into play once. You may well feel that the reduction in image size is more beneficial than the very minor overhead which would be incurred due to the application needing to parse the source code on startup, rather than being able to load the code as compiled byte code.

The removal of the '.pyc' and '.pyo' will no doubt be a contentious issue, but for some types of Python applications, such as web service, may be a quite reasonable thing to do.

---

## Comments

### Collin Anderson - June 27, 2015 at 2:20 AM

I saw the "--enable-unicode=ucs4" option on a docker image a few days ago and thought that seemed unnecessary. Now I know why. Thanks\!

### Piotr Dobrogost - July 21, 2015 at 10:23 PM

Very nice post especially as there's no much information available on this subject.  
  
It might be helpful to set RPATH by passing LDFLAGS="-Wl,-rpath," to configure script so that to prevent loading of wrong dynamic libs when invoking python without LD\_LIBRARY\_PATH set properly. Otherwise one might be surprised for instance to see system python being run after invoking freshly built python executable. This does not apply when python executable is compiled with static libraries of course \(which is the case described in the post\).

### Graham Dumpleton - July 21, 2015 at 10:41 PM

@Piotr You are quite correct. If I am building my own on Linux and not bothering with the static linking part and relying only on dynamic libraries, I will always set the environment variable 'LD\_RUN\_PATH' at compile time with the library directory location. I use the 'LD\_RUN\_PATH' environment variable rather than use 'LDFLAGS' as I have bad experiences in the distant past with trying to use linker flags, with it causing problems with existing linker flags already trying to set the RPATH. This may well not be an issue these days, but old habits die hard when you find a way that reliably works. :-\)

### Piotr Dobrogost - July 23, 2015 at 12:00 AM

Accidentally when compiling Python 2.7.10 after  
./configure --prefix /usr/local --enable-shared LDFLAGS="-Wl,-rpath,/usr/local/lib"  
I saw that the \_io module was not built \(\*\*\* WARNING: renaming "\_io" since importing it failed: build/lib.linux-x86\_64-2.7/\_io.so: undefined symbol: \_PyErr\_ReplaceException\). Setting LD\_RUN\_PATH instead of passing LDFLAGS resulted in the same error. Now the important thing is that I had previously configured Python 2.7.8 with prefix /usr/local and installed it. Retrying without -Wl,-rpath,/usr/local/lib fixed the problem. Alternatively removing files pertaining to python \(old Python 2.7.8\) from /usr/local/lib fixed the problem as well. I'm curious what was happening. It looks like passing LDFLAGS="-Wl,-rpath,/usr/local/lib" made something **during** build/link time use old shared libs of Python 2.7.8 from within /usr/local/lib instead of newly built ones.

### Graham Dumpleton - July 23, 2015 at 9:24 AM

Something like this may well be the catalyst for me using LD\_RUN\_PATH instead. From memory, when building Python with a shared library it uses an RPATH to the source directory itself using a relative path so it can find the shared library before it is installed. When you use LDFLAGS it may have been adding that for /usr/local/lib before that, so when trying to run the freshly built Python as part of the build process to do things, it is picking up the wrong, older, shared library and failing. I recollect that the new io subsystem may have been back ported to Python 2.7 in a minor patch revision and why the symbol is undefined in the older library. In other words, the LD\_RUN\_PATH is applied at a lower priority so to speak and so only gets checked after everything set up by LDFLAGS.

### Piotr Dobrogost - February 8, 2017 at 8:24 PM

Actually one should probably use $ORIGIN for rpath by default so that the compiled Python could be moved to any location afterwards and keep working. The only problem is that this might lead to problems like this one – https://github.com/pypa/virtualenv/issues/1015

### Graham Dumpleton - February 8, 2017 at 9:10 PM

@Piotr In the context of a Docker container at least, the need for having the Python installation be relocatable is probably unlikely to arise. :-\)

### Piotr Dobrogost - February 8, 2017 at 9:54 PM

I was trying to say that unless there are compelling reasons not to one should by \_default\_ use $ORIGIN. That this will not probably bring any value while inside Docker container is not that important. Think of it as a good habit similar as using rpath in the first place is also kind of good habit :\) It's similar to the question of “why bother with a virtualenv if I’m already in a container” – https://glyph.twistedmatrix.com/2015/03/docker-deploy-double-dutch.html. Also "Why people create virtualenv in a docker container?" – http://stackoverflow.com/q/29146792/95735

### Graham Dumpleton - February 8, 2017 at 10:13 PM

On the issue of using virtualenv in a Python container, it is actually very important to still use one if using a system Python installation, or one from a package collection such as Red Hat Software Collections for RHEL/CentOS. I have blogged about those issues in [/posts/2016/01/python-virtual-environments-and-docker/](/posts/2016/01/python-virtual-environments-and-docker/)  
  
As to always using $ORIGIN, I am just wary of using magic in the path resolution for shared libraries as have been burnt by various problems with that on MacOS X. I know that is not Linux and how it works is a bit different, but have learnt from such bad experiences that prefer explicit rather than dynamic. So for Docker at least would take opposite view that unless someone can show me a valid need for it, I wouldn't do it that way. Outside of Docker, it may well be valid, especially for people who manage Python installation and packaging themselves to deploy out to their own hosts.

