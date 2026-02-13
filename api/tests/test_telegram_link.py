"""Tests for Telegram link endpoints (Session 33)."""

import hashlib

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.database import get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.services.security import get_encryption_service

from tests.conftest import (
    TestSession,
    override_get_current_user,
    override_get_db,
    override_get_encryption_service,
)

TEST_API_KEY = "test-telegram-link-api-key-1234567890"
TEST_KEY_HASH = hashlib.sha256(TEST_API_KEY.encode()).hexdigest()
TEST_USER_ID = "tg-test-user-001"
TEST_CHAT_ID = 123456789


def _seed_user_and_api_key(db) -> None:
    """Insert a test user and API key for Telegram link tests."""
    db.execute(
        text(
            "INSERT INTO users (id, username, password_hash, role, is_active) "
            "VALUES (:uid, :uname, 'fakehash', 'user', 1)"
        ),
        {"uid": TEST_USER_ID, "uname": "tg_test_user"},
    )
    db.execute(
        text(
            "INSERT INTO api_keys (id, user_id, key_hash, name, scopes, rate_limit, is_active) "
            "VALUES (:kid, :uid, :khash, 'telegram-test', '', 60, 1)"
        ),
        {"kid": "apikey-tg-001", "uid": TEST_USER_ID, "khash": TEST_KEY_HASH},
    )
    db.commit()


def _seed_inactive_user_and_key(db) -> None:
    """Insert an inactive test user with an API key."""
    db.execute(
        text(
            "INSERT INTO users (id, username, password_hash, role, is_active) "
            "VALUES (:uid, :uname, 'fakehash', 'user', 0)"
        ),
        {"uid": "tg-inactive-user", "uname": "inactive_user"},
    )
    db.execute(
        text(
            "INSERT INTO api_keys (id, user_id, key_hash, name, scopes, rate_limit, is_active) "
            "VALUES (:kid, :uid, :khash, 'inactive-test', '', 60, 1)"
        ),
        {
            "kid": "apikey-tg-002",
            "uid": "tg-inactive-user",
            "khash": hashlib.sha256(b"inactive-key-abc").hexdigest(),
        },
    )
    db.commit()


def _seed_oracle_profile(db, user_id: str) -> None:
    """Insert a minimal oracle_users row linked to a user."""
    db.execute(
        text(
            "INSERT INTO oracle_users (name, birthday, mother_name, created_by) "
            "VALUES ('Test Profile', '2000-01-01', 'Test Mother', :uid)"
        ),
        {"uid": user_id},
    )
    db.commit()


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client():
    """Client without auth — for testing link endpoint (no auth required)."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_db():
    db = TestSession()
    try:
        _seed_user_and_api_key(db)
        yield db
    finally:
        db.close()


@pytest.mark.anyio
async def test_link_telegram_success(unauth_client, seeded_db):
    resp = await unauth_client.post(
        "/api/telegram/link",
        json={
            "telegram_chat_id": TEST_CHAT_ID,
            "telegram_username": "testbot",
            "api_key": TEST_API_KEY,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["telegram_chat_id"] == TEST_CHAT_ID
    assert data["username"] == "tg_test_user"
    assert data["user_id"] == TEST_USER_ID
    assert data["is_active"] is True


@pytest.mark.anyio
async def test_link_telegram_invalid_key(unauth_client, seeded_db):
    resp = await unauth_client.post(
        "/api/telegram/link",
        json={
            "telegram_chat_id": TEST_CHAT_ID,
            "telegram_username": "testbot",
            "api_key": "completely-invalid-key-that-does-not-exist",
        },
    )
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_link_telegram_inactive_user(unauth_client):
    db = TestSession()
    _seed_inactive_user_and_key(db)
    db.close()

    resp = await unauth_client.post(
        "/api/telegram/link",
        json={
            "telegram_chat_id": TEST_CHAT_ID,
            "telegram_username": "testbot",
            "api_key": "inactive-key-abc",
        },
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_link_telegram_upsert(unauth_client, seeded_db):
    # First link
    resp1 = await unauth_client.post(
        "/api/telegram/link",
        json={
            "telegram_chat_id": TEST_CHAT_ID,
            "telegram_username": "user1",
            "api_key": TEST_API_KEY,
        },
    )
    assert resp1.status_code == 200

    # Second link with same chat_id — should update, not duplicate
    resp2 = await unauth_client.post(
        "/api/telegram/link",
        json={
            "telegram_chat_id": TEST_CHAT_ID,
            "telegram_username": "user1_updated",
            "api_key": TEST_API_KEY,
        },
    )
    assert resp2.status_code == 200
    assert resp2.json()["telegram_username"] == "user1_updated"


@pytest.mark.anyio
async def test_status_linked_user(client, seeded_db):
    # Link first via unauth
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as unauth:
        await unauth.post(
            "/api/telegram/link",
            json={
                "telegram_chat_id": TEST_CHAT_ID,
                "telegram_username": "testbot",
                "api_key": TEST_API_KEY,
            },
        )

    resp = await client.get(f"/api/telegram/status/{TEST_CHAT_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["linked"] is True
    assert data["username"] == "tg_test_user"
    assert data["role"] == "user"


@pytest.mark.anyio
async def test_status_unlinked_user(client):
    resp = await client.get("/api/telegram/status/999999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["linked"] is False


@pytest.mark.anyio
async def test_unlink_telegram(client, seeded_db):
    # Link first
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as unauth:
        await unauth.post(
            "/api/telegram/link",
            json={
                "telegram_chat_id": TEST_CHAT_ID,
                "telegram_username": "testbot",
                "api_key": TEST_API_KEY,
            },
        )

    resp = await client.delete(f"/api/telegram/link/{TEST_CHAT_ID}")
    assert resp.status_code == 200
    assert resp.json()["detail"] == "Telegram account unlinked"

    # Status should now show not linked (is_active = False)
    status_resp = await client.get(f"/api/telegram/status/{TEST_CHAT_ID}")
    assert status_resp.json()["linked"] is False


@pytest.mark.anyio
async def test_profile_linked_user(client, seeded_db):
    # Seed an oracle profile
    db = TestSession()
    _seed_oracle_profile(db, TEST_USER_ID)
    db.close()

    # Link first
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as unauth:
        await unauth.post(
            "/api/telegram/link",
            json={
                "telegram_chat_id": TEST_CHAT_ID,
                "telegram_username": "testbot",
                "api_key": TEST_API_KEY,
            },
        )

    resp = await client.get(f"/api/telegram/profile/{TEST_CHAT_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Test Profile"
