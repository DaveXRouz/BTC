"""
Heartbeat Engine - Personal Tier Module 2
==========================================
Purpose: Estimate heartbeat metrics and encode them in FC60 tokens
         Uses age-based BPM estimation tables

Dependencies: Base60Codec (for token encoding)
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict

try:
    from ..core.base60_codec import Base60Codec
except ImportError:
    from core.base60_codec import Base60Codec


class HeartbeatEngine:
    """Heartbeat estimation and FC60 encoding."""

    # BPM by age range: (max_age_exclusive, bpm)
    BPM_TABLE = [
        (1, 120),
        (3, 110),
        (5, 100),
        (10, 90),
        (15, 80),
        (25, 72),
        (35, 70),
        (50, 72),
        (65, 74),
        (80, 76),
    ]
    BPM_DEFAULT = 78  # age 80+

    ELEMENT_NAMES = ["Wood", "Fire", "Earth", "Metal", "Water"]

    @staticmethod
    def estimated_bpm(age: int) -> int:
        """Estimate resting BPM by age."""
        for max_age, bpm in HeartbeatEngine.BPM_TABLE:
            if age < max_age:
                return bpm
        return HeartbeatEngine.BPM_DEFAULT

    @staticmethod
    def beats_per_day(bpm: int) -> int:
        """Calculate beats per day from BPM."""
        return bpm * 60 * 24

    @staticmethod
    def total_lifetime_beats(current_age: int) -> int:
        """Estimate total lifetime heartbeats using yearly BPM averages."""
        total = 0
        for year in range(current_age):
            bpm = HeartbeatEngine.estimated_bpm(year)
            total += int(bpm * 60 * 24 * 365.25)
        return total

    @staticmethod
    def rhythm_token(bpm: int) -> str:
        """Get FC60 token for daily beat count mod 60."""
        daily = HeartbeatEngine.beats_per_day(bpm)
        return Base60Codec.token60(daily % 60)

    @staticmethod
    def life_pulse_signature(total_beats: int) -> str:
        """Encode total lifetime beats as base-60 string."""
        return Base60Codec.encode_base60(total_beats)

    @staticmethod
    def heartbeat_element(bpm: int) -> str:
        """Map BPM to element via modulo."""
        return HeartbeatEngine.ELEMENT_NAMES[bpm % 5]

    @staticmethod
    def heartbeat_profile(age: int, actual_bpm: int = None) -> Dict:
        """Generate complete heartbeat profile."""
        bpm = (
            actual_bpm if actual_bpm is not None else HeartbeatEngine.estimated_bpm(age)
        )
        daily = HeartbeatEngine.beats_per_day(bpm)
        total = HeartbeatEngine.total_lifetime_beats(age)
        element = HeartbeatEngine.heartbeat_element(bpm)
        rhythm = HeartbeatEngine.rhythm_token(bpm)
        pulse_sig = HeartbeatEngine.life_pulse_signature(total)

        return {
            "age": age,
            "bpm": bpm,
            "bpm_source": "actual" if actual_bpm is not None else "estimated",
            "beats_per_day": daily,
            "total_lifetime_beats": total,
            "element": element,
            "rhythm_token": rhythm,
            "life_pulse_signature": pulse_sig,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("HEARTBEAT ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: BPM estimates for known ages
    test_ages = [(0, 120), (25, 70), (50, 74), (80, 78)]
    for age, exp_bpm in test_ages:
        bpm = HeartbeatEngine.estimated_bpm(age)
        if bpm == exp_bpm:
            print(f"✓ Age {age:3d}: {bpm} BPM")
            passed += 1
        else:
            print(f"✗ Age {age}: got {bpm}, expected {exp_bpm}")
            failed += 1

    # Test 2: Beats per day
    daily = HeartbeatEngine.beats_per_day(72)
    expected_daily = 72 * 60 * 24
    if daily == expected_daily:
        print(f"✓ 72 BPM → {daily} beats/day")
        passed += 1
    else:
        print(f"✗ 72 BPM → {daily} (expected {expected_daily})")
        failed += 1

    # Test 3: Element mapping
    elem = HeartbeatEngine.heartbeat_element(72)
    expected_elem = HeartbeatEngine.ELEMENT_NAMES[72 % 5]
    if elem == expected_elem:
        print(f"✓ 72 BPM → element: {elem}")
        passed += 1
    else:
        print(f"✗ 72 BPM → {elem} (expected {expected_elem})")
        failed += 1

    # Test 4: Full profile
    profile = HeartbeatEngine.heartbeat_profile(35)
    if profile["bpm"] > 0 and profile["total_lifetime_beats"] > 0:
        print(
            f"✓ Age 35 profile: {profile['bpm']} BPM, "
            f"{profile['total_lifetime_beats']:,} lifetime beats, "
            f"element={profile['element']}"
        )
        passed += 1
    else:
        print(f"✗ Invalid profile for age 35")
        failed += 1

    # Test 5: Actual BPM override
    profile2 = HeartbeatEngine.heartbeat_profile(35, actual_bpm=68)
    if profile2["bpm"] == 68 and profile2["bpm_source"] == "actual":
        print(f"✓ Custom BPM 68: source={profile2['bpm_source']}")
        passed += 1
    else:
        print(f"✗ Custom BPM override failed")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
