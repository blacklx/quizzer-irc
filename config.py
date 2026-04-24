"""
Configuration loader for Quizzer IRC Bot.

This module provides a centralized way to load and validate configuration
from config.yaml, eliminating duplicate config loading code.

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
import os
from typing import Any, Dict, Optional

# Third-party imports
import yaml


# ============================================================================
# Exceptions
# ============================================================================


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def project_path(*parts: str) -> str:
    """Build an absolute path inside the project root."""
    return os.path.join(BASE_DIR, *parts)


class ConfigError(Exception):
    """Raised when there's an error loading or validating configuration."""
    pass


# ============================================================================
# Config Class
# ============================================================================


class Config:
    """Configuration manager for the Quizzer bot."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from YAML file.
        
        Args:
            config_path: Path to the config.yaml file
            
        Raises:
            ConfigError: If config file is missing or invalid
        """
        if os.path.isabs(config_path):
            self.config_path = config_path
        else:
            self.config_path = project_path(config_path)
        self.config = self._load_config()
        self._validate()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as config_file:
                return yaml.safe_load(config_file)
        except FileNotFoundError:
            raise ConfigError(f"Configuration file '{self.config_path}' not found.")
        except yaml.YAMLError as e:
            raise ConfigError(f"Error loading YAML configuration: {e}")
    
    def _validate(self):
        """Validate that all required configuration keys are present."""
        required_keys = {
            'quiz_settings': ['question_count', 'answer_time_limit', 'RATE_LIMIT'],
            'bot_settings': [
                'server', 'port', 'channel', 'nickname', 'realname', 'use_ssl',
                'reconnect_interval', 'rejoin_interval', 'nickname_retry_interval'
            ],
            'nickserv_settings': [
                'use_nickserv', 'nickserv_name', 'nickserv_account',
                'nickserv_command_format'
            ],
            'bot_log_settings': ['enable_logging', 'enable_debug', 'log_filename'],
            'admin_settings': ['admins']
        }
        
        for category, keys in required_keys.items():
            if category not in self.config:
                raise ConfigError(f"Missing '{category}' section in config.yaml")
            for key in keys:
                if key not in self.config[category]:
                    raise ConfigError(f"Missing '{key}' in '{category}' section of config.yaml")

        verification_method = self.get(
            'admin_settings',
            'verification_method',
            default='nickserv'
        )
        allowed_methods = {'nickserv', 'password', 'hostmask', 'combined'}
        if str(verification_method).lower() not in allowed_methods:
            raise ConfigError(
                "Invalid admin verification method. "
                f"Expected one of: {', '.join(sorted(allowed_methods))}"
            )

        self._validate_positive_int('quiz_settings', 'question_count', minimum=1)
        self._validate_positive_int('quiz_settings', 'answer_time_limit', minimum=1)
        self._validate_positive_int('quiz_settings', 'RATE_LIMIT', minimum=0)
        self._validate_positive_int('bot_settings', 'port', minimum=1, maximum=65535)
        self._validate_positive_int('bot_settings', 'reconnect_interval', minimum=1)
        self._validate_positive_int('bot_settings', 'rejoin_interval', minimum=1)
        self._validate_positive_int('bot_settings', 'nickname_retry_interval', minimum=1)
        self._validate_bool('bot_settings', 'use_ssl')
        self._validate_bool('nickserv_settings', 'use_nickserv')
        self._validate_bool('bot_log_settings', 'enable_logging')
        self._validate_bool('bot_log_settings', 'enable_debug')

    def _validate_positive_int(
        self,
        section: str,
        key: str,
        *,
        minimum: int,
        maximum: Optional[int] = None,
    ) -> None:
        value = self.get(section, key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"'{section}.{key}' must be an integer.")
        if value < minimum:
            raise ConfigError(f"'{section}.{key}' must be >= {minimum}.")
        if maximum is not None and value > maximum:
            raise ConfigError(f"'{section}.{key}' must be <= {maximum}.")

    def _validate_bool(self, section: str, key: str) -> None:
        value = self.get(section, key)
        if not isinstance(value, bool):
            raise ConfigError(f"'{section}.{key}' must be true or false.")
    
    def get(self, *keys, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            *keys: Path to the config value (e.g., 'bot_settings', 'server')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get('bot_settings', 'server')
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_nickserv_password(self) -> str:
        """
        Get NickServ password from the environment.
        
        Returns:
            NickServ password
            
        Raises:
            ConfigError: If password is not set
        """
        if not self.get('nickserv_settings', 'use_nickserv', default=True):
            return ''

        password = os.getenv('NICKSERV_PASSWORD', '')
        if not password:
            raise ConfigError(
                "NICKSERV_PASSWORD environment variable must be set when NickServ is enabled."
            )
        return password


# ============================================================================
# Global Configuration Instance
# ============================================================================

_config_instance: Optional[Config] = None


# ============================================================================
# Public Functions
# ============================================================================


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration (singleton pattern).
    
    Args:
        config_path: Path to config file
        
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance


def load_env_file(env_file: str = '.env'):
    """
    Load KEY=VALUE pairs from a local .env file into the process environment.

    Existing environment variables win over file values.
    """
    env_path = project_path(env_file)
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, 'r', encoding='utf-8') as env_handle:
            for line in env_handle:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value and key not in os.environ:
                    os.environ[key] = value
    except OSError as exc:
        raise ConfigError(f"Could not load environment file '{env_file}': {exc}")


def get_config() -> Config:
    """
    Get the global config instance.
    
    Returns:
        Config instance
        
    Raises:
        ConfigError: If config hasn't been loaded yet
    """
    if _config_instance is None:
        raise ConfigError("Configuration not loaded. Call load_config() first.")
    return _config_instance

