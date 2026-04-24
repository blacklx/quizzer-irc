import unittest
from unittest.mock import patch
import tempfile
import os

from quiz_game import QuizGame, create_delayed_handle, handle_start_command


class FakeTimer:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


class FakeScheduler:
    def __init__(self):
        self.queue = []

    def add(self, command):
        self.queue.append(command)


class QuizGameTests(unittest.TestCase):
    def test_load_questions_from_file_normalizes_correct_answer_key(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        with tempfile.TemporaryDirectory() as tempdir:
            valid_path = os.path.join(tempdir, "valid_questions.json")
            with open(valid_path, "w", encoding="utf-8") as handle:
                handle.write(
                    '[{"question": "Q?", "category": "Animals", "answers": {"A": "Cat"}, "correct": "a"}]'
                )

            loaded = quiz_game.load_questions_from_file(valid_path)

        self.assertTrue(loaded)
        self.assertEqual(quiz_game.questions["Q?"]["correct"], "A")

    def test_load_questions_from_file_rejects_invalid_question_entries(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        with tempfile.TemporaryDirectory() as tempdir:
            invalid_path = os.path.join(tempdir, "invalid_questions.json")
            with open(invalid_path, "w", encoding="utf-8") as handle:
                handle.write('[{"category": "Animals", "answers": {"A": "Cat"}, "correct": "A"}]')

            loaded = quiz_game.load_questions_from_file(invalid_path)

        self.assertFalse(loaded)
        self.assertEqual(quiz_game.questions, {})

    def test_cancel_quiz_clears_active_state_and_timer(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        quiz_game.game_active = True
        quiz_game.joining_allowed = True
        quiz_game.current_question = "Question?"
        quiz_game.participants = {"alice": 0}
        quiz_game.scores = {"alice": 2}
        timer = FakeTimer()
        quiz_game.set_start_timer(timer)

        cancelled = quiz_game.cancel_quiz()

        self.assertTrue(cancelled)
        self.assertTrue(timer.cancelled)
        self.assertTrue(quiz_game.stop_event.is_set())
        self.assertFalse(quiz_game.game_active)
        self.assertFalse(quiz_game.joining_allowed)
        self.assertIsNone(quiz_game.current_question)
        self.assertEqual(quiz_game.participants, {})
        self.assertEqual(quiz_game.scores, {})

    def test_cancel_quiz_can_preserve_scores_for_disconnect_reporting(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        quiz_game.game_active = True
        quiz_game.participants = {"alice": 0}
        quiz_game.scores = {"alice": 2}

        quiz_game.cancel_quiz(
            preserve_scores=True,
            preserve_participants=True,
            interrupted=True,
        )

        self.assertTrue(quiz_game.game_interrupted)
        self.assertEqual(quiz_game.participants, {"alice": 0})
        self.assertEqual(quiz_game.scores, {"alice": 2})

    def test_handle_start_command_returns_when_game_already_active(self):
        class FakeQuiz:
            def __init__(self):
                self.game_active = True
                self.joining_allowed = False
                self.channel = "#quizzer"
                self.question_count = 5
                self.begin_join_window_called = False
                self.timer = None

            def load_questions(self, category):
                return True

            def begin_join_window(self, timer):
                self.begin_join_window_called = True
                self.timer = timer
                return False, "A quiz is already active."

        class FakeConnection:
            def __init__(self):
                self.notices = []

            def notice(self, target, message):
                self.notices.append((target, message))

            def privmsg(self, target, message):
                raise AssertionError("Should not announce a new quiz when one is active")

            def mode(self, target, mode):
                raise AssertionError("Should not toggle channel mode when one is active")

        fake_quiz = FakeQuiz()
        connection = FakeConnection()

        with patch('quiz_game.threading.Timer') as timer_cls:
            handle_start_command(fake_quiz, "random", connection, "alice")

        self.assertTrue(fake_quiz.begin_join_window_called)
        self.assertIsNotNone(fake_quiz.timer)
        timer_cls.assert_called_once()
        self.assertEqual(
            connection.notices,
            [("alice", "A quiz is already active.")]
        )

    def test_begin_join_window_sets_timer_atomically(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        timer = FakeTimer()

        started, error = quiz_game.begin_join_window(timer)

        self.assertTrue(started)
        self.assertIsNone(error)
        self.assertTrue(quiz_game.joining_allowed)
        self.assertIs(quiz_game.start_timer, timer)

    def test_begin_join_window_rejects_second_scheduled_quiz(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        first_timer = FakeTimer()
        second_timer = FakeTimer()

        first_started, _ = quiz_game.begin_join_window(first_timer)
        second_started, second_error = quiz_game.begin_join_window(second_timer)

        self.assertTrue(first_started)
        self.assertFalse(second_started)
        self.assertEqual(
            second_error,
            "A quiz is already scheduled to start. Please join now.",
        )
        self.assertIs(quiz_game.start_timer, first_timer)

    def test_create_delayed_handle_uses_reactor_scheduler_when_available(self):
        calls = []
        connection = type(
            "Connection",
            (),
            {"reactor": type("Reactor", (), {"scheduler": FakeScheduler()})()},
        )()

        handle = create_delayed_handle(connection, 45, lambda value: calls.append(value), args=("ok",))
        handle.start()

        self.assertEqual(len(connection.reactor.scheduler.queue), 1)
        connection.reactor.scheduler.queue[0].target()
        self.assertEqual(calls, ["ok"])

    def test_scheduled_handle_cancel_removes_pending_command(self):
        connection = type(
            "Connection",
            (),
            {"reactor": type("Reactor", (), {"scheduler": FakeScheduler()})()},
        )()

        handle = create_delayed_handle(connection, 45, lambda: None)
        handle.start()
        self.assertEqual(len(connection.reactor.scheduler.queue), 1)

        handle.cancel()

        self.assertEqual(connection.reactor.scheduler.queue, [])

    def test_process_answer_emits_response_after_unlocking(self):
        quiz_game = QuizGame("#quizzer", 5, 10)
        quiz_game.game_active = True
        quiz_game.participants = {"alice": 0}
        quiz_game.scores = {"alice": 0}
        quiz_game.current_question = "Q?"
        quiz_game.questions = {"Q?": {"correct": "A", "answers": {"A": "Cat"}, "category": "Animals"}}

        events = []

        class Connection:
            def privmsg(self_inner, target, message):
                events.append(("send", target, message))
                self.assertFalse(quiz_game._lock._is_owned())

        quiz_game.process_answer("alice", "a", Connection())

        self.assertEqual(quiz_game.scores["alice"], 1)
        self.assertEqual(events[0][1], "#quizzer")
        self.assertIn("Correct!", events[0][2])


if __name__ == "__main__":
    unittest.main()
