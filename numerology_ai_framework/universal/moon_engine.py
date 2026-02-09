"""
Moon Engine - Universal Tier Module 1
=====================================
Purpose: Calculate lunar phase from Julian Day Number
         Uses synodic month approximation (§10 of FC60 Master Spec)

Accuracy: ±0.5 days (sufficient for symbolic readings)
Dependencies: math (stdlib only)
"""

import math
from typing import Dict, Tuple


class MoonEngine:
    """Lunar phase calculator using synodic month approximation."""

    SYNODIC_MONTH = 29.530588853
    REFERENCE_JDN = 2451550.1  # New Moon: Jan 6, 2000 ~18:14 UTC

    PHASE_BOUNDARIES = [1.85, 7.38, 11.07, 14.77, 16.61, 22.14, 25.83]

    PHASE_NAMES = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]

    PHASE_EMOJIS = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]

    PHASE_ENERGY = {
        "New Moon": "Seed",
        "Waxing Crescent": "Build",
        "First Quarter": "Challenge",
        "Waxing Gibbous": "Refine",
        "Full Moon": "Culminate",
        "Waning Gibbous": "Share",
        "Last Quarter": "Release",
        "Waning Crescent": "Rest",
    }

    PHASE_BEST_FOR = {
        "New Moon": "Setting intentions, starting projects",
        "Waxing Crescent": "Taking first steps, gathering resources",
        "First Quarter": "Making decisions, overcoming obstacles",
        "Waxing Gibbous": "Editing, perfecting, patience",
        "Full Moon": "Celebrating, releasing, clarity",
        "Waning Gibbous": "Teaching, distributing, gratitude",
        "Last Quarter": "Letting go, forgiving, cleaning",
        "Waning Crescent": "Reflection, preparation, dreaming",
    }

    PHASE_AVOID = {
        "New Moon": "Big reveals, launches",
        "Waxing Crescent": "Giving up",
        "First Quarter": "Avoiding conflict",
        "Waxing Gibbous": "Starting new things",
        "Full Moon": "Starting (too intense)",
        "Waning Gibbous": "Hoarding",
        "Last Quarter": "Holding on",
        "Waning Crescent": "Pushing hard",
    }

    @staticmethod
    def moon_age(jdn: int) -> float:
        """Calculate moon age in days since last new moon."""
        return (jdn - MoonEngine.REFERENCE_JDN) % MoonEngine.SYNODIC_MONTH

    @staticmethod
    def moon_phase(jdn: int) -> Tuple[str, str, float]:
        """
        Determine moon phase from JDN.

        Returns:
            Tuple of (phase_name, emoji, age_in_days)
        """
        age = MoonEngine.moon_age(jdn)

        for i, boundary in enumerate(MoonEngine.PHASE_BOUNDARIES):
            if age < boundary:
                return MoonEngine.PHASE_NAMES[i], MoonEngine.PHASE_EMOJIS[i], age

        return MoonEngine.PHASE_NAMES[7], MoonEngine.PHASE_EMOJIS[7], age

    @staticmethod
    def moon_illumination(age: float) -> float:
        """
        Calculate approximate illumination percentage.

        Formula: 50 * (1 - cos(2*pi*age/SYNODIC_MONTH))
        """
        return 50.0 * (1.0 - math.cos(2.0 * math.pi * age / MoonEngine.SYNODIC_MONTH))

    @staticmethod
    def moon_energy(phase_name: str) -> str:
        """Get the energy keyword for a given phase name."""
        return MoonEngine.PHASE_ENERGY.get(phase_name, "Unknown")

    @staticmethod
    def full_moon_info(jdn: int) -> Dict:
        """Get complete moon information for a given JDN."""
        phase_name, emoji, age = MoonEngine.moon_phase(jdn)
        illumination = MoonEngine.moon_illumination(age)

        return {
            "phase_name": phase_name,
            "emoji": emoji,
            "age": round(age, 2),
            "illumination": round(illumination, 1),
            "energy": MoonEngine.moon_energy(phase_name),
            "best_for": MoonEngine.PHASE_BEST_FOR.get(phase_name, ""),
            "avoid": MoonEngine.PHASE_AVOID.get(phase_name, ""),
        }


if __name__ == "__main__":
    print("=" * 60)
    print("MOON ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: JDN 2461078 (2026-02-06) should be Waning Gibbous, age ~19.05
    info = MoonEngine.full_moon_info(2461078)
    if info["emoji"] == "🌖" and abs(info["age"] - 19.05) < 0.5:
        print(f"✓ JDN 2461078: {info['emoji']} {info['phase_name']} age={info['age']}d")
        passed += 1
    else:
        print(
            f"✗ JDN 2461078: expected 🌖 age~19.05, got {info['emoji']} age={info['age']}"
        )
        failed += 1

    # Test 2: JDN 2451550 (reference new moon) should be New Moon, age ~0
    info2 = MoonEngine.full_moon_info(2451550)
    if info2["phase_name"] == "Waning Crescent" or info2["phase_name"] == "New Moon":
        print(
            f"✓ JDN 2451550 (ref): {info2['emoji']} {info2['phase_name']} age={info2['age']}d"
        )
        passed += 1
    else:
        print(
            f"✗ JDN 2451550: expected near New Moon, got {info2['phase_name']} age={info2['age']}"
        )
        failed += 1

    # Test 3: Illumination at age 0 should be ~0%
    illum_0 = MoonEngine.moon_illumination(0.0)
    if abs(illum_0) < 0.1:
        print(f"✓ Illumination at age 0: {illum_0:.1f}%")
        passed += 1
    else:
        print(f"✗ Illumination at age 0: {illum_0:.1f}% (expected ~0%)")
        failed += 1

    # Test 4: Illumination at age ~14.77 should be ~100%
    illum_full = MoonEngine.moon_illumination(14.77)
    if abs(illum_full - 100.0) < 1.0:
        print(f"✓ Illumination at age 14.77: {illum_full:.1f}%")
        passed += 1
    else:
        print(f"✗ Illumination at age 14.77: {illum_full:.1f}% (expected ~100%)")
        failed += 1

    # Test 5: Energy lookup
    energy = MoonEngine.moon_energy("Full Moon")
    if energy == "Culminate":
        print(f"✓ Full Moon energy: {energy}")
        passed += 1
    else:
        print(f"✗ Full Moon energy: {energy} (expected Culminate)")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
