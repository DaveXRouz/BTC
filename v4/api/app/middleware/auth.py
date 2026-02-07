"""Authentication middleware — JWT verification and API key validation."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
):
    """Extract and verify the current user from JWT token or API key.

    TODO: Implement JWT decode + verification
    TODO: Implement API key lookup and validation
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Decode JWT token
    # TODO: Look up user in database
    # TODO: Check token expiration
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not yet implemented",
    )


def require_scope(scope: str):
    """Dependency factory — require a specific scope for API key auth.

    Usage: @router.get("/admin", dependencies=[Depends(require_scope("admin"))])
    """

    async def _check_scope(user=Depends(get_current_user)):
        # TODO: Check user scopes
        pass

    return _check_scope
