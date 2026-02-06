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
  - `config.py` — Config management with env var support
  - `notifier.py` — Telegram notifications + command dispatch
  - `balance.py` — Multi-chain balance checking (BTC, ETH, BSC, Polygon)
  - `oracle.py` — Oracle readings, question signs, daily insights
  - `memory.py` — Legacy memory system
  - `perf.py` — Performance timing
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
  - `theme.py`, `widgets.py` — Shared UI components
- `nps/tests/` — Test suite (25 test files, 238 tests)
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

## Code Standards

- Python 3.8+ compatible
- No external dependencies beyond stdlib + those in `requirements.txt`
- All new engines need a corresponding `tests/test_<name>.py`
- Tests must pass with `unittest` — no pytest dependency required
- Use `pathlib.Path` for file paths inside the app
- Use `numerology_reduce` (not `reduce`) from `engines/numerology.py`

## Testing

Tests live in `nps/tests/`. Each engine and solver has its own test file. Tests should be runnable without network access or API keys (mock external calls). Current: 238 tests across 19 files.

## Git Workflow

- Root `.gitignore` excludes `nps/data/`, `__pycache__/`, `.pytest_cache/`, `.claude/`, `archive/nps_old/`
- `nps/.gitignore` additionally excludes `data/` and `__pycache__/` at the app level
- Deployment files (`Procfile`, `railway.toml`) stay inside `nps/`
- Remote: `https://github.com/DaveXRouz/BTC.git`
