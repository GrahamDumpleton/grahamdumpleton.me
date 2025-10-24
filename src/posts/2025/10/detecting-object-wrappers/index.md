---
title: "Detecting object wrappers"
description: "How to detect if an object has already been wrapped."
date: 2025-10-24
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt"]
draft: false
---

It should not need to be said, but monkey patching is evil.

At least that is the mantra we like to recite, but reality is that for some things in Python it is the only practical solution.

The best example of this and the reason that `wrapt` was created in the first place, is to instrument existing Python code to collect metrics about its performance when run in production.

Since one cannot expect a customer for an application performance monitoring (APM) service to modify their code, as well as code of the third party dependencies they may use, transparently reaching in and monkey patching code at runtime is the best one can do.

Doing this can be fraught with danger and one has to be very cautious on how you monkey patch code and what the patches do. It is all well and good if you are doing this only for your own code and so any issues that crop up only affect yourself, but if applying such changes to a customers application code in order for them to use your service, you have to be even more careful.

This caution needs to be elevated to the next level again for `wrapt` since it is the go to package for monkey patching Python code in such situations.

With such caution in mind, the latest version of `wrapt` was marked as a major version update. In general I thought the changes were good and everything should still be compatible for use cases I knew of, but you never know what strange things people do. My memory also isn't the best and I will not necessarily remember all the tricks even I have used in the past when using `wrapt` and how they might be affected. So a major version update it was, just to be safe.

I naively thought that everything should then be good and users of `wrapt` would be diligent and ensure they tested their usage of this major new version before updating. Unfortunately, one major SaaS vendor using `wrapt` wasn't pinning their dependencies against the major version. This resulted in their customers unknowingly being upgraded to the new major version of `wrapt` and although I don't know the full extent of it, apparently this did cause a bit of unexpected havoc for some of their users.

The reason for the problems that arose were that monkey patching was being done dynamically at time of use of some code, vs at time of import. This is nothing strange in itself when doing monkey patching, but the issue was that the code needed to check whether the monkey patches had already been applied and if it had, it should not be done a second time. Detecting this situation is a bit tricky and the simple solution may not always work. Everything was made worse by the fact that `wrapt` made changes to the class hierarchy for the object proxies it provides.

## Object proxy hierarchy

Prior to `wrapt` version 2.0.0, the class hierarchy for the object proxy and function wrappers were as follows.

```python
class ObjectProxy: ...

class CallableObjectProxy(ObjectProxy): ...

class _FunctionWrapperBase(ObjectProxy): ...
class BoundFunctionWrapper(_FunctionWrapperBase): ...
class FunctionWrapper(_FunctionWrapperBase): ...
```

Decorators and generic function wrappers used the `FunctionWrapper` class. If needing to create your own custom object proxies you would derive your custom wrapper class from `ObjectProxy`.

The `_FunctionWrapperBase` was an internal implementation detail and would never be used directly. Except for some corner cases the `BoundFunctionWrapper` class should also never need to be used directly.

In `wrapt` version 2.0.0, this hierarchy was changed, but with some new proxy class types thrown in as well. End result looks as follows.

```python
class BaseObjectProxy: ...
class ObjectProxy(BaseObjectProxy): ...

class AutoObjectProxy(BaseObjectProxy): ...
class LazyObjectProxy(AutoObjectProxy): ...

class CallableObjectProxy(BaseObjectProxy): ...

class _FunctionWrapperBase(BaseObjectProxy): ...
class BoundFunctionWrapper(_FunctionWrapperBase): ...
class FunctionWrapper(_FunctionWrapperBase): ...
```

The reason for introducing `BaseObjectProxy` was that early on in the life of `wrapt` some bad choices were made as to what default proxy methods were added to the `ObjectProxy` class. One of these was for the special `__iter__()` method.

This method presented problems because some code out there, rather than simply attempting to iterate over an object and catching the resulting exception when it wasn't iterable, would try and optimise things, or change behaviour based on whether the `__iter__()` method existed on an object. Even though a wrapped object might not be iterable and define that method, because the object proxy always provided it, it would cause problems with code which had that check for the existance of `__iter__()`.

It was quite a long time before this mistake of adding `__iter__()` was noticed and it couldn't just be backed out as that would then break code which became dependent on that proxy method existing. Taking the proxy method away would have forced people to create a custom object proxy class of their own which added it back for their use case, or at the minimum they would need to add it to their existing custom object proxy class.

In `wrapt` version 2.0.0 it was decided to finally try and address this mistake. The new `BaseObjectProxy` class is the same as the original `ObjectProxy` class except that the proxy method for `__iter__()` has been removed. The only thing in the `ObjectProxy` class in version 2.0.0 is the addition of the `__iter__()` method to keep backward compatibility with code out there using `wrapt`.

The recommended approach going forward is that the `ObjectProxy` class should effectively be ignored and when creating a custom object proxy, you should instead inherit from `BaseObjectProxy`. If you need a proxy method for `__iter__()`, you should add it explicitly in your custom object proxy.

## Testing for an object proxy

I thought the above changes were reasonable and should allow existing code using `wrapt` to continue to work. I have to admit though that I did forget one situation where the change may cause a problem. This is when testing whether an object is already wrapped by an object proxy, in order to avoid applying the same object proxy a second time.

In part I probably overlooked it as it isn't a reliable test to use in the first place if you used the simple way of doing it. As such, when I have had to do it in the past, I have avoided the simple way and used a more complicated test.

The simple test in this case that I am referring to is a test of the form:

```
if not isinstance(object, ObjectProxy):
    ... add custom object proxy to object
```

Prior to `wrapt` 2.0.0 this test could be applied to an object to test whether it was wrapped by a custom object proxy, including `FunctionWrapper` or `BoundFunctionWrapper` as used by decorators, or a generic function wrapper. The test relied on checking whether the object was actually a wrapper derived from the `ObjectProxy` base class.

As I understand it, this is the test that was being used in the instrumentation package used by the SaaS product that had all the issues when it suddenly started using `wrapt` version 2.0.0 due to not being pinned against the major version of `wrapt`.

With `wrapt` version 2.0.0 this check would start failing for `FunctionWrapper` and `BoundFunctionWrapper` as they no longer derive from `ObjectProxy`, but derived from `BaseObjectProxy` instead.

Even if these changes to the class hierarchy hadn't been made in `wrapt`, this test was already fragile and could have broken at some point for other reasons.

Take for example if the original code which was being patched decided to start using `wrapt` themselves to add a decorator to the function which later code then tried to monkey patch. Since the decorator using `wrapt` would pass the test for already being wrapped, the code doing the monkey patching would wrongly assume that it's own object proxy had already been applied and not add it. Thus the target function would not be instrumented as intended.

Another case is where there were multiple packages trying to monkey patch the same function for different purposes. If both used `wrapt` to do the monkey patching, but each with their own custom object proxy, the first to apply the monkey patch would win if the latter was testing whether it should apply its own monkey patch.

In other words, the test is not specific enough and would detect the presense of any object proxy wrapping the target object. This isn't all though and other issues can also arise as will get to later.

Anyway, the end result of this test not working as intended when the SaaS package started using `wrapt` version 2.0.0 was that every time it tested whether it had already applied the generic function wrapper using `FunctionWrapper`, it thought it hadn't and so it would add it again. As the number of times the wrapper was added grew, so did memory usage by the application. It seems that there being a problem was only finally noticed when the number of nested function wrappers became so great that the Python call stack size was exceeded when the wrapped function was being called. Up till then, as well as memory usage being affected, performance would also have been affected, as well as possibly any metrics data captured.

The quick fix to ensure this code would also work with `wrapt` version 2.0.0 would be to use something like the following.

```
import wrapt

BASE_OBJECT_PROXY = wrapt.ObjectProxy

if hasattr(wrapt, "BaseObjectProxy"):
    BASE_OBJECT_PROXY = wrapt.BaseObjectProxy

if not isinstance(object, BASE_OBJECT_PROXY):
    ... add custom object proxy to object
```

This is still going to be fragile though as noted above, even if fixes the immediate problem.

If using a custom object proxy class, it would be better to test for the specific type of that custom object proxy.

```
if not isinstance(object, CustomObjectProxy):
    object = CustomObjectProxy(object)
```

This is better because the custom object proxy is your type and so it is properly testing that it is in fact your wrapper.

If it was the case they were using `FunctionWrapper`, they would likely not have encountered an issue if they had used:

```
if not isinstance(object, FunctionWrapper):
    object = FunctionWrapper(object, ...)
```

but then it still isn't detecting whether it was their specific wrapper.

Depending on how the monkey patch is being applied, it would still be better to create your own empty custom function wrapper class type:

```
class CustomFunctionWrapper(FunctionWrapper): pass

if not isinstance(object, CustomFunctionWrapper):
    object = CustomFunctionWrapper(object, ...)
```

Testing explicitly against your own custom object type is therefore better, but still not foolproof.

## Nested function wrappers

Where this can still fall apart is where multiple wrappers are applied to the same target function. If your custom wrapper was added first, but then another applied on top, when you come back to check whether your wrapper has already been applied, you will not see it if looking for a wrapper using your custom type.

There are two things that might help in this situation.

The first is that for `wrapt` object proxies at least, if you try and access an attribute, if it does not exist on the wrapper, it will lookup whether it exists on the wrapped object.

This means that if you add a uniquely named attribute to a custom object proxy, you can test whether your object proxy wraps an object by looking up that attribute. Because attribute lookup will fall through from the wrapper to the wrapped object, if you have multiple wrappers it will propogate all the way down to the original wrapped object looking for it.

```
class CustomObjectProxy(ObjectProxy):
    __custom_object_proxy_marker__ = True

object = ObjectProxy(CustomObjectProxy(None))

if not hasattr(object, "__custom_object_proxy_marker__"):
    object = CustomObjectProxy(object)
```

Thus your custom object proxy would not be applied a second time, even though it was nested below another.

As noted though, this only works for `wrapt` object proxies. Or at least, it requires any object proxy to propagate attribute look up to the wrapped object.

This will not work for example were there a function wrapper created using a nested function as is typically done with simple decorators, even if the implementation of those decorators uses `functools.wraps()`.

That said, if `functools.wraps()` is used with a conventional function wrapper mixed in with use of an object proxy using `wrapt`, another option does exist.

This is that Python at one point (not sure when), introduced that any function wrapper (eg., decorators), should expose a `__wrapped__` attribute which provides access to the wrapped object.

I can't remember the exact purpose in requiring this, but the `wrapt` object proxy supports it, and `functools.wraps()` also ensures it is provided.

Where the `__wrapped__` attribute exists, what we can therefore do is traverse the chain of wrappers ourselves, looking for the type of our custom wrapper type.

```
found = False

wrapper = object

while wrapper is not None:
    if isinstance(wrapper, CustomObjectProxy):
        found = True
        break

    wrapper = getattr(wrapper, "__wrapped__", None)

if not found:
    object = CustomObjectProxy(object)
```

If you are using the generic `FunctionWrapper` class, rather than need to create a derived version for every different use case, you could use a named function wrapper with attribute that is looked up.

```
class CustomFunctionWrapper(FunctionWrapper):
    def __init__(self, name, wrapped):
        self.__self_name = name
        super().__init__(wrapped)

found = False

wrapper = object

while wrapper is not None:
    if isinstance(wrapper, CustomFunctionWrapper):
        if wrapper.__self_name == "wrapper-type":
            found = True
            break

    wrapper = getattr(wrapper, "__wrapped__", None)

if not found:
    object = CustomFunctionWrapper("wrapper-type", object)
```

End result is that if you want to try and be a resilient as possible, you should always use a custom object proxy type if you need to detect a specific wrapper of your own. This includes needing to create your own derived version of `FunctionWrapper`, with optional name attribute to distinguish different use cases if needed.

This then should be done in combination with traversing any chain of wrappers looking for it, and not assume your wrapper will be top most.

## What's to be learned

The most important thing to learn about what happened in this case is that if packages appear to use the SEMVAR strategy for versioning, then believe that if a major version update occurs, there is a good chance it could have API incompatibilies. Sure it isn't guaranteed that minor versions will not also inadvertantly break things, but a major version sure is a big red flag.

So look at how packages use versioning and consider at least pinning versions to a major version.

Finally, always be very cautious when doing monkey patching and try and design stuff to be as bullet proof as possible, especially if the end target of the monkey patches is with code run by other people, such as the case for APM service instrumentation. Your customers will always appreciate you more when you don't break their applications. 😅
