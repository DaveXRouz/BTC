"""Tests for the Redis-backed response cache middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from app.middleware.cache import ResponseCacheMiddleware, _get_ttl

# ─── Helpers ────────────────────────────────────────────────────────────────


def _create_test_app(redis_mock: AsyncMock | None = None) -> FastAPI:
    """Create a minimal FastAPI app with cache middleware for testing."""
    app = FastAPI()
    app.add_middleware(ResponseCacheMiddleware)

    # Directly set redis on app state (startup events don't fire with ASGITransport)
    app.state.redis = redis_mock

    @app.get("/api/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/oracle/users")
    async def user_list() -> dict:
        return {"users": [], "total": 0}

    @app.get("/api/oracle/users/{user_id}")
    async def user_detail(user_id: int) -> dict:
        return {"id": user_id, "name": "test"}

    @app.get("/api/oracle/readings")
    async def readings() -> dict:
        return {"readings": [], "total": 0}

    @app.post("/api/oracle/users")
    async def create_user() -> JSONResponse:
        return JSONResponse({"id": 1, "name": "new"}, status_code=201)

    @app.post("/api/oracle/reading")
    async def create_reading() -> dict:
        return {"reading_id": 1, "type": "time"}

    @app.get("/api/other/endpoint")
    async def other() -> dict:
        return {"data": "not cached"}

    @app.get("/api/health/error")
    async def error_endpoint() -> JSONResponse:
        return JSONResponse({"error": "bad"}, status_code=500)

    return app


def _make_redis_mock() -> AsyncMock:
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    redis.delete = AsyncMock()
    return redis


# ─── Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_cache_miss_first_request() -> None:
    """First GET request returns X-Cache: MISS."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-cache") == "MISS"


@pytest.mark.anyio
async def test_cache_hit_second_request() -> None:
    """Second identical GET request returns X-Cache: HIT."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)

    # Simulate cached entry on second call
    stored_entry: str | None = None

    async def _setex(key: str, ttl: int, value: str) -> None:
        nonlocal stored_entry
        stored_entry = value

    async def _get(key: str) -> str | None:
        return stored_entry

    redis.setex = AsyncMock(side_effect=_setex)
    redis.get = AsyncMock(side_effect=_get)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First request: MISS
        resp1 = await client.get("/api/health")
        assert resp1.headers.get("x-cache") == "MISS"

        # Second request: HIT
        resp2 = await client.get("/api/health")
        assert resp2.headers.get("x-cache") == "HIT"
        assert resp2.status_code == 200


@pytest.mark.anyio
async def test_cache_not_applied_to_post() -> None:
    """POST requests are never served from cache."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/oracle/users", json={"name": "test"})
        assert resp.status_code == 201
        assert resp.headers.get("x-cache") is None


@pytest.mark.anyio
async def test_cache_control_header_on_get() -> None:
    """GET responses include Cache-Control header with max-age."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert "max-age" in resp.headers.get("cache-control", "")


@pytest.mark.anyio
async def test_cache_control_no_store_on_post() -> None:
    """POST responses include Cache-Control: no-store."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/oracle/users", json={"name": "test"})
        assert "no-store" in resp.headers.get("cache-control", "")


@pytest.mark.anyio
async def test_etag_present_on_cached() -> None:
    """Cached GET responses include ETag header."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.headers.get("etag") is not None


@pytest.mark.anyio
async def test_etag_if_none_match_returns_304() -> None:
    """Request with matching If-None-Match returns 304 Not Modified."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)

    stored_entry: str | None = None

    async def _setex(key: str, ttl: int, value: str) -> None:
        nonlocal stored_entry
        stored_entry = value

    async def _get(key: str) -> str | None:
        return stored_entry

    redis.setex = AsyncMock(side_effect=_setex)
    redis.get = AsyncMock(side_effect=_get)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First request to populate cache
        resp1 = await client.get("/api/health")
        etag = resp1.headers.get("etag", "").strip('"')

        # Second request with matching ETag
        resp2 = await client.get("/api/health", headers={"If-None-Match": f'"{etag}"'})
        assert resp2.status_code == 304


@pytest.mark.anyio
async def test_etag_if_none_match_mismatch() -> None:
    """Request with non-matching If-None-Match returns full response."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)

    stored_entry: str | None = None

    async def _setex(key: str, ttl: int, value: str) -> None:
        nonlocal stored_entry
        stored_entry = value

    async def _get(key: str) -> str | None:
        return stored_entry

    redis.setex = AsyncMock(side_effect=_setex)
    redis.get = AsyncMock(side_effect=_get)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First request to populate cache
        await client.get("/api/health")

        # Second request with wrong ETag
        resp2 = await client.get("/api/health", headers={"If-None-Match": '"wrong-etag"'})
        assert resp2.status_code == 200
        assert resp2.headers.get("x-cache") == "HIT"


@pytest.mark.anyio
async def test_cache_invalidation_on_user_create() -> None:
    """POST to /oracle/users invalidates user list cache entries."""
    redis = _make_redis_mock()
    redis.scan = AsyncMock(return_value=(0, ["nps:cache:abc123"]))
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/oracle/users", json={"name": "test"})
        redis.scan.assert_called()


@pytest.mark.anyio
async def test_cache_invalidation_on_reading_create() -> None:
    """POST to /oracle/reading invalidates reading list cache."""
    redis = _make_redis_mock()
    redis.scan = AsyncMock(return_value=(0, ["nps:cache:def456"]))
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/oracle/reading", json={"datetime": "2024-01-01"})
        redis.scan.assert_called()


@pytest.mark.anyio
async def test_cache_different_auth_different_entry() -> None:
    """Different auth tokens produce separate cache entries."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)

    calls: list[str] = []

    async def _setex(key: str, ttl: int, value: str) -> None:
        calls.append(key)

    redis.setex = AsyncMock(side_effect=_setex)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/health", headers={"Authorization": "Bearer aaaa1111bbbb2222cccc"})
        await client.get("/api/health", headers={"Authorization": "Bearer zzzz9999yyyy8888xxxx"})

    assert len(calls) == 2
    assert calls[0] != calls[1]


@pytest.mark.anyio
async def test_cache_graceful_without_redis() -> None:
    """When Redis is None, requests work normally (no cache, no error)."""
    app = _create_test_app(redis_mock=None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-cache") == "BYPASS"


@pytest.mark.anyio
async def test_error_responses_not_cached() -> None:
    """4xx and 5xx responses are NOT stored in cache."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health/error")
        assert resp.status_code == 500
        assert resp.headers.get("x-cache") == "SKIP"
        redis.setex.assert_not_called()


@pytest.mark.anyio
async def test_response_time_header() -> None:
    """All responses include X-Response-Time header with milliseconds."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        rt = resp.headers.get("x-response-time")
        assert rt is not None
        assert rt.endswith("ms")
        # Parse the numeric part
        ms_value = float(rt.replace("ms", ""))
        assert ms_value >= 0


@pytest.mark.anyio
async def test_cache_ttl_expiry() -> None:
    """Cached entry uses correct TTL when stored via setex."""
    redis = _make_redis_mock()
    app = _create_test_app(redis)

    ttl_used: int | None = None

    async def _setex(key: str, ttl: int, value: str) -> None:
        nonlocal ttl_used
        ttl_used = ttl

    redis.setex = AsyncMock(side_effect=_setex)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/health")

    # /api/health has TTL of 10 seconds
    assert ttl_used == 10


# ─── Unit tests for helper functions ────────────────────────────────────────


def test_get_ttl_health() -> None:
    """Health endpoint has 10s TTL."""
    assert _get_ttl("/api/health") == 10


def test_get_ttl_daily() -> None:
    """Daily endpoint has 300s TTL."""
    assert _get_ttl("/api/oracle/daily") == 300


def test_get_ttl_users() -> None:
    """Users endpoint has 60s TTL."""
    assert _get_ttl("/api/oracle/users") == 60


def test_get_ttl_uncached() -> None:
    """Non-cached endpoint returns None."""
    assert _get_ttl("/api/auth/login") is None
