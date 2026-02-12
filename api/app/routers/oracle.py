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
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_scope
from app.models.audit import AuditLogEntry, AuditLogResponse
from pydantic import ValidationError

from starlette.responses import Response as StarletteResponse

from app.models.dashboard import DashboardStatsResponse
from app.models.oracle import (
    DailyInsightResponse,
    DailyReadingCacheResponse,
    DailyReadingRequest,
    FrameworkReadingResponse,
    MultiUserFrameworkRequest,
    MultiUserFrameworkResponse,
    MultiUserReadingRequest,
    MultiUserReadingResponse,
    NameReadingRequest,
    NameReadingResponse,
    QuestionReadingRequest,
    QuestionReadingResponse,
    RangeRequest,
    RangeResponse,
    ReadingRequest,
    ReadingResponse,
    ReadingStatsResponse,
    StampValidateRequest,
    StampValidateResponse,
    StoredReadingListResponse,
    StoredReadingResponse,
    TimeReadingRequest,
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
    user: OracleUser,
    enc: EncryptionService | None,
    db: Session | None = None,
) -> OracleUserResponse:
    """Decrypt user fields and convert to response model."""
    mother_name = user.mother_name
    mother_name_persian = user.mother_name_persian
    if enc:
        mother_name = enc.decrypt_field(mother_name)
        mother_name_persian = (
            enc.decrypt_field(mother_name_persian) if mother_name_persian else None
        )

    # Get coordinates via raw SQL if db session provided
    latitude, longitude = None, None
    if db and user.id:
        latitude, longitude = _get_coordinates(db, user.id)

    return OracleUserResponse(
        id=user.id,
        name=user.name,
        name_persian=user.name_persian,
        birthday=user.birthday,
        mother_name=mother_name,
        mother_name_persian=mother_name_persian,
        country=user.country,
        city=user.city,
        gender=user.gender,
        heart_rate_bpm=user.heart_rate_bpm,
        timezone_hours=user.timezone_hours,
        timezone_minutes=user.timezone_minutes,
        latitude=latitude,
        longitude=longitude,
        created_by=user.created_by,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _get_client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _set_coordinates(db: Session, user_id: int, lat: float | None, lng: float | None) -> None:
    """Set coordinates POINT column using raw SQL (PostgreSQL only)."""
    if lat is not None and lng is not None:
        try:
            db.execute(
                text("UPDATE oracle_users SET coordinates = POINT(:lng, :lat) WHERE id = :id"),
                {"lng": lng, "lat": lat, "id": user_id},
            )
        except Exception:
            # SQLite doesn't support POINT type — silently skip in test/dev
            pass


def _get_coordinates(db: Session, user_id: int) -> tuple[float | None, float | None]:
    """Read coordinates POINT column, return (latitude, longitude)."""
    try:
        row = db.execute(
            text(
                "SELECT coordinates[0] AS lng, coordinates[1] AS lat "
                "FROM oracle_users WHERE id = :id"
            ),
            {"id": user_id},
        ).first()
        if row and row.lat is not None:
            return (row.lat, row.lng)
    except Exception:
        # SQLite doesn't support POINT type — return None in test/dev
        pass
    return (None, None)


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
    response_model=QuestionReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_question_sign(
    body: QuestionReadingRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Question reading with numerological hashing and framework analysis."""
    try:
        result = svc.get_question_reading_v2(
            question=body.question,
            user_id=body.user_id,
            numerology_system=body.numerology_system,
            include_ai=body.include_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    reading = svc.store_reading(
        user_id=body.user_id,
        sign_type="question",
        sign_value=str(result.get("question_number", "")),
        question=body.question,
        reading_result=result,
        ai_interpretation=result.get("ai_interpretation"),
    )
    audit.log_reading_created(
        reading.id,
        "question",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    result["reading_id"] = reading.id
    return QuestionReadingResponse(**result)


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
    """Name reading with framework numerology analysis."""
    try:
        result = svc.get_name_reading_v2(
            name=body.name,
            user_id=body.user_id,
            numerology_system=body.numerology_system,
            include_ai=body.include_ai,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    reading = svc.store_reading(
        user_id=body.user_id,
        sign_type="name",
        sign_value=body.name,
        question=body.name,
        reading_result=result,
        ai_interpretation=result.get("ai_interpretation"),
    )
    audit.log_reading_created(
        reading.id,
        "name",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    result["reading_id"] = reading.id
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


# ─── FC60 Stamp Validation Endpoint (Session 10) ────────────────────────────


@router.post(
    "/validate-stamp",
    response_model=StampValidateResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def validate_stamp(
    body: StampValidateRequest,
    _user: dict = Depends(get_current_user),
):
    """Validate an FC60 stamp string and return decoded components."""
    import sys
    from pathlib import Path

    # Ensure framework bridge is importable
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    oracle_root = project_root / "services" / "oracle"
    if str(oracle_root) not in sys.path:
        sys.path.insert(0, str(oracle_root))

    try:
        from oracle_service.framework_bridge import validate_fc60_stamp

        result = validate_fc60_stamp(body.stamp)
        return StampValidateResponse(**result)
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Framework bridge not available",
        )


# ─── Multi-User Reading Endpoint ────────────────────────────────────────────


@router.post(
    "/reading/multi-user",
    response_model=MultiUserReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def create_multi_user_reading(
    body: MultiUserReadingRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Multi-user FC60 analysis with compatibility, energy, and dynamics."""
    users = [
        {
            "name": u.name,
            "birth_year": u.birth_year,
            "birth_month": u.birth_month,
            "birth_day": u.birth_day,
        }
        for u in body.users
    ]

    try:
        result = svc.get_multi_user_reading(users, body.include_interpretation)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Collect user_ids for junction table (may be None)
    user_ids = [u.user_id for u in body.users]
    primary_uid = body.users[body.primary_user_index].user_id

    reading = svc.store_multi_user_reading(
        primary_user_id=primary_uid,
        user_ids=user_ids,
        result_dict=result,
        ai_interpretation=result.get("ai_interpretation"),
    )

    audit.log_reading_created(
        reading.id,
        "multi_user",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()

    result["reading_id"] = reading.id
    return MultiUserReadingResponse(**result)


# ─── Framework Reading Endpoint (Session 14+) ───────────────────────────────


@router.post(
    "/readings",
    dependencies=[Depends(require_scope("oracle:write"))],
)
async def create_framework_reading(
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Create a reading using the numerology framework + AI interpretation.

    Unified endpoint for all 5 reading types. The `reading_type` field in the
    request body determines the flow:
    - "time"     -> TimeReadingRequest (Session 14)
    - "name"     -> NameReadingRequest (Session 15)
    - "question" -> QuestionReadingRequest (Session 15)
    - "daily"    -> DailyReadingRequest (Session 16)
    - "multi"    -> MultiUserFrameworkRequest (Session 16)
    """
    body_raw = await request.json()
    reading_type = body_raw.get("reading_type", "time")

    async def progress_callback(step: int, total: int, message: str, rt: str = "time"):
        await oracle_progress.send_progress(step, total, message, reading_type=rt)

    try:
        if reading_type == "daily":
            body = DailyReadingRequest(**body_raw)
            result = await svc.create_daily_reading(
                user_id=body.user_id,
                date_str=body.date,
                locale=body.locale,
                numerology_system=body.numerology_system,
                force_regenerate=body.force_regenerate,
                progress_callback=progress_callback,
            )
            audit.log_reading_created(
                result["id"],
                "daily",
                ip=_get_client_ip(request),
                key_hash=_user.get("api_key_hash"),
            )
            svc.db.commit()
            return FrameworkReadingResponse(**result)

        elif reading_type == "multi":
            body = MultiUserFrameworkRequest(**body_raw)
            result = await svc.create_multi_user_framework_reading(
                user_ids=body.user_ids,
                primary_user_index=body.primary_user_index,
                date_str=body.date,
                locale=body.locale,
                numerology_system=body.numerology_system,
                include_interpretation=body.include_interpretation,
                progress_callback=progress_callback,
            )
            audit.log_reading_created(
                result.get("id"),
                "multi_user",
                ip=_get_client_ip(request),
                key_hash=_user.get("api_key_hash"),
            )
            svc.db.commit()
            return MultiUserFrameworkResponse(**result)

        else:
            # Session 14 time reading (default)
            body = TimeReadingRequest(**body_raw)

            async def time_progress(step: int, total: int, message: str):
                await oracle_progress.send_progress(
                    step,
                    total,
                    message,
                    reading_type=body.reading_type,
                )

            result = await svc.create_framework_reading(
                user_id=body.user_id,
                reading_type=body.reading_type,
                sign_value=body.sign_value,
                date_str=body.date,
                locale=body.locale,
                numerology_system=body.numerology_system,
                progress_callback=time_progress,
            )
            audit.log_reading_created(
                result["id"],
                "time",
                ip=_get_client_ip(request),
                key_hash=_user.get("api_key_hash"),
            )
            svc.db.commit()
            return FrameworkReadingResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


# ─── Daily Reading Cache Endpoint (Session 16) ──────────────────────────────


@router.get(
    "/daily/reading",
    response_model=DailyReadingCacheResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_daily_framework_reading(
    user_id: int = Query(..., description="Oracle user ID"),
    date: str | None = Query(None, description="YYYY-MM-DD, defaults to today"),
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
):
    """Get cached daily reading for a user (read-only, no generation).

    Returns the cached reading if it exists, or null if not generated.
    Use POST /readings with reading_type="daily" to generate one.
    """
    cached = svc.get_cached_daily_reading(user_id, date)
    target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if cached:
        filtered = {k: v for k, v in cached.items() if k != "_cached"}
        return DailyReadingCacheResponse(
            user_id=user_id,
            date=target_date,
            reading=FrameworkReadingResponse(**filtered),
            cached=True,
            generated_at=cached.get("created_at"),
        )
    return DailyReadingCacheResponse(
        user_id=user_id,
        date=target_date,
        reading=None,
        cached=False,
        generated_at=None,
    )


# ─── Dashboard Stats Endpoint (Session 22) ───────────────────────────────────


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_dashboard_stats(
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
) -> DashboardStatsResponse:
    """Aggregated reading statistics for the dashboard."""
    stats = svc.get_dashboard_stats()
    return DashboardStatsResponse(**stats)


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
    search: str | None = Query(None, description="Full-text search query"),
    date_from: str | None = Query(None, description="Filter from date (ISO 8601)"),
    date_to: str | None = Query(None, description="Filter to date (ISO 8601)"),
    is_favorite: bool | None = Query(None, description="Filter favorites only"),
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
        date_from=date_from,
        date_to=date_to,
        is_favorite=is_favorite,
        search_query=search,
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
    "/readings/stats",
    response_model=ReadingStatsResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_reading_stats(
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
):
    """Aggregate reading statistics (total, by type, by month, favorites)."""
    stats = svc.get_reading_stats()
    return ReadingStatsResponse(**stats)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found")
    audit.log_reading_read(
        reading_id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return StoredReadingResponse(**data)


@router.delete(
    "/readings/{reading_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def delete_reading(
    reading_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Soft-delete an oracle reading."""
    deleted = svc.soft_delete_reading(reading_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found")
    audit.log_reading_deleted(
        reading_id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return StarletteResponse(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/readings/{reading_id}/favorite",
    response_model=StoredReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def toggle_reading_favorite(
    reading_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Toggle the favorite status of an oracle reading."""
    data = svc.toggle_favorite(reading_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found")
    audit.log_reading_updated(
        reading_id,
        ["is_favorite"],
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

    # Exclude latitude/longitude (not ORM columns — handled separately via raw SQL)
    user_data = body.model_dump(exclude={"latitude", "longitude"})
    user = OracleUser(**user_data)
    user.created_by = _user.get("user_id")
    _encrypt_user_fields(user, enc)
    db.add(user)
    db.flush()  # Get the ID before commit

    # Set coordinates if provided
    _set_coordinates(db, user.id, body.latitude, body.longitude)

    audit.log_user_created(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()
    db.refresh(user)
    logger.info("Created oracle user id=%d name=%s", user.id, body.name)
    return _decrypt_user(user, enc, db)


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

    # Ownership: non-admin/moderator users see only their own profiles
    if _user["role"] not in ("admin", "moderator"):
        query = query.filter(OracleUser.created_by == _user["user_id"])

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            func.lower(OracleUser.name).like(func.lower(pattern))
            | func.lower(OracleUser.name_persian).like(func.lower(pattern))
        )

    total = query.count()
    users = query.order_by(OracleUser.created_at.desc()).offset(offset).limit(limit).all()

    audit.log_user_listed(
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()

    decrypted = [_decrypt_user(u, enc, db) for u in users]
    return OracleUserListResponse(users=decrypted, total=total, limit=limit, offset=offset)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Ownership check: non-admin/moderator can only see own profiles
    if _user["role"] not in ("admin", "moderator"):
        if user.created_by != _user["user_id"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    audit.log_user_read(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()

    return _decrypt_user(user, enc, db)


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    user = (
        db.query(OracleUser)
        .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Ownership check: non-admin/moderator can only update own profiles
    if _user["role"] not in ("admin", "moderator"):
        if user.created_by != _user["user_id"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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

    # Handle coordinates separately (not ORM columns)
    lat = updates.pop("latitude", None)
    lng = updates.pop("longitude", None)
    if lat is not None or lng is not None:
        _set_coordinates(db, user_id, lat, lng)

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
    return _decrypt_user(user, enc, db)


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.deleted_at = datetime.now(timezone.utc)
    audit.log_user_deleted(
        user.id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    db.commit()
    db.refresh(user)
    logger.info("Soft-deleted oracle user id=%d", user.id)
    return _decrypt_user(user, enc, db)


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
