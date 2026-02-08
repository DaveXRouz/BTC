"""Oracle permission system — row-level access control for readings."""

import logging

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db

logger = logging.getLogger(__name__)


class OraclePermissions:
    """Checks row-level access permissions for Oracle readings."""

    def __init__(self, db: Session):
        self.db = db

    def can_access_reading(
        self, user_id: int, reading_id: int, is_admin: bool = False
    ) -> bool:
        """Check if a user can access a specific reading.

        Rules:
        1. Owner can access own single-user readings
        2. Participants can access multi-user readings (via oracle_reading_users)
        3. Admin can access all readings
        4. All other access denied
        """
        if is_admin:
            return True

        # Import here to avoid circular dependency
        from app.orm.oracle_reading import OracleReading, OracleReadingUser

        reading = (
            self.db.query(OracleReading).filter(OracleReading.id == reading_id).first()
        )
        if not reading:
            return False

        # Rule 1: Owner of single-user reading
        if not reading.is_multi_user and reading.user_id == user_id:
            return True

        # Rule 2: Participant in multi-user reading
        if reading.is_multi_user:
            participant = (
                self.db.query(OracleReadingUser)
                .filter(
                    OracleReadingUser.reading_id == reading_id,
                    OracleReadingUser.user_id == user_id,
                )
                .first()
            )
            if participant:
                return True

        return False

    def get_user_readings(
        self, user_id: int, is_admin: bool = False, limit: int = 50
    ) -> list:
        """Get readings accessible to a user, respecting permissions."""
        from app.orm.oracle_reading import OracleReading, OracleReadingUser

        if is_admin:
            return (
                self.db.query(OracleReading)
                .order_by(OracleReading.created_at.desc())
                .limit(limit)
                .all()
            )

        # Own single-user readings + multi-user readings where participating
        own_readings = (
            self.db.query(OracleReading)
            .filter(
                OracleReading.is_multi_user == False,
                OracleReading.user_id == user_id,
            )
            .all()
        )

        multi_reading_ids = (
            self.db.query(OracleReadingUser.reading_id)
            .filter(OracleReadingUser.user_id == user_id)
            .all()
        )
        multi_ids = [r[0] for r in multi_reading_ids]

        multi_readings = []
        if multi_ids:
            multi_readings = (
                self.db.query(OracleReading)
                .filter(OracleReading.id.in_(multi_ids))
                .all()
            )

        combined = own_readings + multi_readings
        combined.sort(key=lambda r: r.created_at, reverse=True)
        return combined[:limit]

    def get_reading_participants(self, reading_id: int) -> list[int]:
        """Get all user IDs participating in a reading."""
        from app.orm.oracle_reading import OracleReadingUser

        rows = (
            self.db.query(OracleReadingUser.user_id)
            .filter(OracleReadingUser.reading_id == reading_id)
            .all()
        )
        return [r[0] for r in rows]


def get_oracle_permissions(db: Session = Depends(get_db)) -> OraclePermissions:
    """FastAPI dependency — returns OraclePermissions bound to the current DB session."""
    return OraclePermissions(db)
