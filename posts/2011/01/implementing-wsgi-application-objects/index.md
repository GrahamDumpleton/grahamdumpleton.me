---
title: "Implementing WSGI application objects."
author: "Graham Dumpleton"
date: "Wednesday, January 5, 2011"
url: "http://blog.dscpl.com.au/2011/01/implementing-wsgi-application-objects.html"
post_id: "6898389764552731751"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 4
published_timestamp: "2011-01-05T15:53:00+11:00"
blog_title: "Graham Dumpleton"
---

Per the WSGI specification, an application object used as the entry point for requests is described as follows:  
  
"""The application object is simply a callable object that accepts two arguments. The term "object" should not be misconstrued as requiring an actual object instance: a function, method, class, or instance with a \_\_call\_\_ method are all acceptable for use as an application object."""  
  
Because I am doing something where I need to work with all the possible types of application objects and so needed some examples for testing, but also because sometimes newbies get a bit confused about what this means in practice, I thought it worthwhile documenting some examples of the different types of WSGI application objects.  
  
First though just to expand a bit on what the inputs and outputs to the application object are for each request, I’ll quote a few other sections of the WSGI specification. I am using PEP 3333 for the quotations in case you find it differs slightly from PEP 333 that preceded it. Some parts of the paragraphs quoted have been omitted.  
  
"""The application object must accept two positional arguments. For the sake of illustration, we have named them environ and start\_response, but they are not required to have these names. A server or gateway must invoke the application object using positional \(not keyword\) arguments. \(E.g. by calling result = application\(environ, start\_response\) as shown above.\)  
  
The environ parameter is a dictionary object, containing CGI-style environment variables. This object must be a builtin Python dictionary \(not a subclass, UserDict or other dictionary emulation\).  
  
The start\_response parameter is a callable accepting two required positional arguments, and one optional argument. For the sake of illustration, we have named these arguments status, response\_headers, and exc\_info, but they are not required to have these names, and the application must invoke the start\_response callable using positional arguments \(e.g. start\_response\(status, response\_headers\)\).  
  
When called by the server, the application object must return an iterable yielding zero or more bytestrings. This can be accomplished in a variety of ways, such as by returning a list of bytestrings, or by the application being a generator function that yields bytestrings, or by the application being a class whose instances are iterable. Regardless of how it is accomplished, the application object must always return an iterable yielding zero or more bytestrings."""  
  
So, that sets the scene of what to expect, now for the examples.  
  
The simplest example is where the application object is a function. For this case we would have:
    
    
    def application(environ, start_response):  
        status = '200 OK'   
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)   
              
        return ["1\n", "2\n", "3\n", "4\n", "5\n"]

The result returned must be an iterable yielding zero or more byte strings. Here we have used a list but as the specification outlines the application object itself can be a generator.
    
    
    def application(environ, start_response):  
        status = '200 OK'   
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)   
              
        yield "1\n"  
        yield "2\n"  
        yield "3\n"  
        yield "4\n"  
        yield "5\n"

A class instance could also be returned so long as it supports the iterator protocol.
    
    
    class Iterable:  
        def __iter__(self):  
            yield "1\n"  
            yield "2\n"  
            yield "3\n"  
            yield "4\n"  
            yield "5\n"  
      
    def application(environ, start_response):  
        status = '200 OK'  
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)  
          
        return Iterable()

or:
    
    
    class Iterable:  
        def __init__(self):  
            self.__count = 0  
      
        def __iter__(self):  
            return self  
      
        def next(self):  
            if self.__count <= 4:  
                self.__count += 1  
                return '%s\n' % self.__count  
            raise StopIteration  
      
    def application(environ, start_response):  
        status = '200 OK'  
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)  
      
        return Iterable()

or finally:
    
    
    class Iterable:  
        def __getitem__(self, index):  
            if index <= 4:  
                return '%s\n' % (index+1)  
            raise IndexError  
      
    def application(environ, start_response):  
        status = '200 OK'  
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)  
      
        return Iterable()

Important to note is that although a byte string itself is an iterable value, you should never return that explicitly as the result from the WSGI application. It will work if you do that, but the consequence of doing that will be that the underlying WSGI gateway or adapter will still iterate over it. This will result in a single byte being yielded each time, with that single byte being written and then flushed back to the HTTP client. The result of this will obviously be absolutely dreadful performance. So, if you are having performance issues, make sure you are not inadvertently returning a byte string rather than returning a list containing a single byte string value.  
  
The next thing that the application object can be is an instance of a class. In this case as the class instance itself is being executed, it must provide a ‘\_\_call\_\_\(\)’ method with an appropriate signature.
    
    
    class Application:  
        def __call__(self, environ, start_response):  
            status = '200 OK'  
            response_headers = [('Content-type', 'text/plain')]  
            start_response(status, response_headers)  
      
            return ["1\n", "2\n", "3\n", "4\n", "5\n"]  
          
    application = Application()

We have again returned a list here, but as before when using a normal function, the ‘\_\_call\_\_\(\)’ method could be a generator function, or return any sort of iterable object.  
  
When using a class instance as the application object, if for some reason it doesn’t provide a ‘\_\_call\_\_\(\)’ method and instead has named the entry point another name then one could instead also write:
    
    
    class Application:  
        def execute(self, environ, start_response):  
            status = '200 OK'   
            response_headers = [('Content-type', 'text/plain')]  
            start_response(status, response_headers)  
      
            return ["1\n", "2\n", "3\n", "4\n", "5\n"]  
              
    _application = Application()  
      
    application = _application.execute

In other words, a reference to an arbitrary bound method of an instance of a class can be used as the application object. This works the same as if the method were called ‘\_\_call\_\_\(\)’, or if a ‘\_\_call\_\_\(\)’ method were provided which in turned called this second method and returned its result.  
  
Technically you could also use static methods or class methods in the same way, but that would be getting a bit too weird.  
  
When a normal function was used originally, if it was necessary to cache information between requests then the only way it could be done would be to store any such data as global variables within the module containing the function, or some other module. This effectively precludes the ability to have multiple distinct instances of an application based on that one function.  
  
The way to get around that is to use a class instance as the application object. By doing this you could create multiple instances of the class object with each storing any data requiring to be cached as attributes of that instance of the class instead of as global variables.  
  
Either way, because a hosting environment may support multithreading, that is, the ability to handle multiple requests in parallel, any data access, whether it be to global variables or attributes of an instance of the class for the application, should be protected against concurrent access using appropriate thread locking mechanisms.  
  
If for some reason you didn’t need to share data across requests, but did need to share data across multiple functions implementing a WSGI application, then one can use the ‘environ’ dictionary to pass data around. Often this is frowned upon and can get messy for complex data. An alternative to using the ‘environ’ dictionary is to still use a class instance but create an instance of the class per request. To do this, one can use:
    
    
    class Application:  
        def __init__(self, environ, start_response):  
            self.__environ = environ  
            self.__start_response = start_response  
              
        def __iter__(self):  
            status = '200 OK'   
            response_headers = [('Content-type', 'text/plain')]  
            self.__start_response(status, response_headers)  
      
            yield "1\n"  
            yield "2\n"  
            yield "3\n"  
            yield "4\n"  
            yield "5\n"  
      
    application = Application

For this scenario, the application object is actually the class object itself rather than an instance of the class. The result of this is that for each request a new instance of the class is created, with the ‘environ’ and ‘start\_response’ parameters being passed to the constructor of the class.  
  
The result of calling the class object like this to create an instance of the class is the actual instance of the class. The instance returned therefore needs to satisfy the same properties as the result for an application object were it a normal function. That is, the class instance needs to be an iterable object.  
  
Here the instance is made iterable by implementing the ‘\_\_iter\_\_\(\)’ method as a generator function. It could though use other methods for making an iterable as shown before, such as:
    
    
    class Application:  
        def __init__(self, environ, start_response):  
            self.__environ = environ  
            self.__start_response = start_response  
            self.__count = 0  
          
        def __iter__(self):  
            status = '200 OK'   
            response_headers = [('Content-type', 'text/plain')]  
            self.__start_response(status, response_headers)  
            return self  
                  
        def next(self):  
            if self.__count <= 4:  
                self.__count += 1  
                return "%d\n" % self.__count  
              
            raise StopIteration  
      
    application = Application

or:
    
    
    class Application:  
        def __init__(self, environ, start_response):  
            self.__environ = environ  
            self.__start_response = start_response  
              
        def __getitem__(self, index):  
            if index == 0:  
                status = '200 OK'  
                response_headers = [('Content-type', 'text/plain')]  
                self.__start_response(status, response_headers)  
              
                return "%d\n" % (index+1)  
          
            elif index <= 4:  
                return "%d\n" % (index+1)  
                  
            raise IndexError  
              
    application = Application

What does all this mean? Not much except that there are lots of ways of implementing the skeleton for a WSGI application object.  
  
In general it doesn’t matter, even if the WSGI application object is used as part of a middleware stack because all the different ways of implementing the application object satisfy the basic requirement as far as processing of input parameters and the subsequent result being an iterable.  
  
The only time where the range of ways for implementing an application object may be an issue is where you are needing to implement decorators for WSGI applications to transparently perform pre and post actions. This is what I am having to deal with and the reason it gets tricky is because you need to deal with both function and class decorators, with function decorators possibly also needing to be aware of the differences between normal functions and class methods.  
  
If you don’t have the luxury of modifying the original source code to apply a decorator and are instead forced to do monkey patching of a system, then you also need to deal with the differences between unbound and bound methods of classes. All lots of fun.  
  
Anyway, hope this exploration of the different ways of implementing application objects is useful to someone and when I sort out what I am doing with decorators for WSGI application objects, I’ll look at doing a followup with an explanation of what I worked out about that.  
  
BTW, if you know of other ways that WSGI application objects could be implemented, then please followup and describe them. I think I got all of them but could have missed both the obvious and the obscure.

---

## Comments

### fumanchu - January 9, 2011 at 2:15 AM

"there are lots of ways of implementing the skeleton for a WSGI application object...In general it doesn’t matter, even if the WSGI application object is used as part of a middleware stack"  
  
In practice, it _does_ matter which approach you take when writing middleware, because middleware should ALWAYS expose a close\(\) method, even if all it does is call close\(\) on the application interface it itself wraps. If it does not, then the server cannot reliably close all the components in a WSGI graph.

### Graham Dumpleton - January 9, 2011 at 7:58 AM

Robert, yes for middleware it can matter. At this point was trying to address the original WSGI application which is the origin of the data and not so much a middleware. Middleware, the obligations of them and the typical patterns for implementation was going to be subject of future post.

### Kamal Mustafa - April 8, 2012 at 8:25 PM

I was toying around with simple wsgi application \(I just learnt about mod\_wsgi AddHandler directive, for so long I have been using WSGIScriptAlias to launch my wsgi app\). So the idea is to have something that closely resemble PHP way of executing the application. Don't ask me why, just for fun. I use Django or Flask for real thing.  
  
So here's my application defined in ../app/php.py:-  
  
  
class PHPApplication\(object\):  
def \_\_init\_\_\(self\):  
self.out = \[\]  
self.counter = 0  
self.counter += 1  
self.out.append\(str\(self.counter\)\)  
  
def printx\(self, out\):  
self.out.append\(out\)  
  
def \_\_call\_\_\(self, environ, start\_response\):  
start\_response\('200 OK', \[\('Content-type', 'text/html'\)\]\)  
for out in self.out:  
yield out  
  
  
and the index.py:-  
  
  
import os  
import sys  
  
CUR\_DIR = os.path.abspath\(os.path.dirname\(\_\_file\_\_\)\)  
LIB\_DIR = os.path.abspath\(os.path.join\(CUR\_DIR, '../lib'\)\)  
APP\_DIR = os.path.abspath\(os.path.join\(CUR\_DIR, '../app'\)\)  
  
for path in \(LIB\_DIR, APP\_DIR,\):  
if path not in sys.path:  
sys.path.insert\(0, path\)  
  
from php import PHPApplication  
  
php = PHPApplication\(\)  
php.printx\("hello world"\)  
  
application = php  
  
  
and the apache vhost config:-  
  
DocumentRoot /home/kamal/pylikephp/htdocs  
DirectoryIndex index.py  
  
Options ExecCGI  
  
AddHandler wsgi-script .py  
  
Order allow,deny  
Allow from all  
  
  
WSGIDaemonProcess pylikephp processes=1 threads=2 display-name=%\{GROUP\}  
WSGIProcessGroup pylikephp  
  
  
My initial thought was the counter will always get incremented since the application object was created only once during mod\_wsgi daemon process initialization. But it look like the application object is created on each requests since the counter always stayed at 1 even after refreshing my browser few times. What I'm missing here.  
  
If this is how mod\_wsgi work, does it safe to build my application like this ?

### Graham Dumpleton - April 9, 2012 at 9:21 AM

@kamal Use the mod\_wsgi mailing list to ask questions. Blog posts are not support forums.

