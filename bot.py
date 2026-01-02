"""
Quizzer IRC Bot - Main IRC Bot Implementation

This module contains the main IRC bot class that connects to IRC servers,
handles IRC events, and routes commands to appropriate handlers.

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
import logging
import time
import threading
import yaml
import os
import irc
import ssl
from irc.bot import SingleServerIRCBot
from irc.connection import Factory
from admin import AdminCommands
from admin_verifier import AdminVerifier
from quiz_game import QuizGame, handle_start_command, handle_join_command, handle_categories_command, handle_help_command
from category_display import handle_categories_display, get_all_categories
from database import create_database, store_score, get_leaderboard

# Load .env file if it exists (for environment variables)
# This ensures .env is loaded even if bot.py is imported directly
def load_env_file(env_file='.env'):
    """
    Load environment variables from .env file.
    
    Simple .env file parser - reads KEY=VALUE lines and sets environment variables.
    Only sets variables that aren't already in the environment.
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
                        # Only set if not already in environment (env vars take precedence)
                        if key and value and key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logging.warning(f"Could not load .env file: {e}")

# Load .env file before loading configuration
load_env_file()

# Load configuration
try:
    with open("config.yaml", 'r') as config_file:
        config = yaml.safe_load(config_file)
except FileNotFoundError:
    logging.error("Error: The config.yaml file was not found.")
    exit(1)
except yaml.YAMLError as e:
    logging.error(f"Error loading YAML configuration: {e}")
    exit(1)
required_keys = {
    'quiz_settings': ['question_count', 'answer_time_limit'],
    'bot_settings': ['server', 'port', 'channel', 'nickname', 'realname', 'use_ssl', 'reconnect_interval', 'rejoin_interval', 'nickname_retry_interval'],
    'nickserv_settings': ['use_nickserv', 'nickserv_name', 'nickserv_account', 'nickserv_command_format'],
    'bot_log_settings': ['enable_logging', 'enable_debug', 'log_filename'],
    'admin_settings': ['admins']
}
# Note: nickserv_password is optional in config if NICKSERV_PASSWORD env var is set
for category, keys in required_keys.items():
    if category not in config:
        raise ValueError(f"Missing '{category}' section in config.yaml")
    for key in keys:
        if key not in config[category]:
            raise ValueError(f"Missing '{key}' in '{category}' section of config.yaml")

# Bot configuration
server = config['bot_settings']['server']
port = config['bot_settings']['port']
channel = config['bot_settings']['channel']
nickname = config['bot_settings']['nickname']
realname = config['bot_settings']['realname']
use_ssl = config['bot_settings']['use_ssl']
reconnect_interval = config['bot_settings']['reconnect_interval']
rejoin_interval = config['bot_settings']['rejoin_interval']
nickname_retry_interval = config['bot_settings']['nickname_retry_interval']

# NickServ configuration
use_nickserv = config['nickserv_settings']['use_nickserv']
nickserv_name = config['nickserv_settings']['nickserv_name']
nickserv_account = config['nickserv_settings']['nickserv_account']
# Get password from environment variable (from .env file or system env), fallback to config for backward compatibility
nickserv_password = os.getenv('NICKSERV_PASSWORD', config['nickserv_settings'].get('nickserv_password', ''))
if not nickserv_password:
    raise ValueError("NICKSERV_PASSWORD must be set in .env file, as an environment variable, or in config.yaml")
nickserv_command_format = config['nickserv_settings']['nickserv_command_format']

# Admin settings
admins = config['admin_settings']['admins']
admin_verification_method = config['admin_settings'].get('verification_method', 'nickserv').lower()
admin_password_settings = config['admin_settings'].get('password_settings', {})
admin_hostmask_settings = config['admin_settings'].get('hostmask_settings', {})

# Create AdminVerifier if password/hostmask/combined method is used
# Note: Logger not yet initialized, so we'll log this later in QuizzerBot.__init__
admin_verifier = None
if admin_verification_method in ['password', 'hostmask', 'combined']:
    try:
        admin_verifier = AdminVerifier(
            admin_nicks=admins,
            verification_method=admin_verification_method,
            password_settings=admin_password_settings,
            hostmask_settings=admin_hostmask_settings
        )
    except Exception as e:
        # Logger not available yet, print to console
        print(f"Warning: Failed to initialize AdminVerifier: {e}")
        print("Falling back to NickServ verification")
        admin_verifier = None
        admin_verification_method = 'nickserv'

# Ensure required directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('db', exist_ok=True)

# Logging and Debug configuration
enable_logging = config['bot_log_settings']['enable_logging']
enable_debug = config['bot_log_settings']['enable_debug']
log_level = logging.DEBUG if enable_debug else logging.INFO
log_filename = config['bot_log_settings']['log_filename']

# Setting up logging
logger = logging.getLogger('IRC')
logger.setLevel(log_level)
try:
    file_handler = logging.FileHandler(log_filename)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except (OSError, PermissionError) as e:
    logging.warning(f"Warning: Could not create log file '{log_filename}': {e}")
    # Continue with console logging only
if enable_logging:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class QuizzerBot(SingleServerIRCBot):
    """
    Main IRC bot class for Quizzer.
    
    Handles IRC connection, event processing, command routing, and bot lifecycle.
    Extends SingleServerIRCBot from the irc library.
    
    Attributes:
        quiz_game: QuizGame instance managing quiz state
        channel: IRC channel the bot operates in
        admin_commands: AdminCommands instance for admin functionality
    """
    def __init__(self, channel, nickname, realname, server, port, use_ssl, nickserv_settings, nickserv_account, nickserv_password, nickserv_command_format, use_nickserv, bot_version, question_count, answer_time_limit, admins, admin_verification_method='nickserv', admin_verifier=None, bind_address=None):
        """
        Initialize the Quizzer IRC bot.
        
        Args:
            channel: IRC channel to join
            nickname: Bot's IRC nickname
            realname: Bot's realname
            server: IRC server address
            port: IRC server port
            use_ssl: Whether to use SSL/TLS
            nickserv_settings: Dictionary of NickServ settings
            nickserv_account: NickServ account name
            nickserv_password: NickServ password
            nickserv_command_format: Format string for NickServ commands
            use_nickserv: Whether to use NickServ authentication
            bot_version: Bot version string
            question_count: Number of questions per quiz
            answer_time_limit: Time limit for answering questions (seconds)
            admins: List of admin nicknames
            bind_address: Optional IP address or hostname to bind to (IPv4 or IPv6)
        """
        # Convert bind_address to tuple format if specified
        # socket.bind() requires (host, port) tuple, not just a string
        bind_address_tuple = None
        use_ipv6 = False
        if bind_address:
            bind_address = str(bind_address).strip()
            # Auto-detect IPv4 vs IPv6 using socket.getaddrinfo()
            # This is more reliable than string heuristics
            try:
                # Try to resolve the address to determine its family
                addr_info = socket.getaddrinfo(bind_address, 0, socket.AF_UNSPEC, socket.SOCK_STREAM)
                if addr_info:
                    family = addr_info[0][0]
                    if family == socket.AF_INET6:
                        # IPv6 address - use 2-tuple (host, port) with ipv6=True in Factory
                        # Port 0 lets OS choose available port
                        bind_address_tuple = (bind_address, 0)
                        use_ipv6 = True
                    elif family == socket.AF_INET:
                        # IPv4 address - format: (host, port)
                        # For binding, we use port 0 (let OS choose)
                        bind_address_tuple = (bind_address, 0)
                        use_ipv6 = False
                    else:
                        logger.warning(f"Unknown address family for bind_address: {bind_address}, defaulting to IPv4")
                        bind_address_tuple = (bind_address, 0)
                        use_ipv6 = False
                else:
                    logger.warning(f"Could not resolve bind_address: {bind_address}, defaulting to IPv4")
                    bind_address_tuple = (bind_address, 0)
                    use_ipv6 = False
            except (socket.gaierror, OSError) as e:
                # Fallback to simple heuristic if getaddrinfo fails
                logger.warning(f"Could not resolve bind_address {bind_address}: {e}, using heuristic detection")
                if '::' in bind_address or (bind_address.count(':') > 1 and not bind_address.startswith('[')):
                    bind_address_tuple = (bind_address, 0)
                    use_ipv6 = True
                else:
                    bind_address_tuple = (bind_address, 0)
                    use_ipv6 = False
        
        # Create Factory with bind_address if specified
        # Note: Factory needs ipv6=True for IPv6 addresses
        if use_ssl:
            factory = Factory(
                bind_address=bind_address_tuple,
                ipv6=use_ipv6,
                wrapper=lambda sock: ssl.create_default_context().wrap_socket(sock, server_hostname=server)
            )
        else:
            factory = Factory(
                bind_address=bind_address_tuple,
                ipv6=use_ipv6
            )
        
        # Store bind_address for logging (original string)
        self.bind_address = bind_address
        if bind_address:
            logger.info(f"Will bind to local address: {bind_address}")
        
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname, connect_factory=factory)

        # Retrieve quiz settings from the config
        question_count = config['quiz_settings']['question_count']
        answer_time_limit = config['quiz_settings']['answer_time_limit']

        # Pass the channel, question count, and answer time limit to QuizGame
        self.quiz_game = QuizGame(channel, question_count, answer_time_limit)

        self.channel = channel
        self.nickserv_account = nickserv_account
        self.nickserv_password = nickserv_password
        self.nickserv_command_format = nickserv_command_format
        self.use_nickserv = use_nickserv
        self.nickname_attempted = False
        self.original_nickname = nickname
        self.bot_version = bot_version
        self.reconnection_attempts = 0
        self.max_reconnection_attempts = 5  # Maximum reconnection attempts
        self.max_reconnect_wait = 300  # Maximum wait time in seconds
        self.should_reconnect = True

        # Grab nickname for nickserv from config.yaml
        self.nickserv_name = nickserv_settings['nickserv_name']
        self.pending_admin_commands = {}
        self._admin_lock = threading.Lock()  # Lock for thread-safe access to pending_admin_commands

        # Store admin nicks and create AdminCommands instance
        self.admin_nicks = admins
        self.admin_verification_method = admin_verification_method
        self.admin_verifier = admin_verifier
        self.admin_commands = AdminCommands(self.quiz_game, admins, self.nickserv_name, admin_verifier)
        
        # Log admin verification method (logger is now available)
        if admin_verification_method in ['password', 'hostmask', 'combined']:
            logger.info(f"Admin verification method: {admin_verification_method}")
        else:
            logger.info(f"Admin verification method: {admin_verification_method} (NickServ)")

    def send_category_list_in_parts(self, connection, categories, max_length=400):
        """
        Send category list to channel, splitting into multiple messages if needed.
        Legacy method - kept for backward compatibility.
        
        Args:
            connection: IRC connection object
            categories: List of category names
            max_length: Maximum message length (default: 400)
        """
        messages = handle_categories_display(categories, mode='compact', max_length=max_length)
        for msg in messages:
            connection.privmsg(self.channel, msg)

    def on_ctcp(self, c, e):
        """
        Handle CTCP (Client-To-Client Protocol) requests.
        
        Currently handles VERSION requests.
        
        Args:
            c: IRC connection
            e: IRC event
        """
        nick = e.source.nick
        if e.arguments[0] == 'VERSION':
            c.ctcp_reply(nick, f'VERSION {self.bot_version}')
        else:
            # Handle other CTCP messages the default way
            super().on_ctcp(c, e)

    def start(self):
        """Start the bot and connect to IRC server."""
        logger.info("=" * 60)
        logger.info(f"Starting Quizzer Bot v{self.bot_version}")
        bind_info = f" (bind: {self.bind_address})" if self.bind_address else ""
        logger.info(f"Connecting to IRC server: {server}:{port} (SSL: {use_ssl}){bind_info}")
        logger.info(f"Channel: {self.channel}")
        logger.info(f"Nickname: {self.original_nickname}")
        logger.info(f"NickServ: {'Enabled' if self.use_nickserv else 'Disabled'}")
        if self.use_nickserv:
            logger.info(f"NickServ account: {self.nickserv_account}")
        logger.info("=" * 60)
        super().start()

    def on_nicknameinuse(self, c, e):
        logger.info("Nickname is in use. Trying a different nickname.")
        if not self.nickname_attempted:
            c.nick(c.get_nickname() + "_")
            self.nickname_attempted = True
            # Start a thread to periodically attempt to reclaim the original nickname
            self._start_reclaim_nickname_thread()

    def on_welcome(self, c, e):
        """Handle welcome message from IRC server."""
        logger.info("=" * 60)
        logger.info("✓ Connected to IRC server successfully")
        logger.info(f"✓ Server welcome message received")
        logger.info(f"✓ Current nickname: {c.get_nickname()}")
        if self.use_nickserv:
            # Send NickServ authentication command
            nickserv_command = self.nickserv_command_format.format(account=self.nickserv_account, password=self.nickserv_password)
            logger.info(f"Sending NickServ authentication command to {self.nickserv_name}...")
            logger.debug(f"NickServ command: {nickserv_command.replace(self.nickserv_password, '***')}")
            c.privmsg(self.nickserv_name, nickserv_command)
        else:
            logger.info("NickServ authentication disabled")
        # Waiting 5 seconds after receiving MOTD before joining channel
        logger.info(f"Will join channel {self.channel} in 5 seconds (after MOTD)...")
        threading.Timer(5, lambda: c.join(self.channel)).start()


    def on_privmsg(self, c, e):
        """
        Handle private messages (PMs) to the bot.
        
        Processes commands like !join, !a (answer), and admin commands.
        
        Args:
            c: IRC connection
            e: IRC event containing message
        """
        nick = e.source.nick
        message = e.arguments[0]
        command, *params = message.split()

        # Handle help command for admins
        if command == "!help" and self.admin_commands.is_admin(nick):
            help_message = self.admin_commands.get_admin_help_message()
            for line in help_message.split('\n'):
                c.notice(nick, line)

        # Process admin commands
        if command.startswith('!admin'):
            # Handle password verification command
            if command == "!admin" and len(params) >= 1 and params[0] == "verify":
                if len(params) < 2:
                    c.notice(nick, "Usage: !admin verify <password>")
                    return
                password = params[1]
                if self.admin_verifier:
                    success, msg = self.admin_verifier.verify_password(nick, password)
                    c.notice(nick, msg)
                    if success:
                        logger.info(f"Password verification successful for {nick}")
                else:
                    c.notice(nick, "Password verification not available. Using NickServ.")
                return
            
            # Handle admin management commands (require existing admin session)
            if len(params) >= 1:
                action = params[0]
                
                # Admin management commands
                if action == "add_admin" and len(params) >= 3:
                    new_admin = params[1]
                    new_password = params[2]
                    if self._verify_admin(c, e, nick):
                        self.admin_commands.add_admin(c, nick, new_admin, new_password)
                    return
                
                elif action == "remove_admin" and len(params) >= 2:
                    admin_to_remove = params[1]
                    if self._verify_admin(c, e, nick):
                        self.admin_commands.remove_admin(c, nick, admin_to_remove)
                    return
                
                elif action == "set_password" and len(params) >= 3:
                    target_nick = params[1]
                    new_password = params[2]
                    if self._verify_admin(c, e, nick):
                        self.admin_commands.set_password(c, nick, target_nick, new_password)
                    return
                
                elif action == "list_admins":
                    if self._verify_admin(c, e, nick):
                        self.admin_commands.list_admins(c, nick)
                    return
            
            # Regular admin commands - verify first
            if not self.admin_commands.is_admin(nick):
                c.notice(nick, "You are not authorized to use admin commands.")
                return
            
            # Check verification method
            if self.admin_verification_method == 'nickserv':
                # Request NickServ verification - ALL commands must wait for this
                self.admin_commands.request_nickserv_info(c, e.source.nick)
                with self._admin_lock:
                    self.pending_admin_commands[e.source.nick] = (command, params)
                
                # Don't execute commands here - wait for NickServ verification in on_notice()
                logger.debug(f"Admin command '{command}' from {nick} - waiting for NickServ verification")
                c.notice(nick, "Verifying admin status with NickServ...")
            
            elif self.admin_verification_method in ['password', 'hostmask', 'combined']:
                # Check session or verify immediately
                # Get hostmask from IRC event (format: nick!user@host)
                hostmask = f"{e.source.nick}!{e.source.user}@{e.source.host}" if hasattr(e.source, 'host') else None
                if self.admin_verifier and self.admin_verifier.verify_session(nick):
                    # Has valid session, execute command
                    self.handle_admin_command(c, e, command, params)
                elif self.admin_verifier and self.admin_verification_method == 'hostmask':
                    # Try hostmask verification
                    if self.admin_verifier.verify_hostmask(nick, hostmask or ''):
                        self.handle_admin_command(c, e, command, params)
                    else:
                        c.notice(nick, "Hostmask verification failed. You are not authorized.")
                else:
                    # No session, need to verify
                    c.notice(nick, "No active session. Please verify with: !admin verify <password>")
            else:
                c.notice(nick, "Unknown verification method configured.")

        # Non-admin commands
        if command == "!join":
            handle_join_command(self.quiz_game, nick, c)

        elif command == "!a" and params:
            answer = params[0]
            self.quiz_game.process_answer(nick, answer, c)

    def on_pubmsg(self, c, e):
        """
        Handle public channel messages.
        
        Processes commands like !start, !categories, !leaderboard, !help.
        
        Args:
            c: IRC connection
            e: IRC event containing message
        """
        nick = e.source.nick
        message = e.arguments[0]
        command, *params = message.split()

        if command == "!start":
            category = ' '.join(params) if params else "random"
            handle_start_command(self.quiz_game, category, c, nick)

        if command == "!categories":
            # Use hierarchical category system
            from category_hierarchy import format_category_display, get_subcategories
            
            main_cat, subcats, display_mode = handle_categories_command(params)
            
            if display_mode == 'subcategories':
                # Show subcategories for a specific main category
                c.privmsg(self.channel, f"\x02{main_cat} Subcategories:\x02")
                subcat_list = ', '.join(subcats)
                c.privmsg(self.channel, f"  {subcat_list}")
                c.privmsg(self.channel, f"Use \x0303!start {main_cat.lower()}\x03 for random, or \x0303!start {main_cat.lower()} <subcategory>\x03 for specific.")
            elif display_mode == 'standalone':
                # Standalone category (no subcategories)
                c.privmsg(self.channel, f"Category '\x02{main_cat}\x02' has no subcategories.")
                c.privmsg(self.channel, f"Use \x0303!start {main_cat.lower()}\x03 to start a quiz.")
            else:
                # Show all main categories (default)
                messages = format_category_display()
                for msg in messages:
                    c.privmsg(self.channel, msg)
                c.privmsg(self.channel, f"Use \x0303!categories <category>\x03 to see subcategories (e.g., !categories entertainment)")

        if command == "!leaderboard":
            leaderboard = get_leaderboard()
            top_scorers = leaderboard[:10]  # Limit to top 10 scorers

            # Find the longest username for formatting
            if top_scorers:
                max_username_length = max(len(user) for user, _ in top_scorers)

                # Send a message for each top scorer
                c.privmsg(self.channel, " ")
                c.privmsg(self.channel, "\x02Top Scorers:\x02")
                c.privmsg(self.channel, " ")
                for user, score in top_scorers:
                    padded_user = user.ljust(max_username_length)
                    c.privmsg(self.channel, f" {padded_user} : {score}")
                c.privmsg(self.channel, " ")
            else:
                c.privmsg(self.channel, "No scores to display.")

        elif command == "!help":
            help_text = handle_help_command()
            c.privmsg(self.channel, help_text)

    def _verify_admin(self, c, e, nick):
        """Verify admin using configured method."""
        if not self.admin_commands.is_admin(nick):
            return False
        
        if self.admin_verification_method == 'nickserv':
            # NickServ verification handled separately
            return False  # Indicates should use NickServ
        
        elif self.admin_verification_method in ['password', 'hostmask', 'combined']:
            if self.admin_verifier:
                # Check session first
                if self.admin_verifier.verify_session(nick):
                    return True
                
                # Try hostmask if method supports it
                if self.admin_verification_method in ['hostmask', 'combined']:
                    hostmask = f"{e.source.nick}!{e.source.user}@{e.source.host}" if hasattr(e.source, 'host') else None
                    if hostmask and self.admin_verifier.verify_hostmask(nick, hostmask):
                        return True
                
                # No session, need password
                return False
        
        return False
    
    def handle_admin_command(self, c, e, command, params):
        """
        Process admin commands after NickServ verification.
        
        Args:
            c: IRC connection
            e: IRC event
            command: Command string (e.g., "!admin stop")
            params: Command parameters
        """
        nick = e.target
        if not params:
            c.notice(nick, "Invalid admin command format.")
            return
        
        action = params[0]
        if action == "set_rate_limit":
            if len(params) == 2:
                new_limit = params[1]
                self.admin_commands.set_rate_limit(c, nick, new_limit)
            else:
                current_limit = self.admin_commands.get_current_rate_limit()
                c.notice(nick, f"Current rate limit is {current_limit} seconds.")
        elif action == "stop_game":
            self.admin_commands.stop_game(c, nick)
        elif action == "restart":
            self.admin_commands.restart_bot(c)
        elif action == "stop":
            self.admin_commands.stop_bot(c)
        elif action == "msg" and len(params) >= 3:
            target = params[1]
            message = ' '.join(params[2:])
            self.admin_commands.send_message(c, target, message)
        elif action == "stats":
            self.admin_commands.get_bot_stats(c, nick)
        else:
            c.notice(nick, f"Unknown admin command: {action}")

    def on_notice(self, c, e):
        """Handle NOTICE messages from IRC server (including NickServ)."""
        notice_source = e.source.nick.lower() if e.source.nick else ""
        notice_message = ' '.join(e.arguments)
        
        # Handle NickServ notices
        if notice_source == self.nickserv_name.lower():
            logger.info(f"NickServ notice: {notice_message}")
            
            # Log full NickServ response for debugging (especially INFO responses)
            if "INFO" in notice_message or "info" in notice_message.lower():
                logger.debug(f"Full NickServ INFO response: {e.arguments}")
                logger.debug(f"Response parts: {[arg for arg in e.arguments]}")
            
            # Check for successful authentication
            if any(keyword in notice_message.lower() for keyword in ['identified', 'password accepted', 'you are now identified', 'successfully']):
                logger.info("=" * 60)
                logger.info("✓ NickServ authentication successful!")
                logger.info(f"✓ Authenticated as: {self.nickserv_account}")
                logger.info("=" * 60)
            elif any(keyword in notice_message.lower() for keyword in ['invalid', 'incorrect', 'authentication failed', 'password incorrect']):
                logger.error(f"✗ NickServ authentication failed: {notice_message}")
            
            # Handle admin command verification
            # Original logic (customized for your server)
            nick = e.target
            with self._admin_lock:
                if nick in self.pending_admin_commands:
                    command, params = self.pending_admin_commands[nick]
                    del self.pending_admin_commands[nick]
                else:
                    command, params = None, None
            
            if command and params:
                if self.admin_commands.process_nickserv_response(nick, e.arguments):
                    self.handle_admin_command(c, e, command, params)
                else:
                    c.notice(nick, "You are not authorized to use admin commands.")
        else:
            # Other notices (server messages, etc.)
            logger.debug(f"Notice from {e.source.nick}: {notice_message}")

    def on_motd(self, c, e):
        """Handle Message of the Day from IRC server."""
        motd_line = ' '.join(e.arguments)
        if motd_line.strip():
            logger.info(f"MOTD: {motd_line}")

    def on_join(self, c, e):
        """Handle channel join event."""
        joined_channel = e.target
        joined_nick = e.source.nick
        if joined_nick.lower() == c.get_nickname().lower():
            # Bot joined the channel
            logger.info("=" * 60)
            logger.info(f"✓ Successfully joined channel: {joined_channel}")
            logger.info(f"✓ Quiz channel set to: {self.channel}")
            logger.info("=" * 60)
            logger.info("Bot is now ready and listening for commands!")
            
            # Announce if game was interrupted by disconnect
            if self.quiz_game.game_interrupted:
                c.privmsg(self.channel, " ")
                c.privmsg(self.channel, "\x0304⚠ The previous quiz was interrupted due to bot disconnection.\x03")
                if self.quiz_game.scores:
                    # Show partial scores if any
                    c.privmsg(self.channel, "Partial scores before interruption:")
                    sorted_scores = sorted(self.quiz_game.scores.items(), key=lambda x: x[1], reverse=True)
                    for user, score in sorted_scores:
                        c.privmsg(self.channel, f"  {user}: {score} points")
                c.privmsg(self.channel, "The quiz has been cancelled. Please start a new quiz with !start")
                c.privmsg(self.channel, " ")
                # Reset the interrupted flag and game state
                self.quiz_game.game_interrupted = False
                self.quiz_game.reset_game()
                # Ensure channel is not in moderated mode
                c.mode(self.channel, "-m")
        else:
            # Someone else joined
            logger.debug(f"User {joined_nick} joined {joined_channel}")

    def on_kick(self, c, e):
        logger.info("Kicked from channel. Attempting to rejoin.")
        time.sleep(rejoin_interval)
        c.join(self.channel)

    def on_disconnect(self, c, e):
        """
        Handle disconnection from IRC server.
        
        Automatically attempts to reconnect with exponential backoff.
        Handles connection errors gracefully to prevent bot crashes.
        If a game is active, it will be cancelled.
        """
        if not self.should_reconnect:
            return  # Do not attempt to reconnect if shutdown is intentional
        
        # Check if a game was active and cancel it
        if self.quiz_game.game_active:
            logger.warning("Game was active during disconnect - cancelling game")
            self.quiz_game.game_active = False
            self.quiz_game.game_interrupted = True
            self.quiz_game.joining_allowed = False
            # Note: Can't send message to channel here (connection is dead)
            # Will announce on reconnect
        
        self.reconnection_attempts += 1
        if self.reconnection_attempts > self.max_reconnection_attempts:
            logger.error("Maximum reconnection attempts reached. Bot stopped.")
            logger.error("Bot will not automatically reconnect. Use startbot.sh to restart.")
            return

        wait_time = min(self.max_reconnect_wait, 2 ** self.reconnection_attempts)
        logger.info(f"Disconnected. Attempting to reconnect in {wait_time} seconds (attempt {self.reconnection_attempts}/{self.max_reconnection_attempts}).")
        time.sleep(wait_time)
        
        # Attempt reconnection with error handling
        try:
            logger.info("Attempting to reconnect...")
            self.connect()
            # If we get here, connection was successful
            logger.info("✓ Reconnection successful!")
            # Reset attempts after successful reconnection
            self.reconnection_attempts = 0
        except Exception as e:
            # Connection failed - log error and let on_disconnect be called again
            logger.error(f"Reconnection attempt failed: {e}")
            logger.warning(f"Will retry in next disconnect event (attempt {self.reconnection_attempts}/{self.max_reconnection_attempts})")
            # Don't reset attempts - let it continue trying
            # The on_disconnect will be called again when the failed connection is detected

    def on_ping(self, c, e):
        logger.info(f"Received PING, sending PONG.")
        c.pong(e.target)

    def _start_reclaim_nickname_thread(self):
        timer_thread = threading.Thread(target=self._reclaim_nickname_periodically)
        timer_thread.daemon = True
        timer_thread.start()

    def _reclaim_nickname_periodically(self):
        while True:
            time.sleep(nickname_retry_interval)
            if self.connection.is_connected():
                self._attempt_reclaim_nickname(self.connection)

    def _attempt_reclaim_nickname(self, c):
        if c.get_nickname() != self.original_nickname:
            logger.info(f"Attempting to reclaim nickname: {self.original_nickname}")
            c.nick(self.original_nickname)

# Note: This module should be imported, not run directly.
# Use run.py as the entry point instead:
#   python3 run.py
#
# The run.py entry point provides:
#   - Better error handling
#   - .env file loading
#   - Proper configuration management via config.py
#   - Cleaner architecture
