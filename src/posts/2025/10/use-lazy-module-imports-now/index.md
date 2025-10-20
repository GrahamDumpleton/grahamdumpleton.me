---
title: "Use lazy module imports now"
description: "How to test out Python lazy module imports right now."
date: 2025-10-20T12:00:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt"]
draft: false
---

I already made a [post](../lazy-imports-using-wrapt/) a couple of weeks ago about how one could use `wrapt` to implement lazy module imports for Python. This was in response to [PEP 810](https://peps.python.org/pep-0810/) (explicit lazy imports) being announced.

The means of using `wrapt` to implement lazy module imports was based around a lazy object proxy which was being added to `wrapt` version 2.0.0. This new version of `wrapt` is now available and to make it easier to use `wrapt` for this purpose, an extra top level function has been added to the `wrapt` public API.

Before I explain how to use this new feature of `wrapt`, I do acknowledge that implementations for lazy module imports have existed for many years. That said, where they exist as separate Python libraries the few I found hadn't seem to have been touched in quite a while. Sure the concept probably works as it was implemented, but it can be disconcerting to see no updates and one could conclude the package has been abandoned. At least in considering using the implementation provided by `wrapt`, you might feel more comfortable that it will be supported. 😁

As to PEP 810, the intent wasn't therefore to bring something completely new, but to make the concept a first class feature of Python by adding new syntax.

The proposed implementation outlined in the PEP would also eliminate one of the criticisms of lazy module importers that already existed. This was that it was necessary to patch `sys.modules` to add in a standin for a module before it was first imported. This was needed to be done explicitly, or it was necessary to add a special import loader to the Python runtime configuration. Either way, it was necessary to modify startup code for an application to install the patch or loader.

A further issue was that the lazy import behaviour would then affect all imports of that module anywhere in the code base since it wasn't an opt in thing for the code that actually used the module, but was forced onto them by the application developer. This could have various unintended side effects.

Were PEP 810 implemented in Python (which is proposed for 3.15), the new syntax would allow code that uses a module to opt in to the lazy module import behaviour. To do this, instead of writing:

```
import json
from json import dumps
```

you would write:

```
lazy import json
lazy from json import dumps
```

In other words, the `lazy` keyword is proposed to mark that the import should be delayed until the first attempt to actually use something defined by the module.

My first impression is that although I understand the aim of it and the benefits it might bring in some situations, I am not sure I am that keen on having a new keyword just for this feature. There are various cases where using it would be pointless. For example, doing a lazy import and immediately creating a new class deriving from one defined by the module. But then I am sure linters could start to pick up on things like this and tell you that using a lazy import wasn't going to help much in such a case.

Anyway, if you do want to experiment with lazy module imports in Python to see what benefits it could bring without needing to compile up a special version of Python, with the new feature in `wrapt` 2.0.0 you can use it now. Further, you can use it with any Python version that `wrapt` supports, which for now is back to Python 3.8.

The way lazy module imports work with `wrapt` also avoids the need to modify startup code for an application like some other implementations, instead the specific code which wants to make use of lazy module imports needs to opt in just like proposed for PEP 810.

Using `wrapt`, instead of using PEP 810 syntax of:

```
lazy import json
```

you would use:

```
import wrapt

json = wrapt.lazy_import("json")
```

The argument to the `lazy_import()` function can also be a dotted path to a sub module of a package, in which case what is returned will evaluate to the sub module.

For importing a specific function from a module, you can use:

```
import wrapt

dumps = wrapt.lazy_import("json", "dumps")
```

How this is different to other lazy module importers is that `sys.modules` is not patched, nor is a custom import loader used. Instead the `json` and `dumps` objects in the above examples are instances of the `LazyObjectProxy` class from `wrapt`, which is implemented using the transparent object proxy class of `wrapt` but with lazy initialization of the wrapped object. Using this lazy initialization feature, we can delay the importing of the module until the proxy object is first used. Although everything then goes through the object proxy, in general you shouldn't notice any difference.

So if you are excited about using lazy module imports but don't want to wait until you can use Python 3.15 (presuming PEP 810 is added), then consider giving this implementation using `wrapt` a go instead. If you do find issues, please let me know via the [issues tracker](https://github.com/GrahamDumpleton/wrapt/issues) for `wrapt` on GitHub.

---

**UPDATE #1**

[Adam Johnson](https://fosstodon.org/@adamchainz/115404333513311427) pointed out that for type checking to work, possibly still need something like:

```
from typing import TYPE_CHECKING

import wrapt

json = wrapt.lazy_import("json")

if TYPE_CHECKING:
    import json
```
