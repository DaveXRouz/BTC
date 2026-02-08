# SPEC: Frontend Input Components - T1-S2
**Estimated Duration:** 4-5 hours  
**Layer:** Layer 1 (Frontend)  
**Terminal:** Terminal 1  
**Phase:** Phase 3 (Frontend Development)  
**Session:** T1-S2 (Specialized Input Components)

---

## TL;DR

- Creating 4 specialized input components for Oracle interface
- Persian virtual keyboard for Farsi name entry
- Dual-calendar date picker (Gregorian + Solar Hijri)
- Sign type selector with conditional formatters (Time, Number, Car Plate, Custom)
- Location selector with geolocation + manual entry + coordinate display
- All components fully typed, tested, and accessible
- Integration with Oracle page form (from T1-S1)

---

## OBJECTIVE

Create reusable, production-grade input components that enable users to enter Oracle consultation data with culturally appropriate interfaces (Persian keyboard, Solar Hijri calendar) and structured sign/location data.

---

## CONTEXT

**Current State:**
- T1-S1 completed: Project foundation, routing, basic Oracle page structure
- Oracle page has placeholder form inputs (name, birthday, question, sign, location)
- No specialized components for Persian input, calendar, sign types, or location

**What's Changing:**
- Replacing basic inputs with specialized components
- Adding Persian keyboard overlay for Farsi text entry
- Implementing dual-calendar date picker
- Creating sign type selector with conditional formatters
- Building location selector with geolocation + manual entry

**Why:**
- Oracle numerology analysis requires precise date/time data
- Persian/Farsi names need easy input method (virtual keyboard)
- Sign types (time, number, car plate) have different validation rules
- Location coordinates needed for astrological calculations

---

## PREREQUISITES

**From Previous Sessions:**
- [x] T1-S1 completed (verified: Oracle page renders)
- [x] React + TypeScript + Vite setup working
- [x] Tailwind CSS configured
- [x] React Router navigation functional

**External Dependencies:**
- [ ] Browser Geolocation API available (standard, no install needed)
- [ ] react-datepicker library (will install)
- [ ] @date-io/jalaali library for Persian calendar (will install)

**Verification Before Starting:**
```bash
cd frontend/web-ui
npm run dev
# Visit http://localhost:5173/oracle
# Expected: Oracle page renders with basic form
```

---

## TOOLS TO USE

**Extended Thinking:**
- Design decision: react-datepicker vs custom calendar implementation
- Persian keyboard layout design (standard vs simplified)
- Sign type validation logic architecture
- Geolocation error handling strategy

**Skills:**
- Primary: `/mnt/skills/public/frontend-design/SKILL.md` (read before starting)
- Optional: `/mnt/skills/examples/theme-factory/SKILL.md` (for dark theme consistency)

**Subagents:**
- Subagent 1: Persian Keyboard Component
- Subagent 2: Calendar Date Picker Component
- Subagent 3: Sign Type Selector Component
- Subagent 4: Location Selector Component
- Main Agent: Integration + Testing

**No MCP Servers Needed** (frontend-only work)

---

## REQUIREMENTS

### Functional Requirements

**FR1: Persian Virtual Keyboard**
- Displays Farsi character layout when activated
- Inserts characters at cursor position
- Works with name, mother's name, question fields
- Toggleable (show/hide)
- Accessible via keyboard icon button

**FR2: Calendar Date Picker**
- Supports Gregorian calendar (default)
- Supports Solar Hijri (Persian) calendar
- Visual calendar interface with month/year navigation
- Integrates with birthday field
- Stores as YYYY-MM-DD format
- Displays in localized format based on calendar type

**FR3: Sign Type Selector**
- Dropdown with 4 options: Time, Number, Car Plate, Custom
- Conditional input rendering based on selection:
  - **Time:** HH:MM time picker (24-hour format)
  - **Number:** Numeric input (any integer, no decimals)
  - **Car Plate:** Text input with Iranian plate pattern (e.g., "12A345-67")
  - **Custom:** Free text input
- Type-specific validation
- Error messages for invalid formats

**FR4: Location Selector**
- Auto-detect via browser geolocation API
- Manual selection: Country → City → Area dropdowns
- Display coordinates (latitude, longitude) after selection
- Store coordinates for API submission
- Error handling for geolocation denial
- Fallback to manual entry if geolocation fails

### Non-Functional Requirements

**Performance:**
- Keyboard component renders <50ms
- Calendar loads <100ms
- Geolocation request timeout: 5 seconds
- All components responsive (no lag on input)

**Accessibility:**
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader friendly (ARIA labels)
- Focus management (trap focus in keyboard modal)

**Quality:**
- TypeScript strict mode (no `any` types)
- Test coverage: 90%+ for each component
- Component prop validation
- Error boundaries for graceful failures

**User Experience:**
- Dark theme consistent with V3 aesthetic
- Clear visual feedback for selections
- Loading indicators for async operations (geolocation)
- Helpful error messages (not technical jargon)

---

## IMPLEMENTATION PLAN

### Phase 1: Setup & Dependencies (15 minutes)

**Tasks:**
1. Install required npm packages
2. Create component directory structure
3. Create utility functions folder
4. Set up test files

**Files to Create:**
```
frontend/web-ui/src/
├── components/
│   ├── PersianKeyboard/
│   │   ├── PersianKeyboard.tsx
│   │   ├── PersianKeyboard.test.tsx
│   │   └── index.ts
│   ├── CalendarPicker/
│   │   ├── CalendarPicker.tsx
│   │   ├── CalendarPicker.test.tsx
│   │   └── index.ts
│   ├── SignTypeSelector/
│   │   ├── SignTypeSelector.tsx
│   │   ├── SignTypeSelector.test.tsx
│   │   └── index.ts
│   └── LocationSelector/
│       ├── LocationSelector.tsx
│       ├── LocationSelector.test.tsx
│       └── index.ts
├── utils/
│   ├── persianKeyboardLayout.ts
│   ├── dateFormatters.ts
│   ├── signValidators.ts
│   └── geolocationHelpers.ts
```

**Commands:**
```bash
cd frontend/web-ui

# Install dependencies
npm install react-datepicker @date-io/jalaali
npm install --save-dev @types/react-datepicker

# Create directories
mkdir -p src/components/PersianKeyboard
mkdir -p src/components/CalendarPicker
mkdir -p src/components/SignTypeSelector
mkdir -p src/components/LocationSelector
mkdir -p src/utils

# Create placeholder files
touch src/components/PersianKeyboard/{PersianKeyboard.tsx,PersianKeyboard.test.tsx,index.ts}
touch src/components/CalendarPicker/{CalendarPicker.tsx,CalendarPicker.test.tsx,index.ts}
touch src/components/SignTypeSelector/{SignTypeSelector.tsx,SignTypeSelector.test.tsx,index.ts}
touch src/components/LocationSelector/{LocationSelector.tsx,LocationSelector.test.tsx,index.ts}
touch src/utils/{persianKeyboardLayout.ts,dateFormatters.ts,signValidators.ts,geolocationHelpers.ts}
```

**Verification:**
```bash
npm run dev
# Expected: No build errors, all files created
tree src/components src/utils
# Expected: Directory structure as shown above
```

**Checkpoint:**
- [ ] Dependencies installed successfully
- [ ] Directory structure created
- [ ] No TypeScript errors
- [ ] Dev server runs without errors

**STOP if checkpoint fails** - verify npm install completed, check for conflicts

---

### Phase 2: Persian Virtual Keyboard Component (60 minutes)

**Extended Thinking Decision:**
```
DECISION: Keyboard Layout Design

OPTIONS:
1. Full Persian QWERTY layout (32+ keys, standard)
2. Simplified layout (20 common characters + diacritics)
3. Phonetic layout (map to English keys)

EVALUATION:
- Users need full character set for proper Farsi names
- Simplified layout may miss uncommon but valid characters
- Phonetic layout confusing for native Farsi speakers

RECOMMENDATION: Option 1 (Full Persian QWERTY)
- Authentic experience for Farsi users
- Covers all valid Persian characters
- Standard layout familiar to Persian keyboard users
```

**Tasks:**

1. **Create Persian keyboard layout data**
   - File: `src/utils/persianKeyboardLayout.ts`
   - Standard Persian QWERTY layout
   - Include: Letters, numbers, common punctuation
   - Organize in rows (like physical keyboard)

2. **Build PersianKeyboard component**
   - File: `src/components/PersianKeyboard/PersianKeyboard.tsx`
   - Props: `onCharacterClick: (char: string) => void`, `onClose: () => void`
   - Render keyboard grid (3-4 rows)
   - Click handlers for each key
   - Close button (X in top right)
   - Dark theme styling
   - Focus trap (prevent tabbing out while open)

3. **Add keyboard toggle button**
   - Small keyboard icon button
   - Positioned near text input fields
   - Shows/hides keyboard component
   - Accessible (aria-label)

4. **Test component**
   - File: `src/components/PersianKeyboard/PersianKeyboard.test.tsx`
   - Test: Renders all characters
   - Test: Click inserts character
   - Test: Close button works
   - Test: Keyboard navigation

**Code Structure:**
```typescript
// src/utils/persianKeyboardLayout.ts
export const persianKeyboardLayout = {
  row1: ['ض', 'ص', 'ث', 'ق', 'ف', 'غ', 'ع', 'ه', 'خ', 'Ø­', 'ج', 'Ú†'],
  row2: ['ش', 'س', 'ÛŒ', 'ب', 'ل', 'ا', 'ت', 'ن', 'Ù…', 'Ú©', 'Ú¯'],
  row3: ['ظ', 'Ø·', 'Ø²', 'ر', 'Ø°', 'د', 'Ù¾', 'و', 'Û°', 'Û±', 'Û²', 'Û³'],
  row4: [' ', 'Ù‡', 'آ', 'ژ', 'ئ', 'ء']
};

// src/components/PersianKeyboard/PersianKeyboard.tsx
import React from 'react';
import { persianKeyboardLayout } from '@/utils/persianKeyboardLayout';

interface PersianKeyboardProps {
  onCharacterClick: (char: string) => void;
  onClose: () => void;
}

export const PersianKeyboard: React.FC<PersianKeyboardProps> = ({
  onCharacterClick,
  onClose
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-2xl">
        {/* Close button */}
        <button onClick={onClose} className="float-right text-white">✕</button>
        
        {/* Keyboard rows */}
        {Object.values(persianKeyboardLayout).map((row, idx) => (
          <div key={idx} className="flex gap-2 mb-2">
            {row.map((char) => (
              <button
                key={char}
                onClick={() => onCharacterClick(char)}
                className="bg-gray-700 text-white px-4 py-2 rounded hover:bg-gray-600"
              >
                {char}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Verification:**
```bash
cd frontend/web-ui
npm test -- PersianKeyboard.test.tsx
# Expected: All 4 tests pass

# Manual test:
npm run dev
# Visit http://localhost:5173/oracle
# Click keyboard icon → Keyboard appears
# Click Persian character → Character inserted
# Click X → Keyboard closes
```

**Acceptance Criteria:**
- [ ] Keyboard renders all Persian characters (32+ keys)
- [ ] Clicking character inserts into input field
- [ ] Close button dismisses keyboard
- [ ] Dark theme styling matches V3 aesthetic
- [ ] Focus trapped within keyboard when open
- [ ] Tests pass (4/4)

---

### Phase 3: Calendar Date Picker Component (75 minutes)

**Extended Thinking Decision:**
```
DECISION: Calendar Library Choice

OPTIONS:
1. react-datepicker (popular, Gregorian-focused, custom Persian difficult)
2. Custom implementation (full control, more work, reinventing wheel)
3. Hybrid: react-datepicker + jalaali converter (best of both)

EVALUATION:
- react-datepicker battle-tested, accessible
- Custom implementation: 3-5 hours extra work
- Hybrid allows dual calendar with minimal custom code

RECOMMENDATION: Option 3 (Hybrid)
- Use react-datepicker for UI/interaction
- Use @date-io/jalaali for Persian date conversion
- Toggle between calendars with button
- Store as ISO format (YYYY-MM-DD) internally
```

**Tasks:**

1. **Create date formatter utilities**
   - File: `src/utils/dateFormatters.ts`
   - Function: `gregorianToJalaali(date: Date): string`
   - Function: `jalaaliToGregorian(jalaaliDate: string): Date`
   - Function: `formatDateDisplay(date: Date, type: 'gregorian' | 'jalaali'): string`

2. **Build CalendarPicker component**
   - File: `src/components/CalendarPicker/CalendarPicker.tsx`
   - Props: `value: Date | null`, `onChange: (date: Date) => void`, `calendarType?: 'gregorian' | 'jalaali'`
   - Dual calendar toggle button
   - react-datepicker integration
   - Display in appropriate format based on calendar type
   - Store as ISO YYYY-MM-DD

3. **Style calendar for dark theme**
   - Custom CSS for react-datepicker
   - Dark background, light text
   - Highlighted current date
   - Hover states

4. **Test component**
   - File: `src/components/CalendarPicker/CalendarPicker.test.tsx`
   - Test: Renders with Gregorian calendar
   - Test: Switches to Jalaali calendar
   - Test: Date selection updates value
   - Test: Displays correct format for each calendar type

**Code Structure:**
```typescript
// src/utils/dateFormatters.ts
import { DateConverter } from '@date-io/jalaali';

const jalaaliConverter = new DateConverter();

export const gregorianToJalaali = (date: Date): string => {
  return jalaaliConverter.format(date, 'jYYYY/jMM/jDD');
};

export const jalaaliToGregorian = (jalaaliDate: string): Date => {
  return jalaaliConverter.date(jalaaliDate) as Date;
};

export const formatDateDisplay = (
  date: Date,
  type: 'gregorian' | 'jalaali'
): string => {
  if (type === 'jalaali') {
    return gregorianToJalaali(date);
  }
  return date.toLocaleDateString('en-US'); // MM/DD/YYYY
};

// src/components/CalendarPicker/CalendarPicker.tsx
import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { formatDateDisplay } from '@/utils/dateFormatters';

interface CalendarPickerProps {
  value: Date | null;
  onChange: (date: Date) => void;
  calendarType?: 'gregorian' | 'jalaali';
}

export const CalendarPicker: React.FC<CalendarPickerProps> = ({
  value,
  onChange,
  calendarType = 'gregorian'
}) => {
  const [activeCalendar, setActiveCalendar] = useState(calendarType);

  return (
    <div className="space-y-2">
      {/* Calendar type toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveCalendar('gregorian')}
          className={`px-3 py-1 rounded ${
            activeCalendar === 'gregorian' ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          Gregorian
        </button>
        <button
          onClick={() => setActiveCalendar('jalaali')}
          className={`px-3 py-1 rounded ${
            activeCalendar === 'jalaali' ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          Solar Hijri
        </button>
      </div>

      {/* Date display */}
      <div className="text-sm text-gray-400">
        {value ? formatDateDisplay(value, activeCalendar) : 'No date selected'}
      </div>

      {/* Date picker */}
      <DatePicker
        selected={value}
        onChange={onChange}
        dateFormat="yyyy-MM-dd"
        className="bg-gray-700 text-white px-4 py-2 rounded w-full"
        calendarClassName="dark-calendar"
      />
    </div>
  );
};
```

**Custom CSS for dark theme:**
```css
/* Add to src/index.css or component styles */
.dark-calendar {
  background-color: #1f2937;
  border: 1px solid #374151;
}

.react-datepicker__header {
  background-color: #111827;
  border-bottom: 1px solid #374151;
}

.react-datepicker__current-month,
.react-datepicker__day-name {
  color: #f3f4f6;
}

.react-datepicker__day {
  color: #d1d5db;
}

.react-datepicker__day:hover {
  background-color: #374151;
}

.react-datepicker__day--selected {
  background-color: #2563eb;
}
```

**Verification:**
```bash
npm test -- CalendarPicker.test.tsx
# Expected: All 4 tests pass

# Manual test:
npm run dev
# Visit Oracle page
# Click calendar field
# Toggle between Gregorian/Jalaali → Display changes
# Select date → Value updates
# Check stored format: YYYY-MM-DD
```

**Acceptance Criteria:**
- [ ] Both calendar types render correctly
- [ ] Toggle switches display format
- [ ] Date selection updates parent component
- [ ] Stores as ISO YYYY-MM-DD internally
- [ ] Dark theme styling applied
- [ ] Tests pass (4/4)

---

### Phase 4: Sign Type Selector Component (60 minutes)

**Extended Thinking Decision:**
```
DECISION: Sign Type Validation Strategy

OPTIONS:
1. Client-side only validation (fast, can be bypassed)
2. Client + server validation (robust, slower)
3. Client-side with strict type enforcement (TypeScript unions)

EVALUATION:
- This is Oracle input, not security-critical
- User experience benefits from immediate feedback
- Server will validate anyway (Layer 2 API)
- TypeScript ensures type safety at compile time

RECOMMENDATION: Option 3 (Client-side + TypeScript)
- Immediate validation feedback
- Type-safe sign data
- Server validation as safety net (Layer 2)
```

**Tasks:**

1. **Create sign validators**
   - File: `src/utils/signValidators.ts`
   - Function: `validateTime(time: string): boolean`
   - Function: `validateNumber(num: string): boolean`
   - Function: `validateCarPlate(plate: string): boolean`
   - Error message generators

2. **Build SignTypeSelector component**
   - File: `src/components/SignTypeSelector/SignTypeSelector.tsx`
   - Props: `value: SignData`, `onChange: (data: SignData) => void`
   - Type: `SignData = { type: 'time' | 'number' | 'carplate' | 'custom', value: string }`
   - Dropdown for sign type selection
   - Conditional input rendering based on type
   - Real-time validation with error display
   - Clear error messages

3. **Implement type-specific inputs**
   - **Time:** HH:MM input with validation (00:00 - 23:59)
   - **Number:** Numeric input (integers only, no max)
   - **Car Plate:** Text with Iranian pattern (e.g., "12A345-67")
   - **Custom:** Free text (no validation)

4. **Test component**
   - File: `src/components/SignTypeSelector/SignTypeSelector.test.tsx`
   - Test: Type switching renders correct input
   - Test: Time validation (valid/invalid formats)
   - Test: Number validation (rejects decimals/letters)
   - Test: Car plate validation (pattern matching)
   - Test: Custom input accepts any text

**Code Structure:**
```typescript
// src/utils/signValidators.ts
export const validateTime = (time: string): { valid: boolean; error?: string } => {
  const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
  if (!timeRegex.test(time)) {
    return { valid: false, error: 'Invalid time format. Use HH:MM (00:00 - 23:59)' };
  }
  return { valid: true };
};

export const validateNumber = (num: string): { valid: boolean; error?: string } => {
  const numRegex = /^-?\d+$/;
  if (!numRegex.test(num)) {
    return { valid: false, error: 'Must be a whole number (no decimals)' };
  }
  return { valid: true };
};

export const validateCarPlate = (plate: string): { valid: boolean; error?: string } => {
  // Iranian pattern: 2 digits + 1 letter + 3 digits + - + 2 digits
  // Example: 12A345-67
  const plateRegex = /^\d{2}[A-Z]\d{3}-\d{2}$/;
  if (!plateRegex.test(plate)) {
    return { 
      valid: false, 
      error: 'Invalid car plate format. Use: 12A345-67' 
    };
  }
  return { valid: true };
};

// src/components/SignTypeSelector/SignTypeSelector.tsx
import React, { useState } from 'react';
import { validateTime, validateNumber, validateCarPlate } from '@/utils/signValidators';

export type SignType = 'time' | 'number' | 'carplate' | 'custom';

export interface SignData {
  type: SignType;
  value: string;
}

interface SignTypeSelectorProps {
  value: SignData;
  onChange: (data: SignData) => void;
}

export const SignTypeSelector: React.FC<SignTypeSelectorProps> = ({
  value,
  onChange
}) => {
  const [error, setError] = useState<string>('');

  const handleTypeChange = (newType: SignType) => {
    onChange({ type: newType, value: '' });
    setError('');
  };

  const handleValueChange = (newValue: string) => {
    // Validate based on type
    let validation = { valid: true, error: '' };
    
    switch (value.type) {
      case 'time':
        validation = validateTime(newValue);
        break;
      case 'number':
        validation = validateNumber(newValue);
        break;
      case 'carplate':
        validation = validateCarPlate(newValue);
        break;
      // 'custom' has no validation
    }

    setError(validation.error || '');
    onChange({ ...value, value: newValue });
  };

  return (
    <div className="space-y-3">
      {/* Sign type dropdown */}
      <select
        value={value.type}
        onChange={(e) => handleTypeChange(e.target.value as SignType)}
        className="bg-gray-700 text-white px-4 py-2 rounded w-full"
      >
        <option value="time">Time Sign</option>
        <option value="number">Number Sign</option>
        <option value="carplate">Car Plate Sign</option>
        <option value="custom">Custom Sign</option>
      </select>

      {/* Conditional input based on type */}
      {value.type === 'time' && (
        <input
          type="time"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          className="bg-gray-700 text-white px-4 py-2 rounded w-full"
          placeholder="HH:MM"
        />
      )}

      {value.type === 'number' && (
        <input
          type="text"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          className="bg-gray-700 text-white px-4 py-2 rounded w-full"
          placeholder="Enter any number"
        />
      )}

      {value.type === 'carplate' && (
        <input
          type="text"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value.toUpperCase())}
          className="bg-gray-700 text-white px-4 py-2 rounded w-full"
          placeholder="12A345-67"
        />
      )}

      {value.type === 'custom' && (
        <input
          type="text"
          value={value.value}
          onChange={(e) => handleValueChange(e.target.value)}
          className="bg-gray-700 text-white px-4 py-2 rounded w-full"
          placeholder="Enter custom sign"
        />
      )}

      {/* Error display */}
      {error && (
        <p className="text-red-400 text-sm">{error}</p>
      )}
    </div>
  );
};
```

**Verification:**
```bash
npm test -- SignTypeSelector.test.tsx
# Expected: All 5 tests pass

# Manual test:
npm run dev
# Switch sign types → Input changes
# Enter "25:00" in time → Error shown
# Enter "12.5" in number → Error shown
# Enter "ABC123" in car plate → Error shown
# Enter "12A345-67" → No error
```

**Acceptance Criteria:**
- [ ] All 4 sign types selectable
- [ ] Correct input rendered for each type
- [ ] Time validation rejects invalid formats
- [ ] Number validation rejects non-integers
- [ ] Car plate validation enforces pattern
- [ ] Custom accepts any text
- [ ] Error messages clear and helpful
- [ ] Tests pass (5/5)

---

### Phase 5: Location Selector Component (90 minutes)

**Extended Thinking Decision:**
```
DECISION: Geolocation + Manual Entry Strategy

OPTIONS:
1. Geolocation only (fails if user denies)
2. Manual only (tedious for most users)
3. Geolocation first, fallback to manual (best UX)

EVALUATION:
- Browser geolocation has ~70% acceptance rate
- Manual entry needed as fallback
- Coordinates required for Oracle calculations
- API integration for coordinate lookup (manual mode)

RECOMMENDATION: Option 3 (Geolocation + Manual Fallback)
- Auto-detect when possible (fast, accurate)
- Manual selector if geolocation fails/denied
- Both modes store coordinates
- Clear user feedback for each mode
```

**Tasks:**

1. **Create geolocation helper utilities**
   - File: `src/utils/geolocationHelpers.ts`
   - Function: `getCurrentPosition(): Promise<{lat: number, lon: number}>`
   - Function: `getCityFromCoordinates(lat, lon): Promise<string>`
   - Error handling for geolocation denial
   - Timeout handling (5 seconds)

2. **Build LocationSelector component**
   - File: `src/components/LocationSelector/LocationSelector.tsx`
   - Props: `value: LocationData | null`, `onChange: (data: LocationData) => void`
   - Type: `LocationData = { lat: number, lon: number, city?: string, country?: string }`
   - Auto-detect button (uses geolocation API)
   - Manual mode: Country → City → Area cascading dropdowns
   - Display coordinates after selection
   - Loading states for async operations
   - Error handling UI

3. **Implement manual location selector**
   - Hardcoded country list (top 20 countries)
   - City data from API (mock for now, Layer 2 will provide)
   - Coordinate lookup from API (mock for now)
   - Cascading dropdown logic

4. **Test component**
   - File: `src/components/LocationSelector/LocationSelector.test.tsx`
   - Test: Auto-detect triggers geolocation
   - Test: Geolocation success updates coordinates
   - Test: Geolocation error shows fallback
   - Test: Manual selection updates coordinates
   - Test: Coordinates display correctly

**Code Structure:**
```typescript
// src/utils/geolocationHelpers.ts
export interface Coordinates {
  lat: number;
  lon: number;
}

export const getCurrentPosition = (): Promise<Coordinates> => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported by browser'));
      return;
    }

    const timeoutId = setTimeout(() => {
      reject(new Error('Geolocation request timed out'));
    }, 5000); // 5 second timeout

    navigator.geolocation.getCurrentPosition(
      (position) => {
        clearTimeout(timeoutId);
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
      },
      (error) => {
        clearTimeout(timeoutId);
        reject(error);
      }
    );
  });
};

export const getCityFromCoordinates = async (
  lat: number,
  lon: number
): Promise<string> => {
  // TODO: Replace with actual API call to Layer 2
  // Mock implementation for now
  return `City at ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
};

// src/components/LocationSelector/LocationSelector.tsx
import React, { useState } from 'react';
import { getCurrentPosition, getCityFromCoordinates } from '@/utils/geolocationHelpers';

export interface LocationData {
  lat: number;
  lon: number;
  city?: string;
  country?: string;
}

interface LocationSelectorProps {
  value: LocationData | null;
  onChange: (data: LocationData) => void;
}

const COUNTRIES = [
  'United States', 'United Kingdom', 'Iran', 'Canada', 'Germany',
  'France', 'Australia', 'Japan', 'India', 'Brazil'
  // Add more as needed
];

export const LocationSelector: React.FC<LocationSelectorProps> = ({
  value,
  onChange
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [mode, setMode] = useState<'auto' | 'manual'>('auto');
  const [selectedCountry, setSelectedCountry] = useState<string>('');

  const handleAutoDetect = async () => {
    setLoading(true);
    setError('');
    
    try {
      const coords = await getCurrentPosition();
      const city = await getCityFromCoordinates(coords.lat, coords.lon);
      
      onChange({
        lat: coords.lat,
        lon: coords.lon,
        city: city
      });
      setMode('auto');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Geolocation failed');
      setMode('manual'); // Fallback to manual
    } finally {
      setLoading(false);
    }
  };

  const handleManualSelect = (country: string) => {
    setSelectedCountry(country);
    // TODO: Fetch cities for this country from API
    // TODO: Allow city selection
    // TODO: Get coordinates from API for selected city
    
    // Mock coordinates for now
    onChange({
      lat: 35.6892, // Example: Tokyo
      lon: 139.6917,
      country: country,
      city: 'Example City'
    });
  };

  return (
    <div className="space-y-4">
      {/* Mode selection */}
      <div className="flex gap-2">
        <button
          onClick={handleAutoDetect}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? 'Detecting...' : '📍 Auto-Detect Location'}
        </button>
        <button
          onClick={() => setMode('manual')}
          className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
        >
          Manual Entry
        </button>
      </div>

      {/* Error display */}
      {error && (
        <p className="text-red-400 text-sm">
          {error} - Please use manual entry.
        </p>
      )}

      {/* Manual mode selector */}
      {mode === 'manual' && (
        <div className="space-y-3">
          <select
            value={selectedCountry}
            onChange={(e) => handleManualSelect(e.target.value)}
            className="bg-gray-700 text-white px-4 py-2 rounded w-full"
          >
            <option value="">Select Country</option>
            {COUNTRIES.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>

          {/* TODO: Add city selector after country selection */}
          {/* TODO: Add area selector after city selection */}
        </div>
      )}

      {/* Coordinates display */}
      {value && (
        <div className="bg-gray-700 p-4 rounded">
          <p className="text-sm text-gray-300">Coordinates:</p>
          <p className="text-white font-mono">
            Lat: {value.lat.toFixed(6)}, Lon: {value.lon.toFixed(6)}
          </p>
          {value.city && (
            <p className="text-sm text-gray-400 mt-1">
              {value.city}{value.country ? `, ${value.country}` : ''}
            </p>
          )}
        </div>
      )}
    </div>
  );
};
```

**Verification:**
```bash
npm test -- LocationSelector.test.tsx
# Expected: All 5 tests pass

# Manual test:
npm run dev
# Click "Auto-Detect" → Browser prompts for permission
# Allow → Coordinates display
# Deny → Fallback to manual mode
# Select country → Coordinates update
# Verify coordinates display with 6 decimal precision
```

**Acceptance Criteria:**
- [ ] Auto-detect triggers geolocation API
- [ ] Geolocation success displays coordinates
- [ ] Geolocation error falls back to manual
- [ ] Manual country selection works
- [ ] Coordinates display with 6 decimal places
- [ ] Loading states shown during async operations
- [ ] Error messages clear and actionable
- [ ] Tests pass (5/5)

---

### Phase 6: Integration with Oracle Page (45 minutes)

**Tasks:**

1. **Update Oracle page to use new components**
   - File: `src/pages/Oracle.tsx`
   - Replace basic inputs with new components
   - Add Persian keyboard toggle for name fields
   - Wire up calendar picker for birthday
   - Integrate sign type selector
   - Add location selector
   - State management for all form fields

2. **Create form submission handler**
   - Collect all form data
   - Validate before submission
   - Format for API (mock for now, Layer 2 will consume)
   - Show success/error messages

3. **Add loading states**
   - Disable submit while processing
   - Show spinner during submission
   - Clear form after success

4. **Test full integration**
   - Fill out entire form
   - Verify all components work together
   - Check data format matches API expectations
   - Test edge cases (empty fields, invalid inputs)

**Code Structure:**
```typescript
// src/pages/Oracle.tsx (updated)
import React, { useState } from 'react';
import { PersianKeyboard } from '@/components/PersianKeyboard';
import { CalendarPicker } from '@/components/CalendarPicker';
import { SignTypeSelector, SignData } from '@/components/SignTypeSelector';
import { LocationSelector, LocationData } from '@/components/LocationSelector';

interface OracleFormData {
  name: string;
  motherName: string;
  birthday: Date | null;
  question: string;
  sign: SignData;
  location: LocationData | null;
}

export const Oracle: React.FC = () => {
  const [formData, setFormData] = useState<OracleFormData>({
    name: '',
    motherName: '',
    birthday: null,
    question: '',
    sign: { type: 'time', value: '' },
    location: null
  });
  
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [keyboardTarget, setKeyboardTarget] = useState<'name' | 'motherName' | 'question'>('name');
  const [submitting, setSubmitting] = useState(false);

  const handleKeyboardInsert = (char: string) => {
    setFormData(prev => ({
      ...prev,
      [keyboardTarget]: prev[keyboardTarget] + char
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    // Validate all required fields
    if (!formData.name || !formData.birthday || !formData.sign.value || !formData.location) {
      alert('Please fill all required fields');
      setSubmitting(false);
      return;
    }

    // Format data for API
    const apiData = {
      name: formData.name,
      mother_name: formData.motherName,
      birthday: formData.birthday.toISOString().split('T')[0], // YYYY-MM-DD
      question: formData.question,
      sign_type: formData.sign.type,
      sign_value: formData.sign.value,
      latitude: formData.location.lat,
      longitude: formData.location.lon
    };

    console.log('Submitting to API:', apiData);
    
    // TODO: Replace with actual API call (Layer 2)
    await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay
    
    alert('Oracle consultation submitted!');
    setSubmitting(false);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Oracle Consultation</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name field with keyboard */}
        <div>
          <label className="block text-sm mb-2">Name *</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="flex-1 bg-gray-700 px-4 py-2 rounded"
              required
            />
            <button
              type="button"
              onClick={() => {
                setKeyboardTarget('name');
                setShowKeyboard(true);
              }}
              className="bg-gray-600 px-3 py-2 rounded"
              aria-label="Show Persian keyboard"
            >
              ⌨️
            </button>
          </div>
        </div>

        {/* Mother's name field with keyboard */}
        <div>
          <label className="block text-sm mb-2">Mother's Name</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={formData.motherName}
              onChange={(e) => setFormData({ ...formData, motherName: e.target.value })}
              className="flex-1 bg-gray-700 px-4 py-2 rounded"
            />
            <button
              type="button"
              onClick={() => {
                setKeyboardTarget('motherName');
                setShowKeyboard(true);
              }}
              className="bg-gray-600 px-3 py-2 rounded"
              aria-label="Show Persian keyboard"
            >
              ⌨️
            </button>
          </div>
        </div>

        {/* Birthday with calendar */}
        <div>
          <label className="block text-sm mb-2">Birthday *</label>
          <CalendarPicker
            value={formData.birthday}
            onChange={(date) => setFormData({ ...formData, birthday: date })}
          />
        </div>

        {/* Question field with keyboard */}
        <div>
          <label className="block text-sm mb-2">Question</label>
          <div className="flex gap-2">
            <textarea
              value={formData.question}
              onChange={(e) => setFormData({ ...formData, question: e.target.value })}
              className="flex-1 bg-gray-700 px-4 py-2 rounded"
              rows={3}
            />
            <button
              type="button"
              onClick={() => {
                setKeyboardTarget('question');
                setShowKeyboard(true);
              }}
              className="bg-gray-600 px-3 py-2 rounded"
              aria-label="Show Persian keyboard"
            >
              ⌨️
            </button>
          </div>
        </div>

        {/* Sign type selector */}
        <div>
          <label className="block text-sm mb-2">Sign *</label>
          <SignTypeSelector
            value={formData.sign}
            onChange={(sign) => setFormData({ ...formData, sign })}
          />
        </div>

        {/* Location selector */}
        <div>
          <label className="block text-sm mb-2">Location *</label>
          <LocationSelector
            value={formData.location}
            onChange={(location) => setFormData({ ...formData, location })}
          />
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded font-semibold disabled:opacity-50"
        >
          {submitting ? 'Submitting...' : 'Get Oracle Reading'}
        </button>
      </form>

      {/* Persian keyboard modal */}
      {showKeyboard && (
        <PersianKeyboard
          onCharacterClick={handleKeyboardInsert}
          onClose={() => setShowKeyboard(false)}
        />
      )}
    </div>
  );
};
```

**Verification:**
```bash
npm run dev
# Visit http://localhost:5173/oracle

# Full workflow test:
1. Enter name (Persian keyboard)
2. Enter mother's name (Persian keyboard)
3. Select birthday (both calendars)
4. Enter question (Persian keyboard)
5. Select sign type → Enter sign value
6. Auto-detect OR manually select location
7. Submit form → Check console for formatted data

# Expected: All fields populated, submit works, data formatted correctly
```

**Acceptance Criteria:**
- [ ] All 4 components integrated in Oracle page
- [ ] Persian keyboard works for name/mother name/question
- [ ] Calendar picker updates birthday field
- [ ] Sign selector validates before submission
- [ ] Location selector provides coordinates
- [ ] Form submission collects all data
- [ ] Data format matches API expectations (Layer 2)
- [ ] Loading states work during submission
- [ ] Success/error messages display

---

### Phase 7: Testing & Quality Assurance (30 minutes)

**Tasks:**

1. **Run full test suite**
   - All component tests
   - Integration tests
   - Coverage report

2. **Manual testing checklist**
   - Component isolation tests
   - Full form workflow
   - Edge cases (empty, invalid, extreme values)
   - Accessibility (keyboard navigation, screen reader)
   - Responsive design (mobile, tablet, desktop)

3. **Performance testing**
   - Component render times
   - Keyboard responsiveness
   - Calendar load time
   - Geolocation timeout handling

4. **Fix any issues found**
   - Prioritize critical bugs
   - Document known limitations
   - Create TODO list for future enhancements

**Test Commands:**
```bash
# Unit tests
npm test -- --coverage

# Type checking
npm run type-check

# Linting
npm run lint

# Build verification
npm run build

# Manual testing
npm run dev
```

**Verification:**
```bash
npm test -- --coverage
# Expected: 90%+ coverage across all components

npm run build
# Expected: Production build succeeds, no errors

# Lighthouse audit
lighthouse http://localhost:5173/oracle --output html
# Expected: Performance >90, Accessibility >95
```

**Quality Checklist:**
- [ ] All tests pass (18+ total)
- [ ] Coverage â‰¥90% for all components
- [ ] No TypeScript errors
- [ ] No linting errors
- [ ] Production build succeeds
- [ ] Lighthouse performance >90
- [ ] Lighthouse accessibility >95
- [ ] All acceptance criteria met from previous phases
- [ ] No console errors in browser
- [ ] Works on Chrome, Firefox, Safari

---

## SUCCESS CRITERIA

**All of these must be true:**

1. âœ… **Persian Keyboard Component**
   - All 32+ Persian characters render
   - Click-to-insert works in all target fields
   - Close button dismisses keyboard
   - Focus trapped within keyboard when open
   - Dark theme styling consistent
   - Tests pass (4/4)

2. âœ… **Calendar Picker Component**
   - Both Gregorian and Jalaali calendars work
   - Toggle switches display format correctly
   - Date selection updates parent component
   - Stores as YYYY-MM-DD internally
   - Displays in localized format
   - Dark theme styling applied
   - Tests pass (4/4)

3. âœ… **Sign Type Selector Component**
   - All 4 sign types selectable (time, number, carplate, custom)
   - Correct input rendered for each type
   - Time validation rejects invalid formats (e.g., 25:00)
   - Number validation rejects non-integers (e.g., 12.5)
   - Car plate validation enforces Iranian pattern
   - Custom input accepts any text
   - Error messages clear and actionable
   - Tests pass (5/5)

4. âœ… **Location Selector Component**
   - Auto-detect triggers geolocation API
   - Geolocation success displays coordinates
   - Geolocation error falls back to manual mode
   - Manual country selection works
   - Coordinates display with 6 decimal precision
   - Loading states shown during async operations
   - Error messages helpful
   - Tests pass (5/5)

5. âœ… **Oracle Page Integration**
   - All components integrated successfully
   - Form submission collects all data
   - Data formatted correctly for API (Layer 2)
   - Loading states work during submission
   - Validation prevents invalid submissions
   - Success/error messages display

6. âœ… **Quality Gates**
   - Test coverage â‰¥90% overall
   - All TypeScript strict mode (no `any`)
   - No linting errors
   - Production build succeeds
   - Lighthouse performance >90
   - Accessibility >95
   - Works on desktop + mobile

---

## VERIFICATION CHECKLIST

### 2-Minute Quick Check

**Terminal 1:**
```bash
cd frontend/web-ui

# Run all tests
npm test -- --coverage
# Expected: 18+ tests pass, 90%+ coverage

# Type check
npm run type-check
# Expected: 0 errors

# Lint
npm run lint
# Expected: 0 errors

# Build
npm run build
# Expected: Build succeeds
```

**Terminal 2:**
```bash
# Start dev server
npm run dev
# Visit http://localhost:5173/oracle

# Test workflow:
1. Click keyboard icon → Persian keyboard appears
2. Click Persian character → Inserted into field
3. Click calendar → Both calendars work
4. Switch calendar type → Display changes
5. Select sign type → Input changes
6. Enter invalid sign value → Error shown
7. Click auto-detect → Geolocation prompt
8. Allow geolocation → Coordinates display
9. Submit form with all fields → Success message

# Expected: All steps work without errors
```

### Comprehensive Verification

- [ ] All 4 components render without errors
- [ ] Persian keyboard inserts all characters correctly
- [ ] Calendar supports both Gregorian and Jalaali
- [ ] Sign type validation works for all 4 types
- [ ] Location auto-detect works (if permission granted)
- [ ] Location manual fallback works
- [ ] Form submission validates all required fields
- [ ] API data format matches Layer 2 expectations
- [ ] Dark theme consistent across all components
- [ ] Responsive on mobile (320px width)
- [ ] Accessible (keyboard navigation works)
- [ ] No console errors
- [ ] Tests pass (18/18)
- [ ] Coverage â‰¥90%

---

## HANDOFF TO NEXT SESSION

**If session ends mid-implementation:**

**Resume from Phase:** [Indicate current phase]

**Context Needed:**
- Which components are complete (verified with tests)
- Which components are in progress (% complete)
- Any blocking issues or decisions needed
- Current test coverage status

**Verification Before Continuing:**
```bash
# Check what's complete
npm test -- --coverage
# Review output to see which tests exist/pass

# Check Oracle page state
npm run dev
# Visit http://localhost:5173/oracle
# Verify which components are integrated
```

**Files to Review:**
- `src/components/*/` - Check which components exist
- `src/pages/Oracle.tsx` - Check integration status
- `src/utils/*Validators.ts` - Check validation logic

---

## NEXT STEPS (After This Session)

1. **Terminal 2 Session 4: Oracle API Endpoints**
   - Create `/api/oracle/reading` endpoint
   - Integrate FC60 numerology engine
   - Accept form data from Oracle page (this session's output)
   - Return formatted Oracle reading

2. **Terminal 1 Session 3: Oracle Results Display**
   - Create OracleReading component
   - Display FC60 signature
   - Display numerology analysis
   - Display Oracle wisdom interpretation
   - Format for user-friendly reading

3. **Terminal 3 Session 5: Oracle Pattern Analysis**
   - Implement pattern analysis in Oracle service
   - Query successful wallet findings
   - Analyze numerology correlations
   - Generate lucky range suggestions for Scanner

---

## DEPENDENCIES

**This Session Depends On:**
- T1-S1: Foundation (Oracle page structure exists)

**Other Sessions Depend On This:**
- T2-S4: Oracle API (needs form data format from this session)
- T1-S3: Oracle Results Display (uses same components for display)

---

## ESTIMATED TIMELINE

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 1. Setup & Dependencies | 15 min | 15 min |
| 2. Persian Keyboard | 60 min | 75 min |
| 3. Calendar Picker | 75 min | 150 min |
| 4. Sign Type Selector | 60 min | 210 min |
| 5. Location Selector | 90 min | 300 min |
| 6. Oracle Page Integration | 45 min | 345 min |
| 7. Testing & QA | 30 min | 375 min |
| **TOTAL** | **6.25 hours** | |

**Buffer:** Add 30-60 minutes for unexpected issues.

---

## CONFIDENCE LEVEL

**High (90%)** - All components are standard patterns with clear requirements. Extended thinking used for key decisions. Skills consulted. Phase-gated approach with verification checkpoints ensures quality.

**Risk Areas:**
- Persian calendar integration (mitigated: using battle-tested library)
- Geolocation permission denial (mitigated: fallback to manual)
- Form validation complexity (mitigated: type-safe validators)

---

*End of Specification*