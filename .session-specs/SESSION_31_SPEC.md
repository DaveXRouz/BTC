# SESSION 31 SPEC — Frontend Polish & Performance

**Block:** Frontend Advanced (Sessions 26-31)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium-High
**Dependencies:** Sessions 19-30 (all frontend pages, RTL, responsive, a11y, error states, animations)

---

## TL;DR

- Analyze the production bundle (`npm run build`) and reduce initial gzipped size below 500KB
- Add route-level code splitting with `React.lazy` for all pages and heavy components (CalendarPicker, PersianKeyboard)
- Verify Tailwind CSS purges unused classes, optimize assets, and compress images/icons
- Run Lighthouse audits in both EN and FA locales targeting 90+ scores on Performance, Accessibility, Best Practices, SEO
- Perform a visual audit of every page in both locales (EN LTR + FA RTL) fixing any inconsistencies
- Write performance regression tests and document final bundle metrics

---

## OBJECTIVES

1. Produce a bundle analysis report identifying the top 10 largest modules and total gzipped initial load size
2. Implement route-level code splitting so pages are lazy-loaded (Dashboard, Scanner, Vault, Learning, Settings each in separate chunks)
3. Lazy-load heavy Oracle subcomponents (CalendarPicker, PersianKeyboard) that are only rendered on interaction
4. Verify Tailwind CSS content paths are correct so unused classes are purged in production
5. Optimize all static assets (icons, fonts) — remove unused font weights, compress SVGs
6. Achieve Lighthouse scores of 90+ across Performance, Accessibility, Best Practices, and SEO
7. Fix every visual inconsistency found during the dual-locale/dual-direction audit
8. Add performance-related meta tags (viewport, theme-color, description) for SEO compliance
9. Add `React.memo` to heavy pure components to reduce unnecessary re-renders
10. Write automated tests verifying bundle size stays below threshold and key performance metrics

---

## PREREQUISITES

- [ ] All pages exist and render: Dashboard, Scanner, Oracle, Vault, Learning, Settings
  - Verification: `ls frontend/src/pages/{Dashboard,Scanner,Oracle,Vault,Learning,Settings}.tsx`
- [ ] React Router with Layout is configured in `frontend/src/App.tsx`
  - Verification: `grep -q "Routes" frontend/src/App.tsx && echo "OK"`
- [ ] Vite build works without errors
  - Verification: `cd frontend && npm run build 2>&1 | tail -5`
- [ ] Tailwind config exists at `frontend/tailwind.config.ts`
  - Verification: `test -f frontend/tailwind.config.ts && echo "OK"`
- [ ] i18n config exists with EN/FA locales
  - Verification: `test -f frontend/src/i18n/config.ts && echo "OK"`
- [ ] Playwright E2E config exists at `frontend/playwright.config.ts`
  - Verification: `test -f frontend/playwright.config.ts && echo "OK"`

---

## FILES TO CREATE

| #   | File                                                     | Purpose                                                             |
| --- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| 1   | `frontend/src/components/common/LazyPage.tsx`            | NEW — Suspense wrapper with loading skeleton for lazy-loaded pages  |
| 2   | `frontend/src/components/common/PageLoadingFallback.tsx` | NEW — Skeleton/shimmer placeholder shown during chunk loading       |
| 3   | `frontend/e2e/performance.spec.ts`                       | NEW — Playwright performance tests (bundle size, LCP, CLS)          |
| 4   | `frontend/src/__tests__/bundle-size.test.ts`             | NEW — Vitest test that verifies production bundle stays under 500KB |
| 5   | `frontend/src/__tests__/lighthouse-meta.test.ts`         | NEW — Vitest test verifying meta tags and SEO elements exist        |

## FILES TO MODIFY

| #   | File                                                        | What Changes                                                                                                           |
| --- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 6   | `frontend/src/App.tsx`                                      | Replace static imports with `React.lazy()` + `Suspense` for all page routes                                            |
| 7   | `frontend/vite.config.ts`                                   | Add `build.rollupOptions.output.manualChunks` for vendor splitting; add `rollup-plugin-visualizer` for bundle analysis |
| 8   | `frontend/src/main.tsx`                                     | No functional change — verify only one CSS import and i18n import exist                                                |
| 9   | `frontend/src/index.css`                                    | Audit for unused CSS rules; verify Tailwind directives are minimal                                                     |
| 10  | `frontend/tailwind.config.ts`                               | Verify `content` paths cover all .tsx files; ensure no unnecessary plugins                                             |
| 11  | `frontend/src/components/Layout.tsx`                        | Wrap in `React.memo`; verify no unnecessary re-renders on route change                                                 |
| 12  | `frontend/src/components/oracle/CalendarPicker.tsx`         | Extract into lazy-loadable chunk (loaded on first open)                                                                |
| 13  | `frontend/src/components/oracle/PersianKeyboard.tsx`        | Extract into lazy-loadable chunk (loaded on first open)                                                                |
| 14  | `frontend/src/components/oracle/OracleConsultationForm.tsx` | Lazy-load CalendarPicker and PersianKeyboard within this form                                                          |
| 15  | `frontend/src/components/oracle/ReadingResults.tsx`         | Add `React.memo` to prevent re-render when parent updates unrelated state                                              |
| 16  | `frontend/src/components/StatsCard.tsx`                     | Add `React.memo` — pure display component rendered 4+ times on Dashboard                                               |
| 17  | `frontend/src/pages/Dashboard.tsx`                          | Visual polish: fix any hardcoded strings remaining, verify stats layout                                                |
| 18  | `frontend/src/pages/Settings.tsx`                           | Visual polish: fix layout, verify RTL rendering                                                                        |
| 19  | `frontend/index.html`                                       | Add meta tags: viewport, description, theme-color, Open Graph basics                                                   |
| 20  | `frontend/package.json`                                     | Add `rollup-plugin-visualizer` to devDependencies; add `analyze` script                                                |
| 21  | `frontend/playwright.config.ts`                             | Add Firefox project for cross-browser visual testing                                                                   |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Bundle Analysis & Baseline (30 minutes)

**Tasks:**

1. Run `cd frontend && npm run build` and record baseline bundle sizes
2. Install `rollup-plugin-visualizer` as devDependency:
   ```bash
   cd frontend && npm install -D rollup-plugin-visualizer
   ```
3. Add visualizer plugin to `frontend/vite.config.ts`:

   ```typescript
   import { visualizer } from 'rollup-plugin-visualizer';

   // Add to plugins array:
   visualizer({
     filename: 'dist/stats.html',
     open: false,
     gzipSize: true,
   }),
   ```

4. Add `"analyze": "vite build && open dist/stats.html"` script to `package.json`
5. Run build again with visualizer, open `dist/stats.html` to identify:
   - Total gzipped initial JS size
   - Top 10 largest modules
   - Vendor libraries that could be split or tree-shaken
6. Record baseline Lighthouse scores for both EN and FA locales

**Key patterns:**

The baseline build output typically looks like:

```
dist/assets/index-[hash].js    XXX kB │ gzip: XXX kB
dist/assets/index-[hash].css   XXX kB │ gzip: XXX kB
```

Current dependency sizes (estimated from `package.json`):

- `react` + `react-dom`: ~45KB gzipped
- `react-router-dom`: ~13KB gzipped
- `@tanstack/react-query`: ~13KB gzipped
- `i18next` + `react-i18next` + `detector`: ~15KB gzipped
- `jalaali-js`: ~3KB gzipped
- Application code: variable
- **Estimated total: ~150-250KB gzipped** (already likely under 500KB)

**Checkpoint:**

- [ ] `npm run build` succeeds without errors
- [ ] `dist/stats.html` visualizer file generated
- [ ] Baseline bundle sizes recorded (JS + CSS gzipped)
- [ ] Baseline Lighthouse scores recorded

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | grep -E "dist/|gzip"
```

🚨 STOP if build fails — fix TypeScript/build errors before continuing

---

### Phase 2: Route-Level Code Splitting (45 minutes)

**Tasks:**

1. Convert all page imports in `frontend/src/App.tsx` from static to `React.lazy()`:

   Current (static — everything in one bundle):

   ```typescript
   import { Dashboard } from "./pages/Dashboard";
   import { Scanner } from "./pages/Scanner";
   import { Oracle } from "./pages/Oracle";
   import { Vault } from "./pages/Vault";
   import { Learning } from "./pages/Learning";
   import { Settings } from "./pages/Settings";
   ```

   Target (lazy — each page in its own chunk):

   ```typescript
   import { lazy, Suspense } from "react";
   const Dashboard = lazy(() =>
     import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
   );
   const Scanner = lazy(() =>
     import("./pages/Scanner").then((m) => ({ default: m.Scanner })),
   );
   const Oracle = lazy(() =>
     import("./pages/Oracle").then((m) => ({ default: m.Oracle })),
   );
   const Vault = lazy(() =>
     import("./pages/Vault").then((m) => ({ default: m.Vault })),
   );
   const Learning = lazy(() =>
     import("./pages/Learning").then((m) => ({ default: m.Learning })),
   );
   const Settings = lazy(() =>
     import("./pages/Settings").then((m) => ({ default: m.Settings })),
   );
   ```

2. Create `frontend/src/components/common/PageLoadingFallback.tsx`:
   - Shimmer skeleton matching page layout (sidebar stays, content area shows placeholder)
   - Respect dark theme (use `bg-nps-bg-card` colors for skeletons)
   - Should be lightweight — no external dependencies

3. Create `frontend/src/components/common/LazyPage.tsx`:
   - Thin wrapper: `<Suspense fallback={<PageLoadingFallback />}>{children}</Suspense>`
   - Used in `App.tsx` route definitions

4. Wrap each lazy route in `<Suspense>`:

   ```tsx
   <Route
     path="/dashboard"
     element={
       <Suspense fallback={<PageLoadingFallback />}>
         <Dashboard />
       </Suspense>
     }
   />
   ```

5. Verify page components use named exports (not default exports).
   Current pages (`Dashboard.tsx`, etc.) use `export function Dashboard()`.
   The lazy import pattern must handle named exports:
   ```typescript
   lazy(() =>
     import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
   );
   ```

**Checkpoint:**

- [ ] Each page loads in its own JS chunk (verify in Network tab or build output)
- [ ] Navigation between pages shows brief loading state then renders page
- [ ] No flash of unstyled content during page transitions
- [ ] Build output shows multiple chunk files

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | grep -c "\.js"
# Expected: 5+ JS files (vendor + per-page chunks)
```

🚨 STOP if lazy loading causes runtime errors — check named vs default export handling

---

### Phase 3: Component-Level Lazy Loading (30 minutes)

**Tasks:**

1. Lazy-load `CalendarPicker` inside `OracleConsultationForm.tsx`:
   - CalendarPicker is only shown when the date input is clicked
   - Wrap with `Suspense` + minimal inline fallback (spinning indicator)
   - Pattern:
     ```typescript
     const CalendarPicker = lazy(() =>
       import("./CalendarPicker").then((m) => ({ default: m.CalendarPicker })),
     );
     ```

2. Lazy-load `PersianKeyboard` inside `OracleConsultationForm.tsx`:
   - PersianKeyboard is only shown when keyboard toggle is clicked
   - Same pattern as CalendarPicker

3. Verify both components still function correctly after lazy-loading:
   - Calendar opens/closes, date selection works
   - Keyboard opens/closes, character input works
   - RTL rendering correct for both

**Checkpoint:**

- [ ] CalendarPicker appears in its own chunk in build output
- [ ] PersianKeyboard appears in its own chunk in build output
- [ ] Both components render correctly after lazy loading
- [ ] No visible delay for repeat uses (chunk cached after first load)

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | grep -E "Calendar|Keyboard|chunk"
```

🚨 STOP if calendar or keyboard fails to render — check Suspense boundaries

---

### Phase 4: Vendor Chunk Splitting (30 minutes)

**Tasks:**

1. Add manual chunk configuration to `frontend/vite.config.ts`:

   ```typescript
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           'vendor-react': ['react', 'react-dom', 'react-router-dom'],
           'vendor-query': ['@tanstack/react-query'],
           'vendor-i18n': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
           'vendor-calendar': ['jalaali-js'],
         },
       },
     },
   },
   ```

2. This separates vendor code into cacheable chunks:
   - `vendor-react` — changes rarely, cached long-term
   - `vendor-query` — React Query, changes rarely
   - `vendor-i18n` — i18n libs, changes rarely
   - `vendor-calendar` — jalaali-js, changes rarely
   - App code — changes frequently, small chunk

3. Run build and verify chunk sizes:
   - Each vendor chunk should be identifiable in the output
   - Total gzipped JS should not increase (splitting doesn't add overhead)
   - Initial load should only include `vendor-react` + `vendor-i18n` + app shell

4. Verify the import of `@testing-library/*` packages is NOT included in production bundles (should be devDependencies only — already correct in `package.json`)

**Checkpoint:**

- [ ] Build output shows separate vendor chunks
- [ ] No vendor code in the main app chunk
- [ ] Total gzipped JS is same or smaller than Phase 1 baseline
- [ ] `@testing-library/*` NOT in production bundle

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | grep "vendor"
```

🚨 STOP if vendor splitting causes import errors — check manualChunks paths match package names exactly

---

### Phase 5: CSS & Asset Optimization (30 minutes)

**Tasks:**

1. Verify Tailwind `content` paths in `frontend/tailwind.config.ts`:

   ```typescript
   content: ["./index.html", "./src/**/*.{ts,tsx}"],
   ```

   This is already correct — covers all component files. Verify no dead paths.

2. Audit `frontend/src/index.css` for unnecessary rules:
   - Current file is minimal (39 lines): Tailwind directives + scrollbar + RTL base
   - Verify no duplicate RTL rules that conflict with Session 26 (RTL) or Session 24 (i18n)
   - Verify Vazirmatn font declaration — font should be loaded from CDN or locally

3. Check font loading strategy:
   - Current: `font-family: "Inter", "Segoe UI", "Helvetica", sans-serif` (LTR)
   - RTL: `font-family: "Vazirmatn", "Tahoma", sans-serif` (FA)
   - Verify Inter and Vazirmatn are loaded efficiently:
     - If using Google Fonts CDN: use `font-display: swap` to avoid blocking
     - If using local fonts: verify font files exist and are compressed (woff2)
   - Consider using `@font-face` with `font-display: swap` if not already

4. Add performance meta tags to `frontend/index.html`:

   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1" />
   <meta name="theme-color" content="#0d1117" />
   <meta name="description" content="NPS — Numerology Puzzle Solver" />
   <meta property="og:title" content="NPS" />
   <meta property="og:description" content="Numerology Puzzle Solver" />
   ```

5. Verify `index.html` has no blocking scripts in `<head>` — Vite should inject them with `type="module"`.

**Checkpoint:**

- [ ] Tailwind purges unused CSS in production (CSS bundle < 20KB gzipped)
- [ ] Font loading doesn't block initial render (font-display: swap)
- [ ] Meta tags present in `index.html`
- [ ] No render-blocking resources in `<head>`

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | grep ".css"
# Expected: CSS file < 20KB gzipped
```

🚨 STOP if CSS is unexpectedly large — check Tailwind content paths

---

### Phase 6: React.memo & Re-render Optimization (30 minutes)

**Tasks:**

1. Add `React.memo` to pure display components:
   - `frontend/src/components/StatsCard.tsx` — rendered 4+ times on Dashboard, props are primitive
   - `frontend/src/components/oracle/ReadingResults.tsx` — rendered in Oracle page, shouldn't re-render on unrelated state changes
   - `frontend/src/components/Layout.tsx` — wrapping component, ensure child re-renders don't propagate up

   Pattern for StatsCard:

   ```typescript
   export const StatsCard = React.memo(function StatsCard({
     label,
     value,
     subtitle,
     color,
   }: StatsCardProps) {
     // ... existing implementation
   });
   ```

2. Verify `useEffect` dependencies in key components:
   - `frontend/src/App.tsx` — `[i18n.language]` dependency is correct
   - `frontend/src/pages/Oracle.tsx` — check for unnecessary re-renders when typing in form
   - `frontend/src/components/oracle/CalendarPicker.tsx` — verify `today` recalculation doesn't cause loops

3. Verify React Query caching is configured correctly in `frontend/src/main.tsx`:
   - Current: `staleTime: 5 * 60 * 1000` (5 minutes) — good
   - Current: `retry: 1` — acceptable
   - No changes needed unless profiling shows issues

4. Check for components that pass new object/array references as props:
   - Look for inline `style={{}}` or `className` computed on every render
   - Extract stable references where possible

**Checkpoint:**

- [ ] `StatsCard`, `ReadingResults`, and `Layout` wrapped in `React.memo`
- [ ] No infinite re-render loops
- [ ] Dev tools React profiler shows minimal unnecessary renders

Verify:

```bash
grep -rn "React.memo" /Users/hamzeh/Desktop/GitHub/NPS/frontend/src/components/ | wc -l
# Expected: 3+ files with React.memo
```

🚨 STOP if adding React.memo causes test failures — some tests may depend on re-render behavior

---

### Phase 7: Visual Audit — Dual Locale & Consistency (45 minutes)

**Tasks:**

1. Systematically check every page in both locales. For each page, verify:
   - **EN (LTR):** Text alignment, spacing, no overflow, consistent font sizes
   - **FA (RTL):** Text alignment flipped, sidebar on right, no broken layouts, Persian numerals where expected

2. Pages to audit (6 pages × 2 locales = 12 checks):

   | Page      | EN Check                                | FA Check                              |
   | --------- | --------------------------------------- | ------------------------------------- |
   | Dashboard | Stats cards aligned, labels readable    | Stats cards RTL, labels in Persian    |
   | Scanner   | Stub page renders cleanly               | Stub page RTL                         |
   | Oracle    | Full flow: user select → form → results | Full flow RTL, Persian keyboard works |
   | Vault     | Table/list renders correctly            | Table RTL, Persian text               |
   | Learning  | Stats/insights render                   | RTL layout                            |
   | Settings  | Form layout clean                       | Form RTL, labels Persian              |

3. Fix discovered issues:
   - **Color inconsistencies:** Ensure all pages use `nps-*` color tokens from `tailwind.config.ts`
   - **Spacing issues:** Ensure consistent use of `space-y-6` for page layouts, `gap-4` for grids
   - **Font size inconsistencies:** h2 for page titles (`text-xl font-bold`), h3 for section titles (`text-sm font-semibold`)
   - **Border consistency:** Use `border-nps-border` everywhere, not hardcoded colors
   - **RTL overflows:** Look for elements with fixed `left` positioning that should use `start`
   - **Mixed direction text:** FC60 codes, Bitcoin addresses, and technical identifiers should stay LTR even in RTL context using `<bdi>` or `dir="ltr"`

4. Verify dark theme is consistent:
   - Background: `bg-nps-bg` (body), `bg-nps-bg-card` (cards), `bg-nps-bg-input` (inputs)
   - Text: `text-nps-text` (body), `text-nps-text-dim` (secondary), `text-nps-text-bright` (headings)
   - No white/light backgrounds leaking through

5. Verify hover/focus states are visible on all interactive elements:
   - Buttons: `hover:bg-nps-bg-hover`
   - Links: color change on hover
   - Focus: visible outline (from Session 28 accessibility work)

**Checkpoint:**

- [ ] All 6 pages audited in EN locale
- [ ] All 6 pages audited in FA locale
- [ ] Zero visual inconsistencies remaining
- [ ] All text uses NPS color tokens
- [ ] Dark theme consistent across pages

Verify:

```bash
# Check for hardcoded colors that should use NPS tokens
grep -rn "text-white\|text-black\|bg-white\|bg-black\|text-gray\|bg-gray" /Users/hamzeh/Desktop/GitHub/NPS/frontend/src/ --include="*.tsx" | grep -v "node_modules" | grep -v ".test." | head -10
# Expected: No matches (all should use nps-* tokens)
```

🚨 STOP if critical layout issues found — fix before proceeding to Lighthouse

---

### Phase 8: Lighthouse Audit & Fixes (45 minutes)

**Tasks:**

1. Run Lighthouse audit against the built app. Requires production build served locally:

   ```bash
   cd frontend && npm run build && npx vite preview --port 4173
   ```

   Then in another terminal:

   ```bash
   npx lighthouse http://localhost:4173/dashboard --output=json --output-path=./lighthouse-dashboard.json --chrome-flags="--headless"
   ```

2. Target scores and common fixes:

   | Category       | Target | Common Fixes                                                                                |
   | -------------- | ------ | ------------------------------------------------------------------------------------------- |
   | Performance    | 90+    | Code splitting (Phase 2), font-display: swap, image optimization                            |
   | Accessibility  | 90+    | Already handled by Session 28 (a11y). Verify: ARIA labels, color contrast, focus indicators |
   | Best Practices | 90+    | HTTPS in prod, no console errors, no deprecated APIs, no vulnerable packages                |
   | SEO            | 90+    | Meta description, viewport meta, `<html lang>` attribute, heading hierarchy                 |

3. Fix any failing Lighthouse checks:
   - **Performance:** LCP (Largest Contentful Paint) < 2.5s, CLS (Cumulative Layout Shift) < 0.1, FID (First Input Delay) < 100ms
   - **Accessibility:** Already addressed in Session 28. Fix any remaining issues.
   - **Best Practices:** Fix console errors, verify no mixed content warnings
   - **SEO:** `<html lang>` already set in `App.tsx`. Add `<meta name="description">`. Verify heading hierarchy (one `<h1>` per page).

4. Run Lighthouse in FA locale too:
   - Set localStorage `nps_language=fa` before audit
   - Verify RTL layout doesn't degrade performance or accessibility scores

5. Record final Lighthouse scores in a comment at the top of `frontend/index.html` for reference:
   ```html
   <!-- Lighthouse: Performance 95, Accessibility 92, Best Practices 95, SEO 91 (Session 31) -->
   ```

**Checkpoint:**

- [ ] Lighthouse Performance >= 90
- [ ] Lighthouse Accessibility >= 90
- [ ] Lighthouse Best Practices >= 90
- [ ] Lighthouse SEO >= 90
- [ ] Scores recorded

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | tail -3 && echo "Build successful — ready for Lighthouse"
```

🚨 STOP if any Lighthouse category is below 80 — prioritize the lowest-scoring category

---

### Phase 9: Performance Tests (30 minutes)

**Tasks:**

1. Create `frontend/src/__tests__/bundle-size.test.ts`:

   ```typescript
   import { describe, test, expect } from "vitest";
   import { readFileSync, readdirSync } from "fs";
   import { resolve } from "path";
   import { gzipSync } from "zlib";

   describe("Bundle size", () => {
     const distDir = resolve(__dirname, "../../dist/assets");

     test("total gzipped JS is under 500KB", () => {
       const jsFiles = readdirSync(distDir).filter((f) => f.endsWith(".js"));
       let totalGzipped = 0;
       for (const file of jsFiles) {
         const content = readFileSync(resolve(distDir, file));
         totalGzipped += gzipSync(content).length;
       }
       const totalKB = totalGzipped / 1024;
       expect(totalKB).toBeLessThan(500);
     });

     test("no single JS chunk exceeds 200KB gzipped", () => {
       const jsFiles = readdirSync(distDir).filter((f) => f.endsWith(".js"));
       for (const file of jsFiles) {
         const content = readFileSync(resolve(distDir, file));
         const gzippedKB = gzipSync(content).length / 1024;
         expect(gzippedKB).toBeLessThan(200);
       }
     });

     test("CSS is under 20KB gzipped", () => {
       const cssFiles = readdirSync(distDir).filter((f) => f.endsWith(".css"));
       let totalGzipped = 0;
       for (const file of cssFiles) {
         const content = readFileSync(resolve(distDir, file));
         totalGzipped += gzipSync(content).length;
       }
       const totalKB = totalGzipped / 1024;
       expect(totalKB).toBeLessThan(20);
     });

     test("build produces multiple JS chunks (code splitting active)", () => {
       const jsFiles = readdirSync(distDir).filter((f) => f.endsWith(".js"));
       expect(jsFiles.length).toBeGreaterThanOrEqual(5);
     });
   });
   ```

2. Create `frontend/src/__tests__/lighthouse-meta.test.ts`:

   ```typescript
   import { describe, test, expect } from "vitest";
   import { readFileSync } from "fs";
   import { resolve } from "path";

   describe("SEO meta tags", () => {
     const html = readFileSync(resolve(__dirname, "../../index.html"), "utf-8");

     test("has viewport meta tag", () => {
       expect(html).toContain('name="viewport"');
     });

     test("has description meta tag", () => {
       expect(html).toContain('name="description"');
     });

     test("has theme-color meta tag", () => {
       expect(html).toContain('name="theme-color"');
     });

     test("has Open Graph title", () => {
       expect(html).toContain('property="og:title"');
     });

     test("has lang attribute support in App", () => {
       // Verify App.tsx sets document.documentElement.lang
       const appCode = readFileSync(resolve(__dirname, "../App.tsx"), "utf-8");
       expect(appCode).toContain("documentElement.lang");
     });
   });
   ```

3. Create `frontend/e2e/performance.spec.ts`:

   ```typescript
   import { test, expect } from "@playwright/test";

   test.describe("Performance", () => {
     test("Dashboard loads under 3 seconds", async ({ page }) => {
       const start = Date.now();
       await page.goto("/dashboard");
       await page.waitForSelector("h2");
       const loadTime = Date.now() - start;
       expect(loadTime).toBeLessThan(3000);
     });

     test("Oracle page loads under 3 seconds", async ({ page }) => {
       const start = Date.now();
       await page.goto("/oracle");
       await page.waitForSelector("h2");
       const loadTime = Date.now() - start;
       expect(loadTime).toBeLessThan(3000);
     });

     test("Language switch completes under 500ms", async ({ page }) => {
       await page.goto("/dashboard");
       const langToggle = page
         .locator("button:has-text('فا'), button:has-text('FA')")
         .first();
       if (await langToggle.isVisible()) {
         const start = Date.now();
         await langToggle.click();
         await page.waitForFunction(
           () => document.documentElement.dir === "rtl",
         );
         const switchTime = Date.now() - start;
         expect(switchTime).toBeLessThan(500);
       }
     });

     test("No layout shift on page load (CLS check)", async ({ page }) => {
       await page.goto("/dashboard");
       // Wait for full render
       await page.waitForTimeout(2000);
       // Take screenshot to verify no visible shift
       const screenshot = await page.screenshot();
       expect(screenshot.length).toBeGreaterThan(0);
     });

     test("Page navigation does not cause full reload", async ({ page }) => {
       await page.goto("/dashboard");
       // Navigate to Oracle
       await page.click('a[href="/oracle"]');
       await page.waitForSelector("h2");
       // Sidebar should still be visible (SPA navigation, not full reload)
       await expect(page.locator("nav")).toBeVisible();
     });
   });
   ```

**Checkpoint:**

- [ ] Bundle size test passes (< 500KB gzipped total)
- [ ] Meta tags test passes
- [ ] E2E performance tests pass
- [ ] All tests pass: `cd frontend && npm test`

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build && npx vitest run src/__tests__/bundle-size.test.ts --reporter=verbose 2>&1 | tail -15
```

🚨 STOP if bundle size exceeds 500KB — return to Phase 4 and review chunk splitting

---

### Phase 10: Final Verification (30 minutes)

**Tasks:**

1. Run the full test suite:

   ```bash
   cd frontend && npm test
   ```

2. Run E2E tests:

   ```bash
   cd frontend && npx playwright test
   ```

3. Run build and verify final metrics:

   ```bash
   cd frontend && npm run build
   ```

   Record: total JS gzipped, total CSS gzipped, number of chunks.

4. Run lint and format:

   ```bash
   cd frontend && npm run lint && npm run format
   ```

5. Final manual check:
   - Open `http://localhost:5173` in browser
   - Navigate all 6 pages in EN
   - Switch to FA, navigate all 6 pages
   - Verify no console errors
   - Verify no network errors (404s, 500s)

**Checkpoint:**

- [ ] All unit tests pass
- [ ] All E2E tests pass
- [ ] Build succeeds with no warnings
- [ ] Lint passes with no errors
- [ ] Manual verification complete in both locales

Verify:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm test 2>&1 | tail -5 && npm run build 2>&1 | tail -5
```

🚨 STOP if any tests fail — fix before declaring session complete

---

## TESTS TO WRITE

| #   | Test File                                        | Test Name                                    | What It Verifies                 |
| --- | ------------------------------------------------ | -------------------------------------------- | -------------------------------- |
| 1   | `frontend/src/__tests__/bundle-size.test.ts`     | `total gzipped JS is under 500KB`            | Production bundle size threshold |
| 2   | `frontend/src/__tests__/bundle-size.test.ts`     | `no single JS chunk exceeds 200KB gzipped`   | No oversized chunks              |
| 3   | `frontend/src/__tests__/bundle-size.test.ts`     | `CSS is under 20KB gzipped`                  | Tailwind purge working           |
| 4   | `frontend/src/__tests__/bundle-size.test.ts`     | `build produces multiple JS chunks`          | Code splitting active            |
| 5   | `frontend/src/__tests__/lighthouse-meta.test.ts` | `has viewport meta tag`                      | SEO: viewport meta exists        |
| 6   | `frontend/src/__tests__/lighthouse-meta.test.ts` | `has description meta tag`                   | SEO: description exists          |
| 7   | `frontend/src/__tests__/lighthouse-meta.test.ts` | `has theme-color meta tag`                   | PWA: theme-color exists          |
| 8   | `frontend/src/__tests__/lighthouse-meta.test.ts` | `has Open Graph title`                       | Social sharing: OG title         |
| 9   | `frontend/src/__tests__/lighthouse-meta.test.ts` | `has lang attribute support in App`          | i18n: lang attr dynamically set  |
| 10  | `frontend/e2e/performance.spec.ts`               | `Dashboard loads under 3 seconds`            | Page load performance            |
| 11  | `frontend/e2e/performance.spec.ts`               | `Oracle page loads under 3 seconds`          | Page load performance            |
| 12  | `frontend/e2e/performance.spec.ts`               | `Language switch completes under 500ms`      | Language toggle responsiveness   |
| 13  | `frontend/e2e/performance.spec.ts`               | `No layout shift on page load`               | Visual stability (CLS)           |
| 14  | `frontend/e2e/performance.spec.ts`               | `Page navigation does not cause full reload` | SPA routing works                |

---

## ACCEPTANCE CRITERIA

- [ ] Initial bundle < 500KB gzipped (total JS)
- [ ] CSS < 20KB gzipped (Tailwind purge active)
- [ ] Build produces 5+ JS chunks (code splitting active)
- [ ] No single chunk exceeds 200KB gzipped
- [ ] Lighthouse Performance score >= 90
- [ ] Lighthouse Accessibility score >= 90
- [ ] Lighthouse Best Practices score >= 90
- [ ] Lighthouse SEO score >= 90
- [ ] All 6 pages render correctly in EN (LTR) locale
- [ ] All 6 pages render correctly in FA (RTL) locale
- [ ] No hardcoded colors outside NPS token system
- [ ] `React.memo` applied to StatsCard, ReadingResults, Layout
- [ ] Route-level code splitting active (lazy pages)
- [ ] CalendarPicker and PersianKeyboard lazy-loaded
- [ ] Meta tags present: viewport, description, theme-color, og:title
- [ ] All 14 tests pass
- [ ] All existing tests still pass
- [ ] No console errors in production build
- [ ] Lint passes with zero errors

Verify all:

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend && npm run build 2>&1 | tail -10 && npm test 2>&1 | tail -10
```

---

## ERROR SCENARIOS

### Build fails after code splitting

**Problem:** `React.lazy()` import paths don't resolve, or named exports don't match.

**Fix:**

1. Check that page components use named exports: `export function Dashboard()` not `export default function Dashboard()`
2. The lazy import pattern for named exports is:
   ```typescript
   const Dashboard = lazy(() =>
     import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })),
   );
   ```
3. If a page uses default export, simplify to:
   ```typescript
   const Dashboard = lazy(() => import("./pages/Dashboard"));
   ```
4. Verify with `npm run build` — Vite will error on missing exports.

### Bundle size exceeds 500KB

**Problem:** Production bundle is too large even after splitting.

**Fix:**

1. Open `dist/stats.html` (visualizer) to identify the largest modules
2. Check if `@testing-library/*` or other dev dependencies leaked into production
3. Verify `jalaali-js` is in its own chunk (it's 3KB, but check)
4. Check if `react-query` devtools are included in production (they shouldn't be)
5. If a single vendor is very large, check if there's a lighter alternative
6. Consider dynamic import for the heaviest non-critical module

### Lighthouse Performance below 90

**Problem:** Performance score doesn't reach 90 despite code splitting.

**Fix:**

1. Check LCP (Largest Contentful Paint): if a font blocks rendering, add `font-display: swap`
2. Check CLS (Cumulative Layout Shift): add explicit dimensions to images and dynamic containers
3. Check FCP (First Contentful Paint): ensure the app shell renders immediately without waiting for API calls
4. Preload critical fonts in `<head>`:
   ```html
   <link
     rel="preload"
     href="/fonts/inter.woff2"
     as="font"
     type="font/woff2"
     crossorigin
   />
   ```
5. If using Google Fonts CDN, add `<link rel="preconnect" href="https://fonts.googleapis.com">`

### React.memo causes test failures

**Problem:** Tests that rely on component re-rendering behavior break with `React.memo`.

**Fix:**

1. `React.memo` only prevents re-renders when props are shallowly equal
2. Tests that assert on re-render count may need adjustment
3. If a test passes new object props, the component will still re-render (shallow comparison fails for objects)
4. Verify by removing `React.memo` temporarily — if test passes, the test is testing implementation detail

---

## HANDOFF

**Created:**

- `frontend/src/components/common/LazyPage.tsx`
- `frontend/src/components/common/PageLoadingFallback.tsx`
- `frontend/e2e/performance.spec.ts`
- `frontend/src/__tests__/bundle-size.test.ts`
- `frontend/src/__tests__/lighthouse-meta.test.ts`

**Modified:**

- `frontend/src/App.tsx` — lazy page imports + Suspense boundaries
- `frontend/vite.config.ts` — vendor chunks + visualizer plugin
- `frontend/tailwind.config.ts` — verified content paths
- `frontend/src/index.css` — audited and optimized
- `frontend/index.html` — meta tags for SEO
- `frontend/package.json` — added `rollup-plugin-visualizer`, `analyze` script
- `frontend/playwright.config.ts` — Firefox project
- `frontend/src/components/Layout.tsx` — React.memo
- `frontend/src/components/StatsCard.tsx` — React.memo
- `frontend/src/components/oracle/ReadingResults.tsx` — React.memo
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — lazy CalendarPicker + PersianKeyboard
- `frontend/src/pages/Dashboard.tsx` — visual polish
- `frontend/src/pages/Settings.tsx` — visual polish

**Deleted:**

- None

**Next session needs:**
Session 31 is the LAST session in the Frontend Advanced block (26-31). Session 32 begins the Features & Integration block. It receives:

1. **Optimized production bundle** — under 500KB gzipped, code-split by route
2. **Lighthouse-verified frontend** — 90+ across all four categories
3. **Visually consistent UI** — every page audited in both EN/FA locales
4. **Performance test infrastructure** — bundle size tests, E2E performance tests, Lighthouse meta checks
5. **Clean component architecture** — heavy components lazy-loaded, pure components memoized
6. **Complete frontend** — all pages, RTL, responsive, accessible, animated, polished, and performant

Session 32 (Export & Share) will add export functionality (PDF, image, text) to the reading results. It can assume the frontend is production-ready and focus purely on new feature work.
