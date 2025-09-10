---
layout: post
title: "An improved WSGI script for use with Django."
author: "Graham Dumpleton"
date: "2010-03-28"
url: "http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html"
post_id: "5322237241401383060"
blog_id: "2363643920942057324"
tags: ['django', 'mod_wsgi']
comments: 43
published_timestamp: "2010-03-28T20:49:00+11:00"
blog_title: "Graham Dumpleton"
---

Far too often one sees complaints on the Django users list and \#django IRC channel that code that worked fine with the Django development server doesn't work with Apache/mod\_wsgi. For a number of those cases you will see the accusation that Apache/mod\_wsgi must be wrong or is somehow broken. The real reason however is that when using the Django development server various setup steps are carried out which aren't performed if you use the WSGI handler interface provided by Django. The available Django documentation on using the WSGI interface doesn't however go into a great deal of technical detail. The end result is that it isn't obvious what needs to be done when using the Django WSGI interface so as to have the process environment setup to be equivalent to the Django development server, therefore guaranteeing trouble free porting of an application to a production environment using Apache/mod\_wsgi, or any other WSGI hosting mechanism.

  


The purpose of the post is to explain what actually happens when you use the Django development server as far as the setup of critical parts of the process environment, and compare that to what happens if you use the Django WSGI interface in the manner as described in the Django documentation. From that I will describe an alternate way of setting up and configuring Django for use with the supplied WGSI interface so as to better replicate how things are done within the Django development server.

  


To help track down what happens we will instrument the 'settings.py' from a Django site to include the following.
    
    
    import sys, os  
      
    print "__name__ =", __name__  
    print "__file__ =", __file__  
    print "os.getpid() =", os.getpid()  
    print "os.getcwd() =", os.getcwd()  
    print "os.curdir =", os.curdir  
    print "sys.path =", repr(sys.path)  
    print "sys.modules.keys() =", repr(sys.modules.keys())  
    print "sys.modules.has_key('mysite') =", sys.modules.has_key('mysite')  
    if sys.modules.has_key('mysite'):  
      print "sys.modules['mysite'].__name__ =", sys.modules['mysite'].__name__  
      print "sys.modules['mysite'].__file__ =", sys.modules['mysite'].__file__  
      print "os.environ['DJANGO_SETTINGS_MODULE'] =", os.environ.get('DJANGO_SETTINGS_MODULE', None)

Now, for my example the Django site is located at '/usr/local/django/mysite'. To run the Django development server I now from within that directory run 'python manage.py runserver'. The result of that is the following.
    
    
    __name__ = settings  
    __file__ = /usr/local/django/mysite/settings.pyc  
    os.getpid() = 3441  
    os.getcwd() = /usr/local/django/mysite  
    os.curdir = .  
    sys.path = ['/usr/local/django/mysite', ...]  
    sys.modules.keys() = [..., 'settings', ...]  
    sys.modules.has_key('mysite') = False  
    os.environ['DJANGO_SETTINGS_MODULE'] = None
    
    
    __name__ = mysite.settings  
    __file__ = /usr/local/django/mysite/../mysite/settings.pyc  
    os.getpid() = 3441  
    os.getcwd() = /usr/local/django/mysite  
    os.curdir = .  
    sys.path = ['/usr/local/django/mysite', ...]  
    sys.modules.keys() = [..., 'mysite.settings', ..., 'mysite.sys', 'mysite.os', ..., 'mysite', ..., 'settings', ...]  
    sys.modules.has_key('mysite') = True  
    sys.modules['mysite'].__name__ = mysite  
    sys.modules['mysite'].__file__ = /usr/local/django/mysite/../mysite/__init__.pyc  
    os.environ['DJANGO_SETTINGS_MODULE'] = mysite.settings
    
    
    __name__ = settings  
    __file__ = /usr/local/django/mysite/settings.pyc  
    os.getpid() = 3442  
    os.getcwd() = /usr/local/django/mysite  
    os.curdir = .  
    sys.path = ['/usr/local/django/mysite', ...]  
    sys.modules.keys() = [..., 'settings', ...]  
    sys.modules.has_key('mysite') = False  
    os.environ['DJANGO_SETTINGS_MODULE'] = None
    
    
    __name__ = mysite.settings  
    __file__ = /usr/local/django/mysite/../mysite/settings.pyc  
    os.getpid() = 3442  
    os.getcwd() = /usr/local/django/mysite  
    os.curdir = .  
    sys.path = ['/usr/local/django/mysite', ...]  
    sys.modules.keys() = [..., 'mysite.settings', ..., 'mysite.sys', 'mysite.os', ..., 'mysite', ..., 'settings', ...]  
    sys.modules.has_key('mysite') = True  
    sys.modules['mysite'].__name__ = mysite  
    sys.modules['mysite'].__file__ = /usr/local/django/mysite/../mysite/__init__.pyc  
    os.environ['DJANGO_SETTINGS_MODULE'] = mysite.settings 

Two things stand out from this. The first is that there are two different processes involved and the second is that the same settings file is imported twice by each process but using a different Python module name in each instance.

  


The existence of the two processes is explained by the fact that when running the Django development server it has a reload option whereby if changes are made to any code, that it will automatically restart the application. To do this it is necessary to have a supervisor or monitor process and an actual worker process. Each time that a code change is made and detected, the worker process is killed off and the supervisor process will create a new process to replace it. In that way the worker process, which is what is accepting the HTTP requests and handling them, will always have the most up to date code.

  


That the settings file is imported more than once is a bit more tricky and it is likely that the majority wouldn't even know that this occurs. Possibly people would only notice if they had placed debugging statements in the settings file like above, or they had added code to it other than simple variable settings and the code performed an action which was cumulative and thus a problem occurred through the action occurring twice.

  


So, how does the settings module get imported twice?

  


The first time it gets imported is when you run the 'python manage.py runserver' command, the 'manage.py' file will import the settings file as the 'settings' module from the same directory.

  


Worth noting at this point is that 'sys.path' includes the path '/usr/local/django/mysite', which is the directory the 'manage.py' and 'settings.py' are located in. This appears in 'sys.path' as it is standard behaviour of Python to add the directory that a script is contained in to 'sys.path' when a script is passed to Python to execute.

  


Moving on, after having imported the settings module, the 'manage.py' file will eventually call 'django.core.management.execute\_manager\(\)' where the argument supplied is the reference to the 'settings' module it just imported. The code for the 'execute\_manager\(\)' functions is as follows.
    
    
    def execute_manager(settings_mod, argv=None):  
       """  
       Like execute_from_command_line(), but for use by manage.py, a  
       project-specific django-admin.py utility.  
       """  
       setup_environ(settings_mod)  
       utility = ManagementUtility(argv)  
       utility.execute()

The first function called by this is 'setup\_environ\(\)'. This function does two important things.

  


The first thing the 'setup\_environ\(\)' function does is set the 'DJANGO\_SETTINGS\_MODULE' environment variable. Where as the settings module was originally imported as 'settings', the environment variable is instead referenced as a sub module of the package which is the Django site. Thus, instead of 'settings' it is referenced as 'mysite.settings' in this example.

  


The second thing that is done is that the parent directory of the site is added to 'sys.path'. That is, where the site directory is '/usr/local/django/mysite', the directory '/usr/local/django' is added. Having done that, the site package root is imported. For this example, this means that 'mysite' is imported. Immediately after this has been imported however, the directory which was added, ie., '/usr/local/django' in this case, is immediately removed from 'sys.path'.

  


After having does this initialisation, the 'execute\_manager\(\)' function creates an instance of the Django 'ManagementUtility' class. Control is then handed off to this class by calling the 'execute\(\)' method.

  


Delving down into the 'ManagementUtility' class, the next important function to be called is one called 'get\_commands\(\)' in the 'django.core.management' module.

  


What this function does is come up with a list of all the possible management commands. These can be management commands that are supplied as standard with Django, such as 'runserver', or can be management commands associated with installed Django applications for the site as listed in the 'INSTALLED\_APPS' variable of the settings module.

  


To get the 'INSTALLED\_APPS' variable however, it has to load the settings module. To get this the 'django.conf' module is imported and a global object called 'settings' within that module is accessed. That object isn't however the settings module itself, but an instance of the 'LazySettings' class.

  


This 'LazySettings' object acts as a wrapper around the actual settings module. So, it does still import the settings module, but also provides a mechanism for user code to configure various settings variables such that they will override those from the actual settings module.

  


Before it can do that however, it still has to import the original settings module. When it does this it ignores the fact that it was originally imported by the 'manage.py' command and instead loads the settings module based on the name which is recorded in the 'DJANGO\_SETTINGS\_MODULE' environment variable which was set above by the 'setup\_environ\(\)' function.

  


It is this section of code where the notorious error 'Could not import settings '%s' \(Is it on sys.path? Does it have syntax errors?\)' comes from that so often afflicts people using mod\_python and mod\_wsgi when the Python module search path isn't set up correctly or the Apache user doesn't have the appropriate permissions to read the file.

  


Anyway, this is where the second import of the settings module is triggered.

  


We aren't quite done however, as there are a couple of other important things that the initialisation of the settings object does which are worth mentioning.

  


The first is that if the 'INSTALLED\_APPS' uses a wildcard to refer to a group of applications contained with a module, then in order to enumerate what those applications are, the module containing them is imported to determine where the module is located. That directory is then scanned for sub directories and each of those is taken to be an actual application.

  


The second thing that is done is that if the 'TIME\_ZONE' variable is set within the settings module, then the 'TZ' environment variable is set and the 'time.tzset\(\)' function called.

  


Okay, we went on a little side trip there to understand what happens when the settings module is imported. As pointed out though, this had to be done to get that list of installed applications, including those enumerated when a wildcard was used. Having got that list, it is then possible to generate the list of commands that those installed applications provide.

  


To round out the picture, once the list of commands is generated it will for the case of 'python manage.py runserver' load the command for 'runserver'. This will result in 'django.core.management.commands.runserver' module being imported and control passed to it. The effect of that will be in this case to run the Django development server and start serving HTTP requests.

  


Although the command module for the 'runserver' command principally deals with creating an instance of the development web server, it also does a couple of other configuration related steps which may be significant when we come to talk about Apache/mod\_wsgi later.
    
    
    from django.conf import settings  
    from django.utils import translation  
    print "Validating models..."  
    self.validate(display_num_errors=True)  
    print "\nDjango version %s, using settings %r" % (django.get_version(), settings.SETTINGS_MODULE)  
    print "Development server is running at http://%s:%s/" % (addr, port)  
    print "Quit the server with %s." % quit_command  
      
    # django.core.management.base forces the locale to en-us. We should  
    # set it up correctly for the first request (particularly important  
    # in the "--noreload" case).  
    translation.activate(settings.LANGUAGE_CODE)

The first of these is that the models used by the application are validated. The second is that support for language locale is activated.

  


So, we have worked out why it is the settings file was imported twice. We have also worked out why the package root for the site has been able to be imported even though after the fact the parent directory of the site isn't listed in 'sys.path'. The analysis also shows that various other side effects can occur, including importing of parts of the application, validation of data models, setting up of the language locale and time zone setting.

  


Now let us compare all this to what happens when the WSGI interface is used under Apache/mod\_wsgi.

  


The guidance has always been that all you really needed to do for WSGI was to use:
    
    
    import os  
    import sys  
      
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'  
      
    import django.core.handlers.wsgi  
    application = django.core.handlers.wsgi.WSGIHandler()

That in itself is not necessarily going to be sufficient. This is because Python isn't going to know where to find 'mysite' when it goes to import the settings module unless it had been installed in the standard Python 'site-packages' directory, which is unlikely. Thus, what you really need is as follows.
    
    
    import os  
    import sys  
      
    sys.path.insert(0, '/usr/local/django')  
      
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'  
      
    import django.core.handlers.wsgi  
    application = django.core.handlers.wsgi.WSGIHandler()

That is, we have inserted the parent directory of the site into 'sys.path'.

  


The result now if we are to startup Apache/mod\_wsgi and make a request will be the following.
    
    
    __name__ = mysite.settings  
    __file__ = /usr/local/django/mysite/settings.pyc  
    os.getpid() = 3733  
    os.getcwd() = /Users/grahamd  
    os.curdir = .  
    sys.path = ['/usr/local/django', ...]  
    sys.modules.keys() = [..., 'mysite.settings', ..., 'mysite.os', ..., 'mysite.sys', ..., 'mysite', ...]  
    sys.modules.has_key('mysite') = True  
    sys.modules['mysite'].__name__ = mysite  
    sys.modules['mysite'].__file__ = /usr/local/django/mysite/__init__.pyc  
    os.environ['DJANGO_SETTINGS_MODULE'] = mysite.settings  
    

What is different?

  


First off there is only one process, but that is simply because there is no supervisor or monitor process to handle reloading like with the Django development server.

  


The second difference is that the settings module is only imported once and that is from the site package and not as a top level module. That is, it is imported as 'mysite.settings' and not 'settings'.

  


The final difference is that 'sys.path' lists '/usr/local/django' where as in the Django development server it listed '/usr/local/django/mysite'.

  


Remember though that with the Django development server the directory '/usr/local/django' was added to 'sys.path' but only long enough to have imported the 'mysite' package root for the site.

  


The consequence of the directory having been removed when using the Django development server, is that if you wanted to import Python packages from a sibling directory to the site directory, you would need to explicitly add it to the 'PYTHONPATH' variable in the user environment from which 'python manage.py runserver' was run.

  


In the case of using the WSGI interface directly as shown, the directory has to be included such that the settings module can be imported. Although by being added explicitly, it does mean that you have to be careful about what is contained in any sibling directories if you hadn't explicitly added the directory when using the Django development server. This is because those sibling directories will be considered when doing later module imports where as with Django development server they wouldn't.

  


The bigger issue in respect of the differences between 'sys.path' for each hosting mechanism is that under Apache/mod\_wsgi the directory '/usr/local/django/mysite' is missing.

  


Why this causes a problem is that when using the Django development server people become used to being able to reference parts of a site without needing to use the site package prefix. This is especially problematic when references are within strings in the URL mappings contained in 'urls.py' but can also occur for Python module imports as well where they are within a further subdirectory of the site. Where either is used, the code will fail if the site is migrated to run under Apache/mod\_wsgi.

  


Obviously, the way around that is in the WSGI script file used for Apache/mod\_wsgi to also add the directory '/usr/local/django/mysite' to 'sys.path', thus yielding the following.
    
    
    import os  
    import sys  
      
    sys.path.insert(0, '/usr/local/django/mysite')  
    sys.path.insert(0, '/usr/local/django')  
      
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'  
      
    import django.core.handlers.wsgi  
    application = django.core.handlers.wsgi.WSGIHandler()

It should be noted that having to do this highlights an arguable flaw in what Django permits when using the development server. This is because it is now possible to import the same module file via two different names. If naming isn't done consistently, you could end up with multiple copies of the module in memory and with any code within it being executed twice. If any code references global variables within the module, then different parts of the code may not end up accessing the same variable.

  


These points aside, is there anything else different between the Django development server and Apache/mod\_wsgi?

  


The obvious ones are that because the Django development server is never run, that the validation of the models and the setup of the language locale are never done.

  


More significant is that the Django 'ManagementUtility' class is never created and the list of available management commands is never calculated. This means that any implicit actions resulting from that are never performed.

  


The main side effect is that of initialisation of the settings object which wraps the settings module. As described, this sets up the timezone but also can cause additional module imports to be done as the installed applications have to be loaded when wildcards are used.

  


Because the settings object is so key to the operation of Django, it will still be initialised at a later point when required. Even so, there is still a potential difference due to the order in which things are done.

  


Even more problematic than the order though is the context in which the settings modules is finally loaded and the associated initialisation performed.

  


For the Django development server only a single thread is used and all the initialisation is done up front before any requests are handled.

  


In the case of Apache/mod\_wsgi where particular configurations can be multithreaded, the initialisation is only done within the context of the handling of the first request. While this is being done it is possible that a concurrent request could also be occurring.

  


If there is anything about the Django core code or the way in which user code makes use of it which is not completely thread safe, then there is a risk that multithreading could result in aspects of the settings and other global data being accessed before it is properly initialised from concurrent requests other than the one that got to trigger the initialisation.

  


One can only speculate on how such problems may manifest, but certainly it could explain a number of the odd problems people see when running under Apache/mod\_wsgi, especially where the application can be under load from the moment that a process gets restarted.

  


I am starting to run out of steam with this blog post, so lets just jump straight to a possible solution. This is in the form of the alternate WSGI script file contents below.
    
    
    import sys  
      
    sys.path.insert(0, '/usr/local/django/mysite')  
      
    import settings  
      
    import django.core.management  
    django.core.management.setup_environ(settings)  
    utility = django.core.management.ManagementUtility()  
    command = utility.fetch_command('runserver')  
      
    command.validate()  
      
    import django.conf  
    import django.utils  
      
    django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)  
      
    import django.core.handlers.wsgi  
      
    application = django.core.handlers.wsgi.WSGIHandler()

What this is doing is duplicating the way that Django development server is set up.

  


Key is that because an import lock is held when the WSGI script file is first imported, everything is done up front, effectively in the context of a single thread before any concurrent requests can start executing. This avoids all the problems with multithreading.

  


We also don't even set 'DJANGO\_SETTINGS\_MODULE' environment variable and instead leave it up to Django to set it just like with the Django development server. This does mean that the site directory is added to 'sys.path' and that the settings module has to be explicitly imported, with a subsequent second importing of the settings module by a different name, but this is exactly what the Django development server does. The temporary adding of the parent directory for the site into 'sys.path' to import the site package root is still even done by Django just as with the Django development server.

  


Further, the management command infrastructure is initialised and the loading of commands triggered by fetching the command object for 'runserver'. The validation of models is even triggered along with initialisation of the language locale.

  


After all that, we create the WSGI application entry point as normal and we are done.

  


All up, this should be nearly identical to what happens when the Django development server is used. About the only difference is that if 'python manage.py runserver' is used that the current working directory would usually be the site directory. Under Apache/mod\_wsgi the current working directory is going to be something else. But then, you shouldn't ever be using relative paths for file system resources anyway.

  


Anyway, my brain is about fried now.

  


If you know anything about the Django internals, I hope you find this interesting and will validate if my analysis is correct.

  


If you are having problems with porting code between the Django development server and Apache/mod\_wsgi, then perhaps you will give this alternate WSGI script file contents a go and see if things then work without problem.

  


Once I get sufficient feedback and validation that this is a better solution for the WSGI script file, then I will update the integration guide for Django on the mod\_wsgi site.

  


What would be nice though is if Django simply supplied a WSGI application entry point that could be supplied the site directory and which would internally simply ensure that everything is done correctly so that it behaves the same as the Django development server.

---

## Comments

### None - March 29, 2010 at 7:06 PM

I'm unable to completely remove the project name from app models imports under apache/wsgi. The projects are named differently in my development and production environments \(probably my first mistake\), so I need to be able to get the project name entirely out of the codebase.  
  
I can take it out completely in my development environment, but not with my apache/wsgi production environment. I've tried your recipe above, and no dice.  
  
Crucially, it only blows up with the custom comments app, and only in ONE SINGLE PLACE. I've got about five different "from comments.models import MyComment" statements in various parts of my code, and only in one templatetags library \('entry\_tags'\) am I obliged to type "from mysite.comments.models import MyComment", or else it complains:  
  
TemplateSyntaxError: 'entry\_tags' is not a valid tag library: Could not load template library from django.templatetags.entry\_tags, No module named models  
  
I suspect this is mostly a problem with how the custom comments apps work, but it does show up under wsgi only...

### Graham Dumpleton - March 29, 2010 at 7:50 PM

锁柱子. I would try the following two things.  
  
1\. Just to eliminate current working issues as a contributor, do "os.chdir\('/usr/local/django/mysite'\)", but with whatever your site directory is. Do this at start of WSGI script before any initialisation steps done.  
  
2\. Add somehow some debug code or something in your template tag library or template itself which dumps out what is the set of Python 'globals\(\)' and 'locals\(\)' in the context in which the template tag is used, plus 'sys.modules.keys\(\)' and 'sys.modules\['comments'\].\_\_file\_\_'. Maybe there is already a module loaded under that name or something in the context which is causing a problem. In other words a naming clash with that name already being used by something else.  
  
Appreciate that you could take this issue of yours other to the mod\_wsgi list so we can investigate further.

### Gustavo Narea - March 29, 2010 at 8:02 PM

Nice article, Graham\!  
  
I just wanted to say, I believe it'd be even better not to rely on Django's development server in the first place, to make sure the application under development is really portable.  
  
We use Paste Script and I know of some people of who use Cherrypy's server.  
  
Getting Django to work on Paste Script is now easier, thanks to twod.wsgi:  
http://packages.python.org/twod.wsgi/manual/paste-factory.html  
  
\- Gustavo.

### Graham Dumpleton - March 29, 2010 at 9:29 PM

Gustavo, that will not help because of some of the issues I raise.  
  
Part of the problem is that the Django WSGIHandler doesn't force up front initialisation of Django during setup of the WSGI server and/or loading of the WSGI script. Ie., where single threadedness is guaranteed. As a result in a multithreaded system, whether than be Apache/mod\_wsgi, Paste or CherryPy WSGI server, the lazy initialisation of Django within the context of a request, can be a potential problem where concurrent requests are executing.  
  
Unless twod.wsgi does something explicit to force upfront initialisation of Django before a request is actually handled, like I propose with my WSGI script changes, then it could also suffer some of the same odd problems that some people see for Apache/mod\_wsgi even if those other hosting mechanisms are used.  
  
FWIW, Apache/mod\_wsgi can also be used as a development platform for Django. One of the main reasons people use the Django development server is because of automatic code reloading, but that can also be done with Apache/mod\_wsgi.

### Graham Dumpleton - March 29, 2010 at 9:30 PM

锁柱子. Also:  
  
3\. Perform 'import comments' and just validate which module it is importing by dumping out '\_\_file\_\_' attribute of the module. This is in case it wasn't imported prior to 'from comments.models import ...'.

### Gustavo Narea - March 29, 2010 at 10:06 PM

Hi, Graham.  
  
As you say, it wouldn't try to fix those import errors. Which is why I think it's a better solution from a portability point of view:  
  
What I'm saying is that developers shouldn't rely on Django's development server because it does some magic under the hood and this sometimes affects portability. Therefore I suggest to use a Django-agnostic development server; any server.  
  
If an application is broken under mod\_wsgi, it will likely be broken on any other server but it may still work under Django's.  
  
I wouldn't like to work around this problem by making my mod\_wsgi script more complex. Specially because the API used may change or the steps to be performed may be different in future releases.  
  
Of course, if Django offered a single function to run that routine, I wouldn't mind calling it from my WSGI script.  
  
Cheers,  
  
\- Gustavo.

### Doug Blank - March 29, 2010 at 11:14 PM

Thank you for the detailed explanation of what actually happens with these two systems. A shortened, explanation-oriented version would be useful in the django docs. And fixing these differences would be useful too. Is there a django ticket for this?

### Doug - March 30, 2010 at 12:39 AM

I stopped using manage.py a long time ago because of the whole double settings approach it takes.  
  
I setup my project environment with an alias to django-admin.py "da" and a properly set DJANGO\_SETTINGS\_MODULE.  
  
That ends up working just fine.  
  
The one thing I never figured out with mod\_wsgi was how to get multiple web apps running with different timezone settings. The last one initialized always seemed to win.

### Graham Dumpleton - March 30, 2010 at 8:35 AM

Foo. To fix timezone issue you must use mod\_wsgi daemon mode and delegate each Django instance to run in a separate daemon process group. There is simply no other way as you can't run two different application instances in same process that want different timezone settings. The separation offered by using multiple Python sub interpreters in the same process is not enough as the timezone setting is process wide.

### Carl - April 7, 2010 at 6:18 AM

This is very helpful, thanks for the sleuthing.  
  
As Foo mentioned, there's a distinction between manage.py and runserver. You conflated the two in your post, but in fact if you set DJANGO\_SETTINGS\_MODULE in the environment and use "django-admin.py runserver", the double-import of settings.py goes away.  
  
I'm not sure how that affects the thread-safety issues you discuss, but to the extent that it is possible I think a solution that involves modifying how I invoke runserver is preferable to one that inserts cruft into my WSGI script.

### Graham Dumpleton - April 7, 2010 at 10:37 AM

Carl. Thanks, I didn't note the importance of what Foo said as I didn't know that one could use 'django-admin.py' to do that. Thus why when I meant 'runserver' I always was meaning 'python manage.py runserver'. They are still both executing the same internal Django development server by the same mechanism.  
  
The differences are that 'django-admin.py' relies on DJANGO\_SETTINGS\_MODULE and PYTHONPATH being set in environment. As such, it is more aligned with what mod\_python and mod\_wsgi in that that is effectively what they require. This extends to the double import going away and the parent directory being permanently in sys.path and the site directory not at all in sys.path.  
  
This is part of my gripe, that there are multiple ways of starting things up and because what is set up is different in each case leads to issues with code not working when moved to a different way of doing the hosting.  
  
For example, don't use the site name in 'urls.py' and use 'manage.py' and it will work. Do that with 'django-admin.py' and I believe it would fail as the site directory isn't in 'sys.path'.  
  
Anyway, using 'django-admin.py' may well be better if wanting more guarantees of portability to other hosting mechanisms as far as Python path issues, however it isn't going to help with the other stuff I raised as both methods still do those extra bits related to the management utility instance and command loading which WSGI approach doesn't do if documented method used. You still also have the issue of setup in multithreaded context within context of request if you use original WSGIHandler instance only and don't force setup when WSGI script loaded.  
  
Seems I may have to do a followup now showing how 'django-admin.py' results in a third variation in how the environment is setup.  
  
BTW, the Django tutorial seems to always use 'python manage.py runserver'. I would say therefore that this is what the majority use and most probably don't realise you can use 'django-admin.py' in similarly way providing configuration set up in user environment correctly.

### Steven Klass - May 14, 2010 at 10:58 PM

Wow. You helped me to understand this at a much deeper level. Thanks for taking the time to document it. I wasn't dealing with WSGI so much as just the way in which the --noreload affects \(or rather f\*xks\) with the settings loading.   
  
My thoughts --noreload is the only way to go unless you explicitly use it in combinatin of --settings. What's worse is the different behavior depending on whether you call it from manage.py or django-admin.py. Grumble Grumble Grumble.   
  
I am simply floored this hasn't been better documented.

### Art Botterell - June 29, 2010 at 3:25 PM

Huge thanks for this, Graham\!

### Graham Dumpleton - June 29, 2010 at 3:32 PM

@Art. Would you be able to add what sort of problem this has helped you solve. There is still a bit of a debate with Django devs over what this is actually helping solve. It certainly is fixing issues for some people, but there is a question over whether it is merely covering up where users aren't actually doing things by the book as far as how it is documented Django should work. Thus, as much information as possible about any issue you were having which this has fixed would be appreciated. If too hard to post details as blog comment, come over to the mod\_wsgi mailing list.

### Jörn - November 8, 2010 at 9:18 PM

Hi Graham,  
  
thanks a lot for this detailed post.  
  
It helped us A LOT to fix a big issues on our webservers.  
  
Our setup:  
\- multiple VirtualHosts on Apache  
\- each host serves one django site  
\- we run different versions of django \(1.02, 1.1 and 1.2\)  
\- we don't use virtualenv, we normally set up sys.path  
\- a site.wsgi file like recommended here:  
http://code.djangoproject.com/wiki/django\_apache\_and\_mod\_wsgi and here:  
http://code.google.com/p/modwsgi/wiki/IntegrationWithDjango  
  
The problem:  
\- sporadically I received error mails with weird errors: the request path of site A threw an error with a path only available on site B  
\- I set up an test page showing all our hosts within iFrames. A \(concurrent\) refresh showed the problem: the server mixed up the sites and sometime even combined parts of the different sites.  
  
The theory:  
\- concurrent requests mess up the import of different setting.py's  
  
The solution:  
\- your post and your "possible solutions" fixed the problem.  
  
This configuration should really be recommended on the mentioned sites.  
  
Thanks again\!  
  
Best  
Jörn

### Graham Dumpleton - November 8, 2010 at 9:23 PM

Jörn, it is referenced from page on mod\_wsgi site, albeit was only added in the last day or so. The modified WSGI script file should not have helped with your problem. I'd suggest that you might have an underlying Apache configuration problem. You are best off using daemon mode for a start and delegate each Django site to it's own daemon process. You can look at the WSGI request environment to validate whether instance running in correct daemon process group and interpreter.

### Jörn - November 8, 2010 at 9:33 PM

Hi Graham,  
  
obviously the different "import approach" fixed our problem.   
Instead of the officially recommend:  
```
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'  
```  
we import settings explicitly \(our .wsgi file is located in PROJECT\_ROOT/apache/site.wsgi\):  
```  
APACHE_DIR = os.path.dirname(os.path.abspath(__file__))  
PROJECT_ROOT = os.path.abspath("%s/.." % APACHE_DIR)  
DJANGO_SITES, SITE = os.path.split(PROJECT_ROOT)  
SITE_PACKAGES = os.path.abspath("%s/../site-packages-1.1" % DJANGO_SITES)  
  
sys.path.insert(0, PROJECT_ROOT)  
sys.path.insert(0, DJANGO_SITES)  
sys.path.insert(0, SITE_PACKAGES)  
  
import settings_productive  
import django.core.management  
django.core.management.setup_environ(settings_productive)  
```  
The daemon mode is the next configuration change we will do anyway.   
  
Best  
Jörn

### MidGe - November 21, 2010 at 9:11 PM

Great Post\! Thank you\!  
  
It isn't very often that a search for a troubleshooting issue suggests a link to such a well documented answer. And it works\!  
  
Thanks again\!

### bvce - December 14, 2010 at 10:30 PM

Graham,  
Thank you very much for this post. Trying to make configuration for wsgi with apcahe was hardly imposible.... with your help, fixed in minutes.  
Thanks for your time and effort.  
bvcelari

### Graham Dumpleton - December 14, 2010 at 10:45 PM

@bvcelari  
  
Problem is that this alternate script is really a workaround. Django devs think it should not be needed and that if it is then users are using Django wrongly.  
  
Thus, using the script could be masking a problem in your code which might come back and bight you in other ways.

### primeq - January 7, 2011 at 2:13 PM

Django is great. Python is great. But when you need to give your life to something to make it work a lot of people will just walk.  
  
You may be right with "Django devs think it should not be needed ...then users are using Django wrongly", but there's a sure way to fix it - said Django devs should post a guaranteed-to-work, self-contained example \(not there, too many implicit assumptions made\).  
  
Your post is pure gold. When I start working on something, result is everything to begin with, and then I go back and mess with it every which way, breaking stuff to figure out the mechanics behind the scene.  
  
Your post got me there making it work. Django can be like Linux - great x10^6, but it's possible to lose a lot of people because the knowledge needed to be a self-helper is a barrier too many people won't manage to cross. There's no shame in making something clear \(and wsgi/django usage is not clear to anyone without making an investment we don't all have time for\). Seems you had the time and inclination - and I thank your for this effort, even it if is a workaround as you say.

### Graham Dumpleton - January 7, 2011 at 2:16 PM

@primeq A lot of this could be sorted if someone could just supply me with a relatively small Django site example which exhibits the sort of problem, reasonably reliably, that this alternate way of doing things is fixing. If had that, then could identify the cause and potentially what, if anything, that people are doing wrong and then ensure the Django folks document it as bad practice and prone to failure. Am still waiting though for that example site to be able to do that. :-\(

### None - January 18, 2011 at 12:33 AM

It has saved my day =\] Thanks so much, it really works fine.

### Unknown - January 25, 2011 at 10:46 AM

Please note that there is also an outstanding Django bug \([\#12464](http://code.djangoproject.com/ticket/12464)\) which causes URL problems when the WSGI alias is "/path" \(i.e., not /\) and the URL request path is "/path" \(i.e., no trailing slash\). The only solution in that case seems to be to add a redirect in Apache from "/path" to "/path/".

### Graham Dumpleton - January 25, 2011 at 2:01 PM

David, that bug as I can see though has got nothing to do with what the blog post is about, so not sure why you are mentioning it here.

### Unknown - January 26, 2011 at 3:49 AM

Graham, sorry, you're right -- my comment was really meant for the Django Integration page on the mod\_wsgi wiki, but I could not comment there, and I got to this blog post from a link in that article. After I tried the solution here and it didn't solve my problem, I did some more searching and found the Django bug report. Your blog post has obviously helped a number of people, but I thought you might want to the mention the other issue, since if that's the problem, the workaround doesn't involve changing the WSGI script.

### Graham Dumpleton - January 26, 2011 at 8:50 AM

David, highlighting things like that is what the mod\_wsgi mailing list is for. Details of mailing list on mod\_wsgi site wiki.

### Graham Dumpleton - January 26, 2011 at 12:59 PM

David, I hope you are following my updates on that Django ticket you pointed out. It is frightfully more complicated than you think it is. ;-\)

### Unknown - January 26, 2011 at 2:48 PM

Touche\! I hope this issue gets some attention from Django core developers. The docstring of get\_script\_name\(\) actually makes mention of a DJANGO\_USE\_POST\_REWRITE setting which isn't even used in the function -- there's no reference to it anywhere in the code base, nor on the users or developers lists.

### danols - February 7, 2011 at 11:27 AM

This comment has been removed by a blog administrator.

### danols - February 7, 2011 at 4:40 PM

This comment has been removed by a blog administrator.

### Unknown - March 29, 2011 at 8:54 PM

Dear Graham,  
  
Thanks for the excellent blog. I just needed to add the path line of the parent directory of the directory that contains settings.py and everything worked like a charm.  
  
Do media files automatically get served by apache once everything is setup? I did not expect this to be the case. Kindly do let me know.  
  
Thanks once again.  
  
Yours sincerely,  
nav

### Graham Dumpleton - March 29, 2011 at 9:14 PM

If you have any further issues/comments with this blog post, please use the mod\_wsgi mailing list. Thanks.

### Unknown - April 16, 2011 at 5:33 AM

I'm unable to completely remove the project name from app models imports under apache/wsgi. The projects are named differently in my development and production environments \(probably my first mistake\), so I need to be able to get the project name entirely out of the codebase.  
  
I can take it out completely in my development environment, but not with my apache/wsgi production environment. I've tried your recipe above, and no dice.  
  
I have this same problem too.  
\---------------------  
[alliance leveling guide](http://alliancelevelingguidex.com/)

### ruffyleaf - July 29, 2011 at 5:29 PM

"What would be nice though is if Django simply supplied a WSGI application entry point that could be supplied the site directory and which would internally simply ensure that everything is done correctly so that it behaves the same as the Django development server."  
  
YES\!\!\! The best is if we don't have to do any configuration at all. At least minimal configuration.

### Erik - March 29, 2012 at 1:21 PM

Graham,  
  
From your presentation at:  
  
http://blip.tv/pycon-australia/getting-started-with-apache-mod\_wsgi-3859481  
  
you seemed to hope that future Django releases might make this preloading work unnecessary. Is this true for Django 1.3.1 with mod\_wsgi 3.3.1?  
  
Thanks for all your work\!  
  
Erik

### Graham Dumpleton - March 29, 2012 at 1:25 PM

Erik. They have done some cleanup of WSGI application entry point in latest version. They now generate a wsgi.py file and have eliminated I think the double import. They still don't preload by way of triggering management commands.

### Marcp - December 19, 2013 at 2:41 AM

the alternate file you provided isn't working for me on windows with apache configured as "Apache/2.2.17 \(Win32\) mod\_ssl/2.2.17 OpenSSL/0.9.8o mod\_wsgi/3.3 Python/2.7.6 PHP/5.3.4 mod\_perl/2.0.4 Perl/v5.10.1", I get an error on the "import settings" line, stating "ImportError: No module named settings"

### Graham Dumpleton - December 19, 2013 at 2:25 PM

This post related to an old version of Django and may not be completely accurate for newer versions of Django. It may not even be appropriate for newer Django versions, so why specifically are you trying it.  
  
The code would also possibly be dependent on both the project directory and its parent being on sys.path for module imports to work, something which is discouraged in recent Django versions.  
  
Comments on a blog post are also a very bad forum for trying to solve problems. If there is specific reason you are trying this when using mod\_wsgi, then use the mod\_wsgi mailing list.

### Unknown - April 8, 2016 at 9:17 AM

I must say that I am incredibly grateful that there are those as yourself out there who take the time to share what they know on a subject.... I thank you profusely for going through this... now I just have to say... Oh my god. Please get to the point\! haha. For those of us who just want an enumeration of the differences and how to solve the problem \(because we don't care about being Django mod\_wsgi experts and may not ever set up a site like this again\) this is a nightmare of overkill information that we just don't need. in todays incredible overload of information, especially when it comes to developers, this just makes my heart sink and my stomach sick when I have to read something like this to solve such a simple problem. Anyway, I'm sure lots of people out there will flame me for making this comment, and again I really appreciate the work that you have done, but now I get to stay at the office for a few hours while I comb through this post and become an expert on something I don't need to be in order to solve my simple problem. Ugh.

### Graham Dumpleton - April 8, 2016 at 9:40 AM

@Jason Wolfe: If you are still having issues which even necessitate needing to know this I would be surprised. My understanding is that Django versions since this was posted have been changed and so a lot of the information here is not really relevant now. I certainly wouldn't be copy and pasting any code snippets from here to use and expect them to work with newer Django versions.

### Da Tijuca pra Albuquerque - December 15, 2016 at 11:57 AM

@Graham Dumpleton I'm grateful too for you and this posting. \(In\)fortunately, like you mention much has changed since, but I'm still having problems with getting my application URLs included by Django and served by mod\_wsgi. I cannot find help. Could you point me to a newer posting or solution? It runs great witn runserver.  
  
Thanks\!

### Graham Dumpleton - December 15, 2016 at 12:08 PM

If it is related to Django, possibly better to ask on StackOverflow or the Django users mailing list. If it is a mod\_wsgi issue, use the mod\_wsgi mailing list.

