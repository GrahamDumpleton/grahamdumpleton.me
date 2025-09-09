---
layout: post
title: "WSGI issues with HTTP HEAD requests."
author: "Graham Dumpleton"
date: "2009-10-09"
url: "http://blog.dscpl.com.au/2009/10/wsgi-issues-with-http-head-requests.html"
post_id: "4040524508658039424"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 4
published_timestamp: "2009-10-09T17:18:00+11:00"
blog_title: "Graham Dumpleton"
---

The HTTP protocol defines the GET and HEAD method types for requests. As outlined in the [RFC-2616](http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html), the HEAD method is specified as:

> The HEAD method is identical to GET except that the server MUST NOT return a message-body in the response. The metainformation contained in the HTTP headers in response to a HEAD request SHOULD be identical to the information sent in response to a GET request. This method can be used for obtaining metainformation about the entity implied by the request without transferring the entity-body itself. This method is often used for testing hypertext links for validity, accessibility, and recent modification.  
>   
> The response to a HEAD request MAY be cacheable in the sense that the information contained in the response MAY be used to update a previously cached entity from that resource. If the new field values indicate that the cached entity differs from the current entity \(as would be indicated by a change in Content-Length, Content-MD5, ETag or Last-Modified\), then the cache MUST treat the cache entry as stale.

Key in this statement is that it says 'the server MUST NOT return a message-body in the response'. Problem is that many web application authors take it upon themselves to treat differently the HEAD request. What they do is make the decision not to return any content for the response, rather than leaving it up to the underlying web server to discard it and not return it to the client.

  


Taking this action in web applications can have unintended affects. The issue here being that the response headers for a GET and HEAD are supposed to be identical.

  


For WSGI where it is possible to write WSGI middleware that wraps other WSGI components or applications, this can result in the WSGI middleware being deprived from seeing the response content. If that WSGI middleware is generating response headers based on the response content, then it can generate results for a HEAD request which then differ to that for a GET request.

  


There has in the past been some [debate](http://www.b-list.org/weblog/2006/may/21/django-gzip-and-wsgi/) about whether a WSGI middleware that allows for compressing of response content is allowed, but various example abound. One such example is in the [Pylons book](http://pylonsbook.com/en/1.0/the-web-server-gateway-interface-wsgi.html). The idea with such a middleware is that rather than just pass back the response content, it will accumulate it and compress it. From the result of that it will then set an amended Content-Length response header providing the new length of the returned content, then yield that modified content.

  


Imagine now where such a WSGI middleware is used to wrap another WSGI component or application which decides to discard response content for a HEAD request. In this case there will be no content to compress and so the WSGI middleware will generate a Content-Length of '0' rather than the same value that would have been returned for a GET request.

  


So, should a WSGI components or application generating content never distinguish between GET and HEAD and always treat a HEAD request as a GET request? Although it is arguable that they should treat them the same, various of the larger Python frameworks do treat them differently and will throw away response content for a HEAD request. I can't see that they are likely to change their code.

  


What to do then? Simple answer is that since we are never going to be able to trust users not to treat GET and HEAD the same, a general guideline is that if your WSGI middleware must always see the response content, even for a HEAD request, then it should change the 'REQUEST\_METHOD' variable in the WSGI environment passed to the enclosed WSGI component or application from 'HEAD' to 'GET'. This is the only way you will know things will work as intended.

  


This problem isn't isolated to just WSGI middleware though. When using Apache, there can be configured output filters that want to do exactly the same sort of thing as the compressing WSGI middleware. For example, there is the 'DEFLATE' output filter provided by the mod\_deflate module and which also handles compression of response content. In this case though the output filter is outside of the realm of the WSGI stack.

  


Apache/mod\_wsgi has recognised this problem for a while though and as a result when it detects that an output filter has been registered with Apache that processes the response content, it will forcibly change 'REQUEST\_METHOD' from 'HEAD' to 'GET' even before it is passed into the WSGI stack. The WSGI application as far as it can tell got a GET request and is none the wiser.

  


Although this detection is part of mod\_wsgi, it isn't going to occur when using a WSGI adapter on top of mod\_python, FASTCGI, SCGI or CGI. As a result, using those other types of hosting systems means that you still risk getting different results for GET and HEAD if a WSGI component or application decides itself to discard the response content.

  


This isn't the end of our troubles with respect to a HEAD request. In the [WSGI specification](http://www.python.org/dev/peps/pep-0333/#handling-the-content-length-header) it says:

> If the application does not supply a Content-Length header, a server or gateway may choose one of several approaches to handling it. The simplest of these is to close the client connection when the response is completed.  
>   
> Under some circumstances, however, the server or gateway may be able to either generate a Content-Length header, or at least avoid the need to close the client connection. If the application does not call the write\(\) callable, and returns an iterable whose len\(\) is 1, then the server can automatically determine Content-Length by taking the length of the first string yielded by the iterable.

This all sounds good and looks like a good optimisation. Problem is that it itself can cause different results to be returned for the HEAD request than the GET request and thus is arguably wrong and should partly be stricken from the WSGI specification.

  


To understand the issue, imagine a WSGI application which returns an iterable of length 1 and which for a GET request yielded a string of length '666'. If no 'Content-Length' response header is set, then the guideline above says that the WSGI adapter can create the 'Content-Length' header itself, which it would with the value '666'.

  


Now for a HEAD request, if that same WSGI application decided not to return any response content, that is the yielded string was empty, but still didn't set 'Content-Length', then the WSGI adapter would blindly set 'Content-Length' to '0'. So, the result will be different to that for the GET request.

  


One might think that one could just not generate a 'Content-Length' for a HEAD request, but having a 'Content-Length' for GET and not for HEAD is still leaving the two responses different in some way.

  


To me then, it seems that no WSGI adapter should perform automatic generation of 'Content-Length' response header. Alternatively, and to avoid the whole problem, WSGI adapters should always say it is a GET request, rather than passing on the HEAD request.

  


I don't know how other WSGI like systems such as RACK, JACK and PSGI, or even other web systems, deal with this issue, but definitely think that WSGI has got something wrong here.

  


Anyone else got any comments on this? Should I be going and modifying mod\_wsgi to remove that feature whereby it adds 'Content-Length' where it can? Is the WSGI specification wrong in saying that?

---

## Comments

### Armin Ronacher - October 9, 2009 at 7:00 PM

I consider the automatic content length setting a mistake. Everytime a WSGI server does something the chances are, it's wrong.  
  
wsgiref for example fucks up the date header horribily because it \*adds\* it, even if it's already there causing a lot of troubles for proxies.  
  
Incidentally I changed Werkzeug yesterday to automatically add a content length whenever safely possible. However I can already see how this is causing troubles because a middlewares that modify the payload nearly never update the content length.  
  
How do other systems handle that? Undefined behavior basically.

### Graham Dumpleton - October 9, 2009 at 7:41 PM

One other stupid thing about WSGI specification that I forgot to mention is that it says """returns an iterable whose len\(\) is 1, then the server can automatically determine Content-Length by taking the length of the first string yielded by the iterable""". What about where length of iterable is length 0? That is left undefined. The HEAD issue still comes up with that though even if a WSGI adapter was setting Content-Length where iterable didn't yield any strings.

### fumanchu - October 10, 2009 at 5:21 AM

I still say that if a WSGI origin server receives a response that has no Content-Length header, it should send the response encoded with the "chunked" transfer-coding; in that case the Content-Length response header is omitted. You can't have a conflict between different values of a header that isn't present in either the HEAD or GET case.

### Graham Dumpleton - October 10, 2009 at 9:44 PM

Robert, in Apache/mod\_wsgi, the mod\_wsgi layer doesn't control whether chunked transfer encoding is used for response or not, that is a decision made by lower level Apache web server.  
  
Either way, will be changing mod\_wsgi so that Content-Length is never added automatically and so where Apache can use chunked, it will.  
  
Anyway, just highlights another place where WSGI specification just doesn't get it quite right. :-\)

