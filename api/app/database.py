"""Database session and engine setup — PostgreSQL with SQLite fallback."""

import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


def _build_engine():
    """Try PostgreSQL first; fall back to SQLite if unavailable."""
    url = settings.database_url

    if url.startswith("sqlite"):
        logger.info("Using SQLite database: %s", url)
        return create_engine(url, connect_args={"check_same_thread": False})

    # Try PostgreSQL
    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to PostgreSQL")
        return eng
    except Exception as exc:
        logger.warning("PostgreSQL unavailable (%s), falling back to SQLite", exc)

    # Fallback: SQLite in api/data/
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    sqlite_url = f"sqlite:///{data_dir / 'nps.db'}"
    logger.info("Using SQLite fallback: %s", sqlite_url)
    return create_engine(sqlite_url, connect_args={"check_same_thread": False})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_tables():
    """Create all tables (safe to call repeatedly — no-ops on existing tables)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
