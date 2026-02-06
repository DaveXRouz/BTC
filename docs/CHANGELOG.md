# Changelog

All notable changes to NPS are documented here. Derived from the original git history (16 commits on `main`).

## 2026-02-06

### V2 Architecture + Scanner Brain

- `22f5005` Add adaptive ScannerBrain with persistent learning and AI-guided strategies

### Scanner Live Feed Improvements

- `1acac53` Show $0 instead of dash in Balance column, include tx history
- `0d1cc94` Add Balance column to scanner live feed
- `eb869b1` Show key/seed, dynamic columns, and token data in scanner live feed
- `757c26d` Fix scanner live feed empty addresses and add multi-chain selection

### V2 Overhaul

- `776c263` **NPS V2: Architecture overhaul** — 7 tabs to 4, new engines, performance
- `57d2169` Fix hunter_tab padx tuple in Label constructor

### Bug Fixes & Testing

- `1b26eae` Fix deep inspection test gaps: balance API keys, GUI theming, scanner timing

### Telegram Integration

- `3b97a4a` Fix Telegram bot responsiveness: add GUI polling, async callbacks
- `5731e38` Configure Telegram bot and fix SSL for macOS Python

### V1 Update

- `a34204e` Merge remote main with local Update V1 (keep local versions)
- `ddf4821` Update V1: QA sweep, polish, and intelligence enhancements

### Initial Release

- `9440a53` NPS — Numerology Puzzle Solver with Multi-Chain Scanner
- `b62e652` Add multi-chain scanner, Telegram notifications, BIP39/BIP32, headless mode
- `f87c845` Initial commit
- `c0d71f2` Fix 9 incorrect puzzle addresses and add speed/operations to solver callbacks

## 2026-02-07

### NPS V3 — Full Architecture Upgrade

- **Encryption at rest** — PBKDF2 + HMAC-SHA256 stream cipher via `engines/security.py`
- **Findings vault** — Append-only JSONL with encrypted sensitive fields, CSV/JSON export
- **Unified scanner** — 3 modes (random_key, seed_phrase, both), 4 chains (BTC, ETH, BSC, Polygon), checkpoints
- **Human-readable oracle** — `daily_insight()`, `question_sign()` with FC60 meanings
- **AI learning system** — XP/levels (Novice→Master), session insights, auto-adjustments at Level 4+
- **Multi-terminal dashboard** — Up to 10 concurrent scan terminals with health monitoring
- **5-tab GUI** — Dashboard, Hunter, Oracle, Memory, Settings
- **Settings hub** — Telegram config, security status, scanner defaults, reset to defaults
- **Thread safety audit** — All shared mutable state protected with `threading.Lock`
- **Atomic writes** — All critical data files use `.tmp` + `os.replace`
- **25 test files, 238 tests** — Full coverage of all V3 engines and solvers

### Project Reorganization

- Reorganized repository: `BTC/` renamed to `nps/`, old `nps/` archived
- Added `docs/`, `scripts/`, `archive/` directories
- Created root README.md, CLAUDE.md, .gitignore
- Merged unique data files from old nps/ into canonical app
- Preserved original git history in `archive/BTC_git_history.bundle`
