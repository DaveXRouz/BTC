"""Health check endpoints."""

import logging

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.database import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check for Docker/load balancer."""
    return {"status": "healthy", "version": "4.0.0"}


@router.get("/ready")
async def readiness_check(request: Request):
    """Readiness probe — checks database and service connectivity."""
    checks = {}

    # Check PostgreSQL connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        checks["database"] = "unhealthy"

    # Check Redis connection
    redis = getattr(request.app.state, "redis", None)
    if redis:
        try:
            await redis.ping()
            checks["redis"] = "healthy"
        except Exception as exc:
            logger.warning("Redis health check failed: %s", exc)
            checks["redis"] = "unhealthy"
    else:
        checks["redis"] = "not_connected"

    # Scanner service is not deployed (Rust stub)
    checks["scanner_service"] = "not_deployed"

    # Oracle uses direct V3 engine imports (no gRPC needed)
    checks["oracle_service"] = "direct_mode"

    # Overall status: healthy if DB is up (core services only)
    core_healthy = checks["database"] == "healthy"
    return {
        "status": "healthy" if core_healthy else "degraded",
        "checks": checks,
    }


@router.get("/performance")
async def performance_stats():
    """Performance metrics (wraps V3 PerfMonitor pattern)."""
    # TODO: Implement performance tracking
    return {
        "uptime_seconds": 0,
        "requests_total": 0,
        "requests_per_minute": 0,
        "p95_response_ms": 0,
    }
