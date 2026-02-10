# SESSION 2 SPEC — Authentication System Hardening

**Block:** Foundation (Sessions 1-5)
**Estimated Duration:** 3-4 hours
**Complexity:** High
**Dependencies:** Session 1 (schema alignment) — uses same `users` table, `oracle_audit_log` table

---

## TL;DR

- Add **moderator role** to the existing admin/user/readonly hierarchy (scope mapping + DB constraint)
- Implement **refresh tokens** (generation, storage, `/auth/refresh` endpoint, rotation on use)
- Add **logout + token invalidation** (`/auth/logout` endpoint, token blacklist via in-memory set)
- Add **brute-force protection** (failed_attempts + locked_until columns on `users`, auto-lockout after 5 failures)
- Add **admin-only registration** (`/auth/register` endpoint, requires admin scope)
- Wire **audit logging** into all auth endpoints (login success/fail, logout, register, API key create/revoke)
- Write migration 013 (up + rollback) for new columns + role constraint update
- Extend existing 15 auth tests to 30+ with hardening coverage

---

## OBJECTIVES

1. **Add moderator role** — Master spec requires admin/moderator/user. Currently only admin/user/readonly. Add moderator with scopes between admin and user.
2. **Implement refresh tokens** — No refresh token support exists. Add generation, storage, `/auth/refresh` endpoint with token rotation.
3. **Add logout + token invalidation** — No `/auth/logout` endpoint. Add in-memory blacklist for invalidated JWTs (with TTL matching token expiry).
4. **Brute-force protection** — No failed_attempts tracking. Add lockout after 5 consecutive failures, auto-unlock after 15 minutes.
5. **Admin-only registration** — No `/auth/register` endpoint. Add with admin scope requirement.
6. **Wire audit logging** — `AuditService` has `log_auth_failed()` but it's NOT called from any auth endpoint. Wire into login, logout, register, API key operations.
7. **Database migration 013** — Add `failed_attempts`, `locked_until`, `refresh_token_hash` columns to `users`. Update role CHECK constraint.

---

## PREREQUISITES

- [ ] `users` table exists in `database/init.sql` (line 30) with UUID PK, bcrypt hash, role
- [ ] `oracle_audit_log` table exists (line 281) with action, success, ip_address, details
- [ ] `api/app/middleware/auth.py` has JWT + API key auth with scope hierarchy
- [ ] `api/app/routers/auth.py` has `/login`, `/api-keys` CRUD
- [ ] `api/app/services/audit.py` has `AuditService` with `log_auth_failed()`
- [ ] Migrations 010-012 exist in `database/migrations/`
- Verification:
  ```bash
  test -f database/init.sql && \
  test -f api/app/middleware/auth.py && \
  test -f api/app/routers/auth.py && \
  test -f api/app/services/audit.py && \
  test -f api/app/orm/user.py && \
  test -f api/app/models/auth.py && \
  test -f api/tests/test_auth.py && \
  echo "All prerequisite files OK"
  ```

---

## EXISTING CODE ANALYSIS

### What Works (Keep As-Is)

| Component             | File                                 | Lines                                      | Status                              |
| --------------------- | ------------------------------------ | ------------------------------------------ | ----------------------------------- |
| JWT creation + decode | `api/app/middleware/auth.py:80-108`  | `create_access_token()`, `_try_jwt_auth()` | Working — extend for refresh tokens |
| API key auth          | `api/app/middleware/auth.py:111-145` | `_try_api_key_auth()`                      | Working — no changes needed         |
| Scope hierarchy       | `api/app/middleware/auth.py:22-33`   | `_SCOPE_HIERARCHY` dict                    | Working — add moderator scopes      |
| Role-to-scope mapping | `api/app/middleware/auth.py:36-62`   | `_ROLE_SCOPES` dict                        | Working — add moderator mapping     |
| `get_current_user()`  | `api/app/middleware/auth.py:148-187` | Main auth dependency                       | Working — add blacklist check       |
| `require_scope()`     | `api/app/middleware/auth.py:190-205` | Scope enforcement factory                  | Working — no changes needed         |
| Login endpoint        | `api/app/routers/auth.py:26-53`      | POST `/login` with bcrypt                  | Working — add lockout check + audit |
| API key CRUD          | `api/app/routers/auth.py:56-153`     | Create/list/revoke                         | Working — add audit logging         |
| Rate limiter          | `api/app/middleware/rate_limit.py`   | Sliding window                             | Working — no changes needed         |
| AuditService          | `api/app/services/audit.py`          | Full service with `log_auth_failed()`      | Working — add auth-specific methods |

### What's Missing (Session 2 Must Add)

| Gap                         | Impact                                        | Priority |
| --------------------------- | --------------------------------------------- | -------- |
| No moderator role           | Can't have mid-tier admin access              | HIGH     |
| No refresh tokens           | Users must re-login on every JWT expiry (24h) | HIGH     |
| No logout endpoint          | Can't invalidate stolen tokens                | HIGH     |
| No brute-force protection   | Unlimited password guesses                    | CRITICAL |
| No registration endpoint    | Users can only be created via DB seed         | MEDIUM   |
| Audit not wired to auth     | Login/logout events not recorded              | HIGH     |
| No `failed_attempts` column | Can't track brute-force                       | CRITICAL |
| No `locked_until` column    | Can't auto-lockout                            | CRITICAL |

### Design Decision: Password Hashing

Master spec says "PBKDF2 600k iterations" for passwords. However:

- Existing code uses **bcrypt** (industry standard for password hashing)
- The PBKDF2 600k in `api/app/services/security.py:29` is for **encryption key derivation**, not passwords
- bcrypt is purpose-built for passwords (adaptive cost, built-in salt, timing-safe comparison)

**Decision:** Keep bcrypt for password hashing (already implemented, industry best practice). PBKDF2 600k correctly serves encryption key derivation in `security.py`. This satisfies the spirit of the master spec.

### Design Decision: Token Blacklist Storage

Options considered:

1. **Redis** — Ideal for TTL-based blacklist, but Redis is optional in this project
2. **Database table** — Persistent but adds DB load on every auth check
3. **In-memory set with TTL** — Simple, fast, sufficient for single-instance deployment

**Decision:** In-memory set with TTL cleanup (matching JWT expiry). Graceful degradation: if Redis is available (future Session 38), migrate to Redis. The in-memory approach mirrors how `rate_limit.py` already works — consistent pattern.

### Design Decision: Refresh Token Storage

Options:

1. **Separate `refresh_tokens` table** — Clean but adds a table
2. **Column on `users` table** — Simple, one active refresh token per user

**Decision:** Column on `users` table (`refresh_token_hash`). One active refresh token per user. On refresh, old token is invalidated (rotation). This is simpler and sufficient — users don't need multiple active refresh tokens.

---

## FILES TO CREATE

- `database/migrations/013_auth_hardening.sql` — Migration up
- `database/migrations/013_auth_hardening_rollback.sql` — Migration down

## FILES TO MODIFY

- `api/app/middleware/auth.py` — Add moderator scopes, blacklist check, refresh token logic
- `api/app/routers/auth.py` — Add `/register`, `/logout`, `/refresh` endpoints + audit wiring
- `api/app/models/auth.py` — Add RegisterRequest, RefreshRequest, RefreshResponse models
- `api/app/orm/user.py` — Add `failed_attempts`, `locked_until`, `refresh_token_hash` columns
- `api/app/services/audit.py` — Add auth-specific log methods (login_success, logout, register)
- `api/tests/test_auth.py` — Extend from 15 to 30+ tests
- `database/init.sql` — Update `users` table role constraint comment (informational only — migration handles the actual change)

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Database Migration 013 — Auth Hardening (~30 min)

**Tasks:**

1. Create `database/migrations/013_auth_hardening.sql`:

   ```sql
   -- Migration 013: Authentication System Hardening
   -- Adds brute-force protection columns, refresh token storage, and moderator role

   DO $$
   BEGIN
       -- Guard: skip if already applied
       IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
           RAISE NOTICE 'Migration 013 already applied, skipping.';
           RETURN;
       END IF;

       -- 1. Add brute-force protection columns to users
       ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_attempts INTEGER NOT NULL DEFAULT 0;
       ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMPTZ;

       -- 2. Add refresh token hash column
       ALTER TABLE users ADD COLUMN IF NOT EXISTS refresh_token_hash TEXT;

       -- 3. Update role constraint to include 'moderator'
       -- Drop old constraint if it exists (role was unconstrained — just a VARCHAR(20) default 'user')
       -- Add explicit CHECK constraint for the 4 valid roles
       ALTER TABLE users ADD CONSTRAINT users_role_check
           CHECK (role IN ('admin', 'moderator', 'user', 'readonly'));

       -- 4. Index for refresh token lookup (used during token refresh)
       CREATE INDEX IF NOT EXISTS idx_users_refresh_token
           ON users(refresh_token_hash) WHERE refresh_token_hash IS NOT NULL;

       -- 5. Index for locked accounts (used during login to check lockout)
       CREATE INDEX IF NOT EXISTS idx_users_locked
           ON users(locked_until) WHERE locked_until IS NOT NULL;

       -- 6. Record migration
       INSERT INTO schema_migrations (version, name)
       VALUES ('013', 'Auth hardening: brute-force protection, refresh tokens, moderator role');

       RAISE NOTICE 'Migration 013 applied successfully.';
   END $$;
   ```

2. Create `database/migrations/013_auth_hardening_rollback.sql`:

   ```sql
   -- Rollback Migration 013: Auth Hardening
   DO $$
   BEGIN
       -- Guard: skip if not applied
       IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '013') THEN
           RAISE NOTICE 'Migration 013 not applied, nothing to rollback.';
           RETURN;
       END IF;

       -- Drop indexes
       DROP INDEX IF EXISTS idx_users_locked;
       DROP INDEX IF EXISTS idx_users_refresh_token;

       -- Drop role constraint
       ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;

       -- Remove columns (reverse order of addition)
       ALTER TABLE users DROP COLUMN IF EXISTS refresh_token_hash;
       ALTER TABLE users DROP COLUMN IF EXISTS locked_until;
       ALTER TABLE users DROP COLUMN IF EXISTS failed_attempts;

       -- Remove migration record
       DELETE FROM schema_migrations WHERE version = '013';

       RAISE NOTICE 'Migration 013 rolled back successfully.';
   END $$;
   ```

3. Migration design notes:
   - `failed_attempts` defaults to 0 — backward compatible with existing users
   - `locked_until` is nullable — NULL means not locked
   - `refresh_token_hash` is nullable — NULL means no active refresh token
   - Role constraint adds 'moderator' to the existing set. Existing data with 'admin', 'user', 'readonly' all pass.
   - Both migration and rollback are idempotent (guard clauses + IF NOT EXISTS / IF EXISTS)

**Checkpoint:**

- [ ] Migration file has valid SQL syntax
- [ ] Rollback reverses ALL changes from migration
- [ ] Both files have guard clauses for idempotency
- [ ] `failed_attempts` defaults to 0 (not NULL)
- [ ] Role CHECK includes all 4 roles: admin, moderator, user, readonly
- Verify:
  ```bash
  test -f database/migrations/013_auth_hardening.sql && \
  test -f database/migrations/013_auth_hardening_rollback.sql && \
  grep -q "failed_attempts" database/migrations/013_auth_hardening.sql && \
  grep -q "moderator" database/migrations/013_auth_hardening.sql && \
  grep -q "refresh_token_hash" database/migrations/013_auth_hardening.sql && \
  echo "Migration 013 files OK"
  ```

STOP if checkpoint fails

---

### Phase 2: User ORM + Pydantic Model Updates (~20 min)

**Tasks:**

1. Update `api/app/orm/user.py` — Add 3 new columns to the `User` ORM model:

   ```python
   # Add to existing imports
   from sqlalchemy import Boolean, DateTime, Integer, String, Text, func

   # Add these columns to the User class (after is_active):
   failed_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
   locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
   refresh_token_hash: Mapped[str | None] = mapped_column(Text)
   ```

2. Update `api/app/models/auth.py` — Add new Pydantic models:

   ```python
   class RegisterRequest(BaseModel):
       username: str
       password: str
       role: str = "user"  # admin, moderator, user, readonly

   class RegisterResponse(BaseModel):
       id: str
       username: str
       role: str
       created_at: datetime

   class RefreshRequest(BaseModel):
       refresh_token: str

   class RefreshResponse(BaseModel):
       access_token: str
       refresh_token: str
       token_type: str = "bearer"
       expires_in: int  # seconds
   ```

3. Extend `TokenResponse` to include refresh_token:

   ```python
   class TokenResponse(BaseModel):
       access_token: str
       refresh_token: str | None = None  # Added — None for backward compat
       token_type: str = "bearer"
       expires_in: int  # seconds
   ```

**Checkpoint:**

- [ ] `User` ORM has `failed_attempts`, `locked_until`, `refresh_token_hash` columns
- [ ] `RegisterRequest`, `RegisterResponse`, `RefreshRequest`, `RefreshResponse` models exist
- [ ] `TokenResponse` has optional `refresh_token` field
- [ ] No `any` types used (per forbidden patterns)
- Verify:
  ```bash
  grep -q "failed_attempts" api/app/orm/user.py && \
  grep -q "locked_until" api/app/orm/user.py && \
  grep -q "refresh_token_hash" api/app/orm/user.py && \
  grep -q "RegisterRequest" api/app/models/auth.py && \
  grep -q "RefreshRequest" api/app/models/auth.py && \
  echo "ORM + models OK"
  ```

STOP if checkpoint fails

---

### Phase 3: Moderator Role + Scope Mapping (~20 min)

**Tasks:**

1. Update `_ROLE_SCOPES` in `api/app/middleware/auth.py` to add moderator role:

   ```python
   _ROLE_SCOPES = {
       "admin": [
           "oracle:admin", "oracle:write", "oracle:read",
           "scanner:admin", "scanner:write", "scanner:read",
           "vault:admin", "vault:write", "vault:read",
           "admin",
       ],
       "moderator": [
           "oracle:admin", "oracle:write", "oracle:read",
           "scanner:read",
           "vault:read",
       ],
       "user": [
           "oracle:write", "oracle:read",
           "scanner:write", "scanner:read",
           "vault:write", "vault:read",
       ],
       "readonly": [
           "oracle:read",
           "scanner:read",
           "vault:read",
       ],
   }
   ```

   Moderator scope rationale:
   - **oracle:admin** — Can manage Oracle users and readings (primary Oracle responsibility)
   - **oracle:write + oracle:read** — Full Oracle access
   - **scanner:read** — Can view scanner results but NOT write/admin (scanner is admin-only territory)
   - **vault:read** — Can view findings but NOT modify/admin (vault is sensitive)
   - No **admin** scope — Cannot access admin-only system endpoints
   - No **scanner:write/admin** — Cannot control scanner operations
   - No **vault:write/admin** — Cannot modify vault findings

2. Update `_role_to_scopes()` — No change needed (already falls back to readonly for unknown roles, and moderator will be in the dict).

3. Verify scope hierarchy expansion works for moderator:
   - `_expand_scopes(["oracle:admin"])` → includes `oracle:write`, `oracle:read`
   - Moderator gets oracle:admin which implies oracle:write and oracle:read ✓

**Checkpoint:**

- [ ] `_ROLE_SCOPES` has 4 entries: admin, moderator, user, readonly
- [ ] Moderator has oracle:admin but NOT admin, scanner:admin, vault:admin
- [ ] Moderator has scanner:read, vault:read (read-only for non-Oracle)
- Verify:
  ```bash
  grep -q '"moderator"' api/app/middleware/auth.py && \
  echo "Moderator role added"
  ```

STOP if checkpoint fails

---

### Phase 4: Refresh Token System (~45 min)

**Tasks:**

1. Add refresh token generation to `api/app/middleware/auth.py`:

   ```python
   import secrets

   _REFRESH_TOKEN_BYTES = 32  # 256-bit refresh token
   _REFRESH_TOKEN_EXPIRE_DAYS = 30

   def create_refresh_token() -> str:
       """Generate a cryptographically secure refresh token."""
       return secrets.token_urlsafe(_REFRESH_TOKEN_BYTES)

   def hash_refresh_token(token: str) -> str:
       """SHA-256 hash a refresh token for storage."""
       return hashlib.sha256(token.encode()).hexdigest()
   ```

2. Update `create_access_token()` to return both tokens (or keep it focused on JWT only — the router will handle pairing). Decision: Keep `create_access_token()` focused on JWT. The router orchestrates pairing access + refresh tokens.

3. Update login endpoint in `api/app/routers/auth.py` to generate and store refresh token:

   ```python
   @router.post("/login", response_model=TokenResponse)
   def login(request: LoginRequest, db: Session = Depends(get_db)):
       user = db.query(User).filter(User.username == request.username).first()

       # Check if account is locked
       if user and user.locked_until:
           if user.locked_until > datetime.now(timezone.utc):
               raise HTTPException(
                   status_code=status.HTTP_423_LOCKED,
                   detail="Account is temporarily locked due to too many failed attempts",
               )
           # Lock expired — reset
           user.failed_attempts = 0
           user.locked_until = None

       # Verify credentials
       if not user or not _bcrypt.checkpw(
           request.password.encode("utf-8"), user.password_hash.encode("utf-8")
       ):
           # Track failed attempt
           if user:
               user.failed_attempts = (user.failed_attempts or 0) + 1
               if user.failed_attempts >= 5:
                   user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
               db.commit()
           raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
               detail="Invalid username or password",
           )

       if not user.is_active:
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
       db.commit()

       access_token = create_access_token(user.id, user.username, user.role)

       return TokenResponse(
           access_token=access_token,
           refresh_token=refresh_raw,
           expires_in=settings.jwt_expire_minutes * 60,
       )
   ```

4. Add `/auth/refresh` endpoint in `api/app/routers/auth.py`:

   ```python
   @router.post("/refresh", response_model=RefreshResponse)
   def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
       """Exchange a valid refresh token for new access + refresh tokens (rotation)."""
       token_hash = hash_refresh_token(request.refresh_token)
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
       db.commit()

       new_access = create_access_token(user.id, user.username, user.role)

       return RefreshResponse(
           access_token=new_access,
           refresh_token=new_refresh,
           expires_in=settings.jwt_expire_minutes * 60,
       )
   ```

5. Design notes:
   - Refresh token rotation: every use of `/auth/refresh` generates a new refresh token and invalidates the old one. This limits the window for stolen refresh tokens.
   - One active refresh token per user: simpler than a table, sufficient for this use case.
   - Refresh token is 256-bit (32 bytes via `secrets.token_urlsafe`), stored as SHA-256 hash.
   - No separate expiry tracking for refresh tokens: they expire when a new one is issued or on logout.

**Checkpoint:**

- [ ] `create_refresh_token()` and `hash_refresh_token()` exist in auth.py
- [ ] Login endpoint generates and stores refresh token hash
- [ ] `/auth/refresh` endpoint exists and rotates tokens
- [ ] Refresh token is `secrets.token_urlsafe(32)` — cryptographically secure
- [ ] Old refresh token is invalidated on rotation
- Verify:
  ```bash
  grep -q "create_refresh_token" api/app/middleware/auth.py && \
  grep -q "hash_refresh_token" api/app/middleware/auth.py && \
  grep -q "/refresh" api/app/routers/auth.py && \
  echo "Refresh token system OK"
  ```

STOP if checkpoint fails

---

### Phase 5: Logout + Brute-Force Protection (~30 min)

**Tasks:**

1. Add token blacklist to `api/app/middleware/auth.py`:

   ```python
   import threading
   import time

   class _TokenBlacklist:
       """In-memory JWT blacklist with TTL cleanup.

       Mirrors the in-memory pattern used by rate_limit.py.
       Tokens auto-expire from the blacklist when their JWT expiry passes.
       """

       def __init__(self):
           self._tokens: dict[str, float] = {}  # token_hash -> expiry_timestamp
           self._lock = threading.Lock()

       def add(self, token: str, expires_at: float) -> None:
           """Blacklist a token until its expiry time."""
           token_hash = hashlib.sha256(token.encode()).hexdigest()
           with self._lock:
               self._tokens[token_hash] = expires_at
               self._cleanup()

       def is_blacklisted(self, token: str) -> bool:
           """Check if a token is blacklisted."""
           token_hash = hashlib.sha256(token.encode()).hexdigest()
           with self._lock:
               expiry = self._tokens.get(token_hash)
               if expiry is None:
                   return False
               if time.time() > expiry:
                   del self._tokens[token_hash]
                   return False
               return True

       def _cleanup(self) -> None:
           """Remove expired entries. Called internally under lock."""
           now = time.time()
           expired = [k for k, v in self._tokens.items() if now > v]
           for k in expired:
               del self._tokens[k]

   _blacklist = _TokenBlacklist()
   ```

2. Update `_try_jwt_auth()` to check blacklist:

   ```python
   def _try_jwt_auth(token: str) -> dict | None:
       """Try to decode as JWT. Returns user context dict or None."""
       if _blacklist.is_blacklisted(token):
           return None
       try:
           payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.jwt_algorithm])
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
   ```

3. Add `/auth/logout` endpoint in `api/app/routers/auth.py`:

   ```python
   @router.post("/logout")
   def logout(
       credentials: HTTPAuthorizationCredentials = Security(security_scheme),
       db: Session = Depends(get_db),
       user: dict = Depends(get_current_user),
   ):
       """Logout: blacklist current JWT and clear refresh token."""
       token = credentials.credentials

       # Blacklist the JWT until it expires
       try:
           payload = jwt.decode(
               token, settings.api_secret_key,
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
               db.commit()

       return {"detail": "Logged out successfully"}
   ```

4. Brute-force protection is handled in Phase 4's login endpoint update (failed_attempts tracking + locked_until). This phase verifies the lockout constants:
   - `MAX_FAILED_ATTEMPTS = 5` — Lock after 5 consecutive failures
   - `LOCKOUT_DURATION_MINUTES = 15` — Auto-unlock after 15 minutes
   - These are defined as module-level constants in `api/app/routers/auth.py`

**Checkpoint:**

- [ ] `_TokenBlacklist` class exists in auth.py with `add()` and `is_blacklisted()`
- [ ] `_try_jwt_auth()` checks blacklist before decoding
- [ ] `/auth/logout` endpoint blacklists JWT and clears refresh token
- [ ] Lockout constants defined: `MAX_FAILED_ATTEMPTS = 5`, `LOCKOUT_DURATION_MINUTES = 15`
- [ ] Thread-safe blacklist (uses `threading.Lock`)
- Verify:
  ```bash
  grep -q "_TokenBlacklist" api/app/middleware/auth.py && \
  grep -q "is_blacklisted" api/app/middleware/auth.py && \
  grep -q "/logout" api/app/routers/auth.py && \
  grep -q "MAX_FAILED_ATTEMPTS" api/app/routers/auth.py && \
  echo "Logout + brute-force OK"
  ```

STOP if checkpoint fails

---

### Phase 6: Admin-Only Registration Endpoint (~20 min)

**Tasks:**

1. Add `/auth/register` endpoint in `api/app/routers/auth.py`:

   ```python
   @router.post("/register", response_model=RegisterResponse)
   def register(
       request: RegisterRequest,
       db: Session = Depends(get_db),
       user: dict = Depends(require_scope("admin")),
   ):
       """Create a new user account. Admin-only."""
       # Validate role
       valid_roles = {"admin", "moderator", "user", "readonly"}
       if request.role not in valid_roles:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=f"Invalid role. Must be one of: {', '.join(sorted(valid_roles))}",
           )

       # Check username uniqueness
       existing = db.query(User).filter(User.username == request.username).first()
       if existing:
           raise HTTPException(
               status_code=status.HTTP_409_CONFLICT,
               detail="Username already exists",
           )

       # Hash password with bcrypt
       pw_hash = _bcrypt.hashpw(
           request.password.encode("utf-8"), _bcrypt.gensalt()
       ).decode("utf-8")

       new_user = User(
           id=str(uuid.uuid4()),
           username=request.username,
           password_hash=pw_hash,
           role=request.role,
       )
       db.add(new_user)
       db.commit()
       db.refresh(new_user)

       return RegisterResponse(
           id=new_user.id,
           username=new_user.username,
           role=new_user.role,
           created_at=new_user.created_at,
       )
   ```

2. Registration requirements:
   - Requires `admin` scope (uses `require_scope("admin")` dependency)
   - Password minimum length validation via Pydantic (add `min_length=8` to `RegisterRequest.password`)
   - Username uniqueness enforced at application level (DB UNIQUE constraint is backup)
   - Returns `409 CONFLICT` for duplicate usernames (not generic 400)
   - No email required (not in current schema)

3. Update `RegisterRequest` with validation:

   ```python
   class RegisterRequest(BaseModel):
       username: str = Field(..., min_length=3, max_length=100)
       password: str = Field(..., min_length=8, max_length=128)
       role: str = "user"
   ```

**Checkpoint:**

- [ ] `/auth/register` endpoint exists
- [ ] Requires `admin` scope
- [ ] Password minimum 8 characters
- [ ] Username uniqueness checked with 409 response
- [ ] Role validated against allowed set
- Verify:
  ```bash
  grep -q "/register" api/app/routers/auth.py && \
  grep -q 'require_scope("admin")' api/app/routers/auth.py && \
  grep -q "min_length=8" api/app/models/auth.py && \
  echo "Registration endpoint OK"
  ```

STOP if checkpoint fails

---

### Phase 7: Auth Audit Logging + Comprehensive Tests (~60 min)

**Tasks:**

#### Part A: Audit Service Extensions

1. Add auth-specific log methods to `api/app/services/audit.py`:

   ```python
   def log_auth_login(
       self,
       user_id: str,
       *,
       ip: str | None = None,
       username: str | None = None,
   ) -> OracleAuditLog:
       """Log a successful login."""
       return self.log(
           "auth.login",
           user_id=user_id,
           resource_type="auth",
           ip_address=ip,
           details={"username": username},
       )

   def log_auth_logout(
       self,
       user_id: str,
       *,
       ip: str | None = None,
   ) -> OracleAuditLog:
       """Log a logout."""
       return self.log(
           "auth.logout",
           user_id=user_id,
           resource_type="auth",
           ip_address=ip,
       )

   def log_auth_register(
       self,
       new_user_id: str,
       registered_by: str,
       *,
       ip: str | None = None,
       role: str | None = None,
   ) -> OracleAuditLog:
       """Log a new user registration."""
       return self.log(
           "auth.register",
           user_id=registered_by,
           resource_type="auth",
           ip_address=ip,
           details={"new_user_id": new_user_id, "role": role},
       )

   def log_auth_token_refresh(
       self,
       user_id: str,
       *,
       ip: str | None = None,
   ) -> OracleAuditLog:
       """Log a token refresh."""
       return self.log(
           "auth.token_refresh",
           user_id=user_id,
           resource_type="auth",
           ip_address=ip,
       )

   def log_auth_lockout(
       self,
       *,
       ip: str | None = None,
       username: str | None = None,
   ) -> OracleAuditLog:
       """Log an account lockout due to brute-force."""
       return self.log(
           "auth.lockout",
           success=False,
           resource_type="auth",
           ip_address=ip,
           details={"username": username},
       )

   def log_api_key_created(
       self,
       user_id: str,
       key_name: str,
       *,
       ip: str | None = None,
   ) -> OracleAuditLog:
       """Log an API key creation."""
       return self.log(
           "auth.api_key_created",
           user_id=user_id,
           resource_type="api_key",
           ip_address=ip,
           details={"key_name": key_name},
       )

   def log_api_key_revoked(
       self,
       user_id: str,
       key_id: str,
       *,
       ip: str | None = None,
   ) -> OracleAuditLog:
       """Log an API key revocation."""
       return self.log(
           "auth.api_key_revoked",
           user_id=user_id,
           resource_type="api_key",
           ip_address=ip,
           details={"key_id": key_id},
       )
   ```

2. The existing `log_auth_failed()` method (line 143) already handles failed logins. No change needed, just wire it into the login endpoint.

#### Part B: Wire Audit into Auth Endpoints

3. Update all auth endpoints in `api/app/routers/auth.py` to call audit service:
   - `POST /login` — on success: `audit.log_auth_login()`, on failure: `audit.log_auth_failed()`, on lockout: `audit.log_auth_lockout()`
   - `POST /logout` — `audit.log_auth_logout()`
   - `POST /register` — `audit.log_auth_register()`
   - `POST /refresh` — `audit.log_auth_token_refresh()`
   - `POST /api-keys` — `audit.log_api_key_created()`
   - `DELETE /api-keys/{key_id}` — `audit.log_api_key_revoked()`

4. Add `Request` parameter to endpoints that need IP address:

   ```python
   from fastapi import Request

   @router.post("/login", response_model=TokenResponse)
   def login(request_body: LoginRequest, request: Request, db: Session = Depends(get_db)):
       ip = request.client.host if request.client else None
       # ... existing logic ...
       # On success:
       audit = AuditService(db)
       audit.log_auth_login(user.id, ip=ip, username=user.username)
       db.commit()
   ```

   Note: Rename `request` parameter to `request_body` for `LoginRequest` to avoid shadowing the FastAPI `Request`.

#### Part C: Comprehensive Tests

5. Extend `api/tests/test_auth.py` with hardening tests. Add these test functions:

   **Moderator role tests:**

   ```python
   def test_moderator_role_scopes():
       """Moderator gets oracle:admin but not system admin."""
       scopes = _role_to_scopes("moderator")
       assert "oracle:admin" in scopes
       assert "oracle:write" in scopes
       assert "oracle:read" in scopes
       assert "scanner:read" in scopes
       assert "vault:read" in scopes
       assert "admin" not in scopes
       assert "scanner:admin" not in scopes
       assert "vault:admin" not in scopes

   def test_moderator_jwt_has_correct_scopes():
       """JWT for moderator role includes moderator scopes."""
       token = create_access_token("mod-1", "moderator_user", "moderator")
       result = _try_jwt_auth(token)
       assert result is not None
       assert result["role"] == "moderator"
       assert "oracle:admin" in result["scopes"]
       assert "admin" not in result["scopes"]
   ```

   **Refresh token tests:**

   ```python
   def test_create_refresh_token_uniqueness():
       """Each refresh token is unique."""
       tokens = {create_refresh_token() for _ in range(100)}
       assert len(tokens) == 100

   def test_hash_refresh_token_deterministic():
       """Same input always produces same hash."""
       token = "test-token-value"
       assert hash_refresh_token(token) == hash_refresh_token(token)

   def test_hash_refresh_token_different_inputs():
       """Different tokens produce different hashes."""
       assert hash_refresh_token("token-a") != hash_refresh_token("token-b")
   ```

   **Token blacklist tests:**

   ```python
   def test_blacklist_add_and_check():
       """Blacklisted token is detected."""
       blacklist = _TokenBlacklist()
       future = time.time() + 3600
       blacklist.add("test-token", future)
       assert blacklist.is_blacklisted("test-token") is True

   def test_blacklist_expired_not_blocked():
       """Expired blacklist entry is not detected."""
       blacklist = _TokenBlacklist()
       past = time.time() - 1
       blacklist.add("old-token", past)
       assert blacklist.is_blacklisted("old-token") is False

   def test_blacklist_unknown_token():
       """Non-blacklisted token passes."""
       blacklist = _TokenBlacklist()
       assert blacklist.is_blacklisted("never-added") is False

   def test_blacklisted_jwt_rejected():
       """JWT that's been blacklisted returns None from _try_jwt_auth."""
       token = create_access_token("user-1", "alice", "user")
       # Blacklist it
       _blacklist.add(token, time.time() + 3600)
       result = _try_jwt_auth(token)
       assert result is None
       # Cleanup
       _blacklist._tokens.clear()
   ```

   **Brute-force protection tests:**

   ```python
   def test_failed_attempts_increment(db, test_user):
       """Failed login increments failed_attempts."""
       # Attempt login with wrong password
       from app.routers.auth import login
       # ... integration test via HTTP client

   def test_account_locks_after_5_failures(db, test_user):
       """5 consecutive failures lock the account."""
       test_user.failed_attempts = 4
       db.commit()
       # Next failure should trigger lockout
       # ... integration test

   def test_locked_account_rejected(db, test_user):
       """Locked account returns 423."""
       test_user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
       db.commit()
       # Login attempt should return 423
       # ... integration test

   def test_lock_expires_after_duration(db, test_user):
       """Expired lock allows login again."""
       test_user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
       test_user.failed_attempts = 5
       db.commit()
       # Login should succeed (lock expired)
       # ... integration test

   def test_successful_login_resets_failed_attempts(db, test_user):
       """Successful login resets failed_attempts to 0."""
       test_user.failed_attempts = 3
       db.commit()
       # Successful login
       # Verify failed_attempts == 0
   ```

   **Registration tests:**

   ```python
   def test_register_requires_admin_scope():
       """Non-admin cannot register users."""
       # User with 'user' role tries /register → 403

   def test_register_creates_user():
       """Admin can register a new user."""
       # POST /register with admin token
       # Verify user created with correct role

   def test_register_duplicate_username_409():
       """Duplicate username returns 409."""

   def test_register_invalid_role_400():
       """Invalid role returns 400."""

   def test_register_password_too_short_422():
       """Password under 8 chars returns 422 (Pydantic validation)."""
   ```

   **Audit logging tests:**

   ```python
   def test_login_creates_audit_entry(db, test_user):
       """Successful login creates auth.login audit entry."""

   def test_failed_login_creates_audit_entry(db, test_user):
       """Failed login creates auth.failed audit entry."""

   def test_logout_creates_audit_entry(db, test_user):
       """Logout creates auth.logout audit entry."""
   ```

   Total new tests: **~18 new tests** (bringing total from 15 to 33+)

**Checkpoint:**

- [ ] AuditService has 7 new methods: `log_auth_login`, `log_auth_logout`, `log_auth_register`, `log_auth_token_refresh`, `log_auth_lockout`, `log_api_key_created`, `log_api_key_revoked`
- [ ] All 6 auth endpoints call audit service
- [ ] Tests cover: moderator scopes, refresh tokens, blacklist, brute-force, registration, audit
- [ ] All tests pass: `cd api && python3 -m pytest tests/test_auth.py -v`
- Verify:
  ```bash
  grep -q "log_auth_login" api/app/services/audit.py && \
  grep -q "log_auth_logout" api/app/services/audit.py && \
  grep -q "log_auth_register" api/app/services/audit.py && \
  grep -q "log_auth_lockout" api/app/services/audit.py && \
  grep -c "def test_" api/tests/test_auth.py | xargs -I{} test {} -ge 30 && \
  echo "Audit + tests OK"
  ```

STOP if checkpoint fails

---

## TESTS TO WRITE

| #   | Test Function                                  | File                     | Verifies                                                     |
| --- | ---------------------------------------------- | ------------------------ | ------------------------------------------------------------ |
| 1   | `test_moderator_role_scopes`                   | `api/tests/test_auth.py` | Moderator has correct scopes (oracle:admin, no system admin) |
| 2   | `test_moderator_jwt_has_correct_scopes`        | `api/tests/test_auth.py` | JWT for moderator contains right scopes                      |
| 3   | `test_create_refresh_token_uniqueness`         | `api/tests/test_auth.py` | 100 refresh tokens are all unique                            |
| 4   | `test_hash_refresh_token_deterministic`        | `api/tests/test_auth.py` | Same input → same hash                                       |
| 5   | `test_hash_refresh_token_different_inputs`     | `api/tests/test_auth.py` | Different tokens → different hashes                          |
| 6   | `test_blacklist_add_and_check`                 | `api/tests/test_auth.py` | Token blacklist detection works                              |
| 7   | `test_blacklist_expired_not_blocked`           | `api/tests/test_auth.py` | Expired blacklist entries auto-clear                         |
| 8   | `test_blacklist_unknown_token`                 | `api/tests/test_auth.py` | Non-blacklisted tokens pass through                          |
| 9   | `test_blacklisted_jwt_rejected`                | `api/tests/test_auth.py` | \_try_jwt_auth returns None for blacklisted JWT              |
| 10  | `test_failed_attempts_increment`               | `api/tests/test_auth.py` | Wrong password increments counter                            |
| 11  | `test_account_locks_after_5_failures`          | `api/tests/test_auth.py` | 5th failure triggers lockout                                 |
| 12  | `test_locked_account_rejected`                 | `api/tests/test_auth.py` | Locked account returns 423                                   |
| 13  | `test_lock_expires_after_duration`             | `api/tests/test_auth.py` | Expired lock allows login                                    |
| 14  | `test_successful_login_resets_failed_attempts` | `api/tests/test_auth.py` | Success resets counter to 0                                  |
| 15  | `test_register_requires_admin_scope`           | `api/tests/test_auth.py` | Non-admin gets 403 on /register                              |
| 16  | `test_register_creates_user`                   | `api/tests/test_auth.py` | Admin can create user via /register                          |
| 17  | `test_register_duplicate_username_409`         | `api/tests/test_auth.py` | Duplicate username → 409                                     |
| 18  | `test_register_invalid_role_400`               | `api/tests/test_auth.py` | Bad role → 400                                               |
| 19  | `test_register_password_too_short_422`         | `api/tests/test_auth.py` | Short password → 422                                         |
| 20  | `test_login_creates_audit_entry`               | `api/tests/test_auth.py` | Login success writes audit log                               |
| 21  | `test_failed_login_creates_audit_entry`        | `api/tests/test_auth.py` | Login failure writes audit log                               |
| 22  | `test_logout_creates_audit_entry`              | `api/tests/test_auth.py` | Logout writes audit log                                      |
| 23  | `test_refresh_rotates_token`                   | `api/tests/test_auth.py` | Refresh produces new access + refresh tokens                 |
| 24  | `test_refresh_invalid_token_401`               | `api/tests/test_auth.py` | Bad refresh token → 401                                      |
| 25  | `test_logout_clears_refresh_token`             | `api/tests/test_auth.py` | Logout nullifies refresh_token_hash                          |

Total: **25 new tests** + 15 existing = **40 tests**

Run: `cd api && python3 -m pytest tests/test_auth.py -v`

---

## ACCEPTANCE CRITERIA

- [ ] `users` table has 3 new columns: `failed_attempts` (INT, default 0), `locked_until` (TIMESTAMPTZ, nullable), `refresh_token_hash` (TEXT, nullable)
- [ ] `users.role` has CHECK constraint for ('admin', 'moderator', 'user', 'readonly')
- [ ] Migration 013 applies cleanly and is idempotent
- [ ] Rollback 013 removes all changes cleanly
- [ ] Moderator role exists in `_ROLE_SCOPES` with oracle:admin, scanner:read, vault:read
- [ ] `POST /auth/login` returns both access_token and refresh_token
- [ ] `POST /auth/login` tracks failed_attempts and locks after 5 failures
- [ ] `POST /auth/login` returns 423 for locked accounts
- [ ] `POST /auth/refresh` exchanges refresh token for new token pair (rotation)
- [ ] `POST /auth/logout` blacklists JWT and clears refresh token
- [ ] `POST /auth/register` creates user (admin-only, password min 8 chars)
- [ ] All auth endpoints log to `oracle_audit_log` via AuditService
- [ ] 40+ auth tests pass
- [ ] No `any` types, no bare `except:`, no hardcoded paths
- Verify all:
  ```bash
  grep -q "failed_attempts" api/app/orm/user.py && \
  grep -q "locked_until" api/app/orm/user.py && \
  grep -q "refresh_token_hash" api/app/orm/user.py && \
  grep -q '"moderator"' api/app/middleware/auth.py && \
  grep -q "_TokenBlacklist" api/app/middleware/auth.py && \
  grep -q "/register" api/app/routers/auth.py && \
  grep -q "/logout" api/app/routers/auth.py && \
  grep -q "/refresh" api/app/routers/auth.py && \
  grep -q "log_auth_login" api/app/services/audit.py && \
  test -f database/migrations/013_auth_hardening.sql && \
  test -f database/migrations/013_auth_hardening_rollback.sql && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                      | Expected Behavior                                   |
| --------------------------------------------- | --------------------------------------------------- |
| Login with wrong password (1st-4th time)      | 401 + `failed_attempts` incremented                 |
| Login with wrong password (5th time)          | 401 + account locked for 15 minutes                 |
| Login to locked account (within 15 min)       | 423 Locked + no failed_attempts change              |
| Login to locked account (after 15 min)        | Lock cleared, normal login proceeds                 |
| Successful login after 3 failures             | `failed_attempts` reset to 0                        |
| Login to disabled account (`is_active=False`) | 403 Forbidden (checked after credential verify)     |
| Use blacklisted JWT                           | 401/403 — `_try_jwt_auth()` returns None            |
| Refresh with invalid token                    | 401 Unauthorized                                    |
| Refresh with used/rotated token               | 401 (old hash no longer matches)                    |
| Refresh for disabled account                  | 403 Forbidden                                       |
| Register without admin scope                  | 403 Insufficient scope                              |
| Register with duplicate username              | 409 Conflict                                        |
| Register with role='superadmin'               | 400 Invalid role                                    |
| Register with 3-char password                 | 422 Validation error (min_length=8)                 |
| Migration 013 run twice                       | No error — guard clause skips                       |
| Rollback run when 013 not applied             | No error — guard clause skips                       |
| Logout with API key (not JWT)                 | Success — no blacklist action, clears refresh token |

---

## HANDOFF

**Created:**

- `database/migrations/013_auth_hardening.sql`
- `database/migrations/013_auth_hardening_rollback.sql`

**Modified:**

- `api/app/middleware/auth.py` — Moderator scopes, token blacklist, refresh token helpers
- `api/app/routers/auth.py` — `/register`, `/logout`, `/refresh` endpoints + brute-force + audit wiring
- `api/app/models/auth.py` — RegisterRequest, RegisterResponse, RefreshRequest, RefreshResponse
- `api/app/orm/user.py` — failed_attempts, locked_until, refresh_token_hash columns
- `api/app/services/audit.py` — 7 new auth-specific log methods
- `api/tests/test_auth.py` — Extended from 15 to 40 tests

**Next session needs:**

- **Session 3 (User Profile Management)** depends on:
  - Auth system being stable (all 4 roles working, JWT + refresh tokens)
  - `require_scope()` working for moderator role
  - `/auth/register` existing so profile CRUD can reference real users
- **Session 4 (Oracle User Profiles)** depends on:
  - Auth hardening complete — all endpoints protected with correct scopes
  - Audit logging wired in — Session 4 follows same audit pattern for Oracle user CRUD
- **Session 38 (Admin Panel)** depends on:
  - Moderator role existing — admin panel will have role-based views
  - Audit log entries — admin panel will display auth events
