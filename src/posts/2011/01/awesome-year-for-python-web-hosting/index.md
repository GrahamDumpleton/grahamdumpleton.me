---
layout: post
title: "An awesome year for Python web hosting."
author: "Graham Dumpleton"
date: "2011-01-28"
url: "http://blog.dscpl.com.au/2011/01/awesome-year-for-python-web-hosting.html"
post_id: "1307472191905754814"
blog_id: "2363643920942057324"
tags: ['python', 'wsgi']
comments: 9
published_timestamp: "2011-01-28T09:16:00+11:00"
blog_title: "Graham Dumpleton"
---

This year is shaping up to be an awesome year for Python web hosting. Not only do we have existing reliable providers like [WebFaction](http://www.webfaction.com/), but we now also have a gaggle of Python specific web hosting services coming online. So many that one can easily start loosing track of who they are. As such, doing this post to list those that I know of. Are there any more that people know of that are just starting up?  


  


The new contenders that I know of are as follows:

  * [ep.io](http://www.ep.io/)
  * [gondor.io](http://gondor.io/)
  * [djangozoom.com](http://djangozoom.com/)
  * [stable.io](http://stable.io/)
  * [djangy.com](https://www.djangy.com/)
  * [pydra.com](http://pydra.com/)
  * [apphosted.com](https://apphosted.com/)



What will be even more awesome will be to see these teamed up with production monitoring tools like those from [NewRelic](http://www.newrelic.com/). NewRelic has been building relationships with hosting services for other languages they already support, which provide people who sign up with that hosting service free access to their [Bronze level subscription](http://www.newrelic.com/web-app-monitoring-pricing.html). The latest of these announced was for a [PHP web hosting service](http://blog.newrelic.com/2011/01/25/php-fog-offers-free-new-relic-rpm/). So, imagine how things will be if this sort of tool becomes available for the Python web community. As I say, looking to be an awesome year for Python web hosting.

  


And yes, some will say this is just an unashamed blatant plug for NewRelic just because I am working there now. Seriously though, I reckon this influx of new Python web hosting services, and the monitoring tools to match, is going to be a really great thing for the Python web community. I know I have not been this excited about something for a very very long time. :-\)

---

## Comments

### Graham Dumpleton - January 28, 2011 at 7:34 PM

Please note that comments are being moderated. Links advertising existing old school web hosting services, ie., those who provide servers for PHP, Python or arbitrary FASTCGI applications will not be posted. Am only interested in knowing about these new Heroku style of services which are starting to become available and which are specifically dedicated to Python and which are normally using git/mercurial push for automatic deployment to a black box infrastructure and not systems which give you shell or cPanel type access.

### নাসিম - January 29, 2011 at 1:26 AM

Why did you avoid Google Appengine? What are the reasons?

### Graham Dumpleton - January 29, 2011 at 1:49 PM

Google App Engine was not mentioned because it has been around for ages. The point of the post was to highlight the 'NEW' kids on the block. It is not meant to be a catalogue of everything that is available.  
  
An important distinction with the new offerings is that they offer up conventional database systems and you aren't forced into using some special purpose database. The new systems also tend to use tools such as git/mercurial to push changes and deploy. This is the style of system am looking at.

### jfischer - January 30, 2011 at 9:17 AM

Hi, we have a startup called [genForma](http://www.genforma.com) building a Django application service. It will allow easy deployment to the cloud from your development environment and will use standard components. We'll be starting our private beta in the next few weeks and plan to open source our underlying platform.  
  
\- Jeff

### Graham Dumpleton - February 28, 2011 at 11:31 AM

Seems that djangy.com is shutting down even before it makes it out of private beta. http://blog.djangy.com/2011/02/27/final-djangy-newsletter/

### Unknown - March 15, 2011 at 3:46 AM

Another private beta Django and Python hosting platform: [30loops](http://30loops.net)

### Graham Dumpleton - March 16, 2011 at 3:21 AM

Yet another one. http://nuagehq.com/

### Graham Dumpleton - May 6, 2011 at 9:04 AM

ActivateState has finally announced they are entering this area.  
  
http://www.activestate.com/blog/2011/05/stackato-platform-python-and-perl-cloud  
  
I have known about this one for a little but since they hadn't gone public couldn't say anything.  
  
Use of CloudFoundry is interesting and if the addition of Python support has been fed back into the CloudFoundry project then could open up option for VMWare themselves to support Python in their commercial offering as well.  
  
Worth pointing out though is that these companies have a focus on using isolated host instances if I understand it correctly and not shared like with existing services. So it isn't necessarily the same market as the existing providers.

### Harry - January 15, 2013 at 1:08 AM

May I plug our own offering? [PythonAnywhere](http://www.pythonanywhere.com) offers free hosting for Python web apps, plus all sorts of browser-based dev tools. Drop in and tell us what you think via the big feedback button\!

