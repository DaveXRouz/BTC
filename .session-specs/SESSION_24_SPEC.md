# SESSION 24 SPEC — Translation Service & i18n Completion

> **Block:** Frontend Core (Sessions 19-25)
> **Depends on:** Sessions 19-23 (all frontend pages exist)
> **Estimated scope:** ~600-800 lines of code changes across ~25 files
> **Migration:** None required (frontend + translation service only)

---

## TL;DR

Audit every `.tsx` file for hardcoded English strings, replace them with `t()` calls,
complete `en.json` and `fa.json` with full translation coverage, verify Persian numeral
formatting and Jalali calendar dates work throughout the app, enhance the backend
translation service for new reading types (Sessions 13-18), add RTL layout verification
across all pages, and write comprehensive i18n tests ensuring zero hardcoded strings
remain.

---

## OBJECTIVES

1. **Zero hardcoded strings** — Every user-visible string in every `.tsx` file uses `t('key')`
2. **Complete translation files** — `en.json` and `fa.json` cover 100% of UI text, organized by page/component
3. **Persian numeral formatting** — All numbers display as `۰۱۲۳۴۵۶۷۸۹` when locale is FA
4. **Jalali calendar dates** — All dates display in Solar Hijri format when locale is FA
5. **RTL layout integrity** — Every page renders correctly in RTL mode with no overflow or misalignment
6. **Backend translation enhancement** — `translation_service.py` handles new reading types from Sessions 13-18
7. **Validation messages** — All form validation errors available in both EN and FA
8. **i18n test coverage** — Automated tests verify no hardcoded strings remain

---

## PREREQUISITES

### Required Sessions Complete

| Session | What It Provides                   | Why Needed                      |
| ------- | ---------------------------------- | ------------------------------- |
| 19      | Layout shell, sidebar, routing     | Base layout with LanguageToggle |
| 20      | Oracle page foundation             | Oracle UI components to audit   |
| 21      | Oracle consultation form + results | Form inputs and results display |
| 22      | Reading history + export           | History page strings            |
| 23      | Dashboard + stats display          | Dashboard content to translate  |

### Required Infrastructure (Already Exists)

| Component            | File                                                            | Status                                                                           |
| -------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| i18next config       | `frontend/src/i18n/config.ts`                                   | Working: EN/FA, LanguageDetector, localStorage                                   |
| English translations | `frontend/src/locales/en.json`                                  | Partial: 190 lines, oracle section well-covered                                  |
| Persian translations | `frontend/src/locales/fa.json`                                  | Partial: 190 lines, matching en.json structure                                   |
| Persian formatter    | `frontend/src/utils/persianFormatter.ts`                        | Working: toPersianDigits, toPersianNumber, formatPersianDate                     |
| Date formatters      | `frontend/src/utils/dateFormatters.ts`                          | Working: jalaali-js, isoToJalaali, formatDate, buildCalendarGrid                 |
| Language toggle      | `frontend/src/components/LanguageToggle.tsx`                    | Working: EN/FA toggle button                                                     |
| Layout with RTL      | `frontend/src/components/Layout.tsx`                            | Working: RTL border support via Tailwind                                         |
| Translation API      | `api/app/routers/translation.py`                                | Exists: translation endpoints                                                    |
| Translation service  | `services/oracle/oracle_service/engines/translation_service.py` | Working: translate(), batch_translate(), detect_language(), FC60 term protection |
| API client           | `frontend/src/services/api.ts`                                  | Working: translation.translate(), translation.detect()                           |

---

## FILES TO CREATE / MODIFY

### Files to MODIFY (Existing)

| #   | File                                                            | What Changes                                                                                                                         |
| --- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `frontend/src/locales/en.json`                                  | Expand from 190 → ~450 lines: add dashboard, settings, scanner, vault, learning, admin, feedback, validation, accessibility sections |
| 2   | `frontend/src/locales/fa.json`                                  | Mirror en.json expansion with Persian translations for all new keys                                                                  |
| 3   | `frontend/src/pages/Dashboard.tsx`                              | Replace ALL hardcoded strings ("Dashboard", "Keys Tested", "Seeds Tested", "Hits", "Speed") with `t()` calls                         |
| 4   | `frontend/src/pages/Settings.tsx`                               | Replace ALL hardcoded strings ("Settings", placeholder text) with `t()` calls                                                        |
| 5   | `frontend/src/pages/Scanner.tsx`                                | Audit and replace any hardcoded strings with `t()` calls                                                                             |
| 6   | `frontend/src/pages/Vault.tsx`                                  | Audit and replace any hardcoded strings with `t()` calls                                                                             |
| 7   | `frontend/src/pages/Learning.tsx`                               | Audit and replace any hardcoded strings with `t()` calls                                                                             |
| 8   | `frontend/src/pages/Oracle.tsx`                                 | Verify all strings use `t()` (mostly done), fix any remaining hardcoded text                                                         |
| 9   | `frontend/src/components/Layout.tsx`                            | Verify nav labels use `t()`, verify RTL works on all breakpoints                                                                     |
| 10  | `frontend/src/components/StatsCard.tsx`                         | Audit for hardcoded strings, add `t()` and Persian number formatting                                                                 |
| 11  | `frontend/src/components/LogPanel.tsx`                          | Audit for hardcoded strings, add `t()` calls                                                                                         |
| 12  | `frontend/src/components/oracle/ReadingResults.tsx`             | Verify tab labels use `t()`, add Persian number formatting for scores                                                                |
| 13  | `frontend/src/components/oracle/ReadingHistory.tsx`             | Verify date formatting uses Jalali in FA locale                                                                                      |
| 14  | `frontend/src/components/oracle/OracleConsultationForm.tsx`     | Verify all labels/placeholders use `t()`, validation messages translated                                                             |
| 15  | `frontend/src/components/oracle/UserForm.tsx`                   | Verify all form labels use `t()`, validation messages translated                                                                     |
| 16  | `frontend/src/components/oracle/ExportButton.tsx`               | Verify button text and export labels use `t()`                                                                                       |
| 17  | `frontend/src/components/oracle/SummaryTab.tsx`                 | Verify all labels use `t()`, numbers use Persian formatting in FA                                                                    |
| 18  | `frontend/src/components/oracle/DetailsTab.tsx`                 | Verify all labels use `t()`, numbers use Persian formatting in FA                                                                    |
| 19  | `frontend/src/components/oracle/TranslatedReading.tsx`          | Verify translation display and loading states use `t()`                                                                              |
| 20  | `frontend/src/components/oracle/SignTypeSelector.tsx`           | Verify sign type labels use `t()`                                                                                                    |
| 21  | `frontend/src/components/oracle/CalendarPicker.tsx`             | Verify month/day names use locale-appropriate names                                                                                  |
| 22  | `frontend/src/components/oracle/PersianKeyboard.tsx`            | Verify labels use `t()`                                                                                                              |
| 23  | `frontend/src/components/oracle/MultiUserSelector.tsx`          | Verify all labels use `t()`                                                                                                          |
| 24  | `frontend/src/components/oracle/UserChip.tsx`                   | Verify display text uses `t()`                                                                                                       |
| 25  | `frontend/src/components/oracle/LocationSelector.tsx`           | Verify labels use `t()`                                                                                                              |
| 26  | `frontend/src/utils/persianFormatter.ts`                        | Add `formatPersianNumber()` with grouping separators, add `toPersianOrdinal()`                                                       |
| 27  | `frontend/src/i18n/config.ts`                                   | Add interpolation format function for automatic Persian numeral formatting                                                           |
| 28  | `services/oracle/oracle_service/engines/translation_service.py` | Add reading type translation support for Session 13-18 reading types (daily, compatibility, name analysis, AI feedback)              |
| 29  | `api/app/routers/translation.py`                                | Add `/translation/batch` endpoint for bulk UI translations, add `/translation/reading` for reading-specific translation              |

### Files to CREATE (New)

| #   | File                                                | Purpose                                                                            |
| --- | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 30  | `frontend/src/hooks/useFormattedNumber.ts`          | Hook: returns locale-aware number formatting (Persian digits in FA, Western in EN) |
| 31  | `frontend/src/hooks/useFormattedDate.ts`            | Hook: returns locale-aware date formatting (Jalali in FA, Gregorian in EN)         |
| 32  | `frontend/src/styles/rtl.css`                       | RTL-specific CSS overrides that Tailwind alone cannot handle                       |
| 33  | `frontend/src/__tests__/i18n-completeness.test.ts`  | Test: verify en.json and fa.json have identical key structures                     |
| 34  | `frontend/src/__tests__/i18n-no-hardcoded.test.ts`  | Test: scan .tsx files for hardcoded English strings                                |
| 35  | `frontend/src/__tests__/rtl-layout.test.tsx`        | Test: verify RTL rendering for all pages                                           |
| 36  | `frontend/src/__tests__/persian-formatting.test.ts` | Test: Persian numerals, dates, ordinals                                            |

---

## IMPLEMENTATION PHASES

---

### PHASE 1: Translation File Expansion (en.json + fa.json)

**Goal:** Complete translation coverage for every UI string in the application.

**Step 1.1 — Audit all .tsx files for hardcoded strings**

Systematically read every `.tsx` file and catalog every user-visible string that is NOT
wrapped in a `t()` call. Create a working list organized by page/component.

Known hardcoded strings found during context gathering:

```
Dashboard.tsx:
  - "Dashboard" (page title)
  - "Keys Tested" (stat label)
  - "Seeds Tested" (stat label)
  - "Hits" (stat label)
  - "Speed" (stat label)

Settings.tsx:
  - "Settings" (page title)
  - All placeholder/TODO text

Scanner.tsx, Vault.tsx, Learning.tsx:
  - Audit required — likely contain hardcoded strings
```

**Step 1.2 — Expand en.json with all missing keys**

Organize translations by namespace matching page/component structure:

```json
{
  "nav": { ... },           // existing, verify complete
  "dashboard": {            // expand significantly
    "title": "Dashboard",
    "keysTestedLabel": "Keys Tested",
    "seedsTestedLabel": "Seeds Tested",
    "hitsLabel": "Hits",
    "speedLabel": "Speed",
    "recentActivity": "Recent Activity",
    "noActivity": "No activity yet",
    "scannerStatus": "Scanner Status",
    "oracleStatus": "Oracle Status",
    "lastUpdated": "Last updated {{time}}",
    ...
  },
  "settings": {             // NEW section
    "title": "Settings",
    "general": "General",
    "language": "Language",
    "theme": "Theme",
    "notifications": "Notifications",
    "security": "Security",
    "apiKeys": "API Keys",
    "changePassword": "Change Password",
    "currentPassword": "Current Password",
    "newPassword": "New Password",
    "confirmPassword": "Confirm Password",
    "save": "Save Changes",
    "saved": "Settings saved",
    "darkMode": "Dark Mode",
    "lightMode": "Light Mode",
    ...
  },
  "scanner": { ... },      // expand from 8 keys
  "vault": { ... },         // expand from 4 keys
  "learning": { ... },      // expand from 4 keys
  "oracle": { ... },        // existing ~100 keys, verify complete
  "feedback": {             // NEW — from Session 18
    "title": "Rate This Reading",
    "accuracy": "Accuracy",
    "helpfulness": "Helpfulness",
    "clarity": "Clarity",
    "comment": "Additional Comments",
    "commentPlaceholder": "What did you think of this reading?",
    "submit": "Submit Feedback",
    "thankYou": "Thank you for your feedback!",
    "alreadySubmitted": "You've already rated this reading",
    ...
  },
  "validation": {           // NEW — all form validation messages
    "required": "This field is required",
    "nameRequired": "Name is required",
    "nameMinLength": "Name must be at least 2 characters",
    "dateRequired": "Birth date is required",
    "dateInvalid": "Please enter a valid date",
    "dateFuture": "Birth date cannot be in the future",
    "questionRequired": "Please enter a question",
    "questionMinLength": "Question must be at least 10 characters",
    "emailInvalid": "Please enter a valid email address",
    "passwordMinLength": "Password must be at least 8 characters",
    "passwordMismatch": "Passwords do not match",
    ...
  },
  "accessibility": {        // NEW — screen reader text
    "skipToContent": "Skip to main content",
    "menuToggle": "Toggle navigation menu",
    "languageSwitch": "Switch language",
    "closeModal": "Close dialog",
    "loading": "Loading...",
    "error": "An error occurred",
    ...
  },
  "common": { ... }         // expand from 5 keys
}
```

**Step 1.3 — Mirror all new keys in fa.json with Persian translations**

Every key added to `en.json` must have a corresponding entry in `fa.json`.
Persian translations must use proper Persian (not Arabic) script and grammar.

Key translation notes:

- "Dashboard" → "داشبورد"
- "Settings" → "تنظیمات"
- "Keys Tested" → "کلیدهای آزمایش‌شده"
- "Seeds Tested" → "سیدهای آزمایش‌شده"
- "Hits" → "نتایج"
- "Speed" → "سرعت"
- "Save Changes" → "ذخیره تغییرات"
- "This field is required" → "این فیلد الزامی است"
- "Loading..." → "در حال بارگذاری..."
- Use zero-width non-joiner (‌) correctly in compound Persian words

**Step 1.4 — Verify key structure parity**

After expansion, both files must have identical key structures.
Write a quick verification: parse both JSON files and compare key paths.

#### STOP CHECKPOINT 1

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Verify both files parse correctly
node -e "
  const en = require('./src/locales/en.json');
  const fa = require('./src/locales/fa.json');
  const enKeys = JSON.stringify(Object.keys(en).sort());
  const faKeys = JSON.stringify(Object.keys(fa).sort());
  console.log('EN top-level keys:', Object.keys(en).length);
  console.log('FA top-level keys:', Object.keys(fa).length);
  console.log('Match:', enKeys === faKeys);
"
# Expected: Both files have same top-level key count, Match: true
```

---

### PHASE 2: Page Component i18n Conversion

**Goal:** Replace every hardcoded string in every page component with `t()` calls.

**Step 2.1 — Add `useTranslation` import to all page files**

Every page file that doesn't already import `useTranslation` needs:

```tsx
import { useTranslation } from "react-i18next";
```

And inside the component:

```tsx
const { t } = useTranslation();
```

**Step 2.2 — Convert Dashboard.tsx**

Current (hardcoded):

```tsx
<h1>Dashboard</h1>
<span>Keys Tested</span>
<span>Seeds Tested</span>
<span>Hits</span>
<span>Speed</span>
```

Target (translated):

```tsx
<h1>{t('dashboard.title')}</h1>
<span>{t('dashboard.keysTestedLabel')}</span>
<span>{t('dashboard.seedsTestedLabel')}</span>
<span>{t('dashboard.hitsLabel')}</span>
<span>{t('dashboard.speedLabel')}</span>
```

**Step 2.3 — Convert Settings.tsx**

Replace all hardcoded strings in Settings page. This page is mostly stubs/TODOs,
so add `t()` calls to whatever text exists and ensure new text added by
Sessions 19-23 is also translated.

**Step 2.4 — Convert Scanner.tsx, Vault.tsx, Learning.tsx**

Audit each page for hardcoded strings. Even stub pages should use `t()` for
any visible text (titles, placeholder messages, button labels).

**Step 2.5 — Verify Oracle.tsx**

Oracle.tsx already uses `t()` extensively (~100 oracle.\* keys). Verify:

- No remaining hardcoded strings
- Modal titles and button labels all use `t()`
- Error messages use `t()`
- Loading states use `t()`

#### STOP CHECKPOINT 2

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Quick grep for obvious hardcoded strings in page files
grep -rn '"Dashboard"\|"Settings"\|"Scanner"\|"Vault"\|"Learning"' src/pages/ || echo "No hardcoded page titles found - PASS"
# Expected: No matches (all replaced with t() calls)
```

---

### PHASE 3: Oracle Component i18n Verification

**Goal:** Verify and fix i18n in all oracle subcomponents (~15 components).

**Step 3.1 — Audit ReadingResults.tsx, SummaryTab.tsx, DetailsTab.tsx**

These display reading output. Verify:

- Tab labels ("Summary", "Details", "History") use `t('oracle.tabs.summary')` etc.
- Score labels use `t()`
- Number values use locale-aware formatting

**Step 3.2 — Audit OracleConsultationForm.tsx**

Verify:

- Form labels use `t()`
- Placeholder text uses `t()`
- Button text uses `t()`
- Validation error messages use `t('validation.*')` keys

**Step 3.3 — Audit UserForm.tsx, MultiUserSelector.tsx, UserChip.tsx**

Verify:

- "Add User", "Edit User", "Remove" labels use `t()`
- Form field labels use `t()`
- Confirmation dialogs use `t()`

**Step 3.4 — Audit SignTypeSelector.tsx, CalendarPicker.tsx, LocationSelector.tsx**

Verify:

- Sign type names translated (if displayed as text)
- Calendar month/day names use locale-appropriate names (Jalali months in FA)
- Location labels use `t()`

**Step 3.5 — Audit PersianKeyboard.tsx, TranslatedReading.tsx**

Verify:

- PersianKeyboard labels use `t()`
- TranslatedReading loading/error states use `t()`

**Step 3.6 — Audit ExportButton.tsx, ReadingHistory.tsx**

Verify:

- Export format labels use `t()`
- History date displays use locale-aware formatting
- "No history" empty state uses `t()`

#### STOP CHECKPOINT 3

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Search for any remaining hardcoded English strings in oracle components
# Exclude test files, look for quoted strings that aren't i18n keys
grep -rn ">[A-Z][a-z]" src/components/oracle/*.tsx | grep -v ".test." | grep -v "t('" | grep -v "className" | grep -v "import" | head -20
echo "---"
echo "Review above: any remaining hardcoded text should be zero"
```

---

### PHASE 4: Number & Date Formatting Hooks

**Goal:** Create reusable hooks for locale-aware number and date formatting.

**Step 4.1 — Create `useFormattedNumber` hook**

```
File: frontend/src/hooks/useFormattedNumber.ts
```

This hook provides locale-aware number formatting:

```typescript
import { useTranslation } from "react-i18next";
import { toPersianNumber } from "../utils/persianFormatter";

export function useFormattedNumber() {
  const { i18n } = useTranslation();
  const isPersian = i18n.language === "fa";

  const formatNumber = (n: number): string => {
    if (isPersian) {
      return toPersianNumber(n);
    }
    return n.toLocaleString("en-US");
  };

  const formatPercent = (n: number): string => {
    const formatted = isPersian ? toPersianNumber(n) : n.toString();
    return isPersian ? `${formatted}٪` : `${formatted}%`;
  };

  const formatScore = (n: number, max: number = 100): string => {
    const formatted = formatNumber(n);
    const formattedMax = formatNumber(max);
    return `${formatted}/${formattedMax}`;
  };

  return { formatNumber, formatPercent, formatScore, isPersian };
}
```

**Step 4.2 — Create `useFormattedDate` hook**

```
File: frontend/src/hooks/useFormattedDate.ts
```

This hook wraps existing `dateFormatters.ts` utilities with locale awareness:

```typescript
import { useTranslation } from "react-i18next";
import { formatDate, isoToJalaali } from "../utils/dateFormatters";
import { formatPersianDate } from "../utils/persianFormatter";

export function useFormattedDate() {
  const { i18n } = useTranslation();
  const isPersian = i18n.language === "fa";

  const format = (isoDate: string): string => {
    if (isPersian) {
      return formatPersianDate(isoDate);
    }
    return formatDate(isoDate, "gregorian");
  };

  const formatRelative = (isoDate: string): string => {
    // "2 days ago" / "۲ روز پیش"
    const now = new Date();
    const date = new Date(isoDate);
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (isPersian) {
      if (diffDays === 0) return "امروز";
      if (diffDays === 1) return "دیروز";
      return `${toPersianNumber(diffDays)} روز پیش`;
    }
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    return `${diffDays} days ago`;
  };

  return { format, formatRelative, isPersian };
}
```

**Step 4.3 — Enhance persianFormatter.ts**

Add missing utilities to `frontend/src/utils/persianFormatter.ts`:

```typescript
// Add to existing file:

/** Format number with Persian grouping separator (٬) */
export function formatPersianGrouped(n: number): string {
  const parts = n.toString().split(".");
  const intPart = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, "٬");
  const result = parts.length > 1 ? `${intPart}.${parts[1]}` : intPart;
  return toPersianDigits(result);
}

/** Persian ordinal: 1 → "اول", 2 → "دوم", 3 → "سوم", n → "nم" */
export function toPersianOrdinal(n: number): string {
  const ordinals: Record<number, string> = {
    1: "اول",
    2: "دوم",
    3: "سوم",
    4: "چهارم",
    5: "پنجم",
    6: "ششم",
    7: "هفتم",
    8: "هشتم",
    9: "نهم",
    10: "دهم",
  };
  if (ordinals[n]) return ordinals[n];
  return `${toPersianNumber(n)}م`;
}
```

**Step 4.4 — Add interpolation format function to i18n config**

Update `frontend/src/i18n/config.ts` to auto-format numbers in translations:

```typescript
// Add to i18next init config:
interpolation: {
  escapeValue: false,
  format: (value, format, lng) => {
    if (format === 'number' && lng === 'fa') {
      return toPersianNumber(value);
    }
    if (format === 'date' && lng === 'fa') {
      return formatPersianDate(value);
    }
    return value;
  },
},
```

This enables translations like:

```json
{ "keysCount": "{{count, number}} keys tested" }
```

Which auto-formats as "۱٬۲۳۴ keys tested" in FA.

#### STOP CHECKPOINT 4

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Verify new files exist
ls -la src/hooks/useFormattedNumber.ts src/hooks/useFormattedDate.ts
# Verify persianFormatter has new exports
grep -c "export function" src/utils/persianFormatter.ts
# Expected: 5+ exported functions (original 3 + new 2)
```

---

### PHASE 5: RTL Layout Verification & Fixes

**Goal:** Ensure every page renders correctly in RTL mode.

**Step 5.1 — Create RTL CSS overrides**

```
File: frontend/src/styles/rtl.css
```

Tailwind handles most RTL via `rtl:` prefix, but some cases need explicit CSS:

```css
/* RTL-specific overrides that Tailwind cannot handle */

/* Fix icon positioning in RTL */
[dir="rtl"] .icon-left {
  transform: scaleX(-1);
}

/* Fix text alignment for mixed LTR/RTL content */
[dir="rtl"] .ltr-numbers {
  direction: ltr;
  unicode-bidi: embed;
}

/* Fix input field text direction for English input in RTL context */
[dir="rtl"] input[type="email"],
[dir="rtl"] input[type="url"],
[dir="rtl"] input[type="number"] {
  direction: ltr;
  text-align: right;
}

/* Fix sidebar transition direction */
[dir="rtl"] .sidebar-enter {
  transform: translateX(100%);
}
[dir="rtl"] .sidebar-enter-active {
  transform: translateX(0);
}

/* Fix table alignment */
[dir="rtl"] th,
[dir="rtl"] td {
  text-align: right;
}

/* Fix dropdown positioning */
[dir="rtl"] .dropdown-menu {
  left: auto;
  right: 0;
}

/* Bitcoin addresses and hashes always LTR */
.address,
.hash,
.monospace {
  direction: ltr;
  unicode-bidi: embed;
}
```

**Step 5.2 — Import RTL CSS in main entry point**

Add the RTL CSS import to the app's main entry point (likely `main.tsx` or `App.tsx`):

```typescript
import "./styles/rtl.css";
```

**Step 5.3 — Verify Layout.tsx RTL behavior**

The existing `Layout.tsx` has `rtl:border-r-0 rtl:border-l` support.
Verify all sidebar elements flip correctly:

- Navigation items
- Icons (should they flip or stay?)
- Collapse/expand arrows
- LanguageToggle position

**Step 5.4 — Verify page-level RTL rendering**

For each page, check:

- Text alignment flips correctly
- Flexbox/grid layouts reverse direction
- Margins/paddings flip (use `ms-`/`me-` instead of `ml-`/`mr-` where applicable)
- Charts/graphs maintain correct direction (numbers always LTR)
- Form layouts work in RTL

**Step 5.5 — Add `dir` attribute to document root**

Ensure the document `<html>` tag gets `dir="rtl"` when locale is FA.
This should be handled in `i18n/config.ts` or a top-level effect:

```typescript
i18n.on("languageChanged", (lng) => {
  document.documentElement.dir = lng === "fa" ? "rtl" : "ltr";
  document.documentElement.lang = lng;
});
```

Verify this already exists or add it to `i18n/config.ts`.

#### STOP CHECKPOINT 5

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Verify RTL CSS exists
ls -la src/styles/rtl.css
# Verify dir attribute logic exists
grep -n "dir.*rtl\|languageChanged\|documentElement.dir" src/i18n/config.ts
# Expected: RTL file exists, dir change logic found
```

---

### PHASE 6: Backend Translation Service Enhancement

**Goal:** Extend `translation_service.py` to handle reading types from Sessions 13-18.

**Step 6.1 — Add reading-type-specific translation support**

The existing `translation_service.py` has `translate()` and `batch_translate()` with
FC60 term protection. Extend it to understand the reading type context for better
translations:

Add to `services/oracle/oracle_service/engines/translation_service.py`:

```python
# New reading types from Sessions 13-18
READING_TYPE_CONTEXTS = {
    "personal": "numerology personal reading with life path and expression numbers",
    "compatibility": "numerology compatibility analysis between two people",
    "daily": "daily numerology forecast with personal year and universal day",
    "name_analysis": "name numerology analysis with soul urge and personality numbers",
    "question": "numerology-based question answering consultation",
}

def translate_reading(
    reading_text: str,
    reading_type: str,
    source_lang: str = "en",
    target_lang: str = "fa",
) -> TranslationResult:
    """
    Translate a reading with reading-type-specific context for better accuracy.
    Uses FC60 term protection from existing _protect_terms/_restore_terms.
    """
    context = READING_TYPE_CONTEXTS.get(reading_type, "numerology reading")
    # Build context-aware prompt that preserves numerology terminology
    # Use existing translate() with enhanced system prompt
    ...
```

**Step 6.2 — Add batch reading translation endpoint**

Add to `api/app/routers/translation.py`:

```python
@router.post("/translation/reading")
async def translate_reading(request: ReadingTranslationRequest):
    """Translate a reading with type-specific context."""
    ...

@router.post("/translation/batch")
async def batch_translate(request: BatchTranslationRequest):
    """Translate multiple strings in one request (for UI bulk loading)."""
    ...
```

**Step 6.3 — Add Pydantic models for new endpoints**

Add to `api/app/models/` (existing translation models file or new):

```python
class ReadingTranslationRequest(BaseModel):
    text: str
    reading_type: str  # "personal" | "compatibility" | "daily" | "name_analysis" | "question"
    source_lang: str = "en"
    target_lang: str = "fa"

class BatchTranslationRequest(BaseModel):
    texts: list[str]
    source_lang: str = "en"
    target_lang: str = "fa"

class BatchTranslationResponse(BaseModel):
    translations: list[TranslationResult]
```

**Step 6.4 — Update FC60 term protection list**

The existing `FC60_PRESERVED_TERMS` in `prompt_templates.py` and `_protect_terms` in
`translation_service.py` should be synchronized. Verify both lists cover:

- All 12 animal names (Rat, Ox, Tiger, Rabbit, Dragon, Snake, Horse, Goat, Monkey, Rooster, Dog, Pig)
- All 5 element names (Wood, Fire, Earth, Metal, Water)
- Numerology terms: Life Path, Expression, Soul Urge, Personality, Personal Year
- Master numbers: "Master Number 11", "Master Number 22", "Master Number 33"

#### STOP CHECKPOINT 6

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS
# Verify translation service has new function
grep -n "def translate_reading" services/oracle/oracle_service/engines/translation_service.py
# Verify new API endpoints
grep -n "translation/reading\|translation/batch" api/app/routers/translation.py
# Expected: Both found with line numbers
```

---

### PHASE 7: Comprehensive i18n Tests

**Goal:** Write tests that ensure i18n coverage is complete and stays complete.

**Step 7.1 — Translation file completeness test**

```
File: frontend/src/__tests__/i18n-completeness.test.ts
```

```typescript
import en from "../locales/en.json";
import fa from "../locales/fa.json";

function getAllKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "object" && value !== null) {
      return getAllKeys(value as Record<string, unknown>, fullKey);
    }
    return [fullKey];
  });
}

describe("i18n completeness", () => {
  const enKeys = getAllKeys(en);
  const faKeys = getAllKeys(fa);

  test("en.json and fa.json have identical key structures", () => {
    const enSet = new Set(enKeys);
    const faSet = new Set(faKeys);
    const missingInFa = enKeys.filter((k) => !faSet.has(k));
    const missingInEn = faKeys.filter((k) => !enSet.has(k));
    expect(missingInFa).toEqual([]);
    expect(missingInEn).toEqual([]);
  });

  test("no empty translation values in en.json", () => {
    const empty = enKeys.filter((k) => {
      const parts = k.split(".");
      let val: unknown = en;
      for (const p of parts) val = (val as Record<string, unknown>)[p];
      return val === "" || val === null || val === undefined;
    });
    expect(empty).toEqual([]);
  });

  test("no empty translation values in fa.json", () => {
    const empty = faKeys.filter((k) => {
      const parts = k.split(".");
      let val: unknown = fa;
      for (const p of parts) val = (val as Record<string, unknown>)[p];
      return val === "" || val === null || val === undefined;
    });
    expect(empty).toEqual([]);
  });

  test("en.json has minimum expected sections", () => {
    const sections = Object.keys(en);
    expect(sections).toContain("nav");
    expect(sections).toContain("dashboard");
    expect(sections).toContain("settings");
    expect(sections).toContain("scanner");
    expect(sections).toContain("oracle");
    expect(sections).toContain("vault");
    expect(sections).toContain("learning");
    expect(sections).toContain("feedback");
    expect(sections).toContain("validation");
    expect(sections).toContain("common");
  });

  test("translation count is above minimum threshold", () => {
    expect(enKeys.length).toBeGreaterThan(150);
    expect(faKeys.length).toBeGreaterThan(150);
  });
});
```

**Step 7.2 — No hardcoded strings test**

```
File: frontend/src/__tests__/i18n-no-hardcoded.test.ts
```

This test scans `.tsx` files for patterns that indicate hardcoded English text:

```typescript
import * as fs from "fs";
import * as path from "path";
import { globSync } from "glob";

// Patterns that indicate hardcoded strings (not exhaustive, catches common cases)
const HARDCODED_PATTERNS = [
  // JSX text content: >Some Text<
  />[A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)+</g,
];

// Files/patterns to exclude from checking
const EXCLUSIONS = [
  "**/*.test.tsx",
  "**/*.test.ts",
  "**/i18n/**",
  "**/locales/**",
];

// Known exceptions (e.g., component names used in code, not displayed)
const KNOWN_EXCEPTIONS = [
  "NPS", // Brand name, not translated
  "FC60", // Technical term
  "Bitcoin", // Technical term
];

describe("no hardcoded strings", () => {
  const tsxFiles = globSync("src/**/*.tsx", {
    cwd: path.resolve(__dirname, ".."),
    ignore: EXCLUSIONS,
  });

  test("found tsx files to scan", () => {
    expect(tsxFiles.length).toBeGreaterThan(10);
  });

  test.each(tsxFiles)("%s has no hardcoded strings", (file) => {
    const content = fs.readFileSync(
      path.resolve(__dirname, "..", file),
      "utf-8",
    );
    // Check for common hardcoded patterns
    const issues: string[] = [];
    const lines = content.split("\n");

    lines.forEach((line, idx) => {
      // Skip imports, comments, className, type annotations
      if (
        line.trim().startsWith("import") ||
        line.trim().startsWith("//") ||
        line.trim().startsWith("*") ||
        line.includes("className") ||
        line.includes("console.") ||
        line.includes("throw new")
      )
        return;

      // Look for JSX text: >Text here<
      const matches = line.match(/>[A-Z][a-z]{2,}(?:\s+[a-zA-Z]+)*</g);
      if (matches) {
        const filtered = matches.filter((m) => {
          const text = m.slice(1, -1).trim();
          return !KNOWN_EXCEPTIONS.some((ex) => text.includes(ex));
        });
        if (filtered.length > 0) {
          issues.push(`Line ${idx + 1}: ${filtered.join(", ")}`);
        }
      }
    });

    expect(issues).toEqual([]);
  });
});
```

**Step 7.3 — Persian formatting tests**

```
File: frontend/src/__tests__/persian-formatting.test.ts
```

```typescript
import {
  toPersianDigits,
  toPersianNumber,
  formatPersianDate,
  formatPersianGrouped,
  toPersianOrdinal,
} from "../utils/persianFormatter";

describe("Persian formatting", () => {
  describe("toPersianDigits", () => {
    test("converts all digits", () => {
      expect(toPersianDigits("0123456789")).toBe("۰۱۲۳۴۵۶۷۸۹");
    });
    test("preserves non-digit characters", () => {
      expect(toPersianDigits("abc")).toBe("abc");
    });
    test("handles mixed content", () => {
      expect(toPersianDigits("Score: 42")).toBe("Score: ۴۲");
    });
  });

  describe("toPersianNumber", () => {
    test("converts integer", () => {
      expect(toPersianNumber(42)).toBe("۴۲");
    });
    test("converts zero", () => {
      expect(toPersianNumber(0)).toBe("۰");
    });
    test("converts large number", () => {
      expect(toPersianNumber(1234)).toBe("۱۲۳۴");
    });
  });

  describe("formatPersianGrouped", () => {
    test("adds grouping separator", () => {
      expect(formatPersianGrouped(1234567)).toBe("۱٬۲۳۴٬۵۶۷");
    });
    test("no separator for small numbers", () => {
      expect(formatPersianGrouped(999)).toBe("۹۹۹");
    });
    test("handles zero", () => {
      expect(formatPersianGrouped(0)).toBe("۰");
    });
  });

  describe("toPersianOrdinal", () => {
    test("first → اول", () => {
      expect(toPersianOrdinal(1)).toBe("اول");
    });
    test("second → دوم", () => {
      expect(toPersianOrdinal(2)).toBe("دوم");
    });
    test("tenth → دهم", () => {
      expect(toPersianOrdinal(10)).toBe("دهم");
    });
    test("eleventh → ۱۱م (generic pattern)", () => {
      expect(toPersianOrdinal(11)).toBe("۱۱م");
    });
  });

  describe("formatPersianDate", () => {
    test("converts ISO date to Jalali", () => {
      const result = formatPersianDate("2024-03-20");
      // 2024-03-20 = 1403/01/01 (Nowruz)
      expect(result).toContain("۱۴۰۳");
    });
  });
});
```

**Step 7.4 — RTL layout tests**

```
File: frontend/src/__tests__/rtl-layout.test.tsx
```

```typescript
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';

// Helper to render in RTL mode
function renderRTL(ui: React.ReactElement) {
  i18n.changeLanguage('fa');
  return render(
    <I18nextProvider i18n={i18n}>{ui}</I18nextProvider>
  );
}

function renderLTR(ui: React.ReactElement) {
  i18n.changeLanguage('en');
  return render(
    <I18nextProvider i18n={i18n}>{ui}</I18nextProvider>
  );
}

describe('RTL layout', () => {
  test('document direction changes to RTL for Persian', () => {
    i18n.changeLanguage('fa');
    expect(document.documentElement.dir).toBe('rtl');
  });

  test('document direction changes to LTR for English', () => {
    i18n.changeLanguage('en');
    expect(document.documentElement.dir).toBe('ltr');
  });

  test('language attribute updates on language change', () => {
    i18n.changeLanguage('fa');
    expect(document.documentElement.lang).toBe('fa');
    i18n.changeLanguage('en');
    expect(document.documentElement.lang).toBe('en');
  });
});
```

**Step 7.5 — Backend translation tests**

```
File: services/oracle/oracle_service/tests/test_translation_session24.py
```

```python
import pytest
from engines.translation_service import (
    translate,
    batch_translate,
    detect_language,
    translate_reading,
    READING_TYPE_CONTEXTS,
)

class TestTranslateReading:
    """Tests for reading-type-specific translation."""

    def test_reading_type_contexts_defined(self):
        """All expected reading types have context strings."""
        expected = ["personal", "compatibility", "daily", "name_analysis", "question"]
        for rt in expected:
            assert rt in READING_TYPE_CONTEXTS

    def test_translate_reading_preserves_fc60_terms(self):
        """FC60 terms should survive translation."""
        text = "Your Life Path number is 7 (The Seeker). Wood Dragon energy."
        result = translate_reading(text, "personal", "en", "fa")
        assert result.translated_text is not None
        # FC60 terms should be preserved or transliterated, not lost
        assert len(result.translated_text) > 0

    def test_translate_reading_unknown_type_fallback(self):
        """Unknown reading type should still translate successfully."""
        text = "Your number is 5."
        result = translate_reading(text, "unknown_type", "en", "fa")
        assert result.translated_text is not None

class TestDetectLanguage:
    """Tests for language detection."""

    def test_detect_persian(self):
        """Persian text detected correctly."""
        assert detect_language("سلام خوبی") == "fa"

    def test_detect_english(self):
        """English text detected correctly."""
        assert detect_language("Hello world") == "en"

    def test_detect_mixed(self):
        """Mixed text returns dominant language."""
        result = detect_language("Hello سلام")
        assert result in ("en", "fa")

class TestBatchTranslate:
    """Tests for batch translation."""

    def test_batch_returns_correct_count(self):
        """Batch translate returns same number of results as inputs."""
        texts = ["Hello", "World", "Test"]
        results = batch_translate(texts, "en", "fa")
        assert len(results) == 3

    def test_batch_empty_list(self):
        """Empty batch returns empty list."""
        results = batch_translate([], "en", "fa")
        assert results == []
```

**Step 7.6 — API endpoint tests**

```
File: api/tests/test_translation_session24.py
```

```python
import pytest
from httpx import AsyncClient

class TestTranslationEndpoints:
    """Tests for Session 24 translation API endpoints."""

    @pytest.mark.asyncio
    async def test_translate_reading_endpoint(self, client: AsyncClient):
        """POST /translation/reading returns translated text."""
        response = await client.post("/translation/reading", json={
            "text": "Your Life Path is 7.",
            "reading_type": "personal",
            "source_lang": "en",
            "target_lang": "fa",
        })
        assert response.status_code == 200
        data = response.json()
        assert "translated_text" in data

    @pytest.mark.asyncio
    async def test_batch_translate_endpoint(self, client: AsyncClient):
        """POST /translation/batch returns all translations."""
        response = await client.post("/translation/batch", json={
            "texts": ["Hello", "World"],
            "source_lang": "en",
            "target_lang": "fa",
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["translations"]) == 2

    @pytest.mark.asyncio
    async def test_translate_reading_invalid_type(self, client: AsyncClient):
        """Unknown reading type still works (graceful fallback)."""
        response = await client.post("/translation/reading", json={
            "text": "Test text",
            "reading_type": "nonexistent",
            "source_lang": "en",
            "target_lang": "fa",
        })
        assert response.status_code == 200
```

#### STOP CHECKPOINT 7

```bash
cd /Users/hamzeh/Desktop/GitHub/NPS/frontend
# Run i18n tests
npx vitest run src/__tests__/i18n-completeness.test.ts --reporter=verbose 2>&1 | tail -20
npx vitest run src/__tests__/persian-formatting.test.ts --reporter=verbose 2>&1 | tail -20

cd /Users/hamzeh/Desktop/GitHub/NPS
# Run backend translation tests
cd services/oracle && python3 -m pytest tests/test_translation_session24.py -v 2>&1 | tail -20
cd /Users/hamzeh/Desktop/GitHub/NPS
cd api && python3 -m pytest tests/test_translation_session24.py -v 2>&1 | tail -20
# Expected: All tests pass
```

---

## TESTS SUMMARY

| #   | Test File                                           | Test Name                                             | What It Verifies                  |
| --- | --------------------------------------------------- | ----------------------------------------------------- | --------------------------------- |
| 1   | `frontend/src/__tests__/i18n-completeness.test.ts`  | `en.json and fa.json have identical key structures`   | No missing keys in either file    |
| 2   | `frontend/src/__tests__/i18n-completeness.test.ts`  | `no empty translation values in en.json`              | No blank values in EN             |
| 3   | `frontend/src/__tests__/i18n-completeness.test.ts`  | `no empty translation values in fa.json`              | No blank values in FA             |
| 4   | `frontend/src/__tests__/i18n-completeness.test.ts`  | `en.json has minimum expected sections`               | All page sections exist           |
| 5   | `frontend/src/__tests__/i18n-completeness.test.ts`  | `translation count is above minimum threshold`        | 150+ translation keys             |
| 6   | `frontend/src/__tests__/i18n-no-hardcoded.test.ts`  | `found tsx files to scan`                             | Test setup works                  |
| 7   | `frontend/src/__tests__/i18n-no-hardcoded.test.ts`  | `%s has no hardcoded strings` (parametric)            | Each .tsx file passes             |
| 8   | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianDigits converts all digits`                 | 0-9 → ۰-۹                         |
| 9   | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianDigits preserves non-digit characters`      | Letters unchanged                 |
| 10  | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianDigits handles mixed content`               | Partial conversion                |
| 11  | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianNumber converts integer`                    | Number → Persian string           |
| 12  | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianNumber converts zero`                       | Edge case                         |
| 13  | `frontend/src/__tests__/persian-formatting.test.ts` | `formatPersianGrouped adds grouping separator`        | 1234567 → ۱٬۲۳۴٬۵۶۷               |
| 14  | `frontend/src/__tests__/persian-formatting.test.ts` | `formatPersianGrouped no separator for small numbers` | 999 → ۹۹۹                         |
| 15  | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianOrdinal first`                              | 1 → اول                           |
| 16  | `frontend/src/__tests__/persian-formatting.test.ts` | `toPersianOrdinal generic pattern`                    | 11 → ۱۱م                          |
| 17  | `frontend/src/__tests__/persian-formatting.test.ts` | `formatPersianDate converts ISO date to Jalali`       | Nowruz date test                  |
| 18  | `frontend/src/__tests__/rtl-layout.test.tsx`        | `document direction changes to RTL for Persian`       | dir="rtl" on FA                   |
| 19  | `frontend/src/__tests__/rtl-layout.test.tsx`        | `document direction changes to LTR for English`       | dir="ltr" on EN                   |
| 20  | `frontend/src/__tests__/rtl-layout.test.tsx`        | `language attribute updates on language change`       | lang="fa"/"en"                    |
| 21  | `services/oracle/.../test_translation_session24.py` | `test_reading_type_contexts_defined`                  | All 5 types have context          |
| 22  | `services/oracle/.../test_translation_session24.py` | `test_translate_reading_preserves_fc60_terms`         | FC60 terms survive                |
| 23  | `services/oracle/.../test_translation_session24.py` | `test_translate_reading_unknown_type_fallback`        | Graceful fallback                 |
| 24  | `services/oracle/.../test_translation_session24.py` | `test_detect_persian`                                 | Persian detection                 |
| 25  | `services/oracle/.../test_translation_session24.py` | `test_detect_english`                                 | English detection                 |
| 26  | `services/oracle/.../test_translation_session24.py` | `test_detect_mixed`                                   | Mixed text detection              |
| 27  | `services/oracle/.../test_translation_session24.py` | `test_batch_returns_correct_count`                    | Batch count matches               |
| 28  | `services/oracle/.../test_translation_session24.py` | `test_batch_empty_list`                               | Empty batch edge case             |
| 29  | `api/tests/test_translation_session24.py`           | `test_translate_reading_endpoint`                     | POST /translation/reading works   |
| 30  | `api/tests/test_translation_session24.py`           | `test_batch_translate_endpoint`                       | POST /translation/batch works     |
| 31  | `api/tests/test_translation_session24.py`           | `test_translate_reading_invalid_type`                 | Graceful fallback on unknown type |

---

## ACCEPTANCE CRITERIA

All of the following must be true before Session 24 is marked complete:

### Translation Coverage

- [ ] `en.json` has 150+ translation keys organized by page/component
- [ ] `fa.json` has identical key structure to `en.json` with zero empty values
- [ ] Every section exists: nav, dashboard, settings, scanner, oracle, vault, learning, feedback, validation, accessibility, common

### Hardcoded String Elimination

- [ ] `Dashboard.tsx` — zero hardcoded English strings
- [ ] `Settings.tsx` — zero hardcoded English strings
- [ ] `Scanner.tsx` — zero hardcoded English strings
- [ ] `Vault.tsx` — zero hardcoded English strings
- [ ] `Learning.tsx` — zero hardcoded English strings
- [ ] `Oracle.tsx` — zero hardcoded English strings (verify existing)
- [ ] All oracle subcomponents (15 files) — zero hardcoded English strings
- [ ] `Layout.tsx` — nav labels use `t()`
- [ ] `StatsCard.tsx`, `LogPanel.tsx` — zero hardcoded English strings

### Persian Formatting

- [ ] `persianFormatter.ts` exports: toPersianDigits, toPersianNumber, formatPersianDate, formatPersianGrouped, toPersianOrdinal
- [ ] Numbers display as ۰۱۲۳۴۵۶۷۸۹ in FA locale throughout the app
- [ ] Dates display in Jalali format in FA locale
- [ ] Grouping separator uses ٬ (Arabic comma) not , (Latin comma)

### RTL Layout

- [ ] `rtl.css` exists with necessary overrides
- [ ] `document.documentElement.dir` updates on language change
- [ ] `document.documentElement.lang` updates on language change
- [ ] All pages render without overflow or misalignment in RTL
- [ ] Bitcoin addresses/hashes always display LTR even in RTL context

### Hooks

- [ ] `useFormattedNumber` hook exists and returns locale-aware formatters
- [ ] `useFormattedDate` hook exists and returns locale-aware date formatters
- [ ] Both hooks react to language changes

### Backend Translation

- [ ] `translate_reading()` function added to translation_service.py
- [ ] `READING_TYPE_CONTEXTS` covers: personal, compatibility, daily, name_analysis, question
- [ ] `POST /translation/reading` endpoint exists and works
- [ ] `POST /translation/batch` endpoint exists and works
- [ ] FC60 term protection list synchronized between prompt_templates.py and translation_service.py

### Tests

- [ ] All 31 tests pass
- [ ] i18n completeness test confirms en/fa key parity
- [ ] Hardcoded string scanner passes on all .tsx files
- [ ] Persian formatting tests pass
- [ ] RTL layout tests pass
- [ ] Backend translation tests pass
- [ ] API endpoint tests pass

---

## ERROR SCENARIOS

### What If Sessions 19-23 Are Not Complete?

Some pages may still be stubs. In that case:

- Still add `t()` calls to whatever text exists in the stubs
- Still create the translation keys in en.json/fa.json
- When Sessions 19-23 complete their pages, the translation keys will already exist
- The hardcoded string scanner test may need `KNOWN_EXCEPTIONS` for stub/TODO text

### What If Translation Service API Key Is Missing?

The backend `translate_reading()` function uses the Anthropic API for AI translations.
If `ANTHROPIC_API_KEY` is not set:

- `translate_reading()` should return a `TranslationResult` with the original text
- Log a warning: "ANTHROPIC_API_KEY not set, returning untranslated text"
- Tests should mock the API calls
- This follows the project rule: "Missing API key = fallback text, not crash"

### What If jalaali-js Has Edge Cases?

Known edge case: dates before 1300 SH (1921 CE) or after 1500 SH (2121 CE).

- `formatPersianDate` should handle these gracefully
- If jalaali-js throws, catch and return the Gregorian date with a "تاریخ میلادی" prefix
- Test with boundary dates: 1300/01/01 and 1499/12/29

### What If a .tsx File Has Intentionally Untranslated Text?

Some text should NOT be translated:

- Brand names: "NPS", "Bitcoin", "BTC"
- Technical terms: "FC60", "SHA-256", "API"
- Code snippets or terminal output
- These should be in the `KNOWN_EXCEPTIONS` list in the hardcoded string scanner

---

## HANDOFF TO SESSION 25

Session 24 provides Session 25 (and beyond) with:

1. **Complete i18n infrastructure** — Every component uses `t()`, both translation files are complete
2. **Formatting hooks** — `useFormattedNumber` and `useFormattedDate` ready for any component
3. **RTL CSS** — `rtl.css` imported and working for all pages
4. **Translation API** — `/translation/reading` and `/translation/batch` endpoints for on-demand translation
5. **Test suite** — Automated tests catch any regression in i18n coverage

Session 25 can focus on its own scope knowing that:

- Language switching works across the entire app
- Persian formatting is consistent everywhere
- RTL layout is verified and tested
- No hardcoded strings remain to be caught later

---

## NOTES

### Translation Quality

- Persian translations should use formal register (not colloquial)
- Use standard Iranian Persian, not Dari or Tajik variants
- Zero-width non-joiner (‌ U+200C) is essential for correct Persian compound words
- Example: "آزمایش‌شده" (tested) not "آزمایششده"

### Performance Consideration

- i18next loads all translations at startup (both en.json and fa.json are <50KB)
- No lazy loading needed at current scale
- If translation files exceed 200KB in future, consider namespace splitting

### Coordination with Session 18 (Feedback)

Session 18 adds `StarRating.tsx` and `ReadingFeedback.tsx` components.
The `feedback` section in translation files covers their strings.
If Session 18 hasn't run yet, create the feedback translation keys anyway —
the components will pick them up when they're built.

### Existing Oracle Translations

The oracle section in en.json/fa.json already has ~100 keys covering:

- Sign types, reading types, user management
- Form labels, placeholders, validation
- Results display, tabs, export

These should NOT be rewritten — only verified and extended if gaps exist.
