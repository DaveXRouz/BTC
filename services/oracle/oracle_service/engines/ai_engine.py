"""
AI Engine — Claude CLI integration for NPS.
============================================
Uses Claude Code CLI (claude --print -p "prompt") for AI-powered analysis.
Requires Claude Code Max subscription — no API key needed.

Graceful degradation: if CLI is unavailable, all functions return safe defaults.
"""

import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Claude CLI path
CLAUDE_CLI = "/opt/homebrew/bin/claude"

# Cache config
CACHE_DIR = Path(__file__).parent.parent / "data" / "ai_cache"
CACHE_TTL = 3600  # 1 hour
CACHE_MAX = 200

# Rate limiting
_rate_lock = threading.Lock()
_last_call_time = 0.0
_MIN_INTERVAL = 2.0  # seconds between calls

# Availability cache
_available = None

# Last successful insight for silent fallback
_last_insight = ""

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
    """Check if Claude CLI is installed and accessible. Result is cached."""
    global _available
    if _available is not None:
        return _available
    _available = os.path.isfile(CLAUDE_CLI) and os.access(CLAUDE_CLI, os.X_OK)
    if _available:
        logger.info("AI engine: Claude CLI found at %s", CLAUDE_CLI)
    else:
        logger.info("AI engine: Claude CLI not found, AI features disabled")
    return _available


def _cache_key(prompt: str, system_prompt: str = "") -> str:
    """Generate SHA-256 cache key from prompt + system prompt."""
    content = f"{system_prompt}|||{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


def _read_cache(key: str) -> dict | None:
    """Read cached response if it exists and hasn't expired."""
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
        if time.time() - data.get("timestamp", 0) > CACHE_TTL:
            cache_file.unlink(missing_ok=True)
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(key: str, response: str):
    """Write response to file cache, evicting oldest if over limit."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    try:
        data = {"response": response, "timestamp": time.time()}
        cache_file.write_text(json.dumps(data))
        _evict_cache()
    except OSError:
        pass


def _evict_cache():
    """Remove oldest cache files if over CACHE_MAX."""
    try:
        files = sorted(CACHE_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
        while len(files) > CACHE_MAX:
            files[0].unlink(missing_ok=True)
            files.pop(0)
    except OSError:
        pass


def ask_claude(
    prompt: str,
    system_prompt: str = "",
    json_output: bool = False,
    timeout: int = 30,
    use_cache: bool = True,
) -> dict:
    """
    Ask Claude via CLI and return result dict.

    Returns:
        {
            "success": bool,
            "response": str,
            "error": str or None,
            "elapsed": float,
            "cached": bool,
        }
    """
    global _last_call_time

    if not is_available():
        return {
            "success": False,
            "response": "",
            "error": "Claude CLI not available",
            "elapsed": 0.0,
            "cached": False,
        }

    sys_prompt = system_prompt or NPS_SYSTEM_PROMPT
    key = _cache_key(prompt, sys_prompt)

    # Check cache
    if use_cache:
        cached = _read_cache(key)
        if cached:
            return {
                "success": True,
                "response": cached["response"],
                "error": None,
                "elapsed": 0.0,
                "cached": True,
            }

    # Rate limiting
    with _rate_lock:
        now = time.time()
        wait = _MIN_INTERVAL - (now - _last_call_time)
        if wait > 0:
            time.sleep(wait)
        _last_call_time = time.time()

    # Build command
    cmd = [CLAUDE_CLI, "--print", "-p", prompt, "--system-prompt", sys_prompt]
    if json_output:
        cmd.extend(["--output-format", "json"])

    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            response = result.stdout.strip()
            if use_cache:
                _write_cache(key, response)
            return {
                "success": True,
                "response": response,
                "error": None,
                "elapsed": elapsed,
                "cached": False,
            }
        else:
            return {
                "success": False,
                "response": "",
                "error": result.stderr.strip() or f"Exit code {result.returncode}",
                "elapsed": elapsed,
                "cached": False,
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "response": "",
            "error": f"Timeout after {timeout}s",
            "elapsed": time.time() - start,
            "cached": False,
        }
    except Exception as e:
        return {
            "success": False,
            "response": "",
            "error": str(e),
            "elapsed": time.time() - start,
            "cached": False,
        }


def ask_claude_async(
    prompt: str,
    callback,
    system_prompt: str = "",
    json_output: bool = False,
    timeout: int = 30,
    use_cache: bool = True,
):
    """
    Ask Claude asynchronously. Calls callback(result_dict) from a daemon thread.
    The callback should be thread-safe (e.g., put result in a queue).
    """

    def _worker():
        result = ask_claude(
            prompt,
            system_prompt=system_prompt,
            json_output=json_output,
            timeout=timeout,
            use_cache=use_cache,
        )
        callback(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def get_ai_insight_async(prompt, callback, timeout=5):
    """Non-blocking AI insight with silent fallback.

    Unlike ask_claude_async, this:
    - Has a shorter default timeout (5s)
    - On failure/timeout, calls callback with the last successful insight
    - Never shows "Timeout" to the user

    Parameters
    ----------
    prompt : str
    callback : callable
        Called with result dict from background thread.
    timeout : int
        Max seconds to wait for Claude response.
    """
    global _last_insight

    def _worker():
        global _last_insight
        result = ask_claude(prompt, timeout=timeout)
        if result.get("success"):
            _last_insight = result["response"]
            callback(result)
        else:
            # Silent fallback — never expose "Timeout" to user
            if _last_insight:
                callback(
                    {
                        "success": True,
                        "response": _last_insight,
                        "error": None,
                        "elapsed": 0,
                        "cached": True,
                        "fallback": True,
                    }
                )
            else:
                callback(
                    {
                        "success": True,
                        "response": "\u2014",
                        "error": None,
                        "elapsed": 0,
                        "cached": False,
                        "fallback": True,
                    }
                )

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def analyze_scan_pattern(
    tested_count, speed, hits, recent_addresses, scan_mode, memory_summary=None
):
    """Ask Claude for tactical scanning advice based on current scan status.

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

    result = ask_claude(prompt, timeout=15)
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


def numerology_insight_for_key(private_key, addresses):
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

    # Lazy import to avoid circular deps
    from engines.scoring import hybrid_score

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

    result = ask_claude(prompt, timeout=15)
    if not result.get("success"):
        return {**defaults, "fc60_token": token, "score": score}

    # Extract highlights from breakdown
    math_highlights = [
        k for k, v in math_bd.items() if isinstance(v, (int, float)) and v > 0.7
    ]
    numer_highlights = [
        k for k, v in numer_bd.items() if isinstance(v, (int, float)) and v > 0.7
    ]

    return {
        "fc60_token": token,
        "score": score,
        "analysis": result["response"],
        "math_highlights": math_highlights,
        "numerology_highlights": numer_highlights,
    }


def brain_strategy_recommendation(history_summary: str) -> dict:
    """Ask Claude which scanning strategy to try next.

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

    result = ask_claude(prompt, timeout=15)
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
    """Ask Claude if the scanning strategy should adjust mid-session.

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

    result = ask_claude(prompt, timeout=10)
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
    """Ask Claude for lessons learned from a scanning session.

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

    result = ask_claude(prompt, timeout=15)
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


def clear_cache():
    """Purge all cached AI responses."""
    try:
        if CACHE_DIR.exists():
            for f in CACHE_DIR.glob("*.json"):
                f.unlink(missing_ok=True)
            logger.info("AI cache cleared")
    except OSError:
        pass
