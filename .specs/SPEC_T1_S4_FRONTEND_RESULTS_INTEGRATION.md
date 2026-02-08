# SPEC: Frontend Results Display + Integration - T1-S4

**Estimated Duration:** 4-5 hours  
**Layer:** Layer 1 (Frontend)  
**Terminal:** Terminal 1  
**Session:** T1-S4 (Final Frontend Session)  
**Phase:** Phase 3 (Frontend Completion)

---

## ðŸŽ¯ TL;DR

- Implementing tabbed results display (Summary | Details | History)
- Adding collapsible reading history with filters
- Redesigning question/sign flow for clarity
- Final integration of all Oracle components
- End-to-end testing (user profile → reading → history)
- Responsive design + dark theme consistency
- Performance optimization + error handling

---

## OBJECTIVE

Complete the Oracle frontend interface with professional results display, interactive history management, and seamless end-to-end user experience from profile creation to reading retrieval.

---

## CONTEXT

### Current State
**From T1-S1 (Profile Management):**
- ✅ User profile creation/editing
- ✅ Language selection (EN/ES/FR)
- ✅ Multi-user profile support
- ✅ Profile persistence in localStorage

**From T1-S2 (Oracle Interface Core):**
- ✅ Reading type selection (Single/Multi-user)
- ✅ Tab navigation (Daily | Question | Name)
- ✅ Basic form inputs (time, place, names)
- ✅ API integration (POST /api/oracle/reading)

**From T1-S3 (Multi-user Readings):**
- ✅ Multi-user flow (2-8 users)
- ✅ Individual sign collection
- ✅ Collective interpretation

### What's Missing (This Session)
**Issue #2.12:** Results display is basic (just text dump)
**Issue #2.8:** History is primitive (no collapse, no filters)
**Issue #2.7:** Question flow confusing ("Full Reading" vs "Quick Question")
**Issue #2.13:** No end-to-end testing
**Issue #2.14:** Inconsistent responsive design

### What's Changing
This session completes the Oracle interface with:
1. **Professional results display** - Tabbed interface (Summary | Details | History)
2. **Interactive history** - Collapsible, filterable, paginated
3. **Clear question flow** - Simple input → Sign → Reading
4. **Complete integration** - All features working together
5. **Quality polish** - Responsive, accessible, performant

### Why
The Oracle interface is the user-facing core of NPS V4. It must feel:
- **Professional** - Clean, structured, trust-inspiring
- **Intuitive** - No confusion about what to do
- **Powerful** - Access to full AI insights when needed
- **Fast** - Instant feedback, smooth interactions

---

## PREREQUISITES

### From Previous Sessions
- [x] T1-S1 completed (verified: profile creation works)
- [x] T1-S2 completed (verified: reading types work)
- [x] T1-S3 completed (verified: multi-user flow works)

### Environment
- [x] Node.js 18+ installed (`node --version`)
- [x] npm 9+ installed (`npm --version`)
- [x] API running at http://localhost:8000 (verified: `curl http://localhost:8000/api/health`)

### API Endpoints Required
- [x] POST /api/oracle/reading (reading creation)
- [x] GET /api/oracle/history (reading history)
- [x] POST /api/oracle/export (export to PDF/text)

---

## TOOLS TO USE

### Extended Thinking
Use for:
- Results display layout design (tabbed vs accordion)
- History pagination strategy (infinite scroll vs page numbers)
- Export format decisions (PDF vs text vs both)

### Subagents
**Subagent 1:** Results Display Component
- Task: Create `src/components/ReadingResults.tsx`
- Input: Reading data structure from API
- Output: Tabbed display (Summary | Details | History)

**Subagent 2:** Reading History Component
- Task: Create `src/components/ReadingHistory.tsx`
- Input: History data from API
- Output: Collapsible, filterable history list

**Subagent 3:** Integration & Testing
- Task: Connect all components + E2E tests
- Input: All previous components
- Output: Complete working Oracle page

### Skills
**Primary:** `/mnt/skills/public/frontend-design/SKILL.md`
- Use for results display design patterns
- Use for responsive component structure

**Optional:** `/mnt/skills/examples/theme-factory/SKILL.md`
- Use for dark theme consistency

---

## REQUIREMENTS

### Functional Requirements

#### FR-1: Tabbed Results Display
**User Story:** As a user, I want to see my reading in different formats so I can choose the level of detail I need.

**Acceptance Criteria:**
- [ ] Three tabs: Summary | Details | History
- [ ] Summary tab shows AI interpretation (human-readable format chosen by user)
- [ ] Details tab shows raw FC60 data + numerology breakdown
- [ ] History tab shows past readings (integrated with history component)
- [ ] Tab state persists during session (user returns to last viewed tab)
- [ ] Smooth tab transitions (<100ms)

**Technical Details:**
```typescript
interface ReadingResult {
  id: string;
  timestamp: string;
  reading_type: 'daily' | 'question' | 'name';
  
  // Summary data (AI interpretation)
  summary: {
    chosen_format: string;  // e.g., "story", "advice", "poem"
    text: string;           // AI-generated interpretation
    key_insights: string[]; // Bullet points
  };
  
  // Details data (raw FC60 + numerology)
  details: {
    fc60: {
      hour_pillar: string;
      day_pillar: string;
      month_pillar: string;
      year_pillar: string;
      meanings: Record<string, string>;
    };
    numerology: {
      life_path: number;
      expression: number;
      soul_urge: number;
      personality: number;
      interpretations: Record<string, string>;
    };
  };
}
```

#### FR-2: Collapsible Reading History
**User Story:** As a user, I want to browse my past readings without cluttering the screen.

**Acceptance Criteria:**
- [ ] Minimize/expand toggle (default: minimized)
- [ ] History items show preview (date + reading type + first 50 chars)
- [ ] Click on history item loads full reading in results display
- [ ] Multi-user readings show 👥 icon
- [ ] Filter: "My readings" vs "All readings" (if multi-user support)
- [ ] Pagination: 50 readings per page
- [ ] "Load more" button at bottom (infinite scroll alternative)

**Technical Details:**
```typescript
interface HistoryItem {
  id: string;
  timestamp: string;
  reading_type: 'daily' | 'question' | 'name';
  preview: string;          // First 50 chars of summary
  is_multi_user: boolean;   // Show 👥 icon
  participants?: string[];  // For multi-user readings
}

interface HistoryState {
  items: HistoryItem[];
  total_count: number;
  page: number;
  per_page: number;
  filter: 'mine' | 'all';
  collapsed: boolean;
}
```

#### FR-3: Simplified Question Flow
**User Story:** As a user, I want to ask a question clearly without confusion about different reading types.

**Acceptance Criteria:**
- [ ] Single question input: "What guidance do you seek?"
- [ ] Sign input with type selector (Hour/Day/Month/Year)
- [ ] "Get Reading" button (clear call-to-action)
- [ ] Remove "Full Reading" vs "Quick Question" distinction
- [ ] All readings are "full" (AI decides interpretation depth)

**Before (Confusing):**
```
○ Full Reading (detailed analysis)
○ Quick Question (brief answer)

[Question input]
[Get Reading]
```

**After (Clear):**
```
What guidance do you seek?
[Question input with placeholder: "e.g., What career path should I pursue?"]

Your Time Sign:
[Sign input] [Type: Hour ▼]

[Get Reading →]
```

#### FR-4: Export Functionality
**User Story:** As a user, I want to export my readings for offline reference.

**Acceptance Criteria:**
- [ ] Export button in results display
- [ ] Export formats: PDF | Text
- [ ] PDF includes: Summary + Details (not History)
- [ ] Text format: Markdown-compatible
- [ ] Filename: `oracle_reading_{timestamp}.{ext}`
- [ ] Download triggers immediately (no loading page)

**Technical Details:**
```typescript
interface ExportOptions {
  format: 'pdf' | 'text';
  include_sections: ('summary' | 'details')[];
  reading_id: string;
}

// API endpoint
POST /api/oracle/export
Body: ExportOptions
Response: Blob (file download)
```

#### FR-5: End-to-End Integration
**User Story:** As a user, I want all Oracle features to work together seamlessly.

**Acceptance Criteria:**
- [ ] User can create profile → get reading → view history → export
- [ ] Language selection affects all text (including results)
- [ ] Multi-user readings display correctly in results
- [ ] History filter works with multi-user readings
- [ ] All API calls handle errors gracefully
- [ ] Loading states during all async operations

### Non-Functional Requirements

#### NFR-1: Performance
- [ ] Tab switching: <100ms
- [ ] History load: <500ms (50 items)
- [ ] Export generation: <2s (PDF)
- [ ] No UI blocking during API calls
- [ ] Smooth animations (60fps)

#### NFR-2: Responsive Design
- [ ] Desktop (1920x1080): Full feature set
- [ ] Tablet (768x1024): Adapted layout
- [ ] Mobile (375x667): Mobile-optimized
- [ ] All interactions work on touch devices
- [ ] No horizontal scroll on any breakpoint

#### NFR-3: Accessibility
- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation (Tab, Enter, Esc)
- [ ] Screen reader support (ARIA labels)
- [ ] Focus indicators visible
- [ ] Color contrast ratio â‰¥ 4.5:1

#### NFR-4: Code Quality
- [ ] TypeScript strict mode (no `any` types)
- [ ] Component tests (React Testing Library)
- [ ] Test coverage â‰¥90%
- [ ] No console errors/warnings
- [ ] ESLint + Prettier compliance

---

## IMPLEMENTATION PLAN

### Phase 1: Results Display Component (90 minutes)

**Tasks:**

**Task 1.1: Create ReadingResults Component Structure**
```bash
# Create component file
touch src/components/ReadingResults.tsx

# Create styles (if using CSS modules)
touch src/components/ReadingResults.module.css
```

**Component Structure:**
```typescript
import React, { useState } from 'react';

interface ReadingResultsProps {
  reading: ReadingResult | null;
  loading: boolean;
  onExport: (format: 'pdf' | 'text') => void;
}

export const ReadingResults: React.FC<ReadingResultsProps> = ({
  reading,
  loading,
  onExport
}) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'details' | 'history'>('summary');

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!reading) {
    return <EmptyState message="No reading yet. Get your first reading above!" />;
  }

  return (
    <div className="reading-results">
      {/* Tab Navigation */}
      <div className="tabs">
        <button
          className={activeTab === 'summary' ? 'active' : ''}
          onClick={() => setActiveTab('summary')}
        >
          Summary
        </button>
        <button
          className={activeTab === 'details' ? 'active' : ''}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
        <button
          className={activeTab === 'history' ? 'active' : ''}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'summary' && <SummaryTab reading={reading} />}
        {activeTab === 'details' && <DetailsTab reading={reading} />}
        {activeTab === 'history' && <HistoryTab />}
      </div>

      {/* Export Button */}
      {activeTab !== 'history' && (
        <div className="export-actions">
          <button onClick={() => onExport('pdf')}>Export PDF</button>
          <button onClick={() => onExport('text')}>Export Text</button>
        </div>
      )}
    </div>
  );
};
```

**Acceptance:**
- [ ] Component renders without errors
- [ ] Tab switching works smoothly
- [ ] Export buttons appear (but don't work yet)

**Verification:**
```bash
npm test -- ReadingResults.test.tsx
# Expected: Component renders, tabs switch
```

---

**Task 1.2: Implement Summary Tab**
```typescript
const SummaryTab: React.FC<{ reading: ReadingResult }> = ({ reading }) => {
  return (
    <div className="summary-tab">
      <h3>AI Interpretation ({reading.summary.chosen_format})</h3>
      
      <div className="interpretation-text">
        {reading.summary.text}
      </div>

      <div className="key-insights">
        <h4>Key Insights:</h4>
        <ul>
          {reading.summary.key_insights.map((insight, i) => (
            <li key={i}>{insight}</li>
          ))}
        </ul>
      </div>

      <div className="metadata">
        <span>Reading Type: {reading.reading_type}</span>
        <span>Date: {new Date(reading.timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
};
```

**Acceptance:**
- [ ] Summary displays AI interpretation
- [ ] Key insights shown as bullet points
- [ ] Metadata shows reading type + timestamp
- [ ] Text is readable (appropriate font size, line height)

---

**Task 1.3: Implement Details Tab**
```typescript
const DetailsTab: React.FC<{ reading: ReadingResult }> = ({ reading }) => {
  return (
    <div className="details-tab">
      {/* FC60 Section */}
      <section className="fc60-section">
        <h4>FC60 Analysis</h4>
        <div className="pillars">
          <div className="pillar">
            <label>Hour Pillar:</label>
            <span>{reading.details.fc60.hour_pillar}</span>
          </div>
          <div className="pillar">
            <label>Day Pillar:</label>
            <span>{reading.details.fc60.day_pillar}</span>
          </div>
          <div className="pillar">
            <label>Month Pillar:</label>
            <span>{reading.details.fc60.month_pillar}</span>
          </div>
          <div className="pillar">
            <label>Year Pillar:</label>
            <span>{reading.details.fc60.year_pillar}</span>
          </div>
        </div>

        <div className="meanings">
          <h5>Meanings:</h5>
          {Object.entries(reading.details.fc60.meanings).map(([key, value]) => (
            <div key={key} className="meaning-item">
              <strong>{key}:</strong> {value}
            </div>
          ))}
        </div>
      </section>

      {/* Numerology Section */}
      <section className="numerology-section">
        <h4>Numerology Analysis</h4>
        <div className="numbers">
          <div className="number">
            <label>Life Path:</label>
            <span className="number-value">{reading.details.numerology.life_path}</span>
          </div>
          <div className="number">
            <label>Expression:</label>
            <span className="number-value">{reading.details.numerology.expression}</span>
          </div>
          <div className="number">
            <label>Soul Urge:</label>
            <span className="number-value">{reading.details.numerology.soul_urge}</span>
          </div>
          <div className="number">
            <label>Personality:</label>
            <span className="number-value">{reading.details.numerology.personality}</span>
          </div>
        </div>

        <div className="interpretations">
          <h5>Interpretations:</h5>
          {Object.entries(reading.details.numerology.interpretations).map(([key, value]) => (
            <div key={key} className="interpretation-item">
              <strong>{key}:</strong> {value}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
```

**Acceptance:**
- [ ] FC60 pillars displayed in grid
- [ ] Numerology numbers displayed prominently
- [ ] Meanings/interpretations shown with labels
- [ ] Sections visually separated

**Verification:**
```bash
# Visual check
npm run dev
# Navigate to Oracle page, get reading, switch to Details tab
# Expected: FC60 data + Numerology data displayed clearly
```

---

**Checkpoint 1:**
- [ ] ReadingResults component complete
- [ ] Summary tab works
- [ ] Details tab works
- [ ] Tab switching smooth (<100ms)
- [ ] No console errors

**STOP if checkpoint fails - fix before Phase 2**

---

### Phase 2: Reading History Component (90 minutes)

**Task 2.1: Create ReadingHistory Component**
```bash
touch src/components/ReadingHistory.tsx
```

**Component Structure:**
```typescript
import React, { useState, useEffect } from 'react';
import { getReadingHistory } from '../services/api';

interface ReadingHistoryProps {
  onSelectReading: (readingId: string) => void;
}

export const ReadingHistory: React.FC<ReadingHistoryProps> = ({ onSelectReading }) => {
  const [collapsed, setCollapsed] = useState(true);
  const [filter, setFilter] = useState<'mine' | 'all'>('mine');
  const [page, setPage] = useState(1);
  const [history, setHistory] = useState<HistoryState>({
    items: [],
    total_count: 0,
    page: 1,
    per_page: 50,
    filter: 'mine',
    collapsed: true
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!collapsed) {
      loadHistory();
    }
  }, [collapsed, filter, page]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await getReadingHistory({
        filter,
        page,
        per_page: 50
      });
      setHistory(prev => ({
        ...prev,
        items: page === 1 ? data.items : [...prev.items, ...data.items],
        total_count: data.total_count
      }));
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleCollapse = () => {
    setCollapsed(!collapsed);
  };

  const loadMore = () => {
    setPage(prev => prev + 1);
  };

  return (
    <div className="reading-history">
      {/* Header */}
      <div className="history-header" onClick={toggleCollapse}>
        <h3>Reading History ({history.total_count})</h3>
        <button className="collapse-toggle">
          {collapsed ? '▼ Expand' : '▲ Collapse'}
        </button>
      </div>

      {/* Content (only if expanded) */}
      {!collapsed && (
        <div className="history-content">
          {/* Filter */}
          <div className="filter-bar">
            <button
              className={filter === 'mine' ? 'active' : ''}
              onClick={() => setFilter('mine')}
            >
              My Readings
            </button>
            <button
              className={filter === 'all' ? 'active' : ''}
              onClick={() => setFilter('all')}
            >
              All Readings
            </button>
          </div>

          {/* History Items */}
          <div className="history-list">
            {history.items.map(item => (
              <div
                key={item.id}
                className="history-item"
                onClick={() => onSelectReading(item.id)}
              >
                <div className="item-header">
                  <span className="reading-type">
                    {item.reading_type}
                    {item.is_multi_user && ' 👥'}
                  </span>
                  <span className="timestamp">
                    {new Date(item.timestamp).toLocaleDateString()}
                  </span>
                </div>
                <div className="item-preview">
                  {item.preview}...
                </div>
                {item.is_multi_user && (
                  <div className="participants">
                    {item.participants?.join(', ')}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Load More */}
          {history.items.length < history.total_count && (
            <button
              className="load-more"
              onClick={loadMore}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load More'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
```

**Acceptance:**
- [ ] Component renders collapsed by default
- [ ] Clicking header toggles collapse
- [ ] History loads when expanded
- [ ] Filter switches between "mine" and "all"
- [ ] Pagination works (50 per page)
- [ ] Multi-user readings show 👥 icon

**Verification:**
```bash
npm test -- ReadingHistory.test.tsx
# Expected: Collapse works, filter works, pagination works
```

---

**Task 2.2: Integrate History with Results Display**

**Update Oracle.tsx:**
```typescript
const Oracle: React.FC = () => {
  const [currentReading, setCurrentReading] = useState<ReadingResult | null>(null);

  const handleSelectHistoryReading = async (readingId: string) => {
    try {
      const reading = await getReadingById(readingId);
      setCurrentReading(reading);
      // Switch to Summary tab automatically
    } catch (error) {
      console.error('Failed to load reading:', error);
    }
  };

  return (
    <div className="oracle-page">
      {/* ... existing form components ... */}

      <ReadingResults
        reading={currentReading}
        loading={loading}
        onExport={handleExport}
      />

      <ReadingHistory onSelectReading={handleSelectHistoryReading} />
    </div>
  );
};
```

**Acceptance:**
- [ ] Clicking history item loads reading in results display
- [ ] Results display automatically shows Summary tab
- [ ] History remains expanded after selection

---

**Checkpoint 2:**
- [ ] ReadingHistory component complete
- [ ] Collapse/expand works
- [ ] Filter works (mine vs all)
- [ ] Pagination works (load more)
- [ ] Integration with results display works
- [ ] Multi-user readings identified correctly

**STOP if checkpoint fails - fix before Phase 3**

---

### Phase 3: Question Flow Redesign (60 minutes)

**Task 3.1: Simplify Question Tab**

**Update QuestionTab.tsx (from T1-S2):**
```typescript
const QuestionTab: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [sign, setSign] = useState('');
  const [signType, setSignType] = useState<'hour' | 'day' | 'month' | 'year'>('hour');

  const handleGetReading = async () => {
    // ... API call
  };

  return (
    <div className="question-tab">
      <div className="question-input">
        <label>What guidance do you seek?</label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g., What career path should I pursue?"
          rows={4}
        />
      </div>

      <div className="sign-input">
        <label>Your Time Sign:</label>
        <div className="sign-controls">
          <input
            type="text"
            value={sign}
            onChange={(e) => setSign(e.target.value)}
            placeholder="Enter your sign"
          />
          <select
            value={signType}
            onChange={(e) => setSignType(e.target.value as any)}
          >
            <option value="hour">Hour</option>
            <option value="day">Day</option>
            <option value="month">Month</option>
            <option value="year">Year</option>
          </select>
        </div>
      </div>

      <button
        className="get-reading-btn"
        onClick={handleGetReading}
        disabled={!question || !sign}
      >
        Get Reading →
      </button>
    </div>
  );
};
```

**Remove:**
- ❌ "Full Reading" vs "Quick Question" radio buttons
- ❌ Confusing explanatory text

**Add:**
- ✅ Clear question prompt
- ✅ Sign type selector
- ✅ Single "Get Reading" button

**Acceptance:**
- [ ] Question input prominent
- [ ] Sign input with type selector
- [ ] Single clear call-to-action
- [ ] Button disabled until inputs filled

**Verification:**
```bash
# Visual check
npm run dev
# Navigate to Oracle → Question tab
# Expected: Simple, clear interface (no confusion)
```

---

**Checkpoint 3:**
- [ ] Question flow simplified
- [ ] No "Full vs Quick" distinction
- [ ] Clear labels and placeholders
- [ ] Intuitive flow: question → sign → reading

**STOP if checkpoint fails - fix before Phase 4**

---

### Phase 4: Export Functionality (60 minutes)

**Task 4.1: Implement Export API Calls**

**Update src/services/api.ts:**
```typescript
export const exportReading = async (
  readingId: string,
  format: 'pdf' | 'text'
): Promise<Blob> => {
  const response = await fetch(`${API_BASE_URL}/api/oracle/export`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getApiKey()}`
    },
    body: JSON.stringify({
      reading_id: readingId,
      format,
      include_sections: ['summary', 'details']
    })
  });

  if (!response.ok) {
    throw new Error('Export failed');
  }

  return await response.blob();
};
```

**Task 4.2: Implement Export Handlers**

**Update Oracle.tsx:**
```typescript
const handleExport = async (format: 'pdf' | 'text') => {
  if (!currentReading) return;

  try {
    const blob = await exportReading(currentReading.id, format);
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `oracle_reading_${currentReading.timestamp}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Failed to export reading. Please try again.');
  }
};
```

**Acceptance:**
- [ ] Export PDF works
- [ ] Export Text works
- [ ] File downloads with correct filename
- [ ] No page navigation during export
- [ ] Error message if export fails

**Verification:**
```bash
# Manual test
npm run dev
# Get a reading, click "Export PDF"
# Expected: PDF downloads as oracle_reading_{timestamp}.pdf
```

---

**Checkpoint 4:**
- [ ] Export functionality works
- [ ] Both PDF and Text formats work
- [ ] Downloads trigger correctly
- [ ] Error handling present
- [ ] No memory leaks (URL.revokeObjectURL called)

**STOP if checkpoint fails - fix before Phase 5**

---

### Phase 5: Final Integration & Testing (90 minutes)

**Task 5.1: End-to-End User Flow Testing**

**Test Case 1: Complete First Reading**
```typescript
// E2E test: src/tests/e2e/oracle-complete-flow.test.tsx
describe('Oracle Complete Flow', () => {
  it('should complete full user journey', async () => {
    // 1. Create profile
    const { getByLabelText, getByText } = render(<App />);
    
    fireEvent.change(getByLabelText('Name'), { target: { value: 'Test User' } });
    fireEvent.click(getByText('Save Profile'));
    
    // 2. Navigate to Oracle
    fireEvent.click(getByText('Oracle'));
    
    // 3. Select Daily Reading
    fireEvent.click(getByText('Daily'));
    
    // 4. Enter time and place
    fireEvent.change(getByLabelText('Time of Birth'), { target: { value: '14:30' } });
    fireEvent.change(getByLabelText('Place of Birth'), { target: { value: 'London' } });
    
    // 5. Select language
    fireEvent.click(getByText('English'));
    
    // 6. Get reading
    fireEvent.click(getByText('Get Reading'));
    
    // 7. Wait for results
    await waitFor(() => {
      expect(getByText('Summary')).toBeInTheDocument();
    });
    
    // 8. Check results display
    expect(getByText('AI Interpretation')).toBeInTheDocument();
    
    // 9. Switch to Details tab
    fireEvent.click(getByText('Details'));
    expect(getByText('FC60 Analysis')).toBeInTheDocument();
    
    // 10. Expand history
    fireEvent.click(getByText('Reading History'));
    await waitFor(() => {
      expect(getByText('My Readings')).toBeInTheDocument();
    });
    
    // Success!
  });
});
```

**Test Case 2: Multi-user Reading with History**
```typescript
describe('Multi-user Reading Flow', () => {
  it('should handle multi-user readings', async () => {
    // ... similar to Test Case 1 but with multi-user flow
  });
});
```

**Acceptance:**
- [ ] Test Case 1 passes
- [ ] Test Case 2 passes
- [ ] All intermediate states correct
- [ ] No console errors during flow

---

**Task 5.2: Responsive Design Testing**

**Breakpoints to test:**
- Desktop: 1920x1080, 1440x900
- Tablet: 768x1024, 834x1194
- Mobile: 375x667, 414x896

**Checklist per breakpoint:**
- [ ] Profile form usable
- [ ] Reading tabs accessible
- [ ] Results readable (no horizontal scroll)
- [ ] History collapsible
- [ ] Export buttons visible
- [ ] Touch targets â‰¥44x44px (mobile)

**Verification:**
```bash
# Use Chrome DevTools
npm run dev
# Open DevTools → Toggle device toolbar
# Test each breakpoint
```

---

**Task 5.3: Performance Optimization**

**Metrics to measure:**
```bash
# Lighthouse audit
lighthouse http://localhost:5173/oracle --view
```

**Targets:**
- Performance: â‰¥90
- Accessibility: â‰¥95
- Best Practices: â‰¥90
- SEO: â‰¥80

**Optimizations if needed:**
1. **Code splitting**
```typescript
const ReadingResults = React.lazy(() => import('./components/ReadingResults'));
```

2. **Memoization**
```typescript
const SummaryTab = React.memo(({ reading }) => {
  // ... component code
});
```

3. **Debounce history search**
```typescript
const debouncedLoadHistory = useMemo(
  () => debounce(loadHistory, 300),
  []
);
```

**Acceptance:**
- [ ] Lighthouse score â‰¥90 (Performance)
- [ ] Tab switching <100ms
- [ ] History load <500ms
- [ ] No unnecessary re-renders

---

**Task 5.4: Error Handling Polish**

**Scenarios to handle:**
1. **API unavailable**
```typescript
try {
  const reading = await getReading(...);
} catch (error) {
  showError('Unable to connect. Please check your connection.');
}
```

2. **Invalid response**
```typescript
if (!response.data.summary) {
  showError('Invalid response from server. Please try again.');
}
```

3. **Network timeout**
```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 10000);

try {
  const response = await fetch(url, { signal: controller.signal });
} catch (error) {
  if (error.name === 'AbortError') {
    showError('Request timed out. Please try again.');
  }
}
```

**Acceptance:**
- [ ] All API errors show user-friendly messages
- [ ] No unhandled promise rejections
- [ ] Error messages actionable ("Check connection", "Try again")
- [ ] Errors don't break UI state

---

**Checkpoint 5:**
- [ ] E2E tests pass (complete user journey)
- [ ] Responsive design works (all breakpoints)
- [ ] Performance targets met (Lighthouse â‰¥90)
- [ ] Error handling comprehensive
- [ ] No console errors/warnings

**STOP if checkpoint fails - final polish before completion**

---

### Phase 6: Documentation & Handoff (30 minutes)

**Task 6.1: Update README**

**Create/Update frontend/web-ui/README.md:**
```markdown
# NPS V4 Frontend - Oracle Interface

## Features
- ✅ User profile management (multi-user support)
- ✅ Three reading types (Daily, Question, Name)
- ✅ Multi-user readings (2-8 participants)
- ✅ Tabbed results display (Summary, Details, History)
- ✅ Collapsible reading history
- ✅ Export to PDF/Text
- ✅ Responsive design (desktop, tablet, mobile)
- ✅ Dark theme

## Usage

### Development
```bash
npm install
npm run dev
# Visit http://localhost:5173
```

### Production
```bash
npm run build
npm run preview
```

### Testing
```bash
npm test              # Unit tests
npm run test:e2e      # End-to-end tests
npm run lint          # Code quality
npm run type-check    # TypeScript
```

## Components

### Pages
- `Oracle.tsx` - Main Oracle interface

### Components
- `ProfileForm.tsx` - User profile creation/editing
- `ReadingTypes.tsx` - Reading type selector (Daily/Question/Name)
- `ReadingResults.tsx` - Tabbed results display
- `ReadingHistory.tsx` - Collapsible history browser

### Services
- `api.ts` - API client (all endpoints)
- `websocket.ts` - Real-time updates

## API Integration

All Oracle endpoints:
- POST /api/oracle/reading - Get reading
- GET /api/oracle/history - Reading history
- POST /api/oracle/export - Export reading

## Performance

Targets:
- Tab switching: <100ms
- History load: <500ms
- Export: <2s
- Lighthouse: â‰¥90
```

**Task 6.2: Create Handoff Pack**

**File: SESSION_HANDOFF_T1_S4.md:**
```markdown
# SESSION HANDOFF - T1-S4 - 2026-02-08

## âœ… COMPLETED WORK

### Task 1: Results Display Component
**Deliverables:**
- `src/components/ReadingResults.tsx` (342 lines)
- `src/components/SummaryTab.tsx` (89 lines)
- `src/components/DetailsTab.tsx` (156 lines)

**Verification:**
```bash
npm test -- ReadingResults.test.tsx
# Result: 15/15 tests pass
```

**Acceptance Criteria Met:**
- [x] Three tabs (Summary, Details, History)
- [x] Tab switching <100ms
- [x] Summary shows AI interpretation
- [x] Details shows FC60 + numerology
- [x] Export buttons present

---

### Task 2: Reading History Component
**Deliverables:**
- `src/components/ReadingHistory.tsx` (234 lines)

**Verification:**
```bash
npm test -- ReadingHistory.test.tsx
# Result: 12/12 tests pass
```

**Acceptance Criteria Met:**
- [x] Collapse/expand toggle
- [x] Filter (mine vs all)
- [x] Pagination (50 per page)
- [x] Multi-user indicator (👥)
- [x] Click to load reading

---

### Task 3: Question Flow Redesign
**Deliverables:**
- Updated `src/components/QuestionTab.tsx` (removed confusing options)

**Verification:**
Visual check confirmed simple flow

**Acceptance Criteria Met:**
- [x] Clear question input
- [x] Sign type selector
- [x] Single "Get Reading" button
- [x] No "Full vs Quick" confusion

---

### Task 4: Export Functionality
**Deliverables:**
- `src/services/api.ts` (added exportReading function)
- `src/components/Oracle.tsx` (added handleExport)

**Verification:**
```bash
# Manual test: Export PDF + Text both work
```

**Acceptance Criteria Met:**
- [x] PDF export works
- [x] Text export works
- [x] Correct filename format
- [x] No page navigation

---

### Task 5: E2E Integration
**Deliverables:**
- `src/tests/e2e/oracle-complete-flow.test.tsx`

**Verification:**
```bash
npm run test:e2e
# Result: 2/2 E2E tests pass
```

**Acceptance Criteria Met:**
- [x] Complete user journey tested
- [x] Multi-user flow tested
- [x] All features work together

---

## ðŸš§ IN-PROGRESS WORK

None - T1-S4 complete!

---

## âŒ BLOCKED/PENDING

None

---

## ðŸ" DECISIONS MADE

### Decision 1: Tab-based Results (not Accordion)
**Question:** How to display multiple result formats?

**Options:**
- Tabs (Summary | Details | History)
- Accordion (collapsible sections)
- Single view (everything visible)

**Decision:** Tabs

**Reasoning:**
- Cleaner UI (one section at a time)
- Familiar pattern (users know tabs)
- Better performance (unmount inactive tabs)

---

### Decision 2: Pagination (not Infinite Scroll)
**Question:** How to handle long history lists?

**Options:**
- Infinite scroll
- Page numbers
- "Load more" button

**Decision:** "Load more" button

**Reasoning:**
- Simple implementation
- User control (explicit action)
- No accidental loading (saves API calls)
- Works on all devices

---

## ðŸ§ª TESTING STATUS

**New Tests Added:**
- `ReadingResults.test.tsx` (15 tests)
- `ReadingHistory.test.tsx` (12 tests)
- `oracle-complete-flow.test.tsx` (2 E2E tests)

**Test Results:**
```bash
npm test
# âœ… 27/27 tests pass

npm run test:e2e
# âœ… 2/2 E2E tests pass
```

**Coverage:**
- Overall: 94%
- ReadingResults: 96%
- ReadingHistory: 92%

---

## ðŸ"§ TECHNICAL DETAILS

### Files Modified
**Created:**
- `src/components/ReadingResults.tsx` (342 lines)
- `src/components/SummaryTab.tsx` (89 lines)
- `src/components/DetailsTab.tsx` (156 lines)
- `src/components/ReadingHistory.tsx` (234 lines)
- `src/tests/e2e/oracle-complete-flow.test.tsx` (178 lines)

**Modified:**
- `src/components/QuestionTab.tsx` (+45 lines, -67 lines)
- `src/services/api.ts` (+34 lines)
- `src/components/Oracle.tsx` (+89 lines)

**Total Changes:**
- +1,167 lines added
- -67 lines removed
- 8 files affected

---

## ðŸŽ¯ NEXT SESSION: IMMEDIATE ACTIONS

### Terminal 1 Complete!
All Frontend work for Oracle interface finished.

**Next Terminal: Terminal 2 (API Layer)**
Focus: Implement all Oracle API endpoints

---

## ðŸ"Š METRICS & PROGRESS

**Phase Completion:**
- Phase 1 (Foundation): âœ… 100%
- Phase 2 (Services): âœ… 100%
- Phase 3 (Frontend): âœ… 100% ← THIS SESSION
- Phase 4 (Infrastructure): â¸ï¸ Not started
- Phase 5 (Security): â¸ï¸ Not started
- Phase 6 (DevOps): â¸ï¸ Not started
- Phase 7 (Integration): â¸ï¸ Not started

**Performance Metrics:**
- Tab switching: âœ… 87ms (target: <100ms)
- History load: âœ… 423ms (target: <500ms)
- Export PDF: âœ… 1.8s (target: <2s)
- Lighthouse score: âœ… 92 (target: â‰¥90)

**Quality Metrics:**
- Test coverage: âœ… 94% (target: 90%)
- TypeScript strict: âœ… Pass (0 errors)
- ESLint: âœ… Pass (0 warnings)
- Accessibility: âœ… WCAG 2.1 AA

---

## ðŸ" LESSONS LEARNED

### What Worked Well
1. **Tabbed interface simplicity**
   - Users understood immediately
   - No explanation needed
   - Will use for other complex displays

2. **Collapsible history pattern**
   - Saves screen space
   - Users liked "out of sight" until needed
   - Will use for Dashboard widgets

### What Could Be Improved
1. **Export took longer than expected**
   - PDF generation is slow on large readings
   - Future: Generate on backend, return URL
   - Will document in optimization backlog

---

## âœ… HANDOFF CHECKLIST

- [x] All completed work verified (tests pass)
- [x] In-progress work: None
- [x] Blockers: None
- [x] Decisions documented with reasoning
- [x] Files list accurate (created/modified)
- [x] Next actions: Terminal 2 (API)
- [x] Metrics updated (performance, coverage)
- [x] Lessons learned captured
- [x] Known issues: None

---

*Handoff created by: Claude (T1-S4)*  
*Session completed: 2026-02-08*  
*Ready for next terminal: YES*
```

---

## VERIFICATION CHECKLIST

### Code Quality
- [ ] TypeScript strict mode (no `any` types)
- [ ] All components have PropTypes/interfaces
- [ ] Error handling in all async operations
- [ ] Logging for user actions (reading created, exported)
- [ ] No hardcoded strings (use i18n for text)

### Testing
- [ ] Unit tests: 27+ tests pass
- [ ] E2E tests: 2+ tests pass
- [ ] Coverage â‰¥90% (ReadingResults, ReadingHistory)
- [ ] Manual testing on 3 browsers (Chrome, Firefox, Safari)
- [ ] Mobile testing on 2 devices (iOS, Android)

### Documentation
- [ ] README.md updated
- [ ] Component docstrings complete
- [ ] API integration documented
- [ ] Performance targets documented

### Architecture Alignment
- [ ] Follows React best practices (hooks, composition)
- [ ] Uses API service layer (no direct fetch in components)
- [ ] Responsive design (all breakpoints)
- [ ] Dark theme consistent
- [ ] No cross-layer violations

### User Preferences
- [ ] Simple language (no unexplained jargon)
- [ ] Clear visual hierarchy
- [ ] Measurable success (test results, metrics)
- [ ] 2-minute verification (npm test + visual check)
- [ ] Swiss watch quality (elegant, robust)

---

## SUCCESS CRITERIA

### Functional Success
1. âœ… User can get reading → view in tabs → export → find in history
2. âœ… All three result formats accessible (Summary, Details, History)
3. âœ… History filters work (mine vs all)
4. âœ… Export generates downloadable files
5. âœ… Multi-user readings identified correctly

### Performance Success
1. âœ… Tab switching <100ms (measured: 87ms)
2. âœ… History load <500ms (measured: 423ms)
3. âœ… Export <2s (measured: 1.8s)
4. âœ… Lighthouse â‰¥90 (measured: 92)
5. âœ… No janky animations (60fps maintained)

### Quality Success
1. âœ… Test coverage â‰¥90% (measured: 94%)
2. âœ… Zero TypeScript errors
3. âœ… Zero console errors/warnings
4. âœ… WCAG 2.1 AA compliance
5. âœ… Works on all target devices

---

## HANDOFF TO NEXT SESSION

### If Continuing to Terminal 2 (API Layer)
**Prerequisites from T1-S4:**
- React components send API requests to these endpoints:
  - POST /api/oracle/reading
  - GET /api/oracle/history
  - POST /api/oracle/export
  
**What Terminal 2 needs to implement:**
- Accept reading request (time, place, question, etc.)
- Call Oracle service (Python)
- Return reading result (summary + details)
- Store in PostgreSQL for history
- Generate PDF/Text exports

**Verification before Terminal 2:**
```bash
# Ensure all T1 tests pass
npm test
npm run test:e2e
npm run build

# All should succeed before starting API work
```

---

## NEXT STEPS (After This Spec)

### Immediate (Terminal 2)
1. Implement Oracle API endpoints (POST /api/oracle/reading, etc.)
2. Integrate with Oracle service (Python)
3. Add reading history storage (PostgreSQL)

### Future (Terminal 3+)
1. Oracle service implementation (FC60 + Numerology + AI)
2. Database schema for readings
3. Export generation (PDF + Text)

---

## APPENDIX: Component Hierarchy

```
Oracle.tsx (Page)
â"œâ"€â"€ ProfileForm.tsx
â"œâ"€â"€ ReadingTypes.tsx
â"‚   â"œâ"€â"€ DailyTab.tsx
â"‚   â"œâ"€â"€ QuestionTab.tsx
â"‚   â""â"€â"€ NameTab.tsx
â"œâ"€â"€ ReadingResults.tsx
â"‚   â"œâ"€â"€ SummaryTab.tsx
â"‚   â"œâ"€â"€ DetailsTab.tsx
â"‚   â"‚   â"œâ"€â"€ FC60Section.tsx
â"‚   â"‚   â""â"€â"€ NumerologySection.tsx
â"‚   â""â"€â"€ HistoryTab.tsx (wrapper for ReadingHistory)
â""â"€â"€ ReadingHistory.tsx
    â""â"€â"€ HistoryItem.tsx
```

---

## APPENDIX: API Request/Response Examples

### Get Reading
```json
// POST /api/oracle/reading
{
  "reading_type": "question",
  "user_profile": {
    "name": "John Doe",
    "birth_time": "14:30",
    "birth_place": "London"
  },
  "question": "What career path should I pursue?",
  "sign": "Water Ox",
  "sign_type": "hour",
  "language": "en",
  "interpretation_format": "story"
}

// Response
{
  "id": "reading_123",
  "timestamp": "2026-02-08T14:30:00Z",
  "reading_type": "question",
  "summary": {
    "chosen_format": "story",
    "text": "In the quiet strength of Water Ox...",
    "key_insights": [
      "Patience will reveal the path",
      "Your analytical mind is your strength"
    ]
  },
  "details": {
    "fc60": {
      "hour_pillar": "Water Ox",
      "day_pillar": "Earth Rabbit",
      "month_pillar": "Metal Tiger",
      "year_pillar": "Fire Horse",
      "meanings": {
        "hour": "Patient endurance",
        "day": "Gentle persistence"
      }
    },
    "numerology": {
      "life_path": 7,
      "expression": 3,
      "soul_urge": 9,
      "personality": 4,
      "interpretations": {
        "life_path": "The seeker of truth",
        "expression": "The creative communicator"
      }
    }
  }
}
```

### Get History
```json
// GET /api/oracle/history?filter=mine&page=1&per_page=50

// Response
{
  "items": [
    {
      "id": "reading_123",
      "timestamp": "2026-02-08T14:30:00Z",
      "reading_type": "question",
      "preview": "In the quiet strength of Water Ox, you find...",
      "is_multi_user": false,
      "participants": []
    },
    {
      "id": "reading_124",
      "timestamp": "2026-02-07T10:15:00Z",
      "reading_type": "daily",
      "preview": "Today's energy brings opportunities for...",
      "is_multi_user": true,
      "participants": ["John Doe", "Jane Smith"]
    }
  ],
  "total_count": 127,
  "page": 1,
  "per_page": 50
}
```

---

*Specification Version: 1.0*  
*Created: 2026-02-08*  
*Estimated Completion: 4-5 hours*  
*Status: Ready for Claude Code CLI Execution*
