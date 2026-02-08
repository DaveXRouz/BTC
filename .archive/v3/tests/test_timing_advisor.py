"""Tests for logic.timing_advisor."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.timing_advisor import (
    get_current_quality,
    get_optimal_hours_today,
    get_cosmic_alignment,
)


class TestTimingAdvisor(unittest.TestCase):

    def test_get_current_quality(self):
        """get_current_quality should return a valid result dict."""
        result = get_current_quality()
        self.assertIn("quality", result)
        self.assertIn("score", result)
        self.assertIn("moon_phase", result)
        self.assertIn("reasoning", result)

    def test_quality_has_required_fields(self):
        """Quality should be one of the expected values."""
        result = get_current_quality()
        self.assertIn(result["quality"], ("excellent", "good", "fair", "poor"))
        self.assertGreaterEqual(result["score"], 0.0)
        self.assertLessEqual(result["score"], 1.0)
        self.assertIsInstance(result["moon_phase"], str)
        self.assertTrue(len(result["reasoning"]) > 0)

    def test_get_optimal_hours(self):
        """get_optimal_hours_today should return 24 entries."""
        hours = get_optimal_hours_today()
        self.assertEqual(len(hours), 24)
        # Each entry is (hour, score)
        for hour, score in hours:
            self.assertGreaterEqual(hour, 0)
            self.assertLessEqual(hour, 23)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_get_cosmic_alignment(self):
        """get_cosmic_alignment should return a float score."""
        score = get_cosmic_alignment(12345)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_alignment_range(self):
        """Different keys should produce different alignment scores."""
        scores = set()
        for key in [1, 11, 22, 33, 42, 100, 999, 12345, 99999]:
            scores.add(get_cosmic_alignment(key))
        # Should have at least a few distinct values
        self.assertGreater(len(scores), 1)

    def test_optimal_hours_sorted(self):
        """Optimal hours should be sorted by score descending."""
        hours = get_optimal_hours_today()
        scores = [s for _, s in hours]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
