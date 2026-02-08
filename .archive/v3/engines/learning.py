"""
Learning Engine
===============
Tracks solved puzzles and adjusts scoring weights based on
which factors actually correlate with correct answers.

Storage: JSON files in data/ directory.
No external dependencies.
"""

import json
import os
import math
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
HISTORY_FILE = DATA_DIR / "solve_history.json"
WEIGHTS_FILE = DATA_DIR / "factor_weights.json"
SCAN_SESSIONS_FILE = DATA_DIR / "scan_sessions.json"

# Minimum solves before learning kicks in
MIN_SOLVES_FOR_LEARNING = 10


def _ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def record_solve(
    puzzle_type: str,
    candidate: int,
    score_result: dict,
    was_correct: bool,
    metadata: dict = None,
):
    """Record a puzzle solve attempt (correct or incorrect)."""
    _ensure_data_dir()

    record = {
        "puzzle_type": puzzle_type,
        "candidate": candidate,
        "final_score": score_result["final_score"],
        "math_score": score_result["math_score"],
        "math_breakdown": score_result["math_breakdown"],
        "numerology_score": score_result["numerology_score"],
        "numerology_breakdown": score_result["numerology_breakdown"],
        "was_correct": was_correct,
        "fc60_token": score_result["fc60_token"],
        "reduced_number": score_result["reduced_number"],
        "is_master": score_result["is_master"],
        "metadata": metadata or {},
    }

    history = _load_history()
    history.append(record)

    # Keep last 10,000 records max
    if len(history) > 10000:
        history = history[-10000:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def _load_history() -> list:
    """Load solve history from disk."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_weights() -> dict:
    """Load current learned weights. Returns None if no learned weights yet."""
    if not WEIGHTS_FILE.exists():
        return None
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def confidence_level() -> float:
    """
    How confident is the learning engine? 0.0 = no data, 1.0 = very confident.
    0 solves -> 0.0, 10 solves -> 0.3, 50 -> 0.7, 100+ -> 1.0
    """
    history = _load_history()
    correct_count = sum(1 for r in history if r.get("was_correct"))
    if correct_count < MIN_SOLVES_FOR_LEARNING:
        return 0.0
    return min(1.0, correct_count / 100.0)


def get_learned_score(n: int, context: dict = None) -> float:
    """
    Score a candidate based on learned patterns.
    Returns 0.5 (neutral) if not enough data.
    """
    history = _load_history()
    winners = [r for r in history if r.get("was_correct")]

    if len(winners) < MIN_SOLVES_FOR_LEARNING:
        return 0.5

    # LAZY IMPORT — avoids circular dependency
    from engines.math_analysis import entropy, digit_balance
    from engines.numerology import is_master_number

    candidate_entropy = entropy(n)
    candidate_balance = digit_balance(n)

    winner_entropies = [
        r.get("math_breakdown", {}).get("entropy_low", 0.5) for r in winners
    ]
    winner_balances = [
        r.get("math_breakdown", {}).get("digit_balance", 0.5) for r in winners
    ]

    avg_winner_entropy = sum(winner_entropies) / len(winner_entropies)
    avg_winner_balance = sum(winner_balances) / len(winner_balances)

    # Normalize candidate values to 0-1 range
    max_entropy = 3.32
    norm_entropy = max(0, 1.0 - candidate_entropy / max_entropy)

    # Similarity: how close to the winner profile?
    entropy_sim = 1.0 - abs(norm_entropy - avg_winner_entropy)
    balance_sim = 1.0 - abs(candidate_balance - avg_winner_balance)

    # Check numerology factors from history
    winner_master_rate = sum(1 for r in winners if r.get("is_master", False)) / len(
        winners
    )
    candidate_is_master = is_master_number(n)
    master_boost = 0.2 if candidate_is_master and winner_master_rate > 0.15 else 0.0

    return max(
        0.0,
        min(1.0, (entropy_sim * 0.4 + balance_sim * 0.3 + 0.3 * 0.5 + master_boost)),
    )


def recalculate_weights():
    """Analyze solve history and recalculate optimal weights."""
    _ensure_data_dir()
    history = _load_history()

    winners = [r for r in history if r.get("was_correct")]
    losers = [r for r in history if not r.get("was_correct")]

    if len(winners) < MIN_SOLVES_FOR_LEARNING or len(losers) < MIN_SOLVES_FOR_LEARNING:
        return

    winner_math_avg = sum(r.get("math_score", 0.5) for r in winners) / len(winners)
    winner_num_avg = sum(r.get("numerology_score", 0.5) for r in winners) / len(winners)
    loser_math_avg = sum(r.get("math_score", 0.5) for r in losers) / len(losers)
    loser_num_avg = sum(r.get("numerology_score", 0.5) for r in losers) / len(losers)

    math_gap = max(0.01, winner_math_avg - loser_math_avg)
    num_gap = max(0.01, winner_num_avg - loser_num_avg)
    total_gap = math_gap + num_gap

    new_weights = {
        "math_weight": 0.70 * (math_gap / total_gap),
        "numerology_weight": 0.70 * (num_gap / total_gap),
        "learned_weight": 0.30,
    }

    total = sum(new_weights.values())
    new_weights = {k: v / total for k, v in new_weights.items()}

    with open(WEIGHTS_FILE, "w") as f:
        json.dump(new_weights, f, indent=2)


def get_factor_accuracy() -> dict:
    """For the Validation Dashboard. Returns factor accuracy analysis."""
    history = _load_history()
    winners = [r for r in history if r.get("was_correct")]
    losers = [r for r in history if not r.get("was_correct")]

    result = {
        "total_solves": len(history),
        "total_correct": len(winners),
        "factors": {},
    }

    if not winners or not losers:
        return result

    factor_checks = {
        "is_master_number": lambda r: r.get("is_master", False),
        "high_math_score": lambda r: r.get("math_score", 0) > 0.6,
        "high_numerology_score": lambda r: r.get("numerology_score", 0) > 0.6,
        "power_reduced_number": lambda r: r.get("reduced_number", 0)
        in (1, 8, 9, 11, 22, 33),
    }

    for name, check_fn in factor_checks.items():
        winner_rate = sum(1 for w in winners if check_fn(w)) / len(winners)
        loser_rate = sum(1 for l in losers if check_fn(l)) / len(losers)
        lift = (winner_rate / loser_rate - 1.0) if loser_rate > 0 else 0.0

        result["factors"][name] = {
            "winner_rate": round(winner_rate, 4),
            "loser_rate": round(loser_rate, 4),
            "lift": round(lift, 4),
        }

    return result


def get_solve_stats() -> dict:
    """Summary statistics for the dashboard."""
    history = _load_history()
    winners = [r for r in history if r.get("was_correct")]
    losers = [r for r in history if not r.get("was_correct")]

    return {
        "total_attempts": len(history),
        "total_correct": len(winners),
        "success_rate": len(winners) / max(1, len(history)),
        "avg_winner_score": sum(r.get("final_score", 0) for r in winners)
        / max(1, len(winners)),
        "avg_loser_score": sum(r.get("final_score", 0) for r in losers)
        / max(1, len(losers)),
        "best_puzzle_type": _most_common_type(winners),
        "confidence": confidence_level(),
    }


def _most_common_type(records: list) -> str:
    """Find the most common puzzle_type in records."""
    if not records:
        return "none"
    from collections import Counter

    types = Counter(r.get("puzzle_type", "unknown") for r in records)
    return types.most_common(1)[0][0]


def pearson_correlation() -> float:
    """
    Calculate Pearson correlation between final_score and was_correct.
    Returns float from -1.0 to 1.0. Returns 0.0 if not enough data.
    """
    history = _load_history()
    if len(history) < MIN_SOLVES_FOR_LEARNING:
        return 0.0

    scores = [r.get("final_score", 0.5) for r in history]
    correct = [1.0 if r.get("was_correct") else 0.0 for r in history]

    n = len(scores)
    mean_s = sum(scores) / n
    mean_c = sum(correct) / n

    numerator = sum((scores[i] - mean_s) * (correct[i] - mean_c) for i in range(n))
    denom_s = math.sqrt(sum((scores[i] - mean_s) ** 2 for i in range(n)))
    denom_c = math.sqrt(sum((correct[i] - mean_c) ** 2 for i in range(n)))

    if denom_s == 0 or denom_c == 0:
        return 0.0

    return numerator / (denom_s * denom_c)


def export_history_csv(filepath: str = None) -> str:
    """Export solve history to CSV file. Returns the filepath written to."""
    import csv

    if filepath is None:
        filepath = str(DATA_DIR / "solve_history.csv")

    history = _load_history()
    if not history:
        return filepath

    fieldnames = [
        "puzzle_type",
        "candidate",
        "final_score",
        "math_score",
        "numerology_score",
        "was_correct",
        "fc60_token",
        "reduced_number",
        "is_master",
    ]

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(history)

    return filepath


def _load_scan_sessions() -> list:
    """Load scan session history from disk."""
    if not SCAN_SESSIONS_FILE.exists():
        return []
    try:
        with open(SCAN_SESSIONS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def record_scan_session(session_stats: dict):
    """Record a completed scan session. Capped at 1000 records."""
    _ensure_data_dir()
    import time

    record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "duration": session_stats.get("duration", 0),
        "mode": session_stats.get("mode", "unknown"),
        "keys_tested": session_stats.get("keys_tested", 0),
        "seeds_tested": session_stats.get("seeds_tested", 0),
        "hits": session_stats.get("hits", 0),
        "avg_speed": session_stats.get("avg_speed", 0),
        "online_checks": session_stats.get("online_checks", 0),
    }

    sessions = _load_scan_sessions()
    sessions.append(record)

    if len(sessions) > 1000:
        sessions = sessions[-1000:]

    try:
        with open(SCAN_SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
    except OSError as e:
        logger.error(f"Failed to write scan session: {e}")


def get_scan_insights() -> dict:
    """Analyze all scan sessions and return totals, averages, and recommendations."""
    import time

    sessions = _load_scan_sessions()
    if not sessions:
        return {
            "total_sessions": 0,
            "total_keys": 0,
            "total_seeds": 0,
            "total_hits": 0,
            "total_duration_hours": 0,
            "avg_speed": 0,
            "mode_distribution": {},
            "today_keys": 0,
            "today_seeds": 0,
            "recommendation": "No scan data yet. Start scanning to build insights.",
        }

    total_keys = sum(s.get("keys_tested", 0) for s in sessions)
    total_seeds = sum(s.get("seeds_tested", 0) for s in sessions)
    total_hits = sum(s.get("hits", 0) for s in sessions)
    total_duration = sum(s.get("duration", 0) for s in sessions)
    speeds = [s.get("avg_speed", 0) for s in sessions if s.get("avg_speed", 0) > 0]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0

    # Mode distribution
    from collections import Counter

    mode_counts = Counter(s.get("mode", "unknown") for s in sessions)
    mode_distribution = dict(mode_counts)

    # Today's stats
    today_str = time.strftime("%Y-%m-%d", time.gmtime())
    today_sessions = [
        s for s in sessions if s.get("timestamp", "").startswith(today_str)
    ]
    today_keys = sum(s.get("keys_tested", 0) for s in today_sessions)
    today_seeds = sum(s.get("seeds_tested", 0) for s in today_sessions)

    # Simple recommendation
    best_mode = mode_counts.most_common(1)[0][0] if mode_counts else "both"
    if total_hits > 0:
        recommendation = (
            f"You've found {total_hits} hits! Most sessions use '{best_mode}' mode."
        )
    elif total_keys > 1_000_000:
        recommendation = f"Over {total_keys:,} keys tested. Consider enabling scoring for high-value candidates."
    else:
        recommendation = (
            f"Keep scanning! '{best_mode}' mode is your most-used strategy."
        )

    return {
        "total_sessions": len(sessions),
        "total_keys": total_keys,
        "total_seeds": total_seeds,
        "total_hits": total_hits,
        "total_duration_hours": round(total_duration / 3600, 2),
        "avg_speed": round(avg_speed, 1),
        "mode_distribution": mode_distribution,
        "today_keys": today_keys,
        "today_seeds": today_seeds,
        "recommendation": recommendation,
    }


def record_scan_to_memory(session_stats: dict):
    """Record scan session to both learning engine AND memory engine.

    Calls record_scan_session() for backward compatibility,
    then also calls engines.memory.record_session() for the new memory system.
    """
    record_scan_session(session_stats)
    try:
        from engines.memory import record_session

        record_session(session_stats)
    except Exception as e:
        logger.debug("Memory engine unavailable, skipping: %s", e)


def reset_learning_data():
    """Delete all learning data."""
    _ensure_data_dir()
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    if WEIGHTS_FILE.exists():
        WEIGHTS_FILE.unlink()
    if SCAN_SESSIONS_FILE.exists():
        SCAN_SESSIONS_FILE.unlink()
    logger.info("Learning data reset by user")
