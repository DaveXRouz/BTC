"""
Oracle Engine — Multi-System Sign Reader
=========================================
Combines numerology, FC60, Chaldean, Western zodiac, Chinese hour/year,
moon phase, angel numbers, mirror numbers, and synchronicity detection
into a unified "sign reading" engine.

Zero external dependencies — pure Python stdlib.
"""

import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Lazy imports from sibling engines (graceful degradation)
# ════════════════════════════════════════════════════════════

_fc60_available = False
_numerology_available = False

try:
    from engines.fc60 import (
        token60,
        encode_base60,
        ANIMALS,
        ELEMENTS,
        STEMS,
        compute_jdn,
        moon_phase,
        moon_illumination,
        MOON_PHASE_NAMES,
        MOON_PHASE_MEANINGS,
        encode_fc60,
        ganzhi_year,
        ganzhi_year_name,
        ganzhi_hour,
        ANIMAL_NAMES,
        STEM_NAMES,
        STEM_CHINESE,
        STEM_ELEMENTS,
        STEM_POLARITY,
    )

    _fc60_available = True
except ImportError:
    logger.warning("engines.fc60 not available — FC60/moon/ganzhi features disabled")

try:
    from engines.numerology import (
        numerology_reduce,
        digit_sum,
        is_master_number,
        name_to_number,
        name_soul_urge,
        name_personality,
        life_path,
        LIFE_PATH_MEANINGS,
    )

    _numerology_available = True
except ImportError:
    logger.warning("engines.numerology not available — numerology features disabled")


# ════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════

ANGEL_NUMBERS = {
    111: "New beginnings, manifestation",
    222: "Balance, partnership, trust the process",
    333: "Ascended masters, creativity, growth",
    444: "Angels present, foundation, protection",
    555: "Major change coming, transformation",
    666: "Rebalance material/spiritual, self-reflection",
    777: "Divine luck, spiritual awakening",
    888: "Abundance, financial flow, infinity",
    999: "Completion, ending of a cycle",
    1111: "Gateway, make a wish, alignment",
    1212: "Stepping into your power",
    1234: "Simplify, step by step progress",
}

MIRROR_NUMBERS = {
    "01:10": "Return to origin",
    "02:20": "Patience and diplomacy",
    "03:30": "Creative expression",
    "04:40": "Foundation building",
    "05:50": "Freedom and change",
    "10:01": "New cycle beginning",
    "12:21": "Balance of giving and receiving",
    "13:31": "Creative transformation",
    "14:41": "Stable change",
    "15:51": "Adventurous foundation",
    "20:02": "Partnership reflections",
    "21:12": "Leadership in harmony",
    "23:32": "Expressive stability",
}

CHALDEAN_VALUES = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 8,
    "G": 3,
    "H": 5,
    "I": 1,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "O": 7,
    "P": 8,
    "Q": 1,
    "R": 2,
    "S": 3,
    "T": 4,
    "U": 6,
    "V": 6,
    "W": 6,
    "X": 5,
    "Y": 1,
    "Z": 7,
}

ZODIAC_SIGNS = [
    # (month, day_start, name, element, quality, ruler)
    (1, 20, "Aquarius", "Air", "Fixed", "Uranus"),
    (2, 19, "Pisces", "Water", "Mutable", "Neptune"),
    (3, 21, "Aries", "Fire", "Cardinal", "Mars"),
    (4, 20, "Taurus", "Earth", "Fixed", "Venus"),
    (5, 21, "Gemini", "Air", "Mutable", "Mercury"),
    (6, 21, "Cancer", "Water", "Cardinal", "Moon"),
    (7, 23, "Leo", "Fire", "Fixed", "Sun"),
    (8, 23, "Virgo", "Earth", "Mutable", "Mercury"),
    (9, 23, "Libra", "Air", "Cardinal", "Venus"),
    (10, 23, "Scorpio", "Water", "Fixed", "Pluto"),
    (11, 22, "Sagittarius", "Fire", "Mutable", "Jupiter"),
    (12, 22, "Capricorn", "Earth", "Cardinal", "Saturn"),
]

CHINESE_HOURS = [
    (23, 1, "Rat", "Zi"),
    (1, 3, "Ox", "Chou"),
    (3, 5, "Tiger", "Yin"),
    (5, 7, "Rabbit", "Mao"),
    (7, 9, "Dragon", "Chen"),
    (9, 11, "Snake", "Si"),
    (11, 13, "Horse", "Wu"),
    (13, 15, "Goat", "Wei"),
    (15, 17, "Monkey", "Shen"),
    (17, 19, "Rooster", "You"),
    (19, 21, "Dog", "Xu"),
    (21, 23, "Pig", "Hai"),
]

NUMBER_MEANINGS = {
    1: "Independence, leadership, new beginnings, self-reliance",
    2: "Partnership, balance, diplomacy, sensitivity",
    3: "Creativity, expression, joy, communication",
    4: "Stability, structure, hard work, foundation",
    5: "Freedom, change, adventure, versatility",
    6: "Harmony, nurturing, responsibility, love",
    7: "Spirituality, introspection, wisdom, analysis",
    8: "Power, abundance, achievement, material mastery",
    9: "Completion, humanitarianism, wisdom, letting go",
    11: "Intuition, spiritual insight, illumination (Master Number)",
    22: "Master builder, large-scale vision, practical idealism (Master Number)",
    33: "Master teacher, compassion, healing, selfless service (Master Number)",
}


# ════════════════════════════════════════════════════════════
# Internal Helpers
# ════════════════════════════════════════════════════════════


def _extract_numbers(text):
    """
    Extract all integers from text via regex.

    Parameters
    ----------
    text : str
        Any text that may contain numbers.

    Returns
    -------
    list[int]
        All integers found in the text, in order of appearance.
    """
    if not text:
        return []
    try:
        return [int(m) for m in re.findall(r"\d+", str(text))]
    except (TypeError, ValueError):
        return []


def _chaldean_reduce(name):
    """
    Chaldean numerology reduction.

    Sums the Chaldean letter values for all alphabetic characters in the
    name, then reduces to a single digit while preserving master numbers
    (11, 22, 33).

    Parameters
    ----------
    name : str
        Name or word to reduce.

    Returns
    -------
    int
        Chaldean-reduced number.
    """
    if not name:
        return 0
    total = 0
    for ch in name.upper():
        if ch in CHALDEAN_VALUES:
            total += CHALDEAN_VALUES[ch]
    # Reduce preserving master numbers
    if total in (11, 22, 33):
        return total
    while total > 9:
        total = sum(int(d) for d in str(total))
        if total in (11, 22, 33):
            return total
    return total


def _parse_date(date_str):
    """
    Parse a YYYY-MM-DD date string.

    Parameters
    ----------
    date_str : str or None
        Date in YYYY-MM-DD format.

    Returns
    -------
    tuple(int, int, int) or None
        (year, month, day) or None on failure.
    """
    if not date_str:
        return None
    try:
        parts = str(date_str).strip().split("-")
        if len(parts) != 3:
            return None
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
        # Basic validation
        if not (1 <= month <= 12 and 1 <= day <= 31 and year > 0):
            return None
        return (year, month, day)
    except (ValueError, TypeError, AttributeError):
        return None


def _parse_time(time_str):
    """
    Parse an HH:MM time string.

    Parameters
    ----------
    time_str : str or None
        Time in HH:MM format.

    Returns
    -------
    tuple(int, int) or None
        (hour, minute) or None on failure.
    """
    if not time_str:
        return None
    try:
        parts = str(time_str).strip().split(":")
        if len(parts) < 2:
            return None
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return (hour, minute)
    except (ValueError, TypeError, AttributeError):
        return None


def _get_zodiac(month, day):
    """
    Determine Western zodiac sign from month and day.

    Parameters
    ----------
    month : int
        Month (1-12).
    day : int
        Day of month (1-31).

    Returns
    -------
    dict
        Keys: sign, element, quality, ruling_planet.
    """
    try:
        month = int(month)
        day = int(day)
    except (TypeError, ValueError):
        return {
            "sign": "Unknown",
            "element": "Unknown",
            "quality": "Unknown",
            "ruling_planet": "Unknown",
        }

    # ZODIAC_SIGNS entries define the START of the NEXT sign.
    # E.g., (1, 20, "Aquarius", ...) means Aquarius starts on Jan 20.
    # So if month=1, day<20 -> previous sign (Capricorn).
    # Walk through the list; the last sign whose start we have NOT yet
    # passed is the current sign.

    # Build a flat lookup: for each (month, day_start), the sign starting
    # at that date. We need to find which range we fall into.
    for i, (m_start, d_start, name, element, quality, ruler) in enumerate(ZODIAC_SIGNS):
        # Determine the end of this sign's range
        next_i = (i + 1) % len(ZODIAC_SIGNS)
        m_end = ZODIAC_SIGNS[next_i][0]
        d_end = ZODIAC_SIGNS[next_i][1]

        # Check if (month, day) falls in the range from (m_start, d_start)
        # to (m_end, d_end - 1). Handle year wrap (Capricorn: Dec 22 - Jan 19).
        date_val = month * 100 + day
        start_val = m_start * 100 + d_start
        end_val = m_end * 100 + d_end

        if start_val <= end_val:
            # Normal range (no year wrap)
            if start_val <= date_val < end_val:
                return {
                    "sign": name,
                    "element": element,
                    "quality": quality,
                    "ruling_planet": ruler,
                }
        else:
            # Year wrap (e.g., Capricorn: 1222 to 120)
            if date_val >= start_val or date_val < end_val:
                return {
                    "sign": name,
                    "element": element,
                    "quality": quality,
                    "ruling_planet": ruler,
                }

    # Fallback (should not reach here with valid input)
    return {
        "sign": "Capricorn",
        "element": "Earth",
        "quality": "Cardinal",
        "ruling_planet": "Saturn",
    }


def _pythagorean_meaning(n):
    """
    Return the Pythagorean numerology meaning for a reduced number.

    Parameters
    ----------
    n : int
        Reduced number (1-9, 11, 22, or 33).

    Returns
    -------
    str
        Meaning string.
    """
    return NUMBER_MEANINGS.get(n, f"Number {n} — explore its unique vibration")


def _get_chinese_hour(hour):
    """
    Determine the Chinese double-hour animal and branch name.

    Parameters
    ----------
    hour : int
        Hour (0-23).

    Returns
    -------
    dict
        Keys: animal, branch, start, end.
    """
    try:
        hour = int(hour) % 24
    except (TypeError, ValueError):
        return {"animal": "Unknown", "branch": "Unknown", "start": 0, "end": 0}

    for start, end, animal, branch in CHINESE_HOURS:
        if start > end:
            # Wraps midnight (23-1 for Rat)
            if hour >= start or hour < end:
                return {"animal": animal, "branch": branch, "start": start, "end": end}
        else:
            if start <= hour < end:
                return {"animal": animal, "branch": branch, "start": start, "end": end}

    # Fallback
    return {"animal": "Rat", "branch": "Zi", "start": 23, "end": 1}


def _check_synchronicity(numbers):
    """
    Check for meaningful number patterns: angel numbers, mirror numbers,
    repeating digits, and sequential patterns.

    Parameters
    ----------
    numbers : list[int]
        Numbers to analyze.

    Returns
    -------
    list[str]
        Description strings for each synchronicity found.
    """
    if not numbers:
        return []

    syncs = []

    for n in numbers:
        # Angel numbers
        if n in ANGEL_NUMBERS:
            syncs.append(f"Angel number {n}: {ANGEL_NUMBERS[n]}")

        # Check if the number as a time string is a mirror number
        # e.g., 1221 -> "12:21"
        s = str(n)
        if len(s) == 4:
            time_fmt = f"{s[:2]}:{s[2:]}"
            if time_fmt in MIRROR_NUMBERS:
                syncs.append(f"Mirror number {time_fmt}: {MIRROR_NUMBERS[time_fmt]}")

        if len(s) == 3:
            time_fmt = f"0{s[0]}:{s[1:]}"
            if time_fmt in MIRROR_NUMBERS:
                syncs.append(f"Mirror number {time_fmt}: {MIRROR_NUMBERS[time_fmt]}")

        # Repeating digits (e.g., 11, 55, 7777)
        if len(s) >= 2 and len(set(s)) == 1:
            syncs.append(
                f"Repeating digit pattern {n}: "
                f"the digit {s[0]} repeated {len(s)} times "
                f"amplifies its energy"
            )

        # Palindrome check (for numbers with 3+ digits)
        if len(s) >= 3 and s == s[::-1]:
            syncs.append(
                f"Palindrome {n}: reflection pattern, what you send out returns"
            )

        # Sequential ascending (e.g., 123, 1234, 456)
        if len(s) >= 3:
            digits = [int(d) for d in s]
            is_ascending = all(
                digits[i + 1] - digits[i] == 1 for i in range(len(digits) - 1)
            )
            is_descending = all(
                digits[i] - digits[i + 1] == 1 for i in range(len(digits) - 1)
            )
            if is_ascending:
                syncs.append(
                    f"Ascending sequence {n}: forward momentum, step-by-step progress"
                )
            elif is_descending:
                syncs.append(
                    f"Descending sequence {n}: release, letting go, simplification"
                )

    # Check pairs across numbers
    if len(numbers) >= 2:
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                a, b = numbers[i], numbers[j]
                # Same number appearing twice
                if a == b:
                    syncs.append(
                        f"Repeated appearance of {a}: " f"this number demands attention"
                    )
                # Sum to significant number
                total = a + b
                if total in ANGEL_NUMBERS:
                    syncs.append(
                        f"{a} + {b} = {total} (angel number): "
                        f"{ANGEL_NUMBERS[total]}"
                    )
                # Complement pair (sum to 9)
                if _numerology_available:
                    ra = numerology_reduce(digit_sum(a))
                    rb = numerology_reduce(digit_sum(b))
                    if ra + rb == 9:
                        syncs.append(
                            f"{a} (reduces to {ra}) + {b} (reduces to {rb}) = 9: "
                            f"completion pair, karmic balance"
                        )

    return syncs


def _generate_interpretation(systems_results, synchronicities):
    """
    Combine all system results into a human-readable multi-line
    interpretation string.

    Parameters
    ----------
    systems_results : dict
        Dict of system name -> system result dict.
    synchronicities : list[str]
        Synchronicity description strings.

    Returns
    -------
    str
        Multi-line interpretation.
    """
    lines = []
    lines.append("=== ORACLE READING ===")
    lines.append("")

    # Numerology section
    num_data = systems_results.get("numerology")
    if num_data and num_data.get("numbers"):
        lines.append("-- Numerology --")
        for entry in num_data["numbers"]:
            n = entry.get("value", "?")
            reduced = entry.get("reduced", "?")
            meaning = entry.get("pythagorean_meaning", "")
            master_tag = " [MASTER NUMBER]" if entry.get("is_master") else ""
            lines.append(f"  {n} -> reduces to {reduced}{master_tag}")
            if meaning:
                lines.append(f"    Meaning: {meaning}")
        lines.append("")

    # Chaldean section
    chaldean_data = systems_results.get("chaldean")
    if chaldean_data and chaldean_data.get("value"):
        lines.append("-- Chaldean Numerology --")
        lines.append(f"  Text reduces to: {chaldean_data['value']}")
        meaning = chaldean_data.get("meaning", "")
        if meaning:
            lines.append(f"  Meaning: {meaning}")
        lines.append("")

    # Angel numbers section
    angel_data = systems_results.get("angel")
    if angel_data and angel_data.get("matches"):
        lines.append("-- Angel Numbers --")
        for match in angel_data["matches"]:
            lines.append(f"  {match['number']}: {match['meaning']}")
        lines.append("")

    # FC60 section
    fc60_data = systems_results.get("fc60")
    if fc60_data and fc60_data.get("stamp"):
        lines.append("-- FC60 Encoding --")
        lines.append(f"  Stamp: {fc60_data['stamp']}")
        if fc60_data.get("weekday_name"):
            lines.append(
                f"  Day: {fc60_data['weekday_name']} "
                f"({fc60_data.get('weekday_planet', '')})"
            )
            lines.append(f"  Domain: {fc60_data.get('weekday_domain', '')}")
        lines.append("")

    # Moon section
    moon_data = systems_results.get("moon")
    if moon_data and moon_data.get("phase_name"):
        lines.append("-- Moon Phase --")
        lines.append(
            f"  {moon_data.get('emoji', '')} {moon_data['phase_name']} "
            f"({moon_data.get('illumination', 0):.0f}% illuminated)"
        )
        if moon_data.get("meaning"):
            lines.append(f"  Energy: {moon_data['meaning']}")
        lines.append("")

    # Zodiac section
    zodiac_data = systems_results.get("zodiac")
    if zodiac_data and zodiac_data.get("sign") and zodiac_data["sign"] != "Unknown":
        lines.append("-- Western Zodiac --")
        lines.append(
            f"  {zodiac_data['sign']} "
            f"({zodiac_data.get('element', '')} / "
            f"{zodiac_data.get('quality', '')})"
        )
        lines.append(f"  Ruler: {zodiac_data.get('ruling_planet', '')}")
        lines.append("")

    # Ganzhi section
    ganzhi_data = systems_results.get("ganzhi")
    if ganzhi_data:
        lines.append("-- Chinese Cosmology --")
        if ganzhi_data.get("year_name"):
            lines.append(f"  Year: {ganzhi_data['year_name']}")
        if ganzhi_data.get("hour_animal"):
            lines.append(
                f"  Hour: {ganzhi_data['hour_animal']} "
                f"({ganzhi_data.get('hour_branch', '')})"
            )
        if ganzhi_data.get("stem_element"):
            lines.append(
                f"  Element: {ganzhi_data['stem_element']} "
                f"({ganzhi_data.get('stem_polarity', '')})"
            )
        lines.append("")

    # Synchronicities
    if synchronicities:
        lines.append("-- Synchronicities --")
        for sync in synchronicities:
            lines.append(f"  * {sync}")
        lines.append("")

    # Summary line
    system_count = sum(
        1
        for k, v in systems_results.items()
        if v and (isinstance(v, dict) and any(v.values()))
    )
    lines.append(
        f"Reading assembled from {system_count} system(s) "
        f"with {len(synchronicities)} synchronicit"
        f"{'y' if len(synchronicities) == 1 else 'ies'} detected."
    )

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# Numerology System Helpers
# ════════════════════════════════════════════════════════════


def _analyze_numbers_numerology(numbers):
    """
    Run Pythagorean numerology analysis on a list of numbers.

    Parameters
    ----------
    numbers : list[int]
        Numbers to analyze.

    Returns
    -------
    dict
        Keys: numbers (list of per-number analysis dicts).
    """
    if not _numerology_available or not numbers:
        return {"numbers": []}

    results = []
    for n in numbers:
        try:
            ds = digit_sum(n)
            reduced = numerology_reduce(ds)
            master = is_master_number(n)
            meaning = _pythagorean_meaning(reduced)
            results.append(
                {
                    "value": n,
                    "digit_sum": ds,
                    "reduced": reduced,
                    "is_master": master,
                    "pythagorean_meaning": meaning,
                }
            )
        except Exception as exc:
            logger.debug("Numerology analysis failed for %s: %s", n, exc)
            results.append({"value": n, "error": str(exc)})

    return {"numbers": results}


def _analyze_fc60(year, month, day, hour=0, minute=0):
    """
    Run FC60 encoding for a given date/time.

    Returns
    -------
    dict
        FC60 result or empty dict if unavailable.
    """
    if not _fc60_available:
        return {}
    try:
        include_time = hour != 0 or minute != 0
        result = encode_fc60(
            year, month, day, hour, minute, 0, 0, 0, include_time=include_time
        )
        return {
            "stamp": result.get("stamp", ""),
            "iso": result.get("iso", ""),
            "y60": result.get("y60", ""),
            "j60": result.get("j60", ""),
            "jdn": result.get("jdn", 0),
            "weekday_name": result.get("weekday_name", ""),
            "weekday_planet": result.get("weekday_planet", ""),
            "weekday_domain": result.get("weekday_domain", ""),
            "gz_name": result.get("gz_name", ""),
            "chk": result.get("chk", ""),
        }
    except Exception as exc:
        logger.debug("FC60 encoding failed: %s", exc)
        return {}


def _analyze_moon(year, month, day):
    """
    Get moon phase information for a given date.

    Returns
    -------
    dict
        Moon phase data or empty dict if unavailable.
    """
    if not _fc60_available:
        return {}
    try:
        jdn = compute_jdn(year, month, day)
        phase_idx, age = moon_phase(jdn)
        illum = moon_illumination(age)
        return {
            "phase_index": phase_idx,
            "phase_name": MOON_PHASE_NAMES[phase_idx],
            "emoji": ["New", "WxCr", "1stQ", "WxGb", "Full", "WnGb", "3rdQ", "WnCr"][
                phase_idx
            ],
            "age_days": round(age, 2),
            "illumination": round(illum, 1),
            "meaning": MOON_PHASE_MEANINGS[phase_idx],
        }
    except Exception as exc:
        logger.debug("Moon phase calculation failed: %s", exc)
        return {}


def _analyze_ganzhi(year, hour=None):
    """
    Get Chinese cosmology info: year animal/element and optional hour.

    Returns
    -------
    dict
        Ganzhi data or empty dict if unavailable.
    """
    if not _fc60_available:
        return {}
    try:
        stem_idx, branch_idx = ganzhi_year(year)
        result = {
            "year_name": ganzhi_year_name(year),
            "year_animal": ANIMAL_NAMES[branch_idx],
            "year_stem": STEM_NAMES[stem_idx],
            "year_stem_chinese": STEM_CHINESE[stem_idx],
            "stem_element": STEM_ELEMENTS[stem_idx],
            "stem_polarity": STEM_POLARITY[stem_idx],
        }

        if hour is not None:
            try:
                # Use the Chinese hour lookup
                ch = _get_chinese_hour(hour)
                result["hour_animal"] = ch["animal"]
                result["hour_branch"] = ch["branch"]

                # Also use the ganzhi_hour function from fc60 for
                # stem-level detail. We need the day stem; approximate
                # with 0 if we don't have the full day info.
                h_stem, h_branch = ganzhi_hour(hour, stem_idx)
                result["hour_stem"] = STEM_NAMES[h_stem]
                result["hour_stem_chinese"] = STEM_CHINESE[h_stem]
            except Exception as exc:
                logger.debug("Ganzhi hour calculation failed: %s", exc)

        return result
    except Exception as exc:
        logger.debug("Ganzhi year calculation failed: %s", exc)
        return {}


def _analyze_zodiac(month, day):
    """
    Get Western zodiac information for a date.

    Returns
    -------
    dict
        Zodiac data.
    """
    return _get_zodiac(month, day)


def _analyze_angel(numbers):
    """
    Check for angel number matches in a list of numbers.

    Returns
    -------
    dict
        Keys: matches (list of dicts with number, meaning).
    """
    matches = []
    for n in numbers:
        if n in ANGEL_NUMBERS:
            matches.append({"number": n, "meaning": ANGEL_NUMBERS[n]})
    return {"matches": matches}


def _analyze_chaldean(text):
    """
    Run Chaldean numerology on text containing letters.

    Returns
    -------
    dict
        Keys: value, meaning, letter_values. Empty dict if no letters.
    """
    if not text:
        return {}
    # Check if text has alphabetic characters
    alpha_chars = [ch for ch in str(text).upper() if ch.isalpha()]
    if not alpha_chars:
        return {}

    value = _chaldean_reduce(text)
    letter_breakdown = []
    for ch in str(text).upper():
        if ch in CHALDEAN_VALUES:
            letter_breakdown.append(f"{ch}={CHALDEAN_VALUES[ch]}")

    return {
        "value": value,
        "meaning": _pythagorean_meaning(value),
        "letter_values": ", ".join(letter_breakdown),
        "raw_sum": sum(CHALDEAN_VALUES.get(ch, 0) for ch in str(text).upper()),
    }


# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


def read_sign(sign, date=None, time_str=None, location=None, context=None):
    """
    Main entry point — multi-system sign reading.

    Analyzes a "sign" (any text, number, or symbol the user encountered)
    through multiple numerological and cosmological systems.

    Parameters
    ----------
    sign : str or int or float
        The sign to read. Can be a number, text, time, or any string.
    date : str or None
        Optional date in YYYY-MM-DD format.
    time_str : str or None
        Optional time in HH:MM format.
    location : str or None
        Optional location (stored in result, not yet used for calculation).
    context : str or None
        Optional context describing where/how the sign was seen.

    Returns
    -------
    dict
        Keys: sign, numbers, systems, interpretation, synchronicities,
        timestamp, location, context.
    """
    ts = time.time()
    sign_str = str(sign) if sign is not None else ""
    systems = {}

    # Extract numbers from the sign
    numbers = _extract_numbers(sign_str)

    # If the sign itself is a single number, ensure it's included
    try:
        sign_as_int = int(sign)
        if sign_as_int not in numbers:
            numbers.insert(0, sign_as_int)
    except (TypeError, ValueError):
        pass

    # If the sign looks like a time (HH:MM), combine digits as a number too
    if ":" in sign_str:
        combined_sign = sign_str.replace(":", "")
        try:
            combined_sign_int = int(combined_sign)
            if combined_sign_int not in numbers:
                numbers.append(combined_sign_int)
        except (ValueError, TypeError):
            pass

    # Parse date and time
    parsed_date = _parse_date(date)
    parsed_time = _parse_time(time_str)

    # Also extract numbers from the time string if given
    if time_str:
        time_numbers = _extract_numbers(time_str)
        for tn in time_numbers:
            if tn not in numbers:
                numbers.append(tn)
        # Check the full time as a combined number (e.g., "12:21" -> 1221)
        combined = time_str.replace(":", "")
        try:
            combined_int = int(combined)
            if combined_int not in numbers:
                numbers.append(combined_int)
        except (ValueError, TypeError):
            pass

    # --- System 1: Numerology ---
    try:
        systems["numerology"] = _analyze_numbers_numerology(numbers)
    except Exception as exc:
        logger.debug("Numerology system failed: %s", exc)
        systems["numerology"] = {"error": str(exc)}

    # --- System 2: FC60 ---
    if parsed_date:
        year, month, day = parsed_date
        hour = parsed_time[0] if parsed_time else 0
        minute = parsed_time[1] if parsed_time else 0
        try:
            systems["fc60"] = _analyze_fc60(year, month, day, hour, minute)
        except Exception as exc:
            logger.debug("FC60 system failed: %s", exc)
            systems["fc60"] = {"error": str(exc)}
    else:
        systems["fc60"] = {}

    # --- System 3: Moon ---
    if parsed_date:
        year, month, day = parsed_date
        try:
            systems["moon"] = _analyze_moon(year, month, day)
        except Exception as exc:
            logger.debug("Moon system failed: %s", exc)
            systems["moon"] = {"error": str(exc)}
    else:
        systems["moon"] = {}

    # --- System 4: Ganzhi ---
    if parsed_date:
        year = parsed_date[0]
        hour = parsed_time[0] if parsed_time else None
        try:
            systems["ganzhi"] = _analyze_ganzhi(year, hour)
        except Exception as exc:
            logger.debug("Ganzhi system failed: %s", exc)
            systems["ganzhi"] = {"error": str(exc)}
    else:
        systems["ganzhi"] = {}

    # --- System 5: Zodiac ---
    if parsed_date:
        _, month, day = parsed_date
        try:
            systems["zodiac"] = _analyze_zodiac(month, day)
        except Exception as exc:
            logger.debug("Zodiac system failed: %s", exc)
            systems["zodiac"] = {"error": str(exc)}
    else:
        systems["zodiac"] = {}

    # --- System 6: Angel numbers ---
    try:
        systems["angel"] = _analyze_angel(numbers)
    except Exception as exc:
        logger.debug("Angel number system failed: %s", exc)
        systems["angel"] = {"error": str(exc)}

    # --- System 7: Chaldean ---
    try:
        systems["chaldean"] = _analyze_chaldean(sign_str)
    except Exception as exc:
        logger.debug("Chaldean system failed: %s", exc)
        systems["chaldean"] = {"error": str(exc)}

    # --- Synchronicities ---
    try:
        synchronicities = _check_synchronicity(numbers)
        # Also check the time string directly against mirror numbers
        if time_str and time_str in MIRROR_NUMBERS:
            mirror_msg = f"Mirror time {time_str}: {MIRROR_NUMBERS[time_str]}"
            if mirror_msg not in synchronicities:
                synchronicities.append(mirror_msg)
    except Exception as exc:
        logger.debug("Synchronicity check failed: %s", exc)
        synchronicities = []

    # --- Interpretation ---
    try:
        interpretation = _generate_interpretation(systems, synchronicities)
    except Exception as exc:
        logger.debug("Interpretation generation failed: %s", exc)
        interpretation = f"Reading could not be fully assembled: {exc}"

    return {
        "sign": sign_str,
        "numbers": numbers,
        "systems": systems,
        "interpretation": interpretation,
        "synchronicities": synchronicities,
        "timestamp": ts,
        "location": location,
        "context": context,
    }


def read_name(name, birthday=None, mother_name=None):
    """
    Name-based reading combining Pythagorean and Chaldean numerology.

    Parameters
    ----------
    name : str
        Full name to analyze.
    birthday : str or None
        Optional birthday in YYYY-MM-DD format for life path calculation.
    mother_name : str or None
        Optional mother's name for additional influence reading.

    Returns
    -------
    dict
        Keys: name, expression, soul_urge, personality, life_path,
        chaldean, interpretation, birthday_zodiac, mother_influence.
    """
    if not name:
        return {
            "name": "",
            "error": "No name provided",
            "expression": 0,
            "soul_urge": 0,
            "personality": 0,
            "life_path": None,
            "chaldean": 0,
            "interpretation": "No name provided for reading.",
        }

    result = {
        "name": name,
        "expression": 0,
        "soul_urge": 0,
        "personality": 0,
        "life_path": None,
        "chaldean": 0,
        "interpretation": "",
    }

    # --- Pythagorean numerology via NameSolver's engine ---
    if _numerology_available:
        try:
            result["expression"] = name_to_number(name)
            result["soul_urge"] = name_soul_urge(name)
            result["personality"] = name_personality(name)

            # Life path meanings
            expr_info = LIFE_PATH_MEANINGS.get(result["expression"])
            result["expression_meaning"] = (
                f"{expr_info[0]}: {expr_info[1]}" if expr_info else ""
            )
            soul_info = LIFE_PATH_MEANINGS.get(result["soul_urge"])
            result["soul_urge_meaning"] = (
                f"{soul_info[0]}: {soul_info[1]}" if soul_info else ""
            )
            pers_info = LIFE_PATH_MEANINGS.get(result["personality"])
            result["personality_meaning"] = (
                f"{pers_info[0]}: {pers_info[1]}" if pers_info else ""
            )
        except Exception as exc:
            logger.debug("Pythagorean name analysis failed: %s", exc)

    # --- Life path from birthday ---
    parsed_bday = _parse_date(birthday)
    if parsed_bday and _numerology_available:
        try:
            year, month, day = parsed_bday
            lp = life_path(year, month, day)
            result["life_path"] = lp
            lp_info = LIFE_PATH_MEANINGS.get(lp)
            result["life_path_meaning"] = (
                f"{lp_info[0]}: {lp_info[1]}" if lp_info else ""
            )
        except Exception as exc:
            logger.debug("Life path calculation failed: %s", exc)

    # --- Birthday zodiac ---
    if parsed_bday:
        _, month, day = parsed_bday
        result["birthday_zodiac"] = _get_zodiac(month, day)

    # --- Chaldean numerology ---
    try:
        chaldean_val = _chaldean_reduce(name)
        result["chaldean"] = chaldean_val
        result["chaldean_meaning"] = _pythagorean_meaning(chaldean_val)

        # Letter-by-letter Chaldean breakdown
        breakdown = []
        for ch in name.upper():
            if ch in CHALDEAN_VALUES:
                breakdown.append(f"{ch}={CHALDEAN_VALUES[ch]}")
        result["chaldean_breakdown"] = " + ".join(breakdown)
        result["chaldean_raw_sum"] = sum(
            CHALDEAN_VALUES.get(ch, 0) for ch in name.upper()
        )
    except Exception as exc:
        logger.debug("Chaldean name analysis failed: %s", exc)

    # --- Mother's name influence ---
    if mother_name:
        try:
            mother_result = {
                "name": mother_name,
                "chaldean": _chaldean_reduce(mother_name),
            }
            if _numerology_available:
                mother_result["expression"] = name_to_number(mother_name)
                m_info = LIFE_PATH_MEANINGS.get(mother_result["expression"])
                mother_result["expression_meaning"] = (
                    f"{m_info[0]}: {m_info[1]}" if m_info else ""
                )
            result["mother_influence"] = mother_result
        except Exception as exc:
            logger.debug("Mother name analysis failed: %s", exc)

    # --- Build interpretation ---
    try:
        lines = []
        lines.append(f"=== NAME READING: {name.upper()} ===")
        lines.append("")

        lines.append("-- Pythagorean Numerology --")
        lines.append(
            f"  Expression (full name): {result['expression']} "
            f"- {result.get('expression_meaning', '')}"
        )
        lines.append(
            f"  Soul Urge (vowels): {result['soul_urge']} "
            f"- {result.get('soul_urge_meaning', '')}"
        )
        lines.append(
            f"  Personality (consonants): {result['personality']} "
            f"- {result.get('personality_meaning', '')}"
        )

        if result.get("life_path") is not None:
            lines.append(
                f"  Life Path: {result['life_path']} "
                f"- {result.get('life_path_meaning', '')}"
            )
        lines.append("")

        lines.append("-- Chaldean Numerology --")
        lines.append(
            f"  Chaldean value: {result['chaldean']} "
            f"- {result.get('chaldean_meaning', '')}"
        )
        if result.get("chaldean_breakdown"):
            lines.append(f"  Breakdown: {result['chaldean_breakdown']}")
        lines.append("")

        if result.get("birthday_zodiac"):
            z = result["birthday_zodiac"]
            lines.append("-- Birthday Zodiac --")
            lines.append(
                f"  {z['sign']} ({z['element']} / {z['quality']}), "
                f"ruled by {z['ruling_planet']}"
            )
            lines.append("")

        if result.get("mother_influence"):
            mi = result["mother_influence"]
            lines.append(f"-- Mother's Influence ({mi['name']}) --")
            lines.append(
                f"  Expression: {mi.get('expression', '?')} "
                f"- {mi.get('expression_meaning', '')}"
            )
            lines.append(f"  Chaldean: {mi.get('chaldean', '?')}")
            lines.append("")

        # Comparison between Pythagorean and Chaldean
        if result["expression"] and result["chaldean"]:
            if result["expression"] == result["chaldean"]:
                lines.append(
                    "Both Pythagorean and Chaldean systems agree on "
                    f"the core number {result['expression']} — "
                    "a strong, unified vibration."
                )
            else:
                lines.append(
                    f"Pythagorean ({result['expression']}) and Chaldean "
                    f"({result['chaldean']}) differ — "
                    "this suggests a multifaceted nature with both "
                    "an outer expression and a deeper inner current."
                )

        result["interpretation"] = "\n".join(lines)
    except Exception as exc:
        logger.debug("Name interpretation generation failed: %s", exc)
        result["interpretation"] = f"Name reading for {name}"

    return result


# ════════════════════════════════════════════════════════════
# V3: FC60 Human Meanings & New Public API
# ════════════════════════════════════════════════════════════

FC60_MEANINGS = {
    "VE": "Venus — love, beauty, harmony, attraction",
    "OX": "Ox — strength, patience, steady progress",
    "MO": "Moon — intuition, cycles, hidden knowledge",
    "TI": "Tiger — courage, passion, unpredictability",
    "MA": "Mars — action, drive, warrior energy",
    "RA": "Rabbit — gentleness, luck, quick thinking",
    "ME": "Mercury — communication, trade, cleverness",
    "DR": "Dragon — power, transformation, magic",
    "JU": "Jupiter — expansion, wisdom, abundance",
    "SN": "Snake — wisdom, healing, transformation",
    "SA": "Saturn — discipline, karma, boundaries",
    "HO": "Horse — freedom, adventure, speed",
    "SU": "Sun — vitality, success, consciousness",
    "GO": "Goat — creativity, peace, nurturing",
    "UR": "Uranus — innovation, disruption, awakening",
    "MK": "Monkey — wit, adaptability, resourcefulness",
    "NE": "Neptune — dreams, spirituality, illusion",
    "RO": "Rooster — precision, honesty, confidence",
    "PL": "Pluto — rebirth, depth, hidden power",
    "DO": "Dog — loyalty, protection, truth",
    "NO": "Node — destiny, karmic crossroads",
    "PI": "Pig — generosity, enjoyment, completion",
}

COMBINED_MEANINGS = {
    "VE-MO": "Love meets intuition — trust your heart's deeper knowing",
    "MA-TI": "Double fire — bold action with passionate courage",
    "JU-SU": "Expansion meets light — a time of great opportunity",
    "SA-PL": "Deep transformation through discipline — rebirth through patience",
    "ME-UR": "Lightning insight — sudden breakthroughs in understanding",
    "MO-NE": "Dreams within dreams — heightened psychic sensitivity",
    "VE-JU": "Abundance in love — generosity and harmony flow freely",
    "MA-SA": "Controlled power — strategic action with lasting results",
    "SU-MO": "Conscious and unconscious unite — wholeness and clarity",
    "ME-JU": "Wisdom expressed — teaching, learning, sharing knowledge",
}


def get_human_meaning(fc60_code):
    """Return a human-readable meaning for an FC60 symbol code.

    Args:
        fc60_code: FC60 code like "VE", "MO", "VE-MO", etc.

    Returns:
        Human-readable meaning string.
    """
    if not fc60_code:
        return "No code provided"

    code = fc60_code.strip().upper()

    # Check combined meanings first
    if code in COMBINED_MEANINGS:
        return COMBINED_MEANINGS[code]

    # Check single symbols
    if code in FC60_MEANINGS:
        return FC60_MEANINGS[code]

    # Try splitting on dash
    parts = code.split("-")
    meanings = []
    for part in parts:
        part = part.strip()
        if part in FC60_MEANINGS:
            meanings.append(FC60_MEANINGS[part])
    if meanings:
        return " + ".join(meanings)

    return f"Unknown FC60 symbol: {fc60_code}"


def question_sign(question, timestamp=None):
    """Read a sign based on a question and moment in time.

    Args:
        question: The question or sign text (e.g., "11:11", "444", "I saw a hawk")
        timestamp: Optional datetime; defaults to now.

    Returns:
        dict with: question, moment, numerology, fc60, moon, reading, advice
    """
    if timestamp is None:
        timestamp = datetime.now()

    result = {
        "question": question,
        "moment": timestamp.strftime("%Y-%m-%d %H:%M"),
        "numerology": {},
        "fc60": {},
        "moon": {},
        "reading": "",
        "advice": "",
    }

    # Extract numbers from the question
    numbers = _extract_numbers(question)

    # Numerology
    if _numerology_available and numbers:
        from engines.numerology import digit_sum, numerology_reduce, is_master_number

        reduced = [numerology_reduce(digit_sum(n)) for n in numbers]
        result["numerology"] = {
            "numbers": numbers,
            "reduced": reduced,
            "meanings": [_pythagorean_meaning(r) for r in reduced],
        }

    # FC60
    if _fc60_available:
        try:
            y, m, d = timestamp.year, timestamp.month, timestamp.day
            fc60_result = encode_fc60(y, m, d)
            fc60_code = fc60_result.get("fc60", "")
            result["fc60"] = {
                "code": fc60_code,
                "meaning": get_human_meaning(fc60_code),
                "raw": fc60_result,
            }
        except Exception:
            pass

    # Moon
    if _fc60_available:
        try:
            y, m, d = timestamp.year, timestamp.month, timestamp.day
            jdn = compute_jdn(y, m, d)
            phase = moon_phase(jdn)
            phase_name = MOON_PHASE_NAMES[phase]
            phase_meaning = MOON_PHASE_MEANINGS.get(phase, "")
            illum = moon_illumination(jdn)
            result["moon"] = {
                "phase": phase_name,
                "meaning": phase_meaning,
                "illumination": round(illum * 100, 1),
            }
        except Exception:
            pass

    # Generate reading
    reading_parts = []
    if result["numerology"].get("meanings"):
        reading_parts.append(
            "Numerology: " + ", ".join(result["numerology"]["meanings"])
        )
    if result["fc60"].get("meaning"):
        reading_parts.append(f"FC60: {result['fc60']['meaning']}")
    if result["moon"].get("phase"):
        reading_parts.append(
            f"Moon: {result['moon']['phase']} — {result['moon'].get('meaning', '')}"
        )

    result["reading"] = (
        " | ".join(reading_parts) if reading_parts else "Observe the moment"
    )

    # Advice based on numerology
    if numbers:
        syncs = _check_synchronicity(numbers)
        if syncs:
            result["advice"] = f"Synchronicity detected: {syncs[0]}"
        else:
            result["advice"] = (
                "The numbers carry their message — reflect on what drew your attention"
            )
    else:
        result["advice"] = (
            "No numbers in your question — focus on the feeling, not the logic"
        )

    return result


def daily_insight(date=None):
    """Generate a daily insight based on the current date.

    Args:
        date: Optional datetime; defaults to today.

    Returns:
        dict with: date, insight, lucky_numbers, energy
    """
    if date is None:
        date = datetime.now()

    result = {
        "date": date.strftime("%Y-%m-%d"),
        "insight": "",
        "lucky_numbers": [],
        "energy": "",
    }

    # Numerology of the date
    if _numerology_available:
        from engines.numerology import digit_sum, numerology_reduce

        date_num = int(date.strftime("%Y%m%d"))
        day_number = numerology_reduce(digit_sum(date_num))
        month_num = numerology_reduce(date.month)
        year_num = numerology_reduce(digit_sum(date.year))

        meanings = {
            1: ("New beginnings", "Initiative"),
            2: ("Partnership", "Balance"),
            3: ("Creativity", "Expression"),
            4: ("Foundation", "Structure"),
            5: ("Change", "Freedom"),
            6: ("Harmony", "Responsibility"),
            7: ("Reflection", "Wisdom"),
            8: ("Power", "Abundance"),
            9: ("Completion", "Universal love"),
            11: ("Illumination", "Mastery"),
            22: ("Master builder", "Vision"),
            33: ("Master teacher", "Compassion"),
        }

        day_meaning = meanings.get(day_number, ("Unique energy", "Exploration"))
        result["insight"] = (
            f"Day of {day_meaning[0]} — {day_meaning[1]}. Day number: {day_number}"
        )
        result["energy"] = day_meaning[0]

        # Lucky numbers: day number, month, year, their sum
        lucky = sorted(set([day_number, month_num, year_num]))
        result["lucky_numbers"] = lucky[:4]

    # FC60 info
    if _fc60_available:
        try:
            fc60_result = encode_fc60(date.year, date.month, date.day)
            fc60_code = fc60_result.get("fc60", "")
            meaning = get_human_meaning(fc60_code)
            result["insight"] += f" | FC60: {meaning}"
        except Exception:
            pass

    # Moon
    if _fc60_available:
        try:
            jdn = compute_jdn(date.year, date.month, date.day)
            phase = moon_phase(jdn)
            phase_name = MOON_PHASE_NAMES[phase]
            result["insight"] += f" | Moon: {phase_name}"
        except Exception:
            pass

    if not result["insight"]:
        result["insight"] = "Trust the process"
        result["energy"] = "Neutral"

    return result
