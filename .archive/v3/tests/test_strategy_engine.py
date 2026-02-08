"""Tests for logic.strategy_engine."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.strategy_engine import StrategyEngine


def _mock_get_level_low():
    """Mock learner.get_level at level 1."""
    return {
        "level": 1,
        "name": "Novice",
        "xp": 10,
        "xp_next": 100,
        "capabilities": ["Basic scanning"],
    }


def _mock_get_level_high():
    """Mock learner.get_level at level 4."""
    return {
        "level": 4,
        "name": "Expert",
        "xp": 5000,
        "xp_next": 10000,
        "capabilities": [
            "Basic scanning",
            "Pattern recognition",
            "Strategy suggestions",
            "Auto-adjust parameters",
        ],
    }


class TestStrategyEngine(unittest.TestCase):

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_initialize(self, mock_adj, mock_level):
        """initialize should return a strategy dict."""
        engine = StrategyEngine()
        result = engine.initialize(mode="both")
        self.assertIn("strategy", result)
        self.assertIn("params", result)
        self.assertIn("level", result)
        self.assertIn("confidence", result)
        self.assertIn("reasoning", result)
        self.assertIn("timing_quality", result)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_refresh(self, mock_adj, mock_level):
        """refresh should not raise errors."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        # Should not raise
        engine.refresh({"keys_tested": 10000, "hits": 0, "speed": 500})

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_record_result(self, mock_adj, mock_level):
        """record_result should store entries."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        engine.record_result({"key": 42, "score": 0.9, "has_balance": False})
        self.assertEqual(len(engine._session_results), 1)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.learner.add_xp")
    def test_finalize(self, mock_xp, mock_adj, mock_level):
        """finalize should return a summary dict."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        summary = engine.finalize({"keys_tested": 50000, "hits": 1})
        self.assertIn("duration", summary)
        self.assertIn("strategy_used", summary)
        self.assertIn("level", summary)
        self.assertIn("results_recorded", summary)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_get_context(self, mock_adj, mock_level):
        """get_context should return date info."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        ctx = engine.get_context()
        self.assertIn("current_year", ctx)
        self.assertIn("current_month", ctx)
        self.assertIn("current_day", ctx)
        self.assertIn("strategy", ctx)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_get_daily_report(self, mock_adj, mock_level):
        """get_daily_strategy_report should return a string."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        report = engine.get_daily_strategy_report()
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_level_gating_low(self, mock_adj, mock_level):
        """Level 1-2 should use fixed 'random' strategy."""
        engine = StrategyEngine()
        result = engine.initialize(mode="both")
        self.assertEqual(result["strategy"], "random")
        self.assertIn("baseline", result["reasoning"].lower())

    @patch("engines.learner.get_level", side_effect=_mock_get_level_high)
    @patch("engines.learner.get_auto_adjustments", return_value={"batch_size": 2000})
    def test_level_gating_high(self, mock_adj, mock_level):
        """Level 4+ should use scanner brain and auto-adjustments."""
        engine = StrategyEngine()
        result = engine.initialize(mode="random_key")
        self.assertEqual(result["level"], 4)
        # Should have auto_adjust
        self.assertIsNotNone(result["auto_adjust"])

    @patch("engines.learner.get_level", side_effect=_mock_get_level_high)
    @patch("engines.learner.get_auto_adjustments", return_value={"batch_size": 3000})
    def test_auto_adjust(self, mock_adj, mock_level):
        """Level 4+ refresh should apply auto-adjustments."""
        engine = StrategyEngine()
        engine.initialize(mode="both")
        engine.refresh({"keys_tested": 100000, "hits": 0})
        # Auto-adjust should have been applied
        auto = engine._current_strategy.get("auto_adjust")
        self.assertIsNotNone(auto)

    @patch("engines.learner.get_level", side_effect=_mock_get_level_low)
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    def test_timing_quality(self, mock_adj, mock_level):
        """Initialize should include timing quality info."""
        engine = StrategyEngine()
        result = engine.initialize(mode="both")
        timing = result.get("timing_quality", {})
        self.assertIn("quality", timing)
        self.assertIn("score", timing)


if __name__ == "__main__":
    unittest.main()
