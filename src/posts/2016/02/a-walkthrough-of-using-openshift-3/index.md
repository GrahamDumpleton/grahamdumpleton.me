---
layout: post
title: "A walkthrough of using OpenShift 3."
author: "Graham Dumpleton"
date: "2016-02-24"
url: "http://blog.dscpl.com.au/2016/02/a-walkthrough-of-using-openshift-3.html"
post_id: "7488826685869340461"
blog_id: "2363643920942057324"
tags: ['docker', 'kubernetes', 'openshift']
comments: 0
published_timestamp: "2016-02-24T12:56:00+11:00"
blog_title: "Graham Dumpleton"
---

Since starting with Red Hat on the OpenShift project, I have written various blogs posts here on my own site but they were mainly related to Docker. They still had some relevance to OpenShift as they talked about how to [construct Docker images properly](/posts/2016/01/roundup-of-docker-issues-when-hosting/) so that they will work under the more stringent security requirements imposed by a multi tenant hosting service using Docker, such as OpenShift. What I haven’t tackled head on is what it is like to use OpenShift, what role it is providing and why the Python community would be interested in it.

On that front, Grant Shipley, who is also on the OpenShift team, has just saved me a whole lot of work by posting a really good video walk through of using OpenShift 3. The blog post introducing the video can be found on the [OpenShift blog](https://blog.openshift.com/openshift-3-walkthrough/), but I have embedded the video here for quick viewing as well. If at all interested in deploying web applications to a PaaS like environment, it is well worth a watch to understand, from a developer perspective, where OpenShift is headed, how it can very simply be used to host your web applications using provided images, or how you can run your own Docker images.

If you want to play around with OpenShift yourself, the easiest way is to use the [All-In-One VM image for Vagrant](https://www.openshift.org/vm/).

The All-In-One image is what Grant uses in the video and allows you to run up OpenShift on your own laptop or desktop PC. The image is based on the Open Source upstream project for Red Hat’s own product. The upstream project is called OpenShift Origin.

If you like what you see with OpenShift and want to experiment further on some real hosts, you can [install OpenShift Origin](https://github.com/openshift/origin) yourself onto your own physical infrastructure or using an IaaS provider using an easy to run Ansible script.

Being the upstream project, OpenShift Origin is the community supported variant of OpenShift. If you want to run OpenShift and are after all the support that comes with using a Red Hat product, including Red Hat being the one place to call for all the issues you may experience with the product, then you have a couple of options at present.

The first is [OpenShift Enterprise](https://www.openshift.com/enterprise/). This supported variant of OpenShift can also be installed on your own physical infrastructure or using an IaaS provider. Rather not install and manage it yourself and instead have Red Hat look after it for you, the current option is [OpenShift Dedicated](https://www.openshift.com/dedicated/). This provides you with your own OpenShift environment running on an IaaS provider, but Red Hat will install it and look after it. You still don’t share OpenShift with anyone else with this option so can use the full resources however you want.

The option which I know many who might be reading this in the Python community are going to be more interested in is OpenShift Online. Unfortunately the current OpenShift online is still using the prior OpenShift 2 and not OpenShift 3. It therefore still hasn’t switched to using Docker and Kubernetes as yet.

OpenShift Online is definitely coming though. Creating a full on public PaaS which is multi tenant and provides the security and performance that users expect is no simple undertaking and Red Hat wants to get it right. OpenShift Online therefore needs a bit more time baking in the oven before it is going to be ready.

All the complexities in creating a PaaS is something that I have only myself come to better appreciate after having seeing the effort going into OpenShift 3. If you have tried to create a DIY PaaS on top of Docker or a so called container as a service \(CaaS\) product, you will no doubt be aware of some of the traps and pitfalls with trying to do it yourself. Even if you are able to get something working you will find that a DIY PaaS comes with a high maintenance burden. This is a large part of what OpenShift is about, it takes away from you all the effort of understanding how to run a PaaS well and to do it securely.

So if interested in where PaaS environments are headed, I definitely recommend trying the All-In-One VM for OpenShift and watching Grant’s video. With the All-In-One VM available so you can try things yourself, I will also be starting to post more about using Python web applications with OpenShift.

If anyone does have any specific questions about hosting Python web applications with OpenShift, do let me know and perhaps it can be a good subject for a future post. Easiest thing to do is to drop me a message on Twitter \(@GrahamDumpleton\) with any suggestions.