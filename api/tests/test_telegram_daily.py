"""Tests for Telegram daily preference endpoints (Session 35)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.services.security import get_encryption_service

from tests.conftest import (
    override_get_current_user,
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


# ─── GET preferences ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_get_preferences_not_found(client):
    """GET /telegram/daily/preferences/{chat_id} returns 404 for unknown chat."""
    resp = await client.get("/api/telegram/daily/preferences/999999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_get_preferences_by_chat_id(client):
    """GET /telegram/daily/preferences/{chat_id} returns correct data after creation."""
    # Create first
    await client.put(
        "/api/telegram/daily/preferences/12345",
        json={
            "daily_enabled": True,
            "delivery_time": "14:30",
            "timezone_offset_minutes": 210,
        },
    )

    resp = await client.get("/api/telegram/daily/preferences/12345")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chat_id"] == 12345
    assert data["daily_enabled"] is True
    assert data["delivery_time"] == "14:30"
    assert data["timezone_offset_minutes"] == 210


# ─── PUT preferences ────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_update_preferences_creates(client):
    """PUT /telegram/daily/preferences/{chat_id} creates new preference."""
    resp = await client.put(
        "/api/telegram/daily/preferences/12345",
        json={"daily_enabled": True, "delivery_time": "09:30"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chat_id"] == 12345
    assert data["daily_enabled"] is True
    assert data["delivery_time"] == "09:30"


@pytest.mark.anyio
async def test_update_preferences_invalid_time(client):
    """PUT with invalid time format returns 422."""
    resp = await client.put(
        "/api/telegram/daily/preferences/12345",
        json={"delivery_time": "invalid"},
    )
    assert resp.status_code == 422


# ─── POST delivered ──────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_mark_delivered(client):
    """POST /telegram/daily/delivered updates last_delivered_date."""
    # Create preference
    await client.put(
        "/api/telegram/daily/preferences/12345",
        json={"daily_enabled": True},
    )

    resp = await client.post(
        "/api/telegram/daily/delivered",
        json={"chat_id": 12345, "delivered_date": "2026-02-14"},
    )
    assert resp.status_code == 200

    # Verify
    resp2 = await client.get("/api/telegram/daily/preferences/12345")
    assert resp2.json()["last_delivered_date"] == "2026-02-14"


# ─── GET pending ─────────────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_get_pending_deliveries(client):
    """GET /telegram/daily/pending returns only enabled, undelivered users."""
    # Create enabled user with past delivery time
    await client.put(
        "/api/telegram/daily/preferences/11111",
        json={
            "daily_enabled": True,
            "delivery_time": "00:01",
            "timezone_offset_minutes": 0,
        },
    )
    # Create disabled user
    await client.put(
        "/api/telegram/daily/preferences/22222",
        json={"daily_enabled": False, "delivery_time": "00:01"},
    )

    resp = await client.get("/api/telegram/daily/pending")
    assert resp.status_code == 200
    pending = resp.json()
    chat_ids = [p["chat_id"] for p in pending]
    assert 11111 in chat_ids
    assert 22222 not in chat_ids


@pytest.mark.anyio
async def test_pending_excludes_already_delivered(client):
    """Users delivered today are not in pending list."""
    from datetime import date

    today = date.today().isoformat()

    await client.put(
        "/api/telegram/daily/preferences/12345",
        json={"daily_enabled": True, "delivery_time": "00:01"},
    )
    await client.post(
        "/api/telegram/daily/delivered",
        json={"chat_id": 12345, "delivered_date": today},
    )

    resp = await client.get("/api/telegram/daily/pending")
    assert resp.status_code == 200
    chat_ids = [p["chat_id"] for p in resp.json()]
    assert 12345 not in chat_ids
