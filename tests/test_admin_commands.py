import os
import tempfile
import unittest
from unittest.mock import patch

import admin as admin_module
from admin import AdminCommands


class FakeQuizGame:
    def __init__(self):
        self.cancelled = False
        self.game_active = False
        self.participants = {}
        self.question_count = 5
        self.answer_time_limit = 10
        self.questions = {}

    def cancel_quiz(self):
        self.cancelled = True
        return True

    def get_rate_limit(self):
        return 3


class FakeConnection:
    def __init__(self):
        self.privmsgs = []
        self.notices = []
        self.modes = []
        self.quits = []

    def privmsg(self, target, message):
        self.privmsgs.append((target, message))

    def notice(self, target, message):
        self.notices.append((target, message))

    def mode(self, target, mode):
        self.modes.append((target, mode))

    def quit(self, message):
        self.quits.append(message)


class NoticeFailingConnection(FakeConnection):
    def notice(self, target, message):
        raise RuntimeError("notice delivery failed")


class FakeVerifier:
    def __init__(self):
        self.admin_nicks = {"blackroot"}
        self.sessions = {"oldadmin": ("never", "token")}
        self.failed_attempts = {"oldadmin": (1, 0)}
        self.password_hashes = {"oldadmin": "hash"}

    def set_password(self, nick, password):
        return True, f"Password updated for {nick}."

    def save_password_hashes(self):
        return None


class FailingVerifier(FakeVerifier):
    def set_password(self, nick, password):
        return False, "boom"


class HashCleanupFailingVerifier(FakeVerifier):
    def save_password_hashes(self):
        raise OSError("disk full")


class AdminCommandsTests(unittest.TestCase):
    def _temp_project_path(self, tempdir):
        def resolver(*parts):
            return os.path.join(tempdir, *parts)

        return resolver

    def setUp(self):
        self.quiz_game = FakeQuizGame()
        self.quiz_game.channel = "#quizzer"
        self.commands = AdminCommands(
            self.quiz_game,
            ["BlackRoot"],
            "NickServ",
        )
        self.connection = FakeConnection()

    def test_is_admin_is_case_insensitive(self):
        self.assertTrue(self.commands.is_admin("blackroot"))
        self.assertTrue(self.commands.is_admin("BLACKROOT"))

    def test_request_nickserv_info_uses_configured_service_name(self):
        self.commands.request_nickserv_info(self.connection, "blackroot")
        self.assertEqual(
            self.connection.privmsgs,
            [("NickServ", "INFO blackroot")],
        )

    def test_nickserv_response_parsing_handles_multiple_formats(self):
        responses = [
            "Information on blackroot:",
            "Account: blackroot",
            "Status: Online",
        ]
        self.assertTrue(
            self.commands.process_nickserv_response("blackroot", responses)
        )
        self.assertTrue(
            self.commands.nickserv_response_complete("blackroot", responses)
        )

    def test_stop_game_cancels_quiz_and_unmodes_channel(self):
        self.commands.stop_game(self.connection, "blackroot")
        self.assertTrue(self.quiz_game.cancelled)
        self.assertIn(("#quizzer", "-m"), self.connection.modes)
        self.assertIn(
            ("#quizzer", "Game has been stopped by an admin."),
            self.connection.privmsgs,
        )

    def test_set_rate_limit_rejects_negative_values(self):
        self.commands.set_rate_limit(self.connection, "blackroot", "-1")

        self.assertIn(
            ("blackroot", "Rate limit must be 0 or greater."),
            self.connection.notices,
        )

    def test_send_message_sanitizes_line_breaks(self):
        self.commands.send_message(
            self.connection,
            "#quizzer",
            "hello\r\nworld\nagain",
        )

        self.assertEqual(
            self.connection.privmsgs[-1],
            ("#quizzer", "hello  world again"),
        )

    def test_add_and_remove_admin_syncs_verifier_membership(self):
        verifier = FakeVerifier()
        commands = AdminCommands(
            self.quiz_game,
            ["BlackRoot", "OldAdmin"],
            "NickServ",
            admin_verifier=verifier,
        )
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.object(admin_module, "project_path", side_effect=self._temp_project_path(tempdir)):
                    with open(os.path.join(tempdir, "config.yaml"), "w", encoding="utf-8") as handle:
                        handle.write(
                            "admin_settings:\n"
                            "  admins:\n"
                            "    - BlackRoot\n"
                            "    - OldAdmin\n"
                        )

                    added = commands.add_admin(
                        self.connection,
                        "blackroot",
                        "NewAdmin",
                        "secret",
                    )
                    self.assertTrue(added)
                    self.assertIn("newadmin", verifier.admin_nicks)

                    removed = commands.remove_admin(
                        self.connection,
                        "blackroot",
                        "OldAdmin",
                    )
                    self.assertTrue(removed)
                    self.assertNotIn("oldadmin", verifier.admin_nicks)
                    self.assertNotIn("oldadmin", verifier.sessions)
                    self.assertNotIn("oldadmin", verifier.failed_attempts)
            finally:
                os.chdir(original_cwd)

    def test_add_admin_failure_rolls_back_config_and_membership(self):
        verifier = FailingVerifier()
        commands = AdminCommands(
            self.quiz_game,
            ["BlackRoot"],
            "NickServ",
            admin_verifier=verifier,
        )
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.object(admin_module, "project_path", side_effect=self._temp_project_path(tempdir)):
                    with open(os.path.join(tempdir, "config.yaml"), "w", encoding="utf-8") as handle:
                        handle.write(
                            "admin_settings:\n"
                            "  admins:\n"
                            "    - BlackRoot\n"
                        )

                    added = commands.add_admin(
                        self.connection,
                        "blackroot",
                        "NewAdmin",
                        "secret",
                    )
                    self.assertFalse(added)
                    self.assertNotIn("newadmin", verifier.admin_nicks)
                    self.assertNotIn("newadmin", commands.admin_nicks)

                    with open(os.path.join(tempdir, "config.yaml"), "r", encoding="utf-8") as handle:
                        config_text = handle.read()
                    self.assertNotIn("NewAdmin", config_text)
            finally:
                os.chdir(original_cwd)

    def test_add_admin_keeps_persisted_admin_when_notice_fails(self):
        verifier = FakeVerifier()
        commands = AdminCommands(
            self.quiz_game,
            ["BlackRoot"],
            "NickServ",
            admin_verifier=verifier,
        )
        connection = NoticeFailingConnection()
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.object(admin_module, "project_path", side_effect=self._temp_project_path(tempdir)):
                    with open(os.path.join(tempdir, "config.yaml"), "w", encoding="utf-8") as handle:
                        handle.write(
                            "admin_settings:\n"
                            "  admins:\n"
                            "    - BlackRoot\n"
                        )

                    added = commands.add_admin(
                        connection,
                        "blackroot",
                        "NewAdmin",
                        "secret",
                    )
                    self.assertTrue(added)
                    self.assertIn("newadmin", commands.admin_nicks)
                    self.assertIn("newadmin", verifier.admin_nicks)

                    with open(os.path.join(tempdir, "config.yaml"), "r", encoding="utf-8") as handle:
                        config_text = handle.read()
                    self.assertIn("NewAdmin", config_text)
            finally:
                os.chdir(original_cwd)

    def test_remove_admin_reports_hash_cleanup_warning(self):
        verifier = HashCleanupFailingVerifier()
        commands = AdminCommands(
            self.quiz_game,
            ["BlackRoot", "OldAdmin"],
            "NickServ",
            admin_verifier=verifier,
        )
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            try:
                with patch.object(admin_module, "project_path", side_effect=self._temp_project_path(tempdir)):
                    with open(os.path.join(tempdir, "config.yaml"), "w", encoding="utf-8") as handle:
                        handle.write(
                            "admin_settings:\n"
                            "  admins:\n"
                            "    - BlackRoot\n"
                            "    - OldAdmin\n"
                        )

                    removed = commands.remove_admin(
                        self.connection,
                        "blackroot",
                        "OldAdmin",
                    )
                    self.assertTrue(removed)
                    self.assertIn(
                        (
                            "blackroot",
                            "Admin 'OldAdmin' was removed, but password hash cleanup failed.",
                        ),
                        self.connection.notices,
                    )
            finally:
                os.chdir(original_cwd)

    def test_restart_and_stop_use_project_script_path(self):
        with tempfile.TemporaryDirectory() as tempdir:
            script_path = os.path.join(tempdir, "tools", "startbot.sh")
            os.makedirs(os.path.dirname(script_path), exist_ok=True)
            with open(script_path, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\n")
            os.chmod(script_path, 0o755)

            with patch.object(admin_module, "project_path", side_effect=self._temp_project_path(tempdir)):
                with patch.object(admin_module.subprocess, "run") as run_mock:
                    self.commands.restart_bot(self.connection)
                    self.commands.stop_bot(self.connection)

        self.assertEqual(self.connection.quits, ["Restarting for maintenance.", "Received signal to shut down."])
        self.assertEqual(
            run_mock.call_args_list[0].args[0],
            [script_path, "restart"],
        )
        self.assertEqual(
            run_mock.call_args_list[1].args[0],
            [script_path, "stop"],
        )

    def test_get_bot_stats_counts_top_level_categories(self):
        with patch("category_hierarchy.build_category_hierarchy", return_value={"Entertainment": ["Music"], "Animals": None}):
            self.commands.get_bot_stats(self.connection, "blackroot")

        stats_text = "\n".join(message for _, message in self.connection.notices)
        self.assertIn("Main categories: 2", stats_text)


if __name__ == "__main__":
    unittest.main()
