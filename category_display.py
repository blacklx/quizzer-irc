"""
Smart Category Display System for IRC

Handles category listing in a user-friendly way that doesn't flood the channel.
Supports pagination, grouping, and search.

Copyright 2026 blacklx
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Version: 0.90
"""
# Standard library imports
import os
from collections import defaultdict


def get_all_categories():
    """Get all available categories from quiz_data directory."""
    categories = []
    if not os.path.exists('quiz_data'):
        return categories
    
    for filename in os.listdir('quiz_data'):
        if filename.endswith('_questions.json'):
            category = filename.replace('_questions.json', '').replace("_", " ")
            categories.append(category)
    return sorted(categories)


def group_categories(categories):
    """
    Group categories by type (Entertainment, Science, etc.)
    
    Returns:
        Dictionary mapping group name -> list of categories
    """
    groups = defaultdict(list)
    standalone = []
    
    for cat in categories:
        if cat.startswith('Entertainment'):
            groups['Entertainment'].append(cat)
        elif cat.startswith('Science'):
            groups['Science'].append(cat)
        else:
            standalone.append(cat)
    
    if standalone:
        groups['General'] = standalone
    
    return groups


def format_category_groups(groups, max_per_line=3):
    """
    Format category groups for display.
    
    Args:
        groups: Dictionary of group -> categories
        max_per_line: Maximum categories per line
        
    Returns:
        List of formatted lines
    """
    lines = []
    for group_name in sorted(groups.keys()):
        categories = groups[group_name]
        if not categories:
            continue
        
        # Header
        lines.append(f"\x02{group_name}:\x02")
        
        # Format categories in columns
        for i in range(0, len(categories), max_per_line):
            chunk = categories[i:i + max_per_line]
            # Shorten category names for display
            short_cats = [cat.replace('Entertainment ', 'Ent. ').replace('Science ', 'Sci. ') 
                         for cat in chunk]
            line = " | ".join(short_cats)
            lines.append(f"  {line}")
        
        lines.append("")  # Blank line between groups
    
    return lines


def search_categories(categories, search_term):
    """Search categories by name (case-insensitive)."""
    search_lower = search_term.lower()
    return [cat for cat in categories if search_lower in cat.lower()]


def get_categories_page(categories, page_num=1, per_page=10):
    """
    Get a specific page of categories for pagination.
    
    Args:
        categories: List of all categories
        page_num: Page number (1-indexed)
        per_page: Categories per page
        
    Returns:
        Tuple of (categories_for_page, total_pages, current_page)
    """
    total = len(categories)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    if page_num < 1:
        page_num = 1
    if page_num > total_pages:
        page_num = total_pages
    
    start = (page_num - 1) * per_page
    end = start + per_page
    
    return categories[start:end], total_pages, page_num


def format_categories_compact(categories, max_length=400):
    """
    Format categories in a compact way that fits IRC message limits.
    
    Args:
        categories: List of category names
        max_length: Maximum message length
        
    Returns:
        List of message strings
    """
    if not categories:
        return ["No categories available."]
    
    messages = []
    current_line = "Categories: "
    
    for cat in categories:
        # Shorten category names
        short_cat = cat.replace('Entertainment ', 'Ent. ').replace('Science ', 'Sci. ')
        
        # Check if adding this category would exceed limit
        test_line = current_line + short_cat + ", "
        if len(test_line) > max_length and current_line != "Categories: ":
            messages.append(current_line.rstrip(', '))
            current_line = short_cat + ", "
        else:
            current_line = test_line
    
    if current_line != "Categories: ":
        messages.append(current_line.rstrip(', '))
    
    return messages if messages else ["Categories: " + ", ".join(categories)]


def format_categories_grouped(categories, max_length=400):
    """
    Format categories grouped by type.
    
    Args:
        categories: List of category names
        max_length: Maximum message length
        
    Returns:
        List of message strings
    """
    groups = group_categories(categories)
    messages = []
    
    for group_name in sorted(groups.keys()):
        group_cats = groups[group_name]
        if not group_cats:
            continue
        
        # Create header
        header = f"\x02{group_name}\x02 ({len(group_cats)}): "
        
        # Format categories
        cat_list = []
        for cat in group_cats:
            # Shorten names
            short = cat.replace('Entertainment ', '').replace('Science ', '')
            cat_list.append(short)
        
        line = header + ", ".join(cat_list)
        
        # Split if too long
        if len(line) > max_length:
            # Split into multiple lines
            messages.append(header.rstrip(': '))
            current = "  "
            for cat in cat_list:
                test = current + cat + ", "
                if len(test) > max_length - 20:  # Leave some margin
                    messages.append(current.rstrip(', '))
                    current = "  " + cat + ", "
                else:
                    current = test
            if current.strip() != "":
                messages.append(current.rstrip(', '))
        else:
            messages.append(line)
    
    return messages


def handle_categories_display(categories, mode='grouped', page=None, search=None, max_length=400):
    """
    Main function to handle category display with different modes.
    
    Args:
        categories: List of all categories
        mode: 'grouped', 'compact', 'paged', 'search'
        page: Page number for paged mode
        search: Search term for search mode
        max_length: Maximum message length
        
    Returns:
        List of message strings to send
    """
    if search:
        # Search mode
        results = search_categories(categories, search)
        if not results:
            return [f"No categories found matching '{search}'. Use !categories to see all."]
        
        if len(results) <= 10:
            return format_categories_compact(results, max_length)
        else:
            return [f"Found {len(results)} categories matching '{search}'. Showing first 10:"] + \
                   format_categories_compact(results[:10], max_length) + \
                   [f"Use !categories search <term> to refine your search."]
    
    if mode == 'paged' and page:
        # Pagination mode
        page_cats, total_pages, current_page = get_categories_page(categories, page, per_page=10)
        messages = [f"Categories (page {current_page}/{total_pages}):"]
        messages.extend(format_categories_compact(page_cats, max_length))
        messages.append(f"Use !categories {current_page + 1} for next page, or !categories grouped for grouped view.")
        return messages
    
    if mode == 'grouped':
        # Grouped mode (default)
        return format_categories_grouped(categories, max_length)
    
    # Compact mode (fallback)
    return format_categories_compact(categories, max_length)

