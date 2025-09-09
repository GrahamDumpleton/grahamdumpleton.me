---
layout: post
title: "Implementing a factory for creating decorators."
author: "Graham Dumpleton"
date: "2014-01-08"
url: "http://blog.dscpl.com.au/2014/01/implementing-factory-for-creating.html"
post_id: "6271603585721452766"
blog_id: "2363643920942057324"
tags: ['decorators', 'python']
comments: 4
published_timestamp: "2014-01-08T17:46:00+11:00"
blog_title: "Graham Dumpleton"
---

This is the third post in my series of blog posts about Python decorators and how I believe they are generally poorly implemented. It follows on from the previous post titled '[The interaction between decorators and descriptors](/posts/2014/01/the-interaction-between-decorators-and/)', with the very first post in the series being '[How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/)'.  
  
In the very first post I described a number of ways in which the traditional way that Python decorators are implemented is lacking. These were:  
  


  * Preservation of function \_\_name\_\_ and \_\_doc\_\_.
  * Preservation of function argument specification.
  * Preservation of ability to get function source code.
  * Ability to apply decorators on top of other decorators that are implemented as descriptors.



  


In the followup post I described a pattern for implementing a decorator which built on top of what is called an object proxy, with the object proxy solving the first three issues. The final issue was dealt with by creating a function wrapper using the object proxy, which was implemented as a descriptor, and which performed object binding when a wrapper was used on class methods. This combination of the object proxy and a descriptor ensured that introspection continued to work properly and that the execution model of the Python object model was also respected.  
  
The issue at this point was how to make the solution more usable, eliminating the boiler plate and minimising the amount of code that someone implementing a decorator would need to write.  
  
In this post I will describe one such approach to simplifying the task of creating a decorator based on this pattern. This will be done by using a decorator as a factory to create decorators, requiring a user to only have to supply a single wrapper function which does the actual work of invoking the wrapped function, inserting any extra work that the specific decorator is intended to carry out as necessary.  


  


###  Pattern for implementing the decorator

  


Just to refresh where we got to last time, we had an implementation of an object proxy as:

> class object\_proxy\(object\): 

> def \_\_init\_\_\(self, wrapped\):  
>  self.wrapped = wrapped  
>  try:  
>  self.\_\_name\_\_= wrapped.\_\_name\_\_  
>  except AttributeError:  
>  pass 

> @property  
>  def \_\_class\_\_\(self\):  
>  return self.wrapped.\_\_class\_\_ 

> def \_\_getattr\_\_\(self, name\):  
>  return getattr\(self.wrapped, name\)

As pointed out the last time, this is a minimal representation of what it does. In practice it actually needs to do a lot more than this if it is to serve as a general purpose object proxy usable in the more generic use case of monkey patching.

  


The decorator itself would then be implemented per the pattern:

> class bound\_function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped\):  
>  super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\) 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\) 

> class function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped\):  
>  super\(function\_wrapper, self\).\_\_init\_\_\(wrapped\) 

> def \_\_get\_\_\(self, instance, owner\):  
>  wrapped = self.wrapped.\_\_get\_\_\( instance, owner\)  
>  return bound\_function\_wrapper\(wrapped\) 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapped\(\*args, \*\*kwargs\) 

When the wrapper is applied to a normal function, the \_\_call\_\_\(\) method of the wrapper is used. If the wrapper is applied to a method of a class, the \_\_get\_\_\(\) method is called when the attribute is accessed, which returns a new bound wrapper and the \_\_call\_\_\(\) method of that is invoked instead when a call is made. This allows our wrapper to be used around descriptors as it propagates the descriptor protocol, also binding the wrapped object as necessary.

  


###  A decorator for creating decorators

  


So we have a pattern for implementing a decorator that appears to work correctly, but as already mentioned, needing to do all that each time is more work than we really want. What we can do therefore is create a decorator to help us create decorators. This would reduce the code we need to write for each decorator to a single function, allowing us to simplify the code to just:

> @decorator  
>  def my\_function\_wrapper\(wrapped, args, kwargs\):  
>  return wrapped\(\*args, \*\*kwargs\) 

> @my\_function\_wrapper  
>  def function\(\):  
>  pass

What would this decorator factory need to look like?

  


As it turns out, our decorator factory is quite simple and isn't really much different to using a partial\(\), combining our new wrapper argument from when the decorator is defined, with the wrapped function when the decorator is used and passing them into our function wrapper object.

> def decorator\(wrapper\):  
>  @functools.wraps\(wrapper\)  
>  def \_decorator\(wrapped\):  
>  return function\_wrapper\(wrapped, wrapper\)  
>  return \_decorator

We now just need to amend our function wrapper implementation to delegate the actual execution of the wrapped object to the user supplied decorator wrapper function.

> class bound\_function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped, wrapper\):  
>  super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
>  self.wrapper = wrapper 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapper\(self.wrapped, args, kwargs\) 

> class function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped, wrapper\):  
>  super\(function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
>  self.wrapper = wrapper 

> def \_\_get\_\_\(self, instance, owner\):  
>  wrapped = self.wrapped.\_\_get\_\_\(instance, owner\)  
>  return bound\_function\_wrapper\(wrapped, self.wrapper\) 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapper\(self.wrapped, args, kwargs\)

The \_\_call\_\_\(\) method of our function wrapper, for when it is used around a normal function, now just calls the user supplied decorator wrapper function with the wrapped function and arguments, leaving the calling of the wrapped function up to the user supplied decorator wrapper function.

  


In the case where binding a function, the wrapper is also passed to the bound wrapper. The bound wrapper is more or less the same, with the \_\_call\_\_\(\) method delegating to the user supplied decorator wrapper function.

  


So we can make creating decorators easier using a factory. Lets now check that this will in fact work in all cases in which it could be applied and also see what other problems we can find and whether we can improve on those situations as well.

  


###  Decorating methods of classes

  


The first such area which can cause problems is creating a single decorator that can work on both normal functions and instance methods of classes.

  


To test out how our new decorator works, we can print out the args passed to the wrapper when the wrapped function is called and can compare the results.

> @decorator  
>  def my\_function\_wrapper\(wrapped, args, kwargs\):  
>  print\('ARGS', args\)  
>  return wrapped\(\*args, \*\*kwargs\)

First up lets try wrapping a normal function:

> @my\_function\_wrapper  
>  def function\(a, b\):  
>  pass 

> >>> function\(1, 2\)  
>  ARGS \(1, 2\)

As would be expected, just the two arguments passed when the function is called are output.

  


What about when wrapping an instance method?

> class Class\(object\):  
>  @my\_function\_wrapper  
>  def function\_im\(self, a, b\):  
>  pass 

> c = Class\(\) 

> >>> c.function\_im\(\)  
>  ARGS \(1, 2\)

Once again just the two arguments passed when the instance method is called are displayed. How the decorator works for both the normal function and the instance method is therefore the same.

  


The problem here is what if the user within their decorator wrapper function wanted to know what the actual instance of the class was. We have lost that information when the function was bound to the instance of the class as it is now associated with the bound function passed in, rather than the argument list.

  


To solve this problem we can remember what the instance was that was passed to the \_\_get\_\_\(\) method when it was called to bind the function. This can then be passed through to the bound wrapper when it is created.

> class bound\_function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped, instance, wrapper\):  
>  super\(bound\_function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
>  self.instance = instance  
>  self.wrapper = wrapper 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapper\(self.wrapped, self.instance, args, kwargs\) 

> class function\_wrapper\(object\_proxy\): 

> def \_\_init\_\_\(self, wrapped, wrapper\):  
>  super\(function\_wrapper, self\).\_\_init\_\_\(wrapped\)  
>  self.wrapper = wrapper 

> def \_\_get\_\_\(self, instance, owner\):  
>  wrapped = self.wrapped.\_\_get\_\_\( instance, owner\)  
>  return bound\_function\_wrapper\(wrapped, instance, self.wrapper\) 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  return self.wrapper\(self.wrapped, None, args, kwargs\)

In the bound wrapper, the instance pointer can then be passed through to the decorator wrapper function as an extra argument. To be uniform for the case of a normal function, in the top level wrapper we pass None for this new instance argument.

  


We can now modify our wrapper function for the decorator to output both the instance and the arguments passed.

> @decorator  
>  def my\_function\_wrapper\(wrapped, instance, args, kwargs\):  
>  print\('INSTANCE', instance\)  
>  print\('ARGS', args\)  
>  return wrapped\(\*args, \*\*kwargs\) 

> >>> function\(1, 2\)  
>  INSTANCE None  
>  ARGS \(1, 2\) 

> >>> c.function\_im\(1, 2\)  
>  INSTANCE <\_\_main\_\_.Class object at 0x1085ca9d0>  
>  ARGS \(1, 2\)

This change therefore allows us to be able to distinguish between a normal function call and an instance method call within the one decorator wrapper function. The reference to the instance is even passed separately so we don't have to juggle with the arguments to move it out of the way for an instance method when calling the original wrapped function.

  


Now there is one final scenario in which an instance method can be called which we still need to check. This is calling an instance method by calling the function on the class and passing the object instance explicitly as the first argument.

> >>> Class.function\_im\(c, 1, 2\)  
>  INSTANCE None  
>  ARGS \(<\_\_main\_\_.Class object at 0x1085ca9d0>, 1, 2\)

Unfortunately passing in the instance explicitly as an argument against the function from the class, results in the instance passed to the decorator wrapper function being None, with the reference to the instance getting passed through as the first argument instead. This isn't really a desirable outcome.

  


To deal with this variation, we can check for instance being None before calling the decorator wrapper function and pop the instance off the start of the argument list. We then use a partial to bind the instance to the wrapped function ourselves and call the decorator wrapper function.

> class bound\_function\_wrapper\(object\_proxy\): 

> def \_\_call\_\_\(self, \*args, \*\*kwargs\):  
>  if self.instance is None:  
>  instance, args = args\[0\], args\[1:\]  
>  wrapped = functools.partial\(self.wrapped, instance\)  
>  return self.wrapper\(wrapped, instance, args, kwargs\) 

> return self.wrapper\(self.wrapped, self.instance, args, kwargs\)

We then get the same result no matter whether the instance method is called via the class or not.

> >>> Class.function\_im\(c, 1, 2\)  
>  INSTANCE <\_\_main\_\_.Class object at 0x1085ca9d0>  
>  ARGS \(1, 2\)

So everything works okay for instance methods, with the argument list seen by the decorator wrapper function being the same as if a normal function had been wrapped. At the same time though, by virtue of the new instance argument, we can if need be act on the instance of a class where the decorator was applied to an instance method of a class.

  


What about other method types that a class can have, specifically class method and static methods.

> class Class\(object\):  
>  @my\_function\_wrapper  
>  @classmethod  
>  def function\_cm\(cls, a, b\):  
>  pass 

> >>> Class.function\_cm\(1, 2\)  
>  INSTANCE 1  
>  ARGS \(2,\)

As can be seen, this fiddle has though upset things for when we have a class method, also causing the same issue for a static method. In both those cases the instance would initially have been passed as None when the function was bound. The result is that the real first argument ends up as the instance, which is obviously going to be quite wrong.

  


What to do?

  


###  A universal decorator

  


So we aren't quite there yet, but what are we trying to achieve in even trying to do this? What was wrong with our initial pattern for the decorator?

  


The ultimate goal here is what I call a universal decorator. A single decorator that can be applied to a normal function, an instance method, a class method, a static method or even a class, with the decorator being able to determine at the point it was called the context in which it was used.

  


Right now with the way that decorators are normally implemented this is not possible. Instead different decorators are provided to be used in the different contexts, meaning duplication of the code into each, or the use of hacks to try and convert decorators created for one purpose so they can be used in a different context.

  


What I am instead aiming for is the ability to do:

> @decorator  
>  def universal\(wrapped, instance, args, kwargs\):  
>  if instance is None:  
>  if inspect.isclass\(wrapped\):  
>  \# class.  
>  else:  
>  \# function or staticmethod.  
>  else:  
>  if inspect.isclass\(instance\):  
>  \# classmethod.  
>  else:  
>  \# instancemethod.

At this point we have got things working for normal functions and instance methods, we just now need to work out how to handle class methods, static methods and the scenario where a decorator is applied to a class.

  


The next post in this series will continue to pursue this goal and describe how our decorator can be tweaked further to get there.

---

## Comments

### Pekka Klärck - January 8, 2014 at 10:56 PM

Really interesting series. Looking forward for next episodes.  
  
Some questions/comments:  
\- Do you plan to release your final decorator factory in PyPI?  
\- Have you tested the code with other interpreters than CPython \(PyPy, Jython, IronPython\)?  
\- Any change to get the code syntax highlighted?

### Graham Dumpleton - January 9, 2014 at 8:55 AM

The package has been available for some months now, I haven't wanted to link to the package yet so people don't get distracted from the story am trying to tell. Search and you shall find. The package is tested on CPython 2.6, 2.7, 3.3 and pypy. Nothing I can do about syntax highlight as am using crappy Google blogger.

### Pekka Klärck - January 10, 2014 at 1:24 AM

Good to hear the code is available as a package. I don't have urgent need for it so I'll continue following the story.  
  
It's a shame that Blogger doesn't make syntax highlighting easy. You could use, for example, Pygments to highlight the code outside Blogger and add generated HTML and CSS to your post. That's far from being convenient and I totally understand if you don't think it's worth the effort.

### Graham Dumpleton - January 10, 2014 at 7:47 AM

Although blogger allows you to cut and paste stuff from elsewhere and it preserves colours, it also preserves font size as well and the result is generally then totally out with what it is using. Plus that the edit view appears to use a different font size to the final result so it gets all very tricky to get it right. Their editor is quite horrible, but moving everything off to another blog system was going to be more painful than it is worth at this point, plus would take more time than I have.

