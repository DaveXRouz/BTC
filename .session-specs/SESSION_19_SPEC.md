# SESSION 19 SPEC: Frontend Layout & Navigation

**Block:** Frontend Core (Sessions 19-25)
**Complexity:** High
**Dependencies:** Sessions 1-18 (all backend work complete)
**Estimated phases:** 10

---

## Overview

Session 19 establishes the visual foundation for the entire NPS frontend. It replaces the current minimal layout with a polished, professional dark-themed interface featuring a collapsible sidebar, top bar, theme switching, locale switching with RTL support, and lazy-loaded routing. Every subsequent frontend session (20-31) builds on these components.

### The Core Problem

The existing frontend has a functional but minimal layout:

- `Layout.tsx` (57 lines) — A basic sidebar with 6 NavLink items and an Outlet. No top bar, no footer, no mobile collapse, no theme toggle, no user info.
- `App.tsx` (34 lines) — Direct imports of all pages (no lazy loading), basic Routes with Navigate redirect.
- `LanguageToggle.tsx` (39 lines) — Simple EN/FA button with accent highlighting. No flag icons, no persistence indicator, no connection to theme.
- `tailwind.config.ts` (62 lines) — Legacy color palette (`nps-bg: #0d1117`, `nps-gold: #d4a017`, etc.) from the old GUI. Needs updating to the new Black (#0A0A0A) + Emerald Green (#10B981) design system.
- `index.css` (38 lines) — Basic Tailwind directives + RTL body rule + scrollbar styles. No CSS variables for theming.

The new design system requires:

1. **Black + Emerald Green palette** replacing the old GitHub-dark blue/gold palette
2. **Dark/light mode** with system preference detection and localStorage persistence
3. **Collapsible sidebar** that collapses to icons on mobile, expands on desktop
4. **Top bar** with user info placeholder, locale toggle, and theme toggle
5. **Footer** with version info
6. **Lazy-loaded routing** for all pages
7. **Admin-only navigation items** hidden for non-admin users
8. **Scanner "Coming Soon"** stub in navigation

---

## Files to Modify

| File                                         | Action  | Current Lines | Notes                                                |
| -------------------------------------------- | ------- | ------------- | ---------------------------------------------------- |
| `frontend/src/components/Layout.tsx`         | REWRITE | 57            | Sidebar + top bar + footer + mobile collapse         |
| `frontend/src/components/LanguageToggle.tsx` | REWRITE | 39            | Flag labels, better styling, theme-aware colors      |
| `frontend/src/App.tsx`                       | REWRITE | 34            | Lazy imports, Suspense wrapper, theme provider       |
| `frontend/tailwind.config.ts`                | REWRITE | 62            | New color palette, dark mode class strategy          |
| `frontend/src/index.css`                     | REWRITE | 38            | CSS variables for dark/light, scrollbar, transitions |
| `frontend/src/locales/en.json`               | MODIFY  | 190           | Add nav, layout, theme translation keys              |
| `frontend/src/locales/fa.json`               | MODIFY  | 190           | Add nav, layout, theme translation keys (Persian)    |

## Files to Create

| File                                                     | Purpose                                                                       |
| -------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `frontend/src/components/Navigation.tsx`                 | Sidebar navigation component with items, icons, collapse logic, admin gating  |
| `frontend/src/components/ThemeToggle.tsx`                | Dark/light mode toggle with system preference detection                       |
| `frontend/src/hooks/useTheme.ts`                         | Theme state hook: dark/light/system, localStorage persistence, class toggling |
| `frontend/src/styles/theme.css`                          | CSS custom properties for dark/light theme variables                          |
| `frontend/src/components/__tests__/Layout.test.tsx`      | Layout component tests                                                        |
| `frontend/src/components/__tests__/Navigation.test.tsx`  | Navigation component tests                                                    |
| `frontend/src/components/__tests__/ThemeToggle.test.tsx` | Theme toggle tests                                                            |
| `frontend/src/hooks/__tests__/useTheme.test.ts`          | Theme hook tests                                                              |
| `frontend/src/pages/__tests__/App.test.tsx`              | Routing and lazy loading tests                                                |

## Reference Files (Read-Only)

| File                               | Purpose                                                  |
| ---------------------------------- | -------------------------------------------------------- |
| `frontend/src/pages/Dashboard.tsx` | Existing page stub (26 lines) — verify it renders        |
| `frontend/src/pages/Oracle.tsx`    | Existing page (188 lines) — main feature, verify routing |
| `frontend/src/pages/Settings.tsx`  | Existing page stub (26 lines) — verify it renders        |
| `frontend/src/pages/Scanner.tsx`   | Existing page stub (26 lines) — "Coming Soon" target     |
| `frontend/src/pages/Vault.tsx`     | Existing page — verify routing                           |
| `frontend/src/pages/Learning.tsx`  | Existing page — verify routing                           |
| `frontend/src/test/testUtils.tsx`  | Existing test utilities with `renderWithProviders`       |
| `frontend/src/i18n/config.ts`      | i18n setup — verify localStorage key `nps_language`      |
| `frontend/src/main.tsx`            | Entry point — no changes needed                          |
| `frontend/vitest.config.ts`        | Test config — no changes needed                          |

---

## PHASE 1: CSS Theme Variables & Design Tokens

**Goal:** Create the CSS custom property layer that powers dark/light mode switching.

### What Changes

Create `frontend/src/styles/theme.css` with CSS custom properties for both themes. This file is imported in `index.css` and provides the variables that Tailwind config references.

### Design Tokens

```
Dark Mode (default):
  --nps-bg:            #0A0A0A    (primary background)
  --nps-bg-card:       #111111    (card/panel background)
  --nps-bg-sidebar:    #0D0D0D    (sidebar background)
  --nps-bg-input:      #1A1A1A    (input fields)
  --nps-bg-hover:      #1A1A1A    (hover state)
  --nps-border:        #1F1F1F    (borders)
  --nps-border-active: #10B981    (active/focus borders — emerald)
  --nps-text:          #D1D5DB    (primary text — gray-300)
  --nps-text-bright:   #F9FAFB    (headings — gray-50)
  --nps-text-dim:      #6B7280    (secondary text — gray-500)
  --nps-accent:        #10B981    (emerald green — primary accent)
  --nps-accent-hover:  #059669    (emerald-600 — hover)
  --nps-accent-dim:    #065F46    (emerald-800 — subtle)
  --nps-shadow:        0 4px 6px -1px rgba(16, 185, 129, 0.1)  (green-tinted)

Light Mode:
  --nps-bg:            #FFFFFF
  --nps-bg-card:       #F9FAFB
  --nps-bg-sidebar:    #F3F4F6
  --nps-bg-input:      #F3F4F6
  --nps-bg-hover:      #E5E7EB
  --nps-border:        #E5E7EB
  --nps-border-active: #059669
  --nps-text:          #1F2937
  --nps-text-bright:   #111827
  --nps-text-dim:      #6B7280
  --nps-accent:        #059669    (darker emerald for light bg contrast)
  --nps-accent-hover:  #047857
  --nps-accent-dim:    #D1FAE5
  --nps-shadow:        0 4px 6px -1px rgba(0, 0, 0, 0.1)
```

### Implementation Details

The CSS file uses `:root` for dark mode (default) and `:root.light` for light mode. The `useTheme` hook manages the `light` class on `<html>`.

Existing color-specific classes in oracle components (`nps-oracle-bg`, `nps-oracle-border`, `nps-ai-bg`, etc.) must be preserved as static colors in the Tailwind config — they don't change with theme. Only the global layout/chrome colors switch.

### STOP CHECKPOINT 1

- [ ] `frontend/src/styles/theme.css` exists with dark and light variable blocks
- [ ] Variables cover: bg, card, sidebar, input, hover, border, text (3 levels), accent (3 levels), shadow
- [ ] Dark mode is the `:root` default
- [ ] Light mode activates via `:root.light` class

---

## PHASE 2: Tailwind Config Rewrite

**Goal:** Replace the legacy color palette with the new design system while preserving oracle/ai-specific colors.

### What Changes

Rewrite `frontend/tailwind.config.ts` to:

1. Enable `darkMode: 'class'` strategy (the `light` class toggles light mode; absence = dark)
2. Replace `nps.bg`, `nps.text`, `nps.border`, `nps.gold`, `nps.accent` colors with CSS variable references: `var(--nps-bg)`, `var(--nps-text)`, etc.
3. Keep `nps.oracle.*`, `nps.ai.*`, `nps.score.*` as static colors (they don't change with theme)
4. Add new semantic color keys: `nps.accent` (emerald), `nps.sidebar`, `nps.hover`
5. Keep font families: Inter (sans) + JetBrains Mono (mono)
6. Add green-tinted shadow utility: `shadow-nps` using `var(--nps-shadow)`

### Color Migration Map

```
OLD                          → NEW
nps-bg (#0d1117)             → nps-bg (var(--nps-bg))
nps-bg-card (#161b22)        → nps-bg-card (var(--nps-bg-card))
nps-bg-input (#21262d)       → nps-bg-input (var(--nps-bg-input))
nps-bg-hover (#1c2128)       → nps-bg-hover (var(--nps-bg-hover))
nps-bg-button (#1f6feb)      → KEEP (standalone utility blue)
nps-bg-danger (#da3633)      → KEEP (standalone utility red)
nps-bg-success (#238636)     → KEEP (standalone utility green)
nps-border (#30363d)         → nps-border (var(--nps-border))
nps-text (#c9d1d9)           → nps-text (var(--nps-text))
nps-text-dim (#8b949e)       → nps-text-dim (var(--nps-text-dim))
nps-text-bright (#f0f6fc)    → nps-text-bright (var(--nps-text-bright))
nps-gold (#d4a017)           → REMOVE (replaced by nps-accent)
nps-accent (#58a6ff)         → nps-accent (var(--nps-accent))
nps-oracle-* (static blues)  → KEEP as-is
nps-ai-* (static purples)    → KEEP as-is
nps-score-* (static)         → KEEP as-is
nps-success/warning/error    → KEEP as-is
```

### STOP CHECKPOINT 2

- [ ] `frontend/tailwind.config.ts` uses CSS variable references for theme-switchable colors
- [ ] `darkMode: 'class'` is configured
- [ ] Oracle-specific and AI-specific colors preserved as static values
- [ ] Font families unchanged (Inter + JetBrains Mono)
- [ ] No TypeScript errors in the config

---

## PHASE 3: useTheme Hook

**Goal:** Create a React hook that manages dark/light/system theme preference with persistence.

### What Creates

**File:** `frontend/src/hooks/useTheme.ts`

### Hook API

```typescript
type ThemeMode = "dark" | "light" | "system";

interface UseThemeReturn {
  theme: ThemeMode; // Current preference (what user chose)
  resolvedTheme: "dark" | "light"; // Actual applied theme
  setTheme: (mode: ThemeMode) => void;
  toggleTheme: () => void; // Cycles: dark → light → system → dark
}
```

### Implementation Details

1. **Initialization:** Read from `localStorage` key `nps_theme`. Default to `'dark'` if no stored value.
2. **System detection:** Use `window.matchMedia('(prefers-color-scheme: dark)')` when mode is `'system'`.
3. **Class management:** Add/remove `light` class on `document.documentElement`:
   - If resolvedTheme is `'dark'`: remove `light` class (dark is default in CSS)
   - If resolvedTheme is `'light'`: add `light` class
4. **MediaQuery listener:** When mode is `'system'`, listen for `change` events on the media query and update class accordingly. Clean up listener on unmount or mode change.
5. **Persistence:** Write to `localStorage` key `nps_theme` on every `setTheme` call.

### STOP CHECKPOINT 3

- [ ] `frontend/src/hooks/useTheme.ts` exports `useTheme` hook
- [ ] Returns `theme`, `resolvedTheme`, `setTheme`, `toggleTheme`
- [ ] Persists to `localStorage` key `nps_theme`
- [ ] Adds/removes `light` class on `<html>`
- [ ] Handles `'system'` mode with media query listener

---

## PHASE 4: ThemeToggle Component

**Goal:** Create a toggle button component for switching between dark and light mode.

### What Creates

**File:** `frontend/src/components/ThemeToggle.tsx`

### Component Design

A small button (same size as the existing LanguageToggle) that shows:

- Sun icon when dark mode is active (clicking switches to light)
- Moon icon when light mode is active (clicking switches to dark)

Uses inline SVG icons (no icon library dependency). Button has `aria-label` for accessibility.

### Props

No props — uses `useTheme()` hook internally.

### Implementation Details

1. Import and call `useTheme()` to get `resolvedTheme` and `toggleTheme`.
2. Render a `<button>` with:
   - `onClick={toggleTheme}`
   - `aria-label` = `t('layout.theme_toggle')` (translated)
   - Conditional SVG: sun for dark mode, moon for light mode
3. Styling: Same pattern as LanguageToggle — small, bordered, hover transition.
4. SVGs are 16x16 inline paths (no external dependency).

### STOP CHECKPOINT 4

- [ ] `frontend/src/components/ThemeToggle.tsx` renders sun/moon icon
- [ ] Clicking toggles between dark and light
- [ ] Has proper `aria-label`
- [ ] Uses `useTheme` hook (not direct DOM manipulation)
- [ ] No external icon library added

---

## PHASE 5: LanguageToggle Rewrite

**Goal:** Upgrade the existing LanguageToggle to match the new design system and work with theme.

### What Changes

Rewrite `frontend/src/components/LanguageToggle.tsx` (currently 39 lines).

### Current vs New

**Current:** Simple `EN / FA` text with accent highlighting. Works but minimal.

**New:**

1. Replace `nps-oracle-accent` color reference with `nps-accent` (theme-aware emerald)
2. Use proper semantic class names from the new palette
3. Add `title` attribute showing full language name (English / فارسی)
4. Improve focus ring styling for keyboard navigation (`focus:ring-2 focus:ring-nps-accent`)
5. Keep the toggle logic identical: `i18n.changeLanguage(isFA ? 'en' : 'fa')`

### Existing Behavior to Preserve

- `useTranslation` hook for `i18n` access
- `aria-label` (already has it)
- Toggle between `en` and `fa`
- i18n language detection + localStorage persistence via `nps_language` key (handled by `i18n/config.ts`)

### STOP CHECKPOINT 5

- [ ] `frontend/src/components/LanguageToggle.tsx` uses theme-aware colors
- [ ] Focus ring styling added
- [ ] `title` attribute with full language name
- [ ] Toggle behavior unchanged from existing tests
- [ ] Existing `LanguageToggle.test.tsx` assertions still valid (adapt color class names if changed)

---

## PHASE 6: Navigation Component

**Goal:** Create a dedicated navigation component extracted from Layout, with icons, sections, and admin gating.

### What Creates

**File:** `frontend/src/components/Navigation.tsx`

### Navigation Items Configuration

```typescript
interface NavItem {
  path: string;
  labelKey: string; // i18n key
  icon: React.ReactNode; // Inline SVG icon
  adminOnly?: boolean; // Only show for admin users
  disabled?: boolean; // Grayed out + "Coming Soon" tooltip
}
```

Items (in order):

1. `/dashboard` — `nav.dashboard` — grid/home icon
2. `/oracle` — `nav.oracle` — sparkles/crystal icon — **main feature, visually prominent**
3. `/history` — `nav.history` — clock icon — NEW route (reading history page, placeholder until Session 21)
4. `/settings` — `nav.settings` — cog icon
5. `/admin` — `nav.admin` — shield icon — `adminOnly: true`
6. `/scanner` — `nav.scanner` — radar icon — `disabled: true` (Coming Soon)

### Component Design

**Props:**

```typescript
interface NavigationProps {
  collapsed: boolean; // Whether sidebar is in collapsed (icon-only) mode
  isAdmin?: boolean; // Whether to show admin items
}
```

**Behavior:**

1. Renders a `<nav>` with `<NavLink>` items from react-router-dom.
2. Active item: emerald accent background (`bg-nps-accent/10`) + emerald text + left border (2px emerald). In RTL: right border.
3. Inactive item: dim text, hover shows subtle bg.
4. Collapsed mode: Only show icons, hide labels. Add `title` attribute with label for hover tooltip.
5. Disabled items: Gray text, `cursor-not-allowed`, `title="Coming Soon"` tooltip, no link navigation.
6. Admin items: Only rendered when `isAdmin` is true.
7. Icons: Inline SVG, 20x20, `stroke-current` so they inherit text color.

### SVG Icons

Use minimal inline SVG paths (heroicons outline style). No external icon library. Each icon is a simple `<svg>` with `viewBox="0 0 24 24"`, `stroke="currentColor"`, `strokeWidth={1.5}`, `fill="none"`.

Approximate paths:

- Dashboard: 4-square grid
- Oracle: sparkles/star
- History: clock with arrow
- Settings: cog/gear
- Admin: shield with check
- Scanner: signal/radar waves

### STOP CHECKPOINT 6

- [ ] `frontend/src/components/Navigation.tsx` renders 6 nav items
- [ ] Active item has emerald accent styling
- [ ] Collapsed mode shows icons only with tooltip
- [ ] `adminOnly` items hidden when `isAdmin` is false
- [ ] Disabled items (Scanner) are non-clickable with "Coming Soon"
- [ ] All icons are inline SVG (no external library)

---

## PHASE 7: Layout Rewrite

**Goal:** Replace the current Layout with a 3-zone layout: sidebar + top bar + content area + footer.

### What Changes

Rewrite `frontend/src/components/Layout.tsx` (currently 57 lines) into a comprehensive layout component.

### Layout Structure

```
┌─────────┬───────────────────────────────────┐
│         │  TOP BAR (logo, search?, toggles) │
│         ├───────────────────────────────────┤
│ SIDEBAR │                                   │
│  (nav)  │        MAIN CONTENT               │
│         │        (<Outlet />)               │
│         │                                   │
│         ├───────────────────────────────────┤
│         │  FOOTER (version, copyright)      │
└─────────┴───────────────────────────────────┘
```

### Sidebar

- Width: `w-64` expanded, `w-16` collapsed (icon-only mode)
- Background: `bg-[var(--nps-bg-sidebar)]`
- Top section: NPS logo/name + tagline
- Middle: `<Navigation>` component
- Bottom: Collapse toggle button (chevron icon)
- Border: Right border (`border-r`), flips to `border-l` in RTL

### Top Bar

- Height: `h-14`
- Background: `bg-[var(--nps-bg-card)]`
- Left: Page breadcrumb/title (optional — can be empty for now)
- Right: `<LanguageToggle />` + `<ThemeToggle />` + user avatar placeholder
- Border: Bottom border
- In mobile: Add hamburger button (left side) that toggles sidebar overlay

### Main Content

- `flex-1` fills remaining space
- Padding: `p-6` (desktop), `p-4` (mobile)
- `overflow-y-auto` for scrolling
- Contains `<Outlet />` from react-router

### Footer

- Height: auto (small)
- Text: `NPS v4.0.0` + subtle copyright
- Centered, dim text
- Border: Top border

### Mobile Behavior (< 768px / md breakpoint)

1. Sidebar is hidden by default (off-screen left, or overlaid)
2. Hamburger button in top bar toggles sidebar overlay
3. Clicking a nav item closes the overlay
4. Backdrop overlay behind sidebar when open
5. Sidebar slides in from left (RTL: from right) with transition

### State Management

```typescript
// Internal state
const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

// Read from localStorage for sidebar preference
useEffect(() => {
  const stored = localStorage.getItem("nps_sidebar_collapsed");
  if (stored === "true") setSidebarCollapsed(true);
}, []);

// Persist sidebar preference
useEffect(() => {
  localStorage.setItem("nps_sidebar_collapsed", String(sidebarCollapsed));
}, [sidebarCollapsed]);
```

### Admin Detection

For now, `isAdmin` defaults to `false`. When the auth system is wired in later sessions, it will read from auth context. The Layout passes `isAdmin` to `<Navigation>`.

### STOP CHECKPOINT 7

- [ ] `frontend/src/components/Layout.tsx` has sidebar, top bar, content area, footer
- [ ] Sidebar collapses to icon-only mode on desktop
- [ ] Mobile hamburger toggles sidebar overlay
- [ ] Top bar contains LanguageToggle + ThemeToggle
- [ ] Footer shows version
- [ ] Sidebar collapse state persists in localStorage
- [ ] RTL: sidebar and hamburger flip sides

---

## PHASE 8: App.tsx Rewrite — Routing & Lazy Loading

**Goal:** Replace eager imports with lazy-loaded pages wrapped in Suspense, add new routes, and wire theme provider.

### What Changes

Rewrite `frontend/src/App.tsx` (currently 34 lines).

### Current Routing

```
/           → redirect to /dashboard
/dashboard  → Dashboard (eager)
/scanner    → Scanner (eager)
/oracle     → Oracle (eager)
/vault      → Vault (eager)
/learning   → Learning (eager)
/settings   → Settings (eager)
```

### New Routing

```
/           → redirect to /dashboard
/dashboard  → Dashboard (lazy)
/oracle     → Oracle (lazy)
/history    → ReadingHistory (lazy) — NEW placeholder page
/settings   → Settings (lazy)
/admin      → AdminPanel (lazy) — NEW placeholder page
/scanner    → Scanner (lazy)
```

**Removed routes:** `/vault` and `/learning` are removed (they were scaffolding stubs). Their functionality is absorbed into other pages in later sessions.

**New placeholder pages:** Create minimal components for `/history` and `/admin` routes:

- `frontend/src/pages/ReadingHistory.tsx` — placeholder: "Reading History — Coming in Session 21"
- `frontend/src/pages/AdminPanel.tsx` — placeholder: "Admin Panel — Coming in Session 38"

### Lazy Loading Pattern

```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Oracle = lazy(() => import('./pages/Oracle'));
// ...etc

// In JSX:
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route element={<Layout />}>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      ...
    </Route>
  </Routes>
</Suspense>
```

### Page Export Changes

Currently pages use named exports (`export function Dashboard`). Lazy loading requires default exports. Each page file needs a `export default` added (either change the export or add `export default Dashboard` at the bottom).

### Loading Spinner

Add a simple `LoadingSpinner` component inline in App.tsx (or as a tiny component file). A centered spinning circle using Tailwind animation classes (`animate-spin`).

### RTL Direction Effect

Keep the existing `useEffect` that sets `document.documentElement.dir` and `lang` based on `i18n.language`. This already works correctly.

### Files to Create

| File                                    | Purpose                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| `frontend/src/pages/ReadingHistory.tsx` | Placeholder page for reading history (Session 21 will implement) |
| `frontend/src/pages/AdminPanel.tsx`     | Placeholder page for admin panel (Session 38 will implement)     |

### STOP CHECKPOINT 8

- [ ] `frontend/src/App.tsx` uses `React.lazy()` for all page imports
- [ ] `Suspense` wraps routes with a loading spinner fallback
- [ ] Routes: `/dashboard`, `/oracle`, `/history`, `/settings`, `/admin`, `/scanner`
- [ ] `/vault` and `/learning` routes removed
- [ ] `ReadingHistory.tsx` and `AdminPanel.tsx` placeholder pages exist
- [ ] All pages have default exports (for lazy loading compatibility)
- [ ] RTL direction effect preserved
- [ ] No TypeScript errors

---

## PHASE 9: index.css Rewrite & Translations

**Goal:** Update global styles and add all new translation keys.

### index.css Changes

Rewrite `frontend/src/index.css` to:

1. Import the new `theme.css`: `@import './styles/theme.css';`
2. Keep Tailwind directives (`@tailwind base/components/utilities`)
3. Use CSS variables for body background and text: `body { background-color: var(--nps-bg); color: var(--nps-text); }`
4. Keep RTL font override for Persian (`html[dir="rtl"] body { font-family: "Vazirmatn", ... }`)
5. Update scrollbar colors to use CSS variables
6. Add smooth transition for theme switching: `*, *::before, *::after { transition: background-color 0.2s, border-color 0.2s, color 0.2s; }` (but disable during initial load to prevent flash)
7. Keep font-smoothing

### New Translation Keys

Add these to both `en.json` and `fa.json`:

```json
{
  "nav": {
    "dashboard": "Dashboard",
    "oracle": "Oracle",
    "history": "Reading History",
    "settings": "Settings",
    "admin": "Admin Panel",
    "scanner": "Scanner"
  },
  "layout": {
    "app_name": "NPS",
    "app_tagline": "Numerology Puzzle Solver",
    "theme_toggle": "Toggle theme",
    "theme_dark": "Dark mode",
    "theme_light": "Light mode",
    "theme_system": "System preference",
    "sidebar_collapse": "Collapse sidebar",
    "sidebar_expand": "Expand sidebar",
    "mobile_menu": "Open menu",
    "mobile_menu_close": "Close menu",
    "coming_soon": "Coming Soon",
    "version": "v4.0.0",
    "footer_copyright": "NPS Project"
  }
}
```

Persian translations (`fa.json`):

```json
{
  "nav": {
    "dashboard": "داشبورد",
    "oracle": "اوراکل",
    "history": "تاریخچه خوانش",
    "settings": "تنظیمات",
    "admin": "پنل مدیریت",
    "scanner": "اسکنر"
  },
  "layout": {
    "app_name": "NPS",
    "app_tagline": "حل‌کننده پازل اعداد",
    "theme_toggle": "تغییر تم",
    "theme_dark": "حالت تاریک",
    "theme_light": "حالت روشن",
    "theme_system": "تنظیمات سیستم",
    "sidebar_collapse": "جمع کردن نوار کناری",
    "sidebar_expand": "باز کردن نوار کناری",
    "mobile_menu": "باز کردن منو",
    "mobile_menu_close": "بستن منو",
    "coming_soon": "به‌زودی",
    "version": "v4.0.0",
    "footer_copyright": "پروژه NPS"
  }
}
```

**Note:** Keep ALL existing translation keys. Only add new ones. The `nav.vault` and `nav.learning` keys can remain (unused keys don't hurt).

### STOP CHECKPOINT 9

- [ ] `frontend/src/index.css` imports `theme.css`
- [ ] Body uses CSS variables for bg and text color
- [ ] Scrollbar uses CSS variables
- [ ] Theme transition is smooth (0.2s)
- [ ] `en.json` has `layout.*` and updated `nav.*` keys
- [ ] `fa.json` has matching Persian translations
- [ ] No existing translation keys removed

---

## PHASE 10: Tests

**Goal:** Write comprehensive tests for all new and modified components.

### Test Files & Structure

All tests use Vitest + React Testing Library + userEvent. Follow the existing pattern from `LanguageToggle.test.tsx`: mock `react-i18next`, use `vi.mock`, `describe/it/expect`.

### Test File 1: `frontend/src/hooks/__tests__/useTheme.test.ts`

**Class: useTheme hook** (6 tests)

```
test_default_dark_mode
  — Hook returns theme='dark' and resolvedTheme='dark' when no localStorage value

test_persists_to_localStorage
  — After setTheme('light'), localStorage key 'nps_theme' contains 'light'

test_reads_from_localStorage
  — Set localStorage 'nps_theme' = 'light' before hook init → theme='light'

test_toggle_cycles
  — toggleTheme() cycles: dark → light → system → dark

test_system_mode_matches_media_query
  — When theme='system' and matchMedia prefers dark → resolvedTheme='dark'

test_adds_light_class
  — When resolvedTheme='light', document.documentElement has class 'light'
```

### Test File 2: `frontend/src/components/__tests__/ThemeToggle.test.tsx`

**Class: ThemeToggle component** (4 tests)

```
test_renders_sun_icon_in_dark_mode
  — When resolvedTheme='dark', renders SVG with aria-label containing theme toggle text

test_renders_moon_icon_in_light_mode
  — When resolvedTheme='light', renders different SVG

test_click_calls_toggleTheme
  — Click button → toggleTheme is called

test_has_aria_label
  — Button has aria-label attribute
```

### Test File 3: `frontend/src/components/__tests__/Navigation.test.tsx`

**Class: Navigation component** (7 tests)

```
test_renders_all_public_nav_items
  — Renders Dashboard, Oracle, History, Settings, Scanner (5 items when isAdmin=false)

test_hides_admin_item_when_not_admin
  — isAdmin=false → Admin Panel link not in DOM

test_shows_admin_item_when_admin
  — isAdmin=true → Admin Panel link rendered

test_scanner_item_disabled
  — Scanner link has disabled styling and 'Coming Soon' title

test_active_item_highlighted
  — Navigate to /oracle → Oracle item has active class (emerald accent)

test_collapsed_mode_hides_labels
  — collapsed=true → Text labels not visible, icons visible

test_collapsed_mode_shows_tooltips
  — collapsed=true → Items have title attributes with label text
```

### Test File 4: `frontend/src/components/__tests__/Layout.test.tsx`

**Class: Layout component** (6 tests)

```
test_renders_sidebar_and_content
  — Layout renders sidebar nav, top bar, and Outlet area

test_renders_top_bar_with_toggles
  — Top bar contains LanguageToggle and ThemeToggle

test_renders_footer_with_version
  — Footer contains 'v4.0.0' text

test_sidebar_collapse_toggle
  — Click collapse button → sidebar width changes

test_mobile_hamburger_opens_sidebar
  — At mobile viewport, hamburger button visible, click opens sidebar overlay

test_sidebar_collapse_persists
  — After collapse, localStorage 'nps_sidebar_collapsed' is 'true'
```

### Test File 5: `frontend/src/pages/__tests__/App.test.tsx`

**Class: App routing** (5 tests)

```
test_root_redirects_to_dashboard
  — Navigate to '/' → redirects to '/dashboard'

test_all_routes_render
  — Each route (/dashboard, /oracle, /history, /settings, /scanner) renders without error

test_lazy_loading_shows_spinner
  — Suspense fallback (loading spinner) renders during lazy load

test_rtl_direction_set_for_persian
  — When i18n language is 'fa', document.dir is 'rtl'

test_ltr_direction_set_for_english
  — When i18n language is 'en', document.dir is 'ltr'
```

### Updated Test: `frontend/src/components/__tests__/LanguageToggle.test.tsx`

The existing 5 tests in this file need to be updated if color class names change (e.g., `nps-oracle-accent` → `nps-accent`). If the class name changes, update the `toContain` assertions. If the class name stays the same, no changes needed.

### Test Execution

```bash
cd frontend && npx vitest run src/hooks/__tests__/useTheme.test.ts
cd frontend && npx vitest run src/components/__tests__/ThemeToggle.test.tsx
cd frontend && npx vitest run src/components/__tests__/Navigation.test.tsx
cd frontend && npx vitest run src/components/__tests__/Layout.test.tsx
cd frontend && npx vitest run src/pages/__tests__/App.test.tsx
cd frontend && npx vitest run   # Full suite — all tests must pass
```

### STOP CHECKPOINT 10

- [ ] All 5 test files created
- [ ] 28+ individual tests across all files
- [ ] `npx vitest run` — all tests pass (including existing 17 test files)
- [ ] No TypeScript errors in test files
- [ ] Mocking pattern consistent with existing `LanguageToggle.test.tsx`

---

## Summary of All Deliverables

### Files Modified (7)

| #   | File                                         | Lines (current) | Action            |
| --- | -------------------------------------------- | --------------- | ----------------- |
| 1   | `frontend/src/components/Layout.tsx`         | 57              | REWRITE           |
| 2   | `frontend/src/components/LanguageToggle.tsx` | 39              | REWRITE           |
| 3   | `frontend/src/App.tsx`                       | 34              | REWRITE           |
| 4   | `frontend/tailwind.config.ts`                | 62              | REWRITE           |
| 5   | `frontend/src/index.css`                     | 38              | REWRITE           |
| 6   | `frontend/src/locales/en.json`               | 190             | MODIFY (add keys) |
| 7   | `frontend/src/locales/fa.json`               | 190             | MODIFY (add keys) |

### Files Created (13)

| #   | File                                                     | Purpose                              |
| --- | -------------------------------------------------------- | ------------------------------------ |
| 1   | `frontend/src/styles/theme.css`                          | CSS custom properties for dark/light |
| 2   | `frontend/src/components/Navigation.tsx`                 | Sidebar navigation with icons        |
| 3   | `frontend/src/components/ThemeToggle.tsx`                | Dark/light mode toggle               |
| 4   | `frontend/src/hooks/useTheme.ts`                         | Theme state management hook          |
| 5   | `frontend/src/pages/ReadingHistory.tsx`                  | Placeholder page                     |
| 6   | `frontend/src/pages/AdminPanel.tsx`                      | Placeholder page                     |
| 7   | `frontend/src/hooks/__tests__/useTheme.test.ts`          | Theme hook tests (6)                 |
| 8   | `frontend/src/components/__tests__/ThemeToggle.test.tsx` | Theme toggle tests (4)               |
| 9   | `frontend/src/components/__tests__/Navigation.test.tsx`  | Navigation tests (7)                 |
| 10  | `frontend/src/components/__tests__/Layout.test.tsx`      | Layout tests (6)                     |
| 11  | `frontend/src/pages/__tests__/App.test.tsx`              | Routing tests (5)                    |

### Files Removed (0)

No files removed. `Vault.tsx` and `Learning.tsx` remain in the codebase but are no longer routed. They can be cleaned up in a later session.

### Tests: 28+ total

| Test File              | Count  | What It Tests                                         |
| ---------------------- | ------ | ----------------------------------------------------- |
| `useTheme.test.ts`     | 6      | Hook: default, persist, read, toggle, system, class   |
| `ThemeToggle.test.tsx` | 4      | Component: icons, click, aria-label                   |
| `Navigation.test.tsx`  | 7      | Nav items, admin gating, disabled, active, collapse   |
| `Layout.test.tsx`      | 6      | Structure, toggles, footer, collapse, mobile, persist |
| `App.test.tsx`         | 5      | Redirect, routes, lazy loading, RTL/LTR               |
| **Total**              | **28** |                                                       |

### Checkpoints: 10

| #   | Phase               | Key Verification                                     |
| --- | ------------------- | ---------------------------------------------------- |
| 1   | CSS Theme Variables | theme.css exists with dark/light blocks              |
| 2   | Tailwind Config     | CSS variable colors, darkMode class strategy         |
| 3   | useTheme Hook       | Returns theme/resolvedTheme, persists, manages class |
| 4   | ThemeToggle         | Sun/moon icons, toggles, aria-label                  |
| 5   | LanguageToggle      | Theme-aware colors, focus ring                       |
| 6   | Navigation          | 6 items, admin gating, disabled, collapse            |
| 7   | Layout              | Sidebar + top bar + footer, mobile responsive        |
| 8   | App.tsx Routing     | Lazy loading, Suspense, new routes                   |
| 9   | CSS + Translations  | Theme transition, all i18n keys                      |
| 10  | Tests               | 28+ tests pass, full suite green                     |

---

## Dependency Notes

### What This Session Depends On

- **Sessions 1-4:** Database + auth + user API + profile form exist
- **Sessions 6-12:** FC60 framework integration complete (Oracle page works)
- **Sessions 13-18:** AI engine exists (Oracle consultation form functions)

### What Depends On This Session

- **Session 20:** Oracle Main Page — uses Layout, Navigation, routing from this session
- **Session 21:** Reading History — fills in the ReadingHistory placeholder page
- **Session 22:** Reading Results — uses the new theme variables
- **Sessions 23-25:** All frontend sessions build on this layout
- **Sessions 26-31:** RTL polish, responsive, accessibility — build on the mobile/RTL foundation set here
- **Session 38:** Admin Panel — fills in the AdminPanel placeholder page

### Technical Constraints

1. **No external icon library.** All icons are inline SVG. This keeps the bundle small and avoids a new dependency.
2. **No external animation library.** Sidebar transitions use Tailwind's `transition-all` + `duration-200`.
3. **Dark mode is default.** The app starts dark. Light mode is opt-in. This matches the existing dark-first aesthetic.
4. **CSS variables for theme, Tailwind for layout.** Theme colors come from CSS vars (switchable). Layout/spacing use Tailwind utilities directly.
5. **Existing page exports must become default exports.** This is a minor breaking change for lazy loading. Each page file gets `export default ComponentName` added.
6. **Preserve all existing oracle component functionality.** The Oracle page and its sub-components must work identically after the layout rewrite. Oracle-specific colors (`nps-oracle-*`) are preserved as static values.
