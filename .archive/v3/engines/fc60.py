"""
FC60 Engine — FrankenChron-60 Calculation Alphabet Machine
===========================================================
Implements FC60 v2.0 specification:
  - Base-60 token encoding/decoding (12 Animals × 5 Elements)
  - Julian Day Number (Fliegel–Van Flandern)
  - Weekday calculation (JDN method)
  - Timezone encoding (TZ60)
  - Moon phase (synodic month)
  - Gānzhī 干支 sexagenary cycle (stems + branches)
  - Weighted checksum (Luhn-inspired)
  - Symbolic reading engine
  - Numerology integration (Pythagorean)

Zero external dependencies — pure Python stdlib.
"""

import math
import time
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Token Tables
# ════════════════════════════════════════════════════════════

ANIMALS = ["RA", "OX", "TI", "RU", "DR", "SN", "HO", "GO", "MO", "RO", "DO", "PI"]

ELEMENTS = ["WU", "FI", "ER", "MT", "WA"]

WEEKDAYS = ["SO", "LU", "MA", "ME", "JO", "VE", "SA"]

STEMS = ["JA", "YI", "BI", "DI", "WW", "JI", "GE", "XI", "RE", "GU"]

MOON_PHASES = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

SYNODIC_MONTH = 29.530588853
MOON_REF_JDN = 2451550.1  # Jan 6, 2000 18:14 UTC

# ── Animal metadata ──

ANIMAL_NAMES = [
    "Rat",
    "Ox",
    "Tiger",
    "Rabbit",
    "Dragon",
    "Snake",
    "Horse",
    "Goat",
    "Monkey",
    "Rooster",
    "Dog",
    "Pig",
]

ANIMAL_CHINESE = [
    "子 Zǐ",
    "丑 Chǒu",
    "寅 Yín",
    "卯 Mǎo",
    "辰 Chén",
    "巳 Sì",
    "午 Wǔ",
    "未 Wèi",
    "申 Shēn",
    "酉 Yǒu",
    "戌 Xū",
    "亥 Hài",
]

ANIMAL_POWER = [
    "Instinct",
    "Endurance",
    "Courage",
    "Intuition",
    "Destiny",
    "Wisdom",
    "Freedom",
    "Vision",
    "Adaptability",
    "Truth",
    "Loyalty",
    "Abundance",
]

ANIMAL_ESSENCE = [
    "Resourcefulness, new beginnings, sharp perception",
    "Patience, commitment, steady progress",
    "Power, bold action, leadership",
    "Diplomacy, gentle wisdom, sensitivity",
    "Transformation, ambition, greatness",
    "Shedding the old, precision, depth",
    "Movement, passionate energy, independence",
    "Creativity, harmony, artistic expression",
    "Cleverness, problem-solving, flexibility",
    "Confidence, discipline, honesty",
    "Protection, honest companionship, faithfulness",
    "Generosity, completion, prosperity",
]

# ── Element metadata ──

ELEMENT_NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]

ELEMENT_CHINESE = ["木 Mù", "火 Huǒ", "土 Tǔ", "金 Jīn", "水 Shuǐ"]

ELEMENT_FORCE = ["Growth", "Transformation", "Grounding", "Refinement", "Depth"]

ELEMENT_MEANING = [
    "New beginnings, flexibility, expansion",
    "Passion, illumination, change",
    "Stability, foundation, centering",
    "Precision, structure, cutting away excess",
    "Flow, emotion, hidden truths",
]

# ── Weekday metadata ──

WEEKDAY_NAMES = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]

WEEKDAY_PLANETS = [
    "Sun ☉",
    "Moon ☽",
    "Mars ♂",
    "Mercury ☿",
    "Jupiter ♃",
    "Venus ♀",
    "Saturn ♄",
]

WEEKDAY_DOMAINS = [
    "Identity, vitality, core self",
    "Emotions, intuition, inner world",
    "Drive, action, courage",
    "Communication, thought, connection",
    "Expansion, wisdom, abundance",
    "Love, values, beauty",
    "Discipline, lessons, mastery",
]

# ── Stem metadata ──

STEM_NAMES = ["Jiǎ", "Yǐ", "Bǐng", "Dīng", "Wù", "Jǐ", "Gēng", "Xīn", "Rén", "Guǐ"]
STEM_CHINESE = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_ELEMENTS = [
    "Wood",
    "Wood",
    "Fire",
    "Fire",
    "Earth",
    "Earth",
    "Metal",
    "Metal",
    "Water",
    "Water",
]
STEM_POLARITY = [
    "Yang",
    "Yin",
    "Yang",
    "Yin",
    "Yang",
    "Yin",
    "Yang",
    "Yin",
    "Yang",
    "Yin",
]

# ── Moon phase metadata ──

MOON_PHASE_NAMES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]

MOON_PHASE_MEANINGS = [
    "New beginnings, planting seeds",
    "Setting intentions, building",
    "Challenges, decisions, action",
    "Refinement, patience, almost there",
    "Culmination, illumination, release",
    "Gratitude, sharing, distribution",
    "Letting go, forgiveness, release",
    "Rest, reflection, preparation",
]

MOON_PHASE_ENERGY = [
    "Seed",
    "Build",
    "Challenge",
    "Refine",
    "Culminate",
    "Share",
    "Release",
    "Rest",
]

MOON_PHASE_BEST_FOR = [
    "Setting intentions, starting projects",
    "Taking first steps, gathering resources",
    "Making decisions, overcoming obstacles",
    "Editing, perfecting, patience",
    "Celebrating, releasing, clarity",
    "Teaching, distributing, gratitude",
    "Letting go, forgiving, cleaning",
    "Reflection, preparation, dreaming",
]

# ── Moon phase boundaries (days from new moon) ──
MOON_BOUNDARIES = [1.85, 7.38, 11.07, 14.77, 16.61, 22.14, 25.83, 29.53]

# ── Month names ──
MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# ── Time-of-day context ──
TIME_CONTEXT = [
    (0, 5, "The hour of silence — deep night, when the subconscious surfaces"),
    (5, 8, "The early hours — raw potential, day not yet shaped"),
    (8, 12, "Morning engine — clarity peaks, resistance lowest"),
    (12, 15, "Midday checkpoint — momentum building or fading"),
    (15, 18, "Afternoon shift — results arriving, time to adjust"),
    (18, 21, "Evening transition — processing begins"),
    (21, 24, "Night hours — masks off, real questions surface"),
]


# ════════════════════════════════════════════════════════════
# Core Encoding / Decoding
# ════════════════════════════════════════════════════════════


def token60(n):
    """Encode integer 0–59 as 4-char token."""
    n = int(n) % 60
    return ANIMALS[n // 5] + ELEMENTS[n % 5]


def digit60(tok):
    """Decode 4-char token to integer 0–59."""
    animal_tok = tok[:2].upper()
    element_tok = tok[2:4].upper()
    a_idx = ANIMALS.index(animal_tok)
    e_idx = ELEMENTS.index(element_tok)
    return a_idx * 5 + e_idx


def to_base60(n):
    """Convert non-negative integer to list of base-60 digits (most significant first)."""
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
    """Encode integer as hyphen-separated FC60 token string."""
    if n < 0:
        return "NEG-" + encode_base60(-n)
    return "-".join(token60(d) for d in to_base60(n))


def decode_base60(s):
    """Decode hyphen-separated FC60 token string to integer."""
    negative = False
    if s.startswith("NEG-"):
        negative = True
        s = s[4:]
    tokens = s.split("-")
    digits = [digit60(t) for t in tokens]
    result = from_base60(digits)
    return -result if negative else result


# ════════════════════════════════════════════════════════════
# Calendar Algorithms
# ════════════════════════════════════════════════════════════


def compute_jdn(y, m, d):
    """Gregorian date → Julian Day Number (Fliegel–Van Flandern)."""
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + (153 * m2 + 2) // 5 + 365 * y2 + y2 // 4 - y2 // 100 + y2 // 400 - 32045


def jdn_to_gregorian(jdn):
    """Julian Day Number → Gregorian (year, month, day)."""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


def weekday_from_jdn(jdn):
    """JDN → weekday index (0=Sunday, 1=Monday, ... 6=Saturday)."""
    return (jdn + 1) % 7


def weekday_token(jdn):
    """JDN → FC60 weekday token."""
    return WEEKDAYS[weekday_from_jdn(jdn)]


# ════════════════════════════════════════════════════════════
# Timezone Encoding
# ════════════════════════════════════════════════════════════


def encode_tz(tz_hours, tz_minutes=0):
    """Encode timezone offset as TZ60 token."""
    if tz_hours == 0 and tz_minutes == 0:
        return "Z"
    sign = "+" if tz_hours >= 0 else "-"
    return f"{sign}{token60(abs(tz_hours))}-{token60(abs(tz_minutes))}"


# ════════════════════════════════════════════════════════════
# Moon Phase
# ════════════════════════════════════════════════════════════


def moon_phase(jdn):
    """Calculate moon age (days) and phase index."""
    age = (jdn - MOON_REF_JDN) % SYNODIC_MONTH
    phase_idx = 7  # default: waning crescent
    for i, boundary in enumerate(MOON_BOUNDARIES):
        if age < boundary:
            phase_idx = i
            break
    return phase_idx, age


def moon_illumination(age):
    """Approximate illumination percentage from moon age."""
    return 50.0 * (1.0 - math.cos(2.0 * math.pi * age / SYNODIC_MONTH))


# ════════════════════════════════════════════════════════════
# Gānzhī 干支 Sexagenary Cycle
# ════════════════════════════════════════════════════════════


def ganzhi_year(year):
    """Year → (stem_index, branch_index)."""
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    return stem_idx, branch_idx


def ganzhi_year_tokens(year):
    """Year → (stem_token, branch_token)."""
    s, b = ganzhi_year(year)
    return STEMS[s], ANIMALS[b]


def ganzhi_year_name(year):
    """Year → human-readable name like '丙午 Fire Horse'."""
    s, b = ganzhi_year(year)
    return f"{STEM_CHINESE[s]}{ANIMAL_CHINESE[b].split()[0]} {STEM_ELEMENTS[s]} {ANIMAL_NAMES[b]}"


def ganzhi_day(jdn):
    """JDN → (stem_index, branch_index) for the day."""
    gz_idx = (jdn + 49) % 60
    return gz_idx % 10, gz_idx % 12


def ganzhi_hour(hour, day_stem):
    """Hour + day stem → (stem_index, branch_index) for the hour."""
    hour_branch = ((hour + 1) // 2) % 12
    hour_stem = (day_stem * 2 + hour_branch) % 10
    return hour_stem, hour_branch


# ════════════════════════════════════════════════════════════
# Weighted Checksum
# ════════════════════════════════════════════════════════════


def weighted_check(y, m, d, hh=0, mm=0, ss=0, jdn=None):
    """Compute weighted check value (mod 60) → TOKEN60."""
    if jdn is None:
        jdn = compute_jdn(y, m, d)
    chk = (
        1 * (y % 60) + 2 * m + 3 * d + 4 * hh + 5 * mm + 6 * ss + 7 * (jdn % 60)
    ) % 60
    return token60(chk)


def weighted_check_date_only(y, m, d, jdn=None):
    """Compute date-only check value."""
    if jdn is None:
        jdn = compute_jdn(y, m, d)
    chk = (1 * (y % 60) + 2 * m + 3 * d + 7 * (jdn % 60)) % 60
    return token60(chk)


# ════════════════════════════════════════════════════════════
# Full FC60 Encoder
# ════════════════════════════════════════════════════════════


def encode_fc60(
    year,
    month,
    day,
    hour=0,
    minute=0,
    second=0,
    tz_hours=0,
    tz_minutes=0,
    include_time=True,
):
    """
    Full FC60 encoding → dict with all 12 output fields.
    """
    jdn = compute_jdn(year, month, day)
    wd_idx = weekday_from_jdn(jdn)

    # ── FC60 stamp ──
    date_stamp = f"{WEEKDAYS[wd_idx]}-{ANIMALS[month - 1]}-{token60(day)}"
    if include_time:
        half = "☀" if hour < 12 else "🌙"
        time_stamp = f"{half}{ANIMALS[hour % 12]}-{token60(minute)}-{token60(second)}"
        stamp = f"{date_stamp} {time_stamp}"
    else:
        stamp = date_stamp

    # ── ISO-8601 ──
    if include_time:
        tz_sign = "+" if tz_hours >= 0 else "-"
        iso = (
            f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
            f"{tz_sign}{abs(tz_hours):02d}:{abs(tz_minutes):02d}"
        )
    else:
        iso = f"{year:04d}-{month:02d}-{day:02d}"

    # ── TZ60 ──
    tz60 = encode_tz(tz_hours, tz_minutes)

    # ── Y60 (absolute year in base-60) ──
    y60 = encode_base60(year)

    # ── Y2K (60-year cycle) ──
    y2k = token60((year - 2000) % 60)

    # ── J60 (Julian Day in base-60) ──
    j60 = encode_base60(jdn)

    # ── MJD ──
    mjd_val = jdn - 2400001
    mjd60 = encode_base60(mjd_val)

    # ── Rata Die ──
    rd_val = jdn - 1721425
    rd60 = encode_base60(rd_val)

    # ── Unix seconds ──
    if include_time:
        unix_val = (
            (jdn - 2440588) * 86400
            + hour * 3600
            + minute * 60
            + second
            - tz_hours * 3600
            - tz_minutes * 60
        )
    else:
        unix_val = (jdn - 2440588) * 86400
    u60 = encode_base60(unix_val) if unix_val >= 0 else encode_base60(unix_val)

    # ── Moon ──
    phase_idx, moon_age = moon_phase(jdn)
    illum = moon_illumination(moon_age)

    # ── Gānzhī ──
    gz_stem, gz_branch = ganzhi_year_tokens(year)
    gz_name = ganzhi_year_name(year)

    # ── Checksum ──
    if include_time:
        chk = weighted_check(year, month, day, hour, minute, second, jdn)
    else:
        chk = weighted_check_date_only(year, month, day, jdn)

    return {
        "stamp": stamp,
        "iso": iso,
        "tz60": tz60,
        "y60": y60,
        "y2k": y2k,
        "j60": j60,
        "jdn": jdn,
        "mjd60": mjd60,
        "rd60": rd60,
        "u60": u60,
        "unix": unix_val,
        "moon_phase_idx": phase_idx,
        "moon_phase": MOON_PHASES[phase_idx],
        "moon_name": MOON_PHASE_NAMES[phase_idx],
        "moon_age": moon_age,
        "moon_illumination": illum,
        "moon_meaning": MOON_PHASE_MEANINGS[phase_idx],
        "gz_token": f"{gz_stem}-{gz_branch}",
        "gz_name": gz_name,
        "chk": chk,
        "weekday_idx": wd_idx,
        "weekday_name": WEEKDAY_NAMES[wd_idx],
        "weekday_planet": WEEKDAY_PLANETS[wd_idx],
        "weekday_domain": WEEKDAY_DOMAINS[wd_idx],
    }


def format_full_output(result):
    """Format the full 12-line output from encode_fc60 result."""
    lines = [
        f"FC60:  {result['stamp']}",
        f"ISO:   {result['iso']}",
        f"TZ60:  {result['tz60']}",
        f"Y60:   {result['y60']}",
        f"Y2K:   {result['y2k']}",
        f"J:     {result['j60']}",
        f"MJD:   {result['mjd60']}",
        f"RD:    {result['rd60']}",
        f"U:     {result['u60']}",
        f"MOON:  {result['moon_phase']} {result['moon_name']}  age={result['moon_age']:.2f}d  illum={result['moon_illumination']:.0f}%",
        f"GZ:    {result['gz_token']} ({result['gz_name']})",
        f"CHK:   {result['chk']}",
    ]
    return "\n".join(lines)


def format_compact_output(result):
    """Format compact one-line output."""
    return (
        f"FC60={result['stamp']} | ISO={result['iso']} | TZ60={result['tz60']} | "
        f"Y60={result['y60']} | J={result['j60']} | "
        f"MOON={result['moon_phase']} | GZ={result['gz_token']} | CHK={result['chk']}"
    )


# ════════════════════════════════════════════════════════════
# Symbolic Reading Engine
# ════════════════════════════════════════════════════════════


def get_time_context(hour):
    """Get symbolic meaning for the current hour."""
    for start, end, desc in TIME_CONTEXT:
        if start <= hour < end:
            return desc
    return TIME_CONTEXT[-1][2]


def detect_animal_repetitions(month, day, hour, minute, year):
    """
    Detect repeated animals across all time components.
    Returns list of (animal_token, count, positions).
    """
    components = {
        "month": ANIMALS[month - 1],
        "day": ANIMALS[(day) // 5] if day < 60 else ANIMALS[0],
        "hour": ANIMALS[hour % 12],
        "minute": ANIMALS[minute // 5] if minute < 60 else ANIMALS[0],
        "year_branch": ANIMALS[(year - 4) % 12],
    }

    # Count occurrences
    counts = {}
    for pos, animal in components.items():
        if animal not in counts:
            counts[animal] = []
        counts[animal].append(pos)

    repeated = [
        (animal, len(positions), positions)
        for animal, positions in counts.items()
        if len(positions) >= 2
    ]
    repeated.sort(key=lambda x: x[1], reverse=True)
    return repeated, components


def generate_symbolic_reading(year, month, day, hour=0, minute=0, second=0):
    """
    Generate a full symbolic reading from FC60 components.
    Returns a multi-line string.
    """
    jdn = compute_jdn(year, month, day)
    wd_idx = weekday_from_jdn(jdn)
    phase_idx, moon_age = moon_phase(jdn)
    repeated, components = detect_animal_repetitions(month, day, hour, minute, year)

    lines = []

    # ── Time context ──
    time_ctx = get_time_context(hour)
    planet = WEEKDAY_PLANETS[wd_idx].split()[0]
    hour_animal_idx = hour % 12
    lines.append(
        f"At {hour:02d}:{minute:02d} on this {planet} day ({WEEKDAY_DOMAINS[wd_idx]}), "
        f"the {ANIMAL_NAMES[hour_animal_idx]} hour carries the energy of {ANIMAL_POWER[hour_animal_idx]}."
    )
    lines.append(f"  {time_ctx}")
    lines.append("")

    # ── Sun/Moon paradox ──
    half = "☀" if hour < 12 else "🌙"
    if half == "☀" and (hour < 6 or hour >= 21):
        lines.append(
            "☀🌙 Sun/Moon paradox: You're in the Sun half, but sitting in darkness. "
            "You carry light that hasn't been made visible yet."
        )
        lines.append("")

    # ── Repeated animals ──
    if repeated:
        for animal_tok, count, positions in repeated:
            a_idx = ANIMALS.index(animal_tok)
            pos_str = ", ".join(positions)
            if count >= 3:
                lines.append(
                    f"⚡ The {ANIMAL_NAMES[a_idx]} ({animal_tok}) appears {count} times — "
                    f"in the {pos_str}. This is not background noise; this is the main message."
                )
            else:
                lines.append(
                    f"🔁 The {ANIMAL_NAMES[a_idx]} ({animal_tok}) appears {count} times — "
                    f"in the {pos_str}. Doubled signal — emphasized quality."
                )
            lines.append(f"   Power: {ANIMAL_POWER[a_idx]} — {ANIMAL_ESSENCE[a_idx]}")
            lines.append("")

    # ── Day animal + element ──
    day_token = token60(day)
    day_animal_idx = day // 5 if day < 60 else 0
    day_element_idx = day % 5
    lines.append(
        f"Today's core energy: {ANIMAL_NAMES[day_animal_idx]} + {ELEMENT_NAMES[day_element_idx]} "
        f"({day_token})"
    )
    lines.append(f"  {ANIMAL_ESSENCE[day_animal_idx]}")
    lines.append(
        f"  Element force: {ELEMENT_FORCE[day_element_idx]} — {ELEMENT_MEANING[day_element_idx]}"
    )
    lines.append("")

    # ── Moon phase ──
    lines.append(
        f"Moon: {MOON_PHASES[phase_idx]} {MOON_PHASE_NAMES[phase_idx]} "
        f"(age {moon_age:.1f}d, {moon_illumination(moon_age):.0f}% illuminated)"
    )
    lines.append(
        f"  Energy: {MOON_PHASE_ENERGY[phase_idx]} — {MOON_PHASE_MEANINGS[phase_idx]}"
    )
    lines.append(f"  Best for: {MOON_PHASE_BEST_FOR[phase_idx]}")
    lines.append("")

    # ── Gānzhī year ──
    gz_name = ganzhi_year_name(year)
    s, b = ganzhi_year(year)
    lines.append(f"Year cycle: {gz_name} ({STEMS[s]}-{ANIMALS[b]})")
    lines.append(f"  Element: {STEM_ELEMENTS[s]} ({STEM_POLARITY[s]})")
    lines.append("")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# Input Parser
# ════════════════════════════════════════════════════════════


def parse_input(text, tz_hours=0, tz_minutes=0):
    """
    Parse various input formats and return FC60 result dict.
    Supports: ISO datetime, date, time, Unix timestamp, integer, 'now'.
    """
    text = text.strip()

    # ── "now" / "today" ──
    if text.lower() in ("now", "today"):
        now = datetime.now(timezone(timedelta(hours=tz_hours, minutes=tz_minutes)))
        return encode_fc60(
            now.year,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second,
            tz_hours,
            tz_minutes,
        )

    # ── ISO datetime: YYYY-MM-DDTHH:MM:SS ──
    if "T" in text or ("t" in text and "-" in text):
        text = text.replace("t", "T")
        # Strip timezone suffix for parsing
        tz_part = None
        if text.endswith("Z"):
            tz_part = (0, 0)
            text = text[:-1]
        elif "+" in text[10:]:
            idx = text.index("+", 10)
            tz_str = text[idx + 1 :]
            parts = tz_str.split(":")
            tz_part = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
            text = text[:idx]
        elif text.count("-") > 2:
            # Negative timezone
            idx = text.rindex("-")
            if idx > 10:
                tz_str = text[idx + 1 :]
                parts = tz_str.split(":")
                tz_part = (-int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                text = text[:idx]

        date_part, time_part = text.split("T")
        ymd = date_part.split("-")
        hms = time_part.split(":")

        y, m, d = int(ymd[0]), int(ymd[1]), int(ymd[2])
        hh = int(hms[0])
        mm = int(hms[1]) if len(hms) > 1 else 0
        ss = int(hms[2].split(".")[0]) if len(hms) > 2 else 0

        if tz_part:
            tz_hours, tz_minutes = tz_part

        return encode_fc60(y, m, d, hh, mm, ss, tz_hours, tz_minutes)

    # ── ISO date: YYYY-MM-DD ──
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        parts = text.split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
        return encode_fc60(y, m, d, include_time=False)

    # ── Compact date: YYYYMMDD ──
    if len(text) == 8 and text.isdigit():
        y = int(text[:4])
        m = int(text[4:6])
        d = int(text[6:8])
        return encode_fc60(y, m, d, include_time=False)

    # ── Time only: HH:MM or HH:MM:SS ──
    if ":" in text and len(text) <= 8:
        now = datetime.now(timezone(timedelta(hours=tz_hours, minutes=tz_minutes)))
        parts = text.split(":")
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
        ss = int(parts[2]) if len(parts) > 2 else 0
        return encode_fc60(
            now.year, now.month, now.day, hh, mm, ss, tz_hours, tz_minutes
        )

    # ── Unix timestamp (10 digits) ──
    if text.isdigit() and len(text) == 10:
        ts = int(text)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return encode_fc60(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0
        )

    # ── Unix milliseconds (13 digits) ──
    if text.isdigit() and len(text) == 13:
        ts = int(text) / 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return encode_fc60(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0
        )

    # ── Raw integer ──
    if text.lstrip("-").isdigit():
        n = int(text)
        return {
            "raw_integer": n,
            "base60": encode_base60(n),
            "token60": token60(n % 60) if n >= 0 else None,
        }

    # ── FC60 token decode attempt ──
    try:
        val = decode_base60(text)
        return {"decoded_integer": val, "base60": text}
    except (ValueError, IndexError):
        pass

    return {"error": f"Could not parse input: {text}"}


# ════════════════════════════════════════════════════════════
# Self-Test
# ════════════════════════════════════════════════════════════


def self_test():
    """
    Verify FC60 engine against known test vectors from the spec.
    Returns list of (test_name, passed, detail).
    """
    results = []

    # Test 1: TOKEN60 encode/decode round-trip
    all_ok = True
    for i in range(60):
        tok = token60(i)
        decoded = digit60(tok)
        if decoded != i:
            all_ok = False
            break
    results.append(
        (
            "TOKEN60 round-trip (0–59)",
            all_ok,
            "All 60 tokens encode/decode correctly" if all_ok else f"Failed at {i}",
        )
    )

    # Test 2: JDN test vectors (spec had error for 2026-02-06: 2461072 → correct is 2461078)
    jdn_tests = [
        (2000, 1, 1, 2451545),
        (2026, 2, 6, 2461078),
        (1970, 1, 1, 2440588),
    ]
    for y, m, d, expected in jdn_tests:
        got = compute_jdn(y, m, d)
        ok = got == expected
        results.append(
            (f"JDN {y}-{m:02d}-{d:02d}", ok, f"Expected {expected}, got {got}")
        )

    # Test 3: JDN inverse round-trip
    for y, m, d, jdn_val in jdn_tests:
        ry, rm, rd = jdn_to_gregorian(jdn_val)
        ok = ry == y and rm == m and rd == d
        results.append(
            (
                f"JDN→Gregorian {jdn_val}",
                ok,
                f"Expected {y}-{m:02d}-{d:02d}, got {ry}-{rm:02d}-{rd:02d}",
            )
        )

    # Test 4: Weekday test vectors
    wd_tests = [
        (2000, 1, 1, "SA"),  # Saturday
        (2026, 2, 6, "VE"),  # Friday
        (2026, 4, 22, "ME"),  # Wednesday
        (1999, 4, 22, "JO"),  # Thursday
    ]
    for y, m, d, expected_tok in wd_tests:
        jdn_val = compute_jdn(y, m, d)
        got = weekday_token(jdn_val)
        ok = got == expected_tok
        results.append(
            (f"Weekday {y}-{m:02d}-{d:02d}", ok, f"Expected {expected_tok}, got {got}")
        )

    # Test 5: Base-60 round-trip
    test_nums = [0, 1, 59, 60, 3600, 2461072, 999999]
    for n in test_nums:
        encoded = encode_base60(n)
        decoded = decode_base60(encoded)
        ok = decoded == n
        results.append(
            (f"Base60 round-trip {n}", ok, f"Encoded: {encoded}, decoded: {decoded}")
        )

    # Test 6: J60 test vectors (corrected from spec errors)
    j60_tests = [
        (2451545, "TIFI-DRWU-PIWA-OXWU"),
        (2461078, "TIFI-DRMT-GOER-PIMT"),
        (2440588, "TIFI-RUER-PIFI-SNMT"),
    ]
    for jdn_val, expected in j60_tests:
        got = encode_base60(jdn_val)
        ok = got == expected
        results.append((f"J60 {jdn_val}", ok, f"Expected {expected}, got {got}"))

    # Test 7: Gānzhī test vectors
    gz_tests = [
        (2024, "JA", "DR"),  # Wood Dragon
        (2025, "YI", "SN"),  # Wood Snake
        (2026, "BI", "HO"),  # Fire Horse
    ]
    for y, exp_stem, exp_branch in gz_tests:
        stem, branch = ganzhi_year_tokens(y)
        ok = stem == exp_stem and branch == exp_branch
        results.append(
            (
                f"Gānzhī {y}",
                ok,
                f"Expected {exp_stem}-{exp_branch}, got {stem}-{branch}",
            )
        )

    # Test 8: Specific TOKEN60 examples from spec
    tok_tests = [
        (0, "RAWU"),
        (26, "SNFI"),
        (57, "PIER"),
        (59, "PIWA"),
    ]
    for n, expected in tok_tests:
        got = token60(n)
        ok = got == expected
        results.append((f"TOKEN60({n})", ok, f"Expected {expected}, got {got}"))

    # Test 9: Full encode 2026-02-06
    result = encode_fc60(2026, 2, 6, 1, 15, 0, 8, 0)
    ok = result["stamp"] == "VE-OX-OXFI ☀OX-RUWU-RAWU"
    results.append(
        ("Full encode 2026-02-06 01:15:00+08:00", ok, f"Got: {result['stamp']}")
    )

    return results
