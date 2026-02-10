# SESSION 17 SPEC — Reading History & Persistence

> **Block:** AI & Reading Types (Sessions 13-18)
> **Session:** 17 of 45
> **Duration:** ~5 hours
> **Complexity:** Medium-High
> **Dependencies:** Sessions 14-16 (all reading flows: time, name, question, daily)
> **Spec version:** 1.0
> **Created:** 2026-02-10

---

## TL;DR

- Add soft delete, favorites, full-text search, and statistics to reading history system
- Create database migration `014_reading_search.sql` for `is_favorite`, `deleted_at`, `search_vector` (tsvector) columns with trigger + GIN index
- Expand API: `DELETE /readings/{id}` (soft delete), `GET /readings/stats`, `PATCH /readings/{id}/favorite`, plus search + date-range + favorites filters on existing list endpoint
- Rewrite `ReadingHistory.tsx` from accordion list to card-based grid with search bar, date range, favorites toggle, pagination with page numbers
- Create `ReadingCard.tsx` (card component) and `ReadingDetail.tsx` (full detail modal/panel)
- 25 tests across backend (11) and frontend (14)

---

## Objectives

1. **Database schema expansion** — Add `is_favorite BOOLEAN`, `deleted_at TIMESTAMPTZ`, and `search_vector TSVECTOR` columns to `oracle_readings` table via migration `014_reading_search.sql`, with auto-populating trigger and GIN index
2. **Soft delete API** — Create `DELETE /api/oracle/readings/{id}` that sets `deleted_at` timestamp instead of removing the row; all list/search endpoints filter out deleted readings
3. **Full-text search** — Implement PostgreSQL tsvector search across `question`, `question_persian`, `ai_interpretation`, and `ai_interpretation_persian` fields using both `english` and `simple` dictionaries
4. **Reading statistics** — Create `GET /api/oracle/readings/stats` returning count by type, by month, favorites count, and most active day
5. **Favorites toggle** — Create `PATCH /api/oracle/readings/{id}/favorite` to toggle `is_favorite`, with frontend star icon and filter
6. **Frontend rewrite** — Replace accordion-based `ReadingHistory.tsx` with card grid using new `ReadingCard.tsx` and `ReadingDetail.tsx` components, supporting search, date range, type filter, favorites toggle, and page-number pagination

---

## Prerequisites

### Required Sessions Complete

| Session | What It Provides                   | Verify Command                                                                                                                                                          |
| ------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 14      | Time reading flow stored in DB     | `curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"datetime":"2026-02-10T14:30:00"}' http://localhost:8000/api/oracle/reading`   |
| 15      | Name reading flow stored in DB     | `curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Alice"}' http://localhost:8000/api/oracle/name`                        |
| 16      | Question reading flow stored in DB | `curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"question":"Will today be lucky?"}' http://localhost:8000/api/oracle/question` |

### Infrastructure

- PostgreSQL running with `oracle_readings` table populated (at least a few test readings)
- API server running on port 8000
- Frontend dev server running on port 5173

### Verify Existing Endpoints

```bash
# List readings (must return paginated results)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings | python3 -m json.tool

# Get single reading (must return reading object)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/1 | python3 -m json.tool
```

---

## Files to Create

| #   | Path                                                              | Purpose                                                                   | Est. Lines |
| --- | ----------------------------------------------------------------- | ------------------------------------------------------------------------- | ---------- |
| 1   | `database/migrations/014_reading_search.sql`                      | Migration: add is_favorite, deleted_at, search_vector + trigger + indexes | ~60        |
| 2   | `database/migrations/014_reading_search_rollback.sql`             | Rollback migration                                                        | ~15        |
| 3   | `frontend/src/components/oracle/ReadingCard.tsx`                  | Card component for reading history items                                  | ~110       |
| 4   | `frontend/src/components/oracle/ReadingDetail.tsx`                | Full detail view for a selected reading                                   | ~150       |
| 5   | `frontend/src/components/oracle/__tests__/ReadingCard.test.tsx`   | ReadingCard unit tests                                                    | ~120       |
| 6   | `frontend/src/components/oracle/__tests__/ReadingDetail.test.tsx` | ReadingDetail unit tests                                                  | ~100       |

---

## Files to Modify

| #   | Path                                                               | What Changes                                                                                                 | Est. Delta          |
| --- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ------------------- |
| 1   | `api/app/orm/oracle_reading.py`                                    | Add `is_favorite`, `deleted_at` mapped columns                                                               | +6 lines            |
| 2   | `api/app/models/oracle.py`                                         | Add fields to `StoredReadingResponse`, new `ReadingStatsResponse` model                                      | +35 lines           |
| 3   | `api/app/routers/oracle.py`                                        | Add DELETE, stats, favorite endpoints; expand list_readings with search/date/favorites params                | +95 lines           |
| 4   | `api/app/services/oracle_reading.py`                               | Add `soft_delete_reading`, `toggle_favorite`, `search_readings`, `get_reading_stats`; update `list_readings` | +120 lines          |
| 5   | `frontend/src/types/index.ts`                                      | Add `is_favorite`, `deleted_at` to `StoredReading`; new `ReadingStats` interface                             | +20 lines           |
| 6   | `frontend/src/services/api.ts`                                     | Add `deleteReading`, `toggleFavorite`, `readingStats`; expand `history` params                               | +25 lines           |
| 7   | `frontend/src/hooks/useOracleReadings.ts`                          | Add `useDeleteReading`, `useToggleFavorite`, `useReadingStats` hooks; expand `useReadingHistory` params      | +40 lines           |
| 8   | `frontend/src/components/oracle/ReadingHistory.tsx`                | REWRITE: accordion list -> card grid with search, date range, favorites, pagination                          | ~200 (full rewrite) |
| 9   | `frontend/src/components/oracle/__tests__/ReadingHistory.test.tsx` | Expand from 6 to 14 tests (add search, date, favorites, detail, pagination, stats tests)                     | +140 lines          |
| 10  | `frontend/src/locales/en.json`                                     | Add ~20 new reading history i18n keys                                                                        | +20 lines           |
| 11  | `frontend/src/locales/fa.json`                                     | Add matching Persian translations                                                                            | +20 lines           |

---

## Files to Delete

None.

---

## Implementation Phases

### Phase 1: Database Migration (~30 min)

**Goal:** Add `is_favorite`, `deleted_at`, and `search_vector` columns with trigger and indexes.

#### 1a: Create `database/migrations/014_reading_search.sql`

```sql
-- Migration 014: Reading search, favorites, and soft delete
-- Depends on: 010_oracle_schema.sql

-- 1. Add new columns
ALTER TABLE oracle_readings
  ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS search_vector TSVECTOR;

-- 2. Auto-populate search_vector trigger
CREATE OR REPLACE FUNCTION oracle_readings_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.question, '')), 'A') ||
    setweight(to_tsvector('simple', COALESCE(NEW.question_persian, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.ai_interpretation, '')), 'B') ||
    setweight(to_tsvector('simple', COALESCE(NEW.ai_interpretation_persian, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(NEW.sign_value, '')), 'C');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_oracle_readings_search
  BEFORE INSERT OR UPDATE ON oracle_readings
  FOR EACH ROW EXECUTE FUNCTION oracle_readings_search_update();

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_readings_search ON oracle_readings USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_oracle_readings_favorite ON oracle_readings(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_oracle_readings_deleted ON oracle_readings(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_oracle_readings_stats ON oracle_readings(sign_type, created_at) WHERE deleted_at IS NULL;

-- 4. Backfill existing rows
UPDATE oracle_readings SET search_vector =
  setweight(to_tsvector('english', COALESCE(question, '')), 'A') ||
  setweight(to_tsvector('simple', COALESCE(question_persian, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(ai_interpretation, '')), 'B') ||
  setweight(to_tsvector('simple', COALESCE(ai_interpretation_persian, '')), 'B') ||
  setweight(to_tsvector('english', COALESCE(sign_value, '')), 'C')
WHERE search_vector IS NULL;
```

**Key design decisions:**

- `english` dictionary for English fields (handles stemming: "running" -> "run")
- `simple` dictionary for Persian fields (no stemming; Persian morphology too complex for built-in dictionaries)
- Weight A for question text (highest relevance), B for interpretation, C for sign value
- Partial indexes on `is_favorite` and `deleted_at` for efficient filtering
- Composite stats index for fast GROUP BY queries

#### 1b: Create `database/migrations/014_reading_search_rollback.sql`

```sql
DROP TRIGGER IF EXISTS trg_oracle_readings_search ON oracle_readings;
DROP FUNCTION IF EXISTS oracle_readings_search_update();
DROP INDEX IF EXISTS idx_oracle_readings_search;
DROP INDEX IF EXISTS idx_oracle_readings_favorite;
DROP INDEX IF EXISTS idx_oracle_readings_deleted;
DROP INDEX IF EXISTS idx_oracle_readings_stats;
ALTER TABLE oracle_readings
  DROP COLUMN IF EXISTS search_vector,
  DROP COLUMN IF EXISTS deleted_at,
  DROP COLUMN IF EXISTS is_favorite;
```

#### STOP Checkpoint 1

```bash
# Run migration
psql -U nps -d nps -f database/migrations/014_reading_search.sql

# Verify columns exist
psql -U nps -d nps -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'oracle_readings' AND column_name IN ('is_favorite', 'deleted_at', 'search_vector');"
# Expected: 3 rows

# Verify trigger exists
psql -U nps -d nps -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table = 'oracle_readings' AND trigger_name = 'trg_oracle_readings_search';"
# Expected: 1 row

# Verify GIN index exists
psql -U nps -d nps -c "SELECT indexname FROM pg_indexes WHERE tablename = 'oracle_readings' AND indexname = 'idx_oracle_readings_search';"
# Expected: 1 row

# Verify backfill worked (if readings exist)
psql -U nps -d nps -c "SELECT id, search_vector IS NOT NULL AS has_vector FROM oracle_readings LIMIT 5;"
# Expected: all has_vector = true
```

**Do NOT proceed to Phase 2 until all 4 checks pass.**

---

### Phase 2: ORM + Pydantic Models (~20 min)

**Goal:** Update Python models to reflect new database columns and add response types.

#### 2a: Update `api/app/orm/oracle_reading.py`

Add to `OracleReading` class (after `created_at` field):

```python
is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
```

**Note:** Do NOT map `search_vector` — it's managed by the database trigger and never read/written by the ORM directly. Search queries will use raw SQL or `text()` for the tsvector match.

#### 2b: Update `api/app/models/oracle.py`

Add to `StoredReadingResponse`:

```python
is_favorite: bool = False
deleted_at: str | None = None
```

Add new model after `StoredReadingListResponse`:

```python
class ReadingStatsResponse(BaseModel):
    total_readings: int
    by_type: dict[str, int]  # {"time": 15, "name": 8, "question": 22}
    by_month: list[dict]  # [{"month": "2026-01", "count": 12}, ...]
    favorites_count: int
    most_active_day: str | None  # "Monday", "Tuesday", etc.
```

#### STOP Checkpoint 2

```bash
# Verify ORM loads without errors
cd api && python3 -c "from app.orm.oracle_reading import OracleReading; print('ORM OK')"

# Verify models load without errors
cd api && python3 -c "from app.models.oracle import ReadingStatsResponse, StoredReadingResponse; print('Models OK')"
```

**Do NOT proceed to Phase 3 until both checks pass.**

---

### Phase 3: Service Layer (~40 min)

**Goal:** Add search, delete, favorite, and stats methods to `OracleReadingService`.

#### 3a: Add `soft_delete_reading()` to `OracleReadingService`

```python
def soft_delete_reading(self, reading_id: int) -> bool:
    """Soft-delete a reading by setting deleted_at timestamp."""
    row = (
        self.db.query(OracleReading)
        .filter(OracleReading.id == reading_id, OracleReading.deleted_at.is_(None))
        .first()
    )
    if not row:
        return False
    row.deleted_at = datetime.now(timezone.utc)
    self.db.flush()
    return True
```

#### 3b: Add `toggle_favorite()` to `OracleReadingService`

```python
def toggle_favorite(self, reading_id: int) -> dict | None:
    """Toggle the is_favorite flag on a reading."""
    row = (
        self.db.query(OracleReading)
        .filter(OracleReading.id == reading_id, OracleReading.deleted_at.is_(None))
        .first()
    )
    if not row:
        return None
    row.is_favorite = not row.is_favorite
    self.db.flush()
    return self._decrypt_reading(row)
```

#### 3c: Add `search_readings()` to `OracleReadingService`

```python
def search_readings(
    self,
    query_text: str,
    limit: int = 20,
    offset: int = 0,
    sign_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_favorite: bool | None = None,
) -> tuple[list[dict], int]:
    """Full-text search on reading content via PostgreSQL tsvector."""
    from sqlalchemy import text as sql_text

    base = self.db.query(OracleReading).filter(
        OracleReading.deleted_at.is_(None)
    )

    # Full-text search filter
    base = base.filter(
        sql_text("search_vector @@ plainto_tsquery('english', :q) OR search_vector @@ plainto_tsquery('simple', :q)")
    ).params(q=query_text)

    if sign_type:
        base = base.filter(OracleReading.sign_type == sign_type)
    if date_from:
        base = base.filter(OracleReading.created_at >= _parse_datetime(date_from))
    if date_to:
        base = base.filter(OracleReading.created_at <= _parse_datetime(date_to))
    if is_favorite is not None:
        base = base.filter(OracleReading.is_favorite == is_favorite)

    total = base.count()
    rows = base.order_by(OracleReading.created_at.desc()).offset(offset).limit(limit).all()
    return [self._decrypt_reading(r) for r in rows], total
```

#### 3d: Add `get_reading_stats()` to `OracleReadingService`

```python
def get_reading_stats(self) -> dict:
    """Aggregate reading statistics."""
    from sqlalchemy import extract, text as sql_text

    base = self.db.query(OracleReading).filter(
        OracleReading.deleted_at.is_(None)
    )

    total = base.count()
    favorites = base.filter(OracleReading.is_favorite == True).count()

    # Count by sign_type
    type_counts = (
        base.with_entities(OracleReading.sign_type, func.count())
        .group_by(OracleReading.sign_type)
        .all()
    )
    by_type = {t: c for t, c in type_counts}

    # Count by month (last 12 months)
    month_counts = (
        base.with_entities(
            func.to_char(OracleReading.created_at, 'YYYY-MM').label('month'),
            func.count().label('count')
        )
        .group_by('month')
        .order_by('month')
        .limit(12)
        .all()
    )
    by_month = [{"month": m, "count": c} for m, c in month_counts]

    # Most active day of week
    day_counts = (
        base.with_entities(
            func.to_char(OracleReading.created_at, 'Day').label('day_name'),
            func.count().label('count')
        )
        .group_by('day_name')
        .order_by(func.count().desc())
        .first()
    )
    most_active_day = day_counts[0].strip() if day_counts else None

    return {
        "total_readings": total,
        "by_type": by_type,
        "by_month": by_month,
        "favorites_count": favorites,
        "most_active_day": most_active_day,
    }
```

#### 3e: Update existing `list_readings()` method

Add parameters and filters:

```python
def list_readings(
    self,
    user_id: int | None,
    is_admin: bool,
    limit: int,
    offset: int,
    sign_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_favorite: bool | None = None,
    search_query: str | None = None,
) -> tuple[list[dict], int]:
    """Query readings with filters + pagination. Excludes soft-deleted."""
    query = self.db.query(OracleReading).filter(
        OracleReading.deleted_at.is_(None)
    )

    if sign_type:
        query = query.filter(OracleReading.sign_type == sign_type)
    if date_from:
        query = query.filter(OracleReading.created_at >= _parse_datetime(date_from))
    if date_to:
        query = query.filter(OracleReading.created_at <= _parse_datetime(date_to))
    if is_favorite is not None:
        query = query.filter(OracleReading.is_favorite == is_favorite)
    if search_query:
        from sqlalchemy import text as sql_text
        query = query.filter(
            sql_text("search_vector @@ plainto_tsquery('english', :q) OR search_vector @@ plainto_tsquery('simple', :q)")
        ).params(q=search_query)

    total = query.count()
    rows = (
        query.order_by(OracleReading.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [self._decrypt_reading(r) for r in rows], total
```

#### 3f: Update `_decrypt_reading()` method

Add `is_favorite` and `deleted_at` to the returned dict:

```python
# Add at the end of the return dict:
"is_favorite": row.is_favorite,
"deleted_at": row.deleted_at.isoformat() if row.deleted_at else None,
```

#### STOP Checkpoint 3

```bash
# Verify service imports cleanly
cd api && python3 -c "from app.services.oracle_reading import OracleReadingService; print('Service OK')"

# Run existing service tests to confirm nothing broken
cd api && python3 -m pytest tests/ -k "reading" -v --tb=short 2>&1 | tail -20
```

**Do NOT proceed to Phase 4 until service imports cleanly and existing tests still pass.**

---

### Phase 4: API Endpoints (~30 min)

**Goal:** Add DELETE, stats, and favorite endpoints; expand list endpoint with new filters.

**CRITICAL:** The `/readings/stats` route MUST be defined BEFORE `/readings/{reading_id}` in the router. Otherwise FastAPI will interpret "stats" as a `reading_id` path parameter and fail with a validation error.

#### 4a: Add stats endpoint (BEFORE `get_stored_reading`)

Insert this endpoint in `api/app/routers/oracle.py` between the `list_readings` endpoint and the `get_stored_reading` endpoint:

```python
@router.get(
    "/readings/stats",
    response_model=ReadingStatsResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def reading_stats(
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Get reading statistics: counts by type, by month, favorites, most active day."""
    stats = svc.get_reading_stats()
    audit.log_event(
        event_type="reading_stats_viewed",
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return ReadingStatsResponse(**stats)
```

#### 4b: Add DELETE endpoint (after `get_stored_reading`)

```python
@router.delete(
    "/readings/{reading_id}",
    status_code=204,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def delete_reading(
    reading_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Soft-delete a reading (sets deleted_at, does not remove from DB)."""
    success = svc.soft_delete_reading(reading_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found"
        )
    audit.log_event(
        event_type="reading_deleted",
        details={"reading_id": reading_id},
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return Response(status_code=204)
```

#### 4c: Add favorite toggle endpoint

```python
@router.patch(
    "/readings/{reading_id}/favorite",
    response_model=StoredReadingResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def toggle_favorite(
    reading_id: int,
    request: Request,
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
    """Toggle the is_favorite flag on a reading."""
    data = svc.toggle_favorite(reading_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found"
        )
    audit.log_event(
        event_type="reading_favorite_toggled",
        details={"reading_id": reading_id, "is_favorite": data["is_favorite"]},
        ip=_get_client_ip(request),
        key_hash=_user.get("api_key_hash"),
    )
    svc.db.commit()
    return StoredReadingResponse(**data)
```

#### 4d: Expand `list_readings` endpoint

Add new query parameters to the existing `list_readings` function:

```python
def list_readings(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sign_type: str | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=200),
    date_from: str | None = Query(None, description="ISO date, e.g. 2026-01-01"),
    date_to: str | None = Query(None, description="ISO date, e.g. 2026-12-31"),
    is_favorite: bool | None = Query(None),
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
    audit: AuditService = Depends(get_audit_service),
):
```

Pass all new params to `svc.list_readings()`:

```python
readings, total = svc.list_readings(
    user_id=None,
    is_admin=is_admin,
    limit=limit,
    offset=offset,
    sign_type=sign_type,
    date_from=date_from,
    date_to=date_to,
    is_favorite=is_favorite,
    search_query=search,
)
```

#### 4e: Add imports

Add to the top of `oracle.py`:

```python
from starlette.responses import Response
from app.models.oracle import ReadingStatsResponse
```

#### STOP Checkpoint 4

```bash
# Start API server
make dev-api &

# Test stats endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/stats | python3 -m json.tool

# Test soft delete (use a real reading ID)
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/1 -w "\n%{http_code}"
# Expected: 204

# Test favorite toggle
curl -X PATCH -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/2/favorite | python3 -m json.tool
# Expected: reading with is_favorite toggled

# Test search
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?search=love" | python3 -m json.tool

# Test date range
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?date_from=2026-01-01&date_to=2026-02-28" | python3 -m json.tool

# Test favorites filter
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?is_favorite=true" | python3 -m json.tool

# Verify deleted reading excluded from list
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings | python3 -m json.tool
# Reading 1 should NOT appear
```

**Do NOT proceed to Phase 5 until all endpoint tests return expected results.**

---

### Phase 5: Frontend Types + API Client + Hooks (~20 min)

**Goal:** Update TypeScript types, API client, and React Query hooks for new capabilities.

#### 5a: Update `frontend/src/types/index.ts`

Add fields to `StoredReading` interface:

```typescript
export interface StoredReading {
  id: number;
  user_id: number | null;
  sign_type: string;
  sign_value: string;
  question: string | null;
  reading_result: Record<string, unknown> | null;
  ai_interpretation: string | null;
  created_at: string;
  is_favorite: boolean; // NEW
  deleted_at: string | null; // NEW
}
```

Add new interface after `StoredReadingListResponse`:

```typescript
export interface ReadingStats {
  total_readings: number;
  by_type: Record<string, number>;
  by_month: { month: string; count: number }[];
  favorites_count: number;
  most_active_day: string | null;
}

export interface ReadingSearchParams {
  limit?: number;
  offset?: number;
  sign_type?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  is_favorite?: boolean;
}
```

#### 5b: Update `frontend/src/services/api.ts`

Expand `oracle` object:

```typescript
export const oracle = {
  // ... existing methods unchanged ...

  history: (params?: ReadingSearchParams) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    if (params?.sign_type) query.set("sign_type", params.sign_type);
    if (params?.search) query.set("search", params.search);
    if (params?.date_from) query.set("date_from", params.date_from);
    if (params?.date_to) query.set("date_to", params.date_to);
    if (params?.is_favorite !== undefined)
      query.set("is_favorite", String(params.is_favorite));
    return request<StoredReadingListResponse>(`/oracle/readings?${query}`);
  },

  deleteReading: (id: number) =>
    request<void>(`/oracle/readings/${id}`, { method: "DELETE" }),

  toggleFavorite: (id: number) =>
    request<StoredReading>(`/oracle/readings/${id}/favorite`, {
      method: "PATCH",
    }),

  readingStats: () => request<ReadingStats>("/oracle/readings/stats"),
};
```

#### 5c: Update `frontend/src/hooks/useOracleReadings.ts`

Add new hooks:

```typescript
export function useReadingHistory(params?: ReadingSearchParams) {
  return useQuery({
    queryKey: [...HISTORY_KEY, params],
    queryFn: () => oracle.history(params),
  });
}

export function useDeleteReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => oracle.deleteReading(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useToggleFavorite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => oracle.toggleFavorite(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
  });
}

export function useReadingStats() {
  return useQuery({
    queryKey: ["readingStats"],
    queryFn: () => oracle.readingStats(),
  });
}
```

#### STOP Checkpoint 5

```bash
# TypeScript compiles
cd frontend && npx tsc --noEmit 2>&1 | tail -10
# Expected: no errors

# Existing tests still pass
cd frontend && npx vitest run src/components/oracle/__tests__/ReadingHistory.test.tsx 2>&1 | tail -10
```

**Do NOT proceed to Phase 6 until TypeScript compiles and existing tests pass.**

---

### Phase 6: Frontend Components (~90 min)

**Goal:** Create ReadingCard and ReadingDetail components, rewrite ReadingHistory.

#### 6a: Create `frontend/src/components/oracle/ReadingCard.tsx` (~40 min)

**Props:**

```typescript
interface ReadingCardProps {
  reading: StoredReading;
  onSelect: (id: number) => void;
  onToggleFavorite: (id: number) => void;
  onDelete: (id: number) => void;
}
```

**Layout:**

```
┌─────────────────────────────────────────────────────┐
│ [type icon] First line of text...          [date]   │
│             AI interpretation preview...   [star]   │
│             sign_type badge                [trash]  │
└─────────────────────────────────────────────────────┘
```

**Implementation details:**

- Type icon: clock icon for `time`, user icon for `name`, question-mark icon for `question`, circle icon for `multi_user`
- First line: `reading.question || reading.sign_value || ""` truncated to 60 chars
- AI interpretation preview: `reading.ai_interpretation` truncated to 100 chars, dimmed text
- Date: `new Date(reading.created_at).toLocaleDateString()` in small text
- Star icon: filled yellow (`text-yellow-400`) when `is_favorite`, outline when not. Click calls `onToggleFavorite`
- Trash icon: dimmed, on click shows inline confirmation ("Delete? Yes/No"), then calls `onDelete`
- Sign type badge: small pill chip with `reading.sign_type` text
- Entire card clickable → calls `onSelect(reading.id)`, except star and trash buttons (use `e.stopPropagation()`)
- Tailwind classes: `border border-nps-border rounded-lg p-3 hover:bg-nps-bg-input transition-colors cursor-pointer`
- RTL support: use `text-start` and `rtl:` variants as needed
- All visible text through `useTranslation()`

#### 6b: Create `frontend/src/components/oracle/ReadingDetail.tsx` (~30 min)

**Props:**

```typescript
interface ReadingDetailProps {
  readingId: number;
  onClose: () => void;
}
```

**Implementation details:**

- Fetches full reading via `oracle.getReading(readingId)` (useQuery)
- **Loading state:** Spinner with "Loading reading..." text
- **Error state:** "Reading not found" message with close button
- **Content layout:**
  - Header: sign type badge + date + favorite star + close (X) button
  - If `reading.question`: show question text in highlight box
  - If `reading.reading_result`: parse JSON and display sections:
    - FC60 data (cycle, element, polarity, stem, branch)
    - Numerology (life path, day vibration, personal year/month/day)
    - Zodiac (sign, element, ruling planet)
    - Moon (phase, illumination, meaning, emoji)
    - Ganzhi (year name, animal, element, hour animal)
    - FC60 extended (stamp, weekday, planet, domain)
    - Synchronicities list
  - AI interpretation: full text in styled block
- Delete button at bottom with confirmation
- All text through i18n
- Scrollable container if content exceeds viewport

#### 6c: Rewrite `frontend/src/components/oracle/ReadingHistory.tsx` (~20 min)

**Replace the entire component** (currently 135 lines) with new card-based layout:

**State management:**

```typescript
const [search, setSearch] = useState("");
const [debouncedSearch, setDebouncedSearch] = useState("");
const [filter, setFilter] = useState<FilterType>("");
const [dateFrom, setDateFrom] = useState("");
const [dateTo, setDateTo] = useState("");
const [favoritesOnly, setFavoritesOnly] = useState(false);
const [page, setPage] = useState(0);
const [selectedReadingId, setSelectedReadingId] = useState<number | null>(null);
```

**Debounced search:** Use `useEffect` with 300ms `setTimeout` to update `debouncedSearch` from `search`.

**Data fetching:** Pass all filter state to `useReadingHistory()`:

```typescript
const { data, isLoading, isError } = useReadingHistory({
  limit: PAGE_SIZE,
  offset: page * PAGE_SIZE,
  sign_type: filter || undefined,
  search: debouncedSearch || undefined,
  date_from: dateFrom || undefined,
  date_to: dateTo || undefined,
  is_favorite: favoritesOnly ? true : undefined,
});
```

**Layout structure:**

```
┌─────────────────────────────────────────────────────┐
│ Stats: 45 readings | 3 favorites                    │
├─────────────────────────────────────────────────────┤
│ [Search bar _______________]  [Favorites toggle]    │
│ [Date from ___] [Date to ___]                       │
│ [All] [Readings] [Questions] [Names]   (type chips) │
├─────────────────────────────────────────────────────┤
│ [ReadingCard 1]                                     │
│ [ReadingCard 2]                                     │
│ [ReadingCard 3]                                     │
│ ...                                                 │
├─────────────────────────────────────────────────────┤
│ [< Prev] Page 1 of 3 [Next >]                      │
│ 45 readings total                                   │
└─────────────────────────────────────────────────────┘
```

**Pagination:** Use page numbers instead of "load more":

```typescript
const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;
```

Render Prev/Next buttons + current page indicator. Disable Prev on page 0, disable Next on last page.

**When a card is selected:** Show `ReadingDetail` in a panel (conditionally rendered below or beside the list). Pass `selectedReadingId` and `onClose={() => setSelectedReadingId(null)}`.

**Empty states:**

- No readings at all: "No readings yet. Create your first reading to see it here."
- No search results: "No readings match your search."
- Loading: show skeleton cards (3 placeholder cards with pulse animation)

**Reset behavior:** When any filter changes, reset page to 0.

#### STOP Checkpoint 6

```bash
# Frontend compiles
cd frontend && npx tsc --noEmit 2>&1 | tail -10

# Dev server renders without errors
cd frontend && npm run dev &
# Open http://localhost:5173, navigate to reading history tab
# Verify: search bar visible, filter chips visible, cards render

# Manual tests:
# 1. Type in search bar → results update after 300ms
# 2. Click type filter chip → results filter
# 3. Set date range → results filter
# 4. Toggle favorites → only favorites shown
# 5. Click a card → detail view opens
# 6. Click star on a card → favorite toggles
# 7. Click trash on a card → confirm → card disappears
# 8. Navigate pages with Prev/Next
```

**Do NOT proceed to Phase 7 until all manual tests pass.**

---

### Phase 7: i18n (~15 min)

**Goal:** Add all new i18n keys for reading history features in both English and Persian.

#### 7a: Update `frontend/src/locales/en.json`

Add under `"oracle"` section:

```json
{
  "oracle": {
    "search_readings": "Search readings",
    "search_placeholder": "Search by question or interpretation...",
    "date_from": "From",
    "date_to": "To",
    "favorites_only": "Favorites only",
    "no_search_results": "No readings match your search.",
    "reading_stats": "Reading Statistics",
    "total_readings": "Total readings",
    "favorites": "Favorites",
    "delete_reading": "Delete reading",
    "confirm_delete": "Are you sure you want to delete this reading?",
    "confirm_yes": "Yes, delete",
    "confirm_no": "Cancel",
    "reading_deleted": "Reading deleted",
    "toggle_favorite": "Toggle favorite",
    "favorited": "Added to favorites",
    "unfavorited": "Removed from favorites",
    "reading_detail": "Reading Detail",
    "close_detail": "Close",
    "page_of": "Page {{current}} of {{total}}",
    "prev_page": "Previous",
    "next_page": "Next",
    "reading_type_time": "Time Reading",
    "reading_type_name": "Name Reading",
    "reading_type_question": "Question",
    "reading_type_multi_user": "Multi-User"
  }
}
```

#### 7b: Update `frontend/src/locales/fa.json`

Add matching Persian translations:

```json
{
  "oracle": {
    "search_readings": "\u062c\u0633\u062a\u062c\u0648\u06cc \u062e\u0648\u0627\u0646\u0634\u200c\u0647\u0627",
    "search_placeholder": "\u062c\u0633\u062a\u062c\u0648 \u0628\u0631 \u0627\u0633\u0627\u0633 \u0633\u0624\u0627\u0644 \u06cc\u0627 \u062a\u0641\u0633\u06cc\u0631...",
    "date_from": "\u0627\u0632",
    "date_to": "\u062a\u0627",
    "favorites_only": "\u0641\u0642\u0637 \u0645\u0648\u0631\u062f \u0639\u0644\u0627\u0642\u0647",
    "no_search_results": "\u0647\u06cc\u0686 \u062e\u0648\u0627\u0646\u0634\u06cc \u0628\u0627 \u062c\u0633\u062a\u062c\u0648\u06cc \u0634\u0645\u0627 \u0645\u0637\u0627\u0628\u0642\u062a \u0646\u062f\u0627\u0631\u062f.",
    "reading_stats": "\u0622\u0645\u0627\u0631 \u062e\u0648\u0627\u0646\u0634\u200c\u0647\u0627",
    "total_readings": "\u06a9\u0644 \u062e\u0648\u0627\u0646\u0634\u200c\u0647\u0627",
    "favorites": "\u0645\u0648\u0631\u062f \u0639\u0644\u0627\u0642\u0647",
    "delete_reading": "\u062d\u0630\u0641 \u062e\u0648\u0627\u0646\u0634",
    "confirm_delete": "\u0622\u06cc\u0627 \u0645\u0637\u0645\u0626\u0646 \u0647\u0633\u062a\u06cc\u062f \u06a9\u0647 \u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u06cc\u062f \u0627\u06cc\u0646 \u062e\u0648\u0627\u0646\u0634 \u0631\u0627 \u062d\u0630\u0641 \u06a9\u0646\u06cc\u062f\u061f",
    "confirm_yes": "\u0628\u0644\u0647\u060c \u062d\u0630\u0641 \u06a9\u0646",
    "confirm_no": "\u0627\u0646\u0635\u0631\u0627\u0641",
    "reading_deleted": "\u062e\u0648\u0627\u0646\u0634 \u062d\u0630\u0641 \u0634\u062f",
    "toggle_favorite": "\u062a\u063a\u06cc\u06cc\u0631 \u0639\u0644\u0627\u0642\u0647\u200c\u0645\u0646\u062f\u06cc",
    "favorited": "\u0628\u0647 \u0639\u0644\u0627\u0642\u0647\u200c\u0645\u0646\u062f\u06cc\u200c\u0647\u0627 \u0627\u0636\u0627\u0641\u0647 \u0634\u062f",
    "unfavorited": "\u0627\u0632 \u0639\u0644\u0627\u0642\u0647\u200c\u0645\u0646\u062f\u06cc\u200c\u0647\u0627 \u062d\u0630\u0641 \u0634\u062f",
    "reading_detail": "\u062c\u0632\u0626\u06cc\u0627\u062a \u062e\u0648\u0627\u0646\u0634",
    "close_detail": "\u0628\u0633\u062a\u0646",
    "page_of": "\u0635\u0641\u062d\u0647 {{current}} \u0627\u0632 {{total}}",
    "prev_page": "\u0642\u0628\u0644\u06cc",
    "next_page": "\u0628\u0639\u062f\u06cc",
    "reading_type_time": "\u062e\u0648\u0627\u0646\u0634 \u0632\u0645\u0627\u0646",
    "reading_type_name": "\u062e\u0648\u0627\u0646\u0634 \u0646\u0627\u0645",
    "reading_type_question": "\u0633\u0624\u0627\u0644",
    "reading_type_multi_user": "\u0686\u0646\u062f \u06a9\u0627\u0631\u0628\u0631\u0647"
  }
}
```

#### STOP Checkpoint 7

```bash
# Switch browser language to FA
# Verify all new strings display in Persian
# Switch back to EN
# Verify all new strings display in English

# No missing translation keys in console
cd frontend && npm run dev 2>&1 | grep -i "missing"
# Expected: no output
```

**Do NOT proceed to Phase 8 until i18n is verified in both languages.**

---

### Phase 8: Tests (~45 min)

**Goal:** Write 25 tests covering all new functionality.

#### Backend Tests: `api/tests/test_reading_history.py` (11 tests)

| #   | Test Name                         | What It Verifies                                                       |
| --- | --------------------------------- | ---------------------------------------------------------------------- |
| 1   | `test_soft_delete_reading`        | DELETE /readings/{id} returns 204, reading excluded from list          |
| 2   | `test_delete_nonexistent_reading` | DELETE /readings/99999 returns 404                                     |
| 3   | `test_toggle_favorite_on`         | PATCH /readings/{id}/favorite sets is_favorite=True                    |
| 4   | `test_toggle_favorite_off`        | Second PATCH sets is_favorite=False                                    |
| 5   | `test_reading_stats_counts`       | GET /readings/stats returns correct total_readings and by_type counts  |
| 6   | `test_search_by_question_text`    | GET /readings?search=keyword finds matching readings by question       |
| 7   | `test_search_by_interpretation`   | GET /readings?search=keyword finds matching readings by AI text        |
| 8   | `test_search_no_results`          | GET /readings?search=xyznonexistent returns empty list                 |
| 9   | `test_date_range_filter`          | GET /readings?date_from=...&date_to=... only returns readings in range |
| 10  | `test_favorites_filter`           | GET /readings?is_favorite=true only returns favorited readings         |
| 11  | `test_list_excludes_deleted`      | After soft-delete, reading does not appear in list or search           |

**Test structure:**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer test-key"}

@pytest.fixture
def sample_reading(db_session):
    """Create a reading for tests."""
    # Insert via ORM or service
    ...

def test_soft_delete_reading(sample_reading):
    resp = client.delete(f"/api/oracle/readings/{sample_reading.id}", headers=HEADERS)
    assert resp.status_code == 204
    # Verify excluded from list
    list_resp = client.get("/api/oracle/readings", headers=HEADERS)
    ids = [r["id"] for r in list_resp.json()["readings"]]
    assert sample_reading.id not in ids
```

#### Frontend Tests: 14 tests across 3 files

**`frontend/src/components/oracle/__tests__/ReadingCard.test.tsx` (4 tests):**

| #   | Test Name                                    | What It Verifies                                          |
| --- | -------------------------------------------- | --------------------------------------------------------- |
| 12  | `renders reading card with type, date, text` | Card shows sign_type badge, date, truncated text          |
| 13  | `favorite toggle fires callback`             | Clicking star icon calls onToggleFavorite with reading.id |
| 14  | `delete fires callback after confirmation`   | Clicking trash → confirm → calls onDelete with reading.id |
| 15  | `truncates long interpretation text`         | Text longer than 100 chars is truncated with ellipsis     |

**`frontend/src/components/oracle/__tests__/ReadingDetail.test.tsx` (3 tests):**

| #   | Test Name                     | What It Verifies                                                  |
| --- | ----------------------------- | ----------------------------------------------------------------- |
| 16  | `shows loading state`         | Spinner/text visible while fetching                               |
| 17  | `shows full reading sections` | FC60, numerology, zodiac, moon sections rendered when data loaded |
| 18  | `handles not found`           | Shows error message when API returns 404                          |

**`frontend/src/components/oracle/__tests__/ReadingHistory.test.tsx` (7 NEW tests, add to existing 6):**

| #   | Test Name                     | What It Verifies                                             |
| --- | ----------------------------- | ------------------------------------------------------------ |
| 19  | `search debounce works`       | Typing in search bar triggers API call after 300ms delay     |
| 20  | `date range filter works`     | Setting date_from and date_to passes params to API           |
| 21  | `favorites toggle works`      | Clicking favorites toggle passes is_favorite=true to API     |
| 22  | `opens detail on card click`  | Clicking a ReadingCard renders ReadingDetail with correct ID |
| 23  | `shows stats summary`         | Stats bar shows total readings and favorites count           |
| 24  | `pagination navigation works` | Clicking Next/Prev changes page, correct offset sent to API  |
| 25  | `empty search state`          | Shows "no search results" message when search returns 0      |

#### STOP Checkpoint 8 (FINAL)

```bash
# Backend tests
cd api && python3 -m pytest tests/test_reading_history.py -v
# Expected: 11 passed

# Frontend tests — ReadingCard
cd frontend && npx vitest run src/components/oracle/__tests__/ReadingCard.test.tsx
# Expected: 4 passed

# Frontend tests — ReadingDetail
cd frontend && npx vitest run src/components/oracle/__tests__/ReadingDetail.test.tsx
# Expected: 3 passed

# Frontend tests — ReadingHistory (existing + new)
cd frontend && npx vitest run src/components/oracle/__tests__/ReadingHistory.test.tsx
# Expected: 13 passed (6 existing + 7 new)

# Full test suite still passes
cd api && python3 -m pytest tests/ -v --tb=short
cd frontend && npx vitest run
```

**All 25 tests must pass before marking session complete.**

---

## Acceptance Criteria

| #   | Criterion                                                  | Verify Command                                                                                                                                                                                                                  |
| --- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `is_favorite`, `deleted_at`, `search_vector` columns exist | `psql -U nps -d nps -c "SELECT column_name FROM information_schema.columns WHERE table_name='oracle_readings' AND column_name IN ('is_favorite','deleted_at','search_vector');"` (3 rows)                                       |
| 2   | Full-text search trigger auto-populates search_vector      | `psql -U nps -d nps -c "INSERT INTO oracle_readings (user_id, question, sign_type, sign_value) VALUES (1,'test query','time','12:00'); SELECT search_vector IS NOT NULL FROM oracle_readings ORDER BY id DESC LIMIT 1;"` (true) |
| 3   | DELETE /readings/{id} soft-deletes                         | `curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/{id} -w "\n%{http_code}"` (204)                                                                                                     |
| 4   | GET /readings/stats returns statistics                     | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/stats \| python3 -m json.tool` (has total_readings, by_type, favorites_count)                                                                 |
| 5   | PATCH /readings/{id}/favorite toggles                      | `curl -X PATCH -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/oracle/readings/{id}/favorite \| python3 -m json.tool` (is_favorite flips)                                                                           |
| 6   | Search filters readings by text                            | `curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?search=love" \| python3 -m json.tool` (filtered results)                                                                                     |
| 7   | Date range filters readings                                | `curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?date_from=2026-01-01&date_to=2026-02-28" \| python3 -m json.tool` (filtered)                                                                 |
| 8   | Favorites filter works                                     | `curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/oracle/readings?is_favorite=true" \| python3 -m json.tool` (only favorites)                                                                                  |
| 9   | Deleted readings excluded from list                        | After delete, reading absent from list and search results                                                                                                                                                                       |
| 10  | ReadingCard displays type, date, star, truncated text      | Visual: history tab shows card-based layout                                                                                                                                                                                     |
| 11  | ReadingDetail shows all sections                           | Visual: click card, full detail with FC60/numerology/zodiac/moon/ganzhi/AI                                                                                                                                                      |
| 12  | Search bar with debounce in history                        | Visual: type in search, results update after 300ms                                                                                                                                                                              |
| 13  | Pagination with page numbers                               | Visual: Prev/Next buttons, "Page X of Y"                                                                                                                                                                                        |
| 14  | i18n complete EN + FA                                      | Visual: switch language, all new strings translated                                                                                                                                                                             |
| 15  | 25 tests pass                                              | See STOP Checkpoint 8 commands                                                                                                                                                                                                  |

---

## Error Scenarios

### Error 1: Full-text search fails (tsvector function not available)

**Symptoms:** Search endpoint returns 500, PostgreSQL logs show `ERROR: function plainto_tsquery(unknown, unknown) does not exist`

**Root Cause:** Migration `014_reading_search.sql` was not applied, or PostgreSQL version does not support full-text search (unlikely — tsvector supported since 8.3).

**Recovery steps:**

1. Check migration status: `psql -U nps -d nps -c "\d oracle_readings"` — look for `search_vector` column
2. If column missing, run migration: `psql -U nps -d nps -f database/migrations/014_reading_search.sql`
3. Verify trigger: `psql -U nps -d nps -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table='oracle_readings';"`
4. If PostgreSQL version too old (< 8.3): upgrade PostgreSQL, or implement fallback ILIKE search as temporary workaround:
   ```python
   # Fallback: replace tsvector query with ILIKE
   base = base.filter(
       OracleReading.question.ilike(f"%{query_text}%") |
       OracleReading.ai_interpretation.ilike(f"%{query_text}%")
   )
   ```

### Error 2: Persian text not found by search

**Symptoms:** English search works fine, Persian search returns zero results even when matching readings exist.

**Root Cause:** The `simple` dictionary doesn't perform any morphological analysis — it just lowercases and splits on whitespace. If Persian text was stored with different Unicode normalization (e.g., NFKC vs NFC), the tsvector tokens won't match.

**Recovery steps:**

1. Verify Persian text in database: `psql -U nps -d nps -c "SELECT question_persian, ai_interpretation_persian FROM oracle_readings WHERE question_persian IS NOT NULL LIMIT 3;"`
2. Test tsvector manually: `SELECT to_tsvector('simple', 'your-persian-text') @@ plainto_tsquery('simple', 'search-term');`
3. If normalization mismatch: add Unicode NFKC normalization in the trigger function before creating the tsvector
4. If Persian diacritics cause issues: strip diacritics in the trigger function using `regexp_replace`
5. Backfill after fix: `UPDATE oracle_readings SET question_persian = question_persian;` (triggers recalculation)

### Error 3: Stats endpoint slow on large reading table (> 100K rows)

**Symptoms:** GET /readings/stats takes > 5 seconds, causing frontend timeout.

**Root Cause:** Multiple COUNT + GROUP BY queries hitting unoptimized paths.

**Recovery steps:**

1. Verify index exists: `psql -U nps -d nps -c "SELECT indexname FROM pg_indexes WHERE indexname='idx_oracle_readings_stats';"` — should return the composite stats index
2. Run ANALYZE to update query planner stats: `psql -U nps -d nps -c "ANALYZE oracle_readings;"`
3. If still slow, create a materialized view:
   ```sql
   CREATE MATERIALIZED VIEW oracle_reading_stats_mv AS
   SELECT sign_type, date_trunc('month', created_at) as month, count(*) as cnt
   FROM oracle_readings WHERE deleted_at IS NULL
   GROUP BY sign_type, month;
   CREATE UNIQUE INDEX ON oracle_reading_stats_mv(sign_type, month);
   ```
   Refresh periodically: `REFRESH MATERIALIZED VIEW CONCURRENTLY oracle_reading_stats_mv;`
4. Add Redis cache (5-minute TTL) for stats response in the service layer

---

## Handoff to Session 18

Session 18 ("AI Learning & Feedback Loop") receives from Session 17:

### Database

- `oracle_readings` table with `is_favorite`, `deleted_at`, `search_vector` columns
- Full-text search trigger `trg_oracle_readings_search` auto-populating search_vector
- GIN index on search_vector, partial indexes on is_favorite and deleted_at
- Composite stats index for efficient GROUP BY queries

### API

- `GET /api/oracle/readings` — Paginated list with filters: sign_type, search, date_from, date_to, is_favorite
- `GET /api/oracle/readings/{id}` — Full reading details
- `DELETE /api/oracle/readings/{id}` — Soft delete
- `GET /api/oracle/readings/stats` — Reading statistics
- `PATCH /api/oracle/readings/{id}/favorite` — Toggle favorite

### Service Layer

- `OracleReadingService` with methods: `list_readings()`, `get_reading_by_id()`, `store_reading()`, `soft_delete_reading()`, `toggle_favorite()`, `search_readings()`, `get_reading_stats()`

### Frontend

- `ReadingHistory.tsx` — Card grid with search, filters, pagination, stats summary
- `ReadingCard.tsx` — Individual reading card with type icon, text preview, star, delete
- `ReadingDetail.tsx` — Full detail view with all reading sections
- `useReadingHistory()`, `useDeleteReading()`, `useToggleFavorite()`, `useReadingStats()` hooks
- i18n keys for all reading history features in EN + FA

### Session 18 Will Add

- `oracle_reading_feedback` table (new, stores ratings + text feedback per reading)
- `POST /api/oracle/readings/{id}/feedback` endpoint (extends Session 17's reading routes)
- `ReadingFeedback.tsx` embedded in Session 17's `ReadingDetail.tsx` (star rating + section feedback + text)
- `StarRating.tsx` reusable component
- Learning data aggregation from feedback trends
- Admin learning dashboard

Session 18 depends on Session 17's `ReadingDetail.tsx` component (the feedback UI will be embedded at the bottom of the detail view) and the complete reading management API (feedback routes extend the same `/readings/{id}/` URL namespace).

---

## Reference: Current File State Summary

| File                                                               | Current Lines | Current State                                        | Session 17 Action                              |
| ------------------------------------------------------------------ | ------------- | ---------------------------------------------------- | ---------------------------------------------- |
| `database/schemas/oracle_readings.sql`                             | 48            | 10 columns, no favorites/deleted/search              | Reference only (migration adds columns)        |
| `database/schemas/oracle_indexes.sql`                              | 43            | 11 indexes, no search/favorite/deleted               | Reference only (migration adds indexes)        |
| `api/app/orm/oracle_reading.py`                                    | 48            | OracleReading (13 mapped columns), OracleReadingUser | Add is_favorite + deleted_at                   |
| `api/app/models/oracle.py`                                         | 283           | StoredReadingResponse (8 fields), no stats model     | Add fields + ReadingStatsResponse              |
| `api/app/routers/oracle.py`                                        | 627           | GET /readings + GET /readings/{id} only              | Add DELETE + stats + favorite + expand filters |
| `api/app/services/oracle_reading.py`                               | 579           | list_readings, get_reading_by_id, store_reading      | Add delete, favorite, search, stats            |
| `frontend/src/types/index.ts`                                      | 411           | StoredReading (8 fields), no stats type              | Add is_favorite + deleted_at + ReadingStats    |
| `frontend/src/services/api.ts`                                     | 192           | oracle.history (3 params), oracle.getReading         | Add delete, favorite, stats, expand history    |
| `frontend/src/hooks/useOracleReadings.ts`                          | 40            | useReadingHistory only                               | Add delete, favorite, stats hooks              |
| `frontend/src/components/oracle/ReadingHistory.tsx`                | 135           | Accordion list, basic filters                        | FULL REWRITE to card grid                      |
| `frontend/src/components/oracle/__tests__/ReadingHistory.test.tsx` | 142           | 6 tests                                              | Add 7 new tests                                |
| `frontend/src/locales/en.json`                                     | 190           | 6 reading history keys                               | Add ~20 new keys                               |
| `frontend/src/locales/fa.json`                                     | 190           | 6 matching Persian keys                              | Add ~20 new keys                               |
