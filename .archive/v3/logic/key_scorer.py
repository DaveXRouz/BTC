"""
Key Scorer -- Scoring Bridge for the Logic Layer
==================================================
Wraps engines.scoring.hybrid_score with LRU caching, threshold
filtering, batch scoring, top-N tracking, and score distribution.
Thread-safe.
"""

import heapq
import logging
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)

_LRU_MAX = 10000  # max cached scores


class KeyScorer:
    """High-performance key scoring with caching and analytics."""

    def __init__(self, context=None, threshold=0.0):
        """
        Args:
            context: optional dict passed to hybrid_score for moon/date alignment.
            threshold: minimum final_score to include in results (0.0 = keep all).
        """
        self._context = context
        self._threshold = threshold
        self._lock = threading.Lock()

        # LRU cache: key_int -> score_result dict
        self._cache = OrderedDict()

        # Top-N heap: list of (-score, key_int) -- min-heap by negated score
        self._top_heap = []
        self._top_set = set()  # for dedup
        self._top_n_limit = 100

        # Score distribution buckets: bucket_index -> count
        # bucket_index = int(score * 10), so 0..10
        self._distribution = {}

    # ---- Core scoring ----

    def score_key(self, key_int):
        """Score a single key, using cache if available.

        Args:
            key_int: integer key to score.

        Returns:
            dict from hybrid_score, or None if below threshold.
        """
        with self._lock:
            if key_int in self._cache:
                self._cache.move_to_end(key_int)
                result = self._cache[key_int]
                return result if result["final_score"] >= self._threshold else None

        # Cache miss -- compute
        from engines.scoring import hybrid_score

        result = hybrid_score(key_int, context=self._context)

        with self._lock:
            # Store in cache
            self._cache[key_int] = result
            self._cache.move_to_end(key_int)

            # Evict if over limit
            while len(self._cache) > _LRU_MAX:
                self._cache.popitem(last=False)

            # Update top-N
            self._update_top(key_int, result["final_score"])

            # Update distribution
            bucket = min(10, int(result["final_score"] * 10))
            self._distribution[bucket] = self._distribution.get(bucket, 0) + 1

        if result["final_score"] >= self._threshold:
            return result
        return None

    def score_batch(self, keys):
        """Score a batch of keys, returning results sorted by score descending.

        Args:
            keys: list of integer keys.

        Returns:
            list of (key_int, score_result) tuples, sorted by final_score desc.
            Keys below threshold are excluded.
        """
        results = []
        for key in keys:
            result = self.score_key(key)
            if result is not None:
                results.append((key, result))
        results.sort(key=lambda x: x[1]["final_score"], reverse=True)
        return results

    # ---- Top-N tracking ----

    def _update_top(self, key_int, score):
        """Maintain a heap of top-N scores. Must be called under lock."""
        if key_int in self._top_set:
            return

        if len(self._top_heap) < self._top_n_limit:
            heapq.heappush(self._top_heap, (score, key_int))
            self._top_set.add(key_int)
        elif score > self._top_heap[0][0]:
            _, evicted = heapq.heapreplace(self._top_heap, (score, key_int))
            self._top_set.discard(evicted)
            self._top_set.add(key_int)

    def get_top_n(self, n=100):
        """Return the top *n* scored keys of this run.

        Returns:
            list of (key_int, final_score) sorted by score descending.
        """
        with self._lock:
            items = sorted(self._top_heap, key=lambda x: x[0], reverse=True)
            return [(key, score) for score, key in items[:n]]

    # ---- Distribution ----

    def get_score_distribution(self):
        """Return histogram of scores in 0.1-wide buckets.

        Returns:
            dict mapping bucket label (str like '0.0-0.1') to count.
        """
        with self._lock:
            dist = {}
            for bucket_idx in range(11):
                lo = round(bucket_idx * 0.1, 1)
                hi = round(lo + 0.1, 1) if bucket_idx < 10 else 1.0
                label = "{:.1f}-{:.1f}".format(lo, hi)
                dist[label] = self._distribution.get(bucket_idx, 0)
            return dist

    # ---- Cache info ----

    def cache_size(self):
        """Return current cache size."""
        with self._lock:
            return len(self._cache)

    def clear_cache(self):
        """Clear the LRU cache."""
        with self._lock:
            self._cache.clear()
