"""Authentication middleware — JWT verification and API key validation."""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.orm.api_key import APIKey
from app.orm.user import User

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)

# Scope hierarchy: higher scopes imply lower ones
_SCOPE_HIERARCHY = {
    "oracle:admin": {"oracle:admin", "oracle:write", "oracle:read"},
    "oracle:write": {"oracle:write", "oracle:read"},
    "oracle:read": {"oracle:read"},
    "scanner:admin": {"scanner:admin", "scanner:write", "scanner:read"},
    "scanner:write": {"scanner:write", "scanner:read"},
    "scanner:read": {"scanner:read"},
    "vault:admin": {"vault:admin", "vault:write", "vault:read"},
    "vault:write": {"vault:write", "vault:read"},
    "vault:read": {"vault:read"},
    "admin": set(),  # expanded in _expand_scopes
}

# Role to default scopes mapping
_ROLE_SCOPES = {
    "admin": [
        "oracle:admin",
        "oracle:write",
        "oracle:read",
        "scanner:admin",
        "scanner:write",
        "scanner:read",
        "vault:admin",
        "vault:write",
        "vault:read",
        "admin",
    ],
    "user": [
        "oracle:write",
        "oracle:read",
        "scanner:write",
        "scanner:read",
        "vault:write",
        "vault:read",
    ],
    "readonly": [
        "oracle:read",
        "scanner:read",
        "vault:read",
    ],
}


def _expand_scopes(scopes: list[str]) -> set[str]:
    """Expand scopes using hierarchy (e.g. oracle:admin implies oracle:read)."""
    expanded = set()
    for scope in scopes:
        expanded.add(scope)
        if scope in _SCOPE_HIERARCHY:
            expanded.update(_SCOPE_HIERARCHY[scope])
    return expanded


def _role_to_scopes(role: str) -> list[str]:
    """Map a user role to its default scopes."""
    return _ROLE_SCOPES.get(role, _ROLE_SCOPES["readonly"])


def create_access_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT access token."""
    scopes = _role_to_scopes(role)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "scopes": scopes,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload, settings.api_secret_key, algorithm=settings.jwt_algorithm
    )


def _try_jwt_auth(token: str) -> dict | None:
    """Try to decode as JWT. Returns user context dict or None."""
    try:
        payload = jwt.decode(
            token, settings.api_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role", "user"),
            "scopes": payload.get("scopes", []),
            "auth_type": "jwt",
            "api_key_hash": None,
            "rate_limit": None,
        }
    except JWTError:
        return None


def _try_api_key_auth(token: str, db: Session) -> dict | None:
    """Try to authenticate via API key. Returns user context dict or None."""
    key_hash = hashlib.sha256(token.encode()).hexdigest()
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    if not api_key:
        return None
    if not api_key.is_active:
        return None
    if api_key.expires_at:
        expires = api_key.expires_at
        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes (e.g. from SQLite)
        if expires.tzinfo is None:
            now = now.replace(tzinfo=None)
        if expires < now:
            return None

    # Update last_used
    api_key.last_used = datetime.now(timezone.utc)
    db.commit()

    # Look up the user for role info
    user = db.query(User).filter(User.id == api_key.user_id).first()
    role = user.role if user else "user"
    scopes = api_key.scopes_list if api_key.scopes_list else _role_to_scopes(role)

    return {
        "user_id": api_key.user_id,
        "username": user.username if user else None,
        "role": role,
        "scopes": scopes,
        "auth_type": "api_key",
        "api_key_hash": key_hash,
        "rate_limit": api_key.rate_limit,
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    db: Session = Depends(get_db),
):
    """Extract and verify the current user from JWT token or API key."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Try JWT first
    user_ctx = _try_jwt_auth(token)
    if user_ctx:
        return user_ctx

    # Try API key
    user_ctx = _try_api_key_auth(token, db)
    if user_ctx:
        return user_ctx

    # Fallback: check against legacy api_secret_key for backward compat
    if token == settings.api_secret_key:
        return {
            "user_id": None,
            "username": "legacy",
            "role": "admin",
            "scopes": _role_to_scopes("admin"),
            "auth_type": "legacy",
            "api_key_hash": None,
            "rate_limit": None,
        }

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid credentials",
    )


def require_scope(scope: str):
    """Dependency factory — require a specific scope for access.

    Usage: @router.get("/admin", dependencies=[Depends(require_scope("admin"))])
    """

    async def _check_scope(user: dict = Depends(get_current_user)):
        user_scopes = _expand_scopes(user.get("scopes", []))
        if scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope: requires '{scope}'",
            )
        return user

    return _check_scope
