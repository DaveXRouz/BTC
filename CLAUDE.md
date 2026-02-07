# CLAUDE.md — Project Instructions for Claude Code

## Project Overview

NPS (Numerology Puzzle Solver) V3 is a Python/tkinter desktop app that combines FC60 numerology with mathematical analysis for puzzle solving. Features: encryption at rest, findings vault, unified multi-chain scanner with checkpoints, human-readable oracle, active AI learning with levels, multi-terminal dashboard, settings hub, and expanded Telegram commands. Supports GUI and headless modes.

## Repository Layout

- `nps/` — The application (entry point: `main.py`)
- `nps/engines/` — Core computation and services
  - `fc60.py`, `numerology.py`, `math_analysis.py`, `scoring.py` — Pure computation
  - `learning.py`, `ai_engine.py`, `scanner_brain.py` — AI/ML learning
  - `security.py` — Encryption at rest (PBKDF2 + HMAC-SHA256)
  - `vault.py` — Findings vault (JSONL, encrypted sensitive fields)
  - `learner.py` — XP/Level AI learning system (5 levels)
  - `session_manager.py` — Session tracking and archival
  - `terminal_manager.py` — Multi-terminal orchestration (max 10)
  - `health.py` — Endpoint health monitoring
  - `config.py` — Config management with env var support + validation
  - `notifier.py` — Telegram bot (25+ commands, inline keyboards, rate limiting)
  - `balance.py` — Multi-chain balance checking (BTC, ETH, BSC, Polygon)
  - `oracle.py` — Oracle readings, question signs, daily insights
  - `events.py` — Thread-safe pub/sub event bus with GUI-safe callbacks
  - `logger.py` — Centralized logging with RotatingFileHandler + Telegram error handler
  - `errors.py` — Result class, @safe_callback decorator, safe_file_read
  - `memory.py` — Legacy memory system
  - `perf.py` — Performance timing
- `nps/logic/` — Intelligence layer for smart scanning decisions
  - `strategy_engine.py` — Level-gated strategy brain with timing + range integration
  - `pattern_tracker.py` — Pattern analysis: batch recording, finding analysis, coverage
  - `key_scorer.py` — LRU-cached scoring (10K entries), top-N heap tracking
  - `timing_advisor.py` — Cosmic timing: moon phase, FC60, numerology alignment
  - `range_optimizer.py` — Smart range selection with coverage tracking
  - `history_manager.py` — Throttled atomic persistence for logic data
- `nps/solvers/` — Puzzle solvers
  - `unified_solver.py` — V3 unified hunter (random_key/seed_phrase/both + puzzle toggle + checkpoints)
  - `btc_solver.py`, `scanner_solver.py` — V2 solvers (still functional)
  - `number_solver.py`, `name_solver.py`, `date_solver.py` — Puzzle solvers
- `nps/gui/` — Tkinter interface (5-tab V3 layout)
  - `dashboard_tab.py` — Multi-terminal command center
  - `hunter_tab.py` — Unified scanner controls
  - `oracle_tab.py` — Question mode + name cipher
  - `memory_tab.py` — AI learning center
  - `settings_tab.py` — Telegram config, security, scanner defaults
  - `theme.py`, `widgets.py` — Shared UI components (ToolTip, StyledButton with tooltips)
- `nps/tests/` — Test suite (50 test files, 598 tests)
- `nps/data/` — Runtime data (gitignored)
  - `findings/`, `sessions/`, `learning/`, `checkpoints/`
- `docs/` — Architecture specs
- `archive/` — Old versions, read-only reference
- `scripts/` — Environment setup

## Key Commands

```bash
# Run the app (GUI)
cd nps && python3 main.py

# Run headless
cd nps && python3 main.py --headless

# Run all tests
cd nps && python3 -m unittest discover tests/ -v

# Run a single test
cd nps && python3 -m unittest tests/test_fc60.py -v
```

## Architecture Rules

- **main.py uses `__file__`-relative paths** — the app is self-contained in `nps/`. Do not add sys.path hacks at the root level.
- **Engines are stateless computation** — no GUI imports, no direct file I/O. Data flows through solvers. Exceptions: `vault.py`, `session_manager.py`, `learner.py` manage their own data files.
- **Solvers orchestrate** — they call engines, read/write data/, and expose results to GUI.
- **GUI tabs are independent** — each tab file handles its own layout and callbacks.
- **config.json** in `nps/` holds all runtime configuration (API keys, chain settings, Telegram).
- **Security first** — Sensitive data (private keys, seeds) encrypted via `engines/security.py`. Use `encrypt_dict`/`decrypt_dict` for vault records.
- **Thread safety** — Vault, terminal manager, and learner use `threading.Lock`. Atomic file writes via `.tmp` + `os.replace`.
- **Event bus** — Cross-component communication via `engines/events.py`. Subscribe with `gui_root` for GUI-safe callbacks. Events: `FINDING_FOUND`, `HEALTH_CHANGED`, `LEVEL_UP`, `TERMINAL_STATUS_CHANGED`, `SCAN_STARTED`, `SCAN_STOPPED`, `CHECKPOINT_SAVED`, `CONFIG_CHANGED`, `SHUTDOWN`.
- **Logic layer** — `logic/` modules provide intelligence for scanning decisions. StrategyEngine is level-gated (fixed at L1-2, suggestions at L3+, auto-adjust at L4+).

## Code Standards

- Python 3.8+ compatible
- No external dependencies beyond stdlib + those in `requirements.txt`
- All new engines need a corresponding `tests/test_<name>.py`
- Tests must pass with `unittest` — no pytest dependency required
- Use `pathlib.Path` for file paths inside the app
- Use `numerology_reduce` (not `reduce`) from `engines/numerology.py`

## Testing

Tests live in `nps/tests/`. Each engine and solver has its own test file. Tests should be runnable without network access or API keys (mock external calls). Current: 598 tests across 50 files (361 unit + 237 battle/integration/performance tests). Battle tests use `_battle.py` suffix. 8 Telegram live tests skip automatically without `NPS_BOT_TOKEN`/`NPS_CHAT_ID` env vars.

## Git Workflow

- Root `.gitignore` excludes `nps/data/`, `__pycache__/`, `.pytest_cache/`, `.claude/`, `archive/nps_old/`
- `nps/.gitignore` additionally excludes `data/` and `__pycache__/` at the app level
- Deployment files (`Procfile`, `railway.toml`) stay inside `nps/`
- Remote: `https://github.com/DaveXRouz/BTC.git`

---

## V4 Architecture (In Progress)

V4 is a distributed microservices architecture targeting web deployment. The scaffolding lives in `v4/`.

### V4 Repository Layout

- `v4/frontend/` — React + TypeScript + Tailwind (Vite build)
  - `src/pages/` — 6 pages: Dashboard, Scanner, Oracle, Vault, Learning, Settings
  - `src/components/` — Shared UI components (Layout, StatsCard, LogPanel)
  - `src/services/` — API client (`api.ts`) and WebSocket client (`websocket.ts`)
  - `src/types/` — TypeScript types mirroring API Pydantic models
  - `src/i18n/` — Internationalization (EN, stubs for ES/FR)
- `v4/api/` — FastAPI REST + WebSocket gateway
  - `app/routers/` — 6 routers: health, auth, scanner, oracle, vault, learning
  - `app/models/` — Pydantic request/response schemas
  - `app/middleware/` — Auth (JWT + API keys), rate limiting
  - `app/services/` — WebSocket manager, security (AES-256-GCM + V3 legacy decrypt)
- `v4/services/scanner/` — Rust high-performance scanner (Cargo project)
  - `src/crypto/` — secp256k1, bip39, address derivation
  - `src/scanner/` — Multi-threaded scan loop with checkpoints
  - `src/balance/` — Async balance checking via reqwest
  - `src/scoring/` — Scoring engine (must match Python Oracle weights)
  - `src/grpc/` — gRPC server implementing scanner.proto
- `v4/services/oracle/` — Python Oracle service (gRPC)
  - `oracle_service/engines/` — V3 engines copied as-is: fc60, numerology, oracle
  - `oracle_service/logic/` — V3 logic: timing_advisor, strategy_engine
- `v4/proto/` — Shared protobuf contracts (scanner.proto, oracle.proto)
- `v4/database/` — PostgreSQL schema (`init.sql`) and V3->V4 migration scripts
- `v4/infrastructure/` — Nginx config, Prometheus monitoring
- `v4/scripts/` — deploy.sh, backup.sh, restore.sh, rollback.sh
- `v4/docker-compose.yml` — 7-container orchestration

### V4 Key Commands

```bash
# Start all services
cd v4 && make up

# Development servers
cd v4 && make dev-api      # FastAPI on :8000
cd v4 && make dev-frontend  # Vite on :5173

# Run tests
cd v4 && make test

# Generate gRPC stubs from proto files
cd v4 && make proto

# Database backup
cd v4 && make backup
```

### V4 Architecture Rules

- **API is the gateway** — Frontend and Telegram bot only talk to FastAPI; never directly to scanner/oracle gRPC.
- **Proto contracts are source of truth** — scanner.proto and oracle.proto define all service interfaces. Generate client/server code from these.
- **Scoring consistency** — Rust scanner and Python Oracle must produce identical scores for the same input. Shared test vectors required.
- **V3 engines are portable** — fc60.py, numerology.py, oracle.py, timing_advisor.py are pure computation and copy directly into Oracle service.
- **Environment over config files** — V4 uses environment variables (`.env`), not `config.json`.
- **AES-256-GCM for encryption** — V4 uses `ENC4:` prefix. V3 `ENC:` decrypt is kept as legacy fallback for migration.

### V4 Phase Status

| Phase | Description                                 | Status      |
| ----- | ------------------------------------------- | ----------- |
| 0     | Full scaffolding                            | Done        |
| 1     | Foundation (DB + API skeleton + encryption) | Not started |
| 2     | Python Oracle service                       | Not started |
| 3     | API layer (all endpoints)                   | Not started |
| 4     | Rust scanner                                | Not started |
| 5     | React frontend                              | Not started |
| 6     | Infrastructure + DevOps                     | Not started |
| 7     | Integration testing + polish                | Not started |
