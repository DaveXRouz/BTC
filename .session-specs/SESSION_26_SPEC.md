# SESSION 26 SPEC — RTL Layout System

> **Block:** Frontend Advanced (Sessions 26-31)
> **Complexity:** Very High
> **Depends on:** Session 24 (i18n Framework)
> **Spec written:** 2026-02-10

---

## TL;DR

Wire up full RTL (right-to-left) layout support so the entire UI mirrors correctly when Persian locale is active. Install and configure Tailwind RTL plugin, create a `useDirection` hook, add an `rtl.css` override sheet, patch every component that uses directional CSS (margins, paddings, borders, icons, text alignment), handle mixed-direction content (English terms inside RTL text), and add visual regression tests that compare EN vs FA screenshots.

---

## 0. Prerequisites

| Requirement                          | How to verify                                                                                          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| Session 24 complete (i18n Framework) | `App.tsx` sets `document.documentElement.dir` based on `i18n.language`                                 |
| `react-i18next` configured           | `frontend/src/i18n/config.ts` exists with EN/FA resources                                              |
| `LanguageToggle` component           | `frontend/src/components/LanguageToggle.tsx` renders EN/FA switch                                      |
| Locale files                         | `frontend/src/locales/en.json` and `fa.json` exist (~190 keys each)                                    |
| Persian formatter                    | `frontend/src/utils/persianFormatter.ts` has `toPersianDigits`, `toPersianNumber`, `formatPersianDate` |
| Tailwind configured                  | `frontend/tailwind.config.ts` with `nps` color namespace                                               |

**Pre-flight check (run before starting):**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
cat src/App.tsx | grep -c 'documentElement.dir'        # expect ≥ 1
cat src/i18n/config.ts | grep -c 'react-i18next'       # expect ≥ 1
ls src/components/LanguageToggle.tsx                     # must exist
ls src/locales/fa.json                                  # must exist
cat tailwind.config.ts | grep -c 'tailwindcss-rtl\|rtl' # expect 0 (not yet installed)
```

---

## 1. Objectives

| #   | Objective                                 | Deliverable                                                                             |
| --- | ----------------------------------------- | --------------------------------------------------------------------------------------- |
| 1   | Install and configure Tailwind RTL plugin | `tailwindcss-rtl` in `tailwind.config.ts` plugins array                                 |
| 2   | Create `useDirection` hook                | `frontend/src/hooks/useDirection.ts` — returns `dir`, `isRTL`, `locale`                 |
| 3   | Create RTL override stylesheet            | `frontend/src/styles/rtl.css` — direction-specific overrides that Tailwind can't handle |
| 4   | Patch Layout component                    | Sidebar flips to right side, nav items mirror, border sides swap                        |
| 5   | Patch all Oracle components               | Reading cards, detail sections, tabs, forms — all mirror correctly                      |
| 6   | Handle mixed-direction content            | English technical terms (`FC60`, numbers, addresses) stay LTR inside RTL text           |
| 7   | Fix icon directions                       | Arrows, chevrons, navigation icons flip in RTL                                          |
| 8   | Add visual regression tests               | Playwright screenshots comparing EN layout vs FA layout                                 |
| 9   | Update locale files                       | Add any missing RTL-related translation keys                                            |
| 10  | Ensure smooth transition                  | Toggling EN↔FA re-renders without flicker or layout jump                                |

---

## 2. Files to Create

| #   | Path                                                   | Purpose                                                             |
| --- | ------------------------------------------------------ | ------------------------------------------------------------------- |
| 1   | `frontend/src/hooks/useDirection.ts`                   | Hook: returns `{ dir, isRTL, locale }` from i18n state              |
| 2   | `frontend/src/styles/rtl.css`                          | RTL overrides that Tailwind utility classes cannot cover            |
| 3   | `frontend/src/components/common/BiDirectionalText.tsx` | Wrapper for mixed-direction content — isolates LTR spans inside RTL |
| 4   | `frontend/src/components/common/DirectionalIcon.tsx`   | Icon wrapper that auto-flips horizontally in RTL mode               |
| 5   | `frontend/src/__tests__/rtl-layout.test.tsx`           | Unit tests for RTL hook and directional components                  |
| 6   | `frontend/e2e/rtl-visual.spec.ts`                      | Playwright visual regression: EN vs FA screenshots                  |

---

## 3. Files to Modify

| #   | Path                                                        | What Changes                                                                                      |
| --- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| 1   | `frontend/tailwind.config.ts`                               | Add `tailwindcss-rtl` to plugins array                                                            |
| 2   | `frontend/src/App.tsx`                                      | Import `rtl.css`, ensure dir/lang attributes apply cleanly on locale change                       |
| 3   | `frontend/src/components/Layout.tsx`                        | Replace hardcoded `border-r`/`ml-*`/`mr-*` with logical RTL-aware classes; sidebar position flips |
| 4   | `frontend/src/components/LanguageToggle.tsx`                | Add smooth transition when switching, aria-label updates for active direction                     |
| 5   | `frontend/src/components/oracle/ReadingResults.tsx`         | Use `useDirection` for tab alignment, result card padding                                         |
| 6   | `frontend/src/components/oracle/SummaryTab.tsx`             | Mirror stat cards layout, text alignment, badge positioning                                       |
| 7   | `frontend/src/components/oracle/DetailsTab.tsx`             | Collapsible chevron flips, section padding mirrors, mixed-content isolation                       |
| 8   | `frontend/src/components/oracle/OracleConsultationForm.tsx` | Form labels, input alignment, button positioning for RTL                                          |
| 9   | `frontend/src/components/oracle/MultiUserSelector.tsx`      | User chips, add button position, list direction                                                   |
| 10  | `frontend/src/components/oracle/UserForm.tsx`               | Form grid direction, label alignment, error message position                                      |
| 11  | `frontend/src/components/oracle/ExportButton.tsx`           | Dropdown menu position flips in RTL                                                               |
| 12  | `frontend/src/components/oracle/ReadingHistory.tsx`         | Table column order consideration, date alignment                                                  |
| 13  | `frontend/src/components/oracle/PersianKeyboard.tsx`        | Already RTL — verify no regressions                                                               |
| 14  | `frontend/src/locales/en.json`                              | Add RTL-related keys (e.g., `settings.direction`, `common.ltr`, `common.rtl`)                     |
| 15  | `frontend/src/locales/fa.json`                              | Add matching Persian RTL keys                                                                     |
| 16  | `frontend/src/main.tsx`                                     | Import `rtl.css` if not imported via App.tsx                                                      |
| 17  | `frontend/package.json`                                     | Add `tailwindcss-rtl` dependency                                                                  |

---

## 4. Files to Delete

None.

---

## 5. Implementation Phases

### Phase 1 — Tailwind RTL Plugin + useDirection Hook

**Goal:** Install infrastructure so all subsequent phases can use `rtl:` Tailwind prefix and `useDirection()` hook.

**Step 1.1 — Install `tailwindcss-rtl`:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
npm install tailwindcss-rtl
```

**Step 1.2 — Configure plugin in `tailwind.config.ts`:**

Add to plugins array:

```ts
import rtl from "tailwindcss-rtl";

// In config:
plugins: [rtl],
```

The `tailwindcss-rtl` plugin provides:

- `rtl:` and `ltr:` variant prefixes (e.g., `rtl:mr-4` applies only in RTL mode)
- Logical property utilities: `ms-*` (margin-start), `me-*` (margin-end), `ps-*` (padding-start), `pe-*` (padding-end)
- `start-*` and `end-*` for positioning (replaces `left-*`/`right-*`)

**Step 1.3 — Create `useDirection` hook:**

File: `frontend/src/hooks/useDirection.ts`

```
Hook signature:
  useDirection() → { dir: "ltr" | "rtl", isRTL: boolean, locale: string }

Logic:
  - Import useTranslation from react-i18next
  - Derive dir from i18n.language: "fa" → "rtl", else "ltr"
  - Return { dir, isRTL: dir === "rtl", locale: i18n.language }

This hook is the SINGLE SOURCE OF TRUTH for direction.
Components must NOT check i18n.language directly for direction decisions.
```

**Step 1.4 — Create `rtl.css`:**

File: `frontend/src/styles/rtl.css`

Purpose: Overrides that Tailwind classes cannot express (e.g., third-party component internals, scrollbar position, CSS custom properties for direction-dependent values).

```
Contents:
  [dir="rtl"] body { text-align: right; }
  [dir="rtl"] .scrollbar-left { direction: rtl; }
  [dir="rtl"] input[type="number"] { text-align: left; }  /* Numbers stay LTR */
  [dir="rtl"] .font-mono { direction: ltr; unicode-bidi: embed; }  /* Code stays LTR */
  [dir="rtl"] .technical-value { direction: ltr; unicode-bidi: isolate; }
```

**Step 1.5 — Import `rtl.css` in `App.tsx`:**

Add `import "./styles/rtl.css"` near the top of App.tsx (after Tailwind import).

**STOP checkpoint — verify before continuing:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# 1. Plugin installed
grep -c 'tailwindcss-rtl' package.json        # expect 1

# 2. Plugin configured
grep -c 'tailwindcss-rtl\|rtl' tailwind.config.ts  # expect ≥ 1

# 3. Hook exists
ls src/hooks/useDirection.ts                   # must exist

# 4. RTL stylesheet exists
ls src/styles/rtl.css                          # must exist

# 5. Dev server compiles
npx tsc --noEmit 2>&1 | tail -5               # expect no errors
```

---

### Phase 2 — Directional Utility Components

**Goal:** Create reusable `BiDirectionalText` and `DirectionalIcon` components that other phases use.

**Step 2.1 — BiDirectionalText component:**

File: `frontend/src/components/common/BiDirectionalText.tsx`

```
Purpose: Wraps text that may contain mixed-direction content.
Uses <bdi> element and dir attribute to isolate direction.

Props:
  children: ReactNode
  forceDir?: "ltr" | "rtl"    — override auto direction
  as?: "span" | "p" | "div"   — HTML element (default: "span")
  className?: string

Behavior:
  - If forceDir is set, use that direction
  - Otherwise, auto-detect: if content is mostly Latin chars → dir="ltr"
  - Wrap in <bdi> element to prevent Unicode BiDi algorithm issues

Use cases:
  - FC60 stamps like "甲子" inside Persian text
  - Bitcoin addresses (always LTR)
  - English technical terms like "Life Path" in Persian context
  - Numbers that should remain LTR formatted
```

**Step 2.2 — DirectionalIcon component:**

File: `frontend/src/components/common/DirectionalIcon.tsx`

```
Purpose: Wraps icons that need horizontal flipping in RTL.
Not all icons flip — only directional ones (arrows, chevrons, back/forward).

Props:
  children: ReactNode          — the icon element
  flip?: boolean               — whether to flip in RTL (default: true)
  className?: string

Behavior:
  - Import useDirection hook
  - If isRTL && flip → apply CSS transform: scaleX(-1)
  - If !flip → render as-is (e.g., checkmarks, close icons don't flip)

Icons that SHOULD flip:
  - Chevron left/right (→ becomes ←)
  - Arrow left/right
  - Back/forward navigation
  - Sidebar collapse/expand

Icons that SHOULD NOT flip:
  - Checkmark, X/close
  - Up/down arrows
  - Refresh/reload
  - Search magnifier
  - Moon/sun (theme)
  - Plus/minus
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Components exist
ls src/components/common/BiDirectionalText.tsx   # must exist
ls src/components/common/DirectionalIcon.tsx      # must exist

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5                  # expect no errors
```

---

### Phase 3 — Layout Component RTL

**Goal:** Make the sidebar + main content area mirror correctly in RTL.

**Step 3.1 — Patch `Layout.tsx`:**

Current state (from reading the file):

- Sidebar is a fixed `w-64` div on the LEFT side
- Uses `border-r` for right border (with existing `rtl:border-r-0 rtl:border-l` — good start)
- Main content has `ml-64` to offset for sidebar
- Nav items have various `ml-*`/`mr-*` for spacing
- Icons are to the left of text labels

Changes needed:

```
1. SIDEBAR POSITION:
   Current:  fixed left-0 → sidebar on left
   RTL:      fixed right-0 → sidebar on right
   Solution: Replace left-0 with start-0 (logical property from rtl plugin)
             OR use rtl:right-0 rtl:left-auto ltr:left-0

2. MAIN CONTENT OFFSET:
   Current:  ml-64 → content pushed right of sidebar
   RTL:      mr-64 → content pushed left of sidebar
   Solution: Replace ml-64 with ms-64 (margin-start)

3. BORDER:
   Current:  Already has rtl:border-r-0 rtl:border-l — KEEP
   Verify:   Ensure border color is preserved in both directions

4. NAV ITEMS:
   Current:  Icons have mr-3 (margin-right) before text
   RTL:      Icons need ml-3 (margin-left) before text
   Solution: Replace mr-3 with me-3 (margin-end)

5. NAV ITEM HOVER/ACTIVE:
   Current:  May have left border indicator for active state
   RTL:      Flip to right border indicator
   Solution: Use border-s-* (border-start) instead of border-l-*

6. LANGUAGE TOGGLE POSITION:
   Current:  Bottom of sidebar
   RTL:      Should remain at bottom (no horizontal change needed)
   Verify:   Text alignment inside toggle
```

**Step 3.2 — Patch `LanguageToggle.tsx`:**

```
Changes:
  - Add aria-label that describes current direction state
  - Ensure active locale highlight doesn't jump during switch
  - Add transition-all for smooth re-render on direction change
  - Button order: in LTR show [EN | FA], in RTL show [FA | EN]
    OR keep consistent order — decide based on UX (recommend: keep [EN | FA] order always)
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Start dev server
npm run dev &
DEV_PID=$!
sleep 3

# Manual verification steps:
echo "1. Open http://localhost:5173"
echo "2. Click FA language toggle"
echo "3. Verify: sidebar appears on RIGHT side"
echo "4. Verify: main content shifts LEFT"
echo "5. Verify: nav item icons are to RIGHT of text"
echo "6. Verify: no overlapping elements"
echo "7. Click EN toggle — everything returns to LTR"

kill $DEV_PID
```

---

### Phase 4 — Oracle Components RTL

**Goal:** Patch all Oracle-related components to mirror correctly in RTL mode.

**Step 4.1 — ReadingResults.tsx:**

```
Current state: 3-tab interface (Summary / Details / History) with ExportButton

Changes:
  - Tab bar: text-align flips (tabs should flow from right in RTL)
  - Tab underline indicator: ensure it tracks correctly in RTL
  - ExportButton position: if absolutely positioned, flip side
  - Result container: padding-start/padding-end instead of pl/pr
```

**Step 4.2 — SummaryTab.tsx:**

```
Changes:
  - Stat grid: flex-row becomes flex-row-reverse in RTL? NO — grid should just flow naturally with RTL
  - Type badge: if positioned top-right, flip to top-left in RTL
    Solution: Use end-* positioning instead of right-*
  - FC60/numerology labels: text-align inherits from dir — should work automatically
  - AI interpretation block: text-align should follow dir for Persian text
  - TranslatedReading component: verify it handles RTL text properly
  - Number displays: numbers stay LTR even in RTL context
    Wrap with BiDirectionalText forceDir="ltr"
```

**Step 4.3 — DetailsTab.tsx:**

```
Changes:
  - Collapsible section chevron: currently on left (expand/collapse indicator)
    In RTL: flip to right side using DirectionalIcon
  - Section title: text alignment follows dir (automatic)
  - Key-value pairs inside sections:
    LTR: [Label: ····· Value] (label left, value right)
    RTL: [Value ····· :Label] (value left, label right)
    Solution: Use justify-between in flex — works automatically with dir
  - FC60 data display: Chinese characters and stems stay LTR
    Wrap with BiDirectionalText forceDir="ltr"
  - Padding: replace pl-*/pr-* with ps-*/pe-*
```

**Step 4.4 — OracleConsultationForm.tsx:**

```
Changes:
  - Form labels: text-align follows dir (automatic for block labels)
  - Input fields: text input should follow dir, BUT number inputs stay LTR
    Apply class="technical-value" to number inputs (from rtl.css)
  - Sign type radio/select: label text follows dir, value stays LTR
  - Submit button: if right-aligned, use end-* positioning
  - Error messages: text-align follows dir
  - Date picker: numbers should be Persian digits in FA locale (already handled by persianFormatter)
  - Textarea for question: should be RTL in FA mode
```

**Step 4.5 — MultiUserSelector.tsx:**

```
Changes:
  - User chip list: chips flow from right in RTL (natural flex behavior with dir)
  - "Add user" button: if at end of chip list, use ms-auto (margin-start auto)
  - Remove (X) button on chips: stay in same relative position (top-end)
    Use end-* instead of right-*
  - Primary user badge: positioned at start of chip
```

**Step 4.6 — UserForm.tsx:**

```
Changes:
  - Form grid: 2-column layout — columns don't need to swap, but label alignment flips
  - Label text: text-align follows dir (automatic)
  - Input placeholders: Persian placeholders in FA locale (from locale file)
  - Persian name field: should always be RTL
    Apply dir="rtl" directly on that input
  - English name field: should always be LTR
    Apply dir="ltr" directly on that input
  - Birthday inputs (year/month/day): numbers stay LTR
```

**Step 4.7 — ExportButton.tsx:**

```
Changes:
  - Dropdown menu: if opens to the left, flip to open right in RTL
    Use end-0 instead of right-0 for dropdown position
  - Menu items: text-align follows dir
  - Icons in menu items: use DirectionalIcon for download arrow
```

**Step 4.8 — ReadingHistory.tsx:**

```
Changes:
  - Table/list: text alignment follows dir for text columns
  - Date column: numbers stay LTR, but Persian date format from persianFormatter
  - Action buttons: positioned at end of row (use ms-auto or end-*)
  - Pagination: button order may need flipping (← → becomes → ← in RTL)
    Use DirectionalIcon for arrows
  - Empty state message: text-align follows dir
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5    # expect no errors

# Existing tests still pass
npx vitest run --reporter=verbose 2>&1 | tail -20  # all green
```

---

### Phase 5 — Mixed-Direction Content Handling

**Goal:** Ensure English technical terms, numbers, addresses, and code snippets render correctly inside RTL text.

**Step 5.1 — Identify all mixed-content locations:**

```
Mixed-direction content in the app:

1. FC60 stamps (e.g., "甲子-Fire-Yang")
   → Always LTR, wrap with BiDirectionalText forceDir="ltr"

2. Numerology numbers (Life Path: 7, Destiny: 9)
   → Numbers themselves LTR, labels follow dir
   → Wrap number value with BiDirectionalText forceDir="ltr"

3. Zodiac signs (English names like "Aries", "Taurus")
   → Keep LTR inside RTL text
   → Wrap with BiDirectionalText forceDir="ltr"

4. Chinese Ganzhi characters (年号, 天干地支)
   → Keep LTR
   → Wrap with BiDirectionalText forceDir="ltr"

5. Moon phase emoji + name ("🌕 Full Moon")
   → Emoji is neutral, name follows locale
   → If FA locale, use translated name from locale file

6. Angel numbers (111, 222, 333)
   → Numbers always LTR
   → Wrap with BiDirectionalText forceDir="ltr"

7. Chaldean letter-value mappings ("A=1, B=2")
   → Always LTR (these are English letter references)
   → Wrap entire block with BiDirectionalText forceDir="ltr"

8. Technical labels in SummaryTab ("FC60", "Numerology", "Chaldean")
   → In FA locale, use Persian translations from locale file
   → If untranslated (English fallback), wrap with BiDirectionalText

9. Date/time displays
   → FA: use Persian digits and Jalaali calendar from persianFormatter
   → EN: standard Gregorian
   → Dates are always wrapped in BiDirectionalText
```

**Step 5.2 — Apply BiDirectionalText across components:**

Go through each component from Phase 4 and wrap the identified mixed-content spans. Use the following rules:

```
RULE 1: Pure numbers → <BiDirectionalText forceDir="ltr">{value}</BiDirectionalText>
RULE 2: English technical terms → <BiDirectionalText forceDir="ltr">{term}</BiDirectionalText>
RULE 3: Chinese/CJK characters → <BiDirectionalText forceDir="ltr">{chars}</BiDirectionalText>
RULE 4: Translated labels → Just use t("key") — direction follows page dir
RULE 5: Mixed "Label: Value" → Label follows dir, value gets BiDirectionalText if needed
RULE 6: Monospace/code blocks → Already handled by rtl.css .font-mono rule
```

**Step 5.3 — Update `persianFormatter.ts`:**

```
Verify existing functions work in RTL context:
  - toPersianDigits: replaces 0-9 with ۰-۹ — works fine
  - toPersianNumber: uses toLocaleString("fa-IR") — works fine
  - formatPersianDate: returns Jalaali date string — verify it includes Persian month names

Add if missing:
  - formatBiDirectionalNumber(n, locale): returns Persian digits for FA, Western for EN
  - wrapLTR(text): wraps text in Unicode LTR mark characters (U+200E) as fallback
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Verify no raw English text breaks RTL layout
# Start dev server and manually check:
echo "Manual check list:"
echo "1. Open Oracle page in FA mode"
echo "2. Do a reading — verify mixed content in results"
echo "3. Check FC60 stamp displays LTR inside RTL card"
echo "4. Check numbers are not reversed (١٢٣ not ٣٢١)"
echo "5. Check Chaldean letter values read left-to-right"
echo "6. Check angel numbers display correctly"
```

---

### Phase 6 — Transition Smoothness + Edge Cases

**Goal:** Ensure switching EN↔FA is instant, flicker-free, and handles all edge cases.

**Step 6.1 — Smooth locale transition:**

```
Current behavior in App.tsx:
  useEffect monitors i18n.language, sets document.documentElement.dir and lang

Improvements:
  1. Add CSS transition on body for background/text color changes during switch
     (prevents visual flash)
  2. Ensure React re-renders triggered by language change don't cause layout thrashing
     → useDirection hook uses useMemo to prevent unnecessary re-renders
  3. Test rapid toggling (click EN/FA/EN/FA quickly) — should not break layout
  4. Verify localStorage persists language choice (already done in i18n config)
  5. Verify page refresh in FA mode keeps RTL layout (already done via i18n LanguageDetector)
```

**Step 6.2 — Edge cases to handle:**

```
EDGE 1: Scrollbar position
  LTR: scrollbar on right (default)
  RTL: scrollbar on left (handled by browser when dir="rtl")
  Verify: no double scrollbar or missing scrollbar

EDGE 2: Fixed/absolute positioned elements
  - LanguageToggle (sidebar bottom) — verify position
  - Tooltips — if any, verify they appear on correct side
  - Dropdown menus — verify alignment

EDGE 3: CSS animations
  - Slide-in animations should flip direction
  - Spinner/loading animations should NOT flip (rotation is direction-neutral)

EDGE 4: Keyboard shortcuts
  - If any keyboard shortcuts use arrow keys, verify they make sense in RTL
  - Tab order should follow visual order (RTL in FA mode)

EDGE 5: Print layout
  - If Session 21 added print CSS, verify it respects RTL
  - Print stylesheet should include dir attribute

EDGE 6: Text selection
  - Selecting mixed-direction text should work naturally
  - Copy-paste should preserve direction marks

EDGE 7: Form submission
  - RTL text in form fields should submit correctly (UTF-8 handles this)
  - Verify API receives correct text regardless of direction
```

**Step 6.3 — CSS transition for direction switch:**

Add to `rtl.css`:

```
/* Smooth direction transition */
body {
  transition: direction 0s, text-align 0.15s ease;
}

/* Prevent layout shift during switch */
[dir] * {
  transition: margin 0.15s ease, padding 0.15s ease;
}

/* Disable transition on initial load */
.no-transition * {
  transition: none !important;
}
```

Add to `App.tsx`:

- On mount: add `no-transition` class to body
- After first render: remove `no-transition` class (via requestAnimationFrame)
- This prevents the transition animation on page load

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# TypeScript compiles clean
npx tsc --noEmit 2>&1 | tail -5

# All existing tests pass
npx vitest run --reporter=verbose 2>&1 | tail -20

# Dev server starts without warnings
npm run dev 2>&1 &
DEV_PID=$!
sleep 3
kill $DEV_PID
```

---

### Phase 7 — Tests

**Goal:** Write unit tests for RTL utilities and visual regression tests for layout.

**Step 7.1 — Unit tests (`frontend/src/__tests__/rtl-layout.test.tsx`):**

```
Test 1: useDirection returns LTR for English locale
  Setup: mock i18n.language = "en"
  Assert: dir === "ltr", isRTL === false, locale === "en"

Test 2: useDirection returns RTL for Persian locale
  Setup: mock i18n.language = "fa"
  Assert: dir === "rtl", isRTL === true, locale === "fa"

Test 3: BiDirectionalText renders with correct dir attribute
  Render: <BiDirectionalText forceDir="ltr">Hello</BiDirectionalText>
  Assert: output element has dir="ltr"

Test 4: BiDirectionalText auto-detects Latin text as LTR
  Render: <BiDirectionalText>FC60 Stamp</BiDirectionalText>
  Assert: output has dir="ltr" (majority Latin characters)

Test 5: BiDirectionalText auto-detects Persian text as RTL
  Render: <BiDirectionalText>سلام دنیا</BiDirectionalText>
  Assert: output has dir="rtl" (majority Arabic-script characters)

Test 6: DirectionalIcon flips in RTL mode
  Setup: mock i18n.language = "fa"
  Render: <DirectionalIcon><ChevronRight /></DirectionalIcon>
  Assert: wrapper has style transform: scaleX(-1)

Test 7: DirectionalIcon does NOT flip when flip=false
  Setup: mock i18n.language = "fa"
  Render: <DirectionalIcon flip={false}><CheckIcon /></DirectionalIcon>
  Assert: wrapper does NOT have scaleX(-1)

Test 8: Layout sidebar renders on right in RTL
  Setup: mock i18n.language = "fa"
  Render: <Layout />
  Assert: sidebar element has class containing "end-0" or "right-0" for RTL
  Assert: main content has me-64 or equivalent start margin

Test 9: LanguageToggle switches direction
  Render: <LanguageToggle />
  Act: click FA button
  Assert: document.documentElement.dir === "rtl"
  Act: click EN button
  Assert: document.documentElement.dir === "ltr"

Test 10: ReadingResults tabs align correctly in RTL
  Setup: mock i18n.language = "fa"
  Render: <ReadingResults result={mockReading} />
  Assert: tab list has correct RTL-aware classes

Test 11: Form inputs have correct dir attributes
  Setup: mock i18n.language = "fa"
  Render: <UserForm />
  Assert: Persian name input has dir="rtl"
  Assert: English name input has dir="ltr"
  Assert: Number inputs have dir="ltr"

Test 12: Mixed content isolation
  Setup: mock i18n.language = "fa"
  Render: SummaryTab with FC60 data
  Assert: FC60 stamp is wrapped in LTR-isolating element
  Assert: Numerology numbers are in LTR-isolating elements
```

**Step 7.2 — Visual regression tests (`frontend/e2e/rtl-visual.spec.ts`):**

```
Prerequisites:
  - Playwright installed (from Session 24 or install now)
  - Dev server running

Test 13: Layout screenshot — LTR mode
  Navigate: http://localhost:5173
  Set locale: EN
  Screenshot: "layout-ltr.png"
  Assert: screenshot matches baseline (or save as baseline on first run)

Test 14: Layout screenshot — RTL mode
  Navigate: http://localhost:5173
  Set locale: FA
  Wait: 500ms for transition
  Screenshot: "layout-rtl.png"
  Assert: screenshot matches baseline

Test 15: Oracle page — LTR mode
  Navigate: http://localhost:5173/oracle
  Set locale: EN
  Screenshot: "oracle-ltr.png"

Test 16: Oracle page — RTL mode
  Navigate: http://localhost:5173/oracle
  Set locale: FA
  Wait: 500ms
  Screenshot: "oracle-rtl.png"

Test 17: Reading results — RTL mode
  Navigate: http://localhost:5173/oracle
  Set locale: FA
  Mock: API returns full reading result
  Screenshot: "reading-results-rtl.png"

Test 18: Rapid toggle does not break layout
  Navigate: http://localhost:5173
  Loop 10 times: toggle EN→FA→EN
  Screenshot: "after-rapid-toggle.png"
  Assert: layout is identical to initial LTR baseline
```

**STOP checkpoint — final:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Unit tests pass
npx vitest run src/__tests__/rtl-layout.test.tsx --reporter=verbose

# All existing tests still pass (regression check)
npx vitest run --reporter=verbose

# TypeScript compiles clean
npx tsc --noEmit

# Lint passes
npx eslint src/ --ext .ts,.tsx

# Visual regression tests (if Playwright installed)
npx playwright test e2e/rtl-visual.spec.ts --reporter=list
```

---

## 6. Acceptance Criteria

| #   | Criterion                                       | How to Verify                                        |
| --- | ----------------------------------------------- | ---------------------------------------------------- |
| 1   | Tailwind RTL plugin installed and configured    | `grep 'tailwindcss-rtl' package.json` returns match  |
| 2   | `useDirection` hook works for both locales      | Unit tests 1-2 pass                                  |
| 3   | `BiDirectionalText` isolates mixed content      | Unit tests 3-5 pass                                  |
| 4   | `DirectionalIcon` flips correctly               | Unit tests 6-7 pass                                  |
| 5   | Layout sidebar flips in RTL                     | Switch to FA → sidebar on right, content shifts left |
| 6   | All Oracle components render correctly in RTL   | Visual inspection + unit tests 10-12                 |
| 7   | Numbers and technical terms stay LTR inside RTL | FC60 stamps, addresses, numbers readable             |
| 8   | Locale toggle is smooth (no flicker)            | Toggle EN↔FA rapidly — no layout jump                |
| 9   | Page refresh preserves direction                | Refresh in FA → stays RTL                            |
| 10  | All 18 tests pass                               | `npx vitest run` + `npx playwright test` all green   |
| 11  | TypeScript compiles with zero errors            | `npx tsc --noEmit` exits 0                           |
| 12  | No regressions in existing tests                | All pre-existing tests still pass                    |

---

## 7. Error Scenarios

| Scenario                                               | Expected Behavior                                                                                |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `tailwindcss-rtl` not installed                        | `npm install` in Phase 1 — if fails, check npm registry, try `--legacy-peer-deps`                |
| `rtl:` prefix not working in Tailwind                  | Verify plugin is in `plugins` array, restart dev server, check Tailwind version compatibility    |
| Sidebar overlaps content in RTL                        | Check `ms-64` (margin-start) is applied to main content, verify sidebar uses `end-0` positioning |
| Numbers appear reversed in RTL                         | Ensure `unicode-bidi: isolate` or `BiDirectionalText forceDir="ltr"` wraps number values         |
| Text input cursor jumps when typing in mixed content   | Apply `dir` attribute directly on input element, not just parent                                 |
| Transition flicker on locale switch                    | Add `no-transition` class on mount, remove after first paint via `requestAnimationFrame`         |
| Visual regression tests fail on different screen sizes | Pin viewport to 1280x720 in Playwright config                                                    |
| `useDirection` causes unnecessary re-renders           | Memoize return value with `useMemo`, ensure i18n event listener cleans up                        |
| Persian keyboard component breaks in LTR mode          | PersianKeyboard already has local `dir="rtl"` — should work regardless of page direction         |
| Print layout doesn't respect RTL                       | Add `@media print { [dir="rtl"] ... }` rules in `rtl.css`                                        |

---

## 8. Handoff

**What Session 27 needs to know:**

- RTL infrastructure is complete: `tailwindcss-rtl` plugin, `useDirection` hook, `rtl.css`, `BiDirectionalText`, `DirectionalIcon`
- All components in `frontend/src/components/oracle/` have been patched for RTL
- Layout.tsx sidebar flips correctly
- `useDirection()` is the single source of truth — import from `@/hooks/useDirection`
- Mixed-direction content uses `BiDirectionalText` with `forceDir` prop
- Visual regression baselines saved in `frontend/e2e/` (if Playwright is configured)

**Session 27 (Responsive Design) should:**

- Build on the RTL foundation — responsive breakpoints must work in BOTH directions
- Mobile sidebar (hamburger menu) must flip correctly in RTL
- Breakpoint-specific RTL rules may be needed (e.g., `md:rtl:ps-4`)
- Test all responsive breakpoints in both EN and FA locales

**Key files for Session 27 to read:**

- `frontend/src/hooks/useDirection.ts` — direction hook
- `frontend/src/styles/rtl.css` — override stylesheet
- `frontend/src/components/common/BiDirectionalText.tsx` — mixed-content wrapper
- `frontend/src/components/common/DirectionalIcon.tsx` — icon flipper
- `frontend/tailwind.config.ts` — RTL plugin configuration

---

## Appendix A — Tailwind RTL Quick Reference

```
PHYSICAL → LOGICAL property mapping (what to replace):

ml-*  →  ms-*   (margin-left  → margin-start)
mr-*  →  me-*   (margin-right → margin-end)
pl-*  →  ps-*   (padding-left  → padding-start)
pr-*  →  pe-*   (padding-right → padding-end)

left-*   →  start-*  (position left  → position start)
right-*  →  end-*    (position right → position end)

border-l-*  →  border-s-*  (border-left → border-start)
border-r-*  →  border-e-*  (border-right → border-end)

text-left   →  text-start
text-right  →  text-end

rounded-l-*  →  rounded-s-*
rounded-r-*  →  rounded-e-*

VARIANT prefixes (for direction-specific overrides):
  rtl:mr-4     — applies mr-4 only in RTL mode
  ltr:ml-4     — applies ml-4 only in LTR mode

STRATEGY:
  1. First pass: replace physical with logical properties where possible
  2. Second pass: use rtl:/ltr: variants for cases where logical properties don't apply
  3. Third pass: use rtl.css for edge cases neither approach covers
```

---

## Appendix B — Component RTL Checklist

Use this checklist when patching each component:

```
[ ] Replace ml-*/mr-* with ms-*/me-*
[ ] Replace pl-*/pr-* with ps-*/pe-*
[ ] Replace left-*/right-* positioning with start-*/end-*
[ ] Replace border-l-*/border-r-* with border-s-*/border-e-*
[ ] Replace text-left/text-right with text-start/text-end
[ ] Replace rounded-l-*/rounded-r-* with rounded-s-*/rounded-e-*
[ ] Wrap directional icons with DirectionalIcon
[ ] Wrap mixed-content text with BiDirectionalText
[ ] Number inputs have dir="ltr" or class="technical-value"
[ ] Verify flex/grid layouts flow naturally with dir change
[ ] Check absolute/fixed positioned children use start/end
[ ] Test with i18n.language = "fa" in dev tools
```

---

## Appendix C — Testing RTL Manually

```bash
# Quick manual RTL test without starting full app:
# Open browser console on any page and run:
document.documentElement.dir = "rtl"
document.documentElement.lang = "fa"

# To revert:
document.documentElement.dir = "ltr"
document.documentElement.lang = "en"

# This tests CSS-level RTL but NOT React re-renders or i18n translations.
# For full testing, use the LanguageToggle component.
```
