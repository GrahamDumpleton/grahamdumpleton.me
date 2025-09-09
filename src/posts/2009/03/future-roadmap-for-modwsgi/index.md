---
layout: post
title: "Future roadmap for mod_wsgi."
author: "Graham Dumpleton"
date: "2009-03-19"
url: "http://blog.dscpl.com.au/2009/03/future-roadmap-for-modwsgi.html"
post_id: "4502197037710197272"
blog_id: "2363643920942057324"
tags: ['mod_python', 'mod_wsgi', 'python']
comments: 3
published_timestamp: "2009-03-19T20:30:00+11:00"
blog_title: "Graham Dumpleton"
---

Because of family commitments, progress on [mod\_wsgi](http://www.modwsgi.org/) has been slower than I would have liked for the past year. I have a bit more spare time these days, so time to talk a little about where I see mod\_wsgi going from here.

  


Up till now, the little time I have been able to spend on mod\_wsgi which hasn't been chewed up in answering questions on the mailing list and other forums, has been going towards mod\_wsgi version 3.0. This has mainly consisted of a lot of bug fixes and minor refinements, however there are also a few interesting new features, the main ones being described below.

  * Support for Python 3.0. Now support Python 3.0 based on proposed amendments to WSGI specification for this latest incarnation of Python. The mod\_wsgi package was the first major WSGI server to support Python 3.0, albeit that you have had to use it from the subversion repository. Just a pity that it seems it will be a while before any of the larger frameworks support Python 3.0.
  * User chroot environment. Specific daemon process groups can be delegated to run in the context of a chroot environment. Direct support for chroot environments by mod\_wsgi means that you do not have to run Apache as a whole in the chroot environment and you could support many WSGI applications running in different daemon process groups as different users each in their own chroot environment.
  * Ownership of WSGI script files. Enforce that the WSGI script files corresponding to a WSGI application delegated to a specific daemon process group, are owned by or are a member of a specific group. The permissions of the directory containing the WSGI script file are also checked to ensure they are consistent. This is an additional security measure that can be applied in the case where all WSGI scripts in a directory are being delegated to run in a daemon process as a specific user, to ensure that sloppy directory permissions don't allow arbitrary other users to place WSGI scripts in that directory and therefore have it run as a different user.
  * Chunked request content. This is not something that the WSGI specification actually allows, but if you are happy to step slightly outside of the WSGI specification you can support clients which use this feature of HTTP. This appears to becoming more and more important as some mobile phone devices are automatically using chunked request content on HTTP POST requests where data is greater than a certain size. At the moment WSGI applications are ham strung in not being able to support this unless the underlying WSGI adapter uses the rather hacky method of reading in the whole request up front, calculating the CONTENT\_LENGTH and passing it through as if it wasn't a chunked request.  

  * Internal web server redirection. For mod\_wsgi daemon mode, now support the CGI method of being able to return a HTTP 200 response with the Location header defined, to trigger an internal server redirection. The target URL in this case could be within the same Python web application, another web application, another web server proxied via the web server or a static file. The latter would give something akin to X-Sendfile, although actually more like nginx X-Accel-Redirect as the target is a URL and not a physical file.
  * Limits on processor CPU time. For mod\_wsgi daemon mode, this allows one to trigger an automatic restart of a daemon process when the accumulated CPU time used by the process exceeds a specified amount. The intent of providing this feature is as a fail safe to capture when a process may go berserk and starts chewing up processor time due to some programming error.
  * Override application error pages. For mod\_wsgi daemon mode, now allow any error response page returned by the WSGI application to be ignored and the default Apache error page, or any defined by Apache ErrorDocument directive, to be used instead. This is for where multiple applications, implemented in different systems or programming languages, are hosted and they must present error pages in the same style.
  * Authentication and HTTP headers. The HTTP headers are now available to authentication providers allowing them to qualify their behaviour based on information in the headers, such as cookies.
  * Preloading of WSGI applications. The process group and application group to which a WSGI application is to be delegated can now be defined as parameters to the WSGIScriptAlias directive. As a side effect of this, the WSGI script so designated will be preloaded automatically and do not have to separately use WSGIImportScript to preload it.

Although these have all been implemented and mod\_wsgi 3.0 is pretty well all ready to go, have decided at this point to first back port as many as possible of the bug fixes from mod\_wsgi 3.0 back to mod\_wsgi 2.X stream and release mod\_wsgi 2.4. This is to close off the mod\_wsgi 2.X stream with a stable version, given that many people don't like jumping up to a new major version due to the perception that it will introduce its own new problems.

  


Once mod\_wsgi 2.4 has been released, and last tidy up tasks related to mod\_wsgi 3.0 are completed, would expect mod\_wsgi 3.0 to follow not long after.

  


In respect of mod\_wsgi 3.0, we did have a bit of a discussion on the mailing list about whether to disable embedded mode in mod\_wsgi 3.0 by default and force that it be enabled to be used. The reasoning here was that on UNIX systems most people unknowingly use embedded mode without realising that in doing so they really should be tuning the Apache MPM settings to values more appropriate for fat Python web applications. This is necessary as the default MPM settings are more appropriate for PHP and static file serving and certainly not for Python web applications. Don't adjust things properly and you could see yourself suffering [memory issues and load spikes](/posts/2009/03/load-spikes-and-excessive-memory-usage/). So, the thought was that maybe disabling it by default may act as a good flag to people to say, 'do this and you better know what you are doing'. In the end, decided to leave it as is, because without also configuring daemon mode, they would just get an error message and most likely be more confused about what is going on.

  


What is really needed in order to be able to disable embedded mode, or get rid of it all together, is for daemon mode to support a means of dynamically creating daemon processes without the need for any up front configuration to specifically enable it. For example, the default might be that first time that WSGI application is triggered which is associated with a specific virtual host, that a daemon process be automatically started for that virtual host. If multiple WSGI applications are mounted under that same virtual host, they would execute within the context of different sub interpreters of that daemon process.

  


Such a feature along with other mechanisms for supporting transient daemon processes has been on the TODO list for a while and had originally wanted to include it in mod\_wsgi 3.0, but the lack of time meant I had to defer trying to implement it.

  


As such, one of the main tasks down for mod\_wsgi 4.0 is the ability to dynamically create daemon process groups based on some template or parameterised configuration definition. This may see a daemon process created for each virtual host as above, or maybe one for each authenticated user, with each of those daemon process groups automatically running under the account of that authenticated user. Obviously, lots of possibilities exist here, it just depends on how flexible one can make it and from where one draws the input values to fill out the parameterised parts of the configuration.

  


Originally the thought had been to just focus on that one task for mod\_wsgi 4.0, but some recent feedback from Doug Napoleone about some hacks he had done with mod\_wsgi to make it possible to host Python web applications where each used a different version of Python, rekindled some old plans I had for exactly that.

  


The problem to be solved here is that mod\_wsgi is compiled against a specific version of Python and so you are stuck using that one version of Python. If you wanted to use a newer version of Python, you would need to recompile mod\_wsgi and thus upgrade all the Python web applications you host to use the newer version of Python at the same time.

  


Obviously this is a big drawback in a shared environment, be it a university setting or a web hosting provider. This is in part why FASTCGI is still seen as a much better solution than mod\_wsgi for Python web hosting, ignoring even the fact that FASTCGI can also be used for other languages.

  


Now, in order to be able to support using multiple versions of Python, one has to do away with embedded mode. This is necessary as to make embedded mode reasonably efficient on memory and startup costs, one has to load the Python interpreter into the Apache parent process and first initialise it there. That way the Python interpreter is ready for use immediately after the Apache child server processes are forked. Having the Python interpreter linked in and initialised at such an early stage though prevents forked daemon processes from using different versions of Python.

  


Next issue is that mod\_wsgi as it is implemented now, uses the Apache parent process as the monitor process. That is, it is the Apache parent process from which daemon mode processes are directly forked. As such, it was also benefiting from Python being preinitialised in the Apache parent process.

  


What we would now need to do instead, is to separate out from the Apache parent process the function of creating and monitoring the daemon processes. To that end, a separate monitor process would be forked from the Apache parent process and it would be that process which would then in turn create the daemon processes.

  


Now that we have a separate monitor process, the whole linking in of and intialising of the Python interpreter can be delayed until the monitor process has been created. To support multiple versions of Python at the same time, we just create multiple monitor processes, one for each version of Python to be supported and with each loading up a specific instance of the mod\_wsgi code for that version of Python.

  


It is just then a matter of specifying which version of Python one wants to use for a specific daemon process group, and the appropriate monitor process would take on the responsibility for ensuring the daemon process is created and subsequently managed.  
  


Because it is problematic to support embedded mode at the same time as supporting the use of multiple versions of Python, the intent would thus be that mod\_wsgi 4.0 deliver two distinct Apache module variants. These will be the existing mod\_wsgi module and a new mod\_wsgid module.

  


The mod\_wsgi module would provide the same level of functionality as is currently provided, but with the addition of dynamically created daemon processes as explained above. It would be bound to a specific version of Python.

  


The mod\_wsgid module would only support daemon mode. Thus, no embedded mode and no ability to implement Apache authentication providers or group authorisation in Python. Using this version one would be able to use different versions of Python at the same time for different WSGI applications. This will be possible because the mod\_wsgid module wouldn't actually utilise any part of Python directly. Instead there would be companion plugin modules for each different version of Python. It would be these companion modules which would be loaded by the monitor process corresponding to the desired version of Python. Since nothing to do with Python would be done in the Apache parent process, the Apache child server processes would thus be a bit slimmer as a result. A default configuration would also exist which would automatically create a daemon process group for each virtual host using the version of Python designated as the primary version to be used. 

  


Note that mod\_wsgid and mod\_wsgi would not be able to be loaded into Apache at the same time, nor would mod\_python be able to be used at the same time as mod\_wsgid.

  


Because use of embedded mode is the more specialised case and daemon mode the preferred deployment scenario, the mod\_wsgid module would actually likely become the recommended module to use.

  


Now, if you think that is about as far as one could take mod\_wsgi then you would be wrong. For mod\_wsgi 5.0 would like to revisit embedded mode and look at adding in support for some of the features of mod\_python that mod\_wsgi doesn't provide. This would include looking at support for Apache input and output filters implemented using Python, plus exposing the internal Apache APIs for use by Apache style handlers.

  


A reasonable amount of work has already been done on creating SWIG bindings for Apache APIs but so far it looks like one would be better off using hand crafted bindings instead. This is what mod\_python does, but mod\_python doesn't really follow that closely the Apache APIs. Would prefer that the hand crafted bindings be SWIG like in the sense of being a much closer mapping of the actual C APIs. By doing this it would be much easier for people to apply any knowledge they have of the C APIs into their Python equivalents. At this point it is also unknown what is going to happen with SWIG and Python 3.0. It may just be easier to support hand crafted bindings for Python 2.X and Python 3.X at the same time.

  


So, that be the current vision of where mod\_wsgi is heading. This is by no means final and always open to suggestions. If you really want to get into a discussion about it, do suggest though using the [mod\_wsgi mailing list](http://groups.google.com/group/modwsgi?hl=en) hosted on Google Groups for that, rather than trying to use comments to this post to carry out a conversation.

---

## Comments

### Unknown - March 19, 2009 at 11:10 PM

thanks for you hard work\! I've start using the 2.x branch yesterday for a \(private beta\) small site using Django/virtualenv. Glad that the sys.path reordering patch have been backported. Works great so far

### genro - March 21, 2009 at 9:57 AM

Great post Graham. I have no words enough to say you a BIG thank you.

### Christian Joergensen - March 23, 2009 at 8:29 AM

I have great respect for your work. Keep it up :\)  
  
Regards,

