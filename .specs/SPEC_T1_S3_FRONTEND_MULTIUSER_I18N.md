# SPEC: Frontend Multi-User + Internationalization - T1-S3

**Estimated Duration:** 4-5 hours  
**Layer:** Layer 1 (Frontend)  
**Terminal:** Terminal 1  
**Phase:** T1-S3 (Multi-User + i18n)  
**Dependencies:** Terminal 1 Session 1 (Foundation), Terminal 2 Session 3 (Translation API)

---

## TL;DR

- Implementing multi-user selector UI (like email CC field) with primary/secondary user distinction
- Adding full internationalization support (English ↔ فارسی) with react-i18next
- Implementing RTL layout switching for Persian language
- Integrating translation button that calls /api/oracle/translate endpoint
- Persian number formatting (۱۲۳۴) and date formatting
- Validation: max 5 users, no duplicates, primary user required
- Complete test coverage for multi-user logic and i18n switching

---

## OBJECTIVE

Create a production-ready multi-user selector interface with full bilingual support (English/Persian) including RTL layout, proper Persian typography, and translation integration for Oracle readings.

---

## CONTEXT

**Current State:**
- Basic Oracle UI exists (from T1-S1)
- Translation API endpoint available at `/api/oracle/translate` (from T2-S3)
- Single-user Oracle readings working
- No internationalization support
- No multi-user selection capability

**What's Changing:**
- Adding multi-user selector component (CC field style)
- Implementing react-i18next for bilingual support
- Adding RTL layout for Persian
- Integrating translation feature in UI
- Persian number/date formatting

**Why:**
- Issue #2.15.1: Multi-user oracle readings
- Issue #2.11: Full internationalization support
- Issue #2.3: Translation integration
- User experience: Support Persian-speaking users
- Accessibility: Proper RTL support for right-to-left languages

---

## PREREQUISITES

**Completed Work:**
- [x] Terminal 1 Session 1: Frontend foundation completed (verified: React app runs)
- [x] Terminal 2 Session 3: Translation API implemented (verified: endpoint returns translations)

**Required Packages:**
- [x] React 18+ installed
- [x] TypeScript configured
- [ ] react-i18next (will install)
- [ ] i18next (will install)
- [ ] date-fns with locale support (for date formatting)

**Environment:**
- Node.js 18+ available
- API running at `http://localhost:8000`

---

## TOOLS TO USE

**Extended Thinking:**
- Multi-user selector component design (dropdown vs autocomplete)
- RTL layout strategy (CSS-only vs component-level)
- State management for user list (local vs context)
- Translation caching strategy

**Skills:**
- Primary: `/mnt/skills/public/frontend-design/SKILL.md` (React component patterns)
- Secondary: `/mnt/skills/examples/theme-factory/SKILL.md` (consistent styling)

**Subagents:**
- Subagent 1: Multi-User Selector Component
- Subagent 2: i18n Configuration + Language Toggle
- Subagent 3: RTL Layouts + Persian Formatting
- Subagent 4: Translation Integration
- Subagent 5: Tests

**MCP Servers:**
- None required (pure frontend work)

---

## REQUIREMENTS

### Functional Requirements

**Multi-User Selector (Issue #2.15.1):**
1. Primary user dropdown with all available users
2. "+ Add User" button to add secondary users
3. Secondary users displayed as removable chips/tags
4. Visual distinction: primary user highlighted/bolded
5. Remove button for each secondary user (X icon)
6. Validation:
   - Maximum 5 users total (1 primary + 4 secondary)
   - No duplicate users
   - Primary user required
7. UI similar to email CC field (compact, scannable)

**Internationalization (Issue #2.11):**
1. Language toggle button (EN ↔ FA) in header
2. All UI text translated (buttons, labels, placeholders, messages)
3. Language preference persists in localStorage
4. Translation files organized: `src/locales/en.json`, `src/locales/fa.json`
5. Persian language activates RTL layout
6. Persian number formatting: 1234 → ۱۲۳۴
7. Persian date formatting: proper Jalali calendar

**Translation Integration (Issue #2.3):**
1. "Translate" button appears when reading is in English
2. Calls `/api/oracle/translate` endpoint with reading text
3. Displays translated reading below original
4. Toggle between original and translation
5. Error handling for translation failures
6. Loading state during translation

**RTL Layout (Persian Support):**
1. Direction switches: `dir="rtl"` when Persian active
2. Text alignment: right-aligned for Persian
3. Layout mirroring: buttons/icons flip positions
4. Input fields: right-aligned text
5. Proper Persian font stack (Vazir, Samim, or system Persian fonts)

### Non-Functional Requirements

**Performance:**
- Language switch: <100ms
- Translation API call: <2s
- No layout shift during RTL toggle
- Smooth animations for user add/remove

**Quality:**
- Test coverage: 90%+ for new components
- TypeScript strict mode: no `any` types
- Accessibility: WCAG 2.1 AA for both languages
- Mobile responsive: works on 320px+ screens

**User Experience:**
- Clear visual feedback for all actions
- Intuitive user selection (no confusion)
- Graceful error messages in both languages
- Consistent theming in RTL mode

---

## IMPLEMENTATION PLAN

### Phase 1: i18n Foundation (60 minutes)

**Tasks:**

1. **Install i18n packages:**
   ```bash
   npm install react-i18next i18next i18next-browser-languagedetector
   npm install date-fns-jalali  # For Persian calendar
   ```

2. **Create i18n configuration:**
   - File: `src/i18n/config.ts`
   - Configure i18next with English/Persian resources
   - Set up language detector (localStorage → navigator)
   - Configure fallback language (English)

3. **Create translation files:**
   - `src/locales/en.json` - English translations
   - `src/locales/fa.json` - Persian translations (فارسی)
   - Initial keys: common UI text, Oracle page labels

4. **Wrap App with i18n provider:**
   - Modify `src/App.tsx`
   - Import and initialize i18next
   - Add `<I18nextProvider>` wrapper

**Files to Create:**
- `src/i18n/config.ts` - i18next configuration
- `src/locales/en.json` - English translations
- `src/locales/fa.json` - Persian translations
- `src/types/i18n.d.ts` - TypeScript definitions for i18next

**Verification:**
```bash
cd frontend/web-ui
npm install
npm run dev

# Open browser console:
# Type: i18next.changeLanguage('fa')
# Expected: UI should attempt to switch (even if not all text translated yet)
```

**Checkpoint:**
- [ ] i18next initialized without errors
- [ ] Translation files loaded (check Network tab)
- [ ] `useTranslation()` hook works in components
- [ ] Language change triggers re-render

**STOP if checkpoint fails** - Debug i18n setup before continuing

---

### Phase 2: Language Toggle + RTL (75 minutes)

**Tasks:**

1. **Create LanguageToggle component:**
   - File: `src/components/LanguageToggle.tsx`
   - Button to switch EN ↔ FA
   - Current language indicator
   - Persists choice in localStorage
   - Updates `dir` attribute on `<html>` element

2. **Add RTL CSS support:**
   - File: `src/styles/rtl.css`
   - RTL-specific overrides
   - Persian font stack: Vazir, Samim, Tahoma, Arial
   - Layout mirroring rules (flex-direction, text-align)
   - Direction-aware margin/padding

3. **Create Persian formatting utilities:**
   - File: `src/utils/persianFormatter.ts`
   - `toPersianNumber()` - converts 123 to ۱۲۳
   - `toPersianDate()` - converts Date to Jalali format
   - `toPersianDigits()` - for any numeric string

4. **Update App layout for RTL:**
   - Modify `src/App.tsx`
   - Add `dir` attribute binding based on language
   - Load RTL CSS when Persian active
   - Add LanguageToggle to header

5. **Translate existing Oracle page:**
   - Update `src/pages/Oracle.tsx`
   - Wrap all text with `t()` function
   - Add keys to en.json and fa.json
   - Test RTL layout

**Files to Create:**
- `src/components/LanguageToggle.tsx` - Language switcher component
- `src/styles/rtl.css` - RTL layout overrides
- `src/utils/persianFormatter.ts` - Persian number/date utilities

**Files to Modify:**
- `src/App.tsx` - Add dir attribute, LanguageToggle
- `src/pages/Oracle.tsx` - Replace hardcoded text with t()
- `src/locales/en.json` - Add Oracle page translations
- `src/locales/fa.json` - Add Persian translations

**Verification:**
```bash
npm run dev
# Open http://localhost:5173

# Test 1: Language Toggle
# - Click language toggle button
# Expected: UI switches to Persian (فارسی)

# Test 2: RTL Layout
# - Check that text is right-aligned
# - Check that buttons are on the right side
# - Inspect <html> element: should have dir="rtl"

# Test 3: Persian Numbers
# Open browser console:
# import { toPersianNumber } from './utils/persianFormatter'
# toPersianNumber(1234)
# Expected: '۱۲۳۴'
```

**Checkpoint:**
- [ ] Language toggle works (EN ↔ FA)
- [ ] RTL layout activates for Persian
- [ ] Persian font loads correctly
- [ ] Text alignment correct in both directions
- [ ] Numbers display in Persian digits
- [ ] localStorage persists language choice

**STOP if checkpoint fails** - Fix RTL issues before multi-user component

---

### Phase 3: Multi-User Selector Component (90 minutes)

**Tasks:**

1. **Create User type definition:**
   - File: `src/types/user.ts`
   - Interface for User object
   - Validation rules (max 5, no duplicates)

2. **Create MultiUserSelector component:**
   - File: `src/components/MultiUserSelector.tsx`
   - Primary user dropdown (select element)
   - "+ Add User" button
   - Secondary users list (chip/tag style)
   - Remove button for each secondary user
   - Visual distinction for primary user (bold, highlighted)
   - Validation logic (max 5, no duplicates)

3. **Style MultiUserSelector:**
   - File: `src/components/MultiUserSelector.module.css`
   - Email CC field aesthetic
   - Chip/tag styling for secondary users
   - Hover states, focus states
   - RTL support (flex-direction-aware)
   - Mobile responsive

4. **Add translations for multi-user UI:**
   - Update `src/locales/en.json`
   - Update `src/locales/fa.json`
   - Keys: "Primary User", "Add User", "Remove", "Max 5 users", etc.

5. **Integrate into Oracle page:**
   - Modify `src/pages/Oracle.tsx`
   - Replace single-user input with MultiUserSelector
   - Update state management for user list
   - Pass user list to API call (if applicable)

**Files to Create:**
- `src/types/user.ts` - User type definition
- `src/components/MultiUserSelector.tsx` - Main component
- `src/components/MultiUserSelector.module.css` - Styling
- `src/components/UserChip.tsx` - Secondary user chip component

**Files to Modify:**
- `src/pages/Oracle.tsx` - Integrate MultiUserSelector
- `src/locales/en.json` - Add multi-user translations
- `src/locales/fa.json` - Add Persian multi-user translations

**Verification:**
```bash
npm run dev

# Test 1: Add Users
# - Select primary user from dropdown
# - Click "+ Add User"
# - Select secondary user
# Expected: User appears as chip below primary

# Test 2: Remove Users
# - Click X on a secondary user chip
# Expected: User removed from list

# Test 3: Validation
# - Try to add 6th user
# Expected: Error message "Maximum 5 users allowed"

# - Try to add same user twice
# Expected: Error message "User already selected"

# Test 4: Primary User Distinction
# - Check primary user has different styling (bold, highlighted)

# Test 5: RTL Layout
# - Switch to Persian
# Expected: Multi-user selector mirrors layout (chips on right, buttons on left)
```

**Checkpoint:**
- [ ] Primary user dropdown works
- [ ] Secondary users add/remove correctly
- [ ] Maximum 5 users enforced
- [ ] No duplicate users allowed
- [ ] Primary user visually distinct
- [ ] RTL layout works for multi-user selector
- [ ] Responsive on mobile (320px+)

**STOP if checkpoint fails** - Fix multi-user logic before translation integration

---

### Phase 4: Translation Integration (60 minutes)

**Tasks:**

1. **Create Translation service:**
   - File: `src/services/translation.ts`
   - `translateText(text: string, targetLanguage: string)` function
   - Calls `/api/oracle/translate` endpoint
   - Error handling (network errors, API errors)
   - TypeScript interfaces for API request/response

2. **Add Translate button to Oracle reading:**
   - Modify `src/pages/Oracle.tsx`
   - "Translate" button appears when reading displayed
   - Button only shows if reading is in English
   - Loading state during translation
   - Display translated text below original
   - Toggle between original and translation

3. **Update UI for translation display:**
   - Create `src/components/TranslatedReading.tsx`
   - Shows original reading
   - Shows translated reading (if available)
   - Toggle button to switch display
   - Clear visual separation between original and translation

4. **Add translations for translation UI:**
   - Update `src/locales/en.json`
   - Update `src/locales/fa.json`
   - Keys: "Translate", "Original", "Translation", "Translating...", etc.

**Files to Create:**
- `src/services/translation.ts` - Translation API service
- `src/components/TranslatedReading.tsx` - Display translated readings

**Files to Modify:**
- `src/pages/Oracle.tsx` - Add translate button, integrate translation display
- `src/locales/en.json` - Add translation UI text
- `src/locales/fa.json` - Add Persian translation UI text

**Verification:**
```bash
npm run dev

# Test 1: Translation Button Appears
# - Get an Oracle reading (in English)
# Expected: "Translate" button appears below reading

# Test 2: Translation Request
# - Click "Translate" button
# Expected: 
#   - Button shows "Translating..." loading state
#   - API call to /api/oracle/translate (check Network tab)
#   - Translated text appears below original

# Test 3: Toggle Display
# - After translation loaded
# Expected: Can toggle between original and translated reading

# Test 4: Error Handling
# - Stop API server (docker-compose down)
# - Try to translate
# Expected: Error message "Translation failed. Please try again."

# Test 5: RTL Translation Display
# - Switch to Persian UI
# - Get translation
# Expected: Translation display works in RTL layout
```

**Checkpoint:**
- [ ] Translate button works
- [ ] API call to /api/oracle/translate succeeds
- [ ] Translated text displays correctly
- [ ] Toggle between original and translation works
- [ ] Loading state shows during translation
- [ ] Error handling works (network failure, API error)
- [ ] RTL layout correct for translation display

**STOP if checkpoint fails** - Debug translation integration before tests

---

### Phase 5: Tests (60 minutes)

**Tasks:**

1. **Test MultiUserSelector component:**
   - File: `src/components/MultiUserSelector.test.tsx`
   - Test: Add primary user
   - Test: Add secondary user
   - Test: Remove secondary user
   - Test: Validation - max 5 users
   - Test: Validation - no duplicates
   - Test: Primary user visually distinct
   - Test: Renders correctly in RTL

2. **Test LanguageToggle component:**
   - File: `src/components/LanguageToggle.test.tsx`
   - Test: Toggle from EN to FA
   - Test: Toggle from FA to EN
   - Test: Persists language in localStorage
   - Test: Updates HTML dir attribute

3. **Test Persian formatter utilities:**
   - File: `src/utils/persianFormatter.test.ts`
   - Test: `toPersianNumber()` - converts numbers correctly
   - Test: `toPersianDate()` - formats dates in Jalali
   - Test: Edge cases (empty, null, invalid)

4. **Test translation service:**
   - File: `src/services/translation.test.ts`
   - Test: Successful translation request
   - Test: Network error handling
   - Test: API error handling (500 response)
   - Test: Request format correct

5. **Integration test: Oracle page with multi-user + translation:**
   - File: `src/pages/Oracle.test.tsx`
   - Test: Oracle reading with multi-user selection
   - Test: Translation integration end-to-end
   - Test: RTL layout with multi-user and translation

**Files to Create:**
- `src/components/MultiUserSelector.test.tsx` - Multi-user selector tests
- `src/components/LanguageToggle.test.tsx` - Language toggle tests
- `src/utils/persianFormatter.test.ts` - Persian formatter tests
- `src/services/translation.test.ts` - Translation service tests
- `src/pages/Oracle.test.tsx` - Integration tests (expand existing)

**Verification:**
```bash
npm test

# Expected output:
# ✓ MultiUserSelector › adds primary user
# ✓ MultiUserSelector › adds secondary user
# ✓ MultiUserSelector › removes secondary user
# ✓ MultiUserSelector › enforces max 5 users
# ✓ MultiUserSelector › prevents duplicate users
# ✓ MultiUserSelector › primary user styling
# ✓ MultiUserSelector › RTL layout
# ✓ LanguageToggle › switches to Persian
# ✓ LanguageToggle › switches to English
# ✓ LanguageToggle › persists language
# ✓ LanguageToggle › updates dir attribute
# ✓ persianFormatter › converts numbers
# ✓ persianFormatter › formats dates
# ✓ translation service › successful translation
# ✓ translation service › handles network errors
# ✓ Oracle page › multi-user reading
# ✓ Oracle page › translation integration

# Test coverage:
npm run test:coverage

# Expected: 90%+ coverage for new components
```

**Checkpoint:**
- [ ] All tests pass (17/17)
- [ ] Test coverage â‰¥90% for new code
- [ ] No console warnings during tests
- [ ] Integration tests verify end-to-end flow

**STOP if checkpoint fails** - Fix failing tests before final verification

---

## VERIFICATION CHECKLIST

### Code Quality
- [ ] TypeScript strict mode: no `any` types
- [ ] All components have TypeScript interfaces
- [ ] Proper error handling (translation API, user validation)
- [ ] Logging for translation requests (console.debug)
- [ ] No hardcoded text (all via i18n `t()` function)

### Functionality
- [ ] Multi-user selector works (add, remove, validate)
- [ ] Language toggle works (EN ↔ FA)
- [ ] RTL layout activates for Persian
- [ ] Persian numbers display correctly (۱۲۳۴)
- [ ] Translation button calls API and displays result
- [ ] All validation rules enforced (max 5, no duplicates)

### User Experience
- [ ] Responsive design (320px - 1920px)
- [ ] Clear visual feedback for all actions
- [ ] Accessible (keyboard navigation works)
- [ ] Smooth animations (no jank)
- [ ] Error messages helpful and translated

### Internationalization
- [ ] All UI text translated (EN + FA)
- [ ] RTL layout correct (no broken layouts)
- [ ] Persian font loads properly
- [ ] Language persists in localStorage
- [ ] No layout shift during language switch

### Testing
- [ ] All unit tests pass (17/17)
- [ ] Integration tests pass
- [ ] Test coverage â‰¥90%
- [ ] Manual testing on multiple browsers (Chrome, Firefox, Safari)

### Performance
- [ ] Language switch <100ms
- [ ] Translation API call <2s
- [ ] No memory leaks (check DevTools)
- [ ] Lighthouse score >90 (mobile + desktop)

---

## SUCCESS CRITERIA

1. **Multi-User Selector Works:**
   - Can select 1 primary + up to 4 secondary users
   - Validation prevents >5 users and duplicates
   - Primary user visually distinct
   - Verified by: Manual test + automated tests

2. **Internationalization Complete:**
   - UI switches between English and Persian
   - RTL layout activates for Persian
   - Persian numbers formatted correctly (۱۲۳۴)
   - Language persists across page reloads
   - Verified by: Language toggle test + localStorage check

3. **Translation Integration Functional:**
   - Translate button appears for English readings
   - API call to /api/oracle/translate succeeds
   - Translated text displays correctly
   - Can toggle between original and translation
   - Verified by: End-to-end test + Network tab inspection

4. **Quality Standards Met:**
   - Test coverage â‰¥90% for new code
   - No TypeScript errors (`npm run type-check`)
   - No linting errors (`npm run lint`)
   - All tests pass (17/17)
   - Verified by: Test suite + coverage report

5. **RTL Support Proper:**
   - Layout mirrors correctly (buttons, inputs, chips)
   - Text right-aligned for Persian
   - No broken layouts in RTL mode
   - Persian font displays correctly
   - Verified by: Visual test in both languages

---

## HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

### Resume from Phase: [Current Phase Number]

**Context Needed:**
- Which phase was in progress?
- What files were created vs modified?
- Were tests written for completed phases?

**Verification Before Continuing:**
```bash
# Verify Phase 1 (i18n Foundation) completed:
npm run dev
# Check browser console: i18next should be initialized
# Try: i18next.changeLanguage('fa')

# Verify Phase 2 (Language Toggle + RTL) completed:
# Language toggle button should be visible
# Switching to Persian should activate RTL layout

# Verify Phase 3 (Multi-User Selector) completed:
# Multi-user selector should render on Oracle page
# Should be able to add/remove users

# Verify Phase 4 (Translation Integration) completed:
# Translate button should appear after Oracle reading
# Clicking should call API and display translation

# Verify Phase 5 (Tests) completed:
npm test
# All tests should pass
```

**Known Issues to Address:**
- If RTL layout broken: Check `dir` attribute on `<html>` element
- If translation fails: Verify API endpoint is running (Terminal 2)
- If tests fail: Check test data setup (mock users, mock API responses)

---

## NEXT STEPS (After This Spec)

### Immediate Next Actions:

1. **Telegram Bot Integration (T1-S4):**
   - Create Telegram notification component
   - Subscribe to Oracle events
   - Display readings in Telegram format

2. **Multi-User Oracle Logic (Backend T2-S4):**
   - Update Oracle service to handle multi-user readings
   - Generate personalized insights for each user
   - Combine insights into single reading

3. **Advanced Oracle Features (T1-S5):**
   - Oracle history view (past readings)
   - Favorite readings (bookmark feature)
   - Export readings (PDF, JSON)

### Future Enhancements:

- **More Languages:** Add Spanish, Arabic, Chinese
- **Voice Input:** Speak questions instead of typing
- **Theme Switching:** Light/dark mode per language
- **Offline Support:** PWA with service worker
- **Calendar Integration:** Jalali calendar picker for Persian dates

---

## FILES SUMMARY

### Files to Create (New):
1. `src/i18n/config.ts` - i18next configuration
2. `src/locales/en.json` - English translations
3. `src/locales/fa.json` - Persian translations
4. `src/types/i18n.d.ts` - i18next TypeScript definitions
5. `src/components/LanguageToggle.tsx` - Language switcher
6. `src/styles/rtl.css` - RTL layout overrides
7. `src/utils/persianFormatter.ts` - Persian formatting utilities
8. `src/types/user.ts` - User type definition
9. `src/components/MultiUserSelector.tsx` - Multi-user selector component
10. `src/components/MultiUserSelector.module.css` - Multi-user selector styling
11. `src/components/UserChip.tsx` - Secondary user chip component
12. `src/services/translation.ts` - Translation API service
13. `src/components/TranslatedReading.tsx` - Translation display component
14. `src/components/MultiUserSelector.test.tsx` - Multi-user tests
15. `src/components/LanguageToggle.test.tsx` - Language toggle tests
16. `src/utils/persianFormatter.test.ts` - Persian formatter tests
17. `src/services/translation.test.ts` - Translation service tests

### Files to Modify (Existing):
1. `src/App.tsx` - Add i18n provider, dir attribute, LanguageToggle
2. `src/pages/Oracle.tsx` - Integrate MultiUserSelector, translation
3. `package.json` - Add i18n dependencies

### Total Changes:
- **17 new files**
- **3 modified files**
- **~1,200 lines of code** (estimated)

---

## DEPENDENCIES GRAPH

```
Phase 1 (i18n Foundation)
    ↓
Phase 2 (Language Toggle + RTL)
    ↓
Phase 3 (Multi-User Selector) ← Can run parallel with Phase 4
    ↓
Phase 4 (Translation Integration) ← Can run parallel with Phase 3
    ↓
Phase 5 (Tests) ← Requires all previous phases
```

**Critical Path:** Phase 1 → Phase 2 → Phase 5  
**Parallel Work:** Phase 3 and Phase 4 can be done simultaneously if using subagents

---

## EXTENDED THINKING PROMPTS

**For Claude Code CLI execution, use extended thinking for:**

1. **Multi-User Component Design:**
   - Should we use dropdown or autocomplete for user selection?
   - How to handle large user lists (>50 users)?
   - Best UX pattern for removing users (X button vs trash icon)?

2. **RTL Strategy:**
   - CSS-only approach vs component-level props?
   - How to handle mixed LTR/RTL content (names in English, UI in Persian)?
   - Best way to flip icons/images in RTL?

3. **State Management:**
   - Local component state vs React Context for user list?
   - Where to store translation cache (memory vs localStorage)?
   - How to sync language preference across tabs?

4. **Translation Caching:**
   - Should we cache translations to avoid duplicate API calls?
   - How long to keep cached translations?
   - What cache invalidation strategy?

---

## RISK MITIGATION

**Potential Risks:**

1. **RTL Layout Breaks:** Some CSS frameworks don't support RTL well
   - **Mitigation:** Test early, use logical properties (inline-start vs left)

2. **Translation API Slow:** Network latency for translations
   - **Mitigation:** Add loading states, timeout after 5s, cache results

3. **Font Loading Issues:** Persian fonts may not load on all systems
   - **Mitigation:** Font stack with fallbacks (Vazir, Samim, Tahoma, system)

4. **Multi-User Complexity:** Complex state management for user list
   - **Mitigation:** Keep state simple (array), use TypeScript for type safety

5. **Test Coverage Gaps:** Hard to test RTL layouts
   - **Mitigation:** Manual testing + visual regression tests

---

## ACCEPTANCE TEST SCENARIOS

**Scenario 1: Multi-User Selection**
```
Given: Oracle page loaded
When: User selects primary user "Alice"
And: User clicks "+ Add User"
And: User selects secondary user "Bob"
Then: Both users should appear in selector
And: Primary user should be bold/highlighted
And: Bob should appear as removable chip
```

**Scenario 2: Language Switch**
```
Given: App in English
When: User clicks language toggle
Then: UI should switch to Persian (فارسی)
And: Layout should activate RTL (dir="rtl")
And: Text should be right-aligned
And: Numbers should display in Persian (۱۲۳۴)
And: Language preference should save to localStorage
```

**Scenario 3: Translation**
```
Given: Oracle reading in English
When: User clicks "Translate" button
Then: API should call /api/oracle/translate
And: Translated text should appear below original
And: User can toggle between original and translation
And: Loading state should show during translation
```

**Scenario 4: Validation**
```
Given: 5 users already selected
When: User tries to add 6th user
Then: Error message should display "Maximum 5 users allowed"
And: 6th user should not be added

Given: User "Alice" already selected
When: User tries to add "Alice" again
Then: Error message should display "User already selected"
And: Duplicate should not be added
```

---

## DEVELOPER NOTES

**For Claude Code CLI:**

1. **Use Subagents:** Phases 3 and 4 are independent and can run in parallel
2. **Extended Thinking:** Use for RTL strategy and state management decisions
3. **Incremental Testing:** Run tests after each phase (don't wait until Phase 5)
4. **Verify i18n Early:** Phase 1 must work before continuing (easy to break)
5. **Manual RTL Test:** Automated tests can't catch all RTL layout issues

**Common Pitfalls:**
- Forgetting to update translation files (en.json, fa.json)
- Using CSS properties that don't support RTL (margin-left vs margin-inline-start)
- Not handling loading states during translation
- Mixing hardcoded text with translated text

---

## CONFIDENCE LEVEL

**High (90%)** - Standard React patterns, well-documented libraries, clear requirements.

**Uncertainty:**
- RTL layout: 10% uncertainty (some edge cases may need manual fixes)
- Translation API reliability: 5% uncertainty (depends on Terminal 2 implementation)

---

*END OF SPECIFICATION*

**Ready for Claude Code CLI execution with Extended Thinking enabled.**

**Estimated Total Time:** 4-5 hours (if executed sequentially)  
**Estimated with Subagents:** 3-4 hours (Phases 3 & 4 parallel)
