"""Tests for the scoring engine."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.scoring import hybrid_score, score_batch


class TestHybridScore(unittest.TestCase):

    def test_returns_valid_range(self):
        result = hybrid_score(42)
        self.assertGreaterEqual(result["final_score"], 0.0)
        self.assertLessEqual(result["final_score"], 1.0)

    def test_master_number_boost(self):
        score_11 = hybrid_score(11)
        score_10 = hybrid_score(10)
        self.assertGreater(score_11["numerology_score"], score_10["numerology_score"])

    def test_deterministic(self):
        result1 = hybrid_score(42)
        result2 = hybrid_score(42)
        self.assertEqual(result1["final_score"], result2["final_score"])

    def test_has_required_fields(self):
        result = hybrid_score(100)
        for field in [
            "final_score",
            "math_score",
            "numerology_score",
            "learned_score",
            "fc60_token",
            "is_master",
        ]:
            self.assertIn(field, result)


class TestScoreBatch(unittest.TestCase):

    def test_returns_sorted(self):
        results = score_batch([1, 2, 3, 4, 5])
        self.assertEqual(len(results), 5)
        scores = [r[1]["final_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_batch_length(self):
        results = score_batch([10, 20, 30])
        self.assertEqual(len(results), 3)


if __name__ == "__main__":
    unittest.main()
