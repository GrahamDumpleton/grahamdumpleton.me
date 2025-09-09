---
layout: post
title: "Learning more about using OpenShift 3."
author: "Graham Dumpleton"
date: "2016-04-07"
url: "http://blog.dscpl.com.au/2016/04/learning-more-about-using-openshift-3.html"
post_id: "5213582428171061836"
blog_id: "2363643920942057324"
tags: ['docker', 'kubernetes', 'openshift', 'pycon', 'python', 'red hat']
comments: 0
published_timestamp: "2016-04-07T16:18:00+10:00"
blog_title: "Graham Dumpleton"
---

I still have a long list of topics I could post about here on my own blog site, but over the last couple of months or so, I have been having too much fun playing with the new version of [OpenShift](https://www.openshift.org) based on Docker and Kubernetes, and understanding everything about it. The more I dig into OpenShift, the more awesome it gets as far as being the best platform around for deploying applications in our new containerised world.

A platform alone isn’t though going to give you everything you may need to provide you with the best experience for working with a particular programming language, such as Python, but this is where I am working on my own magic secret source to make everything even easier for us Python developers. I described a bit about what I was doing around [improving the deployment experience for Python web applications](/posts/2016/02/building-better-user-experience-for/) in a prior blog post. I am going to start ramping up soon on writing all the documentation for the packages I have been working on and hope to have more to show by the time of PyCon US.

In the interim, if you are interested in OpenShift and some of the things I have been looking at and uncovering, I have been posting over on the OpenShift blog site. The blog posts which I have posted up there over the past month and a bit are:

  * [Using persistent volumes with docker as a Developer on OpenShift](https://blog.openshift.com/experimenting-with-persistent-volumes/) \- This explains about how to use persistent volumes with OpenShift. This is an area where OpenShift goes beyond what is possible with hosting environments which only support 12 factor or cloud native applications. That is, not only can you host up web applications, you can run applications such as databases, which require access to persistent file system based storage
  * [Using an Image Source to reduce build times](https://blog.openshift.com/using-image-source-reduce-build-times/) \- This post is actually an extension to a post I did here on my own site about [improving Docker build times for Python applications](/posts/2016/03/speeding-up-docker-build-times-for/). In this post I show how one can include the sped up build mechanism using a Python wheelhouse within the OpenShift build and deployment infrastructure.
  * [Using a generic webhook to trigger builds](https://blog.openshift.com/using-generic-webhook-trigger-builds/) \- This describes how to use generic web hooks to trigger a build and deployment within OpenShift. This can easily be done when using GitHub to host your web application code, but in this case I wanted to trigger the build and deployment upon the successful completion of a test when using Travis CI, rather than straight away when code was pushed up to GitHub. This necessitated implementing a web hook proxy and I show how that was done.
  * [Working with OpenShift configurations](https://blog.openshift.com/working-openshift-configurations/) \- Finally, this post provides a cheat sheet for where to quickly find information about what different configuration objects in OpenShift are all about and what settings they provide.



I will be posting about more OpenShift topics on the [OpenShift blog](https://blog.openshift.com) in the future, so if you are at all interested in where the next generation of Platform as a Service \(PaaS\), or container application platforms, are headed, ensure you follow that blog.

If you are attending PyCon US this year in Portland Oregon, you also have the opportunity to learn more about OpenShift 3. This year I will be presenting a workshop titled '[Docker, Kubernetes, and OpenShift: Python Containers for the Real World](https://us.pycon.org/2016/schedule/presentation/2260/)’. This is a free workshop. All you need to do if you are already attending PyCon US, is to go back to your registration details on the PyCon US web site and go into the page for adding tutorials or workshops. You will find this workshop listed there and you can add it. Repeating again, attending the workshop will not cost you anything extra, so if you are in Portland early for PyCon US then come along. I will be talking about what OpenShift is, and how it uses Docker and Kubernetes. I will also be demonstrating the deployment of a Django based web application along with a database. This will most likely be using the Wagtail CMS if you are a fan of that. Hope to see you there.