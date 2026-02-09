# FC60 Numerology AI Framework -- Input Collection Guide

**Version:** 1.0
**Purpose:** How to gather, validate, and prioritize user inputs for numerological readings.

---

## Input Priority Order

The framework processes inputs in this priority order (highest signal weight first):

```
heartbeat > location > time > name > gender > DOB > mother
```

Higher-priority inputs carry more immediate, moment-specific information. Lower-priority inputs provide stable, foundational context.

---

## The 6 Input Dimensions (+ 1 Supplementary)

### Dimension 1: Heartbeat (Highest Priority)

**What to ask:**

> "Do you know your current resting heart rate? If you have a smartwatch or fitness tracker, what does it say right now?"

**Why it matters:**
The heartbeat is the most personal, real-time biological signal. It anchors the reading to your literal physical state at this exact moment. No two people share the same heartbeat signature across a lifetime.

**What it produces:**

- BPM (beats per minute) -- actual if provided, or estimated from age
- Heartbeat element (BPM mod 5 maps to Wood/Fire/Earth/Metal/Water)
- Daily beat count (BPM x 60 x 24)
- Rhythm token (daily beats mod 60 -> TOKEN60)
- Total lifetime beats (cumulative estimate based on age-specific BPM)
- Life pulse signature (lifetime beats encoded in base-60)

**Fallback if not provided:**
The engine estimates BPM from age using a standard table:

| Age Range | Estimated BPM |
| --------- | ------------- |
| 0-1       | 120           |
| 1-3       | 110           |
| 3-5       | 100           |
| 5-10      | 90            |
| 10-15     | 80            |
| 15-25     | 72            |
| 25-35     | 70            |
| 35-50     | 72            |
| 50-65     | 74            |
| 65-80     | 76            |
| 80+       | 78            |

The output will indicate `bpm_source: "estimated"` rather than `"actual"`.

---

### Dimension 2: Location

**What to ask:**

> "Where are you right now? A city name is fine, or if you know your coordinates, even better."

**Why it matters:**
Your geographic position determines which elemental zone you occupy and which hemisphere polarities influence the reading. It also enables timezone estimation when the user does not provide an explicit offset.

**What it produces:**

- Latitude element (Fire/Earth/Metal/Water/Wood based on latitude zone)
- Hemisphere polarity (N=Yang, S=Yin for latitude; E=Yang, W=Yin for longitude)
- Timezone estimate (rounded from longitude / 15)

**Latitude Zone Table:**

| Absolute Latitude | Element | Example Cities               |
| ----------------- | ------- | ---------------------------- |
| 0 - 15 degrees    | Fire    | Singapore, Bogota, Nairobi   |
| 15 - 30 degrees   | Earth   | Cairo, New Delhi, Houston    |
| 30 - 45 degrees   | Metal   | New York, Tokyo, Rome        |
| 45 - 60 degrees   | Water   | London, Paris, Moscow        |
| 60 - 90 degrees   | Wood    | Helsinki, Anchorage, Tromsoe |

**Fallback if not provided:**
Location data is omitted from the reading entirely. The confidence score loses 5%. The reading remains valid but lacks spatial grounding.

---

### Dimension 3: Time

**What to ask:**

> "What time is it for you right now? And what timezone are you in?"

**Why it matters:**
Time determines the FC60 stamp's time component, the hour animal, the minute texture, the half marker (AM/PM), and the Ganzhi hour pillar. It is also essential for accurate planetary day determination if near midnight.

**What it produces (time hierarchy):**

- Second -> TOKEN60 encoding in stamp
- Minute -> TOKEN60 encoding, minute animal (first 2 chars)
- Hour -> ANIMALS[hour % 12], half marker (sun/moon), hour Ganzhi
- Day -> Day of month TOKEN60, day Ganzhi
- Weekday -> Planetary ruler (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn)
- Month -> ANIMALS[month - 1], monthly cycle
- Year -> Base-60 encoded year, Y2K offset token
- Cycle -> 60-year Ganzhi sexagenary cycle

**Fallback if not provided:**
If no time is given, the engine uses `datetime.now()` for the current moment. If only the date is known, the stamp is generated in date-only mode (no time component, no hour/minute/second signals). The half marker, hour animal, and minute texture will be absent.

---

### Dimension 4: Name (Required)

**What to ask:**

> "What is your full name -- the one you feel most represents you?"

**Why it matters:**
The full name is the foundation for three core numerology numbers: Expression (all letters), Soul Urge (vowels only), and Personality (consonants only). Each letter maps to a numeric value via the Pythagorean or Chaldean table, and the sum is reduced to a single digit (or master number).

**What it produces:**

- Expression number (full name, all letters)
- Soul Urge number (vowels only: A, E, I, O, U, Y)
- Personality number (consonants only)

**Fallback if not provided:**
This input is **required**. The framework cannot generate a reading without a name. If the user declines to share their full name, ask for a preferred name or initials. Any alphabetic string will work.

---

### Dimension 5: Gender

**What to ask:**

> "Would you like to share your gender? This is optional and simply adds a polarity layer."

**Why it matters:**
Gender maps to a polarity value that adds a Yin/Yang layer to the reading. This is not a judgment -- it is a symbolic mapping used in traditional numerological systems.

**What it produces:**

- Polarity label: male = Yang (+1), female = Yin (-1), unspecified = Neutral (0)

**Fallback if not provided:**
Defaults to Neutral (polarity 0). The reading proceeds without this layer. No confidence impact.

---

### Dimension 6: Date of Birth (Required)

**What to ask:**

> "When were you born? I need the day, month, and year."

**Why it matters:**
The birthdate is required for the Life Path number (the single most important numerology number), Personal Year/Month/Day calculations, and age derivation (which feeds the heartbeat engine).

**What it produces:**

- Life Path number (day + month + year, each reduced separately, then summed and reduced)
- Personal Year (birth_month + birth_day + current_year, reduced)
- Personal Month (Personal Year + current_month, reduced)
- Personal Day (Personal Month + current_day, reduced)
- Age in years and days (for heartbeat estimation)
- Birth JDN (for birth weekday and birth planet)

**Fallback if not provided:**
This input is **required**. Without a birthdate, the Life Path cannot be calculated and age cannot be determined for the heartbeat engine. Ask the user directly.

---

### Dimension 7: Mother's Name (Supplementary)

**What to ask:**

> "If you are comfortable sharing, what is your mother's full name? This adds a layer of maternal influence to the reading."

**Why it matters:**
The mother's name adds an Expression number that represents maternal influence. This is a supplementary signal that enriches the reading with lineage context.

**What it produces:**

- Mother influence number (Expression number of mother's full name)

**Fallback if not provided:**
Omitted from the profile. Confidence score loses 10%. The reading is still valid without it.

---

## Time Hierarchy Detail

Time unfolds in nested cycles, each carrying its own symbolic weight:

```
second   --> TOKEN60(second)           Texture, micro-rhythm
  |
minute   --> TOKEN60(minute)           Current texture, minute animal
  |
hour     --> ANIMALS[hour % 12]        Hour animal, Ganzhi hour pillar
  |          + half marker (☀ or 🌙)
  |
day      --> TOKEN60(day)              Day-of-month energy (animal + element)
  |          + Ganzhi day pillar
  |
weekday  --> (JDN + 1) mod 7           Planetary ruler and domain
  |
month    --> ANIMALS[month - 1]        Monthly animal cycle
  |
year     --> encode_base60(year)       Annual cycle, Y2K offset
  |          + Ganzhi year pillar
  |
cycle    --> 60-year Ganzhi cycle      Background generational energy
```

Each level nests within the one above. Signals closer to "second" are more fleeting; signals closer to "cycle" are more enduring but carry less immediate weight.

---

## Conversation Flow Template

This is a model for how to gather inputs naturally. The tone should be warm, curious, and unhurried -- not clinical or form-like.

### Example Dialogue

```
AI:   Welcome. I would love to create a reading for you.
      Let's start with your name -- the one that feels most like you.

User: My name is Sarah Chen.

AI:   Beautiful. And when were you born, Sarah? I need the day, month, and year.

User: March 14, 1988.

AI:   March 14 -- a day that carries interesting energy.
      Now, where are you right now? A city name works perfectly.

User: I'm in Seattle.

AI:   The Pacific Northwest. Got it.
      What time is it for you right now?

User: It's about 3:15 PM.

AI:   And your timezone -- that would be Pacific Time, so UTC-8?

User: Yes, PST.

AI:   Two more optional questions that can deepen the reading.
      Do you happen to know your current heart rate?
      A smartwatch or fitness tracker reading would be perfect.

User: My watch says 72 BPM.

AI:   And if you're comfortable, what is your mother's full name?
      This adds a layer of lineage to the reading.

User: Linda Chen.

AI:   Thank you, Sarah. I have everything I need.
      Let me run the calculations now.
```

Key principles:

- Ask one or two questions at a time, never a full form
- Acknowledge each answer before moving to the next question
- Make optional inputs feel genuinely optional
- Never pressure for information the user hesitates to share
- Explain briefly why each input matters if the user seems curious

---

## Minimum Required vs Optional Inputs

### Required Inputs

| Input       | Why Required                                 |
| ----------- | -------------------------------------------- |
| Full name   | Expression, Soul Urge, Personality numbers   |
| Birth day   | Life Path, Personal cycles, age              |
| Birth month | Life Path, Personal cycles                   |
| Birth year  | Life Path, Personal cycles, age, Ganzhi year |

### Optional Inputs

| Input         | Default Behavior   | Confidence Impact |
| ------------- | ------------------ | ----------------- |
| Mother's name | Omitted            | +10%              |
| Current time  | Uses system time   | (implicit)        |
| Timezone      | Assumes UTC        | (implicit)        |
| Location      | Omitted            | +5%               |
| Heartbeat     | Estimated from age | +5%               |
| Gender        | Neutral polarity   | (no impact)       |

### Confidence Score Buildup

The confidence score starts at a base of 50% and accumulates as follows:

```
Base confidence:                               50%
  + Numerology profile (always present):      +10%
  + Mother's name provided:                   +10%
  + Moon data (always calculated):             +5%
  + Ganzhi data (always calculated):           +5%
  + Heartbeat data (always calculated*):       +5%
  + Location data provided:                    +5%
  + Master number detected in Life Path:       +5%
  + Animal repetitions detected:               +5%
                                              -----
Maximum possible:                              95%
```

\*Heartbeat is always calculated (estimated if not provided), so its +5% is always present. However, providing actual BPM increases the accuracy of the heartbeat element, even though the confidence score does not distinguish between estimated and actual BPM.

### Confidence Levels

| Score Range | Level     |
| ----------- | --------- |
| 85 - 95%    | Very High |
| 75 - 84%    | High      |
| 65 - 74%    | Medium    |
| 50 - 64%    | Low       |

---

## Input Validation Rules

The engine validates all inputs before processing:

- **Date:** Year must produce a valid Gregorian date. Month 1-12. Day within month bounds (leap year aware).
- **Time:** Hour 0-23. Minute 0-59. Second 0-59.
- **Timezone:** Hours -12 to +14. Minutes 0-59.
- **Name:** Any string with at least one alphabetic character. Non-alpha characters are ignored.
- **Coordinates:** Latitude -90 to +90. Longitude -180 to +180.
- **BPM:** Any positive integer (realistic range is 40-200, but the engine does not reject outliers).

If validation fails, the engine raises a `ValueError` with a descriptive message. The AI should catch this, explain the issue to the user, and ask for corrected input.

---

## What to Do When Inputs Are Ambiguous

| Situation                                    | Resolution                                                          |
| -------------------------------------------- | ------------------------------------------------------------------- |
| User gives city name, not coordinates        | Look up approximate lat/lon for the city                            |
| User says "afternoon" not exact time         | Ask for a more specific time, or use 14:00 as default               |
| User gives nickname, not full name           | Ask if they have a full legal or preferred name; use what they give |
| User gives DOB as "the 80s"                  | Ask for specific year; explain Life Path requires exact date        |
| User declines to share mother's name         | Accept gracefully; note reduced confidence                          |
| User gives BPM as a range ("60-70")          | Use the midpoint (65) or ask for current reading                    |
| Timezone is ambiguous (e.g., "EST" vs "EDT") | Ask if daylight saving time is in effect                            |
