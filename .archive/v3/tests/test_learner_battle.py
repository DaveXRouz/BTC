"""Battle tests for engines.learner module.

Stress tests for level boundaries, edge cases, corruption recovery,
persistence, and thread safety.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines import learner


class TestLearnerBattle(unittest.TestCase):
    """Battle tests targeting learner edge cases and stress scenarios."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_data = learner.DATA_DIR
        self._orig_state = learner.STATE_FILE
        learner.DATA_DIR = Path(self._tmpdir)
        learner.STATE_FILE = Path(self._tmpdir) / "learning_state.json"
        learner._state = None

    def tearDown(self):
        learner.DATA_DIR = self._orig_data
        learner.STATE_FILE = self._orig_state
        learner._state = None
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1-5: Level boundary tests
    # ------------------------------------------------------------------

    def test_level_boundary_100(self):
        """Adding exactly 100 XP reaches Level 2 (Student)."""
        learner.load_state()
        learner.add_xp(100, "boundary test")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 2)
        self.assertEqual(level_info["name"], "Student")
        self.assertEqual(level_info["xp"], 100)

    def test_level_boundary_500(self):
        """Adding 500 XP reaches Level 3 (Apprentice)."""
        learner.load_state()
        learner.add_xp(500, "boundary test")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 3)
        self.assertEqual(level_info["name"], "Apprentice")
        self.assertEqual(level_info["xp"], 500)

    def test_level_boundary_2000(self):
        """Adding 2000 XP reaches Level 4 (Expert)."""
        learner.load_state()
        learner.add_xp(2000, "boundary test")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 4)
        self.assertEqual(level_info["name"], "Expert")
        self.assertEqual(level_info["xp"], 2000)

    def test_level_boundary_10000(self):
        """Adding 10000 XP reaches Level 5 (Master)."""
        learner.load_state()
        learner.add_xp(10000, "boundary test")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 5)
        self.assertEqual(level_info["name"], "Master")
        self.assertEqual(level_info["xp"], 10000)
        # Master has no next level
        self.assertIsNone(level_info["xp_next"])

    def test_level_boundary_99(self):
        """Adding 99 XP stays at Level 1 (Novice)."""
        learner.load_state()
        learner.add_xp(99, "not enough")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 1)
        self.assertEqual(level_info["name"], "Novice")
        self.assertEqual(level_info["xp"], 99)
        # Next level threshold is 100
        self.assertEqual(level_info["xp_next"], 100)

    # ------------------------------------------------------------------
    # 6-7: Edge case XP values
    # ------------------------------------------------------------------

    def test_negative_xp_handling(self):
        """Adding negative XP changes XP total but does not level down."""
        learner.load_state()
        # First reach Level 2
        learner.add_xp(200, "earn")
        self.assertEqual(learner._state["level"], 2)
        self.assertEqual(learner._state["xp"], 200)

        # Now subtract XP via negative amount
        learner.add_xp(-150, "penalty")
        # XP should decrease
        self.assertEqual(learner._state["xp"], 50)
        # Level should NOT go down -- add_xp only levels UP, never down
        self.assertEqual(learner._state["level"], 2)

    def test_large_xp_overflow(self):
        """Adding a very large XP value does not crash and reaches Level 5."""
        learner.load_state()
        learner.add_xp(999_999_999, "mega xp")
        level_info = learner.get_level()
        self.assertEqual(level_info["level"], 5)
        self.assertEqual(level_info["name"], "Master")
        self.assertEqual(level_info["xp"], 999_999_999)
        # Verify save/load round-trips the large number
        learner.save_state()
        learner._state = None
        learner.load_state()
        self.assertEqual(learner._state["xp"], 999_999_999)

    # ------------------------------------------------------------------
    # 8-9: State file integrity
    # ------------------------------------------------------------------

    def test_corrupt_state_recovery(self):
        """Corrupt JSON in state file falls back to default state."""
        # Write garbage to the state file
        os.makedirs(self._tmpdir, exist_ok=True)
        with open(learner.STATE_FILE, "w") as f:
            f.write("{{{INVALID JSON!!!")

        state = learner.load_state()
        # Should have recovered to defaults
        self.assertEqual(state["xp"], 0)
        self.assertEqual(state["level"], 1)
        self.assertIsInstance(state["insights"], list)
        self.assertEqual(len(state["insights"]), 0)

    def test_save_and_reload(self):
        """State survives a full save-reload cycle with all fields intact."""
        learner.load_state()
        learner.add_xp(350, "test persistence")
        learner._state["insights"] = ["insight A", "insight B"]
        learner._state["recommendations"] = ["rec 1"]
        learner._state["total_learn_calls"] = 7
        learner._state["total_keys_scanned"] = 42000
        learner._state["total_hits"] = 3
        learner.save_state()

        # Capture expected values
        expected_xp = learner._state["xp"]
        expected_level = learner._state["level"]
        expected_insights = list(learner._state["insights"])
        expected_recs = list(learner._state["recommendations"])
        expected_learn_calls = learner._state["total_learn_calls"]
        expected_keys = learner._state["total_keys_scanned"]
        expected_hits = learner._state["total_hits"]

        # Wipe in-memory state and reload from disk
        learner._state = None
        state = learner.load_state()

        self.assertEqual(state["xp"], expected_xp)
        self.assertEqual(state["level"], expected_level)
        self.assertEqual(state["insights"], expected_insights)
        self.assertEqual(state["recommendations"], expected_recs)
        self.assertEqual(state["total_learn_calls"], expected_learn_calls)
        self.assertEqual(state["total_keys_scanned"], expected_keys)
        self.assertEqual(state["total_hits"], expected_hits)

    # ------------------------------------------------------------------
    # 10-11: Auto-adjustments gating
    # ------------------------------------------------------------------

    def test_auto_adjustments_below_level4(self):
        """get_auto_adjustments returns None at Levels 1, 2, and 3."""
        learner.load_state()

        # Level 1
        self.assertIsNone(learner.get_auto_adjustments())

        # Level 2
        learner.add_xp(100)
        self.assertEqual(learner._state["level"], 2)
        self.assertIsNone(learner.get_auto_adjustments())

        # Level 3
        learner.add_xp(400)
        self.assertEqual(learner._state["level"], 3)
        self.assertIsNone(learner.get_auto_adjustments())

    def test_auto_adjustments_at_level4(self):
        """get_auto_adjustments returns a dict at Level 4 with sufficient stats."""
        learner.load_state()
        learner.add_xp(2000, "reach expert")
        self.assertEqual(learner._state["level"], 4)

        # Set stats that trigger the batch_size adjustment
        learner._state["total_keys_scanned"] = 5_000_000
        learner._state["total_hits"] = 0

        adjustments = learner.get_auto_adjustments()
        self.assertIsNotNone(adjustments)
        self.assertIsInstance(adjustments, dict)
        self.assertIn("batch_size", adjustments)
        self.assertEqual(adjustments["batch_size"], 2000)
        self.assertIn("check_every_n", adjustments)
        self.assertEqual(adjustments["check_every_n"], 10000)

    # ------------------------------------------------------------------
    # 12: Insights limit
    # ------------------------------------------------------------------

    def test_insights_limit(self):
        """get_insights respects the limit parameter."""
        learner.load_state()
        # Stuff 20 insights into state
        learner._state["insights"] = [f"insight {i}" for i in range(20)]

        # Default limit is 10
        result = learner.get_insights()
        self.assertEqual(len(result), 10)

        # Custom limit of 5
        result = learner.get_insights(limit=5)
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], "insight 0")
        self.assertEqual(result[4], "insight 4")

        # Limit larger than available returns all
        result = learner.get_insights(limit=100)
        self.assertEqual(len(result), 20)

        # Limit of 0 returns empty
        result = learner.get_insights(limit=0)
        self.assertEqual(len(result), 0)

    # ------------------------------------------------------------------
    # 13: XP persistence through save/reload
    # ------------------------------------------------------------------

    def test_xp_persistence(self):
        """XP added across multiple add_xp calls persists after save/reload."""
        learner.load_state()

        # Add XP in several increments
        learner.add_xp(30, "step 1")
        learner.add_xp(70, "step 2")
        learner.add_xp(200, "step 3")
        expected_xp = 300
        expected_level = 3  # 300 >= 100 (L2) but < 500 (L3)? No, 300 < 500 so L2

        self.assertEqual(learner._state["xp"], expected_xp)
        # 300 >= 100 -> Level 2, but < 500 -> not Level 3
        self.assertEqual(learner._state["level"], 2)

        learner.save_state()
        learner._state = None
        state = learner.load_state()

        self.assertEqual(state["xp"], 300)
        self.assertEqual(state["level"], 2)

    # ------------------------------------------------------------------
    # 14: Concurrent thread safety
    # ------------------------------------------------------------------

    def test_concurrent_add_xp(self):
        """10 threads adding XP simultaneously yields correct total."""
        learner.load_state()
        num_threads = 10
        xp_per_thread = 100
        expected_total = num_threads * xp_per_thread

        barrier = threading.Barrier(num_threads)
        errors = []

        def worker():
            try:
                barrier.wait(timeout=5)
                learner.add_xp(xp_per_thread, "thread test")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        self.assertEqual(len(errors), 0, f"Thread errors: {errors}")
        self.assertEqual(learner._state["xp"], expected_total)
        # 1000 XP -> Level 3 (Apprentice, threshold 500)
        self.assertGreaterEqual(learner._state["level"], 3)


if __name__ == "__main__":
    unittest.main()
