"""
Scoring Engine
==============
Combines math analysis, numerology, and learned patterns
into a single harmony score for any candidate number.

The scoring engine is the BRIDGE between numerology and puzzle solving.
"""

import logging
import time
from collections import Counter

from engines import fc60, numerology, math_analysis

logger = logging.getLogger(__name__)

# Default weights (overridden by learning engine)
DEFAULT_WEIGHTS = {
    "math_weight": 0.40,
    "numerology_weight": 0.30,
    "learned_weight": 0.30,
}

# Sub-factor weights within math score
MATH_FACTORS = {
    "entropy_low": 0.20,
    "digit_balance": 0.15,
    "is_prime": 0.10,
    "palindrome": 0.15,
    "repeating": 0.15,
    "mod60_clean": 0.15,
    "power_of_2": 0.10,
}

# Sub-factor weights within numerology score
NUMEROLOGY_FACTORS = {
    "master_number": 0.25,
    "animal_repetition": 0.20,
    "element_balance": 0.15,
    "life_path_power": 0.15,
    "moon_alignment": 0.10,
    "ganzhi_match": 0.10,
    "sacred_geometry": 0.05,
}


def math_score(n: int) -> tuple:
    """Calculate math sub-score for a candidate number.
    Returns (score: float 0.0-1.0, breakdown: dict)."""
    profile = math_analysis.math_profile(n)
    breakdown = {}

    # Entropy: lower = more patterned = higher score
    max_entropy = 3.32
    ent = profile["entropy"]
    breakdown["entropy_low"] = max(0, 1.0 - ent / max_entropy)

    # Digit balance
    breakdown["digit_balance"] = profile["digit_balance"]

    # Prime
    breakdown["is_prime"] = 1.0 if profile.get("is_prime") else 0.0

    # Palindrome
    breakdown["palindrome"] = profile["palindrome_score"]

    # Repeating patterns
    patterns = profile["repeating_patterns"]
    breakdown["repeating"] = min(1.0, len(patterns) * 0.5) if patterns else 0.0

    # Mod60 cleanliness
    gcd = profile["modular"]["gcd_with_60"]
    breakdown["mod60_clean"] = gcd / 60.0

    # Power of 2
    breakdown["power_of_2"] = 1.0 if profile["is_power_of_2"] else 0.0

    # Weighted sum
    score = sum(MATH_FACTORS[k] * breakdown[k] for k in MATH_FACTORS)

    return score, breakdown


def numerology_score(n: int, context: dict = None) -> tuple:
    """Calculate numerology sub-score for a candidate number.
    Returns (score: float 0.0-1.0, breakdown: dict)."""
    context = context or {}
    breakdown = {}

    # Master number check
    breakdown["master_number"] = 1.0 if numerology.is_master_number(n) else 0.0

    # FC60 token analysis
    animal_idx = (n % 60) // 5
    element_idx = (n % 60) % 5

    # Animal repetition in base-60 encoding
    base60_digits = fc60.to_base60(n) if n > 0 else [0]
    animal_tokens = [fc60.ANIMALS[(d) // 5] for d in base60_digits]
    animal_counts = Counter(animal_tokens)
    max_repeat = max(animal_counts.values()) if animal_counts else 1
    total_digits = len(base60_digits)
    breakdown["animal_repetition"] = (
        (max_repeat / total_digits) if total_digits > 1 else 0.0
    )

    # Element balance
    element_tokens = [fc60.ELEMENTS[(d) % 5] for d in base60_digits]
    unique_elements = len(set(element_tokens))
    breakdown["element_balance"] = unique_elements / 5.0

    # Life path power
    reduced = numerology.numerology_reduce(numerology.digit_sum(n))
    power_numbers = {1, 8, 9, 11, 22, 33}
    breakdown["life_path_power"] = 1.0 if reduced in power_numbers else 0.3

    # Moon alignment
    if (
        "current_year" in context
        and "current_month" in context
        and "current_day" in context
    ):
        jdn = fc60.compute_jdn(
            context["current_year"], context["current_month"], context["current_day"]
        )
        phase_idx, age = fc60.moon_phase(jdn)
        peak_phases = {0: 0.9, 4: 1.0, 1: 0.6, 3: 0.6, 5: 0.7, 7: 0.5, 2: 0.5, 6: 0.4}
        breakdown["moon_alignment"] = peak_phases.get(phase_idx, 0.5)
    else:
        breakdown["moon_alignment"] = 0.5

    # Ganzhi year match
    if "current_year" in context:
        year_animal_idx = (context["current_year"] - 4) % 12
        breakdown["ganzhi_match"] = 1.0 if animal_idx == year_animal_idx else 0.2
    else:
        breakdown["ganzhi_match"] = 0.5

    # Sacred geometry
    fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584]
    golden = 1.6180339887
    is_fib = n in fib
    golden_proximity = (
        any(abs(n - round(f * golden)) <= 1 for f in fib if f < n) if n > 1 else False
    )
    breakdown["sacred_geometry"] = 1.0 if is_fib else (0.6 if golden_proximity else 0.0)

    # Weighted sum
    score = sum(NUMEROLOGY_FACTORS[k] * breakdown[k] for k in NUMEROLOGY_FACTORS)

    return score, breakdown


# In-memory AI score cache (LRU-style)
_ai_cache = {}  # key -> (score, timestamp)
_AI_CACHE_MAX = 500
_AI_CACHE_TTL = 600  # 10 minutes


def ai_score(
    n: int, math_breakdown: dict = None, num_breakdown: dict = None, context: str = ""
) -> float:
    """Ask Claude to rate a candidate 0.0-1.0. Returns 0.5 on failure."""
    from engines.ai_engine import is_available, ask_claude

    if not is_available():
        return 0.5

    # Check in-memory cache
    cache_key = n
    if cache_key in _ai_cache:
        cached_score, cached_time = _ai_cache[cache_key]
        if time.time() - cached_time < _AI_CACHE_TTL:
            return cached_score
        else:
            del _ai_cache[cache_key]

    # Build prompt
    parts = [f"Rate this number as a puzzle candidate: {n}"]
    if math_breakdown:
        top_math = sorted(math_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
        parts.append(
            "Math strengths: " + ", ".join(f"{k}={v:.2f}" for k, v in top_math)
        )
    if num_breakdown:
        top_num = sorted(num_breakdown.items(), key=lambda x: x[1], reverse=True)[:3]
        parts.append(
            "Numer strengths: " + ", ".join(f"{k}={v:.2f}" for k, v in top_num)
        )
    if context:
        parts.append(f"Context: {context}")
    parts.append(
        "Return ONLY a single decimal number between 0.0 and 1.0. "
        "Nothing else. No text."
    )

    result = ask_claude("\n".join(parts), timeout=10, use_cache=True)

    if result["success"]:
        try:
            score = float(result["response"].strip())
            score = max(0.0, min(1.0, score))
        except (ValueError, TypeError):
            score = 0.5
    else:
        score = 0.5

    # Store in cache, evict oldest if over limit
    _ai_cache[cache_key] = (score, time.time())
    if len(_ai_cache) > _AI_CACHE_MAX:
        oldest_key = min(_ai_cache, key=lambda k: _ai_cache[k][1])
        del _ai_cache[oldest_key]

    return score


def hybrid_score(
    n: int, context: dict = None, weights: dict = None, include_ai: bool = False
) -> dict:
    """
    THE MAIN SCORING FUNCTION.
    Combines math, numerology, and learned scores into one final score.
    When include_ai=True, also computes AI score (15% AI, 85% existing split).
    """
    # LAZY IMPORT — avoids circular dependency
    from engines import learning

    w = weights or learning.get_weights() or DEFAULT_WEIGHTS

    m_score, m_breakdown = math_score(n)
    n_score, n_breakdown = numerology_score(n, context)
    l_score = learning.get_learned_score(n, context)

    # Normalize learned weight
    actual_learned_weight = w.get("learned_weight", 0.30) * learning.confidence_level()
    remaining = 1.0 - actual_learned_weight

    # Safe division (Fix 3)
    math_w = w.get("math_weight", 0.40)
    num_w = w.get("numerology_weight", 0.30)
    denominator = math_w + num_w
    if denominator == 0:
        denominator = 1.0
        math_w = 0.5
        num_w = 0.5
    actual_math_weight = math_w * remaining / denominator
    actual_num_weight = num_w * remaining / denominator

    final = (
        actual_math_weight * m_score
        + actual_num_weight * n_score
        + actual_learned_weight * l_score
    )

    result = {
        "final_score": round(final, 4),
        "math_score": round(m_score, 4),
        "math_breakdown": m_breakdown,
        "numerology_score": round(n_score, 4),
        "numerology_breakdown": n_breakdown,
        "learned_score": round(l_score, 4),
        "weights_used": {
            "math": round(actual_math_weight, 3),
            "numerology": round(actual_num_weight, 3),
            "learned": round(actual_learned_weight, 3),
        },
        "fc60_token": fc60.token60(n % 60),
        "fc60_full": fc60.encode_base60(n) if n >= 0 else "NEG",
        "reduced_number": numerology.numerology_reduce(
            sum(int(d) for d in str(abs(n)))
        ),
        "is_master": numerology.is_master_number(n),
    }

    # AI scoring (opt-in)
    if include_ai:
        a_score = ai_score(n, m_breakdown, n_breakdown)
        # Re-weight: 15% AI, 85% existing
        result["ai_score"] = round(a_score, 4)
        result["final_score"] = round(final * 0.85 + a_score * 0.15, 4)

    return result


def score_batch(candidates: list, context: dict = None) -> list:
    """Score a list of candidates and return sorted by score (highest first)."""
    results = [(c, hybrid_score(c, context)) for c in candidates]
    results.sort(key=lambda x: x[1]["final_score"], reverse=True)
    return results
