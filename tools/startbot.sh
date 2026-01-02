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

# Load .env file if it exists (for environment variables)
load_env_file() {
    local env_file="$BOT_DIRECTORY/.env"
    if [ -f "$env_file" ]; then
        # Read .env file and export variables
        # Ignores comments and empty lines
        while IFS= read -r line || [ -n "$line" ]; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "${line// }" ]] && continue
            
            # Parse KEY=VALUE
            if [[ "$line" =~ ^[[:space:]]*([^=]+)=(.*)$ ]]; then
                local key="${BASH_REMATCH[1]// /}"
                local value="${BASH_REMATCH[2]}"
                # Remove quotes if present
                value="${value#\"}"
                value="${value%\"}"
                value="${value#\'}"
                value="${value%\'}"
                # Only export if not already set (env vars take precedence)
                if [ -z "${!key}" ]; then
                    # Safely export the variable
                    export "${key}"="${value}"
                fi
            fi
        done < "$env_file"
    fi
}

# Load .env file before checking environment variables
load_env_file

# Check for required environment variable
if [ -z "$NICKSERV_PASSWORD" ] && [ "$1" != "check" ]; then
    echo "Warning: NICKSERV_PASSWORD environment variable not set"
    echo "The bot may fail to authenticate with NickServ"
    echo "Note: Check that NICKSERV_PASSWORD is set in .env file or as an environment variable"
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
        return 0
    else
        echo "Bot is not running."
        log_activity "Bot running check: Bot is not running."
        echo "Attempting to start bot..."
        if start_bot; then
            return 0
        else
            log_activity "Bot running check: Failed to start bot"
            return 1
        fi
    fi
}

# Start bot
function start_bot {
    if is_bot_running; then
        echo "Bot is already running."
        log_activity "Attempted to start bot, but it's already running."
        return 0
    fi
    
    # Check if venv exists (REQUIRED)
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo "ERROR: Virtual environment not found at $VENV_PATH"
        echo "This bot requires a virtual environment."
        echo "Please run ./install.sh to set up the environment."
        log_activity "Failed to start bot: Virtual environment not found"
        return 1
    fi
    
    # Check if bot script exists
    if [ ! -f "$BOT_DIRECTORY/$BOT_SCRIPT" ]; then
        echo "ERROR: Bot script not found: $BOT_DIRECTORY/$BOT_SCRIPT"
        log_activity "Failed to start bot: Script not found"
        return 1
    fi
    
    # Check if config.yaml exists
    if [ ! -f "$BOT_DIRECTORY/config.yaml" ]; then
        echo "ERROR: Configuration file not found: $BOT_DIRECTORY/config.yaml"
        echo "Please copy config.yaml.example to config.yaml and configure it."
        log_activity "Failed to start bot: config.yaml not found"
        return 1
    fi
    
    echo "Starting bot in a new screen session..."
    log_activity "Attempting to start bot..."
    
    # Start bot in screen session with error output captured
    screen -dmS $SCREEN_NAME bash -c "cd $BOT_DIRECTORY; source $VENV_PATH/bin/activate; python3 $BOT_SCRIPT 2>&1 | tee -a $LOG_FILE"
    
    # Wait a moment for the bot to start
    sleep 2
    
    # Check if screen session was created
    if ! screen -list | grep -q "$SCREEN_NAME"; then
        echo "ERROR: Failed to create screen session"
        echo "Check if screen is installed: which screen"
        log_activity "Failed to start bot: Screen session creation failed"
        return 1
    fi
    
    # Wait a bit more and check if bot process is running
    sleep 1
    
    # Check if bot is actually running
    if ! is_bot_running; then
        echo "ERROR: Bot failed to start"
        echo "Checking screen session for errors..."
        
        # Try to capture error output from screen
        if screen -list | grep -q "$SCREEN_NAME"; then
            # Get the last few lines from screen session
            screen -S $SCREEN_NAME -X hardcopy /tmp/quizzer_screen_output.txt 2>/dev/null
            if [ -f /tmp/quizzer_screen_output.txt ]; then
                echo "Last output from bot:"
                tail -20 /tmp/quizzer_screen_output.txt
                rm -f /tmp/quizzer_screen_output.txt
            fi
        fi
        
        echo ""
        echo "Troubleshooting:"
        echo "1. Check the log file: tail -f $LOG_FILE"
        echo "2. Attach to screen session: screen -r $SCREEN_NAME"
        echo "3. Check if Python dependencies are installed: source $VENV_PATH/bin/activate && pip list"
        echo "4. Verify configuration: python3 -c \"from config import load_config; load_config()\""
        
        log_activity "Failed to start bot: Process not running after start attempt"
        return 1
    fi
    
    # Double-check by waiting a bit more and verifying it's still running
    sleep 2
    if ! is_bot_running; then
        echo "ERROR: Bot started but then stopped immediately"
        echo "This usually indicates a configuration error or missing dependency."
        echo "Check the log file: tail -f $LOG_FILE"
        echo "Or attach to screen: screen -r $SCREEN_NAME"
        log_activity "Failed to start bot: Bot stopped immediately after start"
        return 1
    fi
    
    echo "✓ Bot started successfully"
    echo "  Screen session: $SCREEN_NAME"
    echo "  View output: screen -r $SCREEN_NAME"
    echo "  Check logs: tail -f $LOG_FILE"
    log_activity "Bot started successfully"
    return 0
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
        stop_bot
        sleep $SLEEP_DURATION
        echo "Starting bot..."
        if start_bot; then
            log_activity "Bot restarted successfully."
            return 0
        else
            log_activity "Bot restart failed: Start failed"
            return 1
        fi
    else
        echo "Bot is not running, attempting start"
        log_activity "Bot is not running, attempting start"
        if start_bot; then
            log_activity "Bot started"
            return 0
        else
            log_activity "Bot start failed"
            return 1
        fi
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
        exit $?
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        exit $?
        ;;
    check)
        check_bot
        exit $?
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
