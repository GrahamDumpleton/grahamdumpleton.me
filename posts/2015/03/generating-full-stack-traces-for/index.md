---
title: "Generating full stack traces for exceptions in Python."
author: "Graham Dumpleton"
date: "Saturday, March 21, 2015"
url: "http://blog.dscpl.com.au/2015/03/generating-full-stack-traces-for.html"
post_id: "7672746776551574219"
blog_id: "2363643920942057324"
tags: ['python']
comments: 10
published_timestamp: "2015-03-21T23:36:00+11:00"
blog_title: "Graham Dumpleton"
---

My last few blog posts have been about monkey patching. I will be continuing with more posts on that topic, but I am going to take a slight detour away from that topic in this post to talk about a problem related to capturing stack trace information for exceptions in Python applications.

This does still have some relevance to monkey patching, in as much as one of the reasons you may want to monkey patch a Python application is to add in wrappers which will intercept the the details of an exception raised deep with an application. You might want to do this for the case where the exception would otherwise be captured by an application and translated into a different exception, with loss of information about the inner exception, or in the case of a web application result in a generic HTTP 500 web page response with no useful information captured. So monkey patching can be a useful debugging tool where it may not be convenient to modify the original source code of the application.

# Tracebacks for exceptions

To get started, lets consider the following Python script:

```python
    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    function2()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

If we run this script we will get:

```
    Traceback (most recent call last):  
    File "generate-1.py", line 16, in <module>  
    function5()  
    File "generate-1.py", line 14, in function5  
    function4()  
    File "generate-1.py", line 11, in function4  
    function3()  
    File "generate-1.py", line 8, in function3  
    function2()  
    File "generate-1.py", line 5, in function2  
    function1()  
    File "generate-1.py", line 2, in function1  
    raise RuntimeError('xxx')  
    RuntimeError: xxx
```

In this case we have an exception occurring which was never actually caught within the script itself and is propagated all the way up to the top level, causing the script to be terminated and the traceback printed.

When the traceback was printed, it showed all stack frames from the top level all the way down to the point where the exception occurred.

Now consider the Python script:

```python
    import traceback

    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    try:  
    function2()  
    except Exception:  
    traceback.print_exc()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

In this script we have a 'try/except' block half way down the sequence of calls. The call to 'function2\(\)' is made within the 'try' block and when the exception is raised, it is handled within the 'except' block. At that point we use the 'traceback.print\_exc\(\)' function to output the details of the exception, but then let the script continue on normally to completion.

For this Python script the output is:

```
    Traceback (most recent call last):  
    File "generate-2.py", line 11, in function3  
    function2()  
    File "generate-2.py", line 7, in function2  
    function1()  
    File "generate-2.py", line 4, in function1  
    raise RuntimeError('xxx')  
    RuntimeError: xxx
```

What you see here though is that we loose information about the outer stack frames for the sequence of calls that led down to the point where the 'try/except' block existed.

When we want to capture details of an exception for logging purposes so as to later debug an issue, this loss of information can make it harder to debug a problem if the function containing the 'try/except' block could be called from multiple places.

How then can we capture the outer stack frames so we have that additional context?

# Capturing the current stack

There are a number of ways of obtaining information about the current stack. If we are just wanting to dump out the current stack to a log then we can use 'traceback.print\_stack\(\)'.

```python
    import traceback

    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    try:  
    function2()  
    except Exception:  
    traceback.print_stack()  
    print '--------------'  
    traceback.print_exc()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

Run this variant of the Python script and we now get:

```
      File "generate-3.py", line 23, in <module>  
    function5()  
    File "generate-3.py", line 21, in function5  
    function4()  
    File "generate-3.py", line 18, in function4  
    function3()  
    File "generate-3.py", line 13, in function3  
    traceback.print_stack()  
    --------------  
    Traceback (most recent call last):  
    File "generate-3.py", line 11, in function3  
    function2()  
    File "generate-3.py", line 7, in function2  
    function1()  
    File "generate-3.py", line 4, in function1  
    raise RuntimeError('xxx')  
    RuntimeError: xxx
```

So we now have the inner stack frames corresponding to the exception traceback, as well as those outer stack frames corresponding to the current stack. From this we can presumably now join these two sets of stack frames together and get a complete stack trace for where the exception occurred.

If you look closely though you may notice something. That is that there is actually an overlap in the stack frames which are shown for each, plus that the function we have called to print the current stack is also shown.

In the case of the overlap the issue is that in the inner stack frames from the traceback, it shows an execution point in 'function3\(\)' of line 11. This corresponds to the point where 'function2\(\)' was called within the 'try' block and in which the exception occurred.

At the same time, the outer stack frames from the current execution stack show line 13 in 'function3\(\)', which is the point within the 'except' block where we called 'traceback.print\_stack\(\)' to display the current stack.

So the top most stack frame from the traceback is actually want we want and we need to ignore the bottom most two stack frames from the current stack if we were to join these together.

Now although the output of these two functions can be directed to any file like object and thus an instance of 'StringIO' could be used to capture the output, we would still need to break apart the formatted text output, drop certain parts and rearrange others to get the final desired result.

Dealing with such pre formatted output could therefore be a pain, especially if what we really wanted was the raw information about the filename, line number, function and potentially the code snippet. What other options therefore exist for getting such raw information?

# Using the inspect module

When needing to perform introspection or otherwise derive information about Python objects, the module you want to use is the 'inspect' module. For the case of getting information about the current exception and current stack, the two functions you can use are 'inspect.trace\(\)' and 'inspect.stack\(\)'. Using these we can rewrite our Python script as:

```python
    import inspect

    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    try:  
    function2()  
    except Exception:  
    for item in reversed(inspect.stack()):  
    print item[1:]  
    print '--------------'  
    for item in inspect.trace():  
    print item[1:]

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

This time we get:
    
    
    ('generate-4.py', 25, '<module>', ['function5()\n'], 0)  
    ('generate-4.py', 23, 'function5', [' function4()\n'], 0)  
    ('generate-4.py', 20, 'function4', [' function3()\n'], 0)  
    ('generate-4.py', 13, 'function3', [' for item in reversed(inspect.stack()):\n'], 0)  
    --------------  
    ('generate-4.py', 11, 'function3', [' function2()\n'], 0)  
    ('generate-4.py', 7, 'function2', [' function1()\n'], 0)  
    ('generate-4.py', 4, 'function1', [" raise RuntimeError('xxx')\n"], 0)

So these functions provide us with the raw information rather than pre formatted text, thus making it easier to process. For each stack frame we also get a reference to the frame object itself, but since we didn't care about that we skipped it when displaying each frame.

Because though we might want to generate such a combined stack trace in multiple places we obviously separate this out into a function of its own.

```python
    import inspect

    def print_full_stack():  
    print 'Traceback (most recent call last):'  
    for item in reversed(inspect.stack()[2:]):  
    print ' File "{1}", line {2}, in {3}\n'.format(*item),  
    for line in item[4]:  
    print ' ' + line.lstrip(),  
    for item in inspect.trace():  
    print ' File "{1}", line {2}, in {3}\n'.format(*item),  
    for line in item[4]:  
    print ' ' + line.lstrip(),

    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    try:  
    function2()  
    except Exception:  
    print_full_stack()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

The final result would now be:

```
    Traceback (most recent call last):  
    File "generate-5.py", line 32, in <module>  
    function5()  
    File "generate-5.py", line 30, in function5  
    function4()  
    File "generate-5.py", line 27, in function4  
    function3()  
    File "generate-5.py", line 22, in function3  
    function2()  
    File "generate-5.py", line 18, in function2  
    function1()  
    File "generate-5.py", line 15, in function1  
    raise RuntimeError('xxx')
```

# Using the exception traceback

We are done right? No.

In this case we have relied on functions from the 'inspect' module that rely on being called directly from within the 'except' block.

That is, for generating the outer stack frames for the current stack we always assume that we need to drop two stack frames from the result of calling 'inspect.stack\(\)'.

For the inner stack frames from the exception, the 'inspect.trace\(\)' function relies on there being an exception which is currently being handled.

That we are assuming we should skip two stack frames for the current stack is a little bit fragile. For example, consider the case where we don't actually call 'print\_full\_stack\(\)' within the 'except' block itself.

```python
    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3a():  
    print_full_stack()

    def function3():  
    try:  
    function2()  
    except Exception:  
    function3a()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

The result here is:

```
    Traceback (most recent call last):  
    File "generate-6.py", line 35, in <module>  
    function5()  
    File "generate-6.py", line 33, in function5  
    function4()  
    File "generate-6.py", line 30, in function4  
    function3()  
    File "generate-6.py", line 27, in function3  
    function3a()  
    File "generate-6.py", line 25, in function3  
    function2()  
    File "generate-6.py", line 18, in function2  
    function1()  
    File "generate-6.py", line 15, in function1  
    raise RuntimeError('xxx')
```

As can be seen, we actually end up with an additional stack frame being inserted corresponding to 'function3a\(\)' which we called within the 'except' block and which in turn called 'print\_full\_stack\(\)'.

To ensure we do the right thing here we need to look at what 'inspect.stack\(\)' and 'inspect.trace\(\)' actually do.

```python
    def stack(context=1):  
    """Return a list of records for the stack above the caller's frame."""  
    return getouterframes(sys._getframe(1), context)

    def trace(context=1):  
    """Return a list of records for the stack below the current exception."""  
    return getinnerframes(sys.exc_info()[2], context)
```

So the problem we have with the extra stack frame is that 'inspect.stack\(\)' uses 'sys.\_getframe\(\)' to grab the current stack. This is correct and what it is intended to do, but not really what we want. What we instead want is the outer stack frames corresponding to where the exception was caught.

As it turns out this is available as an attribute on the traceback object for the exception called 'tb\_frame'. Learning from how these two functions are implemented, we can therefore change our function to print the full stack.

```python
    import sys  
    import inspect

    def print_full_stack(tb=None):  
    if tb is None:  
    tb = sys.exc_info()[2]

        print 'Traceback (most recent call last):'  
    for item in reversed(inspect.getouterframes(tb.tb_frame)[1:]):  
    print ' File "{1}", line {2}, in {3}\n'.format(*item),  
    for line in item[4]:  
    print ' ' + line.lstrip(),  
    for item in inspect.getinnerframes(tb):  
    print ' File "{1}", line {2}, in {3}\n'.format(*item),  
    for line in item[4]:  
    print ' ' + line.lstrip(),

    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3a():  
    print_full_stack()

    def function3():  
    try:  
    function2()  
    except Exception:  
    function3a()

    def function4():  
    function3()

    def function5():  
    function4()

    function5()
```

We are now back to the desired result we are after.

```
    Traceback (most recent call last):  
    File "generate-7.py", line 39, in <module>  
    function5()  
    File "generate-7.py", line 37, in function5  
    function4()  
    File "generate-7.py", line 34, in function4  
    function3()  
    File "generate-7.py", line 29, in function3  
    function2()  
    File "generate-7.py", line 22, in function2  
    function1()  
    File "generate-7.py", line 19, in function1  
    raise RuntimeError('xxx')
```

# Using a saved traceback

In making this last modification we actually implemented 'print\_full\_stack\(\)' to optionally accept an existing traceback. If none was supplied then we would instead use the traceback for the current exception being handled.

It is likely a rare situation where it would be required, but this allows one to pass in a traceback object which had been saved away and retained beyond the life of the 'try/except' block which generated it.

Be aware though that doing this can generate some surprising results.

```python
    def function1():  
    raise RuntimeError('xxx')

    def function2():  
    function1()

    def function3():  
    try:  
    function2()  
    except Exception:  
    return sys.exc_info()[2]

    def function4():  
    tb = function3()  
    print_full_stack(tb)

    def function5():  
    function4()

    function5()
```

In this case we return the traceback to an outer scope and only within that outer function attempt to print out the full stack for the exception.

```
    Traceback (most recent call last):  
    File "generate-8.py", line 37, in <module>  
    function5()  
    File "generate-8.py", line 35, in function5  
    function4()  
    File "generate-8.py", line 32, in function4  
    print_full_stack(tb)  
    File "generate-8.py", line 26, in function3  
    function2()  
    File "generate-8.py", line 22, in function2  
    function1()  
    File "generate-8.py", line 19, in function1  
    raise RuntimeError('xxx')
```

The problem here is that in 'function4\(\)' rather than seeing the line where the call to 'function3\(\)' was made, we see where the call to 'print\_full\_stack\(\)' is made.

The reason for this is that although the traceback contains a snapshot of information from the current stack at the time of the exception, this only extends back as far as the 'try/except' block.

When we are accessing 'tb.tb\_frame' and getting the outer frames, it is still accessing potentially active stack frames for any currently executing code.

So what has happened is that in looking at the stack frame for 'function4\(\)' it is picking up the current execution line number at that point in time, which has shifted from the time when the original exception occurred. That is, control returned back into 'function4\(\)' and execution progressed to the next line and the call 'print\_full\_stack\(\)'.

Although the ability to print the full stack trace for the exception is useful, it is only reliable if called within the same function that the 'try/except' block existed. If you return the traceback object to an outer function and then try and produce the full stack, line number information in the outer stack frames can be wrong, due to the code execution point within those functions shifting if subsequent code in those functions had been executed since the exception occurred.

If anyone knows a way around this, beyond creating a snapshot of the full stack within the same function as where the 'try/except' occurred, I would be interested to hear how. My current understanding is that there isn't any way and it is just a limitation one has to live with in that case.

---

## Comments

### Deron Meranda - March 22, 2015 at 3:49 AM

Also, what about Python 3's Exception Chaining \(PEP 3134\)?  
  
I have a library that provides hooks via user-supplied callbacks; and if the callback raises an exception, it gets repackaged in my own exception type with a chain to the original exception. To allow the library to work in both Python 2 and 3 \(even with 2to3\) I manually construct the chain, such as this in Python 2 syntax:  
  
try:  
call\_callback\(\)  
except Exception, err:  
e2 = sys.exc\_info\(\)  
newerr = MyException\( ..stuff.. \)  
newerr.\_\_cause\_\_ = err  
newerr.\_\_traceback\_\_ = e2\[2\]  
raise newerr  
  
Is this a good method, or am I loosing information?

### Graham Dumpleton - March 23, 2015 at 9:55 AM

With chaining of exceptions, because the traceback of initial exceptions would be retained beyond the life of the try/except for those when re-raising a different exception, I would imaging the issue described with line numbers not then being accurate for the outer stack frames would apply.

### Piotr Dobrogost - March 26, 2015 at 9:30 PM

It seems _creating a snapshot of the full stack within the same function as where the 'try/except' occurred_ is really the only way to provide full context of exception. The question is why Python itself does not do this and attach this snapshot to exception? I guess this might be to avoid cost of taking snapshot. If this is the case then Python should provide hook called every time a catch clause is entered. Related is http://stackoverflow.com/questions/1029318/calling-a-hook-function-every-time-an-exception-is-raised. I encourage you to take this problem to python-ideas to see if there's a chance of improving this aspect of language. Stack trace is crucial information and Python should really provide easy way to get it.  
  
I'm also wondering if \(contrary to Alex Martelli's statement in above SO thread\) you found a way to monkey patch Python itself, obtaining missing hook I described above as result...

### Graham Dumpleton - March 26, 2015 at 9:45 PM

No, there is no one way of being able to patch Python at that level without changing the C code of the interpreter itself.

### Piotr Dobrogost - March 27, 2015 at 2:10 AM

And what do you think about idea of Python provided hook called upon entering except/finally block?

### Graham Dumpleton - March 27, 2015 at 11:52 AM

One could possibly argue the case for a sys.setexcept\(\)/sys.getexpect\(\) hooking mechanism in the same vain as those for profile and trace call backs, but would want to see the good use case for it.  
  
A problem noted on SO is how you distinguish an internal implementation detail where the exception is caught and suppressed automatically such as StopIteration, AttributeError on getattr\(\) failure etc etc.  
  
Having a callback could easily lead to making it easy for users to cause problems if used poorly, but then that situation exists with the profile and trace hooks now.  
  
So am not fore or against.

### guettli - June 5, 2015 at 4:30 PM

I wanted to see the upper frames some months ago. The issue I created was solved in Python3. I never tried the solution since I am still fixed on Python2. Issue: https://bugs.python.org/issue9427

### None - February 3, 2017 at 1:22 PM

I had the same problem last day, but worse because of threading  
  
Here my solution:  
  
def get\_stack\(skip=1, tb=None\):  
stack = traceback.extract\_stack\(\)\[:-\(1+skip\)\]  
  
\# if we are in a properly created thread, preprend the thread stack  
if hasattr\(threading.current\_thread\(\), "\_stack"\):  
stack = getattr\(threading.current\_thread\(\), "\_stack"\) + stack  
  
\# Remove threading init calls  
threading\_lib\_path = threading.\_\_file\_\_.rstrip\("c"\)  
stack = filter\(lambda x : x\[0\] \!= threading\_lib\_path, stack\)  
  
if tb:  
stack += tb  
else:  
\# complete stack with the real exception launcher if exists  
err\_tb = sys.exc\_info\(\)\[2\]  
if err\_tb is not None:  
stack += traceback.extract\_tb\(err\_tb\)  
del err\_tb  
  
\#return result  
return stack  
  
def create\_thread\(\*args, \*\*kwargs\):  
thread = threading.Thread\(\*args, \*\*kwargs\)  
setattr\(thread, "\_stack", get\_stack\(\)\)  
return thread  
  
  
It's far from perfect, but I don't know make better  
I hope it can help someone

### Delgan - November 1, 2017 at 12:50 AM

Hi, thanks for this article which helped me to better understand how traceback, stacks and exceptions work in Python.  
  
One possible and elegant solution to the problem is to walk back trough the stack and create fake tracebacks which could be preprended to the actual traceback got from "sys.exc\_info". That way, the traceback starts from the root and continues to the error fluently.  
  
This is described in this StackOverflow answer: https://stackoverflow.com/a/13210518/2291710  
  
I actually implemented it before I saw the SO question, it looked like this:  
  
_  
class fake\_traceback:  
  
def \_\_init\_\_\(self, frame, lasti, lineno, next\_=None\):  
self.tb\_frame = frame  
self.tb\_lasti = lasti  
self.tb\_lineno = lineno  
self.tb\_next = next\_  
  
def function3\(\):  
try:  
function2\(\)  
except:  
etype, ex, tb = sys.exc\_info\(\)  
tb = fake\_traceback\(tb.tb\_frame, tb.tb\_lasti, tb.tb\_lineno, tb.tb\_next\)  
frame = tb.tb\_frame.f\_back  
while frame:  
tb = fake\_traceback\(frame, frame.f\_lasti, frame.f\_lineno, tb\)  
frame = frame.f\_back  
  
print\(''.join\(traceback.format\_tb\(tb\)\)\)  
_

### Michael Herrmann - March 30, 2018 at 3:51 AM

I encountered this problem while developing a GUI app with PyQt. For other people with the same setup, I wrote a [blog post](https://fman.io/blog/pyqt-excepthook/) with a solution mirroring the one by Adrien above. Maybe it will spare someone the hours I just spent\!

