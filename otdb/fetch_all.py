#!/usr/bin/env python3
"""
Fetch ALL questions from Open Trivia Database

Downloads questions from all categories, respecting rate limits.
Continues until no new questions are found.

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
import html
import json
import logging
import os
import random
import sys
import time

# Third-party imports
import requests
from collections import defaultdict

# Handle imports - works both as module and standalone script
try:
    from .category_mapper import normalize_category, get_filename_for_category
except ImportError:
    # If running as standalone script, use absolute import
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from category_mapper import normalize_category, get_filename_for_category

# Set up logging
logger = logging.getLogger('FetchAllLogger')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Rate limiting - Open Trivia DB has strict limits
# Using 3 seconds as default to be very safe
REQUEST_DELAY = 3.0  # seconds between requests

# Maximum questions per API call (API limit is 50)
MAX_QUESTIONS_PER_REQUEST = 50

# Retry settings for rate limit errors
MAX_RETRIES = 5
INITIAL_BACKOFF = 10  # seconds to wait after first 429 error


def fetch_questions(amount=50, category=None, difficulty=None, type=None, retry_count=0):
    """
    Fetch questions from Open Trivia Database API.
    
    Args:
        amount: Number of questions to fetch (max 50)
        category: Category ID (optional)
        difficulty: easy, medium, or hard (optional)
        type: multiple or boolean (optional)
        retry_count: Number of retries attempted (for rate limit handling)
        
    Returns:
        Tuple of (questions_list, should_retry)
        - questions_list: List of question dictionaries, or empty list on error
        - should_retry: True if we got rate limited and should retry
    """
    url = "https://opentdb.com/api.php"
    params = {
        "amount": min(amount, 50),  # API max is 50
    }
    if category:
        params["category"] = category
    if difficulty:
        params["difficulty"] = difficulty
    if type:
        params["type"] = type

    try:
        response = requests.get(url, params=params, timeout=10)
        
        # Handle rate limiting (429 Too Many Requests)
        if response.status_code == 429:
            return [], True  # Return empty list and indicate we should retry
        
        response.raise_for_status()
        data = response.json()

        if data.get('response_code') == 0:
            return data.get('results', []), False
        elif data.get('response_code') == 1:
            logger.warning("No results for this request")
            return [], False
        elif data.get('response_code') == 2:
            logger.warning("Invalid parameter")
            return [], False
        elif data.get('response_code') == 3:
            logger.warning("Token not found")
            return [], False
        elif data.get('response_code') == 4:
            logger.warning("Token empty")
            return [], False
        else:
            logger.warning(f"Unknown response code {data.get('response_code')}")
            return [], False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return [], True  # Rate limited, should retry
        logger.error(f"HTTP Error: {e}")
        return [], False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching questions: {e}")
        return [], False
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing response: {e}")
        return [], False


def process_questions(questions, existing_questions_texts=None):
    """
    Process questions from API format to bot's JSON format.
    
    Args:
        questions: List of question dictionaries from API
        existing_questions_texts: Set of existing question texts (for duplicate checking)
        
    Returns:
        Dictionary mapping category names to lists of formatted questions
    """
    if existing_questions_texts is None:
        existing_questions_texts = set()
    
    sorted_questions = defaultdict(list)
    for q in questions:
        # Decode HTML entities
        category = html.unescape(q["category"])
        question_text = html.unescape(q["question"])
        correct_answer = html.unescape(q["correct_answer"])
        incorrect_answers = [html.unescape(a) for a in q["incorrect_answers"]]

        # Check for duplicates (case-insensitive)
        question_key = question_text.lower().strip()
        if question_key in existing_questions_texts:
            continue  # Skip duplicate

        # Combine and shuffle answers
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)

        # Find correct answer position after shuffling
        correct_index = all_answers.index(correct_answer)
        correct_letter = chr(65 + correct_index)  # A, B, C, D, etc.

        # Normalize category name
        normalized_category = normalize_category(category)

        formatted_question = {
            "category": normalized_category,
            "question": question_text,
            "answers": {chr(65+i): a for i, a in enumerate(all_answers)},
            "correct": correct_letter
        }
        sorted_questions[normalized_category].append(formatted_question)
        existing_questions_texts.add(question_key)  # Track this question
    
    return sorted_questions


def load_existing_questions(output_dir):
    """
    Load all existing questions from all JSON files.
    
    Returns:
        Dictionary mapping filename -> list of questions
    """
    existing = {}
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
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


def save_to_json(sorted_questions, output_dir="data"):
    """
    Save processed questions to JSON files.
    
    Args:
        sorted_questions: Dictionary of category -> questions
        output_dir: Directory to save files
        
    Returns:
        Total number of new questions added
    """
    os.makedirs(output_dir, exist_ok=True)
    
    total_new_questions = 0
    for category, new_questions in sorted_questions.items():
        # Use standardized filename
        filename = get_filename_for_category(category)
        filepath = os.path.join(output_dir, filename)

        # Read existing data if file exists
        existing_questions = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_questions = json.load(f)
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            logger.warning(f"Corrupted file {filename}, overwriting")
            existing_questions = []

        # Add new questions, avoiding duplicates
        existing_questions_text = {q["question"].lower().strip() for q in existing_questions}
        added_count = 0
        for new_question in new_questions:
            question_key = new_question["question"].lower().strip()
            if question_key not in existing_questions_text:
                existing_questions.append(new_question)
                existing_questions_text.add(question_key)
                added_count += 1
                total_new_questions += 1

        # Write the combined questions back to the file
        if added_count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_questions, f, ensure_ascii=False, indent=4)

    return total_new_questions


def get_all_categories():
    """Get all category IDs from Open Trivia Database."""
    try:
        response = requests.get('https://opentdb.com/api_category.php', timeout=10)
        response.raise_for_status()
        data = response.json()
        categories = data.get('trivia_categories', [])
        return [(cat['id'], cat['name']) for cat in categories]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return []


def fetch_all_questions(output_dir='data', max_iterations_per_category=100, request_delay=None):
    """
    Fetch ALL questions from all categories.
    
    Args:
        output_dir: Directory to save question files
        max_iterations_per_category: Maximum API calls per category (safety limit)
        request_delay: Delay between requests (uses default if None)
    """
    if request_delay is None:
        request_delay = REQUEST_DELAY
    logger.info("=" * 60)
    logger.info("Open Trivia Database - Fetch ALL Questions")
    logger.info("=" * 60)
    
    # Get all categories
    logger.info("\nFetching category list...")
    categories = get_all_categories()
    if not categories:
        logger.error("ERROR: Could not fetch categories. Exiting.")
        return
    
    logger.info(f"Found {len(categories)} categories")
    logger.info(f"Rate limit: {request_delay} seconds between requests")
    logger.info(f"Max questions per request: {MAX_QUESTIONS_PER_REQUEST}")
    logger.info(f"Max iterations per category: {max_iterations_per_category}")
    logger.info("\n" + "=" * 60)
    
    # Load existing questions for duplicate checking
    logger.info("\nLoading existing questions...")
    existing_questions = load_existing_questions(output_dir)
    all_existing_texts = set()
    for file_questions in existing_questions.values():
        for q in file_questions:
            all_existing_texts.add(q.get("question", "").lower().strip())
    
    logger.info(f"Found {len(all_existing_texts)} existing questions")
    logger.info("\n" + "=" * 60)
    
    # Fetch from each category
    total_new_questions = 0
    total_requests = 0
    
    for cat_id, cat_name in categories:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Category: {cat_name} (ID: {cat_id})")
        logger.info(f"{'=' * 60}")
        
        category_new_questions = 0
        iterations = 0
        consecutive_empty = 0
        consecutive_no_new = 0  # Track requests with no new questions
        
        while iterations < max_iterations_per_category:
            iterations += 1
            total_requests += 1
            
            logger.info(f"  Request #{iterations} (Total: {total_requests})...", end='')
            
            # Fetch questions with retry logic for rate limiting
            retry_count = 0
            questions = []
            should_retry = False
            
            while retry_count < MAX_RETRIES:
                questions, should_retry = fetch_questions(
                    amount=MAX_QUESTIONS_PER_REQUEST,
                    category=cat_id,
                    retry_count=retry_count
                )
                
                if should_retry:
                    # Rate limited - wait with exponential backoff
                    backoff_time = INITIAL_BACKOFF * (2 ** retry_count)
                    logger.warning(f"  ⚠ Rate limited! Waiting {backoff_time} seconds before retry...")
                    time.sleep(backoff_time)
                    retry_count += 1
                    logger.info("  Retrying...")
                    continue
                else:
                    break  # Success or non-retryable error
            
            if should_retry and retry_count >= MAX_RETRIES:
                logger.error(f"  ❌ Rate limited after {MAX_RETRIES} retries. Waiting longer...")
                # Wait even longer before continuing
                time.sleep(INITIAL_BACKOFF * 2)
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.warning("  → Too many rate limit errors. Moving to next category.")
                    break
                continue
            
            if not questions:
                consecutive_empty += 1
                logger.debug(f"No questions returned (empty count: {consecutive_empty})")
                
                # If we get 3 consecutive empty responses, assume we've got everything
                if consecutive_empty >= 3:
                    logger.info("  → No more questions available for this category")
                    break
                
                time.sleep(request_delay)
                continue
            
            consecutive_empty = 0  # Reset counter
            
            # Process questions
            sorted_questions = process_questions(questions, all_existing_texts)
            
            # Save questions
            new_count = save_to_json(sorted_questions, output_dir)
            category_new_questions += new_count
            total_new_questions += new_count
            
            # Check if we got questions but none were new (all duplicates)
            if len(questions) > 0 and new_count == 0:
                consecutive_no_new += 1
                if consecutive_no_new >= 10:  # 10 requests with no new questions
                    logger.info(f"  → No new questions found after {consecutive_no_new} requests. Moving to next category.")
                    break
            else:
                consecutive_no_new = 0  # Reset counter if we found new questions
            
            # Update existing questions set
            for cat, q_list in sorted_questions.items():
                for q in q_list:
                    all_existing_texts.add(q["question"].lower().strip())
            
            logger.info(f"  Fetched {len(questions)}, added {new_count} new questions")
            
            # If we got fewer questions than requested, we might be at the end
            if len(questions) < MAX_QUESTIONS_PER_REQUEST:
                logger.debug("  → Got fewer questions than requested, may have reached end")
                # Continue a few more times to be sure
                if len(questions) < 10:  # Very few questions
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        break
            
            # Rate limiting
            time.sleep(request_delay)
        
        logger.info(f"\n  Category complete: {category_new_questions} new questions added")
        logger.info(f"  Total requests for this category: {iterations}")
    
    logger.info("\n" + "=" * 60)
    logger.info("FETCH COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total categories processed: {len(categories)}")
    logger.info(f"Total API requests: {total_requests}")
    logger.info(f"Total new questions added: {total_new_questions}")
    logger.info(f"Total questions in database: {len(all_existing_texts)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fetch ALL questions from Open Trivia Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all questions to default 'data' directory
  python fetch_all.py
  
  # Fetch all questions to quiz_data directory
  python fetch_all.py --output ../quiz_data
  
  # Limit iterations per category (for testing)
  python fetch_all.py --max-iterations 10
        """
    )
    parser.add_argument(
        '--output',
        default='data',
        help='Output directory for question files (default: data)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=100,
        help='Maximum API calls per category (default: 100, safety limit)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=REQUEST_DELAY,
        help=f'Delay between requests in seconds (default: {REQUEST_DELAY}, recommended: 3-5)'
    )
    
    args = parser.parse_args()
    
    # Update delay if specified
    delay = args.delay
    
    # Pass delay to fetch function (we'll need to update the function signature)
    # For now, just use the global constant
    fetch_all_questions(
        output_dir=args.output,
        max_iterations_per_category=args.max_iterations,
        request_delay=delay
    )

