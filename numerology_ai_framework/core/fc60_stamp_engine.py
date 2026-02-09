"""
FC60 Stamp Engine - Core Tier Module 6
========================================
Purpose: Complete Mode A pipeline — encode dates/times/integers into FC60 stamps
         Implements all 11 steps from §0.1 of the FC60 Master Spec

Critical encoding rules:
  - Month: ANIMALS[month - 1]  (January = RA, index 0)
  - Hour in time stamp: ANIMALS[hour % 12] (2-char), NOT token60
  - CHK uses LOCAL date/time values, not UTC-adjusted
  - HALF: ☀ if hour < 12, 🌙 if hour >= 12
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional

try:
    from .julian_date_engine import JulianDateEngine
    from .base60_codec import Base60Codec
    from .weekday_calculator import WeekdayCalculator
    from .checksum_validator import ChecksumValidator
except ImportError:
    from core.julian_date_engine import JulianDateEngine
    from core.base60_codec import Base60Codec
    from core.weekday_calculator import WeekdayCalculator
    from core.checksum_validator import ChecksumValidator


class FC60StampEngine:
    """Complete FC60 Mode A encoding pipeline."""

    @staticmethod
    def _validate_input(
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        tz_hours: int = 0,
        tz_minutes: int = 0,
    ) -> None:
        """Validate all input parameters."""
        if not JulianDateEngine.is_valid_date(year, month, day):
            raise ValueError(f"Invalid date: {year:04d}-{month:02d}-{day:02d}")
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be 0-23, got {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be 0-59, got {minute}")
        if not (0 <= second <= 59):
            raise ValueError(f"Second must be 0-59, got {second}")
        if not (-12 <= tz_hours <= 14):
            raise ValueError(f"TZ hours must be -12 to +14, got {tz_hours}")
        if not (0 <= abs(tz_minutes) <= 59):
            raise ValueError(f"TZ minutes must be 0-59, got {tz_minutes}")

    @staticmethod
    def _encode_date_stamp(wd_token: str, month: int, day: int) -> str:
        """Step 4: Encode date stamp WD-MO-DOM."""
        mo_token = Base60Codec.ANIMALS[month - 1]  # CRITICAL: month-1
        dom_token = Base60Codec.token60(day)
        return f"{wd_token}-{mo_token}-{dom_token}"

    @staticmethod
    def _encode_time_stamp(hour: int, minute: int, second: int) -> str:
        """Step 5: Encode time stamp HALF+HOUR-MINUTE-SECOND."""
        half = "☀" if hour < 12 else "🌙"
        hour_animal = Base60Codec.ANIMALS[hour % 12]  # CRITICAL: 2-char ANIMALS
        min_token = Base60Codec.token60(minute)
        sec_token = Base60Codec.token60(second)
        return f"{half}{hour_animal}-{min_token}-{sec_token}"

    @staticmethod
    def _encode_timezone(tz_hours: int, tz_minutes: int) -> str:
        """Step 6: Encode timezone."""
        if tz_hours == 0 and tz_minutes == 0:
            return "Z"
        sign = "+" if tz_hours >= 0 else "-"
        h_token = Base60Codec.token60(abs(tz_hours))
        m_token = Base60Codec.token60(abs(tz_minutes))
        return f"{sign}{h_token}-{m_token}"

    @staticmethod
    def _format_iso(
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
        tz_hours: int,
        tz_minutes: int,
        has_time: bool,
    ) -> str:
        """Format ISO-8601 string."""
        if not has_time:
            return f"{year:04d}-{month:02d}-{day:02d}"
        if tz_hours == 0 and tz_minutes == 0:
            tz_str = "Z"
        else:
            sign = "+" if tz_hours >= 0 else "-"
            tz_str = f"{sign}{abs(tz_hours):02d}:{abs(tz_minutes):02d}"
        return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{tz_str}"

    @staticmethod
    def encode(
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        tz_hours: int = 0,
        tz_minutes: int = 0,
        has_time: bool = True,
    ) -> Dict:
        """
        Complete 11-step FC60 Mode A encoding pipeline.

        Args:
            year, month, day: Gregorian date
            hour, minute, second: Time (default 00:00:00)
            tz_hours, tz_minutes: Timezone offset (default UTC)
            has_time: Whether time component is present

        Returns:
            Dict with all FC60 fields and internal metadata
        """
        # Step 1: Validate
        FC60StampEngine._validate_input(
            year, month, day, hour, minute, second, tz_hours, tz_minutes
        )

        # Step 2: JDN (always from LOCAL date, not UTC-adjusted)
        jdn = JulianDateEngine.gregorian_to_jdn(year, month, day)

        # Step 3: Weekday
        wd_idx = WeekdayCalculator.weekday_from_jdn(jdn)
        wd_token = WeekdayCalculator.WEEKDAY_TOKENS[wd_idx]
        wd_name = WeekdayCalculator.WEEKDAY_NAMES[wd_idx]
        planet = WeekdayCalculator.PLANETS[wd_idx]
        domain = WeekdayCalculator.DOMAINS[wd_idx]

        # Step 4: Date stamp
        date_stamp = FC60StampEngine._encode_date_stamp(wd_token, month, day)

        # Step 5: Time stamp
        time_stamp = ""
        if has_time:
            time_stamp = FC60StampEngine._encode_time_stamp(hour, minute, second)

        # Step 6: Timezone
        tz60 = (
            FC60StampEngine._encode_timezone(tz_hours, tz_minutes) if has_time else ""
        )

        # Step 7: Year encoding
        y60 = Base60Codec.encode_base60(year)
        y2k = Base60Codec.token60((year - 2000) % 60)

        # Step 8: J60
        j60 = Base60Codec.encode_base60(jdn)

        # Step 9: Additional cores
        mjd = jdn - JulianDateEngine.EPOCH_MJD
        rd = jdn - JulianDateEngine.EPOCH_RD
        mjd60 = Base60Codec.encode_base60(mjd)
        rd60 = Base60Codec.encode_base60(rd)

        # Unix seconds (from midnight UTC of the date)
        unix_days = jdn - JulianDateEngine.EPOCH_UNIX
        unix_seconds = unix_days * 86400
        if has_time:
            unix_seconds += hour * 3600 + minute * 60 + second
            unix_seconds -= tz_hours * 3600 + tz_minutes * 60
        u60 = Base60Codec.encode_base60(max(0, unix_seconds))

        # Step 10: CHK (uses LOCAL values, not UTC)
        if has_time:
            chk = ChecksumValidator.calculate_chk(
                year, month, day, hour, minute, second, jdn
            )
        else:
            chk = ChecksumValidator.calculate_chk_date_only(year, month, day, jdn)

        # Step 11: Format
        fc60_stamp = f"{date_stamp} {time_stamp}" if has_time else date_stamp
        iso = FC60StampEngine._format_iso(
            year, month, day, hour, minute, second, tz_hours, tz_minutes, has_time
        )

        # Internal metadata for downstream modules
        half_marker = ""
        hour_animal = ""
        minute_token = ""
        if has_time:
            half_marker = "☀" if hour < 12 else "🌙"
            hour_animal = Base60Codec.ANIMALS[hour % 12]
            minute_token = Base60Codec.token60(minute)

        month_animal = Base60Codec.ANIMALS[month - 1]
        dom_token = Base60Codec.token60(day)

        return {
            "fc60": fc60_stamp,
            "iso": iso,
            "tz60": tz60,
            "y60": y60,
            "y2k": y2k,
            "j60": j60,
            "mjd60": mjd60,
            "rd60": rd60,
            "u60": u60,
            "chk": chk,
            # Internal fields for downstream
            "_jdn": jdn,
            "_weekday_index": wd_idx,
            "_weekday_token": wd_token,
            "_weekday_name": wd_name,
            "_planet": planet,
            "_domain": domain,
            "_half_marker": half_marker,
            "_hour_animal": hour_animal,
            "_minute_token": minute_token,
            "_month_animal": month_animal,
            "_dom_token": dom_token,
        }

    @staticmethod
    def encode_integer(n: int) -> str:
        """Convenience: encode an integer to FC60 base-60 tokens."""
        return Base60Codec.encode_base60(n)

    @staticmethod
    def decode_stamp(stamp_str: str) -> Dict:
        """
        Parse an FC60 stamp string back to components.

        Args:
            stamp_str: e.g. "VE-OX-OXFI ☀OX-RUWU-RAWU"

        Returns:
            Dict with parsed components
        """
        result = {}
        parts = stamp_str.split(" ")
        date_part = parts[0]
        time_part = parts[1] if len(parts) > 1 else None

        # Parse date: WD-MO-DOM
        date_tokens = date_part.split("-")
        if len(date_tokens) >= 3:
            result["weekday_token"] = date_tokens[0]
            wd_idx = (
                WeekdayCalculator.WEEKDAY_TOKENS.index(date_tokens[0])
                if date_tokens[0] in WeekdayCalculator.WEEKDAY_TOKENS
                else -1
            )
            result["weekday_name"] = (
                WeekdayCalculator.WEEKDAY_NAMES[wd_idx] if wd_idx >= 0 else "Unknown"
            )

            mo_token = date_tokens[1]
            if mo_token in Base60Codec.ANIMAL_TO_INDEX:
                result["month"] = Base60Codec.ANIMAL_TO_INDEX[mo_token] + 1
            result["month_token"] = mo_token

            dom_token = date_tokens[2]
            result["day"] = Base60Codec.digit60(dom_token)
            result["dom_token"] = dom_token

        # Parse time: HALF+HOUR-MINUTE-SECOND
        if time_part:
            if time_part[0] == "☀":
                result["half"] = "AM"
                time_body = time_part[1:]
            elif time_part[0] == "🌙" or time_part.startswith("\U0001f319"):
                result["half"] = "PM"
                # 🌙 is 4 bytes in UTF-8, but 1 char in Python
                time_body = time_part[1:] if len(time_part[0]) == 1 else time_part[2:]
            else:
                result["half"] = "Unknown"
                time_body = time_part

            time_tokens = time_body.split("-")
            if len(time_tokens) >= 1:
                hour_animal = time_tokens[0]
                if hour_animal in Base60Codec.ANIMAL_TO_INDEX:
                    hour_branch = Base60Codec.ANIMAL_TO_INDEX[hour_animal]
                    result["hour"] = hour_branch + (
                        12 if result.get("half") == "PM" and hour_branch != 0 else 0
                    )
                    if result.get("half") == "PM" and hour_branch == 0:
                        result["hour"] = 12
                    result["hour_animal"] = hour_animal

            if len(time_tokens) >= 2:
                result["minute"] = Base60Codec.digit60(time_tokens[1])
                result["minute_token"] = time_tokens[1]

            if len(time_tokens) >= 3:
                result["second"] = Base60Codec.digit60(time_tokens[2])
                result["second_token"] = time_tokens[2]

        return result


# ===== SELF TEST =====
# Test vectors from §15 of FC60 Master Spec

TEST_VECTORS = [
    # TV1: 2026-02-06T01:15:00+08:00
    {
        "input": (2026, 2, 6, 1, 15, 0, 8, 0),
        "fc60": "VE-OX-OXFI ☀OX-RUWU-RAWU",
        "chk": "TIMT",
        "y60": "HOMT-ROFI",
        "y2k": "SNFI",
        "j60": "TIFI-DRMT-GOER-PIMT",
    },
    # TV2: 2000-01-01T00:00:00Z
    {
        "input": (2000, 1, 1, 0, 0, 0, 0, 0),
        "fc60": "SA-RA-RAFI ☀RA-RAWU-RAWU",
        "chk": "RAWU",
        "y60": "HOMT-DRWU",
        "j60": "TIFI-DRWU-PIWA-OXWU",
    },
    # TV3: 1970-01-01T00:00:00Z
    {
        "input": (1970, 1, 1, 0, 0, 0, 0, 0),
        "fc60": "JO-RA-RAFI ☀RA-RAWU-RAWU",
        "y60": "HOER-DOWU",
        "j60": "TIFI-RUER-PIFI-SNMT",
    },
    # TV4: 2024-02-29T12:00:00Z
    {
        "input": (2024, 2, 29, 12, 0, 0, 0, 0),
        "fc60": "JO-OX-SNWA 🌙RA-RAWU-RAWU",
        "chk": "TIMT",
        "y60": "HOMT-MOWA",
        "j60": "TIFI-DRMT-SNFI-TIWU",
    },
    # TV5: 2025-12-31T23:59:59Z
    {
        "input": (2025, 12, 31, 23, 59, 59, 0, 0),
        "fc60": "ME-PI-HOFI 🌙PI-PIWA-PIWA",
        "chk": "HOWU",
        "y60": "HOMT-ROWU",
        "j60": "TIFI-DRMT-GOER-DRFI",
    },
    # TV7: 2026-01-01T00:00:00Z
    {
        "input": (2026, 1, 1, 0, 0, 0, 0, 0),
        "fc60": "JO-RA-RAFI ☀RA-RAWU-RAWU",
        "chk": "SNWU",
        "y60": "HOMT-ROFI",
        "j60": "TIFI-DRMT-GOER-DRER",
    },
    # TV8: 2026-02-09T00:00:00+08:00
    {
        "input": (2026, 2, 9, 0, 0, 0, 8, 0),
        "fc60": "LU-OX-OXWA ☀RA-RAWU-RAWU",
        "chk": "DRWA",
        "y60": "HOMT-ROFI",
        "j60": "TIFI-DRMT-GOMT-RAFI",
    },
]

# Integer test vectors
INTEGER_VECTORS = [
    (0, "RAWU"),
    (59, "PIWA"),
    (2026, "HOMT-ROFI"),
]


if __name__ == "__main__":
    print("=" * 60)
    print("FC60 STAMP ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test date/time vectors
    for i, tv in enumerate(TEST_VECTORS):
        inp = tv["input"]
        result = FC60StampEngine.encode(*inp)

        ok = True
        errors = []

        if "fc60" in tv and result["fc60"] != tv["fc60"]:
            ok = False
            errors.append(f"FC60: got '{result['fc60']}', expected '{tv['fc60']}'")

        if "chk" in tv and result["chk"] != tv["chk"]:
            ok = False
            errors.append(f"CHK: got '{result['chk']}', expected '{tv['chk']}'")

        if "y60" in tv and result["y60"] != tv["y60"]:
            ok = False
            errors.append(f"Y60: got '{result['y60']}', expected '{tv['y60']}'")

        if "y2k" in tv and result["y2k"] != tv["y2k"]:
            ok = False
            errors.append(f"Y2K: got '{result['y2k']}', expected '{tv['y2k']}'")

        if "j60" in tv and result["j60"] != tv["j60"]:
            ok = False
            errors.append(f"J60: got '{result['j60']}', expected '{tv['j60']}'")

        if ok:
            print(f"✓ TV{i+1}: {result['fc60']}")
            passed += 1
        else:
            print(f"✗ TV{i+1}: {'; '.join(errors)}")
            failed += 1

    # Test integer encoding
    print("\nInteger encoding:")
    for n, expected in INTEGER_VECTORS:
        result = FC60StampEngine.encode_integer(n)
        if result == expected:
            print(f"✓ {n} → {result}")
            passed += 1
        else:
            print(f"✗ {n} → {result} (expected {expected})")
            failed += 1

    # Test round-trip decode (TV15)
    print("\nRound-trip decode:")
    stamp = "VE-OX-OXFI ☀OX-RUWU-RAWU"
    decoded = FC60StampEngine.decode_stamp(stamp)
    rt_ok = (
        decoded.get("weekday_token") == "VE"
        and decoded.get("month") == 2
        and decoded.get("day") == 6
        and decoded.get("minute") == 15
        and decoded.get("second") == 0
    )
    if rt_ok:
        print(
            f"✓ Round-trip: {stamp} → month={decoded['month']}, day={decoded['day']}, "
            f"minute={decoded['minute']}"
        )
        passed += 1
    else:
        print(f"✗ Round-trip failed: {decoded}")
        failed += 1

    # Test date-only (no time)
    print("\nDate-only encoding:")
    result = FC60StampEngine.encode(1999, 4, 22, has_time=False)
    if result["fc60"] == "JO-RU-DRER":
        print(f"✓ 1999-04-22 → {result['fc60']}")
        passed += 1
    else:
        print(f"✗ 1999-04-22 → {result['fc60']} (expected JO-RU-DRER)")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
