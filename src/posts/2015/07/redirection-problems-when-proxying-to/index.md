---
layout: post
title: "Redirection problems when proxying to Apache running in Docker."
author: "Graham Dumpleton"
date: "2015-07-01"
url: "http://blog.dscpl.com.au/2015/07/redirection-problems-when-proxying-to.html"
post_id: "5446026146760798090"
blog_id: "2363643920942057324"
tags: ['apache', 'docker', 'mod_wsgi', 'python', 'wsgi']
comments: 0
published_timestamp: "2015-07-01T14:04:00+10:00"
blog_title: "Graham Dumpleton"
---

In my [prior post](/posts/2015/06/proxying-to-python-web-application/) I described various issues which can arise when moving a Python web application hosted using Apache/mod\_wsgi into a Docker container and then using the existing Apache instance to proxy requests through to the Docker instance.

The issues arose due to the instance of the backend Python web application running under Docker, not knowing what the true URL was that was being used to access the site. The backend would only know about the URL used to identify the Docker host and the port on which the Python web application was being exposed. It did not know what the original URL was that the HTTP client used, nor specifically whether a HTTP or HTTPS connection was being used by the client.

To remedy this situation, the original Apache instance which was proxying the requests through to the backend, was configured to pass through extra request headers giving details about the remote client, public host name of the site, port accessed and the protocol scheme. An ability of mod\_wsgi to interpret these headers and fix up the WSGI environ dictionary passed with each request with correct values was then enabled. The end result was that the WSGI application was able to correctly determine what URL the site was originally accessed as and so generate correct URLs for the same site in HTML responses and redirection headers such as ‘Location’.

Because though a feature of mod\_wsgi was being used here to fix up the information passed into the WSGI application, it wouldn’t be applied if the same backend Apache instance was also being used to host static files. As only static files are being served up one might expect that this wouldn’t be an issue, but there is one situation where it is.

In this blog post I will describe how when using mod\_wsgi-express inside of a Docker container you can host static files at the same time as your WSGI application. I will then illustrate the specific problem still left unresolved by the prior method used to fix up requests bound for the WSGI application. Finally I will look at various solutions to the problem.

# Hosting static files

Our final Dockerfile from the prior post was:

```
 FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
 CMD [ "--trust-proxy-header", "X-Forwarded-Host", \  
       "--trust-proxy-header", "X-Forwarded-Port", \  
       "--trust-proxy-header", "X-Forwarded-For", \  
       "--trust-proxy-header", "X-Forwarded-Scheme", \  
       "site.wsgi" ]
```

The configuration for the front end Apache which proxied requests through to our WSGI application running in the Docker container was:

```
 # blog.example.com

 <VirtualHost *:80>  
 ServerName blog.example.com

 ProxyPass / http://docker.example.com:8002/  
   
 RequestHeader set X-Forwarded-Port 80  
 </VirtualHost>
```

The Docker image was being run as:

```
 docker run --rm -p 8002:80 blog.example.com
```

This was all making use of mod\_wsgi-express shipped as part of the ‘mod\_wsgi-docker’ image from Docker Hub.

  * <https://registry.hub.docker.com/u/grahamdumpleton/mod-wsgi-docker/>



The arguments to ‘CMD’ were the extra options we had been passing to mod\_wsgi-express.

In addition to being able to host a Python WSGI application with no need for a user to configure Apache themselves, mod\_wsgi-express can still be used to also host static files using Apache.

The simplest way of doing this would be to create a ‘htdocs’ directory within your project and populate it with any static files you have. You then tell mod\_wsgi-express to use that directory as the root directory for any static document files.

```
 FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
 CMD [ "--trust-proxy-header", "X-Forwarded-Host", \  
       "--trust-proxy-header", "X-Forwarded-Port", \  
       "--trust-proxy-header", "X-Forwarded-For", \  
       "--trust-proxy-header", "X-Forwarded-Scheme", \  
       "--document-root", "htdocs", "site.wsgi" ]
```

Normally when manually setting up mod\_wsgi, the WSGI application if mounted at the root of the web site would hide any static files which may reside in the Apache ‘DocumentRoot’ directory, however mod\_wsgi-express uses a method which allows any static files to be overlaid on top of the WSGI application.

That is, if a static file is matched by a URL, then the static file will be served up, otherwise if no static file is found, the request will be passed through to the WSGI application instead.

The benefit of this approach is that you do not need to fiddle with mounting selected directories at a sub URL to the site, or even individual files if wishing to return files such as ‘robots.txt’ or ‘favicon.ico’. You just dump the static files in the ‘htdocs’ directory with a path corresponding to the URL path they should be accessed as.

# The redirection problem

Imagine now that the ‘htdocs’ directory contained:

```
 htdocs/robots.txt  
 htdocs/static/  
 htdocs/static/files.txt
```

That is, in the top level directory is contained a ‘robots.txt’ file as well as a sub directory. In the sub directory we then had a further file called ‘files.txt’.

If we now access either of the actual files using the URLs:

```
 http://blog.example.com/robots.txt  
 http://blog.example.com/static/files.txt
```

then all works as expected and the contents of those files will be returned.

So long as the URLs always target the actual files in this way then all is good.

Where a problem arises though is were the URL corresponding to the ’static’ subdirectory is accessed, and specifically where no trailing slash was added to the URL.

```
 http://blog.example.com/static
```

Presuming that the URL is accessed from the public Internet where the Docker host is not going to be accessible, then the request from the browser will fail, indicating that the location is not accessible.

The reason for this is that when a URL is accessed which maps to a directory on the file system, and no trailing slash was added, then Apache will force a redirection back to the same directory, but using a URL with a trailing slash.

Looking at this using ‘curl’ we would see response headers coming back of:

```
 $ curl -v http://blog.example.com/static  
 * Hostname was NOT found in DNS cache  
 * Trying 1.2.3.4...  
 * Connected to blog.example.com (1.2.3.4) port 80 (#0)  
 > GET /static HTTP/1.1  
 > User-Agent: curl/7.37.1  
 > Host: blog.example.com  
 > Accept: */*  
 >  
 < HTTP/1.1 301 Moved Permanently  
 < Date: Wed, 01 Jul 2015 01:37:46 GMT  
 * Server Apache is not blacklisted  
 < Server: Apache  
 < Location: http://docker.example.com:8002/static/  
 < Content-Length: 246  
 < Content-Type: text/html; charset=iso-8859-1
```

Apache has therefore responded with a HTTP status code of 301, indicating via the ‘Location’ response header that the resource being requested is actually located at 'http://docker.example.com:8002/static/'.

When the web browser now accesses the URL given in the ‘Location’ response header, it will fail, as ‘docker.example.com’ is an internal site and not accessible on the public Internet.

# Fixing response headers

When using Apache to host just the WSGI application we didn’t have this issue as we relied on mod\_wsgi to fix the details related to host/port/scheme as it was being passed into the WSGI application. Thus any redirection URL that may have been generated by the WSGI application would have been correct to start with.

For response headers in this case where what mod\_wsgi was doing doesn’t apply, we can use another technique to fix up the URL. This is done by fixing the response headers in the front end proxy as the response passes back through it. This is done using the ‘ProxyPassReverse’ directive.

```
 # blog.example.com

 <VirtualHost *:80>  
 ServerName blog.example.com

 ProxyPass / http://docker.example.com:8002/  
 ProxyPassReverse / http://docker.example.com:8002/  
   
 RequestHeader set X-Forwarded-Port 80  
 </VirtualHost>
```

When the ‘ProxyPassReverse’ directive is specified, the front end will adjust any URL in the ‘Location', 'Content-Location' and ‘URI' headers of HTTP redirect responses. It will replace the URL given to the directive with what the URL for the front facing Apache instance was.

With this in place we now get the URL we would expect to see in the ‘Location’ response header.

```
 $ curl -v http://blog.example.com/static  
 * Hostname was NOT found in DNS cache  
 * Trying 1.2.3.4...  
 * Connected to blog.example.com (1.2.3.4) port 80 (#0)  
 > GET /static HTTP/1.1  
 > User-Agent: curl/7.37.1  
 > Host: blog.example.com  
 > Accept: */*  
 >  
 < HTTP/1.1 301 Moved Permanently  
 < Date: Wed, 01 Jul 2015 02:10:51 GMT  
 * Server Apache is not blacklisted  
 < Server: Apache  
 < Location: http://blog.example.com/static/  
 < Content-Length: 246  
 < Content-Type: text/html; charset=iso-8859-1  
 <  
 <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">  
 <html><head>  
 <title>301 Moved Permanently</title>  
 </head><body>  
 <h1>Moved Permanently</h1>  
 <p>The document has moved <a href="http://docker.example.com:8002/static/">here</a>.</p>  
 </body></html>  
 * Connection #0 to host blog.example.com left intact
```

We aren’t done though as this time the actual body of the response is also being shown. Although the ‘Location’ header is now correct, the URL as it appears in the response content is still wrong.

# Fixing response content

Fixing up any incidences of the incorrect URL in the response content is a bit more complicated. If using Apache 2.4 for the front end though, one can however use the ‘mod\_proxy\_html’ module. For our example here, after having enabled ‘mod\_proxy\_html’, we can modify the proxy setup to be:

```
 # blog.example.com

 <VirtualHost *:80>  
 ServerName blog.example.com

 ProxyPass / http://docker.example.com:8002/  
 ProxyPassReverse / http://docker.example.com:8002/  
   
 ProxyHTMLEnable On  
 ProxyHTMLURLMap http://docker.example.com:8002 http://blog.example.com   
   
 RequestHeader set X-Forwarded-Port 80  
 </VirtualHost>
```

What this will do is cause any response from the backend of type 'text/html' or 'application/xhtml+xml’ to be processed as it is returned back via the proxy, with any text matching 'http://docker.example.com:8002' being replaced with 'http://blog.example.com'. The result then from our redirection would be:

```
 $ curl -v http://blog.example.com/static  
 * Hostname was NOT found in DNS cache  
 * Trying 1.2.3.4...  
 * Connected to blog.example.com (1.2.3.4) port 80 (#0)  
 > GET /static HTTP/1.1  
 > User-Agent: curl/7.37.1  
 > Host: blog.example.com  
 > Accept: */*  
 >  
 < HTTP/1.1 301 Moved Permanently  
 < Date: Wed, 01 Jul 2015 02:56:47 GMT  
 * Server Apache is not blacklisted  
 < Server: Apache  
 < Location: http://blog.example.com/static/  
 < Content-Type: text/html;charset=utf-8  
 < Content-Length: 185  
 <  
 <html><head><title>301 Moved Permanently</title></head><body>  
 <h1>Moved Permanently</h1>  
 <p>The document has moved <a href="http://blog.example.com/static/">here</a>.</p>  
 * Connection #0 to host blog.example.com left intact
```

As it turns out, with the configuration being used in the backend, in following the now correct URL we will get a response of:

```
 $ curl -v http://blog.example.com/static/  
 * Hostname was NOT found in DNS cache  
 * Trying 1.2.3.4...  
 * Connected to blog.example.com (1.2.3.4) port 80 (#0)  
 > GET /static/ HTTP/1.1  
 > User-Agent: curl/7.37.1  
 > Host: blog.example.com  
 > Accept: */*  
 >  
 < HTTP/1.1 404 Not Found  
 < Date: Wed, 01 Jul 2015 02:57:55 GMT  
 * Server Apache is not blacklisted  
 < Server: Apache  
 < Content-Type: text/html;charset=utf-8  
 < Content-Length: 151  
 <  
 <html><head><title>404 Not Found</title></head><body>  
 <h1>Not Found</h1>  
 <p>The requested URL /static/ was not found on this server.</p>  
 * Connection #0 to host blog.example.com left intact
```

So in some respects the example may have been a bit pointless as it subsequently led to a HTTP 404 response, but it did illustrate the redirection problem that exists for static files and how to deal with it.

When using mod\_wsgi-express it is possible to enable directory listings:

```
 FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
 CMD [ "--trust-proxy-header", "X-Forwarded-Host", \  
       "--trust-proxy-header", "X-Forwarded-Port", \  
       "--trust-proxy-header", "X-Forwarded-For", \  
       "--trust-proxy-header", "X-Forwarded-Scheme", \  
       "--document-root", "htdocs", \  
       "—directory-listing”, \  
       "site.wsgi" ]
```

or even directory index files:

```
 FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
 CMD [ "--trust-proxy-header", "X-Forwarded-Host", \  
       "--trust-proxy-header", "X-Forwarded-Port", \  
       "--trust-proxy-header", "X-Forwarded-For", \  
       "--trust-proxy-header", "X-Forwarded-Scheme", \  
       "--document-root", "htdocs", \  
       "—directory-index", "index.html”, \  
       "site.wsgi" ]
```

so the redirection need not have ended up as a HTTP 404 response.

Either way, the problem with using ‘mod\_proxy\_html’ in such a situation is that all HTML responses will be processed. In this case the only HTML response which was an issue was the redirection response created by Apache itself. The additional processing overheads of ‘mod\_proxy\_html’ may not therefore be warranted.

# Error response content

Due to the potential of ‘mod\_proxy\_html’ causing undue overhead if applied to all HTML responses, a simpler way to address the problem may be to change the content of the error responses generated by Apache.

For such redirection responses, it is unlikely these days to encounter a situation where the actual page content would be displayed up on a browser and where a user would need to manually follow the redirection link. Instead the ‘Location’ response header would usually be picked up automatically and the browser would go to the redirection URL immediately.

As the URL in the response content is unlikely to be used, one could therefore change the response simply not to include it. This can be done with Apache by overriding the error document content in the back end.

```
 FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild  
 CMD [ "--trust-proxy-header", "X-Forwarded-Host", \  
       "--trust-proxy-header", "X-Forwarded-Port", \  
       "--trust-proxy-header", "X-Forwarded-For", \  
       "--trust-proxy-header", "X-Forwarded-Scheme", \  
       "--document-root", "htdocs", \  
       "--error-document", "301", "/301.html", \  
       "site.wsgi" ]
```

The actual content you do want to respond with would then be placed as a static file in the ‘htdocs’ directory called ‘301.html’.

```
 <html><head>  
 <title>301 Moved Permanently</title>  
 </head><body>  
 <h1>Moved Permanently</h1>  
 <p>The document has moved.</p>  
 </body></html>
```

Trying ‘curl’ once again, we now get:

```
 $ curl -v http://blog.example.com/static  
 * Hostname was NOT found in DNS cache  
 * Trying 1.2.3.4...  
 * Connected to blog.example.com (1.2.3.4) port 80 (#0)  
 > GET /static HTTP/1.1  
 > User-Agent: curl/7.37.1  
 > Host: blog.example.com  
 > Accept: */*  
 >  
 < HTTP/1.1 301 Moved Permanently  
 < Date: Wed, 01 Jul 2015 03:31:48 GMT  
 * Server Apache is not blacklisted  
 < Server: Apache  
 < Location: http://blog.example.com/static/  
 < Last-Modified: Wed, 01 Jul 2015 03:27:24 GMT  
 < ETag: "89-519c7e6bebf00"  
 < Accept-Ranges: bytes  
 < Content-Length: 137  
 < Content-Type: text/html  
 <  
 <html><head>  
 <title>301 Moved Permanently</title>  
 </head><body>  
 <h1>Moved Permanently</h1>  
 <p>The document has moved.</p>  
 </body></html>  
 * Connection #0 to host blog.example.com left intact
```

For this particular case of also using mod\_wsgi-express to serve up static files, this is the only situation like this that I know of. If however you were using other Apache modules on the backend which were resulting in other inbuilt Apache error responses being generated, then you may want to review those and also override the error documents for them if necessary.

# Other options available

In the original problem described when proxying to a WSGI application, and with this subsequent issue with static file hosting, I have endeavoured to only use features to resolve the problem available in mod\_wsgi or Apache 2.4. These aren’t necessarily the only options available for dealing with these issues though.

Another solution that exists is the third party Apache module called [mod\_rpaf](https://github.com/gnif/mod_rpaf). This module supports doing something similar to what mod\_wsgi was doing for WSGI applications, but such that it can be applied to everything handled by the Apache server. Thus it should be able to cover the issues with both a WSGI application and serving of static files.

I am not going to cover ‘mod\_rpaf’ here, but may do so in a future post.

One issue with using ‘mod\_rpaf’, and which I would cover in any future post, is that it isn’t a module which is bundled with Apache. As a result one needs to build it from source code and incorporate it into the Apache installation within Docker to be able to use it.

I am also a bit concerned about what mechanisms it may have for where multiple headers can be used to indicate the same information. In the mod\_wsgi module there are specific safe guards for that and although ‘mod\_rpaf’ does have the ability to denote the IPs of trusted proxies, I don’t believe it provides a way of saying which header is specifically trusted when multiple options exist to pass information. It will need to be something I research further before posting about it.