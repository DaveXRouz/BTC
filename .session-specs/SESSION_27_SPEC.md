# SESSION 27 SPEC — Responsive Design

**Block:** Frontend Advanced (Sessions 26-31)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 19 (layout & navigation), Session 20 (Oracle main page), Session 21 (reading results), Session 22 (dashboard), Session 26 (RTL layout system)

---

## TL;DR

- Make every page (Dashboard, Oracle, Settings, Vault, Learning, Scanner) fully responsive across mobile (<640px), tablet (640-1024px), and desktop (>1024px)
- Convert the fixed sidebar to a collapsible hamburger menu on mobile with slide-out drawer
- Ensure all touch targets are 44px+ on mobile, and all forms are full-width stacked on small screens
- Create a `MobileKeyboard.tsx` component for full-width Persian keyboard on mobile devices
- Add responsive utility hook `useBreakpoint` and a `MobileNav` drawer component
- Verify responsive behavior works correctly in both LTR (EN) and RTL (FA) layouts

---

## OBJECTIVES

1. Implement a responsive sidebar that collapses into a hamburger menu with slide-out drawer below 1024px
2. Make the Dashboard page responsive: stacked single-column on mobile, 2-column on tablet, full grid on desktop
3. Make the Oracle page responsive: stacked form sections on mobile, two-panel layout on desktop
4. Make reading results stack vertically on mobile with horizontal scroll for tab bar
5. Make the Settings page form sections stack vertically on mobile
6. Create a full-width `MobileKeyboard.tsx` that replaces the popup Persian keyboard on screens below 640px
7. Ensure all interactive elements have minimum 44px touch targets on mobile
8. Ensure responsive layouts work correctly in both LTR and RTL directions
9. Add `useBreakpoint` hook for programmatic breakpoint detection
10. Add Playwright viewport tests to verify key pages render at 375px, 768px, and 1440px

---

## PREREQUISITES

- [ ] `frontend/src/components/Layout.tsx` exists with sidebar + main content outlet
  - Verification: `test -f frontend/src/components/Layout.tsx && echo "OK"`
- [ ] `frontend/src/App.tsx` has RTL direction support based on locale
  - Verification: `grep -q "dir" frontend/src/App.tsx && echo "OK"`
- [ ] Tailwind CSS configured with NPS color tokens and default breakpoints (sm:640px, md:768px, lg:1024px, xl:1280px)
  - Verification: `test -f frontend/tailwind.config.ts && echo "OK"`
- [ ] Oracle page exists with consultation form, user selector, and reading results
  - Verification: `test -f frontend/src/pages/Oracle.tsx && echo "OK"`
- [ ] Dashboard page exists
  - Verification: `test -f frontend/src/pages/Dashboard.tsx && echo "OK"`
- [ ] Persian keyboard component exists at `frontend/src/components/oracle/PersianKeyboard.tsx`
  - Verification: `test -f frontend/src/components/oracle/PersianKeyboard.tsx && echo "OK"`
- [ ] Playwright E2E config exists
  - Verification: `test -f frontend/e2e/oracle.spec.ts && echo "OK"`
- [ ] i18n configured with EN/FA locales
  - Verification: `test -f frontend/src/i18n/config.ts && echo "OK"`

---

## FILES TO CREATE

- `frontend/src/hooks/useBreakpoint.ts` — React hook for detecting current viewport breakpoint (mobile/tablet/desktop)
- `frontend/src/components/MobileNav.tsx` — Hamburger menu + slide-out drawer for mobile/tablet navigation
- `frontend/src/components/oracle/MobileKeyboard.tsx` — Full-width mobile Persian keyboard (fixed to bottom of viewport)
- `frontend/src/hooks/__tests__/useBreakpoint.test.ts` — Tests for breakpoint hook
- `frontend/src/components/__tests__/MobileNav.test.tsx` — Tests for mobile navigation
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx` — Tests for mobile keyboard
- `frontend/src/components/__tests__/Layout.test.tsx` — Tests for responsive layout switching
- `frontend/e2e/responsive.spec.ts` — Playwright viewport tests for responsive behavior

---

## FILES TO MODIFY

- `frontend/src/components/Layout.tsx` — Add mobile hamburger menu, hide sidebar below lg breakpoint, responsive main padding
- `frontend/src/pages/Dashboard.tsx` — Responsive grid: 1-col mobile, 2-col tablet, 4-col desktop for stats cards
- `frontend/src/pages/Oracle.tsx` — Stack sections vertically on mobile, side-by-side on desktop
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — Full-width inputs on mobile, increase touch targets
- `frontend/src/components/oracle/MultiUserSelector.tsx` — Stack primary selector + add button vertically on mobile
- `frontend/src/components/oracle/ReadingResults.tsx` — Horizontal scrollable tabs on mobile, ensure cards stack
- `frontend/src/components/oracle/PersianKeyboard.tsx` — Delegate to MobileKeyboard on small screens
- `frontend/src/components/oracle/CalendarPicker.tsx` — Full-width dropdown on mobile, increase day cell size to 44px
- `frontend/src/components/oracle/SignTypeSelector.tsx` — Stack radio/buttons vertically on mobile
- `frontend/src/components/oracle/LocationSelector.tsx` — Full-width inputs, larger detect button
- `frontend/src/components/StatsCard.tsx` — Min-height for touch target, responsive text sizing
- `frontend/src/components/LanguageToggle.tsx` — Increase tap area to 44px minimum
- `frontend/src/locales/en.json` — Add `common.menu_open`, `common.menu_close` keys
- `frontend/src/locales/fa.json` — Add corresponding Persian translations

---

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: Breakpoint Hook & Mobile Detection (30 minutes)

**Tasks:**

1. Create `frontend/src/hooks/useBreakpoint.ts`:
   - Use `window.matchMedia` to detect breakpoints
   - Return `{ isMobile: boolean, isTablet: boolean, isDesktop: boolean, breakpoint: "mobile" | "tablet" | "desktop" }`
   - Breakpoints: mobile < 640px, tablet 640-1023px, desktop >= 1024px
   - Subscribe to resize events, cleanup on unmount
   - SSR-safe: default to desktop if `window` is undefined

2. Write `frontend/src/hooks/__tests__/useBreakpoint.test.ts`:
   - Returns mobile when viewport < 640px
   - Returns tablet when viewport 640-1023px
   - Returns desktop when viewport >= 1024px
   - Responds to resize events

**Code Pattern — useBreakpoint hook:**

```typescript
interface BreakpointState {
  isMobile: boolean; // < 640px
  isTablet: boolean; // 640-1023px
  isDesktop: boolean; // >= 1024px
  breakpoint: "mobile" | "tablet" | "desktop";
}

export function useBreakpoint(): BreakpointState {
  // Uses window.matchMedia with sm (640px) and lg (1024px) queries
  // Returns reactive state that updates on viewport change
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/hooks/__tests__/useBreakpoint.test.ts` passes
- Verify: `cd frontend && npx vitest run src/hooks/__tests__/useBreakpoint.test.ts`

---

### Phase 2: Mobile Navigation Drawer (45 minutes)

**Tasks:**

1. Create `frontend/src/components/MobileNav.tsx`:
   - Hamburger button (3 horizontal lines) — visible only below lg (1024px)
   - Slide-out drawer from left (LTR) or right (RTL) with backdrop overlay
   - Contains same nav items as sidebar: Dashboard, Scanner, Oracle, Vault, Learning, Settings
   - Active page highlighted, same styling as sidebar NavLinks
   - Close on nav item click, close on backdrop click, close on Escape key
   - LanguageToggle at bottom of drawer
   - Animated slide transition (transform translateX)
   - Drawer width: 280px on tablet, full screen minus 56px on mobile
   - ARIA: `role="dialog"`, `aria-modal="true"`, `aria-label` for menu

2. Modify `frontend/src/components/Layout.tsx`:
   - Import `useBreakpoint` and `MobileNav`
   - Hide sidebar (`hidden lg:flex`) on mobile/tablet
   - Show hamburger button (`lg:hidden`) in a top bar on mobile/tablet
   - Top bar: NPS logo (left), hamburger (right) — flips in RTL
   - Main content: `p-4 lg:p-6` (less padding on mobile)

3. Add locale keys for menu accessibility:
   - `en.json`: `"common.menu_open": "Open menu"`, `"common.menu_close": "Close menu"`
   - `fa.json`: corresponding Persian translations

4. Write `frontend/src/components/__tests__/MobileNav.test.tsx`:
   - Renders hamburger button when viewport < 1024px
   - Opens drawer on hamburger click
   - Closes drawer on backdrop click
   - Closes drawer on Escape key
   - Nav items navigate correctly
   - Drawer slides from correct direction in RTL mode

5. Write `frontend/src/components/__tests__/Layout.test.tsx`:
   - Sidebar visible on desktop viewport
   - Sidebar hidden on mobile viewport
   - Hamburger visible on mobile viewport
   - Hamburger hidden on desktop viewport

**Code Pattern — Layout responsive structure:**

```typescript
export function Layout() {
  const { t } = useTranslation();
  const { isDesktop } = useBreakpoint();
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-nps-bg">
      {/* Desktop sidebar — hidden below lg */}
      <nav className="hidden lg:flex w-64 border-r rtl:border-r-0 rtl:border-l ...">
        {/* existing sidebar content */}
      </nav>

      {/* Mobile top bar — visible below lg */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-30 h-14 bg-nps-bg-card border-b ...">
        <button onClick={() => setDrawerOpen(true)} aria-label={t("common.menu_open")}>
          {/* hamburger icon */}
        </button>
      </div>

      {/* Mobile drawer */}
      <MobileNav isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {/* Main content */}
      <main className="flex-1 p-4 lg:p-6 overflow-auto pt-14 lg:pt-6">
        <Outlet />
      </main>
    </div>
  );
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/__tests__/MobileNav.test.tsx src/components/__tests__/Layout.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/__tests__/MobileNav.test.tsx src/components/__tests__/Layout.test.tsx`

---

### Phase 3: Dashboard Responsive Layout (30 minutes)

**Tasks:**

1. Modify `frontend/src/pages/Dashboard.tsx`:
   - Stats grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` (1 col mobile, 2 tablet, 4 desktop)
   - Section headings: `text-lg sm:text-xl` for responsive typography
   - Cards: full-width on mobile with consistent spacing
   - Welcome banner (if from Session 22): stack text and moon widget vertically on mobile
   - Recent readings: horizontal scroll on mobile (`flex overflow-x-auto snap-x`), grid on desktop
   - Quick actions: stack vertically on mobile (`flex-col sm:flex-row`)

2. Modify `frontend/src/components/StatsCard.tsx`:
   - Add `min-h-[72px]` for touch-friendly height
   - Value text: `text-xl sm:text-2xl` responsive sizing
   - Label text: stay at `text-xs`

**Checkpoint:**

- [ ] Dashboard visually correct at 375px, 768px, and 1440px widths (manual check or Playwright)
- Verify: `cd frontend && npx tsc --noEmit`

---

### Phase 4: Oracle Page Responsive Layout (45 minutes)

**Tasks:**

1. Modify `frontend/src/pages/Oracle.tsx`:
   - Section containers: `space-y-4 lg:space-y-6`
   - On desktop (lg+): user profile and consultation form can sit side by side: `lg:grid lg:grid-cols-2 lg:gap-6`
   - On mobile: stack all sections vertically, full width
   - Reading results section: always full width below the form

2. Modify `frontend/src/components/oracle/MultiUserSelector.tsx`:
   - Primary selector row: `flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3`
   - Select element: `w-full sm:min-w-[200px] sm:w-auto`
   - Buttons: full-width on mobile (`w-full sm:w-auto`), min 44px height
   - User chips: wrap with `flex-wrap gap-2`

3. Modify `frontend/src/components/oracle/OracleConsultationForm.tsx`:
   - All inputs: `w-full` (already are)
   - Submit button: `py-3` on mobile for 44px+ height (increase from `py-2`)
   - Textarea: `min-h-[100px]` on mobile for easier touch input
   - Keyboard toggle button: `w-10 h-10 sm:w-7 sm:h-7` for larger mobile tap target

4. Modify `frontend/src/components/oracle/SignTypeSelector.tsx`:
   - Button group: `flex flex-wrap gap-2` instead of inline row
   - Each type button: `min-h-[44px] px-4` for touch targets

5. Modify `frontend/src/components/oracle/LocationSelector.tsx`:
   - Stack country/city inputs vertically on mobile: `flex flex-col sm:flex-row gap-2`
   - Auto-detect button: full-width on mobile, `min-h-[44px]`

6. Modify `frontend/src/components/oracle/ReadingResults.tsx`:
   - Tab bar: `overflow-x-auto` on mobile for horizontal scroll if many tabs
   - Tab buttons: `min-h-[44px] whitespace-nowrap`
   - Export button: icon-only on mobile, icon+text on tablet+

**Checkpoint:**

- [ ] Oracle page usable at 375px width — all controls tappable, no horizontal overflow
- Verify: `cd frontend && npx tsc --noEmit`

---

### Phase 5: Calendar & Keyboard Mobile Optimization (45 minutes)

**Tasks:**

1. Modify `frontend/src/components/oracle/CalendarPicker.tsx`:
   - Dropdown calendar: `w-full sm:w-72` (full-width on mobile, fixed on desktop)
   - Day cells: `h-10 sm:h-8` (44px on mobile, 32px on desktop)
   - Month navigation buttons: `w-10 h-10 sm:w-7 sm:h-7`
   - Calendar mode toggle buttons: `min-h-[44px] sm:min-h-0`
   - On mobile, calendar opens as bottom sheet instead of dropdown (position `fixed bottom-0 inset-x-0` with backdrop)

2. Create `frontend/src/components/oracle/MobileKeyboard.tsx`:
   - Full-width keyboard fixed to bottom of viewport
   - Visible only on mobile (< 640px)
   - Same character layout as `PersianKeyboard.tsx` (uses `PERSIAN_ROWS`)
   - Larger keys: `min-w-[36px] min-h-[44px]` for touch
   - Space and backspace bar at bottom, full width
   - Slide-up animation from bottom
   - Backdrop overlay to close
   - ARIA: `role="dialog"`, proper labels

3. Modify `frontend/src/components/oracle/PersianKeyboard.tsx`:
   - Import `useBreakpoint`
   - If `isMobile`, render `MobileKeyboard` instead of popup
   - Desktop behavior unchanged (absolute popup below input)

4. Write `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx`:
   - Renders all Persian characters
   - Fires onCharacterClick when key tapped
   - Fires onBackspace
   - Fires onClose when backdrop clicked
   - Has 44px minimum touch targets

**Code Pattern — MobileKeyboard interface:**

```typescript
interface MobileKeyboardProps {
  onCharacterClick: (char: string) => void;
  onBackspace: () => void;
  onClose: () => void;
}

export function MobileKeyboard({
  onCharacterClick,
  onBackspace,
  onClose,
}: MobileKeyboardProps) {
  // Fixed bottom sheet with full-width keys
  // Uses PERSIAN_ROWS from persianKeyboardLayout
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/oracle/__tests__/MobileKeyboard.test.tsx` passes
- [ ] Calendar day cells are 44px on mobile viewport
- Verify: `cd frontend && npx vitest run src/components/oracle/__tests__/MobileKeyboard.test.tsx`

---

### Phase 6: Remaining Pages Responsive (30 minutes)

**Tasks:**

1. Modify `frontend/src/pages/Settings.tsx`:
   - If Settings has form sections (from Session 23): stack vertically on mobile
   - Settings cards: `w-full` on mobile
   - Form inputs: full-width with `min-h-[44px]` for touch targets
   - Note: If Settings is still a stub, add responsive classes to the stub wrapper for future-proofing

2. Review `frontend/src/pages/Vault.tsx`:
   - Ensure findings list is `overflow-x-auto` on mobile for table data
   - Search input: full-width with 44px height

3. Review `frontend/src/pages/Learning.tsx`:
   - Ensure cards stack on mobile
   - Stats: single column on mobile

4. Review `frontend/src/pages/Scanner.tsx`:
   - Scanner is STUB — just ensure the stub text is readable on mobile with `text-sm` sizing

5. Modify `frontend/src/components/LanguageToggle.tsx`:
   - Increase touch target: `min-h-[44px] min-w-[44px]` wrapper or `p-2` padding
   - Keep compact on desktop

**Checkpoint:**

- [ ] All pages render without horizontal scroll at 375px
- Verify: `cd frontend && npx tsc --noEmit`

---

### Phase 7: RTL + Responsive Cross-Verification (30 minutes)

**Tasks:**

1. Verify every responsive modification works in RTL (FA locale):
   - Mobile drawer slides from right in RTL
   - Hamburger button on correct side (left in RTL)
   - Top bar NPS logo flips to right in RTL
   - Oracle form inputs right-aligned in RTL
   - Calendar picker opens correctly in RTL on mobile
   - Stats cards maintain correct order in RTL grid

2. Check mixed-direction edge cases:
   - FC60 stamp codes (`<bdi>` or `dir="ltr"`) within RTL mobile layout
   - English names within Persian mobile nav
   - Number inputs in RTL form

3. Fix any RTL-responsive conflicts found:
   - Drawer animation direction: `rtl:-translate-x-full` to `rtl:translate-x-full`
   - Padding/margin asymmetries: use `ps-*` / `pe-*` (Tailwind logical properties) instead of `pl-*` / `pr-*`

**Checkpoint:**

- [ ] Mobile drawer opens from correct side in both LTR and RTL
- [ ] All forms usable in RTL at 375px width
- Verify: Manual check or `cd frontend && npx tsc --noEmit`

---

### Phase 8: Playwright Viewport Tests (45 minutes)

**Tasks:**

1. Create `frontend/e2e/responsive.spec.ts` with viewport-based tests:
   - **Mobile (375x667 — iPhone SE):**
     - Sidebar is hidden
     - Hamburger button is visible
     - Hamburger opens drawer, nav items visible
     - Oracle page form is full-width
     - Stats cards are single column
     - All buttons have 44px+ height

   - **Tablet (768x1024 — iPad):**
     - Sidebar is hidden (below lg breakpoint)
     - Hamburger visible
     - Oracle form sections are full-width
     - Stats cards are 2 columns

   - **Desktop (1440x900):**
     - Sidebar is visible
     - Hamburger is hidden
     - Oracle page may show two-column layout
     - Stats cards are 4 columns

   - **RTL Mobile (375x667, FA locale):**
     - Drawer slides from right
     - Text is right-aligned
     - Navigation items in correct order

2. Configure viewport in each test:
   ```typescript
   test.use({ viewport: { width: 375, height: 667 } });
   ```

**Code Pattern — Playwright responsive test:**

```typescript
import { test, expect } from "@playwright/test";

test.describe("Responsive — Mobile (375px)", () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test("sidebar is hidden on mobile", async ({ page }) => {
    await page.goto("/dashboard");
    const sidebar = page.locator("nav.w-64, nav[class*='w-64']");
    await expect(sidebar).not.toBeVisible();
  });

  test("hamburger menu is visible", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page.locator(
      "button[aria-label*='menu'], button[aria-label*='Menu']",
    );
    await expect(hamburger).toBeVisible();
  });

  test("drawer opens on hamburger click", async ({ page }) => {
    await page.goto("/dashboard");
    const hamburger = page
      .locator("button[aria-label*='menu'], button[aria-label*='Menu']")
      .first();
    await hamburger.click();
    const drawer = page.locator("[role='dialog']");
    await expect(drawer).toBeVisible();
  });
});

test.describe("Responsive — Desktop (1440px)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("sidebar is visible on desktop", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.locator("text=NPS")).toBeVisible();
    // Sidebar nav items should be visible
    await expect(page.locator("text=Dashboard")).toBeVisible();
  });
});
```

**Checkpoint:**

- [ ] `cd frontend && npx playwright test e2e/responsive.spec.ts` passes
- Verify: `cd frontend && npx playwright test e2e/responsive.spec.ts`

---

### Phase 9: Final Verification (30 minutes)

**Tasks:**

1. Run all frontend unit tests:

   ```bash
   cd frontend && npx vitest run
   ```

2. Run TypeScript type check:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

3. Run linter:

   ```bash
   cd frontend && npm run lint
   ```

4. Run formatter:

   ```bash
   cd frontend && npx prettier --write src/hooks/useBreakpoint.ts src/components/MobileNav.tsx src/components/oracle/MobileKeyboard.tsx src/components/Layout.tsx src/pages/Dashboard.tsx src/pages/Oracle.tsx
   ```

5. Run Playwright E2E tests:

   ```bash
   cd frontend && npx playwright test
   ```

6. Manual spot check (if dev server available):
   - Resize browser to 375px — verify hamburger, drawer, stacked cards
   - Resize to 768px — verify two-column grids
   - Resize to 1440px — verify sidebar, full grids
   - Switch to FA locale at each size — verify RTL behavior

**Checkpoint:**

- [ ] All unit tests pass: `cd frontend && npx vitest run`
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit`
- [ ] Lint passes: `cd frontend && npm run lint`
- [ ] All E2E tests pass: `cd frontend && npx playwright test`
- Verify: `cd frontend && npx vitest run && npx tsc --noEmit && npm run lint`

---

## TESTS TO WRITE

### Unit Tests

- `frontend/src/hooks/__tests__/useBreakpoint.test.ts::returns_mobile_below_640` — Hook returns `isMobile: true` when viewport < 640px
- `frontend/src/hooks/__tests__/useBreakpoint.test.ts::returns_tablet_640_to_1023` — Hook returns `isTablet: true` for viewport 640-1023px
- `frontend/src/hooks/__tests__/useBreakpoint.test.ts::returns_desktop_above_1024` — Hook returns `isDesktop: true` when viewport >= 1024px
- `frontend/src/hooks/__tests__/useBreakpoint.test.ts::updates_on_resize` — Hook responds to window resize events
- `frontend/src/components/__tests__/MobileNav.test.tsx::renders_hamburger_on_mobile` — Hamburger icon visible on mobile viewport
- `frontend/src/components/__tests__/MobileNav.test.tsx::opens_drawer_on_click` — Drawer appears when hamburger clicked
- `frontend/src/components/__tests__/MobileNav.test.tsx::closes_on_escape` — Drawer closes on Escape keypress
- `frontend/src/components/__tests__/MobileNav.test.tsx::closes_on_backdrop` — Drawer closes when backdrop clicked
- `frontend/src/components/__tests__/MobileNav.test.tsx::shows_all_nav_items` — All 6 nav items rendered in drawer
- `frontend/src/components/__tests__/MobileNav.test.tsx::closes_on_nav_click` — Drawer closes after navigating
- `frontend/src/components/__tests__/Layout.test.tsx::sidebar_visible_desktop` — Sidebar rendered on desktop
- `frontend/src/components/__tests__/Layout.test.tsx::sidebar_hidden_mobile` — Sidebar hidden on mobile
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx::renders_all_characters` — All Persian characters displayed
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx::fires_character_click` — Character key calls onCharacterClick
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx::fires_backspace` — Backspace button calls onBackspace
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx::has_44px_touch_targets` — All keys meet minimum 44px tap size
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx::closes_on_backdrop` — Backdrop click triggers onClose

### E2E Tests (Playwright)

- `frontend/e2e/responsive.spec.ts::mobile_sidebar_hidden` — Sidebar not visible at 375px
- `frontend/e2e/responsive.spec.ts::mobile_hamburger_visible` — Hamburger button visible at 375px
- `frontend/e2e/responsive.spec.ts::mobile_drawer_opens` — Drawer opens on hamburger click at 375px
- `frontend/e2e/responsive.spec.ts::tablet_stats_two_columns` — Stats cards in 2 columns at 768px
- `frontend/e2e/responsive.spec.ts::desktop_sidebar_visible` — Sidebar visible at 1440px
- `frontend/e2e/responsive.spec.ts::desktop_hamburger_hidden` — Hamburger not visible at 1440px
- `frontend/e2e/responsive.spec.ts::rtl_mobile_drawer_from_right` — FA locale drawer slides from right at 375px
- `frontend/e2e/responsive.spec.ts::mobile_no_horizontal_overflow` — No horizontal scroll at 375px on any page

---

## ACCEPTANCE CRITERIA

- [ ] Sidebar is hidden below 1024px and replaced by hamburger menu
- [ ] Mobile drawer opens/closes with animation and backdrop
- [ ] Mobile drawer slides from correct direction (left in LTR, right in RTL)
- [ ] Dashboard stats cards: 1 column at 375px, 2 columns at 768px, 4 columns at 1440px
- [ ] Oracle page form sections stack vertically on mobile and are full-width
- [ ] All buttons and interactive elements have minimum 44px touch targets on mobile
- [ ] Persian keyboard renders as full-width bottom sheet on mobile
- [ ] Calendar picker opens as full-width on mobile with 44px day cells
- [ ] No horizontal overflow/scroll on any page at 375px width
- [ ] All responsive changes work correctly in RTL (FA) locale
- [ ] `useBreakpoint` hook returns correct values at each breakpoint
- [ ] LanguageToggle has 44px minimum touch target on mobile
- [ ] All unit tests pass (17+ new tests)
- [ ] All Playwright E2E viewport tests pass (8+ new tests)
- [ ] TypeScript compiles without errors
- [ ] Lint passes without errors
- Verify all: `cd frontend && npx vitest run && npx tsc --noEmit && npm run lint && npx playwright test e2e/responsive.spec.ts`

---

## ERROR SCENARIOS

### Problem: Hamburger menu opens but nav items don't navigate (React Router issue with drawer)

**Fix:** Ensure `MobileNav` uses the same `NavLink` from `react-router-dom` as the sidebar. The drawer must be rendered inside `<BrowserRouter>` context. Check that drawer uses `onClick` to close after navigation: `onClick={() => { navigate(path); onClose(); }}` or wrap NavLink's `onClick`. Test with: `cd frontend && npx vitest run src/components/__tests__/MobileNav.test.tsx --reporter=verbose`.

### Problem: RTL drawer slides from wrong direction

**Fix:** The drawer transition uses `translateX`. In LTR, the off-screen state is `-translate-x-full` (slides from left). In RTL, it should be `translate-x-full` (slides from right). Use Tailwind's `rtl:` variant: `className="-translate-x-full rtl:translate-x-full"` for the closed state, and `translate-x-0` for open. Check `document.documentElement.dir` to confirm RTL is active. Test: `cd frontend && npx playwright test e2e/responsive.spec.ts --grep "rtl"`.

### Problem: `useBreakpoint` tests fail because `window.matchMedia` is not available in jsdom

**Fix:** Mock `window.matchMedia` in the test setup. Create a helper:

```typescript
function mockMatchMedia(width: number) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: (query: string) => ({
      matches: /* evaluate query against width */,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }),
  });
}
```

Alternatively, use `vi.stubGlobal("matchMedia", ...)` in vitest.

### Problem: Calendar bottom sheet overlaps mobile keyboard

**Fix:** Give calendar bottom sheet a higher `z-index` than mobile keyboard (z-50 vs z-40). Only one should be open at a time — when calendar opens, close keyboard; when keyboard opens, close calendar. Add mutual exclusion in `OracleConsultationForm`.

### Problem: Horizontal overflow on mobile despite full-width classes

**Fix:** Check for elements with fixed widths (`w-64`, `min-w-[200px]`) that don't have responsive overrides. Add `max-w-full overflow-hidden` to the main content wrapper. Common culprit: the `MultiUserSelector` select element with `min-w-[200px]` — change to `min-w-0 w-full sm:min-w-[200px] sm:w-auto`. Run: `cd frontend && npx playwright test e2e/responsive.spec.ts --grep "overflow"`.

---

## HANDOFF

**Created:**

- `frontend/src/hooks/useBreakpoint.ts`
- `frontend/src/components/MobileNav.tsx`
- `frontend/src/components/oracle/MobileKeyboard.tsx`
- `frontend/src/hooks/__tests__/useBreakpoint.test.ts`
- `frontend/src/components/__tests__/MobileNav.test.tsx`
- `frontend/src/components/oracle/__tests__/MobileKeyboard.test.tsx`
- `frontend/src/components/__tests__/Layout.test.tsx`
- `frontend/e2e/responsive.spec.ts`

**Modified:**

- `frontend/src/components/Layout.tsx` (responsive sidebar/mobile top bar)
- `frontend/src/pages/Dashboard.tsx` (responsive grid)
- `frontend/src/pages/Oracle.tsx` (responsive layout)
- `frontend/src/components/oracle/OracleConsultationForm.tsx` (touch targets, full-width)
- `frontend/src/components/oracle/MultiUserSelector.tsx` (responsive stacking)
- `frontend/src/components/oracle/ReadingResults.tsx` (scrollable tabs)
- `frontend/src/components/oracle/PersianKeyboard.tsx` (delegates to MobileKeyboard)
- `frontend/src/components/oracle/CalendarPicker.tsx` (full-width mobile, larger cells)
- `frontend/src/components/oracle/SignTypeSelector.tsx` (wrap, touch targets)
- `frontend/src/components/oracle/LocationSelector.tsx` (full-width, larger buttons)
- `frontend/src/components/StatsCard.tsx` (min-height, responsive text)
- `frontend/src/components/LanguageToggle.tsx` (44px touch target)
- `frontend/src/locales/en.json` (menu open/close keys)
- `frontend/src/locales/fa.json` (Persian menu translations)

**Deleted:**

- None

**Next session (Session 28 — Accessibility) needs:**

- All pages responsive at mobile/tablet/desktop breakpoints
- `useBreakpoint` hook available for programmatic breakpoint detection
- `MobileNav` component with drawer navigation
- 44px minimum touch targets on all interactive elements (a11y prerequisite)
- All responsive classes use Tailwind's `rtl:` variants where needed
- Playwright viewport tests passing for baseline visual regression
- No horizontal overflow on any page at 375px — clean foundation for a11y audit
