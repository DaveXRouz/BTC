"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def health_check():
    """Basic health check for Docker/load balancer."""
    return {"status": "healthy", "version": "4.0.0"}


@router.get("/ready")
async def readiness_check():
    """Readiness probe — checks database and service connectivity."""
    checks = {}

    # TODO: Check PostgreSQL connection
    checks["database"] = "healthy"

    # TODO: Check Redis connection
    checks["redis"] = "healthy"

    # TODO: Check Scanner gRPC connection
    checks["scanner_service"] = "unknown"

    # TODO: Check Oracle gRPC connection
    checks["oracle_service"] = "unknown"

    all_healthy = all(v == "healthy" for v in checks.values())
    return {
        "status": "healthy" if all_healthy else "degraded",
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
