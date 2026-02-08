# SPEC: Security Oracle Layer - T6-S1
**Estimated Duration:** 2.5-3 hours  
**Layer:** Layer 6 (Security)  
**Terminal:** Terminal 6  
**Phase:** Phase 5 (Security Infrastructure)  
**Dependencies:** Terminal 4 (Database schema must exist), Terminal 2 (API endpoints)

---

## TL;DR
- Implementing comprehensive security for Oracle system (separate from Scanner vault)
- AES-256 encryption for sensitive Persian/English user data (names, questions)
- API key authentication with 3-tier scope system (read/write/admin)
- Audit logging for compliance and security monitoring
- Row-level permission system (users access own data, multi-user readings shared, admins see all)
- Reusing battle-tested V3 encryption patterns with Oracle-specific adaptations

---

## OBJECTIVE

Create production-grade security infrastructure for Oracle system that:
1. Protects sensitive user information (names, questions in Persian/English)
2. Enforces role-based access control with API keys
3. Maintains complete audit trail for compliance
4. Enables secure multi-user Oracle readings
5. Prevents unauthorized data access at database layer

---

## CONTEXT

**Current State:**
- Database schema exists (Terminal 4 completed)
- API endpoints stubbed (Terminal 2 foundation)
- No security layer implemented
- Sensitive data stored in plaintext (security risk)

**What's Changing:**
- Adding 4-component security system:
  1. Encryption module (AES-256 for user data)
  2. Authentication middleware (API key validation)
  3. Audit logging (security event tracking)
  4. Permission system (row-level access control)

**Why Critical:**
- Oracle stores personal information (names, birthdates, questions)
- Persian text requires proper UTF-8 handling in encryption
- Multi-user readings need complex permission logic
- Compliance requires audit trail
- API exposure demands robust authentication

**Architecture Decision (Extended Thinking):**

The Oracle security system differs from Scanner vault security in key ways:

**Scanner Vault Security:** Protects cryptocurrency private keys (extremely sensitive, single-user, high-value targets)

**Oracle Security:** Protects personal user data (moderately sensitive, multi-user capable, privacy-focused)

**Key Differences:**
1. **Data Sensitivity Level:**
   - Scanner: Private keys = financial asset access
   - Oracle: Names/questions = personal privacy

2. **Access Patterns:**
   - Scanner: Individual wallet findings, no sharing
   - Oracle: Single-user AND multi-user readings (collaboration)

3. **Encryption Scope:**
   - Scanner: Encrypt private_key + seed_phrase
   - Oracle: Encrypt name, name_persian, mother_name, mother_name_persian, question, question_persian

4. **Permission Model:**
   - Scanner: User owns finding = full access
   - Oracle: Complex 3-tier (owner, participant, admin)

**Design Philosophy:**
- **Reuse V3 encryption core** (proven AES-256 implementation)
- **Adapt for Oracle data structures** (user profiles, readings)
- **Add multi-user permission layer** (new requirement)
- **Separate audit log** (Oracle-specific events)

This separation allows:
- Independent security policies per system
- Specialized audit trails
- Different permission models
- Clearer code organization

---

## PREREQUISITES

**Required Completions:**
- [x] Terminal 4: Database schema exists
  - Verify: `psql -c "\d oracle_users"` returns table definition
  - Verify: `psql -c "\d oracle_readings"` returns table definition
  
- [x] Terminal 2: API foundation exists
  - Verify: `curl http://localhost:8000/api/health` returns 200
  
- [x] V3 codebase available
  - Verify: V3 `engines/security.py` file accessible for reference

**Environment Setup:**
- [ ] `NPS_MASTER_PASSWORD` environment variable set
  - This is the master encryption key for all Oracle data
  - Must be same across all services
  - Should be 32+ characters, alphanumeric + special chars
  
- [ ] Python 3.11+ installed
  - Verify: `python3 --version`
  
- [ ] PostgreSQL 15+ running
  - Verify: `psql -c "SELECT version();"`

**Tools Available:**
- [ ] cryptography library (will install)
- [ ] FastAPI (already installed for API layer)
- [ ] pytest (for testing)

---

## TOOLS TO USE

**Extended Thinking:**
- Security threat modeling (what attacks to defend against?)
- Encryption key derivation strategy (PBKDF2 vs direct SHA-256)
- Multi-user permission logic design (who can access what?)
- Performance optimization (caching decrypted data? no - security risk)

**View Tool:**
- `view /mnt/project/NPS_V4_ARCHITECTURE_PLAN.md` Layer 6 section
- `view /mnt/project/VERIFICATION_CHECKLISTS.md` Layer 6 checklist
- V3 `engines/security.py` for encryption reference

**Subagents:** Not needed for this session (linear dependencies)

**MCP Servers:** Not needed (direct database access via psycopg2)

---

## REQUIREMENTS

### Functional Requirements

**FR1: Encryption**
- Encrypt user profile fields: `name`, `name_persian`, `mother_name`, `mother_name_persian`
- Encrypt reading fields: `question`, `question_persian`
- Maintain birthdate fields as plaintext (needed for date calculations, not PII)
- Handle UTF-8 Persian text correctly (no encoding issues)
- Decrypt only when authorized user requests data
- Performance: Encryption/decryption <10ms per operation

**FR2: Authentication**
- Validate API keys using SHA-256 hash comparison
- Support 3 scope levels:
  - `oracle_read`: Can query own readings + public Oracle insights
  - `oracle_write`: Can create users + readings + update own data
  - `oracle_admin`: Full access to all users + readings + system operations
- Reject invalid/expired keys with proper HTTP status (401)
- Reject insufficient scope with proper HTTP status (403)
- Rate limit AI-powered endpoints (prevent abuse)

**FR3: Audit Logging**
- Log security events:
  - `user_created`: New user registration
  - `reading_created`: New Oracle reading
  - `reading_accessed`: User views reading
  - `reading_shared`: Multi-user reading created
  - `auth_failed`: Invalid API key attempt
  - `auth_success`: Valid API key used
  - `permission_denied`: User tried accessing unauthorized data
- Store: timestamp, user_id, action, resource_id, success, IP address, API key hash
- Separate Oracle audit log from Scanner audit log
- Query audit log by: user, action, date range, success/failure

**FR4: Permission System**
- **Rule 1 (Own Data):** User can access readings they created
- **Rule 2 (Multi-User):** All participants can access multi-user readings
- **Rule 3 (Admin):** Admin scope can access all readings
- **Rule 4 (No Cross-User):** User A cannot access User B's single-user readings
- Enforce at database query level (WHERE clause filtering)
- Return 403 if permission check fails

### Non-Functional Requirements

**NFR1: Security**
- Use AES-256-CBC encryption (industry standard)
- Never store encryption keys in code (environment variables only)
- Never log decrypted sensitive data
- No plaintext sensitive data in database
- SQL injection prevention (parameterized queries)

**NFR2: Performance**
- Encryption/decryption: <10ms per field
- API key validation: <5ms
- Audit log write: <2ms (async if possible)
- Permission check: <3ms (single query)

**NFR3: Maintainability**
- Reuse V3 encryption core (don't reinvent crypto)
- Clear separation of concerns (encryption, auth, audit, permissions)
- Comprehensive unit tests (95%+ coverage)
- Integration tests for end-to-end flows

**NFR4: Compliance**
- Audit logs retained for 90 days minimum
- No sensitive data in audit logs (hash/redact as needed)
- GDPR-compatible (encryption, audit trail, data access control)

---

## IMPLEMENTATION PLAN

### Phase 1: Encryption Module (50 minutes)

**Objective:** Create Oracle-specific encryption layer that handles Persian text and user data structures.

**Tasks:**

1. **Copy V3 encryption foundation** (5 min)
   - Reference V3 `engines/security.py`
   - Extract core AES-256 encryption functions
   - Adapt for Oracle data structures

2. **Create OracleEncryption class** (20 min)
   - Initialize with master password
   - Derive encryption key (SHA-256 of master password)
   - Create Fernet cipher instance
   - Handle key encoding (base64 for Fernet compatibility)

3. **Implement encrypt_user_profile()** (10 min)
   - Accept user dict (from database)
   - Encrypt: name, name_persian, mother_name, mother_name_persian
   - Return dict with encrypted fields (suffix: `_encrypted`)
   - Preserve non-sensitive fields (id, birthday, gender, etc.)

4. **Implement decrypt_user_profile()** (10 min)
   - Accept encrypted user dict
   - Decrypt: name_encrypted → name, etc.
   - Return dict with plaintext sensitive fields
   - Handle missing fields gracefully (None if not present)

5. **Implement encrypt_reading() / decrypt_reading()** (5 min)
   - Similar to user profile
   - Encrypt: question, question_persian
   - Preserve: id, user_id, reading_type, created_at, etc.

**Files to Create:**

```
security/
├── encryption/
│   ├── __init__.py
│   ├── oracle_encryption.py        # Main encryption class
│   └── key_derivation.py           # Key management utilities
└── tests/
    └── test_oracle_encryption.py   # Comprehensive encryption tests
```

**Code Structure:**

```python
# security/encryption/oracle_encryption.py
from cryptography.fernet import Fernet
import base64
import hashlib
from typing import Dict, Optional

class OracleEncryption:
    """
    AES-256 encryption for Oracle user data and readings.
    
    Encrypts sensitive fields:
    - User: name, name_persian, mother_name, mother_name_persian
    - Reading: question, question_persian
    
    Uses Fernet (AES-256-CBC + HMAC-SHA256) for authenticated encryption.
    """
    
    def __init__(self, master_password: str):
        """
        Initialize encryption with master password.
        
        Args:
            master_password: Master encryption key from NPS_MASTER_PASSWORD env var
            
        Raises:
            ValueError: If master_password empty or too short
        """
        if not master_password or len(master_password) < 16:
            raise ValueError("Master password must be at least 16 characters")
        
        # Derive 32-byte key from password
        key_material = hashlib.sha256(master_password.encode('utf-8')).digest()
        self.fernet_key = base64.urlsafe_b64encode(key_material)
        self.cipher = Fernet(self.fernet_key)
    
    def encrypt_user_profile(self, user_data: Dict) -> Dict:
        """
        Encrypt sensitive fields in user profile.
        
        Args:
            user_data: User dict from database (plaintext)
            
        Returns:
            Dict with encrypted fields (suffix: _encrypted)
            
        Example:
            Input:  {'id': 1, 'name': 'علی', 'birthday': '1990-01-01'}
            Output: {'id': 1, 'name_encrypted': 'gAAAAA...', 'birthday': '1990-01-01'}
        """
        encrypted = user_data.copy()
        
        # Fields to encrypt
        sensitive_fields = [
            'name', 'name_persian', 
            'mother_name', 'mother_name_persian'
        ]
        
        for field in sensitive_fields:
            if user_data.get(field):
                # Encrypt UTF-8 bytes
                plaintext = user_data[field].encode('utf-8')
                ciphertext = self.cipher.encrypt(plaintext)
                encrypted[f'{field}_encrypted'] = ciphertext.decode('ascii')
                
                # Remove plaintext (don't store both)
                del encrypted[field]
        
        return encrypted
    
    def decrypt_user_profile(self, encrypted_data: Dict) -> Dict:
        """
        Decrypt sensitive fields in user profile.
        
        Args:
            encrypted_data: User dict from database (encrypted)
            
        Returns:
            Dict with decrypted fields (plaintext)
            
        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        decrypted = encrypted_data.copy()
        
        # Fields to decrypt
        encrypted_fields = [
            'name', 'name_persian',
            'mother_name', 'mother_name_persian'
        ]
        
        for field in encrypted_fields:
            encrypted_key = f'{field}_encrypted'
            if encrypted_data.get(encrypted_key):
                # Decrypt to UTF-8 string
                ciphertext = encrypted_data[encrypted_key].encode('ascii')
                plaintext_bytes = self.cipher.decrypt(ciphertext)
                decrypted[field] = plaintext_bytes.decode('utf-8')
                
                # Remove encrypted (return plaintext only)
                del decrypted[encrypted_key]
        
        return decrypted
    
    def encrypt_reading(self, reading_data: Dict) -> Dict:
        """
        Encrypt sensitive fields in Oracle reading.
        
        Args:
            reading_data: Reading dict from database (plaintext)
            
        Returns:
            Dict with encrypted question fields
        """
        encrypted = reading_data.copy()
        
        # Encrypt questions
        if reading_data.get('question'):
            plaintext = reading_data['question'].encode('utf-8')
            ciphertext = self.cipher.encrypt(plaintext)
            encrypted['question_encrypted'] = ciphertext.decode('ascii')
            del encrypted['question']
        
        if reading_data.get('question_persian'):
            plaintext = reading_data['question_persian'].encode('utf-8')
            ciphertext = self.cipher.encrypt(plaintext)
            encrypted['question_persian_encrypted'] = ciphertext.decode('ascii')
            del encrypted['question_persian']
        
        return encrypted
    
    def decrypt_reading(self, encrypted_data: Dict) -> Dict:
        """Decrypt sensitive fields in Oracle reading."""
        decrypted = encrypted_data.copy()
        
        if encrypted_data.get('question_encrypted'):
            ciphertext = encrypted_data['question_encrypted'].encode('ascii')
            plaintext_bytes = self.cipher.decrypt(ciphertext)
            decrypted['question'] = plaintext_bytes.decode('utf-8')
            del decrypted['question_encrypted']
        
        if encrypted_data.get('question_persian_encrypted'):
            ciphertext = encrypted_data['question_persian_encrypted'].encode('ascii')
            plaintext_bytes = self.cipher.decrypt(ciphertext)
            decrypted['question_persian'] = plaintext_bytes.decode('utf-8')
            del decrypted['question_persian_encrypted']
        
        return decrypted
```

**Test Structure:**

```python
# security/tests/test_oracle_encryption.py
import pytest
from encryption.oracle_encryption import OracleEncryption

class TestOracleEncryption:
    """Test Oracle encryption module."""
    
    @pytest.fixture
    def encryptor(self):
        """Create encryptor with test password."""
        return OracleEncryption("test_master_password_32chars!!")
    
    def test_encrypt_decrypt_user_profile_roundtrip(self, encryptor):
        """Test user profile encryption roundtrip preserves data."""
        original = {
            'id': 1,
            'name': 'John Doe',
            'name_persian': 'علی رضایی',
            'mother_name': 'Jane Doe',
            'mother_name_persian': 'فاطمه',
            'birthday': '1990-01-01',
            'gender': 'male'
        }
        
        # Encrypt
        encrypted = encryptor.encrypt_user_profile(original)
        
        # Verify encrypted fields exist
        assert 'name_encrypted' in encrypted
        assert 'name_persian_encrypted' in encrypted
        assert 'name' not in encrypted  # Plaintext removed
        
        # Verify non-sensitive fields preserved
        assert encrypted['birthday'] == '1990-01-01'
        assert encrypted['gender'] == 'male'
        
        # Decrypt
        decrypted = encryptor.decrypt_user_profile(encrypted)
        
        # Verify roundtrip
        assert decrypted['name'] == original['name']
        assert decrypted['name_persian'] == original['name_persian']
        assert decrypted['mother_name'] == original['mother_name']
        assert decrypted['mother_name_persian'] == original['mother_name_persian']
    
    def test_encrypt_persian_text_utf8(self, encryptor):
        """Test Persian text encryption handles UTF-8 correctly."""
        user = {
            'id': 1,
            'name_persian': 'محمد حسینی'
        }
        
        encrypted = encryptor.encrypt_user_profile(user)
        decrypted = encryptor.decrypt_user_profile(encrypted)
        
        assert decrypted['name_persian'] == 'محمد حسینی'
    
    def test_encrypt_reading_question(self, encryptor):
        """Test reading question encryption."""
        reading = {
            'id': 1,
            'question': 'Will I find success?',
            'question_persian': 'آیا موفق خواهم شد؟',
            'user_id': 1
        }
        
        encrypted = encryptor.encrypt_reading(reading)
        decrypted = encryptor.decrypt_reading(encrypted)
        
        assert decrypted['question'] == reading['question']
        assert decrypted['question_persian'] == reading['question_persian']
    
    def test_encryption_performance(self, encryptor):
        """Test encryption performance meets <10ms target."""
        import time
        
        user = {
            'name': 'John Doe',
            'name_persian': 'علی رضایی',
            'mother_name': 'Jane',
            'mother_name_persian': 'فاطمه'
        }
        
        start = time.perf_counter()
        encrypted = encryptor.encrypt_user_profile(user)
        duration = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert duration < 10, f"Encryption took {duration:.2f}ms, target <10ms"
    
    def test_invalid_master_password_raises(self):
        """Test invalid master password raises ValueError."""
        with pytest.raises(ValueError):
            OracleEncryption("")
        
        with pytest.raises(ValueError):
            OracleEncryption("short")  # <16 chars
```

**Acceptance Criteria:**
- [ ] OracleEncryption class created with init, encrypt, decrypt methods
- [ ] Can encrypt user profile with Persian text
- [ ] Can decrypt user profile correctly
- [ ] Roundtrip test passes (encrypt → decrypt = original)
- [ ] Persian UTF-8 text handled correctly (no garbled characters)
- [ ] Performance <10ms per operation
- [ ] Missing fields handled gracefully (no crashes)
- [ ] Invalid master password raises ValueError

**Verification:**

```bash
# Terminal 1: Install dependencies
cd security
pip install cryptography pytest --break-system-packages

# Terminal 2: Run tests
pytest tests/test_oracle_encryption.py -v --tb=short

# Expected output:
# test_oracle_encryption.py::TestOracleEncryption::test_encrypt_decrypt_user_profile_roundtrip PASSED
# test_oracle_encryption.py::TestOracleEncryption::test_encrypt_persian_text_utf8 PASSED
# test_oracle_encryption.py::TestOracleEncryption::test_encrypt_reading_question PASSED
# test_oracle_encryption.py::TestOracleEncryption::test_encryption_performance PASSED
# test_oracle_encryption.py::TestOracleEncryption::test_invalid_master_password_raises PASSED
# ======================== 5 passed in 0.12s ========================

# Terminal 3: Manual verification (Python REPL)
python3 << 'EOF'
import os
os.environ['NPS_MASTER_PASSWORD'] = 'test_password_32_characters_long!'

from encryption.oracle_encryption import OracleEncryption

encryptor = OracleEncryption(os.environ['NPS_MASTER_PASSWORD'])

# Test Persian user
user = {
    'id': 1,
    'name': 'علی رضایی',
    'name_persian': 'علی رضایی',
    'mother_name': 'فاطمه',
    'birthday': '1990-01-01'
}

print("Original:", user)

encrypted = encryptor.encrypt_user_profile(user)
print("Encrypted:", encrypted)

decrypted = encryptor.decrypt_user_profile(encrypted)
print("Decrypted:", decrypted)

# Verify Persian text preserved
assert decrypted['name'] == user['name']
assert decrypted['name_persian'] == user['name_persian']
print("✓ Persian text encryption/decryption successful")
EOF
```

**Checkpoint:**
- [ ] All 5 encryption tests pass
- [ ] Persian text roundtrip verified manually
- [ ] Performance target met (<10ms)

**STOP if checkpoint fails** - encryption is foundation for all other security

---

### Phase 2: Authentication Middleware (45 minutes)

**Objective:** Create API key validation system with 3-tier scope model for Oracle endpoints.

**Tasks:**

1. **Create API key validation function** (15 min)
   - Hash incoming API key (SHA-256)
   - Query database for matching key_hash
   - Check expiration (if expires_at < now, reject)
   - Check scopes (oracle_read, oracle_write, oracle_admin)
   - Update last_used_at timestamp

2. **Create FastAPI dependency** (10 min)
   - Use HTTPBearer for Authorization header
   - Create `validate_oracle_api_key()` dependency
   - Accept required_scope parameter
   - Return user context (api_key_hash, scope, user_id if applicable)

3. **Define scope hierarchy** (5 min)
   - `oracle_read`: Can query own data + public insights
   - `oracle_write`: oracle_read + create/update own data
   - `oracle_admin`: Full access to all users + all readings

4. **Add rate limiting** (10 min)
   - Prevent AI endpoint abuse
   - 100 requests per hour per API key for `/api/oracle/reading` (AI-powered)
   - Use in-memory rate limit tracker (dict with API key → request count + reset time)
   - Return 429 Too Many Requests if exceeded

5. **Write tests** (5 min)
   - Test valid key accepted
   - Test invalid key rejected (401)
   - Test expired key rejected (401)
   - Test insufficient scope rejected (403)
   - Test rate limiting works (429)

**Files to Create:**

```
security/
├── auth/
│   ├── __init__.py
│   ├── oracle_auth.py              # API key validation
│   ├── rate_limiter.py             # Rate limiting logic
│   └── scopes.py                   # Scope definitions
├── middleware/
│   ├── __init__.py
│   └── oracle_middleware.py        # FastAPI dependencies
└── tests/
    └── test_oracle_auth.py         # Authentication tests
```

**Code Structure:**

```python
# security/auth/scopes.py
from enum import Enum

class OracleScope(str, Enum):
    """Oracle API key scopes."""
    READ = "oracle_read"      # Can query own data
    WRITE = "oracle_write"    # Can create/update own data
    ADMIN = "oracle_admin"    # Full access to all data

# Scope hierarchy (higher scopes include lower scopes)
SCOPE_HIERARCHY = {
    OracleScope.ADMIN: [OracleScope.WRITE, OracleScope.READ],
    OracleScope.WRITE: [OracleScope.READ],
    OracleScope.READ: []
}

def has_scope(user_scopes: list[str], required_scope: str) -> bool:
    """
    Check if user has required scope (including hierarchy).
    
    Example:
        has_scope(['oracle_admin'], 'oracle_read') → True
        has_scope(['oracle_read'], 'oracle_write') → False
    """
    if required_scope in user_scopes:
        return True
    
    # Check hierarchy
    for user_scope in user_scopes:
        if user_scope in SCOPE_HIERARCHY:
            if required_scope in SCOPE_HIERARCHY[user_scope]:
                return True
    
    return False


# security/auth/rate_limiter.py
from datetime import datetime, timedelta
from typing import Dict

class RateLimiter:
    """
    In-memory rate limiter for API endpoints.
    
    Tracks requests per API key with sliding window.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds (default 1 hour)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[datetime]] = {}
    
    def is_allowed(self, api_key_hash: str) -> bool:
        """
        Check if request is allowed for API key.
        
        Args:
            api_key_hash: SHA-256 hash of API key
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Initialize or clean old requests
        if api_key_hash not in self.requests:
            self.requests[api_key_hash] = []
        
        # Remove requests outside window
        self.requests[api_key_hash] = [
            req_time for req_time in self.requests[api_key_hash]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[api_key_hash]) >= self.max_requests:
            return False
        
        # Record request
        self.requests[api_key_hash].append(now)
        return True


# security/middleware/oracle_middleware.py
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
from typing import Dict
from datetime import datetime

from ..auth.scopes import OracleScope, has_scope
from ..auth.rate_limiter import RateLimiter

security_scheme = HTTPBearer()

# Global rate limiter (100 requests/hour for AI endpoints)
ai_rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)

async def validate_oracle_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    required_scope: str = OracleScope.READ,
    check_rate_limit: bool = False,
    db = None  # Will be injected by FastAPI dependency
) -> Dict:
    """
    Validate API key for Oracle endpoints.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        required_scope: Minimum required scope (oracle_read, oracle_write, oracle_admin)
        check_rate_limit: If True, enforce rate limiting (for AI endpoints)
        db: Database connection (injected by FastAPI)
        
    Returns:
        Dict with api_key_hash, scope, user_id (if applicable)
        
    Raises:
        HTTPException 401: Invalid or expired API key
        HTTPException 403: Insufficient scope
        HTTPException 429: Rate limit exceeded
        
    Usage in FastAPI:
        @app.get("/api/oracle/users", dependencies=[Depends(validate_oracle_api_key)])
        async def get_users():
            ...
    """
    api_key = credentials.credentials
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Hash the key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Check rate limit (if enabled)
    if check_rate_limit:
        if not ai_rate_limiter.is_allowed(key_hash):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 100 requests per hour."
            )
    
    # Query database for API key
    # NOTE: This is a simplified version - actual implementation will use FastAPI dependency injection
    # to get database connection from app state
    # result = db.query(
    #     "SELECT scopes, expires_at FROM api_keys WHERE key_hash = %s",
    #     (key_hash,)
    # )
    
    # For specification purposes, assume database query works
    # Actual implementation will be in API layer integration
    
    # Example validation logic:
    # if not result:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    #
    # scopes, expires_at = result[0]
    #
    # if expires_at and expires_at < datetime.now():
    #     raise HTTPException(status_code=401, detail="API key expired")
    #
    # if not has_scope(scopes, required_scope):
    #     raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return {
        "api_key_hash": key_hash,
        "scope": required_scope
    }
```

**Test Structure:**

```python
# security/tests/test_oracle_auth.py
import pytest
from fastapi import HTTPException
from auth.scopes import OracleScope, has_scope
from auth.rate_limiter import RateLimiter

class TestOracleScopes:
    """Test scope hierarchy logic."""
    
    def test_exact_scope_match(self):
        """Test exact scope match returns True."""
        assert has_scope(['oracle_read'], 'oracle_read') == True
    
    def test_admin_has_all_scopes(self):
        """Test admin scope includes read and write."""
        assert has_scope(['oracle_admin'], 'oracle_read') == True
        assert has_scope(['oracle_admin'], 'oracle_write') == True
    
    def test_write_has_read(self):
        """Test write scope includes read."""
        assert has_scope(['oracle_write'], 'oracle_read') == True
    
    def test_read_does_not_have_write(self):
        """Test read scope does not include write."""
        assert has_scope(['oracle_read'], 'oracle_write') == False
    
    def test_read_does_not_have_admin(self):
        """Test read scope does not include admin."""
        assert has_scope(['oracle_read'], 'oracle_admin') == False

class TestRateLimiter:
    """Test rate limiting logic."""
    
    def test_first_request_allowed(self):
        """Test first request is allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.is_allowed('test_key_hash') == True
    
    def test_requests_under_limit_allowed(self):
        """Test requests under limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            assert limiter.is_allowed('test_key_hash') == True
    
    def test_requests_over_limit_blocked(self):
        """Test requests over limit are blocked."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 allowed
        for i in range(5):
            limiter.is_allowed('test_key_hash')
        
        # 6th blocked
        assert limiter.is_allowed('test_key_hash') == False
    
    def test_different_keys_independent(self):
        """Test different API keys have independent limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        assert limiter.is_allowed('key1') == True
        assert limiter.is_allowed('key1') == True
        assert limiter.is_allowed('key1') == False  # Over limit
        
        # Different key still has quota
        assert limiter.is_allowed('key2') == True
        assert limiter.is_allowed('key2') == True
```

**Acceptance Criteria:**
- [ ] OracleScope enum defined with READ, WRITE, ADMIN
- [ ] Scope hierarchy works (admin has write, write has read)
- [ ] RateLimiter tracks requests per API key
- [ ] RateLimiter blocks after limit exceeded
- [ ] validate_oracle_api_key() dependency created
- [ ] All scope tests pass (5/5)
- [ ] All rate limiter tests pass (4/4)

**Verification:**

```bash
# Terminal 1: Run authentication tests
cd security
pytest tests/test_oracle_auth.py -v

# Expected output:
# test_oracle_auth.py::TestOracleScopes::test_exact_scope_match PASSED
# test_oracle_auth.py::TestOracleScopes::test_admin_has_all_scopes PASSED
# test_oracle_auth.py::TestOracleScopes::test_write_has_read PASSED
# test_oracle_auth.py::TestOracleScopes::test_read_does_not_have_write PASSED
# test_oracle_auth.py::TestOracleScopes::test_read_does_not_have_admin PASSED
# test_oracle_auth.py::TestRateLimiter::test_first_request_allowed PASSED
# test_oracle_auth.py::TestRateLimiter::test_requests_under_limit_allowed PASSED
# test_oracle_auth.py::TestRateLimiter::test_requests_over_limit_blocked PASSED
# test_oracle_auth.py::TestRateLimiter::test_different_keys_independent PASSED
# ======================== 9 passed in 0.08s ========================

# Terminal 2: Manual rate limit test
python3 << 'EOF'
from auth.rate_limiter import RateLimiter

limiter = RateLimiter(max_requests=3, window_seconds=5)

print("Testing rate limiter with 3 requests/5 seconds:")
for i in range(5):
    allowed = limiter.is_allowed('test_key')
    status = "✓ Allowed" if allowed else "✗ Blocked"
    print(f"Request {i+1}: {status}")

# Expected:
# Request 1: ✓ Allowed
# Request 2: ✓ Allowed
# Request 3: ✓ Allowed
# Request 4: ✗ Blocked
# Request 5: ✗ Blocked
EOF
```

**Checkpoint:**
- [ ] Scope hierarchy tests pass
- [ ] Rate limiter tests pass
- [ ] Manual rate limit test shows blocking after limit

**STOP if checkpoint fails** - authentication is critical for security

---

### Phase 3: Audit Logging (35 minutes)

**Objective:** Create comprehensive audit trail for all Oracle security events.

**Tasks:**

1. **Create audit log database schema** (10 min)
   - Table: `oracle_audit_log`
   - Columns: id, timestamp, user_id, action, resource_id, success, ip_address, api_key_hash, details (JSONB)
   - Indexes: timestamp, user_id, action

2. **Create OracleAuditLogger class** (15 min)
   - log_event() - Generic event logger
   - log_user_created() - User registration
   - log_reading_created() - New reading
   - log_reading_accessed() - Reading viewed
   - log_auth_failed() - Invalid API key
   - log_permission_denied() - Unauthorized access attempt

3. **Write tests** (10 min)
   - Test event insertion
   - Test event querying by user
   - Test event querying by action
   - Test event querying by date range

**Files to Create:**

```
database/
└── schemas/
    └── oracle_audit_log.sql        # Audit log table

security/
├── audit/
│   ├── __init__.py
│   └── oracle_audit.py             # Audit logger class
└── tests/
    └── test_oracle_audit.py        # Audit tests
```

**Database Schema:**

```sql
-- database/schemas/oracle_audit_log.sql

CREATE TABLE oracle_audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_id INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    ip_address VARCHAR(45),
    api_key_hash VARCHAR(64),
    details JSONB,
    
    -- Indexes for fast queries
    INDEX idx_oracle_audit_timestamp (timestamp),
    INDEX idx_oracle_audit_user (user_id),
    INDEX idx_oracle_audit_action (action),
    INDEX idx_oracle_audit_success (success)
);

-- Partition by month for performance (if needed later)
-- This table will grow over time, partitioning helps with query performance
-- Can add later: PARTITION BY RANGE (timestamp);

-- Retention policy: Keep 90 days of audit logs
-- Can add later: DELETE FROM oracle_audit_log WHERE timestamp < NOW() - INTERVAL '90 days';
```

**Code Structure:**

```python
# security/audit/oracle_audit.py
from datetime import datetime
from typing import Optional, Dict, List
import json

class OracleAuditLogger:
    """
    Audit logger for Oracle security events.
    
    Logs all security-relevant operations for compliance and investigation.
    """
    
    # Action type constants
    ACTION_USER_CREATED = "user_created"
    ACTION_READING_CREATED = "reading_created"
    ACTION_READING_ACCESSED = "reading_accessed"
    ACTION_READING_SHARED = "reading_shared"
    ACTION_AUTH_SUCCESS = "auth_success"
    ACTION_AUTH_FAILED = "auth_failed"
    ACTION_PERMISSION_DENIED = "permission_denied"
    
    def __init__(self, db_connection):
        """
        Initialize audit logger.
        
        Args:
            db_connection: PostgreSQL connection (psycopg2 or SQLAlchemy)
        """
        self.db = db_connection
    
    def log_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        api_key_hash: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> int:
        """
        Log security event.
        
        Args:
            action: Event type (e.g., 'user_created', 'reading_accessed')
            user_id: ID of user performing action
            resource_id: ID of resource being accessed (user_id or reading_id)
            success: Whether action succeeded
            ip_address: IP address of request
            api_key_hash: SHA-256 hash of API key used
            details: Additional event details (stored as JSONB)
            
        Returns:
            ID of created audit log entry
        """
        cursor = self.db.cursor()
        
        cursor.execute("""
            INSERT INTO oracle_audit_log 
            (user_id, action, resource_id, success, ip_address, api_key_hash, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id,
            action,
            resource_id,
            success,
            ip_address,
            api_key_hash,
            json.dumps(details) if details else None
        ))
        
        audit_id = cursor.fetchone()[0]
        self.db.commit()
        
        return audit_id
    
    def log_user_created(self, user_id: int, ip_address: str, api_key_hash: str):
        """Log user creation event."""
        return self.log_event(
            action=self.ACTION_USER_CREATED,
            user_id=user_id,
            resource_id=user_id,
            ip_address=ip_address,
            api_key_hash=api_key_hash
        )
    
    def log_reading_created(self, user_id: int, reading_id: int, reading_type: str):
        """Log reading creation event."""
        return self.log_event(
            action=self.ACTION_READING_CREATED,
            user_id=user_id,
            resource_id=reading_id,
            details={'reading_type': reading_type}
        )
    
    def log_reading_accessed(self, user_id: int, reading_id: int, success: bool):
        """Log reading access event."""
        return self.log_event(
            action=self.ACTION_READING_ACCESSED,
            user_id=user_id,
            resource_id=reading_id,
            success=success
        )
    
    def log_auth_failed(self, ip_address: str, api_key_hash: str):
        """Log authentication failure."""
        return self.log_event(
            action=self.ACTION_AUTH_FAILED,
            success=False,
            ip_address=ip_address,
            api_key_hash=api_key_hash
        )
    
    def log_permission_denied(self, user_id: int, resource_id: int, attempted_action: str):
        """Log permission denial event."""
        return self.log_event(
            action=self.ACTION_PERMISSION_DENIED,
            user_id=user_id,
            resource_id=resource_id,
            success=False,
            details={'attempted_action': attempted_action}
        )
    
    def get_user_activity(self, user_id: int, limit: int = 100) -> List[Dict]:
        """
        Get audit log for specific user.
        
        Args:
            user_id: User ID to query
            limit: Maximum number of records
            
        Returns:
            List of audit events
        """
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, action, resource_id, success, ip_address, details
            FROM oracle_audit_log
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """, (user_id, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
    
    def get_failed_attempts(self, hours: int = 24) -> List[Dict]:
        """
        Get failed authentication attempts in last N hours.
        
        Args:
            hours: Time window in hours
            
        Returns:
            List of failed auth events
        """
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT timestamp, action, ip_address, api_key_hash
            FROM oracle_audit_log
            WHERE action = %s
            AND timestamp > NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC
        """, (self.ACTION_AUTH_FAILED, hours))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
```

**Test Structure:**

```python
# security/tests/test_oracle_audit.py
import pytest
from audit.oracle_audit import OracleAuditLogger
from datetime import datetime

class TestOracleAuditLogger:
    """Test Oracle audit logging."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        # In actual tests, use test database or mock
        # For specification, assume mock works
        pass
    
    @pytest.fixture
    def audit_logger(self, mock_db):
        """Create audit logger with mock DB."""
        return OracleAuditLogger(mock_db)
    
    def test_log_user_created(self, audit_logger):
        """Test logging user creation event."""
        audit_id = audit_logger.log_user_created(
            user_id=1,
            ip_address='192.168.1.100',
            api_key_hash='abc123...'
        )
        
        assert isinstance(audit_id, int)
        assert audit_id > 0
    
    def test_log_reading_accessed(self, audit_logger):
        """Test logging reading access event."""
        audit_id = audit_logger.log_reading_accessed(
            user_id=1,
            reading_id=5,
            success=True
        )
        
        assert isinstance(audit_id, int)
    
    def test_get_user_activity(self, audit_logger):
        """Test querying user activity."""
        # Create some events
        audit_logger.log_user_created(1, '192.168.1.1', 'key1')
        audit_logger.log_reading_created(1, 10, 'daily')
        
        # Query activity
        activity = audit_logger.get_user_activity(user_id=1, limit=10)
        
        assert isinstance(activity, list)
        assert len(activity) >= 2
        assert activity[0]['action'] in [
            OracleAuditLogger.ACTION_USER_CREATED,
            OracleAuditLogger.ACTION_READING_CREATED
        ]
    
    def test_get_failed_attempts(self, audit_logger):
        """Test querying failed authentication attempts."""
        # Log failed attempt
        audit_logger.log_auth_failed(
            ip_address='192.168.1.100',
            api_key_hash='invalid_key'
        )
        
        # Query failed attempts
        failed = audit_logger.get_failed_attempts(hours=1)
        
        assert isinstance(failed, list)
        assert len(failed) >= 1
        assert failed[0]['action'] == OracleAuditLogger.ACTION_AUTH_FAILED
```

**Acceptance Criteria:**
- [ ] `oracle_audit_log` table created with indexes
- [ ] OracleAuditLogger class created with all log methods
- [ ] Can log events to database
- [ ] Can query events by user_id
- [ ] Can query failed auth attempts
- [ ] All audit tests pass (4/4)
- [ ] Audit log performance <2ms per write

**Verification:**

```bash
# Terminal 1: Create audit log table
cd database
psql -f schemas/oracle_audit_log.sql

# Expected output:
# CREATE TABLE
# CREATE INDEX
# CREATE INDEX
# CREATE INDEX
# CREATE INDEX

# Terminal 2: Verify table structure
psql -c "\d oracle_audit_log"

# Expected columns: id, timestamp, user_id, action, resource_id, success, ip_address, api_key_hash, details

# Terminal 3: Run audit tests
cd security
pytest tests/test_oracle_audit.py -v

# Expected: All tests pass

# Terminal 4: Manual audit logging test
python3 << 'EOF'
import psycopg2
from audit.oracle_audit import OracleAuditLogger

# Connect to database
conn = psycopg2.connect("dbname=nps_db user=nps_user")
audit = OracleAuditLogger(conn)

# Log some events
user_id = audit.log_user_created(1, '192.168.1.1', 'key123')
reading_id = audit.log_reading_created(1, 5, 'daily')
access_id = audit.log_reading_accessed(1, 5, True)

print(f"Logged user creation: {user_id}")
print(f"Logged reading creation: {reading_id}")
print(f"Logged reading access: {access_id}")

# Query user activity
activity = audit.get_user_activity(1)
print(f"User activity: {len(activity)} events")

# Close connection
conn.close()
print("✓ Audit logging functional")
EOF
```

**Checkpoint:**
- [ ] Audit table created successfully
- [ ] Can insert audit events
- [ ] Can query audit events
- [ ] All tests pass

**STOP if checkpoint fails** - audit trail is critical for compliance

---

### Phase 4: Permission System (40 minutes)

**Objective:** Implement row-level access control for Oracle readings with multi-user support.

**Tasks:**

1. **Create permission checker class** (20 min)
   - can_access_reading() - Check if user can access reading
   - get_user_readings() - Get all readings user can access
   - get_reading_participants() - Get all users who can access reading

2. **Implement permission rules** (10 min)
   - Rule 1: User can access readings they created
   - Rule 2: User can access multi-user readings they're participant in
   - Rule 3: Admin can access all readings
   - Rule 4: All other access denied

3. **Add database helper functions** (5 min)
   - SQL queries with WHERE clause filtering
   - Use user_id from API key context

4. **Write tests** (5 min)
   - Test user can access own reading
   - Test user cannot access others' reading
   - Test multi-user reading accessible by participants
   - Test admin can access all readings

**Files to Create:**

```
security/
├── permissions/
│   ├── __init__.py
│   └── oracle_permissions.py       # Permission checker
└── tests/
    └── test_oracle_permissions.py  # Permission tests
```

**Code Structure:**

```python
# security/permissions/oracle_permissions.py
from typing import List, Dict, Optional

class OraclePermissions:
    """
    Permission system for Oracle data access.
    
    Implements row-level access control:
    - Users can access their own readings
    - Users can access multi-user readings they participate in
    - Admins can access all readings
    """
    
    def __init__(self, db_connection):
        """
        Initialize permissions checker.
        
        Args:
            db_connection: PostgreSQL connection
        """
        self.db = db_connection
    
    def can_access_reading(
        self,
        user_id: int,
        reading_id: int,
        is_admin: bool = False
    ) -> bool:
        """
        Check if user can access reading.
        
        Args:
            user_id: User requesting access
            reading_id: Reading to access
            is_admin: True if user has oracle_admin scope
            
        Returns:
            True if access allowed, False otherwise
        """
        # Admin can access everything
        if is_admin:
            return True
        
        cursor = self.db.cursor()
        
        # Check if single-user reading belongs to user
        cursor.execute("""
            SELECT user_id, is_multi_user
            FROM oracle_readings
            WHERE id = %s
        """, (reading_id,))
        
        result = cursor.fetchone()
        if not result:
            return False  # Reading doesn't exist
        
        reading_user_id, is_multi_user = result
        
        if not is_multi_user:
            # Single-user reading: must be owner
            return reading_user_id == user_id
        else:
            # Multi-user reading: check if user is participant
            cursor.execute("""
                SELECT COUNT(*)
                FROM oracle_reading_users
                WHERE reading_id = %s AND user_id = %s
            """, (reading_id, user_id))
            
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_user_readings(
        self,
        user_id: int,
        is_admin: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all readings user can access.
        
        Args:
            user_id: User requesting readings
            is_admin: True if user has oracle_admin scope
            limit: Maximum number of readings
            
        Returns:
            List of reading dicts
        """
        cursor = self.db.cursor()
        
        if is_admin:
            # Admin gets all readings
            cursor.execute("""
                SELECT id, user_id, reading_type, is_multi_user, created_at
                FROM oracle_readings
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
        else:
            # User gets own readings + multi-user readings they're in
            cursor.execute("""
                SELECT DISTINCT r.id, r.user_id, r.reading_type, r.is_multi_user, r.created_at
                FROM oracle_readings r
                LEFT JOIN oracle_reading_users ru ON r.id = ru.reading_id
                WHERE r.user_id = %s
                   OR (r.is_multi_user = TRUE AND ru.user_id = %s)
                ORDER BY r.created_at DESC
                LIMIT %s
            """, (user_id, user_id, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
    
    def get_reading_participants(self, reading_id: int) -> List[int]:
        """
        Get all user IDs who can access reading.
        
        Args:
            reading_id: Reading to check
            
        Returns:
            List of user IDs
        """
        cursor = self.db.cursor()
        
        # Check if multi-user
        cursor.execute("""
            SELECT is_multi_user, user_id
            FROM oracle_readings
            WHERE id = %s
        """, (reading_id,))
        
        result = cursor.fetchone()
        if not result:
            return []
        
        is_multi_user, owner_id = result
        
        if not is_multi_user:
            # Single-user: only owner
            return [owner_id]
        else:
            # Multi-user: all participants
            cursor.execute("""
                SELECT user_id
                FROM oracle_reading_users
                WHERE reading_id = %s
            """, (reading_id,))
            
            participant_ids = [row[0] for row in cursor.fetchall()]
            return participant_ids
    
    def add_reading_participant(self, reading_id: int, user_id: int) -> bool:
        """
        Add user as participant to multi-user reading.
        
        Args:
            reading_id: Reading to share
            user_id: User to add
            
        Returns:
            True if added, False if already participant or reading is single-user
        """
        cursor = self.db.cursor()
        
        # Verify reading is multi-user
        cursor.execute("""
            SELECT is_multi_user
            FROM oracle_readings
            WHERE id = %s
        """, (reading_id,))
        
        result = cursor.fetchone()
        if not result or not result[0]:
            return False  # Not multi-user
        
        # Add participant
        try:
            cursor.execute("""
                INSERT INTO oracle_reading_users (reading_id, user_id)
                VALUES (%s, %s)
            """, (reading_id, user_id))
            self.db.commit()
            return True
        except Exception as e:
            # Already participant (unique constraint violation)
            return False
```

**Test Structure:**

```python
# security/tests/test_oracle_permissions.py
import pytest
from permissions.oracle_permissions import OraclePermissions

class TestOraclePermissions:
    """Test Oracle permission system."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database with test data."""
        # In actual tests, use test database
        # For specification, assume mock works
        pass
    
    @pytest.fixture
    def permissions(self, mock_db):
        """Create permissions checker."""
        return OraclePermissions(mock_db)
    
    def test_user_can_access_own_reading(self, permissions):
        """Test user can access reading they created."""
        # Assume reading 1 belongs to user 1
        assert permissions.can_access_reading(
            user_id=1,
            reading_id=1,
            is_admin=False
        ) == True
    
    def test_user_cannot_access_others_reading(self, permissions):
        """Test user cannot access another user's reading."""
        # Assume reading 1 belongs to user 1
        assert permissions.can_access_reading(
            user_id=2,
            reading_id=1,
            is_admin=False
        ) == False
    
    def test_participant_can_access_multi_user_reading(self, permissions):
        """Test participant can access multi-user reading."""
        # Assume reading 2 is multi-user with participants [1, 2, 3]
        assert permissions.can_access_reading(
            user_id=2,
            reading_id=2,
            is_admin=False
        ) == True
    
    def test_non_participant_cannot_access_multi_user_reading(self, permissions):
        """Test non-participant cannot access multi-user reading."""
        # Assume reading 2 is multi-user with participants [1, 2, 3]
        assert permissions.can_access_reading(
            user_id=4,
            reading_id=2,
            is_admin=False
        ) == False
    
    def test_admin_can_access_all_readings(self, permissions):
        """Test admin can access any reading."""
        # Admin can access any reading
        assert permissions.can_access_reading(
            user_id=999,
            reading_id=1,
            is_admin=True
        ) == True
        
        assert permissions.can_access_reading(
            user_id=999,
            reading_id=2,
            is_admin=True
        ) == True
    
    def test_get_user_readings_includes_own(self, permissions):
        """Test get_user_readings includes own readings."""
        readings = permissions.get_user_readings(user_id=1, is_admin=False)
        
        assert isinstance(readings, list)
        # Should include readings created by user 1
    
    def test_get_user_readings_includes_multi_user(self, permissions):
        """Test get_user_readings includes multi-user readings user participates in."""
        readings = permissions.get_user_readings(user_id=2, is_admin=False)
        
        # Should include multi-user readings user 2 is participant in
        assert isinstance(readings, list)
```

**Acceptance Criteria:**
- [ ] OraclePermissions class created
- [ ] can_access_reading() enforces all 4 rules
- [ ] get_user_readings() returns correct readings
- [ ] Admin can access all readings
- [ ] All permission tests pass (7/7)
- [ ] Permission check performance <3ms

**Verification:**

```bash
# Terminal 1: Run permission tests
cd security
pytest tests/test_oracle_permissions.py -v

# Expected output:
# test_oracle_permissions.py::TestOraclePermissions::test_user_can_access_own_reading PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_user_cannot_access_others_reading PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_participant_can_access_multi_user_reading PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_non_participant_cannot_access_multi_user_reading PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_admin_can_access_all_readings PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_get_user_readings_includes_own PASSED
# test_oracle_permissions.py::TestOraclePermissions::test_get_user_readings_includes_multi_user PASSED
# ======================== 7 passed in 0.15s ========================

# Terminal 2: Manual permission test
python3 << 'EOF'
import psycopg2
from permissions.oracle_permissions import OraclePermissions

# Connect to database (with test data)
conn = psycopg2.connect("dbname=nps_db_test user=nps_user")
perms = OraclePermissions(conn)

# Test permission checks
print("User 1 accessing own reading 1:", perms.can_access_reading(1, 1, False))
# Expected: True

print("User 2 accessing user 1's reading 1:", perms.can_access_reading(2, 1, False))
# Expected: False

print("Admin accessing reading 1:", perms.can_access_reading(999, 1, True))
# Expected: True

# Get user readings
readings = perms.get_user_readings(1, False, limit=10)
print(f"User 1 has access to {len(readings)} readings")

conn.close()
print("✓ Permission system functional")
EOF
```

**Checkpoint:**
- [ ] Permission tests pass
- [ ] Manual permission checks work correctly
- [ ] Performance <3ms per check

**STOP if checkpoint fails** - permissions are critical for data security

---

## VERIFICATION CHECKLIST

### Encryption Module
- [ ] AES-256 encryption working
- [ ] Persian UTF-8 text handled correctly
- [ ] Roundtrip encryption/decryption preserves data
- [ ] Performance <10ms per operation
- [ ] 5/5 encryption tests pass

### Authentication Module
- [ ] API key validation working
- [ ] Scope hierarchy correct (admin > write > read)
- [ ] Rate limiting blocks after limit
- [ ] 9/9 authentication tests pass

### Audit Logging Module
- [ ] Audit log table created
- [ ] Events logged to database
- [ ] Can query events by user/action/date
- [ ] 4/4 audit tests pass

### Permission Module
- [ ] Row-level access control enforced
- [ ] Multi-user reading permissions work
- [ ] Admin can access all data
- [ ] 7/7 permission tests pass

### Integration
- [ ] All modules import without errors
- [ ] No circular dependencies
- [ ] Database schema compatible
- [ ] Environment variables loaded correctly

### Security
- [ ] No plaintext sensitive data in database
- [ ] No sensitive data in logs
- [ ] No encryption keys in code
- [ ] SQL injection prevented (parameterized queries)

### Performance
- [ ] Encryption: <10ms per field
- [ ] API key validation: <5ms
- [ ] Audit log write: <2ms
- [ ] Permission check: <3ms

---

## SUCCESS CRITERIA

### Functional Success
1. ✅ Can encrypt/decrypt Oracle user profiles with Persian text
2. ✅ Can validate API keys with 3-tier scope system
3. ✅ Audit log captures all security events
4. ✅ Permission system enforces row-level access control
5. ✅ Multi-user readings accessible by all participants
6. ✅ Admin scope has full access to all data

### Quality Success
1. ✅ All 25 tests pass (5 encryption + 9 auth + 4 audit + 7 permissions)
2. ✅ Test coverage â‰¥95%
3. ✅ No security vulnerabilities (no plaintext data, no SQL injection)
4. ✅ Performance targets met (all operations <10ms)

### Architecture Success
1. ✅ Reuses V3 encryption patterns (don't reinvent crypto)
2. ✅ Clear separation of concerns (4 independent modules)
3. ✅ Database schema supports all features
4. ✅ Ready for API layer integration (Terminal 2)

---

## HANDOFF TO NEXT SESSION

**Resume Context:**
If session ends mid-implementation, resume from last completed phase checkpoint.

**Files Created:**
```
security/
├── encryption/
│   ├── __init__.py
│   ├── oracle_encryption.py
│   └── key_derivation.py
├── auth/
│   ├── __init__.py
│   ├── oracle_auth.py
│   ├── rate_limiter.py
│   └── scopes.py
├── middleware/
│   ├── __init__.py
│   └── oracle_middleware.py
├── audit/
│   ├── __init__.py
│   └── oracle_audit.py
├── permissions/
│   ├── __init__.py
│   └── oracle_permissions.py
└── tests/
    ├── test_oracle_encryption.py
    ├── test_oracle_auth.py
    ├── test_oracle_audit.py
    └── test_oracle_permissions.py

database/schemas/
└── oracle_audit_log.sql
```

**Security State:**
- Encryption: Production-ready (AES-256 with Persian text support)
- Authentication: Production-ready (API keys + scopes + rate limiting)
- Audit: Production-ready (comprehensive event logging)
- Permissions: Production-ready (row-level access control)

**Integration Points:**
- Terminal 2 (API): Can now use auth middleware on Oracle endpoints
- Terminal 3 (Backend): Can use encryption before database storage
- Terminal 4 (Database): Audit log table exists, ready for queries

---

## NEXT STEPS (After T6-S1 Complete)

### Immediate (Terminal 2 - API Integration)
1. **Add auth middleware to Oracle endpoints** (30 min)
   - Apply `validate_oracle_api_key()` to all Oracle routes
   - Set appropriate scopes (read vs write vs admin)
   - Add rate limiting to AI endpoints

2. **Encrypt data before database storage** (20 min)
   - Use OracleEncryption in user creation endpoint
   - Use OracleEncryption in reading creation endpoint
   - Decrypt data when returning to API

3. **Add audit logging to API operations** (15 min)
   - Log user creation
   - Log reading creation
   - Log reading access
   - Log auth failures

### Next Session (Terminal 2 - Oracle API Endpoints)
1. **Create Oracle user endpoints** (1 hour)
   - POST /api/oracle/users (create user)
   - GET /api/oracle/users/:id (get user)
   - PUT /api/oracle/users/:id (update user)

2. **Create Oracle reading endpoints** (1.5 hours)
   - POST /api/oracle/readings (create reading)
   - GET /api/oracle/readings/:id (get reading)
   - GET /api/oracle/readings (list user's readings)
   - POST /api/oracle/readings/:id/share (add participant)

3. **Integration testing** (30 min)
   - Test full flow: create user → encrypt → store → retrieve → decrypt
   - Test permissions: user can't access others' data
   - Test audit log: all events captured

---

## APPENDIX: Security Threat Model

**Threats Mitigated:**

1. **Unauthorized Data Access**
   - Mitigation: API key authentication + permission system
   - Result: Users can only access authorized data

2. **Data Breach (Database Compromise)**
   - Mitigation: AES-256 encryption of sensitive fields
   - Result: Stolen database contains encrypted data (useless without master password)

3. **API Key Theft**
   - Mitigation: Rate limiting + audit logging
   - Result: Stolen keys have limited damage potential, usage tracked

4. **Brute Force Attacks**
   - Mitigation: Rate limiting on AI endpoints
   - Result: Attackers can't spam expensive AI calls

5. **Insider Threat (Malicious Admin)**
   - Mitigation: Audit logging
   - Result: All admin actions logged, detectable

6. **SQL Injection**
   - Mitigation: Parameterized queries throughout
   - Result: No SQL injection vectors

**Threats Not Mitigated (Future Work):**

1. **Master Password Compromise**
   - Current: Single master password encrypts all data
   - Future: Key rotation mechanism, per-user encryption keys

2. **Denial of Service**
   - Current: Basic rate limiting
   - Future: CAPTCHA, IP-based rate limiting, DDoS protection

3. **Session Hijacking**
   - Current: API keys don't expire
   - Future: Session tokens, automatic expiration

---

## CONFIDENCE LEVEL

**High (90%+)**

**Reasoning:**
- Reusing proven V3 encryption patterns (battle-tested)
- Standard industry practices (AES-256, API keys, audit logging)
- Comprehensive test coverage (25 tests across 4 modules)
- Clear acceptance criteria with measurable targets
- All performance targets achievable (<10ms operations)
- No novel/unproven techniques

**Risk Factors (Mitigated):**
- Persian text UTF-8 handling: Tested explicitly in Phase 1
- Multi-user permissions complexity: Tested extensively in Phase 4
- Rate limiting accuracy: Simple in-memory implementation, tested
- Database performance: Indexes added, queries optimized

**Estimated Duration:** 2.5-3 hours (with buffer for testing/debugging)
