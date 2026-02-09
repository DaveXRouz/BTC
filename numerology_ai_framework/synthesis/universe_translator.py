"""
Universe Translator - Synthesis Tier Module 2
===============================================
Purpose: Transform reading data into final human-readable output
         9-section structured output with warm, wise tone
         "The numbers suggest" — never absolute predictions

Dependencies: ReadingEngine output, FC60 stamp, numerology profile
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Optional


class UniverseTranslator:
    """Translate readings into final human output."""

    LIFE_PATH_DESCRIPTIONS = {
        1: "You are a natural leader and pioneer. Your path is about independence, innovation, and forging new trails. You learn best through direct experience, and your greatest growth comes when you trust your own vision rather than waiting for permission. The world needs your initiative — the courage to go first.",
        2: "You are a natural mediator and connector. Your path is about cooperation, sensitivity, and creating harmony between opposing forces. You possess an extraordinary ability to sense what others need before they speak it. Your strength is not in leading the charge but in holding the space where others can find their best selves.",
        3: "You are a natural communicator and creator. Your path is about expression, joy, and inspiring others through words, art, and presence. Ideas flow through you like a current, and your challenge is choosing which ones to bring to life. When you express authentically, you give others permission to do the same.",
        4: "You are a natural builder and organizer. Your path is about structure, dedication, and creating lasting foundations that others can rely on. You understand that great things are built one careful step at a time. Your patience and discipline are not limitations — they are your superpower.",
        5: "You are a natural explorer and change agent. Your path is about freedom, adventure, and embracing transformation as a way of life. You are here to experience everything and to teach others that change is not something to fear. Your restlessness is not a flaw — it is your compass pointing toward growth.",
        6: "You are a natural nurturer and guardian. Your path is about responsibility, love, and creating beauty and harmony in your environment. You feel the weight of others' needs deeply, and your challenge is learning that caring for yourself is not selfish — it is essential. Your love creates sanctuaries wherever you go.",
        7: "You are a natural seeker and analyst. Your path is about wisdom, introspection, and finding deeper meaning beneath the surface of things. You are drawn to questions that others overlook, and you have the patience to sit with mystery until understanding arrives. Trust your inner knowing — it sees what logic cannot.",
        8: "You are a natural powerhouse and achiever. Your path is about mastery, abundance, and manifesting material success in service of a greater purpose. You understand the language of power and resources, and your challenge is wielding that power with integrity. When you align ambition with ethics, you become unstoppable.",
        9: "You are a natural sage and humanitarian. Your path is about completion, compassion, and serving the greater good with the wisdom you've gathered. You carry an old soul's understanding of human nature, and your challenge is releasing what you've outgrown. Your generosity of spirit lights the way for others.",
        11: "You carry the Master Number 11 — the Visionary. Your path is about spiritual insight, inspiration, and illuminating others with the clarity of your inner vision. You receive impressions and intuitions that others cannot access, and your challenge is grounding these visions in practical reality. When you trust your sight, you become a beacon.",
        22: "You carry the Master Number 22 — the Master Builder. Your path is about turning grand visions into tangible reality on a scale that serves many. You combine the intuition of 11 with the practical discipline of 4, creating something that outlasts you. Your blueprints are not just for buildings — they are for better worlds.",
        33: "You carry the Master Number 33 — the Master Teacher. Your path is about compassionate healing and wisdom leadership that uplifts entire communities. You combine the sensitivity of 2, the creativity of 3, and the nurturing of 6 into a force for transformation. Your presence itself is a teaching.",
    }

    EXPRESSION_DESCRIPTIONS = {
        1: "Your Expression 1 means you naturally present as a self-starter and original thinker. You manifest your potential through bold initiative, independent projects, and a willingness to stand alone when necessary.",
        2: "Your Expression 2 means you naturally present as a peacemaker and collaborator. You manifest your potential through partnerships, careful listening, and the ability to find common ground where others see only conflict.",
        3: "Your Expression 3 means you naturally present as a creative communicator and entertainer. You manifest your potential through words, art, humor, and the sheer magnetism of your self-expression.",
        4: "Your Expression 4 means you naturally present as a reliable builder and systematic thinker. You manifest your potential through methodical work, attention to detail, and the ability to turn chaos into order.",
        5: "Your Expression 5 means you naturally present as a versatile adventurer and change catalyst. You manifest your potential through adaptability, dynamic energy, and an infectious enthusiasm for new experiences.",
        6: "Your Expression 6 means you naturally present as a responsible caretaker and harmony-seeker. You manifest your potential through service, beauty creation, and the ability to make others feel safe and valued.",
        7: "Your Expression 7 means you naturally present as a thoughtful analyst and truth-seeker. You manifest your potential through research, contemplation, and insights that reveal hidden layers of meaning.",
        8: "Your Expression 8 means you naturally present as an authoritative achiever and strategic thinker. You manifest your potential through leadership, resource management, and the ability to execute ambitious visions.",
        9: "Your Expression 9 means you naturally present as a compassionate humanitarian and wise counselor. You manifest your potential through broad understanding, creative synthesis, and selfless service to ideals larger than yourself.",
        11: "Your Expression 11 carries Master Number energy in how you present to the world. You manifest your potential through inspired communication, spiritual insight, and the ability to channel higher wisdom into practical guidance.",
        22: "Your Expression 22 carries Master Number energy in how you present to the world. You manifest your potential through large-scale organization, visionary leadership, and the rare ability to build lasting institutions.",
        33: "Your Expression 33 carries Master Number energy in how you present to the world. You manifest your potential through selfless teaching, healing presence, and the ability to uplift others through compassionate wisdom.",
    }

    SOUL_URGE_DESCRIPTIONS = {
        1: "Your Soul Urge 1 reveals that deep within, you crave independence and the freedom to follow your own direction. Your heart is fulfilled when you are pioneering something new, leading by example, and proving that your unique vision has value.",
        2: "Your Soul Urge 2 reveals that deep within, you crave connection, peace, and genuine partnership. Your heart is fulfilled when you are creating harmony, being truly seen by someone who understands you, and contributing to something greater through collaboration.",
        3: "Your Soul Urge 3 reveals that deep within, you crave joyful self-expression and creative freedom. Your heart is fulfilled when you are creating, communicating your truth, and sharing the beauty you see in the world with others.",
        4: "Your Soul Urge 4 reveals that deep within, you crave stability, order, and a sense of having built something meaningful. Your heart is fulfilled when your world is structured, your efforts produce tangible results, and you know your work will endure.",
        5: "Your Soul Urge 5 reveals that deep within, you crave freedom, variety, and the thrill of new experience. Your heart is fulfilled when you are exploring, learning, and breaking free from anything that feels like a cage.",
        6: "Your Soul Urge 6 reveals that deep within, you crave love, beauty, and the knowledge that those you care for are safe. Your heart is fulfilled when your home is a sanctuary, your relationships are harmonious, and you are making the world more beautiful.",
        7: "Your Soul Urge 7 reveals that deep within, you crave understanding, solitude, and spiritual connection. Your heart is fulfilled when you are exploring the mysteries of life, spending time in contemplation, and discovering truths that transform your worldview.",
        8: "Your Soul Urge 8 reveals that deep within, you crave achievement, recognition, and the ability to make a significant impact. Your heart is fulfilled when your efforts produce measurable results, your authority is respected, and your resources serve a meaningful purpose.",
        9: "Your Soul Urge 9 reveals that deep within, you crave a sense of completion and the knowledge that your life has served others. Your heart is fulfilled when you are giving back, releasing attachments, and contributing to the healing of the world.",
        11: "Your Soul Urge 11 carries Master Number energy at the deepest level of desire. You crave spiritual truth and the ability to inspire others through your intuitive understanding. Your heart is fulfilled when you are channeling higher wisdom.",
        22: "Your Soul Urge 22 carries Master Number energy at the deepest level of desire. You crave the ability to build something that transforms society. Your heart is fulfilled when your grand visions take concrete form.",
        33: "Your Soul Urge 33 carries Master Number energy at the deepest level of desire. You crave the ability to heal through love and teach through compassion. Your heart is fulfilled when others grow through your presence.",
    }

    PERSONALITY_DESCRIPTIONS = {
        1: "Your Personality 1 means you project an image of independence, confidence, and originality. Others see you as a self-assured leader who walks their own path without hesitation.",
        2: "Your Personality 2 means you project an image of warmth, approachability, and gentle diplomacy. Others see you as someone who is easy to confide in and naturally cooperative.",
        3: "Your Personality 3 means you project an image of charm, wit, and creative flair. Others see you as expressive and socially magnetic — the one who lights up a room.",
        4: "Your Personality 4 means you project an image of reliability, discipline, and quiet competence. Others see you as someone they can count on — solid, practical, and trustworthy.",
        5: "Your Personality 5 means you project an image of dynamism, versatility, and magnetic energy. Others see you as adventurous and exciting — someone who embraces life fully.",
        6: "Your Personality 6 means you project an image of warmth, responsibility, and nurturing grace. Others see you as a natural caretaker — someone who creates beauty and harmony wherever they go.",
        7: "Your Personality 7 means you project an image of depth, intelligence, and quiet mystery. Others see you as thoughtful and discerning — someone whose still waters run deep.",
        8: "Your Personality 8 means you project an image of authority, ambition, and material competence. Others see you as powerful and capable — someone who commands respect naturally.",
        9: "Your Personality 9 means you project an image of wisdom, compassion, and worldly sophistication. Others see you as generous and broad-minded — someone with an old soul's understanding.",
        11: "Your Personality 11 carries Master Number energy in your outward presence. Others sense an unusual depth and intensity about you — an almost electric quality that inspires and unsettles in equal measure.",
        22: "Your Personality 22 carries Master Number energy in your outward presence. Others perceive you as someone capable of extraordinary things — a builder whose ambition operates on a grand scale.",
        33: "Your Personality 33 carries Master Number energy in your outward presence. Others feel uplifted in your company — your warmth and wisdom create a healing atmosphere that transforms those around you.",
    }

    PERSONAL_YEAR_THEMES = {
        1: "New beginnings, independence, and fresh starts",
        2: "Patience, partnerships, and quiet growth",
        3: "Creativity, expression, and social expansion",
        4: "Building foundations, hard work, and discipline",
        5: "Change, freedom, and adventurous exploration",
        6: "Home, family, and responsibility",
        7: "Reflection, spirituality, and inner wisdom",
        8: "Power, achievement, and material harvest",
        9: "Completion, release, and humanitarian service",
        11: "Spiritual awakening and heightened intuition",
        22: "Master building and large-scale manifestation",
        33: "Healing leadership and compassionate teaching",
    }

    # Position labels for FC60 stamp fields
    _POSITION_MAP = {
        "_month_animal": "the month",
        "_dom_token": "the day",
        "_hour_animal": "the hour",
        "_minute_token": "the minute",
    }

    @staticmethod
    def _split_insight(insight_str: str) -> tuple:
        """Parse 'Theme: Message' string into (theme, message) tuple."""
        if ": " in insight_str:
            theme, message = insight_str.split(": ", 1)
            return (theme, message)
        return ("", insight_str)

    @staticmethod
    def _position_names(fc60_stamp: Dict, animal_code: str) -> list:
        """Return list of position names where an animal appears."""
        positions = []
        for field, label in UniverseTranslator._POSITION_MAP.items():
            val = fc60_stamp.get(field, "")
            if val and val[:2] == animal_code:
                positions.append(label)
        return positions

    @staticmethod
    def translate(
        reading: Dict,
        fc60_stamp: Dict,
        numerology_profile: Dict = None,
        person_name: str = "",
        current_date_str: str = "",
        confidence_override: Optional[int] = None,
    ) -> Dict:
        """
        Translate a reading into final 9-section human output.

        Args:
            reading: Output from ReadingEngine.generate_reading()
            fc60_stamp: Output from FC60StampEngine.encode()
            numerology_profile: Output from NumerologyEngine.complete_profile()
            person_name: Person's name for header
            current_date_str: Formatted date string
            confidence_override: If provided, use this confidence score instead
                                 of the reading_engine's internal estimate.

        Returns:
            Dict with each section as string + full_text concatenation
        """
        sections = {}

        # Section 1: Header
        confidence = (
            confidence_override
            if confidence_override is not None
            else reading.get("confidence", 50)
        )
        if confidence >= 85:
            conf_label = "very_high"
        elif confidence >= 75:
            conf_label = "high"
        elif confidence >= 65:
            conf_label = "medium"
        else:
            conf_label = "developing"
        sections["header"] = (
            f"READING FOR {person_name.upper() or 'YOU'}\n"
            f"Date: {current_date_str or fc60_stamp.get('iso', 'Unknown')}\n"
            f"Confidence: {confidence}% ({conf_label})"
        )

        # Section 2: Universal Address
        sections["universal_address"] = (
            "Every moment has a unique signature — like coordinates that place you "
            "precisely in the flow of time. This is yours for today.\n\n"
            f"FC60: {fc60_stamp.get('fc60', 'N/A')}\n"
            f"J60:  {fc60_stamp.get('j60', 'N/A')}\n"
            f"Y60:  {fc60_stamp.get('y60', 'N/A')}"
        )

        # Section 3: Core Identity
        core_identity = ""
        if numerology_profile:
            lp = numerology_profile.get("life_path", {})
            lp_num = lp.get("number", 0)
            lp_desc = UniverseTranslator.LIFE_PATH_DESCRIPTIONS.get(lp_num, "")
            exp = numerology_profile.get("expression", 0)
            soul = numerology_profile.get("soul_urge", 0)
            pers = numerology_profile.get("personality", 0)
            py = numerology_profile.get("personal_year", 0)

            core_identity = f"Life Path {lp_num} — {lp.get('title', '')}\n{lp_desc}"

            exp_desc = UniverseTranslator.EXPRESSION_DESCRIPTIONS.get(exp, "")
            if exp_desc:
                core_identity += f"\n\n{exp_desc}"
            else:
                core_identity += f"\n\nExpression {exp}: This shapes how you manifest your potential in the world."

            soul_desc = UniverseTranslator.SOUL_URGE_DESCRIPTIONS.get(soul, "")
            if soul_desc:
                core_identity += f"\n\n{soul_desc}"
            else:
                core_identity += (
                    f"\nSoul Urge {soul}: This reveals what your heart truly desires."
                )

            pers_desc = UniverseTranslator.PERSONALITY_DESCRIPTIONS.get(pers, "")
            if pers_desc:
                core_identity += f"\n\n{pers_desc}"
            else:
                core_identity += f"\n\nPersonality {pers}: This is how others first perceive you — the impression you make before they know you deeply."

            py_theme = UniverseTranslator.PERSONAL_YEAR_THEMES.get(py, "")
            if py_theme:
                core_identity += f"\n\nPersonal Year {py}: {py_theme}. This theme colors every experience and decision you face this year."

            # LP x PY combo insight
            lpy_dict = reading.get("lifepath_year_insight_dict", {})
            if not lpy_dict and reading.get("lifepath_year_insight"):
                t, m = UniverseTranslator._split_insight(
                    reading["lifepath_year_insight"]
                )
                lpy_dict = {"theme": t, "message": m}
            if lpy_dict.get("theme"):
                lp_title = lp.get("title", f"Life Path {lp_num}")
                core_identity += (
                    f"\n\nYour Life Path {lp_num} meets Personal Year {py} in a moment "
                    f"the numbers call \"{lpy_dict['theme']}.\" "
                    f"The {lp_title} reaches a year shaped by that intersection. "
                    f"{lpy_dict['message']}"
                )
        sections["core_identity"] = core_identity

        # Section 3.5: Foundation (Mother's Name)
        foundation = ""
        if numerology_profile and numerology_profile.get("mother_influence"):
            mi = numerology_profile["mother_influence"]
            lp_num = numerology_profile.get("life_path", {}).get("number", 0)
            if mi == lp_num:
                foundation = (
                    f"Your mother's name carries Expression {mi}, which matches your Life Path. "
                    f"This deep alignment suggests your foundation and your purpose are woven from the same thread. "
                    f"The values instilled in you are the very ones you are here to live. "
                    f"Lean into this alignment — it is a source of quiet strength."
                )
            elif mi and lp_num:
                foundation = (
                    f"Your mother's name carries Expression {mi}, providing the foundation upon which your Life Path {lp_num} was built. "
                    f"This influence shaped your earliest understanding of the world and continues to inform your deepest instincts. "
                    f"Notice where these two energies create a productive tension in your life."
                )
        sections["foundation"] = foundation

        # Section 4: Right Now
        right_now_parts = []
        planet = fc60_stamp.get("_planet", "")
        domain = fc60_stamp.get("_domain", "")
        if planet:
            right_now_parts.append(
                f"Today is governed by {planet}, shaping the domain of {domain.lower()}. "
                f"Every conversation, decision, and impulse today carries a hint of this influence."
            )
        if reading.get("moon_context"):
            right_now_parts.append(reading["moon_context"])
        hour_signals = [
            s for s in reading.get("signals", []) if s.get("type") == "hour_animal"
        ]
        if hour_signals:
            right_now_parts.append(
                f"{hour_signals[0]['message']} Let this shape how you spend the next few hours."
            )
        # Planet-moon combo insight
        pm_dict = reading.get("planet_moon_insight_dict", {})
        if not pm_dict and reading.get("planet_moon_insight"):
            t, m = UniverseTranslator._split_insight(reading["planet_moon_insight"])
            pm_dict = {"theme": t, "message": m}
        if pm_dict.get("theme"):
            right_now_parts.append(
                f"When {planet or 'the planet'} meets this moon phase, the theme is "
                f"\"{pm_dict['theme']}.\" {pm_dict['message']}"
            )
        sections["right_now"] = "\n\n".join(right_now_parts)

        # Section 5: Patterns Detected
        patterns_parts = []
        reps = reading.get("animal_repetitions", [])
        if reps:
            patterns_parts.append(
                "When the same animal appears more than once, it is speaking louder "
                "than the rest. Here is what stands out today."
            )
        for rep in reps:
            positions = UniverseTranslator._position_names(fc60_stamp, rep["animal"])
            pos_str = ""
            if positions:
                pos_str = f" It shows up in {', '.join(positions)}."
            patterns_parts.append(
                f"The {rep['animal_name']} appears {rep['count']} times "
                f"({rep['priority']} signal): {rep['trait']}.{pos_str}"
            )
        # Animal harmony between different repeated animals
        if len(reps) >= 2:
            try:
                from synthesis.signal_combiner import SignalCombiner

                a1, a2 = reps[0]["animal"], reps[1]["animal"]
                if a1 != a2:
                    harmony = SignalCombiner.animal_harmony(a1, a2)
                    patterns_parts.append(
                        f"The {reps[0]['animal_name']} and {reps[1]['animal_name']} "
                        f"share a {harmony['type']} relationship. {harmony['meaning']}"
                    )
            except ImportError:
                pass
        if numerology_profile:
            nums = [
                numerology_profile.get("life_path", {}).get("number", 0),
                numerology_profile.get("expression", 0),
                numerology_profile.get("soul_urge", 0),
                numerology_profile.get("personality", 0),
                numerology_profile.get("personal_year", 0),
            ]
            from collections import Counter

            num_counts = Counter(nums)
            for num, count in num_counts.items():
                if count >= 2:
                    patterns_parts.append(
                        f"The number {num} appears {count} times in your profile — "
                        f"major thematic emphasis."
                    )
        sections["patterns"] = (
            "\n\n".join(patterns_parts)
            if patterns_parts
            else "No strong patterns detected at this time."
        )

        # Section 6: The Message (structured paragraphs)
        msg_paragraphs = []
        # Opening framing line
        msg_paragraphs.append(
            "Here is what the numbers, the animals, and the elements are saying when "
            "woven together into a single thread."
        )
        # Paragraph 1: Loudest signal + day energy
        p1_parts = []
        if reading.get("core_signal"):
            p1_parts.append(reading["core_signal"])
        if reading.get("day_energy"):
            p1_parts.append(reading["day_energy"])
        if p1_parts:
            msg_paragraphs.append(" ".join(p1_parts))
        # Paragraph 2: Personal context woven with universal rhythm
        p2_parts = []
        if reading.get("personal_overlay"):
            p2_parts.append(reading["personal_overlay"])
        if reading.get("year_context"):
            p2_parts.append(reading["year_context"])
        if reading.get("animal_element_description"):
            p2_parts.append(reading["animal_element_description"])
        if p2_parts:
            msg_paragraphs.append(" ".join(p2_parts))
        # Paragraph 3: Body and place — heartbeat + location
        p3_parts = []
        if reading.get("heartbeat_context"):
            p3_parts.append(reading["heartbeat_context"])
        if reading.get("location_context"):
            p3_parts.append(reading["location_context"])
        if p3_parts:
            msg_paragraphs.append(" ".join(p3_parts))
        sections["message"] = (
            "\n\n".join(msg_paragraphs)
            if msg_paragraphs
            else "The current moment carries a balanced energy without strong directional signals."
        )

        # Section 7: Today's Advice (guaranteed 3+ items)
        advice = []
        action_labels = [
            "Focus here first",
            "Keep this in mind",
            "Before the day ends",
        ]
        # Prefer combined_signals recommended_actions (more actionable)
        combined = reading.get("combined_signals")
        if combined and combined.get("recommended_actions"):
            for i, action in enumerate(combined["recommended_actions"][:3]):
                label = action_labels[i] if i < len(action_labels) else f"Also"
                advice.append(f"{i + 1}. **{label}**: {action}")
        # Fill from strongest signals if needed
        if len(advice) < 3:
            strongest_signals = sorted(
                reading.get("signals", []),
                key=lambda s: {
                    "Very High": 4,
                    "High": 3,
                    "Medium": 2,
                    "Low-Medium": 1,
                }.get(s.get("priority", ""), 0),
                reverse=True,
            )
            for signal in strongest_signals:
                if len(advice) >= 3:
                    break
                idx = len(advice)
                label = action_labels[idx] if idx < len(action_labels) else "Also"
                advice.append(f"{idx + 1}. **{label}**: {signal['message']}")
        # Guarantee minimum 3
        defaults = [
            "Stay present and observe the patterns unfolding around you.",
            "Journal about what feels resonant — the signals are personal.",
            "Take one small action aligned with the strongest energy you feel.",
        ]
        for d in defaults:
            if len(advice) >= 3:
                break
            idx = len(advice)
            label = action_labels[idx] if idx < len(action_labels) else "Also"
            advice.append(f"{idx + 1}. **{label}**: {d}")
        sections["advice"] = "\n\n".join(advice)

        # Section 8: Caution
        caution_parts = []
        caution_parts.append(
            "Every energy has a shadow. Knowing yours helps you work with it instead of against it."
        )
        if reading.get("paradox"):
            caution_parts.append(reading["paradox"])
        # Add shadow from day energy element with counter-strategy
        element_counters = {
            "Wood": "Ground yourself with one concrete task before chasing the next idea.",
            "Fire": "Step away from intensity for ten minutes. Cool water, a slow breath.",
            "Earth": "Shake up one small routine today. Movement prevents stagnation.",
            "Metal": "Let something be imperfect on purpose. Flexibility is strength too.",
            "Water": "Write down the three things that matter most right now. Clarity cuts through overwhelm.",
        }
        dom_token = fc60_stamp.get("_dom_token", "")
        if dom_token and len(dom_token) >= 4:
            element_part = dom_token[2:]
            from synthesis.reading_engine import ReadingEngine

            element_info = ReadingEngine.ELEMENT_MEANINGS.get(element_part, {})
            if element_info.get("shadow"):
                shadow_text = (
                    f"Watch for {element_info['shadow'].lower()} — the shadow side "
                    f"of today's {element_info['name']} energy."
                )
                counter = element_counters.get(element_info["name"], "")
                if counter:
                    shadow_text += f" {counter}"
                caution_parts.append(shadow_text)
        # Add tensions from signal combination
        combined = reading.get("combined_signals")
        if combined and combined.get("tensions"):
            for tension in combined["tensions"]:
                caution_parts.append(
                    f"Tension: {tension} Sit with this rather than forcing a resolution."
                )
        sections["caution"] = (
            "\n\n".join(caution_parts)
            if caution_parts
            else "No specific cautions for this moment."
        )

        # Section 9: Footer
        data_sources = ["FC60 stamp", "weekday calculation"]
        if numerology_profile:
            data_sources.append("Pythagorean numerology")
        if reading.get("moon_context"):
            data_sources.append("lunar phase")
        if reading.get("year_context"):
            data_sources.append("Gānzhī cycle")
        if reading.get("heartbeat_context"):
            data_sources.append("heartbeat estimation")
        if reading.get("location_context"):
            data_sources.append("location encoding")

        # Determine missing data dimensions
        missing_data = []
        if not reading.get("location_context"):
            missing_data.append("location")
        if not numerology_profile or not numerology_profile.get("mother_influence"):
            missing_data.append("mother's name")
        if not reading.get("heartbeat_context"):
            missing_data.append("heartbeat")
        # Check if hour/time was provided (hour_animal signal present)
        hour_signals = [
            s for s in reading.get("signals", []) if s.get("type") == "hour_animal"
        ]
        if not hour_signals:
            missing_data.append("exact time of day")

        footer_text = (
            f"Confidence: {confidence}% ({conf_label})\n"
            f"Data sources: {', '.join(data_sources)}"
        )
        if missing_data:
            footer_text += f"\nNot provided: {', '.join(missing_data)}"
        footer_text += (
            f"\nDisclaimer: This reading suggests patterns, not predictions. "
            f"Use as one input among many for reflection and decision-making."
        )
        sections["footer"] = footer_text

        # Build full text
        divider = "\n" + "—" * 50 + "\n"
        full_parts = [
            sections["header"],
            divider,
            "YOUR UNIVERSAL ADDRESS",
            sections["universal_address"],
            divider,
            "CORE IDENTITY",
            sections["core_identity"],
        ]
        if sections.get("foundation"):
            full_parts.extend([divider, "FOUNDATION", sections["foundation"]])
        full_parts.extend(
            [
                divider,
                "RIGHT NOW",
                sections["right_now"],
                divider,
                "PATTERNS DETECTED",
                sections["patterns"],
                divider,
                "THE MESSAGE",
                sections["message"],
                divider,
                "TODAY'S ADVICE",
                sections["advice"],
                divider,
                "CAUTION",
                sections["caution"],
                divider,
                sections["footer"],
            ]
        )
        sections["full_text"] = "\n".join(full_parts)

        return sections


if __name__ == "__main__":
    print("=" * 60)
    print("UNIVERSE TRANSLATOR - SELF TEST")
    print("=" * 60)

    passed = 0
    failed = 0

    # Test with mock data
    mock_reading = {
        "opening": "Test opening",
        "core_signal": "The Ox appears 3 times.",
        "day_energy": "Fire energy today.",
        "moon_context": "🌖 Waning Gibbous — Share energy.",
        "personal_overlay": "Life Path 5 asks you to explore.",
        "heartbeat_context": "",
        "location_context": "",
        "year_context": "Year of the Fire Horse.",
        "paradox": None,
        "closing": "Numbers suggest.",
        "signals": [
            {
                "type": "animal_repetition",
                "priority": "Very High",
                "message": "Ox appears 3 times",
            },
            {"type": "day_planet", "priority": "Medium", "message": "Venus day"},
            {"type": "moon_phase", "priority": "Medium", "message": "Waning Gibbous"},
        ],
        "animal_repetitions": [
            {
                "animal": "OX",
                "animal_name": "Ox",
                "count": 3,
                "priority": "Very High",
                "trait": "Endurance",
                "action": "Persist",
            }
        ],
        "confidence": 80,
    }

    mock_stamp = {
        "fc60": "VE-OX-OXFI ☀OX-RUWU-RAWU",
        "iso": "2026-02-06T01:15:00+08:00",
        "j60": "TIFI-DRMT-GOER-PIMT",
        "y60": "HOMT-ROFI",
        "_planet": "Venus",
        "_domain": "Love, values, beauty",
        "_dom_token": "OXFI",
    }

    mock_numerology = {
        "life_path": {"number": 5, "title": "Explorer", "message": "Change and adapt"},
        "expression": 8,
        "soul_urge": 3,
        "personality": 5,
        "personal_year": 5,
    }

    result = UniverseTranslator.translate(
        mock_reading,
        mock_stamp,
        mock_numerology,
        person_name="Alice Johnson",
        current_date_str="2026-02-06",
    )

    # Test 1: All sections present
    required_sections = [
        "header",
        "universal_address",
        "core_identity",
        "right_now",
        "patterns",
        "message",
        "advice",
        "caution",
        "footer",
        "full_text",
    ]
    all_present = all(s in result for s in required_sections)
    if all_present:
        print(f"✓ All {len(required_sections)} sections present")
        passed += 1
    else:
        missing = [s for s in required_sections if s not in result]
        print(f"✗ Missing sections: {missing}")
        failed += 1

    # Test 2: Header contains name
    if "ALICE JOHNSON" in result["header"]:
        print(f"✓ Header contains person name")
        passed += 1
    else:
        print(f"✗ Header missing name")
        failed += 1

    # Test 3: Full text is non-empty
    if len(result["full_text"]) > 100:
        print(f"✓ Full text generated ({len(result['full_text'])} chars)")
        passed += 1
    else:
        print(f"✗ Full text too short")
        failed += 1

    # Test 4: Patterns detected
    if "Ox" in result["patterns"]:
        print(f"✓ Patterns include animal repetition")
        passed += 1
    else:
        print(f"✗ Patterns missing animal info")
        failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
