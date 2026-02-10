# SESSION 9 SPEC — Framework Integration: Signal Processing & Patterns

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 7 (reading types + `UserProfile`, `ReadingResult` models), Session 6 (framework bridge)

---

## TL;DR

- Create `PatternFormatter` class that extracts raw patterns from framework output and formats them for three consumers: AI prompts, frontend display, and database storage
- Implement signal priority ordering per the framework's 9-level hierarchy (repeated animals 3+ → Very High, down to personal overlays → Variable)
- Map confidence scores (0-100) to UI indicator data (color, icon, label, progress bar width)
- Integrate pattern formatting into `framework_bridge.py` so every reading automatically includes formatted patterns
- Write 15+ tests covering pattern extraction, priority ordering, empty patterns, confidence mapping, and all three output formats

---

## OBJECTIVES

1. **Create `PatternFormatter`** — a stateless class with `@staticmethod` methods that takes raw `reading['patterns']['detected']` and `reading['confidence']` from the framework and produces structured output for three consumers
2. **Implement signal priority sorting** — sort patterns by the framework's 9-level priority hierarchy, highest first, with stable sub-ordering by occurrence count
3. **Format patterns for AI** — produce a priority-ordered text block suitable for injection into AI system prompts, including signal descriptions and their significance levels
4. **Format patterns for frontend** — produce display-ready dicts with badge text, color codes, importance indicators, and tooltip descriptions for React components
5. **Format patterns for database** — produce a compact JSONB-ready dict (`patterns_summary`) with pattern types, counts, and confidence score for storage in `reading_result`
6. **Map confidence to UI indicators** — convert `score` (0-100) and `level` (low/medium/high/very_high) to visual properties (color, icon, label, progress width)
7. **Integrate into bridge** — modify `framework_bridge.py` so `generate_single_reading()` and all typed reading functions automatically include formatted patterns in their output

---

## PREREQUISITES

- [ ] Session 6 completed — `services/oracle/oracle_service/framework_bridge.py` exists and is importable
- [ ] Session 7 completed — `services/oracle/oracle_service/models/reading_types.py` exists with `ReadingResult` dataclass
- [ ] Framework is importable: `from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator`
- Verification:
  ```bash
  test -f services/oracle/oracle_service/framework_bridge.py && echo "Bridge OK"
  python3 -c "from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator; print('Framework OK')"
  python3 -c "from numerology_ai_framework.synthesis.signal_combiner import SignalCombiner; print('SignalCombiner OK')"
  python3 -c "from numerology_ai_framework.synthesis.reading_engine import ReadingEngine; print('ReadingEngine OK')"
  ```

**Note on Sessions 6-8:** Session 6 creates the bridge, Session 7 adds reading types and `UserProfile`/`ReadingResult` models, Session 8 adds numerology system selection. Session 9 is independent of Session 8 — it works with the pattern data that the framework produces regardless of which numerology system was selected. If Sessions 6-7 are not yet complete, the bridge and model references in this spec should be adapted to match whatever exists.

---

## FILES TO CREATE

| Path                                                  | Purpose                                                                                                                                                                   |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/oracle/oracle_service/pattern_formatter.py` | **NEW** — `PatternFormatter` class: extracts, sorts, and formats patterns for AI / frontend / database; `ConfidenceMapper` class: maps confidence scores to UI indicators |
| `services/oracle/tests/test_pattern_formatter.py`     | **NEW** — 15+ tests for pattern formatting, priority ordering, edge cases, and confidence mapping                                                                         |

## FILES TO MODIFY

| Path                                                 | Change                                                                                                                                                        |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `services/oracle/oracle_service/framework_bridge.py` | Add `_format_patterns()` call inside `generate_single_reading()` and typed reading functions; include `patterns_formatted` and `confidence_ui` keys in output |

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: Understand Framework Pattern Output (~20 min)

**Tasks:**

1. Study the framework's pattern output structure by examining `MasterOrchestrator._detect_patterns()` (at `numerology_ai_framework/synthesis/master_orchestrator.py:241`). It returns:

   ```python
   {
       "detected": [
           {
               "type": "number_repetition" | "master_number" | "animal_repetition",
               "number": int,           # for number patterns
               "animal": str,           # for animal patterns (e.g., "Ox")
               "occurrences": int,      # count of repetitions
               "strength": "very_high" | "high" | "medium",
               "message": str,          # human-readable description
           },
           ...
       ],
       "count": int
   }
   ```

2. Study the framework's `ReadingEngine.generate_reading()` signals list (at `numerology_ai_framework/synthesis/reading_engine.py:292`). Each signal dict has:

   ```python
   {
       "type": "animal_repetition" | "day_planet" | "moon_phase" | "dom_animal_element" | "hour_animal",
       "priority": "Very High" | "High" | "Medium" | "Low-Medium" | "Low" | "Background",
       "message": str,
   }
   ```

3. Study the framework's `SignalCombiner.combine_signals()` output (at `numerology_ai_framework/synthesis/signal_combiner.py:942`):

   ```python
   {
       "primary_message": str,
       "supporting_messages": List[str],   # up to 3
       "tensions": List[str],              # element/animal clashes
       "recommended_actions": List[str],   # always 3 items
   }
   ```

4. Study the confidence output from `MasterOrchestrator._calculate_confidence()` (at `numerology_ai_framework/synthesis/master_orchestrator.py:296`):

   ```python
   {
       "score": int,      # 50-95
       "level": str,      # "low" | "medium" | "high" | "very_high"
       "factors": str,    # e.g., "Based on 5 data sources"
   }
   ```

**Checkpoint:**

- [ ] Framework pattern structure understood — know exactly which keys to extract
- [ ] Signal priority hierarchy memorized (9 levels from framework's CLAUDE.md)
- [ ] Confidence score range and level thresholds documented

🚨 STOP if framework output structure is unclear — re-read `master_orchestrator.py` and `reading_engine.py` before proceeding

---

### Phase 2: Create PatternFormatter Class (~90 min)

**Tasks:**

1. Create `services/oracle/oracle_service/pattern_formatter.py` with the following structure:

   ```python
   """
   Pattern Formatter — Signal Processing & Pattern Visualization
   =============================================================
   Extracts patterns from framework output and formats them for:
   - AI prompt context (priority-ordered text)
   - Frontend display (badges, colors, indicators)
   - Database storage (compact JSONB summary)
   """

   from typing import Dict, List, Optional


   class PatternFormatter:
       """Format framework patterns for AI, frontend, and database consumers."""

       # Signal priority hierarchy from framework CLAUDE.md §12.1
       PRIORITY_RANK: Dict[str, int] = {
           "Very High": 9,
           "High": 8,
           "Medium": 6,
           "Low-Medium": 4,
           "Low": 3,
           "Background": 1,
           "Variable": 2,
       }

       # Pattern strength to priority mapping
       STRENGTH_TO_PRIORITY: Dict[str, str] = {
           "very_high": "Very High",
           "high": "High",
           "medium": "Medium",
           "low": "Low",
       }

       # Element colors for frontend display
       ELEMENT_COLORS: Dict[str, str] = {
           "Fire": "#DC2626",    # red-600
           "Water": "#2563EB",   # blue-600
           "Wood": "#16A34A",    # green-600
           "Metal": "#D97706",   # amber-600 (gold)
           "Earth": "#92400E",   # amber-800 (brown)
       }

       # Priority badge colors for frontend
       PRIORITY_COLORS: Dict[str, str] = {
           "Very High": "#DC2626",  # red
           "High": "#EA580C",       # orange
           "Medium": "#CA8A04",     # yellow
           "Low-Medium": "#2563EB", # blue
           "Low": "#6B7280",        # gray
           "Background": "#9CA3AF", # light gray
           "Variable": "#7C3AED",   # purple
       }

       @staticmethod
       def sort_by_priority(signals: List[Dict]) -> List[Dict]:
           ...

       @staticmethod
       def format_for_ai(
           patterns: Dict,
           signals: List[Dict],
           combined_signals: Optional[Dict] = None,
       ) -> str:
           ...

       @staticmethod
       def format_for_frontend(
           patterns: Dict,
           signals: List[Dict],
           confidence: Dict,
       ) -> Dict:
           ...

       @staticmethod
       def format_for_database(
           patterns: Dict,
           confidence: Dict,
       ) -> Dict:
           ...
   ```

2. **`sort_by_priority(signals)`** — takes the `reading['reading']['signals']` list and returns it sorted by `PRIORITY_RANK` (highest first). Within same priority, sort by occurrence count if available, else stable order. Returns a new sorted list (does not mutate input).

3. **`format_for_ai(patterns, signals, combined_signals=None)`** — produces a multi-line string for AI system prompt injection:

   ```
   === PATTERN ANALYSIS ===

   DETECTED PATTERNS (3):
   [Very High] The Ox appears 3 times — Patience and steady endurance. The instruction: Stay the course.
   [High] The number 7 appears 2 times — major theme
   [Medium] Life Path 7 is a Master Number — heightened spiritual potential

   SIGNAL SUMMARY:
   Primary: Ox appears 3 times — endurance is key.
   Supporting: This is a Venus day, governing love and beauty.
   Supporting: The moon is 🌒 Waxing Crescent (age 4 days).

   TENSIONS:
   - Fire and Water oppose — passion and depth struggle for dominance.

   RECOMMENDED ACTIONS:
   1. Pay attention to the repeated pattern — it is the loudest signal.
   2. Your Life Path asks you to...
   3. The moon says this time is best for: reflection.

   CONFIDENCE: 80% (high) — Based on 5 data sources
   ```

   If `combined_signals` is `None`, skip the SIGNAL SUMMARY / TENSIONS / ACTIONS sections. If `patterns['detected']` is empty, output: `"No specific patterns detected — all numbers and animals are unique in this reading."`

4. **`format_for_frontend(patterns, signals, confidence)`** — produces a dict structured for React components:

   ```python
   {
       "patterns": [
           {
               "type": "animal_repetition",
               "badge_text": "Ox ×3",
               "badge_color": "#DC2626",     # Very High = red
               "priority": "Very High",
               "priority_rank": 9,
               "description": "The Ox appears 3 times — Patience and steady endurance.",
               "tooltip": "Repeated animals (3+) are the strongest signal in a reading.",
               "icon": "repeat",             # icon hint for frontend
           },
           ...
       ],
       "signal_count": 5,
       "pattern_count": 3,
       "has_tensions": True,
       "tensions": ["Fire and Water oppose..."],
       "recommended_actions": ["Pay attention...", "Your Life Path...", "The moon says..."],
       "primary_signal": "Ox appears 3 times — endurance is key.",
   }
   ```

   Badge text format:
   - `animal_repetition`: `"{AnimalName} ×{count}"`
   - `number_repetition`: `"#{number} ×{count}"`
   - `master_number`: `"Master {number}"`

   Tooltip text based on pattern type:
   - `animal_repetition` count >= 3: `"Repeated animals (3+) are the strongest signal in a reading."`
   - `animal_repetition` count == 2: `"Repeated animals (2) are a strong signal."`
   - `number_repetition`: `"The same number appearing multiple times amplifies its significance."`
   - `master_number`: `"Master Numbers carry heightened spiritual and creative energy."`

5. **`format_for_database(patterns, confidence)`** — produces a compact dict for JSONB storage in `reading_result`:

   ```python
   {
       "patterns_summary": {
           "count": 3,
           "types": ["animal_repetition", "number_repetition", "master_number"],
           "strongest": {
               "type": "animal_repetition",
               "detail": "Ox ×3",
               "strength": "very_high",
           },
           "all": [
               {"type": "animal_repetition", "detail": "Ox ×3", "strength": "very_high"},
               {"type": "number_repetition", "detail": "#7 ×2", "strength": "high"},
               ...
           ],
       },
       "confidence_score": 80,
       "confidence_level": "high",
   }
   ```

   If no patterns detected: `{"patterns_summary": {"count": 0, "types": [], "strongest": None, "all": []}, "confidence_score": ..., "confidence_level": ...}`

**Checkpoint:**

- [ ] `PatternFormatter.sort_by_priority()` sorts signals correctly (Very High first)
- [ ] `PatternFormatter.format_for_ai()` returns non-empty string for sample input
- [ ] `PatternFormatter.format_for_frontend()` returns dict with all required keys
- [ ] `PatternFormatter.format_for_database()` returns compact JSONB-ready dict
- Verify:
  ```bash
  cd services/oracle && python3 -c "
  from oracle_service.pattern_formatter import PatternFormatter
  test_patterns = {'detected': [{'type': 'animal_repetition', 'animal': 'Ox', 'occurrences': 3, 'strength': 'very_high', 'message': 'Ox appears 3 times'}], 'count': 1}
  test_signals = [{'type': 'animal_repetition', 'priority': 'Very High', 'message': 'Ox appears 3 times'}]
  test_confidence = {'score': 80, 'level': 'high', 'factors': 'Based on 5 data sources'}
  ai = PatternFormatter.format_for_ai(test_patterns, test_signals)
  fe = PatternFormatter.format_for_frontend(test_patterns, test_signals, test_confidence)
  db = PatternFormatter.format_for_database(test_patterns, test_confidence)
  print(f'AI output: {len(ai)} chars')
  print(f'Frontend patterns: {len(fe[\"patterns\"])} items')
  print(f'DB summary count: {db[\"patterns_summary\"][\"count\"]}')
  print('PatternFormatter OK')
  "
  ```

🚨 STOP if PatternFormatter doesn't produce correct output for the sample data

---

### Phase 3: Create ConfidenceMapper Class (~30 min)

**Tasks:**

1. Add `ConfidenceMapper` class to `services/oracle/oracle_service/pattern_formatter.py`:

   ```python
   class ConfidenceMapper:
       """Map framework confidence scores to UI-ready indicator data."""

       LEVEL_CONFIG: Dict[str, Dict] = {
           "very_high": {
               "color": "#16A34A",        # green-600
               "bg_color": "#DCFCE7",     # green-100
               "icon": "shield-check",
               "label_en": "Very High Confidence",
               "label_fa": "اطمینان بسیار بالا",
           },
           "high": {
               "color": "#2563EB",        # blue-600
               "bg_color": "#DBEAFE",     # blue-100
               "icon": "check-circle",
               "label_en": "High Confidence",
               "label_fa": "اطمینان بالا",
           },
           "medium": {
               "color": "#CA8A04",        # yellow-600
               "bg_color": "#FEF9C3",     # yellow-100
               "icon": "info-circle",
               "label_en": "Medium Confidence",
               "label_fa": "اطمینان متوسط",
           },
           "low": {
               "color": "#DC2626",        # red-600
               "bg_color": "#FEE2E2",     # red-100
               "icon": "alert-triangle",
               "label_en": "Low Confidence",
               "label_fa": "اطمینان پایین",
           },
       }

       @staticmethod
       def map_to_ui(confidence: Dict) -> Dict:
           ...
   ```

2. **`map_to_ui(confidence)`** — takes `reading['confidence']` dict and returns:

   ```python
   {
       "score": 80,
       "level": "high",
       "factors": "Based on 5 data sources",
       "color": "#2563EB",
       "bg_color": "#DBEAFE",
       "icon": "check-circle",
       "label_en": "High Confidence",
       "label_fa": "اطمینان بالا",
       "progress_width": 80,             # percentage for CSS width
       "progress_color": "#2563EB",      # same as color
       "caveat_en": "",                  # empty for high/very_high
       "caveat_fa": "",
   }
   ```

   Caveats (only for low/medium):
   - `low`: `"This reading is based on limited data. Add more personal information for deeper insight."`
   - `medium`: `"Good confidence level. Adding optional data (mother's name, location, heart rate) would increase accuracy."`
   - `high` / `very_high`: empty string

3. Handle edge case: if `confidence` dict is missing keys, use defaults: `score=50`, `level="low"`, `factors="Insufficient data"`.

**Checkpoint:**

- [ ] `ConfidenceMapper.map_to_ui()` returns dict with all required keys
- [ ] Low confidence returns caveat text
- [ ] High confidence returns empty caveat
- [ ] Persian labels present and correct
- Verify:
  ```bash
  cd services/oracle && python3 -c "
  from oracle_service.pattern_formatter import ConfidenceMapper
  low = ConfidenceMapper.map_to_ui({'score': 55, 'level': 'low', 'factors': 'Based on 2 data sources'})
  high = ConfidenceMapper.map_to_ui({'score': 85, 'level': 'very_high', 'factors': 'Based on 6 data sources'})
  print(f'Low: color={low[\"color\"]}, caveat={low[\"caveat_en\"][:30]}...')
  print(f'High: color={high[\"color\"]}, caveat=\"{high[\"caveat_en\"]}\"')
  print('ConfidenceMapper OK')
  "
  ```

🚨 STOP if ConfidenceMapper returns incorrect colors or missing keys

---

### Phase 4: Integrate into Framework Bridge (~60 min)

**Tasks:**

1. Modify `services/oracle/oracle_service/framework_bridge.py` to import and use `PatternFormatter` and `ConfidenceMapper`:

   ```python
   from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper
   ```

2. Add a private `_enrich_with_patterns()` function (or method) that takes a raw framework `reading` dict and returns enriched data:

   ```python
   def _enrich_with_patterns(framework_output: Dict) -> Dict:
       """Add formatted pattern data and confidence UI mapping to framework output.

       Args:
           framework_output: Raw dict from MasterOrchestrator.generate_reading()

       Returns:
           Dict with added keys: 'patterns_formatted', 'confidence_ui', 'patterns_db'
       """
       patterns = framework_output.get("patterns", {"detected": [], "count": 0})
       signals = framework_output.get("reading", {}).get("signals", [])
       combined = framework_output.get("reading", {}).get("combined_signals")
       confidence = framework_output.get("confidence", {"score": 50, "level": "low"})

       return {
           "patterns_ai": PatternFormatter.format_for_ai(patterns, signals, combined),
           "patterns_frontend": PatternFormatter.format_for_frontend(patterns, signals, confidence),
           "patterns_db": PatternFormatter.format_for_database(patterns, confidence),
           "confidence_ui": ConfidenceMapper.map_to_ui(confidence),
       }
   ```

3. Modify `generate_single_reading()` (and whatever equivalent the bridge provides) to call `_enrich_with_patterns()` and merge the result into the `ReadingResult.framework_output` dict:

   ```python
   def generate_single_reading(...) -> ReadingResult:
       ...
       raw_output = MasterOrchestrator.generate_reading(**kwargs)
       pattern_data = _enrich_with_patterns(raw_output)
       raw_output.update(pattern_data)
       ...
   ```

4. Ensure all 5 typed reading functions from Session 7 (`generate_time_reading`, `generate_name_reading`, `generate_question_reading`, `generate_daily_reading`, `generate_multi_user_reading`) also include pattern enrichment. If they call `generate_single_reading()` internally, this happens automatically. If they call `MasterOrchestrator` directly, add the `_enrich_with_patterns()` call.

5. For multi-user readings: each individual reading gets its own pattern formatting. The group-level `MultiUserResult` should also include a `group_patterns_summary` that aggregates pattern types across all users (e.g., "3 of 4 users have animal repetitions").

**Checkpoint:**

- [ ] `generate_single_reading()` output includes `patterns_ai`, `patterns_frontend`, `patterns_db`, and `confidence_ui` keys
- [ ] Pattern data is populated correctly for a sample reading
- [ ] All typed reading functions include pattern enrichment
- Verify:
  ```bash
  cd services/oracle && python3 -c "
  import oracle_service
  from oracle_service.framework_bridge import generate_single_reading
  result = generate_single_reading('Test User', 1, 1, 2000)
  output = result.framework_output if hasattr(result, 'framework_output') else result
  assert 'patterns_ai' in output, 'Missing patterns_ai'
  assert 'patterns_frontend' in output, 'Missing patterns_frontend'
  assert 'patterns_db' in output, 'Missing patterns_db'
  assert 'confidence_ui' in output, 'Missing confidence_ui'
  print(f'Pattern count: {output[\"patterns_frontend\"][\"pattern_count\"]}')
  print(f'Confidence: {output[\"confidence_ui\"][\"score\"]}% ({output[\"confidence_ui\"][\"level\"]})')
  print('Bridge integration OK')
  "
  ```

🚨 STOP if bridge output is missing any of the 4 pattern/confidence keys

---

### Phase 5: Write Tests (~90 min)

**Tasks:**

Create `services/oracle/tests/test_pattern_formatter.py` with the following test structure:

```python
"""Tests for PatternFormatter and ConfidenceMapper."""

import pytest
from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper


# ─── Test Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def sample_patterns_with_animals():
    """Patterns dict with animal repetitions."""
    ...

@pytest.fixture
def sample_patterns_with_numbers():
    """Patterns dict with number repetitions and master numbers."""
    ...

@pytest.fixture
def empty_patterns():
    """Patterns dict with no detections."""
    return {"detected": [], "count": 0}

@pytest.fixture
def sample_signals():
    """Signals list from ReadingEngine."""
    ...

@pytest.fixture
def sample_confidence_high():
    """High confidence dict."""
    return {"score": 85, "level": "very_high", "factors": "Based on 6 data sources"}

@pytest.fixture
def sample_confidence_low():
    """Low confidence dict."""
    return {"score": 55, "level": "low", "factors": "Based on 2 data sources"}

@pytest.fixture
def sample_combined_signals():
    """Combined signals from SignalCombiner."""
    ...
```

**Test list — see Tests to Write table below for all 18 tests.**

Run all tests:

```bash
cd services/oracle && python3 -m pytest tests/test_pattern_formatter.py -v --tb=short
```

**Checkpoint:**

- [ ] All 18 tests pass
- [ ] No import errors
- [ ] Tests cover all 3 format outputs + confidence mapping + edge cases

🚨 STOP if any tests fail — fix before proceeding

---

### Phase 6: Integration Smoke Test (~20 min)

**Tasks:**

1. Run a full end-to-end reading through the bridge and verify pattern data flows through:

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service
   from oracle_service.framework_bridge import generate_single_reading
   from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper

   # Generate a reading with data that produces patterns
   result = generate_single_reading(
       'Alice Johnson', 15, 7, 1990,
       mother_name='Barbara Johnson',
       gender='female',
       latitude=40.7, longitude=-74.0,
       actual_bpm=68,
   )

   output = result.framework_output if hasattr(result, 'framework_output') else result

   # Verify AI format
   ai_text = output.get('patterns_ai', '')
   assert len(ai_text) > 0, 'AI format is empty'
   assert 'CONFIDENCE' in ai_text, 'AI format missing confidence section'

   # Verify frontend format
   fe = output.get('patterns_frontend', {})
   assert 'patterns' in fe, 'Frontend format missing patterns list'
   assert 'signal_count' in fe, 'Frontend format missing signal_count'

   # Verify DB format
   db = output.get('patterns_db', {})
   assert 'patterns_summary' in db, 'DB format missing patterns_summary'
   assert 'confidence_score' in db, 'DB format missing confidence_score'

   # Verify confidence UI
   cui = output.get('confidence_ui', {})
   assert 'color' in cui, 'Confidence UI missing color'
   assert 'label_fa' in cui, 'Confidence UI missing Persian label'

   print(f'E2E: {fe[\"pattern_count\"]} patterns, {fe[\"signal_count\"]} signals')
   print(f'Confidence: {cui[\"score\"]}% ({cui[\"level\"]})')
   print(f'AI text length: {len(ai_text)} chars')
   print('E2E smoke test PASSED')
   "
   ```

2. Verify existing framework tests still pass:

   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py
   ```

3. Verify existing bridge tests still pass (from Session 6):

   ```bash
   cd services/oracle && python3 -m pytest tests/test_framework_bridge.py -v --tb=short 2>/dev/null || echo "Bridge tests not yet present — OK if Sessions 6-7 not complete"
   ```

**Checkpoint:**

- [ ] E2E smoke test passes
- [ ] Framework 180 tests still pass (no regressions)
- [ ] Existing bridge tests still pass (if present)

🚨 STOP if any regressions

---

### Phase 7: Final Verification (~15 min)

**Tasks:**

1. Run the full test suite for this session:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_pattern_formatter.py -v --tb=short
   ```

2. Verify no import errors across the oracle service:

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service
   from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper
   print('All imports OK')
   "
   ```

3. Check code quality:

   ```bash
   cd services/oracle && python3 -m py_compile oracle_service/pattern_formatter.py && echo "Compiles OK"
   ```

4. Verify the file structure is clean:

   ```bash
   ls -la services/oracle/oracle_service/pattern_formatter.py
   ls -la services/oracle/tests/test_pattern_formatter.py
   ```

**Checkpoint:**

- [ ] All 18 tests pass
- [ ] All imports resolve
- [ ] File compiles without errors
- [ ] Two new files exist at expected paths

---

## TESTS TO WRITE

| Path                                              | Function Name                                    | Description                                                                           |
| ------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `services/oracle/tests/test_pattern_formatter.py` | `test_sort_by_priority_orders_correctly`         | Very High signals appear before Medium before Low                                     |
| `services/oracle/tests/test_pattern_formatter.py` | `test_sort_by_priority_stable_within_same_level` | Same-priority signals maintain original order                                         |
| `services/oracle/tests/test_pattern_formatter.py` | `test_sort_by_priority_empty_list`               | Empty signal list returns empty list                                                  |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_ai_with_patterns`               | AI output includes DETECTED PATTERNS section with correct count                       |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_ai_empty_patterns`              | AI output includes "No specific patterns detected" message                            |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_ai_with_combined_signals`       | AI output includes SIGNAL SUMMARY, TENSIONS, and ACTIONS sections                     |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_ai_without_combined_signals`    | AI output skips SIGNAL SUMMARY section when `combined_signals=None`                   |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_frontend_badge_text_animal`     | Animal repetition badge = "Ox ×3"                                                     |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_frontend_badge_text_number`     | Number repetition badge = "#7 ×2"                                                     |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_frontend_badge_text_master`     | Master number badge = "Master 11"                                                     |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_frontend_has_required_keys`     | Frontend dict has patterns, signal_count, pattern_count, has_tensions, primary_signal |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_frontend_empty_patterns`        | Returns `pattern_count=0`, `patterns=[]`, `has_tensions=False`                        |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_database_structure`             | DB dict has `patterns_summary` with count, types, strongest, all                      |
| `services/oracle/tests/test_pattern_formatter.py` | `test_format_for_database_empty_patterns`        | DB dict has `count=0`, `strongest=None`, `types=[]`                                   |
| `services/oracle/tests/test_pattern_formatter.py` | `test_confidence_mapper_high`                    | High confidence returns green/blue color, empty caveat                                |
| `services/oracle/tests/test_pattern_formatter.py` | `test_confidence_mapper_low`                     | Low confidence returns red color, non-empty caveat                                    |
| `services/oracle/tests/test_pattern_formatter.py` | `test_confidence_mapper_persian_labels`          | All levels have non-empty `label_fa`                                                  |
| `services/oracle/tests/test_pattern_formatter.py` | `test_confidence_mapper_missing_keys`            | Missing confidence dict keys use defaults (score=50, level=low)                       |

**Total: 18 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] `pattern_formatter.py` exists at `services/oracle/oracle_service/pattern_formatter.py`
- [ ] `PatternFormatter` class has 4 public static methods: `sort_by_priority`, `format_for_ai`, `format_for_frontend`, `format_for_database`
- [ ] `ConfidenceMapper` class has 1 public static method: `map_to_ui`
- [ ] Signal priority ordering follows framework's 9-level hierarchy
- [ ] AI format is a readable text block suitable for prompt injection
- [ ] Frontend format includes badge_text, badge_color, tooltip, priority_rank for each pattern
- [ ] Database format is compact JSONB-ready dict with patterns_summary and confidence_score
- [ ] Confidence UI includes both English and Persian labels (`label_en`, `label_fa`)
- [ ] Confidence UI includes caveat text for low/medium levels, empty for high/very_high
- [ ] `framework_bridge.py` enriches every reading with `patterns_ai`, `patterns_frontend`, `patterns_db`, `confidence_ui`
- [ ] All 18 tests pass: `cd services/oracle && python3 -m pytest tests/test_pattern_formatter.py -v`
- [ ] Framework 180 tests still pass (no regressions)
- [ ] Zero import errors: `python3 -c "from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper"`
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_pattern_formatter.py -v --tb=short && echo "TESTS OK"
  cd services/oracle && python3 -c "from oracle_service.pattern_formatter import PatternFormatter, ConfidenceMapper; print('IMPORTS OK')"
  cd numerology_ai_framework && python3 tests/test_all.py && echo "FRAMEWORK OK"
  ```

---

## ERROR SCENARIOS

| Scenario                                                                                      | Expected Behavior                                                                           | Recovery                                                                                |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Framework output missing `patterns` key                                                       | `PatternFormatter` uses default `{"detected": [], "count": 0}` — never crashes              | Add `.get("patterns", {"detected": [], "count": 0})` guard in `_enrich_with_patterns()` |
| Framework output missing `reading.signals` key                                                | `format_for_ai` and `format_for_frontend` produce empty/minimal output                      | Guard with `.get("reading", {}).get("signals", [])`                                     |
| `combined_signals` is `None` (framework didn't load SignalCombiner)                           | AI format skips SIGNAL SUMMARY section; frontend omits `tensions` and `recommended_actions` | Check for `None` before accessing combined signal fields                                |
| Pattern has unknown `type` not in badge text mapping                                          | Use type string directly as badge text (e.g., `"unknown_type"`)                             | Add a default case in badge text generation                                             |
| Confidence dict has unexpected `level` value                                                  | `ConfidenceMapper` falls back to `"low"` config                                             | Default to `LEVEL_CONFIG["low"]` when level not found                                   |
| `confidence['score']` is `None` or missing                                                    | Use default `score=50`                                                                      | Guard with `.get("score", 50)`                                                          |
| Pattern `occurrences` is missing from pattern dict                                            | Badge text omits count (e.g., just "Ox" instead of "Ox ×3")                                 | Guard with `.get("occurrences", 0)` and skip `×N` when 0                                |
| Multiple patterns have same priority — ordering ambiguous                                     | Stable sort preserves original framework ordering                                           | Use `sorted()` with `key=` (Python's sort is stable)                                    |
| Reading has no animal repetitions but has number repetitions                                  | Only number badges shown; animal section empty                                              | All format methods handle mixed pattern types independently                             |
| Bridge integration fails because `generate_single_reading` signature changed between sessions | `ImportError` or `TypeError` at integration point                                           | Check current bridge function signature; adapt `_enrich_with_patterns` call accordingly |

---

## HANDOFF

**Created:**

- `services/oracle/oracle_service/pattern_formatter.py` — `PatternFormatter` (4 static methods) + `ConfidenceMapper` (1 static method)
- `services/oracle/tests/test_pattern_formatter.py` — 18+ tests

**Modified:**

- `services/oracle/oracle_service/framework_bridge.py` — added `_enrich_with_patterns()` integration; all reading functions now include pattern and confidence UI data in output

**Deleted:**

- None

**Next session (Session 10) receives:**

- Every reading from the bridge now includes `patterns_ai` (text for AI prompts), `patterns_frontend` (display-ready data for React), `patterns_db` (compact JSONB for storage), and `confidence_ui` (color/icon/label/caveat mapping)
- `PatternFormatter` is importable and usable standalone: `from oracle_service.pattern_formatter import PatternFormatter`
- `ConfidenceMapper` provides bilingual (EN/FA) confidence indicator data ready for frontend consumption
- Signal priority ordering is established — patterns always appear highest-priority first
- The `reading_result` JSONB column in `oracle_readings` can now store `patterns_db` output for historical pattern tracking
