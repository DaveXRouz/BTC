"""Tests for admin health monitoring endpoints (Session 39)."""

import json
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session as DBSession

from app.orm.audit_log import OracleAuditLog
from app.orm.oracle_reading import OracleReading

# ─── Helper ──────────────────────────────────────────────────────────────────


def _seed_audit_logs(db_session_factory, count: int = 5, success: bool = True):
    """Insert sample audit logs for testing."""
    db: DBSession = db_session_factory()
    try:
        for i in range(count):
            entry = OracleAuditLog(
                action="oracle_reading.create" if success else "auth.failed",
                resource_type="oracle_reading" if success else "auth",
                resource_id=i + 1 if success else None,
                success=success,
                ip_address="127.0.0.1",
                details=json.dumps({"sign_type": "time", "index": i}),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(entry)
        db.commit()
    finally:
        db.close()


def _seed_readings(db_session_factory, count: int = 3):
    """Insert sample oracle readings for analytics tests."""
    db: DBSession = db_session_factory()
    try:
        for i in range(count):
            reading = OracleReading(
                user_id=1,
                sign_type="time" if i % 2 == 0 else "name",
                sign_value=f"12:0{i}:00",
                question="test question",
                reading_result=json.dumps({"confidence": {"score": 75 + i, "level": "high"}}),
                created_at=datetime.now(timezone.utc),
            )
            db.add(reading)
        db.commit()
    finally:
        db.close()


# ─── Unauthenticated probe endpoints ────────────────────────────────────────


@pytest.mark.anyio
async def test_basic_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.anyio
async def test_readiness_check(client):
    resp = await client.get("/api/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert "checks" in data
    assert "database" in data["checks"]


@pytest.mark.anyio
async def test_performance_stats(client):
    resp = await client.get("/api/health/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "uptime_seconds" in data


# ─── Admin: /health/detailed ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_detailed_health_admin(client):
    resp = await client.get("/api/health/detailed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded", "unhealthy")
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert "system" in data
    system = data["system"]
    assert "python_version" in system
    assert "process_memory_mb" in system
    assert "cpu_count" in system
    assert "platform" in system
    assert "services" in data
    services = data["services"]
    assert "database" in services
    assert "api" in services
    assert "telegram" in services
    assert "nginx" in services


@pytest.mark.anyio
async def test_detailed_health_forbidden_readonly(readonly_client):
    resp = await readonly_client.get("/api/health/detailed")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_detailed_health_services_shape(client):
    resp = await client.get("/api/health/detailed")
    data = resp.json()
    for name, service in data["services"].items():
        assert "status" in service, f"Service {name} missing status"


# ─── Admin: /health/logs ─────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_logs_default(client):
    resp = await client.get("/api/health/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert "logs" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["logs"], list)


@pytest.mark.anyio
async def test_logs_with_data(client):
    """Seed audit logs and verify they show up."""
    from tests.conftest import TestSession

    _seed_audit_logs(TestSession, count=3, success=True)
    resp = await client.get("/api/health/logs")
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["logs"]) >= 3
    for log in data["logs"]:
        assert "id" in log
        assert "action" in log
        assert "severity" in log
        assert log["severity"] in ("info", "warning", "error", "critical")


@pytest.mark.anyio
async def test_logs_search_filter(client):
    from tests.conftest import TestSession

    _seed_audit_logs(TestSession, count=2, success=True)
    resp = await client.get("/api/health/logs?search=oracle_reading")
    data = resp.json()
    assert data["total"] >= 2
    for log in data["logs"]:
        assert "oracle_reading" in log["action"]


@pytest.mark.anyio
async def test_logs_severity_filter(client):
    from tests.conftest import TestSession

    _seed_audit_logs(TestSession, count=2, success=False)
    resp = await client.get("/api/health/logs?severity=error")
    data = resp.json()
    for log in data["logs"]:
        assert log["severity"] == "error"


@pytest.mark.anyio
async def test_logs_pagination(client):
    from tests.conftest import TestSession

    _seed_audit_logs(TestSession, count=10, success=True)
    resp = await client.get("/api/health/logs?limit=3&offset=0")
    data = resp.json()
    assert len(data["logs"]) <= 3
    assert data["limit"] == 3
    assert data["offset"] == 0


@pytest.mark.anyio
async def test_logs_forbidden_readonly(readonly_client):
    resp = await readonly_client.get("/api/health/logs")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_logs_time_window(client):
    resp = await client.get("/api/health/logs?hours=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["time_window_hours"] == 1


# ─── Admin: /health/analytics ───────────────────────────────────────────────


@pytest.mark.anyio
async def test_analytics_empty(client):
    resp = await client.get("/api/health/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert "readings_per_day" in data
    assert "readings_by_type" in data
    assert "confidence_trend" in data
    assert "popular_hours" in data
    assert "totals" in data
    totals = data["totals"]
    assert totals["total_readings"] == 0
    assert totals["most_popular_type"] is None


@pytest.mark.anyio
async def test_analytics_with_readings(client):
    """Seed readings and verify analytics returns correct structure.

    Note: SQLite DATE casting differs from PostgreSQL, so we verify
    structure rather than exact counts. Production uses PostgreSQL.
    """
    from tests.conftest import TestSession

    _seed_readings(TestSession, count=5)
    resp = await client.get("/api/health/analytics?days=30")
    data = resp.json()
    assert isinstance(data["totals"]["total_readings"], int)
    assert isinstance(data["readings_per_day"], list)
    assert isinstance(data["readings_by_type"], list)
    assert isinstance(data["totals"]["error_count"], int)


@pytest.mark.anyio
async def test_analytics_period_parameter(client):
    resp = await client.get("/api/health/analytics?days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["period_days"] == 7


@pytest.mark.anyio
async def test_analytics_forbidden_readonly(readonly_client):
    resp = await readonly_client.get("/api/health/analytics")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_analytics_totals_shape(client):
    resp = await client.get("/api/health/analytics")
    data = resp.json()
    totals = data["totals"]
    assert "total_readings" in totals
    assert "avg_confidence" in totals
    assert "most_popular_type" in totals
    assert "most_active_hour" in totals
    assert "error_count" in totals
