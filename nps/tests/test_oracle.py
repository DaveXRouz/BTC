"""Tests for engines.oracle module."""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines.oracle import read_sign, read_name


class TestOracle(unittest.TestCase):

    def test_read_sign_basic(self):
        """read_sign returns a dict with required keys."""
        result = read_sign("11:11")
        self.assertIsInstance(result, dict)
        for key in ("sign", "numbers", "systems", "interpretation"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_read_sign_with_date(self):
        """read_sign with a date includes fc60 system."""
        result = read_sign("42", date="2026-02-06")
        self.assertIn("systems", result)
        self.assertIn("fc60", result["systems"])

    def test_read_sign_with_time(self):
        """read_sign with date and time includes ganzhi system."""
        result = read_sign("7", date="2026-02-06", time_str="14:30")
        self.assertIn("systems", result)
        self.assertIn("ganzhi", result["systems"])

    def test_angel_numbers(self):
        """read_sign recognises angel number patterns (111)."""
        result = read_sign("111")
        self.assertIn("angel", result["systems"])
        # The angel system entry should contain a match
        angel = result["systems"]["angel"]
        self.assertTrue(angel, "Angel system should have a non-empty result")

    def test_mirror_numbers(self):
        """read_sign detects mirror/palindrome patterns like 12:21."""
        result = read_sign("12:21")
        # Should mention mirror somewhere in synchronicities or interpretation
        found = False
        if "synchronicities" in result:
            for item in result["synchronicities"]:
                if "mirror" in str(item).lower():
                    found = True
                    break
        if not found and "interpretation" in result:
            found = "mirror" in str(result["interpretation"]).lower()
        self.assertTrue(found, "Mirror pattern should be detected for 12:21")

    def test_extract_numbers(self):
        """_extract_numbers pulls integers from free-form text."""
        from engines.oracle import _extract_numbers

        nums = _extract_numbers("abc 42 def 7 xyz")
        self.assertEqual(nums, [42, 7])

    def test_zodiac(self):
        """_get_zodiac returns correct sign for March 25 (Aries)."""
        from engines.oracle import _get_zodiac

        z = _get_zodiac(3, 25)
        self.assertIsInstance(z, dict)
        self.assertEqual(z["sign"], "Aries")

    def test_chaldean(self):
        """_chaldean_reduce returns a positive integer for a word."""
        from engines.oracle import _chaldean_reduce

        r = _chaldean_reduce("HELLO")
        self.assertIsInstance(r, int)
        self.assertGreater(r, 0)

    def test_read_name(self):
        """read_name returns expression, soul_urge, personality, chaldean."""
        result = read_name("Alice")
        self.assertIsInstance(result, dict)
        for key in ("expression", "soul_urge", "personality", "chaldean"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_empty_sign(self):
        """read_sign with empty string returns a valid dict with empty numbers."""
        result = read_sign("")
        self.assertIsInstance(result, dict)
        self.assertIn("numbers", result)
        self.assertEqual(result["numbers"], [])


if __name__ == "__main__":
    unittest.main()
