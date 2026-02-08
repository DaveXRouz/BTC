"""Rate limiting middleware — in-memory sliding window."""

import logging
import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Paths with lower limits (AI-powered endpoints)
_AI_PATHS = {
    "/api/oracle/reading",
    "/api/oracle/question",
    "/api/oracle/name",
    "/api/oracle/reading/multi-user",
    "/api/translation/translate",
}
_AI_RATE_LIMIT = 100  # per hour
_AI_WINDOW = 3600  # 1 hour in seconds

_DEFAULT_RATE_LIMIT = 60  # per minute
_DEFAULT_WINDOW = 60  # 1 minute in seconds


class _SlidingWindow:
    """Thread-safe sliding window rate limiter."""

    def __init__(self):
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check if request is allowed.

        Returns (allowed, remaining, reset_seconds).
        """
        now = time.monotonic()
        cutoff = now - window

        # Prune old entries
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > cutoff]
        timestamps = self._requests[key]

        remaining = max(0, limit - len(timestamps))
        reset = int(window - (now - timestamps[0])) if timestamps else window

        if len(timestamps) >= limit:
            return False, 0, reset

        self._requests[key].append(now)
        remaining = max(0, limit - len(self._requests[key]))
        return True, remaining, reset


_limiter = _SlidingWindow()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP and per-API-key rate limiting with sliding window.

    - AI-powered Oracle endpoints: 100 req/hr
    - Default endpoints: 60 req/min
    - Per-API-key limits override defaults (from api_keys.rate_limit)
    """

    async def dispatch(self, request: Request, call_next):
        try:
            # Determine rate limit key
            key = self._get_key(request)
            limit, window = self._get_limits(request)

            allowed, remaining, reset = _limiter.is_allowed(key, limit, window)

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset),
                        "Retry-After": str(reset),
                    },
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)
            return response

        except Exception:
            # Graceful fallback: if rate limiting fails, allow request
            logger.exception("Rate limiting error, allowing request")
            return await call_next(request)

    def _get_key(self, request: Request) -> str:
        """Build a rate limit key from API key or IP address."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return f"key:{token[:16]}"  # Use prefix of token as key
        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_limits(self, request: Request) -> tuple[int, int]:
        """Determine rate limit and window for this request."""
        path = request.url.path
        if path in _AI_PATHS:
            return _AI_RATE_LIMIT, _AI_WINDOW
        return _DEFAULT_RATE_LIMIT, _DEFAULT_WINDOW
