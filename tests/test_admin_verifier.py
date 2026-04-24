import os
import stat
import tempfile
import unittest
from unittest.mock import patch

import admin_verifier as admin_verifier_module
from admin_verifier import AdminVerifier


class AdminVerifierTests(unittest.TestCase):
    def test_hostmask_lookup_is_case_insensitive_for_configured_nicks(self):
        verifier = AdminVerifier(
            admin_nicks=["BlackRoot"],
            verification_method="hostmask",
            hostmask_settings={
                "hostmasks": {
                    "BlackRoot": ["*!*@trusted.host"]
                }
            },
        )

        self.assertTrue(
            verifier.verify_hostmask("blackroot", "blackroot!user@trusted.host")
        )

    def test_password_modes_require_bcrypt(self):
        with patch.object(admin_verifier_module, "HAS_BCRYPT", False):
            with self.assertRaises(RuntimeError):
                AdminVerifier(
                    admin_nicks=["BlackRoot"],
                    verification_method="password",
                )

    def test_passwords_load_from_environment(self):
        with patch.dict(
            admin_verifier_module.os.environ,
            {"ADMIN_PASSWORD_BLACKROOT": "secret"},
            clear=False,
        ):
            verifier = AdminVerifier(
                admin_nicks=["BlackRoot"],
                verification_method="password",
            )

        success, _ = verifier.verify_password("blackroot", "secret")
        self.assertTrue(success)

    def test_save_password_hashes_writes_file_atomically_with_secure_permissions(self):
        verifier = AdminVerifier(
            admin_nicks=["BlackRoot"],
            verification_method="hostmask",
        )
        verifier.password_hashes = {"blackroot": "$2b$fakehash"}

        with tempfile.TemporaryDirectory() as tempdir:
            hash_path = os.path.join(tempdir, "admin_passwords.yaml")
            with patch.object(admin_verifier_module, "HASH_FILE", hash_path):
                verifier.save_password_hashes()

            with open(hash_path, "r", encoding="utf-8") as handle:
                contents = handle.read()

            self.assertIn("blackroot", contents)
            self.assertEqual(
                stat.S_IMODE(os.stat(hash_path).st_mode),
                0o600,
            )


if __name__ == "__main__":
    unittest.main()
