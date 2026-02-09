# FC60 Framework API Reference

Concise developer reference for the FC60 Numerology AI Framework.
Covers every public method, test command, coding standard, and common pitfall.

---

## 1. Architecture Overview

```
TIER 1: core/               Pure math — no external dependencies
  julian_date_engine.py      Gregorian <-> JDN conversion (Fliegel-Van Flandern)
  base60_codec.py            Encode/decode integers in base-60 syllabic alphabet
  weekday_calculator.py      Weekday + planet + domain from JDN
  checksum_validator.py      Weighted CHK token for error detection
  fc60_stamp_engine.py       Full 11-step Mode A encoding pipeline

TIER 2: personal/           Person-specific calculations
  numerology_engine.py       Life Path, Expression, Soul Urge, PY/PM/PD
  heartbeat_engine.py        BPM estimation + element mapping

TIER 3: universal/          Cosmic / environmental data
  moon_engine.py             Lunar phase from JDN (synodic approximation)
  ganzhi_engine.py           Chinese Sexagenary Cycle (year/day/hour)
  location_engine.py         Lat/lon -> element, polarity, TZ estimate

TIER 4: synthesis/          Combine everything into readings
  reading_engine.py          Signal hierarchy + animal/element analysis
  signal_combiner.py         Planet-Moon combos, LP-PY combos, harmony/clash
  universe_translator.py     9-section human-readable output
  master_orchestrator.py     Main entry point — 10-step pipeline
```

**Dependency flow** (strictly acyclic):

```
core  <--  personal
core  <--  universal
core + personal + universal  <--  synthesis
```

**Two modes:** Mode A = calculator (pure math, deterministic), Mode B = reader (interpretation + synthesis).

---

## 2. Master Orchestrator API

### `MasterOrchestrator.generate_reading(...)` -> Dict

The single entry point for the entire framework.

```python
from synthesis.master_orchestrator import MasterOrchestrator

reading = MasterOrchestrator.generate_reading(
    full_name="Alice Johnson",            # str       REQUIRED
    birth_day=15,                          # int       REQUIRED
    birth_month=7,                         # int       REQUIRED
    birth_year=1990,                       # int       REQUIRED
    current_date=datetime(2026, 2, 9),     # datetime  optional (default: now)
    mother_name="Barbara Johnson",         # str       optional
    gender="female",                       # str       optional ("male"/"female")
    latitude=40.7,                         # float     optional
    longitude=-74.0,                       # float     optional
    actual_bpm=68,                         # int       optional
    current_hour=14,                       # int       optional (0-23)
    current_minute=30,                     # int       optional (0-59)
    current_second=0,                      # int       optional (0-59)
    tz_hours=-5,                           # int       optional (default 0 = UTC)
    tz_minutes=0,                          # int       optional (default 0)
    numerology_system="pythagorean",       # str       optional ("chaldean")
    mode="full",                           # str       optional ("stamp_only")
)
```

### Return dict top-level keys

| Key           | Type | Contents                                                |
| ------------- | ---- | ------------------------------------------------------- |
| `person`      | dict | name, birthdate, age_years, age_days                    |
| `birth`       | dict | jdn, jdn_fc60, weekday, planet, year_fc60               |
| `current`     | dict | date, jdn, jdn_fc60, weekday, planet, domain            |
| `numerology`  | dict | life_path, expression, soul_urge, personality, PY/PM/PD |
| `patterns`    | dict | detected (list), count                                  |
| `confidence`  | dict | score (int 50-95), level, factors                       |
| `synthesis`   | str  | Full prose reading text                                 |
| `fc60_stamp`  | dict | All FC60 fields + internal `_` metadata                 |
| `moon`        | dict | phase_name, emoji, age, illumination, energy            |
| `ganzhi`      | dict | year, day, hour sub-dicts                               |
| `heartbeat`   | dict | bpm, element, rhythm_token, total_lifetime_beats        |
| `location`    | dict | element, lat/lon_hemisphere, timezone_estimate          |
| `reading`     | dict | Raw reading engine output (signals, contexts)           |
| `translation` | dict | 9 named sections + full_text                            |

### Usage Examples

**Minimal** (name + DOB only):

```python
r = MasterOrchestrator.generate_reading(
    full_name="James Chen", birth_day=1, birth_month=3, birth_year=1985
)
```

**Standard** (+ time + location):

```python
r = MasterOrchestrator.generate_reading(
    full_name="Maria Rodriguez", birth_day=22, birth_month=11, birth_year=1978,
    current_date=datetime(2026, 2, 10), current_hour=9, current_minute=15,
    latitude=19.4, longitude=-99.1, tz_hours=-6,
)
```

**Full** (all 6 dimensions):

```python
r = MasterOrchestrator.generate_reading(
    full_name="Alice Johnson", birth_day=15, birth_month=7, birth_year=1990,
    current_date=datetime(2026, 2, 9), mother_name="Barbara Johnson",
    gender="female", latitude=40.7, longitude=-74.0, actual_bpm=68,
    current_hour=14, current_minute=30, current_second=0,
    tz_hours=-5, tz_minutes=0,
)
```

---

## 3. Individual Module APIs

### 3.1 `core/julian_date_engine.py` — `JulianDateEngine`

```python
gregorian_to_jdn(year: int, month: int, day: int) -> int
jdn_to_gregorian(jdn: int) -> Tuple[int, int, int]
is_leap_year(year: int) -> bool
is_valid_date(year: int, month: int, day: int) -> bool
jdn_to_mjd(jdn: int) -> int
mjd_to_jdn(mjd: int) -> int
jdn_to_rd(jdn: int) -> int
rd_to_jdn(rd: int) -> int
jdn_to_unix_days(jdn: int) -> int
unix_days_to_jdn(unix_days: int) -> int
current_jdn() -> int
verify_cross_references(jdn: int) -> dict
```

```python
>>> JulianDateEngine.gregorian_to_jdn(2026, 2, 6)
2461078
>>> JulianDateEngine.jdn_to_gregorian(2451545)
(2000, 1, 1)
```

### 3.2 `core/base60_codec.py` — `Base60Codec`

```python
token60(n: int) -> str                         # 0-59 -> 4-char token
digit60(token: str) -> int                     # 4-char token -> 0-59
to_base60(n: int) -> List[int]                 # int -> base-60 digit list
from_base60(digits: List[int]) -> int          # base-60 digit list -> int
encode_base60(n: int) -> str                   # int -> hyphen-separated tokens
decode_base60(encoded: str) -> int             # hyphen-separated tokens -> int
get_animal_name(index: int) -> str             # 0-11 -> "Rat".."Pig"
get_element_name(index: int) -> str            # 0-4  -> "Wood".."Water"
describe_token(token: str) -> str              # "SNFI" -> "SNFI = 26 (Snake Fire)"
```

```python
>>> Base60Codec.token60(26)
'SNFI'
>>> Base60Codec.encode_base60(2026)
'HOMT-ROFI'
```

### 3.3 `core/weekday_calculator.py` — `WeekdayCalculator`

```python
weekday_from_jdn(jdn: int) -> int             # 0=Sun..6=Sat
weekday_token(jdn: int) -> str                 # "SO","LU","MA","ME","JO","VE","SA"
weekday_name(jdn: int) -> str                  # "Sunday".."Saturday"
planet_name(jdn: int) -> str                   # "Sun".."Saturn"
symbolic_domain(jdn: int) -> str               # domain description
full_info(jdn: int) -> dict                    # all of the above
```

```python
>>> WeekdayCalculator.full_info(2461078)
{'index': 5, 'token': 'VE', 'name': 'Friday', 'planet': 'Venus', 'domain': '...'}
```

### 3.4 `core/checksum_validator.py` — `ChecksumValidator`

```python
calculate_chk(year, month, day, hour=0, minute=0, second=0, jdn=None) -> str
calculate_chk_date_only(year: int, month: int, day: int, jdn: int) -> str
verify_chk(expected_chk, year, month, day, hour=0, minute=0, second=0, jdn=None) -> bool
```

CHK formula: `(1*year%60 + 2*month + 3*day + 4*hour + 5*minute + 6*second + 7*JDN%60) % 60`

```python
>>> ChecksumValidator.calculate_chk(2026, 2, 6, 1, 15, 0, jdn=2461078)
'TIMT'
```

### 3.5 `core/fc60_stamp_engine.py` — `FC60StampEngine`

```python
encode(year, month, day, hour=0, minute=0, second=0,
       tz_hours=0, tz_minutes=0, has_time=True) -> Dict
encode_integer(n: int) -> str
decode_stamp(stamp_str: str) -> Dict
```

Returns dict with keys: `fc60`, `iso`, `tz60`, `y60`, `y2k`, `j60`, `mjd60`, `rd60`, `u60`, `chk`,
plus internal `_jdn`, `_weekday_*`, `_planet`, `_domain`, `_half_marker`, `_hour_animal`,
`_minute_token`, `_month_animal`, `_dom_token`.

```python
>>> FC60StampEngine.encode(2026, 2, 6, 1, 15, 0, 8, 0)['fc60']
'VE-OX-OXFI ☀OX-RUWU-RAWU'
```

### 3.6 `personal/numerology_engine.py` — `NumerologyEngine`

```python
digital_root(n: int) -> int                    # reduce to 1-9 or master 11/22/33
life_path(day: int, month: int, year: int) -> int
expression_number(full_name: str, system: str = "pythagorean") -> int
soul_urge(full_name: str, system: str = "pythagorean") -> int
personality_number(full_name: str, system: str = "pythagorean") -> int
personal_year(birth_month: int, birth_day: int, current_year: int) -> int
personal_month(birth_month, birth_day, current_year, current_month) -> int
personal_day(birth_month, birth_day, current_year, current_month, current_day) -> int
complete_profile(full_name, birth_day, birth_month, birth_year,
                 current_year, current_month, current_day,
                 mother_name=None, system="pythagorean", gender=None) -> Dict
```

```python
>>> NumerologyEngine.life_path(15, 7, 1990)
5
>>> NumerologyEngine.expression_number("Alice Johnson")
8
```

### 3.7 `personal/heartbeat_engine.py` — `HeartbeatEngine`

```python
estimated_bpm(age: int) -> int
beats_per_day(bpm: int) -> int
total_lifetime_beats(current_age: int) -> int
rhythm_token(bpm: int) -> str
life_pulse_signature(total_beats: int) -> str
heartbeat_element(bpm: int) -> str             # ELEMENT_NAMES[bpm % 5]
heartbeat_profile(age: int, actual_bpm: int = None) -> Dict
```

```python
>>> HeartbeatEngine.heartbeat_profile(35, actual_bpm=68)
{'bpm': 68, 'bpm_source': 'actual', 'element': 'Earth', ...}
```

### 3.8 `universal/moon_engine.py` — `MoonEngine`

```python
moon_age(jdn: int) -> float                    # days since last new moon
moon_phase(jdn: int) -> Tuple[str, str, float] # (name, emoji, age)
moon_illumination(age: float) -> float          # 0-100%
moon_energy(phase_name: str) -> str             # "Seed","Build",...,"Rest"
full_moon_info(jdn: int) -> Dict               # all of the above + best_for, avoid
```

```python
>>> MoonEngine.full_moon_info(2461078)
{'phase_name': 'Waning Gibbous', 'emoji': '🌖', 'age': 19.05, ...}
```

### 3.9 `universal/ganzhi_engine.py` — `GanzhiEngine`

```python
year_ganzhi(year: int) -> Tuple[int, int]      # (stem_idx, branch_idx)
year_ganzhi_tokens(year: int) -> Tuple[str, str]
day_ganzhi(jdn: int) -> Tuple[int, int]
day_ganzhi_tokens(jdn: int) -> Tuple[str, str]
hour_ganzhi(hour: int, day_stem_idx: int) -> Tuple[int, int]
hour_ganzhi_tokens(hour: int, day_stem_idx: int) -> Tuple[str, str]
full_year_info(year: int) -> Dict              # stem, branch, element, polarity, etc.
full_day_info(jdn: int) -> Dict
```

```python
>>> GanzhiEngine.full_year_info(2026)
{'stem_token': 'BI', 'branch_token': 'HO', 'traditional_name': 'Fire Horse', ...}
```

### 3.10 `universal/location_engine.py` — `LocationEngine`

```python
latitude_element(lat: float) -> str            # "Fire","Earth","Metal","Water","Wood"
hemisphere_polarity(lat: float, lon: float) -> Dict
timezone_estimate(lon: float) -> int           # round(lon / 15)
location_signature(lat: float, lon: float) -> Dict
```

```python
>>> LocationEngine.location_signature(40.7, -74.0)
{'element': 'Metal', 'timezone_estimate': -5, 'lat_hemisphere': 'N', ...}
```

### 3.11 `synthesis/reading_engine.py` — `ReadingEngine`

```python
generate_reading(fc60_stamp: Dict, numerology_profile=None, moon_data=None,
                 ganzhi_data=None, heartbeat_data=None, location_data=None) -> Dict
```

Internal helpers (used by `generate_reading`):

```python
_collect_animals(fc60_stamp, ganzhi_data=None) -> List[str]
_detect_animal_repetitions(animals: List[str]) -> List[Dict]
_time_context(hour: int) -> Dict
_check_sun_moon_paradox(fc60_stamp, hour) -> Optional[str]
_describe_animal_element(dom_token: str) -> str
_personal_x_current(numerology_profile, planet, moon_data) -> List[Dict]
```

Returns dict with: `opening`, `core_signal`, `day_energy`, `moon_context`,
`personal_overlay`, `heartbeat_context`, `location_context`, `year_context`,
`time_context`, `paradox`, `closing`, `signals`, `animal_repetitions`,
`confidence`, `animal_element_description`, `planet_moon_insight`,
`lifepath_year_insight`, `combined_signals`, and more.

### 3.12 `synthesis/signal_combiner.py` — `SignalCombiner`

```python
planet_meets_moon(planet: str, moon_phase: str) -> Dict[str, str]
lifepath_meets_year(life_path: int, personal_year: int) -> Dict[str, str]
animal_harmony(animal1: str, animal2: str) -> Dict[str, str]
combine_signals(signals: List[Dict], numerology: Dict,
                moon: Dict, ganzhi: Dict) -> Dict
```

Data tables: `PLANET_MOON_COMBOS` (56), `LP_PY_COMBOS` (81), `ANIMAL_HARMONY` (36).

```python
>>> SignalCombiner.planet_meets_moon("Venus", "Full Moon")
{'theme': 'Love Illuminated', 'message': '...'}
>>> SignalCombiner.lifepath_meets_year(1, 1)
{'theme': 'Double Ignition', 'message': '...'}
>>> SignalCombiner.animal_harmony("RA", "OX")
{'type': 'harmony', 'meaning': '...'}
```

### 3.13 `synthesis/universe_translator.py` — `UniverseTranslator`

```python
translate(reading: Dict, fc60_stamp: Dict, numerology_profile=None,
          person_name="", current_date_str="",
          confidence_override: Optional[int] = None) -> Dict
```

Returns dict with 9 sections: `header`, `universal_address`, `core_identity`,
`foundation`, `right_now`, `patterns`, `message`, `advice`, `caution`, `footer`,
plus `full_text` (concatenation of all sections).

Description tables: `LIFE_PATH_DESCRIPTIONS` (12), `EXPRESSION_DESCRIPTIONS` (12),
`SOUL_URGE_DESCRIPTIONS` (12), `PERSONALITY_DESCRIPTIONS` (12),
`PERSONAL_YEAR_THEMES` (12).

---

## 4. Test Commands

### Test Suites

```bash
python3 tests/test_all.py                      # 123 unit tests
python3 tests/test_synthesis_deep.py           # 50 signal combiner + description tests
python3 tests/test_integration.py              # 7 end-to-end integration tests
python3 eval/verify_test_vectors.py            # 94 independent math verification checks
python3 eval/test_signal_combiner_coverage.py  # 14 signal combiner coverage checks
```

### Module Self-Tests (125 total across 13 modules)

```bash
python3 core/julian_date_engine.py
python3 core/base60_codec.py
python3 core/weekday_calculator.py
python3 core/checksum_validator.py
python3 core/fc60_stamp_engine.py
python3 personal/numerology_engine.py
python3 personal/heartbeat_engine.py
python3 universal/moon_engine.py
python3 universal/ganzhi_engine.py
python3 universal/location_engine.py
python3 synthesis/reading_engine.py
python3 synthesis/signal_combiner.py
python3 synthesis/universe_translator.py
```

### End-to-End Demo

```bash
python3 synthesis/master_orchestrator.py       # Runs full pipeline with sample data
```

### Grand Total: 413 tests, 0 failures

### Adding New Tests

1. Add test vectors to the module's `TEST_VECTORS` list
2. Add corresponding assertions in the `run_self_test()` / `if __name__` block
3. Add `unittest` cases in the appropriate `tests/test_*.py` file
4. Pattern: each test calls the function with known input and asserts exact output

---

## 5. Coding Standards

- **All public methods are `@staticmethod`** on classes (pure functions, no instance state)
- **Zero external dependencies** — stdlib only (`math`, `datetime`, `typing`, `collections`)
- **Type hints** on all method signatures
- **Functions <= 50 lines**
- **Every module has self-tests** (`if __name__ == "__main__"`) with known test vectors

### Critical Encoding Rules

| Rule           | Detail                                                  |
| -------------- | ------------------------------------------------------- |
| Month indexing | `ANIMALS[month - 1]` — January = RA (index 0)           |
| Hour in stamp  | 2-char `ANIMALS[hour % 12]`, NOT 4-char token60         |
| CHK values     | Uses LOCAL date/time, not UTC-adjusted                  |
| HALF marker    | `☀` (U+2600) if hour < 12, `🌙` (U+1F319) if hour >= 12 |
| Master numbers | Never reduce 11, 22, 33 in `digital_root()`             |

### Signal Priority (from section 12.1)

| Priority   | Signal Type                       |
| ---------- | --------------------------------- |
| Very High  | Repeated animals (3+)             |
| High       | Repeated animals (2)              |
| Medium     | Day planet, Moon phase, DOM token |
| Low-Medium | Hour animal                       |
| Low        | Minute texture                    |
| Background | Year cycle (GZ)                   |
| Variable   | Personal overlays                 |

### Input Priority

`heartbeat > location > time > name > gender > DOB > mother`

---

## 6. Common Errors & Fixes

### 1. Invalid date (Feb 29 on non-leap year)

```python
FC60StampEngine.encode(2025, 2, 29, 0, 0, 0)  # ValueError
```

**Fix:** Validate with `JulianDateEngine.is_valid_date()` before calling.

### 2. Missing timezone defaults to UTC

When `tz_hours`/`tz_minutes` are omitted, the stamp uses UTC. Note this in the reading footer.

### 3. Non-Latin names produce unexpected results

Only A-Z letters are counted. Accented characters, CJK, Arabic, etc. are ignored.
**Fix:** Provide a romanized name; note transliteration in the reading.

### 4. Month off-by-one

`ANIMALS[month]` is WRONG. Must use `ANIMALS[month - 1]` (January = index 0).

### 5. Hour format confusion

Hour animal uses 2-char `ANIMALS[hour % 12]`, NOT 4-char `token60(hour)`.

### 6. Pre-1900 dates degrade moon accuracy

Moon phase uses a synodic approximation anchored to Jan 6, 2000. Error grows ~0.5 days per 100 years from reference. Ganzhi and weekday remain exact.

### 7. Empty name returns 0 for all name-based numbers

```python
NumerologyEngine.expression_number("")  # 0
```

**Fix:** Treat 0 as "no data", not a meaningful number. Confidence drops.

### 8. Conflicting timezone sources

If both explicit `tz_hours` and location coordinates are provided, the explicit timezone wins. `LocationEngine.timezone_estimate()` is an approximation.

### 9. Missing optional data degrades gracefully

| Missing         | Confidence Impact | Effect                        |
| --------------- | ----------------: | ----------------------------- |
| Mother's name   |              -10% | No mother influence           |
| Gender          |                0% | No polarity overlay           |
| Location        |               -5% | No location element/TZ        |
| Heartbeat / BPM |               -5% | Uses age-based estimate       |
| Current time    |               -5% | No hour animal, minute token  |
| Timezone        |                0% | Defaults UTC, noted in footer |

### 10. Master numbers must never be reduced

`digital_root()` preserves 11, 22, 33. If you write custom reduction logic, check for master numbers first.

### Self-Diagnostic Checklist

1. Run `python3 tests/test_all.py` — all 123 pass?
2. Run `python3 synthesis/master_orchestrator.py` — demo completes without error?
3. Check that `ANIMALS[month - 1]` is used (not `ANIMALS[month]`) in any new code
4. Verify CHK uses local values, not UTC-adjusted
5. Confirm `HALF` marker uses `☀` / `🌙`, not ASCII substitutes

---

## 7. How to Add a New Module

### Step 1: Choose the tier

- **core/** — Pure math, no dependencies on other tiers
- **personal/** — Requires person-specific input (name, DOB, biometrics)
- **universal/** — Requires date/location but not person-specific data
- **synthesis/** — Combines outputs from other tiers

### Step 2: Create the file

```python
"""
Module Name - [Tier] Tier Module
================================
Purpose: One-line description
Dependencies: List what it imports
"""

from typing import Dict  # stdlib only!


class MyEngine:
    """One-line class docstring."""

    @staticmethod
    def my_method(param: int) -> str:
        """Docstring with Args/Returns."""
        # implementation (<= 50 lines)
        return result
```

### Step 3: Add self-tests

```python
TEST_VECTORS = [
    (input1, expected_output1),
    (input2, expected_output2),
]

if __name__ == "__main__":
    passed = failed = 0
    for inp, expected in TEST_VECTORS:
        result = MyEngine.my_method(inp)
        if result == expected:
            passed += 1
        else:
            failed += 1
    print(f"{passed} passed, {failed} failed")
```

### Step 4: Add unittest cases

Create or extend a file in `tests/` following the existing pattern.

### Step 5: Integrate with MasterOrchestrator

1. Add `from <tier>.my_engine import MyEngine` to `master_orchestrator.py`
2. Add a pipeline step (e.g., between steps 7 and 8)
3. Pass the output to `ReadingEngine.generate_reading()` as a new parameter
4. Add the result to the return dict

### Step 6: Update documentation

Add the module to `CLAUDE.md` architecture section and this API reference.

### Step 7: Verify

```bash
python3 <tier>/my_engine.py          # Self-test passes
python3 tests/test_all.py            # Existing tests unaffected
python3 synthesis/master_orchestrator.py  # Demo still works
```

---

## 8. Eval Results Summary

**Final Score:** 116 / 120 (96.7%) — **Grade A**

### Test Coverage

| Suite                                   |   Tests |  Passed | Failed |
| --------------------------------------- | ------: | ------: | -----: |
| `tests/test_all.py`                     |     123 |     123 |      0 |
| `tests/test_synthesis_deep.py`          |      50 |      50 |      0 |
| `tests/test_integration.py`             |       7 |       7 |      0 |
| `eval/verify_test_vectors.py`           |      94 |      94 |      0 |
| `eval/test_signal_combiner_coverage.py` |      14 |      14 |      0 |
| Module self-tests (13 modules)          |     125 |     125 |      0 |
| **Grand Total**                         | **413** | **413** |  **0** |

### Content Completeness: 100%

All combinatorial tables fully populated: 56 planet-moon combos, 81 LP-PY combos, 60 animal-element descriptions, 12 each of Life Path / Expression / Soul Urge / Personality / Personal Year descriptions.

### Structural Health

- 14/14 modules execute without errors
- Stdlib-only imports (zero external dependencies)
- No circular imports
- `@staticmethod` convention on all 14 classes

### Known Gaps (4 deferred, all MEDIUM/LOW)

| Gap     | Severity | Issue                                        |
| ------- | -------- | -------------------------------------------- |
| GAP-004 | MEDIUM   | logic/00 word count 1,345 vs 1,500 target    |
| GAP-005 | MEDIUM   | Synthesis ~573 words vs 800-word target      |
| GAP-006 | MEDIUM   | No low-confidence addendum for readings <65% |
| GAP-007 | LOW      | Sample readings share Life Path 5            |
