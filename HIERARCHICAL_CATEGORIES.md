# Hierarchical Category System - Implementation

## Overview

The bot now uses a **hierarchical category system** that reduces visible categories from 24 to **12 main categories**, while still allowing users to be specific when they want.

---

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

---

## How It Works

### Category Display

**Default (`!categories`):**
```
Entertainment (10): Board Games, Books, Cartoon & Animations, Comics, Film, 
  Japanese Anime & Manga, Music, Musicals & Theatres, Television, Video Games

Science (4): Computers, Gadgets, Mathematics, Nature

General: Animals, Art, Celebrities, General Knowledge, Geography, History, 
  Mythology, Politics, Sports, Vehicles
```

**View Subcategories (`!categories entertainment`):**
```
Entertainment Subcategories:
  Board Games, Books, Cartoon & Animations, Comics, Film, 
  Japanese Anime & Manga, Music, Musicals & Theatres, Television, Video Games
Use !start entertainment for random, or !start entertainment <subcategory> for specific.
```

---

## Usage Examples

### Starting Quizzes

| Command | What It Does |
|---------|--------------|
| `!start entertainment` | Random questions from all Entertainment subcategories |
| `!start entertainment music` | Questions from Entertainment Music only |
| `!start entertainment video games` | Questions from Entertainment Video Games only |
| `!start science` | Random questions from all Science subcategories |
| `!start science computers` | Questions from Science Computers only |
| `!start animals` | Questions from Animals (no subcategories) |
| `!start random` | Random from all categories |

### Viewing Categories

| Command | What It Shows |
|---------|---------------|
| `!categories` | All 12 main categories (grouped) |
| `!categories entertainment` | Entertainment subcategories |
| `!categories science` | Science subcategories |

---

## Benefits

✅ **Only 12 categories shown** - Clean, manageable list  
✅ **No name shortening** - Full category names preserved  
✅ **Flexible usage** - Users can be general or specific  
✅ **Intuitive** - "entertainment music" makes sense  
✅ **Backward compatible** - Old category names still work  

---

## Smart Matching

The system is smart about matching:

- `entertainment` → Main category (random from all Entertainment)
- `entertainment music` → Specific subcategory
- `music` → Finds "Entertainment Music" automatically
- `video games` → Finds "Entertainment Video Games" automatically
- `science computers` → Specific subcategory
- `animals` → Standalone category

---

## Technical Details

- **File structure unchanged** - All files stay as-is
- **Hierarchy defined in** `category_hierarchy.py`
- **Smart matching** handles variations and abbreviations
- **Backward compatible** - old category names still work

---

## Example IRC Conversation

```
User: !categories
Bot: Entertainment (10): Board Games, Books, Cartoon & Animations, Comics, Film, 
     Japanese Anime & Manga, Music, Musicals Theatres, Television, Video Games
Bot: Science (4): Computers, Gadgets, Mathematics, Nature
Bot: General: Animals, Art, Celebrities, General Knowledge, Geography, History, 
     Mythology, Politics, Sports, Vehicles
Bot: Use !categories <category> to see subcategories (e.g., !categories entertainment)

User: !categories entertainment
Bot: Entertainment Subcategories:
Bot:   Board Games, Books, Cartoon & Animations, Comics, Film, 
       Japanese Anime & Manga, Music, Musicals Theatres, Television, Video Games
Bot: Use !start entertainment for random, or !start entertainment <subcategory> for specific.

User: !start entertainment music
Bot: A quiz on 'Music' category will start in 45 seconds...
```

---

## Summary

- **12 main categories** instead of 24
- **Full names preserved** - no shortening
- **Flexible** - general or specific usage
- **Clean display** - easy to read
- **Smart matching** - handles variations

The system is ready to use!

