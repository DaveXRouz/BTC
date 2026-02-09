#!/usr/bin/env python3
"""
Independent Math Verification Script for FC60 Numerology AI Framework
=====================================================================
Verifies all core mathematical operations against known test vectors
using both independent calculations and cross-checks against the framework.

Exit code 0 = all pass, 1 = any failure.
"""

import sys
import os

# Add project root to path for framework imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.julian_date_engine import JulianDateEngine
from core.base60_codec import Base60Codec
from core.weekday_calculator import WeekdayCalculator
from core.checksum_validator import ChecksumValidator
from core.fc60_stamp_engine import FC60StampEngine

# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------
_total = 0
_passed = 0
_failed = 0


def check(label: str, condition: bool, detail: str = ""):
    """Record a PASS/FAIL result."""
    global _total, _passed, _failed
    _total += 1
    if condition:
        _passed += 1
        print(f"  PASS  {label}")
    else:
        _failed += 1
        msg = f" -- {detail}" if detail else ""
        print(f"  FAIL  {label}{msg}")


def section(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


# ===================================================================
# 1. JDN TEST VECTORS
# ===================================================================
section("1. JDN Test Vectors (6 dates)")

JDN_VECTORS = [
    # (year, month, day, expected_jdn, description)
    (2000, 1, 1, 2451545, "Y2K epoch"),
    (1970, 1, 1, 2440588, "Unix epoch"),
    (2026, 2, 6, 2461078, "Primary test case"),
    (2026, 2, 9, 2461081, "Current date reference"),
    (2024, 2, 29, 2460370, "Leap day 2024"),
    (1999, 4, 22, 2451291, "Birthday reference"),
]


# 1a. Independent Fliegel-Van Flandern implementation (no framework import)
def _independent_greg_to_jdn(year: int, month: int, day: int) -> int:
    """Pure re-implementation of the Fliegel-Van Flandern algorithm."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


for year, month, day, expected_jdn, desc in JDN_VECTORS:
    # Independent calculation
    independent_jdn = _independent_greg_to_jdn(year, month, day)
    check(
        f"JDN independent  {year:04d}-{month:02d}-{day:02d} -> {expected_jdn}",
        independent_jdn == expected_jdn,
        f"got {independent_jdn}",
    )
    # Framework cross-check
    framework_jdn = JulianDateEngine.gregorian_to_jdn(year, month, day)
    check(
        f"JDN framework    {year:04d}-{month:02d}-{day:02d} -> {expected_jdn}",
        framework_jdn == expected_jdn,
        f"got {framework_jdn}",
    )
    # Round-trip
    rt_year, rt_month, rt_day = JulianDateEngine.jdn_to_gregorian(expected_jdn)
    check(
        f"JDN round-trip   {year:04d}-{month:02d}-{day:02d}",
        (rt_year, rt_month, rt_day) == (year, month, day),
        f"got {rt_year}-{rt_month:02d}-{rt_day:02d}",
    )


# ===================================================================
# 2. WEEKDAY CORRECTNESS
# ===================================================================
section("2. Weekday Correctness (planet abbreviation system)")

# Weekday tokens: 0=SO(Sun), 1=LU(Moon), 2=MA(Mars), 3=ME(Mercury),
#                 4=JO(Jupiter), 5=VE(Venus), 6=SA(Saturn)
# Formula: (JDN + 1) % 7

WEEKDAY_VECTORS = [
    # (year, month, day, jdn, expected_token)
    (2000, 1, 1, 2451545, "SA"),  # Saturday
    (1970, 1, 1, 2440588, "JO"),  # Thursday
    (2026, 2, 6, 2461078, "VE"),  # Friday
    (2026, 2, 9, 2461081, "LU"),  # Monday
    (2024, 2, 29, 2460370, "JO"),  # Thursday
    (1999, 4, 22, 2451291, "JO"),  # Thursday
]

WEEKDAY_TOKENS = ["SO", "LU", "MA", "ME", "JO", "VE", "SA"]

for year, month, day, jdn, expected_token in WEEKDAY_VECTORS:
    # Independent calculation
    idx = (jdn + 1) % 7
    independent_token = WEEKDAY_TOKENS[idx]
    check(
        f"Weekday independent {year:04d}-{month:02d}-{day:02d} -> {expected_token}",
        independent_token == expected_token,
        f"got {independent_token} (idx={idx})",
    )
    # Framework cross-check
    framework_token = WeekdayCalculator.weekday_token(jdn)
    check(
        f"Weekday framework  {year:04d}-{month:02d}-{day:02d} -> {expected_token}",
        framework_token == expected_token,
        f"got {framework_token}",
    )


# ===================================================================
# 3. CROSS-CHECK: MJD, RD, and their relationships
# ===================================================================
section("3. Cross-Check: MJD = JDN - 2400001, RD = JDN - 1721425, MJD = RD - 678576")

EPOCH_MJD = 2400001
EPOCH_RD = 1721425

for year, month, day, jdn, _desc in JDN_VECTORS:
    mjd = jdn - EPOCH_MJD
    rd = jdn - EPOCH_RD

    # Check MJD definition
    check(
        f"MJD({jdn}) = {mjd}",
        mjd == JulianDateEngine.jdn_to_mjd(jdn),
        f"framework gives {JulianDateEngine.jdn_to_mjd(jdn)}",
    )
    # Check RD definition
    check(
        f"RD({jdn})  = {rd}",
        rd == JulianDateEngine.jdn_to_rd(jdn),
        f"framework gives {JulianDateEngine.jdn_to_rd(jdn)}",
    )
    # Check identity: MJD = RD - 678576
    check(
        f"MJD = RD - 678576 for JDN {jdn}",
        mjd == rd - 678576,
        f"MJD={mjd}, RD-678576={rd - 678576}",
    )


# ===================================================================
# 4. CHK TOKEN VERIFICATIONS (TV1, TV7, TV8)
# ===================================================================
section("4. CHK Token Verifications (TV1, TV7, TV8)")

# CHK = (1*year%60 + 2*month + 3*day + 4*hour + 5*minute + 6*second + 7*JDN%60) mod 60

ANIMALS = ["RA", "OX", "TI", "RU", "DR", "SN", "HO", "GO", "MO", "RO", "DO", "PI"]
ELEMENTS = ["WU", "FI", "ER", "MT", "WA"]


def _independent_token60(n: int) -> str:
    """Independent token60 re-implementation."""
    return ANIMALS[n // 5] + ELEMENTS[n % 5]


def _independent_chk(year, month, day, hour, minute, second, jdn):
    """Independent CHK calculation."""
    val = (
        1 * (year % 60)
        + 2 * month
        + 3 * day
        + 4 * hour
        + 5 * minute
        + 6 * second
        + 7 * (jdn % 60)
    ) % 60
    return _independent_token60(val)


CHK_VECTORS = [
    # (label, year, month, day, hour, minute, second, jdn, expected_chk)
    ("TV1", 2026, 2, 6, 1, 15, 0, 2461078, "TIMT"),
    ("TV7", 2026, 1, 1, 0, 0, 0, 2461042, "SNWU"),
    ("TV8", 2026, 2, 9, 0, 0, 0, 2461081, "DRWA"),
]

for label, year, month, day, hour, minute, second, jdn, expected_chk in CHK_VECTORS:
    # Independent calculation
    ind_chk = _independent_chk(year, month, day, hour, minute, second, jdn)
    check(
        f"CHK independent  {label}: {year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d} -> {expected_chk}",
        ind_chk == expected_chk,
        f"got {ind_chk}",
    )
    # Framework cross-check
    fw_chk = ChecksumValidator.calculate_chk(
        year, month, day, hour, minute, second, jdn
    )
    check(
        f"CHK framework    {label}: {year}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d} -> {expected_chk}",
        fw_chk == expected_chk,
        f"got {fw_chk}",
    )

# Show the arithmetic for each CHK (informational)
print("\n  --- CHK arithmetic breakdown ---")
for label, year, month, day, hour, minute, second, jdn, expected_chk in CHK_VECTORS:
    terms = [
        1 * (year % 60),
        2 * month,
        3 * day,
        4 * hour,
        5 * minute,
        6 * second,
        7 * (jdn % 60),
    ]
    raw = sum(terms)
    mod = raw % 60
    print(
        f"  {label}: 1*{year%60} + 2*{month} + 3*{day} + 4*{hour} + 5*{minute} "
        f"+ 6*{second} + 7*{jdn%60} = {raw} mod 60 = {mod} -> {_independent_token60(mod)}"
    )


# ===================================================================
# 5. MONTH ENCODING RULE: January = RA = ANIMALS[0]
# ===================================================================
section("5. Month Encoding Rule: January = RA = ANIMALS[0]")

# Verify ANIMALS list from framework
fw_animals = Base60Codec.ANIMALS
check(
    "ANIMALS list has 12 entries",
    len(fw_animals) == 12,
    f"got {len(fw_animals)}",
)
check(
    "ANIMALS[0] = 'RA' (Rat)",
    fw_animals[0] == "RA",
    f"got {fw_animals[0]}",
)
check(
    "January (month=1) -> ANIMALS[1-1] = ANIMALS[0] = RA",
    fw_animals[1 - 1] == "RA",
)

# Verify for all 12 months
EXPECTED_MONTH_ANIMALS = [
    (1, "RA"),  # January
    (2, "OX"),  # February
    (3, "TI"),  # March
    (4, "RU"),  # April
    (5, "DR"),  # May
    (6, "SN"),  # June
    (7, "HO"),  # July
    (8, "GO"),  # August
    (9, "MO"),  # September
    (10, "RO"),  # October
    (11, "DO"),  # November
    (12, "PI"),  # December
]

for month_num, expected_animal in EXPECTED_MONTH_ANIMALS:
    actual = fw_animals[month_num - 1]
    check(
        f"Month {month_num:2d} -> ANIMALS[{month_num-1}] = {expected_animal}",
        actual == expected_animal,
        f"got {actual}",
    )

# Verify via FC60StampEngine (spot check TV1: month=2 -> OX)
tv1_result = FC60StampEngine.encode(2026, 2, 6, 1, 15, 0, 8, 0)
check(
    "TV1 stamp month animal = OX (February)",
    tv1_result["_month_animal"] == "OX",
    f"got {tv1_result['_month_animal']}",
)


# ===================================================================
# 6. HOUR ENCODING RULE: 2-char ANIMALS[hour % 12]
# ===================================================================
section("6. Hour Encoding Rule: 2-char ANIMALS[hour % 12]")

# The hour field in the FC60 time stamp uses the 2-character animal code,
# NOT the 4-character token60. hour_animal = ANIMALS[hour % 12]

HOUR_VECTORS = [
    (0, "RA"),  # midnight
    (1, "OX"),
    (6, "HO"),
    (11, "PI"),
    (12, "RA"),  # noon wraps to RA again
    (13, "OX"),
    (14, "TI"),
    (23, "PI"),
]

for hour, expected_animal in HOUR_VECTORS:
    independent = ANIMALS[hour % 12]
    check(
        f"Hour {hour:2d} -> ANIMALS[{hour}%12] = ANIMALS[{hour%12}] = {expected_animal} (2-char)",
        independent == expected_animal and len(independent) == 2,
        f"got {independent} (len={len(independent)})",
    )

# Framework cross-check via FC60StampEngine
# TV1: hour=1 -> ANIMALS[1] = OX
check(
    "TV1 hour_animal = OX (hour=1)",
    tv1_result["_hour_animal"] == "OX",
    f"got {tv1_result['_hour_animal']}",
)

# TV8: hour=0 -> ANIMALS[0] = RA
tv8_result = FC60StampEngine.encode(2026, 2, 9, 0, 0, 0, 8, 0)
check(
    "TV8 hour_animal = RA (hour=0)",
    tv8_result["_hour_animal"] == "RA",
    f"got {tv8_result['_hour_animal']}",
)

# Verify that the hour field in the stamp string is 2 chars (not 4)
# TV1 stamp: "VE-OX-OXFI ☀OX-RUWU-RAWU"
# The time part after ☀ starts with "OX" (2 chars), not "OXWU" (4 chars)
stamp_str = tv1_result["fc60"]
time_part = stamp_str.split(" ")[1]  # "☀OX-RUWU-RAWU"
# After the ☀ marker, first token before '-' is the hour animal
hour_in_stamp = time_part[1:].split("-")[0]  # skip ☀, take first segment
check(
    f"TV1 stamp hour field is 2-char: '{hour_in_stamp}'",
    len(hour_in_stamp) == 2 and hour_in_stamp == "OX",
    f"got '{hour_in_stamp}' (len={len(hour_in_stamp)})",
)


# ===================================================================
# 7. HALF MARKER: sun (U+2600) if hour<12, moon (U+1F319) if hour>=12
# ===================================================================
section("7. HALF Marker: sun if hour<12, moon if hour>=12")

SUN = "\u2600"  # ☀
MOON = "\U0001f319"  # 🌙

HALF_VECTORS = [
    (0, SUN, "midnight"),
    (1, SUN, "1 AM"),
    (6, SUN, "6 AM"),
    (11, SUN, "11 AM"),
    (12, MOON, "noon"),
    (13, MOON, "1 PM"),
    (18, MOON, "6 PM"),
    (23, MOON, "11 PM"),
]

for hour, expected_marker, desc in HALF_VECTORS:
    independent = SUN if hour < 12 else MOON
    check(
        f"HALF hour={hour:2d} ({desc:>8s}) -> {'SUN' if expected_marker == SUN else 'MOON'}",
        independent == expected_marker,
    )

# Framework cross-checks
check(
    "TV1 (hour=1) half_marker = SUN",
    tv1_result["_half_marker"] == SUN,
    f"got repr={repr(tv1_result['_half_marker'])}",
)

# TV4: hour=12 -> MOON
tv4_result = FC60StampEngine.encode(2024, 2, 29, 12, 0, 0, 0, 0)
check(
    "TV4 (hour=12) half_marker = MOON",
    tv4_result["_half_marker"] == MOON,
    f"got repr={repr(tv4_result['_half_marker'])}",
)

# TV5: hour=23 -> MOON
tv5_result = FC60StampEngine.encode(2025, 12, 31, 23, 59, 59, 0, 0)
check(
    "TV5 (hour=23) half_marker = MOON",
    tv5_result["_half_marker"] == MOON,
    f"got repr={repr(tv5_result['_half_marker'])}",
)

# Verify Unicode code points
check(
    "SUN marker is U+2600",
    ord(SUN) == 0x2600,
    f"got U+{ord(SUN):04X}",
)
check(
    "MOON marker is U+1F319",
    ord(MOON) == 0x1F319,
    f"got U+{ord(MOON):04X}",
)


# ===================================================================
# SUMMARY
# ===================================================================
section("SUMMARY")
print(f"  Total:  {_total}")
print(f"  Passed: {_passed}")
print(f"  Failed: {_failed}")
print()

if _failed == 0:
    print("  ALL CHECKS PASSED")
else:
    print(f"  {_failed} CHECK(S) FAILED")

sys.exit(0 if _failed == 0 else 1)
