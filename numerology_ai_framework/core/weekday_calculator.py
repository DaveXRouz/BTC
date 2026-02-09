"""
Weekday Calculator - Core Tier Module 3
========================================
Purpose: Calculate weekday from Julian Day Number
         Never guess - always calculate deterministically

Weekday Index Mapping:
0 = Sunday (Sun ☉)
1 = Monday (Moon ☽)
2 = Tuesday (Mars ♂)
3 = Wednesday (Mercury ☿)
4 = Thursday (Jupiter ♃)
5 = Friday (Venus ♀)
6 = Saturday (Saturn ♄)
"""

from typing import Tuple


class WeekdayCalculator:
    """Calculate weekday from JDN with planetary associations."""
    
    WEEKDAY_TOKENS = ["SO", "LU", "MA", "ME", "JO", "VE", "SA"]
    WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    DOMAINS = [
        "Identity, vitality, core self",
        "Emotions, intuition, inner world",
        "Drive, action, courage",
        "Communication, thought, connection",
        "Expansion, wisdom, abundance",
        "Love, values, beauty",
        "Discipline, lessons, mastery"
    ]
    
    @staticmethod
    def weekday_from_jdn(jdn: int) -> int:
        """
        Calculate weekday index from Julian Day Number.
        
        Formula: (JDN + 1) mod 7
        
        Args:
            jdn: Julian Day Number
            
        Returns:
            Weekday index (0=Sunday ... 6=Saturday)
        """
        return (jdn + 1) % 7
    
    @staticmethod
    def weekday_token(jdn: int) -> str:
        """Get FC60 weekday token from JDN."""
        idx = WeekdayCalculator.weekday_from_jdn(jdn)
        return WeekdayCalculator.WEEKDAY_TOKENS[idx]
    
    @staticmethod
    def weekday_name(jdn: int) -> str:
        """Get full weekday name from JDN."""
        idx = WeekdayCalculator.weekday_from_jdn(jdn)
        return WeekdayCalculator.WEEKDAY_NAMES[idx]
    
    @staticmethod
    def planet_name(jdn: int) -> str:
        """Get ruling planet name from JDN."""
        idx = WeekdayCalculator.weekday_from_jdn(jdn)
        return WeekdayCalculator.PLANETS[idx]
    
    @staticmethod
    def symbolic_domain(jdn: int) -> str:
        """Get symbolic domain for this weekday."""
        idx = WeekdayCalculator.weekday_from_jdn(jdn)
        return WeekdayCalculator.DOMAINS[idx]
    
    @staticmethod
    def full_info(jdn: int) -> dict:
        """Get complete weekday information."""
        idx = WeekdayCalculator.weekday_from_jdn(jdn)
        return {
            'index': idx,
            'token': WeekdayCalculator.WEEKDAY_TOKENS[idx],
            'name': WeekdayCalculator.WEEKDAY_NAMES[idx],
            'planet': WeekdayCalculator.PLANETS[idx],
            'domain': WeekdayCalculator.DOMAINS[idx]
        }


# Test vectors (JDN, expected_index, expected_token, expected_name)
TEST_VECTORS = [
    (2451545, 6, "SA", "Saturday"),   # 2000-01-01
    (2440588, 4, "JO", "Thursday"),   # 1970-01-01
    (2461078, 5, "VE", "Friday"),     # 2026-02-06
    (2461081, 1, "LU", "Monday"),     # 2026-02-09
]


if __name__ == "__main__":
    print("=" * 60)
    print("WEEKDAY CALCULATOR - SELF TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for jdn, exp_idx, exp_token, exp_name in TEST_VECTORS:
        info = WeekdayCalculator.full_info(jdn)
        
        if info['index'] == exp_idx and info['token'] == exp_token and info['name'] == exp_name:
            print(f"✓ JDN {jdn}: {info['token']} ({info['name']}) - {info['planet']}")
            passed += 1
        else:
            print(f"✗ JDN {jdn}: got {info['token']}/{info['name']}, expected {exp_token}/{exp_name}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
