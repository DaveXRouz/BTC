"""Framework Bridge — connects NPS Oracle service to numerology_ai_framework.

This module is the SINGLE integration point between the Oracle gRPC service
and the numerology_ai_framework package. It provides:

1. High-level reading functions (generate_single_reading, generate_multi_reading)
2. DB-to-framework field mapping (map_oracle_user_to_framework_kwargs)
3. Backward-compatible re-exports matching old engines.fc60 / engines.numerology APIs
4. Error handling with FrameworkBridgeError
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from numerology_ai_framework.core.base60_codec import Base60Codec
from numerology_ai_framework.core.fc60_stamp_engine import FC60StampEngine
from numerology_ai_framework.core.julian_date_engine import JulianDateEngine
from numerology_ai_framework.core.weekday_calculator import WeekdayCalculator
from numerology_ai_framework.personal.numerology_engine import NumerologyEngine
from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator
from numerology_ai_framework.universal.ganzhi_engine import GanzhiEngine
from numerology_ai_framework.universal.moon_engine import MoonEngine

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════════════


class FrameworkBridgeError(Exception):
    """Raised when framework integration fails."""


# ═══════════════════════════════════════════════════════════════════════════
# High-Level Bridge Functions
# ═══════════════════════════════════════════════════════════════════════════


def generate_single_reading(
    full_name: str,
    birth_day: int,
    birth_month: int,
    birth_year: int,
    current_date: Optional[datetime] = None,
    mother_name: Optional[str] = None,
    gender: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    heart_rate_bpm: Optional[int] = None,
    current_hour: Optional[int] = None,
    current_minute: Optional[int] = None,
    current_second: Optional[int] = None,
    tz_hours: int = 0,
    tz_minutes: int = 0,
    numerology_system: str = "pythagorean",
    mode: str = "full",
) -> Dict[str, Any]:
    """Generate a complete numerological reading for one person.

    Wraps MasterOrchestrator.generate_reading() with timing, error handling,
    and input validation.

    Returns:
        Full framework output dict (person, numerology, fc60_stamp, moon,
        ganzhi, heartbeat, patterns, confidence, synthesis, etc.)

    Raises:
        FrameworkBridgeError: If reading generation fails.
    """
    if not full_name or not full_name.strip():
        raise FrameworkBridgeError("Full name is required")
    if not (1 <= birth_month <= 12):
        raise FrameworkBridgeError(f"Invalid birth month: {birth_month}")
    if not (1 <= birth_day <= 31):
        raise FrameworkBridgeError(f"Invalid birth day: {birth_day}")
    if birth_year < 1:
        raise FrameworkBridgeError(f"Invalid birth year: {birth_year}")

    t0 = time.perf_counter()
    try:
        result = MasterOrchestrator.generate_reading(
            full_name=full_name,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
            current_date=current_date,
            mother_name=mother_name,
            gender=gender,
            latitude=latitude,
            longitude=longitude,
            actual_bpm=heart_rate_bpm,
            current_hour=current_hour,
            current_minute=current_minute,
            current_second=current_second,
            tz_hours=tz_hours,
            tz_minutes=tz_minutes,
            numerology_system=numerology_system,
            mode=mode,
        )
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.info("Framework reading generated in %.1fms", duration_ms)
        return result
    except (ValueError, TypeError) as e:
        duration_ms = (time.perf_counter() - t0) * 1000
        logger.error("Framework reading failed after %.1fms: %s", duration_ms, e)
        raise FrameworkBridgeError(f"Reading generation failed: {e}") from e


def generate_multi_reading(
    users: List[Dict[str, Any]],
    current_date: Optional[datetime] = None,
    current_hour: Optional[int] = None,
    current_minute: Optional[int] = None,
    current_second: Optional[int] = None,
    numerology_system: str = "pythagorean",
) -> List[Dict[str, Any]]:
    """Generate readings for multiple users.

    Each user dict must have: full_name, birth_day, birth_month, birth_year.
    Optional: mother_name, gender, latitude, longitude, heart_rate_bpm,
    tz_hours, tz_minutes.

    Returns:
        List of framework output dicts, one per user.

    Raises:
        FrameworkBridgeError: If any reading fails.
    """
    results = []
    for user in users:
        result = generate_single_reading(
            full_name=user["full_name"],
            birth_day=user["birth_day"],
            birth_month=user["birth_month"],
            birth_year=user["birth_year"],
            current_date=current_date,
            mother_name=user.get("mother_name"),
            gender=user.get("gender"),
            latitude=user.get("latitude"),
            longitude=user.get("longitude"),
            heart_rate_bpm=user.get("heart_rate_bpm"),
            current_hour=current_hour,
            current_minute=current_minute,
            current_second=current_second,
            tz_hours=user.get("tz_hours", 0),
            tz_minutes=user.get("tz_minutes", 0),
            numerology_system=numerology_system,
        )
        results.append(result)
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Field Mapping (oracle_users DB → framework kwargs)
# ═══════════════════════════════════════════════════════════════════════════


def map_oracle_user_to_framework_kwargs(oracle_user: Any) -> Dict[str, Any]:
    """Map an oracle_user ORM object or dict to MasterOrchestrator kwargs.

    Field mapping:
        oracle_users.name          → full_name
        oracle_users.birthday      → birth_day, birth_month, birth_year
        oracle_users.mother_name   → mother_name
        oracle_users.coordinates   → latitude, longitude
        oracle_users.gender        → gender
        oracle_users.heart_rate_bpm → heart_rate_bpm
        oracle_users.timezone_hours → tz_hours
        oracle_users.timezone_minutes → tz_minutes

    Handles both dict and ORM-style access (getattr with defaults).
    """

    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Extract birthday components
    birthday = _get(oracle_user, "birthday")
    if birthday is None:
        raise FrameworkBridgeError("birthday is required for framework reading")

    if isinstance(birthday, str):
        parts = birthday.split("-")
        birth_year, birth_month, birth_day = int(parts[0]), int(parts[1]), int(parts[2])
    elif hasattr(birthday, "year"):
        birth_year = birthday.year
        birth_month = birthday.month
        birth_day = birthday.day
    else:
        raise FrameworkBridgeError(f"Unsupported birthday type: {type(birthday)}")

    # Extract coordinates from POINT or separate fields
    latitude = _get(oracle_user, "latitude")
    longitude = _get(oracle_user, "longitude")

    if latitude is None or longitude is None:
        coords = _get(oracle_user, "coordinates")
        if coords is not None:
            if isinstance(coords, str) and coords.startswith("("):
                # PostgreSQL POINT format: "(lon,lat)"
                clean = coords.strip("()").split(",")
                longitude = float(clean[0])
                latitude = float(clean[1])

    kwargs: Dict[str, Any] = {
        "full_name": _get(oracle_user, "name", ""),
        "birth_day": birth_day,
        "birth_month": birth_month,
        "birth_year": birth_year,
        "mother_name": _get(oracle_user, "mother_name"),
        "gender": _get(oracle_user, "gender"),
        "latitude": latitude,
        "longitude": longitude,
        "heart_rate_bpm": _get(oracle_user, "heart_rate_bpm"),
        "tz_hours": _get(oracle_user, "timezone_hours", 0) or 0,
        "tz_minutes": _get(oracle_user, "timezone_minutes", 0) or 0,
    }
    return kwargs


# ═══════════════════════════════════════════════════════════════════════════
# Constants — backward-compatible re-exports from old engines.fc60
# ═══════════════════════════════════════════════════════════════════════════

ANIMALS = Base60Codec.ANIMALS
ELEMENTS = Base60Codec.ELEMENTS
WEEKDAYS = WeekdayCalculator.WEEKDAY_TOKENS
STEMS = GanzhiEngine.STEMS

ANIMAL_NAMES = GanzhiEngine.ANIMAL_NAMES
ELEMENT_NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]
STEM_NAMES = GanzhiEngine.STEM_NAMES
STEM_CHINESE = [
    "\u7532",
    "\u4e59",
    "\u4e19",
    "\u4e01",
    "\u620a",
    "\u5df1",
    "\u5e9a",
    "\u8f9b",
    "\u58ec",
    "\u7678",
]
STEM_ELEMENTS = GanzhiEngine.STEM_ELEMENTS
STEM_POLARITY = GanzhiEngine.STEM_POLARITIES

WEEKDAY_NAMES = WeekdayCalculator.WEEKDAY_NAMES
WEEKDAY_PLANETS = WeekdayCalculator.PLANETS
WEEKDAY_DOMAINS = WeekdayCalculator.DOMAINS

MOON_PHASE_NAMES = MoonEngine.PHASE_NAMES
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

ELEMENT_FORCE = ["Growth", "Transformation", "Grounding", "Refinement", "Depth"]

# ── Numerology constants ──

LETTER_VALUES = NumerologyEngine.PYTHAGOREAN
VOWELS = NumerologyEngine.VOWELS

LIFE_PATH_MEANINGS = {
    1: ("The Pioneer", "Lead, start, go first"),
    2: ("The Bridge", "Connect, harmonize, feel"),
    3: ("The Voice", "Create, express, beautify"),
    4: ("The Architect", "Build, structure, stabilize"),
    5: ("The Explorer", "Change, adapt, experience"),
    6: ("The Guardian", "Nurture, heal, protect"),
    7: ("The Seeker", "Question, analyze, find meaning"),
    8: ("The Powerhouse", "Master, achieve, build legacy"),
    9: ("The Sage", "Complete, teach, transcend"),
    11: ("The Visionary", "See what hasn't been built (master)"),
    22: ("The Master Builder", "Turn impossible visions into reality (master)"),
    33: ("The Master Teacher", "Heal through compassionate leadership (master)"),
}


# ═══════════════════════════════════════════════════════════════════════════
# Backward-Compatible Function Wrappers
# ═══════════════════════════════════════════════════════════════════════════

# ── Base-60 encoding ──


def token60(n: int) -> str:
    """Backward-compatible wrapper for Base60Codec.token60."""
    return Base60Codec.token60(n)


def encode_base60(n: int) -> str:
    """Backward-compatible wrapper for Base60Codec.encode_base60."""
    return Base60Codec.encode_base60(n)


# Build reverse lookup for digit60
_TOKEN60_TO_INDEX: Dict[str, int] = {Base60Codec.token60(i): i for i in range(60)}


def digit60(tok: str) -> int:
    """Reverse token60 lookup: 4-char token → 0..59 index."""
    idx = _TOKEN60_TO_INDEX.get(tok)
    if idx is None:
        raise ValueError(f"Unknown token60: {tok!r}")
    return idx


# ── Julian Date / Weekday ──


def compute_jdn(y: int, m: int, d: int) -> int:
    """Backward-compatible wrapper for JulianDateEngine.gregorian_to_jdn."""
    return JulianDateEngine.gregorian_to_jdn(y, m, d)


def jdn_to_gregorian(jdn: int) -> tuple:
    """Backward-compatible wrapper for JulianDateEngine.jdn_to_gregorian."""
    return JulianDateEngine.jdn_to_gregorian(jdn)


def weekday_from_jdn(jdn: int) -> int:
    """Backward-compatible wrapper for WeekdayCalculator.weekday_from_jdn."""
    return WeekdayCalculator.weekday_from_jdn(jdn)


# ── FC60 encoding ──


def encode_fc60(
    y: int,
    m: int,
    d: int,
    h: int = 0,
    mi: int = 0,
    s: int = 0,
    tz_h: int = 0,
    tz_m: int = 0,
    include_time: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Backward-compatible wrapper for FC60StampEngine.encode.

    Old signature: encode_fc60(y, m, d, h, mi, s, tz_h, tz_m, include_time=True)
    New signature: FC60StampEngine.encode(year, month, day, hour, minute, second,
                                          tz_hours, tz_minutes, has_time=True)
    """
    result = FC60StampEngine.encode(y, m, d, h, mi, s, tz_h, tz_m, has_time=include_time)

    # Add backward-compatible keys that old code expects
    jdn = result["_jdn"]
    wd_idx = result["_weekday_index"]
    age = MoonEngine.moon_age(jdn)
    illum = MoonEngine.moon_illumination(age)

    result["jdn"] = jdn
    result["weekday_name"] = WEEKDAY_NAMES[wd_idx]
    result["weekday_planet"] = WEEKDAY_PLANETS[wd_idx]
    result["weekday_domain"] = WEEKDAY_DOMAINS[wd_idx]
    result["moon_illumination"] = round(illum, 1)

    # Ganzhi info
    stem_idx, branch_idx = GanzhiEngine.year_ganzhi(y)
    result["gz_name"] = f"{STEM_NAMES[stem_idx]} {ANIMAL_NAMES[branch_idx]}"

    return result


# ── Ganzhi ──


def ganzhi_year(year: int) -> tuple:
    """Backward-compatible wrapper for GanzhiEngine.year_ganzhi."""
    return GanzhiEngine.year_ganzhi(year)


def ganzhi_year_tokens(year: int) -> tuple:
    """Backward-compatible wrapper for GanzhiEngine.year_ganzhi_tokens."""
    return GanzhiEngine.year_ganzhi_tokens(year)


def ganzhi_year_name(year: int) -> str:
    """Backward-compatible wrapper for GanzhiEngine.full_year_info."""
    info = GanzhiEngine.full_year_info(year)
    return info["traditional_name"]


def ganzhi_day(jdn: int) -> tuple:
    """Backward-compatible wrapper for GanzhiEngine.day_ganzhi."""
    return GanzhiEngine.day_ganzhi(jdn)


def ganzhi_hour(hour: int, day_stem: int) -> tuple:
    """Backward-compatible wrapper for GanzhiEngine.hour_ganzhi."""
    return GanzhiEngine.hour_ganzhi(hour, day_stem)


# ── Moon ──


def moon_phase(jdn: int) -> tuple:
    """Backward-compatible wrapper returning (phase_index, age_in_days).

    Old: moon_phase(jdn) -> (int, float)
    New: MoonEngine.moon_phase(jdn) -> (name, emoji, age)
    """
    phase_name, _emoji, age = MoonEngine.moon_phase(jdn)
    phase_idx = MoonEngine.PHASE_NAMES.index(phase_name)
    return (phase_idx, age)


def moon_illumination(age: float) -> float:
    """Backward-compatible wrapper for MoonEngine.moon_illumination."""
    return MoonEngine.moon_illumination(age)


# ── Numerology ──


def numerology_reduce(n: int) -> int:
    """Backward-compatible wrapper for NumerologyEngine.digital_root."""
    return NumerologyEngine.digital_root(n)


def life_path(year: int, month: int, day: int) -> int:
    """Backward-compatible wrapper for NumerologyEngine.life_path.

    NOTE: Old signature is (year, month, day).
    Framework signature is (day, month, year).
    This wrapper preserves the OLD parameter order.
    """
    return NumerologyEngine.life_path(day, month, year)


def name_to_number(name: str, system: str = "pythagorean") -> int:
    """Backward-compatible wrapper for NumerologyEngine.expression_number."""
    return NumerologyEngine.expression_number(name, system=system)


def name_soul_urge(name: str, system: str = "pythagorean") -> int:
    """Backward-compatible wrapper for NumerologyEngine.soul_urge."""
    return NumerologyEngine.soul_urge(name, system=system)


def name_personality(name: str, system: str = "pythagorean") -> int:
    """Backward-compatible wrapper for NumerologyEngine.personality_number."""
    return NumerologyEngine.personality_number(name, system=system)


def personal_year(birth_month: int, birth_day: int, current_year: int) -> int:
    """Backward-compatible wrapper for NumerologyEngine.personal_year."""
    return NumerologyEngine.personal_year(birth_month, birth_day, current_year)


def digit_sum(n: int) -> int:
    """Sum all digits of n."""
    return sum(int(d) for d in str(abs(n)))


def is_master_number(n: int) -> bool:
    """True if n itself is 11/22/33 or reduces through a master number."""
    if n in (11, 22, 33):
        return True
    total = digit_sum(n)
    while total > 9:
        if total in (11, 22, 33):
            return True
        total = sum(int(d) for d in str(total))
    return total in (11, 22, 33)


# ── FC60 self-test (used by server.py HealthCheck) ──


def self_test() -> list:
    """Run FC60 test vectors and return list of (description, passed) tuples."""
    results = []
    test_vectors = [
        ((2026, 2, 6, 1, 15, 0, 8, 0), "VE-OX-OXFI \u2600OX-RUWU-RAWU"),
        ((2000, 1, 1, 0, 0, 0, 0, 0), "SA-RA-RAFI \u2600RA-RAWU-RAWU"),
        ((2026, 1, 1, 0, 0, 0, 0, 0), "JO-RA-RAFI \u2600RA-RAWU-RAWU"),
    ]
    for args, expected_fc60 in test_vectors:
        result = FC60StampEngine.encode(*args)
        passed = result["fc60"] == expected_fc60
        results.append((f"encode{args[:3]}", passed))
    return results


# ── Symbolic reading (used by old numerology.py) ──


def generate_symbolic_reading(
    year: int,
    month: int,
    day: int,
    hour: int = 0,
    minute: int = 0,
    second: int = 0,
) -> str:
    """Generate a symbolic reading string for a date/time."""
    result = encode_fc60(year, month, day, hour, minute, second)
    wd_idx = weekday_from_jdn(compute_jdn(year, month, day))
    jdn = compute_jdn(year, month, day)
    phase_idx, age = moon_phase(jdn)
    illum = moon_illumination(age)
    stem_idx, branch_idx = ganzhi_year(year)

    lines = []
    lines.append(f"FC60 Stamp: {result['fc60']}")
    lines.append(f"Day: {WEEKDAY_NAMES[wd_idx]} ({WEEKDAY_PLANETS[wd_idx]})")
    lines.append(f"Moon: {MOON_PHASE_NAMES[phase_idx]} ({illum:.0f}% illuminated)")
    lines.append(f"Year: {STEM_NAMES[stem_idx]} {ANIMAL_NAMES[branch_idx]}")
    return "\n".join(lines)
