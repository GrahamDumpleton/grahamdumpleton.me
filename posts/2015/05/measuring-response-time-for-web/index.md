---
title: "Measuring response time for web requests in a WSGI application."
author: "Graham Dumpleton"
date: "Friday, May 15, 2015"
url: "http://blog.dscpl.com.au/2015/05/measuring-response-time-for-web.html"
post_id: "4029927534251797636"
blog_id: "2363643920942057324"
tags: ['decorators', 'python', 'wrapt', 'wsgi']
comments: 2
published_timestamp: "2015-05-15T19:00:00+10:00"
blog_title: "Graham Dumpleton"
---

The first topic I want to cover as part of my planned research for a possible upcoming PyCon talk titled '[Using benchmarks to understand how WSGI servers work](http://blog.dscpl.com.au/2015/05/using-benchmarks-to-understand-how-wsgi.html)' is how can one measure the response time of a web request being handled by a web application.

As far as benchmarks go this is usually done from the perspective of the tool used to generate the web requests. This is though a very gross value, incorporating not just the time spent in the WSGI application, but also network overheads and the time in any underlying or front end web server.

Although this is still a useful measure, it doesn't actually help you to identify where the time is being spent and as a consequence isn't particularly helpful for understanding whether you have configured the system in the best possible way to remove overheads.

As a first step in trying to get more fine grained timing information about where time is being spent for a web request, I want to look at what can be done to track the amount of time spent in the WSGI application itself.

# Timing of function calls

The obvious quick solution people reach for to track the amount of time spent in a function call in Python is to place a timing decorator on the function. The decorator would apply a wrapper which would remember at what time the function call started and then dump out how long it took when it exited.

Using the [wrapt](http://wrapt.readthedocs.org) package to create the decorator this could be implemented as:

> 
>     from __future__ import print_function
>     
>     
>     from wrapt import decorator  
>     > from timeit import default_timer
>     
>     
>     @decorator  
>     > def timed_function(wrapped, instance, args, kwargs):  
>     >     start = default_timer()  
>     >     print('start', wrapped.__name__)
>     
>     
>         try:  
>     >         return wrapped(*args, **kwargs)
>     
>     
>         finally:  
>     >         duration = default_timer() - start  
>     >         print('finish %s %.3fms' % (wrapped.__name__, duration*1000.0))

For this implementation we are using 'timeit.default\_timer\(\)' as the clock source as it will ensure we use as high a resolution clock as possible for a specific platform.

In the case of a WSGI application we could then apply this to the callable entry point.

> 
>     from timer1 import timed_function
>     
>     
>     @timed_function  
>     > def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = b'Hello World!'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         return [output]

Running this WSGI application with any WSGI server we would then get something like:

> 
>     start application  
>     > finish application 0.030ms

The time of 0.03 milliseconds for a 'Hello World\!' application seems to be in the right order of magnitude, but is the decorator truly sufficient. Lets test out a few more simple WSGI applications.

First up lets just add a 'sleep\(\)' call into the WSGI application. With the response time of our most simple of cases being so small, if we sleep for a sizeable amount of time, then that base overhead should be lost as noise within the longer sleep time.

> 
>     from timer1 import timed_function  
>     > from time import sleep
>     
>     
>     @timed_function  
>     > def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = b'Hello World!'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >         ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         sleep(1.0)
>     
>     
>         return [output]

Trigger a web request with this WSGI application and we get:

> 
>     start application  
>     > finish application 1000.653ms

And so the result is closer to the much longer sleep time as we expected.

If we take away the sleep time we end up with 0.653 milliseconds which does seem quite high compared to what we had previously. The reason for this though is likely to be the operating system overheads of waking up the process from its short sleep and resuming execution. The resulting time therefore is still reasonable.

Now in both these examples the WSGI application returned an iterable which was a list of strings. In other words the complete response was returned in one go after being generated up front.

Another way of writing a WSGI application is as a generator. That is, rather than returning all values at one time as a list, we yield each specific value making up the response. This allows the response to be generated as it is being returned.

> 
>     from timer1 import timed_function  
>     > from time import sleep
>     
>     
>     @timed_function  
>     > def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = b'Hello World!'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         sleep(1.0)
>     
>     
>         yield output

We again trigger a web request and the result this time is:

> 
>     start application  
>     > finish application 0.095ms

In this case we are back to a sub millisecond value again for time, so obviously there is a problem with our decorator in this case.

The problem here is that as the WSGI application is a generator function, the decorator is only timing how long it took for the Python interpreter to create the generator object. The time will not actually include the execution of any code within the generator function.

This is the case because the initial code in the function, including the 'sleep\(\)' call, will only be executed upon the first attempt to fetch a value from the generator object. This is something that will only be done by the WSGI server after the generator object has been returned and the wrapper applied by the decorator has also exited.

The traditional method of using a decorator with before and after actions executed either side of the call of the wrapped function will not therefore work for a WSGI application which is implemented as a generator function.

There are actually other situations besides a generator function which will also fail as there are in fact numerous ways that a WSGI application callable object can be implemented. Any scenario which defers work until the point when the iterable returned is being consumed will not yield the correct results with our first attempt at a timing decorator.

If interested in the various ways that WSGI application callable objects can be implemented, you can read a previous post I wrote on the topic called '[Implementing WSGI application objects](http://blog.dscpl.com.au/2011/01/implementing-wsgi-application-objects.html)'.

# Marking the end of a request

The solution to our problem with not being able to use a traditional function timing decorator can be found within the [WSGI](https://www.python.org/dev/peps/pep-3333/) protocol specification itself. Specifically it is stated in the specification:

> _If the iterable returned by the application has a close\(\) method, the server or gateway must call that method upon completion of the current request, whether the request was completed normally, or terminated early due to an application error during iteration or an early disconnect of the browser. \(The close\(\) method requirement is to support resource release by the application. This protocol is intended to complement PEP 342 's generator support, and other common iterables with close\(\) methods.\)_

What this means is that where the iterable from the WSGI application would otherwise be returned, we can instead return a wrapper object around that iterable and in our wrapper provide a 'close\(\)' method. This 'close\(\)' method is then guaranteed to be called at the end of the request regardless of whether it completes successfully or not.

We can therefore use this as the place for ending the timing of the request where the iterable was returned. One requirement in using such a wrapper though is that the wrapper itself must in turn call the 'close\(\)' method of any iterable which was wrapped to preserve any expectation it has that its own 'close\(\)' method is called.

> 
>     from __future__ import print_function
>     
>     
>     from wrapt import decorator, ObjectProxy  
>     > from timeit import default_timer  
>     >   
>     > class WSGIApplicationIterable1(ObjectProxy):
>     
>     
>         def __init__(self, wrapped, name, start):  
>     >         super(WSGIApplicationIterable1, self).__init__(wrapped)  
>     >         self._self_name = name  
>     >         self._self_start = start
>     
>     
>         def close(self):  
>     >         if hasattr(self.__wrapped__, 'close'):  
>     >             self.__wrapped__.close()
>     
>     
>             duration = default_timer() - self._self_start  
>     >         print('finish %s %.3fms' % (self._self_name, duration*1000.0))
>     
>     
>     @decorator  
>     > def timed_wsgi_application1(wrapped, instance, args, kwargs):  
>     >     name = wrapped.__name__
>     
>     
>         start = default_timer()  
>     >     print('start', name)
>     
>     
>         try:  
>     >         return WSGIApplicationIterable1(wrapped(*args, **kwargs), name, start)
>     
>     
>         except:  
>     >         duration = default_timer() - start  
>     >         print('finish %s %.3fms' % (name, duration*1000.0))  
>     >         raise

In the implementation of the wrapper for the WSGI application iterable I have used the 'ObjectProxy' class from the wrapt package. The 'ObjectProxy' class in this case acts as a transparent object proxy for whatever is wrapped. That is, any action on the proxy object will be performed on the wrapped object unless that action is somehow overridden in the proxy object. So in this case we have overridden the 'close\(\)' method to allow us to insert our code for stopping the timer.

This wrapper class could have been implemented as a standalone class without relying on the 'ObjectProxy' class from wrapt, however using 'ObjectProxy' from wrapt brings some benefits which will be covered in a subsequent blog post.

Using this new decorator our test example is:

> 
>     from timer1 import timed_wsgi_application1  
>     > from time import sleep
>     
>     
>     @timed_wsgi_application1  
>     > def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = b'Hello World!'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         sleep(1.0)
>     
>     
>         yield output

When a web request is now issued we get:

> 
>     start application  
>     > finish application 1000.593ms

This is now the result we are expecting.

Just to make sure that we are preserving properly the semantics for 'close\(\)' being called, we can use the test example of:

> 
>     from __future__ import print_function
>     
>     
>     from timer1 import timed_wsgi_application1  
>     > from time import sleep
>     
>     
>     class Iterable(object):  
>     >   
>     >     def __init__(self, output):  
>     >         self.output = output
>     
>     
>         def __iter__(self):  
>     >         return self
>     
>     
>         def next(self):  
>     >         try:  
>     >             return self.output.pop(0)  
>     >         except IndexError:  
>     >             raise StopIteration
>     
>     
>         def close(self):  
>     >         print('close')
>     
>     
>     @timed_wsgi_application1  
>     > def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = b'Hello World!'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         sleep(1.0)
>     
>     
>         return Iterable([output])

What is being done here is that rather than returning a list or using a generator function, we return an iterable implemented as a class object. This iterable object defines a 'close\(\)' method.

If we use this test example the result is:

> 
>     start application  
>     > close  
>     > finish application 1000.851ms

That 'close' is displayed means that when the WSGI server calls the 'close\(\)' method on the result from our WSGI application timing decorator, that we are in turn correctly then calling the 'close\(\)' method of the iterable that was originally returned by the WSGI application.

# Applying the timing decorator

We now have a timing decorator that can be applied to a WSGI application and which will correctly time from the start of when the WSGI application callable object was executed, until the point where all the response content had been written back to a client and any custom 'close\(\)' method of the iterable, if one exists, was called.

In the next few blog posts I will start applying this timing decorator to WSGI applications which do more than return just 'Hello World\!' to see if anything can be learned about the characteristics of the most popular WSGI servers being used under different use cases.

The intent of exploring the different use cases is to show why benchmarks using a single simple test case aren't sufficient to properly evaluate which WSGI server may be the best for you. Rely on such simple tests and you could well make the wrong choice and end up using a WSGI server that doesn't perform as well as alternatives for your specific use case.

---

## Comments

### Max Ludwig - May 16, 2015 at 2:23 AM

Is there any reason why Apache itself shouldn't do that?

### Graham Dumpleton - May 16, 2015 at 7:39 AM

@Max That isn't going to help if running gunicorn, uWSGI or Tornado. I will be exploring what monitoring capabilities some WSGI servers have built in, but this is intended to be applicable to any WSGI server. There are also other things about the interaction with the WSGI layer and web server that I also want to track which aren't readily obtained from information which may be recorded by the web server alone.

