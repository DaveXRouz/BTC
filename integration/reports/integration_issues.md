# NPS Integration Issues Log

**Session:** INTEGRATION-S2 (Deep Testing & Final Polish)
**Date:** 2026-02-08

---

## Critical Issues (Blocking)

### ISSUE-001: `deleted_at` column missing from `oracle_users`

- **Severity:** Critical
- **Found in:** Phase 1 planning (schema analysis)
- **Component:** Database schema (`init.sql` line 213-227)
- **Impact:** All soft-delete operations fail. ORM (`oracle_user.py:28`) defines `deleted_at`, router filters by `OracleUser.deleted_at.is_(None)` at lines 390, 432, 474, 515, 577 — but the column doesn't exist in the table.
- **Fix:** Added `deleted_at TIMESTAMPTZ` column to `oracle_users` table + partial index `idx_oracle_users_active` for efficient soft-delete queries.
- **Status:** Fixed
- **Regression test:** `TestSchemaFixes.test_deleted_at_column_exists`, `TestSchemaFixes.test_soft_delete_workflow`

### ISSUE-002: `sign_type` CHECK constraint too restrictive

- **Severity:** Critical
- **Found in:** Phase 1 planning (code trace)
- **Component:** Database schema (`init.sql` line 252)
- **Impact:** Inserting readings with `sign_type='reading'` (from `oracle.py:119`), `sign_type='multi_user'` (from `oracle_reading.py:339`), or `sign_type='daily'` fails with CHECK violation.
- **Original constraint:** `sign_type IN ('time', 'name', 'question')`
- **Fix:** Expanded to `sign_type IN ('time', 'name', 'question', 'reading', 'multi_user', 'daily')`
- **Status:** Fixed
- **Regression test:** `TestSchemaFixes.test_sign_type_reading_allowed`

### ISSUE-003: `user_id` NOT NULL constraint blocks anonymous readings

- **Severity:** Critical
- **Found in:** Phase 1 planning (constraint analysis)
- **Component:** Database schema (`init.sql` line 253-255)
- **Impact:** All single-user reading endpoints (`/reading`, `/question`, `/name`) store `user_id=None` (see `oracle.py:117-118`), but the CHECK constraint requires `user_id IS NOT NULL` for single-user readings.
- **Original constraint:** `(is_multi_user = FALSE AND user_id IS NOT NULL)`
- **Fix:** Relaxed to `(is_multi_user = FALSE)` — allow anonymous single-user readings.
- **Status:** Fixed
- **Regression test:** `TestSchemaFixes.test_null_user_id_single_user_reading`

---

## Medium Issues

### ISSUE-004: Performance baseline empty

- **Severity:** Medium
- **Found in:** Phase 1 planning
- **Component:** `integration/reports/performance_baseline.json`
- **Impact:** All values are `null`. No actual measurements exist.
- **Fix:** Created `perf_audit.py` script to benchmark endpoints and populate baseline.
- **Status:** Fixed

### ISSUE-005: No `integration_issues.md` report

- **Severity:** Medium
- **Found in:** Phase 1 planning
- **Component:** `integration/reports/`
- **Impact:** Spec expects this file to exist; it was never created in S1.
- **Fix:** This file.
- **Status:** Fixed

---

## Low Issues

### ISSUE-006: No multi-user integration tests

- **Severity:** Low
- **Found in:** Phase 2 planning
- **Component:** `integration/tests/`
- **Impact:** Multi-user flow tested at unit level only, not through API.
- **Fix:** Created `test_multi_user.py` with comprehensive test suite.
- **Status:** Fixed

### ISSUE-007: No browser E2E tests

- **Severity:** Low
- **Found in:** Phase 3 planning
- **Component:** `frontend/`
- **Impact:** No automated browser testing exists.
- **Fix:** Created Playwright test suite in `e2e/`.
- **Status:** Fixed

### ISSUE-008: ARIA accessibility gaps in Oracle components

- **Severity:** Low
- **Found in:** Phase 6 planning
- **Component:** Oracle frontend components
- **Impact:** Missing `aria-*` attributes, tab roles, and form accessibility.
- **Fix:** Added ARIA attributes to OracleConsultationForm, ReadingResults, UserForm.
- **Status:** Fixed

---

## Summary

| Severity  | Found | Fixed | Open  |
| --------- | ----- | ----- | ----- |
| Critical  | 3     | 3     | 0     |
| Medium    | 2     | 2     | 0     |
| Low       | 3     | 3     | 0     |
| **Total** | **8** | **8** | **0** |
