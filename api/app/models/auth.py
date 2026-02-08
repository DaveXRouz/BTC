"""Authentication request/response models."""

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class APIKeyCreate(BaseModel):
    name: str
    scopes: list[str] = []
    expires_in_days: int | None = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None
    last_used: datetime | None
    is_active: bool
    # Only returned on creation
    key: str | None = None
