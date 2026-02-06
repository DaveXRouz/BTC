"""Tests for the Telegram notification system."""

import unittest
from unittest.mock import patch


class TestNotifier(unittest.TestCase):

    @patch("engines.config.get", return_value="")
    def test_is_configured_false_by_default(self, mock_get):
        """is_configured returns False when chat_id is empty."""
        from engines.notifier import is_configured

        self.assertFalse(is_configured())

    @patch("engines.config.get", return_value="")
    def test_send_fails_silently_when_unconfigured(self, mock_get):
        """send_message returns False when not configured."""
        from engines.notifier import send_message

        result = send_message("test")
        self.assertFalse(result)

    @patch("engines.config.get", return_value="")
    def test_notify_solve_fails_silently(self, mock_get):
        """notify_solve returns False when not configured."""
        from engines.notifier import notify_solve

        result = notify_solve(20, 0xDEADBEEF, "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
        self.assertFalse(result)

    @patch("engines.config.get", return_value="")
    def test_notify_balance_fails_silently(self, mock_get):
        """notify_balance_found returns False when not configured."""
        from engines.notifier import notify_balance_found

        result = notify_balance_found("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 1.0)
        self.assertFalse(result)

    @patch("engines.config.get", return_value="")
    def test_notify_error_fails_silently(self, mock_get):
        """notify_error returns False when not configured."""
        from engines.notifier import notify_error

        result = notify_error("test error", "unit test")
        self.assertFalse(result)

    @patch("engines.config.get", return_value="")
    def test_notify_scanner_hit_fails_silently(self, mock_get):
        """notify_scanner_hit returns False when not configured."""
        from engines.notifier import notify_scanner_hit

        result = notify_scanner_hit(
            {"btc": "1xxx", "eth": "0xxx"}, 123, {"btc": "0.1"}, "test"
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
