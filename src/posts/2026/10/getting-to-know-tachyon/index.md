---
title: "Getting to know Tachyon"
description: "A set of hands-on JupyterLab workshops for Tachyon, the sampling profiler in Python 3.15, and the story of why I wrote them to learn it myself."
date: 2026-10-01
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/tachyon-workshops"
tags: ["python", "profiling", "jupyter", "wrapture"]
---

Python 3.15 ships with a new profiler. It is called Tachyon, it lives in the standard library as the `profiling.sampling` module, and unlike cProfile it is a sampling profiler rather than a tracing one. I now have a set of hands-on workshops for it, which you can find at [github.com/GrahamDumpleton/tachyon-workshops](https://github.com/GrahamDumpleton/tachyon-workshops) or on the [workshops page](/workshops/tachyon/) of this site, and they have reached the point where I am happy for other people to do them. That said, they were not written for other people in the first place. They were written so I could learn Tachyon myself, and the reason I wanted to learn it had little to do with profiling as such.

## Why I wrote them

For the past while I have been working on [wrapture](https://github.com/GrahamDumpleton/wrapture), a library built on top of wrapt for attaching bindings to arbitrary call sites in a Python program without modifying the code being observed, then doing something useful with what flows through those call sites, such as recording calls or exporting traces. Everything wrapture does happens from inside the process. It wraps functions, and when they are called it is there in the call path to see the arguments, the return value, the exception, and the time taken.

So when a profiler landed in the standard library the obvious question was whether wrapture could make use of it. Could Tachyon be offered as part of wrapture's tracing, so that a binding on a call site could also tell you what the program was doing underneath that call? Could the two share anything at all? I did not know, and reading the Tachyon documentation was not going to tell me, because the documentation describes what each option does and not what you would want it for. The only way I was going to get a real answer was to use every part of the profiler on real programs, and the way I have been doing that lately is to have workshops written for the thing I want to learn and then do the workshops.

## Working from the outside

A sampling profiler does not instrument your program. Tachyon runs as a separate process, reads the call stack of the target process from the outside, a thousand times a second by default, and counts what it finds. The program runs at full speed and never knows it is being watched. The counts are then an estimate of where time went: a function that appears in half the samples took about half the time. cProfile, which in 3.15 has moved to `profiling.tracing`, does the opposite. It hooks every function call and return, so the counts are exact, but a program made of millions of small calls can run several times slower under it.

One of the early workshops puts the same program under both and the difference is stark enough that it answers the question of which to reach for most of the time. The other consequence of working from the outside is that the profiler needs permission to read another process's memory. Linux lets a user do that to processes they started themselves. macOS and Windows do not without root or administrator rights, which is why the workshops only run on Linux, and why on a Mac the way to run them is in a container. More on that below.

## Where that leaves wrapture

My first impression, having now been through all of it, is that the two do not fit together. Tachyon works by looking in at a process from outside. wrapture works by being inside the process, in the call path. I have found nothing to suggest Tachyon can be driven from within the process it is profiling in the way wrapture would need, and nothing in the way it reads a process that a binding on a call site could hook into. The models are different enough that I cannot see a way of marrying them, at least not with what is in 3.15.

That is a perfectly good answer. I would rather know it now than have spent time trying to bolt one onto the other, and the reasoning behind it is grounded in having used every mode of the profiler rather than guessed from a page of options. If that changes in a later release, or if someone knows something about Tachyon's internals that I missed, I would like to hear about it. For now the question is parked, not closed.

## Learning by having the lesson written

What surprised me was how much better this worked as a way of learning than reading the documentation would have. I did not write the workshops by hand. I described what I wanted each one to teach, had an AI build it, then did the workshop. The useful part was not that the AI knew Tachyon, since the documentation knew Tachyon just as well. It was that the AI kept filling in the context the documentation leaves out: why wall-clock time and CPU time disagree and what that disagreement tells you about the fix, why a view of which thread holds the GIL exists at all, why you would record a profile in the binary format and look at it later rather than looking at it now. Each feature came with a small program written to show it, which had the problem the feature was there to find, and that is what made the feature stick.

This is a different way to use an AI for learning than asking it questions. Asking questions gets you answers at the level of the question. Asking for the lesson to be built gets you something you then have to work through with your own hands, and if the lesson is wrong you find out when the check at the end of a step does not pass. It is also, I have noticed, far closer to how I actually learned things in the first place, which was by having to teach them.

## What the workshops cover

There are two collections, with a catalog in the repository so that one URL offers both.

The first, "Profiling with Tachyon", is fourteen workshops and a little under four hours in total. It starts with running the profiler on a small report generator and reading the table it prints, so that you know what a sample is and why time is samples multiplied by an interval. It then puts a program under both the tracer and the sampler, and looks at how the profiler reads a process from outside and what that needs permission for. From there it moves through the pictures the profiler produces: the interactive flame graph, the heatmap that paints sample counts onto the source so a single expensive line stands out, and recording in the binary format to replay later as a table, a flame graph, a heatmap, a Firefox Profiler file, JSON lines or a pstats file. The next group is about choosing what to measure, with workshops on wall-clock against CPU time, threads and the GIL, the cost of exceptions, and async code profiled as tasks and awaits rather than as the event loop's stack. The last group looks closer, at the markers for native code and the garbage collector, at opcode-level profiling in the heatmap, at differential flame graphs for telling whether a fix worked, and at the live terminal view that watches one process like `top`.

The second, "Tachyon on real applications", is seven workshops and a little over two hours. Each one runs a realistic program in one terminal and drives it from a second, with the profiler between them. There is a Flask application under load, then a slow endpoint found with the flame graph, pinned to a line with the heatmap, fixed, and proven fixed with a second recording. There is a Starlette service under uvicorn whose searches stall when articles are read, including a fix with a thread that does not work and why, and one with a process pool that does. There are worker processes, both a process pool and gunicorn with three workers, profiled with `--subprocesses`. There is a pytest suite with the profiler wrapped around it, attaching to a server that was started without the profiler, and finally a profile recorded in production, carried back and compared in a notebook with a table and a chart.

Every workshop ships the program it profiles, and the flame graphs and heatmaps open in JupyterLab in a tab beside the code, so you are reading the picture and the source together rather than switching between a browser and an editor.

## Running them

The workshops are built on [jupyterlab-workshop](https://github.com/GrahamDumpleton/jupyterlab-workshop), a JupyterLab extension that shows the instructions in a side panel with clickable actions that drive the session, opening files, running commands in a terminal and running cells in a notebook, and checks what you have done as you go.

The easiest way to start is the Binder button in the repository README, which builds the repository into a temporary JupyterLab on [mybinder.org](https://mybinder.org) with nothing to install and no account needed. The session is thrown away when you are done, so finish a workshop in the session you started it in, and shut the session down from the Finish dialog or the File menu rather than just closing the tab, so the resources go back for other people. The Codespaces button does the same in a container tied to your GitHub account, which persists until you delete it and uses your account's monthly allowance.

If you want to run them on your own machine and that machine is a Mac, the Linux requirement means a container. The repository carries a Dockerfile for it, with Python 3.15, JupyterLab, the extension and a non-root user, and the checkout is mounted so everything the workshops write ends up in your checkout:

```
git clone https://github.com/GrahamDumpleton/tachyon-workshops
cd tachyon-workshops
docker build -t tachyon-workshops -f container/Dockerfile .
docker run --rm --init -it -p 127.0.0.1:8888:8888 -e JUPYTER_TOKEN=tachyon \
    -v "$PWD":/home/learner/tachyon-workshops tachyon-workshops
```

Then open `http://127.0.0.1:8888/?token=tachyon`. On Linux with Python 3.15 and [uv](https://docs.astral.sh/uv/) you can skip the clone entirely and launch the extension on the catalog directly, with a directory of your own to keep the workshops in:

```
uvx --python 3.15 --from "jupyterlab-workshop[lab]" jupyter-workshop launch \
    --root ~/training --catalog https://raw.githubusercontent.com/GrahamDumpleton/tachyon-workshops/main/catalog.json
```

Python 3.15 is named because each workshop builds its own environment from the Python that JupyterLab runs on, and the profiler and the program it profiles must be the same Python. If you already have the extension installed somewhere, you can also just subscribe to the catalog from the workshop browser and the collections are offered there.

## What's next

Whether Tachyon ends up having anything to do with wrapture, I know a good deal more about it than I did, and I have something to show for the time that other people can use. If you do the workshops and find a step that is unclear, or one that does not work for you, the [issue tracker](https://github.com/GrahamDumpleton/tachyon-workshops/issues) is the place to say so. Fingers crossed they are as useful a way into Tachyon for you as writing them was for me.
