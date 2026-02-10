# SESSION 15 SPEC — Reading Flow: Name & Question Readings

**Block:** AI & Reading Types (Sessions 13-18)
**Estimated Duration:** 4-5 hours
**Complexity:** High
**Dependencies:** Session 14 (time reading flow — establishes the reading_orchestrator pattern)

---

## TL;DR

- Build complete Name Reading flow: frontend form with Persian keyboard + "use profile name" button, backend endpoint using `MasterOrchestrator`, AI interpretation of name numerology
- Build complete Question Reading flow: frontend form with large textarea (EN + FA, 500-char limit), backend endpoint that hashes question text into a numerological value, AI interpretation addressing the specific question
- Create `question_analyzer.py` — script detection (Latin vs Persian/Arabic) + letter value summation (Pythagorean/Chaldean/Abjad) + reduction to single digit or master number
- Rewrite existing `/oracle/name` and `/oracle/question` endpoints to use the framework's `MasterOrchestrator` instead of legacy engines
- Update TypeScript types and API client to match new response shapes
- Add i18n translations for both forms (EN + FA)
- 30+ tests covering backend logic, frontend rendering, script detection, and end-to-end flows

---

## OBJECTIVES

1. **Create NameReadingForm.tsx** — Text input with Persian keyboard toggle, "use profile name" button, validation, and loading state
2. **Create QuestionReadingForm.tsx** — Large textarea with character counter, EN/FA support, script auto-detection badge, validation
3. **Create question_analyzer.py** — Script detection engine that identifies Latin (Pythagorean/Chaldean) vs Persian/Arabic (Abjad) text and computes a numerological "question number"
4. **Rewrite name reading backend** — Enhance `NameReadingRequest`/`NameReadingResponse` models, update API endpoint to call `MasterOrchestrator.generate_reading()` with name as primary input
5. **Rewrite question reading backend** — Enhance `QuestionRequest`/`QuestionResponse` models, add question hashing, pass question text + question number to AI context
6. **Update TypeScript types and API client** to match new backend response shapes
7. **Add i18n translations** for both forms in EN and FA locales
8. **Write comprehensive tests** for all new code

---

## PREREQUISITES

- [ ] Session 14 completed — `reading_orchestrator.py` exists and handles time readings
- [ ] Framework available at `numerology_ai_framework/` (for `MasterOrchestrator` + `NumerologyEngine`)
- [ ] Existing oracle endpoints functional (`/oracle/name`, `/oracle/question`)
- [ ] Frontend oracle components exist (`PersianKeyboard`, `UserSelector`, etc.)

Verification:

```bash
test -f services/oracle/oracle_service/reading_orchestrator.py && echo "reading_orchestrator OK (from Session 14)"
test -f numerology_ai_framework/synthesis/master_orchestrator.py && echo "Framework OK"
test -f api/app/routers/oracle.py && echo "Oracle router OK"
test -f frontend/src/components/oracle/PersianKeyboard.tsx && echo "PersianKeyboard OK"
```

---

## EXISTING STATE ANALYSIS

### What EXISTS (Verified in Codebase)

| Component               | File                                                        | Current State                                                                                    |
| ----------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Name endpoint           | `api/app/routers/oracle.py:167-196`                         | POST /oracle/name — calls `svc.get_name_reading(body.name)` via legacy engine                    |
| Question endpoint       | `api/app/routers/oracle.py:135-164`                         | POST /oracle/question — calls `svc.get_question_sign(body.question)` via legacy engine           |
| Name request model      | `api/app/models/oracle.py:100-101`                          | `NameReadingRequest(name: str)` — too simple                                                     |
| Name response model     | `api/app/models/oracle.py:110-116`                          | `NameReadingResponse(name, destiny_number, soul_urge, personality, letters, interpretation)`     |
| Question request model  | `api/app/models/oracle.py:88-89`                            | `QuestionRequest(question: str)` — no reading_type or metadata                                   |
| Question response model | `api/app/models/oracle.py:92-97`                            | `QuestionResponse(question, answer, sign_number, interpretation, confidence)`                    |
| Oracle reading service  | `api/app/services/oracle_reading.py`                        | Uses legacy `engines.oracle.read_name()` and `engines.oracle.question_sign()`                    |
| Frontend API client     | `frontend/src/services/api.ts:76-80`                        | `oracle.name(name)` and `oracle.question(question)` — POST with simple body                      |
| TypeScript types        | `frontend/src/types/index.ts:129-136`                       | `NameReading` and `QuestionResponse` — match current simple models                               |
| PersianKeyboard         | `frontend/src/components/oracle/PersianKeyboard.tsx`        | EXISTS — reusable for both forms                                                                 |
| Consultation form       | `frontend/src/components/oracle/OracleConsultationForm.tsx` | Reference pattern — has question textarea + keyboard toggle                                      |
| Legacy name solver      | `services/oracle/oracle_service/solvers/name_solver.py`     | NameSolver class — uses legacy engines, NOT the framework                                        |
| Legacy numerology       | `services/oracle/oracle_service/engines/numerology.py`      | Pythagorean only — `LETTER_VALUES`, `name_to_number()`, `name_soul_urge()`, `name_personality()` |
| Framework numerology    | `numerology_ai_framework/personal/numerology_engine.py`     | `NumerologyEngine` with Pythagorean + Chaldean, `complete_profile()`                             |

### What Does NOT Exist (Must Create)

| Component             | File                                                     | Purpose                                       |
| --------------------- | -------------------------------------------------------- | --------------------------------------------- |
| Name reading form     | `frontend/src/components/oracle/NameReadingForm.tsx`     | NEW — Dedicated name input form               |
| Question reading form | `frontend/src/components/oracle/QuestionReadingForm.tsx` | NEW — Dedicated question input form           |
| Question analyzer     | `services/oracle/oracle_service/question_analyzer.py`    | NEW — Script detection + question hashing     |
| Abjad letter values   | (inside question_analyzer.py)                            | NEW — Persian/Arabic letter-to-number mapping |

### Key Design Decisions

**1. Framework vs Legacy Engines**
The existing `/oracle/name` and `/oracle/question` endpoints use legacy engines (`engines.oracle.read_name`, `engines.oracle.question_sign`). Session 15 rewrites these to use `MasterOrchestrator.generate_reading()` from the framework, following the same pattern Session 14 establishes for time readings. The legacy endpoints are preserved as fallback during transition.

**2. Question Hashing — Three Numerology Systems**
The master spec requires: "Sum letter values (Pythagorean/Chaldean/Abjad based on detected script)". Implementation:

- Latin text (A-Z only) → Pythagorean system (default) or Chaldean (configurable)
- Persian/Arabic text (Unicode range \u0600-\u06FF) → Abjad system
- Mixed text → Use predominant script

**3. Abjad Values (Standard)**
The Abjad numeral system assigns values to Arabic/Persian letters:

```
ا=1 ب=2 ج=3 د=4 ه=5 و=6 ز=7 ح=8 ط=9
ی=10 ک=20 ل=30 م=40 ن=50 س=60 ع=70 ف=80 ص=90
ق=100 ر=200 ش=300 ت=400 ث=500 خ=600 ذ=700 ض=800 ظ=900 غ=1000
```

Persian extras: پ=2, چ=3, ژ=7, گ=20 (mapped to closest Arabic equivalents)

**4. Name Reading: Name as Numerological Input**
For name readings, the name IS the primary input. The framework generates:

- Expression number (full name letter sum)
- Soul Urge (vowels only)
- Personality (consonants only)
- FC60 stamp for current moment
- AI interpretation weaving name numerology with temporal data

If user has a profile, their DOB enriches the reading (Life Path, Personal Year). If no profile, reading focuses on name numerology + current moment.

**5. Question Reading: Profile Data + Question Context**
For question readings, the framework generates a standard reading using profile data + current time. The question text is:

- Hashed to produce a "question number" (numerological reduction)
- Passed to the AI interpreter as additional context
- The AI addresses the specific question using numerological data as insight

---

## FILES TO CREATE/MODIFY

| Action | File                                                                    | Purpose                                                                     |
| ------ | ----------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| CREATE | `services/oracle/oracle_service/question_analyzer.py`                   | Script detection + question hashing + Abjad values                          |
| CREATE | `frontend/src/components/oracle/NameReadingForm.tsx`                    | Name reading input form with Persian keyboard                               |
| CREATE | `frontend/src/components/oracle/QuestionReadingForm.tsx`                | Question reading textarea with char counter                                 |
| MODIFY | `api/app/models/oracle.py`                                              | Enhance request/response models for framework output                        |
| MODIFY | `api/app/routers/oracle.py`                                             | Rewrite `/oracle/name` and `/oracle/question` to use framework              |
| MODIFY | `api/app/services/oracle_reading.py`                                    | Add framework-based `get_name_reading_v2()` and `get_question_reading_v2()` |
| MODIFY | `services/oracle/oracle_service/reading_orchestrator.py`                | Add `generate_name_reading()` and `generate_question_reading()`             |
| MODIFY | `frontend/src/types/index.ts`                                           | Update `NameReading` and `QuestionResponse` types                           |
| MODIFY | `frontend/src/services/api.ts`                                          | Update `oracle.name()` and `oracle.question()` request shapes               |
| MODIFY | `frontend/src/i18n/locales/en.json`                                     | Add name + question form translations                                       |
| MODIFY | `frontend/src/i18n/locales/fa.json`                                     | Add name + question form translations                                       |
| CREATE | `services/oracle/tests/test_question_analyzer.py`                       | Tests for script detection + Abjad + hashing                                |
| CREATE | `api/tests/test_name_question_readings.py`                              | API endpoint tests for both reading types                                   |
| CREATE | `frontend/src/components/oracle/__tests__/NameReadingForm.test.tsx`     | Frontend component tests                                                    |
| CREATE | `frontend/src/components/oracle/__tests__/QuestionReadingForm.test.tsx` | Frontend component tests                                                    |

---

## IMPLEMENTATION PHASES

### Phase 1: Question Analyzer Engine

**Goal:** Create the script detection and question hashing module.

**Create `services/oracle/oracle_service/question_analyzer.py`:**

```python
"""
Question Analyzer — Script detection + numerological hashing.

Detects whether input text is Latin (Pythagorean/Chaldean) or
Persian/Arabic (Abjad), sums letter values, reduces to single
digit or master number.
"""
```

**Must implement:**

1. `detect_script(text: str) -> str` — Returns `"latin"`, `"persian"`, or `"mixed"`
   - Count Unicode code points in Latin range (A-Z, a-z) vs Persian/Arabic range (\u0600-\u06FF)
   - If >70% one script → return that script
   - If mixed → return `"mixed"` (use predominant)

2. `ABJAD_VALUES: dict[str, int]` — Complete mapping of Arabic + Persian letters to Abjad values
   - Standard 28 Arabic letters + 4 Persian extras (پ, چ, ژ, گ)
   - Values range from 1 (alef) to 1000 (ghayn)

3. `sum_letter_values(text: str, system: str = "auto") -> int` — Raw sum before reduction
   - `system="auto"` → detect script, use appropriate table
   - `system="pythagorean"` → use Pythagorean table (A=1...Z=8)
   - `system="chaldean"` → use Chaldean table
   - `system="abjad"` → use Abjad table
   - Strip non-letter characters before summing

4. `question_number(text: str, system: str = "auto") -> dict` — Full analysis
   - Returns: `{"question_text": str, "detected_script": str, "system_used": str, "raw_sum": int, "question_number": int, "is_master_number": bool}`
   - `question_number` = digital root (preserve master numbers 11, 22, 33)

**Reuse:** Import `NumerologyEngine.digital_root()` from framework or reimplement (4 lines) to avoid path coupling.

**STOP — Phase 1 Checkpoint:**

```bash
cd services/oracle && python3 -c "
from oracle_service.question_analyzer import detect_script, question_number
assert detect_script('Hello world') == 'latin'
assert detect_script('سلام دنیا') == 'persian'
r = question_number('Should I change careers?')
assert 1 <= r['question_number'] <= 33
assert r['detected_script'] == 'latin'
r2 = question_number('آیا شغلم را عوض کنم؟')
assert r2['detected_script'] == 'persian'
assert r2['system_used'] == 'abjad'
print('Phase 1 PASS')
"
```

---

### Phase 2: Name Reading Backend

**Goal:** Rewrite the name reading pipeline to use the framework.

**Step 2a: Update Pydantic models in `api/app/models/oracle.py`**

Enhance `NameReadingRequest`:

```python
class NameReadingRequest(BaseModel):
    name: str                           # Required: the name to analyze
    user_id: int | None = None          # Optional: link to oracle_user for enriched reading
    numerology_system: str = "pythagorean"  # "pythagorean" | "chaldean"
    include_ai: bool = True             # Whether to include AI interpretation
```

Enhance `NameReadingResponse` to include framework output:

```python
class NameReadingResponse(BaseModel):
    name: str
    detected_script: str = "latin"      # Script detected in the name
    numerology_system: str = "pythagorean"
    expression: int                     # Expression number (full name)
    soul_urge: int                      # Soul Urge (vowels)
    personality: int                    # Personality (consonants)
    life_path: int | None = None        # Only if user profile has DOB
    personal_year: int | None = None    # Only if user profile has DOB
    fc60_stamp: dict | None = None      # Current moment FC60 stamp
    moon: dict | None = None            # Current moon phase
    ganzhi: dict | None = None          # Current Ganzhi cycle
    patterns: dict | None = None        # Detected patterns
    confidence: dict | None = None      # Confidence score + factors
    ai_interpretation: str | None = None # AI prose reading
    letter_breakdown: list[dict] = []   # Each letter with value [{letter, value, element}]
    reading_id: int | None = None       # Stored reading ID
```

**Step 2b: Add reading_orchestrator method**

In `services/oracle/oracle_service/reading_orchestrator.py` (created by Session 14), add:

```python
def generate_name_reading(
    self,
    name: str,
    birth_day: int | None = None,
    birth_month: int | None = None,
    birth_year: int | None = None,
    mother_name: str | None = None,
    gender: str | None = None,
    numerology_system: str = "pythagorean",
    include_ai: bool = True,
) -> dict:
    """Generate a name-based reading using the framework."""
```

This method:

1. Calls `MasterOrchestrator.generate_reading()` with `full_name=name` and available profile data
2. If no DOB provided, uses minimal parameters (name + current datetime only)
3. Returns the framework's full output dict enriched with name-specific fields

**Step 2c: Update `api/app/services/oracle_reading.py`**

Add `get_name_reading_v2()` method that:

1. Resolves user profile from `user_id` if provided (get DOB, mother_name from oracle_users)
2. Calls `reading_orchestrator.generate_name_reading()` with resolved data
3. Stores reading in `oracle_readings` table with `sign_type="name"`
4. Returns structured response matching `NameReadingResponse`

**Step 2d: Update router endpoint**

In `api/app/routers/oracle.py`, update `create_name_reading()`:

- Accept enhanced `NameReadingRequest`
- Call `svc.get_name_reading_v2()` instead of `svc.get_name_reading()`
- Return enhanced `NameReadingResponse`
- Preserve legacy endpoint as fallback: if `reading_orchestrator` import fails, fall back to `svc.get_name_reading()`

**STOP — Phase 2 Checkpoint:**

```bash
cd api && python3 -c "
from app.models.oracle import NameReadingRequest, NameReadingResponse
req = NameReadingRequest(name='Alice Johnson')
assert req.numerology_system == 'pythagorean'
resp_data = {
    'name': 'Alice Johnson', 'expression': 8, 'soul_urge': 9,
    'personality': 8, 'confidence': {'score': 80, 'level': 'high'},
}
resp = NameReadingResponse(**resp_data)
assert resp.expression == 8
print('Phase 2 models PASS')
"
```

---

### Phase 3: Question Reading Backend

**Goal:** Rewrite the question reading pipeline with question hashing.

**Step 3a: Update Pydantic models in `api/app/models/oracle.py`**

Enhance `QuestionRequest`:

```python
class QuestionReadingRequest(BaseModel):
    question: str                       # Required: the question text (max 500 chars)
    user_id: int | None = None          # Optional: link to oracle_user for profile-enriched reading
    numerology_system: str = "auto"     # "auto" detects script, or force "pythagorean"/"chaldean"/"abjad"
    include_ai: bool = True             # Whether to include AI interpretation

    @field_validator("question")
    @classmethod
    def validate_question_length(cls, v: str) -> str:
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Question cannot be empty")
        if len(v) > 500:
            raise ValueError("Question must be 500 characters or less")
        return v
```

Enhance `QuestionReadingResponse`:

```python
class QuestionReadingResponse(BaseModel):
    question: str                       # Original question text
    question_number: int                # Numerological reduction of question
    detected_script: str                # "latin" | "persian" | "mixed"
    numerology_system: str              # System used for hashing
    raw_letter_sum: int                 # Pre-reduction sum
    is_master_number: bool              # Whether question_number is 11/22/33
    fc60_stamp: dict | None = None      # Current moment FC60 stamp
    numerology: dict | None = None      # Profile numerology (if user_id provided)
    moon: dict | None = None            # Current moon phase
    ganzhi: dict | None = None          # Current Ganzhi cycle
    patterns: dict | None = None        # Detected patterns
    confidence: dict | None = None      # Confidence score
    ai_interpretation: str | None = None # AI interpretation addressing the question
    reading_id: int | None = None       # Stored reading ID
```

**Step 3b: Add reading_orchestrator method**

In `services/oracle/oracle_service/reading_orchestrator.py`, add:

```python
def generate_question_reading(
    self,
    question: str,
    birth_day: int | None = None,
    birth_month: int | None = None,
    birth_year: int | None = None,
    full_name: str | None = None,
    mother_name: str | None = None,
    gender: str | None = None,
    numerology_system: str = "auto",
    include_ai: bool = True,
) -> dict:
    """Generate a question-based reading with question hashing."""
```

This method:

1. Calls `question_analyzer.question_number()` to hash the question text
2. Calls `MasterOrchestrator.generate_reading()` with available profile data + current time
3. Merges question analysis (question_number, detected_script, raw_sum) into the result
4. If AI enabled, passes question text + question number as additional context to AI interpreter
5. Returns enriched dict

**Step 3c: Update `api/app/services/oracle_reading.py`**

Add `get_question_reading_v2()` method that:

1. Resolves user profile from `user_id` if provided
2. Calls `reading_orchestrator.generate_question_reading()` with resolved data + question text
3. Stores reading in `oracle_readings` table with `sign_type="question"`, `question=question_text`
4. Returns structured response matching `QuestionReadingResponse`

**Step 3d: Update router endpoint**

In `api/app/routers/oracle.py`, update `create_question_sign()`:

- Accept enhanced `QuestionReadingRequest`
- Call `svc.get_question_reading_v2()` instead of `svc.get_question_sign()`
- Return enhanced `QuestionReadingResponse`
- Preserve legacy endpoint as fallback

**STOP — Phase 3 Checkpoint:**

```bash
cd api && python3 -c "
from app.models.oracle import QuestionReadingRequest, QuestionReadingResponse
req = QuestionReadingRequest(question='Should I change careers?')
assert req.numerology_system == 'auto'
# Test validation
try:
    QuestionReadingRequest(question='')
    print('FAIL: empty question should raise')
except Exception:
    print('Empty question validation PASS')
try:
    QuestionReadingRequest(question='x' * 501)
    print('FAIL: long question should raise')
except Exception:
    print('Length validation PASS')
print('Phase 3 models PASS')
"
```

---

### Phase 4: Frontend — NameReadingForm.tsx

**Goal:** Create the name reading form component.

**Create `frontend/src/components/oracle/NameReadingForm.tsx`:**

**Component requirements:**

1. Text input for name with label
2. Persian keyboard toggle button (reuse `PersianKeyboard` component)
3. "Use profile name" button — When a user is selected, pre-fills with `user.name` (or `user.name_persian` for FA locale)
4. Numerology system selector (dropdown: Pythagorean / Chaldean) — default Pythagorean
5. Submit button with loading state
6. Error display (aria-live="polite")
7. All text via `useTranslation()` — no hardcoded strings

**Props interface:**

```typescript
interface NameReadingFormProps {
  userId?: number;
  userName?: string; // Pre-fill option
  userNamePersian?: string; // Persian name pre-fill
  onResult: (result: NameReadingResult) => void;
  onError?: (error: string) => void;
}
```

**Behavior:**

- On submit: call `oracle.name()` API with `{ name, user_id, numerology_system, include_ai: true }`
- Show loading spinner during request
- On success: call `onResult(data)`
- On error: display error message
- Input validation: name must be at least 1 character after trimming

**CSS:** Use existing Tailwind classes matching `OracleConsultationForm.tsx` pattern:

- `bg-nps-bg-input border border-nps-border rounded`
- `text-nps-text focus:outline-none focus:border-nps-oracle-accent`
- Button: `bg-nps-oracle-accent text-nps-bg`

**STOP — Phase 4 Checkpoint:**

```bash
cd frontend && npx tsc --noEmit src/components/oracle/NameReadingForm.tsx 2>&1 | head -5
# Should show no type errors (or only import resolution issues in isolation)
test -f src/components/oracle/NameReadingForm.tsx && echo "NameReadingForm created"
```

---

### Phase 5: Frontend — QuestionReadingForm.tsx

**Goal:** Create the question reading form component.

**Create `frontend/src/components/oracle/QuestionReadingForm.tsx`:**

**Component requirements:**

1. Large textarea for question (rows=5, resizable)
2. Character counter showing `{current}/500` — turns red when approaching limit
3. Persian keyboard toggle (reuse `PersianKeyboard`)
4. Script detection badge — shows "EN" or "FA" based on input content (auto-detected)
5. Numerology system info text — "System: Pythagorean" or "System: Abjad" based on detected script
6. Submit button with loading state
7. Error display
8. All text via `useTranslation()`
9. `dir` attribute auto-switches: `dir="rtl"` when Persian detected, `dir="ltr"` otherwise

**Props interface:**

```typescript
interface QuestionReadingFormProps {
  userId?: number;
  onResult: (result: QuestionReadingResult) => void;
  onError?: (error: string) => void;
}
```

**Script detection (frontend-side for UX only):**

```typescript
function detectScript(text: string): "latin" | "persian" | "mixed" {
  const persianRegex = /[\u0600-\u06FF]/;
  const latinRegex = /[A-Za-z]/;
  const hasPersian = persianRegex.test(text);
  const hasLatin = latinRegex.test(text);
  if (hasPersian && !hasLatin) return "persian";
  if (hasLatin && !hasPersian) return "latin";
  if (hasPersian && hasLatin) return "mixed";
  return "latin"; // default
}
```

**Behavior:**

- Character counter updates on every keystroke
- When over 500 chars, prevent additional input (maxLength attribute)
- Script badge updates in real-time as user types
- On submit: call `oracle.question()` API with `{ question, user_id, numerology_system: "auto", include_ai: true }`
- Show loading spinner during request

**STOP — Phase 5 Checkpoint:**

```bash
cd frontend && npx tsc --noEmit src/components/oracle/QuestionReadingForm.tsx 2>&1 | head -5
test -f src/components/oracle/QuestionReadingForm.tsx && echo "QuestionReadingForm created"
```

---

### Phase 6: TypeScript Types + API Client + i18n

**Goal:** Update frontend types, API calls, and translations.

**Step 6a: Update `frontend/src/types/index.ts`**

Update `NameReading` to match new backend response:

```typescript
export interface NameReading {
  name: string;
  detected_script: string;
  numerology_system: string;
  expression: number;
  soul_urge: number;
  personality: number;
  life_path: number | null;
  personal_year: number | null;
  fc60_stamp: Record<string, unknown> | null;
  moon: MoonData | null;
  ganzhi: GanzhiData | null;
  patterns: Record<string, unknown> | null;
  confidence: { score: number; level: string; factors?: string } | null;
  ai_interpretation: string | null;
  letter_breakdown: { letter: string; value: number; element: string }[];
  reading_id: number | null;
}
```

Update `QuestionResponse` to match new backend response:

```typescript
export interface QuestionReadingResponse {
  question: string;
  question_number: number;
  detected_script: string;
  numerology_system: string;
  raw_letter_sum: number;
  is_master_number: boolean;
  fc60_stamp: Record<string, unknown> | null;
  numerology: NumerologyData | null;
  moon: MoonData | null;
  ganzhi: GanzhiData | null;
  patterns: Record<string, unknown> | null;
  confidence: { score: number; level: string; factors?: string } | null;
  ai_interpretation: string | null;
  reading_id: number | null;
}
```

Update `ConsultationResult` union type to include new shapes.

**Step 6b: Update `frontend/src/services/api.ts`**

Update `oracle.name()`:

```typescript
name: (name: string, userId?: number, system?: string) =>
  request<NameReading>("/oracle/name", {
    method: "POST",
    body: JSON.stringify({
      name,
      user_id: userId,
      numerology_system: system || "pythagorean",
      include_ai: true,
    }),
  }),
```

Update `oracle.question()`:

```typescript
question: (question: string, userId?: number, system?: string) =>
  request<QuestionReadingResponse>("/oracle/question", {
    method: "POST",
    body: JSON.stringify({
      question,
      user_id: userId,
      numerology_system: system || "auto",
      include_ai: true,
    }),
  }),
```

**Step 6c: Add i18n translations**

Add to `frontend/src/i18n/locales/en.json` under `oracle` key:

```json
{
  "name_reading_title": "Name Reading",
  "name_input_label": "Enter a name",
  "name_input_placeholder": "Full name...",
  "use_profile_name": "Use Profile Name",
  "numerology_system": "Numerology System",
  "system_pythagorean": "Pythagorean",
  "system_chaldean": "Chaldean",
  "submit_name_reading": "Generate Name Reading",
  "question_reading_title": "Question Reading",
  "question_input_label": "Ask your question",
  "question_input_placeholder": "Type your question here (up to 500 characters)...",
  "char_count": "{{current}}/{{max}} characters",
  "detected_script": "Detected: {{script}}",
  "script_latin": "English",
  "script_persian": "Persian",
  "script_mixed": "Mixed",
  "submit_question_reading": "Get Answer",
  "question_number_label": "Question Number",
  "master_number_badge": "Master Number"
}
```

Add equivalent Persian translations to `frontend/src/i18n/locales/fa.json`.

**STOP — Phase 6 Checkpoint:**

```bash
cd frontend && npx tsc --noEmit 2>&1 | tail -5
echo "TypeScript compilation check complete"
```

---

### Phase 7: Comprehensive Tests

**Goal:** Write all tests for Session 15 deliverables.

#### Test File 1: `services/oracle/tests/test_question_analyzer.py`

| #   | Test Function                         | What It Verifies                                                                   |
| --- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| 1   | `test_detect_script_latin`            | `detect_script("Hello world")` returns `"latin"`                                   |
| 2   | `test_detect_script_persian`          | `detect_script("سلام دنیا")` returns `"persian"`                                   |
| 3   | `test_detect_script_mixed`            | `detect_script("Hello سلام")` returns `"mixed"`                                    |
| 4   | `test_detect_script_empty`            | `detect_script("")` returns `"latin"` (default)                                    |
| 5   | `test_detect_script_numbers_only`     | `detect_script("12345")` returns `"latin"` (default)                               |
| 6   | `test_pythagorean_letter_sum`         | `sum_letter_values("DAVE", "pythagorean")` == 4+1+4+5 = 14                         |
| 7   | `test_abjad_letter_sum`               | `sum_letter_values("سلام", "abjad")` returns correct sum (60+30+1+40=131)          |
| 8   | `test_question_number_latin`          | `question_number("Should I change?")` returns valid dict with 1-33 question_number |
| 9   | `test_question_number_persian`        | `question_number("آیا تغییر کنم؟")` uses Abjad system                              |
| 10  | `test_question_number_master`         | Test input that produces master number 11, 22, or 33                               |
| 11  | `test_auto_system_detection`          | `sum_letter_values("سلام", "auto")` uses Abjad automatically                       |
| 12  | `test_strip_non_letters`              | `sum_letter_values("Hello! World?", "pythagorean")` ignores punctuation            |
| 13  | `test_digital_root_preserves_masters` | `digital_root(11)` == 11, `digital_root(22)` == 22                                 |
| 14  | `test_abjad_persian_extras`           | Verify پ=2, چ=3, ژ=7, گ=20 are mapped correctly                                    |

#### Test File 2: `api/tests/test_name_question_readings.py`

| #   | Test Function                                    | What It Verifies                                                                               |
| --- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 15  | `test_name_reading_basic`                        | POST /oracle/name with `{"name": "Alice"}` returns 200 with expression, soul_urge, personality |
| 16  | `test_name_reading_with_user_id`                 | POST /oracle/name with `{"name": "Alice", "user_id": 1}` enriches with DOB data                |
| 17  | `test_name_reading_empty_name`                   | POST /oracle/name with `{"name": ""}` returns 422                                              |
| 18  | `test_name_reading_chaldean`                     | POST /oracle/name with `numerology_system: "chaldean"` uses Chaldean values                    |
| 19  | `test_name_reading_stored`                       | Name reading is persisted to oracle_readings table                                             |
| 20  | `test_name_reading_audit_logged`                 | Name reading creates audit log entry                                                           |
| 21  | `test_question_reading_basic`                    | POST /oracle/question with `{"question": "Should I change?"}` returns 200 with question_number |
| 22  | `test_question_reading_persian`                  | POST /oracle/question with Persian text uses Abjad and returns detected_script="persian"       |
| 23  | `test_question_reading_too_long`                 | POST /oracle/question with 501+ chars returns 422                                              |
| 24  | `test_question_reading_empty`                    | POST /oracle/question with empty question returns 422                                          |
| 25  | `test_question_reading_stored`                   | Question reading is persisted with question text                                               |
| 26  | `test_question_reading_includes_question_number` | Response includes `question_number`, `raw_letter_sum`, `is_master_number`                      |
| 27  | `test_question_reading_audit_logged`             | Question reading creates audit log entry                                                       |

#### Test File 3: `frontend/src/components/oracle/__tests__/NameReadingForm.test.tsx`

| #   | Test Function                  | What It Verifies                                                   |
| --- | ------------------------------ | ------------------------------------------------------------------ |
| 28  | `test_renders_name_input`      | Form renders with text input and submit button                     |
| 29  | `test_use_profile_name_button` | Clicking "Use Profile Name" pre-fills the input with userName prop |
| 30  | `test_submit_calls_api`        | Submitting calls oracle.name() with correct parameters             |
| 31  | `test_empty_name_shows_error`  | Submitting empty name shows validation error                       |
| 32  | `test_persian_keyboard_toggle` | Keyboard toggle button shows/hides PersianKeyboard                 |

#### Test File 4: `frontend/src/components/oracle/__tests__/QuestionReadingForm.test.tsx`

| #   | Test Function                     | What It Verifies                                           |
| --- | --------------------------------- | ---------------------------------------------------------- |
| 33  | `test_renders_textarea`           | Form renders with textarea and submit button               |
| 34  | `test_character_counter`          | Character counter updates as user types                    |
| 35  | `test_max_length_enforced`        | Cannot type more than 500 characters                       |
| 36  | `test_script_detection_badge`     | Typing Persian shows "FA" badge, Latin shows "EN"          |
| 37  | `test_submit_calls_api`           | Submitting calls oracle.question() with correct parameters |
| 38  | `test_empty_question_shows_error` | Submitting empty question shows validation error           |

**STOP — Phase 7 Checkpoint:**

```bash
# Backend tests
cd services/oracle && python3 -m pytest tests/test_question_analyzer.py -v 2>&1 | tail -20

# API tests
cd api && python3 -m pytest tests/test_name_question_readings.py -v 2>&1 | tail -20

# Frontend tests
cd frontend && npx vitest run src/components/oracle/__tests__/NameReadingForm.test.tsx --reporter=verbose 2>&1 | tail -20
cd frontend && npx vitest run src/components/oracle/__tests__/QuestionReadingForm.test.tsx --reporter=verbose 2>&1 | tail -20

echo "All Session 15 tests complete"
```

---

## ERROR SCENARIOS

| Scenario                                                   | Expected Behavior                                                                |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Framework import fails                                     | Fall back to legacy `engines.oracle.read_name()` / `question_sign()`             |
| AI interpretation fails (no API key)                       | Return reading without `ai_interpretation` field (graceful degradation)          |
| User ID not found in database                              | Return 404 with clear error message                                              |
| Persian text in name input but Pythagorean system selected | Sum only Latin letters (A-Z), skip non-Latin chars — log warning                 |
| Question is only whitespace                                | Validator strips and rejects as empty (422)                                      |
| Question contains only numbers/punctuation                 | Return question_number based on digit sum, no letter analysis — note in response |
| reading_orchestrator not available (Session 14 incomplete) | Fall back to legacy endpoint logic, log deprecation warning                      |
| Database write fails during store_reading                  | Rollback transaction, return 500 with "Reading generated but could not be saved" |

---

## ACCEPTANCE CRITERIA

- [ ] Name reading form renders with text input, Persian keyboard toggle, and "Use Profile Name" button
- [ ] Name reading form submits name and receives Expression, Soul Urge, Personality numbers
- [ ] Name reading with user_id enriches results with Life Path and Personal Year from profile DOB
- [ ] Question reading form accepts up to 500 characters with live character counter
- [ ] Question reading form auto-detects script (EN/FA) and shows badge
- [ ] Question hashing correctly uses Pythagorean for Latin text and Abjad for Persian text
- [ ] Question number is reduced to single digit or master number (11, 22, 33)
- [ ] AI interpretation addresses the specific question text (not generic)
- [ ] Both reading types stored in `oracle_readings` table with correct `sign_type`
- [ ] Both reading types create audit log entries
- [ ] Legacy endpoints still work as fallback if framework unavailable
- [ ] All 38 tests pass
- [ ] TypeScript compiles without errors
- [ ] i18n translations present for EN and FA

---

## HANDOFF TO SESSION 16

Session 15 delivers:

- `question_analyzer.py` with script detection + Abjad values — reusable for any text analysis
- Name and question flows in `reading_orchestrator.py` — pattern for Daily and Multi-User flows
- Enhanced Pydantic models with framework output fields — template for remaining reading types

Session 16 needs:

- Daily auto-reading system (scheduled, one per user per day)
- Multi-user compatibility reading (2-10 users, pairwise analysis)
- Both build on the reading_orchestrator pattern established in Sessions 14-15
