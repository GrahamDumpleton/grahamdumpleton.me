---
title: "What is the current version of mod_wsgi?"
author: "Graham Dumpleton"
date: "Tuesday, September 2, 2014"
url: "http://blog.dscpl.com.au/2014/09/what-is-current-version-of-modwsgi.html"
post_id: "524931427235304285"
blog_id: "2363643920942057324"
tags: ['apache', 'mod_wsgi', 'python', 'wsgi']
comments: 0
published_timestamp: "2014-09-02T02:20:00+10:00"
blog_title: "Graham Dumpleton"
---

If you pick up any Linux distribution, you will most likely come to the conclusion that the newest version of mod\_wsgi available is 3.3 or 3.4. Check when those versions were released and you will find:

  * mod\_wsgi version 3.3 - released 25th July 2010
  * mod\_wsgi version 3.4 - released 22nd August 2012



Problem is that people look at that and seeing that there are only infrequent releases and nothing recently, they think that mod\_wsgi is no longer being developed or supported. I have even seen such comments to the effect of 'mod\_wsgi is dead, use XYZ instead'.

From the perspective of someone who develops Open Source, the inclusion of out of date package versions on Linux distributions has always been a right pain in the neck.

Because of these older versions present in Linux LTS versions, you can't as easily update the documentation to ignore older ways of doing things and instead focus on just the new and better ways.

You are constantly having to deal with users who refuse to upgrade because they worship at the alter of these DEB or RPM gods.

That and users who believe you only exist to help them is why I got so miffed about Open Source and why the releases became fewer and farther in between in the first place. What was the point of providing updated versions with lots of new stuff if they weren't going to be used anyway.

For many Open Source packages you might not actually get away with such infrequent releases, but because mod\_wsgi served one specific purpose and did it very well, there wasn't a great need to be updating it anyway. Where updates were necessary, it tended to revolve around changes in newer versions of Python and Apache. The mod\_wsgi code itself was stable and reliable enough that it just kept on working with no issues.

In my hallway track discussions at DjangoCon US 2014, this issue of mod\_wsgi versions came up. There was actually some surprise that there were actually newer versions than those listed above.

I will not list all the newer versions than 3.4, but some key versions are:

  * mod\_wsgi version 3.5 - released 20th May 2014 \([security release](http://blog.dscpl.com.au/2014/05/security-release-for-modwsgi-version-35.html)\)
  * mod\_wsgi version 4.0 - never released
  * mod\_wsgi version 4.1.0 - released 23rd May 2014
  * mod\_wsgi version 4.1.3 - released 3rd June 2014
  * mod\_wsgi version 4.2.0 - released 8th June 2014
  * mod\_wsgi version 4.2.8 - released 22nd August 2014
  * mod\_wsgi version 4.3.0 - working on it



When you look back at the full release history, from the first official version ever released on the 5th September 2007 up to when version 3.5 was released, but not including version 3.5, you get 21 releases in a period of 6 1/2 years.

Not exactly a lot of releases and it definitely slowed down in the last 4 years of that with only 2 releases.

Contrast that to the period of time from version 3.5 up till now. In that short time of a bit over 3 months there have been 14 releases. I even switched to a 3 digit version numbering scheme from a 2 digit number scheme precisely so I felt no impediment to making new releases.

So mod\_wsgi was resting there for quite a while, but it isn't the dead parrot from the Monty Python skit, it is definitely alive and kicking.

Given there has been so many versions released of late, you might think you would have seen more said about them. I have made a few noises on Twitter and the mod\_wsgi mailing list, but in the main I have indeed been rather quiet about them.

The reason I have been quiet is that I have returned to working on mod\_wsgi for the enjoyment of it. I don't really care if no one wants to use the newer features right now and am more than happy to just use it as a means to explore my ideas for what makes a good deployment system for Python WSGI applications.

If you want to try and work out what I have been working on, for now I would suggest you read the documentation on the mod\_wsgi package entry on [PyPi](https://pypi.python.org/pypi/mod_wsgi). For lower level details of specific changes, see the [release notes](http://modwsgi.readthedocs.org/en/latest/release-notes/index.html). Otherwise, keep an eye here on my blog as what I am working on has been a topic of discussion at DjangoCon as well, which means I will have to explain something about the newer versions if I am to keep reporting on my DjangoCon hallway track discussions as planned.