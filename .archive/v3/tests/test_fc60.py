"""Tests for the FC60 engine."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.fc60 import (
    token60,
    digit60,
    to_base60,
    from_base60,
    encode_base60,
    decode_base60,
    compute_jdn,
    jdn_to_gregorian,
    weekday_from_jdn,
    weekday_token,
    ganzhi_year_tokens,
    encode_fc60,
    self_test,
)


class TestToken60(unittest.TestCase):
    """Round-trip encoding/decoding for all 60 tokens."""

    def test_round_trip_0_to_59(self):
        for i in range(60):
            tok = token60(i)
            decoded = digit60(tok)
            self.assertEqual(decoded, i, f"Failed at {i}: {tok} -> {decoded}")

    def test_specific_tokens(self):
        self.assertEqual(token60(0), "RAWU")
        self.assertEqual(token60(26), "SNFI")
        self.assertEqual(token60(57), "PIER")
        self.assertEqual(token60(59), "PIWA")


class TestBase60(unittest.TestCase):
    """Base-60 round-trip for various numbers."""

    def test_round_trip(self):
        test_nums = [0, 1, 59, 60, 3600, 2461072, 999999]
        for n in test_nums:
            encoded = encode_base60(n)
            decoded = decode_base60(encoded)
            self.assertEqual(decoded, n, f"Failed for {n}: encoded={encoded}")


class TestJDN(unittest.TestCase):
    """Julian Day Number test vectors."""

    def test_jdn_vectors(self):
        self.assertEqual(compute_jdn(2000, 1, 1), 2451545)
        self.assertEqual(compute_jdn(2026, 2, 6), 2461078)
        self.assertEqual(compute_jdn(1970, 1, 1), 2440588)

    def test_jdn_inverse_round_trip(self):
        tests = [(2000, 1, 1, 2451545), (2026, 2, 6, 2461078), (1970, 1, 1, 2440588)]
        for y, m, d, jdn_val in tests:
            ry, rm, rd = jdn_to_gregorian(jdn_val)
            self.assertEqual((ry, rm, rd), (y, m, d))


class TestWeekday(unittest.TestCase):
    """Weekday test vectors."""

    def test_weekday_vectors(self):
        tests = [
            (2000, 1, 1, "SA"),
            (2026, 2, 6, "VE"),
            (2026, 4, 22, "ME"),
            (1999, 4, 22, "JO"),
        ]
        for y, m, d, expected in tests:
            jdn = compute_jdn(y, m, d)
            got = weekday_token(jdn)
            self.assertEqual(
                got,
                expected,
                f"Weekday {y}-{m:02d}-{d:02d}: expected {expected}, got {got}",
            )


class TestGanzhi(unittest.TestCase):
    """Ganzhi year test vectors."""

    def test_ganzhi_vectors(self):
        tests = [
            (2024, "JA", "DR"),
            (2025, "YI", "SN"),
            (2026, "BI", "HO"),
        ]
        for y, exp_stem, exp_branch in tests:
            stem, branch = ganzhi_year_tokens(y)
            self.assertEqual(stem, exp_stem)
            self.assertEqual(branch, exp_branch)


class TestSelfTest(unittest.TestCase):
    """Run all 29 built-in V1 test vectors."""

    def test_all_vectors_pass(self):
        results = self_test()
        for test_name, passed, detail in results:
            self.assertTrue(passed, f"FAILED: {test_name} — {detail}")


class TestFullEncode(unittest.TestCase):
    """Test full FC60 encoding."""

    def test_2026_02_06(self):
        result = encode_fc60(2026, 2, 6, 1, 15, 0, 8, 0)
        self.assertEqual(result["stamp"], "VE-OX-OXFI ☀OX-RUWU-RAWU")


if __name__ == "__main__":
    unittest.main()
