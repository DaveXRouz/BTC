"""Shared test fixtures for V4 API tests."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.middleware.auth import get_current_user
from app.services.security import (
    EncryptionService,
    derive_key,
    get_encryption_service,
)

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Shared test encryption key
_TEST_KEY = derive_key("test-password-32-chars!!", b"salt" * 8)
_test_enc = EncryptionService(_TEST_KEY)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    """Mock auth returning admin-level test user."""
    return {
        "user_id": "test-user-id",
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
        "api_key_hash": "test-key-hash",
        "rate_limit": None,
    }


def override_get_current_user_readonly():
    """Mock auth returning read-only user (no write/admin scopes)."""
    return {
        "user_id": "readonly-user-id",
        "username": "test-readonly",
        "role": "readonly",
        "scopes": ["oracle:read", "scanner:read", "vault:read"],
        "auth_type": "test",
        "api_key_hash": None,
        "rate_limit": None,
    }


def override_get_encryption_service():
    return _test_enc


def override_get_encryption_service_none():
    return None


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test and drop after. Also reset rate limiter."""
    from app.middleware.rate_limit import _limiter

    _limiter._requests.clear()
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
async def client():
    """Authenticated admin test client with encryption enabled."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    # NOTE: get_audit_service is NOT overridden — it uses get_db naturally,
    # which is already overridden to use the test DB.
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_enc():
    """Authenticated admin test client without encryption."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_encryption_service] = (
        override_get_encryption_service_none
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def readonly_client():
    """Authenticated read-only test client."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user_readonly
    app.dependency_overrides[get_encryption_service] = override_get_encryption_service
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def unauth_client():
    """Unauthenticated test client (no auth override)."""
    app.dependency_overrides[get_db] = override_get_db
    # Deliberately do NOT override get_current_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
