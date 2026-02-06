"""Tests for the AI engine module."""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.ai_engine import is_available, ask_claude, _cache_key, CLAUDE_CLI


class TestAIEngine(unittest.TestCase):

    def test_is_available_returns_bool(self):
        result = is_available()
        self.assertIsInstance(result, bool)

    def test_ask_claude_handles_unavailable(self):
        """When CLI path is wrong, ask_claude should return failure dict."""
        import engines.ai_engine as ai

        original = ai.CLAUDE_CLI
        original_available = ai._available
        try:
            ai.CLAUDE_CLI = "/nonexistent/claude"
            ai._available = None  # Force re-check
            result = ask_claude("What is 2+2?")
            self.assertIsInstance(result, dict)
            self.assertFalse(result["success"])
            self.assertEqual(result["response"], "")
            self.assertIn("error", result)
            self.assertIsInstance(result["elapsed"], float)
            self.assertIsInstance(result["cached"], bool)
        finally:
            ai.CLAUDE_CLI = original
            ai._available = original_available

    def test_cache_key_deterministic(self):
        key1 = _cache_key("hello", "system")
        key2 = _cache_key("hello", "system")
        self.assertEqual(key1, key2)

    def test_cache_key_different_for_different_prompts(self):
        key1 = _cache_key("hello", "system")
        key2 = _cache_key("world", "system")
        self.assertNotEqual(key1, key2)

    def test_ask_claude_returns_dict_structure(self):
        """Verify the result dict always has the expected keys."""
        result = ask_claude("test")
        self.assertIn("success", result)
        self.assertIn("response", result)
        self.assertIn("error", result)
        self.assertIn("elapsed", result)
        self.assertIn("cached", result)


if __name__ == "__main__":
    unittest.main()
