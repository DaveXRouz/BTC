"""
Prompt Templates for AI Interpretation
========================================
All prompt strings as constants with named str.format() placeholders.
Templates for 4 interpretation formats, group narratives, and translation.
"""

# ════════════════════════════════════════════════════════════
# System prompt — domain knowledge context
# ════════════════════════════════════════════════════════════

FC60_SYSTEM_PROMPT = (
    "You are a wise and warm numerology oracle who deeply understands:\n"
    "- FrankenChron-60 (FC60): a base-60 encoding system combining 12 animals "
    "(Rat, Ox, Tiger, Rabbit, Dragon, Snake, Horse, Goat, Monkey, Rooster, Dog, Pig) "
    "and 5 elements (Wood, Fire, Earth, Metal, Water) from the Chinese calendar\n"
    "- Wu Xing (Five Elements): the generating cycle (Wood→Fire→Earth→Metal→Water→Wood) "
    "and the overcoming cycle (Wood→Earth→Water→Fire→Metal→Wood)\n"
    "- Pythagorean numerology: life path numbers, expression numbers, soul urge, "
    "personality numbers, and master numbers (11, 22, 33)\n"
    "- Chinese Ganzhi (干支): 60-year cycle of Heavenly Stems and Earthly Branches\n"
    "- Lunar phases and their energetic influence\n"
    "- Western zodiac signs and their elemental associations\n\n"
    "You speak with authority but warmth. You weave multiple systems together "
    "into coherent, meaningful readings. You never dismiss or mock — every sign "
    "carries wisdom for those who seek it."
)

# ════════════════════════════════════════════════════════════
# Individual reading templates
# ════════════════════════════════════════════════════════════

SIMPLE_TEMPLATE = (
    "Give a simple, friendly interpretation of this FC60 reading. "
    "Use everyday language a 5th-grader would understand. Use analogies. "
    "Maximum 150 words.\n\n"
    "Person: {name}\n"
    "FC60 Sign: {fc60_sign}\n"
    "Element: {element}\n"
    "Animal: {animal}\n"
    "Life Path: {life_path}\n"
    "Zodiac: {zodiac_sign}\n"
    "Moon Phase: {moon_phase}\n"
    "Ganzhi: {ganzhi}\n"
    "Interpretation Summary: {interpretation}\n"
    "Synchronicities: {synchronicities}"
)

ADVICE_TEMPLATE = (
    "Give a warm, person-to-person reading as if speaking to a trusted friend. "
    "Be empathetic and encouraging. Show how the different systems connect. "
    "200-250 words.\n\n"
    "Person: {name}\n"
    "FC60 Sign: {fc60_sign}\n"
    "Element: {element}\n"
    "Animal: {animal}\n"
    "Life Path: {life_path}\n"
    "Zodiac: {zodiac_sign}\n"
    "Moon Phase: {moon_phase}\n"
    "Ganzhi: {ganzhi}\n"
    "Numerology Core: Expression {expression}, Soul Urge {soul_urge}, "
    "Personality {personality}\n"
    "Interpretation Summary: {interpretation}\n"
    "Synchronicities: {synchronicities}"
)

ACTION_STEPS_TEMPLATE = (
    "Based on this reading, provide exactly 3 concrete action steps. "
    "Each step should have a category and a specific action.\n"
    "Categories: Daily Practice, Decision-Making, Relationships.\n"
    "Format each as: **Category**: Action description.\n\n"
    "Person: {name}\n"
    "FC60 Sign: {fc60_sign}\n"
    "Element: {element}\n"
    "Animal: {animal}\n"
    "Life Path: {life_path}\n"
    "Zodiac: {zodiac_sign}\n"
    "Moon Phase: {moon_phase}\n"
    "Ganzhi: {ganzhi}\n"
    "Interpretation Summary: {interpretation}\n"
    "Synchronicities: {synchronicities}"
)

UNIVERSE_MESSAGE_TEMPLATE = (
    "Write a poetic, third-person message from the universe to this person. "
    "Begin with 'The universe sees...' and weave together all the symbolic "
    "threads from their reading. 150-200 words. Make it feel cosmic and personal.\n\n"
    "Person: {name}\n"
    "FC60 Sign: {fc60_sign}\n"
    "Element: {element}\n"
    "Animal: {animal}\n"
    "Life Path: {life_path}\n"
    "Zodiac: {zodiac_sign}\n"
    "Moon Phase: {moon_phase}\n"
    "Ganzhi: {ganzhi}\n"
    "Interpretation Summary: {interpretation}\n"
    "Synchronicities: {synchronicities}"
)

# ════════════════════════════════════════════════════════════
# Group / multi-user templates
# ════════════════════════════════════════════════════════════

GROUP_NARRATIVE_TEMPLATE = (
    "Write a narrative about this group's dynamics. Describe how they function "
    "together, their collective strengths, and areas for growth. "
    "Reference specific people by name and their roles. 200-300 words.\n\n"
    "Group Size: {user_count}\n"
    "Members: {member_summaries}\n"
    "Roles: {roles}\n"
    "Average Compatibility: {avg_compatibility}\n"
    "Strongest Bond: {strongest_bond}\n"
    "Weakest Bond: {weakest_bond}\n"
    "Synergies: {synergies}\n"
    "Challenges: {challenges}\n"
    "Growth Areas: {growth_areas}\n"
    "Group Archetype: {archetype} — {archetype_description}\n"
    "Dominant Element: {dominant_element}\n"
    "Dominant Animal: {dominant_animal}\n"
    "Joint Life Path: {joint_life_path}"
)

COMPATIBILITY_NARRATIVE_TEMPLATE = (
    "Write a brief, warm narrative about the compatibility between these two people. "
    "Highlight their strengths and gently note challenges. 100-150 words.\n\n"
    "Person 1: {user1} ({element1} {animal1}, LP {lp1})\n"
    "Person 2: {user2} ({element2} {animal2}, LP {lp2})\n"
    "Overall Score: {overall_score:.1%}\n"
    "Classification: {classification}\n"
    "Strengths: {strengths}\n"
    "Challenges: {challenges}\n"
    "Scores — Life Path: {lp_score:.1%}, Element: {element_score:.1%}, "
    "Animal: {animal_score:.1%}, Destiny: {destiny_score:.1%}, "
    "Name Energy: {name_energy_score:.1%}"
)

ENERGY_NARRATIVE_TEMPLATE = (
    "Write a brief narrative about this group's combined energy signature. "
    "Describe what this energy feels like and how it manifests. 100-150 words.\n\n"
    "Joint Life Path: {joint_life_path}\n"
    "Dominant Element: {dominant_element}\n"
    "Dominant Animal: {dominant_animal}\n"
    "Archetype: {archetype} — {archetype_description}\n"
    "Element Distribution: {element_distribution}\n"
    "Life Path Distribution: {life_path_distribution}"
)

# ════════════════════════════════════════════════════════════
# Translation templates
# ════════════════════════════════════════════════════════════

TRANSLATE_EN_FA_TEMPLATE = (
    "Translate the following English text to Persian (Farsi). "
    "Maintain a warm, poetic tone. "
    "IMPORTANT: Do NOT translate any of these terms — keep them in English: "
    "{preserved_terms}\n\n"
    "Text to translate:\n{text}"
)

TRANSLATE_FA_EN_TEMPLATE = (
    "Translate the following Persian (Farsi) text to English. "
    "Maintain the original tone and nuance. "
    "IMPORTANT: Do NOT translate any of these terms — keep them as-is: "
    "{preserved_terms}\n\n"
    "Text to translate:\n{text}"
)

BATCH_TRANSLATE_TEMPLATE = (
    "Translate each numbered item below from {source_lang} to {target_lang}. "
    "Keep the same numbering. "
    "IMPORTANT: Do NOT translate any of these terms — keep them as-is: "
    "{preserved_terms}\n\n"
    "{numbered_items}"
)

# ════════════════════════════════════════════════════════════
# Preserved terms — never translate these
# ════════════════════════════════════════════════════════════

FC60_PRESERVED_TERMS = [
    "FC60",
    "FrankenChron-60",
    "Wu Xing",
    "Wood",
    "Fire",
    "Earth",
    "Metal",
    "Water",
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
    "Ganzhi",
    "Life Path",
    "Soul Urge",
    "Expression",
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
    "WU",
    "FI",
    "ER",
    "MT",
    "WA",
]

# ════════════════════════════════════════════════════════════
# Template helper
# ════════════════════════════════════════════════════════════

# All valid format keys across all templates
_ALL_KEYS = {
    "name",
    "fc60_sign",
    "element",
    "animal",
    "life_path",
    "zodiac_sign",
    "moon_phase",
    "ganzhi",
    "interpretation",
    "synchronicities",
    "expression",
    "soul_urge",
    "personality",
    # Group keys
    "user_count",
    "member_summaries",
    "roles",
    "avg_compatibility",
    "strongest_bond",
    "weakest_bond",
    "synergies",
    "challenges",
    "growth_areas",
    "archetype",
    "archetype_description",
    "dominant_element",
    "dominant_animal",
    "joint_life_path",
    # Compatibility keys
    "user1",
    "user2",
    "element1",
    "animal1",
    "lp1",
    "element2",
    "animal2",
    "lp2",
    "overall_score",
    "classification",
    "strengths",
    "lp_score",
    "element_score",
    "animal_score",
    "destiny_score",
    "name_energy_score",
    # Energy keys
    "element_distribution",
    "life_path_distribution",
    # Translation keys
    "preserved_terms",
    "text",
    "source_lang",
    "target_lang",
    "numbered_items",
}


def build_prompt(template, context):
    """Safely format a template with context dict.

    Missing keys get "(not available)" as fallback value.
    Extra keys in context are silently ignored.

    Parameters
    ----------
    template : str
        A format string with {key} placeholders.
    context : dict
        Values to substitute.

    Returns
    -------
    str
        The formatted prompt.
    """
    safe_context = {}
    for key in _ALL_KEYS:
        safe_context[key] = context.get(key, "(not available)")
    # Also pass through any extra keys from context
    for key, val in context.items():
        if key not in safe_context:
            safe_context[key] = val
    try:
        return template.format(**safe_context)
    except (KeyError, IndexError, ValueError):
        # Last resort: return template with raw context appended
        return template + "\n\nContext: " + str(context)
