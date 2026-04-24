import os
import tempfile
import unittest

import config as config_module
from config import Config, ConfigError


VALID_CONFIG = """
quiz_settings:
  question_count: 15
  answer_time_limit: 25
  RATE_LIMIT: 3
bot_settings:
  server: "irc.example.org"
  port: 6697
  channel: "#quizzer"
  nickname: "Quizzer"
  realname: "Quizzer"
  use_ssl: true
  reconnect_interval: 15
  rejoin_interval: 15
  nickname_retry_interval: 30
nickserv_settings:
  use_nickserv: true
  nickserv_name: "N"
  nickserv_account: "Quizzer"
  nickserv_command_format: "IDENTIFY {account} {password}"
bot_log_settings:
  enable_logging: true
  enable_debug: false
  log_filename: "logs/Quizzer.log"
admin_settings:
  verification_method: "nickserv"
  admins: ["AdminNick"]
"""


class ConfigTests(unittest.TestCase):
    def tearDown(self):
        config_module._config_instance = None
        os.environ.pop("NICKSERV_PASSWORD", None)

    def test_rate_limit_is_required(self):
        invalid_config = VALID_CONFIG.replace("  RATE_LIMIT: 3\n", "")
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(invalid_config)
            config_path = handle.name

        try:
            with self.assertRaises(ConfigError):
                Config(config_path)
        finally:
            os.unlink(config_path)

    def test_invalid_verification_method_is_rejected(self):
        invalid_config = VALID_CONFIG.replace(
            '  verification_method: "nickserv"\n',
            '  verification_method: "unknown"\n',
        )
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(invalid_config)
            config_path = handle.name

        try:
            with self.assertRaises(ConfigError):
                Config(config_path)
        finally:
            os.unlink(config_path)

    def test_invalid_port_type_is_rejected(self):
        invalid_config = VALID_CONFIG.replace('  port: 6697\n', '  port: "6697"\n')
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(invalid_config)
            config_path = handle.name

        try:
            with self.assertRaises(ConfigError):
                Config(config_path)
        finally:
            os.unlink(config_path)

    def test_negative_question_count_is_rejected(self):
        invalid_config = VALID_CONFIG.replace("  question_count: 15\n", "  question_count: -1\n")
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(invalid_config)
            config_path = handle.name

        try:
            with self.assertRaises(ConfigError):
                Config(config_path)
        finally:
            os.unlink(config_path)

    def test_nickserv_password_prefers_environment(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(VALID_CONFIG)
            config_path = handle.name

        os.environ["NICKSERV_PASSWORD"] = "from-env"
        try:
            loaded = Config(config_path)
            self.assertEqual(loaded.get_nickserv_password(), "from-env")
        finally:
            os.unlink(config_path)

    def test_nickserv_password_not_required_when_disabled(self):
        config_text = VALID_CONFIG.replace("  use_nickserv: true\n", "  use_nickserv: false\n")
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(config_text)
            config_path = handle.name

        try:
            loaded = Config(config_path)
            self.assertEqual(loaded.get_nickserv_password(), "")
        finally:
            os.unlink(config_path)

    def test_nickserv_password_is_required_from_environment_when_enabled(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write(VALID_CONFIG)
            config_path = handle.name

        try:
            loaded = Config(config_path)
            with self.assertRaises(ConfigError):
                loaded.get_nickserv_password()
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
