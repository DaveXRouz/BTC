"""SQLAlchemy ORM model for the oracle_users table."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OracleUser(Base):
    __tablename__ = "oracle_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_persian: Mapped[str | None] = mapped_column(String(200))
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    mother_name: Mapped[str] = mapped_column(Text, nullable=False)
    mother_name_persian: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)

    __table_args__ = (
        CheckConstraint("length(name) >= 2", name="oracle_users_name_check"),
        CheckConstraint("birthday <= CURRENT_DATE", name="oracle_users_birthday_check"),
    )
