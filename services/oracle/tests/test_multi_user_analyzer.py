"""Tests for MultiUserAnalyzer — compatibility and group analysis.

Covers: life path scoring, element compatibility, animal relationships,
moon alignment, pattern overlap, pairwise calculation, group analysis.
"""

import unittest

import oracle_service  # noqa: F401 — triggers sys.path shim

from oracle_service.models.reading_types import (
    ReadingResult,
    ReadingType,
)
from oracle_service.multi_user_analyzer import MultiUserAnalyzer


def _make_reading(
    user_id: int,
    life_path: int,
    element: str,
    animal: str,
    moon_phase: str,
    patterns: list = None,
) -> ReadingResult:
    """Create a ReadingResult with controllable comparison data."""
    return ReadingResult(
        reading_type=ReadingType.TIME,
        user_id=user_id,
        framework_output={
            "numerology": {"life_path": {"number": life_path}},
            "ganzhi": {"year": {"element": element, "animal_name": animal}},
            "moon": {"phase_name": moon_phase},
            "patterns": {"detected": patterns or []},
        },
    )


class TestLifePathScoring(unittest.TestCase):
    """Life path compatibility scoring."""

    def test_life_path_same_number(self):
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(5, 5), 1.0)

    def test_life_path_sum_to_nine(self):
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(4, 5), 0.8)
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(1, 8), 0.8)
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(2, 7), 0.8)

    def test_life_path_master_base_pair(self):
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(11, 2), 0.9)
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(2, 11), 0.9)
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(22, 4), 0.9)
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(33, 6), 0.9)

    def test_life_path_both_master(self):
        self.assertEqual(MultiUserAnalyzer.score_life_path_compatibility(11, 22), 0.85)

    def test_life_path_distant_numbers(self):
        score = MultiUserAnalyzer.score_life_path_compatibility(1, 6)
        # Formula: 0.3 + 0.1 * (1.0 - 5/9) = 0.3 + 0.1 * 0.4444 = 0.3444
        self.assertAlmostEqual(score, 0.3 + 0.1 * (1.0 - 5 / 9.0), places=4)
        self.assertGreater(score, 0.3)
        self.assertLess(score, 0.5)


class TestElementScoring(unittest.TestCase):
    """Element compatibility scoring (Wu Xing)."""

    def test_element_productive_cycle(self):
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Wood", "Fire"), 0.9)
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Fire", "Earth"), 0.9)
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Metal", "Water"), 0.9)

    def test_element_controlling_cycle(self):
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Wood", "Earth"), 0.3)
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Water", "Fire"), 0.3)

    def test_element_same(self):
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Fire", "Fire"), 0.7)
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Water", "Water"), 0.7)

    def test_element_symmetric(self):
        # Productive: symmetric
        self.assertEqual(
            MultiUserAnalyzer.score_element_compatibility("Wood", "Fire"),
            MultiUserAnalyzer.score_element_compatibility("Fire", "Wood"),
        )
        # Controlling: symmetric lookup (both orderings checked)
        self.assertEqual(
            MultiUserAnalyzer.score_element_compatibility("Wood", "Earth"),
            MultiUserAnalyzer.score_element_compatibility("Earth", "Wood"),
        )

    def test_element_unknown_default(self):
        self.assertEqual(MultiUserAnalyzer.score_element_compatibility("Unknown", "Fire"), 0.5)


class TestAnimalScoring(unittest.TestCase):
    """Animal compatibility scoring (Chinese zodiac)."""

    def test_animal_secret_friends(self):
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Rat", "Ox"), 1.0)
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Tiger", "Pig"), 1.0)
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Dragon", "Rooster"), 1.0)

    def test_animal_trine_harmony(self):
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Rat", "Dragon"), 0.8)
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Rat", "Monkey"), 0.8)
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Tiger", "Horse"), 0.8)

    def test_animal_clash(self):
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Rat", "Horse"), 0.2)
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Dragon", "Dog"), 0.2)

    def test_animal_same(self):
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Dragon", "Dragon"), 0.7)

    def test_animal_neutral(self):
        self.assertEqual(MultiUserAnalyzer.score_animal_compatibility("Rat", "Tiger"), 0.5)


class TestMoonScoring(unittest.TestCase):
    """Moon phase alignment scoring."""

    def test_moon_same_phase(self):
        self.assertEqual(
            MultiUserAnalyzer.score_moon_alignment(
                {"phase_name": "Full Moon"}, {"phase_name": "Full Moon"}
            ),
            1.0,
        )

    def test_moon_adjacent_phases(self):
        self.assertEqual(
            MultiUserAnalyzer.score_moon_alignment(
                {"phase_name": "New Moon"}, {"phase_name": "Waxing Crescent"}
            ),
            0.7,
        )

    def test_moon_opposite_phases(self):
        self.assertEqual(
            MultiUserAnalyzer.score_moon_alignment(
                {"phase_name": "New Moon"}, {"phase_name": "Full Moon"}
            ),
            0.3,
        )

    def test_moon_other(self):
        self.assertEqual(
            MultiUserAnalyzer.score_moon_alignment(
                {"phase_name": "New Moon"}, {"phase_name": "First Quarter"}
            ),
            0.5,
        )


class TestPatternScoring(unittest.TestCase):
    """Pattern overlap scoring."""

    def test_pattern_two_shared(self):
        a = [
            {"type": "number_repetition", "number": 5},
            {"type": "animal_repetition", "animal": "Dragon"},
        ]
        b = [
            {"type": "number_repetition", "number": 5},
            {"type": "animal_repetition", "animal": "Dragon"},
        ]
        self.assertEqual(MultiUserAnalyzer.score_pattern_overlap(a, b), 0.9)

    def test_pattern_one_shared(self):
        a = [{"type": "number_repetition", "number": 5}]
        b = [
            {"type": "number_repetition", "number": 5},
            {"type": "animal_repetition", "animal": "Dragon"},
        ]
        self.assertEqual(MultiUserAnalyzer.score_pattern_overlap(a, b), 0.7)

    def test_pattern_none_shared(self):
        a = [{"type": "number_repetition", "number": 5}]
        b = [{"type": "number_repetition", "number": 3}]
        self.assertEqual(MultiUserAnalyzer.score_pattern_overlap(a, b), 0.4)

    def test_pattern_one_empty(self):
        self.assertEqual(
            MultiUserAnalyzer.score_pattern_overlap(
                [{"type": "number_repetition", "number": 5}], []
            ),
            0.5,
        )

    def test_pattern_both_empty(self):
        self.assertEqual(MultiUserAnalyzer.score_pattern_overlap([], []), 0.5)


class TestGroupAnalysis(unittest.TestCase):
    """Group analysis: pairwise combinations and harmony score."""

    def test_group_harmony_score_average(self):
        r1 = _make_reading(1, 5, "Wood", "Rat", "Full Moon")
        r2 = _make_reading(2, 5, "Wood", "Rat", "Full Moon")
        r3 = _make_reading(3, 5, "Wood", "Rat", "Full Moon")

        result = MultiUserAnalyzer.analyze_group([r1, r2, r3])

        # All identical → each pairwise score should be the same
        scores = [p.overall_score for p in result.pairwise_compatibility]
        self.assertEqual(len(set(scores)), 1)
        self.assertAlmostEqual(result.group_harmony_score, scores[0], places=4)

    def test_group_element_balance(self):
        r1 = _make_reading(1, 1, "Wood", "Rat", "New Moon")
        r2 = _make_reading(2, 2, "Fire", "Ox", "New Moon")
        r3 = _make_reading(3, 3, "Earth", "Tiger", "New Moon")

        result = MultiUserAnalyzer.analyze_group([r1, r2, r3])

        self.assertEqual(result.group_element_balance["Wood"], 1)
        self.assertEqual(result.group_element_balance["Fire"], 1)
        self.assertEqual(result.group_element_balance["Earth"], 1)

    def test_group_pairwise_count_2(self):
        r1 = _make_reading(1, 1, "Wood", "Rat", "New Moon")
        r2 = _make_reading(2, 2, "Fire", "Ox", "New Moon")

        result = MultiUserAnalyzer.analyze_group([r1, r2])
        self.assertEqual(len(result.pairwise_compatibility), 1)

    def test_group_pairwise_count_3(self):
        readings = [_make_reading(i, i, "Wood", "Rat", "New Moon") for i in range(1, 4)]
        result = MultiUserAnalyzer.analyze_group(readings)
        self.assertEqual(len(result.pairwise_compatibility), 3)

    def test_group_pairwise_count_5(self):
        readings = [_make_reading(i, i, "Wood", "Rat", "New Moon") for i in range(1, 6)]
        result = MultiUserAnalyzer.analyze_group(readings)
        self.assertEqual(len(result.pairwise_compatibility), 10)

    def test_group_summary_populated(self):
        r1 = _make_reading(1, 1, "Wood", "Rat", "New Moon")
        r2 = _make_reading(2, 2, "Fire", "Ox", "New Moon")

        result = MultiUserAnalyzer.analyze_group([r1, r2])
        self.assertIsInstance(result.group_summary, str)
        self.assertGreater(len(result.group_summary), 0)

    def test_weighted_score_formula(self):
        """Verify weights sum to 1.0."""
        total = (
            MultiUserAnalyzer.WEIGHT_LIFE_PATH
            + MultiUserAnalyzer.WEIGHT_ELEMENT
            + MultiUserAnalyzer.WEIGHT_ANIMAL
            + MultiUserAnalyzer.WEIGHT_MOON
            + MultiUserAnalyzer.WEIGHT_PATTERN
        )
        self.assertAlmostEqual(total, 1.0, places=10)


if __name__ == "__main__":
    unittest.main()
