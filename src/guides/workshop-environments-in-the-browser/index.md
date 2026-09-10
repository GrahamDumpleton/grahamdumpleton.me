---
title: "Running workshop environments in the browser."
description: "Building a multi user workshop environment on Kubernetes, using JupyterHub to spawn an interactive terminal, workshop notes and a dashboard for each attendee."
tags: ["kubernetes", "jupyterhub", "docker", "openshift"]
draft: false
---

Posts on running interactive workshop and training environments in a web browser, hosted
on Kubernetes, are as follows. These were written while working with JupyterHub as the
means of spawning a session for each user, and they lead into the work which later became
[Educates](/guides/creating-workshops-with-educates/).

Please note older posts may not reflect what I now regard as best practice,
or may describe software which has since changed or been superseded.

The starting point, on hosting notebooks for more than one person:

  * [Deploying Jupyter Notebooks in a hosted environment.](/posts/2017/04/deploying-jupyter-notebooks-in-hosted/)

This batch of posts builds up a multi user workshop environment, starting from JupyterHub
being used to spawn something other than a notebook:

  * [Using JupyterHub as a generic application spawner.](/posts/2018/12/using-jupyterhub-as-generic-application/)
  * [Running an interactive terminal in the browser.](/posts/2018/12/running-interactive-terminal-in-browser/)
  * [Creating your own custom terminal image.](/posts/2018/12/creating-your-own-custom-terminal-image/)
  * [Deploying a multi user workshop environment.](/posts/2018/12/deploying-multi-user-workshop/)

This batch of posts fills out what a user sees when they arrive, and what the person
running the workshop can do while it is under way:

  * [Dashboard combining workshop notes and terminal.](/posts/2019/01/dashboard-combining-workshop-notes-and/)
  * [Integrating the workshop notes with the image.](/posts/2019/01/integrating-workshop-notes-with-image/)
  * [Administration features of JupyterHub.](/posts/2019/01/administration-features-of-jupyterhub/)
