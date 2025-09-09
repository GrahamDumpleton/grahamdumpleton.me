---
title: "Google hates mod_wsgi."
author: "Graham Dumpleton"
date: "Sunday, October 14, 2007"
url: "http://blog.dscpl.com.au/2007/10/google-hates-modwsgi.html"
post_id: "6741538930156179499"
blog_id: "2363643920942057324"
tags: ['mod_wsgi']
comments: 8
published_timestamp: "2007-10-14T20:34:00+10:00"
blog_title: "Graham Dumpleton"
---

According to Google Analytics, 99% of all search engine traffic landing at the [mod\_wsgi](http://code.google.com/p/modwsgi/) site is via Google. As a consequence, the results are going to be pretty significant when Google, for no good reason that I can see, recently dropped the mod\_wsgi site home page from its search results. What makes even less sense is that mod\_wsgi is hosted on the Google Code hosting service.  
  
Hopefully the famed Google page rank algorithm will wake from its slumber at some point and start listing it again, otherwise it is going to make it hard for people to find the site. More worrying is that it looks like it might be starting to drop individual pages on the site as well, as searching for quite specific terms which appear within the site pages aren't showing up either, although they did previously.  
  
Is this Google's way of getting retribution on me for grumbling so much about how the search on Google groups has been stuffed up so often of late and is always quite far behind with its search results, or is it just symptomatic of the rot starting to set in at Google. :-\(

---

## Comments

### Lee - October 15, 2007 at 12:18 AM

what are you searching for? It comes up near the top for me.

### None - October 15, 2007 at 1:22 AM

Hm, for me it doesn't come up \(searching for "mod\_wsgi"\).

### Unknown - October 15, 2007 at 2:54 AM

Maybe this is the place to start? [Google webmaster tools](http://www.google.com/webmasters/)  
  
Otherwise I think there's a way to contact Google about it.  
  
Finally, why not ask all satisfied users to link to the page at the bottom of their mod\_wsgi powered sites? E.g., powered by Python and mod\_wsgi. I'll do it when my site is done. Google can't ignore hundreds of links.

### Doug Napoleone - October 15, 2007 at 3:00 AM

If you create a badge, I will add it to the PyCon website. I will add the text 'powered by mod\_wsgi' sometime today.

### Graham Dumpleton - October 15, 2007 at 9:31 AM

Although the page on www.dscpl.com.au comes up near the top when searching for 'mod\_wsgi', this isn't the actual mod\_wsgi site but just the original place holder on my own site which links to it. The actual location is 'http://code.google.com/p/modwsgi/'. There was also a permanent redirect from 'http://www.modwsgi.org/'. It was this which was at the top of the search results up until it vanished.  
  
I'll look at the web master tools but possibly will not be of much use as the site is controlled by Google Code hosting and they define the structure of the site. As such, it isn't really possible to add any special information into the site HTML or change the site structure.  
  
As to reporting what has occurred to Google, I tend to view them as a black hole these days so don't like my chances there. If it doesn't come back after a while I guess I will have no choice but to try that though.  
  
I like the idea of a badge to indicate 'Powered by mod\_wsgi'. I'll have to think about that one when I get some time.

### Graham Dumpleton - October 15, 2007 at 2:15 PM

Webmaster tools are useless as I suspected as there isn't any way with Google Code sites to insert the META tag or special page they want you to, which it can use to verify you are the owner. Thus, not possible to see more detailed analysis of the site. Same issue with trying to use a Sitemap file.  
  
What is interesting is that the webmaster tools show that Google Code site provides a robots.txt file which tells any search engines to go away. Thus, it warns ' Googlebot is blocked from http://code.google.com/p/modwsgi/  
'. Presumably the Googlebot ignores this for its own site or indexes it in some other way. If it doesn't, then someone screwed up.  
  
What is annoying though is that the robots.txt file for code.google.com is notionally going to stop other search engines from indexing the site. This means other search engines will not find stuff on the mod\_wsgi site either. If Google is going to be like this, seems the better option would be to move away from using Google Code altogether and host it elsewhere.  
  
So, we come to the question now of how one can actually contact Google so one might actually expect to get a response. Should one complain via Google Code forums why they are dropping their own sites from the Google index, should one query on the forums for the web master tools as to why it would get dropped or is there some other place. It isn't exactly obvious where one should chase things up.

### Unknown - October 16, 2007 at 9:08 AM

I guess you could always host a "front page" somewhere else which simply describes mod\_wsgi and points to the google code website.   
  
Then at least that page would get indexed normally.  
  
I'd reccomend https://www.nearlyfreespeech.net/  
for the hosting, since they charge by bandwidth. You could probably get by on a few dollars a year for a static page.

### Graham Dumpleton - October 16, 2007 at 9:19 AM

I have a happy ending to this.  
  
Just found a response from Google about this on one of the forums I was asking about it. See:  
  
http://groups.google.com/group/codesite-discuss/browse\_frm/thread/f5422cf7788c97ea  
  
In short, Google actually stuffed up a bit some infrastructure changes they made recently and wrongly installed a robots.txt file which blocked crawlers from the site when they shouldn't have.  
  
Seems I was the first to notice any problems with sites disappearing from the search results and then grumble loud enough about it.

