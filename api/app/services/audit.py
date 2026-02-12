"""Audit logging service for Oracle security events."""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.orm.audit_log import OracleAuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Records and queries Oracle audit log entries."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        *,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        success: bool = True,
        ip_address: str | None = None,
        api_key_hash: str | None = None,
        details: dict | None = None,
    ) -> OracleAuditLog:
        """Record an audit log entry. Does not commit — joins caller's transaction."""
        entry = OracleAuditLog(
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            ip_address=ip_address,
            api_key_hash=api_key_hash,
            details=json.dumps(details) if details else None,
        )
        self.db.add(entry)
        return entry

    # ─── Oracle User audit methods ────────────────────────────────────────────

    def log_user_created(
        self, oracle_user_id: int, *, ip: str | None = None, key_hash: str | None = None
    ):
        return self.log(
            "oracle_user.create",
            resource_type="oracle_user",
            resource_id=oracle_user_id,
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_user_read(
        self, oracle_user_id: int, *, ip: str | None = None, key_hash: str | None = None
    ):
        return self.log(
            "oracle_user.read",
            resource_type="oracle_user",
            resource_id=oracle_user_id,
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_user_updated(
        self,
        oracle_user_id: int,
        fields: list[str],
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ):
        return self.log(
            "oracle_user.update",
            resource_type="oracle_user",
            resource_id=oracle_user_id,
            ip_address=ip,
            api_key_hash=key_hash,
            details={"updated_fields": fields},
        )

    def log_user_deleted(
        self, oracle_user_id: int, *, ip: str | None = None, key_hash: str | None = None
    ):
        return self.log(
            "oracle_user.delete",
            resource_type="oracle_user",
            resource_id=oracle_user_id,
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_user_listed(self, *, ip: str | None = None, key_hash: str | None = None):
        return self.log(
            "oracle_user.list",
            resource_type="oracle_user",
            ip_address=ip,
            api_key_hash=key_hash,
        )

    # ─── Oracle Reading audit methods ─────────────────────────────────────────

    def log_reading_created(
        self,
        reading_id: int,
        sign_type: str,
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ):
        return self.log(
            "oracle_reading.create",
            resource_type="oracle_reading",
            resource_id=reading_id,
            ip_address=ip,
            api_key_hash=key_hash,
            details={"sign_type": sign_type},
        )

    def log_reading_read(
        self, reading_id: int, *, ip: str | None = None, key_hash: str | None = None
    ):
        return self.log(
            "oracle_reading.read",
            resource_type="oracle_reading",
            resource_id=reading_id,
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_reading_listed(self, *, ip: str | None = None, key_hash: str | None = None):
        return self.log(
            "oracle_reading.list",
            resource_type="oracle_reading",
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_reading_deleted(
        self, reading_id: int, *, ip: str | None = None, key_hash: str | None = None
    ):
        return self.log(
            "oracle_reading.delete",
            resource_type="oracle_reading",
            resource_id=reading_id,
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_reading_updated(
        self,
        reading_id: int,
        fields: list[str],
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ):
        return self.log(
            "oracle_reading.update",
            resource_type="oracle_reading",
            resource_id=reading_id,
            ip_address=ip,
            api_key_hash=key_hash,
            details={"fields": fields},
        )

    # ─── Auth audit methods ───────────────────────────────────────────────────

    def log_auth_failed(self, *, ip: str | None = None, details: dict | None = None):
        return self.log(
            "auth.failed",
            success=False,
            resource_type="auth",
            ip_address=ip,
            details=details,
        )

    def log_auth_login(
        self,
        user_id: str,
        *,
        ip: str | None = None,
        username: str | None = None,
    ) -> OracleAuditLog:
        """Log a successful login."""
        return self.log(
            "auth.login",
            resource_type="auth",
            ip_address=ip,
            details={"username": username},
        )

    def log_auth_logout(
        self,
        user_id: str,
        *,
        ip: str | None = None,
    ) -> OracleAuditLog:
        """Log a logout."""
        return self.log(
            "auth.logout",
            resource_type="auth",
            ip_address=ip,
        )

    def log_auth_register(
        self,
        new_user_id: str,
        registered_by: str,
        *,
        ip: str | None = None,
        role: str | None = None,
    ) -> OracleAuditLog:
        """Log a new user registration."""
        return self.log(
            "auth.register",
            resource_type="auth",
            ip_address=ip,
            details={
                "new_user_id": new_user_id,
                "registered_by": registered_by,
                "role": role,
            },
        )

    def log_auth_token_refresh(
        self,
        user_id: str,
        *,
        ip: str | None = None,
    ) -> OracleAuditLog:
        """Log a token refresh."""
        return self.log(
            "auth.token_refresh",
            resource_type="auth",
            ip_address=ip,
        )

    def log_auth_lockout(
        self,
        *,
        ip: str | None = None,
        username: str | None = None,
    ) -> OracleAuditLog:
        """Log an account lockout due to brute-force."""
        return self.log(
            "auth.lockout",
            success=False,
            resource_type="auth",
            ip_address=ip,
            details={"username": username},
        )

    def log_api_key_created(
        self,
        user_id: str,
        key_name: str,
        *,
        ip: str | None = None,
    ) -> OracleAuditLog:
        """Log an API key creation."""
        return self.log(
            "auth.api_key_created",
            resource_type="api_key",
            ip_address=ip,
            details={"key_name": key_name},
        )

    def log_api_key_revoked(
        self,
        user_id: str,
        key_id: str,
        *,
        ip: str | None = None,
    ) -> OracleAuditLog:
        """Log an API key revocation."""
        return self.log(
            "auth.api_key_revoked",
            resource_type="api_key",
            ip_address=ip,
            details={"key_id": key_id},
        )

    # ─── System User audit methods ────────────────────────────────────────────

    def log_system_user_listed(
        self, *, ip: str | None = None, key_hash: str | None = None
    ) -> OracleAuditLog:
        return self.log(
            "system_user.list",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
        )

    def log_system_user_read(
        self,
        user_id: str,
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ) -> OracleAuditLog:
        return self.log(
            "system_user.read",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
            details={"target_user_id": user_id},
        )

    def log_system_user_updated(
        self,
        user_id: str,
        fields: list[str],
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ) -> OracleAuditLog:
        return self.log(
            "system_user.update",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
            details={"target_user_id": user_id, "updated_fields": fields},
        )

    def log_system_user_deactivated(
        self,
        user_id: str,
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ) -> OracleAuditLog:
        return self.log(
            "system_user.deactivate",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
            details={"target_user_id": user_id},
        )

    def log_system_user_password_reset(
        self,
        user_id: str,
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ) -> OracleAuditLog:
        return self.log(
            "system_user.password_reset",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
            details={"target_user_id": user_id},
        )

    def log_system_user_role_changed(
        self,
        user_id: str,
        old_role: str,
        new_role: str,
        *,
        ip: str | None = None,
        key_hash: str | None = None,
    ) -> OracleAuditLog:
        return self.log(
            "system_user.role_change",
            resource_type="system_user",
            ip_address=ip,
            api_key_hash=key_hash,
            details={
                "target_user_id": user_id,
                "old_role": old_role,
                "new_role": new_role,
            },
        )

    # ─── Query methods ────────────────────────────────────────────────────────

    def get_user_activity(self, oracle_user_id: int, limit: int = 50) -> list[OracleAuditLog]:
        return (
            self.db.query(OracleAuditLog)
            .filter(
                OracleAuditLog.resource_type == "oracle_user",
                OracleAuditLog.resource_id == oracle_user_id,
            )
            .order_by(OracleAuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_failed_attempts(self, hours: int = 24) -> list[OracleAuditLog]:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        return (
            self.db.query(OracleAuditLog)
            .filter(
                OracleAuditLog.success == False,  # noqa: E712
                OracleAuditLog.timestamp >= since,
            )
            .order_by(OracleAuditLog.timestamp.desc())
            .all()
        )

    def query_logs(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OracleAuditLog], int]:
        query = self.db.query(OracleAuditLog)
        if action:
            query = query.filter(OracleAuditLog.action == action)
        if resource_type:
            query = query.filter(OracleAuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(OracleAuditLog.resource_id == resource_id)

        total = query.count()
        entries = query.order_by(OracleAuditLog.timestamp.desc()).offset(offset).limit(limit).all()
        return entries, total


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """FastAPI dependency — returns an AuditService bound to the current DB session."""
    return AuditService(db)
