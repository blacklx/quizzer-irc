# Quizzer IRC Bot v0.90 - Initial Release

An IRC bot that hosts interactive quiz games on IRC channels.

## Features

- **Interactive Quiz Games** - Host timed quiz rounds with multiple-choice questions
- **Multiple Categories** - Support for 24+ categories with subcategories (Animals, Science, History, Entertainment, etc.)
- **Score Tracking** - Maintains a leaderboard with persistent database storage
- **Admin Commands** - Comprehensive bot management commands
- **Multiple Admin Verification Methods**:
  - NickServ (default, most secure)
  - Password-based (with session management)
  - Hostmask-based (automatic verification)
  - Combined (password OR hostmask)
- **IPv4/IPv6 Support** - Bind to specific IP addresses or hostnames
- **Virtual Environment Support** - Enforced venv-only installation
- **Comprehensive Documentation** - Complete setup guides and file documentation

## Installation

See [SETUP.md](SETUP.md) for detailed installation instructions.

### Quick Start

```bash
# Clone the repository
git clone https://github.com/blacklx/quizzer-irc.git
cd quizzer-irc

# Install dependencies (creates venv automatically)
./install.sh

# Configure the bot
cp config.yaml.example config.yaml
# Edit config.yaml with your IRC server details

# Set passwords
cp .env.example .env
# Add your passwords to .env file

# Start the bot
./tools/startbot.sh start
```

## Requirements

- Python 3.6+ (Python 3.8+ recommended)
- IRC server access
- NickServ account (if using NickServ authentication)

## Documentation

- **[README.md](README.md)** - Overview, features, and usage
- **[SETUP.md](SETUP.md)** - Complete installation and configuration guide
- **[CHANGELOG.md](CHANGELOG.md)** - Full changelog and improvements
- **[FILE_GUIDE.md](FILE_GUIDE.md)** - Detailed file descriptions

## What's New in v0.90

### Legal & Licensing
- Added Apache 2.0 License
- Added Terms of Service (TERMS.md)
- Added Privacy Policy (PRIVACY.md)
- Added copyright headers to all files

### New Features
- `!admin stats` command - Shows comprehensive bot statistics
- Game disconnect handling - Gracefully handles disconnections during active games
- Enhanced reconnection logic - Better error handling and logging
- Multiple admin verification methods
- IPv4/IPv6 bind address support
- Virtual environment enforcement

### Improvements
- **Code formatting** - Organized imports, added section separators, improved readability across all Python files
- **Configuration files** - Enhanced `config.yaml.example` and `.env.example` with better organization, section separators, and comprehensive comments

### Bug Fixes
- Fixed critical reconnection bug
- Fixed import errors in fetch scripts
- Fixed startbot.sh virtual environment handling
- Improved error detection and reporting
- Fixed IPv6 bind address tuple format handling

## Commands

### Public Commands
- `!start <category>` - Start a quiz (e.g., `!start entertainment`, `!start entertainment music`)
- `!categories` - List all main categories
- `!categories <category>` - Show subcategories for a category
- `!leaderboard` - View top 10 scorers
- `!help` - Show help message

### Private Commands (via PM)
- `!join` - Join an upcoming quiz
- `!a <answer>` - Answer a question (e.g., `!a A` or `!a True`)

### Admin Commands (via PM, requires admin status)
- `!admin stop_game` - Stop the current quiz
- `!admin restart` - Restart the bot
- `!admin stop` - Stop the bot
- `!admin stats` - Show comprehensive bot statistics
- `!admin set_rate_limit <seconds>` - Change command rate limit
- `!admin msg <target> <message>` - Send message from bot

See [README.md](README.md) for complete command reference.

## License

Licensed under the Apache License, Version 2.0 - see [LICENSE](LICENSE) file for details.

## Repository

**GitHub:** https://github.com/blacklx/quizzer-irc

## Support

For issues, questions, or contributions, please visit the GitHub repository.

---

**Copyright 2026 blacklx**

