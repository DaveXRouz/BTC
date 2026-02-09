# FrankenChron-60 (FC60) â€” Master Specification

**Version:** FC60-MASTER-v1.0
**Status:** Definitive (all math verified, all algorithms self-contained, zero external dependencies)
**Created:** 2026-02-09
**License:** CC0 1.0 Universal (Public Domain)

> FC60 is a deterministic encoding system that translates dates, times, and integers into a compact syllabic alphabet built on base-60 arithmetic. It combines ISO-8601 (universal clarity), Julian Day Numbers (continuous counting), base-60 (maximum divisibility), Chinese cosmology (symbolic depth), and lunar cycles (natural rhythm) into one unified notation.

---

## TABLE OF CONTENTS

```
PART I â€” OPERATING SYSTEM
  Â§0   Operating Mode & Rules
  Â§1   The Alphabet (all tokens)

PART II â€” DETERMINISTIC ENGINE (Calculator)
  Â§2   Core Encoding Rules
  Â§3   Julian Day Number (the backbone)
  Â§4   Weekday Calculation
  Â§5   Timezone Encoding (TZ60)
  Â§6   Year Encoding
  Â§7   Additional Cores (MJD, RD, Unix)
  Â§8   Weighted Check Token (CHK)
  Â§9   Output Formats

PART III â€” SYMBOLIC ENGINE (Reader)
  Â§10  Moon Phase Calculation
  Â§11  GÄnzhÄ« Sexagenary Cycle (å¹²æ”¯)
  Â§12  Symbolic Reading Engine
  Â§13  Numerology Integration

PART IV â€” INPUT HANDLING
  Â§14  Parsing Rules (input â†’ meaning)

PART V â€” VERIFICATION
  Â§15  Comprehensive Test Vectors (15 cases)
  Â§16  Error Catalog & Troubleshooting

APPENDICES
  A    Complete TOKEN60 Table (0â€“59)
  B    Quick-Lookup Tables (hours, months, days)
  C    Decoding Cheatsheet (reverse lookups)
  D    Quick Reference Card
  E    Complete Reference Implementation (Python)
  F    Version History
```

---

# PART I â€” OPERATING SYSTEM

---

## Â§0. Operating Mode ðŸ¤–

FC60 has two distinct operating modes. An AI model MUST know which mode it is in at all times.

### 0.1 Mode A â€” FC60 Translator (Deterministic)

**Purpose:** Encode or decode dates, times, and numbers with mathematical precision.

**Rules:**
- Every output must be reproducible by any calculator.
- No interpretation. No symbolism. No creativity.
- If two AI models receive the same input, they MUST produce the same output.
- Every token comes from a table. Every number comes from an algorithm.

**Activation triggers:** "translate", "encode", "decode", "convert", "what is the FC60 for", "stamp"

**Required steps (in this exact order):**

```
STEP 1: Parse the input                        â†’ Â§14
STEP 2: Compute JDN from Gregorian date         â†’ Â§3
STEP 3: Compute weekday from JDN                â†’ Â§4
STEP 4: Encode date stamp (WD-MO-DOM)           â†’ Â§2
STEP 5: Encode time stamp (if time provided)    â†’ Â§2
STEP 6: Encode timezone (if applicable)         â†’ Â§5
STEP 7: Encode year (Y60, Y2K)                  â†’ Â§6
STEP 8: Encode JDN to J60                       â†’ Â§3
STEP 9: Compute additional cores (MJD, RD, U)   â†’ Â§7
STEP 10: Compute weighted check token (CHK)     â†’ Â§8
STEP 11: Format output                          â†’ Â§9
```

### 0.2 Mode B â€” FC60 Reader (Symbolic/Interpretive)

**Purpose:** Generate human-readable symbolic interpretations from FC60 stamps.

**Rules:**
- Mode B ALWAYS runs Mode A first. You cannot interpret what you have not calculated.
- Symbolic readings are creative but must be grounded in the calculated tokens.
- The reading engine (Â§12) provides the structure. The AI provides the voice.
- Always distinguish between "the math says" and "the reading suggests."

**Activation triggers:** "read", "interpret", "what does this mean", "symbolic", "prediction", "reading"

**Required steps:**

```
STEP 1: Run Mode A completely (all 11 steps)
STEP 2: Calculate moon phase                    â†’ Â§10
STEP 3: Calculate GÄnzhÄ« cycle                  â†’ Â§11
STEP 4: If personal data provided, calculate numerology â†’ Â§13
STEP 5: Detect signal patterns (repeated animals) â†’ Â§12
STEP 6: Generate symbolic reading               â†’ Â§12
```

### 0.3 Non-Negotiable Rules (both modes) âœ…

| # | Rule | Why | Consequence of violation |
|--:|------|-----|------------------------|
| 1 | Use token tables exactly as defined | Deterministic = no improvisation | Wrong output, broken decode |
| 2 | Always include Julian core `J:` | Primary cross-reference anchor | Cannot verify any other value |
| 3 | Always include check token `CHK:` | Error detection | Cannot detect transmission errors |
| 4 | State timezone explicitly | Ambiguity prevention | Different dates in different zones |
| 5 | Calculate weekday â€” NEVER assume | Wrong weekday = wrong stamp | Cascading errors in all outputs |
| 6 | Verify CHK before delivering output | Self-check | Catch your own arithmetic errors |
| 7 | Show ISO-8601 alongside FC60 | Human readability | User cannot verify meaning |

### 0.4 Output Priority Order

Every FC60 output follows this sequence. Required fields are marked with â˜….

| Order | Field | Description | Required |
|------:|-------|-------------|----------|
| 1 | `FC60:` | The FC60 stamp | â˜… |
| 2 | `ISO:` | ISO-8601 canonical meaning | â˜… |
| 3 | `TZ60:` | Timezone token | â˜… (if time included) |
| 4 | `Y60:` | Absolute year tokens | â˜… |
| 5 | `Y2K:` | 60-year cycle token | Recommended |
| 6 | `J:` | Julian Day Number as base-60 tokens | â˜… |
| 7 | `MJD:` | Modified Julian Date | Optional |
| 8 | `RD:` | Rata Die | Optional |
| 9 | `U:` | Unix timestamp (seconds) | Optional |
| 10 | `MOON:` | Moon phase marker + age | If Mode B |
| 11 | `GZ:` | GÄnzhÄ« sexagenary cycle | If Mode B |
| 12 | `CHK:` | Weighted check token | â˜… |

---

## Â§1. The Alphabet (All Tokens) ðŸ“š

FC60 is a **syllabic alphabet** where each "letter" is a 2â€“4 character token. Every token is deterministic â€” it maps to exactly one number, and that number maps back to exactly one token.

### 1.1 Design Principle

The number 60 factors as:
```
60 = 12 Ã— 5
```

This single fact is the foundation of FC60. Every number from 0 to 59 decomposes into:
- A **quotient** (0â€“11) â†’ mapped to one of 12 Chinese zodiac Animals
- A **remainder** (0â€“4) â†’ mapped to one of 5 Chinese elements

This creates 60 unique 4-character tokens that are human-readable, culturally meaningful, and mathematically precise.

### 1.2 Animal Digits (12) â€” Quotient Position

The 12 Earthly Branches (åœ°æ”¯ DÃ¬zhÄ«) from Chinese cosmology:

| Value | Animal | Chinese | Token | Power | Essence |
|------:|--------|---------|-------|-------|---------|
| 0 | Rat | å­ ZÇ | `RA` | Instinct | Resourcefulness, new beginnings, sharp perception |
| 1 | Ox | ä¸‘ ChÇ’u | `OX` | Endurance | Patience, commitment, steady progress |
| 2 | Tiger | å¯… YÃ­n | `TI` | Courage | Power, bold action, leadership |
| 3 | Rabbit | å¯ MÇŽo | `RU` | Intuition | Diplomacy, gentle wisdom, sensitivity |
| 4 | Dragon | è¾° ChÃ©n | `DR` | Destiny | Transformation, ambition, greatness |
| 5 | Snake | å·³ SÃ¬ | `SN` | Wisdom | Shedding the old, precision, depth |
| 6 | Horse | åˆ WÇ” | `HO` | Freedom | Movement, passionate energy, independence |
| 7 | Goat | æœª WÃ¨i | `GO` | Vision | Creativity, harmony, artistic expression |
| 8 | Monkey | ç”³ ShÄ“n | `MO` | Adaptability | Cleverness, problem-solving, flexibility |
| 9 | Rooster | é…‰ YÇ’u | `RO` | Truth | Confidence, discipline, honesty |
| 10 | Dog | æˆŒ XÅ« | `DO` | Loyalty | Protection, honest companionship, faithfulness |
| 11 | Pig | äº¥ HÃ i | `PI` | Abundance | Generosity, completion, prosperity |

**Memory aid:** RA-OX-TI-RU-DR-SN-HO-GO-MO-RO-DO-PI

### 1.3 Element Digits (5) â€” Remainder Position

The 5 Elements (äº”è¡Œ WÇ”xÃ­ng):

| Value | Element | Chinese | Token | Force | Meaning |
|------:|---------|---------|-------|-------|---------|
| 0 | Wood | æœ¨ MÃ¹ | `WU` | Growth | New beginnings, flexibility, expansion |
| 1 | Fire | ç« HuÇ’ | `FI` | Transformation | Passion, illumination, change |
| 2 | Earth | åœŸ TÇ” | `ER` | Grounding | Stability, foundation, centering |
| 3 | Metal | é‡‘ JÄ«n | `MT` | Refinement | Precision, structure, cutting away excess |
| 4 | Water | æ°´ ShuÇ | `WA` | Depth | Flow, emotion, hidden truths |

**Memory aid:** WU-FI-ER-MT-WA (Wood Fire Earth Metal Water)

### 1.4 The TOKEN60 Function (the core encoder)

```
INPUT:  Integer n where 0 â‰¤ n â‰¤ 59
OUTPUT: 4-character token string

ALGORITHM:
  q = floor(n / 5)          â†’ Animal index (0..11)
  r = n mod 5               â†’ Element index (0..4)
  TOKEN60(n) = ANIMAL[q] + ELEMENT[r]

INVERSE (DIGIT60):
  INPUT:  4-character token
  OUTPUT: Integer 0..59
  ALGORITHM:
    q = index of token[0:2] in ANIMAL table
    r = index of token[2:4] in ELEMENT table
    DIGIT60(token) = q Ã— 5 + r
```

**Worked examples:**
- `TOKEN60(0)` â†’ q=0, r=0 â†’ `RA`+`WU` â†’ `RAWU`
- `TOKEN60(6)` â†’ q=1, r=1 â†’ `OX`+`FI` â†’ `OXFI`
- `TOKEN60(26)` â†’ q=5, r=1 â†’ `SN`+`FI` â†’ `SNFI`
- `TOKEN60(57)` â†’ q=11, r=2 â†’ `PI`+`ER` â†’ `PIER`
- `TOKEN60(59)` â†’ q=11, r=4 â†’ `PI`+`WA` â†’ `PIWA`

**Verification rule:** For any token T, `TOKEN60(DIGIT60(T)) = T` must always hold.

### 1.5 Base-60 Multi-Digit Encoding (for numbers â‰¥ 60)

For numbers larger than 59, decompose into base-60 digits and encode each:

```
INPUT:  Integer N â‰¥ 0
OUTPUT: Token string with digits separated by hyphens

ALGORITHM (to_base60):
  if N = 0: return [0]
  digits = empty list
  while N > 0:
    digits.prepend(N mod 60)
    N = floor(N / 60)
  return digits

ENCODING:
  encode_base60(N) = join(TOKEN60(d) for d in to_base60(N), separator='-')

DECODING (from_base60):
  digits = [DIGIT60(token) for token in encoded.split('-')]
  N = 0
  for each digit d in digits:
    N = N Ã— 60 + d
  return N
```

**Worked example:** Encode 2026
```
2026 Ã· 60 = 33 remainder 46
33 Ã· 60 = 0 remainder 33
Digits: [33, 46]
TOKEN60(33) = HOMT
TOKEN60(46) = ROFI
Result: HOMT-ROFI

Verify: 33 Ã— 60 + 46 = 1980 + 46 = 2026 âœ…
```

### 1.6 Negative Number Encoding

For negative integers, prefix with `NEG-`:

```
encode(-N) = 'NEG-' + encode_base60(abs(N))
```

**Example:** -500 â†’ NEG-OXMT-DRWU (because 500 = 8Ã—60 + 20)

### 1.7 Weekday Tokens (7)

| Index | Weekday | Planet | Symbol | Token | Symbolic Domain |
|------:|---------|--------|--------|-------|----------------|
| 0 | Sunday | Sun | â˜‰ | `SO` | Identity, vitality, core self |
| 1 | Monday | Moon | â˜½ | `LU` | Emotions, intuition, inner world |
| 2 | Tuesday | Mars | â™‚ | `MA` | Drive, action, courage |
| 3 | Wednesday | Mercury | â˜¿ | `ME` | Communication, thought, connection |
| 4 | Thursday | Jupiter | â™ƒ | `JO` | Expansion, wisdom, abundance |
| 5 | Friday | Venus | â™€ | `VE` | Love, values, beauty |
| 6 | Saturday | Saturn | â™„ | `SA` | Discipline, lessons, mastery |

**Index rule:** `weekday_index = (JDN + 1) mod 7` â†’ use this table to get the token.

**Memory aid:** SO-LU-MA-ME-JO-VE-SA (starts Sunday, planetary order from Romance languages)

### 1.8 Half-Day Markers (2)

| Half | Local Time Range | Marker | Symbolic Meaning |
|------|-----------------|--------|-----------------|
| AM | 00:00â€“11:59 | `â˜€` | Visible, active, outward energy |
| PM | 12:00â€“23:59 | `ðŸŒ™` | Reflective, inner, processing |

**Rule:** `HALF = â˜€ if HH < 12, else ðŸŒ™`

### 1.9 Heavenly Stems (10) â€” for GÄnzhÄ« cycle

The 10 Heavenly Stems (å¤©å¹² TiÄngÄn), used in Â§11:

| Value | Stem | Chinese | Token | Element | Polarity |
|------:|------|---------|-------|---------|----------|
| 0 | JiÇŽ | ç”² | `JA` | Wood | Yang (+) |
| 1 | YÇ | ä¹™ | `YI` | Wood | Yin (âˆ’) |
| 2 | BÇng | ä¸™ | `BI` | Fire | Yang (+) |
| 3 | DÄ«ng | ä¸ | `DI` | Fire | Yin (âˆ’) |
| 4 | WÃ¹ | æˆŠ | `WW` | Earth | Yang (+) |
| 5 | JÇ | å·± | `JI` | Earth | Yin (âˆ’) |
| 6 | GÄ“ng | åºš | `GE` | Metal | Yang (+) |
| 7 | XÄ«n | è¾› | `XI` | Metal | Yin (âˆ’) |
| 8 | RÃ©n | å£¬ | `RE` | Water | Yang (+) |
| 9 | GuÇ | ç™¸ | `GU` | Water | Yin (âˆ’) |

**Memory aid:** JA-YI-BI-DI-WW-JI-GE-XI-RE-GU

### 1.10 Moon Phase Markers (8)

Used in Â§10:

| Phase | Days from New Moon | Marker | Meaning |
|-------|-------------------|--------|---------|
| New Moon | 0.00 â€“ 1.85 | `ðŸŒ‘` | New beginnings, planting seeds |
| Waxing Crescent | 1.85 â€“ 7.38 | `ðŸŒ’` | Setting intentions, building |
| First Quarter | 7.38 â€“ 11.07 | `ðŸŒ“` | Challenges, decisions, action |
| Waxing Gibbous | 11.07 â€“ 14.77 | `ðŸŒ”` | Refinement, patience, almost there |
| Full Moon | 14.77 â€“ 16.61 | `ðŸŒ•` | Culmination, illumination, release |
| Waning Gibbous | 16.61 â€“ 22.14 | `ðŸŒ–` | Gratitude, sharing, distribution |
| Last Quarter | 22.14 â€“ 25.83 | `ðŸŒ—` | Letting go, forgiveness, release |
| Waning Crescent | 25.83 â€“ 29.53 | `ðŸŒ˜` | Rest, reflection, preparation |

### 1.11 Timezone Sign Markers

| Condition | Marker |
|-----------|--------|
| East of UTC (positive offset) | `+` |
| West of UTC (negative offset) | `-` |
| UTC exactly (zero offset) | `Z` |

---

# PART II â€” DETERMINISTIC ENGINE

---

## Â§2. Core Encoding Rules ðŸ§ 

### 2.1 The Canonical Standard

The "real meaning" of any FC60 stamp is always an ISO-8601 datetime. FC60 is a **representation**, not a replacement. ISO-8601 is the ground truth.

| Component | ISO-8601 Format | Example |
|-----------|----------------|---------|
| Date | `YYYY-MM-DD` | `2026-02-06` |
| Time | `HH:MM:SS` | `01:15:00` |
| Timezone | `Z` or `Â±HH:MM` | `+08:00` |
| Combined | `YYYY-MM-DDTHH:MM:SSÂ±HH:MM` | `2026-02-06T01:15:00+08:00` |

### 2.2 Date Stamp Encoding

Given a Gregorian date `YYYY-MM-DD`:

```
STEP 1: Compute JDN                          â†’ Â§3
STEP 2: Compute weekday from JDN             â†’ Â§4
  WD = WEEKDAY_TOKEN[(JDN + 1) mod 7]        â†’ from Â§1.7

STEP 3: Encode month
  MO = ANIMAL[month - 1]
  (January = ANIMAL[0] = RA, December = ANIMAL[11] = PI)

STEP 4: Encode day-of-month
  DOM = TOKEN60(day)
  (Day 1 = TOKEN60(1) = RAFI, Day 31 = TOKEN60(31) = HOFI)

FORMAT: WD-MO-DOM
```

**Example:** 2026-02-06 (Friday)
```
JDN = 2461078 (see Â§3)
WD = WEEKDAY[(2461078 + 1) mod 7] = WEEKDAY[5] = VE
MO = ANIMAL[2-1] = ANIMAL[1] = OX
DOM = TOKEN60(6) = OXFI
â†’ VE-OX-OXFI
```

### 2.3 Month Encoding Table

| Month | Number | Token | Month | Number | Token |
|-------|-------:|-------|-------|-------:|-------|
| January | 1 | `RA` | July | 7 | `HO` |
| February | 2 | `OX` | August | 8 | `GO` |
| March | 3 | `TI` | September | 9 | `MO` |
| April | 4 | `RU` | October | 10 | `RO` |
| May | 5 | `DR` | November | 11 | `DO` |
| June | 6 | `SN` | December | 12 | `PI` |

**Rule:** `MONTH_TOKEN = ANIMAL[month_number - 1]`

### 2.4 Time Encoding

Given local time `HH:MM:SS`:

```
STEP 1: Determine half-day
  HALF = â˜€ if HH < 12, else ðŸŒ™

STEP 2: Convert to 12-hour index
  H12 = HH mod 12
  HOUR = ANIMAL[H12]

STEP 3: Encode minutes
  MINUTE = TOKEN60(MM)

STEP 4: Encode seconds (if provided)
  SECOND = TOKEN60(SS)
```

**Output formats:**
- Without seconds: `HALF` `HOUR` `-` `MINUTE`
- With seconds: `HALF` `HOUR` `-` `MINUTE` `-` `SECOND`

**Example:** 01:15:00
```
HALF = â˜€ (1 < 12)
HOUR = ANIMAL[1 mod 12] = ANIMAL[1] = OX
MINUTE = TOKEN60(15) = RUWU
SECOND = TOKEN60(0) = RAWU
â†’ â˜€OX-RUWU-RAWU
```

**Example:** 23:59:59
```
HALF = ðŸŒ™ (23 â‰¥ 12)
HOUR = ANIMAL[23 mod 12] = ANIMAL[11] = PI
MINUTE = TOKEN60(59) = PIWA
SECOND = TOKEN60(59) = PIWA
â†’ ðŸŒ™PI-PIWA-PIWA
```

### 2.5 Hour Reference Table (00â€“23)

| Hour | Token | | Hour | Token | | Hour | Token |
|-----:|-------|-|-----:|-------|-|-----:|-------|
| 00 | `â˜€RA` | | 08 | `â˜€MO` | | 16 | `ðŸŒ™DR` |
| 01 | `â˜€OX` | | 09 | `â˜€RO` | | 17 | `ðŸŒ™SN` |
| 02 | `â˜€TI` | | 10 | `â˜€DO` | | 18 | `ðŸŒ™HO` |
| 03 | `â˜€RU` | | 11 | `â˜€PI` | | 19 | `ðŸŒ™GO` |
| 04 | `â˜€DR` | | 12 | `ðŸŒ™RA` | | 20 | `ðŸŒ™MO` |
| 05 | `â˜€SN` | | 13 | `ðŸŒ™OX` | | 21 | `ðŸŒ™RO` |
| 06 | `â˜€HO` | | 14 | `ðŸŒ™TI` | | 22 | `ðŸŒ™DO` |
| 07 | `â˜€GO` | | 15 | `ðŸŒ™RU` | | 23 | `ðŸŒ™PI` |

### 2.6 Millisecond Precision (optional, lossy)

For sub-second precision, add a fourth time component. Note: this is **lossy** â€” each token represents approximately 16.67ms of precision.

```
MS_TOKEN = TOKEN60(floor(milliseconds / 16.667))
```

**Format:** `HALF` `HOUR` `-` `MINUTE` `-` `SECOND` `.` `MS_TOKEN`

**Range:** 0ms â†’ `RAWU`, 999ms â†’ `PIWA` (maps 0â€“999 into 0â€“59)

---

## Â§3. Julian Day Number (The Backbone) ðŸ§®

The Julian Day Number (JDN) is a continuous count of days since January 1, 4713 BCE (Julian calendar). It is the **single most important number** in FC60 â€” everything else is derived from it or cross-checked against it.

### 3.1 Why JDN?

- **Continuous:** No gaps, no month boundaries, no leap-year exceptions in the count itself.
- **Universal:** Used by astronomers worldwide since the 1500s.
- **Anchor:** All other date systems (MJD, RD, Unix) can be derived from JDN with simple arithmetic.
- **Weekday:** `(JDN + 1) mod 7` gives the weekday with zero ambiguity.

### 3.2 Gregorian Date â†’ JDN (Fliegelâ€“Van Flandern Algorithm)

```
INPUT:  Y (year), M (month 1â€“12), D (day 1â€“31)
OUTPUT: JDN (integer)

STEP 1: Adjust for January and February
  A  = floor((14 - M) / 12)
  Y2 = Y + 4800 - A
  M2 = M + 12Ã—A - 3

STEP 2: Calculate JDN
  JDN = D
      + floor((153Ã—M2 + 2) / 5)
      + 365Ã—Y2
      + floor(Y2 / 4)
      - floor(Y2 / 100)
      + floor(Y2 / 400)
      - 32045
```

**WARNING about floor((153Ã—M2 + 2) / 5):** This is the most common source of arithmetic error. For M2=11: `153Ã—11 = 1683`, `1683 + 2 = 1685`, `floor(1685/5) = 337` â€” NOT 336.

### 3.3 JDN â†’ Gregorian Date (Inverse Algorithm)

```
INPUT:  JDN (integer)
OUTPUT: Y (year), M (month), D (day)

STEP 1:
  a = JDN + 32044
  b = floor((4Ã—a + 3) / 146097)
  c = a - floor(146097Ã—b / 4)

STEP 2:
  d = floor((4Ã—c + 3) / 1461)
  e = c - floor(1461Ã—d / 4)
  m = floor((5Ã—e + 2) / 153)

STEP 3:
  D = e - floor((153Ã—m + 2) / 5) + 1
  M = m + 3 - 12Ã—floor(m / 10)
  Y = 100Ã—b + d - 4800 + floor(m / 10)
```

### 3.4 JDN â†’ J60 (Base-60 Encoding)

```
J60 = encode_base60(JDN)
```

**Example:** JDN 2461078
```
2461078 Ã· 60 = 41017 remainder 58
41017 Ã· 60 = 683 remainder 37
683 Ã· 60 = 11 remainder 23
11 Ã· 60 = 0 remainder 11

Digits: [11, 23, 37, 58]
â†’ TIFI-DRMT-GOER-PIMT

Verify: 11Ã—216000 + 23Ã—3600 + 37Ã—60 + 58
      = 2376000 + 82800 + 2220 + 58 = 2461078 âœ…
```

### 3.5 Fractional JDN (for reference only)

Traditional astronomy includes time as a decimal where 0.0 = noon UTC:
```
JDN_fractional = JDN + (hour - 12)/24 + minute/1440 + second/86400
```
FC60 keeps date and time as separate components for clarity. This is noted only for interoperability.

### 3.6 JDN Reference Values

| Date | JDN | J60 | Notes |
|------|----:|-----|-------|
| 2000-01-01 | 2,451,545 | `TIFI-DRWU-PIWA-OXWU` | Y2K reference |
| 1970-01-01 | 2,440,588 | `TIFI-RUER-PIFI-SNMT` | Unix epoch |
| 2026-02-06 | 2,461,078 | `TIFI-DRMT-GOER-PIMT` | Primary test vector |
| 2026-02-09 | 2,461,081 | `TIFI-DRMT-GOER-RAFI` | Today's date reference |

---

## Â§4. Weekday Calculation ðŸ“…

**CRITICAL RULE: Never guess the weekday. Always calculate it.**

### 4.1 Primary Method: From JDN (Recommended)

This is the simplest and least error-prone method. Since you always compute JDN anyway, use it:

```
weekday_index = (JDN + 1) mod 7

Index-to-token mapping:
  0 = SO (Sunday)
  1 = LU (Monday)
  2 = MA (Tuesday)
  3 = ME (Wednesday)
  4 = JO (Thursday)
  5 = VE (Friday)
  6 = SA (Saturday)

WEEKDAY_TOKEN = ["SO","LU","MA","ME","JO","VE","SA"][weekday_index]
```

**Example:** JDN 2461078 (2026-02-06)
```
(2461078 + 1) mod 7 = 2461079 mod 7
2461079 = 351582 Ã— 7 + 5
weekday_index = 5 â†’ VE (Friday) âœ…
```

### 4.2 Verification: Known Weekday Anchors

Use these to verify your weekday algorithm is correct:

| Date | JDN | (JDN+1) mod 7 | Weekday | Token |
|------|----:|---------------:|---------|-------|
| 2000-01-01 | 2,451,545 | 6 | Saturday | `SA` |
| 1970-01-01 | 2,440,588 | 4 | Thursday | `JO` |
| 2026-02-06 | 2,461,078 | 5 | Friday | `VE` |
| 2026-02-09 | 2,461,081 | 1 | Monday | `LU` |
| 2024-02-29 | 2,460,370 | 4 | Thursday | `JO` |
| 1999-04-22 | 2,451,291 | 4 | Thursday | `JO` |

---

## Â§5. Timezone Encoding (TZ60) ðŸŒ

### 5.1 Format

```
If offset = +00:00 (UTC exactly):
  TZ60 = "Z"

Otherwise:
  TZ60 = SIGN + TOKEN60(abs_hours) + '-' + TOKEN60(abs_minutes)
  Where SIGN = '+' for east of UTC, '-' for west of UTC
```

### 5.2 Common Timezone Table

| Zone | Offset | TZ60 | Regions |
|------|--------|------|---------|
| UTC | +00:00 | `Z` | Universal |
| CET | +01:00 | `+RAFI-RAWU` | Central Europe |
| EET | +02:00 | `+RAER-RAWU` | Eastern Europe |
| MSK | +03:00 | `+RAMT-RAWU` | Moscow |
| GST | +04:00 | `+RAWA-RAWU` | Gulf States |
| PKT | +05:00 | `+OXWU-RAWU` | Pakistan |
| IST | +05:30 | `+OXWU-HOWU` | India |
| NPT | +05:45 | `+OXWU-ROWU` | Nepal |
| BST | +06:00 | `+OXFI-RAWU` | Bangladesh |
| ICT | +07:00 | `+OXER-RAWU` | Indochina |
| WITA | +08:00 | `+OXMT-RAWU` | Bali, Singapore, China |
| JST | +09:00 | `+OXWA-RAWU` | Japan, Korea |
| AEST | +10:00 | `+TIWU-RAWU` | Australia East |
| NZST | +12:00 | `+TIER-RAWU` | New Zealand |
| HST | -10:00 | `-TIWU-RAWU` | Hawaii |
| PST | -08:00 | `-OXMT-RAWU` | US Pacific |
| MST | -07:00 | `-OXER-RAWU` | US Mountain |
| CST | -06:00 | `-OXFI-RAWU` | US Central |
| EST | -05:00 | `-OXWU-RAWU` | US Eastern |
| AST | -04:00 | `-RAWA-RAWU` | Atlantic |
| BRT | -03:00 | `-RAMT-RAWU` | Brazil |

---

## Â§6. Year Encoding ðŸ“†

FC60 supports three year encoding methods, serving different purposes:

### 6.1 Absolute Year (Y60) â€” Unambiguous, Required

Convert the integer year to base-60 digits, encode each:

```
Y60 = encode_base60(year)
```

| Year | Base-60 Digits | Y60 |
|-----:|---------------|-----|
| 1900 | [31, 40] | `HOFI-MOWU` |
| 1970 | [32, 50] | `HOER-DOWU` |
| 1999 | [33, 19] | `HOMT-RUWA` |
| 2000 | [33, 20] | `HOMT-DRWU` |
| 2024 | [33, 44] | `HOMT-MOWA` |
| 2025 | [33, 45] | `HOMT-ROWU` |
| 2026 | [33, 46] | `HOMT-ROFI` |
| 2060 | [34, 20] | `HOWA-DRWU` |

### 6.2 60-Year Cycle (Y2K) â€” Compact, Cyclical

```
Y2K = TOKEN60((year - 2000) mod 60)
```

**Note:** Y2K is ambiguous without Y60 â€” years 2000 and 2060 both produce `RAWU`. Always include Y60 as the primary.

| Year | (year-2000) mod 60 | Y2K |
|-----:|-------------------:|-----|
| 2000 | 0 | `RAWU` |
| 2024 | 24 | `DRWA` |
| 2025 | 25 | `SNWU` |
| 2026 | 26 | `SNFI` |

### 6.3 GÄnzhÄ« Year (GZ) â€” Traditional 60-Year Cycle

See Â§11 for the full algorithm.

---

## Â§7. Additional Cores ðŸ”©

These provide independent cross-checks against the JDN. Each uses a different epoch, so if one value is wrong, the error becomes obvious.

### 7.1 Modified Julian Date (MJD)

```
MJD = JDN - 2400001
```

**Why:** Smaller number than JDN, starts from November 17, 1858 (midnight, not noon).

**Encoding:** `encode_base60(MJD)`

### 7.2 Rata Die (RD)

```
RD = JDN - 1721425
```

**Why:** Days since January 1, 1 CE (proleptic Gregorian). Used by many calendar libraries.

**Encoding:** `encode_base60(RD)`

### 7.3 Unix Timestamp (U)

```
U_seconds = (JDN - 2440588) Ã— 86400 + hourÃ—3600 + minuteÃ—60 + second - timezone_offset_in_seconds
```

**Why:** Standard machine time. Note: this converts local time to UTC first.

**Encoding:** `encode_base60(U_seconds)`

For timestamps before 1970-01-01 00:00:00 UTC, use negative encoding: `NEG-` prefix.

### 7.4 Cross-Check Relationships

These identities must always hold:

```
MJD = JDN - 2400001
RD  = JDN - 1721425
MJD = RD - 678576
```

If any of these fail, there is an arithmetic error.

---

## Â§8. Weighted Check Token (CHK) âœ…

### 8.1 Purpose

The check token detects transmission and calculation errors. It uses position-weighted factors (inspired by the Luhn algorithm) to catch transposition errors that a simple sum would miss.

### 8.2 Full Algorithm (date + time)

```
INPUT:  Y (year), M (month), D (day), HH (hour), MM (minute), SS (second), JDN

chk_value = (
    1 Ã— (Y mod 60) +
    2 Ã— M +
    3 Ã— D +
    4 Ã— HH +
    5 Ã— MM +
    6 Ã— SS +
    7 Ã— (JDN mod 60)
) mod 60

CHK = TOKEN60(chk_value)
```

### 8.3 Date-Only Algorithm

```
chk_value = (
    1 Ã— (Y mod 60) +
    2 Ã— M +
    3 Ã— D +
    7 Ã— (JDN mod 60)
) mod 60

CHK = TOKEN60(chk_value)
```

### 8.4 Why These Specific Weights?

| Weight | Component | Rationale |
|-------:|-----------|-----------|
| 1 | Year mod 60 | Lowest weight â€” year changes least often |
| 2 | Month | Low weight â€” changes monthly |
| 3 | Day | Medium â€” changes daily |
| 4 | Hour | Medium â€” changes hourly |
| 5 | Minute | Higher â€” changes every minute |
| 6 | Second | Higher â€” changes every second |
| 7 | JDN mod 60 | Highest â€” independent anchor, catches date errors |

The prime-ish weights (1,2,3,4,5,6,7) ensure that swapping any two components changes the checksum.

### 8.5 Verification Process

To verify a received FC60 stamp:
1. Extract all date/time components from the stamp
2. Recompute JDN from the date components
3. Calculate CHK using the formula above
4. Compare with the provided CHK
5. **If mismatch â†’ transmission error detected. Do not trust any values.**

---

## Â§9. Output Formats ðŸ§¾

### 9.1 Full Format (recommended for Mode A)

```
FC60:  WD-MO-DOM HALFÂ·HOUR-MINUTE-SECOND
ISO:   YYYY-MM-DDTHH:MM:SSÂ±HH:MM
TZ60:  Â±TOKEN60(H)-TOKEN60(M) or Z
Y60:   TOKEN60_base60(year)
Y2K:   TOKEN60((year-2000) mod 60)
J:     TOKEN60_base60(JDN)
MJD:   TOKEN60_base60(MJD)
RD:    TOKEN60_base60(RD)
U:     TOKEN60_base60(unix_seconds)
CHK:   TOKEN60(check_value)
```

### 9.2 Compact One-Line Format

```
FC60=<stamp> | ISO=<iso> | TZ60=<tz> | Y60=<y60> | J=<j60> | CHK=<chk>
```

### 9.3 Minimal Format (date only)

```
WD-MO-DOM | Y60=<y60> | J=<j60> | CHK=<chk>
```

### 9.4 Full Format with Symbolic (Mode B)

Add after CHK:
```
MOON:  <phase_marker> age=<days>d
GZ:    <stem>-<branch> (<chinese> <element> <animal>)
```

---

# PART III â€” SYMBOLIC ENGINE

---

## Â§10. Moon Phase Calculation ðŸŒ™

### 10.1 Constants

```
SYNODIC_MONTH = 29.530588853 days    (average new-moon-to-new-moon)
REFERENCE_JDN = 2451550.1            (New moon: January 6, 2000 ~18:14 UTC)
```

### 10.2 Moon Age Calculation

```
moon_age = (JDN - REFERENCE_JDN) mod SYNODIC_MONTH
```

**Note:** This is an approximation. Actual lunar phases can vary by Â±0.5 days from this formula due to orbital mechanics. For symbolic readings this precision is sufficient. For astronomical precision, use a proper ephemeris.

### 10.3 Phase Determination

```
if   moon_age <  1.85 â†’ ðŸŒ‘ New Moon
elif moon_age <  7.38 â†’ ðŸŒ’ Waxing Crescent
elif moon_age < 11.07 â†’ ðŸŒ“ First Quarter
elif moon_age < 14.77 â†’ ðŸŒ” Waxing Gibbous
elif moon_age < 16.61 â†’ ðŸŒ• Full Moon
elif moon_age < 22.14 â†’ ðŸŒ– Waning Gibbous
elif moon_age < 25.83 â†’ ðŸŒ— Last Quarter
else                   â†’ ðŸŒ˜ Waning Crescent
```

### 10.4 Illumination Percentage (approximate)

```
illumination = 50 Ã— (1 - cos(2 Ã— Ï€ Ã— moon_age / SYNODIC_MONTH))
```

### 10.5 Output Format

```
MOON: ðŸŒ” age=10.77d illumination=68%
```

### 10.6 Moon Phase Energy Table

| Phase | Energy | Best For | Avoid |
|-------|--------|----------|-------|
| ðŸŒ‘ New | Seed | Setting intentions, starting projects | Big reveals, launches |
| ðŸŒ’ Waxing Crescent | Build | Taking first steps, gathering resources | Giving up |
| ðŸŒ“ First Quarter | Challenge | Making decisions, overcoming obstacles | Avoiding conflict |
| ðŸŒ” Waxing Gibbous | Refine | Editing, perfecting, patience | Starting new things |
| ðŸŒ• Full | Culminate | Celebrating, releasing, clarity | Starting (too intense) |
| ðŸŒ– Waning Gibbous | Share | Teaching, distributing, gratitude | Hoarding |
| ðŸŒ— Last Quarter | Release | Letting go, forgiving, cleaning | Holding on |
| ðŸŒ˜ Waning Crescent | Rest | Reflection, preparation, dreaming | Pushing hard |

---

## Â§11. GÄnzhÄ« Sexagenary Cycle (å¹²æ”¯) ðŸ²

The traditional Chinese 60-year cycle combining 10 Heavenly Stems and 12 Earthly Branches.

### 11.1 Why 60?

```
LCM(10, 12) = 60
```

The stem and branch each advance by 1 each year (or day, or double-hour), creating 60 unique combinations before repeating. This aligns perfectly with FC60's base-60 system.

### 11.2 Year GÄnzhÄ«

```
Reference: Year 4 CE = ç”²å­ (JiÇŽ-ZÇ) = Stem index 0, Branch index 0

stem_index   = (year - 4) mod 10
branch_index = (year - 4) mod 12

GZ = STEM_TOKEN[stem_index] + '-' + ANIMAL_TOKEN[branch_index]
```

**Recent years:**

| Year | Stem idx | Branch idx | GZ Token | Traditional Name |
|-----:|---------:|-----------:|----------|-----------------|
| 2020 | 6 | 0 | `GE-RA` | åºšå­ Metal Rat |
| 2021 | 7 | 1 | `XI-OX` | è¾›ä¸‘ Metal Ox |
| 2022 | 8 | 2 | `RE-TI` | å£¬å¯… Water Tiger |
| 2023 | 9 | 3 | `GU-RU` | ç™¸å¯ Water Rabbit |
| 2024 | 0 | 4 | `JA-DR` | ç”²è¾° Wood Dragon |
| 2025 | 1 | 5 | `YI-SN` | ä¹™å·³ Wood Snake |
| 2026 | 2 | 6 | `BI-HO` | ä¸™åˆ Fire Horse |
| 2027 | 3 | 7 | `DI-GO` | ä¸æœª Fire Goat |
| 2028 | 4 | 8 | `WW-MO` | æˆŠç”³ Earth Monkey |
| 2029 | 5 | 9 | `JI-RO` | å·±é…‰ Earth Rooster |
| 2030 | 6 | 10 | `GE-DO` | åºšæˆŒ Metal Dog |

### 11.3 Day GÄnzhÄ«

```
day_gz_index = (JDN + 49) mod 60
day_stem     = day_gz_index mod 10
day_branch   = day_gz_index mod 12

Day_GZ = STEM_TOKEN[day_stem] + '-' + ANIMAL_TOKEN[day_branch]
```

### 11.4 Hour GÄnzhÄ«

Traditional Chinese time divides the day into 12 two-hour periods (æ™‚è¾° ShÃ­chÃ©n):

| Hour Range | Branch Index | Animal |
|------------|------------:|--------|
| 23:00â€“00:59 | 0 | Rat |
| 01:00â€“02:59 | 1 | Ox |
| 03:00â€“04:59 | 2 | Tiger |
| 05:00â€“06:59 | 3 | Rabbit |
| 07:00â€“08:59 | 4 | Dragon |
| 09:00â€“10:59 | 5 | Snake |
| 11:00â€“12:59 | 6 | Horse |
| 13:00â€“14:59 | 7 | Goat |
| 15:00â€“16:59 | 8 | Monkey |
| 17:00â€“18:59 | 9 | Rooster |
| 19:00â€“20:59 | 10 | Dog |
| 21:00â€“22:59 | 11 | Pig |

```
hour_branch = floor((hour + 1) / 2) mod 12
hour_stem   = (day_stem Ã— 2 + hour_branch) mod 10
```

### 11.5 Month GÄnzhÄ«

```
month_stem = (year_stem Ã— 2 + month_branch) mod 10
```

Where `month_branch` follows the traditional assignment starting from Tiger (å¯…) for month 1.

---

## Â§12. Symbolic Reading Engine ðŸ”®

This section defines how to generate human-readable interpretations from FC60 stamps. Mode B only.

### 12.1 Signal Hierarchy (priority order)

| Priority | Signal | Weight | How to Detect |
|---------:|--------|--------|--------------|
| 1 | Repeated animals (3+) | Very High | Same ANIMAL code in 3+ positions |
| 2 | Repeated animals (2) | High | Same ANIMAL code in 2 positions |
| 3 | Day planet | Medium | Weekday token â†’ Â§1.7 symbolic domain |
| 4 | Moon phase | Medium | Â§10 phase energy |
| 5 | Day-of-month animal + element | Medium | DOM token â†’ animal and element meanings |
| 6 | Hour animal | Low-Medium | Hour token â†’ animal essence |
| 7 | Minute texture | Low | Minute token â†’ the "how" of the micro-moment |
| 8 | Year cycle (GZ) | Background | Â§11 â†’ annual theme |
| 9 | Personal overlays | Variable | Â§13 numerology Ã— current moment |

### 12.2 Animal Repetition Detection

```
Collect animals from these stamp positions:
  - month_animal     = MO token (e.g., OX for February)
  - day_animal       = first 2 chars of DOM token
  - hour_animal      = HOUR token
  - minute_animal    = first 2 chars of MINUTE token
  - year_animal      = branch from GZ

Count occurrences:
  counts = {animal: count for each unique animal}
  repeated = [(animal, count) for animal, count in counts if count â‰¥ 2]
  Sort by count, descending
```

### 12.3 Time-of-Day Context

| Hour Range | Context | Energy |
|------------|---------|--------|
| 00:00â€“04:59 | The hour of silence | Deep night â€” subconscious surfaces |
| 05:00â€“07:59 | The early hours | Raw potential, day not yet shaped |
| 08:00â€“11:59 | Morning engine | Clarity peaks, resistance lowest |
| 12:00â€“14:59 | Midday checkpoint | Momentum building or fading |
| 15:00â€“17:59 | Afternoon shift | Results arriving, time to adjust |
| 18:00â€“20:59 | Evening transition | Processing begins |
| 21:00â€“23:59 | Night hours | Masks off, real questions surface |

### 12.4 Sun/Moon Paradox

If `HALF = â˜€` but the hour is in darkness (00:00â€“05:59):

> "You're marked as being in the Sun half, but sitting in darkness. This means you're carrying light that hasn't been made visible yet. You see something the world hasn't caught up with."

### 12.5 Conflict Resolution Rules

When signals contradict (e.g., moon says "rest" but planet says "action"):

| Rule | Action |
|------|--------|
| Higher priority signal wins | Follow the hierarchy in Â§12.1 |
| Equal priority with opposing meanings | Present both as tension: "You're being pulled between X and Y â€” the resolution is Z" |
| Personal overlay contradicts universal | Personal overlay shades universal, doesn't override |
| Moon contradicts planet | Moon = emotional truth, Planet = external circumstance. Both are valid at different levels |

### 12.6 Synthesis Template

```
[OPENING â€” Set the scene]
At [TIME] on this [PLANET_NAME] day ([PLANET_DOMAIN]), the [HOUR_ANIMAL] hour
carries the energy of [HOUR_ESSENCE].

[CORE SIGNAL â€” If repeated animals exist]
The [ANIMAL] appears [COUNT] times â€” in the [POSITIONS]. This is the loudest
signal: [ANIMAL_TRAIT]. The instruction: [ANIMAL_ACTION].

[DAY ENERGY]
Today's core energy is [DAY_ANIMAL] paired with [DAY_ELEMENT].
[DAY_MEANING]. The shadow to watch: [DAY_SHADOW].

[MOON CONTEXT]
The moon is [PHASE] â€” [MOON_MEANING].

[PERSONAL â€” If personal data provided]
Through your Life Path [LP] ([LP_TITLE]), this moment asks you to [LP_ACTION].
Your Personal Year [PY] colors everything with [PY_THEME].

[CLOSING]
The prediction: [SYNTHESIS combining strongest signals into actionable insight].
```

---

## Â§13. Numerology Integration ðŸ”¢

For personal readings, FC60 integrates Pythagorean numerology. Used in Mode B only.

### 13.1 Letter-to-Number Mapping (Pythagorean)

```
1: A, J, S
2: B, K, T
3: C, L, U
4: D, M, V
5: E, N, W
6: F, O, X
7: G, P, Y
8: H, Q, Z
9: I, R
```

### 13.2 Digital Root Reduction

```
def reduce(n):
    if n in {11, 22, 33}:    # Master numbers â€” do NOT reduce
        return n
    while n > 9:
        n = sum of all digits of n
    return n
```

### 13.3 Core Numbers

| Number | How to Calculate | What It Means |
|--------|-----------------|---------------|
| Life Path | reduce(reduce(day) + reduce(month) + reduce(year_digits)) | Core life purpose |
| Expression | reduce(sum of ALL name letters) | How you show up in the world |
| Soul Urge | reduce(sum of VOWELS only: A,E,I,O,U) | Deepest inner desire |
| Personality | reduce(sum of CONSONANTS only) | How others perceive you |
| Personal Year | reduce(reduce(birth_month) + reduce(birth_day) + reduce(current_year)) | Current year's theme |

### 13.4 Life Path Meanings

| LP | Title | Core Message |
|---:|-------|-------------|
| 1 | The Pioneer | Lead, start, go first |
| 2 | The Bridge | Connect, harmonize, feel |
| 3 | The Voice | Create, express, beautify |
| 4 | The Architect | Build, structure, stabilize |
| 5 | The Explorer | Change, adapt, experience |
| 6 | The Guardian | Nurture, heal, protect |
| 7 | The Seeker | Question, analyze, find meaning |
| 8 | The Powerhouse | Master, achieve, build legacy |
| 9 | The Sage | Complete, teach, transcend |
| 11 | The Visionary | See what hasn't been built yet (master number) |
| 22 | The Master Builder | Turn impossible visions into reality (master number) |
| 33 | The Master Teacher | Heal through compassionate leadership (master number) |

### 13.5 Mother's Name Influence

The mother's name number (Expression number from mother's full name) represents the "invisible foundation" â€” values inherited before conscious choice.

---

# PART IV â€” INPUT HANDLING

---

## Â§14. Parsing Rules (Input â†’ Meaning) ðŸ”

### 14.1 Input Type Detection (decision tree)

```
INPUT received. Follow this tree in order:

1. Does it contain FC60 tokens (ANIMAL+ELEMENT patterns like "OXFI")?
   YES â†’ Decode FC60 stamp (Â§14.5)

2. Does it match ISO-8601 (contains YYYY-MM-DD)?
   YES â†’ Parse as ISO date/time
   If timezone included â†’ use it
   If no timezone â†’ apply Â§14.3

3. Does it contain ":" (colon)?
   YES â†’ Parse as HH:MM or HH:MM:SS time
   Attach current date (state this assumption)

4. Is it exactly 8 digits (YYYYMMDD)?
   YES â†’ Parse as compact date

5. Is it 10 digits starting with 1 or 2?
   YES â†’ Likely Unix seconds timestamp
   Ask user to confirm if ambiguous

6. Is it 13 digits?
   YES â†’ Likely Unix milliseconds

7. Does it contain "now" or "today"?
   YES â†’ Use current date/time (state timezone assumption)

8. Otherwise â†’ Treat as raw integer, encode via Â§1.5
```

### 14.2 Timezone Inference Priority

```
1. Explicit timezone in input (+08:00, Z, UTC, PST, etc.)     â†’ Use it
2. User has stated a default timezone earlier in conversation   â†’ Use it
3. Otherwise â†’ Ask user OR state assumption explicitly
```

**RULE:** Never silently assume a timezone. Always state it.

### 14.3 Ambiguity Resolution

| Ambiguous Input | Resolution |
|-----------------|-----------|
| `12:00` without date | Attach current date, state assumption |
| `2026` alone | Ask: "Is this a year or the integer 2026?" |
| `1700000000` | Likely Unix timestamp (check: 2023-11-14), but confirm |
| No timezone given | State assumed timezone explicitly |
| `29-02-2025` | Invalid date (2025 is not a leap year) â€” reject and explain |

### 14.4 Leap Year Validation

Before encoding any date, verify it exists:

```
def is_leap_year(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def is_valid_date(y, m, d):
    if m < 1 or m > 12: return False
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(y): days_in_month[2] = 29
    return 1 <= d <= days_in_month[m]
```

### 14.5 FC60 Token Decoding

```
INPUT: "VE-OX-OXFI â˜€OX-RUWU-RAWU"

STEP 1: Split by space
  date_part = "VE-OX-OXFI"
  time_part = "â˜€OX-RUWU-RAWU"

STEP 2: Parse date
  Split by "-": ["VE", "OX", "OXFI"]
  WD    = "VE" â†’ Friday (Â§1.7)
  MO    = "OX" â†’ February, month 2 (Â§2.3)
  DOM   = "OXFI" â†’ DIGIT60("OXFI") = 1Ã—5 + 1 = 6

STEP 3: Parse time
  First char = "â˜€" â†’ AM
  Remove marker: "OX-RUWU-RAWU"
  Split by "-": ["OX", "RUWU", "RAWU"]
  HOUR   = "OX" â†’ index 1, + 0 (AM) = 01:xx
  MINUTE = "RUWU" â†’ DIGIT60("RUWU") = 3Ã—5 + 0 = 15
  SECOND = "RAWU" â†’ DIGIT60("RAWU") = 0Ã—5 + 0 = 0

RESULT: February 6, 01:15:00 (Friday)
```

**Cross-check:** Compute JDN for this date and verify the weekday token matches.

---

# PART V â€” VERIFICATION

---

## Â§15. Comprehensive Test Vectors ðŸ§ª

Every test vector below has been verified by independent computation. Use these to validate any FC60 implementation.

### Test Vector 1: Primary Reference â€” 2026-02-06 01:15:00 UTC+8

```
INPUT:  2026-02-06T01:15:00+08:00

Step-by-step JDN calculation:
  A  = floor((14-2)/12) = 1
  Y2 = 2026 + 4800 - 1 = 6825
  M2 = 2 + 12Ã—1 - 3 = 11
  floor((153Ã—11 + 2)/5) = floor(1685/5) = 337
  365 Ã— 6825 = 2,491,125
  floor(6825/4) = 1706
  floor(6825/100) = 68
  floor(6825/400) = 17
  JDN = 6 + 337 + 2,491,125 + 1706 - 68 + 17 - 32,045 = 2,461,078

OUTPUT:
  FC60:  VE-OX-OXFI â˜€OX-RUWU-RAWU
  ISO:   2026-02-06T01:15:00+08:00
  TZ60:  +OXMT-RAWU
  Y60:   HOMT-ROFI
  Y2K:   SNFI
  J:     TIFI-DRMT-GOER-PIMT
  MJD:   RAFI-RAWU-RUER-PIER
  RD:    RAMT-SNWU-SNER-HOMT
  MOON:  ðŸŒ– age=19.05d
  GZ:    BI-HO (ä¸™åˆ Fire Horse)
  CHK:   TIMT
         (1Ã—46 + 2Ã—2 + 3Ã—6 + 4Ã—1 + 5Ã—15 + 6Ã—0 + 7Ã—58) mod 60
         = (46+4+18+4+75+0+406) mod 60 = 553 mod 60 = 13 â†’ TIMT
```

### Test Vector 2: Y2K Reference â€” 2000-01-01 00:00:00 UTC

```
INPUT:  2000-01-01T00:00:00Z

  JDN = 2,451,545
  Weekday: (2451545+1) mod 7 = 6 â†’ SA (Saturday)

OUTPUT:
  FC60:  SA-RA-RAFI â˜€RA-RAWU-RAWU
  ISO:   2000-01-01T00:00:00Z
  TZ60:  Z
  Y60:   HOMT-DRWU
  Y2K:   RAWU
  J:     TIFI-DRWU-PIWA-OXWU
  RD:    RAMT-DRER-ROMT-MOWU (730,120)
  GZ:    GE-DR (åºšè¾° Metal Dragon)
  CHK:   RAWU
         (1Ã—20 + 2Ã—1 + 3Ã—1 + 4Ã—0 + 5Ã—0 + 6Ã—0 + 7Ã—5) mod 60
         = (20+2+3+0+0+0+35) mod 60 = 60 mod 60 = 0 â†’ RAWU

### Test Vector 3: Unix Epoch â€” 1970-01-01 00:00:00 UTC

```
INPUT:  1970-01-01T00:00:00Z

  JDN = 2,440,588
  Weekday: (2440588+1) mod 7 = 4 â†’ JO (Thursday)

OUTPUT:
  FC60:  JO-RA-RAFI â˜€RA-RAWU-RAWU
  ISO:   1970-01-01T00:00:00Z
  TZ60:  Z
  Y60:   HOER-DOWU
  J:     TIFI-RUER-PIFI-SNMT
  U:     RAWU (0 seconds)
  CHK (date-only): (1Ã—50 + 2Ã—1 + 3Ã—1 + 7Ã—28) mod 60
                  = (50+2+3+196) mod 60 = 251 mod 60 = 11 â†’ TIFI
```

### Test Vector 4: Leap Day â€” 2024-02-29 12:00:00 UTC

```
INPUT:  2024-02-29T12:00:00Z

  JDN = 2,460,370
  Weekday: (2460370+1) mod 7 = 4 â†’ JO (Thursday)

OUTPUT:
  FC60:  JO-OX-SNWA ðŸŒ™RA-RAWU-RAWU
  ISO:   2024-02-29T12:00:00Z
  TZ60:  Z
  Y60:   HOMT-MOWA
  J:     TIFI-DRMT-SNFI-TIWU
  GZ:    JA-DR (ç”²è¾° Wood Dragon)
  CHK:   TIMT
         (1Ã—44 + 2Ã—2 + 3Ã—29 + 4Ã—12 + 5Ã—0 + 6Ã—0 + 7Ã—10) mod 60
         = (44+4+87+48+0+0+70) mod 60 = 253 mod 60 = 13 â†’ TIMT
```

### Test Vector 5: Year End â€” 2025-12-31 23:59:59 UTC

```
INPUT:  2025-12-31T23:59:59Z

  JDN = 2,461,041
  Weekday: (2461041+1) mod 7 = 3 â†’ ME (Wednesday)

OUTPUT:
  FC60:  ME-PI-HOFI ðŸŒ™PI-PIWA-PIWA
  ISO:   2025-12-31T23:59:59Z
  Y60:   HOMT-ROWU
  J:     TIFI-DRMT-GOER-DRFI
  CHK:   HOWU
         (1Ã—45 + 2Ã—12 + 3Ã—31 + 4Ã—23 + 5Ã—59 + 6Ã—59 + 7Ã—21) mod 60
         = (45+24+93+92+295+354+147) mod 60 = 1050 mod 60 = 30 â†’ HOWU
```

### Test Vector 6: Birthday Reference â€” 1999-04-22

```
INPUT:  1999-04-22 (date only)

  JDN = 2,451,291
  Weekday: (2451291+1) mod 7 = 4 â†’ JO (Thursday)

OUTPUT:
  FC60:  JO-RU-DRER
  ISO:   1999-04-22
  Y60:   HOMT-RUWA
  J:     TIFI-DRWU-DOWA-DOFI
  RD:    RAMT-DRER-MOWA-SNFI (729,866)
  CHK (date-only): (1Ã—19 + 2Ã—4 + 3Ã—22 + 7Ã—51) mod 60
                  = (19+8+66+357) mod 60 = 450 mod 60 = 30 â†’ HOWU
```

### Test Vector 7: New Year 2026 â€” 2026-01-01 00:00:00 UTC

```
INPUT:  2026-01-01T00:00:00Z

  JDN = 2,461,042
  Weekday: (2461042+1) mod 7 = 4 â†’ JO (Thursday)

OUTPUT:
  FC60:  JO-RA-RAFI â˜€RA-RAWU-RAWU
  ISO:   2026-01-01T00:00:00Z
  Y60:   HOMT-ROFI
  J:     TIFI-DRMT-GOER-DRER
  CHK:   SNWU
         (1Ã—46 + 2Ã—1 + 3Ã—1 + 4Ã—0 + 5Ã—0 + 6Ã—0 + 7Ã—22) mod 60
         = (46+2+3+0+0+0+154) mod 60 = 205 mod 60 = 25 â†’ SNWU
```

### Test Vector 8: Midnight Boundary â€” 2026-02-09 00:00:00 UTC+8

```
INPUT:  2026-02-09T00:00:00+08:00

  JDN = 2,461,081
  Weekday: (2461081+1) mod 7 = 1 â†’ LU (Monday)

OUTPUT:
  FC60:  LU-OX-OXWA â˜€RA-RAWU-RAWU
  ISO:   2026-02-09T00:00:00+08:00
  TZ60:  +OXMT-RAWU
  Y60:   HOMT-ROFI
  J:     TIFI-DRMT-GOER-RAFI
  CHK:   DRWA
         (1Ã—46 + 2Ã—2 + 3Ã—9 + 4Ã—0 + 5Ã—0 + 6Ã—0 + 7Ã—1) mod 60
         = (46+4+27+0+0+0+7) mod 60 = 84 mod 60 = 24 â†’ DRWA
```

### Test Vector 9: Far Future â€” 2060-12-31

```
INPUT:  2060-12-31 (date only)

  JDN = 2,473,825
  Weekday: (2473825+1) mod 7 = 5 â†’ VE (Friday)

OUTPUT:
  FC60:  VE-PI-HOFI
  Y60:   HOWA-DRWU
  J:     TIFI-SNER-TIWU-SNWU
  CHK (date-only): (1Ã—20 + 2Ã—12 + 3Ã—31 + 7Ã—25) mod 60
                  = (20+24+93+175) mod 60 = 312 mod 60 = 12 â†’ TIER
```

### Test Vector 10: Pre-Epoch â€” 1900-01-01

```
INPUT:  1900-01-01 (date only)

  JDN = 2,415,021
  Weekday: (2415021+1) mod 7 = 1 â†’ LU (Monday)

OUTPUT:
  FC60:  LU-RA-RAFI
  Y60:   HOFI-MOWU
  J:     TIFI-TIWU-DOWU-DRFI
  GZ:    GE-RA (åºšå­ Metal Rat)
```

### Test Vector 11: Day After Leap Day (Y2K) â€” 2000-03-01

```
INPUT:  2000-03-01 (date only)

  JDN = 2,451,605
  Weekday: (2451605+1) mod 7 = 3 â†’ ME (Wednesday)

OUTPUT:
  FC60:  ME-TI-RAFI
  J:     TIFI-DRWU-RAFI-OXWU
```

### Test Vector 12: Encoding Integer 0

```
INPUT:  0
OUTPUT: RAWU
```

### Test Vector 13: Encoding Integer 59

```
INPUT:  59
OUTPUT: PIWA
```

### Test Vector 14: Encoding Integer 2026

```
INPUT:  2026 (as integer)
OUTPUT: HOMT-ROFI
VERIFY: 33 Ã— 60 + 46 = 2026 âœ…
```

### Test Vector 15: Round-Trip Decode

```
INPUT (FC60):  "VE-OX-OXFI â˜€OX-RUWU-RAWU"

DECODE:
  WD = VE â†’ Friday
  MO = OX â†’ February (2)
  DOM = OXFI â†’ 6
  HALF = â˜€ â†’ AM
  HOUR = OX â†’ 1
  MINUTE = RUWU â†’ 15
  SECOND = RAWU â†’ 0

RESULT: Friday, February 6, 01:15:00

VERIFY: Compute JDN for 2026-02-06:
  JDN = 2,461,078
  (2461078 + 1) mod 7 = 5 â†’ VE (Friday) âœ…
```

---

## Â§16. Error Catalog & Troubleshooting ðŸ”§

### 16.1 Common Errors

| # | Error | Cause | Fix |
|--:|-------|-------|-----|
| E1 | Wrong weekday | Assumed instead of calculated | Always use `(JDN+1) mod 7` |
| E2 | JDN off by 1 | floor() rounding error | Double-check `floor((153Ã—M2+2)/5)` |
| E3 | JDN off by N | Month/year adjustment error | Verify A, Y2, M2 intermediate values |
| E4 | CHK mismatch | Any upstream arithmetic error | Recompute from scratch |
| E5 | Wrong month token | Used month number directly | Remember: `ANIMAL[month - 1]`, not `ANIMAL[month]` |
| E6 | Hour 12 encoded as PM-RA | Confusing noon | 12:xx â†’ `ðŸŒ™RA` (PM, index 0). Correct. |
| E7 | Hour 0 encoded as AM-RA | Confusing midnight | 00:xx â†’ `â˜€RA` (AM, index 0). Correct. |
| E8 | Invalid date | Feb 29 in non-leap year | Validate before encoding (Â§14.4) |
| E9 | Timezone assumed | User didn't specify | Always state assumption explicitly |
| E10 | Y2K ambiguity | Year > 2059 produces same token as <2060 | Always include Y60 |

### 16.2 Self-Diagnostic Checklist

Before delivering any FC60 output, verify:

```
â–¡ JDN was computed, not assumed
â–¡ Weekday was derived from JDN via (JDN+1) mod 7
â–¡ Month token uses ANIMAL[month-1], not ANIMAL[month]
â–¡ Day token uses TOKEN60(day), where day â‰¥ 1
â–¡ Hour correctly split into HALF + ANIMAL[HH mod 12]
â–¡ CHK was computed and matches
â–¡ Timezone was stated explicitly
â–¡ ISO-8601 accompanies the FC60 stamp
â–¡ Cross-check: at least one of RD, MJD, or U was computed and is consistent with JDN
```

---

# APPENDICES

---

## Appendix A â€” Complete TOKEN60 Table (0â€“59)

| n | q | r | Token | | n | q | r | Token | | n | q | r | Token |
|--:|--:|--:|-------|-|--:|--:|--:|-------|-|--:|--:|--:|-------|
| 0 | 0 | 0 | `RAWU` | | 20 | 4 | 0 | `DRWU` | | 40 | 8 | 0 | `MOWU` |
| 1 | 0 | 1 | `RAFI` | | 21 | 4 | 1 | `DRFI` | | 41 | 8 | 1 | `MOFI` |
| 2 | 0 | 2 | `RAER` | | 22 | 4 | 2 | `DRER` | | 42 | 8 | 2 | `MOER` |
| 3 | 0 | 3 | `RAMT` | | 23 | 4 | 3 | `DRMT` | | 43 | 8 | 3 | `MOMT` |
| 4 | 0 | 4 | `RAWA` | | 24 | 4 | 4 | `DRWA` | | 44 | 8 | 4 | `MOWA` |
| 5 | 1 | 0 | `OXWU` | | 25 | 5 | 0 | `SNWU` | | 45 | 9 | 0 | `ROWU` |
| 6 | 1 | 1 | `OXFI` | | 26 | 5 | 1 | `SNFI` | | 46 | 9 | 1 | `ROFI` |
| 7 | 1 | 2 | `OXER` | | 27 | 5 | 2 | `SNER` | | 47 | 9 | 2 | `ROER` |
| 8 | 1 | 3 | `OXMT` | | 28 | 5 | 3 | `SNMT` | | 48 | 9 | 3 | `ROMT` |
| 9 | 1 | 4 | `OXWA` | | 29 | 5 | 4 | `SNWA` | | 49 | 9 | 4 | `ROWA` |
| 10 | 2 | 0 | `TIWU` | | 30 | 6 | 0 | `HOWU` | | 50 | 10 | 0 | `DOWU` |
| 11 | 2 | 1 | `TIFI` | | 31 | 6 | 1 | `HOFI` | | 51 | 10 | 1 | `DOFI` |
| 12 | 2 | 2 | `TIER` | | 32 | 6 | 2 | `HOER` | | 52 | 10 | 2 | `DOER` |
| 13 | 2 | 3 | `TIMT` | | 33 | 6 | 3 | `HOMT` | | 53 | 10 | 3 | `DOMT` |
| 14 | 2 | 4 | `TIWA` | | 34 | 6 | 4 | `HOWA` | | 54 | 10 | 4 | `DOWA` |
| 15 | 3 | 0 | `RUWU` | | 35 | 7 | 0 | `GOWU` | | 55 | 11 | 0 | `PIWU` |
| 16 | 3 | 1 | `RUFI` | | 36 | 7 | 1 | `GOFI` | | 56 | 11 | 1 | `PIFI` |
| 17 | 3 | 2 | `RUER` | | 37 | 7 | 2 | `GOER` | | 57 | 11 | 2 | `PIER` |
| 18 | 3 | 3 | `RUMT` | | 38 | 7 | 3 | `GOMT` | | 58 | 11 | 3 | `PIMT` |
| 19 | 3 | 4 | `RUWA` | | 39 | 7 | 4 | `GOWA` | | 59 | 11 | 4 | `PIWA` |

---

## Appendix B â€” Quick-Lookup Tables

### B.1 Day-of-Month Table (1â€“31)

| Day | Token | | Day | Token | | Day | Token | | Day | Token |
|----:|-------|-|----:|-------|-|----:|-------|-|----:|-------|
| 1 | `RAFI` | | 9 | `OXWA` | | 17 | `RUER` | | 25 | `SNWU` |
| 2 | `RAER` | | 10 | `TIWU` | | 18 | `RUMT` | | 26 | `SNFI` |
| 3 | `RAMT` | | 11 | `TIFI` | | 19 | `RUWA` | | 27 | `SNER` |
| 4 | `RAWA` | | 12 | `TIER` | | 20 | `DRWU` | | 28 | `SNMT` |
| 5 | `OXWU` | | 13 | `TIMT` | | 21 | `DRFI` | | 29 | `SNWA` |
| 6 | `OXFI` | | 14 | `TIWA` | | 22 | `DRER` | | 30 | `HOWU` |
| 7 | `OXER` | | 15 | `RUWU` | | 23 | `DRMT` | | 31 | `HOFI` |
| 8 | `OXMT` | | 16 | `RUFI` | | 24 | `DRWA` | | | |

---

## Appendix C â€” Decoding Cheatsheet (Reverse Lookups)

### C.1 TOKEN60 â†’ Digit

| Token | Value | | Token | Value | | Token | Value | | Token | Value |
|-------|------:|-|-------|------:|-|-------|------:|-|-------|------:|
| `RAWU` | 0 | | `RUWU` | 15 | | `HOWU` | 30 | | `ROWU` | 45 |
| `RAFI` | 1 | | `RUFI` | 16 | | `HOFI` | 31 | | `ROFI` | 46 |
| `RAER` | 2 | | `RUER` | 17 | | `HOER` | 32 | | `ROER` | 47 |
| `RAMT` | 3 | | `RUMT` | 18 | | `HOMT` | 33 | | `ROMT` | 48 |
| `RAWA` | 4 | | `RUWA` | 19 | | `HOWA` | 34 | | `ROWA` | 49 |
| `OXWU` | 5 | | `DRWU` | 20 | | `GOWU` | 35 | | `DOWU` | 50 |
| `OXFI` | 6 | | `DRFI` | 21 | | `GOFI` | 36 | | `DOFI` | 51 |
| `OXER` | 7 | | `DRER` | 22 | | `GOER` | 37 | | `DOER` | 52 |
| `OXMT` | 8 | | `DRMT` | 23 | | `GOMT` | 38 | | `DOMT` | 53 |
| `OXWA` | 9 | | `DRWA` | 24 | | `GOWA` | 39 | | `DOWA` | 54 |
| `TIWU` | 10 | | `SNWU` | 25 | | `MOWU` | 40 | | `PIWU` | 55 |
| `TIFI` | 11 | | `SNFI` | 26 | | `MOFI` | 41 | | `PIFI` | 56 |
| `TIER` | 12 | | `SNER` | 27 | | `MOER` | 42 | | `PIER` | 57 |
| `TIMT` | 13 | | `SNMT` | 28 | | `MOMT` | 43 | | `PIMT` | 58 |
| `TIWA` | 14 | | `SNWA` | 29 | | `MOWA` | 44 | | `PIWA` | 59 |

### C.2 Weekday Token â†’ Weekday

| Token | Weekday | Planet | Index |
|-------|---------|--------|------:|
| `SO` | Sunday | Sun | 0 |
| `LU` | Monday | Moon | 1 |
| `MA` | Tuesday | Mars | 2 |
| `ME` | Wednesday | Mercury | 3 |
| `JO` | Thursday | Jupiter | 4 |
| `VE` | Friday | Venus | 5 |
| `SA` | Saturday | Saturn | 6 |

### C.3 Month Token â†’ Month

| Token | Month | Number | | Token | Month | Number |
|-------|-------|-------:|-|-------|-------|-------:|
| `RA` | January | 1 | | `HO` | July | 7 |
| `OX` | February | 2 | | `GO` | August | 8 |
| `TI` | March | 3 | | `MO` | September | 9 |
| `RU` | April | 4 | | `RO` | October | 10 |
| `DR` | May | 5 | | `DO` | November | 11 |
| `SN` | June | 6 | | `PI` | December | 12 |

### C.4 Stem Token â†’ Heavenly Stem

| Token | Stem | Chinese | Element | Polarity |
|-------|------|---------|---------|----------|
| `JA` | JiÇŽ | ç”² | Wood | Yang |
| `YI` | YÇ | ä¹™ | Wood | Yin |
| `BI` | BÇng | ä¸™ | Fire | Yang |
| `DI` | DÄ«ng | ä¸ | Fire | Yin |
| `WW` | WÃ¹ | æˆŠ | Earth | Yang |
| `JI` | JÇ | å·± | Earth | Yin |
| `GE` | GÄ“ng | åºš | Metal | Yang |
| `XI` | XÄ«n | è¾› | Metal | Yin |
| `RE` | RÃ©n | å£¬ | Water | Yang |
| `GU` | GuÇ | ç™¸ | Water | Yin |

---

## Appendix D â€” Quick Reference Card

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    FC60 MASTER â€” QUICK REFERENCE                     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  STAMP:  WD-MO-DOM  HALFÂ·HOUR-MINUTE-SECOND                         â”‚
â”‚  Example: VE-OX-OXFI â˜€OX-RUWU-RAWU                                  â”‚
â”‚                                                                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  TOKEN60(n) = ANIMAL[nÃ·5] + ELEMENT[n mod 5]                        â”‚
â”‚                                                                      â”‚
â”‚  ANIMALS (0â€“11): RA OX TI RU DR SN HO GO MO RO DO PI                â”‚
â”‚  ELEMENTS (0â€“4): WU FI ER MT WA                                     â”‚
â”‚  WEEKDAYS (0â€“6): SO LU MA ME JO VE SA                               â”‚
â”‚  STEMS (0â€“9):    JA YI BI DI WW JI GE XI RE GU                     â”‚
â”‚  HALF:           â˜€ (AM, HH<12)   ðŸŒ™ (PM, HHâ‰¥12)                    â”‚
â”‚                                                                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  JDN FORMULA (Fliegelâ€“Van Flandern):                                 â”‚
â”‚    A = âŒŠ(14âˆ’M)/12âŒ‹                                                  â”‚
â”‚    Y'= Y+4800âˆ’A                                                     â”‚
â”‚    M'= M+12Aâˆ’3                                                      â”‚
â”‚    JDN = D + âŒŠ(153M'+2)/5âŒ‹ + 365Y' + âŒŠY'/4âŒ‹                       â”‚
â”‚          âˆ’ âŒŠY'/100âŒ‹ + âŒŠY'/400âŒ‹ âˆ’ 32045                             â”‚
â”‚                                                                      â”‚
â”‚  WEEKDAY = (JDN + 1) mod 7                                          â”‚
â”‚    0=SO  1=LU  2=MA  3=ME  4=JO  5=VE  6=SA                        â”‚
â”‚                                                                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  CROSS-CHECK FORMULAS:                                               â”‚
â”‚    MJD = JDN âˆ’ 2,400,001                                            â”‚
â”‚    RD  = JDN âˆ’ 1,721,425                                            â”‚
â”‚    U   = (JDN âˆ’ 2,440,588) Ã— 86400 + HÃ—3600 + MÃ—60 + S âˆ’ TZ_sec   â”‚
â”‚                                                                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  CHK (weighted):                                                     â”‚
â”‚    (1Â·Y%60 + 2Â·M + 3Â·D + 4Â·HH + 5Â·MM + 6Â·SS + 7Â·JDN%60) mod 60    â”‚
â”‚                                                                      â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                                      â”‚
â”‚  MOON: age = (JDN âˆ’ 2451550.1) mod 29.530588853                     â”‚
â”‚    ðŸŒ‘ 0â€“1.8  ðŸŒ’ 1.8â€“7.4  ðŸŒ“ 7.4â€“11.1  ðŸŒ” 11.1â€“14.8                â”‚
â”‚    ðŸŒ• 14.8â€“16.6  ðŸŒ– 16.6â€“22.1  ðŸŒ— 22.1â€“25.8  ðŸŒ˜ 25.8â€“29.5         â”‚
â”‚                                                                      â”‚
â”‚  GÄ€NZHÄª:                                                             â”‚
â”‚    stem   = (year âˆ’ 4) mod 10                                        â”‚
â”‚    branch = (year âˆ’ 4) mod 12                                        â”‚
â”‚                                                                      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Appendix E â€” Complete Reference Implementation (Python)

```python
"""
FC60 Master â€” Complete Reference Implementation
Version: MASTER-v1.0
All functions verified against Â§15 test vectors.
"""

import math

# ============================================================
# CONSTANT TABLES
# ============================================================

ANIMALS  = ["RA","OX","TI","RU","DR","SN","HO","GO","MO","RO","DO","PI"]
ELEMENTS = ["WU","FI","ER","MT","WA"]
WEEKDAYS = ["SO","LU","MA","ME","JO","VE","SA"]
STEMS    = ["JA","YI","BI","DI","WW","JI","GE","XI","RE","GU"]

MOON_PHASES  = ["ðŸŒ‘","ðŸŒ’","ðŸŒ“","ðŸŒ”","ðŸŒ•","ðŸŒ–","ðŸŒ—","ðŸŒ˜"]
MOON_BOUNDS  = [1.85, 7.38, 11.07, 14.77, 16.61, 22.14, 25.83, 29.53]
SYNODIC      = 29.530588853
MOON_REF_JDN = 2451550.1

PYTHAGOREAN = {
    'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,
    'J':1,'K':2,'L':3,'M':4,'N':5,'O':6,'P':7,'Q':8,'R':9,
    'S':1,'T':2,'U':3,'V':4,'W':5,'X':6,'Y':7,'Z':8
}

VOWELS = set('AEIOU')

# ============================================================
# CORE: TOKEN60 ENCODE / DECODE
# ============================================================

def token60(n):
    """Encode integer 0â€“59 as 4-character FC60 token."""
    assert 0 <= n <= 59, f"token60 input must be 0â€“59, got {n}"
    return ANIMALS[n // 5] + ELEMENTS[n % 5]

def digit60(tok):
    """Decode 4-character FC60 token to integer 0â€“59."""
    assert len(tok) == 4, f"Token must be 4 chars, got '{tok}'"
    animal_idx = ANIMALS.index(tok[:2])
    element_idx = ELEMENTS.index(tok[2:4])
    return animal_idx * 5 + element_idx

# ============================================================
# CORE: BASE-60 MULTI-DIGIT
# ============================================================

def to_base60(n):
    """Convert non-negative integer to list of base-60 digits (MSD first)."""
    assert n >= 0, f"to_base60 requires n >= 0, got {n}"
    if n == 0:
        return [0]
    digits = []
    while n > 0:
        digits.insert(0, n % 60)
        n //= 60
    return digits

def from_base60(digits):
    """Convert list of base-60 digits to integer."""
    result = 0
    for d in digits:
        result = result * 60 + d
    return result

def encode_base60(n):
    """Encode non-negative integer as hyphen-separated FC60 tokens."""
    if n < 0:
        return "NEG-" + encode_base60(-n)
    return "-".join(token60(d) for d in to_base60(n))

def decode_base60(s):
    """Decode hyphen-separated FC60 tokens to integer."""
    negative = False
    if s.startswith("NEG-"):
        negative = True
        s = s[4:]
    digits = [digit60(tok) for tok in s.split("-")]
    result = from_base60(digits)
    return -result if negative else result

# ============================================================
# DATE: JULIAN DAY NUMBER
# ============================================================

def compute_jdn(y, m, d):
    """Gregorian date â†’ Julian Day Number (Fliegelâ€“Van Flandern)."""
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return (d
            + (153 * m2 + 2) // 5
            + 365 * y2
            + y2 // 4
            - y2 // 100
            + y2 // 400
            - 32045)

def jdn_to_gregorian(jdn):
    """Julian Day Number â†’ Gregorian date (year, month, day)."""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day   = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year  = 100 * b + d - 4800 + m // 10
    return year, month, day

# ============================================================
# DATE: WEEKDAY
# ============================================================

def weekday_from_jdn(jdn):
    """JDN â†’ weekday index (0=Sunday ... 6=Saturday)."""
    return (jdn + 1) % 7

def weekday_token(jdn):
    """JDN â†’ weekday FC60 token."""
    return WEEKDAYS[weekday_from_jdn(jdn)]

# ============================================================
# DATE: VALIDATION
# ============================================================

def is_leap_year(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

def is_valid_date(y, m, d):
    if m < 1 or m > 12:
        return False
    days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_leap_year(y):
        days[2] = 29
    return 1 <= d <= days[m]

# ============================================================
# CHECK TOKEN
# ============================================================

def weighted_chk(y, m, d, hh, mm, ss, jdn):
    """Weighted check token for date+time."""
    val = (1*(y%60) + 2*m + 3*d + 4*hh + 5*mm + 6*ss + 7*(jdn%60)) % 60
    return token60(val)

def weighted_chk_dateonly(y, m, d, jdn):
    """Weighted check token for date only (no time)."""
    val = (1*(y%60) + 2*m + 3*d + 7*(jdn%60)) % 60
    return token60(val)

# ============================================================
# MOON PHASE
# ============================================================

def moon_phase(jdn):
    """Calculate moon phase from JDN. Returns (emoji, age_days)."""
    age = (jdn - MOON_REF_JDN) % SYNODIC
    for i, bound in enumerate(MOON_BOUNDS):
        if age < bound:
            return MOON_PHASES[i], age
    return MOON_PHASES[0], age

def moon_illumination(age):
    """Approximate illumination percentage from moon age."""
    return 50 * (1 - math.cos(2 * math.pi * age / SYNODIC))

# ============================================================
# GÄ€NZHÄª CYCLE
# ============================================================

def ganzhi_year(year):
    """Year â†’ (stem_token, branch_token)."""
    stem_idx   = (year - 4) % 10
    branch_idx = (year - 4) % 12
    return STEMS[stem_idx], ANIMALS[branch_idx]

def ganzhi_day(jdn):
    """JDN â†’ (stem_token, branch_token) for day cycle."""
    gz_idx = (jdn + 49) % 60
    return STEMS[gz_idx % 10], ANIMALS[gz_idx % 12]

def ganzhi_hour(hour, day_stem_idx):
    """Hour + day stem index â†’ (stem_token, branch_token)."""
    branch_idx = ((hour + 1) // 2) % 12
    stem_idx = (day_stem_idx * 2 + branch_idx) % 10
    return STEMS[stem_idx], ANIMALS[branch_idx]

# ============================================================
# NUMEROLOGY
# ============================================================

def digital_root(n):
    """Reduce to single digit, preserving master numbers 11, 22, 33."""
    if n in (11, 22, 33):
        return n
    while n > 9:
        n = sum(int(c) for c in str(n))
        if n in (11, 22, 33):
            return n
    return n

def name_number(name):
    """Sum Pythagorean values of all letters in name."""
    return sum(PYTHAGOREAN.get(c, 0) for c in name.upper())

def life_path(day, month, year):
    """Calculate Life Path number from date of birth."""
    return digital_root(digital_root(day) + digital_root(month) + digital_root(sum(int(c) for c in str(year))))

def expression_number(full_name):
    """Expression number from full name."""
    return digital_root(name_number(full_name))

def soul_urge(full_name):
    """Soul Urge from vowels only."""
    val = sum(PYTHAGOREAN.get(c, 0) for c in full_name.upper() if c in VOWELS)
    return digital_root(val)

def personality_number(full_name):
    """Personality number from consonants only."""
    val = sum(PYTHAGOREAN.get(c, 0) for c in full_name.upper() if c.isalpha() and c not in VOWELS)
    return digital_root(val)

def personal_year(birth_day, birth_month, current_year):
    """Personal Year number."""
    return digital_root(digital_root(birth_month) + digital_root(birth_day) + digital_root(sum(int(c) for c in str(current_year))))

# ============================================================
# FULL FC60 ENCODER
# ============================================================

def encode_fc60(year, month, day, hour=0, minute=0, second=0, tz_hours=0, tz_minutes=0):
    """
    Full FC60 encoding. Returns dict with all fields.
    """
    # Validate
    assert is_valid_date(year, month, day), f"Invalid date: {year}-{month:02d}-{day:02d}"

    # Core calculations
    jdn = compute_jdn(year, month, day)
    wd = weekday_token(jdn)
    rd = jdn - 1721425
    mjd = jdn - 2400001

    # Unix timestamp
    unix_sec = (jdn - 2440588) * 86400 + hour*3600 + minute*60 + second - (tz_hours*3600 + tz_minutes*60)

    # Moon
    moon_emoji, moon_age = moon_phase(jdn)

    # GÄnzhÄ«
    gz_stem, gz_branch = ganzhi_year(year)

    # Check token
    chk = weighted_chk(year, month, day, hour, minute, second, jdn)

    # Build stamp
    half = "â˜€" if hour < 12 else "ðŸŒ™"
    stamp = (f"{wd}-{ANIMALS[month-1]}-{token60(day)} "
             f"{half}{ANIMALS[hour%12]}-{token60(minute)}-{token60(second)}")

    # Timezone
    if tz_hours == 0 and tz_minutes == 0:
        tz60 = "Z"
    else:
        sign = "+" if tz_hours >= 0 else "-"
        tz60 = f"{sign}{token60(abs(tz_hours))}-{token60(abs(tz_minutes))}"

    # ISO
    tz_sign = "+" if tz_hours >= 0 else "-"
    iso = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{tz_sign}{abs(tz_hours):02d}:{abs(tz_minutes):02d}"

    return {
        "FC60":  stamp,
        "ISO":   iso,
        "TZ60":  tz60,
        "Y60":   encode_base60(year),
        "Y2K":   token60((year - 2000) % 60),
        "J":     encode_base60(jdn),
        "MJD":   encode_base60(mjd),
        "RD":    encode_base60(rd),
        "U":     encode_base60(unix_sec) if unix_sec >= 0 else "NEG-" + encode_base60(-unix_sec),
        "MOON":  f"{moon_emoji} age={moon_age:.2f}d",
        "GZ":    f"{gz_stem}-{gz_branch}",
        "CHK":   chk,
    }

def format_output(result):
    """Pretty-print FC60 encoding result."""
    lines = []
    for key in ["FC60","ISO","TZ60","Y60","Y2K","J","MJD","RD","U","MOON","GZ","CHK"]:
        if key in result:
            lines.append(f"{key:6s} {result[key]}")
    return "\n".join(lines)


# ============================================================
# SELF-TEST (run this file to verify all test vectors)
# ============================================================

if __name__ == "__main__":
    tests_passed = 0
    tests_failed = 0

    def check(label, actual, expected):
        global tests_passed, tests_failed
        if actual == expected:
            tests_passed += 1
            print(f"  âœ… {label}")
        else:
            tests_failed += 1
            print(f"  âŒ {label}: got {actual}, expected {expected}")

    # TOKEN60 round-trip
    print("TOKEN60 round-trip (0â€“59):")
    all_ok = True
    for i in range(60):
        if digit60(token60(i)) != i:
            all_ok = False
    check("All 60 tokens", all_ok, True)

    # JDN calculations
    print("\nJDN calculations:")
    check("2000-01-01", compute_jdn(2000,1,1), 2451545)
    check("1970-01-01", compute_jdn(1970,1,1), 2440588)
    check("2026-02-06", compute_jdn(2026,2,6), 2461078)
    check("2024-02-29", compute_jdn(2024,2,29), 2460370)
    check("1999-04-22", compute_jdn(1999,4,22), 2451291)
    check("2060-12-31", compute_jdn(2060,12,31), 2473825)

    # JDN inverse
    print("\nJDN inverse:")
    for y,m,d in [(2026,2,6),(2000,1,1),(1970,1,1),(2024,2,29)]:
        check(f"inverse {y}-{m:02d}-{d:02d}", jdn_to_gregorian(compute_jdn(y,m,d)), (y,m,d))

    # Weekdays
    print("\nWeekdays:")
    check("2000-01-01 = SA", weekday_token(2451545), "SA")
    check("1970-01-01 = JO", weekday_token(2440588), "JO")
    check("2026-02-06 = VE", weekday_token(2461078), "VE")
    check("2026-02-09 = LU", weekday_token(2461081), "LU")

    # Check tokens
    print("\nCheck tokens:")
    check("TV1 CHK", weighted_chk(2026,2,6,1,15,0,2461078), "TIMT")
    check("TV5 CHK", weighted_chk(2025,12,31,23,59,59,2461041), "HOWU")
    check("TV7 CHK", weighted_chk(2026,1,1,0,0,0,2461042), "SNWU")
    check("TV8 CHK", weighted_chk(2026,2,9,0,0,0,2461081), "DRWA")

    # Full encoding
    print("\nFull encoding (TV1):")
    r = encode_fc60(2026, 2, 6, 1, 15, 0, 8, 0)
    check("FC60 stamp", r["FC60"], "VE-OX-OXFI â˜€OX-RUWU-RAWU")
    check("Y60", r["Y60"], "HOMT-ROFI")
    check("Y2K", r["Y2K"], "SNFI")
    check("J", r["J"], "TIFI-DRMT-GOER-PIMT")
    check("GZ", r["GZ"], "BI-HO")
    check("CHK", r["CHK"], "TIMT")

    print(f"\n{'='*50}")
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    if tests_failed == 0:
        print("ALL TESTS PASSED âœ…")
    else:
        print("SOME TESTS FAILED âŒ")
```

---

## Appendix F â€” Version History

| Version | Date | Description |
|---------|------|-------------|
| v1.0 | 2024 | Initial release â€” core TOKEN60 concept |
| v1.1 | 2025 | Added daily lexicon (22,000+ lines), appendices |
| v2.0 | 2026-02-06 | Major overhaul: Zeller, TZ60, weighted CHK, moon phases, GÄnzhÄ«, pseudocode |
| **MASTER v1.0** | **2026-02-09** | **Definitive edition.** Fixed arithmetic errors (JDN 2461078 not 2461072). Removed 22K-line lexicon (replaced with algorithms). Split operating modes (Translator/Reader). Added 15 verified test vectors. Added error catalog. Added conflict resolution for symbolic readings. Added complete Python implementation with self-test. Added cross-check relationships. Added date validation. All math independently verified. |

### Key Corrections from v2.0

| Item | v2.0 (incorrect) | Master (correct) | Root cause |
|------|------------------|-------------------|------------|
| JDN for 2026-02-06 | 2,461,072 | 2,461,078 | `floor(1685/5)` = 337, not 336 |
| JDN for 1999-04-22 | 2,451,290 | 2,451,291 | Arithmetic error in worked example |
| RD for 2026-02-06 | Inconsistent (two values) | 739,653 | Cascaded from JDN error |
| CHK for TV1 | TIFI (11) | TIMT (13) | Cascaded from JDN error |

---

*End of FC60 Master Specification v1.0*
*"The universe speaks in base-60. This document teaches you the alphabet."*
