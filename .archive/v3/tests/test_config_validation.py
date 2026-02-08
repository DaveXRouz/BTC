"""Tests for expanded config validation."""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

# Ensure project root is on sys.path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import config


class TestConfigValidation(unittest.TestCase):
    """Tests for config.validate() field-specific checks."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_path = os.path.join(self._tmpdir, "config.json")
        # Reset module state
        config._config = None

    def tearDown(self):
        config._config = None
        try:
            os.remove(self._config_path)
        except FileNotFoundError:
            pass
        try:
            os.rmdir(self._tmpdir)
        except OSError:
            pass

    def _load_with(self, overrides):
        """Create a config with overrides, bypassing validate() in load_config.

        Sets _config directly so validate() can be tested independently.
        """
        cfg = copy.deepcopy(config.DEFAULT_CONFIG)
        for key_path, value in overrides.items():
            keys = key_path.split(".")
            current = cfg
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = value
        config._config = cfg

    def test_valid_config_no_warnings_except_empty(self):
        """Default config warns about empty token/chat_id only."""
        self._load_with({})
        warnings = config.validate()
        # Should only have telegram empty warnings
        self.assertTrue(any("bot_token" in w for w in warnings))
        self.assertTrue(any("chat_id" in w for w in warnings))

    def test_malformed_bot_token(self):
        """Malformed bot_token triggers warning and reset."""
        self._load_with({"telegram.bot_token": "short"})
        warnings = config.validate()
        self.assertTrue(any("malformed" in w for w in warnings))
        self.assertEqual(config.get("telegram.bot_token"), "")

    def test_valid_bot_token_no_malformed_warning(self):
        """A properly formatted token should not trigger malformed warning."""
        self._load_with({"telegram.bot_token": "123456789:ABCDEFghijklMNOP"})
        warnings = config.validate()
        self.assertFalse(any("malformed" in w for w in warnings))

    def test_non_numeric_chat_id(self):
        """Non-numeric chat_id triggers reset."""
        self._load_with({"telegram.chat_id": "abc123"})
        warnings = config.validate()
        self.assertTrue(any("numeric" in w for w in warnings))
        self.assertEqual(config.get("telegram.chat_id"), "")

    def test_invalid_batch_size_too_low(self):
        """batch_size below 100 triggers reset."""
        self._load_with({"scanner.batch_size": 10})
        warnings = config.validate()
        self.assertTrue(any("batch_size" in w for w in warnings))
        self.assertEqual(config.get("scanner.batch_size"), 1000)

    def test_invalid_batch_size_too_high(self):
        """batch_size above 100000 triggers reset."""
        self._load_with({"scanner.batch_size": 999999})
        warnings = config.validate()
        self.assertTrue(any("batch_size" in w for w in warnings))
        self.assertEqual(config.get("scanner.batch_size"), 1000)

    def test_invalid_threads(self):
        """threads outside [1,16] triggers reset."""
        self._load_with({"scanner.threads": 32})
        warnings = config.validate()
        self.assertTrue(any("threads" in w for w in warnings))
        self.assertEqual(config.get("scanner.threads"), 1)

    def test_invalid_chains(self):
        """Invalid chain names get removed."""
        self._load_with({"scanner.chains": ["btc", "solana", "eth"]})
        warnings = config.validate()
        self.assertTrue(any("Invalid chain" in w for w in warnings))
        chains = config.get("scanner.chains")
        self.assertIn("btc", chains)
        self.assertIn("eth", chains)
        self.assertNotIn("solana", chains)

    def test_invalid_check_every_n(self):
        """check_every_n outside range triggers reset."""
        self._load_with({"scanner.check_every_n": 50})
        warnings = config.validate()
        self.assertTrue(any("check_every_n" in w for w in warnings))
        self.assertEqual(config.get("scanner.check_every_n"), 5000)

    def test_invalid_status_interval(self):
        """status_interval_hours outside [1,168] triggers reset."""
        self._load_with({"headless.status_interval_hours": 0})
        warnings = config.validate()
        self.assertTrue(any("status_interval" in w for w in warnings))
        self.assertEqual(config.get("headless.status_interval_hours"), 24)

    def test_negative_chat_id_valid(self):
        """Negative chat_id (group chat) should be valid."""
        self._load_with({"telegram.chat_id": "-123456"})
        warnings = config.validate()
        self.assertFalse(any("numeric" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
