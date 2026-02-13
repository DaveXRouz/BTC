"""Pydantic models for Telegram bot link endpoints."""

from pydantic import BaseModel


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
