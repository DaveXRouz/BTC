"""
Timing Advisor -- When to Scan
===============================
Combines moon phase, FC60 current moment, and day/hour numerology
to advise on optimal scanning times. Pure computation, no I/O.
"""

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def get_current_quality():
    """Assess the current moment's quality for scanning.

    Returns:
        dict with keys: quality, score (0-1), moon_phase, reasoning.
        quality is one of 'excellent', 'good', 'fair', 'poor'.
    """
    from engines.fc60 import (
        compute_jdn,
        moon_phase,
        moon_illumination,
        MOON_PHASE_NAMES,
        weekday_from_jdn,
        WEEKDAY_PLANETS,
    )
    from engines.numerology import numerology_reduce, is_master_number

    now = datetime.now(timezone.utc)
    year, month, day = now.year, now.month, now.day
    hour = now.hour

    jdn = compute_jdn(year, month, day)
    phase_idx, moon_age = moon_phase(jdn)
    illum = moon_illumination(moon_age)
    phase_name = MOON_PHASE_NAMES[phase_idx]
    wd_idx = weekday_from_jdn(jdn)

    # Score components (each 0-1)
    scores = []
    reasoning = []

    # 1. Moon phase score: Full Moon and New Moon are peak
    moon_scores = {0: 0.9, 1: 0.5, 2: 0.6, 3: 0.7, 4: 1.0, 5: 0.7, 6: 0.6, 7: 0.4}
    moon_s = moon_scores.get(phase_idx, 0.5)
    scores.append(moon_s)
    reasoning.append(
        "Moon: {} ({:.0f}% illum, score {:.1f})".format(phase_name, illum, moon_s)
    )

    # 2. Day numerology
    day_sum = year + month + day
    day_reduced = numerology_reduce(day_sum)
    day_master = is_master_number(day_sum)
    power_numbers = {1, 8, 9, 11, 22, 33}
    if day_master or day_reduced in power_numbers:
        day_s = 0.9
    elif day_reduced in {3, 5, 7}:
        day_s = 0.7
    else:
        day_s = 0.5
    scores.append(day_s)
    reasoning.append(
        "Day number: {} (master={}, score {:.1f})".format(
            day_reduced, day_master, day_s
        )
    )

    # 3. Hour numerology
    hour_reduced = numerology_reduce(hour) if hour > 0 else 1
    hour_master = is_master_number(hour)
    if hour_master or hour_reduced in power_numbers:
        hour_s = 0.85
    elif hour_reduced in {3, 5, 7}:
        hour_s = 0.65
    else:
        hour_s = 0.45
    scores.append(hour_s)
    reasoning.append(
        "Hour {} (reduces to {}, score {:.1f})".format(hour, hour_reduced, hour_s)
    )

    # 4. Weekday alignment
    # Jupiter (Thursday=4) and Venus (Friday=5) are traditionally favorable
    weekday_scores = {0: 0.7, 1: 0.5, 2: 0.6, 3: 0.6, 4: 0.9, 5: 0.8, 6: 0.5}
    wd_s = weekday_scores.get(wd_idx, 0.5)
    planet = WEEKDAY_PLANETS[wd_idx]
    scores.append(wd_s)
    reasoning.append("Weekday: {} (score {:.1f})".format(planet, wd_s))

    # Aggregate
    total = sum(scores) / len(scores)

    if total >= 0.8:
        quality = "excellent"
    elif total >= 0.65:
        quality = "good"
    elif total >= 0.5:
        quality = "fair"
    else:
        quality = "poor"

    return {
        "quality": quality,
        "score": round(total, 4),
        "moon_phase": phase_name,
        "reasoning": "; ".join(reasoning),
    }


def get_optimal_hours_today():
    """Evaluate all 24 hours of today and rank them by scanning quality.

    Returns:
        list of (hour, score) tuples sorted by score descending.
    """
    from engines.fc60 import compute_jdn, moon_phase, weekday_from_jdn
    from engines.numerology import numerology_reduce, is_master_number

    now = datetime.now(timezone.utc)
    year, month, day = now.year, now.month, now.day

    jdn = compute_jdn(year, month, day)
    phase_idx, _ = moon_phase(jdn)
    wd_idx = weekday_from_jdn(jdn)

    # Base day score (constant across hours)
    day_sum = year + month + day
    day_reduced = numerology_reduce(day_sum)
    power_numbers = {1, 8, 9, 11, 22, 33}
    day_master = is_master_number(day_sum)
    if day_master or day_reduced in power_numbers:
        day_s = 0.9
    elif day_reduced in {3, 5, 7}:
        day_s = 0.7
    else:
        day_s = 0.5

    moon_scores = {0: 0.9, 1: 0.5, 2: 0.6, 3: 0.7, 4: 1.0, 5: 0.7, 6: 0.6, 7: 0.4}
    moon_s = moon_scores.get(phase_idx, 0.5)

    weekday_scores = {0: 0.7, 1: 0.5, 2: 0.6, 3: 0.6, 4: 0.9, 5: 0.8, 6: 0.5}
    wd_s = weekday_scores.get(wd_idx, 0.5)

    results = []
    for hour in range(24):
        hour_reduced = numerology_reduce(hour) if hour > 0 else 1
        hour_master = is_master_number(hour)
        if hour_master or hour_reduced in power_numbers:
            hour_s = 0.85
        elif hour_reduced in {3, 5, 7}:
            hour_s = 0.65
        else:
            hour_s = 0.45

        total = (moon_s + day_s + hour_s + wd_s) / 4.0
        results.append((hour, round(total, 4)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def get_cosmic_alignment(key_int):
    """Score how well a key aligns with the current cosmic moment.

    Args:
        key_int: integer key to evaluate.

    Returns:
        float score 0.0 to 1.0.
    """
    from engines.fc60 import compute_jdn, moon_phase, ganzhi_year
    from engines.numerology import numerology_reduce, is_master_number

    now = datetime.now(timezone.utc)
    year, month, day = now.year, now.month, now.day
    hour = now.hour

    # Key properties
    key_digit_sum = sum(int(d) for d in str(abs(key_int)))
    key_reduced = numerology_reduce(key_digit_sum)
    key_is_master = is_master_number(key_int)

    # Moment properties
    jdn = compute_jdn(year, month, day)
    phase_idx, _ = moon_phase(jdn)
    day_sum = year + month + day
    day_reduced = numerology_reduce(day_sum)
    hour_reduced = numerology_reduce(hour) if hour > 0 else 1

    _, branch_idx = ganzhi_year(year)
    year_animal_mod = key_int % 12

    scores = []

    # 1. Key reduced matches day reduced
    if key_reduced == day_reduced:
        scores.append(1.0)
    elif key_reduced + day_reduced == 9:
        scores.append(0.8)
    else:
        scores.append(0.3)

    # 2. Key reduced matches hour reduced
    if key_reduced == hour_reduced:
        scores.append(0.9)
    else:
        scores.append(0.4)

    # 3. Master number alignment
    if key_is_master:
        scores.append(0.9)
    else:
        scores.append(0.4)

    # 4. Moon phase: full moon and new moon favor discovery
    peak_phases = {0, 4}
    good_phases = {3, 5}
    if phase_idx in peak_phases:
        scores.append(0.95)
    elif phase_idx in good_phases:
        scores.append(0.7)
    else:
        scores.append(0.45)

    # 5. Ganzhi year branch alignment
    if year_animal_mod == branch_idx:
        scores.append(1.0)
    else:
        scores.append(0.3)

    alignment = sum(scores) / len(scores) if scores else 0.5
    return round(max(0.0, min(1.0, alignment)), 4)
