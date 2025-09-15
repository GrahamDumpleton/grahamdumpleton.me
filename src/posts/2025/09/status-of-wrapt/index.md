---
title: "Status of wrapt (September 2025)"
description: "The current status of my Python wrapt package and what to expect next."
date: 2025-09-11
image: "/assets/images/graham-avatar.jpg"
tags: ["python", "wrapt", "pycharm"]
---

The Python [wrapt](https://pypi.org/project/wrapt/) package recently turned 12 years old. Originally intended to be a module for monkey patching Python code, its wrapper object turned out to be a useful basis for creating Python decorators.

Back then, constructing decorators using function closures had various short comings and the resulting wrappers didn't preserve introspection and various other attributes associated with the wrapped function. Many of these issues have been resolved in updates to Python and the `functools.wraps` helper function, but `wrapt` based decorators were still useful for certain use cases such as being able to create a decorator where you could work out whether it was applied to a function, instance method, class method or even a class.

## Downloads of wrapt

It is hard to tell how many people directly use `wrapt`, but helped by it being used internally in some widely used Python packages has actually resulted in `wrapt` making it into the list of [PyPi top 100 packages](https://hugovk.github.io/top-pypi-packages/) by number of downloads. As I write this post it sits at position number 65, but it was at one point as high as about position 45. Either way, I am still surprised it makes it into that list at all, especially since the primary purpose of `wrapt` is to do something most view as dangerous, ie., monkey patch code.

## Maintenance mode

As to the core problem that `wrapt` originally tried to solve, that was achieved many years ago and as such it has more or less been kept in maintenance mode ever since. Most changes over recent years have focused around ensuring it works with each new Python version and expanding on the set of Python wheels that are being released for different architectures. There are occassionaly bug fixes or tweaks but generally they relate to corner cases which have arisen due to people trying to do strange things when monkey patching code.

## Version update

Even though few changes are being made, the plan is to soon release a new version. This version number for this release will jump from 1.17.X to 2.0.X.

The jump in major version isn't due to any known incompatibilities but more just to be safe since in this version all the old legacy code from Python 2 and early Python 3 versions has been removed.

## PyCharm issues

The only obscure change which have any concern over relates to a specific corner case that should never occur in actual use, but does occur when using Python debugger IDEs such as PyCharm which offer live views of Python objects.

The problem in the case of PyCharm is that it can attempt to display the state of a Python object before the `__init__()` method has been called. Due to the wrapper object in `wrapt` being implemented in C code, that there is an accessor for the `__wrapped__` attribute is visible, but until `__init__()` is called it has no value. All the same, PyCharm tries to access `__wrapped__` during that time resulting in an exception.

For this exception when `__wrapped__` is accessed in an uninitialised state a `ValueError` exception was being raised on the basis that the object was in an unknown state. The problem is that PyCharm doesn't gracefully handle this exception in this case and this somehow causes problems for PyCharm users.

What PyCharm prefers in this case is to see an `AttributeError` exception which results in it simply ignoring the attribute. Because it isn't known whether raising `AttributeError` instead of `ValueError` would cause issues for other existing code, I have been reticent to change the type of exception being raised.

At one point someone suggested raising a custom exception which inherits from both `AttributeError` and `ValueError` as a middle ground, allowing PyCharm to work but not cause issues for existing code.

Because one can't use multiple inheritence for custom exceptions implemented in C code, a fiddle has been required whereby the C extension code of `wrapt` reaches back to get a reference to an exception type implemented in Python code. Not elegant but appears to work so going to go with that and see if it works. Remember that this situation where the exception is raised should not even occur normally, so it may only be PyCharm that triggers it. Fingers crossed.

## Typing hints

The other notable change for the next `wrapt` release will be the addition of support for type hints.

Adding type hints has been slow coming because `wrapt` supported Python 2 and older Python 3 versions well past when those versions became obsolete. Since such old versions were still supported, I didn't see it as practical to add support for type hints.

Even now, although the next `wrapt` version will still support Python version 3.8 and 3.9, the support for type hints will only be available if using Python 3.10 or later. This is because I finally realised that when using `.pyi` files to inject type hints, you could have version checks and only add them for selected versions. 🤦‍♂️

Another reason type hint support took so long to be added was simply because I wasn't that familiar with using them. Some users did propose changes to add type hints, but they seemed to me to be very minimal and not try and add support across the full APIs `wrapt` provided. Because I didn't understand type hints enough, I didn't want to risk adding them without really understanding how they worked.

This is not to say I am now an expert on type hints, I am definitely still a newbie and know just enough to be dangerous.

The resulting type hint support I added looks plenty scary to me and unfortunately still doesn't do everything I would like it to. My current belief is that due to the complicated overloading that `wrapt` does in certain APIs, that it just isn't possible within the limits of what the type hinting system can handle to do better than what I have managed. I haven't given up, but I also don't want to delay the next `wrapt` release any further, so will release it as is and revisit it later on to see if it can be made better.

## Release candidates

With that all said, a release candidate for the next version of `wrapt` has been available for about a month. This can be installed by explicitly using `wrapt==2.0.0rc2` or if your package installer supports it, to use unstable package versions such as release candidate versions.

After being out for a month I have not had any reports of the release candidate version causing any issues. That said, no one has said it works fine either. There has been something like 190 thousand downloads of the release candidate in that time though, so that is a good sign at least.

At this point it seems to be safe to release a 2.0.0 final version, so I will be aiming to double check everything over the coming week and get the new version released in time for Python 3.14. That said, Python 3.14 doesn't make it a priority as there was a 1.17.3 patch release version of `wrapt` a month ago which included Python wheels for Python 3.14, so every thing should be good to go for the new Python version.

## List of changes

If you are interested in exactly what changes have made it into the next release, you can check out the `develop` branch for the `wrapt` docs on [ReadTheDocs](https://wrapt.readthedocs.io/en/develop/changes.html).
