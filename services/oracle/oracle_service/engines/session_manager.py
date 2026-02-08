"""
Session Manager for NPS.

Tracks scan sessions with start/end times, stats, and provides
aggregate session statistics.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_lock = threading.Lock()

SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"


def start_session(terminal_id, settings=None):
    """Start a new session. Returns session_id."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    session_id = f"{terminal_id}_{ts}"

    session = {
        "session_id": session_id,
        "terminal_id": terminal_id,
        "started": time.time(),
        "ended": None,
        "settings": settings or {},
        "stats": {},
    }

    path = SESSIONS_DIR / f"{session_id}.json"
    with _lock:
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(session, f, indent=2)
        os.replace(str(tmp_path), str(path))

    logger.info(f"Session started: {session_id}")
    return session_id


def end_session(session_id, stats=None):
    """End a session and record final stats."""
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        logger.warning(f"Session not found: {session_id}")
        return

    with _lock:
        with open(path) as f:
            session = json.load(f)

        session["ended"] = time.time()
        session["duration"] = session["ended"] - session["started"]
        session["stats"] = stats or {}

        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(session, f, indent=2)
        os.replace(str(tmp_path), str(path))

    logger.info(f"Session ended: {session_id} ({session['duration']:.1f}s)")


def get_session(session_id):
    """Get a session by ID. Returns dict or None."""
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def list_sessions(limit=50):
    """List recent sessions, newest first."""
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        if len(sessions) >= limit:
            break
        try:
            with open(path) as f:
                session = json.load(f)
            sessions.append(
                {
                    "session_id": session.get("session_id", path.stem),
                    "terminal_id": session.get("terminal_id", ""),
                    "started": session.get("started", 0),
                    "ended": session.get("ended"),
                    "duration": session.get("duration", 0),
                    "stats": session.get("stats", {}),
                }
            )
        except (json.JSONDecodeError, IOError):
            continue

    return sessions


def get_session_stats():
    """Aggregate stats across all sessions."""
    if not SESSIONS_DIR.exists():
        return {
            "total_sessions": 0,
            "total_duration": 0,
            "total_keys": 0,
            "total_seeds": 0,
            "total_hits": 0,
        }

    total_sessions = 0
    total_duration = 0
    total_keys = 0
    total_seeds = 0
    total_hits = 0

    for path in SESSIONS_DIR.glob("*.json"):
        try:
            with open(path) as f:
                session = json.load(f)
            total_sessions += 1
            total_duration += session.get("duration", 0)
            stats = session.get("stats", {})
            total_keys += stats.get("keys_tested", 0)
            total_seeds += stats.get("seeds_tested", 0)
            total_hits += stats.get("hits", 0)
        except (json.JSONDecodeError, IOError):
            continue

    return {
        "total_sessions": total_sessions,
        "total_duration": total_duration,
        "total_keys": total_keys,
        "total_seeds": total_seeds,
        "total_hits": total_hits,
    }
