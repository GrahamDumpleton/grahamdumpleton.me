---
layout: post
title: "Transparent object proxies in Python."
author: "Graham Dumpleton"
date: "2014-08-17"
url: "http://blog.dscpl.com.au/2014/08/transparent-object-proxies-in-python.html"
post_id: "3651363996579395824"
blog_id: "2363643920942057324"
comments: 1
published_timestamp: "2014-08-17T14:57:00+10:00"
blog_title: "Graham Dumpleton"
---

This is a quick rejoinder to a specific comment made in Armin Ronacher's recent blog post titled '[The Python I Would Like To See](http://lucumr.pocoo.org/2014/8/16/the-python-i-would-like-to-see/)'.

In that post Armin gives the following example of something that is possible with old style Python classes.
    
    
    >>> original = 42  
    >>> class FooProxy:  
    ... def __getattr__(self, x):  
    ... return getattr(original, x)  
    ...  
    >>> proxy = FooProxy()  
    >>> proxy  
    42  
    >>> 1 + proxy  
    43  
    >>> proxy + 1  
    43

Armin then goes on to say:

> """We have less features today than we had in Python 2 for a more complex type system. Because the code above cannot be done with new style classes and more."""

Actually that isn't strictly true. It is possible to write a transparent object proxy using new style classes, but in doing so the proxy itself must adopt the conventions around the use of the special slot methods.
    
    
    >>> import wrapt  
    >>> original = 42  
    >>> proxy = wrapt.ObjectProxy(original)  
    >>> print(proxy)  
    42  
    >>> print(1 + proxy)  
    43  
    >>> print(proxy + 1)  
    43

Implementing a general purpose transparent object proxy is non trivial and there are lots of horrible corner cases you have to deal with. The Python standard library does actually have an example of such a proxy, albeit specifically for use in conjunction with weakref instances. Unfortunately the Python standard library itself doesn't get all the corner cases correct, which for one case you can read about in [\#19070](http://bugs.python.org/issue19070). It is also implemented in C, so isn't particularly useful as an example for illustrating what is required.

Because it is a complicated topic I am not going to go into the specifics of how to implement a transparent object proxy. It was previously my intent to post on just this topic in some followup posts to my prior series on decorators, as the decorator implementation I gave was actually implemented on top of a transparent object proxy, but I don't see myself doing that for the time being.

As a result, all I can suggest if you are interested, is that you have a dig through the code implementing my [wrapt](https://github.com/GrahamDumpleton/wrapt) package. It contains transparent object proxy implementations in both C code and as pure Python. It builds on that to implement a function wrapper with binding behaviour as well as all sorts of functions to support monkey patching and the implementation of decorators. There is also an implementation of a post import hook mechanism by which to trigger monkey patching at the time of modules being imported.

So if you are into mind bending stuff, have a look at wrapt.

---

## Comments

### Armin Ronacher - August 17, 2014 at 8:19 PM

I'm unfortunately well aware: https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/local.py\#L250

