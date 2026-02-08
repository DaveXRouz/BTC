# T1-S4: Frontend Results Display + Integration — Session Handoff

## Completed Work

### What was done

Completed the Oracle frontend by wiring API integration, building a tabbed results display, adding collapsible reading history, and implementing client-side export.

### Files Created (9)

| File                                                      | Purpose                                                                                  |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `src/hooks/useOracleReadings.ts`                          | React Query hooks: useSubmitReading, useSubmitQuestion, useSubmitName, useReadingHistory |
| `src/components/oracle/SummaryTab.tsx`                    | Summary view with type badges, quick stats, TranslatedReading                            |
| `src/components/oracle/DetailsTab.tsx`                    | Detailed view with collapsible sections (FC60, Numerology, Zodiac, Chinese, Letters)     |
| `src/components/oracle/ReadingHistory.tsx`                | Paginated history with filter chips and inline expansion                                 |
| `src/components/oracle/ExportButton.tsx`                  | Client-side TXT/JSON export via Blob download                                            |
| `src/components/oracle/ReadingResults.tsx`                | Tabbed container (Summary/Details/History) with eager rendering                          |
| `src/components/oracle/__tests__/SummaryTab.test.tsx`     | 5 tests                                                                                  |
| `src/components/oracle/__tests__/DetailsTab.test.tsx`     | 4 tests                                                                                  |
| `src/components/oracle/__tests__/ReadingHistory.test.tsx` | 6 tests                                                                                  |
| `src/components/oracle/__tests__/ReadingResults.test.tsx` | 6 tests                                                                                  |

### Files Modified (6)

| File                                                              | Changes                                                                                          |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `src/types/index.ts`                                              | Added ConsultationResult, StoredReading, StoredReadingListResponse, ResultsTab                   |
| `src/services/api.ts`                                             | Added oracle.history() and oracle.getReading() methods                                           |
| `src/locales/en.json`                                             | +37 new oracle i18n keys                                                                         |
| `src/locales/fa.json`                                             | +37 new oracle i18n keys (Persian)                                                               |
| `src/components/oracle/OracleConsultationForm.tsx`                | Added onResult prop, replaced console.log with real API calls, added error display               |
| `src/pages/Oracle.tsx`                                            | Replaced string state with ConsultationResult, replaced placeholder sections with ReadingResults |
| `src/pages/__tests__/Oracle.test.tsx`                             | Updated for new tabbed structure, added API mock                                                 |
| `src/components/oracle/__tests__/OracleConsultationForm.test.tsx` | Added onResult prop to all render calls                                                          |

## Key Decisions

1. **ConsultationResult union type** — Discriminated union (`type: "reading" | "question" | "name"`) enables type-safe rendering in all tab components
2. **Eager tab rendering** — All tabs render simultaneously (hidden via CSS `hidden` class) to preserve scroll/expansion state when switching tabs
3. **Client-side export** — No backend endpoint needed; Blob + URL.createObjectURL handles TXT and JSON downloads
4. **ReadingHistory uses React Query** — Pagination via offset param, filter chips map to `sign_type` query param
5. **userId param unused in form** — Backend `ReadingRequest` only accepts `{datetime, extended}`, not `user_id`. Prefixed with underscore for future use

## Verification Results

- `npx tsc --noEmit` — 0 errors
- `npx vitest run` — 110 tests passed (16 files), 0 failures
- `npm run build` — Build succeeds (323 KB JS, 15 KB CSS)

## What's Next

- **T1-S5**: Name cipher tab integration (wire oracle.name() to a dedicated UI)
- **T2-S4**: Backend stored readings — wire `user_id` into reading persistence
- **T5**: Full React frontend build (Dashboard, Scanner, Vault, Learning, Settings pages)
