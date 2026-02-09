# 05 -- Error Handling and Edge Cases

**Version:** 1.0
**Framework:** FC60 Numerology AI Framework
**Purpose:** Document all known edge cases, invalid inputs, ambiguities, and the framework's behavior for each. This guide ensures consistent handling across all integrations.

---

## 1. Invalid Dates

The framework validates all dates through `JulianDateEngine.is_valid_date()` before processing. Invalid dates raise `ValueError`.

### February 29 on Non-Leap Years

```python
# This raises ValueError: Invalid date: 2025-02-29
FC60StampEngine.encode(2025, 2, 29, 0, 0, 0)
```

**Leap year rules (Gregorian):**

- Divisible by 4: leap year
- Divisible by 100: NOT a leap year
- Divisible by 400: leap year

Examples: 2024 is leap (div by 4). 1900 is NOT leap (div by 100 but not 400). 2000 IS leap (div by 400).

**Handling:** Catch `ValueError` and prompt the user to check their date. Do not silently correct to February 28.

### Day 31 on 30-Day Months

April, June, September, and November have 30 days. Passing day=31 for these months raises `ValueError`.

```python
# This raises ValueError: Invalid date: 2026-04-31
FC60StampEngine.encode(2026, 4, 31, 0, 0, 0)
```

### Month 0, Month 13, or Negative Months

Month must be in range 1-12. Values outside this range cause `is_valid_date()` to return `False`, and the engine raises `ValueError`.

### Year 0

The Gregorian calendar has no year 0 (1 BCE is followed by 1 CE). However, the astronomical year numbering system does use year 0. The framework's JDN algorithm handles year 0 mathematically -- it will compute a valid JDN. If your application follows historical convention, validate that year != 0 before calling the engine.

---

## 2. Missing Timezone

**Default behavior:** When `tz_hours` and `tz_minutes` are not provided, they default to 0 (UTC).

**Impact on the reading:**

- The FC60 stamp's timezone field will show `Z` (UTC)
- CHK uses LOCAL values, so if the user's actual timezone differs from UTC, the stamp is technically encoding UTC-adjusted time while using local-time-based CHK. This is by design -- CHK always uses the values as passed, regardless of timezone.

**Best practice:** Always note in the reading footer when timezone was assumed:

> Timezone: UTC (assumed -- user did not provide timezone)

If the user provides location coordinates but no explicit timezone, the framework's `LocationEngine.timezone_estimate()` can estimate a timezone from longitude. However, if both a location-derived timezone and an explicit `tz_hours` are provided, **always use the explicit value**.

---

## 3. Non-Latin Names

The numerology engine processes only A-Z letters. All other characters are ignored during letter-value summation.

```python
# Letters extracted: "J", "O", "S", "E" -- accented and non-Latin chars are ignored
NumerologyEngine.expression_number("Jose\u0301")  # Jose with combining accent
```

**Characters that are ignored:**

- Accented Latin characters (e, a, u, o, n with diacritics) -- the base letter IS counted if it is A-Z, but combining marks are ignored
- Chinese, Japanese, Korean, Arabic, Hebrew, Cyrillic, and all other non-Latin scripts
- Numbers, punctuation, spaces
- Emoji

**Recommendation for users with non-Latin names:**

- Provide a romanized (transliterated) version of the name
- Use the most common transliteration standard for the source language
- Note in the reading that a transliterated name was used, which may affect letter-value accuracy
- If the user has an official Latin-alphabet name (e.g., on a passport), prefer that version

**Example:**

> Name provided: transliterated from original script. The numerology calculations use the romanized form. For maximum accuracy, use the name as it appears on official Latin-alphabet documents.

---

## 4. Hyphens, Apostrophes, and Special Characters in Names

The framework strips all non-alphabetic characters before processing. Only A-Z letters contribute to numerology calculations.

| Input Name         | Letters Processed | Notes                             |
| ------------------ | ----------------- | --------------------------------- |
| "Mary-Jane"        | MARYJANE          | Hyphen stripped                   |
| "O'Brien"          | OBRIEN            | Apostrophe stripped               |
| "de la Cruz"       | DELACRUZ          | Spaces stripped                   |
| "Smith III"        | SMITHIII          | Roman numerals treated as letters |
| "J. R. R. Tolkien" | JRRTOLKIEN        | Periods and spaces stripped       |

This is consistent with standard Pythagorean and Chaldean practice: only the letter values matter.

---

## 5. Pre-1900 and Post-2100 Dates

The framework handles any valid Gregorian date. The JDN algorithm (Fliegel-Van Flandern) is accurate for all positive and negative years in the proleptic Gregorian calendar.

**Known limitations for distant dates:**

### Moon Phase Accuracy

The moon phase calculation uses a fixed synodic month approximation (29.530588853 days) with a reference New Moon at JDN 2451550.1 (January 6, 2000). For dates far from the reference point, accumulated error increases:

| Distance from 2000 | Approximate Error |
| ------------------ | ----------------- |
| Within 100 years   | < 0.5 days        |
| 100-500 years      | 0.5 - 2 days      |
| 500+ years         | > 2 days          |

For symbolic readings, this level of accuracy is acceptable. For astronomical precision, use an ephemeris.

### Ganzhi Cycles

The sexagenary cycle is purely mathematical (modular arithmetic) and remains accurate for any year. There is no accumulation of error.

### Weekday Calculation

Weekday from JDN is also purely mathematical (`(JDN + 1) % 7`) and is exact for all dates.

---

## 6. Negative Unix Timestamps (Pre-1970 Dates)

Dates before January 1, 1970 produce negative Unix day counts. The framework handles this correctly because all internal calculations use Julian Day Numbers, not Unix timestamps.

```python
# 1969-12-31: JDN is valid, Unix days = -1
jdn = JulianDateEngine.gregorian_to_jdn(1969, 12, 31)  # 2440587
unix_days = jdn - JulianDateEngine.EPOCH_UNIX           # -1
```

The `u60` field in the FC60 stamp uses `max(0, unix_seconds)` for pre-epoch dates, so it will show `RAWU` (0) for dates before 1970. This is a known simplification. The J60 field (base-60 encoded JDN) remains accurate for all dates.

---

## 7. Conflicting User Information

### Location-Derived vs. Explicit Timezone

If the user provides both:

- Location coordinates (from which `LocationEngine.timezone_estimate()` derives a timezone)
- Explicit `tz_hours` / `tz_minutes` parameters

**Rule:** Always use the explicit timezone. The location-derived timezone is an estimate based on longitude (±15 degrees per hour zone) and does not account for political timezone boundaries or daylight saving time.

### Conflicting Dates

If the user provides `current_date` as a `datetime` object AND separate `current_hour` / `current_minute` / `current_second` values, the time components from the explicit parameters override the time from the `datetime` object. The date (year, month, day) always comes from the `datetime` object.

This is intentional -- it allows specifying "today's date but at a specific time."

---

## 8. Missing Optional Data and Graceful Degradation

The framework is designed to produce a valid reading with as little as a name and birth date. Each missing dimension reduces confidence but does not cause errors.

| Missing Dimension | Confidence Impact    | Sections Affected                                      |
| ----------------- | -------------------- | ------------------------------------------------------ |
| Mother's name     | -10%                 | No mother influence in Core Identity                   |
| Gender            | 0% (no score impact) | No polarity overlay                                    |
| Location          | -5%                  | No location element, hemisphere, or TZ data            |
| Heartbeat / BPM   | -5% (estimated used) | Uses age-based estimate instead of actual              |
| Current time      | -5%                  | No hour animal, minute token, half marker, Ganzhi hour |
| Timezone          | 0% (defaults UTC)    | Stamp uses UTC; note in footer                         |

**Reading structure with missing data:**

- Sections that depend on missing data are shortened, not omitted
- The Footer explicitly lists what was not provided
- The Confidence score adjusts automatically via `_calculate_confidence()`

**Example footer with missing data:**

> Confidence: 65% (medium)
> Data sources: FC60 stamp, weekday calculation, Pythagorean numerology, lunar phase, Ganzhi cycle
> Not provided: location, mother's name, gender, actual BPM, exact time of day
> Note: This reading uses estimated heartbeat data and UTC timezone by default.

---

## 9. "I Don't Know My Birth Time" Handling

Birth time is not used in this framework -- the framework uses **current** time (the time of the reading), not birth time. However, if the user does not provide a current time:

**What is omitted:**

- Hour animal (no `_hour_animal` in stamp)
- Minute token (no `_minute_token` in stamp)
- Half marker (no sun/moon indicator)
- Ganzhi hour pillar
- Time-of-day context band
- Sun/Moon paradox check

**What still works:**

- Full numerology profile (name + DOB based)
- FC60 date stamp (weekday-month-DOM)
- Moon phase (based on JDN, not time of day)
- Ganzhi year and day pillars
- Heartbeat estimation
- Location encoding

**Recommended note in reading:**

> Time-specific analysis (hour energy, minute texture, Ganzhi hour pillar) is not available because no time of day was provided. The core identity and day-level patterns remain valid.

---

## 10. Y2K and Year-60 Ambiguity

The base-60 encoding of years uses the full year value, not a modular reduction:

```python
Base60Codec.encode_base60(2000)  # "HOMT-DRWU"
Base60Codec.encode_base60(2060)  # "HOMT-MOWU"  -- different from 2000
```

The Y60 field in the FC60 stamp always uses the full 4-digit year encoding, so there is no ambiguity between 2000 and 2060.

However, the `y2k` field uses `(year - 2000) % 60`, which means:

- Year 2000 maps to token60(0) = "RAWU"
- Year 2060 also maps to token60(0) = "RAWU"

**Rule:** Always store and display the full year (Y60 field). The y2k field is a convenience shorthand and should not be used as a unique identifier. When displaying years, always use the 4-digit form.

---

## 11. Empty Name

If `full_name` is an empty string `""`:

```python
NumerologyEngine.expression_number("")   # Returns 0
NumerologyEngine.soul_urge("")           # Returns 0
NumerologyEngine.personality_number("")  # Returns 0
```

**Impact:**

- Expression, Soul Urge, and Personality are all 0
- Life Path is still calculated from DOB (unaffected by name)
- The reading still works but with significantly reduced interpretive depth
- Confidence drops because no name-based patterns can be detected

**Recommended handling:**

- If the name is empty, note this in the reading: "No name was provided. Core identity analysis is limited to the Life Path number derived from the date of birth."
- Do not treat 0 as a valid numerology number for interpretation -- it means "no data," not "the number zero has meaning."

---

## 12. Very Long Names

There is no practical length limit on names. All letters are summed and then reduced via `digital_root()`.

```python
# This works fine -- all 100+ letters are summed, then reduced
NumerologyEngine.expression_number("A" * 1000)  # Valid, returns a single digit or master number
```

The digital root function ensures the result is always a single digit (1-9) or a master number (11, 22, 33), regardless of input length.

---

## 13. Unusual BPM Values

The framework accepts any positive integer as `actual_bpm`. It does not validate medical plausibility.

| BPM Value | Framework Behavior                      | Medical Context          |
| --------- | --------------------------------------- | ------------------------ |
| 1         | Accepted, element = Wood (1 % 5 = 1)    | Not physiologically real |
| 40        | Accepted, element = Wood (40 % 5 = 0)   | Very low but possible    |
| 72        | Accepted, element = Earth (72 % 5 = 2)  | Normal resting rate      |
| 200       | Accepted, element = Wood (200 % 5 = 0)  | Extreme exercise HR      |
| 999       | Accepted, element = Water (999 % 5 = 4) | Not physiologically real |

**Design rationale:** The framework is a numerological tool, not a medical device. Validating BPM ranges is the responsibility of the calling application, not the calculation engine.

If no `actual_bpm` is provided, the engine uses age-based estimation from `HeartbeatEngine.BPM_TABLE`.

---

## 14. Extreme Geographic Coordinates

### North and South Poles

Latitude values of 90.0 and -90.0 are handled correctly:

```python
LocationEngine.location_signature(90.0, 0.0)
# element: "Wood" (lat zone 60-90), lat_hemisphere: "N", lat_polarity: "Yang"

LocationEngine.location_signature(-90.0, 0.0)
# element: "Wood" (lat zone 60-90), lat_hemisphere: "S", lat_polarity: "Yin"
```

### International Date Line

Longitude values of 180.0 and -180.0 are handled correctly:

```python
LocationEngine.location_signature(0.0, 180.0)
# timezone_estimate: 12

LocationEngine.location_signature(0.0, -180.0)
# timezone_estimate: -12
```

### Equator and Prime Meridian

Latitude 0.0 maps to "N" hemisphere (lat >= 0) and "Yang" polarity. Longitude 0.0 maps to "E" hemisphere (lon >= 0) and "Yang" polarity.

```python
LocationEngine.location_signature(0.0, 0.0)
# element: "Fire" (lat zone 0-15), lat_hemisphere: "N", lon_hemisphere: "E"
# Both polarities: "Yang"
```

### Out-of-Range Coordinates

The framework does not validate that latitude is within [-90, 90] or longitude within [-180, 180]. Passing values outside these ranges will produce mathematically valid but geographically meaningless results. The calling application should validate coordinate ranges before passing them to the engine.

---

## 15. Summary: Error Response Patterns

When integrating the framework, use these patterns for error handling:

```python
# Pattern 1: Wrap the entire call
try:
    reading = MasterOrchestrator.generate_reading(
        full_name=name,
        birth_day=day, birth_month=month, birth_year=year,
        current_date=current_date,
        # ... other params
    )
except ValueError as e:
    # Invalid date, hour, minute, second, or timezone
    return f"Could not generate reading: {e}"

# Pattern 2: Validate before calling
from core.julian_date_engine import JulianDateEngine

if not JulianDateEngine.is_valid_date(year, month, day):
    return "The date provided is not valid. Please check the day, month, and year."

if not (0 <= hour <= 23):
    return "Hour must be between 0 and 23."

if not full_name.strip():
    # Decide whether to proceed with empty name or request one
    pass

# Pattern 3: Check confidence after generating
reading = MasterOrchestrator.generate_reading(...)
if reading["confidence"]["score"] < 65:
    reading["_low_confidence_warning"] = (
        "This reading is based on limited data. "
        "Consider providing additional information for a more detailed analysis."
    )
```

---

## 16. Checklist for Edge Case Coverage

Before deploying an integration, verify that your application handles:

- [ ] Invalid dates (Feb 29 non-leap, day 31 on 30-day months, month out of range)
- [ ] Missing timezone (defaults to UTC, noted in output)
- [ ] Non-Latin names (ignored characters, transliteration recommendation)
- [ ] Special characters in names (hyphens, apostrophes, periods stripped)
- [ ] Empty name input (reduced reading with appropriate note)
- [ ] No time provided (date-only stamp, time sections omitted)
- [ ] Extreme coordinates (poles, date line, equator)
- [ ] Pre-1970 dates (negative Unix days, valid JDN)
- [ ] Conflicting timezone vs. location data (explicit wins)
- [ ] Low confidence score (add warning to output)
- [ ] All-zero numerology results from empty name (do not interpret as meaningful)
