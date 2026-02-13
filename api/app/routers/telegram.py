"""Telegram link endpoints — link/unlink Telegram accounts, status, profile lookup.

Also: daily auto-insight preference management (Session 35).
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.telegram import (
    DailyPreferencesResponse,
    DailyPreferencesUpdate,
    DeliveryConfirmation,
    PendingDelivery,
    TelegramLinkRequest,
    TelegramLinkResponse,
    TelegramUserStatus,
)
from app.orm.api_key import APIKey
from app.orm.oracle_reading import OracleReading
from app.orm.oracle_user import OracleUser
from app.orm.telegram_daily_preference import TelegramDailyPreference
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


# ─── Daily Preference Endpoints (Session 35) ─────────────────────────────────


def _pref_to_response(pref: TelegramDailyPreference) -> DailyPreferencesResponse:
    """Convert ORM preference to response model."""
    return DailyPreferencesResponse(
        chat_id=pref.chat_id,
        user_id=pref.user_id,
        daily_enabled=pref.daily_enabled,
        delivery_time=pref.delivery_time.strftime("%H:%M"),
        timezone_offset_minutes=pref.timezone_offset_minutes,
        last_delivered_date=(
            pref.last_delivered_date.isoformat() if pref.last_delivered_date else None
        ),
    )


@router.get("/daily/preferences/{chat_id}", response_model=DailyPreferencesResponse)
def get_daily_preferences_by_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get daily preferences by chat_id. Bot internal use (API key auth)."""
    pref = (
        db.query(TelegramDailyPreference).filter(TelegramDailyPreference.chat_id == chat_id).first()
    )
    if not pref:
        raise HTTPException(status_code=404, detail="No daily preferences found")
    return _pref_to_response(pref)


@router.put("/daily/preferences/{chat_id}", response_model=DailyPreferencesResponse)
def update_daily_preferences_by_chat(
    chat_id: int,
    body: DailyPreferencesUpdate,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update daily preferences by chat_id. Creates if not exists."""
    pref = (
        db.query(TelegramDailyPreference).filter(TelegramDailyPreference.chat_id == chat_id).first()
    )

    if not pref:
        # Link user_id from telegram_links if available
        link = (
            db.query(TelegramLink)
            .filter(
                TelegramLink.telegram_chat_id == chat_id,
                TelegramLink.is_active == True,  # noqa: E712
            )
            .first()
        )
        pref = TelegramDailyPreference(
            chat_id=chat_id,
            user_id=link.user_id if link else None,
        )
        db.add(pref)

    if body.daily_enabled is not None:
        pref.daily_enabled = body.daily_enabled
    if body.delivery_time is not None:
        pref.delivery_time = datetime.strptime(body.delivery_time, "%H:%M").time()
    if body.timezone_offset_minutes is not None:
        pref.timezone_offset_minutes = body.timezone_offset_minutes

    db.commit()
    db.refresh(pref)
    return _pref_to_response(pref)


@router.get("/daily/pending", response_model=list[PendingDelivery])
def get_pending_deliveries(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List users due for daily delivery right now. Scheduler calls this."""
    utc_now = datetime.now(timezone.utc).replace(tzinfo=None)

    enabled = (
        db.query(TelegramDailyPreference)
        .filter(TelegramDailyPreference.daily_enabled == True)  # noqa: E712
        .all()
    )

    pending: list[PendingDelivery] = []
    for pref in enabled:
        user_local_now = utc_now + timedelta(minutes=pref.timezone_offset_minutes)
        today_in_user_tz = user_local_now.date()

        # Skip if already delivered today
        if pref.last_delivered_date and pref.last_delivered_date >= today_in_user_tz:
            continue

        # Check if delivery time has passed in user's local time
        user_local_time = user_local_now.time()
        if user_local_time >= pref.delivery_time:
            pending.append(
                PendingDelivery(
                    chat_id=pref.chat_id,
                    user_id=pref.user_id,
                    delivery_time=pref.delivery_time.strftime("%H:%M"),
                    timezone_offset_minutes=pref.timezone_offset_minutes,
                )
            )

    return pending


@router.post("/daily/delivered")
def mark_delivered(
    body: DeliveryConfirmation,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Mark a user as delivered for a specific date. Scheduler calls this."""
    pref = (
        db.query(TelegramDailyPreference)
        .filter(TelegramDailyPreference.chat_id == body.chat_id)
        .first()
    )
    if not pref:
        raise HTTPException(status_code=404, detail="No daily preferences found")

    pref.last_delivered_date = datetime.strptime(body.delivered_date, "%Y-%m-%d").date()
    db.commit()
    return {"detail": "Delivery recorded"}
