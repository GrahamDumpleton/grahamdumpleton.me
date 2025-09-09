---
title: "Returning a string as the iterable from a WSGI application."
author: "Graham Dumpleton"
date: "Tuesday, May 19, 2015"
url: "http://blog.dscpl.com.au/2015/05/returning-string-as-iterable-from-wsgi.html"
post_id: "344938495038536076"
blog_id: "2363643920942057324"
tags: ['gunicorn', 'mod_wsgi', 'python', 'uWSGI', 'wsgi']
comments: 0
published_timestamp: "2015-05-19T21:03:00+10:00"
blog_title: "Graham Dumpleton"
---

The possible performance consequences of returning many separate data blocks from a WSGI application were covered in the [previous post](http://blog.dscpl.com.au/2015/05/effects-of-yielding-multiple-blocks-in.html). In that post the WSGI application used as an example was one which returned the contents of a file as many small blocks of data. Part of the performance problems seen arose due to how the WSGI servers would flush each individual block of data out, writing it onto the socket connection back to the HTTP client. Flushing the data in this way for many small blocks, as opposed to as few as possible larger blocks had a notable overhead, especially when writing back to an INET socket connection.

In this post I want to investigate an even more severe case of this problem that can occur. For that we need to go back and start over with the more typical way that most Python web frameworks return response data. That is, as a single large string.

> 
>     def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = 1024*1024*b'X'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         return [output]

In this example I have increased the length of the string to be returned so it is 1MB in size.

If we run this under mod\_wsgi-express and use 'curl' then we get an adequately quick response as we would expect.

> 
>     $ time curl -s -o /dev/null http://localhost:8000/
>     
>     
>     real 0m0.017s  
>     > user 0m0.006s  
>     > sys 0m0.005s

# Response as an iterable

As is known, the response from a WSGI application needs to be an iterable of byte strings. The more typical scenarios are that a WSGI application would return either a list of byte strings, or it would be implemented as a generator function which would yield one or more byte strings.

That the WSGI server will accept any iterable does mean that people new to writing Python WSGI applications often make a simple mistake. That is that instead of returning a list of byte strings, they simply return the byte string instead.

> 
>     def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = 1024*1024*b'X'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         return output

Because a byte string is also an iterable then the code will still appear to run fine, returning the response expected back to the HTTP client. For a small byte string the time taken to display the page back in the browser would appear to be normal, but for a larger byte string it would become evident that something is wrong.

Running this test with mod\_wsgi-express again, we can see the time taken balloon out from 17 milliseconds to over 3 seconds:

> 
>     $ time curl -s -o /dev/null http://localhost:8000/
>     
>     
>     real 0m3.659s  
>     > user 0m0.294s  
>     > sys 0m1.544s

Use gunicorn, and as we saw in the previous post the results are much worse again.

> 
>     $ time curl -s -o /dev/null http://localhost:8000/
>     
>     
>     real 0m23.762s  
>     > user 0m1.446s  
>     > sys 0m7.085s

The reason the results are so bad is that when a string is returned as the iterable, when iterating over it you are dealing with the byte string one byte at a time. This means that when the WSGI server is writing the response back to the HTTP client, it is in turn doing it one byte at a time. The overhead of writing one byte at a time to the socket connection is dwarfing everything else.

As was covered in the prior post, this is entirely expected behaviour for a WSGI server. The mistake here is entirely in the example code and the code should be corrected.

Acknowledging that this would be a problem with a users code, lets now though see what happens when this example is run through uWSGI.

> 
>     $ time curl -s -o /dev/null http://localhost:8000/
>     
>     
>     real 0m0.019s  
>     > user 0m0.006s  
>     > sys 0m0.007s

Rather than the larger time we would expect to see, when using uWSGI the time taken is still down at 19 milliseconds.

This may seem to be a good result, but what is happening here is that uWSGI has decided to break with conforming to the WSGI specification and has added special checking to detect this sort of user mistake. Instead of treating the result as an iterable as it is required to by the WSGI specification, it takes the whole string and uses it as is.

You may still be thinking this is great, but it isn't really and will only serve to hide the original mistake, resulting in users writing and shipping code with a latent bug. The problem will only become evident when the WSGI application is run on a different WSGI server which does conform to the WSGI specification.

This could be disastrous if the WSGI application was being shipped out to numerous customers where it was the customer who decided what WSGI server they used.

In addition to there being a problem when run on a conforming WSGI server, there will also be a problem if someone took the WSGI application and wrapped it with a WSGI middleware.

This can be illustrated by now going back and adding the WSGI application timing decorator.

> 
>     from timer1 import timed_wsgi_application1
>     
>     
>     @timed_wsgi_application1  
>     > def application(environ, start_response):
>     
>     
>         status = '200 OK'  
>     >     output = 1024*1024*b'X'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         return output

With the decorator, running with uWSGI again we now get:

> 
>     $ time curl -s -o /dev/null http://localhost:8000/
>     
>     
>     real 0m13.876s  
>     > user 0m0.925s  
>     > sys 0m3.407s

So only now do we get the sort of result we were expecting, with it taking 13 seconds.

The reason that the problem only now shows up with uWSGI is because the wrapper which gets added by the WSGI middleware, around the iterable passed back from the WSGI application, causes the uWSGI check for an explicit string value to fail.

This demonstrates how fragile the WSGI application now is. If it is intended to be something that is used by others, you cannot control whether those users may use any WSGI middleware around it. A user might therefore very easily and unknowingly, cause problems for themselves and have no idea why or even that there is a problem.

# Application portability

As much as the WSGI specification is derided by many, it can't be denied it eliminated the problem that existed at the time with there being many different incompatible ways to host Python web applications. Adherence to the WSGI specification by both WSGI applications and servers is key to that success. It is therefore very disappointing to see where WSGI servers deviate from the WSGI specification as it is a step away from the goal of application portability.

What you instead end up with is pseudo WSGI applications which are in fact locked in to a specific WSGI server implementation and will not run correctly or perform well on other WSGI servers.

If you are developing Python web applications at the WSGI level rather than using a web framework and you value WSGI application portability, one thing you can do to try and ensure WSGI compliance is to use the WSGI validator found in the 'wsgiref.validate' module of the Python standard library.

> 
>     def application(environ, start_response):  
>     >     status = '200 OK'  
>     >     output = 1024*1024*b'X'
>     
>     
>         response_headers = [('Content-type', 'text/plain'),  
>     >             ('Content-Length', str(len(output)))]  
>     >     start_response(status, response_headers)
>     
>     
>         return output  
>     >   
>     > import wsgiref.validate  
>     >   
>     > application = wsgiref.validate.validator(application)

This will perform a range of checks to ensure some basic measure of WSGI compliance and also good practice.

In this particular example of where a string was returned as the WSGI application iterable, the WSGI validator will flag it as a problem, with the error:

> 
>     AssertionError: You should not return a string as your application iterator, instead return a single-item list containing that string.

So run the validator on your application during development or testing at times and exercise your WSGI application to get good coverage. This will at least help with some of the main issues that may come up, although by no means all given how many odd corner cases that exist within the WSGI specification.