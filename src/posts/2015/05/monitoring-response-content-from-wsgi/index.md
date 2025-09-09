---
layout: post
title: "Monitoring the response content from a WSGI application."
author: "Graham Dumpleton"
date: "2015-05-23"
url: "http://blog.dscpl.com.au/2015/05/monitoring-response-content-from-wsgi.html"
post_id: "7325859312769573665"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 0
published_timestamp: "2015-05-23T21:41:00+10:00"
blog_title: "Graham Dumpleton"
---

I have been focusing in the last couple of [posts](/posts/2015/05/returning-string-as-iterable-from-wsgi/) about the overheads of generating response content from a WSGI application as many separate blocks rather than as one large block. This has illustrated how there can be quite marked differences between different WSGI servers and even with a specific WSGI server depending on how it is configured or integrated into an overall architecture. 

In this post I want to look at how we could actually add monitoring which could track how much data is actually being returned in a response and how many blocks it was broken up into. We can also track how much time was being spent by the WSGI server trying to write that data back to the HTTP client.

# Monitoring overall response time

Previously I presented a decorator which could be applied to a WSGI application to time the overall response time. That is, how long it took for the complete handling of the request, including the processing of the request content, as well as the generation of the response and the writing of it back to the HTTP client.

The code for the decorator was:

```
 from __future__ import print_function
 
 
 from wrapt import decorator, ObjectProxy  
 from timeit import default_timer  
   
 class WSGIApplicationIterable1(ObjectProxy):
 
 
     def __init__(self, wrapped, name, start):  
         super(WSGIApplicationIterable1, self).__init__(wrapped)  
         self._self_name = name  
         self._self_start = start
 
 
     def close(self):  
         if hasattr(self.__wrapped__, 'close'):  
             self.__wrapped__.close()
 
 
         duration = default_timer() - self._self_start  
         print('finish %s %.3fms' % (self._self_name, duration*1000.0))
 
 
 @decorator  
 def timed_wsgi_application1(wrapped, instance, args, kwargs):  
     name = wrapped.__name__
 
 
     start = default_timer()  
     print('start', name)
 
 
     try:  
         return WSGIApplicationIterable1(wrapped(*args, **kwargs), name, start)
 
 
     except:  
         duration = default_timer() - start  
         print('finish %s %.3fms' % (name, duration*1000.0))  
         raise
```

Although described as a decorator, this is actually implementing a form of WSGI middleware. In this case the middleware was intercepting the act of calling the WSGI application to handle the request and the finalisation of the request through the calling of any 'close\(\)' method of the returned iterable.

What we didn't intercept in any way was the request content or response content. So what we want to do now is extend this to intercept the response content as it is generated so that we can count how many bytes are being generated and as how many blocks.

# Intercepting the response content

To understand what is now needed to intercept the response content we need to look at how a WSGI server actually interfaces with the WSGI application. This interaction can be seen in the sample CGI to WSGI bridge presented in the [WSGI specification](https://www.python.org/dev/peps/pep-3333/#the-server-gateway-side).

The key part of the sample code presented in the WSGI specification is as follows and has three parts.

```
     result = application(environ, start_response)
 
 
     try:  
         for data in result:  
             if data:  
                 write(data)  
             if not headers_sent:  
                 write('')
 
 
     finally:  
         if hasattr(result, 'close'):  
             result.close()
```

The first part is the calling of the WSGI application. It is the result of this call which has been wrapped by our timing wrapper.

The result returned is then iterated over to yield each data block making up the response, with it being written back to the HTTP client.

Finally, the 'close\(\)' method is then called on the iterable. The 'close\(\)' method of the iterable is called whether or not the iterable was completely consumed. The iterable may not be completely consumed if while generating any response an exception occurred, or if when writing the response back to the HTTP client an error occurred, such as the connection being dropped.

In the middleware wrapper we are so far intercepting the original WSGI application call and the call to 'close\(\)'.

In order to now intercept the response content we need to intercept the creation of the iterator object from the iterable when the 'in' statement is applied to it in the loop.

To do that, we need to intercept the special '\_\_iter\_\_\(\)' method of the iterable. As it stands right now, due to the wrapper for the iterable being implemented as a derived class of the 'ObjectProxy' class from the 'wrapt' package, the call of the '\_\_iter\_\_\(\)' method is being automatically applied to the original wrapped iterable. In effect the object proxy is doing:

```
     def __iter__(self):  
         return iter(self.__wrapped__)
```

We want to do more than simply process in some way the iterator object itself. Instead we want to process each yielded item. For this we need to iterate over the original wrapped iterable object ourselves, turning the '\_\_iter\_\_\(\)' method into a generator function. This can be done as:

```
     def __iter__(self):  
         for data in self.__wrapped__:  
             yield data
```

# The archaic write\(\) callback

The job of intercepting the response content seems simple enough but simply overriding '\_\_iter\_\_\(\)' is unfortunately not enough if you want a completely correct WSGI middleware. This is because returning an iterable is not the only way that it is possible to return response content.

To support certain older style Python web applications that preceded the WSGI specification, another way of generating response content is supported. This is via a 'write\(\)' callback function which is returned by the 'start\_response\(\)' function when called by the WSGI application.

When this 'write\(\)' callback function is used to provide the response content, then the iterable returned by the WSGI application would normally be an empty list. The code above would therefore never actually see any response content.

I have blogged previously about this [hidden 'write\(\)' callback](/posts/2012/10/wsgi-middleware-and-hidden-write/) and although a correct WSGI middleware should support it, for the purposes of this analysis I am going to ignore it.

Ignoring the 'write\(\)' callback function will not affect the operation of the wrapped WSGI application, but it means that if the 'write\(\)' callback function were used, we wouldn't report anything about the response content generated that way.

# Overheads of adding monitoring

Now, before we get started on adding to the basic loop for intercepting the actual response content, it is important to highlight that monitoring isn't necessarily free.

In our original timing decorator for the WSGI application we introduced a number of additional function calls, however that number was fixed for each request handled. The additional overhead from these extra calls would be acceptable so long as what those calls themselves did wasn't excessive.

When we start talking about intercepting the request content so as to accumulate metric information about the data being generated for the response, we would be adding extra calls and processing for every distinct data block.

We have already seen how an excessive number of distinct data blocks in a worst case scenario can be a problem with some WSGI servers. We therefore have to be very careful, as although the additional overhead of the monitoring code may not present a problem when there are a small number of data blocks, the extra work being performed could exacerbate the worst case scenario and severely affect the responsiveness of the monitored application at the one time the server is already stressed and so when you don't want that to occur.

Ideally the generation of metric information about a request would be embedded within the WSGI server itself so as to avoid the need to add in special wrappers which add to the number of intermediate calls being made. Unfortunately the majority of WSGI servers provide no such functionality. The next best alternative is to consider writing any such monitoring wrappers as a Python C extension to limit the potential overhead.

However monitoring is added, one key thing to try and always avoid is doing too much processing during the life of the request itself. Any extra processing that is done during the request will obviously add to the response time as seen by the user. Thus you should try and do the absolute minimum while the request is being handled and try to defer more complex processing based on any raw data collected, until after the request has completed.

By doing this the impact on the response time is at least reduced, albeit that it still potentially comes at a cost. This extra cost may be in extra memory usage due to needing to hold raw data for processing at the end of the request, but also in additional CPU usage from doing that processing.

Deferring complex processing until the end of the request will also still keep that request thread busy until it is complete, preventing it from being released to handle a subsequent request, be that a request on a totally distinct connection or a request on a keep alive connection. This delayed release of the request thread can therefore potentially cause a reduction in available server capacity.

Overall, monitoring is a bit of a balancing act. You can't avoid all overheads from monitoring and so when monitoring is first added you may see a reduction in performance as a result. The visibility one gets from adding monitoring though allows you to more easily identify potential issues and fix them. You therefore quite quickly get to a better point than where you were originally without monitoring and so the hit you take from the monitoring is worth it.

You could well at this point remove the monitoring and so eliminate the overheads once more, but you would then be running in the dark again and so have no idea when you introduce some bad code once more. Best to accept the initial overheads and just get on with improving your code from what you learn. Just be careful in designing the monitoring code to reduce the overheads as much as possible.

That all said, let's try and continue by calculating a baseline to gauge how much overhead any monitoring may be adding. For that we can first try to use our prior test example whereby we returned a large string as the iterable.

```
 from timer1 import timed_wsgi_application1
 
 
 @timed_wsgi_application1  
 def application(environ, start_response):  
     status = '200 OK'  
     output = 100000 * b'Hello World!'
 
 
    response_headers = [('Content-type', 'text/plain'),  
        ('Content-Length', str(len(output)))]  
     start_response(status, response_headers)
 
 
    return output
```

With our original decorator which measures just the length of time spent in the WSGI application, when we use mod\_wsgi-express this time we get:

```
 start application  
 finish application 6269.062ms
```

If we override the '\_\_iter\_\_\(\)' method to introduce the loop but not do any processing:

```
     def __iter__(self):  
         for data in self.__wrapped__:  
             yield data
```

we now get:

```
 start application  
 finish application 6291.978ms
```

Not much difference, but a further big warning has to be made.

The problem with making minor changes like this and triggering one off test runs is that it is actually really hard to truly gauge the impact of the change, especially in a case like this where one was already stressing the WSGI server quite severely, with CPU usage peaking up towards 100%.

This is because when a system is being stressed to the maximum, the variability between the results from one run to the next can be quite marked and so when there isn't much difference the results for the two variations on the code can actually overlap as the result values bounce around.

Although the normal approach to eliminating such variability is to run the benchmark test many many times and try and determine some sort of average, or at least eliminate outliers, this doesn't generally help in a situation where the WSGI server is being stressed to breaking point.

This is actually one of the big mistakes people make when trying to benchmark WSGI servers to try and work out which may be able to handle the greatest throughput. That is, they just flood the WSGI servers with requests such that they are overloaded, which only serves to generate results which are quite unpredictable.

When trying to evaluate WSGI server performance it is better to evaluate how it behaves at a level of about 50% capacity utilisation. This is a level whereby you aren't triggering pathological cases of performance degradation through overloading, yet still gives you some measure of head room for transient peaks in the request throughput.

If you are constantly pushing high levels of capacity utilisation in a WSGI server then you should really be looking at scaling out horizontally to ensure you have the spare capacity to meet demands as they arise, rather than running the WSGI server at breaking point.

So trying to gauge overheads at this point is partly a pointless exercise with the test we have, so lets just get on with implementing the code instead and we will revisit the issue of measuring overhead later.

# Counting writes and bytes

The initial change we were therefore after was tracking how much data is actually being returned in a response and how many blocks it was broken up into. Overriding the '\_\_iter\_\_\(\)' method we can do this using:

```
 class WSGIApplicationIterable2(ObjectProxy):
 
 
     def __init__(self, wrapped, name, start):  
         super(WSGIApplicationIterable2, self).__init__(wrapped)  
         self._self_name = name  
         self._self_start = start  
         self._self_count = 0  
         self._self_bytes = 0
 
 
     def __iter__(self):  
         count = 0  
         bytes = 0  
         try:  
             for data in self.__wrapped__:  
                 yield data  
                 count += 1  
                 bytes += len(data)  
         finally:  
             self._self_count = count  
             self._self_bytes = bytes
 
 
     def close(self):  
         if hasattr(self.__wrapped__, 'close'):  
             self.__wrapped__.close()
 
 
         duration = default_timer() - self._self_start  
         print('write %s blocks %s bytes' % (self._self_count, self._self_bytes))  
         print('finish %s %.3fms' % (self._self_name, duration*1000.0))
```

Run this with our test example where a string was returned as the iterable rather than a list of strings, we get:

```
 start application  
 write 1200000 blocks 1200000 bytes  
 finish application 5499.676ms
```

This is in contrast to what we would hope to see, which is a small as possible number of blocks, and even just the one block if that was achievable without blowing out memory usage.

```
 start application  
 write 1 blocks 1200000 bytes  
 finish application 4.867ms
```

What we are obviously hoping for here is a low number of blocks, or at least a high average number of bytes per block. If the average number of bytes per block is very low, then it would be worthy of further inspection.

# Time taken to write output

Tracking the number of bytes written and the number of blocks can highlight potential issues, but it doesn't actually tell us how long was spent writing the data back to the HTTP client. Knowing the time taken will help us confirm whether the response being returned as a large number of blocks is an issue or not. To capture information about the amount of time taken we can use:

```
 class WSGIApplicationIterable3(ObjectProxy):
 
 
     def __init__(self, wrapped, name, start):  
         super(WSGIApplicationIterable3, self).__init__(wrapped)  
         self._self_name = name  
         self._self_start = start  
         self._self_time = 0.0  
         self._self_count = 0  
         self._self_bytes = 0
 
 
     def __iter__(self):  
         time = 0.0  
         start = 0.0  
         count = 0  
         bytes = 0  
         try:  
             for data in self.__wrapped__:  
                 start = default_timer()  
                 yield data  
                 finish = default_timer()   
                 if finish > start:  
                     time += (finish - start)  
                 start = 0.0  
                 count += 1  
                 bytes += len(data)  
         finally:  
             if start:  
                 finish = default_timer()  
                 if finish > start:  
                     time += (finish - start)
 
 
         self._self_time = time  
         self._self_count = count  
         self._self_bytes = bytes
 
 
     def close(self):  
         if hasattr(self.__wrapped__, 'close'):  
               self.__wrapped__.close()
 
 
         duration = default_timer() - self._self_start  
         print('write %s blocks %s bytes %.3fms' % (self._self_count,  
                 self._self_bytes, self._self_time*1000.0))  
         print('finish %s %.3fms' % (self._self_name, duration*1000.0))
```

In this version of the wrapper we time how long it took to yield each value from the loop. This has the affect of timing how long it took any outer layer, in this case how long the WSGI server took, to process and write the block of data back to the HTTP client.

Running our test example now we get:

```
 start application  
 write 1200000 blocks 1200000 bytes 6654.018ms  
 finish application 7812.504ms
```

We can therefore see that the time taken in writing out the actual data took a large proportion of the overall response time. In this case the actual test example wasn't itself doing much work so that would have been the case anyway, but the magnitude of the amount of time spent writing the response in conjunction with the number of blocks is the concern.

Do though keep in mind that even if you were writing as few blocks as possible that if a large amount of data was involved, that the WSGI server could itself block when writing to the socket if the HTTP client wasn't reading the data quickly enough.

The time taken can therefore be helpful in pointing out other issues as well and not just the cumulative impact of writing many small blocks of data.

The big question now is how you turn such information into actionable data.

Using print statements to output timing values is all well and good in a test scenario when playing around with WSGI servers, but it isn't of any use in a production environment. The next step therefore is to look at how one can capture such information in bulk in the context of a production environment and whether it still remains useful at that point.