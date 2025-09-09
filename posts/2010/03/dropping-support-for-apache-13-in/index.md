---
title: "Dropping support for Apache 1.3 in mod_wsgi."
author: "Graham Dumpleton"
date: "Thursday, March 11, 2010"
url: "http://blog.dscpl.com.au/2010/03/dropping-support-for-apache-13-in.html"
post_id: "6896258104625739306"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python']
comments: 1
published_timestamp: "2010-03-11T21:32:00+11:00"
blog_title: "Graham Dumpleton"
---

The Apache Software Foundation has finally [put Apache 1.3 out to pasture](http://www.apache.org/dist/httpd/Announcement1.3.html). This has been a long time coming and quite overdue in my mind. Even though Apache 1.3 is quite antiquated, mod\_wsgi has continued supporting it at the same time as supporting newer versions of Apache. For the record, mod\_python gave up supporting Apache 1.3 about six years ago, but then, mod\_python hasn't seen a release in three years and development on it is arguably dead at this point.

  


With this decision having been made by the ASF, it is a good time to consider whether it is necessary to keep trying to support Apache 1.3 in newer versions of mod\_wsgi.

  


In making this decision, one has to consider that when running mod\_wsgi under Apache 1.3 only embedded mode is supported, it is not possible to use daemon mode. Further, all the significant changes in most recent versions of mod\_wsgi have related to daemon mode. In fact, there isn't really anything else in the way of functionality that could be added which relates to embedded mode which would provide anything above what can currently be done when using Apache 1.3.

  


As such, I can't see any reason for continuing to provide support for Apache 1.3 in future versions of mod\_wsgi. This doesn't mean you cant use mod\_wsgi with Apache 1.3, just that you would be directed to use whatever is the latest from the mod\_wsgi 3.X branch.

  


Will users of Apache 1.3 loose out by such a decision? I somewhat doubt it. At this point mod\_wsgi has shown itself to be very stable, more so when embedded mode is used, and certainly more stable than mod\_python ever was. Anyway, if some major issue did ever come up which a user/company really wanted fixing, then I am not going to ignore it if they are prepared to throw money my way. ;-\)

  


So, before I make the final decision and wield the axe to extricate the code specific to Apache 1.3 from mod\_wsgi, does any one have any valid objections, or alternatively, comments in support of such a move?

---

## Comments

### Dirkjan Ochtman - March 12, 2010 at 1:43 AM

Yes, yes, yes. Please wield out all support for 1.3 from all future releases.

