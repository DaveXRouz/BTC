"""Tests for logic.pattern_tracker."""

import os
import sys
import threading
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.pattern_tracker import PatternTracker


class TestPatternTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = PatternTracker(history_manager=None)

    def test_record_batch(self):
        """record_batch should update running batch stats."""
        keys = [100, 200, 300, 400, 500]
        scores = [
            {"final_score": 0.5},
            {"final_score": 0.6},
            {"final_score": 0.7},
            {"final_score": 0.4},
            {"final_score": 0.3},
        ]
        self.tracker.record_batch(keys, scores)
        self.assertEqual(self.tracker._batch_stats["total_keys"], 5)
        self.assertEqual(self.tracker._batch_stats["total_batches"], 1)
        self.assertGreater(self.tracker._batch_stats["entropy_sum"], 0)

    def test_record_finding(self):
        """record_finding should store an analyzed finding."""
        score_result = {
            "final_score": 0.85,
            "math_score": 0.7,
            "numerology_score": 0.9,
        }
        self.tracker.record_finding(12345, score_result, has_balance=False)
        self.assertEqual(len(self.tracker._finding_analysis), 1)
        finding = self.tracker._finding_analysis[0]
        self.assertEqual(finding["key"], 12345)
        self.assertEqual(finding["final_score"], 0.85)
        self.assertIn("entropy", finding)
        self.assertIn("digit_balance", finding)

    def test_update_coverage(self):
        """update_coverage should record range data for a puzzle."""
        self.tracker.update_coverage(66, 1000, 2000, 1001)
        cov = self.tracker.get_coverage(66)
        self.assertEqual(cov["total_ranges"], 1)
        self.assertEqual(cov["total_keys"], 1001)

    def test_get_coverage_empty(self):
        """get_coverage should return zeros for unseen puzzles."""
        cov = self.tracker.get_coverage(999)
        self.assertEqual(cov["total_ranges"], 0)
        self.assertEqual(cov["total_keys"], 0)
        self.assertIsNone(cov["least_covered_gap"])

    def test_get_pattern_stats(self):
        """get_pattern_stats should return aggregate data."""
        keys = [42, 99, 1234]
        scores = [{"final_score": 0.5}, {"final_score": 0.6}, {"final_score": 0.7}]
        self.tracker.record_batch(keys, scores)
        stats = self.tracker.get_pattern_stats()
        self.assertEqual(stats["total_keys"], 3)
        self.assertIn("avg_entropy", stats)
        self.assertIn("avg_balance", stats)
        self.assertIn("master_rate", stats)

    def test_empty_stats(self):
        """get_pattern_stats should handle empty tracker gracefully."""
        stats = self.tracker.get_pattern_stats()
        self.assertEqual(stats["total_keys"], 0)
        self.assertEqual(stats["total_batches"], 0)
        self.assertEqual(stats["total_findings"], 0)
        self.assertEqual(stats["finding_avg_score"], 0.0)

    def test_thread_safety(self):
        """Concurrent record_batch calls should not corrupt data."""
        errors = []

        def worker(batch_id):
            try:
                keys = [batch_id * 100 + i for i in range(10)]
                scores = [{"final_score": 0.5} for _ in range(10)]
                self.tracker.record_batch(keys, scores)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(self.tracker._batch_stats["total_keys"], 100)

    def test_coverage_least_covered(self):
        """get_coverage should identify the largest gap."""
        # Two non-adjacent ranges -> gap in between
        self.tracker.update_coverage(66, 1000, 1500, 501)
        self.tracker.update_coverage(66, 3000, 3500, 501)
        cov = self.tracker.get_coverage(66)
        self.assertIsNotNone(cov["least_covered_gap"])
        gap = cov["least_covered_gap"]
        self.assertEqual(gap["start"], 1500)
        self.assertEqual(gap["end"], 3000)


if __name__ == "__main__":
    unittest.main()
