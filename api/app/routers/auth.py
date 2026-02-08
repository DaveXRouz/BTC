"""Authentication endpoints — JWT + API key management."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import create_access_token, get_current_user, require_scope
from app.models.auth import (
    APIKeyCreate,
    APIKeyResponse,
    LoginRequest,
    TokenResponse,
)
from app.orm.api_key import APIKey
from app.orm.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not _bcrypt.checkpw(
        request.password.encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(user.id, user.username, user.role)
    from app.config import settings

    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
    )


@router.post("/api-keys", response_model=APIKeyResponse)
def create_api_key(
    request: APIKeyCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new API key for programmatic access."""
    raw_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = str(uuid.uuid4())

    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=request.expires_in_days
        )

    api_key = APIKey(
        id=key_id,
        user_id=user.get("user_id"),
        key_hash=key_hash,
        name=request.name,
        scopes=",".join(request.scopes),
        expires_at=expires_at,
    )
    db.add(api_key)
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
            APIKey.is_active == True,
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
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Revoke an API key (soft-delete by setting is_active=False)."""
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
    db.commit()
    return {"detail": "API key revoked"}
