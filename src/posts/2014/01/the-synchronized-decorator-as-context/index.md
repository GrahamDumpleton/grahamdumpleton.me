---
layout: post
title: "The @synchronized decorator as context manager."
author: "Graham Dumpleton"
date: "2014-01-15"
url: "http://blog.dscpl.com.au/2014/01/the-synchronized-decorator-as-context.html"
post_id: "2482447269345994553"
blog_id: "2363643920942057324"
tags: ['decorators', 'python']
comments: 0
published_timestamp: "2014-01-15T22:43:00+11:00"
blog_title: "Graham Dumpleton"
---

This is the eigth post in my series of blog posts about Python decorators and how I believe they are generally poorly implemented. It follows on from the previous post titled '[The missing @synchronized decorator](/posts/2014/01/the-missing-synchronized-decorator/)', with the very first post in the series being '[How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/)'.  
  
In the previous post I described how we could use our new universal decorator pattern to implement a better @synchronized decorator for Python. The intent in doing this was to come up with a better approximation of the equivalent synchronization mechanisms in Java.  
  
Of the two synchronization mechanisms provided by Java, [synchronized methods](http://docs.oracle.com/javase/tutorial/essential/concurrency/syncmeth.html) and [synchronized statements](http://docs.oracle.com/javase/tutorial/essential/concurrency/locksync.html), we have however so far only implemented an equivalent to synchronized methods.  
  
In this post I will describe how we can take our @synchronized decorator and extend it to also be used as a context manager, thus providing an an equivalent of synchronized statements in Java.  
  


###  The original @synchronized decorator

  
The implementation of our @synchronized decorator so far is:  


> @decorator  
>  def synchronized\(wrapped, instance, args, kwargs\):  
>  if instance is None:  
>  owner = wrapped  
>  else:  
>  owner = instance 

> lock = vars\(owner\).get\('\_synchronized\_lock', None\) 

> if lock is None:  
>  meta\_lock = vars\(synchronized\).setdefault\(  
>  '\_synchronized\_meta\_lock', threading.Lock\(\)\) 

> with meta\_lock:  
>  lock = vars\(owner\).get\('\_synchronized\_lock', None\)  
>  if lock is None:  
>  lock = threading.RLock\(\)  
>  setattr\(owner, '\_synchronized\_lock', lock\) 

> with lock:  
>  return wrapped\(\*args, \*\*kwargs\)

By determining whether the decorator is being used to wrap a normal function, a method bound to a class instance or a class, and with the decorator changing behaviour as a result, we are able to use the one decorator implementation in a number of scenarios.  


> @synchronized \# lock bound to function1  
>  def function1\(\):  
>  pass 

> @synchronized \# lock bound to function2  
>  def function2\(\):  
>  pass 

> @synchronized \# lock bound to Class  
>  class Class\(object\): 

> @synchronized \# lock bound to instance of Class  
>  def function\_im\(self\):  
>  pass 

> @synchronized \# lock bound to Class  
>  @classmethod  
>  def function\_cm\(cls\):  
>  pass

> @synchronized \# lock bound to function\_sm  
>  @staticmethod  
>  def function\_sm\(\):  
>  pass

What we now want to do is modify the decorator to also allow:  


> class Object\(object\): 

> @synchronized  
>  def function\_im\_1\(self\):  
>  pass 

> def function\_im\_2\(self\):  
>  with synchronized\(self\):  
>  pass

That is, as well as being able to be used as a decorator, we enable it to be used as a context manager in conjunction with the 'with' statement. By doing this it then provides the ability to only acquire the corresponding lock for a selected number of statements within a function rather than the whole function.  
  
For the case of acquiring the same lock used by instance methods, we would pass the 'self' argument or instance object into 'synchronized' when used as a context manager. It could instead also be passed the class type if needing to synchronize with class methods.  
  


###  The function wrapper as context manager

  
Right now with how the decorator is implemented, when we use 'synchronized' as a function call, it will return an instance of our function wrapper class.  


> >>> synchronized\(None\)  
>  <\_\_main\_\_.function\_wrapper object at 0x107b7ea10>

This function wrapper does not implement the \_\_enter\_\_\(\) and \_\_exit\_\_\(\) functions that are required for an object to be used as a context manager. Since the function wrapper type is our own class, all we need to do though is create a derived version of the class and use that instead. Because though the creation of that function wrapper is bound up within the definition of @decorator, we need to bypass @decorator and use the function wrapper directly.  
  
The first step therefore is to rewrite our @synchronized decorator so it doesn't use @decorator.  


> def synchronized\(wrapped\): 

> def \_synchronized\_lock\(owner\):  
>  lock = vars\(owner\).get\('\_synchronized\_lock', None\) 

> if lock is None:  
>  meta\_lock = vars\(synchronized\).setdefault\(  
>  '\_synchronized\_meta\_lock', threading.Lock\(\)\) 

> with meta\_lock:  
>  lock = vars\(owner\).get\('\_synchronized\_lock', None\)  
>  if lock is None:  
>  lock = threading.RLock\(\)  
>  setattr\(owner, '\_synchronized\_lock', lock\) 

> return lock 

> def \_synchronized\_wrapper\(wrapped, instance, args, kwargs\):  
>  with \_synchronized\_lock\(instance or wrapped\):  
>  return wrapped\(\*args, \*\*kwargs\) 

> return function\_wrapper\(wrapped, \_synchronized\_wrapper\)

This works the same as our original implementation but we now have access to the point where the function wrapper was created. With that being the case, we can now create a class which derives from the function wrapper and adds the required methods to satisfy the context manager protocol.  


> def synchronized\(wrapped\): 

> def \_synchronized\_lock\(owner\):  
>  lock = vars\(owner\).get\('\_synchronized\_lock', None\) 

> if lock is None:  
>  meta\_lock = vars\(synchronized\).setdefault\(  
>  '\_synchronized\_meta\_lock', threading.Lock\(\)\) 

> with meta\_lock:  
>  lock = vars\(owner\).get\('\_synchronized\_lock', None\)  
>  if lock is None:  
>  lock = threading.RLock\(\)  
>  setattr\(owner, '\_synchronized\_lock', lock\) 

> return lock 

> def \_synchronized\_wrapper\(wrapped, instance, args, kwargs\):  
>  with \_synchronized\_lock\(instance or wrapped\):  
>  return wrapped\(\*args, \*\*kwargs\) 

> class \_synchronized\_function\_wrapper\(function\_wrapper\): 

> def \_\_enter\_\_\(self\):  
>  self.\_lock = \_synchronized\_lock\(self.wrapped\)  
>  self.\_lock.acquire\(\)  
>  return self.\_lock 

> def \_\_exit\_\_\(self, \*args\):  
>  self.\_lock.release\(\) 

> return \_synchronized\_function\_wrapper\(wrapped, \_synchronized\_wrapper\)

We now have two scenarios for what can happen.  
  
In the case of 'synchronized' being used as a decorator still, our new derived function wrapper will wrap the function or method it was applied to. When that function or class method is called, the existing \_\_call\_\_\(\) method of the function wrapper base class will be called and the decorator semantics will apply with the wrapper called to acquire the appropriate lock and call the wrapped function.  
  
In the case where is was instead used for the purposes of a context manager, our new derived function wrapper would actually be wrapping the class instance or class type. Nothing is being called though and instead the 'with' statement will trigger the execution of the \_\_enter\_\_\(\) and \_\_exit\_\_\(\) methods to acquire the appropriate lock around the context of the statements to be executed.  
  
So all nice and neat and not even that complicated compared to previous attempts at doing the same thing which were referenced in the prior post on this topic.  
  


###  It isn't just about @decorator

  
Now one of the things that this hopefully shows is that although @decorator can be used to create your own custom decorators, this isn't always the most appropriate way to go. The separate existence of the function wrapper gives a great deal of flexibility in what one can do as far as wrapping objects to modify the behaviour. One can also drop down and use the object proxy directly in certain circumstances.  
  
All together these provide a general purpose set of tools for doing any sort of wrapping or monkey patching and not just for use in decorators. I will now start to shift the focus of this series of blog posts to look more at the more general area of wrapping and monkey patching.  
  
Before I do get into that, in my next post I will first talk about the performance implications implicit in using the function wrapper which has been described when compared to the more traditional way of using function closures to implement decorators. This will include overhead comparisons where the complete object proxy and function wrapper classes are implemented as a Python C extension for added performance.