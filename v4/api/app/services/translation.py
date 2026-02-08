"""Translation service wrapper — API-level cache over T3-S3 translation engine."""

import hashlib
import logging
import sys
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Engine imports via sys.path shim ────────────────────────────────────────

_ORACLE_PARENT_DIR = str(Path(__file__).resolve().parents[3] / "services" / "oracle")
_ORACLE_SERVICE_DIR = str(
    Path(__file__).resolve().parents[3] / "services" / "oracle" / "oracle_service"
)
if _ORACLE_PARENT_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_PARENT_DIR)
if _ORACLE_SERVICE_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_SERVICE_DIR)

from engines.translation_service import (  # noqa: E402
    detect_language as _detect,
    translate as _translate,
)

# ─── Module-level cache ─────────────────────────────────────────────────────

_MAX_CACHE_ENTRIES = 1000
_CACHE_TTL_SECONDS = 86400  # 24 hours

_cache: dict[str, dict[str, Any]] = {}
_cache_hits = 0
_cache_misses = 0


def _cache_key(text: str, source_lang: str, target_lang: str) -> str:
    raw = f"{source_lang}:{target_lang}:{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _evict_expired() -> None:
    """Remove expired entries."""
    now = time.monotonic()
    expired = [k for k, v in _cache.items() if now - v["ts"] > _CACHE_TTL_SECONDS]
    for k in expired:
        del _cache[k]


def _evict_lru() -> None:
    """Evict oldest entries if over capacity."""
    while len(_cache) >= _MAX_CACHE_ENTRIES:
        oldest_key = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest_key]


def reset_cache() -> None:
    """Clear all cached translations and reset counters."""
    global _cache_hits, _cache_misses
    _cache.clear()
    _cache_hits = 0
    _cache_misses = 0


# ─── Translation Service ────────────────────────────────────────────────────


class TranslationService:
    """Wraps T3-S3 translation with API-level LRU caching."""

    def translate(
        self, text: str, source_lang: str = "en", target_lang: str = "fa"
    ) -> dict:
        """Translate text between English and Persian.

        Returns dict with keys: source_text, translated_text, source_lang,
        target_lang, preserved_terms, ai_generated, elapsed_ms, cached.
        """
        global _cache_hits, _cache_misses

        # Same-language short-circuit
        if source_lang == target_lang:
            return {
                "source_text": text,
                "translated_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "preserved_terms": [],
                "ai_generated": False,
                "elapsed_ms": 0.0,
                "cached": False,
            }

        key = _cache_key(text, source_lang, target_lang)

        # Check cache
        _evict_expired()
        if key in _cache:
            _cache_hits += 1
            entry = _cache[key]
            entry["ts"] = time.monotonic()  # refresh access time
            return {**entry["result"], "cached": True}

        _cache_misses += 1

        # Call T3-S3 engine
        start = time.monotonic()
        result = _translate(text, source_lang=source_lang, target_lang=target_lang)
        elapsed_ms = (time.monotonic() - start) * 1000

        result_dict = result.to_dict()
        result_dict["elapsed_ms"] = round(elapsed_ms, 1)
        result_dict["cached"] = False

        # Cache result
        _evict_lru()
        _cache[key] = {"result": result_dict, "ts": time.monotonic()}

        return result_dict

    def detect_language(self, text: str) -> dict:
        """Detect whether text is primarily English or Persian.

        Returns dict with keys: text, detected_lang, confidence.
        """
        lang = _detect(text)
        # Simple confidence: if text has clear character markers, high confidence
        if not text or not text.strip():
            return {"text": text, "detected_lang": "en", "confidence": 0.5}
        return {"text": text, "detected_lang": lang, "confidence": 0.9}

    def get_cache_stats(self) -> dict:
        """Return cache statistics."""
        _evict_expired()
        return {
            "total_entries": len(_cache),
            "max_entries": _MAX_CACHE_ENTRIES,
            "hit_count": _cache_hits,
            "miss_count": _cache_misses,
            "ttl_seconds": _CACHE_TTL_SECONDS,
        }
