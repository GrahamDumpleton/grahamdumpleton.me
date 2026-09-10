---
layout: guide
title: "Decorators and monkey patching."
description: "Why the usual Python decorator pattern is wrong and how to implement a better one, and the problems of monkey patching: applying patches safely, ordering, and automatic patching."
url: "http://blog.dscpl.com.au/p/decorators-and-monkey-patching.html"
post_id: "3350721465154129789"
blog_id: "2363643920942057324"
comments: 0
blog_title: "Graham Dumpleton"
---

Prior posts on the topic of decorators and monkey patching are as follows.  
  
This batch of posts deals with Python decorators, how the simple pattern most people use isn't correct and how to implement a better decorator.  

  * [How you implemented your Python decorator is wrong](/posts/2014/01/how-you-implemented-your-python/).
  * [The interaction between decorators and descriptors](/posts/2014/01/the-interaction-between-decorators-and/).
  * [Implementing a factory for creating decorators](/posts/2014/01/implementing-factory-for-creating/).
  * [Implementing a universal decorator](/posts/2014/01/implementing-universal-decorator/).
  * [Decorators which accept arguments](/posts/2014/01/decorators-which-accept-arguments/).
  * [Maintaining decorator state using a class](/posts/2014/01/maintaining-decorator-state-using-class/).
  * [The missing @synchronized decorator](/posts/2014/01/the-missing-synchronized-decorator/).
  * [The @synchronized decorator as context manager](/posts/2014/01/the-synchronized-decorator-as-context/).
  * [Performance overhead of using decorators](/posts/2014/02/performance-overhead-of-using-decorators/).
  * [Performance overhead when applying decorators to methods](/posts/2014/02/performance-overhead-when-applying/).
  * [Transparent object proxies in Python](/posts/2014/08/transparent-object-proxies-in-python/).

This batch of posts deals with issues around the more general problem of monkey patching Python code.

  * [Safely applying monkey patches in Python](/posts/2015/03/safely-applying-monkey-patches-in-python/).
  * [Using wrapt to support testing of software](/posts/2015/03/using-wrapt-to-support-testing-of/).
  * [Ordering issues when monkey patching in Python](/posts/2015/03/ordering-issues-when-monkey-patching-in/).
  * [Automatic patching of Python applications.](/posts/2015/04/automatic-patching-of-python/)

Later posts on wrapt, covering what the package can do now, are collected under
[practical uses for the wrapt package](/guides/using-the-wrapt-package/), and the
[wrapture](/guides/testing-and-tracing-with-wrapture/) posts cover a separate package
built on the same machinery for testing and tracing.
