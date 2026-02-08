"""Tests for the ScannerBrain adaptive learning engine."""

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

# secp256k1 curve order
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


class TestScannerBrain(unittest.TestCase):

    def setUp(self):
        """Create a temporary knowledge directory for each test."""
        self._tmpdir = tempfile.mkdtemp()
        self._knowledge_dir = Path(self._tmpdir) / "scanner_knowledge"

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _make_brain(self):
        """Create a ScannerBrain with temp knowledge dir."""
        from engines.scanner_brain import ScannerBrain

        brain = ScannerBrain()
        brain._knowledge_dir = self._knowledge_dir
        brain._load_knowledge()
        return brain

    def test_brain_init(self):
        """ScannerBrain() creates knowledge dir and loads empty state."""
        brain = self._make_brain()
        self.assertTrue(self._knowledge_dir.exists())
        self.assertTrue((self._knowledge_dir / "sessions").exists())
        self.assertIsInstance(brain._strategy_log, dict)
        self.assertIsInstance(brain._pattern_discoveries, list)
        self.assertIsInstance(brain._ai_insights, list)

    def test_strategy_selection(self):
        """select_strategy returns a valid strategy name."""
        from engines.scanner_brain import STRATEGIES

        brain = self._make_brain()
        strategy = brain.select_strategy()
        self.assertIn(strategy, STRATEGIES)

    def test_strategy_selection_with_history(self):
        """select_strategy considers past performance when exploiting."""
        brain = self._make_brain()
        # Seed strategy log with a clearly winning strategy
        brain._strategy_log = {
            "numerology_guided": {
                "runs": 10,
                "total_keys": 100000,
                "high_scores": 50,
                "patterns": 20,
                "hits": 3,
                "last_used": time.time(),
            },
            "random": {
                "runs": 10,
                "total_keys": 100000,
                "high_scores": 1,
                "patterns": 0,
                "hits": 0,
                "last_used": time.time() - 86400 * 30,
            },
        }
        # With 0% exploration, should always pick the best
        results = set()
        for _ in range(20):
            results.add(brain.select_strategy(exploration_rate=0.0))
        self.assertEqual(results, {"numerology_guided"})

    def test_session_lifecycle(self):
        """start_session + end_session saves session to disk."""
        brain = self._make_brain()

        config = brain.start_session("random_key", ["btc", "eth"], ["USDT"])
        self.assertIn("strategy", config)
        self.assertIn("session_id", config)
        self.assertIsNotNone(brain._current_session_id)

        stats = {
            "keys_tested": 1000,
            "seeds_tested": 0,
            "hits": 0,
            "speed": 500.0,
            "elapsed": 2.0,
        }
        summary = brain.end_session(stats)
        self.assertIn("session_summary", summary)
        self.assertIn("learning_outcomes", summary)
        self.assertIn("next_recommendations", summary)

        # Session file should exist
        sessions_dir = self._knowledge_dir / "sessions"
        session_files = list(sessions_dir.glob("*.json"))
        self.assertGreater(len(session_files), 0)

        # Strategy log should be saved
        strat_path = self._knowledge_dir / "strategy_log.json"
        self.assertTrue(strat_path.exists())

    def test_smart_key_generation(self):
        """generate_smart_key returns valid int in secp256k1 range."""
        brain = self._make_brain()
        brain._current_strategy = "random"

        key = brain.generate_smart_key()
        self.assertIsInstance(key, int)
        self.assertGreaterEqual(key, 1)
        self.assertLess(key, N)

    def test_smart_key_numerology_guided(self):
        """generate_smart_key works with numerology_guided strategy."""
        brain = self._make_brain()
        brain._current_strategy = "numerology_guided"

        key = brain.generate_smart_key()
        self.assertIsInstance(key, int)
        self.assertGreaterEqual(key, 1)
        self.assertLess(key, N)

    def test_smart_key_all_strategies(self):
        """generate_smart_key returns valid keys for all strategies."""
        from engines.scanner_brain import STRATEGIES

        brain = self._make_brain()
        for strategy in STRATEGIES:
            brain._current_strategy = strategy
            key = brain.generate_smart_key()
            self.assertIsInstance(key, int)
            self.assertGreaterEqual(key, 1)
            self.assertLess(key, N)

    def test_record_finding(self):
        """record_finding buffers entries."""
        brain = self._make_brain()
        brain._current_strategy = "random"

        entry = {
            "key_hex": "0x1234abcd",
            "addresses": {"btc": "1abc", "eth": "0xdef"},
            "has_balance": True,
            "score": 0.8,
        }
        brain.record_finding(entry)

        self.assertEqual(len(brain._session_findings), 1)
        self.assertEqual(len(brain._pattern_discoveries), 1)
        self.assertEqual(brain._session_findings[0]["strategy"], "random")
        self.assertTrue(brain._dirty)

    def test_record_finding_computes_entropy(self):
        """record_finding computes entropy for the key."""
        brain = self._make_brain()
        brain._current_strategy = "random"

        entry = {
            "key_hex": "0x" + "ab" * 32,
            "addresses": {},
            "has_balance": False,
            "score": 0.9,
        }
        brain.record_finding(entry)
        self.assertIn("entropy", brain._session_findings[0])

    def test_persistence(self):
        """Knowledge survives brain restart (save + load)."""
        brain = self._make_brain()
        brain._current_strategy = "numerology_guided"

        # Record some data
        brain._strategy_log["numerology_guided"] = {
            "runs": 5,
            "total_keys": 50000,
            "high_scores": 10,
            "patterns": 3,
            "hits": 1,
            "last_used": time.time(),
        }
        brain._pattern_discoveries.append(
            {
                "timestamp": time.time(),
                "key_hex": "0xabc",
                "score": 0.85,
                "strategy": "numerology_guided",
            }
        )
        brain._save_knowledge()

        # Create a new brain instance pointing to same dir
        from engines.scanner_brain import ScannerBrain

        brain2 = ScannerBrain()
        brain2._knowledge_dir = self._knowledge_dir
        brain2._load_knowledge()

        self.assertIn("numerology_guided", brain2._strategy_log)
        self.assertEqual(brain2._strategy_log["numerology_guided"]["runs"], 5)
        self.assertEqual(len(brain2._pattern_discoveries), 1)

    def test_default_backward_compat(self):
        """Scanner still works without brain features — brain=None path."""
        from solvers.scanner_solver import ScannerSolver

        # Scanner should initialize even if brain import works
        s = ScannerSolver("random_key", check_balance_online=False)
        self.assertEqual(s.mode, "random_key")
        # Brain should be initialized
        self.assertIsNotNone(s.brain)

    def test_get_strategy_params(self):
        """get_strategy_params returns valid params for each strategy."""
        from engines.scanner_brain import STRATEGIES

        brain = self._make_brain()
        for strategy in STRATEGIES:
            params = brain.get_strategy_params(strategy)
            self.assertIsInstance(params, dict)
            self.assertEqual(params["strategy"], strategy)

    def test_mid_session_check_no_ai(self):
        """mid_session_check returns None when AI is unavailable."""
        brain = self._make_brain()
        with patch("engines.ai_engine.is_available", return_value=False):
            result = brain.mid_session_check({"keys_tested": 50000})
        self.assertIsNone(result)

    def test_key_entropy(self):
        """_key_entropy returns a positive float."""
        brain = self._make_brain()
        entropy = brain._key_entropy(0xDEADBEEF)
        self.assertIsInstance(entropy, float)
        self.assertGreater(entropy, 0)


if __name__ == "__main__":
    unittest.main()
