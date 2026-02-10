# SESSION 29 SPEC — Error States & Loading UX

**Block:** Frontend Advanced (Sessions 26-31)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium
**Dependencies:** Session 20 (Oracle page), Session 28 (Accessibility)

---

## TL;DR

- Build reusable `LoadingSkeleton` with shimmer animation for all data-dependent views
- Create React `ErrorBoundary` wrapping every page with crash recovery UI
- Add a toast notification system for transient API errors (auto-dismiss, stacking)
- Design friendly `EmptyState` illustrations for zero-data scenarios (no readings, no profiles, empty search)
- Detect offline status with a persistent banner and queue retry actions
- Wire `useRetry` hook with exponential backoff (3 attempts) into React Query and manual fetches

---

## OBJECTIVES

1. **Loading skeletons** — Shimmer placeholders replace every "Loading..." text and blank state across the app
2. **Error boundaries** — React Error Boundary catches component crashes per-page, shows recovery UI with "Try Again" button
3. **Toast notifications** — Transient API errors appear as auto-dismissing toasts (top-right, stacked, 5s default)
4. **Empty states** — Friendly messages with contextual icons for: no readings, no profiles, no vault findings, empty search
5. **Offline detection** — Show a fixed banner when `navigator.onLine` is false; auto-hide when connection returns
6. **Retry logic** — React Query global retry config (3 retries, exponential backoff); `useRetry` hook for manual operations
7. **i18n coverage** — All new strings translated to EN and FA

---

## PREREQUISITES

- [ ] Oracle page (`frontend/src/pages/Oracle.tsx`) exists and is functional
- [ ] React Query is installed and configured (`@tanstack/react-query`)
- [ ] i18n is configured with EN/FA locales
- [ ] Tailwind CSS is configured with NPS color tokens

Verification:

```bash
ls frontend/src/pages/Oracle.tsx
grep "@tanstack/react-query" frontend/package.json
ls frontend/src/locales/en.json frontend/src/locales/fa.json
```

---

## FILES TO CREATE

### Components

- `frontend/src/components/common/LoadingSkeleton.tsx` — Shimmer skeleton primitives (line, card, circle, grid variants)
- `frontend/src/components/common/ErrorBoundary.tsx` — React class component Error Boundary with fallback UI
- `frontend/src/components/common/EmptyState.tsx` — Reusable empty state with icon, title, description, optional action
- `frontend/src/components/common/Toast.tsx` — Toast container + individual toast component (success/error/warning/info)
- `frontend/src/components/common/OfflineBanner.tsx` — Fixed top banner when offline, auto-hides on reconnect

### Hooks

- `frontend/src/hooks/useRetry.ts` — Exponential backoff retry wrapper for async operations
- `frontend/src/hooks/useOnlineStatus.ts` — Track `navigator.onLine` with event listeners
- `frontend/src/hooks/useToast.ts` — Toast state management (add, dismiss, auto-expire)

### Tests (Unit)

- `frontend/src/components/common/__tests__/LoadingSkeleton.test.tsx` — Render variants, shimmer animation class present
- `frontend/src/components/common/__tests__/ErrorBoundary.test.tsx` — Catches thrown errors, shows fallback, retry resets
- `frontend/src/components/common/__tests__/EmptyState.test.tsx` — Renders title/description/action, i18n keys
- `frontend/src/components/common/__tests__/Toast.test.tsx` — Show/dismiss/auto-expire, multiple toasts stack
- `frontend/src/hooks/__tests__/useRetry.test.ts` — Retries N times, exponential delay, gives up after max
- `frontend/src/hooks/__tests__/useOnlineStatus.test.ts` — Returns true/false, listens to online/offline events

### Tests (E2E)

- `frontend/e2e/error-states.spec.ts` — Playwright tests for loading, error, empty, and offline states

---

## FILES TO MODIFY

- `frontend/src/App.tsx` — Wrap each `<Route>` page element with `<ErrorBoundary>`; add `<ToastContainer>` and `<OfflineBanner>` to Layout or App root
- `frontend/src/services/api.ts` — Export error class `ApiError` with status code; no retry logic here (handled by React Query)
- `frontend/src/hooks/useOracleReadings.ts` — Add React Query `retry: 3` and `retryDelay` with exponential backoff to query options
- `frontend/src/hooks/useOracleUsers.ts` — Same retry configuration as above
- `frontend/src/components/oracle/ReadingHistory.tsx` — Replace `isLoading` text with `<LoadingSkeleton variant="list" />` and `isError` text with inline error + retry button
- `frontend/src/components/oracle/MultiUserSelector.tsx` — Show skeleton when `isLoading` is true
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — Use toast for submit errors instead of inline `<p>` (keep inline for validation errors)
- `frontend/src/components/oracle/SummaryTab.tsx` — Replace null-result placeholder with `<EmptyState>` component
- `frontend/src/components/oracle/DetailsTab.tsx` — Replace null-result placeholder with `<EmptyState>` component
- `frontend/src/components/Layout.tsx` — Add `<OfflineBanner />` above main content; add `<ToastContainer />` as portal target
- `frontend/src/pages/Dashboard.tsx` — Add loading skeleton for when stats are fetched
- `frontend/src/pages/Vault.tsx` — Add empty state for when no findings exist
- `frontend/src/pages/Learning.tsx` — Add empty state for when no insights exist
- `frontend/src/locales/en.json` — Add `common.offline`, `common.retry`, `common.empty_*`, `common.error_*`, toast keys
- `frontend/src/locales/fa.json` — Persian translations for all new keys

---

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Toast System & Context (30 min)

**Why first:** Toasts are consumed by every other component. Build the notification layer before anything uses it.

**Tasks:**

1. Create `frontend/src/hooks/useToast.ts`:

   ```typescript
   // Toast state: { id, type, message, duration }
   // useToast() returns { toasts, addToast, dismissToast }
   // Types: "success" | "error" | "warning" | "info"
   // Auto-dismiss after duration (default 5000ms)
   // Max 5 toasts visible (FIFO eviction)
   ```

   - Use React context (`ToastContext`) so any component can call `addToast()`
   - Each toast gets a unique `id` via `crypto.randomUUID()`
   - `useEffect` timer auto-removes after `duration`

2. Create `frontend/src/components/common/Toast.tsx`:
   - `ToastProvider` — wraps app, provides context
   - `ToastContainer` — fixed position `top-4 right-4` (RTL: `top-4 left-4`), renders toast stack
   - Individual `Toast` — card with icon, message, close button, color-coded border:
     - `error`: `border-nps-error` + red icon
     - `success`: `border-nps-success` + green icon
     - `warning`: `border-nps-warning` + yellow icon
     - `info`: `border-nps-accent` + blue icon
   - Enter animation: `animate-slide-in` (slide from right, fade in)
   - Exit: fade out on dismiss
   - RTL support: slide from left when `dir="rtl"`
   - ARIA: `role="alert"` + `aria-live="polite"` on container

3. Add Tailwind animation in `frontend/tailwind.config.ts`:

   ```typescript
   // Under theme.extend:
   keyframes: {
     'slide-in-right': {
       '0%': { transform: 'translateX(100%)', opacity: '0' },
       '100%': { transform: 'translateX(0)', opacity: '1' },
     },
     'slide-in-left': {
       '0%': { transform: 'translateX(-100%)', opacity: '0' },
       '100%': { transform: 'translateX(0)', opacity: '1' },
     },
     shimmer: {
       '0%': { backgroundPosition: '-200% 0' },
       '100%': { backgroundPosition: '200% 0' },
     },
   },
   animation: {
     'slide-in-right': 'slide-in-right 0.3s ease-out',
     'slide-in-left': 'slide-in-left 0.3s ease-out',
     shimmer: 'shimmer 1.5s ease-in-out infinite',
   },
   ```

4. Write tests: `frontend/src/components/common/__tests__/Toast.test.tsx`
   - Test: renders toast with message
   - Test: auto-dismisses after duration
   - Test: manual dismiss removes toast
   - Test: max 5 toasts, oldest evicted
   - Test: correct ARIA attributes

**Checkpoint:**

- [ ] Toast renders with all 4 types (success, error, warning, info)
- [ ] Auto-dismiss works after 5 seconds
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/components/common/__tests__/Toast.test.tsx`

---

### Phase 2: Loading Skeleton (30 min)

**Tasks:**

1. Create `frontend/src/components/common/LoadingSkeleton.tsx`:

   ```typescript
   interface SkeletonProps {
     variant: "line" | "card" | "circle" | "grid" | "list" | "reading";
     count?: number; // number of skeleton items (default 1)
     className?: string; // additional classes
   }
   ```

   - **line**: Single horizontal bar (h-4 rounded, shimmer bg)
   - **card**: Rectangle (h-24 rounded-lg, shimmer bg) — for StatsCard placeholders
   - **circle**: Round (w-10 h-10 rounded-full, shimmer bg) — for avatars
   - **grid**: 2x2 or 4-column grid of card skeletons — mirrors Dashboard stats layout
   - **list**: 3-5 stacked line skeletons with varying widths — for ReadingHistory
   - **reading**: Composite: circle + 3 lines + card — for Oracle reading result placeholder
   - All use `bg-nps-bg-input animate-shimmer` with gradient overlay
   - Shimmer gradient: `background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent); background-size: 200% 100%`
   - Accepts `count` to repeat the skeleton block N times
   - `aria-hidden="true"` + screen-reader-only "Loading" text via `sr-only` span

2. Write tests: `frontend/src/components/common/__tests__/LoadingSkeleton.test.tsx`
   - Test: renders correct variant structure (line = single bar, card = rectangle, etc.)
   - Test: `count` renders multiple items
   - Test: shimmer animation class is applied
   - Test: has `aria-hidden="true"` and sr-only text

**Checkpoint:**

- [ ] All 6 variants render correctly
- [ ] Shimmer animation is visible
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/components/common/__tests__/LoadingSkeleton.test.tsx`

---

### Phase 3: Error Boundary (30 min)

**Tasks:**

1. Create `frontend/src/components/common/ErrorBoundary.tsx`:

   ```typescript
   // React class component (hooks can't catch render errors)
   // Props: children, fallback? (optional custom fallback)
   // State: { hasError: boolean, error: Error | null }
   // static getDerivedStateFromError(error) → { hasError: true, error }
   // componentDidCatch(error, errorInfo) → console.error, optionally report
   ```

   - Default fallback UI:
     - Centered card (`bg-nps-bg-card border-nps-error`)
     - Error icon (red circle with "!")
     - Title: `t("common.error_boundary_title")` → "Something went wrong"
     - Message: `t("common.error_boundary_message")` → "This section encountered an error."
     - Error details in collapsible `<details>` (dev mode only via `import.meta.env.DEV`)
     - "Try Again" button → resets `hasError` to `false` (re-renders children)
     - "Go to Dashboard" link → `navigate("/dashboard")` as escape hatch
   - i18n: Use `withTranslation` HOC (class components can't use `useTranslation`)
   - Custom fallback: If `fallback` prop provided, render that instead

2. Wrap each route in `frontend/src/App.tsx`:

   ```tsx
   <Route
     path="/oracle"
     element={
       <ErrorBoundary>
         <Oracle />
       </ErrorBoundary>
     }
   />
   ```

   Apply to all 6 page routes: dashboard, scanner, oracle, vault, learning, settings.

3. Write tests: `frontend/src/components/common/__tests__/ErrorBoundary.test.tsx`
   - Test: renders children when no error
   - Test: shows fallback when child throws during render
   - Test: "Try Again" button resets and re-renders children
   - Test: error details visible only in dev mode
   - Test: custom fallback prop is used when provided

**Checkpoint:**

- [ ] ErrorBoundary catches thrown errors and shows recovery UI
- [ ] "Try Again" button resets the boundary
- [ ] All 6 routes wrapped in App.tsx
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/components/common/__tests__/ErrorBoundary.test.tsx`

---

### Phase 4: Empty State Component (25 min)

**Tasks:**

1. Create `frontend/src/components/common/EmptyState.tsx`:

   ```typescript
   interface EmptyStateProps {
     icon?:
       | "readings"
       | "profiles"
       | "vault"
       | "search"
       | "learning"
       | "generic";
     title: string;
     description?: string;
     action?: {
       label: string;
       onClick: () => void;
     };
   }
   ```

   - Icon mapping (simple SVG or Unicode):
     - `readings`: crystal ball / scroll icon
     - `profiles`: person outline
     - `vault`: lock / chest icon
     - `search`: magnifying glass
     - `learning`: brain / lightbulb
     - `generic`: empty box
   - Use NPS design tokens: `text-nps-text-dim` for description, `text-nps-oracle-accent` for icon
   - Layout: centered vertically, icon (48px), title (text-sm font-medium), description (text-xs), action button
   - Action button uses `bg-nps-bg-button` style

2. Replace existing placeholder text in components:
   - `SummaryTab.tsx`: Replace `<p>{t("oracle.results_placeholder")}</p>` with:
     ```tsx
     <EmptyState icon="readings" title={t("oracle.results_placeholder")} />
     ```
   - `DetailsTab.tsx`: Same replacement with `t("oracle.details_placeholder")`
   - `ReadingHistory.tsx`: Replace empty state text at line 67 with `<EmptyState icon="readings" ...>`
   - `Vault.tsx`: Add `<EmptyState icon="vault" title={t("vault.empty")} />`
   - `Learning.tsx`: Add `<EmptyState icon="learning" title={t("learning.empty")} />`

3. Write tests: `frontend/src/components/common/__tests__/EmptyState.test.tsx`
   - Test: renders title and description
   - Test: renders icon variant
   - Test: action button calls onClick
   - Test: no action button when prop omitted

**Checkpoint:**

- [ ] EmptyState renders with all 6 icon variants
- [ ] Existing placeholder text replaced in 5 components
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/components/common/__tests__/EmptyState.test.tsx`

---

### Phase 5: Offline Detection (25 min)

**Tasks:**

1. Create `frontend/src/hooks/useOnlineStatus.ts`:

   ```typescript
   // Returns boolean: true if online, false if offline
   // Listens to window "online" and "offline" events
   // Initial value from navigator.onLine
   ```

2. Create `frontend/src/components/common/OfflineBanner.tsx`:
   - Fixed position banner at top of viewport (above everything, `z-50`)
   - Yellow/orange background (`bg-nps-warning/10 border-b border-nps-warning`)
   - Icon + message: "You are offline. Changes will sync when you reconnect."
   - i18n key: `common.offline_message`
   - Only rendered when `useOnlineStatus()` returns `false`
   - Auto-hides with a brief "Back online!" success message when reconnected (2s, then gone)
   - RTL: text direction auto from parent

3. Add `<OfflineBanner />` to `frontend/src/components/Layout.tsx`:
   - Place above the `<div className="flex min-h-screen">` wrapper
   - Or as first child of the flex container

4. Write tests: `frontend/src/hooks/__tests__/useOnlineStatus.test.ts`
   - Test: returns `true` initially (default navigator.onLine)
   - Test: returns `false` after offline event
   - Test: returns `true` after online event

**Checkpoint:**

- [ ] OfflineBanner appears when offline (toggle in DevTools → Network → Offline)
- [ ] Banner auto-hides when back online
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/hooks/__tests__/useOnlineStatus.test.ts`

---

### Phase 6: Retry Logic (30 min)

**Tasks:**

1. Create `frontend/src/hooks/useRetry.ts`:

   ```typescript
   interface RetryOptions {
     maxRetries?: number; // default 3
     baseDelay?: number; // default 1000ms
     maxDelay?: number; // default 10000ms
     backoffFactor?: number; // default 2
     onRetry?: (attempt: number, error: Error) => void;
   }

   function useRetry<T>(
     asyncFn: () => Promise<T>,
     options?: RetryOptions,
   ): {
     execute: () => Promise<T>;
     isRetrying: boolean;
     attempt: number;
     reset: () => void;
   };
   ```

   - Exponential backoff: `delay = min(baseDelay * backoffFactor^attempt, maxDelay)`
   - Add jitter: `delay = delay * (0.5 + Math.random() * 0.5)` to prevent thundering herd
   - Do NOT retry on 4xx errors (client errors) — only 5xx and network errors
   - The hook tracks `isRetrying` and `attempt` count for UI feedback

2. Enhance `frontend/src/services/api.ts`:
   - Create typed error class:
     ```typescript
     export class ApiError extends Error {
       constructor(
         message: string,
         public readonly status: number,
         public readonly detail?: string,
       ) {
         super(message);
         this.name = "ApiError";
       }
       get isClientError(): boolean {
         return this.status >= 400 && this.status < 500;
       }
       get isServerError(): boolean {
         return this.status >= 500;
       }
       get isNetworkError(): boolean {
         return this.status === 0;
       }
     }
     ```
   - Update `request()` function to throw `ApiError` instead of plain `Error`
   - Set `status: 0` for network failures (fetch catch block)

3. Configure React Query global retry in `frontend/src/main.tsx` (or wherever QueryClient is created):

   ```typescript
   const queryClient = new QueryClient({
     defaultOptions: {
       queries: {
         retry: (failureCount, error) => {
           if (error instanceof ApiError && error.isClientError) return false;
           return failureCount < 3;
         },
         retryDelay: (attemptIndex) =>
           Math.min(1000 * 2 ** attemptIndex, 10000),
       },
       mutations: {
         retry: false, // Mutations should not auto-retry
       },
     },
   });
   ```

4. Write tests: `frontend/src/hooks/__tests__/useRetry.test.ts`
   - Test: succeeds on first try — returns result, attempt = 1
   - Test: retries on failure — calls fn 3 times before giving up
   - Test: exponential backoff — delays increase between retries
   - Test: does not retry on 4xx (ApiError with isClientError)
   - Test: `onRetry` callback called on each retry
   - Test: `reset` clears attempt count

**Checkpoint:**

- [ ] `useRetry` retries failed operations 3 times with exponential backoff
- [ ] React Query auto-retries queries (not mutations) on server/network errors
- [ ] `ApiError` class correctly identifies error types
- [ ] Tests pass
- Verify: `cd frontend && npx vitest run src/hooks/__tests__/useRetry.test.ts`

---

### Phase 7: Wire Loading Skeletons Into Existing Components (30 min)

**Tasks:**

1. **ReadingHistory.tsx** (line 61-63 current loading state):
   - Replace `<p className="text-xs text-nps-text-dim">{t("common.loading")}</p>`
   - With: `<LoadingSkeleton variant="list" count={5} />`
   - Replace error state (line 34-37) with:
     ```tsx
     <div className="text-center py-4">
       <p className="text-xs text-nps-error mb-2">
         {t("oracle.error_history")}
       </p>
       <button
         onClick={() => refetch()}
         className="text-xs text-nps-accent hover:underline"
       >
         {t("common.retry")}
       </button>
     </div>
     ```
   - Add `refetch` from `useReadingHistory` return value

2. **MultiUserSelector.tsx** (when `isLoading` is true):
   - Show `<LoadingSkeleton variant="line" count={2} />` instead of empty dropdown

3. **Oracle.tsx** (general loading state):
   - When `isLoading` from `useOracleUsers()` is true, show `<LoadingSkeleton variant="reading" />` for the user profile section

4. **Dashboard.tsx**:
   - Wrap stats grid in conditional: if loading, show `<LoadingSkeleton variant="grid" />`
   - (Dashboard data fetching will come in Session 22 — for now, add skeleton support structure)

5. **OracleConsultationForm.tsx**:
   - Replace inline error `<p>` (line 141-145) — keep it for form validation, but also fire a toast:
     ```tsx
     // In the catch block:
     const errorMsg =
       err instanceof Error ? err.message : t("oracle.error_submit");
     setError(errorMsg);
     addToast({ type: "error", message: errorMsg });
     ```
   - Import `useToast` from context

**Checkpoint:**

- [ ] ReadingHistory shows skeleton during load, retry button on error
- [ ] MultiUserSelector shows skeleton while loading users
- [ ] Oracle page shows skeleton while loading user profiles
- [ ] OracleConsultationForm fires toast on submit error
- Verify: `cd frontend && npx vitest run --reporter=verbose 2>&1 | head -50`

---

### Phase 8: i18n Translations (20 min)

**Tasks:**

1. Add keys to `frontend/src/locales/en.json` under `common`:

   ```json
   {
     "common": {
       "loading": "Loading...",
       "error": "An error occurred",
       "retry": "Try Again",
       "go_home": "Go to Dashboard",
       "offline_message": "You are offline. Changes will sync when you reconnect.",
       "back_online": "Back online!",
       "error_boundary_title": "Something went wrong",
       "error_boundary_message": "This section encountered an error. You can try again or return to the dashboard.",
       "error_details": "Error Details",
       "save": "Save",
       "cancel": "Cancel",
       "confirm": "Confirm"
     }
   }
   ```

2. Add empty state keys to `en.json`:

   ```json
   {
     "vault": {
       "empty": "No findings yet. Start a scan to discover wallet data."
     },
     "learning": {
       "empty": "No insights yet. Run scans and readings to train the AI."
     }
   }
   ```

3. Add all corresponding Persian translations to `frontend/src/locales/fa.json`:
   ```json
   {
     "common": {
       "retry": "\u062a\u0644\u0627\u0634 \u0645\u062c\u062f\u062f",
       "go_home": "\u0628\u0627\u0632\u06af\u0634\u062a \u0628\u0647 \u062f\u0627\u0634\u0628\u0648\u0631\u062f",
       "offline_message": "\u0634\u0645\u0627 \u0622\u0641\u0644\u0627\u06cc\u0646 \u0647\u0633\u062a\u06cc\u062f. \u062a\u063a\u06cc\u06cc\u0631\u0627\u062a \u067e\u0633 \u0627\u0632 \u0627\u062a\u0635\u0627\u0644 \u0645\u062c\u062f\u062f \u0647\u0645\u06af\u0627\u0645\u200c\u0633\u0627\u0632\u06cc \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.",
       "back_online": "\u062f\u0648\u0628\u0627\u0631\u0647 \u0622\u0646\u0644\u0627\u06cc\u0646 \u0634\u062f\u06cc\u062f!",
       "error_boundary_title": "\u0645\u0634\u06a9\u0644\u06cc \u067e\u06cc\u0634 \u0622\u0645\u062f",
       "error_boundary_message": "\u0627\u06cc\u0646 \u0628\u062e\u0634 \u0628\u0627 \u062e\u0637\u0627 \u0645\u0648\u0627\u062c\u0647 \u0634\u062f. \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u062a\u0644\u0627\u0634 \u06a9\u0646\u06cc\u062f.",
       "error_details": "\u062c\u0632\u0626\u06cc\u0627\u062a \u062e\u0637\u0627"
     }
   }
   ```
   (Actual Unicode Persian text — spec shows escaped form for safety; implementor writes real Persian.)

**Checkpoint:**

- [ ] All new i18n keys exist in both `en.json` and `fa.json`
- [ ] No missing keys when switching locale to FA
- Verify: `cd frontend && node -e "const en=require('./src/locales/en.json'); const fa=require('./src/locales/fa.json'); const missing = Object.keys(en.common).filter(k => !fa.common?.[k]); console.log(missing.length ? 'MISSING: ' + missing.join(', ') : 'OK')"`

---

### Phase 9: App-Level Integration (25 min)

**Tasks:**

1. **Wrap App with ToastProvider** in `frontend/src/main.tsx` (or wherever the React tree root is):

   ```tsx
   <QueryClientProvider client={queryClient}>
     <ToastProvider>
       <BrowserRouter>
         <App />
       </BrowserRouter>
     </ToastProvider>
   </QueryClientProvider>
   ```

2. **Add ToastContainer** to `Layout.tsx`:
   - Render `<ToastContainer />` as a sibling of the main content area (not inside Outlet)
   - It renders fixed-positioned, so it overlays content

3. **Add OfflineBanner** to `Layout.tsx`:
   - Render `<OfflineBanner />` before the flex container:
     ```tsx
     return (
       <>
         <OfflineBanner />
         <div className="flex min-h-screen bg-nps-bg">...</div>
         <ToastContainer />
       </>
     );
     ```

4. **Update QueryClient** with global retry config (see Phase 6 task 3)

5. **Verify ErrorBoundary wrapping** from Phase 3 is in place in App.tsx

**Checkpoint:**

- [ ] Toasts appear on API errors
- [ ] Offline banner shows when network toggled off
- [ ] ErrorBoundary catches crashes on any page
- [ ] React Query retries failed queries automatically
- Verify: `cd frontend && npx vitest run --reporter=verbose 2>&1 | tail -20`

---

### Phase 10: E2E Tests & Final Verification (30 min)

**Tasks:**

1. Create `frontend/e2e/error-states.spec.ts`:

   ```typescript
   // Test 1: Loading skeleton visible during data fetch
   //   - Navigate to Oracle page
   //   - Mock API to delay 2 seconds
   //   - Assert skeleton elements visible
   //   - After resolve, assert skeleton gone, data visible

   // Test 2: Error boundary catches page crash
   //   - Navigate to a page that throws (use a test-only error trigger)
   //   - Assert ErrorBoundary fallback UI visible
   //   - Click "Try Again"
   //   - Assert page re-renders

   // Test 3: Toast appears on API error
   //   - Navigate to Oracle page
   //   - Mock API to return 500
   //   - Submit a reading
   //   - Assert toast notification appears with error message
   //   - Assert toast auto-dismisses after ~5s

   // Test 4: Empty state on zero readings
   //   - Navigate to Oracle page
   //   - Mock reading history to return empty array
   //   - Switch to History tab
   //   - Assert EmptyState component visible with correct text

   // Test 5: Offline banner detection
   //   - Use Playwright context.setOffline(true)
   //   - Assert OfflineBanner visible with offline message
   //   - Set online again
   //   - Assert "Back online!" briefly visible, then banner gone

   // Test 6: Retry on server error
   //   - Mock API to fail twice then succeed
   //   - Navigate to Oracle page
   //   - Assert data eventually loads (after retries)
   ```

2. Run full test suite:

   ```bash
   cd frontend && npx vitest run
   cd frontend && npx playwright test e2e/error-states.spec.ts
   ```

3. Visual verification checklist:
   - [ ] Open browser → Oracle page → loading skeletons visible during fetch
   - [ ] Switch to FA locale → RTL toast slides from left
   - [ ] Toggle DevTools offline → yellow banner appears
   - [ ] Go back online → "Back online!" flash → banner gone
   - [ ] Kill API → submit reading → red toast appears

**Checkpoint:**

- [ ] All unit tests pass (0 failures)
- [ ] All E2E tests pass (0 failures)
- [ ] No TypeScript errors: `cd frontend && npx tsc --noEmit`
- [ ] No lint errors: `cd frontend && npx eslint src/ --max-warnings 0`
- Verify: `cd frontend && npx vitest run && npx tsc --noEmit && npx eslint src/ --max-warnings 0`

---

## TESTS TO WRITE

### Unit Tests (Vitest + Testing Library)

| Test File                                                           | What It Verifies                                              |
| ------------------------------------------------------------------- | ------------------------------------------------------------- |
| `frontend/src/components/common/__tests__/Toast.test.tsx`           | Toast renders, auto-dismisses, stacks, ARIA attrs             |
| `frontend/src/components/common/__tests__/LoadingSkeleton.test.tsx` | 6 variants render, shimmer class, count prop, a11y            |
| `frontend/src/components/common/__tests__/ErrorBoundary.test.tsx`   | Catches errors, shows fallback, retry resets, custom fallback |
| `frontend/src/components/common/__tests__/EmptyState.test.tsx`      | Renders title/desc/icon/action, all 6 variants                |
| `frontend/src/hooks/__tests__/useRetry.test.ts`                     | Retries N times, backoff delays, skips 4xx, callback, reset   |
| `frontend/src/hooks/__tests__/useOnlineStatus.test.ts`              | Online/offline event detection                                |

### E2E Tests (Playwright)

| Test File                           | What It Verifies                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| `frontend/e2e/error-states.spec.ts` | Loading skeletons, error boundary, toast on error, empty state, offline banner, retry behavior |

**Total: 6 unit test files + 1 E2E test file = ~30 individual test cases**

---

## ERROR SCENARIOS

| Scenario                            | Expected Behavior                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| API returns 500 on query            | React Query retries 3 times with exponential backoff, then shows error state   |
| API returns 500 on mutation         | No retry; toast notification shown immediately                                 |
| API returns 400 (validation error)  | No retry; inline error message in form                                         |
| API returns 401 (unauthorized)      | No retry; redirect to login (future) or toast                                  |
| Network failure (fetch throws)      | `ApiError` with `status: 0`; retry logic kicks in; offline banner if sustained |
| Component throws during render      | ErrorBoundary catches it, shows fallback with "Try Again"                      |
| Empty data from API                 | EmptyState component shown instead of blank space                              |
| User goes offline mid-operation     | Offline banner appears; pending mutations show toast "offline"                 |
| User comes back online              | Banner shows "Back online!" for 2s, then disappears                            |
| Multiple errors in quick succession | Toasts stack (max 5), oldest dismissed FIFO                                    |

---

## ACCEPTANCE CRITERIA

- [ ] Loading skeletons (shimmer) appear during every data fetch across Oracle, Dashboard, and History views
- [ ] Error boundaries wrap every page route — crashing one page does not crash the app
- [ ] Toast notifications appear for transient API errors (server/network), auto-dismiss in 5s
- [ ] Empty state components show for: no readings, no profiles selected, empty vault, empty learning
- [ ] Offline banner appears within 1s of going offline, disappears within 3s of reconnection
- [ ] React Query retries failed queries 3 times with exponential backoff (not mutations)
- [ ] `ApiError` class distinguishes client vs server vs network errors
- [ ] All new strings available in both EN and FA locales
- [ ] RTL: toasts slide from left, offline banner text is RTL, EmptyState layout centered
- [ ] No TypeScript errors (`npx tsc --noEmit`)
- [ ] All unit tests pass (`npx vitest run`)
- [ ] All E2E tests pass (`npx playwright test e2e/error-states.spec.ts`)
- [ ] No lint warnings (`npx eslint src/ --max-warnings 0`)

Verify all:

```bash
cd frontend && npx tsc --noEmit && npx vitest run && npx eslint src/ --max-warnings 0 && npx playwright test e2e/error-states.spec.ts
```

---

## HANDOFF

**Created:**

- `frontend/src/components/common/LoadingSkeleton.tsx`
- `frontend/src/components/common/ErrorBoundary.tsx`
- `frontend/src/components/common/EmptyState.tsx`
- `frontend/src/components/common/Toast.tsx`
- `frontend/src/components/common/OfflineBanner.tsx`
- `frontend/src/hooks/useRetry.ts`
- `frontend/src/hooks/useOnlineStatus.ts`
- `frontend/src/hooks/useToast.ts`
- `frontend/src/components/common/__tests__/Toast.test.tsx`
- `frontend/src/components/common/__tests__/LoadingSkeleton.test.tsx`
- `frontend/src/components/common/__tests__/ErrorBoundary.test.tsx`
- `frontend/src/components/common/__tests__/EmptyState.test.tsx`
- `frontend/src/hooks/__tests__/useRetry.test.ts`
- `frontend/src/hooks/__tests__/useOnlineStatus.test.ts`
- `frontend/e2e/error-states.spec.ts`

**Modified:**

- `frontend/src/App.tsx` — ErrorBoundary wrapping all routes
- `frontend/src/services/api.ts` — `ApiError` class, typed error throwing
- `frontend/src/hooks/useOracleReadings.ts` — Retry config (via global QueryClient)
- `frontend/src/hooks/useOracleUsers.ts` — Retry config (via global QueryClient)
- `frontend/src/components/oracle/ReadingHistory.tsx` — Skeleton + retry button
- `frontend/src/components/oracle/MultiUserSelector.tsx` — Skeleton when loading
- `frontend/src/components/oracle/OracleConsultationForm.tsx` — Toast on error
- `frontend/src/components/oracle/SummaryTab.tsx` — EmptyState replacement
- `frontend/src/components/oracle/DetailsTab.tsx` — EmptyState replacement
- `frontend/src/components/Layout.tsx` — OfflineBanner + ToastContainer
- `frontend/src/pages/Dashboard.tsx` — Skeleton support
- `frontend/src/pages/Vault.tsx` — EmptyState
- `frontend/src/pages/Learning.tsx` — EmptyState
- `frontend/src/locales/en.json` — New i18n keys
- `frontend/src/locales/fa.json` — Persian translations
- `frontend/tailwind.config.ts` — Shimmer + slide-in animations
- `frontend/src/main.tsx` — ToastProvider wrapper, QueryClient retry config

**Next session needs:**

- Session 30 (Animations & Micro-interactions) depends on the loading skeleton shimmer animation infrastructure from this session. The `tailwind.config.ts` keyframe system and the component architecture (common components pattern) established here are the foundation for adding page transitions, card animations, and the loading orb in Session 30.
- The `ErrorBoundary`, `Toast`, and `EmptyState` components are consumed by Sessions 31+ as new features are added.
