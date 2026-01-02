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
    
    # Test if screen works by creating a test session
    if ! screen -dmS test_session_$$ bash -c "sleep 1" 2>/dev/null; then
        echo "ERROR: Cannot create screen sessions"
        echo "Screen may not be properly configured or accessible"
        echo "Try: screen -dmS test bash -c 'sleep 1' && screen -list"
        log_activity "Failed to start bot: Screen test session creation failed"
        return 1
    fi
    sleep 0.5
    if screen -list 2>&1 | grep -q "test_session_$$"; then
        # Clean up test session
        screen -S test_session_$$ -X quit 2>/dev/null
    else
        echo "WARNING: Screen test session was not found, but continuing anyway..."
    fi
    
    # Start bot in screen session with error output captured
    local screen_cmd="cd $BOT_DIRECTORY && source $VENV_PATH/bin/activate && python3 $BOT_SCRIPT 2>&1 | tee -a $LOG_FILE"
    
    # Try to create screen session (redirect stderr to see any screen errors)
    screen -dmS $SCREEN_NAME bash -c "$screen_cmd" 2>>"$LOG_FILE"
    local screen_exit=$?
    
    # Check if screen command itself failed
    if [ $screen_exit -ne 0 ]; then
        echo "ERROR: Failed to execute screen command (exit code: $screen_exit)"
        echo "Check if screen is installed: which screen"
        echo "Check screen permissions and configuration"
        echo "Check log file for details: tail -20 $LOG_FILE"
        log_activity "Failed to start bot: Screen command failed with exit code $screen_exit"
        return 1
    fi
    
    # Wait a moment for the screen session to be created and initialized
    sleep 1
    
    # Check if screen session was created (handle both "No Sockets" message and actual session list)
    local screen_list_output
    screen_list_output=$(screen -list 2>&1)
    
    if ! echo "$screen_list_output" | grep -q "$SCREEN_NAME"; then
        # Check if screen is actually working (might just be no sessions yet)
        if echo "$screen_list_output" | grep -q "No Sockets found"; then
            # Screen is working but session might not have appeared yet, wait a bit more
            sleep 1
            screen_list_output=$(screen -list 2>&1)
            if ! echo "$screen_list_output" | grep -q "$SCREEN_NAME"; then
                echo "ERROR: Screen session '$SCREEN_NAME' was not created or exited immediately"
                echo "This usually means the command inside screen failed right away"
                echo ""
                echo "Troubleshooting:"
                echo "1. Check the log file for errors:"
                echo "   tail -50 $LOG_FILE"
                echo "2. Try running the bot command directly to see errors:"
                echo "   cd $BOT_DIRECTORY && source $VENV_PATH/bin/activate && python3 $BOT_SCRIPT"
                echo "3. Verify screen works:"
                echo "   screen -dmS test bash -c 'sleep 5' && sleep 1 && screen -list"
                log_activity "Failed to start bot: Screen session not found after creation (likely command failed immediately)"
                return 1
            fi
        else
            echo "ERROR: Failed to check screen sessions"
            echo "Screen output: $screen_list_output"
            log_activity "Failed to start bot: Could not check screen sessions"
            return 1
        fi
    fi
    
    # Wait a bit more for the bot process to start
    sleep 2
    
    # Check if bot process is actually running (screen session might exit if command fails)
    if ! pgrep -f "$BOT_SCRIPT" > /dev/null; then
        # Process not running - check if screen session still exists
        local screen_still_exists=0
        if screen -list 2>&1 | grep -q "$SCREEN_NAME"; then
            screen_still_exists=1
        fi
        
        echo "ERROR: Bot process is not running"
        if [ $screen_still_exists -eq 1 ]; then
            echo "Screen session exists but bot process not found"
            echo "The bot may have crashed or failed to start"
            # Try to capture error output from screen
            screen -S $SCREEN_NAME -X hardcopy /tmp/quizzer_screen_output.txt 2>/dev/null
            if [ -f /tmp/quizzer_screen_output.txt ]; then
                echo ""
                echo "Last output from bot:"
                tail -30 /tmp/quizzer_screen_output.txt
                rm -f /tmp/quizzer_screen_output.txt
            fi
        else
            echo "Screen session also not found - command likely failed immediately"
            echo "This usually means there's an error in the bot startup command"
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
    # Check if crontab is installed
    if ! command -v crontab >/dev/null 2>&1; then
        echo "ERROR: crontab command not found"
        echo "Please install cron/crontab:"
        echo "  Debian/Ubuntu: sudo apt-get install cron"
        echo "  RedHat/CentOS: sudo yum install cronie"
        echo "  Arch Linux: sudo pacman -S cronie"
        log_activity "Failed to update crontab: crontab command not found"
        return 1
    fi

    echo "Updating crontab for the bot..."
    
    # Virtual environment is REQUIRED - verify it exists and is valid
    if [ ! -d "$VENV_PATH" ]; then
        echo "ERROR: Virtual environment directory not found at $VENV_PATH"
        echo "This bot requires a virtual environment."
        echo "Please run ./install.sh to set up the environment."
        log_activity "Failed to update crontab: Virtual environment directory not found"
        return 1
    fi
    
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        echo "ERROR: Virtual environment is invalid - activate script not found at $VENV_PATH/bin/activate"
        echo "The virtual environment may have been created incorrectly or is corrupted."
        echo "Please recreate it by running: ./install.sh"
        echo "Or manually: rm -rf $VENV_PATH && python3 -m venv $VENV_PATH"
        log_activity "Failed to update crontab: Virtual environment activate script not found"
        return 1
    fi
    
    # Verify the venv has Python
    if [ ! -f "$VENV_PATH/bin/python3" ] && [ ! -f "$VENV_PATH/bin/python" ]; then
        echo "ERROR: Virtual environment is invalid - Python executable not found"
        echo "The virtual environment may be corrupted."
        echo "Please recreate it by running: ./install.sh"
        log_activity "Failed to update crontab: Virtual environment Python executable not found"
        return 1
    fi

    # Get existing crontab entries (handle case where no crontab exists yet)
    local existing_cron
    if crontab -l >/dev/null 2>&1; then
        # Crontab exists, get entries excluding bot-related ones
        existing_cron=$(crontab -l 2>/dev/null | grep -v "$BOT_SCRIPT" | grep -v "startbot.sh check")
        local crontab_exit=$?
        if [ $crontab_exit -ne 0 ] && [ $crontab_exit -ne 1 ]; then
            # Exit code 1 means no crontab exists (normal), other codes are errors
            echo "ERROR: Failed to read existing crontab (exit code: $crontab_exit)"
            log_activity "Failed to update crontab: Could not read existing crontab"
            return 1
        fi
    else
        # No crontab exists yet, that's fine
        existing_cron=""
    fi

    # Prepare new crontab entries
    # Use full path to venv Python directly (more reliable in cron than 'source activate')
    # Check which Python executable exists in venv
    local venv_python
    if [ -f "$VENV_PATH/bin/python3" ]; then
        venv_python="$VENV_PATH/bin/python3"
    elif [ -f "$VENV_PATH/bin/python" ]; then
        venv_python="$VENV_PATH/bin/python"
    else
        echo "ERROR: Python executable not found in virtual environment"
        log_activity "Failed to update crontab: Python executable not found in venv"
        return 1
    fi
    
    # Use full paths for cron (cron has minimal environment)
    START_CMD="cd $BOT_DIRECTORY && $venv_python $BOT_SCRIPT"
    local new_crontab
    new_crontab=$(echo "$existing_cron"; echo "@reboot $START_CMD >/dev/null 2>&1"; echo "$CRON_CHECK_INTERVAL cd $BOT_DIRECTORY && $BOT_DIRECTORY/tools/startbot.sh check >/dev/null 2>&1")
    
    # Update crontab and check if it succeeded
    if echo "$new_crontab" | crontab -; then
        echo "Crontab updated successfully."
        log_activity "Crontab updated for bot reboot and periodic checks."
        return 0
    else
        echo "ERROR: Failed to update crontab"
        echo "The crontab command returned a non-zero exit code"
        echo "Check crontab permissions and configuration"
        log_activity "Failed to update crontab: crontab - command failed"
        return 1
    fi
}

# Remove bot entries from crontab
function remove_cron_entries {
    # Check if crontab is installed
    if ! command -v crontab >/dev/null 2>&1; then
        echo "ERROR: crontab command not found"
        echo "Please install cron/crontab:"
        echo "  Debian/Ubuntu: sudo apt-get install cron"
        echo "  RedHat/CentOS: sudo yum install cronie"
        echo "  Arch Linux: sudo pacman -S cronie"
        log_activity "Failed to remove cron entries: crontab command not found"
        return 1
    fi

    echo "Removing bot cron entries..."
    
    # Check if crontab exists
    if ! crontab -l >/dev/null 2>&1; then
        echo "No crontab found. Nothing to remove."
        log_activity "Attempted to remove cron entries: No crontab found"
        return 0
    fi

    # Get remaining crontab entries (excluding bot-related ones)
    local remaining_cron
    remaining_cron=$(crontab -l 2>/dev/null | grep -v "$BOT_SCRIPT" | grep -v "startbot.sh check")
    local read_exit=$?
    
    if [ $read_exit -ne 0 ] && [ $read_exit -ne 1 ]; then
        echo "ERROR: Failed to read crontab (exit code: $read_exit)"
        log_activity "Failed to remove cron entries: Could not read crontab"
        return 1
    fi

    # Update the crontab without bot entries
    if echo "$remaining_cron" | crontab -; then
        # Verify removal was successful
        if crontab -l 2>/dev/null | grep -q "$BOT_SCRIPT" || crontab -l 2>/dev/null | grep -q "startbot.sh check"; then
            echo "WARNING: Some bot cron entries may still remain"
            echo "Please check manually: crontab -l"
            log_activity "Warning: Some bot cron entries may still remain after removal"
            return 1
        else
            echo "Cron entries for the bot removed successfully."
            log_activity "Cron entries for bot removed successfully."
            return 0
        fi
    else
        echo "ERROR: Failed to update crontab"
        echo "The crontab command returned a non-zero exit code"
        log_activity "Failed to remove cron entries: crontab - command failed"
        return 1
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
        exit $?
        ;;
    remove-cron)
        remove_cron_entries
        exit $?
        ;;
    *)
        echo "Usage: $0 { start | stop | restart | check | cron | remove-cron }"
        exit 1
esac
