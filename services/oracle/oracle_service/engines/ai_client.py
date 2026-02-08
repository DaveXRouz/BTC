"""
AI Client — Anthropic SDK Wrapper
===================================
Low-level wrapper for the Anthropic Python SDK. Provides:
  - Availability checking (API key + SDK import)
  - In-memory dict cache with TTL and max size
  - Thread-safe rate limiting
  - Graceful degradation when SDK/key unavailable

Mirrors patterns from ai_engine.py (cache key, rate limiting, result shape)
but uses the SDK instead of CLI subprocess.
"""

import hashlib
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Configuration (env vars)
# ════════════════════════════════════════════════════════════

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_TIMEOUT = 30

# Cache config
_CACHE_TTL = 3600  # 1 hour
_CACHE_MAX = 200

# Rate limiting
_MIN_INTERVAL = 1.0  # seconds between API calls

# ════════════════════════════════════════════════════════════
# Internal state
# ════════════════════════════════════════════════════════════

_rate_lock = threading.Lock()
_last_call_time = 0.0

_cache_lock = threading.Lock()
_cache = {}  # key -> {"response": str, "timestamp": float}

_client = None
_client_lock = threading.Lock()
_available = None

# Try importing the SDK at module level — but don't fail
_sdk_available = False
try:
    import anthropic as _anthropic_module

    _sdk_available = True
except ImportError:
    _anthropic_module = None


# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


def is_available():
    """Check if AI features are available (API key set + SDK importable).

    Result is cached after first call.

    Returns
    -------
    bool
    """
    global _available
    if _available is not None:
        return _available

    if not _sdk_available:
        logger.info("AI client: anthropic SDK not installed, AI features disabled")
        _available = False
        return False

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.info("AI client: ANTHROPIC_API_KEY not set, AI features disabled")
        _available = False
        return False

    logger.info("AI client: SDK and API key available, AI features enabled")
    _available = True
    return True


def generate(
    prompt, system_prompt="", max_tokens=None, temperature=0.7, use_cache=True
):
    """Generate a response from the Anthropic API.

    Parameters
    ----------
    prompt : str
        The user message to send.
    system_prompt : str
        Optional system prompt for context.
    max_tokens : int or None
        Max tokens in response. Defaults to NPS_AI_MAX_TOKENS env var or 1024.
    temperature : float
        Sampling temperature (0.0-1.0).
    use_cache : bool
        Whether to use the in-memory cache.

    Returns
    -------
    dict
        {"success": bool, "response": str, "error": str|None,
         "elapsed": float, "cached": bool}
    """
    if not is_available():
        return {
            "success": False,
            "response": "",
            "error": "AI not available (no SDK or API key)",
            "elapsed": 0.0,
            "cached": False,
        }

    # Cache lookup
    key = _cache_key(prompt, system_prompt)
    if use_cache:
        cached = _read_cache(key)
        if cached is not None:
            return {
                "success": True,
                "response": cached,
                "error": None,
                "elapsed": 0.0,
                "cached": True,
            }

    # Rate limiting
    _enforce_rate_limit()

    # Resolve config
    if max_tokens is None:
        try:
            max_tokens = int(os.environ.get("NPS_AI_MAX_TOKENS", _DEFAULT_MAX_TOKENS))
        except (ValueError, TypeError):
            max_tokens = _DEFAULT_MAX_TOKENS

    try:
        timeout = int(os.environ.get("NPS_AI_TIMEOUT", _DEFAULT_TIMEOUT))
    except (ValueError, TypeError):
        timeout = _DEFAULT_TIMEOUT

    model = os.environ.get("NPS_AI_MODEL", _DEFAULT_MODEL)

    # Make the API call
    start = time.time()
    try:
        client = _get_client()
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        if timeout:
            kwargs["timeout"] = float(timeout)

        response = client.messages.create(**kwargs)
        elapsed = time.time() - start

        # Extract text from response
        text = ""
        if response.content:
            text = response.content[0].text

        # Cache the result
        if use_cache and text:
            _write_cache(key, text)

        return {
            "success": True,
            "response": text,
            "error": None,
            "elapsed": elapsed,
            "cached": False,
        }

    except Exception as e:
        elapsed = time.time() - start
        error_msg = str(e)
        # Avoid leaking API key in error messages
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key in error_msg:
            error_msg = error_msg.replace(api_key, "***")
        logger.warning("AI client error: %s (%.1fs)", error_msg, elapsed)
        return {
            "success": False,
            "response": "",
            "error": error_msg,
            "elapsed": elapsed,
            "cached": False,
        }


def clear_cache():
    """Remove all cached responses."""
    with _cache_lock:
        _cache.clear()
    logger.info("AI client cache cleared")


def reset_availability():
    """Reset the cached availability check. Useful for testing."""
    global _available, _client
    _available = None
    with _client_lock:
        _client = None


# ════════════════════════════════════════════════════════════
# Internal helpers
# ════════════════════════════════════════════════════════════


def _cache_key(prompt, system_prompt=""):
    """Generate SHA-256 cache key from prompt + system prompt."""
    content = f"{system_prompt}|||{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


def _read_cache(key):
    """Read cached response if it exists and hasn't expired.

    Returns the response string or None.
    """
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > _CACHE_TTL:
            del _cache[key]
            return None
        return entry["response"]


def _write_cache(key, response):
    """Write response to in-memory cache, evicting oldest if over limit."""
    with _cache_lock:
        _cache[key] = {"response": response, "timestamp": time.time()}
        _evict_cache()


def _evict_cache():
    """Remove oldest entries if cache exceeds max size. Must hold _cache_lock."""
    if len(_cache) <= _CACHE_MAX:
        return
    # Sort by timestamp, remove oldest
    sorted_keys = sorted(_cache.keys(), key=lambda k: _cache[k]["timestamp"])
    while len(_cache) > _CACHE_MAX:
        del _cache[sorted_keys.pop(0)]


def _enforce_rate_limit():
    """Block until minimum interval has passed since last API call."""
    global _last_call_time
    with _rate_lock:
        now = time.time()
        wait = _MIN_INTERVAL - (now - _last_call_time)
        if wait > 0:
            time.sleep(wait)
        _last_call_time = time.time()


def _get_client():
    """Lazy singleton client initialization."""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            _client = _anthropic_module.Anthropic(api_key=api_key)
        return _client
