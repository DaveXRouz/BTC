"""Tests for engines.session_manager module."""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import session_manager


class TestSessionManager(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = session_manager.SESSIONS_DIR
        session_manager.SESSIONS_DIR = session_manager.Path(self._tmpdir) / "sessions"

    def tearDown(self):
        session_manager.SESSIONS_DIR = self._orig_dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_start_session(self):
        """start_session creates a session file."""
        session_id = session_manager.start_session("test_terminal")
        self.assertIsInstance(session_id, str)
        self.assertIn("test_terminal", session_id)
        path = session_manager.SESSIONS_DIR / f"{session_id}.json"
        self.assertTrue(path.exists())

    def test_end_session(self):
        """end_session records stats and duration."""
        session_id = session_manager.start_session("t1")
        time.sleep(0.1)
        session_manager.end_session(session_id, {"keys_tested": 5000, "hits": 1})

        session = session_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertIsNotNone(session["ended"])
        self.assertGreater(session["duration"], 0)
        self.assertEqual(session["stats"]["keys_tested"], 5000)

    def test_get_session(self):
        """get_session returns session data."""
        session_id = session_manager.start_session("t2", {"mode": "random_key"})
        session = session_manager.get_session(session_id)
        self.assertEqual(session["terminal_id"], "t2")
        self.assertEqual(session["settings"]["mode"], "random_key")

    def test_get_session_missing(self):
        """get_session returns None for missing session."""
        self.assertIsNone(session_manager.get_session("nonexistent"))

    def test_list_sessions(self):
        """list_sessions returns recent sessions."""
        for i in range(3):
            session_manager.start_session(f"t{i}")

        sessions = session_manager.list_sessions()
        self.assertEqual(len(sessions), 3)

    def test_list_sessions_limit(self):
        """list_sessions respects limit."""
        for i in range(5):
            session_manager.start_session(f"t{i}")

        sessions = session_manager.list_sessions(limit=2)
        self.assertEqual(len(sessions), 2)

    def test_get_session_stats(self):
        """get_session_stats aggregates across sessions."""
        s1 = session_manager.start_session("t1")
        session_manager.end_session(s1, {"keys_tested": 1000, "hits": 1})

        s2 = session_manager.start_session("t2")
        session_manager.end_session(s2, {"keys_tested": 2000, "hits": 0})

        stats = session_manager.get_session_stats()
        self.assertEqual(stats["total_sessions"], 2)
        self.assertEqual(stats["total_keys"], 3000)
        self.assertEqual(stats["total_hits"], 1)

    def test_empty_stats(self):
        """get_session_stats returns zeros when no sessions."""
        stats = session_manager.get_session_stats()
        self.assertEqual(stats["total_sessions"], 0)


if __name__ == "__main__":
    unittest.main()
