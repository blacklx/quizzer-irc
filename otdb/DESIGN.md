# Question Fetching System Design

## Overview

The system is designed to prevent duplicate questions and categories by:
1. **Standardized category mapping** - Maps API categories to bot's standard format
2. **Global duplicate checking** - Checks for duplicates across ALL files, not just within files
3. **Consistent filename generation** - Uses standardized naming to prevent duplicate category files

---

## Original Categories (24 total)

From your original `quiz_data/` directory:

1. Animals
2. Art
3. Celebrities
4. Entertainment Board Games
5. Entertainment Books
6. Entertainment Cartoon Animations
7. Entertainment Comics
8. Entertainment Film
9. Entertainment Japanese Anime Manga
10. Entertainment Music
11. Entertainment Musicals Theatres
12. Entertainment Television
13. Entertainment Video Games
14. General Knowledge
15. Geography
16. History
17. Mythology
18. Politics
19. Science Computers
20. Science Gadgets
21. Science Mathematics
22. Science Nature
23. Sports
24. Vehicles

---

## How It Works

### 1. Category Mapping (`category_mapper.py`)

Maps Open Trivia DB categories to your bot's standard format:

**API Format Examples:**
- `"Entertainment: Video Games"` → `"Entertainment Video Games"`
- `"Entertainment: Cartoon & Animations"` → `"Entertainment Cartoon Animations"`
- `"Science & Nature"` → `"Science Nature"`
- `"Entertainment: Cartoon &amp; Animations"` → `"Entertainment Cartoon Animations"` (handles HTML entities)

**Benefits:**
- Consistent category names
- Prevents duplicate category files
- Handles HTML entity variations

### 2. Global Duplicate Prevention

**Before saving:**
1. Loads ALL existing questions from ALL files
2. Creates a set of all question texts (case-insensitive)
3. Checks each new question against this global set
4. Only saves questions that don't already exist

**Benefits:**
- No duplicate questions across any files
- Case-insensitive matching (handles variations)
- Works across all categories

### 3. Standardized Filenames

Uses `get_filename_for_category()` to generate consistent filenames:
- `"Entertainment Video Games"` → `"Entertainment_Video_Games_questions.json"`
- `"Science Nature"` → `"Science_Nature_questions.json"`

**Benefits:**
- One file per category (no duplicates)
- Matches your original naming convention
- Easy to find and manage

---

## Data Flow

```
API Question
    ↓
[Decode HTML entities]
    ↓
[Normalize category name] → category_mapper.py
    ↓
[Check global duplicates] → load_existing_questions()
    ↓
[Shuffle answers]
    ↓
[Format question]
    ↓
[Save to standardized filename] → get_filename_for_category()
    ↓
JSON File
```

---

## Features

### ✅ Prevents Duplicate Categories
- Maps all API category variations to standard names
- One file per category
- No more `Entertainment:_Comics` vs `Entertainment__Comics`

### ✅ Prevents Duplicate Questions
- Global duplicate checking across all files
- Case-insensitive matching
- Works even if same question appears in different categories

### ✅ Consistent Naming
- Standardized filenames match your original convention
- Handles HTML entities (`&amp;` → `and`)
- Handles special characters

### ✅ Answer Shuffling
- Randomizes answer order
- Correct answer not always in same position
- Fair for quiz participants

---

## Usage

```bash
cd otdb

# Fetch questions (automatically prevents duplicates)
python fetch.py --once --amount 50

# Save directly to quiz_data directory
python fetch.py --once --amount 50 --output ../quiz_data
```

---

## Cleanup Existing Duplicates

To clean up existing duplicate files:

```bash
cd otdb
python cleanup_duplicates.py --data-dir data --execute
```

This will:
1. Merge duplicate category files
2. Remove duplicate questions
3. Normalize category names

---

## Testing

The system has been tested and verified to:
- ✅ Map categories correctly
- ✅ Prevent duplicate questions
- ✅ Generate consistent filenames
- ✅ Handle HTML entities
- ✅ Shuffle answers properly

