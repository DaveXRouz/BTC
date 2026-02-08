"""Oracle endpoints — reading computation, history, user management."""

import logging
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_scope
from app.models.audit import AuditLogEntry, AuditLogResponse
from app.models.oracle import (
    DailyInsightResponse,
    NameReadingRequest,
    NameReadingResponse,
    QuestionRequest,
    QuestionResponse,
    RangeRequest,
    RangeResponse,
    ReadingRequest,
    ReadingResponse,
    StoredReadingListResponse,
    StoredReadingResponse,
)
from app.models.oracle_user import (
    OracleUserCreate,
    OracleUserListResponse,
    OracleUserResponse,
    OracleUserUpdate,
)
from app.orm.oracle_user import OracleUser
from app.services.audit import AuditService, get_audit_service
from app.services.oracle_reading import (
    OracleReadingService,
    get_oracle_reading_service,
    oracle_progress,
)
from app.services.security import EncryptionService, get_encryption_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _encrypt_user_fields(user: OracleUser, enc: EncryptionService | None) -> None:
    """Encrypt sensitive fields on an ORM user object before DB write."""
    if not enc:
        return
    if user.mother_name:
        user.mother_name = enc.encrypt(user.mother_name)
    if user.mother_name_persian:
        user.mother_name_persian = enc.encrypt(user.mother_name_persian)


def _decrypt_user(
    user: OracleUser, enc: EncryptionService | None
) -> OracleUserResponse:
    """Decrypt user fields and convert to response model."""
    mother_name = user.mother_name
    mother_name_persian = user.mother_name_persian
    if enc:
        mother_name = enc.decrypt_field(mother_name)
        mother_name_persian = (
            enc.decrypt_field(mother_name_persian) if mother_name_persian else None
        )

    return OracleUserResponse(
        id=user.id,
        name=user.name,
        name_persian=user.name_persian,
        birthday=user.birthday,
        mother_name=mother_name,
        mother_name_persian=mother_name_persian,
        country=user.country,
        city=user.city,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _get_client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ─── Oracle Reading Endpoints ─────────────────────────────────────────────────


@router.post(
    "/reading",
    response_model=ReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_reading(
    body: ReadingRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Get a full oracle reading for a date/time."""
    result = svc.get_reading(body.datetime, body.extended)
    reading = svc.store_reading(
        user_id=None,
        sign_type="reading",
        sign_value=result.get("generated_at", ""),
        question=body.datetime,
        reading_result=result,
        ai_interpretation=result.get("summary"),
    )
    audit.log_reading_created(
        reading.id,
        "reading",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return ReadingResponse(**result)


@router.post(
    "/question",
    response_model=QuestionResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_question_sign(
    body: QuestionRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Ask a yes/no question with numerological context."""
    result = svc.get_question_sign(body.question)
    reading = svc.store_reading(
        user_id=None,
        sign_type="question",
        sign_value=result.get("answer", ""),
        question=body.question,
        reading_result=result,
        ai_interpretation=result.get("interpretation"),
    )
    audit.log_reading_created(
        reading.id,
        "question",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return QuestionResponse(**result)


@router.post(
    "/name",
    response_model=NameReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_name_reading(
    body: NameReadingRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Get a name cipher reading."""
    result = svc.get_name_reading(body.name)
    reading = svc.store_reading(
        user_id=None,
        sign_type="name",
        sign_value=body.name,
        question=body.name,
        reading_result=result,
        ai_interpretation=result.get("interpretation"),
    )
    audit.log_reading_created(
        reading.id,
        "name",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return NameReadingResponse(**result)


@router.get(
    "/daily",
    response_model=DailyInsightResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_daily_insight(
    date: str | None = None,
    svc: OracleReadingService = Depends(get_oracle_reading_service),
):
    """Get daily insight for today or a specific date."""
    result = svc.get_daily_insight(date)
    return DailyInsightResponse(**result)


@router.post(
    "/suggest-range",
    response_model=RangeResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def suggest_scan_range(
    body: RangeRequest,
    svc: OracleReadingService = Depends(get_oracle_reading_service),
):
    """Get AI-suggested scan range based on timing + coverage."""
    result = svc.suggest_range(
        scanned_ranges=body.scanned_ranges,
        puzzle_number=body.puzzle_number,
        ai_level=body.ai_level,
    )
    return RangeResponse(**result)


# ─── Reading History Endpoints ───────────────────────────────────────────────


@router.get(
    "/readings",
    response_model=StoredReadingListResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def list_readings(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sign_type: str | None = Query(None),
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """List stored oracle readings with optional filters."""
    is_admin = "oracle:admin" in _user.get("scopes", [])
    readings, total = svc.list_readings(
        user_id=None,
        is_admin=is_admin,
        limit=limit,
        offset=offset,
        sign_type=sign_type,
    )
    audit.log_reading_listed(
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return StoredReadingListResponse(
        readings=[StoredReadingResponse(**r) for r in readings],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/readings/{reading_id}",
    response_model=StoredReadingResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_stored_reading(
    reading_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Get a single stored oracle reading by ID."""
    data = svc.get_reading_by_id(reading_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found"
        )
    audit.log_reading_read(
        reading_id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return StoredReadingResponse(**data)


# ─── Oracle WebSocket ────────────────────────────────────────────────────────


@router.websocket("/ws")
async def oracle_ws(websocket: WebSocket):
    """WebSocket endpoint for oracle progress updates."""
    await oracle_progress.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        oracle_progress.disconnect(websocket)


# ─── Oracle User Management ─────────────────────────────────────────────────


@router.post(
    "/users",
    response_model=OracleUserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_user(
    body: OracleUserCreate,
    request: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
    enc: EncryptionService | None = Depends(get_encryption_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Create a new Oracle user profile."""
    existing = (
        db.query(OracleUser)
        .filter(
            OracleUser.name == body.name,
            OracleUser.birthday == body.birthday,
            OracleUser.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name and birthday already exists",
        )

    user = OracleUser(**body.model_dump())
    _encrypt_user_fields(user, enc)
    db.add(user)
    db.flush()  # Get the ID before commit

    audit.log_user_created(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()
    db.refresh(user)
    logger.info("Created oracle user id=%d name=%s", user.id, body.name)
    return _decrypt_user(user, enc)


@router.get(
    "/users",
    response_model=OracleUserListResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def list_users(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
    enc: EncryptionService | None = Depends(get_encryption_service),
    audit: AuditService = Depends(get_audit_service),
):
    """List Oracle user profiles with optional search."""
    query = db.query(OracleUser).filter(OracleUser.deleted_at.is_(None))

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            func.lower(OracleUser.name).like(func.lower(pattern))
            | func.lower(OracleUser.name_persian).like(func.lower(pattern))
        )

    total = query.count()
    users = (
        query.order_by(OracleUser.created_at.desc()).offset(offset).limit(limit).all()
    )

    audit.log_user_listed(
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()

    decrypted = [_decrypt_user(u, enc) for u in users]
    return OracleUserListResponse(
        users=decrypted, total=total, limit=limit, offset=offset
    )


@router.get(
    "/users/{user_id}",
    response_model=OracleUserResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
    enc: EncryptionService | None = Depends(get_encryption_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Get a single Oracle user profile."""
    user = (
        db.query(OracleUser)
        .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    audit.log_user_read(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()

    return _decrypt_user(user, enc)


@router.put(
    "/users/{user_id}",
    response_model=OracleUserResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def update_user(
    user_id: int,
    body: OracleUserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
    enc: EncryptionService | None = Depends(get_encryption_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Update an Oracle user profile (partial update)."""
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    user = (
        db.query(OracleUser)
        .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check uniqueness if name or birthday is changing
    new_name = updates.get("name", user.name)
    new_birthday = updates.get("birthday", user.birthday)
    if new_name != user.name or new_birthday != user.birthday:
        conflict = (
            db.query(OracleUser)
            .filter(
                OracleUser.name == new_name,
                OracleUser.birthday == new_birthday,
                OracleUser.deleted_at.is_(None),
                OracleUser.id != user_id,
            )
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this name and birthday already exists",
            )

    for field, value in updates.items():
        # Encrypt sensitive fields
        if enc and field in ("mother_name", "mother_name_persian") and value:
            value = enc.encrypt(value)
        setattr(user, field, value)

    audit.log_user_updated(
        user.id,
        list(updates.keys()),
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()
    db.refresh(user)
    logger.info("Updated oracle user id=%d fields=%s", user.id, list(updates.keys()))
    return _decrypt_user(user, enc)


@router.delete(
    "/users/{user_id}",
    response_model=OracleUserResponse,
    dependencies=[Depends(require_scope("oracle:admin"))],
)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
    enc: EncryptionService | None = Depends(get_encryption_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Soft-delete an Oracle user profile."""
    user = (
        db.query(OracleUser)
        .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.deleted_at = datetime.now(timezone.utc)
    audit.log_user_deleted(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()
    db.refresh(user)
    logger.info("Soft-deleted oracle user id=%d", user.id)
    return _decrypt_user(user, enc)


# ─── Audit Log Endpoint ─────────────────────────────────────────────────────


@router.get(
    "/audit",
    response_model=AuditLogResponse,
    dependencies=[Depends(require_scope("oracle:admin"))],
)
def get_audit_log(
    action: str | None = Query(None),
    resource_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: dict = Depends(get_current_user),
    audit: AuditService = Depends(get_audit_service),
):
    """Query Oracle audit log (admin-only)."""
    entries, total = audit.query_logs(
        action=action,
        resource_type="oracle_user" if resource_id else None,
        resource_id=resource_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogResponse(
        entries=[AuditLogEntry.model_validate(e) for e in entries],
        total=total,
        limit=limit,
        offset=offset,
    )
