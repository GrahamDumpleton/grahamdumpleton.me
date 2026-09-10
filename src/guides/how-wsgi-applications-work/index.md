---
title: "How WSGI applications and servers work."
description: "The parts of the WSGI specification people skip over: close() obligations, the write() callable, file_wrapper, streaming responses, and monitoring what an application really does."
tags: ["python", "wsgi"]
draft: false
---

Posts on how WSGI applications and the servers which host them actually behave, as opposed
to what the specification appears to say at first reading, are as follows.

Please note older posts may not reflect what I now regard as best practice,
or may describe software which has since changed or been superseded.

This batch of posts deals with writing the application or middleware itself, and the
obligations that come with the parts of the specification people skip over:

  * [Implementing WSGI application objects.](/posts/2011/01/implementing-wsgi-application-objects/)
  * [Decorating WSGI applications.](/posts/2011/01/decorating-wsgi-applications/)
  * [Obligations for calling close() on the iterable returned by a WSGI application.](/posts/2012/10/obligations-for-calling-close-on/)
  * [WSGI middleware and the hidden write() callable.](/posts/2012/10/wsgi-middleware-and-hidden-write/)
  * [Returning a string as the iterable from a WSGI application.](/posts/2015/05/returning-string-as-iterable-from-wsgi/)
  * [Effects of yielding multiple blocks in a WSGI application response.](/posts/2015/05/effects-of-yielding-multiple-blocks-in/)
  * [WSGI issues with HTTP HEAD requests.](/posts/2009/10/wsgi-issues-with-http-head-requests/)
  * [WSGI and printing to standard output.](/posts/2009/04/wsgi-and-printing-to-standard-output/)

This batch of posts works through wsgi.file_wrapper, the optional server extension for
serving a file efficiently, and what it takes to implement one correctly:

  * [Solving some of the problems with wsgi.file_wrapper.](/posts/2010/12/solving-some-of-problems-with/)
  * [Content length and wsgi.file_wrapper.](/posts/2011/01/content-length-and-wsgifilewrapper/)
  * [Testing a wsgi.file_wrapper implementation.](/posts/2011/01/testing-wsgifilewrapper-implementation/)

This batch of posts is about measuring what a real application is doing, from a wrapper
around the application through to monitoring built into the server itself:

  * [Measuring response time for web requests in a WSGI application.](/posts/2015/05/measuring-response-time-for-web/)
  * [Monitoring the response content from a WSGI application.](/posts/2015/05/monitoring-response-content-from-wsgi/)
  * [Performance monitoring of real WSGI application traffic.](/posts/2015/05/performance-monitoring-of-real-wsgi/)
  * [Implementing request monitoring within the WSGI server.](/posts/2015/06/implementing-request-monitoring-within/)

And on how the servers themselves differ, and why benchmarks of them mislead:

  * [Using benchmarks to understand how WSGI servers work.](/posts/2015/05/using-benchmarks-to-understand-how-wsgi/)
