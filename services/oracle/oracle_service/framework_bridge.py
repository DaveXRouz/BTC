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

from oracle_service.models.reading_types import (
    MultiUserResult,
    ReadingResult,
    ReadingType,
    UserProfile,
)
from oracle_service.multi_user_analyzer import MultiUserAnalyzer

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


# ═══════════════════════════════════════════════════════════════════════════
# Typed Reading Functions (Session 7)
# ═══════════════════════════════════════════════════════════════════════════

# Personal day number -> suggested activities
_DAY_ACTIVITIES: Dict[int, List[str]] = {
    1: ["Start new projects", "Take initiative", "Assert yourself"],
    2: ["Collaborate with others", "Mediate conflicts", "Listen deeply"],
    3: ["Create art or music", "Write or express ideas", "Socialize"],
    4: ["Organize your workspace", "Build solid foundations", "Plan ahead"],
    5: ["Try something new", "Travel or explore", "Embrace change"],
    6: ["Help someone in need", "Focus on family", "Beautify your space"],
    7: ["Study or research", "Meditate", "Seek inner wisdom"],
    8: ["Focus on financial goals", "Exercise leadership", "Make bold decisions"],
    9: ["Give back", "Complete unfinished tasks", "Release what no longer serves"],
    11: ["Follow your intuition", "Inspire others", "Pursue spiritual growth"],
    22: ["Work on big visions", "Manifest your goals", "Build for the future"],
    33: ["Teach or mentor", "Practice compassion", "Heal through understanding"],
}

# Personal month number -> focus area
_MONTH_FOCUS: Dict[int, str] = {
    1: "New beginnings and self-reliance",
    2: "Relationships and cooperation",
    3: "Creative expression and communication",
    4: "Building foundations and discipline",
    5: "Freedom and embracing change",
    6: "Home, family, and responsibility",
    7: "Inner reflection and spiritual growth",
    8: "Career advancement and material goals",
    9: "Completion and humanitarian service",
    11: "Spiritual awareness and inspiration",
    22: "Large-scale manifesting and leadership",
    33: "Compassionate teaching and healing",
}


def _build_daily_insights(user: UserProfile, output: Dict[str, Any]) -> Dict[str, Any]:
    """Build daily_insights dict from framework output and user profile.

    Returns dict with 5 keys: suggested_activities, energy_forecast,
    lucky_hours, focus_area, element_of_day.
    """
    numerology = output.get("numerology", {})
    moon_data = output.get("moon", {})
    ganzhi_data = output.get("ganzhi", {})
    current = output.get("current", {})

    personal_day = numerology.get("personal_day", 1)
    moon_energy = moon_data.get("energy", "")
    moon_phase_name = moon_data.get("phase_name", "")
    planet = current.get("planet", "")
    domain = current.get("domain", "")
    day_element = ganzhi_data.get("day", {}).get("element", "Earth")
    day_stem_idx = ganzhi_data.get("day", {}).get("stem_index", 0)
    personal_month = numerology.get("personal_month", 1)

    # Suggested activities from personal day number
    activities = _DAY_ACTIVITIES.get(personal_day, ["Follow your daily routine"])

    # Energy forecast: moon phase energy + planetary day domain
    energy_forecast = f"{moon_phase_name} energy ({moon_energy}) meets {planet}'s {domain}"

    # Lucky hours: hours where user's birth year animal appears
    user_branch = GanzhiEngine.year_ganzhi(user.birth_year)[1]
    lucky_hours: List[int] = []
    for h in range(24):
        _, hour_branch = GanzhiEngine.hour_ganzhi(h, day_stem_idx)
        if hour_branch == user_branch:
            lucky_hours.append(h)

    # Focus area from personal month
    focus_area = _MONTH_FOCUS.get(personal_month, "Balance and awareness")

    return {
        "suggested_activities": activities,
        "energy_forecast": energy_forecast,
        "lucky_hours": lucky_hours,
        "focus_area": focus_area,
        "element_of_day": day_element,
    }


def generate_time_reading(
    user: UserProfile,
    hour: int,
    minute: int,
    second: int,
    target_date: Optional[datetime] = None,
) -> ReadingResult:
    """Generate a reading where the "sign" is a specific time (HH:MM:SS).

    The time overrides any time in target_date.

    Raises:
        ValueError: If hour/minute/second are out of range.
        FrameworkBridgeError: If framework reading generation fails.
    """
    if not (0 <= hour <= 23):
        raise ValueError(f"Invalid hour: {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"Invalid minute: {minute}")
    if not (0 <= second <= 59):
        raise ValueError(f"Invalid second: {second}")

    t0 = time.perf_counter()
    kwargs = user.to_framework_kwargs()
    kwargs["current_hour"] = hour
    kwargs["current_minute"] = minute
    kwargs["current_second"] = second
    if target_date is not None:
        kwargs["current_date"] = target_date

    output = generate_single_reading(**kwargs)
    duration_ms = (time.perf_counter() - t0) * 1000
    logger.info("Time reading generated in %.1fms", duration_ms)

    return ReadingResult(
        reading_type=ReadingType.TIME,
        user_id=user.user_id,
        framework_output=output,
        sign_value=f"{hour:02d}:{minute:02d}:{second:02d}",
        confidence_score=float(output.get("confidence", {}).get("score", 0)),
    )


def generate_name_reading(
    user: UserProfile,
    name_to_analyze: str,
    target_date: Optional[datetime] = None,
) -> ReadingResult:
    """Generate a reading where the "sign" is a name string.

    The name_to_analyze overrides user.full_name for numerology calculation.
    Other personal data (birth date, location, etc.) still comes from the
    user's profile.

    Raises:
        ValueError: If name_to_analyze is empty.
        FrameworkBridgeError: If framework reading generation fails.
    """
    if not name_to_analyze or not name_to_analyze.strip():
        raise ValueError("Name cannot be empty")

    t0 = time.perf_counter()
    kwargs = user.to_framework_kwargs()
    kwargs["full_name"] = name_to_analyze
    if target_date is not None:
        kwargs["current_date"] = target_date

    output = generate_single_reading(**kwargs)
    duration_ms = (time.perf_counter() - t0) * 1000
    logger.info("Name reading for '%s' generated in %.1fms", name_to_analyze, duration_ms)

    return ReadingResult(
        reading_type=ReadingType.NAME,
        user_id=user.user_id,
        framework_output=output,
        sign_value=name_to_analyze,
        confidence_score=float(output.get("confidence", {}).get("score", 0)),
    )


def generate_question_reading(
    user: UserProfile,
    question_text: str,
    target_date: Optional[datetime] = None,
) -> ReadingResult:
    """Generate a reading where the "sign" is a question typed by the user.

    The question's numerological vibration number is computed via
    NumerologyEngine.expression_number() and stored in the framework
    output as 'question_vibration'.

    Raises:
        ValueError: If question_text is empty.
        FrameworkBridgeError: If framework reading generation fails.
    """
    if not question_text or not question_text.strip():
        raise ValueError("Question cannot be empty")

    t0 = time.perf_counter()

    vibration = NumerologyEngine.expression_number(question_text, system=user.numerology_system)

    kwargs = user.to_framework_kwargs()
    if target_date is not None:
        kwargs["current_date"] = target_date

    output = generate_single_reading(**kwargs)
    output["question_vibration"] = vibration

    duration_ms = (time.perf_counter() - t0) * 1000
    logger.info("Question reading (vibration=%d) generated in %.1fms", vibration, duration_ms)

    return ReadingResult(
        reading_type=ReadingType.QUESTION,
        user_id=user.user_id,
        framework_output=output,
        sign_value=question_text,
        confidence_score=float(output.get("confidence", {}).get("score", 0)),
    )


def generate_daily_reading(
    user: UserProfile,
    target_date: Optional[datetime] = None,
) -> ReadingResult:
    """Generate a daily reading — no manual sign input.

    Uses noon (12:00:00) as the neutral midday energy point.
    Populates daily_insights with suggested_activities, energy_forecast,
    lucky_hours, focus_area, and element_of_day.

    Raises:
        FrameworkBridgeError: If framework reading generation fails.
    """
    t0 = time.perf_counter()

    kwargs = user.to_framework_kwargs()
    kwargs["current_hour"] = 12
    kwargs["current_minute"] = 0
    kwargs["current_second"] = 0
    if target_date is not None:
        kwargs["current_date"] = target_date

    output = generate_single_reading(**kwargs)
    daily_insights = _build_daily_insights(user, output)

    duration_ms = (time.perf_counter() - t0) * 1000
    logger.info("Daily reading generated in %.1fms", duration_ms)

    date_str = (target_date or datetime.now()).strftime("%Y-%m-%d")

    return ReadingResult(
        reading_type=ReadingType.DAILY,
        user_id=user.user_id,
        framework_output=output,
        sign_value=date_str,
        confidence_score=float(output.get("confidence", {}).get("score", 0)),
        daily_insights=daily_insights,
    )


def generate_multi_user_reading(
    users: List[UserProfile],
    reading_type: ReadingType = ReadingType.TIME,
    sign_value: Optional[str] = None,
    target_date: Optional[datetime] = None,
) -> MultiUserResult:
    """Generate readings for 2-5 users with pairwise compatibility analysis.

    Generates individual readings using the appropriate single-user function
    based on reading_type, then passes results to MultiUserAnalyzer.

    Raises:
        ValueError: If fewer than 2 or more than 5 users.
        FrameworkBridgeError: If any individual reading fails.
    """
    if len(users) < 2:
        raise ValueError("At least 2 users required")
    if len(users) > 5:
        raise ValueError("Maximum 5 users allowed")

    t0 = time.perf_counter()
    individual: List[ReadingResult] = []

    for user in users:
        if reading_type == ReadingType.TIME:
            if sign_value:
                parts = sign_value.split(":")
                h = int(parts[0])
                m = int(parts[1]) if len(parts) > 1 else 0
                s = int(parts[2]) if len(parts) > 2 else 0
            else:
                now = target_date or datetime.now()
                h, m, s = now.hour, now.minute, now.second
            reading = generate_time_reading(user, h, m, s, target_date)
        elif reading_type == ReadingType.NAME:
            reading = generate_name_reading(user, sign_value or user.full_name, target_date)
        elif reading_type == ReadingType.QUESTION:
            reading = generate_question_reading(
                user, sign_value or "What is our shared destiny?", target_date
            )
        elif reading_type == ReadingType.DAILY:
            reading = generate_daily_reading(user, target_date)
        else:
            reading = generate_time_reading(user, 12, 0, 0, target_date)
        individual.append(reading)

    result = MultiUserAnalyzer.analyze_group(individual)

    duration_ms = (time.perf_counter() - t0) * 1000
    logger.info("Multi-user reading (%d users) generated in %.1fms", len(users), duration_ms)

    return result
