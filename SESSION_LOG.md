# SESSION_LOG.md — Development Session Tracker

> Claude Code reads this at step 2 of every session.
> Update at the END of every session.

---

## Project State Summary

**Plan:** 45-session Oracle rebuild (hybrid approach)
**Strategy:** Keep infrastructure, rewrite Oracle logic
**Sessions completed:** 2 of 45
**Last session:** Session 2 — Authentication System Hardening
**Current block:** Foundation (Sessions 1-5)

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
