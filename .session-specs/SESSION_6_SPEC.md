# SESSION 6 SPEC — Framework Integration: Core Setup

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 1 (schema), Session 5 (location)

---

## TL;DR

- Verify `numerology_ai_framework` passes all 180 standalone tests before touching anything
- Create `framework_bridge.py` — the single bridge connecting NPS Oracle service to the framework's `MasterOrchestrator`
- Add PYTHONPATH configuration so the framework is importable from within the Oracle service (local dev + Docker)
- Delete 12+ obsolete engine files plus the `solvers/` and `logic/` directories (replaced by framework)
- Update all broken imports in `server.py`, `engines/__init__.py`, and any other affected files
- Write 15+ tests covering the bridge, error handling, field mapping, and backward compatibility

---

## OBJECTIVES

1. **Confirm framework integrity** — all 180 tests pass (`test_all.py` + `test_synthesis_deep.py` + `test_integration.py`)
2. **Establish import path** — `from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator` works from inside the Oracle service (both local and Docker)
3. **Create bridge module** — `framework_bridge.py` with `generate_single_reading()` and `generate_multi_reading()` functions that map Oracle service data to framework inputs
4. **Delete duplicate engines** — remove 12+ files in `engines/` plus `solvers/` and `logic/` directories whose functionality is now in the framework
5. **Fix all broken imports** — `server.py`, `engines/__init__.py`, and any other files that imported deleted modules must be redirected to framework equivalents via the bridge
6. **Pass all tests** — new bridge tests pass, no import errors anywhere, framework tests still pass

---

## PREREQUISITES

- [ ] `numerology_ai_framework/` directory exists at project root with all modules
- [ ] Python 3.11+ available
- [ ] No external dependencies needed (framework is pure stdlib)

Verification:
```bash
test -d numerology_ai_framework/synthesis && echo "Framework directory OK"
python3 -c "import sys; print(sys.version)" | grep -q "3.1[1-9]" && echo "Python 3.11+ OK"
```

**Note on Sessions 1-5:** The master spec lists Sessions 1 and 5 as dependencies. However, the `oracle_users` table and Oracle service scaffolding already exist from the 16-session scaffolding phase. The bridge module maps from these existing structures. If Sessions 1-5 added new columns (e.g., `gender`, `heart_rate_bpm`, `timezone_hours`), the bridge handles their absence gracefully via `Optional` parameters and defaults.

---

## FILES TO CREATE

| Path | Purpose |
|------|---------|
| `services/oracle/oracle_service/framework_bridge.py` | **NEW** — Main bridge: maps Oracle service data → `MasterOrchestrator` inputs, provides `generate_single_reading()` and `generate_multi_reading()` |
| `services/oracle/tests/test_framework_bridge.py` | **NEW** — 15+ tests for the bridge module |

## FILES TO MODIFY

| Path | Change |
|------|--------|
| `services/oracle/oracle_service/__init__.py` | Add framework root to `sys.path` alongside existing engine path shim |
| `services/oracle/oracle_service/engines/__init__.py` | Remove all imports from deleted modules; add bridge-based re-exports |
| `services/oracle/oracle_service/server.py` | Redirect imports from deleted engines/logic to framework bridge equivalents |
| `services/oracle/Dockerfile` | Add `COPY` for `numerology_ai_framework/` and `ENV PYTHONPATH` |
| `services/oracle/pyproject.toml` | No changes expected (framework has zero dependencies) |

## FILES TO DELETE

**Engine files (12):**
| Path | Replaced By |
|------|------------|
| `services/oracle/oracle_service/engines/fc60.py` | `numerology_ai_framework/core/fc60_stamp_engine.py` |
| `services/oracle/oracle_service/engines/numerology.py` | `numerology_ai_framework/personal/numerology_engine.py` |
| `services/oracle/oracle_service/engines/multi_user_fc60.py` | Framework + bridge `generate_multi_reading()` |
| `services/oracle/oracle_service/engines/compatibility_analyzer.py` | Session 7 `MultiUserAnalyzer` |
| `services/oracle/oracle_service/engines/compatibility_matrices.py` | Session 7 `MultiUserAnalyzer` |
| `services/oracle/oracle_service/engines/group_dynamics.py` | Session 7 `MultiUserAnalyzer` |
| `services/oracle/oracle_service/engines/group_energy.py` | Session 7 `MultiUserAnalyzer` |
| `services/oracle/oracle_service/engines/math_analysis.py` | `numerology_ai_framework/personal/numerology_engine.py` |
| `services/oracle/oracle_service/engines/scoring.py` | Framework confidence scoring |
| `services/oracle/oracle_service/engines/balance.py` | Framework element balance |
| `services/oracle/oracle_service/engines/perf.py` | No replacement needed (dev-only profiling) |
| `services/oracle/oracle_service/engines/terminal_manager.py` | No replacement needed (terminal UI) |

**Directories (2):**
| Path | Replaced By |
|------|------------|
| `services/oracle/oracle_service/solvers/` (7 files + `__init__.py`) | Framework + bridge |
| `services/oracle/oracle_service/logic/` (6 files + `__init__.py`) | Framework synthesis tier |

**Total deletions:** 12 files + 2 directories (containing 14 more files) = **26 files removed**

---

## IMPLEMENTATION PHASES

### Phase 1: Framework Verification (~20 min)

**Tasks:**

1. Run all three framework test suites:

   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py
   cd numerology_ai_framework && python3 tests/test_synthesis_deep.py
   cd numerology_ai_framework && python3 tests/test_integration.py
   ```

2. Run the orchestrator demo to confirm end-to-end output:

   ```bash
   cd numerology_ai_framework && python3 synthesis/master_orchestrator.py
   ```

3. Verify test counts match expected:
   - `test_all.py` → 123 tests
   - `test_synthesis_deep.py` → 50 tests
   - `test_integration.py` → 7 tests

**Checkpoint:**

- [ ] All 180 tests pass (123 + 50 + 7)
- [ ] Demo produces complete reading with all sections (person, FC60, numerology, moon, ganzhi, heartbeat, patterns, confidence, synthesis)
- Verify: `cd numerology_ai_framework && python3 tests/test_all.py 2>&1 | tail -5`

🚨 STOP if checkpoint fails — framework must be healthy before any integration work

---

### Phase 2: PYTHONPATH Setup (~30 min)

**Tasks:**

1. **Update `services/oracle/oracle_service/__init__.py`** — add framework root to `sys.path`:

   Current code adds `oracle_service/` to path for legacy `from engines.xxx` imports. Add framework root alongside it:

   ```python
   # Key pattern — add framework root so `from numerology_ai_framework.xxx` resolves
   _project_root = str(Path(__file__).resolve().parents[3])  # NPS/
   if _project_root not in sys.path:
       sys.path.insert(0, _project_root)
   ```

   The directory hierarchy is:
   ```
   NPS/                                    ← parents[3] from __init__.py
   ├── numerology_ai_framework/            ← this needs to be importable
   └── services/oracle/oracle_service/     ← __init__.py lives here
                     └── __init__.py       ← parents[0] = oracle_service/
                                              parents[1] = oracle/
                                              parents[2] = services/
                                              parents[3] = NPS/
   ```

2. **Update `services/oracle/Dockerfile`** — copy framework into container and set PYTHONPATH:

   ```dockerfile
   # Copy framework (before application code for layer caching)
   COPY ../../numerology_ai_framework /app/numerology_ai_framework
   ```

   **Important Docker context note:** The Dockerfile is at `services/oracle/Dockerfile`. If `docker-compose.yml` sets context to project root, use:
   ```dockerfile
   COPY numerology_ai_framework/ /app/numerology_ai_framework/
   ```
   If context is `services/oracle/`, the compose file needs a context change. Check `docker-compose.yml` to determine the correct COPY path.

   Add environment variable:
   ```dockerfile
   ENV PYTHONPATH="/app:/app/numerology_ai_framework:${PYTHONPATH}"
   ```

3. **Verify import works locally:**

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service  # triggers sys.path shim
   from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator
   print('Framework import OK')
   "
   ```

**Checkpoint:**

- [ ] `from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator` succeeds from within Oracle service context
- [ ] `Path(__file__).resolve().parents[3]` correctly resolves to project root (NPS/)
- Verify: `cd services/oracle && python3 -c "import oracle_service; from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator; print('OK')"`

🚨 STOP if checkpoint fails — all subsequent work depends on this import path

---

### Phase 3: Create Framework Bridge (~90 min)

**Tasks:**

Create `services/oracle/oracle_service/framework_bridge.py` with these components:

**3A. High-level bridge functions (primary API for Sessions 7+):**

```python
def generate_single_reading(
    full_name: str,
    birth_day: int,
    birth_month: int,
    birth_year: int,
    current_date: Optional[datetime] = None,
    mother_name: Optional[str] = None,
    gender: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    heart_rate_bpm: Optional[int] = None,
    current_hour: Optional[int] = None,
    current_minute: Optional[int] = None,
    current_second: Optional[int] = None,
    tz_hours: int = 0,
    tz_minutes: int = 0,
    numerology_system: str = "pythagorean",
    mode: str = "full",
) -> Dict[str, Any]:
    """
    Generate a complete numerological reading for one person.

    Wraps MasterOrchestrator.generate_reading() with:
    - Timing (logs duration via time.perf_counter())
    - Error handling (framework exceptions → NPS error format)
    - Input validation

    Returns: Full framework output dict (person, numerology, fc60_stamp, moon, ganzhi, etc.)
    """
```

```python
def generate_multi_reading(
    users: List[Dict[str, Any]],
    current_date: Optional[datetime] = None,
    current_hour: Optional[int] = None,
    current_minute: Optional[int] = None,
    current_second: Optional[int] = None,
    numerology_system: str = "pythagorean",
) -> List[Dict[str, Any]]:
    """
    Generate readings for multiple users.

    Each user dict must have: full_name, birth_day, birth_month, birth_year.
    Optional: mother_name, gender, latitude, longitude, heart_rate_bpm, tz_hours, tz_minutes.

    Returns: List of framework output dicts, one per user.
    """
```

**3B. Field mapping helper (maps oracle_users DB columns → framework params):**

```python
def map_oracle_user_to_framework_kwargs(oracle_user) -> Dict[str, Any]:
    """
    Map an oracle_user ORM object or dict to MasterOrchestrator keyword arguments.

    Field mapping:
        oracle_users.name          → full_name
        oracle_users.birthday      → birth_day, birth_month, birth_year (extracted from DATE)
        oracle_users.mother_name   → mother_name
        oracle_users.coordinates   → latitude, longitude (extracted from POINT)
        oracle_users.gender        → gender (if column exists, else None)
        oracle_users.heart_rate_bpm → actual_bpm (if column exists, else None)
        oracle_users.timezone_hours → tz_hours (if column exists, else 0)
        oracle_users.timezone_minutes → tz_minutes (if column exists, else 0)

    Handles both dict and ORM-style access (getattr with defaults).
    """
```

**3C. Backward-compatible re-exports (for server.py transition):**

The current `server.py` calls specific low-level functions from deleted engines:
- `encode_fc60()`, `ganzhi_year()`, `ANIMAL_NAMES`, `ELEMENT_NAMES`, etc. from `engines/fc60.py`
- `life_path()`, `numerology_reduce()`, `name_to_number()`, etc. from `engines/numerology.py`
- `get_current_quality()`, `get_optimal_hours_today()` from `logic/timing_advisor.py`

The bridge must re-export these from the framework with compatible signatures:

```python
# Re-exports from framework for backward compatibility with server.py
# These map old engine function names → framework equivalents

from numerology_ai_framework.core.fc60_stamp_engine import FC60StampEngine
from numerology_ai_framework.core.base60_codec import Base60Codec
from numerology_ai_framework.core.julian_date_engine import JulianDateEngine
from numerology_ai_framework.core.weekday_calculator import WeekdayCalculator
from numerology_ai_framework.personal.numerology_engine import NumerologyEngine
from numerology_ai_framework.universal.ganzhi_engine import GanzhiEngine
from numerology_ai_framework.universal.moon_engine import MoonEngine

def encode_fc60(year, month, day, hour=0, minute=0, second=0, tz_h=0, tz_m=0, **kwargs):
    """Backward-compatible wrapper for FC60StampEngine.encode()."""
    has_time = hour > 0 or minute > 0 or second > 0 or kwargs.get("include_time", True)
    return FC60StampEngine.encode(year, month, day, hour, minute, second, tz_h, tz_m, has_time=has_time)

def life_path(year, month, day):
    """Backward-compatible wrapper for NumerologyEngine.life_path()."""
    return NumerologyEngine.life_path(year, month, day)

def numerology_reduce(n):
    """Backward-compatible wrapper for NumerologyEngine.reduce()."""
    return NumerologyEngine.reduce(n)

def name_to_number(name, system="pythagorean"):
    """Backward-compatible wrapper for NumerologyEngine.expression_number()."""
    return NumerologyEngine.expression_number(name, system=system)

# ... (additional re-exports as needed by server.py)
```

**Important:** Before writing these re-exports, carefully read each framework module to confirm the exact method signatures match. Some legacy functions may have different parameter names or return formats. Document any mismatches and adapt the wrapper.

**3D. Wrapper for `engines/oracle.py` functions:**

`engines/oracle.py` (which is KEPT, not deleted) calls functions from `engines/fc60.py` and `engines/numerology.py` internally. After those files are deleted, `oracle.py` will break. Two options:

- **Option A:** Update `oracle.py` imports to use `framework_bridge` re-exports
- **Option B:** Update `oracle.py` imports to use framework modules directly

Choose whichever is simpler. The goal is zero import errors.

**3E. Error handling pattern:**

```python
import logging
import time

logger = logging.getLogger(__name__)

class FrameworkBridgeError(Exception):
    """Raised when framework integration fails."""
    pass

def generate_single_reading(...) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = MasterOrchestrator.generate_reading(...)
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info("Framework reading generated in %.1fms", duration_ms)
        return result
    except (ValueError, TypeError) as e:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.error("Framework reading failed after %.1fms: %s", duration_ms, e)
        raise FrameworkBridgeError(f"Reading generation failed: {e}") from e
```

**Checkpoint:**

- [ ] `framework_bridge.py` exists with all components (3A-3E)
- [ ] `generate_single_reading()` returns a valid framework output dict
- [ ] `map_oracle_user_to_framework_kwargs()` maps a sample dict correctly
- [ ] Re-export functions (`encode_fc60`, `life_path`, etc.) produce correct output
- Verify: `cd services/oracle && python3 -c "import oracle_service; from oracle_service.framework_bridge import generate_single_reading; r = generate_single_reading('Test User', 15, 7, 1990); print(r['confidence'])"`

🚨 STOP if checkpoint fails

---

### Phase 4: Delete Old Engines (~30 min)

**Tasks:**

1. **Before deleting anything**, scan for all imports from files about to be deleted:

   ```bash
   grep -rn "from engines.fc60" services/oracle/ --include="*.py"
   grep -rn "from engines.numerology" services/oracle/ --include="*.py"
   grep -rn "from engines.math_analysis" services/oracle/ --include="*.py"
   grep -rn "from engines.scoring" services/oracle/ --include="*.py"
   grep -rn "from engines.balance" services/oracle/ --include="*.py"
   grep -rn "from engines.perf" services/oracle/ --include="*.py"
   grep -rn "from engines.terminal_manager" services/oracle/ --include="*.py"
   grep -rn "from engines.multi_user" services/oracle/ --include="*.py"
   grep -rn "from engines.compatibility" services/oracle/ --include="*.py"
   grep -rn "from engines.group" services/oracle/ --include="*.py"
   grep -rn "from logic." services/oracle/ --include="*.py"
   grep -rn "from solvers." services/oracle/ --include="*.py"
   grep -rn "import engines.fc60" services/oracle/ --include="*.py"
   ```

   **Record every hit.** Each must be fixed in Phase 5 before the code is usable.

2. **Git stash** before deletion (safety):

   ```bash
   git stash push -m "pre-session-6-deletion-safety"
   ```

3. **Delete engine files** (12 files):

   ```bash
   rm services/oracle/oracle_service/engines/fc60.py
   rm services/oracle/oracle_service/engines/numerology.py
   rm services/oracle/oracle_service/engines/multi_user_fc60.py
   rm services/oracle/oracle_service/engines/compatibility_analyzer.py
   rm services/oracle/oracle_service/engines/compatibility_matrices.py
   rm services/oracle/oracle_service/engines/group_dynamics.py
   rm services/oracle/oracle_service/engines/group_energy.py
   rm services/oracle/oracle_service/engines/math_analysis.py
   rm services/oracle/oracle_service/engines/scoring.py
   rm services/oracle/oracle_service/engines/balance.py
   rm services/oracle/oracle_service/engines/perf.py
   rm services/oracle/oracle_service/engines/terminal_manager.py
   ```

4. **Delete directories** (2 folders):

   ```bash
   rm -rf services/oracle/oracle_service/solvers/
   rm -rf services/oracle/oracle_service/logic/
   ```

5. **Verify deletion** — confirm only KEPT files remain in engines/:

   ```bash
   ls services/oracle/oracle_service/engines/
   ```

   Expected remaining files:
   - `__init__.py`
   - `ai_client.py`
   - `ai_engine.py`
   - `ai_interpreter.py`
   - `config.py`
   - `errors.py`
   - `events.py`
   - `health.py`
   - `learner.py`
   - `learning.py`
   - `logger.py`
   - `memory.py`
   - `multi_user_service.py`
   - `notifier.py`
   - `oracle.py`
   - `prompt_templates.py`
   - `scanner_brain.py`
   - `security.py`
   - `session_manager.py`
   - `translation_service.py`
   - `vault.py`

**Checkpoint:**

- [ ] 12 engine files deleted
- [ ] `solvers/` directory deleted (8 files including `__init__.py`)
- [ ] `logic/` directory deleted (7 files including `__init__.py`)
- [ ] Only 21 engine files remain (the KEPT ones listed above)
- Verify: `ls services/oracle/oracle_service/engines/*.py | wc -l` → should be 21
- Verify: `test -d services/oracle/oracle_service/solvers && echo "ERROR: solvers still exists" || echo "OK: solvers deleted"`
- Verify: `test -d services/oracle/oracle_service/logic && echo "ERROR: logic still exists" || echo "OK: logic deleted"`

🚨 STOP if wrong files were deleted — use `git stash pop` to recover

---

### Phase 5: Update All Broken Imports (~60 min)

This is the most critical phase. After deleting files, many imports are broken. Fix them all.

**Tasks:**

**5A. Update `services/oracle/oracle_service/engines/__init__.py`:**

Current file imports from deleted modules (fc60, numerology, math_analysis, scoring). Replace with:

```python
"""Oracle Service — Engine Layer.

Calculation engines now provided by numerology_ai_framework.
Bridge module provides backward-compatible wrappers.
Kept engines: ai_*, oracle, translation_service, security, vault, learner, scanner_brain, etc.
"""

# Bridge re-exports (backward compatibility for code that imported from engines)
from oracle_service.framework_bridge import (
    encode_fc60,
    life_path,
    name_to_number,
    numerology_reduce,
    # ... other re-exported functions
)

# Oracle readings (KEPT — not deleted)
from engines.oracle import read_sign, read_name, question_sign, daily_insight

# AI interpretation (KEPT)
from engines.ai_interpreter import (
    interpret_reading,
    interpret_all_formats,
    interpret_group,
)
from engines.translation_service import translate, batch_translate, detect_language
```

**5B. Update `services/oracle/oracle_service/server.py`:**

Current imports on lines 26-52 reference deleted modules. Replace with framework bridge imports:

```python
# BEFORE (broken — these files are deleted):
from engines.fc60 import encode_fc60, ganzhi_year, ANIMAL_NAMES, ...
from engines.numerology import life_path, numerology_reduce, ...
from logic.timing_advisor import get_current_quality, get_optimal_hours_today

# AFTER (uses bridge re-exports):
from oracle_service.framework_bridge import (
    encode_fc60,
    life_path,
    numerology_reduce,
    name_to_number,
    name_soul_urge,
    name_personality,
    personal_year,
    ganzhi_year,
    ANIMAL_NAMES,
    ELEMENT_NAMES,
    STEM_ELEMENTS,
    STEM_POLARITY,
    STEM_NAMES,
    LETTER_VALUES,
    LIFE_PATH_MEANINGS,
)
from engines.oracle import read_sign, read_name, question_sign, daily_insight, _get_zodiac
```

**Critical:** `server.py` also imports `get_current_quality` and `get_optimal_hours_today` from `logic.timing_advisor` (line 52). This module is in the deleted `logic/` folder. The framework does NOT have a timing_advisor equivalent. Options:

1. **Keep `logic/timing_advisor.py` as an exception** — don't delete it, move it into `engines/` since it's still needed by the gRPC server
2. **Rewrite timing logic** using framework's moon/ganzhi data — more work but cleaner
3. **Stub the functions** to return defaults until a later session rewrites the server

**Recommended: Option 1** — move `timing_advisor.py` to `engines/timing_advisor.py`. It's a small, self-contained module that the gRPC server actively uses. Deleting it breaks a running RPC (`GetTimingAlignment`). The spec should check `timing_advisor.py`'s own imports to ensure they don't depend on other deleted files.

```bash
# Check timing_advisor's dependencies:
grep "^from\|^import" services/oracle/oracle_service/logic/timing_advisor.py
```

If `timing_advisor.py` imports from deleted engines (e.g., `from engines.fc60 import ...`), those imports must also be updated to use the bridge.

**5C. Update `engines/oracle.py`:**

This KEPT file likely imports from deleted engines internally. Check and fix:

```bash
grep "^from\|^import" services/oracle/oracle_service/engines/oracle.py
```

Redirect any imports from deleted modules to use `framework_bridge` re-exports or framework modules directly.

**5D. Check ALL remaining engine files:**

Some kept files (e.g., `multi_user_service.py`, `learner.py`, `scanner_brain.py`) may import from deleted modules:

```bash
for f in services/oracle/oracle_service/engines/*.py; do
    echo "=== $f ==="
    grep "^from\|^import" "$f" | grep -E "fc60|numerology|math_analysis|scoring|balance|solvers|logic\." || echo "(clean)"
done
```

Fix every broken import found.

**5E. Check test files:**

```bash
grep -rn "from engines.fc60\|from engines.numerology\|from engines.scoring\|from engines.math\|from logic\.\|from solvers\." services/oracle/tests/ --include="*.py"
```

Update test imports. Some test files may need significant rework if they tested deleted engines directly.

**5F. Final import sweep:**

```bash
cd services/oracle && python3 -c "import oracle_service" 2>&1
cd services/oracle && python3 -c "import oracle_service.server" 2>&1
cd services/oracle && python3 -c "from oracle_service.engines import read_sign, life_path" 2>&1
cd services/oracle && python3 -c "from oracle_service.framework_bridge import generate_single_reading" 2>&1
```

All four commands must succeed with zero import errors.

**Checkpoint:**

- [ ] `python3 -c "import oracle_service"` — no errors
- [ ] `python3 -c "import oracle_service.server"` — no errors (requires gRPC packages)
- [ ] `python3 -c "from oracle_service.framework_bridge import generate_single_reading"` — no errors
- [ ] `python3 -c "from oracle_service.engines import read_sign"` — no errors
- [ ] Zero grep hits for deleted module imports: `grep -rn "from engines.fc60\|from engines.numerology\|from engines.scoring\|from engines.math_analysis\|from engines.balance\|from engines.perf\|from engines.terminal_manager\|from engines.multi_user_fc60\|from engines.compatibility\|from engines.group\|from solvers\." services/oracle/ --include="*.py"` returns nothing

🚨 STOP if any import fails — fix before proceeding

---

### Phase 6: Write Tests (~60 min)

**Tasks:**

Create `services/oracle/tests/test_framework_bridge.py`:

**6A. Bridge function tests:**

```python
def test_generate_single_reading_basic():
    """Full reading with all required fields returns complete dict."""

def test_generate_single_reading_minimal():
    """Reading with only required fields (no optional data) succeeds with lower confidence."""

def test_generate_single_reading_all_fields():
    """Reading with all optional fields produces highest confidence."""

def test_generate_single_reading_stamp_only_mode():
    """mode='stamp_only' returns only fc60_stamp section."""

def test_generate_multi_reading_two_users():
    """Two-user reading returns list of 2 complete dicts."""

def test_generate_multi_reading_five_users():
    """Five-user reading returns list of 5 complete dicts."""
```

**6B. Field mapping tests:**

```python
def test_map_oracle_user_dict():
    """Dict with oracle_users column names maps correctly to framework kwargs."""

def test_map_oracle_user_missing_optionals():
    """Dict with only name+birthday+mother_name maps correctly; optional fields default to None/0."""

def test_map_oracle_user_coordinates_extraction():
    """Coordinates POINT field extracts latitude and longitude correctly."""

def test_map_oracle_user_birthday_extraction():
    """DATE field extracts birth_day, birth_month, birth_year correctly."""
```

**6C. Backward compatibility tests:**

```python
def test_compat_encode_fc60():
    """Bridge encode_fc60() produces valid FC60 stamp dict with expected keys."""

def test_compat_life_path():
    """Bridge life_path() returns correct life path number (test vector: 1990-07-15 → known LP)."""

def test_compat_numerology_reduce():
    """Bridge numerology_reduce() reduces correctly (e.g., 29 → 11 master, 28 → 1)."""

def test_compat_name_to_number():
    """Bridge name_to_number() returns expression number for a name."""
```

**6D. Error handling tests:**

```python
def test_generate_reading_invalid_date():
    """Invalid birth date (month=13) raises FrameworkBridgeError."""

def test_generate_reading_empty_name():
    """Empty name string raises FrameworkBridgeError."""

def test_error_includes_original_exception():
    """FrameworkBridgeError wraps original exception via __cause__."""
```

**6E. Timing/logging tests:**

```python
def test_reading_logs_timing(caplog):
    """Reading generation logs duration in milliseconds."""
```

**Test vectors (deterministic — same input always gives same output):**

```python
# Alice Johnson test vector (from framework demo)
ALICE = {
    "full_name": "Alice Johnson",
    "birth_day": 15, "birth_month": 7, "birth_year": 1990,
    "mother_name": "Barbara Johnson",
    "gender": "female",
    "latitude": 40.7, "longitude": -74.0,
    "heart_rate_bpm": 68,
    "tz_hours": -5, "tz_minutes": 0,
}

# Bob Smith (minimal data — only required fields)
BOB = {
    "full_name": "Bob Smith",
    "birth_day": 1, "birth_month": 1, "birth_year": 2000,
}
```

**Checkpoint:**

- [ ] All 15+ tests pass
- [ ] Framework tests still pass (no regressions)
- Verify:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_framework_bridge.py -v --tb=short
  cd numerology_ai_framework && python3 tests/test_all.py
  ```

🚨 STOP if tests fail

---

### Phase 7: Final Verification (~20 min)

**Tasks:**

1. **Full import test** — every Python file in Oracle service imports cleanly:

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service
   from oracle_service.framework_bridge import generate_single_reading, generate_multi_reading, map_oracle_user_to_framework_kwargs
   from oracle_service.framework_bridge import encode_fc60, life_path, numerology_reduce, name_to_number
   from oracle_service.engines import read_sign, interpret_reading, translate
   print('All imports OK')
   "
   ```

2. **Generate a test reading through the bridge:**

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service
   from oracle_service.framework_bridge import generate_single_reading
   r = generate_single_reading('Alice Johnson', 15, 7, 1990, mother_name='Barbara Johnson', gender='female', latitude=40.7, longitude=-74.0)
   assert 'numerology' in r
   assert 'fc60_stamp' in r
   assert 'confidence' in r
   assert r['confidence']['score'] >= 50
   print(f'Reading OK — confidence: {r[\"confidence\"][\"score\"]}%')
   "
   ```

3. **Run all Oracle service tests:**

   ```bash
   cd services/oracle && python3 -m pytest tests/ -v --tb=short
   ```

   Some pre-existing tests (e.g., `test_engines.py`, `test_multi_user_fc60.py`) may fail because they tested deleted engines directly. These should either be:
   - Updated to test via the bridge
   - Deleted if they test functionality that no longer exists at this layer
   - Marked with notes for future sessions

4. **Framework tests still pass (regression check):**

   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py && python3 tests/test_synthesis_deep.py && python3 tests/test_integration.py
   ```

5. **Lint and format:**

   ```bash
   cd services/oracle && python3 -m ruff check oracle_service/framework_bridge.py --fix
   cd services/oracle && python3 -m ruff format oracle_service/framework_bridge.py
   ```

6. **Git commit:**

   ```bash
   git add -A
   git commit -m "[oracle] integrate numerology_ai_framework via bridge module (#session-6)

   - Create framework_bridge.py with generate_single_reading/multi_reading
   - Delete 26 obsolete engine/solver/logic files replaced by framework
   - Update server.py and engines/__init__.py imports
   - Add PYTHONPATH setup for framework in __init__.py and Dockerfile
   - Add 15+ bridge tests"
   ```

**Checkpoint:**

- [ ] Zero import errors across entire Oracle service
- [ ] Bridge generates valid readings
- [ ] All new tests pass
- [ ] Framework tests still pass (180/180)
- [ ] Code linted and formatted
- [ ] Committed to git

---

## TESTS TO WRITE

### `services/oracle/tests/test_framework_bridge.py`

| Test Function | Verifies |
|--------------|----------|
| `test_generate_single_reading_basic` | Full reading returns dict with all expected top-level keys |
| `test_generate_single_reading_minimal` | Reading with only required fields succeeds |
| `test_generate_single_reading_all_fields` | All optional fields produce highest confidence |
| `test_generate_single_reading_stamp_only_mode` | `mode='stamp_only'` returns only fc60_stamp |
| `test_generate_multi_reading_two_users` | Two users produce list of 2 result dicts |
| `test_generate_multi_reading_five_users` | Five users produce list of 5 result dicts |
| `test_map_oracle_user_dict` | Dict with DB column names maps to framework kwargs correctly |
| `test_map_oracle_user_missing_optionals` | Missing optional fields default gracefully |
| `test_map_oracle_user_coordinates_extraction` | POINT coordinates extract lat/lon |
| `test_map_oracle_user_birthday_extraction` | DATE extracts day/month/year |
| `test_compat_encode_fc60` | Bridge `encode_fc60()` produces valid FC60 stamp |
| `test_compat_life_path` | Bridge `life_path()` matches known test vector |
| `test_compat_numerology_reduce` | Bridge `numerology_reduce()` handles master numbers correctly |
| `test_compat_name_to_number` | Bridge `name_to_number()` returns expression number |
| `test_generate_reading_invalid_date` | Invalid date raises `FrameworkBridgeError` |
| `test_generate_reading_empty_name` | Empty name raises `FrameworkBridgeError` |
| `test_error_includes_original_exception` | `FrameworkBridgeError.__cause__` is set |
| `test_reading_logs_timing` | Duration logged via `caplog` |

**Total: 18 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] `numerology_ai_framework` tests: 180/180 pass (no regressions)
- [ ] `framework_bridge.py` exists at `services/oracle/oracle_service/framework_bridge.py`
- [ ] `generate_single_reading()` returns complete reading dict for any valid user
- [ ] `generate_multi_reading()` returns list of reading dicts for 1-N users
- [ ] `map_oracle_user_to_framework_kwargs()` maps oracle_users DB fields correctly
- [ ] Backward-compatible re-exports (`encode_fc60`, `life_path`, `numerology_reduce`, `name_to_number`, etc.) work
- [ ] 26 files deleted (12 engines + 8 solvers + 7 logic, counting `__init__.py` files)
- [ ] Zero broken imports: `python3 -c "import oracle_service"` succeeds
- [ ] `server.py` imports resolve without error: `python3 -c "import oracle_service.server"` succeeds
- [ ] `engines/__init__.py` exports work: `python3 -c "from oracle_service.engines import read_sign"` succeeds
- [ ] All 18+ new tests pass: `cd services/oracle && python3 -m pytest tests/test_framework_bridge.py -v`
- [ ] Docker PYTHONPATH configured in `services/oracle/Dockerfile`
- Verify all:
  ```bash
  cd numerology_ai_framework && python3 tests/test_all.py && echo "FRAMEWORK OK"
  cd services/oracle && python3 -m pytest tests/test_framework_bridge.py -v --tb=short && echo "BRIDGE TESTS OK"
  cd services/oracle && python3 -c "import oracle_service; from oracle_service.framework_bridge import generate_single_reading; r = generate_single_reading('Test', 1, 1, 2000); print(f'Confidence: {r[\"confidence\"][\"score\"]}%')" && echo "E2E OK"
  ```

---

## ERROR SCENARIOS

| Scenario | Expected Behavior | Recovery |
|----------|-------------------|----------|
| Framework not at project root | `ImportError` at `oracle_service/__init__.py` load time | Verify `numerology_ai_framework/` exists at repo root; check `sys.path` resolution |
| `parents[3]` resolves to wrong directory | Framework imports fail | Print `Path(__file__).resolve().parents[3]` and adjust index; use absolute path as fallback |
| Deleted engine still imported somewhere | `ModuleNotFoundError: No module named 'engines.fc60'` | Run grep sweep from Phase 5 to find missed imports; redirect to bridge |
| `timing_advisor.py` depends on deleted engines | `ImportError` inside timing_advisor after move | Check timing_advisor's own imports; redirect its internal imports to bridge re-exports |
| Legacy `encode_fc60()` signature differs from framework | `TypeError: unexpected keyword argument` in server.py | Compare old vs new signatures carefully; add `**kwargs` to bridge wrapper to absorb extras |
| Framework function returns different dict structure than old engine | `KeyError` in server.py gRPC handlers | Map framework output keys to expected proto field names in bridge |
| Docker build fails (COPY path wrong) | `COPY failed: file not found` | Check docker-compose context directory; adjust COPY source path accordingly |
| Oracle gRPC server won't start after import changes | Server crash at startup | Run `python3 -c "import oracle_service.server"` to isolate import errors; fix one by one |
| Pre-existing tests fail because they tested deleted engines | Test failures in `test_engines.py`, `test_multi_user_fc60.py` | Update tests to use bridge, or delete if they test removed functionality |
| `oracle.py` breaks because it imported from deleted `fc60.py` | `ImportError` in KEPT file | Update `oracle.py` internal imports to use bridge re-exports |

---

## HANDOFF

**Created:**
- `services/oracle/oracle_service/framework_bridge.py` — bridge module with high-level API + backward-compat re-exports
- `services/oracle/tests/test_framework_bridge.py` — 18+ tests

**Modified:**
- `services/oracle/oracle_service/__init__.py` — framework root added to sys.path
- `services/oracle/oracle_service/engines/__init__.py` — cleaned up, uses bridge re-exports
- `services/oracle/oracle_service/server.py` — imports redirected to bridge
- `services/oracle/oracle_service/engines/oracle.py` — imports updated (if it depended on deleted modules)
- `services/oracle/Dockerfile` — PYTHONPATH for framework
- Possibly `services/oracle/oracle_service/engines/timing_advisor.py` (moved from logic/)

**Deleted:**
- 12 engine files (fc60.py, numerology.py, multi_user_fc60.py, compatibility_analyzer.py, compatibility_matrices.py, group_dynamics.py, group_energy.py, math_analysis.py, scoring.py, balance.py, perf.py, terminal_manager.py)
- `services/oracle/oracle_service/solvers/` directory (8 files)
- `services/oracle/oracle_service/logic/` directory (7 files)

**Next session (Session 7) receives:**
- `framework_bridge.py` exists and is importable with `generate_single_reading()` function
- `MasterOrchestrator` accessible from Oracle service context
- All old duplicate engines removed — clean slate for building typed reading functions
- `map_oracle_user_to_framework_kwargs()` available for Session 7's `UserProfile.to_framework_kwargs()` design
- Backward-compatible function re-exports allow `server.py` to continue operating during transition
