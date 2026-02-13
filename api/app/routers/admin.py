"""Admin endpoints — system user management, Oracle profile management, stats."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, require_scope
from app.models.admin import (
    AdminOracleProfileListResponse,
    AdminOracleProfileResponse,
    AdminStatsResponse,
    PasswordResetResponse,
    RoleUpdateRequest,
    StatusUpdateRequest,
    SystemUserListResponse,
    SystemUserResponse,
)
from app.services.admin_service import AdminService
from app.services.audit import AuditService, get_audit_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


def _get_client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ─── System User Management ────────────────────────────────────────


@router.get(
    "/users",
    response_model=SystemUserListResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def list_system_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query(
        "created_at",
        pattern=r"^(username|role|created_at|last_login|is_active)$",
    ),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    svc: AdminService = Depends(_get_admin_service),
) -> SystemUserListResponse:
    """List all system users (admin only). Supports search, sort, pagination."""
    users, total = svc.list_users(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SystemUserListResponse(
        users=[SystemUserResponse(**u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/users/{user_id}",
    response_model=SystemUserResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def get_system_user(
    user_id: str,
    svc: AdminService = Depends(_get_admin_service),
) -> SystemUserResponse:
    """Get a single system user by ID (admin only)."""
    user = svc.get_user_detail(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return SystemUserResponse(**user)


@router.patch(
    "/users/{user_id}/role",
    response_model=SystemUserResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def update_user_role(
    user_id: str,
    body: RoleUpdateRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: AdminService = Depends(_get_admin_service),
    audit: AuditService = Depends(get_audit_service),
) -> SystemUserResponse:
    """Change a user's role (admin only). Cannot change own role."""
    # Get old role for audit
    old_detail = svc.get_user_detail(user_id)
    if not old_detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    old_role = old_detail["role"]

    try:
        svc.update_role(user_id, body.role, _user.get("user_id", ""))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    audit.log_admin_role_changed(
        target_user_id=user_id,
        old_role=old_role,
        new_role=body.role,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()

    detail = svc.get_user_detail(user_id)
    return SystemUserResponse(**detail)  # type: ignore[arg-type]


@router.post(
    "/users/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def reset_user_password(
    user_id: str,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: AdminService = Depends(_get_admin_service),
    audit: AuditService = Depends(get_audit_service),
) -> PasswordResetResponse:
    """Reset a user's password to a temporary value (admin only)."""
    result = svc.reset_password(user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _user_obj, temp_password = result

    audit.log_admin_password_reset(
        target_user_id=user_id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()

    return PasswordResetResponse(
        temporary_password=temp_password,
        message="Password has been reset. Share this temporary password securely.",
    )


@router.patch(
    "/users/{user_id}/status",
    response_model=SystemUserResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def update_user_status(
    user_id: str,
    body: StatusUpdateRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: AdminService = Depends(_get_admin_service),
    audit: AuditService = Depends(get_audit_service),
) -> SystemUserResponse:
    """Activate or deactivate a user (admin only). Cannot deactivate self."""
    try:
        svc.update_status(user_id, body.is_active, _user.get("user_id", ""))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    audit.log_admin_status_changed(
        target_user_id=user_id,
        new_status=body.is_active,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()

    detail = svc.get_user_detail(user_id)
    return SystemUserResponse(**detail)  # type: ignore[arg-type]


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def get_admin_stats(
    svc: AdminService = Depends(_get_admin_service),
) -> AdminStatsResponse:
    """Get aggregated system statistics (admin only)."""
    stats = svc.get_stats()
    return AdminStatsResponse(**stats)


# ─── Oracle Profile Management ────────────────────────────────────


@router.get(
    "/profiles",
    response_model=AdminOracleProfileListResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def list_oracle_profiles(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("created_at", pattern=r"^(name|birthday|created_at)$"),
    sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
    include_deleted: bool = Query(False),
    svc: AdminService = Depends(_get_admin_service),
) -> AdminOracleProfileListResponse:
    """List all Oracle profiles (admin only). Optionally include soft-deleted."""
    profiles, total = svc.list_oracle_profiles(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        include_deleted=include_deleted,
    )
    return AdminOracleProfileListResponse(
        profiles=[AdminOracleProfileResponse(**p) for p in profiles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete(
    "/profiles/{profile_id}",
    response_model=AdminOracleProfileResponse,
    dependencies=[Depends(require_scope("admin"))],
)
def delete_oracle_profile(
    profile_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: AdminService = Depends(_get_admin_service),
    audit: AuditService = Depends(get_audit_service),
) -> AdminOracleProfileResponse:
    """Hard-delete an Oracle profile and its readings (admin only)."""
    profile = svc.delete_oracle_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    audit.log_admin_profile_deleted(
        profile_id=profile_id,
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()

    return AdminOracleProfileResponse(**profile)
