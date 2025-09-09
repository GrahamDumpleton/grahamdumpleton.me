---
title: "Integrating  the workshop notes with the image"
author: "Graham Dumpleton"
date: "Thursday, January 3, 2019"
url: "http://blog.dscpl.com.au/2019/01/integrating-workshop-notes-with-image.html"
post_id: "4780813243574726591"
blog_id: "2363643920942057324"
tags: ['docker', 'jupyterhub', 'kubernetes', 'openshift', 'red hat']
comments: 0
published_timestamp: "2019-01-03T17:48:00+11:00"
blog_title: "Graham Dumpleton"
---

If you are still following this series of blog posts, we now have a [dashboard](/posts/2019/01/dashboard-combining-workshop-notes-and/) for our workshop environment which combines workshop notes with the interactive terminal in the users browser.

This enabled us to have the instructions right next to the terminal where workshop attendees execute the commands. Further, it was possible to have it so that they need only click on the commands and they would be automatically executed in the terminal. This way they didn't need to manually enter commands or cut and paste them, both which can be prone to mistakes.

In this blog post we will look at how workshop notes for a specific workshop can be combined with the dashboard to create a self contained image, which can be deployed to a local container runtime, to OpenShift as a standalone instance, or using JupyterHub in a multi user workshop.

# Building a custom dashboard image

We already [covered previously](/posts/2018/12/creating-your-own-custom-terminal-image/) the methods for creating a custom version of the terminal image which included additional command line tools and source files required for a workshop. The process is the same, but instead of using the terminal base image, the dashboard base image is used instead.

The two methods that could be used were to use the base image as a Source-to-Image \(S2I\) builder, or to build a custom image from a `Dockerfile`.

If you were running the build in OpenShift as an S2I build, with your files in a hosted Git repository, you could create the build by running the command:
    
    
```
  oc new-build quay.io/openshiftlabs/workshop-dashboard:latest~https://your-repository-url \
      --name my-workshop-dashboard
```
    
    

All you now need to know is the layout for the workshop notes so they are picked up and displayed correctly.

# Layout for the custom workshop notes

The workshop notes were being hosted using [Raneto](http://docs.raneto.com/), a knowledge base application implemented in Node.js. This was installed as part of the dashboard image which extends the terminal base image. When the image is started, Raneto will be started along side Butterfly and the proxy, with supervisord managing them all.

When building the custom image, the files for Raneto should be placed in the `raneto` sub directory. Within the `raneto` directory, the Markdown files for the workshop notes should be placed in the `content` subdirectory. Files should be Markdown files with `.md` extension.

The Markdown files can be placed directly into the `content` directory, or you can create further subdirectories to represent a category or set of multi part exercises.

By default, when pages are listed in the catalog on the home page for the workshop notes, they will appear in sorted order based on the names of the files. In the case of a subdirectory, they will be sorted within that category. If you need to control sorting, you can use meta data within the Markdown files to control relative file order, or using a `sort` file when needing to control the order that categories are shown. Check the Raneto [documentation](http://docs.raneto.com/usage/sorting) for more details on sorting.

If you want to replace the default home page which shows the categories and files within each category, you can provide an `index.md` file in the `content` directory.

A typical layout for the files might therefore be:
    
    
```
  raneto/content/index.md
  raneto/content/setup.md
  raneto/content/exercise-01/01-first-part-of-exercise.md
  raneto/content/exercise-01/02-second-part-of-exercise.md
  raneto/content/exercise-01/03-third-part-of-exercise.md
  raneto/content/finish.md
```
    
    

The `index.md` file would be a custom home page giving an overview of the workshop. The `setup.md` file would be any pre-requisite setup that may be required, such as logging in from the command line, creating projects, adding special roles etc. The `finish.md` file would be a final summary shown at the end of the workshop.

The subdirectories will then be where the exercises are kept, with the exercises broken into parts of a manageable size.

# Defining the navigation path for the workshop

As Raneto is intended as being a knowledge base, it normally doesn't dictate a navigation path to direct the order in which pages should be visited. The templates used with the dashboard add to Raneto the ability to define a path to follow by specifying the navigation path as meta data in the Markdown files.

The metadata at the head of the `index.md` file would be:
    
    
```
  ---
  Title: Workshop Overview
  NextPage: setup
  ExitSign: Setup Environment
  Sort: 1
  ---
```
    
    

That for `setup.md` would be:
    
    
```
  ---
  Title: Setup Environment
  PrevPage: index
  NextPage: exercise-01/01-first-part-of-exercise
  ExitSign: Start Exercise 1
  Sort: 2
  ---
```
    
    

That for the last part of the last exercise:
    
    
```
  ---
  PrevPage: 02-second-part-of-exercise
  NextPage: ../finish
  ExitSign: Finish Workshop
  ---
```
    
    

And that for `finish.md`:
    
    
```
  ---
  Title: Workshop Summary
  PrevPage: exercise-02/02-second-part-of-exercise
  Sort: 3
  ---
```
    
    

The `Title` field allows the generated page title based on the name of the file to be overridden. The `NextPage` and `PrevPage` define the navigation path. The `ExitSign` allows you to override the label on the button at the end of a page which you click on to progress to the next page in the navigation path.

Each of the pages making up the exercises should similarly be chained together to define the navigation path to be followed.

# Interpolation of variables into workshop notes

A set of predefined variables are available which can be automatically interpolated into the page content. These variables are:

  * `base_url` \- The base URL for the root of the workshop notes.
  * `username` \- The name of the OpenShift user/service account when deployed with JupyterHub.
  * `project_namespace` \- The name of an existing project namespace that should be used.
  * `cluster_subdomain` \- The sub domain used for any application routes created by OpenShift.



How these are set will depend on how the dashboard image is being deployed. Workshop notes will have to be tolerant of different deployment options and may need to specify alternate sets of steps if expected to be deployed in different ways.

To use the variables in the Markdown files, use the syntax:
    
    
```
  %username%
```
    
    

Additional variables for interpolation can be supplied for a workshop by providing the file `raneto/config.js`, including:
    
    
```
  var config = {
      variables: [
        {
          name: 'name',
          content: 'value'
        }
      ]
  };
```
    
```
  module.exports = config;
```
    
    

The contents of this config file will be merged with that for Raneto. The contents of the file must be valid Javascript code. You can use code in the file to lookup environment variables or files to work out what to set values to. The Javascript code will be executed on the server, in the container for the users environment.

This config file can also be used to override the default title for the workshop by setting the `site_title` attribute of the `config` dictionary.

# Formatting and executable/copyable code blocks

You can use GitHub flavoured Markdown when needing to do formatting in pages.

In order to mark code blocks so that clicking on them will cause them to be copied to the first terminal and run, add `execute` or `execute-1` after the leading triple back quotes which starts the code block, on the same line and with no space between then. If you want the second terminal to be used instead, use `execute-2`.

To have the contents of the code block copied into the copy and paste buffer when clicked on, use `copy` instead of `execute`.

# Embedded images in workshop notes

The workshop notes can include embedded images. Place the image in the same directory as the Markdown file and use appropriate Markdown syntax to embed it.
    
    
```
  ![Screenshot](./screenshot.png)
```
    
    

# Using HTML for more complex formatting

As with many Markdown parsers, it is possible to include HTML markup. This could be used to render complex tables, or could also be used in conjunction with Javascript, to add conditional sections based on the values passed in using the interpolated values. Note that any such Javascript is executed in the browser, not on the server.

# Defining additional build and runtime steps

As when creating a custom terminal image using the S2I build process, you can define an executable shell script `.workshop/build` to specify additional steps to run. This can be used to check out Git repositories and pre-build application artifacts for anything used in the workshop. Similarly, a `.workshop/setup` script can be included to define steps that should be run each time the container is started.

# Coming up next, deploying the full workshop

This post provides a rough guide on how to add workshop notes to the image when using the dashboard image in an S2I build. How to deploy the dashboard image for a multi user workshop is similar to what was [described previously](/posts/2018/12/deploying-multi-user-workshop/), you just need to supply the custom dashboard image instead of the custom terminal image.

Deploying a multi user workshop where the users are known in advance by virtue of performing user authentication against OpenShift, isn't the only way that JupyterHub could be used to create a workshop environment.

In the next post we will revise how to deploy the multi user workshop using the custom dashboard image and the existing JupyterHub deployment, but we will have a look at an alternate scenario as well.

This scenario is where you accomodate anonymous users, where they are given an ephemeral identity in the cluster using a service account, along with a temporary project namespace to work in that is automatically deleted when they are done.