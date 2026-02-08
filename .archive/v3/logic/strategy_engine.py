"""
Strategy Engine -- The Brain of the Logic Layer
=================================================
Orchestrates scanning strategy selection, mid-session adjustments,
and session finalization. Level-gated by the learner XP system.
"""

import logging
import time

logger = logging.getLogger(__name__)


class StrategyEngine:
    """High-level strategy coordinator for NPS scanning sessions."""

    def __init__(self):
        self._current_strategy = None
        self._session_start = 0
        self._session_results = []
        self._refresh_count = 0
        self._mode = None
        self._chains = []
        self._tokens = []
        self._last_timing_quality = None

    # ---- Lifecycle ----

    def initialize(self, mode="both", chains=None, tokens=None):
        """Initialize a scanning session strategy.

        Args:
            mode: 'random_key', 'seed_phrase', or 'both'.
            chains: list of chain strings, e.g. ['btc', 'eth'].
            tokens: list of token strings to check.

        Returns:
            strategy dict with: strategy, params, weights, level, auto_adjust,
            confidence, reasoning, timing_quality.
        """
        from engines.learner import get_level, get_auto_adjustments
        from engines.config import get as config_get

        self._mode = mode
        self._chains = chains or config_get("scanner.chains", ["btc", "eth"])
        self._tokens = tokens or []
        self._session_start = time.time()
        self._session_results = []
        self._refresh_count = 0

        level_info = get_level()
        level = level_info.get("level", 1)
        confidence = level_info.get("xp", 0) / max(
            level_info.get("xp_next", 10000) or 10000, 1
        )
        confidence = min(1.0, confidence)

        # Select strategy based on level
        strategy, params, reasoning = self._select_strategy(level, mode)

        # Weights from learning engine
        try:
            from engines.learning import get_weights

            weights = get_weights() or {}
        except Exception:
            weights = {}

        # Auto-adjust (Level 4+)
        auto_adjust = None
        if level >= 4:
            auto_adjust = get_auto_adjustments()

        # Timing quality
        try:
            from logic.timing_advisor import get_current_quality

            timing = get_current_quality()
            self._last_timing_quality = timing
        except Exception:
            timing = {"quality": "unknown", "score": 0.5}
            self._last_timing_quality = timing

        self._current_strategy = {
            "strategy": strategy,
            "params": params,
            "weights": weights,
            "level": level,
            "auto_adjust": auto_adjust,
            "confidence": round(confidence, 4),
            "reasoning": reasoning,
            "timing_quality": timing,
        }

        return dict(self._current_strategy)

    def _select_strategy(self, level, mode):
        """Choose strategy based on level and mode.

        Level 1-2: fixed strategy.
        Level 3+: suggestions based on scanner brain.
        Level 4+: auto-adjustment from learner.

        Returns:
            (strategy_name, params_dict, reasoning_str)
        """
        if level <= 2:
            strategy = "random"
            params = {"batch_size": 1000, "mode": mode}
            reasoning = "Level {}: using baseline random strategy".format(level)
            return strategy, params, reasoning

        # Level 3+: consult scanner brain for strategy selection
        try:
            from engines.scanner_brain import ScannerBrain

            brain = ScannerBrain()
            strategy = brain.select_strategy(exploration_rate=0.15)
            params = brain.get_strategy_params(strategy)
            params["mode"] = mode
            reasoning = "Level {}: scanner brain selected '{}'".format(level, strategy)
        except Exception as exc:
            logger.debug("Scanner brain unavailable: %s", exc)
            strategy = "numerology_guided"
            params = {"batch_size": 1000, "mode": mode}
            reasoning = (
                "Level {}: default numerology_guided (brain unavailable)".format(level)
            )

        return strategy, params, reasoning

    # ---- Mid-session ----

    def refresh(self, stats):
        """Called every ~10K keys. May switch strategy based on performance.

        Args:
            stats: dict with keys_tested, hits, speed, etc.
        """
        self._refresh_count += 1

        if self._current_strategy is None:
            return

        level = self._current_strategy.get("level", 1)

        # Update timing quality periodically
        try:
            from logic.timing_advisor import get_current_quality

            timing = get_current_quality()
            self._last_timing_quality = timing
            self._current_strategy["timing_quality"] = timing
        except Exception:
            pass

        # Level 3+: consider strategy switch if no results after many refreshes
        if level >= 3 and self._refresh_count >= 5:
            hits = stats.get("hits", 0)
            if hits == 0:
                # No hits after 50K+ keys -- try a different strategy
                try:
                    strategy, params, reasoning = self._select_strategy(
                        level, self._mode or "both"
                    )
                    self._current_strategy["strategy"] = strategy
                    self._current_strategy["params"] = params
                    self._current_strategy["reasoning"] = (
                        "Auto-switched after {} refreshes with 0 hits: {}".format(
                            self._refresh_count, reasoning
                        )
                    )
                    self._refresh_count = 0
                except Exception:
                    pass

        # Level 4+: apply auto-adjustments
        if level >= 4:
            try:
                from engines.learner import get_auto_adjustments

                adj = get_auto_adjustments()
                if adj:
                    self._current_strategy["auto_adjust"] = adj
                    if "batch_size" in adj:
                        self._current_strategy["params"]["batch_size"] = adj[
                            "batch_size"
                        ]
            except Exception:
                pass

    def record_result(self, entry):
        """Feed a finding into the strategy engine.

        Args:
            entry: dict with key info, score, has_balance, etc.
        """
        self._session_results.append(entry)

    # ---- Finalization ----

    def finalize(self, final_stats):
        """End session and produce a summary.

        Args:
            final_stats: dict with total keys_tested, hits, duration, etc.

        Returns:
            dict with session summary info.
        """
        elapsed = time.time() - self._session_start if self._session_start else 0

        summary = {
            "duration": round(elapsed, 2),
            "strategy_used": (
                self._current_strategy.get("strategy", "unknown")
                if self._current_strategy
                else "unknown"
            ),
            "level": (
                self._current_strategy.get("level", 1) if self._current_strategy else 1
            ),
            "refreshes": self._refresh_count,
            "results_recorded": len(self._session_results),
            "final_stats": final_stats,
            "timing_quality": self._last_timing_quality,
        }

        # Record XP for the session
        try:
            from engines.learner import add_xp

            keys = final_stats.get("keys_tested", 0)
            hits = final_stats.get("hits", 0)
            xp = keys // 1000 + hits * 50
            if xp > 0:
                add_xp(xp, reason="scan session")
        except Exception:
            pass

        return summary

    # ---- Context ----

    def get_context(self):
        """Return current strategy context for scoring.

        Returns:
            dict suitable for passing as context to hybrid_score.
        """
        if not self._current_strategy:
            return {}

        import time as _time

        now = _time.localtime()
        return {
            "current_year": now.tm_year,
            "current_month": now.tm_mon,
            "current_day": now.tm_mday,
            "strategy": self._current_strategy.get("strategy", "random"),
            "level": self._current_strategy.get("level", 1),
        }

    # ---- Reporting ----

    def get_daily_strategy_report(self):
        """Generate a human-readable daily strategy report.

        Returns:
            str report.
        """
        try:
            from engines.learner import get_level
            from engines.learning import get_solve_stats
            from logic.timing_advisor import (
                get_current_quality,
                get_optimal_hours_today,
            )

            level_info = get_level()
            solve_stats = get_solve_stats()
            timing = get_current_quality()
            optimal = get_optimal_hours_today()[:5]

            lines = [
                "=== NPS Daily Strategy Report ===",
                "",
                "Level: {} ({})".format(
                    level_info.get("level", 1),
                    level_info.get("name", "Unknown"),
                ),
                "XP: {} / {}".format(
                    level_info.get("xp", 0),
                    level_info.get("xp_next", "MAX"),
                ),
                "",
                "Current Timing Quality: {} (score {})".format(
                    timing.get("quality", "unknown"),
                    timing.get("score", 0),
                ),
                "Moon Phase: {}".format(timing.get("moon_phase", "unknown")),
                "Reasoning: {}".format(timing.get("reasoning", "")),
                "",
                "Optimal Hours Today (UTC):",
            ]
            for hour, score in optimal:
                lines.append("  {:02d}:00 -- score {:.3f}".format(hour, score))

            lines.extend(
                [
                    "",
                    "Historical Stats:",
                    "  Total attempts: {}".format(solve_stats.get("total_attempts", 0)),
                    "  Success rate: {:.2%}".format(solve_stats.get("success_rate", 0)),
                    "  Confidence: {:.2f}".format(solve_stats.get("confidence", 0)),
                ]
            )

            if self._current_strategy:
                lines.extend(
                    [
                        "",
                        "Current Strategy: {}".format(
                            self._current_strategy.get("strategy", "none")
                        ),
                        "Session Refreshes: {}".format(self._refresh_count),
                        "Results Recorded: {}".format(len(self._session_results)),
                    ]
                )

            return "\n".join(lines)

        except Exception as exc:
            logger.debug("Failed to generate report: %s", exc)
            return "Strategy report unavailable: {}".format(exc)
