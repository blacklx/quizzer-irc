# Category System Documentation

## Overview

The Quizzer bot uses a **hierarchical category system** that automatically organizes categories for easy browsing and usage.

## Main Categories (12 total)

1. **Entertainment** (10 subcategories)
2. **Science** (4 subcategories)
3. **Animals**
4. **Art**
5. **Celebrities**
6. **General Knowledge**
7. **Geography**
8. **History**
9. **Mythology**
10. **Politics**
11. **Sports**
12. **Vehicles**

## How It Works

### Dynamic Detection

The system **automatically detects** categories from your `quiz_data/` directory:
- Scans all `*_questions.json` files
- Reads category names from question data
- Groups Entertainment and Science subcategories
- Handles new categories automatically

### Category Display

**`!categories`** shows:
```
Entertainment (10): Board Games, Books, Cartoon & Animations, Comics, Film, 
  Japanese Anime & Manga, Music, Musicals & Theatres, Television, Video Games

Science (4): Computers, Gadgets, Mathematics, Nature

General: Animals, Art, Celebrities, General Knowledge, Geography, History, 
  Mythology, Politics, Sports, Vehicles
```

**`!categories entertainment`** shows:
```
Entertainment Subcategories:
  Board Games, Books, Cartoon & Animations, Comics, Film, 
  Japanese Anime & Manga, Music, Musicals Theatres, Television, Video Games
Use !start entertainment for random, or !start entertainment <subcategory> for specific.
```

## Usage Examples

### Starting Quizzes

| Command | What It Does |
|---------|--------------|
| `!start entertainment` | Random questions from all Entertainment subcategories |
| `!start entertainment music` | Questions from Entertainment Music only |
| `!start entertainment video games` | Entertainment Video Games specifically |
| `!start science` | Random from all Science subcategories |
| `!start science computers` | Science Computers specifically |
| `!start animals` | Animals category (no subcategories) |
| `!start random` | Random from all categories |

### Smart Matching

The system is smart about matching:
- `entertainment` → Main category (random from all Entertainment)
- `entertainment music` → Specific subcategory
- `music` → Automatically finds "Entertainment Music"
- `video games` → Automatically finds "Entertainment Video Games"
- `science computers` → Specific subcategory
- `animals` → Standalone category

## Adding New Categories

When you fetch new categories from the API:

```bash
cd otdb
python3 fetch_all.py --output ../quiz_data
```

The system will:
- ✅ Automatically detect new categories
- ✅ Add them to the hierarchy
- ✅ Display them in `!categories` command
- ✅ Make them available for `!start` immediately

## Technical Details

- **File structure:** Categories stored as `{category}_questions.json`
- **Hierarchy defined in:** `category_hierarchy.py`
- **Display handled by:** `category_display.py`
- **Normalization:** `otdb/category_mapper.py` handles API category names

## Benefits

✅ **Only 12 categories shown** - Clean, manageable list  
✅ **Full names preserved** - No shortening needed  
✅ **Flexible usage** - General or specific  
✅ **Automatic detection** - New categories included automatically  
✅ **No channel flooding** - Smart grouping for IRC  

