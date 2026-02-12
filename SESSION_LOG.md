# SESSION_LOG.md — Development Session Tracker

> Claude Code reads this at step 2 of every session.
> Update at the END of every session.

---

## Project State Summary

**Plan:** 45-session Oracle rebuild (hybrid approach)
**Strategy:** Keep infrastructure, rewrite Oracle logic
**Sessions completed:** 9 of 45
**Last session:** Session 9 — Signal Processing & Patterns
**Current block:** Calculation Engines (Sessions 6-12)

---

## Pre-Build State (Before Session 1)

The 16-session scaffolding process produced 45,903 lines of code:

- Working database schema (PostgreSQL init.sql + migrations)
- API skeleton with 13 Oracle endpoints (FastAPI)
- Frontend with 20+ React components (Oracle UI, Persian keyboard, calendar)
- Oracle service structure with legacy engines copied in
- Integration tests (56+), Playwright E2E (8 scenarios)
- Docker Compose (7 containers), Dockerfiles, nginx config
- Auth middleware (JWT + API key), encryption (AES-256-GCM)

**What works:** Infrastructure, database, auth, encryption, basic API routing
**What needs rewrite:** Oracle engines, reading logic, AI interpretation, translation, frontend Oracle internals

---

## Session-to-Spec Mapping

The .specs/ folder contains specs from the 16-session scaffolding. They are REFERENCE ONLY — not execution targets. For the 45-session rebuild, session specs are created in `.session-specs/` using the naming convention `SESSION_[N]_SPEC.md`. Workflow:

- Claude creates the spec BEFORE starting the session
- Dave reviews and approves
- Claude executes the approved spec
- If a reference spec exists in .specs/ that covers similar ground → read it for context
- If no reference exists → build spec from CLAUDE.md block descriptions + logic/ docs

| Block                  | Sessions | Focus                           | Relevant .specs/ (reference only)                    |
| ---------------------- | -------- | ------------------------------- | ---------------------------------------------------- |
| Foundation             | 1-5      | Database schema, auth, profiles | SPEC_T4_S1, SPEC_T2_S1, SPEC_T6_S1                   |
| Calculation Engines    | 6-12     | FC60, numerology, zodiac        | logic/FC60_ALGORITHM.md, logic/NUMEROLOGY_SYSTEMS.md |
| AI & Reading Types     | 13-18    | Wisdom AI, 5 reading flows      | SPEC_T3_S3                                           |
| Frontend Core          | 19-25    | Layout, Oracle UI, results      | SPEC_T1_S1 through S4                                |
| Frontend Advanced      | 26-31    | RTL, responsive, accessibility  | SPEC_T1_S3                                           |
| Features & Integration | 32-37    | Export, share, Telegram         | SPEC_INTEGRATION_S1                                  |
| Admin & DevOps         | 38-40    | Admin UI, monitoring, backup    | SPEC_T7_S1                                           |
| Testing & Deployment   | 41-45    | Tests, optimization, deploy     | SPEC_INTEGRATION_S2                                  |

---

## Session Log

<!--
TEMPLATE — copy this for each new session:

## Session [N] — [YYYY-MM-DD]
**Terminal:** [SINGLE / T1-T7]
**Block:** [Foundation / Engines / AI / Frontend / Features / Admin / Testing]
**Task:** [One sentence]
**Spec:** [.specs/SPEC_FILE.md or "none"]

**Files changed:**
- `path/to/file1.py` — what changed
- `path/to/file2.tsx` — what changed

**Tests:** [X pass / Y fail / Z new]
**Commit:** [hash — message]
**Issues:** [Any problems, or "None"]
**Decisions:** [Any decisions with reasoning, or "None"]

**Next:** [Clear task for next session]
-->

<!-- Sessions logged below this line -->

## Session 1 — 2026-02-11

**Terminal:** SINGLE
**Block:** Foundation
**Task:** Database Schema Audit & Alignment — add missing framework columns, create oracle_settings and oracle_daily_readings tables
**Spec:** .session-specs/SESSION_1_SPEC.md

**Files changed:**

- `database/schemas/oracle_users.sql` — Added 4 columns: gender, heart_rate_bpm, timezone_hours, timezone_minutes with CHECK constraints
- `database/schemas/oracle_readings.sql` — Added 3 columns: framework_version, reading_mode, numerology_system with CHECK constraints + index; updated sign_type constraint to include 'reading', 'multi_user', 'daily'
- `database/schemas/oracle_settings.sql` — NEW: user preferences table (language, theme, numerology_system, timezone, toggles) with UNIQUE(user_id)
- `database/schemas/oracle_daily_readings.sql` — NEW: auto-generated daily readings with UNIQUE(user_id, reading_date)
- `database/migrations/012_framework_alignment.sql` — NEW: idempotent migration adding all columns + tables
- `database/migrations/012_framework_alignment_rollback.sql` — NEW: clean rollback for migration 012
- `database/seeds/oracle_seed_data.sql` — Added framework test vector user (id=100, "Test User", 2000-01-01), updated 3 existing users with gender/BPM/timezone, added oracle_settings rows for all 4 users
- `database/init.sql` — Added 4 columns to oracle_users, 3 columns to oracle_readings, added oracle_settings and oracle_daily_readings table definitions with indexes and triggers

**Tests:** SQL syntax validation pass (balanced parens + UTF-8 for all 8 files), Persian text round-trip verified (8 strings), acceptance criteria all verifiable
**Commit:** 1a42fb1 — [database] schema audit & framework alignment (#session-1)
**Issues:** None
**Decisions:**

- Kept POINT coordinate order as (longitude, latitude) — documented in schema comments, framework bridge (Session 6) must extract accordingly
- sign_type CHECK constraint in oracle_readings.sql expanded to match init.sql ('reading', 'multi_user', 'daily' added)
- Test vector user id=100 to avoid collision with seed user sequence (1-3)

**Next:** Session 2 — Authentication System Hardening (JWT refresh tokens, API key management, password policies, migration 013)

---

## Session 2 — 2026-02-11

**Terminal:** SINGLE
**Block:** Foundation
**Task:** Authentication System Hardening — moderator role, refresh tokens, logout, brute-force protection, admin registration, audit wiring
**Spec:** .session-specs/SESSION_2_SPEC.md

**Files changed:**

- `database/migrations/013_auth_hardening.sql` — NEW: adds failed_attempts, locked_until, refresh_token_hash columns to users; adds users_role_check constraint (admin/moderator/user/readonly); adds partial indexes for refresh token and lockout lookup
- `database/migrations/013_auth_hardening_rollback.sql` — NEW: clean rollback for migration 013 (drops columns, indexes, constraint)
- `api/app/orm/user.py` — Added 3 columns: failed_attempts (int, default 0), locked_until (DateTime TZ), refresh_token_hash (Text)
- `api/app/models/auth.py` — Added RegisterRequest (min_length validation), RegisterResponse, RefreshRequest, RefreshResponse; updated TokenResponse with optional refresh_token
- `api/app/middleware/auth.py` — Added moderator role to \_ROLE_SCOPES; added \_TokenBlacklist class (thread-safe, TTL cleanup); added create_refresh_token() and hash_refresh_token() helpers; \_try_jwt_auth now checks blacklist
- `api/app/routers/auth.py` — Added POST /login with brute-force protection (5 failures → 15min lockout) + refresh token generation + audit logging; added POST /refresh (token rotation); added POST /logout (JWT blacklist + clear refresh); added POST /register (admin-only, role validation, password min 8); wired audit logging to all endpoints including API key create/revoke
- `api/app/services/audit.py` — Added 7 auth-specific methods: log_auth_login, log_auth_logout, log_auth_register, log_auth_token_refresh, log_auth_lockout, log_api_key_created, log_api_key_revoked; added resource_type="auth" to log_auth_failed
- `api/tests/test_auth.py` — Extended from 15 to 56 tests: moderator scopes (3), refresh tokens (4), blacklist (5), brute-force (5), registration validation (4), token models (3), audit service (8), ORM columns (4), existing tests (15 preserved + 5 HTTP scope tests)

**Tests:** 202 pass / 0 fail / 41 new (56 total in test_auth.py)
**Commit:** a9875a6 — [api] auth system hardening: moderator role, refresh tokens, brute-force protection (#session-2)
**Issues:** None
**Decisions:**

- Kept bcrypt for password hashing (industry standard, already implemented). PBKDF2 600k serves encryption key derivation in security.py.
- In-memory token blacklist (same pattern as rate_limit.py). Migrateable to Redis in Session 38.
- One refresh token per user (column on users table, not separate table). Simpler, sufficient.
- Moderator scopes: oracle:admin + scanner:read + vault:read. No system admin, no scanner/vault write.
- Lockout: 5 failures → 15min auto-lock. Lock resets on expiry or successful login.

**Next:** Session 3 — User Profile Management (CRUD for user profiles with auth-protected endpoints, profile settings, Session 1 oracle_settings table integration)

---

## Session 3 — 2026-02-11

**Terminal:** SINGLE
**Block:** Foundation
**Task:** User Profile Management — system user CRUD (6 endpoints), oracle user ownership + new fields, migration 014, comprehensive tests
**Spec:** .session-specs/SESSION_3_SPEC.md

**Files changed:**

- `api/app/models/user.py` — NEW: 5 Pydantic models (SystemUserResponse, SystemUserListResponse, SystemUserUpdate, PasswordResetRequest, RoleChangeRequest) with field validators
- `api/app/routers/users.py` — NEW: 6 system user endpoints (list, get, update, deactivate, reset-password, change-role) with role-based access control + audit logging
- `api/app/orm/oracle_user.py` — Added 5 columns: gender, heart_rate_bpm, timezone_hours, timezone_minutes, created_by (FK → users.id)
- `api/app/models/oracle_user.py` — Added new fields to Create/Update/Response models; added name_no_digits and birthday_range validators; gender/heart_rate/coordinate validation
- `api/app/routers/oracle.py` — Added ownership filtering (created_by), coordinate helpers (\_set_coordinates, \_get_coordinates), updated \_decrypt_user with db param; non-owner access returns 404 (security: don't reveal existence)
- `api/app/services/audit.py` — Added 6 system user audit methods: log_system_user_listed, \_read, \_updated, \_deactivated, \_password_reset, \_role_changed
- `api/app/main.py` — Registered users router at /api/users
- `database/migrations/014_user_management.sql` — NEW: adds created_by FK column to oracle_users + index + moderator seed user
- `database/migrations/014_user_management_rollback.sql` — NEW: clean rollback for migration 014
- `api/tests/test_users.py` — NEW: 16 tests for system user endpoints (admin/moderator/user roles, CRUD operations, password reset, role change)
- `api/tests/test_oracle_users.py` — REWRITTEN: expanded from 25 to 34 tests; added ownership tests, new field validation, coordinate updates, Persian name roundtrip; uses mutable user context pattern for multi-user test scenarios

**Tests:** 231 pass / 0 fail / 50 new (16 system user + 34 oracle user)
**Commit:** e9a623d — [api] user management: system user CRUD, oracle user ownership + new fields (#session-3)
**Issues:** None
**Decisions:**

- Used migration 014 (not 013 as spec stated) since Session 2 already claimed 013_auth_hardening
- Used String(36) for created_by FK instead of UUID(as_uuid=False) for SQLite test compatibility
- PostgreSQL POINT type handled via raw SQL helpers with graceful SQLite fallback (try/except)
- Ownership security: non-owner access returns 404 instead of 403 to avoid revealing resource existence
- Mutable \_active_user dict pattern for test fixtures avoids FastAPI dependency override collision when testing multiple user identities

**Next:** Session 4 — Oracle Profiles Form & Validation UI (frontend rewrite of UserForm, new UserCard/UserProfileList components)

---

## Session 4 — 2026-02-11

**Terminal:** SINGLE
**Block:** Foundation
**Task:** Oracle Profiles Form & Validation UI — rewrite UserForm (13 fields, 4 sections), integrate PersianKeyboard/CalendarPicker/LocationSelector, create UserCard + UserProfileList components, expand TypeScript types
**Spec:** .session-specs/SESSION_4_SPEC.md

**Files changed:**

- `frontend/src/types/index.ts` — Added 7 fields to OracleUser (gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude, created_by), 6 fields to OracleUserCreate
- `frontend/src/components/oracle/UserForm.tsx` — Full rewrite: 13 fields in 4 sections (Identity, Family, Location, Details), PersianKeyboard toggle per Persian field, CalendarPicker replaces native date input, LocationSelector replaces country/city text inputs, gender dropdown, heart rate number input, timezone hour+minute selectors, enhanced validation (no-digits name, pre-1900 birthday, BPM 30-220 range)
- `frontend/src/components/oracle/UserCard.tsx` — NEW: compact profile card showing name/Persian name, birthday, location, gender badge, heart rate indicator, timezone display, edit/delete action buttons, selected state highlight
- `frontend/src/components/oracle/UserProfileList.tsx` — NEW: searchable card grid with useOracleUsers hook, search filter, add/edit/delete actions via UserForm modals, loading/empty/error states
- `frontend/src/components/oracle/__tests__/UserForm.test.tsx` — Rewritten: expanded from 11 to 23 tests; mocks for PersianKeyboard/CalendarPicker/LocationSelector; tests for gender select, BPM validation, timezone selectors, name no-digits, birthday before-1900, keyboard toggle+insert, component integrations, edit mode new fields, submit payload
- `frontend/src/components/oracle/__tests__/UserCard.test.tsx` — NEW: 10 tests (name+Persian, birthday, location, gender badge, heart rate, timezone, missing optionals, edit/delete callbacks, selected highlight)
- `frontend/src/components/oracle/__tests__/UserProfileList.test.tsx` — NEW: 6 tests (renders cards, search filter, loading state, empty state, add profile opens form, edit opens form)
- `frontend/src/components/oracle/__tests__/Accessibility.test.tsx` — Updated: added child component mocks, new translation keys, fixed label query for rewritten UserForm
- `frontend/vitest.config.ts` — Added e2e exclude to prevent vitest from picking up Playwright tests

**Tests:** 147 pass / 0 fail / 39 new (23 UserForm + 10 UserCard + 6 UserProfileList)
**Commit:** 481309f — [frontend] oracle profiles form & validation UI: UserForm rewrite, UserCard, UserProfileList (#session-4)
**Issues:** None
**Decisions:**

- Used `fireEvent.submit(form)` instead of `userEvent.click(submitBtn)` for form validation tests — jsdom + React 18 doesn't reliably trigger form onSubmit via button click in testing-library
- Pre-populated invalid BPM via user prop for validation test — avoids jsdom number input type quirks with event dispatching
- Added `exclude: ["e2e/**"]` to vitest.config.ts — Playwright tests were being picked up by vitest runner (pre-existing issue, fixed proactively)

**Next:** Session 5 — Location System Upgrade & Persian Keyboard Polish

---

## Session 5 — 2026-02-11

**Terminal:** SINGLE
**Block:** Foundation
**Task:** Location System Upgrade & Persian Keyboard Polish — replace hardcoded location data with API-backed static JSON (249 countries, 272 cities in 50 countries), add 3 new location endpoints, rewrite LocationSelector with searchable country/city cascading, polish PersianKeyboard with Shift key layer
**Spec:** .session-specs/SESSION_5_SPEC.md

**Files changed:**

- `api/data/countries.json` — NEW: 249 countries with bilingual EN/FA names, coordinates, timezones, phone codes (ISO 3166-1 alpha-2)
- `api/data/cities_by_country.json` — NEW: 272 cities across 50 countries with bilingual names, coordinates, timezones; priority countries (IR, US, GB, DE, FR, TR, AE, CA, AU, IN, AF, IQ, PK, SA, EG) get 8-10 cities each
- `api/app/services/location_service.py` — Full rewrite: added static data loading from JSON at module level, \_COUNTRY_BY_CODE index, 4 new methods (get_countries, get_cities, get_timezone, search_cities), \_lookup_static helper for coordinates fallback
- `api/app/routers/location.py` — Added 3 new endpoints: GET /countries (lang param), GET /countries/{code}/cities (lang param), GET /timezone (country_code + optional city)
- `api/app/models/location.py` — Added 6 new Pydantic models: CountryResponse, CountryListResponse, CityResponse, CityListResponse, TimezoneResponse, CitySearchResponse
- `frontend/src/utils/persianKeyboardLayout.ts` — Added PERSIAN_SHIFT_ROWS: 4 rows of Persian digits (۱-۰), Arabic diacritics (tanwin, fatha, etc.), Persian punctuation, common symbols
- `frontend/src/utils/geolocationHelpers.ts` — Removed hardcoded COUNTRIES constant, added Country/City interfaces, added fetchCountries()/fetchCities() async API helpers
- `frontend/src/types/index.ts` — Added countryCode and timezone fields to LocationData interface
- `frontend/src/components/oracle/PersianKeyboard.tsx` — Added isShifted state toggle between PERSIAN_ROWS and PERSIAN_SHIFT_ROWS, smart above/below positioning via getBoundingClientRect, mobile touch handlers with preventDefault, select-none CSS
- `frontend/src/components/oracle/LocationSelector.tsx` — Full rewrite: API-backed searchable country dropdown with text filter, cascading city select, manual coordinate input toggle, auto-detect via browser geolocation, bilingual labels
- `frontend/src/locales/en.json` — Added 11 new oracle keys (location_search_country, location_select_city, location_no_cities, location_manual_coords, location_latitude, location_longitude, location_timezone, location_loading_countries, location_loading_cities, keyboard_shift, keyboard_numbers)
- `frontend/src/locales/fa.json` — Added 11 corresponding Persian translation keys
- `api/tests/test_location.py` — Extended from 13 to 25 tests: 12 new (countries list, countries FA, sorted alphabetically, unauthenticated, cities Iran EN/FA, unknown country, coordinate bounds, timezone Iran/with city/unknown 404, static fallback); fixed 2 existing tests for static data compatibility
- `frontend/src/components/oracle/__tests__/PersianKeyboard.test.tsx` — 10 tests covering shift toggle, character/touch/backspace/close callbacks, Escape key, ARIA, active styling
- `frontend/src/components/oracle/__tests__/LocationSelector.test.tsx` — 7 tests with mocked API helpers covering search, country select, city cascade, auto-detect, manual coords
- `frontend/src/components/oracle/__tests__/OracleConsultationForm.test.tsx` — Fixed: added i18n.language and geolocationHelpers mock for LocationSelector compatibility

**Tests:** 243 API pass / 0 fail | 153 frontend pass / 0 fail | 24 new tests
**Commit:** 243722c — [api][frontend] upgrade location system + polish Persian keyboard (#session-5)
**Issues:** None
**Decisions:**

- Static JSON files loaded at module import time (not per-request) for zero-latency country/city lookups; graceful fallback to empty lists if files missing
- get_coordinates() checks static data BEFORE Nominatim — instant for known cities, network only for unknowns
- 249 countries (full ISO 3166-1 alpha-2 including territories) with Persian names; 50 countries have city data (272 total cities)
- PersianKeyboard shift layer shows Persian digits + diacritics + punctuation (not just symbols) — more useful for Oracle Persian text input
- LocationSelector uses API helpers (fetchCountries/fetchCities) instead of hardcoded data — future-proof for server-side additions

**Next:** Session 6 — Framework Integration: Core Setup

---

## Session 6 — 2026-02-11

**Terminal:** SINGLE
**Block:** Calculation Engines
**Task:** Framework Integration: Core Setup — integrate numerology_ai_framework via bridge module, delete 26 obsolete files (12 engines + 8 solvers + 6 logic), update all imports, create 53 bridge tests
**Spec:** .session-specs/SESSION_6_SPEC.md

**Files changed:**

- `services/oracle/oracle_service/framework_bridge.py` — NEW: single integration point between Oracle service and numerology_ai_framework (534 lines); FrameworkBridgeError, generate_single_reading, generate_multi_reading, map_oracle_user_to_framework_kwargs; 30+ backward-compatible function wrappers (encode_fc60, life_path, moon_phase, ganzhi_year, etc. with parameter order/return type translations); 20+ constant re-exports (ANIMALS, ELEMENTS, STEMS, LETTER_VALUES, LIFE_PATH_MEANINGS, etc.)
- `services/oracle/oracle_service/__init__.py` — Added project root to sys.path for framework imports
- `services/oracle/Dockerfile` — Added PYTHONPATH for framework availability in container
- `docker-compose.yml` — Added numerology_ai_framework volume mount (read-only) to oracle-service
- `services/oracle/oracle_service/server.py` — Redirected all imports from engines.fc60/engines.numerology/logic.timing_advisor to oracle_service.framework_bridge + engines.timing_advisor; removed sys import and redundant oracle_service import
- `services/oracle/oracle_service/engines/__init__.py` — Rewritten: explicit re-exports from framework_bridge + oracle + ai_interpreter + translation_service
- `services/oracle/oracle_service/engines/oracle.py` — Updated 4 lazy import blocks from engines.fc60/engines.numerology → oracle_service.framework_bridge
- `services/oracle/oracle_service/engines/timing_advisor.py` — Moved from logic/ to engines/; updated 6 lazy import blocks to use oracle_service.framework_bridge
- `services/oracle/oracle_service/engines/multi_user_service.py` — Wrapped 4 deleted module imports in try/except (Session 7 rebuild)
- `services/oracle/oracle_service/engines/learning.py` — Wrapped engines.math_analysis import in try/except with neutral fallback; redirected engines.numerology to bridge
- `services/oracle/oracle_service/engines/ai_engine.py` — Wrapped engines.scoring import in try/except with defaults fallback
- `services/oracle/oracle_service/engines/scanner_brain.py` — Existing try/except blocks handle deleted module gracefully (no changes needed)
- `services/oracle/oracle_service/engines/notifier.py` — Existing try/except blocks handle deleted modules gracefully (no changes needed)
- `services/oracle/tests/test_framework_bridge.py` — NEW: 53 tests across 12 test classes covering constants, base-60, Julian dates, FC60 encoding, Ganzhi, moon phases, numerology, self-test, symbolic reading, single/multi reading generation, DB field mapping, error handling
- `services/oracle/tests/test_engines.py` — Rewritten: imports redirected to framework_bridge; updated key assertions for bridge output format (fc60/chk/jdn/gz_name vs old stamp/iso/moon_phase keys)

**Files deleted (26):**

- `engines/fc60.py` — replaced by framework_bridge wrappers
- `engines/numerology.py` — replaced by framework_bridge wrappers
- `engines/multi_user_fc60.py` — Session 7 rewrite
- `engines/compatibility_analyzer.py` — Session 7 rewrite
- `engines/compatibility_matrices.py` — Session 7 rewrite
- `engines/group_dynamics.py` — Session 7 rewrite
- `engines/group_energy.py` — Session 7 rewrite
- `engines/math_analysis.py` — Session 8 rewrite
- `engines/scoring.py` — Session 8 rewrite
- `engines/balance.py` — unused
- `engines/perf.py` — replaced by devops monitoring
- `engines/terminal_manager.py` — scanner-only, not needed
- `solvers/` (8 files) — Session 8+ rewrite
- `logic/` (6 files + timing_advisor moved) — timing_advisor moved to engines/; rest replaced by framework
- `tests/test_multi_user_fc60.py` — tested deleted modules

**Tests:** 75 pass / 0 fail / 53 new (test_framework_bridge: 53, test_engines: 22 updated)
**Commit:** 10ae762 — [oracle] integrate numerology_ai_framework via bridge module (#session-6)
**Issues:** None
**Decisions:**

- Volume mount approach for framework in Docker (not build context change) — simpler, no risk of breaking existing COPY commands
- Bridge wraps parameter order differences: old life_path(year,month,day) → framework life_path(day,month,year)
- Bridge converts moon_phase return type: old (index,age) ← framework (name,emoji,age) via PHASE_NAMES.index()
- Bridge adds backward-compat keys to encode_fc60 output: jdn, weekday_name, weekday_planet, weekday_domain, moon_illumination, gz_name
- Deleted modules with try/except callers (scoring, math_analysis, terminal_manager, perf) degrade gracefully — no runtime crashes
- multi_user_service.py wrapped in try/except, awaiting Session 7 rewrite

**Next:** Session 7 — Multi-User Analysis Engine (rewrite compatibility + group analysis using framework bridge)

---

## Session 7 — 2026-02-11

**Terminal:** SINGLE
**Block:** Calculation Engines
**Task:** Framework Integration: Reading Types — implement 5 typed reading functions (Time, Name, Question, Daily, Multi-User), UserProfile dataclass, MultiUserAnalyzer with element/animal/life-path compatibility matrices
**Spec:** .session-specs/SESSION_7_SPEC.md

**Files changed:**

- `services/oracle/oracle_service/models/__init__.py` — NEW: package init with public exports (UserProfile, ReadingType, ReadingResult, CompatibilityResult, MultiUserResult, ReadingRequest)
- `services/oracle/oracle_service/models/reading_types.py` — NEW: 6 dataclasses (UserProfile with to_framework_kwargs(), ReadingType enum, ReadingRequest, ReadingResult, CompatibilityResult, MultiUserResult)
- `services/oracle/oracle_service/multi_user_analyzer.py` — NEW: MultiUserAnalyzer class with Wu Xing element matrix (15 pairs), Chinese zodiac animal relationships (6 secret friends, 4 trine groups, 6 clash pairs), life path scoring, moon alignment, pattern overlap; weighted pairwise scoring (LP 30% + Element 25% + Animal 20% + Moon 15% + Pattern 10%); group harmony analysis
- `services/oracle/oracle_service/framework_bridge.py` — Added 5 typed reading functions (generate_time_reading, generate_name_reading, generate_question_reading, generate_daily_reading, generate_multi_user_reading), daily insights builder with lucky hours calculation, activity/focus mappings; added imports for new models and MultiUserAnalyzer
- `services/oracle/tests/test_reading_types.py` — NEW: 27 tests across 7 classes (TimeReading 6, NameReading 5, QuestionReading 4, DailyReading 5, MultiUserReading 5, UserProfileModel 2)
- `services/oracle/tests/test_multi_user_analyzer.py` — NEW: 31 tests across 7 classes (LifePathScoring 5, ElementScoring 5, AnimalScoring 5, MoonScoring 4, PatternScoring 5, GroupAnalysis 6, weighted formula 1)

**Tests:** 198 pass / 1 pre-existing fail (grpc_server Docker path) / 58 new (27 reading types + 31 multi-user analyzer) | 123 framework pass (no regressions)
**Commit:** 0863dc3 — [oracle] implement 5 typed reading functions + multi-user compatibility analyzer (#session-7)
**Issues:** None
**Decisions:**

- Used @dataclass (not Pydantic) for Oracle service models — keeps service dependency-free; Pydantic models go in API layer (Session 13+)
- Element compatibility matrix checks both orderings → full 5x5 coverage (25 pairs) from 15 explicit entries
- Lucky hours calculated via GanzhiEngine.hour_ganzhi() matching user's birth year animal branch — each user gets exactly 2 lucky hours per day
- Daily reading uses noon (12:00:00) as neutral midday energy point for consistent daily readings
- Question vibration computed via NumerologyEngine.expression_number() with user's preferred numerology system; stored as augmented key in framework_output
- Multi-user reading dispatches to appropriate single-user function based on reading_type, then passes to MultiUserAnalyzer.analyze_group()

**Next:** Session 8 — Numerology System Selection (auto-detection logic, selector UI, API parameter for pythagorean/chaldean/abjad switching)

---

## Session 8 — 2026-02-11

**Terminal:** SINGLE
**Block:** Calculation Engines
**Task:** Numerology System Selection — Abjad letter table, script detection (Python + TypeScript), auto-selection logic, API parameter, settings persistence, frontend selector component
**Spec:** .session-specs/SESSION_8_SPEC.md

**Files changed:**

- `numerology_ai_framework/personal/abjad_table.py` — NEW: Abjad numeral system mapping (28 Arabic + 4 Persian letters), IGNORED_CHARS (diacritics), ALEF_VARIANTS, get_abjad_value() and name_to_abjad_sum() functions
- `numerology_ai_framework/personal/numerology_engine.py` — Added Abjad system support to expression_number(), soul_urge(), personality_number(); added ABJAD_VOWEL_LETTERS class var (alef, vav, ya in Arabic + Persian forms); added get_abjad_value import
- `services/oracle/oracle_service/utils/__init__.py` — NEW: utils package init
- `services/oracle/oracle_service/utils/script_detector.py` — NEW: detect_script(), contains_persian(), contains_latin(), auto_select_system() with priority: manual override > name script > locale > pythagorean default
- `services/oracle/oracle_service/framework_bridge.py` — Added resolve_numerology_system() function; updated all 5 typed reading functions with locale parameter and system resolution via auto_select_system
- `api/app/models/oracle.py` — Added NumerologySystemType Literal type; added numerology_system field to ReadingRequest, QuestionRequest, NameReadingRequest, MultiUserReadingRequest
- `api/app/orm/oracle_settings.py` — NEW: SQLAlchemy ORM for oracle_settings table (user_id FK, language, theme, numerology_system, timezone, toggles)
- `api/app/main.py` — Added oracle_settings ORM import for table registration
- `frontend/src/utils/scriptDetector.ts` — NEW: TypeScript mirror of Python script_detector (detectScript, containsPersian, containsLatin, autoSelectSystem)
- `frontend/src/components/oracle/NumerologySystemSelector.tsx` — NEW: radio group with 4 options (auto/pythagorean/chaldean/abjad), auto-detect hint, i18n
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — Integrated NumerologySystemSelector after SignTypeSelector
- `frontend/src/locales/en.json` — Added 11 numerology selector i18n keys
- `frontend/src/locales/fa.json` — Added 11 corresponding Persian translation keys
- `numerology_ai_framework/tests/test_abjad.py` — NEW: 15 tests (Abjad table values, name sums, diacritics, alef variants, Persian-specific letters, vowel equivalents, digital root)
- `services/oracle/tests/test_numerology_selection.py` — NEW: 17 tests (script detection, contains_persian/latin, auto_select_system, resolve_numerology_system with UserProfile)
- `frontend/src/utils/__tests__/scriptDetector.test.ts` — NEW: 12 tests (detectScript, containsPersian, containsLatin, autoSelectSystem)

**Tests:** 123 framework pass (no regressions) | 15 Abjad tests pass | 17 selection tests pass | 12 frontend script tests pass | 165 total frontend pass (20 files, no regressions)
**Commit:** f8a38ad — [oracle][api][frontend] numerology system selection: Abjad support, script detection, auto-selection (#session-8)
**Issues:** None
**Decisions:**

- Persian Ya (U+06CC) added alongside Arabic Ya (U+064A) in Abjad table — critical for correct Persian name calculations; both map to value 10
- Abjad soul_urge for names without long vowel letters (e.g., حمزه) correctly returns 0 — ح and ه are not vowel equivalents in Abjad tradition
- Auto-selection priority: manual override > Persian characters in name > fa locale > pythagorean default — ensures correct system without user intervention for most cases
- ORM model uses String(36) for user_id FK for SQLite test compatibility (same pattern as Session 3)
- Framework bridge resolve_numerology_system() called at the start of each typed reading function, keeping system selection centralized

**Next:** Session 9 — Zodiac & Elemental Engine (Chinese zodiac animal/element calculations, Western zodiac mapping, element balance analysis)

---

## Session 9 — 2026-02-12

**Terminal:** SINGLE
**Block:** Calculation Engines
**Task:** Signal Processing & Patterns — PatternFormatter class (4 static methods) for AI/frontend/database output, ConfidenceMapper for UI indicators, bridge integration enriching every reading with formatted patterns
**Spec:** .session-specs/SESSION_9_SPEC.md

**Files changed:**

- `services/oracle/oracle_service/pattern_formatter.py` — NEW: PatternFormatter class (sort_by_priority, format_for_ai, format_for_frontend, format_for_frontend_full, format_for_database) with priority hierarchy, badge text generation, tooltip mapping; ConfidenceMapper class (map_to_ui) with bilingual EN/FA labels, caveats for low/medium confidence
- `services/oracle/oracle_service/framework_bridge.py` — Added import of PatternFormatter + ConfidenceMapper; added \_enrich_with_patterns() function; integrated enrichment into generate_single_reading() so all typed reading functions automatically include patterns_ai, patterns_frontend, patterns_db, confidence_ui
- `services/oracle/tests/test_pattern_formatter.py` — NEW: 18 tests across 6 classes (SortByPriority 3, FormatForAI 4, FormatForFrontend 5, FormatForDatabase 2, ConfidenceMapper 4)

**Tests:** 233 pass / 1 pre-existing fail (Docker path) / 18 new | 123 framework pass (no regressions)
**Commit:** 1093261 — [oracle] signal processing & patterns: PatternFormatter, ConfidenceMapper, bridge integration (#session-9)
**Issues:** None
**Decisions:**

- Used framework's actual PRIORITY_RANK values (1-6) from SignalCombiner, not the 1-9 range in the spec — matches real framework behavior
- Added format_for_frontend_full() as extended version accepting combined_signals for tension/action data; basic format_for_frontend() works without combined signals
- Pattern enrichment happens inside generate_single_reading() so all 5 typed reading functions (time, name, question, daily, multi-user) inherit it automatically
- Confidence caveats in both EN and FA — low gets "limited data" warning, medium gets "add optional data" suggestion, high/very_high get empty string

**Next:** Session 10 — Zodiac & Elemental Engine (Chinese zodiac animal/element calculations, Western zodiac mapping, element balance analysis)

---

## Cross-Terminal Dependencies

> Only used in multi-terminal mode. Track what each terminal needs from others.

| Source | Depends On | Status | Notes                          |
| ------ | ---------- | ------ | ------------------------------ |
| —      | —          | —      | No multi-terminal sessions yet |

---

## Stitching Issues

> Track anything that needs fixing when layers connect.

| #   | Issue | Layers | Status | Fix           |
| --- | ----- | ------ | ------ | ------------- |
| —   | —     | —      | —      | No issues yet |
