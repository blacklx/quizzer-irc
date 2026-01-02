# Quizzer IRC Bot

An IRC bot that hosts interactive quiz games on IRC channels.

**Repository:** [https://github.com/blacklx/quizzer-irc](https://github.com/blacklx/quizzer-irc)

## What It Does

- Hosts timed quiz rounds with multiple-choice questions
- Supports multiple categories (Animals, Science, History, etc.)
- Tracks scores and maintains a leaderboard
- Allows users to join quizzes and answer questions
- Provides admin commands for bot management

## Quick Start

### Prerequisites
- Python 3.6+ (Python 3.8+ recommended)
- IRC server access
- NickServ account (if using NickServ authentication)

### Quick Setup

1. **Install dependencies (creates virtual environment automatically):**
   ```bash
   ./install.sh
   ```
   
   **Note:** This bot REQUIRES a virtual environment. The install script will create `.venv` and install all dependencies there.

2. **Configure the bot:**
   ```bash
   cp config.yaml.example config.yaml
   ```
   Then edit `config.yaml` with your IRC server details, channel, and settings.

3. **Set password (choose one method):**
   - **Option A:** Use `.env` file (recommended):
     ```bash
     cp .env.example .env
     # Edit .env and add your password
     ```
   - **Option B:** Set environment variable:
     ```bash
     export NICKSERV_PASSWORD="your_nickserv_password"
     ```
   - **Option C:** Add password directly to `config.yaml` (not recommended for production)

4. **Verify questions (optional):**
   The bot comes with a pre-loaded question database. To verify:
   ```bash
   ls quiz_data/*.json | wc -l  # Should show 24+ files
   ```

5. **Run the bot:**
   
   **Option A: Direct run (activate venv first):**
   ```bash
   source .venv/bin/activate
   python3 run.py
   ```
   
   **Option B: Use management script (recommended):**
   ```bash
   ./tools/startbot.sh start
   ```
   
   The management script automatically activates the virtual environment.

**For detailed setup instructions, see [SETUP.md](SETUP.md)**

## Commands

### Public Commands (in channel)
- `!start <category>` - Start a quiz in a category
  - `!start entertainment` - Random from all Entertainment subcategories
  - `!start entertainment music` - Entertainment Music specifically
  - `!start science` - Random from all Science subcategories
  - `!start animals` - Animals category
  - `!start random` - Random from all categories
- `!categories` - List all main categories (grouped)
- `!categories <category>` - Show subcategories for a category (e.g., `!categories entertainment`)
- `!leaderboard` - View top 10 scorers
- `!help` - Show help message

### Private Commands (via PM to bot)
- `!join` - Join an upcoming quiz
- `!a <answer>` - Answer a question (e.g., `!a A` or `!a True`)

### Admin Commands (via PM, requires admin status)

**Admin Verification:**
The bot supports multiple admin verification methods (configurable in `config.yaml`):
- **NickServ** (default) - Uses IRC network's NickServ service
- **Password** - Password-based verification with sessions
- **Hostmask** - Automatic verification by hostmask
- **Combined** - Multiple methods (password OR hostmask)

**Standard Admin Commands:**
- `!admin stop_game` - Stop the current quiz
- `!admin restart` - Restart the bot
- `!admin stop` - Stop the bot
- `!admin set_rate_limit <seconds>` - Change command rate limit
- `!admin msg <target> <message>` - Send message from bot
- `!admin stats` - Show comprehensive bot statistics

**Password-Based Admin Commands** (if using password verification):
- `!admin verify <password>` - Verify password and start session
- `!admin add_admin <nick> <password>` - Add new admin
- `!admin remove_admin <nick>` - Remove admin
- `!admin set_password <nick> <password>` - Set/update admin password
- `!admin list_admins` - List all admin nicknames

## File Structure

### Core Bot Files
- `bot.py` - Main IRC bot (connects to IRC, handles events)
- `quiz_game.py` - Quiz game logic (questions, scoring, game flow)
- `admin.py` - Admin command handlers
- `admin_verifier.py` - Admin verification system (password, hostmask, NickServ)
- `database.py` - Database operations (score storage)
- `config.py` - Configuration loader module
- `category_hierarchy.py` - Dynamic category system
- `category_display.py` - Smart category display for IRC
- `config.yaml` - Configuration file
- `run.py` - Entry point (recommended way to start)

### Data Directories
- `quiz_data/` - Question JSON files
- `db/` - SQLite database
- `logs/` - Log files

### Tools & Scripts
- `tools/startbot.sh` - Bot management script
- `otdb/fetch.py` - Fetch questions from Open Trivia DB (updates database)
- `otdb/fetch_all.py` - Fetch ALL questions from all categories (updates database)
- `otdb/category_mapper.py` - Category name normalization
- `view_leaderboard.py` - View database contents

See `FILE_GUIDE.md` for detailed file descriptions.

## Configuration

Edit `config.yaml` to configure:
- IRC server and channel
- Quiz settings (question count, time limits)
- Admin nicknames
- Logging options

**Important:** Set `NICKSERV_PASSWORD` environment variable instead of putting password in config file.

## Category System

The bot uses a **hierarchical category system** that automatically organizes categories. See `CATEGORIES.md` for complete documentation.

- **12 main categories** shown in `!categories` command
- **Entertainment** and **Science** have subcategories
- **Other categories** are standalone (Animals, Art, Geography, etc.)

The system **automatically detects** categories from your `quiz_data/` directory, so new categories from the fetch script are included automatically.

### Category Examples

```
!start entertainment              # Random from all Entertainment
!start entertainment music        # Entertainment Music specifically
!start entertainment video games  # Entertainment Video Games specifically
!start science                    # Random from all Science
!start science computers          # Science Computers specifically
!start animals                    # Animals category
```

## Questions Database

**The bot comes with a pre-loaded question database** in the `quiz_data/` directory with thousands of questions across all categories. You can start using the bot immediately without fetching questions.

### Updating Questions

To add more questions or update existing ones, use the fetch scripts:

**Fetch all questions (updates existing database):**
```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

This will download all questions from all categories, respecting rate limits and preventing duplicates.

**Fetch specific amount:**
```bash
cd otdb
python3 fetch.py --once --amount 50 --output ../quiz_data
```

### Question Format

Questions are stored in JSON format in `quiz_data/` directory.

Format: `{category}_questions.json`

Example question structure:
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

## Bot Management

Use `tools/startbot.sh` to manage the bot:

```bash
./tools/startbot.sh start      # Start bot in screen session
./tools/startbot.sh stop       # Stop bot
./tools/startbot.sh restart    # Restart bot
./tools/startbot.sh check      # Check if bot is running
```

## Troubleshooting

See [SETUP.md](SETUP.md) for detailed troubleshooting steps.

**Common issues:**

**Bot won't start:**
- Check `NICKSERV_PASSWORD` environment variable is set
- Verify IRC server details in `config.yaml`
- Check log files in `logs/` directory

**Can't connect to IRC:**
- Verify server address and port
- Check SSL settings match server requirements
- Ensure firewall allows connection

**Questions not loading:**
- Verify `quiz_data/` directory exists
- Check JSON files are valid format
- Check file permissions

## Features

- ✅ **Hierarchical Categories** - Smart category system with 12 main categories
- ✅ **Dynamic Category Detection** - Automatically detects new categories
- ✅ **Question Fetching** - Tools to fetch questions from Open Trivia Database
- ✅ **Duplicate Prevention** - Prevents duplicate questions and categories
- ✅ **Rate Limiting** - Built-in rate limiting for API requests
- ✅ **Thread-Safe** - Proper locking for concurrent operations
- ✅ **Admin Commands** - Full admin control via IRC
- ✅ **Leaderboard** - Persistent score tracking

## Version

Quizzer v0.90

## License

Copyright 2026 blacklx

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

See [LICENSE](LICENSE) for the full license text.
See [TERMS.md](TERMS.md) for Terms of Service.
See [PRIVACY.md](PRIVACY.md) for Privacy Policy.

