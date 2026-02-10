# SESSION 30 SPEC — Animations & Micro-interactions

> **Block:** Frontend Advanced (Sessions 26-31)
> **Complexity:** Medium
> **Depends on:** Sessions 19-29 (all UI complete)
> **Spec written:** 2026-02-10

---

## TL;DR

- Add subtle, purposeful animations that make the NPS app feel premium: page transitions, card slide-ins, loading orb, number count-up, and FC60 stamp reveal
- Create a shared `animations.css` stylesheet with CSS `@keyframes` and utility classes
- Build a `useReducedMotion` hook so every animation respects `prefers-reduced-motion`
- Create reusable animation wrapper components (`FadeIn`, `SlideIn`, `CountUp`, `StaggerChildren`)
- Modify existing components to apply animation classes where appropriate
- Zero layout shift — animations must not cause content to jump or reflow

---

## 0. Prerequisites

| Requirement                                                             | How to verify                                                                       |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| All pages exist (Dashboard, Scanner, Oracle, Vault, Learning, Settings) | `ls frontend/src/pages/*.tsx` — 6 page files                                        |
| Layout + routing working                                                | `frontend/src/App.tsx` uses `<Routes>` with `<Layout />` wrapper                    |
| Oracle reading results display                                          | `frontend/src/components/oracle/ReadingResults.tsx` renders SummaryTab, DetailsTab  |
| DetailsTab collapsible sections                                         | `frontend/src/components/oracle/DetailsTab.tsx` has `DetailSection` with open/close |
| StatsCard on Dashboard                                                  | `frontend/src/components/StatsCard.tsx` renders label + value                       |
| Tailwind configured                                                     | `frontend/tailwind.config.ts` exists                                                |
| Vitest test framework                                                   | `npx vitest run` succeeds                                                           |

**Pre-flight check (run before starting):**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
ls src/pages/Dashboard.tsx src/pages/Oracle.tsx src/pages/Scanner.tsx  # must exist
ls src/components/oracle/ReadingResults.tsx                            # must exist
ls src/components/oracle/DetailsTab.tsx                                # must exist
ls src/components/StatsCard.tsx                                        # must exist
npx tsc --noEmit 2>&1 | tail -3                                       # expect clean
```

---

## 1. Objectives

| #   | Objective                              | Deliverable                                                                                |
| --- | -------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1   | Create shared animation stylesheet     | `frontend/src/styles/animations.css` with `@keyframes` and utility classes                 |
| 2   | Create `useReducedMotion` hook         | `frontend/src/hooks/useReducedMotion.ts` — returns `boolean` from `prefers-reduced-motion` |
| 3   | Build `FadeIn` animation wrapper       | `frontend/src/components/common/FadeIn.tsx` — fade + optional translate on mount           |
| 4   | Build `SlideIn` animation wrapper      | `frontend/src/components/common/SlideIn.tsx` — slide from direction on mount               |
| 5   | Build `CountUp` number component       | `frontend/src/components/common/CountUp.tsx` — animates number from 0 to target            |
| 6   | Build `StaggerChildren` wrapper        | `frontend/src/components/common/StaggerChildren.tsx` — staggers child entry                |
| 7   | Add page transitions                   | Wrap page `<Outlet />` content with fade-in on route change                                |
| 8   | Add reading card animations            | Oracle reading sections slide/fade in on result load                                       |
| 9   | Add loading orb                        | Pulsing orb component replaces plain "Loading..." text during reading generation           |
| 10  | Add number reveal to numerology values | Life Path, Destiny, etc. count up from 0                                                   |
| 11  | Add FC60 stamp segment reveal          | Stamp parts appear one-by-one with stagger                                                 |
| 12  | Respect `prefers-reduced-motion`       | All animations disable when reduced motion is preferred                                    |

---

## 2. Files to Create

| #   | Path                                                 | Purpose                                                                     |
| --- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | `frontend/src/styles/animations.css`                 | CSS `@keyframes` definitions + animation utility classes                    |
| 2   | `frontend/src/hooks/useReducedMotion.ts`             | Hook: returns `prefersReducedMotion: boolean` from media query              |
| 3   | `frontend/src/components/common/FadeIn.tsx`          | Wrapper: fades children in on mount (opacity 0 to 1 + optional Y translate) |
| 4   | `frontend/src/components/common/SlideIn.tsx`         | Wrapper: slides children from specified direction on mount                  |
| 5   | `frontend/src/components/common/CountUp.tsx`         | Animated number: counts from 0 to value over duration                       |
| 6   | `frontend/src/components/common/StaggerChildren.tsx` | Wrapper: applies incremental delay to each child's entry animation          |
| 7   | `frontend/src/components/common/LoadingOrb.tsx`      | Pulsing green orb with label, used during reading generation                |
| 8   | `frontend/src/components/common/PageTransition.tsx`  | Wraps `<Outlet />` to apply fade on route change                            |
| 9   | `frontend/src/__tests__/animations.test.tsx`         | Unit tests for animation hooks and components                               |
| 10  | `frontend/e2e/animations.spec.ts`                    | Playwright tests for reduced-motion and no-layout-shift                     |

---

## 3. Files to Modify

| #   | Path                                                        | What Changes                                                                             |
| --- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | `frontend/tailwind.config.ts`                               | Add custom animation utilities to `theme.extend.animation` and `theme.extend.keyframes`  |
| 2   | `frontend/src/App.tsx`                                      | Import `animations.css`; wrap `<Outlet />` with `PageTransition`                         |
| 3   | `frontend/src/components/Layout.tsx`                        | Pass routing key to `PageTransition` or apply class to `<main>`                          |
| 4   | `frontend/src/components/oracle/ReadingResults.tsx`         | Wrap tab content with `FadeIn` on tab switch                                             |
| 5   | `frontend/src/components/oracle/SummaryTab.tsx`             | Wrap stat cards in `StaggerChildren`; add `FadeIn` to AI interpretation block            |
| 6   | `frontend/src/components/oracle/DetailsTab.tsx`             | Animate section expand/collapse with height transition; stagger section reveals          |
| 7   | `frontend/src/components/oracle/OracleConsultationForm.tsx` | Replace submit button loading text with `LoadingOrb`; add fade for form sections         |
| 8   | `frontend/src/components/StatsCard.tsx`                     | Use `CountUp` for numeric values; add `FadeIn` on mount                                  |
| 9   | `frontend/src/components/oracle/ReadingHistory.tsx`         | `StaggerChildren` for history items; `FadeIn` on expand                                  |
| 10  | `frontend/src/pages/Dashboard.tsx`                          | Wrap stats grid in `StaggerChildren`                                                     |
| 11  | `frontend/src/pages/Oracle.tsx`                             | Wrap sections in `FadeIn` with stagger; apply `SlideIn` to result section on new reading |
| 12  | `frontend/src/components/oracle/MultiUserSelector.tsx`      | Animate user chip add/remove                                                             |
| 13  | `frontend/src/components/oracle/ExportButton.tsx`           | Animate dropdown open/close                                                              |
| 14  | `frontend/src/locales/en.json`                              | Add `"common.loading_reading"` key for orb label                                         |
| 15  | `frontend/src/locales/fa.json`                              | Add matching Persian key                                                                 |

---

## 4. Files to Delete

None.

---

## 5. Implementation Phases

### Phase 1 — Animation Infrastructure (useReducedMotion + animations.css + Tailwind Config)

**Goal:** Create the animation foundation that all subsequent phases build on.

**Step 1.1 — Create `useReducedMotion` hook:**

File: `frontend/src/hooks/useReducedMotion.ts`

```
Hook signature:
  useReducedMotion() → boolean

Logic:
  - Use window.matchMedia("(prefers-reduced-motion: reduce)")
  - Listen for changes (user can toggle at OS level)
  - Return true if user prefers reduced motion
  - Clean up listener on unmount
  - SSR-safe: return false if window is undefined

Every animation component MUST check this hook.
If true → skip animation, render content immediately with full opacity.
```

**Step 1.2 — Create `animations.css`:**

File: `frontend/src/styles/animations.css`

```
@keyframes definitions needed:

1. nps-fade-in
   from: opacity 0, transform translateY(8px)
   to: opacity 1, transform translateY(0)

2. nps-fade-in-up
   from: opacity 0, transform translateY(16px)
   to: opacity 1, transform translateY(0)

3. nps-slide-in-left
   from: opacity 0, transform translateX(-20px)
   to: opacity 1, transform translateX(0)

4. nps-slide-in-right
   from: opacity 0, transform translateX(20px)
   to: opacity 1, transform translateX(0)

5. nps-slide-in-down
   from: opacity 0, transform translateY(-16px)
   to: opacity 1, transform translateY(0)

6. nps-scale-in
   from: opacity 0, transform scale(0.95)
   to: opacity 1, transform scale(1)

7. nps-pulse-glow
   0%: box-shadow 0 0 4px #3fb950
   50%: box-shadow 0 0 16px #3fb950, 0 0 32px #3fb95040
   100%: box-shadow 0 0 4px #3fb950

8. nps-orb-pulse
   0%: transform scale(1), opacity 1
   50%: transform scale(1.15), opacity 0.7
   100%: transform scale(1), opacity 1

9. nps-stamp-reveal
   from: opacity 0, transform scale(0.8) rotate(-5deg)
   to: opacity 1, transform scale(1) rotate(0deg)

10. nps-height-expand
    (for collapsible sections — use max-height trick)
    from: max-height 0, opacity 0
    to: max-height var(--section-height), opacity 1

Utility classes:

.nps-animate-fade-in { animation: nps-fade-in 0.3s ease-out forwards; }
.nps-animate-fade-in-up { animation: nps-fade-in-up 0.4s ease-out forwards; }
.nps-animate-slide-left { animation: nps-slide-in-left 0.3s ease-out forwards; }
.nps-animate-slide-right { animation: nps-slide-in-right 0.3s ease-out forwards; }
.nps-animate-scale-in { animation: nps-scale-in 0.2s ease-out forwards; }
.nps-animate-orb-pulse { animation: nps-orb-pulse 1.5s ease-in-out infinite; }
.nps-animate-stamp { animation: nps-stamp-reveal 0.4s ease-out forwards; }

Stagger delay classes:
.nps-delay-1 { animation-delay: 50ms; }
.nps-delay-2 { animation-delay: 100ms; }
.nps-delay-3 { animation-delay: 150ms; }
.nps-delay-4 { animation-delay: 200ms; }
.nps-delay-5 { animation-delay: 250ms; }
.nps-delay-6 { animation-delay: 300ms; }
.nps-delay-7 { animation-delay: 350ms; }
.nps-delay-8 { animation-delay: 400ms; }

Reduced motion override:
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

Initial opacity for animated elements:
.nps-animate-initial { opacity: 0; }
```

**Step 1.3 — Extend Tailwind config:**

File: `frontend/tailwind.config.ts`

Add to `theme.extend`:

```
keyframes: {
  "nps-fade-in": { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
  "nps-pulse-glow": { "0%, 100%": { boxShadow: "0 0 4px #3fb950" }, "50%": { boxShadow: "0 0 16px #3fb950, 0 0 32px #3fb95040" } },
},
animation: {
  "nps-fade-in": "nps-fade-in 0.3s ease-out forwards",
  "nps-pulse-glow": "nps-pulse-glow 2s ease-in-out infinite",
},
```

Note: The bulk of animation classes live in `animations.css` (more flexible than Tailwind plugin for complex keyframes). Only add the most-used ones to Tailwind for convenience.

**Step 1.4 — Import `animations.css` in `App.tsx`:**

Add `import "./styles/animations.css"` near the top.

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Hook exists
ls src/hooks/useReducedMotion.ts                # must exist

# Stylesheet exists
ls src/styles/animations.css                    # must exist

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5                # expect no errors

# Dev server loads without CSS errors
npm run dev &
DEV_PID=$!
sleep 3
kill $DEV_PID
```

---

### Phase 2 — Reusable Animation Components

**Goal:** Build the 5 animation wrapper components that other phases use.

**Step 2.1 — FadeIn component:**

File: `frontend/src/components/common/FadeIn.tsx`

```
Props:
  children: ReactNode
  delay?: number          — ms before animation starts (default: 0)
  duration?: number       — ms for animation (default: 300)
  direction?: "up" | "down" | "none"  — translate direction (default: "up")
  className?: string
  as?: "div" | "span"    — wrapper element (default: "div")

Behavior:
  - Check useReducedMotion(). If reduced → render children immediately, no animation
  - Otherwise:
    1. Mount with opacity: 0
    2. After delay, trigger CSS animation (using a class from animations.css)
    3. Forward fill: element stays visible after animation
  - Use CSS classes, NOT inline styles for animation (keeps things GPU-composited)
  - The element uses opacity: 0 initially via .nps-animate-initial class
  - When animation triggers, swap to .nps-animate-fade-in (or -up/-down)
  - Set animation-delay via inline style (the only inline style)
```

**Step 2.2 — SlideIn component:**

File: `frontend/src/components/common/SlideIn.tsx`

```
Props:
  children: ReactNode
  from?: "left" | "right" | "top" | "bottom"  — slide direction (default: "left")
  delay?: number
  duration?: number
  className?: string

Behavior:
  - Same reduced-motion check as FadeIn
  - Maps direction to CSS class:
    "left"  → nps-animate-slide-left
    "right" → nps-animate-slide-right
    "top"   → nps-animate-fade-in (translateY from negative)
    "bottom" → nps-animate-fade-in-up
  - RTL awareness: when dir="rtl", "left" and "right" swap
    Import useDirection from hooks if available (from Session 26)
    If useDirection unavailable (Session 26 not done), check document.dir directly
```

**Step 2.3 — CountUp component:**

File: `frontend/src/components/common/CountUp.tsx`

```
Props:
  value: number           — target number to count to
  duration?: number       — animation duration in ms (default: 800)
  delay?: number          — ms before starting (default: 0)
  decimals?: number       — decimal places (default: 0)
  prefix?: string         — e.g., "$"
  suffix?: string         — e.g., "%"
  className?: string

Behavior:
  - Check useReducedMotion(). If reduced → show final value immediately
  - Otherwise:
    1. Start at 0
    2. Use requestAnimationFrame loop
    3. Ease-out timing function (fast start, slow finish)
    4. Display current number with proper formatting
    5. Stop at exact target value (no overshoot)
  - Easing formula: easeOutCubic(t) = 1 - (1 - t)^3
  - Clean up animation frame on unmount
  - If value changes, restart animation from current displayed value to new target

Use cases:
  - StatsCard numeric values (keys tested, speed, etc.)
  - Numerology number displays (Life Path: 7 counts from 0 to 7)
  - Confidence percentage
  - Energy level
```

**Step 2.4 — StaggerChildren component:**

File: `frontend/src/components/common/StaggerChildren.tsx`

```
Props:
  children: ReactNode
  staggerMs?: number      — delay between each child (default: 50ms)
  baseDelay?: number      — initial delay before first child (default: 0)
  animation?: "fade" | "slide" | "scale"  — animation type for children (default: "fade")
  className?: string

Behavior:
  - Check useReducedMotion(). If reduced → render all children immediately
  - Otherwise:
    1. Iterate over React.Children
    2. Wrap each child in a FadeIn/SlideIn with increasing delay
    3. Child 0: baseDelay + 0ms
    4. Child 1: baseDelay + staggerMs
    5. Child 2: baseDelay + staggerMs * 2
    6. ...and so on
  - Use React.Children.map to preserve child keys
  - Maximum stagger cap: 800ms total (prevents long waits for many children)
```

**Step 2.5 — LoadingOrb component:**

File: `frontend/src/components/common/LoadingOrb.tsx`

```
Props:
  label?: string          — text below orb (default: "Loading...")
  size?: "sm" | "md" | "lg"  — orb diameter (default: "md")
  className?: string

Behavior:
  - Renders a circular div with nps-success (#3fb950) glow
  - Uses nps-animate-orb-pulse for breathing effect
  - Text label below with text-nps-text-dim
  - Reduced motion: still shows orb but with static glow (no pulse)

Sizing:
  sm: w-4 h-4, text-xs label
  md: w-8 h-8, text-sm label
  lg: w-12 h-12, text-base label

Visual:
  - Circular shape: rounded-full
  - Background: bg-nps-success/20
  - Border: border border-nps-success/40
  - Inner glow: box-shadow via nps-pulse-glow animation
  - Center dot: small solid circle inside
```

**Step 2.6 — PageTransition component:**

File: `frontend/src/components/common/PageTransition.tsx`

```
Props:
  children: ReactNode
  locationKey: string     — from useLocation().key (triggers re-animation on route change)

Behavior:
  - Check useReducedMotion(). If reduced → render children directly
  - Otherwise:
    1. When locationKey changes, apply nps-animate-fade-in to wrapper
    2. Reset animation when key changes (remove + re-add class via key prop)
  - Implementation: Use React key prop on wrapper div keyed by locationKey
    This forces React to unmount/remount, triggering CSS animation fresh
  - Keep it simple: no exit animations (they add complexity for minimal UX gain)
    Just fade-in the new page content
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# All components exist
ls src/components/common/FadeIn.tsx           # must exist
ls src/components/common/SlideIn.tsx          # must exist
ls src/components/common/CountUp.tsx          # must exist
ls src/components/common/StaggerChildren.tsx  # must exist
ls src/components/common/LoadingOrb.tsx       # must exist
ls src/components/common/PageTransition.tsx   # must exist

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5              # expect no errors
```

---

### Phase 3 — Page Transitions

**Goal:** Add smooth fade-in when navigating between pages.

**Step 3.1 — Wire PageTransition into Layout:**

Modify `frontend/src/components/Layout.tsx`:

```
Current <main> section:
  <main className="flex-1 p-6 overflow-auto">
    <Outlet />
  </main>

Change to:
  Import { useLocation } from "react-router-dom"
  Import { PageTransition } from "./common/PageTransition"

  const location = useLocation();

  <main className="flex-1 p-6 overflow-auto">
    <PageTransition locationKey={location.key}>
      <Outlet />
    </PageTransition>
  </main>

This causes page content to fade in when navigating between
Dashboard, Scanner, Oracle, Vault, Learning, Settings.
```

**Step 3.2 — Verify no layout shift:**

```
Critical check: the PageTransition wrapper must NOT:
  - Add extra height/margin/padding
  - Cause scrollbar to appear/disappear during animation
  - Shift sidebar position
  - Flash white/empty during transition

The wrapper div should be:
  - display: contents (no box) OR
  - min-height: 100% to prevent content jump
  - overflow: hidden during animation (prevents horizontal scroll from translateX)
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

npm run dev &
DEV_PID=$!
sleep 3

echo "Manual check:"
echo "1. Navigate between pages using sidebar"
echo "2. Content should fade in smoothly"
echo "3. No white flash between pages"
echo "4. No layout shift (sidebar stays fixed)"
echo "5. No scrollbar flicker"

kill $DEV_PID
```

---

### Phase 4 — Oracle Reading Animations

**Goal:** Add animations to Oracle reading flow — form submission, result appearance, detail sections.

**Step 4.1 — Loading orb during reading generation:**

Modify `frontend/src/components/oracle/OracleConsultationForm.tsx`:

```
Current:
  The submit button shows t("common.loading") text when isSubmitting

Change:
  When isSubmitting, instead of (or in addition to) the button text change,
  show a LoadingOrb below the form with label t("common.loading_reading")

  The orb appears between the form and the results section,
  centered, with a fade-in animation.

  Add to locales:
    en.json: "common.loading_reading": "Consulting the Oracle..."
    fa.json: "common.loading_reading": "در حال مشورت با اوراکل..."
```

**Step 4.2 — Reading results slide-in:**

Modify `frontend/src/pages/Oracle.tsx`:

```
Current:
  The Reading Results section renders immediately when consultationResult is set

Change:
  When consultationResult changes from null to a value,
  wrap the results section in <SlideIn from="bottom">
  This makes the reading results slide up into view

  Use a key prop on SlideIn tied to a counter/timestamp
  so it re-animates each time a new reading arrives
  (not just on first load)
```

**Step 4.3 — Tab content animation:**

Modify `frontend/src/components/oracle/ReadingResults.tsx`:

```
Current:
  Tab panels use hidden class to show/hide
  (all panels are rendered, visibility toggled via CSS)

Change:
  When a tab becomes active, wrap its content in <FadeIn>
  Use the activeTab value as a key so the FadeIn re-triggers on tab switch

  Alternative approach (simpler):
    Instead of hidden class, use conditional rendering:
    {activeTab === "summary" && <FadeIn><SummaryTab .../></FadeIn>}
    This triggers fresh animation each time user switches tabs

  Choose the approach that feels smoother.
  The hidden-class approach is better for performance (no remount).
  Add CSS animation class to the shown panel instead:
    className={activeTab === tab ? "nps-animate-fade-in" : "hidden"}
```

**Step 4.4 — Summary stat stagger:**

Modify `frontend/src/components/oracle/SummaryTab.tsx`:

```
Current:
  Quick stats rendered in a flex container

Change:
  Wrap the stats flex container in <StaggerChildren staggerMs={60}>
  Each stat span fades in with incremental delay

  For numerology numbers (life_path, energy_level):
  Replace static number with <CountUp value={number} duration={600} />
```

**Step 4.5 — Detail section expand animation:**

Modify `frontend/src/components/oracle/DetailsTab.tsx`:

```
Current DetailSection behavior:
  {open && <div className="px-3 pb-3 ...">children</div>}
  Content appears/disappears instantly

Change:
  Replace instant show/hide with animated height transition:
  1. Always render the content div (not conditional)
  2. Use CSS:
     - When closed: max-height: 0, overflow: hidden, opacity: 0
     - When open: max-height: 500px (or auto via JS), overflow: visible, opacity: 1
     - Transition: max-height 0.3s ease, opacity 0.2s ease
  3. This creates a smooth expand/collapse animation

  Also: wrap each DetailSection in <FadeIn> with stagger when
  the reading first loads (sections appear one by one)

  Chevron rotation:
  Current: ▲ / ▼ swap
  Change: Use a single ▼ character that rotates:
    - Closed: rotate(0deg)
    - Open: rotate(180deg)
    - Transition: transform 0.2s ease
```

**Step 4.6 — FC60 stamp segment reveal:**

Modify `frontend/src/components/oracle/DetailsTab.tsx` (FC60 section):

```
When FC60 section opens, the DataRow items appear with stagger:
  Wrap FC60 DataRows in <StaggerChildren staggerMs={40}>

For the FC60 stamp value (if fc60_extended.stamp is displayed):
  Apply .nps-animate-stamp class to the stamp display
  This makes the stamp scale-in with a slight rotation
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5

# Existing tests still pass
npx vitest run --reporter=verbose 2>&1 | tail -20

# Manual check:
echo "1. Submit oracle reading — loading orb appears"
echo "2. Results slide in from bottom"
echo "3. Switch tabs — content fades in"
echo "4. Open FC60 details — rows stagger in"
echo "5. Expand/collapse sections — smooth height animation"
echo "6. Numbers count up in Summary stats"
```

---

### Phase 5 — Dashboard & Remaining Component Animations

**Goal:** Apply animations to Dashboard and remaining components.

**Step 5.1 — Dashboard stats grid:**

Modify `frontend/src/pages/Dashboard.tsx`:

```
Current:
  Stats grid renders StatsCards immediately

Change:
  Wrap the grid in <StaggerChildren staggerMs={80}>
  Each StatsCard fades in with delay
```

**Step 5.2 — StatsCard number animation:**

Modify `frontend/src/components/StatsCard.tsx`:

```
Current:
  <p className="text-2xl font-mono font-bold mt-1">{value}</p>

Change:
  If value is a number (or numeric string), use CountUp:
    <CountUp value={numericValue} duration={800} className="..." />
  If value is a string with suffix (e.g., "0/s"), parse number and pass suffix:
    <CountUp value={0} suffix="/s" duration={800} className="..." />
  If value is non-numeric, render as-is (no animation)

  Wrap the card itself in <FadeIn> for entry animation
```

**Step 5.3 — MultiUserSelector chip animation:**

Modify `frontend/src/components/oracle/MultiUserSelector.tsx`:

```
When a user chip is added:
  Apply nps-animate-scale-in to the new chip
  This creates a subtle pop-in effect

When a user chip is removed:
  CSS exit animation is harder without a library.
  Simplest approach: don't animate removal (instant disappear is fine)
  Alternative: apply opacity 0 + scale(0.9) with transition before removing from DOM
  (requires a timeout pattern — keep it simple, skip exit animation)
```

**Step 5.4 — ReadingHistory list stagger:**

Modify `frontend/src/components/oracle/ReadingHistory.tsx`:

```
Wrap reading history list items in <StaggerChildren staggerMs={30}>
Each history entry fades in with slight delay

When a history item expands:
  Apply <FadeIn> to the expanded content div
```

**Step 5.5 — ExportButton dropdown animation:**

Modify `frontend/src/components/oracle/ExportButton.tsx`:

```
When dropdown opens:
  Apply nps-animate-scale-in to the dropdown container
  This creates a pop-in effect from the button origin

When dropdown closes:
  Instant hide (no exit animation needed)
```

**Step 5.6 — Oracle page section stagger:**

Modify `frontend/src/pages/Oracle.tsx`:

```
The three oracle sections (User Profile, Consultation, Results)
should stagger in when the page loads:

  <FadeIn delay={0}>User Profile section</FadeIn>
  <FadeIn delay={100}>Consultation section</FadeIn>
  <FadeIn delay={200}>Results section</FadeIn>

OR use <StaggerChildren staggerMs={100}> around the three sections.
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# TypeScript compiles
npx tsc --noEmit 2>&1 | tail -5

# All existing tests pass
npx vitest run --reporter=verbose 2>&1 | tail -20

echo "Manual check:"
echo "1. Dashboard — stats cards stagger in, numbers count up"
echo "2. Oracle — three sections stagger in on page load"
echo "3. Add user chip — subtle pop-in animation"
echo "4. History items — stagger in on tab switch"
echo "5. Export dropdown — pop-in on open"
```

---

### Phase 6 — Reduced Motion + Polish

**Goal:** Verify `prefers-reduced-motion` is fully respected and polish animation timing.

**Step 6.1 — Verify reduced motion works everywhere:**

```
Test procedure:
  1. Open Chrome DevTools → Rendering panel
  2. Enable "Emulate CSS media feature prefers-reduced-motion: reduce"
  3. Navigate through ALL pages
  4. Verify: NO animations play
     - No fade-ins
     - No slide-ins
     - No count-ups (number shows final value immediately)
     - No orb pulse (orb renders static)
     - No stagger (all children appear at once)
     - No page transitions (content appears instantly)
  5. Content is still visible and functional (no stuck opacity: 0 elements)
```

**Step 6.2 — Check for layout shift:**

```
Test procedure:
  1. Open Chrome DevTools → Performance tab
  2. Record a page navigation sequence
  3. Check CLS (Cumulative Layout Shift) metric
  4. Target: CLS < 0.1 (good score)
  5. If layout shift detected:
     - Check that animated elements have explicit dimensions
     - Ensure opacity animations don't cause reflow
     - Verify transform-only animations (GPU composited, no layout trigger)
```

**Step 6.3 — Timing consistency:**

```
Ensure all animation durations follow a consistent scale:
  - Micro (hover, focus): 150ms
  - Small (fade, scale): 200-300ms
  - Medium (slide, expand): 300-400ms
  - Large (page transition): 300-400ms
  - Count-up: 600-1000ms (longer for bigger numbers)

Easing consistency:
  - Entries: ease-out (fast start → gentle stop)
  - Exits: ease-in (gentle start → fast finish)
  - Continuous (orb pulse): ease-in-out
  - Interactive (hover): ease or linear

All durations defined as CSS custom properties in animations.css:
  :root {
    --nps-duration-micro: 150ms;
    --nps-duration-sm: 250ms;
    --nps-duration-md: 350ms;
    --nps-duration-lg: 400ms;
    --nps-duration-count: 800ms;
  }
```

**Step 6.4 — Performance check:**

```
Animations must use ONLY compositable properties:
  GOOD: opacity, transform (translateX/Y, scale, rotate)
  BAD: width, height, margin, padding, top/left/right/bottom, color

Exception: max-height for collapsible sections (acceptable — not used in scroll path)

Check: No animation should trigger layout or paint
  - DevTools → Performance → check for purple (layout) bars during animation
  - All animations should show only green (paint) or nothing (GPU composited)
```

**STOP checkpoint:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Full test suite
npx vitest run --reporter=verbose

# TypeScript clean
npx tsc --noEmit

# Lint clean
npx eslint src/ --ext .ts,.tsx

echo "Reduced motion verified: all animations disabled when preference set"
echo "Layout shift check: CLS < 0.1"
echo "Performance check: transform + opacity only (GPU composited)"
```

---

### Phase 7 — Tests

**Goal:** Write unit tests for animation components and Playwright tests for visual/reduced-motion.

**Step 7.1 — Unit tests (`frontend/src/__tests__/animations.test.tsx`):**

```
Test 1: useReducedMotion returns false by default
  Setup: default matchMedia mock (no preference set)
  Assert: hook returns false

Test 2: useReducedMotion returns true when preference is set
  Setup: mock matchMedia to return matches: true for prefers-reduced-motion
  Assert: hook returns true

Test 3: useReducedMotion updates on media query change
  Setup: mock matchMedia, initially false
  Act: trigger change event with matches: true
  Assert: hook returns true after update

Test 4: FadeIn renders children
  Render: <FadeIn>Hello</FadeIn>
  Assert: "Hello" is in the document

Test 5: FadeIn applies animation class
  Setup: mock useReducedMotion → false
  Render: <FadeIn>Content</FadeIn>
  Assert: wrapper element has animation-related class (nps-animate-fade-in or similar)

Test 6: FadeIn skips animation when reduced motion preferred
  Setup: mock useReducedMotion → true
  Render: <FadeIn>Content</FadeIn>
  Assert: wrapper element does NOT have animation class
  Assert: content is visible (opacity: 1 or no opacity style)

Test 7: CountUp displays final value
  Render: <CountUp value={42} />
  Wait: for animation to complete (or mock timers)
  Assert: "42" is displayed in the document

Test 8: CountUp shows final value immediately when reduced motion
  Setup: mock useReducedMotion → true
  Render: <CountUp value={42} />
  Assert: "42" is displayed immediately (no animation needed)

Test 9: CountUp handles value change
  Render: <CountUp value={10} />
  Wait: animation completes
  Rerender: <CountUp value={20} />
  Wait: animation completes
  Assert: "20" is displayed

Test 10: StaggerChildren renders all children
  Render: <StaggerChildren><div>A</div><div>B</div><div>C</div></StaggerChildren>
  Assert: A, B, C all in document

Test 11: LoadingOrb renders with label
  Render: <LoadingOrb label="Loading..." />
  Assert: "Loading..." is in the document

Test 12: LoadingOrb applies pulse animation class
  Setup: mock useReducedMotion → false
  Render: <LoadingOrb />
  Assert: orb element has pulse animation class

Test 13: PageTransition re-animates on key change
  Render: <PageTransition locationKey="page-1">Page 1</PageTransition>
  Assert: "Page 1" visible
  Rerender: <PageTransition locationKey="page-2">Page 2</PageTransition>
  Assert: "Page 2" visible with animation class re-applied

Test 14: SlideIn applies correct direction class
  Render: <SlideIn from="left">Content</SlideIn>
  Assert: wrapper has slide-left animation class
  Render: <SlideIn from="right">Content</SlideIn>
  Assert: wrapper has slide-right animation class

Test 15: DetailSection expand animates (integration)
  Render: DetailsTab with a mock reading result
  Act: click FC60 section header
  Assert: section content appears with animation (has transition or animation styles)
```

**Step 7.2 — Playwright tests (`frontend/e2e/animations.spec.ts`):**

```
Test 16: Page transition fires on navigation
  Navigate: /dashboard
  Click: Oracle nav link
  Wait: 400ms
  Assert: Oracle page content is visible
  Assert: no layout shift during transition (check bounding box stability)

Test 17: Reduced motion disables all animations
  Set: emulateMedia({ reducedMotion: "reduce" })
  Navigate: /oracle
  Assert: all content visible immediately (no opacity: 0 elements)
  Assert: no animation CSS classes with non-zero duration applied

Test 18: Loading orb appears during reading
  Navigate: /oracle
  Mock: API to delay 2 seconds
  Submit: reading request
  Assert: LoadingOrb component is visible
  Wait: API resolves
  Assert: LoadingOrb disappears, results appear
```

**STOP checkpoint — final:**

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend

# Unit tests pass
npx vitest run src/__tests__/animations.test.tsx --reporter=verbose

# All tests pass (regression check)
npx vitest run --reporter=verbose

# TypeScript clean
npx tsc --noEmit

# Lint clean
npx eslint src/ --ext .ts,.tsx

# Playwright tests (if Playwright installed)
npx playwright test e2e/animations.spec.ts --reporter=list
```

---

## 6. Acceptance Criteria

| #   | Criterion                                       | How to Verify                                                  |
| --- | ----------------------------------------------- | -------------------------------------------------------------- |
| 1   | `animations.css` with 10+ keyframe definitions  | `grep -c '@keyframes' src/styles/animations.css` returns >= 10 |
| 2   | `useReducedMotion` hook works                   | Unit tests 1-3 pass                                            |
| 3   | FadeIn component animates on mount              | Unit tests 4-6 pass                                            |
| 4   | CountUp component counts to target              | Unit tests 7-9 pass                                            |
| 5   | StaggerChildren renders all children with delay | Unit test 10 passes                                            |
| 6   | LoadingOrb renders and pulses                   | Unit tests 11-12 pass                                          |
| 7   | Page transitions fire on navigation             | Navigate Dashboard → Oracle → Vault — content fades in         |
| 8   | Reading results animate in                      | Submit reading → results slide in from bottom                  |
| 9   | Tab switch animates                             | Click Summary → Details → History — fade-in on each            |
| 10  | Detail sections expand smoothly                 | Click FC60 section — smooth height transition                  |
| 11  | Numbers count up                                | Life Path, energy level values count from 0 to final           |
| 12  | `prefers-reduced-motion` fully respected        | Enable preference → zero animations, all content visible       |
| 13  | No layout shift                                 | CLS < 0.1 during any animation                                 |
| 14  | Only compositable properties used               | transform + opacity (no width/height/margin animations)        |
| 15  | All 18 tests pass                               | `npx vitest run` + `npx playwright test` all green             |
| 16  | No regressions                                  | All pre-existing tests still pass                              |

---

## 7. Error Scenarios

| Scenario                                                    | Expected Behavior                                                                                                                                                   |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Browser doesn't support `matchMedia`                        | `useReducedMotion` returns `false` (animations play); wrapped in try/catch                                                                                          |
| CSS `@keyframes` not loaded (broken import path)            | Components still render — just without animation. FadeIn shows content at opacity 1 as fallback. Verify import path is correct in `App.tsx`                         |
| CountUp receives `NaN` or `Infinity`                        | Guard: if `!isFinite(value)`, render "—" placeholder instead of animating                                                                                           |
| CountUp receives negative number                            | Count down from 0 to negative (same easing, reversed direction)                                                                                                     |
| Animation blocks interaction (user clicks during fade-in)   | All animated elements must be interactive immediately — use `pointer-events: auto` even while animating. Never disable clicks during entry animation                |
| Too many StaggerChildren items (50+)                        | Cap total stagger at 800ms. Children beyond cap appear at the cap delay (no further increase)                                                                       |
| Page transition race condition (rapid navigation)           | React key-based remount handles this: each PageTransition instance is independent. Old one unmounts, new one mounts fresh                                           |
| Reduced motion not detected on first render (SSR/hydration) | Default to `false` (animations enabled). After hydration, `useEffect` picks up real preference. Brief flash is acceptable — CSS `@media` override catches it anyway |
| `requestAnimationFrame` not available (test environment)    | CountUp falls back to `setTimeout`. Or in tests, mock `requestAnimationFrame`                                                                                       |
| Detail section max-height too small for content             | Use a generous max-height (e.g., 2000px) or compute actual height via `scrollHeight` ref measurement. If using computed height, set as CSS custom property          |

---

## 8. Handoff

**What Session 31 needs to know:**

- Animation infrastructure is complete: `animations.css`, `useReducedMotion`, 6 animation components
- All Oracle components, Dashboard, and Layout have animations applied
- `prefers-reduced-motion` is respected at both CSS level (`@media` in `animations.css`) and component level (`useReducedMotion` hook)
- Animations use only `opacity` and `transform` (GPU composited, no layout triggers)
- Duration variables are defined as CSS custom properties in `animations.css` under `:root`

**Session 31 (Frontend Polish & Performance) should:**

- Check that animations don't bloat bundle size (CSS is small, but verify)
- Verify animation performance on low-end devices (throttle CPU in DevTools)
- Include animations.css in Tailwind purge whitelist (classes are used dynamically)
- Lighthouse audit should still score 90+ with animations enabled
- Bundle analysis: `animations.css` + animation components should be < 5KB total

**Key files for Session 31 to read:**

- `frontend/src/styles/animations.css` — all keyframe definitions
- `frontend/src/hooks/useReducedMotion.ts` — motion preference detection
- `frontend/src/components/common/FadeIn.tsx` — primary animation wrapper
- `frontend/src/components/common/CountUp.tsx` — number animation
- `frontend/src/components/common/LoadingOrb.tsx` — loading indicator

---

## Appendix A — Animation Component Quick Reference

```
COMPONENT         | USAGE                                        | REDUCED MOTION
──────────────────┼──────────────────────────────────────────────┼────────────────
FadeIn            | <FadeIn delay={100}>content</FadeIn>         | Shows immediately
SlideIn           | <SlideIn from="left">content</SlideIn>       | Shows immediately
CountUp           | <CountUp value={42} duration={800} />        | Shows "42" instantly
StaggerChildren   | <StaggerChildren staggerMs={50}>items</...>  | Shows all at once
LoadingOrb        | <LoadingOrb label="Loading..." />            | Static orb, no pulse
PageTransition    | <PageTransition locationKey={key}>page</...> | Shows immediately

CSS classes (from animations.css):
  .nps-animate-fade-in      — opacity 0→1 + translateY 8→0
  .nps-animate-fade-in-up   — opacity 0→1 + translateY 16→0
  .nps-animate-slide-left   — opacity 0→1 + translateX -20→0
  .nps-animate-slide-right  — opacity 0→1 + translateX 20→0
  .nps-animate-scale-in     — opacity 0→1 + scale 0.95→1
  .nps-animate-orb-pulse    — scale + opacity breathing
  .nps-animate-stamp        — scale + rotate stamp reveal
  .nps-animate-initial      — opacity: 0 (starting state)
  .nps-delay-{1-8}          — stagger delays (50ms increments)
```

---

## Appendix B — Animation Decision Rationale

```
WHY CSS ANIMATIONS (not Framer Motion or React Spring):
  1. Zero bundle size increase — CSS is native
  2. GPU composited — transform + opacity only
  3. No JavaScript during animation — main thread free
  4. prefers-reduced-motion works at CSS level automatically
  5. Simple animations don't need a physics engine
  6. The app's animations are subtle micro-interactions, not complex choreography

WHEN TO UPGRADE TO FRAMER MOTION (if needed later):
  - Exit animations (elements animating OUT)
  - Layout animations (elements moving between positions)
  - Gesture-driven animations (drag, spring physics)
  - Shared layout transitions (morph between views)
  If Session 31 or later needs these, install framer-motion then.

WHY NO EXIT ANIMATIONS:
  - React unmount is instant — CSS can't animate something being removed
  - Exit animations require either:
    a. Animation library (framer-motion AnimatePresence)
    b. Timeout + state management (complex, error-prone)
  - Entry-only animations provide 90% of the "premium feel" at 10% of the complexity
  - If exit animations are needed later, add framer-motion in Session 31
```

---

## Appendix C — Testing Reduced Motion

```bash
# Chrome DevTools method:
# 1. Open DevTools (F12)
# 2. Ctrl+Shift+P → "Show Rendering"
# 3. Scroll down to "Emulate CSS media feature prefers-reduced-motion"
# 4. Select "prefers-reduced-motion: reduce"

# macOS system setting:
# System Preferences → Accessibility → Display → Reduce Motion

# Firefox method:
# about:config → ui.prefersReducedMotion → 1

# Playwright method:
# page.emulateMedia({ reducedMotion: "reduce" })
```
