"""Rate limiting middleware using Redis."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP and per-API-key rate limiting using Redis sliding window.

    TODO: Implement with Redis
    - Default: 60 requests/minute per IP
    - API key users: configurable per-key limit (from api_keys.rate_limit)
    - Scanner endpoints: higher limits (streaming data)
    """

    async def dispatch(self, request: Request, call_next):
        # TODO: Check rate limit in Redis
        # TODO: Add X-RateLimit-* headers to response
        response = await call_next(request)
        return response
