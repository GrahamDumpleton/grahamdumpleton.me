---
layout: post
title: "The interaction between decorators and descriptors."
author: "Graham Dumpleton"
date: "2014-01-07"
url: "http://blog.dscpl.com.au/2014/01/the-interaction-between-decorators-and.html"
post_id: "7579850449762006304"
blog_id: "2363643920942057324"
tags: ['decorators', 'python']
comments: 6
published_timestamp: "2014-01-07T22:00:00+11:00"
blog_title: "Graham Dumpleton"
---

This is the second post in my series of blog posts about Python decorators and how I believe they are generally poorly implemented. It follows on from the first post titled '[How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/)'.  
  
In that first post I described a number of ways in which the traditional way that Python decorators are implemented is lacking. These were:  
  


  * Preservation of function \_\_name\_\_ and \_\_doc\_\_.
  * Preservation of function argument specification.
  * Preservation of ability to get function source code.
  * Ability to apply decorators on top of other decorators that are implemented as descriptors.

  
I described previously how functools.wraps\(\) attempts to solve the problem with preservation of the introspection of the \_\_name\_\_ and \_\_doc\_\_ attributes, but highlight one case in Python 2 where it can fail, and also note that it doesn't help with the preservation of the function argument specification nor the ability to access the source code.  
  
In this post I want to focus mainly on the last of the issues above. That is the interaction between decorators and descriptors, where a function wrapper is applied to a Python object which is actually a descriptor.  
  


###  What are descriptors?

  
I am not going to give an exhaustive analysis of what descriptors are or how they work so if you want to understand them in depth, I would suggest reading up about them elsewhere.  
  
In short though, a descriptor is an object attribute with “binding behaviour”, one whose attribute access has been overridden by methods in the descriptor protocol. Those methods are \_\_get\_\_\(\), \_\_set\_\_\(\), and \_\_delete\_\_\(\). If any of those methods are defined for an object, it is said to be a descriptor.  
  


  * obj.attribute   
\--> attribute.\_\_get\_\_\(obj, type\(obj\)\) 
  * obj.attribute = value  
\--> attribute.\_\_set\_\_\(obj, value\) 
  * del obj.attribute   
\--> attribute.\_\_delete\_\_\(obj\)

  
What this means is that if an attribute of a class has any of these special methods defined, when the corresponding operation is performed on that attribute of a class, then those methods will be called instead of the default action. This allows an attribute to override how those operations are going to work.  
  
You may well be thinking that you have never made use of descriptors, but fact is that function objects are actually descriptors. When a function is originally added to a class definition it is as a normal function. When you access that function using a dotted attribute path, you are invoking the \_\_get\_\_\(\) method to bind the function to the class instance, turning it into a bound method of that object.  


```
> def f\(obj\): pass  
>  >>> hasattr\(f, '\_\_get\_\_'\)  
>  True 
```

```
> >>> f  
>  <function f at 0x10e963cf8>
```

```
> >>> obj = object\(\)  
>  >>> f.\_\_get\_\_\(obj, type\(obj\)\)  
>  <bound method object.f of <object object at 0x10e8ac0b0>>
```

So when calling a method of a class, it is not the \_\_call\_\_\(\) method of the original function object that is called, but the \_\_call\_\_\(\) method of the temporary bound object that is created as a result of accessing the function.  
  
You of course don't usually see all these intermediary steps and just see the outcome.  


```
> >>> class Object\(object\):  
>  ... def f\(self\): pass 
```

```
> >>> obj = Object\(\)  
>  >>> obj.f  
>  <bound method Object.f of <\_\_main\_\_.Object object at 0x10abf29d0>>
```

Looking back now at the example given in the first blog post where we wrapped a decorator around a class method, we encountered the error:  


```
> class Class\(object\):  
>  @function\_wrapper  
>  @classmethod  
>  def cmethod\(cls\):  
>  pass 
```

> Class.cmethod\(\) 

> Traceback \(most recent call last\):  
>  File "classmethod.py", line 15, in <module>  
>  Class.cmethod\(\)  
>  File "classmethod.py", line 6, in \_wrapper  
>  return wrapped\(\*args, \*\*kwargs\)  
>  TypeError: 'classmethod' object is not callable

The problem with this example was that for the @classmethod decorator to work correctly, it is dependent on the descriptor protocol being applied properly. This is because the \_\_call\_\_\(\) method only exists on the result returned by \_\_get\_\_\(\) when it is called, there is no \_\_call\_\_\(\) method on the @classmethod decorator itself.  
  
More specifically, the simple type of decorator that people normally use is not itself honouring the descriptor protocol and applying that to the wrapped object to yield the bound function object which should actually be called. Instead it is simply calling the wrapped object directly, which will fail if it doesn't have a \_\_call\_\_\(\).  
  
Why then does applying a decorator to a normal instance method still work?  
  
This still works because a normal function still has a \_\_call\_\_\(\) method. In bypassing the descriptor protocol of the wrapped function it is calling this. Although the binding protocol is side stepped, things still work out because the wrapper will pass the 'self' argument for the instance explicitly as the first argument when calling the original unbound function object.  
  
For a normal instance method the result in this situation is effectively the same. It only falls apart when the wrapped object, as in the case of @classmethod, are dependent on the descriptor protocol being applied correctly.  
  


###  Wrappers as descriptors

  
The way to solve this problem where the wrapper is not honouring the descriptor protocol and performing binding on the wrapped object in the case of a method on a class, is for wrappers to also be descriptors.  


```
> class bound\_function\_wrapper\(object\): 
```

```
> def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped 
```

```
> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\) 
```

```
> class function\_wrapper\(object\): 
```

```
> def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped 
```

```
> def \_\_get\_\_\(self, instance, owner\):  
>  wrapped = self.wrapped.\_\_get\_\_\( instance, owner\)  
>  return bound\_function\_wrapper\(wrapped\) 
```

```
> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\)
```

If the wrapper is applied to a normal function, the \_\_call\_\_\(\) method of the wrapper is used. If the wrapper is applied to a method of a class, the \_\_get\_\_\(\) method is called, which returns a new bound wrapper and the \_\_call\_\_\(\) method of that is invoked instead. This allows our wrapper to be used around descriptors as it propagates the descriptor protocol.  
  
So since using a function closure will ultimately fail if used around a decorator which is implemented as a descriptor, the situation we therefore have is that if we want everything to work, then decorators should always use a class based wrapper, where the class implements the descriptor protocol as shown.  
  
The question now is how do we address the other issues that were listed.  
  
We solved naming using functools.wrap\(\)/functools.update\_wrapper\(\) before, but what do they do and can we still use them.  
  
Well wraps\(\) just uses update\_wrapper\(\), so we just need to look at it.  


> WRAPPER\_ASSIGNMENTS = \('\_\_module\_\_',  
>  '\_\_name\_\_', '\_\_qualname\_\_', '\_\_doc\_\_',  
>  '\_\_annotations\_\_'\)

> WRAPPER\_UPDATES = \('\_\_dict\_\_',\) 

```
> def update\_wrapper\(wrapper, wrapped,  
>  assigned = WRAPPER\_ASSIGNMENTS,  
>  updated = WRAPPER\_UPDATES\): 
```

> wrapper.\_\_wrapped\_\_ = wrapped 

```
> for attr in assigned:  
>  try:  
>  value = getattr\(wrapped, attr\)  
>  except AttributeError:  
>  pass  
>  else:  
>  setattr\(wrapper, attr, value\) 
```

```
> for attr in updated:  
>  getattr\(wrapper, attr\).update\(  
>  getattr\(wrapped, attr, \{\}\)\)
```

What is shown here is what is in Python 3.3, although that actually has a bug in it, which is fixed in Python 3.4. :-\)  
  
Looking at the body of the function, three things are being done. First off a reference to the wrapped function is saved as \_\_wrapped\_\_. This is the bug, as it should be done last.  
  
The second is to copy those attributes such as \_\_name\_\_ and \_\_doc\_\_.  
  
Finally the third thing is to copy the contents of \_\_dict\_\_ from the wrapped function into the wrapper, which could actually result in quite a lot of objects needing to be copied.  
  
If we are using a function closure or straight class wrapper this copying is able to be done at the point that the decorator is applied.  
  
With the wrapper being a descriptor though, it technically now also needs to be done in the bound wrapper.  


```
> class bound\_function\_wrapper\(object\):  
>  def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped  
>  functools.update\_wrapper\(self, wrapped\) 
```

```
> class function\_wrapper\(object\):  
>  def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped  
>  functools.update\_wrapper\(self, wrapped\)
```

As the bound wrapper is created every time the wrapper is called for a function bound to a class, this is going to be too slow. We need a more performant way of handling this.  
  


###  Transparent object proxy

  
The solution to the performance issue is to use what is called an object proxy. This is a special wrapper class which looks and behaves like what it wraps.  


```
> class object\_proxy\(object\): 
```

```
> def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped  
>  try:  
>  self.\_\_name\_\_= wrapped.\_\_name\_\_  
>  except AttributeError:  
>  pass 
```

```
> @property  
>  def \_\_class\_\_\(self\):  
>  return self.wrapped.\_\_class\_\_ 
```

```
> def \_\_getattr\_\_\(self, name\):  
>  return getattr\(self.wrapped, name\)
```

A fully transparent object proxy is a complicated beast in its own right, so I am going to gloss over the details for the moment and cover it in a separate blog post at some point.  
  
The above example though is a minimal representation of what it does. In practice it actually needs to do a lot more than this though if it is to serve as a general purpose object proxy usable in the more generic use case of monkey patching.  
  
In short though, it copies limited attributes from the wrapped object to itself, and otherwise uses special methods, properties and \_\_getattr\_\_\(\) to fetch attributes from the wrapped object only when required thereby avoiding the need to copy across lots of attributes which may never actually be accessed.  
  
What we now do is derive our wrapper class from the object proxy and do away with calling update\_wrapper\(\).  


```
> class bound\_function\_wrapper\(object\_proxy\):  
>  def \_\_init\_\_\(self, wrapped\):  
>  super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\)
```

```
> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\) 
```

```
> class function\_wrapper\(object\_proxy\):  
>  def \_\_init\_\_\(self, wrapped\):  
>  super\(function\_wrapper, self\).\_\_init\_\_\(wrapped\)
```

```
> def \_\_get\_\_\(self, instance, owner\):  
>  wrapped = self.wrapped.\_\_get\_\_\( instance, owner\)  
>  return bound\_function\_wrapper\(wrapped\) 
```

```
> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\) 
```

In doing this, attributes like \_\_name\_\_ and \_\_doc\_\_, when queried from the wrapper, return the values from the wrapped function. We don't therefore as a result have the problem we did before where details were being returned from the wrapper instead.  
  
Using a transparent object proxy in this way also means that calls like inspect.getargspec\(\) and inspect.getsource\(\) will now work and return what we expect. So we have actually managed to solve those two problems at the same time without any extra effort, which is a bonus.  
  


###  Making this all more usable

  
Although this pattern addresses the problems which were originally identified, it consists of a lot of boiler plate code. Further, you now have two places in the code where the wrapped function is actually being called where you would need to insert the code to implement what the decorator was intended to do.  
  
Replicating this every time you need to implement a decorator would therefore be a bit of a pain.  
  
What we can instead do is wrap this all up and package it up into a decorator factory, thereby avoiding the need for this all to be done manually each time. How to do that will be the subject of the next blog post in this series.  
  
From that point we can start to look at how we can further improve the functionality and introduce new capabilities which are generally hard to pull off with the way that decorators are normally implemented.  
  
And before people start to complain that using this pattern is going to be too slow in the general use case, I will also address that in a future post as well, so just hold your complaints for now.

---

## Comments

### Unknown - January 7, 2014 at 11:09 PM

On mixing descriptors and decorators, I've often advised people that the descriptor part should wrap the decorator part. For example:  
  
@staticmethod  
@decorator  
def func\(\):  
...  
  
But not this:  
  
@decorator  
@staticmethod  
def func\(\):  
...  
  
Curious if you had any thoughts about this?

### Graham Dumpleton - January 8, 2014 at 8:47 AM

If that inner decorator is itself implemented as a descriptor, placing it inside of @classmethod will not strictly work properly. This is an issue with @classmethod and was one of the things I expected to cover in the next post.

### eternicode - January 9, 2014 at 10:23 AM

class bound\_function\_wrapper\(object\_proxy\):  
def \_\_init\_\_\(self, wrapped\):  
super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
  
I may be unaware of some nuance here, but isn't an \_\_init\_\_ that just calls super.\_\_init\_\_ the same as having no \_\_init\_\_ defined at all in the subclass?

### Graham Dumpleton - January 9, 2014 at 10:26 AM

True. I wanted to make is explicit as later on that constructor has extra arguments added which will be stored on the wrapper itself and used by other methods.

### Daniel Sank - May 25, 2014 at 2:41 AM

In the blog you propose two separate classes. You have function\_wrapper to be used as a decorator for both normal functions and methods, and you have bound\_function\_wrapper, which is invoked to handle cases where function\_wrapper is accessed as a descriptor. Does bound\_function\_wrapper need to exist? It seems that every place it might be invoked could be replaced by function\_wrapper, since function\_wrapper implements all of the methods that bound\_function\_wrapper implements, and with exactly the same code.  
  
class bound\_function\_wrapper\(object\_proxy\):  
def \_\_init\_\_\(self, wrapped\):  
super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
  
def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
return self.wrapped\(\*args, \*\*kwargs\)   
  
class function\_wrapper\(object\_proxy\):  
def \_\_init\_\_\(self, wrapped\):  
super\(function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
  
def \_\_get\_\_\(self, instance, owner\):  
wrapped = self.wrapped.\_\_get\_\_\( instance, owner\)  
return bound\_function\_wrapper\(wrapped\)   
  
def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
return self.wrapped\(\*args, \*\*kwargs\)

### Graham Dumpleton - May 25, 2014 at 1:02 PM

@Daniel You misunderstand. The function\_wrapper class is still used to handle the case where the function is first bound by the descriptor protocol. The bound\_function\_wrapper is the result of the binding process and not the starting point. It is similar to how instance methods in Python 2 exist in unbound and bound forms. It also isn't true that the methods of each are the same. The \_\_call\_\_\(\) method implementations need to be different. The bound wrapped also needs an instance variable. Trying to do it all in one class just be comes a bit messy and easier to separate out the concepts and not try and force it into one class. Some of the differences will become clearer in later blog posts in this series. I also advise to actually look at the source code of the wrapt package. This isn't a proposal. There is a working and available implementation for all of this.

