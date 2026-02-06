# NPS — Numerology Puzzle Solver

A Python/Tkinter desktop application that combines **FC60 numerology**, **Pythagorean analysis**, **Chinese Calendar cycles**, and **mathematical pattern detection** to explore and solve puzzles. Features encryption at rest, findings vault, multi-chain cryptocurrency scanning (BTC, ETH, BSC, Polygon), adaptive AI learning with levels, multi-terminal dashboard, Telegram remote control, BIP39 seed generation, and headless deployment.

**Zero external dependencies** — runs on Python 3.8+ standard library only.

---

## Quick Start

```bash
# Verify environment
bash scripts/setup.sh

# Launch GUI
cd nps && python3 main.py

# Launch headless (server/cloud)
cd nps && python3 main.py --headless
```

**Requirements:** Python 3.8+ with tkinter (included on Windows/macOS).

Ubuntu/Debian — if tkinter is missing:

```bash
sudo apt install python3-tk
```

---

## Features

### 5-Tab Interface

| Tab           | Purpose                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------- |
| **Dashboard** | Multi-terminal command center — terminal cards, health dots, daily insight, vault quick view |
| **Hunter**    | Unified scanner controls — random keys, seed phrases, or both + puzzle toggle + checkpoints  |
| **Oracle**    | Question mode + name cipher + daily insights with FC60 meanings                              |
| **Memory**    | AI learning center — XP/levels, insights, recommendations, Learn Now                         |
| **Settings**  | Telegram config, security status, scanner defaults, deployment, reset                        |

### Multi-Chain Scanner

- **Bitcoin** — Random key generation with balance checking via Blockstream API
- **Ethereum** — Address scanning with ERC-20 token support (USDT, USDC, DAI, WBTC, WETH, UNI, LINK, SHIB)
- **BSC** — Binance Smart Chain scanning
- **Polygon** — Polygon network scanning
- **BIP39** — Seed phrase generation and derivation
- **Modes** — Random keys, seed phrases, or both
- **Checkpoints** — Resume scanning after crashes

### Encryption at Rest

- PBKDF2 key derivation (600K iterations, SHA-256)
- HMAC-SHA256 stream cipher for sensitive data
- `encrypt_dict` / `decrypt_dict` for vault records
- Environment variable override (`NPS_MASTER_PASSWORD`, `NPS_BOT_TOKEN`, `NPS_CHAT_ID`)

### Findings Vault

- Append-only JSONL storage with encrypted sensitive fields
- Per-session tracking with auto-summaries
- CSV and JSON export
- Thread-safe writes with atomic file operations

### AI Learning System

- 5 levels: Novice → Student → Apprentice → Expert → Master
- XP earned from scanning sessions
- Claude CLI integration for session analysis
- Auto-parameter adjustment at Level 4+
- Persistent state across sessions

### Multi-Terminal Dashboard

- Up to 10 concurrent scan terminals
- Per-terminal health monitoring
- Endpoint health dots (blockstream, ETH RPC, BSC, Polygon)

### Puzzle-Solving Strategies

- **Lightning** — Pure brute force with minimal overhead
- **Mystic** — Score candidates first, explore high-scoring regions
- **Hybrid** — Combines scoring with Pollard's Kangaroo algorithm
- **Oracle** — AI-guided candidate selection via Claude CLI

### Adaptive Learning

- Records every puzzle attempt with full scoring breakdown
- Tracks correlation between scoring factors and actual success
- Dynamically adjusts weights to emphasize predictive factors
- Validates improvement through confidence score progression

### Telegram Integration

Remote control and notifications via Telegram bot:

| Command              | Action                   |
| -------------------- | ------------------------ |
| `/status`            | Show active solver stats |
| `/pause` / `/resume` | Pause or resume scanning |
| `/stop`              | Stop all solvers         |
| `/sign <text>`       | Oracle sign reading      |
| `/name <name>`       | Name numerology          |
| `/memory`            | Memory stats             |
| `/perf`              | Performance profiling    |
| `/daily`             | Daily insight            |
| `/vault`             | Vault summary            |

---

## How It Works

1. Every puzzle candidate gets translated into **FC60 symbolic tokens** (12 animals x 5 elements)
2. A **hybrid scoring engine** rates each candidate:
   - Math score (40%) — entropy, digit balance, primality, palindromes, mod-60 patterns
   - Numerology score (30%) — master numbers, element balance, life path, moon alignment
   - Learned score (30%) — adaptive weights from solve history
3. Solvers try the **highest-scored candidates first**
4. A **learning engine** tracks what works and adjusts weights over time
5. A **validation dashboard** honestly shows whether scoring improves results

---

## Project Structure

```
BTC/
├── README.md                 # This file
├── CLAUDE.md                 # Claude Code project instructions
├── docs/
│   ├── BLUEPRINT.md          # Complete technical specification
│   ├── UPDATE_V1.md          # V1 additions and QA
│   ├── UPDATE_V2.md          # V2 restructuring (7 → 4 tabs)
│   └── CHANGELOG.md          # Version history
├── nps/                      # The application
│   ├── main.py               # Entry point (GUI + headless)
│   ├── config.json           # Runtime configuration
│   ├── engines/              # Core computation (23 modules)
│   │   ├── fc60.py           # FrankenChron-60 encoding
│   │   ├── numerology.py     # Pythagorean numerology
│   │   ├── scoring.py        # Hybrid scoring engine
│   │   ├── learning.py       # Adaptive weight adjustment
│   │   ├── learner.py        # XP/Level AI learning (5 levels)
│   │   ├── security.py       # Encryption at rest (PBKDF2+HMAC)
│   │   ├── vault.py          # Findings vault (JSONL, encrypted)
│   │   ├── session_manager.py # Session tracking
│   │   ├── terminal_manager.py # Multi-terminal (max 10)
│   │   ├── health.py         # Endpoint health monitoring
│   │   ├── memory.py         # Session caching
│   │   ├── scanner_brain.py  # Adaptive strategy selection
│   │   ├── ai_engine.py      # Claude CLI integration
│   │   ├── crypto.py         # secp256k1, Pollard's Kangaroo
│   │   ├── bip39.py          # BIP39 mnemonic generation
│   │   ├── balance.py        # Multi-chain balance checking
│   │   ├── oracle.py         # Sign reader + daily insight
│   │   ├── notifier.py       # Telegram integration
│   │   ├── math_analysis.py  # Entropy, primes, digit patterns
│   │   ├── keccak.py         # Keccak-256 (Ethereum)
│   │   ├── config.py         # Config loader with env var support
│   │   └── perf.py           # Performance profiler
│   ├── solvers/              # Puzzle solvers (7 modules)
│   │   ├── base_solver.py    # Abstract base with threading
│   │   ├── unified_solver.py # V3 unified hunter (3 modes)
│   │   ├── btc_solver.py     # 4 Bitcoin strategies
│   │   ├── scanner_solver.py # Multi-chain scanner
│   │   ├── number_solver.py  # Sequence prediction
│   │   ├── name_solver.py    # Name numerology
│   │   └── date_solver.py    # Date analysis
│   ├── gui/                  # Tkinter interface (8 modules)
│   │   ├── dashboard_tab.py  # Multi-terminal command center
│   │   ├── hunter_tab.py     # Unified scanner controls
│   │   ├── oracle_tab.py     # Question mode + name cipher
│   │   ├── memory_tab.py     # AI learning center
│   │   ├── settings_tab.py   # Settings & connections
│   │   ├── widgets.py        # Custom components
│   │   └── theme.py          # Dark theme
│   ├── tests/                # Test suite (25 files, 238 tests)
│   └── data/                 # Runtime JSON data (gitignored)
├── scripts/
│   └── setup.sh              # Environment verification
└── archive/                  # Old versions (read-only)
```

---

## Architecture

```
┌──────────────────────────────────────────────┐
│  GUI Layer — Tkinter (5 tabs + theme)        │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Solver Layer — Orchestration + threading     │
│  (Unified, BTC, Scanner, Number, Name, Date) │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Engine Layer — Computation + services        │
│  (FC60, Scoring, Learning, Crypto, BIP39,    │
│   Balance, Oracle, AI, Notifier, Security,   │
│   Vault, Learner, Health, Session Manager)   │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│  Data Layer — Encrypted persistence           │
│  (vault JSONL, sessions, checkpoints,        │
│   learning state, config.json)               │
└──────────────────────────────────────────────┘
```

**Principles:**

- Engines are **stateless computation** (exceptions: vault, session_manager, learner manage own files)
- Solvers **orchestrate** — call engines, manage data, expose results via callbacks
- GUI tabs are **independent** — each handles its own layout and state
- All services **degrade gracefully** — works without Telegram, AI, or network
- **Security first** — sensitive data encrypted at rest, env var overrides for secrets
- **Thread safety** — shared mutable state protected with `threading.Lock`, atomic file writes

---

## Running Tests

```bash
# All tests
cd nps && python3 -m unittest discover tests/ -v

# Single test
cd nps && python3 -m unittest tests/test_fc60.py -v
```

25 test files, 238 tests covering all engines and solvers. Tests run without network access or API keys.

---

## Deployment

### Headless Mode

```bash
cd nps && python3 main.py --headless
```

Runs without GUI — controlled via Telegram bot commands. Ideal for servers and cloud.

### Railway

Deployment files (`Procfile`, `railway.toml`) are inside `nps/`.

---

## Configuration

All settings live in `nps/config.json`:

- **telegram** — Bot token, chat ID, enable/disable
- **balance_check** — RPC endpoints (BTC, ETH, BSC, Polygon), token list, rate limits
- **scanner** — Chains, batch size, thread count, addresses per seed
- **headless** — Auto-start, scanner mode, status intervals
- **oracle** — Reading history max
- **memory** — Flush interval, max size (10 MB)
- **performance** — GUI refresh rates

---

## Credits

- FC60 specification by Dave (FC60-v2.0, 2026)
- Pythagorean numerology system (ancient, adapted)
- Bitcoin Puzzle by anonymous (2015)
- Pollard's Kangaroo by John Pollard (1978)
- secp256k1 curve by Certicom Research
