"""Battle tests for the Telegram notification system (engines/notifier.py).

These tests exercise edge cases and adversarial scenarios:
- Command registry completeness
- Dispatch with various inputs
- Bot health state machine (disable / re-enable)
- Rate limiting via consecutive failures
- Message truncation for oversized payloads
- Notification template HTML structure
- Callback routing through the menu system
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the nps package root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import notifier


def _reset_bot_state():
    """Reset all mutable module-level bot state to pristine defaults."""
    notifier._consecutive_failures = 0
    notifier._bot_disabled = False
    notifier._error_count = 0
    notifier._last_send_time = 0


class TestNotifierBattle(unittest.TestCase):
    """Battle tests targeting robustness of the notifier module."""

    def setUp(self):
        """Capture original state so tearDown can restore it."""
        self._orig_failures = notifier._consecutive_failures
        self._orig_disabled = notifier._bot_disabled
        self._orig_error_count = notifier._error_count
        self._orig_last_send = notifier._last_send_time

    def tearDown(self):
        """Restore module state to avoid polluting other tests."""
        notifier._consecutive_failures = self._orig_failures
        notifier._bot_disabled = self._orig_disabled
        notifier._error_count = self._orig_error_count
        notifier._last_send_time = self._orig_last_send

    # ----------------------------------------------------------------
    # 1. All COMMANDS keys present in the command registry
    # ----------------------------------------------------------------
    def test_all_commands_registered(self):
        """Every key in the public COMMANDS dict must have a handler in _command_registry."""
        missing = []
        for cmd_name in notifier.COMMANDS:
            if cmd_name.lower() not in notifier._command_registry:
                missing.append(cmd_name)
        self.assertEqual(
            missing,
            [],
            f"Commands missing from _command_registry: {missing}",
        )

    # ----------------------------------------------------------------
    # 2. /help dispatch returns "Command Reference"
    # ----------------------------------------------------------------
    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_help(self, _mock_btn, _mock_send):
        """dispatch_command('/help') must return text containing 'Command Reference'."""
        result = notifier.dispatch_command("/help")
        self.assertIsInstance(result, str)
        self.assertIn("Command Reference", result)

    # ----------------------------------------------------------------
    # 3. /status dispatch returns "Status"
    # ----------------------------------------------------------------
    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_status(self, _mock_btn, _mock_send):
        """dispatch_command('/status') must return text containing 'Status'."""
        result = notifier.dispatch_command("/status")
        self.assertIsInstance(result, str)
        self.assertIn("Status", result)

    # ----------------------------------------------------------------
    # 4. Unknown command returns "Unknown command"
    # ----------------------------------------------------------------
    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_unknown_command(self, _mock_btn, _mock_send):
        """dispatch_command('/foobar') must return 'Unknown command'."""
        result = notifier.dispatch_command("/foobar")
        self.assertIsInstance(result, str)
        self.assertIn("Unknown command", result)

    # ----------------------------------------------------------------
    # 5. /sign with arguments passes args to the handler
    # ----------------------------------------------------------------
    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_with_args(self, _mock_btn, _mock_send):
        """dispatch_command('/sign hello world') must forward 'hello world' as the arg."""
        # Temporarily replace the /sign handler to capture the arg it receives
        original_handler = notifier._command_registry["/sign"]["handler"]
        captured_args = []

        def _spy_handler(arg, app_controller):
            captured_args.append(arg)
            return original_handler(arg, app_controller)

        notifier._command_registry["/sign"]["handler"] = _spy_handler
        try:
            result = notifier.dispatch_command("/sign hello world")
            self.assertEqual(len(captured_args), 1)
            self.assertEqual(captured_args[0], "hello world")
            # The result should NOT be the "Usage" hint because we supplied an arg
            self.assertNotIn("Usage", result)
        finally:
            notifier._command_registry["/sign"]["handler"] = original_handler

    # ----------------------------------------------------------------
    # 6. _record_failure 5 times triggers _bot_disabled
    # ----------------------------------------------------------------
    def test_rate_limiting_mock(self):
        """Calling _record_failure 5 times must set _bot_disabled to True."""
        _reset_bot_state()
        self.assertFalse(notifier._bot_disabled)

        for i in range(notifier._BOT_DISABLE_THRESHOLD):
            notifier._record_failure()

        self.assertTrue(notifier._bot_disabled)
        self.assertEqual(
            notifier._consecutive_failures, notifier._BOT_DISABLE_THRESHOLD
        )

    # ----------------------------------------------------------------
    # 7. After 5 consecutive failures, is_bot_healthy() returns False
    # ----------------------------------------------------------------
    def test_health_auto_disable(self):
        """After _BOT_DISABLE_THRESHOLD consecutive failures, is_bot_healthy() returns False."""
        _reset_bot_state()
        self.assertTrue(notifier.is_bot_healthy())

        for _ in range(notifier._BOT_DISABLE_THRESHOLD):
            notifier._record_failure()

        self.assertFalse(notifier.is_bot_healthy())

    # ----------------------------------------------------------------
    # 8. Disable then _record_success re-enables
    # ----------------------------------------------------------------
    def test_health_re_enable(self):
        """A single _record_success after auto-disable must re-enable the bot."""
        _reset_bot_state()

        # Force disable
        for _ in range(notifier._BOT_DISABLE_THRESHOLD):
            notifier._record_failure()
        self.assertFalse(notifier.is_bot_healthy())

        # Single success should re-enable
        notifier._record_success()
        self.assertTrue(notifier.is_bot_healthy())
        self.assertEqual(notifier._consecutive_failures, 0)

    # ----------------------------------------------------------------
    # 9. 10 KB message gets truncated to _MAX_MESSAGE_LENGTH
    # ----------------------------------------------------------------
    @patch("engines.notifier.is_configured", return_value=True)
    @patch("urllib.request.urlopen")
    def test_message_truncation(self, mock_urlopen, _mock_cfg):
        """A message exceeding _MAX_MESSAGE_LENGTH must be truncated before sending."""
        _reset_bot_state()

        # Build a message well over the limit (10 KB)
        huge_message = "X" * 10_000
        self.assertGreater(len(huge_message), notifier._MAX_MESSAGE_LENGTH)

        # Mock config.get to return a test token and chat_id
        def fake_config_get(key, default=""):
            mapping = {
                "telegram.bot_token": "TEST_TOKEN",
                "telegram.chat_id": "12345",
                "telegram.enabled": True,
            }
            return mapping.get(key, default)

        # Mock urlopen to capture the payload
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        import json

        with patch("engines.config.get", side_effect=fake_config_get):
            notifier._send_raw("TEST_TOKEN", "12345", huge_message)

        # Inspect the payload that was sent
        self.assertTrue(mock_urlopen.called)
        call_args = mock_urlopen.call_args
        request_obj = call_args[0][0]
        sent_payload = json.loads(request_obj.data.decode("utf-8"))
        sent_text = sent_payload["text"]

        self.assertLessEqual(len(sent_text), notifier._MAX_MESSAGE_LENGTH)
        self.assertTrue(sent_text.endswith("(truncated)"))

    # ----------------------------------------------------------------
    # 10. _format_balance_hit returns expected HTML structure
    # ----------------------------------------------------------------
    def test_format_balance_hit(self):
        """_format_balance_hit must produce HTML with key fields present."""
        data = {
            "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "balance": 50.0,
            "chain": "BTC",
            "method": "random_key",
            "key": "0xdeadbeef",
        }
        result = notifier._format_balance_hit(data)

        self.assertIn("<b>Balance Hit!</b>", result)
        self.assertIn("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", result)
        self.assertIn("50.0", result)
        self.assertIn("BTC", result)
        self.assertIn("<code>0xdeadbeef</code>", result)
        self.assertIn("Method: random_key", result)

    # ----------------------------------------------------------------
    # 11. _format_daily_report with stats dict returns HTML
    # ----------------------------------------------------------------
    def test_format_daily_report(self):
        """_format_daily_report must produce HTML with all stat fields."""
        stats = {
            "keys_tested": 123456,
            "seeds_tested": 789,
            "hits": 3,
            "uptime": "8h 15m",
            "speed": 2500.0,
            "terminals": 5,
        }
        result = notifier._format_daily_report(stats)

        self.assertIn("<b>NPS Daily Report</b>", result)
        self.assertIn("123,456", result)
        self.assertIn("789", result)
        self.assertIn("Hits: 3", result)
        self.assertIn("Uptime: 8h 15m", result)
        self.assertIn("2,500", result)
        self.assertIn("Terminals: 5", result)

    # ----------------------------------------------------------------
    # 12. _route_callback("menu:status") dispatches to /status handler
    # ----------------------------------------------------------------
    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_route_callback_menu(self, _mock_btn, _mock_send):
        """_route_callback('menu:status') must route to the /status handler."""
        text, buttons = notifier._route_callback("menu:status", app_controller=None)
        self.assertIsInstance(text, str)
        self.assertIn("Status", text)
        # The /status handler returns buttons=None
        self.assertIsNone(buttons)


if __name__ == "__main__":
    unittest.main()
