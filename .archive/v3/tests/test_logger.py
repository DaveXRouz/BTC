"""Tests for engines/logger.py — Centralized logging."""

import logging
import os
import tempfile
import unittest
from unittest.mock import patch

from engines.logger import (
    MAX_BYTES,
    TelegramErrorHandler,
    get_logger,
    reset,
    setup,
)


class TestLoggerSetup(unittest.TestCase):
    def setUp(self):
        reset()
        # Remove any handlers added by previous tests
        root = logging.getLogger()
        for h in root.handlers[:]:
            root.removeHandler(h)

    def tearDown(self):
        reset()

    def test_setup_idempotent(self):
        setup()
        root = logging.getLogger()
        count1 = len(root.handlers)
        setup()
        count2 = len(root.handlers)
        self.assertEqual(count1, count2)

    def test_get_logger_returns_named_logger(self):
        log = get_logger("test.module")
        self.assertEqual(log.name, "test.module")

    def test_get_logger_calls_setup(self):
        reset()
        log = get_logger("auto.setup")
        self.assertIsNotNone(log)

    def test_setup_creates_data_dir(self):
        from pathlib import Path

        data_dir = Path(__file__).parent.parent / "data"
        setup()
        self.assertTrue(data_dir.exists())

    def test_root_logger_level_debug(self):
        setup()
        root = logging.getLogger()
        self.assertEqual(root.level, logging.DEBUG)

    def test_max_bytes_constant(self):
        self.assertEqual(MAX_BYTES, 10 * 1024 * 1024)


class TestTelegramErrorHandler(unittest.TestCase):
    def test_handler_level_is_error(self):
        handler = TelegramErrorHandler()
        self.assertEqual(handler.level, logging.ERROR)

    def test_rate_limiting(self):
        handler = TelegramErrorHandler()
        handler._last_send = 0
        # After setting _last_send to recent time, emit should skip
        import time

        handler._last_send = time.time()
        record = logging.LogRecord("test", logging.ERROR, "", 0, "msg", (), None)
        # Should not raise (skips due to rate limit)
        handler.emit(record)


if __name__ == "__main__":
    unittest.main()
