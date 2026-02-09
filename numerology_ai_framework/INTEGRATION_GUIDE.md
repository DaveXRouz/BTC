# Integration Guide for AI Models

> **Note:** For the most comprehensive integration guide with JSON schemas, system prompt templates, and Flask/FastAPI code templates, see `logic/06_API_INTEGRATION_TEMPLATE.md`.

## Purpose

This guide shows AI models how to integrate the FC60 Numerology Framework into their workflows for generating high-confidence numerological readings.

---

## STEP-BY-STEP INTEGRATION

### Step 1: Import the Framework

```python
import sys
sys.path.append('/path/to/numerology_ai_framework')

from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime
```

### Step 2: Gather User Data

Ask the user for:

- Full name (required)
- Birth date: day, month, year (required)
- Mother's name (optional - increases confidence by 10%)
- Gender (optional - adds polarity data)
- Location coordinates (optional - adds element mapping)
- Heart rate / BPM (optional - adds rhythm data)
- Current date/time (optional - defaults to now)
- Timezone offset (optional - defaults to UTC)

Example prompt:

```
"To generate your numerological reading, I need:
1. Your full name (as it appears on official documents)
2. Your birth date (day, month, year)
3. (Optional) Your mother's full name - adds depth
4. (Optional) Your gender - adds polarity data
5. (Optional) Your location - adds elemental mapping
6. (Optional) Your resting heart rate - adds rhythm data"
```

### Step 3: Generate Reading

#### Full Data Example (all 7 inputs)

```python
reading = MasterOrchestrator.generate_reading(
    full_name="Alice Johnson",
    birth_day=15,
    birth_month=7,
    birth_year=1990,
    current_date=datetime(2026, 2, 9),
    mother_name="Barbara Johnson",
    gender="female",
    latitude=40.7,
    longitude=-74.0,
    actual_bpm=68,
    current_hour=14,
    current_minute=30,
    current_second=0,
    tz_hours=-5,
    tz_minutes=0,
    numerology_system='pythagorean',
)
```

#### Minimal Data Example (name + birthdate only)

```python
reading = MasterOrchestrator.generate_reading(
    full_name="James Chen",
    birth_day=5,
    birth_month=3,
    birth_year=1988,
    current_date=datetime.now(),
)
```

#### Stamp-Only Mode (no personal data needed)

```python
stamp = MasterOrchestrator.generate_reading(
    full_name="",
    birth_day=1,
    birth_month=1,
    birth_year=2000,
    current_date=datetime(2026, 2, 9),
    current_hour=14,
    current_minute=30,
    current_second=0,
    mode="stamp_only",
)
print(f"FC60: {stamp['fc60_stamp']['fc60']}")
print(f"J60:  {stamp['fc60_stamp']['j60']}")
print(f"CHK:  {stamp['fc60_stamp']['chk']}")
```

### Step 4: Check Confidence

```python
confidence = reading['confidence']['score']
level = reading['confidence']['level']  # 'low', 'medium', 'high', 'very_high'

if confidence < 65:
    caveat = "This reading is based on limited data. "
elif confidence < 75:
    caveat = "Good confidence level. "
else:
    caveat = ""
```

### Step 5: Extract Key Information

```python
# Core numerology
life_path = reading['numerology']['life_path']  # {number, title, message}
expression = reading['numerology']['expression']
soul_urge = reading['numerology']['soul_urge']
personality = reading['numerology']['personality']
personal_year = reading['numerology']['personal_year']
personal_month = reading['numerology']['personal_month']
personal_day = reading['numerology']['personal_day']

# FC60 universal address
fc60_stamp = reading['fc60_stamp']['fc60']  # e.g., "LU-OX-OXWA 🌙TI-HOWU-RAWU"
j60 = reading['fc60_stamp']['j60']          # JDN in base-60
chk = reading['fc60_stamp']['chk']          # Checksum token

# Current moment context
current_planet = reading['current']['planet']
current_domain = reading['current']['domain']
current_weekday = reading['current']['weekday']

# Cosmic cycles
moon = reading['moon']      # {phase_name, emoji, age, illumination, energy, best_for, avoid}
ganzhi = reading['ganzhi']  # {year: {gz_token, traditional_name, element, ...}, day: {...}}

# Personal rhythm
heartbeat = reading['heartbeat']  # {bpm, element, total_lifetime_beats, ...}

# Location
location = reading['location']    # {element, timezone_estimate, lat_hemisphere, ...} or None

# Patterns
patterns = reading['patterns']['detected']  # List of detected patterns

# Full synthesis text
synthesis = reading['synthesis']  # Complete human-readable reading
```

### Step 6: Generate Response

Use the `reading['synthesis']` as the base output, or build your own:

```python
response = f"""
NUMEROLOGICAL READING FOR {reading['person']['name']}

CORE IDENTITY
Life Path {life_path['number']} - The {life_path['title']}
"{life_path['message']}"

Expression: {expression} | Soul Urge: {soul_urge} | Personality: {personality}

THIS YEAR: Personal Year {personal_year}
THIS MONTH: Personal Month {personal_month}
TODAY: Personal Day {personal_day}

UNIVERSAL ADDRESS: {fc60_stamp}

MOON: {moon['emoji']} {moon['phase_name']} (age {moon['age']}d)
Energy: {moon['energy']} | Best for: {moon['best_for']}

GANZHI YEAR: {ganzhi['year']['traditional_name']} ({ganzhi['year']['gz_token']})
"""

if patterns:
    response += "\nPATTERNS DETECTED:\n"
    for pattern in patterns:
        response += f"  - {pattern['message']}\n"

response += f"\nConfidence: {reading['confidence']['score']}% ({reading['confidence']['level']})"
```

---

## OUTPUT SECTIONS EXPLAINED

The `reading['synthesis']` contains 9 sections:

| Section           | Key                                | Content                            |
| ----------------- | ---------------------------------- | ---------------------------------- |
| Header            | `translation['header']`            | Person name, date, confidence      |
| Universal Address | `translation['universal_address']` | FC60, J60, Y60 stamps              |
| Core Identity     | `translation['core_identity']`     | Life Path + Expression + Soul Urge |
| Right Now         | `translation['right_now']`         | Planetary day + moon + hour energy |
| Patterns          | `translation['patterns']`          | Repeated numbers/animals           |
| The Message       | `translation['message']`           | 3-5 sentence synthesis             |
| Today's Advice    | `translation['advice']`            | 3 actionable items                 |
| Caution           | `translation['caution']`           | Shadow warnings                    |
| Footer            | `translation['footer']`            | Confidence, sources, disclaimer    |

Access individual sections via `reading['translation']`.

---

## ERROR HANDLING

### Common Issues & Solutions

**Issue 1: Invalid Date**

```python
try:
    reading = MasterOrchestrator.generate_reading(...)
except ValueError as e:
    return f"I couldn't process that date: {e}. Please check your birth date."
```

**Issue 2: Missing Required Data**

```python
if not full_name or not birth_day or not birth_month or not birth_year:
    return "I need your full name and complete birth date to generate a reading."
```

**Issue 3: Name Contains Numbers**

```python
if any(char.isdigit() for char in full_name):
    return "Please provide your name using only letters."
```

---

## ADVANCED USAGE

### Comparing Two People (Compatibility)

```python
reading_a = MasterOrchestrator.generate_reading(...)
reading_b = MasterOrchestrator.generate_reading(...)

lp_a = reading_a['numerology']['life_path']['number']
lp_b = reading_b['numerology']['life_path']['number']
```

### Time-Specific Queries

```python
# "What's my energy for next Tuesday?"
reading = MasterOrchestrator.generate_reading(
    ...,
    current_date=datetime(2026, 2, 11),
    current_hour=12, current_minute=0, current_second=0,
)
```

### FC60 Stamp for Any Integer

```python
from core.fc60_stamp_engine import FC60StampEngine
token = FC60StampEngine.encode_integer(2026)  # "HOMT-ROFI"
```

---

## BEST PRACTICES FOR AI MODELS

### DO:

- Always state confidence level upfront
- Use patterns as the strongest signals
- Ground interpretations in the actual numbers
- Explain what each number means before interpreting
- Use "the numbers suggest" language, never absolute predictions
- Respect user privacy

### DON'T:

- Make absolute predictions ("You WILL meet someone")
- Claim higher confidence than the score indicates
- Invent numbers or patterns not in the reading
- Ignore low confidence scores
- Use numerology to replace professional advice
- Create dependency ("You must consult me daily")

---

## TESTING YOUR INTEGRATION

```python
reading = MasterOrchestrator.generate_reading(
    full_name="Test User",
    birth_day=1,
    birth_month=1,
    birth_year=2000,
    current_date=datetime(2026, 2, 9)
)

assert reading['numerology']['life_path']['number'] == 4  # 1+1+2+0+0+0 → 4
assert reading['person']['age_years'] == 26
assert reading['birth']['weekday'] == 'Saturday'
assert 50 <= reading['confidence']['score'] <= 95
assert reading['fc60_stamp']['fc60']  # Not empty
assert reading['moon']['phase_name']  # Not empty

print("Integration test passed")
```

---

## TROUBLESHOOTING

**Reading seems wrong?**

1. Check input data - are day/month/year correct?
2. Verify name spelling - every letter matters
3. Check system choice - Pythagorean vs Chaldean give different results

**Confidence too low?**

- Add mother's name → +10%
- Add location coordinates → +5%
- Add heart rate → +5%
- Add exact time → +5%

**Pattern detection empty?**

- This is normal if all numbers are unique
- Not every reading has patterns - that's valid

**Moon phase seems off?**

- Accuracy is ±0.5 days (synodic approximation)
- This is sufficient for symbolic readings

---

**You're now ready to integrate FC60 Numerology into your AI workflow!**
