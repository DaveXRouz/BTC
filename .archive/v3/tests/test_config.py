"""Tests for the centralized config system."""

import json
import os
import tempfile
import unittest
from pathlib import Path


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.tmpdir.name) / "config.json"
        # Reset module state
        import engines.config as cfg

        cfg._config = None
        self._cfg = cfg

    def tearDown(self):
        self.tmpdir.cleanup()
        self._cfg._config = None

    def test_load_creates_default(self):
        """Loading from non-existent file creates it with defaults."""
        self.assertFalse(self.config_path.exists())
        config = self._cfg.load_config(path=self.config_path)
        self.assertTrue(self.config_path.exists())
        self.assertIn("telegram", config)
        self.assertIn("scanner", config)

    def test_get_dot_notation(self):
        """Dot-notation get retrieves nested values."""
        self._cfg.load_config(path=self.config_path)
        token = self._cfg.get("telegram.bot_token")
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

    def test_set_persists(self):
        """Set writes to file and is retrievable."""
        self._cfg.load_config(path=self.config_path)
        self._cfg.set("telegram.chat_id", "12345", path=self.config_path)
        self.assertEqual(self._cfg.get("telegram.chat_id"), "12345")
        # Verify it's on disk
        with open(self.config_path) as f:
            data = json.load(f)
        self.assertEqual(data["telegram"]["chat_id"], "12345")

    def test_missing_key_returns_default(self):
        """Missing key returns default value."""
        self._cfg.load_config(path=self.config_path)
        result = self._cfg.get("nonexistent.key", "fallback")
        self.assertEqual(result, "fallback")

    def test_validate_warns_empty_chat_id(self):
        """Validate warns when chat_id is empty."""
        self._cfg.load_config(path=self.config_path)
        warnings = self._cfg.validate()
        self.assertTrue(any("chat_id" in w for w in warnings))

    def test_deep_merge_preserves_custom_values(self):
        """Custom values in file are preserved, missing keys filled from defaults."""
        custom = {"telegram": {"bot_token": "123456789012345678901:ABCtoken"}}
        with open(self.config_path, "w") as f:
            json.dump(custom, f)
        config = self._cfg.load_config(path=self.config_path)
        self.assertEqual(
            config["telegram"]["bot_token"], "123456789012345678901:ABCtoken"
        )
        # scanner section should come from defaults
        self.assertIn("scanner", config)
        self.assertEqual(config["scanner"]["batch_size"], 1000)


if __name__ == "__main__":
    unittest.main()
