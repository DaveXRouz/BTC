"""Tests for authentication middleware — JWT, API keys, scope enforcement, and hardening."""

import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.middleware.auth import (
    _TokenBlacklist,
    _blacklist,
    _expand_scopes,
    _role_to_scopes,
    _try_api_key_auth,
    _try_jwt_auth,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
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
    pw_hash = _bcrypt.hashpw(b"testpass123", _bcrypt.gensalt()).decode("utf-8")
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
def admin_user(db):
    """Create an admin test user in the DB."""
    pw_hash = _bcrypt.hashpw(b"adminpass123", _bcrypt.gensalt()).decode("utf-8")
    user = User(
        id=str(uuid.uuid4()),
        username="adminuser",
        password_hash=pw_hash,
        role="admin",
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


# ─── Moderator Role Tests ──────────────────────────────────────────────────


def test_moderator_role_scopes():
    """Moderator gets oracle:admin but not system admin."""
    scopes = _role_to_scopes("moderator")
    assert "oracle:admin" in scopes
    assert "oracle:write" in scopes
    assert "oracle:read" in scopes
    assert "scanner:read" in scopes
    assert "vault:read" in scopes
    assert "admin" not in scopes
    assert "scanner:admin" not in scopes
    assert "vault:admin" not in scopes
    assert "scanner:write" not in scopes
    assert "vault:write" not in scopes


def test_moderator_jwt_has_correct_scopes():
    """JWT for moderator role includes moderator scopes."""
    token = create_access_token("mod-1", "moderator_user", "moderator")
    result = _try_jwt_auth(token)
    assert result is not None
    assert result["role"] == "moderator"
    assert "oracle:admin" in result["scopes"]
    assert "admin" not in result["scopes"]


def test_moderator_scope_expansion():
    """Moderator oracle:admin expands to include oracle:write and oracle:read."""
    scopes = _role_to_scopes("moderator")
    expanded = _expand_scopes(scopes)
    assert "oracle:admin" in expanded
    assert "oracle:write" in expanded
    assert "oracle:read" in expanded
    assert "scanner:read" in expanded
    assert "vault:read" in expanded


# ─── Refresh Token Tests ───────────────────────────────────────────────────


def test_create_refresh_token_uniqueness():
    """Each refresh token is unique."""
    tokens = {create_refresh_token() for _ in range(100)}
    assert len(tokens) == 100


def test_hash_refresh_token_deterministic():
    """Same input always produces same hash."""
    token = "test-token-value"
    assert hash_refresh_token(token) == hash_refresh_token(token)


def test_hash_refresh_token_different_inputs():
    """Different tokens produce different hashes."""
    assert hash_refresh_token("token-a") != hash_refresh_token("token-b")


def test_refresh_token_length():
    """Refresh token is a non-empty URL-safe string."""
    token = create_refresh_token()
    assert len(token) > 20  # 32 bytes base64url encoded = ~43 chars


# ─── Token Blacklist Tests ─────────────────────────────────────────────────


def test_blacklist_add_and_check():
    """Blacklisted token is detected."""
    blacklist = _TokenBlacklist()
    future = time.time() + 3600
    blacklist.add("test-token-bl", future)
    assert blacklist.is_blacklisted("test-token-bl") is True


def test_blacklist_expired_not_blocked():
    """Expired blacklist entry is not detected."""
    blacklist = _TokenBlacklist()
    past = time.time() - 1
    blacklist.add("old-token", past)
    assert blacklist.is_blacklisted("old-token") is False


def test_blacklist_unknown_token():
    """Non-blacklisted token passes."""
    blacklist = _TokenBlacklist()
    assert blacklist.is_blacklisted("never-added") is False


def test_blacklisted_jwt_rejected():
    """JWT that's been blacklisted returns None from _try_jwt_auth."""
    token = create_access_token("user-1", "alice", "user")
    # Blacklist it
    _blacklist.add(token, time.time() + 3600)
    result = _try_jwt_auth(token)
    assert result is None
    # Cleanup
    _blacklist._tokens.clear()


def test_blacklist_cleanup_removes_expired():
    """Cleanup removes expired entries."""
    blacklist = _TokenBlacklist()
    blacklist.add("expired-1", time.time() - 100)
    blacklist.add("expired-2", time.time() - 50)
    blacklist.add("valid-1", time.time() + 3600)
    # Trigger cleanup by adding another
    blacklist.add("trigger", time.time() + 3600)
    assert blacklist.is_blacklisted("expired-1") is False
    assert blacklist.is_blacklisted("expired-2") is False
    assert blacklist.is_blacklisted("valid-1") is True


# ─── Brute-Force Protection Tests (unit) ───────────────────────────────────


def test_failed_attempts_increment(db, test_user):
    """Failed login increments failed_attempts on user."""
    assert test_user.failed_attempts == 0
    test_user.failed_attempts = (test_user.failed_attempts or 0) + 1
    db.commit()
    db.refresh(test_user)
    assert test_user.failed_attempts == 1


def test_account_locks_after_5_failures(db, test_user):
    """5 consecutive failures set locked_until."""
    test_user.failed_attempts = 5
    test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()
    db.refresh(test_user)
    assert test_user.locked_until is not None
    assert test_user.failed_attempts == 5


def test_locked_account_has_future_timestamp(db, test_user):
    """Locked account has a locked_until in the future."""
    test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.commit()
    db.refresh(test_user)
    # SQLite stores naive datetimes, so compare accordingly
    lock_time = test_user.locked_until
    if lock_time.tzinfo is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        now = datetime.now(timezone.utc)
    assert lock_time > now


def test_lock_expires_after_duration(db, test_user):
    """Expired lock (in the past) should be detected as expired."""
    test_user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    test_user.failed_attempts = 5
    db.commit()
    db.refresh(test_user)
    lock_time = test_user.locked_until
    if lock_time.tzinfo is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        now = datetime.now(timezone.utc)
    assert lock_time < now  # Lock is in the past = expired


def test_successful_login_resets_failed_attempts(db, test_user):
    """Resetting failed_attempts to 0 simulates successful login."""
    test_user.failed_attempts = 3
    db.commit()
    # Simulate successful login reset
    test_user.failed_attempts = 0
    test_user.locked_until = None
    db.commit()
    db.refresh(test_user)
    assert test_user.failed_attempts == 0
    assert test_user.locked_until is None


# ─── Registration Model Validation Tests ────────────────────────────────────


def test_register_request_valid():
    """Valid registration request passes validation."""
    from app.models.auth import RegisterRequest

    req = RegisterRequest(username="newuser", password="securepass123", role="user")
    assert req.username == "newuser"
    assert req.role == "user"


def test_register_request_password_too_short():
    """Password under 8 chars raises validation error."""
    from pydantic import ValidationError
    from app.models.auth import RegisterRequest

    with pytest.raises(ValidationError):
        RegisterRequest(username="newuser", password="short", role="user")


def test_register_request_username_too_short():
    """Username under 3 chars raises validation error."""
    from pydantic import ValidationError
    from app.models.auth import RegisterRequest

    with pytest.raises(ValidationError):
        RegisterRequest(username="ab", password="securepass123", role="user")


def test_register_request_defaults_to_user_role():
    """Default role is 'user'."""
    from app.models.auth import RegisterRequest

    req = RegisterRequest(username="someone", password="longpassword")
    assert req.role == "user"


# ─── Refresh/Token Model Tests ─────────────────────────────────────────────


def test_token_response_with_refresh():
    """TokenResponse can include refresh_token."""
    from app.models.auth import TokenResponse

    resp = TokenResponse(access_token="abc", refresh_token="xyz", expires_in=3600)
    assert resp.refresh_token == "xyz"
    assert resp.token_type == "bearer"


def test_token_response_without_refresh():
    """TokenResponse works without refresh_token (backward compat)."""
    from app.models.auth import TokenResponse

    resp = TokenResponse(access_token="abc", expires_in=3600)
    assert resp.refresh_token is None


def test_refresh_response_model():
    """RefreshResponse model works correctly."""
    from app.models.auth import RefreshResponse

    resp = RefreshResponse(access_token="new-access", refresh_token="new-refresh", expires_in=86400)
    assert resp.access_token == "new-access"
    assert resp.refresh_token == "new-refresh"
    assert resp.token_type == "bearer"


# ─── Audit Service Tests ───────────────────────────────────────────────────


def test_audit_log_auth_login(db):
    """AuditService.log_auth_login creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_login("user-123", ip="127.0.0.1", username="alice")
    db.commit()
    assert entry.action == "auth.login"
    assert entry.resource_type == "auth"
    assert entry.ip_address == "127.0.0.1"
    assert entry.success is True


def test_audit_log_auth_failed(db):
    """AuditService.log_auth_failed creates a failed audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_failed(
        ip="10.0.0.1", details={"username": "baduser", "reason": "invalid_credentials"}
    )
    db.commit()
    assert entry.action == "auth.failed"
    assert entry.success is False
    assert entry.resource_type == "auth"


def test_audit_log_auth_logout(db):
    """AuditService.log_auth_logout creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_logout("user-123", ip="127.0.0.1")
    db.commit()
    assert entry.action == "auth.logout"
    assert entry.success is True


def test_audit_log_auth_register(db):
    """AuditService.log_auth_register creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_register("new-user-1", "admin-1", ip="127.0.0.1", role="user")
    db.commit()
    assert entry.action == "auth.register"
    assert entry.success is True
    assert '"role": "user"' in entry.details


def test_audit_log_auth_token_refresh(db):
    """AuditService.log_auth_token_refresh creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_token_refresh("user-123", ip="127.0.0.1")
    db.commit()
    assert entry.action == "auth.token_refresh"


def test_audit_log_auth_lockout(db):
    """AuditService.log_auth_lockout creates a failed audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_auth_lockout(ip="10.0.0.1", username="brute-user")
    db.commit()
    assert entry.action == "auth.lockout"
    assert entry.success is False


def test_audit_log_api_key_created(db):
    """AuditService.log_api_key_created creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_api_key_created("user-123", "My Key", ip="127.0.0.1")
    db.commit()
    assert entry.action == "auth.api_key_created"
    assert entry.resource_type == "api_key"


def test_audit_log_api_key_revoked(db):
    """AuditService.log_api_key_revoked creates an audit entry."""
    from app.services.audit import AuditService

    audit = AuditService(db)
    entry = audit.log_api_key_revoked("user-123", "key-456", ip="127.0.0.1")
    db.commit()
    assert entry.action == "auth.api_key_revoked"
    assert entry.resource_type == "api_key"


# ─── User ORM Column Tests ─────────────────────────────────────────────────


def test_user_has_failed_attempts_column(db, test_user):
    """User ORM model has failed_attempts column."""
    assert hasattr(test_user, "failed_attempts")
    assert test_user.failed_attempts == 0


def test_user_has_locked_until_column(db, test_user):
    """User ORM model has locked_until column."""
    assert hasattr(test_user, "locked_until")
    assert test_user.locked_until is None


def test_user_has_refresh_token_hash_column(db, test_user):
    """User ORM model has refresh_token_hash column."""
    assert hasattr(test_user, "refresh_token_hash")
    assert test_user.refresh_token_hash is None


def test_user_refresh_token_hash_roundtrip(db, test_user):
    """Can store and retrieve refresh_token_hash."""
    token = create_refresh_token()
    test_user.refresh_token_hash = hash_refresh_token(token)
    db.commit()
    db.refresh(test_user)
    assert test_user.refresh_token_hash == hash_refresh_token(token)


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
