---
title: "Speeding up Docker build times for Python applications."
author: "Graham Dumpleton"
date: "Wednesday, March 2, 2016"
url: "http://blog.dscpl.com.au/2016/03/speeding-up-docker-build-times-for.html"
post_id: "2004116114657697132"
blog_id: "2363643920942057324"
tags: ['docker', 'openshift', 'python', 's2i']
comments: 1
published_timestamp: "2016-03-02T09:09:00+11:00"
blog_title: "Graham Dumpleton"
---

I recently wrote a [post](/posts/2016/02/building-better-user-experience-for/) where I talked about building a better user experience for deploying Python web applications. If one counts page hits as an indicator of interest in a subject then it certainly seems like an area people would like to see improvements.

In that post I talked about a system I was working on which simplified starting up a Python web server for your web application in your local environment, but also then how you can easily move to deploying that Python web application to Docker or OpenShift 3.

In moving to Docker, or OpenShift 3 \(which internally also uses Docker\), the beauty of the system I described was that you didn’t have to know how to create a Docker image yourself. Instead I used a package called [S2I](https://github.com/openshift/source-to-image) \(Source to Image\) to construct the Docker image for you.

What S2I does is use a Docker base image which incorporates all the system packages and the language run time environment you need for working in a specific programming language such as Python. That same Docker image also includes a special script which is run to incorporate your web application code into a new Docker image which builds off the base image. A further script within the image starts up an appropriate web server to run your web application. In the typical case, you don’t need to know anything at all about how to configure the web server as everything is done for you.

# Docker build times

A problem that can arise any time you use Docker, unless you are careful, is how long it takes to actually perform the build of the Docker image for your web application. If you are making constant changes but need to rebuild the Docker image each time to test it, or redeploy it into a live environment, you could end up waiting quite a long time over the period of your work day. Decreasing the time it takes to build the Docker image can therefore be important.

The general approach usually followed is to very carefully craft your ‘Dockerfile’ so that it uses multiple layers, where the incorporation of parts which change most frequently are done last. By doing this, the fact that Docker will cache layers and start rebuilding only at the first layer changed, means you can avoid rebuilding everything every time.

This approach does break down though in various ways, especially with Python. The use of S2I can also complicate matters because it aims to construct the final image incorporating your application code, as well as all the dependent packages required by your application in a single Docker layer.

One issue with Python is the use of a ‘requirements.txt’ file and ‘pip’ to install packages. If you need to install a lot of packages and you add a single new package to the list, then all of them have to be reinstalled. Further, if those packages are being installed in the same layer as when your application code is being incorporated, as is the case with S2I, then a change to the application code causes all the packages to also be reinstalled.

So although S2I provides a really simple and clean way of constructing Docker images without you yourself needing to know how to create them, long build times are obviously not ideal.

As an example of how long a build time can be, consider the creation of a Docker image for hosting a Wagtail CMS site using Django. The ‘requirements.txt’ file in this case contains only:

```
    Django>=1.9,<1.10  
    wagtail==1.3.1  
    psycopg2==2.6.1
```

Although this isn’t all that is installed. The complete list of packages which gets installed are:

```
    beautifulsoup4==4.4.1  
    Django==1.9.2  
    django-appconf==1.0.1  
    django-compressor==2.0  
    django-modelcluster==1.1  
    django-taggit==0.18.0  
    django-treebeard==3.0  
    djangorestframework==3.3.2  
    html5lib==0.9999999  
    Pillow==3.1.1  
    psycopg2==2.6.1  
    pytz==2015.7  
    rcssmin==1.0.6  
    rjsmin==1.0.12  
    six==1.10.0  
    Unidecode==0.4.19  
    wagtail==1.3.1  
    wheel==0.29.0  
    Willow==0.2.2
```

Using my ‘warpdrive’ script from the previous blog post I referenced, it can take over 5 minutes over my slow Internet connection to bring down all the required Python packages, build them and construct the image.

```python
    (warpdrive+wagtail-demo-site) $ time warpdrive image wagtail  
    I0301 22:01:01.374459 16060 install.go:236] Using "assemble" installed from "image:///usr/local/s2i/bin/assemble"  
    I0301 22:01:01.374643 16060 install.go:236] Using "run" installed from "image:///usr/local/s2i/bin/run"  
    I0301 22:01:01.374674 16060 install.go:236] Using "save-artifacts" installed from "image:///usr/local/s2i/bin/save-artifacts"  
    ---> Installing application source  
    ---> Building application from source  
    -----> Installing dependencies with pip (requirements.txt)  
    Collecting Django<1.10,>=1.9 (from -r requirements.txt (line 1))  
    Downloading Django-1.9.2-py2.py3-none-any.whl (6.6MB)  
    Collecting wagtail==1.3.1 (from -r requirements.txt (line 2))  
    Downloading wagtail-1.3.1-py2.py3-none-any.whl (9.0MB)  
    Collecting psycopg2==2.6.1 (from -r requirements.txt (line 3))  
    Downloading psycopg2-2.6.1.tar.gz (371kB)  
    ...  
    Installing collected packages: Django, djangorestframework, Unidecode, Pillow, rcssmin, rjsmin, six, django-appconf, django-compressor, Willow, html5lib, django-taggit, pytz, django-modelcluster, beautifulsoup4, django-treebeard, wagtail, psycopg2  
    ...  
    Running setup.py install for psycopg2: finished with status 'done'  
    Successfully installed Django-1.9.2 Pillow-3.1.1 Unidecode-0.4.19 Willow-0.2.2 beautifulsoup4-4.4.1 django-appconf-1.0.1 django-compressor-2.0 django-modelcluster-1.1 django-taggit-0.18.0 django-treebeard-3.0 djangorestframework-3.3.2 html5lib-0.9999999 psycopg2-2.6.1 pytz-2015.7 rcssmin-1.0.6 rjsmin-1.0.12 six-1.10.0 wagtail-1.3.1  
    -----> Collecting static files for Django  
    ...  
    Copying '/opt/warpdrive/demo/static/js/demo.js'  
    ...  
    Copying '/usr/local/python/lib/python2.7/site-packages/django/contrib/admin/static/admin/img/gis/move_vertex_off.svg'

    179 static files copied to '/home/warpdrive/django_static_root'.  
    ---> Fix permissions on application source

    real 5m40.780s  
    user 0m0.850s  
    sys 0m0.115s
```

If you were running ‘pip’ in your local environment and installing into a Python virtual environment, rerunning ‘pip’ on the ‘requirements.txt’ wouldn't be a big issue. This is because the packages would already be detected as being installed and so wouldn’t need to be downloaded and installed again. Even if you did blow away your Python virtual environment and recreate it, the downloaded packages would be in the cache that ‘pip’ maintains in your home directory. It could therefore just use those.

When creating Docker images however, you don’t get the benefit of those caching mechanisms because everything is done over every time. This means that all the packages have to be downloaded every time.

# Using a wheelhouse

A possible solution to this is to create a wheelhouse. That is, you use ‘pip’ to create a directory of the packages you need to install as Python wheels. For pure Python packages these would just be that code, but if a Python package included C extensions, the Python wheel file would include the compiled code as object files. This means that the code doesn’t need to be recompiled every time and can simply be copied into place.

Although this can be done, working this into how you build your Docker images can get a bit messy as shown by Glyph in a [blog post](https://glyph.twistedmatrix.com/2015/03/docker-deploy-double-dutch.html) he wrote about it. It is therefore an area which is ripe for being simplified and so I have also been working that into what I have been doing with trying to simplify the deployment of web applications. In this post I want to show how that is progressing.

First step now is to create a special Docker image which acts as our Python wheelhouse. This can be done by running the following command.

```python
    (warpdrive+wagtail-demo-site) $ warpdrive image --build-target wheelhouse wagtail-wheelhouse  
    I0301 23:03:32.687290 17126 install.go:236] Using "assemble" installed from "image:///usr/local/s2i/bin/assemble"  
    I0301 23:03:32.687446 17126 install.go:236] Using "run" installed from "image:///usr/local/s2i/bin/run"  
    I0301 23:03:32.687475 17126 install.go:236] Using "save-artifacts" installed from "image:///usr/local/s2i/bin/save-artifacts"  
    I0301 23:03:32.709215 17126 docker.go:286] Image "wagtail-wheelhouse:latest" not available locally, pulling ...  
    ---> Installing application source  
    ---> Building Python wheels for packages  
    -----> Installing dependencies as wheels with pip (requirements.txt)  
    Collecting Django<1.10,>=1.9 (from -r requirements.txt (line 1))  
    Downloading Django-1.9.2-py2.py3-none-any.whl (6.6MB)  
    Saved ./.warpdrive/wheelhouse/Django-1.9.2-py2.py3-none-any.whl  
    Collecting wagtail==1.3.1 (from -r requirements.txt (line 2))  
    Downloading wagtail-1.3.1-py2.py3-none-any.whl (9.0MB)  
    Saved ./.warpdrive/wheelhouse/wagtail-1.3.1-py2.py3-none-any.whl  
    Collecting psycopg2==2.6.1 (from -r requirements.txt (line 3))  
    Downloading psycopg2-2.6.1.tar.gz (371kB)  
    ...  
    ---> Fix permissions on application source
```

This command is going to run a bit differently to the command above. Rather than use ‘pip install’ to install the actual packages, it will run ‘pip wheel’ to create the Python wheels we are after. At that point it will stop, as we don’t need it do additional steps such as run ‘collectstatic’ for Django to gather up static file assets. This will still take up to 5 minutes though since the bulk of the time was involved in downloading and building the packages.

Once we have our wheelhouse, when building the Docker image for our application, we can point it at the wheelhouse as a source for the prebuilt Python packages we want to install. We can even tell it to take what it provides as the authority and not consult the Python package index \(PyPi\) to check whether there aren’t newer versions of the packages when packages haven’t been pinned to a specific package.

```python
    (warpdrive+wagtail-demo-site) $ time warpdrive image --wheelhouse wagtail-wheelhouse --no-index wagtail  
    warpdrive-image-17312  
    I0301 23:12:54.610882 17329 install.go:236] Using "assemble" installed from "image:///usr/local/s2i/bin/assemble"  
    I0301 23:12:54.611033 17329 install.go:236] Using "run" installed from "image:///usr/local/s2i/bin/run"  
    I0301 23:12:54.611089 17329 install.go:236] Using "save-artifacts" installed from "image:///usr/local/s2i/bin/save-artifacts"  
    ---> Installing application source  
    ---> Building application from source  
    -----> Found Python wheelhouse of packages  
    -----> Installing dependencies with pip (requirements.txt)  
    Collecting Django<1.10,>=1.9 (from -r requirements.txt (line 1))  
    Collecting wagtail==1.3.1 (from -r requirements.txt (line 2))  
    Collecting psycopg2==2.6.1 (from -r requirements.txt (line 3))  
    ...Installing collected packages: Django, Unidecode, pytz, django-modelcluster, djangorestframework, Pillow, django-treebeard, django-taggit, six, Willow, rjsmin, django-appconf, rcssmin, django-compressor, beautifulsoup4, html5lib, wagtail, psycopg2  
    Successfully installed Django-1.9.2 Pillow-3.1.1 Unidecode-0.4.19 Willow-0.2.2 beautifulsoup4-4.4.1 django-appconf-1.0.1 django-compressor-2.0 django-modelcluster-1.1 django-taggit-0.18.0 django-treebeard-3.0 djangorestframework-3.3.2 html5lib-0.9999999 psycopg2-2.6.1 pytz-2015.7 rcssmin-1.0.6 rjsmin-1.0.12 six-1.10.0 wagtail-1.3.1  
    -----> Collecting static files for Django  
    ...  
    Copying '/opt/warpdrive/demo/static/js/demo.js'  
    ...  
    Copying '/usr/local/python/lib/python2.7/site-packages/django/contrib/admin/static/admin/img/gis/move_vertex_off.svg'

    179 static files copied to '/home/warpdrive/django_static_root'.  
    ---> Fix permissions on application source

    real 0m45.859s  
    user 0m3.555s  
    sys 0m2.575s
```

With our wheelhouse, building of the Docker image for our web application has dropped from over 5 minutes down to less than a minute. This is because when installing the Python packages, it is able to reuse the pre built packages from the wheelhouse. This means a quicker turnaround for creating a new application image. We will only need to rebuild the wheelhouse itself if we change what packages we need to have installed.

# Incremental builds

Reuse therefore allows us to speed up the building of Docker images considerably where we have a lot of Python packages that need to be installed. The reuse of previous builds can also be used in another way, which is to reuse the prior wheelhouse itself when updating the wheelhouse after changes to the list of packages we need.

```python
    (warpdrive+wagtail-demo-site) $ time warpdrive image --build-target wheelhouse wagtail-wheelhouse  
    I0301 23:18:24.150533 17448 install.go:236] Using "assemble" installed from "image:///usr/local/s2i/bin/assemble"  
    I0301 23:18:24.151074 17448 install.go:236] Using "run" installed from "image:///usr/local/s2i/bin/run"  
    I0301 23:18:24.151121 17448 install.go:236] Using "save-artifacts" installed from "image:///usr/local/s2i/bin/save-artifacts"  
    ---> Restoring wheelhouse from prior build  
    ---> Installing application source  
    ---> Building Python wheels for packages  
    -----> Installing dependencies as wheels with pip (requirements.txt)  
    Collecting Django<1.10,>=1.9 (from -r requirements.txt (line 1))  
    File was already downloaded /opt/warpdrive/.warpdrive/wheelhouse/Django-1.9.2-py2.py3-none-any.whl  
    Collecting wagtail==1.3.1 (from -r requirements.txt (line 2))  
    File was already downloaded /opt/warpdrive/.warpdrive/wheelhouse/wagtail-1.3.1-py2.py3-none-any.whl  
    Collecting psycopg2==2.6.1 (from -r requirements.txt (line 3))  
    Using cached psycopg2-2.6.1.tar.gz  
    ...  
    ---> Fix permissions on application source

    real 1m17.180s  
    user 0m3.653s  
    sys 0m2.316s
```

Here we have run the exact same command as we ran before to create the wheelhouse in the first place, but instead of taking 5 minutes to build, it has taken just over 1 minute.

This speed up was achieved because we were able to copy across the ‘pip’ cache as well as the directory of Python wheel files from the previous instance of the wheelhouse.

# Not a Dockerfile in sight

Now what you didn’t see here at all was a ‘Dockerfile’. For me this is a good thing.

The problem with Docker right now is that the novelty still hasn’t warn off, with it still not being seen for what it is, just another tool we can use. As a result we are still in this phase where developers using Docker like to play with it and so try and do everything themselves from scratch. We need to get beyond that phase and start incorporating best practices into canned scripts and systems and simply get on with using it.

Anyway, this is where I am at least heading with the work I am doing. That is, encapsulate all the best practices for Python web application deployment, including the building of Docker images which you can run directly, or with a PaaS using Docker such as OpenShift. The aim here being to make it so much easier for you, with you knowing that you can trust that the mechanisms have been put together will all the best practices being followed. After all, do you really want to keep reinventing the wheel all the time?

---

## Comments

### Graham Dumpleton - March 5, 2016 at 7:37 AM

A followup post to this about how to integrate this mechanism with OpenShift can now be found at:  
  
https://blog.openshift.com/using-image-source-reduce-build-times/

