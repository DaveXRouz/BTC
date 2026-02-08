"""Tests for authentication middleware — JWT, API keys, and scope enforcement."""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.middleware.auth import (
    _expand_scopes,
    _role_to_scopes,
    _try_api_key_auth,
    _try_jwt_auth,
    create_access_token,
)
from app.orm.api_key import APIKey
from app.orm.user import User


@pytest.fixture
def db():
    """Fresh in-memory DB for auth tests."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create a test user in the DB."""
    import bcrypt as _bcrypt

    pw_hash = _bcrypt.hashpw(b"testpass", _bcrypt.gensalt()).decode("utf-8")
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        password_hash=pw_hash,
        role="user",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def test_api_key(db, test_user):
    """Create a test API key in the DB. Returns (raw_key, APIKey)."""
    raw_key = "test-api-key-raw-value"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = APIKey(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        key_hash=key_hash,
        name="Test Key",
        scopes="oracle:read,oracle:write",
        rate_limit=100,
    )
    db.add(api_key)
    db.commit()
    return raw_key, api_key


# ─── JWT Tests ──────────────────────────────────────────────────────────────


def test_create_and_decode_jwt():
    token = create_access_token("user-123", "alice", "admin")
    result = _try_jwt_auth(token)
    assert result is not None
    assert result["user_id"] == "user-123"
    assert result["username"] == "alice"
    assert result["role"] == "admin"
    assert result["auth_type"] == "jwt"
    assert "oracle:admin" in result["scopes"]


def test_invalid_jwt_returns_none():
    result = _try_jwt_auth("not-a-valid-jwt-token")
    assert result is None


def test_expired_jwt_returns_none():
    from jose import jwt
    from app.config import settings

    payload = {
        "sub": "user-1",
        "username": "old",
        "role": "user",
        "scopes": [],
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }
    token = jwt.encode(payload, settings.api_secret_key, algorithm="HS256")
    result = _try_jwt_auth(token)
    assert result is None


# ─── API Key Tests ──────────────────────────────────────────────────────────


def test_api_key_auth_valid(db, test_user, test_api_key):
    raw_key, _ = test_api_key
    result = _try_api_key_auth(raw_key, db)
    assert result is not None
    assert result["user_id"] == test_user.id
    assert result["auth_type"] == "api_key"
    assert "oracle:read" in result["scopes"]


def test_api_key_auth_invalid(db):
    result = _try_api_key_auth("nonexistent-key", db)
    assert result is None


def test_api_key_auth_revoked(db, test_user, test_api_key):
    raw_key, api_key = test_api_key
    api_key.is_active = False
    db.commit()
    result = _try_api_key_auth(raw_key, db)
    assert result is None


def test_api_key_auth_expired(db, test_user, test_api_key):
    raw_key, api_key = test_api_key
    # Use naive datetime for SQLite compatibility
    api_key.expires_at = datetime(2020, 1, 1)
    db.commit()
    result = _try_api_key_auth(raw_key, db)
    assert result is None


def test_api_key_updates_last_used(db, test_user, test_api_key):
    raw_key, api_key = test_api_key
    assert api_key.last_used is None
    _try_api_key_auth(raw_key, db)
    db.refresh(api_key)
    assert api_key.last_used is not None


# ─── Scope Tests ────────────────────────────────────────────────────────────


def test_scope_hierarchy_admin_implies_read():
    expanded = _expand_scopes(["oracle:admin"])
    assert "oracle:read" in expanded
    assert "oracle:write" in expanded
    assert "oracle:admin" in expanded


def test_scope_hierarchy_write_implies_read():
    expanded = _expand_scopes(["oracle:write"])
    assert "oracle:read" in expanded
    assert "oracle:admin" not in expanded


def test_scope_hierarchy_read_only():
    expanded = _expand_scopes(["oracle:read"])
    assert "oracle:read" in expanded
    assert "oracle:write" not in expanded
    assert "oracle:admin" not in expanded


def test_role_to_scopes_admin():
    scopes = _role_to_scopes("admin")
    assert "oracle:admin" in scopes
    assert "scanner:admin" in scopes
    assert "admin" in scopes


def test_role_to_scopes_user():
    scopes = _role_to_scopes("user")
    assert "oracle:write" in scopes
    assert "oracle:admin" not in scopes


def test_role_to_scopes_readonly():
    scopes = _role_to_scopes("readonly")
    assert "oracle:read" in scopes
    assert "oracle:write" not in scopes


def test_role_to_scopes_unknown_defaults_readonly():
    scopes = _role_to_scopes("unknown_role")
    assert scopes == _role_to_scopes("readonly")


# ─── Scope Enforcement (via HTTP) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_readonly_cannot_create_user(readonly_client):
    resp = await readonly_client.post(
        "/api/oracle/users",
        json={"name": "Test User", "birthday": "1990-01-01", "mother_name": "Mom"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_readonly_can_list_users(readonly_client):
    resp = await readonly_client.get("/api/oracle/users")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_readonly_cannot_delete_user(readonly_client):
    # Readonly user tries to delete — should get 403 from scope check
    # (even if user doesn't exist, scope check happens first)
    resp = await readonly_client.delete("/api/oracle/users/1")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_audit(client):
    resp = await client.get("/api/oracle/audit")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_readonly_cannot_access_audit(readonly_client):
    resp = await readonly_client.get("/api/oracle/audit")
    assert resp.status_code == 403
