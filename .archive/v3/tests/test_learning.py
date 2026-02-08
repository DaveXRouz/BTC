"""Tests for the learning engine."""

import sys
import os
import unittest
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLearning(unittest.TestCase):

    def setUp(self):
        """Use a temp directory for data files."""
        import engines.learning as learning

        self._orig_data_dir = learning.DATA_DIR
        self._orig_history = learning.HISTORY_FILE
        self._orig_weights = learning.WEIGHTS_FILE

        from pathlib import Path

        self.tmp_dir = tempfile.mkdtemp()
        learning.DATA_DIR = Path(self.tmp_dir)
        learning.HISTORY_FILE = Path(self.tmp_dir) / "solve_history.json"
        learning.WEIGHTS_FILE = Path(self.tmp_dir) / "factor_weights.json"

    def tearDown(self):
        import engines.learning as learning

        learning.DATA_DIR = self._orig_data_dir
        learning.HISTORY_FILE = self._orig_history
        learning.WEIGHTS_FILE = self._orig_weights

        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_confidence_starts_zero(self):
        from engines.learning import confidence_level

        self.assertEqual(confidence_level(), 0.0)

    def test_record_solve_creates_file(self):
        from engines.learning import record_solve, HISTORY_FILE

        score_result = {
            "final_score": 0.5,
            "math_score": 0.5,
            "math_breakdown": {},
            "numerology_score": 0.5,
            "numerology_breakdown": {},
            "learned_score": 0.5,
            "fc60_token": "RAWU",
            "reduced_number": 5,
            "is_master": False,
        }
        record_solve("test", 42, score_result, True)
        self.assertTrue(HISTORY_FILE.exists())

    def test_history_cap(self):
        from engines.learning import record_solve, _load_history, HISTORY_FILE

        score_result = {
            "final_score": 0.5,
            "math_score": 0.5,
            "math_breakdown": {},
            "numerology_score": 0.5,
            "numerology_breakdown": {},
            "learned_score": 0.5,
            "fc60_token": "RAWU",
            "reduced_number": 5,
            "is_master": False,
        }
        # Write 10001 records directly
        history = [
            {
                "puzzle_type": "test",
                "candidate": i,
                "was_correct": False,
                **score_result,
            }
            for i in range(10001)
        ]
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)

        record_solve("test", 99999, score_result, True)
        loaded = _load_history()
        self.assertLessEqual(len(loaded), 10000)

    def test_get_factor_accuracy_structure(self):
        from engines.learning import get_factor_accuracy

        result = get_factor_accuracy()
        self.assertIn("total_solves", result)
        self.assertIn("total_correct", result)
        self.assertIn("factors", result)

    def test_confidence_after_solves(self):
        from engines.learning import record_solve, confidence_level

        score_result = {
            "final_score": 0.5,
            "math_score": 0.5,
            "math_breakdown": {},
            "numerology_score": 0.5,
            "numerology_breakdown": {},
            "learned_score": 0.5,
            "fc60_token": "RAWU",
            "reduced_number": 5,
            "is_master": False,
        }
        for i in range(15):
            record_solve("test", i, score_result, True)
        self.assertGreater(confidence_level(), 0.0)


if __name__ == "__main__":
    unittest.main()
