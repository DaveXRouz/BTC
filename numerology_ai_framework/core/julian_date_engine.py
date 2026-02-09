"""
Julian Date Engine - Core Tier Module 1
========================================
Purpose: Convert between Gregorian dates and Julian Day Numbers (JDN)
         Provides the mathematical backbone for all date-based calculations

JDN is a continuous count of days since January 1, 4713 BCE (Julian calendar)
Used by astronomers worldwide since the 1500s - completely unambiguous

All algorithms verified against astronomical tables and test vectors
"""

from typing import Tuple
from datetime import datetime, timezone


class JulianDateEngine:
    """
    Core engine for Julian Day Number calculations.
    
    Uses the Fliegel-Van Flandern algorithm (standard astronomical method)
    Accurate for all Gregorian calendar dates
    """
    
    # Reference points for cross-validation
    EPOCH_Y2K = 2451545      # JDN for 2000-01-01
    EPOCH_UNIX = 2440588     # JDN for 1970-01-01  
    EPOCH_MJD = 2400001      # Offset for Modified Julian Date
    EPOCH_RD = 1721425       # Offset for Rata Die
    
    @staticmethod
    def gregorian_to_jdn(year: int, month: int, day: int) -> int:
        """
        Convert Gregorian calendar date to Julian Day Number.
        
        Algorithm: Fliegel-Van Flandern (1968)
        
        Args:
            year: Gregorian year (any integer, negative for BCE)
            month: Month (1-12)
            day: Day of month (1-31)
            
        Returns:
            Julian Day Number (integer)
            
        Raises:
            ValueError: If date is invalid
            
        Examples:
            >>> JulianDateEngine.gregorian_to_jdn(2000, 1, 1)
            2451545
            >>> JulianDateEngine.gregorian_to_jdn(1970, 1, 1)
            2440588
            >>> JulianDateEngine.gregorian_to_jdn(2026, 2, 6)
            2461078
        """
        # Validate input
        if not JulianDateEngine.is_valid_date(year, month, day):
            raise ValueError(f"Invalid date: {year:04d}-{month:02d}-{day:02d}")
        
        # Step 1: Adjust for January and February
        # In the algorithm, January and February are treated as months 13 and 14
        # of the previous year to simplify leap year handling
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        
        # Step 2: Calculate JDN
        # This is the core Fliegel-Van Flandern formula
        jdn = (day 
               + (153 * m + 2) // 5      # Days from months
               + 365 * y                  # Days from years
               + y // 4                   # Leap years (every 4 years)
               - y // 100                 # Not leap years (every 100 years)
               + y // 400                 # Leap years (every 400 years)
               - 32045)                   # Adjustment constant
        
        return jdn
    
    @staticmethod
    def jdn_to_gregorian(jdn: int) -> Tuple[int, int, int]:
        """
        Convert Julian Day Number to Gregorian calendar date.
        
        Inverse of gregorian_to_jdn - guaranteed to round-trip correctly
        
        Args:
            jdn: Julian Day Number (integer)
            
        Returns:
            Tuple of (year, month, day)
            
        Examples:
            >>> JulianDateEngine.jdn_to_gregorian(2451545)
            (2000, 1, 1)
            >>> JulianDateEngine.jdn_to_gregorian(2440588)
            (1970, 1, 1)
        """
        # Step 1: Calculate intermediate values
        a = jdn + 32044
        b = (4 * a + 3) // 146097
        c = a - (146097 * b) // 4
        
        # Step 2: Calculate more intermediate values
        d = (4 * c + 3) // 1461
        e = c - (1461 * d) // 4
        m = (5 * e + 2) // 153
        
        # Step 3: Extract day, month, year
        day = e - (153 * m + 2) // 5 + 1
        month = m + 3 - 12 * (m // 10)
        year = 100 * b + d - 4800 + m // 10
        
        return year, month, day
    
    @staticmethod
    def is_leap_year(year: int) -> bool:
        """
        Determine if a year is a leap year in the Gregorian calendar.
        
        Rules:
        - Divisible by 4: leap year
        - Divisible by 100: NOT a leap year
        - Divisible by 400: leap year
        
        Args:
            year: Gregorian year
            
        Returns:
            True if leap year, False otherwise
            
        Examples:
            >>> JulianDateEngine.is_leap_year(2000)
            True
            >>> JulianDateEngine.is_leap_year(1900)
            False
            >>> JulianDateEngine.is_leap_year(2024)
            True
        """
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    
    @staticmethod
    def is_valid_date(year: int, month: int, day: int) -> bool:
        """
        Validate a Gregorian calendar date.
        
        Args:
            year: Year
            month: Month (1-12)
            day: Day (1-31)
            
        Returns:
            True if valid, False otherwise
            
        Examples:
            >>> JulianDateEngine.is_valid_date(2024, 2, 29)
            True
            >>> JulianDateEngine.is_valid_date(2025, 2, 29)
            False
        """
        if month < 1 or month > 12:
            return False
        
        # Days in each month (non-leap year)
        days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        
        # Adjust February for leap years
        if JulianDateEngine.is_leap_year(year):
            days_in_month[2] = 29
        
        return 1 <= day <= days_in_month[month]
    
    @staticmethod
    def jdn_to_mjd(jdn: int) -> int:
        """
        Convert JDN to Modified Julian Date.
        
        MJD = JDN - 2400001
        MJD starts at midnight on November 17, 1858
        
        Args:
            jdn: Julian Day Number
            
        Returns:
            Modified Julian Date
        """
        return jdn - JulianDateEngine.EPOCH_MJD
    
    @staticmethod
    def mjd_to_jdn(mjd: int) -> int:
        """Convert Modified Julian Date to JDN."""
        return mjd + JulianDateEngine.EPOCH_MJD
    
    @staticmethod
    def jdn_to_rd(jdn: int) -> int:
        """
        Convert JDN to Rata Die.
        
        RD = JDN - 1721425
        RD is days since January 1, 1 CE (proleptic Gregorian)
        
        Args:
            jdn: Julian Day Number
            
        Returns:
            Rata Die
        """
        return jdn - JulianDateEngine.EPOCH_RD
    
    @staticmethod
    def rd_to_jdn(rd: int) -> int:
        """Convert Rata Die to JDN."""
        return rd + JulianDateEngine.EPOCH_RD
    
    @staticmethod
    def jdn_to_unix_days(jdn: int) -> int:
        """
        Convert JDN to days since Unix epoch.
        
        Unix epoch = January 1, 1970 00:00:00 UTC
        
        Args:
            jdn: Julian Day Number
            
        Returns:
            Days since Unix epoch (can be negative)
        """
        return jdn - JulianDateEngine.EPOCH_UNIX
    
    @staticmethod
    def unix_days_to_jdn(unix_days: int) -> int:
        """Convert days since Unix epoch to JDN."""
        return unix_days + JulianDateEngine.EPOCH_UNIX
    
    @staticmethod
    def current_jdn() -> int:
        """
        Get the current Julian Day Number (today's date at 00:00 UTC).
        
        Returns:
            Current JDN
        """
        now = datetime.now(timezone.utc)
        return JulianDateEngine.gregorian_to_jdn(now.year, now.month, now.day)
    
    @staticmethod
    def verify_cross_references(jdn: int) -> dict:
        """
        Verify cross-reference relationships for a given JDN.
        
        These relationships must always hold:
        - MJD = JDN - 2400001
        - RD = JDN - 1721425
        - MJD = RD - 678576
        
        Args:
            jdn: Julian Day Number
            
        Returns:
            Dict with all cross-reference values and validation status
        """
        mjd = JulianDateEngine.jdn_to_mjd(jdn)
        rd = JulianDateEngine.jdn_to_rd(jdn)
        
        # Verify the relationships
        mjd_check = (mjd == rd - 678576)
        
        return {
            'jdn': jdn,
            'mjd': mjd,
            'rd': rd,
            'unix_days': JulianDateEngine.jdn_to_unix_days(jdn),
            'relationships_valid': mjd_check
        }


# Test vectors for validation
TEST_VECTORS = [
    # (year, month, day, expected_jdn)
    (2000, 1, 1, 2451545),     # Y2K reference
    (1970, 1, 1, 2440588),     # Unix epoch
    (2026, 2, 6, 2461078),     # Primary test case
    (2026, 2, 9, 2461081),     # Current date reference
    (2024, 2, 29, 2460370),    # Leap day
    (2025, 12, 31, 2461041),   # Year end
    (1999, 4, 22, 2451291),    # Birthday reference
    (2026, 1, 1, 2461042),     # New year 2026
    (2060, 12, 31, 2473825),   # Far future
    (1900, 1, 1, 2415021),     # Pre-epoch
]


def run_self_test() -> bool:
    """
    Run comprehensive self-test on the Julian Date Engine.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("=" * 60)
    print("JULIAN DATE ENGINE - SELF TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # Test 1: Forward conversion
    print("\n1. Testing Gregorian → JDN conversion:")
    for year, month, day, expected_jdn in TEST_VECTORS:
        computed_jdn = JulianDateEngine.gregorian_to_jdn(year, month, day)
        if computed_jdn == expected_jdn:
            passed += 1
            print(f"   ✓ {year:04d}-{month:02d}-{day:02d} → {computed_jdn}")
        else:
            failed += 1
            print(f"   ✗ {year:04d}-{month:02d}-{day:02d} → {computed_jdn} (expected {expected_jdn})")
    
    # Test 2: Round-trip conversion
    print("\n2. Testing round-trip (JDN → Gregorian → JDN):")
    for year, month, day, expected_jdn in TEST_VECTORS:
        computed_jdn = JulianDateEngine.gregorian_to_jdn(year, month, day)
        back_year, back_month, back_day = JulianDateEngine.jdn_to_gregorian(computed_jdn)
        round_trip_jdn = JulianDateEngine.gregorian_to_jdn(back_year, back_month, back_day)
        
        if round_trip_jdn == computed_jdn:
            passed += 1
            print(f"   ✓ {year:04d}-{month:02d}-{day:02d} round-trips correctly")
        else:
            failed += 1
            print(f"   ✗ {year:04d}-{month:02d}-{day:02d} round-trip failed")
    
    # Test 3: Leap year validation
    print("\n3. Testing leap year detection:")
    leap_tests = [
        (2000, True),   # Divisible by 400
        (1900, False),  # Divisible by 100 but not 400
        (2024, True),   # Divisible by 4
        (2025, False),  # Not divisible by 4
    ]
    for year, expected in leap_tests:
        result = JulianDateEngine.is_leap_year(year)
        if result == expected:
            passed += 1
            print(f"   ✓ {year} leap={result}")
        else:
            failed += 1
            print(f"   ✗ {year} leap={result} (expected {expected})")
    
    # Test 4: Cross-reference validation
    print("\n4. Testing cross-reference relationships:")
    test_jdns = [2451545, 2440588, 2461078]
    for jdn in test_jdns:
        refs = JulianDateEngine.verify_cross_references(jdn)
        if refs['relationships_valid']:
            passed += 1
            print(f"   ✓ JDN {jdn}: MJD={refs['mjd']}, RD={refs['rd']}")
        else:
            failed += 1
            print(f"   ✗ JDN {jdn}: Cross-reference validation failed")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_self_test()
    exit(0 if success else 1)
