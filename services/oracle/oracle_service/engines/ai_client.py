"""
AI Client — Anthropic SDK Wrapper
===================================
Low-level wrapper for the Anthropic Python SDK. Provides:
  - Availability checking (API key + SDK import)
  - In-memory dict cache with TTL and max size
  - Thread-safe rate limiting
  - Retry logic (1 retry for rate-limit/server/connection errors)
  - Graceful degradation when SDK/key unavailable
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
_DEFAULT_MAX_TOKENS_SINGLE = 2000
_DEFAULT_MAX_TOKENS_MULTI = 3000
_DEFAULT_TIMEOUT = 30

# Cache config
_CACHE_TTL = 3600  # 1 hour
_CACHE_MAX = 200

# Rate limiting
_MIN_INTERVAL = 1.0  # seconds between API calls

# Retry config
_RETRY_WAIT = 2.0  # seconds between retries
_MAX_RETRIES = 1

# ════════════════════════════════════════════════════════════
# Internal state
# ════════════════════════════════════════════════════════════

_rate_lock = threading.Lock()
_last_call_time = 0.0

_cache_lock = threading.Lock()
_cache: dict = {}  # key -> {"response": str, "timestamp": float}

_client = None
_client_lock = threading.Lock()
_available = None

# Try importing the SDK at module level — but don't fail
_sdk_available = False
_RateLimitError = None
_InternalServerError = None
_APIConnectionError = None
_AuthenticationError = None
_BadRequestError = None

try:
    import anthropic as _anthropic_module

    _sdk_available = True
    _RateLimitError = _anthropic_module.RateLimitError
    _InternalServerError = _anthropic_module.InternalServerError
    _APIConnectionError = _anthropic_module.APIConnectionError
    _AuthenticationError = _anthropic_module.AuthenticationError
    _BadRequestError = _anthropic_module.BadRequestError
except ImportError:
    _anthropic_module = None


# ════════════════════════════════════════════════════════════
# Retryable error check
# ════════════════════════════════════════════════════════════


def _is_retryable(exc: Exception) -> bool:
    """Return True if the exception is retryable (rate limit, server, connection)."""
    if not _sdk_available:
        return False
    return isinstance(exc, (_RateLimitError, _InternalServerError, _APIConnectionError))


# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


def is_available() -> bool:
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
    prompt: str,
    system_prompt: str = "",
    max_tokens: int | None = None,
    temperature: float = 0.7,
    use_cache: bool = True,
) -> dict:
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
         "elapsed": float, "cached": bool, "retried": bool}
    """
    if not is_available():
        return {
            "success": False,
            "response": "",
            "error": "AI not available (no SDK or API key)",
            "elapsed": 0.0,
            "cached": False,
            "retried": False,
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
                "retried": False,
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

    # Make the API call with retry logic
    start = time.time()
    retried = False

    for attempt in range(_MAX_RETRIES + 1):
        try:
            client = _get_client()
            kwargs: dict = {
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
                "retried": retried,
            }

        except Exception as e:
            # Check if retryable and haven't exhausted retries
            if _is_retryable(e) and attempt < _MAX_RETRIES:
                retried = True
                logger.warning(
                    "AI client retryable error (attempt %d): %s — retrying in %.1fs",
                    attempt + 1,
                    type(e).__name__,
                    _RETRY_WAIT,
                )
                time.sleep(_RETRY_WAIT)
                continue

            # Non-retryable or retries exhausted
            elapsed = time.time() - start
            error_msg = str(e)
            # Avoid leaking API key in error messages
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if api_key and api_key in error_msg:
                error_msg = error_msg.replace(api_key, "***")

            if _sdk_available and isinstance(e, (_AuthenticationError, _BadRequestError)):
                logger.error("AI client non-retryable error: %s (%.1fs)", error_msg, elapsed)
            else:
                logger.warning("AI client error: %s (%.1fs)", error_msg, elapsed)

            return {
                "success": False,
                "response": "",
                "error": error_msg,
                "elapsed": elapsed,
                "cached": False,
                "retried": retried,
            }

    # Should not reach here, but safety net
    elapsed = time.time() - start
    return {
        "success": False,
        "response": "",
        "error": "Retry exhausted",
        "elapsed": elapsed,
        "cached": False,
        "retried": True,
    }


def generate_reading(
    user_prompt: str,
    system_prompt: str,
    locale: str = "en",
    max_tokens: int = _DEFAULT_MAX_TOKENS_SINGLE,
    use_cache: bool = True,
) -> dict:
    """Convenience wrapper for reading generation.

    Parameters
    ----------
    user_prompt : str
        The formatted user prompt from ai_prompt_builder.
    system_prompt : str
        The Wisdom system prompt from prompt_templates.
    locale : str
        "en" or "fa" — for logging only; prompt already handles locale.
    max_tokens : int
        Max tokens for the response.
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    dict
        Same shape as generate() return value.
    """
    return generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        use_cache=use_cache,
    )


def clear_cache() -> None:
    """Remove all cached responses."""
    with _cache_lock:
        _cache.clear()
    logger.info("AI client cache cleared")


def reset_availability() -> None:
    """Reset the cached availability check. Useful for testing."""
    global _available, _client
    _available = None
    with _client_lock:
        _client = None


# ════════════════════════════════════════════════════════════
# Internal helpers
# ════════════════════════════════════════════════════════════


def _cache_key(prompt: str, system_prompt: str = "") -> str:
    """Generate SHA-256 cache key from prompt + system prompt."""
    content = f"{system_prompt}|||{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()


def _read_cache(key: str) -> str | None:
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


def _write_cache(key: str, response: str) -> None:
    """Write response to in-memory cache, evicting oldest if over limit."""
    with _cache_lock:
        _cache[key] = {"response": response, "timestamp": time.time()}
        _evict_cache()


def _evict_cache() -> None:
    """Remove oldest entries if cache exceeds max size. Must hold _cache_lock."""
    if len(_cache) <= _CACHE_MAX:
        return
    sorted_keys = sorted(_cache.keys(), key=lambda k: _cache[k]["timestamp"])
    while len(_cache) > _CACHE_MAX:
        del _cache[sorted_keys.pop(0)]


def _enforce_rate_limit() -> None:
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
