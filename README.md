# Blogger Post Extractor

A collection of Python scripts for managing blog post data from Google Blogger.

## Scripts

### 1. Post Downloader (`download_posts.py`)

Downloads web pages from URLs in the posts metadata and saves them to organized subdirectories.

**Usage:**

Download all posts from metadata:
```bash
uv run python scripts/download_posts.py
```

Download a single URL:
```bash
uv run python scripts/download_posts.py <URL>
```

Download a single URL with overwrite:
```bash
uv run python scripts/download_posts.py <URL> --overwrite
```

Show help:
```bash
uv run python scripts/download_posts.py --help
```

**Features:**
- Reads URLs from `posts-metadata.json`
- Creates organized directory structure (`posts/YYYY/MM/`)
- Downloads HTML content using the `requests` library
- Skips existing files (unless `--overwrite` is used)
- Handles network errors and timeouts gracefully
- Provides detailed progress reporting and statistics
- Supports both batch processing and single URL downloads

**Directory Structure:**
The script automatically creates subdirectories based on the URL path:
- `http://blog.dscpl.com.au/2007/03/resistance-is-futile.html` → `posts/2007/03/resistance-is-futile.html`
- `http://blog.dscpl.com.au/2019/01/administration-features-of-jupyterhub.html` → `posts/2019/01/administration-features-of-jupyterhub.html`

**Error Handling:**
- Network timeouts and connection errors
- HTTP error responses (404, 500, etc.)
- File system permission issues
- Invalid JSON in metadata file
- Missing or malformed URLs
- Unicode encoding issues

### 2. Post Extractor (`extract_post.py`)

Extracts blog post data from Google Blogger HTML files.

**Usage:**
```bash
uv run python scripts/extract_post.py <html_file_path>
```

**Features:**
- Extracts blog post title, content, author, date
- Parses comments and labels/tags
- Generates structured JSON output
- Preserves metadata and Open Graph data
