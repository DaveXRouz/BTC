# SESSION 28 SPEC: Accessibility (a11y)

**Block:** Frontend Advanced (Sessions 26-31)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium-High
**Dependencies:** Sessions 26-27 (RTL + responsive)

---

## TL;DR

- Achieve WCAG 2.1 AA compliance across the entire NPS frontend
- Add keyboard navigation: logical tab order, Enter/Space activation, arrow-key tab switching, focus trapping in dialogs
- Install axe-core for automated accessibility auditing in tests
- Add skip-navigation link for keyboard users to jump past the sidebar
- Add visible focus indicators (ring styles) on all interactive elements via global CSS
- Fix ARIA gaps: missing labels, missing `role`/`aria-*` attributes, missing `lang` attributes for Persian text
- Add `aria-live` regions for dynamic content (loading states, error messages, reading results)
- Verify color contrast meets 4.5:1 for normal text, 3:1 for large text
- Rewrite `Accessibility.test.tsx` with comprehensive 30+ test suite using axe-core + keyboard simulation

---

## OBJECTIVES

1. Every interactive element is keyboard-focusable with a visible focus indicator
2. Tab order follows logical reading order (sidebar nav top-to-bottom, then main content)
3. Dialogs (UserForm, PersianKeyboard) trap focus inside and return focus on close
4. All form inputs have programmatically-associated labels (htmlFor/id or aria-label)
5. Error messages are announced to screen readers via `role="alert"` or `aria-live`
6. Dynamic content changes (loading, results, tab switches) are announced via `aria-live` regions
7. Color contrast meets WCAG AA: 4.5:1 for normal text, 3:1 for large text and UI components
8. Persian text sections have `lang="fa"` attribute for screen reader pronunciation
9. Skip-navigation link lets keyboard users bypass the sidebar
10. axe-core integration catches regressions automatically in CI
11. Zero critical or serious axe-core violations across all pages

---

## PREREQUISITES

- [ ] Layout with sidebar navigation exists (`frontend/src/components/Layout.tsx`)
- [ ] Oracle components exist with partial ARIA support
- [ ] i18n with RTL support exists (`frontend/src/App.tsx` sets `dir` and `lang`)
- [ ] Vitest + React Testing Library test infrastructure exists

Verification:

```bash
test -f frontend/src/components/Layout.tsx && echo "OK" || echo "MISSING"
test -f frontend/src/components/oracle/UserForm.tsx && echo "OK" || echo "MISSING"
test -f frontend/src/components/oracle/ReadingResults.tsx && echo "OK" || echo "MISSING"
test -f frontend/src/components/oracle/__tests__/Accessibility.test.tsx && echo "OK" || echo "MISSING"
test -f frontend/vitest.config.ts && echo "OK" || echo "MISSING"
```

---

## FILES TO CREATE

- `frontend/src/hooks/useFocusTrap.ts` -- Reusable focus trap hook for dialogs
- `frontend/src/hooks/useArrowNavigation.ts` -- Arrow key navigation for tablists, radio groups, menus
- `frontend/src/components/SkipNavLink.tsx` -- Skip-to-content link component
- `frontend/src/components/__tests__/SkipNavLink.test.tsx` -- Skip nav tests
- `frontend/src/hooks/__tests__/useFocusTrap.test.ts` -- Focus trap hook tests
- `frontend/src/hooks/__tests__/useArrowNavigation.test.ts` -- Arrow nav hook tests

## FILES TO MODIFY

| File                                                              | Current Lines | Action  | Notes                                                                                                           |
| ----------------------------------------------------------------- | ------------- | ------- | --------------------------------------------------------------------------------------------------------------- |
| `frontend/src/index.css`                                          | 39            | MODIFY  | Add focus indicator styles, skip-nav styles, reduced-motion media query                                         |
| `frontend/src/components/Layout.tsx`                              | 57            | MODIFY  | Add skip-nav link, `<nav aria-label>`, landmark roles, `role="navigation"`                                      |
| `frontend/src/components/LanguageToggle.tsx`                      | 39            | MODIFY  | Add `aria-pressed` for toggle state                                                                             |
| `frontend/src/components/StatsCard.tsx`                           | 23            | MODIFY  | Add `role="group"` and `aria-label`                                                                             |
| `frontend/src/components/LogPanel.tsx`                            | 51            | MODIFY  | Add `role="log"` and `aria-live="polite"` and `aria-label`                                                      |
| `frontend/src/components/oracle/UserForm.tsx`                     | 261           | MODIFY  | Add focus trap, Escape to close, return focus on unmount, focus first field on open                             |
| `frontend/src/components/oracle/PersianKeyboard.tsx`              | 91            | MODIFY  | Add focus trap, `role="dialog"`, keyboard grid navigation                                                       |
| `frontend/src/components/oracle/OracleConsultationForm.tsx`       | 150           | MODIFY  | Link label to textarea via id, add `aria-describedby` for sign error, add `aria-required` on sign               |
| `frontend/src/components/oracle/ReadingResults.tsx`               | 79            | MODIFY  | Add arrow-key navigation for tabs, `tabIndex` management, `aria-live` for panel changes                         |
| `frontend/src/components/oracle/SignTypeSelector.tsx`             | 104           | MODIFY  | Link label to select via id, add `aria-required`, add `aria-describedby` for error, add `role="alert"` on error |
| `frontend/src/components/oracle/LocationSelector.tsx`             | 107           | MODIFY  | Link label to elements, add `aria-busy` on detect button, add `role="alert"` on error                           |
| `frontend/src/components/oracle/CalendarPicker.tsx`               | 245           | MODIFY  | Add `role="dialog"` on dropdown, `role="grid"` on day grid, `aria-label` on day buttons, focus trap when open   |
| `frontend/src/components/oracle/MultiUserSelector.tsx`            | 203           | MODIFY  | Add `role="alert"` on error, `aria-label` on add/edit buttons, label linking                                    |
| `frontend/src/components/oracle/UserSelector.tsx`                 | 72            | MODIFY  | Add `aria-label` on add/edit buttons                                                                            |
| `frontend/src/components/oracle/UserChip.tsx`                     | 32            | MODIFY  | Already has good `aria-label` on remove -- add `role="listitem"` context                                        |
| `frontend/src/components/oracle/TranslatedReading.tsx`            | 73            | MODIFY  | Add `aria-live="polite"` for translation result, `aria-busy` on translate, `lang="fa"` on Persian text          |
| `frontend/src/components/oracle/ExportButton.tsx`                 | 84            | MODIFY  | Add `aria-label` on export buttons                                                                              |
| `frontend/src/components/oracle/ReadingHistory.tsx`               | 134           | MODIFY  | Add `role="listbox"` pattern for filter chips, `aria-expanded` on expandable items, `aria-label` on load more   |
| `frontend/src/components/oracle/SummaryTab.tsx`                   | ~varies       | MODIFY  | Add `lang="fa"` on Persian interpretation blocks                                                                |
| `frontend/src/components/oracle/DetailsTab.tsx`                   | ~varies       | MODIFY  | Add `lang="fa"` on Persian content blocks                                                                       |
| `frontend/src/components/oracle/__tests__/Accessibility.test.tsx` | 142           | REWRITE | Comprehensive 30+ test suite with axe-core                                                                      |
| `frontend/src/App.tsx`                                            | 34            | VERIFY  | Already sets `dir` and `lang` on `<html>` -- no changes needed                                                  |
| `frontend/tailwind.config.ts`                                     | 62            | MODIFY  | Add `ring` color utilities for focus indicators matching theme                                                  |

---

## PHASE 1: Install axe-core & Focus Ring Foundation

### 1.1 Install axe-core for Testing

```bash
cd frontend && npm install --save-dev axe-core @axe-core/react vitest-axe
```

> **Note:** `vitest-axe` provides `toHaveNoViolations()` matcher for Vitest. If `vitest-axe` is not available as a package, use `axe-core` directly with a custom matcher wrapper.

Add to `frontend/src/test/setup.ts`:

```ts
import "vitest-axe/extend-expect";
```

### 1.2 Global Focus Indicator Styles

**File:** `frontend/src/index.css`

Add after the existing styles:

```css
/* ─── Accessibility: Focus indicators ─── */

/* Visible focus ring on all interactive elements */
*:focus-visible {
  outline: 2px solid #4fc3f7; /* nps-oracle-accent */
  outline-offset: 2px;
  border-radius: 2px;
}

/* Remove default outline only when focus-visible handles it */
*:focus:not(:focus-visible) {
  outline: none;
}

/* Skip navigation link */
.skip-nav {
  position: absolute;
  top: -100%;
  left: 0;
  z-index: 100;
  padding: 0.75rem 1.5rem;
  background: #4fc3f7;
  color: #0d1117;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: none;
  border-radius: 0 0 0.5rem 0;
}

.skip-nav:focus {
  top: 0;
}

/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### 1.3 Tailwind Focus Ring Utilities

**File:** `frontend/tailwind.config.ts`

Add to `extend`:

```ts
ringColor: {
  focus: "#4fc3f7", // matches oracle accent
},
```

### Checkpoint 1

```bash
cd frontend && npx tsc --noEmit
# Verify: focus-visible styles render in browser dev tools
# Verify: reduced-motion media query present in compiled CSS
```

---

## PHASE 2: Skip Navigation & Layout Landmarks

### 2.1 SkipNavLink Component

**File:** `frontend/src/components/SkipNavLink.tsx` (NEW)

```tsx
import { useTranslation } from "react-i18next";

export function SkipNavLink() {
  const { t } = useTranslation();

  return (
    <a href="#main-content" className="skip-nav">
      {t("a11y.skip_to_content")}
    </a>
  );
}
```

### 2.2 Layout Landmark Roles

**File:** `frontend/src/components/Layout.tsx`

Changes:

1. Import and render `<SkipNavLink />` before sidebar
2. Add `aria-label={t("nav.sidebar")}` to `<nav>` element
3. Add `id="main-content"` to `<main>` element
4. Add `role="banner"` to the NPS header div inside nav
5. Wrap nav items in a `<ul>` with `role="list"` and each item in `<li>`

Target structure:

```tsx
<div className="flex min-h-screen bg-nps-bg">
  <SkipNavLink />
  <nav aria-label={t("nav.sidebar")} className="...">
    <div role="banner" className="...">
      <h1>NPS</h1>
      <LanguageToggle />
    </div>
    <ul role="list" className="flex-1 py-4">
      {navItems.map((item) => (
        <li key={item.path}>
          <NavLink to={item.path} aria-current={isActive ? "page" : undefined} ...>
            {t(item.labelKey)}
          </NavLink>
        </li>
      ))}
    </ul>
  </nav>
  <main id="main-content" className="flex-1 p-6 overflow-auto" tabIndex={-1}>
    <Outlet />
  </main>
</div>
```

> **Key:** `tabIndex={-1}` on `<main>` allows the skip link to programmatically focus it. `aria-current="page"` is added by NavLink automatically via React Router, but verify it works.

### Checkpoint 2

```bash
cd frontend && npx tsc --noEmit
# Verify: Tab → skip link appears → Enter → focus jumps to main content
# Verify: Screen reader announces "navigation, sidebar" on nav element
```

---

## PHASE 3: Focus Trap Hook & Dialog Accessibility

### 3.1 useFocusTrap Hook

**File:** `frontend/src/hooks/useFocusTrap.ts` (NEW)

Implement a hook that:

1. Accepts a ref to the container element and an `isActive` boolean
2. When active: finds all focusable elements inside the container
3. On Tab at last element: wraps to first. On Shift+Tab at first: wraps to last
4. On mount (when isActive becomes true): focuses the first focusable element
5. On unmount: returns focus to the previously focused element (captured on mount)
6. Focusable selector: `a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])`

```ts
import { useEffect, useRef } from "react";

const FOCUSABLE_SELECTOR =
  'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])';

export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement | null>,
  isActive: boolean,
) {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isActive || !containerRef.current) return;

    previousFocusRef.current = document.activeElement as HTMLElement;
    const container = containerRef.current;
    const focusableEls =
      container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
    if (focusableEls.length > 0) {
      focusableEls[0].focus();
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key !== "Tab") return;
      const focusable =
        container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    container.addEventListener("keydown", handleKeyDown);
    return () => {
      container.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [isActive, containerRef]);
}
```

### 3.2 UserForm Dialog Focus Trap

**File:** `frontend/src/components/oracle/UserForm.tsx`

Changes:

1. Import `useFocusTrap`
2. Add a ref to the inner dialog `<div>` (the one with `onClick stopPropagation`)
3. Call `useFocusTrap(dialogRef, true)` -- always active since the form is only rendered when open
4. The existing Escape-to-close behavior is handled by the backdrop click -- add explicit `onKeyDown` on the outer div: if `e.key === "Escape"`, call `onCancel()`
5. Keep existing ARIA: `role="dialog"`, `aria-modal="true"`, `aria-label`

### 3.3 PersianKeyboard Dialog Focus Trap

**File:** `frontend/src/components/oracle/PersianKeyboard.tsx`

Changes:

1. Import `useFocusTrap`
2. Apply `useFocusTrap(panelRef, true)` using the existing `panelRef`
3. Already has: `role="dialog"`, `aria-label`, Escape key handler
4. Add `aria-modal="true"` (currently missing)

### 3.4 CalendarPicker Dropdown Accessibility

**File:** `frontend/src/components/oracle/CalendarPicker.tsx`

Changes:

1. When `isOpen`, the dropdown div gets: `role="dialog"`, `aria-label={t("oracle.calendar_select_date")}`, `aria-modal="false"` (not truly modal)
2. Add `useFocusTrap` when open (wrap the dropdown container ref)
3. Add Escape key to close: `onKeyDown` handler on the dropdown div
4. Day buttons get `aria-label` with full date string: `aria-label={formatDate(cell.iso, mode)}`
5. Day grid wrapper gets `role="grid"`, week rows get `role="row"`, day cells get `role="gridcell"`
6. Selected day gets `aria-selected="true"`
7. Today's button gets `aria-current="date"`
8. Prev/Next month buttons: change hardcoded English aria-labels to i18n keys: `t("a11y.previous_month")`, `t("a11y.next_month")`

### Checkpoint 3

```bash
cd frontend && npx tsc --noEmit
# Verify: Tab cycles within UserForm dialog without escaping
# Verify: Opening UserForm focuses the Name input
# Verify: Closing UserForm returns focus to the trigger button
# Verify: PersianKeyboard traps focus, Escape closes
# Verify: CalendarPicker day buttons have date aria-labels
```

---

## PHASE 4: Tab Navigation & Arrow Keys

### 4.1 useArrowNavigation Hook

**File:** `frontend/src/hooks/useArrowNavigation.ts` (NEW)

Hook for managing arrow-key navigation within a group of elements (tabs, radio buttons, menu items).

```ts
import { useCallback } from "react";

interface ArrowNavOptions {
  orientation?: "horizontal" | "vertical";
  loop?: boolean;
}

export function useArrowNavigation(
  containerRef: React.RefObject<HTMLElement | null>,
  options: ArrowNavOptions = {},
) {
  const { orientation = "horizontal", loop = true } = options;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const container = containerRef.current;
      if (!container) return;

      const items = Array.from(
        container.querySelectorAll<HTMLElement>(
          '[role="tab"], [role="menuitem"], [role="option"]',
        ),
      );
      if (items.length === 0) return;

      const currentIndex = items.indexOf(e.target as HTMLElement);
      if (currentIndex === -1) return;

      const prevKey = orientation === "horizontal" ? "ArrowLeft" : "ArrowUp";
      const nextKey = orientation === "horizontal" ? "ArrowRight" : "ArrowDown";

      let newIndex = currentIndex;

      if (e.key === nextKey) {
        e.preventDefault();
        newIndex = loop
          ? (currentIndex + 1) % items.length
          : Math.min(currentIndex + 1, items.length - 1);
      } else if (e.key === prevKey) {
        e.preventDefault();
        newIndex = loop
          ? (currentIndex - 1 + items.length) % items.length
          : Math.max(currentIndex - 1, 0);
      } else if (e.key === "Home") {
        e.preventDefault();
        newIndex = 0;
      } else if (e.key === "End") {
        e.preventDefault();
        newIndex = items.length - 1;
      }

      if (newIndex !== currentIndex) {
        items[newIndex].focus();
        // If tab pattern, activate on focus (roving tabindex)
        items[newIndex].click();
      }
    },
    [containerRef, orientation, loop],
  );

  return { handleKeyDown };
}
```

### 4.2 ReadingResults Tab Arrow Navigation

**File:** `frontend/src/components/oracle/ReadingResults.tsx`

Changes:

1. Import `useArrowNavigation`
2. Add `useRef` for the tablist container
3. Apply `onKeyDown={handleKeyDown}` on the tablist `<div>`
4. Set `tabIndex={activeTab === tab ? 0 : -1}` on each tab button (roving tabindex pattern)
5. Add `aria-live="polite"` on the active tabpanel so screen readers announce content changes
6. Currently hidden panels use `className="hidden"` -- this is correct for a11y since hidden elements are excluded from the accessibility tree

> **Important RTL consideration:** For RTL (Persian), ArrowRight should go to the _previous_ tab and ArrowLeft to _next_. The `useArrowNavigation` hook should check `document.documentElement.dir` and reverse direction when RTL. Add this logic inside the hook.

### 4.3 ReadingHistory Filter Chips as Tabs

**File:** `frontend/src/components/oracle/ReadingHistory.tsx`

Changes:

1. Wrap filter buttons in `role="tablist"`, each button gets `role="tab"`
2. Active filter gets `aria-selected="true"`, others `aria-selected="false"`
3. Apply arrow-key navigation via `useArrowNavigation`
4. Expandable history items: add `aria-expanded={expandedId === reading.id}` on the button
5. The expanded content section: add `role="region"` and `aria-label` with reading type/date

### Checkpoint 4

```bash
cd frontend && npx tsc --noEmit
# Verify: Arrow keys navigate between tabs in ReadingResults
# Verify: Home/End jump to first/last tab
# Verify: RTL mode reverses arrow direction
# Verify: History expandable items announce expanded/collapsed state
```

---

## PHASE 5: Form Accessibility Fixes

### 5.1 OracleConsultationForm Label Fixes

**File:** `frontend/src/components/oracle/OracleConsultationForm.tsx`

Current issues:

- Question textarea `<label>` is not linked (no `htmlFor`/`id` pair)
- Sign error is not linked to the sign selector via `aria-describedby`
- No `aria-required` on the sign selector section

Changes:

1. Add `id="question-input"` to the textarea, `htmlFor="question-input"` to the label
2. Pass `aria-describedby` through to `SignTypeSelector` for sign error
3. Add `aria-required="true"` on the textarea if question is required (or on the sign select since sign is required)
4. Add `lang="fa"` and `dir="rtl"` already present on textarea -- good
5. The keyboard toggle button already has `aria-label` -- good
6. The `aria-live="polite"` region for errors already exists -- good

### 5.2 SignTypeSelector Label + Error Linking

**File:** `frontend/src/components/oracle/SignTypeSelector.tsx`

Current issues:

- The `<label>` wrapping "Sign" text is not linked to the `<select>` (no htmlFor/id)
- Error message `<p>` has no `role="alert"` or `id` for `aria-describedby`
- Conditional inputs use `aria-label` which is OK, but should also get `aria-describedby` when there's an error

Changes:

1. Add `id="sign-type-select"` to the select, `htmlFor="sign-type-select"` to the label
2. Add `id="sign-error"` and `role="alert"` to the error `<p>`
3. Add `aria-describedby="sign-error"` on the active input when error exists
4. Add `aria-required="true"` on the select

### 5.3 LocationSelector Label + Error Fixes

**File:** `frontend/src/components/oracle/LocationSelector.tsx`

Current issues:

- Top-level `<label>` not linked to anything specific
- Detect error has no `role="alert"`
- Auto-detect button has no `aria-busy` during detection

Changes:

1. Change top-level `<label>` to a `<span>` or `<fieldset>`/`<legend>` since it labels a group, not one input
2. Add `aria-busy={isDetecting}` to the auto-detect button
3. Add `role="alert"` to the detect error `<p>`
4. Country select and city input already have `aria-label` -- good

### 5.4 MultiUserSelector Accessibility

**File:** `frontend/src/components/oracle/MultiUserSelector.tsx`

Changes:

1. Add `role="alert"` on the error message `<p>` (line ~200)
2. Add `aria-label` on the "Add new profile" and "Edit profile" buttons (they have visible text, but adding context)
3. The secondary user chips area: wrap in a container with `role="list"` and `aria-label={t("oracle.selected_users")}`
4. Each `<UserChip>` gets `role="listitem"` context
5. The add secondary dropdown: add `aria-label` on the select

### 5.5 UserSelector Button Labels

**File:** `frontend/src/components/oracle/UserSelector.tsx`

Changes:

1. Add `aria-label` attributes to the Add and Edit buttons for screen reader clarity
2. The select already has `aria-label` -- good

### Checkpoint 5

```bash
cd frontend && npx tsc --noEmit
# Verify: All form inputs have associated labels (inspect with browser a11y tree)
# Verify: Error messages appear in screen reader announcement
# Verify: Required fields are announced as required
```

---

## PHASE 6: Dynamic Content & Live Regions

### 6.1 TranslatedReading Live Regions

**File:** `frontend/src/components/oracle/TranslatedReading.tsx`

Changes:

1. Wrap the translated text display in `aria-live="polite"` so screen readers announce when translation appears
2. Add `aria-busy={isTranslating}` on the translate button
3. Add `lang="fa"` on the `<p dir="rtl">` containing Persian translated text
4. Add `role="alert"` on the error `<p>`

### 6.2 ExportButton Labels

**File:** `frontend/src/components/oracle/ExportButton.tsx`

Changes:

1. Add `aria-label={t("oracle.export_text")}` and `aria-label={t("oracle.export_json")}` on buttons (they have visible text which serves as label, but ensure it's descriptive: "Export as Text", "Export as JSON")

### 6.3 StatsCard Semantics

**File:** `frontend/src/components/StatsCard.tsx`

Changes:

1. Add `role="group"` on the card div
2. Add `aria-label={label}` on the card div so screen readers announce the stat context

### 6.4 LogPanel Live Region

**File:** `frontend/src/components/LogPanel.tsx`

Changes:

1. Add `role="log"` on the scrollable entries container (semantically correct for a log panel)
2. Add `aria-live="polite"` so new entries are announced
3. Add `aria-label={title}` on the container

### 6.5 SummaryTab & DetailsTab Persian Language Tags

**Files:** `frontend/src/components/oracle/SummaryTab.tsx`, `frontend/src/components/oracle/DetailsTab.tsx`

Changes:

1. Any block displaying AI interpretation or Persian content: wrap in `<div lang="fa">` when the content language is Persian
2. Check if the i18n language is "fa" and apply `lang="fa"` to the interpretation text blocks

### Checkpoint 6

```bash
cd frontend && npx tsc --noEmit
# Verify: Screen reader announces translation appearing
# Verify: Screen reader announces new log entries
# Verify: Persian text is read with correct pronunciation (lang="fa" set)
```

---

## PHASE 7: Color Contrast Verification & Fixes

### 7.1 Audit Current Color Pairs

Using the NPS color palette from `frontend/tailwind.config.ts`:

| Text Color                | Background                       | Contrast Ratio | WCAG AA       | Status |
| ------------------------- | -------------------------------- | -------------- | ------------- | ------ |
| `#c9d1d9` (text)          | `#0d1117` (bg)                   | ~11.5:1        | Pass          | OK     |
| `#8b949e` (text-dim)      | `#0d1117` (bg)                   | ~5.2:1         | Pass          | OK     |
| `#8b949e` (text-dim)      | `#161b22` (bg-card)              | ~4.1:1         | Pass (barely) | WATCH  |
| `#f0f6fc` (text-bright)   | `#0d1117` (bg)                   | ~15.3:1        | Pass          | OK     |
| `#4fc3f7` (oracle-accent) | `#0d1117` (bg)                   | ~8.5:1         | Pass          | OK     |
| `#4fc3f7` (oracle-accent) | `#0f1a2e` (oracle-bg)            | ~7.2:1         | Pass          | OK     |
| `#0d1117` (bg)            | `#4fc3f7` (oracle-accent, as bg) | ~8.5:1         | Pass          | OK     |
| `#f85149` (error)         | `#0d1117` (bg)                   | ~5.5:1         | Pass          | OK     |
| `#3fb950` (success)       | `#0d1117` (bg)                   | ~6.8:1         | Pass          | OK     |
| `#d29922` (warning)       | `#0d1117` (bg)                   | ~6.7:1         | Pass          | OK     |
| `#d4a017` (gold)          | `#0d1117` (bg)                   | ~6.4:1         | Pass          | OK     |
| `#a371f7` (purple)        | `#0d1117` (bg)                   | ~5.6:1         | Pass          | OK     |
| `#c4b5fd` (ai-text)       | `#1a1033` (ai-bg)                | ~8.1:1         | Pass          | OK     |

> **Potential issues to verify during implementation:**
>
> - `text-dim` (#8b949e) on `bg-card` (#161b22) = ~4.1:1 -- passes AA for normal text at 4.5:1? Actually 4.1:1 FAILS. This needs a fix.
> - `text-dim` on `bg-hover` (#1c2128) -- may be even lower

### 7.2 Contrast Fixes

If `#8b949e` on `#161b22` fails 4.5:1, options:

1. **Preferred:** Lighten `text-dim` to `#9ca3af` (~4.7:1 on #161b22) -- minimal visual change
2. **Alternative:** Darken `bg-card` slightly

Add a computed verification in the test suite using axe-core `color-contrast` rule.

### 7.3 Focus Indicator Contrast

The focus ring color `#4fc3f7` must have 3:1 contrast against both:

- `#0d1117` (dark bg) -- ~8.5:1 -- Pass
- `#161b22` (card bg) -- ~7.2:1 -- Pass

### Checkpoint 7

```bash
cd frontend && npx tsc --noEmit
# Run axe-core color contrast check via test
# Verify: No contrast violations in test output
# Verify: text-dim on bg-card meets 4.5:1 after fix
```

---

## PHASE 8: Persian Accessibility (lang Attributes)

### 8.1 App.tsx Already Sets Root Lang

**File:** `frontend/src/App.tsx` -- already correct:

```tsx
document.documentElement.lang = i18n.language;
```

This sets `<html lang="fa">` when Persian is active. Screen readers use this for pronunciation.

### 8.2 Mixed-Language Content

When the UI is in English but displays Persian content (names, translations, interpretations):

1. **UserForm Persian fields:** Already have `dir="rtl"` -- add `lang="fa"` as well
2. **TranslatedReading:** Already has `dir="rtl"` on Persian text -- add `lang="fa"`
3. **UserChip:** If displaying a Persian name, the chip should inherit lang from context or have it set
4. **OracleConsultationForm textarea:** Already has `dir="rtl"` -- add `lang="fa"`

### 8.3 LanguageToggle Announcement

**File:** `frontend/src/components/LanguageToggle.tsx`

Add `aria-pressed` attribute to indicate the current state:

- When FA is active: `aria-pressed="true"` (since the button represents "toggle to/from Persian")
- Or better: use `aria-label` that already describes the action (already present) and add `role="switch"` with `aria-checked={isFA}`

### Checkpoint 8

```bash
cd frontend && npx tsc --noEmit
# Verify: <html lang="fa"> when Persian is selected
# Verify: Persian input fields have lang="fa"
# Verify: LanguageToggle announces its state to screen readers
```

---

## PHASE 9: Comprehensive Test Suite (REWRITE)

### 9.1 Test File Structure

**File:** `frontend/src/components/oracle/__tests__/Accessibility.test.tsx` (REWRITE)

Delete all existing content (142 lines) and replace with a comprehensive suite organized by category.

### 9.2 Test Categories & Definitions

#### Category A: axe-core Automated Checks (6 tests)

| #   | Test Name                                            | What It Verifies                                                                        |
| --- | ---------------------------------------------------- | --------------------------------------------------------------------------------------- |
| A1  | `axe: Layout has no critical violations`             | Render Layout with mocked routes, run axe-core, assert zero critical/serious violations |
| A2  | `axe: UserForm dialog has no violations`             | Render UserForm, run axe-core on dialog                                                 |
| A3  | `axe: OracleConsultationForm has no violations`      | Render form, run axe-core                                                               |
| A4  | `axe: ReadingResults tabs have no violations`        | Render results with mock data, run axe-core                                             |
| A5  | `axe: CalendarPicker open state has no violations`   | Open calendar, run axe-core                                                             |
| A6  | `axe: ReadingHistory with entries has no violations` | Render with mock history, run axe-core                                                  |

#### Category B: Keyboard Navigation (8 tests)

| #   | Test Name                                                  | What It Verifies                                                       |
| --- | ---------------------------------------------------------- | ---------------------------------------------------------------------- |
| B1  | `keyboard: skip-nav link focuses main content`             | Tab to skip link, press Enter, verify `document.activeElement` is main |
| B2  | `keyboard: sidebar nav items are tab-focusable`            | Tab through nav, verify each NavLink receives focus                    |
| B3  | `keyboard: ReadingResults tabs navigate with arrow keys`   | Focus tab, press ArrowRight, verify next tab focused and selected      |
| B4  | `keyboard: ReadingResults Home/End jump to first/last tab` | Focus middle tab, press Home, verify first tab focused                 |
| B5  | `keyboard: UserForm traps focus within dialog`             | Tab through all fields, verify focus wraps from last to first          |
| B6  | `keyboard: UserForm Escape closes dialog`                  | Press Escape, verify onCancel called                                   |
| B7  | `keyboard: PersianKeyboard traps focus`                    | Render keyboard, verify Tab wraps within it                            |
| B8  | `keyboard: CalendarPicker closes on Escape`                | Open calendar, press Escape, verify it closes                          |

#### Category C: Screen Reader / ARIA (10 tests)

| #   | Test Name                                                | What It Verifies                                                                |
| --- | -------------------------------------------------------- | ------------------------------------------------------------------------------- |
| C1  | `aria: Layout nav has aria-label`                        | Verify `<nav>` has `aria-label`                                                 |
| C2  | `aria: ReadingResults tablist has correct ARIA roles`    | tablist, tab, tabpanel, aria-selected, aria-controls, aria-labelledby           |
| C3  | `aria: UserForm dialog has aria-modal`                   | role="dialog", aria-modal="true"                                                |
| C4  | `aria: UserForm inputs have aria-required`               | Required inputs have aria-required="true"                                       |
| C5  | `aria: UserForm errors linked via aria-describedby`      | Submit empty, verify aria-invalid + aria-describedby + referenced error element |
| C6  | `aria: OracleConsultationForm textarea has linked label` | Verify label htmlFor matches textarea id                                        |
| C7  | `aria: SignTypeSelector select has linked label`         | Verify label htmlFor matches select id                                          |
| C8  | `aria: error messages have role=alert`                   | Trigger errors, verify role="alert" on error elements                           |
| C9  | `aria: LogPanel has role=log`                            | Render LogPanel, verify role="log"                                              |
| C10 | `aria: StatsCard has role=group and aria-label`          | Render StatsCard, verify attributes                                             |

#### Category D: Live Regions & Dynamic Content (4 tests)

| #   | Test Name                                         | What It Verifies                                              |
| --- | ------------------------------------------------- | ------------------------------------------------------------- |
| D1  | `live: error messages appear in aria-live region` | Trigger form error, verify aria-live="polite" contains error  |
| D2  | `live: TranslatedReading announces translation`   | Mock translate, verify aria-live region updates               |
| D3  | `live: ReadingResults panel change announced`     | Switch tab, verify new panel has aria-live or is re-announced |
| D4  | `live: loading states announced via aria-busy`    | Trigger loading, verify aria-busy="true" on submit button     |

#### Category E: Persian Accessibility (4 tests)

| #   | Test Name                                               | What It Verifies                                            |
| --- | ------------------------------------------------------- | ----------------------------------------------------------- |
| E1  | `persian: html lang is set to fa when Persian selected` | Change language to fa, verify document.documentElement.lang |
| E2  | `persian: Persian input fields have lang=fa`            | Verify UserForm Persian name field has lang="fa"            |
| E3  | `persian: translated text has lang=fa`                  | Verify TranslatedReading Persian output has lang="fa"       |
| E4  | `persian: LanguageToggle announces state`               | Verify role="switch" and aria-checked on toggle             |

#### Category F: Color Contrast (2 tests)

| #   | Test Name                                                          | What It Verifies                                            |
| --- | ------------------------------------------------------------------ | ----------------------------------------------------------- |
| F1  | `contrast: axe-core reports no contrast violations on main layout` | Run axe color-contrast rule specifically on rendered layout |
| F2  | `contrast: axe-core reports no contrast violations on oracle form` | Run axe color-contrast rule on consultation form            |

**Total: 34 tests**

### 9.3 Test Helper: axe-core Runner

Add at the top of the test file:

```ts
import { axe, toHaveNoViolations } from "vitest-axe";
expect.extend(toHaveNoViolations);

// Helper to run axe on a container with specific rules
async function checkA11y(container: HTMLElement, rules?: string[]) {
  const config = rules
    ? { rules: Object.fromEntries(rules.map((r) => [r, { enabled: true }])) }
    : undefined;
  const results = await axe(container, config);
  expect(results).toHaveNoViolations();
}
```

> **Fallback:** If `vitest-axe` package is unavailable, use `axe-core` directly:
>
> ```ts
> import axeCore from "axe-core";
> async function checkA11y(container: HTMLElement) {
>   const results = await axeCore.run(container);
>   const violations = results.violations.filter(
>     (v) => v.impact === "critical" || v.impact === "serious",
>   );
>   expect(violations).toEqual([]);
> }
> ```

### Checkpoint 9

```bash
cd frontend && npx vitest run src/components/oracle/__tests__/Accessibility.test.tsx --reporter=verbose
# Verify: All 34 tests pass
# Verify: Zero axe-core critical violations
# Verify: All keyboard navigation tests pass
```

---

## PHASE 10: SkipNavLink & Hook Tests

### 10.1 SkipNavLink Tests

**File:** `frontend/src/components/__tests__/SkipNavLink.test.tsx` (NEW)

| #   | Test Name                                    | What It Verifies                                |
| --- | -------------------------------------------- | ----------------------------------------------- |
| 1   | `renders skip link with correct href`        | Link has `href="#main-content"`                 |
| 2   | `skip link is visually hidden until focused` | Has `.skip-nav` class (CSS positions offscreen) |
| 3   | `skip link text comes from i18n`             | Shows translated "Skip to content" text         |

### 10.2 useFocusTrap Tests

**File:** `frontend/src/hooks/__tests__/useFocusTrap.test.ts` (NEW)

| #   | Test Name                                      | What It Verifies                                                 |
| --- | ---------------------------------------------- | ---------------------------------------------------------------- |
| 1   | `focuses first focusable element on mount`     | Render container with buttons, verify first is focused           |
| 2   | `wraps focus from last to first on Tab`        | Focus last button, press Tab, verify first is focused            |
| 3   | `wraps focus from first to last on Shift+Tab`  | Focus first button, press Shift+Tab, verify last is focused      |
| 4   | `returns focus to previous element on unmount` | Track activeElement before mount, unmount, verify focus returned |
| 5   | `does nothing when isActive is false`          | Pass isActive=false, verify no focus changes                     |

### 10.3 useArrowNavigation Tests

**File:** `frontend/src/hooks/__tests__/useArrowNavigation.test.ts` (NEW)

| #   | Test Name                                | What It Verifies                                                               |
| --- | ---------------------------------------- | ------------------------------------------------------------------------------ |
| 1   | `ArrowRight moves focus to next item`    | Focus first tab, press ArrowRight, verify second is focused                    |
| 2   | `ArrowLeft moves focus to previous item` | Focus second tab, press ArrowLeft, verify first is focused                     |
| 3   | `loops from last to first`               | Focus last tab, press ArrowRight, verify first is focused                      |
| 4   | `Home focuses first item`                | Focus last tab, press Home, verify first is focused                            |
| 5   | `End focuses last item`                  | Focus first tab, press End, verify last is focused                             |
| 6   | `reverses direction in RTL`              | Set `document.documentElement.dir = "rtl"`, verify ArrowRight goes to previous |

### Checkpoint 10

```bash
cd frontend && npx vitest run --reporter=verbose
# Verify: All new hook tests pass
# Verify: SkipNavLink tests pass
# Verify: Total test count includes 34 a11y + 3 skip + 5 trap + 6 arrow = 48 new tests
```

---

## PHASE 11: i18n Keys & Final Integration

### 11.1 New Translation Keys

**File:** `frontend/src/locales/en.json`

Add under a new `"a11y"` namespace:

```json
{
  "a11y": {
    "skip_to_content": "Skip to content",
    "previous_month": "Previous month",
    "next_month": "Next month",
    "selected_users": "Selected users",
    "expand_reading": "Expand reading details",
    "collapse_reading": "Collapse reading details",
    "filter_readings": "Filter readings",
    "calendar_dialog": "Calendar date picker",
    "loading": "Loading, please wait"
  }
}
```

**File:** `frontend/src/locales/fa.json`

```json
{
  "a11y": {
    "skip_to_content": "\u0631\u0641\u062a\u0646 \u0628\u0647 \u0645\u062d\u062a\u0648\u0627",
    "previous_month": "\u0645\u0627\u0647 \u0642\u0628\u0644",
    "next_month": "\u0645\u0627\u0647 \u0628\u0639\u062f",
    "selected_users": "\u06a9\u0627\u0631\u0628\u0631\u0627\u0646 \u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u062f\u0647",
    "expand_reading": "\u0646\u0645\u0627\u06cc\u0634 \u062c\u0632\u0626\u06cc\u0627\u062a",
    "collapse_reading": "\u0628\u0633\u062a\u0646 \u062c\u0632\u0626\u06cc\u0627\u062a",
    "filter_readings": "\u0641\u06cc\u0644\u062a\u0631 \u062e\u0648\u0627\u0646\u0634\u200c\u0647\u0627",
    "calendar_dialog": "\u0627\u0646\u062a\u062e\u0627\u0628 \u062a\u0627\u0631\u06cc\u062e",
    "loading": "\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc"
  }
}
```

### 11.2 Full Integration Test

Run the complete test suite to verify nothing broke:

```bash
cd frontend && npx vitest run --reporter=verbose 2>&1 | tail -20
```

### 11.3 Manual Verification Checklist

Before marking session as complete, verify each item:

- [ ] Tab through entire app from skip-nav to last element in main content
- [ ] Open UserForm with keyboard (Enter on "Add Profile"), fill fields with Tab, submit with Enter
- [ ] Open CalendarPicker, navigate days with arrows, select with Enter
- [ ] Switch ReadingResults tabs with arrow keys
- [ ] Trigger form validation errors, verify screen reader announces them
- [ ] Switch to Persian, verify `<html lang="fa" dir="rtl">`
- [ ] Open PersianKeyboard, navigate with Tab, type character with Enter/Space
- [ ] Run axe-core browser extension on each page: zero critical violations
- [ ] Check color contrast with browser DevTools on `text-dim` on `bg-card`

### Checkpoint 11 (FINAL)

```bash
cd frontend && npx vitest run --reporter=verbose
cd frontend && npx tsc --noEmit
# Verify: ALL tests pass (existing + 48 new)
# Verify: Zero TypeScript errors
# Verify: axe-core zero critical violations
```

---

## ACCEPTANCE CRITERIA

- [ ] Keyboard-only navigation works for all flows (skip nav, sidebar, forms, tabs, dialogs, calendar)
- [ ] axe-core reports zero critical or serious violations across all tested components
- [ ] Color contrast meets 4.5:1 minimum for normal text, 3:1 for large text
- [ ] All form inputs have programmatically-associated labels (htmlFor/id or aria-label)
- [ ] All error messages have `role="alert"` and are linked via `aria-describedby` where applicable
- [ ] Dialogs trap focus and return focus on close
- [ ] Persian text has `lang="fa"` attribute for correct screen reader pronunciation
- [ ] Skip-to-content link works and is visible on focus
- [ ] ReadingResults tabs support arrow-key navigation with roving tabindex
- [ ] `prefers-reduced-motion` respected (animations disabled)
- [ ] All 48+ new tests pass
- [ ] All existing tests continue to pass
- [ ] Zero TypeScript compilation errors

---

## DEPENDENCY GRAPH

```
Phase 1 (axe-core + focus CSS)
  ├── Phase 2 (skip nav + landmarks)
  ├── Phase 3 (focus trap + dialogs) ──→ Phase 4 (arrow nav + tabs)
  ├── Phase 5 (form fixes)
  ├── Phase 6 (live regions)
  ├── Phase 7 (contrast fixes)
  └── Phase 8 (Persian a11y)
        ↓
      Phase 9 (comprehensive tests) ──→ Phase 10 (hook + component tests)
        ↓
      Phase 11 (i18n + integration)
```

Phases 2-8 can be done in any order after Phase 1.
Phases 9-10 require all component modifications to be complete.
Phase 11 is final integration and verification.

---

## NOTES FOR EXECUTOR

1. **axe-core package:** Try `vitest-axe` first. If unavailable, use `axe-core` directly with a custom `toHaveNoViolations` matcher (example provided in Phase 9).

2. **Contrast fix for text-dim:** The `#8b949e` on `#161b22` ratio is borderline. Measure with a contrast checker tool. If it fails 4.5:1, lighten to `#9ca3af` or similar. Do NOT change it if it passes.

3. **RTL arrow key reversal:** This is critical for Persian users. The `useArrowNavigation` hook MUST check `document.documentElement.dir` and swap ArrowLeft/ArrowRight meanings when `dir="rtl"`.

4. **Do NOT change component behavior.** This session is about a11y attributes, ARIA roles, focus management, and testing. No feature changes, no visual redesign.

5. **Existing tests:** The 11 tests in the current `Accessibility.test.tsx` are being REPLACED, not extended. The new suite is a superset covering everything the old tests covered plus much more.

6. **Focus trap and dialog pattern:** The UserForm currently uses `onClick={onCancel}` on the backdrop for closing. This is mouse-only. Add `onKeyDown` for Escape key as well. The `useFocusTrap` hook handles Tab wrapping.

7. **CalendarPicker grid pattern:** The ARIA grid pattern (`role="grid"`, `role="row"`, `role="gridcell"`) is the correct pattern for a date picker. Each day button should have `aria-label` with the full date (e.g., "February 10, 2026" or "۲۱ بهمن ۱۴۰۴" in Jalaali mode).

8. **Reduced motion:** The CSS media query in Phase 1 handles animation disabling globally. No per-component changes needed.
