"""Battle tests for engines.security module.

Stress-tests encryption edge cases: huge payloads, IV uniqueness,
salt corruption recovery, unicode extremes, concurrency, password
changes, tamper detection, and dict encryption with nested structures.
"""

import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import security


class TestSecurityBattle(unittest.TestCase):
    """Battle-hardened tests for the security module."""

    def setUp(self):
        """Reset security state and redirect salt file to temp dir."""
        security.reset()
        self._orig_data_dir = security.DATA_DIR
        self._orig_salt_file = security.SALT_FILE
        self._tmpdir = tempfile.mkdtemp()
        security.DATA_DIR = security.Path(self._tmpdir)
        security.SALT_FILE = security.Path(self._tmpdir) / ".vault_salt"

    def tearDown(self):
        """Restore original paths and clean up."""
        security.DATA_DIR = self._orig_data_dir
        security.SALT_FILE = self._orig_salt_file
        security.reset()
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ---- 1. Empty string roundtrip ----

    def test_encrypt_empty_string(self):
        """Encrypt and decrypt an empty string preserves emptiness."""
        security.set_master_password("battle-pass")
        encrypted = security.encrypt("")
        self.assertTrue(encrypted.startswith("ENC:"))
        self.assertNotEqual(encrypted, "ENC:")  # has nonce + tag even for empty
        decrypted = security.decrypt(encrypted)
        self.assertEqual(decrypted, "")

    # ---- 2. Huge payload ----

    def test_encrypt_huge_payload(self):
        """100 KB plaintext roundtrip succeeds without data loss."""
        security.set_master_password("big-data-pass")
        plaintext = "A" * 102_400  # 100 KB
        encrypted = security.encrypt(plaintext)
        self.assertTrue(encrypted.startswith("ENC:"))
        decrypted = security.decrypt(encrypted)
        self.assertEqual(len(decrypted), 102_400)
        self.assertEqual(decrypted, plaintext)

    # ---- 3. IV / nonce uniqueness ----

    def test_iv_uniqueness(self):
        """Encrypting the same text 100 times produces 100 distinct ciphertexts."""
        security.set_master_password("nonce-test")
        ciphertexts = set()
        for _ in range(100):
            ct = security.encrypt("identical plaintext")
            ciphertexts.add(ct)
        self.assertEqual(
            len(ciphertexts), 100, "All 100 encryptions must produce unique ciphertexts"
        )

    # ---- 4. Salt creation and persistence ----

    def test_salt_creation_and_persistence(self):
        """Setting a password creates the salt file; salt survives module reset."""
        salt_path = security.SALT_FILE
        self.assertFalse(salt_path.exists())

        security.set_master_password("persist-pass")
        self.assertTrue(salt_path.exists())
        salt_bytes = salt_path.read_bytes()
        self.assertEqual(len(salt_bytes), 32)

        # Reset module state (simulates app restart) but keep the file
        security.reset()
        # Re-read: the file should still be there with the same salt
        self.assertTrue(salt_path.exists())
        self.assertEqual(salt_path.read_bytes(), salt_bytes)

    # ---- 5. Salt corruption recovery ----

    def test_salt_corruption_recovery(self):
        """Corrupted salt file is overwritten with a fresh salt on next password set."""
        salt_path = security.SALT_FILE
        salt_path.parent.mkdir(parents=True, exist_ok=True)
        # Write garbage (wrong length)
        salt_path.write_bytes(b"corrupt")

        # set_master_password should still succeed -- _load_or_create_salt
        # reads whatever bytes are there (even short), derives a key, and
        # proceeds. The key will be based on the corrupt salt, but the call
        # itself must not crash.
        result = security.set_master_password("recovery-pass")
        self.assertTrue(result)
        self.assertTrue(security.is_encrypted_mode())

        # Encrypt/decrypt must still roundtrip with the (corrupt-salt) key
        enc = security.encrypt("test-data")
        self.assertEqual(security.decrypt(enc), "test-data")

    # ---- 6. Unicode password ----

    def test_unicode_password(self):
        """Unicode password (Chinese, Arabic, emoji) works for encrypt/decrypt."""
        unicode_pw = "\u5bc6\u7801\u0643\u0644\u0645\u0629 \u0627\u0644\u0633\u0631\U0001f512\U0001f511"
        security.set_master_password(unicode_pw)
        self.assertTrue(security.is_encrypted_mode())
        encrypted = security.encrypt("secret with unicode pw")
        decrypted = security.decrypt(encrypted)
        self.assertEqual(decrypted, "secret with unicode pw")

    # ---- 7. Unicode plaintext ----

    def test_unicode_plaintext(self):
        """Full Unicode spectrum in plaintext survives encrypt/decrypt."""
        security.set_master_password("plain-unicode")
        # Chinese, Arabic, emoji, accented, Cyrillic, math symbols
        plaintext = (
            "\u4f60\u597d\u4e16\u754c "
            "\u0645\u0631\u062d\u0628\u0627 "
            "\U0001f600\U0001f680\U0001f30d "
            "\u00e9\u00e8\u00ea\u00eb "
            "\u041f\u0440\u0438\u0432\u0435\u0442 "
            "\u2200x\u2208\u211d: x\u00b2\u22650"
        )
        encrypted = security.encrypt(plaintext)
        self.assertEqual(security.decrypt(encrypted), plaintext)

    # ---- 8. Double set password ----

    def test_double_set_password(self):
        """Second call to set_master_password returns False, key unchanged."""
        self.assertTrue(security.set_master_password("first"))
        encrypted = security.encrypt("data-under-first")

        self.assertFalse(security.set_master_password("second"))
        # Key should still be the first one -- decrypt must work
        self.assertEqual(security.decrypt(encrypted), "data-under-first")

    # ---- 9. Decrypt without password ----

    def test_decrypt_without_password(self):
        """Decrypting ENC: data after reset (no password) raises ValueError."""
        security.set_master_password("temp-pass")
        encrypted = security.encrypt("classified")
        self.assertTrue(encrypted.startswith("ENC:"))

        security.reset()
        # No password set now
        self.assertFalse(security.is_encrypted_mode())
        with self.assertRaises(ValueError) as ctx:
            security.decrypt(encrypted)
        self.assertIn("No master password", str(ctx.exception))

    # ---- 10. Wrong password decrypt ----

    def test_wrong_password_decrypt(self):
        """Encrypt with pw1, reset, set pw2 -- decrypt raises ValueError (tampered)."""
        security.set_master_password("password-one")
        encrypted = security.encrypt("top secret")

        # Reset and set a different password with a different salt
        security.reset()
        # Remove old salt so a new one is generated
        if security.SALT_FILE.exists():
            security.SALT_FILE.unlink()
        security.set_master_password("password-two")

        with self.assertRaises(ValueError):
            security.decrypt(encrypted)

    # ---- 11. Tampered ciphertext ----

    def test_tampered_ciphertext(self):
        """Flipping a byte in the ciphertext body triggers auth tag failure."""
        security.set_master_password("tamper-test")
        encrypted = security.encrypt("integrity check")
        hex_payload = encrypted[4:]  # strip "ENC:"
        raw = bytearray(bytes.fromhex(hex_payload))

        # Flip a byte in the ciphertext region (between nonce and auth tag)
        if len(raw) > 32:
            # Ciphertext starts at byte 16, auth tag is last 16 bytes
            target = 16 + (len(raw) - 32) // 2  # middle of ciphertext
            raw[target] ^= 0xFF
        else:
            # Edge case: very short, flip in nonce area
            raw[0] ^= 0xFF

        tampered = "ENC:" + bytes(raw).hex()
        with self.assertRaises(ValueError) as ctx:
            security.decrypt(tampered)
        self.assertIn("tampered", str(ctx.exception).lower())

    # ---- 12. No password -> PLAIN prefix ----

    def test_encrypt_no_password_returns_plain(self):
        """Without a password set, encrypt returns PLAIN: prefix."""
        self.assertFalse(security.is_encrypted_mode())
        result = security.encrypt("open data")
        self.assertTrue(result.startswith("PLAIN:"))
        self.assertEqual(result, "PLAIN:open data")

    # ---- 13. PLAIN prefix decrypts without password ----

    def test_decrypt_plain_prefix(self):
        """PLAIN: prefixed strings decrypt without needing a password."""
        self.assertFalse(security.is_encrypted_mode())
        decrypted = security.decrypt("PLAIN:hello world")
        self.assertEqual(decrypted, "hello world")

        # Also works when a password IS set
        security.set_master_password("some-pass")
        decrypted2 = security.decrypt("PLAIN:still works")
        self.assertEqual(decrypted2, "still works")

    # ---- 14. Nested dict encryption ----

    def test_encrypt_dict_nested(self):
        """encrypt_dict recurses into nested dicts and encrypts sensitive keys."""
        security.set_master_password("dict-pass")
        data = {
            "address": "1ABC...",
            "private_key": "5Jxyz...",
            "details": {
                "seed_phrase": "abandon abandon ...",
                "label": "my wallet",
                "inner": {
                    "wif": "KwDiBf...",
                    "extended_private_key": "xprv9s21...",
                    "note": "safe",
                },
            },
            "balance": 0.5,
        }
        encrypted = security.encrypt_dict(data)

        # Top-level sensitive key encrypted
        self.assertTrue(encrypted["private_key"].startswith("ENC:"))
        # Non-sensitive top-level key unchanged
        self.assertEqual(encrypted["address"], "1ABC...")
        self.assertEqual(encrypted["balance"], 0.5)

        # Nested sensitive keys encrypted
        self.assertTrue(encrypted["details"]["seed_phrase"].startswith("ENC:"))
        self.assertEqual(encrypted["details"]["label"], "my wallet")
        self.assertTrue(encrypted["details"]["inner"]["wif"].startswith("ENC:"))
        self.assertTrue(
            encrypted["details"]["inner"]["extended_private_key"].startswith("ENC:")
        )
        self.assertEqual(encrypted["details"]["inner"]["note"], "safe")

        # Full roundtrip
        decrypted = security.decrypt_dict(encrypted)
        self.assertEqual(decrypted["private_key"], "5Jxyz...")
        self.assertEqual(decrypted["details"]["seed_phrase"], "abandon abandon ...")
        self.assertEqual(decrypted["details"]["inner"]["wif"], "KwDiBf...")
        self.assertEqual(
            decrypted["details"]["inner"]["extended_private_key"], "xprv9s21..."
        )

    # ---- 15. Non-string sensitive values are NOT encrypted ----

    def test_encrypt_dict_non_string_values(self):
        """Non-string values for sensitive keys are left untouched."""
        security.set_master_password("dict-types")
        data = {
            "private_key": 12345,
            "seed_phrase": None,
            "wif": ["a", "b"],
            "extended_private_key": {"nested": True},
            "normal_key": "normal_value",
        }
        encrypted = security.encrypt_dict(data)

        # Non-string sensitive values pass through unchanged
        self.assertEqual(encrypted["private_key"], 12345)
        self.assertIsNone(encrypted["seed_phrase"])
        self.assertEqual(encrypted["wif"], ["a", "b"])
        # dict value for sensitive key: encrypt_dict recurses into it,
        # but "nested" is not a sensitive key, so it stays unchanged
        self.assertEqual(encrypted["extended_private_key"], {"nested": True})
        self.assertEqual(encrypted["normal_key"], "normal_value")

    # ---- 16. Change password with wrong old password ----

    def test_change_password_wrong_old(self):
        """change_master_password with incorrect old password raises ValueError."""
        security.set_master_password("original")
        with self.assertRaises(ValueError) as ctx:
            security.change_master_password("WRONG-old", "new-pass")
        self.assertIn("incorrect", str(ctx.exception).lower())
        # Original key should still work
        enc = security.encrypt("still alive")
        self.assertEqual(security.decrypt(enc), "still alive")

    # ---- 17. Change password success ----

    def test_change_password_success(self):
        """After changing password, old ciphertexts fail and new ones succeed."""
        security.set_master_password("old-pass")
        old_encrypted = security.encrypt("old-era data")

        # Change password
        result = security.change_master_password("old-pass", "new-pass")
        self.assertTrue(result)

        # Old ciphertext should fail (different salt + key now)
        with self.assertRaises(ValueError):
            security.decrypt(old_encrypted)

        # New encryption works
        new_encrypted = security.encrypt("new-era data")
        self.assertEqual(security.decrypt(new_encrypted), "new-era data")

    # ---- 18. Concurrent encryption ----

    def test_concurrent_encrypt(self):
        """20 threads encrypting simultaneously all produce valid ciphertexts."""
        security.set_master_password("thread-safe")
        results = {}
        errors = []

        def worker(thread_id):
            try:
                plaintext = f"thread-{thread_id}-payload"
                encrypted = security.encrypt(plaintext)
                results[thread_id] = (plaintext, encrypted)
            except Exception as e:
                errors.append((thread_id, e))

        threads = []
        for i in range(20):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(len(errors), 0, f"Threads raised errors: {errors}")
        self.assertEqual(len(results), 20, "All 20 threads must produce results")

        # Verify every ciphertext decrypts to the correct plaintext
        for thread_id, (plaintext, encrypted) in results.items():
            self.assertTrue(
                encrypted.startswith("ENC:"),
                f"Thread {thread_id} didn't produce ENC: prefix",
            )
            decrypted = security.decrypt(encrypted)
            self.assertEqual(
                decrypted, plaintext, f"Thread {thread_id} roundtrip failed"
            )

        # All ciphertexts should be unique (different nonces)
        all_cts = [ct for _, ct in results.values()]
        self.assertEqual(len(set(all_cts)), 20, "All 20 ciphertexts must be unique")


if __name__ == "__main__":
    unittest.main()
