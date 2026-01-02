#!/usr/bin/env python3
"""
Quizzer IRC Bot - Main Entry Point

This is the recommended way to start the bot. It handles initialization
and error handling.

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

Version: 0.90
"""
# Standard library imports
import logging
import os
import sys

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# Environment Variable Loading
# ============================================================================


def load_env_file(env_file='.env'):
    """
    Load environment variables from .env file.
    
    Simple .env file parser - reads KEY=VALUE lines and sets environment variables.
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), env_file)
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        # Only set if not already in environment
                        if key and value and key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logging.warning(f"Could not load .env file: {e}")

# Load .env file before importing bot modules
load_env_file()

# Local imports
from bot import QuizzerBot
from config import load_config, ConfigError
from database import create_database

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger('RunLogger')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# ============================================================================
# Main Function
# ============================================================================


def main():
    """Main entry point for the Quizzer IRC Bot."""
    try:
        # Load configuration
        config = load_config()
        
        # Ensure database exists
        create_database()
        
        # Extract configuration values
        server = config.get('bot_settings', 'server')
        port = config.get('bot_settings', 'port')
        channel = config.get('bot_settings', 'channel')
        nickname = config.get('bot_settings', 'nickname')
        realname = config.get('bot_settings', 'realname')
        use_ssl = config.get('bot_settings', 'use_ssl')
        reconnect_interval = config.get('bot_settings', 'reconnect_interval')
        rejoin_interval = config.get('bot_settings', 'rejoin_interval')
        nickname_retry_interval = config.get(
            'bot_settings', 'nickname_retry_interval'
        )
        
        # bind_address is optional - get it if present, otherwise None
        bind_address = config.config.get('bot_settings', {}).get(
            'bind_address', None
        )
        if bind_address:
            bind_address = str(bind_address).strip()
            if bind_address.lower() in ['null', 'none', '']:
                bind_address = None
        
        use_nickserv = config.get('nickserv_settings', 'use_nickserv')
        nickserv_name = config.get('nickserv_settings', 'nickserv_name')
        nickserv_account = config.get('nickserv_settings', 'nickserv_account')
        nickserv_password = config.get_nickserv_password()
        nickserv_command_format = config.get('nickserv_settings', 'nickserv_command_format')
        nickserv_settings = config.config['nickserv_settings']
        
        question_count = config.get('quiz_settings', 'question_count')
        answer_time_limit = config.get('quiz_settings', 'answer_time_limit')
        admin_nicks = config.get('admin_settings', 'admins')
        
        # Admin verification settings
        admin_verification_method = config.config.get(
            'admin_settings', {}
        ).get('verification_method', 'nickserv').lower()
        admin_password_settings = config.config.get(
            'admin_settings', {}
        ).get('password_settings', {})
        admin_hostmask_settings = config.config.get(
            'admin_settings', {}
        ).get('hostmask_settings', {})
        
        # Create AdminVerifier if needed
        admin_verifier = None
        if admin_verification_method in ['password', 'hostmask', 'combined']:
            try:
                from admin_verifier import AdminVerifier
                admin_verifier = AdminVerifier(
                    admin_nicks=admin_nicks,
                    verification_method=admin_verification_method,
                    password_settings=admin_password_settings,
                    hostmask_settings=admin_hostmask_settings
                )
                logger.info(f"Admin verification method: {admin_verification_method}")
            except Exception as e:
                logger.error(f"Failed to initialize AdminVerifier: {e}")
                logger.warning("Falling back to NickServ verification")
                admin_verifier = None
                admin_verification_method = 'nickserv'
        else:
            logger.info(f"Admin verification method: {admin_verification_method} (NickServ)")
        
        bot_version = "Quizzer v0.90"
        
        logger.info(f"Starting {bot_version}...")
        logger.info(f"Connecting to {server}:{port} as {nickname}")
        logger.info(f"Channel: {channel}")
        
        # Create and start bot
        bot = QuizzerBot(
            channel,
            nickname,
            realname,
            server,
            port,
            use_ssl,
            nickserv_settings,
            nickserv_account,
            nickserv_password,
            nickserv_command_format,
            use_nickserv,
            bot_version,
            question_count,
            answer_time_limit,
            admin_nicks,
            admin_verification_method,
            admin_verifier,
            bind_address
        )
        bot.start()
        
    except ConfigError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

