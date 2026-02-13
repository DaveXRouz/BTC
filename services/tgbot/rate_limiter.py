"""Per-chat-ID sliding window rate limiter."""

import time
from collections import defaultdict

from . import config

_CLEANUP_INTERVAL = 100  # prune old entries every N calls


class RateLimiter:
    """Sliding window rate limiter — tracks timestamps per chat_id."""

    def __init__(self, max_per_minute: int | None = None) -> None:
        self.max_per_minute = max_per_minute or config.RATE_LIMIT_PER_MINUTE
        self._timestamps: dict[int, list[float]] = defaultdict(list)
        self._call_count: int = 0

    def is_allowed(self, chat_id: int) -> bool:
        """Return True if the chat_id is within the rate limit."""
        now = time.monotonic()
        window_start = now - 60.0

        # Prune old timestamps for this chat
        self._timestamps[chat_id] = [
            t for t in self._timestamps[chat_id] if t > window_start
        ]

        if len(self._timestamps[chat_id]) >= self.max_per_minute:
            return False

        self._timestamps[chat_id].append(now)

        # Periodic global cleanup
        self._call_count += 1
        if self._call_count >= _CLEANUP_INTERVAL:
            self._cleanup(now)
            self._call_count = 0

        return True

    def _cleanup(self, now: float) -> None:
        """Remove stale chat_id entries where all timestamps are expired."""
        window_start = now - 60.0
        stale = [
            cid
            for cid, ts in self._timestamps.items()
            if not ts or ts[-1] <= window_start
        ]
        for cid in stale:
            del self._timestamps[cid]


rate_limiter = RateLimiter()
