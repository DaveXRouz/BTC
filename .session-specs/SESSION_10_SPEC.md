# SESSION 10 SPEC — Framework Integration: FC60 Stamp Display & Validation

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 3-4 hours
**Complexity:** Medium-High
**Dependencies:** Session 6 (framework bridge — creates `framework_bridge.py`, deletes old engines)

---

## TL;DR

- Add **stamp validation API endpoint** `POST /api/oracle/validate-stamp` using the framework's `ChecksumValidator`
- Create **FC60StampDisplay** React component — renders FC60 stamps with animal/element colors, half-day marker, tooltips, and copy-to-clipboard
- Create **StampComparison** React component — side-by-side stamp display for multi-user readings with shared elements highlighted
- Add **stamp validation helper** to `framework_bridge.py` that exposes `ChecksumValidator.verify_chk` for the API layer
- Update **TypeScript types** and **i18n** files for FC60 stamp data from the framework output structure

---

## OBJECTIVES

1. **Expose stamp validation** — API endpoint that accepts an FC60 stamp string and returns valid/invalid + decoded components
2. **Create FC60StampDisplay component** — Beautiful rendering of FC60 stamps with animal symbols, element coloring, half-day indicator, segment tooltips, and clipboard copy
3. **Create StampComparison component** — Multi-user stamp side-by-side display highlighting shared animals/elements
4. **Add stamp utilities to framework bridge** — Validation, decoding, and formatting functions that wrap framework classes
5. **Update TypeScript types** — Replace legacy `FC60Data` interface with framework-aligned `FC60StampData` interface
6. **Add i18n translations** — English and Persian labels for all FC60 stamp segments, animals, elements, and weekday names

---

## PREREQUISITES

- [ ] Framework exists at `numerology_ai_framework/` with `core/fc60_stamp_engine.py`, `core/checksum_validator.py`, `core/base60_codec.py`
- [ ] Session 6 has created `services/oracle/oracle_service/framework_bridge.py` (framework bridge module)
- [ ] API router exists at `api/app/routers/oracle.py`
- [ ] Frontend types at `frontend/src/types/index.ts`
- [ ] Frontend oracle component dir at `frontend/src/components/oracle/`
- Verification:
  ```bash
  test -f numerology_ai_framework/core/fc60_stamp_engine.py && \
  test -f numerology_ai_framework/core/checksum_validator.py && \
  test -f numerology_ai_framework/core/base60_codec.py && \
  test -f api/app/routers/oracle.py && \
  test -f frontend/src/types/index.ts && \
  test -d frontend/src/components/oracle && \
  echo "All prerequisite files OK"
  ```

---

## FRAMEWORK FC60 STAMP REFERENCE

The framework's `FC60StampEngine.encode()` returns a dict with these fields:

| Field           | Example                       | Description                       |
| --------------- | ----------------------------- | --------------------------------- |
| `fc60`          | `"VE-OX-OXFI ☀OX-RUWU-RAWU"`  | Full FC60 stamp string            |
| `iso`           | `"2026-02-06T01:15:00+08:00"` | ISO-8601 datetime                 |
| `j60`           | `"TIFI-DRMT-GOER-PIMT"`       | Julian Day Number in base-60      |
| `y60`           | `"HOMT-ROFI"`                 | Year in base-60                   |
| `y2k`           | `"SNFI"`                      | Year offset from 2000 in base-60  |
| `chk`           | `"TIMT"`                      | Weighted checksum token           |
| `tz60`          | `"+OXMT-RAWU"`                | Timezone in base-60               |
| `_weekday_name` | `"Venus"`                     | Weekday name (planet-based)       |
| `_planet`       | `"Venus"`                     | Ruling planet of the day          |
| `_domain`       | `"Love, Beauty, Harmony"`     | Planet's domain                   |
| `_half_marker`  | `"☀"`                         | AM/PM: ☀ (U+2600) or 🌙 (U+1F319) |
| `_hour_animal`  | `"OX"`                        | 2-char animal for the hour        |
| `_month_animal` | `"OX"`                        | 2-char animal for the month       |
| `_dom_token`    | `"OXFI"`                      | 4-char token for day-of-month     |

**Critical encoding rules (from framework CLAUDE.md):**

- Month: `ANIMALS[month - 1]` — January = RA (index 0)
- Hour in time stamp: 2-char `ANIMALS[hour % 12]`, NOT 4-char token60
- CHK uses LOCAL date/time values, not UTC-adjusted
- HALF marker: ☀ (U+2600) if hour < 12, 🌙 (U+1F319) if hour >= 12

**12 Animals:** RA(Rat), OX(Ox), TI(Tiger), RU(Rabbit), DR(Dragon), SN(Snake), HO(Horse), GO(Goat), MO(Monkey), RO(Rooster), DO(Dog), PI(Pig)

**5 Elements:** WU(Wood), FI(Fire), ER(Earth), MT(Metal), WA(Water)

**Token formula:** `token60(n) = ANIMALS[n // 5] + ELEMENTS[n % 5]`

**Stamp format:** `WD-MO-DOM HALF+HOUR-MINUTE-SECOND`

- WD = weekday token (SU/LU/MA/ME/JO/VE/SA)
- MO = month animal (2-char)
- DOM = day-of-month token (4-char)
- HALF = ☀ or 🌙
- HOUR = hour animal (2-char)
- MINUTE = minute token (4-char)
- SECOND = second token (4-char)

---

## FILES TO CREATE

- `frontend/src/components/oracle/FC60StampDisplay.tsx` — Main stamp display component
- `frontend/src/components/oracle/StampComparison.tsx` — Multi-user stamp comparison
- `frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx` — Component tests
- `frontend/src/components/oracle/__tests__/StampComparison.test.tsx` — Comparison tests
- `services/oracle/tests/test_stamp_validation.py` — Backend stamp validation tests
- `api/tests/test_stamp_endpoint.py` — API endpoint tests

## FILES TO MODIFY

- `services/oracle/oracle_service/framework_bridge.py` — Add stamp validation/decode functions
- `api/app/routers/oracle.py` — Add `POST /api/oracle/validate-stamp` endpoint
- `api/app/models/oracle.py` — Add `StampValidateRequest`, `StampValidateResponse` Pydantic models
- `frontend/src/types/index.ts` — Add `FC60StampData` interface (framework-aligned), update `FC60Extended`
- `frontend/src/services/api.ts` — Add `oracle.validateStamp()` method
- `frontend/src/i18n/config.ts` — Add FC60-specific translation keys (if i18n is inline config) OR create separate locale files

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Framework Bridge — Stamp Validation Functions (~30 min)

**Tasks:**

1. Add stamp validation and decoding functions to `services/oracle/oracle_service/framework_bridge.py`:

   ```python
   # Key function signatures to add:

   def validate_fc60_stamp(stamp_string: str) -> dict:
       """Validate an FC60 stamp and return decoded components.

       Uses FC60StampEngine.decode_stamp() for parsing and
       ChecksumValidator for verification.

       Returns:
           {
               "valid": bool,
               "stamp": str,           # original stamp
               "decoded": {            # parsed components (if valid)
                   "weekday_token": str,
                   "weekday_name": str,
                   "month": int,
                   "month_token": str,
                   "day": int,
                   "dom_token": str,
                   "half": str,         # "AM" or "PM"
                   "hour": int,
                   "hour_animal": str,
                   "minute": int,
                   "minute_token": str,
                   "second": int,
                   "second_token": str,
               },
               "error": str | None,    # error message if invalid
           }
       """

   def format_stamp_for_display(reading: dict) -> dict:
       """Extract and format FC60 stamp data from a framework reading for frontend display.

       Takes the full reading dict from MasterOrchestrator.generate_reading()
       and returns a display-ready dict with all stamp segments annotated.

       Returns:
           {
               "fc60": str,
               "j60": str,
               "y60": str,
               "chk": str,
               "weekday": {"token": str, "name": str, "planet": str, "domain": str},
               "month": {"token": str, "animal_name": str, "index": int},
               "dom": {"token": str, "value": int, "animal_name": str, "element_name": str},
               "time": {
                   "half": str,  # "☀" or "🌙"
                   "hour": {"token": str, "animal_name": str, "value": int},
                   "minute": {"token": str, "value": int, "animal_name": str, "element_name": str},
                   "second": {"token": str, "value": int, "animal_name": str, "element_name": str},
               },
           }
       """
   ```

2. Import the framework classes:

   ```python
   from numerology_ai_framework.core.fc60_stamp_engine import FC60StampEngine
   from numerology_ai_framework.core.checksum_validator import ChecksumValidator
   from numerology_ai_framework.core.base60_codec import Base60Codec
   ```

3. Helper to annotate a 4-char token with animal/element names:
   ```python
   def _describe_token(token: str) -> dict:
       """Break a 4-char FC60 token into animal + element with names."""
       n = Base60Codec.digit60(token)
       animal_idx = n // 5
       element_idx = n % 5
       return {
           "token": token,
           "value": n,
           "animal_name": Base60Codec.get_animal_name(animal_idx),
           "element_name": Base60Codec.get_element_name(element_idx),
       }
   ```

**Checkpoint:**

- [ ] `validate_fc60_stamp()` function exists in `framework_bridge.py`
- [ ] `format_stamp_for_display()` function exists in `framework_bridge.py`
- [ ] Functions import from `numerology_ai_framework.core.*` (not from deleted engines)
- [ ] `_describe_token()` helper returns animal + element names
- Verify:
  ```bash
  grep -q "validate_fc60_stamp" services/oracle/oracle_service/framework_bridge.py && \
  grep -q "format_stamp_for_display" services/oracle/oracle_service/framework_bridge.py && \
  grep -q "ChecksumValidator" services/oracle/oracle_service/framework_bridge.py && \
  echo "Bridge stamp functions OK"
  ```

STOP if checkpoint fails

---

### Phase 2: API Endpoint — Stamp Validation (~30 min)

**Tasks:**

1. Add Pydantic models to `api/app/models/oracle.py`:

   ```python
   class StampValidateRequest(BaseModel):
       stamp: str  # FC60 stamp string to validate

   class StampSegment(BaseModel):
       token: str
       value: int | None = None
       animal_name: str | None = None
       element_name: str | None = None

   class StampDecodedResponse(BaseModel):
       weekday_token: str
       weekday_name: str
       month: int | None = None
       month_token: str
       day: int | None = None
       dom_token: str
       half: str | None = None          # "AM" or "PM"
       hour: int | None = None
       hour_animal: str | None = None
       minute: int | None = None
       minute_token: str | None = None
       second: int | None = None
       second_token: str | None = None

   class StampValidateResponse(BaseModel):
       valid: bool
       stamp: str
       decoded: StampDecodedResponse | None = None
       error: str | None = None
   ```

2. Add endpoint to `api/app/routers/oracle.py`:

   ```python
   @router.post("/validate-stamp", response_model=StampValidateResponse)
   def validate_stamp(
       request: StampValidateRequest,
       user: dict = Depends(get_current_user),
   ):
       """Validate an FC60 stamp string and return decoded components."""
       # Import from framework bridge (Session 6 creates this)
       from services.oracle.oracle_service.framework_bridge import validate_fc60_stamp

       result = validate_fc60_stamp(request.stamp)
       return StampValidateResponse(**result)
   ```

   Note: The bridge function handles all validation logic. The API layer just wraps it with auth and serialization.

3. Route note: The endpoint is at `/api/oracle/validate-stamp` (oracle router is mounted at `/api/oracle/`). Requires authentication (any role).

**Checkpoint:**

- [ ] `StampValidateRequest` and `StampValidateResponse` models exist in `api/app/models/oracle.py`
- [ ] `POST /api/oracle/validate-stamp` endpoint exists in `api/app/routers/oracle.py`
- [ ] Endpoint requires authentication
- [ ] No hardcoded paths (uses framework_bridge import)
- Verify:
  ```bash
  grep -q "StampValidateRequest" api/app/models/oracle.py && \
  grep -q "StampValidateResponse" api/app/models/oracle.py && \
  grep -q "validate-stamp" api/app/routers/oracle.py && \
  echo "API stamp endpoint OK"
  ```

STOP if checkpoint fails

---

### Phase 3: TypeScript Types & API Client (~20 min)

**Tasks:**

1. Add framework-aligned FC60 stamp interface to `frontend/src/types/index.ts`:

   ```typescript
   // ─── FC60 Stamp (Framework-aligned) ───

   export interface FC60StampSegment {
     token: string;
     value?: number;
     animalName?: string;
     elementName?: string;
   }

   export interface FC60StampWeekday {
     token: string;
     name: string;
     planet: string;
     domain: string;
   }

   export interface FC60StampTime {
     half: string; // "☀" or "🌙"
     hour: FC60StampSegment;
     minute: FC60StampSegment;
     second: FC60StampSegment;
   }

   export interface FC60StampData {
     fc60: string; // Full stamp string
     j60: string; // Julian Day in base-60
     y60: string; // Year in base-60
     chk: string; // Checksum token
     weekday: FC60StampWeekday;
     month: FC60StampSegment & { index: number };
     dom: FC60StampSegment;
     time: FC60StampTime | null; // null for date-only stamps
   }

   export interface StampValidateResponse {
     valid: boolean;
     stamp: string;
     decoded: Record<string, unknown> | null;
     error: string | null;
   }
   ```

   The existing `FC60Data` and `FC60Extended` interfaces remain for backward compat during migration — they will be deprecated in later sessions.

2. Add stamp validation to `frontend/src/services/api.ts` in the `oracle` object:

   ```typescript
   validateStamp: (stamp: string) =>
     request<StampValidateResponse>("/oracle/validate-stamp", {
       method: "POST",
       body: JSON.stringify({ stamp }),
     }),
   ```

**Checkpoint:**

- [ ] `FC60StampData` interface exists in `frontend/src/types/index.ts`
- [ ] `FC60StampSegment`, `FC60StampWeekday`, `FC60StampTime` interfaces exist
- [ ] `StampValidateResponse` interface exists
- [ ] `oracle.validateStamp()` method added to `frontend/src/services/api.ts`
- [ ] No `any` types used
- Verify:
  ```bash
  grep -q "FC60StampData" frontend/src/types/index.ts && \
  grep -q "FC60StampSegment" frontend/src/types/index.ts && \
  grep -q "validateStamp" frontend/src/services/api.ts && \
  echo "TypeScript types OK"
  ```

STOP if checkpoint fails

---

### Phase 4: FC60StampDisplay Component (~60 min)

**Tasks:**

1. Create `frontend/src/components/oracle/FC60StampDisplay.tsx`:

   Key interface:

   ```typescript
   interface FC60StampDisplayProps {
     stamp: FC60StampData;
     size?: "compact" | "normal" | "large";
     showTooltips?: boolean;
     showCopyButton?: boolean;
   }
   ```

2. Visual design specifications:
   - **Layout:** Horizontal stamp display with date and time parts separated by a space
   - **Element colors** (Tailwind classes):
     - WU (Wood) → `text-green-500` / `bg-green-500/10`
     - FI (Fire) → `text-red-500` / `bg-red-500/10`
     - ER (Earth) → `text-amber-700` / `bg-amber-700/10`
     - MT (Metal) → `text-yellow-400` / `bg-yellow-400/10`
     - WA (Water) → `text-blue-500` / `bg-blue-500/10`
   - **Animal display:** Show 2-letter code with full name in tooltip (e.g., hover "OX" → "Ox — Endurance, patience")
   - **Half-day marker:** ☀ rendered in yellow, 🌙 rendered as-is (emoji)
   - **Monospace font:** Use `font-mono` (JetBrains Mono if available) for stamp text
   - **Copy button:** Small clipboard icon button, copies full FC60 string to clipboard. Show brief "Copied!" toast.
   - **Token segments:** Each 4-char token rendered as a pill/badge with element background color
   - **Separator dashes:** Rendered as lighter text between segments

3. Tooltip content for each segment:
   - WD token → "Wednesday (Mercury — Communication, Intelligence)"
   - MO token → "February (Ox — Endurance)"
   - DOM token → "Day 6 (Ox Fire — OXFI)"
   - HALF → "Morning (before noon)" / "Afternoon (after noon)"
   - HOUR → "Hour 1 (Ox — Endurance)"
   - MINUTE → "Minute 15 (Rabbit Wood — RUWU)"
   - SECOND → "Second 0 (Rat Wood — RAWU)"

4. Compact mode: Single line, no tooltips, smaller font. Used in reading history lists.
5. Normal mode: Full display with tooltips. Default in reading results.
6. Large mode: Extra spacing, larger font. Used in standalone stamp view.

7. Accessibility:
   - `aria-label` on the stamp container with readable description
   - Each segment has `title` attribute for native tooltip fallback
   - Copy button has `aria-label="Copy FC60 stamp to clipboard"`
   - Color is not the only indicator (element name shown on hover)

**Checkpoint:**

- [ ] `FC60StampDisplay.tsx` exists at `frontend/src/components/oracle/`
- [ ] Component accepts `FC60StampData` prop
- [ ] Element colors mapped (5 colors for 5 elements)
- [ ] Copy-to-clipboard functionality works
- [ ] Tooltips show animal/element descriptions
- [ ] Three size variants: compact, normal, large
- [ ] No `any` types
- Verify:
  ```bash
  test -f frontend/src/components/oracle/FC60StampDisplay.tsx && \
  grep -q "FC60StampData" frontend/src/components/oracle/FC60StampDisplay.tsx && \
  grep -q "clipboard" frontend/src/components/oracle/FC60StampDisplay.tsx && \
  echo "FC60StampDisplay OK"
  ```

STOP if checkpoint fails

---

### Phase 5: StampComparison Component (~30 min)

**Tasks:**

1. Create `frontend/src/components/oracle/StampComparison.tsx`:

   Key interface:

   ```typescript
   interface StampComparisonProps {
     stamps: {
       userName: string;
       stamp: FC60StampData;
     }[];
     highlightShared?: boolean;
   }
   ```

2. Side-by-side layout:
   - Each user's stamp in a column (max 5 columns for multi-user readings)
   - User name as column header
   - Stamp segments aligned vertically for easy comparison
   - On mobile: stack vertically instead of side-by-side

3. Shared element highlighting:
   - When `highlightShared=true`, find animals/elements that appear in 2+ stamps
   - Highlight shared animals with a ring/border effect (e.g., `ring-2 ring-emerald-400`)
   - Show "Shared: OX (Ox)" label below the stamps when animals match
   - Shared elements get a colored underline matching the element color

4. Comparison summary:
   - Count shared animals across stamps
   - Count shared elements across stamps
   - Display: "2 shared animals, 1 shared element" as a summary badge

**Checkpoint:**

- [ ] `StampComparison.tsx` exists at `frontend/src/components/oracle/`
- [ ] Component accepts array of `{userName, stamp}` objects
- [ ] Shared animals/elements highlighted
- [ ] Responsive layout (side-by-side on desktop, stacked on mobile)
- Verify:
  ```bash
  test -f frontend/src/components/oracle/StampComparison.tsx && \
  grep -q "StampComparison" frontend/src/components/oracle/StampComparison.tsx && \
  grep -q "highlightShared" frontend/src/components/oracle/StampComparison.tsx && \
  echo "StampComparison OK"
  ```

STOP if checkpoint fails

---

### Phase 6: i18n — FC60 Translations (~20 min)

**Tasks:**

1. Add FC60-specific translation keys. The i18n config is at `frontend/src/i18n/config.ts`. Check if it uses inline resources or external JSON files. Add translations to whichever format is used.

   English translations needed:

   ```json
   {
     "fc60.title": "Universal Address",
     "fc60.stamp": "FC60 Stamp",
     "fc60.julian_day": "Julian Day",
     "fc60.year": "Year Code",
     "fc60.checksum": "Checksum",
     "fc60.copy": "Copy stamp",
     "fc60.copied": "Copied!",
     "fc60.validate": "Validate Stamp",
     "fc60.valid": "Valid stamp",
     "fc60.invalid": "Invalid stamp",
     "fc60.date_part": "Date",
     "fc60.time_part": "Time",
     "fc60.weekday": "Weekday",
     "fc60.month": "Month",
     "fc60.day": "Day",
     "fc60.hour": "Hour",
     "fc60.minute": "Minute",
     "fc60.second": "Second",
     "fc60.half_am": "Morning",
     "fc60.half_pm": "Afternoon",
     "fc60.comparison_title": "Stamp Comparison",
     "fc60.shared_animals": "Shared animals",
     "fc60.shared_elements": "Shared elements",
     "fc60.animals.RA": "Rat",
     "fc60.animals.OX": "Ox",
     "fc60.animals.TI": "Tiger",
     "fc60.animals.RU": "Rabbit",
     "fc60.animals.DR": "Dragon",
     "fc60.animals.SN": "Snake",
     "fc60.animals.HO": "Horse",
     "fc60.animals.GO": "Goat",
     "fc60.animals.MO": "Monkey",
     "fc60.animals.RO": "Rooster",
     "fc60.animals.DO": "Dog",
     "fc60.animals.PI": "Pig",
     "fc60.elements.WU": "Wood",
     "fc60.elements.FI": "Fire",
     "fc60.elements.ER": "Earth",
     "fc60.elements.MT": "Metal",
     "fc60.elements.WA": "Water"
   }
   ```

   Persian translations needed:

   ```json
   {
     "fc60.title": "آدرس جهانی",
     "fc60.stamp": "مُهر FC60",
     "fc60.julian_day": "روز ژولیانی",
     "fc60.year": "کد سال",
     "fc60.checksum": "جمع کنترلی",
     "fc60.copy": "کپی مُهر",
     "fc60.copied": "کپی شد!",
     "fc60.validate": "اعتبارسنجی مُهر",
     "fc60.valid": "مُهر معتبر",
     "fc60.invalid": "مُهر نامعتبر",
     "fc60.date_part": "تاریخ",
     "fc60.time_part": "زمان",
     "fc60.weekday": "روز هفته",
     "fc60.month": "ماه",
     "fc60.day": "روز",
     "fc60.hour": "ساعت",
     "fc60.minute": "دقیقه",
     "fc60.second": "ثانیه",
     "fc60.half_am": "صبح",
     "fc60.half_pm": "بعدازظهر",
     "fc60.comparison_title": "مقایسه مُهرها",
     "fc60.shared_animals": "حیوانات مشترک",
     "fc60.shared_elements": "عناصر مشترک",
     "fc60.animals.RA": "موش",
     "fc60.animals.OX": "گاو",
     "fc60.animals.TI": "ببر",
     "fc60.animals.RU": "خرگوش",
     "fc60.animals.DR": "اژدها",
     "fc60.animals.SN": "مار",
     "fc60.animals.HO": "اسب",
     "fc60.animals.GO": "بز",
     "fc60.animals.MO": "میمون",
     "fc60.animals.RO": "خروس",
     "fc60.animals.DO": "سگ",
     "fc60.animals.PI": "خوک",
     "fc60.elements.WU": "چوب",
     "fc60.elements.FI": "آتش",
     "fc60.elements.ER": "خاک",
     "fc60.elements.MT": "فلز",
     "fc60.elements.WA": "آب"
   }
   ```

2. All Persian text is valid UTF-8. RTL rendering is handled by the locale direction system (existing from scaffolding).

**Checkpoint:**

- [ ] English FC60 translations added (animals, elements, UI labels)
- [ ] Persian FC60 translations added (all 12 animals, 5 elements, labels in Persian)
- [ ] All Persian text is valid UTF-8
- [ ] Translation keys follow existing naming convention
- Verify:
  ```bash
  grep -q "fc60.animals.RA" frontend/src/i18n/config.ts && \
  grep -q "fc60.elements.WU" frontend/src/i18n/config.ts && \
  echo "i18n FC60 translations OK"
  ```
  (Adjust path if i18n uses separate JSON files instead of inline config)

STOP if checkpoint fails

---

### Phase 7: Tests + Final Verification (~45 min)

**Tasks:**

#### Part A: Backend Tests

1. Create `services/oracle/tests/test_stamp_validation.py`:

   ```python
   # Test the framework bridge stamp functions

   def test_validate_valid_stamp():
       """Valid FC60 stamp returns valid=True with decoded components."""

   def test_validate_invalid_stamp_bad_format():
       """Malformed stamp string returns valid=False with error message."""

   def test_validate_stamp_date_only():
       """Date-only stamp (no time part) validates correctly."""

   def test_format_stamp_for_display_full():
       """Full reading produces display-ready stamp data with all segments."""

   def test_format_stamp_for_display_annotates_tokens():
       """Each token in display data includes animal_name and element_name."""

   def test_describe_token_known_values():
       """Known tokens decode to correct animal + element names."""
       # RAWU → Rat + Wood (value 0)
       # SNFI → Snake + Fire (value 26)
       # PIWA → Pig + Water (value 59)

   def test_validate_stamp_with_test_vectors():
       """Framework test vectors validate correctly through bridge."""
       # TV1: "VE-OX-OXFI ☀OX-RUWU-RAWU" — valid
       # TV2: "SA-RA-RAFI ☀RA-RAWU-RAWU" — valid

   def test_validate_stamp_empty_string():
       """Empty string returns valid=False."""

   def test_validate_stamp_random_text():
       """Non-FC60 text returns valid=False with descriptive error."""

   def test_month_encoding_january_is_ra():
       """Month 1 (January) encodes to animal RA (index 0), not OX."""
   ```

2. Create `api/tests/test_stamp_endpoint.py`:

   ```python
   # Test the API endpoint

   def test_validate_stamp_endpoint_valid():
       """POST /api/oracle/validate-stamp with valid stamp returns 200."""

   def test_validate_stamp_endpoint_invalid():
       """POST /api/oracle/validate-stamp with invalid stamp returns 200 with valid=False."""

   def test_validate_stamp_endpoint_unauthorized():
       """POST /api/oracle/validate-stamp without auth returns 401."""
   ```

#### Part B: Frontend Tests

3. Create `frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx`:

   ```typescript
   // Tests for FC60StampDisplay component

   test("renders full FC60 stamp string");
   test("applies correct element color for Fire token");
   test("applies correct element color for Water token");
   test("applies correct element color for Wood token");
   test("applies correct element color for Metal token");
   test("applies correct element color for Earth token");
   test("shows half-day marker (sun for AM)");
   test("shows half-day marker (moon for PM)");
   test("shows tooltips with animal names on hover");
   test("copy button copies stamp to clipboard");
   test("renders compact size variant");
   test("renders large size variant");
   test("has proper aria-label for accessibility");
   ```

4. Create `frontend/src/components/oracle/__tests__/StampComparison.test.tsx`:

   ```typescript
   test("renders multiple stamps side by side");
   test("shows user names as column headers");
   test("highlights shared animals when enabled");
   test("shows shared elements count");
   ```

**Checkpoint:**

- [ ] `services/oracle/tests/test_stamp_validation.py` has 10+ test functions
- [ ] `api/tests/test_stamp_endpoint.py` has 3+ test functions
- [ ] `frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx` has 10+ tests
- [ ] `frontend/src/components/oracle/__tests__/StampComparison.test.tsx` has 4+ tests
- [ ] All tests use proper assertions (no bare `assert True`)
- Verify:
  ```bash
  test -f services/oracle/tests/test_stamp_validation.py && \
  test -f api/tests/test_stamp_endpoint.py && \
  test -f frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx && \
  test -f frontend/src/components/oracle/__tests__/StampComparison.test.tsx && \
  echo "All test files created"
  ```

Run backend tests:

```bash
cd services/oracle && python3 -m pytest tests/test_stamp_validation.py -v
cd api && python3 -m pytest tests/test_stamp_endpoint.py -v
```

Run frontend tests:

```bash
cd frontend && npx vitest run src/components/oracle/__tests__/FC60StampDisplay.test.tsx src/components/oracle/__tests__/StampComparison.test.tsx
```

STOP if checkpoint fails

---

## TESTS TO WRITE

| #   | Test                                             | File                                               | Verifies                                       |
| --- | ------------------------------------------------ | -------------------------------------------------- | ---------------------------------------------- |
| 1   | `test_validate_valid_stamp`                      | `services/oracle/tests/test_stamp_validation.py`   | Valid stamp returns `valid=True` + decoded     |
| 2   | `test_validate_invalid_stamp_bad_format`         | `services/oracle/tests/test_stamp_validation.py`   | Malformed stamp returns `valid=False`          |
| 3   | `test_validate_stamp_date_only`                  | `services/oracle/tests/test_stamp_validation.py`   | Date-only stamp validates                      |
| 4   | `test_format_stamp_for_display_full`             | `services/oracle/tests/test_stamp_validation.py`   | Display format has all segments                |
| 5   | `test_format_stamp_for_display_annotates_tokens` | `services/oracle/tests/test_stamp_validation.py`   | Tokens have animal/element names               |
| 6   | `test_describe_token_known_values`               | `services/oracle/tests/test_stamp_validation.py`   | RAWU=Rat+Wood, SNFI=Snake+Fire, PIWA=Pig+Water |
| 7   | `test_validate_stamp_with_test_vectors`          | `services/oracle/tests/test_stamp_validation.py`   | Framework TV1/TV2 stamps validate              |
| 8   | `test_validate_stamp_empty_string`               | `services/oracle/tests/test_stamp_validation.py`   | Empty string → `valid=False`                   |
| 9   | `test_validate_stamp_random_text`                | `services/oracle/tests/test_stamp_validation.py`   | Random text → `valid=False` with error         |
| 10  | `test_month_encoding_january_is_ra`              | `services/oracle/tests/test_stamp_validation.py`   | Month 1 = RA (index 0)                         |
| 11  | `test_validate_stamp_endpoint_valid`             | `api/tests/test_stamp_endpoint.py`                 | POST valid stamp → 200                         |
| 12  | `test_validate_stamp_endpoint_invalid`           | `api/tests/test_stamp_endpoint.py`                 | POST invalid stamp → 200, valid=False          |
| 13  | `test_validate_stamp_endpoint_unauthorized`      | `api/tests/test_stamp_endpoint.py`                 | No auth → 401                                  |
| 14  | `renders full FC60 stamp string`                 | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Stamp text visible                             |
| 15  | `applies correct element color for Fire`         | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Fire tokens get red styling                    |
| 16  | `applies correct element color for Water`        | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Water tokens get blue styling                  |
| 17  | `applies correct element color for Wood`         | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Wood tokens get green styling                  |
| 18  | `applies correct element color for Metal`        | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Metal tokens get gold styling                  |
| 19  | `applies correct element color for Earth`        | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Earth tokens get brown styling                 |
| 20  | `shows half-day marker (sun)`                    | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | ☀ rendered for AM                              |
| 21  | `shows half-day marker (moon)`                   | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | 🌙 rendered for PM                             |
| 22  | `shows tooltips with animal names`               | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Tooltip text includes animal name              |
| 23  | `copy button copies stamp`                       | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Clipboard API called                           |
| 24  | `renders compact size variant`                   | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Compact class applied                          |
| 25  | `renders large size variant`                     | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Large class applied                            |
| 26  | `has proper aria-label`                          | `frontend/.../__tests__/FC60StampDisplay.test.tsx` | Accessibility attribute present                |
| 27  | `renders multiple stamps side by side`           | `frontend/.../__tests__/StampComparison.test.tsx`  | Multiple stamps visible                        |
| 28  | `shows user names as headers`                    | `frontend/.../__tests__/StampComparison.test.tsx`  | Column headers match user names                |
| 29  | `highlights shared animals`                      | `frontend/.../__tests__/StampComparison.test.tsx`  | Shared animal has highlight class              |
| 30  | `shows shared elements count`                    | `frontend/.../__tests__/StampComparison.test.tsx`  | Summary badge shows count                      |

Total: **30 tests** (10 backend + 3 API + 13 component + 4 comparison)

---

## ACCEPTANCE CRITERIA

- [ ] `POST /api/oracle/validate-stamp` accepts FC60 stamps and returns valid/invalid + decoded components
- [ ] Framework test vectors (TV1-TV8 from `fc60_stamp_engine.py`) validate correctly through the API
- [ ] `FC60StampDisplay` component renders stamps with element-colored tokens
- [ ] Each stamp segment shows tooltip with animal name, element name, and meaning
- [ ] Copy-to-clipboard button works and shows confirmation
- [ ] `StampComparison` component shows 2-5 stamps side by side with shared elements highlighted
- [ ] All 12 animals and 5 elements translated to Persian in i18n
- [ ] Encoding rules respected: month-1 indexing, 2-char hour animal, CHK uses local time, ☀/🌙 half markers
- [ ] All TypeScript interfaces use proper types (no `any`)
- [ ] Backend tests pass: `cd services/oracle && python3 -m pytest tests/test_stamp_validation.py -v`
- [ ] API tests pass: `cd api && python3 -m pytest tests/test_stamp_endpoint.py -v`
- [ ] Frontend tests pass: `cd frontend && npx vitest run`
- Verify all:
  ```bash
  test -f services/oracle/oracle_service/framework_bridge.py && \
  test -f frontend/src/components/oracle/FC60StampDisplay.tsx && \
  test -f frontend/src/components/oracle/StampComparison.tsx && \
  grep -q "validate_fc60_stamp" services/oracle/oracle_service/framework_bridge.py && \
  grep -q "validate-stamp" api/app/routers/oracle.py && \
  grep -q "FC60StampData" frontend/src/types/index.ts && \
  grep -q "fc60.animals.RA" frontend/src/i18n/config.ts && \
  test -f services/oracle/tests/test_stamp_validation.py && \
  test -f frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                                | Expected Behavior                                                                    | Recovery                                                                     |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| Invalid stamp format (missing parts)                    | `validate_fc60_stamp()` returns `{"valid": false, "error": "..."}`                   | Display error message in UI                                                  |
| Empty stamp string                                      | Returns `{"valid": false, "error": "Empty stamp"}`                                   | Show validation error                                                        |
| Stamp with invalid animal token                         | `Base60Codec.digit60()` raises `ValueError` → caught and returned as error           | Return descriptive error                                                     |
| Stamp with unicode issues                               | Emoji markers (☀/🌙) handled correctly in Python and JavaScript                      | Ensure UTF-8 encoding throughout                                             |
| Framework bridge not yet created (Session 6 incomplete) | API endpoint import fails → `ImportError` → 500                                      | Return 503 Service Unavailable with message "Framework bridge not available" |
| Clipboard API not available (HTTP context)              | `navigator.clipboard.writeText()` fails → fallback to `document.execCommand('copy')` | Graceful fallback or show "Copy not available"                               |
| Multi-user comparison with 1 stamp                      | `StampComparison` renders single stamp without comparison                            | No shared elements shown                                                     |
| Missing time part in stamp                              | `FC60StampDisplay` renders date-only stamp (no time section)                         | `time` prop is null                                                          |
| i18n key missing                                        | `useTranslation()` returns key name as fallback                                      | Animal codes shown as-is (RA, OX, etc.)                                      |
| Non-authenticated request to validate endpoint          | Returns 401 Unauthorized                                                             | Frontend redirects to login                                                  |

---

## HANDOFF

**Created:**

- `frontend/src/components/oracle/FC60StampDisplay.tsx` — Main stamp display component
- `frontend/src/components/oracle/StampComparison.tsx` — Multi-user stamp comparison
- `frontend/src/components/oracle/__tests__/FC60StampDisplay.test.tsx` — 13 component tests
- `frontend/src/components/oracle/__tests__/StampComparison.test.tsx` — 4 comparison tests
- `services/oracle/tests/test_stamp_validation.py` — 10 backend validation tests
- `api/tests/test_stamp_endpoint.py` — 3 API endpoint tests

**Modified:**

- `services/oracle/oracle_service/framework_bridge.py` — Added `validate_fc60_stamp()`, `format_stamp_for_display()`, `_describe_token()`
- `api/app/routers/oracle.py` — Added `POST /api/oracle/validate-stamp` endpoint
- `api/app/models/oracle.py` — Added `StampValidateRequest`, `StampValidateResponse`, `StampSegment`, `StampDecodedResponse`
- `frontend/src/types/index.ts` — Added `FC60StampData`, `FC60StampSegment`, `FC60StampWeekday`, `FC60StampTime`, `StampValidateResponse`
- `frontend/src/services/api.ts` — Added `oracle.validateStamp()` method
- `frontend/src/i18n/config.ts` — Added FC60 animal/element/UI translations (EN + FA)

**Deleted:**

- None

**Next session needs:**

- **Session 11 (Moon, Ganzhi & Cosmic Cycles)** depends on:
  - Framework bridge being functional (from Session 6)
  - i18n pattern established here for adding cosmic cycle translations
  - Component pattern from `FC60StampDisplay` as template for `MoonPhaseDisplay`, `GanzhiDisplay`
- **Session 12 (Heartbeat & Location Engines)** depends on:
  - Framework bridge stamp functions as pattern for heartbeat/location display formatting
- **Session 20 (Reading Results Page)** depends on:
  - `FC60StampDisplay` component — used as the "Universal Address" section in the full reading display
  - `StampComparison` component — used in multi-user reading results
  - `FC60StampData` TypeScript interface — reading results page consumes this type
