"""
Live Telegram integration tests — only run when NPS_BOT_TOKEN and NPS_CHAT_ID
environment variables are set.

Wave 6: ~8 tests.

All tests are skipped when credentials are absent, so the test file is safe
to include in CI and local runs without side effects.
"""

import os
import sys
import unittest
from pathlib import Path

# Allow imports from the nps package
sys.path.insert(0, str(Path(__file__).parent.parent))

_HAS_CREDS = bool(os.environ.get("NPS_BOT_TOKEN") and os.environ.get("NPS_CHAT_ID"))


def _setup_config():
    """Inject env-var credentials into the NPS config system so notifier
    sees them via ``config.get()``."""
    from engines import config as cfg

    cfg.load()
    cfg.set("telegram.bot_token", os.environ["NPS_BOT_TOKEN"])
    cfg.set("telegram.chat_id", os.environ["NPS_CHAT_ID"])
    cfg.set("telegram.enabled", True)


@unittest.skipUnless(
    _HAS_CREDS, "No Telegram credentials (NPS_BOT_TOKEN / NPS_CHAT_ID)"
)
class TestTelegramLive(unittest.TestCase):
    """Live Telegram tests — require real bot token + chat id."""

    @classmethod
    def setUpClass(cls):
        _setup_config()
        from engines import notifier  # noqa: F401

        cls.notifier = notifier

    # ------------------------------------------------------------------
    # 1. Configuration
    # ------------------------------------------------------------------

    def test_is_configured(self):
        """With token + chat_id set, is_configured() returns True."""
        self.assertTrue(self.notifier.is_configured())

    # ------------------------------------------------------------------
    # 2. Send message
    # ------------------------------------------------------------------

    def test_send_message(self):
        """send_message delivers a test message and returns True."""
        result = self.notifier.send_message(
            "<b>NPS Test</b>\nAutomated test message from test_telegram_live.py"
        )
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # 3. Dispatch /help command
    # ------------------------------------------------------------------

    def test_dispatch_help_command(self):
        """dispatch_command('/help') returns a non-empty string."""
        result = self.notifier.dispatch_command("/help")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    # ------------------------------------------------------------------
    # 4. Dispatch /status command
    # ------------------------------------------------------------------

    def test_dispatch_status_command(self):
        """dispatch_command('/status') returns a string containing 'Status'."""
        result = self.notifier.dispatch_command("/status")
        self.assertIsInstance(result, str)
        self.assertIn("Status", result)

    # ------------------------------------------------------------------
    # 5. Daily status notification
    # ------------------------------------------------------------------

    def test_notify_daily_status(self):
        """notify_daily_status with mock stats returns True."""
        mock_stats = {
            "keys_tested": 1000,
            "seeds_tested": 500,
            "online_checks": 200,
            "hits": 0,
            "uptime": "0h 1m",
        }
        result = self.notifier.notify_daily_status(mock_stats)
        self.assertTrue(result)

    # ------------------------------------------------------------------
    # 6. Format balance hit (template — no send)
    # ------------------------------------------------------------------

    def test_format_balance_hit(self):
        """_format_balance_hit returns an HTML string."""
        data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "balance": 0.001,
            "chain": "BTC",
            "method": "random",
        }
        result = self.notifier._format_balance_hit(data)
        self.assertIsInstance(result, str)
        self.assertIn("Balance Hit", result)
        self.assertIn("BTC", result)

    # ------------------------------------------------------------------
    # 7. Format daily report (template — no send)
    # ------------------------------------------------------------------

    def test_format_daily_report(self):
        """_format_daily_report returns an HTML string."""
        stats = {
            "keys_tested": 5000,
            "seeds_tested": 1000,
            "hits": 0,
            "uptime": "2h 30m",
            "speed": 450,
            "terminals": 2,
        }
        result = self.notifier._format_daily_report(stats)
        self.assertIsInstance(result, str)
        self.assertIn("Daily Report", result)

    # ------------------------------------------------------------------
    # 8. process_telegram_command
    # ------------------------------------------------------------------

    def test_process_telegram_command(self):
        """process_telegram_command('/help') returns a non-empty string."""
        result = self.notifier.process_telegram_command("/help")
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
