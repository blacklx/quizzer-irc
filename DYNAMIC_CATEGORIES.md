# Dynamic Category System

## Overview

The category hierarchy system is now **fully dynamic** - it automatically detects categories from your `quiz_data/` directory and builds the hierarchy on-the-fly.

## Key Features

✅ **Auto-detection** - Scans actual files to find categories  
✅ **Handles new categories** - Automatically includes categories from fetch script  
✅ **No hardcoding** - Works with any categories you add  
✅ **Smart grouping** - Automatically groups Entertainment and Science subcategories  
✅ **HTML entity handling** - Handles `&amp;` and other HTML entities  
✅ **Duplicate prevention** - Removes duplicate categories automatically  

## How It Works

1. **Scans `quiz_data/` directory** for all `*_questions.json` files
2. **Reads category names** from the actual question data
3. **Normalizes names** - Handles HTML entities, removes prefixes
4. **Groups automatically** - Entertainment and Science subcategories grouped
5. **Builds hierarchy** - Creates main categories with subcategories

## Example

When you fetch new categories from the API:

```bash
cd otdb
python fetch.py --once --amount 50 --output ../quiz_data
```

The system will:
- ✅ Automatically detect new categories
- ✅ Add them to the hierarchy
- ✅ Group them correctly (Entertainment, Science, or standalone)
- ✅ Display them in `!categories` command

## Category Detection

The system detects categories by:
1. Reading filenames: `Entertainment_Music_questions.json`
2. Reading actual category from question data: `"category": "Entertainment: Music"`
3. Normalizing: Removes prefixes, handles HTML entities
4. Grouping: Entertainment subcategories → Entertainment main category

## Display Format

**Main categories:**
```
Entertainment (10): Board Games, Books, Cartoon & Animations, Comics, Film, 
  Japanese Anime & Manga, Music, Musicals & Theatres, Television, Video Games

Science (4): Nature, Computers, Gadgets, Mathematics

General: Animals, Art, Celebrities, General Knowledge, Geography, History, 
  Mythology, Politics, Sports, Vehicles
```

## Adding New Categories

Just fetch questions and the system handles the rest:

1. Fetch questions: `python fetch.py --once --output ../quiz_data`
2. System auto-detects new categories
3. Categories appear in `!categories` command
4. Users can use them immediately: `!start <new_category>`

## Cache

The hierarchy is cached for performance. To refresh after adding new categories:

```python
from category_hierarchy import clear_hierarchy_cache
clear_hierarchy_cache()
```

Or just restart the bot - it will rebuild on next access.

## Benefits

- ✅ **No manual updates** - System detects categories automatically
- ✅ **Works with API** - New categories from fetch script work immediately
- ✅ **Scalable** - Handles any number of categories
- ✅ **Maintainable** - No hardcoded lists to update

The system is ready to handle new categories from the API automatically!

