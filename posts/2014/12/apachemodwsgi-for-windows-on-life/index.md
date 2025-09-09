---
title: "Apache/mod_wsgi for Windows on life support."
author: "Graham Dumpleton"
date: "Thursday, December 18, 2014"
url: "http://blog.dscpl.com.au/2014/12/apachemodwsgi-for-windows-on-life.html"
post_id: "3343458877052235082"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 5
published_timestamp: "2014-12-18T22:41:00+11:00"
blog_title: "Graham Dumpleton"
---

The critics will say that Apache/mod\_wsgi as a whole is on life support and not worth saving. I have a history of creating Open Source projects that no one much wants to use, or get bypassed over time, but I am again having lots of fun with Apache/mod\_wsgi so I don't particularly care what they may have to say right now.

I do have to say though, that right now it looks like continued support for the Windows platform is in dire straights unless I can get some help.

A bit of history is in order to understand how things got to this point.

First up, I hate Windows with an absolute passion. Always have and always will. Whenever I even try and use a Windows box it is like my whole body is screaming "stop, don't do it, this is not natural". My patience in having to use a Windows system is therefore very low, even when I can load it up with a decent shell and set of command line tools.

Even with my distaste for Windows I did at one point manage to get mod\_wsgi ported to Windows, this was possibly more luck than anything else. A few issues have come up with the Windows support over the years as new versions of Python came out, but luckily there were very few which were Windows specific and I could in the main blissfully ignore Windows and whatever I was doing on more familiar UNIX systems just worked. The Apache ecosystem and runtime libraries helped here a lot as they hid nearly everything about the differences between Windows and UNIX. It was more Python that I had to deal with the little differences.

All my development back then for mod\_wsgi on Windows was done with a 32 bit version of Windows XP. I did for a time make available precompiled binaries for two different Python versions, but only 32 bit and only for the binary distribution of Apache that the Apache Software Foundation made available at the time.

As 64 bit platforms came along I couldn't do much to help people and I also never tried third party distributions of Apache for Windows either. Luckily though someone who I don't even know stepped in and started making available [precompiled Windows binaries](http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi) for a range of Python and Apache versions for both 32 bit and 64 bit platforms. I am quite grateful for the effort they put in as it meant I could in the main ignore Windows and only have to deal with it when something broke because a new version of Python had come out.

Now a number of years ago I got into extreme burnout over my Open Source work and mod\_wsgi got neglected for a number of years. No big deal for users because mod\_wsgi had proven itself so stable over the years that it was possible to neglect it and it didn't cause anyone any problems.

When I finally managed to truly dig myself out of the hole I was in earlier this year I well and truly ripped into mod\_wsgi and started making quite a lot of changes. I made no attempt though to try and ensure that it kept working on Windows. Even the makefiles I used for Windows would no longer work as I finally started breaking up the large single monolithic source code file that was mod\_wsgi into many smaller code files.

To put in context how much I have been working on mod\_wsgi this year, in the 6 1/2 years up to the start of this year there had been about 20 separate releases of mod\_wsgi. In just this year alone I am already nearly up to 20 releases. The most recent release at this time is version 4.4.2.

So I haven't been idle, doing quite a lot of work on mod\_wsgi and doing much more frequent releases. Now if only the Linux distributions would actually bother to catch up, with some still shipping versions of mod\_wsgi from a number of years ago.

What this all means is that Windows support has been neglected for more than 20 versions and obviously a lot could have changed in that time in the mod\_wsgi source code. There has also been a number of new Python releases since the last time I even tried to build mod\_wsgi myself on Windows.

With the last version of mod\_wsgi for Windows available being version 3.5, the calls for updated binaries has been growing. My benefactor who builds the Windows binaries again stepped in and tried himself to get some newer builds compiled. He did manage this and started making them available.

Unfortunately the reports of a range of problems started to come in. These range from Apache crashing on start up or after a number of requests and also in some cases the Apache configuration to have requests sent through to Apache weren't even working.

Eventually I relented and figured I better try and sort it out. Just getting myself to a point where I could start debugging things was huge drama. First up my trusty old copy of Windows XP was too old to even be usable with current Microsoft tools required to compile code for Python. I therefore had to stoop to actually going out and buying a copy of Windows 8.1. That was a sad day for me.

Being the most recent version of Windows I would have thought the experience of setting things up would have improved over the years. Not so, it turned out to be even more aggravating. Just getting Windows 8.1 installed into a VM and applying all of the operating system patches took over 6 hours. Did I say I hated Windows.

Next I need to get the Microsoft compilers installed. Which version of these you need for Python these days appear to be documented in some dusty filing cabinet in a distant galaxy. At least I couldn't find it in an obvious place in the documentation, which was frustrating. Result was I wasted time installing the wrong version of Visual Studio Express only to find it wouldn't work.

So I work out I need to use Visual Studio Express 2008, but is there is an obvious link in the documentation of where to get that from. Of course not, or not that I could find and you have to go searching with Google and weeding out what are the dead links until you finally find the [right one](http://stackoverflow.com/a/15319069/128141).

I had been at this for a few days now.

Rather stupidly I thought I would ignore my existing makefiles for Windows and try and build mod\_wsgi using a Python 'setup.py' file like I have been doing with the 'pip' installable version for UNIX systems. That failed immediately because I had installed a 64 bit version of Python and distutils can only build 32 bit binaries using the Express edition of Visual Studio 2008. So I had to remove the 64 bit versions of Python and Apache and install 32 bit versions.

So I got distutils compiling the code, but then found I had to create a dummy Python module initialisation function that wasn't required on UNIX systems. I finally did though manage to get it all compiled and the one 'setup.py' file would work for different Python versions.

The joy was short lived though as Apache would crash on startup with every single Python version I tried.

My first suspicion was that it was the dreaded DLL manifest problem that has occasionally cropped up over the years.

The problem here is that long ago when building Python modules using distutils, it would attach a manifest to the resulting Python extension module which matched that used for the main Python binary itself. This meant that any DLL runtimes such as 'msvcr90.dll' would be explicitly referenced by the extension module DLL.

Some bright spark decided though that this was redundant and changed distutils to stop doing this. This would be fine so long as when using Python in an embedded system that the main executable, Apache in this instance, was compiled with the same compiler and so linked that runtime DLL.

When Apache builds started though to use newer versions of the Microsoft compilers Apache stopped linking that DLL. So right now the most recent Apache builds don't link 'msvcr90.dll'. The result therefore of distutils not linking that DLL any more meant the 'msvcr90.dll' DLL was missing when mod\_wsgi was loaded into Apache and it crashed.

I therefore went back to my previous makefiles. This actually turned out to be less painful than I was expecting and I even managed to clean up the makefiles, separating out the key rules into a common file with the version specific versions having just the locations of Apache and Python. I even managed to avoid needing to define where the Microsoft compilers were located, which varied depending on various factors. It did mean that to do the compilation you had to do it from the special Windows command shell you can startup from the application menus with all the compiled specific shell variables already set, but I could live with that.

Great, all things were compiling again. I even managed to use a DLL dependency walker to verify that 'msvcr90.dll' was being linked in properly so it would be found okay when mod\_wsgi was loaded into Apache.

First up I tried Python 2.7 and I was happy to see that it actually appeared to work. When I tried in turn Python 2.6, 3.2, 3.3 and 3.4 though, they either crashed immediately when initialising Python or when handling the first request.

I have tried for a while to narrow down where the problems are by adding in extra logging, but the main culprit is deep down in Python somewhere. Although I did actually manage to get the Microsoft debugger attached to the process before it crashed, because neither of the precompiled binaries for Apache and Python have debugging information, what one got was absolutely useless.

So that is where I am at. I have already wasted quite a lot of time on this and lack the patience but also the skills for debugging stuff on Windows. The most likely next step I guess would be to try and build up versions of Apache and Python from scratch with debugging symbols so that the exact point of the crashes can be determined. I can easily see that being an even larger time suck and so am not prepared to go there.

The end result is that unless someone else can some in and rescue the situation that is likely the end of Windows support for Apache/mod\_wsgi.

So summarising where things are at.

1\. I have multiple versions of Python installed on a Windows 8.1 system. These are python 2.6, 2.7, 3.2, 3.3 and 3.4. They are all 32 bit because getting Visual Studio Express to compile 64 bit binaries is apparently a drama in itself if using Python distutils, as one has to modify the installed version of distutil. I decided to skip on that problem and just use 32 bit versions. Whether having many versions of Python installed at the same time is a problem in itself I have no idea.

2\. I have both Visual Studio Express 2008 and 2012 installed. Again don't know whether having both installed at the same time will cause conflicts of some sort.

3\. I am using Apache 2.4 32 bit binaries from [Apache Lounge](http://www.apachelounge.com/download/). I haven't bothered to try and find older Apache 2.2 versions at this point.

4\. Latest mod\_wsgi version compiled from Python 2.7 does actually appear to work, or at least for the few requests I gave it.

5\. Use Python version 2.6, 3.2, 3.3 or 3.4 and mod\_wsgi will always crash on Apache startup or when handling the first request.

Now I know from experience that it is a pretty rare person who even considers whether they might be able to contribute to mod\_wsgi. The combination of Apache, embedding Python using Python C APIs, non trivial use of Python sub interpreters and multithreading seem to scare people away. I can't understand why, such complexity can actually be fun.

Anyway, I throw all this information out here in case there is anyone brave enough to want to help me out.

If you are, then the latest mod\_wsgi source code can be found on github at:

  * https://github.com/GrahamDumpleton/mod\_wsgi



The source code has a 'win32' subdirectory. You need to create a Visual Studio 2008 Command Prompt window and get yourself into that directory. You can then build specific Apache/Python versions by running:

```
    nmake -f ap24py33.mk clean

    nmake -f ap24py33.mk

    nmake -f ap24py33.mk install
```

Just point at the appropriate makefile.

The 'install' target will tell you what to add into the Apache configuration file to load the mod\_wsgi module after it has copied it to the Apache modules directory.

You can then follow normal steps for configuring a WSGI application to run with Apache, start up Apache and see what happens.

Have success and learn anything then jump on the [mod\_wsgi mailing list](https://groups.google.com/forum/#!forum/modwsgi) and let me know. We can see where we go from there.

Much thanks and kudos in advance to anyone who does try.

---

## Comments

### wmwdld - December 19, 2014 at 2:39 AM

Some notes:  
  
\- Python.org builds their binaries with VS2010 for version 3.3 and later, while VS2008 is used for 2.x and 3.0-3.2. That's documented [in the Python Developer's Guide](https://docs.python.org/devguide/setup.html#windows). Each major release of VS corresponds to a different version of the C runtime, e.g. VS2008 is MSVCRT9, VS2010 is MSVCRT10, VS2012 is MSVCRT11, and so on. These libraries are not ABI compatible, which means bad things will happen if you have two different versions loaded in the same executable \(e.g. trying to pass a FILE \* between MSVCRT9 and MSVCRT10 will likely result in a crash.\) If you're linking against the python27.lib or python33.lib or whatever from python.org, you have to use the corresponding VS version, i.e. using VS2012 is no good. And this applies to whatever version is being used to build Apache too. You can't mix and match versions at will. It appears that the apachelounge.com binaries are being built with VS2012, so that means that there is no combination that will work. For Python 2.x you will need to build Apache with VS2008, and for Python 3.3 and 3.4 you'll have to build Apache with VS2010. You can try building Python 2.x with VS2012 but I doubt that will work; see [Python bug \#13210](http://bugs.python.org/issue13210) for the effort that went into making 3.3 compatible with VS2010, which was not backported to 2.x.  
  
\- VS debug information for Python.org binaries is available at the site \(e.g. [here for 3.3](https://www.python.org/download/releases/3.3.0/#download).\)  
  
\- Back in September, Microsoft released a special version of VS2008 intended specifically for use with Python 2.x development. [Here's the download link](http://www.microsoft.com/en-us/download/details.aspx?id=44266). This should contain all the necessary platform headers for both 32 bit and 64 bit development.

### Piotr Dobrogost - December 19, 2014 at 2:55 AM

I think you might be interested to know that Microsoft has recently released "Microsoft Visual C++ Compiler for Python 2.7". According to Steve Dover from Microsoft, "this package contains all the tools and headers required to build C extension modules for Python 2.7 32-bit and 64-bit \(note that some extension modules require 3rd party dependencies such as OpenSSL or libxml2 that are not included\). Other versions of Python built with Visual C++ 2008 are also supported, so "Python 2.7" is just advertising - it'll work fine with 2.6 and 3.2." See https://mail.python.org/pipermail/distutils-sig/2014-September/024885.html for more details. I think Steve might be interested to help you out with your work on mod\_wsgi on Windows.

### Graham Dumpleton - December 19, 2014 at 1:54 PM

Thanks for the pointers. I was not aware that the mixing of the runtime DLLs was so strict with Python. On the ApacheLounge site for Apache, it talks about being able to mix some combinations of Apache modules compiled with different versions of the compiler. Anyway, being more careful now about which Apache version I am choosing, I seem to have working versions for Python 2.6, 2.7 and 3.2. I need to get down the correct compiler to try Python 3.3 yet, so that is next. Thanks.

### Graham Dumpleton - December 19, 2014 at 10:02 PM

Compiled binaries for all combinations targeting now appear to be working. Using mod\_wsgi mailing list volunteers to test out. Thanks again for the help.

### Graham Dumpleton - January 15, 2015 at 10:39 PM

Windows binaries for mod\_wsgi are now being made available at:  
  
https://github.com/GrahamDumpleton/mod\_wsgi/releases  
  
They will only be updated when a change is made in a release which affected Windows. So if not attached to the latest release, just go back and look for a prior release with them attached.  
  
Details of the Windows binaries can be found in:  
  
https://github.com/GrahamDumpleton/mod\_wsgi/blob/master/win32/README.rst

