# SESSION 41 SPEC — Integration Tests: Auth & Profiles

**Block:** Testing & Deployment (Sessions 41-45)
**Estimated Duration:** 4-5 hours
**Complexity:** High
**Dependencies:** All previous sessions (1-40) — requires functional API, database, auth middleware, and Oracle profile endpoints

---

## TL;DR

- Write comprehensive integration tests for the full authentication lifecycle: JWT login, token validation edge cases, failed login handling, role-based access control, API key creation/usage/revocation, and legacy API secret fallback
- Write comprehensive integration tests for Oracle profile CRUD: create, read, update, delete (soft-delete), duplicate detection, and full Persian (Farsi) UTF-8 round-trip verification
- Extend `integration/tests/conftest.py` with reusable fixtures: seeded users (admin, user, readonly), JWT token helpers, role-specific HTTP clients, API key fixtures, sample profiles with English and Persian data
- All tests run against a real PostgreSQL database in Docker — no mocking, no SQLite fallbacks
- Target: 77 new tests across 2 new files, 13+ new fixtures in conftest, full coverage of auth and profile edge cases

---

## OBJECTIVES

1. **Auth flow coverage** — Test every authentication path the API supports: JWT login with valid/invalid credentials, token structure validation, role-based scope enforcement on protected endpoints, API key CRUD and authentication, legacy Bearer token fallback, and disabled account rejection
2. **Profile flow coverage** — Test the complete Oracle profile lifecycle through the API: creation with all fields (EN + FA), retrieval (single + list + search), partial updates, soft-delete, re-creation after delete, duplicate detection, and input validation
3. **Persian UTF-8 verification** — Prove that Persian names, mother names, and search queries survive the full round-trip: client -> API -> encryption -> database -> decryption -> API -> client
4. **Role isolation** — Verify that readonly users cannot write, non-admin users cannot delete or access audit, and each role sees exactly the scopes it should
5. **Fixture infrastructure** — Build reusable fixtures that future sessions (42-45) can import for their own integration tests

---

## PREREQUISITES

- [ ] PostgreSQL is running (Docker or local) on configured host/port
- [ ] API server is running on port 8000
- [ ] At least one user exists in the `users` table (or seed data has been applied)
- [ ] `API_SECRET_KEY` is set in `.env` (used for legacy auth and test bootstrapping)
- [ ] Integration test directory exists: `integration/tests/`
- Verification:
  ```bash
  curl -s http://localhost:8000/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('API OK' if d.get('status')=='healthy' else 'API DOWN')"
  test -f integration/tests/conftest.py && echo "Conftest OK"
  test -d integration/tests/ && echo "Test directory OK"
  ```

---

## CODEBASE CONTEXT

### Authentication Architecture (from `api/app/middleware/auth.py`)

The `get_current_user` dependency resolves credentials in this order:

1. **JWT token** — Decoded with `HS256` using `API_SECRET_KEY`. Payload contains `sub` (user_id), `username`, `role`, `scopes`, `exp`, `iat`
2. **API key** — SHA-256 hashed, looked up in `api_keys` table. Must be active and not expired. Updates `last_used` on each use
3. **Legacy fallback** — If the raw Bearer token matches `API_SECRET_KEY` exactly, grants admin-level access with `auth_type: "legacy"`

Missing/invalid credentials: 401. Valid but insufficient: 403.

### Scope Hierarchy (from `api/app/middleware/auth.py`)

```
admin role   -> oracle:admin, oracle:write, oracle:read, scanner:*, vault:*, admin
user role    -> oracle:write, oracle:read, scanner:write/read, vault:write/read
readonly     -> oracle:read, scanner:read, vault:read
```

Scope expansion: `oracle:admin` implies `oracle:write` and `oracle:read`.

### Auth Endpoints (mounted at `/api/auth/`)

| Method | Path                          | Auth Required | Scope       | Description                           |
| ------ | ----------------------------- | ------------- | ----------- | ------------------------------------- |
| POST   | `/api/auth/login`             | No            | None        | Returns JWT `access_token`            |
| POST   | `/api/auth/api-keys`          | Yes           | Any         | Create API key (returns raw key once) |
| GET    | `/api/auth/api-keys`          | Yes           | Any         | List user's API keys                  |
| DELETE | `/api/auth/api-keys/{key_id}` | Yes           | Owner/Admin | Revoke (soft-delete) API key          |

### Oracle Profile Endpoints (mounted at `/api/oracle/`)

| Method | Path                     | Scope Required | Description                  |
| ------ | ------------------------ | -------------- | ---------------------------- |
| POST   | `/api/oracle/users`      | oracle:write   | Create profile (201)         |
| GET    | `/api/oracle/users`      | oracle:read    | List profiles (search, page) |
| GET    | `/api/oracle/users/{id}` | oracle:read    | Get single profile           |
| PUT    | `/api/oracle/users/{id}` | oracle:write   | Partial update               |
| DELETE | `/api/oracle/users/{id}` | oracle:admin   | Soft-delete                  |
| GET    | `/api/oracle/audit`      | oracle:admin   | View audit log               |

### Database Tables

- **`users`** — System auth users (UUID id, username, password_hash via bcrypt, role, is_active)
- **`api_keys`** — API keys (UUID id, user_id FK, key_hash SHA-256, scopes comma-separated, rate_limit, expires_at, is_active)
- **`oracle_users`** — Oracle profiles (SERIAL id, name, name_persian, birthday DATE, mother_name, mother_name_persian, country, city, coordinates POINT, soft-delete via deleted_at)
- **`oracle_audit_log`** — Audit trail for Oracle operations (action, resource_type, resource_id, success, ip_address, api_key_hash, details JSONB)

### Existing Test Patterns (from `integration/tests/`)

- Tests use `api_client` fixture with `requests.Session` and legacy Bearer auth
- Test data names prefixed with `IntTest_` for cleanup via `autouse` fixture
- `conftest.py` provides: `db_engine`, `db_session_factory`, `db_session`, `db_connection`, `api_client`, `api_base_url`, `cleanup_test_data`
- Helper: `api_url(path)` builds full URL from `API_BASE_URL`
- Cleanup fixture deletes `oracle_users WHERE name LIKE 'IntTest%'` after each test

### Pydantic Models (from `api/app/models/oracle_user.py`)

- `OracleUserCreate`: name (str, 2-200), name_persian (optional), birthday (date, not future), mother_name (str, 1-200), mother_name_persian (optional), country (optional), city (optional)
- `OracleUserUpdate`: all fields optional, same validators
- `OracleUserResponse`: id, name, name_persian, birthday, mother_name, mother_name_persian, country, city, created_at, updated_at
- `OracleUserListResponse`: users (list), total, limit, offset

### Auth Models (from `api/app/models/auth.py`)

- `LoginRequest`: username (str), password (str)
- `TokenResponse`: access_token (str), token_type (str, default "bearer"), expires_in (int, seconds)
- `APIKeyCreate`: name (str), scopes (list[str]), expires_in_days (int, optional)
- `APIKeyResponse`: id, name, scopes, created_at, expires_at, last_used, is_active, key (optional, only on creation)

---

## FILES TO CREATE

- `integration/tests/test_auth_flow.py` — Authentication lifecycle integration tests (NEW, ~40 tests)
- `integration/tests/test_profile_flow.py` — Oracle profile CRUD integration tests (NEW, ~37 tests)

## FILES TO MODIFY

- `integration/tests/conftest.py` — Add auth-specific fixtures (user seeding, JWT helpers, role-specific clients, API key fixtures, profile fixtures with Persian data)

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Extend conftest.py with Auth & Profile Fixtures (~60 min)

**Tasks:**

1. Add helper function to create a test user in the `users` table directly via SQL:

   ```python
   def _create_test_system_user(
       db_session_factory, username: str, password: str, role: str
   ) -> dict:
       """Insert a user into the `users` table and return {id, username, password, role}.

       Uses ON CONFLICT to handle re-runs gracefully (upsert pattern).
       Password is bcrypt-hashed before storage.
       """
       import bcrypt as _bcrypt
       import uuid

       pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
       user_id = str(uuid.uuid4())
       session = db_session_factory()
       try:
           session.execute(text(
               "INSERT INTO users (id, username, password_hash, role, is_active) "
               "VALUES (:id, :username, :pw, :role, TRUE) "
               "ON CONFLICT (username) DO UPDATE SET password_hash = :pw, role = :role, is_active = TRUE"
           ), {"id": user_id, "username": username, "pw": pw_hash, "role": role})
           session.commit()
           row = session.execute(
               text("SELECT id FROM users WHERE username = :u"), {"u": username}
           ).fetchone()
           return {"id": row[0], "username": username, "password": password, "role": role}
       finally:
           session.close()
   ```

2. Add session-scoped fixtures for three test users (admin, regular user, readonly):

   ```python
   @pytest.fixture(scope="session")
   def admin_user(db_session_factory):
       """Create and return an admin-role test user."""
       return _create_test_system_user(db_session_factory, "IntTest_admin", "AdminPass123!", "admin")

   @pytest.fixture(scope="session")
   def regular_user(db_session_factory):
       """Create and return a user-role test user."""
       return _create_test_system_user(db_session_factory, "IntTest_user", "UserPass123!", "user")

   @pytest.fixture(scope="session")
   def readonly_user(db_session_factory):
       """Create and return a readonly-role test user."""
       return _create_test_system_user(db_session_factory, "IntTest_readonly", "ReadPass123!", "readonly")
   ```

3. Add helper function to obtain a JWT token via the login endpoint:

   ```python
   def _login(username: str, password: str) -> str:
       """Login via POST /api/auth/login and return the access_token string."""
       resp = requests.post(
           api_url("/api/auth/login"),
           json={"username": username, "password": password},
           timeout=10,
       )
       resp.raise_for_status()
       return resp.json()["access_token"]
   ```

4. Add fixtures for role-specific HTTP clients with JWT tokens:

   ```python
   @pytest.fixture(scope="session")
   def admin_jwt_client(admin_user):
       """HTTP client authenticated as admin via JWT."""
       token = _login(admin_user["username"], admin_user["password"])
       session = requests.Session()
       session.headers.update({
           "Authorization": f"Bearer {token}",
           "Content-Type": "application/json",
       })
       yield session
       session.close()

   @pytest.fixture(scope="session")
   def user_jwt_client(regular_user):
       """HTTP client authenticated as regular user via JWT."""
       token = _login(regular_user["username"], regular_user["password"])
       session = requests.Session()
       session.headers.update({
           "Authorization": f"Bearer {token}",
           "Content-Type": "application/json",
       })
       yield session
       session.close()

   @pytest.fixture(scope="session")
   def readonly_jwt_client(readonly_user):
       """HTTP client authenticated as readonly user via JWT."""
       token = _login(readonly_user["username"], readonly_user["password"])
       session = requests.Session()
       session.headers.update({
           "Authorization": f"Bearer {token}",
           "Content-Type": "application/json",
       })
       yield session
       session.close()

   @pytest.fixture
   def unauth_client():
       """HTTP client with NO authentication headers."""
       session = requests.Session()
       session.headers.update({"Content-Type": "application/json"})
       yield session
       session.close()
   ```

5. Add sample profile data constants with English and Persian data:

   ```python
   SAMPLE_PROFILE_EN = {
       "name": "IntTest_Alice",
       "birthday": "1990-05-15",
       "mother_name": "Sarah",
       "country": "US",
       "city": "New York",
   }

   SAMPLE_PROFILE_FA = {
       "name": "IntTest_Hamzeh",
       "name_persian": "\u062d\u0645\u0632\u0647",   # حمزه
       "birthday": "1988-03-21",
       "mother_name": "Fatemeh",
       "mother_name_persian": "\u0641\u0627\u0637\u0645\u0647",   # فاطمه
       "country": "Iran",
       "city": "Tehran",
   }

   SAMPLE_PROFILE_MIXED = {
       "name": "IntTest_Sara",
       "name_persian": "\u0633\u0627\u0631\u0627",   # سارا
       "birthday": "1995-11-30",
       "mother_name": "Maryam",
       "mother_name_persian": "\u0645\u0631\u06cc\u0645",   # مریم
       "country": "Iran",
       "city": "Isfahan",
   }
   ```

6. Add session-scoped cleanup fixture for test system users:

   ```python
   @pytest.fixture(autouse=True, scope="session")
   def cleanup_test_system_users(db_session_factory):
       """Delete test system users and their API keys after the entire test session."""
       yield
       session = db_session_factory()
       try:
           session.execute(text(
               "DELETE FROM api_keys WHERE user_id IN "
               "(SELECT id FROM users WHERE username LIKE 'IntTest_%')"
           ))
           session.execute(text("DELETE FROM users WHERE username LIKE 'IntTest_%'"))
           session.commit()
       except Exception:
           session.rollback()
       finally:
           session.close()
   ```

**Checkpoint:**

- [ ] `conftest.py` has `_create_test_system_user` helper function
- [ ] `conftest.py` has `admin_user`, `regular_user`, `readonly_user` fixtures (session-scoped)
- [ ] `conftest.py` has `_login` helper function
- [ ] `conftest.py` has `admin_jwt_client`, `user_jwt_client`, `readonly_jwt_client` fixtures (session-scoped)
- [ ] `conftest.py` has `unauth_client` fixture (function-scoped)
- [ ] `conftest.py` has `SAMPLE_PROFILE_EN`, `SAMPLE_PROFILE_FA`, `SAMPLE_PROFILE_MIXED` constants
- [ ] `conftest.py` has `cleanup_test_system_users` session-scoped autouse fixture
- [ ] Existing fixtures (`db_engine`, `db_session`, `api_client`, `cleanup_test_data`) remain unchanged and functional
- Verify: `python3 -c "import ast; ast.parse(open('integration/tests/conftest.py').read()); print('Syntax OK')"`

STOP if checkpoint fails.

---

### Phase 2: Auth Flow Tests — Login & Token Validation (~45 min)

**File:** `integration/tests/test_auth_flow.py`

**Tests to write:**

```python
@pytest.mark.auth
class TestLoginFlow:
    """Test POST /api/auth/login endpoint behavior across all scenarios."""

    def test_login_valid_admin(self, admin_user):
        """Valid admin credentials return JWT with access_token, token_type, expires_in."""

    def test_login_valid_user(self, regular_user):
        """Valid user credentials return JWT with user-level scopes."""

    def test_login_valid_readonly(self, readonly_user):
        """Valid readonly credentials return JWT with read-only scopes."""

    def test_login_wrong_password(self, admin_user):
        """Wrong password returns 401 with detail message."""

    def test_login_nonexistent_user(self):
        """Nonexistent username returns 401 (same as wrong password — no user enumeration)."""

    def test_login_empty_username(self):
        """Empty username returns 422."""

    def test_login_empty_password(self):
        """Empty password returns 422 or 401."""

    def test_login_missing_fields(self):
        """Empty JSON body returns 422."""

    def test_login_disabled_account(self, db_session_factory, regular_user):
        """Disabled account returns 403. Re-enables account in finally block."""

    def test_login_updates_last_login(self, db_session_factory, admin_user):
        """Successful login updates last_login timestamp in users table."""
```

Each test calls `requests.post(api_url("/api/auth/login"), json=...)` directly (login is unauthenticated). The `test_login_disabled_account` test must:

1. Set `is_active=False` in the DB
2. Attempt login and assert 403
3. Re-enable `is_active=True` in a `finally` block so other tests are not affected

**Test count at end of phase:** 10

**Checkpoint:**

- [ ] 10 test methods in `TestLoginFlow`
- [ ] Each test uses `requests.post` directly (not authenticated clients)
- [ ] Disabled account test has try/finally cleanup
- Verify: `grep -c "def test_" integration/tests/test_auth_flow.py` returns 10

STOP if checkpoint fails.

---

### Phase 3: Auth Flow Tests — API Key Lifecycle (~45 min)

**File:** `integration/tests/test_auth_flow.py` (continued)

**Tests to write:**

```python
@pytest.mark.auth
class TestAPIKeyFlow:
    """Test API key creation, usage, listing, and revocation."""

    def test_create_api_key(self, admin_jwt_client):
        """POST /api/auth/api-keys creates key and returns raw key value once."""

    def test_create_api_key_with_expiry(self, admin_jwt_client):
        """POST /api/auth/api-keys with expires_in_days sets correct expires_at."""

    def test_use_api_key_for_auth(self, admin_jwt_client):
        """Created API key can authenticate requests as Bearer token."""

    def test_list_api_keys(self, admin_jwt_client):
        """GET /api/auth/api-keys returns user's keys without raw key values."""

    def test_revoke_api_key(self, admin_jwt_client):
        """DELETE /api/auth/api-keys/{id} deactivates the key."""

    def test_revoked_key_cannot_authenticate(self, admin_jwt_client):
        """After revocation, using the key returns 403."""

    def test_api_key_updates_last_used(self, admin_jwt_client, db_session_factory):
        """Using an API key updates its last_used timestamp in the database."""
```

Key implementation details:

- `test_create_api_key`: POST to `/api/auth/api-keys` with `{"name": "IntTest_Key", "scopes": ["oracle:read"]}`, verify response has `id`, `name`, `scopes`, `key` (raw value), `created_at`
- `test_use_api_key_for_auth`: Create key, then make a separate request using only the raw key as Bearer token to GET `/api/oracle/users`, verify 200
- `test_revoked_key_cannot_authenticate`: Create key, save raw value, revoke via DELETE, then use raw value as Bearer -> 403
- `test_api_key_updates_last_used`: Create key, verify `last_used` is NULL in DB, use key, verify `last_used` is now set

**Test count at end of phase:** 17

**Checkpoint:**

- [ ] 7 test methods in `TestAPIKeyFlow`
- [ ] Tests create, use, list, and revoke keys entirely through the API
- [ ] No direct DB manipulation for key creation (only for verification)
- Verify: `grep -c "def test_" integration/tests/test_auth_flow.py` returns 17

STOP if checkpoint fails.

---

### Phase 4: Auth Flow Tests — Role-Based Access & Legacy Auth (~45 min)

**File:** `integration/tests/test_auth_flow.py` (continued)

**Tests to write:**

```python
@pytest.mark.auth
class TestRoleBasedAccess:
    """Test that role-based scope enforcement works across all endpoint types."""

    # --- Admin-only endpoints (oracle:admin) ---

    def test_admin_can_access_audit(self, admin_jwt_client):
        """Admin can GET /api/oracle/audit (requires oracle:admin)."""

    def test_user_cannot_access_audit(self, user_jwt_client):
        """Regular user gets 403 on GET /api/oracle/audit."""

    def test_readonly_cannot_access_audit(self, readonly_jwt_client):
        """Readonly user gets 403 on GET /api/oracle/audit."""

    def test_admin_can_delete_profile(self, admin_jwt_client):
        """Admin can DELETE /api/oracle/users/{id} (requires oracle:admin)."""

    def test_user_cannot_delete_profile(self, user_jwt_client, admin_jwt_client):
        """Regular user gets 403 on DELETE /api/oracle/users/{id}."""

    def test_readonly_cannot_delete_profile(self, readonly_jwt_client, admin_jwt_client):
        """Readonly user gets 403 on DELETE /api/oracle/users/{id}."""

    # --- Write endpoints (oracle:write) ---

    def test_admin_can_create_profile(self, admin_jwt_client):
        """Admin can POST /api/oracle/users (has oracle:write via hierarchy)."""

    def test_user_can_create_profile(self, user_jwt_client):
        """Regular user can POST /api/oracle/users (has oracle:write)."""

    def test_readonly_cannot_create_profile(self, readonly_jwt_client):
        """Readonly user gets 403 on POST /api/oracle/users (no oracle:write)."""

    # --- Read endpoints (oracle:read) ---

    def test_admin_can_list_profiles(self, admin_jwt_client):
        """Admin can GET /api/oracle/users."""

    def test_user_can_list_profiles(self, user_jwt_client):
        """Regular user can GET /api/oracle/users."""

    def test_readonly_can_list_profiles(self, readonly_jwt_client):
        """Readonly user can GET /api/oracle/users (has oracle:read)."""

    # --- Unauthenticated & invalid ---

    def test_unauthenticated_gets_401(self, unauth_client):
        """No auth header returns 401 on protected endpoints."""

    def test_invalid_token_gets_403(self):
        """Garbage Bearer token returns 403."""

    def test_legacy_api_secret_grants_admin(self, api_client):
        """Legacy Bearer <API_SECRET_KEY> grants full admin access (backward compat)."""
```

Key implementation details:

- For delete tests: admin creates a profile first, then the tested role attempts deletion
- `test_unauthenticated_gets_401`: Tests against multiple endpoints: GET `/api/oracle/users`, POST `/api/oracle/users`, GET `/api/oracle/audit`, POST `/api/oracle/reading`
- `test_legacy_api_secret_grants_admin`: Uses the existing `api_client` fixture (which uses legacy Bearer auth) to call the admin-only audit endpoint

**Test count at end of phase:** 32

**Checkpoint:**

- [ ] 15 test methods in `TestRoleBasedAccess` (including legacy auth test)
- [ ] Each test uses the correct client fixture for its role
- [ ] Delete permission tests create profile with admin first, then test with restricted role
- [ ] All test profile names start with `IntTest_`
- Verify: `grep -c "def test_" integration/tests/test_auth_flow.py` returns 32

STOP if checkpoint fails.

---

### Phase 5: Auth Flow Tests — Edge Cases (~30 min)

**File:** `integration/tests/test_auth_flow.py` (continued)

**Tests to write:**

```python
@pytest.mark.auth
class TestAuthEdgeCases:
    """Edge cases and security-focused auth scenarios."""

    def test_expired_jwt_rejected(self):
        """A manually crafted JWT with past expiration is rejected (403)."""

    def test_jwt_with_wrong_secret_rejected(self):
        """A JWT signed with a different secret is rejected (403)."""

    def test_jwt_with_tampered_role_rejected(self):
        """A JWT where the role was modified after signing is rejected (403)."""

    def test_api_key_with_restricted_scopes(self, admin_jwt_client):
        """API key with only oracle:read cannot access oracle:write endpoints."""

    def test_concurrent_sessions_isolated(self, admin_user, regular_user):
        """Two users logged in simultaneously have independent sessions."""

    def test_sql_injection_in_login(self):
        """SQL injection attempts in username are safely handled (returns 401)."""

    def test_very_long_credentials_handled(self):
        """Extremely long username/password return 422 or 401, not 500."""

    def test_api_key_scopes_expansion(self, admin_jwt_client):
        """API key with oracle:admin can access oracle:read endpoints (hierarchy)."""
```

Key implementation details:

- `test_expired_jwt_rejected`: Use `python-jose` to craft a JWT with `exp` in the past, signed with the correct `API_SECRET_KEY`, send as Bearer -> 403
- `test_jwt_with_wrong_secret_rejected`: Sign with a different key -> 403
- `test_jwt_with_tampered_role_rejected`: Craft token with `role: "admin"` but signed with wrong key -> 403
- `test_api_key_with_restricted_scopes`: Create key with `scopes=["oracle:read"]`, try POST `/api/oracle/users` -> 403, try GET `/api/oracle/users` -> 200
- `test_sql_injection_in_login`: Use `username="admin' OR '1'='1"` -> must return 401 (not 200 or 500)
- `test_api_key_scopes_expansion`: Create key with `scopes=["oracle:admin"]`, use to GET `/api/oracle/users` -> 200 (admin implies read)

**Test count at end of phase:** 40

**Checkpoint:**

- [ ] 8 test methods in `TestAuthEdgeCases`
- [ ] JWT crafting tests use `jose.jwt.encode` directly
- [ ] SQL injection test verifies the server does NOT crash (status != 500)
- [ ] No test relies on `time.sleep()` for synchronization
- Verify: `grep -c "def test_" integration/tests/test_auth_flow.py` returns 40

STOP if checkpoint fails.

---

### Phase 6: Profile Flow Tests — CRUD Operations (~60 min)

**File:** `integration/tests/test_profile_flow.py`

**Tests to write:**

```python
@pytest.mark.profile
class TestProfileCreate:
    """Test Oracle profile creation via POST /api/oracle/users."""

    def test_create_profile_minimal(self, admin_jwt_client):
        """Create with required fields only: name, birthday, mother_name. Returns 201."""

    def test_create_profile_full_english(self, admin_jwt_client):
        """Create with all English fields including country and city. Returns 201."""

    def test_create_profile_full_persian(self, admin_jwt_client):
        """Create with Persian name_persian and mother_name_persian. Returns 201."""

    def test_create_profile_mixed_en_fa(self, admin_jwt_client):
        """Create with both English and Persian fields. Returns 201."""

    def test_create_duplicate_rejected(self, admin_jwt_client):
        """Same name+birthday for active profile returns 409."""

    def test_create_with_future_birthday_rejected(self, admin_jwt_client):
        """Birthday in the future returns 422."""

    def test_create_with_short_name_rejected(self, admin_jwt_client):
        """Name shorter than 2 characters returns 422."""

    def test_create_with_invalid_date_rejected(self, admin_jwt_client):
        """Non-date birthday string returns 422."""


@pytest.mark.profile
class TestProfileRead:
    """Test Oracle profile retrieval endpoints."""

    def test_get_profile_by_id(self, admin_jwt_client):
        """GET /api/oracle/users/{id} returns correct profile with all fields."""

    def test_get_nonexistent_profile_returns_404(self, admin_jwt_client):
        """GET /api/oracle/users/999999 returns 404."""

    def test_list_profiles(self, admin_jwt_client):
        """GET /api/oracle/users returns paginated list with total, limit, offset."""

    def test_list_profiles_with_search(self, admin_jwt_client):
        """GET /api/oracle/users?search=<name> filters results by name match."""

    def test_list_profiles_pagination(self, admin_jwt_client):
        """GET /api/oracle/users?limit=1&offset=0 returns exactly 1 result."""

    def test_search_by_persian_name(self, admin_jwt_client):
        """GET /api/oracle/users?search=<persian_text> finds Persian-named profiles."""


@pytest.mark.profile
class TestProfileUpdate:
    """Test Oracle profile updates via PUT /api/oracle/users/{id}."""

    def test_update_single_field(self, admin_jwt_client):
        """PUT with one field updates only that field, others unchanged."""

    def test_update_multiple_fields(self, admin_jwt_client):
        """PUT with multiple fields updates all of them."""

    def test_update_persian_fields(self, admin_jwt_client):
        """PUT with Persian name_persian/mother_name_persian works."""

    def test_update_nonexistent_profile_returns_404(self, admin_jwt_client):
        """PUT /api/oracle/users/999999 returns 404."""

    def test_update_empty_body_returns_400(self, admin_jwt_client):
        """PUT with no fields returns 400."""

    def test_update_name_to_duplicate_returns_409(self, admin_jwt_client):
        """Changing name+birthday to match existing active profile returns 409."""


@pytest.mark.profile
class TestProfileDelete:
    """Test Oracle profile soft-delete via DELETE /api/oracle/users/{id}."""

    def test_delete_profile(self, admin_jwt_client):
        """DELETE soft-deletes the profile (sets deleted_at). Returns 200."""

    def test_deleted_profile_not_in_list(self, admin_jwt_client):
        """After DELETE, profile does not appear in GET /api/oracle/users."""

    def test_deleted_profile_returns_404_on_get(self, admin_jwt_client):
        """After DELETE, GET /api/oracle/users/{id} returns 404."""

    def test_deleted_profile_returns_404_on_update(self, admin_jwt_client):
        """After DELETE, PUT /api/oracle/users/{id} returns 404."""

    def test_recreate_after_soft_delete(self, admin_jwt_client):
        """Same name+birthday can be re-created after soft-delete (new ID)."""

    def test_delete_nonexistent_returns_404(self, admin_jwt_client):
        """DELETE /api/oracle/users/999999 returns 404."""
```

Key implementation details:

- Each test that needs a profile creates one first via POST, then operates on it
- `test_create_duplicate_rejected`: Create profile, then try to create same name+birthday -> 409
- `test_list_profiles_with_search`: Create profile with unique name, search for it, verify it appears and total is correct
- `test_update_name_to_duplicate_returns_409`: Create profiles A and B, update B's name+birthday to match A -> 409
- `test_recreate_after_soft_delete`: Create, delete, create again with same payload -> 201 with different ID

**Test count in profile file:** 26

**Checkpoint:**

- [ ] `TestProfileCreate` has 8 tests
- [ ] `TestProfileRead` has 6 tests
- [ ] `TestProfileUpdate` has 6 tests
- [ ] `TestProfileDelete` has 6 tests
- [ ] All profile names start with `IntTest_`
- Verify: `grep -c "def test_" integration/tests/test_profile_flow.py` returns 26

STOP if checkpoint fails.

---

### Phase 7: Profile Flow Tests — Persian Data & Encryption (~45 min)

**File:** `integration/tests/test_profile_flow.py` (continued)

**Tests to write:**

```python
@pytest.mark.profile
@pytest.mark.persian
class TestPersianDataHandling:
    """Verify Persian/Farsi UTF-8 text handling across the full stack."""

    def test_persian_name_roundtrip(self, admin_jwt_client):
        """Persian name_persian survives create -> get -> compare."""

    def test_persian_mother_name_roundtrip(self, admin_jwt_client):
        """Persian mother_name_persian survives create -> get -> compare."""

    def test_persian_in_list_response(self, admin_jwt_client):
        """Persian fields appear correctly in list endpoint response."""

    def test_persian_search_finds_profile(self, admin_jwt_client):
        """Search by partial Persian name finds the profile."""

    def test_persian_update_roundtrip(self, admin_jwt_client):
        """Update name_persian from None to Persian value, verify change persists."""

    def test_mixed_script_name(self, admin_jwt_client):
        """Profile with Latin name and Persian name_persian both returned correctly."""

    def test_long_persian_name(self, admin_jwt_client):
        """Persian name up to 100 characters works (well within VARCHAR 200 limit)."""


@pytest.mark.profile
class TestProfileEncryption:
    """Verify encryption at rest for sensitive profile fields."""

    def test_mother_name_encrypted_in_db(self, admin_jwt_client, db_connection):
        """mother_name stored with ENC4: prefix in DB when encryption is configured."""

    def test_mother_name_persian_encrypted_in_db(self, admin_jwt_client, db_connection):
        """mother_name_persian stored with ENC4: prefix in DB when encryption is configured."""

    def test_api_returns_decrypted_values(self, admin_jwt_client):
        """API response always returns plaintext (decrypted) mother_name values."""

    def test_encrypted_persian_roundtrip(self, admin_jwt_client, db_connection):
        """Persian mother_name_persian encrypts and decrypts correctly through full stack."""
```

Key implementation details:

- `test_persian_name_roundtrip`: Create with `name_persian="حمزه"`, GET by ID, assert `response["name_persian"] == "حمزه"`
- `test_persian_search_finds_profile`: Create with `name_persian="سارا"`, search with `?search=سار`, verify profile appears in results
- `test_persian_update_roundtrip`: Create English-only profile, PUT with `{"name_persian": "مریم"}`, GET, verify `name_persian == "مریم"`
- `test_long_persian_name`: Create with `name_persian="آ" * 100` (100 Persian characters), verify round-trip
- Encryption tests: If `NPS_ENCRYPTION_KEY` is not set, use `pytest.skip("Encryption not configured")` for ENC4 assertions, but plaintext tests always run
- `test_encrypted_persian_roundtrip`: Create with `mother_name_persian="زهرا"`, query DB directly for raw value (should start with `ENC4:` if encryption enabled), then GET via API and verify `"زهرا"` returned

**Test count in profile file:** 37 (26 + 11)

**Checkpoint:**

- [ ] `TestPersianDataHandling` has 7 tests
- [ ] `TestProfileEncryption` has 4 tests
- [ ] Persian tests use actual Persian characters in assertions
- [ ] Encryption tests handle both encrypted and non-encrypted environments gracefully
- [ ] All test data names start with `IntTest_`
- Verify: `grep -c "def test_" integration/tests/test_profile_flow.py` returns 37

STOP if checkpoint fails.

---

### Phase 8: Test Execution & Verification (~30 min)

**Tasks:**

1. Run all new auth flow tests:

   ```bash
   python3 -m pytest integration/tests/test_auth_flow.py -v -s --tb=short 2>&1 | tail -60
   ```

2. Run all new profile flow tests:

   ```bash
   python3 -m pytest integration/tests/test_profile_flow.py -v -s --tb=short 2>&1 | tail -60
   ```

3. Run all integration tests together to verify no regressions:

   ```bash
   python3 -m pytest integration/tests/ -v --tb=short 2>&1 | tail -80
   ```

4. Fix any failures using the 3-strike rule (attempt fix silently up to 3 times, then report)

5. Run linters:

   ```bash
   python3 -m ruff check integration/tests/test_auth_flow.py integration/tests/test_profile_flow.py integration/tests/conftest.py
   python3 -m black --check integration/tests/test_auth_flow.py integration/tests/test_profile_flow.py integration/tests/conftest.py
   ```

6. Record pass/fail counts

**Checkpoint:**

- [ ] `test_auth_flow.py` — all 40 tests pass
- [ ] `test_profile_flow.py` — all 37 tests pass
- [ ] Existing integration tests (56+) still pass — no regressions
- [ ] Total integration test count is now 130+ (56 existing + 77 new)
- [ ] Linters pass with no errors
- Verify: `python3 -m pytest integration/tests/ --co -q 2>&1 | tail -5` shows total test count

STOP if checkpoint fails.

---

## TESTS SUMMARY

### test_auth_flow.py (40 tests)

| Class               | Count | Focus                                               |
| ------------------- | ----- | --------------------------------------------------- |
| TestLoginFlow       | 10    | Login success/failure, disabled accounts, timing    |
| TestAPIKeyFlow      | 7     | Key CRUD, auth via key, revocation, last_used       |
| TestRoleBasedAccess | 15    | Admin/user/readonly on create, delete, audit, list  |
| TestAuthEdgeCases   | 8     | Expired JWT, injection, scope expansion, edge cases |

### test_profile_flow.py (37 tests)

| Class                   | Count | Focus                                          |
| ----------------------- | ----- | ---------------------------------------------- |
| TestProfileCreate       | 8     | Valid/invalid creation, duplicates, validation |
| TestProfileRead         | 6     | Get by ID, list, search, pagination, Persian   |
| TestProfileUpdate       | 6     | Partial update, duplicates, empty body, 404    |
| TestProfileDelete       | 6     | Soft-delete, re-creation, 404 cases            |
| TestPersianDataHandling | 7     | UTF-8 round-trip, search, mixed scripts        |
| TestProfileEncryption   | 4     | ENC4: prefix, decrypt on read, Persian crypto  |

### conftest.py Additions

| Fixture/Helper              | Scope    | Purpose                                    |
| --------------------------- | -------- | ------------------------------------------ |
| `_create_test_system_user`  | Helper   | Insert user into `users` table with bcrypt |
| `_login`                    | Helper   | Login via API and return JWT token         |
| `admin_user`                | Session  | Admin user credentials dict                |
| `regular_user`              | Session  | Regular user credentials dict              |
| `readonly_user`             | Session  | Readonly user credentials dict             |
| `admin_jwt_client`          | Session  | requests.Session with admin JWT            |
| `user_jwt_client`           | Session  | requests.Session with user JWT             |
| `readonly_jwt_client`       | Session  | requests.Session with readonly JWT         |
| `unauth_client`             | Function | requests.Session with no auth              |
| `SAMPLE_PROFILE_EN`         | Constant | English-only profile data                  |
| `SAMPLE_PROFILE_FA`         | Constant | Persian profile data                       |
| `SAMPLE_PROFILE_MIXED`      | Constant | Mixed English + Persian profile data       |
| `cleanup_test_system_users` | Session  | Cleanup `users` and `api_keys` after tests |

---

## ACCEPTANCE CRITERIA

1. [ ] `integration/tests/test_auth_flow.py` exists and contains 40 test methods
2. [ ] `integration/tests/test_profile_flow.py` exists and contains 37 test methods
3. [ ] `integration/tests/conftest.py` has 13+ new fixtures/helpers added
4. [ ] All 77 new tests pass against a running PostgreSQL + API stack
5. [ ] All 56+ existing integration tests still pass (zero regressions)
6. [ ] Login flow covers: valid login (3 roles), wrong password, nonexistent user, disabled account, empty fields, last_login update
7. [ ] API key flow covers: create, create with expiry, use for auth, list, revoke, revoked key rejected, last_used update
8. [ ] Role access covers: admin/user/readonly on create, delete, audit endpoints; unauthenticated 401; invalid token 403; legacy fallback
9. [ ] Profile CRUD covers: create (minimal, full EN, full FA, mixed), read (by ID, list, search, pagination, Persian search), update (single, multiple, Persian, 404, 400, 409), delete (soft, list exclusion, 404, re-create)
10. [ ] Persian UTF-8 tests verify round-trip for: name_persian, mother_name_persian, search by Persian text, update to Persian, mixed script, long Persian string
11. [ ] Encryption tests verify: mother_name has ENC4: prefix in DB (when encryption enabled), API returns plaintext, Persian encryption round-trip
12. [ ] Edge case tests cover: expired JWT, wrong secret, tampered JWT, restricted API key scopes, SQL injection in login, long credentials, scope expansion
13. [ ] All test profile names start with `IntTest_` for automated cleanup
14. [ ] No test uses `time.sleep()` for synchronization
15. [ ] Test files have proper module docstrings and class docstrings
16. [ ] `ruff check` and `black --check` pass on all new/modified test files
17. [ ] No bare `except:` in any test file

- Verify:
  ```bash
  test -f integration/tests/test_auth_flow.py && \
  test -f integration/tests/test_profile_flow.py && \
  python3 -c "
  import ast
  for f in ['integration/tests/test_auth_flow.py', 'integration/tests/test_profile_flow.py', 'integration/tests/conftest.py']:
      ast.parse(open(f).read())
  print('ALL SYNTAX OK')
  " && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                    | Expected Behavior                                                             | Recovery                                                                  |
| ------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| API server not running                      | All tests fail with `ConnectionError`. Prerequisite check catches this early  | Start API: `make dev-api` or `cd api && uvicorn app.main:app --port 8000` |
| PostgreSQL not running                      | DB fixtures fail on connect. Login tests fail                                 | Start DB: `docker-compose up -d postgres`                                 |
| `API_SECRET_KEY` not set in `.env`          | Legacy auth fixture fails. JWT creation uses default key                      | Set `API_SECRET_KEY` in `.env`                                            |
| `NPS_ENCRYPTION_KEY` not set                | Encryption tests skip ENC4: assertions; plaintext tests still pass            | Tests use `pytest.skip()` for encryption-specific checks                  |
| Test run interrupted (Ctrl+C)               | Cleanup fixtures may not execute. Test data remains in DB                     | Manual: `DELETE FROM users WHERE username LIKE 'IntTest_%'`               |
| Concurrent test runs                        | `IntTest_` prefix collision possible                                          | Add UUID suffixes to names if concurrent runs are needed                  |
| `python-jose` not installed                 | JWT crafting edge case tests fail on import                                   | `pip install python-jose[cryptography]`                                   |
| `bcrypt` version incompatibility            | User seeding fails on `hashpw`                                                | `pip install bcrypt>=4.0.0`                                               |
| Profile creation returns 500                | Indicates API/DB issue, not test issue                                        | Check API logs: `docker-compose logs api`                                 |
| Persian text mojibake (encoding corruption) | Test assertion catches it: expected `"حمزه"` vs actual garbled text           | Check PostgreSQL encoding: `SHOW server_encoding;` (should be `UTF8`)     |
| JWT token expired during long test run      | Session-scoped client tokens expire after `jwt_expire_minutes` (default 1440) | Increase `JWT_EXPIRE_MINUTES` in `.env` or use function-scoped clients    |

---

## HANDOFF

**Created:**

- `integration/tests/test_auth_flow.py` — 40 integration tests for authentication flows
- `integration/tests/test_profile_flow.py` — 37 integration tests for Oracle profile flows

**Modified:**

- `integration/tests/conftest.py` — 13+ new fixtures and helpers for auth/profile testing

**Test metrics:**

- New tests: 77
- Existing tests: 56+ (unchanged)
- Total integration tests: 130+

**Next session needs:**

- **Session 42 (Integration Tests: Readings & Calculations)** depends on:
  - Auth fixtures from this session (`admin_jwt_client`, `user_jwt_client`, `readonly_jwt_client`) for testing reading endpoints with different roles
  - Profile fixtures (`SAMPLE_PROFILE_EN`, `SAMPLE_PROFILE_FA`) for creating profiles before reading tests
  - `_login` helper for generating fresh tokens if needed
  - Pattern established here: test classes grouped by feature, `IntTest_` naming, Persian verification approach
  - Verify Session 41 tests still pass before adding Session 42 tests (regression check)
- **Session 43 (Integration Tests: End-to-End Flows)** depends on:
  - All fixtures from Sessions 41-42
  - Complete coverage of auth + profiles + readings to compose end-to-end scenarios
- **Session 44 (Performance & Load Testing)** may reuse:
  - `_login` helper for generating auth tokens under load
  - `_create_test_system_user` for provisioning test users
  - Session-scoped client pattern for persistent connections
