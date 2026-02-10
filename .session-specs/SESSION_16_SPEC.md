# SESSION 16 SPEC — Reading Flow: Daily & Multi-User Readings

**Block:** AI & Reading Types (Sessions 13-18)
**Estimated Duration:** 7-8 hours
**Complexity:** Very High
**Dependencies:** Session 14 (time reading flow + `ReadingOrchestrator` + `FrameworkReadingResponse`), Session 15 (name & question reading flows — confirms discriminator pattern on `POST /api/oracle/readings`), Session 7 (`generate_daily_reading()` + `generate_multi_user_reading()` + `MultiUserAnalyzer` in framework bridge)

---

## TL;DR

- Build the two most complex reading flows: **daily auto-reading** (one per user per day, cached, background scheduler) and **multi-user compatibility reading** (2-5 users, individual readings + pairwise compatibility + group analysis + AI group interpretation)
- Extend `POST /api/oracle/readings` with `reading_type: "daily"` and `reading_type: "multi"` — completing all 5 reading types on the unified endpoint
- New `oracle_daily_readings` cache table: maps `(user_id, date)` → `reading_id` for O(1) daily lookups with unique constraint preventing re-generation
- New `GET /api/oracle/daily/reading?user_id=X&date=YYYY-MM-DD` endpoint for fast cached daily reading retrieval
- Background scheduler pre-generates daily readings for all active users (asyncio task on FastAPI startup)
- Frontend: `DailyReadingCard.tsx` ("Today's Reading" dashboard card), `MultiUserReadingDisplay.tsx` (individual readings + group analysis), `CompatibilityMeter.tsx` (0-100 visual gauge)
- Reuses existing `MultiUserSelector.tsx` for user selection and Session 7's `MultiUserAnalyzer` for compatibility math
- The `oracle_readings.sign_type` CHECK constraint already includes `'daily'` and `'multi_user'` — no schema migration needed for that

---

## OBJECTIVES

1. **Extend `ReadingOrchestrator`** with `generate_daily_reading()` and `generate_multi_user_reading()` — following the established pipeline pattern (framework bridge → AI → response)
2. **Create `oracle_daily_readings` table** with unique `(user_id, date)` constraint as a cache/lookup layer over `oracle_readings`
3. **Extend `POST /api/oracle/readings`** to accept `reading_type: "daily"` (with `user_id` + optional `date`) and `reading_type: "multi"` (with `user_ids[]` + `primary_user_index`)
4. **Create `GET /api/oracle/daily/reading`** endpoint for retrieving cached daily readings without re-generation
5. **Create `daily_scheduler.py`** background task that pre-generates daily readings for all active oracle users at a configurable time
6. **Create `DailyReadingCard.tsx`** frontend component — auto-fetches today's reading on mount, shows "no reading yet" state, displays reading with daily insights (suggested activities, energy forecast, lucky hours)
7. **Create `MultiUserReadingDisplay.tsx`** — shows individual readings in tabs + compatibility grid + group analysis section
8. **Create `CompatibilityMeter.tsx`** — animated 0-100 gauge with color coding (red <40, yellow 40-70, green >70) and dimension breakdown
9. **Write 36+ tests** covering scheduler, caching, multi-user combinations, compatibility scoring, and frontend components

---

## PREREQUISITES

- [ ] Session 14 completed — `services/oracle/oracle_service/reading_orchestrator.py` has `ReadingOrchestrator` with `generate_time_reading()` and the established 4-step pipeline pattern
- [ ] Session 14 completed — `api/app/models/oracle.py` has `FrameworkReadingResponse`, `AIInterpretationSections`, `FrameworkConfidence`, `PatternDetected`, `FrameworkNumerologyData`
- [ ] Session 14 completed — `POST /api/oracle/readings` endpoint exists and returns `FrameworkReadingResponse`
- [ ] Session 15 completed — `ReadingOrchestrator` has `generate_name_reading()` and `generate_question_reading()`; `POST /api/oracle/readings` accepts `reading_type: "name"` and `reading_type: "question"` via request body discriminator
- [ ] Session 7 completed — `services/oracle/oracle_service/framework_bridge.py` has `generate_daily_reading()` and `generate_multi_user_reading()`
- [ ] Session 7 completed — `services/oracle/oracle_service/multi_user_analyzer.py` has `MultiUserAnalyzer` with compatibility matrices and `analyze_group()`
- [ ] Session 7 completed — `services/oracle/oracle_service/models/reading_types.py` has `UserProfile`, `ReadingResult`, `MultiUserResult`, `CompatibilityResult`
- Verification:
  ```bash
  python3 -c "from services.oracle.oracle_service.reading_orchestrator import ReadingOrchestrator; print('Orchestrator OK')"
  python3 -c "from services.oracle.oracle_service.framework_bridge import generate_daily_reading, generate_multi_user_reading; print('Bridge OK')"
  python3 -c "from services.oracle.oracle_service.multi_user_analyzer import MultiUserAnalyzer; print('Analyzer OK')"
  python3 -c "from api.app.models.oracle import FrameworkReadingResponse; print('Models OK')"
  test -f frontend/src/components/oracle/MultiUserSelector.tsx && echo "MultiUserSelector OK"
  ```

---

## FILES TO CREATE

- `database/migrations/016_daily_readings_cache.sql` — Migration for `oracle_daily_readings` cache table
- `services/oracle/oracle_service/daily_scheduler.py` — Background asyncio task for pre-generating daily readings
- `frontend/src/components/oracle/DailyReadingCard.tsx` — "Today's Reading" dashboard card
- `frontend/src/components/oracle/MultiUserReadingDisplay.tsx` — Side-by-side multi-user results + group analysis
- `frontend/src/components/oracle/CompatibilityMeter.tsx` — Visual compatibility score (0-100)
- `frontend/src/components/oracle/__tests__/DailyReadingCard.test.tsx` — 4 tests
- `frontend/src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx` — 4 tests
- `api/tests/test_daily_reading.py` — 8 tests for daily reading API + caching
- `api/tests/test_multi_user_framework_reading.py` — 8 tests for framework-based multi-user readings
- `services/oracle/tests/test_daily_orchestrator.py` — 12 tests for daily + multi-user orchestrator flows

## FILES TO MODIFY

- `api/app/models/oracle.py` — Add `DailyReadingRequest`, `MultiUserFrameworkRequest`, `DailyReadingCacheResponse`, `PairwiseCompatibilityResult`, `GroupAnalysisResult`, `MultiUserFrameworkResponse` models
- `api/app/routers/oracle.py` — Extend `POST /api/oracle/readings` for daily + multi; add `GET /api/oracle/daily/reading`
- `api/app/services/oracle_reading.py` — Add `create_daily_reading()`, `get_cached_daily_reading()`, `create_multi_user_framework_reading()` methods
- `services/oracle/oracle_service/reading_orchestrator.py` — Add `generate_daily_reading()` and `generate_multi_user_reading()` methods
- `api/app/orm/oracle_reading.py` — Add `OracleDailyReading` ORM model
- `api/app/main.py` — Register daily scheduler on startup/shutdown
- `frontend/src/types/index.ts` — Add `DailyReadingRequest`, `MultiUserFrameworkRequest`, `DailyReadingCacheResponse`, `PairwiseCompatibilityResult`, `MultiUserFrameworkResponse` types
- `frontend/src/services/api.ts` — Add `oracle.dailyReading()`, `oracle.getDailyReading()`, `oracle.multiUserFrameworkReading()` methods
- `frontend/src/hooks/useOracleReadings.ts` — Add `useDailyReading()`, `useGenerateDailyReading()`, `useSubmitMultiUserReading()` hooks

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Database Migration — `oracle_daily_readings` Cache Table (~20 min)

**Tasks:**

1. Create `database/migrations/016_daily_readings_cache.sql`:

   ```sql
   -- Migration 016: Daily readings cache table
   -- Session 16 — daily reading lookup/cache layer

   BEGIN;

   CREATE TABLE IF NOT EXISTS oracle_daily_readings (
       id BIGSERIAL PRIMARY KEY,
       user_id INTEGER NOT NULL REFERENCES oracle_users(id) ON DELETE CASCADE,
       reading_date DATE NOT NULL,
       reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
       generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
       CONSTRAINT uq_daily_user_date UNIQUE (user_id, reading_date)
   );

   COMMENT ON TABLE oracle_daily_readings IS 'Cache/lookup: maps (user_id, date) → oracle_readings.id for daily readings';
   COMMENT ON COLUMN oracle_daily_readings.reading_date IS 'Calendar date (no time) — one reading per user per day';
   COMMENT ON CONSTRAINT uq_daily_user_date ON oracle_daily_readings IS 'Ensures at most one daily reading per user per day';

   CREATE INDEX IF NOT EXISTS idx_daily_readings_user_date ON oracle_daily_readings(user_id, reading_date DESC);
   CREATE INDEX IF NOT EXISTS idx_daily_readings_reading_id ON oracle_daily_readings(reading_id);

   INSERT INTO schema_migrations (version, name) VALUES ('016', 'daily_readings_cache')
   ON CONFLICT DO NOTHING;

   COMMIT;
   ```

2. Design notes:
   - `oracle_daily_readings` is a **thin cache/lookup table** — the actual reading data lives in `oracle_readings` (with `sign_type='daily'`)
   - The unique constraint `(user_id, reading_date)` enforces one-per-user-per-day at the database level
   - `reading_date` is `DATE` type (not `TIMESTAMPTZ`) — we compare calendar days, not timestamps
   - The `oracle_readings.sign_type` CHECK constraint already includes `'daily'` and `'multi_user'` (see `database/init.sql:253`) — no constraint migration needed
   - No denormalized fields in the cache table — framework data and AI interpretation are accessed via the `reading_id` FK join

**Checkpoint:**

- [ ] Migration SQL is syntactically valid: `docker-compose exec postgres psql -U nps -d nps -f /docker-entrypoint-initdb.d/migrations/016_daily_readings_cache.sql`
- [ ] `oracle_daily_readings` table exists with unique constraint on `(user_id, reading_date)`
- [ ] `schema_migrations` has row with version '016'
- Verify: `docker-compose exec postgres psql -U nps -d nps -c "\d oracle_daily_readings"`

🚨 STOP if checkpoint fails

---

### Phase 2: New Pydantic & ORM Models (~40 min)

**Tasks:**

1. Add ORM model to `api/app/orm/oracle_reading.py`:

   ```python
   class OracleDailyReading(Base):
       """Cache/lookup: maps (user_id, date) to an oracle reading."""
       __tablename__ = "oracle_daily_readings"

       id = Column(BigInteger, primary_key=True, autoincrement=True)
       user_id = Column(Integer, ForeignKey("oracle_users.id", ondelete="CASCADE"), nullable=False)
       reading_date = Column(Date, nullable=False)
       reading_id = Column(BigInteger, ForeignKey("oracle_readings.id", ondelete="CASCADE"), nullable=False)
       generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

       __table_args__ = (
           UniqueConstraint("user_id", "reading_date", name="uq_daily_user_date"),
       )
   ```

2. Add new Pydantic models to `api/app/models/oracle.py`:

   **`DailyReadingRequest`** — for `POST /api/oracle/readings` with `reading_type: "daily"`:

   ```python
   class DailyReadingRequest(BaseModel):
       user_id: int
       reading_type: str = "daily"                          # Literal["daily"]
       date: str | None = None                              # "YYYY-MM-DD", defaults to today
       locale: str = "en"
       numerology_system: str = "auto"
       force_regenerate: bool = False                       # If True, ignore cache and regenerate

       @field_validator("date")
       @classmethod
       def validate_date_format(cls, v: str | None) -> str | None:
           """Validate YYYY-MM-DD format if provided."""
           if v is None:
               return v
           parts = v.split("-")
           if len(parts) != 3:
               raise ValueError("Date must be YYYY-MM-DD format")
           year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
           if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
               raise ValueError("Invalid date values")
           return v
   ```

   **`MultiUserFrameworkRequest`** — for `POST /api/oracle/readings` with `reading_type: "multi"`:

   ```python
   class MultiUserFrameworkRequest(BaseModel):
       user_ids: list[int]                                  # 2-5 oracle_user IDs
       primary_user_index: int = 0                          # Index into user_ids for primary user
       reading_type: str = "multi"                          # Literal["multi"]
       date: str | None = None                              # "YYYY-MM-DD", defaults to today
       locale: str = "en"
       numerology_system: str = "auto"
       include_interpretation: bool = True                  # Whether to include AI group interpretation

       @field_validator("user_ids")
       @classmethod
       def validate_user_count(cls, v: list[int]) -> list[int]:
           if len(v) < 2:
               raise ValueError("At least 2 users are required")
           if len(v) > 5:
               raise ValueError("Maximum 5 users allowed")
           if len(v) != len(set(v)):
               raise ValueError("Duplicate user IDs not allowed")
           return v

       @field_validator("primary_user_index")
       @classmethod
       def validate_primary_index(cls, v: int, info) -> int:
           user_ids = info.data.get("user_ids", [])
           if user_ids and (v < 0 or v >= len(user_ids)):
               raise ValueError(f"primary_user_index must be 0-{len(user_ids) - 1}")
           return v
   ```

   **`DailyReadingCacheResponse`** — for `GET /api/oracle/daily/reading`:

   ```python
   class DailyReadingCacheResponse(BaseModel):
       user_id: int
       date: str                                            # "YYYY-MM-DD"
       reading: FrameworkReadingResponse | None = None      # The cached reading, or null if not generated yet
       cached: bool = False                                 # True if reading was served from cache
       generated_at: str | None = None                      # ISO 8601 timestamp of generation
   ```

   **`PairwiseCompatibilityResult`** — individual pair compatibility:

   ```python
   class PairwiseCompatibilityResult(BaseModel):
       user_a_name: str
       user_b_name: str
       user_a_id: int
       user_b_id: int
       overall_score: float                                 # 0.0-1.0 weighted combination
       overall_percentage: int                              # 0-100 for display
       classification: str                                  # "excellent"/"good"/"moderate"/"challenging"
       dimensions: dict[str, float]                         # {"life_path": 0.8, "element": 0.9, ...}
       strengths: list[str]                                 # Dimensions scoring >= 0.7
       challenges: list[str]                                # Dimensions scoring <= 0.3
       description: str                                     # Human-readable summary
   ```

   **`GroupAnalysisResult`** — group-level analysis:

   ```python
   class GroupAnalysisResult(BaseModel):
       group_harmony_score: float                           # 0.0-1.0 (average of all pairwise)
       group_harmony_percentage: int                        # 0-100
       element_balance: dict[str, int]                      # {"Wood": 2, "Fire": 1, ...}
       animal_distribution: dict[str, int]                  # {"Rat": 1, "Dragon": 1, ...}
       dominant_element: str
       dominant_animal: str
       group_summary: str                                   # Human-readable group dynamic description
   ```

   **`MultiUserFrameworkResponse`** — extends FrameworkReadingResponse pattern:

   ```python
   class MultiUserFrameworkResponse(BaseModel):
       id: int | None = None                                # reading_id if stored
       user_count: int
       pair_count: int                                      # N*(N-1)/2
       computation_ms: float
       individual_readings: list[FrameworkReadingResponse]   # One per user
       pairwise_compatibility: list[PairwiseCompatibilityResult]
       group_analysis: GroupAnalysisResult | None = None    # Only for 3+ users
       ai_interpretation: AIInterpretationSections | None = None  # AI group interpretation
       locale: str = "en"
       created_at: str
   ```

**Checkpoint:**

- [ ] `python3 -c "from api.app.models.oracle import DailyReadingRequest, MultiUserFrameworkRequest, MultiUserFrameworkResponse; print('Models OK')"` — imports without error
- [ ] `DailyReadingRequest(user_id=1)` validates (date defaults to None)
- [ ] `MultiUserFrameworkRequest(user_ids=[1, 2])` validates
- [ ] `MultiUserFrameworkRequest(user_ids=[1])` raises ValidationError (too few)
- [ ] `MultiUserFrameworkRequest(user_ids=[1, 1, 2])` raises ValidationError (duplicates)
- Verify: `cd api && python3 -c "from app.models.oracle import DailyReadingRequest; r = DailyReadingRequest(user_id=1); print(r.model_dump())"`

🚨 STOP if checkpoint fails

---

### Phase 3: ReadingOrchestrator Extensions (~60 min)

**Tasks:**

1. Add `generate_daily_reading()` to `services/oracle/oracle_service/reading_orchestrator.py`:

   ```python
   async def generate_daily_reading(
       self,
       user_profile: UserProfile,
       target_date: Optional[datetime] = None,
       locale: str = "en",
   ) -> dict:
       """Full pipeline for daily reading.

       Uses noon (12:00:00) as the reading time — neutral midday energy.
       Adds daily_insights dict (suggested_activities, energy_forecast,
       lucky_hours, focus_area, element_of_day) from framework bridge.
       Returns dict matching FrameworkReadingResponse fields + daily_insights.
       """
       total_steps = 4
       start = time.perf_counter()

       # Step 1: Generate framework reading via bridge
       await self._send_progress(1, total_steps, "Generating daily reading...", "daily")
       reading_result = self._call_framework_daily(user_profile, target_date)

       # Step 2: AI interpretation
       await self._send_progress(2, total_steps, "Interpreting today's energy...", "daily")
       ai_sections = self._call_ai_interpreter(
           reading_result.framework_output, locale,
           context_hint="daily_reading"
       )

       # Step 3: Format response
       await self._send_progress(3, total_steps, "Formatting response...", "daily")
       response = self._build_daily_response(reading_result, ai_sections, locale)

       # Step 4: Done
       elapsed = (time.perf_counter() - start) * 1000
       await self._send_progress(4, total_steps, "Done", "daily")
       logger.info("Daily reading generated", extra={"elapsed_ms": elapsed})

       return response

   def _call_framework_daily(self, user, target_date):
       """Invoke framework_bridge.generate_daily_reading().

       Uses hour=12 (noon) for neutral midday energy. Adds daily_insights
       dict to ReadingResult: suggested_activities, energy_forecast,
       lucky_hours, focus_area, element_of_day.
       """
       from framework_bridge import generate_daily_reading
       return generate_daily_reading(user, target_date)

   def _build_daily_response(self, reading_result, ai_sections, locale) -> dict:
       """Build response dict for daily reading.

       Includes daily_insights from framework bridge output.
       """
       fw = reading_result.framework_output
       base = self._build_response(reading_result, ai_sections, locale)
       base["reading_type"] = "daily"
       base["sign_value"] = reading_result.sign_value  # date string "YYYY-MM-DD"
       # daily_insights populated by framework_bridge.generate_daily_reading()
       base["daily_insights"] = getattr(reading_result, 'daily_insights', None) or fw.get("daily_insights", {})
       return base
   ```

2. Add `generate_multi_user_reading()` to `ReadingOrchestrator`:

   ```python
   async def generate_multi_user_reading(
       self,
       user_profiles: list[UserProfile],
       primary_index: int = 0,
       target_date: Optional[datetime] = None,
       locale: str = "en",
       include_interpretation: bool = True,
   ) -> dict:
       """Full pipeline for multi-user compatibility reading.

       Generates individual readings for each user, then runs Session 7's
       MultiUserAnalyzer for pairwise compatibility + group analysis.
       Optionally invokes AI for group interpretation.
       Returns dict matching MultiUserFrameworkResponse fields.
       """
       total_steps = 5
       start = time.perf_counter()
       n_users = len(user_profiles)

       # Step 1: Generate individual readings for each user
       await self._send_progress(1, total_steps, f"Generating readings for {n_users} users...", "multi")
       individual_results = self._call_framework_multi(user_profiles, target_date)

       # Step 2: Run compatibility analysis via Session 7's MultiUserAnalyzer
       await self._send_progress(2, total_steps, "Analyzing compatibility...", "multi")
       multi_result = self._call_multi_analyzer(individual_results)

       # Step 3: AI group interpretation (optional)
       ai_sections = None
       if include_interpretation:
           await self._send_progress(3, total_steps, "Generating group interpretation...", "multi")
           ai_sections = self._call_ai_group_interpreter(
               individual_results, multi_result, locale
           )
       else:
           await self._send_progress(3, total_steps, "Skipping AI interpretation...", "multi")

       # Step 4: Format response
       await self._send_progress(4, total_steps, "Formatting response...", "multi")
       response = self._build_multi_response(
           user_profiles, individual_results, multi_result,
           ai_sections, primary_index, locale
       )

       # Step 5: Done
       elapsed = (time.perf_counter() - start) * 1000
       await self._send_progress(5, total_steps, "Done", "multi")
       logger.info("Multi-user reading generated", extra={
           "elapsed_ms": elapsed, "user_count": n_users,
           "pair_count": n_users * (n_users - 1) // 2,
       })

       response["computation_ms"] = elapsed
       return response
   ```

3. Multi-user helper methods:

   ```python
   def _call_framework_multi(self, users, target_date):
       """Invoke framework_bridge.generate_multi_user_reading().

       Returns list of ReadingResult objects, one per user.
       """
       from framework_bridge import generate_multi_user_reading
       return generate_multi_user_reading(users, target_date=target_date)

   def _call_multi_analyzer(self, individual_results):
       """Invoke Session 7's MultiUserAnalyzer.analyze_group().

       Uses the compatibility matrices defined in Session 7:
       - Element: Wu Xing productive/controlling cycles
       - Animal: Secret friends, trine harmony, clash pairs
       - Life Path: Same number, sum-to-9, master pairs
       - Moon: Same phase, adjacent, opposite
       - Pattern: Shared pattern types

       Weighted: LP 30%, Element 25%, Animal 20%, Moon 15%, Pattern 10%
       """
       from multi_user_analyzer import MultiUserAnalyzer
       return MultiUserAnalyzer.analyze_group(individual_results)

   def _call_ai_group_interpreter(self, individual_results, multi_result, locale) -> dict:
       """Invoke AI interpreter with group context.

       Combines individual reading data + compatibility scores for AI to
       generate a cohesive group narrative.
       """
       try:
           from engines.ai_interpreter import interpret_group_reading
           context = {
               "individual_readings": [r.framework_output for r in individual_results],
               "compatibility": multi_result.pairwise_scores,
               "group_summary": multi_result.group_summary,
           }
           result = interpret_group_reading(context, locale=locale)
           return result.to_dict() if hasattr(result, 'to_dict') else result
       except Exception:
           logger.warning("AI group interpretation unavailable", exc_info=True)
           return {"full_text": multi_result.group_summary or "", "header": ""}

   def _build_multi_response(self, profiles, individual, multi, ai, primary_idx, locale) -> dict:
       """Build response dict matching MultiUserFrameworkResponse fields.

       Maps Session 7's MultiUserResult fields to API response format.
       """
       n = len(profiles)
       individual_responses = []
       for user, reading in zip(profiles, individual):
           resp = self._build_response(reading, None, locale)
           resp["reading_type"] = "multi"
           individual_responses.append(resp)

       pairwise = []
       for pair_result in multi.pairwise_scores:
           pairwise.append({
               "user_a_name": pair_result.user_a_name,
               "user_b_name": pair_result.user_b_name,
               "user_a_id": pair_result.user_a_id,
               "user_b_id": pair_result.user_b_id,
               "overall_score": pair_result.overall_score,
               "overall_percentage": int(pair_result.overall_score * 100),
               "classification": pair_result.classification,
               "dimensions": pair_result.dimension_scores,
               "strengths": pair_result.strengths,
               "challenges": pair_result.challenges,
               "description": pair_result.description,
           })

       group_analysis = None
       if n >= 3 and multi.group_summary:
           group_analysis = {
               "group_harmony_score": multi.group_harmony_score,
               "group_harmony_percentage": int(multi.group_harmony_score * 100),
               "element_balance": multi.group_element_balance,
               "animal_distribution": multi.animal_distribution,
               "dominant_element": multi.dominant_element,
               "dominant_animal": multi.dominant_animal,
               "group_summary": multi.group_summary,
           }

       return {
           "user_count": n,
           "pair_count": n * (n - 1) // 2,
           "computation_ms": 0,  # Set by caller after timing
           "individual_readings": individual_responses,
           "pairwise_compatibility": pairwise,
           "group_analysis": group_analysis,
           "ai_interpretation": ai,
           "locale": locale,
       }
   ```

4. Update `_send_progress()` to accept `reading_type` parameter:

   ```python
   async def _send_progress(self, step: int, total: int, message: str, reading_type: str = "time") -> None:
       if self.progress_callback:
           await self.progress_callback(step, total, message, reading_type)
   ```

**Checkpoint:**

- [ ] `ReadingOrchestrator` still instantiates — no regression on existing time/name/question methods
- [ ] `generate_daily_reading()` returns dict with all `FrameworkReadingResponse` keys plus `daily_insights`
- [ ] `generate_multi_user_reading()` returns dict with `individual_readings` (list), `pairwise_compatibility` (list), `group_analysis` (dict or None)
- [ ] Multi-user with 2 users → 1 pairwise; 3 users → 3 pairwise; 5 users → 10 pairwise
- [ ] AI failure in group interpretation falls back to `group_summary` text
- [ ] Progress callback called 4 times for daily, 5 times for multi-user
- Verify: `cd services/oracle && python3 -c "from oracle_service.reading_orchestrator import ReadingOrchestrator; print('Orchestrator extended OK')"`

🚨 STOP if checkpoint fails

---

### Phase 4: API Service Layer (~60 min)

**Tasks:**

1. Add daily reading methods to `api/app/services/oracle_reading.py`:

   **`create_daily_reading()`** — generates or retrieves cached daily reading:

   ```python
   async def create_daily_reading(
       self,
       user_id: int,
       date_str: str | None,
       locale: str,
       numerology_system: str,
       force_regenerate: bool = False,
       progress_callback=None,
   ) -> dict:
       """Create a daily reading (or return cached version).

       1. Check oracle_daily_readings for existing (user_id, date)
       2. If found and not force_regenerate: return cached reading from oracle_readings
       3. If not found: generate via orchestrator, store in oracle_readings, create cache entry
       """
       target_date_str = date_str or datetime.now().strftime("%Y-%m-%d")
       target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
       reading_date = target_date.date()

       # Check cache (unless force_regenerate)
       if not force_regenerate:
           cached = self._get_daily_cache(user_id, reading_date)
           if cached:
               return cached

       # Load user, build profile, generate reading
       oracle_user = self._get_oracle_user(user_id)
       user_profile = self._build_user_profile(oracle_user, numerology_system)

       from oracle_service.reading_orchestrator import ReadingOrchestrator
       orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
       result = await orchestrator.generate_daily_reading(
           user_profile, target_date, locale
       )

       # Store in oracle_readings
       reading = self.store_reading(
           user_id=user_id,
           sign_type="daily",
           sign_value=target_date_str,
           question=None,
           reading_result=result.get("framework_result"),
           ai_interpretation=result.get("ai_interpretation", {}).get("full_text"),
       )

       # Create cache entry in oracle_daily_readings
       self._create_daily_cache(user_id, reading_date, reading.id)

       result["id"] = reading.id
       result["created_at"] = reading.created_at.isoformat() if hasattr(reading.created_at, 'isoformat') else str(reading.created_at)
       return result
   ```

   **`get_cached_daily_reading()`** — retrieves cached daily reading without generation:

   ```python
   def get_cached_daily_reading(self, user_id: int, date_str: str | None) -> dict | None:
       """Get cached daily reading for a user and date. Returns None if not cached."""
       target_date_str = date_str or datetime.now().strftime("%Y-%m-%d")
       target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
       return self._get_daily_cache(user_id, target_date)
   ```

   **Private helpers:**

   ```python
   def _get_daily_cache(self, user_id: int, reading_date) -> dict | None:
       """Look up daily reading via oracle_daily_readings → oracle_readings join."""
       from app.orm.oracle_reading import OracleDailyReading, OracleReading
       import json

       cache_row = self.db.query(OracleDailyReading).filter(
           OracleDailyReading.user_id == user_id,
           OracleDailyReading.reading_date == reading_date,
       ).first()
       if not cache_row:
           return None

       reading = self.db.query(OracleReading).filter(
           OracleReading.id == cache_row.reading_id,
       ).first()
       if not reading:
           return None

       # Reconstruct response from stored reading
       reading_result = json.loads(reading.reading_result) if isinstance(reading.reading_result, str) else reading.reading_result
       return {
           "id": reading.id,
           "reading_type": "daily",
           "sign_value": reading.sign_value,
           "framework_result": reading_result or {},
           "ai_interpretation": {"full_text": reading.ai_interpretation or ""},
           "confidence": (reading_result or {}).get("confidence", {}),
           "patterns": (reading_result or {}).get("patterns", {}).get("detected", []),
           "fc60_stamp": (reading_result or {}).get("fc60_stamp", {}).get("fc60", ""),
           "numerology": (reading_result or {}).get("numerology"),
           "moon": (reading_result or {}).get("moon"),
           "ganzhi": (reading_result or {}).get("ganzhi"),
           "daily_insights": (reading_result or {}).get("daily_insights", {}),
           "locale": "en",
           "created_at": reading.created_at.isoformat() if hasattr(reading.created_at, 'isoformat') else str(reading.created_at),
           "_cached": True,
       }

   def _create_daily_cache(self, user_id: int, reading_date, reading_id: int) -> None:
       """Insert row into oracle_daily_readings. Handles race condition via unique constraint."""
       from app.orm.oracle_reading import OracleDailyReading
       from sqlalchemy.exc import IntegrityError

       try:
           cache_entry = OracleDailyReading(
               user_id=user_id,
               reading_date=reading_date,
               reading_id=reading_id,
           )
           self.db.add(cache_entry)
           self.db.flush()
       except IntegrityError:
           # Race condition: another request already cached this reading
           self.db.rollback()
           # Return the existing cached reading instead
           pass

   def _get_oracle_user(self, user_id: int):
       """Load oracle user or raise ValueError."""
       oracle_user = self.db.query(OracleUser).filter(
           OracleUser.id == user_id,
           OracleUser.deleted_at.is_(None),
       ).first()
       if not oracle_user:
           raise ValueError(f"Oracle user {user_id} not found")
       return oracle_user
   ```

2. Add `create_multi_user_framework_reading()`:

   ```python
   async def create_multi_user_framework_reading(
       self,
       user_ids: list[int],
       primary_user_index: int,
       date_str: str | None,
       locale: str,
       numerology_system: str,
       include_interpretation: bool,
       progress_callback=None,
   ) -> dict:
       """Create multi-user compatibility reading using framework pipeline.

       1. Load all oracle users by ID
       2. Build UserProfile for each
       3. Orchestrate via generate_multi_user_reading()
       4. Store in oracle_readings (is_multi_user=True) + oracle_reading_users junction
       """
       user_profiles = []
       for uid in user_ids:
           oracle_user = self._get_oracle_user(uid)
           profile = self._build_user_profile(oracle_user, numerology_system)
           user_profiles.append(profile)

       target_date = _parse_datetime(date_str) if date_str else None

       from oracle_service.reading_orchestrator import ReadingOrchestrator
       orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
       result = await orchestrator.generate_multi_user_reading(
           user_profiles, primary_user_index, target_date, locale, include_interpretation
       )

       # Store main reading
       primary_uid = user_ids[primary_user_index]
       reading = self.store_multi_user_reading(
           primary_user_id=primary_uid,
           user_ids=user_ids,
           result_dict={
               "individual_results": result.get("individual_readings"),
               "compatibility_matrix": result.get("pairwise_compatibility"),
               "combined_energy": result.get("group_analysis"),
               "user_count": result["user_count"],
               "pair_count": result["pair_count"],
               "computation_ms": result["computation_ms"],
           },
           ai_interpretation=result.get("ai_interpretation"),
       )

       result["id"] = reading.id
       result["created_at"] = reading.created_at.isoformat() if hasattr(reading.created_at, 'isoformat') else str(reading.created_at)
       return result
   ```

3. Refactor: ensure `_build_user_profile()` is a standalone reusable method (Session 14 created it; verify it's not inlined).

**Checkpoint:**

- [ ] `create_daily_reading()` generates and stores in `oracle_readings` + `oracle_daily_readings`
- [ ] Calling again for same user+date returns cached reading (no re-generation)
- [ ] `force_regenerate=True` bypasses cache
- [ ] `get_cached_daily_reading()` returns None for uncached dates
- [ ] `create_multi_user_framework_reading()` loads users, generates, stores with junction entries
- [ ] Race condition on daily cache handled via IntegrityError catch
- Verify: `cd api && python3 -c "from app.services.oracle_reading import OracleReadingService; print('Service OK')"`

🚨 STOP if checkpoint fails

---

### Phase 5: API Endpoints (~45 min)

**Tasks:**

1. Extend `POST /api/oracle/readings` in `api/app/routers/oracle.py` for daily + multi types:

   ```python
   from app.models.oracle import (
       ...,
       DailyReadingRequest,
       MultiUserFrameworkRequest,
       MultiUserFrameworkResponse,
       DailyReadingCacheResponse,
   )

   @router.post(
       "/readings",
       dependencies=[Depends(require_scope("oracle:write"))],
   )
   async def create_framework_reading(
       request: Request,
       _user: dict = Depends(get_current_user),
       svc: OracleReadingService = Depends(get_oracle_reading_service),
       audit: AuditService = Depends(get_audit_service),
   ):
       """Create a reading using the numerology framework + AI interpretation.

       Unified endpoint for all 5 reading types. The `reading_type` field in the
       request body determines the flow:
       - "time"     → TimeReadingRequest (Session 14)
       - "name"     → NameReadingRequest (Session 15)
       - "question" → QuestionReadingRequest (Session 15)
       - "daily"    → DailyReadingRequest (Session 16)
       - "multi"    → MultiUserFrameworkRequest (Session 16)
       """
       body_raw = await request.json()
       reading_type = body_raw.get("reading_type", "time")

       async def progress_callback(step, total, message, rt="time"):
           await oracle_progress.send_progress(step, total, message, reading_type=rt)

       try:
           if reading_type == "daily":
               body = DailyReadingRequest(**body_raw)
               result = await svc.create_daily_reading(
                   user_id=body.user_id,
                   date_str=body.date,
                   locale=body.locale,
                   numerology_system=body.numerology_system,
                   force_regenerate=body.force_regenerate,
                   progress_callback=progress_callback,
               )
               audit.log_reading_created(result["id"], "daily", ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"))
               svc.db.commit()
               return FrameworkReadingResponse(**result)

           elif reading_type == "multi":
               body = MultiUserFrameworkRequest(**body_raw)
               result = await svc.create_multi_user_framework_reading(
                   user_ids=body.user_ids,
                   primary_user_index=body.primary_user_index,
                   date_str=body.date,
                   locale=body.locale,
                   numerology_system=body.numerology_system,
                   include_interpretation=body.include_interpretation,
                   progress_callback=progress_callback,
               )
               audit.log_reading_created(result.get("id"), "multi_user", ip=_get_client_ip(request), key_hash=_user.get("api_key_hash"))
               svc.db.commit()
               return MultiUserFrameworkResponse(**result)

           # ... existing time/name/question branches from Sessions 14-15 preserved ...
           else:
               # Session 14 time reading / Session 15 name/question
               ...

       except ValueError as exc:
           raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
       except ValidationError as exc:
           raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
   ```

   Note: Preserve the existing time/name/question branches from Sessions 14-15 exactly as they are.

2. Add `GET /api/oracle/daily/reading` endpoint (distinct from legacy `GET /daily`):

   ```python
   @router.get(
       "/daily/reading",
       response_model=DailyReadingCacheResponse,
       dependencies=[Depends(require_scope("oracle:read"))],
   )
   def get_daily_framework_reading(
       user_id: int = Query(..., description="Oracle user ID"),
       date: str | None = Query(None, description="YYYY-MM-DD, defaults to today"),
       _user: dict = Depends(get_current_user),
       svc: OracleReadingService = Depends(get_oracle_reading_service),
   ):
       """Get cached daily reading for a user (read-only, no generation).

       Returns the cached reading if it exists, or null if not generated.
       Use POST /readings with reading_type="daily" to generate one.
       """
       cached = svc.get_cached_daily_reading(user_id, date)
       target_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

       if cached:
           return DailyReadingCacheResponse(
               user_id=user_id,
               date=target_date,
               reading=FrameworkReadingResponse(**{k: v for k, v in cached.items() if k != "_cached"}),
               cached=True,
               generated_at=cached.get("created_at"),
           )
       else:
           return DailyReadingCacheResponse(
               user_id=user_id,
               date=target_date,
               reading=None,
               cached=False,
               generated_at=None,
           )
   ```

3. Update `OracleProgressManager.send_progress()` to include `reading_type`:

   ```python
   async def send_progress(self, step: int, total: int, message: str, reading_type: str = "time"):
       payload = {
           "event": "reading_progress",
           "step": step,
           "total": total,
           "message": message,
           "reading_type": reading_type,
       }
       # broadcast to all connected WebSocket clients
   ```

4. Legacy endpoints remain untouched:
   - `GET /daily` → `DailyInsightResponse` (legacy)
   - `POST /reading/multi-user` → `MultiUserReadingResponse` (legacy)

**Checkpoint:**

- [ ] `POST /api/oracle/readings` with `{"reading_type": "daily", "user_id": 1}` returns `FrameworkReadingResponse`
- [ ] Same request again returns cached version (faster response)
- [ ] `POST /api/oracle/readings` with `{"reading_type": "multi", "user_ids": [1, 2]}` returns `MultiUserFrameworkResponse`
- [ ] `GET /api/oracle/daily/reading?user_id=1` returns `DailyReadingCacheResponse`
- [ ] Invalid `user_ids: [1]` returns 422
- [ ] WebSocket receives 4 progress events for daily, 5 for multi-user
- [ ] Legacy endpoints (`GET /daily`, `POST /reading/multi-user`) still work
- Verify: `cd api && python3 -m pytest tests/test_daily_reading.py -v -k "test_create_daily"`

🚨 STOP if checkpoint fails

---

### Phase 6: Daily Scheduler (~45 min)

**Tasks:**

1. Create `services/oracle/oracle_service/daily_scheduler.py`:

   ```python
   """Daily Reading Scheduler — pre-generates readings for active users.

   Runs as a background asyncio task registered on FastAPI startup.
   At a configurable time (default 00:05 UTC), generates daily readings
   for all active oracle users who don't have one for today yet.

   Configuration via environment variables:
       NPS_DAILY_SCHEDULER_ENABLED=true/false (default: true)
       NPS_DAILY_SCHEDULER_HOUR=0 (0-23, UTC)
       NPS_DAILY_SCHEDULER_MINUTE=5 (0-59)
   """

   import asyncio
   import logging
   import os
   from datetime import datetime, timedelta, timezone
   from typing import Optional

   logger = logging.getLogger(__name__)


   class DailyScheduler:
       """Background task that pre-generates daily readings."""

       def __init__(self, db_session_factory):
           self.db_session_factory = db_session_factory
           self._enabled = os.environ.get("NPS_DAILY_SCHEDULER_ENABLED", "true").lower() == "true"
           self._hour = int(os.environ.get("NPS_DAILY_SCHEDULER_HOUR", "0"))
           self._minute = int(os.environ.get("NPS_DAILY_SCHEDULER_MINUTE", "5"))
           self._task: Optional[asyncio.Task] = None
           self._running = False

       async def start(self):
           """Start the scheduler background task."""
           if not self._enabled:
               logger.info("Daily scheduler disabled via NPS_DAILY_SCHEDULER_ENABLED")
               return
           self._running = True
           self._task = asyncio.create_task(self._scheduler_loop())
           logger.info("Daily scheduler started (generation at %02d:%02d UTC)", self._hour, self._minute)

       async def stop(self):
           """Stop the scheduler."""
           self._running = False
           if self._task:
               self._task.cancel()
               try:
                   await self._task
               except asyncio.CancelledError:
                   pass
           logger.info("Daily scheduler stopped")

       async def _scheduler_loop(self):
           """Main loop — waits until generation time, runs, sleeps until next day."""
           while self._running:
               try:
                   now = datetime.now(timezone.utc)
                   target = now.replace(hour=self._hour, minute=self._minute, second=0, microsecond=0)
                   if now >= target:
                       target += timedelta(days=1)

                   wait_seconds = (target - now).total_seconds()
                   logger.info("Next daily generation in %.0f seconds (at %s)", wait_seconds, target)
                   await asyncio.sleep(wait_seconds)

                   await self.generate_all_daily_readings()

               except asyncio.CancelledError:
                   break
               except Exception:
                   logger.exception("Daily scheduler error — retrying in 60s")
                   await asyncio.sleep(60)

       async def generate_all_daily_readings(self) -> dict:
           """Generate daily readings for all active oracle users.

           Returns stats dict: {"total_users", "generated", "cached", "errors"}.
           """
           from app.orm.oracle_user import OracleUser
           from app.services.oracle_reading import OracleReadingService

           stats = {"total_users": 0, "generated": 0, "cached": 0, "errors": 0}
           db = self.db_session_factory()

           try:
               active_users = db.query(OracleUser).filter(
                   OracleUser.deleted_at.is_(None)
               ).all()
               stats["total_users"] = len(active_users)
               logger.info("Generating daily readings for %d active users", len(active_users))

               svc = OracleReadingService(db)
               for user in active_users:
                   try:
                       result = await svc.create_daily_reading(
                           user_id=user.id,
                           date_str=None,  # today
                           locale="en",
                           numerology_system="auto",
                           force_regenerate=False,
                       )
                       if result.get("_cached"):
                           stats["cached"] += 1
                       else:
                           stats["generated"] += 1
                   except Exception:
                       logger.warning("Failed to generate daily for user %d", user.id, exc_info=True)
                       stats["errors"] += 1

               db.commit()
               logger.info("Daily generation complete: %s", stats)
           except Exception:
               logger.exception("Critical error in daily generation")
               db.rollback()
           finally:
               db.close()

           return stats

       async def trigger_manual(self) -> dict:
           """Manually trigger daily generation (admin action)."""
           logger.info("Manual daily generation triggered")
           return await self.generate_all_daily_readings()
   ```

2. Register scheduler in `api/app/main.py`:

   ```python
   from services.oracle.oracle_service.daily_scheduler import DailyScheduler

   daily_scheduler = DailyScheduler(db_session_factory=SessionLocal)

   @app.on_event("startup")
   async def startup_daily_scheduler():
       await daily_scheduler.start()

   @app.on_event("shutdown")
   async def shutdown_daily_scheduler():
       await daily_scheduler.stop()
   ```

3. Add environment variable defaults to `.env.example`:

   ```
   NPS_DAILY_SCHEDULER_ENABLED=true
   NPS_DAILY_SCHEDULER_HOUR=0
   NPS_DAILY_SCHEDULER_MINUTE=5
   ```

**Checkpoint:**

- [ ] `DailyScheduler` instantiates without errors
- [ ] `generate_all_daily_readings()` returns stats dict
- [ ] Already-cached readings skipped (stats["cached"] > 0 on second run)
- [ ] Failed readings increment stats["errors"], don't crash the loop
- [ ] Scheduler registers on FastAPI startup
- Verify: `cd services/oracle && python3 -c "from oracle_service.daily_scheduler import DailyScheduler; print('Scheduler OK')"`

🚨 STOP if checkpoint fails

---

### Phase 7: Frontend Components (~90 min)

**Tasks:**

1. Create `frontend/src/components/oracle/DailyReadingCard.tsx`:

   ```tsx
   interface DailyReadingCardProps {
     userId: number;
     userName: string;
     onViewFull?: (reading: FrameworkReadingResponse) => void;
   }
   ```

   Component structure:
   - **Auto-fetch on mount**: Uses `useDailyReading(userId)` hook to check for cached reading
   - **"No reading yet" state**: Shows "Generate Today's Reading" button that calls `useGenerateDailyReading()` mutation
   - **Reading display**: Card layout showing:
     - Energy forecast (text + moon emoji)
     - Element of the day (colored badge)
     - Lucky hours (comma-separated list)
     - Suggested activities (bulleted list)
     - Focus area (single line)
   - **Compact card mode**: Summary view; "View Full Reading" expands or navigates
   - **Date selector**: Small calendar icon for past daily readings (defaults to today)
   - **WebSocket progress**: Progress bar during generation
   - **RTL support**: Respects locale for right-to-left layout
   - **States**: Loading (skeleton shimmer), Empty (generate button), Error (retry), Loaded (full card)

2. Create `frontend/src/components/oracle/MultiUserReadingDisplay.tsx`:

   ```tsx
   interface MultiUserReadingDisplayProps {
     result: MultiUserFrameworkResponse;
     onClose?: () => void;
   }
   ```

   Component structure:
   - **Tab navigation**: One tab per user showing individual reading
   - **Compatibility grid**: NxN grid with pairwise scores, color-coded cells
   - **Pair details**: Click cell → dimension breakdown with `CompatibilityMeter`
   - **Group analysis** (3+ users): Large `CompatibilityMeter` for group harmony, dominant element/animal badges, element balance bars, group summary
   - **AI interpretation**: Expandable section with group narrative
   - **Design**: Uses existing `MultiUserSelector.tsx` pattern for user chips; grid cells colored red (0-39), yellow (40-69), green (70-100)

3. Create `frontend/src/components/oracle/CompatibilityMeter.tsx`:

   ```tsx
   interface CompatibilityMeterProps {
     score: number; // 0-100
     label?: string; // Dimension name
     size?: "sm" | "md" | "lg";
     showPercentage?: boolean; // Default true
     animated?: boolean; // Default true
   }
   ```

   Component structure:
   - **Circular gauge** (lg) or **horizontal bar** (sm/md)
   - **Color coding**: 0-39 red, 40-69 yellow, 70-100 green
   - **Classification label**: "Excellent" (80+), "Good" (60-79), "Moderate" (40-59), "Challenging" (<40)
   - **Animation**: CSS transition on mount from 0 to target
   - **Accessible**: `role="meter"`, `aria-valuenow`, `aria-valuemin=0`, `aria-valuemax=100`

4. i18n keys to add (EN + FA):
   - `oracle.daily_reading_title` / `oracle.generate_daily` / `oracle.no_daily_reading`
   - `oracle.daily_energy_forecast` / `oracle.daily_lucky_hours` / `oracle.daily_activities` / `oracle.daily_focus` / `oracle.daily_element`
   - `oracle.multi_user_title` / `oracle.compatibility` / `oracle.group_harmony` / `oracle.group_analysis`
   - `oracle.strengths` / `oracle.challenges` / `oracle.view_full_reading` / `oracle.regenerate`

**Checkpoint:**

- [ ] `DailyReadingCard` renders with userId and userName props
- [ ] Shows "Generate" button when no cached reading
- [ ] After generating, shows daily insights
- [ ] `MultiUserReadingDisplay` renders tabs for each user + compatibility grid
- [ ] `CompatibilityMeter` renders with correct color for given score
- [ ] All components support RTL layout
- Verify: `cd frontend && npx vitest run src/components/oracle/__tests__/DailyReadingCard.test.tsx`

🚨 STOP if checkpoint fails

---

### Phase 8: Frontend API Client, Types & Hooks (~30 min)

**Tasks:**

1. Add TypeScript types to `frontend/src/types/index.ts`:

   ```typescript
   // ─── Daily Reading (Session 16) ───

   export interface DailyReadingRequest {
     user_id: number;
     reading_type: "daily";
     date?: string;
     locale?: string;
     numerology_system?: string;
     force_regenerate?: boolean;
   }

   export interface DailyInsights {
     suggested_activities: string[];
     energy_forecast: string;
     lucky_hours: number[];
     focus_area: string;
     element_of_day: string;
   }

   export interface DailyReadingCacheResponse {
     user_id: number;
     date: string;
     reading:
       | (FrameworkReadingResponse & { daily_insights?: DailyInsights })
       | null;
     cached: boolean;
     generated_at: string | null;
   }

   // ─── Multi-User Framework Reading (Session 16) ───

   export interface MultiUserFrameworkRequest {
     user_ids: number[];
     primary_user_index: number;
     reading_type: "multi";
     date?: string;
     locale?: string;
     numerology_system?: string;
     include_interpretation?: boolean;
   }

   export interface PairwiseCompatibilityResult {
     user_a_name: string;
     user_b_name: string;
     user_a_id: number;
     user_b_id: number;
     overall_score: number;
     overall_percentage: number;
     classification: string;
     dimensions: Record<string, number>;
     strengths: string[];
     challenges: string[];
     description: string;
   }

   export interface GroupAnalysisResult {
     group_harmony_score: number;
     group_harmony_percentage: number;
     element_balance: Record<string, number>;
     animal_distribution: Record<string, number>;
     dominant_element: string;
     dominant_animal: string;
     group_summary: string;
   }

   export interface MultiUserFrameworkResponse {
     id: number | null;
     user_count: number;
     pair_count: number;
     computation_ms: number;
     individual_readings: FrameworkReadingResponse[];
     pairwise_compatibility: PairwiseCompatibilityResult[];
     group_analysis: GroupAnalysisResult | null;
     ai_interpretation: AIInterpretationSections | null;
     locale: string;
     created_at: string;
   }
   ```

2. Add API methods to `frontend/src/services/api.ts`:

   ```typescript
   dailyReading: (data: import("@/types").DailyReadingRequest) =>
     request<import("@/types").FrameworkReadingResponse>("/oracle/readings", {
       method: "POST",
       body: JSON.stringify(data),
     }),

   getDailyReading: (userId: number, date?: string) =>
     request<import("@/types").DailyReadingCacheResponse>(
       `/oracle/daily/reading?user_id=${userId}${date ? `&date=${date}` : ""}`,
     ),

   multiUserFrameworkReading: (data: import("@/types").MultiUserFrameworkRequest) =>
     request<import("@/types").MultiUserFrameworkResponse>("/oracle/readings", {
       method: "POST",
       body: JSON.stringify(data),
     }),
   ```

3. Add hooks to `frontend/src/hooks/useOracleReadings.ts`:

   ```typescript
   export function useDailyReading(userId: number | null, date?: string) {
     return useQuery({
       queryKey: ["dailyReading", userId, date],
       queryFn: () => oracle.getDailyReading(userId!, date),
       enabled: !!userId,
       staleTime: 5 * 60 * 1000, // 5 min — daily readings don't change often
     });
   }

   export function useGenerateDailyReading() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: (data: import("@/types").DailyReadingRequest) =>
         oracle.dailyReading(data),
       onSuccess: (_data, variables) => {
         qc.invalidateQueries({
           queryKey: ["dailyReading", variables.user_id],
         });
         qc.invalidateQueries({ queryKey: HISTORY_KEY });
       },
     });
   }

   export function useSubmitMultiUserReading() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: (data: import("@/types").MultiUserFrameworkRequest) =>
         oracle.multiUserFrameworkReading(data),
       onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
     });
   }
   ```

**Checkpoint:**

- [ ] TypeScript compiles without errors: `cd frontend && npx tsc --noEmit`
- [ ] `oracle.dailyReading()` calls `POST /oracle/readings`
- [ ] `oracle.getDailyReading()` calls `GET /oracle/daily/reading`
- [ ] `oracle.multiUserFrameworkReading()` calls `POST /oracle/readings`
- [ ] `useDailyReading()` returns query with `data`, `isLoading`, `error`
- [ ] `useGenerateDailyReading()` invalidates daily reading cache on success
- Verify: `cd frontend && npx tsc --noEmit && echo "Types OK"`

🚨 STOP if checkpoint fails

---

### Phase 9: Tests (~60 min)

**Tasks:**

1. Create `services/oracle/tests/test_daily_orchestrator.py` — 12 tests:

   | Test                                       | Verifies                                                                                       |
   | ------------------------------------------ | ---------------------------------------------------------------------------------------------- |
   | `test_daily_reading_returns_required_keys` | All FrameworkReadingResponse keys present + `daily_insights`                                   |
   | `test_daily_reading_has_daily_insights`    | 5 insight keys: suggested_activities, energy_forecast, lucky_hours, focus_area, element_of_day |
   | `test_daily_reading_uses_noon`             | Framework called with hour=12, minute=0, second=0                                              |
   | `test_daily_reading_default_date`          | Omitting target_date defaults to today                                                         |
   | `test_daily_reading_sign_value_is_date`    | sign_value is "YYYY-MM-DD" format                                                              |
   | `test_daily_progress_callback_called`      | 4 progress events with reading_type="daily"                                                    |
   | `test_multi_reading_two_users`             | 2 users → 1 pairwise + 2 individual readings                                                   |
   | `test_multi_reading_three_users`           | 3 users → 3 pairwise + group_analysis not None                                                 |
   | `test_multi_reading_five_users`            | 5 users → 10 pairwise + 5 individual readings                                                  |
   | `test_multi_reading_group_analysis_3plus`  | group_analysis present for 3+, None for 2                                                      |
   | `test_multi_progress_callback_called`      | 5 progress events with reading_type="multi"                                                    |
   | `test_multi_ai_fallback`                   | AI failure falls back to group_summary text                                                    |

2. Create `api/tests/test_daily_reading.py` — 8 tests:

   | Test                                       | Verifies                                          |
   | ------------------------------------------ | ------------------------------------------------- |
   | `test_create_daily_reading_success`        | POST returns 200 with reading_type="daily"        |
   | `test_daily_reading_cached_on_second_call` | Same user+date returns cached (no re-generation)  |
   | `test_daily_reading_force_regenerate`      | force_regenerate=True bypasses cache              |
   | `test_daily_reading_user_not_found`        | Non-existent user_id returns 422                  |
   | `test_daily_reading_stored_in_db`          | Row in oracle_readings with sign_type="daily"     |
   | `test_daily_cache_entry_created`           | Row in oracle_daily_readings                      |
   | `test_get_daily_reading_cached`            | GET /daily/reading returns cached reading         |
   | `test_get_daily_reading_not_found`         | GET /daily/reading returns null for uncached date |

3. Create `api/tests/test_multi_user_framework_reading.py` — 8 tests:

   | Test                                        | Verifies                                 |
   | ------------------------------------------- | ---------------------------------------- |
   | `test_multi_user_reading_two_users`         | POST returns MultiUserFrameworkResponse  |
   | `test_multi_user_reading_five_users`        | 5 users produces 10 pairwise results     |
   | `test_multi_user_one_user_fails`            | user_ids=[1] returns 422                 |
   | `test_multi_user_six_users_fails`           | user_ids=[1,2,3,4,5,6] returns 422       |
   | `test_multi_user_duplicate_ids_fails`       | user_ids=[1,1,2] returns 422             |
   | `test_multi_user_reading_stored_in_db`      | Reading + junction rows in DB            |
   | `test_multi_user_individual_readings_count` | individual_readings.length == user_count |
   | `test_multi_user_compatibility_dimensions`  | Each pairwise has all 5 dimension keys   |

4. Create `frontend/src/components/oracle/__tests__/DailyReadingCard.test.tsx` — 4 tests:

   | Test                                         | Verifies                               |
   | -------------------------------------------- | -------------------------------------- |
   | `test_renders_card_title`                    | "Today's Reading" text present         |
   | `test_shows_generate_button_when_no_reading` | Generate button visible                |
   | `test_shows_daily_insights_after_generation` | Energy forecast, lucky hours displayed |
   | `test_shows_loading_state`                   | Loading spinner during generation      |

5. Create `frontend/src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx` — 4 tests:

   | Test                                    | Verifies                          |
   | --------------------------------------- | --------------------------------- |
   | `test_renders_user_tabs`                | Tab for each user present         |
   | `test_renders_compatibility_grid`       | Grid cells rendered for each pair |
   | `test_compatibility_meter_color_coding` | Red <40, yellow 40-69, green 70+  |
   | `test_group_analysis_visible_for_3plus` | Group section shown for 3+ users  |

6. All tests use mocks: framework bridge, AI interpreter, API calls, hooks.

**Checkpoint:**

- [ ] All 12 orchestrator tests pass: `cd services/oracle && python3 -m pytest tests/test_daily_orchestrator.py -v`
- [ ] All 8 daily API tests pass: `cd api && python3 -m pytest tests/test_daily_reading.py -v`
- [ ] All 8 multi-user API tests pass: `cd api && python3 -m pytest tests/test_multi_user_framework_reading.py -v`
- [ ] All 8 frontend tests pass: `cd frontend && npx vitest run src/components/oracle/__tests__/DailyReadingCard.test.tsx src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx`
- Verify: `cd api && python3 -m pytest tests/test_daily_reading.py tests/test_multi_user_framework_reading.py -v && echo "All API tests pass"`

🚨 STOP if checkpoint fails

---

### Phase 10: Final Verification (~30 min)

**Tasks:**

1. Run full test suites:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_daily_orchestrator.py -v
   cd api && python3 -m pytest tests/test_daily_reading.py tests/test_multi_user_framework_reading.py -v
   cd frontend && npx vitest run src/components/oracle/__tests__/DailyReadingCard.test.tsx src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx
   cd frontend && npx tsc --noEmit
   ```

2. Verify daily reading with curl:

   ```bash
   # Generate daily reading
   curl -s -X POST http://localhost:8000/api/oracle/readings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"user_id": 1, "reading_type": "daily", "locale": "en"}' | python3 -m json.tool

   # Verify cached (should be instant)
   curl -s -X POST http://localhost:8000/api/oracle/readings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"user_id": 1, "reading_type": "daily"}' | python3 -m json.tool

   # Get cached via GET
   curl -s http://localhost:8000/api/oracle/daily/reading?user_id=1 \
     -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
   ```

3. Verify multi-user reading:

   ```bash
   curl -s -X POST http://localhost:8000/api/oracle/readings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "reading_type": "multi",
       "user_ids": [1, 2, 3],
       "primary_user_index": 0,
       "locale": "en",
       "include_interpretation": true
     }' | python3 -m json.tool
   ```

4. Verify database storage:

   ```bash
   docker-compose exec postgres psql -U nps -d nps -c \
     "SELECT id, sign_type, sign_value, created_at FROM oracle_readings WHERE sign_type='daily' ORDER BY id DESC LIMIT 5;"

   docker-compose exec postgres psql -U nps -d nps -c \
     "SELECT * FROM oracle_daily_readings ORDER BY id DESC LIMIT 5;"

   docker-compose exec postgres psql -U nps -d nps -c \
     "SELECT id, is_multi_user, sign_type FROM oracle_readings WHERE is_multi_user=TRUE ORDER BY id DESC LIMIT 5;"

   docker-compose exec postgres psql -U nps -d nps -c \
     "SELECT * FROM oracle_reading_users ORDER BY reading_id DESC LIMIT 10;"
   ```

5. Verify WebSocket progress:

   ```bash
   # Terminal 1: connect
   wscat -c ws://localhost:8000/api/oracle/ws
   # Terminal 2: trigger daily (4 events) then multi (5 events)
   ```

6. Verify no regressions:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_reading_orchestrator.py -v
   cd api && python3 -m pytest tests/test_time_reading.py -v
   cd numerology_ai_framework && python3 tests/test_all.py
   ```

7. Lint and format:

   ```bash
   cd api && python3 -m ruff check app/ tests/ --fix && python3 -m black app/ tests/
   cd frontend && npx eslint src/ --fix && npx prettier --write src/
   cd services/oracle && python3 -m ruff check oracle_service/ tests/ --fix && python3 -m black oracle_service/ tests/
   ```

**Checkpoint:**

- [ ] All Python tests pass (0 failures across 3 test files)
- [ ] All frontend tests pass (0 failures across 2 test files)
- [ ] TypeScript compiles without errors
- [ ] Daily reading curl returns valid response with `daily_insights`
- [ ] Multi-user curl returns valid response with pairwise scores
- [ ] Second daily request returns cached reading (faster)
- [ ] Database has correct rows in all tables
- [ ] WebSocket receives correct event counts (4 daily, 5 multi)
- [ ] No regressions in existing tests
- [ ] Linter reports 0 errors

🚨 STOP if any check fails — fix before marking session complete

---

## TESTS TO WRITE

### Oracle Service Tests (`services/oracle/tests/test_daily_orchestrator.py`)

| Test                                       | Verifies                                           |
| ------------------------------------------ | -------------------------------------------------- |
| `test_daily_reading_returns_required_keys` | All FrameworkReadingResponse keys + daily_insights |
| `test_daily_reading_has_daily_insights`    | 5 insight keys present                             |
| `test_daily_reading_uses_noon`             | Framework called with hour=12                      |
| `test_daily_reading_default_date`          | Defaults to today                                  |
| `test_daily_reading_sign_value_is_date`    | sign_value = "YYYY-MM-DD"                          |
| `test_daily_progress_callback_called`      | 4 events, reading_type="daily"                     |
| `test_multi_reading_two_users`             | 1 pairwise + 2 individual                          |
| `test_multi_reading_three_users`           | 3 pairwise + group_analysis                        |
| `test_multi_reading_five_users`            | 10 pairwise + 5 individual                         |
| `test_multi_reading_group_analysis_3plus`  | group_analysis for 3+, None for 2                  |
| `test_multi_progress_callback_called`      | 5 events, reading_type="multi"                     |
| `test_multi_ai_fallback`                   | AI failure → group_summary fallback                |

### API Tests — Daily (`api/tests/test_daily_reading.py`)

| Test                                       | Verifies                      |
| ------------------------------------------ | ----------------------------- |
| `test_create_daily_reading_success`        | 200 with reading_type="daily" |
| `test_daily_reading_cached_on_second_call` | Cached, no re-generation      |
| `test_daily_reading_force_regenerate`      | Bypasses cache                |
| `test_daily_reading_user_not_found`        | 422 for bad user              |
| `test_daily_reading_stored_in_db`          | Row in oracle_readings        |
| `test_daily_cache_entry_created`           | Row in oracle_daily_readings  |
| `test_get_daily_reading_cached`            | GET returns cached            |
| `test_get_daily_reading_not_found`         | GET returns null              |

### API Tests — Multi-User (`api/tests/test_multi_user_framework_reading.py`)

| Test                                        | Verifies                         |
| ------------------------------------------- | -------------------------------- |
| `test_multi_user_reading_two_users`         | Valid MultiUserFrameworkResponse |
| `test_multi_user_reading_five_users`        | 10 pairwise results              |
| `test_multi_user_one_user_fails`            | 422 for 1 user                   |
| `test_multi_user_six_users_fails`           | 422 for 6 users                  |
| `test_multi_user_duplicate_ids_fails`       | 422 for duplicates               |
| `test_multi_user_reading_stored_in_db`      | Reading + junction rows          |
| `test_multi_user_individual_readings_count` | length == user_count             |
| `test_multi_user_compatibility_dimensions`  | 5 dimension keys per pair        |

### Frontend Tests

| Test                                         | File                             | Verifies                  |
| -------------------------------------------- | -------------------------------- | ------------------------- |
| `test_renders_card_title`                    | DailyReadingCard.test.tsx        | "Today's Reading" present |
| `test_shows_generate_button_when_no_reading` | DailyReadingCard.test.tsx        | Generate button visible   |
| `test_shows_daily_insights_after_generation` | DailyReadingCard.test.tsx        | Energy/hours displayed    |
| `test_shows_loading_state`                   | DailyReadingCard.test.tsx        | Spinner during generation |
| `test_renders_user_tabs`                     | MultiUserReadingDisplay.test.tsx | Tab per user              |
| `test_renders_compatibility_grid`            | MultiUserReadingDisplay.test.tsx | Grid cells rendered       |
| `test_compatibility_meter_color_coding`      | MultiUserReadingDisplay.test.tsx | Red/yellow/green          |
| `test_group_analysis_visible_for_3plus`      | MultiUserReadingDisplay.test.tsx | Group section for 3+      |

**Total: 36 tests** (12 orchestrator + 8 daily API + 8 multi API + 4 daily frontend + 4 multi frontend)

---

## ACCEPTANCE CRITERIA

- [ ] `POST /api/oracle/readings` with `reading_type: "daily"` returns `FrameworkReadingResponse` with `daily_insights` populated
- [ ] Daily reading cached: same user + same date returns identical reading without re-generation
- [ ] `force_regenerate: true` bypasses cache and creates new reading
- [ ] `GET /api/oracle/daily/reading?user_id=X` returns cached reading or null
- [ ] Daily scheduler pre-generates readings for all active users (verified via `generate_all_daily_readings()`)
- [ ] `POST /api/oracle/readings` with `reading_type: "multi"` returns `MultiUserFrameworkResponse`
- [ ] Multi-user response contains individual readings (one per user) + pairwise compatibility + group analysis
- [ ] Pairwise compatibility has 5 dimensions: life_path, element, animal, moon, pattern (weighted 30/25/20/15/10)
- [ ] Group analysis present for 3+ users, null for 2 users
- [ ] AI group interpretation included (or null if API key missing — graceful fallback)
- [ ] WebSocket sends 4 progress events for daily, 5 for multi-user
- [ ] `DailyReadingCard.tsx` auto-fetches and displays today's reading
- [ ] `MultiUserReadingDisplay.tsx` shows tabs + compatibility grid + group section
- [ ] `CompatibilityMeter.tsx` renders with correct color coding (red/yellow/green)
- [ ] Legacy endpoints unchanged (`GET /daily`, `POST /reading/multi-user`)
- [ ] All 36 tests pass
- [ ] TypeScript compiles without errors
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_daily_orchestrator.py -v && \
  cd ../.. && cd api && python3 -m pytest tests/test_daily_reading.py tests/test_multi_user_framework_reading.py -v && \
  cd ../frontend && npx vitest run src/components/oracle/__tests__/DailyReadingCard.test.tsx src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx && \
  npx tsc --noEmit && echo "ALL SESSION 16 ACCEPTANCE CRITERIA PASS"
  ```

---

## ERROR SCENARIOS

### Problem: Daily reading generates duplicate (unique constraint violation)

**Cause:** Race condition — two requests for same user+date arrive simultaneously.
**Fix:** `_create_daily_cache()` wraps the insert in try/except for `IntegrityError`. On conflict, the existing cached reading is returned. The database unique constraint `uq_daily_user_date` is the safety net.

### Problem: MultiUserAnalyzer import fails

**Cause:** Session 7 incomplete or `multi_user_analyzer.py` not on Python path.
**Fix:** Verify: `python3 -c "from oracle_service.multi_user_analyzer import MultiUserAnalyzer"`. Check `sys.path` includes `services/oracle`.

### Problem: Multi-user reading times out for 5 users

**Cause:** 5 individual framework readings + AI = slow (~5-10 seconds total).
**Fix:** Each reading takes ~1-2 seconds. Consider `asyncio.gather()` for parallel generation. Add timeout parameter to orchestrator (default 30s). AI timeout falls back to framework synthesis.

### Problem: Daily scheduler doesn't start

**Cause:** `on_event("startup")` not registered or import error.
**Fix:** Check FastAPI startup logs for "Daily scheduler started" message. Verify import: `python3 -c "from services.oracle.oracle_service.daily_scheduler import DailyScheduler"`. Check `api/app/main.py` has the startup handler.

### Problem: Frontend CompatibilityMeter doesn't animate

**Cause:** CSS transition not applied or component re-renders too fast.
**Fix:** Use `useEffect` with `requestAnimationFrame` to set target width after initial render. Ensure `transition-all duration-700` on the bar element.

### Problem: WebSocket progress events have wrong reading_type

**Cause:** Progress callback not passing `reading_type` through.
**Fix:** Ensure the lambda in the router passes `reading_type` to `oracle_progress.send_progress()`. Verify with `wscat`.

---

## HANDOFF

**Created:**

- `database/migrations/016_daily_readings_cache.sql` — Daily readings cache table migration
- `services/oracle/oracle_service/daily_scheduler.py` — Background task for pre-generating daily readings
- `frontend/src/components/oracle/DailyReadingCard.tsx` — "Today's Reading" dashboard card
- `frontend/src/components/oracle/MultiUserReadingDisplay.tsx` — Multi-user results + compatibility grid
- `frontend/src/components/oracle/CompatibilityMeter.tsx` — Visual 0-100 compatibility gauge
- `frontend/src/components/oracle/__tests__/DailyReadingCard.test.tsx` — 4 tests
- `frontend/src/components/oracle/__tests__/MultiUserReadingDisplay.test.tsx` — 4 tests
- `api/tests/test_daily_reading.py` — 8 tests
- `api/tests/test_multi_user_framework_reading.py` — 8 tests
- `services/oracle/tests/test_daily_orchestrator.py` — 12 tests

**Modified:**

- `api/app/models/oracle.py` — Added 6 Pydantic models (DailyReadingRequest, MultiUserFrameworkRequest, DailyReadingCacheResponse, PairwiseCompatibilityResult, GroupAnalysisResult, MultiUserFrameworkResponse)
- `api/app/routers/oracle.py` — Extended `POST /api/oracle/readings` for daily + multi; added `GET /api/oracle/daily/reading`
- `api/app/services/oracle_reading.py` — Added daily + multi-user service methods + cache helpers
- `services/oracle/oracle_service/reading_orchestrator.py` — Added `generate_daily_reading()`, `generate_multi_user_reading()` + helper methods
- `api/app/orm/oracle_reading.py` — Added `OracleDailyReading` ORM model
- `api/app/main.py` — Registered daily scheduler on startup/shutdown
- `frontend/src/types/index.ts` — Added 7 TypeScript interfaces
- `frontend/src/services/api.ts` — Added 3 API methods
- `frontend/src/hooks/useOracleReadings.ts` — Added 3 hooks

**Deleted:**

- None

**Next session needs:**

- Session 17 (Reading History & Persistence) builds on all 5 reading types now complete (time, name, question, daily, multi)
- Session 17 adds history browsing, filtering by reading_type, pagination, and reading detail views
- `DailyReadingCard` can be placed on the main dashboard in Session 19+ (Frontend Core)
- `MultiUserReadingDisplay` connects to existing `MultiUserSelector.tsx` for the complete flow
- `CompatibilityMeter` is reusable for any score display in later sessions
- The daily scheduler runs at UTC midnight — production may need timezone configuration
- All 5 reading types flow through the unified `POST /api/oracle/readings` endpoint
