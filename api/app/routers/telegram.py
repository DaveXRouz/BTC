"""Telegram link endpoints — link/unlink Telegram accounts, status, profile lookup."""

import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.telegram import (
    TelegramLinkRequest,
    TelegramLinkResponse,
    TelegramUserStatus,
)
from app.orm.api_key import APIKey
from app.orm.oracle_reading import OracleReading
from app.orm.oracle_user import OracleUser
from app.orm.telegram_link import TelegramLink
from app.orm.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/link", response_model=TelegramLinkResponse)
def link_telegram(body: TelegramLinkRequest, db: Session = Depends(get_db)):
    """Link a Telegram chat to an NPS user account via API key validation."""
    key_hash = hashlib.sha256(body.api_key.encode()).hexdigest()
    api_key = (
        db.query(APIKey)
        .filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    user = db.query(User).filter(User.id == api_key.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive",
        )

    existing = (
        db.query(TelegramLink)
        .filter(TelegramLink.telegram_chat_id == body.telegram_chat_id)
        .first()
    )
    if existing:
        existing.user_id = user.id
        existing.telegram_username = body.telegram_username
        existing.is_active = True
    else:
        existing = TelegramLink(
            telegram_chat_id=body.telegram_chat_id,
            telegram_username=body.telegram_username,
            user_id=user.id,
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)

    return TelegramLinkResponse(
        telegram_chat_id=existing.telegram_chat_id,
        telegram_username=existing.telegram_username,
        user_id=user.id,
        username=user.username,
        role=user.role,
        linked_at=existing.linked_at.isoformat(),
        is_active=existing.is_active,
    )


@router.get("/status/{chat_id}", response_model=TelegramUserStatus)
def get_telegram_status(
    chat_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get link status for a Telegram chat. Requires bot service key auth."""
    link = (
        db.query(TelegramLink)
        .filter(
            TelegramLink.telegram_chat_id == chat_id,
            TelegramLink.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not link:
        return TelegramUserStatus(linked=False)

    user = db.query(User).filter(User.id == link.user_id).first()
    if not user:
        return TelegramUserStatus(linked=False)

    profile_count = db.query(OracleUser).filter(OracleUser.created_by == link.user_id).count()
    reading_count = db.query(OracleReading).filter(OracleReading.user_id.isnot(None)).count()

    return TelegramUserStatus(
        linked=True,
        username=user.username,
        role=user.role,
        oracle_profile_count=profile_count,
        reading_count=reading_count,
    )


@router.delete("/link/{chat_id}")
def unlink_telegram(
    chat_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Unlink a Telegram account. Sets is_active=False."""
    link = db.query(TelegramLink).filter(TelegramLink.telegram_chat_id == chat_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Telegram link not found")

    link.is_active = False
    db.commit()
    return {"detail": "Telegram account unlinked"}


@router.get("/profile/{chat_id}")
def get_telegram_profile(
    chat_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get Oracle profiles for a linked Telegram user."""
    link = (
        db.query(TelegramLink)
        .filter(
            TelegramLink.telegram_chat_id == chat_id,
            TelegramLink.is_active == True,  # noqa: E712
        )
        .first()
    )

    if not link:
        return []

    profiles = (
        db.query(OracleUser)
        .filter(OracleUser.created_by == link.user_id, OracleUser.deleted_at.is_(None))
        .all()
    )

    return [
        {
            "id": p.id,
            "name": p.name,
            "name_persian": p.name_persian,
            "birthday": p.birthday.isoformat() if p.birthday else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in profiles
    ]
