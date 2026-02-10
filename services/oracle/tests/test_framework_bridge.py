"""Tests for oracle_service.framework_bridge — the single integration point
between NPS Oracle service and numerology_ai_framework.

Covers:
  - High-level reading functions (generate_single_reading, generate_multi_reading)
  - DB field mapper (map_oracle_user_to_framework_kwargs)
  - Backward-compatible constant re-exports
  - Backward-compatible function wrappers
  - Error handling (FrameworkBridgeError)
"""

import unittest
from datetime import datetime

import oracle_service  # noqa: F401 — triggers sys.path shim

from oracle_service.framework_bridge import (
    # High-level
    generate_single_reading,
    generate_multi_reading,
    map_oracle_user_to_framework_kwargs,
    FrameworkBridgeError,
    # Constants
    ANIMALS,
    ELEMENTS,
    STEMS,
    ANIMAL_NAMES,
    ELEMENT_NAMES,
    STEM_NAMES,
    STEM_CHINESE,
    STEM_ELEMENTS,
    STEM_POLARITY,
    WEEKDAY_NAMES,
    WEEKDAY_PLANETS,
    WEEKDAY_DOMAINS,
    MOON_PHASE_NAMES,
    MOON_PHASE_MEANINGS,
    LETTER_VALUES,
    LIFE_PATH_MEANINGS,
    VOWELS,
    # Functions
    token60,
    digit60,
    encode_base60,
    compute_jdn,
    jdn_to_gregorian,
    weekday_from_jdn,
    encode_fc60,
    ganzhi_year,
    ganzhi_year_name,
    ganzhi_day,
    ganzhi_hour,
    moon_phase,
    moon_illumination,
    numerology_reduce,
    life_path,
    name_to_number,
    name_soul_urge,
    name_personality,
    personal_year,
    digit_sum,
    is_master_number,
    self_test,
    generate_symbolic_reading,
)


class TestConstants(unittest.TestCase):
    """Verify backward-compatible constants are present and correct."""

    def test_animals_length(self):
        self.assertEqual(len(ANIMALS), 12)

    def test_elements_length(self):
        self.assertEqual(len(ELEMENTS), 5)

    def test_stems_length(self):
        self.assertEqual(len(STEMS), 10)

    def test_animal_names_length(self):
        self.assertEqual(len(ANIMAL_NAMES), 12)

    def test_element_names(self):
        self.assertEqual(ELEMENT_NAMES, ["Wood", "Fire", "Earth", "Metal", "Water"])

    def test_stem_names_length(self):
        self.assertEqual(len(STEM_NAMES), 10)

    def test_stem_chinese_length(self):
        self.assertEqual(len(STEM_CHINESE), 10)

    def test_stem_elements_length(self):
        self.assertEqual(len(STEM_ELEMENTS), 10)

    def test_stem_polarity_length(self):
        self.assertEqual(len(STEM_POLARITY), 10)

    def test_weekday_names(self):
        self.assertEqual(len(WEEKDAY_NAMES), 7)
        self.assertIn("Monday", WEEKDAY_NAMES)
        self.assertIn("Sunday", WEEKDAY_NAMES)

    def test_weekday_planets(self):
        self.assertEqual(len(WEEKDAY_PLANETS), 7)

    def test_weekday_domains(self):
        self.assertEqual(len(WEEKDAY_DOMAINS), 7)

    def test_moon_phase_names(self):
        self.assertEqual(len(MOON_PHASE_NAMES), 8)

    def test_moon_phase_meanings(self):
        self.assertEqual(len(MOON_PHASE_MEANINGS), 8)

    def test_letter_values_complete(self):
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.assertIn(c, LETTER_VALUES)
            self.assertIn(LETTER_VALUES[c], range(1, 10))

    def test_life_path_meanings(self):
        for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]:
            self.assertIn(n, LIFE_PATH_MEANINGS)
            self.assertIsInstance(LIFE_PATH_MEANINGS[n], tuple)
            self.assertEqual(len(LIFE_PATH_MEANINGS[n]), 2)

    def test_vowels(self):
        self.assertIn("A", VOWELS)
        self.assertIn("E", VOWELS)
        self.assertIn("I", VOWELS)
        self.assertIn("O", VOWELS)
        self.assertIn("U", VOWELS)


class TestBase60Functions(unittest.TestCase):
    """Base-60 encoding/decoding functions."""

    def test_token60_all_60(self):
        for i in range(60):
            tok = token60(i)
            self.assertEqual(len(tok), 4)

    def test_digit60_roundtrip(self):
        for i in range(60):
            self.assertEqual(digit60(token60(i)), i)

    def test_digit60_invalid(self):
        with self.assertRaises(ValueError):
            digit60("XXXX")

    def test_encode_base60(self):
        result = encode_base60(0)
        self.assertIsInstance(result, str)


class TestJulianDate(unittest.TestCase):
    """Julian Date Engine wrappers."""

    def test_compute_jdn_epoch(self):
        self.assertEqual(compute_jdn(2000, 1, 1), 2451545)

    def test_jdn_roundtrip(self):
        jdn = compute_jdn(2026, 2, 11)
        y, m, d = jdn_to_gregorian(jdn)
        self.assertEqual((y, m, d), (2026, 2, 11))

    def test_weekday_from_jdn(self):
        # 2000-01-01 = Saturday = index 6
        self.assertEqual(weekday_from_jdn(2451545), 6)


class TestFC60Encoding(unittest.TestCase):
    """FC60 stamp encoding wrapper."""

    def test_encode_fc60_keys(self):
        result = encode_fc60(2026, 2, 11, 14, 30, 0, 3, 30)
        self.assertIn("fc60", result)
        self.assertIn("chk", result)
        self.assertIn("jdn", result)
        self.assertIn("weekday_name", result)
        self.assertIn("weekday_planet", result)
        self.assertIn("weekday_domain", result)
        self.assertIn("moon_illumination", result)
        self.assertIn("gz_name", result)

    def test_encode_fc60_no_time(self):
        result = encode_fc60(2026, 2, 11, include_time=False)
        self.assertIn("fc60", result)

    def test_encode_fc60_jdn_value(self):
        result = encode_fc60(2000, 1, 1)
        self.assertEqual(result["jdn"], 2451545)


class TestGanzhi(unittest.TestCase):
    """Ganzhi (Chinese calendar) wrappers."""

    def test_ganzhi_year_range(self):
        stem, branch = ganzhi_year(2026)
        self.assertIn(stem, range(10))
        self.assertIn(branch, range(12))

    def test_ganzhi_year_name(self):
        name = ganzhi_year_name(2026)
        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)

    def test_ganzhi_day(self):
        jdn = compute_jdn(2026, 2, 11)
        stem, branch = ganzhi_day(jdn)
        self.assertIn(stem, range(10))
        self.assertIn(branch, range(12))

    def test_ganzhi_hour(self):
        stem, branch = ganzhi_hour(14, 0)
        self.assertIn(stem, range(10))
        self.assertIn(branch, range(12))


class TestMoon(unittest.TestCase):
    """Moon phase wrappers."""

    def test_moon_phase_returns_tuple(self):
        jdn = compute_jdn(2026, 2, 11)
        result = moon_phase(jdn)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        phase_idx, age = result
        self.assertIn(phase_idx, range(8))
        self.assertGreaterEqual(age, 0)

    def test_moon_illumination_range(self):
        illum = moon_illumination(14.765)  # near full moon
        self.assertGreaterEqual(illum, 0)
        self.assertLessEqual(illum, 100)

    def test_moon_illumination_new(self):
        illum = moon_illumination(0)  # new moon
        self.assertLessEqual(illum, 5)


class TestNumerology(unittest.TestCase):
    """Numerology function wrappers."""

    def test_numerology_reduce_basic(self):
        self.assertEqual(numerology_reduce(29), 11)
        self.assertEqual(numerology_reduce(10), 1)
        self.assertEqual(numerology_reduce(7), 7)

    def test_numerology_reduce_master(self):
        self.assertEqual(numerology_reduce(11), 11)
        self.assertEqual(numerology_reduce(22), 22)
        self.assertEqual(numerology_reduce(33), 33)

    def test_life_path_param_order(self):
        """Verify life_path(year, month, day) backward-compatible order."""
        result = life_path(1990, 7, 15)
        self.assertIn(result, list(range(1, 10)) + [11, 22, 33])

    def test_name_to_number(self):
        self.assertEqual(name_to_number("JOHN"), 2)
        self.assertEqual(name_to_number("DAVE"), 5)

    def test_name_soul_urge(self):
        self.assertEqual(name_soul_urge("JOHN"), 6)

    def test_name_personality(self):
        self.assertEqual(name_personality("JOHN"), 5)

    def test_personal_year(self):
        result = personal_year(1, 15, 2026)
        self.assertIn(result, list(range(1, 10)) + [11, 22, 33])

    def test_digit_sum(self):
        self.assertEqual(digit_sum(123), 6)
        self.assertEqual(digit_sum(999), 27)
        self.assertEqual(digit_sum(0), 0)

    def test_is_master_number(self):
        self.assertTrue(is_master_number(11))
        self.assertTrue(is_master_number(22))
        self.assertTrue(is_master_number(33))
        self.assertFalse(is_master_number(10))
        self.assertFalse(is_master_number(12))


class TestSelfTest(unittest.TestCase):
    """FC60 self-test used by HealthCheck."""

    def test_self_test_passes(self):
        results = self_test()
        self.assertGreater(len(results), 0)
        for desc, passed in results:
            self.assertTrue(passed, f"Failed: {desc}")


class TestSymbolicReading(unittest.TestCase):
    """Symbolic reading string generation."""

    def test_generate_symbolic_reading(self):
        text = generate_symbolic_reading(2026, 2, 11, 14, 30, 0)
        self.assertIn("FC60 Stamp:", text)
        self.assertIn("Day:", text)
        self.assertIn("Moon:", text)
        self.assertIn("Year:", text)


class TestGenerateSingleReading(unittest.TestCase):
    """High-level generate_single_reading function."""

    def test_basic_reading(self):
        result = generate_single_reading(
            full_name="Alice Johnson",
            birth_day=15,
            birth_month=7,
            birth_year=1990,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("confidence", result)

    def test_reading_with_all_params(self):
        result = generate_single_reading(
            full_name="Alice Johnson",
            birth_day=15,
            birth_month=7,
            birth_year=1990,
            current_date=datetime(2026, 2, 11),
            mother_name="Barbara Johnson",
            gender="female",
            latitude=40.7,
            longitude=-74.0,
            heart_rate_bpm=68,
            current_hour=14,
            current_minute=30,
            current_second=0,
            tz_hours=-5,
            tz_minutes=0,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("confidence", result)

    def test_empty_name_raises(self):
        with self.assertRaises(FrameworkBridgeError):
            generate_single_reading(
                full_name="",
                birth_day=15,
                birth_month=7,
                birth_year=1990,
            )

    def test_invalid_month_raises(self):
        with self.assertRaises(FrameworkBridgeError):
            generate_single_reading(
                full_name="Test",
                birth_day=15,
                birth_month=13,
                birth_year=1990,
            )


class TestGenerateMultiReading(unittest.TestCase):
    """Multi-user reading generation."""

    def test_multi_reading(self):
        users = [
            {
                "full_name": "Alice Johnson",
                "birth_day": 15,
                "birth_month": 7,
                "birth_year": 1990,
            },
            {
                "full_name": "Bob Smith",
                "birth_day": 3,
                "birth_month": 11,
                "birth_year": 1985,
            },
        ]
        results = generate_multi_reading(users)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIsInstance(r, dict)
            self.assertIn("confidence", r)


class TestMapOracleUser(unittest.TestCase):
    """DB field mapping utility."""

    def test_map_dict(self):
        user = {
            "name": "Alice",
            "birthday": "1990-07-15",
            "mother_name": "Barbara",
            "gender": "female",
        }
        kwargs = map_oracle_user_to_framework_kwargs(user)
        self.assertEqual(kwargs["full_name"], "Alice")
        self.assertEqual(kwargs["birth_day"], 15)
        self.assertEqual(kwargs["birth_month"], 7)
        self.assertEqual(kwargs["birth_year"], 1990)
        self.assertEqual(kwargs["mother_name"], "Barbara")
        self.assertEqual(kwargs["gender"], "female")

    def test_map_point_coordinates(self):
        user = {
            "name": "Alice",
            "birthday": "1990-07-15",
            "coordinates": "(-74.0,40.7)",
        }
        kwargs = map_oracle_user_to_framework_kwargs(user)
        self.assertAlmostEqual(kwargs["longitude"], -74.0)
        self.assertAlmostEqual(kwargs["latitude"], 40.7)

    def test_map_missing_birthday_raises(self):
        with self.assertRaises(FrameworkBridgeError):
            map_oracle_user_to_framework_kwargs({"name": "Alice"})


if __name__ == "__main__":
    unittest.main()
