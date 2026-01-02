# File Guide - What Does What?

Quick reference for understanding the codebase.

**Copyright 2026 blacklx** - Licensed under Apache License 2.0

---

## 📁 Core Bot Files

### `bot.py` - **Main IRC Bot**
**What it does:** The main entry point that connects to IRC and handles all IRC events.

**Key responsibilities:**
- Connects to IRC server
- Handles IRC events (messages, joins, disconnects)
- Routes commands to appropriate handlers
- Manages reconnection logic
- Handles admin command authentication via NickServ

**Key class:** `QuizzerBot`

**Main functions:**
- `on_pubmsg()` - Handles public channel messages (!start, !categories, !leaderboard, !help)
- `on_privmsg()` - Handles private messages (!join, !a for answers, admin commands)
- `on_notice()` - Handles NickServ notices for admin verification
- `on_disconnect()` - Handles reconnection when disconnected

---

### `quiz_game.py` - **Quiz Game Logic**
**What it does:** Contains all the quiz game mechanics and question handling.

**Key responsibilities:**
- Manages quiz game state (active/inactive, participants, scores)
- Loads questions from JSON files
- Handles question asking and answer processing
- Tracks scores and participants
- Manages quiz timing and flow

**Key class:** `QuizGame`

**Main functions:**
- `load_questions()` - Loads questions from JSON files by category
- `ask_question()` - Displays a question to the channel
- `process_answer()` - Checks if user's answer is correct and updates score
- `end_quiz()` - Ends quiz, displays results, saves scores
- `handle_start_command()` - Starts a new quiz (called from bot)
- `handle_join_command()` - Allows users to join a quiz
- `start_quiz()` - Runs the quiz game loop

---

### `admin.py` - **Admin Commands**
**What it does:** Handles all admin-only commands.

**Key responsibilities:**
- Processes admin commands (stop, restart, rate limit, etc.)
- Manages bot lifecycle (stop/restart)
- Admin management (add/remove admins, set passwords)
- Integrates with AdminVerifier for authentication

**Key class:** `AdminCommands`

**Main functions:**
- `is_admin()` - Checks if user is an admin
- `stop_game()` - Stops current quiz game
- `restart_bot()` - Restarts the bot
- `stop_bot()` - Stops the bot
- `set_rate_limit()` - Changes rate limit for commands
- `send_message()` - Sends message from bot
- `get_bot_stats()` - Shows comprehensive bot statistics
- `add_admin()` - Add new admin (password method)
- `remove_admin()` - Remove admin (password method)
- `set_password()` - Set/update admin password
- `list_admins()` - List all admin nicknames

---

### `admin_verifier.py` - **Admin Verification System**
**What it does:** Provides multiple admin verification methods.

**Key responsibilities:**
- Password-based verification (bcrypt hashing)
- Session management (time-based expiration)
- Hostmask-based verification
- Rate limiting (prevents brute force)
- Auto-hashing passwords on first use

**Key class:** `AdminVerifier`

**Supported methods:**
- **NickServ** (default) - Uses IRC network's NickServ
- **Password** - Password-based with sessions
- **Hostmask** - Automatic verification by hostmask
- **Combined** - Multiple methods (password OR hostmask)

**Main functions:**
- `verify_password()` - Verify password and grant session
- `verify_session()` - Check if admin has valid session
- `verify_hostmask()` - Verify admin by hostmask
- `set_password()` - Set/update admin password (hashes automatically)
- `is_admin()` - Check if nickname is in admin list

---

### `database.py` - **Database Operations**
**What it does:** Handles all database operations for storing scores.

**Key responsibilities:**
- Creates database and tables
- Stores quiz scores
- Retrieves leaderboard data

**Main functions:**
- `create_database()` - Creates SQLite database and tables
- `store_score()` - Saves a user's score to database
- `get_leaderboard()` - Gets top scorers from database

---

## 📁 Utility Files

### `view_leaderboard.py` - **Database Viewer**
**What it does:** Simple script to view database contents (for debugging).

**Usage:** `python view_leaderboard.py`

---

---

## 📁 Configuration

### `config.yaml` - **Configuration File**
**What it does:** Contains all bot settings.

**Sections:**
- `quiz_settings` - Quiz game settings (question count, time limits, rate limiting)
- `bot_settings` - IRC connection settings (server, port, channel, nickname)
- `nickserv_settings` - NickServ authentication settings
- `bot_log_settings` - Logging configuration
- `admin_settings` - Admin configuration:
  - `verification_method` - Admin verification method ("nickserv", "password", "hostmask", "combined")
  - `admins` - List of admin nicknames
  - `password_settings` - Password verification settings (if using password method)
  - `hostmask_settings` - Hostmask verification settings (if using hostmask method)

**Note:** Passwords should be in `.env` file or environment variables, not in this file.

---

### `.env` - **Environment Variables**
**What it does:** Stores sensitive data (passwords) outside of config files.

**Contents:**
- `NICKSERV_PASSWORD` - NickServ authentication password
- `ADMIN_PASSWORD_<nickname>` - Admin passwords (for password-based verification)

**Note:** This file is in `.gitignore` and should never be committed to git.
Use `.env.example` as a template.

---

### `admin_passwords.yaml` - **Admin Password Hashes** (Auto-generated)
**What it does:** Stores hashed admin passwords (auto-generated by bot).

**Contents:**
- Hashed passwords (bcrypt) for each admin
- Auto-created when passwords are first used
- Plaintext passwords are never stored here

**Note:** This file is in `.gitignore` and should never be committed to git.
The bot automatically manages this file.

---

## 📁 Scripts

### `tools/startbot.sh` - **Bot Management Script**
**What it does:** Manages bot lifecycle (start, stop, restart, check status).

**Usage:**
```bash
./tools/startbot.sh start    # Start bot
./tools/startbot.sh stop     # Stop bot
./tools/startbot.sh restart  # Restart bot
./tools/startbot.sh check    # Check if bot is running
```

**Note:** Script now auto-detects directory path (fixed in refactoring).

---

### `category_hierarchy.py` - **Dynamic Category System**
**What it does:** Automatically builds category hierarchy from question files.

**Key features:**
- Auto-detects categories from `quiz_data/` directory
- Groups Entertainment and Science subcategories
- Handles new categories automatically
- Provides category matching for user input

**Key functions:**
- `build_category_hierarchy()` - Scans files and builds hierarchy
- `find_category_match()` - Matches user input to categories
- `format_category_display()` - Formats categories for IRC display

---

### `category_display.py` - **Smart Category Display**
**What it does:** Handles category listing in IRC-friendly format.

**Key features:**
- Groups categories to avoid channel flooding
- Supports pagination and search
- Formats categories for IRC message limits

---

---

### `otdb/fetch.py` - **Question Fetcher**
**What it does:** Fetches questions from Open Trivia Database API.

**Usage:**
```bash
cd otdb
python3 fetch.py --once --amount 50 --output ../quiz_data
```

**Features:**
- Prevents duplicate questions
- Normalizes category names
- Handles HTML entities
- Shuffles answers

---

### `otdb/fetch_all.py` - **Fetch All Questions**
**What it does:** Downloads ALL questions from all categories.

**Usage:**
```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

**Features:**
- Fetches from all 24 categories
- Respects API rate limits
- Early exit for fully collected categories
- Exponential backoff on rate limit errors

---

### `otdb/category_mapper.py` - **Category Name Normalization**
**What it does:** Maps API category names to standardized bot format.

**Key functions:**
- `normalize_category()` - Normalizes category names
- `get_filename_for_category()` - Generates consistent filenames

---

## 📁 Data Directories

### `quiz_data/` - **Question Files**
**What it does:** Contains all quiz questions in JSON format.

**Format:** `{category}_questions.json`

**Example:** `Animals_questions.json`, `Science_questions.json`

---

### `db/` - **Database Files**
**What it does:** Contains SQLite database file.

**File:** `quiz_leaderboard.db` - Stores all quiz scores

---

### `logs/` - **Log Files**
**What it does:** Contains all log files.

**Files:**
- `Quizzer.log` - Main bot log
- `quiz_game.log` - Quiz game events
- `db_manager.log` - Database operations
- `admin_actions.log` - Admin command logs

---

## 🔄 How It All Works Together

1. **Bot starts** (`bot.py`)
   - Loads config
   - Connects to IRC
   - Creates `QuizGame` instance

2. **User starts quiz** (`!start` command)
   - Bot calls `handle_start_command()` in `quiz_game.py`
   - Quiz game loads questions
   - Announces quiz start, allows joining

3. **Users join** (`!join` via PM)
   - Bot calls `handle_join_command()` in `quiz_game.py`
   - Adds user to participants list

4. **Quiz runs** (`start_quiz()` function)
   - Asks questions one by one
   - Users answer via PM (`!a <answer>`)
   - `process_answer()` checks answers and updates scores

5. **Quiz ends**
   - `end_quiz()` displays results
   - Scores saved to database via `database.py`
   - Game state reset

6. **Admin commands**
   - Admin sends `!admin <command>` via PM
   - Bot verifies via NickServ
   - `AdminCommands` class handles the command

---

## 🎯 Quick Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `bot.py` | IRC connection & event handling | Adding new IRC commands/events |
| `quiz_game.py` | Quiz game logic | Changing quiz mechanics |
| `admin.py` | Admin commands | Adding new admin features |
| `database.py` | Database operations | Changing database schema/queries |
| `config.py` | Configuration loader | Changing config loading logic |
| `config.yaml` | Configuration | Changing bot settings |
| `tools/startbot.sh` | Bot management | Changing deployment/startup |

---

## ✅ Naming (All Fixed!)

- `RachnarBot` → ✅ `QuizzerBot`
- `module_quizzer.py` → ✅ `quiz_game.py`
- `main_bot.py` → ✅ `bot.py`
- `read_db.py` → ✅ `view_leaderboard.py`
- `db_manager.py` → ✅ `database.py`
- `config_loader.py` → ✅ `config.py`

## 🆕 Recent Additions

- ✅ `category_hierarchy.py` - Dynamic category system
- ✅ `category_display.py` - Smart category display
- ✅ `otdb/fetch_all.py` - Fetch all questions script
- ✅ `otdb/category_mapper.py` - Category normalization

