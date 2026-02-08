"""Audit logging service for Oracle security events."""

import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends
from sqlalchemy import func
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

    def log_auth_failed(self, *, ip: str | None = None, details: dict | None = None):
        return self.log(
            "auth.failed",
            success=False,
            ip_address=ip,
            details=details,
        )

    def get_user_activity(
        self, oracle_user_id: int, limit: int = 50
    ) -> list[OracleAuditLog]:
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
                OracleAuditLog.success == False,
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
        entries = (
            query.order_by(OracleAuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return entries, total


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """FastAPI dependency — returns an AuditService bound to the current DB session."""
    return AuditService(db)
