"""
Numerology Engine
=================
Pythagorean numerology functions extracted from v1 fc60_engine.py,
plus new helper functions for digit analysis, master-number detection,
number vibration profiling, and compatibility scoring.

Integrates with engines.fc60 for FC60 token / animal / element lookups.
"""

import logging

from engines.fc60 import (
    compute_jdn,
    weekday_from_jdn,
    token60,
    ganzhi_year_name,
    generate_symbolic_reading,
    WEEKDAYS,
    ANIMALS,
    WEEKDAY_NAMES,
    WEEKDAY_PLANETS,
    WEEKDAY_DOMAINS,
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Constants (from v1 fc60_engine.py lines 160-181)
# ════════════════════════════════════════════════════════════

LETTER_VALUES = {
    "A": 1,
    "B": 2,
    "C": 3,
    "D": 4,
    "E": 5,
    "F": 6,
    "G": 7,
    "H": 8,
    "I": 9,
    "J": 1,
    "K": 2,
    "L": 3,
    "M": 4,
    "N": 5,
    "O": 6,
    "P": 7,
    "Q": 8,
    "R": 9,
    "S": 1,
    "T": 2,
    "U": 3,
    "V": 4,
    "W": 5,
    "X": 6,
    "Y": 7,
    "Z": 8,
}

VOWELS = set("AEIOU")

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


# ════════════════════════════════════════════════════════════
# V1 Numerology Functions (from v1 fc60_engine.py)
# ════════════════════════════════════════════════════════════


def numerology_reduce(n):
    """Reduce to single digit, preserving master numbers 11, 22, 33."""
    if n in (11, 22, 33):
        return n
    while n > 9:
        n = sum(int(d) for d in str(n))
        if n in (11, 22, 33):
            return n
    return n


def name_to_number(name):
    """Sum letter values of a name -> reduced number."""
    total = sum(LETTER_VALUES.get(c, 0) for c in name.upper())
    return numerology_reduce(total)


def name_soul_urge(name):
    """Sum vowels only -> reduced number."""
    total = sum(LETTER_VALUES.get(c, 0) for c in name.upper() if c in VOWELS)
    return numerology_reduce(total)


def name_personality(name):
    """Sum consonants only -> reduced number."""
    total = sum(
        LETTER_VALUES.get(c, 0) for c in name.upper() if c.isalpha() and c not in VOWELS
    )
    return numerology_reduce(total)


def life_path(year, month, day):
    """Calculate Life Path number from birth date."""
    d_red = numerology_reduce(day)
    m_red = numerology_reduce(month)
    y_red = numerology_reduce(sum(int(c) for c in str(year)))
    return numerology_reduce(d_red + m_red + y_red)


def personal_year(birth_month, birth_day, current_year):
    """Calculate Personal Year number."""
    return numerology_reduce(
        numerology_reduce(birth_month)
        + numerology_reduce(birth_day)
        + numerology_reduce(sum(int(c) for c in str(current_year)))
    )


def generate_personal_reading(
    name,
    birth_year,
    birth_month,
    birth_day,
    current_year,
    current_month,
    current_day,
    current_hour=0,
    current_minute=0,
    mother_name=None,
):
    """
    Generate a personal numerology + FC60 reading.
    Returns a multi-line string.
    """
    lines = []

    # -- Numerology --
    lp = life_path(birth_year, birth_month, birth_day)
    expr = name_to_number(name)
    soul = name_soul_urge(name)
    pers = name_personality(name)
    py = personal_year(birth_month, birth_day, current_year)

    lp_title, lp_msg = LIFE_PATH_MEANINGS.get(lp, ("Unknown", ""))
    py_title, py_msg = LIFE_PATH_MEANINGS.get(py, ("Unknown", ""))

    lines.append("═══ PERSONAL NUMEROLOGY ═══")
    lines.append(f"  Life Path:   {lp} — {lp_title}: {lp_msg}")
    lines.append(f"  Expression:  {expr}")
    lines.append(f"  Soul Urge:   {soul}")
    lines.append(f"  Personality: {pers}")
    lines.append(f"  Personal Year ({current_year}): {py} — {py_title}: {py_msg}")

    if mother_name:
        mother_num = name_to_number(mother_name)
        m_title, m_msg = LIFE_PATH_MEANINGS.get(mother_num, ("Unknown", ""))
        lines.append(
            f"  Mother's influence ({mother_name}): {mother_num} — {m_title}: {m_msg}"
        )

    lines.append("")

    # -- Birth FC60 --
    birth_jdn = compute_jdn(birth_year, birth_month, birth_day)
    birth_wd = weekday_from_jdn(birth_jdn)
    birth_stamp = (
        f"{WEEKDAYS[birth_wd]}-{ANIMALS[birth_month - 1]}-{token60(birth_day)}"
    )
    lines.append(f"Birth stamp: {birth_stamp}")
    lines.append(f"  Born on a {WEEKDAY_NAMES[birth_wd]} ({WEEKDAY_PLANETS[birth_wd]})")
    lines.append(f"  Birth domain: {WEEKDAY_DOMAINS[birth_wd]}")

    birth_gz = ganzhi_year_name(birth_year)
    lines.append(f"  Birth year: {birth_gz}")
    lines.append("")

    # -- Current moment --
    lines.append("═══ CURRENT MOMENT ═══")
    symbolic = generate_symbolic_reading(
        current_year, current_month, current_day, current_hour, current_minute
    )
    lines.append(symbolic)

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
# New Numerology Functions
# ════════════════════════════════════════════════════════════


def digit_sum(n: int) -> int:
    """Sum all digits of n. Example: 347 -> 3+4+7 = 14."""
    return sum(int(d) for d in str(abs(n)))


def digit_sum_reduced(n: int) -> int:
    """digit_sum but reduced via numerology_reduce. 347 -> 14 -> 5."""
    return numerology_reduce(digit_sum(n))


def is_master_number(n: int) -> bool:
    """True if n itself is 11/22/33 or reduces through 11/22/33 at any stage."""
    if n in (11, 22, 33):
        return True
    total = digit_sum(n)
    while total > 9:
        if total in (11, 22, 33):
            return True
        total = sum(int(d) for d in str(total))
    return total in (11, 22, 33)


def number_vibration(n: int) -> dict:
    """
    Complete numerological profile of any integer.
    """
    from engines.fc60 import (
        token60,
        ANIMAL_NAMES,
        ELEMENT_NAMES,
        ANIMAL_POWER,
        ELEMENT_FORCE,
    )

    mod60 = n % 60
    animal_idx = mod60 // 5
    element_idx = mod60 % 5
    reduced = numerology_reduce(digit_sum(n))

    return {
        "digit_sum": digit_sum(n),
        "reduced": reduced,
        "is_master": is_master_number(n),
        "life_path_meaning": LIFE_PATH_MEANINGS.get(reduced),
        "fc60_token": token60(mod60),
        "fc60_animal": ANIMAL_NAMES[animal_idx],
        "fc60_element": ELEMENT_NAMES[element_idx],
        "fc60_animal_power": ANIMAL_POWER[animal_idx],
        "fc60_element_force": ELEMENT_FORCE[element_idx],
    }


def compatibility_score(num_a: int, num_b: int) -> float:
    """
    How compatible are two numbers in numerological terms.
    0.0 = opposite, 1.0 = perfect match.
    """
    from engines.fc60 import ANIMALS, ELEMENTS

    red_a = numerology_reduce(digit_sum(num_a))
    red_b = numerology_reduce(digit_sum(num_b))

    score = 0.3  # base

    # Same reduced number
    if red_a == red_b:
        return 1.0

    # Completion pair (sum to 9)
    if red_a + red_b == 9:
        score = 0.8

    # Master number + its base
    master_pairs = {(11, 2), (2, 11), (22, 4), (4, 22), (33, 6), (6, 33)}
    if (red_a, red_b) in master_pairs:
        score = 0.9

    # FC60 animal match bonus
    animal_a = ANIMALS[(num_a % 60) // 5]
    animal_b = ANIMALS[(num_b % 60) // 5]
    if animal_a == animal_b:
        score = min(1.0, score + 0.2)

    # FC60 element match bonus
    element_a = ELEMENTS[(num_a % 60) % 5]
    element_b = ELEMENTS[(num_b % 60) % 5]
    if element_a == element_b:
        score = min(1.0, score + 0.1)

    return score
