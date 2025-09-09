---
layout: post
title: "Why is WSGI deployment under FASTCGI so painful?"
author: "Graham Dumpleton"
date: "2011-09-20"
url: "http://blog.dscpl.com.au/2011/09/why-is-wsgi-deployment-under-fastcgi-so.html"
post_id: "9079528338602022459"
blog_id: "2363643920942057324"
tags: ['apache', 'fastcgi', 'wsgi']
comments: 7
published_timestamp: "2011-09-20T22:36:00+10:00"
blog_title: "Graham Dumpleton"
---

Out of all the deployment methods for Python WSGI applications, the one which seems to generate the most trouble is FASTCGI deployment. So much so that the general advice one often sees in relation to FASTCGI is that one should simply avoid it. In some cases people will go as far as justifying this by saying that FASTCGI is old technology and the cool kids aren't using it so you shouldn't either.  
  
What is reality here. Well, FASTCGI may be old technology but it does work. If it didn't work the bulk of the PHP web sites out there, which there are many many more of than Python web sites, would be falling over left, right and centre. They don't though, so the issue isn't FASTCGI but for Python at least it is the deployment experience. Put simply, PHP provides a simple deployment path where as no one has really gone out of there way to provide a pre canned FASTCGI integration for WSGI which service providers can set up easily and make the users life better.  
  
To try and understand where the problems lie I will go through the setup required for running a Python WSGI script under mod\_fcgid, these days the preferred FASTCGI hosting solution for Apache. Unlike other blogs out there I am not just going to present the final recipe, but actually explain the pain points which people seem to encounter and why they arise.  
  
The FASTCGI Script  
  
In the case of Apache/mod\_wsgi, all a user need do is drop a WSGI script file into a directory and either map a URL to it using the WSGIScriptAlias directive, or have it automatically mapped to based on its file system location and extension mapping provided by the AddHandler directive. A simple hello world WSGI script file suitable for Apache/mod\_wsgi would be as follows.  


  


def application\(environ, start\_response\):

status = '200 OK'

output = 'Hello World\!'

response\_headers = \[\('Content-type', 'text/plain'\),

\('Content-Length', str\(len\(output\)\)\)\]

start\_response\(status, response\_headers\)

return \[output\]

  


Important to note here is that the WSGI script file only contains the WSGI application entry point which defines the programmatic API for communicating with the WSGI application. The WSGI script file does not say anything about how the WSGI application gets started or how requests are then passed off to it, this is the job of the hosting container \(mod\_wsgi\) to manage.  
  
In contrast, for mod\_fcgid, instead of a WSGI script file like above, it is necessary to provide an executable program. This program must start itself up and must have knowledge of how to communicate back to mod\_fcgid across a socket using the FASTCGI wire protocol.  
  
Now it would indeed be really painful if users had to implement this wire protocol themselves from scratch, but luckily they don't. There are actually a few Python packages available which implement an adapter bridging between the FASTCGI socket wire protocol and the programmatic WSGI application interface. The only one of these WSGI adapters for FASTCGI that seems to be used these days is [flup](http://trac.saddi.com/flup). Using flup, the above WSGI script file would be replaced with the following FASTCGI program.  
  


  


\#\!/usr/bin/env python

  


def application\(environ, start\_response\):

status = '200 OK'

output = 'Hello World\!'

response\_headers = \[\('Content-type', 'text/plain'\),

\('Content-Length', str\(len\(output\)\)\)\]

start\_response\(status, response\_headers\)

return \[output\]

  


if \_\_name\_\_ == '\_\_main\_\_':

from flup.server.fcgi import WSGIServer

WSGIServer\(application\).run\(\)

  


When this is executed as a program, \_\_name\_\_ will equate to '\_\_main\_\_' and so the flup WSGI server will be imported and started. The process will then stay persistent and handle the request which triggered it to be started and any subsequent requests.  


  


Seems simple enough, what can possibly go wrong.

  
Configuration And Startup  
  
Having loaded mod\_fcgid into Apache using:  
  


  


LoadModule fcgid\_module modules/mod\_fcgid.so  


  
you still need to tell Apache that the program must be processed by mod\_fcgid. This can be done in number of different ways. The most often used is to specify that any resource ending with a '.fcgi' extension should be handled by mod\_fcgid. This would be done using the AddHandler directive.  
  


  


<Directory /usr/local/www/htdocs>

Order deny, allow

Allow from All

AddHandler fcgid-script .fcgi

</Directory>  


  
So access control has been defined and the mapping for the extension is defined. Presuming that the directory corresponded to the DocumentRoot for the server and the FASTCGI program was called 'hello.fcgi', we would use the URL:  
  


  


http://localhost/hello.fcgi  


  
It fails though with the error in the browser of:  
  


  


Forbidden  


You don't have permission to access /hello.fcgi on this server.  


  
But we set access control so what can it be? In this case the problem is that being a script it is necessary to tell Apache that it is okay to be able to execute scripts out of that directory. To do this we need to turn on the ExecCGI option.  
  


  


<Directory /usr/local/www/htdocs>

Order deny, allow

Allow from All

Options ExecCGI

AddHandler fcgid-script .fcgi

</Directory>

  
This sort of setup would be done by the Apache administrator and for a shared hosting service they should know what is required and just get it right in the first place. So try again.  
  


  


Internal Server Error

The server encountered an internal error or misconfiguration and was unable to complete your request.

Please contact the server administrator, you@example.com and inform them of the time the error occurred, and anything you might have done that may have caused the error.

More information about this error may be available in the server error log.

  


At least this time we get an error in the Apache error logs.

  


\[info\] mod\_fcgid: server example.com:/usr/local/www/htdocs/hello.fcgi\(30887\) started

\[info\] mod\_fcgid: process /usr/local/www/htdocs/hello.fcgi\(30887\) exit\(communication error\), terminated by calling exit\(\), return code: 255

  


  
You have to remember though that on a shared hosting service a user isn't going to have access to the Apache error logs, all they will see is the message in the browser. It is possible they may have access to the error log for their own virtual host, but mod\_fcgid has a tendency to push such error messages to the main Apache error log and not that for the virtual host. Even then, if they do manage to get some one handling support for the hosting service to try and dig the message out of the Apache error logs, it is almost as unhelpful as that displayed in the browser.

  
One can start to see the frustration that people can experience.  
  
The cause of this cryptic error message in this case was the permissions on our actual FASTCGI program.  
  
  
8 -rw-r--r-- 1 graham admin 430 20 Sep 21:10 hello.fcgi  
  
Because it is going to be executed as a program, we need to ensure that it is executable. So we need to do:  
  
  
chmod +x hello.fcgi  
  
  


  


to yield:

  


8 -rwxr-xr-x 1 graham admin 430 20 Sep 21:10 hello.fcgi

  


Note here that I at least have made the file readable to others and the directories this is contained in is also readable to others. If this was not the case and the directory and/or files were not accessible/readable to the user that Apache runs as then you encounter even more errors. Lets quickly go back and revisit them.

  


If the directory the file is in isn't accessible to the user that Apache runs as, then you will get 'Forbidden' in the browser and in the Apache error logs you will get:

  


\[error\] \[client 127.0.0.1\] \(13\)Permission denied: access to /hello.fcgi denied

  


If instead the directory was accessible and the file was not readable to the Apache user, you will instead get 'Internal Server Error' in the browser and in the Apache error logs you will get:

  


\[warn\] \[client 127.0.0.1\] mod\_fcgid: error reading data, FastCGI server closed connection

\[error\] \[client 127.0.0.1\] Premature end of script headers: hello.fcgi

  


Is your head starting to hurt yet? And we haven't finished yet with all the things that can go wrong.

  


Anyway if you manage to get past all that, the 'python' executable was actually in the PATH and flup was actually installed into your Python installation then it will hopefully have worked.

  


The WSGI Adapter

  


As stated above, success will actually have depended on the flup package having been installed into the Python installation. What if it isn't? You will get 'Internal Server Error' in the browser and in the Apache error log you will get:

  


\[info\] mod\_fcgid: server fcgid-1.example.com:/usr/local/www/htdocs/hello.fcgi\(31130\) started

Traceback \(most recent call last\):

File "/usr/local/www/htdocs/hello.fcgi", line 19, in <module>

from flup.server.fcgi import WSGIServer

ImportError: No module named flup.server.fcgi

\[info\] mod\_fcgid: process /usr/local/www/hello.fcgi\(31130\) exit\(communication error\), terminated by calling exit\(\), return code: 1

  


I guess we at least got a traceback out of Python. Remember though, this is still in the Apache error log file and on a shared hosting service you are likely always going to have to go knock on the door of the support staff to get it. This will be the case even if flup was installed and you made the slightest syntactical error in the file which caused it not to run.

  


Input And Outputs

  


Now we did manage to get an error message above, even so, you are probably lucky to even get that message. This is because the FASTCGI specification says:

> The initial state of a FastCGI process is more spartan than the initial state of a CGI/1.1 process, because the FastCGI process doesn't begin life connected to anything. It doesn't have the conventional open files stdin, stdout, and stderr, and it doesn't receive much information through environment variables. The key piece of initial state in a FastCGI process is a listening socket, through which it accepts connections from a Web server.

> After a FastCGI process accepts a connection on its listening socket, the process executes a simple protocol to receive and send data. The protocol serves two purposes. First, the protocol multiplexes a single transport connection between several independent FastCGI requests. This supports applications that are able to process concurrent requests using event-driven or multi-threaded programming techniques. Second, within each request the protocol provides several independent data streams in each direction. This way, for instance, both stdout and stderr data pass over a single transport connection from the application to the Web server, rather than requiring separate pipes as with CGI/1.1.

Technically this means that prior to the point that you actually manage to start up the FASTCGI communications channel, there is no stderr or stdout. If a FASTCGI server sticks to the specification that error message likely wouldn't have any where to go and behaviour would be completely unpredictable. Most likely the process would just crash. Luckily mod\_fcgid preserves stderr, with stderr mapping into the Apache error log file.

  


What about stdout?

  


As it happens, mod\_fcgid also ignores the specification for stdout and it also maps to the Apache error log. There is a catch though in that stdout is buffered. If you therefore were to add 'print' statements into your code to try and generate debugging output to find out what is going on, they will appear not to even be written to the Apache error logs. For the messages to appear, stdout has to either be explicitly flushed, the buffer fill up, or the process cleanly exited.

  


So, if you are going to use print statements for debugging, then make sure you direct them to stderr and not the default of stdout. Better still, use the logging module and set up a logging handler to direct it to you own log file, one you can actually access and not be dependent on someone else to get stuff out of.

  


Finally there is stdin. Here the relevant part of the FASTCGI specification is:

> The Web server leaves a single file descriptor, FCGI\_LISTENSOCK\_FILENO, open when the application begins execution. This descriptor refers to a listening socket created by the Web server. 

> FCGI\_LISTENSOCK\_FILENO equals STDIN\_FILENO. The standard descriptors STDOUT\_FILENO and STDERR\_FILENO are closed when the application begins execution. A reliable method for an application to determine whether it was invoked using CGI or FastCGI is to call getpeername\(FCGI\_LISTENSOCK\_FILENO\), which returns -1 with errno set to ENOTCONN for a FastCGI application.

Remember above how it says that stdin doesn't exist, well guess what the file descriptor got replaced with. Yes, the socket over which FASTCGI communication occurs.

  


Okay, so you don't think you are touching stdin, so it isn't a problem. Think again. Various third party Python modules will actually perform checks on stdin to see whether it is a tty or has some other properties. Based on that the code may change its behaviour. You just want to hope those packages don't prod too deep, or are at least resilient to errors if they occur due to the underlying file descriptor actually being a socket connection and not a normal file object.

  


Is It A Lost Cause?

  


As you can see it isn't the most user friendly deployment system out there. Yet, PHP quite successfully makes use of FASTCGI for many deployments and they don't see to have to deal with these low level issues.

  


Part of the reason why PHP doesn't come to grief is the way it is packaged up such that all the important stuff is handled by the system administrators. The user therefore just needs to dump stuff in a directory and it works. If there are errors there are means of easily getting the details back in the browser or via their own log.

  


In contrast, with Python and trying to deploy a WSGI application, it is the user who has to worry about getting the FASTCGI process up and running with flup inside to bridge between the FASTCGI protocol and the WSGI application entry point.

  


FASTCGI environments though are what newbies or users who know nothing about setting this stuff up encounter due to chasing the cheapest hosting they can find. So the people who are least able to likely cope with it, are given what can be the worst thing to deal with if things go wrong.

  


Can it be done better? Sure it could. I have though had enough of fighting with bloggers handling of vertical whitespace for now, so that will have to wait until the next instalment.

---

## Comments

### Brandon Rhodes - October 3, 2011 at 8:51 AM

Once I figure out a recipe for deploying something, I often forget all of the errors and missteps that can occur along the way. Thanks for exactly the kind of reminder I often need: of the kinds of confusion, friction, and failure that make people reluctant to ever try deploying Python again if they are used to another environment and get into a series of problems like the ones you outline here.

### Ochoto - January 24, 2012 at 1:25 AM

You should check out uWSGI http://projects.unbit.it/uwsgi/ , it solves most, if not all, of these issues.

### Graham Dumpleton - January 24, 2012 at 4:36 PM

uWSGI is not the solution you may think it is. Existing web hosting companies have a lot invested in FASTCGI. They cannot just dump FASTCGI and replace it with uWSGI for all their existing use cases, ie., PHP. So, uWSGI may be a solution if starting from green fields, but trying to run it in parallel with an existing FASTCGI solution is likely just going to cause more problems than it worth and so unlikely to be adopted.

### Ochoto - January 25, 2012 at 9:50 PM

Graham, 3rd line from the uWSGI homepage says:  
  
"It uses the uwsgi \(all lowercase, already included by default in the Nginx and Cherokee releases\) protocol for all the networking/interprocess communications, but it can speak other protocols as well \(http, **fastcgi** , mongrel2...\)"  
  
I propose uWSGI as a fastcgi adapter, I find it more effective and simple to use in combination with Nginx which only needs a socket to talk to the fastcgi \(uWSGI\) process .

### Graham Dumpleton - January 26, 2012 at 12:02 AM

Large scale web hosting services do not use nginx or Cherokee but use Apache. They have huge amounts invested in Apache and the existing ways they run PHP with Apache. They are also dependent on modules like mod\_fcgid for handling FASTCGI process creation. So it is more than just being able to speak the FASTCGI protocol, automatic process management that ties in with Apache and its security mechanisms is also important.

### chort - February 13, 2012 at 7:38 PM

This comment has been removed by the author.

### Graham Dumpleton - February 13, 2012 at 8:28 PM

Sasha, I am not having a go at Python or WSGI, more the reliance of a specific old technology that hosting providers continue to use because of history. You might want to look at the bigger picture of my contribution to Python and WSGI hosting and my attempts to improve them to see that I definitely not against them. If I was I wouldn't be doing as much as I am. :-\)

