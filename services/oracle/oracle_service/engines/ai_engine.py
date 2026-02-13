"""
AI Engine — Scanner-focused AI functions for NPS.
==================================================
Delegates all AI calls to ai_client.py (Anthropic Python SDK).
No subprocess, no CLI — uses only the HTTP API.

Graceful degradation: if SDK/API key unavailable, all functions return safe defaults.
"""

import logging

from . import ai_client

logger = logging.getLogger(__name__)

NPS_SYSTEM_PROMPT = (
    "You are an expert numerologist and mathematician embedded in the NPS "
    "(Numerology Puzzle Solver) application. You understand:\n"
    "- FrankenChron-60 (FC60): a base-60 encoding system with 12 animals "
    "(RA, OX, TI, RU, DR, SN, HO, GO, MO, RO, DO, PI) and 5 elements "
    "(WU/Wood, FI/Fire, ER/Earth, MT/Metal, WA/Water)\n"
    "- Pythagorean numerology: digit reduction, master numbers (11, 22, 33), "
    "life path, expression, soul urge, personality numbers\n"
    "- Scoring factors: entropy, digit balance, primality, palindromes, "
    "repeating patterns, mod-60 cleanliness, power-of-2, animal repetition, "
    "element balance, moon alignment, ganzhi match, sacred geometry\n"
    "- Chinese calendar: 60-year ganzhi cycle, 12 earthly branches, "
    "10 heavenly stems, lunar phases\n"
    "- Bitcoin puzzle hunting: brute force, Pollard's kangaroo, "
    "scored candidate selection\n\n"
    "Keep responses concise and actionable. Use numerological and FC60 "
    "terminology naturally."
)


def is_available() -> bool:
    """Check if AI features are available (API key set + SDK importable)."""
    return ai_client.is_available()


def clear_cache() -> None:
    """Purge all cached AI responses."""
    ai_client.clear_cache()


def analyze_scan_pattern(
    tested_count: int,
    speed: float,
    hits: int,
    recent_addresses: list,
    scan_mode: str,
    memory_summary: str | None = None,
) -> dict:
    """Ask AI for tactical scanning advice based on current scan status.

    Returns dict: {suggestion, confidence, should_change_mode, recommended_mode}
    """
    defaults = {
        "suggestion": "",
        "confidence": 0.0,
        "should_change_mode": False,
        "recommended_mode": scan_mode,
    }

    if not is_available():
        return defaults

    addr_sample = ", ".join(recent_addresses[:5]) if recent_addresses else "none yet"
    memory_line = f"\nScan Memory: {memory_summary}\n" if memory_summary else ""
    prompt = (
        f"NPS Scanner Status:\n"
        f"- Keys tested: {tested_count:,}\n"
        f"- Speed: {speed:.0f}/s\n"
        f"- Hits: {hits}\n"
        f"- Mode: {scan_mode}\n"
        f"- Recent BTC addresses: {addr_sample}\n"
        f"{memory_line}\n"
        f"Give exactly 1 tactical suggestion for the scanner.\n"
        f"Format your response as:\n"
        f"SUGGESTION: <one sentence>\n"
        f"CONFIDENCE: <0.0 to 1.0>\n"
        f"CHANGE_MODE: <yes/no>\n"
        f"RECOMMENDED_MODE: <random_key/seed_phrase/both>"
    )

    result = ai_client.generate(prompt, system_prompt=NPS_SYSTEM_PROMPT)
    if not result.get("success"):
        return defaults

    response = result["response"]
    parsed = dict(defaults)
    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("SUGGESTION:"):
            parsed["suggestion"] = line[len("SUGGESTION:") :].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                parsed["confidence"] = float(line[len("CONFIDENCE:") :].strip())
            except ValueError:
                pass
        elif line.startswith("CHANGE_MODE:"):
            parsed["should_change_mode"] = "yes" in line.lower()
        elif line.startswith("RECOMMENDED_MODE:"):
            mode = line[len("RECOMMENDED_MODE:") :].strip().lower()
            if mode in ("random_key", "seed_phrase", "both"):
                parsed["recommended_mode"] = mode

    return parsed


def numerology_insight_for_key(private_key: int | str, addresses: dict) -> dict:
    """Get AI numerology insight for a high-scoring key.

    Returns dict: {fc60_token, score, analysis, math_highlights, numerology_highlights}
    """
    defaults = {
        "fc60_token": "",
        "score": 0.0,
        "analysis": "",
        "math_highlights": [],
        "numerology_highlights": [],
    }

    if not is_available():
        return defaults

    try:
        from engines.scoring import hybrid_score
    except ImportError:
        return defaults

    key_int = private_key if isinstance(private_key, int) else int(private_key, 16)
    score_result = hybrid_score(key_int)

    btc_addr = addresses.get("btc", "unknown")
    token = score_result.get("fc60_token", "----")
    score = score_result.get("final_score", 0.0)
    math_bd = score_result.get("math_breakdown", {})
    numer_bd = score_result.get("numerology_breakdown", {})

    prompt = (
        f"Key hex: {hex(key_int)[:20]}...\n"
        f"BTC address: {btc_addr}\n"
        f"FC60 token: {token}\n"
        f"Hybrid score: {score:.3f}\n"
        f"Math factors: {math_bd}\n"
        f"Numerology factors: {numer_bd}\n\n"
        f"Give a brief 2-sentence numerological insight about this key. "
        f"What makes it interesting from an FC60/numerology perspective?"
    )

    result = ai_client.generate(prompt, system_prompt=NPS_SYSTEM_PROMPT)
    if not result.get("success"):
        return {**defaults, "fc60_token": token, "score": score}

    math_highlights = [k for k, v in math_bd.items() if isinstance(v, (int, float)) and v > 0.7]
    numer_highlights = [k for k, v in numer_bd.items() if isinstance(v, (int, float)) and v > 0.7]

    return {
        "fc60_token": token,
        "score": score,
        "analysis": result["response"],
        "math_highlights": math_highlights,
        "numerology_highlights": numer_highlights,
    }


def brain_strategy_recommendation(history_summary: str) -> dict:
    """Ask AI which scanning strategy to try next.

    Returns dict: {strategy, confidence, reasoning}
    """
    defaults = {"strategy": "", "confidence": 0.0, "reasoning": ""}
    if not is_available():
        return defaults

    prompt = (
        f"Scanner Brain strategy history:\n{history_summary}\n\n"
        f"Available strategies: random, numerology_guided, entropy_targeted, "
        f"pattern_replay, time_aligned.\n\n"
        f"Based on past performance, which strategy should the scanner use next?\n"
        f"Format your response as:\n"
        f"STRATEGY: <strategy_name>\n"
        f"CONFIDENCE: <0.0 to 1.0>\n"
        f"REASONING: <one sentence>"
    )

    result = ai_client.generate(prompt, system_prompt=NPS_SYSTEM_PROMPT)
    if not result.get("success"):
        return defaults

    parsed = dict(defaults)
    for line in result["response"].split("\n"):
        line = line.strip()
        if line.startswith("STRATEGY:"):
            s = line[len("STRATEGY:") :].strip().lower()
            if s in (
                "random",
                "numerology_guided",
                "entropy_targeted",
                "pattern_replay",
                "time_aligned",
            ):
                parsed["strategy"] = s
        elif line.startswith("CONFIDENCE:"):
            try:
                parsed["confidence"] = float(line[len("CONFIDENCE:") :].strip())
            except ValueError:
                pass
        elif line.startswith("REASONING:"):
            parsed["reasoning"] = line[len("REASONING:") :].strip()

    return parsed


def brain_mid_session_analysis(session_stats: dict) -> dict:
    """Ask AI if the scanning strategy should adjust mid-session.

    Returns dict: {recommendation, confidence, should_switch}
    """
    defaults = {"recommendation": "", "confidence": 0.0, "should_switch": False}
    if not is_available():
        return defaults

    prompt = (
        f"Scanner Brain mid-session check:\n"
        f"- Strategy: {session_stats.get('strategy', 'unknown')}\n"
        f"- Keys tested: {session_stats.get('keys_tested', 0):,}\n"
        f"- Speed: {session_stats.get('speed', 0):.0f}/s\n"
        f"- Hits: {session_stats.get('hits', 0)}\n"
        f"- Findings this session: {session_stats.get('findings_this_session', 0)}\n"
        f"- Elapsed: {session_stats.get('elapsed', 0):.0f}s\n\n"
        f"Should the scanner adjust its strategy? Give a brief recommendation.\n"
        f"Format your response as:\n"
        f"RECOMMENDATION: <one sentence>\n"
        f"CONFIDENCE: <0.0 to 1.0>\n"
        f"SWITCH: <yes/no>"
    )

    result = ai_client.generate(prompt, system_prompt=NPS_SYSTEM_PROMPT)
    if not result.get("success"):
        return defaults

    parsed = dict(defaults)
    for line in result["response"].split("\n"):
        line = line.strip()
        if line.startswith("RECOMMENDATION:"):
            parsed["recommendation"] = line[len("RECOMMENDATION:") :].strip()
        elif line.startswith("CONFIDENCE:"):
            try:
                parsed["confidence"] = float(line[len("CONFIDENCE:") :].strip())
            except ValueError:
                pass
        elif line.startswith("SWITCH:"):
            parsed["should_switch"] = "yes" in line.lower()

    return parsed


def brain_session_summary(session_data: str) -> dict:
    """Ask AI for lessons learned from a scanning session.

    Returns dict: {effectiveness, key_learnings, recommendations}
    """
    defaults = {"effectiveness": "", "key_learnings": [], "recommendations": []}
    if not is_available():
        return defaults

    prompt = (
        f"Scanner Brain session completed. Analyze this session:\n{session_data}\n\n"
        f"Provide a brief post-session analysis.\n"
        f"Format your response as:\n"
        f"EFFECTIVENESS: <one sentence summary>\n"
        f"LEARNING_1: <key insight>\n"
        f"LEARNING_2: <key insight>\n"
        f"RECOMMEND_1: <next session recommendation>\n"
        f"RECOMMEND_2: <next session recommendation>"
    )

    result = ai_client.generate(prompt, system_prompt=NPS_SYSTEM_PROMPT)
    if not result.get("success"):
        return defaults

    parsed = dict(defaults)
    learnings = []
    recommendations = []
    for line in result["response"].split("\n"):
        line = line.strip()
        if line.startswith("EFFECTIVENESS:"):
            parsed["effectiveness"] = line[len("EFFECTIVENESS:") :].strip()
        elif line.startswith("LEARNING_"):
            val = line.split(":", 1)[-1].strip()
            if val:
                learnings.append(val)
        elif line.startswith("RECOMMEND_"):
            val = line.split(":", 1)[-1].strip()
            if val:
                recommendations.append(val)

    parsed["key_learnings"] = learnings
    parsed["recommendations"] = recommendations
    return parsed
