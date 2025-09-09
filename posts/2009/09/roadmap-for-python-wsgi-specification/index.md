---
title: "A roadmap for the Python WSGI specification."
author: "Graham Dumpleton"
date: "Thursday, September 17, 2009"
url: "http://blog.dscpl.com.au/2009/09/roadmap-for-python-wsgi-specification.html"
post_id: "6796371828982948720"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'wsgi']
comments: 23
published_timestamp: "2009-09-17T21:50:00+10:00"
blog_title: "Graham Dumpleton"
---

**EDIT: Note that the discussion around this on the Python WEB-SIG went round in many circles and died. Thus nothing much here came into being and thus should be viewed merely for amusement value and not taken as being any indicator of any sort of reality.**

  


The discussion on the Python WEB-SIG about what to do about WSGI and Python 3.X has been going round and round in circles for some time now without any resolution. I could be optimistic and say it was a spiral which was at least slowly approaching a solution, but given how long it has been going on, I am much too pessimistic now about seeing any consensus coming out of the Python WEB-SIG.

  


This whole process has been quite frustrating as I don't have the time to sit around and constantly prod the discussion forward. Because of the whole uncertainty though, I have also held off releasing mod\_wsgi 3.0, which for all intent and purposes has been ready for quite a while, including support for Python 3.X. That the WSGI question for Python 3.X was unresolved, it just never felt right to release it, because if it turns out people decided to do something quite different in respect of WSGI for Python 3.X, then it would inconvenience anyone who had relied on how mod\_wsgi had already implemented support for Python 3.X.

  


Anyway, a few weeks back I was having a bit of discussion about WSGI directly with Robert Brewer of the CherryPy project. This discussion has also stalled, partly because I still don't have the time at present to pursue it but also perhaps because Robert and I also didn't seem to agree on some issues. Despite that, the discussion has been good in that it has at least helped to crystalise in my mind how some aspects of the WSGI specification should be interpreted and why people perhaps have divergent opinions on what to do.

  


Since then I have also learnt that Armin Ronacher and Ian Bicking have set off on their own course in rewriting the WSGI specification. So, it looks like the proliferation of divergent views is possibly just going to get worse and not better, especially since looks like everyone is giving up on the Python WEB-SIG and more or less going it alone.

  


The point of this post is then for me to describe how I see things in respect of some aspects of WSGI and how that might relate to WSGI going forward, not just for Python 3.X, but also in relation to future versions of the WSGI specification for Python 2.X. It is also in part about setting down some language or terms to apply to discussions about WSGI so we are all reading from the same page.

  


Now, the major sticking point in the discussions with how WSGI 1.0 should be applied to Python 3.X was the argument over whether byte strings or unicode strings should be used. And if unicode strings were used, what encoding should be used when interpreting the original byte string value for those CGI variables.

  


The specification for WSGI 1.0 is quite clear on this point though in that it says:

  


"""HTTP does not directly support unicode, and neither does this interface. All encoding/decoding must be handled by the application; all strings passed to or from the server must be standard Python byte strings, not unicode objects. The result of using a unicode object where a string object is required, is undefined."""

  


In other words, this clearly states that byte strings should be used everywhere, and so for Python 3.X that would mean that all strings used in the interface should be of type 'bytes'.

  


The alternate view that unicode strings should be used arises in part because the WSGI 1.0 specification also says:

  


"""On Python platforms where the str or StringType type is in fact unicode-based \(e.g. Jython, IronPython, Python 3000, etc.\), all "strings" referred to in this specification must contain only code points representable in ISO-8859-1 encoding \(\u0000 through \u00FF, inclusive\)."""

  


That Python 3000, ie., Python 3.X, is mentioned, suggests that for Python 3.X at least, a unicode string must be used albeit subject to the restriction mentioned.

  


You have to remember though that the WSGI specification was drafted back in 2003 before Python 3.0 even existed. The first discussion about a distinct byte string type in Python 3.0 didn't seem to arise until the latter part of 2004.

  


It is arguable therefore, that Python 3000 should not be mentioned in that context within the WSGI specification, because Python 3.0 ended up with a distinct byte string type in the form of the 'bytes' type and so the alternate way of doing things for Jython, for example, didn't need to apply.

  


Setting that aside for a moment, lets review the key bits of the WSGI interface and how the bytes vs unicode strings factors into that.

  


If one takes the first statement from the WSGI 1.0 specification above that all strings are byte strings as gospel, then we can say the following in respect of certain key aspects of the WSGI interface where string type is an issue.

  


1\. The application is passed an instance of a Python dictionary containing what is referred to as the WSGI environment. All keys in this dictionary are byte strings.

  


2\. For the WSGI variable 'wsgi.url\_scheme' contained in the WSGI environment, the value of the variable should be a byte string.

  


3\. For the CGI variables contained in the WSGI environment, the values of the variables are byte strings.

  


4\. The WSGI input stream 'wsgi.input' contained in the WSGI environment and from which request content is read, should yield byte strings.

  


5\. The status line specified by the WSGI application must be a byte string.

  


6\. The list of response headers specified by the WSGI application must contain tuples consisting of two values, where each value is a byte string.

  


7\. The iterable returned by the application and from which response content is derived, must yield byte strings.

  


For later reference, will label this as 'Definition \#1'.

  


As written, this will work with CPython implementations of Python 2.X and Python 3.X with no ambiguity. For Python 2.X, the byte strings will be the 'str' type. For Python 3.X, the byte strings will be the 'bytes' type.

  


For a Python 2.X implementation on Jython, which doesn't have a distinct byte string implementation, this can still work, but as the second statement from the WSGI specification above indicates, a unicode string is used instead with the restriction on what characters can appear in the string.

  


What should be highlighted is that for Jython, as I understand it at least, when reading from a socket connection it returns a unicode string. That unicode string will only have characters in the range \u0000 through \u00FF, inclusive. Further, it is possible to transcode that unicode string without needing to go through a separate byte string type.

  


Neither of these act the same with Python 3.X, where reading from a socket connection returns an instance of the 'bytes' type. Although you can decode that to a unicode string, you can't transcode that unicode string to another unicode string without converting it back to an instance of the 'bytes' type first.

  


This is therefore why I can't see how Python 3.X can be compared to the Jython case and treated the same way.

  


Even if you did try and apply it the same way, you need to consider that wsgi.input is nearly always going to be associated with a socket connection. To apply it literally the WSGI adapter would also need to convert all the strings of type 'bytes' read from the socket connection to unicode strings before they are passed back to the WSGI application for consumption.

  


Because though the WSGI application may want the unicode string to have been decoded as UTF-8 instead of ISO-8859-1, it is just going to have to convert them back to 'bytes' and decode them again. To have to do that would be just plain stupid.

  


Those who push that unicode strings should be used for Python 3.X, admittedly don't use that interpretation and instead still have wsgi.input returning 'bytes'. To do that though, they are admitting in part that the above rule cannot or should not be applied. As such, they are only taking part of what was actually stated for Python 3000, and in reality they are ignoring what the WSGI 1.0 specification says even though they point to the WSGI specification for justification of their interpretation.

  


Admittedly though, having to deal with everything as 'bytes' in Python 3.X could be a bit onerous, given that byte strings in Python 3.X no longer behave exactly like they did for the byte string type in Python 2.X. Even so, WSGI 1.0 is how it is and I believe it is quite clear that byte strings should be used for Python 3.X.

  


The discussion on the Python WEB-SIG is therefore really more about making WSGI easier to use in Python 3.X, rather than just confirming how WSGI 1.0 should work under Python 3.X.

  


Any attempt though to make WSGI more usable under Python 3.X should perhaps though not be called WSGI 1.0, but be defined as a later version of WSGI. If it is a later version, to avoid having two WSGI specification streams, one for Python 2.X and another for Python 3.X, the revised version must also be able to be applied to Python 2.X in a meaningful way so that there remains one specification.

  


Personally though, I think that part of the problem with the WSGI specification is that it tries to describe things only in terms of byte strings and unicode strings. I believe this is wrong and just makes it harder to apply in respect of the different ways Python is implemented between Python 2.X, 3.X on CPython and Jython implementations.

  


What I want to see is the WSGI specification be described in terms of three different types of strings. These are:

  * byte string
  * unicode string
  * native string



What I mean here by 'native string' is the primary string type for a particular Python implementation. For Python 2.X as implemented by CPython, this is a byte string. For Python 3.X, this is a unicode string.

  


I feel that it is important to distinguish native string from a particular implementation as I believe it makes it easier to specify how WSGI should work. The general rule WSGI sets down is that byte strings should be used everywhere, but this isn't necessarily the best approach and the native string is arguably better used in some places and as such what type it actually is depends on what Python implementation is used. Doing this means it will be easier to have one definition that works for different implementations rather than having to effectively maintain multiple versions or special exceptions.

  


As to 'byte string', since some Python implementations don't actually have a distinct byte string type, what constitutes a byte string would be determined from what type is returned were a read performed on a socket object. This is why for Python 3.X, the 'bytes' type it provides is still what needs to be used, where as for a Python implementation on top of Jython, a unicode string with restriction on characters being in range 0x00 to 0xFF is used.

  


Using those terms for the different string types, as a first step towards a new version of WSGI specification, I see Definition \#1 above at least being redefined as follows.

  


1\. The application is passed an instance of a Python dictionary containing what is referred to as the WSGI environment. All keys in this dictionary are native strings. For CGI variables, all names are going to be ISO-8859-1 and so where native strings are unicode strings, that encoding is used for the names of CGI variables

  


2\. For the WSGI variable 'wsgi.url\_scheme' contained in the WSGI environment, the value of the variable should be a native string.

  


3\. For the CGI variables contained in the WSGI environment, the values of the variables are byte strings.

  


4\. The WSGI input stream 'wsgi.input' contained in the WSGI environment and from which request content is read, should yield byte strings.

  


5\. The status line specified by the WSGI application must be a byte string.

  


6\. The list of response headers specified by the WSGI application must contain tuples consisting of two values, where each value is a byte string.

  


7\. The iterable returned by the application and from which response content is derived, must yield byte strings.

  


For later reference, will label this as 'Definition \#2'.

  


So, still no trouble for us to implement that for Python 3.X as is. The question is whether the result is useful.

  


To gauge this, first consider the WSGI hello world example. This is:
    
    
    def application(environ, start_response):  
    status = '200 OK'  
    output = 'Hello World!'  
      
    response_headers = [('Content-type', 'text/plain'),  
                       ('Content-Length', str(len(output)))]  
    start_response(status, response_headers)  
      
    return [output]

It would be nice if this example would continue to work in Python 3.X. If it doesn't then it is going to be mighty confusing for anyone reading any existing books or documentation on WSGI who is moving from Python 2.X to Python 3.X.

  


Unfortunately, since all those strings will be unicode strings when run under Python 3.X, it isn't going to work. For this simple hello world example to work with WSGI under Python 3.X per Definition \#1 or \#2, it would need to be written as:
    
    
    def application(environ, start_response):  
    status = b'200 OK'  
    output = b'Hello World!'  
      
    response_headers = [(b'Content-type', b'text/plain'),  
                        (b'Content-Length', bytes(str(len(output))))]  
      
    start_response(status, response_headers)  
      
    return [output]

Now, the reason that byte strings are required in the first place is so that the WSGI server doesn't need to make any decisions about what encoding to use when converting unicode strings to byte strings.  


  


In reality though, values such as the status line and the HTTP response headers are generally limited in the characters they can use. Specifically they are limited to characters within the ISO-8859-1 character set.

  


For those values we can therefore take a dual pronged approach. If the values are byte strings then we just pass them through as is. If they are unicode strings, then they would be converted to byte strings by applying ISO-8859-1 encoding. In the event that the unicode string cannot be converted to ISO-8859-1, then an error would be raised.

  


For the response content itself, the encoding needing to be used would more often than not be UTF-8, but this will not always be the case. One may be able to deduce the encoding from the charset attribute of the content type response header, but even that isn't a full proof solution. This is because the charset need not be specified. Also, for a multipart response, different encodings may be used for the different parts of the response.

  


A further problem is that when a unicode string is encoded to bytes, the number of bytes can be different to the number of characters in the original unicode string. If a content length is supplied by the WSGI application along with the unicode strings for the response, can you really completely trust that it is correct. If it was a properly calculated length, why isn't the WSGI application just returning byte strings for content in the first place.

  


Ultimately, how the response content should be converted to bytes and what any corresponding content length for the response will be, will only be truly known to the WSGI application. Having the WSGI server be responsible for this task is therefore not really practical.

  


That said, it still would be preferable for the WSGI hello world example to work unmodified.

  


It could be said that it is just a hello world example and in practice has no relevance, but that isn't quite true. This is because the simplicity of WSGI means that it is fairly trivial for people to produce small purpose built WSGI applications to perform simple tasks, without requiring the use of a large framework. Further, because ISO-8859-1 is the predominant language on the Internet, they may not care therefore about implementing full unicode support.

  


Now, since ISO-8859-1 character data is effectively preserved when converting to bytes, including the derived length, we can therefore apply the same approach as we did before with the status line and response headers. That is, if it is bytes it is passed straight through. If it is a unicode string, it is converted to bytes as ISO-8859-1. If that fails, an error is generated.

  


Doing this, the WSGI hello world example will work as written and instil a bit of confidence in users moving to Python 3.X that life shouldn't be that difficult after all.

  


That deals with the response, but what about the request.

  


Obviously 'wsgi.input' needs to still be dealt with as byte strings. The same issues arise here as for response content. Only the WSGI application will know what encoding is required, if at all, or whether different parts of the request content need to be treated differently.

  


We are left now with the WSGI environment and this is what the bulk of the discussion on the Python WEB-SIG revolved around.

  


Consider here the following example code from Python 2.X and WSGI 1.0.
    
    
    def application(environ, start_response):  
     if environ['REQUEST_METHOD'] == 'GET':  
         ...

In the bytes everywhere interpretation of Definition \#1, for Python 3.X this would have to be written as:
    
    
    def application(environ, start_response):  
     if environ[b'REQUEST_METHOD'] == b'GET':  
         ...

This is because unlike Python 2.X, you can't really compare byte strings and unicode strings and so use them interchangeably.

  


In the interpretation given by Definition \#2 above where the keys in the WSGI environment are native strings, one would still need to use:
    
    
    def application(environ, start_response):  
     if environ['REQUEST_METHOD'] == b'GET':  
         ...

We still don't therefore get the ability to take simple hello world type WSGI applications from Python 2.X and use them unchanged. Unchanged in as much as the native string would be used rather than having to know you have to use byte strings instead. This is awkward and what we want to avoid for the simple case.

  


The original suggestion in this area on the Python WEB-SIG was that for Python 3.X all WSGI environment values be passed as unicode strings decoded from the original byte strings as read from the socket connection, as ISO-8859-1.

  


The intent here is that ISO-8859-1 will preserve the original character data and so although for some CGI variables the actual character data may need to be in a different encoding, one can transcode the data by converting back to bytes and thence again to unicode with the correct encoding without loosing any information.

  


Remember though we want one specification that will work with both Python 2.X and Python 3.X. Thus, we wouldn't want the specification to necessarily refer only to unicode strings. Instead, we would again use the term 'native string'. This way it would work just as well with Python 2.X and be compatible with how WSGI works for Python 2.X today.

  


Combining then the observations about the request and response, the key parts of the WSGI interface where the string type comes into play could thus be defined as follows.

  


1\. The application is passed an instance of a Python dictionary containing what is referred to as the WSGI environment. All keys in this dictionary are native strings. For CGI variables, all names are going to be ISO-8859-1 and so where native strings are unicode strings, that encoding is used for the names of CGI variables

  


2\. For the WSGI variable 'wsgi.url\_scheme' contained in the WSGI environment, the value of the variable should be a native string.

  


3\. For the CGI variables contained in the WSGI environment, the values of the variables are native strings. Where native strings are unicode strings, ISO-8859-1 encoding would be used such that the original character data is preserved and as necessary the unicode string can be converted back to bytes and thence decoded to unicode again using a different encoding.

  


4\. The WSGI input stream 'wsgi.input' contained in the WSGI environment and from which request content is read, should yield byte strings.

  


5\. The status line specified by the WSGI application should be a byte string. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


6\. The list of response headers specified by the WSGI application should contain tuples consisting of two values, where each value is a byte string. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


7\. The iterable returned by the application and from which response content is derived, should yield byte strings. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


For later reference, will label this as 'Definition \#3'.

  


In effect this is what the main proposal has been on the Python WEB-SIG for a while. What is different is that I have incorporated in the term native string to the definition so that the one definition can be equally applied to Python 2.X implemented on CPython as well as Jython.

  


The result is, that as written, the above still describes how WSGI 1.0 works with Python 2.X today and an application written for Python 3.X would effectively be the same. The only thing likely to be seen as different, is that in Python 3.X you have to convert the values of the CGI variables back to byte strings before converting them to a unicode string with a specific encoding if the default is not suitable. In Python 2.X it is already a byte string, so one less step. Although it is an extra step, for the bulk of the CGI variables it wouldn't even be necessary to do such a conversion and so this is going to be much more friendly than using bytes.

  


The big question now is, if this is where people want to go, should WSGI 1.0 be ammended to get rid of the bytes everywhere definition, and instead use this more flexible definition, or should it be viewed as a new version of WSGI.

  


One might think it is the logical thing to do, but every so often someone would comment on the Python WEB-SIG that 'no, I want bytes instead'.

  


What was frustrating was that was about all they would say. They would never then go into more detail and explain exactly what their expectations were.

  


Did they really want it that all the keys and values in the WSGI environment dictionary should be bytes as per the original description. Or was there complaint more about the values of certain key CGI variables.

  


To try and understand what the concern is, we need to start looking at what CGI variables are passed in the WSGI environment.

  


Of the CGI variables passed in the WSGI environment there can more or less be seen to be three distinct categories.

  


The first consists of just the REQUEST\_URI variable. This is the original URI provided by the remote client and identifies the resource being requested. This value includes any original percent-encoded characters from before the server decodes them. The URI may also contain repeating slashes, which may be collapsed into single slashes by some servers when it is being processed and the path normalised.

  


The most important CGI variables and those which fall into the second category are SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING. These are normally derived from REQUEST\_URI by the underlying web server after any decoding and normalising of the URI.

  


Because rewrites can occur in the web server, REQUEST\_URI may not necessarily have a direct relationship with the final resource mapped to. In other words, SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING may actually be derived from some completely different URI calculated within the server. Because of this, REQUEST\_URI, although interesting for debugging purposes, should possibly not be used by WSGI applications directly which intend to be portable between WSGI hosting mechanisms.

  


When these second category of variables finally get passed to a WSGI application, the SCRIPT\_NAME variable identifies the mount point of the WSGI application. The PATH\_INFO variable identifies the target resource within the context of that WSGI application, and QUERY\_STRING are the request query parameters typical of GET style requests.

  


Before we start looking further at the variables in the first two categories, will just state that the last category of CGI variables is effectively everything else.

  


Now, in the case of the first category consisting of just the REQUEST\_URI variable, this is according to the standards only meant to include ASCII characters. Even then, in a URI certain ASCII characters are themselves reserved and need to be percent-escaped. The end result is that in its original form, there seems to be no reason to retain the value as a byte string, at least not at the level of the WSGI application. A WSGI server may need to keep it as bytes when initially processing it, but if a portable WSGI application possibly shouldn't be using REQUEST\_URI directly anyway, what is the point of preserving it as bytes when passed through to the WSGI application.

  


The only justification seems to be where WSGI applications do for some reason still want to deal directly with the value of the REQUEST\_URI and so need to ignore what decoding of the variable was done by the server and do it themselves. In this case they need to decode the percent-escaped values and this is where it starts to get tricky. This is because the decoded

bytes are the raw bytes before any charset encoding is applied to convert it to a unicode string. Ignoring the issues around knowing what charset encoding to apply, the argument simply seems to be that performing manipulations on the strings is simply best done as bytes. If that is the case, it would be a pain if one had to always convert the value of REQUEST\_URI back to a byte string first.

  


Anyway, as much as the fact that the relationship between SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING to the original value of REQUEST\_URI can be tenuous where a server is performing rewriting, one cant say that there aren't valid reasons to be working on REQUEST\_URI directly, and if to use REQUEST\_URI always means needing to go back to bytes, then perhaps it should always be passed as a byte string. It would be nice though for those pushing bytes to properly explain why they need to be working with REQUEST\_URI directly. Up to now they have tended to gloss over why it is important and I don't know enough about implementing Python web frameworks and HTTP decoding to understand why SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING aren't sufficient.

  


Looking again at the second category of variables, SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING. These are derived from REQUEST\_URI by the server. How to extract QUERY\_STRING is fairly obvious, but not so with SCRIPT\_NAME. This is because the value of SCRIPT\_NAME is actually the logical URL at which the WSGI application is mounted. This will be dictated by the way a user has configured the web server. If the WSGI application was mapped such that all requests handled by the server are to be handled by the WSGI application, then SCRIPT\_NAME will be empty. If only requests under a certain URL were to be handled by the WSGI application, then SCRIPT\_NAME will be that sub URL.

  


These are the simple cases, what SCRIPT\_NAME will be can get more complicated than that in a web server which performs some degree of mapping URLs to physical files in the file system. Here the mount point of the WSGI application will be a combination of some URL prefix, a sub section of a file system path and the name of a file containing the WSGI application code or some other information allowing the request to be bridged to the WSGI application.

  


In the first case where the configuration dictates at what URL the WSGI application is mounted, the charset encoding for that part of the URL will be dictated by what charset encoding the configuration file or code specifying the mapping uses. In the latter case where the file system path also matches some component of the URL, then technically, the charset encoding is dictated by both that used for the configuration and that used by the file system. File system paths are typically UTF-8, but configuration and/or code may not.

  


The end result can be a mess where technically different parts of the byte string containing the URL, may need to have been bytes decoded using different charsets. For determining SCRIPT\_NAME, one can only really hope that the underlying web server is getting things right. I guess if it isn't then it will not end up matching against the declared location for the WSGI application and it will never be called and return a 404 instead.

  


So, we just need to trust the underlying web server as far as SCRIPT\_NAME is concerned. In the case of PATH\_INFO though, that is up to the WSGI application and for that, it could well be a different encoding again from what the underlying web server required based on configuration or file system paths. The same also applies to QUERY\_STRING, where the encoding is only going to be known or be able to be determined by the WSGI application.

  


Now, if PATH\_INFO and QUERY\_STRING are always passed as ISO-8859-1, it is quite possible then that the WSGI application will always have to convert them back to a byte string to convert them back to a unicode string with the correct encoding. Since modern web applications tend to always use UTF-8, this is an additional overhead that could be eliminated.

  


This then is perhaps in part why people want byte strings passed instead for these values. That is, it allows the WSGI application to decide what encoding is used.

  


The downside of always passing bytes for the values of these variables is that those not using large frameworks which hide any conversion from byte strings to unicode strings are encumbered with the complexity of having to deal with it even for simple web applications.

  


If modern web applications tend to use UTF-8 the question is then why these variables couldn't instead be converted to unicode strings using that encoding. The problem with that is that for applications which use the full range of ISO-8859-1, this will fail. This in part gets back to why ISO-8859-1 was used in the first place. That is, it works for ISO-8859-1, but it is also byte preserving and can be reversed if you need to use a different encoding.

  


It would perhaps seem that it is going to be impossible to satisfy everyone.

  


One compromise which has been suggested is that the values of SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING be converted to unicode strings using UTF-8. If any of the three variables fails to be converted, then a fallback would occur and ISO-8859-1 would be used. Performing the latter would mean that for that small proportion of cases which are going to be using an encoding other than UTF-8 or ISO-8859-1, that they still have a way of recovering the raw byte string and converting it using the encoding they do need to use.

  


The only trick in this is knowing what encoding was successfully used. The proposal here is that a new WSGI environment variable be introduced. This variable would be called 'wsgi.uri\_encoding'. If the conversion was successful using UTF-8, the 'wsgi.uri\_encoding' would be set to 'UTF-8'. If it failed, the values of the variables would instead be ISO-8859-1 and 'wsgi.uri\_encoding' would correspondingly be set to 'ISO-8859-1'.

  


What we have then is a solution which is likely to handle automatically the vast majority of real world cases. Importantly, no horrible magic would be required for simple applications that don't want to deal with all this stuff.

  


One possible issue might be that to avoid having separate additional variables indicating encoding used for each of SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING, we have said that all of them must be converted successfully as UTF-8. Strictly speaking though the encoding of SCRIPT\_NAME is dictated by the web server as explained previously. In practice though, the likelyhood of different encodings being used for different parts of the URL is slim, with UTF-8 more than likely being used for everything. For simplicity it seems a reasonable compromise.

  


One out on top of this may also be to dicate as part of the WSGI specification that any WSGI adapter must provide an option to allow the encoding used to convert the values of the three variables to be set. That way, if an application was using a special encoding, then that would be attempted instead of UTF-8 with a fallback to ISO-8859-1 still occurring after that. If the special encoding works, then that would be set in 'wsgi.uri\_encoding' as it was before if UTF-8 had worked, or ISO-8859-1 if the fallback occurred.

  


Trying to summarise all that and hopefully perhaps addressing what the bytes advocates desire, or giving them what they need without actually needing to drop down to bytes for everything, what we end up with is the following revised statements about the WSGI interface.

  


1\. The application is passed an instance of a Python dictionary containing what is referred to as the WSGI environment. All keys in this dictionary are native strings. For CGI variables, all names are going to be ISO-8859-1 and so where native strings are unicode strings, that encoding is used for the names of CGI variables

  


2\. For the WSGI variable 'wsgi.url\_scheme' contained in the WSGI environment, the value of the variable should be a native string.

  


3\. For CGI variables other than REQUEST\_URI, SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING contained in the WSGI environment, the values of the variables are native strings. Where native strings are unicode strings, ISO-8859-1 encoding would be used such that the original character data is preserved and as necessary the unicode string can be converted back to bytes and thence decoded to a unicode string again using a different encoding.

  


4\. The WSGI input stream 'wsgi.input' contained in the WSGI environment and from which request content is read, should yield byte strings.

  


5\. The status line specified by the WSGI application should be a byte string. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


6\. The list of response headers specified by the WSGI application should contain tuples consisting of two values, where each value is a byte string. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


7\. The iterable returned by the application and from which response content is derived, should yield byte strings. Where native strings are unicode strings, the native string type can also be returned in which case it would be encoded as ISO-8859-1.

  


8\. For the CGI variable REQUEST\_URI, the value of the variable contained in the WSGI environment will be a byte string.

  


9\. For the CGI variables SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING, the values of the variables in the WSGI environment will be unicode strings. What encoding was used in converting the values to unicode strings will be stored in the special WSGI variable called 'wsgi.uri\_encoding'. The values would be converted to unicode strings using any encoding explicitly specified by the user, or UTF-8 if not supplied. If for either case the conversion failed, then ISO-8859-1 would be used.

  


10\. For the WSGI variable 'wsgi.uri\_encoding' contained in the WSGI environment, the value of the variable should be a native string.

  


For later reference, will label this as 'Definition \#4'.

  


Note that we haven't changed anything about the third category of CGI variables. These would still be native strings as per Definition \#3. This is because these are nearly always going to be ISO-8859-1 anyway. The only exceptions may be CGI variables corresponding to HTTP headers such as Referrer. To try and deal with every exception is going to get too messy if we have to always have a second variable indicating the encoding used and possibly allow user to override the encoding. Thus, leave them as is and accept that they will have to be dealt with specially.

  


The only time that approach might be a pain though is for server specific CGI variables such as DOCUMENT\_ROOT and SCRIPT\_FILENAME. Where such server specific variables are provided a WSGI adapter would be entitled to convert them to unicode strings, in the case where native string is unicode, using the correct encoding rather than ISO-8859-1. This would actually be essential in some cases else those paths when supplied to operating system functions which operate on paths would otherwise fail.

  


At this point we have definitely deviated from what the WSGI 1.0 specification says. This is especially the case where applied to Python 2.X as unicode strings would start to be passed for the values of some variables in the WSGI environment. As such, Definition \#4 if it were to be adopted should almost certainly be cast instead as WSGI 1.1 with 'wsgi.version' being the tuple '\(1,1\)'.

  


If it is a new version number, we may as well go and fixup some of the short comings in other areas of WSGI 1.0. As such, suggested that the following changes also be made on top of what has already been listed in Definition \#4 for WSGI 1.1.

  


11\. The 'readline\(\)' function of 'wsgi.input' may optionally take a size hint. This will mean that 'cgi.FieldStorage' will be legal.

  


12\. The 'wsgi.input' must provide an empty string as end of input stream marker. This will make it easier to consume 'wsgi.input' as not required to ensure that one doesn't read more than CONTENT\_LENGTH. It also opens the window for supporting chunked request content and mutating input filters where CONTENT\_LENGTH will not be present or may not be accurate.

  


13\. The size argument to 'read\(\)' function of 'wsgi.input' would be optional and if not supplied the function would return all available request content. Thus would make 'wsgi.input' more file like as the WSGI specification suggests it is, but isn't really per original definition.

  


14\. The 'wsgi.file\_wrapper' supplied by the WSGI adapter must honour the Content-Length response header and must only return from the file that amount of content. This would guarantee that using wsgi.file\_wrapper to return part of a file for byte range requests would work.

  


15\. Any WSGI application or middleware should not return more data than specified by the Content-Length response header if defined.

  


16\. The WSGI adapter must not pass on to the server any data above what the Content-Length response header defines if supplied.

  


So, what are the final set of suggestions.

  


The first is that although WSGI 1.0 on Python 3.X should strictly be bytes everywhere as per Definition \#1, it is probably too late to enforce this now. This is because wsgiref in Python 3.X has been using the interpretation as per Definition \#3, where the values of the WSGI variables would be passed as ISO-8859-1 and where unicode strings are allowed in the response so long as they can be converted to byte strings as ISO-8859-1. Although mod\_wsgi 3.0 has not yet been officially released, it was also using this interim interpretation, with people having been using the code either from the subversion trunk or by way of the release candidates.

  


It is known that there are various people out there implementing WSGI applications with Python 3.X with the expectation that things will work as per Definition \#3. It sort of seems a bit brutal to tell them that all their effort is wasted.

  


The second suggestion is though that WSGI 1.0 for Python 3.X, per Definition \#3, be immediately deprecated and instead Definition \#4, which uses 'wsgi.uri\_encoding' to indicate encoding of SCRIPT\_NAME, PATH\_INFO and QUERY\_STRING be adopted as WSGI 1.1. Any Python 3.X WSGI adapter should default to WSGI 1.1 although could be configured as necessary to use the WSGI 1.0 interpretation instead. By promoting WSGI 1.1 as the default for Python 3.X, we are setting the way forward and people will not be as inclined to ignore it and persist with WSGI 1.0.

  


The final one is that in the case of Python 2.X WSGI adpaters, these would still default to WSGI 1.0, but could be configured instead to use WSGI 1.1 as per Definition \#4.

  


The purpose of WSGI 1.1 in Python 2.X, as well as being the way forward in general, would be to allow an easier transition to Python 3.X, by allowing people to convert to WSGI 1.1 first and then using 2to3 to jump to Python 3.X. The thought here is that WSGI 1.1 per Definition \#4 may be a better platform for 2to3 than WSGI 1.0 as the WSGI adpater itself will be worrying about the conversion to unicode strings for key values in the WSGI environment which will possibly remove some of the issues with the 2to3 conversion.

  


If we want to be brave, we also introduce WSGI 2.0 at this point as well. This would be WSGI 1.1 but with 'start\_response' eliminated and a simple tuple returned. The hello world application for WSGI 2.0 would be.
    
    
    def application(environ):  
       status = '200 OK'  
       output = 'Hello World!'  
      
       response_headers = [('Content-type', 'text/plain'),  
                           ('Content-Length', str(len(output)))]  
      
       return (status, response_headers, [output])

So, there we have my ideas for a roadmap for WSGI. These aren't strictly speaking all my own ideas, but instead bring together ideas of various people in an attempt to come up with some whole that might satisfy most of what people are putting forward as requirements.

  


Hopefully having laid this all out with the rational and an actual roadmap, we might be able to now bridge any last gaps in the divergent opinions that are out there. I fear that if we can't manage that soon, it is all a lost cause and may as well just move onto other stuff and give up on Python 3.X. It is just becoming too much of a waste of time trying to shephard this forward.

  


If you are going to pull all this apart and give feedback, or you have a differing opinion, then describe it as part of a complete solution by way of an amended definition like I have given along with an explanation rationalising why you think it should be done your way. Too many times the discussions on the Python WEB-SIG went off on tagents in relation to specific issues and the overall picture was lost of how that fit into the whole. I felt that it was when this happened that people started switching off and the discussion died.

  


And please, all you people who want to see WSGI somehow encompass support for asynchronous systems as well as synchronous, hold your fire. That is a distinct issue and is irrelevant to the main problem. A number of times the discussion on the Python WEB-SIG has been derailed because people brought up asynchronous system support. So just leave it be, let us get WSGI for synchronous systems worked out first.

  


Finally, Robert Brewer and Ian Bicking, who hopefully will read this, as maintainers of the other two high profile WSGI hosting mechanisms, I would really like you to see you state your own definitions for how you believe any update should work, or at least clearly state which of the above you think is the right one if you agree. Ultimately I believe it is going to be us three who decide this as we effectively control it by what we implement in our respective packages.

---

## Comments

### fumanchu - September 18, 2009 at 2:39 AM

Finally\! :\)  
  
Your proposal is very very close to what we've already got in CherryPy 3.2 beta; at a cursory glance, the only difference is that we aren't making SCRIPT\_NAME etc unicode for Python 2.x. I'll take a look and see how onerous that might be ASAP.

### James Thiele - September 18, 2009 at 6:50 AM

Please "Just Do It" - release your version.  
  
It won't be the first or last time a programming community has had potentially competing standards.

### PJE - September 18, 2009 at 7:46 AM

I personally vote for \#3 as an amendment/clarification of WSGI 1.0, and then just get working on WSGI 2.0 ASAP. It's really sort of embarrassing that Ruby's port of WSGI is basically on the 2.0 version already, while we languish with ancient backward-compatibility issues.  
  
Anyway, thanks for writing such a nice, step-by-step explanation of the issues.

### Wheat - September 18, 2009 at 8:05 AM

Word count gives me 7,271 words. Longest python blog post ever? I think I wore out my mouse wheel just scrolling through it\! Good stuff though.

### Vinay Sajip - September 18, 2009 at 9:00 AM

Thank you for the clear and precise discussion of the issues. I hope that something workable can be arrived at soon.

### mae - September 18, 2009 at 10:57 AM

Thank you\! I agree 100%, Robert already replied what about Ian? I hope this is settle for ones and for all.

### Graham Dumpleton - September 18, 2009 at 5:05 PM

Robert \(fumanchu\)  
  
Yeah, took me a while after I told you I was writing this and sent you first part to look at it. Work is a bit full on at the moment. Am though becoming somewhat of an expert on Jira/Confluence upgrades and complex JIRA workflow configuration. Generally leaves me quite buggered and not inclined to do much at home, plus our almost 2 year old demands a lot of time as well.  
  
If you are saying that for what we want to call WSGI 1.1 \(wsgi.uri\_encoding\) as we discussed previously and which mutated into what I described, that in Python 2.X it would still have used bytes for SCRIPT\_NAME etc, I am a bit surprised. I got the impression that you were using unicode for SCRIPT\_NAME etc, but also that for non category 1/2, ie. all the other CGI variables, you were also intending to use unicode as well for Python 2.X. This is in part where my comment came about in terms of us disagreeing on things. That is, I thought you were going even further to using unicode in Python 2.X that I had in mind.  
  
It was uncertainties like that which made be really want to lay out all the possibilities as a clear set of rules and try and have everyone try and explain things as a complete set of such rules when trying to discuss different opinions, else it can start to get hard to understand the full picture of what someone thinks. As is, still making assumptions that you are even talking about definition \#4 as applied to Python 2.X.  
  
At the time I was also of mind to push the line on using definition \#1 for WSGI 1.0 on Python 3.X, simply because that is really what the specification says. So, another point of disagreement. I was attracted to definition \#1 as I saw using that definition as a good lever to get people to move to newer version of specification because for most people dealing with all bytes would suck pretty bad and they would probably gladly want to use any new improved version. In the end I felt that the existing practice \(almost defacto specification\), of definition \#3 for WSGI 1.0 on Python 3.X must just have to be lived with now.  
  
The danger in using definition \#3 as I saw it is coming out in PJE's belief that should jump straight from that to WSGI 2.0 and not bother with a WSGI 1.1 as per definition \#4. Am not convinced at this point of skipping WSGI 1.1 even if people agree now that WSGI 2.0 would be definition \#4 with start\_response\(\) dropped.  
  
My concern here is that some number of packages are still dependent on the write\(\) function returned from start\_response\(\). If you go to WSGI 2.0 and drop that, they will be stuck at WSGI 1.0 until they can make major changes to their code to do it the other way. Alternatively, they need to be shown how to use greenlets to get a write\(\) type interface on top of WSGI 2.0. There has been some talk about using greenlets to allow a WSGI 2.0 to WSGI 1.0 bridge, but I don't believe I have ever actually seen an implementation offered up by anyone. If some one actually comes out with that example bridge, and a description of the general technique, maybe I will not be so concerned about skipping WSGI 1.1 and going direct to WSGI 2.0.

### Graham Dumpleton - September 18, 2009 at 10:05 PM

BTW, I should have said that as much as I rant about this stuff, I don't know that much about using it in actual applications. Instead, I just write the WSGI adapter for the server. So, don't trust a word I say. See me as the stupid moderator who is just trying to get people to agree to something. Frankly I don't care what it is, as long as everyone agrees. When they agree, then I'll implement it.

### PJE - September 19, 2009 at 5:35 AM

Just for the heck of it, I sketched a 2-to-1 adapter using greenlets in about 20 minutes just now, about 40 lines of code. No error-handling, though; it just assumes the WSGI 1 app is well-behaved, and that the only difference between WSGI 1 and 2 is the calling convention. \(Technically, it should also change the wsgi.version key and a few other odds and ends.\) But the basic idea seems quite sound, and straightforward to write.

### fumanchu - September 20, 2009 at 3:08 AM

Graham; yes you're right. CherryPy 3.2 beta uses your definition \#1 for WSGI 1.0 for both py2 \(str\) and py3 \(bytes\). And it uses your definition \#4 for WSGI 1.1 for py3 \(str\), but unicode everywhere for py2. So to align completely with your definition \#4, we'd have to switch Python 2/WSGI 1.1 to primarily byte strings.  
  
We can do that fairly easily, but note that for Python 2:  
  
Definition \#1  
env keys: bytes  
wsgi.url\_scheme: bytes  
REQUEST\_URI: bytes  
SCRIPT\_NAME/PATH\_INFO/QUERY\_STRING: unicode  
other cgi vars: bytes  
wsgi.input: bytes  
response status/headers/body: bytes  
  
Definition \#4:  
env keys: bytes  
wsgi.url\_scheme: bytes  
REQUEST\_URI: bytes  
SCRIPT\_NAME/PATH\_INFO/QUERY\_STRING: unicode  
other cgi vars: bytes  
wsgi.input: bytes  
response status/headers/body: bytes  
  
So the upshot is that, for CPython 2, WSGI 1.1 will only differ from WSGI 1.0 by using unicode for SCRIPT\_NAME, PATH\_INFO, and QUERY\_STRING. Not a very compelling reason to upgrade. In fact, CherryPy-the-framework would most likely just change these back to bytes \(using wsgi.uri\_encoding\) to minimize confusion.

### Graham Dumpleton - September 20, 2009 at 1:54 PM

Robert, more confusion.  
  
You say 'CherryPy 3.2 beta uses your definition \#1 for WSGI 1.0 for both py2 \(str\) and py3 \(bytes\)'. I actually thought you were using definition \#3 for WSGI 1.0 on Python 3.X. That is why in the end I thought that definition \#3 may have to be used for WSGI 1.0 on Python 3.X rather than pushing the strict WSGI PEP interpretation I felt was correct.  
  
In other words thought that wsgiref, mod\_wsgi and CherryPy using definition \#3 for Python 3.X and seemed to me too much precedence and possibly code already dependent on that.  
  
As I said, pushing definition \#1 for Python 3.X may actually have been a good thing in my mind as I had a nagging suspicion it would be horrible to work with and so would hurry people along to come up with something better.  
  
Armin wanted definition \#1, but is now interesting in that based on his looking further at bytes in Python 3.X, he is stepping back a bit from that now. Will be interesting now to see what happens.  
  
As to definition \#4 not being much different on Python 2.X, that is true if you only look at those core definitions. More important to me is the clarifications detailed in \(11\) through \(16\) that I was adding on top.  
  
Although I raised the issue of a WSGI 2.0/WSGI 1.0 bridge in response to PJE, of more concern to me in PJE's preference for skipping WSGI 1.1 and going straight to WSGI 2.0, is that those clarifications would then never come to any WSGI 1.X version. That sort of sucks and means we are going to be stuck with WSGI implementations that due to use of cgi.FieldStorage etc, are actually violating the WSGI specification. It isn't just about readline\(\) though, I am seeing more and more cases where people are needing to support chunked request content in streaming manner and WSGI as is doesn't support that.  
  
I could live with deferring any significant change around REQUEST\_URI, SCRIPT\_NAME etc until WSGI 2.0 so long as a WSGI 1.1 came out for Python 2.X which added those clarifications. That would give people more to work with in WSGI implementations for Python 2.X that are going to still stick around for a long time to come.  
  
As to WSGI 1.X on Python 3.X. So long as least WSGI 1.1 came out for Python 2.X, could live with there never being a WSGI 1.X for Python 3.X. In fact I argued for this back at start of 2008, but promptly got chastised by people on the basis that I was saying this because felt that since people were going to have to change their code when moving to Python 3.X, they could live with an API change as well. The 2to3 crowd thought this was sacrilege and that there tool was in part infallible. They didn't understand at the time that WSGI wasn't necessarily just going to work fine as is on Python 3.X without change anyway. The ongoing discussions are proving that last point out and that it isn't going to be a simple transition for WSGI.

### Graham Dumpleton - September 20, 2009 at 1:58 PM

Robert, BTW, I don't think you mean:  
  
SCRIPT\_NAME/PATH\_INFO/QUERY\_STRING: unicode  
  
in your summary of definition \#1 on Python 2.X. Presume you meant bytes, else they are exactly the same.

### fumanchu - September 20, 2009 at 5:08 PM

Yes, I meant bytes. My mistake due to too much copy/paste while commenting.

### fumanchu - September 20, 2009 at 5:11 PM

I guess I spelled out the facts but didn't ask the question: why not make SCRIPT\_NAME/PATH\_INFO/QUERY\_STRING native \(instead of unicode\) for WSGI 1.1?

### Graham Dumpleton - September 20, 2009 at 5:22 PM

What I was trying to avoid was having a WSGI definition which was specific to Python 3.X and have no relevance to Python 2.X. That is, if SCRIPT\_NAME etc are native, then for Python 2.X wsgi.uri\_encoding is meaningless. I thought that having some correspondence between the two would have been a good idea.  
  
I have been trying to draft a followup message to the WEB-SIG about the higher level goals of what we think we want to achieve and get people to agree on that high level plan, separate from the low level details, but trip to take baby to park intruded.

### J - September 25, 2009 at 1:05 AM

Hi there. I'm a user of mod\_wsgi and appreciate the work you've put into it and also into discussing the WSGI specification. All the specification arcana to me is a little difficult, but I had a couple of comments.  
  
1\) I'm not sure what you mean by this:   
  
"Further, because ISO-8859-1 is the predominant language on the Internet, they may not care therefore about implementing full unicode support."  
  
This can't be true, at least not anymore. The predominant language of the Internet is now UTF-8. That's what urls are \(with that percent encoding, but it's not Latin-1 percent encoded is my point\). That's what query parameters are supposed to be \(though some use the encoding of the originating page, but since...\) All the major websites are using utf-8. Google, Yahoo, Blogger, Wordpress, Twitter, Facebook... emails, I think it still varies somewhat, but moving towards UTF-8. Firefox, IE, Chrome, Safari assume UTF-8 for the urls and in my experiments, it respects it in the header too \(ie for redirects\). Regardless of what is underlying, the web interfaces are all UTF-8.  
  
2\) I did a brief scan of some discussion on the Python WEB-SIG mailing list. I understand there are a lot of complex issues for dealing with different versions of Python, WSGI, backwards compatibility, RFCs, etc. But here's an important principle when it comes to encoding:  
  
When dealing with multiple encodings, make everything unicode first, then re-encode to whatever you want.  
  
If you have a case where you are afraid of the user giving you input that can't be coerced to another encoding easily without them telling you what the original encoding was, then force them to give you unicode. Once you have unicode, you can encode to whatever you want. Everything goes to unicode, then you get out whatever you want \(say, UTF-8\). You don't have to worry about invalid \_\_\_\_ because you already made sure it was valid in the original -> unicode conversion. So even if your input isn't unicode and your output isn't unicode, using unicode is quite desirable because it forces for the conversion to be right.  
  
My two cents.

### Graham Dumpleton - September 25, 2009 at 9:18 AM

James.  
  
In relation to \(1\), rather than ISO-8859-1, I perhaps should have said English. What I was trying to get across is that the characters people actually use would fit within ISO-8859-1.  
  
In relation to \(2\), yes you can go to unicode, but given you may not be 100% sure about what encoding is used, you are restricted to assuming a single character encoding such as ISO-8859-1 to be able to reverse it and transcode to another encoding. In other words, you couldn't decode as UTF-8 as not all ISO-8859-1 bytes strings are decodable as UTF-8 and would fail.

### mrts - October 9, 2009 at 6:38 AM

_In relation to \(1\), rather than ISO-8859-1, I perhaps should have said English. What I was trying to get across is that the characters people actually use would fit within ISO-8859-1._  
  
Being a native speaker of a language that doesn't fit into ISO-8859-1 that well \(Estonian\), I'm quite convinced this assumption will cause lots and lots of grief later on.  
  
Let me outline some use cases for you.  
  
1\. I'm a Greek web developer who has registered the domain http://ουτοπία.eu \(IDNs will become more and more common and EU is just right now opening up IDNs in .eu, see http://www.eurid.eu/en/content/december-date-internationalised-eu-domain-names \). I want the domain name to be spelled out as-is in my headers and URLs \(instead of relying on the clunky Punycode http://tools.ietf.org/html/rfc3492 or any other hacks\)  
  
2\. I'm also a professional blogger blogging in Greek. Knowing that search engines give credit to meaningful URLs that match content, I want my URLs match my blog post titles. When I write a blog post about UTF-8 in URLs titled "UTF-8 σε URLs", then I want to link to it as http://ουτοπία.eu/ιστολόγιο/UTF-8 σε URLs/.  
  
3\. I also want to use the _Location: http://ουτοπία.eu/ιστολόγιο/UTF-8 σε URLs/_ header to redirect to that post from my legacy non-Unicode-aware blog.  
  
3\. I often attach pictures to my blog post. The filenames are descriptive and also in greek. When I upload "όμορφη κυρία.jpg" I expect it to be saved under the same name to my filesystem \(that uses UTF-8 encoding\) and served under that filename. I'm either using the _X-Sendfile_ header for serving files to offload the work from my web application to my web server or the wsgi.file\_wrapper mechanism.  
  
\(My apologies for Greek speakers in the audience for the clunky examples.\)

### Graham Dumpleton - October 9, 2009 at 9:14 AM

mrts. All that can still be achieved. The reason ISO-8859-1 is used for request variables is purely because it preserves the byte stream and so can be converted back to bytes and then decoded to a different encoding with out loss of information if your application needs to use a different encoding. For the response, you should be converting stuff like Location back to bytes yourself anyway so you still control the encoding so again, no loss of functional ability.

### Mekk - November 14, 2009 at 11:01 AM

1\) If you said a\) and accept setting the default encoding, maybe it would make sense to say b\) and let the application stack provide _callable\(s\)_ responsible for input decoding \(and maybe output encoding, the latter used to handle all unicode strings which reached that far\). Then utf-8 could be used as default but it would be easy to replace it with anything, from iso-8859-1 decoding to sophisticated dictionary based encoding detection function.  
  
2\) I'd also like to join mrts. Being Polish I fairly often face problems with libraries which assume iso-8859-1 here or there \(for example not that long ago WebError used to crash if debugged source code contained Polish accented characters in comments\). The main risk area here is that of reusable wsgi middlewares. I'd prefer their autors not to rely on native iso-8859-1 strings...  
  
3\) Finally: I have more and more doubts whether _WSGI - the interface between the webserver and the python code_ and _WSGI - the API used for middleware and application writing_ \- should be the same. For "hello world" app, for "fill error messages" or "inject CSRF protection" middlewares it is natural to use unicode. For the request parsing code, but also some middlewares \(gzip/gunzip, external cache interaction, ...\) bytes are natural. And the best moment to en/decode lies usually somewhere in the middle of the stack \(yes, I know, it contradicts suggestion 1\)\). "Byte interface" + reference de/encoding middleware + "unicode interface"?  
  
Well, all those are vague remarks and feel free to ignore them for now. I'd like to see _any_ version released. Your proposals \(especially \#3\) are well thought out, keep things working without ruining anything, and are implementable now.

### J - November 23, 2009 at 6:51 PM

**"\(2\), yes you can go to unicode, but given you may not be 100% sure about what encoding is used, you are restricted to assuming a single character encoding such as ISO-8859-1 to be able to reverse it and transcode to another encoding. In other words, you couldn't decode as UTF-8 as not all ISO-8859-1 bytes strings are decodable as UTF-8 and would fail."**  
  
But the situation is symmetric\! If the original data was encoded as UTF-8, trying to decode using ISO-8859-1 would fail as well\!  
  
ISO-8859-1 is used for some Western European languages, not English, which does fine with just ASCII \(_American_ Standard Code for Information Interchange\), and ISO-8859-1 actually is NOT a common encoding. ASCII is, and these days, the move is towards UTF-8. If you are going to assume an encoding, you should be assuming UTF-8, which will correctly decode all ASCII as well.

### fumanchu - November 24, 2009 at 6:07 AM

@James: unlike many other charsets, decoding with ISO-8859-1 cannot fail for any sequence of bytes--each byte is mapped directly to its corresponding code point. It may not be \*correct\*, but it won't error; that makes it perfectly reversible. Other charsets don't have that property.

### Graham Dumpleton - November 24, 2009 at 8:57 AM

@fumanchu: Hmmm, I thought any of ISO-8859-X would have been okay since they are all single byte charsets. So, could just have readily used ISO-8859-16 although it would have cheesed off people even more.

