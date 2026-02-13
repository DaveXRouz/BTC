"""Response Cache Middleware -- Redis-backed HTTP caching with ETag support.

Caches GET responses for configured paths with configurable TTL.
Falls back gracefully to no caching when Redis is unavailable.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from typing import TYPE_CHECKING

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

if TYPE_CHECKING:
    import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# Path prefix -> TTL in seconds
_CACHE_TTLS: dict[str, int] = {
    "/api/health": 10,
    "/api/oracle/daily": 300,
    "/api/oracle/users": 60,
    "/api/oracle/readings": 60,
}

_CACHE_PREFIX = "nps:cache:"


def _get_ttl(path: str) -> int | None:
    """Return cache TTL for a path, or None if not cacheable."""
    for prefix, ttl in _CACHE_TTLS.items():
        if path.startswith(prefix):
            return ttl
    return None


def _build_key(request: Request) -> str:
    """Build a unique cache key from request method, path, params, and auth."""
    auth = request.headers.get("authorization", "")
    auth_prefix = auth[:16] if len(auth) >= 16 else auth
    query_params = sorted(request.query_params.items())
    raw = f"{request.method}:{request.url.path}:{query_params}:{auth_prefix}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{_CACHE_PREFIX}{digest}"


async def _invalidate_related(redis: "aioredis.Redis", request: Request) -> None:
    """Invalidate cache entries related to the request path."""
    path = request.url.path
    if "/oracle/users" in path or "/oracle/reading" in path:
        try:
            cursor = "0"
            while cursor:
                cursor, keys = await redis.scan(
                    cursor=int(cursor), match=f"{_CACHE_PREFIX}*", count=100
                )
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as exc:
            logger.warning("Cache invalidation failed: %s", exc)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """Redis-backed response caching with ETag and cache invalidation."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Process request with caching layer and timing header."""
        start = time.perf_counter()
        try:
            response = await self._handle(request, call_next)
        except Exception:
            logger.exception("Cache middleware error, passing through")
            response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"
        return response

    async def _handle(self, request: Request, call_next) -> Response:
        """Core cache logic: check cache, serve or pass through."""
        # Only cache GET requests
        if request.method != "GET":
            response = await call_next(request)
            if request.method in ("POST", "PUT", "DELETE"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                redis = getattr(request.app.state, "redis", None)
                if redis is not None:
                    await _invalidate_related(redis, request)
            return response

        # Check if this path is cacheable
        ttl = _get_ttl(request.url.path)
        if ttl is None:
            return await call_next(request)

        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            response = await call_next(request)
            response.headers["X-Cache"] = "BYPASS"
            return response

        cache_key = _build_key(request)

        # Check If-None-Match (ETag)
        if_none_match = request.headers.get("if-none-match")

        # Try cache hit
        try:
            cached = await redis.get(cache_key)
        except Exception:
            cached = None

        if cached:
            entry = json.loads(cached)
            etag = entry.get("etag", "")
            if if_none_match and if_none_match.strip('"') == etag:
                return Response(
                    status_code=304,
                    headers={
                        "ETag": f'"{etag}"',
                        "X-Cache": "HIT",
                    },
                )
            body = base64.b64decode(entry["body"])
            return Response(
                content=body,
                status_code=entry["status"],
                headers={
                    "Content-Type": entry["content_type"],
                    "Cache-Control": f"public, max-age={ttl}",
                    "ETag": f'"{etag}"',
                    "X-Cache": "HIT",
                },
            )

        # Cache miss -- call downstream
        response = await call_next(request)

        # Only cache successful responses
        if response.status_code < 400:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk if isinstance(chunk, bytes) else chunk.encode()

            etag = hashlib.md5(body).hexdigest()  # noqa: S324 -- ETag, not security

            entry = json.dumps(
                {
                    "body": base64.b64encode(body).decode(),
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", "application/json"),
                    "etag": etag,
                }
            )

            try:
                await redis.setex(cache_key, ttl, entry)
            except Exception as exc:
                logger.warning("Cache write failed: %s", exc)

            return Response(
                content=body,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "Cache-Control": f"public, max-age={ttl}",
                    "ETag": f'"{etag}"',
                    "X-Cache": "MISS",
                },
            )

        response.headers["X-Cache"] = "SKIP"
        return response
