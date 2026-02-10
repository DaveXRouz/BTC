# SESSION 4 SPEC — Oracle Profiles Form & Validation UI

**Block:** Foundation (Sessions 1-5)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium
**Dependencies:** Session 1 (schema — new oracle_users columns), Session 2 (auth — JWT), Session 3 (API — oracle user CRUD with new fields + ownership)

---

## TL;DR

- Rewrite `UserForm.tsx` from a 7-field basic form to a 13-field form with all oracle_users columns (gender, heart_rate_bpm, timezone, coordinates)
- Integrate existing `PersianKeyboard.tsx` into Persian name fields (currently standalone, not wired)
- Replace native `<input type="date">` with existing `CalendarPicker.tsx` (dual Gregorian/Jalaali)
- Replace manual country/city text inputs with existing `LocationSelector.tsx` (GPS auto-detect + dropdown)
- Create `UserCard.tsx` — compact profile display card for grid/list views
- Create `UserProfileList.tsx` — searchable card grid of all user profiles with create/edit/delete actions
- Expand TypeScript types and API client to match Session 3's enhanced response model
- Write 18+ tests covering new fields, component integrations, validation, and the new components

---

## OBJECTIVES

1. **Expand OracleUser types** — Add gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude, created_by to `OracleUser`, `OracleUserCreate`, and `OracleUserUpdate` interfaces
2. **Rewrite UserForm** — 13-field modal form integrating PersianKeyboard (for name_persian, mother_name_persian), CalendarPicker (for birthday), and LocationSelector (for coordinates/country/city), plus new fields (gender dropdown, heart_rate_bpm number input, timezone selectors)
3. **Create UserCard** — Compact card component displaying user name, birthday, country/city, gender badge, and action buttons (edit/delete)
4. **Create UserProfileList** — Searchable grid of UserCards with "Add Profile" button, loading/empty states, and search filtering
5. **Update API client & hooks** — Ensure `api.ts` and `useOracleUsers.ts` pass new fields through correctly
6. **Write comprehensive tests** — 18+ tests covering expanded UserForm, UserCard, UserProfileList, and integration scenarios

---

## PREREQUISITES

- [ ] Session 1 complete — `oracle_users` table has `gender`, `heart_rate_bpm`, `timezone_hours`, `timezone_minutes` columns
- [ ] Session 2 complete — Auth working with JWT tokens
- [ ] Session 3 complete — Oracle user CRUD endpoints return new fields (gender, heart_rate_bpm, timezone, latitude, longitude, created_by) and enforce ownership
- [ ] Existing components verified:
  - `PersianKeyboard.tsx` renders and fires `onCharacterClick` / `onBackspace` / `onClose`
  - `CalendarPicker.tsx` renders dual calendar and fires `onChange` with ISO date string
  - `LocationSelector.tsx` renders country dropdown + GPS detect and fires `onChange` with `LocationData`
- Verification:
  ```bash
  test -f frontend/src/components/oracle/PersianKeyboard.tsx && \
  test -f frontend/src/components/oracle/CalendarPicker.tsx && \
  test -f frontend/src/components/oracle/LocationSelector.tsx && \
  test -f frontend/src/components/oracle/UserForm.tsx && \
  test -f frontend/src/types/index.ts && \
  test -f frontend/src/services/api.ts && \
  test -f frontend/src/hooks/useOracleUsers.ts && \
  echo "Prerequisites OK"
  ```

---

## EXISTING CODE ANALYSIS

### What Already Works (Keep & Enhance)

**UserForm.tsx** (262 lines) — `frontend/src/components/oracle/UserForm.tsx`:

- Modal dialog with backdrop close
- 7 fields: name, name_persian, birthday, mother_name, mother_name_persian, country, city
- Client-side validation for name (min 2 chars), birthday (required, not future), mother_name (min 2 chars)
- Edit/create mode toggle, delete confirmation (two-click), isSubmitting state
- Uses generic `Field` sub-component for all inputs
- **Missing:** gender, heart_rate_bpm, timezone, coordinates, PersianKeyboard integration, CalendarPicker integration, LocationSelector integration

**PersianKeyboard.tsx** (90 lines) — `frontend/src/components/oracle/PersianKeyboard.tsx`:

- Standalone component with `onCharacterClick`, `onBackspace`, `onClose` props
- Full Persian QWERTY layout via `PERSIAN_ROWS` from `@/utils/persianKeyboardLayout`
- Positioned absolute (relative to parent), with backdrop for outside-click close
- RTL direction, Escape key to close
- **Not wired:** UserForm's Persian fields use plain `<input dir="rtl">`, no keyboard toggle

**CalendarPicker.tsx** (245 lines) — `frontend/src/components/oracle/CalendarPicker.tsx`:

- Props: `value: string` (ISO "YYYY-MM-DD"), `onChange: (isoDate: string) => void`, `label?`, `error?`
- Dual Gregorian/Jalaali toggle, visual month grid, year/month navigation
- Custom implementation (no external calendar library)
- **Not used:** UserForm uses `<input type="date">` for birthday

**LocationSelector.tsx** (106 lines) — `frontend/src/components/oracle/LocationSelector.tsx`:

- Props: `value: LocationData | null`, `onChange: (data: LocationData) => void`
- GPS auto-detect button via `getCurrentPosition()`
- Country dropdown from `COUNTRIES` object (with lat/lon presets)
- City text input
- Displays coordinates when available
- **Not used:** UserForm has separate country/city text inputs with no coordinate capture

**UserSelector.tsx** (72 lines) — `frontend/src/components/oracle/UserSelector.tsx`:

- Dropdown selector for choosing active user profile
- "Add new" and "Edit" buttons
- Loading state
- **Keep as-is:** This component works correctly, no changes needed

**useOracleUsers.ts** (45 lines) — `frontend/src/hooks/useOracleUsers.ts`:

- 5 hooks: useOracleUsers (list), useOracleUser (single), useCreateOracleUser, useUpdateOracleUser, useDeleteOracleUser
- Uses React Query with `["oracleUsers"]` query key
- **Verify:** Hook signatures pass through new fields correctly (they use generic types, so should work once types are updated)

**api.ts** — `frontend/src/services/api.ts` (lines 109-135):

- `oracleUsers.list()` — returns `OracleUser[]` from paginated response
- `oracleUsers.get(id)` — returns single `OracleUser`
- `oracleUsers.create(data)` — sends `OracleUserCreate`, returns `OracleUser`
- `oracleUsers.update(id, data)` — sends `OracleUserUpdate`, returns `OracleUser`
- `oracleUsers.delete(id)` — void
- **Verify:** These pass through whatever types define, so updating types is sufficient

### Gaps to Close

| Component                    | Current                 | Session 4 Target                                                                                          |
| ---------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------- |
| `OracleUser` type            | 10 fields               | 17 fields (add gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude, created_by) |
| `OracleUserCreate` type      | 7 fields                | 13 fields (add gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude)             |
| `UserForm.tsx`               | 7 inputs, all text/date | 13 inputs + PersianKeyboard + CalendarPicker + LocationSelector                                           |
| PersianKeyboard integration  | Not connected           | Toggled on `name_persian` and `mother_name_persian` fields                                                |
| CalendarPicker integration   | Not used                | Replaces `<input type="date">` for birthday                                                               |
| LocationSelector integration | Not used                | Replaces country/city text inputs, captures coordinates                                                   |
| `UserCard.tsx`               | Does not exist          | Compact profile card with name, birthday, location, actions                                               |
| `UserProfileList.tsx`        | Does not exist          | Searchable grid of UserCards                                                                              |

---

## FILES TO CREATE

- `frontend/src/components/oracle/UserCard.tsx` — Profile display card
- `frontend/src/components/oracle/UserProfileList.tsx` — Searchable profile grid
- `frontend/src/components/oracle/__tests__/UserCard.test.tsx` — UserCard tests
- `frontend/src/components/oracle/__tests__/UserProfileList.test.tsx` — UserProfileList tests

## FILES TO MODIFY

- `frontend/src/types/index.ts` — Expand OracleUser, OracleUserCreate, OracleUserUpdate interfaces
- `frontend/src/components/oracle/UserForm.tsx` — Major rewrite: 13 fields, component integrations, enhanced validation
- `frontend/src/components/oracle/__tests__/UserForm.test.tsx` — Expand with tests for new fields and integrations
- `frontend/src/services/api.ts` — Verify/minor adjustments if needed for new field pass-through
- `frontend/src/hooks/useOracleUsers.ts` — Verify/minor adjustments if needed

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Update TypeScript Types (~20 min)

**Tasks:**

1. Update `frontend/src/types/index.ts` — `OracleUser` interface:

   Add after existing fields:

   ```typescript
   export interface OracleUser {
     id: number;
     name: string;
     name_persian?: string;
     birthday: string; // "YYYY-MM-DD"
     mother_name: string;
     mother_name_persian?: string;
     country?: string;
     city?: string;
     // NEW fields from Session 1 schema + Session 3 API
     gender?: string; // "male" | "female" | null
     heart_rate_bpm?: number; // 30-220 | null
     timezone_hours?: number; // -12 to +14
     timezone_minutes?: number; // 0-59
     latitude?: number; // -90 to 90
     longitude?: number; // -180 to 180
     created_by?: string; // UUID of system user who created this profile
     created_at?: string;
     updated_at?: string;
   }
   ```

2. Update `OracleUserCreate` interface:

   ```typescript
   export interface OracleUserCreate {
     name: string;
     name_persian?: string;
     birthday: string;
     mother_name: string;
     mother_name_persian?: string;
     country?: string;
     city?: string;
     // NEW fields
     gender?: string;
     heart_rate_bpm?: number;
     timezone_hours?: number;
     timezone_minutes?: number;
     latitude?: number;
     longitude?: number;
   }
   ```

3. Update `OracleUserUpdate`:

   ```typescript
   export type OracleUserUpdate = Partial<OracleUserCreate>;
   ```

   This already works — `Partial<OracleUserCreate>` will automatically include the new fields since it derives from `OracleUserCreate`.

**Checkpoint:**

- [ ] `OracleUser` has 17 fields (id + 9 existing + 7 new)
- [ ] `OracleUserCreate` has 13 fields (7 existing + 6 new)
- [ ] `OracleUserUpdate` still uses `Partial<OracleUserCreate>`
- [ ] No TypeScript compilation errors: `cd frontend && npx tsc --noEmit`
- Verify: `grep -c "gender\|heart_rate_bpm\|timezone_hours\|timezone_minutes\|latitude\|longitude\|created_by" frontend/src/types/index.ts` — should return 7+

STOP if checkpoint fails

---

### Phase 2: Rewrite UserForm.tsx (~90 min)

This is the largest phase. The form grows from 7 fields to 13 fields and integrates 3 existing components.

**Tasks:**

1. **Update `FormErrors` interface** — add error keys for all new validatable fields:

   ```typescript
   interface FormErrors {
     name?: string;
     birthday?: string;
     mother_name?: string;
     gender?: string;
     heart_rate_bpm?: string;
     timezone_hours?: string;
     timezone_minutes?: string;
   }
   ```

2. **Update `validate()` function** — add validation for new fields:

   ```typescript
   // Existing: name min 2, birthday required + not future, mother_name min 2
   // NEW validations:
   if (data.name && /\d/.test(data.name)) {
     errors.name = t("oracle.error_name_no_digits");
   }
   if (data.birthday) {
     const bd = new Date(data.birthday);
     if (bd.getFullYear() < 1900) {
       errors.birthday = t("oracle.error_birthday_too_old");
     }
   }
   if (data.heart_rate_bpm !== undefined && data.heart_rate_bpm !== null) {
     if (data.heart_rate_bpm < 30 || data.heart_rate_bpm > 220) {
       errors.heart_rate_bpm = t("oracle.error_heart_rate_range");
     }
   }
   ```

3. **Update form state** — expand initial state with new fields:

   ```typescript
   const [form, setForm] = useState<OracleUserCreate>({
     name: user?.name ?? "",
     name_persian: user?.name_persian ?? "",
     birthday: user?.birthday ?? "",
     mother_name: user?.mother_name ?? "",
     mother_name_persian: user?.mother_name_persian ?? "",
     country: user?.country ?? "",
     city: user?.city ?? "",
     gender: user?.gender ?? undefined,
     heart_rate_bpm: user?.heart_rate_bpm ?? undefined,
     timezone_hours: user?.timezone_hours ?? 0,
     timezone_minutes: user?.timezone_minutes ?? 0,
     latitude: user?.latitude ?? undefined,
     longitude: user?.longitude ?? undefined,
   });
   ```

4. **Add PersianKeyboard integration for Persian name fields:**

   For each Persian field (`name_persian`, `mother_name_persian`), add:
   - A state `showKeyboard` tracking which field is active (null | "name_persian" | "mother_name_persian")
   - A keyboard toggle button (small keyboard icon) next to the input
   - When PersianKeyboard's `onCharacterClick` fires, append char to the active field
   - When `onBackspace` fires, remove last char from the active field
   - When `onClose` fires, set `showKeyboard` to null
   - PersianKeyboard positioned relative to the field's container

   ```typescript
   const [activeKeyboard, setActiveKeyboard] = useState<string | null>(null);

   function handleKeyboardChar(char: string) {
     if (!activeKeyboard) return;
     setForm((prev) => ({
       ...prev,
       [activeKeyboard]:
         (prev[activeKeyboard as keyof OracleUserCreate] ?? "") + char,
     }));
   }

   function handleKeyboardBackspace() {
     if (!activeKeyboard) return;
     setForm((prev) => {
       const current = String(
         prev[activeKeyboard as keyof OracleUserCreate] ?? "",
       );
       return { ...prev, [activeKeyboard]: current.slice(0, -1) };
     });
   }
   ```

5. **Replace birthday `<input type="date">` with CalendarPicker:**

   ```tsx
   <CalendarPicker
     value={form.birthday}
     onChange={(isoDate) => handleChange("birthday", isoDate)}
     label={t("oracle.field_birthday")}
     error={errors.birthday}
   />
   ```

6. **Replace country/city text inputs with LocationSelector:**

   ```tsx
   <LocationSelector
     value={
       form.latitude !== undefined && form.longitude !== undefined
         ? {
             lat: form.latitude,
             lon: form.longitude,
             country: form.country,
             city: form.city,
           }
         : null
     }
     onChange={(loc) => {
       setForm((prev) => ({
         ...prev,
         country: loc.country ?? prev.country,
         city: loc.city ?? prev.city,
         latitude: loc.lat,
         longitude: loc.lon,
       }));
     }}
   />
   ```

7. **Add new field inputs:**
   - **Gender:** `<select>` with options: empty/male/female
   - **Heart Rate BPM:** `<input type="number" min={30} max={220}>`
   - **Timezone Hours:** `<select>` with options -12 to +14
   - **Timezone Minutes:** `<select>` with options 0, 15, 30, 45

8. **Organize form layout into logical sections:**
   - Section 1: Identity (name, name_persian + keyboard, birthday via CalendarPicker)
   - Section 2: Family (mother_name, mother_name_persian + keyboard)
   - Section 3: Location (LocationSelector replaces country/city)
   - Section 4: Profile Details (gender, heart_rate_bpm, timezone)
   - Each section has a subtle divider or heading

9. **Update `handleChange` for mixed types** — the current handler only accepts strings. New fields need number support:

   ```typescript
   function handleFieldChange(
     field: keyof OracleUserCreate,
     value: string | number | undefined,
   ) {
     setForm((prev) => ({ ...prev, [field]: value }));
     if (errors[field as keyof FormErrors]) {
       setErrors((prev) => ({ ...prev, [field]: undefined }));
     }
   }
   ```

**Checkpoint:**

- [ ] UserForm renders with 13 fields organized in 4 sections
- [ ] PersianKeyboard toggle appears next to `name_persian` and `mother_name_persian`
- [ ] CalendarPicker replaces the native date input for birthday
- [ ] LocationSelector replaces country/city text inputs
- [ ] Gender dropdown works (male/female/empty)
- [ ] Heart rate BPM input accepts numbers 30-220
- [ ] Timezone selectors work (-12 to +14 hours, 0/15/30/45 minutes)
- [ ] All existing validation still works (name min 2, birthday required, mother_name min 2)
- [ ] New validation works (name no digits, birthday after 1900, BPM range)
- [ ] Form submits with all fields included in payload
- [ ] Edit mode pre-populates all 13 fields
- Verify: `cd frontend && npx tsc --noEmit` — no errors

STOP if checkpoint fails

---

### Phase 3: Create UserCard Component (~30 min)

**Tasks:**

1. Create `frontend/src/components/oracle/UserCard.tsx`:

   ```typescript
   interface UserCardProps {
     user: OracleUser;
     onEdit: (user: OracleUser) => void;
     onDelete: (user: OracleUser) => void;
     onSelect?: (user: OracleUser) => void;
     isSelected?: boolean;
   }
   ```

2. Card displays:
   - User name (bold) + Persian name (if exists, in RTL)
   - Birthday formatted (show both Gregorian and Jalaali using `formatDate` from `@/utils/dateFormatters`)
   - Location: country + city (if available)
   - Gender badge (if set): small colored pill ("Male" / "Female")
   - Heart rate indicator (if set): small icon + BPM value
   - Timezone display (if non-zero): UTC offset string like "UTC+3:30"
   - Action buttons: Edit (pencil icon), Delete (trash icon)
   - Selected state: highlighted border when `isSelected` is true

3. Styling:
   - Tailwind classes matching `nps-*` design tokens (consistent with existing components)
   - Compact card: fixed height, responsive width
   - Hover state: subtle border color change
   - RTL-aware: Persian name right-aligned

4. Accessibility:
   - Card is a `<div>` with `role="article"` and `aria-label` with user name
   - Action buttons have `aria-label` attributes
   - Keyboard focusable if `onSelect` provided

**Checkpoint:**

- [ ] `UserCard.tsx` renders user info (name, birthday, location, gender, BPM, timezone)
- [ ] Edit button fires `onEdit` callback
- [ ] Delete button fires `onDelete` callback
- [ ] Selected state shows visual highlight
- [ ] No TypeScript errors
- Verify: `test -f frontend/src/components/oracle/UserCard.tsx && echo "UserCard OK"`

STOP if checkpoint fails

---

### Phase 4: Create UserProfileList Component (~30 min)

**Tasks:**

1. Create `frontend/src/components/oracle/UserProfileList.tsx`:

   ```typescript
   interface UserProfileListProps {
     onSelectUser?: (user: OracleUser) => void;
     selectedUserId?: number | null;
   }
   ```

2. Component behavior:
   - Uses `useOracleUsers()` hook to fetch all profiles
   - Search bar at top: filters users by name (client-side filter)
   - "Add Profile" button opens UserForm in create mode
   - Grid layout: responsive card grid (1 col mobile, 2 cols tablet, 3 cols desktop)
   - Each card is a `UserCard` with edit/delete wired to UserForm modal and delete mutation
   - Loading state: skeleton cards or spinner
   - Empty state: friendly message with "Create your first profile" CTA
   - Error state: error message with retry button

3. Internal state:
   - `searchQuery: string` — text filter
   - `editingUser: OracleUser | null` — opens UserForm in edit mode
   - `showCreateForm: boolean` — opens UserForm in create mode
   - `deletingUser: OracleUser | null` — triggers delete confirmation

4. Delete confirmation:
   - Two-step: click delete on card sets `deletingUser`, confirmation dialog confirms
   - Uses `useDeleteOracleUser()` mutation
   - On success: invalidates query, clears `deletingUser`

**Checkpoint:**

- [ ] `UserProfileList.tsx` renders grid of UserCards
- [ ] Search bar filters users by name
- [ ] "Add Profile" button opens UserForm in create mode
- [ ] Edit button on card opens UserForm in edit mode with pre-populated data
- [ ] Delete button triggers confirmation dialog
- [ ] Loading, empty, and error states render correctly
- [ ] No TypeScript errors
- Verify: `test -f frontend/src/components/oracle/UserProfileList.tsx && echo "UserProfileList OK"`

STOP if checkpoint fails

---

### Phase 5: Verify/Fix API Client & Hooks (~20 min)

**Tasks:**

1. **Verify `api.ts`:** The `oracleUsers.create()` and `oracleUsers.update()` methods send the full body via `JSON.stringify(data)`. Since they accept `OracleUserCreate` and `OracleUserUpdate` respectively, and those types now include new fields, no code changes should be needed — just verify the types flow through.

2. **Verify `useOracleUsers.ts`:** The hooks use generic mutation functions that pass through whatever data the caller provides. The type signatures `(data: OracleUserCreate)` and `({ id, data }: { id: number; data: OracleUserUpdate })` will automatically include new fields once types are updated. Verify no code changes needed.

3. **Verify `UserSelector.tsx`:** This component takes `users: OracleUser[]` and displays `user.name` in a dropdown. The expanded `OracleUser` type is backward compatible (all new fields are optional). No changes needed.

4. **Verify `MultiUserSelector.tsx`:** Same as UserSelector — takes `OracleUser[]`, no changes needed.

5. **If any verification fails:** Make the minimal change needed. Most likely, everything passes because:
   - `api.ts` sends whatever the type defines
   - Hooks pass through generic mutation data
   - Display components only read name/id

**Checkpoint:**

- [ ] `api.ts` sends new fields in create/update requests (verified by type inspection)
- [ ] `useOracleUsers.ts` hooks accept new fields in mutation data
- [ ] `UserSelector.tsx` renders without errors with expanded `OracleUser` type
- [ ] `MultiUserSelector.tsx` renders without errors
- Verify: `cd frontend && npx tsc --noEmit` — zero errors

STOP if checkpoint fails

---

### Phase 6: Write Comprehensive Tests (~60 min)

**Tasks:**

1. **Expand `frontend/src/components/oracle/__tests__/UserForm.test.tsx`:**

   Add tests (in addition to existing 11 tests):

   ```
   test_gender_select              — Gender dropdown renders male/female options and updates form state
   test_heart_rate_input           — BPM input accepts valid numbers, rejects out-of-range
   test_heart_rate_validation      — Submitting with BPM < 30 or > 220 shows error
   test_timezone_selectors         — Timezone hour and minute dropdowns render and update form
   test_name_no_digits_validation  — Name containing digits shows validation error
   test_birthday_before_1900       — Birthday before 1900 shows validation error
   test_calendar_picker_replaces_date — CalendarPicker renders instead of native date input
   test_persian_keyboard_toggle    — Clicking keyboard icon shows PersianKeyboard for persian field
   test_persian_keyboard_inserts   — PersianKeyboard character click appends to active persian field
   test_location_selector_replaces — LocationSelector renders instead of separate country/city inputs
   test_edit_mode_new_fields       — Edit mode pre-populates gender, BPM, timezone, coordinates
   test_submit_includes_all_fields — Valid submit includes all 13 fields in onSubmit callback
   ```

   Update the mock translation map with new i18n keys:

   ```typescript
   "oracle.field_gender": "Gender",
   "oracle.field_heart_rate": "Heart Rate (BPM)",
   "oracle.field_timezone": "Timezone",
   "oracle.error_name_no_digits": "Name must not contain digits",
   "oracle.error_birthday_too_old": "Birthday must be after 1900",
   "oracle.error_heart_rate_range": "Heart rate must be between 30 and 220 BPM",
   ```

   Update `existingUser` mock to include new fields:

   ```typescript
   const existingUser: OracleUser = {
     id: 1,
     name: "Alice",
     name_persian: "\u0622\u0644\u06CC\u0633",
     birthday: "1990-01-15",
     mother_name: "Carol",
     mother_name_persian: "\u06A9\u0627\u0631\u0648\u0644",
     country: "US",
     city: "NYC",
     gender: "female",
     heart_rate_bpm: 72,
     timezone_hours: -5,
     timezone_minutes: 0,
     latitude: 40.7128,
     longitude: -74.006,
     created_at: "2024-01-01T00:00:00Z",
   };
   ```

2. **Create `frontend/src/components/oracle/__tests__/UserCard.test.tsx`:**

   ```
   test_renders_user_name          — Card shows user name and persian name
   test_renders_birthday           — Card shows formatted birthday
   test_renders_location           — Card shows country/city
   test_renders_gender_badge       — Gender badge renders with correct text
   test_renders_heart_rate         — BPM indicator renders when heart_rate_bpm set
   test_renders_timezone           — Timezone display renders as "UTC+3:30" format
   test_handles_missing_optional   — Card renders gracefully when optional fields are null/undefined
   test_edit_button_fires_callback — Edit button fires onEdit with user object
   test_delete_button_fires_callback — Delete button fires onDelete with user object
   test_selected_state_highlight   — isSelected=true adds visual highlight class
   ```

3. **Create `frontend/src/components/oracle/__tests__/UserProfileList.test.tsx`:**

   ```
   test_renders_user_cards         — Grid renders a UserCard for each user
   test_search_filters_by_name     — Typing in search filters visible cards
   test_loading_state              — Shows loading indicator while fetching
   test_empty_state                — Shows empty message when no users
   test_add_profile_opens_form     — "Add Profile" button opens UserForm modal
   test_edit_card_opens_form       — Edit action on card opens UserForm with user data
   ```

4. All tests must:
   - Mock `react-i18next` with translation key map
   - Mock `PersianKeyboard`, `CalendarPicker`, `LocationSelector` where appropriate (to test integration points without testing those components' internals)
   - Use `vitest` + `@testing-library/react` + `userEvent`
   - Assert specific DOM elements, callback arguments, and error messages

**Checkpoint:**

- [ ] `UserForm.test.tsx` has 23+ test cases (11 existing + 12 new)
- [ ] `UserCard.test.tsx` has 10+ test cases
- [ ] `UserProfileList.test.tsx` has 6+ test cases
- [ ] All tests pass: `cd frontend && npx vitest run --reporter verbose`
- Verify: `find frontend/src/components/oracle/__tests__ -name "*.test.tsx" | xargs grep -c "it(" | awk -F: '{sum+=$2} END{print "Total tests:", sum}'` — should be 39+

STOP if checkpoint fails

---

### Phase 7: Final Verification (~15 min)

**Tasks:**

1. Run TypeScript compilation:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

2. Run linter:

   ```bash
   cd frontend && npx eslint src/components/oracle/UserForm.tsx src/components/oracle/UserCard.tsx src/components/oracle/UserProfileList.tsx src/types/index.ts
   ```

3. Run formatter:

   ```bash
   cd frontend && npx prettier --check src/components/oracle/UserForm.tsx src/components/oracle/UserCard.tsx src/components/oracle/UserProfileList.tsx
   ```

4. Run all tests:

   ```bash
   cd frontend && npx vitest run
   ```

5. Visual verification (if dev server is running):
   - UserForm opens with all 13 fields
   - PersianKeyboard toggles on Persian name fields
   - CalendarPicker opens for birthday field
   - LocationSelector renders with country dropdown and GPS detect
   - Gender dropdown shows Male/Female
   - Heart rate input accepts numbers
   - Timezone selectors render
   - UserCard displays all info compactly
   - UserProfileList shows grid with search

**Checkpoint:**

- [ ] TypeScript: zero errors
- [ ] ESLint: zero errors
- [ ] Prettier: all files formatted
- [ ] All tests pass
- [ ] No `any` types used (forbidden pattern #5)

STOP if checkpoint fails

---

## TESTS TO WRITE

| Test File                            | Test Name                            | What It Verifies                                 |
| ------------------------------------ | ------------------------------------ | ------------------------------------------------ |
| `__tests__/UserForm.test.tsx`        | `test_gender_select`                 | Gender dropdown renders and updates state        |
| `__tests__/UserForm.test.tsx`        | `test_heart_rate_input`              | BPM input accepts valid numbers                  |
| `__tests__/UserForm.test.tsx`        | `test_heart_rate_validation`         | BPM outside 30-220 shows error on submit         |
| `__tests__/UserForm.test.tsx`        | `test_timezone_selectors`            | Timezone hour/minute dropdowns render and update |
| `__tests__/UserForm.test.tsx`        | `test_name_no_digits_validation`     | Name with digits shows validation error          |
| `__tests__/UserForm.test.tsx`        | `test_birthday_before_1900`          | Pre-1900 birthday shows validation error         |
| `__tests__/UserForm.test.tsx`        | `test_calendar_picker_replaces_date` | CalendarPicker used instead of native date input |
| `__tests__/UserForm.test.tsx`        | `test_persian_keyboard_toggle`       | Keyboard icon toggles PersianKeyboard visibility |
| `__tests__/UserForm.test.tsx`        | `test_persian_keyboard_inserts`      | PersianKeyboard click appends char to field      |
| `__tests__/UserForm.test.tsx`        | `test_location_selector_replaces`    | LocationSelector replaces country/city inputs    |
| `__tests__/UserForm.test.tsx`        | `test_edit_mode_new_fields`          | Edit mode pre-populates all new fields           |
| `__tests__/UserForm.test.tsx`        | `test_submit_includes_all_fields`    | onSubmit receives all 13 fields                  |
| `__tests__/UserCard.test.tsx`        | `test_renders_user_name`             | Shows name and Persian name                      |
| `__tests__/UserCard.test.tsx`        | `test_renders_birthday`              | Shows formatted birthday                         |
| `__tests__/UserCard.test.tsx`        | `test_renders_location`              | Shows country/city                               |
| `__tests__/UserCard.test.tsx`        | `test_renders_gender_badge`          | Gender badge with correct text                   |
| `__tests__/UserCard.test.tsx`        | `test_renders_heart_rate`            | BPM indicator when set                           |
| `__tests__/UserCard.test.tsx`        | `test_renders_timezone`              | UTC offset string                                |
| `__tests__/UserCard.test.tsx`        | `test_handles_missing_optional`      | Renders when optional fields null                |
| `__tests__/UserCard.test.tsx`        | `test_edit_button_fires_callback`    | onEdit called with user                          |
| `__tests__/UserCard.test.tsx`        | `test_delete_button_fires_callback`  | onDelete called with user                        |
| `__tests__/UserCard.test.tsx`        | `test_selected_state_highlight`      | Visual highlight when selected                   |
| `__tests__/UserProfileList.test.tsx` | `test_renders_user_cards`            | Grid renders UserCard per user                   |
| `__tests__/UserProfileList.test.tsx` | `test_search_filters_by_name`        | Search filters visible cards                     |
| `__tests__/UserProfileList.test.tsx` | `test_loading_state`                 | Shows loading indicator                          |
| `__tests__/UserProfileList.test.tsx` | `test_empty_state`                   | Shows empty message                              |
| `__tests__/UserProfileList.test.tsx` | `test_add_profile_opens_form`        | Add button opens UserForm                        |
| `__tests__/UserProfileList.test.tsx` | `test_edit_card_opens_form`          | Edit action opens UserForm with user             |

---

## ACCEPTANCE CRITERIA

- [ ] `OracleUser` type has gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude, created_by fields
- [ ] `OracleUserCreate` type has gender, heart_rate_bpm, timezone_hours, timezone_minutes, latitude, longitude fields
- [ ] UserForm renders 13 fields organized in 4 sections
- [ ] PersianKeyboard integrates with name_persian and mother_name_persian fields (toggle, insert, backspace, close)
- [ ] CalendarPicker replaces native date input for birthday (dual Gregorian/Jalaali)
- [ ] LocationSelector replaces country/city inputs (GPS detect + dropdown + coordinates)
- [ ] Gender dropdown works (male/female/empty)
- [ ] Heart rate BPM input with validation (30-220)
- [ ] Timezone selectors work (hours: -12 to +14, minutes: 0/15/30/45)
- [ ] Name validation rejects digits
- [ ] Birthday validation rejects dates before 1900
- [ ] UserCard renders compact profile with all fields
- [ ] UserProfileList renders searchable grid of UserCards
- [ ] All 28+ tests pass
- [ ] Zero TypeScript errors, zero ESLint errors
- [ ] No `any` types used anywhere in new/modified code
- Verify all:
  ```bash
  test -f frontend/src/components/oracle/UserCard.tsx && \
  test -f frontend/src/components/oracle/UserProfileList.tsx && \
  test -f frontend/src/components/oracle/__tests__/UserCard.test.tsx && \
  test -f frontend/src/components/oracle/__tests__/UserProfileList.test.tsx && \
  grep -q "gender" frontend/src/types/index.ts && \
  grep -q "heart_rate_bpm" frontend/src/types/index.ts && \
  grep -q "CalendarPicker" frontend/src/components/oracle/UserForm.tsx && \
  grep -q "PersianKeyboard" frontend/src/components/oracle/UserForm.tsx && \
  grep -q "LocationSelector" frontend/src/components/oracle/UserForm.tsx && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                                          | Expected Behavior                                                                                                                                                                                                 |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Session 3 API not yet deployed                                    | Form renders with all fields; create/update fail with network error displayed via `serverError` prop. PersianKeyboard, CalendarPicker, LocationSelector all work standalone since they're client-side components. |
| GPS geolocation denied by user                                    | LocationSelector shows error message and falls back to manual country dropdown. Form still submittable without coordinates (latitude/longitude remain undefined).                                                 |
| API returns OracleUser without new fields (pre-Session-3 backend) | All new fields are optional (`?`), so TypeScript handles gracefully. UserForm shows empty/default values for missing fields. UserCard omits badges/indicators for undefined fields.                               |
| User enters digits in name field                                  | Validation fires on submit: "Name must not contain digits" error displayed on the name field. Submit blocked.                                                                                                     |
| User enters BPM of 0                                              | Validation fires on submit: "Heart rate must be between 30 and 220 BPM" error displayed. Submit blocked.                                                                                                          |
| CalendarPicker Jalaali conversion error                           | CalendarPicker handles this internally with fallback to Gregorian. No crash propagated to UserForm.                                                                                                               |
| PersianKeyboard opened while another is active                    | Only one keyboard at a time (controlled by `activeKeyboard` state). Opening a new one closes the previous.                                                                                                        |

---

## DESIGN DECISIONS

| Decision                              | Choice                                     | Rationale                                                                                                                                                                                      |
| ------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PersianKeyboard integration approach  | Toggle per-field, not global               | Each Persian field needs its own toggle button. The keyboard positions itself relative to the parent field, so it appears contextually near the input.                                         |
| CalendarPicker vs native date input   | Replace with CalendarPicker                | CalendarPicker already supports Jalaali calendar, which is required for Persian users. Native `<input type="date">` only supports Gregorian.                                                   |
| LocationSelector vs separate inputs   | Replace country/city with LocationSelector | LocationSelector captures coordinates (needed by Session 6 framework bridge), provides GPS auto-detect, and handles country/city in a single component. Reduces form clutter.                  |
| Timezone input approach               | Two dropdowns (hours + minutes)            | Real timezones have fractional offsets (India +5:30, Nepal +5:45). A single dropdown would need 50+ options. Two dropdowns (hours: 27 options, minutes: 4 options) are cleaner.                |
| Form section organization             | 4 sections with visual dividers            | 13 fields in one flat list is overwhelming. Grouping by category (Identity, Family, Location, Profile) improves scannability.                                                                  |
| UserCard creation                     | New component                              | Reusable for UserProfileList grid and potentially for multi-user comparison views (Session 13+).                                                                                               |
| UserProfileList as separate component | New component                              | Separates list management (search, grid layout, CRUD actions) from individual card display. Follows existing pattern of UserSelector (list/select) being separate from UserForm (create/edit). |

---

## HANDOFF

**Created:**

- `frontend/src/components/oracle/UserCard.tsx` (compact profile card)
- `frontend/src/components/oracle/UserProfileList.tsx` (searchable card grid)
- `frontend/src/components/oracle/__tests__/UserCard.test.tsx` (10+ tests)
- `frontend/src/components/oracle/__tests__/UserProfileList.test.tsx` (6+ tests)

**Modified:**

- `frontend/src/types/index.ts` (OracleUser: 7 new fields, OracleUserCreate: 6 new fields)
- `frontend/src/components/oracle/UserForm.tsx` (rewrite: 13 fields, PersianKeyboard + CalendarPicker + LocationSelector integrations, enhanced validation)
- `frontend/src/components/oracle/__tests__/UserForm.test.tsx` (12 new tests for new fields + integrations)
- `frontend/src/services/api.ts` (verified — no code changes needed if types flow through)
- `frontend/src/hooks/useOracleUsers.ts` (verified — no code changes needed)

**Next session needs:**

- **Session 5 (API Key Dashboard & Settings UI)** depends on:
  - User profile management UI working (this session)
  - System user CRUD endpoints from Session 3
  - User can view their own account settings
- **Session 19-25 (Frontend Core block)** depends on:
  - All profile components (UserForm, UserCard, UserProfileList) being production-ready
  - TypeScript types matching backend API response models
  - Component integrations (PersianKeyboard, CalendarPicker, LocationSelector) tested and stable
