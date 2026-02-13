# Senior Builder 1/4: Architecture & Foundation Cleanup — Report

**Date:** 2026-02-14
**Scope:** Architecture violations, foundation documentation, legacy code decisions

---

## Summary

SB1 addressed the most critical architecture violation in the NPS codebase — the Claude CLI subprocess integration — and established foundation documentation for encryption, gRPC exceptions, database validation, and engine inventory.

---

## Phase 1: Environment Configuration

**Status:** Already configured (`.env` exists with all required values)

The `.env` file contains all required variables including `ANTHROPIC_API_KEY`, `NPS_ENCRYPTION_KEY`, `NPS_ENCRYPTION_SALT`, database credentials, and Telegram bot tokens. `.gitignore` already excludes `.env`.

---

## Phase 2: AI Engine Rewrite (CRITICAL FIX)

**Status:** Complete

**Problem:** `services/oracle/oracle_service/engines/ai_engine.py` (569 lines) called `/opt/homebrew/bin/claude` via `subprocess.run()`, violating Forbidden Pattern #1 ("NEVER use Claude CLI").

**Solution:** Rewrote `ai_engine.py` (now 307 lines) to delegate all AI calls to `ai_client.py` which uses the Anthropic Python SDK properly.

**What was removed:**

- `import subprocess` — no more process spawning
- `CLAUDE_CLI = "/opt/homebrew/bin/claude"` — no hardcoded binary path
- File-based cache (`CACHE_DIR`, `_read_cache`, `_write_cache`, `_evict_cache`) — `ai_client.py` has its own in-memory cache
- `ask_claude()` — subprocess-based Claude call
- `ask_claude_async()` — threaded subprocess wrapper
- `get_ai_insight_async()` — fallback wrapper around subprocess

**What was preserved (identical public API):**

- `NPS_SYSTEM_PROMPT` — scanner-specific system prompt
- `is_available()` — delegates to `ai_client.is_available()`
- `clear_cache()` — delegates to `ai_client.clear_cache()`
- `analyze_scan_pattern()` — same signature, same response parsing
- `numerology_insight_for_key()` — same signature, same response parsing
- `brain_strategy_recommendation()` — same signature, same response parsing
- `brain_mid_session_analysis()` — same signature, same response parsing
- `brain_session_summary()` — same signature, same response parsing

**Verification:**

- `grep -r "subprocess" ai_engine.py` — no matches (only appears in docstring comment about NOT using it)
- `grep -r "/opt/homebrew" services/oracle/` — no matches
- All imports from `scanner_brain.py` verified working

---

## Phase 3: gRPC Bypass Documentation

**Status:** Complete

**Finding:** Only 1 gRPC bypass in non-archive code:

- `api/app/routers/learning.py:255` — imports `learner.py` functions directly

**Decision:** Acceptable exception. Admin-only endpoint (`oracle:admin` scope), maintenance operation, same-process optimization. Documented in `docs/ARCHITECTURE_EXCEPTIONS.md`.

**File created:** `docs/ARCHITECTURE_EXCEPTIONS.md` (with template for future exceptions)

---

## Phase 4: Database Schema Validation

**Status:** Complete

**File created:** `scripts/validate_db_schema.py`

Features:

- Parses expected tables and indexes from `database/schemas/*.sql`
- Connects to PostgreSQL and validates presence
- Checks triggers
- Generates pass/fail report
- Supports `--dry-run` mode (schema parsing only, no DB needed)
- Supports environment variables for connection (`POSTGRES_HOST`, etc.)

**Dry-run verification:** Successfully parsed 7 tables and 26 indexes from schema files.

**Full validation** requires Docker (`docker-compose up -d postgres`).

---

## Phase 5: Legacy Code Decision

**Status:** Complete — DEVIATED FROM ORIGINAL PROMPT

**Original request:** Move `vault.py` and `notifier.py` to `.archive/legacy/`

**Decision:** Do NOT move them. Investigation confirmed both are active production code:

- `vault.py` is imported by `notifier.py` (lines 683, 780, 788, 799)
- `notifier.py` is imported by `logger.py` (line 44)
- Both have production-quality implementations, not legacy stubs

**Instead:**

1. Created `services/oracle/oracle_service/engines/README.md` — documents all 21 engine modules with purpose, key exports, and dependency graph
2. Created `api/app/services/notification_service.py` — proper API-layer wrapper for notifications with `NotificationType` enum and `get_notification_service()` FastAPI dependency

---

## Phase 6: Encryption Specification

**Status:** Complete

**File created:** `docs/ENCRYPTION_SPEC.md`

Documents:

- ENC4 format: AES-256-GCM, PBKDF2-HMAC-SHA256 (600K iterations), 12-byte nonce, 16-byte tag
- Legacy ENC format: HMAC-SHA256 stream cipher (decrypt-only)
- Wire formats for both
- Sensitive field lists (scanner + Oracle)
- Environment variables
- Security properties
- Migration path from ENC to ENC4

---

## Files Changed

| Action  | File                                                  | Lines      |
| ------- | ----------------------------------------------------- | ---------- |
| Rewrite | `services/oracle/oracle_service/engines/ai_engine.py` | 569 -> 307 |
| Create  | `docs/ARCHITECTURE_EXCEPTIONS.md`                     | ~80        |
| Create  | `scripts/validate_db_schema.py`                       | ~250       |
| Create  | `services/oracle/oracle_service/engines/README.md`    | ~65        |
| Create  | `api/app/services/notification_service.py`            | ~110       |
| Create  | `docs/ENCRYPTION_SPEC.md`                             | ~185       |
| Create  | `docs/SENIOR_BUILDER_1_REPORT.md`                     | this file  |

**Total:** 1 file rewritten, 6 files created

---

## Verification Checklist

- [x] No `/opt/homebrew/bin/claude` references in `services/oracle/`
- [x] No `subprocess` usage in `ai_engine.py`
- [x] `scanner_brain.py` imports from `ai_engine` still work
- [x] AI uses only Anthropic SDK (via `ai_client.py`)
- [x] gRPC bypass documented in `ARCHITECTURE_EXCEPTIONS.md`
- [x] DB validation script exists and parses schemas correctly (7 tables, 26 indexes)
- [x] `vault.py` and `notifier.py` untouched (still in engines/)
- [x] `notification_service.py` created in API layer
- [x] Encryption spec documented
- [x] This report complete

---

## Issues for SB2

1. **Notification service integration** — `notification_service.py` wraps the notifier but isn't wired into any routes yet. SB2 should integrate it where API routes need to send notifications.
2. **Learning endpoint** — The gRPC bypass in `learning.py` is documented but could be refactored to use a proper service layer in SB2.
3. **DB validation against live database** — The validation script needs `docker-compose up -d postgres` to run a full check. Consider adding to CI.
4. **ai_engine.py unused functions** — `ask_claude()`, `ask_claude_async()`, and `get_ai_insight_async()` were removed. If any other code besides `scanner_brain.py` referenced them, those imports will fail. Grep found no other importers, but worth monitoring.
5. **Engine test coverage** — The engines directory has 21 modules but no local test suite. SB2 should consider adding `services/oracle/tests/`.
