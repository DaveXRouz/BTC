"""Tests for the numerology engine."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.numerology import (
    numerology_reduce,
    name_to_number,
    name_soul_urge,
    name_personality,
    life_path,
    is_master_number,
    digit_sum,
    digit_sum_reduced,
)


class TestNumerologyReduce(unittest.TestCase):

    def test_master_11(self):
        self.assertEqual(numerology_reduce(29), 11)

    def test_master_11_from_38(self):
        self.assertEqual(numerology_reduce(38), 11)

    def test_simple_reduce(self):
        self.assertEqual(numerology_reduce(15), 6)

    def test_single_digit(self):
        self.assertEqual(numerology_reduce(7), 7)


class TestNameToNumber(unittest.TestCase):

    def test_dave(self):
        # D=4, A=1, V=4, E=5 -> 14 -> 5
        self.assertEqual(name_to_number("DAVE"), 5)


class TestIsMasterNumber(unittest.TestCase):

    def test_29_is_master(self):
        self.assertTrue(is_master_number(29))  # 2+9=11

    def test_13_not_master(self):
        self.assertFalse(is_master_number(13))  # 1+3=4

    def test_22_is_master(self):
        self.assertTrue(is_master_number(22))


class TestDigitSum(unittest.TestCase):

    def test_347(self):
        self.assertEqual(digit_sum(347), 14)

    def test_digit_sum_reduced(self):
        self.assertEqual(digit_sum_reduced(347), 5)


class TestLifePath(unittest.TestCase):

    def test_basic(self):
        lp = life_path(1990, 1, 15)
        self.assertIsInstance(lp, int)
        self.assertTrue(1 <= lp <= 33)


if __name__ == "__main__":
    unittest.main()
