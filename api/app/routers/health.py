"""Health check endpoints — basic probes (unauthenticated) + admin monitoring."""

import json as json_mod
import logging
import os
import platform
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import cast, Date, Float, extract, func
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.middleware.auth import require_scope
from app.orm.audit_log import OracleAuditLog
from app.orm.oracle_reading import OracleReading
from app.services.audit import AuditService, get_audit_service

logger = logging.getLogger(__name__)

router = APIRouter()

_server_start_time = time.time()


def _get_process_memory_mb() -> float:
    """Get current process RSS in megabytes, cross-platform."""
    try:
        import resource as resource_mod

        usage = resource_mod.getrusage(resource_mod.RUSAGE_SELF)
        rss = usage.ru_maxrss
        if platform.system() == "Darwin":
            return round(rss / (1024 * 1024), 1)  # macOS: bytes
        return round(rss / 1024, 1)  # Linux: KB
    except (ImportError, AttributeError):
        return 0.0


def _derive_severity(entry: OracleAuditLog) -> str:
    """Derive log severity from audit log entry properties."""
    if not entry.success:
        if "auth" in (entry.action or ""):
            return "critical"
        return "error"
    action = entry.action or ""
    if "delete" in action or "deactivate" in action:
        return "warning"
    return "info"


# ─── Unauthenticated probes (Docker / load balancer) ─────────────────────────


@router.get("")
async def health_check():
    """Basic health check for Docker/load balancer."""
    return {"status": "healthy", "version": "4.0.0"}


@router.get("/ready")
async def readiness_check(request: Request):
    """Readiness probe — checks database and service connectivity."""
    checks = {}

    try:
        with engine.connect() as conn:
            from sqlalchemy import text

            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        checks["database"] = "unhealthy"

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

    checks["scanner_service"] = "not_deployed"
    checks["oracle_service"] = "direct_mode"

    core_healthy = checks["database"] == "healthy"
    return {
        "status": "healthy" if core_healthy else "degraded",
        "checks": checks,
    }


@router.get("/performance")
async def performance_stats():
    """Performance metrics (wraps legacy PerfMonitor pattern)."""
    return {
        "uptime_seconds": 0,
        "requests_total": 0,
        "requests_per_minute": 0,
        "p95_response_ms": 0,
    }


# ─── Admin-only monitoring endpoints ─────────────────────────────────────────


@router.get("/detailed")
async def detailed_health(
    request: Request,
    _user: dict = Depends(require_scope("admin")),
):
    """Detailed system health — admin only."""
    from sqlalchemy import text

    checks: dict = {}

    # 1. Database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            try:
                db_info = conn.execute(
                    text("SELECT pg_database_size(current_database()) as size_bytes")
                ).first()
                size_bytes = db_info.size_bytes if db_info else None
            except Exception:
                size_bytes = None
        checks["database"] = {
            "status": "healthy",
            "type": "postgresql",
            "size_bytes": size_bytes,
        }
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        checks["database"] = {"status": "unhealthy", "error": str(exc)}

    # 2. Redis
    redis = getattr(request.app.state, "redis", None)
    if redis:
        try:
            info = await redis.info("memory")
            await redis.ping()
            checks["redis"] = {
                "status": "healthy",
                "used_memory_bytes": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
            }
        except Exception as exc:
            checks["redis"] = {"status": "unhealthy", "error": str(exc)}
    else:
        checks["redis"] = {"status": "not_connected"}

    # 3. Oracle gRPC
    oracle_channel = getattr(request.app.state, "oracle_channel", None)
    if oracle_channel:
        try:
            import grpc

            grpc.channel_ready_future(oracle_channel).result(timeout=1)
            checks["oracle_service"] = {"status": "healthy", "mode": "grpc"}
        except Exception:
            checks["oracle_service"] = {"status": "unhealthy", "mode": "grpc"}
    else:
        checks["oracle_service"] = {"status": "direct_mode", "mode": "legacy"}

    # 4. Scanner (stub)
    checks["scanner_service"] = {"status": "not_deployed"}

    # 5. API self-check
    checks["api"] = {
        "status": "healthy",
        "version": "4.0.0",
        "python_version": platform.python_version(),
    }

    # 6. Telegram
    telegram_token = os.environ.get("NPS_BOT_TOKEN")
    checks["telegram"] = {
        "status": "configured" if telegram_token else "not_configured",
    }

    # 7. Nginx (external)
    checks["nginx"] = {"status": "external", "note": "Check via Docker health"}

    uptime_seconds = time.time() - _server_start_time

    return {
        "status": ("healthy" if checks["database"]["status"] == "healthy" else "degraded"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(uptime_seconds),
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "process_memory_mb": _get_process_memory_mb(),
        },
        "services": checks,
    }


@router.get("/logs")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    severity: str | None = Query(None, description="Filter: info, warning, error, critical"),
    action: str | None = Query(None, description="Filter by action type"),
    resource_type: str | None = Query(None),
    success: bool | None = Query(None),
    search: str | None = Query(None, description="Search in action and details"),
    hours: int = Query(24, ge=1, le=720, description="Time window in hours"),
    _user: dict = Depends(require_scope("admin")),
    audit: AuditService = Depends(get_audit_service),
):
    """Query audit logs with filtering — admin only."""
    effective_success = success
    if severity == "error":
        effective_success = False
    elif severity == "critical":
        effective_success = False
    elif severity == "info":
        if effective_success is None:
            effective_success = True

    entries, total = audit.query_logs_extended(
        action=action,
        resource_type=resource_type,
        success=effective_success,
        search=search,
        hours=hours,
        limit=limit,
        offset=offset,
    )

    logs = []
    for entry in entries:
        derived_severity = _derive_severity(entry)
        if severity and derived_severity != severity:
            continue
        details = None
        if entry.details:
            try:
                details = json_mod.loads(entry.details)
            except (json_mod.JSONDecodeError, TypeError):
                details = {"raw": entry.details}
        logs.append(
            {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "success": entry.success,
                "ip_address": entry.ip_address,
                "details": details,
                "severity": derived_severity,
            }
        )

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
        "time_window_hours": hours,
    }


@router.get("/analytics")
async def reading_analytics(
    days: int = Query(30, ge=1, le=365, description="Time range in days"),
    _user: dict = Depends(require_scope("admin")),
    db: Session = Depends(get_db),
):
    """Reading analytics for admin dashboard — admin only."""
    since = date.today() - timedelta(days=days)

    # Total readings in period
    total_readings = (
        db.query(func.count())
        .select_from(OracleReading)
        .filter(cast(OracleReading.created_at, Date) >= since)
        .scalar()
        or 0
    )

    # Readings per day
    readings_per_day_rows = (
        db.query(
            cast(OracleReading.created_at, Date).label("date"),
            func.count().label("count"),
        )
        .filter(cast(OracleReading.created_at, Date) >= since)
        .group_by(cast(OracleReading.created_at, Date))
        .order_by(cast(OracleReading.created_at, Date))
        .all()
    )
    readings_per_day = [
        {"date": str(row.date), "count": row.count} for row in readings_per_day_rows
    ]

    # Readings by type
    readings_by_type_rows = (
        db.query(
            OracleReading.sign_type.label("type"),
            func.count().label("count"),
        )
        .filter(cast(OracleReading.created_at, Date) >= since)
        .group_by(OracleReading.sign_type)
        .order_by(func.count().desc())
        .all()
    )
    readings_by_type = [
        {"type": row.type or "unknown", "count": row.count} for row in readings_by_type_rows
    ]

    # Confidence trend — JSONB path extraction (PostgreSQL only)
    confidence_trend: list[dict] = []
    try:
        confidence_rows = (
            db.query(
                cast(OracleReading.created_at, Date).label("date"),
                func.avg(
                    cast(
                        OracleReading.reading_result["confidence"]["score"].as_string(),
                        Float,
                    )
                ).label("avg_confidence"),
            )
            .filter(
                cast(OracleReading.created_at, Date) >= since,
                OracleReading.reading_result.isnot(None),
            )
            .group_by(cast(OracleReading.created_at, Date))
            .order_by(cast(OracleReading.created_at, Date))
            .all()
        )
        confidence_trend = [
            {
                "date": str(row.date),
                "avg_confidence": (
                    round(float(row.avg_confidence), 1) if row.avg_confidence is not None else 0.0
                ),
            }
            for row in confidence_rows
        ]
    except Exception:
        confidence_trend = []

    # Popular hours
    popular_hours_rows = (
        db.query(
            extract("hour", OracleReading.created_at).label("hour"),
            func.count().label("count"),
        )
        .filter(cast(OracleReading.created_at, Date) >= since)
        .group_by(extract("hour", OracleReading.created_at))
        .order_by(extract("hour", OracleReading.created_at))
        .all()
    )
    popular_hours = [{"hour": int(row.hour), "count": row.count} for row in popular_hours_rows]

    # Error count from audit log
    error_count = (
        db.query(func.count())
        .select_from(OracleAuditLog)
        .filter(
            OracleAuditLog.success == False,  # noqa: E712
            OracleAuditLog.timestamp >= datetime.now(timezone.utc) - timedelta(days=days),
        )
        .scalar()
        or 0
    )

    most_popular_type = readings_by_type[0]["type"] if readings_by_type else None
    most_active_hour = (
        max(popular_hours, key=lambda h: h["count"])["hour"] if popular_hours else None
    )

    return {
        "period_days": days,
        "readings_per_day": readings_per_day,
        "readings_by_type": readings_by_type,
        "confidence_trend": confidence_trend,
        "popular_hours": popular_hours,
        "totals": {
            "total_readings": total_readings,
            "avg_confidence": (
                round(
                    sum(c["avg_confidence"] for c in confidence_trend) / len(confidence_trend),
                    1,
                )
                if confidence_trend
                else 0.0
            ),
            "most_popular_type": most_popular_type,
            "most_active_hour": most_active_hour,
            "error_count": error_count,
        },
    }
