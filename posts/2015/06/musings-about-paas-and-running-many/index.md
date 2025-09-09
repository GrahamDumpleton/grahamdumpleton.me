---
title: "Musings about PaaS and running many small micro services."
author: "Graham Dumpleton"
date: "Thursday, June 18, 2015"
url: "http://blog.dscpl.com.au/2015/06/musings-about-paas-and-running-many.html"
post_id: "6416006511013101949"
blog_id: "2363643920942057324"
tags: ['docker', 'kubernetes', 'python', 'wsgi']
comments: 2
published_timestamp: "2015-06-18T17:45:00+10:00"
blog_title: "Graham Dumpleton"
---

One of the problems with various PaaS offerings out there is that the resource limits they offer are actually too large for your needs. This is especially the case where you want to run a bunch of little web sites or micro services. For example, the most commonly available memory size for instances at the low end is 512MB. Where disk space is provided, it is often 1GB. Having such fixed limits, with no further flexibility in choice at the low end, means that you are wasting a lot of resources per site where it may only require at most 128MB and little disk space. When you are paying for such a service, this is wasted money if you are needing to deploy many micro services with small resource requirements.

You might be thinking, how is that a problem, I will just run multiple services within the one instance. If only it were that simple.

Running multiple services within the one instance is generally hard because of the model by which the PaaS requires you to push code up to the service. That is, for a single instance, all the code you want to run on it must be pushed up from the one git repository.

That you have to push all the code as one unit means you cannot break up your micro services and manage them as separate git repositories. You could separate each micro service into separate sub directories of a single git repository, but needing to do it in this way is less than ideal as then you can't readily manage the code bases independently.

The next restriction when using Python for small web sites at least, is that a PaaS may restrict your choice as to what WSGI servers you can use. This can be due to locking you into using a specific WSGI server configured in a certain way, or locking out the ability to run a WSGI server where the underlying web server component provides native support for virtual hosts and capabilities to separate the distinct sites as separate processes.

The latter issue means you are generally forced to run the multiple web sites within the same process and use a WSGI middleware to effect switching between the different web sites based on the host the request was destined for. This will not work though where for example you were wanting to run multiple Django web sites. This is because the reliance on global environment variables and settings in Django means multiple distinct sites with separate code bases can't coexist.

Going forward, the Docker ecosystem promises to be a solution to this problem, as it will allow you to create each micro service as a separate Docker image and then run the Docker instances together on the same platform, be that you own Docker installation or as a managed service.

As far as PaaS goes, the issue is still going to be how the service provider allocates resources to each Docker instance. If they follow the existing paradigm of simply assigning a memory limit in the order of 512MB to each Docker instance and effectively charge in the same way, then you are not really in much better of a situation.

The addition of Kubernetes into the mix with Docker, in order to handle service orchestration for deployment, does potentially offers some much better possibilities.

In the case of Kubernetes, in addition to the concept of a container, there is a concept of a pod.

When you deploy an instance of a container, you actually need to allocate it to a pod. More than one container can be allocated to a pod. They could be the same type of container or different.

The intent of a pod is principally to allow you to group containers related to a specific application which need to share resources. The services running in a particular pod would also all be allocated to the same host.

How pods help us with the issue of micro services with small resource requirements is that resource limitations are defined at the level of both the pod and the container.

What ideally will happen as PaaS offerings using Docker and Kubernetes come along is that where now you pay for having 512MB and can effectively only run a single service, is that the 512MB limitation will actually be applied at the level of the pod. How many micro services you can then fit within that pod running in separate containers is really up to you.

This gets around the original problem because when deploying the container for each micro service you can say how much memory it will use. You might therefore have 4 separate containers you want to deploy to the pod and for each of these you would say they use 128MB each. As the total memory requirement fits within the 512MB memory limitation of the pod, then all should be good.

The end result is that Docker, using Kubernetes as the orchestration tool, has the potential for making the way you carve up the resources provided by a PaaS much more flexible than what exists now. The big question will be how the different PaaS offerings which are moving to a Docker based architecture using an orchestration tool such as Kubernetes will manage how they charge for resources.

If a service is simply going to try and charge per container in a similar vein to how existing PaaS offerings work, then it isn't going to offer anything better in the way of value. So here is hoping that the pod is the new unit of billing.

---

## Comments

### Lee Calcote - September 2, 2015 at 11:56 AM

Graham, good thoughts. Have you looked at the minimum pod and container resource sizings in OpenShift v3? How low do these go?

### Graham Dumpleton - September 2, 2015 at 12:05 PM

I don't know if there is a minimum as a safety net but will find out, or at least keep it in mind to work it out.  
  
One thing I have heard is that for OpenShift Online with V3 when that happens, it does look like you will have your resource allocation at a high enough level to be able to do such dividing up of the resources across projects/pods based on your own requirements. So it looks like the flexibility I would like to see even in the Online offering will be there.

