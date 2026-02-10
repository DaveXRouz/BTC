# SESSION 22 SPEC — Dashboard Page

**Block:** Frontend Core (Sessions 19-25)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium-High
**Dependencies:** Sessions 17 (reading history API), 19 (layout & navigation), 20 (Oracle main page), 21 (reading results display)

---

## TL;DR

- Rewrite `Dashboard.tsx` from scanner-centric stub to Oracle-centric homepage with welcome banner, daily reading, recent readings, stats, and quick actions
- Create 5 new dashboard components: `WelcomeBanner`, `DailyReadingCard`, `RecentReadings`, `StatsCards`, `QuickActions`
- Add new API endpoint `GET /oracle/stats` for aggregated reading statistics
- Add new `useDashboard` hook for data fetching (stats, recent readings, daily reading)
- Full bilingual support (EN/FA) with Persian numerals and RTL layout

---

## OBJECTIVES

1. Replace the current scanner-stats-based `Dashboard.tsx` with an Oracle-focused dashboard
2. Display a personalized welcome banner with user name and today's date (Gregorian + Jalali)
3. Show a daily reading card that either displays today's auto-reading or offers a "Generate" button
4. Display the 5 most recent readings as clickable cards with type badge, date, and summary
5. Show 4 statistics cards: total readings, average confidence, most used reading type, reading streak (consecutive days)
6. Provide quick action buttons that navigate to Oracle page with pre-selected reading type
7. Add a moon phase widget showing current phase with emoji and name
8. Create API endpoint `GET /oracle/stats` returning aggregated reading statistics
9. Ensure all dashboard text is translated in both EN and FA locales
10. Ensure RTL layout, Persian numerals, and Jalali dates render correctly in FA locale

---

## PREREQUISITES

- [ ] `frontend/src/components/Layout.tsx` exists with sidebar navigation and `<Outlet />`
  - Verification: `test -f frontend/src/components/Layout.tsx && echo "OK"`
- [ ] `frontend/src/pages/Dashboard.tsx` exists (current stub)
  - Verification: `test -f frontend/src/pages/Dashboard.tsx && echo "OK"`
- [ ] React Router is configured with `/dashboard` route
  - Verification: `grep -q "dashboard" frontend/src/App.tsx && echo "OK"`
- [ ] `@tanstack/react-query` is available for data fetching
  - Verification: `grep -q "react-query" frontend/package.json && echo "OK"`
- [ ] i18n config exists with EN/FA locales
  - Verification: `test -f frontend/src/i18n/config.ts && test -f frontend/src/locales/en.json && test -f frontend/src/locales/fa.json && echo "OK"`
- [ ] API oracle router exists at `api/app/routers/oracle.py`
  - Verification: `test -f api/app/routers/oracle.py && echo "OK"`
- [ ] Oracle reading service exists for querying reading data
  - Verification: `grep -q "OracleReadingService" api/app/services/oracle_reading.py && echo "OK"`
- [ ] `frontend/src/services/api.ts` has `oracle.history()` and `oracle.daily()` methods
  - Verification: `grep -q "history" frontend/src/services/api.ts && grep -q "daily" frontend/src/services/api.ts && echo "OK"`
- [ ] Tailwind config has NPS color tokens (nps-bg, nps-text, nps-gold, etc.)
  - Verification: `grep -q "npsColors" frontend/tailwind.config.ts && echo "OK"`

---

## FILES TO CREATE

- `frontend/src/components/dashboard/WelcomeBanner.tsx` — Welcome greeting with user name, date, and moon phase widget
- `frontend/src/components/dashboard/DailyReadingCard.tsx` — Today's reading display or generate button
- `frontend/src/components/dashboard/RecentReadings.tsx` — Card grid of last 5 readings
- `frontend/src/components/dashboard/StatsCards.tsx` — 4 statistics cards with counters
- `frontend/src/components/dashboard/QuickActions.tsx` — Quick action buttons for common reading types
- `frontend/src/components/dashboard/MoonPhaseWidget.tsx` — Current moon phase display
- `frontend/src/hooks/useDashboard.ts` — React Query hooks for dashboard data (stats, recent, daily)
- `frontend/src/components/dashboard/__tests__/WelcomeBanner.test.tsx` — Tests for WelcomeBanner
- `frontend/src/components/dashboard/__tests__/DailyReadingCard.test.tsx` — Tests for DailyReadingCard
- `frontend/src/components/dashboard/__tests__/RecentReadings.test.tsx` — Tests for RecentReadings
- `frontend/src/components/dashboard/__tests__/StatsCards.test.tsx` — Tests for StatsCards
- `frontend/src/components/dashboard/__tests__/QuickActions.test.tsx` — Tests for QuickActions
- `frontend/src/components/dashboard/__tests__/MoonPhaseWidget.test.tsx` — Tests for MoonPhaseWidget
- `frontend/src/pages/__tests__/Dashboard.test.tsx` — Integration test for full Dashboard page
- `api/app/models/dashboard.py` — Pydantic models for dashboard stats response
- `api/tests/test_dashboard_stats.py` — Tests for the dashboard stats endpoint

---

## FILES TO MODIFY

- `frontend/src/pages/Dashboard.tsx` — REWRITE from scanner stub to Oracle dashboard
- `frontend/src/components/StatsCard.tsx` — ENHANCE with optional icon, trend indicator, and locale-aware number formatting
- `frontend/src/services/api.ts` — ADD `dashboard.stats()` method
- `frontend/src/types/index.ts` — ADD `DashboardStats`, `DailyReading`, and `MoonPhase` interfaces
- `frontend/src/locales/en.json` — ADD `dashboard.*` translation keys (replace scanner-centric keys)
- `frontend/src/locales/fa.json` — ADD `dashboard.*` Persian translations
- `api/app/routers/oracle.py` — ADD `GET /stats` endpoint for aggregated reading statistics

---

## FILES TO DELETE

None

---

## IMPLEMENTATION PHASES

### Phase 1: API — Dashboard Stats Endpoint (30 minutes)

**Tasks:**

1. Create `api/app/models/dashboard.py` with Pydantic model `DashboardStatsResponse`:

   ```python
   class DashboardStatsResponse(BaseModel):
       total_readings: int
       readings_by_type: dict[str, int]  # {"time": 12, "name": 5, "question": 8}
       average_confidence: float | None
       most_used_type: str | None
       streak_days: int  # consecutive days with at least one reading
       readings_today: int
       readings_this_week: int
       readings_this_month: int
   ```

2. Add `GET /stats` endpoint in `api/app/routers/oracle.py`:
   - Query `oracle_readings` table for aggregated counts
   - Calculate streak by finding consecutive days with readings backwards from today
   - Calculate average confidence from `reading_result->>'confidence'` JSONB field
   - Requires `oracle:read` scope

3. Write `api/tests/test_dashboard_stats.py` with tests for:
   - Empty database returns zero stats
   - Stats reflect inserted readings correctly
   - Streak calculation is accurate
   - Confidence averaging works with null values

**Code Pattern — Stats endpoint signature:**

```python
@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_reading_stats(
    _user: dict = Depends(get_current_user),
    svc: OracleReadingService = Depends(get_oracle_reading_service),
) -> DashboardStatsResponse:
    ...
```

**Checkpoint:**

- [ ] `cd api && python3 -m pytest tests/test_dashboard_stats.py -v` passes
- Verify: `cd api && python3 -m pytest tests/test_dashboard_stats.py -v`

---

### Phase 2: Frontend Types & API Client (20 minutes)

**Tasks:**

1. Add TypeScript interfaces to `frontend/src/types/index.ts`:

   ```typescript
   export interface DashboardStats {
     total_readings: number;
     readings_by_type: Record<string, number>;
     average_confidence: number | null;
     most_used_type: string | null;
     streak_days: number;
     readings_today: number;
     readings_this_week: number;
     readings_this_month: number;
   }

   export interface MoonPhaseInfo {
     phase_name: string;
     illumination: number;
     emoji: string;
     age_days: number;
   }
   ```

2. Add `dashboard` section to `frontend/src/services/api.ts`:

   ```typescript
   export const dashboard = {
     stats: () => request<DashboardStats>("/oracle/stats"),
   };
   ```

3. Create `frontend/src/hooks/useDashboard.ts` with React Query hooks:
   - `useDashboardStats()` — fetches `GET /oracle/stats`, refetch every 60s
   - `useRecentReadings()` — fetches `oracle.history({ limit: 5 })`, reuses existing API
   - `useDailyReading()` — fetches `oracle.daily()`, reuses existing API

**Code Pattern — useDashboard hook:**

```typescript
import { useQuery } from "@tanstack/react-query";
import { dashboard, oracle } from "@/services/api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboardStats"],
    queryFn: () => dashboard.stats(),
    refetchInterval: 60_000,
  });
}

export function useRecentReadings(limit = 5) {
  return useQuery({
    queryKey: ["recentReadings", limit],
    queryFn: () => oracle.history({ limit }),
  });
}

export function useDailyReading(date?: string) {
  return useQuery({
    queryKey: ["dailyReading", date],
    queryFn: () => oracle.daily(date),
  });
}
```

**Checkpoint:**

- [ ] `frontend/src/types/index.ts` compiles without errors
- [ ] `frontend/src/hooks/useDashboard.ts` compiles without errors
- Verify: `cd frontend && npx tsc --noEmit --pretty 2>&1 | head -20`

---

### Phase 3: WelcomeBanner & MoonPhaseWidget Components (40 minutes)

**Tasks:**

1. Create `frontend/src/components/dashboard/MoonPhaseWidget.tsx`:
   - Accept `moonData` prop (from daily reading API) or show loading skeleton
   - Display moon emoji, phase name, and illumination percentage
   - Translate phase name via i18n
   - Compact inline widget (not a full card)

2. Create `frontend/src/components/dashboard/WelcomeBanner.tsx`:
   - Display greeting based on time of day: "Good morning" / "Good afternoon" / "Good evening"
   - Show user name (from auth context or localStorage) or generic "Explorer"
   - Show today's date: Gregorian format in EN, Jalali format in FA
   - Include `MoonPhaseWidget` inline on the right side of the banner
   - Use `nps-oracle-bg` background with subtle gradient
   - RTL-aware layout (greeting on right, moon on left in FA)

3. Write tests:
   - `WelcomeBanner.test.tsx`: renders greeting, shows date, shows moon widget
   - `MoonPhaseWidget.test.tsx`: renders phase name, emoji, illumination

**Code Pattern — WelcomeBanner interface:**

```typescript
interface WelcomeBannerProps {
  userName?: string;
  moonData?: MoonPhaseInfo | null;
  isLoading?: boolean;
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/WelcomeBanner.test.tsx` passes
- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/MoonPhaseWidget.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/dashboard/__tests__/WelcomeBanner.test.tsx src/components/dashboard/__tests__/MoonPhaseWidget.test.tsx`

---

### Phase 4: DailyReadingCard Component (30 minutes)

**Tasks:**

1. Create `frontend/src/components/dashboard/DailyReadingCard.tsx`:
   - If daily reading exists for today: show summary, FC60 stamp snippet, confidence badge
   - If no daily reading: show "Generate Today's Reading" button with pulsing green animation
   - Button navigates to Oracle page with `?type=daily` query param (handled by Session 20)
   - Loading state: skeleton card with shimmer
   - Error state: graceful message with retry button
   - Card uses `nps-bg-card` with `nps-oracle-border` accent

2. Write `DailyReadingCard.test.tsx`:
   - Renders reading summary when data provided
   - Shows generate button when no reading exists
   - Shows loading skeleton during fetch
   - Generate button navigates to Oracle page
   - Error state shows retry button

**Code Pattern — DailyReadingCard interface:**

```typescript
interface DailyReadingCardProps {
  dailyReading?: DailyInsightResponse | null;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

interface DailyInsightResponse {
  date: string;
  summary: string;
  fc60_stamp?: string;
  moon_phase?: string;
  energy_level?: number;
  advice?: string[];
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/DailyReadingCard.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/dashboard/__tests__/DailyReadingCard.test.tsx`

---

### Phase 5: StatsCards Component (30 minutes)

**Tasks:**

1. Enhance `frontend/src/components/StatsCard.tsx`:
   - Add optional `icon` prop (emoji or component)
   - Add optional `trend` prop (`{ direction: "up" | "down" | "flat"; value: string }`)
   - Add locale-aware number formatting using `Intl.NumberFormat` (Persian numerals in FA)
   - Keep backward-compatible (all new props optional)

2. Create `frontend/src/components/dashboard/StatsCards.tsx`:
   - Accept `stats: DashboardStats | undefined` and `isLoading: boolean` props
   - Render 4 `StatsCard` components in a responsive grid:
     - **Total Readings:** `stats.total_readings` with book icon
     - **Avg Confidence:** `stats.average_confidence` formatted as percentage with chart icon
     - **Most Used Type:** `stats.most_used_type` with star icon, translated via i18n
     - **Streak:** `stats.streak_days` days with fire icon
   - Loading state: 4 skeleton cards
   - Use `nps-success` for positive trends, `nps-warning` for declining

3. Write `StatsCards.test.tsx`:
   - Renders all 4 stat cards with correct values
   - Shows loading skeletons when isLoading=true
   - Handles null/zero stats gracefully
   - Persian numerals render in FA locale
   - Formats confidence as percentage

**Code Pattern — StatsCards interface:**

```typescript
interface StatsCardsProps {
  stats?: DashboardStats;
  isLoading: boolean;
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/StatsCards.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/dashboard/__tests__/StatsCards.test.tsx`

---

### Phase 6: RecentReadings Component (40 minutes)

**Tasks:**

1. Create `frontend/src/components/dashboard/RecentReadings.tsx`:
   - Accept `readings: StoredReading[]`, `isLoading: boolean`, `isError: boolean` props
   - Render up to 5 readings as horizontal scrollable card row (or 2-column grid on desktop)
   - Each card shows:
     - Type badge (color-coded): time=blue, name=purple, question=gold
     - Date (Gregorian in EN, Jalali in FA)
     - Summary text (truncated to 2 lines)
     - Confidence badge (if available)
   - Click on card navigates to `/oracle?reading=<id>` (reading detail view)
   - Empty state: "No readings yet. Start your first reading!" with CTA button
   - Section header: "Recent Readings" with "View All" link to reading history

2. Write `RecentReadings.test.tsx`:
   - Renders correct number of reading cards
   - Each card shows type, date, summary
   - Click navigates to reading detail
   - Empty state renders CTA
   - Loading state shows skeleton cards
   - Type badges have correct colors

**Code Pattern — RecentReadings interface:**

```typescript
interface RecentReadingsProps {
  readings: StoredReading[];
  isLoading: boolean;
  isError: boolean;
  total: number;
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/RecentReadings.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/dashboard/__tests__/RecentReadings.test.tsx`

---

### Phase 7: QuickActions Component (20 minutes)

**Tasks:**

1. Create `frontend/src/components/dashboard/QuickActions.tsx`:
   - Render 3 action buttons in a row:
     - **Time Reading** — navigates to `/oracle?type=time` — clock icon — `nps-oracle-accent` color
     - **Ask a Question** — navigates to `/oracle?type=question` — question mark icon — `nps-gold` color
     - **Name Reading** — navigates to `/oracle?type=name` — text icon — `nps-purple` color
   - Each button: icon + label, subtle hover animation, rounded card style
   - Use `react-router-dom` `useNavigate` for navigation
   - All labels translated via i18n

2. Write `QuickActions.test.tsx`:
   - All 3 buttons render with correct labels
   - Click triggers navigation to correct Oracle page URL
   - Labels are translatable (verify i18n key usage)

**Code Pattern — QuickActions (no special props needed):**

```typescript
export function QuickActions(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  // ...
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/components/dashboard/__tests__/QuickActions.test.tsx` passes
- Verify: `cd frontend && npx vitest run src/components/dashboard/__tests__/QuickActions.test.tsx`

---

### Phase 8: Dashboard Page Assembly (30 minutes)

**Tasks:**

1. Rewrite `frontend/src/pages/Dashboard.tsx`:
   - Import all 5 dashboard components + hooks
   - Use `useDashboardStats()`, `useRecentReadings()`, `useDailyReading()` hooks
   - Layout (top to bottom):
     1. `WelcomeBanner` — full width
     2. `DailyReadingCard` — full width
     3. `StatsCards` — full width (4-column grid)
     4. `RecentReadings` — full width
     5. `QuickActions` — full width
   - Pass loading/error states from hooks to components
   - Page wrapper: `<div className="space-y-6">` (matches existing pattern)

2. Write `frontend/src/pages/__tests__/Dashboard.test.tsx`:
   - Renders all 5 sections
   - Shows loading state initially
   - Mock API calls and verify data flows to components
   - Verify page title uses i18n

**Code Pattern — Dashboard page structure:**

```typescript
export function Dashboard() {
  const { t } = useTranslation();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: recent, isLoading: recentLoading } = useRecentReadings();
  const { data: daily, isLoading: dailyLoading, isError: dailyError, refetch: retryDaily } = useDailyReading();

  return (
    <div className="space-y-6">
      <WelcomeBanner userName={...} moonData={daily?.moon_phase} isLoading={dailyLoading} />
      <DailyReadingCard dailyReading={daily} isLoading={dailyLoading} isError={dailyError} onRetry={retryDaily} />
      <StatsCards stats={stats} isLoading={statsLoading} />
      <RecentReadings readings={recent?.readings ?? []} isLoading={recentLoading} isError={false} total={recent?.total ?? 0} />
      <QuickActions />
    </div>
  );
}
```

**Checkpoint:**

- [ ] `cd frontend && npx vitest run src/pages/__tests__/Dashboard.test.tsx` passes
- [ ] Dashboard renders in dev mode without errors
- Verify: `cd frontend && npx vitest run src/pages/__tests__/Dashboard.test.tsx`

---

### Phase 9: Translations (20 minutes)

**Tasks:**

1. Update `frontend/src/locales/en.json` — replace scanner-centric `dashboard.*` keys with:

   ```json
   "dashboard": {
     "title": "Dashboard",
     "welcome_morning": "Good morning",
     "welcome_afternoon": "Good afternoon",
     "welcome_evening": "Good evening",
     "welcome_user": "{{greeting}}, {{name}}",
     "welcome_explorer": "{{greeting}}, Explorer",
     "today_date": "Today is {{date}}",
     "daily_reading": "Today's Reading",
     "daily_generate": "Generate Today's Reading",
     "daily_no_reading": "No reading generated for today yet.",
     "daily_error": "Could not load daily reading.",
     "daily_retry": "Retry",
     "stats_total": "Total Readings",
     "stats_confidence": "Avg Confidence",
     "stats_most_used": "Most Used Type",
     "stats_streak": "Streak",
     "stats_streak_days": "{{count}} days",
     "recent_title": "Recent Readings",
     "recent_view_all": "View All",
     "recent_empty": "No readings yet. Start your first reading!",
     "recent_start": "Start Reading",
     "quick_actions": "Quick Actions",
     "quick_time": "Time Reading",
     "quick_question": "Ask a Question",
     "quick_name": "Name Reading",
     "type_time": "Time",
     "type_name": "Name",
     "type_question": "Question",
     "moon_phase": "Moon Phase",
     "moon_illumination": "{{percent}}% illuminated"
   }
   ```

2. Update `frontend/src/locales/fa.json` — add matching Persian translations:

   ```json
   "dashboard": {
     "title": "داشبورد",
     "welcome_morning": "صبح بخیر",
     "welcome_afternoon": "عصر بخیر",
     "welcome_evening": "شب بخیر",
     "welcome_user": "{{greeting}}، {{name}}",
     "welcome_explorer": "{{greeting}}، کاوشگر",
     "today_date": "امروز {{date}}",
     "daily_reading": "خوانش امروز",
     "daily_generate": "ایجاد خوانش امروز",
     "daily_no_reading": "هنوز خوانشی برای امروز ایجاد نشده.",
     "daily_error": "خطا در بارگذاری خوانش روزانه.",
     "daily_retry": "تلاش مجدد",
     "stats_total": "کل خوانش‌ها",
     "stats_confidence": "میانگین اطمینان",
     "stats_most_used": "پرکاربردترین نوع",
     "stats_streak": "روزهای متوالی",
     "stats_streak_days": "{{count}} روز",
     "recent_title": "خوانش‌های اخیر",
     "recent_view_all": "مشاهده همه",
     "recent_empty": "هنوز خوانشی وجود ندارد. اولین خوانش خود را شروع کنید!",
     "recent_start": "شروع خوانش",
     "quick_actions": "دسترسی سریع",
     "quick_time": "خوانش زمان",
     "quick_question": "پرسیدن سؤال",
     "quick_name": "خوانش نام",
     "type_time": "زمان",
     "type_name": "نام",
     "type_question": "سؤال",
     "moon_phase": "فاز ماه",
     "moon_illumination": "{{percent}}٪ روشنایی"
   }
   ```

3. Verify every key in `en.json` `dashboard.*` has a corresponding `fa.json` entry.

**Checkpoint:**

- [ ] `node -e "const en=require('./frontend/src/locales/en.json'); const fa=require('./frontend/src/locales/fa.json'); const enKeys=Object.keys(en.dashboard); const faKeys=Object.keys(fa.dashboard); const missing=enKeys.filter(k=>!faKeys.includes(k)); console.log(missing.length===0 ? 'OK' : 'MISSING: '+missing.join(', '))"` outputs "OK"
- Verify: Run the command above

---

### Phase 10: Final Verification (30 minutes)

**Tasks:**

1. Run all dashboard-related frontend tests:

   ```bash
   cd frontend && npx vitest run src/components/dashboard/ src/pages/__tests__/Dashboard.test.tsx
   ```

2. Run API tests for the stats endpoint:

   ```bash
   cd api && python3 -m pytest tests/test_dashboard_stats.py -v
   ```

3. Run TypeScript type check:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

4. Run linter:

   ```bash
   cd frontend && npx eslint src/pages/Dashboard.tsx src/components/dashboard/ src/hooks/useDashboard.ts --ext .ts,.tsx
   ```

5. Run formatter:

   ```bash
   cd frontend && npx prettier --write src/pages/Dashboard.tsx src/components/dashboard/ src/hooks/useDashboard.ts
   ```

6. Manual verification (if dev server available):
   - Navigate to `/dashboard`
   - Verify welcome banner shows with correct greeting
   - Verify stats cards show (0 values if no readings)
   - Toggle locale to FA — verify RTL flip, Persian text
   - Verify quick action buttons navigate to Oracle page

**Checkpoint:**

- [ ] All frontend tests pass: `cd frontend && npx vitest run`
- [ ] All API tests pass: `cd api && python3 -m pytest tests/ -v`
- [ ] TypeScript compiles: `cd frontend && npx tsc --noEmit`
- [ ] Lint passes: `cd frontend && npm run lint`
- Verify: `cd frontend && npx vitest run && npx tsc --noEmit && npm run lint`

---

## TESTS TO WRITE

### Frontend Component Tests

- `frontend/src/components/dashboard/__tests__/WelcomeBanner.test.tsx::renders_greeting_based_on_time` — Verifies morning/afternoon/evening greeting selection
- `frontend/src/components/dashboard/__tests__/WelcomeBanner.test.tsx::renders_user_name` — Verifies user name appears in banner
- `frontend/src/components/dashboard/__tests__/WelcomeBanner.test.tsx::renders_today_date` — Verifies today's date display
- `frontend/src/components/dashboard/__tests__/WelcomeBanner.test.tsx::renders_jalali_date_in_fa_locale` — Verifies Jalali date in Persian mode
- `frontend/src/components/dashboard/__tests__/MoonPhaseWidget.test.tsx::renders_moon_emoji_and_phase` — Verifies moon phase display
- `frontend/src/components/dashboard/__tests__/MoonPhaseWidget.test.tsx::renders_loading_skeleton` — Verifies loading state
- `frontend/src/components/dashboard/__tests__/DailyReadingCard.test.tsx::renders_reading_when_available` — Shows reading summary
- `frontend/src/components/dashboard/__tests__/DailyReadingCard.test.tsx::renders_generate_button_when_empty` — Shows CTA when no reading
- `frontend/src/components/dashboard/__tests__/DailyReadingCard.test.tsx::renders_error_with_retry` — Shows error state with retry
- `frontend/src/components/dashboard/__tests__/StatsCards.test.tsx::renders_four_stat_cards` — All 4 cards render
- `frontend/src/components/dashboard/__tests__/StatsCards.test.tsx::formats_confidence_as_percentage` — Confidence value formatting
- `frontend/src/components/dashboard/__tests__/StatsCards.test.tsx::handles_zero_stats` — Zero values don't crash
- `frontend/src/components/dashboard/__tests__/StatsCards.test.tsx::renders_persian_numerals_in_fa` — Persian number formatting
- `frontend/src/components/dashboard/__tests__/RecentReadings.test.tsx::renders_reading_cards` — Reading cards appear
- `frontend/src/components/dashboard/__tests__/RecentReadings.test.tsx::renders_type_badges` — Type badges with colors
- `frontend/src/components/dashboard/__tests__/RecentReadings.test.tsx::renders_empty_state` — Empty state CTA
- `frontend/src/components/dashboard/__tests__/RecentReadings.test.tsx::truncates_long_summaries` — Summary truncation
- `frontend/src/components/dashboard/__tests__/QuickActions.test.tsx::renders_three_action_buttons` — All 3 buttons render
- `frontend/src/components/dashboard/__tests__/QuickActions.test.tsx::navigates_to_oracle_with_type` — Navigation URLs correct
- `frontend/src/components/dashboard/__tests__/QuickActions.test.tsx::labels_use_i18n_keys` — Translation keys used

### Page Integration Tests

- `frontend/src/pages/__tests__/Dashboard.test.tsx::renders_all_sections` — All 5 dashboard sections present
- `frontend/src/pages/__tests__/Dashboard.test.tsx::shows_loading_states` — Loading skeletons appear initially
- `frontend/src/pages/__tests__/Dashboard.test.tsx::renders_with_mock_data` — Full render with mocked API data

### API Tests

- `api/tests/test_dashboard_stats.py::test_stats_empty_database` — Returns zeros when no readings exist
- `api/tests/test_dashboard_stats.py::test_stats_with_readings` — Returns correct counts after inserting readings
- `api/tests/test_dashboard_stats.py::test_stats_streak_calculation` — Streak counts consecutive days
- `api/tests/test_dashboard_stats.py::test_stats_confidence_average` — Average confidence handles nulls
- `api/tests/test_dashboard_stats.py::test_stats_requires_auth` — Endpoint requires `oracle:read` scope

---

## ACCEPTANCE CRITERIA

- [ ] Dashboard page loads and displays all 5 sections (welcome, daily, stats, recent, quick actions)
- [ ] Welcome banner shows correct time-of-day greeting
- [ ] Daily reading card either shows today's reading or a generate button
- [ ] Stats cards display accurate numbers (verified against API response)
- [ ] Recent readings show the 5 most recent with correct type badges and dates
- [ ] Quick action buttons navigate to Oracle page with correct type parameters
- [ ] Moon phase widget displays current phase data
- [ ] All text translates correctly when switching to FA locale
- [ ] RTL layout works in FA locale (greeting right-aligned, moon widget left-aligned)
- [ ] Persian numerals display in stats cards in FA locale
- [ ] Jalali date displays in welcome banner in FA locale
- [ ] Loading skeletons show while data is fetching
- [ ] Error states display graceful messages with retry options
- [ ] No TypeScript `any` types in any new files
- [ ] All 28+ tests pass
- [ ] `GET /oracle/stats` endpoint returns correct aggregated data
- [ ] Linter passes with no errors
- Verify all: `cd frontend && npx vitest run && npx tsc --noEmit && npm run lint`

---

## ERROR SCENARIOS

### Problem: API `GET /oracle/stats` returns 500 due to malformed JSONB query

**Fix:** Check that `reading_result` JSONB column is queried correctly. Use `COALESCE` for null confidence values. Test with: `cd api && python3 -m pytest tests/test_dashboard_stats.py -v`. If JSONB extraction fails, use `try/except` in the service layer and return `average_confidence: null` when parsing fails.

### Problem: `useRecentReadings` returns data but cards don't render

**Fix:** Check that the `StoredReadingListResponse` type matches the API response shape. The API returns `{ readings: [...], total: N, limit: N, offset: N }` — ensure the hook destructures correctly. Run: `cd frontend && npx vitest run src/components/dashboard/__tests__/RecentReadings.test.tsx --reporter=verbose`.

### Problem: Persian numerals not rendering in FA locale

**Fix:** Check that `frontend/src/utils/persianFormatter.ts` is imported and used in `StatsCard.tsx`. The formatter should convert Western digits (0-9) to Persian digits (۰-۹). Verify with: `cd frontend && npx vitest run src/utils/__tests__/persianFormatter.test.ts`. If the formatter doesn't exist, create a simple `toPersianDigits(n: number | string): string` utility.

### Problem: Jalali date not displaying in WelcomeBanner

**Fix:** Verify `jalaali-js` is installed (it is in `package.json`). Import `toJalaali` from `jalaali-js` and use it when locale is `fa`. Test: `node -e "const j=require('jalaali-js'); console.log(j.toJalaali(2026, 2, 10))"`.

### Problem: Dashboard tests fail because React Query hooks require Provider

**Fix:** Wrap test renders in `QueryClientProvider` with a fresh `QueryClient`. Create a test utility `renderWithProviders()` that wraps components in `BrowserRouter + QueryClientProvider + I18nextProvider`. Check if such a utility already exists in the test setup.

---

## HANDOFF

**Created:**

- `frontend/src/components/dashboard/WelcomeBanner.tsx`
- `frontend/src/components/dashboard/DailyReadingCard.tsx`
- `frontend/src/components/dashboard/RecentReadings.tsx`
- `frontend/src/components/dashboard/StatsCards.tsx`
- `frontend/src/components/dashboard/QuickActions.tsx`
- `frontend/src/components/dashboard/MoonPhaseWidget.tsx`
- `frontend/src/hooks/useDashboard.ts`
- `frontend/src/components/dashboard/__tests__/` (6 test files)
- `frontend/src/pages/__tests__/Dashboard.test.tsx`
- `api/app/models/dashboard.py`
- `api/tests/test_dashboard_stats.py`

**Modified:**

- `frontend/src/pages/Dashboard.tsx` (full rewrite)
- `frontend/src/components/StatsCard.tsx` (enhanced with icon, trend, locale formatting)
- `frontend/src/services/api.ts` (added `dashboard.stats()`)
- `frontend/src/types/index.ts` (added `DashboardStats`, `MoonPhaseInfo`)
- `frontend/src/locales/en.json` (replaced scanner dashboard keys with Oracle dashboard keys)
- `frontend/src/locales/fa.json` (added Persian dashboard translations)
- `api/app/routers/oracle.py` (added `GET /stats` endpoint)

**Deleted:**

- None

**Next session (Session 23) needs:**

- Dashboard page fully functional at `/dashboard`
- `GET /oracle/stats` API endpoint operational
- `useDashboard.ts` hooks pattern for React Query data fetching
- Updated locale files with comprehensive `dashboard.*` keys (both EN and FA)
- `StatsCard` component with locale-aware formatting (reusable in Settings page)
- `DashboardStats` TypeScript interface (may be extended for admin dashboard later)
