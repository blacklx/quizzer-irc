# File Naming Proposal - Cleaner Structure

## Current vs Proposed Names

### Core Bot Files

| Current Name | Proposed Name | Reason |
|-------------|---------------|--------|
| `main_bot.py` | `bot.py` | Simpler, clearer purpose |
| `module_quizzer.py` | `quiz_game.py` | Much clearer - it's the quiz game logic |
| `db_manager.py` | `database.py` | More standard naming convention |
| `config_loader.py` | `config.py` | Simpler, standard naming |

### Utility Files

| Current Name | Proposed Name | Status |
|-------------|---------------|--------|
| `view_leaderboard.py` | ✅ Already good | - |
| `admin.py` | ✅ Already good | - |
| `test.py` | ✅ Removed | - |

## File Structure Comparison

### Current Structure
```
quizzer/
├── main_bot.py          ❓ "main" is vague
├── module_quizzer.py    ❓ "module_" prefix is redundant
├── db_manager.py        ❓ "manager" is generic
├── config_loader.py     ❓ "loader" is redundant
├── admin.py             ✅ Clear
├── view_leaderboard.py   ✅ Clear
└── run.py               ✅ Clear
```

### Proposed Structure
```
quizzer/
├── bot.py               ✅ Clear purpose
├── quiz_game.py         ✅ Clear purpose
├── database.py          ✅ Clear purpose
├── config.py            ✅ Clear purpose
├── admin.py             ✅ Clear
├── view_leaderboard.py  ✅ Clear
└── run.py               ✅ Clear
```

## Benefits

1. **Shorter names** - Easier to type and remember
2. **Clearer purpose** - Names immediately tell you what they do
3. **Standard conventions** - Follows Python naming best practices
4. **Less redundancy** - No unnecessary prefixes like "module_" or "manager"

## Impact

- **Imports need updating** in:
  - `bot.py` (was main_bot.py)
  - `run.py`
  - `admin.py`
  - `tools/startbot.sh`

- **No functional changes** - Just renaming for clarity

## Recommendation

✅ **Yes, rename them!** The proposed names are:
- More intuitive
- Follow standard Python conventions
- Make the codebase easier to navigate
- Remove unnecessary prefixes

