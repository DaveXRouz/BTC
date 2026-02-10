# SESSION 13 SPEC: AI Interpretation Engine — Anthropic Integration

**Block:** AI & Reading Types (Sessions 13-18)
**Complexity:** Very High
**Dependencies:** Sessions 6-12 (framework integration complete)
**Estimated phases:** 10

---

## Overview

Session 13 connects the Anthropic Claude API to the numerology framework output. The AI receives the framework's raw reading data plus interpretation docs and generates the "Wisdom AI" interpretation — an honest, caring, insightful reading in 9 structured sections.

### The Core Problem

The existing AI engine files (`ai_client.py`, `ai_interpreter.py`, `prompt_templates.py`) consume the OLD oracle engine output format (`oracle.read_sign()` → sign, numbers, systems dict). Sessions 6-12 replaced that engine with the `numerology_ai_framework`'s `MasterOrchestrator.generate_reading()`, which produces a completely different output structure (person, fc60_stamp, numerology, moon, ganzhi, heartbeat, location, patterns, confidence, synthesis, translation).

This session rewrites the AI interpretation layer to:

1. Build a system prompt from the framework's `logic/` documentation (not a hand-written summary)
2. Construct user prompts from the framework's reading output structure
3. Parse AI responses into the 9-section structure defined in `logic/04_READING_COMPOSITION_GUIDE.md`
4. Support bilingual EN/FA output
5. Cache daily readings in the database
6. Gracefully degrade when the API key is missing (use `reading['synthesis']` as fallback)

---

## Files to Modify

| File                                                         | Action  | Current Lines | Notes                                                                       |
| ------------------------------------------------------------ | ------- | ------------- | --------------------------------------------------------------------------- |
| `services/oracle/oracle_service/engines/ai_client.py`        | REWRITE | 289           | Keep good patterns (cache, rate limit, singleton), update config, add retry |
| `services/oracle/oracle_service/engines/ai_interpreter.py`   | REWRITE | 665           | New input format (framework output), 9-section parsing, bilingual           |
| `services/oracle/oracle_service/engines/prompt_templates.py` | REWRITE | 317           | System prompt from framework docs, new user prompt templates                |
| `services/oracle/tests/test_ai_integration.py`               | REWRITE | 1080          | New test fixtures matching framework output, new test classes               |

## Files to Create

| File                                                  | Purpose                                             |
| ----------------------------------------------------- | --------------------------------------------------- |
| `services/oracle/oracle_service/ai_prompt_builder.py` | Constructs user prompts from framework reading data |

## Reference Files (Read-Only)

| File                                                            | Purpose                                                                |
| --------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `numerology_ai_framework/logic/00_MASTER_SYSTEM_PROMPT.md`      | System prompt source: capabilities, input dimensions, signal hierarchy |
| `numerology_ai_framework/logic/04_READING_COMPOSITION_GUIDE.md` | 9-section structure, tone guidelines, length guidelines                |
| `numerology_ai_framework/logic/06_API_INTEGRATION_TEMPLATE.md`  | JSON schemas for input/output, system prompt template                  |
| `numerology_ai_framework/logic/03_INTERPRETATION_BIBLE.md`      | Deep number meanings for system prompt context                         |
| `numerology_ai_framework/INTEGRATION_GUIDE.md`                  | MasterOrchestrator.generate_reading() usage                            |
| `numerology_ai_framework/CLAUDE.md`                             | Signal priority, coding standards                                      |

---

## PHASE 1: System Prompt Construction

**Goal:** Build the AI system prompt from framework documentation rather than hand-written summaries.

### What Changes

The current `FC60_SYSTEM_PROMPT` in `prompt_templates.py` (lines 12-27) is a hand-written 15-line summary of the numerology systems. It needs to be replaced with a comprehensive prompt built from:

1. **Framework's logic/06 Section A** — The system prompt template with rules, tone, and structure
2. **Framework's logic/04 Section A** — Tone and voice guidelines (warm but grounded, specific over vague, honest about uncertainty, mathematical not mystical)
3. **Framework's logic/04 Section B** — 9-section output structure definitions

### System Prompt Structure

The new system prompt in `prompt_templates.py` must include these sections (in order):

```
IDENTITY
- You are "Wisdom" — an honest, caring friend who understands numerological mathematics
- Never a fortune teller, mystic, or guru

RULES (from logic/06 Section A)
1. Never calculate numbers yourself — only use values from the engine
2. Never invent or estimate values
3. Always include FC60 stamp, confidence %, timezone
4. Use "the numbers suggest" language — never absolute predictions
5. Always include a disclaimer
6. Cap confidence at 95%
7. Master Numbers (11, 22, 33) never reduce further

TONE (from logic/04 Section A)
- Warm, honest, specific — reference actual numbers
- Ground in mathematics, not mysticism
- Acknowledge uncertainty — state what data is missing
- Include shadow warnings (Caution section)
- Compassionate but not flattering
- Suggestive, never predictive

READING STRUCTURE (from logic/04 Section B)
1. Header: Name, date, confidence
2. Universal Address: FC60 stamp, J60, Y60
3. Core Identity: Life Path, Expression, Soul Urge, Personality
4. Right Now: Planetary day, moon phase, hour energy
5. Patterns: Repeated animals, repeated numbers
6. The Message: 3-5 sentence synthesis
7. Today's Advice: 3 actionable items
8. Caution: Shadow warnings
9. Footer: Confidence, data sources, disclaimer

SIGNAL HIERARCHY (from framework CLAUDE.md)
1. Repeated animals (3+): Very High
2. Repeated animals (2): High
3. Day planet: Medium
4. Moon phase: Medium
5. DOM token animal+element: Medium
6. Hour animal: Low-Medium
7. Minute texture: Low
8. Year cycle (GZ): Background
9. Personal overlays: Variable

CONFIDENCE SCORING
- 50% minimum (base calculation only)
- 95% maximum cap
- Increases with more input dimensions provided
- State confidence level honestly
```

### Persian System Prompt

Create a `WISDOM_SYSTEM_PROMPT_FA` variant that:

- Has the same structure as the EN version
- Instructs the AI to respond entirely in Persian (Farsi)
- Preserves FC60 terms in English (use `FC60_PRESERVED_TERMS` list)
- Instructs RTL-aware formatting

### Implementation Details

In `prompt_templates.py`:

- Replace `FC60_SYSTEM_PROMPT` with `WISDOM_SYSTEM_PROMPT_EN` (comprehensive, ~80-120 lines of prompt text)
- Add `WISDOM_SYSTEM_PROMPT_FA` (~80-120 lines)
- Add `get_system_prompt(locale: str) -> str` helper that returns the correct prompt for "en" or "fa"
- Keep `FC60_PRESERVED_TERMS` list (already correct)
- Keep `build_prompt()` helper function (already correct)
- Remove old individual templates: `SIMPLE_TEMPLATE`, `ADVICE_TEMPLATE`, `ACTION_STEPS_TEMPLATE`, `UNIVERSE_MESSAGE_TEMPLATE`
- Remove old group templates: `GROUP_NARRATIVE_TEMPLATE`, `COMPATIBILITY_NARRATIVE_TEMPLATE`, `ENERGY_NARRATIVE_TEMPLATE`
- Remove old translation templates (translation is handled by locale-aware generation, not post-hoc)

### STOP — Checkpoint 1

- [ ] `WISDOM_SYSTEM_PROMPT_EN` contains all 5 sections (identity, rules, tone, structure, signal hierarchy)
- [ ] `WISDOM_SYSTEM_PROMPT_FA` mirrors EN but instructs Persian output
- [ ] `get_system_prompt("en")` returns EN, `get_system_prompt("fa")` returns FA
- [ ] Old templates removed
- [ ] `FC60_PRESERVED_TERMS` preserved
- [ ] `build_prompt()` preserved

---

## PHASE 2: AI Client Refactor

**Goal:** Keep the good patterns in `ai_client.py`, update configuration, add retry logic.

### What to Keep (Good Patterns)

These patterns in the existing `ai_client.py` are well-designed — keep them:

1. **Lazy singleton client** (`_get_client()`, lines 279-288) — thread-safe, lazy init
2. **In-memory cache** with TTL + max size (`_read_cache`, `_write_cache`, `_evict_cache`)
3. **Thread-safe rate limiting** (`_enforce_rate_limit`)
4. **Availability check** (`is_available()`) — checks SDK + API key
5. **Cache key generation** (`_cache_key`) — SHA-256 from prompt + system_prompt
6. **API key sanitization** in error messages (lines 197-199)
7. **Public reset functions** (`clear_cache()`, `reset_availability()`)

### What to Change

1. **Default max_tokens**: Change from 1024 to 2000 for single readings, 3000 for multi-user
   - Add `_DEFAULT_MAX_TOKENS_SINGLE = 2000`
   - Add `_DEFAULT_MAX_TOKENS_MULTI = 3000`
   - The `generate()` function keeps `max_tokens` parameter — caller decides

2. **Default temperature**: Keep at 0.7 (already correct)

3. **Default model**: Keep `claude-sonnet-4-20250514` (already correct on line 26)

4. **Add retry logic**: When the API returns a retryable error (rate limit, server error), retry once after a 2-second wait
   - Only retry on `anthropic.RateLimitError`, `anthropic.InternalServerError`, `anthropic.APIConnectionError`
   - Do NOT retry on `anthropic.AuthenticationError`, `anthropic.BadRequestError`
   - Max 1 retry (not infinite)

5. **Add `generate_reading()` convenience function**: Wraps `generate()` with reading-specific defaults

   ```python
   def generate_reading(
       user_prompt: str,
       system_prompt: str,
       locale: str = "en",
       max_tokens: int = 2000,
       use_cache: bool = True,
   ) -> dict:
   ```

6. **Update error return shape**: Add `retried: bool` field to the return dict

### Implementation Details

In `ai_client.py`:

- Keep module docstring, update to mention retry
- Keep all imports, add `from anthropic import RateLimitError, InternalServerError, APIConnectionError` (guarded by `_sdk_available`)
- Keep `_DEFAULT_MODEL`, update token constants
- Keep all cache/rate-limit infrastructure
- Modify `generate()`: add retry loop (max 1 retry for retryable errors)
- Add `generate_reading()` convenience wrapper
- Keep `clear_cache()`, `reset_availability()`
- Keep all internal helpers

### STOP — Checkpoint 2

- [ ] `ai_client.py` passes import without errors
- [ ] `is_available()` still works (SDK + key check)
- [ ] `generate()` retries once on rate limit, then returns error
- [ ] `generate()` does NOT retry on auth error
- [ ] `generate_reading()` exists with correct signature
- [ ] Cache still works (TTL, eviction, clear)
- [ ] Return dict includes `retried` field

---

## PHASE 3: AI Prompt Builder (New File)

**Goal:** Create `ai_prompt_builder.py` — constructs user prompts from framework reading data.

### Why a Separate File

The user prompt construction logic is complex enough to warrant its own module:

- It must extract data from 12+ top-level keys in the framework output
- It must handle missing/null sections gracefully
- It must format data differently for single vs. multi-user readings
- It must be independently testable

### File Location

`services/oracle/oracle_service/ai_prompt_builder.py`

### Public API

```python
def build_reading_prompt(
    reading: dict,
    reading_type: str = "daily",
    question: str = "",
    locale: str = "en",
) -> str:
    """Build user prompt from MasterOrchestrator.generate_reading() output.

    Parameters
    ----------
    reading : dict
        Full output from MasterOrchestrator.generate_reading().
    reading_type : str
        One of: "daily", "time", "name", "question", "multi".
    question : str
        The user's question (only for reading_type="question").
    locale : str
        "en" or "fa" — affects section labels and instructions.

    Returns
    -------
    str
        Formatted user prompt ready to send to the AI.
    """
```

```python
def build_multi_user_prompt(
    readings: list[dict],
    names: list[str],
    locale: str = "en",
) -> str:
    """Build user prompt for multi-user reading.

    Parameters
    ----------
    readings : list[dict]
        List of reading dicts from MasterOrchestrator.generate_reading().
    names : list[str]
        List of user names corresponding to each reading.
    locale : str
        "en" or "fa".

    Returns
    -------
    str
        Formatted multi-user prompt.
    """
```

### User Prompt Structure (Single Reading)

The prompt must include ALL of these sections from the reading dict, in this order:

```
READING TYPE: {reading_type}
QUESTION: {question}  (only if reading_type == "question")
LOCALE: {locale}

--- PERSON ---
Name: {reading['person']['name']}
Birthdate: {reading['person']['birthdate']}
Age: {reading['person']['age_years']} years ({reading['person']['age_days']} days)

--- FC60 STAMP ---
FC60: {reading['fc60_stamp']['fc60']}
J60: {reading['fc60_stamp']['j60']}
Y60: {reading['fc60_stamp']['y60']}
CHK: {reading['fc60_stamp']['chk']}

--- BIRTH DATA ---
JDN: {reading['birth']['jdn']}
Weekday: {reading['birth']['weekday']}
Planet: {reading['birth']['planet']}

--- CURRENT DATA ---
Date: {reading['current']['date']}
Weekday: {reading['current']['weekday']}
Planet: {reading['current']['planet']}
Domain: {reading['current']['domain']}

--- NUMEROLOGY ---
Life Path: {reading['numerology']['life_path']['number']} ({reading['numerology']['life_path']['title']})
  Message: {reading['numerology']['life_path']['message']}
Expression: {reading['numerology']['expression']}
Soul Urge: {reading['numerology']['soul_urge']}
Personality: {reading['numerology']['personality']}
Personal Year: {reading['numerology']['personal_year']}
Personal Month: {reading['numerology']['personal_month']}
Personal Day: {reading['numerology']['personal_day']}
Gender Polarity: {reading['numerology']['gender_polarity']['label']} (if present)
Mother Influence: {reading['numerology']['mother_influence']} (if present)

--- MOON ---
Phase: {reading['moon']['phase_name']} {reading['moon']['emoji']}
Age: {reading['moon']['age']} days
Illumination: {reading['moon']['illumination']}%
Energy: {reading['moon']['energy']}
Best For: {reading['moon']['best_for']}
Avoid: {reading['moon']['avoid']}

--- GANZHI ---
Year: {reading['ganzhi']['year']['traditional_name']} ({reading['ganzhi']['year']['element']}, {reading['ganzhi']['year']['animal_name']})
Day: {reading['ganzhi']['day']['gz_token']} ({reading['ganzhi']['day']['element']}, {reading['ganzhi']['day']['animal_name']})
Hour: {reading['ganzhi']['hour']['animal_name']} (if present)

--- HEARTBEAT ---
BPM: {reading['heartbeat']['bpm']} ({reading['heartbeat']['bpm_source']})
Element: {reading['heartbeat']['element']}
Lifetime Beats: {reading['heartbeat']['total_lifetime_beats']}
Rhythm Token: {reading['heartbeat']['rhythm_token']}

--- LOCATION --- (if reading['location'] is not None)
Latitude: {reading['location']['latitude']} ({reading['location']['lat_hemisphere']})
Longitude: {reading['location']['longitude']} ({reading['location']['lon_hemisphere']})
Element: {reading['location']['element']}

--- PATTERNS ---
Count: {reading['patterns']['count']}
{for each pattern in reading['patterns']['detected']:}
  Type: {pattern['type']}, Strength: {pattern['strength']}, Message: {pattern['message']}

--- CONFIDENCE ---
Score: {reading['confidence']['score']}%
Level: {reading['confidence']['level']}
Factors: {reading['confidence']['factors']}

--- FRAMEWORK SYNTHESIS ---
{reading['synthesis']}
```

### Internal Helpers

```python
def _format_numerology(numerology: dict) -> str:
    """Format the numerology section of a reading."""

def _format_moon(moon: dict) -> str:
    """Format the moon section of a reading."""

def _format_ganzhi(ganzhi: dict) -> str:
    """Format the ganzhi section of a reading."""

def _format_heartbeat(heartbeat: dict) -> str:
    """Format the heartbeat section of a reading."""

def _format_location(location: dict | None) -> str:
    """Format the location section (returns 'Not provided' if None)."""

def _format_patterns(patterns: dict) -> str:
    """Format the patterns section, sorted by strength."""

def _safe_get(d: dict, *keys, default: str = "not provided") -> str:
    """Safely traverse nested dict keys."""
```

### STOP — Checkpoint 3

- [ ] `ai_prompt_builder.py` exists at correct path
- [ ] `build_reading_prompt()` handles full reading (all 12 sections present)
- [ ] `build_reading_prompt()` handles minimal reading (location=None, no time, no mother)
- [ ] `build_multi_user_prompt()` handles 2+ readings
- [ ] Missing/null fields produce "not provided", not KeyError
- [ ] Reading type and question are included when relevant
- [ ] File imports successfully

---

## PHASE 4: AI Interpreter Rewrite

**Goal:** Rewrite `ai_interpreter.py` to consume framework output and parse AI responses into 9 sections.

### What Changes Completely

The existing `ai_interpreter.py` is built around:

- `oracle.read_sign()` output format → **GONE** (replaced by framework)
- 4 format types (simple, advice, action_steps, universe_message) → **REPLACED** by 9-section structure
- `InterpretationResult`, `MultiFormatResult`, `GroupInterpretationResult` → **REPLACED** by new result classes

### New Result Classes

```python
@dataclass
class ReadingInterpretation:
    """Result of a single AI-generated reading interpretation."""
    header: str
    universal_address: str
    core_identity: str
    right_now: str
    patterns: str
    message: str
    advice: str
    caution: str
    footer: str
    full_text: str          # All 9 sections concatenated
    ai_generated: bool
    locale: str             # "en" or "fa"
    elapsed_ms: float
    cached: bool
    confidence_score: int   # From the reading data

    def to_dict(self) -> dict: ...
```

```python
@dataclass
class MultiUserInterpretation:
    """Result of a multi-user group reading interpretation."""
    individual_readings: dict[str, ReadingInterpretation]  # name -> reading
    group_narrative: str
    compatibility_summary: str
    ai_generated: bool
    locale: str
    elapsed_ms: float

    def to_dict(self) -> dict: ...
```

### New Public API

```python
def interpret_reading(
    reading: dict,
    reading_type: str = "daily",
    question: str = "",
    locale: str = "en",
    use_cache: bool = True,
) -> ReadingInterpretation:
    """Generate AI interpretation from framework reading output.

    Parameters
    ----------
    reading : dict
        Output of MasterOrchestrator.generate_reading().
    reading_type : str
        One of: "daily", "time", "name", "question", "multi".
    question : str
        User's question (for reading_type="question").
    locale : str
        "en" or "fa".
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    ReadingInterpretation
    """
```

```python
def interpret_multi_user(
    readings: list[dict],
    names: list[str],
    locale: str = "en",
) -> MultiUserInterpretation:
    """Generate AI interpretation for multiple users."""
```

### Response Parsing

The AI returns prose text with 9 sections. Parse it by looking for section headers:

```python
_SECTION_MARKERS_EN = {
    "header": ["READING FOR", "reading for"],
    "universal_address": ["UNIVERSAL ADDRESS", "YOUR UNIVERSAL ADDRESS", "FC60:"],
    "core_identity": ["CORE IDENTITY", "YOUR CORE IDENTITY"],
    "right_now": ["RIGHT NOW", "THE PRESENT MOMENT"],
    "patterns": ["PATTERNS DETECTED", "PATTERNS"],
    "message": ["THE MESSAGE", "MESSAGE"],
    "advice": ["TODAY'S ADVICE", "ADVICE"],
    "caution": ["CAUTION", "SHADOW WARNING"],
    "footer": ["Confidence:", "Data sources:", "Disclaimer:"],
}

_SECTION_MARKERS_FA = {
    "header": ["خوانش برای", "گزارش برای"],
    "universal_address": ["آدرس جهانی", "FC60:"],
    "core_identity": ["هویت اصلی"],
    "right_now": ["اکنون", "لحظه حاضر"],
    "patterns": ["الگوها"],
    "message": ["پیام"],
    "advice": ["توصیه", "راهنمایی"],
    "caution": ["هشدار", "احتیاط"],
    "footer": ["اطمینان:", "منابع داده:"],
}
```

The parser function:

```python
def _parse_sections(text: str, locale: str = "en") -> dict[str, str]:
    """Parse AI response text into 9 named sections.

    Splits on section headers using marker strings.
    If parsing fails (headers not found), returns the full text
    in the 'message' section with other sections empty.

    Returns dict with keys: header, universal_address, core_identity,
    right_now, patterns, message, advice, caution, footer.
    """
```

### Fallback Behavior

When AI is unavailable (no API key) or fails:

1. Use `reading['synthesis']` as the full reading text (framework generates this deterministically)
2. Use `reading['translation']` dict to populate individual sections (header, universal_address, etc.)
3. Set `ai_generated = False`
4. This is a GOOD fallback — the framework's synthesis is comprehensive

```python
def _build_fallback(reading: dict, locale: str) -> ReadingInterpretation:
    """Build fallback interpretation from framework's own synthesis.

    Uses reading['translation'] for individual sections if available,
    otherwise uses reading['synthesis'] as full_text with empty sections.
    """
```

### STOP — Checkpoint 4

- [ ] `ReadingInterpretation` dataclass has all 9 section fields + metadata
- [ ] `MultiUserInterpretation` dataclass has individual readings + group narrative
- [ ] `interpret_reading()` calls `build_reading_prompt()` → `generate_reading()` → `_parse_sections()`
- [ ] `interpret_reading()` falls back to `reading['synthesis']` when AI unavailable
- [ ] `_parse_sections()` handles both EN and FA section markers
- [ ] `_parse_sections()` returns full text in 'message' if parsing fails (graceful)
- [ ] Old classes removed: `InterpretationResult`, `MultiFormatResult`, `GroupInterpretationResult`
- [ ] Old functions removed: `interpret_name()`, `interpret_all_formats()`, `interpret_group()`
- [ ] Old context builders removed: `_build_reading_context()`, `_build_group_context()`, `_build_compat_context()`

---

## PHASE 5: Bilingual Support

**Goal:** Generate readings in the user's locale (EN or FA).

### How It Works

1. The `locale` parameter flows through: `interpret_reading(locale=)` → `get_system_prompt(locale)` + `build_reading_prompt(locale=)` → AI generates in that language
2. For EN: Use `WISDOM_SYSTEM_PROMPT_EN`, AI responds in English
3. For FA: Use `WISDOM_SYSTEM_PROMPT_FA`, AI responds in Persian

### Persian-Specific Rules

- FC60 terms stay in English (use `FC60_PRESERVED_TERMS`)
- Numbers stay as Arabic numerals (not Persian digits) for consistency with the engine output
- Section headers in the AI response are in Persian (parser uses `_SECTION_MARKERS_FA`)
- The `disclaimer` in the footer is in Persian

### No Post-Hoc Translation

The OLD approach used `translation_service.py` to translate an English reading to Persian. The NEW approach generates natively in Persian — the system prompt instructs the AI to write in Persian from the start. This produces much better results.

Note: `services/oracle/oracle_service/engines/translation_service.py` still exists from the scaffolding. Session 13 does NOT delete it — it may be useful for other features later. But `ai_interpreter.py` does NOT import or use it.

### STOP — Checkpoint 5

- [ ] `interpret_reading(locale="en")` generates English reading
- [ ] `interpret_reading(locale="fa")` generates Persian reading
- [ ] System prompt changes based on locale
- [ ] FC60 terms preserved in English even in FA output
- [ ] Section parser handles FA markers

---

## PHASE 6: Caching Strategy

**Goal:** Cache AI interpretations for daily readings.

### In-Memory Cache (Keep)

The existing in-memory cache in `ai_client.py` stays:

- TTL: 1 hour
- Max entries: 200
- Cache key: SHA-256 of prompt + system_prompt

This handles short-term deduplication (same user refreshing the page).

### Database Cache (New — Future Session)

The master spec mentions caching in `oracle_daily_readings` table. However, this table's schema was not defined in Sessions 1-5 (Foundation block). Session 13 prepares for DB caching but does NOT implement it yet:

- Add a `_make_daily_cache_key(user_id: str, date: str, locale: str) -> str` helper in `ai_interpreter.py`
- Add a comment/TODO noting where DB cache integration will plug in
- The actual DB caching will be implemented when the daily readings API endpoint is built (Session 14-16)

### Cache Key Design

For the in-memory cache, the key is derived from:

- User prompt (which includes all reading data — deterministic for same input)
- System prompt (which includes locale)
- This means same person + same date + same locale = cache hit

### STOP — Checkpoint 6

- [ ] In-memory cache still works in `ai_client.py`
- [ ] `_make_daily_cache_key()` exists as a helper
- [ ] No premature DB cache implementation

---

## PHASE 7: Error Handling and Retry

**Goal:** Robust error handling with graceful degradation.

### Error Cascade

```
AI call
  ├─ Success → parse sections → return ReadingInterpretation(ai_generated=True)
  ├─ Retryable error (rate limit, server error, connection error)
  │   └─ Wait 2s → retry once
  │       ├─ Success → parse sections → return ReadingInterpretation(ai_generated=True)
  │       └─ Fail again → fallback
  ├─ Non-retryable error (auth, bad request)
  │   └─ fallback immediately
  └─ API key missing (is_available() == False)
      └─ fallback immediately

Fallback:
  reading['translation'] exists? → populate sections from translation dict
  reading['synthesis'] exists? → use as full_text
  neither exists? → return minimal "reading unavailable" message
```

### Specific Error Types

| Error                           | Action                                   | Retry? |
| ------------------------------- | ---------------------------------------- | ------ |
| `anthropic.RateLimitError`      | Wait 2s, retry once                      | Yes    |
| `anthropic.InternalServerError` | Wait 2s, retry once                      | Yes    |
| `anthropic.APIConnectionError`  | Wait 2s, retry once                      | Yes    |
| `anthropic.AuthenticationError` | Log warning, fallback                    | No     |
| `anthropic.BadRequestError`     | Log error, fallback                      | No     |
| `TimeoutError`                  | Log warning, fallback                    | No     |
| `Exception` (catch-all)         | Log error, fallback                      | No     |
| SDK not installed               | `is_available()` returns False, fallback | No     |
| API key not set                 | `is_available()` returns False, fallback | No     |

### Logging

All errors logged at appropriate levels:

- Rate limit → `logger.warning`
- Server error → `logger.warning`
- Auth error → `logger.error` (misconfiguration)
- Fallback used → `logger.info`

### STOP — Checkpoint 7

- [ ] Retry logic works for rate limit errors
- [ ] Auth errors do NOT retry
- [ ] Fallback always produces a valid `ReadingInterpretation`
- [ ] All errors logged (no silent failures)
- [ ] API key never appears in log messages

---

## PHASE 8: Test Suite Rewrite

**Goal:** Rewrite `test_ai_integration.py` with new fixtures matching framework output.

### Test Fixture: Framework Reading Output

Create a `SAMPLE_FRAMEWORK_READING` fixture that matches `MasterOrchestrator.generate_reading()` output:

```python
SAMPLE_FRAMEWORK_READING = {
    "person": {
        "name": "Alice Johnson",
        "birthdate": "1990-07-15",
        "age_years": 35,
        "age_days": 12993,
    },
    "fc60_stamp": {
        "fc60": "LU-OX-OXWA 🌙TI-HOWU-RAWU",
        "j60": "TIFI-DRMT-GOMT-RAFI",
        "y60": "HOMT-ROFI",
        "chk": "DOWU",
        "iso": "2026-02-09T14:30:00-05:00",
    },
    "numerology": {
        "life_path": {"number": 5, "title": "Explorer", "message": "Change and adapt"},
        "expression": 8,
        "soul_urge": 9,
        "personality": 8,
        "personal_year": 5,
        "personal_month": 7,
        "personal_day": 7,
        "gender_polarity": {"gender": "female", "polarity": -1, "label": "Yin"},
        "mother_influence": 3,
    },
    "moon": {
        "phase_name": "Waning Gibbous",
        "emoji": "🌖",
        "age": 22.05,
        "illumination": 51.0,
        "energy": "Share",
        "best_for": "teaching, distributing, gratitude",
        "avoid": "hoarding",
    },
    "ganzhi": {
        "year": {"gz_token": "BI-HO", "traditional_name": "Fire Horse", "element": "Fire", "polarity": "Yang", "animal_name": "Horse"},
        "day": {"gz_token": "JA-TI", "element": "Wood", "animal_name": "Tiger"},
        "hour": {"stem_token": "XI", "branch_token": "GO", "animal_name": "Goat"},
    },
    "heartbeat": {
        "age": 35,
        "bpm": 68,
        "bpm_source": "actual",
        "beats_per_day": 97920,
        "total_lifetime_beats": 1477947600,
        "element": "Metal",
        "rhythm_token": "MTHO",
        "life_pulse_signature": "LP5-MT68",
    },
    "location": {
        "latitude": 40.7,
        "longitude": -74.0,
        "element": "Metal",
        "timezone_estimate": -5,
        "lat_hemisphere": "N",
        "lon_hemisphere": "W",
        "lat_polarity": "Yang",
        "lon_polarity": "Yin",
    },
    "patterns": {
        "detected": [
            {"type": "animal_repetition", "animal": "Ox", "occurrences": 2, "strength": "high", "message": "Ox appears 2 times — patience and endurance"},
            {"type": "animal_repetition", "animal": "Horse", "occurrences": 2, "strength": "high", "message": "Horse appears 2 times — freedom and movement"},
            {"type": "number_repetition", "number": 5, "occurrences": 2, "strength": "medium", "message": "5 appears in Life Path and Personal Year"},
            {"type": "number_repetition", "number": 8, "occurrences": 2, "strength": "medium", "message": "8 appears in Expression and Personality"},
        ],
        "count": 4,
    },
    "confidence": {
        "score": 95,
        "level": "very_high",
        "factors": "Based on 6 data sources",
    },
    "synthesis": "READING FOR ALICE JOHNSON\nDate: 2026-02-09\nConfidence: 95% (very high)\n\n...[full synthesis text]...",
    "translation": {
        "header": "READING FOR ALICE JOHNSON\nDate: 2026-02-09\nConfidence: 95% (very high)",
        "universal_address": "FC60: LU-OX-OXWA 🌙TI-HOWU-RAWU\nJ60: TIFI-DRMT-GOMT-RAFI\nY60: HOMT-ROFI",
        "core_identity": "Your Life Path is 5 -- the Explorer...",
        "right_now": "Today is Monday, a Moon day...",
        "patterns": "The Ox appears 2 times...",
        "message": "The Ox and Horse both appear twice...",
        "advice": "1. Move with intention...",
        "caution": "Watch for overwhelm...",
        "footer": "Confidence: 95% (very high)\nData sources: ...\nDisclaimer: ...",
        "full_text": "READING FOR ALICE JOHNSON\n...[complete reading]...",
    },
}
```

Create a `SAMPLE_MINIMAL_READING` fixture with `location=None`, no `hour` in ganzhi, `bpm_source="estimated"`, `confidence.score=80`.

### Test Classes (12+ tests minimum)

#### Class 1: `TestPromptBuilder` (5 tests)

| Test                                | Function                                                                   | What it Verifies                               |
| ----------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------- |
| `test_build_full_reading_prompt`    | `build_reading_prompt(SAMPLE_FRAMEWORK_READING)`                           | All 12 sections present in output              |
| `test_build_minimal_reading_prompt` | `build_reading_prompt(SAMPLE_MINIMAL_READING)`                             | Location shows "not provided", no hour section |
| `test_build_question_prompt`        | `build_reading_prompt(..., reading_type="question", question="Will I...")` | Question text included                         |
| `test_build_multi_user_prompt`      | `build_multi_user_prompt([reading1, reading2], ["Alice", "Bob"])`          | Both readings present                          |
| `test_safe_get_nested`              | `_safe_get(reading, "numerology", "life_path", "number")`                  | Returns value or default                       |

#### Class 2: `TestSystemPrompt` (4 tests)

| Test                                           | Function                  | What it Verifies                                     |
| ---------------------------------------------- | ------------------------- | ---------------------------------------------------- |
| `test_en_system_prompt_content`                | `get_system_prompt("en")` | Contains rules, tone, 9-section structure            |
| `test_fa_system_prompt_content`                | `get_system_prompt("fa")` | Contains Persian instructions, FC60 terms in English |
| `test_system_prompt_includes_signal_hierarchy` | `get_system_prompt("en")` | Signal hierarchy present                             |
| `test_unknown_locale_defaults_to_en`           | `get_system_prompt("de")` | Falls back to English                                |

#### Class 3: `TestAIClientRetry` (4 tests)

| Test                           | Function                                         | What it Verifies                          |
| ------------------------------ | ------------------------------------------------ | ----------------------------------------- |
| `test_retry_on_rate_limit`     | `generate()` with mocked rate limit then success | Retries once, returns success             |
| `test_no_retry_on_auth_error`  | `generate()` with mocked auth error              | Does NOT retry, returns error immediately |
| `test_retry_exhausted`         | `generate()` with rate limit both times          | Returns error after 1 retry               |
| `test_retried_field_in_result` | `generate()` with retry scenario                 | `result['retried']` is True               |

#### Class 4: `TestResponseParsing` (4 tests)

| Test                              | Function                                           | What it Verifies                       |
| --------------------------------- | -------------------------------------------------- | -------------------------------------- |
| `test_parse_9_sections_en`        | `_parse_sections(SAMPLE_EN_RESPONSE)`              | All 9 sections populated               |
| `test_parse_9_sections_fa`        | `_parse_sections(SAMPLE_FA_RESPONSE, locale="fa")` | All 9 sections populated               |
| `test_parse_fallback_unparseable` | `_parse_sections("just plain text")`               | Full text in 'message', others empty   |
| `test_parse_partial_sections`     | `_parse_sections(response_with_only_5_sections)`   | Found sections populated, others empty |

#### Class 5: `TestInterpreter` (5 tests)

| Test                                  | Function                                                          | What it Verifies                                                                   |
| ------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `test_interpret_reading_ai_success`   | `interpret_reading(SAMPLE_FRAMEWORK_READING)` with mock AI        | Returns `ReadingInterpretation(ai_generated=True)`                                 |
| `test_interpret_reading_fallback`     | `interpret_reading(SAMPLE_FRAMEWORK_READING)` with AI unavailable | Returns `ReadingInterpretation(ai_generated=False)`, uses `reading['translation']` |
| `test_interpret_reading_fa`           | `interpret_reading(..., locale="fa")`                             | FA system prompt used                                                              |
| `test_interpret_multi_user`           | `interpret_multi_user([r1, r2], ["Alice", "Bob"])`                | Returns `MultiUserInterpretation` with 2 individual readings                       |
| `test_reading_interpretation_to_dict` | `result.to_dict()`                                                | JSON-serializable, all 9 section keys present                                      |

#### Class 6: `TestFallback` (3 tests)

| Test                                               | Function                                       | What it Verifies                                            |
| -------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------- |
| `test_fallback_uses_translation_sections`          | `_build_fallback(reading_with_translation)`    | Individual sections populated from `reading['translation']` |
| `test_fallback_uses_synthesis_when_no_translation` | `_build_fallback(reading_without_translation)` | `full_text` has synthesis, sections empty                   |
| `test_fallback_minimal_reading`                    | `_build_fallback(SAMPLE_MINIMAL_READING)`      | No crash, valid result                                      |

#### Class 7: `TestCacheKey` (2 tests)

| Test                                     | Function                                                                                | What it Verifies    |
| ---------------------------------------- | --------------------------------------------------------------------------------------- | ------------------- |
| `test_daily_cache_key_deterministic`     | `_make_daily_cache_key("user1", "2026-02-09", "en")` twice                              | Same key both times |
| `test_daily_cache_key_differs_by_locale` | `_make_daily_cache_key("user1", "2026-02-09", "en")` vs `("user1", "2026-02-09", "fa")` | Different keys      |

### Mock Setup

All AI calls mocked — zero real API calls:

```python
SAMPLE_AI_RESPONSE_EN = """READING FOR ALICE JOHNSON
Date: 2026-02-09
Confidence: 95% (very high)

---

YOUR UNIVERSAL ADDRESS

FC60: LU-OX-OXWA 🌙TI-HOWU-RAWU
J60: TIFI-DRMT-GOMT-RAFI

---

CORE IDENTITY

Your Life Path is 5 -- the Explorer...

---

RIGHT NOW

Today is Monday, a Moon day...

---

PATTERNS DETECTED

The Ox appears 2 times...

---

THE MESSAGE

The numbers suggest patience and forward motion...

---

TODAY'S ADVICE

1. Move with intention...
2. Share what you know...
3. Trust your emotional compass...

---

CAUTION

Watch for overwhelm...

---

Confidence: 95% (very high)
Data sources: FC60 stamp, Pythagorean numerology, lunar phase
Disclaimer: This reading suggests patterns, not predictions."""
```

### Test Run Command

```bash
cd services/oracle && python3 -m pytest tests/test_ai_integration.py -v
```

### STOP — Checkpoint 8

- [ ] `test_ai_integration.py` has 27+ tests across 7 classes
- [ ] All fixtures use framework output format (not old oracle format)
- [ ] All AI calls mocked (no real API calls)
- [ ] Tests cover: prompt building, system prompt, retry, parsing, interpreter, fallback, cache key
- [ ] All tests pass: `cd services/oracle && python3 -m pytest tests/test_ai_integration.py -v`

---

## PHASE 9: Integration Verification

**Goal:** Verify all components work together end-to-end.

### Integration Test Scenarios

1. **Full pipeline (mocked AI):**

   ```
   SAMPLE_FRAMEWORK_READING → build_reading_prompt() → generate_reading() → _parse_sections() → ReadingInterpretation
   ```

   Verify: all 9 sections populated, `ai_generated=True`, `to_dict()` is JSON-serializable

2. **Full pipeline (AI unavailable):**

   ```
   SAMPLE_FRAMEWORK_READING → is_available() returns False → _build_fallback() → ReadingInterpretation
   ```

   Verify: `ai_generated=False`, sections from `reading['translation']`, `full_text` from `reading['synthesis']`

3. **Persian pipeline (mocked AI):**

   ```
   SAMPLE_FRAMEWORK_READING + locale="fa" → FA system prompt → FA user prompt → mock FA response → parse FA sections
   ```

   Verify: FA section markers used, `locale="fa"` in result

4. **Multi-user pipeline (mocked AI):**
   ```
   [reading1, reading2] → build_multi_user_prompt() → generate_reading(max_tokens=3000) → parse → MultiUserInterpretation
   ```
   Verify: 2 individual readings, group narrative present

### Import Verification

Verify that the new modules can be imported from within the Oracle service:

```python
from ai_prompt_builder import build_reading_prompt, build_multi_user_prompt
from engines.ai_client import generate, generate_reading, is_available
from engines.ai_interpreter import interpret_reading, interpret_multi_user, ReadingInterpretation, MultiUserInterpretation
from engines.prompt_templates import get_system_prompt, WISDOM_SYSTEM_PROMPT_EN, WISDOM_SYSTEM_PROMPT_FA, FC60_PRESERVED_TERMS
```

### STOP — Checkpoint 9

- [ ] Integration test: full pipeline produces valid ReadingInterpretation
- [ ] Integration test: fallback pipeline produces valid ReadingInterpretation
- [ ] Integration test: FA pipeline uses FA system prompt
- [ ] All imports work from `services/oracle/` context
- [ ] All tests pass: `cd services/oracle && python3 -m pytest tests/test_ai_integration.py -v`

---

## PHASE 10: Cleanup and Documentation

**Goal:** Clean up code, add docstrings, verify standards.

### Code Quality

Run on all modified/created files:

1. `black` formatter
2. `ruff` linter (fix any issues)
3. Verify no `any` types in Python (use proper type hints)
4. Verify no bare `except:` (catch specific exceptions)
5. Verify no hardcoded file paths (use `Path(__file__).resolve()`)
6. Verify no secrets in code (API key only via env var)

### Files Modified Summary

| File                                                         | Lines (approx) | What Changed                                                                       |
| ------------------------------------------------------------ | -------------- | ---------------------------------------------------------------------------------- |
| `services/oracle/oracle_service/engines/prompt_templates.py` | ~150           | Replaced hand-written prompt with framework-sourced prompt, removed old templates  |
| `services/oracle/oracle_service/engines/ai_client.py`        | ~320           | Added retry logic, `generate_reading()` wrapper, updated token defaults            |
| `services/oracle/oracle_service/engines/ai_interpreter.py`   | ~400           | Complete rewrite: new result classes, framework input, 9-section parsing, fallback |
| `services/oracle/oracle_service/ai_prompt_builder.py`        | ~250           | NEW: constructs user prompts from framework reading data                           |
| `services/oracle/tests/test_ai_integration.py`               | ~600           | Complete rewrite: new fixtures, 27+ tests across 7 classes                         |

### What Was NOT Changed

- `services/oracle/oracle_service/engines/ai_client.py` core patterns (cache, rate limit, singleton) — kept intact
- `services/oracle/oracle_service/engines/translation_service.py` — not touched (may be used later)
- `numerology_ai_framework/` — read-only reference, never modified
- Database schema — no changes (DB caching deferred to later session)

### STOP — Checkpoint 10 (Final)

- [ ] All files formatted with `black`
- [ ] All files pass `ruff` with zero warnings
- [ ] No bare `except:` anywhere
- [ ] No `any` types in Python
- [ ] No hardcoded paths
- [ ] All 27+ tests pass
- [ ] `import ai_prompt_builder` works
- [ ] `import engines.ai_interpreter` works with new classes
- [ ] `import engines.prompt_templates` works with new constants

---

## Acceptance Criteria

- [ ] AI generates reading from framework output (mock test passes)
- [ ] Fallback to framework `synthesis` works when API key missing
- [ ] Both EN and FA prompts generate correct language
- [ ] Response parsed into 9 structured sections
- [ ] Retry logic works for rate-limit errors
- [ ] All tests pass: `cd services/oracle && python3 -m pytest tests/test_ai_integration.py -v`

---

## Dependencies

### Upstream (must be complete before Session 13)

- **Sessions 6-12**: Framework integration complete — `MasterOrchestrator.generate_reading()` is callable and returns the documented output structure

### Downstream (depends on Session 13)

- **Session 14**: Daily Reading Flow — uses `interpret_reading()` for the daily reading endpoint
- **Session 15**: Name Reading Flow — uses `interpret_reading(reading_type="name")`
- **Session 16**: Question Reading Flow — uses `interpret_reading(reading_type="question")`
- **Session 17**: Multi-User Reading Flow — uses `interpret_multi_user()`
- **Session 18**: Reading History & Export — reads cached readings

---

## Key Decisions

1. **Native bilingual generation (not translation)**: Instead of generating in English then translating to Persian, we generate natively in both languages. This produces much better Persian prose.

2. **Framework synthesis as fallback**: When AI is unavailable, the framework's own `synthesis` field provides a deterministic, comprehensive reading. This is a high-quality fallback.

3. **9-section structure**: Replaces the old 4-format model (simple, advice, action_steps, universe_message). Every reading now has the same 9 sections at varying depth — consistent with the framework's `logic/04_READING_COMPOSITION_GUIDE.md`.

4. **Deferred DB caching**: The `oracle_daily_readings` table doesn't exist yet (not in Sessions 1-5 schema). We prepare the cache key helper but defer actual DB integration.

5. **Single retry for retryable errors**: Keeps things simple. One retry with 2-second wait. If it fails twice, fall back.

6. **Keep translation_service.py**: Not deleted — it may be useful for non-reading translation needs later.
