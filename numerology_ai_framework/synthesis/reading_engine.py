"""
Reading Engine - Synthesis Tier Module 1
=========================================
Purpose: Generate symbolic readings from FC60 stamps and related data
         Implements signal hierarchy from §12 of FC60 Master Spec

Dependencies: All core + universal + personal modules
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional
from collections import Counter


class ReadingEngine:
    """Signal-based reading generator using FC60 stamp components."""

    # Animal traits (§12.2)
    ANIMAL_TRAITS = {
        "RA": {
            "name": "Rat",
            "trait": "Resourcefulness and sharp perception",
            "action": "Trust your instincts and act quickly",
        },
        "OX": {
            "name": "Ox",
            "trait": "Patience and steady endurance",
            "action": "Stay the course — persistence is your power",
        },
        "TI": {
            "name": "Tiger",
            "trait": "Courage and bold leadership",
            "action": "Take charge of the situation with confidence",
        },
        "RU": {
            "name": "Rabbit",
            "trait": "Intuition and gentle diplomacy",
            "action": "Listen to your inner voice before acting",
        },
        "DR": {
            "name": "Dragon",
            "trait": "Transformation and destiny",
            "action": "Embrace the change that's calling you",
        },
        "SN": {
            "name": "Snake",
            "trait": "Wisdom and precision",
            "action": "Look deeper — the answer is in the details",
        },
        "HO": {
            "name": "Horse",
            "trait": "Freedom and passionate movement",
            "action": "Move forward with energy and independence",
        },
        "GO": {
            "name": "Goat",
            "trait": "Creativity and artistic vision",
            "action": "Express yourself through creative channels",
        },
        "MO": {
            "name": "Monkey",
            "trait": "Adaptability and cleverness",
            "action": "Find the creative solution others have missed",
        },
        "RO": {
            "name": "Rooster",
            "trait": "Truth and confident discipline",
            "action": "Speak your truth clearly and without hesitation",
        },
        "DO": {
            "name": "Dog",
            "trait": "Loyalty and honest protection",
            "action": "Stand guard over what matters most to you",
        },
        "PI": {
            "name": "Pig",
            "trait": "Abundance and generous completion",
            "action": "Share freely — there is more than enough",
        },
    }

    # Element meanings
    ELEMENT_MEANINGS = {
        "WU": {
            "name": "Wood",
            "meaning": "Growth and new beginnings",
            "shadow": "Scattered energy",
        },
        "FI": {
            "name": "Fire",
            "meaning": "Transformation and passion",
            "shadow": "Burnout",
        },
        "ER": {
            "name": "Earth",
            "meaning": "Stability and grounding",
            "shadow": "Stagnation",
        },
        "MT": {
            "name": "Metal",
            "meaning": "Refinement and structure",
            "shadow": "Rigidity",
        },
        "WA": {
            "name": "Water",
            "meaning": "Depth and hidden flow",
            "shadow": "Overwhelm",
        },
    }

    # Animal × Element descriptions (60 unique entries)
    ANIMAL_ELEMENT_DESCRIPTIONS = {
        "RAWU": "Rat Wood — Quick-growing resourcefulness. New ideas sprout fast; trust your instinct to seize emerging opportunities.",
        "RAFI": "Rat Fire — Blazing perception. Sharp intuition meets passionate drive, burning through obstacles with clever intensity.",
        "RAER": "Rat Earth — Grounded cunning. Practical wisdom anchors your quick mind; build something stable from fleeting insights.",
        "RAMT": "Rat Metal — Refined instinct. Precision cuts through confusion; your sharp mind finds the exact right moment to act.",
        "RAWA": "Rat Water — Deep perception. Intuition flows beneath the surface; trust the currents you sense but cannot yet see.",
        "OXWU": "Ox Wood — Patient growth. Steady effort meets new beginnings; foundations built now will flourish over seasons.",
        "OXFI": "Ox Fire — Determined transformation. Endurance fueled by passion; slow-burning change that reshapes everything it touches.",
        "OXER": "Ox Earth — Double stability. Unshakeable foundation energy; this is the bedrock upon which empires are built.",
        "OXMT": "Ox Metal — Disciplined structure. Iron patience meets refined purpose; nothing can rush or derail this energy.",
        "OXWA": "Ox Water — Deep endurance. Emotional resilience runs like an underground river; quiet strength that never runs dry.",
        "TIWU": "Tiger Wood — Bold expansion. Courage meets growth; charge forward into new territory with fierce confidence.",
        "TIFI": "Tiger Fire — Blazing courage. Fearless passion ignites action; this energy transforms timidity into triumph.",
        "TIER": "Tiger Earth — Grounded power. Raw strength meets practical wisdom; the warrior who knows when to fight and when to wait.",
        "TIMT": "Tiger Metal — Sharp authority. Cutting decisiveness backed by fearless will; leadership that commands through clarity.",
        "TIWA": "Tiger Water — Intuitive courage. Deep emotional bravery; the strength to face what lies beneath the surface.",
        "RUWU": "Rabbit Wood — Gentle growth. Diplomatic expansion through kindness; soft influence that shapes the world without force.",
        "RUFI": "Rabbit Fire — Passionate intuition. Inner warmth meets outer grace; creative fire channeled through elegant expression.",
        "RUER": "Rabbit Earth — Stable sensitivity. Emotional intelligence grounded in practicality; the diplomat with unshakeable foundations.",
        "RUMT": "Rabbit Metal — Refined diplomacy. Precise communication and elegant boundaries; kindness with an edge of steel.",
        "RUWA": "Rabbit Water — Deep gentleness. Profound empathy flows quietly; understanding that heals without words.",
        "DRWU": "Dragon Wood — Destined growth. Transformation aligned with expansion; the seed of greatness finding its season.",
        "DRFI": "Dragon Fire — Blazing destiny. Powerful transformation at full intensity; the moment everything changes forever.",
        "DRER": "Dragon Earth — Grounded transformation. Practical magic; turning grand visions into tangible reality step by step.",
        "DRMT": "Dragon Metal — Refined power. Destiny sharpened to a fine edge; precise, purposeful, and unstoppable transformation.",
        "DRWA": "Dragon Water — Deep destiny. Hidden currents of change flowing beneath calm surfaces; transformation from the depths.",
        "SNWU": "Snake Wood — Growing wisdom. Knowledge rooted in observation; understanding that develops slowly and bears fruit.",
        "SNFI": "Snake Fire — Passionate insight. Intense perception fueled by desire to understand; seeing through every illusion.",
        "SNER": "Snake Earth — Grounded precision. Practical wisdom based on careful observation; nothing escapes this measured attention.",
        "SNMT": "Snake Metal — Razor insight. Analytical precision at its sharpest; cutting straight to the truth of any matter.",
        "SNWA": "Snake Water — Deep knowing. Intuitive wisdom that moves like water — finding every crack, filling every space.",
        "HOWU": "Horse Wood — Free growth. Independent expansion; galloping toward new horizons with unbridled enthusiasm for life.",
        "HOFI": "Horse Fire — Blazing freedom. Passionate independence at full speed; nothing can contain this wild, joyful energy.",
        "HOER": "Horse Earth — Grounded movement. Freedom with direction; the traveler who always knows the way home.",
        "HOMT": "Horse Metal — Disciplined freedom. Structured independence; the power of movement channeled through clear purpose.",
        "HOWA": "Horse Water — Flowing freedom. Emotional liberation; releasing what binds and following the heart's true current.",
        "GOWU": "Goat Wood — Creative growth. Artistic vision finding new forms; beauty emerging from imagination's fertile ground.",
        "GOFI": "Goat Fire — Passionate artistry. Creative flame burns bright; inspiration transforms into tangible beauty and meaning.",
        "GOER": "Goat Earth — Grounded creativity. Practical artistry; turning aesthetic vision into lasting works that nourish the soul.",
        "GOMT": "Goat Metal — Refined beauty. Artistic precision; the craft of perfecting what the heart imagines into elegant form.",
        "GOWA": "Goat Water — Deep creativity. Emotional artistry flowing from the subconscious; art that heals and reveals truth.",
        "MOWU": "Monkey Wood — Clever expansion. Adaptable intelligence finding new paths; inventive solutions growing from playful curiosity.",
        "MOFI": "Monkey Fire — Blazing ingenuity. Clever passion sparks innovation; wit and warmth combined into brilliant action.",
        "MOER": "Monkey Earth — Practical cleverness. Grounded adaptability; finding workable solutions when others see only problems.",
        "MOMT": "Monkey Metal — Sharp wit. Precision intelligence; the mind that cuts through complexity with elegant simplicity.",
        "MOWA": "Monkey Water — Deep adaptability. Fluid intelligence that flows around every obstacle; emotional cleverness and insight.",
        "ROWU": "Rooster Wood — Growing confidence. Truthful expression taking root; honest voice strengthening with every word spoken.",
        "ROFI": "Rooster Fire — Blazing truth. Passionate honesty that illuminates; speaking with conviction that transforms listeners.",
        "ROER": "Rooster Earth — Grounded discipline. Practical truth-telling; reliable, methodical, and steadfastly honest in all things.",
        "ROMT": "Rooster Metal — Sharp honesty. Double refinement; the clearest, most precise voice in the room speaks unavoidable truth.",
        "ROWA": "Rooster Water — Deep integrity. Emotional truth-telling; the honest voice that speaks from the heart's depths.",
        "DOWU": "Dog Wood — Loyal growth. Protective devotion expanding into new territory; faithfulness finding new causes to champion.",
        "DOFI": "Dog Fire — Passionate loyalty. Fierce devotion fueled by love; the guardian whose fire burns for those they protect.",
        "DOER": "Dog Earth — Grounded protection. Steady faithfulness; the reliable guardian who is always there, always watching.",
        "DOMT": "Dog Metal — Disciplined loyalty. Unwavering duty sharpened to precision; protection through structure and principled action.",
        "DOWA": "Dog Water — Deep devotion. Emotional loyalty that runs to the core; protection born from profound understanding.",
        "PIWU": "Pig Wood — Abundant growth. Generous expansion; sharing freely creates more for everyone, abundance multiplying through giving.",
        "PIFI": "Pig Fire — Passionate generosity. Warm-hearted abundance; the joy of giving fueled by genuine love for others.",
        "PIER": "Pig Earth — Grounded abundance. Practical generosity; sharing resources wisely to create lasting prosperity for all.",
        "PIMT": "Pig Metal — Refined generosity. Structured giving; abundance channeled through purposeful, well-organized acts of kindness.",
        "PIWA": "Pig Water — Deep abundance. Emotional generosity flowing without limit; the completion that comes from giving everything.",
    }

    # Time-of-day context (§12.3)
    TIME_BANDS = [
        (5, "The hour of silence", "Deep night — subconscious surfaces"),
        (8, "The early hours", "Raw potential, day not yet shaped"),
        (12, "Morning engine", "Clarity peaks, resistance lowest"),
        (15, "Midday checkpoint", "Momentum building or fading"),
        (18, "Afternoon shift", "Results arriving, time to adjust"),
        (21, "Evening transition", "Processing begins"),
        (24, "Night hours", "Masks off, real questions surface"),
    ]

    @staticmethod
    def _collect_animals(fc60_stamp: Dict, ganzhi_data: Dict = None) -> List[str]:
        """Collect animal tokens from all stamp positions."""
        animals = []
        if fc60_stamp.get("_month_animal"):
            animals.append(fc60_stamp["_month_animal"])
        if fc60_stamp.get("_dom_token"):
            animals.append(fc60_stamp["_dom_token"][:2])
        if fc60_stamp.get("_hour_animal"):
            animals.append(fc60_stamp["_hour_animal"])
        if fc60_stamp.get("_minute_token"):
            animals.append(fc60_stamp["_minute_token"][:2])
        if ganzhi_data and "year" in ganzhi_data:
            animals.append(ganzhi_data["year"].get("branch_token", ""))
        return [a for a in animals if a]

    @staticmethod
    def _detect_animal_repetitions(animals: List[str]) -> List[Dict]:
        """Detect repeated animals (§12.2)."""
        counts = Counter(animals)
        repeated = []
        for animal, count in counts.most_common():
            if count >= 2:
                trait_info = ReadingEngine.ANIMAL_TRAITS.get(animal, {})
                repeated.append(
                    {
                        "animal": animal,
                        "animal_name": trait_info.get("name", animal),
                        "count": count,
                        "priority": "Very High" if count >= 3 else "High",
                        "trait": trait_info.get("trait", ""),
                        "action": trait_info.get("action", ""),
                    }
                )
        return repeated

    @staticmethod
    def _time_context(hour: int) -> Dict:
        """Get time-of-day context (§12.3)."""
        for boundary, context, energy in ReadingEngine.TIME_BANDS:
            if hour < boundary:
                return {"context": context, "energy": energy}
        return {"context": "Night hours", "energy": "Masks off, real questions surface"}

    @staticmethod
    def _check_sun_moon_paradox(fc60_stamp: Dict, hour: int) -> Optional[str]:
        """Check for Sun/Moon paradox (§12.4)."""
        if fc60_stamp.get("_half_marker") == "☀" and 0 <= hour <= 5:
            return (
                "You're marked as being in the Sun half, but sitting in darkness. "
                "This means you're carrying light that hasn't been made visible yet. "
                "You see something the world hasn't caught up with."
            )
        return None

    @staticmethod
    def _describe_animal_element(dom_token: str) -> str:
        """Get description for a specific animal×element combination."""
        return ReadingEngine.ANIMAL_ELEMENT_DESCRIPTIONS.get(dom_token, "")

    @staticmethod
    def _personal_x_current(
        numerology_profile: Dict, planet: str, moon_data: Dict
    ) -> List[Dict]:
        """Cross-reference personal numbers with current cosmic state."""
        insights = []
        if not numerology_profile:
            return insights

        try:
            from synthesis.signal_combiner import SignalCombiner

            lp = numerology_profile.get("life_path", {}).get("number", 0)
            py = numerology_profile.get("personal_year", 0)

            if lp and py:
                lp_py = SignalCombiner.lifepath_meets_year(lp, py)
                insights.append(
                    {
                        "type": "lifepath_year",
                        "theme": lp_py["theme"],
                        "message": lp_py["message"],
                    }
                )

            if planet and moon_data:
                phase = moon_data.get("phase_name", "")
                if phase:
                    pm = SignalCombiner.planet_meets_moon(planet, phase)
                    insights.append(
                        {
                            "type": "planet_moon",
                            "theme": pm["theme"],
                            "message": pm["message"],
                        }
                    )
        except ImportError:
            pass

        return insights

    @staticmethod
    def generate_reading(
        fc60_stamp: Dict,
        numerology_profile: Dict = None,
        moon_data: Dict = None,
        ganzhi_data: Dict = None,
        heartbeat_data: Dict = None,
        location_data: Dict = None,
    ) -> Dict:
        """
        Generate a complete symbolic reading.

        Args:
            fc60_stamp: Output from FC60StampEngine.encode()
            numerology_profile: Output from NumerologyEngine.complete_profile()
            moon_data: Output from MoonEngine.full_moon_info()
            ganzhi_data: Dict with 'year', 'day', 'hour' ganzhi info
            heartbeat_data: Output from HeartbeatEngine.heartbeat_profile()
            location_data: Output from LocationEngine.location_signature()

        Returns:
            Dict with reading sections and metadata
        """
        signals = []

        # Collect and analyze animals
        animals = ReadingEngine._collect_animals(fc60_stamp, ganzhi_data)
        repetitions = ReadingEngine._detect_animal_repetitions(animals)

        for rep in repetitions:
            signals.append(
                {
                    "type": "animal_repetition",
                    "priority": rep["priority"],
                    "message": f"The {rep['animal_name']} appears {rep['count']} times — "
                    f"{rep['trait']}. The instruction: {rep['action']}",
                }
            )

        # Day planet signal
        planet = fc60_stamp.get("_planet", "")
        domain = fc60_stamp.get("_domain", "")
        if planet:
            signals.append(
                {
                    "type": "day_planet",
                    "priority": "Medium",
                    "message": f"This is a {planet} day, governing {domain.lower()}.",
                }
            )

        # Moon phase signal
        moon_context = ""
        if moon_data:
            moon_context = (
                f"The moon is {moon_data['emoji']} {moon_data['phase_name']} "
                f"(age {moon_data['age']} days, {moon_data['illumination']}% illuminated). "
                f"Energy: {moon_data['energy']}. "
                f"Best for: {moon_data['best_for']}."
            )
            signals.append(
                {
                    "type": "moon_phase",
                    "priority": "Medium",
                    "message": moon_context,
                }
            )

        # DOM token analysis
        dom_token = fc60_stamp.get("_dom_token", "")
        if dom_token:
            animal_part = dom_token[:2]
            element_part = dom_token[2:]
            animal_info = ReadingEngine.ANIMAL_TRAITS.get(animal_part, {})
            element_info = ReadingEngine.ELEMENT_MEANINGS.get(element_part, {})
            if animal_info and element_info:
                signals.append(
                    {
                        "type": "dom_animal_element",
                        "priority": "Medium",
                        "message": f"Today's day-of-month energy: "
                        f"{animal_info['name']} {element_info['name']} — "
                        f"{element_info['meaning']}.",
                    }
                )

        # Hour animal
        hour_animal = fc60_stamp.get("_hour_animal", "")
        if hour_animal:
            hour_info = ReadingEngine.ANIMAL_TRAITS.get(hour_animal, {})
            if hour_info:
                signals.append(
                    {
                        "type": "hour_animal",
                        "priority": "Low-Medium",
                        "message": f"The {hour_info['name']} hour carries the energy of "
                        f"{hour_info['trait'].lower()}.",
                    }
                )

        # Time context
        hour = 0
        if fc60_stamp.get("_half_marker"):
            # Extract hour from the stamp
            hour_animal_token = fc60_stamp.get("_hour_animal", "RA")
            from core.base60_codec import Base60Codec

            hour_idx = Base60Codec.ANIMAL_TO_INDEX.get(hour_animal_token, 0)
            if fc60_stamp.get("_half_marker") == "🌙":
                hour = hour_idx + 12 if hour_idx != 0 else 12
            else:
                hour = hour_idx

        time_ctx = ReadingEngine._time_context(hour)

        # Sun/Moon paradox
        paradox = ReadingEngine._check_sun_moon_paradox(fc60_stamp, hour)

        # Personal overlay
        personal_overlay = ""
        if numerology_profile:
            lp = numerology_profile.get("life_path", {})
            py = numerology_profile.get("personal_year", 0)
            if lp:
                personal_overlay = (
                    f"Through your Life Path {lp.get('number', '')} "
                    f"({lp.get('title', '')}), this moment asks you to "
                    f"{lp.get('message', '').lower()}. "
                    f"Your Personal Year {py} colors everything with its theme."
                )

        # Heartbeat context
        heartbeat_context = ""
        if heartbeat_data:
            heartbeat_context = (
                f"Your heart beats at {heartbeat_data['bpm']} BPM "
                f"({heartbeat_data['element']} rhythm). "
                f"{heartbeat_data['total_lifetime_beats']:,} beats have "
                f"carried you to this exact moment."
            )

        # Location context
        location_context = ""
        if location_data:
            location_context = (
                f"Your location resonates with {location_data['element']} energy "
                f"({location_data['lat_hemisphere']}/{location_data['lon_hemisphere']}). "
                f"The {location_data['lat_polarity']} latitude meets "
                f"{location_data['lon_polarity']} longitude."
            )

        # Ganzhi year context
        year_context = ""
        if ganzhi_data and "year" in ganzhi_data:
            gy = ganzhi_data["year"]
            year_context = (
                f"This is the year of the {gy.get('traditional_name', '')} "
                f"({gy.get('gz_token', '')}) — {gy.get('element', '')} energy "
                f"with {gy.get('polarity', '')} polarity."
            )

        # Build opening
        weekday_name = fc60_stamp.get("_weekday_name", "Unknown")
        opening = (
            f"At this moment on this {planet} {weekday_name}, "
            f"the {time_ctx['context'].lower()} shapes the energy. "
            f"{time_ctx['energy']}."
        )

        # Build core signal
        core_signal = ""
        if repetitions:
            rep = repetitions[0]
            core_signal = (
                f"The {rep['animal_name']} appears {rep['count']} times — "
                f"this is the loudest signal. "
                f"{rep['trait']}. The instruction: {rep['action']}"
            )

        # Day energy
        day_energy = ""
        if dom_token:
            animal_part = dom_token[:2]
            element_part = dom_token[2:]
            a_info = ReadingEngine.ANIMAL_TRAITS.get(animal_part, {})
            e_info = ReadingEngine.ELEMENT_MEANINGS.get(element_part, {})
            if a_info and e_info:
                day_energy = (
                    f"Today's core energy is {a_info['name']} "
                    f"paired with {e_info['name']}. "
                    f"{e_info['meaning']}. "
                    f"The shadow to watch: {e_info['shadow'].lower()}."
                )

        # Closing
        closing = "The numbers suggest this energy is present — not as prediction, but as pattern."

        # Calculate confidence from signals
        confidence = min(95, 50 + len(signals) * 5)

        # Enrichment: animal×element description
        animal_element_description = ""
        if dom_token:
            animal_element_description = ReadingEngine._describe_animal_element(
                dom_token
            )

        # Enrichment: cross-reference personal × current
        cross_insights = ReadingEngine._personal_x_current(
            numerology_profile, planet, moon_data
        )
        planet_moon_insight = ""
        lifepath_year_insight = ""
        planet_moon_insight_dict = {}
        lifepath_year_insight_dict = {}
        for ci in cross_insights:
            if ci["type"] == "planet_moon":
                planet_moon_insight = f"{ci['theme']}: {ci['message']}"
                planet_moon_insight_dict = {
                    "theme": ci["theme"],
                    "message": ci["message"],
                }
            elif ci["type"] == "lifepath_year":
                lifepath_year_insight = f"{ci['theme']}: {ci['message']}"
                lifepath_year_insight_dict = {
                    "theme": ci["theme"],
                    "message": ci["message"],
                }

        # Signal combination (if combiner available)
        combined_signals = None
        try:
            from synthesis.signal_combiner import SignalCombiner

            combined_signals = SignalCombiner.combine_signals(
                signals,
                numerology_profile or {},
                moon_data or {},
                ganzhi_data or {},
            )
        except ImportError:
            pass

        return {
            "opening": opening,
            "core_signal": core_signal,
            "day_energy": day_energy,
            "moon_context": moon_context,
            "personal_overlay": personal_overlay,
            "heartbeat_context": heartbeat_context,
            "location_context": location_context,
            "year_context": year_context,
            "time_context": time_ctx,
            "paradox": paradox,
            "closing": closing,
            "signals": signals,
            "animal_repetitions": repetitions,
            "confidence": confidence,
            # Enriched fields (v2.1)
            "animal_element_description": animal_element_description,
            "planet_moon_insight": planet_moon_insight,
            "lifepath_year_insight": lifepath_year_insight,
            "planet_moon_insight_dict": planet_moon_insight_dict,
            "lifepath_year_insight_dict": lifepath_year_insight_dict,
            "animals_collected": animals,
            "combined_signals": combined_signals,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("READING ENGINE - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test 1: Animal repetition detection
    animals = ["OX", "OX", "RA", "OX", "PI"]
    reps = ReadingEngine._detect_animal_repetitions(animals)
    if len(reps) == 1 and reps[0]["animal"] == "OX" and reps[0]["count"] == 3:
        print(f"✓ Animal repetition: OX×3 detected ({reps[0]['priority']})")
        passed += 1
    else:
        print(f"✗ Animal repetition: {reps}")
        failed += 1

    # Test 2: Time context
    ctx = ReadingEngine._time_context(14)
    if "Midday" in ctx["context"]:
        print(f"✓ Time context 14:00: {ctx['context']}")
        passed += 1
    else:
        print(f"✗ Time context 14:00: {ctx}")
        failed += 1

    # Test 3: Sun/Moon paradox
    fake_stamp = {"_half_marker": "☀"}
    paradox = ReadingEngine._check_sun_moon_paradox(fake_stamp, 3)
    if paradox and "light" in paradox:
        print(f"✓ Sun/Moon paradox detected at 03:00")
        passed += 1
    else:
        print(f"✗ Sun/Moon paradox not detected")
        failed += 1

    # Test 4: Full reading with mock data
    mock_stamp = {
        "_planet": "Venus",
        "_domain": "Love, values, beauty",
        "_weekday_name": "Friday",
        "_half_marker": "☀",
        "_hour_animal": "OX",
        "_minute_token": "RUWU",
        "_month_animal": "OX",
        "_dom_token": "OXFI",
    }
    reading = ReadingEngine.generate_reading(mock_stamp)
    if reading["opening"] and reading["signals"] and reading["confidence"] > 50:
        print(
            f"✓ Full reading: {len(reading['signals'])} signals, "
            f"confidence={reading['confidence']}%"
        )
        passed += 1
    else:
        print(f"✗ Full reading incomplete")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
