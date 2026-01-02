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

Version: 0.90
"""
# Standard library imports
import logging
import os
import sqlite3

# ============================================================================
# Directory Setup
# ============================================================================

os.makedirs('logs', exist_ok=True)
os.makedirs('db', exist_ok=True)

# ============================================================================
# Logging Setup
# ============================================================================

logger = logging.getLogger('DBManagerLogger')
logger.setLevel(logging.INFO)

try:
    log_handler = logging.FileHandler('logs/database.log')
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
        f"Could not create log file 'logs/database.log': {e}. "
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
        with sqlite3.connect('db/quiz_leaderboard.db') as conn:
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
        logger.error(f"Could not create database 'db/quiz_leaderboard.db': {e}")
        raise

def store_score(user, score):
    """
    Store a user's score in the database.
    
    Args:
        user: Username/nickname
        score: Score to store
        
    Note:
        Errors are logged but don't raise exceptions to avoid disrupting quiz flow.
    """
    logger.info("store_score function called")
    logger.info(f"store_score called with user: {user}, score: {score}")
    try:
        with sqlite3.connect('db/quiz_leaderboard.db') as conn:
            cursor = conn.cursor()
            logger.info(f"Attempting to store score: User = {user}, Score = {score}")
            cursor.execute('INSERT INTO scores (user, score) VALUES (?, ?)', (user, score))
            conn.commit()
            logger.info(f"Score stored: {user} - {score}")
    except Exception as e:
        logger.error(f"Error storing score for User = {user}, Score = {score}: {e}")

def get_leaderboard():
    """
    Get the leaderboard with total scores for all users.
    
    Returns:
        List of tuples (username, total_score) sorted by score descending.
        Returns empty list on error.
    """
    try:
        with sqlite3.connect('db/quiz_leaderboard.db') as conn:
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
