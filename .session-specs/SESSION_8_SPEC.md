# SESSION 8 SPEC — Framework Integration: Numerology System Selection

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium-High
**Dependencies:** Session 6 (framework bridge), Session 7 (reading types — `UserProfile.numerology_system` field)

---

## TL;DR

- Add Abjad (Persian/Arabic) numerology system to the framework's `NumerologyEngine` — currently only Pythagorean and Chaldean exist
- Build script detection utilities (Python + TypeScript) that identify Persian/Arabic Unicode characters in names
- Implement auto-selection logic: Persian script → Abjad, English locale → Pythagorean, manual override always wins
- Add `numerology_system` parameter to API reading endpoints and save preference in `oracle_settings` table
- Build `NumerologySystemSelector.tsx` frontend component with radio buttons + explanatory descriptions
- Write 20+ tests covering Abjad calculations, script detection, auto-selection, and API integration

---

## OBJECTIVES

1. **Add Abjad system to framework** — Implement the full Abjad letter→number mapping (28 Arabic + 4 Persian extras) in `NumerologyEngine` with the same reduction and profile functions
2. **Script detection utility** — Python function `detect_script(text) → 'persian' | 'latin' | 'mixed'` using Unicode range 0x0600-0x06FF, plus TypeScript equivalent
3. **Auto-selection logic** — Determine the best numerology system based on name script + user locale + settings preference, with manual override
4. **API integration** — Add optional `numerology_system` field to reading request models, pass through to framework bridge
5. **Settings persistence** — Read/write `numerology_system` preference from `oracle_settings` table (schema from Session 1)
6. **Frontend selector** — Three-option radio group (Pythagorean, Chaldean, Abjad) + Auto-detect toggle with brief descriptions of each system

---

## PREREQUISITES

- [ ] Session 6 completed — `services/oracle/oracle_service/framework_bridge.py` exists and `MasterOrchestrator` is importable
- [ ] Session 7 completed — `UserProfile` dataclass has `numerology_system` field, all 5 reading functions pass it through to framework
- [ ] `numerology_ai_framework/personal/numerology_engine.py` exists with `NumerologyEngine` class
- Verification:
  ```bash
  test -f services/oracle/oracle_service/framework_bridge.py && echo "Bridge OK"
  test -f numerology_ai_framework/personal/numerology_engine.py && echo "NumerologyEngine OK"
  python3 -c "from numerology_ai_framework.personal.numerology_engine import NumerologyEngine; print('Import OK')"
  ```

---

## CRITICAL FINDING: Abjad Not Yet in Framework

The framework's `NumerologyEngine` (at `numerology_ai_framework/personal/numerology_engine.py`) currently only has:

- `PYTHAGOREAN` dict — A=1...Z=8 (line 22-49)
- `CHALDEAN` dict — A=1...Z=7, no letter=9 (line 51-78)
- `expression_number()` checks `system == "pythagorean"` else uses Chaldean (line 118-126)

**There is no Abjad support.** This session must add it to the framework engine before building the selection logic around it. The `logic/NUMEROLOGY_SYSTEMS.md` reference doc describes Abjad as: "Arabic/Persian letters with traditional values: ا=1 ب=2 ج=3 ... غ=1000. Persian extras: پ=2 چ=3 ژ=7 گ=20. Same reduction principle."

---

## FILES TO CREATE

- `numerology_ai_framework/personal/abjad_table.py` — Abjad letter→value mapping as a standalone module (keeps NumerologyEngine clean)
- `services/oracle/oracle_service/utils/__init__.py` — Package init
- `services/oracle/oracle_service/utils/script_detector.py` — Python script detection: `detect_script()`, `contains_persian()`, `auto_select_system()`
- `frontend/src/utils/scriptDetector.ts` — TypeScript script detection: `detectScript()`, `containsPersian()`, `autoSelectSystem()`
- `frontend/src/components/oracle/NumerologySystemSelector.tsx` — Radio group component
- `services/oracle/tests/test_numerology_selection.py` — Backend tests (script detection, auto-selection, Abjad integration)
- `numerology_ai_framework/tests/test_abjad.py` — Framework-level Abjad calculation tests
- `frontend/src/utils/__tests__/scriptDetector.test.ts` — Frontend script detection tests

## FILES TO MODIFY

- `numerology_ai_framework/personal/numerology_engine.py` — Add Abjad system support (import table, update `expression_number()`, `soul_urge()`, `personality_number()`, `complete_profile()`)
- `services/oracle/oracle_service/framework_bridge.py` — Add `resolve_numerology_system()` that applies auto-detection before calling framework
- `api/app/models/oracle.py` — Add `numerology_system` field to `ReadingRequest`, `QuestionRequest`, `NameReadingRequest`, `MultiUserReadingRequest`
- `api/app/routers/oracle.py` — Pass `numerology_system` from request body to service layer
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — Integrate `NumerologySystemSelector`

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Abjad Letter Table (~30 min)

**Tasks:**

1. Create `numerology_ai_framework/personal/abjad_table.py` with the complete Abjad numeral mapping:

   ```python
   """Abjad numeral system — traditional Arabic/Persian letter-to-number mapping.

   The Abjad system assigns numerical values to the 28 Arabic letters
   plus 4 additional Persian letters. Used for numerological analysis
   of Persian and Arabic names.
   """

   # Standard 28 Arabic Abjad letters (Abjad Hawaz ordering)
   ABJAD_TABLE: dict[str, int] = {
       # Units (1-9)
       "\u0627": 1,   # ا  alef
       "\u0628": 2,   # ب  ba
       "\u062C": 3,   # ج  jim
       "\u062F": 4,   # د  dal
       "\u0647": 5,   # ه  ha
       "\u0648": 6,   # و  vav
       "\u0632": 7,   # ز  za
       "\u062D": 8,   # ح  ha (guttural)
       "\u0637": 9,   # ط  ta (emphatic)
       # Tens (10-90)
       "\u064A": 10,  # ی  ya
       "\u06A9": 20,  # ک  kaf (Persian form)
       "\u0643": 20,  # ك  kaf (Arabic form)
       "\u0644": 30,  # ل  lam
       "\u0645": 40,  # م  mim
       "\u0646": 50,  # ن  nun
       "\u0633": 60,  # س  sin
       "\u0639": 70,  # ع  ain
       "\u0641": 80,  # ف  fa
       "\u0635": 90,  # ص  sad
       # Hundreds (100-900)
       "\u0642": 100, # ق  qaf
       "\u0631": 200, # ر  ra
       "\u0634": 300, # ش  shin
       "\u062A": 400, # ت  ta
       "\u062B": 500, # ث  sa (tha)
       "\u062E": 600, # خ  kha
       "\u0630": 700, # ذ  dhal
       "\u0636": 800, # ض  dad
       "\u0638": 900, # ظ  za (emphatic)
       "\u063A": 1000,# غ  ghain
       # Persian-specific letters (map to closest Arabic equivalent values)
       "\u067E": 2,   # پ  pe → same as ba (2)
       "\u0686": 3,   # چ  che → same as jim (3)
       "\u0698": 7,   # ژ  zhe → same as za (7)
       "\u06AF": 20,  # گ  gaf → same as kaf (20)
   }

   # Common diacritics and modifiers to ignore during calculation
   IGNORED_CHARS: set[str] = {
       "\u0640",  # ـ  tatweel (kashida)
       "\u064B",  # ً  fathatan
       "\u064C",  # ٌ  dammatan
       "\u064D",  # ٍ  kasratan
       "\u064E",  # َ  fatha
       "\u064F",  # ُ  damma
       "\u0650",  # ِ  kasra
       "\u0651",  # ّ  shadda (doubled letter — counted once)
       "\u0652",  # ْ  sukun
       "\u0654",  # ٔ  hamza above
       "\u0670",  # ٰ  superscript alef
       "\u200C",  # ZWNJ (zero-width non-joiner, common in Persian)
       "\u200D",  # ZWJ (zero-width joiner)
   }

   # Alef variants — all map to alef value (1)
   ALEF_VARIANTS: dict[str, int] = {
       "\u0622": 1,   # آ  alef madda
       "\u0623": 1,   # أ  alef hamza above
       "\u0625": 1,   # إ  alef hamza below
       "\u0671": 1,   # ٱ  alef wasla
   }
   ```

2. Add a `get_abjad_value(char: str) -> int` helper function:

   ```python
   def get_abjad_value(char: str) -> int:
       """Get the Abjad numerical value for a single character.
       Returns 0 for non-Abjad characters (spaces, digits, Latin, etc.)."""
       if char in ABJAD_TABLE:
           return ABJAD_TABLE[char]
       if char in ALEF_VARIANTS:
           return ALEF_VARIANTS[char]
       if char in IGNORED_CHARS:
           return 0
       return 0
   ```

3. Add a `name_to_abjad_sum(name: str) -> int` function:

   ```python
   def name_to_abjad_sum(name: str) -> int:
       """Calculate raw Abjad sum for a name string."""
       return sum(get_abjad_value(c) for c in name)
   ```

**Checkpoint:**

- [ ] `abjad_table.py` has 28+ Arabic letters + 4 Persian letters + alef variants
- [ ] `get_abjad_value("ا")` returns 1
- [ ] `get_abjad_value("پ")` returns 2 (Persian pe)
- [ ] `name_to_abjad_sum("علی")` returns 70+30+10 = 110
- Verify: `cd numerology_ai_framework && python3 -c "from personal.abjad_table import name_to_abjad_sum; print(name_to_abjad_sum('علی'))"`

STOP if checkpoint fails

---

### Phase 2: Integrate Abjad into NumerologyEngine (~45 min)

**Tasks:**

1. Update `numerology_ai_framework/personal/numerology_engine.py`:

   Add import at top:

   ```python
   from personal.abjad_table import get_abjad_value, ABJAD_TABLE, IGNORED_CHARS
   ```

   Update `expression_number()`:

   ```python
   @staticmethod
   def expression_number(full_name: str, system: str = "pythagorean") -> int:
       """Expression from full name. Supports pythagorean, chaldean, abjad."""
       if system == "abjad":
           value = sum(get_abjad_value(c) for c in full_name)
           return NumerologyEngine.digital_root(value) if value > 0 else 0
       table = (
           NumerologyEngine.PYTHAGOREAN
           if system == "pythagorean"
           else NumerologyEngine.CHALDEAN
       )
       value = sum(table.get(c, 0) for c in full_name.upper() if c.isalpha())
       return NumerologyEngine.digital_root(value)
   ```

2. Update `soul_urge()` — Abjad does not have a vowel/consonant distinction the same way Latin scripts do. For Abjad, the "soul urge" is calculated from the **hidden letters** (harakat/short vowels implied but not written). Since Abjad names are typically written without short vowels, use the **alef-family** characters as the "vowel equivalent":

   ```python
   # Abjad "vowel equivalents" — letters that represent long vowels
   ABJAD_VOWEL_LETTERS = {"\u0627", "\u0648", "\u064A",  # alef, vav, ya
                           "\u0622", "\u0623", "\u0625", "\u0671"}  # alef variants
   ```

   ```python
   @staticmethod
   def soul_urge(full_name: str, system: str = "pythagorean") -> int:
       if system == "abjad":
           value = sum(get_abjad_value(c) for c in full_name
                       if c in NumerologyEngine.ABJAD_VOWEL_LETTERS)
           return NumerologyEngine.digital_root(value) if value > 0 else 0
       # ... existing code unchanged ...
   ```

3. Update `personality_number()` — consonant equivalent for Abjad = all non-vowel letters:

   ```python
   @staticmethod
   def personality_number(full_name: str, system: str = "pythagorean") -> int:
       if system == "abjad":
           value = sum(get_abjad_value(c) for c in full_name
                       if c not in NumerologyEngine.ABJAD_VOWEL_LETTERS
                       and get_abjad_value(c) > 0)
           return NumerologyEngine.digital_root(value) if value > 0 else 0
       # ... existing code unchanged ...
   ```

4. Update `complete_profile()` — no structural change needed, just ensure `system="abjad"` flows through all calls.

5. Update docstrings to mention all three systems.

**Checkpoint:**

- [ ] `NumerologyEngine.expression_number("علی", "abjad")` returns a valid single digit or master number
- [ ] `NumerologyEngine.soul_urge("علی", "abjad")` returns a valid result (alef=1, ya=10 → sum=11 → master 11)
- [ ] `NumerologyEngine.personality_number("علی", "abjad")` returns a valid result (ain=70 + lam=30 → 100 → 1)
- [ ] `NumerologyEngine.complete_profile("علی", 1, 1, 2000, 2026, 2, 10, system="abjad")` returns full profile dict
- [ ] Existing Pythagorean/Chaldean tests still pass
- Verify: `cd numerology_ai_framework && python3 -c "from personal.numerology_engine import NumerologyEngine; p = NumerologyEngine.complete_profile('علی', 1, 1, 2000, 2026, 2, 10, system='abjad'); print(f'LP={p[\"life_path\"][\"number\"]}, Expr={p[\"expression\"]}, Soul={p[\"soul_urge\"]}')"` && `python3 tests/test_all.py`

STOP if checkpoint fails

---

### Phase 3: Script Detection Utilities (~30 min)

**Tasks:**

1. Create `services/oracle/oracle_service/utils/__init__.py` (empty init).

2. Create `services/oracle/oracle_service/utils/script_detector.py`:

   ```python
   """Detect script type in text — Persian/Arabic vs Latin.

   Used for auto-selecting the appropriate numerology system.
   Persian/Arabic Unicode range: U+0600 to U+06FF (Arabic block)
   plus U+FB50 to U+FDFF (Arabic Presentation Forms-A)
   and U+FE70 to U+FEFF (Arabic Presentation Forms-B).
   """

   import re
   from typing import Literal

   # Regex for Arabic/Persian characters
   _PERSIAN_ARABIC_RE = re.compile(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]")
   _LATIN_RE = re.compile(r"[A-Za-z]")

   ScriptType = Literal["persian", "latin", "mixed", "unknown"]


   def contains_persian(text: str) -> bool:
       """Return True if text contains any Persian/Arabic characters."""
       return bool(_PERSIAN_ARABIC_RE.search(text))


   def contains_latin(text: str) -> bool:
       """Return True if text contains any Latin alphabetic characters."""
       return bool(_LATIN_RE.search(text))


   def detect_script(text: str) -> ScriptType:
       """Detect the dominant script in a text string.

       Returns:
           'persian' — text contains Persian/Arabic chars, no Latin
           'latin'   — text contains Latin chars, no Persian/Arabic
           'mixed'   — text contains both
           'unknown' — text contains neither (digits, symbols only)
       """
       has_persian = contains_persian(text)
       has_latin = contains_latin(text)

       if has_persian and has_latin:
           return "mixed"
       if has_persian:
           return "persian"
       if has_latin:
           return "latin"
       return "unknown"


   def auto_select_system(
       name: str,
       locale: str = "en",
       user_preference: str = "auto",
   ) -> str:
       """Auto-select the best numerology system.

       Priority:
       1. Manual override (user_preference != 'auto') → use that
       2. Name contains Persian/Arabic characters → 'abjad'
       3. Locale is 'fa' → 'abjad'
       4. Default → 'pythagorean'

       Args:
           name: The name to analyze
           locale: User's locale ('en', 'fa')
           user_preference: 'auto', 'pythagorean', 'chaldean', or 'abjad'

       Returns:
           One of: 'pythagorean', 'chaldean', 'abjad'
       """
       if user_preference != "auto":
           return user_preference

       if contains_persian(name):
           return "abjad"

       if locale.lower().startswith("fa"):
           return "abjad"

       return "pythagorean"
   ```

3. Create `frontend/src/utils/scriptDetector.ts`:

   ```typescript
   /**
    * Detect script type in text for numerology system auto-selection.
    * Persian/Arabic Unicode range: U+0600 to U+06FF.
    */

   export type ScriptType = "persian" | "latin" | "mixed" | "unknown";
   export type NumerologySystem = "pythagorean" | "chaldean" | "abjad" | "auto";

   const PERSIAN_ARABIC_RE = /[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
   const LATIN_RE = /[A-Za-z]/;

   export function containsPersian(text: string): boolean {
     return PERSIAN_ARABIC_RE.test(text);
   }

   export function containsLatin(text: string): boolean {
     return LATIN_RE.test(text);
   }

   export function detectScript(text: string): ScriptType {
     const hasPersian = containsPersian(text);
     const hasLatin = containsLatin(text);
     if (hasPersian && hasLatin) return "mixed";
     if (hasPersian) return "persian";
     if (hasLatin) return "latin";
     return "unknown";
   }

   export function autoSelectSystem(
     name: string,
     locale: string = "en",
     userPreference: NumerologySystem = "auto",
   ): Exclude<NumerologySystem, "auto"> {
     if (userPreference !== "auto") return userPreference;
     if (containsPersian(name)) return "abjad";
     if (locale.toLowerCase().startsWith("fa")) return "abjad";
     return "pythagorean";
   }
   ```

**Checkpoint:**

- [ ] `detect_script("علی")` → `"persian"`
- [ ] `detect_script("Alice")` → `"latin"`
- [ ] `detect_script("علی Alice")` → `"mixed"`
- [ ] `auto_select_system("علی")` → `"abjad"`
- [ ] `auto_select_system("Alice", locale="fa")` → `"abjad"`
- [ ] `auto_select_system("Alice", locale="en")` → `"pythagorean"`
- [ ] `auto_select_system("Alice", user_preference="chaldean")` → `"chaldean"`
- Verify: `python3 -c "from services.oracle.oracle_service.utils.script_detector import auto_select_system, detect_script; print(detect_script('علی'), auto_select_system('علی'))"`

STOP if checkpoint fails

---

### Phase 4: Framework Bridge Integration (~30 min)

**Tasks:**

1. Update `services/oracle/oracle_service/framework_bridge.py`:

   Add import:

   ```python
   from services.oracle.oracle_service.utils.script_detector import auto_select_system
   ```

   Add `resolve_numerology_system()` function:

   ```python
   def resolve_numerology_system(
       user: UserProfile,
       locale: str = "en",
   ) -> str:
       """Resolve the effective numerology system for a reading.

       If user's numerology_system is 'auto', detects based on name script + locale.
       Otherwise uses the explicit setting.
       """
       return auto_select_system(
           name=user.full_name,
           locale=locale,
           user_preference=user.numerology_system,
       )
   ```

2. Update each of the 5 reading functions (`generate_time_reading`, `generate_name_reading`, `generate_question_reading`, `generate_daily_reading`, `generate_multi_user_reading`) to:
   - Accept optional `locale: str = "en"` parameter
   - Call `resolve_numerology_system(user, locale)` before building framework kwargs
   - Override `user.numerology_system` with the resolved value in the kwargs passed to `MasterOrchestrator`

   Example for `generate_time_reading()`:

   ```python
   def generate_time_reading(
       user: UserProfile,
       hour: int, minute: int, second: int,
       target_date: datetime | None = None,
       locale: str = "en",
   ) -> ReadingResult:
       resolved_system = resolve_numerology_system(user, locale)
       kwargs = user.to_framework_kwargs()
       kwargs["numerology_system"] = resolved_system
       kwargs["current_hour"] = hour
       kwargs["current_minute"] = minute
       kwargs["current_second"] = second
       if target_date:
           kwargs["current_date"] = target_date
       # ... rest of function ...
   ```

3. For `generate_name_reading()`, use the `name_to_analyze` parameter for script detection:
   ```python
   def generate_name_reading(
       user: UserProfile,
       name_to_analyze: str,
       target_date: datetime | None = None,
       locale: str = "en",
   ) -> ReadingResult:
       # For name readings, detect script from the analyzed name, not the user's name
       resolved_system = auto_select_system(
           name=name_to_analyze,
           locale=locale,
           user_preference=user.numerology_system,
       )
       # ...
   ```

**Checkpoint:**

- [ ] `resolve_numerology_system()` exists and returns correct system
- [ ] Time reading with Persian user name resolves to "abjad" when system is "auto"
- [ ] Name reading with Persian `name_to_analyze` resolves to "abjad" even if user profile is English
- [ ] Explicit system preference ("chaldean") overrides auto-detection
- Verify: `python3 -c "from services.oracle.oracle_service.utils.script_detector import auto_select_system; print(auto_select_system('حمزه', 'en', 'auto'))"`

STOP if checkpoint fails

---

### Phase 5: API Layer Changes (~30 min)

**Tasks:**

1. Update `api/app/models/oracle.py` — Add `numerology_system` field to request models:

   ```python
   from typing import Literal

   NumerologySystemType = Literal["pythagorean", "chaldean", "abjad", "auto"]

   class ReadingRequest(BaseModel):
       datetime: str | None = None
       extended: bool = False
       numerology_system: NumerologySystemType = "auto"

   class QuestionRequest(BaseModel):
       question: str
       numerology_system: NumerologySystemType = "auto"

   class NameReadingRequest(BaseModel):
       name: str
       numerology_system: NumerologySystemType = "auto"

   class MultiUserReadingRequest(BaseModel):
       users: list[MultiUserInput]
       primary_user_index: int = 0
       include_interpretation: bool = True
       numerology_system: NumerologySystemType = "auto"
       # ... existing validation ...
   ```

2. Update `api/app/routers/oracle.py` reading endpoints to pass `numerology_system` through:

   For each reading endpoint (`create_reading`, `create_question_sign`, `create_name_reading`, `create_multi_user_reading`):
   - Extract `body.numerology_system` from request
   - Pass it to the service layer (which passes to framework bridge)
   - Store the resolved system in the `oracle_readings` record (in the `numerology_system` column added by Session 1)

   The exact wiring depends on how Sessions 6-7 restructured the service layer. The key principle: `numerology_system` flows from `request body` → `API router` → `OracleReadingService` → `framework_bridge` → `MasterOrchestrator.generate_reading(numerology_system=...)`.

3. The `oracle_readings.numerology_system` column (added by Session 1, migration 012) stores the resolved system for each reading. Update `store_reading()` call to include `numerology_system=resolved_system`.

**Checkpoint:**

- [ ] `ReadingRequest` accepts `numerology_system` parameter
- [ ] `QuestionRequest` accepts `numerology_system` parameter
- [ ] `NameReadingRequest` accepts `numerology_system` parameter
- [ ] `MultiUserReadingRequest` accepts `numerology_system` parameter
- [ ] Default is "auto" for all request models
- Verify: `python3 -c "from app.models.oracle import ReadingRequest; r = ReadingRequest(numerology_system='abjad'); print(r.numerology_system)"` (run from `api/`)

STOP if checkpoint fails

---

### Phase 6: Settings Persistence (~20 min)

**Tasks:**

1. The `oracle_settings` table (created by Session 1, migration 012) already has a `numerology_system` column with `CHECK(numerology_system IN ('pythagorean', 'chaldean', 'abjad', 'auto'))` and default `'auto'`.

2. Add a settings read/write utility or use the existing `oracle_settings` ORM (if Session 1-5 created one). If no ORM exists yet, create a minimal one:

   Create `api/app/orm/oracle_settings.py` (if it doesn't already exist):

   ```python
   """SQLAlchemy ORM model for oracle_settings table."""
   from datetime import datetime
   from sqlalchemy import Integer, String, Boolean, ForeignKey, func
   from sqlalchemy.orm import Mapped, mapped_column
   from app.database import Base

   class OracleSettings(Base):
       __tablename__ = "oracle_settings"

       id: Mapped[int] = mapped_column(primary_key=True)
       user_id: Mapped[int] = mapped_column(
           Integer, ForeignKey("oracle_users.id", ondelete="CASCADE"),
           unique=True, nullable=False
       )
       language: Mapped[str] = mapped_column(String(10), server_default="en")
       theme: Mapped[str] = mapped_column(String(20), server_default="light")
       numerology_system: Mapped[str] = mapped_column(String(20), server_default="auto")
       default_timezone_hours: Mapped[int] = mapped_column(Integer, server_default="0")
       default_timezone_minutes: Mapped[int] = mapped_column(Integer, server_default="0")
       daily_reading_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true")
       notifications_enabled: Mapped[bool] = mapped_column(Boolean, server_default="false")
       created_at: Mapped[datetime] = mapped_column(server_default=func.now())
       updated_at: Mapped[datetime] = mapped_column(
           server_default=func.now(), onupdate=func.now()
       )
   ```

3. Add helper functions to read/write the numerology system preference:

   In the framework bridge or a new settings service:

   ```python
   def get_user_numerology_preference(db: Session, oracle_user_id: int) -> str:
       """Get user's preferred numerology system from settings. Defaults to 'auto'."""
       settings = db.query(OracleSettings).filter(
           OracleSettings.user_id == oracle_user_id
       ).first()
       return settings.numerology_system if settings else "auto"
   ```

4. Register ORM import in `api/app/main.py`:
   ```python
   import app.orm.oracle_settings  # noqa: F401
   ```

**Checkpoint:**

- [ ] `OracleSettings` ORM maps all columns from `oracle_settings` table
- [ ] `get_user_numerology_preference()` returns "auto" for users without settings
- [ ] Settings can be read for a given oracle_user_id
- Verify: `python3 -c "from app.orm.oracle_settings import OracleSettings; print(OracleSettings.__tablename__)"` (run from `api/`)

STOP if checkpoint fails

---

### Phase 7: Frontend Component (~45 min)

**Tasks:**

1. Create `frontend/src/components/oracle/NumerologySystemSelector.tsx`:

   ```typescript
   interface NumerologySystemSelectorProps {
     value: NumerologySystem;
     onChange: (system: NumerologySystem) => void;
     userName?: string; // For auto-detect hint
     disabled?: boolean;
   }
   ```

   Component structure:
   - Radio group with 4 options: Auto-detect (default), Pythagorean, Chaldean, Abjad
   - Each option has a label and brief description:
     - **Auto-detect** — "Automatically selects based on name script and language"
     - **Pythagorean** — "Western system (A=1, B=2...Z=8). Best for English names"
     - **Chaldean** — "Ancient Babylonian system. Alternative for English names"
     - **Abjad** — "Traditional Arabic/Persian system (ا=1, ب=2...). For Persian names"
   - When Auto-detect is selected and `userName` is provided, show a hint: "Detected: [system]" using `autoSelectSystem()` from `scriptDetector.ts`
   - Use `useTranslation()` for i18n — all labels need Persian translations
   - RTL-aware layout (descriptions flow correctly in both LTR and RTL)
   - Tailwind styling consistent with existing Oracle form components (check `OracleConsultationForm.tsx`, `SignTypeSelector.tsx` patterns)

2. Update `frontend/src/components/oracle/OracleConsultationForm.tsx`:
   - Add state: `const [numerologySystem, setNumerologySystem] = useState<NumerologySystem>("auto")`
   - Import and render `<NumerologySystemSelector>` in the form, after the sign type selector
   - Pass `numerologySystem` in the API request body when submitting readings
   - The auto-detect hint should react to the user's name (from `userName` prop)

3. Add i18n keys for both English and Persian locales:

   English (`frontend/src/locales/en.json`):

   ```json
   {
     "numerology.selector.title": "Numerology System",
     "numerology.selector.auto": "Auto-detect",
     "numerology.selector.auto.desc": "Automatically selects based on name script",
     "numerology.selector.pythagorean": "Pythagorean",
     "numerology.selector.pythagorean.desc": "Western system, best for English names",
     "numerology.selector.chaldean": "Chaldean",
     "numerology.selector.chaldean.desc": "Ancient Babylonian alternative",
     "numerology.selector.abjad": "Abjad",
     "numerology.selector.abjad.desc": "Traditional Arabic/Persian system",
     "numerology.selector.detected": "Detected: {{system}}"
   }
   ```

   Persian (`frontend/src/locales/fa.json`):

   ```json
   {
     "numerology.selector.title": "سیستم حروف‌شناسی",
     "numerology.selector.auto": "تشخیص خودکار",
     "numerology.selector.auto.desc": "انتخاب خودکار بر اساس خط نام",
     "numerology.selector.pythagorean": "فیثاغورسی",
     "numerology.selector.pythagorean.desc": "سیستم غربی، مناسب نام‌های انگلیسی",
     "numerology.selector.chaldean": "کلدانی",
     "numerology.selector.chaldean.desc": "سیستم بابلی باستانی",
     "numerology.selector.abjad": "ابجد",
     "numerology.selector.abjad.desc": "سیستم سنتی عربی/فارسی",
     "numerology.selector.detected": "تشخیص داده شده: {{system}}"
   }
   ```

**Checkpoint:**

- [ ] `NumerologySystemSelector.tsx` renders 4 radio options
- [ ] Auto-detect shows "Detected: [system]" hint when username is provided
- [ ] `OracleConsultationForm.tsx` includes the selector
- [ ] API request includes `numerology_system` field
- [ ] Persian translations exist for all selector labels
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | head -20` (should have no new type errors)

STOP if checkpoint fails

---

### Phase 8: Tests (~60 min)

**Tasks:**

1. Create `numerology_ai_framework/tests/test_abjad.py`:

   ```
   test_abjad_alef_value            — ا = 1
   test_abjad_persian_pe            — پ = 2
   test_abjad_ali_sum               — علی = 70+30+10 = 110
   test_abjad_hamzeh_sum            — حمزه = 8+40+7+5 = 60
   test_abjad_expression_ali        — expression_number("علی", "abjad") = digital_root(110) = 2
   test_abjad_expression_hamzeh     — expression_number("حمزه", "abjad") = digital_root(60) = 6
   test_abjad_soul_urge             — soul_urge uses vowel-equivalent letters (alef, vav, ya)
   test_abjad_personality            — personality uses non-vowel letters
   test_abjad_complete_profile       — complete_profile with system="abjad" returns full dict
   test_abjad_does_not_break_latin   — "Alice" with "abjad" returns 0 (no Abjad chars → expression=0)
   test_pythagorean_unchanged        — Existing test vector still passes (regression)
   test_chaldean_unchanged           — Existing test vector still passes (regression)
   ```

2. Create `services/oracle/tests/test_numerology_selection.py`:

   ```
   test_detect_script_persian       — "علی" → "persian"
   test_detect_script_latin         — "Alice" → "latin"
   test_detect_script_mixed         — "علی Alice" → "mixed"
   test_detect_script_unknown       — "123" → "unknown"
   test_contains_persian_true       — "سلام" → True
   test_contains_persian_false      — "Hello" → False
   test_auto_select_persian_name    — Persian name + auto → "abjad"
   test_auto_select_english_name    — English name + auto → "pythagorean"
   test_auto_select_fa_locale       — English name + fa locale + auto → "abjad"
   test_auto_select_manual_override — Any name + explicit "chaldean" → "chaldean"
   test_resolve_numerology_system   — Through framework bridge function
   ```

3. Create `frontend/src/utils/__tests__/scriptDetector.test.ts`:

   ```
   test_detect_script_persian        — "علی" → "persian"
   test_detect_script_latin          — "Alice" → "latin"
   test_detect_script_mixed          — "Ali علی" → "mixed"
   test_auto_select_persian          — autoSelectSystem("علی") → "abjad"
   test_auto_select_english          — autoSelectSystem("Alice") → "pythagorean"
   test_auto_select_fa_locale        — autoSelectSystem("Alice", "fa") → "abjad"
   test_auto_select_manual_override  — autoSelectSystem("Alice", "en", "chaldean") → "chaldean"
   ```

4. Run all test suites:

   ```bash
   # Framework tests (including new Abjad tests)
   cd numerology_ai_framework && python3 tests/test_all.py && python3 tests/test_abjad.py

   # Oracle service tests
   cd services/oracle && python3 -m pytest tests/test_numerology_selection.py -v

   # Frontend tests
   cd frontend && npx vitest run src/utils/__tests__/scriptDetector.test.ts
   ```

**Checkpoint:**

- [ ] All 12 Abjad framework tests pass
- [ ] All 11 script detection/selection tests pass
- [ ] All 7 frontend script detector tests pass
- [ ] No regressions in existing framework tests (`test_all.py` still passes)
- Verify: `cd numerology_ai_framework && python3 tests/test_all.py && echo "Framework OK" && cd ../.. && cd services/oracle && python3 -m pytest tests/test_numerology_selection.py -v && echo "Selection OK"`

STOP if checkpoint fails

---

### Phase 9: Final Verification & Quality (~20 min)

**Tasks:**

1. Run formatting and linting:

   ```bash
   cd numerology_ai_framework && python3 -m black personal/abjad_table.py personal/numerology_engine.py tests/test_abjad.py
   cd services/oracle && python3 -m black oracle_service/utils/ tests/test_numerology_selection.py && python3 -m ruff check --fix .
   cd api && python3 -m black . && python3 -m ruff check --fix .
   cd frontend && npx prettier --write src/utils/scriptDetector.ts src/components/oracle/NumerologySystemSelector.tsx
   ```

2. Verify end-to-end: Generate a reading with each system:

   ```bash
   python3 -c "
   from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator
   from datetime import datetime

   # Pythagorean (English name)
   r1 = MasterOrchestrator.generate_reading('Alice Johnson', 15, 7, 1990, datetime(2026, 2, 10), numerology_system='pythagorean')
   print(f'Pythagorean LP={r1[\"numerology\"][\"life_path\"][\"number\"]}, Expr={r1[\"numerology\"][\"expression\"]}')

   # Chaldean (English name, different system)
   r2 = MasterOrchestrator.generate_reading('Alice Johnson', 15, 7, 1990, datetime(2026, 2, 10), numerology_system='chaldean')
   print(f'Chaldean LP={r2[\"numerology\"][\"life_path\"][\"number\"]}, Expr={r2[\"numerology\"][\"expression\"]}')

   # Abjad (Persian name)
   r3 = MasterOrchestrator.generate_reading('حمزه', 22, 4, 1999, datetime(2026, 2, 10), numerology_system='abjad')
   print(f'Abjad LP={r3[\"numerology\"][\"life_path\"][\"number\"]}, Expr={r3[\"numerology\"][\"expression\"]}')
   print('All 3 systems OK')
   "
   ```

3. Verify TypeScript compiles:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

4. Verify Pythagorean and Chaldean produce different Expression numbers for the same English name (they should — the letter tables are different):
   ```bash
   python3 -c "
   from numerology_ai_framework.personal.numerology_engine import NumerologyEngine
   p = NumerologyEngine.expression_number('Alice Johnson', 'pythagorean')
   c = NumerologyEngine.expression_number('Alice Johnson', 'chaldean')
   assert p != c, f'Expected different: pythagorean={p}, chaldean={c}'
   print(f'Pythagorean={p}, Chaldean={c} — correctly different')
   "
   ```

**Checkpoint:**

- [ ] All 3 systems produce valid readings
- [ ] Pythagorean != Chaldean expression for same English name
- [ ] Abjad produces valid (non-zero) expression for Persian name
- [ ] Life Path is system-independent (always from birthdate math)
- [ ] TypeScript compiles without errors
- [ ] No linting errors

STOP if checkpoint fails

---

## TESTS TO WRITE

### `numerology_ai_framework/tests/test_abjad.py`

| Test Function                     | What It Verifies                                      |
| --------------------------------- | ----------------------------------------------------- |
| `test_abjad_alef_value`           | ا (alef) maps to 1                                    |
| `test_abjad_persian_pe`           | پ (pe) maps to 2                                      |
| `test_abjad_ali_sum`              | "علی" raw sum = 110                                   |
| `test_abjad_hamzeh_sum`           | "حمزه" raw sum = 60                                   |
| `test_abjad_expression_ali`       | Expression number of "علی" = digital_root(110) = 2    |
| `test_abjad_expression_hamzeh`    | Expression number of "حمزه" = digital_root(60) = 6    |
| `test_abjad_soul_urge`            | Soul urge uses alef/vav/ya as vowel equivalents       |
| `test_abjad_personality`          | Personality uses non-vowel Abjad letters              |
| `test_abjad_complete_profile`     | Full profile dict with all expected keys              |
| `test_abjad_does_not_break_latin` | English name with "abjad" system returns 0 expression |
| `test_pythagorean_unchanged`      | "DAVE" expression still = 5 (regression check)        |
| `test_chaldean_unchanged`         | Chaldean letter values unchanged (regression check)   |

### `services/oracle/tests/test_numerology_selection.py`

| Test Function                      | What It Verifies                        |
| ---------------------------------- | --------------------------------------- |
| `test_detect_script_persian`       | Persian text detected correctly         |
| `test_detect_script_latin`         | Latin text detected correctly           |
| `test_detect_script_mixed`         | Mixed text detected correctly           |
| `test_detect_script_unknown`       | Digits-only returns "unknown"           |
| `test_contains_persian_true`       | Persian chars detected                  |
| `test_contains_persian_false`      | English chars not flagged as Persian    |
| `test_auto_select_persian_name`    | Persian name auto-selects "abjad"       |
| `test_auto_select_english_name`    | English name auto-selects "pythagorean" |
| `test_auto_select_fa_locale`       | FA locale auto-selects "abjad"          |
| `test_auto_select_manual_override` | Manual preference overrides auto-detect |
| `test_resolve_numerology_system`   | Bridge-level resolution function works  |

### `frontend/src/utils/__tests__/scriptDetector.test.ts`

| Test Function                      | What It Verifies                                         |
| ---------------------------------- | -------------------------------------------------------- |
| `test_detect_script_persian`       | detectScript("علی") → "persian"                          |
| `test_detect_script_latin`         | detectScript("Alice") → "latin"                          |
| `test_detect_script_mixed`         | detectScript("Ali علی") → "mixed"                        |
| `test_auto_select_persian`         | autoSelectSystem("علی") → "abjad"                        |
| `test_auto_select_english`         | autoSelectSystem("Alice") → "pythagorean"                |
| `test_auto_select_fa_locale`       | autoSelectSystem("Alice", "fa") → "abjad"                |
| `test_auto_select_manual_override` | autoSelectSystem("Alice", "en", "chaldean") → "chaldean" |

**Total: 30 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] Abjad system produces valid numerology numbers for Persian names (expression, soul urge, personality are non-zero)
- [ ] All 3 systems (Pythagorean, Chaldean, Abjad) work through `MasterOrchestrator.generate_reading()`
- [ ] `detect_script()` correctly identifies persian/latin/mixed/unknown text in both Python and TypeScript
- [ ] `auto_select_system()` selects Abjad for Persian names, Pythagorean for English, respects manual override
- [ ] API reading endpoints accept optional `numerology_system` parameter (defaults to "auto")
- [ ] `oracle_settings.numerology_system` preference is readable from database
- [ ] Frontend `NumerologySystemSelector` renders 4 options with i18n labels
- [ ] Auto-detect shows detected system hint when user name is provided
- [ ] Persian translations exist for all selector labels
- [ ] Life Path number is system-independent (same for all 3 systems — birthdate math only)
- [ ] No regressions: existing Pythagorean/Chaldean calculations unchanged
- [ ] All 30+ tests pass across 3 test files
- Verify all:
  ```bash
  test -f numerology_ai_framework/personal/abjad_table.py && \
  test -f services/oracle/oracle_service/utils/script_detector.py && \
  test -f frontend/src/utils/scriptDetector.ts && \
  test -f frontend/src/components/oracle/NumerologySystemSelector.tsx && \
  test -f numerology_ai_framework/tests/test_abjad.py && \
  test -f services/oracle/tests/test_numerology_selection.py && \
  grep -q "abjad" numerology_ai_framework/personal/numerology_engine.py && \
  grep -q "numerology_system" api/app/models/oracle.py && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                                      | Expected Behavior                                                               | Recovery Path                                                                                                                                  |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ----------------------------- | ---------------------------------------------------------- |
| English name passed with system="abjad"                       | Expression/soul_urge/personality all return 0 (no Abjad chars found)            | Auto-detect would have chosen "pythagorean" — this is a manual misuse, not a crash. The reading still generates with Life Path from birthdate. |
| Persian name passed with system="pythagorean"                 | Expression/soul_urge/personality all return 0 (no Latin chars found)            | Auto-detect would have chosen "abjad". Same as above — reading still generates.                                                                |
| Mixed script name (e.g., "Ali علی") with system="auto"        | Auto-detect picks "abjad" (Persian presence takes priority)                     | If user wants Pythagorean, they must explicitly set it. The `mixed` detection is logged for future UX improvements.                            |
| `oracle_settings` table doesn't exist yet (Session 1 not run) | `get_user_numerology_preference()` falls back to "auto"                         | Graceful degradation — no crash. Settings feature just doesn't persist until Session 1 migration runs.                                         |
| Invalid system string (e.g., "tarot")                         | API validation rejects with 422 — Pydantic `Literal` type enforces valid values | No special handling needed — Pydantic does it.                                                                                                 |
| Name is entirely digits/symbols                               | `detect_script()` returns "unknown", auto-select defaults to "pythagorean"      | No Abjad or Latin chars found — system falls through to default.                                                                               |
| Alef variants (آ أ إ) in name                                 | All map to Abjad value 1 via `ALEF_VARIANTS` dict                               | Correctly handled — common Persian/Arabic orthographic variants.                                                                               |
| Shadda (ّ) doubling marker                                    | Counted as 0 (ignored) — the letter it doubles is already counted once          | Per traditional Abjad convention. Some traditions count the letter twice — document this as a known simplification.                            |
| Framework import fails                                        | Reading functions catch `ImportError` and return clear error message            | Session 6 prerequisite check catches this early.                                                                                               |
| TypeScript type mismatch                                      | `NumerologySystem` type is `"pythagorean"                                       | "chaldean"                                                                                                                                     | "abjad" | "auto"` — compile-time safety | Type errors caught by `tsc --noEmit` in verification step. |

---

## DESIGN DECISIONS

| Decision                          | Choice                                                       | Rationale                                                                                                                                                           |
| --------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Abjad table as separate module    | `abjad_table.py` (not inline in NumerologyEngine)            | Keeps the 40+ character mapping clean and testable. NumerologyEngine stays focused on calculation logic.                                                            |
| Vowel equivalents for Abjad       | Alef (ا), Vav (و), Ya (ی) + alef variants                    | Arabic/Persian has 3 "long vowel" letters. Short vowels are diacritics (usually omitted in names). This is the standard approach in Abjad numerology.               |
| Script detection threshold        | Any Persian char → "persian" (even 1 char)                   | Conservative approach: if a name has any Persian characters, it's likely a Persian name with some transliteration mixed in.                                         |
| Auto-detect priority              | Manual > Name script > Locale > Default                      | Most specific wins. A Persian name should use Abjad even if the UI locale is English (e.g., diaspora user).                                                         |
| Abjad for English names returns 0 | Intentional (not an error)                                   | The Abjad table only has Arabic/Persian characters. An English name has no matching chars → sum=0 → expression=0. This is correct — Abjad doesn't apply to English. |
| Life Path independent of system   | Always uses birthdate math (digital_root of date components) | Life Path is universal across all numerology systems — it's purely mathematical. Only name-based numbers differ.                                                    |
| ORM for oracle_settings           | Create if not already existing                               | Session 1 creates the SQL table, but the ORM mapping might not exist yet. Defensive creation with checks.                                                           |

---

## HANDOFF

**Created:**

- `numerology_ai_framework/personal/abjad_table.py` (Abjad letter→value mapping + helpers)
- `numerology_ai_framework/tests/test_abjad.py` (12 tests)
- `services/oracle/oracle_service/utils/__init__.py`
- `services/oracle/oracle_service/utils/script_detector.py` (detect_script, auto_select_system)
- `services/oracle/tests/test_numerology_selection.py` (11 tests)
- `frontend/src/utils/scriptDetector.ts` (TypeScript equivalent)
- `frontend/src/utils/__tests__/scriptDetector.test.ts` (7 tests)
- `frontend/src/components/oracle/NumerologySystemSelector.tsx` (UI component)
- `api/app/orm/oracle_settings.py` (if not already existing)

**Modified:**

- `numerology_ai_framework/personal/numerology_engine.py` (Abjad system support in expression, soul_urge, personality)
- `services/oracle/oracle_service/framework_bridge.py` (resolve_numerology_system, locale parameter)
- `api/app/models/oracle.py` (numerology_system field on 4 request models)
- `api/app/routers/oracle.py` (pass numerology_system through to service)
- `api/app/main.py` (register oracle_settings ORM import)
- `frontend/src/components/oracle/OracleConsultationForm.tsx` (integrate selector)
- `frontend/src/locales/en.json` (numerology selector i18n keys)
- `frontend/src/locales/fa.json` (numerology selector Persian translations)

**Next session needs:**

- **Session 9 (Signal Processing & Patterns)** depends on:
  - All 3 numerology systems producing valid readings — patterns may differ per system
  - `framework_bridge.py` resolving the system before generating readings — patterns are extracted from the resolved reading
- **Session 10 (FC60 Stamp Display)** depends on:
  - FC60 stamps being system-independent (they are — stamps come from date/time, not names)
  - This session does not affect FC60 functionality
- **Session 13+ (AI & Reading Types)** depends on:
  - `numerology_system` being stored in `oracle_readings.numerology_system` column — AI needs to know which system was used to interpret results correctly
  - Abjad number meanings may differ from Pythagorean — AI interpretation prompts need system context
- **Session 19+ (Frontend)** depends on:
  - `NumerologySystemSelector.tsx` existing and working — will be integrated into broader form layouts
  - i18n keys existing for both locales
