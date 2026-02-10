# SESSION 43 SPEC — E2E Tests: Frontend Flows (Playwright)

**Block:** Testing & Deployment (Sessions 41-45)
**Estimated Duration:** 6-8 hours
**Complexity:** High
**Dependencies:** Sessions 41-42 (backend tests), Sessions 19-31 (frontend pages + components built)

---

## TL;DR

- Write 6 new Playwright E2E spec files covering all major user-facing flows: authentication/navigation, profile CRUD, time/question reading, multi-user reading, reading history, and settings/locale/RTL
- Add a 7th spec for responsive/mobile viewport testing at 375px width
- Expand the shared `fixtures.ts` with robust helpers for login, profile seeding, screenshot capture, locale switching, and test cleanup
- Update `playwright.config.ts` to add a mobile project, enable screenshots on every step, configure HTML report output, and increase timeouts
- Capture timestamped screenshots at every critical UI step for visual regression review
- Target 26+ individual test cases across all spec files, covering happy paths, error states, edge cases, and RTL/locale switching

---

## OBJECTIVES

1. **Authentication & navigation E2E** — Verify the app loads, redirects to `/dashboard`, sidebar contains all 6 nav links, active link highlighting works, and direct URL access works for all routes
2. **Profile CRUD E2E** — Create a new Oracle user profile via the modal form, verify it appears in the `MultiUserSelector` dropdown, edit it, delete it with two-step confirmation, and verify selection persistence across navigation
3. **Time/question reading E2E** — Select a user, choose a time sign type, submit a consultation, verify reading results appear in the Summary/Details/History tabs, and submit a question reading with Persian keyboard input
4. **Multi-user reading E2E** — Select a primary user + secondary users via the chip-based `MultiUserSelector`, submit a multi-user reading, verify the max 5 users limit is enforced, and verify results render
5. **Reading history E2E** — Navigate to the History tab, verify past readings display with type badges and dates, filter by type via chips, expand/collapse reading details, and verify count display
6. **Settings & locale E2E** — Toggle language from English to Persian via `LanguageToggle`, verify `document.documentElement.dir` flips to `"rtl"`, verify translated nav labels, verify sidebar border flips, and verify language persists across route navigation
7. **Responsive E2E** — Re-run key flows (navigation, profile creation, reading submission, RTL mode) at 375px mobile viewport width and verify no horizontal overflow
8. **Screenshot documentation** — Capture named screenshots at every significant UI state for visual review in `e2e-screenshots/`

---

## PREREQUISITES

- [ ] Frontend pages exist: `Dashboard.tsx`, `Oracle.tsx`, `Settings.tsx` in `frontend/src/pages/`
- [ ] Oracle components exist: `MultiUserSelector.tsx`, `UserForm.tsx`, `OracleConsultationForm.tsx`, `ReadingResults.tsx`, `ReadingHistory.tsx`, `LanguageToggle.tsx` in `frontend/src/components/`
- [ ] Playwright installed and configured (`frontend/playwright.config.ts` exists — 30 lines, Chromium only, `webServer` auto-starts Vite)
- [ ] API server running at `http://localhost:8000` with Oracle endpoints functional (user CRUD + reading submission)
- [ ] Frontend dev server running at `http://localhost:5173` (or auto-started by Playwright)
- [ ] Existing `frontend/e2e/fixtures.ts` (51 lines) with `createTestUser()` and `cleanupTestUsers()` helpers
- [ ] Existing `frontend/e2e/oracle.spec.ts` (173 lines) with 8 basic Oracle E2E scenarios (reference, kept for backward compatibility)
- [ ] i18n locale files: `frontend/src/locales/en.json` (190 lines) and `frontend/src/locales/fa.json`
- [ ] Sessions 41-42 complete (backend API tests and Oracle service tests passing)
- Verification:
  ```bash
  test -f frontend/playwright.config.ts && \
  test -f frontend/e2e/fixtures.ts && \
  test -f frontend/e2e/oracle.spec.ts && \
  test -f frontend/src/pages/Oracle.tsx && \
  test -f frontend/src/pages/Settings.tsx && \
  test -f frontend/src/pages/Dashboard.tsx && \
  test -f frontend/src/components/oracle/ReadingHistory.tsx && \
  test -f frontend/src/components/LanguageToggle.tsx && \
  test -f frontend/src/locales/en.json && \
  test -f frontend/src/locales/fa.json && \
  echo "ALL PREREQUISITES OK"
  ```

---

## EXISTING CODE CONTEXT

### Current Playwright Config (`frontend/playwright.config.ts` — 30 lines)

```typescript
// Key settings:
testDir: "./e2e"
timeout: 30000
expect: { timeout: 5000 }
screenshot: "only-on-failure"   // Needs upgrade to "on"
projects: [{ name: "chromium" }] // Needs mobile project
webServer: { command: "npm run dev", url: "http://localhost:5173" }
```

### Current Fixtures (`frontend/e2e/fixtures.ts` — 51 lines)

- `createTestUser(page, name)` — POST `/api/oracle/users` with Bearer token auth, returns user ID
- `cleanupTestUsers(page)` — searches for `E2E_` prefixed users via GET, deletes each one
- Both use `process.env.API_SECRET_KEY || "changeme-generate-a-real-secret"`
- Missing: login helper, profile seeding, screenshot capture, locale switching, multi-profile creation

### Current Routes (`frontend/src/App.tsx` — 35 lines)

| Route        | Page Component | Notes                                         |
| ------------ | -------------- | --------------------------------------------- |
| `/`          | Redirect       | Redirects to `/dashboard`                     |
| `/dashboard` | `Dashboard`    | Stats cards (Keys Tested, Seeds, Hits, Speed) |
| `/scanner`   | `Scanner`      | Scanner control page                          |
| `/oracle`    | `Oracle`       | User profiles + consultation + results        |
| `/vault`     | `Vault`        | Findings browser                              |
| `/learning`  | `Learning`     | AI insights                                   |
| `/settings`  | `Settings`     | Stub page (TODOs for language, theme, etc.)   |

No `/login` route — auth flow depends on Session 2 implementation. The `login()` fixture must handle both scenarios (login page present vs. direct localStorage injection).

### Key UI Components for Test Targeting

| Component                | Key Selectors                                                                   |
| ------------------------ | ------------------------------------------------------------------------------- |
| `Layout.tsx`             | Sidebar: `nav.w-64`, NavLinks: `a.block`, NPS title: `h1.text-nps-gold`         |
| `LanguageToggle.tsx`     | Button with EN/FA text, `aria-label` for accessibility                          |
| `MultiUserSelector.tsx`  | Primary: `select[aria-label="Select profile"]`, Add: `+ Add New Profile` button |
| `UserForm.tsx`           | Modal: `div[role="dialog"][aria-modal="true"]`, Submit: `button[type="submit"]` |
| `OracleConsultationForm` | Textarea `dir="rtl"`, Keyboard: `aria-label="Toggle Persian keyboard"`, Submit  |
| `ReadingResults.tsx`     | Tabs: `role="tablist"`, each tab: `role="tab"` with `aria-selected`             |
| `ReadingHistory.tsx`     | Filter chips: 4 buttons (All/Readings/Questions/Names), expandable items        |
| `SignTypeSelector`       | Sign types: time, number, carplate, custom                                      |

### i18n Keys Used in Tests

```
nav.dashboard, nav.scanner, nav.oracle, nav.vault, nav.learning, nav.settings
oracle.title, oracle.subtitle, oracle.user_profile, oracle.add_new_profile
oracle.edit_profile, oracle.new_profile, oracle.select_to_begin, oracle.select_profile
oracle.submit_reading, oracle.tab_summary, oracle.tab_details, oracle.tab_history
oracle.error_name_required, oracle.error_birthday_required, oracle.error_mother_name_required
oracle.history_empty, oracle.history_count, oracle.load_more
oracle.keyboard_toggle, oracle.primary_user, oracle.add_secondary
common.loading, common.save, common.cancel
```

---

## FILES TO CREATE

| #   | File                              | Purpose                                                  |
| --- | --------------------------------- | -------------------------------------------------------- |
| 1   | `frontend/e2e/auth.spec.ts`       | App load, sidebar navigation, routing, active link tests |
| 2   | `frontend/e2e/profile.spec.ts`    | Oracle user profile CRUD via modal form                  |
| 3   | `frontend/e2e/reading.spec.ts`    | Time/question reading submission + results tabs          |
| 4   | `frontend/e2e/history.spec.ts`    | Reading history browsing, filtering, expansion           |
| 5   | `frontend/e2e/settings.spec.ts`   | Language toggle, RTL/LTR, Persian translations           |
| 6   | `frontend/e2e/responsive.spec.ts` | Mobile viewport (375px) key flow tests                   |

## FILES TO MODIFY

| #   | File                            | Changes                                                                                                                                           |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `frontend/e2e/fixtures.ts`      | Add 8 new helpers: login, seedTestProfile, seedMultipleProfiles, takeStepScreenshot, waitForApiReady, authHeaders, switchToFarsi, switchToEnglish |
| 2   | `frontend/playwright.config.ts` | Add mobile project, screenshot "on", HTML report, increase timeouts                                                                               |
| 3   | `frontend/.gitignore`           | Add e2e-screenshots/, e2e-results/, e2e-report/                                                                                                   |

## FILES TO DELETE

- None (existing `oracle.spec.ts` kept for backward compatibility — its 8 tests remain as a baseline)

---

## IMPLEMENTATION PHASES

### Phase 1: Update Playwright Config & Shared Fixtures (~60 min)

**Tasks:**

1. Update `frontend/playwright.config.ts` (currently 30 lines):

   ```typescript
   import { defineConfig, devices } from "@playwright/test";

   export default defineConfig({
     testDir: "./e2e",
     timeout: 60000, // 30s -> 60s for API-dependent flows
     expect: { timeout: 10000 }, // 5s -> 10s for API response assertions
     fullyParallel: false, // Sequential — tests may share DB state
     forbidOnly: !!process.env.CI,
     retries: process.env.CI ? 2 : 0,
     workers: process.env.CI ? 1 : 1, // Single worker for state safety
     reporter: [["html", { outputFolder: "e2e-report" }], ["list"]],
     outputDir: "e2e-results",
     use: {
       baseURL: "http://localhost:5173",
       trace: "on-first-retry",
       screenshot: "on", // Capture at every step (was "only-on-failure")
       video: "on-first-retry",
     },
     projects: [
       {
         name: "chromium",
         use: { ...devices["Desktop Chrome"] },
       },
       {
         name: "mobile-chrome",
         use: { ...devices["Pixel 5"] }, // 393x851 viewport, mobile UA
       },
     ],
     webServer: {
       command: "npm run dev",
       url: "http://localhost:5173",
       reuseExistingServer: !process.env.CI,
       timeout: 120000,
     },
   });
   ```

   Key changes from current config:
   - `timeout`: 30000 -> 60000
   - `expect.timeout`: 5000 -> 10000
   - `screenshot`: "only-on-failure" -> "on"
   - `fullyParallel`: true -> false
   - Added `mobile-chrome` project (Pixel 5 = 393px, close to 375px target)
   - Added `reporter` with HTML + list
   - Added `outputDir` and `video` on retry

2. Expand `frontend/e2e/fixtures.ts` (currently 51 lines) with these helpers:

   **`getAuthToken()` and `authHeaders()`** — centralize auth header construction:

   ```typescript
   export function getAuthToken(): string {
     return process.env.API_SECRET_KEY || "changeme-generate-a-real-secret";
   }

   export function authHeaders(): Record<string, string> {
     return {
       Authorization: `Bearer ${getAuthToken()}`,
       "Content-Type": "application/json",
     };
   }
   ```

   **`login(page, username?, password?)`** — handles both auth-gated and non-gated scenarios:

   ```typescript
   export async function login(
     page: Page,
     username: string = "admin",
     password: string = "admin",
   ): Promise<void> {
     await page.goto("/");

     // Check if login page exists (adaptive — works whether Session 2 auth is complete or not)
     const loginForm = page.locator(
       "[data-testid='login-form'], form[action*='login'], input[name='username']",
     );
     if (await loginForm.isVisible({ timeout: 3000 }).catch(() => false)) {
       await page
         .locator("input[name='username'], input[type='text']")
         .first()
         .fill(username);
       await page
         .locator("input[name='password'], input[type='password']")
         .first()
         .fill(password);
       await page.locator("button[type='submit']").first().click();
       await page.waitForURL("**/dashboard", { timeout: 10000 });
     } else {
       // No login page — set token directly in localStorage (legacy auth mode)
       await page.evaluate((token) => {
         localStorage.setItem("nps_auth_token", token);
       }, getAuthToken());
       await page.goto("/dashboard");
     }
     await page.waitForLoadState("networkidle");
   }
   ```

   **`seedTestProfile(page, overrides?)`** — creates profile via API, returns full object:

   ```typescript
   export interface TestProfile {
     id: number;
     name: string;
     birthday: string;
     mother_name: string;
     country?: string;
     city?: string;
   }

   export async function seedTestProfile(
     page: Page,
     overrides: Partial<TestProfile> = {},
   ): Promise<TestProfile> {
     const defaults = {
       name: `E2E_Profile_${Date.now()}`,
       birthday: "1990-06-15",
       mother_name: "E2E_Mother",
       country: "US",
       city: "Test City",
     };
     const data = { ...defaults, ...overrides };
     const response = await page.request.post(`${API_BASE}/api/oracle/users`, {
       data,
       headers: authHeaders(),
     });
     const json = await response.json();
     return { ...data, id: json.id };
   }
   ```

   **`seedMultipleProfiles(page, count)`** — creates N profiles for multi-user tests:

   ```typescript
   export async function seedMultipleProfiles(
     page: Page,
     count: number,
   ): Promise<TestProfile[]> {
     const profiles: TestProfile[] = [];
     const birthdays = [
       "1990-06-15",
       "1985-03-22",
       "1992-11-08",
       "1988-01-30",
       "1995-07-04",
     ];
     for (let i = 0; i < count; i++) {
       const profile = await seedTestProfile(page, {
         name: `E2E_Multi_${i}_${Date.now()}`,
         birthday: birthdays[i % birthdays.length],
         mother_name: `E2E_Mother_${i}`,
       });
       profiles.push(profile);
     }
     return profiles;
   }
   ```

   **`takeStepScreenshot(page, testName, stepName)`** — captures named screenshot:

   ```typescript
   import * as fs from "fs";
   import * as path from "path";

   export async function takeStepScreenshot(
     page: Page,
     testName: string,
     stepName: string,
   ): Promise<void> {
     const dir = path.join(__dirname, "..", "e2e-screenshots");
     if (!fs.existsSync(dir)) {
       fs.mkdirSync(dir, { recursive: true });
     }
     const safeName = `${testName}--${stepName}`.replace(
       /[^a-zA-Z0-9_-]/g,
       "_",
     );
     await page.screenshot({
       path: path.join(dir, `${safeName}.png`),
       fullPage: true,
     });
   }
   ```

   **`waitForApiReady(page, maxRetries?)`** — polls health endpoint:

   ```typescript
   export async function waitForApiReady(
     page: Page,
     maxRetries: number = 10,
   ): Promise<void> {
     for (let i = 0; i < maxRetries; i++) {
       try {
         const response = await page.request.get(`${API_BASE}/health`);
         if (response.ok()) return;
       } catch {
         // API not ready yet
       }
       await page.waitForTimeout(1000);
     }
     throw new Error("API server not ready after retries");
   }
   ```

   **`switchToFarsi(page)` and `switchToEnglish(page)`** — locale toggle helpers:

   ```typescript
   export async function switchToFarsi(page: Page): Promise<void> {
     const htmlLang = await page.locator("html").getAttribute("lang");
     if (htmlLang === "fa") return; // Already in Farsi
     const toggle = page
       .locator("button")
       .filter({ hasText: /EN.*FA|FA.*EN/ })
       .first();
     await toggle.click();
     await expect(page.locator("html")).toHaveAttribute("dir", "rtl", {
       timeout: 5000,
     });
   }

   export async function switchToEnglish(page: Page): Promise<void> {
     const htmlLang = await page.locator("html").getAttribute("lang");
     if (htmlLang === "en" || !htmlLang) return; // Already in English
     const toggle = page
       .locator("button")
       .filter({ hasText: /EN.*FA|FA.*EN/ })
       .first();
     await toggle.click();
     await expect(page.locator("html")).toHaveAttribute("dir", "ltr", {
       timeout: 5000,
     });
   }
   ```

   Keep existing `createTestUser()` and `cleanupTestUsers()` unchanged (used by `oracle.spec.ts`).

3. Add to `frontend/.gitignore`:
   ```
   e2e-screenshots/
   e2e-results/
   e2e-report/
   ```

**Checkpoint:**

- [ ] `playwright.config.ts` has `chromium` and `mobile-chrome` projects
- [ ] `fixtures.ts` exports all 10 helpers: `getAuthToken`, `authHeaders`, `login`, `seedTestProfile`, `seedMultipleProfiles`, `takeStepScreenshot`, `waitForApiReady`, `switchToFarsi`, `switchToEnglish`, `cleanupTestUsers`, `createTestUser`
- [ ] `screenshot` config set to `"on"`, timeout set to `60000`
- [ ] `.gitignore` updated with e2e output directories
- Verify: `cd frontend && npx tsc --noEmit e2e/fixtures.ts 2>&1 | head -5` — no TypeScript errors

STOP if checkpoint fails

---

### Phase 2: Auth & Navigation Tests — `auth.spec.ts` (~45 min)

**Tasks:**

Create `frontend/e2e/auth.spec.ts` with 4 tests:

**Test 1: `app loads and redirects to dashboard`**

- Navigate to `/`
- Verify URL becomes `/dashboard` (redirect from `App.tsx: <Navigate to="/dashboard" replace />`)
- Verify Dashboard heading "Dashboard" is visible
- Verify sidebar contains NPS title (`h1` with "NPS" text)
- Screenshot: "auth--app-loaded"

**Test 2: `sidebar shows all navigation links`**

- Navigate to `/dashboard`
- Verify 6 NavLink elements exist in the sidebar with expected text: Dashboard, Scanner, Oracle, Vault, Learning, Settings
- Verify LanguageToggle button (EN/FA) is visible in sidebar header
- Screenshot: "auth--sidebar-links"

**Test 3: `navigate to each page via sidebar clicks`**

- Start at `/dashboard`
- For each page (Scanner, Oracle, Vault, Learning, Settings):
  - Click the corresponding sidebar NavLink
  - Verify URL changes to the expected path
  - Verify page heading is visible
  - Verify the clicked NavLink has the active class (`bg-nps-bg-button text-nps-text-bright`)
- Screenshot at each page

**Test 4: `direct URL access works for all routes`**

- For each route (`/dashboard`, `/scanner`, `/oracle`, `/vault`, `/learning`, `/settings`):
  - Navigate directly via `page.goto(route)`
  - Verify the page loads (heading element visible, no error state)
- This confirms react-router-dom handles all routes

**Checkpoint:**

- [ ] `auth.spec.ts` has 4 test cases
- [ ] Each test captures at least 1 screenshot via `takeStepScreenshot()`
- [ ] Tests use `login()` fixture for initial page setup
- Verify: `cd frontend && npx playwright test e2e/auth.spec.ts --list` — lists 4 tests

STOP if checkpoint fails

---

### Phase 3: Profile CRUD Tests — `profile.spec.ts` (~60 min)

**Tasks:**

Create `frontend/e2e/profile.spec.ts` with 5 tests.

All tests use `test.beforeEach(login)` and `test.afterEach(cleanupTestUsers)`.

**Test 1: `create new profile via form`**

- Navigate to `/oracle`
- Click "+ Add New Profile" button (from `MultiUserSelector`)
- Verify `UserForm` modal appears with `role="dialog"` and `aria-modal="true"`
- Fill fields: name="E2E_NewProfile", birthday="1990-06-15", mother_name="E2E_TestMother"
- Screenshot: "profile--form-filled"
- Click `button[type="submit"]` (submit text: "Add New Profile" from `t("oracle.add_new_profile")`)
- Wait for modal to close (dialog element hidden)
- Verify "E2E_NewProfile" appears as an option in the primary user `select[aria-label]` dropdown
- Verify profile is auto-selected (birthday "1990-06-15" visible in info section below selector)
- Screenshot: "profile--created-in-selector"

**Test 2: `form validation rejects empty required fields`**

- Navigate to `/oracle`
- Click "+ Add New Profile"
- Click submit immediately without filling any fields
- Verify 3 validation errors appear via `role="alert"` elements:
  - Name error: text matching "Name must be at least 2 characters"
  - Birthday error: text matching "Birthday is required"
  - Mother's name error: text matching "Mother's name must be at least 2 characters"
- Screenshot: "profile--validation-errors"
- Fill name with "A" (1 char) — verify name error persists
- Fill birthday with future date — verify error changes to "Birthday cannot be in the future"

**Test 3: `edit existing profile`**

- Seed a profile via API: `seedTestProfile(page, { name: "E2E_EditTarget" })`
- Navigate to `/oracle`, reload to pick up new profile
- Select "E2E_EditTarget" from the primary user dropdown
- Click "Edit Profile" button (visible only when user selected, from `MultiUserSelector`)
- Verify `UserForm` modal opens with pre-filled name "E2E_EditTarget"
- Change city field to "Los Angeles"
- Click Save (`t("common.save")`)
- Verify modal closes, profile still selected
- Screenshot: "profile--after-edit"

**Test 4: `delete profile with two-step confirmation`**

- Seed a profile via API: `seedTestProfile(page, { name: "E2E_DeleteTarget" })`
- Navigate to `/oracle`, select "E2E_DeleteTarget"
- Click "Edit Profile" to open modal
- Click "Delete" button — verify it changes text to "Confirm Delete" (two-step from `UserForm.tsx` line 191-196)
- Screenshot: "profile--delete-confirmation"
- Click "Confirm Delete"
- Verify modal closes
- Verify "E2E_DeleteTarget" no longer appears in dropdown options
- Verify `oracle.select_to_begin` placeholder message is visible (no user selected)
- Screenshot: "profile--after-delete"

**Test 5: `profile selection persists across page navigation`**

- Seed a profile via API: `seedTestProfile(page, { name: "E2E_PersistTest" })`
- Navigate to `/oracle`, select "E2E_PersistTest"
- Verify selected (birthday info visible)
- Navigate to `/settings` via sidebar
- Navigate back to `/oracle` via sidebar
- Verify "E2E_PersistTest" is still selected (from `Oracle.tsx` localStorage persistence via `SELECTED_USER_KEY = "nps_selected_oracle_user"`)
- Screenshot: "profile--persisted-selection"

**Checkpoint:**

- [ ] `profile.spec.ts` has 5 test cases
- [ ] Tests cover: create, validate, edit, delete (two-step), and persistence
- [ ] All tests use `cleanupTestUsers()` in `afterEach`
- [ ] Each test captures at least 1 screenshot
- Verify: `cd frontend && npx playwright test e2e/profile.spec.ts --list` — lists 5 tests

STOP if checkpoint fails

---

### Phase 4: Reading Flow Tests — `reading.spec.ts` (~75 min)

**Tasks:**

Create `frontend/e2e/reading.spec.ts` with 5 tests.

All tests use `test.beforeEach(login)` and `test.afterEach(cleanupTestUsers)`.

**Test 1: `select user and submit time reading`**

- Seed profile via `seedTestProfile(page)`
- Navigate to `/oracle`, select the seeded profile
- Verify consultation form appears: "Consulting for [name]" text (from `OracleConsultationForm.tsx` line 78)
- `SignTypeSelector` defaults to type "time" — verify sign input area visible
- Enter a valid time value (e.g., "14:30")
- Screenshot: "reading--form-ready"
- Click "Submit Reading" button
- Verify loading state: button text changes to "Loading..." (`aria-busy="true"`)
- Wait for results: loading state disappears, `ReadingResults` section updates
- Verify Summary tab is active by default (`role="tab"` with `aria-selected="true"` on `#tab-summary`)
- Verify summary content not empty (no placeholder text)
- Screenshot: "reading--results-visible"

**Test 2: `reading results tab switching with ARIA`**

- Seed profile, select it, submit a reading, wait for results
- Verify `tablist` exists with 3 tabs: Summary, Details, History
- Click "Details" tab (`#tab-details`)
- Verify `#tab-details` has `aria-selected="true"`, `#tab-summary` has `aria-selected="false"`
- Verify `#tabpanel-details` is visible (no `hidden` class), `#tabpanel-summary` has `hidden` class
- Screenshot: "reading--details-tab"
- Click "History" tab
- Verify History panel visible, Details panel hidden
- Screenshot: "reading--history-tab"
- Click "Summary" tab
- Verify Summary panel visible again

**Test 3: `submit reading with question text and Persian keyboard`**

- Seed profile, select it
- Type a question in the textarea: "What does today hold?"
- Click the Persian keyboard toggle button (`aria-label` matching `t("oracle.keyboard_toggle")`)
- Verify `PersianKeyboard` component appears below textarea
- Click a Persian character button (e.g., button with text "ا" or "ب")
- Verify the character appends to the textarea value
- Close keyboard (click close button matching `t("oracle.keyboard_close")`)
- Screenshot: "reading--question-with-keyboard"
- Click "Submit Reading"
- Wait for results
- Verify results section shows data
- Screenshot: "reading--question-results"

**Test 4: `multi-user selection and reading`**

- Seed 3 profiles via `seedMultipleProfiles(page, 3)`
- Navigate to `/oracle`
- Select first profile as primary user from dropdown
- Verify "Secondary Users" section appears (from `MultiUserSelector.tsx` line 148)
- Verify primary user appears as `UserChip` with `isPrimary` badge
- Click "+ Add User" button to show secondary dropdown
- Select second profile from secondary dropdown
- Verify second profile appears as a `UserChip`
- Click "+ Add User" again, select third profile
- Verify 3 total chips visible (1 primary + 2 secondary)
- Screenshot: "reading--multi-user-selected"
- Submit reading
- Wait for results
- Screenshot: "reading--multi-user-results"

**Test 5: `no profile selected shows guidance message`**

- Navigate to `/oracle` without selecting any profile
- Verify consultation section shows: "Select a profile to begin readings." (from `Oracle.tsx` line 148: `t("oracle.select_to_begin")`)
- Verify no "Submit Reading" button is present (form only renders when `primaryUser` is truthy)
- Screenshot: "reading--no-profile-guidance"

**Checkpoint:**

- [ ] `reading.spec.ts` has 5 test cases
- [ ] Tests cover: single reading, tab switching (ARIA), question with keyboard, multi-user, empty state
- [ ] All tests use seeded profiles via API (not manual form filling) for speed
- [ ] Each test captures at least 1 screenshot
- Verify: `cd frontend && npx playwright test e2e/reading.spec.ts --list` — lists 5 tests

STOP if checkpoint fails

---

### Phase 5: History & Settings Tests — `history.spec.ts` + `settings.spec.ts` (~75 min)

**Tasks — `history.spec.ts` (3 tests):**

Create `frontend/e2e/history.spec.ts`. Tests use `beforeEach(login)` and `afterEach(cleanupTestUsers)`.

**Test 1: `reading history displays past readings`**

- Seed profile, select it, submit a reading via the consultation form (to create history)
- Click the "History" tab in `ReadingResults`
- Verify at least 1 history item appears (from `ReadingHistory.tsx` line 74: `data.readings.map(...)`)
- Verify each item shows: sign_type badge (`text-[10px]` span), truncated text, and date (`toLocaleDateString()`)
- Verify count text: "N readings" from `t("oracle.history_count", { count: data.total })`
- Screenshot: "history--readings-listed"

**Test 2: `history filter chips work`**

- Navigate to History tab (with readings present)
- Verify 4 filter chip buttons visible with text: "All", "Readings", "Questions", "Names" (from `ReadingHistory.tsx` lines 22-26)
- Verify "All" chip has active styling (`bg-nps-oracle-accent text-nps-bg`)
- Click "Readings" chip
- Verify "Readings" chip becomes active, "All" chip loses active styling
- Click "All" chip
- Verify "All" becomes active again
- Screenshot: "history--filter-active"

**Test 3: `expand and collapse history item`**

- Navigate to History tab with readings present
- Click on the first history item row button
- Verify expanded content appears below the item (border-t section from `ReadingHistory.tsx` line 100)
- Verify expanded section contains either `ai_interpretation` text or `reading_result` JSON
- Screenshot: "history--expanded-reading"
- Click the same item again
- Verify expanded content is hidden (toggle via `expandedId` state)

---

**Tasks — `settings.spec.ts` (4 tests):**

Create `frontend/e2e/settings.spec.ts`. Tests use `beforeEach(login)`.

**Test 1: `language toggle switches to Persian and activates RTL`**

- Navigate to `/oracle` (richest translatable content)
- Verify initial state: `document.documentElement.dir` is `"ltr"` (or absent), `lang` is `"en"`
- Locate LanguageToggle button (contains "EN" and "FA" spans from `LanguageToggle.tsx`)
- Verify EN span has bold class (`text-nps-oracle-accent font-bold`), FA span has dim class
- Screenshot: "settings--english-mode"
- Click the toggle
- Verify `document.documentElement.dir` changes to `"rtl"` (from `App.tsx` line 17)
- Verify `document.documentElement.lang` changes to `"fa"` (from `App.tsx` line 18)
- Verify FA span now has bold class, EN span has dim class
- Verify sidebar nav labels changed to Persian text
- Screenshot: "settings--persian-mode-rtl"

**Test 2: `RTL layout flips sidebar border correctly`**

- Switch to Persian via `switchToFarsi(page)` fixture
- Inspect sidebar `nav` element (from `Layout.tsx` line 20):
  - In LTR: has `border-r` class (right border)
  - In RTL: `rtl:border-r-0` removes right border, `rtl:border-l` adds left border
- Verify the computed border style has changed sides
- Screenshot: "settings--rtl-sidebar-border"

**Test 3: `language persists across navigation`**

- Switch to Persian on `/oracle`
- Click Settings nav link -> navigate to `/settings`
- Verify `document.documentElement.dir` is still `"rtl"`
- Click Dashboard nav link -> navigate to `/dashboard`
- Verify `document.documentElement.dir` is still `"rtl"`
- Switch back to English via `switchToEnglish(page)` fixture
- Verify `dir` returns to `"ltr"`
- Screenshot: "settings--language-persists"

**Test 4: `settings page renders with expected sections`**

- Navigate to `/settings`
- Verify heading "Settings" is visible
- Verify the placeholder card contains text: "Settings management connects to the API service." (from `Settings.tsx` line 20-22)
- Screenshot: "settings--page-rendered"
- Note: Full settings controls (language selector, theme, Telegram) are stubs — this test verifies the page loads without errors. More detailed settings tests added after Sessions 32+.

**Checkpoint:**

- [ ] `history.spec.ts` has 3 test cases
- [ ] `settings.spec.ts` has 4 test cases
- [ ] Language toggle tests verify `dir`, `lang`, and visual class changes on the toggle spans
- [ ] History tests verify filter chips, expansion toggle, and reading list with count
- [ ] Each test captures at least 1 screenshot
- Verify:
  ```bash
  cd frontend && \
  npx playwright test e2e/history.spec.ts --list && \
  npx playwright test e2e/settings.spec.ts --list
  # Should list 3 + 4 = 7 tests
  ```

STOP if checkpoint fails

---

### Phase 6: Responsive Tests — `responsive.spec.ts` (~45 min)

**Tasks:**

Create `frontend/e2e/responsive.spec.ts` with explicit `375x812` viewport override.

```typescript
test.use({ viewport: { width: 375, height: 812 } });
```

All tests use `beforeEach(login)` and `afterEach(cleanupTestUsers)`.

**Test 1: `app loads at mobile viewport without overflow`**

- Navigate to `/dashboard`
- Verify page loads (Dashboard heading visible)
- Verify no horizontal overflow: `document.documentElement.scrollWidth <= window.innerWidth`
- Check sidebar behavior: either visible but narrower, collapsed behind a hamburger menu, or scrollable
- Screenshot: "responsive--mobile-dashboard"

**Test 2: `oracle page usable at mobile viewport`**

- Seed profile via API
- Navigate to `/oracle`
- Verify no horizontal scrollbar
- Verify primary user dropdown is visible and interactive (click to open)
- Select the seeded profile
- Verify consultation form renders within viewport bounds
- Verify all form elements (textarea, sign selector, submit button) are reachable by scrolling
- Screenshot: "responsive--mobile-oracle"

**Test 3: `profile form modal fits mobile screen`**

- Navigate to `/oracle`
- Click "+ Add New Profile"
- Verify modal form is visible within viewport (`max-w-md` from `UserForm.tsx` line 89 = 448px, but modal has `p-4` padding and `w-full` so it should compress)
- Verify form inputs are full-width and not clipped
- Fill in profile fields (name, birthday, mother_name)
- Verify submit and cancel buttons are visible (may need scroll in modal via `max-h-[90vh] overflow-y-auto`)
- Screenshot: "responsive--mobile-profile-form"

**Test 4: `reading results render at mobile viewport`**

- Seed profile, select, submit a reading
- Verify results section renders within viewport
- Verify tab buttons (Summary, Details, History) are visible and large enough to tap
- Click each tab — verify content appears without overflow
- Screenshot: "responsive--mobile-reading-results"

**Test 5: `RTL mode at mobile viewport`**

- Switch to Persian via `switchToFarsi(page)`
- Verify `dir="rtl"` active
- Navigate to `/oracle`
- Verify content flows right-to-left
- Verify no horizontal scrollbar: `document.documentElement.scrollWidth <= window.innerWidth`
- Screenshot: "responsive--mobile-rtl-oracle"

**Checkpoint:**

- [ ] `responsive.spec.ts` has 5 test cases
- [ ] All tests use `viewport: { width: 375, height: 812 }`
- [ ] Tests check for no horizontal overflow via `scrollWidth` comparison
- [ ] RTL + mobile combination tested
- [ ] Each test captures at least 1 screenshot
- Verify: `cd frontend && npx playwright test e2e/responsive.spec.ts --list` — lists 5 tests

STOP if checkpoint fails

---

### Phase 7: Full Suite Execution & Screenshot Verification (~45 min)

**Tasks:**

1. Run full E2E suite against `chromium` project:

   ```bash
   cd frontend && npx playwright test --project=chromium --reporter=list
   ```

2. Fix any failing tests iteratively:
   - **Selector mismatches** — update locators to match actual rendered DOM (use `npx playwright test --headed --debug` for inspection)
   - **Timing issues** — replace any `waitForTimeout()` with proper `expect(locator).toBeVisible()` assertions or `waitForLoadState("networkidle")`
   - **API unavailable** — ensure tests that need the API server skip gracefully with clear error if API is down
   - **Auth flow differences** — the `login()` helper handles both auth-gated and non-gated scenarios

3. Run responsive tests against mobile project:

   ```bash
   cd frontend && npx playwright test e2e/responsive.spec.ts --project=mobile-chrome --reporter=list
   ```

4. Verify screenshots captured:

   ```bash
   ls -la frontend/e2e-screenshots/ | wc -l
   # Should be 20+ screenshot files
   ```

5. Generate HTML report:

   ```bash
   cd frontend && npx playwright show-report e2e-report
   ```

6. Verify existing `oracle.spec.ts` still passes (no regressions):

   ```bash
   cd frontend && npx playwright test e2e/oracle.spec.ts --project=chromium --reporter=list
   ```

7. Run TypeScript check on all test files:
   ```bash
   cd frontend && npx tsc --noEmit
   ```

**Checkpoint:**

- [ ] All 26+ tests pass on chromium (or skip gracefully if API unavailable)
- [ ] Responsive tests pass on mobile-chrome
- [ ] 20+ screenshots captured in `e2e-screenshots/`
- [ ] HTML report generated in `e2e-report/`
- [ ] Existing `oracle.spec.ts` tests still pass (no regressions)
- [ ] No TypeScript compilation errors
- Verify:
  ```bash
  cd frontend && \
  npx playwright test --project=chromium --reporter=list 2>&1 | tail -5 && \
  echo "FULL SUITE VERIFIED"
  ```

STOP if checkpoint fails

---

## TESTS TO WRITE

### `frontend/e2e/auth.spec.ts` (4 tests)

| Test Function                            | Verifies                                                      |
| ---------------------------------------- | ------------------------------------------------------------- |
| `app loads and redirects to dashboard`   | `/` -> `/dashboard` redirect, heading visible, NPS title      |
| `sidebar shows all navigation links`     | 6 NavLinks present, LanguageToggle visible in header          |
| `navigate to each page via sidebar`      | Click each link -> URL changes, heading visible, active class |
| `direct URL access works for all routes` | Goto each route directly -> page loads without error          |

### `frontend/e2e/profile.spec.ts` (5 tests)

| Test Function                                       | Verifies                                                  |
| --------------------------------------------------- | --------------------------------------------------------- |
| `create new profile via form`                       | Modal opens, fields fill, submit creates user in dropdown |
| `form validation rejects empty required fields`     | 3 validation errors for name, birthday, mother_name       |
| `edit existing profile`                             | Pre-filled form opens, field change saves, UI updates     |
| `delete profile with two-step confirmation`         | Delete -> Confirm Delete -> user removed from dropdown    |
| `profile selection persists across page navigation` | localStorage stores selected user, survives route changes |

### `frontend/e2e/reading.spec.ts` (5 tests)

| Test Function                                            | Verifies                                                         |
| -------------------------------------------------------- | ---------------------------------------------------------------- |
| `select user and submit time reading`                    | Full flow: select -> time sign -> submit -> results in Summary   |
| `reading results tab switching with ARIA`                | Tab buttons toggle correctly, `aria-selected` + panel visibility |
| `submit reading with question text and Persian keyboard` | Question input + keyboard chars -> submit -> results             |
| `multi-user selection and reading`                       | Primary + 2 secondary chips -> submit -> multi-user results      |
| `no profile selected shows guidance message`             | Empty state message visible, no submit button                    |

### `frontend/e2e/history.spec.ts` (3 tests)

| Test Function                            | Verifies                                                   |
| ---------------------------------------- | ---------------------------------------------------------- |
| `reading history displays past readings` | History tab shows items with type badge, text, date, count |
| `history filter chips work`              | Chip click toggles active styling, filter selection works  |
| `expand and collapse history item`       | Click expands details, click again collapses (toggle)      |

### `frontend/e2e/settings.spec.ts` (4 tests)

| Test Function                                           | Verifies                                                |
| ------------------------------------------------------- | ------------------------------------------------------- |
| `language toggle switches to Persian and activates RTL` | `dir="rtl"`, `lang="fa"`, toggle span classes flip      |
| `RTL layout flips sidebar border correctly`             | Sidebar border moves from right to left in RTL          |
| `language persists across navigation`                   | RTL/LTR state survives page route changes               |
| `settings page renders with expected sections`          | Settings page loads, heading + placeholder card visible |

### `frontend/e2e/responsive.spec.ts` (5 tests)

| Test Function                                   | Verifies                                                  |
| ----------------------------------------------- | --------------------------------------------------------- |
| `app loads at mobile viewport without overflow` | Dashboard renders, no horizontal scrollbar at 375px       |
| `oracle page usable at mobile viewport`         | Dropdown, form, submit all accessible at 375px            |
| `profile form modal fits mobile screen`         | Modal visible, inputs full-width, buttons reachable       |
| `reading results render at mobile viewport`     | Tabs and results fit within 375px viewport bounds         |
| `RTL mode at mobile viewport`                   | RTL + 375px combination renders without horizontal scroll |

**Total: 26 test cases across 6 spec files**

---

## ACCEPTANCE CRITERIA

- [ ] 6 new E2E spec files created in `frontend/e2e/`: auth, profile, reading, history, settings, responsive
- [ ] `fixtures.ts` updated with 8+ new helpers (login, seedTestProfile, seedMultipleProfiles, takeStepScreenshot, waitForApiReady, authHeaders, switchToFarsi, switchToEnglish)
- [ ] `playwright.config.ts` updated: mobile project, screenshot "on", HTML report, 60s timeout
- [ ] `.gitignore` updated with e2e output directories
- [ ] All 26 tests pass on chromium project (or skip gracefully when API unavailable)
- [ ] At least 20 screenshots captured in `e2e-screenshots/`
- [ ] No TypeScript compilation errors: `cd frontend && npx tsc --noEmit`
- [ ] Auth tests handle both login-page and no-login-page scenarios adaptively
- [ ] Profile tests cover full CRUD lifecycle + form validation + localStorage persistence
- [ ] Reading tests cover time reading, question with Persian keyboard, multi-user, tab switching, empty state
- [ ] History tests verify filter chips, item expansion/collapse, and reading count display
- [ ] Settings tests verify EN/FA toggle, `dir`/`lang` attribute changes, sidebar border flip, language persistence
- [ ] Responsive tests verify no horizontal overflow at 375px, forms fit, RTL works at mobile
- [ ] Existing `oracle.spec.ts` (8 tests) still passes — no regressions
- Verify all:
  ```bash
  cd frontend && \
  test -f e2e/auth.spec.ts && \
  test -f e2e/profile.spec.ts && \
  test -f e2e/reading.spec.ts && \
  test -f e2e/history.spec.ts && \
  test -f e2e/settings.spec.ts && \
  test -f e2e/responsive.spec.ts && \
  npx playwright test --project=chromium --reporter=list 2>&1 | grep -E "passed|failed" && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                           | Expected Behavior                                                                   |
| -------------------------------------------------- | ----------------------------------------------------------------------------------- |
| API server not running during E2E tests            | Tests that call API fail with clear timeout message, not hang indefinitely          |
| Frontend dev server not running                    | Playwright `webServer` config auto-starts Vite; reuses existing if port busy        |
| Login page not implemented yet (Session 2 pending) | `login()` fixture detects absence, falls back to direct localStorage token inject   |
| Settings page is still a stub                      | `settings.spec.ts` Test 4 verifies stub renders, not full functionality             |
| No readings in history (fresh user)                | History tests seed readings by submitting via form before testing history tab       |
| Profile dropdown has no users on fresh DB          | Tests seed profiles via API before testing UI selector interactions                 |
| Mobile viewport causes sidebar to overflow         | Test detects and reports overflow; responsive test documents behavior               |
| Screenshot directory does not exist                | `takeStepScreenshot()` creates directory with `mkdirSync({ recursive: true })`      |
| Stale localStorage from previous test run          | `login()` fixture navigates fresh; `afterEach` cleans up test users                 |
| Cleanup fails (API error during user deletion)     | `cleanupTestUsers()` uses `E2E_` prefix search; orphaned users cleaned on next run  |
| Network timeout waiting for reading submission     | 60-second test timeout catches; Playwright shows clear timeout error message        |
| RTL locale file missing translation keys           | Tests verify `dir` attribute change, not specific translated text strings           |
| Tab switching has CSS animation delays             | Tests wait for `aria-selected` attribute changes, not CSS transition completion     |
| Keyboard character click not appending to textarea | Test asserts `textarea.inputValue()` changed; failure caught with descriptive error |

---

## HANDOFF

**Created:**

- `frontend/e2e/auth.spec.ts` — 4 authentication and navigation tests
- `frontend/e2e/profile.spec.ts` — 5 Oracle profile CRUD tests
- `frontend/e2e/reading.spec.ts` — 5 reading submission and results tests
- `frontend/e2e/history.spec.ts` — 3 reading history browsing tests
- `frontend/e2e/settings.spec.ts` — 4 locale/RTL/settings tests
- `frontend/e2e/responsive.spec.ts` — 5 mobile viewport tests

**Modified:**

- `frontend/e2e/fixtures.ts` — Added 8 new helper functions (login, seedTestProfile, seedMultipleProfiles, takeStepScreenshot, waitForApiReady, authHeaders, switchToFarsi, switchToEnglish)
- `frontend/playwright.config.ts` — Added mobile project, screenshot config, HTML report, increased timeouts
- `frontend/.gitignore` — Added e2e-screenshots/, e2e-results/, e2e-report/

**Next session needs:**

- **Session 44 (Performance Optimization)** depends on:
  - All 26 E2E tests from this session proving frontend flows work end-to-end before any optimization begins
  - Screenshot baselines from this session for visual regression comparison after performance changes
  - The `e2e-report/` HTML report serves as the pre-optimization quality baseline
  - Playwright trace data (`trace: "on-first-retry"`) supplements API-level timing from Sessions 41-42
  - E2E tests serve as the regression safety net — any optimization that breaks a test must be reverted
- **Session 45 (Deployment)** depends on:
  - All E2E tests passing in CI environment (this session configures CI-aware settings: `forbidOnly`, `retries`, `workers`)
  - The `mobile-chrome` project ensures responsive quality before production deploy
  - Screenshot artifacts from E2E runs stored as deployment quality evidence
  - The full Playwright test suite becomes part of the CI/CD gate: no deploy if E2E tests fail
