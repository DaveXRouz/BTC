"""Admin service — business logic for user and profile management."""

from __future__ import annotations

import logging
import secrets

import bcrypt as _bcrypt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.orm.oracle_reading import OracleDailyReading, OracleReading, OracleReadingUser
from app.orm.oracle_user import OracleUser
from app.orm.user import User

logger = logging.getLogger(__name__)

_ALLOWED_USER_SORT = {"username", "role", "created_at", "last_login", "is_active"}
_ALLOWED_PROFILE_SORT = {"name", "birthday", "created_at"}


class AdminService:
    """Business logic for admin user and profile management."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ─── System Users ──────────────────────────────────────────────────

    def list_users(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[dict], int]:
        """List system users with optional search, sort, and pagination."""
        query = self.db.query(User)

        if search:
            query = query.filter(User.username.ilike(f"%{search}%"))

        total = query.count()

        sort_col = getattr(User, sort_by) if sort_by in _ALLOWED_USER_SORT else User.created_at
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        users = query.offset(offset).limit(limit).all()

        return [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
                "last_login": u.last_login,
                "is_active": u.is_active,
                "reading_count": 0,
            }
            for u in users
        ], total

    def get_user_detail(self, user_id: str) -> dict | None:
        """Get a single system user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
            "is_active": user.is_active,
            "reading_count": 0,
        }

    def update_role(self, user_id: str, new_role: str, admin_user_id: str) -> User:
        """Change a user's role. Raises ValueError if trying to modify own role."""
        if user_id == admin_user_id:
            raise ValueError("Cannot modify your own role")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.role = new_role
        self.db.flush()
        return user

    def reset_password(self, user_id: str) -> tuple[User, str] | None:
        """Generate temp password, bcrypt hash it, store it."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        temp_password = secrets.token_urlsafe(16)
        hashed = _bcrypt.hashpw(temp_password.encode("utf-8"), _bcrypt.gensalt())
        user.password_hash = hashed.decode("utf-8")
        user.salt = None
        self.db.flush()
        return user, temp_password

    def update_status(self, user_id: str, is_active: bool, admin_user_id: str) -> User:
        """Activate or deactivate. Raises ValueError if trying to deactivate self."""
        if user_id == admin_user_id and not is_active:
            raise ValueError("Cannot deactivate your own account")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        user.is_active = is_active
        self.db.flush()
        return user

    # ─── Stats ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Aggregate stats: user counts by role/status, reading counts, today's readings."""
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        active_users = (
            self.db.query(func.count(User.id))
            .filter(User.is_active == True)  # noqa: E712
            .scalar()
            or 0
        )
        inactive_users = total_users - active_users

        # Users by role
        role_rows = self.db.query(User.role, func.count(User.id)).group_by(User.role).all()
        users_by_role = {role: count for role, count in role_rows}

        total_profiles = (
            self.db.query(func.count(OracleUser.id))
            .filter(OracleUser.deleted_at == None)  # noqa: E711
            .scalar()
            or 0
        )

        total_readings = self.db.query(func.count(OracleReading.id)).scalar() or 0

        # Readings today
        today_start = func.date(func.now())
        readings_today = (
            self.db.query(func.count(OracleReading.id))
            .filter(func.date(OracleReading.created_at) == today_start)
            .scalar()
            or 0
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_oracle_profiles": total_profiles,
            "total_readings": total_readings,
            "readings_today": readings_today,
            "users_by_role": users_by_role,
        }

    # ─── Oracle Profiles ───────────────────────────────────────────────

    def list_oracle_profiles(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_deleted: bool = False,
    ) -> tuple[list[dict], int]:
        """List all Oracle profiles with reading counts."""
        # Build reading count subquery
        reading_counts = (
            self.db.query(
                OracleReading.user_id,
                func.count(OracleReading.id).label("count"),
            )
            .group_by(OracleReading.user_id)
            .subquery()
        )

        query = self.db.query(
            OracleUser,
            func.coalesce(reading_counts.c.count, 0).label("reading_count"),
        ).outerjoin(reading_counts, OracleUser.id == reading_counts.c.user_id)

        if not include_deleted:
            query = query.filter(OracleUser.deleted_at == None)  # noqa: E711

        if search:
            query = query.filter(
                OracleUser.name.ilike(f"%{search}%") | OracleUser.name_persian.ilike(f"%{search}%")
            )

        # Count query (without join for efficiency)
        count_query = self.db.query(func.count(OracleUser.id))
        if not include_deleted:
            count_query = count_query.filter(
                OracleUser.deleted_at == None  # noqa: E711
            )
        if search:
            count_query = count_query.filter(
                OracleUser.name.ilike(f"%{search}%") | OracleUser.name_persian.ilike(f"%{search}%")
            )
        total = count_query.scalar() or 0

        sort_col = (
            getattr(OracleUser, sort_by)
            if sort_by in _ALLOWED_PROFILE_SORT
            else OracleUser.created_at
        )
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        results = query.offset(offset).limit(limit).all()

        profiles = []
        for profile, rc in results:
            profiles.append(
                {
                    "id": profile.id,
                    "name": profile.name,
                    "name_persian": profile.name_persian,
                    "birthday": profile.birthday,
                    "country": profile.country,
                    "city": profile.city,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                    "deleted_at": profile.deleted_at,
                    "reading_count": rc,
                }
            )
        return profiles, total

    def delete_oracle_profile(self, profile_id: int) -> dict | None:
        """Hard-delete an Oracle profile and its readings."""
        profile = self.db.query(OracleUser).filter(OracleUser.id == profile_id).first()
        if not profile:
            return None

        data = {
            "id": profile.id,
            "name": profile.name,
            "name_persian": profile.name_persian,
            "birthday": profile.birthday,
            "country": profile.country,
            "city": profile.city,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "deleted_at": profile.deleted_at,
            "reading_count": 0,
        }

        # Clean up related records
        self.db.query(OracleReadingUser).filter(OracleReadingUser.user_id == profile_id).delete()
        self.db.query(OracleDailyReading).filter(OracleDailyReading.user_id == profile_id).delete()
        self.db.query(OracleReading).filter(OracleReading.primary_user_id == profile_id).update(
            {"primary_user_id": None}
        )
        self.db.query(OracleReading).filter(OracleReading.user_id == profile_id).delete()
        self.db.delete(profile)

        return data
