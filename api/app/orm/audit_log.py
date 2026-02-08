"""SQLAlchemy ORM model for the oracle_audit_log table."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OracleAuditLog(Base):
    __tablename__ = "oracle_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    api_key_hash: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[str | None] = mapped_column(Text)  # JSON string
