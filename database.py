"""
Database Manager for Quizzer IRC Bot

This module handles all database operations including creating the database,
storing scores, and retrieving leaderboard data.

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

Version: 0.90.2
"""
# Standard library imports
import logging
import os
import sqlite3

# Local imports
from config import project_path

# ============================================================================
# Directory Setup
# ============================================================================

LOGS_DIR = project_path('logs')
DB_DIR = project_path('db')
DB_PATH = project_path('db', 'quiz_leaderboard.db')
SQLITE_TIMEOUT_SECONDS = 5.0

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger('DBManagerLogger')
logger.setLevel(logging.INFO)

try:
    log_handler = logging.FileHandler(project_path('logs', 'database.log'))
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
except (OSError, PermissionError) as e:
    # Fallback to console logging if file can't be written
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    logger.warning(
        f"Could not create log file '{project_path('logs', 'database.log')}': {e}. "
        f"Using console logging."
    )


# ============================================================================
# Database Functions
# ============================================================================

def create_database():
    """
    Create the SQLite database and scores table if they don't exist.
    
    Raises:
        OSError: If database file cannot be created
    """
    try:
        with sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    user TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    games_played INTEGER DEFAULT 0,
                    highest_score INTEGER DEFAULT 0,
                    quiz_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    except (OSError, PermissionError) as e:
        logger.error(f"Could not create database '{DB_PATH}': {e}")
        raise

def store_score(user, score):
    """
    Store a user's score in the database.
    
    Args:
        user: Username/nickname
        score: Score to store
        
    Returns:
        True when the score is stored, False if persistence failed.

    Note:
        Errors are logged but don't raise exceptions to avoid disrupting quiz flow.
    """
    try:
        with sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO scores (user, score) VALUES (?, ?)', (user, score))
            conn.commit()
            logger.debug(f"Score stored for user '{user}'")
            return True
    except Exception as e:
        logger.error(f"Error storing score for User = {user}, Score = {score}: {e}")
        return False

def get_leaderboard():
    """
    Get the leaderboard with total scores for all users.
    
    Returns:
        List of tuples (username, total_score) sorted by score descending.
        Returns empty list on error.
    """
    try:
        with sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user, SUM(score) as total_score
                FROM scores
                GROUP BY user
                ORDER BY total_score DESC
            ''')
            leaderboard = cursor.fetchall()
            logger.info("Leaderboard retrieved")
            return leaderboard
    except Exception as e:
        logger.error(f"Error retrieving leaderboard: {e}")
        return []
