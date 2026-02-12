"""
AI Prompt Builder — Framework Reading to User Prompt
=====================================================
Constructs user prompts from MasterOrchestrator.generate_reading() output.
Each section of the reading is formatted into a structured text block
that the AI can parse and interpret.

Public API:
  - build_reading_prompt(reading, reading_type, question, locale) -> str
  - build_multi_user_prompt(readings, names, locale) -> str
"""

from __future__ import annotations


def _safe_get(d: dict, *keys, default: str = "not provided") -> str:
    """Safely traverse nested dict keys, returning default on any miss."""
    current = d
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return str(current)


def _format_person(reading: dict) -> str:
    """Format the person section."""
    person = reading.get("person", {})
    if not person:
        return "--- PERSON ---\nnot provided"
    lines = ["--- PERSON ---"]
    lines.append(f"Name: {person.get('name', 'not provided')}")
    lines.append(f"Birthdate: {person.get('birthdate', 'not provided')}")
    age_years = person.get("age_years")
    age_days = person.get("age_days")
    if age_years is not None:
        age_str = f"{age_years} years"
        if age_days is not None:
            age_str += f" ({age_days} days)"
        lines.append(f"Age: {age_str}")
    return "\n".join(lines)


def _format_fc60_stamp(reading: dict) -> str:
    """Format the FC60 stamp section."""
    stamp = reading.get("fc60_stamp", {})
    if not stamp:
        return "--- FC60 STAMP ---\nnot provided"
    lines = ["--- FC60 STAMP ---"]
    lines.append(f"FC60: {stamp.get('fc60', 'not provided')}")
    lines.append(f"J60: {stamp.get('j60', 'not provided')}")
    lines.append(f"Y60: {stamp.get('y60', 'not provided')}")
    lines.append(f"CHK: {stamp.get('chk', 'not provided')}")
    iso = stamp.get("iso")
    if iso:
        lines.append(f"ISO: {iso}")
    return "\n".join(lines)


def _format_birth(reading: dict) -> str:
    """Format the birth data section."""
    birth = reading.get("birth", {})
    if not birth:
        return "--- BIRTH DATA ---\nnot provided"
    lines = ["--- BIRTH DATA ---"]
    lines.append(f"JDN: {birth.get('jdn', 'not provided')}")
    lines.append(f"Weekday: {birth.get('weekday', 'not provided')}")
    lines.append(f"Planet: {birth.get('planet', 'not provided')}")
    return "\n".join(lines)


def _format_current(reading: dict) -> str:
    """Format the current moment section."""
    current = reading.get("current", {})
    if not current:
        return "--- CURRENT DATA ---\nnot provided"
    lines = ["--- CURRENT DATA ---"]
    lines.append(f"Date: {current.get('date', 'not provided')}")
    lines.append(f"Weekday: {current.get('weekday', 'not provided')}")
    lines.append(f"Planet: {current.get('planet', 'not provided')}")
    lines.append(f"Domain: {current.get('domain', 'not provided')}")
    return "\n".join(lines)


def _format_numerology(numerology: dict) -> str:
    """Format the numerology section of a reading."""
    if not numerology:
        return "--- NUMEROLOGY ---\nnot provided"
    lines = ["--- NUMEROLOGY ---"]

    lp = numerology.get("life_path", {})
    if isinstance(lp, dict):
        lp_num = lp.get("number", "not provided")
        lp_title = lp.get("title", "")
        lp_msg = lp.get("message", "")
        lines.append(f"Life Path: {lp_num} ({lp_title})")
        if lp_msg:
            lines.append(f"  Message: {lp_msg}")
    else:
        lines.append(f"Life Path: {lp}")

    lines.append(f"Expression: {numerology.get('expression', 'not provided')}")
    lines.append(f"Soul Urge: {numerology.get('soul_urge', 'not provided')}")
    lines.append(f"Personality: {numerology.get('personality', 'not provided')}")
    lines.append(f"Personal Year: {numerology.get('personal_year', 'not provided')}")
    lines.append(f"Personal Month: {numerology.get('personal_month', 'not provided')}")
    lines.append(f"Personal Day: {numerology.get('personal_day', 'not provided')}")

    gp = numerology.get("gender_polarity")
    if gp and isinstance(gp, dict):
        lines.append(f"Gender Polarity: {gp.get('label', 'not provided')}")

    mi = numerology.get("mother_influence")
    if mi is not None:
        lines.append(f"Mother Influence: {mi}")

    return "\n".join(lines)


def _format_moon(moon: dict) -> str:
    """Format the moon section of a reading."""
    if not moon:
        return "--- MOON ---\nnot provided"
    lines = ["--- MOON ---"]
    lines.append(f"Phase: {moon.get('phase_name', 'not provided')} {moon.get('emoji', '')}")
    lines.append(f"Age: {moon.get('age', 'not provided')} days")
    lines.append(f"Illumination: {moon.get('illumination', 'not provided')}%")
    lines.append(f"Energy: {moon.get('energy', 'not provided')}")
    lines.append(f"Best For: {moon.get('best_for', 'not provided')}")
    lines.append(f"Avoid: {moon.get('avoid', 'not provided')}")
    return "\n".join(lines)


def _format_ganzhi(ganzhi: dict) -> str:
    """Format the ganzhi section of a reading."""
    if not ganzhi:
        return "--- GANZHI ---\nnot provided"
    lines = ["--- GANZHI ---"]

    year = ganzhi.get("year", {})
    if year and isinstance(year, dict):
        trad = year.get("traditional_name", "")
        elem = year.get("element", "")
        animal = year.get("animal_name", "")
        lines.append(f"Year: {trad} ({elem}, {animal})")

    day = ganzhi.get("day", {})
    if day and isinstance(day, dict):
        gz = day.get("gz_token", "")
        elem = day.get("element", "")
        animal = day.get("animal_name", "")
        lines.append(f"Day: {gz} ({elem}, {animal})")

    hour = ganzhi.get("hour", {})
    if hour and isinstance(hour, dict):
        animal = hour.get("animal_name", "")
        if animal:
            lines.append(f"Hour: {animal}")

    return "\n".join(lines)


def _format_heartbeat(heartbeat: dict) -> str:
    """Format the heartbeat section of a reading."""
    if not heartbeat:
        return "--- HEARTBEAT ---\nnot provided"
    lines = ["--- HEARTBEAT ---"]
    lines.append(
        f"BPM: {heartbeat.get('bpm', 'not provided')} "
        f"({heartbeat.get('bpm_source', 'not provided')})"
    )
    lines.append(f"Element: {heartbeat.get('element', 'not provided')}")
    lines.append(f"Lifetime Beats: {heartbeat.get('total_lifetime_beats', 'not provided')}")
    lines.append(f"Rhythm Token: {heartbeat.get('rhythm_token', 'not provided')}")
    return "\n".join(lines)


def _format_location(location: dict | None) -> str:
    """Format the location section (returns 'Not provided' if None)."""
    if not location:
        return "--- LOCATION ---\nnot provided"
    lines = ["--- LOCATION ---"]
    lines.append(
        f"Latitude: {location.get('latitude', 'not provided')} "
        f"({location.get('lat_hemisphere', '')})"
    )
    lines.append(
        f"Longitude: {location.get('longitude', 'not provided')} "
        f"({location.get('lon_hemisphere', '')})"
    )
    lines.append(f"Element: {location.get('element', 'not provided')}")
    return "\n".join(lines)


def _format_patterns(patterns: dict) -> str:
    """Format the patterns section, sorted by strength."""
    if not patterns:
        return "--- PATTERNS ---\nnot provided"
    lines = ["--- PATTERNS ---"]
    detected = patterns.get("detected", [])
    count = patterns.get("count", len(detected))
    lines.append(f"Count: {count}")

    strength_order = {"very_high": 0, "high": 1, "medium": 2, "low": 3}
    sorted_patterns = sorted(
        detected,
        key=lambda p: strength_order.get(p.get("strength", "low"), 4),
    )
    for p in sorted_patterns:
        ptype = p.get("type", "unknown")
        strength = p.get("strength", "unknown")
        message = p.get("message", "")
        lines.append(f"  Type: {ptype}, Strength: {strength}, Message: {message}")

    return "\n".join(lines)


def _format_confidence(confidence: dict) -> str:
    """Format the confidence section."""
    if not confidence:
        return "--- CONFIDENCE ---\nnot provided"
    lines = ["--- CONFIDENCE ---"]
    lines.append(f"Score: {confidence.get('score', 'not provided')}%")
    lines.append(f"Level: {confidence.get('level', 'not provided')}")
    lines.append(f"Factors: {confidence.get('factors', 'not provided')}")
    return "\n".join(lines)


def build_reading_prompt(
    reading: dict,
    reading_type: str = "daily",
    question: str = "",
    locale: str = "en",
) -> str:
    """Build user prompt from MasterOrchestrator.generate_reading() output.

    Parameters
    ----------
    reading : dict
        Full output from MasterOrchestrator.generate_reading().
    reading_type : str
        One of: "daily", "time", "name", "question", "multi".
    question : str
        The user's question (only for reading_type="question").
    locale : str
        "en" or "fa" — affects section labels and instructions.

    Returns
    -------
    str
        Formatted user prompt ready to send to the AI.
    """
    parts = [f"READING TYPE: {reading_type}"]
    if reading_type == "question" and question:
        parts.append(f"QUESTION: {question}")
    parts.append(f"LOCALE: {locale}")
    parts.append("")

    parts.append(_format_person(reading))
    parts.append("")
    parts.append(_format_fc60_stamp(reading))
    parts.append("")
    parts.append(_format_birth(reading))
    parts.append("")
    parts.append(_format_current(reading))
    parts.append("")
    parts.append(_format_numerology(reading.get("numerology", {})))
    parts.append("")
    parts.append(_format_moon(reading.get("moon", {})))
    parts.append("")
    parts.append(_format_ganzhi(reading.get("ganzhi", {})))
    parts.append("")
    parts.append(_format_heartbeat(reading.get("heartbeat", {})))
    parts.append("")
    parts.append(_format_location(reading.get("location")))
    parts.append("")
    parts.append(_format_patterns(reading.get("patterns", {})))
    parts.append("")
    parts.append(_format_confidence(reading.get("confidence", {})))
    parts.append("")

    synthesis = reading.get("synthesis", "")
    if synthesis:
        parts.append("--- FRAMEWORK SYNTHESIS ---")
        parts.append(synthesis)

    return "\n".join(parts)


def build_multi_user_prompt(
    readings: list[dict],
    names: list[str],
    locale: str = "en",
) -> str:
    """Build user prompt for multi-user reading.

    Parameters
    ----------
    readings : list[dict]
        List of reading dicts from MasterOrchestrator.generate_reading().
    names : list[str]
        List of user names corresponding to each reading.
    locale : str
        "en" or "fa".

    Returns
    -------
    str
        Formatted multi-user prompt.
    """
    parts = [
        "READING TYPE: multi",
        f"LOCALE: {locale}",
        f"USER COUNT: {len(readings)}",
        "",
    ]

    for i, (reading, name) in enumerate(zip(readings, names)):
        parts.append(f"========== USER {i + 1}: {name} ==========")
        parts.append("")
        parts.append(build_reading_prompt(reading, reading_type="multi", locale=locale))
        parts.append("")

    parts.append("========== GROUP ANALYSIS ==========")
    parts.append(
        "Please provide individual interpretations for each user above, "
        "followed by a group compatibility narrative and group synthesis."
    )

    return "\n".join(parts)
