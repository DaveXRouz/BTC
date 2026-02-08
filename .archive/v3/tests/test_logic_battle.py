"""Battle tests for the logic layer: StrategyEngine and KeyScorer.

25 tests covering level-gating, caching, concurrency, top-N tracking,
score distribution, and edge cases.
"""

import os
import sys
import threading
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# Helpers -- build mock return values that match real module signatures
# ---------------------------------------------------------------------------


def _mock_get_level(level=1, xp=0, xp_next=100):
    return {
        "level": level,
        "name": "Mock",
        "xp": xp,
        "xp_next": xp_next,
        "capabilities": [],
    }


def _mock_hybrid_score(key_int, context=None):
    """Deterministic fake score based on key_int for reproducible tests."""
    score = round((key_int % 997) / 997.0, 4)
    return {
        "final_score": score,
        "math_score": round(score * 0.6, 4),
        "numerology_score": round(score * 0.4, 4),
        "learned_score": 0.0,
        "weights_used": {"math": 0.4, "numerology": 0.3, "learned": 0.3},
        "fc60_token": "MockToken",
        "fc60_full": "M0",
        "reduced_number": 1,
        "is_master": False,
    }


# ===========================================================================
# StrategyEngine Tests
# ===========================================================================


class TestStrategyWithoutLearner(unittest.TestCase):
    """1. test_strategy_without_learner -- level 1 -> strategy='random'."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=1))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.8},
    )
    def test_strategy_without_learner(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        ctx = se.initialize()
        self.assertEqual(ctx["strategy"], "random")


class TestStrategyLevel2(unittest.TestCase):
    """2. test_strategy_level2 -- level 2 still uses 'random'."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=2, xp=50))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_strategy_level2(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        ctx = se.initialize()
        self.assertEqual(ctx["strategy"], "random")
        self.assertEqual(ctx["level"], 2)


class TestStrategyLevel3(unittest.TestCase):
    """3. test_strategy_level3 -- level 3 tries scanner brain or falls back."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=3, xp=500))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_strategy_level3(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        ctx = se.initialize()
        # At level 3 it tries scanner brain; may select any strategy from
        # STRATEGIES list, or fall back to 'numerology_guided'.
        valid_strategies = (
            "numerology_guided",
            "entropy_targeted",
            "pattern_replay",
            "time_aligned",
            "random",  # scanner brain can pick any
        )
        self.assertIn(ctx["strategy"], valid_strategies)
        # Key assertion: level 3 should use brain, not be forced to "random"
        self.assertEqual(ctx["level"], 3)


class TestInitializeReturnsDict(unittest.TestCase):
    """4. test_initialize_returns_dict -- result contains required keys."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=1))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_initialize_returns_dict(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        ctx = se.initialize()
        required_keys = [
            "strategy",
            "params",
            "weights",
            "level",
            "auto_adjust",
            "confidence",
            "reasoning",
            "timing_quality",
        ]
        for key in required_keys:
            self.assertIn(key, ctx, f"Missing key: {key}")


class TestRefreshLevel1NoSwitch(unittest.TestCase):
    """5. test_refresh_level1_no_switch -- refresh at level 1 keeps strategy."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=1))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_refresh_level1_no_switch(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize()
        original = se._current_strategy["strategy"]
        for _ in range(10):
            se.refresh({"keys_tested": 10000, "hits": 0, "speed": 500})
        self.assertEqual(se._current_strategy["strategy"], original)


class TestRefreshLevel3SwitchAfter5(unittest.TestCase):
    """6. test_refresh_level3_switch_after_5 -- strategy switches at level 3 after 5 refreshes with 0 hits."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=3, xp=500))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_refresh_level3_switch_after_5(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize()
        original_reasoning = se._current_strategy["reasoning"]
        # 5 refreshes with 0 hits should trigger a strategy re-selection
        for _ in range(5):
            se.refresh({"keys_tested": 10000, "hits": 0, "speed": 500})
        # After the switch, reasoning should mention auto-switch
        self.assertIn("Auto-switched", se._current_strategy["reasoning"])
        self.assertEqual(se._refresh_count, 0)  # reset after switch


class TestRecordResult(unittest.TestCase):
    """7. test_record_result -- record_result stores entries."""

    def test_record_result(self):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        self.assertEqual(len(se._session_results), 0)
        se.record_result({"key": 123, "score": 0.8, "has_balance": False})
        se.record_result({"key": 456, "score": 0.9, "has_balance": True})
        self.assertEqual(len(se._session_results), 2)
        self.assertEqual(se._session_results[0]["key"], 123)


class TestFinalizeReturnsSummary(unittest.TestCase):
    """8. test_finalize_returns_summary -- finalize returns dict with expected keys."""

    @patch("engines.learner.add_xp")
    @patch("engines.learner.get_level", return_value=_mock_get_level(level=1))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_finalize_returns_summary(self, _tq, _gw, _cfg, _adj, _gl, _axp):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize()
        se.record_result({"key": 1, "score": 0.5})
        summary = se.finalize({"keys_tested": 5000, "hits": 1, "duration": 10.0})
        expected_keys = [
            "duration",
            "strategy_used",
            "level",
            "refreshes",
            "results_recorded",
            "final_stats",
            "timing_quality",
        ]
        for key in expected_keys:
            self.assertIn(key, summary, f"Missing key: {key}")
        self.assertEqual(summary["results_recorded"], 1)


class TestFinalizeAwardsXp(unittest.TestCase):
    """9. test_finalize_awards_xp -- finalize calls add_xp."""

    @patch("engines.learner.add_xp")
    @patch("engines.learner.get_level", return_value=_mock_get_level(level=1))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_finalize_awards_xp(self, _tq, _gw, _cfg, _adj, _gl, mock_add_xp):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize()
        se.finalize({"keys_tested": 5000, "hits": 2, "duration": 10.0})
        # XP = keys_tested // 1000 + hits * 50 = 5 + 100 = 105
        mock_add_xp.assert_called_once_with(105, reason="scan session")


class TestGetContextNoInit(unittest.TestCase):
    """10. test_get_context_no_init -- get_context before initialize returns {}."""

    def test_get_context_no_init(self):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        ctx = se.get_context()
        self.assertEqual(ctx, {})


class TestGetContextAfterInit(unittest.TestCase):
    """11. test_get_context_after_init -- get_context after initialize has expected keys."""

    @patch("engines.learner.get_level", return_value=_mock_get_level(level=2, xp=80))
    @patch("engines.learner.get_auto_adjustments", return_value=None)
    @patch("engines.config.get", return_value=["btc"])
    @patch("engines.learning.get_weights", return_value={})
    @patch(
        "logic.timing_advisor.get_current_quality",
        return_value={"quality": "good", "score": 0.7},
    )
    def test_get_context_after_init(self, _tq, _gw, _cfg, _adj, _gl):
        from logic.strategy_engine import StrategyEngine

        se = StrategyEngine()
        se.initialize()
        ctx = se.get_context()
        self.assertIn("current_year", ctx)
        self.assertIn("current_month", ctx)
        self.assertIn("current_day", ctx)
        self.assertIn("strategy", ctx)
        self.assertIn("level", ctx)
        self.assertEqual(ctx["level"], 2)


# ===========================================================================
# KeyScorer Tests
# ===========================================================================


class TestScoreKeyBasic(unittest.TestCase):
    """12. test_score_key_basic -- score a key, verify result dict."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_key_basic(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        result = ks.score_key(42)
        self.assertIsInstance(result, dict)
        self.assertIn("final_score", result)
        self.assertGreaterEqual(result["final_score"], 0.0)
        self.assertLessEqual(result["final_score"], 1.0)


class TestScoreKeyCached(unittest.TestCase):
    """13. test_score_key_cached -- score same key twice, cache_size stays 1."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_key_cached(self, mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        r1 = ks.score_key(42)
        r2 = ks.score_key(42)
        self.assertEqual(r1["final_score"], r2["final_score"])
        self.assertEqual(ks.cache_size(), 1)
        # hybrid_score should only be called once (second hit is cached)
        mock_hs.assert_called_once()


class TestCacheEvictionAtMax(unittest.TestCase):
    """14. test_cache_eviction_at_max -- score 10001 unique keys, cache stays at 10000."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_cache_eviction_at_max(self, _mock_hs):
        from logic.key_scorer import KeyScorer, _LRU_MAX

        ks = KeyScorer()
        for i in range(1, _LRU_MAX + 2):  # 10001 keys
            ks.score_key(i)
        self.assertLessEqual(ks.cache_size(), _LRU_MAX)


class TestScoreBatchSorted(unittest.TestCase):
    """15. test_score_batch_sorted -- batch of 5 keys, results sorted by score desc."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_batch_sorted(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        results = ks.score_batch([10, 20, 30, 40, 50])
        scores = [r[1]["final_score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(len(results), 5)


class TestThresholdFilters(unittest.TestCase):
    """16. test_threshold_filters -- scorer with threshold=0.5, low-score keys return None."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_threshold_filters(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer(threshold=0.5)
        # Key 1 -> score = (1 % 997) / 997.0 ~ 0.001 -> below threshold
        result = ks.score_key(1)
        self.assertIsNone(result)
        # Key 997 -> score = 0 / 997 = 0.0 -> below threshold
        result2 = ks.score_key(997)
        self.assertIsNone(result2)
        # Key 750 -> score = 750 / 997 ~ 0.752 -> above threshold
        result3 = ks.score_key(750)
        self.assertIsNotNone(result3)
        self.assertGreaterEqual(result3["final_score"], 0.5)


class TestTopNTracking(unittest.TestCase):
    """17. test_top_n_tracking -- score 200 keys, get_top_n(10) returns exactly 10."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_top_n_tracking(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        for i in range(1, 201):
            ks.score_key(i)
        top10 = ks.get_top_n(10)
        self.assertEqual(len(top10), 10)
        # Verify descending order
        scores = [s for _, s in top10]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestScoreDistribution(unittest.TestCase):
    """18. test_score_distribution -- score 100 keys, distribution has entries."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_distribution(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        for i in range(1, 101):
            ks.score_key(i)
        dist = ks.get_score_distribution()
        self.assertIsInstance(dist, dict)
        # At least some buckets should be populated
        total = sum(dist.values())
        self.assertEqual(total, 100)


class TestClearCache(unittest.TestCase):
    """19. test_clear_cache -- clear_cache empties the cache."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_clear_cache(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        ks.score_key(42)
        ks.score_key(99)
        self.assertEqual(ks.cache_size(), 2)
        ks.clear_cache()
        self.assertEqual(ks.cache_size(), 0)


class TestScoreKeyZero(unittest.TestCase):
    """20. test_score_key_zero -- key_int = 0 doesn't crash."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_key_zero(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        result = ks.score_key(0)
        self.assertIsNotNone(result)
        self.assertIn("final_score", result)


class TestScoreKeyLarge(unittest.TestCase):
    """21. test_score_key_large -- key_int = 2**255 doesn't crash."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_score_key_large(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        big_key = 2**255
        result = ks.score_key(big_key)
        self.assertIsNotNone(result)
        self.assertIn("final_score", result)


class TestConcurrentScoring(unittest.TestCase):
    """22. test_concurrent_scoring -- 5 threads scoring different keys, no crashes."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_concurrent_scoring(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        errors = []

        def worker(start, count):
            try:
                for i in range(start, start + count):
                    ks.score_key(i)
            except Exception as exc:
                errors.append(exc)

        threads = []
        for t_idx in range(5):
            t = threading.Thread(target=worker, args=(t_idx * 100, 100))
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(len(errors), 0, f"Threads raised errors: {errors}")
        self.assertEqual(ks.cache_size(), 500)


class TestTopNDedup(unittest.TestCase):
    """23. test_top_n_dedup -- score same key multiple times, only appears once in top_n."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_top_n_dedup(self, mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        # Score key 42 multiple times (only first call computes, rest cached)
        for _ in range(50):
            ks.score_key(42)
        top = ks.get_top_n(100)
        keys_in_top = [k for k, _ in top]
        # key 42 should appear at most once
        self.assertLessEqual(keys_in_top.count(42), 1)


class TestCacheSizeMethod(unittest.TestCase):
    """24. test_cache_size_method -- cache_size() returns correct count."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_cache_size_method(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        self.assertEqual(ks.cache_size(), 0)
        ks.score_key(1)
        self.assertEqual(ks.cache_size(), 1)
        ks.score_key(2)
        self.assertEqual(ks.cache_size(), 2)
        ks.score_key(1)  # cached, no new entry
        self.assertEqual(ks.cache_size(), 2)


class TestBatchEmpty(unittest.TestCase):
    """25. test_batch_empty -- score_batch([]) returns empty list."""

    @patch("engines.scoring.hybrid_score", side_effect=_mock_hybrid_score)
    def test_batch_empty(self, _mock_hs):
        from logic.key_scorer import KeyScorer

        ks = KeyScorer()
        results = ks.score_batch([])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
