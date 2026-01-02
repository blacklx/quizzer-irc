# Setup Guide - Quizzer IRC Bot

Complete step-by-step setup instructions for the Quizzer IRC Bot.

## Prerequisites

### Required

- **Python 3.6+** (Python 3.8+ recommended)
- **IRC server access** (or your own IRC server)
- **NickServ account** (if your IRC network requires authentication)

### Optional

- **Screen or tmux** (for running bot in background)
- **Systemd** (for service management)

## Step 1: Clone/Download the Bot

If you have the bot files, skip to Step 2. Otherwise:

```bash
# If using git
git clone https://github.com/blacklx/quizzer-irc.git
cd quizzer-irc

# Or download and extract the bot files
```

## Step 2: Install Dependencies

**IMPORTANT: This bot REQUIRES a virtual environment. The installation script will create one automatically.**

### Automated Installation (Recommended)

Use the provided installation script:

```bash
./install.sh
```

This script will:
- Detect your operating system automatically
- Check for required system packages (python3, python3-venv, python3-pip)
- Install missing system packages automatically (requires sudo)
- Create a virtual environment (`.venv`)
- Install all required Python packages in the virtual environment
- Verify the installation

**Note:** The script may require `sudo` privileges to install system packages.

### Manual Installation

If you prefer to install manually:

**1. Install system packages:**

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-venv python3-pip

# RedHat/CentOS/Fedora
sudo dnf install python3 python3-pip
# Note: On RHEL/CentOS/Fedora, venv is usually included with python3
```

**2. Create virtual environment:**

```bash
# Create virtual environment (REQUIRED)
python3 -m venv .venv
```

**3. Activate virtual environment and install dependencies:**

```bash
# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

**Note:** You must activate the virtual environment before running the bot.

## Step 3: Configure the Bot

### 3.1 Edit `config.yaml`

**First, copy the example configuration:**
```bash
cp config.yaml.example config.yaml
```

Then open `config.yaml` and configure:

```yaml
quiz_settings:
  question_count: 15          # Number of questions per quiz
  answer_time_limit: 25       # Seconds to answer each question
  RATE_LIMIT: 3               # Seconds between user commands

bot_settings:
  server: "irc.example.org"    # Your IRC server
  port: 6697                   # IRC port (6697 for SSL, 6667 for non-SSL)
  channel: "#quizzer"         # Channel to join
  nickname: "Quizzer"          # Bot's nickname
  realname: "Quizzer"          # Bot's realname
  use_ssl: true                # true for SSL, false for plain text
  reconnect_interval: 15       # Seconds to wait before reconnecting
  rejoin_interval: 15          # Seconds to wait before rejoining channel
  nickname_retry_interval: 30  # Seconds to wait before retrying nickname

nickserv_settings:
  use_nickserv: true           # Set to false if not using NickServ
  nickserv_name: "N"           # NickServ service name (usually "N" or "NickServ")
  nickserv_account: "Quizzer"  # Your NickServ account name
  nickserv_password: ""        # Leave empty, use environment variable instead
  nickserv_command_format: "IDENTIFY {account} {password}"

bot_log_settings:
  enable_logging: true         # Enable file logging
  enable_debug: false         # Enable debug logging
  log_filename: "Quizzer.log" # Log file name

admin_settings:
  # Verification method: "nickserv" (default), "password", "hostmask", or "combined"
  verification_method: "nickserv"
  
  admins: ["YourNick"]         # List of admin nicknames
  
  # Password-based verification settings (if verification_method is "password" or "combined")
  password_settings:
    session_timeout: 3600      # Session duration in seconds (default: 1 hour)
    max_attempts: 3            # Maximum failed password attempts before lockout
    lockout_duration: 300       # Lockout duration in seconds (default: 5 minutes)
  
  # Hostmask-based verification settings (if verification_method is "hostmask" or "combined")
  hostmask_settings:
    hostmasks:
      # "YourNick": ["*!*@trusted.host", "*!*@*.example.com"]
```

### 3.2 Set Environment Variable

**Important:** Never put your NickServ password in `config.yaml`. Use an environment variable instead:

```bash
# Linux/Mac
export NICKSERV_PASSWORD="your_nickserv_password_here"

# Windows (Command Prompt)
set NICKSERV_PASSWORD=your_nickserv_password_here

# Windows (PowerShell)
$env:NICKSERV_PASSWORD="your_nickserv_password_here"
```

**Or use a `.env` file (recommended):**

```bash
cp .env.example .env
# Edit .env and add:
# NICKSERV_PASSWORD=your_nickserv_password_here
# 
# If using password-based admin verification, also add:
# ADMIN_PASSWORD_YourNick=your_admin_password_here
```

**To make environment variable permanent:**

**Linux/Mac** - Add to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export NICKSERV_PASSWORD="your_password"' >> ~/.bashrc
source ~/.bashrc
```

**Windows** - Set as system environment variable through Control Panel.

## Step 4: Question Database

**Good news:** The bot comes with a **pre-loaded question database** in `quiz_data/` with thousands of questions across all categories. You can skip this step and start using the bot immediately!

### Verify Questions Are Present

```bash
ls quiz_data/*.json | wc -l  # Should show 24+ category files
```

### Optional: Update Questions

To add more questions or update the database:

**Fetch all questions (updates existing database):**

```bash
# Activate virtual environment first
source .venv/bin/activate

cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

**Fetch specific amount:**

```bash
# Activate virtual environment first
source .venv/bin/activate

cd otdb
python3 fetch.py --once --amount 100 --output ../quiz_data
```

### Legacy: Text File Conversion

Text file conversion tools have been removed. Use fetch scripts instead.

## Step 5: Test the Configuration

**Note:** Activate the virtual environment before running tests:

```bash
source .venv/bin/activate
```

### 5.1 Test Configuration Loading

```bash
python3 -c "from config import load_config; config = load_config(); print('✓ Config loaded successfully')"
```

### 5.2 Test Database

```bash
python3 -c "from database import create_database; create_database(); print('✓ Database created successfully')"
```

### 5.3 Test Question Loading

```bash
python3 -c "from quiz_game import QuizGame; qg = QuizGame('#test', 15, 25); print('✓ QuizGame initialized')"
```

## Step 6: Run the Bot

### Option A: Direct Run (for testing)

```bash
python3 run.py
```

### Option B: Using Management Script (recommended)

```bash
# Make script executable
chmod +x tools/startbot.sh

# Start bot in screen session
./tools/startbot.sh start

# Check if running
./tools/startbot.sh check

# View bot output
screen -r quizzer

# Stop bot
./tools/startbot.sh stop
```

### Option C: Using Screen Manually

```bash
# Start screen session
screen -S quizzer

# Activate virtual environment and run bot
source .venv/bin/activate
python3 run.py

# Detach: Press Ctrl+A, then D
# Reattach: screen -r quizzer
```

### Option D: Using Systemd (Linux)

Create `/etc/systemd/system/quizzer.service`:

```ini

```ini
[Unit]
Description=Quizzer IRC Bot
After=network.target

[Service]
Type=simple
User=quizzer
WorkingDirectory=/home/quizzer/quizzer
Environment="NICKSERV_PASSWORD=your_password_here"
ExecStart=/usr/bin/python3 /home/quizzer/quizzer/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable quizzer
sudo systemctl start quizzer
sudo systemctl status quizzer
```

## Step 7: Verify Bot is Working

1. **Check IRC connection:**

   - Bot should appear in your IRC channel
   - Bot should respond to `!help` command

2. **Test commands:**

   ```irc
   !categories          # Should list categories
   !start random        # Should start a quiz
   !join                # Join the quiz (via PM)
   ```

3. **Check logs:**

   ```bash
   tail -f logs/Quizzer.log
   ```

## Troubleshooting

### Bot Won't Start

**Check environment variable:**

```bash
echo $NICKSERV_PASSWORD  # Should show your password
```

**Check configuration:**

```bash
python3 -c "from config import load_config; load_config()"
```

**Check Python version:**

```bash
python3 --version  # Should be 3.6+
```

### Can't Connect to IRC

**Verify server details:**

- Check `server` and `port` in `config.yaml`
- Verify `use_ssl` matches server requirements
- Test connection manually: `telnet irc.example.org 6667`

**Check firewall:**

- Ensure port is not blocked
- Check if server requires SSL

### Questions Not Loading

**Check directory:**

```bash
ls quiz_data/  # Should show .json files
```

**Check file format:**

```bash
python3 -c "import json; json.load(open('quiz_data/Animals_questions.json'))"
```

**Check permissions:**

```bash
ls -la quiz_data/  # Ensure files are readable
```

### Bot Not Responding

**Check if bot is in channel:**

- Verify bot nickname appears in channel user list
- Check if bot was kicked/banned

**Check logs:**

```bash
tail -f logs/Quizzer.log
tail -f logs/quiz_game.log
```

**Check rate limiting:**

- Wait a few seconds between commands
- Check `RATE_LIMIT` setting in `config.yaml`

## Post-Setup

### Update Questions Database

The bot comes with a pre-loaded database, but you can update it:

**Periodically fetch new questions:**

```bash
cd otdb
python3 fetch_all.py --output ../quiz_data --delay 5.0
```

This will add new questions while preventing duplicates.

### View Leaderboard

```bash
python3 view_leaderboard.py
```

### Update Bot

If you update the bot code:

```bash
# Stop bot
./tools/startbot.sh stop

# Update code (git pull, etc.)

# Restart bot
./tools/startbot.sh start
```

## Security Notes

1. **Never commit `config.yaml` with passwords** - Use environment variables
2. **Protect your NickServ password** - Keep it secure
3. **Review admin list** - Only trusted users should be admins
4. **Check logs regularly** - Monitor for suspicious activity

## Next Steps

- Read `README.md` for usage instructions
- Read `CATEGORIES.md` for category system details
- Read `FILE_GUIDE.md` to understand the codebase
- Customize `config.yaml` for your needs

## Getting Help

- Check log files in `logs/` directory
- Review `README.md` troubleshooting section
- Verify all prerequisites are met
- Test configuration with test commands above
