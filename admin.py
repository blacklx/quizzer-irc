"""
Admin Commands Module for Quizzer IRC Bot

This module handles all admin-only commands including bot management,
game control, and administrative functions.

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
import subprocess
import logging
import os
import yaml
from quiz_game import QuizGame
from admin_verifier import AdminVerifier

# Ensure required directories exist
os.makedirs('logs', exist_ok=True)

# Set up logging for admin actions
admin_logger = logging.getLogger('AdminLogger')
admin_logger.setLevel(logging.INFO)
try:
    file_handler = logging.FileHandler('logs/admin_actions.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    admin_logger.addHandler(file_handler)
except (OSError, PermissionError) as e:
    # Fallback to console logging if file can't be written
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    admin_logger.addHandler(console_handler)
    admin_logger.warning(f"Could not create log file 'logs/admin_actions.log': {e}. Using console logging.")

class AdminCommands:
    """
    Handles admin-only commands and bot management.
    
    Provides functionality for stopping games, restarting the bot,
    managing rate limits, and other administrative tasks.
    """
    def __init__(self, quiz_game: QuizGame, admin_nicks, nickserv_name, 
                 admin_verifier: AdminVerifier = None):
        """
        Initialize AdminCommands.
        
        Args:
            quiz_game: QuizGame instance to manage
            admin_nicks: List of admin nicknames
            nickserv_name: NickServ service name
            admin_verifier: AdminVerifier instance (optional, for password/hostmask verification)
        """
        self.quiz_game = quiz_game
        self.admin_nicks = set(admin_nicks)  # Set of admin nicks for faster lookup
        self.admin_verifier = admin_verifier

    def is_admin(self, user):
        # Check if a user is an admin
        return user in self.admin_nicks

    def request_nickserv_info(self, connection, nick):
        # Send a request to NickServ for information about the nick
        connection.privmsg("N", f"INFO {nick}")

    def process_nickserv_response(self, nick, responses):
        """
        Process NickServ INFO response to verify admin status.
        
        This method checks if the user is registered and online.
        This was customized for UmbrellaNet IRC network.
        
        Args:
            nick: The nickname to verify
            responses: List of response strings from NickServ
            
        Returns:
            bool: True if user is registered and online, False otherwise
        """
        is_registered = False
        is_online = False
        
        # Log the raw response for debugging (to see exact format)
        admin_logger.debug(f"NickServ INFO response for {nick}: {responses}")
        
        # Original parsing logic (customized for your server)
        for response in responses:
            if f"Account: {nick}" in response:
                is_registered = True
            if f"{nick} is currently online." in response:
                is_online = True
        
        result = is_registered and is_online
        admin_logger.info(f"NickServ verification for {nick}: registered={is_registered}, online={is_online}, authorized={result}")
        
        return result

    def get_current_rate_limit(self):
        return self.quiz_game.get_rate_limit()

    def set_rate_limit(self, connection, nick, new_limit):
        if self.is_admin(nick):
            try:
                new_limit = int(new_limit)
                self.quiz_game.set_rate_limit(new_limit)
                connection.notice(nick, f"Rate limit updated to {new_limit} seconds.")
            except ValueError:
                connection.notice(nick, "Invalid rate limit value.")

    def stop_game(self, connection, nick):
        if self.quiz_game.game_active:
            self.quiz_game.game_active = False
            connection.privmsg(self.quiz_game.channel, "Game has been stopped by an admin.")
            admin_logger.info(f"Game stopped by admin.")
        else:
            connection.privmsg(nick, "No active game to stop.")

    def get_admin_help_message(self):
        help_msg = (
            "Admin Commands Help:\n"
            "!admin stop - Stops the bot with a shutdown message.\n"
            "!admin restart - Restarts the bot with a maintenance message.\n"
            "!admin msg <user/#channel> <message> - Sends a message from the bot.\n"
            "!admin set_rate_limit <seconds> - Sets a new rate limit for quiz commands.\n"
            "!admin stop_game - Stops the current game for various reasons.\n"
            "!admin stats - Shows comprehensive bot statistics.\n"
        )
        
        # Add password-based commands if verifier is available
        if self.admin_verifier and self.admin_verifier.verification_method in ['password', 'combined']:
            help_msg += (
                "\nPassword Verification Commands:\n"
                "!admin verify <password> - Verify admin password and start session.\n"
                "!admin set_password <nick> <password> - Set or update admin password.\n"
                "!admin add_admin <nick> <password> - Add new admin (requires existing admin).\n"
                "!admin remove_admin <nick> - Remove admin (requires existing admin).\n"
                "!admin list_admins - List all admin nicknames.\n"
            )
        
        return help_msg
    
    def add_admin(self, connection, nick, new_admin_nick, password):
        """Add a new admin (requires existing admin session)."""
        if not self.is_admin(nick):
            connection.notice(nick, "You are not authorized to add admins.")
            return False
        
        if not self.admin_verifier:
            connection.notice(nick, "Admin verifier not configured. Cannot add admins via command.")
            return False
        
        # Add to admin list
        new_admin_lower = new_admin_nick.lower()
        if new_admin_lower in self.admin_nicks:
            connection.notice(nick, f"Admin '{new_admin_nick}' already exists.")
            return False
        
        # Add to config.yaml
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            if 'admin_settings' not in config:
                config['admin_settings'] = {}
            
            if 'admins' not in config['admin_settings']:
                config['admin_settings']['admins'] = []
            
            if new_admin_nick not in config['admin_settings']['admins']:
                config['admin_settings']['admins'].append(new_admin_nick)
            
            with open('config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Update in-memory list
            self.admin_nicks.add(new_admin_lower)
            
            # Set password
            success, msg = self.admin_verifier.set_password(new_admin_nick, password)
            if success:
                connection.notice(nick, f"✓ Admin '{new_admin_nick}' added successfully.")
                connection.notice(nick, "Password hashed and saved. New admin can verify now.")
                admin_logger.info(f"Admin '{new_admin_nick}' added by {nick}")
                return True
            else:
                connection.notice(nick, f"Error setting password: {msg}")
                return False
        except Exception as e:
            connection.notice(nick, f"Error adding admin: {e}")
            admin_logger.error(f"Error adding admin: {e}")
            return False
    
    def remove_admin(self, connection, nick, admin_to_remove):
        """Remove an admin (requires existing admin session)."""
        if not self.is_admin(nick):
            connection.notice(nick, "You are not authorized to remove admins.")
            return False
        
        admin_to_remove_lower = admin_to_remove.lower()
        if admin_to_remove_lower not in self.admin_nicks:
            connection.notice(nick, f"Admin '{admin_to_remove}' not found.")
            return False
        
        # Don't allow removing yourself
        if admin_to_remove_lower == nick.lower():
            connection.notice(nick, "You cannot remove yourself as admin.")
            return False
        
        # Remove from config.yaml
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            if 'admin_settings' in config and 'admins' in config['admin_settings']:
                config['admin_settings']['admins'] = [
                    a for a in config['admin_settings']['admins'] 
                    if a.lower() != admin_to_remove_lower
                ]
            
            with open('config.yaml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Update in-memory list
            self.admin_nicks.discard(admin_to_remove_lower)
            
            # Remove password hash if verifier exists
            if self.admin_verifier and admin_to_remove_lower in self.admin_verifier.password_hashes:
                del self.admin_verifier.password_hashes[admin_to_remove_lower]
                # Update hash file
                hash_file = 'admin_passwords.yaml'
                if os.path.exists(hash_file):
                    try:
                        with open(hash_file, 'r') as f:
                            data = yaml.safe_load(f) or {}
                        if 'passwords' in data:
                            data['passwords'] = {
                                k: v for k, v in data['passwords'].items() 
                                if k.lower() != admin_to_remove_lower
                            }
                        with open(hash_file, 'w') as f:
                            yaml.dump(data, f, default_flow_style=False)
                    except Exception as e:
                        admin_logger.warning(f"Could not update password hash file: {e}")
            
            connection.notice(nick, f"✓ Admin '{admin_to_remove}' removed successfully.")
            admin_logger.info(f"Admin '{admin_to_remove}' removed by {nick}")
            return True
        except Exception as e:
            connection.notice(nick, f"Error removing admin: {e}")
            admin_logger.error(f"Error removing admin: {e}")
            return False
    
    def list_admins(self, connection, nick):
        """List all admin nicknames."""
        if not self.is_admin(nick):
            connection.notice(nick, "You are not authorized to list admins.")
            return
        
        admins_list = sorted(self.admin_nicks)
        connection.notice(nick, f"Admins ({len(admins_list)}): {', '.join(admins_list)}")
        admin_logger.info(f"Admin list requested by {nick}")
    
    def set_password(self, connection, nick, target_nick, new_password):
        """Set or update admin password."""
        if not self.is_admin(nick):
            connection.notice(nick, "You are not authorized to set passwords.")
            return False
        
        if not self.admin_verifier:
            connection.notice(nick, "Admin verifier not configured.")
            return False
        
        # Check if target is admin
        if not self.is_admin(target_nick):
            connection.notice(nick, f"'{target_nick}' is not an admin.")
            return False
        
        success, msg = self.admin_verifier.set_password(target_nick, new_password)
        if success:
            connection.notice(nick, msg)
            admin_logger.info(f"Password updated for {target_nick} by {nick}")
        else:
            connection.notice(nick, msg)
        
        return success

    def restart_bot(self, connection):
        """Restart the bot using the startbot.sh script."""
        connection.quit("Restarting for maintenance.")
        # Use absolute path to prevent path injection
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools', 'startbot.sh')
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            subprocess.run([script_path, 'restart'], check=False)
        else:
            admin_logger.error(f"startbot.sh not found or not executable: {script_path}")

    def stop_bot(self, connection):
        """Stop the bot using the startbot.sh script."""
        connection.quit("Received signal to shut down.")
        # Use absolute path to prevent path injection
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tools', 'startbot.sh')
        if os.path.exists(script_path) and os.access(script_path, os.X_OK):
            subprocess.run([script_path, 'stop'], check=False)
        else:
            admin_logger.error(f"startbot.sh not found or not executable: {script_path}")

    def send_message(self, connection, target, message):
        connection.privmsg(target, message)
        admin_logger.info(f"Message sent to {target}: {message}")

    def broadcast_message(self, message):
        # Logic to broadcast a message to all channels or specific channel
        pass

    def get_bot_stats(self, connection, nick):
        """
        Display comprehensive bot statistics.
        
        Shows:
        - Questions loaded per category
        - Total questions
        - Categories available
        - Database statistics
        - Current game state
        """
        import os
        import json
        import sqlite3
        from category_hierarchy import build_category_hierarchy
        
        stats_lines = []
        stats_lines.append("=== Bot Statistics ===")
        stats_lines.append("")
        
        # Game state
        stats_lines.append("Game State:")
        stats_lines.append(f"  Active: {'Yes' if self.quiz_game.game_active else 'No'}")
        stats_lines.append(f"  Participants: {len(self.quiz_game.participants)}")
        stats_lines.append(f"  Questions per quiz: {self.quiz_game.question_count}")
        stats_lines.append(f"  Answer time limit: {self.quiz_game.answer_time_limit}s")
        stats_lines.append(f"  Rate limit: {self.quiz_game.get_rate_limit()}s")
        stats_lines.append("")
        
        # Questions loaded
        total_questions = len(self.quiz_game.questions)
        stats_lines.append("Questions Loaded:")
        stats_lines.append(f"  Total in memory: {total_questions}")
        stats_lines.append("")
        
        # Questions by category (from files)
        quiz_data_dir = 'quiz_data'
        if os.path.exists(quiz_data_dir):
            category_counts = {}
            total_in_files = 0
            json_files = [f for f in os.listdir(quiz_data_dir) if f.endswith('_questions.json')]
            
            for filename in json_files:
                filepath = os.path.join(quiz_data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                        count = len(questions)
                        category_name = filename.replace('_questions.json', '').replace('_', ' ')
                        category_counts[category_name] = count
                        total_in_files += count
                except (FileNotFoundError, json.JSONDecodeError, OSError, IOError):
                    continue
            
            stats_lines.append("Questions in Files:")
            stats_lines.append(f"  Total: {total_in_files}")
            stats_lines.append(f"  Categories: {len(category_counts)}")
            
            # Show top 5 categories by question count
            if category_counts:
                sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
                stats_lines.append("  Top categories:")
                for cat, count in sorted_cats[:5]:
                    stats_lines.append(f"    {cat}: {count}")
        else:
            stats_lines.append("Questions in Files:")
            stats_lines.append("  quiz_data/ directory not found")
        
        stats_lines.append("")
        
        # Category hierarchy
        try:
            hierarchy = build_category_hierarchy()
            main_cats = len([k for k in hierarchy.keys() if isinstance(hierarchy[k], dict)])
            stats_lines.append("Category System:")
            stats_lines.append(f"  Main categories: {main_cats}")
            stats_lines.append(f"  Hierarchical structure: Active")
        except Exception as e:
            stats_lines.append("Category System:")
            stats_lines.append(f"  Error loading: {e}")
        
        stats_lines.append("")
        
        # Database statistics
        try:
            with sqlite3.connect('db/quiz_leaderboard.db') as conn:
                cursor = conn.cursor()
                
                # Total entries
                cursor.execute('SELECT COUNT(*) FROM scores')
                total_entries = cursor.fetchone()[0]
                
                # Unique users
                cursor.execute('SELECT COUNT(DISTINCT user) FROM scores')
                unique_users = cursor.fetchone()[0]
                
                # Total score sum
                cursor.execute('SELECT SUM(score) FROM scores')
                total_score = cursor.fetchone()[0] or 0
                
                # Top scorer
                cursor.execute('''
                    SELECT user, SUM(score) as total_score
                    FROM scores
                    GROUP BY user
                    ORDER BY total_score DESC
                    LIMIT 1
                ''')
                top_scorer = cursor.fetchone()
                
                stats_lines.append("Database Statistics:")
                stats_lines.append(f"  Total entries: {total_entries}")
                stats_lines.append(f"  Unique users: {unique_users}")
                stats_lines.append(f"  Total points: {total_score}")
                if top_scorer:
                    stats_lines.append(f"  Top scorer: {top_scorer[0]} ({top_scorer[1]} points)")
        except Exception as e:
            stats_lines.append("Database Statistics:")
            stats_lines.append(f"  Error: {e}")
        
        # Send stats in parts (IRC message length limit)
        message = '\n'.join(stats_lines)
        # Split into chunks of ~400 characters to avoid IRC message limits
        max_length = 400
        lines = message.split('\n')
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            if current_length + line_length > max_length and current_chunk:
                # Send current chunk
                chunk_message = '\n'.join(current_chunk)
                connection.notice(nick, chunk_message)
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # Send remaining chunk
        if current_chunk:
            chunk_message = '\n'.join(current_chunk)
            connection.notice(nick, chunk_message)
        
        admin_logger.info(f"Stats requested by {nick}")

    # Additional admin commands as needed
