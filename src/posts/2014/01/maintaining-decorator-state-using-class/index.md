---
layout: post
title: "Maintaining decorator state using a class."
author: "Graham Dumpleton"
date: "2014-01-13"
url: "http://blog.dscpl.com.au/2014/01/maintaining-decorator-state-using-class.html"
post_id: "4409669009274192117"
blog_id: "2363643920942057324"
tags: ['decorators', 'python']
comments: 12
published_timestamp: "2014-01-13T10:07:00+11:00"
blog_title: "Graham Dumpleton"
---

This is the sixth post in my series of blog posts about Python decorators and how I believe they are generally poorly implemented. It follows on from the previous post titled '[Decorators which accept arguments](/posts/2014/01/decorators-which-accept-arguments/)', with the very first post in the series being '[How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/)'.

  
In the previous post I described how to implement decorators which accept arguments. This covered mandatory arguments, but also how to have a decorator optionally accept arguments. I also touched on how one can maintain state between invocations of the decorator wrapper function for a specific wrapped function.  
  
One of the approaches described for maintaining state was to implement the decorator as a class. Using this approach though resulted in an unexpected error.  
  
This post will explore the source of the error when attempting to implement our decorator as a class using our new decorator factory and function wrapper, and then see if any other issues crop up.  
  


###  Single decorator for functions and methods

  
As described in the previous post, the pattern we were trying to use so as to allow us to use a class as a decorator was:  

```
class with_arguments(object):
    def __init__(self, arg):
        self.arg = arg

    @decorator
    def __call__(self, wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

@with_arguments(arg=1)
def function():
    pass
```

The intent here is that the application of the decorator, with arguments supplied, would result in an instance of the class being created. In the next phase where that is called with the wrapped function, the \_\_call\_\_\(\) method with @decorator applied will be used as a decorator on the function to be wrapped. The end result should be that the \_\_call\_\_\(\) method of the class instance created ends up being our wrapper function.  
  
When the decorated function is now called, the \_\_call\_\_\(\) method of the class would be called with it in turn calling the wrapped function. As the \_\_call\_\_\(\) method at that point is bound to an instance of the class, it would have access to the state that it contained.  
  
When we tried this though we got, at the time that the decorator was being applied, the error:  

```
Traceback (most recent call last):
  File "test.py", line 483, in <module>
    @with_arguments(1)
TypeError: _decorator() takes exactly 1 argument (2 given)
```

The \_decorator\(\) function in this case is the inner function from our decorator factory.  

```
def decorator(wrapper):
    @functools.wraps(wrapper)
    def _decorator(wrapped):
        return function_wrapper(wrapped, wrapper)
    return _decorator
```

The mistake that has been made here is that we are using a function closure to implement our decorator factory, yet we were expecting it to work on both normal functions and methods of classes.  
  
The reason this will not work is due to the binding that occurs when a method of a class is accessed. This process was described in a previous post in this series and is the result of the descriptor protocol being applied. This binding results in the reference to the instance of the class being automatically passed as the first argument to the method.  
  
Now as the \_decorator\(\) function was acting as a wrapper for the method call, and because \_decorator\(\) was not defined so as to accept both 'self' and 'wrapped' as arguments, the call would fail.  
  
We could create a special variant of the decorator factory to be used just on instance methods, but that goes against the specific complaint expressed earlier in regard to how people create multiple variants of decorators for use on normal functions and instance methods.  
  
To resolve this issue, what we can do is use our function wrapper for the decorator returned by the decorator factory, instead of a function closure.  

```
def decorator(wrapper):
    def _wrapper(wrapped, instance, args, kwargs):
        def _execute(wrapped):
            return function_wrapper(wrapped, wrapper)
        return _execute(*args, **kwargs)
    return function_wrapper(wrapper, _wrapper)
```
  


###  Explicit binding of methods required

  
This above change now means we do not have to worry about whether @decorator is being applied to a normal function, instance method or even a class method. This is because in all cases, any reference to the instance being bound to is never passed through in 'args'. Thus any wrapper function doesn't need to worry about the distinction.  
  
Trying again with this change though, we are confronted with a further problem. This time at the point that the wrapped function is called.  

```
>>> function()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "test.py", line 243, in __call__
    return self.wrapper(self.wrapped, None, args, kwargs)
TypeError: __call__() takes exactly 5 arguments (4 given)
```

The issue this time is that when @decorator is applied to the \_\_call\_\_\(\) method, the reference it is passed is that of the unbound method. This is because this occurs during the processing of the class definition, long before any instance of the class has been created.  
  
Normally the reference to the instance would be supplied later when the method is bound, but because our decorator is actually a factory there are two layers involved. The target instance is available to the upper factory as the 'instance' argument, but that isn't being used in any way when the inner function wrapper object is being created which associates the function to be wrapped with our wrapper function.  
  
To solve this problem we need for the case where we are being bound to an instance, to explicitly bind the wrapper function ourselves against the instance.  

```
def decorator(wrapper):
    def _wrapper(wrapped, instance, args, kwargs):
        def _execute(*args, **kwargs):
            if instance is None:
                return function_wrapper(wrapped, wrapper)
            elif inspect.isclass(instance):
                return function_wrapper(wrapped, wrapper.__get__(None, instance))
            else:
                return function_wrapper(wrapped, wrapper.__get__(instance, type(instance)))
        return _execute(*args, **kwargs)
    return function_wrapper(wrapper, _wrapper)
```

So what we are using here is the feature of our function wrapper that allows us to implement a universal decorator. That is, one which can change its behaviour dependent upon the context it is used in.  
  
In this case we had three cases we needed to deal with.  
  
The first is where the instance was None. This corresponds to a normal function, a static method or where the decorator was applied to a class type.  
  
The second is where the instance was not None, but where it referred to a class type. This corresponds to a class method. In this case we need to bind the wrapper function to the class type by calling the \_\_get\_\_\(\) method of the wrapper function explicitly.  
  
The third and final case is where the instance was not None, but where it was not referring to a class type. This corresponds to an instance method. In this case we again need to bind the wrapper function, this time to the instance.  
  
With these changes, we are now all done with addressing this issue, and to a large degree with filling out our new decorator pattern.  
  


###  Do not try and reproduce this

  
So the complete solution we now have at this point is:  

```
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
        def _execute(*args, **kwargs):
            if instance is None:
                return function_wrapper(wrapped, wrapper)
            elif inspect.isclass(instance):
                return function_wrapper(wrapped, wrapper.__get__(None, instance))
            else:
                return function_wrapper(wrapped, wrapper.__get__(instance, type(instance)))
        return _execute(*args, **kwargs)
    return function_wrapper(wrapper, _wrapper)
```

Take heed though of what was said in prior posts though. The object proxy implementation given here is not a complete solution. As a result, do not take this code and try and use it yourself as is. If you do you will find that some aspects of performing introspection on the wrapped function will not work as indicated they should.  
  
In particular, access to the function \_\_doc\_\_ string will always yield None. Various attributes such as \_\_qualname\_\_ in Python 3 and \_\_module\_\_ are not propagated either.  
  
Handling an attribute such as \_\_doc\_\_ string correctly is actually a bit of a pain. This is because you cannot use a \_\_doc\_\_ property in an object proxy base class that returns the value from the wrapped function and have it then work when you derive another class from it. This is because the separate \_\_doc\_\_ string attribute from the derived class, even if no documentation string were specified in the derived class, will override that of the base class.  
  
So the object proxy as shown here was intended to be illustrative only of what was required.  
  
In some respects all the code here is meant to be illustrative only. It is not here to say use this code but to show you the general path to implementing a more robust decorator implementation. It is to provide a narrative from which you can learn. If you were expecting a one line TLDR summary on how to do it, then you can forget it, things just aren't that simple.  
  


###  Introducing the wrapt decorator module

  
If I am telling you not to use this code, what are you supposed to do then?  
  
The answer to that already exists in the form of the [wrapt](https://pypi.python.org/pypi/wrapt) module on PyPi.  
  
The wrapt package has been available for a number of months already, but isn't widely known of at this point. It implements all of what is described but also more. The module has a complete implementation of the object proxy required to make all this work correctly. The module also provides a range of other features related to the decorator factory as well as other separate features related to monkey patching in general.  
  
Although I am now finally pointing out that this module exists, I will not be stopping the blog posts at this point as there is a range of topics I still want to cover. These include examples of how a universal decorator can be used, enabling/disabling of decorators, performance issues, the remaining parts of the implementation of the object proxy, monkey patching and much more.  
  
In the next post in this series I will look at one specific example of using a universal decorator by posing the question of if Python decorators are so wonderful, why does Python not provide a @synchronized decorator?  
  
Such a decorator was held up as a bit of a poster child as to what could be done with decorators when they were first introduced to the language, yet all the implementations I could find are half baked and not very practical in the real world. I believe that a universal decorator can help here and we can actually have a usable @synchronized decorator. I will therefore explore that possibility in the next post.

---

## Comments

### A. Jesse Jiryu Davis - January 13, 2014 at 11:01 AM

This series is a tour de force.

### None - January 14, 2014 at 12:55 AM

Thank you for taking the time to put these articles together\!

### tomislater - February 27, 2014 at 8:19 AM

Such a series\! Very useful articles. The wrapt module is adorable.

### Nico - March 16, 2014 at 5:42 AM

Is there some interaction between your 'wrapt' module and print statements? I have an existing piece of code that uses print\(\) inside a decorator for producing debugging output. This works fine if I don't use wrapt.decorator. If I add @wrapt.decorator, all lines of print\(\) produce zero output.

### Graham Dumpleton - March 16, 2014 at 11:59 AM

There should be no interaction between print and the use of the decorator factory. Are you sure you defined the decorator correctly? Ignoring the print, does the functionality of the decorator otherwise work?

### Nico - March 16, 2014 at 8:22 PM

I think you're right: there's no problem with print, but there's another problem, and I can't figure out where it is.  
  
The short piece of code below appears to work. If I remove the '\#' in front of @wrapt.decorator, it looks the decorator isn't called at all, hence no print output. Can you see what's wrong?  

```
#!/usr/bin/python3
import wrapt

def action(pattern):
    # @wrapt.decorator
    def wrapper(wrapped):
        wrapped.pattern = pattern
        print('wrapped pattern =', pattern)
        return wrapped
    return wrapper

class Controller(object):
    def __init__(self):
        for name in dir(self):
            member = getattr(self, name)
            if hasattr(member, 'pattern'):
                print('pattern =', member.pattern)

@action('/find')
def search(self, req):
    return 'search collection'

c = Controller()
print('c.search has __name__ attribute', c.search.__name__)
```

### Graham Dumpleton - March 16, 2014 at 8:28 PM

You are not constructing the decorator correctly. Go and read:  
  
http://wrapt.readthedocs.org/en/latest/decorators.html\#creating-decorators  
  
Your decorator wrapper function is meant to have more arguments than that. Specifically, it is meant to have wrapped, instance, args and kwargs arguments as described in the documentation.

### Nico - March 16, 2014 at 8:50 PM

I read the docs yesterday and again today, and I'm still not seeing it. Could you please point out what needs to be fixed in the example script below?  

```
import wrapt

def action(pattern):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        wrapped.pattern = pattern
        print('wrapped pattern =', pattern)
        return wrapped(*args, **kwargs)
    return wrapper

class Controller(object):
    def __init__(self):
        for name in dir(self):
            member = getattr(self, name)
            if hasattr(member, 'pattern'):
                print('pattern =', member.pattern)

@action('/find')
def search(self, req):
    return 'search collection'

c = Controller()
print('c.search has __name__ attribute', c.search.__name__)
```

### Nico - March 16, 2014 at 8:52 PM

P.S.: I'm trying to combine examples from two paragraphs in the docs: the one about "Decorators With Optional Arguments" and the one about "Decorating Instance Methods".

### Graham Dumpleton - March 16, 2014 at 9:02 PM

In your case I suspect you shouldn't even be using the wrapt decorator factory as you don't want to intercept when the function is being called, you only want to add an attribute to the decorated function and return the original function again.  

```
# Replace leading underscores with spaces in the following.

def action(pattern):
    def wrapper(wrapped):
        wrapped.pattern = pattern
        return wrapped
    return wrapper
```

### Nico - March 16, 2014 at 10:52 PM

Thanks for your reply. In the example I gave you, you're right: there's no intercept when the function is being called. But at some point I want to add that.  
  
I'm going to experiment now with the "alternative approach \[...\] to use a class, where the wrapper function is the \_\_call\_\_\(\) method of the class".

### Graham Dumpleton - March 17, 2014 at 11:02 AM

You need to use an extra level of indirection.  

```
import wrapt

def action(pattern):
    def wrapper1(wrapped):
        @wrapt.decorator
        def wrapper2(wrapped, instance, args, kwargs):
            print('wrapped pattern =', wrapped.pattern)
            return wrapped(*args, **kwargs)
        wrapped.pattern = pattern
        return wrapper2(wrapped)
    return wrapper1

@action('xyz')
def f(x, y):
    print('f', x, y)

print(f.pattern)

f(1, 2)
```
