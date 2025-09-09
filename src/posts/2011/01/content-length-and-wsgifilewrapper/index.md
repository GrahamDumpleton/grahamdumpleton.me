---
layout: post
title: "Content length and wsgi.file_wrapper."
author: "Graham Dumpleton"
date: "2011-01-05"
url: "http://blog.dscpl.com.au/2011/01/content-length-and-wsgifilewrapper.html"
post_id: "8802232990230740588"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 1
published_timestamp: "2011-01-05T21:54:00+11:00"
blog_title: "Graham Dumpleton"
---

Following on from the previous post about the close\(\) method and wsgi.file\_wrapper, I am now going to deal with issues around the ‘Content-Length’ header in responses when dealing with wsgi.file\_wrapper.  
  
When returning a response from a WSGI application, the ‘Content-Length’ header can be specified to indicate how much data is being returned in the body of the response. To be in compliance with HTTP specifications, you should only return that amount of data. In PEP 333, the original specification for WSGI, this wasn’t clearly spelt out and there were other statements which could be seen as creating situations which conflicted with that requirement.  
  
Specifically, in PEP 333 the way in which an instance of wsgi.file\_wrapper was dealt with was explained as:  
  
"""Apart from the handling of close\(\), the semantics of returning a file wrapper from the application should be the same as if the application had returned iter\(filelike.read, ''\). In other words, transmission should begin at the current position within the "file" at the time that transmission begins, and continue until the end is reached."""  
  
The problem here is if a WSGI application returns an instance of wsgi.file\_wrapper, but sets a ‘Content-Length’ response header with a value which is less than the actual length of the filelike object used, then because the WSGI specification was indicating that all content from the filelike object should be returned, then one could actually end up with more data being returned than that specified by the ‘Content-Length’ header.
    
    
    def application(environ, start_response):  
        status = '200 OK'  
      
        filelike = file('/usr/share/dict/words', 'r')  
      
        blksize = 8192  
        filesize = 1024  
      
        response_headers = [('Content-Type', 'text/plain'),  
                            (‘Content-Length’, str(filesize)),]  
        start_response(status, response_headers)  
      
        file_wrapper = environ.get('wsgi.file_wrapper', None)  
      
        if file_wrapper:  
            return file_wrapper(filelike, blksize)  
        else:  
            return iter(lambda: filelike.read(blksize), '')

This issue in the WSGI specification was remedied in the PEP 3333 update to PEP 333 where it clearly spells out that in general:  
  
"""If the application supplies a Content-Length header, the server should not transmit more bytes to the client than the header allows, and should stop iterating over the response when enough data has been sent, or raise an error if the application tries to write\(\) past that point. \(Of course, if the application does not provide enough data to meet its stated Content-Length, the server should close the connection and log or otherwise report the error.\)"""  
  
Further, in relation to wsgi.file\_wrapper it now instead says:  
  
"""Apart from the handling of close\(\), the semantics of returning a file wrapper from the application should be the same as if the application had returned iter\(filelike.read, ''\). In other words, transmission should begin at the current position within the "file" at the time that transmission begins, and continue until the end is reached, or until Content-Length bytes have been written. \(If the application doesn't supply a Content-Length, the server may generate one from the file using its knowledge of the underlying file implementation.\)"""  
  
So, the WSGI server or gateway is now clearly required to protect against more data than is specified by the ‘Content-Length’ response header being written back to the HTTP client.  
  
This though doesn’t indicate that any WSGI middleware is effectively bound by the same requirement. Unfortunately you generally never see WSGI middleware check what ‘Content-Length’ may already be set to and restrict how much data they consume from a WSGI component it is wrapping. This results in incorrect output for some types of WSGI middleware.  
  
Take the GzipResponse middleware from Paste as an example. This WSGI middleware performs compression on any response data. The middleware provides its own start\_response\(\) stand in which does the following:
    
    
    def gzip_start_response(self, status, headers, exc_info=None):  
        self.headers = headers  
        ct = header_value(headers,'content-type')  
        ce = header_value(headers,'content-encoding')  
        self.compressible = False  
        if ct and (ct.startswith('text/') or \  
            ct.startswith('application/')) and 'zip' not in ct:  
            self.compressible = True  
        if ce:  
            self.compressible = False  
        if self.compressible:  
            headers.append(('content-encoding', 'gzip'))  
        remove_header(headers, 'content-length')  
        self.headers = headers  
        self.status = status  
        return self.buffer.write

The code in this case removes the ‘Content-Length’ header from the response headers but you will note that it doesn’t actually pay attention to what the original value of the ‘Content-Length’ header was and limit itself to only consuming that much data from the enclosed WSGI application component.
    
    
    def finish_response(self, app_iter):  
        if self.compressible:  
            output = gzip.GzipFile(mode='wb',  
                compresslevel=self.compress_level,  
                fileobj=self.buffer)  
        else:  
            output = self.buffer  
        try:  
            for s in app_iter:  
                output.write(s)  
            if self.compressible:  
                output.close()  
        finally:  
            if hasattr(app_iter, 'close'):  
                app_iter.close()  
        content_length = self.buffer.tell()  
        CONTENT_LENGTH.update(self.headers, content_length)  
        self.start_response(self.status, self.headers)

This means that for our original example where a ‘Content-Length’ of 1024 had been specified, but where the actual file could have been much much bigger, that the GzipResponse middleware will consume the complete file instead and not limit it to 1024 bytes. In the end, this middleware could end up actually setting ‘Content-Length’ to be a larger value than it even was originally, due to the inclusion of data in the output which was not intended to be included.  
  
Yes it would be nice to see WSGI middleware do the correct thing, but reality is that not everyone is going to get WSGI middleware correct. As a result, the better solution here in relation to wsgi.file\_wrapper, is for a future revision of the WSGI specification to be amended so as to allow a ‘filesize’ argument to optionally be provided to wsgi.file\_wrapper.  
  
By doing this it puts control of how much data is returned from the iterable produced by wsgi.file\_wrapper in the hands of the code which is invoking wsgi.file\_wrapper in the first place, rather than relying on WSGI middleware to be implemented properly.  
  
So, where as the FileWrapper class type previously may have been implemented as:
    
    
    class FileWrapper:  
        def __init__(self, filelike, blksize=8192):  
            self.filelike = filelike  
            self.blksize = blksize  
            if hasattr(filelike, 'close'):  
                self.close = filelike.close  
        def __getitem__(self, key):  
            data = self.filelike.read(self.blksize)  
            if data:  
                return data  
            raise IndexError

it would instead be implemented as:
    
    
    class FileWrapper:  
        def __init__(self, filelike, blksize=8192, filesize=-1):  
            self.filelike = filelike  
            self.blksize = blksize  
            self.filesize = filesize  
            if hasattr(filelike, 'close'):  
                self.close = filelike.close  
        def __getitem__(self, key):  
            if self.filesize < 0:  
                data = self.filelike.read(self.blksize)  
                if data:  
                    return data  
            elif self.filesize > 0:  
                blksize = self.blksize  
                if blksize > self.filesize:  
                    blksize = self.filesize  
                data = self.filelike.read(blksize)  
                self.filesize -= len(data)  
                if data:  
                    return data  
            raise IndexError

Our original example could then be reimplemented as:
    
    
    def application(environ, start_response):  
        status = '200 OK'  
      
        filelike = file('/usr/share/dict/words', 'r')  
      
        blksize = 8192  
        filesize = 1024  
      
        response_headers = [('Content-Type', 'text/plain'),  
                            (‘Content-Length’, str(filesize)),]  
        start_response(status, response_headers)  
      
        file_wrapper = environ.get('wsgi.file_wrapper', None)  
      
        if file_wrapper:  
            return file_wrapper(filelike, blksize, filesize)  
        else:  
            return iter(lambda: filelike.read(blksize), '')

Even though the file size is now being passed as a parameter, we still need to set the ‘Content-Length’ header in the response for completeness. This is because the only situation where it may be set for us, if is the WSGI gateway did actually decide to implement platform specific optimisations for wsgi.file\_wrapper and set it for us, but even that is not guaranteed. We have at least though ensured that any WSGI middleware will only consume as much of the iterable created by wsgi.file\_wrapper as we may want it to and not produce an entirely incorrect result.  
  
Look closely though and we still have problems where a platform doesn’t provide wsgi.file\_wrapper, at least with the simplistic alternative shown using iter and lambda. This is because that code is still going to read to the end of the file rather than it being restricted to how much data we want it to be able to read.  
  
This means that if wsgi.file\_wrapper is going to continue to be optional, we have to always also provide our own implementation of the FileWrapper class as shown above and use it as:
    
    
    if file_wrapper:  
        return file_wrapper(filelike, blksize, filesize)  
    else:  
        return FileWrapper(filelike, blksize, filesize)

That is plain stupid, especially since people may not realise the importance of implementing a file wrapper with a size restriction when they aren’t wanting to return the complete contents of the file or where it is possible the amount of data in the file could change.  
  
It is therefore suggested that in addition to the file size being able to be specified to wsgi.file\_wrapper, that it be made mandatory that wsgi.file\_wrapper be supplied.  
  
This should be the case even if a specific WSGI gateway or adapter cannot provide an optimised way for delivering the file back to the client. In this case it would simply provide the FileWrapper implementation described here as wsgi.file\_wrapper instead, thereby avoiding users having to provide their own all the time.  
  
The code could thus be simplified to:
    
    
    def application(environ, start_response):  
        status = '200 OK'  
      
        filelike = file('/usr/share/dict/words', 'r')  
      
        blksize = 8192  
        filesize = 1024  
      
        response_headers = [('Content-Type', 'text/plain'),  
                            (‘Content-Length’, str(filesize)),]  
        start_response(status, response_headers)  
      
        file_wrapper = environ['wsgi.file_wrapper']  
      
        return file_wrapper(filelike, blksize, filesize)

on the basis that wsgi.file\_wrapper would always exist. So, one less thing for programmers of WSGI applications to worry about and get wrong and a bit less of a burden on implementors of WSGI middleware as well.

---

## Comments

### Graham Dumpleton - January 5, 2011 at 9:59 PM

If you have any comments about the topic of this post, you are best probably taking up the issue on the Python WEB-SIG mailing list. Be aware that this post is only one of a series of posts about wsgi.file\_wrapper issues and potential remedies. To solve some of the short comings of wsgi.file\_wrapper is going to need a refactoring of the current WSGI specification at a basic level, so you may want to wait until the whole series of posts about wsgi.file\_wrapper issues has been completed before commenting.

