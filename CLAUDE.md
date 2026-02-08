# CLAUDE.md — Project Instructions for Claude Code

## Project Overview

NPS (Numerology Puzzle Solver) V4 is a distributed microservices architecture for FC60 numerology, oracle readings, and mathematical analysis. V4 transforms the V3 Python/tkinter desktop app into a web-accessible platform with FastAPI backend, React frontend, and specialized microservices.

## Repository Layout

- `api/` — FastAPI REST + WebSocket gateway
  - `app/routers/` — 6 routers: health, auth, scanner, oracle, vault, learning
  - `app/models/` — Pydantic request/response schemas
  - `app/middleware/` — Auth (JWT + API keys), rate limiting
  - `app/orm/` — SQLAlchemy ORM models
  - `app/services/` — Business logic (oracle_reading, security, audit)
- `frontend/` — React + TypeScript + Tailwind (Vite build)
  - `src/pages/` — 6 pages: Dashboard, Scanner, Oracle, Vault, Learning, Settings
  - `src/components/` — Shared UI components (Layout, StatsCard, LogPanel)
  - `src/services/` — API client (`api.ts`) and WebSocket client (`websocket.ts`)
  - `src/types/` — TypeScript types mirroring API Pydantic models
  - `src/i18n/` — Internationalization (EN, stubs for ES/FR)
  - `e2e/` — Playwright browser tests
- `services/scanner/` — Rust high-performance scanner (Cargo project)
  - `src/crypto/` — secp256k1, bip39, address derivation
  - `src/scanner/` — Multi-threaded scan loop with checkpoints
  - `src/balance/` — Async balance checking via reqwest
  - `src/scoring/` — Scoring engine (must match Python Oracle weights)
  - `src/grpc/` — gRPC server implementing scanner.proto
- `services/oracle/` — Python Oracle service (gRPC)
  - `oracle_service/engines/` — V3 engines copied as-is: fc60, numerology, oracle
  - `oracle_service/logic/` — V3 logic: timing_advisor, strategy_engine
- `proto/` — Shared protobuf contracts (scanner.proto, oracle.proto)
- `database/` — PostgreSQL schema (`init.sql`) and V3->V4 migration scripts
- `infrastructure/` — Nginx config, Prometheus monitoring
- `integration/` — Integration tests, scripts, reports
- `devops/` — Monitoring, alerting, dashboards
- `scripts/` — deploy.sh, backup.sh, restore.sh, rollback.sh
- `docs/` — Architecture specs, API reference, deployment guide
- `.archive/` — Legacy versions (V1, V2, V3). Do not use for V4 development.
  - `v1/` — V1 source (read-only)
  - `v2/` — V2 source (gitignored, read-only)
  - `v3/` — V3 Python/tkinter monolith (read-only)
  - `old-docs/` — V3-era documentation and root .md files
- `.specs/` — V4 session specification files for Claude Code execution
- `.project/` — Project architecture plans and Claude workflow guides
- `docker-compose.yml` — 7-container orchestration

## Key Commands

```bash
# Start all services
make up

# Development servers
make dev-api      # FastAPI on :8000
make dev-frontend  # Vite on :5173

# Run tests
make test

# Run API tests
cd api && python3 -m pytest tests/ -v

# Run integration tests (requires running API + DB)
python3 -m pytest integration/tests/ -v -s

# Run E2E browser tests
cd frontend && npx playwright test

# Generate gRPC stubs from proto files
make proto

# Database backup
make backup

# Production readiness check
./scripts/production_readiness_check.sh
```

## Architecture Rules

- **API is the gateway** — Frontend and Telegram bot only talk to FastAPI; never directly to scanner/oracle gRPC.
- **Proto contracts are source of truth** — scanner.proto and oracle.proto define all service interfaces. Generate client/server code from these.
- **Scoring consistency** — Rust scanner and Python Oracle must produce identical scores for the same input. Shared test vectors required.
- **V3 engines are portable** — fc60.py, numerology.py, oracle.py, timing_advisor.py are pure computation and copy directly into Oracle service.
- **Environment over config files** — V4 uses environment variables (`.env`), not `config.json`.
- **AES-256-GCM for encryption** — V4 uses `ENC4:` prefix. V3 `ENC:` decrypt is kept as legacy fallback for migration.
- **Path resolution uses `__file__`** — Python code uses `Path(__file__).resolve().parents[N]` for relative paths. No hardcoded directory names.

## Code Standards

- Python 3.11+ for API and Oracle service
- TypeScript strict mode for frontend
- Rust stable for scanner service
- All new modules need corresponding test files
- Use `pathlib.Path` for file paths in Python
- Use environment variables for configuration (never config files)

## Testing

- **API tests:** `api/tests/` — pytest, runnable without external services (SQLite fallback)
- **Integration tests:** `integration/tests/` — 56+ tests across 7 files (requires running API + DB)
- **Browser E2E:** `frontend/e2e/` — Playwright (8 scenarios)
- **DevOps tests:** `devops/tests/` — pytest (28+ tests)
- **Performance audit:** `integration/scripts/perf_audit.py`
- **Security audit:** `integration/scripts/security_audit.py`

## Git Workflow

- `.gitignore` covers Python, Node.js, Rust, Docker, and runtime data
- Key gitignored paths: `.env`, `api/data/`, `node_modules/`, `services/scanner/target/`, `.archive/v2/`
- Remote: `https://github.com/DaveXRouz/BTC.git`

## Phase Status

| Phase | Description                                  | Status           |
| ----- | -------------------------------------------- | ---------------- |
| 0a    | Full scaffolding (93 files)                  | Done             |
| 0b    | V3 file migration + documentation (45 files) | Done             |
| 1     | Foundation (DB + API skeleton + encryption)  | Done             |
| 2     | Python Oracle service                        | Done             |
| 3     | API layer (all endpoints)                    | Partial (Oracle) |
| 4     | Rust scanner                                 | Not started      |
| 5     | React frontend                               | Partial (Oracle) |
| 6     | Infrastructure + DevOps                      | Partial          |
| 7     | Integration testing + polish                 | Partial          |
