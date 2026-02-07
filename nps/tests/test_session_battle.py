"""Battle tests for engines.session_manager module.

Stress-tests concurrency, corruption handling, edge cases, and
lifecycle invariants that go beyond the basic unit tests.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import session_manager


class TestSessionBattle(unittest.TestCase):
    """Battle tests for session_manager resilience and correctness."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = session_manager.SESSIONS_DIR
        session_manager.SESSIONS_DIR = Path(self._tmpdir) / "sessions"

    def tearDown(self):
        session_manager.SESSIONS_DIR = self._orig_dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Nonexistent session ID returns None
    # ------------------------------------------------------------------
    def test_nonexistent_session_id(self):
        """get_session with a fabricated ID returns None, no exception."""
        # Ensure the sessions dir exists so the test isn't trivially None
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        result = session_manager.get_session("fake_id_999")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 2. Corrupt session file handled gracefully
    # ------------------------------------------------------------------
    def test_corrupt_session_file(self):
        """get_session returns None when the JSON file is corrupt."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        corrupt_id = "corrupt_session"
        path = session_manager.SESSIONS_DIR / f"{corrupt_id}.json"
        path.write_text("{{{not valid json!!!", encoding="utf-8")

        result = session_manager.get_session(corrupt_id)
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 3. Concurrent session starts produce unique IDs
    # ------------------------------------------------------------------
    def test_concurrent_start(self):
        """5 threads starting sessions simultaneously all get unique IDs."""
        results = []
        errors = []

        def _start(terminal_id):
            try:
                sid = session_manager.start_session(terminal_id)
                results.append(sid)
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=_start, args=(f"term_{i}",)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertEqual(len(results), 5)
        # All session IDs must be unique
        self.assertEqual(len(set(results)), 5, "Duplicate session IDs detected")

        # Each session must be retrievable
        for sid in results:
            session = session_manager.get_session(sid)
            self.assertIsNotNone(session, f"Session {sid} not retrievable")

    # ------------------------------------------------------------------
    # 4. Atomic write: no .tmp files left behind
    # ------------------------------------------------------------------
    def test_atomic_write_verification(self):
        """After start_session, a .json file exists and no .tmp remains."""
        sid = session_manager.start_session("atomic_term")
        json_path = session_manager.SESSIONS_DIR / f"{sid}.json"
        tmp_path = session_manager.SESSIONS_DIR / f"{sid}.tmp"

        self.assertTrue(json_path.exists(), ".json file must exist")
        self.assertFalse(tmp_path.exists(), ".tmp file must not remain")

        # Also verify after end_session
        session_manager.end_session(sid, {"keys_tested": 42})
        self.assertTrue(json_path.exists(), ".json file must still exist after end")
        self.assertFalse(tmp_path.exists(), ".tmp file must not remain after end")

    # ------------------------------------------------------------------
    # 5. end_session on nonexistent ID doesn't crash
    # ------------------------------------------------------------------
    def test_end_session_nonexistent(self):
        """Ending a session that doesn't exist logs a warning but no exception."""
        session_manager.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        # Should not raise
        try:
            session_manager.end_session("does_not_exist_12345")
        except Exception as exc:
            self.fail(f"end_session raised an exception on nonexistent ID: {exc}")

    # ------------------------------------------------------------------
    # 6. Full session lifecycle: start -> end -> verify duration
    # ------------------------------------------------------------------
    def test_session_lifecycle(self):
        """Start, sleep briefly, end with stats, verify duration recorded."""
        sid = session_manager.start_session("lifecycle_term", {"mode": "both"})

        # Brief pause so duration is measurable
        time.sleep(0.05)

        stats = {"keys_tested": 500, "seeds_tested": 100, "hits": 2}
        session_manager.end_session(sid, stats)

        session = session_manager.get_session(sid)
        self.assertIsNotNone(session)
        self.assertIsNotNone(session["ended"])
        self.assertIn("duration", session)
        self.assertGreater(session["duration"], 0)
        self.assertEqual(session["stats"]["keys_tested"], 500)
        self.assertEqual(session["stats"]["seeds_tested"], 100)
        self.assertEqual(session["stats"]["hits"], 2)

    # ------------------------------------------------------------------
    # 7. list_sessions respects limit with many sessions
    # ------------------------------------------------------------------
    def test_list_sessions_limit(self):
        """Create 10 sessions, list_sessions(limit=3) returns exactly 3."""
        for i in range(10):
            session_manager.start_session(f"bulk_{i}")

        sessions = session_manager.list_sessions(limit=3)
        self.assertEqual(len(sessions), 3)

        # Default limit should still return all 10
        all_sessions = session_manager.list_sessions()
        self.assertEqual(len(all_sessions), 10)

    # ------------------------------------------------------------------
    # 8. get_session_stats with no sessions returns all zeros
    # ------------------------------------------------------------------
    def test_get_session_stats_empty(self):
        """When no sessions exist, stats are all zero."""
        # Don't even create the sessions dir
        stats = session_manager.get_session_stats()
        self.assertEqual(stats["total_sessions"], 0)
        self.assertEqual(stats["total_duration"], 0)
        self.assertEqual(stats["total_keys"], 0)
        self.assertEqual(stats["total_seeds"], 0)
        self.assertEqual(stats["total_hits"], 0)

    # ------------------------------------------------------------------
    # 9. get_session_stats aggregates across multiple sessions
    # ------------------------------------------------------------------
    def test_get_session_stats_aggregate(self):
        """3 sessions with different stats produce correct aggregate sums."""
        session_stats_list = [
            {"keys_tested": 1000, "seeds_tested": 200, "hits": 1},
            {"keys_tested": 3000, "seeds_tested": 500, "hits": 0},
            {"keys_tested": 6000, "seeds_tested": 300, "hits": 3},
        ]

        for i, st in enumerate(session_stats_list):
            sid = session_manager.start_session(f"agg_{i}")
            session_manager.end_session(sid, st)

        stats = session_manager.get_session_stats()
        self.assertEqual(stats["total_sessions"], 3)
        self.assertEqual(stats["total_keys"], 10000)
        self.assertEqual(stats["total_seeds"], 1000)
        self.assertEqual(stats["total_hits"], 4)
        self.assertGreater(stats["total_duration"], 0)

    # ------------------------------------------------------------------
    # 10. get_session returns all expected metadata fields
    # ------------------------------------------------------------------
    def test_session_metadata_fields(self):
        """get_session returns a dict with all expected top-level fields."""
        settings = {"mode": "random_key", "puzzle": True}
        sid = session_manager.start_session("meta_term", settings)

        session = session_manager.get_session(sid)
        self.assertIsNotNone(session)

        # Check all required fields are present
        required_fields = [
            "session_id",
            "terminal_id",
            "started",
            "ended",
            "settings",
            "stats",
        ]
        for field in required_fields:
            self.assertIn(field, session, f"Missing field: {field}")

        # Verify field values before ending
        self.assertEqual(session["session_id"], sid)
        self.assertEqual(session["terminal_id"], "meta_term")
        self.assertIsInstance(session["started"], (int, float))
        self.assertIsNone(session["ended"])
        self.assertEqual(session["settings"], settings)
        self.assertIsInstance(session["stats"], dict)

        # End the session and re-check
        session_manager.end_session(sid, {"keys_tested": 10})
        session = session_manager.get_session(sid)
        self.assertIsNotNone(session["ended"])
        self.assertIn("duration", session)
        self.assertIsInstance(session["duration"], (int, float))


if __name__ == "__main__":
    unittest.main()
