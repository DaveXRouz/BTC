# SPEC: API Oracle User Management - T2-S1
**Estimated Duration:** 3-4 hours  
**Layer:** Layer 2 (API)  
**Terminal:** Terminal 2  
**Session:** T2-S1  
**Dependencies:** 
- Terminal 4 (Database: `oracle_users` table schema)
- Terminal 6 (Security: encryption + API key auth middleware)

---

## 🎯 TL;DR

- Creating 5 REST API endpoints for Oracle user profile management (CRUD)
- Pydantic models for strict request/response validation
- SQLAlchemy ORM for database operations with encryption
- API key authentication + audit logging for all operations
- Comprehensive testing with 95%+ coverage target
- Pagination, filtering, and soft delete support
- OpenAPI documentation auto-generated

---

## 📋 OBJECTIVE

Build production-ready FastAPI endpoints for managing Oracle user profiles with security, validation, error handling, and comprehensive testing. Users store personal information (name, birthday, questions) for Oracle readings.

---

## 🔍 CONTEXT

**Current State:**
- Terminal 4 (Database) has `oracle_users` table schema (assumed complete)
- Terminal 6 (Security) has encryption utilities and API key middleware (assumed complete)
- No API endpoints for user management exist yet

**What's Changing:**
- Creating 5 new endpoints in `api/app/routers/oracle.py` (user management section)
- Creating Pydantic models in `api/app/models/oracle.py`
- Creating service layer in `api/app/services/oracle_service.py`
- Creating SQLAlchemy ORM model in `api/app/database/models.py`
- Creating comprehensive tests in `api/tests/test_oracle_users.py`

**Why:**
Oracle readings require user profiles (name, birthday) for accurate FC60 and numerology calculations. This API allows frontend to manage these profiles securely.

---

## ✅ PREREQUISITES

**Before starting, verify these are complete:**

- [ ] Database Layer (Terminal 4)
  - `oracle_users` table exists in PostgreSQL
  - Columns: `id`, `name`, `birthday`, `created_at`, `updated_at`, `deleted_at`
  - Indexes on `id` and `created_at`
  - Verification: `psql -c "\d oracle_users"`

- [ ] Security Layer (Terminal 6)
  - API key middleware exists at `api/app/security/auth.py`
  - Encryption utilities exist at `api/app/security/encryption.py`
  - Functions: `encrypt_field(value)`, `decrypt_field(encrypted_value)`
  - Verification: `python -c "from app.security.encryption import encrypt_field; print(encrypt_field('test'))"`

- [ ] Environment Setup
  - Python 3.11+ installed: `python --version`
  - Virtual environment active: `which python` (should show venv path)
  - PostgreSQL running: `psql -c "SELECT 1"`
  - Required packages installed: `pip list | grep fastapi`

---

## 🛠️ TOOLS TO USE

**Extended Thinking (for these decisions):**
1. Soft delete vs hard delete strategy (preserving Oracle reading history)
2. Pagination approach (offset-based vs cursor-based for performance)
3. Encryption scope (which fields need encryption vs plain storage)
4. Error response standardization (consistent format across all endpoints)

**Subagents (parallel execution):**
- Subagent 1: Pydantic models + SQLAlchemy ORM (independent)
- Subagent 2: Service layer business logic (depends on Subagent 1)
- Subagent 3: API route handlers (depends on Subagent 2)
- Subagent 4: Comprehensive tests (depends on Subagent 3)

**Skills to read first:**
- `view /mnt/skills/public/product-self-knowledge/SKILL.md` (FastAPI best practices)

---

## 📐 REQUIREMENTS

### Functional Requirements

**FR1: Create User Profile**
- Endpoint: `POST /api/oracle/users`
- Input: Name (string, 1-100 chars), Birthday (date, YYYY-MM-DD), Optional notes
- Output: User ID, created user object
- Validation: Name required, birthday valid date (not future), unique constraint on name+birthday

**FR2: List User Profiles**
- Endpoint: `GET /api/oracle/users?page=1&limit=20&sort=created_at&order=desc`
- Input: Query params (page, limit, sort field, order)
- Output: Paginated list of users, total count, page metadata
- Business rule: Default limit 20, max limit 100, soft-deleted users excluded

**FR3: Get User Profile**
- Endpoint: `GET /api/oracle/users/{id}`
- Input: User ID (UUID or integer)
- Output: Full user object with decrypted sensitive fields
- Error: 404 if user not found or soft-deleted

**FR4: Update User Profile**
- Endpoint: `PUT /api/oracle/users/{id}`
- Input: User ID, fields to update (name, birthday, notes)
- Output: Updated user object
- Business rule: At least one field must be provided, name+birthday uniqueness enforced

**FR5: Delete User Profile**
- Endpoint: `DELETE /api/oracle/users/{id}`
- Input: User ID
- Output: Success message
- Business rule: Soft delete (set `deleted_at` timestamp), preserve data for Oracle history

### Non-Functional Requirements

**NFR1: Performance**
- Response time: <50ms p95 for all endpoints
- Database queries optimized: Use indexes, no N+1 queries
- Connection pooling: SQLAlchemy async session management

**NFR2: Security**
- Authentication: All endpoints require valid API key (scope: `oracle_read` or `admin`)
- Encryption: Birthday field encrypted before database storage
- Audit logging: All create/update/delete operations logged with user ID, action, timestamp
- Input validation: Pydantic strict mode, XSS protection

**NFR3: Quality**
- Test coverage: 95%+ for all new code
- Type hints: mypy strict mode compliance
- Documentation: OpenAPI schema with examples for all endpoints
- Error handling: Consistent error response format with error codes

---

## 🔧 IMPLEMENTATION PLAN

### PHASE 1: Extended Thinking - Design Decisions (Duration: 30 min)

**Tasks:**

1. **Decision: Soft Delete vs Hard Delete**
   ```
   <extended_thinking>
   DECISION: Should DELETE endpoint perform soft delete or hard delete?
   
   OPTIONS:
   1. Hard Delete - Permanently remove user from database
      - Pros: Clean database, no orphaned data
      - Cons: Loses Oracle reading history, can't restore accidentally deleted users
   
   2. Soft Delete - Set deleted_at timestamp, filter in queries
      - Pros: Preserves Oracle reading history, allows "undelete" feature, audit trail
      - Cons: Database grows over time, slightly more complex queries
   
   CONTEXT:
   - Oracle readings reference user profiles for historical analysis
   - Users might accidentally delete profiles
   - Compliance may require data retention
   
   EVALUATION:
   - Historical Integrity: Soft delete preserves Oracle reading context
   - User Experience: Soft delete allows recovery from mistakes
   - Performance: Negligible impact with proper indexing
   - Compliance: Soft delete better for audit requirements
   
   RECOMMENDATION: Soft Delete
   - Implement `deleted_at` timestamp column
   - All queries add `WHERE deleted_at IS NULL` filter
   - Consider background job to hard-delete after 90 days if needed
   </extended_thinking>
   ```

2. **Decision: Pagination Strategy**
   ```
   <extended_thinking>
   DECISION: Offset-based vs Cursor-based pagination?
   
   OPTIONS:
   1. Offset-based (LIMIT/OFFSET)
      - Pros: Simple to implement, standard pattern, allows jumping to page N
      - Cons: Slow for large offsets, inconsistent results if data changes during pagination
   
   2. Cursor-based (WHERE id > last_id)
      - Pros: Consistent performance, handles concurrent updates better
      - Cons: Can't jump to arbitrary page, more complex for sorting
   
   CONTEXT:
   - Expected dataset: <10,000 users per deployment (small to medium)
   - Access pattern: Most recent users viewed first
   - Concurrent updates: Low frequency
   
   EVALUATION:
   - Dataset Size: Small enough that offset performance is acceptable
   - UX Requirement: Users expect page numbers (jump to page 5)
   - Implementation Complexity: Offset much simpler
   - Consistency: Low update frequency means offset inconsistency is rare
   
   RECOMMENDATION: Offset-based
   - Use `LIMIT` and `OFFSET` with `created_at DESC` default sort
   - Add index on `created_at` for performance
   - Document that page contents may shift if data changes
   </extended_thinking>
   ```

3. **Decision: Encryption Scope**
   ```
   <extended_thinking>
   DECISION: Which user fields need encryption?
   
   FIELDS:
   - id: No (public identifier)
   - name: ? (PII, but used for display)
   - birthday: ? (PII, used for calculations)
   - notes: ? (potentially sensitive user input)
   - created_at/updated_at/deleted_at: No (metadata)
   
   EVALUATION:
   Birthday:
   - Sensitivity: High (PII, can identify person)
   - Usage: Frequent (every Oracle reading calculation)
   - Recommendation: ENCRYPT (AES-256)
   
   Name:
   - Sensitivity: Medium (PII, but less identifying than birthday)
   - Usage: Very frequent (displayed in UI, Oracle readings)
   - Trade-off: Encryption prevents database-level name search
   - Recommendation: PLAIN TEXT (accept trade-off for UX)
   
   Notes:
   - Sensitivity: Variable (user-provided text)
   - Usage: Rare (optional field)
   - Recommendation: ENCRYPT (low performance impact, high security)
   
   DECISION: Encrypt birthday + notes, plain text for name
   </extended_thinking>
   ```

4. **Decision: Error Response Format**
   ```
   <extended_thinking>
   DECISION: Standardize error response structure
   
   GOAL: Consistent error format for frontend parsing
   
   FORMAT:
   {
     "error": {
       "code": "USER_NOT_FOUND",
       "message": "User with ID 123 does not exist",
       "details": null,
       "timestamp": "2026-02-08T10:30:00Z"
     }
   }
   
   ERROR CODES:
   - USER_NOT_FOUND (404)
   - USER_ALREADY_EXISTS (400)
   - INVALID_INPUT (400)
   - UNAUTHORIZED (401)
   - FORBIDDEN (403)
   - INTERNAL_ERROR (500)
   
   IMPLEMENTATION:
   - Create custom exception handler in main.py
   - All endpoints use HTTPException with custom detail dict
   - Pydantic validation errors auto-formatted to match
   </extended_thinking>
   ```

**Checkpoint:**
- [ ] All 4 design decisions documented with reasoning
- [ ] Trade-offs clearly understood
- [ ] Implementation approach defined

**STOP if checkpoint fails** - Review decisions before proceeding

---

### PHASE 2: Data Models (Duration: 45 min)

**Subagent 1: Pydantic + SQLAlchemy Models**

**Tasks:**

1. **Create Pydantic Request/Response Models**
   
   File: `api/app/models/oracle.py`
   
   Models to create:
   ```python
   # Request Models
   - UserCreateRequest: name, birthday, notes (optional)
   - UserUpdateRequest: name (optional), birthday (optional), notes (optional)
   - UserListQueryParams: page, limit, sort, order
   
   # Response Models
   - UserResponse: id, name, birthday, notes, created_at, updated_at
   - UserListResponse: users[], total, page, limit, has_more
   - UserDeleteResponse: success, message
   ```
   
   **Requirements:**
   - Use Pydantic v2 syntax (`Field`, `ConfigDict`)
   - Birthday validation: Must be valid date, not in future
   - Name validation: 1-100 chars, no leading/trailing whitespace
   - Limit validation: 1-100, default 20
   - Include OpenAPI examples for each model

2. **Create SQLAlchemy ORM Model**
   
   File: `api/app/database/models.py` (add to existing)
   
   ```python
   class OracleUser(Base):
       __tablename__ = "oracle_users"
       
       id = Column(Integer, primary_key=True)
       name = Column(String(100), nullable=False)
       birthday_encrypted = Column(Text, nullable=False)
       notes_encrypted = Column(Text, nullable=True)
       created_at = Column(DateTime, default=func.now())
       updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
       deleted_at = Column(DateTime, nullable=True)
       
       # Indexes
       __table_args__ = (
           Index('ix_oracle_users_created_at', 'created_at'),
           Index('ix_oracle_users_deleted_at', 'deleted_at'),
           UniqueConstraint('name', 'birthday_encrypted', name='uq_name_birthday'),
       )
   ```
   
   **Requirements:**
   - Async SQLAlchemy session support
   - Proper indexing for performance
   - Soft delete support (deleted_at column)

**Verification:**
```bash
cd api

# Test Pydantic models
python -c "from app.models.oracle import UserCreateRequest; u = UserCreateRequest(name='Test', birthday='1990-01-01'); print(u)"

# Test SQLAlchemy model
python -c "from app.database.models import OracleUser; print(OracleUser.__tablename__)"

# Mypy type check
mypy app/models/oracle.py --strict
# Expected: No errors
```

**Checkpoint:**
- [ ] Pydantic models validate correctly (test with valid + invalid inputs)
- [ ] SQLAlchemy model matches database schema
- [ ] Type hints pass mypy strict check
- [ ] OpenAPI examples included in Pydantic models

**STOP if checkpoint fails** - Fix models before service layer

---

### PHASE 3: Service Layer (Duration: 60 min)

**Subagent 2: Business Logic**

**Tasks:**

1. **Create Oracle User Service**
   
   File: `api/app/services/oracle_service.py`
   
   Functions to implement:
   ```python
   async def create_user(db: AsyncSession, user_data: UserCreateRequest) -> OracleUser
   async def list_users(db: AsyncSession, query: UserListQueryParams) -> UserListResponse
   async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[OracleUser]
   async def update_user(db: AsyncSession, user_id: int, updates: UserUpdateRequest) -> OracleUser
   async def delete_user(db: AsyncSession, user_id: int) -> bool
   ```
   
   **Requirements:**
   - Encryption/decryption integration (from Terminal 6)
   - Soft delete logic (set deleted_at, don't remove from DB)
   - Duplicate check (name + birthday uniqueness)
   - Pagination logic (offset-based)
   - Error handling (raise custom exceptions)
   - Audit logging (log all CUD operations)

2. **Integration with Security Layer**
   
   ```python
   from app.security.encryption import encrypt_field, decrypt_field
   
   # Before saving to DB
   birthday_encrypted = encrypt_field(user_data.birthday)
   notes_encrypted = encrypt_field(user_data.notes) if user_data.notes else None
   
   # After retrieving from DB
   birthday = decrypt_field(user.birthday_encrypted)
   notes = decrypt_field(user.notes_encrypted) if user.notes_encrypted else None
   ```

3. **Audit Logging**
   
   ```python
   import logging
   logger = logging.getLogger(__name__)
   
   # After create
   logger.info("User created", extra={
       "user_id": user.id,
       "action": "create",
       "timestamp": datetime.utcnow().isoformat()
   })
   ```

**Verification:**
```bash
cd api

# Run service layer tests (create these in parallel)
pytest tests/test_oracle_service.py -v

# Expected: All service layer functions work
# - create_user: Creates with encrypted birthday
# - list_users: Returns paginated results
# - get_user_by_id: Returns decrypted user or None
# - update_user: Updates and re-encrypts fields
# - delete_user: Soft deletes (sets deleted_at)
```

**Checkpoint:**
- [ ] All 5 service functions implemented
- [ ] Encryption/decryption works (test roundtrip)
- [ ] Soft delete works (deleted users not in list)
- [ ] Duplicate check prevents name+birthday collision
- [ ] Audit logs written for CUD operations
- [ ] Unit tests pass (mock database)

**STOP if checkpoint fails** - Fix service layer before routes

---

### PHASE 4: API Routes (Duration: 60 min)

**Subagent 3: FastAPI Endpoint Handlers**

**Tasks:**

1. **Create Router**
   
   File: `api/app/routers/oracle.py` (add user management section)
   
   Endpoints to implement:
   ```python
   router = APIRouter(prefix="/api/oracle", tags=["Oracle User Management"])
   
   @router.post("/users", response_model=UserResponse, status_code=201)
   @router.get("/users", response_model=UserListResponse)
   @router.get("/users/{user_id}", response_model=UserResponse)
   @router.put("/users/{user_id}", response_model=UserResponse)
   @router.delete("/users/{user_id}", response_model=UserDeleteResponse)
   ```
   
   **Requirements:**
   - API key authentication on all endpoints (`dependencies=[Depends(validate_api_key)]`)
   - Proper HTTP status codes (201, 200, 404, 400, 500)
   - HTTPException for errors
   - OpenAPI documentation (docstrings, examples)
   - Async handlers

2. **Endpoint Implementation Example (POST /users)**
   
   ```python
   from fastapi import Depends, HTTPException, status
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.database.connection import get_db
   from app.security.auth import validate_api_key
   from app.services.oracle_service import create_user, UserAlreadyExistsError
   
   @router.post(
       "/users",
       response_model=UserResponse,
       status_code=status.HTTP_201_CREATED,
       summary="Create new Oracle user profile",
       description="Creates a new user profile for Oracle readings with encrypted birthday",
       dependencies=[Depends(validate_api_key)]
   )
   async def create_oracle_user(
       user_data: UserCreateRequest,
       db: AsyncSession = Depends(get_db)
   ):
       """
       Create a new Oracle user profile.
       
       Args:
           user_data: User information (name, birthday, optional notes)
           db: Database session
       
       Returns:
           UserResponse: Created user object
       
       Raises:
           400: User with same name+birthday already exists
           401: Invalid or missing API key
           500: Internal server error
       """
       try:
           user = await create_user(db, user_data)
           return UserResponse.from_orm(user)
       except UserAlreadyExistsError:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail={
                   "error": {
                       "code": "USER_ALREADY_EXISTS",
                       "message": f"User with name '{user_data.name}' and birthday already exists",
                       "timestamp": datetime.utcnow().isoformat()
                   }
               }
           )
       except Exception as e:
           logger.error("Failed to create user", exc_info=True)
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail={
                   "error": {
                       "code": "INTERNAL_ERROR",
                       "message": "Failed to create user",
                       "timestamp": datetime.utcnow().isoformat()
                   }
               }
           )
   ```

3. **Register Router in Main App**
   
   File: `api/app/main.py`
   
   ```python
   from app.routers import oracle
   app.include_router(oracle.router)
   ```

**Verification:**
```bash
cd api

# Start API server
uvicorn app.main:app --reload &

# Wait for startup
sleep 5

# Test CREATE endpoint
curl -X POST http://localhost:8000/api/oracle/users \
  -H "Authorization: Bearer test_api_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test User", "birthday": "1990-01-01"}'
# Expected: 201 Created, user object with id

# Test LIST endpoint
curl http://localhost:8000/api/oracle/users \
  -H "Authorization: Bearer test_api_key"
# Expected: 200 OK, paginated list with total count

# Test GET endpoint
curl http://localhost:8000/api/oracle/users/1 \
  -H "Authorization: Bearer test_api_key"
# Expected: 200 OK, user object OR 404 Not Found

# Test UPDATE endpoint
curl -X PUT http://localhost:8000/api/oracle/users/1 \
  -H "Authorization: Bearer test_api_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
# Expected: 200 OK, updated user object

# Test DELETE endpoint
curl -X DELETE http://localhost:8000/api/oracle/users/1 \
  -H "Authorization: Bearer test_api_key"
# Expected: 200 OK, success message

# Test OpenAPI docs
curl http://localhost:8000/docs
# Expected: Swagger UI with all 5 endpoints documented

# Stop server
pkill -f uvicorn
```

**Checkpoint:**
- [ ] All 5 endpoints respond correctly
- [ ] Authentication works (401 without API key)
- [ ] Validation works (400 for invalid input)
- [ ] Error responses follow standard format
- [ ] OpenAPI documentation complete
- [ ] Manual testing passes

**STOP if checkpoint fails** - Fix endpoints before comprehensive tests

---

### PHASE 5: Comprehensive Testing (Duration: 60 min)

**Subagent 4: Integration Tests**

**Tasks:**

1. **Create Test File**
   
   File: `api/tests/test_oracle_users.py`
   
   Test categories:
   ```python
   class TestCreateUser:
       # Happy path
       test_create_user_success
       test_create_user_with_notes
       
       # Validation errors
       test_create_user_missing_name
       test_create_user_invalid_birthday
       test_create_user_future_birthday
       test_create_user_name_too_long
       
       # Business logic errors
       test_create_user_duplicate
       
       # Security
       test_create_user_without_api_key
       test_create_user_birthday_encrypted
   
   class TestListUsers:
       test_list_users_default_pagination
       test_list_users_custom_pagination
       test_list_users_sorting
       test_list_users_empty_database
       test_list_users_excludes_deleted
       test_list_users_without_api_key
   
   class TestGetUser:
       test_get_user_success
       test_get_user_decrypts_birthday
       test_get_user_not_found
       test_get_user_deleted
       test_get_user_without_api_key
   
   class TestUpdateUser:
       test_update_user_name
       test_update_user_birthday
       test_update_user_notes
       test_update_user_multiple_fields
       test_update_user_not_found
       test_update_user_duplicate_name_birthday
       test_update_user_invalid_data
       test_update_user_without_api_key
   
   class TestDeleteUser:
       test_delete_user_success
       test_delete_user_soft_delete
       test_delete_user_not_found
       test_delete_user_already_deleted
       test_delete_user_without_api_key
   ```
   
   **Requirements:**
   - Use pytest fixtures for test database
   - Use TestClient from FastAPI
   - Mock API key validation
   - Test all status codes (200, 201, 400, 401, 404, 500)
   - Test edge cases (empty strings, max lengths, special chars)
   - Verify encryption (check database contains encrypted birthday)
   - Verify audit logs written

2. **Test Coverage Measurement**
   
   ```bash
   pytest tests/test_oracle_users.py -v --cov=app/routers/oracle --cov=app/services/oracle_service --cov=app/models/oracle --cov-report=term-missing
   ```
   
   **Target:** 95%+ coverage for all new code

**Verification:**
```bash
cd api

# Run all tests
pytest tests/test_oracle_users.py -v --cov --cov-report=term-missing

# Expected output:
# - All tests pass (50+ tests)
# - Coverage 95%+
# - No warnings

# Run specific test categories
pytest tests/test_oracle_users.py::TestCreateUser -v
pytest tests/test_oracle_users.py::TestListUsers -v
pytest tests/test_oracle_users.py::TestGetUser -v
pytest tests/test_oracle_users.py::TestUpdateUser -v
pytest tests/test_oracle_users.py::TestDeleteUser -v
```

**Checkpoint:**
- [ ] All 50+ tests pass
- [ ] Coverage ≥95% for routers/oracle.py
- [ ] Coverage ≥95% for services/oracle_service.py
- [ ] Coverage ≥95% for models/oracle.py
- [ ] All status codes tested
- [ ] Encryption verified in tests
- [ ] Audit logging verified in tests
- [ ] Edge cases covered

**STOP if checkpoint fails** - Fix failing tests before verification

---

### PHASE 6: Final Verification & Documentation (Duration: 30 min)

**Tasks:**

1. **Run Full Test Suite**
   
   ```bash
   cd api
   pytest tests/ -v --cov --cov-report=html
   # Open htmlcov/index.html to verify coverage
   ```

2. **Type Check**
   
   ```bash
   mypy app/ --strict
   # Expected: No errors
   ```

3. **Performance Test**
   
   ```bash
   # Install Apache Bench if needed
   # apt-get install apache2-utils
   
   # Test LIST endpoint performance
   ab -n 1000 -c 10 -H "Authorization: Bearer test_api_key" http://localhost:8000/api/oracle/users
   
   # Check p95 response time
   # Expected: <50ms
   ```

4. **OpenAPI Documentation Review**
   
   ```bash
   # Start server
   uvicorn app.main:app --reload &
   
   # Visit Swagger UI
   curl http://localhost:8000/docs
   
   # Verify:
   # - All 5 endpoints documented
   # - Request/response examples present
   # - Error codes documented
   # - Authentication requirement shown
   ```

5. **Database Verification**
   
   ```bash
   # Check encrypted data in database
   psql -c "SELECT id, name, birthday_encrypted, deleted_at FROM oracle_users LIMIT 5;"
   
   # Verify:
   # - birthday_encrypted contains encrypted string (not plaintext date)
   # - Soft-deleted users have deleted_at timestamp
   # - Indexes exist
   
   psql -c "\d oracle_users"
   # Verify indexes: ix_oracle_users_created_at, ix_oracle_users_deleted_at
   ```

6. **Audit Log Verification**
   
   ```bash
   # Check audit logs
   tail -n 50 logs/api.log | grep "user_id" | jq .
   
   # Verify:
   # - CREATE operations logged
   # - UPDATE operations logged
   # - DELETE operations logged
   # - Logs in JSON format
   ```

**Checkpoint (Final Quality Gate):**
- [ ] All tests pass (50+ tests, 0 failures)
- [ ] Test coverage ≥95%
- [ ] Type check passes (mypy strict)
- [ ] Performance <50ms p95
- [ ] OpenAPI docs complete
- [ ] Birthday encrypted in database
- [ ] Soft delete working (deleted_at set)
- [ ] Audit logs written
- [ ] No security vulnerabilities (API key required, no SQL injection)

**STOP if any checkpoint fails** - Fix before declaring complete

---

## ✅ SUCCESS CRITERIA

**The implementation is considered complete when ALL of these are met:**

### Functional Criteria
1. **Create User (POST /api/oracle/users)**
   - ✅ Creates user with name + birthday
   - ✅ Returns 201 status code
   - ✅ Birthday encrypted before database storage
   - ✅ Duplicate name+birthday returns 400 error
   - ✅ Invalid input returns 400 error
   - ✅ Missing API key returns 401 error

2. **List Users (GET /api/oracle/users)**
   - ✅ Returns paginated list (default 20 per page)
   - ✅ Pagination works (page, limit, sort, order params)
   - ✅ Excludes soft-deleted users
   - ✅ Returns total count
   - ✅ Response time <50ms for 1000 users

3. **Get User (GET /api/oracle/users/{id})**
   - ✅ Returns user by ID
   - ✅ Birthday decrypted in response
   - ✅ Returns 404 if user not found
   - ✅ Returns 404 if user soft-deleted

4. **Update User (PUT /api/oracle/users/{id})**
   - ✅ Updates name, birthday, or notes
   - ✅ Re-encrypts birthday if changed
   - ✅ Returns 404 if user not found
   - ✅ Returns 400 for invalid input
   - ✅ Duplicate check enforced

5. **Delete User (DELETE /api/oracle/users/{id})**
   - ✅ Soft deletes user (sets deleted_at)
   - ✅ User not in list after deletion
   - ✅ Returns 404 if already deleted
   - ✅ Preserves data in database (not hard delete)

### Quality Criteria
- ✅ Test coverage ≥95% (verified: `pytest --cov`)
- ✅ All tests pass (50+ tests, 0 failures)
- ✅ Type hints pass mypy strict check
- ✅ No linting errors (flake8, black)
- ✅ Performance target met (<50ms p95)

### Security Criteria
- ✅ API key authentication on all endpoints
- ✅ Birthday encrypted in database (AES-256)
- ✅ No SQL injection (parameterized queries)
- ✅ No sensitive data in error responses
- ✅ Audit logging for all CUD operations

### Documentation Criteria
- ✅ OpenAPI schema complete (all endpoints)
- ✅ Request/response examples provided
- ✅ Error codes documented
- ✅ Code comments for complex logic
- ✅ Docstrings for all public functions

---

## 🔄 HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

### Resume from Phase: [CURRENT_PHASE]

**Context needed to continue:**
- Last completed phase: [X]
- Files created so far: [list]
- Tests passing: [X/Y]
- Current blockers: [list]

**Verification before continuing:**
```bash
# Verify previous phase checkpoint
cd api
pytest tests/test_oracle_users.py -v

# Check file structure
ls -R app/routers/ app/models/ app/services/ tests/

# Verify imports work
python -c "from app.models.oracle import UserCreateRequest; print('OK')"
```

**What to do next:**
1. Complete Phase [N]
2. Run Phase [N] checkpoint
3. If checkpoint passes, proceed to Phase [N+1]
4. If checkpoint fails, debug before continuing

---

## 🎯 NEXT STEPS (After This Spec Completes)

**Immediate next actions:**

1. **Terminal 2 - Session 2 (T2-S2): Oracle Reading Endpoints**
   - POST /api/oracle/reading (daily insight)
   - POST /api/oracle/question (question + time sign)
   - POST /api/oracle/name (name numerology)
   - Integration with Terminal 3B (Oracle service)
   - Estimated: 4-5 hours

2. **Terminal 1 - Session 3 (T1-S3): Oracle User Management UI**
   - Create OracleUsers.tsx page
   - User list table with pagination
   - Create/Edit user form modal
   - Delete confirmation dialog
   - API integration (use endpoints from T2-S1)
   - Estimated: 3-4 hours

3. **Terminal 7 - Session 1 (T7-S1): User Management Monitoring**
   - Add user creation/deletion metrics to dashboard
   - Alert on high user deletion rate
   - Audit log analysis for user operations
   - Estimated: 1-2 hours

---

## 📚 REFERENCES

**Project Documents:**
- Architecture Plan: `/mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` (Layer 2 section)
- Verification Checklist: `/mnt/project/VERIFICATION_CHECKLISTS.md` (Layer 2 section)
- Error Recovery: `/mnt/project/ERROR_RECOVERY.md` (API errors section)

**Dependencies:**
- Terminal 4 Database Schema: `database/schemas/oracle_users.sql`
- Terminal 6 Security: `api/app/security/auth.py`, `api/app/security/encryption.py`

**Related Conversations:**
- Use `conversation_search("oracle user management")` for past decisions
- Use `conversation_search("API authentication")` for auth patterns

---

## 🎓 LESSONS LEARNED (Update after completion)

**What worked well:**
- [To be filled after implementation]

**What could be improved:**
- [To be filled after implementation]

**Patterns to reuse:**
- [To be filled after implementation]

---

*Spec Version: 1.0*  
*Created: 2026-02-08*  
*For: Claude Code CLI with Extended Thinking*  
*Session: T2-S1 (Oracle User Management API)*
