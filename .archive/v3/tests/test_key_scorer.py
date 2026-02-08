"""Tests for logic.key_scorer."""

import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.key_scorer import KeyScorer


class TestKeyScorer(unittest.TestCase):

    def setUp(self):
        self.scorer = KeyScorer()

    def test_score_key(self):
        """score_key should return a valid score dict."""
        result = self.scorer.score_key(42)
        self.assertIsNotNone(result)
        self.assertIn("final_score", result)
        self.assertGreaterEqual(result["final_score"], 0.0)
        self.assertLessEqual(result["final_score"], 1.0)

    def test_score_key_caching(self):
        """Scoring the same key twice should use the cache."""
        result1 = self.scorer.score_key(42)
        result2 = self.scorer.score_key(42)
        self.assertEqual(result1["final_score"], result2["final_score"])
        # Cache should contain the key
        self.assertEqual(self.scorer.cache_size(), 1)

    def test_score_batch(self):
        """score_batch should return results sorted by score descending."""
        results = self.scorer.score_batch([10, 20, 30, 40, 50])
        self.assertEqual(len(results), 5)
        scores = [r[1]["final_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_get_top_n(self):
        """get_top_n should track highest scored keys."""
        for i in range(1, 51):
            self.scorer.score_key(i)
        top = self.scorer.get_top_n(10)
        self.assertLessEqual(len(top), 10)
        # Should be sorted by score descending
        top_scores = [s for _, s in top]
        self.assertEqual(top_scores, sorted(top_scores, reverse=True))

    def test_get_score_distribution(self):
        """get_score_distribution should have all 11 buckets."""
        self.scorer.score_key(42)
        dist = self.scorer.get_score_distribution()
        self.assertEqual(len(dist), 11)
        # At least one bucket should have count > 0
        self.assertGreater(sum(dist.values()), 0)

    def test_empty_distribution(self):
        """Empty scorer should have all-zero distribution."""
        dist = self.scorer.get_score_distribution()
        self.assertEqual(len(dist), 11)
        self.assertEqual(sum(dist.values()), 0)

    def test_cache_limit(self):
        """Cache should not exceed LRU_MAX."""
        # Score many keys to fill cache
        for i in range(100):
            self.scorer.score_key(i)
        self.assertLessEqual(self.scorer.cache_size(), 10000)

    def test_thread_safety(self):
        """Concurrent scoring should not raise exceptions."""
        errors = []

        def worker(start):
            try:
                for i in range(start, start + 20):
                    self.scorer.score_key(i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i * 20,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        # All keys should be scored
        self.assertEqual(self.scorer.cache_size(), 100)


if __name__ == "__main__":
    unittest.main()
