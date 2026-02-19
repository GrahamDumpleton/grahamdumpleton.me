# Graham Dumpleton's Blog

A modern static blog site for Graham Dumpleton, originally migrated from the Blogger site at [blog.dscpl.com.au](http://blog.dscpl.com.au). The site is built and managed using [Eleventy (11ty)](https://www.11ty.dev/) for fast, static site generation and is hosted at [https://grahamdumpleton.me](https://grahamdumpleton.me).

## About This Site

This is the personal blog of Graham Dumpleton, software developer and creator of mod_wsgi, wrapt, and other open source projects. The blog covers topics including Python, WSGI, web development, deployment practices, and technical education.

The site was migrated from Google Blogger using custom Python scripts to extract and convert the original content, then rebuilt as a modern static site using Eleventy for improved performance and maintainability.

## Static Site Generation with Eleventy

This blog is powered by [Eleventy (11ty)](https://www.11ty.dev/), a simpler static site generator that transforms content into a fast, modern website.

### Quick Start

Install dependencies:
```bash
npm install
```

Build the static site:
```bash
npm run build
```

Start development server with live reload:
```bash
npm run dev
```

Start development server without watch mode:
```bash
npm run serve
```

### Site Features

- **Modern Design**: Responsive Bootstrap 5-based layout with dark/light mode toggle
- **Fast Performance**: Static site generation for optimal loading speeds
- **SEO Optimized**: Open Graph and Twitter Card meta tags for social sharing
- **RSS Feed**: Automatic RSS feed generation for blog posts
- **Syntax Highlighting**: Prism.js for beautiful code syntax highlighting
- **Content Management**: Automatic post collection and organization by date
- **Asset Optimization**: Automatic copying and optimization of images and CSS

### Site Structure

```
src/
├── _layouts/          # Liquid template layouts
│   ├── base.liquid    # Main site layout
│   ├── post.liquid    # Individual post layout
│   └── guide.liquid   # Individual guide layout
├── assets/            # Static assets (CSS, images)
├── posts/             # Blog posts organized by date
│   ├── index.liquid   # Posts listing page
│   └── YYYY/MM/       # Year/Month structure
│       └── post-name/ # Individual post directories
│           ├── index.md
│           └── image.jpg (optional)
├── guides/            # Topic guides and tutorials
│   ├── index.liquid   # Guides listing page
│   └── guide-name/    # Individual guide directories
│       ├── index.md
│       └── image.png (optional)
├── about/             # About page content
│   └── index.liquid   # About page template
└── index.liquid       # Homepage template
```

### Content Management

The site contains two main types of content:

#### Blog Posts (`src/posts/`)
- **Purpose**: Individual blog posts with timestamps and chronological organization
- **Structure**: Organized by date (`YYYY/MM/post-name/`)
- **Content**: Each post directory contains `index.md` with metadata and content
- **Features**: Automatically collected and sorted by date (newest first), tags preserved from original Blogger posts
- **Layout**: Uses `post.liquid` template with date-based navigation

#### Topic Guides (`src/guides/`)
- **Purpose**: Comprehensive topic guides and tutorials that serve as reference material
- **Structure**: Individual guide directories (`guide-name/`)
- **Content**: Each guide directory contains `index.md` with metadata and content
- **Features**: Searchable collection, topic-based organization, cross-references to related posts
- **Layout**: Uses `guide.liquid` template with guide-specific navigation

Both content types support:
- Markdown files with YAML front matter
- Automatic image copying and linking from content directories
- Tag and metadata preservation from original Blogger content
- SEO optimization with Open Graph and Twitter Card meta tags

#### Required Metadata

**Blog Posts** require the following minimal metadata in `index.md`:
```yaml
---
layout: post
title: "Your Post Title"
date: 2024-01-15
tags: ["python", "web-development"]
---
```

**Topic Guides** require the following minimal metadata in `index.md`:
```yaml
---
layout: guide
title: "Your Guide Title"
description: "Brief description of the guide content"
tags: ["tutorial", "python"]
---
```

#### Page Description Metadata

Both blog posts and guides support an optional `description` property in the front matter to control the page's meta description:

```yaml
---
layout: post
title: "Your Post Title"
date: 2024-01-15
description: "A concise summary of what this post covers"
tags: ["python", "web-development"]
---
```

**Description behavior:**
- **Purpose**: Controls the `<meta name="description">` tag in the HTML head
- **SEO Impact**: Used by search engines and social media platforms for page summaries
- **Social Sharing**: Displayed when the URL is shared on platforms like Twitter, Facebook, LinkedIn
- **Fallback**: If no description is provided, defaults to "Graham Dumpleton's blog"
- **Best Practices**: 
  - Keep descriptions concise (150-160 characters recommended)
  - Write descriptive summaries that accurately represent the content
  - Avoid keyword stuffing; focus on readability and value

**Example usage:**
```yaml
---
layout: post
title: "Getting Started with Python WSGI"
date: 2024-01-15
description: "Learn the basics of Python WSGI applications and how to deploy them effectively"
tags: ["python", "wsgi", "deployment"]
---
```

#### Draft Content

Both blog posts and guides support a `draft` property to control content visibility:

**To mark content as draft**, add `draft: true` to the front matter:
```yaml
---
layout: post
title: "My Draft Post"
date: 2024-01-15
draft: true
tags: ["python", "draft"]
---
```

**Draft behavior:**
- **Default**: If `draft` is not specified, content is published (equivalent to `draft: false`)
- **Hidden from collections**: Draft content does not appear in:
  - Posts collection (homepage, posts index)
  - Guides collection (guides index)
  - RSS feed
- **Direct access**: Draft content is still processed and accessible via direct URL
- **Publishing**: Remove the `draft` property or set `draft: false` to publish

**Use cases:**
- Work-in-progress content that needs review
- Content scheduled for future publication
- Testing new content without affecting public collections
- Private notes or documentation

### Customization

The site can be customized by modifying:
- **Layouts**: Edit files in `src/_layouts/` to change page structure
- **Styling**: Modify `src/assets/css/style.css` for custom styles
- **Configuration**: Update `.eleventy.js` for site-wide settings
- **Content**: Add new posts in `src/posts/`, guides in `src/guides/`, or other pages in `src/`

### 11ty Configuration

The site is configured via `.eleventy.js` with:
- **Template Engine**: Liquid templates for flexible content rendering
- **Collections**: Organized blog posts and guides with automatic sorting
- **RSS Feed**: Automatic RSS feed generation using `@11ty/eleventy-plugin-rss`
- **Custom Filters**: Date formatting, excerpt generation, and content processing
- **Asset Management**: Automatic copying of CSS, images, and other static files
- **Content Types**: Separate collections for posts (chronological) and guides (topic-based)

### RSS Feed

The site automatically generates an RSS feed at `/feed.xml` that includes:
- **Content**: Recent blog posts (limited to 10 most recent)
- **Filtering**: Only posts from 2025 onwards (configurable cutoff date)
- **Metadata**: Site title, description, author information, and language settings
- **Format**: Standard RSS 2.0 format for compatibility with feed readers

The RSS feed is generated using the `@11ty/eleventy-plugin-rss` plugin and can be accessed at `https://grahamdumpleton.me/feed.xml`.
