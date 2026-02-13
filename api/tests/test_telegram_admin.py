"""Tests for Telegram admin endpoints (Session 36)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.services.security import get_encryption_service

from tests.conftest import (
    override_get_current_user,
    override_get_current_user_readonly,
    override_get_db,
    override_get_encryption_service,
)


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def readonly_client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user_readonly
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── GET /admin/stats ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_admin_stats_endpoint_returns_data(client):
    """API stats endpoint returns correct JSON shape."""
    resp = await client.get("/api/telegram/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "readings_today" in data
    assert "readings_total" in data
    assert "error_count_24h" in data
    assert "uptime_seconds" in data
    assert "db_size_mb" in data
    assert isinstance(data["total_users"], int)


@pytest.mark.anyio
async def test_admin_stats_requires_admin_scope(readonly_client):
    """Non-admin tokens get 403."""
    resp = await readonly_client.get("/api/telegram/admin/stats")
    assert resp.status_code == 403


# ─── GET /admin/users ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_admin_users_endpoint_returns_paginated(client):
    """API users endpoint returns paginated data."""
    resp = await client.get("/api/telegram/admin/users?limit=5&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "users" in data
    assert isinstance(data["users"], list)


@pytest.mark.anyio
async def test_admin_users_requires_admin_scope(readonly_client):
    """Non-admin tokens get 403."""
    resp = await readonly_client.get("/api/telegram/admin/users")
    assert resp.status_code == 403


# ─── POST /admin/audit ───────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_admin_audit_creates_entry(client):
    """Audit endpoint creates an entry."""
    resp = await client.post(
        "/api/telegram/admin/audit",
        json={
            "action": "telegram_admin_stats",
            "resource_type": "system",
            "success": True,
            "details": '{"chat_id": 12345}',
        },
    )
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Audit entry created"


# ─── GET /admin/linked_chats ─────────────────────────────────────────────────


@pytest.mark.anyio
async def test_linked_chats_returns_list(client):
    """Linked chats endpoint returns chat_ids list."""
    resp = await client.get("/api/telegram/admin/linked_chats")
    assert resp.status_code == 200
    data = resp.json()
    assert "chat_ids" in data
    assert isinstance(data["chat_ids"], list)


# ─── POST /internal/notify ──────────────────────────────────────────────────


@pytest.mark.anyio
async def test_internal_notify_endpoint_accepts_event(client):
    """Internal notify endpoint processes events."""
    resp = await client.post(
        "/api/telegram/internal/notify",
        json={"event_type": "startup", "data": {"service": "api"}},
    )
    assert resp.status_code == 200
    assert resp.json()["event_type"] == "startup"
