# FC60 Numerology AI Framework

A pure-Python framework for AI-powered numerological analysis using the FC60 base-60 encoding system. Zero external dependencies.

**Start here:** For comprehensive AI integration guidance, read `logic/00_MASTER_SYSTEM_PROMPT.md` first.

## Architecture

Four tiers with clear dependency flow:

```
core/           → julian_date_engine, base60_codec, weekday_calculator, checksum_validator, fc60_stamp_engine
personal/       → numerology_engine, heartbeat_engine
universal/      → moon_engine, ganzhi_engine, location_engine
synthesis/      → reading_engine, signal_combiner, universe_translator, master_orchestrator
logic/          → 7 documentation files (00-06) for AI interpretation and integration
```

Two modes: **Mode A** = calculator (pure math, deterministic), **Mode B** = reader (interpretation + synthesis via signal_combiner).

## Running Tests

```bash
python3 tests/test_all.py               # Original suite (123 tests)
python3 tests/test_synthesis_deep.py     # Signal combiner + descriptions (50 tests)
python3 tests/test_integration.py        # End-to-end integration (7 tests)
python3 core/fc60_stamp_engine.py        # FC60 stamp self-test
python3 synthesis/master_orchestrator.py # End-to-end demo
```

Each module also has `if __name__ == "__main__"` self-tests.

## Coding Standards

- All public methods are `@staticmethod` on classes (pure functions)
- No external dependencies (stdlib only: `math`, `datetime`, `typing`, `collections`)
- Type hints on all method signatures
- Functions should be <=50 lines
- Every module has self-tests with known test vectors

## Critical Encoding Rules

- **Month**: `ANIMALS[month - 1]` — January = RA (index 0), NOT ANIMALS[month]
- **Hour in time stamp**: 2-char `ANIMALS[hour % 12]`, NOT 4-char token60
- **CHK**: Uses LOCAL date/time values, not UTC-adjusted
- **HALF marker**: `☀` (U+2600) if hour < 12, `🌙` (U+1F319) if hour >= 12

## Signal Priority (from §12.1)

1. Repeated animals (3+) → Very High
2. Repeated animals (2) → High
3. Day planet → Medium
4. Moon phase → Medium
5. DOM token animal+element → Medium
6. Hour animal → Low-Medium
7. Minute texture → Low
8. Year cycle (GZ) → Background
9. Personal overlays → Variable

## Input Priority

heartbeat > location > time > name > gender > DOB > mother

## Key Entry Point

```python
from synthesis.master_orchestrator import MasterOrchestrator

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
)
```
