---
title: "Decorating WSGI applications."
author: "Graham Dumpleton"
date: "Friday, January 7, 2011"
url: "http://blog.dscpl.com.au/2011/01/decorating-wsgi-applications.html"
post_id: "8329258324963338074"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 2
published_timestamp: "2011-01-07T13:12:00+11:00"
blog_title: "Graham Dumpleton"
---

One of my recent blog posts showed how one could construct a wrapper for a WSGI application component such that a cleanup action could be associated with requests, with the cleanup action only being executed after any request content had been written back to the HTTP client. This time I am going to show how that can be converted into a Python decorator.  
  
Recalling the final code from before, what we had was:
    
    
    def FileWrapper(iterable, callback, environ):  
        class _FileWrapper(type(iterable)):  
            def close(self):  
                try:  
                    iterable.close()  
                finally:  
                    callback(environ)  
        return _FileWrapper(iterable.filelike, iterable.blksize)  
      
    class Generator:  
        def __init__(self, iterable, callback, environ):  
            self.__iterable = iterable  
            self.__callback = callback  
            self.__environ = environ  
        def __iter__(self):  
            for item in self.__iterable:  
                yield item  
        def close(self):  
            try:  
                if hasattr(self.__iterable, 'close'):  
                    self.__iterable.close()  
            finally:  
                self.__callback(self.__environ)  
      
    class ExecuteOnCompletion:  
        def __init__(self, application, callback):  
            self.__application = application  
            self.__callback = callback  
        def __call__(self, environ, start_response):  
            try:  
                result = self.__application(environ, start_response)  
            except:  
                self.__callback(environ)  
                raise  
            file_wrapper = environ.get('wsgi.file_wrapper', None)  
            if file_wrapper and isinstance(result, file_wrapper):  
                return FileWrapper(result, self.__callback, environ)  
            else  
                return Generator(result, self.__callback, environ)

Note that this is relying on wsgi.file\_wrapper being a type object, which as explained in prior post probably should be a requirement in a future WSGI specification. I’ll leave it for the example, but you may want to remove that part if concerned about portability.  
  
The above could then be used as:
    
    
    def _application(environ, start_response):  
        ...  
      
    def cleanup(environ):  
        # Perform required cleanup task.  
        ...  
      
    application = ExecuteOnCompletion(_application, cleanup)

What I instead however want to be able to do is write this using the decorator syntax of Python. That is:
    
    
    @execute_on_completion(cleanup)  
    def application(environ, start_response):  
        ...

In another of my recent blog posts I also detailed the different ways that WSGI application objects could be implemented. Namely, as functions, class instances and class objects. As such, we need to make sure it also works for those as well. Specifically:
    
    
    class Application:  
      
        @execute_on_completion(cleanup)  
        def __call__(self, environ, start_response):  
            ...  
          
    application = Application()

and:
    
    
    @execute_on_completion(cleanup)  
    class Application:  
      
        def __init__(self, environ, start_response):  
            ...  
              
        def __iter__(self):  
            ...  
      
    application = Application

For this decorator we want to be able to use a parameter, namely the reference to the cleanup function. In that case the pattern we will need to use for the implementation of the decorator is:
    
    
    def execute_on_completion(cleanup):  
        def decorator(application):  
            def wrapper(environ, start_response):  
                ...  
            return wrapper  
        return decorator

We already have a wrapper object in the form of the ‘ExecuteOnCompletion’ class though and so don’t need the ‘wrapper\(\)’ function here. The result being:
    
    
    def execute_on_completion(cleanup):  
        def decorator(application):  
            return ExecuteOnCompletion(application, cleanup)  
        return decorator

And when we try that out for the case where our WSGI application is a normal function:
    
    
    @execute_on_completion(cleanup)  
    def application(environ, start_response):  
        status = '200 OK'  
        response_headers = [('Content-type', 'text/plain')]  
        start_response(status, response_headers)  
      
        return ["1\n", "2\n", "3\n", "4\n", "5\n"]

that works fine.  
  
Now let us however try the case where we use the decorator on a class method:
    
    
    class Application:  
        @execute_on_completion(cleanup)  
        def __call__(self, environ, start_response):  
            status = '200 OK'  
            response_headers = [('Content-type', 'text/plain')]  
            start_response(status, response_headers)  
      
            return iter(["1\n", "2\n", "3\n", "4\n", "5\n"])  
      
    application = Application()

For this we find it fails. The specific error being:
    
    
    Traceback (most recent call last):  
      File "/some/path/example.wsgi", line 31, in __call__  
        result = self.__application(environ, start_response)  
    TypeError: __call__() takes exactly 3 arguments (2 given)

This is occurring at the point in the ‘\_\_call\_\_\(\)’ method of the ‘ExecuteOnCompletion’ class where the wrapped WSGI application object is being called.  
  
I am not going to go into detail here about what the actual cause of the error is, partly because it isn’t something I don’t really understand really well. In summary though, in order to use a class object as a wrapper within a decorator in this way, it needs to have an appropriate descriptor added to it, with the descriptor triggering some magic so that the class method being invoked is seen as a bound method of the class instance, thus ensuring that the ‘self’ parameter is available.  
  
Because descriptors only work for new style classes, which I should have used from the outset anyway, we need to also make ‘ExecuteOnCompletion’ derive from the ‘object’ type. This leaves us with:
    
    
    class ExecuteOnCompletion(object):  
      
        def __init__(self, application, callback):  
            self.__application = application  
            self.__callback = callback  
      
        def __get__(self, obj, objtype=None):  
            return types.MethodType(self, obj, objtype)  
      
        def __call__(self, environ, start_response):  
            try:  
                result = self.__application(environ, start_response)  
            except:  
                self.__callback(environ)  
                raise  
            file_wrapper = environ.get('wsgi.file_wrapper', None)  
            if file_wrapper and isinstance(result, file_wrapper):  
                return FileWrapper(result, self.__callback, environ)  
            else:  
                return Generator(result, self.__callback, environ)

The descriptor is the special ‘\_\_get\_\_\(\)’ method which has been added.  
  
We now try again, but it still fails. This time with the different error:
    
    
    TypeError: __call__() takes exactly 3 arguments (4 given)

Under mod\_wsgi at least, this didn’t even come with a traceback, possibly because it is coming from C internals of Python, but what is being referred to here is the ‘\_\_call\_\_\(\)’ method of the ‘ExecuteOnCompletion’ class.  
  
The reason the error arises is that with the descriptor being in place, the ‘self’ parameter required when invoking the target WSGI application object is actually being passed in to ‘\_\_call\_\_\(\)’ in addition to the ‘self’ parameter for the instance of ‘ExecuteOnCompletion’ and the ‘environ’ and ‘start\_response’ parameters.  
  
Going quickly back to our example where we wrapped a normal function and not a class method, we find that adding the descriptor has not changed the operation for that case. At least then the addition of the descriptor hasn’t broken that.  
  
What it does indicate though is that our ‘\_\_call\_\_\(\)’ method has to be able to handle two scenarios. In the first it will only get passed ‘environ’ and ‘start\_response’, but when the decorator is applied to a class method, it will also be passed in the ‘self’ parameter for the target WSGI application object, inserted into the argument list before that of ‘environ’ and ‘start\_response’.  
  
Now, we can just change the prototype of the ‘\_\_call\_\_\(\)’ method to accept a variable number of arguments:
    
    
    def __call__(self, *args):  
      ...

and the actual invocation of the target WSGI application to:
    
    
    result = self.__application(*args)

but we have the problem that we need access to the ‘environ’ parameter within the body of the ‘\_\_call\_\_\(\)’ method. This being required where needing access to ‘wsgi.file\_wrapper’ but also so we can pass the ‘environ’ parameter onto the cleanup function.  
  
What we do know though is that WSGI application objects can only be called with positional parameters and that there is only ever the two of ‘environ’ and ‘start\_response’. Thus, it doesn’t matter whether there are two or three arguments depending on whether a normal function or a bound class method is being called, the ‘environ’ parameter will always be the second last argument. We can therefore rewrite the ‘\_\_call\_\_\(\)’ method as:
    
    
    class ExecuteOnCompletion(object):  
      
        def __init__(self, application, callback):  
            self.__application = application  
            self.__callback = callback  
      
        def __get__(self, obj, objtype=None):  
            return types.MethodType(self, obj, objtype)  
      
        def __call__(self, *args):  
            environ = args[-2]  
            try:  
                result = self.__application(*args)  
            except:  
                self.__callback(environ)  
                raise  
            file_wrapper = environ.get('wsgi.file_wrapper', None)  
            if file_wrapper and isinstance(result, file_wrapper):  
                return FileWrapper(result, self.__callback, environ)  
            else:  
                return Generator(result, self.__callback, environ)

And we have success for both the case of the decorator being applied to a normal function, as well as the class method.  
  
Now for the final scenario of the decorator being applied to a class.
    
    
    @execute_on_completion(cleanup)  
    class Application:  
        def __init__(self, environ, start_response):  
            self.__environ = environ  
            self.__start_response = start_response  
      
        def __iter__(self):  
            status = '200 OK'  
            response_headers = [('Content-type', 'text/plain')]  
            self.__start_response(status, response_headers)  
      
            for item in ["1\n", "2\n", "3\n", "4\n", "5\n"]:  
                yield item  
      
    application = Application

This also works fine.  
  
One final thing to check is whether this also works if you don’t have access to the source code and need to monkey patch this wrapper to existing code imported from other modules. For example:
    
    
    application = execute_on_completion(cleanup)(application)

And the answer to that one is that it does also work for that, so we have pretty well covered all bases.

---

## Comments

### mrploppy - November 7, 2014 at 2:18 AM

hi graham, do you have any advice on using callbacks where content must be generated before served? i've only just happened across the idea that a request handler is an iterable \(\_\_iter\_\_\). but who calls \_\_iter\_\_? and can I make it wait for data to be created and serve that?  
cheers,  
robin

### Graham Dumpleton - November 7, 2014 at 7:24 AM

Can't say I understand what you mean. Please us the mod\_wsgi mailing list to ask your question.

