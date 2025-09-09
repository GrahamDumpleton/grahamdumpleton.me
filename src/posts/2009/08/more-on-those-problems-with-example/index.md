---
layout: post
title: "More on those problems with example web2py configurations for mod_wsgi."
author: "Graham Dumpleton"
date: "2009-08-21"
url: "http://blog.dscpl.com.au/2009/08/more-on-those-problems-with-example.html"
post_id: "216198985569117188"
blog_id: "2363643920942057324"
tags: ['mod_wsgi', 'python', 'web2py']
comments: 2
published_timestamp: "2009-08-21T20:39:00+10:00"
blog_title: "Graham Dumpleton"
---

In the [last post](/posts/2009/08/problems-with-example-web2py/) about web2py I covered the problems with the HTTP configuration for using [mod\_wsgi](http://www.modwsgi.org). This time will look at the combined HTTP/HTTPS configurations from the web2py book. The configuration in this case is as follows.
    
    
    1  ### for requests on port 80  
    2  NameVirtualHost *:80  
    3  <VirtualHost *:80>  
    4    ### set the servername  
    5    ServerName example.com  
    6    ### alias the location of applications (for static files)  
    7    Alias / /home/web2py/applications/  
    8    ### setup WSGI  
    9    WSGIScriptAlias / /home/web2py/wsgihandler.py  
    10   WSGIDaemonProcess web2py user=www-data group=www-data \  
    11     home=/home/web2py/ \  
    12     processes=10 maximum-requests=500  
    13     ### admin requires SSL  
    14   <Location "/admin">  
    15     SSLRequireSSL  
    16   </Location>  
    17   ### appadmin requires SSL  
    18   <LocationMatch "ˆ(/[\w_]*/appadmin/.*)">  
    19     SSLRequireSSL  
    20   </LocationMatch>  
    21   ### static files do not need WSGI  
    22   <LocationMatch "ˆ(/[\w_]*/static/.*)">  
    23     Order Allow,Deny  
    24     Allow from all  
    25   </LocationMatch>  
    26   ### everything else goes over WSGI  
    27   <Location "/">  
    28     Order deny,allow  
    29     Allow from all  
    30     WSGIProcessGroup web2py  
    31   </Location>  
    32   LogFormat "%h %l %u %t \"%r\" %>s %b" common  
    33   CustomLog /var/log/apache2/access.log common  
    34 </VirtualHost>  
    35 ### for requests via SSL (port 443) enable SSL  
    36 NameVirtualHost *:443  
    37 <VirtualHost *:443>  
    38   ServerName example.com  
    39   Alias / /home/web2py/applications/  
    40   WSGIScriptAlias / /home/web2py/wsgihandler.py  
    41   WSGIDaemonProcess web2py user=www-data group=www-data \  
    42     home=/home/web2py/ \  
    43     processes=10 maximum-requests=500  
    44   SSLEngine On  
    45   SSLCertificateFile /etc/apache2/ssl/server.crt  
    46   SSLCertificateKeyFile /etc/apache2/ssl/server.key  
    47   <LocationMatch "ˆ(/[\w_]*/static/.*)">  
    48     Order Allow,Deny  
    49     Allow from all  
    50   </Location>  
    51   <Location "/">  
    52     Order deny,allow  
    53     Allow from all  
    54     WSGIProcessGroup web2py  
    55   </Location>>  
    56   LogFormat "%h %l %u %t \"%r\" %>s %b" common  
    57   CustomLog /var/log/apache2/access.log common  
    58 </VirtualHost> 

As already stated in the last post, this has all the same problems as for the HTTP only configuration. Because a separate VirtualHost is used for HTTP and HTTPS, the problems are actually duplicated and occur in each VirtualHost. I will not cover all that again, so ensure you read the [last post](/posts/2009/08/problems-with-example-web2py/).

  


On top of those problems, the HTTPS configuration contains an additional mistake, this time in how mod\_wsgi is used.

  


The mistake here is having a second WSGIDaemonProcess directive at line 41. Doing this will fail because the same daemon process group name of 'web2py' was used as the first argument to the directive, as was used in the WSGIDaemonProcess directive at line 10. The mod\_wsgi module will reject this, as the names for daemon process groups must be unique no matter what context they are placed in.

  


The first thought might be just to change the name as well as the reference to it in the WSGIProcessGroup directive at line 54. Although this will work, it does mean you then have a second daemon process group containing another 10 processes just for handling the HTTPS requests. As I already explained, the number of processes/threads was excessive and doing that would just make the problem twice as bad.

  


What one really wants is for both HTTP and HTTPS requests to use the same daemon process group. There are two ways one could achieve this.

  


The first is to delete the WSGIDaemonProcess directive at line 41 and move the WSGIDaemonProcess directive at line 10 outside of both VirtualHost definitions. In other words, it is placed at global scope within the Apache configuration. By doing this, WSGI applications within any VirtualHost, regardless of ServerName, could be delegated to that daemon process group.

  


If this your own system and you aren't hosting sites for other users, doing it this way is likely acceptable. If you want a slightly more secure configuration, you should still delete the WSGIDaemonProcess directive at line 41, but leave that at line 10 in place.

  


What is being relied upon in that case is that mod\_wsgi will allow you to reference using the WSGIProcessGroup directive, a daemon process group specified in the context of another VirtualHost, so long as the ServerName for the VirtualHost is the same.

  


This is a bit safer, because having the WSGIDaemonProcess directive within the VirtualHost means you can't accidentally delegate a WSGI application to it from a VirtualHost for a different ServerName set up for a different user.

  


Which ever of the two methods is used, there is another subtlety at play in what is happening that is important to point out. This is that by default mod\_wsgi will separate WSGI applications such that they run in distinct sub interpreters of the process they run in. The name of the sub interpreter is derived from ServerName, the port for the VirtualHost and the mount point of the application.

  


Normally this rule for deriving the name of the sub interpreter would actually mean that since HTTP and HTTPS connections are received on different ports, that there would still be two instances of the WSGI application in each process and thus twice as much memory used. Because though ports 80 and 443 are generally paired together for a site, mod\_wsgi makes an exception in this case and will actually assign requests for the WSGI application through either port to run in the same sub interpreter. Thus, only one instance of the application in each process.

  


If for some reason this was a big issue, then you could go back to using two distinctly named daemon process groups. Alternatively, you could use the WSGIApplicationGroup directive to control the name of the sub interpreter each is assigned to. This would see them run together in the same process, but in different sub interpreters with names you designate.

  


So, that is it for the problems with the configuration that is doing the rounds for web2py and mod\_wsgi. In summary, it will not work. Even if you drop the Alias directive so the web2py application receives requests, the use of Location and LocationMatch to control access to URLs is dangerous. On top of that, for the combined HTTP/HTTPS configuration, Apache wouldn't have even started up as mod\_wsgi would have complained about the daemon process group names not being unique.

  


I'll give details of a working configuration for running web2py on top of mod\_wsgi later when I get some more time.

---

## Comments

### Max - August 30, 2009 at 12:06 AM

A new web2py book is out. The new book contains a revised version of the script written by Graham. Thank you Graham.

### Javi - June 25, 2012 at 6:53 PM

Many thanks, this solved my problem installing web2py in production with SSL. You are so generous sharing your knowledge. Thanks Thanks and Thanks...

