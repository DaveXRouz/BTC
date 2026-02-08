"""
Pattern Tracker -- Pattern Analysis for the Logic Layer
========================================================
Tracks batch statistics, finding analysis, and coverage maps.
Delegates persistence to HistoryManager.
"""

import logging
import threading

logger = logging.getLogger(__name__)


class PatternTracker:
    """Analyze patterns across scanned keys and findings."""

    def __init__(self, history_manager=None):
        self._hm = history_manager
        self._lock = threading.Lock()

        # Running batch aggregates
        self._batch_stats = {
            "total_keys": 0,
            "total_batches": 0,
            "entropy_sum": 0.0,
            "balance_sum": 0.0,
            "master_count": 0,
            "score_sum": 0.0,
        }

        # Analyzed findings
        self._finding_analysis = []

        # Coverage map: {puzzle_number_str: [(start, end, keys_tested), ...]}
        self._coverage = {}

    # ---- Batch recording ----

    def record_batch(self, keys, scores):
        """Aggregate entropy, digit balance, master number rate from a batch.

        Args:
            keys: list of int keys.
            scores: list of score result dicts (from hybrid_score).
        """
        from engines.math_analysis import entropy, digit_balance
        from engines.numerology import is_master_number

        batch_size = len(keys)
        if batch_size == 0:
            return

        ent_sum = 0.0
        bal_sum = 0.0
        master_cnt = 0
        score_total = 0.0

        for i, key in enumerate(keys):
            ent_sum += entropy(key)
            bal_sum += digit_balance(key)
            if is_master_number(key):
                master_cnt += 1
            if i < len(scores) and scores[i]:
                score_total += scores[i].get("final_score", 0)

        with self._lock:
            self._batch_stats["total_keys"] += batch_size
            self._batch_stats["total_batches"] += 1
            self._batch_stats["entropy_sum"] += ent_sum
            self._batch_stats["balance_sum"] += bal_sum
            self._batch_stats["master_count"] += master_cnt
            self._batch_stats["score_sum"] += score_total

    # ---- Finding recording ----

    def record_finding(self, key_int, score_result, has_balance=False):
        """Deep analysis of a finding (hit or high-scoring key).

        Args:
            key_int: the integer key.
            score_result: dict from hybrid_score.
            has_balance: whether a balance was found.
        """
        from engines.math_analysis import entropy, digit_balance, prime_factors
        from engines.numerology import is_master_number, numerology_reduce
        from engines.scoring import hybrid_score

        analysis = {
            "key": key_int,
            "final_score": score_result.get("final_score", 0),
            "math_score": score_result.get("math_score", 0),
            "numerology_score": score_result.get("numerology_score", 0),
            "entropy": entropy(key_int),
            "digit_balance": digit_balance(key_int),
            "is_master": is_master_number(key_int),
            "reduced": numerology_reduce(sum(int(d) for d in str(abs(key_int)))),
            "has_balance": has_balance,
            "prime_factor_count": (
                len(prime_factors(key_int)) if key_int < 10**9 else -1
            ),
        }

        with self._lock:
            self._finding_analysis.append(analysis)
            # Keep bounded
            if len(self._finding_analysis) > 1000:
                self._finding_analysis = self._finding_analysis[-500:]

    # ---- Coverage ----

    def update_coverage(self, puzzle_number, range_start, range_end, keys_tested):
        """Record that a range was scanned for a puzzle.

        Args:
            puzzle_number: int puzzle identifier.
            range_start: start of range scanned.
            range_end: end of range scanned.
            keys_tested: number of keys actually tested in that range.
        """
        key = str(puzzle_number)
        with self._lock:
            if key not in self._coverage:
                self._coverage[key] = []
            self._coverage[key].append((range_start, range_end, keys_tested))

        # Persist via history manager
        if self._hm:
            self._hm.set_coverage(self._get_coverage_snapshot())

    def _get_coverage_snapshot(self):
        """Return a serializable snapshot of coverage data."""
        with self._lock:
            result = {}
            for puz, ranges in self._coverage.items():
                result[puz] = [{"start": s, "end": e, "keys": k} for s, e, k in ranges]
            return result

    def get_coverage(self, puzzle_number):
        """Return coverage stats and least-covered suggestion for a puzzle.

        Returns:
            dict with total_ranges, total_keys, ranges list, least_covered_gap.
        """
        key = str(puzzle_number)
        with self._lock:
            ranges = self._coverage.get(key, [])

        if not ranges:
            return {
                "total_ranges": 0,
                "total_keys": 0,
                "ranges": [],
                "least_covered_gap": None,
            }

        total_keys = sum(r[2] for r in ranges)
        sorted_ranges = sorted(ranges, key=lambda r: r[0])

        # Find the largest gap between scanned ranges
        gaps = []
        for i in range(len(sorted_ranges) - 1):
            gap_start = sorted_ranges[i][1]
            gap_end = sorted_ranges[i + 1][0]
            if gap_end > gap_start:
                gaps.append((gap_start, gap_end, gap_end - gap_start))

        least_covered = None
        if gaps:
            biggest = max(gaps, key=lambda g: g[2])
            least_covered = {"start": biggest[0], "end": biggest[1], "size": biggest[2]}

        return {
            "total_ranges": len(ranges),
            "total_keys": total_keys,
            "ranges": [(r[0], r[1]) for r in sorted_ranges],
            "least_covered_gap": least_covered,
        }

    # ---- Aggregate stats ----

    def get_pattern_stats(self):
        """Return aggregate distributions and stats from all batches and findings.

        Returns:
            dict with batch averages and finding analysis summary.
        """
        with self._lock:
            bs = dict(self._batch_stats)
            findings = list(self._finding_analysis)

        total = bs["total_keys"]
        result = {
            "total_keys": total,
            "total_batches": bs["total_batches"],
            "avg_entropy": round(bs["entropy_sum"] / max(total, 1), 4),
            "avg_balance": round(bs["balance_sum"] / max(total, 1), 4),
            "master_rate": round(bs["master_count"] / max(total, 1), 6),
            "avg_score": round(bs["score_sum"] / max(total, 1), 4),
            "total_findings": len(findings),
        }

        # Finding analysis summary
        if findings:
            result["finding_avg_score"] = round(
                sum(f["final_score"] for f in findings) / len(findings), 4
            )
            result["finding_avg_entropy"] = round(
                sum(f["entropy"] for f in findings) / len(findings), 4
            )
            result["finding_master_rate"] = round(
                sum(1 for f in findings if f["is_master"]) / len(findings), 4
            )
            result["finding_balance_rate"] = round(
                sum(1 for f in findings if f["has_balance"]) / len(findings), 4
            )
        else:
            result["finding_avg_score"] = 0.0
            result["finding_avg_entropy"] = 0.0
            result["finding_master_rate"] = 0.0
            result["finding_balance_rate"] = 0.0

        # Persist stats
        if self._hm:
            self._hm.set_stats(result)

        return result
