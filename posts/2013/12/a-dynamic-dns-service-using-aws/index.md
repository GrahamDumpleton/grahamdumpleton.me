---
title: "A dynamic DNS service using AWS Route53/S3 and Heroku."
author: "Graham Dumpleton"
date: "Monday, December 2, 2013"
url: "http://blog.dscpl.com.au/2013/12/a-dynamic-dns-service-using-aws.html"
post_id: "3681351111058400567"
blog_id: "2363643920942057324"
tags: ['new relic', 'python']
images: ['DynamicDNSServiceSampleTransaction.jpg']
comments: 1
published_timestamp: "2013-12-02T13:06:00+11:00"
blog_title: "Graham Dumpleton"
---

It has been almost a year since I posted something on my personal blog, with work and home life just taking over all my free time. I can also relate very much to comments made recently by Armin Ronacher on his [blog](http://lucumr.pocoo.org/2013/11/28/emotional-programming/) which effectively amounted to the fact that when work is more interesting than your Open Source projects, that it is inevitable that Open Source projects will lose out. This is especially the case where the Open Source project meets your own requirements or has satisfied whatever curiosity you had to work in that area in the first place.  
  
It is for this exact reason that my own Apache/mod\_wsgi project hasn't exactly been getting much attention of late. It does what is was designed to do. It works and it is stable. It may well not be the latest cool thing there is out there, but right now if users want to go off and use something which is still rapidly developing, is growing into areas way outside of the core functionality you need, and is no where near as stable, it isn't going to bother me one bit. Those sorts of users are generally the ones who never learnt enough about how to setup Apache/mod\_wsgi properly in the first place to make the most of it. As such they were often more of a burden when it came to support.  
  
Anyway, when it does come to working on stuff outside of what I do at work, right now it is generally things which I need to meet a specific requirement, spark my interest or which just seem like something fun to work on for a bit.  
  
Such it was that recently I sat down and went and wrote a dynamic DNS service. This came about because of some issues I had with the ISP which hosted an old site of mine which I have been meaning to move for quite some time. They started to break inbound email and also stop propagating DNS configuration. I had therefore to move some stuff off of the site quite quickly.  
  
To resolve the DNS issues I started looking around for cheap and/or free services which would manage my DNS domains. I could have simply used the DNS management services of my registrars, but one of those wanted extra money each year and I didn't really want to be beholden to them for it anyway.  
  
One option was dyndns.org, which I had used in the past for dynamic DNS services, but they got rid of their free service for dynamic DNS a while ago and although as an existing user you can keep it, you are required to now manually log into their web site each month or loose it. They also recently said they will now start sending you emails every fortnight to remind you to login, or as it is in reality, to nag you to cough up money for their paid service.  
  
After some research I ended up settling on Route 53 from Amazon Web Services for DNS management services. This would cost me a small amount of money each month, but then I still had unused credit from an AWS voucher which would cover that until the credit expired. It wasn't therefore going to cost me anything to try it out for a while.  
  
While I was at it I thought I may as well work out how I could get rid of my dependence on dyndns.org for dynamic DNS, although to be honest, I wasn't actually really making use of it for anything I couldn't do without.  
  
In my search I did find a Python script which used the Python 'boto' module to update Route 53 with the details of a changing IP address, but it had to be run from a system within your home network, either manually or from cron. Unless you had this running quite frequently though, a change in the IP assigned to your ADSL/cable modem may not be picked up very quickly. As my modem supported automatic registration against dynamic DNS services and would register an IP change straight away, I would have preferred to use that.  
  
Further research did find some Open Source implementations of dynamic DNS services you could run up on a VPS and point your modem at that, but they were often PHP scripts and were bound to some obscure DNS server which you also had to run yourself, which is exactly what I didn't want. There had to be a better way.  
  
After some playing, what I ended up doing was write my own little dynamic DNS service using Python and Flask and hosted it up on Heroku. Because I wasn't using Heroku for anything else, hosting it there wouldn't cost me anything as I was within the bounds of what can be run for free.  
  
I could now point my modem at this personal dynamic DNS service running on Heroku. When it got the registration request, it would use 'boto' to contact the AWS Route 53 service and automatically update the IP address assignment for a host name within my existing personal domain.  
  
So that the dynamic DNS service wasn't hard wired to my specific host and domain information, I decided to generalise it and use AWS S3 to store a simple database file containing details of the hosts it supported, along with a unique authentication token for each. That way I could easily support more than one dynamic DNS client mapping to different host names if I ever needed it.  
  
Now as with other stuff I write, I like to share it as Open Source when I can, so I have put up all the code for this dynamic DNS service on my github account. You can find it at:  
  


  * <https://github.com/GrahamDumpleton/dyndns53>



You will need to work out yourself how to get Heroku, AWS Route 53 and S3 set up, but do your homework on that and the documentation should be enough to get things setup.

  


Finally, one of the reasons I was actually interested in doing this, is that I needed a practical example of using the 'boto' module for Python. This was so I could use it in working out instrumentation for the 'boto' module as part of my job at [New Relic](http://www.newrelic.com/) in working on web application performance monitoring tools.

  


If you dig around in the code you will therefore also find how I hooked New Relic into it to monitor it. This specific web application, because it is only very infrequently accessed, isn't going to show much, but the application specific and 'boto' instrumentation does yield some cute sample transaction traces for when a request does come in. Even on this small application it gave an interesting insight into what was going on and how much time was being spent in talking to Amazon Web Services for Route 53 and S3.

  


[![](DynamicDNSServiceSampleTransaction.jpg)](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjx1x5Ubq2D9IU1niqwtqipLJLXpy5cMz0LxfL17c3THYZUlAL7mbr_tV0L0dFJqv-trUPXbOYEvs9Q5FUSYgJvC090_Tu9i-hM9LNIfFkCvfu6OI8ovTt8bRhhxNiSuAo-qll4voxf1neO/s1600/DynamicDNSServiceSampleTransaction.jpg)

  


If you are specifically interested in building on New Relic's Python instrumentation as I did for this web application, keep an eye out on the New Relic [blog](http://blog.newrelic.com/) as I hope to say more about that in the coming months there.

---

## Comments

### Unknown - December 2, 2013 at 8:04 PM

I built something similar using PowerDNS and Python. I also didn't want to poll for the IP change, so I set the router up to syslog onto a machine on the network and had a little script watch the log... hacky, but it works :\)

