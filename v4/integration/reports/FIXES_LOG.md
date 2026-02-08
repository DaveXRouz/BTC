# INTEGRATION-S2 Fixes Log

Detailed record of all fixes applied during the INTEGRATION-S2 session.

---

## Fix 1: Add `deleted_at` column to `oracle_users`

**File:** `v4/database/init.sql`
**Issue:** ISSUE-001

**Before:**

```sql
CREATE TABLE IF NOT EXISTS oracle_users (
    ...
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT oracle_users_birthday_check CHECK (birthday <= CURRENT_DATE),
    ...
);
```

**After:**

```sql
CREATE TABLE IF NOT EXISTS oracle_users (
    ...
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT oracle_users_birthday_check CHECK (birthday <= CURRENT_DATE),
    ...
);
```

**Additional:** Added partial index:

```sql
CREATE INDEX IF NOT EXISTS idx_oracle_users_active ON oracle_users(deleted_at) WHERE deleted_at IS NULL;
```

**Rationale:** The ORM model (`oracle_user.py:28`) defines `deleted_at: Mapped[datetime | None]` and the router filters by `OracleUser.deleted_at.is_(None)` in 5 locations. Without the column, all user queries would fail with a database error.

---

## Fix 2: Expand `sign_type` CHECK constraint

**File:** `v4/database/init.sql`
**Issue:** ISSUE-002

**Before:**

```sql
CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question'))
```

**After:**

```sql
CONSTRAINT oracle_readings_sign_type_check CHECK (sign_type IN ('time', 'name', 'question', 'reading', 'multi_user', 'daily'))
```

**Rationale:** The API stores `sign_type="reading"` for general readings (`oracle.py:119`), `sign_type="multi_user"` for multi-user readings (`oracle_reading.py:339`), and `sign_type="daily"` would be needed for daily insight persistence. The original CHECK only allowed the three V3-era types.

---

## Fix 3: Relax `user_check` constraint for anonymous readings

**File:** `v4/database/init.sql`
**Issue:** ISSUE-003

**Before:**

```sql
CONSTRAINT oracle_readings_user_check CHECK (
    (is_multi_user = FALSE AND user_id IS NOT NULL) OR
    (is_multi_user = TRUE AND primary_user_id IS NOT NULL)
)
```

**After:**

```sql
CONSTRAINT oracle_readings_user_check CHECK (
    (is_multi_user = FALSE) OR
    (is_multi_user = TRUE AND primary_user_id IS NOT NULL)
)
```

**Rationale:** All single-user reading endpoints (`/reading`, `/question`, `/name`) store `user_id=None` because they are anonymous readings not tied to an oracle_user profile. The constraint was blocking all reading creation. Multi-user readings still require `primary_user_id IS NOT NULL`.

---

## Fix 4: Add schema regression tests

**File:** `v4/integration/tests/test_database.py`

Added `TestSchemaFixes` class with 5 tests:

1. `test_deleted_at_column_exists` — Column presence verification
2. `test_soft_delete_workflow` — INSERT → soft-delete → verify filtered out → verify still exists
3. `test_sign_type_reading_allowed` — INSERT with `reading` and `daily` sign types
4. `test_null_user_id_single_user_reading` — INSERT with `user_id=NULL, is_multi_user=FALSE`
5. `test_partial_index_active_users` — Verify index exists in `pg_indexes`

Added `TestQueryPerformance.test_explain_analyze_active_users_uses_index` for query plan verification.

---

## Fix 5: Add soft-delete API verification tests

**File:** `v4/integration/tests/test_api_oracle.py`

Added `TestSoftDeleteVerification` class with 3 tests:

1. `test_deleted_user_not_in_list` — DELETE then verify not in GET list and GET by ID returns 404
2. `test_deleted_user_cannot_be_updated` — PUT after DELETE returns 404
3. `test_can_recreate_after_soft_delete` — Same name+birthday POST succeeds after soft-delete

---

## Fix 6: Update `oracle_users` column test

**File:** `v4/integration/tests/test_database.py`

Updated `TestDatabaseSchema.test_oracle_users_columns` to include `deleted_at` in expected columns set.
