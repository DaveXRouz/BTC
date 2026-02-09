"""
Deep Synthesis Tests - FC60 Numerology AI Framework
=====================================================
Thorough tests for SignalCombiner and ReadingEngine (ANIMAL_ELEMENT_DESCRIPTIONS).

Run: python3 tests/test_synthesis_deep.py
  or python3 -m unittest tests.test_synthesis_deep
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from synthesis.signal_combiner import SignalCombiner
from synthesis.reading_engine import ReadingEngine

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
MOON_PHASES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]
ANIMALS = ["RA", "OX", "TI", "RU", "DR", "SN", "HO", "GO", "MO", "RO", "DO", "PI"]


class TestSignalCombiner(unittest.TestCase):
    """Tests for SignalCombiner: planet-moon combos, LP-PY combos,
    animal harmony, and combine_signals."""

    # ------------------------------------------------------------------
    # Planet x Moon combos (56 total)
    # ------------------------------------------------------------------

    def test_planet_moon_combo_count(self):
        """PLANET_MOON_COMBOS has exactly 56 entries."""
        self.assertEqual(len(SignalCombiner.PLANET_MOON_COMBOS), 56)

    def test_all_56_planet_moon_combos_return_nonempty(self):
        """Every planet x moon combo returns non-empty theme and message."""
        for planet in PLANETS:
            for phase in MOON_PHASES:
                result = SignalCombiner.planet_meets_moon(planet, phase)
                self.assertIn(
                    "theme", result, f"Missing 'theme' for ({planet}, {phase})"
                )
                self.assertIn(
                    "message", result, f"Missing 'message' for ({planet}, {phase})"
                )
                self.assertTrue(
                    len(result["theme"]) > 0,
                    f"Empty theme for ({planet}, {phase})",
                )
                self.assertTrue(
                    len(result["message"]) > 0,
                    f"Empty message for ({planet}, {phase})",
                )

    def test_planet_moon_known_value_sun_full(self):
        """Sun + Full Moon = 'Radiant Revelation'."""
        r = SignalCombiner.planet_meets_moon("Sun", "Full Moon")
        self.assertEqual(r["theme"], "Radiant Revelation")

    def test_planet_moon_known_value_saturn_new(self):
        """Saturn + New Moon = 'Foundation in Darkness'."""
        r = SignalCombiner.planet_meets_moon("Saturn", "New Moon")
        self.assertEqual(r["theme"], "Foundation in Darkness")

    def test_planet_moon_invalid_falls_back(self):
        """Invalid planet or phase returns fallback with 'Uncharted Alignment'."""
        r = SignalCombiner.planet_meets_moon("Pluto", "New Moon")
        self.assertEqual(r["theme"], "Uncharted Alignment")

    # ------------------------------------------------------------------
    # Life Path x Personal Year combos (81 total)
    # ------------------------------------------------------------------

    def test_lp_py_combo_count(self):
        """LP_PY_COMBOS has exactly 81 entries."""
        self.assertEqual(len(SignalCombiner.LP_PY_COMBOS), 81)

    def test_all_81_lp_py_combos_return_nonempty(self):
        """Every LP (1-9) x PY (1-9) combo returns non-empty theme and message."""
        for lp in range(1, 10):
            for py in range(1, 10):
                result = SignalCombiner.lifepath_meets_year(lp, py)
                self.assertIn("theme", result, f"Missing 'theme' for ({lp}, {py})")
                self.assertIn("message", result, f"Missing 'message' for ({lp}, {py})")
                self.assertTrue(
                    len(result["theme"]) > 0,
                    f"Empty theme for LP={lp}, PY={py}",
                )
                self.assertTrue(
                    len(result["message"]) > 0,
                    f"Empty message for LP={lp}, PY={py}",
                )

    def test_lp_py_known_value_1_1(self):
        """LP 1 + PY 1 = 'Double Ignition'."""
        r = SignalCombiner.lifepath_meets_year(1, 1)
        self.assertEqual(r["theme"], "Double Ignition")

    def test_lp_py_known_value_9_9(self):
        """LP 9 + PY 9 = 'Grand Completion'."""
        r = SignalCombiner.lifepath_meets_year(9, 9)
        self.assertEqual(r["theme"], "Grand Completion")

    # ------------------------------------------------------------------
    # Master number LP x PY handling (11, 22, 33)
    # ------------------------------------------------------------------

    def test_master_11_falls_back_to_reduced(self):
        """LP 11 falls back to LP 2 with 'Master Number 11' modifier."""
        r = SignalCombiner.lifepath_meets_year(11, 5)
        base = SignalCombiner.LP_PY_COMBOS[(2, 5)]
        self.assertEqual(r["theme"], base["theme"])
        self.assertIn("Master Number 11", r["message"])

    def test_master_22_falls_back_to_reduced(self):
        """LP 22 falls back to LP 4 with 'Master Number 22' modifier."""
        r = SignalCombiner.lifepath_meets_year(22, 3)
        base = SignalCombiner.LP_PY_COMBOS[(4, 3)]
        self.assertEqual(r["theme"], base["theme"])
        self.assertIn("Master Number 22", r["message"])

    def test_master_33_falls_back_to_reduced(self):
        """LP 33 falls back to LP 6 with 'Master Number 33' modifier."""
        r = SignalCombiner.lifepath_meets_year(33, 7)
        base = SignalCombiner.LP_PY_COMBOS[(6, 7)]
        self.assertEqual(r["theme"], base["theme"])
        self.assertIn("Master Number 33", r["message"])

    def test_master_year_22_falls_back(self):
        """PY 22 falls back to PY 4 with 'Master Year 22' modifier."""
        r = SignalCombiner.lifepath_meets_year(1, 22)
        base = SignalCombiner.LP_PY_COMBOS[(1, 4)]
        self.assertEqual(r["theme"], base["theme"])
        self.assertIn("Master Year 22", r["message"])

    def test_master_both_lp_and_py(self):
        """Both LP and PY are master numbers — both modifiers present."""
        r = SignalCombiner.lifepath_meets_year(11, 33)
        base = SignalCombiner.LP_PY_COMBOS[(2, 6)]
        self.assertEqual(r["theme"], base["theme"])
        self.assertIn("Master Number 11", r["message"])
        self.assertIn("Master Year 33", r["message"])

    # ------------------------------------------------------------------
    # Animal harmony: symmetry
    # ------------------------------------------------------------------

    def test_animal_harmony_symmetry_harmony_pair(self):
        """animal_harmony(RA, OX) == animal_harmony(OX, RA)."""
        r1 = SignalCombiner.animal_harmony("RA", "OX")
        r2 = SignalCombiner.animal_harmony("OX", "RA")
        self.assertEqual(r1, r2)

    def test_animal_harmony_symmetry_clash_pair(self):
        """animal_harmony(RA, HO) == animal_harmony(HO, RA)."""
        r1 = SignalCombiner.animal_harmony("RA", "HO")
        r2 = SignalCombiner.animal_harmony("HO", "RA")
        self.assertEqual(r1, r2)

    def test_animal_harmony_symmetry_neutral_pair(self):
        """animal_harmony(RA, DR) == animal_harmony(DR, RA)."""
        r1 = SignalCombiner.animal_harmony("RA", "DR")
        r2 = SignalCombiner.animal_harmony("DR", "RA")
        self.assertEqual(r1, r2)

    def test_animal_harmony_symmetry_all_known_pairs(self):
        """All entries in ANIMAL_HARMONY are symmetric by construction (frozenset)."""
        for key, value in SignalCombiner.ANIMAL_HARMONY.items():
            animals = list(key)
            if len(animals) == 2:
                r1 = SignalCombiner.animal_harmony(animals[0], animals[1])
                r2 = SignalCombiner.animal_harmony(animals[1], animals[0])
                self.assertEqual(
                    r1, r2, f"Symmetry broken for {animals[0]}-{animals[1]}"
                )

    # ------------------------------------------------------------------
    # Animal harmony: harmony pairs
    # ------------------------------------------------------------------

    def test_harmony_ra_ox(self):
        """RA-OX is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("RA", "OX")["type"], "harmony")

    def test_harmony_ti_pi(self):
        """TI-PI is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("TI", "PI")["type"], "harmony")

    def test_harmony_ru_do(self):
        """RU-DO is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("RU", "DO")["type"], "harmony")

    def test_harmony_dr_ro(self):
        """DR-RO is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("DR", "RO")["type"], "harmony")

    def test_harmony_sn_mo(self):
        """SN-MO is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("SN", "MO")["type"], "harmony")

    def test_harmony_ho_go(self):
        """HO-GO is a harmony pair."""
        self.assertEqual(SignalCombiner.animal_harmony("HO", "GO")["type"], "harmony")

    # ------------------------------------------------------------------
    # Animal harmony: clash pairs
    # ------------------------------------------------------------------

    def test_clash_ra_ho(self):
        """RA-HO is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("RA", "HO")["type"], "clash")

    def test_clash_ox_go(self):
        """OX-GO is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("OX", "GO")["type"], "clash")

    def test_clash_ti_mo(self):
        """TI-MO is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("TI", "MO")["type"], "clash")

    def test_clash_ru_ro(self):
        """RU-RO is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("RU", "RO")["type"], "clash")

    def test_clash_dr_do(self):
        """DR-DO is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("DR", "DO")["type"], "clash")

    def test_clash_sn_pi(self):
        """SN-PI is a clash pair."""
        self.assertEqual(SignalCombiner.animal_harmony("SN", "PI")["type"], "clash")

    # ------------------------------------------------------------------
    # Animal harmony: self-pairing (resonance)
    # ------------------------------------------------------------------

    def test_self_pairing_all_12_animals(self):
        """Every animal paired with itself returns 'resonance'."""
        for animal in ANIMALS:
            result = SignalCombiner.animal_harmony(animal, animal)
            self.assertEqual(
                result["type"],
                "resonance",
                f"{animal}+{animal} should be 'resonance', got '{result['type']}'",
            )

    def test_self_pairing_has_meaning(self):
        """Each self-pairing resonance includes non-empty meaning."""
        for animal in ANIMALS:
            result = SignalCombiner.animal_harmony(animal, animal)
            self.assertTrue(
                len(result["meaning"]) > 0,
                f"Empty meaning for {animal}+{animal} resonance",
            )

    # ------------------------------------------------------------------
    # Animal harmony: unknown pair falls back to neutral
    # ------------------------------------------------------------------

    def test_unknown_pair_returns_neutral(self):
        """An unlisted pair falls back to neutral type."""
        # RA-TI is not in the explicit harmony/clash/neutral tables
        r = SignalCombiner.animal_harmony("RA", "TI")
        self.assertEqual(r["type"], "neutral")
        self.assertTrue(len(r["meaning"]) > 0)

    # ------------------------------------------------------------------
    # combine_signals: aligned signals
    # ------------------------------------------------------------------

    def test_combine_signals_aligned(self):
        """Aligned signals produce coherent output with non-empty primary_message
        and exactly 3 recommended_actions."""
        signals = [
            {
                "type": "animal_repetition",
                "priority": "Very High",
                "message": "Ox appears 3 times — endurance is key.",
            },
            {
                "type": "day_planet",
                "priority": "Medium",
                "message": "This is a Venus day, governing love and beauty.",
            },
            {
                "type": "moon_phase",
                "priority": "Medium",
                "message": "Waning Gibbous — share what you have learned.",
            },
            {
                "type": "hour_animal",
                "priority": "Low-Medium",
                "message": "The Tiger hour carries courage.",
            },
        ]
        numerology = {
            "life_path": {
                "number": 5,
                "title": "Explorer",
                "message": "Change and adapt",
            },
            "personal_year": 9,
        }
        moon = {"best_for": "reflection and release"}
        ganzhi = {}

        combined = SignalCombiner.combine_signals(signals, numerology, moon, ganzhi)

        self.assertIn("primary_message", combined)
        self.assertIn("supporting_messages", combined)
        self.assertIn("tensions", combined)
        self.assertIn("recommended_actions", combined)

        self.assertTrue(len(combined["primary_message"]) > 0)
        self.assertEqual(len(combined["recommended_actions"]), 3)

        # Primary message should come from highest priority signal
        self.assertIn("Ox appears 3 times", combined["primary_message"])

    def test_combine_signals_priority_ordering(self):
        """Primary message comes from the highest-priority signal."""
        signals = [
            {
                "type": "hour_animal",
                "priority": "Low-Medium",
                "message": "Horse energy",
            },
            {"type": "day_planet", "priority": "Medium", "message": "Mercury day"},
            {
                "type": "animal_repetition",
                "priority": "Very High",
                "message": "Triple Dragon",
            },
        ]
        combined = SignalCombiner.combine_signals(signals, {}, {}, {})
        self.assertEqual(combined["primary_message"], "Triple Dragon")

    # ------------------------------------------------------------------
    # combine_signals: conflicting signals -> tensions populated
    # ------------------------------------------------------------------

    def test_combine_signals_conflicting_has_tensions(self):
        """Conflicting animal signals via ganzhi produce tensions."""
        signals = [
            {
                "type": "day_planet",
                "priority": "Medium",
                "message": "Fire and Water elements today.",
            },
        ]
        # RA and HO clash in the ANIMAL_HARMONY table
        ganzhi = {
            "year": {"branch_token": "RA"},
            "day": {"branch_token": "HO"},
            "hour": {"branch_token": "DR"},
        }
        combined = SignalCombiner.combine_signals(signals, {}, {}, ganzhi)
        # RA-HO is a known clash
        self.assertIsInstance(combined["tensions"], list)
        self.assertGreater(
            len(combined["tensions"]),
            0,
            "Expected tensions from RA-HO clash in ganzhi data",
        )

    # ------------------------------------------------------------------
    # combine_signals: empty input -> graceful fallback
    # ------------------------------------------------------------------

    def test_combine_signals_empty_input_no_crash(self):
        """Empty input does not crash and returns all expected keys."""
        combined = SignalCombiner.combine_signals([], {}, {}, {})

        self.assertIn("primary_message", combined)
        self.assertIn("supporting_messages", combined)
        self.assertIn("tensions", combined)
        self.assertIn("recommended_actions", combined)

        # primary_message should be empty string (no signals)
        self.assertEqual(combined["primary_message"], "")
        self.assertIsInstance(combined["supporting_messages"], list)
        self.assertIsInstance(combined["tensions"], list)
        self.assertIsInstance(combined["recommended_actions"], list)
        self.assertEqual(len(combined["recommended_actions"]), 3)

    def test_combine_signals_empty_signals_only(self):
        """Empty signals but with numerology and moon still produces 3 actions."""
        numerology = {
            "life_path": {"number": 7, "title": "Seeker", "message": "Seek truth"},
            "personal_year": 3,
        }
        moon = {"best_for": "creative expression"}
        combined = SignalCombiner.combine_signals([], numerology, moon, {})
        self.assertEqual(len(combined["recommended_actions"]), 3)


class TestAnimalElementDescriptions(unittest.TestCase):
    """Tests for ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS and _describe_animal_element."""

    # ------------------------------------------------------------------
    # Count and completeness
    # ------------------------------------------------------------------

    def test_exactly_60_descriptions(self):
        """ANIMAL_ELEMENT_DESCRIPTIONS has exactly 60 entries."""
        self.assertEqual(len(ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS), 60)

    def test_all_60_descriptions_nonempty_strings(self):
        """All 60 descriptions are non-empty strings."""
        for key, desc in ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS.items():
            self.assertIsInstance(desc, str, f"Description for {key} is not a string")
            self.assertTrue(len(desc) > 0, f"Description for {key} is empty")

    # ------------------------------------------------------------------
    # Uniqueness
    # ------------------------------------------------------------------

    def test_all_60_descriptions_unique(self):
        """All 60 descriptions are unique (no duplicates)."""
        descs = list(ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS.values())
        self.assertEqual(
            len(descs),
            len(set(descs)),
            "Found duplicate descriptions in ANIMAL_ELEMENT_DESCRIPTIONS",
        )

    # ------------------------------------------------------------------
    # Key coverage: every animal x element combination
    # ------------------------------------------------------------------

    def test_all_animal_element_keys_present(self):
        """Every 4-char animal+element token is present as a key."""
        animals = [
            "RA",
            "OX",
            "TI",
            "RU",
            "DR",
            "SN",
            "HO",
            "GO",
            "MO",
            "RO",
            "DO",
            "PI",
        ]
        elements = ["WU", "FI", "ER", "MT", "WA"]
        for animal in animals:
            for element in elements:
                token = animal + element
                self.assertIn(
                    token,
                    ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS,
                    f"Missing key: {token}",
                )

    # ------------------------------------------------------------------
    # _describe_animal_element: known tokens
    # ------------------------------------------------------------------

    def test_describe_known_token_rawu(self):
        """_describe_animal_element('RAWU') returns the correct string."""
        result = ReadingEngine._describe_animal_element("RAWU")
        expected = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS["RAWU"]
        self.assertEqual(result, expected)

    def test_describe_known_token_piwa(self):
        """_describe_animal_element('PIWA') returns the correct string."""
        result = ReadingEngine._describe_animal_element("PIWA")
        expected = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS["PIWA"]
        self.assertEqual(result, expected)

    def test_describe_known_token_drfi(self):
        """_describe_animal_element('DRFI') returns the correct string."""
        result = ReadingEngine._describe_animal_element("DRFI")
        expected = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS["DRFI"]
        self.assertEqual(result, expected)

    # ------------------------------------------------------------------
    # _describe_animal_element: invalid tokens
    # ------------------------------------------------------------------

    def test_describe_invalid_token_returns_empty(self):
        """_describe_animal_element with invalid token returns empty string."""
        self.assertEqual(ReadingEngine._describe_animal_element("XXXX"), "")

    def test_describe_empty_string_returns_empty(self):
        """_describe_animal_element('') returns empty string."""
        self.assertEqual(ReadingEngine._describe_animal_element(""), "")

    def test_describe_partial_token_returns_empty(self):
        """_describe_animal_element with partial token returns empty string."""
        self.assertEqual(ReadingEngine._describe_animal_element("RA"), "")

    # ------------------------------------------------------------------
    # Description content checks
    # ------------------------------------------------------------------

    def test_descriptions_contain_animal_names(self):
        """Spot-check: descriptions reference the animal name."""
        animal_names = {
            "RA": "Rat",
            "OX": "Ox",
            "TI": "Tiger",
            "RU": "Rabbit",
            "DR": "Dragon",
            "SN": "Snake",
            "HO": "Horse",
            "GO": "Goat",
            "MO": "Monkey",
            "RO": "Rooster",
            "DO": "Dog",
            "PI": "Pig",
        }
        elements = ["WU", "FI", "ER", "MT", "WA"]
        for animal_code, animal_name in animal_names.items():
            token = animal_code + elements[0]  # Check at least the Wood element
            desc = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS[token]
            self.assertIn(
                animal_name,
                desc,
                f"Description for {token} does not mention '{animal_name}'",
            )

    def test_descriptions_contain_element_names(self):
        """Spot-check: descriptions reference the element name."""
        element_names = {
            "WU": "Wood",
            "FI": "Fire",
            "ER": "Earth",
            "MT": "Metal",
            "WA": "Water",
        }
        for elem_code, elem_name in element_names.items():
            token = "RA" + elem_code  # Check using Rat as the animal
            desc = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS[token]
            self.assertIn(
                elem_name,
                desc,
                f"Description for {token} does not mention '{elem_name}'",
            )


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    total = suite.countTestCases()
    print(f"Running {total} tests...\n")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
