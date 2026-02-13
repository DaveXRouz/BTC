"""Pydantic models for Telegram bot link and daily preference endpoints."""

from datetime import datetime

from pydantic import BaseModel, field_validator


class TelegramLinkRequest(BaseModel):
    telegram_chat_id: int
    telegram_username: str | None = None
    api_key: str


class TelegramLinkResponse(BaseModel):
    telegram_chat_id: int
    telegram_username: str | None
    user_id: str
    username: str
    role: str
    linked_at: str
    is_active: bool


class TelegramUserStatus(BaseModel):
    linked: bool
    username: str | None = None
    role: str | None = None
    oracle_profile_count: int = 0
    reading_count: int = 0


# ─── Daily Preference Models (Session 35) ──────────────────────────────────


class DailyPreferencesResponse(BaseModel):
    chat_id: int
    user_id: str | None = None
    daily_enabled: bool
    delivery_time: str  # "HH:MM"
    timezone_offset_minutes: int
    last_delivered_date: str | None = None  # "YYYY-MM-DD"


class DailyPreferencesUpdate(BaseModel):
    daily_enabled: bool | None = None
    delivery_time: str | None = None  # "HH:MM"
    timezone_offset_minutes: int | None = None

    @field_validator("delivery_time")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError as exc:
            raise ValueError("delivery_time must be HH:MM format (24h)") from exc
        return v


class PendingDelivery(BaseModel):
    chat_id: int
    user_id: str | None = None
    delivery_time: str
    timezone_offset_minutes: int


class DeliveryConfirmation(BaseModel):
    chat_id: int
    delivered_date: str  # "YYYY-MM-DD"
