# SESSION 38 SPEC — Admin Panel: User Management

**Block:** Admin & DevOps (Sessions 38-40)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium
**Dependencies:** Sessions 2-3 (auth system + user API), Sessions 19-25 (frontend core + Layout)

---

## TL;DR

- Build admin-only API endpoints in a new `api/app/routers/admin.py` router for listing system users, editing roles, resetting passwords, deactivating/reactivating accounts, and viewing admin statistics
- Build admin-only API endpoints for managing Oracle profiles: list all with reading counts, hard-delete
- Build frontend admin pages at `/admin/users` and `/admin/profiles` with sortable, searchable, paginated tables using existing Tailwind dark theme
- Enforce `admin` scope on all admin routes via `require_scope("admin")`; non-admin users receive HTTP 403 at the API and a 403 page on the frontend
- Add i18n strings (EN + FA) for all admin UI text; support RTL layout for Persian

---

## OBJECTIVES

1. **Create admin Pydantic models** (`api/app/models/admin.py`) -- Request/response models for all admin endpoints: `SystemUserResponse`, `SystemUserListResponse`, `RoleUpdateRequest`, `StatusUpdateRequest`, `PasswordResetResponse`, `AdminStatsResponse`, `AdminOracleProfileResponse`, `AdminOracleProfileListResponse`
2. **Create admin service layer** (`api/app/services/admin_service.py`) -- Business logic for user listing with reading counts, role changes with self-protection, password reset via bcrypt, status toggling, Oracle profile listing and deletion
3. **Create admin API router** (`api/app/routers/admin.py`) -- Eight endpoints: `GET /users`, `GET /users/{id}`, `PATCH /users/{id}/role`, `POST /users/{id}/reset-password`, `PATCH /users/{id}/status`, `GET /stats`, `GET /profiles`, `DELETE /profiles/{id}` -- all requiring `admin` scope
4. **Register admin router** in `api/app/main.py` at `/api/admin` prefix
5. **Add audit logging** for all admin actions via new methods in `AuditService`
6. **Create frontend TypeScript types** for admin domain objects in `frontend/src/types/index.ts`
7. **Create frontend API client** methods in `frontend/src/services/api.ts` under an `admin` namespace
8. **Create React Query hooks** (`frontend/src/hooks/useAdmin.ts`) for all admin API calls with proper cache invalidation
9. **Build `AdminGuard` component** that checks admin role and renders 403 page for non-admin users
10. **Build `UserTable` component** with sortable columns, search, pagination, role/status badges
11. **Build `UserActions` component** with confirmation dialogs for role change, password reset, activate/deactivate
12. **Build `ProfileTable` component** with Oracle profile listing, search, pagination, and delete action
13. **Build `ProfileActions` component** with delete confirmation and cascade warning
14. **Build admin pages** (`Admin.tsx`, `AdminUsers.tsx`, `AdminProfiles.tsx`) with tab navigation
15. **Wire routes** in `App.tsx` and conditional admin nav link in `Layout.tsx`
16. **Add bilingual i18n** (EN + FA) with ~45 admin translation keys each

---

## PREREQUISITES

- [ ] `users` table exists with columns: `id` (VARCHAR 36), `username`, `password_hash`, `salt`, `role`, `created_at`, `updated_at`, `last_login`, `is_active`
  - Verify: `test -f api/app/orm/user.py && grep -q "is_active" api/app/orm/user.py && echo "OK"`
- [ ] `oracle_users` table exists with columns: `id`, `name`, `name_persian`, `birthday`, `mother_name`, etc.
  - Verify: `test -f api/app/orm/oracle_user.py && echo "OK"`
- [ ] `oracle_readings` table exists (for reading count aggregation)
  - Verify: `test -f api/app/orm/oracle_reading.py && echo "OK"`
- [ ] Auth middleware with `require_scope()` dependency works and `admin` is in `_ROLE_SCOPES`
  - Verify: `grep -q '"admin"' api/app/middleware/auth.py && echo "OK"`
- [ ] Frontend React + TypeScript + Tailwind + Vite is functional
  - Verify: `test -f frontend/src/App.tsx && test -f frontend/src/components/Layout.tsx && echo "OK"`
- [ ] `@tanstack/react-query` is available (used by existing hooks like `useOracleUsers`)
  - Verify: `grep -q "tanstack/react-query" frontend/package.json && echo "OK"`
- [ ] i18n configured with `react-i18next`, locales at `frontend/src/locales/en.json` and `fa.json`
  - Verify: `test -f frontend/src/locales/en.json && test -f frontend/src/locales/fa.json && echo "OK"`
- [ ] Existing API client pattern in `frontend/src/services/api.ts` with `request<T>()` helper
  - Verify: `grep -q "function request" frontend/src/services/api.ts && echo "OK"`

---

## FILES TO CREATE

| File                                                            | Purpose                                                                                      |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `api/app/models/admin.py`                                       | Pydantic request/response models for admin endpoints                                         |
| `api/app/services/admin_service.py`                             | Business logic: user listing, role change, password reset, status toggle, profile management |
| `api/app/routers/admin.py`                                      | Admin-only API router with 8 endpoints                                                       |
| `api/tests/test_admin.py`                                       | 23 API tests covering auth, CRUD, edge cases                                                 |
| `frontend/src/pages/Admin.tsx`                                  | Admin page shell with tab navigation (Users / Profiles)                                      |
| `frontend/src/pages/AdminUsers.tsx`                             | Admin users sub-page composing UserTable + UserActions                                       |
| `frontend/src/pages/AdminProfiles.tsx`                          | Admin profiles sub-page composing ProfileTable + ProfileActions                              |
| `frontend/src/components/admin/UserTable.tsx`                   | Sortable, searchable, paginated system user table                                            |
| `frontend/src/components/admin/UserActions.tsx`                 | Action buttons with confirmation dialogs for user management                                 |
| `frontend/src/components/admin/ProfileTable.tsx`                | Sortable, searchable, paginated Oracle profile table                                         |
| `frontend/src/components/admin/ProfileActions.tsx`              | Delete action with cascade warning confirmation                                              |
| `frontend/src/components/admin/AdminGuard.tsx`                  | Route guard checking admin role, renders 403 for non-admin                                   |
| `frontend/src/hooks/useAdmin.ts`                                | React Query hooks for all admin API calls                                                    |
| `frontend/src/components/admin/__tests__/UserTable.test.tsx`    | 5 tests for UserTable component                                                              |
| `frontend/src/components/admin/__tests__/UserActions.test.tsx`  | 4 tests for UserActions component                                                            |
| `frontend/src/components/admin/__tests__/ProfileTable.test.tsx` | 3 tests for ProfileTable component                                                           |
| `frontend/src/components/admin/__tests__/AdminGuard.test.tsx`   | 3 tests for AdminGuard component                                                             |
| `frontend/src/pages/__tests__/Admin.test.tsx`                   | 2 tests for Admin page shell                                                                 |

## FILES TO MODIFY

| File                                 | What Changes                                                                                                                                 |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/app/main.py`                    | Add `from app.routers import admin` and register at `/api/admin` prefix with `tags=["admin"]`                                                |
| `api/app/services/audit.py`          | Add 4 new methods: `log_admin_role_changed()`, `log_admin_password_reset()`, `log_admin_status_changed()`, `log_admin_profile_deleted()`     |
| `frontend/src/App.tsx`               | Add `/admin/*` routes wrapped in `AdminGuard`, import new pages                                                                              |
| `frontend/src/components/Layout.tsx` | Add conditional "Admin" nav link visible only when user role is admin                                                                        |
| `frontend/src/services/api.ts`       | Add `admin` namespace with 7 typed fetch methods                                                                                             |
| `frontend/src/types/index.ts`        | Add `SystemUser`, `SystemUserListResponse`, `AdminOracleProfile`, `AdminOracleProfileListResponse`, `PasswordResetResult`, sort type aliases |
| `frontend/src/locales/en.json`       | Add `nav.admin` and `admin.*` keys (~45 strings)                                                                                             |
| `frontend/src/locales/fa.json`       | Add `nav.admin` and `admin.*` keys (~45 Persian strings)                                                                                     |

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: API Models and Admin Service (~45 min)

**Tasks:**

1. Create `api/app/models/admin.py` with all Pydantic models:

   ```python
   """Pydantic models for admin management endpoints."""
   from __future__ import annotations
   from datetime import date, datetime
   from pydantic import BaseModel, ConfigDict, Field

   class SystemUserResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: str
       username: str
       role: str
       created_at: datetime
       updated_at: datetime
       last_login: datetime | None
       is_active: bool
       reading_count: int = 0

   class SystemUserListResponse(BaseModel):
       users: list[SystemUserResponse]
       total: int
       limit: int
       offset: int

   class RoleUpdateRequest(BaseModel):
       role: str = Field(..., pattern=r"^(admin|user|readonly)$")

   class StatusUpdateRequest(BaseModel):
       is_active: bool

   class PasswordResetResponse(BaseModel):
       temporary_password: str
       message: str

   class AdminStatsResponse(BaseModel):
       total_users: int
       active_users: int
       inactive_users: int
       total_oracle_profiles: int
       total_readings: int
       readings_today: int
       users_by_role: dict[str, int]

   class AdminOracleProfileResponse(BaseModel):
       model_config = ConfigDict(from_attributes=True)
       id: int
       name: str
       name_persian: str | None = None
       birthday: date
       country: str | None = None
       city: str | None = None
       created_at: datetime
       updated_at: datetime
       deleted_at: datetime | None = None
       reading_count: int = 0

   class AdminOracleProfileListResponse(BaseModel):
       profiles: list[AdminOracleProfileResponse]
       total: int
       limit: int
       offset: int
   ```

2. Create `api/app/services/admin_service.py` with business logic:

   ```python
   """Admin service — business logic for user and profile management."""
   from __future__ import annotations
   import logging
   import secrets
   import bcrypt as _bcrypt
   from datetime import date, datetime, timezone
   from sqlalchemy import func, case
   from sqlalchemy.orm import Session
   from app.orm.user import User
   from app.orm.oracle_user import OracleUser
   from app.orm.oracle_reading import OracleReading

   logger = logging.getLogger(__name__)

   class AdminService:
       def __init__(self, db: Session) -> None:
           self.db = db

       def list_users(
           self, *, limit: int = 20, offset: int = 0,
           search: str | None = None, sort_by: str = "created_at",
           sort_order: str = "desc",
       ) -> tuple[list[dict], int]:
           """List system users with optional search, sort, and pagination.
           Returns (users_list, total_count)."""
           # Build base query
           # Join with subquery for reading count (COUNT oracle_readings per user_id)
           # Note: users.id is VARCHAR(36), oracle_readings.user_id is INTEGER
           # For now, reading_count = 0 for all system users (no FK link exists)
           ...

       def get_user_detail(self, user_id: str) -> dict | None:
           """Get a single system user by ID with reading count."""
           ...

       def update_role(self, user_id: str, new_role: str, admin_user_id: str) -> User:
           """Change a user's role. Raises ValueError if trying to modify own role."""
           if user_id == admin_user_id:
               raise ValueError("Cannot modify your own role")
           ...

       def reset_password(self, user_id: str) -> tuple[User, str]:
           """Generate temp password, bcrypt hash it, store it. Returns (user, plaintext)."""
           temp_password = secrets.token_urlsafe(16)
           hashed = _bcrypt.hashpw(temp_password.encode("utf-8"), _bcrypt.gensalt())
           ...
           return user, temp_password

       def update_status(self, user_id: str, is_active: bool, admin_user_id: str) -> User:
           """Activate or deactivate. Raises ValueError if trying to deactivate self."""
           if user_id == admin_user_id and not is_active:
               raise ValueError("Cannot deactivate your own account")
           ...

       def get_stats(self) -> dict:
           """Aggregate stats: user counts by role/status, reading counts, today's readings."""
           ...

       def list_oracle_profiles(
           self, *, limit: int = 20, offset: int = 0,
           search: str | None = None, sort_by: str = "created_at",
           sort_order: str = "desc", include_deleted: bool = False,
       ) -> tuple[list[dict], int]:
           """List all Oracle profiles with reading counts."""
           ...

       def delete_oracle_profile(self, profile_id: int) -> OracleUser | None:
           """Hard-delete an Oracle profile. Returns the deleted profile or None if not found."""
           ...
   ```

   Key implementation details:
   - `reset_password` uses `secrets.token_urlsafe(16)` for temp password, `bcrypt.hashpw()` for hashing
   - `update_role` validates against `admin`, `user`, `readonly` (Pydantic does this too, belt-and-suspenders)
   - `list_users` supports sorting by: `username`, `role`, `created_at`, `last_login`, `is_active`
   - `list_oracle_profiles` supports sorting by: `name`, `birthday`, `created_at`
   - Reading count for Oracle profiles uses subquery: `SELECT COUNT(*) FROM oracle_readings WHERE user_id = oracle_users.id`
   - Reading count for system users is 0 for now (no direct FK between `users` and `oracle_readings`)

**STOP Checkpoint:**

- [ ] `api/app/models/admin.py` has all 9 model classes with proper types and no `any`
- [ ] `api/app/services/admin_service.py` has all 8 methods with type hints and docstrings
- [ ] No bare `except:` clauses anywhere
- [ ] Verify: `cd api && python3 -c "from app.models.admin import SystemUserResponse, AdminStatsResponse; from app.services.admin_service import AdminService; print('Imports OK')"`

---

### Phase 2: Admin API Router and Audit Logging (~60 min)

**Tasks:**

1. Create `api/app/routers/admin.py` with 8 admin-only endpoints:

   ```python
   """Admin endpoints — system user management, Oracle profile management, stats."""
   from __future__ import annotations
   import logging
   from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
   from sqlalchemy.orm import Session
   from app.database import get_db
   from app.middleware.auth import get_current_user, require_scope
   from app.models.admin import (
       AdminOracleProfileListResponse, AdminOracleProfileResponse, AdminStatsResponse,
       PasswordResetResponse, RoleUpdateRequest, StatusUpdateRequest,
       SystemUserListResponse, SystemUserResponse,
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

   @router.get("/users", response_model=SystemUserListResponse,
               dependencies=[Depends(require_scope("admin"))])
   def list_system_users(
       limit: int = Query(20, ge=1, le=100),
       offset: int = Query(0, ge=0),
       search: str | None = Query(None, max_length=100),
       sort_by: str = Query("created_at",
                            pattern=r"^(username|role|created_at|last_login|is_active)$"),
       sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
       svc: AdminService = Depends(_get_admin_service),
   ) -> SystemUserListResponse:
       """List all system users (admin only). Supports search, sort, pagination."""
       users, total = svc.list_users(
           limit=limit, offset=offset, search=search,
           sort_by=sort_by, sort_order=sort_order,
       )
       return SystemUserListResponse(
           users=[SystemUserResponse(**u) for u in users],
           total=total, limit=limit, offset=offset,
       )

   @router.get("/users/{user_id}", response_model=SystemUserResponse,
               dependencies=[Depends(require_scope("admin"))])
   def get_system_user(
       user_id: str,
       svc: AdminService = Depends(_get_admin_service),
   ) -> SystemUserResponse:
       """Get a single system user by ID (admin only)."""
       user = svc.get_user_detail(user_id)
       if not user:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                               detail="User not found")
       return SystemUserResponse(**user)

   @router.patch("/users/{user_id}/role", response_model=SystemUserResponse,
                 dependencies=[Depends(require_scope("admin"))])
   def update_user_role(
       user_id: str, body: RoleUpdateRequest, request: Request,
       _user: dict = Depends(get_current_user),
       svc: AdminService = Depends(_get_admin_service),
       audit: AuditService = Depends(get_audit_service),
   ) -> SystemUserResponse:
       """Change a user's role (admin only). Cannot change own role."""
       try:
           user = svc.update_role(user_id, body.role, _user.get("user_id", ""))
       except ValueError as exc:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                               detail=str(exc))
       audit.log_admin_role_changed(
           target_user_id=user_id, old_role="", new_role=body.role,
           ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"),
       )
       svc.db.commit()
       detail = svc.get_user_detail(user_id)
       return SystemUserResponse(**detail)

   @router.post("/users/{user_id}/reset-password",
                response_model=PasswordResetResponse,
                dependencies=[Depends(require_scope("admin"))])
   def reset_user_password(
       user_id: str, request: Request,
       _user: dict = Depends(get_current_user),
       svc: AdminService = Depends(_get_admin_service),
       audit: AuditService = Depends(get_audit_service),
   ) -> PasswordResetResponse:
       """Reset a user's password to a temporary value (admin only)."""
       result = svc.reset_password(user_id)
       if not result:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                               detail="User not found")
       user, temp_password = result
       audit.log_admin_password_reset(
           target_user_id=user_id,
           ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"),
       )
       svc.db.commit()
       return PasswordResetResponse(
           temporary_password=temp_password,
           message="Password has been reset. Share this temporary password securely.",
       )

   @router.patch("/users/{user_id}/status", response_model=SystemUserResponse,
                 dependencies=[Depends(require_scope("admin"))])
   def update_user_status(
       user_id: str, body: StatusUpdateRequest, request: Request,
       _user: dict = Depends(get_current_user),
       svc: AdminService = Depends(_get_admin_service),
       audit: AuditService = Depends(get_audit_service),
   ) -> SystemUserResponse:
       """Activate or deactivate a user (admin only). Cannot deactivate self."""
       try:
           user = svc.update_status(
               user_id, body.is_active, _user.get("user_id", ""))
       except ValueError as exc:
           raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                               detail=str(exc))
       audit.log_admin_status_changed(
           target_user_id=user_id, new_status=body.is_active,
           ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"),
       )
       svc.db.commit()
       detail = svc.get_user_detail(user_id)
       return SystemUserResponse(**detail)

   @router.get("/stats", response_model=AdminStatsResponse,
               dependencies=[Depends(require_scope("admin"))])
   def get_admin_stats(
       svc: AdminService = Depends(_get_admin_service),
   ) -> AdminStatsResponse:
       """Get aggregated system statistics (admin only)."""
       stats = svc.get_stats()
       return AdminStatsResponse(**stats)

   # ─── Oracle Profile Management ────────────────────────────────────

   @router.get("/profiles", response_model=AdminOracleProfileListResponse,
               dependencies=[Depends(require_scope("admin"))])
   def list_oracle_profiles(
       limit: int = Query(20, ge=1, le=100),
       offset: int = Query(0, ge=0),
       search: str | None = Query(None, max_length=100),
       sort_by: str = Query("created_at",
                            pattern=r"^(name|birthday|created_at)$"),
       sort_order: str = Query("desc", pattern=r"^(asc|desc)$"),
       include_deleted: bool = Query(False),
       svc: AdminService = Depends(_get_admin_service),
   ) -> AdminOracleProfileListResponse:
       """List all Oracle profiles (admin only). Optionally include soft-deleted."""
       profiles, total = svc.list_oracle_profiles(
           limit=limit, offset=offset, search=search,
           sort_by=sort_by, sort_order=sort_order,
           include_deleted=include_deleted,
       )
       return AdminOracleProfileListResponse(
           profiles=[AdminOracleProfileResponse(**p) for p in profiles],
           total=total, limit=limit, offset=offset,
       )

   @router.delete("/profiles/{profile_id}",
                  response_model=AdminOracleProfileResponse,
                  dependencies=[Depends(require_scope("admin"))])
   def delete_oracle_profile(
       profile_id: int, request: Request,
       _user: dict = Depends(get_current_user),
       svc: AdminService = Depends(_get_admin_service),
       audit: AuditService = Depends(get_audit_service),
   ) -> AdminOracleProfileResponse:
       """Hard-delete an Oracle profile and its readings (admin only)."""
       profile = svc.delete_oracle_profile(profile_id)
       if not profile:
           raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                               detail="Profile not found")
       audit.log_admin_profile_deleted(
           profile_id=profile_id,
           ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"),
       )
       svc.db.commit()
       return AdminOracleProfileResponse(**profile)
   ```

2. Register the router in `api/app/main.py` -- add after the existing router registrations:

   ```python
   from app.routers import admin
   app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
   ```

3. Add 4 audit methods to `api/app/services/audit.py`:

   ```python
   def log_admin_role_changed(
       self, target_user_id: str, old_role: str, new_role: str,
       *, ip: str | None = None, key_hash: str | None = None,
   ):
       return self.log(
           "admin.role_changed", resource_type="user",
           details={"target_user_id": target_user_id,
                    "old_role": old_role, "new_role": new_role},
           ip_address=ip, api_key_hash=key_hash,
       )

   def log_admin_password_reset(
       self, target_user_id: str,
       *, ip: str | None = None, key_hash: str | None = None,
   ):
       return self.log(
           "admin.password_reset", resource_type="user",
           details={"target_user_id": target_user_id},
           ip_address=ip, api_key_hash=key_hash,
       )

   def log_admin_status_changed(
       self, target_user_id: str, new_status: bool,
       *, ip: str | None = None, key_hash: str | None = None,
   ):
       return self.log(
           "admin.status_changed", resource_type="user",
           details={"target_user_id": target_user_id,
                    "new_status": new_status},
           ip_address=ip, api_key_hash=key_hash,
       )

   def log_admin_profile_deleted(
       self, profile_id: int,
       *, ip: str | None = None, key_hash: str | None = None,
   ):
       return self.log(
           "admin.profile_deleted", resource_type="oracle_user",
           resource_id=profile_id,
           ip_address=ip, api_key_hash=key_hash,
       )
   ```

**STOP Checkpoint:**

- [ ] All 8 endpoints require `admin` scope via `require_scope("admin")`
- [ ] Router registered in `main.py` at `/api/admin`
- [ ] Self-modification guards: role change and deactivation check `_user.get("user_id") == user_id`
- [ ] All endpoints have proper response models and error handling
- [ ] 4 audit methods added to `AuditService`
- [ ] Verify: `cd api && python3 -c "from app.routers.admin import router; print(f'{len(router.routes)} routes')"`

---

### Phase 3: API Tests (~45 min)

**Tasks:**

1. Create `api/tests/test_admin.py` with 23 test cases:

   Test fixtures:

   ```python
   @pytest.fixture
   def db():
       """Yield a test database session with rollback."""
       ...

   @pytest.fixture
   def admin_user(db) -> tuple[User, str]:
       """Create admin user, return (user_obj, jwt_token)."""
       user = User(id=str(uuid4()), username="testadmin",
                   password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode(),
                   role="admin")
       db.add(user); db.commit()
       token = create_access_token(user.id, user.username, user.role)
       return user, token

   @pytest.fixture
   def regular_user(db) -> tuple[User, str]:
       """Create regular user, return (user_obj, jwt_token)."""
       ...

   @pytest.fixture
   def readonly_user(db) -> tuple[User, str]:
       """Create readonly user, return (user_obj, jwt_token)."""
       ...

   @pytest.fixture
   def sample_oracle_profiles(db) -> list[OracleUser]:
       """Create 5 Oracle profiles for testing."""
       ...
   ```

2. Use `TestClient` from FastAPI with SQLite in-memory backend for test isolation.

3. Each test verifies one behavior -- success paths, failure paths, edge cases, and authorization.

**STOP Checkpoint:**

- [ ] All 23 tests pass: `cd api && python3 -m pytest tests/test_admin.py -v`
- [ ] No test depends on another test's state
- [ ] Success and failure paths both covered for every endpoint

---

### Phase 4: Frontend Types, API Client, and Hooks (~30 min)

**Tasks:**

1. Add admin types to `frontend/src/types/index.ts` -- append after the existing `// --- Auth ---` section:

   ```typescript
   // ─── Admin ───

   export interface SystemUser {
     id: string;
     username: string;
     role: string;
     created_at: string;
     updated_at: string;
     last_login: string | null;
     is_active: boolean;
     reading_count: number;
   }

   export interface SystemUserListResponse {
     users: SystemUser[];
     total: number;
     limit: number;
     offset: number;
   }

   export interface AdminOracleProfile {
     id: number;
     name: string;
     name_persian: string | null;
     birthday: string;
     country: string | null;
     city: string | null;
     created_at: string;
     updated_at: string;
     deleted_at: string | null;
     reading_count: number;
   }

   export interface AdminOracleProfileListResponse {
     profiles: AdminOracleProfile[];
     total: number;
     limit: number;
     offset: number;
   }

   export interface PasswordResetResult {
     temporary_password: string;
     message: string;
   }

   export interface AdminStats {
     total_users: number;
     active_users: number;
     inactive_users: number;
     total_oracle_profiles: number;
     total_readings: number;
     readings_today: number;
     users_by_role: Record<string, number>;
   }

   export type UserSortField =
     | "username"
     | "role"
     | "created_at"
     | "last_login"
     | "is_active";
   export type ProfileSortField = "name" | "birthday" | "created_at";
   export type SortOrder = "asc" | "desc";
   ```

2. Add `admin` namespace to `frontend/src/services/api.ts` -- append after the existing `learning` section:

   ```typescript
   // ─── Admin ───

   export const admin = {
     listUsers: (params?: {
       limit?: number;
       offset?: number;
       search?: string;
       sort_by?: import("@/types").UserSortField;
       sort_order?: import("@/types").SortOrder;
     }) => {
       const query = new URLSearchParams();
       if (params?.limit) query.set("limit", String(params.limit));
       if (params?.offset) query.set("offset", String(params.offset));
       if (params?.search) query.set("search", params.search);
       if (params?.sort_by) query.set("sort_by", params.sort_by);
       if (params?.sort_order) query.set("sort_order", params.sort_order);
       return request<import("@/types").SystemUserListResponse>(
         `/admin/users?${query}`,
       );
     },
     getUser: (id: string) =>
       request<import("@/types").SystemUser>(`/admin/users/${id}`),
     updateRole: (id: string, role: string) =>
       request<import("@/types").SystemUser>(`/admin/users/${id}/role`, {
         method: "PATCH",
         body: JSON.stringify({ role }),
       }),
     resetPassword: (id: string) =>
       request<import("@/types").PasswordResetResult>(
         `/admin/users/${id}/reset-password`,
         { method: "POST" },
       ),
     updateStatus: (id: string, is_active: boolean) =>
       request<import("@/types").SystemUser>(`/admin/users/${id}/status`, {
         method: "PATCH",
         body: JSON.stringify({ is_active }),
       }),
     stats: () => request<import("@/types").AdminStats>("/admin/stats"),
     listProfiles: (params?: {
       limit?: number;
       offset?: number;
       search?: string;
       sort_by?: import("@/types").ProfileSortField;
       sort_order?: import("@/types").SortOrder;
       include_deleted?: boolean;
     }) => {
       const query = new URLSearchParams();
       if (params?.limit) query.set("limit", String(params.limit));
       if (params?.offset) query.set("offset", String(params.offset));
       if (params?.search) query.set("search", params.search);
       if (params?.sort_by) query.set("sort_by", params.sort_by);
       if (params?.sort_order) query.set("sort_order", params.sort_order);
       if (params?.include_deleted) query.set("include_deleted", "true");
       return request<import("@/types").AdminOracleProfileListResponse>(
         `/admin/profiles?${query}`,
       );
     },
     deleteProfile: (id: number) =>
       request<import("@/types").AdminOracleProfile>(`/admin/profiles/${id}`, {
         method: "DELETE",
       }),
   };
   ```

3. Create `frontend/src/hooks/useAdmin.ts` with React Query hooks following the same pattern as `useOracleUsers.ts`:

   ```typescript
   import {
     useQuery,
     useMutation,
     useQueryClient,
   } from "@tanstack/react-query";
   import { admin as api } from "@/services/api";
   import type { UserSortField, SortOrder, ProfileSortField } from "@/types";

   const USERS_KEY = ["admin", "users"] as const;
   const PROFILES_KEY = ["admin", "profiles"] as const;
   const STATS_KEY = ["admin", "stats"] as const;

   export function useAdminUsers(params?: {
     limit?: number;
     offset?: number;
     search?: string;
     sort_by?: UserSortField;
     sort_order?: SortOrder;
   }) {
     return useQuery({
       queryKey: [...USERS_KEY, params],
       queryFn: () => api.listUsers(params),
     });
   }

   export function useAdminUser(id: string | null) {
     return useQuery({
       queryKey: [...USERS_KEY, id],
       queryFn: () => api.getUser(id!),
       enabled: id !== null,
     });
   }

   export function useUpdateRole() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: ({ id, role }: { id: string; role: string }) =>
         api.updateRole(id, role),
       onSuccess: () => qc.invalidateQueries({ queryKey: USERS_KEY }),
     });
   }

   export function useResetPassword() {
     return useMutation({
       mutationFn: (id: string) => api.resetPassword(id),
     });
   }

   export function useUpdateStatus() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
         api.updateStatus(id, is_active),
       onSuccess: () => qc.invalidateQueries({ queryKey: USERS_KEY }),
     });
   }

   export function useAdminStats() {
     return useQuery({
       queryKey: STATS_KEY,
       queryFn: () => api.stats(),
     });
   }

   export function useAdminProfiles(params?: {
     limit?: number;
     offset?: number;
     search?: string;
     sort_by?: ProfileSortField;
     sort_order?: SortOrder;
     include_deleted?: boolean;
   }) {
     return useQuery({
       queryKey: [...PROFILES_KEY, params],
       queryFn: () => api.listProfiles(params),
     });
   }

   export function useDeleteProfile() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: (id: number) => api.deleteProfile(id),
       onSuccess: () => qc.invalidateQueries({ queryKey: PROFILES_KEY }),
     });
   }
   ```

**STOP Checkpoint:**

- [ ] Types compile: `cd frontend && npx tsc --noEmit`
- [ ] API client methods match the 8 backend endpoints exactly
- [ ] All hooks use distinct query keys for proper cache isolation
- [ ] No `any` type used anywhere

---

### Phase 5: Frontend Components -- Tables, Actions, and Guard (~60 min)

**Tasks:**

1. **`AdminGuard.tsx`** -- Checks user role from `localStorage.getItem("nps_user_role")`. If not `"admin"`, renders a styled 403 page with i18n text (`admin.forbidden_title`, `admin.forbidden_message`). If admin, renders `<Outlet />`. Uses `useTranslation` for all text. Supports RTL via `i18n.language === 'fa'`.

2. **`UserTable.tsx`** -- Receives data from parent via props:
   - Props: `users: SystemUser[]`, `total: number`, `loading: boolean`, `sortBy: UserSortField`, `sortOrder: SortOrder`, `onSort: (field: UserSortField) => void`, `onSearch: (query: string) => void`, `page: number`, `pageSize: number`, `onPageChange: (page: number) => void`, `currentUserId: string`
   - Columns: Username (monospace), Role (color-coded badge: admin=purple, user=blue, readonly=gray), Created (formatted date), Last Login (relative time or "Never"), Readings (count), Status (green "Active" / red "Inactive" badge), Actions (renders `UserActions`)
   - Search input with `placeholder={t("admin.search_placeholder")}`, fires `onSearch` with debounced (300ms) value
   - Column headers clickable for sorting, show directional arrow indicator
   - Pagination: "Showing X-Y of Z" text, Previous/Next buttons, per-page selector (10/20/50)
   - Empty state: centered "No users found" message
   - Loading state: 5 skeleton rows with pulsing animation
   - All text through `t()` from `useTranslation`

3. **`UserActions.tsx`** -- Action buttons for a single user row:
   - Props: `user: SystemUser`, `currentUserId: string`, `onRoleChange: (id: string, role: string) => void`, `onResetPassword: (id: string) => void`, `onStatusChange: (id: string, is_active: boolean) => void`
   - **Edit Role**: dropdown button with options admin/user/readonly; clicking an option shows a confirmation dialog: "Change role of {username} to {role}?"
   - **Reset Password**: button; clicking shows confirmation dialog: "Reset password for {username}?"; on success, shows the temporary password in a copy-able text box
   - **Activate/Deactivate**: toggle button; clicking shows confirmation dialog
   - Self-protection: if `user.id === currentUserId`, the Edit Role and Deactivate buttons are disabled with tooltip "Cannot modify your own account"
   - All confirmation dialogs are modal overlays with Cancel/Confirm buttons

4. **`ProfileTable.tsx`** -- Same pattern as UserTable but for Oracle profiles:
   - Props: `profiles: AdminOracleProfile[]`, `total: number`, `loading: boolean`, sort/search/pagination callbacks
   - Columns: Name, Name (Persian), Birthday, Location (country + city), Created, Readings (count), Status (show "Deleted" badge if `deleted_at` is not null), Actions
   - Search by name (both English and Persian)
   - Soft-deleted profiles show with a red "Deleted" badge and grayed-out row

5. **`ProfileActions.tsx`** -- Action buttons for a single profile row:
   - Props: `profile: AdminOracleProfile`, `onDelete: (id: number) => void`
   - **Delete**: red button; clicking shows confirmation dialog with cascade warning: "Delete profile {name}? This will also delete all associated readings. This cannot be undone."
   - If profile is already soft-deleted (`deleted_at` is not null), show "Already deleted" text instead of button

**STOP Checkpoint:**

- [ ] All 5 components render without crashes (verified via TypeScript compilation)
- [ ] RTL layout applied (check `dir` attribute and RTL-aware class usage)
- [ ] No `any` types
- [ ] All user-facing text uses `t()` from `useTranslation`
- [ ] Verify: `cd frontend && npx tsc --noEmit`

---

### Phase 6: Frontend Pages, Routing, and i18n (~45 min)

**Tasks:**

1. **`Admin.tsx`** -- Shell page with:
   - Page header: `t("admin.title")` with subtitle `t("admin.subtitle")`
   - Stats cards row using existing `StatsCard` component (Total Users, Active Users, Total Profiles, Readings Today) -- data from `useAdminStats()`
   - Tab navigation with two `NavLink` elements: "Users" (`/admin/users`) and "Profiles" (`/admin/profiles`)
   - `<Outlet />` for nested route content

2. **`AdminUsers.tsx`** -- Composes `UserTable` and manages state:
   - State: `search`, `sortBy`, `sortOrder`, `page`, `pageSize`
   - Uses `useAdminUsers({ limit: pageSize, offset: page * pageSize, search, sort_by: sortBy, sort_order: sortOrder })`
   - Passes mutation hooks (`useUpdateRole`, `useResetPassword`, `useUpdateStatus`) down to `UserActions`
   - Gets `currentUserId` from `localStorage.getItem("nps_user_id")`

3. **`AdminProfiles.tsx`** -- Composes `ProfileTable` and manages state:
   - Same state management pattern as AdminUsers
   - Uses `useAdminProfiles({ ... })`
   - Toggle checkbox: "Show deleted" (`include_deleted` param)
   - Passes `useDeleteProfile` mutation down to `ProfileActions`

4. **Modify `App.tsx`** -- Add admin routes inside the `<Route element={<Layout />}>` parent:

   ```tsx
   <Route element={<AdminGuard />}>
     <Route path="/admin" element={<Admin />}>
       <Route index element={<Navigate to="/admin/users" replace />} />
       <Route path="users" element={<AdminUsers />} />
       <Route path="profiles" element={<AdminProfiles />} />
     </Route>
   </Route>
   ```

5. **Modify `Layout.tsx`** -- Add conditional admin nav link:

   ```tsx
   // After existing navItems rendering:
   {
     (() => {
       const role = localStorage.getItem("nps_user_role");
       if (role !== "admin") return null;
       return (
         <NavLink
           to="/admin"
           className={({ isActive }) =>
             `block px-4 py-2 mx-2 rounded text-sm ${
               isActive
                 ? "bg-nps-bg-button text-nps-text-bright"
                 : "text-nps-text-dim hover:bg-nps-bg-hover hover:text-nps-text"
             }`
           }
         >
           {t("nav.admin")}
         </NavLink>
       );
     })();
   }
   ```

6. **Add i18n keys to `en.json`** -- Add `"admin"` section and `"nav.admin"`:

   ```json
   "nav": { ...existing..., "admin": "Admin" },
   "admin": {
     "title": "Admin Panel",
     "subtitle": "User & Profile Management",
     "tab_users": "Users",
     "tab_profiles": "Oracle Profiles",
     "users_title": "System Users",
     "profiles_title": "Oracle Profiles",
     "col_username": "Username",
     "col_role": "Role",
     "col_created": "Created",
     "col_last_login": "Last Login",
     "col_readings": "Readings",
     "col_status": "Status",
     "col_actions": "Actions",
     "col_name": "Name",
     "col_name_persian": "Name (Persian)",
     "col_birthday": "Birthday",
     "col_location": "Location",
     "role_admin": "Admin",
     "role_user": "User",
     "role_readonly": "Read Only",
     "status_active": "Active",
     "status_inactive": "Inactive",
     "status_deleted": "Deleted",
     "action_edit_role": "Edit Role",
     "action_reset_password": "Reset Password",
     "action_activate": "Activate",
     "action_deactivate": "Deactivate",
     "action_view_readings": "View Readings",
     "action_delete": "Delete",
     "confirm_role_change": "Change role of {{username}} to {{role}}?",
     "confirm_password_reset": "Reset password for {{username}}? A temporary password will be generated.",
     "confirm_deactivate": "Deactivate {{username}}? They will not be able to log in.",
     "confirm_activate": "Reactivate {{username}}?",
     "confirm_delete_profile": "Delete profile {{name}}? This will also delete all associated readings. This cannot be undone.",
     "password_reset_success": "Temporary password: {{password}} -- Share this securely.",
     "role_updated": "Role updated successfully",
     "status_updated": "Status updated successfully",
     "profile_deleted_success": "Profile deleted successfully",
     "search_placeholder": "Search...",
     "no_users": "No users found",
     "no_profiles": "No profiles found",
     "show_deleted": "Show deleted",
     "never_logged_in": "Never",
     "forbidden_title": "Access Denied",
     "forbidden_message": "You do not have permission to access this page. Admin role required.",
     "page_info": "Showing {{from}}-{{to}} of {{total}}",
     "per_page": "Per page",
     "prev": "Previous",
     "next": "Next",
     "total_users": "Total Users",
     "active_users": "Active Users",
     "total_profiles": "Total Profiles",
     "readings_today": "Readings Today",
     "error_load_users": "Failed to load users",
     "error_load_profiles": "Failed to load profiles",
     "error_update_role": "Failed to update role",
     "error_reset_password": "Failed to reset password",
     "error_update_status": "Failed to update status",
     "error_delete_profile": "Failed to delete profile",
     "cannot_modify_self": "Cannot modify your own account"
   }
   ```

7. **Add corresponding Persian translations to `fa.json`** with identical key structure. Key translations:
   - `"title": "پنل مدیریت"` (Panel-e Modiriat)
   - `"users_title": "کاربران سیستم"` (Karbaraan-e System)
   - `"forbidden_title": "دسترسی ممنوع"` (Dastresi Mamnu)
   - `"col_username": "نام کاربری"` (Naam-e Karbari)
   - `"search_placeholder": "جستجو..."` (Jostoju...)
   - `"confirm_delete_profile": "پروفایل {{name}} حذف شود؟ تمامی خوانش‌های مرتبط نیز حذف خواهند شد. این عمل غیرقابل بازگشت است."`
   - All strings must be valid UTF-8

**STOP Checkpoint:**

- [ ] `/admin/users` route renders UserTable inside Admin shell
- [ ] `/admin/profiles` route renders ProfileTable inside Admin shell
- [ ] Non-admin users see 403 page at `/admin/*`
- [ ] Admin nav link only visible for admin role in sidebar
- [ ] All text uses i18n keys (no hardcoded strings in components)
- [ ] EN and FA locale files have matching admin key counts
- [ ] Verify: `cd frontend && npx tsc --noEmit && echo "OK"`

---

### Phase 7: Frontend Tests and Final Verification (~45 min)

**Tasks:**

1. **`frontend/src/components/admin/__tests__/UserTable.test.tsx`** (5 tests):
   - Renders all column headers with i18n keys
   - Renders user rows with correct data in correct columns
   - Search input triggers `onSearch` callback
   - Clicking sort header calls `onSort` with field name
   - Shows "No users found" when users array is empty

2. **`frontend/src/components/admin/__tests__/UserActions.test.tsx`** (4 tests):
   - Renders Edit Role, Reset Password, and Deactivate buttons
   - Edit Role click opens role selection dialog
   - Buttons disabled when `user.id === currentUserId`
   - Reset password success shows temporary password text

3. **`frontend/src/components/admin/__tests__/ProfileTable.test.tsx`** (3 tests):
   - Renders profile name, birthday, and reading count
   - Soft-deleted profiles show "Deleted" badge
   - Shows "No profiles found" when empty

4. **`frontend/src/components/admin/__tests__/AdminGuard.test.tsx`** (3 tests):
   - Renders `<Outlet />` children when `nps_user_role` is `"admin"` in localStorage
   - Renders 403 page when role is `"user"`
   - Renders 403 page when no role is set in localStorage

5. **`frontend/src/pages/__tests__/Admin.test.tsx`** (2 tests):
   - Renders tab navigation with "Users" and "Profiles" links
   - Default route `/admin` redirects to `/admin/users`

6. All tests use `vi.mock('react-i18next')` pattern from existing test files, `renderWithProviders` from `frontend/src/test/testUtils.tsx`, and `vi.fn()` for callbacks.

7. Run full verification:

   ```bash
   # API tests
   cd api && python3 -m pytest tests/test_admin.py -v --tb=short

   # Frontend tests
   cd frontend && npx vitest run --reporter=verbose

   # TypeScript check
   cd frontend && npx tsc --noEmit

   # Lint
   cd api && python3 -m ruff check app/routers/admin.py app/models/admin.py app/services/admin_service.py
   cd frontend && npx eslint src/pages/Admin.tsx src/pages/AdminUsers.tsx src/pages/AdminProfiles.tsx src/components/admin/
   ```

**STOP Checkpoint:**

- [ ] All 23 API tests pass
- [ ] All 17 frontend tests pass
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Verify:
  ```bash
  cd api && python3 -m pytest tests/test_admin.py -v --tb=short && echo "API OK"
  cd frontend && npx vitest run --reporter=verbose && echo "FRONTEND OK"
  cd frontend && npx tsc --noEmit && echo "TYPES OK"
  ```

---

## TESTS TO WRITE

### API Tests (`api/tests/test_admin.py`)

| #   | Test Name                                      | What It Verifies                                                                  |
| --- | ---------------------------------------------- | --------------------------------------------------------------------------------- |
| 1   | `test_list_users_as_admin`                     | Admin can list all system users; response has `users`, `total`, `limit`, `offset` |
| 2   | `test_list_users_as_regular_user_forbidden`    | Non-admin user gets HTTP 403 on `GET /api/admin/users`                            |
| 3   | `test_list_users_unauthenticated`              | No token gets HTTP 401 on `GET /api/admin/users`                                  |
| 4   | `test_list_users_search_filter`                | `?search=admin` returns only users with "admin" in username                       |
| 5   | `test_list_users_pagination`                   | `?limit=1&offset=1` returns second user; `total` reflects full count              |
| 6   | `test_list_users_sort_by_username_asc`         | `?sort_by=username&sort_order=asc` returns alphabetically sorted                  |
| 7   | `test_list_users_sort_by_created_at_desc`      | Default sort returns newest first                                                 |
| 8   | `test_get_user_detail`                         | Admin can get single user by ID with `reading_count` field                        |
| 9   | `test_get_user_not_found`                      | `GET /api/admin/users/nonexistent-uuid` returns 404                               |
| 10  | `test_update_role_success`                     | Admin changes another user from `user` to `readonly`; persists in DB              |
| 11  | `test_update_role_invalid_value`               | Role value `"superadmin"` returns 422 validation error                            |
| 12  | `test_update_role_self_forbidden`              | Admin cannot change own role; returns 400                                         |
| 13  | `test_reset_password_success`                  | Returns `temporary_password` string; old password no longer works                 |
| 14  | `test_reset_password_new_temp_works`           | Temp password from reset can be used to log in                                    |
| 15  | `test_reset_password_user_not_found`           | Reset for nonexistent user returns 404                                            |
| 16  | `test_update_status_deactivate`                | Admin can set `is_active=false`; user `is_active` is False in DB                  |
| 17  | `test_update_status_activate`                  | Admin can set `is_active=true` for inactive user                                  |
| 18  | `test_update_status_self_deactivate_forbidden` | Admin cannot deactivate themselves; returns 400                                   |
| 19  | `test_get_stats`                               | Stats endpoint returns `total_users`, `active_users`, `users_by_role`, etc.       |
| 20  | `test_list_profiles_as_admin`                  | Admin can list all Oracle profiles with `reading_count`                           |
| 21  | `test_list_profiles_include_deleted`           | `?include_deleted=true` includes soft-deleted profiles                            |
| 22  | `test_list_profiles_search_by_name`            | `?search=Test` filters profiles by name                                           |
| 23  | `test_delete_profile_success`                  | Admin hard-deletes an Oracle profile; profile no longer in DB                     |
| 24  | `test_delete_profile_not_found`                | `DELETE /api/admin/profiles/999999` returns 404                                   |
| 25  | `test_audit_log_role_change`                   | Role change creates audit entry with action `admin.role_changed`                  |
| 26  | `test_audit_log_password_reset`                | Password reset creates audit entry with action `admin.password_reset`             |

### Frontend Tests

| #   | Test Name                      | File                    | What It Verifies                                  |
| --- | ------------------------------ | ----------------------- | ------------------------------------------------- |
| 27  | `renders all column headers`   | `UserTable.test.tsx`    | Headers for username, role, created, etc. present |
| 28  | `renders user rows with data`  | `UserTable.test.tsx`    | Username, role badge, status badge displayed      |
| 29  | `search triggers onSearch`     | `UserTable.test.tsx`    | Typing in search fires callback                   |
| 30  | `sort toggles direction`       | `UserTable.test.tsx`    | Clicking header calls onSort                      |
| 31  | `shows empty state`            | `UserTable.test.tsx`    | "No users found" when array empty                 |
| 32  | `renders action buttons`       | `UserActions.test.tsx`  | Edit Role, Reset Password, Deactivate visible     |
| 33  | `role change shows dialog`     | `UserActions.test.tsx`  | Clicking Edit Role shows confirmation             |
| 34  | `self-actions disabled`        | `UserActions.test.tsx`  | Buttons disabled for current user                 |
| 35  | `shows temp password`          | `UserActions.test.tsx`  | After reset, password displayed                   |
| 36  | `renders profile data`         | `ProfileTable.test.tsx` | Name, birthday, reading count displayed           |
| 37  | `shows deleted badge`          | `ProfileTable.test.tsx` | Soft-deleted profiles have "Deleted" badge        |
| 38  | `shows empty profiles`         | `ProfileTable.test.tsx` | "No profiles found" when array empty              |
| 39  | `admin guard allows admin`     | `AdminGuard.test.tsx`   | Children rendered when role is admin              |
| 40  | `admin guard blocks non-admin` | `AdminGuard.test.tsx`   | 403 page rendered when role is user               |
| 41  | `admin guard blocks no role`   | `AdminGuard.test.tsx`   | 403 page rendered when no role in localStorage    |
| 42  | `admin page renders tabs`      | `Admin.test.tsx`        | Users and Profiles tab links visible              |
| 43  | `admin default redirects`      | `Admin.test.tsx`        | `/admin` redirects to `/admin/users`              |

---

## ACCEPTANCE CRITERIA

| #   | Criterion                                                             | Verification                                                                                                  |
| --- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 1   | Admin can list all system users via `GET /api/admin/users`            | `curl -H "Authorization: Bearer $ADMIN_TOKEN" localhost:8000/api/admin/users` returns JSON with `users` array |
| 2   | User list supports search, sort, and pagination                       | `?search=admin&sort_by=username&sort_order=asc&limit=10&offset=0` returns filtered, sorted results            |
| 3   | User detail includes `reading_count`                                  | `GET /api/admin/users/{id}` response has `reading_count` integer field                                        |
| 4   | Admin can change another user's role                                  | `PATCH /api/admin/users/{id}/role` with `{"role": "readonly"}` persists new role                              |
| 5   | Admin can reset a user's password                                     | `POST /api/admin/users/{id}/reset-password` returns `temporary_password`; old password stops working          |
| 6   | Admin can deactivate/reactivate users                                 | `PATCH /api/admin/users/{id}/status` with `{"is_active": false}` sets flag; deactivated user cannot log in    |
| 7   | Admin cannot modify own role or deactivate self                       | Self-targeted role change and deactivation return HTTP 400                                                    |
| 8   | Non-admin users get HTTP 403 on all `/api/admin/*` endpoints          | Regular user JWT receives 403 with "Insufficient scope"                                                       |
| 9   | Unauthenticated requests get HTTP 401                                 | No Authorization header receives 401                                                                          |
| 10  | Admin stats endpoint returns correct aggregates                       | `GET /api/admin/stats` has `total_users`, `active_users`, `users_by_role`, `total_readings`, `readings_today` |
| 11  | Admin can list all Oracle profiles with reading counts                | `GET /api/admin/profiles` returns profiles with `reading_count`                                               |
| 12  | Admin can hard-delete Oracle profiles                                 | `DELETE /api/admin/profiles/{id}` removes profile from database                                               |
| 13  | Frontend `/admin/users` renders sortable, searchable user table       | Table shows columns, sort arrows, search input, pagination                                                    |
| 14  | Frontend `/admin/profiles` renders sortable, searchable profile table | Table shows profile data with search and pagination                                                           |
| 15  | Non-admin frontend users see 403 page at `/admin/*`                   | AdminGuard renders "Access Denied" with i18n text                                                             |
| 16  | Admin nav link only visible for admin users in sidebar                | Layout sidebar shows "Admin" link only when `nps_user_role` is `"admin"`                                      |
| 17  | All admin UI text supports EN and FA with RTL                         | Switching locale renders Persian text with `dir="rtl"`                                                        |
| 18  | All admin actions create audit log entries                            | `oracle_audit_log` table has entries for role changes, password resets, status changes, profile deletions     |
| 19  | All API tests pass                                                    | `cd api && python3 -m pytest tests/test_admin.py -v` exits 0                                                  |
| 20  | All frontend tests pass                                               | `cd frontend && npx vitest run` exits 0                                                                       |
| 21  | No TypeScript errors                                                  | `cd frontend && npx tsc --noEmit` exits 0                                                                     |

---

## ERROR SCENARIOS

| #   | Scenario                                          | Problem                                                  | Expected Behavior / Fix                                                          |
| --- | ------------------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 1   | Non-admin user accesses `GET /api/admin/users`    | `require_scope("admin")` rejects the request             | HTTP 403 `{"detail": "Insufficient scope: requires 'admin'"}`                    |
| 2   | Admin tries to change their own role              | `AdminService.update_role()` detects self-modification   | HTTP 400 `{"detail": "Cannot modify your own role"}`                             |
| 3   | Admin tries to deactivate themselves              | `AdminService.update_status()` detects self-modification | HTTP 400 `{"detail": "Cannot deactivate your own account"}`                      |
| 4   | Admin sets invalid role value like `"superadmin"` | Pydantic `Field(pattern=...)` rejects at validation      | HTTP 422 with validation error detail                                            |
| 5   | Admin tries to delete nonexistent Oracle profile  | `AdminService.delete_oracle_profile()` returns None      | HTTP 404 `{"detail": "Profile not found"}`                                       |
| 6   | Admin resets password for nonexistent user        | `AdminService.reset_password()` returns None             | HTTP 404 `{"detail": "User not found"}`                                          |
| 7   | Frontend sends admin request without valid token  | Auth middleware rejects before reaching admin router     | HTTP 401 `{"detail": "Not authenticated"}`                                       |
| 8   | Frontend `localStorage` has no `nps_user_role`    | `AdminGuard` treats missing role as non-admin            | 403 page rendered with "Access Denied" text                                      |
| 9   | Database connection fails during admin operation  | SQLAlchemy raises `OperationalError`                     | HTTP 500 logged by FastAPI; frontend shows error toast via React Query `onError` |
| 10  | Two admins change same user's role simultaneously | Last write wins (SQLAlchemy default behavior)            | No crash; both audit log entries preserved; latest role persists                 |
| 11  | Admin token expired while on admin page           | API returns 401; frontend `request()` helper throws      | React Query retries fail; user sees error and must re-authenticate               |

---

## HANDOFF

### Created:

- `api/app/models/admin.py` -- 9 Pydantic models for admin request/response
- `api/app/services/admin_service.py` -- Admin business logic service with 8 methods
- `api/app/routers/admin.py` -- Admin API router with 8 endpoints (all admin-scoped)
- `api/tests/test_admin.py` -- 26 API tests
- `frontend/src/pages/Admin.tsx` -- Admin shell page with stats cards and tab navigation
- `frontend/src/pages/AdminUsers.tsx` -- User management page (state + UserTable composition)
- `frontend/src/pages/AdminProfiles.tsx` -- Profile management page (state + ProfileTable composition)
- `frontend/src/components/admin/UserTable.tsx` -- Sortable, searchable, paginated user table
- `frontend/src/components/admin/UserActions.tsx` -- User action buttons with confirmation dialogs
- `frontend/src/components/admin/ProfileTable.tsx` -- Sortable, searchable, paginated profile table
- `frontend/src/components/admin/ProfileActions.tsx` -- Profile delete action with cascade warning
- `frontend/src/components/admin/AdminGuard.tsx` -- Admin route guard (403 for non-admin)
- `frontend/src/hooks/useAdmin.ts` -- 8 React Query hooks for admin API calls
- `frontend/src/components/admin/__tests__/UserTable.test.tsx` -- 5 component tests
- `frontend/src/components/admin/__tests__/UserActions.test.tsx` -- 4 component tests
- `frontend/src/components/admin/__tests__/ProfileTable.test.tsx` -- 3 component tests
- `frontend/src/components/admin/__tests__/AdminGuard.test.tsx` -- 3 component tests
- `frontend/src/pages/__tests__/Admin.test.tsx` -- 2 page tests

### Modified:

- `api/app/main.py` -- Registered admin router at `/api/admin` with `tags=["admin"]`
- `api/app/services/audit.py` -- Added 4 admin-specific audit methods (`log_admin_role_changed`, `log_admin_password_reset`, `log_admin_status_changed`, `log_admin_profile_deleted`)
- `frontend/src/App.tsx` -- Added `/admin/*` routes with `AdminGuard` wrapper and nested `Admin`/`AdminUsers`/`AdminProfiles`
- `frontend/src/components/Layout.tsx` -- Conditional "Admin" nav link in sidebar (visible only for admin role)
- `frontend/src/services/api.ts` -- Added `admin` namespace with 8 typed fetch methods
- `frontend/src/types/index.ts` -- Added 8 admin TypeScript interfaces + 3 sort type aliases
- `frontend/src/locales/en.json` -- Added `nav.admin` and ~45 `admin.*` i18n keys
- `frontend/src/locales/fa.json` -- Added `nav.admin` and ~45 `admin.*` i18n keys (Persian)

### Deleted:

- None

### Next session needs:

**Session 39 (Monitoring Dashboard & System Health)** depends on:

- Admin router infrastructure: `api/app/routers/admin.py` exists and is registered at `/api/admin` -- Session 39 can add monitoring endpoints to the same router or create a new `api/app/routers/monitoring.py`
- `require_scope("admin")` pattern is established -- Session 39 reuses the same dependency for monitoring endpoints
- `AdminGuard` component is available -- Session 39 adds a "Monitoring" tab to the existing admin page shell (`Admin.tsx`)
- Tab navigation pattern is established -- Session 39 adds `/admin/monitoring` route with same `NavLink` pattern
- `AuditService` has admin logging methods -- Session 39 can query audit logs for system activity display
- Frontend patterns (sortable tables, paginated lists, stats cards) are all available for reuse
- `useAdmin.ts` hooks demonstrate the React Query pattern for admin data

**Session 39 will build:**

- System health monitoring dashboard (`/admin/monitoring`) showing API uptime, database connection status, Redis status, gRPC channel status
- Prometheus metrics endpoint at `/api/metrics` for external scraping
- Real-time system status updates via existing WebSocket infrastructure
- Log viewer showing recent application log entries
- Alert configuration UI for Telegram notification thresholds

**Session 40 (Backup & Recovery) will need:**

- Admin auth patterns from Session 38
- Monitoring endpoints from Session 39
- Database backup/restore API endpoints
- Scheduled backup configuration UI in admin panel
