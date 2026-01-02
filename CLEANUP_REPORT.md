# Cleanup Report - Unused Files and Cleanup Opportunities

## 🔴 CRITICAL - Security Issue

### `chatgtp-api-key`
- **Location:** `/home/quizzer/quizzer/chatgtp-api-key`
- **Issue:** Contains an exposed API key
- **Action:** **DELETE IMMEDIATELY** or move to `.gitignore` if needed
- **Command:** `rm chatgtp-api-key` or `mv chatgtp-api-key .env` (if needed)

---

## 🟡 Python Cache Files (Safe to Delete)

### `__pycache__/` directories
- **Location:** Root and `otdb/` directory
- **Contains:** Python bytecode cache files
- **Action:** Safe to delete, will regenerate automatically
- **Command:** 
  ```bash
  find . -type d -name __pycache__ -exec rm -r {} +
  find . -name "*.pyc" -delete
  ```

### Old .pyc files referencing renamed files:
- `config_loader.cpython-313.pyc` (old name, now `config.py`)
- `db_manager.cpython-313.pyc` (old name, now `database.py`)
- `main_bot.cpython-313.pyc` (old name, now `bot.py`)
- `module_quizzer.cpython-313.pyc` (old name, now `quiz_game.py`)

---

## 🟡 Test/Development Files

### `test.py` ✅ REMOVED
- **Location:** Was in root directory
- **Purpose:** Simple test script for database
- **Status:** ✅ Removed during cleanup

### `otdb/test_fetch.py` ✅ REMOVED
- **Location:** Was in `otdb/` directory
- **Purpose:** Test script for fetch functionality
- **Status:** ✅ Removed during cleanup

### `quiz_data/test/`
- **Location:** `quiz_data/test/`
- **Contains:** 
  - Duplicate question files (all categories)
  - `fix.py`, `remove_html.py` scripts
- **Status:** Appears to be test/development directory
- **Action:** **DELETE** - these are duplicates of main quiz_data files

---

## 🟡 Backup Directory

### `backup/`
- **Location:** `backup/`
- **Contains:** 
  - Old Python files (`main_bot.py`, `module_quizzer.py`)
  - Old text question files
  - Old `startbot.sh`
- **Status:** Backup of old files before refactoring
- **Action:** Optional - keep for reference or archive/delete

---

## 🟡 Log Files

### Old log files:
- `Quizzer.log` (root)
- `bot_management.log` (root)
- `otdb/fetch_test.log`
- `logs/*.log` (various)

**Action:** Can be cleaned up periodically. Logs are useful for debugging but can grow large.

---

## 🟡 Documentation Files (Potential Consolidation)

### Multiple category-related docs:
- `CATEGORY_DISPLAY.md`
- `CATEGORY_PROPOSALS.md`
- `CATEGORY_REDESIGN.md`
- `CATEGORY_SYSTEM_SUMMARY.md`
- `HIERARCHICAL_CATEGORIES.md`
- `DYNAMIC_CATEGORIES.md`
- `DYNAMIC_SYSTEM_READY.md`

**Action:** Consider consolidating into a single `CATEGORIES.md` file

### Multiple fetch-related docs:
- `otdb/DESIGN.md`
- `otdb/FETCH_ALL.md`
- `otdb/EARLY_EXIT.md`
- `otdb/RATE_LIMIT_FIX.md`
- `otdb/TEST_RESULTS.md`

**Action:** Consider consolidating into `otdb/README.md`

---

## 🟢 Files to Keep

### Core application files:
- ✅ `bot.py`, `quiz_game.py`, `database.py`, `config.py`, `admin.py`
- ✅ `run.py` (entry point)
- ✅ `view_leaderboard.py` (utility)
- ✅ `category_hierarchy.py`, `category_display.py` (new features)

### Tools:
- ✅ `tools/startbot.sh` (management script)
- ✅ `otdb/fetch.py` (fetch script)
- ✅ `otdb/fetch_all.py` (fetch all script)
- ✅ `otdb/category_mapper.py` (category mapping)

### Essential docs:
- ✅ `README.md` (main documentation)
- ✅ `FILE_GUIDE.md` (file reference)
- ✅ `CHANGELOG.md` (change history)

---

## 📋 Recommended Cleanup Commands

```bash
# 1. SECURITY: Remove exposed API key
rm chatgtp-api-key

# 2. Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

# 3. Remove test directory (duplicates)
rm -r quiz_data/test/

# 4. Optional: Clean old logs (keep recent ones)
# find logs/ -name "*.log" -mtime +30 -delete  # Delete logs older than 30 days

# 5. ✅ COMPLETED: Removed test scripts
# ✅ test.py - Removed
# ✅ otdb/test_fetch.py - Removed
# ✅ tools/txt2json.py - Removed (legacy ChatGPT converter)
```

---

## 📊 Summary

| Category | Count | Action |
|----------|-------|--------|
| 🔴 Security Issues | 1 | **DELETE IMMEDIATELY** |
| 🟡 Python Cache | 15+ files | Safe to delete |
| 🟡 Test Files | 3+ files | Optional cleanup |
| 🟡 Duplicate Data | 1 directory | Delete |
| 🟡 Old Logs | 7+ files | Optional cleanup |
| 🟡 Documentation | 13+ files | Consider consolidation |

---

## ⚠️ Before Cleaning

1. **Backup important data** (if not already backed up)
2. **Review test files** - make sure you don't need them
3. **Check backup/ directory** - might contain useful old code
4. **Review logs** - might have useful debugging info

---

## ✅ Safe Cleanup Script

```bash
#!/bin/bash
# Safe cleanup script

echo "Cleaning Python cache..."
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -delete

echo "Removing test directory (duplicates)..."
rm -r quiz_data/test/ 2>/dev/null

echo "Cleanup complete!"
```

