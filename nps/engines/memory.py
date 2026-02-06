"""
In-memory cache engine with periodic disk flush.

Stores scan session history, high-score discoveries, and score
distribution data.  Everything lives in RAM for fast access and is
flushed to ``data/scan_memory.json`` periodically (every 60 s while
dirty) and on shutdown.

Zero pip dependencies -- Python stdlib only.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_FILE = DATA_DIR / "scan_memory.json"

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

_lock = threading.RLock()  # Reentrant lock for thread safety
_cache = None  # None until first load, then dict
_dirty = False  # True if cache has unsaved changes
_flush_timer = None  # threading.Timer for periodic flush

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MAX_SESSIONS = 1000
_MAX_HIGH_SCORES = 500
_MAX_SIZE_BYTES = 10_000_000  # ~10 MB
_FLUSH_INTERVAL = 60  # seconds
_AGGRESSIVE_SESSION_TRIM = 500

# ===================================================================
# Internal helpers
# ===================================================================


def _default_memory() -> dict:
    """Return the default empty memory structure."""
    return {
        "version": 2,
        "sessions": [],
        "high_scores": [],
        "score_distribution": {},
        "lifetime_stats": {
            "total_keys": 0,
            "total_seeds": 0,
            "total_hits": 0,
            "total_duration": 0,
        },
        "created": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "last_updated": "",
    }


def _ensure_loaded() -> None:
    """Load the cache from disk on first access (or create a default).

    The caller should already hold ``_lock`` or this function acquires it
    itself -- safe either way because the lock is reentrant.
    """
    global _cache

    with _lock:
        if _cache is not None:
            return

        if MEMORY_FILE.exists():
            try:
                raw = MEMORY_FILE.read_text(encoding="utf-8")
                _cache = json.loads(raw)
                log.info("Memory loaded from %s", MEMORY_FILE)
            except (json.JSONDecodeError, OSError) as exc:
                log.warning(
                    "Failed to load memory file (%s) -- starting fresh: %s",
                    MEMORY_FILE,
                    exc,
                )
                _cache = _default_memory()
        else:
            log.info("No memory file found -- creating default memory")
            _cache = _default_memory()

        # Ensure all expected keys exist (forward-compat with older files)
        defaults = _default_memory()
        for key, value in defaults.items():
            if key not in _cache:
                _cache[key] = value
        for key, value in defaults["lifetime_stats"].items():
            if key not in _cache.get("lifetime_stats", {}):
                _cache.setdefault("lifetime_stats", {})[key] = value


def _trim_memory() -> None:
    """Trim the cache to stay within size budgets.

    Must be called while holding ``_lock``.
    """
    global _cache

    # Sessions: hard cap
    if len(_cache.get("sessions", [])) > _MAX_SESSIONS:
        _cache["sessions"] = _cache["sessions"][-_MAX_SESSIONS:]

    # High scores: keep top N by score descending
    hs = _cache.get("high_scores", [])
    if len(hs) > _MAX_HIGH_SCORES:
        hs.sort(key=lambda h: h.get("score", 0), reverse=True)
        _cache["high_scores"] = hs[:_MAX_HIGH_SCORES]

    # Byte-size check -- aggressive trim if needed
    try:
        size = len(json.dumps(_cache))
    except (TypeError, ValueError):
        size = 0

    if size > _MAX_SIZE_BYTES:
        log.warning(
            "Memory cache size %d exceeds limit %d -- aggressive trim",
            size,
            _MAX_SIZE_BYTES,
        )
        _cache["sessions"] = _cache["sessions"][-_AGGRESSIVE_SESSION_TRIM:]
        hs = _cache.get("high_scores", [])
        hs.sort(key=lambda h: h.get("score", 0), reverse=True)
        _cache["high_scores"] = hs[:_AGGRESSIVE_SESSION_TRIM]


def _start_flush_timer() -> None:
    """Start a background timer to auto-flush in ``_FLUSH_INTERVAL`` seconds.

    No-op if a timer is already running.
    """
    global _flush_timer

    if _flush_timer is not None and _flush_timer.is_alive():
        return

    _flush_timer = threading.Timer(_FLUSH_INTERVAL, _auto_flush)
    _flush_timer.daemon = True
    _flush_timer.start()


def _auto_flush() -> None:
    """Timer callback: flush to disk, then reschedule if still dirty."""
    global _flush_timer

    _flush_timer = None
    flush_to_disk()

    with _lock:
        if _dirty:
            _start_flush_timer()


# ===================================================================
# Public API
# ===================================================================


def get_memory() -> dict:
    """Return the current memory cache (loads from disk on first call).

    The returned dict is the *live* cache -- callers should treat it as
    read-only unless they also set ``_dirty`` under ``_lock``.
    """
    with _lock:
        _ensure_loaded()
        return _cache


def record_session(session: dict) -> None:
    """Record a scan session.

    *session* should contain keys such as ``mode``, ``duration``,
    ``keys_tested``, ``seeds_tested``, ``hits``, ``avg_speed``.
    A ``timestamp`` is added automatically if missing.
    """
    global _dirty

    with _lock:
        _ensure_loaded()

        if "timestamp" not in session:
            session["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        _cache["sessions"].append(session)

        # Update lifetime stats
        stats = _cache["lifetime_stats"]
        stats["total_keys"] += session.get("keys_tested", 0)
        stats["total_seeds"] += session.get("seeds_tested", 0)
        stats["total_hits"] += session.get("hits", 0)
        stats["total_duration"] += session.get("duration", 0)

        _cache["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        _trim_memory()
        _dirty = True
        _start_flush_timer()


def record_high_score(key_hex: str, score: float, addresses: list) -> None:
    """Record a high-scoring key discovery."""
    global _dirty

    with _lock:
        _ensure_loaded()

        entry = {
            "key_hex": key_hex,
            "score": score,
            "addresses": addresses,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        }

        _cache["high_scores"].append(entry)

        # Keep sorted descending by score, trim to max
        _cache["high_scores"].sort(key=lambda h: h.get("score", 0), reverse=True)
        if len(_cache["high_scores"]) > _MAX_HIGH_SCORES:
            _cache["high_scores"] = _cache["high_scores"][:_MAX_HIGH_SCORES]

        _cache["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        _dirty = True
        _start_flush_timer()


def record_score_distribution(score: float) -> None:
    """Track *score* in the appropriate 0.1-wide bucket."""
    global _dirty

    with _lock:
        _ensure_loaded()

        # Clamp to [0.0, 1.0]
        clamped = max(0.0, min(1.0, score))

        # Determine bucket: "0.0-0.1", "0.1-0.2", ..., "0.9-1.0"
        bucket_idx = min(int(clamped * 10), 9)
        lo = round(bucket_idx * 0.1, 1)
        hi = round(lo + 0.1, 1)
        bucket_key = f"{lo}-{hi}"

        dist = _cache.setdefault("score_distribution", {})
        dist[bucket_key] = dist.get(bucket_key, 0) + 1

        _dirty = True


def get_recommendations() -> list:
    """Analyse memory and return a list of human-readable recommendations."""
    with _lock:
        _ensure_loaded()

        recs: list[str] = []
        sessions = _cache.get("sessions", [])
        stats = _cache.get("lifetime_stats", {})
        dist = _cache.get("score_distribution", {})
        high_scores = _cache.get("high_scores", [])

        total_sessions = len(sessions)
        total_keys = stats.get("total_keys", 0)
        total_seeds = stats.get("total_seeds", 0)
        total_hits = stats.get("total_hits", 0)

        # --- Session count summary ---
        if total_sessions > 0:
            recs.append(
                f"You've tested {total_keys:,} keys total across "
                f"{total_sessions} sessions."
            )

        # --- Speed trend ---
        if total_sessions >= 3:
            recent = sessions[-3:]
            older = sessions[:-3] if total_sessions > 3 else []
            recent_avg = sum(s.get("avg_speed", 0) for s in recent) / len(recent)
            if older:
                older_avg = sum(s.get("avg_speed", 0) for s in older) / len(older)
                if recent_avg > older_avg * 1.05:
                    recs.append("Your average speed is improving. Keep it up!")
                elif recent_avg < older_avg * 0.90:
                    recs.append(
                        "Your recent speed has dipped -- consider closing "
                        "other applications to free resources."
                    )

        # --- Hit rate ---
        if total_keys > 0 and total_hits == 0:
            recs.append(
                "No hits yet -- this is normal. Puzzle solving is a "
                "numbers game; keep scanning!"
            )
        elif total_keys > 0 and total_hits > 0:
            rate = total_hits / total_keys
            recs.append(f"Hit rate: {rate:.2e} -- every hit matters!")

        # --- Mode suggestion ---
        modes = [s.get("mode") for s in sessions if s.get("mode")]
        if modes and "both" not in modes:
            recs.append("Consider trying 'both' mode for better coverage.")

        # --- Score distribution insight ---
        if dist:
            best_bucket = max(dist, key=lambda k: dist[k])
            recs.append(
                f"High scores tend to cluster around {best_bucket} " f"-- focus there."
            )

        # --- Seeds ---
        if total_seeds > 0:
            recs.append(
                f"You've tested {total_seeds:,} seeds -- "
                "BIP-39 coverage adds diversity to your search."
            )

        # --- Top high score ---
        if high_scores:
            top = high_scores[0].get("score", 0)
            recs.append(f"Your top score so far is {top:.4f}.")

        if not recs:
            recs.append("Start a scan session to begin building memory insights!")

        return recs


def get_summary() -> dict:
    """Return summary statistics computed entirely from the in-RAM cache."""
    with _lock:
        _ensure_loaded()

        sessions = _cache.get("sessions", [])
        stats = _cache.get("lifetime_stats", {})
        high_scores = _cache.get("high_scores", [])
        dist = _cache.get("score_distribution", {})

        total_keys = stats.get("total_keys", 0)
        total_seeds = stats.get("total_seeds", 0)
        total_hits = stats.get("total_hits", 0)
        total_duration = stats.get("total_duration", 0)

        speeds = [s.get("avg_speed", 0) for s in sessions if s.get("avg_speed")]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        best_speed = max(speeds) if speeds else 0.0

        top_score = high_scores[0].get("score", 0) if high_scores else 0.0

        last_session_time = ""
        if sessions:
            last_session_time = sessions[-1].get("timestamp", "")

        return {
            "total_sessions": len(sessions),
            "total_keys": total_keys,
            "total_seeds": total_seeds,
            "total_hits": total_hits,
            "avg_speed": round(avg_speed, 2),
            "best_speed": round(best_speed, 2),
            "total_duration_hours": round(total_duration / 3600, 2),
            "high_score_count": len(high_scores),
            "top_score": top_score,
            "score_distribution": dict(dist),
            "last_session_time": last_session_time,
        }


def flush_to_disk() -> None:
    """Write the cache to disk atomically (temp-file + rename).

    Only writes if there are unsaved changes (``_dirty is True``).
    """
    global _dirty

    with _lock:
        if not _dirty or _cache is None:
            return

        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            _cache["last_updated"] = time.strftime(
                "%Y-%m-%d %H:%M:%S UTC", time.gmtime()
            )

            tmp_path = MEMORY_FILE.with_suffix(".tmp")
            data = json.dumps(_cache, indent=2, ensure_ascii=False)
            tmp_path.write_text(data, encoding="utf-8")
            os.replace(str(tmp_path), str(MEMORY_FILE))

            _dirty = False
            log.info("Memory flushed to %s (%d bytes)", MEMORY_FILE, len(data))
        except OSError as exc:
            log.error("Failed to flush memory to disk: %s", exc)


def shutdown() -> None:
    """Cancel any pending flush timer and do a final flush."""
    global _flush_timer

    with _lock:
        if _flush_timer is not None:
            _flush_timer.cancel()
            _flush_timer = None

        flush_to_disk()
        log.info("Memory engine shut down")
