---
layout: post
title: "A Python interpreter is not created for each request in mod_python."
author: "Graham Dumpleton"
date: "2009-03-09"
url: "http://blog.dscpl.com.au/2009/03/python-interpreter-is-not-created-for.html"
post_id: "4053686739275841577"
blog_id: "2363643920942057324"
tags: ['mod_python', 'mod_wsgi', 'python']
comments: 17
published_timestamp: "2009-03-09T10:21:00+11:00"
blog_title: "Graham Dumpleton"
---

There are various myths about mod\_python floating around the net and it gets a bit annoying when one keeps seeing them posted again and again, especially when used to support some conjecture that some other system is so much better as a result. It gets more annoying though when they are posted on sites whose commenting feature doesn't work, or you have to jump through hoops to register for the site. As such, often one can't even correct the misconceptions and so the misinformation just keeps propagating and you can never kill it.

  


The latest instance of this is at [www.pypi.info](http://www.pypi.info/index.php?option=com_content&task=view&id=478&Itemid=0), and it isn't the first time I have seen this person making incorrect statements about mod\_python and how it works.

  


So, let me set the record straight on one such myth about mod\_python. That myth is that mod\_python creates a separate Python interpreter instance for each request. This is just not the case.

  


What actually happens is that the first time a request arrives for an application which hasn't yet been loaded, and which hasn't been marked to run in the main Python interpreter, is that a new sub interpreter is created. That sub interpreter is then persistent within that process though, not being destroyed until the process itself is destroyed. Any subsequent requests for that application are then handled within the context of that same sub interpreter which has already been created, so no new sub interpreter is created. Even when multithreading is used, all the request handler threads execute within the context of that one sub interpreter. So, neither is a separate sub interpreter created for each distinct request handler thread in the Apache thread pool, as is also sometimes claimed.

  


As to why that poster had the problems he had with mod\_python, they are more likely because of which Apache MPM was selected when Apache was compiled, as well as not changing the default MPM settings used. Especially with prefork MPM, the default settings are more appropriate for static file serving and PHP. If you do not change the default MPM settings as well as tweak HTTP keep alive settings to make them more appropriate for a large persistent Python web application, you will see load spikes and memory issues, especially when a system is put under load.

  


From what I have seen, the majority of people setting up mod\_python don't understand the need to change the default Apache configuration. It may well have been the case that back in time when mod\_python was somewhat newer that you didn't have to, but this is because back then Python web applications were typically much smaller and so didn't have significant start up times or use large amounts of memory. These days though they do, so you need to change how Apache is configured to have it perform adequately.

  


Now, can we please stop trying to do performance and memory usage comparisons if you don't know how to setup the systems being compared properly. :-\(

  


BTW, everything above also applies to mod\_wsgi when using embedded mode, as it is implemented in a similar manner to mod\_python. Because I'd rather not see these misconceptions about mod\_python transfers onto mod\_wsgi, I will blog later more about the real source of these load spikes and memory issues. In the mean time, if using mod\_wsgi use daemon mode and you will not have to think about it, as these issues in the main only relate to embedded mode.

---

## Comments

### Unknown - March 9, 2009 at 11:15 AM

That site is the same turkey who is selling "Django 2.0". His attempts at sowing name-brand confusion \(pypi.info?\!\) are legendary, too, unfortunately.  
  
Good to have this information laid out clearly, but there might be an argument for not feeding the trolls in the future for that particular site.

### Graham Dumpleton - March 9, 2009 at 12:31 PM

Oh, one of those sort of people. Always gets my goat up when people try and trade off of someone else's name and good work. I did notice the 'pypi' site name and thought they were going a bit far in thinking they could hijack it. Didn't know about them also using 'Django 2.0'.

### Unknown - March 9, 2009 at 12:56 PM

Yes that website really is a horrible hoax trying to exploit money out of naive people, I wish there was some way someone could shut them down.

### mike bayer - March 9, 2009 at 1:05 PM

and SalesForceAlchemy \! sites like these are for dummies, and you can't do much about them.

### Florian - March 9, 2009 at 7:01 PM

mod\_python still sucks because  
  
\- the build in module/function dispatch algorithm  
\- weird configuration  
\- need to re-configure from apache default  
\- fails to reload properly when configured thus \(which wouldn't matter if...\)  
\- poor hosting choices, apache only \(as opposed to wsgi which you run on apache and nginx as mod\_wsgi, on flup as fscgi, scgi or ajp, with wsgiref etc.\)  
\- random crashes  
\- inability to configure it to daemon mode \(as opposed to apache mod\_wsgi\) which prevents any sane shared hoster from offering it

### Graham Dumpleton - March 9, 2009 at 8:52 PM

@florian  
  
 _the build in module/function dispatch algorithm_  
  
Not sure exactly what you mean here. If you mean how it supplies both a low level handler mechanism and the high level publisher dispatch mechanism then would in part agree.  
  
I believe that mod\_python should have stopped at the low level handler mechanism and made it as simple as possible. All the other high level handlers such as publisher should have been done as a separate package with its own release schedule.  
  
Part of the problem with mod\_python is those high level handlers have added to mod\_python overall code size, plus some of the machinery to support them has been pushed down into the lower level handler causing a bit more in memory bloat, even though not used, that really should not exist, for those people who are only using the low level handler.  
  
_weird configuration_  
  
For the content handler phase, I believe the mistake in mod\_python was moving away from the more conventional CGI approach of using proper URL matching rules to match to a file based resource. Instead you give the name of a Python module as an entry point. This is bad in my mind as you have side stepped all the security mechanisms in Apache as far as controlling what file based resources can be served up by Apache. Also, by doing what it did and not using proper URL to resource based matching, there is no reliable way of determining what SCRIPT\_NAME should be for a WSGI application.  
  
That said, some of the Trac folks think how mod\_wsgi works, which is the CGI approach is a PITA as they can't just do everything in the Apache configuration file and instead must create a WSGI script file as the entry point and set up permissions properly on the directory such that it can be used.  
  
_need to re-configure from apache default_  
  
If you mean the need to change the default MPM settings then that isn't strictly mod\_python's fault, but the fault of the specific heavy weight Python applications that people try and run on top of it. In short, mod\_python came about when Python web applications were small, but now that they are much much bigger and have greater memory requirements. Thus, it isn't really possible any more to mix Python web applications and static file serving and PHP all on the one Apache server. I am writing a separate blog about that.  
  
_fails to reload properly_  
  
The module importer in mod\_python is not meant to provide automatic reload ability for all Python code. It is a misconception I have seen many people have. When you are using a high level framework or Python application such as Django or Trac, you may as well turn off mod\_python autoreload as it doesn't do anything for that case where entry point is a Python module on standard sys.path. The situation is not much different for mod\_wsgi embedded mode, although recently showed how on Windows at least one could implement automatic restarts for any code change.  
  
_poor hosting choices, apache only_  
  
If you bind code to the mod\_python specific API then yes, but no reason why you can't use a mod\_python/WSGI bridge and so it just becomes another WSGI hosting mechanism. Well, accept for the fact that SCRIPT\_NAME isn't correct and you have to manually set it.  
  
_random crashes_  
  
The reason for which most are understood and logged as issues, but because mod\_python has stagnated, the fixes haven't been implemented. At least learnt from the mistakes in mod\_python and didn't do the same thing in mod\_wsgi. Actually, most of the problems with mod\_python were worked out when implementing mod\_wsgi and seeing how the code in mod\_python was just broken.  
  
_inability to configure it to daemon mode \(as opposed to apache mod\_wsgi\) which prevents any sane shared hoster from offering it_  
  
My personal opinion is that any sane shared hoster shouldn't necessarily be offering shared hosting with mod\_wsgi just yet, well commodity shared hosting at least. At least, I wouldn't trust them to set it up as securely as possible, especially since how to do so isn't properly documented yet. Also, mod\_wsgi 2.X isn't as secure as it could be and mod\_wsgi 3.0 improves things in that area. Even so, for maximum security a certain architecture should be used which would involve not only Apache but a separate front end proxy and static file server such as nginx.  
  
At the moment, only web hosting company I would trust fully is WebFaction, as they give each user their own Apache for running the dynamic web applications. Any others I would be suspicious of for commodity web hosting. Managed application web hosting is a different matter.  
  
BTW, I have never once been approached by any web hosting company, at least not one that has been open about it, as to how to properly configure mod\_wsgi for any level of shared hosting. This in part shows how conservative they are in taking up new technology, but perhaps also shows a mistaken belief that they think they know what they are doing. Certainly I have heard some feedback from people who have talked to companies about using mod\_wsgi, and some of what the companies was saying was just utter nonsense and only showed they had no idea how mod\_wsgi or even mod\_python worked and how to use it properly.

### Florian - March 9, 2009 at 9:03 PM

@Graham  
  
so since you basically agree with the raised points, and add a few of your own like that mod\_python is kinda bloated and that its development is stagnant, why does it matter who spreads what kind of missinformation about it?  
  
The bottom line is nobody should use it.

### Graham Dumpleton - March 9, 2009 at 9:20 PM

@florian  
  
It matters because in some ways mod\_wsgi works very similar to mod\_python.  
  
If people think that mod\_python works in a certain way, when it doesn't, or that mod\_python has certain problems, which may not actually be its fault directly, then they will assume that the same applies to mod\_wsgi.  
  
This isn't fiction. I have already come across people doing exactly this, most out of ignorance, but a few who seemed to knowingly do it with the intention to cast mod\_wsgi as a broken solution as well because it competed with their own favoured solution.  
  
So, would rather like to just try and set the record straight a bit. Explaining how mod\_python works also helps people to understand mod\_wsgi at the same time.

### Graham Dumpleton - March 9, 2009 at 11:11 PM

@florian  
  
One final thing about what is getting labelled here as bloat in mod\_python. The extra stuff I am talking about represents at most 1MB of memory and it stays constant and doesn't increase over time. This amount isn't that much when Python web applications quite often are 30MB+ in size in their own right. In some cases the Python web applications would actually drag in the same code that mod\_python had already imported but which wasn't strictly needed for basic mod\_python use case.

### Florian - March 10, 2009 at 1:39 AM

@graham  
  
by bloat I'm largely refering to features nobody wants, but needs to configure and put up and that keep development of mod\_python up.

### Laurence Rowe - March 11, 2009 at 4:01 AM

@florian  
I much prefer mod\_wsgi in general, but mod\_python still has one feature that mod\_wsgi lacks: the ability to write apache filters in python.  
  
And as for the general statements on bloat... surely you have nginx and varnish in front of anything that serves a serious amount of traffic.

### Graham Dumpleton - March 11, 2009 at 7:51 AM

@laurence  
  
Python isn't particularly the best language for writing Apache input/output filters as the performance hit is quite significant. So, although it wouldn't be that hard to add support for writing input/output filters in Python, I am dubious about whether it is something that should be encouraged.  
  
If you haven't already had a discussion on mod\_wsgi list about what you are doing with input/output filters suggest you come other and we talk about it some more, especially with respect to what you are doing. This would be a really good time to revisit this issue as last opportunity to get something into mod\_wsgi 3.0.

### Graham Dumpleton - March 11, 2009 at 8:21 AM

@laurence  
  
Ahhh, but then I remembered all the other reasons why implementing Apache input/output filters in Python is bad. I'll try and blog about why mod\_wsgi is unlikely to support them and why in general Python is bad for implementing them. Even so, do still come over to the mod\_wsgi list if want to discuss it.

### Unknown - March 11, 2009 at 9:49 PM

Even though writing filters in python might not be optimal, they are hugely easier to do than implementing in C. The relevant Apache APIs are poorly documented, and there do not appear to be any useful examples you ca start from.  
  
After trying the C implementation for a while I switched to python and had an output filter up and running quickly.

### Graham Dumpleton - March 12, 2009 at 7:36 AM

That writing input/output filters in Python using mod\_python is easy I will accept. Part of my concerns though are that in making it so simple it has abstracted away too much and you have lost the ability to properly deal with the buckets in the underlying bucket brigade. The result is that although it may work in most cases, there seems to be a small subset where mod\_python may not be dealing with what comes down the bucket brigade properly and it fails in strange ways. In other words, it may not be a properly behaved filter implementation. Yes I realise this is an implementation detail and might be able to be solved, but it is just one of a number of issues I have with the existing mod\_python code.  
  
Anyway, as I said to previous poster, please come over to the mod\_wsgi list so we can have a proper discussion about it. I'll still entertain the idea of filters if I believe there is a reasonable set of use cases for it to make it worthwhile and that such use cases can actually work with mod\_wsgi and WSGI applications. Problem is that the way the WSGI interface works is that some input filters wouldn't be able to work with them. Specifically input filters that modify/add setenv variables or request headers upon first read are lost to WSGI because it takes a snapshot when application first entered. This is in contrast to mod\_python which allows access to original data all the time so if modified it can see it.  
  
So, at the moment I have people say that they want filter support, but no idea how you are using it and whether the use case is specific to an associated Python web application or being used in conjunction with non Python applications. Where associated with a specific Python web application, it is likely that it can just be done at the level of the WSGI application.

### Unknown - February 5, 2016 at 11:18 PM

Hello,  
Thanks for the article.  
I have the following question : my django app uses a python module I wrote. This module makes calls to a postgres DB \(which is not the DB used by the app for the model, it's an other DB\). Every time django receives a request, a new DB connection is created by this module, which is very time consuming. So I was wondering, if I run Apache in daemon mode and that all my python application stays loaded in memory, does it mean I can open a DB connection at the first call and then let it open ?  
  
something like \(pseudo code\):  
  
\#MyModule.py  
con = psycopg2.connect\(\)  
  
def foo\(query\):  
cur = con.cursor\(\)  
cur.execute\(query\)  
...  
return results  
  
\#views.py \(django app\)  
from MyModule import foo  
  
def bar\(request\):  
...  
res = foo\(someQuery\)  
...  
  
The only other solution I could think about was to have an external process running in the background with a pool of open connections, and making requests to this external process.  
Any advice will be much appreciated \!

### Graham Dumpleton - February 12, 2016 at 1:48 PM

@Francis You should ask your question on the mod\_wsgi mailing list, not here in a very old blog post. Also why aren't you using Django's builtin database support? It manages cursors for you and newer versions of Django support database connection pooling across requests. Followups to the mod\_wsgi mailing list, not here.

