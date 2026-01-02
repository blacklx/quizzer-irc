# Questions Database

## Overview

The Quizzer bot comes with a **pre-loaded question database** containing thousands of questions across all categories. You can start using the bot immediately without fetching questions.

## Included Database

- **Location:** `quiz_data/` directory
- **Format:** JSON files (`{category}_questions.json`)
- **Categories:** 24 categories with hierarchical organization
- **Total Questions:** 4,000+ questions (varies based on fetch results)

## Category Files

The database includes questions for all main categories:
- Entertainment (10 subcategories)
- Science (4 subcategories)
- Animals, Art, Celebrities, General Knowledge, Geography, History, Mythology, Politics, Sports, Vehicles

## Updating Questions

### Recommended: Use Fetch Scripts

The easiest way to add or update questions is using the fetch scripts:

**Update all questions:**
```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

**Add specific amount:**
```bash
cd otdb
python3 fetch.py --once --amount 50 --output ../quiz_data
```

The fetch scripts:
- ✅ Automatically prevent duplicates
- ✅ Normalize category names
- ✅ Handle HTML entities
- ✅ Shuffle answers
- ✅ Update existing files

### Legacy: Text File Conversion

⚠️ **NOTE:** Text file conversion tools have been removed. They were legacy code from the ChatGPT era and are not needed.

**Recommendation:** Use fetch scripts to add/update questions. They handle everything automatically.

## Question Format

Questions are stored in JSON format:

```json
{
  "category": "Animals",
  "question": "What is a group of crows called?",
  "answers": {
    "A": "A murder",
    "B": "A flock",
    "C": "A pack",
    "D": "A herd"
  },
  "correct": "A"
}
```

## Adding Custom Questions

### Option 1: Manual JSON Editing

Edit the JSON files directly in `quiz_data/`:

```bash
# Edit a category file
nano quiz_data/Animals_questions.json

# Add your question following the format above
```

### Option 2: Use Fetch Scripts

The fetch scripts are the recommended way to add questions:
- Handles all formatting automatically
- Prevents duplicates
- Normalizes category names
- Works with Open Trivia Database API

### Option 3: Manual JSON Editing

Edit JSON files directly in `quiz_data/`:

```bash
# Edit a category file
nano quiz_data/Animals_questions.json

# Add questions following the JSON format
```

⚠️ **Note:** Manual editing requires careful attention to JSON format. Use fetch scripts for automatic updates.

## Best Practices

1. **Use fetch scripts** - Most reliable and automatic
2. **Keep backups** - Backup `quiz_data/` before major updates
3. **Verify format** - Check JSON files are valid after manual edits
4. **Test questions** - Test that questions load correctly after adding

## Troubleshooting

**Questions not loading:**
- Check JSON files are valid: `python3 -m json.tool quiz_data/Animals_questions.json`
- Verify file format matches expected structure
- Check file permissions

**Duplicate questions:**
- Fetch scripts automatically prevent duplicates
- Manual additions may create duplicates
- Use fetch scripts to clean up

**Category not showing:**
- Ensure filename matches: `{Category}_questions.json`
- Check category name in JSON matches filename
- Verify file is in `quiz_data/` directory

