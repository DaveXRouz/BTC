# Project Instructions

## Quick Start for AI Models

1. Read `logic/00_MASTER_SYSTEM_PROMPT.md` first — it contains the system overview, file map, non-negotiable rules, and a quick-start example.

2. Run the Python engine to generate readings:

```python
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime

reading = MasterOrchestrator.generate_reading(
    full_name="...",
    birth_day=..., birth_month=..., birth_year=...,
    current_date=datetime.now(),
)
print(reading['synthesis'])
```

3. Read `logic/03_INTERPRETATION_BIBLE.md` for deep number meanings.
4. Read `logic/04_READING_COMPOSITION_GUIDE.md` for tone and output structure.

## Requirements

- Python 3.6+
- No external dependencies (pure stdlib)
- Works by copying the folder — no install needed

## Two Modes

- **Mode A (Calculator)**: Deterministic math — same input always gives same output
- **Mode B (Reader)**: Interpretation + synthesis via `signal_combiner.py`

## Running Tests

```bash
python3 tests/test_all.py               # 123 tests
python3 tests/test_synthesis_deep.py     # 50 tests
python3 tests/test_integration.py        # 7 tests
```

## Entry Points

- **Main API**: `synthesis/master_orchestrator.py` → `MasterOrchestrator.generate_reading()`
- **Documentation**: `logic/00_MASTER_SYSTEM_PROMPT.md`
- **Full demo**: `example_usage.py`
