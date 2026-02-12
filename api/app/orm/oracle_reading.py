"""SQLAlchemy ORM models for oracle_readings, oracle_reading_users, and oracle_daily_readings tables."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OracleReading(Base):
    __tablename__ = "oracle_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("oracle_users.id"))
    is_multi_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    primary_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("oracle_users.id"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_persian: Mapped[str | None] = mapped_column(Text)
    sign_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sign_value: Mapped[str] = mapped_column(String(100), nullable=False)
    reading_result: Mapped[str | None] = mapped_column(Text)  # JSONB as text
    ai_interpretation: Mapped[str | None] = mapped_column(Text)
    ai_interpretation_persian: Mapped[str | None] = mapped_column(Text)
    individual_results: Mapped[str | None] = mapped_column(Text)  # JSONB
    compatibility_matrix: Mapped[str | None] = mapped_column(Text)  # JSONB
    combined_energy: Mapped[str | None] = mapped_column(Text)  # JSONB
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OracleReadingUser(Base):
    __tablename__ = "oracle_reading_users"

    reading_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("oracle_readings.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("oracle_users.id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)


class OracleDailyReading(Base):
    """Cache/lookup: maps (user_id, date) to an oracle reading."""

    __tablename__ = "oracle_daily_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("oracle_users.id", ondelete="CASCADE"), nullable=False
    )
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    reading_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("oracle_readings.id", ondelete="CASCADE"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("user_id", "reading_date", name="uq_daily_user_date"),)
