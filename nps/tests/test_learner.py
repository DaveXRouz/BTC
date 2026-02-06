"""Tests for engines.learner module."""

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines import learner


class TestLearner(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_data = learner.DATA_DIR
        self._orig_state = learner.STATE_FILE
        learner.DATA_DIR = learner.Path(self._tmpdir)
        learner.STATE_FILE = learner.Path(self._tmpdir) / "learning_state.json"
        learner._state = None

    def tearDown(self):
        learner.DATA_DIR = self._orig_data
        learner.STATE_FILE = self._orig_state
        learner._state = None
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_default_state(self):
        """Default state has expected fields."""
        state = learner.load_state()
        self.assertEqual(state["xp"], 0)
        self.assertEqual(state["level"], 1)
        self.assertIsInstance(state["insights"], list)

    def test_get_level_initial(self):
        """get_level returns Novice at start."""
        result = learner.get_level()
        self.assertEqual(result["level"], 1)
        self.assertEqual(result["name"], "Novice")
        self.assertEqual(result["xp"], 0)

    def test_add_xp(self):
        """add_xp increases XP."""
        learner.load_state()
        learner.add_xp(50, "test")
        self.assertEqual(learner._state["xp"], 50)

    def test_level_up(self):
        """Adding enough XP triggers level up."""
        learner.load_state()
        learner.add_xp(100, "test")
        self.assertEqual(learner._state["level"], 2)
        learner.add_xp(400, "more test")
        self.assertEqual(learner._state["level"], 3)

    def test_level_5(self):
        """Adding 10000+ XP reaches Level 5."""
        learner.load_state()
        learner.add_xp(10000, "master")
        level = learner.get_level()
        self.assertEqual(level["level"], 5)
        self.assertEqual(level["name"], "Master")

    def test_save_and_load(self):
        """State persists to disk."""
        learner.load_state()
        learner.add_xp(250, "persist")
        learner.save_state()

        # Reload
        learner._state = None
        learner.load_state()
        self.assertEqual(learner._state["xp"], 250)

    def test_learn_without_ai(self):
        """learn() returns graceful result when AI is unavailable."""
        learner.load_state()
        result = learner.learn({"keys_tested": 1000, "hits": 0})
        self.assertIsInstance(result, dict)
        self.assertIn("insights", result)
        self.assertIsInstance(result["insights"], list)
        self.assertGreater(len(result["insights"]), 0)

    def test_auto_adjustments_below_level_4(self):
        """get_auto_adjustments returns None below Level 4."""
        learner.load_state()
        result = learner.get_auto_adjustments()
        self.assertIsNone(result)

    def test_auto_adjustments_level_4(self):
        """get_auto_adjustments returns dict at Level 4+."""
        learner.load_state()
        learner.add_xp(2000)
        learner._state["total_keys_scanned"] = 2_000_000
        result = learner.get_auto_adjustments()
        self.assertIsInstance(result, dict)

    def test_get_insights(self):
        """get_insights returns a list."""
        learner.load_state()
        learner._state["insights"] = ["test insight 1", "test insight 2"]
        result = learner.get_insights()
        self.assertEqual(len(result), 2)

    def test_get_recommendations(self):
        """get_recommendations returns a list."""
        learner.load_state()
        result = learner.get_recommendations()
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
