# SESSION 21 SPEC — Reading Results Display

**Block:** Frontend Core (Sessions 19-25)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 20 (Oracle Main Page), Session 10 (FC60 Stamp Display engine)

---

## TL;DR

- Rewrite `ReadingResults.tsx` from a minimal 3-tab shell into a rich, section-based reading display with 9 distinct content sections
- Create new components: `ReadingSection`, `NumerologyNumberDisplay`, `PatternBadge`, `ReadingHeader`, `ReadingFooter`, and `ShareButton`
- Each reading section renders as its own card with scroll-reveal animation and proper i18n (EN/FA with RTL)
- Add print-friendly CSS (`@media print`) for clean printed readings
- Add share functionality (copy-to-clipboard text summary generation)

---

## OBJECTIVES

1. Build a beautiful, section-based reading results display showing all 9 Oracle reading sections (Header, Universal Address, Core Identity, Right Now, Patterns, The Message, Today's Advice, Caution, Footer)
2. Create reusable `NumerologyNumberDisplay` component that renders large styled numerology numbers with meaning text (e.g., "Life Path 7 — The Seeker")
3. Create `PatternBadge` component to display detected patterns with color-coded priority levels
4. Implement `ReadingHeader` with person name, date, and confidence badge
5. Implement `ReadingFooter` with confidence score meter and disclaimer text
6. Add `ShareButton` that generates a shareable plain-text summary and copies to clipboard
7. Add `@media print` CSS for clean printed output across all section cards
8. Ensure all text renders RTL with optional Persian numerals when locale is FA
9. Maintain existing tab structure (Summary/Details/History) but replace Summary tab content with the new sectioned layout
10. Write 12+ tests covering all sections, Persian rendering, print styles, and share functionality

---

## PREREQUISITES

- [ ] Session 20 completed — Oracle page renders with `ReadingResults` component
  - Verify: `grep -r "ReadingResults" frontend/src/pages/Oracle.tsx` returns import + usage
- [ ] Existing `ConsultationResult` type defined in `frontend/src/types/index.ts`
  - Verify: `grep "ConsultationResult" frontend/src/types/index.ts` returns the union type
- [ ] Tailwind config has `nps-oracle-*` theme tokens
  - Verify: `grep "oracle" frontend/tailwind.config.ts` returns oracle color definitions
- [ ] i18n setup exists with `useTranslation` hook working
  - Verify: `grep "useTranslation" frontend/src/components/oracle/SummaryTab.tsx` returns import
- [ ] Node.js 18+ and npm available
  - Verify: `node --version && npm --version`
- [ ] Frontend dependencies installed
  - Verify: `ls frontend/node_modules/.package-lock.json`

---

## FILES TO CREATE

- `frontend/src/components/oracle/ReadingSection.tsx` — Reusable card wrapper for each reading section with scroll-reveal animation, collapsible behavior, and icon support
- `frontend/src/components/oracle/NumerologyNumberDisplay.tsx` — Large styled numerology number with meaning text below; supports Life Path, Expression, Soul Urge, Personality
- `frontend/src/components/oracle/PatternBadge.tsx` — Color-coded badge for detected patterns with priority levels (high/medium/low)
- `frontend/src/components/oracle/ReadingHeader.tsx` — Top banner: person name, reading date, reading type badge, confidence indicator
- `frontend/src/components/oracle/ReadingFooter.tsx` — Bottom section: confidence score bar, framework attribution, disclaimer text
- `frontend/src/components/oracle/ShareButton.tsx` — Button that generates plain-text summary of reading and copies to clipboard with toast feedback
- `frontend/src/components/oracle/__tests__/ReadingSection.test.tsx` — Tests for section card rendering, collapse toggle, animation classes
- `frontend/src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx` — Tests for number display, meaning text, Persian numeral conversion
- `frontend/src/components/oracle/__tests__/PatternBadge.test.tsx` — Tests for priority color mapping, text rendering
- `frontend/src/components/oracle/__tests__/ReadingHeader.test.tsx` — Tests for name display, date formatting, confidence badge
- `frontend/src/components/oracle/__tests__/ReadingFooter.test.tsx` — Tests for confidence bar, disclaimer text
- `frontend/src/components/oracle/__tests__/ShareButton.test.tsx` — Tests for clipboard copy, text generation
- `frontend/src/styles/print.css` — Print-specific styles for clean reading output

---

## FILES TO MODIFY

- `frontend/src/components/oracle/ReadingResults.tsx` — Integrate new section-based layout into Summary tab; add ShareButton next to ExportButton
- `frontend/src/components/oracle/SummaryTab.tsx` — Rewrite to use the 9 new sections (ReadingHeader, ReadingSection cards, ReadingFooter) instead of current flat layout
- `frontend/src/components/oracle/DetailsTab.tsx` — Minor: add NumerologyNumberDisplay for numerology values instead of plain DataRow
- `frontend/src/components/oracle/__tests__/ReadingResults.test.tsx` — Extend with tests for new sections rendering, share button presence
- `frontend/src/components/oracle/__tests__/SummaryTab.test.tsx` — Rewrite to test section-based layout
- `frontend/tailwind.config.ts` — Add animation utility for scroll-reveal (`animate-fade-in-up`)
- `frontend/src/main.tsx` — Import `print.css` globally

---

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: Foundation Components (60 minutes)

**Tasks:**

1. Create `ReadingSection.tsx` — A card wrapper component:
   - Props: `title: string`, `icon?: string`, `children: ReactNode`, `defaultOpen?: boolean`, `priority?: 'high' | 'medium' | 'low'`, `className?: string`
   - Renders a bordered card with header (icon + title) and collapsible body
   - Uses Tailwind classes matching existing `nps-oracle-*` theme tokens
   - Supports RTL via `useTranslation` direction detection

2. Create `NumerologyNumberDisplay.tsx`:
   - Props: `number: number`, `label: string`, `meaning: string`, `size?: 'sm' | 'md' | 'lg'`
   - Renders large number (e.g., `text-4xl font-mono font-bold`) with label above and meaning below
   - When locale is FA, converts digits to Persian numerals (۰-۹)
   - Color-codes master numbers (11, 22, 33) with `nps-gold` accent

3. Create `PatternBadge.tsx`:
   - Props: `pattern: string`, `priority: 'high' | 'medium' | 'low'`, `description?: string`
   - Maps priority to colors: high → `nps-error`, medium → `nps-warning`, low → `nps-success`
   - Renders as inline badge with optional tooltip for description

4. Add `animate-fade-in-up` to Tailwind config:
   ```typescript
   // In tailwind.config.ts extend.animation
   'fade-in-up': 'fadeInUp 0.4s ease-out forwards',
   // In extend.keyframes
   fadeInUp: {
     '0%': { opacity: '0', transform: 'translateY(12px)' },
     '100%': { opacity: '1', transform: 'translateY(0)' },
   }
   ```

**Code Pattern — ReadingSection:**

```typescript
interface ReadingSectionProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  priority?: "high" | "medium" | "low";
  className?: string;
}

export function ReadingSection({
  title,
  icon,
  children,
  defaultOpen = true,
  priority,
  className = "",
}: ReadingSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  // ... renders card with nps-oracle-bg/border theme
}
```

**Code Pattern — NumerologyNumberDisplay:**

```typescript
interface NumerologyNumberDisplayProps {
  number: number;
  label: string;
  meaning: string;
  size?: "sm" | "md" | "lg";
}

export function NumerologyNumberDisplay({
  number,
  label,
  meaning,
  size = "md",
}: NumerologyNumberDisplayProps) {
  const { i18n } = useTranslation();
  const displayNumber =
    i18n.language === "fa" ? toPersianDigits(number) : String(number);
  // ... renders large styled number
}
```

**Checkpoint:**

- [ ] `ReadingSection` renders a collapsible card with title and children
- [ ] `NumerologyNumberDisplay` renders number with label and meaning
- [ ] `PatternBadge` renders with correct priority colors
- [ ] Tailwind config includes `animate-fade-in-up`
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | head -5` — expect no errors
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/ReadingSection.test.tsx src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx src/components/oracle/__tests__/PatternBadge.test.tsx 2>&1 | tail -10`

🚨 STOP if checkpoint fails

---

### Phase 2: Header and Footer Components (45 minutes)

**Tasks:**

1. Create `ReadingHeader.tsx`:
   - Props: `userName: string`, `readingDate: string`, `readingType: ConsultationResult['type']`, `confidence?: number`
   - Renders person name prominently with `text-lg font-semibold text-nps-text-bright`
   - Date formatted via `toLocaleDateString()` respecting locale
   - Reading type shown as colored badge (reuse badge pattern from existing `SummaryTab.tsx` `getTypeBadge()`)
   - Confidence shown as small pill: green (>0.7), yellow (0.4-0.7), red (<0.4)

2. Create `ReadingFooter.tsx`:
   - Props: `confidence: number`, `generatedAt?: string`, `frameworkVersion?: string`
   - Confidence score displayed as a horizontal bar (gradient from red → yellow → green)
   - Percentage text next to bar
   - Disclaimer: "This reading is for entertainment and personal reflection purposes only."
   - Framework attribution: "Powered by NPS Numerology Framework"
   - All text translatable via i18n

**Code Pattern — ReadingHeader:**

```typescript
interface ReadingHeaderProps {
  userName: string;
  readingDate: string;
  readingType: "reading" | "question" | "name";
  confidence?: number;
}

export function ReadingHeader({
  userName,
  readingDate,
  readingType,
  confidence,
}: ReadingHeaderProps) {
  const { t } = useTranslation();
  // ... renders header banner
}
```

**Code Pattern — ReadingFooter:**

```typescript
interface ReadingFooterProps {
  confidence: number;
  generatedAt?: string;
}

export function ReadingFooter({ confidence, generatedAt }: ReadingFooterProps) {
  const { t } = useTranslation();
  const barWidth = `${Math.round(confidence * 100)}%`;
  const barColor =
    confidence > 0.7
      ? "bg-nps-success"
      : confidence > 0.4
        ? "bg-nps-warning"
        : "bg-nps-error";
  // ... renders confidence bar + disclaimer
}
```

**Checkpoint:**

- [ ] `ReadingHeader` shows name, date, type badge, confidence pill
- [ ] `ReadingFooter` shows confidence bar and disclaimer
- [ ] Both components use i18n for all text
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/ReadingHeader.test.tsx src/components/oracle/__tests__/ReadingFooter.test.tsx 2>&1 | tail -10`

🚨 STOP if checkpoint fails

---

### Phase 3: Rewrite SummaryTab with 9 Sections (90 minutes)

**Tasks:**

1. Rewrite `SummaryTab.tsx` to display a reading result as 9 ordered sections using `ReadingSection` cards:

   **Section 1 — Header (ReadingHeader):**
   - Person name, date, confidence badge
   - Use `result.data.generated_at` for date

   **Section 2 — Universal Address:**
   - FC60 stamp from `result.data.fc60_extended.stamp`
   - Weekday name, planet, domain from `fc60_extended`
   - Styled in monospace font (`font-mono`) for stamp display

   **Section 3 — Core Identity:**
   - Numerology numbers using `NumerologyNumberDisplay`: Life Path, Day Vibration, Personal Year
   - From `result.data.numerology`
   - Horizontal grid of 3-4 numbers

   **Section 4 — Right Now:**
   - Current planet from `fc60_extended.weekday_planet`
   - Moon phase from `result.data.moon` (emoji + phase name + illumination)
   - Hour energy from `result.data.fc60.energy_level`
   - Ganzhi data from `result.data.ganzhi` (hour animal, hour branch)

   **Section 5 — Patterns:**
   - Display `result.data.synchronicities` as `PatternBadge` components
   - If no patterns, show "No synchronicities detected" message
   - Angel number matches from `result.data.angel`

   **Section 6 — The Message (Synthesis):**
   - AI interpretation from `result.data.ai_interpretation`
   - If present, render in larger text (`text-base`) with left border accent
   - Use `TranslatedReading` component for translation support
   - Highlighted with `bg-nps-oracle-accent/5` background

   **Section 7 — Today's Advice:**
   - Extract from `result.data.summary` — the main summary text
   - Render with `TranslatedReading` component
   - Styled with subtle border-left accent line

   **Section 8 — Caution (Shadow Warnings):**
   - Element balance warnings from `result.data.fc60.element_balance` (if any element is 0 or dominant >3)
   - Render in subtle red-amber tones (`text-nps-warning`, `border-nps-error/30`)
   - Only show if there are warnings to display; otherwise hide section entirely

   **Section 9 — Footer (ReadingFooter):**
   - Confidence score and disclaimer

2. For `question` type results: show simplified layout (question, answer, confidence, interpretation) — keep existing behavior from current SummaryTab but wrap in ReadingSection cards

3. For `name` type results: show simplified layout (destiny, soul urge, personality, letter table, interpretation) — keep existing behavior but wrap in ReadingSection cards

**Code Pattern — SummaryTab section ordering for reading type:**

```typescript
export function SummaryTab({ result }: SummaryTabProps) {
  if (!result) return <Placeholder />;

  if (result.type === 'reading') {
    return <ReadingSummary result={result} />;
  }
  if (result.type === 'question') {
    return <QuestionSummary result={result} />;
  }
  return <NameSummary result={result} />;
}

function ReadingSummary({ result }: { result: Extract<ConsultationResult, { type: 'reading' }> }) {
  const { data } = result;
  return (
    <div className="space-y-4">
      <ReadingHeader userName="..." readingDate={data.generated_at} readingType="reading" />
      <ReadingSection title="Universal Address" icon="...">
        {/* FC60 stamp display */}
      </ReadingSection>
      <ReadingSection title="Core Identity" icon="...">
        <div className="grid grid-cols-3 gap-4">
          <NumerologyNumberDisplay number={data.numerology.life_path} label="Life Path" meaning="..." />
          {/* ... */}
        </div>
      </ReadingSection>
      {/* ... remaining sections */}
      <ReadingFooter confidence={0.85} generatedAt={data.generated_at} />
    </div>
  );
}
```

**Checkpoint:**

- [ ] Reading type shows all 9 sections in order
- [ ] Numerology numbers display large with meanings
- [ ] FC60 stamp shows in monospace
- [ ] Moon phase shows emoji + name
- [ ] Patterns show as badges
- [ ] AI interpretation highlighted
- [ ] Caution section only appears when relevant
- [ ] Question and Name types render correctly with section cards
- [ ] No TypeScript errors
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | head -5`
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/SummaryTab.test.tsx 2>&1 | tail -20`

🚨 STOP if checkpoint fails

---

### Phase 4: Share Button & Print Styles (45 minutes)

**Tasks:**

1. Create `ShareButton.tsx`:
   - Props: `result: ConsultationResult`
   - On click: generates a plain-text summary of the reading
   - Copies to clipboard using `navigator.clipboard.writeText()`
   - Shows brief "Copied!" feedback (2 seconds) via local state toggle
   - Text format:

     ```
     NPS Oracle Reading
     Date: [date]
     Type: [reading/question/name]

     [Summary text]

     Life Path: [N] | Element: [X] | Energy: [N]
     Moon: [emoji] [phase]

     — Generated by NPS Numerology Framework
     ```

2. Create `frontend/src/styles/print.css`:
   - Hide navigation sidebar, top bar, tabs, buttons (export/share/collapse toggles)
   - Show all reading sections expanded (no collapse)
   - Black text on white background
   - Clean margins and padding
   - Page break rules: `page-break-inside: avoid` on ReadingSection cards
   - Remove background colors and borders (except subtle section separators)
   - Show confidence as text instead of bar
   - Hide caution border colors (print as plain text)

3. Import `print.css` in `frontend/src/main.tsx`

4. Add ShareButton to `ReadingResults.tsx` next to existing ExportButton

**Code Pattern — ShareButton:**

```typescript
interface ShareButtonProps {
  result: ConsultationResult;
}

export function ShareButton({ result }: ShareButtonProps) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    const text = generateShareText(result);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button type="button" onClick={handleShare} className="...">
      {copied ? t('oracle.copied') : t('oracle.share')}
    </button>
  );
}
```

**Code Pattern — print.css:**

```css
@media print {
  /* Hide non-content elements */
  nav,
  [role="tablist"],
  .export-actions,
  .share-button {
    display: none !important;
  }

  /* Force white background */
  body,
  .oracle-page,
  [class*="nps-oracle-bg"] {
    background: white !important;
    color: black !important;
  }

  /* Expand all sections */
  [data-reading-section] {
    display: block !important;
  }

  /* Clean card styles */
  [data-reading-section] {
    border: 1px solid #ddd !important;
    page-break-inside: avoid;
    margin-bottom: 1rem;
  }
}
```

**Checkpoint:**

- [ ] Share button generates text summary and copies to clipboard
- [ ] "Copied!" feedback appears for 2 seconds
- [ ] Print preview (Cmd+P) shows clean reading without UI chrome
- [ ] All sections visible in print (no collapsed sections)
- [ ] Print uses black on white
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/ShareButton.test.tsx 2>&1 | tail -10`

🚨 STOP if checkpoint fails

---

### Phase 5: Persian/RTL Support & Integration (45 minutes)

**Tasks:**

1. Add helper function `toPersianDigits(n: number): string` in a shared utils file or inline:
   - Maps 0-9 → ۰-۹
   - Used by `NumerologyNumberDisplay` when locale is FA

2. Verify all new components respect RTL:
   - `ReadingSection` title and icon flip correctly
   - `NumerologyNumberDisplay` text alignment works in RTL
   - `PatternBadge` layout doesn't break in RTL
   - `ReadingHeader` name display works for Persian names
   - `ReadingFooter` confidence bar direction stays LTR (numbers always left-to-right)

3. Add i18n keys for all new text strings:
   - `oracle.section_universal_address`
   - `oracle.section_core_identity`
   - `oracle.section_right_now`
   - `oracle.section_patterns`
   - `oracle.section_message`
   - `oracle.section_advice`
   - `oracle.section_caution`
   - `oracle.confidence_label`
   - `oracle.disclaimer`
   - `oracle.share`
   - `oracle.copied`
   - `oracle.no_patterns`
   - `oracle.powered_by`
   - `oracle.master_number` (for 11, 22, 33)
   - `oracle.life_path_meaning`, `oracle.expression_meaning`, `oracle.soul_urge_meaning`

4. Integrate all components into the existing `Oracle.tsx` flow:
   - `ReadingResults` still receives `result: ConsultationResult | null`
   - When a reading result arrives from the consultation form, the new sectioned Summary tab renders automatically
   - Existing History and Details tabs remain unchanged (Details tab gets minor NumerologyNumberDisplay enhancement)

5. Update `DetailsTab.tsx` to use `NumerologyNumberDisplay` for numerology values instead of plain `DataRow`

**Checkpoint:**

- [ ] Setting locale to FA shows Persian numerals in NumerologyNumberDisplay
- [ ] RTL layout renders correctly for all new components
- [ ] All i18n keys have English values (Persian translations can be placeholder strings for now)
- [ ] DetailsTab uses NumerologyNumberDisplay for numerology numbers
- [ ] Full flow works: submit reading → see new sectioned results
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | head -5`

🚨 STOP if checkpoint fails

---

### Phase 6: Comprehensive Testing (45 minutes)

**Tasks:**

1. Write/update test files:

   **`ReadingSection.test.tsx`** (3 tests):
   - Renders title and children
   - Collapses/expands on header click
   - Applies priority border color

   **`NumerologyNumberDisplay.test.tsx`** (3 tests):
   - Renders number, label, and meaning
   - Converts to Persian digits when locale is FA
   - Highlights master numbers (11, 22, 33)

   **`PatternBadge.test.tsx`** (2 tests):
   - Renders pattern text
   - Applies correct color class per priority

   **`ReadingHeader.test.tsx`** (2 tests):
   - Shows user name and formatted date
   - Shows confidence pill with correct color

   **`ReadingFooter.test.tsx`** (2 tests):
   - Renders confidence bar at correct width
   - Shows disclaimer text

   **`ShareButton.test.tsx`** (2 tests):
   - Calls clipboard.writeText with generated summary
   - Shows "Copied!" text after click

   **`SummaryTab.test.tsx`** (update, 4 tests):
   - Reading type shows all 9 sections
   - Question type shows simplified sections
   - Name type shows simplified sections
   - Shows placeholder when no result

   **`ReadingResults.test.tsx`** (update, 2 additional tests):
   - Share button appears when result exists
   - Share button hidden when no result

2. Run full test suite and ensure all pass

**Checkpoint:**

- [ ] All 12+ new/updated tests pass
- [ ] No console errors or warnings during tests
- [ ] TypeScript compiles cleanly
- Verify: `cd frontend && npx vitest run --reporter=verbose 2>&1 | tail -30`

🚨 STOP if checkpoint fails

---

### Phase 7: Final Verification (30 minutes)

**Tasks:**

1. Run TypeScript check: `cd frontend && npx tsc --noEmit`
2. Run linter: `cd frontend && npx eslint src/components/oracle/ --ext .ts,.tsx`
3. Run all tests: `cd frontend && npx vitest run`
4. Verify print output manually (or describe verification steps)
5. Verify all components match existing theme (nps-oracle-\* colors, font-mono for stamps, font-sans for body)
6. Check no `any` types were introduced
7. Verify no new dependencies were installed (all components use existing React, Tailwind, react-i18next)

**Checkpoint:**

- [ ] `npx tsc --noEmit` exits 0
- [ ] `npx vitest run` — all tests pass, 0 failures
- [ ] No `any` type in any new file: `grep -r ": any" frontend/src/components/oracle/ReadingSection.tsx frontend/src/components/oracle/NumerologyNumberDisplay.tsx frontend/src/components/oracle/PatternBadge.tsx frontend/src/components/oracle/ReadingHeader.tsx frontend/src/components/oracle/ReadingFooter.tsx frontend/src/components/oracle/ShareButton.tsx` returns empty
- [ ] Print CSS imported: `grep "print.css" frontend/src/main.tsx` returns import line
- Verify all: `cd frontend && npx tsc --noEmit && npx vitest run --reporter=verbose 2>&1 | tail -20`

🚨 STOP if checkpoint fails — fix before marking session complete

---

## TESTS TO WRITE

- `frontend/src/components/oracle/__tests__/ReadingSection.test.tsx::renders title and children` — Section card shows title text and renders child content
- `frontend/src/components/oracle/__tests__/ReadingSection.test.tsx::collapses and expands on click` — Clicking header toggles body visibility
- `frontend/src/components/oracle/__tests__/ReadingSection.test.tsx::applies priority border color` — High priority gets error border, low gets success
- `frontend/src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx::renders number label and meaning` — Shows "7" with "Life Path" and "The Seeker"
- `frontend/src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx::converts to Persian digits when locale is fa` — Shows ۷ instead of 7
- `frontend/src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx::highlights master numbers` — 11, 22, 33 get gold accent color
- `frontend/src/components/oracle/__tests__/PatternBadge.test.tsx::renders pattern text` — Shows pattern name inside badge
- `frontend/src/components/oracle/__tests__/PatternBadge.test.tsx::applies correct color per priority` — High=red, medium=yellow, low=green classes
- `frontend/src/components/oracle/__tests__/ReadingHeader.test.tsx::shows user name and date` — Renders name prominently with formatted date
- `frontend/src/components/oracle/__tests__/ReadingHeader.test.tsx::shows confidence pill` — Confidence > 0.7 shows green pill
- `frontend/src/components/oracle/__tests__/ReadingFooter.test.tsx::renders confidence bar` — Bar width matches confidence percentage
- `frontend/src/components/oracle/__tests__/ReadingFooter.test.tsx::shows disclaimer` — Disclaimer text present in DOM
- `frontend/src/components/oracle/__tests__/ShareButton.test.tsx::copies text to clipboard` — navigator.clipboard.writeText called with summary
- `frontend/src/components/oracle/__tests__/ShareButton.test.tsx::shows copied feedback` — Button text changes to "Copied!" after click
- `frontend/src/components/oracle/__tests__/SummaryTab.test.tsx::reading type shows all 9 sections` — All section titles present for reading result
- `frontend/src/components/oracle/__tests__/SummaryTab.test.tsx::question type shows simplified sections` — Question-specific layout renders
- `frontend/src/components/oracle/__tests__/ReadingResults.test.tsx::share button appears with result` — ShareButton visible when result is provided
- `frontend/src/components/oracle/__tests__/ReadingResults.test.tsx::share button hidden without result` — ShareButton not in DOM when result is null

---

## ACCEPTANCE CRITERIA

- [ ] Full reading displays all 9 sections in correct order (Header → Universal Address → Core Identity → Right Now → Patterns → Message → Advice → Caution → Footer)
- [ ] Numerology numbers (Life Path, Day Vibration, Personal Year) render large and styled with meanings
- [ ] FC60 stamp displays in monospace font
- [ ] Moon phase shows with emoji and illumination percentage
- [ ] Detected patterns render as color-coded priority badges
- [ ] AI interpretation highlighted in accent background
- [ ] Caution section only visible when element balance warnings exist
- [ ] Share button copies text summary to clipboard with "Copied!" feedback
- [ ] Print (Cmd+P / Ctrl+P) shows clean reading: white bg, no nav, all sections expanded
- [ ] Persian mode: numerals convert to ۰-۹, layout flips RTL
- [ ] Existing tabs (Summary/Details/History) still work — Details and History unchanged
- [ ] 18+ tests pass with zero failures
- [ ] No TypeScript errors (`npx tsc --noEmit` exits 0)
- [ ] No `any` types in any new file
- [ ] No new npm dependencies required
- Verify all: `cd frontend && npx tsc --noEmit && npx vitest run 2>&1 | tail -5`

---

## ERROR SCENARIOS

### Problem: `result.data.fc60_extended` is null (no FC60 stamp data)

**Fix:** Guard all FC60 extended fields with conditional rendering. Universal Address section shows "FC60 data unavailable" placeholder when `fc60_extended` is null. This matches the existing pattern in `DetailsTab.tsx` where every section checks for null before rendering.

### Problem: `navigator.clipboard.writeText` fails (insecure context or denied permission)

**Fix:** Wrap clipboard call in try/catch. On failure, fall back to creating a temporary `<textarea>`, selecting its content, and using `document.execCommand('copy')`. If both fail, show a toast saying "Copy failed — please copy manually" and render the text in a selectable `<pre>` block.

### Problem: Tailwind animation class not applying (fade-in-up not working)

**Fix:** Verify `tailwind.config.ts` has the `animation` and `keyframes` extensions under `theme.extend`. Run `npx tailwindcss --content ./src/**/*.tsx --output /dev/null` to confirm class generation. If class still missing, fall back to inline CSS transition as temporary workaround.

### Problem: Print CSS not loading or overriding screen styles

**Fix:** Ensure `print.css` uses `@media print { }` wrapper for all rules. Verify import order in `main.tsx` — print CSS must come after Tailwind base styles. Use `!important` sparingly and only for overriding deeply nested Tailwind utilities. Test with browser print preview (Cmd+P).

---

## HANDOFF

**Created:**

- `frontend/src/components/oracle/ReadingSection.tsx`
- `frontend/src/components/oracle/NumerologyNumberDisplay.tsx`
- `frontend/src/components/oracle/PatternBadge.tsx`
- `frontend/src/components/oracle/ReadingHeader.tsx`
- `frontend/src/components/oracle/ReadingFooter.tsx`
- `frontend/src/components/oracle/ShareButton.tsx`
- `frontend/src/styles/print.css`
- `frontend/src/components/oracle/__tests__/ReadingSection.test.tsx`
- `frontend/src/components/oracle/__tests__/NumerologyNumberDisplay.test.tsx`
- `frontend/src/components/oracle/__tests__/PatternBadge.test.tsx`
- `frontend/src/components/oracle/__tests__/ReadingHeader.test.tsx`
- `frontend/src/components/oracle/__tests__/ReadingFooter.test.tsx`
- `frontend/src/components/oracle/__tests__/ShareButton.test.tsx`

**Modified:**

- `frontend/src/components/oracle/ReadingResults.tsx`
- `frontend/src/components/oracle/SummaryTab.tsx`
- `frontend/src/components/oracle/DetailsTab.tsx`
- `frontend/src/components/oracle/__tests__/ReadingResults.test.tsx`
- `frontend/src/components/oracle/__tests__/SummaryTab.test.tsx`
- `frontend/tailwind.config.ts`
- `frontend/src/main.tsx`

**Deleted:**

- None

**Next session (Session 22 — Dashboard Page) needs:**

- All reading result components from this session working and tested
- The `ReadingSection` component is reusable and can be used for Dashboard widgets
- The `NumerologyNumberDisplay` component can be reused in Dashboard stats
- i18n keys established in this session for section titles and labels
- Print CSS pattern can be extended for Dashboard print view
- Session 22 will build: Welcome banner, daily reading card, recent readings grid (using data from oracle history API), statistics cards, quick action buttons, moon phase widget
