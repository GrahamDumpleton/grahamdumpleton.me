# Graham Dumpleton's Blog

A modern static blog site for Graham Dumpleton, originally migrated from the Blogger site at [blog.dscpl.com.au](http://blog.dscpl.com.au). The site is built and managed using [Eleventy (11ty)](https://www.11ty.dev/) for fast, static site generation.

## About This Site

This is the personal blog of Graham Dumpleton, software developer and creator of mod_wsgi, wrapt, and other open source projects. The blog covers topics including Python, WSGI, web development, deployment practices, and technical education.

The site was migrated from Google Blogger using custom Python scripts to extract and convert the original content, then rebuilt as a modern static site using Eleventy for improved performance and maintainability.

## Static Site Generation with Eleventy

This blog is powered by [Eleventy (11ty)](https://www.11ty.dev/), a simpler static site generator that transforms content into a fast, modern website.

### Quick Start

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
- **Syntax Highlighting**: Prism.js for beautiful code syntax highlighting
- **Content Management**: Automatic post collection and organization by date
- **Asset Optimization**: Automatic copying and optimization of images and CSS

### Site Structure

```
src/
├── _layouts/          # Liquid template layouts
│   ├── base.liquid    # Main site layout
│   └── post.liquid    # Individual post layout
├── assets/            # Static assets (CSS, images)
├── posts/             # Blog posts organized by date
│   └── YYYY/MM/       # Year/Month structure
└── index.liquid       # Homepage template
```

### Content Management

Posts are automatically processed from Markdown files with YAML front matter:
- Each post directory contains `index.md` with metadata and content
- Posts are automatically collected and sorted by date (newest first)
- Images are automatically copied and linked from post directories
- Tags and metadata are preserved from the original Blogger posts

### Customization

The site can be customized by modifying:
- **Layouts**: Edit files in `src/_layouts/` to change page structure
- **Styling**: Modify `src/assets/css/style.css` for custom styles
- **Configuration**: Update `.eleventy.js` for site-wide settings
- **Content**: Add new pages in `src/` or modify existing posts

### 11ty Configuration

The site is configured via `.eleventy.js` with:
- **Template Engine**: Liquid templates for flexible content rendering
- **Collections**: Organized blog posts with automatic sorting
- **Custom Filters**: Date formatting, excerpt generation, and content processing
- **Asset Management**: Automatic copying of CSS, images, and other static files

## Blogger Migration Scripts

The following Python scripts were used to migrate content from the original Blogger site:

### 1. Post Downloader (`download_posts.py`)

Downloads web pages from URLs in the posts metadata and saves them to organized subdirectories for migration from Blogger.

**Usage:**

Download all posts from metadata:
```bash
uv run python archive/download_posts.py
```

Download a single URL:
```bash
uv run python archive/download_posts.py <URL>
```

Download a single URL with overwrite:
```bash
uv run python archive/download_posts.py <URL> --overwrite
```

Show help:
```bash
uv run python archive/download_posts.py --help
```

**Features:**
- Reads URLs from `archive/posts-metadata.json`
- Creates organized directory structure (`src/posts/YYYY/MM/`)
- Downloads HTML content using the `requests` library
- Skips existing files (unless `--overwrite` is used)
- Handles network errors and timeouts gracefully
- Provides detailed progress reporting and statistics
- Supports both batch processing and single URL downloads

**Directory Structure:**
The script automatically creates subdirectories based on the URL path, with each post getting its own directory:
- `http://blog.dscpl.com.au/2007/03/resistance-is-futile.html` → `src/posts/2007/03/resistance-is-futile/original.html`
- `http://blog.dscpl.com.au/2019/01/administration-features-of-jupyterhub.html` → `src/posts/2019/01/administration-features-of-jupyterhub/original.html`

Each post is saved in its own subdirectory named after the HTML filename (without the .html extension), with the downloaded content saved as `original.html`. This structure allows for additional files (like extracted content, metadata, etc.) to be stored alongside the original HTML file.

**Error Handling:**
- Network timeouts and connection errors
- HTTP error responses (404, 500, etc.)
- File system permission issues
- Invalid JSON in metadata file
- Missing or malformed URLs
- Unicode encoding issues

### 2. Post Extractor (`extract_post.py`)

Extracts blog post data from Google Blogger HTML files and converts them to structured formats suitable for Eleventy.

**Usage:**

Process all posts from metadata (batch mode):
```bash
uv run python archive/extract_post.py
```

Process a single HTML file:
```bash
uv run python archive/extract_post.py <html_file_path>
```

Process a single HTML file with image overwrite:
```bash
uv run python archive/extract_post.py <html_file_path> --overwrite
```

Show help:
```bash
uv run python archive/extract_post.py --help
```

**Features:**
- **Batch Processing**: Automatically processes all posts from `archive/posts-metadata.json`
- **Single File Processing**: Process individual HTML files
- **Image Download**: Downloads and localizes images from blog posts
- **Overwrite Control**: `--overwrite` flag controls whether existing images are replaced
- **Standardized Output**: Always creates `index.md` and `data.json` files in each post directory
- **Content Extraction**: Extracts blog post title, content, author, date
- **Comment Parsing**: Parses and converts comments to Markdown
- **Label/Tag Extraction**: Extracts and preserves blog labels as tags
- **Metadata Preservation**: Preserves Open Graph data and other metadata
- **Markdown Generation**: Creates standalone Markdown files with YAML front matter
- **JSON Output**: Generates structured JSON with all extracted data

**Output Files:**
For each processed post, the script creates two files in the post's directory:
- `index.md`: Markdown file with YAML front matter containing post metadata and content
- `data.json`: Complete structured JSON with all extracted data including comments and metadata

**Image Handling:**
- Downloads images referenced in blog posts to the post's directory
- Updates image references in the content to point to local files
- Skips existing images unless `--overwrite` flag is used
- Generates safe filenames for images without proper names

**Directory Structure:**
The script works with the directory structure created by `download_posts.py`:
- `src/posts/2007/03/resistance-is-futile/original.html` → generates `index.md` and `data.json` in the same directory
- `src/posts/2019/01/administration-features-of-jupyterhub/original.html` → generates `index.md` and `data.json` in the same directory
