---
title: "Problems with example web2py configurations for mod_wsgi."
author: "Graham Dumpleton"
date: "Thursday, August 20, 2009"
url: "http://blog.dscpl.com.au/2009/08/problems-with-example-web2py.html"
post_id: "8404916280431179570"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'web2py']
comments: 1
published_timestamp: "2009-08-20T15:26:00+10:00"
blog_title: "Graham Dumpleton"
---

I get really annoyed when I see instructions for how to use mod\_wsgi which are wrong. Normally I will post a followup or comment to whatever forum or blog the information is on, but for some web applications/frameworks I haven't done that in the past as I simply haven't had the time to sit down and work out how it should be done properly for that specific package. This has been the case for web2py and I have probably pissed off a few people by simply warning them that the configuration is broken and in part compromising the security of their system, but then not telling them how they can fix it nor what was really wrong with it in the first place.

  


I still don't get much free time these days, but a couple of weeks back I did finally find a little bit of time to work out a way of getting web2py working properly on mod\_wsgi and which satisfied my criteria as far as doing it the correct and most secure way. Before I get on to that though, I want to highlight what was wrong with the configurations that were being published for using web2py on top of mod\_wsgi as it is a good example of the many ways people who don't know how to use Apache can stuff things up.

  


Not necessarily the original source of the broken configuration, but the web2py book sample paragraphs available at this time lists the following as configuration for HTTP only configuration:
    
    
```
1  ### for requests on port 80  
2  NameVirtualHost*:80  
3  <virualhost *:80>  
4    ### set the servername  
5    ServerName example.com  
6    ### alias the location of applications (for static files)  
7    Alias / /home/web2py/applications/  
8    ### setup WSGI  
9    WSGIScriptAlias / /home/web2py/wsgihandler.py  
10   WSGIDaemonProcess web2py user=www-data group=www-data \  
11     home=/home/web2py/ \  
12     processes=10 maximum-requests=500  
13   ### static files do not need WSGI  
14   <locationmatch "ˆ(/[\w_]*/static/.*)">  
15     Order Allow,Deny  
16     Allow from all  
17   <locationmatch>  
18   ### everything else goes over WSGI  
19   <location "/">  
20     Order deny,allow  
21     Allow from all  
22     WSGIProcessGroup web2py  
23   </location>  
24   LogFormat "%h %l %u %t \"%r\" %>s %b" common  
25   CustomLog /var/log/apache2/access.log common  
26 </virtualhost>  
```
    

There are four principal things that are being attempted here. These are:

  1. Map the web2py instance at the root of the web server.
  2. Map the static files for the web2py applications so they are served via Apache not by web2py. The intent being to get better performance in doing so.
  3. Tell Apache that it is allowed to host a WSGI application from the web2py WSGI script file.
  4. Tell Apache that it is allowed to host the static files for the WSGI applications.
  5. Delegate web2py instance to run in a separate daemon process.



To achieve \(1\), the WSGIScriptAlias at line 9 is used and that isn't too hard. The problem is that as simple is that is, it doesn't work in this configuration. The reason for this is that when using mod\_wsgi an Alias directive in Apache will take precedence over WSGIScriptAlias, irrespective of the ordering of the directives in the configuration file. This is done to allow overlaying of static files on top of a mounted WSGI application. That is, have static files appear at what would be a sub URL of the WSGI application. In this configuration, because the Alias directive at line 7 was also set for '/', it completely overrides the WSGIScriptAlias directive and requests would never get passed through to the web2py instance and only the mapped static files would be accessible.

  


Okay, so if all requests go through to static files, you might therefore think that at least \(2\) has been achieved. Well, it does, but the way it does has other implications. The problem here is that the web2py applications directory doesn't hold just the static files that you want to be able to serve via the web server, it also hosts Python code files specific to applications, along with database files and upload directories. In short, there is also a lot of application code and data stored under their. By mapping the whole of the web2py applications directory, that has all been made accessible which is a tad bit insecure to say the least. Luckily it would probably not get left that way for long since use of the Alias directive for '/' would have meant the web2py instance wouldn't have been accessible anyway and chances are that people would remove the Alias directive and find it then worked and so left it disabled. Does mean though, that static files aren't being served by Apache but by web2py which will be a lot slower.

  


Now, there is actually a possible attempt to restrict access to just the static files with the LocationMatch directive at line 14 and the default Deny rule at line 15, but this doesn't do anything. First off because the Allow rule at 16 overrides that, secondly because the default Deny rule only applies to the static locations and not the stuff outside of that, which is the real problem, and because the Location directive at line 19 will likely override it all anyway depending on how Apache deals with ordering of Location directives.

  


That said, that the Location and LocationMatch directives are allowing everything through does in effect mean that \(3\) and \(4\) are satisfied, but that access control is done based on URL rather that file system directories is in itself a security problem.

  


Under normal circumstances the setting up of access controls as to what files in the file system can be accessed would be done inside of Directory and/or DirectoryMatch directives and not Location or LocationMatch directives. One would only really use Location and LocationMatch where for specific URLs you might want to implement further restrictions, rather than opening up access where underlying access controls are more strict.

  


The overall principal therefore is that you deny access to the whole file system and then only allow access to specific parts of the file system that need to be accessed. The directives in main Apache configuration file that enforce this are:
    
    
```
<Directory />  
Options FollowSymLinks  
AllowOverride None  
Order deny,allow  
Deny from all  
</Directory>
```

  


The use of a Location directive for '/' at line 19 around the Allow directive at line 21 overrides that whole security mechanism though and says that what ever the URL is and no matter what part of the file system it maps to, that we will allow Apache to access it. This means that if an errant rewrite rule mapped a URL to wrong part of file system, or if a user had a symbolic link under the web2py application directory pointing at somewhere outside of that part of the file system, such as '/etc', then what ever file was mapped to could be retrieved by a remote user.  
  
It should also be noted that using Location directive for '/' is a bit silly anyway as '/' is the default context for the VirtualHost directive. Thus, the Location directive for '/' is redundant and the contained directives could have been placed at top level context under the VirtualHost directive and result would have been the same.  
  
Anyway, it is highly recommended that you never use 'Allow from all' inside of a Location or LocationMatch directive. Always use Directory and/or DirectoryMatch for specifying the access control directives that are opening up access to Apache to serve files.  
  
Next issue is that to satisfy \(5\), the WSGIDaemonProcess directive at line 10 was specified. To delegate the web2py instance to run in that daemon process group, the WSGIProcessGroup directive at line 22 was used. As already pointed out above though, the use of a Location directive for '/' is redundant and so that should have just been placed at top level context under VirtualHost directive.  
  
As for the options to the WSGIDaemonProcess directive, the user and group options shown are redundant because the listed user and group are what Apache runs as anyway. In other words, if you want to have the daemon process run as same user as Apache, there is no need to specify the options.  
  
The option for processes is also questionable. This is because the default number of threads per daemon process is 15. With 10 processes, this means that theoretically you have the capacity for 150 concurrent requests. I'd suggest that much much less than that would be required by your typical Python web application. Thus, specifying that many in an example configuration isn't really appropriate. I would start out with 2 processes at most and work from there.  
  
The maximum requests option is another option which is probably not advisable in an example configuration. Overall this option is only really needed if a web application has a problem with leaking Python objects, through inability to be garbage collected, or general memory leaks. If web2py doesn't have those problems, there is no sense using that option. Leaving it out means you will not incurr periodic restarts and reloading of the whole web2py instance.  
  
That covers all the problems with the example for serving up via HTTP. All these issues also exist in the example in the web2py book for HTTPS, but the HTTPS example also has other mistakes in it as well. I've had enough of this for today though, so I'll cover the HTTPS configuration problems and supply a working configuration in other posts.  
  
BTW, Massimo has been supplied the working configuration for inclusion in future update of his book, although I will possibly suggest he make a couple of more tweaks to what he was given.

---

## Comments

### Max - August 30, 2009 at 12:21 AM

A new web2py book is out on lulu.com. The new book contains a revised version of the wsgi script, written by Graham. Thank you Graham.

