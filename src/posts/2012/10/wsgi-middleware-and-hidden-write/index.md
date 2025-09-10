---
layout: post
title: "WSGI middleware and the hidden write() callable."
author: "Graham Dumpleton"
date: "2012-10-14"
url: "http://blog.dscpl.com.au/2012/10/wsgi-middleware-and-hidden-write.html"
post_id: "6369346180815684579"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 0
published_timestamp: "2012-10-14T23:17:00+11:00"
blog_title: "Graham Dumpleton"
---

When I posted recently about the [obligations of a WSGI server or middleware to call close\(\)](/posts/2012/10/obligations-for-calling-close-on/) on the iterable returned from a WSGI application, I posted a pattern for a WSGI middleware of:  
  
```  
class Middleware(object):

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        iterable = None

        try:
            iterable = self.application(environ, start_response)
            for data in iterable:
                yield data

        finally:
            if hasattr(iterable, 'close'):
                iterable.close()
```  
  
In this example, as each block of data was consumed from the iterable of the WSGI application, it was immediately yielded. The use of yield in turn caused the result returned from the '\_\_call\_\_\(\)' method to be a generator satisfying the requirement that a WSGI application or middleware return an iterable.  
  
This WSGI middleware will work for the specific case of response content being passed through unmodified, but things get a bit more complicated if it were wanting to actually modify the response content.  
  
Consider for example the following.  
  
```
class Middleware(object):

    def __init__(self, application):
        self.application = application

    def transform(self, data):
        return data.upper()

    def __call__(self, environ, start_response):
        iterable = None

        try:
            iterable = self.application(environ, start_response)
            for data in iterable:
                yield self.transform(data)

        finally:
            if hasattr(iterable, 'close'):
                iterable.close()
```
  
Although it looks entirely reasonable, this WSGI middleware is not correct.  
  
What is missing from this WSGI middleware is handling of the 'write\(\)' callable that is returned by 'start\_response\(\)' and which can be used as an alternative to returning data via the iterable returned from the WSGI application.  
  
If the above WSGI middleware was used to wrap a WSGI application which used that 'write\(\)' callable, then the response wouldn't actually be transformed as intended.  
  
Having to deal with the 'write\(\)' callable in WSGI middleware is a pain and unduly makes writing WSGI middleware potentially quite complicated as you need to track two data paths through the WSGI middleware. It is even possible that response content may be provided by both 'write\(\)' and via the iterable for the same request.  
  
A revised version of the WSGI middleware which supports the 'write\(\)' callable is:  
  
```  
class Middleware(object):

    def __init__(self, application):
        self.application = application

    def transform(self, data):
        return data.upper()

    def __call__(self, environ, start_response):

        def _start_response(status, response_headers, *args):
            write = start_response(status, response_headers, *args)
            def _write(data):
                write(self.transform(data))
            return _write

        iterable = None

        try:
            iterable = self.application(environ, _start_response)
            for data in iterable:
                yield self.transform(data)

        finally:
            if hasattr(iterable, 'close'):
                iterable.close()
```
 
That 'write\(\)' exists and how to deal with it in WSGI middleware which is transforming a response is often glossed over in tutorials on WSGI. It is somewhat lucky then that most people resort to using web frameworks because it would be a point which would be easy to get wrong with WSGI middleware being non compliant if not supported.  
  
Note that in this example the transformation being done does not modify the amount of data returned for the response. If the amount of data being returned is being modified then additional steps need to be taken to ensure a correct response. Options around what needs to be done where a WSGI middleware is changing the content length will be the subject of a future post.