# Claude Code Workflow Modes

> Two modes of operation. Single-terminal is preferred. Multi-terminal for parallelism when needed.

---

## MODE 1: SINGLE-TERMINAL (Preferred)

One Claude Code terminal handles everything sequentially. This is the default mode.

### Flow:
```
OPEN SESSION
  → Silent boot checks (.claude/startup.md)
  → Read SESSION_LOG.md
  → Show 1-line status
  → Read spec (if referenced)
  → Create comprehensive plan (100% coverage, 100% confidence)
  → Show plan to Dave
  → Wait for approval
  → Execute silently
  → Run tests
  → Auto-format + lint
  → Git commit
  → Update SESSION_LOG.md
  → Define next task
  → Show summary
END SESSION
```

### When to Use:
- Default for all sessions
- Sequential work (one task depends on previous)
- When Dave says "continue" or "next"
- When context allows completing the full task (~80% context budget)

### Context Budget:
- Target: 80% of context limit per session
- Auto-compact at 70% if conversation grows long
- If task exceeds budget: split at natural boundary, note in SESSION_LOG.md

---

## MODE 2: MULTI-TERMINAL (On Request)

Multiple Claude Code terminals working on different layers simultaneously. Use only when Dave explicitly requests parallel work.

### Terminal Assignments:
```
Terminal 1 (T1): FRONTEND     — React, TypeScript, Tailwind
Terminal 2 (T2): API          — FastAPI, Pydantic, routers
Terminal 3 (T3): BACKEND      — Oracle engines, solvers, AI
Terminal 4 (T4): DATABASE     — PostgreSQL, migrations, seeds
Terminal 5 (T5): INFRA        — Docker, nginx, deployment
Terminal 6 (T6): SECURITY     — Encryption, auth, audit
Terminal 7 (T7): DEVOPS       — Monitoring, logging, alerts
```

### Rules for Multi-Terminal:
1. Each terminal reads CLAUDE.md + SESSION_LOG.md at start
2. Each terminal writes to its OWN section in SESSION_LOG.md
3. Use file locking awareness — if two terminals edit same file, last write wins
4. Cross-terminal dependencies noted in the shared dependencies table
5. Stitching issues tracked at bottom of SESSION_LOG.md

### Communication Between Terminals:
Terminals don't talk to each other directly. They communicate through:
- **SESSION_LOG.md** — shared state file
- **Proto files** — `proto/scanner.proto`, `proto/oracle.proto` define contracts
- **Pydantic models** — `api/app/models/` define shared data shapes
- **Database schema** — `database/init.sql` defines shared tables

---

## SESSION_LOG.md FORMAT

```markdown
# SESSION_LOG.md — Development Session Tracker

## Project State Summary
**Plan:** 45-session Oracle rebuild (hybrid)
**Sessions completed:** [N] of 45
**Last session:** [date]
**Current block:** [Foundation / Engines / AI / Frontend / etc.]

---

## Session [N] — [YYYY-MM-DD]
**Terminal:** [T1-T7 or SINGLE]
**Block:** [Foundation / Engines / AI / Frontend / etc.]
**Task:** [One sentence]
**Spec:** [.specs/SPEC_FILE.md or "none"]

**Files changed:**
- `path/to/file1.py` — what changed
- `path/to/file2.tsx` — what changed

**Tests:** [X pass / Y fail / Z new tests added]
**Commit:** [commit hash — message]
**Issues:** [Problems found, or "None"]
**Decisions:** [Decisions made with reasoning, or "None"]

**Next:** [Clear task for next session]

---

## Cross-Terminal Dependencies

| Source | Depends On | Status | Notes |
|--------|-----------|--------|-------|
| T1 (Frontend) | T2 API endpoints | ⏳ Waiting | Need /api/oracle/reading |
| T2 (API) | T4 DB schema | ✅ Ready | oracle_readings table exists |
| T3 (Backend) | T4 DB connection | ✅ Ready | SQLAlchemy configured |
| T3 (Backend) | T6 Encryption | ⏳ Waiting | Need AES-256 service |

---

## Stitching Issues

Track anything that needs fixing when layers connect:

| # | Issue | Layers | Status | Fix |
|---|-------|--------|--------|-----|
| 1 | API model doesn't match frontend type | T1+T2 | 🔴 Open | Sync OracleReading interface |
| 2 | gRPC proto missing new reading type | T2+T3 | 🔴 Open | Add to oracle.proto |
| 3 | DB migration needs rerun after schema change | T4 | 🟡 Pending | Run migrate_all.py |
```

---

## SWITCHING MODES

### From Single to Multi:
Dave says: "Let's go parallel" or "Use multiple terminals"
1. Note current progress in SESSION_LOG.md
2. Identify which terminals are needed
3. Split remaining work across terminals
4. Each terminal starts with CLAUDE.md + SESSION_LOG.md

### From Multi to Single:
Dave says: "Back to single" or just opens one terminal
1. Each terminal completes its current task
2. All terminals update SESSION_LOG.md
3. Resolve any stitching issues
4. Single terminal picks up from combined state

---

## PLAN CREATION PROTOCOL

When creating a plan (before execution), the plan MUST include:

### Structure:
```markdown
# Session [N] Plan — [Task Name]

## Scope
[What this session will accomplish — specific, measurable]

## Prerequisites
- [ ] [What must exist before starting]
- [ ] [What must be verified]

## Steps (Detailed)
### Step 1: [Name]
- What: [Exactly what will be done]
- Files: [Which files created/modified]
- Tests: [What tests will verify this]
- Acceptance: [How to know it's done]

### Step 2: [Name]
[Same structure]

[Continue for all steps]

## Files to Create/Modify
- `path/to/file.py` — [purpose]
- `path/to/file.tsx` — [purpose]

## Tests to Write
- `test_feature_x.py` — [what it verifies]
- `test_feature_y.py` — [what it verifies]

## Risks
- [Risk 1] — [mitigation]
- [Risk 2] — [mitigation]

## Definition of Done
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
- [ ] All tests pass
- [ ] No lint errors
- [ ] Committed to git
```

### Requirements:
- **100% coverage** — every aspect of the task is planned
- **100% confidence** — no "we'll figure this out later" items
- **Specific files listed** — exact paths, not vague references
- **Tests defined** — what exactly gets tested
- **Acceptance criteria** — how Dave (or CI) can verify in 2 minutes
