import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bot import QuizzerBot


class QuizzerBotTests(unittest.TestCase):
    def _make_bot(self):
        bot = QuizzerBot.__new__(QuizzerBot)
        bot._admin_lock = threading.Lock()
        bot.pending_admin_commands = {}
        bot.admin_commands = Mock()
        return bot

    def test_match_pending_admin_notice_uses_exact_nick_tokens(self):
        bot = self._make_bot()
        bot.pending_admin_commands = {
            "alice": {"nick": "Alice"},
            "malice": {"nick": "Malice"},
        }

        matched = bot._match_pending_admin_notice("Information on malice: account is verified")

        self.assertEqual(matched, "malice")

    def test_match_pending_admin_notice_single_pending_falls_back(self):
        bot = self._make_bot()
        bot.pending_admin_commands = {
            "alice": {"nick": "Alice"},
        }

        matched = bot._match_pending_admin_notice("Status: account is verified")

        self.assertEqual(matched, "alice")

    def test_handle_admin_command_preserves_multi_word_passwords(self):
        bot = self._make_bot()
        connection = Mock()
        event = SimpleNamespace(source=SimpleNamespace(nick="blackroot"))

        bot.handle_admin_command(
            connection,
            event,
            "!admin",
            ["set_password", "targetnick", "multi", "word", "secret"],
            nick="blackroot",
        )

        bot.admin_commands.set_password.assert_called_once_with(
            connection,
            "blackroot",
            "targetnick",
            "multi word secret",
        )

    def test_on_welcome_uses_reactor_scheduler_for_delayed_join(self):
        bot = self._make_bot()
        bot.reconnection_attempts = 3
        bot.use_nickserv = False
        bot.channel = "#quizzer"
        connection = Mock()
        connection.get_nickname.return_value = "Quizzer"
        delayed_handle = Mock()

        with patch("bot.create_delayed_handle", return_value=delayed_handle) as create_handle:
            bot.on_welcome(connection, Mock())

        self.assertEqual(bot.reconnection_attempts, 0)
        create_handle.assert_called_once()
        call_args = create_handle.call_args.args
        self.assertIs(call_args[0], connection)
        self.assertEqual(call_args[1], 5)
        call_args[2]()
        connection.join.assert_called_once_with("#quizzer")
        delayed_handle.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
