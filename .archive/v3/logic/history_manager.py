"""
History Manager -- Data Persistence for the Logic Layer
========================================================
Manages data/logic/history.json, coverage.json, and pattern_stats.json.
Throttled writes (max 1 per 60s), atomic via .tmp + os.replace,
thread-safe with threading.Lock.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "logic"

_THROTTLE_INTERVAL = 60  # seconds between disk writes
_MAX_HISTORY_ENTRIES = 10000


class HistoryManager:
    """Persistent storage for logic layer history, coverage, and stats."""

    def __init__(self, data_dir=None):
        self._data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._lock = threading.Lock()

        # In-memory state
        self._history = {"entries": [], "daily_summaries": {}}
        self._coverage = {}
        self._stats = {}

        # Throttle tracking
        self._last_history_save = 0.0
        self._last_coverage_save = 0.0
        self._last_stats_save = 0.0

        # Dirty flags
        self._history_dirty = False
        self._coverage_dirty = False
        self._stats_dirty = False

    # ---- File paths ----

    @property
    def _history_path(self):
        return self._data_dir / "history.json"

    @property
    def _coverage_path(self):
        return self._data_dir / "coverage.json"

    @property
    def _stats_path(self):
        return self._data_dir / "pattern_stats.json"

    # ---- Load / Ensure ----

    def _ensure_dir(self):
        """Create data directory if it does not exist."""
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def load_all(self):
        """Load history, coverage, and stats from disk."""
        self._ensure_dir()
        with self._lock:
            self._history = self._load_json(
                self._history_path,
                {"entries": [], "daily_summaries": {}},
            )
            # Ensure expected keys exist
            if "entries" not in self._history:
                self._history["entries"] = []
            if "daily_summaries" not in self._history:
                self._history["daily_summaries"] = {}

            self._coverage = self._load_json(self._coverage_path, {})
            self._stats = self._load_json(self._stats_path, {})

    def _load_json(self, path, default):
        """Load a JSON file, returning *default* on any error."""
        if not path.exists():
            return default
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError) as exc:
            logger.debug("Failed to load %s: %s", path, exc)
            return default

    # ---- Atomic write helper ----

    def _atomic_write(self, path, data):
        """Write JSON atomically via .tmp + os.replace."""
        self._ensure_dir()
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(str(tmp_path), str(path))
        except (IOError, OSError) as exc:
            logger.error("Atomic write failed for %s: %s", path, exc)

    # ---- Save methods (throttled) ----

    def save_history(self, force=False):
        """Save history to disk if throttle interval has elapsed or force=True."""
        now = time.time()
        with self._lock:
            if not force and (now - self._last_history_save < _THROTTLE_INTERVAL):
                self._history_dirty = True
                return
            self._atomic_write(self._history_path, self._history)
            self._last_history_save = now
            self._history_dirty = False

    def save_coverage(self, force=False):
        """Save coverage to disk if throttle interval has elapsed or force=True."""
        now = time.time()
        with self._lock:
            if not force and (now - self._last_coverage_save < _THROTTLE_INTERVAL):
                self._coverage_dirty = True
                return
            self._atomic_write(self._coverage_path, self._coverage)
            self._last_coverage_save = now
            self._coverage_dirty = False

    def save_stats(self, force=False):
        """Save pattern_stats to disk if throttle interval has elapsed or force=True."""
        now = time.time()
        with self._lock:
            if not force and (now - self._last_stats_save < _THROTTLE_INTERVAL):
                self._stats_dirty = True
                return
            self._atomic_write(self._stats_path, self._stats)
            self._last_stats_save = now
            self._stats_dirty = False

    def flush(self):
        """Force-write all dirty data to disk immediately."""
        if self._history_dirty or True:
            self.save_history(force=True)
        if self._coverage_dirty or True:
            self.save_coverage(force=True)
        if self._stats_dirty or True:
            self.save_stats(force=True)

    # ---- History API ----

    def record_entry(self, entry):
        """Append an entry to history and auto-save if throttle allows.

        Args:
            entry: dict with session/scan summary data.
        """
        with self._lock:
            self._history["entries"].append(entry)
        self.save_history()

    def get_history(self, limit=100):
        """Return the most recent *limit* history entries."""
        with self._lock:
            entries = self._history.get("entries", [])
            return list(entries[-limit:])

    def get_daily_summary(self, date_str):
        """Return aggregate stats for a given date (YYYY-MM-DD).

        If a pre-computed summary exists, return it. Otherwise aggregate
        from entries that match the date prefix.
        """
        with self._lock:
            # Check pre-computed
            summaries = self._history.get("daily_summaries", {})
            if date_str in summaries:
                return summaries[date_str]

            # Aggregate from entries
            matching = [
                e
                for e in self._history.get("entries", [])
                if str(e.get("date", e.get("timestamp", ""))).startswith(date_str)
            ]
            if not matching:
                return None

            total_keys = sum(e.get("keys_tested", 0) for e in matching)
            total_hits = sum(e.get("hits", 0) for e in matching)
            scores = [e.get("avg_score", 0) for e in matching if e.get("avg_score")]
            avg_score = sum(scores) / len(scores) if scores else 0.0

            return {
                "date": date_str,
                "sessions": len(matching),
                "total_keys": total_keys,
                "total_hits": total_hits,
                "avg_score": round(avg_score, 4),
            }

    # ---- Coverage API ----

    def set_coverage(self, coverage_data):
        """Replace coverage data (used by PatternTracker)."""
        with self._lock:
            self._coverage = coverage_data
        self.save_coverage()

    def get_coverage_data(self):
        """Return the raw coverage dict."""
        with self._lock:
            return dict(self._coverage)

    # ---- Stats API ----

    def set_stats(self, stats_data):
        """Replace pattern stats data."""
        with self._lock:
            self._stats = stats_data
        self.save_stats()

    def get_stats_data(self):
        """Return the raw stats dict."""
        with self._lock:
            return dict(self._stats)

    # ---- Compact ----

    def compact(self):
        """Trim history to _MAX_HISTORY_ENTRIES, rolling old into daily summaries."""
        with self._lock:
            entries = self._history.get("entries", [])
            if len(entries) <= _MAX_HISTORY_ENTRIES:
                return

            # Entries to roll up
            overflow = entries[:-_MAX_HISTORY_ENTRIES]
            self._history["entries"] = entries[-_MAX_HISTORY_ENTRIES:]

            # Group overflow by date and create daily summaries
            daily = {}
            for e in overflow:
                date_key = str(e.get("date", e.get("timestamp", "unknown")))[:10]
                if date_key not in daily:
                    daily[date_key] = {
                        "keys": 0,
                        "hits": 0,
                        "sessions": 0,
                        "scores": [],
                    }
                daily[date_key]["keys"] += e.get("keys_tested", 0)
                daily[date_key]["hits"] += e.get("hits", 0)
                daily[date_key]["sessions"] += 1
                if e.get("avg_score"):
                    daily[date_key]["scores"].append(e["avg_score"])

            summaries = self._history.setdefault("daily_summaries", {})
            for date_key, agg in daily.items():
                scores = agg.pop("scores", [])
                agg["avg_score"] = (
                    round(sum(scores) / len(scores), 4) if scores else 0.0
                )
                agg["date"] = date_key
                # Merge with existing summary if present
                if date_key in summaries:
                    existing = summaries[date_key]
                    agg["keys"] += existing.get("keys", existing.get("total_keys", 0))
                    agg["hits"] += existing.get("hits", existing.get("total_hits", 0))
                    agg["sessions"] += existing.get("sessions", 0)
                summaries[date_key] = agg

        self.save_history(force=True)
