---
title: "Deploying Jupyter Notebooks in a hosted environment."
author: "Graham Dumpleton"
date: "Sunday, April 30, 2017"
url: "http://blog.dscpl.com.au/2017/04/deploying-jupyter-notebooks-in-hosted.html"
post_id: "3201848606607116967"
blog_id: "2363643920942057324"
tags: ['docker', 'ipython', 'jupyter', 'kubernetes', 'openshift', 'python']
comments: 0
published_timestamp: "2017-04-30T16:20:00+10:00"
blog_title: "Graham Dumpleton"
---

The popularity of a programming language can often be dictated by the existence of a [killer application](https://en.wikipedia.org/wiki/Killer_application). One example is PHP and the web site creation tool Wordpress. In the Python language community, it is harder to point to any one application that helps in promoting the language above and beyond any others. This is in part because Python can be applied in various ways and is not focused on just one area, such as implementing web applications, as is the case of PHP. Python therefore has a number of candidates for what could potentially be deemed a killer application or enabling framework, but in different subject domains.

One example of such an application for Python is the interactive code based environment provided by [Jupyter Notebooks](http://jupyter.org/). In the data science, research and education fields, Jupyter Notebooks are becoming an increasing popular method for working with data to perform ad-hoc analysis, as well as for teaching of programming language concepts and algorithms.

# Running in containers

As a teaching tool in education, Jupyter Notebooks provide a rich environment in which students can work, but one of the challenges is ensuring that all students have the same environment. This is made difficult due to students running different operating systems, or different versions of software, both bundled and self installed.

A solution to this problem is to run software in a defined environment. That is, create a software image which includes all the required packages already pre-installed in an operating system image and run that.

In the past one would have done this using a virtualised environment, where an image is run in its own virtual machine, complete with a running operating system of its own. These days, one would instead run the application in a light weight container, where operating system services are provided by the underlying host operating system and are not actually running inside of the container.

# Hosted vs running locally

Distributing your own image means that if teaching with Jupyter Notebooks, you can ensure that all students are using the same software. You can also bundle any required course material as part of the image so you know that students have everything they need.

In distributing an environment in this way, although you know it will be the same for each student, it doesn't avoid the issue that students still need to install some software locally to run it. This is because they would still need to install any software that allows them to run the container image. There is also the problem of the size of images and a students access to a good enough Internet connection to download them.

The alternative to running the image locally is to use a hosted environment. This is where whoever is teaching the students would set up a purpose built hosted environment specifically to run the Jupyter Notebooks for the students.

Doing this isn't necessarily a trivial task, but at least it has to only be done once, notionally by those who would have the knowledge of how to set it up and run it, or at least the impetus to do it.

The task of running a hosted environment for Jupyter Notebooks is also made easier using the [JupyterHub](https://github.com/jupyterhub/jupyterhub) software, a purpose built application for interacting with users and starting up Jupyter Notebook instances on their behalf.

The JupyterHub software even supports different backend systems for running Jupyter Notebooks, including running them all on the one host, or delegating them to run across a cluster of hosts.

# Generic hosting platform

Even using JupyterHub, you still generally need purpose built infrastructure to be set up and dedicated to the specific requirement of running the Jupyter Notebook instances. It is not really possible to make use of a generic multi user hosting service to run JupyterHub and have it manage the Jupyter Notebook instances. You cannot for example signup to Heroku or Amazon Elastic Beanstalk and hope to run JupyterHub on those in order to provide an environment to run a class with many students.

The closest you can get is to use the [dockerspawner](https://github.com/jupyterhub/dockerspawner) plugin for JupyterHub and run it across a set of hosts on a Docker Swarm cluster, or use [kubespawner](https://github.com/jupyterhub/kubespawner) and run it on a Kubernetes cluster.

Neither of these though are multi user generic hosting services. Yes, you could setup and run Docker Swarm or Kubernetes, but the instance is still effectively dedicated to you. Neither Docker Swarm or Kubernetes alone are a multi tenant hosting service where the instance is shared by other users, running completely different applications all isolated from each other.

You might be thinking, why does it matter if it is my own cluster and no one else is using it for anything else. From the perspective of an educational institution or organisation wanting to run it, a key reason is cost.

When you have a dedicated cluster just for your specific use in running JupyterHub, it means one more piece of infrastructure that the IT team has to manage on top of everything else they have to run, adding to maintenance and support overheads. Also, your cluster is likely going to be very much under utilised, with machines sitting idle most of the time. Because it is dedicated infrastructure, the IT department can't readily utilise it for anything else to make the most productive use of any hardware resources.

This is where being able to run JupyterHub on a generic multi tenant hosting platform can be beneficial. The IT department need only set up one set of infrastructure which provides hosting for many different users, for different applications and purposes, at the same time. This reduces the number of systems they need to manage, as well as ensure they can make the most of available hardware resources. This all comes together to allow them to reduce overall operating expenditure and money can be used for other purposes.

# Conferences and blog posts

With that as background, for the past year and a half I have as a personal side project, been researching the problem of best methods for deploying Jupyter Notebooks, directly and via JupyterHub, using container based deployment methods. This has been as an extension of other research I have been doing for many years on deploying Python web applications.

I have published a few blog posts in the past related to what I have been doing, but they have mainly been addressing specific issues which arise in running Python web applications, including Jupyter Notebooks, in containers. To date I haven't really posted much about the bigger problem I am trying to solve in running Jupyter Notebooks and JupyerHub on a modern container platform. I have submitted talks for half a dozen different conferences in that time on the topic, but have yet to have any success in getting a talk accepted.

Despite having no success in getting word out via conferences on what I have been working on, I don't like to work on things and then move on without saying something about it, so I am going to fall back to writing further blog posts about the topic. The only downside with blog posts is I do like to try and cover all the intricacies of problems in details. I can therefore go down a bit of a meandering path in getting to the final picture.

If you can put up with that you should be good, and hopefully as well as the core problem I am trying to solve, you will learn about some side topics in the process.

With that said, I present the first seven blog posts I have written on the topic. These were posted over the past few weeks, albeit not here on my own blog site, but on the blog site for OpenShift.

In this first series of blog posts I look at the issue of deploying single Jupyter Notebook instances to OpenShift. The posts are:

  * [Jupyter on OpenShift: Using OpenShift for Data Analytics](https://blog.openshift.com/jupyter-openshift-using-openshift-data-analytics/) – Introductory post which introduced the series and provided a quick tour of deploying a Jupyter Notebook on OpenShift.
  * [Jupyter on OpenShift Part 2: Using Jupyter Project Images](https://blog.openshift.com/jupyter-openshift-part-2-using-jupyter-project-images/) – Showed how the Jupyter Notebook images from the Jupyter Project can be deployed on OpenShift.
  * [Jupyter on OpenShift Part 3: Creating a S2I Builder Image](https://blog.openshift.com/jupyter-on-openshift-part-3-creating-a-s2i-builder-image/) – Showed how the Jupyter Project images can be Source-to-Image \(S2I\) enabled, allowing them to be run against a Git repository to bundle notebooks and data files, as well as install required Python packages.
  * [Jupyter on OpenShift Part 4: Adding a Persistent Workspace](https://blog.openshift.com/jupyter-on-openshift-part-4-adding-a-persistent-workspace/) – Showed how to add a persistent volume and automatically transfer notebooks and data files into it so work is saved.
  * [Jupyter on OpenShift Part 5: Ad-hoc Package Installation](https://blog.openshift.com/jupyter-on-openshift-part-5-ad-hoc-package-installation/) – Showed how to deal with ad-hoc package installation and moving the Python virtual environment into the persistent volume.
  * [Jupyter on OpenShift Part 6: Running as an Assigned User ID](https://blog.openshift.com/jupyter-on-openshift-part-6-running-as-an-assigned-user-id/) – Showed how the S2I enabled image can be modified to allow it to run under the default security policy of OpenShift.
  * [Jupyter on OpenShift Part 7: Adding the Image to the Catalog](https://blog.openshift.com/jupyter-on-openshift-part-7-adding-the-image-to-the-catalog/) – Showed how to create the image stream definitions which allowed the Jupyter Notebook image to be listed in the application catalog of the web console.



The final goal for all the posts I will write, is to show a simple way to deploy JupyterHub to OpenShift and run it at scale to host large numbers of students in a teaching environment. This could be your own OpenShift cluster which you have installed using the Open Source upstream [OpenShift Origin](https://www.openshift.org/) project. It could also be a managed or public OpenShift instance such as [OpenShift Dedicated](https://www.openshift.com/dedicated/), [OpenShift Online](https://www.openshift.com/devpreview/) or any service from the various hosting providers starting to pop up which are using OpenShift. Finally it might be a supported on premise instance of [OpenShift Container Platform](https://www.openshift.com/).

I also hope to eventually post about any additional lessons learnt in trying to deploy JupyterHub to OpenShift in support of running a course for up to 150 students in a university setting, something which I have recently started working with a university to achieve.

Mosts posts will be made on the OpenShift [blog site](https://blog.openshift.com/), but I will do followups here occasionally to summarise each series of posts and provide links. I expect it to take a few months to get through everything I want to cover.