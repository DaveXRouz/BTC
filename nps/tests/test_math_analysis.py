"""Tests for the math analysis engine."""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.math_analysis import (
    entropy,
    is_prime,
    prime_factors,
    palindrome_score,
    digit_frequency,
    digit_balance,
    math_profile,
)


class TestEntropy(unittest.TestCase):

    def test_all_same(self):
        self.assertAlmostEqual(entropy(111111), 0.0)

    def test_all_different(self):
        self.assertAlmostEqual(entropy(123456), 2.585, places=2)

    def test_single_digit(self):
        self.assertEqual(entropy(5), 0.0)


class TestPrime(unittest.TestCase):

    def test_7_is_prime(self):
        self.assertTrue(is_prime(7))

    def test_8_not_prime(self):
        self.assertFalse(is_prime(8))

    def test_2_is_prime(self):
        self.assertTrue(is_prime(2))

    def test_1_not_prime(self):
        self.assertFalse(is_prime(1))


class TestPrimeFactors(unittest.TestCase):

    def test_60(self):
        self.assertEqual(prime_factors(60), [2, 2, 3, 5])

    def test_prime_number(self):
        self.assertEqual(prime_factors(7), [7])

    def test_one(self):
        self.assertEqual(prime_factors(1), [])


class TestPalindromeScore(unittest.TestCase):

    def test_perfect_palindrome(self):
        self.assertAlmostEqual(palindrome_score(12321), 1.0)

    def test_not_palindrome(self):
        self.assertAlmostEqual(palindrome_score(12345), 0.0)

    def test_single_digit(self):
        self.assertAlmostEqual(palindrome_score(5), 1.0)


class TestMathProfile(unittest.TestCase):

    def test_returns_dict(self):
        profile = math_profile(42)
        self.assertIn("entropy", profile)
        self.assertIn("is_prime", profile)
        self.assertIn("palindrome_score", profile)

    def test_handles_zero(self):
        profile = math_profile(0)
        self.assertIsNotNone(profile)

    def test_handles_large(self):
        profile = math_profile(10**15)
        self.assertIsNotNone(profile)


if __name__ == "__main__":
    unittest.main()
