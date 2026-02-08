"""
Range Optimizer -- Smart Range Selection for Puzzle Scanning
=============================================================
Selects optimal scanning ranges based on coverage gaps and
numerology alignment. Thread-safe.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# Known Bitcoin puzzle ranges (puzzle_number -> (min_key, max_key))
# These are the known bit-length ranges for the Bitcoin puzzle.
PUZZLE_RANGES = {}
for i in range(1, 161):
    if i == 1:
        PUZZLE_RANGES[1] = (1, 1)
    else:
        PUZZLE_RANGES[i] = (2 ** (i - 1), 2**i - 1)


class RangeOptimizer:
    """Smart range selection for puzzle scanning."""

    def __init__(self):
        self._lock = threading.Lock()
        # {puzzle_number: [(start, end), ...]}
        self._coverage = {}

    # ---- Scanned range tracking ----

    def mark_scanned(self, puzzle_number, start, end):
        """Record a scanned range for a puzzle.

        Args:
            puzzle_number: int puzzle identifier.
            start: range start (inclusive).
            end: range end (inclusive).
        """
        with self._lock:
            if puzzle_number not in self._coverage:
                self._coverage[puzzle_number] = []
            self._coverage[puzzle_number].append((start, end))

    # ---- Coverage map ----

    def get_coverage_map(self, puzzle_number):
        """Return coverage statistics for a puzzle.

        Returns:
            dict with total_range, scanned_count, coverage_pct, gaps.
        """
        prange = PUZZLE_RANGES.get(puzzle_number)
        if prange is None:
            # Unknown puzzle -- assume 256-bit range
            prange = (1, 2**256 - 1)

        total_range = prange[1] - prange[0] + 1

        with self._lock:
            ranges = list(self._coverage.get(puzzle_number, []))

        if not ranges:
            return {
                "total_range": total_range,
                "scanned_count": 0,
                "coverage_pct": 0.0,
                "gaps": [{"start": prange[0], "end": prange[1]}],
            }

        # Merge overlapping ranges to count unique keys scanned
        sorted_ranges = sorted(ranges, key=lambda r: r[0])
        merged = [sorted_ranges[0]]
        for start, end in sorted_ranges[1:]:
            prev_start, prev_end = merged[-1]
            if start <= prev_end + 1:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

        scanned_count = sum(e - s + 1 for s, e in merged)
        coverage_pct = (scanned_count / total_range * 100) if total_range > 0 else 0.0

        # Find gaps
        gaps = []
        # Gap before first merged range
        if merged[0][0] > prange[0]:
            gaps.append({"start": prange[0], "end": merged[0][0] - 1})
        # Gaps between merged ranges
        for i in range(len(merged) - 1):
            gap_start = merged[i][1] + 1
            gap_end = merged[i + 1][0] - 1
            if gap_end >= gap_start:
                gaps.append({"start": gap_start, "end": gap_end})
        # Gap after last merged range
        if merged[-1][1] < prange[1]:
            gaps.append({"start": merged[-1][1] + 1, "end": prange[1]})

        return {
            "total_range": total_range,
            "scanned_count": scanned_count,
            "coverage_pct": round(coverage_pct, 6),
            "gaps": gaps,
        }

    # ---- Smart range selection ----

    def get_next_range(self, puzzle_number, batch_size=1000):
        """Select the next range to scan based on coverage gaps.

        Picks the largest gap and returns a batch_size chunk from it.

        Args:
            puzzle_number: puzzle identifier.
            batch_size: number of keys in the returned range.

        Returns:
            (start, end) tuple.
        """
        coverage = self.get_coverage_map(puzzle_number)
        gaps = coverage.get("gaps", [])

        if not gaps:
            # Fully covered (extremely unlikely) -- rescan from beginning
            prange = PUZZLE_RANGES.get(puzzle_number, (1, 2**256 - 1))
            return (prange[0], prange[0] + batch_size - 1)

        # Pick the largest gap
        largest_gap = max(gaps, key=lambda g: g["end"] - g["start"])
        start = largest_gap["start"]
        end = min(start + batch_size - 1, largest_gap["end"])
        return (start, end)

    # ---- Favorable ranges (numerology-aligned) ----

    def get_favorable_ranges(self, puzzle_number, count=5):
        """Return ranges with high numerology alignment.

        Picks *count* starting points within the puzzle range whose
        numerology reduction falls on power numbers.

        Args:
            puzzle_number: puzzle identifier.
            count: number of ranges to return.

        Returns:
            list of (start, end) tuples.
        """
        from engines.numerology import numerology_reduce, is_master_number

        prange = PUZZLE_RANGES.get(puzzle_number)
        if prange is None:
            prange = (1, 2**256 - 1)

        range_min, range_max = prange
        range_size = range_max - range_min + 1
        batch_size = 1000

        # Sample candidate starting points spread across the range
        # We pick evenly spaced samples and score them
        power_numbers = {1, 8, 9, 11, 22, 33}
        candidates = []

        # Determine sample spacing
        num_samples = min(count * 20, 200)
        if range_size <= num_samples:
            step = 1
        else:
            step = range_size // num_samples

        pos = range_min
        for _ in range(num_samples):
            if pos > range_max:
                break
            digit_sum = sum(int(d) for d in str(pos))
            reduced = numerology_reduce(digit_sum)
            score = 0.0
            if is_master_number(pos):
                score = 1.0
            elif reduced in power_numbers:
                score = 0.8
            elif reduced in {3, 5, 7}:
                score = 0.6
            else:
                score = 0.3
            candidates.append((pos, score))
            pos += step

        # Sort by score descending, take top *count*
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = []
        for start, _ in candidates[:count]:
            end = min(start + batch_size - 1, range_max)
            results.append((start, end))

        return results
