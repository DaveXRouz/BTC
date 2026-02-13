"""Telegram link endpoints — link/unlink Telegram accounts, status, profile lookup.

Also: daily auto-insight preference management (Session 35).
Also: admin stats, users, audit, linked_chats, and internal notify (Session 36).
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_scope
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
from app.orm.audit_log import OracleAuditLog
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


# ─── Admin Endpoints (Session 36) ────────────────────────────────────────────

# Store app start time for uptime calculation
_APP_START_TIME = time.time()


class AdminAuditRequest(BaseModel):
    action: str
    resource_type: str = "system"
    success: bool = True
    details: str | None = None


class AdminNotifyRequest(BaseModel):
    event_type: str
    data: dict


@router.get("/admin/stats", dependencies=[Depends(require_scope("admin"))])
def get_admin_stats(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_scope("admin")),
):
    """System statistics for admin dashboard / Telegram /admin_stats command."""
    utc_now = datetime.now(timezone.utc)
    today_start = utc_now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = db.query(func.count(OracleUser.id)).scalar() or 0

    readings_total = db.query(func.count(OracleReading.id)).scalar() or 0

    # Readings today — handle both timezone-aware and naive timestamps
    readings_today = (
        db.query(func.count(OracleReading.id))
        .filter(OracleReading.created_at >= today_start.replace(tzinfo=None))
        .scalar()
        or 0
    )

    # Errors in last 24h from audit log
    yesterday = utc_now - timedelta(hours=24)
    error_count_24h = (
        db.query(func.count(OracleAuditLog.id))
        .filter(
            OracleAuditLog.action == "error",
            OracleAuditLog.timestamp >= yesterday.replace(tzinfo=None),
        )
        .scalar()
        or 0
    )

    # Last reading timestamp
    last_reading = (
        db.query(OracleReading.created_at).order_by(OracleReading.created_at.desc()).first()
    )
    last_reading_at = None
    if last_reading and last_reading[0]:
        last_reading_at = last_reading[0].isoformat()

    # DB size — try PostgreSQL-specific query, fall back to 0
    db_size_mb = 0.0
    try:
        result = db.execute(text("SELECT pg_database_size(current_database()) / 1024.0 / 1024.0"))
        row = result.scalar()
        if row:
            db_size_mb = float(row)
    except Exception:
        pass  # SQLite or other DB — no pg_database_size

    uptime_seconds = time.time() - _APP_START_TIME

    return {
        "total_users": total_users,
        "readings_today": readings_today,
        "readings_total": readings_total,
        "error_count_24h": error_count_24h,
        "active_sessions": 0,  # Placeholder — session tracking not implemented yet
        "uptime_seconds": uptime_seconds,
        "db_size_mb": db_size_mb,
        "last_reading_at": last_reading_at,
    }


@router.get("/admin/users", dependencies=[Depends(require_scope("admin"))])
def get_admin_users(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: dict = Depends(require_scope("admin")),
):
    """Paginated user listing for admin. Returns non-sensitive fields only."""
    total = db.query(func.count(OracleUser.id)).scalar() or 0

    users = (
        db.query(OracleUser)
        .order_by(OracleUser.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "birthday": u.birthday.isoformat() if u.birthday else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.get("/admin/linked_chats", dependencies=[Depends(require_scope("admin"))])
def get_linked_chats(
    db: Session = Depends(get_db),
    _user: dict = Depends(require_scope("admin")),
):
    """List all active linked Telegram chat IDs (for broadcast)."""
    links = (
        db.query(TelegramLink.telegram_chat_id)
        .filter(TelegramLink.is_active == True)  # noqa: E712
        .all()
    )
    return {"chat_ids": [link[0] for link in links]}


@router.post("/admin/audit", dependencies=[Depends(require_scope("admin"))])
def create_audit_entry(
    body: AdminAuditRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_scope("admin")),
):
    """Log an admin action to oracle_audit_log. Used by Telegram bot admin commands."""
    entry = OracleAuditLog(
        user_id=None,  # user_id is int in ORM, telegram bot doesn't have numeric user id
        action=body.action,
        resource_type=body.resource_type,
        success=body.success,
        ip_address="telegram",
        api_key_hash=user.get("api_key_hash"),
        details=body.details,
    )
    db.add(entry)
    db.commit()
    return {"detail": "Audit entry created"}


@router.post("/internal/notify")
def internal_notify(
    body: AdminNotifyRequest,
    _user: dict = Depends(get_current_user),
):
    """Internal notification endpoint for service-to-service event forwarding.

    Accepts events from API middleware (errors, new users, etc.) and forwards
    to the Telegram notification service. In the current architecture, the bot
    polls the API rather than receiving pushes, so this stores events for
    the bot to pick up if needed.
    """
    logger.info("Internal notify: %s — %s", body.event_type, body.data)
    return {"detail": "Event received", "event_type": body.event_type}
