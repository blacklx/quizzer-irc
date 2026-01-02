# Fetch ALL Questions from Open Trivia Database

## Overview

The `fetch_all.py` script downloads **ALL questions** from all categories on Open Trivia Database, respecting rate limits and preventing duplicates.

## Rate Limiting

- **Default delay:** 1.5 seconds between requests
- **API recommendation:** ~1 request per second
- **Safety margin:** Using 1.5 seconds to be safe

## Usage

### Basic Usage (Fetch Everything)

```bash
cd otdb
python fetch_all.py
```

This will:
- Fetch from all 24 categories
- Save to `data/` directory
- Continue until no new questions found
- Respect rate limits (1.5s between requests)

### Save to quiz_data Directory

```bash
cd otdb
python fetch_all.py --output ../quiz_data
```

### Custom Rate Limit

```bash
# Use 2 seconds between requests (more conservative)
python fetch_all.py --delay 2.0

# Use 1 second (faster, but closer to API limit)
python fetch_all.py --delay 1.0
```

### Limit Iterations (for Testing)

```bash
# Only fetch 10 requests per category (for testing)
python fetch_all.py --max-iterations 10
```

## How It Works

1. **Fetches category list** from API
2. **For each category:**
   - Makes API requests (50 questions per request)
   - Continues until no new questions found
   - Stops after 3 consecutive empty responses
3. **Prevents duplicates** across all files
4. **Respects rate limits** with delays between requests
5. **Saves to standardized filenames** using category mapper

## Estimated Time

- **24 categories**
- **~1.5 seconds per request**
- **Multiple requests per category** (depends on how many questions exist)

**Rough estimate:** Several hours to fetch everything (depends on total questions in database)

## Safety Features

- ✅ **Rate limiting** - Respects API limits
- ✅ **Duplicate prevention** - Global duplicate checking
- ✅ **Error handling** - Continues on errors
- ✅ **Progress tracking** - Shows progress for each category
- ✅ **Safety limits** - Max iterations per category (default: 100)

## Example Output

```
============================================================
Open Trivia Database - Fetch ALL Questions
============================================================

Fetching category list...
Found 24 categories
Rate limit: 1.5 seconds between requests
Max questions per request: 50
Max iterations per category: 100

============================================================

Loading existing questions...
Found 1500 existing questions

============================================================

============================================================
Category: General Knowledge (ID: 9)
============================================================

  Request #1 (Total: 1)... Fetched 50, added 50 new questions
  Request #2 (Total: 2)... Fetched 50, added 50 new questions
  Request #3 (Total: 3)... Fetched 30, added 30 new questions
  Request #4 (Total: 4)... No questions returned (empty count: 1)
  Request #5 (Total: 5)... No questions returned (empty count: 2)
  Request #6 (Total: 6)... No questions returned (empty count: 3)
  → No more questions available for this category

  Category complete: 130 new questions added
  Total requests for this category: 6

[... continues for all 24 categories ...]

============================================================
FETCH COMPLETE
============================================================
Total categories processed: 24
Total API requests: 150
Total new questions added: 3500
Total questions in database: 5000
============================================================
```

## Tips

1. **Run overnight** - It will take several hours
2. **Monitor progress** - Check output periodically
3. **Can be interrupted** - Resume later, duplicates are prevented
4. **Safe to re-run** - Won't re-download existing questions

## Command Reference

```bash
# Fetch everything (default settings)
python fetch_all.py

# Save to quiz_data
python fetch_all.py --output ../quiz_data

# More conservative rate limit
python fetch_all.py --delay 2.0

# Test with limited iterations
python fetch_all.py --max-iterations 5
```

## Notes

- The script will continue fetching until no new questions are found
- It automatically stops after 3 consecutive empty responses per category
- All questions are checked for duplicates globally (across all files)
- Questions are saved with standardized category names

