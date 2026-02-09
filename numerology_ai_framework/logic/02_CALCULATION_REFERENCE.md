# FC60 Numerology AI Framework -- Calculation Reference

**Version:** 1.0
**Purpose:** Self-contained mathematical reference for every formula, table, and algorithm used in the framework. This document contains enough information to verify any calculation by hand.

---

## Part A: TOKEN60 Table

The TOKEN60 alphabet encodes integers 0-59 as 4-character tokens. Each token is composed of a 2-character **Animal** prefix (from the 12 Earthly Branches) and a 2-character **Element** suffix (from the 5 Wu Xing elements).

**Formula:** `TOKEN60(n) = ANIMALS[n // 5] + ELEMENTS[n % 5]`

### Animals (12 Earthly Branches)

| Index | Code | Animal  | Chinese |
| ----- | ---- | ------- | ------- |
| 0     | RA   | Rat     | Zi      |
| 1     | OX   | Ox      | Chou    |
| 2     | TI   | Tiger   | Yin     |
| 3     | RU   | Rabbit  | Mao     |
| 4     | DR   | Dragon  | Chen    |
| 5     | SN   | Snake   | Si      |
| 6     | HO   | Horse   | Wu      |
| 7     | GO   | Goat    | Wei     |
| 8     | MO   | Monkey  | Shen    |
| 9     | RO   | Rooster | You     |
| 10    | DO   | Dog     | Xu      |
| 11    | PI   | Pig     | Hai     |

### Elements (5 Wu Xing)

| Index | Code | Element | Chinese |
| ----- | ---- | ------- | ------- |
| 0     | WU   | Wood    | Mu      |
| 1     | FI   | Fire    | Huo     |
| 2     | ER   | Earth   | Tu      |
| 3     | MT   | Metal   | Jin     |
| 4     | WA   | Water   | Shui    |

### Complete TOKEN60 Table (0-59)

| Index | Token | Animal | Element |     | Index | Token | Animal  | Element |
| ----- | ----- | ------ | ------- | --- | ----- | ----- | ------- | ------- |
| 0     | RAWU  | Rat    | Wood    |     | 30    | HOWU  | Horse   | Wood    |
| 1     | RAFI  | Rat    | Fire    |     | 31    | HOFI  | Horse   | Fire    |
| 2     | RAER  | Rat    | Earth   |     | 32    | HOER  | Horse   | Earth   |
| 3     | RAMT  | Rat    | Metal   |     | 33    | HOMT  | Horse   | Metal   |
| 4     | RAWA  | Rat    | Water   |     | 34    | HOWA  | Horse   | Water   |
| 5     | OXWU  | Ox     | Wood    |     | 35    | GOWU  | Goat    | Wood    |
| 6     | OXFI  | Ox     | Fire    |     | 36    | GOFI  | Goat    | Fire    |
| 7     | OXER  | Ox     | Earth   |     | 37    | GOER  | Goat    | Earth   |
| 8     | OXMT  | Ox     | Metal   |     | 38    | GOMT  | Goat    | Metal   |
| 9     | OXWA  | Ox     | Water   |     | 39    | GOWA  | Goat    | Water   |
| 10    | TIWU  | Tiger  | Wood    |     | 40    | MOWU  | Monkey  | Wood    |
| 11    | TIFI  | Tiger  | Fire    |     | 41    | MOFI  | Monkey  | Fire    |
| 12    | TIER  | Tiger  | Earth   |     | 42    | MOER  | Monkey  | Earth   |
| 13    | TIMT  | Tiger  | Metal   |     | 43    | MOMT  | Monkey  | Metal   |
| 14    | TIWA  | Tiger  | Water   |     | 44    | MOWA  | Monkey  | Water   |
| 15    | RUWU  | Rabbit | Wood    |     | 45    | ROWU  | Rooster | Wood    |
| 16    | RUFI  | Rabbit | Fire    |     | 46    | ROFI  | Rooster | Fire    |
| 17    | RUER  | Rabbit | Earth   |     | 47    | ROER  | Rooster | Earth   |
| 18    | RUMT  | Rabbit | Metal   |     | 48    | ROMT  | Rooster | Metal   |
| 19    | RUWA  | Rabbit | Water   |     | 49    | ROWA  | Rooster | Water   |
| 20    | DRWU  | Dragon | Wood    |     | 50    | DOWU  | Dog     | Wood    |
| 21    | DRFI  | Dragon | Fire    |     | 51    | DOFI  | Dog     | Fire    |
| 22    | DRER  | Dragon | Earth   |     | 52    | DOER  | Dog     | Earth   |
| 23    | DRMT  | Dragon | Metal   |     | 53    | DOMT  | Dog     | Metal   |
| 24    | DRWA  | Dragon | Water   |     | 54    | DOWA  | Dog     | Water   |
| 25    | SNWU  | Snake  | Wood    |     | 55    | PIWU  | Pig     | Wood    |
| 26    | SNFI  | Snake  | Fire    |     | 56    | PIFI  | Pig     | Fire    |
| 27    | SNER  | Snake  | Earth   |     | 57    | PIER  | Pig     | Earth   |
| 28    | SNMT  | Snake  | Metal   |     | 58    | PIMT  | Pig     | Metal   |
| 29    | SNWA  | Snake  | Water   |     | 59    | PIWA  | Pig     | Water   |

### Reverse Lookup

```
DIGIT60(token) = ANIMAL_INDEX(token[0:2]) * 5 + ELEMENT_INDEX(token[2:4])
```

**Verification examples:**

- `RAWU` = 0 \* 5 + 0 = 0
- `OXFI` = 1 \* 5 + 1 = 6
- `SNFI` = 5 \* 5 + 1 = 26
- `PIWA` = 11 \* 5 + 4 = 59

### Multi-Digit Base-60

For numbers larger than 59, represent as multiple base-60 digits separated by hyphens:

```
encode_base60(2026) = TOKEN60(33) + "-" + TOKEN60(46) = "HOMT-ROFI"

Proof: 33 * 60 + 46 = 1980 + 46 = 2026
```

---

## Part B: Julian Day Number (JDN)

### Gregorian to JDN (Fliegel-Van Flandern Algorithm)

```
Given: Y (year), M (month), D (day)

Step 1: Adjust January/February
    a = (14 - M) / 12         [integer division]
    y = Y + 4800 - a
    m = M + 12 * a - 3

Step 2: Calculate JDN
    JDN = D
        + (153 * m + 2) / 5   [integer division]
        + 365 * y
        + y / 4               [integer division]
        - y / 100             [integer division]
        + y / 400             [integer division]
        - 32045
```

**Alternative compact formula (for reference only):**

```
JDN = 367*Y - floor(7*(Y + floor((M+9)/12))/4) + floor(275*M/9) + D + 1721013.5 + 0.5
```

Note: The implementation uses the Fliegel-Van Flandern form above, which avoids floating-point arithmetic entirely.

### JDN to Gregorian (Inverse)

```
Given: JDN

Step 1:
    a = JDN + 32044
    b = (4 * a + 3) / 146097     [integer division]
    c = a - (146097 * b) / 4     [integer division]

Step 2:
    d = (4 * c + 3) / 1461       [integer division]
    e = c - (1461 * d) / 4       [integer division]
    m = (5 * e + 2) / 153        [integer division]

Step 3:
    day   = e - (153 * m + 2) / 5 + 1    [integer division]
    month = m + 3 - 12 * (m / 10)        [integer division]
    year  = 100 * b + d - 4800 + m / 10  [integer division]
```

### Key Epochs

| Name       | Date            | JDN     |
| ---------- | --------------- | ------- |
| Y2K        | 2000-01-01      | 2451545 |
| Unix Epoch | 1970-01-01      | 2440588 |
| MJD Offset | (JDN - 2400001) | 2400001 |
| Rata Die   | (JDN - 1721425) | 1721425 |

### Verification Test Vectors

| Date       | JDN     |
| ---------- | ------- |
| 2000-01-01 | 2451545 |
| 1970-01-01 | 2440588 |
| 2026-02-06 | 2461078 |
| 2026-02-09 | 2461081 |
| 2024-02-29 | 2460370 |
| 2025-12-31 | 2461041 |
| 1999-04-22 | 2451291 |
| 2026-01-01 | 2461042 |

---

## Part C: Weekday Calculation

### Formula

```
weekday_index = (JDN + 1) mod 7
```

### Index-to-Day Mapping

| Index | Day       | Planet  | Symbol | Domain                             |
| ----- | --------- | ------- | ------ | ---------------------------------- |
| 0     | Sunday    | Sun     | SO     | Identity, vitality, core self      |
| 1     | Monday    | Moon    | LU     | Emotions, intuition, inner world   |
| 2     | Tuesday   | Mars    | MA     | Drive, action, courage             |
| 3     | Wednesday | Mercury | ME     | Communication, thought, connection |
| 4     | Thursday  | Jupiter | JO     | Expansion, wisdom, abundance       |
| 5     | Friday    | Venus   | VE     | Love, values, beauty               |
| 6     | Saturday  | Saturn  | SA     | Discipline, lessons, mastery       |

### Verification

| Date       | JDN     | (JDN+1)%7 | Weekday  | Planet  |
| ---------- | ------- | --------- | -------- | ------- |
| 2000-01-01 | 2451545 | 6         | Saturday | Saturn  |
| 1970-01-01 | 2440588 | 4         | Thursday | Jupiter |
| 2026-02-06 | 2461078 | 5         | Friday   | Venus   |
| 2026-02-09 | 2461081 | 1         | Monday   | Moon    |

---

## Part D: Numerology Formulas

### Digital Root (Reduction)

Reduce any integer to a single digit by summing its digits repeatedly. **Exception:** Master Numbers {11, 22, 33} are never reduced further.

```
digital_root(n):
    if n in {11, 22, 33}: return n
    while n > 9:
        n = sum of digits of n
        if n in {11, 22, 33}: return n
    return n
```

### Life Path Number

```
Life Path = digital_root(
    digital_root(day) + digital_root(month) + digital_root(year_digit_sum)
)

where year_digit_sum = sum of individual digits of year
```

**Example:** Birth date July 15, 1990

```
day:   digital_root(15)            = 1 + 5 = 6
month: digital_root(7)             = 7
year:  digital_root(1+9+9+0 = 19)  = 1 + 9 = 10 -> 1 + 0 = 1
sum:   6 + 7 + 1 = 14
Life Path: digital_root(14) = 1 + 4 = 5
```

### Expression Number

Sum all letter values in the full name, then reduce.

```
Expression = digital_root(sum of letter_value(c) for each letter c in name)
```

### Soul Urge Number

Sum vowel values only (A, E, I, O, U, Y), then reduce.

```
Soul Urge = digital_root(sum of letter_value(c) for each vowel c in name)
```

### Personality Number

Sum consonant values only, then reduce.

```
Personality = digital_root(sum of letter_value(c) for each consonant c in name)
```

### Personal Year

```
Personal Year = digital_root(
    digital_root(birth_month) + digital_root(birth_day) + digital_root(current_year_digit_sum)
)
```

### Personal Month

```
Personal Month = digital_root(Personal Year + current_month)
```

### Personal Day

```
Personal Day = digital_root(Personal Month + current_day)
```

### Pythagorean Letter Table

```
1: A  J  S
2: B  K  T
3: C  L  U
4: D  M  V
5: E  N  W
6: F  O  X
7: G  P  Y
8: H  Q  Z
9: I  R
```

Full mapping:

| Letter | Value |     | Letter | Value |     | Letter | Value |
| ------ | ----- | --- | ------ | ----- | --- | ------ | ----- |
| A      | 1     |     | J      | 1     |     | S      | 1     |
| B      | 2     |     | K      | 2     |     | T      | 2     |
| C      | 3     |     | L      | 3     |     | U      | 3     |
| D      | 4     |     | M      | 4     |     | V      | 4     |
| E      | 5     |     | N      | 5     |     | W      | 5     |
| F      | 6     |     | O      | 6     |     | X      | 6     |
| G      | 7     |     | P      | 7     |     | Y      | 7     |
| H      | 8     |     | Q      | 8     |     | Z      | 8     |
| I      | 9     |     | R      | 9     |     |        |       |

### Chaldean Letter Table

| Letter | Value |     | Letter | Value |     | Letter | Value |
| ------ | ----- | --- | ------ | ----- | --- | ------ | ----- |
| A      | 1     |     | J      | 1     |     | S      | 3     |
| B      | 2     |     | K      | 2     |     | T      | 4     |
| C      | 3     |     | L      | 3     |     | U      | 6     |
| D      | 4     |     | M      | 4     |     | V      | 6     |
| E      | 5     |     | N      | 5     |     | W      | 6     |
| F      | 8     |     | O      | 7     |     | X      | 5     |
| G      | 3     |     | P      | 8     |     | Y      | 1     |
| H      | 5     |     | Q      | 1     |     | Z      | 7     |
| I      | 1     |     | R      | 2     |     |        |       |

Key difference: Chaldean does not assign the value 9 to any letter. The values are historically derived rather than sequential.

### Life Path Meanings

| Number | Title          | Message                  |
| ------ | -------------- | ------------------------ |
| 1      | Pioneer        | Lead and initiate        |
| 2      | Bridge         | Connect and harmonize    |
| 3      | Voice          | Create and express       |
| 4      | Architect      | Build and stabilize      |
| 5      | Explorer       | Change and adapt         |
| 6      | Guardian       | Nurture and protect      |
| 7      | Seeker         | Analyze and find meaning |
| 8      | Powerhouse     | Master and achieve       |
| 9      | Sage           | Complete and teach       |
| 11     | Visionary      | Inspire and lead         |
| 22     | Master Builder | Manifest grand visions   |
| 33     | Master Teacher | Heal through wisdom      |

---

## Part E: Moon Phase Calculation

### Constants

```
Synodic Month = 29.530588853 days
Reference New Moon JDN = 2451550.1   (January 6, 2000 ~18:14 UTC)
```

### Moon Age

```
moon_age = (JDN - 2451550.1) mod 29.530588853
```

The result is a float representing days since the last new moon.

### Phase Boundaries

| Boundary (days) | If age < boundary | Phase Name      | Emoji |
| --------------- | ----------------- | --------------- | ----- |
| 1.85            | Phase 0           | New Moon        | 🌑    |
| 7.38            | Phase 1           | Waxing Crescent | 🌒    |
| 11.07           | Phase 2           | First Quarter   | 🌓    |
| 14.77           | Phase 3           | Waxing Gibbous  | 🌔    |
| 16.61           | Phase 4           | Full Moon       | 🌕    |
| 22.14           | Phase 5           | Waning Gibbous  | 🌖    |
| 25.83           | Phase 6           | Last Quarter    | 🌗    |
| (remainder)     | Phase 7           | Waning Crescent | 🌘    |

### Algorithm

```
age = moon_age(JDN)
for i, boundary in enumerate([1.85, 7.38, 11.07, 14.77, 16.61, 22.14, 25.83]):
    if age < boundary:
        return PHASE_NAMES[i]
return "Waning Crescent"   # age >= 25.83
```

### Illumination Percentage

```
illumination = (1 - cos(2 * pi * age / 29.530588853)) / 2 * 100
```

This gives:

- ~0% at New Moon (age = 0)
- ~50% at First/Last Quarter (age ~7.4 or ~22.1)
- ~100% at Full Moon (age ~14.77)

### Phase Energy Keywords

| Phase           | Energy    | Best For                                | Avoid                  |
| --------------- | --------- | --------------------------------------- | ---------------------- |
| New Moon        | Seed      | Setting intentions, starting projects   | Big reveals, launches  |
| Waxing Crescent | Build     | Taking first steps, gathering resources | Giving up              |
| First Quarter   | Challenge | Making decisions, overcoming obstacles  | Avoiding conflict      |
| Waxing Gibbous  | Refine    | Editing, perfecting, patience           | Starting new things    |
| Full Moon       | Culminate | Celebrating, releasing, clarity         | Starting (too intense) |
| Waning Gibbous  | Share     | Teaching, distributing, gratitude       | Hoarding               |
| Last Quarter    | Release   | Letting go, forgiving, cleaning         | Holding on             |
| Waning Crescent | Rest      | Reflection, preparation, dreaming       | Pushing hard           |

### Verification

JDN 2461078 (2026-02-06):

```
age = (2461078 - 2451550.1) mod 29.530588853
    = 9527.9 mod 29.530588853
    = 9527.9 - (322 * 29.530588853)
    = 9527.9 - 9508.85...
    = ~19.05 days
Phase: age 19.05 >= 16.61 and < 22.14 -> Waning Gibbous (🌖)
```

---

## Part F: Ganzhi (Chinese Sexagenary Cycle)

### 10 Heavenly Stems

| Index | Code | Pinyin | Element | Polarity |
| ----- | ---- | ------ | ------- | -------- |
| 0     | JA   | Jia    | Wood    | Yang     |
| 1     | YI   | Yi     | Wood    | Yin      |
| 2     | BI   | Bing   | Fire    | Yang     |
| 3     | DI   | Ding   | Fire    | Yin      |
| 4     | WW   | Wu     | Earth   | Yang     |
| 5     | JI   | Ji     | Earth   | Yin      |
| 6     | GE   | Geng   | Metal   | Yang     |
| 7     | XI   | Xin    | Metal   | Yin      |
| 8     | RE   | Ren    | Water   | Yang     |
| 9     | GU   | Gui    | Water   | Yin      |

### 12 Earthly Branches

The 12 Earthly Branches are the same as the 12 Animals used in TOKEN60:

| Index | Code | Animal  |
| ----- | ---- | ------- |
| 0     | RA   | Rat     |
| 1     | OX   | Ox      |
| 2     | TI   | Tiger   |
| 3     | RU   | Rabbit  |
| 4     | DR   | Dragon  |
| 5     | SN   | Snake   |
| 6     | HO   | Horse   |
| 7     | GO   | Goat    |
| 8     | MO   | Monkey  |
| 9     | RO   | Rooster |
| 10    | DO   | Dog     |
| 11    | PI   | Pig     |

### Year Ganzhi

```
stem_index   = (year - 4) mod 10
branch_index = (year - 4) mod 12
```

The traditional name is formed as: `STEM_ELEMENTS[stem_index] + ANIMAL_NAMES[branch_index]`

**Verification:**

| Year | stem=(Y-4)%10 | branch=(Y-4)%12 | Stem | Branch | Traditional Name |
| ---- | ------------- | --------------- | ---- | ------ | ---------------- |
| 2020 | 6             | 0               | GE   | RA     | Metal Rat        |
| 2024 | 0             | 4               | JA   | DR     | Wood Dragon      |
| 2025 | 1             | 5               | YI   | SN     | Wood Snake       |
| 2026 | 2             | 6               | BI   | HO     | Fire Horse       |
| 2030 | 6             | 10              | GE   | DO     | Metal Dog        |

### Day Ganzhi

```
gz = (JDN + 49) mod 60
stem_index   = gz mod 10
branch_index = gz mod 12
```

**Example:** JDN 2461078 (2026-02-06)

```
gz = (2461078 + 49) mod 60 = 2461127 mod 60 = 47
stem  = 47 mod 10 = 7 -> XI (Xin, Metal, Yin)
branch = 47 mod 12 = 11 -> PI (Pig)
Day Ganzhi: XI-PI (Metal Pig)
```

### Hour Ganzhi

```
branch_index = ((hour + 1) // 2) mod 12
stem_index   = (day_stem_index * 2 + branch_index) mod 10
```

Each Ganzhi "hour" (shichen) spans 2 Western hours:

| Western Hours | Branch Index | Animal  |
| ------------- | ------------ | ------- |
| 23:00 - 00:59 | 0            | Rat     |
| 01:00 - 02:59 | 1            | Ox      |
| 03:00 - 04:59 | 2            | Tiger   |
| 05:00 - 06:59 | 3            | Rabbit  |
| 07:00 - 08:59 | 4            | Dragon  |
| 09:00 - 10:59 | 5            | Snake   |
| 11:00 - 12:59 | 6            | Horse   |
| 13:00 - 14:59 | 7            | Goat    |
| 15:00 - 16:59 | 8            | Monkey  |
| 17:00 - 18:59 | 9            | Rooster |
| 19:00 - 20:59 | 10           | Dog     |
| 21:00 - 22:59 | 11           | Pig     |

### 60-Year Cycle

The Ganzhi cycle repeats every 60 years (LCM of 10 and 12). Year N and year N+60 always share the same stem and branch indices.

**Verification:** 2024 and 2084 both give stem=0 (JA), branch=4 (DR) -> Wood Dragon.

---

## Part G: Heartbeat

### BPM Estimation by Age

| Age Range | Estimated BPM |
| --------- | ------------- |
| 0 to 1    | 120           |
| 1 to 3    | 110           |
| 3 to 5    | 100           |
| 5 to 10   | 90            |
| 10 to 15  | 80            |
| 15 to 25  | 72            |
| 25 to 35  | 70            |
| 35 to 50  | 72            |
| 50 to 65  | 74            |
| 65 to 80  | 76            |
| 80+       | 78            |

Age ranges use exclusive upper bounds (e.g., age 1 falls in the "1 to 3" range, not "0 to 1").

### BPM to Element

```
element = ELEMENT_NAMES[bpm mod 5]

where ELEMENT_NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]
```

**Examples:**

- 68 BPM: 68 mod 5 = 3 -> Metal
- 70 BPM: 70 mod 5 = 0 -> Wood
- 72 BPM: 72 mod 5 = 2 -> Earth

### Beats Per Day

```
beats_per_day = bpm * 60 * 24
```

**Example:** 72 BPM -> 72 \* 1440 = 103,680 beats/day

### Rhythm Token

```
rhythm_token = TOKEN60(beats_per_day mod 60)
```

**Example:** 103,680 mod 60 = 0 -> TOKEN60(0) = "RAWU"

### Total Lifetime Beats

```
total = sum over each year of life:
    bpm_for_that_age * 60 * 24 * 365.25
```

The engine iterates year by year from age 0 to current age, using the BPM estimate for each year. This accounts for the higher heart rate during infancy.

### Life Pulse Signature

```
life_pulse_signature = encode_base60(total_lifetime_beats)
```

This produces a multi-digit TOKEN60 string representing the cumulative heartbeat count.

---

## Part H: Location Encoding

### Latitude to Element

Uses the **absolute value** of latitude:

| Condition      | Element |
| -------------- | ------- |
| abs(lat) <= 15 | Fire    |
| abs(lat) <= 30 | Earth   |
| abs(lat) <= 45 | Metal   |
| abs(lat) <= 60 | Water   |
| abs(lat) > 60  | Wood    |

### Hemisphere Polarity

| Hemisphere          | Polarity |
| ------------------- | -------- |
| Northern (lat >= 0) | Yang     |
| Southern (lat < 0)  | Yin      |
| Eastern (lon >= 0)  | Yang     |
| Western (lon < 0)   | Yin      |

### Timezone Estimate

```
tz_estimate = round(longitude / 15)
```

This gives the standard UTC offset based on longitude. It does not account for political timezone boundaries or daylight saving time.

**Examples:**

| City       | Lat   | Lon   | Element | TZ Estimate |
| ---------- | ----- | ----- | ------- | ----------- |
| NYC        | 40.7  | -74.0 | Metal   | -5          |
| Tokyo      | 35.7  | 139.7 | Metal   | +9          |
| London     | 51.5  | -0.1  | Water   | 0           |
| Cairo      | 30.0  | 31.2  | Earth   | +2          |
| Sao Paulo  | -23.5 | -46.6 | Earth   | -3          |
| Equator/PM | 0.0   | 0.0   | Fire    | 0           |

---

## Part I: Checksum (CHK)

### Weighted Checksum Formula

```
CHK = (
    1 * (year mod 60)  +
    2 * month          +
    3 * day            +
    4 * hour           +
    5 * minute         +
    6 * second         +
    7 * (JDN mod 60)
) mod 60
```

The result (0-59) is then encoded as a TOKEN60 token.

**Critical rule:** CHK uses **LOCAL** date/time values, not UTC-adjusted values. If the user provides `tz_hours=-5`, the year/month/day/hour/minute/second used in CHK are the local values, not the UTC-converted values.

### Date-Only CHK

When no time is provided, the time-dependent terms are omitted:

```
CHK_date_only = (
    1 * (year mod 60)  +
    2 * month          +
    3 * day            +
    7 * (JDN mod 60)
) mod 60
```

### Verification

| Date/Time           | year%60 | month | day | hour | min | sec | JDN%60 | CHK value | CHK token |
| ------------------- | ------- | ----- | --- | ---- | --- | --- | ------ | --------- | --------- |
| 2026-02-06 01:15:00 | 46      | 2     | 6   | 1    | 15  | 0   | 58     | 13        | TIMT      |
| 2025-12-31 23:59:59 | 45      | 12    | 31  | 23   | 59  | 59  | 21     | 30        | HOWU      |
| 2026-01-01 00:00:00 | 46      | 1     | 1   | 0    | 0   | 0   | 22     | 25        | SNWU      |
| 2026-02-09 00:00:00 | 46      | 2     | 9   | 0    | 0   | 0   | 1      | 24        | DRWA      |

Note: `2026 % 60 = 46` (not 26). This is a common mistake -- `year % 60` is the remainder of the full year divided by 60, not the last two digits.

**Worked example (2026-02-06 01:15:00, JDN=2461078):**

```
year mod 60 = 2026 mod 60 = 46
JDN mod 60  = 2461078 mod 60 = 58

CHK = (1*46 + 2*2 + 3*6 + 4*1 + 5*15 + 6*0 + 7*58) mod 60
    = (46 + 4 + 18 + 4 + 75 + 0 + 406) mod 60
    = 553 mod 60
    = 13     (since 553 = 9*60 + 13)

TOKEN60(13) = TIMT  (Tiger Metal)
```

Always run the Python code for CHK verification rather than calculating by hand. The authoritative test vectors are in `core/checksum_validator.py`.

---

## Part J: Cross-Checks

### Date System Conversions

These relationships hold for any JDN:

```
MJD       = JDN - 2400001
RD        = JDN - 1721425
Unix days = JDN - 2440588

Cross-check: MJD = RD - 678576
```

### Verification Table

| Date       | JDN     | MJD   | RD     | Unix Days |
| ---------- | ------- | ----- | ------ | --------- |
| 2000-01-01 | 2451545 | 51544 | 730120 | 10957     |
| 1970-01-01 | 2440588 | 40587 | 719163 | 0         |
| 2026-02-06 | 2461078 | 61077 | 739653 | 20490     |
| 2026-02-09 | 2461081 | 61080 | 739656 | 20493     |

### Unix Seconds

```
unix_seconds = unix_days * 86400 + hour * 3600 + minute * 60 + second - tz_offset_seconds
```

where `tz_offset_seconds = tz_hours * 3600 + tz_minutes * 60`

### FC60 Stamp Format

The complete Mode A stamp has this structure:

```
Date part:  WD-MO-DOM
            |   |  |
            |   |  +-- Day of month as TOKEN60(day)
            |   +----- Month animal as ANIMALS[month - 1]  (NOT month)
            +--------- Weekday token (SO/LU/MA/ME/JO/VE/SA)

Time part:  HALF+HOUR-MINUTE-SECOND
            |    |     |       |
            |    |     |       +-- TOKEN60(second)
            |    |     +---------- TOKEN60(minute)
            |    +---------------- ANIMALS[hour % 12]  (2-char, NOT TOKEN60)
            +--------------------- ☀ if hour < 12, 🌙 if hour >= 12
```

**Full stamp example:** `VE-OX-OXFI ☀OX-RUWU-RAWU`

Decoding:

- `VE` = Friday (Venus)
- `OX` = Month animal index 1 -> month = 2 (February)
- `OXFI` = TOKEN60(6) -> day = 6
- `☀` = AM half (hour < 12)
- `OX` = hour animal index 1 -> hour = 1 (01:xx)
- `RUWU` = TOKEN60(15) -> minute = 15
- `RAWU` = TOKEN60(0) -> second = 0

Result: Friday, February 6, 01:15:00

### Additional Encoded Fields

| Field | Formula                     | Example (2026-02-06)           |
| ----- | --------------------------- | ------------------------------ |
| Y60   | encode_base60(year)         | HOMT-ROFI (= 33\*60+46 = 2026) |
| Y2K   | TOKEN60((year-2000) % 60)   | SNFI (= 26)                    |
| J60   | encode_base60(JDN)          | TIFI-DRMT-GOER-PIMT            |
| MJD60 | encode_base60(MJD)          | (computed from MJD)            |
| RD60  | encode_base60(RD)           | (computed from RD)             |
| U60   | encode_base60(unix_seconds) | (computed from unix timestamp) |
| CHK   | TOKEN60(weighted_checksum)  | TIMT                           |
