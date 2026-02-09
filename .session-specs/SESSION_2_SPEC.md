# SESSION 2 SPEC — Fix Gaps & Validate Reading Flow

**Block:** Foundation (Sessions 1-5)
**Focus:** Fix 5 gaps from Session 1, validate Oracle reading endpoints
**Estimated Duration:** 2-3 hours
**Dependencies:** Session 1 (baseline verified)

---

## TL;DR

Session 2 fixes the 5 gaps identified in Session 1 (schema discrepancy, Pydantic deprecation, admin scope, etc.) and validates that the Oracle reading flow (create reading, store results, retrieve history) works end-to-end through the unit test suite.

---

## OBJECTIVES

1. **Fix schema discrepancy** — Sync `database/schemas/oracle_readings.sql` with `init.sql` (6 sign_types, relaxed user_check)
2. **Fix Pydantic deprecation** — Migrate `api/app/config.py` from class-based `Config` to `ConfigDict`
3. **Verify admin scope** — Confirm `admin` empty scope is intentional (domain-specific scopes used instead)
4. **Validate reading flow** — Verify all 5 reading endpoints compute + store + return correctly
5. **Validate reading history** — Verify list/get readings with decryption
6. **Re-run tests** — Confirm 322+ tests still pass after fixes

---

## PHASES

### Phase 1: Fix Schema Discrepancy (15 min)

**Problem:** `init.sql` (authoritative) has 6 sign_types and relaxed user_check. Standalone `oracle_readings.sql` has only 3 sign_types and stricter user_check.

**Fix:**

- Update `database/schemas/oracle_readings.sql` to match `init.sql`:
  - sign_type CHECK: `('time', 'name', 'question', 'reading', 'multi_user', 'daily')`
  - user_check: `(is_multi_user = FALSE) OR (is_multi_user = TRUE AND primary_user_id IS NOT NULL)`

**Files:**

- `database/schemas/oracle_readings.sql`

**Acceptance:**

- [ ] Standalone SQL matches init.sql constraints exactly
- [ ] Comment on sign_type updated to reflect all 6 types

### Phase 2: Fix Pydantic Deprecation (10 min)

**Problem:** `api/app/config.py` uses deprecated class-based `Config` inner class. Pydantic V2 warns about this.

**Fix:**

- Replace `class Config:` with `model_config = ConfigDict(...)` pattern

**Files:**

- `api/app/config.py`

**Acceptance:**

- [ ] No Pydantic deprecation warnings in test output
- [ ] All 166 API tests still pass

### Phase 3: Document Admin Scope Design (10 min)

**Problem:** `_SCOPE_HIERARCHY["admin"]` maps to empty set. Need to verify and document this is intentional.

**Action:**

- Review auth middleware to confirm domain-specific scopes (oracle:admin, scanner:admin, vault:admin) are the intended mechanism
- Add a clarifying comment in `auth.py` explaining the empty `admin` scope
- If `admin` is unused/unreachable, remove it to avoid confusion

**Files:**

- `api/app/middleware/auth.py`

**Acceptance:**

- [ ] Admin scope design documented or fixed
- [ ] Auth tests still pass

### Phase 4: Validate Oracle Reading Flow (30 min)

**Verify through existing test suite that:**

1. `POST /api/oracle/reading` — FC60 + numerology + zodiac + chinese computed correctly
2. `POST /api/oracle/question` — Question sign with yes/no/maybe answer
3. `POST /api/oracle/name` — Name cipher with destiny/soul/personality numbers
4. `GET /api/oracle/daily` — Daily insight with lucky numbers
5. `POST /api/oracle/suggest-range` — AI scan range suggestion
6. `POST /api/oracle/reading/multi-user` — Multi-user FC60 analysis
7. All readings stored to DB via `store_reading()` / `store_multi_user_reading()`
8. `GET /api/oracle/readings` — Reading history with pagination + filtering
9. `GET /api/oracle/readings/{id}` — Single reading fetch with decryption

**Files to review:**

- `api/app/services/oracle_reading.py` — Core computation + persistence
- `api/app/routers/oracle.py` — Endpoint handlers (reading section)
- `api/app/models/oracle.py` — Pydantic request/response models
- `api/tests/test_oracle_readings.py` — Reading endpoint tests

**Acceptance:**

- [ ] All reading-related tests pass
- [ ] Reading computation produces valid data structures
- [ ] Store/retrieve roundtrip works (SQLite fallback)
- [ ] Encrypted fields (question, ai_interpretation) handled correctly

### Phase 5: Re-run Full Test Suite (15 min)

**Tasks:**

1. Run API tests: `cd api && python3 -m pytest tests/ -v`
2. Run Oracle service tests: `cd services/oracle && python3 -m pytest tests/ -v`
3. Verify no regressions from Phase 1-3 fixes
4. Record updated baseline

**Acceptance:**

- [ ] API tests: 166+ pass / 0 fail (no Pydantic warning)
- [ ] Oracle service tests: 156+ pass / 0 fail
- [ ] No regressions introduced

### Phase 6: Update Session Log & Commit (10 min)

**Tasks:**

1. Update SESSION_LOG.md with Session 2 results
2. Git commit with `[foundation] fix gaps, validate reading flow (#session-2)`

**Acceptance:**

- [ ] SESSION_LOG.md updated
- [ ] Clean git commit

---

## SUCCESS CRITERIA

1. Schema discrepancy fixed — standalone SQL matches init.sql
2. Pydantic deprecation warning eliminated
3. Admin scope design clarified
4. Oracle reading flow validated (all 5 types + history)
5. 322+ tests pass with no regressions
6. SESSION_LOG.md updated with Session 2 entry

---

## NEXT SESSION

Session 3 will validate profile management (Oracle user profiles with encryption, birthday validation, coordinates/location) and the remaining Foundation endpoints.
