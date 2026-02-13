"""Tests for the per-chat-ID rate limiter."""

import time
from unittest.mock import patch

from services.tgbot.rate_limiter import RateLimiter


def test_allows_under_limit():
    limiter = RateLimiter(max_per_minute=5)
    for _ in range(5):
        assert limiter.is_allowed(100) is True


def test_blocks_over_limit():
    limiter = RateLimiter(max_per_minute=3)
    for _ in range(3):
        assert limiter.is_allowed(200) is True
    assert limiter.is_allowed(200) is False


def test_window_expires():
    limiter = RateLimiter(max_per_minute=2)
    assert limiter.is_allowed(300) is True
    assert limiter.is_allowed(300) is True
    assert limiter.is_allowed(300) is False

    # Simulate time passing beyond 60s window
    future = time.monotonic() + 61
    with patch("time.monotonic", return_value=future):
        assert limiter.is_allowed(300) is True


def test_separate_chat_ids():
    limiter = RateLimiter(max_per_minute=2)
    assert limiter.is_allowed(400) is True
    assert limiter.is_allowed(400) is True
    assert limiter.is_allowed(400) is False

    # Different chat_id should be independent
    assert limiter.is_allowed(401) is True
    assert limiter.is_allowed(401) is True
