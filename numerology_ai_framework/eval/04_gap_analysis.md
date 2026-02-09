# FC60 Numerology AI Framework — Gap Analysis

**Date:** 2026-02-09
**Auditor:** Claude Opus 4.6 (automated)
**Sources:** `01_structural_audit.md`, `02_math_verification.md`, `03_depth_quality_audit.md`

---

## Summary

| Severity  | Count | Status         |
| --------- | ----: | -------------- |
| CRITICAL  |     1 | Fix in Phase D |
| HIGH      |     2 | Fix in Phase D |
| MEDIUM    |     3 | DEFERRED       |
| LOW       |     1 | DEFERRED       |
| **Total** | **7** |                |

---

## GAP-001: Confidence Score Discrepancy Between Orchestrator and Synthesis Text

**Severity:** CRITICAL
**Files:** `synthesis/universe_translator.py` (line 106), `synthesis/reading_engine.py` (line 489), `synthesis/master_orchestrator.py` (lines 292-349)

**What's wrong:** Two independent confidence calculations exist:

1. `ReadingEngine.generate_reading()` calculates `min(95, 50 + len(signals) * 5)` — a signal-count-based heuristic. For a full-data reading with 6 signals, this gives 80%. This value is stored in `reading["confidence"]`.
2. `MasterOrchestrator._calculate_confidence()` calculates based on data source availability (base 50 + 10 numerology + 10 mother + 5 moon + 5 ganzhi + 5 heartbeat + 5 location + 5 repetitions = 95%). This is stored in the top-level `result["confidence"]["score"]`.

The `UniverseTranslator.translate()` reads `reading.get("confidence", 50)` on line 106, which gets the reading_engine's lower number. The synthesis text therefore reports 80% while the structured data correctly reports 95%.

**What should be there:** A single, unified confidence score. The orchestrator's data-source-based calculation is more accurate and should be the canonical value. The universe_translator should receive and use the orchestrator's confidence, not the reading_engine's.

**Impact:** Users see conflicting confidence numbers — structured API data says 95% while the prose reading says 80%. This undermines trust in the system.

---

## GAP-002: Personality Number Uses Generic One-Liner Instead of Full Descriptions

**Severity:** HIGH
**File:** `synthesis/universe_translator.py` (line 152)

**What's wrong:** The universe_translator has `LIFE_PATH_DESCRIPTIONS` (12 entries), `EXPRESSION_DESCRIPTIONS` (12 entries), and `SOUL_URGE_DESCRIPTIONS` (12 entries) — but Personality uses a generic fallback on line 152:

```python
core_identity += f"\n\nPersonality {pers}: This is how others first perceive you — the impression you make before they know you deeply."
```

This is identical for all 12 Personality numbers. A Personality 1 reading and a Personality 9 reading produce the same text.

**What should be there:** A `PERSONALITY_DESCRIPTIONS` dict with 12 entries (1-9, 11, 22, 33) parallel to the other three dicts. Each entry should describe how that Personality number manifests as an outward impression.

**Impact:** The Personality section of every reading is generic and undifferentiated, losing one dimension of personalization. The documentation (`logic/03_INTERPRETATION_BIBLE.md`) has full Personality descriptions that could inform these.

---

## GAP-003: Synthesis Footer Does Not List Missing Data Dimensions

**Severity:** HIGH
**File:** `synthesis/universe_translator.py` (lines 301-319)

**What's wrong:** The footer (Section 9) lists data sources used but never mentions what was NOT provided. Per the composition guide (`logic/04_READING_COMPOSITION_GUIDE.md`, Section 9: Footer): "List of data NOT provided (if any)" — example: "Not provided: location, mother's name, gender, exact time of day."

Currently the footer just says: "Data sources: FC60 stamp, weekday calculation, Pythagorean numerology, lunar phase, Gānzhī cycle, heartbeat estimation"

**What should be there:** An additional line listing missing data when not all inputs are provided. For example: "Not provided: location, mother's name, gender, exact time of day."

**Impact:** Minimal-data readings appear to have used all possible sources. Users don't know what additional inputs would improve their reading. The composition guide specifically requires this.

---

## GAP-004: logic/00_MASTER_SYSTEM_PROMPT.md Below 1,500-Word Minimum

**Severity:** MEDIUM
**File:** `logic/00_MASTER_SYSTEM_PROMPT.md`

**What's wrong:** The file has 1,345 words, which is 155 words (10%) below the 1,500-word minimum threshold.

**What should be there:** At least 1,500 words. The current content covers system overview, non-negotiable rules, file map, and quick-start but could expand the quick-start examples or add a troubleshooting section.

**Impact:** Minor. The file is functional and comprehensive for its purpose. The shortfall is modest and does not affect framework functionality.

---

## GAP-005: Synthesis Word Count Below 800-Word Target for Full Readings

**Severity:** MEDIUM
**File:** `synthesis/universe_translator.py`

**What's wrong:** Full-data readings produce ~580 words of synthesis text, below the 800-word target specified in the composition guide (Section C: "800-1200 words for full readings"). Each section is relatively terse.

**What should be there:** More interpretive prose per section, especially in "The Message" (Section 6) and "Core Identity" (Section 3), which could expand on the numerological significance with additional context from the interpretation data.

**Impact:** Medium. Readings feel adequate but not as richly detailed as the example readings in the composition guide. This is a quality-of-experience issue rather than a functional bug.

---

## GAP-006: No Low-Confidence Addendum in Synthesis

**Severity:** MEDIUM
**File:** `synthesis/universe_translator.py`

**What's wrong:** The composition guide specifies that readings with confidence below 65% should include an addendum noting the limited data impact. The translator does not implement this.

**What should be there:** When confidence is below 65%, the synthesis should include a note such as: "This reading is based on limited data. Providing [missing inputs] would significantly enhance accuracy."

**Impact:** Low practical impact since most readings score 70%+ confidence. But for edge cases with very minimal data, users would benefit from this transparency.

---

## GAP-007: Alice and Maria Sample Readings Share Life Path 5

**Severity:** LOW
**File:** `eval/sample_readings/`

**What's wrong:** Both sample full-data readings (Alice Johnson and Maria Rodriguez) happen to compute to Life Path 5 (Explorer). This means the Core Identity opening paragraph is identical between the two readings, reducing the apparent uniqueness of the sample outputs.

**What should be there:** Ideally, sample readings should demonstrate different Life Path numbers to showcase the framework's differentiation capabilities. This is a test-data selection issue, not a code bug.

**Impact:** Purely cosmetic for the audit. The readings still differ substantially in 13 of 15 dimensions. No code change needed.

---

## Fix Plan (Phase D)

### Will Fix (CRITICAL + HIGH):

1. **GAP-001**: Pass orchestrator confidence to universe_translator; have translator use it instead of reading_engine's confidence.
2. **GAP-002**: Add `PERSONALITY_DESCRIPTIONS` dict to universe_translator.py with 12 entries.
3. **GAP-003**: Add missing-data listing to the synthesis footer.

### DEFERRED (MEDIUM + LOW):

4. **GAP-004**: Word count expansion of logic/00 — cosmetic, functional content is complete.
5. **GAP-005**: Synthesis verbosity — would require significant prose expansion across multiple sections.
6. **GAP-006**: Low-confidence addendum — edge case with minimal practical impact.
7. **GAP-007**: Sample reading LP overlap — test data selection, not a code issue.
