"""Tests for Oracle permission system."""

from datetime import date

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.orm.oracle_reading import OracleReading, OracleReadingUser
from app.orm.oracle_user import OracleUser
from app.services.oracle_permissions import OraclePermissions


@pytest.fixture
def db():
    """Fresh in-memory DB for permission tests."""
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
def perms(db):
    return OraclePermissions(db)


@pytest.fixture
def user_alice(db):
    user = OracleUser(
        name="Alice",
        birthday=date(1990, 1, 1),
        mother_name="Mom A",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_bob(db):
    user = OracleUser(
        name="Bob",
        birthday=date(1991, 2, 2),
        mother_name="Mom B",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def single_reading(db, user_alice):
    """A single-user reading owned by Alice."""
    reading = OracleReading(
        user_id=user_alice.id,
        is_multi_user=False,
        question="Will it work?",
        sign_type="question",
        sign_value="Yes",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@pytest.fixture
def multi_reading(db, user_alice, user_bob):
    """A multi-user reading with Alice as primary, Bob as participant."""
    reading = OracleReading(
        is_multi_user=True,
        primary_user_id=user_alice.id,
        question="Compatibility?",
        sign_type="name",
        sign_value="Strong",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    # Add participants
    db.add(
        OracleReadingUser(reading_id=reading.id, user_id=user_alice.id, is_primary=True)
    )
    db.add(
        OracleReadingUser(reading_id=reading.id, user_id=user_bob.id, is_primary=False)
    )
    db.commit()
    return reading


# ─── Rule 1: Owner access to single-user reading ───────────────────────────


def test_owner_can_access_own_single_reading(perms, user_alice, single_reading):
    assert perms.can_access_reading(user_alice.id, single_reading.id) is True


def test_other_user_cannot_access_single_reading(perms, user_bob, single_reading):
    assert perms.can_access_reading(user_bob.id, single_reading.id) is False


# ─── Rule 2: Participant access to multi-user reading ──────────────────────


def test_primary_can_access_multi_reading(perms, user_alice, multi_reading):
    assert perms.can_access_reading(user_alice.id, multi_reading.id) is True


def test_participant_can_access_multi_reading(perms, user_bob, multi_reading):
    assert perms.can_access_reading(user_bob.id, multi_reading.id) is True


def test_non_participant_cannot_access_multi_reading(perms, db, multi_reading):
    outsider = OracleUser(
        name="Charlie",
        birthday=date(1992, 3, 3),
        mother_name="Mom C",
    )
    db.add(outsider)
    db.commit()
    db.refresh(outsider)
    assert perms.can_access_reading(outsider.id, multi_reading.id) is False


# ─── Rule 3: Admin access ──────────────────────────────────────────────────


def test_admin_can_access_any_single_reading(perms, user_bob, single_reading):
    assert (
        perms.can_access_reading(user_bob.id, single_reading.id, is_admin=True) is True
    )


def test_admin_can_access_any_multi_reading(perms, db, multi_reading):
    outsider = OracleUser(
        name="Dave",
        birthday=date(1993, 4, 4),
        mother_name="Mom D",
    )
    db.add(outsider)
    db.commit()
    db.refresh(outsider)
    assert (
        perms.can_access_reading(outsider.id, multi_reading.id, is_admin=True) is True
    )


# ─── Rule 4: Nonexistent reading ───────────────────────────────────────────


def test_nonexistent_reading_denied(perms, user_alice):
    assert perms.can_access_reading(user_alice.id, 99999) is False


# ─── get_user_readings ─────────────────────────────────────────────────────


def test_get_user_readings_returns_own(perms, user_alice, single_reading):
    readings = perms.get_user_readings(user_alice.id)
    assert len(readings) == 1
    assert readings[0].id == single_reading.id


def test_get_user_readings_excludes_others(perms, user_bob, single_reading):
    readings = perms.get_user_readings(user_bob.id)
    assert len(readings) == 0


def test_get_user_readings_includes_multi(perms, user_bob, multi_reading):
    readings = perms.get_user_readings(user_bob.id)
    assert len(readings) == 1
    assert readings[0].id == multi_reading.id


def test_get_user_readings_admin_sees_all(
    perms, user_bob, single_reading, multi_reading
):
    readings = perms.get_user_readings(user_bob.id, is_admin=True)
    assert len(readings) >= 2


# ─── get_reading_participants ───────────────────────────────────────────────


def test_get_reading_participants(perms, user_alice, user_bob, multi_reading):
    participants = perms.get_reading_participants(multi_reading.id)
    assert user_alice.id in participants
    assert user_bob.id in participants
    assert len(participants) == 2


def test_get_reading_participants_empty_for_single(perms, single_reading):
    participants = perms.get_reading_participants(single_reading.id)
    assert len(participants) == 0
