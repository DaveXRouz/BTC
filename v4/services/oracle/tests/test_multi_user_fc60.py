"""
Tests for Multi-User FC60 Analysis System (T3-S2)
===================================================
6 test classes, 25+ test methods covering:
  - Compatibility matrices (completeness, symmetry, Wu Xing, clashes)
  - Profile calculation (structure, Ganzhi, batch, validation)
  - Pairwise compatibility (scoring, weights, identical, pair count)
  - Group energy (joint LP, dominant selection, archetypes)
  - Group dynamics (roles, synergies, challenges, avg compatibility)
  - Multi-user service (integration, JSON, performance, validation)
"""

import json
import time
import unittest

import oracle_service  # triggers sys.path shim

from engines.compatibility_matrices import (
    LIFE_PATH_COMPATIBILITY,
    ELEMENT_COMPATIBILITY,
    ANIMAL_COMPATIBILITY,
    get_life_path_compatibility,
    get_element_compatibility,
    get_animal_compatibility,
)
from engines.multi_user_fc60 import (
    UserFC60Profile,
    calculate_profile,
    calculate_profiles,
)
from engines.compatibility_analyzer import CompatibilityAnalyzer, PairwiseCompatibility
from engines.group_energy import GroupEnergyCalculator, CombinedGroupEnergy
from engines.group_dynamics import GroupDynamicsAnalyzer, GroupDynamics
from engines.multi_user_service import MultiUserFC60Service, MultiUserAnalysisResult

# ════════════════════════════════════════════════════════════
# Test fixtures
# ════════════════════════════════════════════════════════════

ALICE = {"name": "Alice", "birth_year": 1990, "birth_month": 5, "birth_day": 15}
BOB = {"name": "Bob", "birth_year": 1992, "birth_month": 3, "birth_day": 20}
CAROL = {"name": "Carol", "birth_year": 1988, "birth_month": 11, "birth_day": 7}
DAVE = {"name": "Dave", "birth_year": 1995, "birth_month": 8, "birth_day": 25}


class TestCompatibilityMatrices(unittest.TestCase):
    """Tests for compatibility_matrices.py"""

    def test_life_path_completeness(self):
        """All 78 unique pairs (12 choose 2 + 12 self) are in the matrix."""
        lp_nums = [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33]
        expected_count = len(lp_nums) * (len(lp_nums) + 1) // 2  # 78
        self.assertEqual(len(LIFE_PATH_COMPATIBILITY), expected_count)

    def test_life_path_symmetry(self):
        """Lookup (a, b) == lookup (b, a) for all pairs."""
        self.assertEqual(
            get_life_path_compatibility(1, 5),
            get_life_path_compatibility(5, 1),
        )
        self.assertEqual(
            get_life_path_compatibility(3, 22),
            get_life_path_compatibility(22, 3),
        )

    def test_life_path_score_range(self):
        """All scores in [0.0, 1.0]."""
        for key, score in LIFE_PATH_COMPATIBILITY.items():
            self.assertGreaterEqual(score, 0.0, f"Score too low for {key}")
            self.assertLessEqual(score, 1.0, f"Score too high for {key}")

    def test_element_wu_xing_generating(self):
        """Generating cycle: Wood→Fire→Earth→Metal→Water→Wood = 0.9."""
        cycle = [
            ("Wood", "Fire"),
            ("Fire", "Earth"),
            ("Earth", "Metal"),
            ("Metal", "Water"),
            ("Water", "Wood"),
        ]
        for e1, e2 in cycle:
            self.assertEqual(
                get_element_compatibility(e1, e2), 0.9, f"{e1}→{e2} should be 0.9"
            )

    def test_element_controlling(self):
        """Controlling cycle scores 0.3."""
        controls = [
            ("Wood", "Earth"),
            ("Earth", "Water"),
            ("Water", "Fire"),
            ("Fire", "Metal"),
            ("Metal", "Wood"),
        ]
        for e1, e2 in controls:
            self.assertEqual(
                get_element_compatibility(e1, e2), 0.3, f"{e1}→{e2} should be 0.3"
            )

    def test_element_same(self):
        """Same element = 0.6."""
        for elem in ["Wood", "Fire", "Earth", "Metal", "Water"]:
            self.assertEqual(get_element_compatibility(elem, elem), 0.6)

    def test_element_completeness(self):
        """All 25 element pairs are covered."""
        self.assertEqual(len(ELEMENT_COMPATIBILITY), 25)

    def test_animal_trine_groups(self):
        """Trine group animals score 0.9."""
        self.assertEqual(get_animal_compatibility("Rat", "Dragon"), 0.9)
        self.assertEqual(get_animal_compatibility("Ox", "Snake"), 0.9)
        self.assertEqual(get_animal_compatibility("Tiger", "Dog"), 0.9)
        self.assertEqual(get_animal_compatibility("Rabbit", "Pig"), 0.9)

    def test_animal_six_harmonies(self):
        """Six harmony pairs score 0.95."""
        self.assertEqual(get_animal_compatibility("Rat", "Ox"), 0.95)
        self.assertEqual(get_animal_compatibility("Horse", "Goat"), 0.95)

    def test_animal_clashes(self):
        """Clash pairs score 0.1."""
        self.assertEqual(get_animal_compatibility("Rat", "Horse"), 0.1)
        self.assertEqual(get_animal_compatibility("Dragon", "Dog"), 0.1)

    def test_animal_symmetry(self):
        """Lookup is symmetric."""
        self.assertEqual(
            get_animal_compatibility("Tiger", "Pig"),
            get_animal_compatibility("Pig", "Tiger"),
        )

    def test_unknown_life_path_default(self):
        """Unknown life path pair returns default."""
        self.assertEqual(get_life_path_compatibility(99, 100), 0.5)
        self.assertEqual(get_life_path_compatibility(99, 100, default=0.3), 0.3)


class TestProfileCalculation(unittest.TestCase):
    """Tests for multi_user_fc60.py"""

    def test_profile_structure(self):
        """Profile has all expected fields."""
        p = calculate_profile("Alice", 1990, 5, 15)
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.birth_year, 1990)
        self.assertEqual(p.birth_month, 5)
        self.assertEqual(p.birth_day, 15)
        self.assertIsInstance(p.fc60_sign, str)
        self.assertIn(p.element, ["Wood", "Fire", "Earth", "Metal", "Water"])
        self.assertIn(
            p.animal,
            [
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
            ],
        )
        self.assertIsInstance(p.life_path, int)
        self.assertIsInstance(p.destiny_number, int)
        self.assertIsInstance(p.name_energy, int)

    def test_ganzhi_2026_horse_fire(self):
        """2026 is Fire Horse year — verify extraction."""
        p = calculate_profile("Test", 2026, 1, 1)
        self.assertEqual(p.animal, "Horse")
        self.assertEqual(p.element, "Fire")

    def test_ganzhi_1990_horse_metal(self):
        """1990 is Metal Horse year."""
        p = calculate_profile("Test", 1990, 1, 1)
        self.assertEqual(p.animal, "Horse")
        self.assertEqual(p.element, "Metal")

    def test_to_dict(self):
        """to_dict returns all expected keys."""
        p = calculate_profile("Alice", 1990, 5, 15)
        d = p.to_dict()
        expected_keys = {
            "name",
            "birth_year",
            "birth_month",
            "birth_day",
            "fc60_sign",
            "element",
            "animal",
            "life_path",
            "destiny_number",
            "name_energy",
        }
        self.assertEqual(set(d.keys()), expected_keys)

    def test_batch_profiles(self):
        """calculate_profiles returns correct count."""
        profiles = calculate_profiles([ALICE, BOB])
        self.assertEqual(len(profiles), 2)
        self.assertEqual(profiles[0].name, "Alice")
        self.assertEqual(profiles[1].name, "Bob")

    def test_batch_too_few(self):
        """Less than 2 users raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_profiles([ALICE])

    def test_batch_too_many(self):
        """More than 10 users raises ValueError."""
        users = [
            {"name": f"U{i}", "birth_year": 1990, "birth_month": 1, "birth_day": 1}
            for i in range(11)
        ]
        with self.assertRaises(ValueError):
            calculate_profiles(users)

    def test_missing_field(self):
        """Missing field raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_profiles([{"name": "A", "birth_year": 1990}, ALICE])

    def test_invalid_name(self):
        """Empty name raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_profile("", 1990, 5, 15)

    def test_repr(self):
        """__repr__ includes key info."""
        p = calculate_profile("Alice", 1990, 5, 15)
        r = repr(p)
        self.assertIn("Alice", r)
        self.assertIn("LP=", r)


class TestPairwiseCompatibility(unittest.TestCase):
    """Tests for compatibility_analyzer.py"""

    def setUp(self):
        self.analyzer = CompatibilityAnalyzer()
        self.profiles = calculate_profiles([ALICE, BOB, CAROL, DAVE])

    def test_pair_score_range(self):
        """Overall score in [0, 1]."""
        result = self.analyzer.analyze_pair(self.profiles[0], self.profiles[1])
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 1.0)

    def test_pair_classification(self):
        """Classification is one of 4 valid values."""
        result = self.analyzer.analyze_pair(self.profiles[0], self.profiles[1])
        self.assertIn(
            result.classification, ["Excellent", "Good", "Neutral", "Challenging"]
        )

    def test_weights_sum_to_one(self):
        """Verify weight constants sum to 1.0."""
        from engines.compatibility_analyzer import (
            W_LIFE_PATH,
            W_ELEMENT,
            W_ANIMAL,
            W_DESTINY,
            W_NAME_ENERGY,
        )

        total = W_LIFE_PATH + W_ELEMENT + W_ANIMAL + W_DESTINY + W_NAME_ENERGY
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_identical_users_high_score(self):
        """Same user paired with themselves should score high."""
        p = self.profiles[0]
        result = self.analyzer.analyze_pair(p, p)
        self.assertGreaterEqual(result.overall_score, 0.5)
        # Destiny and name energy should be 1.0 (same person)
        self.assertAlmostEqual(result.destiny_score, 1.0)
        self.assertAlmostEqual(result.name_energy_score, 1.0)

    def test_all_pairs_count(self):
        """N profiles produce N*(N-1)/2 pairs."""
        results = self.analyzer.analyze_all_pairs(self.profiles)
        n = len(self.profiles)
        self.assertEqual(len(results), n * (n - 1) // 2)

    def test_pair_names(self):
        """Pair result includes correct user names."""
        result = self.analyzer.analyze_pair(self.profiles[0], self.profiles[1])
        self.assertEqual(result.user1_name, "Alice")
        self.assertEqual(result.user2_name, "Bob")

    def test_to_dict(self):
        """to_dict returns expected structure."""
        result = self.analyzer.analyze_pair(self.profiles[0], self.profiles[1])
        d = result.to_dict()
        self.assertIn("overall", d)
        self.assertIn("scores", d)
        self.assertIn("life_path", d["scores"])
        self.assertIn("classification", d)
        self.assertIn("strengths", d)
        self.assertIn("challenges", d)

    def test_strengths_challenges_types(self):
        """Strengths and challenges are lists of strings."""
        result = self.analyzer.analyze_pair(self.profiles[0], self.profiles[1])
        self.assertIsInstance(result.strengths, list)
        self.assertIsInstance(result.challenges, list)
        for s in result.strengths:
            self.assertIsInstance(s, str)


class TestGroupEnergy(unittest.TestCase):
    """Tests for group_energy.py"""

    def setUp(self):
        self.calculator = GroupEnergyCalculator()
        self.profiles = calculate_profiles([ALICE, BOB, CAROL, DAVE])

    def test_joint_life_path_type(self):
        """Joint life path is an integer."""
        energy = self.calculator.calculate(self.profiles)
        self.assertIsInstance(energy.joint_life_path, int)
        # Should be 1-9 or master number
        self.assertTrue(
            1 <= energy.joint_life_path <= 9 or energy.joint_life_path in (11, 22, 33)
        )

    def test_dominant_element_valid(self):
        """Dominant element is a valid element."""
        energy = self.calculator.calculate(self.profiles)
        self.assertIn(
            energy.dominant_element, ["Wood", "Fire", "Earth", "Metal", "Water"]
        )

    def test_dominant_animal_valid(self):
        """Dominant animal is a valid animal."""
        energy = self.calculator.calculate(self.profiles)
        self.assertIn(
            energy.dominant_animal,
            [
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
            ],
        )

    def test_archetype_is_known(self):
        """Archetype is one of the defined types."""
        energy = self.calculator.calculate(self.profiles)
        known = {
            "Complementary Duo",
            "Collaborative Builders",
            "Dynamic Innovators",
            "Strategic Thinkers",
            "Action Catalysts",
            "Growth Explorers",
            "Balanced Harmonizers",
            "Master Collective",
        }
        self.assertIn(energy.archetype, known)

    def test_duo_archetype(self):
        """Two users always get Complementary Duo."""
        profiles = calculate_profiles([ALICE, BOB])
        energy = self.calculator.calculate(profiles)
        self.assertEqual(energy.archetype, "Complementary Duo")

    def test_distributions_present(self):
        """Element, animal, LP distributions are non-empty dicts."""
        energy = self.calculator.calculate(self.profiles)
        self.assertIsInstance(energy.element_distribution, dict)
        self.assertIsInstance(energy.animal_distribution, dict)
        self.assertIsInstance(energy.life_path_distribution, dict)
        self.assertTrue(len(energy.element_distribution) > 0)

    def test_to_dict(self):
        """to_dict returns expected keys."""
        energy = self.calculator.calculate(self.profiles)
        d = energy.to_dict()
        expected_keys = {
            "joint_life_path",
            "dominant_element",
            "dominant_animal",
            "archetype",
            "archetype_description",
            "element_distribution",
            "animal_distribution",
            "life_path_distribution",
        }
        self.assertEqual(set(d.keys()), expected_keys)


class TestGroupDynamics(unittest.TestCase):
    """Tests for group_dynamics.py"""

    def setUp(self):
        self.profiles = calculate_profiles([ALICE, BOB, CAROL, DAVE])
        analyzer = CompatibilityAnalyzer()
        self.pairwise = analyzer.analyze_all_pairs(self.profiles)
        self.dynamics_analyzer = GroupDynamicsAnalyzer()

    def test_roles_for_all_users(self):
        """Every user gets a role."""
        dynamics = self.dynamics_analyzer.analyze(self.profiles, self.pairwise)
        for p in self.profiles:
            self.assertIn(p.name, dynamics.roles)
            role_info = dynamics.roles[p.name]
            self.assertIn("role", role_info)
            self.assertIn(
                role_info["role"], ["Leader", "Supporter", "Challenger", "Harmonizer"]
            )

    def test_avg_compatibility_range(self):
        """Avg compatibility is in [0, 1]."""
        dynamics = self.dynamics_analyzer.analyze(self.profiles, self.pairwise)
        self.assertGreaterEqual(dynamics.avg_compatibility, 0.0)
        self.assertLessEqual(dynamics.avg_compatibility, 1.0)

    def test_strongest_weakest_bond(self):
        """Strongest and weakest bonds are present."""
        dynamics = self.dynamics_analyzer.analyze(self.profiles, self.pairwise)
        self.assertIsNotNone(dynamics.strongest_bond)
        self.assertIsNotNone(dynamics.weakest_bond)
        self.assertIn("pair", dynamics.strongest_bond)
        self.assertIn("score", dynamics.strongest_bond)

    def test_synergies_challenges_growth_types(self):
        """All output lists contain strings."""
        dynamics = self.dynamics_analyzer.analyze(self.profiles, self.pairwise)
        for lst in [dynamics.synergies, dynamics.challenges, dynamics.growth_areas]:
            self.assertIsInstance(lst, list)
            for item in lst:
                self.assertIsInstance(item, str)

    def test_to_dict(self):
        """to_dict returns expected keys."""
        dynamics = self.dynamics_analyzer.analyze(self.profiles, self.pairwise)
        d = dynamics.to_dict()
        expected_keys = {
            "roles",
            "synergies",
            "challenges",
            "growth_areas",
            "avg_compatibility",
            "strongest_bond",
            "weakest_bond",
        }
        self.assertEqual(set(d.keys()), expected_keys)


class TestMultiUserService(unittest.TestCase):
    """Tests for multi_user_service.py — integration + performance"""

    def setUp(self):
        self.service = MultiUserFC60Service()

    def test_two_user_analysis(self):
        """Basic 2-user analysis returns complete result."""
        result = self.service.analyze([ALICE, BOB])
        self.assertIsInstance(result, MultiUserAnalysisResult)
        self.assertEqual(result.user_count, 2)
        self.assertEqual(result.pair_count, 1)
        self.assertEqual(len(result.profiles), 2)
        self.assertEqual(len(result.pairwise_compatibility), 1)

    def test_four_user_analysis(self):
        """4-user analysis produces 6 pairs."""
        result = self.service.analyze([ALICE, BOB, CAROL, DAVE])
        self.assertEqual(result.user_count, 4)
        self.assertEqual(result.pair_count, 6)
        self.assertEqual(len(result.pairwise_compatibility), 6)

    def test_json_serializable(self):
        """to_dict() output is fully JSON-serializable."""
        result = self.service.analyze([ALICE, BOB, CAROL])
        d = result.to_dict()
        serialized = json.dumps(d, default=str)
        self.assertIsInstance(serialized, str)
        parsed = json.loads(serialized)
        self.assertEqual(parsed["user_count"], 3)

    def test_computation_time_recorded(self):
        """computation_ms is positive."""
        result = self.service.analyze([ALICE, BOB])
        self.assertGreater(result.computation_ms, 0)

    def test_performance_10_users(self):
        """10-user analysis completes in under 2 seconds."""
        users = [
            {
                "name": f"User{i}",
                "birth_year": 1980 + i,
                "birth_month": (i % 12) + 1,
                "birth_day": (i % 28) + 1,
            }
            for i in range(10)
        ]
        start = time.monotonic()
        result = self.service.analyze(users)
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 2.0, f"10-user analysis took {elapsed:.2f}s")
        self.assertEqual(result.user_count, 10)
        self.assertEqual(result.pair_count, 45)

    def test_validation_too_few(self):
        """Single user raises ValueError."""
        with self.assertRaises(ValueError):
            self.service.analyze([ALICE])

    def test_validation_too_many(self):
        """11 users raises ValueError."""
        users = [
            {"name": f"U{i}", "birth_year": 1990, "birth_month": 1, "birth_day": 1}
            for i in range(11)
        ]
        with self.assertRaises(ValueError):
            self.service.analyze(users)

    def test_validation_missing_field(self):
        """Missing field in user raises ValueError."""
        with self.assertRaises(ValueError):
            self.service.analyze([{"name": "A"}, BOB])

    def test_to_dict_structure(self):
        """to_dict has all top-level keys."""
        result = self.service.analyze([ALICE, BOB])
        d = result.to_dict()
        expected = {
            "user_count",
            "pair_count",
            "computation_ms",
            "profiles",
            "pairwise_compatibility",
            "group_energy",
            "group_dynamics",
        }
        self.assertEqual(set(d.keys()), expected)


if __name__ == "__main__":
    unittest.main()
