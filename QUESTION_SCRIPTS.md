# Question Fetching Scripts

## Overview

Scripts for fetching and updating questions from Open Trivia Database:

1. **`otdb/fetch.py`** - Fetches questions from Open Trivia Database API ✅ **WORKING**
2. **`otdb/fetch_all.py`** - Fetches ALL questions from all categories ✅ **NEW**

---

## 1. Open Trivia Database Fetcher (`otdb/fetch.py`)

### What It Does
Fetches questions from the [Open Trivia Database](https://opentdb.com/) API and saves them to JSON files.

### Status
✅ **API is working** - Tested and confirmed  
✅ **Script is fixed** - Added error handling, HTML entity decoding, answer shuffling

### Usage

**Basic (fetch 50 questions, loop forever):**
```bash
cd otdb
python fetch.py
```

**Fetch once (recommended):**
```bash
cd otdb
python fetch.py --once --amount 50
```

**Fetch specific category:**
```bash
python fetch.py --once --amount 20 --category 9  # Category 9 = General Knowledge
```

**Save to main quiz_data directory:**
```bash
python fetch.py --once --amount 50 --output ../quiz_data
```

### Command-Line Options

- `--amount N` - Number of questions to fetch (default: 50)
- `--category ID` - Category ID (optional, see opentdb.com for IDs)
- `--difficulty easy|medium|hard` - Question difficulty
- `--type multiple|boolean` - Question type
- `--once` - Run once instead of looping forever
- `--output DIR` - Output directory (default: `data/`)
- `--delay SECONDS` - Delay between fetches when looping (default: 5)

### Features

✅ **Fetches from Open Trivia DB** - Free API with thousands of questions  
✅ **Automatic categorization** - Sorts questions by category  
✅ **Duplicate prevention** - Checks existing questions before adding  
✅ **HTML entity decoding** - Fixes `&amp;` and other HTML entities  
✅ **Answer shuffling** - Randomizes answer order (correct answer not always last)  
✅ **Error handling** - Won't crash if API is down  
✅ **Command-line options** - Flexible usage  

### Improvements Made

1. ✅ Added error handling for API failures
2. ✅ Fixed HTML entity decoding (`&amp;` → `&`)
3. ✅ Added answer shuffling (correct answer position randomized)
4. ✅ Added command-line arguments
5. ✅ Added `--once` flag to run once instead of infinite loop
6. ✅ Added `--output` option to save to different directory
7. ✅ Added docstrings and better logging

### Example Output

```
=== Fetch #1 ===
✓ Fetched 50 questions
✓ Processed into 8 categories
✓ Added 45 new questions
```

---

## 2. Fetch All Questions (`otdb/fetch_all.py`)

### What It Does
Downloads ALL questions from all categories on Open Trivia Database.

### Usage

**Fetch everything:**
```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

### Features

✅ **Fetches from all 24 categories**  
✅ **Respects rate limits** - Automatic backoff on 429 errors  
✅ **Prevents duplicates** - Global duplicate checking  
✅ **Early exit** - Skips fully collected categories  
✅ **Progress tracking** - Shows progress for each category  

### Command-Line Options

- `--output DIR` - Output directory (default: data)
- `--delay SECONDS` - Delay between requests (default: 3.0, recommended: 5.0)
- `--max-iterations N` - Max API calls per category (default: 100)

---

## File Locations

### Current Structure
- **Bot questions:** `quiz_data/*.json` (pre-loaded, ships with bot)
- **Fetch script:** `otdb/fetch.py` (updates questions)
- **Fetch all script:** `otdb/fetch_all.py` (updates all questions)

### Recommendation

The bot ships with a pre-loaded question database. To update it:

```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

This will add new questions while preventing duplicates.

---

## Quick Start Guide

### Fetch Questions from API

```bash
# Fetch 100 questions once and save to quiz_data
cd otdb
python fetch.py --once --amount 100 --output ../quiz_data
```


---

## API Information

**Open Trivia Database:**
- Website: https://opentdb.com/
- API: https://opentdb.com/api.php
- Free, no API key required
- Thousands of questions across many categories
- Rate limit: ~1 request per second recommended

**Category IDs:**
- 9: General Knowledge
- 10: Entertainment: Books
- 11: Entertainment: Film
- 12: Entertainment: Music
- 13: Entertainment: Musicals & Theatres
- 14: Entertainment: Television
- 15: Entertainment: Video Games
- 16: Entertainment: Board Games
- 17: Science & Nature
- 18: Science: Computers
- 19: Science: Mathematics
- 20: Mythology
- 21: Sports
- 22: Geography
- 23: History
- 24: Politics
- 25: Art
- 26: Celebrities
- 27: Animals
- 28: Vehicles
- 29: Entertainment: Comics
- 30: Science: Gadgets
- 31: Entertainment: Japanese Anime & Manga
- 32: Entertainment: Cartoon & Animations

See https://opentdb.com/api_category.php for full list.

---

## Testing

The fetch scripts have been tested and are working:

✅ **fetch.py** - Successfully fetches and processes questions  
✅ **fetch_all.py** - Successfully fetches all questions from all categories  
