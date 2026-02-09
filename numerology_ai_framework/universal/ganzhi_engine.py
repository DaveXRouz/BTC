"""
Ganzhi Engine - Universal Tier Module 2
========================================
Purpose: Calculate the Chinese Sexagenary Cycle (干支 Gānzhī)
         Combines 10 Heavenly Stems + 12 Earthly Branches = 60 combinations
         Used for year, day, and hour cycles (§11 of FC60 Master Spec)

Dependencies: Base60Codec (for ANIMALS list)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Tuple

try:
    from ..core.base60_codec import Base60Codec
except ImportError:
    from core.base60_codec import Base60Codec


class GanzhiEngine:
    """Sexagenary cycle calculator for years, days, and hours."""

    # 10 Heavenly Stems (天干 Tiāngān)
    STEMS = ["JA", "YI", "BI", "DI", "WW", "JI", "GE", "XI", "RE", "GU"]

    STEM_NAMES = ["Jiǎ", "Yǐ", "Bǐng", "Dīng", "Wù", "Jǐ", "Gēng", "Xīn", "Rén", "Guǐ"]

    STEM_ELEMENTS = [
        "Wood",
        "Wood",
        "Fire",
        "Fire",
        "Earth",
        "Earth",
        "Metal",
        "Metal",
        "Water",
        "Water",
    ]

    STEM_POLARITIES = [
        "Yang",
        "Yin",
        "Yang",
        "Yin",
        "Yang",
        "Yin",
        "Yang",
        "Yin",
        "Yang",
        "Yin",
    ]

    # 12 Earthly Branches — reuse from Base60Codec
    ANIMALS = (
        Base60Codec.ANIMALS
    )  # ["RA","OX","TI","RU","DR","SN","HO","GO","MO","RO","DO","PI"]

    ANIMAL_NAMES = [
        "Rat",
        "Ox",
        "Tiger",
        "Rabbit",
        "Dragon",
        "Snake",
        "Horse",
        "Goat",
        "Monkey",
        "Rooster",
        "Dog",
        "Pig",
    ]

    @staticmethod
    def year_ganzhi(year: int) -> Tuple[int, int]:
        """
        Calculate year Gānzhī indices.

        Returns:
            (stem_index, branch_index) both 0-based
        """
        stem = (year - 4) % 10
        branch = (year - 4) % 12
        return stem, branch

    @staticmethod
    def year_ganzhi_tokens(year: int) -> Tuple[str, str]:
        """Get year Gānzhī tokens."""
        stem_idx, branch_idx = GanzhiEngine.year_ganzhi(year)
        return GanzhiEngine.STEMS[stem_idx], GanzhiEngine.ANIMALS[branch_idx]

    @staticmethod
    def day_ganzhi(jdn: int) -> Tuple[int, int]:
        """
        Calculate day Gānzhī indices from JDN.

        Formula: gz = (JDN + 49) % 60
        """
        gz = (jdn + 49) % 60
        stem = gz % 10
        branch = gz % 12
        return stem, branch

    @staticmethod
    def day_ganzhi_tokens(jdn: int) -> Tuple[str, str]:
        """Get day Gānzhī tokens from JDN."""
        stem_idx, branch_idx = GanzhiEngine.day_ganzhi(jdn)
        return GanzhiEngine.STEMS[stem_idx], GanzhiEngine.ANIMALS[branch_idx]

    @staticmethod
    def hour_ganzhi(hour: int, day_stem_idx: int) -> Tuple[int, int]:
        """
        Calculate hour Gānzhī indices.

        Args:
            hour: Hour of day (0-23)
            day_stem_idx: Stem index of the current day (0-9)

        Returns:
            (stem_index, branch_index)
        """
        branch = ((hour + 1) // 2) % 12
        stem = (day_stem_idx * 2 + branch) % 10
        return stem, branch

    @staticmethod
    def hour_ganzhi_tokens(hour: int, day_stem_idx: int) -> Tuple[str, str]:
        """Get hour Gānzhī tokens."""
        stem_idx, branch_idx = GanzhiEngine.hour_ganzhi(hour, day_stem_idx)
        return GanzhiEngine.STEMS[stem_idx], GanzhiEngine.ANIMALS[branch_idx]

    @staticmethod
    def full_year_info(year: int) -> Dict:
        """Get complete year Gānzhī information."""
        stem_idx, branch_idx = GanzhiEngine.year_ganzhi(year)
        return {
            "year": year,
            "stem_index": stem_idx,
            "branch_index": branch_idx,
            "stem_token": GanzhiEngine.STEMS[stem_idx],
            "branch_token": GanzhiEngine.ANIMALS[branch_idx],
            "gz_token": f"{GanzhiEngine.STEMS[stem_idx]}-{GanzhiEngine.ANIMALS[branch_idx]}",
            "stem_name": GanzhiEngine.STEM_NAMES[stem_idx],
            "animal_name": GanzhiEngine.ANIMAL_NAMES[branch_idx],
            "element": GanzhiEngine.STEM_ELEMENTS[stem_idx],
            "polarity": GanzhiEngine.STEM_POLARITIES[stem_idx],
            "traditional_name": f"{GanzhiEngine.STEM_ELEMENTS[stem_idx]} {GanzhiEngine.ANIMAL_NAMES[branch_idx]}",
        }

    @staticmethod
    def full_day_info(jdn: int) -> Dict:
        """Get complete day Gānzhī information."""
        stem_idx, branch_idx = GanzhiEngine.day_ganzhi(jdn)
        return {
            "jdn": jdn,
            "stem_index": stem_idx,
            "branch_index": branch_idx,
            "stem_token": GanzhiEngine.STEMS[stem_idx],
            "branch_token": GanzhiEngine.ANIMALS[branch_idx],
            "gz_token": f"{GanzhiEngine.STEMS[stem_idx]}-{GanzhiEngine.ANIMALS[branch_idx]}",
            "stem_name": GanzhiEngine.STEM_NAMES[stem_idx],
            "animal_name": GanzhiEngine.ANIMAL_NAMES[branch_idx],
            "element": GanzhiEngine.STEM_ELEMENTS[stem_idx],
            "polarity": GanzhiEngine.STEM_POLARITIES[stem_idx],
        }


# Test vectors from §11.2
TEST_VECTORS = [
    # (year, expected_stem_token, expected_branch_token, expected_name)
    (2020, "GE", "RA", "Metal Rat"),
    (2024, "JA", "DR", "Wood Dragon"),
    (2025, "YI", "SN", "Wood Snake"),
    (2026, "BI", "HO", "Fire Horse"),
    (2030, "GE", "DO", "Metal Dog"),
]


if __name__ == "__main__":
    print("=" * 60)
    print("GANZHI ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: Year Gānzhī
    print("\n1. Testing year Gānzhī:")
    for year, exp_stem, exp_branch, exp_name in TEST_VECTORS:
        info = GanzhiEngine.full_year_info(year)
        if info["stem_token"] == exp_stem and info["branch_token"] == exp_branch:
            print(f"   ✓ {year}: {info['gz_token']} ({info['traditional_name']})")
            passed += 1
        else:
            print(
                f"   ✗ {year}: got {info['gz_token']}, expected {exp_stem}-{exp_branch}"
            )
            failed += 1

    # Test 2: Day Gānzhī for known JDN
    print("\n2. Testing day Gānzhī:")
    day_info = GanzhiEngine.full_day_info(2461078)  # 2026-02-06
    print(
        f"   JDN 2461078: {day_info['gz_token']} ({day_info['element']} {day_info['animal_name']})"
    )
    passed += 1

    # Test 3: Hour Gānzhī
    print("\n3. Testing hour Gānzhī:")
    stem_idx, branch_idx = GanzhiEngine.hour_ganzhi(1, 0)
    h_stem = GanzhiEngine.STEMS[stem_idx]
    h_branch = GanzhiEngine.ANIMALS[branch_idx]
    print(f"   Hour 01, day_stem=0: {h_stem}-{h_branch}")
    passed += 1

    # Test 4: Verify 60-year cycle (2024 + 60 = 2084 should give same GZ)
    print("\n4. Testing 60-year cycle:")
    gz_2024 = GanzhiEngine.year_ganzhi(2024)
    gz_2084 = GanzhiEngine.year_ganzhi(2084)
    if gz_2024 == gz_2084:
        print(f"   ✓ 2024 and 2084 have same GZ indices: {gz_2024}")
        passed += 1
    else:
        print(f"   ✗ 2024={gz_2024}, 2084={gz_2084} (should be equal)")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
