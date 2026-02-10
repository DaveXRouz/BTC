# SESSION 12 SPEC — Framework Integration: Heartbeat & Location Engines

**Block:** Calculation Engines (Sessions 6-12) — FINAL session in block
**Estimated Duration:** 6-7 hours
**Complexity:** Medium-High (cross-layer: DB + API + Oracle service + Frontend)
**Dependencies:** Session 6 (framework bridge), Session 5 (LocationSelector), Session 9 (ConfidenceMapper)

---

## TL;DR

- Add `gender`, `heart_rate_bpm`, and `timezone_hours` columns to `oracle_users` table (migration + ORM + Pydantic + TypeScript types)
- Create `HeartbeatInput.tsx` with both manual BPM entry and tap-to-count mode for real-time heart rate measurement
- Create `HeartbeatDisplay.tsx`, `LocationDisplay.tsx`, and `ConfidenceMeter.tsx` frontend components that render framework engine output
- Ensure `framework_bridge.py` passes heartbeat and location data through to `MasterOrchestrator.generate_reading()`
- Add bilingual (EN/FA) i18n keys for all heartbeat, location, and confidence terms
- Write 15+ tests across backend and frontend covering BPM validation, element mapping, tap-to-count logic, confidence meter display, and graceful handling of missing optional data

---

## OBJECTIVES

1. **Extend the user data model** — add `gender` (VARCHAR), `heart_rate_bpm` (INTEGER), and `timezone_hours` (SMALLINT) as optional columns to `oracle_users`, with corresponding ORM, Pydantic, and TypeScript type updates
2. **Create `HeartbeatInput` component** — accepts manual BPM entry (validated range 30-220) or tap-to-count mode that measures inter-tap intervals to estimate BPM
3. **Create `HeartbeatDisplay` component** — renders BPM, element (from `HeartbeatEngine`), lifetime beats counter, rhythm description, and BPM source indicator (actual vs estimated)
4. **Create `LocationDisplay` component** — renders location element mapping, hemisphere polarity, timezone estimate, and zone description using data from `LocationEngine`
5. **Create `ConfidenceMeter` component** — renders a visual progress bar showing reading confidence (0-100%), level indicator, and a "completeness" breakdown showing which optional fields are filled and their individual confidence boost values
6. **Wire bridge data flow** — ensure `framework_bridge.py` passes `actual_bpm`, `latitude`, `longitude`, and `gender` to `MasterOrchestrator.generate_reading()` when present in user profile
7. **Add i18n translations** — all new UI text in both English and Persian for heartbeat, location, and confidence terms

---

## PREREQUISITES

- [ ] Session 6 completed — `services/oracle/oracle_service/framework_bridge.py` exists
- [ ] Framework is importable with heartbeat and location engines
- [ ] `frontend/src/components/oracle/LocationSelector.tsx` exists (from scaffolding)
- [ ] `frontend/src/locales/en.json` and `frontend/src/locales/fa.json` exist
- Verification:
  ```bash
  test -f services/oracle/oracle_service/framework_bridge.py && echo "Bridge OK"
  python3 -c "from numerology_ai_framework.personal.heartbeat_engine import HeartbeatEngine; print('HeartbeatEngine OK')"
  python3 -c "from numerology_ai_framework.universal.location_engine import LocationEngine; print('LocationEngine OK')"
  test -f frontend/src/components/oracle/LocationSelector.tsx && echo "LocationSelector OK"
  test -f frontend/src/locales/en.json && echo "i18n OK"
  ```

**Note on Session 9 dependency:** Session 9 creates `ConfidenceMapper` in `pattern_formatter.py` with UI color/icon/label mappings. If Session 9 is not yet complete, `ConfidenceMeter.tsx` should use inline confidence level colors as a fallback and be easily updated later when the API response includes `confidence_ui` data from Session 9.

---

## FILES TO CREATE

| Path                                                                | Purpose                                                                              |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `database/migrations/012_heartbeat_location_columns.sql`            | **NEW** — Add `gender`, `heart_rate_bpm`, `timezone_hours` columns to `oracle_users` |
| `database/migrations/012_heartbeat_location_columns_rollback.sql`   | **NEW** — Rollback migration                                                         |
| `frontend/src/components/oracle/HeartbeatInput.tsx`                 | **NEW** — BPM manual entry + tap-to-count mode                                       |
| `frontend/src/components/oracle/HeartbeatDisplay.tsx`               | **NEW** — Render heartbeat engine output (BPM, element, lifetime beats)              |
| `frontend/src/components/oracle/LocationDisplay.tsx`                | **NEW** — Render location engine output (element, hemisphere, timezone)              |
| `frontend/src/components/oracle/ConfidenceMeter.tsx`                | **NEW** — Visual confidence bar + completeness breakdown                             |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | **NEW** — Tests for BPM input and tap-to-count                                       |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | **NEW** — Tests for confidence display                                               |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | **NEW** — Tests for heartbeat/location data flowing through bridge                   |

## FILES TO MODIFY

| Path                                                        | Change                                                                                                               |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `database/schemas/oracle_users.sql`                         | Add `gender`, `heart_rate_bpm`, `timezone_hours` column definitions (for reference; migration is the execution path) |
| `api/app/orm/oracle_user.py`                                | Add `gender`, `heart_rate_bpm`, `timezone_hours` mapped columns                                                      |
| `api/app/models/oracle_user.py`                             | Add optional fields to `OracleUserCreate`, `OracleUserResponse`, `OracleUserUpdate` Pydantic models                  |
| `frontend/src/types/index.ts`                               | Add `gender`, `heart_rate_bpm`, `timezone_hours` to `OracleUser` and `OracleUserCreate` interfaces                   |
| `frontend/src/components/oracle/UserForm.tsx`               | Add gender selector (Male/Female/Prefer not to say) and BPM input field                                              |
| `frontend/src/components/oracle/OracleConsultationForm.tsx` | Integrate `HeartbeatInput` as optional expandable section                                                            |
| `frontend/src/components/oracle/ReadingResults.tsx`         | Add `HeartbeatDisplay`, `LocationDisplay`, `ConfidenceMeter` to results view                                         |
| `frontend/src/locales/en.json`                              | Add heartbeat, location, confidence, and gender i18n keys                                                            |
| `frontend/src/locales/fa.json`                              | Add Persian translations for all new keys                                                                            |
| `services/oracle/oracle_service/framework_bridge.py`        | Ensure `actual_bpm`, `latitude`, `longitude`, `gender` are passed to `MasterOrchestrator.generate_reading()`         |

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: Database Migration (~30 min)

**Tasks:**

1. Create migration `database/migrations/012_heartbeat_location_columns.sql`:

   ```sql
   -- Add optional heartbeat, gender, and timezone columns to oracle_users
   -- These fields boost reading confidence when provided

   ALTER TABLE oracle_users
       ADD COLUMN IF NOT EXISTS gender VARCHAR(20),
       ADD COLUMN IF NOT EXISTS heart_rate_bpm SMALLINT,
       ADD COLUMN IF NOT EXISTS timezone_hours SMALLINT DEFAULT 0;

   -- Constraints
   ALTER TABLE oracle_users
       ADD CONSTRAINT oracle_users_gender_check
           CHECK (gender IS NULL OR gender IN ('male', 'female')),
       ADD CONSTRAINT oracle_users_bpm_check
           CHECK (heart_rate_bpm IS NULL OR (heart_rate_bpm >= 30 AND heart_rate_bpm <= 220)),
       ADD CONSTRAINT oracle_users_timezone_check
           CHECK (timezone_hours >= -12 AND timezone_hours <= 14);

   COMMENT ON COLUMN oracle_users.gender IS 'Optional gender for polarity data (male/female/NULL)';
   COMMENT ON COLUMN oracle_users.heart_rate_bpm IS 'Optional resting heart rate in BPM (30-220)';
   COMMENT ON COLUMN oracle_users.timezone_hours IS 'UTC offset hours (-12 to +14), default 0';
   ```

2. Create rollback `database/migrations/012_heartbeat_location_columns_rollback.sql`:

   ```sql
   ALTER TABLE oracle_users
       DROP CONSTRAINT IF EXISTS oracle_users_gender_check,
       DROP CONSTRAINT IF EXISTS oracle_users_bpm_check,
       DROP CONSTRAINT IF EXISTS oracle_users_timezone_check;

   ALTER TABLE oracle_users
       DROP COLUMN IF EXISTS gender,
       DROP COLUMN IF EXISTS heart_rate_bpm,
       DROP COLUMN IF EXISTS timezone_hours;
   ```

3. Update `database/schemas/oracle_users.sql` reference schema to include the new columns (as documentation — the migration is the execution path).

**Checkpoint:**

- [ ] Migration SQL is syntactically valid
- [ ] Rollback reverses all changes
- [ ] Constraints enforce valid ranges (BPM 30-220, timezone -12 to +14, gender male/female/NULL)
- Verify:
  ```bash
  test -f database/migrations/012_heartbeat_location_columns.sql && echo "Migration OK"
  test -f database/migrations/012_heartbeat_location_columns_rollback.sql && echo "Rollback OK"
  ```

🚨 STOP if migration SQL has syntax errors

---

### Phase 2: Backend Model Updates (~45 min)

**Tasks:**

1. Update `api/app/orm/oracle_user.py` — add three new mapped columns:

   ```python
   gender: Mapped[str | None] = mapped_column(String(20))
   heart_rate_bpm: Mapped[int | None] = mapped_column()
   timezone_hours: Mapped[int] = mapped_column(default=0, server_default="0")
   ```

2. Update `api/app/models/oracle_user.py` — add optional fields to Pydantic models:

   ```python
   # In OracleUserCreate:
   gender: str | None = None          # 'male' / 'female' / None
   heart_rate_bpm: int | None = None  # 30-220 or None
   timezone_hours: int = 0            # -12 to +14

   # In OracleUserResponse:
   gender: str | None = None
   heart_rate_bpm: int | None = None
   timezone_hours: int = 0
   ```

   Add Pydantic validators:

   ```python
   @field_validator("heart_rate_bpm")
   @classmethod
   def validate_bpm(cls, v: int | None) -> int | None:
       if v is not None and not (30 <= v <= 220):
           raise ValueError("heart_rate_bpm must be between 30 and 220")
       return v

   @field_validator("gender")
   @classmethod
   def validate_gender(cls, v: str | None) -> str | None:
       if v is not None and v not in ("male", "female"):
           raise ValueError("gender must be 'male', 'female', or null")
       return v
   ```

3. Ensure the existing `_encrypt_user_fields()` / `_decrypt_user()` functions in `api/app/routers/oracle.py` handle the new fields (they don't need encryption — BPM and gender are not sensitive). Just ensure they're included in the response mapping.

4. Update `services/oracle/oracle_service/framework_bridge.py` — ensure when building kwargs for `MasterOrchestrator.generate_reading()`, the bridge passes:
   - `actual_bpm=user.heart_rate_bpm` (if not None)
   - `latitude=user.latitude` and `longitude=user.longitude` (if coordinates available)
   - `gender=user.gender` (if not None)
   - `tz_hours=user.timezone_hours` (default 0)

   The bridge's `map_oracle_user_to_framework_kwargs()` function (from Session 6) or `UserProfile.to_framework_kwargs()` (from Session 7) should already handle some of these. Verify and fill gaps.

**Checkpoint:**

- [ ] ORM model compiles: `python3 -c "from app.orm.oracle_user import OracleUser; print(OracleUser.__table__.columns.keys())"`
- [ ] Pydantic model validates: `python3 -c "from app.models.oracle_user import OracleUserCreate; u = OracleUserCreate(name='Test', birthday='2000-01-01', mother_name='Mom', heart_rate_bpm=72); print(u.model_dump())"`
- [ ] BPM validation rejects out-of-range: `python3 -c "from app.models.oracle_user import OracleUserCreate; OracleUserCreate(name='T', birthday='2000-01-01', mother_name='M', heart_rate_bpm=300)"` should raise `ValidationError`
- Verify:
  ```bash
  cd api && python3 -c "from app.orm.oracle_user import OracleUser; cols = [c.name for c in OracleUser.__table__.columns]; assert 'gender' in cols; assert 'heart_rate_bpm' in cols; print('ORM columns:', cols)"
  ```

🚨 STOP if ORM or Pydantic model changes cause import errors

---

### Phase 3: Frontend Type Updates (~20 min)

**Tasks:**

1. Update `frontend/src/types/index.ts` — add new fields to `OracleUser`:

   ```typescript
   export interface OracleUser {
     // ... existing fields ...
     gender?: "male" | "female" | null;
     heart_rate_bpm?: number | null;
     timezone_hours?: number;
   }
   ```

   Add to `OracleUserCreate`:

   ```typescript
   export interface OracleUserCreate {
     // ... existing fields ...
     gender?: "male" | "female" | null;
     heart_rate_bpm?: number | null;
     timezone_hours?: number;
   }
   ```

2. Add new types for heartbeat/location display data:

   ```typescript
   export interface HeartbeatData {
     bpm: number;
     bpm_source: "actual" | "estimated";
     element: string;
     beats_per_day: number;
     total_lifetime_beats: number;
     rhythm_token: string;
   }

   export interface LocationElementData {
     element: string;
     timezone_estimate: number;
     lat_hemisphere: "N" | "S";
     lon_hemisphere: "E" | "W";
     lat_polarity: "Yang" | "Yin";
     lon_polarity: "Yang" | "Yin";
   }

   export interface ConfidenceData {
     score: number;
     level: "low" | "medium" | "high" | "very_high";
     factors: string;
   }

   export interface ConfidenceBoost {
     field: string;
     label: string;
     boost: number; // percentage points
     filled: boolean;
   }
   ```

**Checkpoint:**

- [ ] TypeScript compiles without errors: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
- [ ] New types are exported from `frontend/src/types/index.ts`

🚨 STOP if TypeScript type errors

---

### Phase 4: HeartbeatInput Component (~60 min)

**Tasks:**

1. Create `frontend/src/components/oracle/HeartbeatInput.tsx`:

   ```typescript
   interface HeartbeatInputProps {
     value: number | null;
     onChange: (bpm: number | null) => void;
   }
   ```

   Two input modes:

   **Mode A: Manual entry**
   - Number input field, range 30-220
   - Validate on blur, show error for out-of-range
   - Clear button to reset to null

   **Mode B: Tap-to-count**
   - Large tappable button with heart icon
   - User taps in rhythm with their pulse
   - Track last 5 inter-tap intervals
   - Calculate average BPM from intervals: `BPM = 60000 / avg_interval_ms`
   - Discard intervals > 3000ms (too slow, user probably paused)
   - Show real-time BPM as user taps
   - "Done" button to confirm measured BPM
   - Reset button to start over

   Implementation details:
   - Use `useRef` for tap timestamps (avoid re-renders during tapping)
   - Use `useState` for display BPM and mode toggle
   - Animate the heart icon on each tap (CSS pulse animation)
   - Show "Tap at least 5 times" instruction initially
   - Show "Keep tapping..." after 2-4 taps
   - Show calculated BPM after 5+ taps

2. Ensure the component is fully accessible:
   - Tap button has `aria-label="Tap to measure heart rate"`
   - BPM input has proper label association
   - Mode toggle has `role="tablist"` with `aria-selected`

**Checkpoint:**

- [ ] Component renders without errors
- [ ] Manual mode accepts numeric input 30-220
- [ ] Tap mode calculates BPM from 5+ taps
- Verify:
  ```bash
  cd frontend && npx tsc --noEmit 2>&1 | grep -i "HeartbeatInput" || echo "No type errors"
  ```

🚨 STOP if component has TypeScript errors

---

### Phase 5: Display Components (~90 min)

**Tasks:**

1. Create `frontend/src/components/oracle/HeartbeatDisplay.tsx`:

   ```typescript
   interface HeartbeatDisplayProps {
     heartbeat: HeartbeatData | null;
   }
   ```

   Display layout:
   - BPM with pulsing heart icon (CSS animation at the actual BPM rate)
   - Element badge with element color (Fire=red, Water=blue, Wood=green, Metal=gold, Earth=brown)
   - "Source: Actual" or "Source: Estimated" indicator
   - Lifetime beats counter (formatted with locale-appropriate thousands separator)
   - Rhythm token (FC60 encoded daily beats)
   - If `heartbeat` is null, show "No heartbeat data — add BPM to your profile for deeper readings" prompt

2. Create `frontend/src/components/oracle/LocationDisplay.tsx`:

   ```typescript
   interface LocationDisplayProps {
     location: LocationElementData | null;
   }
   ```

   Display layout:
   - Element badge with color
   - Hemisphere indicator: "N/E" or "S/W" etc.
   - Polarity: "Yang/Yin" pairing
   - Timezone estimate: "UTC+X" or "UTC-X"
   - If `location` is null, show "No location data — add coordinates for elemental mapping"

3. Create `frontend/src/components/oracle/ConfidenceMeter.tsx`:

   ```typescript
   interface ConfidenceMeterProps {
     confidence: ConfidenceData | null;
     boosts: ConfidenceBoost[];
   }
   ```

   Display layout:
   - **Progress bar** — horizontal bar filled to `score`%, colored by level:
     - `very_high` (85-95%): green (#16A34A)
     - `high` (75-84%): blue (#2563EB)
     - `medium` (65-74%): amber (#CA8A04)
     - `low` (50-64%): red (#DC2626)
   - **Score label** — e.g., "80% — High Confidence"
   - **Completeness breakdown** — list of optional fields with their boost values:
     ```
     ✅ Mother's name     +10%
     ✅ Location           +5%
     ❌ Heart rate         +5%   ← "Add to boost"
     ❌ Exact time         +5%
     ```
   - Each unfilled field shows a subtle "Add to boost" link that scrolls to the relevant form field
   - Tooltip on the progress bar showing: "Confidence is calculated from {N} data sources"

   **Input priority display** — small info tooltip showing the framework's input priority hierarchy:

   ```
   heartbeat > location > time > name > gender > DOB > mother
   ```

**Checkpoint:**

- [ ] All three components render without errors
- [ ] HeartbeatDisplay shows element with correct color
- [ ] LocationDisplay shows hemisphere and polarity
- [ ] ConfidenceMeter shows progress bar and completeness breakdown
- Verify:
  ```bash
  cd frontend && npx tsc --noEmit 2>&1 | grep -c "error" || echo "0 errors"
  ```

🚨 STOP if any component has TypeScript errors

---

### Phase 6: Integration into Existing Components (~60 min)

**Tasks:**

1. Update `frontend/src/components/oracle/UserForm.tsx` — add two new optional fields:

   **Gender selector:**

   ```tsx
   <select value={form.gender || ""} onChange={...}>
     <option value="">{t("oracle.gender_unspecified")}</option>
     <option value="male">{t("oracle.gender_male")}</option>
     <option value="female">{t("oracle.gender_female")}</option>
   </select>
   ```

   **BPM field:**
   - Use the `HeartbeatInput` component
   - Place below the existing location fields
   - Label: "Resting Heart Rate (optional)"
   - Show "+5% confidence" hint text next to label

2. Update `frontend/src/components/oracle/OracleConsultationForm.tsx`:
   - Add an expandable "Advanced Options" section below the location selector
   - Inside: `HeartbeatInput` for one-time BPM measurement during consultation
   - This is separate from the profile BPM — it allows the user to measure their current BPM for a specific reading
   - If the user has a profile BPM but enters a different one here, the consultation BPM takes precedence

3. Update `frontend/src/components/oracle/ReadingResults.tsx`:
   - Add `HeartbeatDisplay` component to the details tab
   - Add `LocationDisplay` component to the details tab
   - Add `ConfidenceMeter` component to the summary tab header (before reading content)
   - Pass heartbeat/location/confidence data from the reading result

4. Update `frontend/src/components/oracle/UserForm.tsx` `validate()` function — no validation needed for gender (optional), validate BPM only if provided (30-220).

**Checkpoint:**

- [ ] UserForm shows gender selector and BPM input
- [ ] OracleConsultationForm has expandable "Advanced Options" with HeartbeatInput
- [ ] ReadingResults includes HeartbeatDisplay, LocationDisplay, ConfidenceMeter
- [ ] All existing form behavior unchanged (new fields are optional)
- Verify:
  ```bash
  cd frontend && npx tsc --noEmit 2>&1 | grep -c "error" || echo "0 errors"
  ```

🚨 STOP if existing component behavior is broken

---

### Phase 7: i18n Translations (~30 min)

**Tasks:**

1. Add keys to `frontend/src/locales/en.json` under the `"oracle"` namespace:

   ```json
   {
     "oracle": {
       "heartbeat_label": "Resting Heart Rate",
       "heartbeat_placeholder": "BPM (30-220)",
       "heartbeat_optional": "Optional — adds rhythm data (+5% confidence)",
       "heartbeat_tap_mode": "Tap to Measure",
       "heartbeat_manual_mode": "Enter Manually",
       "heartbeat_tap_instruction": "Tap the button in rhythm with your pulse",
       "heartbeat_tap_count": "Taps: {{count}}",
       "heartbeat_tap_result": "Your BPM: {{bpm}}",
       "heartbeat_tap_confirm": "Use This BPM",
       "heartbeat_tap_reset": "Start Over",
       "heartbeat_tap_minimum": "Tap at least 5 times",
       "heartbeat_display_bpm": "{{bpm}} BPM",
       "heartbeat_display_element": "Element: {{element}}",
       "heartbeat_display_lifetime": "{{beats}} lifetime beats",
       "heartbeat_display_source_actual": "Measured",
       "heartbeat_display_source_estimated": "Estimated",
       "heartbeat_display_empty": "No heartbeat data — add BPM for deeper readings",
       "location_display_element": "Element: {{element}}",
       "location_display_hemisphere": "{{lat_hem}}/{{lon_hem}}",
       "location_display_polarity": "{{lat_pol}}/{{lon_pol}}",
       "location_display_timezone": "UTC{{offset}}",
       "location_display_empty": "No location data — add coordinates for elemental mapping",
       "confidence_label": "Reading Confidence",
       "confidence_score": "{{score}}%",
       "confidence_level_low": "Low Confidence",
       "confidence_level_medium": "Medium Confidence",
       "confidence_level_high": "High Confidence",
       "confidence_level_very_high": "Very High Confidence",
       "confidence_boost_mother": "Mother's name",
       "confidence_boost_location": "Location",
       "confidence_boost_heartbeat": "Heart rate",
       "confidence_boost_time": "Exact time",
       "confidence_boost_gender": "Gender",
       "confidence_boost_add": "Add to boost",
       "confidence_factors": "Based on {{count}} data sources",
       "confidence_priority_hint": "Input priority: heartbeat > location > time > name > gender > DOB > mother",
       "gender_label": "Gender (optional)",
       "gender_unspecified": "Prefer not to say",
       "gender_male": "Male",
       "gender_female": "Female",
       "advanced_options": "Advanced Options",
       "advanced_options_hint": "BPM measurement for this reading"
     }
   }
   ```

2. Add Persian translations to `frontend/src/locales/fa.json`:

   ```json
   {
     "oracle": {
       "heartbeat_label": "ضربان قلب در حالت استراحت",
       "heartbeat_placeholder": "ضربان در دقیقه (۳۰-۲۲۰)",
       "heartbeat_optional": "اختیاری — داده ریتمیک اضافه می‌کند (+۵٪ اطمینان)",
       "heartbeat_tap_mode": "اندازه‌گیری با ضربه",
       "heartbeat_manual_mode": "ورود دستی",
       "heartbeat_tap_instruction": "دکمه را هم‌ریتم با نبض خود بزنید",
       "heartbeat_tap_count": "ضربه‌ها: {{count}}",
       "heartbeat_tap_result": "ضربان شما: {{bpm}}",
       "heartbeat_tap_confirm": "استفاده از این ضربان",
       "heartbeat_tap_reset": "شروع دوباره",
       "heartbeat_tap_minimum": "حداقل ۵ بار ضربه بزنید",
       "heartbeat_display_bpm": "{{bpm}} ضربان در دقیقه",
       "heartbeat_display_element": "عنصر: {{element}}",
       "heartbeat_display_lifetime": "{{beats}} ضربان در طول عمر",
       "heartbeat_display_source_actual": "اندازه‌گیری شده",
       "heartbeat_display_source_estimated": "تخمینی",
       "heartbeat_display_empty": "داده ضربان قلب موجود نیست — ضربان را اضافه کنید",
       "location_display_element": "عنصر: {{element}}",
       "location_display_hemisphere": "{{lat_hem}}/{{lon_hem}}",
       "location_display_polarity": "{{lat_pol}}/{{lon_pol}}",
       "location_display_timezone": "UTC{{offset}}",
       "location_display_empty": "داده مکان موجود نیست — مختصات را اضافه کنید",
       "confidence_label": "اطمینان خوانش",
       "confidence_score": "{{score}}٪",
       "confidence_level_low": "اطمینان پایین",
       "confidence_level_medium": "اطمینان متوسط",
       "confidence_level_high": "اطمینان بالا",
       "confidence_level_very_high": "اطمینان بسیار بالا",
       "confidence_boost_mother": "نام مادر",
       "confidence_boost_location": "موقعیت مکانی",
       "confidence_boost_heartbeat": "ضربان قلب",
       "confidence_boost_time": "زمان دقیق",
       "confidence_boost_gender": "جنسیت",
       "confidence_boost_add": "اضافه کنید",
       "confidence_factors": "بر اساس {{count}} منبع داده",
       "confidence_priority_hint": "اولویت ورودی: ضربان قلب > مکان > زمان > نام > جنسیت > تاریخ تولد > مادر",
       "gender_label": "جنسیت (اختیاری)",
       "gender_unspecified": "ترجیح می‌دهم نگویم",
       "gender_male": "مرد",
       "gender_female": "زن",
       "advanced_options": "گزینه‌های پیشرفته",
       "advanced_options_hint": "اندازه‌گیری ضربان قلب برای این خوانش"
     }
   }
   ```

   Note: Merge these keys into the existing `"oracle"` namespace — do not replace existing keys.

**Checkpoint:**

- [ ] All new i18n keys are present in both `en.json` and `fa.json`
- [ ] Key count matches between EN and FA
- [ ] No JSON syntax errors
- Verify:
  ```bash
  cd frontend && python3 -c "
  import json
  en = json.load(open('src/locales/en.json'))
  fa = json.load(open('src/locales/fa.json'))
  en_keys = set(en.get('oracle', {}).keys())
  fa_keys = set(fa.get('oracle', {}).keys())
  missing = en_keys - fa_keys
  if missing:
      print(f'Missing FA keys: {missing}')
  else:
      print(f'All {len(en_keys)} oracle keys present in both languages')
  "
  ```

🚨 STOP if JSON parse errors or missing translations

---

### Phase 8: Backend Bridge Verification (~30 min)

**Tasks:**

1. Verify `services/oracle/oracle_service/framework_bridge.py` passes optional data through. The key mapping should be:

   | User Profile Field             | Framework Parameter | Default if Missing                    |
   | ------------------------------ | ------------------- | ------------------------------------- |
   | `heart_rate_bpm`               | `actual_bpm`        | `None` (framework estimates from age) |
   | `latitude` (from coordinates)  | `latitude`          | `None` (location section omitted)     |
   | `longitude` (from coordinates) | `longitude`         | `None` (location section omitted)     |
   | `gender`                       | `gender`            | `None` (polarity section omitted)     |
   | `timezone_hours`               | `tz_hours`          | `0` (UTC default)                     |

2. If Session 7's `UserProfile.to_framework_kwargs()` already handles these mappings, verify it. If not, add the mapping in the bridge's data preparation step.

3. Verify that when heartbeat/location data is missing, the framework still produces a valid reading with reduced confidence (graceful degradation, never crashes).

**Checkpoint:**

- [ ] Bridge passes `actual_bpm` when user has BPM
- [ ] Bridge passes `latitude`/`longitude` when user has coordinates
- [ ] Bridge passes `gender` when user has gender
- [ ] Missing optional fields produce valid readings (no crashes)
- Verify:
  ```bash
  cd services/oracle && python3 -c "
  import oracle_service
  from oracle_service.framework_bridge import generate_single_reading
  # Minimal reading (no optional data)
  r1 = generate_single_reading('Test', 1, 1, 2000)
  out1 = r1.framework_output if hasattr(r1, 'framework_output') else r1
  print(f'Minimal confidence: {out1[\"confidence\"][\"score\"]}%')
  assert out1['heartbeat'] is not None, 'Heartbeat should be estimated even without BPM'
  assert out1['location'] is None, 'Location should be None without coordinates'
  print('Minimal reading OK')
  " 2>/dev/null || echo "Bridge test skipped — Sessions 6-7 may not be complete"
  ```

🚨 STOP if bridge crashes on missing optional data

---

### Phase 9: Write Tests (~60 min)

**Tasks:**

Create test files as listed in the TESTS TO WRITE section below.

**Backend tests** — `services/oracle/tests/test_heartbeat_location_bridge.py`:

```python
"""Tests for heartbeat and location data flow through the framework bridge."""

import pytest


class TestHeartbeatBridge:
    """Verify heartbeat data passes through bridge to framework."""

    def test_actual_bpm_passed_to_framework(self): ...
    def test_missing_bpm_uses_estimated(self): ...
    def test_bpm_element_mapping(self): ...
    def test_bpm_lifetime_beats_positive(self): ...


class TestLocationBridge:
    """Verify location data passes through bridge to framework."""

    def test_coordinates_produce_location_data(self): ...
    def test_missing_coordinates_returns_none(self): ...
    def test_location_element_mapping(self): ...


class TestConfidenceBridge:
    """Verify confidence scoring includes heartbeat/location boosts."""

    def test_confidence_with_all_optional_data(self): ...
    def test_confidence_without_optional_data(self): ...
    def test_confidence_partial_optional_data(self): ...
```

**Frontend tests** — `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`:

```typescript
describe("HeartbeatInput", () => {
  it("renders manual input mode by default", () => { ... });
  it("accepts valid BPM in range 30-220", () => { ... });
  it("rejects BPM below 30", () => { ... });
  it("rejects BPM above 220", () => { ... });
  it("clears value when clear button clicked", () => { ... });
});
```

**Frontend tests** — `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx`:

```typescript
describe("ConfidenceMeter", () => {
  it("renders progress bar with correct width", () => { ... });
  it("shows correct color for high confidence", () => { ... });
  it("shows correct color for low confidence", () => { ... });
  it("displays completeness breakdown", () => { ... });
  it("marks filled fields with checkmark", () => { ... });
  it("shows 'Add to boost' for unfilled fields", () => { ... });
});
```

**Checkpoint:**

- [ ] All backend tests pass: `cd services/oracle && python3 -m pytest tests/test_heartbeat_location_bridge.py -v --tb=short`
- [ ] All frontend tests pass: `cd frontend && npx vitest run src/components/oracle/__tests__/HeartbeatInput.test.tsx src/components/oracle/__tests__/ConfidenceMeter.test.tsx`

🚨 STOP if any tests fail

---

### Phase 10: Final Verification (~20 min)

**Tasks:**

1. Run full frontend type check:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

2. Run full backend import check:

   ```bash
   cd services/oracle && python3 -c "
   import oracle_service
   from oracle_service.framework_bridge import generate_single_reading
   print('All Oracle imports OK')
   "
   ```

3. Run framework tests to verify no regressions:

   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py
   ```

4. Verify file structure:
   ```bash
   ls -la frontend/src/components/oracle/HeartbeatInput.tsx
   ls -la frontend/src/components/oracle/HeartbeatDisplay.tsx
   ls -la frontend/src/components/oracle/LocationDisplay.tsx
   ls -la frontend/src/components/oracle/ConfidenceMeter.tsx
   ls -la database/migrations/012_heartbeat_location_columns.sql
   ls -la services/oracle/tests/test_heartbeat_location_bridge.py
   ```

**Checkpoint:**

- [ ] Zero TypeScript errors
- [ ] Zero Python import errors
- [ ] Framework 180 tests pass
- [ ] All new files exist at expected paths
- [ ] All new tests pass

---

## TESTS TO WRITE

| Path                                                                | Function/Test Name                        | Description                                                                                            |
| ------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_actual_bpm_passed_to_framework`     | When user has `heart_rate_bpm=72`, framework output `heartbeat.bpm` is 72 and `bpm_source` is "actual" |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_missing_bpm_uses_estimated`         | When user has no BPM, framework estimates from age; `bpm_source` is "estimated"                        |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_bpm_element_mapping`                | BPM of 72 maps to element via `72 % 5` → index 2 → "Earth"                                             |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_bpm_lifetime_beats_positive`        | Lifetime beats for age > 0 is always positive                                                          |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_coordinates_produce_location_data`  | Lat/lon (40.7, -74.0) produces non-None location with element "Metal"                                  |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_missing_coordinates_returns_none`   | No lat/lon produces `location=None` in reading                                                         |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_location_element_mapping`           | NYC (40.7N) → Metal, Cairo (30.0N) → Earth, London (51.5N) → Water                                     |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_confidence_with_all_optional_data`  | Reading with BPM + location + mother + gender has higher confidence than minimal                       |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_confidence_without_optional_data`   | Minimal reading (name + DOB only) has confidence >= 50                                                 |
| `services/oracle/tests/test_heartbeat_location_bridge.py`           | `test_confidence_partial_optional_data`   | Adding location boosts confidence by ~5%                                                               |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | `renders manual input mode by default`    | Component shows number input field on initial render                                                   |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | `accepts valid BPM in range`              | Entering 72 calls onChange with 72                                                                     |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | `rejects BPM below 30`                    | Shows validation error for BPM < 30                                                                    |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | `rejects BPM above 220`                   | Shows validation error for BPM > 220                                                                   |
| `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx`  | `clears value on clear button click`      | Clear button calls onChange with null                                                                  |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | `renders progress bar with correct width` | Score=80 → progress bar width is 80%                                                                   |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | `shows correct color for high confidence` | Score >= 75 shows blue color                                                                           |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | `shows correct color for low confidence`  | Score < 65 shows red color                                                                             |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | `displays completeness breakdown`         | Renders list of boost fields with filled/unfilled indicators                                           |
| `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` | `marks filled fields with checkmark`      | Filled field shows check icon                                                                          |

**Total: 20 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] Migration `012_heartbeat_location_columns.sql` exists with valid SQL
- [ ] `oracle_users` table gains `gender`, `heart_rate_bpm`, `timezone_hours` columns
- [ ] ORM model includes new columns; Pydantic models validate BPM range (30-220) and gender values
- [ ] TypeScript `OracleUser` and `OracleUserCreate` interfaces include new fields
- [ ] `HeartbeatInput.tsx` supports manual entry (30-220) and tap-to-count mode
- [ ] `HeartbeatDisplay.tsx` renders BPM, element, lifetime beats, and source indicator
- [ ] `LocationDisplay.tsx` renders element, hemisphere, polarity, and timezone
- [ ] `ConfidenceMeter.tsx` shows progress bar, score label, and completeness breakdown with individual boost values
- [ ] `UserForm.tsx` includes gender selector and BPM input
- [ ] `ReadingResults.tsx` includes all three new display components
- [ ] All i18n keys present in both `en.json` and `fa.json`
- [ ] Framework bridge passes `actual_bpm`, `latitude`, `longitude`, `gender` to `MasterOrchestrator`
- [ ] Missing optional fields produce valid readings (graceful degradation)
- [ ] All 20+ tests pass
- [ ] Framework 180 tests still pass (no regressions)
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_heartbeat_location_bridge.py -v --tb=short && echo "BACKEND TESTS OK"
  cd frontend && npx tsc --noEmit && echo "TYPES OK"
  cd frontend && npx vitest run src/components/oracle/__tests__/HeartbeatInput.test.tsx src/components/oracle/__tests__/ConfidenceMeter.test.tsx && echo "FRONTEND TESTS OK"
  cd numerology_ai_framework && python3 tests/test_all.py && echo "FRAMEWORK OK"
  ```

---

## ERROR SCENARIOS

| Scenario                                                           | Expected Behavior                                                                                  | Recovery                                                            |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Migration fails (column already exists)                            | `ADD COLUMN IF NOT EXISTS` prevents error                                                          | Check if prior run partially applied; use rollback then re-run      |
| BPM value out of range (< 30 or > 220)                             | Pydantic validator rejects; frontend shows error message                                           | Clamp to range or show validation error with acceptable range       |
| Tap-to-count produces unreasonable BPM                             | Intervals > 3000ms discarded; BPM < 30 or > 220 shows warning "Unusual reading — please try again" | Auto-reset tap session after 5 seconds of inactivity                |
| User enters BPM but browser doesn't support `useRef`               | Impossible (React 16.8+), but if SSR: guard with `typeof window !== 'undefined'`                   | n/a — all target browsers support hooks                             |
| Location coordinates are (0, 0) — equator/prime meridian           | Valid location: Fire element, TZ=0. Not an error — some users genuinely live near (0,0)            | Framework handles correctly per test vectors                        |
| User has coordinates but LocationEngine returns unexpected element | All latitudes map to one of 5 elements. No undefined case exists in `LATITUDE_ZONES`               | Verify against test vectors: NYC→Metal, Cairo→Earth, London→Water   |
| Framework bridge receives `gender="other"` (not male/female)       | Pydantic validator rejects at API layer; DB constraint also rejects                                | Frontend only offers male/female/null; "other" cannot reach backend |
| Persian locale but element names are in English                    | Element names in HeartbeatDisplay and LocationDisplay use i18n keys, not raw strings               | Ensure element names go through `t()` translation function          |
| Confidence meter receives null confidence data                     | Show "Calculating..." placeholder or hide meter entirely                                           | Guard with `if (!confidence) return <Skeleton />`                   |
| Existing UserForm tests fail because of new fields                 | New fields are optional with defaults — existing test data should still work                       | Ensure new fields have `= ""` / `= null` defaults in form state     |

---

## HANDOFF

**Created:**

- `database/migrations/012_heartbeat_location_columns.sql` — adds `gender`, `heart_rate_bpm`, `timezone_hours` to `oracle_users`
- `database/migrations/012_heartbeat_location_columns_rollback.sql` — rollback
- `frontend/src/components/oracle/HeartbeatInput.tsx` — BPM input with manual + tap-to-count modes
- `frontend/src/components/oracle/HeartbeatDisplay.tsx` — renders heartbeat engine output
- `frontend/src/components/oracle/LocationDisplay.tsx` — renders location engine output
- `frontend/src/components/oracle/ConfidenceMeter.tsx` — visual confidence bar with completeness breakdown
- `frontend/src/components/oracle/__tests__/HeartbeatInput.test.tsx` — 5 tests
- `frontend/src/components/oracle/__tests__/ConfidenceMeter.test.tsx` — 6 tests
- `services/oracle/tests/test_heartbeat_location_bridge.py` — 10 tests

**Modified:**

- `api/app/orm/oracle_user.py` — 3 new columns
- `api/app/models/oracle_user.py` — 3 new Pydantic fields with validators
- `frontend/src/types/index.ts` — new fields on `OracleUser`, `OracleUserCreate`; new interfaces `HeartbeatData`, `LocationElementData`, `ConfidenceData`, `ConfidenceBoost`
- `frontend/src/components/oracle/UserForm.tsx` — gender selector + BPM input
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — expandable "Advanced Options" with HeartbeatInput
- `frontend/src/components/oracle/ReadingResults.tsx` — integrates HeartbeatDisplay, LocationDisplay, ConfidenceMeter
- `frontend/src/locales/en.json` — ~35 new i18n keys under `oracle` namespace
- `frontend/src/locales/fa.json` — matching Persian translations
- `services/oracle/oracle_service/framework_bridge.py` — verified/updated heartbeat+location data passthrough

**Deleted:**

- None

**Calculation Engines block (Sessions 6-12) is now COMPLETE.**

**Next block (AI & Reading Types, Session 13) receives:**

- All framework engines fully integrated: FC60 stamps, numerology, moon, ganzhi, heartbeat, location, patterns, confidence
- User profiles can include gender, BPM, timezone, and location coordinates
- `framework_bridge.py` passes all available user data to `MasterOrchestrator.generate_reading()`
- Pattern data is formatted for AI prompts (from Session 9's `PatternFormatter.format_for_ai()`)
- Confidence scoring works end-to-end with visual display
- Frontend has all display components ready for reading result rendering
- Session 13 can focus entirely on connecting the Anthropic AI API to the framework output
