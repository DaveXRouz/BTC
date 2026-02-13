"""Unit tests for performance audit statistics functions."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

# Import from the perf_audit module (sibling file)
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perf_audit import compare_baselines, compute_stats


class TestComputeStats:
    """Tests for compute_stats function."""

    def test_compute_stats_basic(self) -> None:
        """compute_stats returns correct p50/p95/p99 for known input list."""
        # 20 values: 1, 2, 3, ..., 20
        times = [float(i) for i in range(1, 21)]
        stats = compute_stats(times)
        assert stats["p50"] == 11.0  # idx 10
        assert stats["p95"] == 20.0  # idx 19
        assert stats["p99"] == 20.0  # idx 19 (clamped)
        assert stats["min"] == 1.0
        assert stats["max"] == 20.0
        assert stats["mean"] == 10.5

    def test_compute_stats_empty(self) -> None:
        """compute_stats handles empty list, returns None for all metrics."""
        stats = compute_stats([])
        assert stats["p50"] is None
        assert stats["p95"] is None
        assert stats["p99"] is None
        assert stats["mean"] is None
        assert stats["min"] is None
        assert stats["max"] is None

    def test_compute_stats_single_value(self) -> None:
        """compute_stats with 1 value returns that value for all percentiles."""
        stats = compute_stats([42.5])
        assert stats["p50"] == 42.5
        assert stats["p95"] == 42.5
        assert stats["p99"] == 42.5
        assert stats["mean"] == 42.5
        assert stats["min"] == 42.5
        assert stats["max"] == 42.5


class TestBaselineComparison:
    """Tests for compare_baselines function."""

    def test_baseline_comparison_regression(self) -> None:
        """Regression detection flags p95 increase > 20%."""
        current = {
            "health": {"p95_ms": 120.0},  # 100 -> 120 = +20% (boundary)
            "user_list": {"p95_ms": 250.0},  # 100 -> 250 = +150% (regression)
        }
        baseline_data = {
            "endpoints": {
                "health": {"p95_ms": 100.0},
                "user_list": {"p95_ms": 100.0},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(baseline_data, f)
            f.flush()
            lines = compare_baselines(current, f.name)

        # user_list should be flagged as REGRESSION
        regression_lines = [line for line in lines if "REGRESSION" in line]
        assert len(regression_lines) >= 1
        assert any("user_list" in line for line in regression_lines)

    def test_baseline_comparison_improvement(self) -> None:
        """Improvement detection notes p95 decrease > 20%."""
        current = {
            "health": {"p95_ms": 50.0},  # 100 -> 50 = -50% (improvement)
        }
        baseline_data = {
            "endpoints": {
                "health": {"p95_ms": 100.0},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(baseline_data, f)
            f.flush()
            lines = compare_baselines(current, f.name)

        improved_lines = [line for line in lines if "IMPROVED" in line]
        assert len(improved_lines) >= 1
        assert any("health" in line for line in improved_lines)

    def test_baseline_comparison_stable(self) -> None:
        """Stable detection for p95 change within +/- 20%."""
        current = {
            "health": {"p95_ms": 105.0},  # 100 -> 105 = +5% (stable)
        }
        baseline_data = {
            "endpoints": {
                "health": {"p95_ms": 100.0},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(baseline_data, f)
            f.flush()
            lines = compare_baselines(current, f.name)

        stable_lines = [line for line in lines if "STABLE" in line]
        assert len(stable_lines) >= 1

    def test_baseline_file_not_found(self) -> None:
        """Missing baseline file returns warning."""
        lines = compare_baselines({"health": {"p95_ms": 50.0}}, "/nonexistent.json")
        assert len(lines) == 1
        assert "WARNING" in lines[0]
