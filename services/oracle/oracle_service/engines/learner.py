"""
Active AI Learning System for NPS.

Tracks XP and levels, stores insights from AI analysis,
provides auto-adjustment recommendations at higher levels.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "learning"
STATE_FILE = DATA_DIR / "learning_state.json"
_lock = threading.Lock()

LEVELS = {
    1: {"name": "Novice", "xp": 0, "capabilities": ["Basic scanning"]},
    2: {
        "name": "Student",
        "xp": 100,
        "capabilities": ["Basic scanning", "Pattern recognition"],
    },
    3: {
        "name": "Apprentice",
        "xp": 500,
        "capabilities": [
            "Basic scanning",
            "Pattern recognition",
            "Strategy suggestions",
        ],
    },
    4: {
        "name": "Expert",
        "xp": 2000,
        "capabilities": [
            "Basic scanning",
            "Pattern recognition",
            "Strategy suggestions",
            "Auto-adjust parameters",
        ],
    },
    5: {
        "name": "Master",
        "xp": 10000,
        "capabilities": [
            "Basic scanning",
            "Pattern recognition",
            "Strategy suggestions",
            "Auto-adjust parameters",
            "Predictive analysis",
        ],
    },
}

# Module state
_state = None


def _default_state():
    """Return default learning state."""
    return {
        "xp": 0,
        "level": 1,
        "insights": [],
        "recommendations": [],
        "auto_adjustments": None,
        "total_learn_calls": 0,
        "total_keys_scanned": 0,
        "total_hits": 0,
        "model": "sonnet",
        "last_learn": None,
    }


def load_state():
    """Load learning state from disk."""
    global _state
    with _lock:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    _state = json.load(f)
            except (json.JSONDecodeError, IOError):
                _state = _default_state()
        else:
            _state = _default_state()
    return _state


def save_state():
    """Save learning state to disk. Atomic write."""
    global _state
    if _state is None:
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        tmp_path = STATE_FILE.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(_state, f, indent=2)
        os.replace(str(tmp_path), str(STATE_FILE))
    except IOError as e:
        logger.error(f"Failed to save learning state: {e}")


def _ensure_state():
    """Ensure state is loaded."""
    global _state
    if _state is None:
        load_state()


def get_level():
    """Get current level info.

    Returns:
        dict with: level, name, xp, xp_next, capabilities
    """
    _ensure_state()
    current_level = _state["level"]
    level_info = LEVELS.get(current_level, LEVELS[1])

    # Find XP needed for next level
    next_level = current_level + 1
    xp_next = LEVELS.get(next_level, {}).get("xp", None)

    return {
        "level": current_level,
        "name": level_info["name"],
        "xp": _state["xp"],
        "xp_next": xp_next,
        "capabilities": level_info["capabilities"],
    }


def add_xp(amount, reason=""):
    """Add XP and auto-level up if threshold reached.

    Args:
        amount: XP to add
        reason: Description of why XP was earned
    """
    _ensure_state()
    with _lock:
        _state["xp"] += amount

        # Check for level up
        leveled_up = False
        new_level_info = None
        for level_num in sorted(LEVELS.keys(), reverse=True):
            if _state["xp"] >= LEVELS[level_num]["xp"]:
                if level_num > _state["level"]:
                    old_level = _state["level"]
                    _state["level"] = level_num
                    leveled_up = True
                    new_level_info = {
                        "old_level": old_level,
                        "new_level": level_num,
                        "name": LEVELS[level_num]["name"],
                        "xp": _state["xp"],
                    }
                    logger.info(
                        f"Level up! {old_level} -> {level_num} ({LEVELS[level_num]['name']})"
                    )
                break

    save_state()

    if leveled_up and new_level_info:
        try:
            from engines.events import emit, LEVEL_UP

            emit(LEVEL_UP, new_level_info)
        except Exception:
            pass


def learn(session_data, model="sonnet"):
    """Trigger AI analysis of session data.

    Uses Claude CLI if available, returns insights and recommendations.
    Graceful degradation if CLI is unavailable.

    Args:
        session_data: dict with session stats
        model: model to use for analysis

    Returns:
        dict with: insights, recommendations, adjustments
    """
    _ensure_state()
    with _lock:
        _state["total_learn_calls"] += 1
        _state["last_learn"] = time.time()
        _state["model"] = model

    result = {
        "insights": [],
        "recommendations": [],
        "adjustments": None,
    }

    try:
        from engines.ai_engine import is_available, ask_claude

        if not is_available():
            result["insights"] = [
                "AI CLI not available — install Claude CLI for AI-powered learning"
            ]
            save_state()
            return result

        prompt = (
            f"Analyze this NPS scanning session and provide insights:\n"
            f"Keys tested: {session_data.get('keys_tested', 0):,}\n"
            f"Seeds tested: {session_data.get('seeds_tested', 0):,}\n"
            f"Hits: {session_data.get('hits', 0)}\n"
            f"Speed: {session_data.get('speed', 0):.0f}/s\n"
            f"Duration: {session_data.get('elapsed', 0):.0f}s\n"
            f"Mode: {session_data.get('mode', 'unknown')}\n\n"
            f"Provide 2-3 short insights and 1-2 recommendations."
        )

        ai_result = ask_claude(prompt, model=model)
        if ai_result.get("success"):
            text = ai_result.get("response", "")
            # Parse into insights and recommendations
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for line in lines:
                if line.startswith("-") or line.startswith("*"):
                    line = line.lstrip("-* ")
                if (
                    "recommend" in line.lower()
                    or "suggest" in line.lower()
                    or "try" in line.lower()
                ):
                    result["recommendations"].append(line)
                else:
                    result["insights"].append(line)

            # Store insights
            with _lock:
                _state["insights"] = (result["insights"] + _state.get("insights", []))[
                    :50
                ]
                _state["recommendations"] = result["recommendations"]
        else:
            result["insights"] = ["AI analysis unavailable"]

    except ImportError:
        result["insights"] = ["AI engine not available"]
    except Exception as e:
        result["insights"] = [f"Analysis failed: {str(e)}"]

    save_state()
    return result


def get_auto_adjustments():
    """Get auto-adjustment recommendations (Level 4+ only).

    Returns:
        dict with parameter adjustments, or None if below Level 4.
    """
    _ensure_state()
    if _state["level"] < 4:
        return None

    # Basic auto-adjustments based on stats
    adjustments = {}
    total_keys = _state.get("total_keys_scanned", 0)
    total_hits = _state.get("total_hits", 0)

    # If scanning many keys with no hits, suggest larger batches
    if total_keys > 1_000_000 and total_hits == 0:
        adjustments["batch_size"] = 2000
        adjustments["check_every_n"] = 10000

    # Use stored AI recommendations if available
    if _state.get("auto_adjustments"):
        adjustments.update(_state["auto_adjustments"])

    return adjustments if adjustments else None


def get_insights(limit=10):
    """Get stored insights.

    Returns:
        list of insight strings
    """
    _ensure_state()
    return _state.get("insights", [])[:limit]


def get_recommendations():
    """Get current recommendations.

    Returns:
        list of recommendation strings
    """
    _ensure_state()
    return _state.get("recommendations", [])
