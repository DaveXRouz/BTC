"""
Lightweight performance monitoring engine.

Thread-safe operation timing and counting with rolling sample windows.
Zero pip dependencies -- Python stdlib only.
"""

import time
import threading
import logging
from collections import deque

logger = logging.getLogger(__name__)

_SAMPLE_LIMIT = 1000


class PerfTimer:
    """Context manager for timing a block."""

    def __init__(self, monitor, name):
        self.monitor = monitor
        self.name = name
        self.elapsed = 0.0

    def __enter__(self):
        self.monitor.start(self.name)
        return self

    def __exit__(self, *args):
        self.elapsed = self.monitor.stop(self.name)


class PerfMonitor:
    """Thread-safe performance monitor that tracks operation timings and counts.

    Usage::

        perf.start("solve")
        # ... work ...
        elapsed = perf.stop("solve")

        # Or as a context manager:
        with perf.timer("solve") as t:
            # ... work ...
        print(t.elapsed)

        # Counters:
        perf.count("keys_tested", 500)
        print(perf.get_count("keys_tested"))

        # Aggregate stats:
        print(perf.summary())
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._timers: dict[str, float] = {}
        self._samples: dict[str, deque] = {}
        self._counters: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------

    def start(self, name: str) -> None:
        """Record start time for named operation."""
        with self._lock:
            self._timers[name] = time.perf_counter()

    def stop(self, name: str) -> float:
        """Calculate elapsed time since ``start(name)``.

        Appends the elapsed value (seconds) to a rolling deque of up to
        ``_SAMPLE_LIMIT`` samples and returns it.  Returns ``0.0`` if
        *name* was never started.
        """
        with self._lock:
            t0 = self._timers.pop(name, None)
            if t0 is None:
                return 0.0
            elapsed = time.perf_counter() - t0
            if name not in self._samples:
                self._samples[name] = deque(maxlen=_SAMPLE_LIMIT)
            self._samples[name].append(elapsed)
            return elapsed

    def timer(self, name: str) -> PerfTimer:
        """Return a context manager for timing a block.

        Example::

            with perf.timer("hash") as t:
                do_work()
            print(t.elapsed)
        """
        return PerfTimer(self, name)

    # ------------------------------------------------------------------
    # Counters
    # ------------------------------------------------------------------

    def count(self, name: str, n: int = 1) -> None:
        """Increment counter *name* by *n*."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + n

    def get_count(self, name: str) -> int:
        """Return current counter value (``0`` if not set)."""
        with self._lock:
            return self._counters.get(name, 0)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """Return a summary dict of all tracked operations.

        Each operation key maps to a dict with ``count``, ``min_ms``,
        ``max_ms``, ``avg_ms``, ``p95_ms``, and ``last_ms``.  A
        ``"counters"`` key holds all raw counter values.
        """
        with self._lock:
            result: dict = {}

            for name, samples in self._samples.items():
                if not samples:
                    result[name] = {
                        "count": 0,
                        "min_ms": 0.0,
                        "max_ms": 0.0,
                        "avg_ms": 0.0,
                        "p95_ms": 0.0,
                        "last_ms": 0.0,
                    }
                    continue

                sorted_s = sorted(samples)
                n = len(sorted_s)
                p95_idx = int(0.95 * n)
                # Clamp to last valid index
                if p95_idx >= n:
                    p95_idx = n - 1

                result[name] = {
                    "count": n,
                    "min_ms": sorted_s[0] * 1000,
                    "max_ms": sorted_s[-1] * 1000,
                    "avg_ms": (sum(sorted_s) / n) * 1000,
                    "p95_ms": sorted_s[p95_idx] * 1000,
                    "last_ms": samples[-1] * 1000,
                }

            result["counters"] = dict(self._counters)
            return result

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all timers, samples, and counters."""
        with self._lock:
            self._timers.clear()
            self._samples.clear()
            self._counters.clear()


# ------------------------------------------------------------------
# Module-level global instance
# ------------------------------------------------------------------

perf = PerfMonitor()
