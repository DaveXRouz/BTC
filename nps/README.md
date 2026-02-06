# NPS — Numerology Puzzle Solver

A desktop puzzle-solving app that combines **numerology** (FC60 + Pythagorean + Chinese Calendar + Lunar) with **mathematical analysis** to explore and solve puzzles.

## Quick Start

```
python main.py
```

**Requirements:** Python 3.8+ with tkinter (included on Windows/Mac).

Ubuntu/Debian — if tkinter is missing:
```
sudo apt install python3-tk
```

## Features

| Tab | What It Does |
|-----|-------------|
| **Dashboard** | Current moment FC60 reading, solve stats, learning engine status |
| **BTC Hunter** | Bitcoin puzzle solver with 3 strategies (Lightning/Mystic/Hybrid) |
| **Number Oracle** | Predict next number in a sequence using math + FC60 patterns |
| **Name Cipher** | Full numerology profile from name + birthday |
| **Date Decoder** | FC60 analysis of dates + pattern detection + prediction |
| **Validation** | Honest dashboard showing whether scoring actually helps |

## How It Works

1. Every puzzle candidate gets translated into FC60 symbolic tokens (animals + elements)
2. A hybrid scoring engine rates each candidate on math patterns + numerology + learned history
3. Solvers try the highest-scored candidates first
4. A learning engine tracks what works and adjusts weights over time
5. A validation dashboard honestly shows whether scoring improves results

## Project Structure

```
nps/
├── main.py                # Launch the app
├── engines/               # Core computation (FC60, numerology, math, scoring, learning)
├── solvers/               # Puzzle solvers (BTC, number, name, date)
├── gui/                   # Tkinter interface (tabs, widgets, theme)
├── data/                  # JSON storage (created automatically)
├── tests/                 # Test suite
├── BLUEPRINT.md           # Full technical specification
└── README.md              # This file
```

## Running Tests

```
python -m unittest discover tests/ -v
```

## Credits

- FC60 specification by Dave (FC60-v2.0, 2026)
- Pythagorean numerology system (ancient, adapted)
- Bitcoin Puzzle by anonymous (2015)
- Pollard's Kangaroo by John Pollard (1978)
- secp256k1 curve by Certicom Research
