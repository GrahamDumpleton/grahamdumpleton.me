---
layout: post
title: "The \"Decorator Pattern\" versus the Python \"wrapt\" package."
author: "Graham Dumpleton"
date: "2018-01-30"
url: "http://blog.dscpl.com.au/2018/01/the-pattern-versus-python-package.html"
post_id: "6268623409921269759"
blog_id: "2363643920942057324"
tags: ['decorators', 'python', 'wrapt']
comments: 0
published_timestamp: "2018-01-30T18:31:00+11:00"
blog_title: "Graham Dumpleton"
---

Brandon Rhodes published a [post today about the Decorator Pattern](http://python-patterns.guide/gang-of-four/decorator-pattern/) and how that translates into Python. He explains the manual way that the pattern can be implemented in Python as a wrapper, as well as how you can try to minimise the amount of work you need to do by overriding special methods of a Python object.

The [wrapt](https://pypi.python.org/pypi/wrapt) package I authored was purpose built for this task of creating wrappers which Brandon describes, and much more. To avoid some of the name confusion around Decorator Pattern versus Python decorators, which Brandon highlights as an issue, I tend to refer to the wrappers as transparent object proxies.

Lets have a quick look at some of the examples Brandon gave and see how they would be implemented using the wrapt package and what happens when one tries to perform introspection on an object via the wrapper.

# Implement: Dynamic Wrapper

Jumping to the example of the dynamic wrapper that Brandon gave, the equivalent using wrapt would be:

```
 import wrapt

 class WriteLoggingFile(wrapt.ObjectProxy):

     def __init__(self, wrapped, logger):  
         super(WriteLoggingFile, self).__init__(wrapped)  
         self._self_logger = logger

     def write(self, s):  
         self.__wrapped__.write(s)  
         self._self_logger.debug('wrote %s bytes to %s', len(s), self.__wrapped__)

     def writelines(self, strings):  
         if self.closed:  
             raise ValueError('this file is closed')  
         for s in strings:  
             self.write(s)
```

All that needed to be provided was the methods you want to override. All that boilerplate functionality of the special methods for attribute access and update, and object iteration etc, are provided by the wrapt.ObjectProxy base class that the wrapper inherits from.

Now lets look at what happens when we introspect an instance of the wrapper object.

```
 >>> import sys, logging  
 >>> stdout = WriteLoggingFile(sys.stdout, logging)  
 >>> dir(stdout)  
 ['__class__', '__delattr__', '__doc__', '__enter__', '__exit__',  
  '__format__', '__getattribute__', '__hash__', '__init__', '__iter__',  
  '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',  
  '__sizeof__', '__str__', '__subclasshook__', 'close', 'closed',  
  'encoding', 'errors', 'fileno', 'flush', 'isatty', 'mode', 'name',  
  'newlines', 'next', 'read', 'readinto', 'readline', 'readlines',  
  'seek', 'softspace', 'tell', 'truncate', 'write', 'writelines',  
  'xreadlines']
```

We get what we want to see, which is the same as what we would get if we introspect the wrapped object.

The wrapt.ObjectProxy class does much more than that though. Take for example the following:

```
 >>> isinstance(stdout, type(sys.stdout))  
 True  
 >>> isinstance(stdout, file)  
 True
```

The isinstance\(\) check will also succeed and say that the wrapper is an instance of the type of object which was wrapped.

It should be noted that you can't completely fool Python though:

```
 >>> type(stdout)  
 <class '__main__.WriteLoggingFile'>
```

But then, if you want to allow for duck typing, you should never directly compare types and should always use isinstance\(\).

# Hack: Monkey-patch each object

The next example which has an equivalent when using wrapt is monkey patching an instance of an object rather than use a wrapper. Using wrapt this would be written as:

```
 def bind_write_method(logger):  
     @wrapt.function_wrapper  
     def write_and_log(wrapped, instance, args, kwargs):  
         wrapped(*args, **kwargs)  
         logger.debug('wrote %s bytes to %s', len(args[0]), instance)  
     return write_and_log

 f = open('/dev/null', 'w')  
 f.write = bind_write_method(logging)(f.write)
```

The @wrapt.function\_wrapper is a factory for creating a wrapper function. If you have used wrapt before, it does the same job as @wrapt.decorator, but doesn't have as many of the features for customisation that the latter does. When doing monkey patching, using @wrapt.function\_wrapper is less confusing naming wise as well.

Using wrapt to do this in this way, introspection even still works correctly on the patched method.

```
 >>> f.write.__name__  
 write

 >>> inspect.getargspec(f.write)  
 ArgSpec(args=['self', 'text'], varargs=None, keywords=None, defaults=None)
```

# Not just for Python decorators

As shown above, although the wrapt package is probably more well known as being useful for implementing well behaved Python decorators, the primary reason it was created was for implementing the Decorator Pattern for use in monkey-patching Python code dynamically.

Monkey-patching is often regarded as a hack with opinion being that it should never be used. It is absolutely essential though if you want to dynamically instrument Python code to do things like collect metric data without you needing to modify code yourself. In this situation where you would want to use it on production applications, you want to ensure the wrappers work as correctly as properly. That is what the wrapt package aims to do, ensuring as much as possible that all works properly, even in the many obscure corners cases.

If you still think this is a bad idea and don't trust what wrapt does, you may want to look under the covers of how the two leading application performance monitoring services for Python web applications instrument Python code. Hint, they use wrapt.

If you want to learn more about wrapt, check out the documentation:

  * [http://wrapt.readthedocs.io](http://wrapt.readthedocs.io/)



I have also written over a dozen related blog posts on decorators and monkey patching:

  * <[/guides/decorators-and-monkey-patching/](/guides/decorators-and-monkey-patching/)>



Finally, I have presented at a number of conferences on wrapt \(but not PyCon US\).

  * <https://www.youtube.com/watch?v=GCZmGgtWi3M>



I have neglected wrapt a little of late and there are a few outstanding issues that need to be addressed. If you are using wrapt, please let me know via Twitter as getting such messages is always a good motivating force when you work on open source projects. Without such messages it is too easy to get the opinion that no one is using your software and so why you should bother continuing with it.