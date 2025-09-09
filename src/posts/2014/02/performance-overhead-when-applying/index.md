---
layout: post
title: "Performance overhead when applying decorators to methods."
author: "Graham Dumpleton"
date: "2014-02-17"
url: "http://blog.dscpl.com.au/2014/02/performance-overhead-when-applying.html"
post_id: "4074385092944256054"
blog_id: "2363643920942057324"
tags: ['decorators', 'python']
comments: 4
published_timestamp: "2014-02-17T23:36:00+11:00"
blog_title: "Graham Dumpleton"
---

This is the tenth post in my series of blog posts about Python decorators and how I believe they are generally poorly implemented. It follows on from the previous post titled '[Performance overhead of using decorators](/posts/2014/02/performance-overhead-of-using-decorators/)', with the very first post in the series being '[How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/)'.  
  
In the previous post I started looking at the performance implications of using decorators. In that post I started out by looking at the overheads when applying a decorator to a normal function, comparing a decorator implemented as a function closure to the more robust decorator implementation which has been the subject of this series of posts.  
  
For a 2012 model MacBook Pro the tests yielded for a straight function call:  


> 10000000 loops, best of 3: 0.132 usec per loop

When using a decorator implemented as a function closure the result was:  


> 1000000 loops, best of 3: 0.326 usec per loop

And finally with the decorator factory described in this series of blog posts:  


> 1000000 loops, best of 3: 0.771 usec per loop

This final figure was based on a pure Python implementation. When however the object proxy and function wrapper were implemented as a C extension, it was possible to get this down to:  


> 1000000 loops, best of 3: 0.382 usec per loop

This result was not much different to when using a decorator implemented as a function closure.  
What now for when decorators are applied to methods of a class?  
  


###  Overhead of having to bind functions

  


The issue with applying decorators to methods of a class is that if you are going to honour the Python execution model, the decorator needs to be implemented as a descriptor and correctly bind methods to a class or class instance when accessed. In the decorator described in this series of posts we actually made use of that mechanism so as to be able to determine when a decorator was being applied to a normal function, instance method or class method.  
  
Although this process of binding ensures correct operation, it comes at an additional cost in overhead over what a decorator implemented as a function closure, which does not make any attempt to preserve the Python execution model, would do.  
  
In order to see what extra steps occur, we can again use the Python profile hooks mechanism to trace execution of the call of our decorated function. In this case the execution of an instance method.  
First lets check again what we would get for a decorator implemented as a function closure.  


```python
    def my_function_wrapper(wrapped):
        def _my_function_wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _my_function_wrapper 

    class Class(object):
        @my_function_wrapper
        def method(self):
            pass

    instance = Class()

    import sys

    def tracer(frame, event, arg):
        print(frame.f_code.co_name, event)

    sys.setprofile(tracer)

    instance.method()
```

The result in running this is effectively the same as when decorating a normal function.  


> \_my\_function\_wrapper call  
>  method call  
>  method return  
> \_my\_function\_wrapper return

We should therefore expect that the overhead will not be substantially different when we perform actual timing tests.  
  
Now for when using our decorator factory. To provide context this time we need to present the complete recipe for the implementation.  


```python
    class object_proxy(object):
        def __init__(self, wrapped):
            self.wrapped = wrapped
            try:
                self.__name__ = wrapped.__name__
            except AttributeError:
                pass

        @property
        def __class__(self):
            return self.wrapped.__class__

        def __getattr__(self, name):
            return getattr(self.wrapped, name)

    class bound_function_wrapper(object_proxy):
        def __init__(self, wrapped, instance, wrapper, binding, parent):
            super(bound_function_wrapper, self).__init__(wrapped)
            self.instance = instance
            self.wrapper = wrapper
            self.binding = binding
            self.parent = parent

        def __call__(self, *args, **kwargs):
            if self.binding == 'function':
                if self.instance is None:
                    instance, args = args[0], args[1:]
                    wrapped = functools.partial(self.wrapped, instance)
                    return self.wrapper(wrapped, instance, args, kwargs)
                else:
                    return self.wrapper(self.wrapped, self.instance, args, kwargs)
            else:
                instance = getattr(self.wrapped, '__self__', None)
                return self.wrapper(self.wrapped, instance, args, kwargs)

        def __get__(self, instance, owner):
            if self.instance is None and self.binding == 'function':
                descriptor = self.parent.wrapped.__get__(instance, owner)
                return bound_function_wrapper(descriptor, instance, self.wrapper,
                        self.binding, self.parent)
            return self 

    class function_wrapper(object_proxy):

        def __init__(self, wrapped, wrapper):
            super(function_wrapper, self).__init__(wrapped)
            self.wrapper = wrapper
            if isinstance(wrapped, classmethod):
                self.binding = 'classmethod'
            elif isinstance(wrapped, staticmethod):
                self.binding = 'staticmethod'
            else:
                self.binding = 'function' 

        def __get__(self, instance, owner):
            wrapped = self.wrapped.__get__(instance, owner)
            return bound_function_wrapper(wrapped, instance, self.wrapper,
                    self.binding, self) 

        def __call__(self, *args, **kwargs):
            return self.wrapper(self.wrapped, None, args, kwargs) 

    def decorator(wrapper):
        def _wrapper(wrapped, instance, args, kwargs):
            def _execute(wrapped):
                if instance is None:
                    return function_wrapper(wrapped, wrapper)
                elif inspect.isclass(instance):
                    return function_wrapper(wrapped,
                            wrapper.__get__(None, instance))
                else:
                    return function_wrapper(wrapped,
                            wrapper.__get__(instance, type(instance)))
            return _execute(*args, **kwargs)
        return function_wrapper(wrapper, _wrapper)
```

With our decorator implementation now being:  


```python
    @decorator
    def my_function_wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)
```

the result we get when executing the decorated instance method of the class is:  


```bash
\('\_\_get\_\_', 'call'\) \# function\_wrapper  
 \('\_\_init\_\_', 'call'\) \# bound\_function\_wrapper  
 \('\_\_init\_\_', 'call'\) \# object\_proxy  
 \('\_\_init\_\_', 'return'\)  
 \('\_\_init\_\_', 'return'\)  
\('\_\_get\_\_', 'return'\)  
 \('\_\_call\_\_', 'call'\) \# bound\_function\_wrapper  
 \('my\_function\_wrapper', 'call'\)  
 \('method', 'call'\)  
 \('method', 'return'\)  
 \('my\_function\_wrapper', 'return'\)  
\('\_\_call\_\_', 'return'\)
```

As can be seen, due to the binding of the method to the instance of the class which occurs in \_\_get\_\_\(\), a lot more is now happening. The overhead can therefore be expected to be significantly more also.  
  


###  Timing execution of the method call

  


As before, rather than use the implementation above, the actual implementation from the wrapt library will again be used.  
This time our test is run as:  


```python
    $ python -m timeit -s 'import benchmarks; c=benchmarks.Class()' 'c.method()'
```

For the case of no decorator being used on the instance method, the result is:  


> 10000000 loops, best of 3: 0.143 usec per loop

This is a bit more than for the case of a normal function call due to the binding of the function to the instance which is occurring.  
  
Next up is using the decorator implemented as a function closure. For this we get:  


> 1000000 loops, best of 3: 0.382 usec per loop

Again, somewhat more than the undecorated case, but not a great deal more than when the decorator implemented as a function closure was applied to a normal function. The overhead of this decorator when applied to a normal function vs a instance method is therefore not significantly different.  
  
Now for the case of our decorator factory and function wrapper which honours the Python execution model, by ensuring that binding of the function to the instance of the class is done correctly.  
First up is where a pure Python implementation is used.  


> 100000 loops, best of 3: 6.67 usec per loop

Ouch. Compared to when using a function closure to implement the decorator, this is quite an additional hit in runtime overhead.  
  
Although this is only about an extra 6 usec per call, you do need to think about this in context. In particular, if such a decorator is applied to a function which is called 1000 times in the process of handing a web request, that is an extra 6 ms added on top of the response time for that web request.  
  
This is the point where many will no doubt argue that being correct is not worth it if the overhead is simply too much. But then, it also isn't likely the case that the decorated function, nor the decorator itself are going to do nothing and so the additional overhead incurred may still be a small percentage of the run time cost of those and so not in practice noticeable.  
  
All the same, can the use of a C extension improve things?  
  
For the case of the object proxy and function wrapper being implemented as a C extension, the result is:  


> 1000000 loops, best of 3: 0.836 usec per loop

So instead of 6 ms, that is less than 1 ms of additional overhead if the decorated function was called a 1000 times.  
  
It is still somewhat more than when using a decorator implemented as a function closure, but reiterating again, the use of a function closure when decorating a method of a class is technically broken by design as it does not honour the Python execution model.  
  


###  Who cares if it isn't quite correct

  
Am I splitting hairs and being overly pedantic in wanting things to be done properly?  
  
Sure, for what you are using decorators for you may well get away with using a decorator implemented as a function closure. When you start though moving into the area of using function wrappers to perform monkey patching of arbitrary code, you cannot afford to do things in a sloppy way.  
  
If you do not honour the Python execution model when doing monkey patching, you can too easily break in very subtle and obscure ways the third party code you are monkey patching. Customers don't really like it when what you do crashes their web application. So for what I need to do at least, it does matter and it matters a lot.  
  
Now in this post I have only considered the overhead when decorating instance methods of a class. I did not cover what the overheads are when decorating static methods and class methods. If you are curious about those and how they may be different, you can check out the benchmarks for the full range of cases in the [wrapt documentation](http://wrapt.readthedocs.org/en/latest/benchmarks.html).  
  
In the next post I will touch once again on issues of performance overhead, but also a bit on alternative ways of implementing a decorator so as to try and address the problems raised in my very first post. This will be as a part of a comparison between the approach described in this series of posts and the way in which the '[decorator](https://pypi.python.org/pypi/decorator)' module available from PyPi implements its variant of a decorator factory.

---

## Comments

### dougm - February 19, 2014 at 5:14 AM

This is a follow-up on "How you implemented your Python decorator is wrong.", right? Well, I'm going to save you a lot of CPU time and code by pointing out exactly how:  
  
>@function\_wrapper  
>@classmethod  
  
Reverse the order, and everything will work like a charm even without these AbstractSingletonMethodDecoratorFactories.  
  
http://ideone.com/Drp1cg

### Graham Dumpleton - February 19, 2014 at 9:30 AM

Now go and write a decorator with a single implementation that can be used on both normal functions and methods of classes, and which is aware of which case it is being applied in and behave differently when it knows it is wrapping an instance method, a class method or a normal function.  
  
Also come up with a generic solution for the bigger problem of monkey patching existing code to apply decorators/function wrappers, where it is not possible to change the order of the decorators because you don't have the ability to modify the original code.  
  
There are use cases outside of the specific one you are thinking about where using a decorator/function wrapper implemented as a function closure simply does not work or which produces very brittle code which causes subtle run time problems.  
  
There are eight other posts in this series besides this one and the very first one you referenced. These cover aspects of these other use cases, as will some future posts yet be done about the more general case of monkey patching.  
  
You are taking a quite narrow view. The problem area is much bigger than you seem to think it is. So, just because you think you have a solution that works for your particular example does not mean that can be used everywhere.

### dougm - February 19, 2014 at 3:41 PM

Your request doesn't make sense. There's no difference between unbound methods and functions, class method and metaclass instance methods, static methods and metaclass attribute functions. If your decorator needs more than that, maybe it's a sign that you need \*two completely different\* decorators?  
  
As for monkey patching, there's a reason it's considered bad practice. Your code is also very brittle due to replacing actual methods with descriptors.

### Graham Dumpleton - February 19, 2014 at 5:22 PM

Functions, methods, static methods and class methods are all what are called non-data descriptors.  
  
http://docs.python.org/2/howto/descriptor.html\#functions-and-methods  
http://docs.python.org/2/howto/descriptor.html\#static-methods-and-class-methods  
  
Saying that replacing them with descriptors is somehow wrong doesn't make any sense because they are already descriptors.  
  
The reason that monkey patching is generally brittle is not the practice as such, but because people don't do it properly. They simply don't understand the subtleties of how this stuff actually works under the covers. They also try and do it post import rather than at the time of import, but that is a totally different discussion.  
  
When monkey patching, if you use a descriptor to implement the wrapper and that wrapper properly implements the non-data descriptor method \_\_get\_\_\(\) properly and translates that into a call of \_\_get\_\_\(\) of the wrapped object to bind it, with any \_\_call\_\_\(\) then subsequently being on the bound object, then it works totally fine.  
  
Where it is brittle is where people use function closures as wrappers because the function closure will not properly apply binding to the non-data descriptor which is being wrapped.  
  
It only works at all in most cases because the outer wrapper passes through the self or cls as first argument anyway. Relying on that is the problem. Rely on that for a class method or static method and the result is wrong as the class method or static method never itself got to do binding and so it all breaks down.  
  
This was explained in earlier posts in the series of posts. Later posts also described a concrete example of where a decorator that can be applied in different contexts, rather than having a special decorator in each case, can result in a cleaner solution which doesn't rely on hacks or the need to use multiple implementations.  
  
Monkey patching can be just as robust as the code which is being patched. After all, you are implementing wrappers with the same constructs that the things being wrapped used. You just need to make sure you use the correct construct and not one which bypasses the normal hidden steps that occur when calling functions, methods, static methods, class methods etc.

