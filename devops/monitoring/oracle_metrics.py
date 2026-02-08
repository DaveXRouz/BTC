"""
Thread-safe RPC metrics collector for the Oracle service.

Tracks per-RPC timing (p50/p95/p99/avg/max), error counts by type,
and readings per hour using deque-based rolling windows.

Zero pip dependencies — Python stdlib only.
"""

import time
import threading
from collections import deque


class OracleMetrics:
    """Collects Oracle RPC performance metrics with a rolling time window.

    Parameters
    ----------
    window_seconds : int
        How far back to retain samples (default 3600 = 1 hour).
    """

    def __init__(self, window_seconds=3600):
        self._lock = threading.Lock()
        self._window = window_seconds
        # {rpc_name: deque of (timestamp, duration_ms)}
        self._rpcs = {}
        # {rpc_name: deque of (timestamp, error_type_str)}
        self._errors = {}
        self._start_time = time.time()

    def record_rpc(self, name, duration_ms):
        """Record a successful RPC call with its duration in milliseconds."""
        now = time.time()
        with self._lock:
            if name not in self._rpcs:
                self._rpcs[name] = deque()
            self._rpcs[name].append((now, duration_ms))

    def record_error(self, name, error_type):
        """Record an RPC error.

        Parameters
        ----------
        name : str
            RPC method name.
        error_type : str
            Error class name or description.
        """
        now = time.time()
        with self._lock:
            if name not in self._errors:
                self._errors[name] = deque()
            self._errors[name].append((now, error_type))

    def _cleanup(self, now):
        """Remove samples older than the window. Must be called under lock."""
        cutoff = now - self._window
        for dq in self._rpcs.values():
            while dq and dq[0][0] < cutoff:
                dq.popleft()
        for dq in self._errors.values():
            while dq and dq[0][0] < cutoff:
                dq.popleft()

    def get_snapshot(self):
        """Return a JSON-serializable metrics snapshot.

        Returns
        -------
        dict
            {
                "uptime_seconds": int,
                "window_seconds": int,
                "rpcs": {
                    "MethodName": {
                        "count": int,
                        "avg_ms": float,
                        "p50_ms": float,
                        "p95_ms": float,
                        "p99_ms": float,
                        "max_ms": float,
                    }, ...
                },
                "errors": {
                    "total_count": int,
                    "rate_percent": float,
                    "by_rpc": {"MethodName": int, ...},
                    "by_type": {"ErrorType": int, ...},
                },
                "readings_per_hour": float,
            }
        """
        now = time.time()
        with self._lock:
            self._cleanup(now)

            rpcs_snapshot = {}
            total_rpc_count = 0

            for name, dq in self._rpcs.items():
                if not dq:
                    continue
                durations = sorted(d for _, d in dq)
                n = len(durations)
                total_rpc_count += n

                rpcs_snapshot[name] = {
                    "count": n,
                    "avg_ms": round(sum(durations) / n, 2),
                    "p50_ms": round(durations[_percentile_idx(n, 50)], 2),
                    "p95_ms": round(durations[_percentile_idx(n, 95)], 2),
                    "p99_ms": round(durations[_percentile_idx(n, 99)], 2),
                    "max_ms": round(durations[-1], 2),
                }

            # Error aggregation
            total_errors = 0
            errors_by_rpc = {}
            errors_by_type = {}
            for name, dq in self._errors.items():
                count = len(dq)
                if count == 0:
                    continue
                total_errors += count
                errors_by_rpc[name] = count
                for _, etype in dq:
                    errors_by_type[etype] = errors_by_type.get(etype, 0) + 1

            total_calls = total_rpc_count + total_errors
            error_rate = (
                round((total_errors / total_calls * 100), 2) if total_calls > 0 else 0.0
            )

            # Readings per hour estimate
            elapsed = now - self._start_time
            if elapsed > 0:
                readings_per_hour = round(total_rpc_count / elapsed * 3600, 1)
            else:
                readings_per_hour = 0.0

            return {
                "uptime_seconds": int(elapsed),
                "window_seconds": self._window,
                "rpcs": rpcs_snapshot,
                "errors": {
                    "total_count": total_errors,
                    "rate_percent": error_rate,
                    "by_rpc": errors_by_rpc,
                    "by_type": errors_by_type,
                },
                "readings_per_hour": readings_per_hour,
            }

    def reset(self):
        """Clear all collected metrics. For testing only."""
        with self._lock:
            self._rpcs.clear()
            self._errors.clear()
            self._start_time = time.time()


def _percentile_idx(n, pct):
    """Return the index for the given percentile in a sorted list of length n."""
    idx = int(pct / 100.0 * n)
    return min(idx, n - 1)


# Module-level singleton
metrics = OracleMetrics()
