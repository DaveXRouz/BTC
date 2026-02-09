"""
Signal Combiner Coverage Test
==============================
Validates completeness of all lookup tables in SignalCombiner:
- 56 planet x moon phase combinations
- 81 life path x personal year combinations
- Master number fallback (11->2, 22->4, 33->6)
- Animal harmony with 3 different animal pairs
- All 60 animal x element descriptions exist and are >= 10 words

Run: python3 eval/test_signal_combiner_coverage.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from synthesis.signal_combiner import SignalCombiner
from synthesis.reading_engine import ReadingEngine


def main():
    passed = 0
    failed = 0
    total = 0

    print("=" * 60)
    print("SIGNAL COMBINER COVERAGE TEST")
    print("=" * 60)

    # -----------------------------------------------------------
    # TEST 1: All 56 planet x moon phase combos return non-empty
    # -----------------------------------------------------------
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    phases = [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    ]

    pm_pass = 0
    pm_fail = 0
    for planet in planets:
        for phase in phases:
            total += 1
            result = SignalCombiner.planet_meets_moon(planet, phase)
            if (
                result
                and result.get("theme")
                and result.get("message")
                and result["theme"] != "Uncharted Alignment"
            ):
                pm_pass += 1
            else:
                pm_fail += 1
                print(f"  FAIL planet_meets_moon({planet!r}, {phase!r}) -> {result}")

    if pm_pass == 56 and pm_fail == 0:
        print(
            f"PASS [1] All 56 planet x moon phase combos return non-empty (7x8={pm_pass})"
        )
        passed += 1
    else:
        print(
            f"FAIL [1] planet x moon: {pm_pass} passed, {pm_fail} failed (expected 56)"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 2: All 81 LP x PY combos return non-empty
    # -----------------------------------------------------------
    lp_py_pass = 0
    lp_py_fail = 0
    for lp in range(1, 10):
        for py in range(1, 10):
            total += 1
            result = SignalCombiner.lifepath_meets_year(lp, py)
            if (
                result
                and result.get("theme")
                and result.get("message")
                and result["theme"] != "Unique Intersection"
            ):
                lp_py_pass += 1
            else:
                lp_py_fail += 1
                print(f"  FAIL lifepath_meets_year({lp}, {py}) -> {result}")

    if lp_py_pass == 81 and lp_py_fail == 0:
        print(f"PASS [2] All 81 LP x PY combos return non-empty (9x9={lp_py_pass})")
        passed += 1
    else:
        print(
            f"FAIL [2] LP x PY: {lp_py_pass} passed, {lp_py_fail} failed (expected 81)"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 3: Master number fallback 11 -> 2
    # -----------------------------------------------------------
    total += 1
    r11 = SignalCombiner.lifepath_meets_year(11, 5)
    r2 = SignalCombiner.lifepath_meets_year(2, 5)
    if r11["theme"] == r2["theme"] and "Master Number 11" in r11["message"]:
        print(
            f"PASS [3] LP 11 falls back to LP 2 with amplification note: theme='{r11['theme']}'"
        )
        passed += 1
    else:
        print(
            f"FAIL [3] LP 11 fallback: theme={r11['theme']}, msg={r11['message'][:80]}"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 4: Master number fallback 22 -> 4
    # -----------------------------------------------------------
    total += 1
    r22 = SignalCombiner.lifepath_meets_year(22, 3)
    r4 = SignalCombiner.lifepath_meets_year(4, 3)
    if r22["theme"] == r4["theme"] and "Master Number 22" in r22["message"]:
        print(
            f"PASS [4] LP 22 falls back to LP 4 with amplification note: theme='{r22['theme']}'"
        )
        passed += 1
    else:
        print(
            f"FAIL [4] LP 22 fallback: theme={r22['theme']}, msg={r22['message'][:80]}"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 5: Master number fallback 33 -> 6
    # -----------------------------------------------------------
    total += 1
    r33 = SignalCombiner.lifepath_meets_year(33, 7)
    r6 = SignalCombiner.lifepath_meets_year(6, 7)
    if r33["theme"] == r6["theme"] and "Master Number 33" in r33["message"]:
        print(
            f"PASS [5] LP 33 falls back to LP 6 with amplification note: theme='{r33['theme']}'"
        )
        passed += 1
    else:
        print(
            f"FAIL [5] LP 33 fallback: theme={r33['theme']}, msg={r33['message'][:80]}"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 6: Animal harmony - harmony pair (RA + OX)
    # -----------------------------------------------------------
    total += 1
    r_harmony = SignalCombiner.animal_harmony("RA", "OX")
    if r_harmony["type"] == "harmony" and r_harmony.get("meaning"):
        print(
            f"PASS [6] animal_harmony('RA','OX') -> type='harmony', meaning='{r_harmony['meaning'][:50]}...'"
        )
        passed += 1
    else:
        print(f"FAIL [6] animal_harmony('RA','OX') -> {r_harmony}")
        failed += 1

    # -----------------------------------------------------------
    # TEST 7: Animal harmony - clash pair (RA + HO)
    # -----------------------------------------------------------
    total += 1
    r_clash = SignalCombiner.animal_harmony("RA", "HO")
    if r_clash["type"] == "clash" and r_clash.get("meaning"):
        print(
            f"PASS [7] animal_harmony('RA','HO') -> type='clash', meaning='{r_clash['meaning'][:50]}...'"
        )
        passed += 1
    else:
        print(f"FAIL [7] animal_harmony('RA','HO') -> {r_clash}")
        failed += 1

    # -----------------------------------------------------------
    # TEST 8: Animal harmony - resonance pair (DR + DR)
    # -----------------------------------------------------------
    total += 1
    r_res = SignalCombiner.animal_harmony("DR", "DR")
    if r_res["type"] == "resonance" and r_res.get("meaning"):
        print(
            f"PASS [8] animal_harmony('DR','DR') -> type='resonance', meaning='{r_res['meaning'][:50]}...'"
        )
        passed += 1
    else:
        print(f"FAIL [8] animal_harmony('DR','DR') -> {r_res}")
        failed += 1

    # -----------------------------------------------------------
    # TEST 9: All 60 animal x element descriptions exist in
    #          ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS
    # -----------------------------------------------------------
    animals = ["RA", "OX", "TI", "RU", "DR", "SN", "HO", "GO", "MO", "RO", "DO", "PI"]
    elements = ["WU", "FI", "ER", "MT", "WA"]

    ae_pass = 0
    ae_fail = 0
    ae_short = 0
    for animal in animals:
        for element in elements:
            total += 1
            token = animal + element
            desc = ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS.get(token, "")
            if desc:
                word_count = len(desc.split())
                if word_count >= 10:
                    ae_pass += 1
                else:
                    ae_short += 1
                    print(f"  FAIL {token}: only {word_count} words (need >= 10)")
            else:
                ae_fail += 1
                print(f"  FAIL {token}: missing from ANIMAL_ELEMENT_DESCRIPTIONS")

    expected = 60
    if ae_pass == expected and ae_fail == 0 and ae_short == 0:
        print(
            f"PASS [9] All 60 animal x element descriptions exist and are >= 10 words ({ae_pass}/{expected})"
        )
        passed += 1
    else:
        print(
            f"FAIL [9] animal x element: {ae_pass} pass, {ae_fail} missing, {ae_short} too short (expected {expected})"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 10: combine_signals sorts by priority (highest first)
    # -----------------------------------------------------------
    total += 1
    test_signals = [
        {
            "type": "hour_animal",
            "priority": "Low-Medium",
            "message": "Low-medium signal",
        },
        {
            "type": "animal_repetition",
            "priority": "Very High",
            "message": "Very high signal",
        },
        {"type": "day_planet", "priority": "Medium", "message": "Medium signal"},
    ]
    combined = SignalCombiner.combine_signals(test_signals, {}, {}, {})
    if combined["primary_message"] == "Very high signal":
        print(
            f"PASS [10] combine_signals sorts by priority: primary is 'Very High' signal"
        )
        passed += 1
    else:
        print(
            f"FAIL [10] combine_signals primary: '{combined['primary_message']}' (expected 'Very high signal')"
        )
        failed += 1

    # -----------------------------------------------------------
    # TEST 11: Verify dict key count for PLANET_MOON_COMBOS == 56
    # -----------------------------------------------------------
    total += 1
    pm_count = len(SignalCombiner.PLANET_MOON_COMBOS)
    if pm_count == 56:
        print(f"PASS [11] PLANET_MOON_COMBOS dict has exactly 56 entries")
        passed += 1
    else:
        print(f"FAIL [11] PLANET_MOON_COMBOS has {pm_count} entries (expected 56)")
        failed += 1

    # -----------------------------------------------------------
    # TEST 12: Verify dict key count for LP_PY_COMBOS == 81
    # -----------------------------------------------------------
    total += 1
    lp_py_count = len(SignalCombiner.LP_PY_COMBOS)
    if lp_py_count == 81:
        print(f"PASS [12] LP_PY_COMBOS dict has exactly 81 entries")
        passed += 1
    else:
        print(f"FAIL [12] LP_PY_COMBOS has {lp_py_count} entries (expected 81)")
        failed += 1

    # -----------------------------------------------------------
    # TEST 13: LP5+PY1 vs LP5+PY9 are meaningfully different
    # -----------------------------------------------------------
    total += 1
    r51 = SignalCombiner.lifepath_meets_year(5, 1)
    r59 = SignalCombiner.lifepath_meets_year(5, 9)
    themes_different = r51["theme"] != r59["theme"]
    messages_different = r51["message"] != r59["message"]
    if themes_different and messages_different:
        print(
            f"PASS [13] LP5+PY1 ('{r51['theme']}') vs LP5+PY9 ('{r59['theme']}') are meaningfully different"
        )
        passed += 1
    else:
        print(f"FAIL [13] LP5+PY1 vs LP5+PY9 not different enough")
        failed += 1

    # -----------------------------------------------------------
    # TEST 14: Planet_meets_moon combos are genuinely unique
    #          (no two combos share identical theme AND message)
    # -----------------------------------------------------------
    total += 1
    seen = set()
    duplicates = 0
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        for phase in phases:
            r = SignalCombiner.planet_meets_moon(planet, phase)
            key = (r["theme"], r["message"])
            if key in seen:
                duplicates += 1
            seen.add(key)
    if duplicates == 0:
        print(f"PASS [14] All 56 planet x moon combos have unique theme+message")
        passed += 1
    else:
        print(f"FAIL [14] {duplicates} duplicate planet x moon combos found")
        failed += 1

    # -----------------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} checks")
    print(f"{'=' * 60}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
