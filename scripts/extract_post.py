#!/usr/bin/env python3
"""
Blog Post Extractor

This script parses HTML files from Google Blogger and extracts key post information
into a structured JSON format.

Usage:
  python extract_post.py                           # Process all posts from metadata
  python extract_post.py <html_file_path>          # Process single HTML file
  python extract_post.py <html_file_path> --overwrite  # Process single file, overwrite existing images
"""

import json
import sys
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import re
import html2text
import requests
from urllib.parse import urlparse


def download_image(image_url, output_dir, overwrite=False):
    """
    Download an image from a URL and save it to the output directory.
    
    Args:
        image_url (str): URL of the image to download
        output_dir (Path): Directory to save the image to
        overwrite (bool): Whether to overwrite existing files
        
    Returns:
        str: Local filename of the downloaded image, or None if download failed
    """
    try:
        # Parse the URL to get the filename
        parsed_url = urlparse(image_url)
        filename = Path(parsed_url.path).name
        
        # If no filename in URL, generate one
        if not filename or '.' not in filename:
            filename = f"image_{hash(image_url) % 100000}.png"
        
        # Ensure the filename is safe
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Check if file already exists
        output_path = output_dir / filename
        if output_path.exists() and not overwrite:
            print(f"Image already exists, skipping: {filename}")
            return filename
        
        # Download the image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Save to output directory
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return filename
    except Exception as e:
        print(f"Warning: Failed to download image {image_url}: {e}")
        return None


def extract_and_download_images(content_element, output_dir, overwrite=False):
    """
    Extract image URLs from content and download them.
    
    Args:
        content_element: BeautifulSoup element containing the content
        output_dir (Path): Directory to save images to
        overwrite (bool): Whether to overwrite existing image files
        
    Returns:
        tuple: (markdown_content, list of downloaded image filenames)
    """
    # Find all images in the content
    images = content_element.find_all('img')
    downloaded_images = []
    
    # Download each image and update the content
    for img in images:
        src = img.get('src')
        if src:
            # Download the image
            local_filename = download_image(src, output_dir, overwrite)
            if local_filename:
                downloaded_images.append(local_filename)
                # Update the src to point to the local file
                img['src'] = local_filename
    
    return downloaded_images


def create_markdown_file(post_data, output_path):
    """
    Create a standalone Markdown file with YAML front matter for 11ty/Hugo.
    
    Args:
        post_data (dict): Extracted post data
        output_path (Path): Path for the Markdown file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write YAML front matter
        f.write("---\n")
        f.write(f"title: \"{post_data['title']}\"\n")
        f.write(f"author: \"{post_data['author']}\"\n")
        f.write(f"date: \"{post_data['date']}\"\n")
        f.write(f"url: \"{post_data['url']}\"\n")
        
        # Add post ID and blog ID if available
        if post_data.get('post_id'):
            f.write(f"post_id: \"{post_data['post_id']}\"\n")
        if post_data.get('blog_id'):
            f.write(f"blog_id: \"{post_data['blog_id']}\"\n")
        
        # Add labels as tags if any
        if post_data['labels']:
            f.write(f"tags: {post_data['labels']}\n")
        
        # Add downloaded images if any
        if post_data.get('downloaded_images'):
            f.write(f"images: {post_data['downloaded_images']}\n")
        
        # Add comment count
        f.write(f"comments: {len(post_data['comments'])}\n")
        
        # Add metadata if available
        if post_data.get('metadata'):
            metadata = post_data['metadata']
            if metadata.get('published_timestamp'):
                f.write(f"published_timestamp: \"{metadata['published_timestamp']}\"\n")
            if metadata.get('blog_title'):
                f.write(f"blog_title: \"{metadata['blog_title']}\"\n")
        
        f.write("---\n\n")
        
        # Write the content
        f.write(post_data['content'])
        
        # Write comments if any
        if post_data['comments']:
            f.write("\n\n---\n\n## Comments\n\n")
            for comment in post_data['comments']:
                f.write(f"### {comment['author']} - {comment['timestamp']}\n\n")
                f.write(f"{comment['content']}\n\n")


def extract_post_data(html_file_path, overwrite=False):
    """
    Extract blog post data from an HTML file.
    
    Args:
        html_file_path (str): Path to the HTML file
        overwrite (bool): Whether to overwrite existing image files
        
    Returns:
        dict: Extracted post data
    """
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize the result dictionary
    post_data = {
        'title': None,
        'content': None,
        'date': None,
        'author': None,
        'url': None,
        'post_id': None,
        'blog_id': None,
        'comments': [],
        'labels': [],
        'metadata': {}
    }
    
    # Extract title
    title_element = soup.find('h3', class_='post-title entry-title')
    if title_element:
        post_data['title'] = title_element.get_text(strip=True)
    
    # Extract content and convert HTML to Markdown
    content_element = soup.find('div', id=re.compile(r'post-body-\d+'))
    if content_element:
        # Download images and update references
        output_dir = Path(html_file_path).parent
        downloaded_images = extract_and_download_images(content_element, output_dir, overwrite)
        post_data['downloaded_images'] = downloaded_images
        
        # Convert HTML to Markdown with better code block handling
        h = html2text.HTML2Text()
        h.ignore_links = False  # Keep links
        h.ignore_images = False  # Keep images
        h.ignore_emphasis = False  # Keep bold/italic formatting
        h.body_width = 0  # Don't wrap lines
        h.unicode_snob = True  # Use unicode characters
        h.escape_snob = True  # Escape special characters
        
        # Get the HTML content and convert to Markdown
        html_content = str(content_element)
        markdown_content = h.handle(html_content).strip()
        
        # Post-process to improve code blocks
        # Look for lines that start with spaces and convert them to code blocks
        lines = markdown_content.split('\n')
        processed_lines = []
        in_code_block = False
        
        for line in lines:
            # Check if line starts with 4+ spaces (likely code)
            if line.startswith('    ') and line.strip():
                if not in_code_block:
                    processed_lines.append('```')
                    in_code_block = True
                # Remove leading spaces and add the line
                processed_lines.append(line[4:])
            else:
                if in_code_block:
                    processed_lines.append('```')
                    in_code_block = False
                processed_lines.append(line)
        
        # Close any open code block
        if in_code_block:
            processed_lines.append('```')
        
        post_data['content'] = '\n'.join(processed_lines)
    
    # Extract date
    date_element = soup.find('h2', class_='date-header')
    if date_element:
        date_text = date_element.get_text(strip=True)
        post_data['date'] = date_text
    
    # Extract author
    author_element = soup.find('span', class_='fn')
    if author_element:
        post_data['author'] = author_element.get_text(strip=True)
    
    # Extract canonical URL
    canonical_link = soup.find('link', rel='canonical')
    if canonical_link:
        post_data['url'] = canonical_link.get('href')
    
    # Extract post ID and blog ID from meta tags
    post_meta = soup.find('meta', {'itemprop': 'postId'})
    if post_meta:
        post_data['post_id'] = post_meta.get('content')
    
    blog_meta = soup.find('meta', {'itemprop': 'blogId'})
    if blog_meta:
        post_data['blog_id'] = blog_meta.get('content')
    
    # Extract publication timestamp
    timestamp_element = soup.find('abbr', class_='published')
    if timestamp_element:
        timestamp = timestamp_element.get('title')
        if timestamp:
            post_data['metadata']['published_timestamp'] = timestamp
    
    # Extract comments
    comments_section = soup.find('div', id='comments')
    if comments_section:
        # Check if there are actual comments
        comments_block = comments_section.find('dl', id='comments-block')
        if comments_block and comments_block.find_all('dt'):
            # Extract individual comments
            for comment_element in comments_block.find_all('dt', class_='comment-author'):
                comment_data = {
                    'comment_id': None,
                    'author': None,
                    'author_url': None,
                    'author_profile_id': None,
                    'content': None,
                    'timestamp': None,
                    'permalink': None,
                    'is_blog_author': False
                }
                
                # Extract comment ID
                comment_id = comment_element.get('id')
                if comment_id and comment_id.startswith('c'):
                    comment_data['comment_id'] = comment_id[1:]  # Remove 'c' prefix
                
                # Check if this is a blog author comment
                if 'blog-author' in comment_element.get('class', []):
                    comment_data['is_blog_author'] = True
                
                # Extract comment author - look for the link that contains the author name
                # The author name is in the text content of the link, not in an attribute
                author_links = comment_element.find_all('a', rel='nofollow')
                for link in author_links:
                    href = link.get('href', '')
                    if '/profile/' in href:
                        author_text = link.get_text(strip=True)
                        # Only use this link if it has actual text content (author name)
                        if author_text and author_text not in ['', 'said...']:
                            comment_data['author'] = author_text
                            comment_data['author_url'] = href
                            # Extract profile ID from URL
                            profile_id = href.split('/profile/')[-1]
                            comment_data['author_profile_id'] = profile_id
                            break
                
                
                # Extract comment content and convert HTML to Markdown
                content_element = comment_element.find_next('dd', class_='comment-body')
                if content_element:
                    # Convert HTML to Markdown for comments too
                    h = html2text.HTML2Text()
                    h.ignore_links = False
                    h.ignore_images = False
                    h.ignore_emphasis = False
                    h.body_width = 0
                    h.unicode_snob = True
                    h.escape_snob = True
                    
                    html_content = str(content_element)
                    comment_data['content'] = h.handle(html_content).strip()
                
                # Extract comment timestamp and permalink
                comment_footer = comment_element.find_next('dd', class_='comment-footer')
                if comment_footer:
                    timestamp_span = comment_footer.find('span', class_='comment-timestamp')
                    if timestamp_span:
                        timestamp_link = timestamp_span.find('a')
                        if timestamp_link:
                            comment_data['permalink'] = timestamp_link.get('href')
                            # The timestamp is in the text content
                            comment_data['timestamp'] = timestamp_link.get_text(strip=True)
                
                post_data['comments'].append(comment_data)
        else:
            # No comments found
            post_data['comments'] = []
    
    # Extract labels/tags
    labels_section = soup.find('div', class_='post-footer-line post-footer-line-2')
    if labels_section:
        labels_links = labels_section.find_all('a', href=re.compile(r'/search/label/'))
        for label_link in labels_links:
            post_data['labels'].append(label_link.get_text(strip=True))
    
    # Extract additional metadata
    # Blog title
    blog_title_element = soup.find('h1', class_='title')
    if blog_title_element:
        post_data['metadata']['blog_title'] = blog_title_element.get_text(strip=True)
    
    # Page title
    title_tag = soup.find('title')
    if title_tag:
        post_data['metadata']['page_title'] = title_tag.get_text(strip=True)
    
    # Open Graph data
    og_title = soup.find('meta', property='og:title')
    if og_title:
        post_data['metadata']['og_title'] = og_title.get('content')
    
    og_description = soup.find('meta', property='og:description')
    if og_description:
        post_data['metadata']['og_description'] = og_description.get('content')
    
    og_url = soup.find('meta', property='og:url')
    if og_url:
        post_data['metadata']['og_url'] = og_url.get('content')
    
    return post_data


def load_metadata(metadata_file):
    """Load the posts metadata from JSON file."""
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Metadata file '{metadata_file}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metadata file: {e}")
        return None


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


def get_basename_from_url(url):
    """Extract basename (without extension) from URL."""
    parsed = urlparse(url)
    filename = parsed.path.split('/')[-1]
    # Remove .html extension if present
    if filename.endswith('.html'):
        return filename[:-5]  # Remove last 5 characters (.html)
    return filename


def url_to_html_path(url, posts_dir):
    """
    Convert a URL to the expected HTML file path based on the download structure.
    
    Args:
        url (str): The original URL
        posts_dir (Path): Base posts directory
        
    Returns:
        Path: Path to the original.html file, or None if URL format is invalid
    """
    year, month = extract_year_month_from_url(url)
    if not year or not month:
        return None
    
    basename = get_basename_from_url(url)
    if not basename:
        return None
    
    # Create path: posts/YYYY/MM/filename/original.html
    return posts_dir / year / month / basename / "original.html"


def process_single_post(html_file_path, overwrite=False):
    """
    Process a single HTML file and extract post data.
    
    Args:
        html_file_path (Path): Path to the HTML file
        overwrite (bool): Whether to overwrite existing image files
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Extract post data
        post_data = extract_post_data(str(html_file_path), overwrite)
        
        # Generate output filenames (always index.md and data.json)
        output_dir = html_file_path.parent
        json_output_path = output_dir / "data.json"
        md_output_path = output_dir / "index.md"
        
        # Write to JSON file (always recreate)
        with open(json_output_path, 'w', encoding='utf-8') as json_file:
            json.dump(post_data, json_file, indent=2, ensure_ascii=False)
        
        # Create standalone Markdown file (always recreate)
        create_markdown_file(post_data, md_output_path)
        
        print(f"Successfully extracted post data to: {json_output_path}")
        print(f"Created Markdown file: {md_output_path}")
        print(f"Title: {post_data['title']}")
        print(f"Author: {post_data['author']}")
        print(f"Date: {post_data['date']}")
        print(f"Comments: {len(post_data['comments'])}")
        print(f"Labels: {len(post_data['labels'])}")
        
        # Report downloaded images
        if 'downloaded_images' in post_data and post_data['downloaded_images']:
            print(f"Downloaded images: {', '.join(post_data['downloaded_images'])}")
        
        return True
        
    except Exception as e:
        print(f"Error processing file {html_file_path}: {e}")
        return False


def process_all_posts(posts_dir, overwrite=False):
    """
    Process all posts from the metadata file.
    
    Args:
        posts_dir (Path): Base posts directory
        overwrite (bool): Whether to overwrite existing image files
        
    Returns:
        tuple: (successful_count, failed_count)
    """
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Load metadata
    metadata_file = project_root / 'posts-metadata.json'
    posts_data = load_metadata(metadata_file)
    
    if not posts_data:
        return 0, 0
    
    print(f"Found {len(posts_data)} posts to process")
    print(f"Posts directory: {posts_dir}")
    if overwrite:
        print("Overwrite mode: existing images will be replaced")
    print()
    
    successful = 0
    failed = 0
    
    for i, post in enumerate(posts_data, 1):
        original_url = post.get('originalUrl')
        title = post.get('title', 'Unknown')
        
        if not original_url:
            print(f"[{i}/{len(posts_data)}] Skipping post with no URL: {title}")
            failed += 1
            continue
        
        print(f"[{i}/{len(posts_data)}] Processing: {title}")
        print(f"  URL: {original_url}")
        
        # Convert URL to HTML file path
        html_file_path = url_to_html_path(original_url, posts_dir)
        if not html_file_path:
            print("  Warning: Cannot determine HTML file path from URL, skipping")
            failed += 1
            continue
        
        if not html_file_path.exists():
            print(f"  Warning: HTML file not found: {html_file_path}, skipping")
            failed += 1
            continue
        
        print(f"  Processing: {html_file_path}")
        
        # Process the post
        if process_single_post(html_file_path, overwrite):
            successful += 1
        else:
            failed += 1
        
        print()
    
    return successful, failed


def main():
    """Main function to run the extraction."""
    parser = argparse.ArgumentParser(
        description='Extract blog post data from HTML files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_post.py                           # Process all posts from metadata
  python extract_post.py posts/2007/03/resistance-is-futile/original.html
  python extract_post.py posts/2007/03/resistance-is-futile/original.html --overwrite
        """
    )
    
    parser.add_argument(
        'html_file_path',
        nargs='?',
        help='Path to HTML file to process (optional - if not provided, processes all posts from metadata)'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing image files (only applies to single file mode)'
    )
    
    args = parser.parse_args()
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    posts_dir = project_root / 'posts'
    
    if args.html_file_path:
        # Single file mode
        html_file_path = Path(args.html_file_path)
        
        if not html_file_path.exists():
            print(f"Error: File '{html_file_path}' not found.")
            sys.exit(1)
        
        print(f"Processing single file: {html_file_path}")
        if args.overwrite:
            print("Overwrite mode: existing images will be replaced")
        print()
        
        success = process_single_post(html_file_path, args.overwrite)
        if success:
            print("Processing completed successfully")
        else:
            print("Processing failed")
            sys.exit(1)
    else:
        # Batch processing mode
        print("Batch processing mode - processing all posts from metadata")
        print()
        
        successful, failed = process_all_posts(posts_dir, args.overwrite)
        
        print("=" * 50)
        print("Processing Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total processed: {successful + failed}")
        
        if failed > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
