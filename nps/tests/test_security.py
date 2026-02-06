"""Tests for engines.security module."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import security


class TestSecurity(unittest.TestCase):

    def setUp(self):
        """Reset security module state before each test."""
        security.reset()
        # Use a temp dir for salt file
        self._orig_salt_file = security.SALT_FILE
        self._tmpdir = tempfile.mkdtemp()
        security.SALT_FILE = security.Path(self._tmpdir) / ".vault_salt"

    def tearDown(self):
        """Restore original salt path."""
        security.SALT_FILE = self._orig_salt_file
        security.reset()
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_set_master_password(self):
        """set_master_password returns True on first call."""
        self.assertTrue(security.set_master_password("testpass"))
        self.assertTrue(security.is_encrypted_mode())

    def test_set_master_password_twice_fails(self):
        """set_master_password returns False on second call."""
        security.set_master_password("testpass")
        self.assertFalse(security.set_master_password("testpass2"))

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt then decrypt returns original text."""
        security.set_master_password("mypassword")
        original = "Hello World 123 !@# sensitive_data"
        encrypted = security.encrypt(original)
        self.assertTrue(encrypted.startswith("ENC:"))
        decrypted = security.decrypt(encrypted)
        self.assertEqual(decrypted, original)

    def test_plain_prefix_without_password(self):
        """Without password, encrypt returns PLAIN: prefix."""
        result = security.encrypt("hello")
        self.assertTrue(result.startswith("PLAIN:"))
        self.assertEqual(security.decrypt(result), "hello")

    def test_wrong_password_raises(self):
        """Decrypting with wrong key raises ValueError."""
        security.set_master_password("correct_password")
        encrypted = security.encrypt("secret data")

        # Reset and set a different password
        security.reset()
        security.SALT_FILE = security.Path(self._tmpdir) / ".vault_salt"
        # Need to create new salt for different key
        security._salt = os.urandom(32)
        security._master_key = security._derive_key("wrong_password", security._salt)

        with self.assertRaises(ValueError):
            security.decrypt(encrypted)

    def test_dict_encryption(self):
        """encrypt_dict encrypts only sensitive keys."""
        security.set_master_password("testpass")
        data = {
            "address": "1A1zP1...",
            "private_key": "5HueCGU...",
            "balance": 1.5,
        }
        encrypted = security.encrypt_dict(data)
        self.assertEqual(encrypted["address"], "1A1zP1...")
        self.assertTrue(encrypted["private_key"].startswith("ENC:"))
        self.assertEqual(encrypted["balance"], 1.5)

        decrypted = security.decrypt_dict(encrypted)
        self.assertEqual(decrypted["private_key"], "5HueCGU...")

    def test_empty_string(self):
        """Encrypt/decrypt handles empty strings."""
        security.set_master_password("testpass")
        encrypted = security.encrypt("")
        self.assertEqual(security.decrypt(encrypted), "")

    def test_unicode_string(self):
        """Encrypt/decrypt handles unicode."""
        security.set_master_password("testpass")
        original = "Hello \u4e16\u754c \U0001f600 \u00e9\u00e8\u00ea"
        encrypted = security.encrypt(original)
        self.assertEqual(security.decrypt(encrypted), original)

    def test_tamper_detection(self):
        """Modifying ciphertext raises ValueError."""
        security.set_master_password("testpass")
        encrypted = security.encrypt("secret")
        # Tamper with the hex payload
        hex_payload = encrypted[4:]
        tampered = list(bytes.fromhex(hex_payload))
        tampered[20] ^= 0xFF  # flip a byte in the ciphertext
        tampered_str = "ENC:" + bytes(tampered).hex()
        with self.assertRaises(ValueError):
            security.decrypt(tampered_str)

    def test_env_var_priority(self):
        """get_env_or_config returns env var when set."""
        os.environ["NPS_BOT_TOKEN"] = "env_token_123"
        try:
            result = security.get_env_or_config("bot_token", "config_token")
            self.assertEqual(result, "env_token_123")
        finally:
            del os.environ["NPS_BOT_TOKEN"]

    def test_env_var_fallback(self):
        """get_env_or_config falls back to config value."""
        os.environ.pop("NPS_TEST_KEY", None)
        result = security.get_env_or_config("test_key", "config_value")
        self.assertEqual(result, "config_value")

    def test_legacy_data_passthrough(self):
        """Data without PLAIN: or ENC: prefix is returned as-is."""
        result = security.decrypt("some_legacy_data")
        self.assertEqual(result, "some_legacy_data")

    def test_has_salt(self):
        """has_salt returns False before and True after setting password."""
        self.assertFalse(security.has_salt())
        security.set_master_password("testpass")
        self.assertTrue(security.has_salt())


if __name__ == "__main__":
    unittest.main()
