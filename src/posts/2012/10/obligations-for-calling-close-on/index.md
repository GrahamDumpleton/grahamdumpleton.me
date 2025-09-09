---
layout: post
title: "Obligations for calling close() on the iterable returned by a WSGI application."
author: "Graham Dumpleton"
date: "2012-10-11"
url: "http://blog.dscpl.com.au/2012/10/obligations-for-calling-close-on.html"
post_id: "1240502205809946291"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 7
published_timestamp: "2012-10-11T14:56:00+11:00"
blog_title: "Graham Dumpleton"
---

Despite the [WSGI](http://www.python.org/dev/peps/pep-3333/) specification having been around for so long, one keeps seeing instances where it is implemented wrongly. At [New Relic](http://newrelic.com/) where I work on the Python agent, we have been caught by this a number of times. The problem is that if people don't implement a WSGI server or WSGI middleware per the requirements of the specification, our Python agent for web application performance monitoring will not always work as intended.  
  
This is especially the case in relation to the obligations of a WSGI server or WSGI middleware to call the close\(\) method, if it exists, on the iterable object returned by the WSGI application. This caused us ongoing issues for a while with uWSGI, but we worked with Roberto, the uWSGI author, and managed to get the issues resolved, finally being completely fixed \(we hope\) in uWSGI 1.2.6.  
  
The next notable example we ran up against where a major package isn't implementing the WSGI specification correctly is Raven, the Python client for Sentry. We have reported this to David, the Sentry author, but since there is some confusion about what the code should be doing, I am going to use it as an example to explain what the obligations of a WSGI middleware are in relation to the close\(\) method, hopefully so I don't have to keep explaining it.  
  


####  What Raven currently does wrong.

  
The current code for the Sentry client in Raven is:  
  
  
class Sentry\(object\):  
"""  
A WSGI middleware which will attempt to capture any  
uncaught exceptions and send them to Sentry.  
  
```python
>> from raven.base import Client  
>> application = Sentry\(application, Client\(\)\)  
```
"""  
def \_\_init\_\_\(self, application, client\):  
self.application = application  
self.client = client  
  
def \_\_call\_\_\(self, environ, start\_response\):  
try:  
for event in self.application\(environ, start\_response\):  
yield event  
except Exception:  
exc\_info = sys.exc\_info\(\)  
self.handle\_exception\(exc\_info, environ\)  
exc\_info = None  
raise  
  
def handle\_exception\(self, exc\_info, environ\):  
event\_id = self.client.capture\('Exception',  
exc\_info=exc\_info,  
data=\{  
'sentry.interfaces.Http': \{  
'method': environ.get\('REQUEST\_METHOD'\),  
'url': get\_current\_url\(environ, strip\_querystring=True\),  
'query\_string': environ.get\('QUERY\_STRING'\),  
\# TODO  
\# 'data': environ.get\('wsgi.input'\),  
'headers': dict\(get\_headers\(environ\)\),  
'env': dict\(get\_environ\(environ\)\),  
\}  
\},  
\)  
return event\_id  
  
  
The reason this code is wrong is because it does not satisfy the following requirement from the WSGI specification:  


> """If the iterable returned by the application has a close\(\) method, the server or gateway must call that method upon completion of the current request, whether the request was completed normally, or terminated early due to an application error during iteration or an early disconnect of the browser."""

What is not entirely clear in the language used here, specifically there only being a reference to 'the server or gateway', is that this obligation extends to WSGI middleware as well.  
  
In other words, although a server or gateway must ensure that close\(\) is called on the iterable returned by the application, a WSGI middleware must also ensure that it does the same for any iterable it may consume from a wrapped WSGI application or component.  
  
The code:  
  
  
for event in self.application\(environ, start\_response\):  
yield event  
  
  
is therefore incomplete, because although it consumes the iterable returned by the wrapped WSGI application, it does not ensure close\(\) is called on it upon completion, or in the event of any errors.  
  


####  Pattern for a generic WSGI middleware.

  
There are numerous ways one can structure a WSGI middleware, but following the general pattern used by Raven, a WSGI middleware that does ensure that close\(\) is called would be implemented as follows.  
  
  
class Middleware1\(object\):  
  
def \_\_init\_\_\(self, application\):  
self.application = application  
  
def \_\_call\_\_\(self, environ, start\_response\):  
iterable = None  
  
try:  
iterable = self.application\(environ, start\_response\)  
for data in iterable:  
yield data  
  
finally:  
if hasattr\(iterable, 'close'\):  
iterable.close\(\)  
  
  
Important to note here is that the act of calling the wrapped application to obtain the iterable has been separated from the process of iterating over it. This is necessary in order that we have a reference to the iterable to call close\(\) in the three cases necessary, they being an exception occurring when the actual iterator object itself is being created from the iterable object, if an exception occurs when getting the next item from the iterator object and finally upon the last item being yielded from the iterator.  
  
Now because WSGI middleware weren't specifically mentioned in the requirement, it does open up a slight grey area. The problem is the statement:  


> """must call that method upon completion of the current request"""

The intent of that statement, at least from the perspective of the WSGI server, is that close\(\) only be called once all content has been consumed from the iterable and that content has been sent to the client.  
  
For a WSGI middleware written as above, that isn't necessarily the point at which it would be called. Instead the close\(\) method would get called when the 'for' loop has completed. We have therefore lost any direction association between when close\(\) is called by the WSGI server itself upon actual completion of the request and when it is called by the WSGI middleware.  
  
Overall, for WSGI middleware it probably isn't a critical issue and having it called immediately the 'for' loop exits is fine. If it were important that close\(\) be directly chained, then it would be necessary to implement it differently, instead using.  
  
  
class Iterable2\(object\):  
  
def \_\_init\_\_\(self, iterable\):  
self.iterable = iterable  
if hasattr\(iterable, 'close'\):  
self.close = iterable.close  
  
def \_\_iter\_\_\(self\):  
for data in self.iterable:  
yield data  
  
class Middleware2\(object\):  
  
def \_\_init\_\_\(self, application\):  
self.application = application  
  
def \_\_call\_\_\(self, environ, start\_response\):  
return Iterable2\(self.application\(environ, start\_response\)\)  
  
  
That way the close\(\) method is only called for the iterable returned from the wrapped application when close\(\) is called by the WSGI server, or any further WSGI middleware that wraps this one.  
  
Requiring two classes like this does complicate the implementation of the WSGI middleware however, because both may need to track state for the current request as the iterable is consumed.  
  


####  Correcting the Sentry client in Raven.

  
Assuming the first pattern for implementing the WSGI middleware is okay, the existing Sentry client in Raven would be rewritten as follows.  
  
  
class Sentry\(object\):  
  
def \_\_init\_\_\(self, application, client\):  
self.application = application  
self.client = client  
  
def \_\_call\_\_\(self, environ, start\_response\):  
iterable = None  
  
try:  
iterable = self.application\(environ, start\_response\)  
for event in iterable:  
yield event  
  
except Exception:  
exc\_info = sys.exc\_info\(\)  
self.handle\_exception\(exc\_info, environ\)  
exc\_info = None  
raise  
  
finally:  
if hasattr\(iterable, 'close'\):  
iterable.close\(\)  
  
def handle\_exception\(self, exc\_info, environ\):  
...  


  


  
This provides the same functionality as it originally performed, but also ensures the close\(\) method is called correctly if the iterable provides one.  
  
We are not done though, because technically an exception could be raised by the close\(\) method when it is called. Presumably it would be desirable for this also to be captured and reported to Sentry. The more complete solution which does this is:  
  
  
class Sentry\(object\):  
  
def \_\_init\_\_\(self, application, client\):  
self.application = application  
self.client = client  
  
def \_\_call\_\_\(self, environ, start\_response\):  
iterable = None  
  
try:  
iterable = self.application\(environ, start\_response\)  
for event in iterable:  
yield event  
  
except Exception:  
exc\_info = sys.exc\_info\(\)  
self.handle\_exception\(exc\_info, environ\)  
exc\_info = None  
raise  
  
finally:  
if hasattr\(iterable, 'close'\):  
try:  
iterable.close\(\)  
except Exception:  
exc\_info = sys.exc\_info\(\)  
self.handle\_exception\(exc\_info, environ\)  
exc\_info = None  
raise  
  
def handle\_exception\(self, exc\_info, environ\):  
...  


  


  


####  Check what your WSGI middleware does.

  
So are you implementing your WSGI middleware correctly?

---

## Comments

### Rog - October 14, 2012 at 2:11 PM

Thanks for inestigating and explaining this Graham. As a New Relic, uWSGI and Sentry user, it's good to see collaboration on getting them all working together.  
  
For everyone's reference, it looks like David has committed a change for Raven in response to this...  
https://github.com/getsentry/raven-python/commit/eb6171a24819e16c8e2ba391a3e95c882d7ccbe2\#raven/middleware.py

### Piotr Dobrogost - October 15, 2012 at 6:52 AM

Graham, have you spoken with P.J. Eby, author of PEP 333, asking if close\(\) should be chained or if it can be called by middleware directly?

### Graham Dumpleton - October 15, 2012 at 9:40 AM

PJE is by no means the authority on this. Unless things have changed, he has over recent years not been doing a great deal in the area of Python web frameworks. I can think of a bunch of other Python web developers who are likely to be in a much better position to comment.  
  
It also isn't like the pros and cons of each aren't understood. If close\(\) is used for resource management, having it called as early as possible after the iterable is consumed is better. If however you are relying on close\(\) as a means for performing timing of the complete request for performance monitoring, then requiring close\(\) be chained is preferable. This is because if the timing middleware is wrapped and the wrapper doesn't chain, the results will not be as accurate. Although, unless the wrapper is doing something really odd, the difference in timing is likely to be negligible and so insignificant.  
  
Overall, because close\(\) is so rarely used to actually do anything, the issue would only be of interest to a very small number of people. So it is one of those little details worth noting but that can be ignored for now. If however there were ever a significant update to WSGI it could could be addressed then. I have already given my ideas for how to get rid of close\(\) in its current form at the Python web session prior to PyCon this year.

### Piotr Dobrogost - October 15, 2012 at 9:37 PM

"PJE is by no means the authority on this." Well, I still think it would be valuable to have input from author of the standard you interpret - I notified PJE about your post. Nevertheless thanks for taking time to write detailed comment.

### Unknown - October 19, 2012 at 9:51 AM

Is this a situation where using a context manager would enable the code to be cleaner?

### Graham Dumpleton - October 19, 2012 at 11:25 AM

My suggestion back when talked about future of WSGI at workshop prior to PyCon US this year, was to employ context manager semantics as alternative. This got rid of close\(\) as it exists now, but via enter/exit of a context manager allowed for both before and after actions. I will need to try and find out if there is video somewhere and get my slides up on SlideShare.

### Graham Dumpleton - October 20, 2012 at 12:26 PM

Slides for my talk about state of WSGI 2 and ideas about changing it, including eliminating close\(\) can be found at http://www.slideshare.net/GrahamDumpleton/pycon-us-2012-state-of-wsgi-2-14808297

