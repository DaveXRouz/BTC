"""Tests for admin endpoints — /api/admin."""

import uuid
from datetime import date

import bcrypt as _bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.orm.oracle_user import OracleUser
from app.orm.user import User

# ─── Test DB Setup ────────────────────────────────────────────────────────────

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

ADMIN_ID = str(uuid.uuid4())
USER_A_ID = str(uuid.uuid4())
USER_B_ID = str(uuid.uuid4())


def _override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def _make_admin():
    return {
        "user_id": ADMIN_ID,
        "username": "test-admin",
        "role": "admin",
        "scopes": [
            "oracle:admin",
            "oracle:write",
            "oracle:read",
            "scanner:admin",
            "scanner:write",
            "scanner:read",
            "vault:admin",
            "vault:write",
            "vault:read",
            "admin",
        ],
        "auth_type": "test",
        "api_key_hash": None,
        "rate_limit": None,
    }


def _make_regular_user():
    return {
        "user_id": USER_A_ID,
        "username": "regular-user",
        "role": "user",
        "scopes": ["oracle:write", "oracle:read", "scanner:read", "vault:read"],
        "auth_type": "test",
        "api_key_hash": None,
        "rate_limit": None,
    }


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def seed_data():
    """Seed test users and one oracle profile into the DB."""
    db = _TestSession()
    pw_hash = _bcrypt.hashpw(b"testpass123", _bcrypt.gensalt()).decode("utf-8")
    db.add(User(id=ADMIN_ID, username="admin-user", password_hash=pw_hash, role="admin"))
    db.add(User(id=USER_A_ID, username="user-a", password_hash=pw_hash, role="user"))
    db.add(
        User(
            id=USER_B_ID,
            username="user-b",
            password_hash=pw_hash,
            role="user",
            is_active=False,
        )
    )
    db.add(
        OracleUser(
            name="Test Profile",
            name_persian="پروفایل تست",
            birthday=date(1990, 5, 15),
            mother_name="Test Mother",
            created_by=USER_A_ID,
        )
    )
    db.commit()
    db.close()


@pytest.fixture
async def admin_client(seed_data):
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _make_admin
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def user_client(seed_data):
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _make_regular_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── List Users ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users_admin(admin_client):
    """Admin can list all system users."""
    resp = await admin_client.get("/api/admin/users")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["users"]) == 3
    for u in data["users"]:
        assert "password_hash" not in u


@pytest.mark.asyncio
async def test_list_users_with_search(admin_client):
    """Admin can search users by username."""
    resp = await admin_client.get("/api/admin/users?search=user-a")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["users"][0]["username"] == "user-a"


@pytest.mark.asyncio
async def test_list_users_with_pagination(admin_client):
    """Pagination works."""
    resp = await admin_client.get("/api/admin/users?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 1
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_list_users_forbidden(user_client):
    """Non-admin gets 403."""
    resp = await user_client.get("/api/admin/users")
    assert resp.status_code == 403


# ─── Get User ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_detail(admin_client):
    """Admin can get user detail."""
    resp = await admin_client.get(f"/api/admin/users/{USER_A_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "user-a"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_get_user_not_found(admin_client):
    """Non-existent user returns 404."""
    resp = await admin_client.get(f"/api/admin/users/{uuid.uuid4()}")
    assert resp.status_code == 404


# ─── Update Role ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_role(admin_client):
    """Admin can change another user's role."""
    resp = await admin_client.patch(
        f"/api/admin/users/{USER_A_ID}/role",
        json={"role": "admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_update_own_role_blocked(admin_client):
    """Admin cannot change own role."""
    resp = await admin_client.patch(
        f"/api/admin/users/{ADMIN_ID}/role",
        json={"role": "user"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_update_role_invalid(admin_client):
    """Invalid role rejected by validation."""
    resp = await admin_client.patch(
        f"/api/admin/users/{USER_A_ID}/role",
        json={"role": "superadmin"},
    )
    assert resp.status_code == 422


# ─── Reset Password ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_password(admin_client):
    """Admin can reset a user's password."""
    resp = await admin_client.post(f"/api/admin/users/{USER_A_ID}/reset-password")
    assert resp.status_code == 200
    data = resp.json()
    assert "temporary_password" in data
    assert len(data["temporary_password"]) > 8
    assert "message" in data


@pytest.mark.asyncio
async def test_reset_password_not_found(admin_client):
    """Reset for non-existent user returns 404."""
    resp = await admin_client.post(f"/api/admin/users/{uuid.uuid4()}/reset-password")
    assert resp.status_code == 404


# ─── Update Status ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_deactivate_user(admin_client):
    """Admin can deactivate a user."""
    resp = await admin_client.patch(
        f"/api/admin/users/{USER_A_ID}/status",
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_activate_user(admin_client):
    """Admin can activate a previously inactive user."""
    resp = await admin_client.patch(
        f"/api/admin/users/{USER_B_ID}/status",
        json={"is_active": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_deactivate_self_blocked(admin_client):
    """Admin cannot deactivate self."""
    resp = await admin_client.patch(
        f"/api/admin/users/{ADMIN_ID}/status",
        json={"is_active": False},
    )
    assert resp.status_code == 400


# ─── Stats ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_stats(admin_client):
    """Admin can get system statistics."""
    resp = await admin_client.get("/api/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] == 3
    assert data["active_users"] == 2
    assert data["inactive_users"] == 1
    assert data["total_oracle_profiles"] == 1
    assert "users_by_role" in data


@pytest.mark.asyncio
async def test_get_stats_forbidden(user_client):
    """Non-admin gets 403 on stats."""
    resp = await user_client.get("/api/admin/stats")
    assert resp.status_code == 403


# ─── Oracle Profiles ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_profiles(admin_client):
    """Admin can list oracle profiles."""
    resp = await admin_client.get("/api/admin/profiles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["profiles"][0]["name"] == "Test Profile"


@pytest.mark.asyncio
async def test_list_profiles_search(admin_client):
    """Search filters oracle profiles."""
    resp = await admin_client.get("/api/admin/profiles?search=nonexistent")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_profile(admin_client):
    """Admin can delete an oracle profile."""
    # Find the profile ID
    list_resp = await admin_client.get("/api/admin/profiles")
    profile_id = list_resp.json()["profiles"][0]["id"]

    resp = await admin_client.delete(f"/api/admin/profiles/{profile_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Profile"

    # Verify it's gone
    list_after = await admin_client.get("/api/admin/profiles")
    assert list_after.json()["total"] == 0


@pytest.mark.asyncio
async def test_delete_profile_not_found(admin_client):
    """Non-existent profile returns 404."""
    resp = await admin_client.delete("/api/admin/profiles/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_profiles_forbidden(user_client):
    """Non-admin gets 403 on profiles."""
    resp = await user_client.get("/api/admin/profiles")
    assert resp.status_code == 403
