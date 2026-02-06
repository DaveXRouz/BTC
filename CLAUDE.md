# CLAUDE.md — Project Instructions for Claude Code

## Project Overview

NPS (Numerology Puzzle Solver) is a Python/tkinter desktop app that combines FC60 numerology with mathematical analysis for puzzle solving. Supports GUI and headless modes, multi-chain scanning, Telegram notifications, and BIP39 seed generation.

## Repository Layout

- `nps/` — The application (entry point: `main.py`)
- `nps/engines/` — Core computation (FC60, numerology, math, scoring, learning, AI, scanner_brain)
- `nps/solvers/` — Puzzle solvers (BTC, number, name, date, scanner)
- `nps/gui/` — Tkinter interface (4-tab V2 layout)
- `nps/tests/` — Test suite (18 test files)
- `nps/data/` — Runtime JSON data (gitignored)
- `docs/` — Architecture specs (BLUEPRINT.md, UPDATE_V1.md, UPDATE_V2.md)
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
- **Engines are stateless computation** — no GUI imports, no direct file I/O. Data flows through solvers.
- **Solvers orchestrate** — they call engines, read/write data/, and expose results to GUI.
- **GUI tabs are independent** — each tab file handles its own layout and callbacks.
- **config.json** in `nps/` holds all runtime configuration (API keys, chain settings, Telegram).

## Code Standards

- Python 3.8+ compatible
- No external dependencies beyond stdlib + those in `requirements.txt`
- All new engines need a corresponding `tests/test_<name>.py`
- Tests must pass with `unittest` — no pytest dependency required
- Use `pathlib.Path` for file paths inside the app

## Testing

Tests live in `nps/tests/`. Each engine and solver has its own test file. Tests should be runnable without network access or API keys (mock external calls).

## Git Workflow

- Root `.gitignore` excludes `nps/data/`, `__pycache__/`, `.pytest_cache/`, `.claude/`, `archive/nps_old/`
- `nps/.gitignore` additionally excludes `data/` and `__pycache__/` at the app level
- Deployment files (`Procfile`, `railway.toml`) stay inside `nps/`
- Remote: `https://github.com/DaveXRouz/BTC.git`
