"""Tests for logic.range_optimizer."""

import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.range_optimizer import RangeOptimizer, PUZZLE_RANGES


class TestRangeOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = RangeOptimizer()

    def test_get_next_range(self):
        """get_next_range should return a valid (start, end) tuple."""
        start, end = self.optimizer.get_next_range(66, batch_size=1000)
        self.assertIsInstance(start, int)
        self.assertIsInstance(end, int)
        self.assertLessEqual(end - start + 1, 1000)
        # Should be within the puzzle range
        prange = PUZZLE_RANGES.get(66)
        self.assertGreaterEqual(start, prange[0])
        self.assertLessEqual(end, prange[1])

    def test_mark_scanned(self):
        """mark_scanned should record the range."""
        self.optimizer.mark_scanned(66, 1000, 2000)
        cov = self.optimizer.get_coverage_map(66)
        self.assertGreater(cov["scanned_count"], 0)

    def test_get_coverage_map(self):
        """get_coverage_map should return correct stats."""
        self.optimizer.mark_scanned(10, 512, 612)
        cov = self.optimizer.get_coverage_map(10)
        self.assertIn("total_range", cov)
        self.assertIn("scanned_count", cov)
        self.assertIn("coverage_pct", cov)
        self.assertIn("gaps", cov)
        self.assertEqual(cov["scanned_count"], 101)  # 612 - 512 + 1

    def test_get_favorable_ranges(self):
        """get_favorable_ranges should return the requested count."""
        ranges = self.optimizer.get_favorable_ranges(66, count=5)
        self.assertEqual(len(ranges), 5)
        for start, end in ranges:
            self.assertIsInstance(start, int)
            self.assertIsInstance(end, int)
            self.assertLessEqual(start, end)

    def test_coverage_after_scanning(self):
        """Coverage percentage should increase after scanning."""
        cov_before = self.optimizer.get_coverage_map(10)
        self.assertEqual(cov_before["scanned_count"], 0)

        # Puzzle 10 range: 2^9 = 512 to 2^10 - 1 = 1023
        self.optimizer.mark_scanned(10, 512, 612)
        cov_after = self.optimizer.get_coverage_map(10)
        self.assertGreater(cov_after["coverage_pct"], 0)

    def test_no_overlap(self):
        """Overlapping scanned ranges should be merged in coverage count."""
        self.optimizer.mark_scanned(10, 512, 612)
        self.optimizer.mark_scanned(10, 600, 700)
        cov = self.optimizer.get_coverage_map(10)
        # Merged: 512-700 = 189 keys
        self.assertEqual(cov["scanned_count"], 189)

    def test_small_puzzle(self):
        """Small puzzles (e.g., puzzle 2) should work correctly."""
        # Puzzle 2 range: 2 to 3
        self.optimizer.mark_scanned(2, 2, 3)
        cov = self.optimizer.get_coverage_map(2)
        self.assertEqual(cov["scanned_count"], 2)
        self.assertAlmostEqual(cov["coverage_pct"], 100.0, places=1)

    def test_thread_safety(self):
        """Concurrent mark_scanned calls should not corrupt data."""
        errors = []

        def worker(idx):
            try:
                base = idx * 100 + 1000
                self.optimizer.mark_scanned(66, base, base + 50)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        cov = self.optimizer.get_coverage_map(66)
        self.assertGreater(cov["scanned_count"], 0)


if __name__ == "__main__":
    unittest.main()
