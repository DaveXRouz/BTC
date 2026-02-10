# SESSION 14 SPEC — Reading Flow: Time Reading

**Block:** AI & Reading Types (Sessions 13-18)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 7 (framework bridge reading functions + `UserProfile` dataclass), Session 13 (AI interpreter with Anthropic SDK)

---

## TL;DR

- Build the first complete end-to-end reading flow: **frontend form → API → framework bridge → AI interpreter → database → display**
- New unified `POST /api/oracle/readings` endpoint with `reading_type` discriminator — becomes the canonical reading creation pattern for Sessions 15-18
- New `ReadingOrchestrator` in the Oracle service coordinates framework bridge + AI interpretation + response formatting
- Frontend `TimeReadingForm.tsx` with hour/minute/second dropdown pickers + WebSocket progress updates
- Establishes the architectural pattern that all subsequent reading flows (name, question, daily, multi-user) will follow

---

## OBJECTIVES

1. **Create `ReadingOrchestrator`** in the Oracle service that coordinates: load user profile → call framework bridge → call AI interpreter → build response
2. **Create `POST /api/oracle/readings` endpoint** accepting `{ user_id, reading_type: "time", sign_value: "14:30:00", date, locale, numerology_system }` and returning the full framework reading + AI interpretation
3. **Create new Pydantic request/response models** that map to the framework output format (fc60_stamp, numerology, moon, patterns, confidence, ai_interpretation sections)
4. **Create `TimeReadingForm.tsx`** frontend component with hour/minute/second dropdowns, optional date picker, submit button, and WebSocket progress display
5. **Integrate WebSocket progress** — send real-time step updates during reading generation ("Loading profile..." → "Generating reading..." → "Interpreting..." → "Done")
6. **Store readings in database** — save framework output + AI interpretation to `oracle_readings` table with `sign_type='time'`
7. **Write 12+ tests** covering API endpoint, orchestrator logic, and frontend component

---

## PREREQUISITES

- [ ] Session 7 completed — `services/oracle/oracle_service/framework_bridge.py` has `generate_time_reading(user, hour, minute, second, target_date)` function
- [ ] Session 7 completed — `services/oracle/oracle_service/models/reading_types.py` has `UserProfile`, `ReadingResult`, `ReadingType` classes
- [ ] Session 13 completed — `services/oracle/oracle_service/engines/ai_client.py` rewritten with Anthropic SDK
- [ ] Session 13 completed — `services/oracle/oracle_service/engines/ai_interpreter.py` has `interpret_reading()` function
- [ ] Framework importable from project root
- Verification:
  ```bash
  python3 -c "from services.oracle.oracle_service.models.reading_types import UserProfile, ReadingType; print('Models OK')"
  python3 -c "from services.oracle.oracle_service.framework_bridge import generate_time_reading; print('Bridge OK')"
  test -f services/oracle/oracle_service/engines/ai_client.py && echo "AI Client OK"
  test -f services/oracle/oracle_service/engines/ai_interpreter.py && echo "AI Interpreter OK"
  ```

---

## FILES TO CREATE

- `services/oracle/oracle_service/reading_orchestrator.py` — Coordinates framework bridge → AI interpreter → response building (the central reading pipeline)
- `frontend/src/components/oracle/TimeReadingForm.tsx` — Time reading input component with hour/minute/second dropdowns
- `frontend/src/components/oracle/__tests__/TimeReadingForm.test.tsx` — Frontend tests
- `api/tests/test_time_reading.py` — API endpoint + orchestrator integration tests
- `services/oracle/tests/test_reading_orchestrator.py` — Unit tests for ReadingOrchestrator

## FILES TO MODIFY

- `api/app/models/oracle.py` — Add `TimeReadingRequest`, `FrameworkReadingResponse`, `ReadingProgressEvent` models
- `api/app/routers/oracle.py` — Add `POST /api/oracle/readings` endpoint + WebSocket progress integration
- `api/app/services/oracle_reading.py` — Add `create_framework_reading()` method using ReadingOrchestrator
- `frontend/src/types/index.ts` — Add `TimeReadingRequest`, `FrameworkReadingResponse`, `ReadingProgressEvent` types
- `frontend/src/services/api.ts` — Add `oracle.timeReading()` method
- `frontend/src/hooks/useOracleReadings.ts` — Add `useSubmitTimeReading()` hook

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: New Pydantic Models (~30 min)

**Tasks:**

1. Add new request/response models to `api/app/models/oracle.py`:

   **`TimeReadingRequest`** — unified reading request body:

   ```python
   class TimeReadingRequest(BaseModel):
       user_id: int
       reading_type: str = "time"                             # Literal["time"] for now, expanded in Session 15
       sign_value: str                                        # "HH:MM:SS" format
       date: str | None = None                                # "YYYY-MM-DD", defaults to today
       locale: str = "en"                                     # "en" or "fa"
       numerology_system: str = "auto"                        # "pythagorean"/"chaldean"/"abjad"/"auto"

       @field_validator("sign_value")
       @classmethod
       def validate_time_format(cls, v: str) -> str:
           """Validate HH:MM:SS format with valid ranges."""
           # Parse and validate 0-23 hours, 0-59 minutes, 0-59 seconds
           ...

       @field_validator("date")
       @classmethod
       def validate_date_format(cls, v: str | None) -> str | None:
           """Validate YYYY-MM-DD format if provided."""
           ...
   ```

   **`FrameworkNumerologyData`** — maps to framework `reading["numerology"]`:

   ```python
   class FrameworkNumerologyData(BaseModel):
       life_path: dict                                        # {"number": int, "title": str, "message": str}
       expression: int
       soul_urge: int
       personality: int
       personal_year: int
       personal_month: int
       personal_day: int
       gender_polarity: dict | None = None
       mother_influence: int | None = None
   ```

   **`FrameworkConfidence`** — maps to framework `reading["confidence"]`:

   ```python
   class FrameworkConfidence(BaseModel):
       score: int                                             # 50-95
       level: str                                             # "low"/"medium"/"high"/"very_high"
       factors: str = ""
   ```

   **`PatternDetected`** — maps to framework `reading["patterns"]["detected"]` items:

   ```python
   class PatternDetected(BaseModel):
       type: str                                              # "animal_repetition", "number_repetition"
       strength: str                                          # "high", "medium", "low"
       message: str = ""
       animal: str | None = None
       number: int | None = None
       occurrences: int | None = None
   ```

   **`AIInterpretationSections`** — parsed AI response (from Session 13):

   ```python
   class AIInterpretationSections(BaseModel):
       header: str = ""
       core_identity: str = ""
       right_now: str = ""
       patterns: str = ""
       message: str = ""
       advice: str = ""
       caution: str = ""
       footer: str = ""
       full_text: str = ""
   ```

   **`FrameworkReadingResponse`** — the unified reading response:

   ```python
   class FrameworkReadingResponse(BaseModel):
       id: int
       reading_type: str
       sign_value: str
       framework_result: dict                                 # Full MasterOrchestrator output
       ai_interpretation: AIInterpretationSections | None = None
       confidence: FrameworkConfidence
       patterns: list[PatternDetected] = []
       fc60_stamp: str                                        # e.g., "LU-OX-OXWA ☀TI-HOWU-RAWU"
       numerology: FrameworkNumerologyData | None = None
       moon: dict | None = None
       ganzhi: dict | None = None
       locale: str = "en"
       created_at: str
   ```

   **`ReadingProgressEvent`** — WebSocket progress message:

   ```python
   class ReadingProgressEvent(BaseModel):
       step: int
       total: int
       message: str
       reading_type: str = "time"
   ```

2. Import `field_validator` from pydantic for validation decorators.

**Checkpoint:**

- [ ] `python3 -c "from api.app.models.oracle import TimeReadingRequest, FrameworkReadingResponse; print('Models OK')"` — imports without error
- [ ] `TimeReadingRequest(user_id=1, sign_value='14:30:00')` validates successfully
- [ ] `TimeReadingRequest(user_id=1, sign_value='25:00:00')` raises ValidationError (invalid hour)
- [ ] `TimeReadingRequest(user_id=1, sign_value='abc')` raises ValidationError (invalid format)
- Verify: `cd api && python3 -c "from app.models.oracle import TimeReadingRequest; r = TimeReadingRequest(user_id=1, sign_value='14:30:00'); print(r.model_dump())"`

🚨 STOP if checkpoint fails

---

### Phase 2: Reading Orchestrator (~60 min)

**Tasks:**

1. Create `services/oracle/oracle_service/reading_orchestrator.py`:

   ```python
   """Reading Orchestrator — coordinates the full reading pipeline.

   Pipeline: load profile → framework bridge → AI interpretation → response.
   This is the central coordinator for ALL reading types.
   Session 14 implements time reading; Sessions 15-18 add others.
   """

   import logging
   import time
   from datetime import datetime
   from typing import Any, Callable, Optional

   from models.reading_types import UserProfile, ReadingType, ReadingResult

   logger = logging.getLogger(__name__)


   class ReadingOrchestrator:
       """Orchestrates the reading pipeline for all reading types.

       Provides:
       - Framework bridge invocation for each reading type
       - AI interpretation via Session 13 engine
       - Response formatting to API model structure
       - Progress callback for WebSocket updates
       """

       def __init__(
           self,
           progress_callback: Optional[Callable] = None,
       ):
           self.progress_callback = progress_callback

       async def _send_progress(self, step: int, total: int, message: str) -> None:
           """Send progress update via callback if registered."""
           if self.progress_callback:
               await self.progress_callback(step, total, message)

       async def generate_time_reading(
           self,
           user_profile: UserProfile,
           hour: int,
           minute: int,
           second: int,
           target_date: Optional[datetime] = None,
           locale: str = "en",
       ) -> dict:
           """Full pipeline for time reading.

           Returns dict matching FrameworkReadingResponse fields.
           """
           total_steps = 4
           start = time.perf_counter()

           # Step 1: Generate framework reading
           await self._send_progress(1, total_steps, "Generating reading...")
           reading_result = self._call_framework_time(
               user_profile, hour, minute, second, target_date
           )

           # Step 2: AI interpretation
           await self._send_progress(2, total_steps, "Interpreting patterns...")
           ai_sections = self._call_ai_interpreter(
               reading_result.framework_output, locale
           )

           # Step 3: Format response
           await self._send_progress(3, total_steps, "Formatting response...")
           response = self._build_response(reading_result, ai_sections, locale)

           # Step 4: Done
           elapsed = (time.perf_counter() - start) * 1000
           await self._send_progress(4, total_steps, "Done")
           logger.info("Time reading generated", extra={"elapsed_ms": elapsed})

           return response

       def _call_framework_time(self, user, hour, minute, second, target_date):
           """Invoke framework_bridge.generate_time_reading()."""
           from framework_bridge import generate_time_reading
           return generate_time_reading(user, hour, minute, second, target_date)

       def _call_ai_interpreter(self, framework_output: dict, locale: str) -> dict:
           """Invoke AI interpreter from Session 13."""
           try:
               from engines.ai_interpreter import interpret_reading
               result = interpret_reading(framework_output, locale=locale)
               return result.to_dict() if hasattr(result, 'to_dict') else result
           except Exception:
               logger.warning("AI interpretation unavailable", exc_info=True)
               # Fallback: use framework synthesis
               synthesis = framework_output.get("synthesis", "")
               return {"full_text": synthesis, "header": "", ...}

       def _build_response(self, reading_result, ai_sections, locale) -> dict:
           """Build response dict matching FrameworkReadingResponse."""
           fw = reading_result.framework_output
           return {
               "reading_type": "time",
               "sign_value": reading_result.sign_value,
               "framework_result": fw,
               "ai_interpretation": ai_sections,
               "confidence": fw.get("confidence", {}),
               "patterns": fw.get("patterns", {}).get("detected", []),
               "fc60_stamp": fw.get("fc60_stamp", {}).get("fc60", ""),
               "numerology": fw.get("numerology"),
               "moon": fw.get("moon"),
               "ganzhi": fw.get("ganzhi"),
               "locale": locale,
           }
   ```

2. Key design decisions:
   - `ReadingOrchestrator` is stateless except for the progress callback
   - `_call_framework_time()` and `_call_ai_interpreter()` are separate methods for testability (mock individually)
   - AI failure never crashes the reading — falls back to framework synthesis text
   - Progress callback is async to support WebSocket `send_json()`
   - This class is extended in Sessions 15-18 with `generate_name_reading()`, `generate_question_reading()`, etc.

**Checkpoint:**

- [ ] `ReadingOrchestrator` instantiates without errors
- [ ] `generate_time_reading()` returns dict with all required keys: `reading_type`, `sign_value`, `framework_result`, `ai_interpretation`, `confidence`, `patterns`, `fc60_stamp`, `numerology`, `moon`, `ganzhi`, `locale`
- [ ] AI failure does not crash — fallback to synthesis text works
- [ ] Progress callback called 4 times with incrementing step numbers
- Verify: `cd services/oracle && python3 -c "from oracle_service.reading_orchestrator import ReadingOrchestrator; print('Orchestrator OK')"`

🚨 STOP if checkpoint fails

---

### Phase 3: API Endpoint (~60 min)

**Tasks:**

1. Modify `api/app/services/oracle_reading.py`:

   Add `UserProfile` building helper and `create_framework_reading()` method:

   ```python
   def _build_user_profile(self, oracle_user: OracleUser) -> "UserProfile":
       """Convert OracleUser ORM to UserProfile dataclass for framework bridge."""
       from oracle_service.models.reading_types import UserProfile

       # Parse birthday string "YYYY-MM-DD" to components
       bday = oracle_user.birthday  # date object or string
       if isinstance(bday, str):
           parts = bday.split("-")
           birth_year, birth_month, birth_day = int(parts[0]), int(parts[1]), int(parts[2])
       else:
           birth_year, birth_month, birth_day = bday.year, bday.month, bday.day

       # Decrypt mother_name if encrypted
       mother_name = oracle_user.mother_name
       if self.enc and mother_name:
           mother_name = self.enc.decrypt_field(mother_name)

       return UserProfile(
           user_id=oracle_user.id,
           full_name=oracle_user.name,
           birth_day=birth_day,
           birth_month=birth_month,
           birth_year=birth_year,
           mother_name=mother_name,
           # Fields added by Session 1 migration:
           gender=getattr(oracle_user, 'gender', None),
           heart_rate_bpm=getattr(oracle_user, 'heart_rate_bpm', None),
           timezone_hours=getattr(oracle_user, 'timezone_hours', 0) or 0,
           timezone_minutes=getattr(oracle_user, 'timezone_minutes', 0) or 0,
           # numerology_system from oracle_settings (Session 8)
           numerology_system=numerology_system or "pythagorean",
       )

   async def create_framework_reading(
       self,
       user_id: int,
       reading_type: str,
       sign_value: str,
       date_str: str | None,
       locale: str,
       numerology_system: str,
       progress_callback=None,
   ) -> dict:
       """Create a reading using the framework pipeline.

       Returns dict ready for FrameworkReadingResponse + the OracleReading DB row.
       """
       # 1. Load oracle_user
       oracle_user = self.db.query(OracleUser).filter(
           OracleUser.id == user_id,
           OracleUser.deleted_at.is_(None),
       ).first()
       if not oracle_user:
           raise ValueError(f"Oracle user {user_id} not found")

       # 2. Build UserProfile
       user_profile = self._build_user_profile(oracle_user)
       if numerology_system != "auto":
           user_profile.numerology_system = numerology_system

       # 3. Parse sign_value for time reading
       hour, minute, second = [int(x) for x in sign_value.split(":")]
       target_date = _parse_datetime(date_str) if date_str else None

       # 4. Orchestrate reading
       from oracle_service.reading_orchestrator import ReadingOrchestrator
       orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
       result = await orchestrator.generate_time_reading(
           user_profile, hour, minute, second, target_date, locale
       )

       # 5. Store in database
       reading = self.store_reading(
           user_id=user_id,
           sign_type="time",
           sign_value=sign_value,
           question=None,
           reading_result=result.get("framework_result"),
           ai_interpretation=result.get("ai_interpretation", {}).get("full_text"),
       )

       result["id"] = reading.id
       result["created_at"] = reading.created_at.isoformat() if hasattr(reading.created_at, 'isoformat') else str(reading.created_at)

       return result
   ```

2. Modify `api/app/routers/oracle.py` — add the new unified endpoint:

   ```python
   @router.post(
       "/readings",
       response_model=FrameworkReadingResponse,
       dependencies=[Depends(require_scope("oracle:write"))],
   )
   async def create_framework_reading(
       body: TimeReadingRequest,
       request: Request,
       _user: dict = Depends(get_current_user),
       svc: OracleReadingService = Depends(get_oracle_reading_service),
       audit: AuditService = Depends(get_audit_service),
   ):
       """Create a reading using the numerology framework + AI interpretation.

       This is the new unified reading endpoint. Session 14 supports reading_type='time'.
       Sessions 15-18 add 'name', 'question', 'daily', 'multi_user'.
       """
       # Build progress callback bound to the oracle WS manager
       async def progress_callback(step: int, total: int, message: str):
           await oracle_progress.send_progress(step, total, message)

       try:
           result = await svc.create_framework_reading(
               user_id=body.user_id,
               reading_type=body.reading_type,
               sign_value=body.sign_value,
               date_str=body.date,
               locale=body.locale,
               numerology_system=body.numerology_system,
               progress_callback=progress_callback,
           )
       except ValueError as exc:
           raise HTTPException(
               status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
           )

       audit.log_reading_created(
           result["id"],
           "time",
           ip=_get_client_ip(request),
           key_hash=_user.get("api_key_hash"),
       )
       svc.db.commit()
       return FrameworkReadingResponse(**result)
   ```

3. Add imports for new models at top of `oracle.py`:

   ```python
   from app.models.oracle import (
       ...,
       TimeReadingRequest,
       FrameworkReadingResponse,
   )
   ```

4. Note: The existing legacy endpoints (`/reading`, `/question`, `/name`) remain untouched — they still work but the new `/readings` endpoint is the preferred path going forward.

**Checkpoint:**

- [ ] `POST /api/oracle/readings` with valid body returns 200 with `FrameworkReadingResponse`
- [ ] Invalid `sign_value` ("25:00:00") returns 422
- [ ] Non-existent `user_id` returns 422 with "user not found"
- [ ] WebSocket at `/api/oracle/ws` receives 4 progress events during reading
- [ ] Reading stored in `oracle_readings` table with `sign_type='time'`
- Verify: `cd api && python3 -m pytest tests/test_time_reading.py -v -k "test_create_time_reading"`

🚨 STOP if checkpoint fails

---

### Phase 4: WebSocket Progress Integration (~30 min)

**Tasks:**

1. The `OracleProgressManager` in `api/app/services/oracle_reading.py` already exists (lines 555-578). It supports `send_progress(step, total, message)`.

2. The WebSocket endpoint at `/api/oracle/ws` already exists in `api/app/routers/oracle.py` (lines 356-364).

3. Enhance progress messages for the time reading flow. The `progress_callback` from Phase 3 maps to these steps:

   | Step | Total | Message                    |
   | ---- | ----- | -------------------------- |
   | 1    | 4     | "Generating reading..."    |
   | 2    | 4     | "Interpreting patterns..." |
   | 3    | 4     | "Formatting response..."   |
   | 4    | 4     | "Done"                     |

4. Add `reading_type` field to progress JSON payload. Modify `OracleProgressManager.send_progress()`:

   ```python
   async def send_progress(self, step: int, total: int, message: str, reading_type: str = "time"):
       payload = {"step": step, "total": total, "message": message, "reading_type": reading_type}
       ...
   ```

5. Frontend will connect to this WebSocket and display a progress bar or step indicator.

**Checkpoint:**

- [ ] WebSocket at `/api/oracle/ws` accepts connections
- [ ] Progress events sent as JSON with `step`, `total`, `message`, `reading_type` keys
- [ ] Multiple concurrent WebSocket clients all receive progress events
- Verify: Manual test — connect `wscat -c ws://localhost:8000/api/oracle/ws` and trigger a reading

🚨 STOP if checkpoint fails

---

### Phase 5: Frontend — TimeReadingForm Component (~60 min)

**Tasks:**

1. Create `frontend/src/components/oracle/TimeReadingForm.tsx`:

   ```tsx
   interface TimeReadingFormProps {
     userId: number;
     userName: string;
     onResult: (result: FrameworkReadingResponse) => void;
     onProgress?: (event: ReadingProgressEvent) => void;
   }
   ```

   Component structure:
   - **Hour dropdown**: `<select>` with options 0-23, displaying "00" through "23"
   - **Minute dropdown**: `<select>` with options 0-59, displaying "00" through "59"
   - **Second dropdown**: `<select>` with options 0-59, displaying "00" through "59"
   - **"Use current time" button**: Fills dropdowns with `new Date()` values
   - **Date picker**: Optional, uses existing `CalendarPicker` component. Defaults to today.
   - **Locale toggle**: "EN" / "FA" switch (uses i18n)
   - **Submit button**: Disabled while submitting, shows "Generating..." text
   - **Progress indicator**: Shows current step message from WebSocket updates

2. Key design decisions:
   - Dropdowns (not free text) prevent invalid input — no need for complex validation
   - "Use current time" is the primary CTA — most users want a reading for "right now"
   - Default values: current hour, current minute, 0 seconds, today's date
   - RTL layout when locale is FA — dropdowns flow right-to-left
   - Uses existing Tailwind classes matching the project's `nps-*` theme tokens

3. WebSocket integration for progress:

   ```tsx
   // Connect to WebSocket for progress updates
   const ws = useRef<WebSocket | null>(null);

   useEffect(() => {
     ws.current = new WebSocket(`${wsUrl}/api/oracle/ws`);
     ws.current.onmessage = (event) => {
       const data = JSON.parse(event.data);
       if (data.reading_type === "time") {
         setProgress(data);
         onProgress?.(data);
       }
     };
     return () => ws.current?.close();
   }, []);
   ```

4. i18n keys to add (use existing `frontend/src/i18n/config.ts` pattern):
   - `oracle.time_reading_title` — "Time Reading"
   - `oracle.hour_label` — "Hour"
   - `oracle.minute_label` — "Minute"
   - `oracle.second_label` — "Second"
   - `oracle.use_current_time` — "Use current time"
   - `oracle.generating_reading` — "Generating reading..."
   - Persian equivalents for all keys

**Checkpoint:**

- [ ] `TimeReadingForm` renders without errors
- [ ] Hour dropdown has 24 options (0-23)
- [ ] Minute and second dropdowns have 60 options each (0-59)
- [ ] "Use current time" button fills all three dropdowns
- [ ] Submit triggers API call with correct `sign_value` format ("HH:MM:SS")
- [ ] Progress indicator updates during reading generation
- [ ] Form disabled while submitting
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/TimeReadingForm.test.tsx`

🚨 STOP if checkpoint fails

---

### Phase 6: Frontend API Client, Types & Hooks (~30 min)

**Tasks:**

1. Add TypeScript types to `frontend/src/types/index.ts`:

   ```typescript
   // ─── Framework Reading (Session 14+) ───

   export interface TimeReadingRequest {
     user_id: number;
     reading_type: "time";
     sign_value: string; // "HH:MM:SS"
     date?: string; // "YYYY-MM-DD"
     locale?: string; // "en" | "fa"
     numerology_system?: string; // "pythagorean" | "chaldean" | "abjad" | "auto"
   }

   export interface FrameworkConfidence {
     score: number;
     level: string;
     factors?: string;
   }

   export interface PatternDetected {
     type: string;
     strength: string;
     message?: string;
     animal?: string;
     number?: number;
     occurrences?: number;
   }

   export interface AIInterpretationSections {
     header: string;
     core_identity: string;
     right_now: string;
     patterns: string;
     message: string;
     advice: string;
     caution: string;
     footer: string;
     full_text: string;
   }

   export interface FrameworkNumerologyData {
     life_path: { number: number; title: string; message: string };
     expression: number;
     soul_urge: number;
     personality: number;
     personal_year: number;
     personal_month: number;
     personal_day: number;
     gender_polarity?: {
       gender: string;
       polarity: number;
       label: string;
     } | null;
     mother_influence?: number | null;
   }

   export interface FrameworkReadingResponse {
     id: number;
     reading_type: string;
     sign_value: string;
     framework_result: Record<string, unknown>;
     ai_interpretation: AIInterpretationSections | null;
     confidence: FrameworkConfidence;
     patterns: PatternDetected[];
     fc60_stamp: string;
     numerology: FrameworkNumerologyData | null;
     moon: Record<string, unknown> | null;
     ganzhi: Record<string, unknown> | null;
     locale: string;
     created_at: string;
   }

   export interface ReadingProgressEvent {
     step: number;
     total: number;
     message: string;
     reading_type: string;
   }
   ```

2. Add API method to `frontend/src/services/api.ts`:

   ```typescript
   // Inside oracle object:
   timeReading: (data: import("@/types").TimeReadingRequest) =>
     request<import("@/types").FrameworkReadingResponse>("/oracle/readings", {
       method: "POST",
       body: JSON.stringify(data),
     }),
   ```

3. Add hook to `frontend/src/hooks/useOracleReadings.ts`:

   ```typescript
   export function useSubmitTimeReading() {
     const qc = useQueryClient();
     return useMutation({
       mutationFn: (data: import("@/types").TimeReadingRequest) =>
         oracle.timeReading(data),
       onSuccess: () => qc.invalidateQueries({ queryKey: HISTORY_KEY }),
     });
   }
   ```

**Checkpoint:**

- [ ] TypeScript compiles without errors: `cd frontend && npx tsc --noEmit`
- [ ] `oracle.timeReading()` calls correct endpoint
- [ ] `useSubmitTimeReading()` hook returns mutation with `mutate`, `isPending`, `data`, `error`
- Verify: `cd frontend && npx tsc --noEmit && echo "Types OK"`

🚨 STOP if checkpoint fails

---

### Phase 7: Tests (~60 min)

**Tasks:**

1. Create `services/oracle/tests/test_reading_orchestrator.py`:

   ```
   test_orchestrator_creates_instance          — ReadingOrchestrator() instantiates without error
   test_time_reading_returns_required_keys      — generate_time_reading() returns dict with all FrameworkReadingResponse fields
   test_time_reading_correct_sign_value         — sign_value matches "HH:MM:SS" format from input
   test_time_reading_framework_output_present   — framework_result dict is non-empty, has fc60_stamp
   test_ai_fallback_on_error                    — AI failure returns synthesis text as fallback
   test_progress_callback_called                — progress_callback called 4 times with incrementing steps
   test_progress_callback_optional              — Works fine with progress_callback=None
   ```

2. Create `api/tests/test_time_reading.py`:

   ```
   test_create_time_reading_success             — POST /oracle/readings returns 200 with valid body
   test_create_time_reading_invalid_time        — sign_value "25:00:00" returns 422
   test_create_time_reading_invalid_format      — sign_value "abc" returns 422
   test_create_time_reading_user_not_found      — non-existent user_id returns 422
   test_create_time_reading_stored_in_db        — Reading exists in oracle_readings after creation
   test_create_time_reading_with_date           — Custom date passed correctly
   test_create_time_reading_locale_fa           — locale="fa" passed to orchestrator
   test_reading_response_has_fc60_stamp         — Response includes non-empty fc60_stamp
   test_reading_response_has_confidence         — confidence.score between 50-95
   ```

3. Create `frontend/src/components/oracle/__tests__/TimeReadingForm.test.tsx`:

   ```
   test_renders_time_dropdowns                  — 3 select elements present (hour, minute, second)
   test_hour_dropdown_has_24_options            — Hour select has 24 option elements
   test_use_current_time_button                 — Clicking fills dropdowns with current time
   test_submit_calls_api                        — Form submission calls oracle.timeReading()
   test_submit_disabled_while_loading           — Submit button disabled during isPending
   test_displays_progress_message               — Progress message shown during generation
   ```

4. All tests use mocks:
   - Oracle service tests: mock `framework_bridge` and `ai_interpreter` imports
   - API tests: mock `OracleReadingService` dependency
   - Frontend tests: mock `oracle.timeReading()` API call

**Checkpoint:**

- [ ] All orchestrator tests pass: `cd services/oracle && python3 -m pytest tests/test_reading_orchestrator.py -v`
- [ ] All API tests pass: `cd api && python3 -m pytest tests/test_time_reading.py -v`
- [ ] All frontend tests pass: `cd frontend && npx vitest run src/components/oracle/__tests__/TimeReadingForm.test.tsx`
- Verify: `cd api && python3 -m pytest tests/test_time_reading.py -v && echo "All API tests pass"`

🚨 STOP if checkpoint fails

---

### Phase 8: Final Verification (~30 min)

**Tasks:**

1. Run full test suites:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_reading_orchestrator.py -v
   cd api && python3 -m pytest tests/test_time_reading.py -v
   cd frontend && npx vitest run src/components/oracle/__tests__/TimeReadingForm.test.tsx
   cd frontend && npx tsc --noEmit
   ```

2. Verify endpoint with curl:

   ```bash
   curl -s -X POST http://localhost:8000/api/oracle/readings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "user_id": 1,
       "reading_type": "time",
       "sign_value": "14:30:00",
       "locale": "en",
       "numerology_system": "auto"
     }' | python3 -m json.tool
   ```

3. Verify response structure has all required fields:
   - `id` (integer, from database)
   - `reading_type` = "time"
   - `sign_value` = "14:30:00"
   - `framework_result` (non-empty dict with `fc60_stamp`, `numerology`, `moon`, etc.)
   - `ai_interpretation` (sections object or null)
   - `confidence` (score 50-95, level string)
   - `patterns` (array)
   - `fc60_stamp` (non-empty string)
   - `created_at` (ISO 8601 timestamp)

4. Verify WebSocket:

   ```bash
   # In terminal 1: connect WebSocket
   wscat -c ws://localhost:8000/api/oracle/ws

   # In terminal 2: trigger reading
   curl -s -X POST http://localhost:8000/api/oracle/readings \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"user_id": 1, "reading_type": "time", "sign_value": "14:30:00"}'

   # Terminal 1 should show 4 progress messages
   ```

5. Verify database storage:

   ```bash
   docker-compose exec postgres psql -U nps -d nps -c \
     "SELECT id, sign_type, sign_value, created_at FROM oracle_readings ORDER BY id DESC LIMIT 5;"
   ```

6. Lint and format:
   ```bash
   cd api && python3 -m ruff check app/ tests/ --fix
   cd api && python3 -m black app/ tests/
   cd frontend && npx eslint src/ --fix
   cd frontend && npx prettier --write src/
   ```

**Checkpoint:**

- [ ] All Python tests pass (0 failures)
- [ ] All frontend tests pass (0 failures)
- [ ] TypeScript compiles without errors
- [ ] Curl returns valid `FrameworkReadingResponse` JSON
- [ ] WebSocket receives 4 progress events during reading
- [ ] Reading row exists in database with `sign_type='time'`
- [ ] Linter reports 0 errors

🚨 STOP if any check fails — fix before marking session complete

---

## TESTS TO WRITE

### Oracle Service Tests (`services/oracle/tests/test_reading_orchestrator.py`)

- `test_reading_orchestrator.py::test_orchestrator_creates_instance` — Instantiation works
- `test_reading_orchestrator.py::test_time_reading_returns_required_keys` — All response keys present
- `test_reading_orchestrator.py::test_time_reading_correct_sign_value` — sign_value = "14:30:00"
- `test_reading_orchestrator.py::test_time_reading_framework_output_present` — framework_result is non-empty
- `test_reading_orchestrator.py::test_ai_fallback_on_error` — AI crash returns synthesis fallback
- `test_reading_orchestrator.py::test_progress_callback_called` — 4 progress events fired
- `test_reading_orchestrator.py::test_progress_callback_optional` — No crash when callback is None

### API Tests (`api/tests/test_time_reading.py`)

- `test_time_reading.py::test_create_time_reading_success` — 200 response with valid body
- `test_time_reading.py::test_create_time_reading_invalid_time` — 422 for "25:00:00"
- `test_time_reading.py::test_create_time_reading_invalid_format` — 422 for "abc"
- `test_time_reading.py::test_create_time_reading_user_not_found` — 422 for nonexistent user
- `test_time_reading.py::test_create_time_reading_stored_in_db` — Row in oracle_readings
- `test_time_reading.py::test_create_time_reading_with_date` — Custom date works
- `test_time_reading.py::test_create_time_reading_locale_fa` — Persian locale passed through
- `test_time_reading.py::test_reading_response_has_fc60_stamp` — fc60_stamp field present
- `test_time_reading.py::test_reading_response_has_confidence` — score between 50-95

### Frontend Tests (`frontend/src/components/oracle/__tests__/TimeReadingForm.test.tsx`)

- `TimeReadingForm.test.tsx::renders time dropdowns` — 3 select elements exist
- `TimeReadingForm.test.tsx::hour dropdown has 24 options` — 24 option elements
- `TimeReadingForm.test.tsx::use current time button fills dropdowns` — Button sets values
- `TimeReadingForm.test.tsx::submit calls API with correct format` — "HH:MM:SS" sent
- `TimeReadingForm.test.tsx::submit disabled while loading` — Button disabled during mutation
- `TimeReadingForm.test.tsx::displays progress message` — WebSocket message shown

---

## ACCEPTANCE CRITERIA

- [ ] `POST /api/oracle/readings` returns full `FrameworkReadingResponse` for time reading
- [ ] Response includes framework calculation data (fc60_stamp, numerology, moon, patterns)
- [ ] Response includes AI interpretation sections (or null if API key missing)
- [ ] Confidence score is between 50-95
- [ ] Reading stored in `oracle_readings` with `sign_type='time'`
- [ ] WebSocket sends 4 progress events during reading generation
- [ ] `TimeReadingForm.tsx` renders with hour/minute/second dropdowns
- [ ] Form submits and displays results (or progress indicator)
- [ ] Both EN and FA locales work (locale passed to AI interpreter)
- [ ] Invalid inputs rejected with 422 (bad time format, non-existent user)
- [ ] All 22 tests pass
- [ ] TypeScript compiles without errors
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_reading_orchestrator.py -v && \
  cd ../.. && cd api && python3 -m pytest tests/test_time_reading.py -v && \
  cd ../frontend && npx vitest run src/components/oracle/__tests__/TimeReadingForm.test.tsx && \
  npx tsc --noEmit && echo "ALL ACCEPTANCE CRITERIA PASS"
  ```

---

## ERROR SCENARIOS

### Problem: Framework bridge import fails

**Cause:** PYTHONPATH not configured or Session 6/7 incomplete
**Fix:** Verify `services/oracle/oracle_service/framework_bridge.py` exists. Check `sys.path` includes `services/oracle` and `numerology_ai_framework` directories. Run: `python3 -c "from oracle_service.framework_bridge import generate_time_reading; print('OK')"`

### Problem: AI interpreter returns empty response

**Cause:** ANTHROPIC_API_KEY not set or Anthropic API unreachable
**Fix:** `ReadingOrchestrator._call_ai_interpreter()` has fallback — it returns `framework_output["synthesis"]` text. Check env: `echo $ANTHROPIC_API_KEY`. The reading should still succeed with framework synthesis as the interpretation text.

### Problem: Oracle user not found (422)

**Cause:** `user_id` doesn't exist in `oracle_users` table or user is soft-deleted
**Fix:** Create a test oracle user first: `POST /api/oracle/users` with valid profile data. Check `deleted_at IS NULL`.

### Problem: WebSocket progress events not received

**Cause:** WebSocket connection not established before reading triggered, or CORS blocking
**Fix:** Ensure frontend connects to WS before triggering the reading. Check nginx WebSocket proxy config (upgrade headers). Test with `wscat -c ws://localhost:8000/api/oracle/ws` first.

### Problem: Frontend TypeScript compile error on new types

**Cause:** Type mismatch between API response and TypeScript interface
**Fix:** Ensure `FrameworkReadingResponse` TypeScript interface exactly matches the Pydantic model field names and types. Run `npx tsc --noEmit` and fix any type errors.

---

## HANDOFF

**Created:**

- `services/oracle/oracle_service/reading_orchestrator.py` — Central reading pipeline coordinator
- `frontend/src/components/oracle/TimeReadingForm.tsx` — Time reading input form
- `frontend/src/components/oracle/__tests__/TimeReadingForm.test.tsx` — Frontend tests
- `api/tests/test_time_reading.py` — API endpoint tests
- `services/oracle/tests/test_reading_orchestrator.py` — Orchestrator unit tests

**Modified:**

- `api/app/models/oracle.py` — Added 7 new Pydantic models for framework readings
- `api/app/routers/oracle.py` — Added `POST /api/oracle/readings` endpoint
- `api/app/services/oracle_reading.py` — Added `create_framework_reading()` + `_build_user_profile()`
- `frontend/src/types/index.ts` — Added 7 new TypeScript interfaces
- `frontend/src/services/api.ts` — Added `oracle.timeReading()` method
- `frontend/src/hooks/useOracleReadings.ts` — Added `useSubmitTimeReading()` hook

**Deleted:**

- None

**Next session needs:**

- Session 15 extends `ReadingOrchestrator` with `generate_name_reading()` and `generate_question_reading()` — the orchestrator's pattern is established here
- Session 15 adds `reading_type: "name"` and `reading_type: "question"` to the same `POST /api/oracle/readings` endpoint using a request discriminator
- Session 15 creates `NameReadingForm.tsx` and `QuestionReadingForm.tsx` following the `TimeReadingForm.tsx` pattern
- The `_build_user_profile()` helper is reused by all subsequent reading sessions
- The `FrameworkReadingResponse` model is shared across all reading types
- WebSocket progress pattern (4-step pipeline) is reused
