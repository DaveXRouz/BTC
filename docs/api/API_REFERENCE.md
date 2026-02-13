# NPS API Reference

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints (except health) require authentication via one of:

- **Legacy token:** `Authorization: Bearer <API_SECRET_KEY>` — grants admin access
- **JWT token:** `Authorization: Bearer <jwt>` — from `POST /api/auth/login`
- **API key:** `Authorization: Bearer <api_key>` — hashed against `api_keys` table

### Scopes

| Scope          | Description                     |
| -------------- | ------------------------------- |
| `admin`        | Full system access              |
| `moderator`    | User management + oracle access |
| `oracle:read`  | Read oracle data                |
| `oracle:write` | Create readings and profiles    |
| `oracle:admin` | Oracle admin operations         |

---

## Health (`/api/health`)

### `GET /api/health`

Basic health check. **No auth required.** Use for load balancer health checks.

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "scanner_service": "not_deployed",
  "oracle_service": "direct_mode"
}
```

### `GET /api/health/ready`

Readiness probe. **No auth required.**

### `GET /api/health/detailed`

Full system status with versions, uptime, and component health. **Admin only.**

### `GET /api/health/performance`

Performance metrics (response times, throughput). **Admin only.**

### `GET /api/health/logs`

Recent application logs. **Admin only.**
Query params: `limit`, `level`

### `GET /api/health/analytics`

Usage analytics and statistics. **Admin only.**

---

## Auth (`/api/auth`)

### `POST /api/auth/login`

Authenticate and receive JWT tokens.

```json
// Request
{
  "username": "admin",
  "password": "password"
}

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": { "id": 1, "username": "admin", "role": "admin" }
}
```

### `POST /api/auth/register`

Register a new user account.

```json
// Request
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword"
}

// Response 201
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "role": "user"
}
```

### `POST /api/auth/refresh`

Refresh an expired access token.

```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "access_token": "eyJ...", "expires_in": 86400 }
```

### `POST /api/auth/logout`

Invalidate the current session.

### `POST /api/auth/change-password`

Change the authenticated user's password.

```json
// Request
{ "current_password": "old", "new_password": "new" }
```

### `POST /api/auth/api-keys`

Create a new API key. **Admin only.** The plaintext key is shown only once at creation.

```json
// Response 201
{
  "id": 1,
  "name": "my-key",
  "key": "nps_abc123...",
  "scopes": ["oracle:read", "oracle:write"],
  "created_at": "2026-02-14T00:00:00Z"
}
```

### `GET /api/auth/api-keys`

List all API keys (without plaintext values). **Admin only.**

### `DELETE /api/auth/api-keys/{key_id}`

Revoke an API key. **Admin only.**

---

## Oracle Users (`/api/oracle/users`)

### `POST /api/oracle/users`

Create a new Oracle user profile. **Scope:** `oracle:write`

```json
// Request
{
  "name": "John Doe",
  "name_persian": "جان دو",
  "birthday": "1990-06-15",
  "mother_name": "Jane Doe",
  "mother_name_persian": "جین دو",
  "country": "US",
  "city": "New York"
}

// Response 201
{
  "id": 1,
  "name": "John Doe",
  "name_persian": "جان دو",
  "birthday": "1990-06-15",
  "mother_name": "Jane Doe",
  "mother_name_persian": "جین دو",
  "country": "US",
  "city": "New York",
  "created_at": "2026-02-14T12:00:00Z",
  "updated_at": "2026-02-14T12:00:00Z"
}
```

### `GET /api/oracle/users`

List Oracle user profiles. **Scope:** `oracle:read`
Query params: `limit` (1-100, default 20), `offset` (default 0), `search` (name filter)

```json
// Response 200
{
  "users": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

### `GET /api/oracle/users/{user_id}`

Get a specific user profile. **Scope:** `oracle:read`

### `PUT /api/oracle/users/{user_id}`

Update a user profile (partial update). **Scope:** `oracle:write`

```json
// Request (only changed fields)
{ "city": "Los Angeles" }

// Response 200: updated user object
```

### `DELETE /api/oracle/users/{user_id}`

Soft-delete a user profile. **Scope:** `oracle:admin`

---

## Oracle Readings (`/api/oracle`)

### `POST /api/oracle/reading`

Get a full oracle reading (FC60 + numerology + zodiac + Chinese zodiac). **Scope:** `oracle:write`

```json
// Request
{
  "datetime": "2024-06-15T14:30:00+00:00",
  "extended": false
}

// Response 200
{
  "fc60": {
    "cycle": 43,
    "element": "Fire",
    "polarity": "Yang",
    "stem": "Bing",
    "branch": "Wu",
    "year_number": 7,
    "month_number": 3,
    "day_number": 9,
    "energy_level": 0.85,
    "element_balance": { "Wood": 0.2, "Fire": 0.4, "Earth": 0.2, "Metal": 0.1, "Water": 0.1 }
  },
  "numerology": {
    "life_path": 7,
    "day_vibration": 8,
    "personal_year": 3,
    "personal_month": 5,
    "personal_day": 2,
    "interpretation": "The Seeker: You are on a path of knowledge and understanding"
  },
  "zodiac": { "sign": "Gemini", "element": "Air", "ruling_planet": "Mercury" },
  "chinese": { "animal": "Horse", "element": "Fire", "yin_yang": "Yang" },
  "summary": "...",
  "generated_at": "2024-06-15T14:30:00+00:00"
}
```

### `POST /api/oracle/question`

Ask a yes/no question with numerological context. **Scope:** `oracle:write`

```json
// Request
{ "question": "Is today a good day for important decisions?" }

// Response 200
{
  "question": "Is today a good day for important decisions?",
  "answer": "yes",
  "sign_number": 7,
  "interpretation": "...",
  "confidence": 0.7
}
```

### `POST /api/oracle/name`

Get a name cipher reading (Pythagorean numerology). **Scope:** `oracle:write`

```json
// Request
{ "name": "Satoshi Nakamoto" }

// Response 200
{
  "name": "Satoshi Nakamoto",
  "destiny_number": 1,
  "soul_urge": 6,
  "personality": 4,
  "letters": [
    { "letter": "S", "value": 1, "element": "Fire" },
    { "letter": "A", "value": 1, "element": "Fire" }
  ],
  "interpretation": "..."
}
```

### `GET /api/oracle/daily`

Get daily oracle insight. **Scope:** `oracle:read`
Query params: `date` (YYYY-MM-DD, default today)

```json
// Response 200
{
  "date": "2026-02-14",
  "insight": "...",
  "lucky_numbers": ["3", "7", "11"],
  "optimal_activity": "..."
}
```

### `POST /api/oracle/suggest-range`

Get AI-suggested scan range for Bitcoin puzzle. **Scope:** `oracle:write`

```json
// Request
{
  "scanned_ranges": ["20000000000000000-20000000000100000"],
  "puzzle_number": 66,
  "ai_level": 3
}

// Response 200
{
  "range_start": "0x20000000000000000",
  "range_end": "0x3ffffffffffffffff",
  "strategy": "cosmic",
  "confidence": 0.8,
  "reasoning": "..."
}
```

### `POST /api/oracle/validate-stamp`

Validate a cosmic stamp value. **Scope:** `oracle:write`

### `POST /api/oracle/reading/multi-user`

Multi-user FC60 analysis with compatibility. **Scope:** `oracle:write`

```json
// Request
{
  "users": [
    { "name": "Alice", "birth_year": 1990, "birth_month": 3, "birth_day": 15 },
    { "name": "Bob", "birth_year": 1985, "birth_month": 7, "birth_day": 22 }
  ],
  "primary_user_index": 0,
  "include_interpretation": true
}

// Response 200
{
  "user_count": 2,
  "profiles": [...],
  "pairwise_compatibility": [...],
  "group_energy": {...},
  "ai_interpretation": {...},
  "reading_id": 42
}
```

### `POST /api/oracle/readings`

Store a reading result. **Scope:** `oracle:write`

### `GET /api/oracle/daily/reading`

Get daily reading with full analysis. **Scope:** `oracle:read`

### `GET /api/oracle/stats`

Oracle statistics and usage data. **Scope:** `oracle:read`

---

## Reading History (`/api/oracle/readings`)

### `GET /api/oracle/readings`

List stored oracle readings. **Scope:** `oracle:read`
Query params: `limit`, `offset`, `sign_type`

### `GET /api/oracle/readings/stats`

Reading statistics. **Scope:** `oracle:read`

### `GET /api/oracle/readings/{reading_id}`

Get a specific stored reading. **Scope:** `oracle:read`

### `DELETE /api/oracle/readings/{reading_id}`

Delete a reading. **Scope:** `oracle:admin`

### `PATCH /api/oracle/readings/{reading_id}/favorite`

Toggle reading favorite status. **Scope:** `oracle:write`

---

## Audit Log (`/api/oracle/audit`)

### `GET /api/oracle/audit`

Query Oracle audit log. **Scope:** `oracle:admin`
Query params: `action`, `resource_id`, `limit`, `offset`

---

## Admin (`/api/admin`)

### `GET /api/admin/users`

List all system users with role info. **Scope:** `admin`
Query params: `limit`, `offset`, `role`, `search`

### `GET /api/admin/users/{user_id}`

Get detailed user info. **Scope:** `admin`

### `PATCH /api/admin/users/{user_id}/role`

Change a user's role. **Scope:** `admin`

### `POST /api/admin/users/{user_id}/reset-password`

Admin-initiated password reset. **Scope:** `admin`

### `PATCH /api/admin/users/{user_id}/status`

Activate/deactivate a user. **Scope:** `admin`

### `GET /api/admin/stats`

System-wide statistics. **Scope:** `admin`

### `GET /api/admin/profiles`

List all oracle profiles. **Scope:** `admin`

### `DELETE /api/admin/profiles/{profile_id}`

Delete an oracle profile. **Scope:** `admin`

### `GET /api/admin/backups`

List database backups. **Scope:** `admin`

### `POST /api/admin/backups`

Trigger a database backup. **Scope:** `admin`

### `POST /api/admin/backups/restore`

Restore from a backup. **Scope:** `admin`

### `DELETE /api/admin/backups/{filename}`

Delete a backup file. **Scope:** `admin`

---

## System Users (`/api/users`)

### `GET /api/users`

List system users. **Scope:** `admin`
Query params: `limit`, `offset`, `role`, `search`

### `GET /api/users/{user_id}`

Get system user details. **Scope:** `admin`

### `PUT /api/users/{user_id}`

Update system user. **Scope:** `admin`

### `DELETE /api/users/{user_id}`

Delete system user. **Scope:** `admin`

### `POST /api/users/{user_id}/reset-password`

Reset user password. **Scope:** `admin`

### `PUT /api/users/{user_id}/role`

Change user role. **Scope:** `admin`

---

## Telegram (`/api/telegram`)

### `POST /api/telegram/link`

Link a Telegram chat to a user account.

### `GET /api/telegram/status/{chat_id}`

Get Telegram user link status.

### `DELETE /api/telegram/link/{chat_id}`

Unlink a Telegram chat.

### `GET /api/telegram/profile/{chat_id}`

Get oracle profile for a linked Telegram user.

### `GET /api/telegram/daily/preferences/{chat_id}`

Get daily digest preferences.

### `PUT /api/telegram/daily/preferences/{chat_id}`

Update daily digest preferences.

### `GET /api/telegram/daily/pending`

List pending daily digest deliveries. **Service key required.**

### `POST /api/telegram/daily/delivered`

Mark daily digest as delivered. **Service key required.**

### `GET /api/telegram/admin/stats`

Telegram usage statistics. **Scope:** `admin`

### `GET /api/telegram/admin/users`

List Telegram-linked users. **Scope:** `admin`

### `GET /api/telegram/admin/linked_chats`

List all linked chat IDs. **Scope:** `admin`

### `POST /api/telegram/admin/audit`

Query Telegram audit log. **Scope:** `admin`

### `POST /api/telegram/internal/notify`

Send internal notification. **Service key required.**

---

## Translation (`/api/translation`)

### `POST /api/translation/translate`

Translate text between languages.

### `POST /api/translation/reading`

Translate a reading result.

### `POST /api/translation/batch`

Batch translate multiple texts.

### `GET /api/translation/detect`

Detect text language.

### `GET /api/translation/cache/stats`

Translation cache statistics.

---

## Location (`/api/location`)

### `GET /api/location/countries`

List available countries.

### `GET /api/location/countries/{country_code}/cities`

List cities for a country.

### `GET /api/location/timezone`

Get timezone for coordinates.

### `GET /api/location/coordinates`

Get coordinates for a location.

### `GET /api/location/detect`

Detect location from IP.

---

## Share (`/api/share`)

### `POST /api/share`

Create a shareable link for a reading. Returns a unique token.

```json
// Request
{ "reading_id": 42, "expires_hours": 72 }

// Response 201
{
  "token": "abc123...",
  "url": "https://your-domain.com/share/abc123...",
  "expires_at": "2026-02-17T00:00:00Z"
}
```

### `GET /api/share/{token}`

Get shared reading data. **No auth required** (public link).

### `DELETE /api/share/{token}`

Revoke a shared link.

---

## Settings (`/api/settings`)

### `GET /api/settings`

Get application settings. **Scope:** `admin`

### `PUT /api/settings`

Update application settings. **Scope:** `admin`

---

## Learning (`/api/learning`)

### `GET /api/learning/stats`

Learning system statistics. **Stub — returns 501.**

### `GET /api/learning/insights`

AI-generated insights. **Stub — returns 501.**

### `POST /api/learning/analyze`

Analyze a scanning session. **Stub — returns 501.**

### `GET /api/learning/weights`

Model weights. **Stub — returns 501.**

### `GET /api/learning/patterns`

Discovered patterns. **Stub — returns 501.**

### `POST /api/learning/oracle/readings/{reading_id}/feedback`

Submit feedback for an oracle reading.

### `GET /api/learning/oracle/readings/{reading_id}/feedback`

Get feedback for a reading.

### `GET /api/learning/oracle/stats`

Oracle learning statistics.

### `POST /api/learning/oracle/recalculate`

Trigger model recalculation.

---

## Scanner (`/api/scanner`) — Stub, returns 501

### `POST /api/scanner/start`

### `POST /api/scanner/stop/{session_id}`

### `POST /api/scanner/pause/{session_id}`

### `POST /api/scanner/resume/{session_id}`

### `GET /api/scanner/stats/{session_id}`

### `GET /api/scanner/terminals`

### `POST /api/scanner/checkpoint/{session_id}`

---

## Vault (`/api/vault`) — Stub, returns 501

### `GET /api/vault/findings`

### `GET /api/vault/summary`

### `GET /api/vault/search`

### `POST /api/vault/export`

---

## WebSocket

### `WS /api/oracle/ws`

Real-time oracle reading progress updates.

---

## Error Format

```json
{ "detail": "Human-readable error message" }
```

| Code | Meaning                                   |
| ---- | ----------------------------------------- |
| 400  | Invalid request parameters                |
| 401  | Missing authentication                    |
| 403  | Invalid credentials or insufficient scope |
| 404  | Resource not found                        |
| 409  | Conflict (duplicate resource)             |
| 422  | Validation error                          |
| 429  | Rate limit exceeded                       |
| 500  | Internal server error                     |
| 501  | Not implemented (stub)                    |

---

## Rate Limits

| Endpoint Group | Rate   | Burst |
| -------------- | ------ | ----- |
| `/api/auth/*`  | 5/sec  | 10    |
| `/api/*`       | 30/sec | 50    |

Rate limits are enforced by nginx. Exceeding limits returns `429 Too Many Requests`.
