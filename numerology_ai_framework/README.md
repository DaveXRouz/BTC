# FC60 Numerology AI Framework

**Complete Modular System for AI-Powered Numerological Analysis**

Version: 2.0.0
Created: 2026-02-09
License: CC0 1.0 Universal (Public Domain)

---

## OVERVIEW

This framework enables AI models to perform comprehensive numerological and astrological analyses with 95%+ confidence. It combines:

- **FC60 Encoding** - Base-60 date/time system using Chinese zodiac tokens
- **Dual Numerology** - Pythagorean + Chaldean calculations
- **Julian Date Engine** - Astronomical-grade date arithmetic
- **Lunar Phase Calculator** - Synodic month approximation
- **Ganzhi Cycle** - Chinese sexagenary (60-year/day/hour) cycles
- **Heartbeat Estimation** - Age-based BPM and lifetime beat calculations
- **Location Encoding** - Coordinate-to-element mapping
- **Pattern Detection** - Automatic identification of significant themes
- **Confidence Scoring** - Grounded reliability metrics (50-95%)

---

## ARCHITECTURE

```
numerology_ai_framework/
├── core/                  # Tier 1: Fundamental calculations
│   ├── julian_date_engine.py      # JDN ↔ Gregorian conversion
│   ├── base60_codec.py            # TOKEN60 encoding/decoding (60 tokens)
│   ├── weekday_calculator.py      # Planetary day associations
│   ├── checksum_validator.py      # Weighted error detection (CHK)
│   └── fc60_stamp_engine.py       # Complete Mode A pipeline (11 steps)
│
├── personal/              # Tier 2: Individual analysis
│   ├── numerology_engine.py       # Life Path, Expression, Soul Urge, etc.
│   └── heartbeat_engine.py        # BPM estimation, lifetime beats
│
├── universal/             # Tier 3: Cosmic cycles
│   ├── moon_engine.py             # Lunar phase from JDN
│   ├── ganzhi_engine.py           # Sexagenary cycle (year/day/hour)
│   └── location_engine.py         # Coordinate → element encoding
│
├── synthesis/             # Tier 4: Integration layer
│   ├── reading_engine.py          # Signal hierarchy and reading generation
│   ├── signal_combiner.py         # Planet×Moon, LP×PY, animal harmony logic
│   ├── universe_translator.py     # 9-section human-readable output
│   └── master_orchestrator.py     # Main AI interface (10-step pipeline)
│
├── logic/                 # Documentation layer for AI interpretation
│   ├── 00_MASTER_SYSTEM_PROMPT.md # Start here — system overview and rules
│   ├── 01_INPUT_COLLECTION_GUIDE.md # 6 input dimensions, conversation flow
│   ├── 02_CALCULATION_REFERENCE.md  # All formulas, tables, test vectors
│   ├── 03_INTERPRETATION_BIBLE.md   # Numbers → meaning (3,200+ lines)
│   ├── 04_READING_COMPOSITION_GUIDE.md # Tone, structure, example readings
│   ├── 05_ERROR_HANDLING_AND_EDGE_CASES.md # Edge cases and validation
│   └── 06_API_INTEGRATION_TEMPLATE.md # JSON schemas, Flask/FastAPI templates
│
├── tests/
│   ├── test_all.py                # Original suite (123 tests)
│   ├── test_synthesis_deep.py     # Signal combiner + descriptions (50 tests)
│   └── test_integration.py        # End-to-end integration (7 tests)
│
├── CLAUDE.md              # Project instructions for AI assistants
├── PROJECT_INSTRUCTIONS.md # Quick entry point for any project
├── INTEGRATION_GUIDE.md   # Quick usage examples (see logic/06 for full guide)
└── example_usage.py       # Full demo with all 7 input dimensions
```

---

## QUICK START

### Installation

```bash
# No external dependencies - pure Python stdlib
cd numerology_ai_framework
python3 example_usage.py        # Full demo
python3 tests/test_all.py       # Run all tests
```

### Basic Usage

```python
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime

# Minimal reading (name + birthdate)
reading = MasterOrchestrator.generate_reading(
    full_name="John Smith",
    birth_day=15,
    birth_month=7,
    birth_year=1990,
    current_date=datetime(2026, 2, 9),
)

print(f"Life Path: {reading['numerology']['life_path']['number']}")
print(f"Confidence: {reading['confidence']['score']}%")
print(f"\n{reading['synthesis']}")
```

### Full Reading (all 7 input dimensions)

```python
reading = MasterOrchestrator.generate_reading(
    full_name="Alice Johnson",
    birth_day=15, birth_month=7, birth_year=1990,
    current_date=datetime(2026, 2, 9),
    mother_name="Barbara Johnson",
    gender="female",
    latitude=40.7, longitude=-74.0,
    actual_bpm=68,
    current_hour=14, current_minute=30, current_second=0,
    tz_hours=-5, tz_minutes=0,
    numerology_system="pythagorean",
)
```

### Stamp-Only Mode

```python
stamp = MasterOrchestrator.generate_reading(
    full_name="", birth_day=1, birth_month=1, birth_year=2000,
    current_date=datetime(2026, 2, 9),
    current_hour=14, current_minute=30, current_second=0,
    mode="stamp_only",
)
print(f"FC60: {stamp['fc60_stamp']['fc60']}")
```

---

## KEY FEATURES

### 1. Deterministic Core

- Every calculation is reproducible
- Same input → Same output (always)
- No randomness, no guessing

### 2. Universal Address System (FC60)

- Every moment encoded as a unique base-60 stamp
- Format: `WD-MO-DOM HALF+HOUR-MINUTE-SECOND`
- Example: `VE-OX-OXFI ☀OX-RUWU-RAWU`
- 60 tokens = 12 animals × 5 elements

### 3. Multi-System Analysis

- **Pythagorean Numerology** (A=1, B=2, ...)
- **Chaldean Numerology** (ancient system, no 9)
- **FC60 Base-60** (Chinese zodiac encoding)
- **Lunar Phase** (synodic month approximation)
- **Ganzhi Cycle** (10 stems × 12 branches)

### 4. Signal Hierarchy (from §12)

1. Repeated animals (3+) → Very High priority
2. Repeated animals (2) → High
3. Day planet → Medium
4. Moon phase → Medium
5. DOM token → Medium
6. Hour animal → Low-Medium

### 5. Confidence Scoring

- 50-95% range based on data completeness
- Base 50% + increments per data source
- Never claims 100% — capped at 95%

---

## NUMEROLOGY NUMBERS EXPLAINED

### Core Numbers

| Number         | Name                | Calculated From                | Meaning              |
| -------------- | ------------------- | ------------------------------ | -------------------- |
| Life Path      | Your soul's purpose | Birthdate (day+month+year)     | Core mission in life |
| Expression     | Your potential      | Full name (all letters)        | How you manifest     |
| Soul Urge      | Inner desire        | Vowels in name                 | What you truly want  |
| Personality    | Outer self          | Consonants in name             | How others see you   |
| Personal Year  | Annual theme        | Birth month+day + current year | This year's focus    |
| Personal Month | Monthly theme       | Personal Year + current month  | This month's focus   |
| Personal Day   | Daily theme         | Personal Month + current day   | Today's focus        |

### Master Numbers

**11, 22, 33** - Never reduced. Heightened spiritual potential.

- **11** - The Visionary: Intuition, illumination, inspiration
- **22** - The Master Builder: Turning dreams into reality
- **33** - The Master Teacher: Compassionate healing leadership

---

## VALIDATION & TESTING

```bash
# Full test suites
python3 tests/test_all.py               # Original suite (123 tests)
python3 tests/test_synthesis_deep.py     # Signal combiner + descriptions (50 tests)
python3 tests/test_integration.py        # End-to-end integration (7 tests)

# Individual module self-tests
python3 core/julian_date_engine.py        # 27 passed
python3 core/base60_codec.py              # 27 passed
python3 core/weekday_calculator.py        # 4 passed
python3 core/checksum_validator.py        # 4 passed
python3 core/fc60_stamp_engine.py         # 12+ passed
python3 personal/numerology_engine.py     # 6 passed
python3 personal/heartbeat_engine.py      # 8 passed
python3 universal/moon_engine.py          # 5 passed
python3 universal/ganzhi_engine.py        # 8 passed
python3 universal/location_engine.py      # 6 passed
python3 synthesis/reading_engine.py       # 4 passed
python3 synthesis/universe_translator.py  # 4 passed
python3 synthesis/signal_combiner.py      # 10 passed

# End-to-end demo
python3 synthesis/master_orchestrator.py  # Full demo
python3 example_usage.py                  # 4 examples
```

---

## FOR AI MODELS: START HERE

For comprehensive integration guidance, read the `logic/` folder in order:

1. `logic/00_MASTER_SYSTEM_PROMPT.md` — System overview, rules, file map
2. `logic/01_INPUT_COLLECTION_GUIDE.md` — What to ask users, in what order
3. `logic/02_CALCULATION_REFERENCE.md` — All formulas and test vectors
4. `logic/03_INTERPRETATION_BIBLE.md` — Numbers → meaning (the richest file)
5. `logic/04_READING_COMPOSITION_GUIDE.md` — Tone, structure, example readings
6. `logic/05_ERROR_HANDLING_AND_EDGE_CASES.md` — Edge cases and validation
7. `logic/06_API_INTEGRATION_TEMPLATE.md` — JSON schemas, code templates

## HOW TO DROP THIS INTO ANY PROJECT

```bash
# 1. Copy the folder
cp -r numerology_ai_framework/ /path/to/your/project/

# 2. No install needed — zero dependencies, pure Python 3.6+ stdlib

# 3. Use it
python3 -c "
import sys; sys.path.append('/path/to/your/project/numerology_ai_framework')
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime
reading = MasterOrchestrator.generate_reading(
    full_name='Test', birth_day=1, birth_month=1, birth_year=2000,
    current_date=datetime.now())
print(reading['synthesis'])
"
```

## QUICK REFERENCE: HOW TO USE THIS FRAMEWORK

### Step 1: Gather Data

Minimum required:

- Full name (first + last)
- Birthdate (day, month, year)

Optional (increases confidence):

- Mother's full name (+10%)
- Gender (+polarity data)
- Geographic coordinates (+5%)
- Actual heart rate (+5%)
- Current exact time (+5%)
- Timezone offset

### Step 2: Call Master Orchestrator

```python
reading = MasterOrchestrator.generate_reading(
    full_name=user_input['name'],
    birth_day=user_input['day'],
    birth_month=user_input['month'],
    birth_year=user_input['year'],
    mother_name=user_input.get('mother_name'),
    gender=user_input.get('gender'),
    latitude=user_input.get('latitude'),
    longitude=user_input.get('longitude'),
    actual_bpm=user_input.get('bpm'),
    current_hour=user_input.get('hour'),
    current_minute=user_input.get('minute'),
    current_second=user_input.get('second'),
    tz_hours=user_input.get('tz_hours', 0),
    tz_minutes=user_input.get('tz_minutes', 0),
)
```

### Step 3: Use Results

- `reading['synthesis']` — Full human-readable output
- `reading['confidence']` — Score and level
- `reading['patterns']` — Detected patterns
- `reading['numerology']` — All numerology numbers
- `reading['fc60_stamp']` — Universal address
- `reading['moon']` — Lunar phase data
- `reading['ganzhi']` — Sexagenary cycle data
- `reading['heartbeat']` — Heart rhythm data
- `reading['location']` — Location encoding

---

## TECHNICAL SPECIFICATIONS

### Requirements

- Python 3.6+
- No external dependencies
- ~100KB total size

### Performance

- All calculations: O(1) or O(log n)
- Complete reading generation: <10ms on modern hardware
- Memory footprint: <1MB

### Compatibility

- Works as standalone package
- Works in restricted environments (no network needed)
- Thread-safe (pure functions)
- Compatible with all major AI model architectures

---

## LIMITATIONS & DISCLAIMERS

### What This Framework CAN Do

- Calculate numerology numbers with 100% mathematical accuracy
- Detect patterns and repetitions across multiple systems
- Provide confidence scores for readings
- Generate structured, grounded interpretations

### What This Framework CANNOT Do

- Predict specific future events
- Override free will or personal choice
- Replace professional advice (medical, legal, financial)
- Guarantee outcomes

---

## LICENSE

CC0 1.0 Universal (Public Domain)

You can copy, modify, distribute and perform the work, even for commercial
purposes, all without asking permission.

---

**Built for AI. Powered by mathematics. Grounded in tradition.**
