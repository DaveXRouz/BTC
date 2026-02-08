"""Tests for logic.history_manager."""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.history_manager import HistoryManager


class TestHistoryManager(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.hm = HistoryManager(data_dir=self._tmpdir)

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_load_creates_dir(self):
        """load_all should create the data directory if missing."""
        nested = os.path.join(self._tmpdir, "sub", "dir")
        hm = HistoryManager(data_dir=nested)
        hm.load_all()
        self.assertTrue(os.path.isdir(nested))

    def test_record_entry(self):
        """record_entry should append to in-memory history."""
        self.hm.load_all()
        self.hm.record_entry({"date": "2026-01-01", "keys_tested": 100, "hits": 0})
        entries = self.hm.get_history()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["keys_tested"], 100)

    def test_get_history_limit(self):
        """get_history should respect the limit parameter."""
        self.hm.load_all()
        for i in range(20):
            self.hm.record_entry({"index": i, "date": "2026-01-01"})
        result = self.hm.get_history(limit=5)
        self.assertEqual(len(result), 5)
        # Should be the LAST 5 entries
        self.assertEqual(result[0]["index"], 15)

    def test_throttled_save(self):
        """Rapid writes should not all flush to disk due to throttle."""
        self.hm.load_all()
        # First write goes through
        self.hm.record_entry({"date": "2026-01-01", "i": 0})
        # Subsequent writes within 60s should be throttled
        self.hm.record_entry({"date": "2026-01-01", "i": 1})
        self.hm.record_entry({"date": "2026-01-01", "i": 2})
        # In-memory should have all 3
        self.assertEqual(len(self.hm.get_history()), 3)

    def test_compact(self):
        """compact should trim history beyond max and roll into daily summaries."""
        self.hm.load_all()
        # Add more than max entries
        for i in range(10010):
            self.hm._history["entries"].append(
                {"date": "2026-01-01", "keys_tested": 1, "hits": 0}
            )
        self.assertEqual(len(self.hm._history["entries"]), 10010)
        self.hm.compact()
        self.assertLessEqual(len(self.hm._history["entries"]), 10000)
        # Should have created a daily summary
        summaries = self.hm._history.get("daily_summaries", {})
        self.assertIn("2026-01-01", summaries)

    def test_flush(self):
        """flush should force-write all data to disk."""
        self.hm.load_all()
        self.hm.record_entry({"date": "2026-01-01", "keys_tested": 50, "hits": 1})
        self.hm.flush()
        # Verify file was written
        history_path = os.path.join(self._tmpdir, "history.json")
        self.assertTrue(os.path.exists(history_path))
        with open(history_path) as f:
            data = json.load(f)
        self.assertEqual(len(data["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
