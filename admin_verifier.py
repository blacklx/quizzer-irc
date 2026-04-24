"""
Admin Verification Module for Quizzer IRC Bot

This module provides multiple admin verification methods:
- NickServ (default, most secure)
- Password-based (works everywhere)
- Hostmask-based (automatic)
- Combined (multiple methods)

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
import logging
import os
import re
import threading
import tempfile
import time
from typing import Dict, List, Optional, Tuple

# Third-party imports
import yaml

# Try to import bcrypt, fall back to hashlib if not available
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

from config import project_path


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HASH_FILE = os.path.join(BASE_DIR, 'admin_passwords.yaml')

# ============================================================================
# Directory Setup
# ============================================================================

os.makedirs(project_path('logs'), exist_ok=True)

# ============================================================================
# Logging Setup
# ============================================================================

verifier_logger = logging.getLogger('AdminVerifier')
verifier_logger.setLevel(logging.INFO)

try:
    file_handler = logging.FileHandler(project_path('logs', 'admin_verification.log'))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    verifier_logger.addHandler(file_handler)
except (OSError, PermissionError) as e:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    verifier_logger.addHandler(console_handler)
    verifier_logger.warning(
        f"Could not create log file '{project_path('logs', 'admin_verification.log')}': {e}. "
        f"Using console logging."
    )


# ============================================================================
# AdminVerifier Class
# ============================================================================


class AdminVerifier:
    """
    Handles admin verification using multiple methods.
    
    Supports:
    - NickServ verification (default)
    - Password-based verification
    - Hostmask-based verification
    - Combined methods
    """
    
    def __init__(
        self,
        admin_nicks: List[str],
        verification_method: str = "nickserv",
        password_settings: Optional[Dict] = None,
        hostmask_settings: Optional[Dict] = None
    ):
        """
        Initialize AdminVerifier.
        
        Args:
            admin_nicks: List of admin nicknames
            verification_method: "nickserv", "password", "hostmask", or "combined"
            password_settings: Dictionary with password configuration
            hostmask_settings: Dictionary with hostmask configuration
        """
        self.admin_nicks = set(nick.lower() for nick in admin_nicks)  # Case-insensitive
        self.verification_method = verification_method.lower()
        self.password_settings = password_settings or {}
        self.hostmask_settings = self._normalize_hostmask_settings(hostmask_settings or {})

        if self.verification_method in ['password', 'combined'] and not HAS_BCRYPT:
            raise RuntimeError(
                "bcrypt is required for password-based admin verification."
            )
        
        # Session management
        self.sessions: Dict[str, float] = {}  # {nick: expiry_time}
        self.session_timeout = self.password_settings.get('session_timeout', 3600)  # 1 hour default
        self._session_lock = threading.Lock()
        
        # Rate limiting for password attempts
        self.failed_attempts: Dict[str, Tuple[int, float]] = {}  # {nick: (count, lockout_until)}
        self.max_attempts = self.password_settings.get('max_attempts', 3)
        self.lockout_duration = self.password_settings.get('lockout_duration', 300)  # 5 minutes
        self._rate_limit_lock = threading.Lock()
        
        # Password storage
        self.password_hashes: Dict[str, str] = {}
        self._load_passwords()

    def _normalize_hostmask_settings(self, hostmask_settings: Dict) -> Dict:
        """Normalize hostmask keys to lowercase for case-insensitive admin matching."""
        normalized = dict(hostmask_settings)
        hostmasks = normalized.get('hostmasks', {})
        normalized['hostmasks'] = {
            str(nick).lower(): patterns
            for nick, patterns in hostmasks.items()
        }
        return normalized
    
    def _load_passwords(self):
        """Load password hashes from files."""
        if self.verification_method not in ['password', 'combined']:
            return
        
        # Load admin passwords from the environment.
        # config.load_env_file() already imports project .env into os.environ, so
        # this supports both real environment variables and a project-local .env.
        env_passwords = {}
        for key, value in os.environ.items():
            if key.startswith('ADMIN_PASSWORD_') and value:
                nick = key.replace('ADMIN_PASSWORD_', '').strip()
                env_passwords[nick.lower()] = value.strip()
        
        # Load from admin_passwords.yaml (hashed)
        hashed_passwords = {}
        if os.path.exists(HASH_FILE):
            try:
                with open(HASH_FILE, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    hashed_passwords = data.get('passwords', {})
            except (OSError, IOError, yaml.YAMLError) as e:
                verifier_logger.warning(f"Could not read {HASH_FILE}: {e}")
        
        # Process passwords: hash plaintext, use existing hashes
        passwords_to_hash = {}
        for nick in self.admin_nicks:
            nick_lower = nick.lower()
            
            # Check if we have a plaintext password in .env
            if nick_lower in env_passwords:
                password = env_passwords[nick_lower]
                
                # Check if already hashed
                if password.startswith('$2b$') or password.startswith('$2a$'):
                    # Already hashed, use it
                    self.password_hashes[nick_lower] = password
                else:
                    # Plaintext, needs hashing
                    passwords_to_hash[nick_lower] = password
                    self.password_hashes[nick_lower] = None  # Placeholder
            
            # Check if we have a hash in admin_passwords.yaml
            elif nick_lower in hashed_passwords:
                self.password_hashes[nick_lower] = hashed_passwords[nick_lower]
        
        # Hash plaintext passwords
        if passwords_to_hash:
            self._hash_and_save_passwords(passwords_to_hash)
    
    def _hash_password(self, plaintext: str) -> str:
        """Hash a plaintext password."""
        if HAS_BCRYPT:
            return bcrypt.hashpw(plaintext.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        raise RuntimeError("bcrypt is required for password hashing.")
    
    def _verify_password(self, plaintext: str, hashed: str) -> bool:
        """Verify a plaintext password against a hash."""
        if not hashed:
            return False
        if HAS_BCRYPT:
            if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
                try:
                    return bcrypt.checkpw(plaintext.encode('utf-8'), hashed.encode('utf-8'))
                except Exception as e:
                    verifier_logger.error(f"Error verifying password: {e}")
                    return False
            else:
                # Old SHA-256 hash, upgrade it
                return False
        raise RuntimeError("bcrypt is required for password verification.")
    
    def _hash_and_save_passwords(self, passwords: Dict[str, str]):
        """Hash plaintext passwords and save to files."""
        if not passwords:
            return
        
        # Hash passwords
        hashed_passwords = {}
        for nick, plaintext in passwords.items():
            hashed = self._hash_password(plaintext)
            hashed_passwords[nick] = hashed
            self.password_hashes[nick] = hashed
        
        # Save to admin_passwords.yaml
        try:
            existing_hashes = {}
            if os.path.exists(HASH_FILE):
                with open(HASH_FILE, 'r', encoding='utf-8') as f:
                    existing_data = yaml.safe_load(f) or {}
                    existing_hashes = existing_data.get('passwords', {})

            existing_hashes.update(hashed_passwords)
            self.password_hashes.update(existing_hashes)
            self.save_password_hashes()
            verifier_logger.info(f"Hashed and saved passwords for {len(hashed_passwords)} admins")
        except (OSError, IOError) as e:
            verifier_logger.error(f"Could not save password hashes: {e}")
        
        # Update .env file (remove plaintext, add comment)
        # Note: We keep .env as-is for user convenience, but log a warning
        verifier_logger.info("Passwords have been hashed. Consider removing plaintext from .env for security.")
    
    def is_admin(self, nick: str) -> bool:
        """Check if nickname is in admin list (case-insensitive)."""
        return nick.lower() in self.admin_nicks
    
    def verify_password(self, nick: str, password: str) -> Tuple[bool, str]:
        """
        Verify password and grant session if correct.
        
        Args:
            nick: Admin nickname
            password: Plaintext password
            
        Returns:
            Tuple of (success, message)
        """
        nick_lower = nick.lower()
        
        # Check if locked out
        with self._rate_limit_lock:
            if nick_lower in self.failed_attempts:
                count, lockout_until = self.failed_attempts[nick_lower]
                if time.time() < lockout_until:
                    remaining = int(lockout_until - time.time())
                    return False, f"Too many failed attempts. Locked out for {remaining} more seconds."
                else:
                    # Lockout expired, reset
                    del self.failed_attempts[nick_lower]
        
        # Check if admin
        if not self.is_admin(nick):
            return False, "You are not an admin."
        
        # Check if password hash exists
        if nick_lower not in self.password_hashes:
            return False, "No password set for this admin. Contact bot owner."
        
        # Verify password
        hashed = self.password_hashes[nick_lower]
        if self._verify_password(password, hashed):
            # Grant session
            expiry = time.time() + self.session_timeout
            
            with self._session_lock:
                self.sessions[nick_lower] = expiry
            
            # Reset failed attempts
            with self._rate_limit_lock:
                if nick_lower in self.failed_attempts:
                    del self.failed_attempts[nick_lower]
            
            verifier_logger.info(f"Password verification successful for {nick}")
            return True, f"Admin verification successful. Session valid for {self.session_timeout // 60} minutes."
        else:
            # Failed attempt
            with self._rate_limit_lock:
                if nick_lower not in self.failed_attempts:
                    self.failed_attempts[nick_lower] = (1, 0)
                else:
                    count, _ = self.failed_attempts[nick_lower]
                    count += 1
                    if count >= self.max_attempts:
                        lockout_until = time.time() + self.lockout_duration
                        self.failed_attempts[nick_lower] = (count, lockout_until)
                        verifier_logger.warning(f"Locked out {nick} after {count} failed attempts")
                    else:
                        self.failed_attempts[nick_lower] = (count, 0)
            
            verifier_logger.warning(f"Failed password verification for {nick}")
            return False, "Incorrect password."
    
    def verify_session(self, nick: str) -> bool:
        """Check if admin has valid session."""
        nick_lower = nick.lower()
        
        with self._session_lock:
            if nick_lower not in self.sessions:
                return False
            
            expiry = self.sessions[nick_lower]
            if time.time() > expiry:
                # Session expired
                del self.sessions[nick_lower]
                return False
            
            return True
    
    def verify_hostmask(self, nick: str, hostmask: str) -> bool:
        """Verify admin by hostmask."""
        if not self.is_admin(nick):
            return False
        
        nick_lower = nick.lower()
        hostmasks = self.hostmask_settings.get('hostmasks', {})
        
        if nick_lower not in hostmasks:
            return False
        
        allowed = hostmasks[nick_lower]
        for pattern in allowed:
            if self._match_hostmask(hostmask, pattern):
                verifier_logger.info(
                    "Hostmask verification successful for %s",
                    nick,
                )
                return True
        
        return False
    
    def _match_hostmask(self, hostmask: str, pattern: str) -> bool:
        """Match hostmask against pattern (supports wildcards)."""
        # Simple wildcard matching: * matches anything
        pattern_parts = pattern.split('!')
        hostmask_parts = hostmask.split('!')
        
        if len(pattern_parts) != len(hostmask_parts):
            return False
        
        for p, h in zip(pattern_parts, hostmask_parts):
            if p == '*':
                continue
            if '*' in p:
                escaped_pattern = re.escape(p).replace(r'\*', '.*')
                if not re.fullmatch(escaped_pattern, h):
                    return False
            elif p != h:
                return False
        
        return True
    
    def verify(self, nick: str, method: Optional[str] = None, 
               password: Optional[str] = None, hostmask: Optional[str] = None) -> bool:
        """
        Verify admin using configured method.
        
        Args:
            nick: Admin nickname
            method: Override verification method
            password: Password (for password method)
            hostmask: Hostmask (for hostmask method)
            
        Returns:
            True if verified, False otherwise
        """
        method = method or self.verification_method
        nick_lower = nick.lower()
        
        if not self.is_admin(nick):
            return False
        
        if method == "nickserv":
            # NickServ verification handled separately in bot.py
            return False  # Indicates NickServ should be used
        
        elif method == "password":
            # Check session first
            if self.verify_session(nick):
                return True
            
            # If password provided, verify it
            if password:
                success, _ = self.verify_password(nick, password)
                return success
            
            return False
        
        elif method == "hostmask":
            if hostmask:
                return self.verify_hostmask(nick, hostmask)
            return False
        
        elif method == "combined":
            # Try password first, then hostmask
            if self.verify_session(nick):
                return True
            
            if password:
                success, _ = self.verify_password(nick, password)
                if success:
                    return True
            
            if hostmask:
                return self.verify_hostmask(nick, hostmask)
            
            return False
        
        return False
    
    def set_password(self, nick: str, new_password: str) -> Tuple[bool, str]:
        """Set or update admin password."""
        if not self.is_admin(nick):
            return False, "You are not an admin."
        
        nick_lower = nick.lower()
        hashed = self._hash_password(new_password)
        self.password_hashes[nick_lower] = hashed
        
        # Save to file
        try:
            self.save_password_hashes()
            verifier_logger.info(f"Password updated for {nick}")
            return True, f"Password updated for {nick}."
        except (OSError, IOError) as e:
            verifier_logger.error(f"Could not save password: {e}")
            return False, f"Error saving password: {e}"

    def save_password_hashes(self):
        """Persist password hashes to disk."""
        data = {'passwords': self.password_hashes}
        directory = os.path.dirname(HASH_FILE) or '.'
        fd, temp_path = tempfile.mkstemp(
            prefix='.admin-passwords.',
            suffix='.yaml.tmp',
            dir=directory,
            text=True,
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                yaml.dump(data, handle, default_flow_style=False, sort_keys=False)
            os.chmod(temp_path, 0o600)
            os.replace(temp_path, HASH_FILE)
        except Exception:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            raise

