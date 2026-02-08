"""
Centralized configuration system for NPS.

Provides load/save/get/set with dot-notation access, auto-creation of defaults,
and thread-safe writes.
"""

import copy
import json
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"
_lock = threading.Lock()
_config = None

DEFAULT_CONFIG = {
    "telegram": {
        "bot_token": "",
        "chat_id": "",
        "enabled": True,
        "notify_balance": True,
        "notify_error": True,
        "notify_daily": True,
        "notify_balance_hit": True,
    },
    "balance_check": {
        "btc_rpc_endpoints": ["https://blockstream.info/api"],
        "eth_rpc_endpoints": [
            "https://eth.llamarpc.com",
            "https://rpc.ankr.com/eth",
            "https://ethereum-rpc.publicnode.com",
            "https://1rpc.io/eth",
        ],
        "tokens_to_check": [
            "USDT",
            "USDC",
            "DAI",
            "WBTC",
            "WETH",
            "UNI",
            "LINK",
            "SHIB",
        ],
        "btc_delay": 0.5,
        "eth_delay": 0.3,
        "erc20_delay": 0.2,
        "timeout": 10,
    },
    "scanner": {
        "chains": ["btc", "eth"],
        "batch_size": 1000,
        "check_every_n": 5000,
        "addresses_per_seed": 5,
        "live_feed_max_rows": 200,
        "threads": 1,
        "mode": "both",
        "checkpoint_interval": 100000,
    },
    "headless": {
        "auto_start_scanner": True,
        "scanner_mode": "both",
        "auto_start_puzzles": [],
        "daily_status": True,
        "status_interval_hours": 24,
    },
    "oracle": {
        "reading_history_max": 100,
    },
    "memory": {
        "flush_interval_s": 60,
        "max_memory_mb": 10,
    },
    "performance": {
        "gui_feed_max_fps": 10,
        "gui_stats_max_fps": 2,
        "feed_max_rows": 200,
    },
    "security": {
        "encryption_enabled": False,
    },
    "vault": {
        "auto_record": True,
        "summary_interval": 100,
    },
    "terminals": {
        "max_terminals": 10,
    },
    "learning": {
        "auto_adapt": True,
        "default_model": "sonnet",
    },
    "health": {
        "enabled": True,
        "interval_seconds": 60,
    },
}


def _deep_merge(base, override):
    """Merge override into base, filling missing keys from base."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path=None):
    """Load config from file, merging with defaults for any missing keys.
    Creates file with defaults if absent."""
    global _config
    config_path = Path(path) if path else _CONFIG_PATH

    with _lock:
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                _config = _deep_merge(DEFAULT_CONFIG, file_config)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Config file corrupt, using defaults: {e}")
                _config = copy.deepcopy(DEFAULT_CONFIG)
        else:
            logger.info(f"Config file not found, creating defaults at {config_path}")
            _config = copy.deepcopy(DEFAULT_CONFIG)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(_config, f, indent=2)

    validate()
    return _config


def save_config(config=None, path=None):
    """Write config to disk. Uses current in-memory config if none provided."""
    global _config
    config_path = Path(path) if path else _CONFIG_PATH

    with _lock:
        if config is not None:
            _config = config
        if _config is None:
            _config = copy.deepcopy(DEFAULT_CONFIG)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = config_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(_config, f, indent=2)
        import os

        os.replace(str(tmp_path), str(config_path))


def get(key_path, default=None):
    """Get a config value using dot-notation. E.g. get('telegram.bot_token')."""
    global _config
    if _config is None:
        load_config()

    keys = key_path.split(".")
    current = _config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def set(key_path, value, path=None):
    """Set a config value using dot-notation and auto-save."""
    global _config
    if _config is None:
        load_config()

    with _lock:
        keys = key_path.split(".")
        current = _config
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    save_config(path=path)


def save_config_updates(updates: dict, path=None):
    """Merge updates into current config and save. Atomic write."""
    global _config
    if _config is None:
        load_config()

    with _lock:
        _config = _deep_merge(_config, updates)
        config_path = Path(path) if path else _CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = config_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(_config, f, indent=2)
        import os

        os.replace(str(tmp_path), str(config_path))


def reset_defaults(path=None):
    """Reset config to factory defaults."""
    global _config
    with _lock:
        _config = copy.deepcopy(DEFAULT_CONFIG)
        config_path = Path(path) if path else _CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = config_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(_config, f, indent=2)
        import os

        os.replace(str(tmp_path), str(config_path))


def get_config_path() -> str:
    """Return the absolute path to the config file."""
    return str(_CONFIG_PATH)


def get_bot_token() -> str:
    """Get Telegram bot token (env var NPS_BOT_TOKEN takes priority)."""
    try:
        from engines.security import get_env_or_config

        return get_env_or_config("bot_token", get("telegram.bot_token", ""))
    except ImportError:
        return get("telegram.bot_token", "")


def get_chat_id() -> str:
    """Get Telegram chat ID (env var NPS_CHAT_ID takes priority)."""
    try:
        from engines.security import get_env_or_config

        return get_env_or_config("chat_id", get("telegram.chat_id", ""))
    except ImportError:
        return get("telegram.chat_id", "")


def validate():
    """Validate config, warn about common issues, fix invalid values.

    Checks format and range constraints on all fields.  Invalid values
    are silently reset to their defaults and logged as warnings.

    Returns list of warning strings.
    """
    global _config
    if _config is None:
        load_config()

    warnings = []

    # --- Telegram ---
    token = get("telegram.bot_token", "")
    chat_id = get("telegram.chat_id", "")

    if not token:
        warnings.append("Telegram bot_token is empty")
    elif len(token) < 20 or ":" not in token:
        warnings.append(
            "Telegram bot_token looks malformed (expected digits:alphanumeric)"
        )
        _config["telegram"]["bot_token"] = ""

    if not chat_id:
        warnings.append("Telegram chat_id is empty — notifications disabled")
    elif chat_id and not str(chat_id).lstrip("-").isdigit():
        warnings.append("Telegram chat_id must be numeric — resetting")
        _config["telegram"]["chat_id"] = ""

    # --- Balance check ---
    endpoints = get("balance_check.eth_rpc_endpoints", [])
    if not endpoints:
        warnings.append("No ETH RPC endpoints configured")

    # --- Scanner ---
    valid_chains = {"btc", "eth", "bsc", "polygon"}
    chains = get("scanner.chains", [])
    if chains:
        invalid = [c for c in chains if c not in valid_chains]
        if invalid:
            warnings.append(f"Invalid chain(s) {invalid} — removing")
            _config.setdefault("scanner", {})["chains"] = [
                c for c in chains if c in valid_chains
            ] or ["btc", "eth"]

    batch_size = get("scanner.batch_size", 1000)
    if not isinstance(batch_size, int) or batch_size < 100 or batch_size > 100000:
        warnings.append(
            f"scanner.batch_size={batch_size} out of range [100,100000] — reset to 1000"
        )
        _config.setdefault("scanner", {})["batch_size"] = 1000

    check_every = get("scanner.check_every_n", 5000)
    if not isinstance(check_every, int) or check_every < 100 or check_every > 1000000:
        warnings.append(
            f"scanner.check_every_n={check_every} out of range [100,1000000] — reset to 5000"
        )
        _config.setdefault("scanner", {})["check_every_n"] = 5000

    threads = get("scanner.threads", 1)
    if not isinstance(threads, int) or threads < 1 or threads > 16:
        warnings.append(f"scanner.threads={threads} out of range [1,16] — reset to 1")
        _config.setdefault("scanner", {})["threads"] = 1

    # --- Scanner mode ---
    scanner_mode = get("scanner.mode", "both")
    valid_modes = {"random_key", "seed_phrase", "both"}
    if scanner_mode not in valid_modes:
        warnings.append(
            f"scanner.mode='{scanner_mode}' invalid — must be one of {valid_modes} — reset to 'both'"
        )
        _config.setdefault("scanner", {})["mode"] = "both"

    # --- Scanner checkpoint_interval ---
    cp_interval = get("scanner.checkpoint_interval", 100000)
    if (
        not isinstance(cp_interval, int)
        or cp_interval < 1000
        or cp_interval > 10_000_000
    ):
        warnings.append(
            f"scanner.checkpoint_interval={cp_interval} out of range [1000,10000000] — reset to 100000"
        )
        _config.setdefault("scanner", {})["checkpoint_interval"] = 100000

    # --- Headless ---
    status_hours = get("headless.status_interval_hours", 24)
    if (
        not isinstance(status_hours, (int, float))
        or status_hours < 1
        or status_hours > 168
    ):
        warnings.append(
            f"headless.status_interval_hours={status_hours} out of range [1,168] — reset to 24"
        )
        _config.setdefault("headless", {})["status_interval_hours"] = 24

    # --- Terminals ---
    max_terminals = get("terminals.max_terminals", 10)
    if not isinstance(max_terminals, int) or max_terminals < 1 or max_terminals > 20:
        warnings.append(
            f"terminals.max_terminals={max_terminals} out of range [1,20] — reset to 10"
        )
        _config.setdefault("terminals", {})["max_terminals"] = 10

    # --- Health ---
    health_interval = get("health.interval_seconds", 60)
    if (
        not isinstance(health_interval, int)
        or health_interval < 10
        or health_interval > 3600
    ):
        warnings.append(
            f"health.interval_seconds={health_interval} out of range [10,3600] — reset to 60"
        )
        _config.setdefault("health", {})["interval_seconds"] = 60

    for w in warnings:
        logger.warning(f"Config: {w}")

    return warnings
