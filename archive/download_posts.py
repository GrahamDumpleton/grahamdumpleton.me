#!/usr/bin/env python3
"""
Script to download web pages from URLs in posts-metadata.json and save them
to organized subdirectories based on year and month from the URL path.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
import requests
from requests.exceptions import RequestException, Timeout, HTTPError
from requests.exceptions import ConnectionError as RequestsConnectionError


def load_metadata(metadata_file):
    """Load the posts metadata from JSON file."""
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file '{metadata_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metadata file: {e}")
        sys.exit(1)


def extract_year_month_from_url(url):
    """
    Extract year and month from URL path.
    Expected format: http://blog.dscpl.com.au/YYYY/MM/filename.html
    Returns tuple (year, month) or (None, None) if pattern doesn't match.
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        year = path_parts[0]
        month = path_parts[1]
        
        # Validate that year and month are numeric
        if year.isdigit() and month.isdigit():
            return year, month
    
    return None, None


def is_guide_url(url):
    """
    Check if URL is a guide URL (contains /p/ pattern).
    Expected format: http://blog.dscpl.com.au/p/filename.html
    Returns True if it's a guide URL, False otherwise.
    """
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2 and path_parts[0] == 'p':
        return True
    
    return False


def get_filename_from_url(url):
    """Extract filename from URL."""
    parsed = urlparse(url)
    return os.path.basename(parsed.path)


def get_basename_from_url(url):
    """Extract basename (without extension) from URL."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    # Remove .html extension if present
    if filename.endswith('.html'):
        return filename[:-5]  # Remove last 5 characters (.html)
    return filename


def download_webpage(url, user_agent=None):
    """
    Download webpage content from URL.
    Returns the HTML content as string, or None if download fails.
    """
    if user_agent is None:
        user_agent = 'Mozilla/5.0 (compatible; BlogDownloader/1.0)'
    
    headers = {'User-Agent': user_agent}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad responses
        
        # Try to decode as UTF-8, fallback to latin-1 if that fails
        try:
            return response.text
        except UnicodeDecodeError:
            return response.content.decode('latin-1')
                
    except HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} for {url}")
        return None
    except (RequestsConnectionError, Timeout) as e:
        print(f"Error: Network error for {url}: {e}")
        return None
    except RequestException as e:
        print(f"Error: Request error downloading {url}: {e}")
        return None


def create_directory_if_not_exists(directory_path):
    """Create directory if it doesn't exist."""
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        print(f"Error: Cannot create directory '{directory_path}': {e}")
        return False


def save_html_content(content, file_path):
    """Save HTML content to file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except (OSError, PermissionError, UnicodeEncodeError) as e:
        print(f"Error: Cannot save file '{file_path}': {e}")
        return False


def process_single_url(url, posts_dir, overwrite=False):
    """Process a single URL and download it to the appropriate directory."""
    print(f"Processing single URL: {url}")
    
    # Get basename from URL (without .html extension)
    basename = get_basename_from_url(url)
    if not basename:
        print("Error: Cannot extract basename from URL")
        return False
    
    # Check if this is a guide URL (contains /p/ pattern)
    if is_guide_url(url):
        # For guide URLs, create path: guides/basename/
        guides_dir = posts_dir.parent / 'guides'
        subdir = guides_dir / basename
        print("Target directory (guide):", subdir)
    else:
        # Regular post URL with YYYY/MM pattern
        year, month = extract_year_month_from_url(url)
        if not year or not month:
            print("Error: Cannot extract year/month from URL")
            return False
        
        # Create subdirectory path: posts/YYYY/MM/filename/
        subdir = posts_dir / year / month / basename
        print("Target directory (post):", subdir)
    
    # Create directory if it doesn't exist
    if not create_directory_if_not_exists(subdir):
        return False
    
    # Save as original.html inside the subdirectory
    file_path = subdir / "original.html"
    
    # Check if file already exists (unless overwrite is True)
    if file_path.exists() and not overwrite:
        print(f"File already exists, skipping: {file_path}")
        print("Use --overwrite flag to force download")
        return False
    
    # Download the webpage
    print("Downloading...")
    html_content = download_webpage(url)
    
    if html_content is None:
        print("Failed to download")
        return False
    
    # Save the content
    if save_html_content(html_content, file_path):
        print(f"Saved: {file_path}")
        return True
    else:
        return False


def main():
    """Main function to process all posts or a single URL."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Define paths
    metadata_file = project_root / 'archive/posts-metadata.json'
    posts_dir = project_root / 'src/posts'
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Check for help
        if sys.argv[1] in ['-h', '--help']:
            print("Usage:")
            print("  python download_posts.py                    # Download all posts from metadata")
            print("  python download_posts.py <URL>              # Download single URL")
            print("  python download_posts.py <URL> --overwrite  # Download single URL, overwrite if exists")
            return
        
        # Single URL mode
        url = sys.argv[1]
        overwrite = '--overwrite' in sys.argv
        
        print("Single URL mode")
        print("Posts will be saved to:", posts_dir)
        if overwrite:
            print("Overwrite mode: existing files will be replaced")
        print()
        
        success = process_single_url(url, posts_dir, overwrite)
        if success:
            print("Download completed successfully")
        else:
            print("Download failed")
        return
    
    # Normal mode - process all posts from metadata
    print(f"Loading metadata from: {metadata_file}")
    posts_data = load_metadata(metadata_file)
    
    print(f"Found {len(posts_data)} posts to process")
    print("Posts will be saved to:", posts_dir)
    
    # Statistics
    downloaded = 0
    skipped = 0
    errors = 0
    
    for i, post in enumerate(posts_data, 1):
        original_url = post.get('originalUrl')
        title = post.get('title', 'Unknown')
        
        if not original_url:
            print(f"[{i}/{len(posts_data)}] Skipping post with no URL: {title}")
            skipped += 1
            continue
        
        print(f"[{i}/{len(posts_data)}] Processing: {title}")
        print(f"  URL: {original_url}")
        
        # Get basename from URL (without .html extension)
        basename = get_basename_from_url(original_url)
        if not basename:
            print("  Warning: Cannot extract basename from URL, skipping")
            skipped += 1
            continue
        
        # Check if this is a guide URL (contains /p/ pattern)
        if is_guide_url(original_url):
            # For guide URLs, create path: guides/basename/
            guides_dir = posts_dir.parent / 'guides'
            subdir = guides_dir / basename
            print("  Target directory (guide):", subdir)
        else:
            # Regular post URL with YYYY/MM pattern
            year, month = extract_year_month_from_url(original_url)
            if not year or not month:
                print("  Warning: Cannot extract year/month from URL, skipping")
                skipped += 1
                continue
            
            # Create subdirectory path: posts/YYYY/MM/filename/
            subdir = posts_dir / year / month / basename
            print("  Target directory (post):", subdir)
        
        # Create directory if it doesn't exist
        if not create_directory_if_not_exists(subdir):
            errors += 1
            continue
        
        # Save as original.html inside the subdirectory
        file_path = subdir / "original.html"
        
        # Check if file already exists (normal mode never overwrites)
        if file_path.exists():
            print(f"  File already exists, skipping: {file_path}")
            skipped += 1
            continue
        
        # Download the webpage
        print("  Downloading...")
        html_content = download_webpage(original_url)
        
        if html_content is None:
            print("  Failed to download")
            errors += 1
            continue
        
        # Save the content
        if save_html_content(html_content, file_path):
            print(f"  Saved: {file_path}")
            downloaded += 1
        else:
            errors += 1
        
        # Add a small delay to be respectful to the server
        time.sleep(0.5)
        print()
    
    # Print summary
    print("=" * 50)
    print("Download Summary:")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total processed: {downloaded + skipped + errors}")


if __name__ == '__main__':
    main()
