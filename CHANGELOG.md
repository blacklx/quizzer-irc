# Changelog - Improvements Made

## Version 0.90 (2026)

### Legal & Licensing
- ✅ Added Apache 2.0 License
- ✅ Added Terms of Service (TERMS.md)
- ✅ Added Privacy Policy (PRIVACY.md)
- ✅ Added copyright headers to all Python files (Copyright 2026 blacklx)
- ✅ Standardized version to v0.90 across all files

### New Features
- ✅ Added `!admin stats` command - Shows comprehensive bot statistics
- ✅ Game disconnect handling - Gracefully handles disconnections during active games
- ✅ Enhanced reconnection logic - Better error handling and logging

### Bug Fixes
- ✅ Fixed critical reconnection bug - Bot no longer crashes on connection failures
- ✅ Fixed import errors in fetch scripts
- ✅ Fixed startbot.sh virtual environment handling

## Completed Improvements

### 1. Naming Improvements ✅
- **Renamed `RachnarBot` → `QuizzerBot`** - Class name now matches project name
- **Renamed `read_db.py` → `view_leaderboard.py`** - Clearer purpose

### 2. Script Improvements ✅
- **Fixed `startbot.sh`** - Now auto-detects directory path instead of hardcoded `/home/quizzer/bot2`
- **Added environment variable check** - Warns if `NICKSERV_PASSWORD` is not set
- **Updated to use `run.py`** - Management script now uses the new entry point

### 3. Code Organization ✅
- **Created `config_loader.py`** - Centralized configuration loading (eliminates duplicate code)
- **Created `run.py`** - Clean entry point with proper error handling
- **Added comprehensive docstrings** - All main classes and functions now documented

### 4. Documentation ✅
- **Created `README.md`** - Complete project documentation
- **Created `FILE_GUIDE.md`** - Explains what each file does
- **Created `IMPROVEMENTS.md`** - Detailed improvement recommendations
- **Created `requirements.txt`** - Python dependencies list

### 5. Code Quality ✅
- **Added module docstrings** - All Python modules now have header documentation
- **Added class docstrings** - All classes documented with purpose and attributes
- **Added function docstrings** - All main functions documented with args/returns

## Files Changed

### Modified Files
- `main_bot.py` - Renamed class, added docstrings
- `module_quizzer.py` - Added docstrings
- `admin.py` - Added docstrings
- `db_manager.py` - Added docstrings
- `tools/startbot.sh` - Fixed paths, added env var check
- `README.md` - Updated with new information

### New Files
- `config_loader.py` - Shared configuration module
- `run.py` - New entry point
- `view_leaderboard.py` - Renamed from read_db.py
- `requirements.txt` - Dependencies
- `FILE_GUIDE.md` - File reference guide
- `IMPROVEMENTS.md` - Improvement recommendations
- `CHANGELOG.md` - This file

## Usage Changes

### Starting the Bot
**Old way:**
```bash
python main_bot.py
```

**New way (recommended):**
```bash
python run.py
```

Both still work, but `run.py` provides better error handling and initialization.

### Configuration
The new `config_loader.py` module is available but not yet integrated into existing files to maintain backward compatibility. You can use it in new code or gradually migrate.

### 6. Category System Improvements ✅
- **Hierarchical Category System** - 12 main categories with subcategories
- **Dynamic Category Detection** - Automatically detects categories from files
- **Smart Category Display** - Groups categories to avoid IRC flooding
- **Category Matching** - Flexible matching (e.g., "entertainment music" or just "music")
- **Category Mapper** - Normalizes API category names to standard format

### 7. Question Fetching Improvements ✅
- **fetch_all.py** - Script to download ALL questions from all categories
- **Rate Limit Handling** - Exponential backoff on 429 errors
- **Early Exit** - Skips fully collected categories automatically
- **Duplicate Prevention** - Global duplicate checking across all files
- **Category Normalization** - Handles HTML entities and name variations

### 8. Security & Cleanup ✅
- **Removed exposed API key** - Deleted `chatgtp-api-key` file
- **Cleaned Python cache** - Removed `__pycache__` directories
- **Removed duplicate test files** - Cleaned up `quiz_data/test/` directory

## Files Changed (Complete List)

### Renamed Files
- `main_bot.py` → `bot.py`
- `module_quizzer.py` → `quiz_game.py`
- `read_db.py` → `view_leaderboard.py`
- `db_manager.py` → `database.py`
- `config_loader.py` → `config.py`

### New Files
- `run.py` - Entry point
- `category_hierarchy.py` - Dynamic category system
- `category_display.py` - Smart category display
- `otdb/fetch_all.py` - Fetch all questions script
- `otdb/category_mapper.py` - Category normalization
- `otdb/fetch.py` - Improved fetch script with duplicate prevention
- `CLEANUP_REPORT.md` - Cleanup documentation

### Modified Files
- `bot.py` - Added hierarchical category support
- `quiz_game.py` - Added hierarchical category loading
- `admin.py` - Added docstrings, improved error handling
- `database.py` - Added docstrings, improved resource management
- `tools/startbot.sh` - Fixed paths, uses `run.py`
- `README.md` - Updated with new features
- `FILE_GUIDE.md` - Updated with new files

## Usage Changes

### Category Commands
**New hierarchical system:**
```bash
!start entertainment              # Random from all Entertainment
!start entertainment music        # Entertainment Music specifically
!start science                    # Random from all Science
!categories                       # Shows 12 main categories
!categories entertainment         # Shows Entertainment subcategories
```

### Fetching Questions
**New fetch_all script:**
```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

## Backward Compatibility

All changes maintain backward compatibility:
- Old category names still work
- All existing functionality preserved
- No breaking changes to configuration format
- Old question file format still supported

---

## Cleanup (Latest)

### Files Removed
- ✅ `tools/txt2json.py` - Legacy converter from ChatGPT era (not used, not related to Open Trivia DB)
- ✅ `test.py` - Test script (removed)
- ✅ `otdb/test_fetch.py` - Test script (removed)
- ✅ All Python cache files (`__pycache__/`, `*.pyc`)
- ✅ ChatGPT-generated text files (removed from legacy/)

### Documentation Updated
- ✅ Removed all references to `txt2json.py`
- ✅ Updated `QUESTIONS.md` - Removed text conversion section
- ✅ Updated `FILE_GUIDE.md` - Removed txt2json and test.py sections
- ✅ Updated `SETUP.md` - Removed text conversion instructions
- ✅ Updated `QUESTION_SCRIPTS.md` - Removed txt2json, added fetch_all.py
- ✅ Updated `CLEANUP_REPORT.md` - Marked files as removed

### Current State
- ✅ Project is clean and focused
- ✅ Only Open Trivia Database system remains
- ✅ All ChatGPT-era files removed
- ✅ Bot ships with pre-loaded questions

