"""
Numerology Engine - Personal Tier Module 1
===========================================
Purpose: Calculate all core numerology numbers from names and birthdates
         Supports Pythagorean and Chaldean systems

Core Numbers:
- Life Path: Core purpose from birthdate
- Expression: Full potential from full name
- Soul Urge: Inner desires from vowels
- Personality: Outer impression from consonants
- Personal Year/Month/Day: Current cycle themes
"""

from typing import Dict


class NumerologyEngine:
    """Complete numerology calculator with dual-system support."""

    # Pythagorean Letter Values
    PYTHAGOREAN = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }

    CHALDEAN = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 8,
        "G": 3,
        "H": 5,
        "I": 1,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 7,
        "P": 8,
        "Q": 1,
        "R": 2,
        "S": 3,
        "T": 4,
        "U": 6,
        "V": 6,
        "W": 6,
        "X": 5,
        "Y": 1,
        "Z": 7,
    }

    VOWELS = set("AEIOUY")
    MASTER_NUMBERS = {11, 22, 33}

    LIFE_PATH_MEANINGS = {
        1: ("Pioneer", "Lead and initiate"),
        2: ("Bridge", "Connect and harmonize"),
        3: ("Voice", "Create and express"),
        4: ("Architect", "Build and stabilize"),
        5: ("Explorer", "Change and adapt"),
        6: ("Guardian", "Nurture and protect"),
        7: ("Seeker", "Analyze and find meaning"),
        8: ("Powerhouse", "Master and achieve"),
        9: ("Sage", "Complete and teach"),
        11: ("Visionary", "Inspire and lead"),
        22: ("Master Builder", "Manifest grand visions"),
        33: ("Master Teacher", "Heal through wisdom"),
    }

    @staticmethod
    def digital_root(n: int) -> int:
        """Reduce to single digit, preserve master numbers."""
        if n in NumerologyEngine.MASTER_NUMBERS:
            return n
        while n > 9:
            n = sum(int(d) for d in str(n))
            if n in NumerologyEngine.MASTER_NUMBERS:
                return n
        return n

    @staticmethod
    def life_path(day: int, month: int, year: int) -> int:
        """Calculate Life Path from birthdate."""
        d = NumerologyEngine.digital_root(day)
        m = NumerologyEngine.digital_root(month)
        y = NumerologyEngine.digital_root(sum(int(c) for c in str(year)))
        return NumerologyEngine.digital_root(d + m + y)

    @staticmethod
    def expression_number(full_name: str, system: str = "pythagorean") -> int:
        """Expression from full name."""
        table = (
            NumerologyEngine.PYTHAGOREAN
            if system == "pythagorean"
            else NumerologyEngine.CHALDEAN
        )
        value = sum(table.get(c, 0) for c in full_name.upper() if c.isalpha())
        return NumerologyEngine.digital_root(value)

    @staticmethod
    def soul_urge(full_name: str, system: str = "pythagorean") -> int:
        """Soul Urge from vowels."""
        table = (
            NumerologyEngine.PYTHAGOREAN
            if system == "pythagorean"
            else NumerologyEngine.CHALDEAN
        )
        value = sum(
            table.get(c, 0) for c in full_name.upper() if c in NumerologyEngine.VOWELS
        )
        return NumerologyEngine.digital_root(value)

    @staticmethod
    def personality_number(full_name: str, system: str = "pythagorean") -> int:
        """Personality from consonants."""
        table = (
            NumerologyEngine.PYTHAGOREAN
            if system == "pythagorean"
            else NumerologyEngine.CHALDEAN
        )
        value = sum(
            table.get(c, 0)
            for c in full_name.upper()
            if c.isalpha() and c not in NumerologyEngine.VOWELS
        )
        return NumerologyEngine.digital_root(value)

    @staticmethod
    def personal_year(birth_month: int, birth_day: int, current_year: int) -> int:
        """Calculate Personal Year."""
        m = NumerologyEngine.digital_root(birth_month)
        d = NumerologyEngine.digital_root(birth_day)
        y = NumerologyEngine.digital_root(sum(int(c) for c in str(current_year)))
        return NumerologyEngine.digital_root(m + d + y)

    @staticmethod
    def personal_month(
        birth_month: int, birth_day: int, current_year: int, current_month: int
    ) -> int:
        """Calculate Personal Month from Personal Year + current month."""
        py = NumerologyEngine.personal_year(birth_month, birth_day, current_year)
        return NumerologyEngine.digital_root(py + current_month)

    @staticmethod
    def personal_day(
        birth_month: int,
        birth_day: int,
        current_year: int,
        current_month: int,
        current_day: int,
    ) -> int:
        """Calculate Personal Day from Personal Month + current day."""
        pm = NumerologyEngine.personal_month(
            birth_month, birth_day, current_year, current_month
        )
        return NumerologyEngine.digital_root(pm + current_day)

    @staticmethod
    def _gender_polarity(gender: str = None) -> Dict:
        """Map gender to polarity."""
        if gender is None:
            return {"gender": None, "polarity": 0, "label": "Neutral"}
        g = gender.strip().lower()
        if g in ("male", "m"):
            return {"gender": gender, "polarity": 1, "label": "Yang"}
        elif g in ("female", "f"):
            return {"gender": gender, "polarity": -1, "label": "Yin"}
        return {"gender": gender, "polarity": 0, "label": "Neutral"}

    @staticmethod
    def complete_profile(
        full_name: str,
        birth_day: int,
        birth_month: int,
        birth_year: int,
        current_year: int,
        current_month: int,
        current_day: int,
        mother_name: str = None,
        system: str = "pythagorean",
        gender: str = None,
    ) -> Dict:
        """Generate complete numerology profile."""
        lp = NumerologyEngine.life_path(birth_day, birth_month, birth_year)

        profile = {
            "life_path": {
                "number": lp,
                "title": NumerologyEngine.LIFE_PATH_MEANINGS[lp][0],
                "message": NumerologyEngine.LIFE_PATH_MEANINGS[lp][1],
            },
            "expression": NumerologyEngine.expression_number(full_name, system),
            "soul_urge": NumerologyEngine.soul_urge(full_name, system),
            "personality": NumerologyEngine.personality_number(full_name, system),
            "personal_year": NumerologyEngine.personal_year(
                birth_month, birth_day, current_year
            ),
            "personal_month": NumerologyEngine.personal_month(
                birth_month, birth_day, current_year, current_month
            ),
            "personal_day": NumerologyEngine.personal_day(
                birth_month, birth_day, current_year, current_month, current_day
            ),
            "gender_polarity": NumerologyEngine._gender_polarity(gender),
        }

        if mother_name:
            profile["mother_influence"] = NumerologyEngine.expression_number(
                mother_name, system
            )

        return profile


if __name__ == "__main__":
    print("=" * 60)
    print("NUMEROLOGY ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: Basic profile
    profile = NumerologyEngine.complete_profile(
        "John Smith", 22, 4, 1999, 2026, 2, 9, "Mary Smith"
    )
    if profile["life_path"]["number"] > 0:
        print(
            f"✓ Life Path: {profile['life_path']['number']} - {profile['life_path']['title']}"
        )
        passed += 1
    else:
        print("✗ Life Path calculation failed")
        failed += 1

    # Test 2: Personal month
    pm = NumerologyEngine.personal_month(4, 22, 2026, 2)
    if 1 <= pm <= 33:
        print(f"✓ Personal Month: {pm}")
        passed += 1
    else:
        print(f"✗ Personal Month out of range: {pm}")
        failed += 1

    # Test 3: Personal day
    pd = NumerologyEngine.personal_day(4, 22, 2026, 2, 9)
    if 1 <= pd <= 33:
        print(f"✓ Personal Day: {pd}")
        passed += 1
    else:
        print(f"✗ Personal Day out of range: {pd}")
        failed += 1

    # Test 4: Gender polarity
    gp_m = NumerologyEngine._gender_polarity("male")
    gp_f = NumerologyEngine._gender_polarity("female")
    gp_n = NumerologyEngine._gender_polarity(None)
    if (
        gp_m["label"] == "Yang"
        and gp_f["label"] == "Yin"
        and gp_n["label"] == "Neutral"
    ):
        print(
            f"✓ Gender polarity: M={gp_m['label']}, F={gp_f['label']}, None={gp_n['label']}"
        )
        passed += 1
    else:
        print(f"✗ Gender polarity incorrect")
        failed += 1

    # Test 5: Profile with gender
    profile2 = NumerologyEngine.complete_profile(
        "Alice Johnson", 15, 7, 1990, 2026, 2, 9, gender="female"
    )
    if (
        "personal_month" in profile2
        and "personal_day" in profile2
        and "gender_polarity" in profile2
    ):
        print(
            f"✓ Extended profile: PM={profile2['personal_month']}, "
            f"PD={profile2['personal_day']}, gender={profile2['gender_polarity']['label']}"
        )
        passed += 1
    else:
        print("✗ Extended profile missing new fields")
        failed += 1

    # Test 6: Backward compatibility (no gender param)
    profile3 = NumerologyEngine.complete_profile("Test User", 1, 1, 2000, 2026, 2, 9)
    if profile3["gender_polarity"]["label"] == "Neutral":
        print(f"✓ Backward compat: no gender → Neutral")
        passed += 1
    else:
        print("✗ Backward compat broken")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
