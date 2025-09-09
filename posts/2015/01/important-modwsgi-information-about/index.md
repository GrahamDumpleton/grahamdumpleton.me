---
title: "Important mod_wsgi information about coming Apache httpd update."
author: "Graham Dumpleton"
date: "Tuesday, January 13, 2015"
url: "http://blog.dscpl.com.au/2015/01/important-modwsgi-information-about.html"
post_id: "5545546034876694523"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 1
published_timestamp: "2015-01-13T23:15:00+11:00"
blog_title: "Graham Dumpleton"
---

If you are using any of mod\_wsgi versions 4.4.0 through 4.4.5 ensure you read this post.

In the near future Apache httpd 2.4.11 is about to be released. This includes a change which if you upgrade the Apache web server, but don't do anything about mod\_wsgi, and you are using mod\_wsgi versions 4.4.0-4.4.5, will cause mod\_wsgi to crash if you are using daemon mode.

This is the case whether you have compiled mod\_wsgi for installation direct into the Apache web server installation, or if you are using the pip installable mod\_wsgi-express.

So the TLDR version is that if you are using any of the mod\_wsgi versions 4.4.0 through 4.4.5, be prepared to upgrade to mod\_wsgi 4.4.6 when released. Because of various trickery, the upgrade to mod\_wsgi 4.4.6 should be able to be done before hand, but must at the latest, and preferably, be done at the time of upgrading the Apache web server to 2.4.11.

# All the gory details

The trigger for needing to do this is that the Apache 2.4.11 web server adds changes related to CVE-2013-5704. These changes add additional members to the end of the key request\_rec structure, both changing the size of the structure, but also adding dependencies in parts of the web server on the new fields, including in the HTTP input filter used to read chunked request content.

In the past, changes to key web server structures have only been done at major/minor httpd version increments and not in patch level revisions. This works out okay as modules must be recompiled across major/minor versions as there are embedded version markers that prohibit a module compiled for Apache httpd 2.2 being used with Apache httpd 2.4. The web server will simply not load the module and will fail to start up if you try.

Within a specific major/minor version, when you compile a module, it is usually safe to keep upgrading the Apache web server and not have to recompile the module. This is because changes are always done through the addition of new APIs.

As the APIs can change over time and a module may want to use newer APIs, but still allow the module to be compiled for older versions of Apache, the code will check what is called the module magic number. This is a special number which is incremented each time there is an addition of a new API. By checking with this number a module can know at compile time what is and isn't available and if necessary fall back to older APIs, or not provide certain features based on newer APIs.

This therefore allows a module binary to be left as is as the Apache web server is upgraded as nothing is ever actually taken away. At the same time though, what you shouldn't do is use a module binary compiled for a new version of the Apache web server than the version you are running.

Anyway, the one place where this module magic number falls down is where additional fields are added to web server data structures and for some reason allocation of and initialisation of that data structure isn't done through an API call.

In practice this shouldn't ever be done, but due to a lack of a generic API for allocating the request\_rec structure to suit custom use cases, in order to implement aspects of mod\_wsgi daemon request processing, the request\_rec was being used directly and not via an API call.

The mod\_wsgi module isn't the only guilty party in this instance as there are a number of other third party modules for Apache which have had to use similar tricks due to APIs not being available. So luckily I am not all alone in this.

So this lack of an API for doing what was required has thus resulted in the current pickle, where because of the changes to the request\_rec structure, there is no alternative but to recompile mod\_wsgi from source code if you upgrade to Apache httpd 2.4.11 from an older version and are using mod\_wsgi 4.4.0-4.4.5.

It is believed only these mod\_wsgi versions are affected as the use of chunked encoding for request content sent between the Apache child worker processes and the mod\_wsgi daemon processes, was only added in mod\_wsgi version 4.4.0. With that change, the HTTP input filter will try and access the new structure members.

Technically if you are using older mod\_wsgi versions, you should also probably recompile as well, because the allocated request\_rec structure will now be too short, but so far it looks like that with older mod\_wsgi versions it is survivable because nothing will ever attempt to access the new structure members.

Now, as it turns out this change was already rolled out in Apache httpd 2.2.29 a few months ago but the problems resulting from it were not noticed. In practice this is because Linux distributions still using the older Apache web server, are also using an older mod\_wsgi version. So even if the change was back ported to the Apache web server provided by the Linux distribution, that an older mod\_wsgi was being used didn't cause an issue.

For those using more recent mod\_wsgi versions they are generally always using Apache httpd 2.4 and so this whole problem will only raise its ugly head when the same change is released in Apache httpd 2.4.11.

Important thing to note therefore is that you also need to be aware of this issue if you are using Apache httpd 2.2 and haven't yet updated to version 2.2.29. You will hit the same issue there and will also need to upgrade to mod\_wsgi version 4.4.6 if already using version 4.4.0-4.4.5.

# When will mod\_wsgi 4.4.6 be released?

The state of play right now is that the changes for mod\_wsgi 4.4.6 have been made, but I just want to recheck everything one last time before making an actual release. If you want to get ahead of things and also want to help me test the latest release, you can download it from the mod\_wsgi github repository at:

  * <https://github.com/GrahamDumpleton/mod_wsgi>



If you do try it and it works, or if you have issues, please let me know via the mod\_wsgi mailing list on Google Groups at:

  * <https://groups.google.com/forum/#!forum/modwsgi>



I will attempt to release version 4.4.6 of mod\_wsgi in the next day or so. Hopefully the Apache Software Foundation doesn't release the Apache web server update before I get a chance, but I haven't seen a definitive release date for it yet, so I should be good.

As to Linux distributions who are already shipping mod\_wsgi version 4.4.X, I don't actually believe there are many at this point. For the one I know about a back port of the minimal change to mod\_wsgi that is required is already being done. My understanding is that mention of the issue will be made in conjunction with the Apache web server release, so if you are using a binary Linux distribution and refuse to compile from source code yourself, hopefully the distributions will pick up that a change is required. The minimal code change required is:

  * <https://github.com/GrahamDumpleton/mod_wsgi/commit/808e9667fdddad16f94927b9f8ad947d56ea0071>



Note that if the code change for CVE-2013-5704 is being back ported to an older Apache web server version though, the C preprocessor condition check must not be included, as the module magic number when back porting would not be getting updated. Thus the only change should be:

> 
>      r->trailers_in = apr_table_make(r->pool, 5);  
>     >  r->trailers_out = apr_table_make(r->pool, 5);

What would be nice to see is Linux distributions simply pick up and use mod\_wsgi version 4.4.6, but I know I am dreaming on that, as they have a history of shipping out of date versions.

---

## Comments

### Graham Dumpleton - January 15, 2015 at 10:40 PM

Version 4.4.6 of mod\_wsgi has now been released. All releases can be found at:  
  
https://github.com/GrahamDumpleton/mod\_wsgi/releases

