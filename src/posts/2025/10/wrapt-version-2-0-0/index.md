---
title: "Wrapt version 2.0.0"
description: "Version 2.0.0 of wrapt is finally available."
date: 2025-10-20T10:30:00
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/wrapt"
tags: ["python", "wrapt"]
draft: false
---

After a few delays, I have finally released version 2.0.0 of `wrapt`.

This release has a major version bump for a number of reasons.

The first main reason is simply because there hasn't been any release of `wrapt` with any significant changes for quite a while. All releases for wrapt for sometime have included only minor fixes or updates related to supporting new Python versions.

Next is that although support for Python 2.7 was dropped some time back, the code base still included a lot of code which was Python 2.7 specific. All these accomodations for Python 2.7 have now been removed.

Finally, there have been some subtle internal changes to how a few things were implemented in `wrapt`. It is believed the changes should be backward compatible, but combined with the above and that `wrapt` seems to be seeing significant use now based on PyPi download statistics, I felt it best to be cautious and release this version of `wrapt` as a new major version.

For more information on all the changes you can see the [release notes](https://wrapt.readthedocs.io/en/master/changes.html). The `wrapt` package can be installed from [PyPi](https://pypi.org/project/wrapt/). If you find any issues or have questions, you can use the [issue tracker](https://github.com/GrahamDumpleton/wrapt/issues) on Github.
