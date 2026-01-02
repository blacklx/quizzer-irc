#!/bin/bash
#
# startbot.sh - Bot management script for Quizzer IRC Bot
#
# This script manages the bot lifecycle: start, stop, restart, and status checks.

# Get the directory where this script is located, then go up one level to bot root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_DIRECTORY="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$BOT_DIRECTORY/.venv"
SCREEN_NAME="quizzer"
BOT_SCRIPT="run.py"  # Use run.py as entry point (recommended) or "bot.py" for direct execution
LOG_FILE="$BOT_DIRECTORY/bot_management.log"
SLEEP_DURATION=10  # Configurable sleep duration for restarts
CRON_CHECK_INTERVAL="*/15 * * * *"  # Interval for cron check, e.g., every 15 minutes

# Check for required environment variable
if [ -z "$NICKSERV_PASSWORD" ] && [ "$1" != "check" ]; then
    echo "Warning: NICKSERV_PASSWORD environment variable not set"
    echo "The bot may fail to authenticate with NickServ"
fi

# Initialize log file
if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

# Log function
function log_activity {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Check if bot is running
function is_bot_running {
    if screen -list | grep -q "$SCREEN_NAME"; then
        # Further check if the bot process is actually running
        if pgrep -f "$BOT_SCRIPT" > /dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to check if the bot is actually running
function check_bot {
    if is_bot_running; then
        echo "Bot is running."
        log_activity "Bot running check: Bot is running."
    else
        echo "Bot is not running."
        log_activity "Bot running check: Bot is not running."
        start_bot
    fi
}

# Start bot
function start_bot {
    if is_bot_running; then
        echo "Bot is already running."
        log_activity "Attempted to start bot, but it's already running."
    else
        # Check if venv exists (REQUIRED)
        if [ ! -f "$VENV_PATH/bin/activate" ]; then
            echo "ERROR: Virtual environment not found at $VENV_PATH"
            echo "This bot requires a virtual environment."
            echo "Please run ./install.sh to set up the environment."
            log_activity "Failed to start bot: Virtual environment not found"
            exit 1
        fi
        
        echo "Starting bot in a new screen session..."
        screen -dmS $SCREEN_NAME bash -c "cd $BOT_DIRECTORY; source $VENV_PATH/bin/activate; python3 $BOT_SCRIPT"
        if is_bot_running; then
            echo "Bot started."
            log_activity "Bot started."
        else
            echo "Failed to start bot."
            log_activity "Failed to start bot."
        fi
    fi
}

# Stop bot
function stop_bot {
    if is_bot_running; then
        echo "Stopping bot..."
        screen -S $SCREEN_NAME -X quit
        sleep 2
        if ! is_bot_running; then
            echo "Bot stopped."
            log_activity "Bot stopped."
        else
            echo "Failed to stop bot."
            log_activity "Failed to stop bot."
        fi
    else
        echo "Bot is not currently running."
        log_activity "Attempted to stop bot, but it was not running."
    fi
}

# Restart bot
function restart_bot {
    if is_bot_running; then
        echo "Stopping bot..."
        log_activity "Stopping bot..."
        #stop_bot
        "$BOT_DIRECTORY/tools/startbot.sh" stop
        sleep $SLEEP_DURATION
        echo "Starting bot in 10 seconds"
        #start_bot
        "$BOT_DIRECTORY/tools/startbot.sh" start
        log_activity "Bot restarted."
    else
        echo "Bot is not running, attempting start"
        log_activity "Bot is not running, attempting start"
        "$BOT_DIRECTORY/tools/startbot.sh" start
        log_activity "Bot started"
    fi
}

# Update crontab
function update_crontab {
    echo "Updating crontab for the bot..."
    local existing_cron
    existing_cron=$(crontab -l 2>/dev/null | grep -v "$BOT_SCRIPT" | grep -v "startbot.sh check")

    # Add new cron jobs
    # Virtual environment is REQUIRED
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo "ERROR: Virtual environment not found at $VENV_PATH"
        echo "This bot requires a virtual environment."
        echo "Please run ./install.sh to set up the environment."
        log_activity "Failed to update crontab: Virtual environment not found"
        exit 1
    fi
    START_CMD="cd $BOT_DIRECTORY && source $VENV_PATH/bin/activate && python3 $BOT_SCRIPT"
    (echo "$existing_cron"; echo "@reboot $START_CMD >/dev/null 2>&1"; echo "$CRON_CHECK_INTERVAL cd $BOT_DIRECTORY && $BOT_DIRECTORY/tools/startbot.sh check >/dev/null 2>&1") | crontab -
    echo "Crontab updated."
    log_activity "Crontab updated for bot reboot and periodic checks."
}

# Remove bot entries from crontab
function remove_cron_entries {
    echo "Removing bot cron entries..."
    local remaining_cron
    remaining_cron=$(crontab -l 2>/dev/null | grep -v "$BOT_SCRIPT" | grep -v "startbot.sh check")

    # Update the crontab without bot entries
    echo "$remaining_cron" | crontab -
    if ! crontab -l | grep -q "$BOT_SCRIPT" && ! crontab -l | grep -q "startbot.sh check"; then
        echo "Cron entries for the bot removed."
        log_activity "Cron entries for bot removed."
    else
        echo "Failed to remove some or all cron entries for the bot."
        log_activity "Failed to remove some or all cron entries for bot."
    fi
}

# Validate configuration
function validate_configuration {
    # Check bot directory and script
    if [[ ! -d "$BOT_DIRECTORY" ]] || [[ ! -f "$BOT_DIRECTORY/$BOT_SCRIPT" ]]; then
        echo "Configuration error. Please check your settings."
        log_activity "Configuration error detected."
        exit 1
    fi
    # Check if venv exists (REQUIRED)
    if [[ ! -d "$VENV_PATH" ]] || [[ ! -f "$VENV_PATH/bin/activate" ]]; then
        echo "ERROR: Virtual environment not found at $VENV_PATH"
        echo "This bot requires a virtual environment."
        echo "Please run ./install.sh to set up the environment."
        log_activity "Configuration error: Virtual environment not found"
        exit 1
    fi
}

# Set script permissions
function set_script_permissions {
    if [[ $(stat -c "%a" "$0") != "700" ]]; then
        echo "Setting script permissions to 700..."
        chmod 700 "$0"
        echo "Permissions set."
        log_activity "Script permissions set to 700."
    else
        echo ""
    fi
}

# Main logic
validate_configuration
set_script_permissions

case "$1" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    check)
        check_bot
        ;;
    cron)
        update_crontab
        ;;
    remove-cron)
        remove_cron_entries
        ;;
    *)
        echo "Usage: $0 { start | stop | restart | check | cron | remove-cron }"
        exit 1
esac
