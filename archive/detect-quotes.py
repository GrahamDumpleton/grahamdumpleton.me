#!/usr/bin/env python3
"""
Script to detect markdown files with problematic quoted sections that should be code blocks.

This script looks for patterns where quoted sections (starting with ">") contain code
that should be converted to proper markdown code blocks with ``` fences.

The problematic patterns include:
1. Lines starting with "> " (quote + space) followed by code indentation
2. Multiple blank lines within quoted sections ("> " followed by spaces)
3. Nested quote characters within code indentation
"""

import os
import re
from pathlib import Path


def has_problematic_quoted_sections(content):
    """
    Check if the markdown content has problematic quoted sections that should be code blocks.
    
    Returns True if problematic patterns are found, False otherwise.
    """
    lines = content.split('\n')
    in_quoted_section = False
    quoted_lines = []
    
    for line in lines:
        # Check if line starts with quote character
        if line.startswith('>'):
            in_quoted_section = True
            quoted_lines.append(line)
        elif in_quoted_section:
            # If we were in a quoted section and hit a non-quoted line
            if line.strip() == '':
                # Empty line, continue collecting
                quoted_lines.append(line)
            else:
                # End of quoted section, analyze it
                if analyze_quoted_section(quoted_lines):
                    return True
                quoted_lines = []
                in_quoted_section = False
    
    # Check final quoted section if file ends with one
    if in_quoted_section and quoted_lines:
        if analyze_quoted_section(quoted_lines):
            return True
    
    return False


def analyze_quoted_section(quoted_lines):
    """
    Analyze a quoted section to determine if it contains problematic patterns.
    
    Returns True if the section should be converted to a code block.
    """
    if not quoted_lines:
        return False
    
    # Pattern 1: Check for lines that start with "> " followed by code indentation
    # This includes lines like ">     def function():" or ">     >     @decorator"
    code_indent_pattern = re.compile(r'^>\s+(\s{4,}.*|>\s+.*)')
    
    # Pattern 2: Check for multiple consecutive blank lines in quoted section
    # Lines like "> " or ">    " (quote followed by spaces only)
    blank_quote_pattern = re.compile(r'^>\s*$')
    
    # Pattern 3: Check for nested quote characters within indentation
    # Lines like ">     >     @decorator"
    nested_quote_pattern = re.compile(r'^>\s+>\s+')
    
    has_code_indentation = False
    has_multiple_blanks = False
    has_nested_quotes = False
    blank_count = 0
    
    for line in quoted_lines:
        # Check for code indentation pattern
        if code_indent_pattern.match(line):
            has_code_indentation = True
        
        # Check for nested quotes
        if nested_quote_pattern.match(line):
            has_nested_quotes = True
        
        # Check for blank lines
        if blank_quote_pattern.match(line):
            blank_count += 1
        else:
            if blank_count > 1:
                has_multiple_blanks = True
            blank_count = 0
    
    # Check if we ended with multiple blanks
    if blank_count > 1:
        has_multiple_blanks = True
    
    # This is a problematic quoted section if it has any of these patterns
    return has_code_indentation or has_multiple_blanks or has_nested_quotes


def find_affected_files(posts_dir):
    """
    Find all markdown files under posts_dir that have problematic quoted sections.
    
    Returns a list of file paths.
    """
    affected_files = []
    posts_path = Path(posts_dir)
    
    # Find all index.md files under posts directory
    for md_file in posts_path.rglob('index.md'):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if has_problematic_quoted_sections(content):
                affected_files.append(str(md_file))
                
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return affected_files


def main():
    """Main function to detect and report affected files."""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    # Posts directory is one level up from archive
    posts_dir = script_dir.parent / 'posts'
    
    if not posts_dir.exists():
        print(f"Posts directory not found: {posts_dir}")
        return
    
    print("Scanning for markdown files with problematic quoted sections...")
    print(f"Searching in: {posts_dir}")
    print()
    
    affected_files = find_affected_files(posts_dir)
    
    if affected_files:
        print(f"Found {len(affected_files)} files with problematic quoted sections:")
        print()
        for file_path in affected_files:
            # Make path relative to posts directory for cleaner output
            rel_path = Path(file_path).relative_to(posts_dir)
            print(f"  {rel_path}")
    else:
        print("No files with problematic quoted sections found.")


if __name__ == '__main__':
    main()
