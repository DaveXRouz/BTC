"""Tests for engines.memory module."""

import unittest
import sys
import os
import json
import tempfile
import shutil
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestMemory(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        import engines.memory as mem

        self.mem = mem
        # Override the data path so tests never touch real data
        self.orig_file = mem.MEMORY_FILE
        self.orig_dir = mem.DATA_DIR
        mem.DATA_DIR = __import__("pathlib").Path(self.tmpdir)
        mem.MEMORY_FILE = mem.DATA_DIR / "scan_memory.json"
        # Reset module state
        mem._cache = None
        mem._dirty = False
        if mem._flush_timer:
            mem._flush_timer.cancel()
        mem._flush_timer = None

    def tearDown(self):
        self.mem.shutdown()
        self.mem.DATA_DIR = self.orig_dir
        self.mem.MEMORY_FILE = self.orig_file
        self.mem._cache = None
        self.mem._dirty = False
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_memory(self):
        """get_memory returns a dict with version 2, sessions list, high_scores list."""
        data = self.mem.get_memory()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["version"], 2)
        self.assertIsInstance(data["sessions"], list)
        self.assertIsInstance(data["high_scores"], list)

    def test_record_session(self):
        """Recorded session appears in get_memory()['sessions']."""
        self.mem.record_session(
            {
                "mode": "puzzle",
                "puzzle": 66,
                "strategy": "mystic",
                "keys_tested": 1000,
                "best_score": 42.5,
                "duration": 10.0,
            }
        )
        sessions = self.mem.get_memory()["sessions"]
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["puzzle"], 66)

    def test_record_high_score(self):
        """Recorded high score appears in get_memory()['high_scores']."""
        self.mem.record_high_score(
            key_hex="deadbeef",
            score=99.9,
            addresses=["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"],
        )
        scores = self.mem.get_memory()["high_scores"]
        self.assertEqual(len(scores), 1)
        self.assertAlmostEqual(scores[0]["score"], 99.9)

    def test_trim_sessions(self):
        """Sessions list is trimmed to <= 1000 entries."""
        for i in range(1100):
            self.mem.record_session(
                {
                    "mode": "puzzle",
                    "puzzle": i,
                    "strategy": "test",
                    "keys_tested": 1,
                    "best_score": 0.0,
                    "duration": 0.1,
                }
            )
        sessions = self.mem.get_memory()["sessions"]
        self.assertLessEqual(len(sessions), 1000)

    def test_recommendations(self):
        """get_recommendations returns a list of strings."""
        recs = self.mem.get_recommendations()
        self.assertIsInstance(recs, list)
        for r in recs:
            self.assertIsInstance(r, str)

    def test_thread_safety(self):
        """10 threads each recording 10 sessions produces 100 sessions without crash."""
        errors = []

        def worker():
            try:
                for _ in range(10):
                    self.mem.record_session(
                        {
                            "mode": "puzzle",
                            "puzzle": 66,
                            "strategy": "thread",
                            "keys_tested": 1,
                            "best_score": 0.0,
                            "duration": 0.01,
                        }
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Errors in threads: {errors}")
        sessions = self.mem.get_memory()["sessions"]
        self.assertEqual(len(sessions), 100)

    def test_get_summary(self):
        """get_summary returns dict with expected aggregate keys."""
        self.mem.record_session(
            {
                "mode": "puzzle",
                "puzzle": 66,
                "strategy": "test",
                "keys_tested": 500,
                "best_score": 10.0,
                "duration": 5.0,
            }
        )
        summary = self.mem.get_summary()
        self.assertIsInstance(summary, dict)
        for key in ("total_sessions", "total_keys"):
            self.assertIn(key, summary, f"Missing key: {key}")

    def test_no_disk_on_read(self):
        """Merely calling get_memory does not create the file on disk."""
        self.mem.get_memory()
        self.assertFalse(
            self.mem.MEMORY_FILE.exists(),
            "File should not exist on disk after a read-only access",
        )

    def test_flush_writes_file(self):
        """After recording + flush_to_disk, the file exists and is valid JSON."""
        self.mem.record_session(
            {
                "mode": "puzzle",
                "puzzle": 1,
                "strategy": "flush_test",
                "keys_tested": 1,
                "best_score": 0.0,
                "duration": 0.1,
            }
        )
        self.mem.flush_to_disk()
        self.assertTrue(
            self.mem.MEMORY_FILE.exists(),
            "File should exist after flush_to_disk()",
        )
        with open(self.mem.MEMORY_FILE, "r") as f:
            data = json.load(f)
        self.assertIn("sessions", data)


if __name__ == "__main__":
    unittest.main()
