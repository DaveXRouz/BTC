# SESSION 20 SPEC — Oracle Main Page

**Block:** Frontend Core (Sessions 19-25)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 19 (layout & navigation), Sessions 14-16 (all 5 reading type forms + API endpoints), Session 17 (reading history), Session 18 (feedback UI)

---

## TL;DR

- Rewrite `Oracle.tsx` from a single-form layout to a two-column page with user selector + reading type tabs + dynamic form + loading animation + results display
- Create `ReadingTypeSelector.tsx` — segmented control with 5 tabs (Time, Name, Question, Daily, Multi-user) that drives the dynamic form area
- Rewrite `OracleConsultationForm.tsx` from a monolithic sign-based form to a thin coordinator that renders the correct sub-form component per reading type
- Create `LoadingAnimation.tsx` — pulsing green orb with WebSocket progress text during reading generation
- All individual reading form components already exist from Sessions 14-16 (`TimeReadingForm`, `NameReadingForm`, `QuestionReadingForm`, `DailyReadingCard`, `MultiUserReadingDisplay`); this session composes them into a unified page
- Add `useReadingProgress` hook for WebSocket progress tracking during any reading type
- 24 tests across 4 test files

---

## OBJECTIVES

1. **Rewrite `Oracle.tsx`** — Two-column responsive layout: left panel (user profile selector, reading type tabs) + main area (dynamic form, loading animation, results). Mobile: stacks vertically.
2. **Create `ReadingTypeSelector.tsx`** — 5-tab segmented control: Time | Name | Question | Daily | Multi-user. Active tab drives which form renders. Accessible with `role="tablist"` + `aria-selected`.
3. **Rewrite `OracleConsultationForm.tsx`** — Coordinator component that receives `readingType` prop and renders the correct child form (`TimeReadingForm`, `NameReadingForm`, `QuestionReadingForm`, `DailyReadingCard` auto-view, or multi-user flow).
4. **Create `LoadingAnimation.tsx`** — Pulsing emerald orb animation with WebSocket-driven progress text ("Loading profile..." / "Generating reading..." / "Consulting AI..." / "Done"). Centered in the form area during submission.
5. **Create `useReadingProgress` hook** — Subscribes to WebSocket reading progress events, tracks current step/total/message, resets between readings.
6. **Wire submit → loading → results flow** — Submit triggers LoadingAnimation overlay, WebSocket updates progress text, completion scrolls to results display (existing `ReadingResults` component).
7. **Add i18n translations** — New keys for reading type labels, loading messages, and progress steps in EN and FA.
8. **Write 24 tests** covering page layout, tab switching, form rendering, loading animation, and progress tracking.

---

## PREREQUISITES

- [ ] Session 19 completed — Layout with sidebar navigation, routing, theme system. Oracle page routed at `/oracle`.
- [ ] Session 14 completed — `TimeReadingForm.tsx` exists, `POST /api/oracle/readings` endpoint with `reading_type: "time"`.
- [ ] Session 15 completed — `NameReadingForm.tsx` and `QuestionReadingForm.tsx` exist, reading types "name" and "question" on the unified endpoint.
- [ ] Session 16 completed — `DailyReadingCard.tsx`, `MultiUserReadingDisplay.tsx`, `CompatibilityMeter.tsx` exist. Reading types "daily" and "multi" on the unified endpoint.
- [ ] Session 17 completed — `ReadingHistory.tsx` rewritten with card grid, `ReadingCard.tsx`, `ReadingDetail.tsx`.
- [ ] Session 18 completed — `ReadingFeedback.tsx` and `StarRating.tsx` integrated into `ReadingResults.tsx`.

Verification:

```bash
# Individual reading form components exist
test -f frontend/src/components/oracle/TimeReadingForm.tsx && echo "TimeReadingForm OK"
test -f frontend/src/components/oracle/NameReadingForm.tsx && echo "NameReadingForm OK"
test -f frontend/src/components/oracle/QuestionReadingForm.tsx && echo "QuestionReadingForm OK"
test -f frontend/src/components/oracle/DailyReadingCard.tsx && echo "DailyReadingCard OK"
test -f frontend/src/components/oracle/MultiUserReadingDisplay.tsx && echo "MultiUserReadingDisplay OK"

# Layout and results
test -f frontend/src/components/Layout.tsx && echo "Layout OK"
test -f frontend/src/components/oracle/ReadingResults.tsx && echo "ReadingResults OK"
test -f frontend/src/components/oracle/ReadingFeedback.tsx && echo "ReadingFeedback OK"

# Hooks
test -f frontend/src/hooks/useOracleReadings.ts && echo "Hooks OK"
test -f frontend/src/hooks/useWebSocket.ts && echo "WebSocket hook OK"
```

---

## EXISTING STATE ANALYSIS

### What EXISTS (Verified in Codebase)

| Component             | File                                                                    | Current State                                                                                                                                                                                                                       |
| --------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Oracle page           | `frontend/src/pages/Oracle.tsx` (188 lines)                             | Monolithic: user profile section + OracleConsultationForm + ReadingResults. No reading type tabs, no two-column layout. Uses legacy form only.                                                                                      |
| Consultation form     | `frontend/src/components/oracle/OracleConsultationForm.tsx` (149 lines) | Single form: question textarea + date picker + sign type selector + location selector + submit button. Does NOT use the framework-based reading forms from Sessions 14-16.                                                          |
| Reading results       | `frontend/src/components/oracle/ReadingResults.tsx` (79 lines)          | Tabbed display: Summary / Details / History. Already functional.                                                                                                                                                                    |
| Multi-user selector   | `frontend/src/components/oracle/MultiUserSelector.tsx` (204 lines)      | Primary + secondary user selection with chips. Reuse as-is for multi-user reading type.                                                                                                                                             |
| User form             | `frontend/src/components/oracle/UserForm.tsx`                           | Modal form for creating/editing oracle user profiles. Keep as-is.                                                                                                                                                                   |
| Time reading form     | `frontend/src/components/oracle/TimeReadingForm.tsx`                    | Created by Session 14: hour/minute/second dropdowns, "Use current time" button, CalendarPicker. Calls `POST /api/oracle/readings` with `reading_type: "time"`.                                                                      |
| Name reading form     | `frontend/src/components/oracle/NameReadingForm.tsx`                    | Created by Session 15: text input with Persian keyboard, "use profile name" button.                                                                                                                                                 |
| Question reading form | `frontend/src/components/oracle/QuestionReadingForm.tsx`                | Created by Session 15: textarea with character counter, script detection badge.                                                                                                                                                     |
| Daily reading card    | `frontend/src/components/oracle/DailyReadingCard.tsx`                   | Created by Session 16: auto-fetches today's reading, shows daily insights.                                                                                                                                                          |
| Multi-user display    | `frontend/src/components/oracle/MultiUserReadingDisplay.tsx`            | Created by Session 16: individual readings tabs + compatibility grid + group analysis.                                                                                                                                              |
| WebSocket hook        | `frontend/src/hooks/useWebSocket.ts` (33 lines)                         | `useWebSocket(event, handler)` — subscribes to typed events. `useWebSocketConnection()` — connect/disconnect.                                                                                                                       |
| Oracle readings hooks | `frontend/src/hooks/useOracleReadings.ts` (39 lines)                    | Sessions 14-16 added: `useSubmitTimeReading()`, `useSubmitName()`, `useSubmitQuestion()`, `useDailyReading()`, `useGenerateDailyReading()`, `useSubmitMultiUserReading()`, `useReadingHistory()`.                                   |
| API client            | `frontend/src/services/api.ts`                                          | Sessions 14-16 added: `oracle.timeReading()`, `oracle.dailyReading()`, `oracle.getDailyReading()`, `oracle.multiUserFrameworkReading()`. Legacy: `oracle.reading()`, `oracle.question()`, `oracle.name()`, `oracle.daily()`.        |
| TS types              | `frontend/src/types/index.ts` (411 lines)                               | Session 14 added: `TimeReadingRequest`, `FrameworkReadingResponse`, `ReadingProgressEvent`, `AIInterpretationSections`, `FrameworkConfidence`, `PatternDetected`, `FrameworkNumerologyData`. Session 16 added: daily + multi types. |
| i18n translations     | `frontend/src/locales/en.json` (190 lines)                              | Has `oracle.*` section. Missing: reading type tab labels, loading/progress messages.                                                                                                                                                |

### What Does NOT Exist (Must Create)

| Component             | File                                                     | Purpose                                            |
| --------------------- | -------------------------------------------------------- | -------------------------------------------------- |
| Reading type selector | `frontend/src/components/oracle/ReadingTypeSelector.tsx` | NEW — 5-tab segmented control driving dynamic form |
| Loading animation     | `frontend/src/components/oracle/LoadingAnimation.tsx`    | NEW — Pulsing orb + progress text                  |
| Reading progress hook | `frontend/src/hooks/useReadingProgress.ts`               | NEW — WebSocket progress state management          |

---

## KEY DESIGN DECISIONS

### 1. Two-Column Page Layout

The Oracle page uses a responsive two-column layout matching the master spec's description ("Left panel: User selector + reading type selector. Center: Reading form"):

```
Desktop (md+):
┌──────────────────┬─────────────────────────────────────┐
│  LEFT PANEL      │  MAIN AREA                          │
│  (320px fixed)   │  (flex-1)                           │
│                  │                                     │
│  ┌────────────┐  │  ┌─────────────────────────────┐    │
│  │ User       │  │  │ Dynamic Form               │    │
│  │ Selector   │  │  │ (TimeReading / Name / etc.) │    │
│  └────────────┘  │  └─────────────────────────────┘    │
│                  │                                     │
│  ┌────────────┐  │  ┌─────────────────────────────┐    │
│  │ Reading    │  │  │ Loading Animation           │    │
│  │ Type Tabs  │  │  │ (shown during generation)   │    │
│  │ ─────────  │  │  └─────────────────────────────┘    │
│  │ ● Time     │  │                                     │
│  │ ○ Name     │  │  ┌─────────────────────────────┐    │
│  │ ○ Question │  │  │ Reading Results              │    │
│  │ ○ Daily    │  │  │ (Summary / Details / History)│    │
│  │ ○ Multi    │  │  └─────────────────────────────┘    │
│  └────────────┘  │                                     │
└──────────────────┴─────────────────────────────────────┘

Mobile (< md):
┌─────────────────────────────────────┐
│  User Selector (collapsed row)      │
├─────────────────────────────────────┤
│  Reading Type Tabs (horizontal)     │
├─────────────────────────────────────┤
│  Dynamic Form                       │
├─────────────────────────────────────┤
│  Loading / Results                  │
└─────────────────────────────────────┘
```

On desktop: left panel is `w-80` (320px), sticky via `md:sticky md:top-6`. Main area fills the rest.
On mobile: everything stacks vertically. Reading type tabs become a horizontal scrollable row.

### 2. Reading Type as URL Query Parameter

The selected reading type persists in the URL as a query parameter: `/oracle?type=time`. This enables:

- Direct links to specific reading types
- Browser back/forward preserves type selection
- Bookmarkable reading flows

Use `useSearchParams()` from react-router-dom. Default to `"time"` if no query parameter or invalid value.

### 3. Thin Coordinator Pattern (Not Monolithic)

`OracleConsultationForm.tsx` becomes a thin coordinator:

- Receives `readingType`, `userId`, `userName`, `selectedUsers` props
- Renders the appropriate child form via a switch statement:
  - `"time"` → `<TimeReadingForm>` (Session 14)
  - `"name"` → `<NameReadingForm>` (Session 15)
  - `"question"` → `<QuestionReadingForm>` (Session 15)
  - `"daily"` → `<DailyReadingCard>` (Session 16)
  - `"multi"` → multi-user flow using `<MultiUserReadingDisplay>` (Session 16)
- Each child form handles its own submission via its existing hook (e.g., `useSubmitTimeReading`)
- All child forms call back via `onResult(response)` prop
- The coordinator does NOT manage form state — each form is self-contained
- This avoids duplicating form logic that already exists in the Session 14-16 components

### 4. Response Normalization

All framework-based reading types (time, name, question, daily) produce a `FrameworkReadingResponse` (from Session 14). The existing `ReadingResults` component expects `ConsultationResult` which wraps the older `OracleReading` shape. A `normalizeFrameworkResult()` utility bridges the gap:

```typescript
function normalizeFrameworkResult(
  response: FrameworkReadingResponse,
  type: "reading" | "name" | "question",
): ConsultationResult;
```

This maps `FrameworkReadingResponse` fields (fc60_stamp, numerology, moon, ganzhi, patterns, ai_interpretation sections, confidence) into the `OracleReading` / `NameReading` / `QuestionResponse` shapes that `ReadingResults` already knows how to render.

For multi-user results: `MultiUserReadingDisplay` is self-contained and renders directly (it doesn't go through `ReadingResults`).

### 5. Loading Animation Design

The loading animation replaces the form area during submission:

- Centered pulsing emerald orb (CSS animations only — no animation library)
- Below orb: step text from WebSocket progress events
- Progress bar showing step N of total
- Cancel button to abort the reading
- Fallback: if WebSocket has no events, auto-cycle through generic messages every 2 seconds

### 6. Preserve Existing Oracle Functionality

The current `OracleConsultationForm` behavior (question textarea, sign type selector, location selector) was the only reading flow before Session 14. Now that Sessions 14-16 created dedicated forms for each type, the old monolithic form is fully replaced. But all the sub-components it used (`PersianKeyboard`, `CalendarPicker`, `SignTypeSelector`, `LocationSelector`) are preserved — they're imported by the individual form components.

### 7. UserForm Modal Unchanged

The `UserForm` modal for creating/editing profiles is independent of reading type. It remains triggered by "Add New Profile" / "Edit Profile" buttons in the user selector area.

---

## FILES TO CREATE

| File                                                                       | Purpose                                   |
| -------------------------------------------------------------------------- | ----------------------------------------- |
| `frontend/src/components/oracle/ReadingTypeSelector.tsx`                   | 5-tab segmented control for reading types |
| `frontend/src/components/oracle/LoadingAnimation.tsx`                      | Pulsing orb + progress text animation     |
| `frontend/src/hooks/useReadingProgress.ts`                                 | WebSocket progress state hook             |
| `frontend/src/components/oracle/__tests__/ReadingTypeSelector.test.tsx`    | 6 tests                                   |
| `frontend/src/components/oracle/__tests__/LoadingAnimation.test.tsx`       | 4 tests                                   |
| `frontend/src/components/oracle/__tests__/OracleConsultationForm.test.tsx` | 8 tests                                   |
| `frontend/src/pages/__tests__/Oracle.test.tsx`                             | 6 tests                                   |

## FILES TO MODIFY

| File                                                        | Current Lines | Action                                                                  |
| ----------------------------------------------------------- | ------------- | ----------------------------------------------------------------------- |
| `frontend/src/pages/Oracle.tsx`                             | 188           | REWRITE — Two-column layout with reading type tabs                      |
| `frontend/src/components/oracle/OracleConsultationForm.tsx` | 149           | REWRITE — Thin coordinator rendering appropriate form per type          |
| `frontend/src/types/index.ts`                               | 411           | MODIFY — Add `"reading_progress"` to EventType, add `ReadingType` alias |
| `frontend/src/locales/en.json`                              | 190           | MODIFY — Add ~16 reading type + loading i18n keys                       |
| `frontend/src/locales/fa.json`                              | ~190          | MODIFY — Add ~16 Persian translations for new keys                      |

## FILES TO DELETE

- None. Existing sub-components (`SignTypeSelector.tsx`, `LocationSelector.tsx`, `CalendarPicker.tsx`, `PersianKeyboard.tsx`) remain — they are used by individual reading form components.

---

## IMPLEMENTATION PHASES

### Phase 1: ReadingTypeSelector Component

**Goal:** Create the 5-tab segmented control that drives the dynamic form area.

**Create `frontend/src/components/oracle/ReadingTypeSelector.tsx`:**

```typescript
import { useTranslation } from "react-i18next";

export type ReadingType = "time" | "name" | "question" | "daily" | "multi";

interface ReadingTypeSelectorProps {
  value: ReadingType;
  onChange: (type: ReadingType) => void;
  disabled?: boolean; // Disable during loading
}
```

**Implementation:**

1. Define the 5 reading types as a constant array with icon + label key:

   ```typescript
   const READING_TYPES: { type: ReadingType; labelKey: string; icon: React.ReactNode }[] = [
     { type: "time", labelKey: "oracle.type_time", icon: /* clock SVG */ },
     { type: "name", labelKey: "oracle.type_name", icon: /* user SVG */ },
     { type: "question", labelKey: "oracle.type_question", icon: /* question SVG */ },
     { type: "daily", labelKey: "oracle.type_daily", icon: /* sun SVG */ },
     { type: "multi", labelKey: "oracle.type_multi", icon: /* users SVG */ },
   ];
   ```

2. Render as a vertical list on desktop (inside left panel), horizontal scrollable row on mobile:
   - Each item: icon + label text
   - Active item: `bg-nps-accent/10 text-[var(--nps-accent)]` + left border `border-l-2 border-[var(--nps-accent)]` (RTL: `rtl:border-l-0 rtl:border-r-2`)
   - Inactive: `text-[var(--nps-text-dim)] hover:bg-[var(--nps-bg-hover)]`
   - Disabled: `opacity-50 cursor-not-allowed pointer-events-none`

3. Accessibility:
   - Container: `role="tablist"` + `aria-label={t("oracle.reading_type")}`
   - Each item: `role="tab"` + `aria-selected={isActive}` + `aria-controls="oracle-form-panel"`
   - Keyboard: items are `<button>` elements (native keyboard support)

4. Icons: inline SVG, 20x20, `stroke="currentColor"` (heroicons outline style):
   - Time: clock face with hands
   - Name: person outline
   - Question: question mark in circle
   - Daily: sun with rays
   - Multi: two people

5. Responsive: On mobile (`md:` breakpoint), switch from vertical `flex-col` to horizontal `flex-row overflow-x-auto`. Labels abbreviated or hidden below `sm:`.

### STOP CHECKPOINT 1

- [ ] `ReadingTypeSelector.tsx` renders 5 items with icons and labels
- [ ] Active item has emerald accent styling with left border
- [ ] Clicking a tab calls `onChange` with the correct type
- [ ] `disabled` prop prevents interaction
- [ ] Accessible: `role="tablist"`, `role="tab"`, `aria-selected`
- [ ] Responsive: vertical list (desktop), horizontal scroll (mobile)

---

### Phase 2: LoadingAnimation Component

**Goal:** Create the pulsing orb animation shown during reading generation.

**Create `frontend/src/components/oracle/LoadingAnimation.tsx`:**

```typescript
interface LoadingAnimationProps {
  step: number;
  total: number;
  message: string;
  onCancel?: () => void;
}
```

**Implementation:**

1. Centered container with flex column alignment:

   ```tsx
   <div className="flex flex-col items-center justify-center py-12" aria-live="polite">
   ```

2. Pulsing orb (three concentric circles):

   ```tsx
   <div className="relative w-24 h-24 mx-auto mb-6">
     {/* Outer glow ring — slow ping */}
     <div className="absolute inset-0 rounded-full bg-[var(--nps-accent)]/20 animate-ping" />
     {/* Middle ring — steady pulse */}
     <div className="absolute inset-2 rounded-full bg-[var(--nps-accent)]/40 animate-pulse" />
     {/* Core — solid emerald */}
     <div className="absolute inset-4 rounded-full bg-[var(--nps-accent)] shadow-lg shadow-[var(--nps-accent)]/30" />
   </div>
   ```

3. Progress message text: Centered paragraph below orb with `transition-opacity` for smooth text changes.

4. Progress bar:

   ```tsx
   <div className="w-48 h-1 bg-[var(--nps-border)] rounded-full mx-auto mt-4">
     <div
       className="h-full bg-[var(--nps-accent)] rounded-full transition-all duration-500"
       style={{ width: `${(step / total) * 100}%` }}
     />
   </div>
   ```

5. Step counter: `<p className="text-xs text-[var(--nps-text-dim)] mt-2">{t("oracle.progress_step", { step, total })}</p>`

6. Cancel button: Small text link styled button below the progress bar. Visible only when `onCancel` is provided. `<button onClick={onCancel} className="mt-4 text-xs text-[var(--nps-text-dim)] hover:text-[var(--nps-accent)] underline">{t("oracle.loading_cancel")}</button>`

### STOP CHECKPOINT 2

- [ ] `LoadingAnimation.tsx` renders pulsing green orb
- [ ] Progress text updates with step message
- [ ] Progress bar width reflects step/total ratio
- [ ] Cancel button visible when `onCancel` provided
- [ ] `aria-live="polite"` on container for screen reader announcements
- [ ] Animation uses CSS only (no JS animation library)

---

### Phase 3: useReadingProgress Hook

**Goal:** Create a hook that tracks WebSocket progress events during reading generation.

**Create `frontend/src/hooks/useReadingProgress.ts`:**

```typescript
import { useState, useCallback, useEffect, useRef } from "react";
import { useWebSocket } from "./useWebSocket";
import type { EventType } from "@/types";

interface ReadingProgress {
  step: number;
  total: number;
  message: string;
  readingType: string;
  isActive: boolean;
}

const INITIAL_PROGRESS: ReadingProgress = {
  step: 0,
  total: 0,
  message: "",
  readingType: "",
  isActive: false,
};

export function useReadingProgress(): {
  progress: ReadingProgress;
  startProgress: (readingType: string) => void;
  resetProgress: () => void;
};
```

**Implementation:**

1. Internal state: `const [progress, setProgress] = useState<ReadingProgress>(INITIAL_PROGRESS);`

2. WebSocket subscription via existing `useWebSocket` hook:

   ```typescript
   useWebSocket("reading_progress" as EventType, (data) => {
     if (!activeRef.current) return;
     setProgress((prev) => ({
       ...prev,
       step: (data.step as number) ?? prev.step,
       total: (data.total as number) ?? prev.total,
       message: (data.message as string) ?? prev.message,
     }));
   });
   ```

   Use a ref (`activeRef`) to avoid stale closure issues with the `isActive` flag.

3. `startProgress(readingType: string)`:
   - Sets `isActive: true`, `readingType`, resets step/total/message
   - Sets `activeRef.current = true`

4. `resetProgress()`:
   - Sets state to `INITIAL_PROGRESS`
   - Sets `activeRef.current = false`

5. Auto-deactivation: When `step === total && total > 0`, schedule a 500ms timeout to set `isActive: false` (allows the final progress message to display briefly before the form reappears).

6. Fallback for no WebSocket: If no progress events arrive within 3 seconds of `startProgress()`, the `LoadingAnimation` component handles its own fallback by auto-cycling generic messages. This hook doesn't need its own fallback.

### STOP CHECKPOINT 3

- [ ] `useReadingProgress` hook compiles without TypeScript errors
- [ ] Returns `progress`, `startProgress`, `resetProgress`
- [ ] Subscribes to WebSocket `"reading_progress"` events
- [ ] `isActive` flag correctly tracks active/inactive state
- [ ] Auto-deactivates when step reaches total after brief delay
- [ ] Uses ref to avoid stale closure in WebSocket handler

---

### Phase 4: OracleConsultationForm Rewrite

**Goal:** Replace the monolithic form with a thin coordinator that renders the correct sub-form per reading type.

**Rewrite `frontend/src/components/oracle/OracleConsultationForm.tsx`:**

New props interface:

```typescript
import type { ReadingType } from "./ReadingTypeSelector";
import type { SelectedUsers, ConsultationResult } from "@/types";

interface OracleConsultationFormProps {
  readingType: ReadingType;
  userId: number;
  userName: string;
  selectedUsers: SelectedUsers | null;
  onResult: (result: ConsultationResult) => void;
  onLoadingChange: (isLoading: boolean) => void;
}
```

**Implementation:**

1. Render the correct child form based on `readingType`:

   ```typescript
   switch (readingType) {
     case "time":
       return (
         <TimeReadingForm
           userId={userId}
           userName={userName}
           onResult={(response) => onResult(normalizeFrameworkResult(response, "reading"))}
           onProgress={handleProgress}
         />
       );
     case "name":
       return (
         <NameReadingForm
           userId={userId}
           userName={userName}
           onResult={(response) => onResult(normalizeFrameworkResult(response, "name"))}
         />
       );
     case "question":
       return (
         <QuestionReadingForm
           userId={userId}
           userName={userName}
           onResult={(response) => onResult(normalizeFrameworkResult(response, "question"))}
         />
       );
     case "daily":
       return <DailyReadingCard userId={userId} />;
     case "multi":
       return (
         <MultiUserReadingFlow
           userId={userId}
           selectedUsers={selectedUsers}
           onResult={(response) => onResult({ type: "multi", data: response })}
         />
       );
   }
   ```

2. **`normalizeFrameworkResult()` utility** — Maps `FrameworkReadingResponse` to `ConsultationResult`:

   ```typescript
   function normalizeFrameworkResult(
     response: FrameworkReadingResponse,
     type: "reading" | "name" | "question",
   ): ConsultationResult {
     if (type === "reading") {
       const oracleReading: OracleReading = {
         fc60: null,
         numerology: response.numerology
           ? {
               life_path: response.numerology.life_path.number,
               day_vibration: response.numerology.personal_day,
               personal_year: response.numerology.personal_year,
               personal_month: response.numerology.personal_month,
               personal_day: response.numerology.personal_day,
               interpretation: response.ai_interpretation?.core_identity ?? "",
             }
           : null,
         zodiac: null,
         chinese: null,
         moon: response.moon as Record<string, string> | null,
         angel: null,
         chaldean: null,
         ganzhi: response.ganzhi as Record<string, string> | null,
         fc60_extended: null,
         synchronicities: response.patterns.map((p) => p.message ?? p.type),
         ai_interpretation: response.ai_interpretation?.full_text ?? null,
         summary: response.ai_interpretation?.message ?? "",
         generated_at: response.created_at,
       };
       return { type: "reading", data: oracleReading };
     }
     // For name and question, similar mapping...
     // (name maps to NameReading, question maps to QuestionResponse)
   }
   ```

   This function lives in the same file — it's specific to form coordination and not needed elsewhere.

3. **Multi-user flow inline component**: When `readingType === "multi"`, render a small wrapper that:
   - Checks `selectedUsers` has >= 2 total users (primary + secondary)
   - If < 2: shows `t("oracle.multi_need_users")` warning message
   - If >= 2: renders submit button that calls `useSubmitMultiUserReading()` and then renders `MultiUserReadingDisplay` with results

4. **Daily card is self-contained**: When `readingType === "daily"`, `DailyReadingCard` handles everything internally (fetches data, displays reading, handles loading state). No `onResult` needed — the card IS the results display for daily readings.

5. **`onLoadingChange` passthrough**: Each child form manages its own loading state internally. The coordinator observes loading by:
   - For time/name/question: wrapping `onResult` to call `onLoadingChange(false)` on result, and detecting mutation start via the child form's built-in loading state
   - For daily: `DailyReadingCard` handles loading internally
   - For multi: submit button triggers `onLoadingChange(true)`, completion triggers `onLoadingChange(false)`

### STOP CHECKPOINT 4

- [ ] `OracleConsultationForm` renders `TimeReadingForm` when `readingType="time"`
- [ ] Renders `NameReadingForm` when `readingType="name"`
- [ ] Renders `QuestionReadingForm` when `readingType="question"`
- [ ] Renders `DailyReadingCard` when `readingType="daily"`
- [ ] Renders multi-user flow when `readingType="multi"` with user count validation
- [ ] `normalizeFrameworkResult()` maps framework response to ConsultationResult shapes
- [ ] Each child form's result is normalized before passing to `onResult`
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`

---

### Phase 5: Oracle.tsx Rewrite

**Goal:** Rewrite the Oracle page with two-column layout, reading type tabs, and integrated flow.

**Rewrite `frontend/src/pages/Oracle.tsx`:**

```typescript
import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  ReadingTypeSelector,
  ReadingType,
} from "@/components/oracle/ReadingTypeSelector";
import { OracleConsultationForm } from "@/components/oracle/OracleConsultationForm";
import { LoadingAnimation } from "@/components/oracle/LoadingAnimation";
import { ReadingResults } from "@/components/oracle/ReadingResults";
import { MultiUserSelector } from "@/components/oracle/MultiUserSelector";
import { UserForm } from "@/components/oracle/UserForm";
import {
  useOracleUsers,
  useCreateOracleUser,
  useUpdateOracleUser,
  useDeleteOracleUser,
} from "@/hooks/useOracleUsers";
import { useReadingProgress } from "@/hooks/useReadingProgress";
import type {
  OracleUserCreate,
  SelectedUsers,
  ConsultationResult,
} from "@/types";

const SELECTED_USER_KEY = "nps_selected_oracle_user";
const VALID_TYPES: ReadingType[] = [
  "time",
  "name",
  "question",
  "daily",
  "multi",
];

export default function Oracle() {
  // ...
}
```

**Key state:**

```typescript
// Reading type from URL query param
const [searchParams, setSearchParams] = useSearchParams();
const rawType = searchParams.get("type");
const readingType: ReadingType = VALID_TYPES.includes(rawType as ReadingType)
  ? (rawType as ReadingType)
  : "time";

// User selection (preserved from current Oracle.tsx)
const { data: users = [], isLoading: usersLoading } = useOracleUsers();
const createUser = useCreateOracleUser();
const updateUser = useUpdateOracleUser();
const deleteUser = useDeleteOracleUser();
const [selectedUsers, setSelectedUsers] = useState<SelectedUsers | null>(null);
const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
const [formError, setFormError] = useState<string | null>(null);

// Reading state
const [consultationResult, setConsultationResult] =
  useState<ConsultationResult | null>(null);
const { progress, startProgress, resetProgress } = useReadingProgress();
const [isLoading, setIsLoading] = useState(false);
const resultsRef = useRef<HTMLDivElement>(null);
```

**Implementation details:**

1. **User profile selection** — Keep existing user selection logic from current `Oracle.tsx`:
   - localStorage persistence of primary user via `SELECTED_USER_KEY`
   - Restore persisted user on load
   - Clear selection if primary user no longer exists
   - Create/update/delete via mutation hooks

2. **Reading type from URL** — `useSearchParams()` reads `?type=time` from URL. Validate against `VALID_TYPES` array, default to `"time"` if invalid/missing. When user clicks a tab: `setSearchParams({ type: newType })`.

3. **`export default` required** — Session 19's lazy loading requires default exports from page components.

4. **Left panel content:**
   - Card 1: User profile selector
     - Primary user dropdown + "Add New" + "Edit" buttons
     - Selected user info (birthday, country, city)
     - When `readingType === "multi"`: full `MultiUserSelector` with secondary user chips
     - When other types: compact primary-only dropdown
   - Card 2: Reading type selector
     - `<ReadingTypeSelector value={readingType} onChange={handleTypeChange} disabled={isLoading} />`

5. **Main area content:**
   - Card 1: Dynamic form / Loading
     - Title: `t("oracle.type_${readingType}_title")`
     - If `isLoading && progress.isActive`: show `<LoadingAnimation>`
     - Else if `primaryUser` (or daily type): show `<OracleConsultationForm>`
     - Else: show `t("oracle.select_to_begin")` prompt
   - Card 2: Results (always rendered)
     - `<ReadingResults result={consultationResult} />`
     - `ref={resultsRef}` for scroll-to behavior

6. **Result handler with scroll:**

   ```typescript
   function handleResult(result: ConsultationResult) {
     setConsultationResult(result);
     setIsLoading(false);
     resetProgress();
     requestAnimationFrame(() => {
       resultsRef.current?.scrollIntoView({
         behavior: "smooth",
         block: "start",
       });
     });
   }
   ```

7. **Type change handler:**

   ```typescript
   function handleTypeChange(type: ReadingType) {
     setSearchParams({ type });
     setConsultationResult(null); // Clear previous results
   }
   ```

8. **Multi-user secondary selector** — When `readingType === "multi"`, the left panel's user card shows the full `MultiUserSelector` (primary + secondary chips + "Add User" button). Other types show only the primary user dropdown.

9. **UserForm modal** — Keep existing modal behavior. Triggered by "Add New Profile" / "Edit" buttons. Floats over the page.

**Layout JSX structure (simplified):**

```tsx
<div className="flex flex-col md:flex-row gap-6">
  {/* LEFT PANEL */}
  <aside className="w-full md:w-80 md:flex-shrink-0 md:sticky md:top-6 md:self-start space-y-4">
    {/* User Profile Card */}
    <section className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
      <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
        {t("oracle.user_profile")}
      </h3>
      {readingType === "multi" ? (
        <MultiUserSelector
          users={users}
          selectedUsers={selectedUsers}
          onChange={setSelectedUsers}
          onAddNew={() => setFormMode("create")}
          onEdit={() => setFormMode("edit")}
          isLoading={usersLoading}
        />
      ) : (
        /* Compact primary-only selector: dropdown + add/edit buttons + user info */
      )}
    </section>

    {/* Reading Type Card */}
    <section className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-4">
      <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
        {t("oracle.reading_type")}
      </h3>
      <ReadingTypeSelector
        value={readingType}
        onChange={handleTypeChange}
        disabled={isLoading}
      />
    </section>
  </aside>

  {/* MAIN AREA */}
  <main className="flex-1 space-y-6">
    {/* Form / Loading Card */}
    <section
      id="oracle-form-panel"
      role="tabpanel"
      className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6 min-h-[300px]"
    >
      <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-4">
        {t(`oracle.type_${readingType}_title`)}
      </h3>
      {isLoading ? (
        <LoadingAnimation
          step={progress.step}
          total={progress.total}
          message={progress.message || t("oracle.loading_generating")}
          onCancel={() => { setIsLoading(false); resetProgress(); }}
        />
      ) : primaryUser || readingType === "daily" ? (
        <OracleConsultationForm
          readingType={readingType}
          userId={primaryUser?.id ?? 0}
          userName={primaryUser?.name ?? ""}
          selectedUsers={selectedUsers}
          onResult={handleResult}
          onLoadingChange={handleLoadingChange}
        />
      ) : (
        <p className="text-[var(--nps-text-dim)] text-sm">
          {t("oracle.select_to_begin")}
        </p>
      )}
    </section>

    {/* Results Card */}
    <section
      ref={resultsRef}
      className="bg-[var(--nps-bg-card)] border border-[var(--nps-border)] rounded-lg p-6"
    >
      <h3 className="text-sm font-semibold text-[var(--nps-accent)] mb-3">
        {t("oracle.reading_results")}
      </h3>
      <ReadingResults result={consultationResult} />
    </section>
  </main>
</div>

{/* UserForm Modal — outside the layout flow */}
{formMode === "create" && (
  <UserForm onSubmit={handleCreate} onCancel={() => { setFormMode(null); setFormError(null); }}
    isSubmitting={createUser.isPending} serverError={formError} />
)}
{formMode === "edit" && primaryUser && (
  <UserForm user={primaryUser} onSubmit={handleUpdate}
    onCancel={() => { setFormMode(null); setFormError(null); }}
    onDelete={handleDelete} isSubmitting={updateUser.isPending} serverError={formError} />
)}
```

### STOP CHECKPOINT 5

- [ ] `Oracle.tsx` renders two-column layout on desktop, stacked on mobile
- [ ] Left panel: user profile selector + reading type tabs
- [ ] Main area: dynamic form + results
- [ ] Reading type persists in URL query parameter `?type=...`
- [ ] Invalid/missing type defaults to "time"
- [ ] Loading animation shows during reading generation
- [ ] Results scroll into view on completion
- [ ] User create/edit/delete modal still works
- [ ] Multi-user type shows full `MultiUserSelector` in left panel
- [ ] `export default` for lazy loading compatibility
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`

---

### Phase 6: TypeScript Types Update

**Goal:** Add the missing `EventType` variant and `ReadingType` export to the types file.

**Modify `frontend/src/types/index.ts`:**

1. Add `"reading_progress"` to the `EventType` union:

   ```typescript
   export type EventType =
     | "finding"
     | "health"
     | "ai_adjusted"
     | "level_up"
     | "checkpoint"
     | "terminal_status"
     | "scan_started"
     | "scan_stopped"
     | "high_score"
     | "config_changed"
     | "shutdown"
     | "stats_update"
     | "error"
     | "reading_progress"; // NEW — WebSocket reading generation progress
   ```

2. Add the `ReadingType` alias (allows importing from `@/types` instead of from the component):

   ```typescript
   // ─── Oracle Reading Types ───
   export type ReadingType = "time" | "name" | "question" | "daily" | "multi";
   ```

   Note: `ReadingTypeSelector.tsx` also exports this type. Having it in both places is fine — the types file is the canonical source, and the component re-exports for convenience.

### STOP CHECKPOINT 6

- [ ] `EventType` union includes `"reading_progress"`
- [ ] `ReadingType` exported from `@/types`
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit`

---

### Phase 7: i18n Translations

**Goal:** Add translation keys for reading type labels, loading messages, and progress steps.

**Modify `frontend/src/locales/en.json` — add to the `oracle` section:**

```json
"reading_type": "Reading Type",
"type_time": "Time",
"type_name": "Name",
"type_question": "Question",
"type_daily": "Daily",
"type_multi": "Multi-User",
"type_time_title": "Time Reading",
"type_name_title": "Name Reading",
"type_question_title": "Ask a Question",
"type_daily_title": "Today's Reading",
"type_multi_title": "Multi-User Reading",
"loading_generating": "Generating your reading...",
"loading_profile": "Loading profile...",
"loading_calculating": "Running calculations...",
"loading_ai": "Consulting Wisdom AI...",
"loading_done": "Preparing your reading...",
"loading_cancel": "Cancel",
"progress_step": "Step {{step}} of {{total}}",
"multi_need_users": "Select at least 2 users for a multi-user reading.",
"multi_select_hint": "Add secondary users from the user panel."
```

**Modify `frontend/src/locales/fa.json` — add matching Persian translations:**

```json
"reading_type": "نوع خوانش",
"type_time": "زمان",
"type_name": "نام",
"type_question": "سوال",
"type_daily": "روزانه",
"type_multi": "چند نفره",
"type_time_title": "خوانش زمان",
"type_name_title": "خوانش نام",
"type_question_title": "پرسش از اوراکل",
"type_daily_title": "خوانش امروز",
"type_multi_title": "خوانش چند نفره",
"loading_generating": "در حال تولید خوانش شما...",
"loading_profile": "بارگذاری پروفایل...",
"loading_calculating": "انجام محاسبات...",
"loading_ai": "مشاوره با هوش مصنوعی حکمت...",
"loading_done": "آماده‌سازی خوانش شما...",
"loading_cancel": "لغو",
"progress_step": "مرحله {{step}} از {{total}}",
"multi_need_users": "حداقل ۲ کاربر برای خوانش چند نفره انتخاب کنید.",
"multi_select_hint": "کاربران بیشتر را از پنل کاربری اضافه کنید."
```

**Important:** Keep ALL existing translation keys. Only add new ones. Do not modify or remove any existing keys.

### STOP CHECKPOINT 7

- [ ] `en.json` has all `oracle.type_*`, `oracle.loading_*`, `oracle.progress_*`, `oracle.multi_*` keys
- [ ] `fa.json` has matching Persian translations for every new key
- [ ] No duplicate keys in JSON files
- [ ] All existing keys preserved
- [ ] JSON valid in both files: `node -e "JSON.parse(require('fs').readFileSync('frontend/src/locales/en.json'))"`

---

### Phase 8: Tests

**Goal:** Write comprehensive tests for all new and modified components.

All tests use Vitest + React Testing Library + userEvent. Follow existing test patterns.

### Test File 1: `frontend/src/components/oracle/__tests__/ReadingTypeSelector.test.tsx`

**6 tests:**

```
test_renders_all_five_types
  — All 5 tab labels visible: Time, Name, Question, Daily, Multi-User

test_active_tab_has_accent_styling
  — Active tab has emerald accent class (bg-nps-accent/10 or matching CSS variable class)

test_click_calls_onChange
  — Clicking a non-active tab calls onChange with the correct ReadingType value

test_disabled_prevents_clicks
  — When disabled=true, clicking tabs does NOT call onChange

test_accessible_roles
  — Container has role="tablist", items have role="tab", active has aria-selected="true"

test_icons_render
  — Each tab renders an SVG element
```

### Test File 2: `frontend/src/components/oracle/__tests__/LoadingAnimation.test.tsx`

**4 tests:**

```
test_renders_pulsing_orb
  — Component renders elements with animate-pulse and/or animate-ping classes

test_displays_progress_message
  — The message text is visible in the DOM

test_progress_bar_width
  — Progress bar inner element has width style matching (step/total)*100 percentage

test_cancel_button_calls_handler
  — When onCancel provided, cancel button visible and clicking it calls the handler
```

### Test File 3: `frontend/src/components/oracle/__tests__/OracleConsultationForm.test.tsx`

**8 tests:**

```
test_renders_time_form_for_time_type
  — When readingType="time", the TimeReadingForm component renders (mock it and check it's called)

test_renders_name_form_for_name_type
  — When readingType="name", NameReadingForm renders

test_renders_question_form_for_question_type
  — When readingType="question", QuestionReadingForm renders

test_renders_daily_card_for_daily_type
  — When readingType="daily", DailyReadingCard renders

test_renders_multi_flow_for_multi_type
  — When readingType="multi" with 2+ users, multi-user submit flow renders

test_multi_shows_warning_when_too_few_users
  — When readingType="multi" and selectedUsers has <2 total users, warning message is shown

test_calls_onResult_after_form_result
  — After a child form invokes its result callback, the parent onResult is called with normalized data

test_no_form_when_no_user
  — When userId=0 and readingType is not "daily", the select-profile prompt message appears
```

### Test File 4: `frontend/src/pages/__tests__/Oracle.test.tsx`

**6 tests:**

```
test_renders_two_column_layout
  — Page renders an aside (left panel) and a main (content) element

test_renders_user_selector
  — User profile dropdown is visible in the left panel area

test_renders_reading_type_selector
  — ReadingTypeSelector component is present (5 tabs visible)

test_default_reading_type_is_time
  — Without URL query param, the time reading form renders

test_reading_type_from_url
  — With ?type=question in the URL, the question reading form renders instead

test_results_section_visible
  — ReadingResults component is rendered in the main area
```

### Test Mocking Strategy

```typescript
// Mock all child form components to isolate Oracle page testing
vi.mock("@/components/oracle/TimeReadingForm", () => ({
  TimeReadingForm: (props: Record<string, unknown>) => (
    <div data-testid="time-reading-form" data-user-id={props.userId} />
  ),
}));
// Similar mocks for NameReadingForm, QuestionReadingForm, DailyReadingCard, etc.

// Mock oracle users hook
vi.mock("@/hooks/useOracleUsers", () => ({
  useOracleUsers: () => ({ data: mockUsers, isLoading: false }),
  useCreateOracleUser: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateOracleUser: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteOracleUser: () => ({ mutate: vi.fn() }),
}));

// Mock react-router-dom useSearchParams
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useSearchParams: () => [new URLSearchParams("type=time"), vi.fn()] };
});
```

### Test Execution

```bash
cd frontend && npx vitest run src/components/oracle/__tests__/ReadingTypeSelector.test.tsx
cd frontend && npx vitest run src/components/oracle/__tests__/LoadingAnimation.test.tsx
cd frontend && npx vitest run src/components/oracle/__tests__/OracleConsultationForm.test.tsx
cd frontend && npx vitest run src/pages/__tests__/Oracle.test.tsx
cd frontend && npx vitest run  # Full suite — all tests must pass
```

### STOP CHECKPOINT 8

- [ ] All 4 test files created with 24 total tests
- [ ] `npx vitest run` — all tests pass (including all existing tests)
- [ ] No TypeScript errors in test files
- [ ] Mock strategy is consistent with existing test patterns

---

### Phase 9: Visual Polish & Integration Verification

**Goal:** Ensure the Oracle page integrates correctly with Session 19's layout and looks correct across all modes.

**Tasks:**

1. **Theme compatibility** — Verify all new components use CSS variable references from Session 19's theme system. Toggle dark/light and confirm:
   - Cards use `var(--nps-bg-card)` background
   - Borders use `var(--nps-border)`
   - Accent colors use `var(--nps-accent)`
   - Text levels use `var(--nps-text)`, `var(--nps-text-bright)`, `var(--nps-text-dim)`

2. **RTL compatibility** — Switch to FA locale:
   - Left panel moves to the right (`md:flex-row-reverse` or CSS logical properties)
   - Reading type selector active border flips to right side (`rtl:border-r-2`)
   - Form content renders right-to-left
   - Icons don't flip (they're symmetric)

3. **Mobile responsiveness** (< 768px):
   - Two columns collapse to single column
   - Reading type tabs become horizontal scrollable row
   - Form and results stack vertically
   - Left panel cards take full width
   - No horizontal overflow

4. **Loading flow walkthrough:**
   - Select user → select reading type → fill form → submit
   - Loading animation appears with pulsing orb
   - Progress text updates via WebSocket (or auto-cycles if no WebSocket)
   - Results appear below form after completion
   - Scroll-to-results works smoothly
   - Cancel button stops the loading

5. **Keyboard navigation:**
   - Tab through: user dropdown → reading type tabs → form fields → submit → result tabs
   - Focus indicators visible on all interactive elements
   - Enter/Space activates reading type tabs

### STOP CHECKPOINT 9

- [ ] Dark mode: All cards, borders, text render with dark theme variables
- [ ] Light mode: All cards, borders, text render with light theme variables
- [ ] FA locale: Full RTL flip — left panel moves right, active tab border flips
- [ ] Mobile: Single-column stack, horizontal tab scroll, no overflow
- [ ] Loading animation visible during submission with progress
- [ ] Results scroll into view on completion
- [ ] Keyboard navigation works through all interactive elements

---

## Summary of All Deliverables

### Files Modified (5)

| #   | File                                                        | Lines (current) | Action                                                             |
| --- | ----------------------------------------------------------- | --------------- | ------------------------------------------------------------------ |
| 1   | `frontend/src/pages/Oracle.tsx`                             | 188             | REWRITE — Two-column layout with URL-driven reading type           |
| 2   | `frontend/src/components/oracle/OracleConsultationForm.tsx` | 149             | REWRITE — Thin coordinator rendering Session 14-16 form components |
| 3   | `frontend/src/types/index.ts`                               | 411             | MODIFY — Add `"reading_progress"` to EventType, add `ReadingType`  |
| 4   | `frontend/src/locales/en.json`                              | 190             | MODIFY — Add ~19 new translation keys                              |
| 5   | `frontend/src/locales/fa.json`                              | ~190            | MODIFY — Add ~19 matching Persian keys                             |

### Files Created (7)

| #   | File                                                                       | Purpose                             |
| --- | -------------------------------------------------------------------------- | ----------------------------------- |
| 1   | `frontend/src/components/oracle/ReadingTypeSelector.tsx`                   | 5-tab segmented control             |
| 2   | `frontend/src/components/oracle/LoadingAnimation.tsx`                      | Pulsing orb + progress bar + cancel |
| 3   | `frontend/src/hooks/useReadingProgress.ts`                                 | WebSocket progress state hook       |
| 4   | `frontend/src/components/oracle/__tests__/ReadingTypeSelector.test.tsx`    | 6 tests                             |
| 5   | `frontend/src/components/oracle/__tests__/LoadingAnimation.test.tsx`       | 4 tests                             |
| 6   | `frontend/src/components/oracle/__tests__/OracleConsultationForm.test.tsx` | 8 tests                             |
| 7   | `frontend/src/pages/__tests__/Oracle.test.tsx`                             | 6 tests                             |

### Files Deleted (0)

None.

### Tests: 24 total

| Test File                         | Count  | What It Tests                                                                    |
| --------------------------------- | ------ | -------------------------------------------------------------------------------- |
| `ReadingTypeSelector.test.tsx`    | 6      | 5 types render, active styling, click handler, disabled, a11y, icons             |
| `LoadingAnimation.test.tsx`       | 4      | Orb animation, progress message, bar width, cancel button                        |
| `OracleConsultationForm.test.tsx` | 8      | Each type renders correct form, multi validation, result callback, no-user guard |
| `Oracle.test.tsx`                 | 6      | Two-column layout, selectors, URL-driven type, defaults, results                 |
| **Total**                         | **24** |                                                                                  |

### Checkpoints: 9

| #   | Phase                  | Key Verification                                                    |
| --- | ---------------------- | ------------------------------------------------------------------- |
| 1   | ReadingTypeSelector    | 5 tabs, active styling, accessible roles, responsive                |
| 2   | LoadingAnimation       | Pulsing orb, progress bar, cancel, aria-live                        |
| 3   | useReadingProgress     | WebSocket subscription, isActive flag, auto-deactivation            |
| 4   | OracleConsultationForm | Coordinator renders correct form per type, normalizeFrameworkResult |
| 5   | Oracle.tsx             | Two-column layout, URL params, scroll to results, default export    |
| 6   | TypeScript types       | EventType updated, ReadingType exported                             |
| 7   | i18n translations      | EN + FA keys added, JSON valid                                      |
| 8   | Tests                  | 24 tests pass, full suite green                                     |
| 9   | Visual polish          | Theme, RTL, mobile, keyboard navigation                             |

---

## Dependency Notes

### What This Session Depends On

- **Session 19:** Layout system, routing (`/oracle` route), theme CSS variables, `useTheme` hook
- **Session 14:** `TimeReadingForm.tsx`, `FrameworkReadingResponse` type, `useSubmitTimeReading()` hook, unified `POST /api/oracle/readings` endpoint
- **Session 15:** `NameReadingForm.tsx`, `QuestionReadingForm.tsx`, updated hooks
- **Session 16:** `DailyReadingCard.tsx`, `MultiUserReadingDisplay.tsx`, `CompatibilityMeter.tsx`, daily + multi-user hooks
- **Session 17:** Rewritten `ReadingHistory.tsx`, `ReadingCard.tsx`, `ReadingDetail.tsx`
- **Session 18:** `ReadingFeedback.tsx` and `StarRating.tsx` integrated into `ReadingResults.tsx`

### What Depends On This Session

- **Session 21:** Reading Results Display — enhances the results section with 9-section cards, FC60 stamp visualization, numerology number displays, pattern badges, share button, print CSS
- **Session 22:** Dashboard Page — embeds `DailyReadingCard` for "Today's Reading" widget, links "View Full Reading" to `/oracle?type=daily`
- **Sessions 23-25:** User profile page, settings — may reference Oracle page patterns
- **Sessions 26-31:** RTL polish, responsive refinement, accessibility enhancements — build on the mobile/RTL foundation established here

### Technical Constraints

1. **No new npm dependencies.** All UI built with existing React + Tailwind + react-router-dom.
2. **No new API endpoints.** Session 20 is frontend-only. All API calls use existing endpoints from Sessions 14-16.
3. **Existing form component contracts preserved.** `TimeReadingForm`, `NameReadingForm`, `QuestionReadingForm`, `DailyReadingCard`, `MultiUserReadingDisplay` are used as-is with their established props interfaces from Sessions 14-16.
4. **URL query parameter for reading type.** Uses `useSearchParams()` from react-router-dom — not component state alone. Enables deep linking and browser back/forward navigation.
5. **Default export required.** `Oracle.tsx` must use `export default` for Session 19's lazy loading (`React.lazy()`).
6. **Theme-aware colors only.** All new components use CSS variable references (`var(--nps-bg-card)`, `var(--nps-accent)`, etc.) — not hardcoded hex values.

---

## Error Scenarios

| Scenario                                   | Expected Behavior                                                                                                                                  |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| No user profiles exist                     | Left panel shows "No profiles" + "Add New Profile" button. Main area shows "Select a profile to begin." Daily type still works (no user required). |
| User switches reading type during loading  | Tabs disabled during loading (`disabled` prop). Cancel button available.                                                                           |
| WebSocket not connected                    | Loading animation shows with generic "Generating..." message. `useReadingProgress` receives no events; `LoadingAnimation` uses its props directly. |
| Reading API returns error                  | Loading animation hides. Error message displayed in form area via child form's error handling.                                                     |
| Multi-user with < 2 users                  | Warning message: "Select at least 2 users for a multi-user reading." Submit disabled.                                                              |
| Invalid URL type parameter (`?type=xyz`)   | Defaults to `"time"`. No error shown.                                                                                                              |
| Browser back after type change             | URL updates → `useSearchParams` detects change → reading type selector syncs automatically.                                                        |
| Daily reading when already generated today | `DailyReadingCard` handles cache display (Session 16 cache logic). No duplicate generation.                                                        |

---

## Handoff

**Session 21 (Reading Results Display) receives:**

- Oracle page with all 5 reading types functional via tabbed interface
- `ConsultationResult` type handles all reading type outputs
- `ReadingResults` component renders via existing `SummaryTab`, `DetailsTab`, `ReadingHistory` tabs
- Session 21 will rewrite the results area into a rich 9-section display: header, Universal Address (FC60 stamp), Core Identity, Right Now, Patterns, The Message, Advice, Caution, Footer — with scroll-reveal animations, numerology number displays, pattern badges, share button, and print-friendly CSS

**Session 22 (Dashboard Page) receives:**

- All reading types working — Dashboard can show reading stats by type
- `DailyReadingCard` available for embedding as a dashboard widget
- Deep link pattern: Dashboard "View Reading" links to `/oracle?type=daily`
- `LoadingAnimation` reusable in other contexts if needed
