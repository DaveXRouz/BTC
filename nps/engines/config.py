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
        "bot_token": "8229103669:AAHv98IVTbtMXENK48DHwT2DXOQ5p1vXJIE",
        "chat_id": "",
        "enabled": True,
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
        with open(config_path, "w") as f:
            json.dump(_config, f, indent=2)


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
        with open(config_path, "w") as f:
            json.dump(_config, f, indent=2)


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
    """Validate config, warn about common issues. Returns list of warnings."""
    global _config
    if _config is None:
        load_config()

    warnings = []
    token = get("telegram.bot_token", "")
    chat_id = get("telegram.chat_id", "")

    if not token:
        warnings.append("Telegram bot_token is empty")
    if not chat_id:
        warnings.append("Telegram chat_id is empty — notifications disabled")

    endpoints = get("balance_check.eth_rpc_endpoints", [])
    if not endpoints:
        warnings.append("No ETH RPC endpoints configured")

    for w in warnings:
        logger.warning(f"Config: {w}")

    return warnings
