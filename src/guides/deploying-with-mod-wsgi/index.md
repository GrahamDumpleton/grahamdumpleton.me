---
title: "Deploying Python web applications with mod_wsgi."
description: "Getting mod_wsgi installed and pointed at the right Python, mod_wsgi-express, choosing between embedded and daemon mode, debugging under Apache, and free threading in 6.0.0."
tags: ["python", "mod_wsgi", "apache", "wsgi"]
draft: false
---

Posts on deploying Python web applications with
[mod_wsgi](https://github.com/GrahamDumpleton/mod_wsgi) are as follows. The list leaves out
the release announcements, of which there have been many over the years.

Please note older posts may not reflect what I now regard as best practice,
or may describe software which has since changed or been superseded.

This batch of posts covers getting mod_wsgi installed and pointed at the right Python
installation, which is where most problems begin:

  * [What is the current version of mod_wsgi?](/posts/2014/09/what-is-current-version-of-modwsgi/)
  * [Installing mod_wsgi on MacOS X with native operating system tools.](/posts/2016/07/installing-modwsgi-on-macos-x-with/)
  * [Using Python virtual environments with mod_wsgi.](/posts/2014/09/using-python-virtual-environments-with/)
  * [Python module search path and mod_wsgi.](/posts/2014/09/python-module-search-path-and-modwsgi/)
  * [Setting LANG and LC_ALL when using mod_wsgi.](/posts/2014/09/setting-lang-and-lcall-when-using/)

This batch of posts is about mod_wsgi-express, which packages a working Apache and
mod_wsgi configuration so that no Apache configuration has to be written at all:

  * [Introducing mod_wsgi-express.](/posts/2015/04/introducing-modwsgi-express/)
  * [Using mod_wsgi-express with Django.](/posts/2015/04/using-modwsgi-express-with-django/)
  * [Using mod_wsgi-express as a development server.](/posts/2015/05/using-modwsgi-express-as-development/)
  * [Integrating mod_wsgi-express as a Django admin command.](/posts/2015/04/integrating-modwsgi-express-as-django/)
  * [Packaging mod_wsgi into a zipapp using shiv.](/posts/2018/10/packaging-modwsgi-into-zipapp-using-shiv/)

This batch of posts deals with processes and threads, and why the mode an application runs
under matters more than any other setting:

  * [Why are you using embedded mode of mod_wsgi?](/posts/2012/10/why-are-you-using-embedded-mode-of/)
  * [Use of threading in mod_wsgi daemon mode.](/posts/2014/02/use-of-threading-in-modwsgi-daemon-mode/)
  * [Vertically partitioning Python web applications.](/posts/2014/02/vertically-partitioning-python-web/)

This batch of posts covers what to do when an application misbehaves under Apache:

  * [Debugging with pdb when using mod_wsgi.](/posts/2014/09/debugging-with-pdb-when-using-modwsgi/)
  * [Requests running in wrong Django instance under Apache/mod_wsgi.](/posts/2012/10/requests-running-in-wrong-django/)
  * [An improved WSGI script for use with Django.](/posts/2010/03/improved-wsgi-script-for-use-with/)

This batch of posts covers mod_wsgi 6.0.0, which added support for the free threaded build
of Python and for a separate GIL per interpreter:

  * [Free-threading in mod_wsgi 6.0.0.](/posts/2026/05/free-threading-in-mod-wsgi-6-0-0/)
  * [Per-interpreter GIL in mod_wsgi 6.0.0.](/posts/2026/05/per-interpreter-gil-in-mod-wsgi-6-0-0/)
  * [Free-threading vs the GIL in mod_wsgi 6.0.0.](/posts/2026/05/free-threading-vs-the-gil-in-mod-wsgi-6-0-0/)
  * [WSGISwitchInterval in mod_wsgi 6.0.0.](/posts/2026/05/wsgi-switch-interval-in-mod-wsgi-6-0-0/)

How the applications being hosted are meant to behave is covered separately under
[how WSGI applications and servers work](/guides/how-wsgi-applications-work/).
