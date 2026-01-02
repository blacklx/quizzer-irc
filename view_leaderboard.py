"""
Database Viewer for Quizzer IRC Bot

Simple utility script to view database contents.
Useful for debugging and checking leaderboard data.

Usage:
    python3 view_leaderboard.py

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
import sqlite3
import re
import sys

# Connect to the SQLite database
try:
    with sqlite3.connect('db/quiz_leaderboard.db') as conn:
        cursor = conn.cursor()
        
        # Get a list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in database.")
            sys.exit(0)
        
        # Loop through the tables and read data from each one
        for table in tables:
            table_name = table[0]
            # Validate table name to prevent SQL injection (only alphanumeric and underscore)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
                print(f"Skipping invalid table name: {table_name}", file=sys.stderr)
                continue
            
            # Use parameterized query with table name validation
            # Note: SQLite doesn't support parameterized table names, so we validate instead
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            
            # Print the data from the current table
            print(f"\nTable: {table_name}")
            print("-" * 60)
            if rows:
                for row in rows:
                    print(row)
            else:
                print("(empty)")
except FileNotFoundError:
    print("Error: Database file 'db/quiz_leaderboard.db' not found.", file=sys.stderr)
    print("Make sure the bot has been run at least once to create the database.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
