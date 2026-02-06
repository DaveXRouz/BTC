"""Tests for engines.perf module."""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestPerf(unittest.TestCase):

    def setUp(self):
        from engines.perf import PerfMonitor

        self.perf = PerfMonitor()

    def test_start_stop_timing(self):
        """start/stop records an elapsed time within expected bounds."""
        self.perf.start("op")
        time.sleep(0.01)
        elapsed = self.perf.stop("op")
        self.assertGreater(elapsed, 0.005)
        self.assertLess(elapsed, 0.1)

    def test_summary(self):
        """After 5 start/stop cycles, summary reports count=5 for the operation."""
        for _ in range(5):
            self.perf.start("repeat")
            self.perf.stop("repeat")
        summary = self.perf.summary()
        self.assertIn("repeat", summary)
        self.assertEqual(summary["repeat"]["count"], 5)

    def test_counters(self):
        """count() accumulates values; get_count() returns the total."""
        self.perf.count("keys", 100)
        self.perf.count("keys", 50)
        self.assertEqual(self.perf.get_count("keys"), 150)

    def test_context_manager(self):
        """timer() context manager records elapsed time on the PerfTimer."""
        with self.perf.timer("test_op") as t:
            time.sleep(0.01)
        self.assertGreater(t.elapsed, 0.005)


if __name__ == "__main__":
    unittest.main()
