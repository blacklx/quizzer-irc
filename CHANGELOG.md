# Changelog

All notable changes to the Quizzer IRC Bot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.90] - 2026-01-02

### Added
- Apache 2.0 License
- Terms of Service (TERMS.md)
- Privacy Policy (PRIVACY.md)
- Copyright headers to all Python files (Copyright 2026 blacklx)
- `!admin stats` command - Shows comprehensive bot statistics
- IPv4/IPv6 bind address support with auto-detection
- Multiple admin verification methods (password, hostmask, combined)
- Admin password management commands (`!admin add_admin`, `!admin remove_admin`, `!admin set_password`, `!admin list_admins`)
- `.env` file support for environment variables
- Improved error detection and reporting in startbot.sh
- Virtual environment enforcement (venv-only installation)
- Comprehensive documentation updates

### Changed
- Standardized version to v0.90 across all files
- Improved screen session detection in startbot.sh
- Enhanced error handling and logging throughout
- Updated admin verification system to support multiple methods
- **Code formatting improvements** - Organized imports, added section separators, improved readability across all Python files
- **Configuration file improvements** - Enhanced `config.yaml.example` and `.env.example` with better organization, section separators, and comprehensive comments

### Fixed
- Game disconnect handling - Gracefully handles disconnections during active games
- Critical reconnection bug - Bot no longer crashes on connection failures
- Import errors in fetch scripts
- startbot.sh virtual environment handling
- Screen session detection issues
- IPv6 bind address tuple format handling

## [0.80] - 2025-11-15

### Added
- Hierarchical category system with 12 main categories and subcategories
- Dynamic category detection from files
- Smart category display to avoid IRC flooding
- Category matching with flexible syntax (e.g., "entertainment music")
- `category_hierarchy.py` - Dynamic category system
- `category_display.py` - Smart category display for IRC
- `otdb/fetch_all.py` - Script to download ALL questions from all categories
- `otdb/category_mapper.py` - Category normalization
- Rate limit handling with exponential backoff on 429 errors
- Duplicate prevention across all question files
- Early exit for fully collected categories

### Changed
- Category commands now support hierarchical navigation
- Question fetching improved with better error handling
- Category names normalized for consistency

## [0.70] - 2025-08-20

### Added
- `run.py` - Clean entry point with proper error handling
- `config.py` - Centralized configuration loading module
- Comprehensive docstrings to all Python modules
- Module, class, and function documentation
- `FILE_GUIDE.md` - Detailed file descriptions
- `requirements.txt` - Python dependencies list

### Changed
- Renamed `main_bot.py` → `bot.py`
- Renamed `module_quizzer.py` → `quiz_game.py`
- Renamed `read_db.py` → `view_leaderboard.py`
- Renamed `db_manager.py` → `database.py`
- Renamed `config_loader.py` → `config.py`
- Renamed `RachnarBot` class → `QuizzerBot`
- Updated `startbot.sh` to use `run.py` as entry point
- Improved code organization and structure

## [0.60] - 2025-05-10

### Added
- Enhanced reconnection logic with exponential backoff
- Better error handling for connection failures
- Improved logging throughout the bot
- Game state preservation during disconnects
- Automatic game cancellation on disconnect with partial score display

### Fixed
- Bot crash on connection failures
- Reconnection attempts now properly reset after successful connection
- Game state cleanup on disconnect

## [0.50] - 2024-12-18

### Added
- `startbot.sh` management script improvements
- Auto-detection of directory path (removed hardcoded paths)
- Environment variable check for `NICKSERV_PASSWORD`
- Screen session management
- Cron job support for automatic bot monitoring
- Bot status checking functionality

### Changed
- `startbot.sh` now auto-detects bot directory
- Improved script error handling

## [0.40] - 2024-09-05

### Added
- Open Trivia Database integration
- Question fetching from Open Trivia DB API
- `otdb/fetch.py` - Question fetching script
- Support for 24+ question categories
- Pre-loaded question database in `quiz_data/`
- JSON question file format
- HTML entity decoding for questions

### Changed
- Question storage format from text to JSON
- Improved question loading performance

## [0.30] - 2024-03-22

### Added
- Admin command system
- `admin.py` - Admin command handlers
- Admin verification via NickServ
- Admin commands: `!admin stop`, `!admin restart`, `!admin stop_game`, `!admin set_rate_limit`, `!admin msg`
- Rate limiting for quiz commands
- Admin help command

### Changed
- Improved command routing
- Better permission checking

## [0.20] - 2023-11-08

### Added
- Score tracking and leaderboard
- `database.py` - SQLite database operations
- Persistent score storage
- `!leaderboard` command
- `view_leaderboard.py` - Database viewer utility
- Score statistics (total score, games played, highest score)

### Changed
- Score system now uses database instead of in-memory storage

## [0.10] - 2023-06-15

### Added
- Basic quiz game functionality
- `quiz_game.py` - Core quiz game logic
- Question asking and answer processing
- Multiple choice question support
- Timed quiz rounds
- Participant management
- Score calculation
- `!start` command to begin quizzes
- `!join` command to join quizzes
- `!a <answer>` command to answer questions
- `!categories` command to list categories
- `!help` command

### Changed
- Initial quiz game implementation

## [0.01] - 2022-05-05

### Added
- Initial project creation
- Basic IRC bot framework
- IRC connection handling
- Channel joining
- Message handling
- Basic command structure
- Configuration file support (`config.yaml`)
- NickServ authentication support
- SSL/TLS connection support
- Reconnection logic
- Logging system

---

## Version History Summary

- **v0.90** (2026-01-02) - Legal documentation, admin verification improvements, IPv6 support
- **v0.80** (2025-11-15) - Hierarchical category system, improved question fetching
- **v0.70** (2025-08-20) - Code organization, documentation, entry point improvements
- **v0.60** (2025-05-10) - Enhanced reconnection and error handling
- **v0.50** (2024-12-18) - Management script improvements
- **v0.40** (2024-09-05) - Open Trivia Database integration
- **v0.30** (2024-03-22) - Admin command system
- **v0.20** (2023-11-08) - Score tracking and leaderboard
- **v0.10** (2023-06-15) - Basic quiz game functionality
- **v0.01** (2022-05-05) - Initial project creation

---

**Copyright 2026 blacklx** - Licensed under Apache License 2.0
