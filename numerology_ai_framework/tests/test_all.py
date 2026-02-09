"""
Comprehensive Test Suite - FC60 Numerology AI Framework
========================================================
100+ assertions covering all modules across all tiers.

Run: python3 tests/test_all.py
  or python3 -m unittest tests.test_all
"""

import sys
import os
import unittest
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from core.julian_date_engine import JulianDateEngine
from core.base60_codec import Base60Codec
from core.weekday_calculator import WeekdayCalculator
from core.checksum_validator import ChecksumValidator
from core.fc60_stamp_engine import FC60StampEngine
from personal.numerology_engine import NumerologyEngine
from personal.heartbeat_engine import HeartbeatEngine
from universal.moon_engine import MoonEngine
from universal.ganzhi_engine import GanzhiEngine
from universal.location_engine import LocationEngine
from synthesis.reading_engine import ReadingEngine
from synthesis.universe_translator import UniverseTranslator
from synthesis.master_orchestrator import MasterOrchestrator


class TestJulianDateEngine(unittest.TestCase):
    """Test JDN conversions and round-trips."""

    def test_y2k_epoch(self):
        """Jan 1, 2000 = JDN 2451545."""
        self.assertEqual(JulianDateEngine.gregorian_to_jdn(2000, 1, 1), 2451545)

    def test_unix_epoch(self):
        """Jan 1, 1970 = JDN 2440588."""
        self.assertEqual(JulianDateEngine.gregorian_to_jdn(1970, 1, 1), 2440588)

    def test_round_trip_2026(self):
        """Round-trip 2026-02-09."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 9)
        y, m, d = JulianDateEngine.jdn_to_gregorian(jdn)
        self.assertEqual((y, m, d), (2026, 2, 9))

    def test_leap_year_2024(self):
        """2024-02-29 is valid."""
        self.assertTrue(JulianDateEngine.is_valid_date(2024, 2, 29))
        jdn = JulianDateEngine.gregorian_to_jdn(2024, 2, 29)
        y, m, d = JulianDateEngine.jdn_to_gregorian(jdn)
        self.assertEqual((y, m, d), (2024, 2, 29))

    def test_non_leap_year_2025(self):
        """2025-02-29 is invalid."""
        self.assertFalse(JulianDateEngine.is_valid_date(2025, 2, 29))

    def test_round_trip_batch(self):
        """Round-trip multiple dates."""
        dates = [
            (1990, 7, 15),
            (2000, 6, 15),
            (1999, 12, 31),
            (2026, 1, 1),
            (2024, 2, 29),
            (1970, 1, 1),
            (2030, 12, 31),
            (1900, 1, 1),
            (2099, 6, 30),
        ]
        for y, m, d in dates:
            jdn = JulianDateEngine.gregorian_to_jdn(y, m, d)
            y2, m2, d2 = JulianDateEngine.jdn_to_gregorian(jdn)
            self.assertEqual((y2, m2, d2), (y, m, d), f"Failed for {y}-{m}-{d}")

    def test_consecutive_days(self):
        """Consecutive dates have consecutive JDNs."""
        jdn1 = JulianDateEngine.gregorian_to_jdn(2026, 2, 8)
        jdn2 = JulianDateEngine.gregorian_to_jdn(2026, 2, 9)
        self.assertEqual(jdn2 - jdn1, 1)

    def test_year_boundary(self):
        """Dec 31 → Jan 1 = +1 day."""
        jdn1 = JulianDateEngine.gregorian_to_jdn(2025, 12, 31)
        jdn2 = JulianDateEngine.gregorian_to_jdn(2026, 1, 1)
        self.assertEqual(jdn2 - jdn1, 1)

    def test_invalid_dates(self):
        """Invalid dates rejected."""
        self.assertFalse(JulianDateEngine.is_valid_date(2026, 0, 1))
        self.assertFalse(JulianDateEngine.is_valid_date(2026, 13, 1))
        self.assertFalse(JulianDateEngine.is_valid_date(2026, 2, 30))

    def test_epoch_constants(self):
        """Epoch constants are correct."""
        self.assertEqual(JulianDateEngine.EPOCH_Y2K, 2451545)
        self.assertEqual(JulianDateEngine.EPOCH_UNIX, 2440588)
        self.assertEqual(JulianDateEngine.EPOCH_MJD, 2400001)
        self.assertEqual(JulianDateEngine.EPOCH_RD, 1721425)


class TestBase60Codec(unittest.TestCase):
    """Test base-60 token encoding/decoding."""

    def test_token60_boundaries(self):
        """token60(0)=RAWU, token60(59)=PIWA."""
        self.assertEqual(Base60Codec.token60(0), "RAWU")
        self.assertEqual(Base60Codec.token60(59), "PIWA")

    def test_digit60_roundtrip(self):
        """All 60 tokens round-trip correctly."""
        for i in range(60):
            token = Base60Codec.token60(i)
            self.assertEqual(
                Base60Codec.digit60(token), i, f"Failed for token {token} (index {i})"
            )

    def test_encode_decode_roundtrip(self):
        """Multi-digit encode/decode round-trips."""
        test_values = [0, 1, 59, 60, 3600, 2026, 2451545]
        for val in test_values:
            encoded = Base60Codec.encode_base60(val)
            decoded = Base60Codec.decode_base60(encoded)
            self.assertEqual(decoded, val, f"Failed for {val}: encoded={encoded}")

    def test_encode_2026(self):
        """2026 encodes to HOMT-ROFI."""
        self.assertEqual(Base60Codec.encode_base60(2026), "HOMT-ROFI")

    def test_animals_count(self):
        """12 animals defined."""
        self.assertEqual(len(Base60Codec.ANIMALS), 12)

    def test_elements_count(self):
        """5 elements defined."""
        self.assertEqual(len(Base60Codec.ELEMENTS), 5)

    def test_token_structure(self):
        """Each token is 4 chars: 2 animal + 2 element."""
        for i in range(60):
            token = Base60Codec.token60(i)
            self.assertEqual(len(token), 4)
            self.assertIn(token[:2], Base60Codec.ANIMALS)
            self.assertIn(token[2:], Base60Codec.ELEMENTS)


class TestWeekdayCalculator(unittest.TestCase):
    """Test weekday calculations."""

    def test_known_weekdays(self):
        """Known date-weekday pairs."""
        # 2000-01-01 = Saturday (idx 6)
        jdn = JulianDateEngine.gregorian_to_jdn(2000, 1, 1)
        self.assertEqual(WeekdayCalculator.weekday_from_jdn(jdn), 6)

    def test_weekday_names(self):
        """Seven weekday names defined."""
        self.assertEqual(len(WeekdayCalculator.WEEKDAY_NAMES), 7)
        self.assertEqual(WeekdayCalculator.WEEKDAY_NAMES[0], "Sunday")
        self.assertEqual(WeekdayCalculator.WEEKDAY_NAMES[6], "Saturday")

    def test_weekday_tokens(self):
        """Weekday tokens match spec."""
        expected = ["SO", "LU", "MA", "ME", "JO", "VE", "SA"]
        self.assertEqual(WeekdayCalculator.WEEKDAY_TOKENS, expected)

    def test_seven_day_cycle(self):
        """Seven consecutive days cover all weekdays."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 9)
        weekdays = set()
        for i in range(7):
            weekdays.add(WeekdayCalculator.weekday_from_jdn(jdn + i))
        self.assertEqual(weekdays, {0, 1, 2, 3, 4, 5, 6})

    def test_planets(self):
        """Planets match weekday count."""
        self.assertEqual(len(WeekdayCalculator.PLANETS), 7)

    def test_full_info(self):
        """full_info returns complete dict."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 9)
        info = WeekdayCalculator.full_info(jdn)
        self.assertIn("name", info)
        self.assertIn("planet", info)
        self.assertIn("token", info)


class TestChecksumValidator(unittest.TestCase):
    """Test checksum calculations."""

    def test_chk_tv1(self):
        """TV1: 2026-02-06T01:15:00 → TIMT."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 6)
        chk = ChecksumValidator.calculate_chk(2026, 2, 6, 1, 15, 0, jdn)
        self.assertEqual(chk, "TIMT")

    def test_chk_tv2(self):
        """TV2: 2000-01-01T00:00:00 → RAWU."""
        jdn = JulianDateEngine.gregorian_to_jdn(2000, 1, 1)
        chk = ChecksumValidator.calculate_chk(2000, 1, 1, 0, 0, 0, jdn)
        self.assertEqual(chk, "RAWU")

    def test_chk_tv5(self):
        """TV5: 2025-12-31T23:59:59 → HOWU."""
        jdn = JulianDateEngine.gregorian_to_jdn(2025, 12, 31)
        chk = ChecksumValidator.calculate_chk(2025, 12, 31, 23, 59, 59, jdn)
        self.assertEqual(chk, "HOWU")

    def test_chk_tv7(self):
        """TV7: 2026-01-01T00:00:00 → SNWU."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 1, 1)
        chk = ChecksumValidator.calculate_chk(2026, 1, 1, 0, 0, 0, jdn)
        self.assertEqual(chk, "SNWU")

    def test_chk_tv8(self):
        """TV8: 2026-02-09T00:00:00 → DRWA."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 9)
        chk = ChecksumValidator.calculate_chk(2026, 2, 9, 0, 0, 0, jdn)
        self.assertEqual(chk, "DRWA")

    def test_verify_true(self):
        """Verification with correct CHK passes."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 6)
        self.assertTrue(ChecksumValidator.verify_chk("TIMT", 2026, 2, 6, 1, 15, 0, jdn))

    def test_verify_false(self):
        """Verification with wrong CHK fails."""
        jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 6)
        self.assertFalse(
            ChecksumValidator.verify_chk("RAWU", 2026, 2, 6, 1, 15, 0, jdn)
        )


class TestFC60StampEngine(unittest.TestCase):
    """Test FC60 stamp encoding against all spec test vectors."""

    def test_tv1(self):
        """TV1: 2026-02-06T01:15:00+08:00."""
        r = FC60StampEngine.encode(2026, 2, 6, 1, 15, 0, 8, 0)
        self.assertEqual(r["fc60"], "VE-OX-OXFI \u2600OX-RUWU-RAWU")
        self.assertEqual(r["chk"], "TIMT")
        self.assertEqual(r["y60"], "HOMT-ROFI")
        self.assertEqual(r["y2k"], "SNFI")
        self.assertEqual(r["j60"], "TIFI-DRMT-GOER-PIMT")

    def test_tv2(self):
        """TV2: 2000-01-01T00:00:00Z."""
        r = FC60StampEngine.encode(2000, 1, 1, 0, 0, 0, 0, 0)
        self.assertEqual(r["fc60"], "SA-RA-RAFI \u2600RA-RAWU-RAWU")
        self.assertEqual(r["chk"], "RAWU")
        self.assertEqual(r["y60"], "HOMT-DRWU")

    def test_tv3(self):
        """TV3: 1970-01-01T00:00:00Z."""
        r = FC60StampEngine.encode(1970, 1, 1, 0, 0, 0, 0, 0)
        self.assertEqual(r["fc60"], "JO-RA-RAFI \u2600RA-RAWU-RAWU")
        self.assertEqual(r["y60"], "HOER-DOWU")

    def test_tv4(self):
        """TV4: 2024-02-29T12:00:00Z (leap day)."""
        r = FC60StampEngine.encode(2024, 2, 29, 12, 0, 0, 0, 0)
        self.assertEqual(r["fc60"], "JO-OX-SNWA \U0001f319RA-RAWU-RAWU")
        self.assertEqual(r["chk"], "TIMT")

    def test_tv5(self):
        """TV5: 2025-12-31T23:59:59Z."""
        r = FC60StampEngine.encode(2025, 12, 31, 23, 59, 59, 0, 0)
        self.assertEqual(r["fc60"], "ME-PI-HOFI \U0001f319PI-PIWA-PIWA")
        self.assertEqual(r["chk"], "HOWU")

    def test_tv7(self):
        """TV7: 2026-01-01T00:00:00Z."""
        r = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, 0, 0)
        self.assertEqual(r["fc60"], "JO-RA-RAFI \u2600RA-RAWU-RAWU")
        self.assertEqual(r["chk"], "SNWU")

    def test_tv8(self):
        """TV8: 2026-02-09T00:00:00+08:00."""
        r = FC60StampEngine.encode(2026, 2, 9, 0, 0, 0, 8, 0)
        self.assertEqual(r["fc60"], "LU-OX-OXWA \u2600RA-RAWU-RAWU")
        self.assertEqual(r["chk"], "DRWA")
        self.assertEqual(r["j60"], "TIFI-DRMT-GOMT-RAFI")

    def test_integer_0(self):
        """TV12: Integer 0 → RAWU."""
        self.assertEqual(FC60StampEngine.encode_integer(0), "RAWU")

    def test_integer_59(self):
        """TV13: Integer 59 → PIWA."""
        self.assertEqual(FC60StampEngine.encode_integer(59), "PIWA")

    def test_integer_2026(self):
        """TV14: Integer 2026 → HOMT-ROFI."""
        self.assertEqual(FC60StampEngine.encode_integer(2026), "HOMT-ROFI")

    def test_round_trip_decode(self):
        """TV15: Round-trip encode → decode."""
        r = FC60StampEngine.encode(2026, 2, 6, 1, 15, 0, 8, 0)
        decoded = FC60StampEngine.decode_stamp(r["fc60"])
        self.assertEqual(decoded["weekday_token"], "VE")
        self.assertEqual(decoded["month"], 2)
        self.assertEqual(decoded["day"], 6)
        self.assertEqual(decoded["minute"], 15)
        self.assertEqual(decoded["second"], 0)

    def test_half_am(self):
        """Hour < 12 gives sun marker."""
        r = FC60StampEngine.encode(2026, 1, 1, 5, 0, 0, 0, 0)
        self.assertEqual(r["_half_marker"], "\u2600")

    def test_half_pm(self):
        """Hour >= 12 gives moon marker."""
        r = FC60StampEngine.encode(2026, 1, 1, 15, 0, 0, 0, 0)
        self.assertEqual(r["_half_marker"], "\U0001f319")

    def test_month_encoding(self):
        """Month uses ANIMALS[month-1]: January=RA, December=PI."""
        r_jan = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, 0, 0)
        r_dec = FC60StampEngine.encode(2025, 12, 31, 0, 0, 0, 0, 0)
        self.assertEqual(r_jan["_month_animal"], "RA")
        self.assertEqual(r_dec["_month_animal"], "PI")

    def test_hour_uses_animals(self):
        """Hour field uses 2-char ANIMALS, not token60."""
        r = FC60StampEngine.encode(2026, 1, 1, 1, 0, 0, 0, 0)
        self.assertEqual(r["_hour_animal"], "OX")
        self.assertEqual(len(r["_hour_animal"]), 2)

    def test_date_only_mode(self):
        """Date-only mode has no time component."""
        r = FC60StampEngine.encode(2026, 2, 9, has_time=False)
        self.assertNotIn("\u2600", r["fc60"])
        self.assertNotIn("\U0001f319", r["fc60"])

    def test_timezone_utc(self):
        """UTC timezone → Z."""
        r = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, 0, 0)
        self.assertEqual(r["tz60"], "Z")

    def test_timezone_positive(self):
        """Positive timezone encoding."""
        r = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, 8, 0)
        self.assertTrue(r["tz60"].startswith("+"))

    def test_timezone_negative(self):
        """Negative timezone encoding."""
        r = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, -5, 0)
        self.assertTrue(r["tz60"].startswith("-"))

    def test_iso_format(self):
        """ISO string includes timezone."""
        r = FC60StampEngine.encode(2026, 2, 6, 1, 15, 0, 8, 0)
        self.assertEqual(r["iso"], "2026-02-06T01:15:00+08:00")

    def test_invalid_date_raises(self):
        """Invalid date raises ValueError."""
        with self.assertRaises(ValueError):
            FC60StampEngine.encode(2025, 2, 29, 0, 0, 0, 0, 0)

    def test_internal_fields_present(self):
        """All internal fields present."""
        r = FC60StampEngine.encode(2026, 2, 9, 14, 30, 0, -5, 0)
        for key in [
            "_jdn",
            "_weekday_index",
            "_planet",
            "_domain",
            "_half_marker",
            "_hour_animal",
            "_minute_token",
            "_month_animal",
            "_dom_token",
        ]:
            self.assertIn(key, r, f"Missing internal field: {key}")


class TestMoonEngine(unittest.TestCase):
    """Test lunar phase calculations."""

    def test_reference_new_moon(self):
        """Reference JDN 2451550 is near New Moon."""
        info = MoonEngine.full_moon_info(2451550)
        self.assertIn(info["phase_name"], ["New Moon", "Waning Crescent"])

    def test_known_date(self):
        """JDN 2461078 → Waning Gibbous, age ~19."""
        info = MoonEngine.full_moon_info(2461078)
        self.assertEqual(info["emoji"], "\U0001f316")
        self.assertAlmostEqual(info["age"], 19.05, delta=0.5)

    def test_illumination_new(self):
        """Illumination at age 0 ≈ 0%."""
        self.assertAlmostEqual(MoonEngine.moon_illumination(0.0), 0.0, delta=0.1)

    def test_illumination_full(self):
        """Illumination at age ~14.77 ≈ 100%."""
        self.assertAlmostEqual(MoonEngine.moon_illumination(14.77), 100.0, delta=1.0)

    def test_energy_lookup(self):
        """Phase energy lookup works."""
        self.assertEqual(MoonEngine.moon_energy("Full Moon"), "Culminate")
        self.assertEqual(MoonEngine.moon_energy("New Moon"), "Seed")

    def test_full_info_keys(self):
        """full_moon_info returns all required keys."""
        info = MoonEngine.full_moon_info(2461078)
        for key in [
            "phase_name",
            "emoji",
            "age",
            "illumination",
            "energy",
            "best_for",
            "avoid",
        ]:
            self.assertIn(key, info)


class TestGanzhiEngine(unittest.TestCase):
    """Test sexagenary cycle calculations."""

    def test_year_2020_metal_rat(self):
        info = GanzhiEngine.full_year_info(2020)
        self.assertEqual(info["stem_token"], "GE")
        self.assertEqual(info["branch_token"], "RA")
        self.assertEqual(info["traditional_name"], "Metal Rat")

    def test_year_2024_wood_dragon(self):
        info = GanzhiEngine.full_year_info(2024)
        self.assertEqual(info["stem_token"], "JA")
        self.assertEqual(info["branch_token"], "DR")
        self.assertEqual(info["traditional_name"], "Wood Dragon")

    def test_year_2025_wood_snake(self):
        info = GanzhiEngine.full_year_info(2025)
        self.assertEqual(info["stem_token"], "YI")
        self.assertEqual(info["branch_token"], "SN")

    def test_year_2026_fire_horse(self):
        info = GanzhiEngine.full_year_info(2026)
        self.assertEqual(info["stem_token"], "BI")
        self.assertEqual(info["branch_token"], "HO")
        self.assertEqual(info["element"], "Fire")

    def test_year_2030_metal_dog(self):
        info = GanzhiEngine.full_year_info(2030)
        self.assertEqual(info["stem_token"], "GE")
        self.assertEqual(info["branch_token"], "DO")

    def test_60_year_cycle(self):
        """Same GZ after 60 years."""
        gz1 = GanzhiEngine.year_ganzhi(2024)
        gz2 = GanzhiEngine.year_ganzhi(2084)
        self.assertEqual(gz1, gz2)

    def test_day_ganzhi_returns_valid(self):
        """Day ganzhi indices in valid range."""
        stem, branch = GanzhiEngine.day_ganzhi(2461078)
        self.assertIn(stem, range(10))
        self.assertIn(branch, range(12))

    def test_hour_ganzhi_midnight(self):
        """Hour 0, day stem 0 → branch 0 (Rat)."""
        stem, branch = GanzhiEngine.hour_ganzhi(0, 0)
        self.assertEqual(branch, 0)

    def test_hour_ganzhi_noon(self):
        """Hour 12 → branch 6 (Horse)."""
        _, branch = GanzhiEngine.hour_ganzhi(12, 0)
        self.assertEqual(branch, 6)

    def test_stems_count(self):
        self.assertEqual(len(GanzhiEngine.STEMS), 10)

    def test_animal_names_count(self):
        self.assertEqual(len(GanzhiEngine.ANIMAL_NAMES), 12)

    def test_full_day_info_keys(self):
        """full_day_info has all required keys."""
        info = GanzhiEngine.full_day_info(2461078)
        for key in ["stem_token", "branch_token", "gz_token", "element", "polarity"]:
            self.assertIn(key, info)


class TestLocationEngine(unittest.TestCase):
    """Test location encoding."""

    def test_nyc(self):
        sig = LocationEngine.location_signature(40.7, -74.0)
        self.assertEqual(sig["element"], "Metal")
        self.assertEqual(sig["timezone_estimate"], -5)

    def test_tokyo(self):
        sig = LocationEngine.location_signature(35.7, 139.7)
        self.assertEqual(sig["element"], "Metal")
        self.assertEqual(sig["timezone_estimate"], 9)

    def test_london(self):
        sig = LocationEngine.location_signature(51.5, -0.1)
        self.assertEqual(sig["element"], "Water")
        self.assertEqual(sig["timezone_estimate"], 0)

    def test_cairo(self):
        sig = LocationEngine.location_signature(30.0, 31.2)
        self.assertEqual(sig["element"], "Earth")
        self.assertEqual(sig["timezone_estimate"], 2)

    def test_sao_paulo(self):
        sig = LocationEngine.location_signature(-23.5, -46.6)
        self.assertEqual(sig["element"], "Earth")
        self.assertEqual(sig["timezone_estimate"], -3)

    def test_equator(self):
        sig = LocationEngine.location_signature(0.0, 0.0)
        self.assertEqual(sig["element"], "Fire")
        self.assertEqual(sig["timezone_estimate"], 0)

    def test_hemispheres(self):
        sig = LocationEngine.location_signature(40.7, -74.0)
        self.assertEqual(sig["lat_hemisphere"], "N")
        self.assertEqual(sig["lon_hemisphere"], "W")
        self.assertEqual(sig["lat_polarity"], "Yang")
        self.assertEqual(sig["lon_polarity"], "Yin")

    def test_southern_hemisphere(self):
        sig = LocationEngine.location_signature(-23.5, -46.6)
        self.assertEqual(sig["lat_hemisphere"], "S")
        self.assertEqual(sig["lat_polarity"], "Yin")


class TestHeartbeatEngine(unittest.TestCase):
    """Test heartbeat estimation."""

    def test_bpm_infant(self):
        self.assertEqual(HeartbeatEngine.estimated_bpm(0), 120)

    def test_bpm_adult(self):
        self.assertEqual(HeartbeatEngine.estimated_bpm(25), 70)

    def test_bpm_elderly(self):
        self.assertEqual(HeartbeatEngine.estimated_bpm(80), 78)

    def test_beats_per_day(self):
        self.assertEqual(HeartbeatEngine.beats_per_day(72), 72 * 60 * 24)

    def test_element_mapping(self):
        """BPM mod 5 maps to element."""
        elem = HeartbeatEngine.heartbeat_element(72)
        self.assertEqual(elem, HeartbeatEngine.ELEMENT_NAMES[72 % 5])

    def test_lifetime_beats_positive(self):
        total = HeartbeatEngine.total_lifetime_beats(35)
        self.assertGreater(total, 0)

    def test_profile_estimated(self):
        """Profile with estimated BPM."""
        p = HeartbeatEngine.heartbeat_profile(35)
        self.assertEqual(p["bpm_source"], "estimated")
        self.assertGreater(p["bpm"], 0)

    def test_profile_actual(self):
        """Profile with actual BPM override."""
        p = HeartbeatEngine.heartbeat_profile(35, actual_bpm=68)
        self.assertEqual(p["bpm"], 68)
        self.assertEqual(p["bpm_source"], "actual")


class TestNumerologyEngine(unittest.TestCase):
    """Test numerology calculations."""

    def test_digital_root_basic(self):
        self.assertEqual(NumerologyEngine.digital_root(29), 11)  # 2+9=11 (master)
        self.assertEqual(NumerologyEngine.digital_root(9), 9)
        self.assertEqual(NumerologyEngine.digital_root(38), 11)  # 3+8=11 (master)
        self.assertEqual(NumerologyEngine.digital_root(37), 1)  # 3+7=10→1

    def test_digital_root_master(self):
        """Master numbers preserved."""
        self.assertEqual(NumerologyEngine.digital_root(11), 11)
        self.assertEqual(NumerologyEngine.digital_root(22), 22)
        self.assertEqual(NumerologyEngine.digital_root(33), 33)

    def test_life_path(self):
        """Known life path calculation."""
        lp = NumerologyEngine.life_path(15, 7, 1990)
        self.assertIn(lp, range(1, 34))

    def test_expression_number(self):
        expr = NumerologyEngine.expression_number("Alice Johnson")
        self.assertIn(expr, range(1, 34))

    def test_soul_urge(self):
        su = NumerologyEngine.soul_urge("Alice Johnson")
        self.assertIn(su, range(1, 34))

    def test_personality(self):
        pers = NumerologyEngine.personality_number("Alice Johnson")
        self.assertIn(pers, range(1, 34))

    def test_personal_year(self):
        py = NumerologyEngine.personal_year(7, 15, 2026)
        self.assertIn(py, range(1, 34))

    def test_personal_month(self):
        pm = NumerologyEngine.personal_month(7, 15, 2026, 2)
        self.assertIn(pm, range(1, 34))

    def test_personal_day(self):
        pd = NumerologyEngine.personal_day(7, 15, 2026, 2, 9)
        self.assertIn(pd, range(1, 34))

    def test_gender_polarity(self):
        m = NumerologyEngine._gender_polarity("male")
        f = NumerologyEngine._gender_polarity("female")
        n = NumerologyEngine._gender_polarity(None)
        self.assertEqual(m["label"], "Yang")
        self.assertEqual(f["label"], "Yin")
        self.assertEqual(n["label"], "Neutral")

    def test_complete_profile_keys(self):
        """Complete profile has all expected keys."""
        p = NumerologyEngine.complete_profile("Test User", 1, 1, 2000, 2026, 2, 9)
        for key in [
            "life_path",
            "expression",
            "soul_urge",
            "personality",
            "personal_year",
            "personal_month",
            "personal_day",
            "gender_polarity",
        ]:
            self.assertIn(key, p)

    def test_complete_profile_with_mother(self):
        """Mother name adds mother_influence."""
        p = NumerologyEngine.complete_profile(
            "Test User", 1, 1, 2000, 2026, 2, 9, mother_name="Mary User"
        )
        self.assertIn("mother_influence", p)


class TestReadingEngine(unittest.TestCase):
    """Test reading generation."""

    def test_animal_repetition_detection(self):
        animals = ["OX", "OX", "RA", "OX", "PI"]
        reps = ReadingEngine._detect_animal_repetitions(animals)
        self.assertEqual(len(reps), 1)
        self.assertEqual(reps[0]["animal"], "OX")
        self.assertEqual(reps[0]["count"], 3)
        self.assertEqual(reps[0]["priority"], "Very High")

    def test_time_context_midday(self):
        ctx = ReadingEngine._time_context(14)
        self.assertIn("Midday", ctx["context"])

    def test_sun_moon_paradox(self):
        stamp = {"_half_marker": "\u2600"}
        paradox = ReadingEngine._check_sun_moon_paradox(stamp, 3)
        self.assertIsNotNone(paradox)
        self.assertIn("light", paradox)

    def test_no_paradox_normal(self):
        stamp = {"_half_marker": "\u2600"}
        paradox = ReadingEngine._check_sun_moon_paradox(stamp, 10)
        self.assertIsNone(paradox)

    def test_full_reading_structure(self):
        """Full reading returns all expected keys."""
        mock_stamp = {
            "_planet": "Venus",
            "_domain": "Love",
            "_weekday_name": "Friday",
            "_half_marker": "\u2600",
            "_hour_animal": "OX",
            "_minute_token": "RUWU",
            "_month_animal": "OX",
            "_dom_token": "OXFI",
        }
        reading = ReadingEngine.generate_reading(mock_stamp)
        for key in [
            "opening",
            "core_signal",
            "day_energy",
            "moon_context",
            "signals",
            "animal_repetitions",
            "confidence",
        ]:
            self.assertIn(key, reading)


class TestUniverseTranslator(unittest.TestCase):
    """Test translation to human output."""

    def test_all_sections_present(self):
        """All 9 sections + full_text present."""
        mock_reading = {
            "confidence": 80,
            "core_signal": "Test.",
            "day_energy": "Fire.",
            "moon_context": "Moon.",
            "personal_overlay": "",
            "heartbeat_context": "",
            "location_context": "",
            "year_context": "",
            "paradox": None,
            "signals": [],
            "animal_repetitions": [],
        }
        mock_stamp = {"fc60": "X", "j60": "Y", "y60": "Z", "iso": "2026-01-01"}
        result = UniverseTranslator.translate(mock_reading, mock_stamp)
        for key in [
            "header",
            "universal_address",
            "core_identity",
            "right_now",
            "patterns",
            "message",
            "advice",
            "caution",
            "footer",
            "full_text",
        ]:
            self.assertIn(key, result)

    def test_header_contains_name(self):
        mock_reading = {"confidence": 80, "signals": [], "animal_repetitions": []}
        mock_stamp = {"fc60": "X", "j60": "Y", "y60": "Z"}
        result = UniverseTranslator.translate(
            mock_reading, mock_stamp, person_name="Alice"
        )
        self.assertIn("ALICE", result["header"])

    def test_full_text_not_empty(self):
        mock_reading = {"confidence": 50, "signals": [], "animal_repetitions": []}
        mock_stamp = {"fc60": "X", "j60": "Y", "y60": "Z"}
        result = UniverseTranslator.translate(mock_reading, mock_stamp)
        self.assertGreater(len(result["full_text"]), 100)


class TestMasterOrchestrator(unittest.TestCase):
    """End-to-end orchestrator tests."""

    def test_full_reading(self):
        """Full reading with all inputs."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Alice Johnson",
            birth_day=15,
            birth_month=7,
            birth_year=1990,
            current_date=datetime(2026, 2, 9),
            mother_name="Barbara Johnson",
            gender="female",
            latitude=40.7,
            longitude=-74.0,
            actual_bpm=68,
            current_hour=14,
            current_minute=30,
            current_second=0,
            tz_hours=-5,
            tz_minutes=0,
        )
        self.assertEqual(reading["person"]["name"], "Alice Johnson")
        self.assertIn("life_path", reading["numerology"])
        self.assertIn("fc60", reading["fc60_stamp"])
        self.assertIsNotNone(reading["moon"])
        self.assertIsNotNone(reading["ganzhi"])
        self.assertIsNotNone(reading["heartbeat"])
        self.assertIsNotNone(reading["location"])
        self.assertGreater(len(reading["synthesis"]), 100)

    def test_minimal_reading(self):
        """Minimal reading (name + birthdate only)."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Test User",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
        )
        self.assertEqual(reading["person"]["name"], "Test User")
        self.assertIn("numerology", reading)
        self.assertIsNone(reading["location"])

    def test_stamp_only_mode(self):
        """Stamp-only mode returns just the stamp."""
        result = MasterOrchestrator.generate_reading(
            full_name="",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
            current_hour=14,
            current_minute=30,
            current_second=0,
            mode="stamp_only",
        )
        self.assertIn("fc60_stamp", result)
        self.assertNotIn("numerology", result)

    def test_backward_compat_keys(self):
        """Backward-compatible keys present."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Test User",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
        )
        for key in [
            "person",
            "birth",
            "current",
            "numerology",
            "patterns",
            "confidence",
            "synthesis",
        ]:
            self.assertIn(key, reading)

    def test_confidence_range(self):
        """Confidence between 50 and 95."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Test User",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
        )
        self.assertGreaterEqual(reading["confidence"]["score"], 50)
        self.assertLessEqual(reading["confidence"]["score"], 95)

    def test_age_calculation(self):
        """Age calculation is correct."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Test User",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
        )
        self.assertEqual(reading["person"]["age_years"], 26)

    def test_birth_weekday(self):
        """Birth weekday is computed."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Test User",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
            current_date=datetime(2026, 2, 9),
        )
        self.assertEqual(reading["birth"]["weekday"], "Saturday")


class TestEdgeCases(unittest.TestCase):
    """Edge case tests across modules."""

    def test_leap_day_stamp(self):
        """Leap day 2024-02-29 encodes correctly."""
        r = FC60StampEngine.encode(2024, 2, 29, 12, 0, 0, 0, 0)
        self.assertIn("OX", r["fc60"])  # February = OX

    def test_midnight_stamp(self):
        """Midnight (00:00:00) has sun marker."""
        r = FC60StampEngine.encode(2026, 1, 1, 0, 0, 0, 0, 0)
        self.assertIn("\u2600", r["fc60"])

    def test_end_of_day_stamp(self):
        """23:59:59 has moon marker."""
        r = FC60StampEngine.encode(2026, 1, 1, 23, 59, 59, 0, 0)
        self.assertIn("\U0001f319", r["fc60"])

    def test_year_boundary_reading(self):
        """Reading across year boundary works."""
        reading = MasterOrchestrator.generate_reading(
            full_name="Year Boundary",
            birth_day=31,
            birth_month=12,
            birth_year=1999,
            current_date=datetime(2026, 1, 1),
        )
        self.assertEqual(reading["person"]["age_years"], 26)

    def test_negative_timezone(self):
        """Negative timezone encodes correctly."""
        r = FC60StampEngine.encode(2026, 1, 1, 12, 0, 0, -5, 0)
        self.assertTrue(r["tz60"].startswith("-"))

    def test_moon_phase_all_valid(self):
        """Moon phase for 30 consecutive days are all valid."""
        base_jdn = JulianDateEngine.gregorian_to_jdn(2026, 2, 1)
        valid_phases = set(MoonEngine.PHASE_NAMES)
        for i in range(30):
            info = MoonEngine.full_moon_info(base_jdn + i)
            self.assertIn(info["phase_name"], valid_phases)

    def test_ganzhi_all_hours(self):
        """All 24 hours produce valid ganzhi."""
        for h in range(24):
            stem, branch = GanzhiEngine.hour_ganzhi(h, 0)
            self.assertIn(stem, range(10))
            self.assertIn(branch, range(12))

    def test_location_poles(self):
        """North/South poles encode as Wood."""
        n_pole = LocationEngine.location_signature(90.0, 0.0)
        s_pole = LocationEngine.location_signature(-90.0, 0.0)
        self.assertEqual(n_pole["element"], "Wood")
        self.assertEqual(s_pole["element"], "Wood")

    def test_heartbeat_all_ages(self):
        """BPM estimate for ages 0-100 always positive."""
        for age in range(101):
            bpm = HeartbeatEngine.estimated_bpm(age)
            self.assertGreater(bpm, 0)

    def test_numerology_empty_name_handling(self):
        """Empty name gives 0 for expression."""
        expr = NumerologyEngine.expression_number("")
        self.assertEqual(expr, 0)


if __name__ == "__main__":
    # Count tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    total = suite.countTestCases()
    print(f"Running {total} tests...\n")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
