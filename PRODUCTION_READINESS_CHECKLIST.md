# NPS V4 Production Readiness Checklist

## Critical (Must Pass)

- [x] Database schema has `deleted_at` column on `oracle_users`
- [x] Database `sign_type` CHECK allows `reading`, `multi_user`, `daily`
- [x] Database `user_check` allows anonymous (NULL `user_id`) readings
- [x] Partial index `idx_oracle_users_active` for soft-delete performance
- [x] All 13 Oracle API endpoints return correct status codes
- [x] Auth enforcement: 401 without token, 403 with invalid token
- [x] Encryption at rest operational (ENC4: prefix when key configured)
- [x] Soft-delete workflow: delete -> 404 on GET -> recreate succeeds

## Integration Tests

- [x] `test_database.py` — schema, CRUD, constraints, triggers, schema fixes
- [x] `test_api_oracle.py` — user CRUD, readings, encryption, auth, soft-delete
- [x] `test_api_health.py` — health endpoint verification
- [x] `test_frontend_api.py` — frontend-API connectivity
- [x] `test_e2e_flow.py` — full Oracle flow with timing + multi-user step
- [x] `test_multi_user.py` — core flow, validation, performance, junction table
- [x] `test_security.py` — auth, encryption, rate limiting, input validation

## Performance

- [x] Performance audit script (`perf_audit.py`) created
- [x] Targets defined for all Oracle endpoints
- [x] `performance_baseline.json` structure ready for population
- [x] Multi-user performance targets: 2-user <5s, 5-user <8s, 10-user <15s

## Security

- [x] Security audit script (`security_audit.py`) created
- [x] Auth enforcement verified (7 checks)
- [x] Input validation tests for special chars, long input, invalid dates
- [x] Credential scan for leaked secrets in source
- [x] CORS enforcement check
- [x] No subprocess calls in production code

## Frontend

- [x] Playwright E2E config and 8 test scenarios
- [x] ARIA accessibility: `role="tablist"`, `role="tab"`, `aria-selected`
- [x] ARIA accessibility: `role="dialog"`, `aria-modal`
- [x] ARIA accessibility: `aria-required`, `aria-invalid`, `aria-describedby`
- [x] ARIA accessibility: `aria-busy` on submit, `aria-live="polite"` on errors
- [x] Accessibility unit tests (`Accessibility.test.tsx`)

## Documentation

- [x] `README.md` — project overview, architecture, quick start
- [x] `docs/api/API_REFERENCE.md` — all working endpoints with examples
- [x] `docs/DEPLOYMENT.md` — Docker, manual, SSL, monitoring, backup
- [x] `docs/TROUBLESHOOTING.md` — common issues and solutions
- [x] `integration/reports/integration_issues.md` — 8 issues tracked
- [x] `integration/reports/FIXES_LOG.md` — 6 fixes documented
- [x] `PRODUCTION_READINESS_CHECKLIST.md` — this file

## Automated Verification

```bash
chmod +x scripts/production_readiness_check.sh && ./scripts/production_readiness_check.sh
```
