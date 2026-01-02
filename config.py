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

Version: 0.90
"""
import yaml
import os
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Raised when there's an error loading or validating configuration."""
    pass


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
        self.config_path = config_path
        self.config = self._load_config()
        self._validate()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as config_file:
                return yaml.safe_load(config_file)
        except FileNotFoundError:
            raise ConfigError(f"Configuration file '{self.config_path}' not found.")
        except yaml.YAMLError as e:
            raise ConfigError(f"Error loading YAML configuration: {e}")
    
    def _validate(self):
        """Validate that all required configuration keys are present."""
        required_keys = {
            'quiz_settings': ['question_count', 'answer_time_limit'],
            'bot_settings': ['server', 'port', 'channel', 'nickname', 'realname', 'use_ssl', 
                           'reconnect_interval', 'rejoin_interval', 'nickname_retry_interval'],
            'nickserv_settings': ['use_nickserv', 'nickserv_name', 'nickserv_account', 
                                 'nickserv_command_format'],
            'bot_log_settings': ['enable_logging', 'enable_debug', 'log_filename'],
            'admin_settings': ['admins']
        }
        
        for category, keys in required_keys.items():
            if category not in self.config:
                raise ConfigError(f"Missing '{category}' section in config.yaml")
            for key in keys:
                if key not in self.config[category]:
                    raise ConfigError(f"Missing '{key}' in '{category}' section of config.yaml")
    
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
        Get NickServ password from environment variable or config.
        
        Returns:
            NickServ password
            
        Raises:
            ConfigError: If password is not set
        """
        password = os.getenv('NICKSERV_PASSWORD', 
                           self.config['nickserv_settings'].get('nickserv_password', ''))
        if not password:
            raise ConfigError(
                "NICKSERV_PASSWORD environment variable must be set, "
                "or nickserv_password must be in config.yaml"
            )
        return password


# Global config instance (loaded on import)
_config_instance: Optional[Config] = None


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

