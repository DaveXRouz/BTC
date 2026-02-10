"""Authentication endpoints — JWT, refresh tokens, API key management, registration."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.middleware.auth import (
    _blacklist,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_refresh_token,
    require_scope,
    security_scheme,
)
from app.models.auth import (
    APIKeyCreate,
    APIKeyResponse,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.orm.api_key import APIKey
from app.orm.user import User
from app.services.audit import AuditService

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


@router.post("/login", response_model=TokenResponse)
def login(request_body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate and receive JWT + refresh tokens."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)

    user = db.query(User).filter(User.username == request_body.username).first()

    # Check if account is locked
    if user and user.locked_until:
        if user.locked_until.tzinfo is None:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            now = datetime.now(timezone.utc)
        if user.locked_until > now:
            audit.log_auth_failed(
                ip=ip,
                details={"username": request_body.username, "reason": "account_locked"},
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed attempts",
            )
        # Lock expired — reset
        user.failed_attempts = 0
        user.locked_until = None

    # Verify credentials
    if not user or not _bcrypt.checkpw(
        request_body.password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        # Track failed attempt
        if user:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=LOCKOUT_DURATION_MINUTES
                )
                audit.log_auth_lockout(ip=ip, username=request_body.username)
            db.commit()
        audit.log_auth_failed(
            ip=ip,
            details={
                "username": request_body.username,
                "reason": "invalid_credentials",
            },
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        audit.log_auth_failed(
            ip=ip,
            details={"username": request_body.username, "reason": "account_disabled"},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Success — reset failed attempts, generate tokens
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)

    # Generate refresh token
    refresh_raw = create_refresh_token()
    user.refresh_token_hash = hash_refresh_token(refresh_raw)

    audit.log_auth_login(user.id, ip=ip, username=user.username)
    db.commit()

    access_token = create_access_token(user.id, user.username, user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(request_body: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for new access + refresh tokens (rotation)."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)

    token_hash = hash_refresh_token(request_body.refresh_token)
    user = db.query(User).filter(User.refresh_token_hash == token_hash).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Rotate: generate new refresh token, invalidate old
    new_refresh = create_refresh_token()
    user.refresh_token_hash = hash_refresh_token(new_refresh)

    audit.log_auth_token_refresh(user.id, ip=ip)
    db.commit()

    new_access = create_access_token(user.id, user.username, user.role)

    return RefreshResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/logout")
def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Logout: blacklist current JWT and clear refresh token."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)
    token = credentials.credentials

    # Blacklist the JWT until it expires
    try:
        payload = jwt.decode(
            token,
            settings.api_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
        exp = payload.get("exp", 0)
        _blacklist.add(token, float(exp))
    except JWTError:
        pass  # Non-JWT auth (API key) — no blacklist needed

    # Clear refresh token
    user_id = user.get("user_id")
    if user_id:
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user:
            db_user.refresh_token_hash = None

    audit.log_auth_logout(user.get("user_id", ""), ip=ip)
    db.commit()

    return {"detail": "Logged out successfully"}


@router.post("/register", response_model=RegisterResponse)
def register(
    request_body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(require_scope("admin")),
):
    """Create a new user account. Admin-only."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)

    # Validate role
    valid_roles = {"admin", "moderator", "user", "readonly"}
    if request_body.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}",
        )

    # Check username uniqueness
    existing = db.query(User).filter(User.username == request_body.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    # Hash password with bcrypt
    pw_hash = _bcrypt.hashpw(request_body.password.encode("utf-8"), _bcrypt.gensalt()).decode(
        "utf-8"
    )

    new_user = User(
        id=str(uuid.uuid4()),
        username=request_body.username,
        password_hash=pw_hash,
        role=request_body.role,
    )
    db.add(new_user)
    db.flush()

    audit.log_auth_register(new_user.id, user.get("user_id", ""), ip=ip, role=request_body.role)
    db.commit()
    db.refresh(new_user)

    return RegisterResponse(
        id=new_user.id,
        username=new_user.username,
        role=new_user.role,
        created_at=new_user.created_at,
    )


@router.post("/api-keys", response_model=APIKeyResponse)
def create_api_key(
    request_body: APIKeyCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new API key for programmatic access."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)

    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = str(uuid.uuid4())

    expires_at = None
    if request_body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request_body.expires_in_days)

    api_key = APIKey(
        id=key_id,
        user_id=user.get("user_id"),
        key_hash=key_hash,
        name=request_body.name,
        scopes=",".join(request_body.scopes),
        expires_at=expires_at,
    )
    db.add(api_key)

    audit.log_api_key_created(user.get("user_id", ""), request_body.name, ip=ip)
    db.commit()
    db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        scopes=api_key.scopes_list,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        last_used=api_key.last_used,
        is_active=api_key.is_active,
        key=raw_key,  # Only returned on creation
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """List API keys for the current user."""
    user_id = user.get("user_id")
    if not user_id:
        return []

    keys = (
        db.query(APIKey)
        .filter(
            APIKey.user_id == user_id,
            APIKey.is_active == True,  # noqa: E712
        )
        .all()
    )

    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            scopes=k.scopes_list,
            created_at=k.created_at,
            expires_at=k.expires_at,
            last_used=k.last_used,
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Revoke an API key (soft-delete by setting is_active=False)."""
    ip = request.client.host if request.client else None
    audit = AuditService(db)

    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Only the key owner or admin can revoke
    if api_key.user_id != user.get("user_id") and user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke another user's API key",
        )

    api_key.is_active = False

    audit.log_api_key_revoked(user.get("user_id", ""), key_id, ip=ip)
    db.commit()

    return {"detail": "API key revoked"}
