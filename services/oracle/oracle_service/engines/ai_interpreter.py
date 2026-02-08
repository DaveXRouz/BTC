"""
AI Interpreter — Human-Friendly Reading Interpretations
========================================================
High-level interpretation engine that consumes output from:
  - oracle.read_sign() → individual sign reading
  - oracle.read_name() → name-based reading
  - MultiUserFC60Service.analyze() → multi-user group analysis

Produces 4 interpretation formats (simple, advice, action_steps, universe_message),
AI-enhanced multi-user narratives, and deterministic fallbacks when AI is unavailable.
"""

import time

from engines.ai_client import generate, is_available
from engines.prompt_templates import (
    FC60_SYSTEM_PROMPT,
    SIMPLE_TEMPLATE,
    ADVICE_TEMPLATE,
    ACTION_STEPS_TEMPLATE,
    UNIVERSE_MESSAGE_TEMPLATE,
    GROUP_NARRATIVE_TEMPLATE,
    COMPATIBILITY_NARRATIVE_TEMPLATE,
    ENERGY_NARRATIVE_TEMPLATE,
    build_prompt,
)

# Valid format types
_VALID_FORMATS = ("simple", "advice", "action_steps", "universe_message")

_FORMAT_TEMPLATES = {
    "simple": SIMPLE_TEMPLATE,
    "advice": ADVICE_TEMPLATE,
    "action_steps": ACTION_STEPS_TEMPLATE,
    "universe_message": UNIVERSE_MESSAGE_TEMPLATE,
}


# ════════════════════════════════════════════════════════════
# Result classes
# ════════════════════════════════════════════════════════════


class InterpretationResult:
    """Result of a single interpretation."""

    __slots__ = ("format", "text", "ai_generated", "elapsed_ms", "cached")

    def __init__(self, fmt, text, ai_generated, elapsed_ms, cached):
        self.format = fmt
        self.text = text
        self.ai_generated = ai_generated
        self.elapsed_ms = elapsed_ms
        self.cached = cached

    def to_dict(self):
        return {
            "format": self.format,
            "text": self.text,
            "ai_generated": self.ai_generated,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "cached": self.cached,
        }

    def __repr__(self):
        src = "AI" if self.ai_generated else "fallback"
        return f"InterpretationResult({self.format!r}, {src}, {len(self.text)} chars)"


class MultiFormatResult:
    """Result of interpreting a reading in all 4 formats."""

    __slots__ = (
        "simple",
        "advice",
        "action_steps",
        "universe_message",
        "ai_available",
        "computation_ms",
    )

    def __init__(
        self,
        simple,
        advice,
        action_steps,
        universe_message,
        ai_available,
        computation_ms,
    ):
        self.simple = simple
        self.advice = advice
        self.action_steps = action_steps
        self.universe_message = universe_message
        self.ai_available = ai_available
        self.computation_ms = computation_ms

    def to_dict(self):
        return {
            "simple": self.simple.to_dict(),
            "advice": self.advice.to_dict(),
            "action_steps": self.action_steps.to_dict(),
            "universe_message": self.universe_message.to_dict(),
            "ai_available": self.ai_available,
            "computation_ms": round(self.computation_ms, 1),
        }

    def __repr__(self):
        return (
            f"MultiFormatResult(ai={self.ai_available}, "
            f"{self.computation_ms:.0f}ms)"
        )


class GroupInterpretationResult:
    """Result of interpreting a multi-user group analysis."""

    __slots__ = (
        "compatibility_narrative",
        "dynamics_narrative",
        "energy_narrative",
        "individual_insights",
        "ai_available",
        "computation_ms",
    )

    def __init__(
        self,
        compatibility_narrative,
        dynamics_narrative,
        energy_narrative,
        individual_insights,
        ai_available,
        computation_ms,
    ):
        self.compatibility_narrative = compatibility_narrative
        self.dynamics_narrative = dynamics_narrative
        self.energy_narrative = energy_narrative
        self.individual_insights = individual_insights
        self.ai_available = ai_available
        self.computation_ms = computation_ms

    def to_dict(self):
        return {
            "compatibility_narrative": self.compatibility_narrative,
            "dynamics_narrative": self.dynamics_narrative,
            "energy_narrative": self.energy_narrative,
            "individual_insights": self.individual_insights,
            "ai_available": self.ai_available,
            "computation_ms": round(self.computation_ms, 1),
        }

    def __repr__(self):
        return (
            f"GroupInterpretationResult(ai={self.ai_available}, "
            f"{len(self.individual_insights)} insights)"
        )


# ════════════════════════════════════════════════════════════
# Public API — Individual readings
# ════════════════════════════════════════════════════════════


def interpret_reading(reading_data, format_type="simple", name=""):
    """Interpret a sign reading in the specified format.

    Parameters
    ----------
    reading_data : dict
        Output of oracle.read_sign() — keys: sign, numbers, systems,
        interpretation, synchronicities.
    format_type : str
        One of: simple, advice, action_steps, universe_message.
    name : str
        Optional person's name for personalization.

    Returns
    -------
    InterpretationResult
    """
    if format_type not in _VALID_FORMATS:
        return InterpretationResult(
            fmt=format_type,
            text=f"Unknown format '{format_type}'. Valid: {', '.join(_VALID_FORMATS)}",
            ai_generated=False,
            elapsed_ms=0.0,
            cached=False,
        )

    ctx = _build_reading_context(reading_data, name)
    template = _FORMAT_TEMPLATES[format_type]
    prompt = build_prompt(template, ctx)

    start = time.time()

    if is_available():
        result = generate(prompt, system_prompt=FC60_SYSTEM_PROMPT)
        elapsed_ms = (time.time() - start) * 1000

        if result["success"]:
            return InterpretationResult(
                fmt=format_type,
                text=result["response"],
                ai_generated=True,
                elapsed_ms=elapsed_ms,
                cached=result["cached"],
            )

    # Fallback
    elapsed_ms = (time.time() - start) * 1000
    fallback_fn = _FALLBACK_MAP.get(format_type, _fallback_simple)
    fallback_text = fallback_fn(ctx)

    return InterpretationResult(
        fmt=format_type,
        text=fallback_text,
        ai_generated=False,
        elapsed_ms=elapsed_ms,
        cached=False,
    )


def interpret_name(name_data, format_type="simple"):
    """Interpret a name reading in the specified format.

    Parameters
    ----------
    name_data : dict
        Output of oracle.read_name() — keys: name, expression, soul_urge,
        personality, life_path, interpretation.
    format_type : str
        One of: simple, advice, action_steps, universe_message.

    Returns
    -------
    InterpretationResult
    """
    # Build a reading-like context from name data
    ctx = {
        "name": name_data.get("name", ""),
        "fc60_sign": "",
        "element": "",
        "animal": "",
        "life_path": name_data.get("life_path", ""),
        "zodiac_sign": (
            name_data.get("birthday_zodiac", {}).get("sign", "")
            if isinstance(name_data.get("birthday_zodiac"), dict)
            else ""
        ),
        "moon_phase": "",
        "ganzhi": "",
        "interpretation": name_data.get("interpretation", ""),
        "synchronicities": "",
        "expression": name_data.get("expression", ""),
        "soul_urge": name_data.get("soul_urge", ""),
        "personality": name_data.get("personality", ""),
    }
    return interpret_reading(
        {
            "systems": {},
            "interpretation": name_data.get("interpretation", ""),
            "synchronicities": [],
        },
        format_type=format_type,
        name=name_data.get("name", ""),
    )


def interpret_all_formats(reading_data, name=""):
    """Interpret a sign reading in all 4 formats.

    Parameters
    ----------
    reading_data : dict
        Output of oracle.read_sign().
    name : str
        Optional person's name.

    Returns
    -------
    MultiFormatResult
    """
    start = time.time()

    simple = interpret_reading(reading_data, "simple", name)
    advice = interpret_reading(reading_data, "advice", name)
    action_steps = interpret_reading(reading_data, "action_steps", name)
    universe = interpret_reading(reading_data, "universe_message", name)

    elapsed_ms = (time.time() - start) * 1000

    return MultiFormatResult(
        simple=simple,
        advice=advice,
        action_steps=action_steps,
        universe_message=universe,
        ai_available=is_available(),
        computation_ms=elapsed_ms,
    )


# ════════════════════════════════════════════════════════════
# Public API — Group interpretation
# ════════════════════════════════════════════════════════════


def interpret_group(analysis_dict):
    """Interpret a multi-user group analysis.

    Parameters
    ----------
    analysis_dict : dict
        Output of MultiUserAnalysisResult.to_dict().

    Returns
    -------
    GroupInterpretationResult
    """
    start = time.time()

    group_ctx = _build_group_context(analysis_dict)

    # 1. Dynamics narrative
    dynamics_prompt = build_prompt(GROUP_NARRATIVE_TEMPLATE, group_ctx)
    dynamics_narrative = ""

    # 2. Energy narrative
    energy_ctx = {
        "joint_life_path": group_ctx.get("joint_life_path", ""),
        "dominant_element": group_ctx.get("dominant_element", ""),
        "dominant_animal": group_ctx.get("dominant_animal", ""),
        "archetype": group_ctx.get("archetype", ""),
        "archetype_description": group_ctx.get("archetype_description", ""),
        "element_distribution": group_ctx.get("element_distribution", ""),
        "life_path_distribution": group_ctx.get("life_path_distribution", ""),
    }
    energy_prompt = build_prompt(ENERGY_NARRATIVE_TEMPLATE, energy_ctx)
    energy_narrative = ""

    # 3. Compatibility narratives for each pair
    compatibility_parts = []
    pairwise = analysis_dict.get("pairwise_compatibility", [])
    profiles_by_name = {}
    for p in analysis_dict.get("profiles", []):
        profiles_by_name[p["name"]] = p

    ai_avail = is_available()

    if ai_avail:
        # Generate dynamics narrative
        result = generate(dynamics_prompt, system_prompt=FC60_SYSTEM_PROMPT)
        if result["success"]:
            dynamics_narrative = result["response"]

        # Generate energy narrative
        result = generate(energy_prompt, system_prompt=FC60_SYSTEM_PROMPT)
        if result["success"]:
            energy_narrative = result["response"]

        # Generate compatibility narratives for each pair
        for pair in pairwise:
            compat_ctx = _build_compat_context(pair, profiles_by_name)
            compat_prompt = build_prompt(COMPATIBILITY_NARRATIVE_TEMPLATE, compat_ctx)
            result = generate(compat_prompt, system_prompt=FC60_SYSTEM_PROMPT)
            if result["success"]:
                compatibility_parts.append(result["response"])
            else:
                compatibility_parts.append(
                    _fallback_compatibility(pair, profiles_by_name)
                )

    # Fallbacks
    if not dynamics_narrative:
        dynamics_narrative = _fallback_dynamics(group_ctx)
    if not energy_narrative:
        energy_narrative = _fallback_energy(energy_ctx)
    if not compatibility_parts:
        for pair in pairwise:
            compatibility_parts.append(_fallback_compatibility(pair, profiles_by_name))

    compatibility_narrative = "\n\n".join(compatibility_parts)

    # 4. Individual insights (brief summary per person)
    individual_insights = {}
    for profile in analysis_dict.get("profiles", []):
        name = profile["name"]
        individual_insights[name] = (
            f"{name}: {profile.get('element', '?')} {profile.get('animal', '?')}, "
            f"Life Path {profile.get('life_path', '?')}, "
            f"Destiny {profile.get('destiny_number', '?')}"
        )

    elapsed_ms = (time.time() - start) * 1000

    return GroupInterpretationResult(
        compatibility_narrative=compatibility_narrative,
        dynamics_narrative=dynamics_narrative,
        energy_narrative=energy_narrative,
        individual_insights=individual_insights,
        ai_available=ai_avail,
        computation_ms=elapsed_ms,
    )


# ════════════════════════════════════════════════════════════
# Context builders
# ════════════════════════════════════════════════════════════


def _build_reading_context(reading_data, name=""):
    """Extract a flat context dict from a nested reading result."""
    systems = reading_data.get("systems", {})

    # FC60 system
    fc60 = systems.get("fc60", {})
    fc60_sign = fc60.get("token", fc60.get("full_output", ""))

    # Numerology
    numer = systems.get("numerology", {})
    life_path_val = ""
    if numer.get("life_path"):
        life_path_val = str(numer["life_path"])
    elif numer.get("reductions"):
        # Sometimes stored as list of reductions
        reds = numer["reductions"]
        if reds:
            life_path_val = str(reds[0].get("reduced", ""))

    # Moon
    moon = systems.get("moon", {})
    moon_phase = moon.get("phase", "")

    # Ganzhi
    ganzhi = systems.get("ganzhi", {})
    ganzhi_str = ganzhi.get("year_pillar", "")
    if ganzhi.get("hour_pillar"):
        ganzhi_str += f", hour: {ganzhi['hour_pillar']}"

    # Zodiac
    zodiac = systems.get("zodiac", {})
    zodiac_sign = zodiac.get("sign", "")

    # Synchronicities
    syncs = reading_data.get("synchronicities", [])
    sync_str = "; ".join(syncs) if syncs else "none detected"

    return {
        "name": name or "Seeker",
        "fc60_sign": fc60_sign or "(not available)",
        "element": fc60.get("element", "(not available)"),
        "animal": fc60.get("animal", "(not available)"),
        "life_path": life_path_val or "(not available)",
        "zodiac_sign": zodiac_sign or "(not available)",
        "moon_phase": moon_phase or "(not available)",
        "ganzhi": ganzhi_str or "(not available)",
        "interpretation": reading_data.get("interpretation", ""),
        "synchronicities": sync_str,
        "expression": str(numer.get("expression", "")),
        "soul_urge": str(numer.get("soul_urge", "")),
        "personality": str(numer.get("personality", "")),
    }


def _build_group_context(analysis_dict):
    """Build a flat context dict from a multi-user analysis result dict."""
    profiles = analysis_dict.get("profiles", [])
    dynamics = analysis_dict.get("group_dynamics", {})
    energy = analysis_dict.get("group_energy", {})

    member_summaries = "; ".join(
        f"{p['name']} ({p.get('element', '?')} {p.get('animal', '?')}, "
        f"LP {p.get('life_path', '?')})"
        for p in profiles
    )

    roles = dynamics.get("roles", {})
    roles_str = "; ".join(f"{name}: {role}" for name, role in roles.items())

    return {
        "user_count": str(analysis_dict.get("user_count", len(profiles))),
        "member_summaries": member_summaries,
        "roles": roles_str,
        "avg_compatibility": str(dynamics.get("avg_compatibility", "")),
        "strongest_bond": str(dynamics.get("strongest_bond", "")),
        "weakest_bond": str(dynamics.get("weakest_bond", "")),
        "synergies": "; ".join(dynamics.get("synergies", [])),
        "challenges": "; ".join(dynamics.get("challenges", [])),
        "growth_areas": "; ".join(dynamics.get("growth_areas", [])),
        "archetype": energy.get("archetype", ""),
        "archetype_description": energy.get("archetype_description", ""),
        "dominant_element": energy.get("dominant_element", ""),
        "dominant_animal": energy.get("dominant_animal", ""),
        "joint_life_path": str(energy.get("joint_life_path", "")),
        "element_distribution": str(energy.get("element_distribution", {})),
        "life_path_distribution": str(energy.get("life_path_distribution", {})),
    }


def _build_compat_context(pair_dict, profiles_by_name):
    """Build context for a compatibility narrative from a pairwise dict."""
    user1 = pair_dict.get("user1", "")
    user2 = pair_dict.get("user2", "")
    p1 = profiles_by_name.get(user1, {})
    p2 = profiles_by_name.get(user2, {})
    scores = pair_dict.get("scores", {})

    return {
        "user1": user1,
        "user2": user2,
        "element1": p1.get("element", "?"),
        "animal1": p1.get("animal", "?"),
        "lp1": str(p1.get("life_path", "?")),
        "element2": p2.get("element", "?"),
        "animal2": p2.get("animal", "?"),
        "lp2": str(p2.get("life_path", "?")),
        "overall_score": scores.get("overall", pair_dict.get("overall_score", 0)),
        "classification": pair_dict.get("classification", ""),
        "strengths": "; ".join(pair_dict.get("strengths", [])),
        "challenges": "; ".join(pair_dict.get("challenges", [])),
        "lp_score": scores.get("life_path", 0),
        "element_score": scores.get("element", 0),
        "animal_score": scores.get("animal", 0),
        "destiny_score": scores.get("destiny", 0),
        "name_energy_score": scores.get("name_energy", 0),
    }


# ════════════════════════════════════════════════════════════
# Deterministic fallbacks
# ════════════════════════════════════════════════════════════


def _fallback_simple(ctx):
    """Simple fallback using raw data."""
    name = ctx.get("name", "Seeker")
    element = ctx.get("element", "unknown")
    animal = ctx.get("animal", "unknown")
    lp = ctx.get("life_path", "unknown")
    zodiac = ctx.get("zodiac_sign", "")

    parts = [f"Your FC60 signature is {element} {animal} with Life Path {lp}."]
    if zodiac and zodiac != "(not available)":
        parts.append(f"As a {zodiac}, you carry that sign's natural gifts.")
    parts.append(
        f"The {element} element shapes how you interact with the world, "
        f"while the {animal} energy guides your instincts."
    )
    return " ".join(parts)


def _fallback_advice(ctx):
    """Advice fallback using raw data."""
    name = ctx.get("name", "friend")
    element = ctx.get("element", "your element")
    animal = ctx.get("animal", "your animal sign")
    lp = ctx.get("life_path", "your life path")
    moon = ctx.get("moon_phase", "")

    text = (
        f"Dear {name}, your {element} {animal} nature gives you a unique perspective. "
        f"With Life Path {lp}, you're drawn to understanding and growth. "
    )
    if moon and moon != "(not available)":
        text += f"The current {moon} moon phase supports reflection and planning. "
    text += (
        "Trust the patterns you see — they are not coincidence. "
        "Your numerological signature suggests this is a time for "
        "thoughtful action rather than rushing forward."
    )
    return text


def _fallback_actions(ctx):
    """Action steps fallback using raw data."""
    element = ctx.get("element", "your element")
    animal = ctx.get("animal", "your sign")

    return (
        f"**Daily Practice**: Spend 5 minutes each morning connecting with your "
        f"{element} energy — notice where it shows up in your environment.\n\n"
        f"**Decision-Making**: When faced with choices, ask yourself: "
        f"'What would {animal} energy guide me toward?' — trust your instincts.\n\n"
        f"**Relationships**: Share your numerological insights with someone close "
        f"to you today. Understanding each other's energetic signatures "
        f"deepens connection."
    )


def _fallback_universe(ctx):
    """Universe message fallback using raw data."""
    name = ctx.get("name", "dear one")
    element = ctx.get("element", "the elements")
    animal = ctx.get("animal", "ancient wisdom")
    lp = ctx.get("life_path", "a sacred number")

    return (
        f"The universe sees {name} as a bearer of {element} energy, "
        f"walking the path of {animal} with the wisdom of Life Path {lp}. "
        f"Every number you encounter, every pattern that catches your eye, "
        f"is the cosmos whispering its secrets to one who listens. "
        f"You are not separate from the great mathematical fabric — "
        f"you are woven into it, a unique thread that the pattern needs."
    )


def _fallback_dynamics(ctx):
    """Group dynamics fallback narrative."""
    members = ctx.get("member_summaries", "the group members")
    roles = ctx.get("roles", "various roles")
    avg = ctx.get("avg_compatibility", "moderate")
    archetype = ctx.get("archetype", "a unique collective")

    return (
        f"This group of {ctx.get('user_count', 'several')} individuals — "
        f"{members} — forms {archetype}. "
        f"With roles spanning {roles}, the group achieves an average compatibility "
        f"of {avg}. Their combined energies create a dynamic where each member's "
        f"strengths complement the others' areas for growth."
    )


def _fallback_energy(ctx):
    """Group energy fallback narrative."""
    dominant = ctx.get("dominant_element", "mixed")
    animal = ctx.get("dominant_animal", "diverse")
    jlp = ctx.get("joint_life_path", "?")
    archetype = ctx.get("archetype", "unique")

    return (
        f"The group's combined energy signature reveals a {dominant}-dominant "
        f"collective with {animal} as the prevailing animal energy. "
        f"Their joint Life Path of {jlp} suggests a shared destiny direction. "
        f"As '{archetype}', this group naturally gravitates toward collective evolution."
    )


def _fallback_compatibility(pair_dict, profiles_by_name):
    """Single pair compatibility fallback."""
    user1 = pair_dict.get("user1", "Person 1")
    user2 = pair_dict.get("user2", "Person 2")
    scores = pair_dict.get("scores", {})
    overall = scores.get("overall", pair_dict.get("overall_score", 0))
    classification = pair_dict.get("classification", "Neutral")

    p1 = profiles_by_name.get(user1, {})
    p2 = profiles_by_name.get(user2, {})

    return (
        f"{user1} ({p1.get('element', '?')} {p1.get('animal', '?')}) and "
        f"{user2} ({p2.get('element', '?')} {p2.get('animal', '?')}) share a "
        f"{classification.lower()} connection at {overall:.0%} overall compatibility. "
        f"Their bond draws from {'strong' if overall > 0.6 else 'growing'} "
        f"elemental and life path resonance."
    )


# Fallback dispatch map
_FALLBACK_MAP = {
    "simple": _fallback_simple,
    "advice": _fallback_advice,
    "action_steps": _fallback_actions,
    "universe_message": _fallback_universe,
}
