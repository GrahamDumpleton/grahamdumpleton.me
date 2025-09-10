# Blogger Migration Scripts

The following Python scripts were used to migrate content from the original Blogger site at [blog.dscpl.com.au](http://blog.dscpl.com.au) to this modern static site.

**NOTE**: Don't run these scripts again on this repo as some fixups in the converted blog posts had to be done manually afterwards, so running the conversion again will loose those changes. The scripts are kept here just in case they are useful to someone else.

## Overview

These scripts handle the complete migration process from Google Blogger to a static site built with Eleventy:

1. **Post Downloader** - Downloads HTML content from Blogger URLs
2. **Post Extractor** - Extracts and converts content to Markdown and JSON formats

## Scripts

### 1. Post Downloader (`download_posts.py`)

Downloads web pages from URLs in the posts metadata and saves them to organized subdirectories for migration from Blogger.

**Usage:**

Download all posts from metadata:
```bash
uv run python blogger/download_posts.py
```

Download a single URL:
```bash
uv run python blogger/download_posts.py <URL>
```

Download a single URL with overwrite:
```bash
uv run python blogger/download_posts.py <URL> --overwrite
```

Show help:
```bash
uv run python blogger/download_posts.py --help
```

**Features:**
- Reads URLs from `blogger/posts-metadata.json`
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
uv run python blogger/extract_post.py
```

Process a single HTML file:
```bash
uv run python blogger/extract_post.py <html_file_path>
```

Process a single HTML file with image overwrite:
```bash
uv run python blogger/extract_post.py <html_file_path> --overwrite
```

Show help:
```bash
uv run python blogger/extract_post.py --help
```

**Features:**
- **Batch Processing**: Automatically processes all posts from `blogger/posts-metadata.json`
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
