"""SQLAlchemy ORM model for the telegram_daily_preferences table."""

from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelegramDailyPreference(Base):
    __tablename__ = "telegram_daily_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL")
    )
    daily_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_time: Mapped[time] = mapped_column(Time, default=time(8, 0))
    timezone_offset_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_delivered_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
