# SESSION 11 SPEC — Framework Integration: Moon, Ganzhi & Cosmic Cycles

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 5-6 hours
**Complexity:** Medium
**Dependencies:** Session 6 (framework bridge — `framework_bridge.py` must exist and be importable)

---

## TL;DR

- Create `cosmic_formatter.py` backend module to extract and format moon phase, Ganzhi (Chinese zodiac), and current moment data from the framework's `MasterOrchestrator` output
- Expand existing `MoonData` and `GanzhiData` Pydantic models in the API layer to carry all framework fields (energy, best_for, avoid, day/hour cycles, traditional names, planet-moon combos)
- Build 3 new React components: `MoonPhaseDisplay.tsx` (emoji + illumination bar + energy), `GanzhiDisplay.tsx` (zodiac animal + element + cycles), `CosmicCyclePanel.tsx` (combined panel)
- Add 40+ cosmic cycle i18n terms to both English and Persian locale files
- Write 14+ tests covering the backend formatter, API model expansion, and all 3 frontend components

---

## OBJECTIVES

1. **Create cosmic data formatter** — `cosmic_formatter.py` extracts `reading['moon']`, `reading['ganzhi']`, and `reading['current']` from framework output and returns a single structured dict ready for API serialization
2. **Expand API response models** — `MoonData` gains `energy`, `best_for`, `avoid` fields; `GanzhiData` gains day cycle, hour cycle, `traditional_name`, `polarity`; new `CurrentMomentData` and `CosmicCycleResponse` models added
3. **Build MoonPhaseDisplay component** — renders moon emoji, phase name, animated illumination progress bar, energy keyword, best-for/avoid guidance; supports i18n
4. **Build GanzhiDisplay component** — renders Chinese zodiac year animal + element + polarity, day cycle info, optional hour cycle; supports i18n
5. **Build CosmicCyclePanel component** — composes MoonPhaseDisplay + GanzhiDisplay + current planet/domain into a unified panel usable inside reading results
6. **Add Persian translations** — all cosmic cycle terms (8 moon phases, 12 animals, 5 elements, 8 energies, 7 planets, polarity labels) translated in `fa.json`

---

## PREREQUISITES

- [ ] Session 6 completed — `services/oracle/oracle_service/framework_bridge.py` exists
- [ ] Framework is importable from Oracle service context
- [ ] `numerology_ai_framework/universal/moon_engine.py` exists and passes self-tests
- [ ] `numerology_ai_framework/universal/ganzhi_engine.py` exists and passes self-tests
- [ ] Frontend dev server runs (`cd frontend && npm run dev`)

Verification:

```bash
python3 -c "from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator; print('Framework OK')"
test -f services/oracle/oracle_service/framework_bridge.py && echo "Bridge OK"
cd numerology_ai_framework && python3 universal/moon_engine.py && echo "MoonEngine OK"
cd numerology_ai_framework && python3 universal/ganzhi_engine.py && echo "GanzhiEngine OK"
```

---

## FILES TO CREATE

| Path                                                                 | Purpose                                                                                          |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `services/oracle/oracle_service/cosmic_formatter.py`                 | **NEW** — Extract and format moon, ganzhi, and current moment data from framework reading output |
| `frontend/src/components/oracle/MoonPhaseDisplay.tsx`                | **NEW** — Moon phase display with emoji, illumination bar, energy, best_for/avoid                |
| `frontend/src/components/oracle/GanzhiDisplay.tsx`                   | **NEW** — Chinese zodiac display with year/day/hour cycles                                       |
| `frontend/src/components/oracle/CosmicCyclePanel.tsx`                | **NEW** — Combined panel composing moon + ganzhi + current planet                                |
| `services/oracle/tests/test_cosmic_formatter.py`                     | **NEW** — Tests for cosmic formatter                                                             |
| `frontend/src/components/oracle/__tests__/MoonPhaseDisplay.test.tsx` | **NEW** — Tests for moon phase component                                                         |
| `frontend/src/components/oracle/__tests__/GanzhiDisplay.test.tsx`    | **NEW** — Tests for ganzhi component                                                             |
| `frontend/src/components/oracle/__tests__/CosmicCyclePanel.test.tsx` | **NEW** — Tests for combined panel                                                               |

## FILES TO MODIFY

| Path                           | Change                                                                                                                                                                                                   |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api/app/models/oracle.py`     | Expand `MoonData` (add `energy`, `best_for`, `avoid`), expand `GanzhiData` (add `day_*`, `hour_*`, `traditional_name`, `polarity`, `gz_token`), add `CurrentMomentData` and `CosmicCycleResponse` models |
| `frontend/src/locales/en.json` | Add `oracle.cosmic` section with moon phases, animals, elements, energies, planets, polarity labels (~40 keys)                                                                                           |
| `frontend/src/locales/fa.json` | Add matching `oracle.cosmic` section with Persian translations (~40 keys)                                                                                                                                |
| `frontend/src/types/index.ts`  | Add TypeScript interfaces for `MoonPhaseData`, `GanzhiData`, `CurrentMomentData`, `CosmicCycleData`                                                                                                      |

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Backend — Cosmic Data Formatter (~60 min)

**Tasks:**

1. **Read framework output structure** to understand exact keys available:

   From `MasterOrchestrator.generate_reading()` (verified in `numerology_ai_framework/synthesis/master_orchestrator.py`):

   ```python
   reading['moon'] = {
       'phase_name': str,   # e.g. "Waning Gibbous"
       'emoji': str,        # e.g. "🌖"
       'age': float,        # days since new moon, e.g. 19.05
       'illumination': float, # percentage, e.g. 87.3
       'energy': str,       # e.g. "Share"
       'best_for': str,     # e.g. "Teaching, distributing, gratitude"
       'avoid': str,        # e.g. "Hoarding"
   }

   reading['ganzhi'] = {
       'year': {
           'year': int, 'stem_index': int, 'branch_index': int,
           'stem_token': str, 'branch_token': str, 'gz_token': str,
           'stem_name': str, 'animal_name': str, 'element': str,
           'polarity': str, 'traditional_name': str,
       },
       'day': {
           'jdn': int, 'stem_index': int, 'branch_index': int,
           'stem_token': str, 'branch_token': str, 'gz_token': str,
           'stem_name': str, 'animal_name': str, 'element': str,
           'polarity': str,
       },
       'hour': {  # only present if has_time=True
           'stem_token': str, 'branch_token': str, 'animal_name': str,
       },
   }

   reading['current'] = {
       'date': str, 'jdn': int, 'jdn_fc60': str,
       'weekday': str, 'planet': str, 'domain': str,
       'year_fc60': str,
   }
   ```

2. **Create `services/oracle/oracle_service/cosmic_formatter.py`:**

   ```python
   """Cosmic cycle data formatter.

   Extracts moon phase, Ganzhi (Chinese zodiac), and current moment data
   from MasterOrchestrator reading output. Formats for API serialization
   and frontend display.
   """

   import logging
   from typing import Dict, Any, Optional

   logger = logging.getLogger(__name__)


   class CosmicFormatter:
       """Format cosmic cycle data from framework reading output."""

       @staticmethod
       def format_moon(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
           """Extract and format moon phase data."""

       @staticmethod
       def format_ganzhi(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
           """Extract and format Ganzhi (Chinese zodiac) data."""

       @staticmethod
       def format_current_moment(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
           """Extract and format current moment data (planet, domain, weekday)."""

       @staticmethod
       def format_planet_moon_combo(
           planet: str, moon_phase: str
       ) -> Optional[Dict[str, str]]:
           """Get planet-moon combination insight from SignalCombiner."""

       @staticmethod
       def format_cosmic_cycles(reading: Dict[str, Any]) -> Dict[str, Any]:
           """Format all cosmic cycle data into a single response dict.

           This is the primary entry point. Returns:
           {
               'moon': { phase_name, emoji, age, illumination, energy, best_for, avoid },
               'ganzhi': {
                   'year': { animal_name, element, polarity, traditional_name, gz_token },
                   'day': { animal_name, element, polarity, gz_token },
                   'hour': { animal_name } | None,
               },
               'current': { weekday, planet, domain },
               'planet_moon': { theme, message } | None,
           }
           """
   ```

   **Key design decisions:**
   - `CosmicFormatter` uses `@staticmethod` methods (per framework convention)
   - All methods accept the full reading dict and handle missing keys gracefully (return `None`)
   - `format_planet_moon_combo()` imports `SignalCombiner.planet_meets_moon()` from the framework to enrich output
   - No external dependencies beyond the framework itself

3. **Implementation details for `format_cosmic_cycles()`:**

   ```python
   @staticmethod
   def format_cosmic_cycles(reading: Dict[str, Any]) -> Dict[str, Any]:
       moon = CosmicFormatter.format_moon(reading)
       ganzhi = CosmicFormatter.format_ganzhi(reading)
       current = CosmicFormatter.format_current_moment(reading)

       planet_moon = None
       if moon and current:
           planet_moon = CosmicFormatter.format_planet_moon_combo(
               current.get('planet', ''),
               moon.get('phase_name', ''),
           )

       return {
           'moon': moon,
           'ganzhi': ganzhi,
           'current': current,
           'planet_moon': planet_moon,
       }
   ```

**Checkpoint:**

- [ ] `cosmic_formatter.py` exists at `services/oracle/oracle_service/cosmic_formatter.py`
- [ ] `CosmicFormatter.format_cosmic_cycles()` returns valid dict when given a sample reading
- [ ] Missing keys in reading dict handled gracefully (returns `None` sections, no crash)
- Verify:
  ```bash
  cd services/oracle && python3 -c "
  import oracle_service
  from oracle_service.cosmic_formatter import CosmicFormatter
  # Test with mock reading data
  mock_reading = {
      'moon': {'phase_name': 'Full Moon', 'emoji': '🌕', 'age': 14.77, 'illumination': 99.8, 'energy': 'Culminate', 'best_for': 'Celebrating', 'avoid': 'Starting'},
      'ganzhi': {'year': {'animal_name': 'Horse', 'element': 'Fire', 'polarity': 'Yang', 'traditional_name': 'Fire Horse', 'gz_token': 'BI-HO'}, 'day': {'animal_name': 'Rat', 'element': 'Wood', 'polarity': 'Yang', 'gz_token': 'JA-RA'}},
      'current': {'weekday': 'Friday', 'planet': 'Venus', 'domain': 'Love, values, beauty'},
  }
  result = CosmicFormatter.format_cosmic_cycles(mock_reading)
  assert result['moon'] is not None
  assert result['ganzhi'] is not None
  assert result['current'] is not None
  print('CosmicFormatter OK')
  "
  ```

🚨 STOP if checkpoint fails — all subsequent phases depend on this formatter

---

### Phase 2: API Layer — Expand Response Models (~30 min)

**Tasks:**

1. **Expand `MoonData` model** in `api/app/models/oracle.py`:

   Current (line 33-38):

   ```python
   class MoonData(BaseModel):
       phase_name: str = ""
       illumination: float = 0
       age_days: float = 0
       meaning: str = ""
       emoji: str = ""
   ```

   Add:

   ```python
   class MoonData(BaseModel):
       phase_name: str = ""
       illumination: float = 0
       age_days: float = 0
       meaning: str = ""
       emoji: str = ""
       energy: str = ""           # NEW: Seed/Build/Challenge/Refine/Culminate/Share/Release/Rest
       best_for: str = ""         # NEW: Activity guidance
       avoid: str = ""            # NEW: What to avoid
   ```

2. **Expand `GanzhiData` model** in `api/app/models/oracle.py`:

   Current (line 56-62):

   ```python
   class GanzhiData(BaseModel):
       year_name: str = ""
       year_animal: str = ""
       stem_element: str = ""
       stem_polarity: str = ""
       hour_animal: str = ""
       hour_branch: str = ""
   ```

   Expand:

   ```python
   class GanzhiData(BaseModel):
       # Year cycle
       year_name: str = ""
       year_animal: str = ""
       year_gz_token: str = ""          # NEW: e.g. "BI-HO"
       year_traditional_name: str = ""  # NEW: e.g. "Fire Horse"
       stem_element: str = ""
       stem_polarity: str = ""
       # Day cycle
       day_animal: str = ""             # NEW
       day_element: str = ""            # NEW
       day_polarity: str = ""           # NEW
       day_gz_token: str = ""           # NEW
       # Hour cycle (optional)
       hour_animal: str = ""
       hour_branch: str = ""
   ```

3. **Add new models** after `GanzhiData`:

   ```python
   class CurrentMomentData(BaseModel):
       weekday: str = ""
       planet: str = ""        # Ruling planet of the day
       domain: str = ""        # Planet's domain (e.g. "Love, values, beauty")

   class PlanetMoonCombo(BaseModel):
       theme: str = ""         # e.g. "Love Illuminated"
       message: str = ""       # Interpretive message

   class CosmicCycleResponse(BaseModel):
       moon: MoonData | None = None
       ganzhi: GanzhiData | None = None
       current: CurrentMomentData | None = None
       planet_moon: PlanetMoonCombo | None = None
   ```

**Checkpoint:**

- [ ] `MoonData` has `energy`, `best_for`, `avoid` fields
- [ ] `GanzhiData` has `day_animal`, `day_element`, `day_polarity`, `day_gz_token`, `year_gz_token`, `year_traditional_name` fields
- [ ] `CurrentMomentData`, `PlanetMoonCombo`, and `CosmicCycleResponse` models exist
- Verify:
  ```bash
  cd api && python3 -c "
  from app.models.oracle import MoonData, GanzhiData, CurrentMomentData, PlanetMoonCombo, CosmicCycleResponse
  m = MoonData(phase_name='Full Moon', energy='Culminate', best_for='Celebrating', avoid='Starting')
  g = GanzhiData(year_animal='Horse', day_animal='Rat', year_traditional_name='Fire Horse')
  c = CurrentMomentData(weekday='Friday', planet='Venus', domain='Love')
  r = CosmicCycleResponse(moon=m, ganzhi=g, current=c)
  print('API Models OK')
  "
  ```

🚨 STOP if checkpoint fails

---

### Phase 3: Frontend — TypeScript Types & i18n (~45 min)

**Tasks:**

1. **Add TypeScript interfaces** to `frontend/src/types/index.ts`:

   ```typescript
   /** Moon phase data from the cosmic cycle API */
   export interface MoonPhaseData {
     phase_name: string;
     emoji: string;
     age: number; // days since new moon
     illumination: number; // percentage (0-100)
     energy: string; // Seed/Build/Challenge/Refine/Culminate/Share/Release/Rest
     best_for: string;
     avoid: string;
   }

   /** Single Ganzhi cycle (year, day, or hour) */
   export interface GanzhiCycleData {
     animal_name: string;
     element: string;
     polarity: string;
     gz_token: string;
     traditional_name?: string; // only on year cycle
   }

   /** Full Ganzhi data with year/day/hour cycles */
   export interface GanzhiFullData {
     year: GanzhiCycleData;
     day: GanzhiCycleData;
     hour?: {
       animal_name: string;
     };
   }

   /** Current moment cosmic data */
   export interface CurrentMomentData {
     weekday: string;
     planet: string;
     domain: string;
   }

   /** Planet-Moon combination insight */
   export interface PlanetMoonCombo {
     theme: string;
     message: string;
   }

   /** Complete cosmic cycle data */
   export interface CosmicCycleData {
     moon: MoonPhaseData | null;
     ganzhi: GanzhiFullData | null;
     current: CurrentMomentData | null;
     planet_moon: PlanetMoonCombo | null;
   }
   ```

2. **Add English cosmic cycle terms** to `frontend/src/locales/en.json` under `oracle.cosmic`:

   ```json
   "cosmic": {
     "title": "Cosmic Cycles",
     "moon_title": "Moon Phase",
     "ganzhi_title": "Chinese Zodiac",
     "current_title": "Current Moment",
     "planet_moon_title": "Planet-Moon Insight",
     "illumination": "Illumination",
     "moon_age": "Moon Age",
     "days": "days",
     "energy": "Energy",
     "best_for": "Best For",
     "avoid": "Avoid",
     "year_cycle": "Year Cycle",
     "day_cycle": "Day Cycle",
     "hour_cycle": "Hour Cycle",
     "ruling_planet": "Ruling Planet",
     "domain": "Domain",
     "phase_new_moon": "New Moon",
     "phase_waxing_crescent": "Waxing Crescent",
     "phase_first_quarter": "First Quarter",
     "phase_waxing_gibbous": "Waxing Gibbous",
     "phase_full_moon": "Full Moon",
     "phase_waning_gibbous": "Waning Gibbous",
     "phase_last_quarter": "Last Quarter",
     "phase_waning_crescent": "Waning Crescent",
     "energy_seed": "Seed",
     "energy_build": "Build",
     "energy_challenge": "Challenge",
     "energy_refine": "Refine",
     "energy_culminate": "Culminate",
     "energy_share": "Share",
     "energy_release": "Release",
     "energy_rest": "Rest",
     "animal_rat": "Rat",
     "animal_ox": "Ox",
     "animal_tiger": "Tiger",
     "animal_rabbit": "Rabbit",
     "animal_dragon": "Dragon",
     "animal_snake": "Snake",
     "animal_horse": "Horse",
     "animal_goat": "Goat",
     "animal_monkey": "Monkey",
     "animal_rooster": "Rooster",
     "animal_dog": "Dog",
     "animal_pig": "Pig",
     "element_wood": "Wood",
     "element_fire": "Fire",
     "element_earth": "Earth",
     "element_metal": "Metal",
     "element_water": "Water",
     "polarity_yin": "Yin",
     "polarity_yang": "Yang"
   }
   ```

3. **Add Persian cosmic cycle terms** to `frontend/src/locales/fa.json` under `oracle.cosmic`:

   ```json
   "cosmic": {
     "title": "چرخه‌های کیهانی",
     "moon_title": "فاز ماه",
     "ganzhi_title": "زودیاک چینی",
     "current_title": "لحظه حاضر",
     "planet_moon_title": "بینش سیاره-ماه",
     "illumination": "روشنایی",
     "moon_age": "سن ماه",
     "days": "روز",
     "energy": "انرژی",
     "best_for": "بهترین برای",
     "avoid": "پرهیز از",
     "year_cycle": "چرخه سال",
     "day_cycle": "چرخه روز",
     "hour_cycle": "چرخه ساعت",
     "ruling_planet": "سیاره حاکم",
     "domain": "حوزه",
     "phase_new_moon": "ماه نو",
     "phase_waxing_crescent": "هلال رو به رشد",
     "phase_first_quarter": "تربیع اول",
     "phase_waxing_gibbous": "کوژ رو به رشد",
     "phase_full_moon": "بدر",
     "phase_waning_gibbous": "کوژ رو به کاهش",
     "phase_last_quarter": "تربیع آخر",
     "phase_waning_crescent": "هلال رو به کاهش",
     "energy_seed": "بذر",
     "energy_build": "ساختن",
     "energy_challenge": "چالش",
     "energy_refine": "پالایش",
     "energy_culminate": "اوج",
     "energy_share": "بخشیدن",
     "energy_release": "رهایی",
     "energy_rest": "آرامش",
     "animal_rat": "موش",
     "animal_ox": "گاو",
     "animal_tiger": "ببر",
     "animal_rabbit": "خرگوش",
     "animal_dragon": "اژدها",
     "animal_snake": "مار",
     "animal_horse": "اسب",
     "animal_goat": "بز",
     "animal_monkey": "میمون",
     "animal_rooster": "خروس",
     "animal_dog": "سگ",
     "animal_pig": "خوک",
     "element_wood": "چوب",
     "element_fire": "آتش",
     "element_earth": "خاک",
     "element_metal": "فلز",
     "element_water": "آب",
     "polarity_yin": "یین",
     "polarity_yang": "یانگ"
   }
   ```

   **Key Persian translations note:** Moon phase names follow standard Iranian astronomical terminology. Animal names use colloquial Persian equivalents. Elements use classical Persian names (آتش for Fire, آب for Water, etc.).

**Checkpoint:**

- [ ] TypeScript interfaces compile without errors
- [ ] `oracle.cosmic` key exists in both `en.json` and `fa.json`
- [ ] English has 50+ cosmic keys, Persian has matching set
- Verify:
  ```bash
  cd frontend && npx tsc --noEmit 2>&1 | head -20
  node -e "const en = require('./src/locales/en.json'); console.log(Object.keys(en.oracle.cosmic).length + ' cosmic keys in en.json')"
  node -e "const fa = require('./src/locales/fa.json'); console.log(Object.keys(fa.oracle.cosmic).length + ' cosmic keys in fa.json')"
  ```

🚨 STOP if checkpoint fails

---

### Phase 4: Frontend — MoonPhaseDisplay Component (~45 min)

**Tasks:**

Create `frontend/src/components/oracle/MoonPhaseDisplay.tsx`:

**Props interface:**

```typescript
interface MoonPhaseDisplayProps {
  moon: MoonPhaseData;
  compact?: boolean; // Compact mode for embedding in panels
}
```

**Component requirements:**

1. **Header row:** Moon emoji (large, e.g. 2rem) + phase name text
2. **Illumination bar:** Horizontal progress bar (0-100%) with percentage label. Use Tailwind's `bg-yellow-300` fill on `bg-gray-200` track. Smooth width transition.
3. **Moon age:** "X.XX days" since new moon — small text below bar
4. **Energy keyword:** Bold label with colored badge (energy-specific colors: Seed=green, Build=blue, Challenge=red, Refine=purple, Culminate=gold, Share=teal, Release=orange, Rest=gray)
5. **Best for / Avoid:** Two-column layout with icon indicators (checkmark for best_for, warning for avoid)
6. **i18n:** All labels use `useTranslation()` with `oracle.cosmic.*` keys
7. **RTL support:** Component uses `dir` attribute for RTL when locale is FA
8. **Compact mode:** When `compact={true}`, show only emoji + phase name + illumination bar (no best_for/avoid)

**Accessibility:**

- Illumination bar has `role="progressbar"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Moon emoji has `aria-label` with phase name

**Checkpoint:**

- [ ] `MoonPhaseDisplay.tsx` exists and exports default
- [ ] Renders moon emoji, phase name, illumination bar, energy, best_for, avoid
- [ ] Compact mode renders fewer elements
- [ ] No TypeScript errors
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | grep MoonPhaseDisplay || echo "No errors"`

🚨 STOP if checkpoint fails

---

### Phase 5: Frontend — GanzhiDisplay Component (~45 min)

**Tasks:**

Create `frontend/src/components/oracle/GanzhiDisplay.tsx`:

**Props interface:**

```typescript
interface GanzhiDisplayProps {
  ganzhi: GanzhiFullData;
  compact?: boolean;
}
```

**Component requirements:**

1. **Year cycle section:**
   - Large animal name (e.g. "Horse") with element badge (e.g. "Fire" with red background)
   - Traditional name: "Fire Horse" in subtitle
   - Polarity indicator: "Yang" / "Yin" with visual indicator (☀/🌙 or similar)
   - GZ token as small monospace text (e.g. "BI-HO")

2. **Day cycle section:**
   - Animal name + element + polarity (same layout as year, smaller)
   - GZ token

3. **Hour cycle section (conditional):**
   - Only rendered if `ganzhi.hour` exists
   - Animal name only (hour data is simpler)

4. **Visual layout:**
   - Vertical stack: Year (prominent) → Day (medium) → Hour (small, optional)
   - Each section separated by thin divider
   - Element colors: Wood=green, Fire=red, Earth=amber, Metal=gray, Water=blue

5. **i18n:** Animal names, elements, polarity labels use `oracle.cosmic.*` keys
6. **RTL support:** Layout respects document direction
7. **Compact mode:** Show only year cycle (animal + element)

**Checkpoint:**

- [ ] `GanzhiDisplay.tsx` exists and exports default
- [ ] Renders year animal, element, polarity, traditional name
- [ ] Day cycle renders when data present
- [ ] Hour cycle conditionally renders
- [ ] No TypeScript errors
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | grep GanzhiDisplay || echo "No errors"`

🚨 STOP if checkpoint fails

---

### Phase 6: Frontend — CosmicCyclePanel Component (~30 min)

**Tasks:**

Create `frontend/src/components/oracle/CosmicCyclePanel.tsx`:

**Props interface:**

```typescript
interface CosmicCyclePanelProps {
  cosmicData: CosmicCycleData;
  compact?: boolean;
}
```

**Component requirements:**

1. **Panel header:** "Cosmic Cycles" title with cosmic icon
2. **Three-section layout:**
   - **Moon section:** `<MoonPhaseDisplay>` with data from `cosmicData.moon`
   - **Ganzhi section:** `<GanzhiDisplay>` with data from `cosmicData.ganzhi`
   - **Current moment section:** Ruling planet name + domain description
3. **Planet-Moon insight (conditional):**
   - If `cosmicData.planet_moon` exists, render themed insight card
   - Shows `theme` as title, `message` as body
   - Styled as a highlighted callout box
4. **Responsive layout:**
   - Desktop: 3-column grid (moon | ganzhi | current+planet_moon)
   - Mobile: vertical stack
5. **Graceful degradation:**
   - Each section renders independently — if `moon` is null, skip that section
   - If all data is null, show a "No cosmic data available" placeholder
6. **Compact mode:** Passes `compact={true}` to child components; uses single-column layout

**Checkpoint:**

- [ ] `CosmicCyclePanel.tsx` exists and exports default
- [ ] Renders all three sections when data present
- [ ] Handles null sections gracefully
- [ ] Responsive layout works (grid on wide, stack on narrow)
- [ ] No TypeScript errors
- Verify: `cd frontend && npx tsc --noEmit 2>&1 | grep CosmicCyclePanel || echo "No errors"`

🚨 STOP if checkpoint fails

---

### Phase 7: Write Tests (~60 min)

**Tasks:**

**7A. Backend tests — `services/oracle/tests/test_cosmic_formatter.py`:**

```python
def test_format_moon_full_data():
    """Full moon data returns all expected fields."""

def test_format_moon_missing_key():
    """Missing 'moon' key in reading returns None."""

def test_format_ganzhi_year_and_day():
    """Ganzhi data with year and day cycles formatted correctly."""

def test_format_ganzhi_with_hour():
    """Ganzhi data including hour cycle formatted correctly."""

def test_format_ganzhi_no_hour():
    """Ganzhi data without hour cycle still returns year and day."""

def test_format_current_moment():
    """Current moment data returns weekday, planet, domain."""

def test_format_planet_moon_combo():
    """Planet-moon combo returns theme and message from SignalCombiner."""

def test_format_cosmic_cycles_complete():
    """Complete reading produces all four sections."""

def test_format_cosmic_cycles_empty_reading():
    """Empty reading dict returns all-None sections."""

def test_format_cosmic_cycles_partial():
    """Reading with only moon data returns moon section, others None."""
```

**Test vectors (use framework demo data):**

```python
SAMPLE_READING = {
    'moon': {
        'phase_name': 'Waning Gibbous', 'emoji': '🌖',
        'age': 19.05, 'illumination': 87.3,
        'energy': 'Share', 'best_for': 'Teaching, distributing, gratitude',
        'avoid': 'Hoarding',
    },
    'ganzhi': {
        'year': {
            'animal_name': 'Horse', 'element': 'Fire', 'polarity': 'Yang',
            'traditional_name': 'Fire Horse', 'gz_token': 'BI-HO',
        },
        'day': {
            'animal_name': 'Rat', 'element': 'Wood', 'polarity': 'Yang',
            'gz_token': 'JA-RA',
        },
    },
    'current': {
        'weekday': 'Friday', 'planet': 'Venus',
        'domain': 'Love, values, beauty',
    },
}
```

**7B. Frontend tests — `MoonPhaseDisplay.test.tsx`:**

```typescript
test("renders moon emoji and phase name");
test("renders illumination progress bar with correct percentage");
test("renders energy badge");
test("renders best_for and avoid sections");
test("compact mode hides best_for and avoid");
```

**7C. Frontend tests — `GanzhiDisplay.test.tsx`:**

```typescript
test("renders year animal name and element");
test("renders traditional name");
test("renders day cycle when data present");
test("conditionally renders hour cycle");
test("compact mode shows only year cycle");
```

**7D. Frontend tests — `CosmicCyclePanel.test.tsx`:**

```typescript
test("renders all three sections with complete data");
test("handles null moon data gracefully");
test("handles null ganzhi data gracefully");
test("renders planet-moon insight when present");
test("shows placeholder when all data is null");
```

**Checkpoint:**

- [ ] All backend tests pass: `cd services/oracle && python3 -m pytest tests/test_cosmic_formatter.py -v`
- [ ] All frontend tests pass: `cd frontend && npm test -- --testPathPattern="(MoonPhaseDisplay|GanzhiDisplay|CosmicCyclePanel)" --watchAll=false`
- [ ] 14+ tests total (10 backend + 5+ frontend per component)
- Verify:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_cosmic_formatter.py -v --tb=short
  cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/MoonPhaseDisplay.test.tsx src/components/oracle/__tests__/GanzhiDisplay.test.tsx src/components/oracle/__tests__/CosmicCyclePanel.test.tsx
  ```

🚨 STOP if tests fail

---

### Phase 8: Final Verification & Commit (~15 min)

**Tasks:**

1. **Full TypeScript check:**

   ```bash
   cd frontend && npx tsc --noEmit
   ```

2. **Lint and format — backend:**

   ```bash
   cd services/oracle && python3 -m ruff check oracle_service/cosmic_formatter.py --fix
   cd services/oracle && python3 -m ruff format oracle_service/cosmic_formatter.py
   ```

3. **Lint and format — frontend:**

   ```bash
   cd frontend && npx eslint src/components/oracle/MoonPhaseDisplay.tsx src/components/oracle/GanzhiDisplay.tsx src/components/oracle/CosmicCyclePanel.tsx --fix
   cd frontend && npx prettier --write src/components/oracle/MoonPhaseDisplay.tsx src/components/oracle/GanzhiDisplay.tsx src/components/oracle/CosmicCyclePanel.tsx
   ```

4. **i18n key parity check** — ensure en.json and fa.json have matching keys:

   ```bash
   node -e "
   const en = require('./frontend/src/locales/en.json');
   const fa = require('./frontend/src/locales/fa.json');
   const enKeys = Object.keys(en.oracle.cosmic).sort();
   const faKeys = Object.keys(fa.oracle.cosmic).sort();
   const missing = enKeys.filter(k => !faKeys.includes(k));
   if (missing.length) { console.log('Missing in fa.json:', missing); process.exit(1); }
   else { console.log('i18n parity OK: ' + enKeys.length + ' keys match'); }
   "
   ```

5. **Framework regression check:**

   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py && echo "Framework OK"
   ```

6. **Git commit:**

   ```bash
   git add -A
   git commit -m "[oracle][frontend] add cosmic cycle formatter and display components (#session-11)

   - Create CosmicFormatter for moon/ganzhi/current data extraction
   - Expand MoonData and GanzhiData API models
   - Add MoonPhaseDisplay, GanzhiDisplay, CosmicCyclePanel components
   - Add 50+ cosmic cycle i18n terms (EN + FA)
   - Add TypeScript interfaces for cosmic data
   - Add 14+ tests (backend formatter + frontend components)"
   ```

**Checkpoint:**

- [ ] Zero TypeScript errors
- [ ] Zero lint errors
- [ ] i18n keys match between en.json and fa.json
- [ ] Framework tests still pass
- [ ] All new tests pass
- [ ] Committed to git

---

## TESTS TO WRITE

### `services/oracle/tests/test_cosmic_formatter.py`

| Test Function                             | Verifies                                                                                  |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| `test_format_moon_full_data`              | All 7 moon fields extracted correctly from reading dict                                   |
| `test_format_moon_missing_key`            | Missing `moon` key returns `None` gracefully                                              |
| `test_format_ganzhi_year_and_day`         | Year and day cycle data formatted with animal, element, polarity, gz_token                |
| `test_format_ganzhi_with_hour`            | Hour cycle included when present in reading                                               |
| `test_format_ganzhi_no_hour`              | Missing hour cycle doesn't crash, returns year+day only                                   |
| `test_format_current_moment`              | Weekday, planet, domain extracted correctly                                               |
| `test_format_planet_moon_combo`           | SignalCombiner integration returns theme and message                                      |
| `test_format_cosmic_cycles_complete`      | Full reading produces all 4 sections (moon, ganzhi, current, planet_moon)                 |
| `test_format_cosmic_cycles_empty_reading` | Empty dict returns `{'moon': None, 'ganzhi': None, 'current': None, 'planet_moon': None}` |
| `test_format_cosmic_cycles_partial`       | Partial reading returns available sections, `None` for missing                            |

### `frontend/src/components/oracle/__tests__/MoonPhaseDisplay.test.tsx`

| Test                                  | Verifies                                      |
| ------------------------------------- | --------------------------------------------- |
| `renders moon emoji and phase name`   | Emoji and name text visible in DOM            |
| `renders illumination progress bar`   | Progress bar has correct width/aria-valuenow  |
| `renders energy badge`                | Energy keyword displayed                      |
| `renders best_for and avoid sections` | Both guidance sections present                |
| `compact mode hides guidance`         | best_for/avoid not rendered when compact=true |

### `frontend/src/components/oracle/__tests__/GanzhiDisplay.test.tsx`

| Test                               | Verifies                           |
| ---------------------------------- | ---------------------------------- |
| `renders year animal and element`  | Year cycle data visible            |
| `renders traditional name`         | Traditional name subtitle present  |
| `renders day cycle`                | Day cycle section present          |
| `conditionally renders hour cycle` | Hour section only when data exists |
| `compact mode shows year only`     | Day/hour hidden in compact mode    |

### `frontend/src/components/oracle/__tests__/CosmicCyclePanel.test.tsx`

| Test                                      | Verifies                               |
| ----------------------------------------- | -------------------------------------- |
| `renders all sections with complete data` | Moon + Ganzhi + Current all visible    |
| `handles null moon data`                  | No crash, moon section hidden          |
| `handles null ganzhi data`                | No crash, ganzhi section hidden        |
| `renders planet-moon insight`             | Insight card visible when data present |
| `shows placeholder when all null`         | Placeholder message displayed          |

**Total: 25 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] `cosmic_formatter.py` exists at `services/oracle/oracle_service/cosmic_formatter.py`
- [ ] `CosmicFormatter.format_cosmic_cycles()` returns a valid dict with `moon`, `ganzhi`, `current`, `planet_moon` sections
- [ ] `MoonData` model has `energy`, `best_for`, `avoid` fields
- [ ] `GanzhiData` model has `day_animal`, `day_element`, `day_polarity`, `day_gz_token`, `year_gz_token`, `year_traditional_name` fields
- [ ] `CurrentMomentData`, `PlanetMoonCombo`, `CosmicCycleResponse` Pydantic models exist in `api/app/models/oracle.py`
- [ ] `MoonPhaseDisplay.tsx` renders emoji + phase name + illumination bar + energy + best_for/avoid
- [ ] `GanzhiDisplay.tsx` renders year animal + element + polarity + traditional name + day cycle
- [ ] `CosmicCyclePanel.tsx` composes all three sections into a responsive panel
- [ ] `en.json` and `fa.json` both have `oracle.cosmic` section with 50+ matching keys
- [ ] TypeScript types (`MoonPhaseData`, `GanzhiFullData`, `CurrentMomentData`, `CosmicCycleData`) defined in `frontend/src/types/index.ts`
- [ ] All 25+ tests pass
- [ ] Zero TypeScript errors: `cd frontend && npx tsc --noEmit`
- [ ] Framework tests still pass (no regressions): `cd numerology_ai_framework && python3 tests/test_all.py`
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_cosmic_formatter.py -v --tb=short && echo "BACKEND TESTS OK"
  cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/MoonPhaseDisplay.test.tsx src/components/oracle/__tests__/GanzhiDisplay.test.tsx src/components/oracle/__tests__/CosmicCyclePanel.test.tsx && echo "FRONTEND TESTS OK"
  cd frontend && npx tsc --noEmit && echo "TYPES OK"
  cd numerology_ai_framework && python3 tests/test_all.py && echo "FRAMEWORK OK"
  ```

---

## ERROR SCENARIOS

| Scenario                                                                            | Expected Behavior                                                         | Recovery                                                                                                                                                                                     |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Framework bridge not available (Session 6 incomplete)                               | `ImportError` when `cosmic_formatter.py` tries to import `SignalCombiner` | Verify Session 6 prerequisites. Run `python3 -c "from numerology_ai_framework.synthesis.signal_combiner import SignalCombiner"` to isolate. Check `sys.path` in `oracle_service/__init__.py` |
| Reading dict has unexpected structure (e.g., `moon` key present but fields renamed) | `KeyError` in `format_moon()`                                             | All formatter methods must use `.get()` with defaults for every field access. Never assume keys exist. Add defensive checks                                                                  |
| SignalCombiner.planet_meets_moon returns unexpected format                          | `KeyError` when accessing `theme`/`message`                               | `format_planet_moon_combo()` wraps the call in try/except and returns `None` on failure. Log the error                                                                                       |
| i18n keys missing in fa.json                                                        | Persian users see English fallback text                                   | Run parity check from Phase 8, step 4. Fallback language is `en` (configured in `i18n/config.ts`). Missing keys show English — ugly but functional                                           |
| Frontend TypeScript interfaces don't match API response                             | Runtime type mismatches, no errors at compile time                        | TypeScript interfaces must mirror the Pydantic models exactly. If API adds a field, add to TS interface. Use API response fixture in tests                                                   |
| MoonPhaseDisplay receives null/undefined moon data                                  | Component crash (React error boundary)                                    | `CosmicCyclePanel` must check for null before rendering child components. Each child component should also have an early return for undefined props                                          |
| `en.json` / `fa.json` JSON syntax error after editing                               | i18n initialization fails, app shows raw keys                             | Validate JSON after every edit: `node -e "require('./frontend/src/locales/en.json')"`. If broken, check for trailing commas or missing quotes                                                |
| Illumination bar shows negative or >100% values                                     | Visual glitch (bar overflows or goes negative)                            | Clamp value in component: `Math.max(0, Math.min(100, illumination))`. Add test for boundary values                                                                                           |

---

## DESIGN DECISIONS

| Decision                                      | Choice                                                                                      | Rationale                                                                                                                                   |
| --------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Formatter as static class vs functions        | Static class (`CosmicFormatter`)                                                            | Consistent with framework convention (`MoonEngine`, `GanzhiEngine` are classes with `@staticmethod`). Easier to mock in tests               |
| Where to put cosmic formatter                 | `services/oracle/oracle_service/cosmic_formatter.py`                                        | Same level as `framework_bridge.py`. Part of the Oracle service layer, not the framework itself                                             |
| Expand existing Pydantic models vs new models | Both — expand `MoonData`/`GanzhiData`, create new `CurrentMomentData`/`CosmicCycleResponse` | Backward compatible (existing fields unchanged). New models for new data. `CosmicCycleResponse` wraps everything                            |
| Planet-Moon combo from SignalCombiner         | Import and call at formatting time                                                          | The 56 planet×moon combinations already exist in the framework. No reason to duplicate                                                      |
| i18n key structure                            | Flat under `oracle.cosmic.*`                                                                | Consistent with existing `oracle.*` keys. No deep nesting (phase names, animals, elements all at same level)                                |
| Component composition vs monolith             | Three components (Moon, Ganzhi, Panel)                                                      | Single responsibility. Moon and Ganzhi can be reused independently (e.g., in reading details, summary tabs). Panel is the composition layer |
| Compact mode                                  | Boolean prop on each component                                                              | Reading results page may need compact cosmic display. Profile page may need full display. Same components, different density                |

---

## HANDOFF

**Created:**

- `services/oracle/oracle_service/cosmic_formatter.py` — `CosmicFormatter` with `format_cosmic_cycles()` entry point
- `frontend/src/components/oracle/MoonPhaseDisplay.tsx` — Moon phase display component
- `frontend/src/components/oracle/GanzhiDisplay.tsx` — Chinese zodiac display component
- `frontend/src/components/oracle/CosmicCyclePanel.tsx` — Combined cosmic panel
- `services/oracle/tests/test_cosmic_formatter.py` — 10+ backend tests
- `frontend/src/components/oracle/__tests__/MoonPhaseDisplay.test.tsx` — 5 tests
- `frontend/src/components/oracle/__tests__/GanzhiDisplay.test.tsx` — 5 tests
- `frontend/src/components/oracle/__tests__/CosmicCyclePanel.test.tsx` — 5 tests

**Modified:**

- `api/app/models/oracle.py` — Expanded `MoonData`, `GanzhiData`; added `CurrentMomentData`, `PlanetMoonCombo`, `CosmicCycleResponse`
- `frontend/src/locales/en.json` — Added `oracle.cosmic` section (50+ keys)
- `frontend/src/locales/fa.json` — Added `oracle.cosmic` section (50+ keys, Persian)
- `frontend/src/types/index.ts` — Added `MoonPhaseData`, `GanzhiCycleData`, `GanzhiFullData`, `CurrentMomentData`, `PlanetMoonCombo`, `CosmicCycleData` interfaces

**Next session (Session 12) receives:**

- `CosmicFormatter` available for formatting moon/ganzhi/current data from any framework reading
- `CosmicCyclePanel` component ready to embed in reading result views
- `MoonPhaseDisplay` and `GanzhiDisplay` available as standalone components
- All cosmic i18n terms in place for both EN and FA
- Expanded Pydantic models ready for heartbeat and location data additions (Session 12 scope)
- TypeScript interfaces that Session 12 can extend for heartbeat/location display
