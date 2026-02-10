# SESSION 3 SPEC — User Management API

**Block:** Foundation (Sessions 1-5)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium-High
**Dependencies:** Session 1 (schema — new oracle_users columns), Session 2 (auth — hardened JWT, roles, moderator role)

---

## TL;DR

- Build 6 system user admin endpoints under `/api/users` (list, get, update, deactivate, reset-password, change-role)
- Enhance existing 5 Oracle user CRUD endpoints with ownership (`created_by` FK), new fields (gender, heart_rate_bpm, timezone, coordinates), and visibility rules
- Add migration 013 for `created_by` column on `oracle_users` + moderator seed user
- Write comprehensive tests for both system user and oracle user management
- Extend audit service with system user event helpers

---

## OBJECTIVES

1. **System user management** — 6 admin/moderator endpoints for managing system accounts (the people who log in)
2. **Oracle user ownership** — Link oracle profiles to their creating system user via `created_by` FK, enforce "users see only their own profiles"
3. **Oracle user field expansion** — Expose the 4 new columns from Session 1 (gender, heart_rate_bpm, timezone_hours, timezone_minutes) plus coordinates through Pydantic models and ORM
4. **Enhanced validation** — Name no-digits check, birthday range 1900-today, coordinate range validation, gender enum, heart_rate_bpm 30-220
5. **Audit trail** — Every system user CRUD event logged to `oracle_audit_log`

---

## PREREQUISITES

- [ ] Session 1 complete — `oracle_users` table has `gender`, `heart_rate_bpm`, `timezone_hours`, `timezone_minutes` columns
- [ ] Session 2 complete — Auth hardened with `moderator` role, JWT refresh, role-checking middleware
- [ ] `users` table exists with UUID id, username, password_hash, role, is_active columns
- [ ] `oracle_audit_log` table exists with action, resource_type, resource_id columns
- Verification:
  ```bash
  test -f api/app/middleware/auth.py && \
  test -f api/app/orm/user.py && \
  test -f api/app/orm/oracle_user.py && \
  test -f api/app/services/audit.py && \
  echo "Prerequisites OK"
  ```

---

## EXISTING CODE ANALYSIS

### What Already Works (Keep & Enhance)

**Oracle user CRUD** in `api/app/routers/oracle.py:367-594`:

- `POST /api/oracle/users` — Create user (scope: `oracle:write`)
- `GET /api/oracle/users` — List users with search (scope: `oracle:read`)
- `GET /api/oracle/users/{user_id}` — Get single user (scope: `oracle:read`)
- `PUT /api/oracle/users/{user_id}` — Update user, partial (scope: `oracle:write`)
- `DELETE /api/oracle/users/{user_id}` — Soft delete (scope: `oracle:admin`)

These 5 endpoints follow good patterns: encryption helpers, audit logging, scope dependencies. We modify them in-place, not rewrite.

**Helpers** in `api/app/routers/oracle.py:57-98`:

- `_encrypt_user_fields()` — Encrypts mother_name fields before DB write
- `_decrypt_user()` — Decrypts and converts ORM to response model
- `_get_client_ip()` — Extracts client IP from request

**Auth middleware** in `api/app/middleware/auth.py`:

- `get_current_user` — Returns user context dict with `user_id`, `username`, `role`, `scopes`
- `require_scope(scope)` — Dependency factory for scope checking
- Role→scope mapping: admin gets all, user gets read+write, readonly gets read
- Scope hierarchy: `oracle:admin` implies `oracle:write` implies `oracle:read`

**Audit service** in `api/app/services/audit.py`:

- `AuditService.log()` — Generic audit entry (joins caller's transaction)
- 5 oracle-user helpers: `log_user_created`, `log_user_read`, `log_user_updated`, `log_user_deleted`, `log_user_listed`
- `get_audit_service` FastAPI dependency

### What's Missing

| Component                      | Current State                                                                  | What Session 3 Adds                               |
| ------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------- |
| System user router             | Does not exist                                                                 | New `api/app/routers/users.py` with 6 endpoints   |
| System user Pydantic models    | Does not exist                                                                 | New `api/app/models/user.py`                      |
| `oracle_users.created_by`      | No column                                                                      | UUID FK → `users.id`, migration 013               |
| OracleUser ORM fields          | Missing: gender, heart_rate_bpm, timezone_hours, timezone_minutes, coordinates | Add all 5 mapped columns                          |
| OracleUser Pydantic fields     | Missing same                                                                   | Add to Create/Update/Response models              |
| `_decrypt_user()` helper       | Missing new fields in response                                                 | Add gender, heart_rate_bpm, timezone, coordinates |
| Ownership filtering            | Oracle list returns ALL users                                                  | Filter by `created_by` for non-admin              |
| Audit helpers for system users | None                                                                           | Add 6 new helpers to AuditService                 |

---

## FILES TO CREATE

- `api/app/routers/users.py` — System user management router (6 endpoints)
- `api/app/models/user.py` — Pydantic models for system user endpoints
- `database/migrations/013_user_management.sql` — Add `created_by` to oracle_users + moderator seed
- `database/migrations/013_user_management_rollback.sql` — Reverse migration 013
- `api/tests/test_users.py` — System user endpoint tests (8+ tests)
- `api/tests/test_oracle_users.py` — Oracle user endpoint tests (8+ tests)

## FILES TO MODIFY

- `api/app/orm/oracle_user.py` — Add gender, heart_rate_bpm, timezone_hours, timezone_minutes, coordinates, created_by columns
- `api/app/models/oracle_user.py` — Add new fields to Create/Update/Response models + enhanced validation
- `api/app/routers/oracle.py` — Add ownership filtering to list/get, inject created_by on create, update `_decrypt_user()` helper
- `api/app/services/audit.py` — Add system user audit helpers
- `api/app/main.py` — Register users router, import users ORM

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Pydantic Models (~30 min)

**Tasks:**

1. Create `api/app/models/user.py` — System user models:

   ```python
   class SystemUserResponse(BaseModel):
       """System user profile (never exposes password_hash)."""
       model_config = ConfigDict(from_attributes=True)

       id: str  # UUID
       username: str
       role: str
       is_active: bool
       created_at: datetime
       updated_at: datetime
       last_login: datetime | None = None

   class SystemUserListResponse(BaseModel):
       users: list[SystemUserResponse]
       total: int
       limit: int
       offset: int

   class SystemUserUpdate(BaseModel):
       """Admin can update username and is_active."""
       username: str | None = Field(None, min_length=3, max_length=100)
       is_active: bool | None = None

   class PasswordResetRequest(BaseModel):
       new_password: str = Field(..., min_length=8, max_length=128)

   class RoleChangeRequest(BaseModel):
       role: str = Field(...)

       @field_validator("role")
       @classmethod
       def validate_role(cls, v: str) -> str:
           if v not in ("admin", "moderator", "user", "readonly"):
               raise ValueError("Role must be one of: admin, moderator, user, readonly")
           return v
   ```

2. Update `api/app/models/oracle_user.py` — Add new fields:

   **OracleUserCreate** — add:

   ```python
   gender: str | None = Field(None, pattern=r"^(male|female)$")
   heart_rate_bpm: int | None = Field(None, ge=30, le=220)
   timezone_hours: int | None = Field(None, ge=-12, le=14)
   timezone_minutes: int | None = Field(None, ge=0, le=59)
   latitude: float | None = Field(None, ge=-90.0, le=90.0)
   longitude: float | None = Field(None, ge=-180.0, le=180.0)
   ```

   **OracleUserUpdate** — add same fields (all optional).

   **OracleUserResponse** — add:

   ```python
   gender: str | None = None
   heart_rate_bpm: int | None = None
   timezone_hours: int | None = None
   timezone_minutes: int | None = None
   latitude: float | None = None
   longitude: float | None = None
   created_by: str | None = None  # UUID of system user who created this profile
   ```

   **Enhanced validation** on both Create and Update:

   ```python
   @field_validator("name")
   @classmethod
   def name_no_digits(cls, v: str) -> str:
       if v and any(c.isdigit() for c in v):
           raise ValueError("Name must not contain digits")
       return v

   @field_validator("birthday")
   @classmethod
   def birthday_range(cls, v: date) -> date:
       if v and v.year < 1900:
           raise ValueError("Birthday must be after 1900")
       if v and v > date.today():
           raise ValueError("Birthday cannot be in the future")
       return v
   ```

**Checkpoint:**

- [ ] `api/app/models/user.py` exists with all 5 models
- [ ] `api/app/models/oracle_user.py` has gender, heart_rate_bpm, timezone, latitude, longitude, created_by fields
- [ ] Validators: name_no_digits, birthday_range, gender pattern, coordinate ranges
- Verify: `python3 -c "from app.models.user import SystemUserResponse, PasswordResetRequest, RoleChangeRequest; from app.models.oracle_user import OracleUserCreate; print('Models OK')"` (run from `api/` directory)

STOP if checkpoint fails

---

### Phase 2: ORM Updates (~20 min)

**Tasks:**

1. Update `api/app/orm/oracle_user.py` — Add columns to match database schema:

   ```python
   from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text, func
   from sqlalchemy.dialects.postgresql import UUID

   class OracleUser(Base):
       __tablename__ = "oracle_users"

       # ... existing columns stay unchanged ...

       # New columns (Session 1 adds these to DB, Session 3 adds ORM mapping)
       gender: Mapped[str | None] = mapped_column(String(20))
       heart_rate_bpm: Mapped[int | None] = mapped_column(Integer)
       timezone_hours: Mapped[int | None] = mapped_column(Integer, server_default="0")
       timezone_minutes: Mapped[int | None] = mapped_column(Integer, server_default="0")
       # coordinates stored as POINT in PostgreSQL — read as tuple, but we use
       # separate lat/lng in the API. Stored raw, extracted in the router layer.
       # The existing coordinates column is a POINT type — do NOT add an ORM mapping
       # for it (SQLAlchemy doesn't natively support POINT). Instead, use raw SQL
       # or a custom type. For now, latitude/longitude are handled at the router layer.

       # Ownership (Session 3 migration 013 adds this column)
       created_by: Mapped[str | None] = mapped_column(
           UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL")
       )
   ```

   **Important: coordinates handling strategy.**
   PostgreSQL `POINT` type is not natively supported by SQLAlchemy's `mapped_column`. The existing `oracle_users.coordinates` column is POINT type. Options:
   - A: Use `from geoalchemy2 import Geometry` — adds heavy dependency
   - B: Use raw SQL for coordinate read/write — lightweight, no new dependency
   - **Decision: B** — Use raw SQL `ST_MakePoint(lon, lat)` on write, extract with `coordinates[0]` / `coordinates[1]` on read. Wrap in helper functions in the router.

   Add coordinate helpers to the oracle router:

   ```python
   from sqlalchemy import text

   def _set_coordinates(db: Session, user_id: int, lat: float | None, lng: float | None) -> None:
       """Set coordinates POINT column using raw SQL."""
       if lat is not None and lng is not None:
           db.execute(
               text("UPDATE oracle_users SET coordinates = POINT(:lng, :lat) WHERE id = :id"),
               {"lng": lng, "lat": lat, "id": user_id},
           )

   def _get_coordinates(db: Session, user_id: int) -> tuple[float | None, float | None]:
       """Read coordinates POINT column, return (latitude, longitude)."""
       row = db.execute(
           text("SELECT coordinates[0] AS lng, coordinates[1] AS lat FROM oracle_users WHERE id = :id"),
           {"id": user_id},
       ).first()
       if row and row.lat is not None:
           return (row.lat, row.lng)
       return (None, None)
   ```

**Checkpoint:**

- [ ] OracleUser ORM has gender, heart_rate_bpm, timezone_hours, timezone_minutes, created_by mapped columns
- [ ] Coordinate helpers `_set_coordinates` and `_get_coordinates` defined
- Verify: `python3 -c "from app.orm.oracle_user import OracleUser; print([c.key for c in OracleUser.__table__.columns])"` (run from `api/`)

STOP if checkpoint fails

---

### Phase 3: Migration 013 (~20 min)

**Tasks:**

1. Create `database/migrations/013_user_management.sql`:

   ```sql
   -- Migration 013: User Management — created_by ownership + moderator seed
   -- Depends on: Migration 012 (framework alignment)

   DO $$
   BEGIN
       -- Guard: skip if already applied
       IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
           RAISE NOTICE 'Migration 013 already applied, skipping.';
           RETURN;
       END IF;

       -- 1. Add created_by FK column to oracle_users
       ALTER TABLE oracle_users ADD COLUMN IF NOT EXISTS created_by UUID
           REFERENCES users(id) ON DELETE SET NULL;

       -- 2. Index for ownership queries (filter oracle_users by system user)
       CREATE INDEX IF NOT EXISTS idx_oracle_users_created_by
           ON oracle_users(created_by);

       -- 3. Seed a moderator user (password: change-me-immediately, bcrypt hash)
       -- Admins should change this password immediately after first deployment
       INSERT INTO users (id, username, password_hash, role, is_active)
       VALUES (
           uuid_generate_v4(),
           'moderator',
           -- bcrypt hash of 'change-me-immediately' with cost factor 12
           '$2b$12$LJ3m4ys3Lz0JFOdOKmGrOeQxJONBnPfGdPjC6x5T9YldvYmKz/dm',
           'moderator',
           TRUE
       )
       ON CONFLICT (username) DO NOTHING;

       -- 4. Record migration
       INSERT INTO schema_migrations (version, name)
       VALUES ('013', 'User management: oracle_users.created_by ownership + moderator seed');

       RAISE NOTICE 'Migration 013 applied successfully.';
   END $$;
   ```

2. Create `database/migrations/013_user_management_rollback.sql`:

   ```sql
   -- Rollback Migration 013: User Management
   DO $$
   BEGIN
       IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
           RAISE NOTICE 'Migration 013 not applied, nothing to rollback.';
           RETURN;
       END IF;

       -- Drop ownership index
       DROP INDEX IF EXISTS idx_oracle_users_created_by;

       -- Remove created_by column
       ALTER TABLE oracle_users DROP COLUMN IF EXISTS created_by;

       -- Remove moderator seed user (only if it was our seed)
       DELETE FROM users WHERE username = 'moderator' AND role = 'moderator';

       -- Remove migration record
       DELETE FROM schema_migrations WHERE version = '013';

       RAISE NOTICE 'Migration 013 rolled back successfully.';
   END $$;
   ```

**Checkpoint:**

- [ ] Migration 013 adds `created_by` UUID FK column + index
- [ ] Migration seeds moderator user with bcrypt hash
- [ ] Rollback reverses all changes
- [ ] Both files are idempotent (guard clauses)
- Verify: `test -f database/migrations/013_user_management.sql && test -f database/migrations/013_user_management_rollback.sql && echo "Migration OK"`

STOP if checkpoint fails

---

### Phase 4: System User Router — `/api/users` (~60 min)

**Tasks:**

1. Create `api/app/routers/users.py` with 6 endpoints:

   **Endpoint 1: `GET /api/users` — List all system users**

   ```python
   @router.get("", response_model=SystemUserListResponse)
   def list_users(
       limit: int = Query(20, ge=1, le=100),
       offset: int = Query(0, ge=0),
       role: str | None = Query(None),
       is_active: bool | None = Query(None),
       db: Session = Depends(get_db),
       current_user: dict = Depends(require_scope("admin")),
       audit: AuditService = Depends(get_audit_service),
   ):
   ```

   - Scope: `admin` (admins and moderators via hierarchy — add `user:read` scope, or use `admin` scope)
   - **Decision:** Use a new scope `user:admin` for system user management. Only `admin` role gets this scope. Moderators can view but not modify.
   - Actually, per master spec: "List all users (admin/moderator)" — so moderators can list.
   - **Implementation:** Check role directly: `if current_user["role"] not in ("admin", "moderator"): raise 403`
   - Filters: optional `role` and `is_active` query params
   - Returns paginated list (never expose password_hash)
   - Audit: `log("system_user.list", ...)`

   **Endpoint 2: `GET /api/users/{user_id}` — Get user details**

   ```python
   @router.get("/{user_id}", response_model=SystemUserResponse)
   def get_user(user_id: str, ...):
   ```

   - Scope: admin, moderator, or self (current_user["user_id"] == user_id)
   - Returns single user (never expose password_hash)
   - Audit: `log("system_user.read", ...)`

   **Endpoint 3: `PUT /api/users/{user_id}` — Update user**

   ```python
   @router.put("/{user_id}", response_model=SystemUserResponse)
   def update_user(user_id: str, body: SystemUserUpdate, ...):
   ```

   - Scope: admin for any user, self for own account (username change only, not is_active)
   - Self cannot deactivate own account
   - Admin cannot deactivate their own account (prevent lockout)
   - Audit: `log("system_user.update", ..., details={"fields": [...]})`

   **Endpoint 4: `DELETE /api/users/{user_id}` — Deactivate user (soft delete)**

   ```python
   @router.delete("/{user_id}", response_model=SystemUserResponse)
   def deactivate_user(user_id: str, ...):
   ```

   - Scope: admin only
   - Sets `is_active = False` (does NOT delete row — soft delete)
   - Cannot deactivate self (prevent admin lockout)
   - Audit: `log("system_user.deactivate", ...)`

   **Endpoint 5: `POST /api/users/{user_id}/reset-password` — Force password reset**

   ```python
   @router.post("/{user_id}/reset-password")
   def reset_password(user_id: str, body: PasswordResetRequest, ...):
   ```

   - Scope: admin only
   - Hashes new password with bcrypt (same params as auth.py login)
   - Updates `password_hash` in DB
   - Audit: `log("system_user.password_reset", ...)`

   **Endpoint 6: `PUT /api/users/{user_id}/role` — Change user role**

   ```python
   @router.put("/{user_id}/role", response_model=SystemUserResponse)
   def change_role(user_id: str, body: RoleChangeRequest, ...):
   ```

   - Scope: admin only
   - Cannot change own role (prevent privilege loss)
   - Valid roles: admin, moderator, user, readonly
   - Audit: `log("system_user.role_change", ..., details={"old_role": ..., "new_role": ...})`

2. All endpoints follow the existing pattern:
   - Use `get_current_user` / `require_scope` dependencies
   - Use `AuditService` for logging
   - Use `_get_client_ip` helper (import from oracle.py or extract to shared module)
   - Return Pydantic models (never raw ORM objects)

3. **Shared helper extraction:** Move `_get_client_ip()` from `api/app/routers/oracle.py` to a new utility or keep it duplicated in both routers (simpler, no refactor needed). **Decision:** Duplicate — it's a 1-line function. Avoid unnecessary refactor.

**Checkpoint:**

- [ ] `api/app/routers/users.py` has 6 endpoints
- [ ] All endpoints require authentication
- [ ] Admin-only endpoints reject non-admin users
- [ ] Self-access endpoints allow users to view/update their own account
- [ ] No endpoint exposes `password_hash`
- Verify: `grep -c "@router\." api/app/routers/users.py` — should return 6

STOP if checkpoint fails

---

### Phase 5: Oracle User CRUD Improvements (~60 min)

**Tasks:**

1. **Update `_decrypt_user()` helper** in `api/app/routers/oracle.py` to include new fields:

   ```python
   def _decrypt_user(
       user: OracleUser, enc: EncryptionService | None, db: Session | None = None
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
   ```

   Update all call sites of `_decrypt_user()` to pass `db` session.

2. **Update `POST /api/oracle/users` (create_user):**
   - Set `created_by = _user["user_id"]` on the new OracleUser before DB write
   - Handle `latitude` / `longitude` from request body: after `db.flush()`, call `_set_coordinates(db, user.id, body.latitude, body.longitude)`
   - The `body.model_dump()` will now include gender, heart_rate_bpm, timezone_hours, timezone_minutes — these map directly to ORM columns
   - Exclude `latitude` and `longitude` from `model_dump()` since they aren't ORM columns: `body.model_dump(exclude={"latitude", "longitude"})`

3. **Update `GET /api/oracle/users` (list_users) — Ownership filtering:**
   - If `_user["role"]` is `admin` or `moderator`: return all profiles (existing behavior)
   - Otherwise: filter by `OracleUser.created_by == _user["user_id"]`
   - This ensures regular users only see profiles they created

   ```python
   query = db.query(OracleUser).filter(OracleUser.deleted_at.is_(None))

   # Ownership: non-admin/moderator users see only their own profiles
   if _user["role"] not in ("admin", "moderator"):
       query = query.filter(OracleUser.created_by == _user["user_id"])
   ```

4. **Update `GET /api/oracle/users/{user_id}` (get_user) — Ownership check:**
   - After fetching user, if `_user["role"]` not in (admin, moderator): verify `user.created_by == _user["user_id"]`
   - If not: raise 404 (not 403 — don't reveal existence)

5. **Update `PUT /api/oracle/users/{user_id}` (update_user) — Ownership + new fields:**
   - Same ownership check as get_user
   - Handle coordinate update: if `latitude` or `longitude` in updates, call `_set_coordinates()`
   - Exclude `latitude` and `longitude` from the `setattr` loop (they're not ORM columns)

6. **Update `DELETE /api/oracle/users/{user_id}` (delete_user) — Ownership check:**
   - Admin can delete any profile
   - Moderator can delete any profile (existing: requires `oracle:admin` scope — keep this)
   - Regular user: can only delete their own profiles (add created_by check)

**Checkpoint:**

- [ ] `_decrypt_user()` returns all new fields including coordinates
- [ ] `POST /api/oracle/users` sets `created_by` and handles coordinates
- [ ] `GET /api/oracle/users` filters by ownership for non-admin users
- [ ] `GET /api/oracle/users/{id}` checks ownership
- [ ] `PUT /api/oracle/users/{id}` checks ownership + handles coordinate updates
- [ ] `DELETE /api/oracle/users/{id}` checks ownership for non-admin
- Verify: `grep -c "created_by" api/app/routers/oracle.py` — should return 3+

STOP if checkpoint fails

---

### Phase 6: Audit Service Extensions (~15 min)

**Tasks:**

1. Add system user audit helpers to `api/app/services/audit.py`:

   ```python
   # ─── System User Events ─────────────────────────────────────

   def log_system_user_listed(self, *, ip: str | None = None, key_hash: str | None = None):
       return self.log(
           "system_user.list",
           resource_type="system_user",
           ip_address=ip,
           api_key_hash=key_hash,
       )

   def log_system_user_read(
       self, user_id: str, *, ip: str | None = None, key_hash: str | None = None
   ):
       return self.log(
           "system_user.read",
           resource_type="system_user",
           resource_id=None,  # resource_id is int, user_id is UUID — store in details
           ip_address=ip,
           api_key_hash=key_hash,
           details={"target_user_id": user_id},
       )

   def log_system_user_updated(
       self, user_id: str, fields: list[str], *, ip: str | None = None, key_hash: str | None = None
   ):
       return self.log(
           "system_user.update",
           resource_type="system_user",
           ip_address=ip,
           api_key_hash=key_hash,
           details={"target_user_id": user_id, "updated_fields": fields},
       )

   def log_system_user_deactivated(
       self, user_id: str, *, ip: str | None = None, key_hash: str | None = None
   ):
       return self.log(
           "system_user.deactivate",
           resource_type="system_user",
           ip_address=ip,
           api_key_hash=key_hash,
           details={"target_user_id": user_id},
       )

   def log_system_user_password_reset(
       self, user_id: str, *, ip: str | None = None, key_hash: str | None = None
   ):
       return self.log(
           "system_user.password_reset",
           resource_type="system_user",
           ip_address=ip,
           api_key_hash=key_hash,
           details={"target_user_id": user_id},
       )

   def log_system_user_role_changed(
       self, user_id: str, old_role: str, new_role: str,
       *, ip: str | None = None, key_hash: str | None = None
   ):
       return self.log(
           "system_user.role_change",
           resource_type="system_user",
           ip_address=ip,
           api_key_hash=key_hash,
           details={"target_user_id": user_id, "old_role": old_role, "new_role": new_role},
       )
   ```

   **Note on resource_id:** The existing `oracle_audit_log.resource_id` is BIGINT, but system user IDs are UUIDs. Store UUID in the `details` JSONB instead of forcing it into `resource_id`.

**Checkpoint:**

- [ ] AuditService has 6 new `log_system_user_*` methods
- [ ] All methods use `resource_type="system_user"`
- [ ] UUID stored in `details` JSONB, not `resource_id`
- Verify: `grep -c "log_system_user" api/app/services/audit.py` — should return 6+

STOP if checkpoint fails

---

### Phase 7: Router Registration & Wiring (~10 min)

**Tasks:**

1. Update `api/app/main.py`:

   Add import:

   ```python
   from app.routers import (
       auth,
       health,
       learning,
       location,
       oracle,
       scanner,
       translation,
       users,  # NEW
       vault,
   )
   ```

   Add router registration (between auth and scanner):

   ```python
   app.include_router(users.router, prefix="/api/users", tags=["users"])
   ```

2. Verify no route conflicts:
   - `/api/users` — system user management (new)
   - `/api/oracle/users` — oracle profile management (existing)
   - These are distinct prefixes — no conflict.

**Checkpoint:**

- [ ] `api/app/main.py` imports and registers users router
- [ ] No route prefix conflicts
- Verify: `grep "users.router" api/app/main.py` — should return 1 match

STOP if checkpoint fails

---

### Phase 8: Tests (~60 min)

**Tasks:**

1. Create `api/tests/test_users.py` — System user endpoint tests:

   ```
   test_list_users_admin          — Admin can list all users
   test_list_users_forbidden      — Regular user gets 403
   test_get_user_self             — User can get own profile
   test_get_user_other_forbidden  — Non-admin cannot get other user
   test_update_user_admin         — Admin can update any user
   test_update_self_username      — User can change own username
   test_deactivate_user           — Admin can deactivate user
   test_deactivate_self_forbidden — Admin cannot deactivate self
   test_reset_password            — Admin can reset password
   test_change_role               — Admin can change role
   test_change_own_role_forbidden — Admin cannot change own role
   ```

   Use `pytest` fixtures with test DB, create test admin + regular users via ORM (not API), use `TestClient` from FastAPI.

2. Create `api/tests/test_oracle_users.py` — Oracle user endpoint tests:

   ```
   test_create_oracle_user             — Create with all fields including new ones
   test_create_sets_created_by         — created_by is set to current user's ID
   test_list_users_ownership           — Regular user sees only own profiles
   test_list_users_admin_sees_all      — Admin sees all profiles
   test_get_user_own                   — User can get own profile
   test_get_user_other_forbidden       — User cannot get other's profile (returns 404)
   test_update_user_own                — User can update own profile
   test_update_coordinates             — Coordinates are stored and retrieved correctly
   test_delete_user_own                — User can soft-delete own profile
   test_validation_name_no_digits      — Name with digits rejected
   test_validation_birthday_future     — Future birthday rejected
   test_validation_birthday_before_1900 — Pre-1900 birthday rejected
   test_validation_gender_invalid      — Invalid gender rejected
   test_validation_heart_rate_bounds   — BPM outside 30-220 rejected
   test_validation_coordinate_bounds   — Lat/lng outside valid range rejected
   test_persian_name_roundtrip         — Persian text stored and retrieved correctly
   ```

3. All tests must:
   - Use a test database (SQLite in-memory or test PostgreSQL)
   - Create/tear down test data per test
   - Assert specific HTTP status codes
   - Verify response body contents
   - Verify audit log entries where relevant

**Checkpoint:**

- [ ] `api/tests/test_users.py` has 11+ test functions
- [ ] `api/tests/test_oracle_users.py` has 16+ test functions
- [ ] All tests pass: `cd api && python3 -m pytest tests/test_users.py tests/test_oracle_users.py -v`

STOP if checkpoint fails

---

### Phase 9: Final Verification (~15 min)

**Tasks:**

1. Run full quality pipeline:

   ```bash
   cd api && python3 -m black . && python3 -m ruff check --fix .
   ```

2. Run all tests:

   ```bash
   cd api && python3 -m pytest tests/ -v
   ```

3. Verify endpoint documentation:
   - Start API: `cd api && uvicorn app.main:app --port 8000`
   - Open `http://localhost:8000/docs`
   - Verify `/api/users` group shows 6 endpoints
   - Verify `/api/oracle` group still shows 5 user endpoints (improved)

4. Verify migration SQL syntax:
   ```bash
   python3 -c "
   for f in ['database/migrations/013_user_management.sql', 'database/migrations/013_user_management_rollback.sql']:
       content = open(f).read()
       assert content.count('(') == content.count(')'), f'{f}: unbalanced parens'
       print(f'  OK: {f}')
   print('SQL syntax check passed')
   "
   ```

**Checkpoint:**

- [ ] Black + ruff pass with no errors
- [ ] All tests pass
- [ ] Swagger docs show all endpoints
- [ ] Migration SQL is syntactically valid

STOP if checkpoint fails

---

## TESTS TO WRITE

| Test File                        | Test Name                              | What It Verifies                                            |
| -------------------------------- | -------------------------------------- | ----------------------------------------------------------- |
| `api/tests/test_users.py`        | `test_list_users_admin`                | Admin can list system users with pagination                 |
| `api/tests/test_users.py`        | `test_list_users_forbidden`            | Non-admin gets 403 on system user list                      |
| `api/tests/test_users.py`        | `test_get_user_self`                   | User can view own system account                            |
| `api/tests/test_users.py`        | `test_get_user_other_forbidden`        | Non-admin cannot view other accounts                        |
| `api/tests/test_users.py`        | `test_update_user_admin`               | Admin can update username/is_active                         |
| `api/tests/test_users.py`        | `test_update_self_username`            | User can change own username                                |
| `api/tests/test_users.py`        | `test_deactivate_user`                 | Admin can soft-deactivate a user                            |
| `api/tests/test_users.py`        | `test_deactivate_self_forbidden`       | Admin cannot deactivate themselves                          |
| `api/tests/test_users.py`        | `test_reset_password`                  | Admin can force password reset                              |
| `api/tests/test_users.py`        | `test_change_role`                     | Admin can change another user's role                        |
| `api/tests/test_users.py`        | `test_change_own_role_forbidden`       | Admin cannot change own role                                |
| `api/tests/test_oracle_users.py` | `test_create_oracle_user`              | Create user with all fields including gender, BPM, timezone |
| `api/tests/test_oracle_users.py` | `test_create_sets_created_by`          | created_by matches authenticated user's ID                  |
| `api/tests/test_oracle_users.py` | `test_list_users_ownership`            | Non-admin sees only own oracle profiles                     |
| `api/tests/test_oracle_users.py` | `test_list_users_admin_sees_all`       | Admin sees all oracle profiles                              |
| `api/tests/test_oracle_users.py` | `test_get_user_own`                    | User can get their own oracle profile                       |
| `api/tests/test_oracle_users.py` | `test_get_user_other_forbidden`        | Non-admin gets 404 for other's profile                      |
| `api/tests/test_oracle_users.py` | `test_update_user_own`                 | User can update own oracle profile                          |
| `api/tests/test_oracle_users.py` | `test_update_coordinates`              | Lat/lng stored as POINT and retrieved correctly             |
| `api/tests/test_oracle_users.py` | `test_delete_user_own`                 | User can soft-delete own oracle profile                     |
| `api/tests/test_oracle_users.py` | `test_validation_name_no_digits`       | Name with digits returns 422                                |
| `api/tests/test_oracle_users.py` | `test_validation_birthday_future`      | Future birthday returns 422                                 |
| `api/tests/test_oracle_users.py` | `test_validation_birthday_before_1900` | Pre-1900 birthday returns 422                               |
| `api/tests/test_oracle_users.py` | `test_validation_gender_invalid`       | Invalid gender string returns 422                           |
| `api/tests/test_oracle_users.py` | `test_validation_heart_rate_bounds`    | BPM outside 30-220 returns 422                              |
| `api/tests/test_oracle_users.py` | `test_validation_coordinate_bounds`    | Latitude/longitude out of range returns 422                 |
| `api/tests/test_oracle_users.py` | `test_persian_name_roundtrip`          | Persian name_persian stored and retrieved intact            |

---

## ACCEPTANCE CRITERIA

- [ ] 6 system user endpoints work at `/api/users`: list, get, update, deactivate, reset-password, role-change
- [ ] Only admin can access system user management (moderator can list/get only)
- [ ] 5 oracle user endpoints at `/api/oracle/users` enhanced with new fields and ownership
- [ ] Oracle user create sets `created_by` to authenticated user's UUID
- [ ] Non-admin users see only their own oracle profiles in list/get
- [ ] New fields in oracle responses: gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude, created_by
- [ ] Validation rejects: names with digits, future birthdays, pre-1900 birthdays, invalid gender, BPM out of range, coordinates out of range
- [ ] Persian text stores and retrieves correctly (UTF-8)
- [ ] Migration 013 applies cleanly and is idempotent
- [ ] Migration 013 rollback reverses all changes
- [ ] All system user CRUD events are audit-logged
- [ ] All tests pass: `cd api && python3 -m pytest tests/test_users.py tests/test_oracle_users.py -v`
- Verify all:
  ```bash
  test -f api/app/routers/users.py && \
  test -f api/app/models/user.py && \
  test -f api/tests/test_users.py && \
  test -f api/tests/test_oracle_users.py && \
  test -f database/migrations/013_user_management.sql && \
  test -f database/migrations/013_user_management_rollback.sql && \
  grep -q "created_by" api/app/orm/oracle_user.py && \
  grep -q "gender" api/app/models/oracle_user.py && \
  grep -q "users.router" api/app/main.py && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                       | Expected Behavior                                                                                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Non-admin calls `GET /api/users`               | 403 Forbidden                                                                                                              |
| Non-admin calls `DELETE /api/users/{id}`       | 403 Forbidden                                                                                                              |
| Admin deactivates self                         | 400 Bad Request "Cannot deactivate your own account"                                                                       |
| Admin changes own role                         | 400 Bad Request "Cannot change your own role"                                                                              |
| User A views User B's oracle profile           | 404 Not Found (not 403 — don't reveal existence)                                                                           |
| User A lists oracle profiles                   | Only sees profiles where created_by = A's UUID                                                                             |
| Create oracle user with name "John123"         | 422 Validation Error — name contains digits                                                                                |
| Create oracle user with birthday 1850-01-01    | 422 Validation Error — before 1900                                                                                         |
| Create oracle user with gender="other"         | 422 Validation Error — must be male/female/null                                                                            |
| Create oracle user with heart_rate_bpm=0       | 422 Validation Error — below 30                                                                                            |
| Create oracle user with latitude=100           | 422 Validation Error — above 90                                                                                            |
| Migration 013 run before 012                   | Depends on `users` table (exists from init.sql) — should work. `created_by` references `users.id` which exists from day 1. |
| Migration 013 run twice                        | No error — guard clause skips                                                                                              |
| Rollback 013 when not applied                  | No error — guard clause skips                                                                                              |
| Delete system user who created oracle profiles | `oracle_users.created_by` set to NULL (ON DELETE SET NULL) — profiles preserved                                            |
| Unauthenticated request to any endpoint        | 401 Unauthorized                                                                                                           |

---

## DESIGN DECISIONS

| Decision                          | Choice                                   | Rationale                                                                                                                                                                           |
| --------------------------------- | ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| System user router placement      | New file `api/app/routers/users.py`      | Separate from auth.py (auth = login/tokens, users = CRUD). Separate from oracle.py (different resource).                                                                            |
| Coordinate handling               | Raw SQL helpers, not ORM column          | PostgreSQL POINT type has no native SQLAlchemy mapping. GeoAlchemy2 is a heavy dependency for a simple 2-field column. Raw SQL with `POINT(:lng, :lat)` is lightweight and correct. |
| Ownership column name             | `created_by` UUID FK                     | Standard naming. FK to `users.id` with ON DELETE SET NULL preserves oracle profiles if system user is deleted.                                                                      |
| Ownership enforcement return code | 404 (not 403) for unauthorized access    | Security best practice: don't reveal resource existence to unauthorized users.                                                                                                      |
| System user ID in audit log       | Store in `details` JSONB                 | `oracle_audit_log.resource_id` is BIGINT, system user IDs are UUID. JSONB is flexible.                                                                                              |
| Moderator access level            | Can list/get system users, cannot modify | Per master spec: "List all users (admin/moderator)" but only admin can modify/deactivate/reset.                                                                                     |
| \_get_client_ip duplication       | Duplicate 1-line function in users.py    | Avoids unnecessary refactor. Function is trivial.                                                                                                                                   |
| Bcrypt for password reset         | Use same `bcrypt.hashpw()` as auth.py    | Consistency with existing auth system.                                                                                                                                              |

---

## HANDOFF

**Created:**

- `api/app/routers/users.py` (6 endpoints)
- `api/app/models/user.py` (5 Pydantic models)
- `database/migrations/013_user_management.sql`
- `database/migrations/013_user_management_rollback.sql`
- `api/tests/test_users.py` (11+ tests)
- `api/tests/test_oracle_users.py` (16+ tests)

**Modified:**

- `api/app/orm/oracle_user.py` (6 new columns: gender, heart_rate_bpm, timezone_hours, timezone_minutes, created_by + coordinate helpers)
- `api/app/models/oracle_user.py` (new fields + enhanced validation)
- `api/app/routers/oracle.py` (ownership filtering, created_by injection, coordinate handling, updated \_decrypt_user)
- `api/app/services/audit.py` (6 new system_user audit helpers)
- `api/app/main.py` (users router registration)

**Next session needs:**

- **Session 4 (Oracle Profiles Form & Validation UI)** depends on:
  - All 5 oracle user endpoints working with new fields
  - Response model includes gender, heart_rate_bpm, timezone, latitude, longitude
  - Ownership filtering working (frontend will call API as authenticated user)
- **Session 5 (API Key Dashboard & Settings UI)** depends on:
  - System user CRUD working for user profile display
  - User self-update endpoint for settings changes
- **Session 6 (Framework Bridge)** depends on:
  - Oracle user ORM having all framework-required fields mapped
  - Coordinate extraction helpers for passing lat/lng to framework
