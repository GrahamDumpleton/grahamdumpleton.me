# Author, Projects, and Topics Reference

## About Graham Dumpleton

Experienced software developer with primary focus on Python development, but also extensive work with C/C++, JavaScript, TypeScript, Go, and supporting technologies including Kubernetes, Docker, and modern deployment practices.

Currently on sabbatical (micro retirement) and pondering full retirement. Based in Australia. Previously worked at:
- **New Relic** (2010 to 2015) - Developer advocacy, Python agent
- **Red Hat** (2015 to 2018) - Developer advocacy, OpenShift
- **VMware/Broadcom** (2018 to 2023) - Made redundant after Broadcom acquisition

Self-description on the blog navbar: "That Grumpy Old Guy"

### Links
- Blog: https://grahamdumpleton.me
- GitHub: https://github.com/GrahamDumpleton
- GitHub Sponsors: https://github.com/sponsors/GrahamDumpleton
- Educates org: https://github.com/educates

## Key Projects

### mod_wsgi
Apache HTTP Server module providing a WSGI-compliant interface for hosting Python web applications. Graham's longest-running project with significant impact on the Python ecosystem. Includes mod_wsgi-express for streamlined deployment.

- GitHub: https://github.com/GrahamDumpleton/mod_wsgi
- Docs: https://modwsgi.readthedocs.io/
- PyPI: https://pypi.org/project/mod-wsgi/
- Tags: `mod_wsgi`, `wsgi`, `apache`

### wrapt
Python library for creating decorators and performing monkey patching. Provides a robust foundation for implementing decorators that properly preserve function metadata and handle edge cases. In PyPI's top 100 packages by downloads.

Key classes: `ObjectProxy`, `BaseObjectProxy`, `FunctionWrapper`, `BoundFunctionWrapper`, `LazyObjectProxy`, `CallableObjectProxy`

Version 2.0.0 released October 2025. Major changes: removed Python 2 legacy code, new `BaseObjectProxy` class hierarchy, `LazyObjectProxy` for lazy imports, type hint support.

- GitHub: https://github.com/GrahamDumpleton/wrapt
- Docs: https://wrapt.readthedocs.io/
- PyPI: https://pypi.org/project/wrapt/
- Tags: `python`, `wrapt`

### Educates
Interactive training platform for technical education. Kubernetes-native, provides hands-on workshop environments with pre-configured setups. Over 5 years of development, not yet widely promoted. Graham considers this his most significant project by effort invested.

- Website: https://educates.dev
- Docs: https://docs.educates.dev
- GitHub org: https://github.com/educates
- Suggested tag: `educates`

## Blog History

- ~241 posts spanning 2007 to 2026
- Originally hosted at blog.dscpl.com.au on Google Blogger
- Migrated to grahamdumpleton.me (Eleventy) with custom Python migration scripts
- 6-year posting hiatus: 2019 to 2025 (due to constraints at VMware/Broadcom)
- Resumed posting September 2025 with "Back from the dead"
- Older posts may contain Blogger-era metadata (`originalUrl`, `post_id`, `blog_id`, `comments`, `published_timestamp`). New posts should not include these fields

## Topic Areas

Topics Graham writes about and has expertise in:

- **Python decorators and monkey patching** - the core use case for wrapt, correct decorator implementation, transparent object proxies
- **Lazy module imports** - wrapt's `LazyObjectProxy`, PEP 810
- **Python WSGI deployment** - mod_wsgi, mod_wsgi-express, Apache configuration, WSGI specification details
- **Docker and containers** - Python in Docker, best practices, user permissions, PID 1 issues
- **Kubernetes and OpenShift** - deployment patterns, Source-to-Image (s2i) builds
- **JupyterHub and Jupyter** - deployment, customisation, multi-user environments
- **Interactive technical education** - workshop platforms, hands-on learning, the Educates project
- **Developer advocacy** - community building, content strategy, industry observations
- **Performance** - profiling, monitoring, decorator overhead, WSGI benchmarking
- **Open source** - sustainability, maintenance, community engagement
- **Career and industry reflections** - remote work, job market, personal observations

## Cross-Referencing Conventions

When linking to resources in blog posts:

- **Own posts**: Use site-relative paths like `/posts/YYYY/MM/post-slug/`
- **PEPs**: `[PEP NNN](https://peps.python.org/pep-NNNN/)` (zero-padded to 4 digits)
- **PyPI**: `https://pypi.org/project/package-name/`
- **ReadTheDocs**: `https://project.readthedocs.io/`
- **GitHub repos**: `https://github.com/GrahamDumpleton/project-name`
- **GitHub issues**: `https://github.com/GrahamDumpleton/project-name/issues`

Graham frequently cross-links to his own previous blog posts when building on earlier work. When writing a post that relates to a previous one, check the existing posts and link to them.
