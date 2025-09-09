---
title: "WSGI and printing to standard output."
author: "Graham Dumpleton"
date: "Friday, April 3, 2009"
url: "http://blog.dscpl.com.au/2009/04/wsgi-and-printing-to-standard-output.html"
post_id: "1907691383491678344"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'wsgi']
comments: 9
published_timestamp: "2009-04-03T15:47:00+11:00"
blog_title: "Graham Dumpleton"
---

If you use WSGI on top of CGI, the WSGI adapter communicates with the web server using standard input \(sys.stdin\) and standard output \(sys.stdout\). Available WSGI adapters for CGI do not do anything to try and protect the original sys.stdin and sys.stdout. This means that if you use 'print' to output debug messages for your application, without redirecting 'print' to sys.stderr explicitly within your code, then you will actually screw up the response from your WSGI application.

  


Although CGI may not be the most popular platform to host WSGI applications, with the intent of trying to promote the cause of writing portable WSGI application code, in [mod\_wsgi](http://www.modwsgi.org/) the decision was made to restrict access to [sys.stdin](http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Reading_From_Standard_Input) and [sys.stdout](http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Writing_To_Standard_Output) to highlight when non portable WSGI code was being written.

  


The result of doing this is that when 'print' was used in a WSGI application hosted by mod\_wsgi, a Python exception would be raised of the type:
    
    
```
IOError: sys.stdout access restricted by mod_wsgi
```

This was all done with good intention, but what has been found is that people can't be bothered reading the [documentation](http://code.google.com/p/modwsgi/wiki/ApplicationIssues#Writing_To_Standard_Output) which explains why it was done and even when they do, they still can't be bothered fixing up the code not to use 'print'. It seems the convenience of using 'print' out weighs the ideal of writing code that may actually work across different WSGI hosting mechanisms.

  


More annoying is that whenever questions arise about this error on the irc channels, rather than people being told to read the documentation and/or fix their code not to use 'print', voodoo is summoned and they are instead told to use the magic incantation of:
    
    
```
sys.stdout = sys.stderr
```

Yes this is given as one of the workarounds in the documentation, the other being to disable the restriction using the configuration directive specifically for the purpose, but the only reason the workaround is given is for where you have no choice because you cannot change the code to remove the 'print' statement. People aren't told this though, all they are told is to make that change and effectively ignore the whole issue.

  


The whole mythology that is developing around this is now getting to the extent that some have been saying that neither 'sys.stdout' or 'sys.stderr' are working in mod\_wsgi. The suggestion is starting to come out now that if you want to get any debug output from your WSGI application that you have to use a separate log file of your own creation, optionally hooked up to the 'logging' module. In one case, a [BuildOut](http://www.buildout.org/) recipe is explicitly providing an option to define the separate log file that they believe has be used to replace 'sys.stdout' and 'sys.stderr'.

  


So, what is the real answer? Well, if you care about writing portable WSGI application code, then do not use 'print' by itself, instead redirect it to 'sys.stderr' by writing:
    
    
```
print >> sys.stderr, 'message ...'
```

This is especially important if you are writing framework libraries or plugins to be used in some other application or by other users. You shouldn't be making an assumption that 'sys.stdout' can always be used. If it is a debug or error message, then use 'sys.stderr' as it is meant to be.

  


If for some reason you really don't want to care about the issue, then rather than use the magic voodoo above, you should simply disable the restrictions that mod\_wsgi puts into place altogether. This is done by putting in the main Apache configuration file:
    
    
```
WSGIRestrictStdin Off  
WSGIRestrictStdout Off
```

Anyway, because of all the contention arising over all of this, in [mod\_wsgi 3.0](http://code.google.com/p/modwsgi/wiki/ChangesInVersion0300) I will be giving up and will be making the restrictions off by default. If you want to write non portable WSGI application, you can quite happily do so. If you do care about portable WSGI application code, then you will be able to optionally reenable the restriction using the same directives above.

---

## Comments

### Brian Morton - April 3, 2009 at 10:35 PM

This comment has been removed by the author.

### Brian Morton - April 3, 2009 at 10:36 PM

I'm sorry to see you having to make this change to appeal to the unwashed masses who can't read documentation. I will certainly turn that feature back on in mod\_wsgi 3.0.

### garylinux - April 4, 2009 at 3:21 AM

I am trying hard to figure out why I should care if my debugging code is cross system compatible. Its debugging code, written to run on the system I am working on right now.  
It's going to be gone once the bug is tracked down.  
  
The WSGIRestrictStdin Off  
WSGIRestrictStdout Off  
settings would be much more useful for developers if they would work in the .htaccess  
Since \(I think\) the average developer does not have access to the httpd.conf he or she may feel that there is no way to get stdout. Since for them there is not.

### Deron Meranda - April 4, 2009 at 5:36 AM

What about providing a third option, a data sink, like /dev/null. Provide a fake stdout file object that instead of raising an error or sending the output back to CGI, it just silently discards it. Maybe  
  
WSGIRestrictStdin Discard  
  
This could also help in those situations where you have to use a third-party module, that unfortunately sometimes does a stray print.

### Graham Dumpleton - April 4, 2009 at 7:45 PM

@garylinux  
  
It isn't just debug code we are talking about here, it could be quite valid error messages which the application wants to log to the error log file, but people have wrongly used 'print' by itself to send it to stdout instead of stderr. Any WSGI framework library which used stdout for logging error messages would fail to work properly if used with a WSGI application hosted by a CGI/WSGI bridge.  
  
One cant have WSGIRestrictStdin and WSGIRestrictStdout in the .htaccess file because the settings need to be known at the time that the Python interpreter is initialised. This is why they are global directives which affect the main interpreter and all sub interpreters which are created. The .htaccess file is way too late for that as the interpreters are already created before that point.

### Graham Dumpleton - April 4, 2009 at 7:48 PM

@Deron  
  
The issue isn't to have the messages logged to stdout to vanish, it is to get people to log them to the proper output stream, which is stderr.  
  
One thing that both yours and the other response show is that even people who have some experience with Python development don't necessarily understand the greater issues around this. So, what hope is there for an absolute newbie who wouldn't even know about the concepts of standard input, standard output and standard error in the first place. This is why one can never win and you just have to make it accepting of bad programming practice.

### Unknown - September 29, 2009 at 9:51 AM

For Google people that find this post in the future, a cause of:  
  
"sys.stdin access restricted by mod\_wsgi" when moving from dev to production is because of an errant:  
  
import pdb; pdb.set\_trace\(\);  
  
Frustratingly, wsgi will throw an error from the NEXT line so you won't know that pdb caused it :-\)

### Jon R - March 24, 2010 at 5:41 AM

Your suggested "portable" version of  
  
print >> sys.stderr, 'message ...'  
  
is no more portable than the  
  
print 'message ...'  
  
than it's replacing.  
  
It should be:  
  
environ\['wsgi.errors'\].write\('message ...'\)

### Graham Dumpleton - March 24, 2010 at 8:58 AM

Jon, the documentation at 'http://code.google.com/p/modwsgi/wiki/DebuggingTechniques' mentions 'wsgi.errors'. The problem is that most frameworks hide it or it is non obvious how to get access to it. Even more, practically no one realises it is there and uses it and they always just use 'print' without even redirecting it. The 'wsgi.errors' stream is also not available outside of the request context, so useless at global scope when importing modules or in background threads, or library code. Finally, using 'write\(\)' on 'wsgi.errors' is also technically not sufficient anyway as WSGI specification says that to guarantee display of message straight away, must also be flushed. Normally 'sys.stderr' would at least be automatic flush at end of line or earlier, except for broken systems like mod\_python.

