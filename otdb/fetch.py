"""
Open Trivia Database Question Fetcher

Fetches questions from opentdb.com API and converts them to the bot's JSON format.
Prevents duplicate questions and uses standardized category names.

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
import requests
import json
import time
import html
import random
import os
import sys
import logging
from collections import defaultdict

# Handle imports - works both as module and standalone script
try:
    from .category_mapper import normalize_category, get_filename_for_category
except ImportError:
    # If running as standalone script, use absolute import
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from category_mapper import normalize_category, get_filename_for_category

# Set up logging
logger = logging.getLogger('FetchLogger')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Function to fetch questions from OTDB
def fetch_questions(amount=50, category=None, difficulty=None, type=None):
    """
    Fetch questions from Open Trivia Database API.
    
    Args:
        amount: Number of questions to fetch (default: 50)
        category: Category ID (optional)
        difficulty: easy, medium, or hard (optional)
        type: multiple or boolean (optional)
        
    Returns:
        List of question dictionaries, or empty list on error
    """
    url = "https://opentdb.com/api.php"
    params = {
        "amount": amount,
    }
    if category:
        params["category"] = category
    if difficulty:
        params["difficulty"] = difficulty
    if type:
        params["type"] = type
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check response code
        if data.get('response_code') != 0:
            logger.warning(f"API Error: Response code {data.get('response_code')}")
            return []
        
        return data.get('results', [])
    except requests.RequestException as e:
        logger.error(f"Error fetching questions: {e}")
        return []
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing response: {e}")
        return []

# Process and sort questions by category, avoiding duplicates
def process_questions(questions, existing_questions=None):
    """
    Process questions from API format to bot's JSON format.
    
    Args:
        questions: List of question dictionaries from API
        existing_questions: Set of existing question texts (for duplicate checking)
        
    Returns:
        Dictionary mapping normalized category names to lists of formatted questions
    """
    if existing_questions is None:
        existing_questions = set()
    
    sorted_questions = defaultdict(list)
    new_questions = set()
    
    for q in questions:
        # Decode HTML entities
        api_category = html.unescape(q["category"])
        question_text = html.unescape(q["question"])
        correct_answer = html.unescape(q["correct_answer"])
        incorrect_answers = [html.unescape(a) for a in q["incorrect_answers"]]
        
        # Normalize category name to bot's standard format
        normalized_category = normalize_category(api_category)
        
        # Check for duplicate question (case-insensitive)
        question_key = question_text.lower().strip()
        if question_key in existing_questions or question_key in new_questions:
            continue  # Skip duplicate
        
        # Combine and shuffle answers
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        
        # Find correct answer position after shuffling
        correct_index = all_answers.index(correct_answer)
        correct_letter = chr(65 + correct_index)  # A, B, C, D, etc.
        
        formatted_question = {
            "category": normalized_category,  # Use normalized category
            "question": question_text,
            "answers": {chr(65+i): a for i, a in enumerate(all_answers)},
            "correct": correct_letter
        }
        sorted_questions[normalized_category].append(formatted_question)
        new_questions.add(question_key)
    
    return sorted_questions

# Save questions to JSON files
def save_to_json(sorted_questions, output_dir="data"):
    """
    Save questions to JSON files by category.
    Uses standardized filenames to prevent duplicates.
    
    Args:
        sorted_questions: Dictionary of normalized category -> questions
        output_dir: Directory to save files (default: "data")
        
    Returns:
        Total number of new questions added
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load existing questions to check for duplicates
    existing_questions = load_existing_questions(output_dir)
    
    total_new_questions = 0
    for category, new_questions in sorted_questions.items():
        # Use standardized filename from category mapper
        filename = get_filename_for_category(category)
        filepath = os.path.join(output_dir, filename)

        # Read existing data if file exists
        file_questions = existing_questions.get(filename, [])
        existing_questions_text = {q["question"].lower().strip() for q in file_questions}

        # Add new questions, avoiding duplicates (case-insensitive)
        added_count = 0
        for new_question in new_questions:
            question_key = new_question["question"].lower().strip()
            if question_key not in existing_questions_text:
                file_questions.append(new_question)
                existing_questions_text.add(question_key)
                added_count += 1
                total_new_questions += 1

        # Write the combined questions back to the file
        if added_count > 0:
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(file_questions, file, ensure_ascii=False, indent=4)

    return total_new_questions


def load_existing_questions(output_dir):
    """
    Load all existing questions from all JSON files in output directory.
    
    Returns:
        Dictionary mapping filename -> list of questions
    """
    existing = {}
    if not os.path.exists(output_dir):
        return existing
    
    for filename in os.listdir(output_dir):
        if not filename.endswith('_questions.json'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing[filename] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError, IOError) as e:
            logger.warning(f"Could not load {filename}: {e}")
            existing[filename] = []
    
    return existing


def load_existing_questions(output_dir):
    """
    Load all existing questions from all JSON files in output directory.
    
    Returns:
        Dictionary mapping filename -> list of questions
    """
    existing = {}
    if not os.path.exists(output_dir):
        return existing
    
    for filename in os.listdir(output_dir):
        if not filename.endswith('_questions.json'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing[filename] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError, IOError) as e:
            logger.warning(f"Could not load {filename}: {e}")
            existing[filename] = []
    
    return existing

# Main function to continuously fetch, process, and save questions
def main():
    """
    Main function - fetches questions in a loop.
    
    Use --once flag to run once instead of looping.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Fetch questions from Open Trivia Database')
    parser.add_argument('--amount', type=int, default=50, help='Number of questions to fetch')
    parser.add_argument('--category', type=int, help='Category ID (optional)')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], help='Question difficulty')
    parser.add_argument('--type', choices=['multiple', 'boolean'], help='Question type')
    parser.add_argument('--once', action='store_true', help='Run once instead of looping')
    parser.add_argument('--output', default='data', help='Output directory (default: data)')
    parser.add_argument('--delay', type=int, default=5, help='Delay between fetches in seconds (default: 5)')
    
    args = parser.parse_args()
    
    run_count = 0
    while True:
        run_count += 1
        logger.info(f"\n=== Fetch #{run_count} ===")
        
        questions = fetch_questions(
            amount=args.amount,
            category=args.category,
            difficulty=args.difficulty,
            type=args.type
        )
        
        if not questions:
            logger.warning("No questions fetched. Check API status or parameters.")
            if args.once:
                break
            time.sleep(args.delay)
            continue
        
        # Load existing questions for duplicate checking
        existing_questions = load_existing_questions(args.output)
        all_existing_texts = set()
        for file_questions in existing_questions.values():
            for q in file_questions:
                all_existing_texts.add(q.get("question", "").lower().strip())
        
        sorted_questions = process_questions(questions, all_existing_texts)
        total_new_questions = save_to_json(sorted_questions, args.output)
        
        logger.info(f"✓ Fetched {len(questions)} questions")
        logger.info(f"✓ Processed into {len(sorted_questions)} categories")
        logger.info(f"✓ Added {total_new_questions} new questions")
        
        if args.once:
            break
            
        logger.info(f"Waiting {args.delay} seconds before next fetch...")
        time.sleep(args.delay)

if __name__ == "__main__":
    main()
