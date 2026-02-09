"""
Checksum Validator - Core Tier Module 5
========================================
Purpose: Generate and validate weighted checksums for error detection
         Uses position-weighted factors inspired by Luhn algorithm

Weighted Formula:
CHK = (1×year%60 + 2×month + 3×day + 4×hour + 5×minute + 6×second + 7×JDN%60) mod 60
"""

try:
    from .base60_codec import Base60Codec
except ImportError:
    from base60_codec import Base60Codec


class ChecksumValidator:
    """Weighted checksum calculator for FC60 timestamps."""
    
    @staticmethod
    def calculate_chk(year: int, month: int, day: int, hour: int = 0, 
                     minute: int = 0, second: int = 0, jdn: int = None) -> str:
        """
        Calculate weighted checksum token.
        
        Args:
            year: Gregorian year
            month: Month (1-12)
            day: Day (1-31)
            hour: Hour (0-23), default 0
            minute: Minute (0-59), default 0
            second: Second (0-59), default 0
            jdn: Julian Day Number (required)
            
        Returns:
            4-character CHK token
        """
        if jdn is None:
            raise ValueError("JDN is required for checksum calculation")
        
        chk_value = (
            1 * (year % 60) +
            2 * month +
            3 * day +
            4 * hour +
            5 * minute +
            6 * second +
            7 * (jdn % 60)
        ) % 60
        
        return Base60Codec.token60(chk_value)
    
    @staticmethod
    def calculate_chk_date_only(year: int, month: int, day: int, jdn: int) -> str:
        """Calculate CHK for date-only (no time component)."""
        chk_value = (
            1 * (year % 60) +
            2 * month +
            3 * day +
            7 * (jdn % 60)
        ) % 60
        
        return Base60Codec.token60(chk_value)
    
    @staticmethod
    def verify_chk(expected_chk: str, year: int, month: int, day: int,
                   hour: int = 0, minute: int = 0, second: int = 0, jdn: int = None) -> bool:
        """
        Verify a checksum token.
        
        Returns:
            True if checksum matches, False otherwise
        """
        computed_chk = ChecksumValidator.calculate_chk(year, month, day, hour, minute, second, jdn)
        return computed_chk == expected_chk.upper()


# Test vectors: (year, month, day, hour, minute, second, jdn, expected_chk)
TEST_VECTORS = [
    (2026, 2, 6, 1, 15, 0, 2461078, "TIMT"),
    (2025, 12, 31, 23, 59, 59, 2461041, "HOWU"),
    (2026, 1, 1, 0, 0, 0, 2461042, "SNWU"),
    (2026, 2, 9, 0, 0, 0, 2461081, "DRWA"),
]


if __name__ == "__main__":
    print("=" * 60)
    print("CHECKSUM VALIDATOR - SELF TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for year, month, day, hour, minute, second, jdn, expected in TEST_VECTORS:
        computed = ChecksumValidator.calculate_chk(year, month, day, hour, minute, second, jdn)
        
        if computed == expected:
            print(f"✓ {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d} → {computed}")
            passed += 1
        else:
            print(f"✗ Expected {expected}, got {computed}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
