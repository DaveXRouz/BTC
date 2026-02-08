"""Shared fixtures for NPS V4 integration tests."""

import os
import sys
from pathlib import Path

import pytest
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ─── Environment Setup ─────────────────────────────────────────────────────

# Load .env values into os.environ for tests
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value

# API config
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_SECRET_KEY = os.environ.get("API_SECRET_KEY", "")

# Database config
DB_URL = (
    f"postgresql://{os.environ.get('POSTGRES_USER', 'nps')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'changeme')}@"
    f"{os.environ.get('POSTGRES_HOST', 'localhost')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'nps')}"
)


# ─── Database Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def db_engine():
    """Create a SQLAlchemy engine for the test database."""
    engine = create_engine(DB_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Create a session factory."""
    return sessionmaker(bind=db_engine)


@pytest.fixture
def db_session(db_session_factory):
    """Yield a database session that rolls back after each test."""
    session = db_session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def db_connection(db_engine):
    """Yield a raw database connection."""
    conn = db_engine.connect()
    yield conn
    conn.close()


# ─── API Client Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="session")
def api_client():
    """HTTP client with auth header for API tests."""
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {API_SECRET_KEY}",
            "Content-Type": "application/json",
        }
    )
    session.base_url = API_BASE_URL
    yield session
    session.close()


@pytest.fixture(scope="session")
def api_base_url():
    """The base URL for API requests."""
    return API_BASE_URL


# ─── Cleanup Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def cleanup_test_data(db_session_factory):
    """Delete test data created during tests (IntTest% prefix)."""
    yield
    # Post-test cleanup
    session = db_session_factory()
    try:
        # Clean up test oracle users (cascade deletes readings/audit)
        session.execute(text("DELETE FROM oracle_users WHERE name LIKE 'IntTest%'"))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


# ─── Helpers ───────────────────────────────────────────────────────────────


def api_url(path: str) -> str:
    """Build a full API URL from a relative path."""
    return f"{API_BASE_URL}{path}"
