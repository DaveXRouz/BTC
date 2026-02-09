# NPS — 45-Session Master Spec Generator

> **Purpose:** This file is the blueprint for Claude Code CLI terminals to generate individual `SESSION_N_SPEC.md` files.
> **How to use:** Open a Claude Code terminal in plan mode on the NPS project folder. Tell it: "Read `NPS_45_SESSION_MASTER_SPEC.md` and generate the spec for Session [N]."
> **Each session is self-contained.** Any terminal can generate any session spec without reading other sessions.
> **Output location:** `.session-specs/SESSION_[N]_SPEC.md`

---

## GLOBAL CONTEXT (Every terminal must read this)

### Project Identity
- **Name:** NPS (Numerology Puzzle Solver)
- **No version labels.** Never say "V3" or "V4." Say "legacy version" for old code.
- **Encryption prefix:** `ENC4:` (current), `ENC:` (legacy migration only)
- **Design philosophy:** Swiss watch — simple surface, sophisticated internals

### What Already Exists (Pre-Build State)
The 16-session scaffolding produced 45,903 lines:
- **Database:** PostgreSQL schema (oracle_users, oracle_readings, oracle_reading_users + indexes, migrations, seeds)
- **API:** FastAPI skeleton with 13 Oracle endpoints, auth middleware (JWT + API key), routers for health/auth/oracle/vault/location/translation/learning/scanner
- **Frontend:** React 18 + TypeScript + Tailwind + Vite with 20+ Oracle components, Persian keyboard, calendar picker, i18n config, E2E tests
- **Oracle Service:** Python gRPC service at `services/oracle/` with legacy engines copied in (WILL BE REPLACED)
- **Scanner Service:** Rust stub at `services/scanner/` (DO NOT TOUCH)
- **Infrastructure:** Docker Compose (7 containers), nginx, Dockerfiles
- **Tests:** 56+ integration tests, 8 Playwright E2E scenarios
- **DevOps:** Monitoring, alerts, logging stubs

### The Big Change: `numerology_ai_framework` Replaces Old Engines

The folder `numerology_ai_framework/` at project root contains the **final, authoritative** calculation engine. It is a complete, tested, zero-dependency Python library (5,430 lines, 180+ tests).

**Framework Architecture:**
```
numerology_ai_framework/
├── core/                          # FC60 math (1,487 lines)
│   ├── julian_date_engine.py      # Julian Date Number calculations
│   ├── base60_codec.py            # Base-60 encoding/decoding
│   ├── weekday_calculator.py      # Day-of-week from any date
│   ├── checksum_validator.py      # CHK token validation
│   └── fc60_stamp_engine.py       # Full FC60 stamp generation
├── personal/                      # Personal numerology (494 lines)
│   ├── numerology_engine.py       # Pythagorean/Chaldean/Abjad systems
│   └── heartbeat_engine.py        # BPM-based rhythm analysis
├── universal/                     # Cosmic cycles (527 lines)
│   ├── moon_engine.py             # Moon phase calculations
│   ├── ganzhi_engine.py           # Chinese zodiac (Heavenly Stems + Earthly Branches)
│   └── location_engine.py         # GPS → element mapping
├── synthesis/                     # Reading generation (2,909 lines)
│   ├── reading_engine.py          # Combines all engines into raw reading
│   ├── signal_combiner.py         # Pattern detection + signal priority
│   ├── universe_translator.py     # Raw data → human-readable sections
│   └── master_orchestrator.py     # MAIN ENTRY POINT
├── logic/                         # AI interpretation docs (7 files)
│   ├── 00_MASTER_SYSTEM_PROMPT.md # System overview for AI
│   ├── 01_INPUT_COLLECTION_GUIDE.md
│   ├── 02_CALCULATION_REFERENCE.md
│   ├── 03_INTERPRETATION_BIBLE.md # 279K — deep number meanings
│   ├── 04_READING_COMPOSITION_GUIDE.md
│   ├── 05_ERROR_HANDLING_AND_EDGE_CASES.md
│   └── 06_API_INTEGRATION_TEMPLATE.md
├── tests/                         # 180+ tests
├── eval/                          # Evaluation & audit reports
├── CLAUDE.md                      # Framework rules
├── INTEGRATION_GUIDE.md           # How to use from external code
└── README.md
```

**Key Entry Point:**
```python
from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator

reading = MasterOrchestrator.generate_reading(
    full_name="Alice Johnson",
    birth_day=15, birth_month=7, birth_year=1990,
    current_date=datetime(2026, 2, 9),
    mother_name="Barbara Johnson",
    gender="female",
    latitude=40.7, longitude=-74.0,
    actual_bpm=68,
    current_hour=14, current_minute=30, current_second=0,
    tz_hours=-5, tz_minutes=0,
    numerology_system='pythagorean',
)
```

**Two Modes:**
- **Mode A (Calculator):** Deterministic math — same input always gives same output
- **Mode B (Reader):** Interpretation + synthesis via signal_combiner

**Output Structure:** The `reading` dict contains: `numerology`, `fc60_stamp`, `moon`, `ganzhi`, `heartbeat`, `location`, `patterns`, `current`, `birth`, `person`, `confidence`, `synthesis`, `translation`

**What Gets Deleted:**
All old calculation engines in `services/oracle/oracle_service/engines/` that duplicate framework functionality:
- `fc60.py`, `numerology.py`, `multi_user_fc60.py`, `compatibility_analyzer.py`, `compatibility_matrices.py`, `group_dynamics.py`, `group_energy.py`, `math_analysis.py`, `scoring.py`
- These are replaced by the framework's engines

**What Gets Kept in `services/oracle/oracle_service/engines/`:**
- `ai_engine.py`, `ai_interpreter.py`, `ai_client.py` → Refactored to use framework output
- `config.py`, `errors.py`, `events.py`, `health.py`, `logger.py` → Infrastructure (keep)
- `security.py`, `vault.py` → Security (keep)
- `notifier.py` → Telegram notifications (keep)
- `session_manager.py`, `memory.py` → State management (keep)
- `translation_service.py` → Bilingual support (keep, refactor)
- `learner.py`, `learning.py` → Learning system (keep, refactor)
- `scanner_brain.py` → Scanner loop (keep, refactor)
- `prompt_templates.py` → AI prompts (keep, refactor to use framework's logic/ docs)

### Architecture Rules
1. **Layer separation is strict:** Frontend → API → Services → Database (no shortcuts)
2. **Scanner is STUB only** — do not plan work on it
3. **AI uses Anthropic Python SDK (HTTP API only, never CLI)**
4. **All text supports Persian UTF-8 with RTL when locale is FA**
5. **Encryption prefix is `ENC4:`**
6. **Framework imports from project root:** `from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator`

### Technology Stack
- **Frontend:** React 18 + TypeScript 5.3 + Vite 5.1 + Tailwind 3.4
- **API:** FastAPI + Python 3.11+ + SQLAlchemy 2.0 + Pydantic 2.x
- **Oracle Service:** Python + gRPC + Anthropic SDK
- **Scanner Service:** Rust + secp256k1 + tonic gRPC (stub — DO NOT TOUCH)
- **Database:** PostgreSQL 15+
- **Infrastructure:** Docker Compose (7 containers) + nginx
- **Security:** AES-256-GCM, JWT + API keys, PBKDF2 600k iterations

### Session Spec Output Format

Every generated `SESSION_N_SPEC.md` must follow this structure:

```markdown
# SESSION [N] SPEC — [Title]
**Block:** [Block Name] (Sessions X-Y)
**Estimated Duration:** [hours]
**Complexity:** [Medium / High / Very High]
**Dependencies:** [Previous session numbers or "None"]

## TL;DR
- [3-5 bullet summary of what this session builds]

## OBJECTIVES
1. [Specific, measurable objective]
2. ...

## PREREQUISITES
- [ ] [What must exist before this session starts]
- Verification: `[bash command to verify]`

## FILES TO CREATE
- `path/to/new/file.py` — [purpose]

## FILES TO MODIFY
- `path/to/existing/file.py` — [what changes]

## FILES TO DELETE
- `path/to/obsolete/file.py` — [why]

## IMPLEMENTATION PHASES

### Phase 1: [Name] ([estimated minutes])
**Tasks:**
1. [Task]
2. [Task]

**Checkpoint:**
- [ ] [Verification step]
- Verify: `[bash command]`
🚨 STOP if checkpoint fails

### Phase 2: [Name] ([estimated minutes])
...

## TESTS TO WRITE
- `path/to/test_file.py::test_name` — [what it verifies]

## ACCEPTANCE CRITERIA
- [ ] [Criterion 1 — verifiable in 2 minutes]
- [ ] [Criterion 2]
- Verify all: `[single bash command that checks everything]`

## HANDOFF
**Created:** [list of files]
**Modified:** [list of files]
**Next session needs:** [what Session N+1 depends on from this session]
```

### Reference Spec Mapping
When generating a session spec, Claude Code should also read these reference files for context:

| Block | Sessions | Read These Reference Specs |
|-------|----------|--------------------------|
| Foundation | 1-5 | `.specs/SPEC_T4_S1*`, `.specs/SPEC_T2_S1*`, `.specs/SPEC_T6_S1*` |
| Engines | 6-12 | `numerology_ai_framework/CLAUDE.md`, `numerology_ai_framework/INTEGRATION_GUIDE.md`, `logic/FC60_ALGORITHM.md` |
| AI & Readings | 13-18 | `.specs/SPEC_T3_S3*`, `numerology_ai_framework/logic/00_MASTER_SYSTEM_PROMPT.md`, `numerology_ai_framework/logic/06_API_INTEGRATION_TEMPLATE.md` |
| Frontend Core | 19-25 | `.specs/SPEC_T1_S1*` through `SPEC_T1_S4*` |
| Frontend Advanced | 26-31 | `.specs/SPEC_T1_S3*` |
| Features | 32-37 | `.specs/SPEC_INTEGRATION_S1*`, `.specs/SPEC_T2_S3*` |
| Admin & DevOps | 38-40 | `.specs/SPEC_T7_S1*` |
| Testing & Deploy | 41-45 | `.specs/SPEC_INTEGRATION_S2*` |

---

# SESSION DETAILS

---

## SESSION 1 — Database Schema Audit & Alignment

**Block:** Foundation (Sessions 1-5)
**Complexity:** High
**Dependencies:** None — this is the starting point

### What to Build
The database schema already exists from scaffolding. This session audits it, aligns it with the framework's data model, and adds any missing tables/columns.

### Detailed Instructions

1. **Audit existing schema** — Read all files in `database/schemas/` and `database/migrations/`. List every table, column, constraint, and index.

2. **Compare with framework output** — The framework's `MasterOrchestrator.generate_reading()` returns a dict with these top-level keys: `numerology`, `fc60_stamp`, `moon`, `ganzhi`, `heartbeat`, `location`, `patterns`, `current`, `birth`, `person`, `confidence`, `synthesis`, `translation`. The `reading_result` JSONB column in `oracle_readings` must store ALL of this.

3. **Add missing columns/tables:**
   - `oracle_users`: Ensure columns for `gender` (VARCHAR(20)), `heart_rate_bpm` (INTEGER), `timezone_hours` (INTEGER), `timezone_minutes` (INTEGER) exist. The framework needs these for full readings.
   - `oracle_readings`: Ensure `reading_result` JSONB can hold the full framework output. Add `framework_version` VARCHAR(20) column to track which framework version generated the reading. Add `reading_mode` VARCHAR(20) for 'full' or 'stamp_only'. Add `numerology_system` VARCHAR(20) for 'pythagorean'/'chaldean'/'abjad'.
   - `oracle_settings`: Create table for user preferences (language, theme, default numerology system, default timezone).
   - `oracle_daily_readings`: Create table for auto-generated daily readings (cron job generates one per user per day).

4. **Update migrations** — Create migration `012_framework_alignment.sql` (up) and `012_framework_alignment_rollback.sql` (down).

5. **Update seed data** — Add seed data that matches framework's test vectors (e.g., "Test User" born 2000-01-01 with Life Path 4).

6. **Verify Persian text** — Insert and retrieve Persian text in name_persian, question_persian columns. Ensure no encoding corruption.

### Files to Create/Modify
- `database/schemas/oracle_settings.sql` — NEW
- `database/schemas/oracle_daily_readings.sql` — NEW
- `database/migrations/012_framework_alignment.sql` — NEW
- `database/migrations/012_framework_alignment_rollback.sql` — NEW
- `database/schemas/oracle_users.sql` — MODIFY (add columns)
- `database/schemas/oracle_readings.sql` — MODIFY (add columns)
- `database/seeds/oracle_seed_data.sql` — MODIFY (add framework test vectors)

### Tests
- All tables created without errors
- All new columns accept valid data
- Persian text round-trips correctly (insert → select → compare)
- Foreign keys cascade correctly
- Indexes improve query performance (EXPLAIN ANALYZE)
- Migration is idempotent (run twice without errors)
- Rollback removes only new additions

### Acceptance Criteria
- [ ] `psql -c "\dt oracle_*"` shows all Oracle tables including new ones
- [ ] Framework test vector data inserted and retrievable
- [ ] Persian text `SELECT name_persian FROM oracle_users` returns uncorrupted text
- [ ] `EXPLAIN ANALYZE` shows index usage on common queries
- [ ] Migration up + down works cleanly

---

## SESSION 2 — Authentication System Hardening

**Block:** Foundation (Sessions 1-5)
**Complexity:** High (security-critical)
**Dependencies:** Session 1 (database schema)

### What to Build
Auth system already has JWT + API key scaffolding. This session hardens it: proper password hashing (PBKDF2 600k iterations), role-based access (Admin/Moderator/User), session management, and audit logging.

### Detailed Instructions

1. **Audit existing auth** — Read `api/app/middleware/auth.py`, `api/app/routers/auth.py`, `api/app/models/auth.py`. Identify what works and what needs hardening.

2. **Password hashing** — Ensure PBKDF2 with 600,000 iterations, SHA-256, 16-byte salt. Check `api/app/services/security.py`.

3. **Role system** — Three roles: `admin` (creates accounts, sees all), `moderator` (manages readings, limited user management), `user` (own data only). Roles stored in `users` table. Implement role-checking middleware.

4. **JWT improvements** — Token expiry (24h access, 7d refresh), token refresh endpoint, token blacklist on logout. Store refresh tokens in database.

5. **API key system** — Three scopes: `read` (GET only), `write` (GET + POST + PUT), `admin` (all). Keys stored hashed in database. Rate limiting per key.

6. **Audit logging** — Every auth event (login, logout, failed login, password change, role change) logged to `oracle_audit_log` table with IP, user agent, timestamp.

7. **Admin account creation** — Only admins can create new accounts. No public registration. First admin created via CLI seed command.

### Files to Create/Modify
- `api/app/middleware/auth.py` — MODIFY (add role checking, JWT refresh)
- `api/app/routers/auth.py` — MODIFY (add refresh, logout, admin-only registration)
- `api/app/models/auth.py` — MODIFY (add role model, refresh token model)
- `api/app/services/security.py` — MODIFY (verify PBKDF2 params)
- `api/app/orm/user.py` — MODIFY (add role column, refresh_token)
- `database/migrations/013_auth_hardening.sql` — NEW
- `api/tests/test_auth.py` — MODIFY (comprehensive auth tests)

### Tests
- Password hashing with correct PBKDF2 params
- JWT access token expires after 24h
- JWT refresh token works and expires after 7d
- Role middleware blocks unauthorized access
- Admin-only endpoints reject non-admin users
- Audit log records all auth events
- API key scopes enforced correctly
- Brute-force protection (lockout after 5 failed attempts)

### Acceptance Criteria
- [ ] `POST /api/auth/login` returns JWT with role claim
- [ ] `POST /api/auth/refresh` returns new access token
- [ ] Non-admin cannot access `POST /api/auth/register`
- [ ] Audit log has entries for login/logout/failed attempts
- [ ] All auth tests pass: `cd api && python3 -m pytest tests/test_auth.py -v`

---

## SESSION 3 — User Management API

**Block:** Foundation (Sessions 1-5)
**Complexity:** Medium-High
**Dependencies:** Session 1 (schema), Session 2 (auth)

### What to Build
Admin CRUD for system users (the people who log in), plus Oracle user profiles (the people readings are about — may or may not be system users).

### Detailed Instructions

1. **System user CRUD (admin only):**
   - `GET /api/users` — List all users (admin/moderator)
   - `GET /api/users/{id}` — Get user details (admin/moderator/self)
   - `PUT /api/users/{id}` — Update user (admin/self with restrictions)
   - `DELETE /api/users/{id}` — Deactivate user (admin only, soft delete)
   - `POST /api/users/{id}/reset-password` — Force password reset (admin)
   - `PUT /api/users/{id}/role` — Change role (admin only)

2. **Oracle user profiles CRUD:**
   - `POST /api/oracle/users` — Create profile (any authenticated user)
   - `GET /api/oracle/users` — List profiles (own profiles for users, all for admin)
   - `GET /api/oracle/users/{id}` — Get profile with all fields
   - `PUT /api/oracle/users/{id}` — Update profile
   - `DELETE /api/oracle/users/{id}` — Delete profile (cascade readings? → soft delete, keep readings)
   - All profiles include: name, name_persian, birthday, mother_name, mother_name_persian, gender, country, city, coordinates, heart_rate_bpm, timezone

3. **Validation:**
   - Name: 2-200 chars, no digits
   - Birthday: must be past date, not before 1900
   - Mother name: 2-200 chars
   - Gender: 'male', 'female', or null
   - Coordinates: valid lat/lng ranges
   - Persian fields: valid UTF-8 Persian characters

4. **Ownership:** Each oracle_user profile is owned by the system user who created it. Users see only their own profiles unless admin.

### Files to Create/Modify
- `api/app/routers/users.py` — NEW (system user management)
- `api/app/routers/oracle.py` — MODIFY (oracle user CRUD improvements)
- `api/app/models/oracle_user.py` — MODIFY (add new fields)
- `api/app/orm/oracle_user.py` — MODIFY (add ownership, new columns)
- `api/app/services/oracle_permissions.py` — MODIFY (ownership checks)
- `api/tests/test_oracle_users.py` — MODIFY (comprehensive tests)
- `api/tests/test_users.py` — NEW (system user tests)

### Tests
- CRUD operations for system users (admin only)
- CRUD operations for oracle profiles
- Ownership enforcement (user A cannot see user B's profiles)
- Validation rejects invalid data
- Persian names stored and retrieved correctly
- Soft delete preserves readings

### Acceptance Criteria
- [ ] All 6 system user endpoints work correctly
- [ ] All 5 oracle user endpoints work correctly
- [ ] Non-admin cannot access system user management
- [ ] Users see only their own oracle profiles
- [ ] Persian text validation works
- [ ] All tests pass: `cd api && python3 -m pytest tests/test_users.py tests/test_oracle_users.py -v`

---

## SESSION 4 — Oracle Profiles Form & Validation UI

**Block:** Foundation (Sessions 1-5)
**Complexity:** Medium
**Dependencies:** Session 3 (user API)

### What to Build
React form component for creating/editing Oracle user profiles. The form must support bilingual input (English + Persian), validate all fields client-side, and connect to the API.

### Detailed Instructions

1. **Profile form component** — `frontend/src/components/oracle/UserForm.tsx` already exists as scaffold. Rewrite it to:
   - Include all fields: name (EN), name_persian (FA), birthday (date picker), mother_name (EN), mother_name_persian (FA), gender (dropdown), country (dropdown), city (dropdown/text), coordinates (auto from city or manual), heart_rate_bpm (number input), timezone (auto-detect or manual)
   - Persian fields get the Persian keyboard popup
   - Birthday field supports both Gregorian and Jalali calendars
   - Real-time validation with per-field error messages
   - Submit sends POST/PUT to API

2. **User list component** — Show all oracle profiles for the logged-in user in a card grid. Each card shows name, birthday, and a quick "start reading" button.

3. **User selector component** — `UserSelector.tsx` already exists. Verify it works with the updated API. Must support selecting 1-5 users for multi-user readings.

4. **Hooks** — `useOracleUsers.ts` already exists. Verify it handles CRUD operations and error states.

5. **Persian keyboard** — `PersianKeyboard.tsx` already exists. Verify it attaches to all Persian input fields and types correctly.

### Files to Create/Modify
- `frontend/src/components/oracle/UserForm.tsx` — REWRITE
- `frontend/src/components/oracle/UserSelector.tsx` — VERIFY/FIX
- `frontend/src/components/oracle/PersianKeyboard.tsx` — VERIFY/FIX
- `frontend/src/hooks/useOracleUsers.ts` — VERIFY/FIX
- `frontend/src/components/oracle/UserCard.tsx` — NEW (profile card)
- `frontend/src/components/oracle/UserProfileList.tsx` — NEW (card grid)
- `frontend/src/services/api.ts` — MODIFY (add user endpoints)
- `frontend/src/types/index.ts` — MODIFY (update OracleUser type)

### Tests
- Form renders all fields
- Validation shows errors for invalid input
- Persian keyboard types correctly
- Form submits to API
- User list loads profiles
- User selector allows 1-5 selections

### Acceptance Criteria
- [ ] Profile form renders with all fields
- [ ] Validation blocks invalid submissions
- [ ] Persian keyboard works on Persian fields
- [ ] Form creates new profile via API
- [ ] User list shows all profiles for logged-in user
- [ ] All tests pass: `cd frontend && npm test`

---

## SESSION 5 — Location Service & Persian Keyboard Polish

**Block:** Foundation (Sessions 1-5)
**Complexity:** Medium-High
**Dependencies:** Session 4 (profile form)

### What to Build
GeoNames/timezone integration for location fields, and Polish the Persian keyboard for production quality.

### Detailed Instructions

1. **Location service** — `api/app/services/location_service.py` exists. Verify/rewrite:
   - Country list (static JSON, 250+ countries with EN + FA names)
   - City lookup (GeoNames API or static dataset for top cities per country)
   - Timezone from coordinates (use `timezonefinder` Python package or static lookup)
   - Auto-detect user timezone from browser (frontend sends to API)
   - Coordinates from city selection (lat/lng lookup)

2. **Location selector component** — `LocationSelector.tsx` exists. Verify/rewrite:
   - Country dropdown (searchable, shows both EN and FA names based on locale)
   - City dropdown (cascading — changes when country changes)
   - Map preview (optional — show pin on mini map if coordinates available)
   - Manual coordinate input (for power users)
   - Auto-detect button (uses browser geolocation API)

3. **Persian keyboard polish:**
   - Ensure keyboard layout matches standard Persian layout
   - Support Shift for special characters (ژ, ء, etc.)
   - Keyboard appears as popup near the focused input
   - Keyboard dismisses on click outside or Escape
   - Works on mobile (touch events)
   - Verify against `frontend/src/utils/persianKeyboardLayout.ts`

4. **Text direction handling:**
   - Persian fields get `dir="rtl"` attribute
   - English fields keep `dir="ltr"`
   - Mixed content (EN field with some Persian) keeps ltr
   - Form labels flip direction based on locale

### Files to Create/Modify
- `api/app/services/location_service.py` — REWRITE
- `api/app/routers/location.py` — MODIFY
- `frontend/src/components/oracle/LocationSelector.tsx` — REWRITE
- `frontend/src/components/oracle/PersianKeyboard.tsx` — POLISH
- `frontend/src/utils/persianKeyboardLayout.ts` — VERIFY
- `frontend/src/utils/geolocationHelpers.ts` — MODIFY
- `api/data/countries.json` — NEW (static country list EN+FA)
- `api/data/cities_by_country.json` — NEW (top cities per country)

### Tests
- Country list loads correctly in both languages
- City dropdown updates when country changes
- Coordinates auto-fill when city selected
- Timezone auto-detects from coordinates
- Persian keyboard types all Persian characters
- RTL direction applied correctly to Persian fields
- Browser geolocation detection works

### Acceptance Criteria
- [ ] Country dropdown shows 250+ countries
- [ ] City dropdown cascades from country selection
- [ ] Timezone auto-detected from location
- [ ] Persian keyboard types full Persian alphabet
- [ ] RTL direction correct on all Persian fields
- [ ] All tests pass for location and keyboard components

---

## SESSION 6 — Framework Integration: Core Setup

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** High
**Dependencies:** Session 1 (schema), Session 5 (location)

### What to Build
Integrate `numerology_ai_framework` into the Oracle service. Create the bridge layer that connects the framework to the NPS service architecture. Delete old duplicate engines.

### Detailed Instructions

1. **Verify framework works standalone:**
   ```bash
   cd numerology_ai_framework
   python3 tests/test_all.py           # 123 tests
   python3 tests/test_synthesis_deep.py # 50 tests
   python3 tests/test_integration.py    # 7 tests
   ```
   All must pass. If any fail, fix them first.

2. **Create bridge module** — `services/oracle/oracle_service/framework_bridge.py`:
   - Imports `MasterOrchestrator` from framework
   - Provides `generate_single_reading(oracle_user, reading_type, sign_value, current_datetime)` that maps NPS database fields to framework input parameters
   - Provides `generate_multi_reading(oracle_users: list, reading_type, sign_value, current_datetime)` that generates readings for each user and then combines them
   - Handles errors gracefully (framework exceptions → NPS error format)
   - Logs framework calls with timing data
   - Maps oracle_user ORM object to framework params: `name → full_name`, `birthday → birth_day/month/year`, `mother_name → mother_name`, `gender → gender`, `coordinates → latitude/longitude`, `heart_rate_bpm → actual_bpm`, `timezone_hours/minutes → tz_hours/tz_minutes`

3. **Delete old engines** that the framework replaces:
   - `services/oracle/oracle_service/engines/fc60.py`
   - `services/oracle/oracle_service/engines/numerology.py`
   - `services/oracle/oracle_service/engines/multi_user_fc60.py`
   - `services/oracle/oracle_service/engines/compatibility_analyzer.py`
   - `services/oracle/oracle_service/engines/compatibility_matrices.py`
   - `services/oracle/oracle_service/engines/group_dynamics.py`
   - `services/oracle/oracle_service/engines/group_energy.py`
   - `services/oracle/oracle_service/engines/math_analysis.py`
   - `services/oracle/oracle_service/engines/scoring.py`
   - `services/oracle/oracle_service/engines/balance.py`
   - `services/oracle/oracle_service/engines/perf.py`
   - `services/oracle/oracle_service/engines/terminal_manager.py`
   - Also delete: `services/oracle/oracle_service/solvers/` entire folder (framework handles all solving)
   - Also delete: `services/oracle/oracle_service/logic/` entire folder (framework has its own logic/)

4. **Update imports** — Search all files that imported the deleted engines. Redirect them to `framework_bridge.py`.

5. **Update `__init__.py`** — `services/oracle/oracle_service/engines/__init__.py` must remove deleted module imports.

6. **Python path setup** — Ensure the framework is importable. Add to `services/oracle/pyproject.toml` or `services/oracle/Dockerfile`:
   ```
   PYTHONPATH=/app/numerology_ai_framework:$PYTHONPATH
   ```
   Or in code: `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'numerology_ai_framework'))`

### Files to Create
- `services/oracle/oracle_service/framework_bridge.py` — NEW (main bridge)
- `services/oracle/tests/test_framework_bridge.py` — NEW

### Files to Delete
- All files listed in step 3 above (12+ files + 2 folders)

### Files to Modify
- `services/oracle/oracle_service/engines/__init__.py` — Remove deleted imports
- `services/oracle/pyproject.toml` — Add framework to Python path
- `services/oracle/Dockerfile` — Add PYTHONPATH

### Tests
- Framework tests still pass after integration
- Bridge generates reading for a mock oracle_user
- Bridge handles missing optional fields gracefully
- Bridge handles invalid input with proper error messages
- Bridge logs timing data
- No import errors anywhere in the project

### Acceptance Criteria
- [ ] `python3 numerology_ai_framework/tests/test_all.py` — all pass
- [ ] `python3 -c "from services.oracle.oracle_service.framework_bridge import generate_single_reading; print('OK')"` — works
- [ ] Old engine files are deleted
- [ ] No broken imports in any Python file: `python3 -c "import services.oracle.oracle_service"` — no errors
- [ ] Bridge test passes: `cd services/oracle && python3 -m pytest tests/test_framework_bridge.py -v`

---

## SESSION 7 — Framework Integration: Reading Types

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** High
**Dependencies:** Session 6 (framework bridge)

### What to Build
Implement the 5 reading types through the framework bridge. Each reading type collects different input and passes different parameters to the framework.

### Detailed Instructions

The 5 reading types:

1. **Time Reading** — User enters a specific time (HH:MM:SS). Framework receives `current_hour`, `current_minute`, `current_second`. The time is the "sign."
2. **Name Reading** — User enters a name (or uses their profile name). Framework uses `full_name` as primary input. The name is the "sign."
3. **Question Reading** — User types a question. The question text is hashed/analyzed for numerological value, then passed as additional context to the AI interpretation. Framework generates reading using user's profile data + current time.
4. **Daily Reading** — Auto-generated for today's date. Framework uses user's profile data + today's date/time. No manual sign input needed.
5. **Multi-User Reading** — 2-5 users selected. Framework generates individual readings for each, then a compatibility/group analysis combines them.

For each type, implement in `framework_bridge.py`:
- `generate_time_reading(user, hour, minute, second, date)`
- `generate_name_reading(user, name_to_analyze, date)`
- `generate_question_reading(user, question_text, date)`
- `generate_daily_reading(user, date)`
- `generate_multi_user_reading(users, reading_type, sign_value, date)`

The multi-user reading generates individual readings then creates a compatibility analysis by comparing:
- Life path numbers
- FC60 stamps (shared animals/elements)
- Moon phase alignment
- Ganzhi compatibility
- Pattern overlap

### Files to Create/Modify
- `services/oracle/oracle_service/framework_bridge.py` — MODIFY (add 5 reading functions)
- `services/oracle/oracle_service/multi_user_analyzer.py` — NEW (compatibility logic)
- `services/oracle/tests/test_reading_types.py` — NEW
- `services/oracle/tests/test_multi_user_analyzer.py` — NEW

### Tests
- Each of the 5 reading types produces valid output
- Time reading uses the provided time
- Name reading uses the provided name
- Question reading includes question in AI context
- Daily reading uses today's date
- Multi-user reading generates N individual readings + 1 group analysis
- Invalid inputs return proper error messages

### Acceptance Criteria
- [ ] All 5 reading type functions return valid framework output
- [ ] Multi-user reading works with 2, 3, 4, and 5 users
- [ ] All tests pass: `cd services/oracle && python3 -m pytest tests/test_reading_types.py tests/test_multi_user_analyzer.py -v`

---

## SESSION 8 — Framework Integration: Numerology System Selection

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** Medium-High
**Dependencies:** Session 7 (reading types)

### What to Build
The framework supports 3 numerology systems: Pythagorean (default for English), Chaldean (alternative for English), and Abjad (for Persian/Arabic names). This session implements the logic to auto-select the right system based on user locale and name script, with manual override.

### Detailed Instructions

1. **Auto-detection logic:**
   - If user locale is FA (Persian) → default to Abjad
   - If user locale is EN → default to Pythagorean
   - If name contains Persian characters → use Abjad regardless of locale
   - Manual override always respected

2. **API parameter** — Add `numerology_system` parameter to reading endpoints: `POST /api/oracle/readings` accepts optional `numerology_system` field ('pythagorean', 'chaldean', 'abjad', 'auto').

3. **Framework integration** — Pass `numerology_system` parameter to `MasterOrchestrator.generate_reading()`.

4. **User settings** — Save preferred numerology system in `oracle_settings` table (from Session 1). Default to 'auto'.

5. **Frontend** — Add numerology system selector to Oracle form. Three radio buttons (or dropdown): Pythagorean, Chaldean, Abjad, Auto-detect. Show brief explanation of each.

6. **Character detection** — Write utility function that detects if a string contains Persian/Arabic characters (Unicode range 0x0600-0x06FF).

### Files to Create/Modify
- `services/oracle/oracle_service/framework_bridge.py` — MODIFY (add system selection logic)
- `api/app/routers/oracle.py` — MODIFY (add numerology_system param)
- `api/app/models/oracle.py` — MODIFY (add numerology_system field)
- `frontend/src/components/oracle/NumerologySystemSelector.tsx` — NEW
- `frontend/src/utils/scriptDetector.ts` — NEW (Persian character detection)
- `services/oracle/oracle_service/utils/script_detector.py` — NEW (backend version)
- `services/oracle/tests/test_numerology_selection.py` — NEW

### Tests
- Pythagorean selected for English names
- Abjad selected for Persian names
- Chaldean selected when manually chosen
- Auto-detect picks correct system
- Persian character detection works correctly
- API accepts and passes numerology_system parameter
- Settings are saved and loaded

### Acceptance Criteria
- [ ] Auto-detection selects Abjad for Persian, Pythagorean for English
- [ ] Manual override works for all 3 systems
- [ ] Frontend shows system selector
- [ ] API endpoint accepts numerology_system parameter
- [ ] All tests pass

---

## SESSION 9 — Framework Integration: Signal Processing & Patterns

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** High
**Dependencies:** Session 7 (reading types)

### What to Build
The framework's `signal_combiner.py` detects patterns (repeated numbers, animal clusters, element dominance). This session ensures the pattern data is properly extracted, stored, and made available for AI interpretation and frontend display.

### Detailed Instructions

1. **Pattern extraction** — The framework returns `reading['patterns']['detected']` as a list of pattern dicts. Each pattern has: `type`, `description`, `priority` (very_high/high/medium/low), `animals_involved`, `elements_involved`, `significance`.

2. **Store patterns** — Extend `reading_result` JSONB to include a `patterns_summary` key with extracted patterns. Also store `confidence` score.

3. **Signal priority for AI** — From framework's CLAUDE.md:
   ```
   1. Repeated animals (3+) → Very High
   2. Repeated animals (2) → High
   3. Day planet → Medium
   4. Moon phase → Medium
   5. DOM token animal+element → Medium
   6. Hour animal → Low-Medium
   7. Minute texture → Low
   8. Year cycle (GZ) → Background
   9. Personal overlays → Variable
   ```
   Create a `PatternFormatter` class that takes raw patterns and formats them for: (a) AI prompt context, (b) frontend display, (c) database storage.

4. **Confidence scoring** — Framework provides `reading['confidence']['score']` (0-100) and `level` (low/medium/high/very_high). Map these to UI indicators.

5. **Pattern visualization data** — Prepare pattern data in a format the frontend can display as visual elements (badges, highlight colors, importance indicators).

### Files to Create/Modify
- `services/oracle/oracle_service/pattern_formatter.py` — NEW
- `services/oracle/oracle_service/framework_bridge.py` — MODIFY (integrate pattern formatting)
- `services/oracle/tests/test_pattern_formatter.py` — NEW

### Tests
- Patterns extracted from framework output
- Patterns formatted for AI, frontend, and database
- Signal priority ordering is correct
- Confidence score mapping works
- Edge case: no patterns detected (valid — not every reading has patterns)

### Acceptance Criteria
- [ ] Pattern formatter processes all pattern types
- [ ] AI format includes priority-ordered signal descriptions
- [ ] Frontend format includes display-ready pattern data
- [ ] Confidence score stored and retrievable
- [ ] All tests pass

---

## SESSION 10 — Framework Integration: FC60 Stamp Display & Validation

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** Medium-High
**Dependencies:** Session 6 (framework bridge)

### What to Build
FC60 stamps are the framework's unique "universal address" for any moment in time. This session ensures stamps are correctly generated, validated, displayed, and stored.

### Detailed Instructions

1. **FC60 stamp format** — From framework: `reading['fc60_stamp']['fc60']` returns something like `"LU-OX-OXWA ☀TI-HOWU-RAWU"`. Also: `j60` (Julian Day in base-60), `chk` (checksum token), `y60` (year in base-60).

2. **Stamp validation** — Use framework's `ChecksumValidator` to verify stamps. Expose validation as API endpoint: `POST /api/oracle/validate-stamp` that accepts an FC60 string and returns valid/invalid.

3. **Stamp display component** — Frontend component that beautifully renders an FC60 stamp with:
   - Animal symbols with emoji/icons
   - Element colors (Fire=red, Water=blue, Wood=green, Metal=gold, Earth=brown)
   - Half-day indicator (☀ or 🌙)
   - Tooltip explanations for each segment
   - Copy-to-clipboard button

4. **Stamp comparison** — For multi-user readings, show stamps side by side with shared elements highlighted.

5. **Encoding rules from framework's CLAUDE.md:**
   - Month: `ANIMALS[month - 1]` — January = RA (index 0)
   - Hour in time stamp: 2-char `ANIMALS[hour % 12]`, NOT 4-char token60
   - CHK uses LOCAL date/time values, not UTC-adjusted
   - HALF marker: ☀ (U+2600) if hour < 12, 🌙 (U+1F319) if hour >= 12

### Files to Create/Modify
- `api/app/routers/oracle.py` — MODIFY (add validate-stamp endpoint)
- `frontend/src/components/oracle/FC60StampDisplay.tsx` — NEW
- `frontend/src/components/oracle/StampComparison.tsx` — NEW
- `services/oracle/oracle_service/framework_bridge.py` — MODIFY (add stamp validation)
- `services/oracle/tests/test_stamp_validation.py` — NEW
- `frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx` — NEW

### Tests
- Stamp generation produces valid format
- Stamp validation accepts valid stamps, rejects invalid
- Display component renders all stamp segments
- Element colors mapped correctly
- Copy-to-clipboard works
- Multi-stamp comparison highlights shared elements

### Acceptance Criteria
- [ ] FC60 stamp displays correctly in frontend
- [ ] Validation endpoint works for valid and invalid stamps
- [ ] All encoding rules respected (month indexing, hour format, CHK, HALF)
- [ ] All tests pass

---

## SESSION 11 — Framework Integration: Moon, Ganzhi & Cosmic Cycles

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** Medium
**Dependencies:** Session 6 (framework bridge)

### What to Build
Ensure moon phase, Chinese zodiac (Ganzhi), and other cosmic cycle data from the framework is properly extracted, formatted, and ready for frontend display and AI interpretation.

### Detailed Instructions

1. **Moon data** — `reading['moon']` contains: `phase_name`, `emoji`, `age` (days), `illumination` (%), `energy`, `best_for`, `avoid`. Create display components and format for AI.

2. **Ganzhi data** — `reading['ganzhi']` contains year, day, and hour cycles with: `gz_token`, `traditional_name`, `element`, `polarity`. Display Chinese zodiac year animal, day element, hour energy.

3. **Current moment** — `reading['current']` contains: `planet` (ruling planet of the day), `domain`, `weekday`. Display prominently.

4. **Cosmic cycle display components:**
   - `MoonPhaseDisplay.tsx` — Moon emoji + phase name + illumination bar + energy description
   - `GanzhiDisplay.tsx` — Chinese zodiac year animal + element + traditional name
   - `CosmicCyclePanel.tsx` — Combines moon, ganzhi, and current planet into one section

5. **Persian translations** — All cosmic cycle terms need Persian equivalents in i18n files.

### Files to Create/Modify
- `frontend/src/components/oracle/MoonPhaseDisplay.tsx` — NEW
- `frontend/src/components/oracle/GanzhiDisplay.tsx` — NEW
- `frontend/src/components/oracle/CosmicCyclePanel.tsx` — NEW
- `frontend/src/i18n/en.json` — MODIFY (add cosmic cycle terms)
- `frontend/src/i18n/fa.json` — MODIFY (add Persian cosmic cycle terms)
- `services/oracle/oracle_service/cosmic_formatter.py` — NEW (format cosmic data for API response)

### Tests
- Moon phase data extracted and formatted correctly
- Ganzhi data extracted and formatted correctly
- Display components render all fields
- Persian translations present for all terms
- Edge cases: new moon, full moon, year boundaries

### Acceptance Criteria
- [ ] Moon phase displays with emoji, name, and illumination
- [ ] Chinese zodiac year + element displays correctly
- [ ] Current planet and domain show
- [ ] All terms translated to Persian
- [ ] All tests pass

---

## SESSION 12 — Framework Integration: Heartbeat & Location Engines

**Block:** Calculation Engines (Sessions 6-12)
**Complexity:** Medium
**Dependencies:** Session 6 (framework bridge), Session 5 (location service)

### What to Build
Integrate the framework's heartbeat engine (BPM analysis) and location engine (GPS → element mapping) with the NPS user interface and data flow.

### Detailed Instructions

1. **Heartbeat integration:**
   - `reading['heartbeat']` contains: `bpm`, `element`, `total_lifetime_beats`, `beats_per_year`, `rhythm_description`
   - BPM input on user profile form (optional field)
   - Real-time BPM input option (tap-to-count feature in frontend?)
   - Display: Show BPM element, lifetime beats counter, rhythm description

2. **Location integration:**
   - `reading['location']` contains: `element`, `timezone_estimate`, `lat_hemisphere`, `lng_hemisphere`, `zone_description`
   - Already have location selector from Session 5
   - Ensure coordinates are passed through framework_bridge to framework
   - Display: Show location element mapping, hemisphere info

3. **Confidence boost display:**
   - Show user which optional fields boost confidence and by how much:
     - Mother's name: +10%
     - Location coordinates: +5%
     - Heart rate: +5%
     - Exact time: +5%
   - Display as a "completeness meter" on the reading form

4. **Input priority** — From framework: `heartbeat > location > time > name > gender > DOB > mother`. Display this priority in the UI help tooltip.

### Files to Create/Modify
- `frontend/src/components/oracle/HeartbeatInput.tsx` — NEW (BPM input with tap-to-count)
- `frontend/src/components/oracle/HeartbeatDisplay.tsx` — NEW
- `frontend/src/components/oracle/LocationDisplay.tsx` — NEW
- `frontend/src/components/oracle/ConfidenceMeter.tsx` — NEW
- `services/oracle/oracle_service/framework_bridge.py` — MODIFY (pass heartbeat/location)

### Tests
- Heartbeat data displayed correctly
- Location element mapping displayed
- Confidence meter updates as fields are filled
- BPM input validates (30-200 range)
- Missing optional fields handled gracefully

### Acceptance Criteria
- [ ] Heartbeat display shows BPM element and lifetime beats
- [ ] Location display shows element mapping
- [ ] Confidence meter shows percentage and level
- [ ] Optional fields are truly optional (reading works without them)
- [ ] All tests pass

---

## SESSION 13 — AI Interpretation Engine: Anthropic Integration

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** Very High
**Dependencies:** Sessions 6-12 (framework integration complete)

### What to Build
Connect Anthropic Claude API to the framework output. The AI receives framework's raw reading data + the framework's interpretation docs and generates the "Wisdom AI" interpretation — an honest, caring, insightful reading.

### Detailed Instructions

1. **AI client** — `services/oracle/oracle_service/engines/ai_client.py` exists. Refactor:
   - Use `anthropic` Python SDK (pip install anthropic)
   - Never use CLI subprocess calls
   - Model: `claude-sonnet-4-20250514` (cost-effective for readings)
   - Fallback: if API key missing, return framework's `reading['synthesis']` as fallback text
   - Max tokens: 2000 for single reading, 3000 for multi-user
   - Temperature: 0.7 (warm but not wild)

2. **System prompt** — Build from framework's `logic/00_MASTER_SYSTEM_PROMPT.md` + `logic/04_READING_COMPOSITION_GUIDE.md`. The prompt tells the AI:
   - You are "Wisdom" — an honest, caring friend who gives numerological insights
   - Tone: warm, direct, no fortune-telling, use "the numbers suggest" language
   - Structure: Opening → Core Identity → Right Now → Patterns → Message → Advice → Caution → Footer
   - Never make absolute predictions
   - Always state confidence level

3. **User prompt** — Construct from framework output:
   - Include all numerology numbers with meanings
   - Include FC60 stamp with decoded segments
   - Include moon phase + energy
   - Include Ganzhi cycle
   - Include detected patterns (priority-ordered)
   - Include heartbeat/location data if available
   - Include the reading type (time/name/question/daily/multi) and sign value
   - For question readings: include the question text

4. **Response parsing** — AI returns prose text. Parse into sections matching `reading['translation']` structure: header, universal_address, core_identity, right_now, patterns, message, advice, caution, footer.

5. **Bilingual support** — Generate readings in the user's locale (EN or FA). When locale is FA, the system prompt instructs the AI to respond in Persian.

6. **Caching** — Cache AI interpretations for daily readings (same user + same date = same reading). Use database `oracle_daily_readings` table.

7. **Error handling** — API key missing → use framework synthesis. API error → retry once, then use framework synthesis. Rate limit → queue and retry.

### Files to Create/Modify
- `services/oracle/oracle_service/engines/ai_client.py` — REWRITE
- `services/oracle/oracle_service/engines/ai_interpreter.py` — REWRITE
- `services/oracle/oracle_service/engines/prompt_templates.py` — REWRITE (use framework logic docs)
- `services/oracle/oracle_service/ai_prompt_builder.py` — NEW
- `services/oracle/tests/test_ai_integration.py` — REWRITE

### Tests
- AI client connects to Anthropic API (mock for tests)
- System prompt includes framework interpretation rules
- User prompt includes all reading data
- Response parsed into correct sections
- Persian locale generates Persian response
- Fallback works when API key missing
- Caching works for daily readings
- Error handling works for API failures

### Acceptance Criteria
- [ ] AI generates reading from framework output (mock test)
- [ ] Fallback to framework synthesis works
- [ ] Both EN and FA prompts generate correct language
- [ ] Response parsed into structured sections
- [ ] All tests pass: `cd services/oracle && python3 -m pytest tests/test_ai_integration.py -v`

---

## SESSION 14 — Reading Flow: Time Reading

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** High
**Dependencies:** Session 13 (AI engine), Session 7 (reading types)

### What to Build
Complete end-to-end flow for Time Reading: frontend form → API → framework → AI → database → display.

### Detailed Instructions

1. **Frontend** — Time input component: hour/minute/second pickers (dropdowns or scrollers). User selects a time, optionally selects a date (defaults to today). Submit button.

2. **API endpoint** — `POST /api/oracle/readings` with body: `{ user_id, reading_type: "time", sign_value: "14:30:00", date: "2026-02-10", locale: "en", numerology_system: "auto" }`

3. **Backend flow:**
   - Validate inputs
   - Load oracle_user from database
   - Call `framework_bridge.generate_time_reading(user, hour, minute, second, date)`
   - Call AI interpreter with framework output
   - Store reading + AI interpretation in database
   - Return full reading response

4. **Response format:**
   ```json
   {
     "id": 1,
     "reading_type": "time",
     "sign_value": "14:30:00",
     "framework_result": { ... },
     "ai_interpretation": { "header": "...", "core_identity": "...", ... },
     "confidence": { "score": 75, "level": "high" },
     "patterns": [ ... ],
     "fc60_stamp": "LU-OX-OXWA ☀TI-HOWU-RAWU",
     "created_at": "2026-02-10T14:30:00Z"
   }
   ```

5. **WebSocket** — Send real-time progress updates: "Calculating..." → "Generating interpretation..." → "Done"

### Files to Create/Modify
- `frontend/src/components/oracle/TimeReadingForm.tsx` — NEW
- `api/app/routers/oracle.py` — MODIFY (time reading endpoint)
- `api/app/services/oracle_reading.py` — MODIFY (time reading flow)
- `services/oracle/oracle_service/reading_orchestrator.py` — NEW (coordinates the full flow)

### Tests
- Time input validates (0-23 hours, 0-59 minutes/seconds)
- API creates reading and returns full response
- Framework generates reading with correct time
- AI interpretation included in response
- Reading stored in database
- WebSocket sends progress updates

### Acceptance Criteria
- [ ] Time reading form renders and submits
- [ ] API returns full reading response
- [ ] Reading stored in database with all data
- [ ] Works for both EN and FA locales
- [ ] All tests pass

---

## SESSION 15 — Reading Flow: Name & Question Readings

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** High
**Dependencies:** Session 14 (time reading flow — sets the pattern)

### What to Build
Complete flows for Name Reading and Question Reading, following the same pattern as Time Reading.

### Detailed Instructions

1. **Name Reading:**
   - Frontend: Text input for name (with Persian keyboard support). Can also "use profile name" button.
   - API: `{ reading_type: "name", sign_value: "Alice Johnson" }`
   - Framework: `generate_name_reading()` uses the name as primary numerological input
   - AI: Interprets name numerology (Life Path from name, not birthdate)

2. **Question Reading:**
   - Frontend: Large text area for question. Supports both EN and FA input. Character limit: 500.
   - API: `{ reading_type: "question", sign_value: "Should I change careers?", question_text: "Should I change careers?" }`
   - Framework: Generates reading using profile data + current time. Question text passed to AI as additional context.
   - AI: Addresses the specific question in the interpretation. Uses numerological data to provide insight on the question topic.

3. **Question hashing** — For the question reading, extract numerological value from the question text:
   - Sum letter values (Pythagorean/Chaldean/Abjad based on detected script)
   - Reduce to single digit or master number
   - Include this "question number" in AI context

### Files to Create/Modify
- `frontend/src/components/oracle/NameReadingForm.tsx` — NEW
- `frontend/src/components/oracle/QuestionReadingForm.tsx` — NEW
- `api/app/routers/oracle.py` — MODIFY (name + question endpoints)
- `services/oracle/oracle_service/reading_orchestrator.py` — MODIFY (add name + question flows)
- `services/oracle/oracle_service/question_analyzer.py` — NEW (question text → numerological value)

### Tests
- Name reading uses provided name for numerology
- Question reading includes question in AI context
- Persian question detected and uses Abjad
- Question number calculated correctly
- Both reading types stored in database
- Frontend forms validate and submit

### Acceptance Criteria
- [ ] Name reading form works with typed name and "use profile" button
- [ ] Question reading form accepts up to 500 characters
- [ ] AI interpretation addresses the question topic
- [ ] Both reading types stored and retrievable
- [ ] All tests pass

---

## SESSION 16 — Reading Flow: Daily & Multi-User Readings

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** Very High
**Dependencies:** Sessions 14-15 (single reading flows)

### What to Build
Daily auto-reading and multi-user compatibility reading — the two most complex reading types.

### Detailed Instructions

1. **Daily Reading:**
   - Auto-generated: one per user per day
   - Scheduled via background task (Python `asyncio` or cron job in Docker)
   - Uses user's profile data + today's date + current time (noon by default)
   - Stored in `oracle_daily_readings` table
   - Cached: same user + same date = same reading (no re-generation)
   - Frontend: "Today's Reading" card on dashboard
   - API: `GET /api/oracle/daily?user_id=X&date=2026-02-10`

2. **Multi-User Reading:**
   - 2-5 users selected from profile list
   - Each user gets individual reading via framework
   - Then compatibility analysis compares all readings
   - Compatibility dimensions:
     - Life Path compatibility (number harmony)
     - FC60 shared animals/elements
     - Moon phase alignment
     - Ganzhi year/element compatibility
     - Pattern overlap analysis
   - AI receives all individual readings + compatibility data → generates group interpretation
   - Frontend: Show individual readings side-by-side + group analysis section
   - API: `POST /api/oracle/readings` with `{ reading_type: "multi", user_ids: [1, 2, 3], ... }`

3. **Multi-user display:**
   - Individual readings in tabs or accordion
   - Compatibility score (0-100) with visual meter
   - Shared elements highlighted
   - Group advice section

### Files to Create/Modify
- `frontend/src/components/oracle/DailyReadingCard.tsx` — NEW
- `frontend/src/components/oracle/MultiUserReadingDisplay.tsx` — NEW
- `frontend/src/components/oracle/CompatibilityMeter.tsx` — NEW
- `api/app/routers/oracle.py` — MODIFY (daily + multi-user endpoints)
- `services/oracle/oracle_service/reading_orchestrator.py` — MODIFY (daily + multi flows)
- `services/oracle/oracle_service/multi_user_analyzer.py` — MODIFY (full compatibility)
- `services/oracle/oracle_service/daily_scheduler.py` — NEW (background task)
- `api/tests/test_multi_user_reading.py` — MODIFY

### Tests
- Daily reading generates once per user per day
- Cached daily reading returns same result
- Multi-user reading works with 2, 3, 4, 5 users
- Compatibility score calculated correctly
- AI generates group interpretation
- Background scheduler runs on schedule

### Acceptance Criteria
- [ ] Daily reading auto-generates and caches
- [ ] Multi-user reading produces individual + group results
- [ ] Compatibility score displayed
- [ ] All tests pass

---

## SESSION 17 — Reading History & Persistence

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** Medium-High
**Dependencies:** Sessions 14-16 (all reading flows)

### What to Build
Reading history storage, retrieval, search, and display.

### Detailed Instructions

1. **API endpoints:**
   - `GET /api/oracle/readings` — List readings with pagination, filters (by type, date range, user, locale)
   - `GET /api/oracle/readings/{id}` — Full reading details with AI interpretation
   - `DELETE /api/oracle/readings/{id}` — Soft delete (mark as deleted, don't remove)
   - `GET /api/oracle/readings/stats` — Reading statistics (count by type, average confidence, most active days)

2. **Search** — Full-text search on question text, AI interpretation text. PostgreSQL `tsvector` with both English and Persian dictionaries.

3. **Frontend:**
   - `ReadingHistory.tsx` already exists. Rewrite to:
     - Card-based list with reading type icon, date, confidence badge, first line of interpretation
     - Filters: by type, date range, user
     - Search bar
     - Pagination (20 per page)
     - Click to expand full reading
   - Reading detail view: full interpretation with all sections, patterns, FC60 stamp, cosmic cycles

4. **Favorites** — Users can mark readings as favorites. Add `is_favorite` boolean to `oracle_readings` table.

### Files to Create/Modify
- `frontend/src/components/oracle/ReadingHistory.tsx` — REWRITE
- `frontend/src/components/oracle/ReadingCard.tsx` — NEW
- `frontend/src/components/oracle/ReadingDetail.tsx` — NEW
- `api/app/routers/oracle.py` — MODIFY (history endpoints)
- `api/app/services/oracle_reading.py` — MODIFY (search, stats)
- `database/migrations/014_reading_search.sql` — NEW (full-text index)

### Tests
- Reading list returns paginated results
- Filters work (type, date range, user)
- Full-text search finds readings by question or interpretation text
- Soft delete hides reading from list
- Favorites toggle works
- Statistics endpoint returns correct counts

### Acceptance Criteria
- [ ] Reading history shows all readings with pagination
- [ ] Filters narrow results correctly
- [ ] Search finds readings by text content
- [ ] Reading detail shows all sections
- [ ] Favorites work
- [ ] All tests pass

---

## SESSION 18 — AI Learning & Feedback Loop

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** High
**Dependencies:** Session 17 (reading history)

### What to Build
System for AI to learn from feedback and improve over time. Users rate readings, and the system tracks what makes good interpretations.

### Detailed Instructions

1. **User feedback** — After each reading, user can:
   - Rate 1-5 stars
   - Mark specific sections as "helpful" or "not helpful"
   - Optional text feedback
   - Store in `oracle_reading_feedback` table (new)

2. **Learning data** — Track which patterns/signals led to highly-rated readings. Store in `oracle_learning_data` table (update from existing).

3. **Prompt optimization** — Use feedback to adjust AI prompts:
   - If users consistently rate "advice" section highest → emphasize advice in prompt
   - If users mark "caution" as unhelpful → soften caution language
   - Simple weighted scoring, no ML needed

4. **API endpoints:**
   - `POST /api/oracle/readings/{id}/feedback` — Submit rating + feedback
   - `GET /api/oracle/learning/stats` — Admin view of feedback aggregates

5. **Frontend:**
   - Star rating component after reading display
   - Section-level thumbs up/down
   - Optional text feedback input
   - Admin: learning dashboard showing feedback trends

### Files to Create/Modify
- `database/migrations/015_feedback_learning.sql` — NEW
- `api/app/routers/learning.py` — MODIFY
- `api/app/models/learning.py` — MODIFY
- `services/oracle/oracle_service/engines/learner.py` — MODIFY
- `frontend/src/components/oracle/ReadingFeedback.tsx` — NEW
- `frontend/src/components/oracle/StarRating.tsx` — NEW

### Tests
- Feedback stored correctly
- Rating aggregation works
- Learning data updated from feedback
- Prompt adjustment based on feedback trends
- Admin stats endpoint returns correct data

### Acceptance Criteria
- [ ] Users can rate readings 1-5 stars
- [ ] Section-level feedback works
- [ ] Learning stats show feedback trends
- [ ] All tests pass

---

## SESSION 19 — Frontend Layout & Navigation

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** High
**Dependencies:** Sessions 1-18 (all backend work)

### What to Build
Main app layout, navigation, routing, and theme system. Black & green futuristic aesthetic with dark/light mode.

### Detailed Instructions

1. **Design system:**
   - Primary: Black (#0A0A0A) + Emerald Green (#10B981)
   - Dark mode: Black bg, green accents, white text
   - Light mode: White bg, dark green accents, dark text
   - Font: Inter (body) + JetBrains Mono (code/stamps)
   - Spacing: 4px grid (Tailwind defaults)
   - Border radius: rounded-lg (8px) for cards, rounded-full for badges
   - Shadows: subtle, green-tinted in dark mode

2. **Layout component** — `Layout.tsx` exists. Rewrite:
   - Sidebar navigation (collapsible on mobile)
   - Top bar with user info, locale toggle, theme toggle
   - Main content area
   - Footer with version info

3. **Navigation items:**
   - Dashboard (home/overview)
   - Oracle (reading interface — main feature)
   - Reading History
   - Settings
   - Admin Panel (admin only)
   - Scanner (stub — grayed out with "Coming Soon")

4. **Routing** — React Router with lazy loading for each page.

5. **Theme toggle** — Dark/light mode with system preference detection. Persist in localStorage.

6. **Locale toggle** — EN/FA switch. When FA selected, entire layout flips RTL. Persist in localStorage.

### Files to Create/Modify
- `frontend/src/components/Layout.tsx` — REWRITE
- `frontend/src/components/Navigation.tsx` — NEW
- `frontend/src/components/ThemeToggle.tsx` — NEW
- `frontend/src/components/LanguageToggle.tsx` — REWRITE
- `frontend/src/App.tsx` — MODIFY (add routing)
- `frontend/tailwind.config.ts` — MODIFY (custom theme colors)
- `frontend/src/styles/theme.css` — NEW (CSS variables for theme)

### Tests
- Layout renders with all navigation items
- Theme toggle switches dark/light
- Locale toggle switches EN/FA with RTL flip
- Routing works for all pages
- Sidebar collapses on mobile
- Admin items hidden for non-admin users

### Acceptance Criteria
- [ ] App has black & green aesthetic
- [ ] Dark/light toggle works
- [ ] EN/FA toggle flips layout direction
- [ ] All routes accessible
- [ ] Mobile-responsive sidebar
- [ ] All tests pass

---

## SESSION 20 — Oracle Main Page

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** High
**Dependencies:** Session 19 (layout)

### What to Build
The main Oracle page — the primary interface where users perform readings.

### Detailed Instructions

1. **Page layout:**
   - Left panel: User selector + reading type selector
   - Center: Reading form (changes based on type)
   - Bottom: Submit button + confidence meter

2. **Reading type selector** — 5 tabs or segmented control: Time | Name | Question | Daily | Multi-user

3. **Dynamic form** — Content changes based on selected reading type:
   - Time: Time picker
   - Name: Text input + "use profile" button
   - Question: Text area
   - Daily: No input needed (auto)
   - Multi-user: User selector (checkboxes for 2-5 users) + sub-type selector (time/name/question)

4. **User selector** — Dropdown or card selector showing the user's Oracle profiles. "Quick add" button to create new profile inline.

5. **Submit flow:**
   - Show loading animation (pulsing green orb?)
   - WebSocket progress: "Calculating..." → "Consulting Wisdom AI..." → "Preparing reading..."
   - Scroll to results on completion

6. **Results display** — After reading completes, show results on the same page below the form (or navigate to detail page).

### Files to Create/Modify
- `frontend/src/pages/Oracle.tsx` — REWRITE
- `frontend/src/components/oracle/ReadingTypeSelector.tsx` — NEW
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — REWRITE
- `frontend/src/components/oracle/LoadingAnimation.tsx` — NEW
- `frontend/src/hooks/useOracleReadings.ts` — MODIFY

### Tests
- Page renders with all 5 reading type tabs
- Form changes based on selected type
- User selector works
- Submit triggers API call
- Loading animation shows during processing
- Results display after completion

### Acceptance Criteria
- [ ] Oracle page renders with all components
- [ ] All 5 reading types selectable
- [ ] Form submits and shows loading
- [ ] Results display correctly
- [ ] All tests pass

---

## SESSION 21 — Reading Results Display

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** High
**Dependencies:** Session 20 (Oracle page)

### What to Build
Beautiful reading results display with all sections from the AI interpretation.

### Detailed Instructions

1. **Results layout** — Full reading display with sections:
   - Header: Person name, date, confidence badge
   - Universal Address: FC60 stamp (use FC60StampDisplay from Session 10)
   - Core Identity: Life Path, Expression, Soul Urge numbers with meanings
   - Right Now: Current planet, moon phase, hour energy
   - Patterns: Detected patterns with priority badges
   - The Message: 3-5 sentence synthesis (highlighted, larger text)
   - Today's Advice: 3 actionable items
   - Caution: Shadow warnings (subtle, red-amber tones)
   - Footer: Confidence score, disclaimer

2. **Section cards** — Each section in its own card with subtle animation on scroll reveal.

3. **Number display** — Large, styled numerology numbers with meaning text below. Example: "Life Path 7 — The Seeker"

4. **Persian rendering** — When locale is FA, all text renders RTL with Persian numerals option.

5. **Share button** — Generate shareable summary (text or image).

6. **Print-friendly** — CSS @media print styling for clean printed readings.

### Files to Create/Modify
- `frontend/src/components/oracle/ReadingResults.tsx` — REWRITE
- `frontend/src/components/oracle/ReadingSection.tsx` — NEW
- `frontend/src/components/oracle/NumerologyNumberDisplay.tsx` — NEW
- `frontend/src/components/oracle/PatternBadge.tsx` — NEW
- `frontend/src/components/oracle/ReadingHeader.tsx` — NEW
- `frontend/src/components/oracle/ReadingFooter.tsx` — NEW

### Tests
- All 9 sections render correctly
- FC60 stamp displays correctly
- Numerology numbers show with meanings
- Patterns displayed with correct priority styling
- Persian rendering works
- Print CSS produces clean output

### Acceptance Criteria
- [ ] Full reading displays all 9 sections
- [ ] Beautiful, futuristic green/black aesthetic
- [ ] Persian mode renders correctly
- [ ] Print produces clean output
- [ ] All tests pass

---

## SESSION 22 — Dashboard Page

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** Medium-High
**Dependencies:** Sessions 17 (history), 20-21 (Oracle page)

### What to Build
Dashboard homepage showing overview, recent readings, daily reading, and quick actions.

### Detailed Instructions

1. **Layout:**
   - Welcome banner with user name and today's date
   - Daily reading card (today's auto-reading or "Generate" button)
   - Recent readings (last 5, card grid)
   - Statistics cards (total readings, average confidence, most used type, streak days)
   - Quick action buttons (New Time Reading, New Question Reading)

2. **Stats visualization** — Simple counters/sparklines. No heavy charting library needed.

3. **Moon phase widget** — Current moon phase display in sidebar or banner.

4. **Multi-locale** — All dashboard text translated EN/FA.

### Files to Create/Modify
- `frontend/src/pages/Dashboard.tsx` — REWRITE
- `frontend/src/components/dashboard/WelcomeBanner.tsx` — NEW
- `frontend/src/components/dashboard/StatsCards.tsx` — NEW
- `frontend/src/components/dashboard/RecentReadings.tsx` — NEW
- `frontend/src/components/dashboard/QuickActions.tsx` — NEW

### Acceptance Criteria
- [ ] Dashboard shows welcome banner with user name
- [ ] Daily reading card shows or offers to generate
- [ ] Recent readings display correctly
- [ ] Statistics are accurate
- [ ] All tests pass

---

## SESSION 23 — Settings Page

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** Medium
**Dependencies:** Session 19 (layout)

### What to Build
User settings page for preferences, profile management, and account settings.

### Detailed Instructions

1. **Sections:**
   - Profile: Edit name, email, password
   - Preferences: Default locale, theme, numerology system, timezone
   - Oracle settings: Default reading type, auto-daily toggle
   - API keys: View/regenerate personal API key (for Telegram bot linking)
   - About: App version, framework version, credits

2. **Settings persistence** — Save to `oracle_settings` table via API.

3. **API key display** — Show masked key with "reveal" button. Copy button. Regenerate with confirmation.

### Files to Create/Modify
- `frontend/src/pages/Settings.tsx` — REWRITE
- `frontend/src/components/settings/ProfileSection.tsx` — NEW
- `frontend/src/components/settings/PreferencesSection.tsx` — NEW
- `frontend/src/components/settings/ApiKeySection.tsx` — NEW
- `api/app/routers/settings.py` — NEW

### Acceptance Criteria
- [ ] All settings sections render
- [ ] Settings save to database
- [ ] API key management works
- [ ] All tests pass

---

## SESSION 24 — Translation Service & i18n Completion

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** High
**Dependencies:** Sessions 19-23 (all frontend pages exist)

### What to Build
Complete bilingual support: every string in the app translated to both English and Persian.

### Detailed Instructions

1. **Audit all strings** — Scan every `.tsx` file for hardcoded strings. Replace with `t('key')` calls.

2. **Translation files:**
   - `frontend/src/i18n/en.json` — Complete English translations
   - `frontend/src/i18n/fa.json` — Complete Persian translations
   - Organize by page/component: `dashboard.*`, `oracle.*`, `settings.*`, `common.*`

3. **Backend translations** — `services/oracle/oracle_service/engines/translation_service.py` handles backend string translations for AI prompts, error messages, etc.

4. **Number formatting** — Persian locale shows Persian numerals (۰۱۲۳۴۵۶۷۸۹) vs Western (0123456789). Use `persianFormatter.ts`.

5. **Date formatting** — Persian locale shows Jalali calendar dates. Use existing `jalaali-js` integration.

6. **Validation messages** — All form validation errors in both languages.

### Files to Create/Modify
- `frontend/src/i18n/en.json` — COMPLETE
- `frontend/src/i18n/fa.json` — COMPLETE
- `frontend/src/i18n/config.ts` — VERIFY
- `frontend/src/utils/persianFormatter.ts` — VERIFY/FIX
- Every `.tsx` component — MODIFY (replace hardcoded strings)
- `services/oracle/oracle_service/engines/translation_service.py` — MODIFY

### Acceptance Criteria
- [ ] Zero hardcoded strings in frontend
- [ ] Every key in en.json has corresponding fa.json entry
- [ ] Persian numerals display in FA locale
- [ ] Jalali dates display in FA locale
- [ ] All tests pass

---

## SESSION 25 — WebSocket & Real-Time Updates

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** Medium-High
**Dependencies:** Session 20 (Oracle page)

### What to Build
WebSocket connection for real-time reading progress and live updates.

### Detailed Instructions

1. **WebSocket server** — FastAPI WebSocket endpoint at `/ws/oracle`.
2. **Progress events:** Reading started → Calculating → AI generating → Complete/Error
3. **Live daily reading** — When daily reading generates, push to connected clients.
4. **Connection management** — Auto-reconnect, heartbeat ping/pong, auth via JWT in query param.
5. **Frontend hook** — `useWebSocket.ts` already exists. Verify/fix.

### Files to Create/Modify
- `api/app/services/websocket_manager.py` — MODIFY
- `frontend/src/hooks/useWebSocket.ts` — MODIFY
- `frontend/src/services/websocket.ts` — MODIFY

### Acceptance Criteria
- [ ] WebSocket connects with JWT auth
- [ ] Progress events received during reading generation
- [ ] Auto-reconnect on disconnection
- [ ] All tests pass

---

## SESSION 26 — RTL Layout System

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** Very High
**Dependencies:** Session 24 (i18n complete)

### What to Build
Complete RTL (Right-to-Left) layout flip when Persian locale is active.

### Detailed Instructions

1. **HTML dir attribute** — Set `<html dir="rtl" lang="fa">` when FA locale active.
2. **Tailwind RTL** — Use `rtl:` prefix variants for RTL-specific styles. Add `@tailwindcss/rtl` plugin if needed.
3. **Component-level RTL:**
   - Sidebar flips to right side
   - Text alignment flips
   - Icons that indicate direction flip (arrows, chevrons)
   - Margins/paddings that use left/right flip to start/end
   - Form labels position flips
4. **Mixed-direction content** — When Persian page has English words (like FC60 stamp codes), those stay LTR within RTL context. Use `<bdi>` or `dir="ltr"` on those elements.
5. **Testing** — Visual regression tests comparing EN and FA layouts.

### Files to Create/Modify
- `frontend/tailwind.config.ts` — MODIFY (RTL plugin)
- `frontend/src/styles/rtl.css` — NEW
- Multiple component files — MODIFY (add RTL variants)
- `frontend/src/hooks/useDirection.ts` — NEW (provides dir based on locale)

### Acceptance Criteria
- [ ] Full layout flips correctly when FA locale active
- [ ] Sidebar moves to right
- [ ] Text alignment correct in both modes
- [ ] Mixed content (EN within FA) displays correctly
- [ ] All tests pass

---

## SESSION 27 — Responsive Design

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** High
**Dependencies:** Session 26 (RTL)

### What to Build
Full responsive design for mobile, tablet, and desktop.

### Detailed Instructions
1. **Breakpoints:** Mobile (<640px), Tablet (640-1024px), Desktop (>1024px)
2. **Mobile:** Hamburger menu, stacked cards, full-width forms, touch-friendly buttons (min 44px tap target)
3. **Tablet:** Two-column layouts, collapsible sidebar
4. **Desktop:** Three-column where appropriate, expanded sidebar
5. **Reading results:** Responsive sections that stack on mobile, grid on desktop
6. **Persian keyboard:** Full-width on mobile, popup on desktop

### Files to Create/Modify
- Multiple component files — MODIFY (responsive classes)
- `frontend/src/components/oracle/MobileKeyboard.tsx` — NEW (full-width mobile keyboard)

### Acceptance Criteria
- [ ] All pages usable on 375px width (iPhone SE)
- [ ] Tablet layout looks good at 768px
- [ ] Desktop layout uses full width at 1440px
- [ ] Touch targets are 44px+ on mobile
- [ ] All tests pass

---

## SESSION 28 — Accessibility (a11y)

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** Medium-High
**Dependencies:** Sessions 26-27 (RTL + responsive)

### What to Build
WCAG 2.1 AA compliance for the entire application.

### Detailed Instructions
1. **Keyboard navigation** — All interactive elements focusable, tab order logical, Enter/Space activates
2. **Screen reader** — ARIA labels on all controls, live regions for dynamic content, reading results announced
3. **Color contrast** — Minimum 4.5:1 for text, 3:1 for large text. Verify with axe-core.
4. **Focus indicators** — Visible focus outlines on all interactive elements
5. **Form accessibility** — Labels linked to inputs, error messages announced, required fields marked
6. **Persian a11y** — Screen reader support for Persian text, correct lang attributes

### Files to Create/Modify
- Multiple component files — MODIFY (add ARIA attributes)
- `frontend/src/components/oracle/__tests__/Accessibility.test.tsx` — REWRITE

### Acceptance Criteria
- [ ] Keyboard-only navigation works for all flows
- [ ] axe-core reports zero critical violations
- [ ] Color contrast meets 4.5:1 minimum
- [ ] All form inputs have associated labels
- [ ] All tests pass

---

## SESSION 29 — Error States & Loading UX

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** Medium
**Dependencies:** Session 20 (Oracle page)

### What to Build
Beautiful error states, loading skeletons, empty states, and offline handling.

### Detailed Instructions
1. **Loading skeletons** — Shimmer placeholders for every data-dependent component
2. **Error boundaries** — React Error Boundary wrapping each page
3. **API error display** — Toast notifications for transient errors, inline messages for form errors
4. **Empty states** — Friendly illustrations/messages for: no readings yet, no profiles, search returns empty
5. **Offline detection** — Show banner when offline, queue actions for retry
6. **Retry logic** — Auto-retry failed API calls (3 attempts with exponential backoff)

### Files to Create/Modify
- `frontend/src/components/common/LoadingSkeleton.tsx` — NEW
- `frontend/src/components/common/ErrorBoundary.tsx` — NEW
- `frontend/src/components/common/EmptyState.tsx` — NEW
- `frontend/src/components/common/Toast.tsx` — NEW
- `frontend/src/hooks/useRetry.ts` — NEW

### Acceptance Criteria
- [ ] Loading skeletons show during data fetch
- [ ] Error boundaries catch component crashes
- [ ] Toast notifications for API errors
- [ ] Empty states display friendly messages
- [ ] All tests pass

---

## SESSION 30 — Animations & Micro-interactions

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** Medium
**Dependencies:** Sessions 19-29 (all UI complete)

### What to Build
Subtle animations that make the app feel premium and alive.

### Detailed Instructions
1. **Page transitions** — Fade/slide between pages
2. **Card animations** — Reading cards slide in on scroll
3. **Loading orb** — Pulsing green orb during reading generation
4. **Number reveal** — Numerology numbers count up from 0 to final value
5. **Stamp animation** — FC60 stamp segments appear one by one
6. **Preference** — Respect `prefers-reduced-motion` media query

### Files to Create/Modify
- `frontend/src/styles/animations.css` — NEW
- Multiple component files — MODIFY (add animation classes)

### Acceptance Criteria
- [ ] Page transitions smooth
- [ ] Reduced motion respected
- [ ] Animations don't cause layout shift
- [ ] All tests pass

---

## SESSION 31 — Frontend Polish & Performance

**Block:** Frontend Advanced (Sessions 26-31)
**Complexity:** Medium-High
**Dependencies:** Sessions 19-30 (all frontend)

### What to Build
Final frontend polish: performance optimization, bundle size, code splitting, and visual refinements.

### Detailed Instructions
1. **Bundle analysis** — `npm run build` + analyze bundle. Target: < 500KB gzipped initial load
2. **Code splitting** — Lazy load pages, heavy components (calendar, keyboard)
3. **Image optimization** — Compress any icons/assets
4. **CSS purge** — Ensure Tailwind purges unused classes
5. **Visual audit** — Screenshot every page in both locales + both themes. Fix inconsistencies.
6. **Lighthouse audit** — Target: 90+ on Performance, Accessibility, Best Practices, SEO

### Acceptance Criteria
- [ ] Initial bundle < 500KB gzipped
- [ ] Lighthouse scores 90+ across all categories
- [ ] No visual inconsistencies in any locale/theme combination
- [ ] All tests pass

---

## SESSION 32 — Export & Share

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** Medium-High
**Dependencies:** Session 21 (reading results)

### What to Build
Export readings to PDF, image, and shareable text. Share via link, copy, or social media.

### Detailed Instructions
1. **PDF export** — Generate PDF of reading results (use html-to-pdf or jsPDF). Include all sections, FC60 stamp, patterns.
2. **Image export** — Screenshot of reading card as PNG (use html-to-canvas).
3. **Text export** — Plain text summary for copying to messenger/email.
4. **Share link** — Generate unique URL for reading (public, no auth required to view, read-only).
5. **Social sharing** — Open Graph meta tags for shared links.
6. **Persian support** — PDF and image exports render Persian correctly.

### Files to Create/Modify
- `frontend/src/components/oracle/ExportButton.tsx` — REWRITE
- `frontend/src/utils/exportReading.ts` — NEW
- `api/app/routers/share.py` — NEW (public reading endpoint)

### Acceptance Criteria
- [ ] PDF export generates with all sections
- [ ] Image export captures reading card
- [ ] Share link works for non-authenticated viewers
- [ ] Persian exports render correctly
- [ ] All tests pass

---

## SESSION 33 — Telegram Bot: Core Setup

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** High
**Dependencies:** Sessions 14-16 (reading flows)

### What to Build
Telegram bot foundation: registration, linking accounts, basic commands.

### Detailed Instructions
1. **Bot setup** — Use `python-telegram-bot` library (async version)
2. **Account linking** — User sends API key from Settings page → bot links Telegram chat ID to NPS user account
3. **Commands:**
   - `/start` — Welcome + link instructions
   - `/link <api_key>` — Link Telegram account to NPS
   - `/help` — Show all commands
   - `/status` — Show account status and profile info
   - `/profile` — Show linked Oracle profile
4. **Architecture** — Bot runs as separate service in Docker container. Communicates with API via HTTP.
5. **Security** — API key validated, rate limiting per chat ID.

### Files to Create/Modify
- `services/telegram/` — NEW directory
- `services/telegram/bot.py` — NEW (main bot)
- `services/telegram/handlers/` — NEW (command handlers)
- `services/telegram/Dockerfile` — NEW
- `docker-compose.yml` — MODIFY (add telegram service)

### Acceptance Criteria
- [ ] Bot starts and responds to /start
- [ ] Account linking works with API key
- [ ] All commands respond correctly
- [ ] Bot runs in Docker
- [ ] All tests pass

---

## SESSION 34 — Telegram Bot: Reading Commands

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** High
**Dependencies:** Session 33 (bot core)

### What to Build
Telegram commands for generating readings.

### Detailed Instructions
1. **Commands:**
   - `/time HH:MM` — Generate time reading
   - `/name [name]` — Generate name reading (or use profile name)
   - `/question [text]` — Generate question reading
   - `/daily` — Get today's daily reading
   - `/history` — Show last 5 readings (inline buttons to view details)
2. **Formatting** — Telegram supports Markdown. Format reading sections beautifully.
3. **Progress updates** — Edit message during generation: "⏳ Calculating..." → "🔮 Consulting Wisdom AI..." → "✅ Reading ready!"
4. **Inline keyboard** — After reading, show buttons: "📊 Full Details" | "⭐ Rate" | "📤 Share"

### Files to Create/Modify
- `services/telegram/handlers/readings.py` — NEW
- `services/telegram/formatters.py` — NEW (Telegram Markdown formatting)

### Acceptance Criteria
- [ ] All 4 reading commands generate readings
- [ ] Progress updates show during generation
- [ ] Inline keyboard buttons work
- [ ] All tests pass

---

## SESSION 35 — Telegram Bot: Daily Auto-Insight

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** Medium-High
**Dependencies:** Session 34 (reading commands)

### What to Build
Automatic daily reading delivery via Telegram.

### Detailed Instructions
1. **Scheduled delivery** — Send daily reading at user's preferred time (default: 8:00 AM user timezone)
2. **Opt-in/out** — `/daily_on` and `/daily_off` commands
3. **Time preference** — `/daily_time HH:MM` to set preferred delivery time
4. **Content** — Brief daily insight (shorter than full reading) + "See full reading" button that links to web
5. **Scheduler** — Background task that runs every minute, checks for pending deliveries

### Files to Create/Modify
- `services/telegram/handlers/daily.py` — NEW
- `services/telegram/scheduler.py` — NEW
- `api/app/routers/telegram.py` — NEW (telegram settings API)

### Acceptance Criteria
- [ ] Daily readings delivered at scheduled time
- [ ] Opt-in/out works
- [ ] Time preference saved and respected
- [ ] All tests pass

---

## SESSION 36 — Telegram Bot: Admin Commands & Notifications

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** Medium
**Dependencies:** Session 35 (daily bot)

### What to Build
Admin commands for managing the bot + system notifications via Telegram.

### Detailed Instructions
1. **Admin commands:**
   - `/admin_stats` — System stats (total users, readings today, error count)
   - `/admin_users` — List recent users
   - `/admin_broadcast [message]` — Send message to all linked users
2. **System notifications** — Use `services/oracle/oracle_service/engines/notifier.py` (already exists):
   - Send alerts on: API errors, high error rate, new user registration, system startup/shutdown
   - Admin-only notification channel

### Files to Create/Modify
- `services/telegram/handlers/admin.py` — NEW
- `services/oracle/oracle_service/engines/notifier.py` — MODIFY (integrate with Telegram bot)

### Acceptance Criteria
- [ ] Admin commands work for admin-role users only
- [ ] System notifications delivered to admin Telegram
- [ ] Broadcast sends to all linked users
- [ ] All tests pass

---

## SESSION 37 — Telegram Bot: Multi-User & Polish

**Block:** Features & Integration (Sessions 32-37)
**Complexity:** Medium-High
**Dependencies:** Sessions 33-36 (all bot features)

### What to Build
Multi-user reading via Telegram and final bot polish.

### Detailed Instructions
1. **Multi-user reading** — `/compare @user1 @user2` or `/compare [profile_name1] [profile_name2]`
2. **Error handling** — Friendly error messages for all failure modes
3. **Rate limiting** — Max 10 readings per hour per user
4. **Help text** — Comprehensive help with examples for each command
5. **Persian support** — Bot responds in FA if user's locale is FA
6. **Emoji/formatting** — Consistent use of emoji and Telegram Markdown

### Files to Create/Modify
- `services/telegram/handlers/multi_user.py` — NEW
- All handler files — POLISH
- `services/telegram/i18n/` — NEW (telegram-specific translations)

### Acceptance Criteria
- [ ] Multi-user reading works via Telegram
- [ ] Rate limiting enforced
- [ ] Bilingual responses
- [ ] All tests pass

---

## SESSION 38 — Admin Panel: User Management

**Block:** Admin & DevOps (Sessions 38-40)
**Complexity:** Medium
**Dependencies:** Sessions 2-3 (auth + user API)

### What to Build
Admin-only web interface for managing users and system settings.

### Detailed Instructions
1. **User list** — Sortable, searchable table of all system users. Columns: name, email, role, created date, last login, reading count, status
2. **User actions** — Edit role, reset password, deactivate/reactivate, view reading history
3. **Oracle profile management** — View all Oracle profiles, reassign ownership, delete
4. **Access control** — Only accessible by admin role. 403 for others.
5. **Route** — `/admin/users`, `/admin/profiles`

### Files to Create/Modify
- `frontend/src/pages/Admin.tsx` — NEW
- `frontend/src/components/admin/UserTable.tsx` — NEW
- `frontend/src/components/admin/UserActions.tsx` — NEW
- `frontend/src/components/admin/ProfileTable.tsx` — NEW

### Acceptance Criteria
- [ ] Admin page shows user list
- [ ] CRUD operations work
- [ ] Non-admin users get 403
- [ ] All tests pass

---

## SESSION 39 — Admin Panel: System Monitoring

**Block:** Admin & DevOps (Sessions 38-40)
**Complexity:** Medium-High
**Dependencies:** Session 38 (admin base)

### What to Build
System health dashboard for admins.

### Detailed Instructions
1. **Health dashboard** — Service status (API, Oracle, Scanner, Database, Telegram), uptime, memory usage, CPU
2. **Log viewer** — Recent logs with severity filter. Structured JSON logs from `devops/logging/`.
3. **Reading analytics** — Charts: readings per day, by type, average confidence trend, popular reading times
4. **Error tracking** — Recent errors with stack traces, error rate trend
5. **API:** Extend health endpoints with detailed system info (admin only)

### Files to Create/Modify
- `frontend/src/pages/AdminMonitoring.tsx` — NEW
- `frontend/src/components/admin/HealthDashboard.tsx` — NEW
- `frontend/src/components/admin/LogViewer.tsx` — NEW
- `frontend/src/components/admin/AnalyticsCharts.tsx` — NEW
- `api/app/routers/health.py` — MODIFY (add detailed health for admin)
- `devops/dashboards/simple_dashboard.py` — MODIFY

### Acceptance Criteria
- [ ] Health dashboard shows all service statuses
- [ ] Log viewer displays and filters logs
- [ ] Analytics charts render
- [ ] All tests pass

---

## SESSION 40 — Backup, Restore & Infrastructure

**Block:** Admin & DevOps (Sessions 38-40)
**Complexity:** Medium-High
**Dependencies:** Session 39 (monitoring)

### What to Build
Automated backups, restore functionality, and infrastructure polish.

### Detailed Instructions
1. **Auto backup** — Daily + weekly PostgreSQL backups via cron in Docker. Store locally + optional S3/Railway.
2. **Manual backup** — Admin UI button to trigger immediate backup
3. **Restore** — Admin UI to list backups and restore from selected backup (with confirmation)
4. **Backup management** — Auto-delete backups older than 30 days
5. **Docker Compose polish** — Verify all 7 containers start correctly, health checks, restart policies
6. **Environment validation** — Script that checks all required env vars and connections

### Files to Create/Modify
- `database/scripts/oracle_backup.sh` — MODIFY
- `database/scripts/oracle_restore.sh` — MODIFY
- `frontend/src/components/admin/BackupManager.tsx` — NEW
- `api/app/routers/admin.py` — NEW (backup/restore endpoints)
- `docker-compose.yml` — MODIFY (health checks, restart policies)
- `scripts/validate_env.py` — NEW (or modify existing)

### Acceptance Criteria
- [ ] Auto backup runs on schedule
- [ ] Manual backup creates valid dump
- [ ] Restore recovers data correctly
- [ ] Old backups auto-deleted
- [ ] Docker Compose starts all services
- [ ] All tests pass

---

## SESSION 41 — Integration Tests: Auth & Profiles

**Block:** Testing & Deployment (Sessions 41-45)
**Complexity:** High
**Dependencies:** All previous sessions

### What to Build
Comprehensive integration tests for authentication and Oracle profile flows.

### Detailed Instructions
1. **Auth tests:** Login, token refresh, logout, failed login lockout, role-based access, API key auth
2. **Profile tests:** Create, read, update, delete profiles, ownership enforcement, Persian data handling
3. **Test fixtures:** Seed users with all roles, sample profiles with EN and FA data
4. **Run against real database** (Docker test environment)

### Files to Create/Modify
- `integration/tests/test_auth_flow.py` — NEW
- `integration/tests/test_profile_flow.py` — NEW
- `integration/tests/conftest.py` — MODIFY (add fixtures)

### Acceptance Criteria
- [ ] All auth flow tests pass
- [ ] All profile flow tests pass
- [ ] Tests run against real PostgreSQL
- [ ] Persian data handled correctly in tests

---

## SESSION 42 — Integration Tests: All Reading Types

**Block:** Testing & Deployment (Sessions 41-45)
**Complexity:** High
**Dependencies:** Session 41 (auth tests)

### What to Build
Integration tests for all 5 reading types end-to-end.

### Detailed Instructions
1. **Time reading test** — Create user → submit time reading → verify response has all sections
2. **Name reading test** — Submit name → verify numerology uses the name
3. **Question reading test** — Submit question → verify AI addresses it
4. **Daily reading test** — Generate daily → verify caching → verify different day gives different reading
5. **Multi-user test** — Create 3 users → submit multi-user → verify individual + group results
6. **Framework verification** — Readings use framework (check for framework-specific output fields)
7. **AI mock** — Mock Anthropic API for CI. Test with real API in staging.

### Files to Create/Modify
- `integration/tests/test_time_reading.py` — NEW
- `integration/tests/test_name_reading.py` — NEW
- `integration/tests/test_question_reading.py` — NEW
- `integration/tests/test_daily_reading.py` — NEW
- `integration/tests/test_multi_user_reading.py` — NEW
- `integration/tests/test_framework_integration.py` — NEW

### Acceptance Criteria
- [ ] All 5 reading types produce valid end-to-end results
- [ ] Framework output present in reading results
- [ ] AI interpretation (mocked) included
- [ ] All tests pass

---

## SESSION 43 — E2E Tests: Frontend Flows

**Block:** Testing & Deployment (Sessions 41-45)
**Complexity:** High
**Dependencies:** Sessions 41-42 (backend tests)

### What to Build
Playwright end-to-end tests for all major user flows.

### Detailed Instructions
1. **Login flow** — Open app → login → see dashboard
2. **Profile creation** — Navigate to Oracle → create profile → verify in list
3. **Time reading flow** — Select user → choose time → submit → see results
4. **Multi-user reading flow** — Select multiple users → submit → see comparison
5. **Reading history** — Navigate to history → search → view details
6. **Settings** — Change locale → verify RTL flip → change theme → verify
7. **Responsive** — Run key flows at mobile viewport (375px)
8. **Screenshots** — Capture screenshots at each step for visual review

### Files to Create/Modify
- `frontend/e2e/auth.spec.ts` — NEW
- `frontend/e2e/profile.spec.ts` — NEW
- `frontend/e2e/reading.spec.ts` — NEW
- `frontend/e2e/history.spec.ts` — NEW
- `frontend/e2e/settings.spec.ts` — NEW
- `frontend/e2e/responsive.spec.ts` — NEW
- `frontend/e2e/fixtures.ts` — MODIFY

### Acceptance Criteria
- [ ] All E2E flows complete without errors
- [ ] Screenshots captured for visual review
- [ ] Mobile flows work
- [ ] All tests pass: `cd frontend && npx playwright test`

---

## SESSION 44 — Performance Optimization

**Block:** Testing & Deployment (Sessions 41-45)
**Complexity:** High
**Dependencies:** Sessions 41-43 (all tests)

### What to Build
Optimize performance to meet all targets.

### Detailed Instructions

1. **API targets:**
   - Simple endpoints: < 50ms p95
   - Reading generation: < 5s (including AI call)
   - Profile queries: < 100ms indexed

2. **Frontend targets:**
   - Initial load: < 2 seconds
   - Page transitions: < 100ms
   - Time to interactive: < 3 seconds

3. **Database targets:**
   - Indexed queries: < 100ms
   - Full-text search: < 500ms

4. **Optimization steps:**
   - Profile API responses (add caching headers)
   - Database query optimization (EXPLAIN ANALYZE on slow queries)
   - Frontend bundle splitting
   - API connection pooling
   - Reading result caching for identical inputs

5. **Benchmark script** — Create script that runs N readings and measures p50/p95/p99 response times.

### Files to Create/Modify
- `integration/scripts/perf_audit.py` — MODIFY
- `api/app/middleware/cache.py` — NEW
- Various files for optimization

### Acceptance Criteria
- [ ] API simple endpoints < 50ms p95
- [ ] Frontend initial load < 2s
- [ ] Database indexed queries < 100ms
- [ ] Benchmark script shows all targets met

---

## SESSION 45 — Security Audit & Production Deployment

**Block:** Testing & Deployment (Sessions 41-45)
**Complexity:** Very High
**Dependencies:** All previous sessions

### What to Build
Final security audit and Railway deployment.

### Detailed Instructions

1. **Security audit:**
   - Check for hardcoded secrets (grep for API keys, passwords)
   - SQL injection test (SQLAlchemy parameterized queries)
   - XSS test (React auto-escapes, verify custom `dangerouslySetInnerHTML` uses)
   - CSRF protection
   - Rate limiting verification
   - CORS configuration
   - Auth bypass attempts
   - Encryption verification (AES-256-GCM with ENC4: prefix)

2. **Production environment:**
   - Railway deployment configuration
   - Environment variables in Railway dashboard
   - SSL/TLS certificate (Railway provides)
   - Domain configuration (if custom domain)
   - PostgreSQL production database
   - Docker images optimized (multi-stage builds, minimal layers)

3. **Production checklist:**
   - [ ] All tests pass (unit + integration + E2E)
   - [ ] No security vulnerabilities found
   - [ ] Environment variables set in Railway
   - [ ] Database migrated to production
   - [ ] Seed admin account created
   - [ ] SSL certificate active
   - [ ] Health endpoint returns 200
   - [ ] Telegram bot running
   - [ ] Backup schedule configured
   - [ ] Monitoring active

4. **Documentation:**
   - Deployment guide in `docs/DEPLOYMENT.md`
   - API reference in `docs/API_REFERENCE.md`
   - Update `README.md` with final setup instructions

### Files to Create/Modify
- `integration/scripts/security_audit.py` — MODIFY
- `docs/DEPLOYMENT.md` — NEW
- `docs/API_REFERENCE.md` — NEW
- `README.md` — MODIFY
- Docker files — MODIFY (production optimization)
- `railway.toml` — NEW (or verify)

### Acceptance Criteria
- [ ] Security audit passes with zero critical findings
- [ ] App deployed and accessible via Railway URL
- [ ] SSL active (HTTPS)
- [ ] Health endpoint returns 200
- [ ] Telegram bot responds to commands
- [ ] Admin can login and manage users
- [ ] Reading generation works end-to-end in production
- [ ] Backup runs successfully in production
- [ ] All documentation complete

---

# TERMINAL ASSIGNMENT GUIDE

Each session is independent. Assign to any terminal using this instruction:

```
Read NPS_45_SESSION_MASTER_SPEC.md, go to Session [N], and generate
.session-specs/SESSION_[N]_SPEC.md following the output format defined
in the "Session Spec Output Format" section of the Global Context.

Also read the relevant reference specs listed in the Reference Spec
Mapping table for additional context.

Output the spec to: .session-specs/SESSION_[N]_SPEC.md
```

**Parallel safety:** Sessions within the same block can be generated in parallel since they are spec files (no code changes). All 45 can be generated simultaneously.

**Dependency note:** Dependencies listed in each session are for EXECUTION order (when actually building). For SPEC GENERATION, all sessions can be generated independently and simultaneously.

---

# APPENDIX: Quick Reference

## Framework Module → NPS Component Mapping

| Framework Module | NPS Component | Used In Sessions |
|-----------------|---------------|-----------------|
| `master_orchestrator.py` | `framework_bridge.py` | 6, 7, 14-16 |
| `numerology_engine.py` | Numerology system selection | 8 |
| `signal_combiner.py` | `pattern_formatter.py` | 9 |
| `fc60_stamp_engine.py` | `FC60StampDisplay.tsx` | 10 |
| `moon_engine.py` | `MoonPhaseDisplay.tsx` | 11 |
| `ganzhi_engine.py` | `GanzhiDisplay.tsx` | 11 |
| `heartbeat_engine.py` | `HeartbeatInput.tsx` | 12 |
| `location_engine.py` | `LocationDisplay.tsx` | 12 |
| `universe_translator.py` | AI prompt builder | 13 |
| `reading_engine.py` | Reading orchestrator | 14-16 |
| `logic/00-06` | AI system prompt | 13 |

## Old Files to Delete (Session 6)

```
services/oracle/oracle_service/engines/fc60.py
services/oracle/oracle_service/engines/numerology.py
services/oracle/oracle_service/engines/multi_user_fc60.py
services/oracle/oracle_service/engines/compatibility_analyzer.py
services/oracle/oracle_service/engines/compatibility_matrices.py
services/oracle/oracle_service/engines/group_dynamics.py
services/oracle/oracle_service/engines/group_energy.py
services/oracle/oracle_service/engines/math_analysis.py
services/oracle/oracle_service/engines/scoring.py
services/oracle/oracle_service/engines/balance.py
services/oracle/oracle_service/engines/perf.py
services/oracle/oracle_service/engines/terminal_manager.py
services/oracle/oracle_service/solvers/  (entire folder)
services/oracle/oracle_service/logic/   (entire folder)
```

## 5 Reading Types Summary

| Type | Input | Framework Call | AI Focus |
|------|-------|---------------|----------|
| Time | HH:MM:SS | `current_hour/minute/second` | Moment energy |
| Name | Text string | `full_name` override | Name numerology |
| Question | Question text | Profile data + current time | Answer the question |
| Daily | None (auto) | Profile + today noon | Day overview |
| Multi-user | 2-5 user IDs | N individual + 1 group | Compatibility |
