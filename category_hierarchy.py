"""
Category Hierarchy System

Dynamically builds category hierarchy from actual files.
Auto-detects categories and groups them intelligently.

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
import os
import json
from collections import defaultdict


def normalize_category_name(category_name):
    """
    Normalize category name for display.
    - Removes main category prefix for subcategories
    - Handles HTML entities
    - Standardizes format
    """
    import html
    
    # Decode HTML entities
    normalized = html.unescape(category_name)
    
    # Handle "Science & Nature" -> "Science Nature"
    if normalized == 'Science & Nature' or normalized == 'Science &amp; Nature':
        normalized = 'Science Nature'
    
    # Remove main category prefix for subcategories
    if normalized.startswith('Entertainment: '):
        normalized = normalized.replace('Entertainment: ', '', 1)
    elif normalized.startswith('Entertainment '):
        normalized = normalized.replace('Entertainment ', '', 1)
    elif normalized.startswith('Science: '):
        normalized = normalized.replace('Science: ', '', 1)
    elif normalized.startswith('Science '):
        normalized = normalized.replace('Science ', '', 1)
    
    return normalized


def build_category_hierarchy(quiz_data_dir='quiz_data'):
    """
    Dynamically build category hierarchy from actual files.
    
    Groups categories by prefix (Entertainment, Science, etc.)
    and handles standalone categories.
    
    Returns:
        Dictionary mapping main_category -> list of subcategories (or None for standalone)
    """
    if not os.path.exists(quiz_data_dir):
        return {}
    
    hierarchy = {}
    category_groups = defaultdict(set)  # Use set to avoid duplicates
    standalone_categories = set()
    
    # Scan all question files
    for filename in os.listdir(quiz_data_dir):
        if not filename.endswith('_questions.json'):
            continue
        
        # Get category name from filename
        file_category = filename.replace('_questions.json', '').replace('_', ' ')
        
        # Try to get actual category name from file
        filepath = os.path.join(quiz_data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and isinstance(data, list) and len(data) > 0:
                    actual_category = data[0].get('category', file_category)
                else:
                    actual_category = file_category
        except (FileNotFoundError, json.JSONDecodeError, OSError, IOError, KeyError):
            # If file doesn't exist or is invalid, use filename-based category
            actual_category = file_category
        
        # Check original category name to determine grouping (before normalization)
        if actual_category.startswith('Entertainment:') or actual_category.startswith('Entertainment '):
            # Extract subcategory name
            if actual_category.startswith('Entertainment: '):
                subcat = actual_category.replace('Entertainment: ', '', 1)
            else:
                subcat = actual_category.replace('Entertainment ', '', 1)
            # Normalize the subcategory name
            subcat = normalize_category_name(subcat)
            category_groups['Entertainment'].add(subcat)
        elif actual_category.startswith('Science:') or actual_category.startswith('Science ') or actual_category.startswith('Science &'):
            # Extract subcategory name
            if actual_category.startswith('Science: '):
                subcat = actual_category.replace('Science: ', '', 1)
            elif actual_category.startswith('Science &'):
                subcat = actual_category.replace('Science &', '', 1).replace('Nature', 'Nature').strip()
                if subcat == 'Nature' or subcat == '& Nature':
                    subcat = 'Nature'
            else:
                subcat = actual_category.replace('Science ', '', 1)
            # Normalize the subcategory name
            subcat = normalize_category_name(subcat)
            category_groups['Science'].add(subcat)
        else:
            # Standalone category - normalize it
            normalized = normalize_category_name(actual_category)
            standalone_categories.add(normalized)
    
    # Build hierarchy
    # Add grouped categories
    for main_cat, subcats in category_groups.items():
        # Sort subcategories
        sorted_subcats = sorted(list(subcats))
        hierarchy[main_cat] = sorted_subcats
    
    # Add standalone categories
    for cat in sorted(standalone_categories):
        hierarchy[cat] = None  # None means no subcategories
    
    return hierarchy


# Cache the hierarchy (built on first access)
_cached_hierarchy = None


def get_category_hierarchy():
    """Get the category hierarchy (cached)."""
    global _cached_hierarchy
    if _cached_hierarchy is None:
        _cached_hierarchy = build_category_hierarchy()
    return _cached_hierarchy


def clear_hierarchy_cache():
    """Clear the hierarchy cache (call after adding new categories)."""
    global _cached_hierarchy
    _cached_hierarchy = None


def get_main_categories():
    """Get list of main category names."""
    hierarchy = get_category_hierarchy()
    return sorted(hierarchy.keys())


def get_subcategories(main_category):
    """Get subcategories for a main category."""
    hierarchy = get_category_hierarchy()
    subcats = hierarchy.get(main_category, None)
    return subcats if subcats is not None else []


def is_main_category(category_name):
    """Check if a category name is a main category."""
    hierarchy = get_category_hierarchy()
    return category_name in hierarchy


def has_subcategories(category_name):
    """Check if a main category has subcategories."""
    hierarchy = get_category_hierarchy()
    subcats = hierarchy.get(category_name)
    return subcats is not None and len(subcats) > 0


def find_category_match(user_input):
    """
    Find matching category from user input.
    
    Handles:
    - "entertainment" → main category
    - "entertainment music" → specific subcategory
    - "music" → tries to find matching subcategory
    - "animals" → standalone category
    
    Returns:
        Tuple of (main_category, subcategory, is_random)
        - main_category: Main category name or None
        - subcategory: Specific subcategory filename or None
        - is_random: Whether to use random selection
    """
    hierarchy = get_category_hierarchy()
    user_input = user_input.strip().lower()
    
    # Check for exact main category match
    for main_cat in hierarchy.keys():
        if user_input == main_cat.lower():
            subcats = hierarchy[main_cat]
            if subcats:
                # Has subcategories - will use random from all
                return main_cat, None, True
            else:
                # Standalone category
                return main_cat, None, False
    
    # Check for "main subcategory" format (e.g., "entertainment music")
    parts = user_input.split()
    if len(parts) >= 2:
        main_part = parts[0]
        sub_part = ' '.join(parts[1:])
        
        for main_cat, subcats in hierarchy.items():
            if subcats and main_part == main_cat.lower():
                # Find matching subcategory
                for subcat in subcats:
                    # Subcategories already have prefix removed
                    subcat_lower = subcat.lower()
                    if sub_part in subcat_lower or subcat_lower in sub_part:
                        # Convert to filename format (add main category prefix back)
                        full_name = f"{main_cat} {subcat}"
                        filename = full_name.replace(' ', '_')
                        return main_cat, filename, False
    
    # Check if it's a subcategory name directly (e.g., "music", "video games")
    for main_cat, subcats in hierarchy.items():
        if subcats:
            for subcat in subcats:
                # Subcategories already have prefix removed
                subcat_lower = subcat.lower()
                if user_input == subcat_lower or user_input in subcat_lower:
                    # Convert to filename format (add main category prefix back)
                    full_name = f"{main_cat} {subcat}"
                    filename = full_name.replace(' ', '_')
                    return main_cat, filename, False
    
    # Check for filename match (backward compatibility)
    for main_cat, subcats in hierarchy.items():
        if subcats:
            for subcat in subcats:
                filename = subcat.replace(' ', '_')
                if user_input == filename.lower():
                    return main_cat, filename, False
        else:
            # Standalone category
            filename = main_cat.replace(' ', '_')
            if user_input == filename.lower() or user_input == main_cat.lower():
                return main_cat, None, False
    
    return None, None, False


def format_category_display():
    """
    Format categories for display in IRC.
    Dynamically builds from actual files.
    
    Returns:
        List of formatted message strings
    """
    hierarchy = get_category_hierarchy()
    messages = []
    
    # Group main categories
    main_with_subs = []
    standalone = []
    
    for main_cat, subcats in sorted(hierarchy.items()):
        if subcats:
            main_with_subs.append((main_cat, subcats))
        else:
            standalone.append(main_cat)
    
    # Display categories with subcategories
    for main_cat, subcats in sorted(main_with_subs):
        # Subcategories already have prefix removed during build
        subcat_list = ', '.join(subcats)
        
        messages.append(f"\x02{main_cat}\x02 ({len(subcats)}): {subcat_list}")
    
    # Display standalone categories
    if standalone:
        standalone_list = ', '.join(sorted(standalone))
        messages.append(f"\x02General\x02: {standalone_list}")
    
    return messages


def get_category_filename(category_name, subcategory=None):
    """
    Get the filename for a category.
    
    Args:
        category_name: Main category name
        subcategory: Optional subcategory name (filename format)
        
    Returns:
        Filename string (e.g., "Entertainment_Music_questions.json")
    """
    if subcategory:
        return f"{subcategory}_questions.json"
    else:
        return f"{category_name.replace(' ', '_')}_questions.json"


if __name__ == "__main__":
    # Test the hierarchy system
    print("=== Main Categories ===")
    for cat in get_main_categories():
        print(f"  {cat}")
    
    print("\n=== Category Display ===")
    for msg in format_category_display():
        print(msg)
    
    print("\n=== Test Matching ===")
    test_inputs = [
        "entertainment",
        "entertainment music",
        "music",
        "science",
        "science computers",
        "animals",
        "video games",
    ]
    
    for test in test_inputs:
        main, sub, is_random = find_category_match(test)
        print(f"'{test}' → main={main}, sub={sub}, random={is_random}")

