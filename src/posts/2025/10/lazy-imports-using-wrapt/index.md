---
title: "Lazy imports using wrapt"
description: "How to implement Python lazy import mechanism using wrapt."
date: 2025-10-04
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt"]
draft: false
---

[PEP 810](https://peps.python.org/pep-0810/) (explicit lazy imports) was recently released for Python. The idea with this PEP is to add explicit syntax for implementing lazy imports for modules in Python.

```
lazy import json
```

Lazily importing modules in Python is not a new idea and there have been a number of packages available to achieve a similar result, they just lacked an explicit language syntax to hide what is actually going on under the covers.

When I saw this PEP it made me realise that a new feature I added into `wrapt` for upcoming 2.0.0 release can be used to implement a lazy import with little effort.

For those who only know of `wrapt` as being a package for implementing Python decorators, it should be known that the ability to implement decorators using the approach it does, was merely one outcome of the true reason for `wrapt` existing.

The actual reason `wrapt` was created was to be able to perform monkey patching of Python code.

One key aspect of being able to monkey patch Python code is to be able to have the ability to wrap target objects in Python with a wrapper which acts as a transparent object proxy for the original object. By extending the object proxy type, one can then intercept access to the target object to perform specific actions.

For the purpose of this discussion we can ignore the step of creating a custom object proxy type and look at just how the base object proxy works.

```
import wrapt

import graphlib

print(type(graphlib))

print(id(graphlib.TopologicalSorter), graphlib.TopologicalSorter)

xgraphlib = wrapt.ObjectProxy(graphlib)

print(type(xgraphlib))

print(id(graphlib.TopologicalSorter), xgraphlib.TopologicalSorter)
```

In this example we import a module called `graphlib` from the Python standard library. We then access from that module the class `graphlib.TopologicalSorter` and print it out.

When we wrap the same module with an object proxy, the aim is that anything you could do with the original module, could also be done via the object proxy. The output from the above is thus:

```
<class 'module'>
35852012560 <class 'graphlib.TopologicalSorter'>
<class 'ObjectProxy'>
35852012560 <class 'graphlib.TopologicalSorter'>
```

verifying that in both cases the `TopologicalSorter` is in fact the same object, even though for the proxy the apparent type is different.

The new feature which has been added for `wrapt` version 2.0.0 is a lazy object proxy. That is, instead of passing to the object proxy when created the target object to be wrapped, you pass a function, with this function being called to create or otherwise obtain the target object to be wrapped, the first time the proxy object is accessed.

Using this feature we can easily implement lazy module importing.

```
import sys
import wrapt

def lazy_import(name):
    return wrapt.LazyObjectProxy(lambda: __import__(name))

graphlib = lazy_import("graphlib")

print("sys.modules['graphlib'] =", sys.modules.get("graphlib", None))

print(type(graphlib))

print(graphlib.TopologicalSorter)

print("sys.modules['graphlib'] =", sys.modules.get("graphlib", None))
```

Running this the output is:

```
sys.modules['graphlib'] = None
<class 'LazyObjectProxy'>
<class 'graphlib.TopologicalSorter'>
sys.modules['graphlib'] = <module 'graphlib' from '.../lib/python3.13/graphlib.py'>
```

One key thing to note here is that when the lazy import is setup, no changes have been made to `sys.modules`. It is only later when the module is truly imported that you see an entry in `sys.modules` for that module name.

Some lazy module importers work by injecting into `sys.modules` a fake module object for the target module. This has to be done right up front when the application is started. Because the fake entry exists, when `import` is later used to import that module it thinks it has already been imported and thus what is added into the scope where `import` is used is the fake module, with the actual module not being imported at that point.

What then happens is that when code attempts to use something from the module, an overridden `__getattr__` special dunder method on the fake module object gets triggered, which on the first use causes the actual module to then be imported.

That `sys.modules` is modified and a fake module added is one of the criticisms one sees about such lazy module importers. That is, the change they make is global to the whole application which could have implications such as where side affects of importing a module are expected to be immediate.

With the way the `wrapt` example works above, no global change is required to `sys.modules`, and instead impacts are only local to the scope where the lazy import was made.

Reducing the impacts to just the scope where the lazy import was used is actually one of the goals of the PEP. The example using `wrapt` shows that it can be done, but it means you can't use an `import` statement, but then that is what the PEP aims to still allow, albeit they still require a new `lazy` keyword for when doing the import. Either way, the code where you want to have a lazy import needs to be different.

The other thing which the PEP should avoid is the module reference in the scope where the module is imported being any sort of fake module object. Initially the module reference would effectively be a place holder, but as soon as used, the actual module would be imported and the place holder replaced.

For the `wrapt` example the module reference would always be a proxy object, although technically with a bit of stack diving trickey you could also replace the module reference with the actual module as a side effect of the first use. I will explore that possibility in a followup post.
