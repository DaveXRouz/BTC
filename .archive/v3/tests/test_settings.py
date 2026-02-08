"""Tests for Phase 7: Settings & Connections."""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestConfigSave(unittest.TestCase):
    """Test config save and reset functions."""

    def test_save_config_updates_merges(self):
        """save_config_updates merges into existing config."""
        from engines.config import load_config, save_config_updates, get

        load_config()
        save_config_updates({"test_section": {"key1": "value1"}})
        val = get("test_section.key1", "missing")
        self.assertEqual(val, "value1")

    def test_reset_defaults_restores(self):
        """reset_defaults restores config to default state."""
        from engines.config import load_config, save_config_updates, reset_defaults, get

        load_config()
        save_config_updates({"test_reset": {"x": 42}})
        reset_defaults()
        val = get("test_reset.x", "gone")
        self.assertEqual(val, "gone")

    def test_get_config_path_returns_string(self):
        """get_config_path returns a non-empty string."""
        from engines.config import get_config_path

        path = get_config_path()
        self.assertIsInstance(path, str)
        self.assertTrue(len(path) > 0)


class TestTelegramDispatch(unittest.TestCase):
    """Test Telegram command dispatch returns valid responses."""

    def test_help_returns_commands(self):
        """process_telegram_command('/help') lists commands."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/help")
        self.assertIn("Command Reference", result)
        self.assertIn("/status", result)

    def test_status_returns_nonempty(self):
        """process_telegram_command('/status') returns a response."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/status")
        self.assertTrue(len(result) > 0)

    def test_vault_returns_nonempty(self):
        """process_telegram_command('/vault') returns a response."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/vault")
        self.assertTrue(len(result) > 0)

    def test_terminals_returns_nonempty(self):
        """process_telegram_command('/terminals') returns a response."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/terminals")
        self.assertTrue(len(result) > 0)

    def test_memory_returns_nonempty(self):
        """process_telegram_command('/memory') returns a response."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/memory")
        self.assertTrue(len(result) > 0)

    def test_unknown_command(self):
        """process_telegram_command with unknown command returns error."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/nonexistent")
        self.assertIn("Unknown command", result)

    def test_all_commands_return_nonempty(self):
        """Every registered command returns a non-empty string."""
        from engines.notifier import process_telegram_command, COMMANDS

        for cmd in COMMANDS:
            result = process_telegram_command(cmd)
            self.assertTrue(len(result) > 0, f"Command {cmd} returned empty response")


class TestSettingsTabInit(unittest.TestCase):
    """Test SettingsTab can be imported."""

    def test_settings_tab_importable(self):
        """SettingsTab class can be imported."""
        from gui.settings_tab import SettingsTab

        self.assertTrue(callable(SettingsTab))


if __name__ == "__main__":
    unittest.main()
