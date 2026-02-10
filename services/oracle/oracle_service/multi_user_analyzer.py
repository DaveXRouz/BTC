"""Multi-User Analyzer — compatibility and group analysis.

Uses element cycles (Wu Xing), animal relationships (Chinese zodiac),
life path numerology, moon alignment, and pattern overlap to calculate
pairwise compatibility scores and group harmony.

Scoring weights: LP(30%) + Element(25%) + Animal(20%) + Moon(15%) + Patterns(10%)
"""

import itertools
import logging
from typing import Dict, List

from oracle_service.models.reading_types import (
    CompatibilityResult,
    MultiUserResult,
    ReadingResult,
)

logger = logging.getLogger(__name__)


class MultiUserAnalyzer:
    """Compatibility and group analysis engine."""

    # ── Element Compatibility Matrix (Wu Xing) ──
    # Productive cycle: Wood -> Fire -> Earth -> Metal -> Water -> Wood (0.9)
    # Controlling cycle: Wood -> Earth -> Water -> Fire -> Metal -> Wood (0.3)
    # Same element: 0.7
    ELEMENT_COMPATIBILITY: Dict[tuple, float] = {
        # Productive cycle
        ("Wood", "Fire"): 0.9,
        ("Fire", "Earth"): 0.9,
        ("Earth", "Metal"): 0.9,
        ("Metal", "Water"): 0.9,
        ("Water", "Wood"): 0.9,
        # Controlling cycle
        ("Wood", "Earth"): 0.3,
        ("Earth", "Water"): 0.3,
        ("Water", "Fire"): 0.3,
        ("Fire", "Metal"): 0.3,
        ("Metal", "Wood"): 0.3,
        # Same element
        ("Wood", "Wood"): 0.7,
        ("Fire", "Fire"): 0.7,
        ("Earth", "Earth"): 0.7,
        ("Metal", "Metal"): 0.7,
        ("Water", "Water"): 0.7,
    }

    # ── Animal Compatibility ──
    # Secret friends (best match)
    SECRET_FRIENDS: Dict[frozenset, float] = {
        frozenset({"Rat", "Ox"}): 1.0,
        frozenset({"Tiger", "Pig"}): 1.0,
        frozenset({"Rabbit", "Dog"}): 1.0,
        frozenset({"Dragon", "Rooster"}): 1.0,
        frozenset({"Snake", "Monkey"}): 1.0,
        frozenset({"Horse", "Goat"}): 1.0,
    }

    # Trine harmony groups (same element affinity)
    TRINE_GROUPS: List[set] = [
        {"Rat", "Dragon", "Monkey"},
        {"Ox", "Snake", "Rooster"},
        {"Tiger", "Horse", "Dog"},
        {"Rabbit", "Goat", "Pig"},
    ]

    # Clash pairs (conflict)
    CLASH_PAIRS: Dict[frozenset, float] = {
        frozenset({"Rat", "Horse"}): 0.2,
        frozenset({"Ox", "Goat"}): 0.2,
        frozenset({"Tiger", "Monkey"}): 0.2,
        frozenset({"Rabbit", "Rooster"}): 0.2,
        frozenset({"Dragon", "Dog"}): 0.2,
        frozenset({"Snake", "Pig"}): 0.2,
    }

    # Moon phase order for adjacency/opposition
    PHASE_ORDER: List[str] = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]

    # ── Scoring Weights ──
    WEIGHT_LIFE_PATH = 0.30
    WEIGHT_ELEMENT = 0.25
    WEIGHT_ANIMAL = 0.20
    WEIGHT_MOON = 0.15
    WEIGHT_PATTERN = 0.10

    @classmethod
    def score_life_path_compatibility(cls, lp_a: int, lp_b: int) -> float:
        """Score life path compatibility between two numbers.

        Same number -> 1.0, sum to 9 -> 0.8, master+base -> 0.9,
        both master -> 0.85, default formula for others.
        """
        if lp_a == lp_b:
            return 1.0

        # Sum to 9 (completion pair: 1+8, 2+7, 3+6, 4+5)
        if lp_a + lp_b == 9:
            return 0.8

        # Master number + its base (11&2, 22&4, 33&6)
        master_base = {11: 2, 22: 4, 33: 6}
        for master, base in master_base.items():
            if (lp_a == master and lp_b == base) or (lp_b == master and lp_a == base):
                return 0.9

        # Both master numbers
        if lp_a in (11, 22, 33) and lp_b in (11, 22, 33):
            return 0.85

        # Default: closer numbers slightly more compatible
        return 0.3 + 0.1 * (1.0 - abs(lp_a - lp_b) / 9.0)

    @classmethod
    def score_element_compatibility(cls, elem_a: str, elem_b: str) -> float:
        """Score element compatibility using Wu Xing cycles.

        Checks both orderings. Default 0.5 for pairs not in matrix.
        """
        score = cls.ELEMENT_COMPATIBILITY.get((elem_a, elem_b))
        if score is not None:
            return score
        score = cls.ELEMENT_COMPATIBILITY.get((elem_b, elem_a))
        if score is not None:
            return score
        return 0.5

    @classmethod
    def score_animal_compatibility(cls, animal_a: str, animal_b: str) -> float:
        """Score animal compatibility using Chinese zodiac relationships.

        Secret friends -> 1.0, same trine -> 0.8, clash -> 0.2,
        same animal -> 0.7, default -> 0.5.
        """
        pair = frozenset({animal_a, animal_b})

        if animal_a == animal_b:
            return 0.7

        if pair in cls.SECRET_FRIENDS:
            return 1.0

        if pair in cls.CLASH_PAIRS:
            return 0.2

        for group in cls.TRINE_GROUPS:
            if animal_a in group and animal_b in group:
                return 0.8

        return 0.5

    @classmethod
    def score_moon_alignment(cls, moon_a: Dict, moon_b: Dict) -> float:
        """Score moon phase alignment between two readings.

        Same phase -> 1.0, adjacent -> 0.7, opposite -> 0.3, other -> 0.5.
        """
        phase_a = moon_a.get("phase_name", "")
        phase_b = moon_b.get("phase_name", "")

        if phase_a == phase_b:
            return 1.0

        try:
            idx_a = cls.PHASE_ORDER.index(phase_a)
            idx_b = cls.PHASE_ORDER.index(phase_b)
        except ValueError:
            return 0.5

        diff = abs(idx_a - idx_b)
        circular_diff = min(diff, 8 - diff)

        if circular_diff == 1:
            return 0.7
        if circular_diff == 4:
            return 0.3
        return 0.5

    @classmethod
    def score_pattern_overlap(cls, patterns_a: List[Dict], patterns_b: List[Dict]) -> float:
        """Score shared pattern types between two readings.

        2+ shared -> 0.9, 1 shared -> 0.7, 0 shared both have patterns -> 0.4,
        one/both empty -> 0.5.
        """
        if not patterns_a or not patterns_b:
            return 0.5

        types_a = {(p.get("type"), p.get("number", p.get("animal"))) for p in patterns_a}
        types_b = {(p.get("type"), p.get("number", p.get("animal"))) for p in patterns_b}
        shared = types_a & types_b

        if len(shared) >= 2:
            return 0.9
        if len(shared) == 1:
            return 0.7
        return 0.4

    @classmethod
    def _extract_comparison_data(cls, reading: ReadingResult) -> Dict:
        """Extract comparison fields from a ReadingResult's framework output."""
        output = reading.framework_output
        numerology = output.get("numerology", {})
        ganzhi = output.get("ganzhi", {})
        moon = output.get("moon", {})
        patterns = output.get("patterns", {})

        life_path_data = numerology.get("life_path", {})

        return {
            "life_path": life_path_data.get("number", 1),
            "element": ganzhi.get("year", {}).get("element", "Earth"),
            "animal": ganzhi.get("year", {}).get("animal_name", "Rat"),
            "moon": moon,
            "patterns": patterns.get("detected", []),
        }

    @classmethod
    def calculate_pairwise(
        cls, reading_a: ReadingResult, reading_b: ReadingResult
    ) -> CompatibilityResult:
        """Calculate compatibility between two users' readings."""
        data_a = cls._extract_comparison_data(reading_a)
        data_b = cls._extract_comparison_data(reading_b)

        lp_score = cls.score_life_path_compatibility(data_a["life_path"], data_b["life_path"])
        elem_score = cls.score_element_compatibility(data_a["element"], data_b["element"])
        animal_score = cls.score_animal_compatibility(data_a["animal"], data_b["animal"])
        moon_score = cls.score_moon_alignment(data_a["moon"], data_b["moon"])
        pattern_score = cls.score_pattern_overlap(data_a["patterns"], data_b["patterns"])

        overall = (
            lp_score * cls.WEIGHT_LIFE_PATH
            + elem_score * cls.WEIGHT_ELEMENT
            + animal_score * cls.WEIGHT_ANIMAL
            + moon_score * cls.WEIGHT_MOON
            + pattern_score * cls.WEIGHT_PATTERN
        )

        scores = {
            "Life Path": lp_score,
            "Element": elem_score,
            "Animal": animal_score,
            "Moon": moon_score,
            "Pattern": pattern_score,
        }
        strengths = [name for name, s in scores.items() if s >= 0.7]
        challenges = [name for name, s in scores.items() if s <= 0.3]

        if overall >= 0.8:
            desc = "Highly compatible — strong natural harmony"
        elif overall >= 0.6:
            desc = "Good compatibility — complementary energies"
        elif overall >= 0.4:
            desc = "Mixed compatibility — some alignment, some tension"
        else:
            desc = "Challenging compatibility — growth through friction"

        return CompatibilityResult(
            user_a_id=reading_a.user_id,
            user_b_id=reading_b.user_id,
            overall_score=round(overall, 4),
            life_path_score=lp_score,
            element_score=elem_score,
            animal_score=animal_score,
            moon_score=moon_score,
            pattern_score=pattern_score,
            description=desc,
            strengths=strengths,
            challenges=challenges,
        )

    @classmethod
    def analyze_group(cls, readings: List[ReadingResult]) -> MultiUserResult:
        """Analyze group compatibility from individual readings.

        Generates all pairwise combinations, calculates compatibility for each,
        and produces group harmony score + element balance.
        """
        pairs = list(itertools.combinations(readings, 2))
        pairwise = [cls.calculate_pairwise(a, b) for a, b in pairs]

        if pairwise:
            harmony = sum(p.overall_score for p in pairwise) / len(pairwise)
        else:
            harmony = 0.0

        element_balance: Dict[str, int] = {}
        for reading in readings:
            data = cls._extract_comparison_data(reading)
            elem = data["element"]
            element_balance[elem] = element_balance.get(elem, 0) + 1

        if harmony >= 0.8:
            summary = "Exceptional group harmony — strong collective energy"
        elif harmony >= 0.6:
            summary = "Good group dynamics — complementary strengths"
        elif harmony >= 0.4:
            summary = "Balanced group — diverse energies require mutual respect"
        else:
            summary = "Challenging group dynamic — individual strengths may conflict"

        unique_elements = len(element_balance)
        if unique_elements >= 4:
            summary += ". Highly diverse element composition."
        elif unique_elements == 1:
            elem_name = list(element_balance.keys())[0]
            summary += f". Uniform {elem_name} energy — focused but narrow."

        return MultiUserResult(
            individual_readings=readings,
            pairwise_compatibility=pairwise,
            group_harmony_score=round(harmony, 4),
            group_element_balance=element_balance,
            group_summary=summary,
        )
