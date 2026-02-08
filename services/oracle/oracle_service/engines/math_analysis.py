"""
Math Analysis Engine
====================
Provides mathematical analysis of numbers independent of numerology.
These functions detect REAL patterns: entropy, prime structure, digit distribution.
Combined with numerology scoring, they create the hybrid scoring system.

Zero external dependencies — pure Python stdlib.
"""

import math
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def entropy(n: int) -> float:
    """
    Shannon entropy of the digit sequence of n.
    Low entropy (< 1.5) = very patterned (like 111111, 123123)
    Medium entropy (1.5-2.5) = somewhat structured
    High entropy (> 2.5) = appears random
    Returns: float (0.0 to ~3.32 for base-10 digits)
    """
    digits = str(abs(n))
    if len(digits) <= 1:
        return 0.0
    counts = Counter(digits)
    total = len(digits)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())


def digit_frequency(n: int) -> dict:
    """Count how often each digit (0-9) appears in n."""
    digits = str(abs(n))
    freq = {str(i): 0 for i in range(10)}
    for d in digits:
        freq[d] += 1
    return freq


def digit_balance(n: int) -> float:
    """
    How evenly distributed are the digits?
    1.0 = perfectly balanced, 0.0 = maximally imbalanced.
    """
    freq = digit_frequency(n)
    present = [v for v in freq.values() if v > 0]
    if len(present) <= 1:
        return 0.0
    mean = sum(present) / len(present)
    variance = sum((x - mean) ** 2 for x in present) / len(present)
    std = math.sqrt(variance)
    if mean == 0:
        return 0.0
    cv = std / mean
    return max(0.0, 1.0 - cv / 2.0)


def prime_factors(n: int) -> list:
    """
    Return list of prime factors (with repetition).
    Example: prime_factors(60) -> [2, 2, 3, 5]
    """
    if n <= 1:
        return []
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def is_prime(n: int) -> bool:
    """Simple primality test. Works well for n < 10^12."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def modular_properties(n: int) -> dict:
    """Properties of n relative to base-60 (the FC60 base)."""
    return {
        'mod60': n % 60,
        'mod12': n % 12,
        'mod5': n % 5,
        'mod10': n % 10,
        'divides_60': (60 % n == 0) if n > 0 else False,
        'divisible_by_60': (n % 60 == 0) if n > 0 else False,
        'gcd_with_60': math.gcd(abs(n), 60),
    }


def repeating_patterns(n: int) -> list:
    """
    Detect repeating digit patterns in n.
    Returns list of (pattern, count) tuples.
    """
    s = str(abs(n))
    patterns = []
    for length in range(1, len(s) // 2 + 1):
        pattern = s[:length]
        count = 0
        for i in range(0, len(s), length):
            if s[i:i+length] == pattern:
                count += 1
            else:
                break
        if count >= 2 and count * length == len(s):
            patterns.append((pattern, count))
    return patterns


def palindrome_score(n: int) -> float:
    """
    How close to a palindrome is n?
    1.0 = perfect palindrome, 0.0 = no palindromic similarity.
    """
    s = str(abs(n))
    if len(s) <= 1:
        return 1.0
    matches = 0
    total = len(s) // 2
    for i in range(total):
        if s[i] == s[-(i+1)]:
            matches += 1
    return matches / total if total > 0 else 1.0


def math_profile(n: int) -> dict:
    """Complete mathematical profile of any integer."""
    return {
        'value': n,
        'num_digits': len(str(abs(n))),
        'entropy': entropy(n),
        'digit_balance': digit_balance(n),
        'digit_frequency': digit_frequency(n),
        'is_prime': is_prime(n) if n < 10**12 else None,
        'prime_factors': prime_factors(n) if n < 10**9 else [],
        'modular': modular_properties(n),
        'repeating_patterns': repeating_patterns(n),
        'palindrome_score': palindrome_score(n),
        'is_even': n % 2 == 0,
        'is_power_of_2': (n > 0) and (n & (n - 1) == 0),
    }
