"""
Quiz Game Module for Quizzer IRC Bot

This module contains the QuizGame class and related functions that handle
quiz game logic, question management, scoring, and game flow.

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
from contextlib import suppress
import html
import json
import logging
import os
import random
import threading
import time

# Third-party imports
from tempora.schedule import DelayedCommand

# Local imports
from config import ConfigError, load_config, project_path
from database import store_score

# ============================================================================
# Configuration
# ============================================================================

try:
    config = load_config()
    RATE_LIMIT = config.get('quiz_settings', 'RATE_LIMIT')
    BOT_NICKNAME = config.get('bot_settings', 'nickname')
except ConfigError:
    config = None
    RATE_LIMIT = 3
    BOT_NICKNAME = 'Quizzer'

# ============================================================================
# Directory Setup
# ============================================================================

os.makedirs(project_path('logs'), exist_ok=True)
os.makedirs(project_path('quiz_data'), exist_ok=True)

# ============================================================================
# Logging Setup
# ============================================================================

quiz_logger = logging.getLogger('QuizGameLogger')
quiz_logger.setLevel(logging.INFO)

try:
    quiz_handler = logging.FileHandler(project_path('logs', 'quiz_game.log'))
    quiz_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    quiz_handler.setFormatter(quiz_formatter)
    quiz_logger.addHandler(quiz_handler)
except (OSError, PermissionError) as e:
    # Fallback to console logging if file can't be written
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    quiz_logger.addHandler(console_handler)
    quiz_logger.warning(
        f"Could not create log file '{project_path('logs', 'quiz_game.log')}': {e}. "
        f"Using console logging."
    )


class ScheduledCommandHandle:
    """Timer-like wrapper around the IRC reactor scheduler."""

    def __init__(self, scheduler, delay, callback, args=None, kwargs=None):
        self.scheduler = scheduler
        self.callback = callback
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})
        self._cancelled = False
        self.command = DelayedCommand.after(delay, self._run)

    def _run(self):
        if self._cancelled:
            return
        self.callback(*self.args, **self.kwargs)

    def start(self):
        if not self._cancelled:
            self.scheduler.add(self.command)

    def cancel(self):
        self._cancelled = True
        with suppress(ValueError):
            self.scheduler.queue.remove(self.command)


def create_delayed_handle(connection, delay, callback, args=None, kwargs=None):
    """Use the IRC reactor scheduler when available, else fall back to threading.Timer."""
    scheduler = getattr(getattr(connection, "reactor", None), "scheduler", None)
    if scheduler and hasattr(scheduler, "add"):
        return ScheduledCommandHandle(scheduler, delay, callback, args=args, kwargs=kwargs)
    return threading.Timer(delay, callback, args=args, kwargs=kwargs)


# ============================================================================
# QuizGame Class
# ============================================================================

class QuizGame:
    """
    Manages quiz game state and logic.
    
    Handles question loading, participant management, scoring,
    and game flow control.
    
    Attributes:
        channel: IRC channel name
        questions: Dictionary of loaded questions
        participants: Dictionary of participants (nick -> score)
        scores: Dictionary of current scores
        game_active: Whether a quiz is currently running
        question_count: Number of questions per quiz
        answer_time_limit: Time limit for answering (seconds)
    """
    def __init__(self, channel, question_count, answer_time_limit):
        """
        Initialize a new QuizGame instance.
        
        Args:
            channel: IRC channel name
            question_count: Number of questions per quiz
            answer_time_limit: Time limit for answering questions (seconds)
        """
        self.channel = channel
        self.questions = {}
        self.current_question = None
        self.participants = {}
        self.scores = {}
        self.game_active = False
        self.question_count = question_count
        self.answer_time_limit = answer_time_limit
        self.joining_allowed = False
        self.asked_questions = set()
        self.last_command_time = {}  # For rate limiting
        self.answered_participants = {}  # Track if a participant has answered
        self._lock = threading.RLock()  # Lock for thread-safe access to shared state
        self.game_interrupted = False  # Track if game was interrupted by disconnect
        self.stop_event = threading.Event()
        self.start_timer = None

    def set_rate_limit(self, new_limit):
        global RATE_LIMIT
        RATE_LIMIT = new_limit

    def get_rate_limit(self):
        global RATE_LIMIT
        return RATE_LIMIT

    def reset_game(self):
        with self._lock:
            self.stop_event.clear()
            if self.start_timer:
                self.start_timer.cancel()
                self.start_timer = None
            self.participants.clear()
            self.scores.clear()
            self.current_question = None
            self.game_active = False
            self.joining_allowed = False
            self.asked_questions.clear()
            self.answered_participants = {}
            self.game_interrupted = False  # Reset interrupted flag
            quiz_logger.info(f"Scores after reset: {self.scores}")

    def reset_current_question(self):
        with self._lock:
            self.current_question = None
            self.answered_participants = {}  # Track if a participant has answered

    def allow_joining(self):
        with self._lock:
            self.stop_event.clear()
            self.joining_allowed = True

    def begin_join_window(self, timer):
        """Atomically reserve the next quiz start and store its timer."""
        with self._lock:
            if self.game_active:
                return False, "A quiz is already active."
            if self.joining_allowed or self.start_timer is not None:
                return False, "A quiz is already scheduled to start. Please join now."

            self.stop_event.clear()
            self.joining_allowed = True
            self.start_timer = timer
            return True, None

    def set_start_timer(self, timer):
        with self._lock:
            self.start_timer = timer

    def cancel_quiz(self, preserve_scores=False, preserve_participants=False, interrupted=False):
        """
        Cancel a scheduled or active quiz.

        Returns True if there was anything to cancel.
        """
        with self._lock:
            had_quiz = (
                self.game_active or
                self.joining_allowed or
                (self.start_timer is not None)
            )
            self.stop_event.set()
            if self.start_timer:
                self.start_timer.cancel()
                self.start_timer = None
            self.game_active = False
            self.joining_allowed = False
            self.current_question = None
            self.answered_participants = {}
            self.game_interrupted = interrupted
            if not preserve_scores:
                self.scores.clear()
            if not preserve_participants:
                self.participants.clear()
            return had_quiz

    def load_questions(self, category):
        """
        Load questions for a category.
        
        Supports hierarchical categories:
        - "Entertainment" → loads all Entertainment subcategories
        - "Entertainment_Music" → loads specific subcategory
        - "random" → loads all categories
        """
        with self._lock:
            self.questions.clear()
            self.asked_questions.clear()  # Clear the set of asked questions
        
        if category == "random":
            all_categories = self.get_available_categories()
            for cat in all_categories:
                if not self.load_questions_from_file(
                    project_path('quiz_data', f"{cat}_questions.json")
                ):
                    return False
            return True
        else:
            # Check if it's a main category that should load all subcategories
            from category_hierarchy import get_category_hierarchy, find_category_match
            
            # Try to match using hierarchy
            main_cat, subcat, is_random = find_category_match(category)
            
            if main_cat and is_random:
                # Load all subcategories for this main category
                hierarchy = get_category_hierarchy()
                subcategories = hierarchy.get(main_cat, [])
                if subcategories:
                    for subcat_name in subcategories:
                        filename = subcat_name.replace(' ', '_')
                        if not self.load_questions_from_file(
                            project_path('quiz_data', f"{filename}_questions.json")
                        ):
                            return False
                    return True
            
            # Load specific category (subcategory or standalone)
            if subcat:
                return self.load_questions_from_file(
                    project_path('quiz_data', f"{subcat}_questions.json")
                )
            elif main_cat:
                filename = main_cat.replace(' ', '_')
                return self.load_questions_from_file(
                    project_path('quiz_data', f"{filename}_questions.json")
                )
            else:
                # Fallback to old behavior (backward compatibility)
                return self.load_questions_from_file(
                    project_path('quiz_data', f"{category}_questions.json")
                )

    def load_questions_from_file(self, filename):
        #quiz_logger.info(f"Trying to load file: {filename}")
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                questions_data = json.load(file)
                if not isinstance(questions_data, list):
                    raise TypeError("Question file must contain a JSON list.")

                loaded_questions = 0
                parsed_questions = {}
                for index, q in enumerate(questions_data, start=1):
                    if not isinstance(q, dict):
                        quiz_logger.warning(f"Skipping malformed question #{index} in '{filename}': entry is not an object.")
                        continue

                    question_text = q.get('question')
                    category = q.get('category')
                    answers = q.get('answers')
                    correct = q.get('correct')

                    if not isinstance(question_text, str) or not question_text.strip():
                        quiz_logger.warning(f"Skipping malformed question #{index} in '{filename}': missing question text.")
                        continue
                    if not isinstance(category, str) or not category.strip():
                        quiz_logger.warning(f"Skipping malformed question #{index} in '{filename}': missing category.")
                        continue
                    if not isinstance(answers, dict) or not answers:
                        quiz_logger.warning(f"Skipping malformed question #{index} in '{filename}': answers must be a non-empty mapping.")
                        continue
                    normalized_correct = str(correct).upper()
                    if normalized_correct not in {str(label).upper() for label in answers}:
                        quiz_logger.warning(f"Skipping malformed question #{index} in '{filename}': correct answer key not found.")
                        continue

                    normalized_question = html.unescape(question_text)
                    normalized_answers = {
                        str(label): html.unescape(str(answer))
                        for label, answer in answers.items()
                    }
                    parsed_questions[normalized_question] = {
                        "answers": normalized_answers,
                        "correct": normalized_correct,
                        "category": category,
                    }
                    loaded_questions += 1

                with self._lock:
                    for normalized_question, data in parsed_questions.items():
                        if normalized_question in self.asked_questions:
                            continue
                        self.questions[normalized_question] = data

                return loaded_questions > 0
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError) as e:
            quiz_logger.error(f"Error loading file '{filename}': {e}")
            return False

    def get_available_categories(self):
        categories = []
        for filename in os.listdir(project_path('quiz_data')):
            if filename.endswith('_questions.json'):
                categories.append(filename.replace('_questions.json', ''))
        return categories

    def ask_question(self, connection, question, question_number, data):
        with self._lock:
            if question in self.asked_questions:
                return
            if self.stop_event.is_set() or not self.game_active:
                return
            self.asked_questions.add(question)
            self.current_question = question
            self.answered_participants = {}
        connection.privmsg(self.channel, " ")
        q_category = data["category"]
        connection.privmsg(self.channel, f"[ Category: \x02{q_category}\x02 ]")
        connection.privmsg(self.channel, " ")
        bold_question = f"\x0312Question {question_number:02}\x03: \x02{question}\x02"
        connection.privmsg(self.channel, bold_question)
        for label, answer in data["answers"].items():
            connection.privmsg(self.channel, f"\x0312{label}\x03: {answer}")
        connection.privmsg(self.channel, " ")  # Blank line
        connection.privmsg(self.channel, f"You have \x0304{self.answer_time_limit}\x03 seconds to answer.")
        connection.privmsg(self.channel, " ")

    def show_results(self, connection):
        with self._lock:
            if self.stop_event.is_set() or self.current_question is None:
                return
            question = self.current_question
            correct_answer = self.questions[question]["correct"]
            correct_answer_text = self.questions[question]["answers"][correct_answer]
        connection.privmsg(self.channel, f"The correct answer was {correct_answer}: \x02{correct_answer_text}\x02")
        connection.privmsg(self.channel, " ")
        # Additional feedback, if necessary

    def end_quiz(self, connection):
        with self._lock:
            score_snapshot = dict(self.scores)
            self.game_active = False
            self.joining_allowed = False

        if not score_snapshot:
            connection.privmsg(self.channel, "Quiz ended with no scores to report.")
            connection.mode(self.channel, "-m")
            self.reset_game()
            return

        connection.privmsg(self.channel, " ")
        max_score = max(score_snapshot.values())
        winners = [nick for nick, score in score_snapshot.items() if score == max_score]
        connection.privmsg(self.channel, f"\x0303Quiz ended.\x03")
        connection.privmsg(self.channel, " ")
        connection.privmsg(self.channel, f"\x02Winners:\x02 \x0303{', '.join(winners)}\x03 with \x0303{max_score} points.\x03")
        connection.privmsg(self.channel, " ")
        # Announce all participants sorted by score, one line per user
        connection.privmsg(self.channel, "\x02Scores:\x02")
        connection.privmsg(self.channel, " ")
        sorted_scores = sorted(score_snapshot.items(), key=lambda x: x[1], reverse=True)
        max_username_length = max(len(user) for user, _ in sorted_scores)
        for user, score in sorted_scores:
            padded_user = user.ljust(max_username_length)
            connection.privmsg(self.channel, f" {padded_user} : {score} points")
        connection.privmsg(self.channel, " ")
        connection.mode(self.channel, "-m")  # Set channel to non-moderated

        # Store the scores before resetting the game
        quiz_logger.info(f"Scores at end of quiz: {score_snapshot}")
        failed_persists = []
        for user, score in score_snapshot.items():
            quiz_logger.info(f"Storing score for user: {user}, score: {score}")
            if not store_score(user, score):
                failed_persists.append(user)

        if failed_persists:
            quiz_logger.warning(
                f"Could not persist scores for: {', '.join(failed_persists)}"
            )

        self.reset_game()

    def process_answer(self, user, answer, connection):
        quiz_logger.debug(
            "process_answer called with user=%s answer_length=%s",
            user,
            len(answer),
        )

        response_message = None
        with self._lock:
            # Rate limiting check
            if user in self.last_command_time:
                if time.time() - self.last_command_time[user] < RATE_LIMIT:
                    response_message = f"{user}, please wait before sending another command."
                else:
                    self.last_command_time[user] = time.time()
            else:
                self.last_command_time[user] = time.time()

            if response_message is None:
                if not self.game_active or user not in self.participants or self.current_question is None:
                    return
                if user in self.answered_participants:
                    # Ignore if the user has already answered
                    return

                correct_answer = self.questions[self.current_question]["correct"]
                if answer.upper() == correct_answer:
                    quiz_logger.info(f"Correct answer by user: {user}")
                    self.scores[user] += 1
                    quiz_logger.info(f"Updated scores: {self.scores}")
                    response_message = f"{user} answered \x0303Correct!\x03"
                else:
                    response_message = f"{user} answered \x0304Wrong!\x03"
                # Mark the user as having answered
                self.answered_participants[user] = True

        if response_message:
            connection.privmsg(self.channel, response_message)

def start_quiz(quiz_game, actual_category, connection):
    """
    Start and run a quiz game.
    
    Loads questions, asks them one by one with time limits,
    processes answers, and ends the quiz.
    
    Args:
        quiz_game: QuizGame instance
        actual_category: Category name for the quiz
        connection: IRC connection object
    """
    if quiz_game.stop_event.is_set():
        quiz_logger.info("Quiz start aborted because the quiz was cancelled before launch.")
        return

    with quiz_game._lock:
        has_participants = bool(quiz_game.participants)

    if not has_participants:
        connection.privmsg(quiz_game.channel, "Quiz cancelled due to no participants.")
        connection.mode(quiz_game.channel, "-m")
        quiz_game.reset_game()
        return
    if not quiz_game.load_questions(actual_category):
        connection.privmsg(quiz_game.channel, "Error: Unable to load questions.")
        connection.mode(quiz_game.channel, "-m")
        quiz_game.reset_game()
        return

    with quiz_game._lock:
        quiz_game.game_active = True
        quiz_game.joining_allowed = False
        quiz_game.start_timer = None
        quiz_game.scores = {nick: 0 for nick in quiz_game.participants}

    # Randomly select questions for the quiz
    questions = random.sample(list(quiz_game.questions.items()), min(quiz_game.question_count, len(quiz_game.questions)))
    for i, (question, data) in enumerate(questions, start=1):
        if quiz_game.stop_event.is_set() or not quiz_game.game_active:
            break
        quiz_game.ask_question(connection, question, i, data)
        if quiz_game.stop_event.wait(quiz_game.answer_time_limit):
            break
        if quiz_game.stop_event.is_set() or not quiz_game.game_active:
            break
        quiz_game.show_results(connection)

    if quiz_game.stop_event.is_set() or not quiz_game.game_active:
        try:
            connection.mode(quiz_game.channel, "-m")
        except Exception as exc:
            quiz_logger.warning(f"Could not reset channel mode during cancellation: {exc}")
        if not quiz_game.game_interrupted:
            try:
                connection.privmsg(quiz_game.channel, "Quiz cancelled.")
            except Exception as exc:
                quiz_logger.warning(f"Could not announce quiz cancellation: {exc}")
        quiz_game.reset_game()
        return

    quiz_game.end_quiz(connection)

def handle_start_command(quiz_game, category, connection, user):
    """
    Handle the !start command to begin a new quiz.
    
    Supports hierarchical categories:
    - "entertainment" → random from all Entertainment
    - "entertainment music" → Entertainment Music specifically
    - "animals" → Animals category
    
    Args:
        quiz_game: QuizGame instance
        category: Category name (or "random")
        connection: IRC connection object
        user: Nickname of user who started the quiz
    """
    from category_hierarchy import find_category_match
    
    # Use hierarchy system to find category
    if category.lower() == "random":
        formatted_category = "random"
        display_category = "random"
    else:
        main_cat, subcat, is_random = find_category_match(category)
        
        if not main_cat:
            connection.notice(user, f"Error: Category '{category}' not found. Use !categories to see available categories.")
            return
        
        # Determine what to load and display
        if subcat:
            formatted_category = subcat  # Use subcategory filename
            # Get display name (remove main category prefix)
            display_category = subcat.replace('_', ' ').replace(main_cat + ' ', '')
        elif is_random:
            formatted_category = main_cat.replace(' ', '_')  # Will load all subcategories
            display_category = main_cat
        else:
            formatted_category = main_cat.replace(' ', '_')
            display_category = main_cat

    timer = create_delayed_handle(
        connection,
        45,
        start_quiz,
        args=(quiz_game, formatted_category, connection),
    )
    join_window_opened, error_message = quiz_game.begin_join_window(timer)
    if not join_window_opened:
        connection.notice(user, error_message)
        return

    connection.privmsg(quiz_game.channel, " ")
    connection.privmsg(quiz_game.channel, f"A quiz on '\x0304{display_category}\x03' category will start in\x0304 45\x03 seconds. \x0303'/msg {BOT_NICKNAME} !join'\x03 to participate.")
    connection.privmsg(quiz_game.channel, f"The quiz round will consist of \x0303{quiz_game.question_count}\x03 questions.")
    connection.privmsg(quiz_game.channel, f"To register your answer to each question: \x0303'/msg {BOT_NICKNAME} !a <answer>'\x03")
    connection.privmsg(quiz_game.channel, " ")
    connection.mode(quiz_game.channel, "+m")
    timer.start()

def handle_join_command(quiz_game, user, connection):
    """
    Handle the !join command to allow a user to join a quiz.
    
    Args:
        quiz_game: QuizGame instance
        user: Nickname of user joining
        connection: IRC connection object
    """
    with quiz_game._lock:
        # Check if a quiz is not active and if joining is allowed
        if not quiz_game.game_active and not quiz_game.joining_allowed:
            connection.notice(user, "Sorry, there is no quiz currently accepting participants.")
        elif quiz_game.game_active:
            connection.notice(user, "Sorry, a quiz is already in progress. Please wait for the next round.")
        elif user in quiz_game.participants:
            connection.notice(user, "You have already registered for the quiz.")
        else:
            quiz_game.participants[user] = 0
            connection.privmsg(quiz_game.channel, f"{user} has joined the quiz! Good luck!")

def handle_categories_command(params=None):
    """
    Handle categories command with hierarchical display.
    
    Args:
        params: Optional list of parameters (e.g., ['entertainment'] to show subcategories)
        
    Returns:
        Tuple of (main_category, subcategories, display_mode)
    """
    from category_hierarchy import (
        get_main_categories, get_subcategories, format_category_display,
        find_category_match, get_category_hierarchy
    )
    
    # If specific category requested, show its subcategories
    if params and len(params) > 0:
        category_input = ' '.join(params).lower()
        main_cat, subcat, is_random = find_category_match(category_input)
        
        if main_cat and get_subcategories(main_cat):
            # Show subcategories for this main category
            subcats = get_subcategories(main_cat)
            short_subs = [s.replace(main_cat + ' ', '') for s in subcats]
            return main_cat, short_subs, 'subcategories'
        elif main_cat:
            # Standalone category, no subcategories
            return main_cat, [], 'standalone'
    
    # Default: show all main categories
    return None, None, 'main'

def handle_help_command():
    return ("Commands: "
            "!start <category> - Start a quiz (e.g., !start entertainment, !start entertainment music). | "
            "!categories [category] - List main categories, or show subcategories for a category. | "
            f"!join - Join an upcoming quiz. Use '/msg {BOT_NICKNAME} !join'. | "
            f"!a <answer> - Answer a quiz question. Use '/msg {BOT_NICKNAME} !a <answer>'. | "
            "Examples: !start entertainment | !start entertainment music | !categories entertainment")
