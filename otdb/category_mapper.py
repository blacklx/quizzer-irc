#!/usr/bin/env python3
"""
Category Mapper - Maps Open Trivia DB categories to standardized bot categories.

This ensures consistent category naming and prevents duplicates.

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
import html

# Standard category names used by the bot (from original quiz_data)
STANDARD_CATEGORIES = {
    # Direct matches
    "Animals": "Animals",
    "Art": "Art",
    "Celebrities": "Celebrities",
    "General Knowledge": "General Knowledge",
    "Geography": "Geography",
    "History": "History",
    "Mythology": "Mythology",
    "Politics": "Politics",
    "Sports": "Sports",
    "Vehicles": "Vehicles",
    
    # Entertainment categories
    "Entertainment: Board Games": "Entertainment Board Games",
    "Entertainment: Books": "Entertainment Books",
    "Entertainment: Cartoon & Animations": "Entertainment Cartoon Animations",
    "Entertainment: Comics": "Entertainment Comics",
    "Entertainment: Film": "Entertainment Film",
    "Entertainment: Japanese Anime & Manga": "Entertainment Japanese Anime Manga",
    "Entertainment: Music": "Entertainment Music",
    "Entertainment: Musicals & Theatres": "Entertainment Musicals Theatres",
    "Entertainment: Television": "Entertainment Television",
    "Entertainment: Video Games": "Entertainment Video Games",
    
    # Science categories
    "Science & Nature": "Science Nature",
    "Science: Computers": "Science Computers",
    "Science: Gadgets": "Science Gadgets",
    "Science: Mathematics": "Science Mathematics",
}

# Reverse mapping for variations
CATEGORY_VARIATIONS = {
    # Handle HTML entities
    "Entertainment: Cartoon &amp; Animations": "Entertainment Cartoon Animations",
    "Entertainment: Japanese Anime &amp; Manga": "Entertainment Japanese Anime Manga",
    "Entertainment: Musicals &amp; Theatres": "Entertainment Musicals Theatres",
    "Science &amp; Nature": "Science Nature",
    
    # Handle underscore variations
    "Entertainment_Board_Games": "Entertainment Board Games",
    "Entertainment_Books": "Entertainment Books",
    "Entertainment_Cartoon_Animations": "Entertainment Cartoon Animations",
    "Entertainment_Comics": "Entertainment Comics",
    "Entertainment_Film": "Entertainment Film",
    "Entertainment_Japanese_Anime_Manga": "Entertainment Japanese Anime Manga",
    "Entertainment_Music": "Entertainment Music",
    "Entertainment_Musicals_Theatres": "Entertainment Musicals Theatres",
    "Entertainment_Television": "Entertainment Television",
    "Entertainment_Video_Games": "Entertainment Video Games",
    "Science_Computers": "Science Computers",
    "Science_Gadgets": "Science Gadgets",
    "Science_Mathematics": "Science Mathematics",
    "Science_Nature": "Science Nature",
}


def normalize_category(api_category):
    """
    Normalize an API category name to the bot's standard format.
    
    Args:
        api_category: Category name from Open Trivia DB API
        
    Returns:
        Standardized category name
    """
    # Decode HTML entities first
    category = html.unescape(api_category)
    
    # Check direct mapping
    if category in STANDARD_CATEGORIES:
        return STANDARD_CATEGORIES[category]
    
    # Check variations
    if category in CATEGORY_VARIATIONS:
        return CATEGORY_VARIATIONS[category]
    
    # If not found, return normalized version (for new categories)
    # Replace colons and ampersands
    normalized = category.replace(':', ' ').replace('&', 'and').replace('amp;', '')
    # Clean up spaces
    normalized = ' '.join(normalized.split())
    return normalized


def get_filename_for_category(category):
    """
    Get the standard filename for a category.
    
    Args:
        category: Standardized category name
        
    Returns:
        Filename (e.g., "Entertainment_Board_Games_questions.json")
    """
    # Replace spaces with underscores
    filename = category.replace(' ', '_')
    return f"{filename}_questions.json"


def is_valid_category(category):
    """Check if a category is one of the standard bot categories."""
    normalized = normalize_category(category)
    return normalized in STANDARD_CATEGORIES.values()


if __name__ == "__main__":
    # Test the mapper
    test_categories = [
        "Entertainment: Video Games",
        "Entertainment: Cartoon & Animations",
        "Entertainment: Cartoon &amp; Animations",
        "Science & Nature",
        "Science &amp; Nature",
        "Entertainment_Board_Games",
        "General Knowledge",
        "Animals",
    ]
    
    print("=== Category Mapping Test ===")
    for cat in test_categories:
        normalized = normalize_category(cat)
        filename = get_filename_for_category(normalized)
        print(f"{cat:45s} -> {normalized:40s} -> {filename}")

