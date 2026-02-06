# NPS — Numerology Puzzle Solver

A desktop application that combines **numerology** (FC60 + Pythagorean + Chinese Calendar + Lunar) with **mathematical analysis** to explore and solve puzzles. Features multi-chain scanning, Telegram notifications, BIP39 seed generation, and headless mode.

## Quick Start

```bash
# Verify environment
bash scripts/setup.sh

# Launch GUI
cd nps && python3 main.py

# Launch headless
cd nps && python3 main.py --headless
```

**Requirements:** Python 3.8+ with tkinter (included on Windows/Mac).

Ubuntu/Debian — if tkinter is missing:

```bash
sudo apt install python3-tk
```

## Project Structure

```
BTC/
├── README.md              # This file
├── CLAUDE.md              # Claude Code project instructions
├── .gitignore             # Python + project-specific ignores
├── docs/
│   ├── BLUEPRINT.md       # Original architecture specification
│   ├── UPDATE_V1.md       # V1 additions and QA sweep
│   ├── UPDATE_V2.md       # V2 restructuring (7 tabs → 4)
│   └── CHANGELOG.md       # Version history
├── nps/                   # The application
│   ├── main.py            # Entry point (GUI + headless)
│   ├── config.json        # App configuration
│   ├── engines/           # Core computation (17 modules)
│   ├── solvers/           # Puzzle solvers (7 modules)
│   ├── gui/               # Tkinter interface (8 modules)
│   ├── tools/             # Utilities
│   ├── data/              # Runtime data (gitignored)
│   └── tests/             # Test suite (18 files)
├── scripts/
│   └── setup.sh           # Environment verification
└── archive/               # Old versions (read-only reference)
    ├── v1_source/         # Legacy V1 code
    ├── nps_old/           # Previous nps/ copy (not tracked)
    └── BTC_git_history.bundle  # Git bundle of original commits
```

## Running Tests

```bash
cd nps && python3 -m unittest discover tests/ -v
```

## Features

| Tab               | What It Does                                                      |
| ----------------- | ----------------------------------------------------------------- |
| **Dashboard**     | Current moment FC60 reading, solve stats, learning engine status  |
| **BTC Hunter**    | Bitcoin puzzle solver with 3 strategies (Lightning/Mystic/Hybrid) |
| **Number Oracle** | Predict next number in a sequence using math + FC60 patterns      |
| **Name Cipher**   | Full numerology profile from name + birthday                      |

## How It Works

1. Every puzzle candidate gets translated into FC60 symbolic tokens (animals + elements)
2. A hybrid scoring engine rates each candidate on math patterns + numerology + learned history
3. Solvers try the highest-scored candidates first
4. A learning engine tracks what works and adjusts weights over time
5. A validation dashboard honestly shows whether scoring improves results

## Deployment

Railway deployment files (`Procfile`, `railway.toml`) live inside `nps/` alongside `main.py`.

## Credits

- FC60 specification by Dave (FC60-v2.0, 2026)
- Pythagorean numerology system (ancient, adapted)
- Bitcoin Puzzle by anonymous (2015)
- Pollard's Kangaroo by John Pollard (1978)
- secp256k1 curve by Certicom Research
