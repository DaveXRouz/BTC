# CLAUDE.md — NPS V4 Project Brain

> **Read this file FIRST. Every session. No exceptions.**
> **Last updated:** 2026-02-09

---

## BOOT SEQUENCE

When you open this project, execute this SILENTLY (no output to user):

```
1. READ this file (CLAUDE.md)
2. READ SESSION_LOG.md → find the next task
3. READ .claude/startup.md → run silent checks
4. SHOW 1-line status: "Continuing session [N]: [task name]"
5. READ the relevant spec file if one is referenced
6. CREATE comprehensive plan → show to user → wait for approval
7. EXECUTE after approval
```

**If user says "continue" or "next" or "go":** follow steps 1-7 automatically.
**If user gives a specific task:** skip step 2, do that task instead.
**If user says nothing after opening:** follow steps 1-4, then wait.

**First session (no prior entries in SESSION_LOG.md):**
If SESSION_LOG.md has zero session entries, start Session 1 of the current block. Read the session-to-spec mapping table in SESSION_LOG.md to find relevant reference specs.

For detailed startup protocol → `.claude/startup.md`
For workflow modes → `.claude/workflows.md`
For all workflow paths → `.claude/master-workflow.md`

---

## PROJECT IDENTITY

**Name:** NPS (Numerology Puzzle Solver) V4
**Purpose:** Bitcoin wallet hunting via Scanner ↔ Oracle collaboration with AI learning
**Repo:** https://github.com/DaveXRouz/BTC.git
**Owner:** Dave (DaveXRouz)

**Simple version:** Scanner generates Bitcoin keys fast. Oracle analyzes patterns using numerology + AI. They share a PostgreSQL database and make each other smarter over time.

**Design philosophy:** Swiss watch — simple surface, sophisticated internals.

---

## CURRENT STATE

**Active plan:** 45-session Oracle rebuild (hybrid approach)
**Strategy:** Keep infrastructure, rewrite Oracle logic
**Sessions completed:** Check SESSION_LOG.md for current count

### What EXISTS (from earlier 16-session scaffolding):

| Layer                   | Status          | Keep/Rewrite                           |
| ----------------------- | --------------- | -------------------------------------- |
| Frontend (React)        | ~80% scaffolded | KEEP shells, REWRITE Oracle internals  |
| API (FastAPI)           | ~70% scaffolded | KEEP skeleton, REWRITE Oracle handlers |
| Backend/Oracle          | ~60% scaffolded | REWRITE engines, reading logic, AI     |
| Database (PostgreSQL)   | Done            | KEEP                                   |
| Scanner (Rust)          | Stub only       | DO NOT TOUCH                           |
| Infrastructure (Docker) | Partial         | KEEP                                   |
| DevOps (Monitoring)     | Partial         | KEEP                                   |
| Integration Tests       | 56+ tests       | KEEP, extend                           |

### 45-Session Blocks:

| Block                  | Sessions | Focus                           |
| ---------------------- | -------- | ------------------------------- |
| Foundation             | 1-5      | Database schema, auth, profiles |
| Calculation Engines    | 6-12     | FC60, numerology, zodiac        |
| AI & Reading Types     | 13-18    | Wisdom AI, 5 reading flows      |
| Frontend Core          | 19-25    | Layout, Oracle UI, results      |
| Frontend Advanced      | 26-31    | RTL, responsive, accessibility  |
| Features & Integration | 32-37    | Export, share, Telegram         |
| Admin & DevOps         | 38-40    | Admin UI, monitoring, backup    |
| Testing & Deployment   | 41-45    | Tests, optimization, deploy     |

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────┐
│  LAYER 1: FRONTEND                          │
│  React + TypeScript + Tailwind + Vite       │
│  Port: 5173 (dev) / 80 (prod nginx)        │
│  i18n: English + Persian (RTL)              │
└──────────────┬──────────────────────────────┘
               │ HTTP / WebSocket
┌──────────────▼──────────────────────────────┐
│  LAYER 2: API GATEWAY                       │
│  FastAPI + Python 3.11+                     │
│  Port: 8000 │ Docs: /docs (Swagger)        │
│  Auth: JWT + API Key + Legacy               │
└──────┬───────────────────┬──────────────────┘
       │ SQLAlchemy         │ gRPC
┌──────▼──────┐    ┌───────▼──────────────────┐
│  LAYER 4:   │    │  LAYER 3: BACKEND        │
│  DATABASE   │    │  Oracle (Python :50052)   │
│  PostgreSQL │◄───┤  Scanner (Rust :50051)    │
│  Port: 5432 │    │  AI via Anthropic API     │
└─────────────┘    └──────────────────────────┘

LAYER 5: Docker Compose (7 containers)
LAYER 6: AES-256-GCM + API keys (3-tier)
LAYER 7: JSON logging + Prometheus + Telegram alerts
```

### Scanner ↔ Oracle Loop:

```
Scanner generates keys → checks balances → stores in PostgreSQL
    ↓
Oracle analyzes patterns → suggests lucky ranges → confidence scores
    ↓
Scanner prioritizes suggestions → finds more → AI learns → REPEAT
```

For detailed architecture → `logic/ARCHITECTURE_DECISIONS.md`
For loop details → `logic/SCANNER_ORACLE_LOOP.md`

---

## REPOSITORY LAYOUT

```
BTC/
├── CLAUDE.md              ← YOU ARE HERE
├── README.md              ← Human overview
├── SESSION_LOG.md         ← Session tracker (read at step 2)
├── .claude/               ← Detailed Claude Code configs
│   ├── startup.md             Boot protocol + silent checks
│   ├── workflows.md           Single-terminal + multi-terminal modes
│   ├── master-workflow.md     All paths through the 45-session build
│   └── templates.md           File templates (Python, TS, Rust)
├── logic/                 ← Algorithm docs + recipes
│   ├── FC60_ALGORITHM.md      FC60 math + formulas + test vectors
│   ├── NUMEROLOGY_SYSTEMS.md  Pythagorean + Chaldean + Abjad
│   ├── ARCHITECTURE_DECISIONS.md  10 key decisions with reasoning
│   ├── SCANNER_ORACLE_LOOP.md     Collaboration pattern
│   └── RECIPES.md             Step-by-step common task recipes
├── api/                   ← FastAPI gateway
├── frontend/              ← React + TypeScript + Tailwind
├── services/oracle/       ← Python Oracle service
├── services/scanner/      ← Rust scanner [STUB]
├── database/              ← PostgreSQL schemas + migrations
├── integration/           ← 56+ integration tests
├── devops/                ← Monitoring + alerts
├── infrastructure/        ← Nginx + Prometheus
├── proto/                 ← gRPC definitions
├── scripts/               ← Deploy, backup, restore
├── docs/                  ← API reference, deployment guide
├── .archive/              ← V1/V3 code (READ-ONLY)
├── .specs/                ← 16-session specs (reference only)
├── .session-specs/        ← 45-session specs (active)
├── .project/              ← Project management playbooks
└── docker-compose.yml
```

---

## OPERATING RULES

### Autonomy Level: MAXIMUM

Make all decisions yourself. Only ask Dave for:

- **Money** — paid services, API costs, infrastructure upgrades
- **Security** — encryption changes, auth system changes, key management
- **Architecture** — changes that affect multiple layers or the overall design

Everything else: decide, do it, show results.

### Communication: SILENT WORKER

**During planning (before work starts):**

- Complex tasks (new features, multi-file changes, new sessions): show plan → wait for approval
- Simple tasks (bug fix, typo, single-file edit, direct instruction): execute directly, no plan needed

**During execution (after plan is approved or task is simple):**

- Work silently. No progress narration.
- Show results at the end only.

**Rule of thumb:** If a task takes more than 5 minutes or touches more than 2 files, show a plan first.

### Error Handling: 3-STRIKE RULE

```
Error encountered →
  Attempt fix #1 (silently) →
    Still broken → Attempt fix #2 (silently) →
      Still broken → Attempt fix #3 (silently) →
        Still broken → STOP. Tell Dave what's wrong. Ask for guidance.
```

### Quality Pipeline (Every File, Every Time):

```
Write code
  → Auto-format (black/prettier/rustfmt)
  → Auto-lint + fix (ruff/eslint/clippy)
  → Write tests
  → Run tests (must pass before "done")
  → Auto-generate docs (public APIs + complex logic only)
  → Git commit with descriptive message
```

### Git Behavior:

- Auto-commit after each completed task
- Commit message format: `[layer] description (#session)`
  - Example: `[api] add oracle reading endpoint (#session-13)`
- Auto `git stash` before risky changes (revert if broken)
- Never commit broken code — tests must pass first

### Dependency Management:

- Auto-install known safe packages (from requirements.txt, package.json, Cargo.toml) silently
- For NEW/unknown packages: ask Dave first
- Run `pip-audit` / `npm audit` after installing — flag vulnerabilities

### Context Limit:

- Auto-compact at 70% context capacity
- Keep working after compaction — don't stop or ask
- If a task is too large for one context: split it, note split point in SESSION_LOG.md

### Web Search:

- Use ONLY for: package version verification, API documentation lookups
- Do NOT search for: general coding questions, tutorials, Stack Overflow

---

## 10 FORBIDDEN PATTERNS

1. **NEVER use Claude CLI** (`subprocess`, `os.system`, shell commands for AI). Only Anthropic HTTP API.
2. **NEVER store secrets in code.** Always `.env` variables.
3. **NEVER use bare `except:` in Python.** Catch specific exceptions.
4. **NEVER use `.unwrap()` in Rust production code.** Use `Result<T,E>`.
5. **NEVER use `any` type in TypeScript.** Define proper interfaces.
6. **NEVER hardcode file paths.** Use `Path(__file__).resolve().parents[N]`.
7. **NEVER skip tests.** Every change gets tested before commit.
8. **NEVER modify `.archive/` folder.** Read-only reference.
9. **NEVER commit `.env` files.** Only `.env.example`.
10. **NEVER say "done" without proof.** Tests pass + verification output.

---

## ARCHITECTURE RULES (Non-Negotiable)

1. **API is the gateway** — Frontend/Telegram only talk to FastAPI. Never directly to gRPC services.
2. **AI uses API only** — Anthropic Python SDK, HTTP calls. Never CLI.
3. **Proto contracts are source of truth** — `scanner.proto` and `oracle.proto` define interfaces.
4. **Scoring consistency** — Rust and Python must produce identical outputs for same input.
5. **V3 engines are reference** — `.archive/v3/engines/` is the math baseline. New code must match outputs.
6. **Environment over config files** — `.env` only. Not `config.json`.
7. **AES-256-GCM encryption** — `ENC4:` prefix (V4). `ENC:` fallback for V3 migration only.
8. **Layer separation** — No shortcuts. Frontend→API→Service→Database.
9. **Persian UTF-8** — All text supports Persian. RTL when locale is FA.
10. **Graceful degradation** — Missing API key = fallback text, not crash. Missing Redis = in-memory.

---

## SECURITY RULES

- AES-256-GCM, keys via `secrets.token_hex(32)`
- API keys: SHA-256 hashed in DB, plaintext shown only at creation
- Three-tier scopes: `admin` / `moderator` / `user`
- Audit all security events to `oracle_audit_log` table
- No plaintext private keys in database — ever
- SSL/TLS in production (nginx terminates)
- Security scan on every commit (check for leaked secrets, SQL injection, XSS)

---

## KEY COMMANDS

```bash
# Services
make up                    # Start all (Docker)
make dev-api               # FastAPI :8000
make dev-frontend          # Vite :5173

# Tests
cd api && python3 -m pytest tests/ -v
cd frontend && npm test
cd services/oracle && python3 -m pytest tests/ -v
python3 -m pytest integration/tests/ -v -s
cd frontend && npx playwright test

# Quality
make lint && make format
pip-audit                  # Python vulnerability check
npm audit                  # Node vulnerability check

# Database
docker-compose exec postgres psql -U nps -d nps
make backup
```

---

## MCP SERVERS (Plugins)

Use these when available:

- **GitHub MCP** — auto PR, issue tracking, branch management
- **PostgreSQL MCP** — direct DB queries, schema verification
- **File System MCP** — advanced file operations, bulk search

---

## SMART TOOL USAGE

### Extended Thinking (deep reasoning):

- **AUTO-USE for:** architecture, security, complex algorithms, trade-offs, multi-file refactors
- **SKIP for:** simple edits, standard CRUD, formatting, straightforward fixes

### Subagents (parallel workers):

- **AUTO-USE for:** 3+ file creation, independent modules, test+implementation simultaneously
- **SKIP for:** sequential tasks, single-file changes, tightly coupled tasks

### Thinking Depth: USE YOUR BRAIN

Use deep/extended thinking for:

- **Architecture decisions** — anything touching 2+ layers or choosing between approaches
- **Security** — encryption, auth, key management, vulnerability analysis
- **Complex algorithms** — FC60, numerology engines, AI scoring, pattern matching
- **Trade-off analysis** — when choosing between options with real consequences
- **Multi-file refactors** — understanding ripple effects before making changes
- **Bug diagnosis** — when root cause isn't obvious from surface symptoms

Skip deep thinking for:

- Simple edits, standard CRUD, formatting fixes
- Following established patterns (e.g., "add another endpoint like the existing ones")
- Direct instructions with no ambiguity

**Rule:** When in doubt, think deeper. The cost of over-thinking is low. The cost of under-thinking is rework.

### Model Strategy: Right Model for the Job

| Task Type                                   | Model      | Why                                |
| ------------------------------------------- | ---------- | ---------------------------------- |
| Architecture, security, complex logic       | **Opus**   | Deep reasoning, nuance, trade-offs |
| Standard implementation, features, tests    | **Sonnet** | Fast, capable, cost-effective      |
| Quick lookups, simple searches, boilerplate | **Haiku**  | Fastest, cheapest, good enough     |

**Subagent model selection:**

- `Explore` agents → **Haiku** (file counting, pattern finding, codebase navigation)
- `Plan` agents → **Sonnet** (design work, implementation planning)
- Code review agents → **Sonnet** (quality analysis needs good judgment)
- Complex research → **Opus** (only when reasoning depth matters)

**Default:** Sonnet for most work. Upgrade to Opus for decisions that affect architecture. Downgrade to Haiku for mechanical tasks.

### Session Spec Workflow: How Sessions Get Built

Sessions follow a two-phase workflow:

**Phase 1 — Spec Creation (before session starts):**

```
1. Read SESSION_LOG.md → identify next session number and block
2. Read relevant .specs/ files for reference context
3. Read logic/ docs for algorithm/architecture guidance
4. Create .session-specs/SESSION_[N]_SPEC.md with:
   - Objectives (what gets built)
   - Files to create/modify (exact paths)
   - Acceptance criteria (how to verify)
   - Test requirements
   - Dependencies on previous sessions
5. Show spec to Dave → wait for approval
```

**Phase 2 — Execution (after spec approval):**

```
1. Read approved .session-specs/SESSION_[N]_SPEC.md
2. Execute silently per CLAUDE.md rules
3. Run quality pipeline on every file
4. Update SESSION_LOG.md at end
5. Git commit with session tag
```

**Spec storage:** `.session-specs/` folder (tracked in git).
**Naming:** `SESSION_[N]_SPEC.md` (e.g., `SESSION_1_SPEC.md`).
**Old specs:** `.specs/` folder is REFERENCE ONLY from the 16-session scaffolding.

---

## EXISTING CODE POLICY

When you touch any file that doesn't match project standards:

- **Fix it proactively.** Don't just fix what you came for — upgrade the whole file.
- Apply templates from `.claude/templates.md`
- Add missing type hints, docstrings, error handling
- Run linter + formatter on the file

---

## SESSION END PROTOCOL

Every session MUST end with:

1. ✅ Update SESSION_LOG.md (what done, files changed, test results)
2. ✅ Git commit with descriptive message
3. ✅ Define next session's task clearly in SESSION_LOG.md
4. ✅ Show summary to Dave

---

## SPEC FILE PROTOCOL

When a session references a spec from `.specs/` or `.session-specs/`:

1. Read the full spec
2. Create a **comprehensive, detailed plan** that covers 100% of everything needed
3. The plan must have **100% confidence** — no gaps, no "we'll figure this out later"
4. Show the plan to Dave
5. Wait for approval
6. Execute silently after approval

---

## ENVIRONMENT VARIABLES

All config in `.env` (copy from `.env.example`):

| Variable              | Purpose                   | Required                     |
| --------------------- | ------------------------- | ---------------------------- |
| `POSTGRES_PASSWORD`   | Database password         | Yes                          |
| `API_SECRET_KEY`      | JWT signing + legacy auth | Yes                          |
| `NPS_ENCRYPTION_KEY`  | AES-256-GCM key (hex)     | For encryption               |
| `NPS_ENCRYPTION_SALT` | Encryption salt (hex)     | For encryption               |
| `ANTHROPIC_API_KEY`   | AI interpretations        | Optional (graceful fallback) |
| `NPS_BOT_TOKEN`       | Telegram bot token        | Optional                     |
| `NPS_CHAT_ID`         | Telegram chat ID          | Optional                     |

---

## PERFORMANCE TARGETS

| Operation                | Target      |
| ------------------------ | ----------- |
| API response (simple)    | < 50ms p95  |
| API response (reading)   | < 5 seconds |
| Frontend initial load    | < 2 seconds |
| Frontend transitions     | < 100ms     |
| Database query (indexed) | < 100ms     |

---

## FILE REFERENCES

| Need                               | Read                              |
| ---------------------------------- | --------------------------------- |
| Boot protocol + silent checks      | `.claude/startup.md`              |
| Single vs multi-terminal workflows | `.claude/workflows.md`            |
| File creation templates            | `.claude/templates.md`            |
| FC60 math + formulas               | `logic/FC60_ALGORITHM.md`         |
| Numerology systems                 | `logic/NUMEROLOGY_SYSTEMS.md`     |
| Architecture decisions             | `logic/ARCHITECTURE_DECISIONS.md` |
| Scanner↔Oracle loop                | `logic/SCANNER_ORACLE_LOOP.md`    |
| Common task step-by-step           | `logic/RECIPES.md`                |
| Session history                    | `SESSION_LOG.md`                  |
| Spec files (reference)             | `.specs/` folder                  |
| Session specs (active)             | `.session-specs/` folder          |
| All workflow paths                 | `.claude/master-workflow.md`      |
| V3 source (reference)              | `.archive/v3/`                    |
| Project playbooks                  | `.project/` folder                |
