"""Tests for the Telegram notification system."""

import unittest
from unittest.mock import patch, MagicMock


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


# ================================================================
# New V3 Tests: Command Registry & Dispatch
# ================================================================


class TestCommandRegistry(unittest.TestCase):
    """Tests for the command registry system (4.1)."""

    def test_command_registry_populated(self):
        """The command registry should be populated at module load."""
        from engines.notifier import _command_registry

        # Should have many commands registered
        self.assertGreater(len(_command_registry), 15)
        # Check some specific commands exist
        self.assertIn("/status", _command_registry)
        self.assertIn("/help", _command_registry)
        self.assertIn("/start", _command_registry)
        self.assertIn("/sign", _command_registry)
        self.assertIn("/daily", _command_registry)
        self.assertIn("/health", _command_registry)
        self.assertIn("/export", _command_registry)

    def test_register_command(self):
        """_register_command adds a command to the registry."""
        from engines.notifier import _register_command, _command_registry

        def _test_handler(arg, app_controller):
            return ("test response", None)

        _register_command("/test_custom", "A test command", "status", _test_handler)
        self.assertIn("/test_custom", _command_registry)
        entry = _command_registry["/test_custom"]
        self.assertEqual(entry["desc"], "A test command")
        self.assertEqual(entry["category"], "status")
        self.assertEqual(entry["handler"], _test_handler)

        # Clean up
        del _command_registry["/test_custom"]

    def test_registry_entry_structure(self):
        """Each registry entry should have name, desc, category, handler."""
        from engines.notifier import _command_registry

        for cmd, entry in _command_registry.items():
            self.assertIn("name", entry)
            self.assertIn("desc", entry)
            self.assertIn("category", entry)
            self.assertIn("handler", entry)
            self.assertTrue(callable(entry["handler"]))


class TestDispatchCommand(unittest.TestCase):
    """Tests for dispatch_command and individual command handlers."""

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_status(self, mock_send_buttons, mock_send):
        """dispatch_command /status returns status text."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/status")
        self.assertIsInstance(result, str)
        self.assertIn("Status", result)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_help(self, mock_send_buttons, mock_send):
        """dispatch_command /help returns command reference."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/help")
        self.assertIsInstance(result, str)
        self.assertIn("Command Reference", result)
        # Should contain some command names
        self.assertIn("/status", result)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_health(self, mock_send_buttons, mock_send):
        """dispatch_command /health returns health info."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/health")
        self.assertIsInstance(result, str)
        self.assertIn("Health", result)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_daily(self, mock_send_buttons, mock_send):
        """dispatch_command /daily returns daily insight."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/daily")
        self.assertIsInstance(result, str)
        # Should contain insight or error
        self.assertTrue(
            "Daily Insight" in result
            or "Daily insight error" in result
            or "Trust the process" in result
        )

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_sign_no_arg(self, mock_send_buttons, mock_send):
        """dispatch_command /sign without args returns usage hint."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/sign")
        self.assertIsInstance(result, str)
        self.assertIn("Usage", result)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_sign_with_arg(self, mock_send_buttons, mock_send):
        """dispatch_command /sign with argument calls oracle."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/sign What does 444 mean?")
        self.assertIsInstance(result, str)
        # Should contain oracle reading or error
        self.assertTrue("Oracle" in result or "error" in result.lower())

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_name_no_arg(self, mock_send_buttons, mock_send):
        """dispatch_command /name without args returns usage hint."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/name")
        self.assertIsInstance(result, str)
        self.assertIn("Usage", result)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_name_with_arg(self, mock_send_buttons, mock_send):
        """dispatch_command /name with argument calls oracle name reading."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/name Alice")
        self.assertIsInstance(result, str)
        self.assertTrue("Name" in result or "error" in result.lower())

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_start(self, mock_send_buttons, mock_send):
        """dispatch_command /start returns welcome with menu buttons."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/start")
        self.assertIsInstance(result, str)
        self.assertIn("NPS", result)
        # Should have sent with buttons (the welcome menu)
        mock_send_buttons.assert_called()

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_menu(self, mock_send_buttons, mock_send):
        """dispatch_command /menu returns main menu with buttons."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/menu")
        self.assertIsInstance(result, str)
        self.assertIn("Main Menu", result)
        mock_send_buttons.assert_called()

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_dispatch_command_unknown(self, mock_send_buttons, mock_send):
        """dispatch_command with unknown command returns error text."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/nonexistent_xyz")
        self.assertIsInstance(result, str)
        self.assertIn("Unknown command", result)
        self.assertIn("/help", result)


# ================================================================
# Inline Keyboard Callbacks (4.3)
# ================================================================


class TestRouteCallback(unittest.TestCase):
    """Tests for _route_callback inline keyboard routing."""

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_route_callback_menu(self, mock_send_buttons, mock_send):
        """menu:status callback routes to /status command."""
        from engines.notifier import _route_callback

        text, buttons = _route_callback("menu:status")
        self.assertIsInstance(text, str)
        self.assertIn("Status", text)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_route_callback_ctrl(self, mock_send_buttons, mock_send):
        """ctrl:start_all callback routes to /start_all command."""
        from engines.notifier import _route_callback

        text, buttons = _route_callback("ctrl:start_all")
        self.assertIsInstance(text, str)
        # Should mention starting or failure
        self.assertTrue("Started" in text or "Start failed" in text)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_route_callback_unknown(self, mock_send_buttons, mock_send):
        """Unknown callback returns help text."""
        from engines.notifier import _route_callback

        text, buttons = _route_callback("unknown:action")
        self.assertIsInstance(text, str)
        self.assertIn("Unknown callback", text)

    @patch("engines.notifier.send_message", return_value=True)
    @patch("engines.notifier.send_message_with_buttons", return_value=True)
    def test_route_callback_menu_help(self, mock_send_buttons, mock_send):
        """menu:help callback routes to /help command."""
        from engines.notifier import _route_callback

        text, buttons = _route_callback("menu:help")
        self.assertIsInstance(text, str)
        self.assertIn("Command Reference", text)


# ================================================================
# Message Queue & Rate Limiting (4.4)
# ================================================================


class TestMessageQueue(unittest.TestCase):
    """Tests for message queue and retry logic."""

    @patch("engines.notifier.send_message", return_value=True)
    def test_send_with_retry_success_first_try(self, mock_send):
        """_send_with_retry returns True on first successful attempt."""
        from engines.notifier import _send_with_retry

        result = _send_with_retry("test message", max_retries=3)
        self.assertTrue(result)
        mock_send.assert_called_once()

    @patch("engines.notifier.send_message", side_effect=[False, False, True])
    def test_send_with_retry_succeeds_after_failures(self, mock_send):
        """_send_with_retry succeeds on third attempt."""
        import engines.notifier as n

        # Ensure bot not disabled
        old_disabled = n._bot_disabled
        n._bot_disabled = False
        try:
            result = n._send_with_retry("test", max_retries=3)
            self.assertTrue(result)
            self.assertEqual(mock_send.call_count, 3)
        finally:
            n._bot_disabled = old_disabled

    @patch("engines.notifier.send_message", return_value=False)
    def test_send_with_retry_exhausted(self, mock_send):
        """_send_with_retry returns False after all retries fail."""
        import engines.notifier as n

        old_disabled = n._bot_disabled
        n._bot_disabled = False
        try:
            result = n._send_with_retry("test", max_retries=2)
            self.assertFalse(result)
            self.assertEqual(mock_send.call_count, 2)
        finally:
            n._bot_disabled = old_disabled

    def test_enqueue_message_adds_to_queue(self):
        """_enqueue_message adds messages to the internal queue."""
        import engines.notifier as n

        # Save and reset queue state
        old_queue = n._message_queue[:]
        old_running = n._queue_running
        n._message_queue.clear()
        n._queue_running = True  # Prevent starting the processor thread

        try:
            n._enqueue_message("test enqueue", parse_mode="HTML")
            self.assertEqual(len(n._message_queue), 1)
            self.assertEqual(n._message_queue[0]["text"], "test enqueue")
            self.assertIsNone(n._message_queue[0]["buttons"])
            self.assertEqual(n._message_queue[0]["parse_mode"], "HTML")
        finally:
            n._message_queue = old_queue
            n._queue_running = old_running


# ================================================================
# Bot Health & Auto-Disable (4.5)
# ================================================================


class TestBotHealth(unittest.TestCase):
    """Tests for bot health tracking and auto-disable."""

    def test_is_bot_healthy_default(self):
        """Bot should be healthy by default."""
        import engines.notifier as n

        old_disabled = n._bot_disabled
        n._bot_disabled = False
        try:
            self.assertTrue(n.is_bot_healthy())
        finally:
            n._bot_disabled = old_disabled

    def test_is_bot_healthy_after_disable(self):
        """Bot should be unhealthy after being disabled."""
        import engines.notifier as n

        old_disabled = n._bot_disabled
        n._bot_disabled = True
        try:
            self.assertFalse(n.is_bot_healthy())
        finally:
            n._bot_disabled = old_disabled

    def test_record_success_resets_failures(self):
        """_record_success should reset consecutive failure count."""
        import engines.notifier as n

        old_failures = n._consecutive_failures
        old_disabled = n._bot_disabled
        n._consecutive_failures = 3
        n._bot_disabled = False
        try:
            n._record_success()
            self.assertEqual(n._consecutive_failures, 0)
        finally:
            n._consecutive_failures = old_failures
            n._bot_disabled = old_disabled

    def test_record_success_reenables_bot(self):
        """_record_success should re-enable a disabled bot."""
        import engines.notifier as n

        old_failures = n._consecutive_failures
        old_disabled = n._bot_disabled
        n._consecutive_failures = 10
        n._bot_disabled = True
        try:
            n._record_success()
            self.assertFalse(n._bot_disabled)
            self.assertEqual(n._consecutive_failures, 0)
        finally:
            n._consecutive_failures = old_failures
            n._bot_disabled = old_disabled

    def test_record_failure_disables_after_threshold(self):
        """_record_failure should disable bot after 5 consecutive failures."""
        import engines.notifier as n

        old_failures = n._consecutive_failures
        old_disabled = n._bot_disabled
        n._consecutive_failures = 0
        n._bot_disabled = False
        try:
            for _ in range(5):
                n._record_failure()
            self.assertTrue(n._bot_disabled)
            self.assertEqual(n._consecutive_failures, 5)
        finally:
            n._consecutive_failures = old_failures
            n._bot_disabled = old_disabled


# ================================================================
# Notification Templates (4.6)
# ================================================================


class TestNotificationTemplates(unittest.TestCase):
    """Tests for notification template formatting functions."""

    def test_format_balance_hit(self):
        """_format_balance_hit returns HTML with address and balance."""
        from engines.notifier import _format_balance_hit

        result = _format_balance_hit(
            {
                "address": "1ABC",
                "balance": 0.5,
                "chain": "BTC",
                "method": "random",
            }
        )
        self.assertIn("Balance Hit", result)
        self.assertIn("1ABC", result)
        self.assertIn("0.5", result)
        self.assertIn("BTC", result)

    def test_format_daily_report(self):
        """_format_daily_report returns HTML with stats."""
        from engines.notifier import _format_daily_report

        result = _format_daily_report(
            {
                "keys_tested": 50000,
                "seeds_tested": 100,
                "hits": 2,
                "uptime": "12h",
                "speed": 1500,
                "terminals": 3,
            }
        )
        self.assertIn("Daily Report", result)
        self.assertIn("50,000", result)
        self.assertIn("Terminals: 3", result)

    def test_format_health_alert(self):
        """_format_health_alert returns HTML with endpoint status."""
        from engines.notifier import _format_health_alert

        result = _format_health_alert(
            {
                "endpoint": "blockstream",
                "healthy": True,
                "url": "https://blockstream.info/api",
            }
        )
        self.assertIn("Health Alert", result)
        self.assertIn("blockstream", result)
        self.assertIn("UP", result)

    def test_format_health_alert_down(self):
        """_format_health_alert shows DOWN for unhealthy endpoints."""
        from engines.notifier import _format_health_alert

        result = _format_health_alert(
            {
                "endpoint": "eth_rpc",
                "healthy": False,
                "url": "https://eth.llamarpc.com",
            }
        )
        self.assertIn("DOWN", result)

    def test_format_ai_adjustment(self):
        """_format_ai_adjustment returns HTML with adjustment details."""
        from engines.notifier import _format_ai_adjustment

        result = _format_ai_adjustment(
            {
                "parameter": "batch_size",
                "old_value": 1000,
                "new_value": 2000,
                "reason": "improved throughput",
                "level": 3,
            }
        )
        self.assertIn("AI Adjustment", result)
        self.assertIn("batch_size", result)
        self.assertIn("1000", result)
        self.assertIn("2000", result)
        self.assertIn("AI Level: 3", result)


# ================================================================
# Backward Compatibility
# ================================================================


class TestBackwardCompatibility(unittest.TestCase):
    """Ensure old API entry points still work."""

    @patch("engines.notifier.send_message", return_value=True)
    def test_process_telegram_command_returns_string(self, mock_send):
        """process_telegram_command returns a response string."""
        from engines.notifier import process_telegram_command

        result = process_telegram_command("/help")
        self.assertIsInstance(result, str)
        self.assertIn("Command Reference", result)

    @patch("engines.notifier.send_message", return_value=True)
    def test_dispatch_command_preserves_args(self, mock_send):
        """dispatch_command should pass arguments to handlers."""
        from engines.notifier import dispatch_command

        result = dispatch_command("/sign test question 123")
        self.assertIsInstance(result, str)
        # Should not say "Usage" since we provided an argument
        self.assertNotIn("Usage", result)


if __name__ == "__main__":
    unittest.main()
