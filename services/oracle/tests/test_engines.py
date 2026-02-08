"""Engine parity tests — verify V3 engines work correctly under V4 import paths."""

import unittest

import oracle_service  # triggers sys.path shim

from engines.fc60 import (
    token60,
    digit60,
    compute_jdn,
    weekday_from_jdn,
    encode_fc60,
    self_test,
    ganzhi_year,
    moon_phase,
    WEEKDAY_NAMES,
)
from engines.numerology import (
    numerology_reduce,
    name_to_number,
    name_soul_urge,
    name_personality,
    life_path,
    personal_year,
    is_master_number,
    LETTER_VALUES,
)
from engines.oracle import read_sign, read_name, question_sign, daily_insight


class TestFC60Engine(unittest.TestCase):
    """FC60 engine parity with V3 test vectors."""

    def test_token60_roundtrip(self):
        """All 60 tokens encode/decode correctly."""
        for i in range(60):
            tok = token60(i)
            self.assertEqual(len(tok), 4, f"Token {i} length != 4: {tok}")
            self.assertEqual(digit60(tok), i, f"Round-trip failed for {i}")

    def test_jdn_vectors(self):
        """JDN matches known astronomical values."""
        vectors = [
            (2000, 1, 1, 2451545),
            (2026, 2, 6, 2461078),
            (1970, 1, 1, 2440588),
        ]
        for y, m, d, expected in vectors:
            self.assertEqual(
                compute_jdn(y, m, d), expected, f"JDN failed for {y}-{m}-{d}"
            )

    def test_weekday_vectors(self):
        """Weekday from JDN matches known days."""
        # 2000-01-01 was Saturday (idx 6)
        self.assertEqual(weekday_from_jdn(2451545), 6)
        self.assertEqual(WEEKDAY_NAMES[6], "Saturday")
        # 1970-01-01 was Thursday (idx 4)
        self.assertEqual(weekday_from_jdn(2440588), 4)

    def test_self_test_all_pass(self):
        """Built-in self_test() passes all 29 vectors."""
        results = self_test()
        self.assertEqual(len(results), 29)
        for name, passed, detail in results:
            self.assertTrue(passed, f"self_test failed: {name} — {detail}")

    def test_encode_fc60_returns_dict(self):
        """encode_fc60 returns dict with expected keys."""
        result = encode_fc60(2026, 2, 8)
        required_keys = [
            "stamp",
            "iso",
            "jdn",
            "moon_phase",
            "moon_name",
            "gz_name",
            "weekday_name",
            "chk",
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_ganzhi_year(self):
        """Ganzhi year indices are in range."""
        stem, branch = ganzhi_year(2026)
        self.assertIn(stem, range(10))
        self.assertIn(branch, range(12))

    def test_moon_phase_range(self):
        """Moon phase index is 0-7."""
        jdn = compute_jdn(2026, 2, 8)
        phase_idx, age = moon_phase(jdn)
        self.assertIn(phase_idx, range(8))
        self.assertGreaterEqual(age, 0)


class TestNumerologyEngine(unittest.TestCase):
    """Numerology engine parity with V3."""

    def test_reduce_basic(self):
        self.assertEqual(numerology_reduce(29), 11)  # master number preserved
        self.assertEqual(numerology_reduce(38), 11)  # 3+8=11 master
        self.assertEqual(numerology_reduce(10), 1)
        self.assertEqual(numerology_reduce(7), 7)

    def test_reduce_master_numbers(self):
        self.assertEqual(numerology_reduce(11), 11)
        self.assertEqual(numerology_reduce(22), 22)
        self.assertEqual(numerology_reduce(33), 33)

    def test_name_to_number(self):
        # J=1 + O=6 + H=8 + N=5 = 20 -> 2
        self.assertEqual(name_to_number("JOHN"), 2)
        # D=4 + A=1 + V=4 + E=5 = 14 -> 5
        self.assertEqual(name_to_number("DAVE"), 5)

    def test_name_soul_urge(self):
        # Vowels in JOHN: O=6 -> 6
        self.assertEqual(name_soul_urge("JOHN"), 6)

    def test_name_personality(self):
        # Consonants in JOHN: J=1, H=8, N=5 = 14 -> 5
        self.assertEqual(name_personality("JOHN"), 5)

    def test_life_path_range(self):
        result = life_path(1990, 1, 15)
        self.assertIn(result, list(range(1, 10)) + [11, 22, 33])

    def test_personal_year(self):
        result = personal_year(1, 15, 2026)
        self.assertIn(result, list(range(1, 10)) + [11, 22, 33])

    def test_is_master_number(self):
        self.assertTrue(is_master_number(11))
        self.assertTrue(is_master_number(22))
        self.assertTrue(is_master_number(33))
        self.assertFalse(is_master_number(10))

    def test_letter_values_complete(self):
        """All 26 letters have values 1-9."""
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.assertIn(c, LETTER_VALUES)
            self.assertIn(LETTER_VALUES[c], range(1, 10))


class TestOracleEngine(unittest.TestCase):
    """Oracle engine parity with V3."""

    def test_read_sign_structure(self):
        result = read_sign("11:11")
        self.assertIsInstance(result, dict)
        self.assertIn("systems", result)
        self.assertIn("interpretation", result)
        self.assertIn("sign", result)
        self.assertEqual(result["sign"], "11:11")

    def test_read_sign_with_date(self):
        result = read_sign("777", date="2026-02-08", time_str="14:30")
        self.assertIn("systems", result)
        self.assertIsInstance(result["systems"], dict)

    def test_read_name_structure(self):
        result = read_name("DAVE")
        self.assertIn("expression", result)
        self.assertIn("soul_urge", result)
        self.assertIn("personality", result)
        self.assertEqual(result["expression"], 5)

    def test_read_name_empty(self):
        result = read_name("")
        self.assertIn("error", result)

    def test_question_sign_structure(self):
        result = question_sign("test")
        self.assertIsInstance(result, dict)
        self.assertIn("question", result)
        self.assertIn("reading", result)
        self.assertIn("advice", result)

    def test_daily_insight_structure(self):
        result = daily_insight()
        self.assertIsInstance(result, dict)
        self.assertIn("date", result)
        self.assertIn("insight", result)
        self.assertIn("lucky_numbers", result)
        self.assertIsInstance(result["lucky_numbers"], list)


if __name__ == "__main__":
    unittest.main()
