---
title: "The mod_python project soon to be officially dead."
author: "Graham Dumpleton"
date: "Thursday, May 27, 2010"
url: "http://blog.dscpl.com.au/2010/05/modpython-project-soon-to-be-officially.html"
post_id: "850786034399276221"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_python', 'mod_wsgi']
comments: 11
published_timestamp: "2010-05-27T20:29:00+10:00"
blog_title: "Graham Dumpleton"
---

The [mod\_python](http://www.modpython.org/) project last had a release February 2007. There has more or less been no developer activity since. Under the rules of the Apache Software Foundation if a project becomes inactive then it can be moved into what is called the [Apache Attic](http://attic.apache.org/). Come the next meeting of the ASF board a proposed resolution will be put up to dissolve the Quetzalcoatl project management committee and projects which it overseas, namely mod\_python. Thus, in some respect one can say that mod\_python will be officially dead.

  


What will this really mean. Well, no more development on mod\_python, but then that isn't happening now. Linux distributions will likely still carry the package, but they will need to apply any changes themselves to ensure that it continues to work for newer versions of Apache. This actually is already being done as a bug in mod\_python was exposed by some changes to the Apache runtime library and since no mod\_python release has been made since then, only option was for distributions to patch it themselves.

  


I suspect though that this patching by distributions will only extend to Apache 2.2.X as Apache 2.4 changes the internal APIs enough that getting mod\_python to compile will need more significant changes than a minor patch. You also will never see a version of mod\_python for Python 3.X as that is going to require a radical rewrite.

  


For platforms like MacOS X where the last release of mod\_python doesn't build properly, the only option will be to checkout mod\_python source code from the subversion repository as that incorporates a fix for those issues, although it has since been shown to not be a complete fix and so you may still have some problems. In other words, the subversion repository will still exist, but it will be made read only and the location may potentially move.

  


What options exist if you want to move away from mod\_python?

  


If you are only using mod\_python as a means of hosting within Apache a distinct Python web framework or application and it supports the WSGI interface, then the obvious candidate is to move to [mod\_wsgi](http://www.modwsgi.org/) instead.

  


If you are using mod\_python to implement custom access, authentication or authorization handlers, then you may also be able to get away with using mod\_wsgi. You may have to make compromises though as mod\_wsgi doesn't currently allow you to write full blown Apache style handlers and instead only implements the Apache [authentication and authorization provider interfaces](http://code.google.com/p/modwsgi/wiki/AccessControlMechanisms). This actually makes it easier to do most things, but you loose the ability to do some more complicated stuff which depends on using different error status values or custom error pages. You can partly get away with using ErrorDocument directive to return custom error pages, but not always.

  


Although proper support for Apache style handlers could be added to mod\_wsgi, and a lot of work has been done in that direction already through the implementation of [SWIG bindings for Apache](http://bitbucket.org/grahamdumpleton/apswigpy), whether the remaining work to allow the actual hooking of handlers into mod\_wsgi will be done will really depend on interest in it. Up till now, there hasn't been sufficient interest to justify doing the final bit of work and there has actually been some resistance put up to the idea of extending mod\_wsgi too far beyond the core goal of providing WSGI hosting.

  


If you are not using the basic handler mechanisms of mod\_python and are instead using the CGI handler, the publisher handler or PSP handler, then there aren't really any options at this point except for rewriting your application on top of a WSGI framework. If you have to do such a rewrite, but like the low level that one works at when using mod\_python, then would strongly recommend you perhaps look at [Werkzeug](http://werkzeug.pocoo.org/) and [Flask](http://flask.pocoo.org/).

  


If you are using mod\_python input or output filters there simply isn't any replacement. Frankly though I always thought that writing input or output filters in mod\_python was a really bad idea. Yeah it may work, but it wouldn't exactly be efficient. You would be much better writing a proper Apache module in C to do what is required, certainly if performance is an issue.

  


Finally, the ability to use Python code with Apache server side include mechanism also has no real equivalent. But then, not sure anyone ever actually used that feature anyway. Something similar could possibly be implemented in mod\_wsgi but not sure there would really be a point. If you are only using ability to include Python code, you would be much better off using a proper templating system that works with a WSGI framework.

  


So, the writing is on the wall so to speak and if you are using mod\_python, you really should be starting to plan how to move away from it as eventually it will likely not be an option you can use if you want to keep up to date with Apache and/or Python.

  


Could it yet be saved by a white knight. Well, yes it could as the Apache Attic does allow projects to be resurrected or forked with it then being maintained outside of the ASF. If someone does do the latter though, you would need to be mindful of the name as the ASF in some respects has rights over the mod\_python name. As such, you would likely need to rename the project when you take it over.

  


If you fork mod\_python, you would also want to think about capturing all the details of the significant number of still open bug reports for mod\_python in its [issue tracker](https://issues.apache.org/jira/browse/MODPYTHON), as am not sure what will happen to that and whether it will be made read only or whether it will be completely closed down.

  


Anyway, will be interesting times ahead. I should point out though that according to [Google trends](http://www.google.com/trends?q=mod_python%2C+WSGI%2C+mod_wsgi) \(currently borked\), searches on WSGI finally overtook those for mod\_python recently. Searches for mod\_wsgi haven't yet, but not far off occuring. It is also the common belief that WSGI is the way to go for Python web applications now, so perhaps it is simply time to just move on from mod\_python. If we could only just get newbies, who even now keep using mod\_python even though better options exist, to understand this, then maybe it can finally be left to die in peace.

---

## Comments

### Brandon Rhodes - May 28, 2010 at 3:41 AM

Thanks for providing such a complete update on a historically very important Python effort, Graham\! Many of us first used Python with the web through experiments with mod\_python, and I am glad that the Apache Foundation provides a process for a project retiring, instead of the \(unfortunately\) more usual drop into oblivion that open source projects experience at the end of their lives.  
  
And, I hope that the explicitness of this process really helps push people over to the wonderful world of mod\_wsgi and its great features. Keep us updated\!

### Deron Meranda - May 28, 2010 at 4:02 AM

Graham, thanks for the informative post.  
  
I know I've discussed before; but I'm one \(of the few?\) who currently use and depend on many of the advanced Apache handler features that mod\_python provides. I'm still very interested in whether such things might make it into mod\_wsgi or some add-on; and also if there's anything I could possibly help with to make that work easier.

### Deron Meranda - May 28, 2010 at 4:05 AM

Oh, shouldn't your announcement also be sent to the mod\_python mailing list? I didn't see it \(or it hasn't shown up yet\). Thanks

### Jack Diederich - May 28, 2010 at 1:42 PM

I'm sad to see it go - I was a participant many moons ago and recall meeting Grisha at PyCon in DC; but happily it was retired because there are better alternatives.

### Unknown - May 30, 2010 at 4:54 PM

mod\_wsgi-- Is a better and more reliable option.   
  
In particular with Python-3.X on the horizon with 64 bit support its much easier to configure mod\_wsgi VS mod\_python.  
  
I this we must move on to support mod\_wsgi and help this community grow.

### patsplat - June 13, 2010 at 2:11 AM

Thanks for the clear and thoughtful post outlining the directions that python / apache development has taken.

### Unknown - June 20, 2010 at 9:19 AM

Session based clustering using mod\_wsgi.  
  
Friends: wanted to know how can we do session based clustering to scale the Python/mod-wsgi env, If I don’t want to use Apache clustering, load balancing or hardware based load balancing, is there any soln avilable, any help will be highly appreciate.  
  
If there is just nothing avilable can we are a group try to do it? I can contribute to the society as much as possible.

### Graham Dumpleton - June 20, 2010 at 10:55 AM

@Ruchir. Have you looked at Beaker? That provides session mechanisms for systems using WSGI interface.

### Unknown - June 20, 2010 at 11:23 AM

I will surly look into the details of Beaker, on the face of it, it looks like this is not the soln I am looking for, I am looking to cluster multiple nodes of django, and I don’t want to loose session while moving from one node to other, my customer must not know that the node has died. Is there a possibility of doing it with the existing stack?

### Graham Dumpleton - June 20, 2010 at 11:32 AM

Beaker can use a separate database that holds session information, it is not in memory only. If it were only in memory, then even a single Apache instance wouldn't work as most modes of Apache are multi process. If something supports multi process model, then shouldn't be any reason why the multiple processes cant be on different systems. The only caveat is that must be a database that can be accessed from remote nodes, ie., not sqlite for example.

### Unknown - June 21, 2010 at 10:56 AM

Appreciate your clarification,   
I will try it and let you know how it went.

