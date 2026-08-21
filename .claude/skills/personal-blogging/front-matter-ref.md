# Front Matter and Conventions Reference

## Post Front Matter Template

```yaml
---
title: "Post Title Here"
description: "A concise summary of what this post covers, aim for 150-160 characters"
date: YYYY-MM-DD
tags: ["tag1", "tag2"]
draft: true
---
```

Notes:
- The `layout` field is **not needed** for posts. It defaults to `post` via `src/posts/posts.11tydata.json`.
- Always set `draft: true` for new posts so they can be reviewed before publishing.
- The `date` field uses `YYYY-MM-DD` format (e.g., `2025-10-04`).
- The `description` should be a concise summary suitable for SEO meta tags and social sharing.

## Post Front Matter with OpenGraph Image

When the post is about a specific GitHub project, use the GitHub OpenGraph URL:

```yaml
---
title: "Post Title Here"
description: "A concise summary of what this post covers"
date: YYYY-MM-DD
image: "https://opengraph.githubassets.com/1/GrahamDumpleton/project-name"
tags: ["python", "project-name"]
draft: true
---
```

## File Path Conventions

- **Posts**: `src/posts/YYYY/MM/post-slug/index.md`
  - Year as four digits: `2025`
  - Month zero-padded: `01` through `12`
  - Slug: lowercase, hyphen-separated, derived from the title
  - Each post gets its own directory
  - Images go in the same directory as `index.md`

- **Guides**: `src/guides/guide-name/index.md`
  - Slug: lowercase, hyphen-separated

## Established Tags

These tags are already in use across the blog. Prefer reusing existing tags over inventing new ones.

### Project tags
- `mod_wsgi` - mod_wsgi project
- `wrapt` - wrapt library
- `decorators` - Python decorator patterns (often paired with `python`)

### Language and framework tags
- `python` - Python language (most common tag)
- `django` - Django framework
- `wsgi` - WSGI specification and implementations

### Infrastructure tags
- `docker` - Docker and containerisation
- `kubernetes` - Kubernetes orchestration
- `openshift` - OpenShift platform
- `apache` - Apache HTTP Server

### Tool and service tags
- `jupyter` - Jupyter notebooks
- `jupyterhub` - JupyterHub platform
- `ipython` - IPython (older posts)
- `new relic` - New Relic monitoring
- `pycharm` - PyCharm IDE
- `gunicorn` - Gunicorn WSGI server
- `uWSGI` - uWSGI server
- `nginx` - Nginx web server
- `s2i` - Source-to-Image builds
- `datadog` - Datadog monitoring
- `statsd` - StatsD metrics
- `heroku` - Heroku platform
- `lektor` - Lektor CMS

### Topic tags
- `pycon` - PyCon conferences
- `red hat` - Red Hat related
- `testing` - Testing practices
- `async` - Async Python
- `mod_python` - mod_python (historical)

### Tag conventions
- Always lowercase (exception: `uWSGI` preserved as-is in older posts)
- Use JSON array format with double-quoted strings: `["python", "wrapt"]`
- Keep tags simple and specific
- A post typically has 1 to 4 tags
- New tags are fine when covering genuinely new topics (e.g., `educates` for Educates platform posts)
