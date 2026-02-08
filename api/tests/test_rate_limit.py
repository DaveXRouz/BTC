"""Tests for rate limiting middleware."""

import pytest

from app.middleware.rate_limit import _SlidingWindow

# ─── Sliding Window Unit Tests ──────────────────────────────────────────────


def test_under_limit_allowed():
    limiter = _SlidingWindow()
    allowed, remaining, _ = limiter.is_allowed("test-key", limit=5, window=60)
    assert allowed is True
    assert remaining == 4


def test_at_limit_rejected():
    limiter = _SlidingWindow()
    for _ in range(5):
        limiter.is_allowed("test-key", limit=5, window=60)
    allowed, remaining, _ = limiter.is_allowed("test-key", limit=5, window=60)
    assert allowed is False
    assert remaining == 0


def test_different_keys_independent():
    limiter = _SlidingWindow()
    for _ in range(5):
        limiter.is_allowed("key-a", limit=5, window=60)
    # key-a is at limit
    allowed_a, _, _ = limiter.is_allowed("key-a", limit=5, window=60)
    assert allowed_a is False
    # key-b should still be allowed
    allowed_b, remaining_b, _ = limiter.is_allowed("key-b", limit=5, window=60)
    assert allowed_b is True
    assert remaining_b == 4


def test_reset_returns_positive():
    limiter = _SlidingWindow()
    _, _, reset = limiter.is_allowed("test-key", limit=5, window=60)
    assert reset > 0


# ─── HTTP Integration Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_headers_present(client):
    resp = await client.get("/api/oracle/users")
    assert "x-ratelimit-limit" in resp.headers
    assert "x-ratelimit-remaining" in resp.headers
    assert "x-ratelimit-reset" in resp.headers
