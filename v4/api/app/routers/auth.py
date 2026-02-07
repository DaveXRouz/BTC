"""Authentication endpoints — JWT + API key management."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.auth import (
    APIKeyCreate,
    APIKeyResponse,
    LoginRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate and receive a JWT token."""
    # TODO: Verify credentials against users table
    # TODO: Generate JWT token
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented",
    )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreate):
    """Create a new API key for programmatic access."""
    # TODO: Generate API key, hash it, store in api_keys table
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API key management not yet implemented",
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys():
    """List API keys for the current user."""
    # TODO: Query api_keys table for current user
    return []


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: str):
    """Revoke an API key."""
    # TODO: Set is_active=False on api_keys table
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API key revocation not yet implemented",
    )
