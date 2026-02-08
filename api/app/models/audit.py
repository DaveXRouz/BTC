"""Pydantic models for audit log endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    user_id: int | None = None
    action: str
    resource_type: str | None = None
    resource_id: int | None = None
    success: bool = True
    ip_address: str | None = None
    api_key_hash: str | None = None
    details: str | None = None


class AuditLogResponse(BaseModel):
    entries: list[AuditLogEntry]
    total: int
    limit: int
    offset: int
