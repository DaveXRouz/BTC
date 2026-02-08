# V4 REST API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints require authentication unless noted otherwise. Use either:

- **JWT Bearer token:** `Authorization: Bearer <token>`
- **API key:** `X-API-Key: <key>`

---

## Health

### `GET /health`

Basic health check. **No auth required.**

**Response:**

```json
{ "status": "healthy", "version": "4.0.0" }
```

### `GET /health/ready`

Readiness probe — checks database and service connectivity.

**Response:**

```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "scanner_service": "healthy",
    "oracle_service": "healthy"
  }
}
```

### `GET /health/performance`

Performance metrics.

**Response:**

```json
{
  "uptime_seconds": 3600,
  "requests_total": 1500,
  "requests_per_minute": 25,
  "p95_response_ms": 45
}
```

---

## Authentication

### `POST /auth/login`

Authenticate and receive JWT tokens.

**Request:**

```json
{
  "username": "admin",
  "password": "secret"
}
```

**Response:**

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `POST /auth/api-keys`

Create a new API key.

**Request:**

```json
{
  "name": "telegram-bot",
  "expires_in_days": 365
}
```

**Response:**

```json
{
  "id": "uuid",
  "name": "telegram-bot",
  "key": "nps_...",
  "created_at": "2026-02-08T00:00:00Z"
}
```

### `GET /auth/api-keys`

List API keys for the current user.

### `DELETE /auth/api-keys/{key_id}`

Revoke an API key.

---

## Scanner

### `POST /scanner/start`

Start a new scan session.

**Request:**

```json
{
  "mode": "random_key",
  "chains": ["btc", "eth"],
  "batch_size": 1000,
  "check_every_n": 100,
  "threads": 4,
  "checkpoint_interval": 10000,
  "puzzle": {
    "puzzle_number": 66,
    "range_start": "20000000000000000",
    "range_end": "3ffffffffffffffff"
  }
}
```

**Response:**

```json
{
  "session_id": "uuid",
  "status": "running",
  "config": {...},
  "started_at": "2026-02-08T00:00:00Z"
}
```

### `POST /scanner/stop/{session_id}`

Stop a running scan session with automatic checkpoint.

### `POST /scanner/pause/{session_id}`

Pause a running scan session.

### `POST /scanner/resume/{session_id}`

Resume a paused scan session.

### `GET /scanner/stats/{session_id}`

Get real-time stats for a scan session.

**Response:**

```json
{
  "session_id": "uuid",
  "keys_tested": 1500000,
  "seeds_tested": 0,
  "hits": 0,
  "keys_per_second": 12500.5,
  "elapsed_seconds": 120.0,
  "checkpoint_count": 15,
  "current_mode": "random_key",
  "highest_score": 0.82
}
```

### `GET /scanner/terminals`

List all active scan sessions.

### `POST /scanner/checkpoint/{session_id}`

Force a checkpoint save.

---

## Oracle

### `POST /oracle/reading`

Get a full oracle reading.

**Request:**

```json
{
  "datetime": "2026-02-08T12:00:00Z",
  "extended": true
}
```

**Response:**

```json
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
    "element_balance": {
      "fire": 0.3,
      "earth": 0.2,
      "metal": 0.15,
      "water": 0.15,
      "wood": 0.2
    }
  },
  "numerology": {
    "life_path": 7,
    "day_vibration": 8,
    "personal_year": 3,
    "personal_month": 5,
    "personal_day": 2,
    "interpretation": "..."
  },
  "zodiac": { "sign": "Aquarius", "element": "Air", "ruling_planet": "Uranus" },
  "chinese": { "animal": "Horse", "element": "Fire", "yin_yang": "Yang" },
  "summary": "...",
  "generated_at": "2026-02-08T12:00:00Z"
}
```

### `POST /oracle/question`

Ask a yes/no question with numerological context.

**Request:**

```json
{
  "question": "Is today a good day for scanning?"
}
```

**Response:**

```json
{
  "question": "Is today a good day for scanning?",
  "answer": "yes",
  "sign_number": 7,
  "interpretation": "...",
  "confidence": 0.85
}
```

### `POST /oracle/name`

Get a name cipher reading.

**Request:**

```json
{
  "name": "Satoshi Nakamoto"
}
```

**Response:**

```json
{
  "name": "Satoshi Nakamoto",
  "destiny_number": 1,
  "soul_urge": 6,
  "personality": 4,
  "letters": [
    { "letter": "S", "value": 1, "element": "Fire" },
    { "letter": "a", "value": 1, "element": "Fire" }
  ],
  "interpretation": "..."
}
```

### `GET /oracle/daily?date=2026-02-08`

Get daily insight. Defaults to today if no date provided.

### `POST /oracle/suggest-range`

Get AI-suggested scan range.

**Request:**

```json
{
  "scanned_ranges": ["20000000000000000-20000000000100000"],
  "puzzle_number": 66,
  "ai_level": 3
}
```

**Response:**

```json
{
  "range_start": "20000000000100000",
  "range_end": "20000000000200000",
  "strategy": "sequential",
  "confidence": 0.72,
  "reasoning": "Continuing from last scanned position with gap-fill strategy"
}
```

---

## Vault

### `GET /vault/findings`

Get vault findings with pagination and filtering.

**Query params:** `limit` (default 100), `offset` (default 0), `chain`, `min_balance`, `min_score`

### `GET /vault/summary`

Get vault summary statistics.

**Response:**

```json
{
  "total": 150,
  "with_balance": 3,
  "by_chain": { "btc": 80, "eth": 70 },
  "sessions": 25
}
```

### `GET /vault/search?q=1A1z`

Search findings by address or metadata.

### `POST /vault/export`

Export vault data.

**Request:**

```json
{
  "format": "csv"
}
```

---

## Learning

### `GET /learning/stats`

Get current AI level, XP, and capabilities.

**Response:**

```json
{
  "level": 3,
  "name": "Adept",
  "xp": 450,
  "xp_next": 500,
  "capabilities": [
    "Basic scanning",
    "Pattern detection",
    "Strategy suggestions"
  ]
}
```

### `GET /learning/insights?limit=10`

Get stored AI insights.

### `POST /learning/analyze`

Trigger AI analysis of a completed session.

**Request:**

```json
{
  "session_id": "uuid",
  "model": "claude"
}
```

### `GET /learning/weights`

Get current scoring weights configuration.

### `GET /learning/patterns`

Get detected patterns from scanning history.

---

## WebSocket

### `WS /ws`

Real-time event stream. Authenticated via query parameter: `/ws?token=<jwt>`

**Event types:**

```json
{"type": "scan_progress", "data": {"session_id": "...", "keys_tested": 1500000, "kps": 12500}}
{"type": "finding", "data": {"address": "1...", "chain": "btc", "balance": 0.001}}
{"type": "high_score", "data": {"address": "1...", "score": 0.95}}
{"type": "checkpoint", "data": {"session_id": "...", "keys_at": 1500000}}
{"type": "level_up", "data": {"level": 4, "name": "Expert"}}
{"type": "health", "data": {"service": "scanner", "status": "healthy"}}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "SCANNER_NOT_CONNECTED",
  "status_code": 503
}
```

Common status codes:

- `400` — Invalid request parameters
- `401` — Missing or invalid authentication
- `403` — Insufficient permissions
- `404` — Resource not found
- `429` — Rate limit exceeded
- `501` — Service not yet implemented (Phase 0 stubs)
- `503` — Backend service unavailable
