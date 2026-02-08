# NPS V4 API Reference

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints (except health) require authentication via one of:

- **Legacy token:** `Authorization: Bearer <API_SECRET_KEY>` — grants admin access
- **JWT token:** `Authorization: Bearer <jwt>` — from POST /api/auth/login
- **API key:** `Authorization: Bearer <api_key>` — hashed against api_keys table

## Working Endpoints (Oracle)

### Health

#### `GET /api/health`

Basic health check. **No auth required.**

```json
// Response 200
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "scanner_service": "not_deployed",
  "oracle_service": "direct_mode"
}
```

---

### Oracle Users

#### `POST /api/oracle/users`

Create a new Oracle user profile.

**Scope:** `oracle:write`

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
  "created_at": "2026-02-08T12:00:00Z",
  "updated_at": "2026-02-08T12:00:00Z"
}
```

#### `GET /api/oracle/users`

List Oracle user profiles.

**Scope:** `oracle:read`
**Query params:** `limit` (1-100, default 20), `offset` (default 0), `search` (name filter)

```json
// Response 200
{
  "users": [...],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/oracle/users/{user_id}`

Get a specific user profile.

**Scope:** `oracle:read`

#### `PUT /api/oracle/users/{user_id}`

Update a user profile (partial update).

**Scope:** `oracle:write`

```json
// Request (only changed fields)
{ "city": "Los Angeles" }

// Response 200: updated user object
```

#### `DELETE /api/oracle/users/{user_id}`

Soft-delete a user profile.

**Scope:** `oracle:admin`

Returns the deleted user object. User is excluded from future queries.

---

### Oracle Readings

#### `POST /api/oracle/reading`

Get a full oracle reading (FC60 + numerology + zodiac + Chinese).

**Scope:** `oracle:write`

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

#### `POST /api/oracle/question`

Ask a yes/no question with numerological context.

**Scope:** `oracle:write`

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

#### `POST /api/oracle/name`

Get a name cipher reading.

**Scope:** `oracle:write`

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

#### `GET /api/oracle/daily`

Get daily insight.

**Scope:** `oracle:read`
**Query params:** `date` (YYYY-MM-DD, default today)

```json
// Response 200
{
  "date": "2026-02-08",
  "insight": "...",
  "lucky_numbers": ["3", "7", "11"],
  "optimal_activity": "..."
}
```

#### `POST /api/oracle/suggest-range`

Get AI-suggested scan range.

**Scope:** `oracle:write`

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

#### `POST /api/oracle/reading/multi-user`

Multi-user FC60 analysis with compatibility.

**Scope:** `oracle:write`

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

---

### Reading History

#### `GET /api/oracle/readings`

List stored oracle readings.

**Scope:** `oracle:read`
**Query params:** `limit`, `offset`, `sign_type`

#### `GET /api/oracle/readings/{reading_id}`

Get a specific stored reading.

**Scope:** `oracle:read`

---

### Audit Log

#### `GET /api/oracle/audit`

Query Oracle audit log.

**Scope:** `oracle:admin`
**Query params:** `action`, `resource_id`, `limit`, `offset`

---

### WebSocket

#### `WS /api/oracle/ws`

Oracle progress updates via WebSocket.

---

## Stub Endpoints (Return 501)

These endpoints are scaffolded but not yet implemented:

- Scanner: `POST /api/scanner/start`, `/stop`, `/pause`, `/resume`, `GET /stats`, `/terminals`
- Vault: `GET /api/vault/findings`, `/summary`, `/search`, `POST /export`
- Learning: `GET /api/learning/stats`, `/insights`, `/weights`, `/patterns`, `POST /analyze`

## Error Format

```json
{
  "detail": "Human-readable error message"
}
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
