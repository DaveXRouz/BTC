"""
Telegram notification system for NPS.

Sends alerts for puzzle solves, balance discoveries, errors, and daily status.
All functions fail silently when unconfigured or on network error.

V3 additions:
- Command registry with _register_command / dispatch_command
- Inline keyboard system with callback routing
- Message queue with rate limiting and auto-retry
- Bot health tracking with auto-disable after consecutive failures
- Notification templates for common alert types
"""

import json
import threading
import time
import logging
import ssl
import urllib.request
import urllib.error

# SSL context -- macOS Python often lacks system CA certs
try:
    import certifi

    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _ssl_ctx = ssl._create_unverified_context()

logger = logging.getLogger(__name__)

CURRENCY_ICONS = {
    "BTC": "\u20bf",
    "ETH": "\u039e",
    "USDT": "\u20ae",
    "USDC": "\u25c9",
    "DAI": "\u25c8",
    "WBTC": "\u20bfw",
    "LINK": "\u2b21",
    "SHIB": "SHIB",
}

CONTROL_BUTTONS = [
    [
        {"text": "Status", "callback_data": "/status"},
        {"text": "Pause", "callback_data": "/pause"},
    ],
    [
        {"text": "Resume", "callback_data": "/resume"},
        {"text": "Stop", "callback_data": "/stop"},
    ],
]

COMMANDS = {
    "/start": "Start scanning",
    "/stop": "Stop scanning",
    "/pause": "Pause all terminals",
    "/resume": "Resume all terminals",
    "/status": "Show current status",
    "/sign": "Oracle sign reading",
    "/name": "Name reading",
    "/memory": "Show memory stats",
    "/vault": "Show vault summary",
    "/perf": "Show performance stats",
    "/terminals": "List all terminals",
    "/checkpoint": "Force checkpoint save",
    "/help": "Show available commands",
    "/menu": "Show main menu",
    "/health": "Endpoint health status",
    "/daily": "Oracle daily insight",
    "/start_all": "Start all terminals",
    "/stop_all": "Stop all terminals",
    "/pause_all": "Pause all terminals",
    "/resume_all": "Resume all terminals",
    "/set": "Change setting (mode|puzzle|chains|sound)",
    "/export": "Export vault or report",
}

_lock = threading.Lock()
_last_send_time = 0.0
_error_count = 0
_error_count_reset_time = 0.0
_MAX_ERRORS_PER_HOUR = 10
_MIN_SEND_INTERVAL = 2.0
_MAX_MESSAGE_LENGTH = 4096
_last_update_id = 0

# ================================================================
# Bot Health & Auto-Disable (4.5)
# ================================================================

_consecutive_failures = 0
_bot_disabled = False
_BOT_DISABLE_THRESHOLD = 5


def is_bot_healthy():
    """Return True if the bot has not been auto-disabled due to consecutive failures."""
    return not _bot_disabled


def _record_success():
    """Record a successful API call; re-enable bot if it was disabled."""
    global _consecutive_failures, _bot_disabled
    with _lock:
        _consecutive_failures = 0
        if _bot_disabled:
            _bot_disabled = False
            logger.info("Telegram bot re-enabled after successful send")


def _record_failure():
    """Record a failed API call; disable bot after threshold."""
    global _consecutive_failures, _bot_disabled
    with _lock:
        _consecutive_failures += 1
        if _consecutive_failures >= _BOT_DISABLE_THRESHOLD and not _bot_disabled:
            _bot_disabled = True
            logger.error(
                "Telegram bot auto-disabled after %d consecutive failures",
                _consecutive_failures,
            )


# ================================================================
# Message Queue & Rate Limiting (4.4)
# ================================================================

_message_queue = []
_queue_lock = threading.Lock()
_queue_thread = None
_queue_running = False


def _enqueue_message(text, buttons=None, parse_mode="HTML"):
    """Add a message to the outgoing queue. Starts processor if needed."""
    global _queue_thread, _queue_running
    with _queue_lock:
        _message_queue.append(
            {
                "text": text,
                "buttons": buttons,
                "parse_mode": parse_mode,
            }
        )

    # Start queue processor daemon if not running
    if not _queue_running:
        _queue_running = True
        _queue_thread = threading.Thread(target=_process_queue, daemon=True)
        _queue_thread.start()


def _process_queue():
    """Daemon thread: processes queued messages at 1 msg/sec."""
    global _queue_running
    while True:
        msg = None
        with _queue_lock:
            if _message_queue:
                msg = _message_queue.pop(0)

        if msg is None:
            # No messages -- check again in 0.5s, exit after 10s idle
            time.sleep(0.5)
            with _queue_lock:
                if not _message_queue:
                    _queue_running = False
                    return
            continue

        # Send with retry
        _send_with_retry(
            msg["text"],
            buttons=msg.get("buttons"),
            parse_mode=msg.get("parse_mode", "HTML"),
        )
        time.sleep(1.0)  # 1 msg/sec rate limit


def _send_with_retry(text, buttons=None, parse_mode="HTML", max_retries=3):
    """Send a message with exponential backoff retry (1s, 2s, 4s).

    Returns True on success, False after all retries exhausted.
    """
    if _bot_disabled:
        logger.debug("Bot disabled, skipping send_with_retry")
        return False

    for attempt in range(max_retries):
        if buttons:
            ok = send_message_with_buttons(text, buttons, parse_mode)
        else:
            ok = send_message(text, parse_mode)

        if ok:
            return True

        if attempt < max_retries - 1:
            delay = 2**attempt  # 1s, 2s, 4s
            time.sleep(delay)

    return False


# ================================================================
# Core Send Functions (preserved from V2)
# ================================================================


def is_configured():
    """Check if Telegram bot token and chat_id are both set."""
    try:
        from engines.config import get

        token = get("telegram.bot_token", "")
        chat_id = get("telegram.chat_id", "")
        enabled = get("telegram.enabled", True)
        return bool(token and chat_id and enabled)
    except Exception:
        return False


def _send_raw(token, chat_id, text, parse_mode="HTML"):
    """Send a message via Telegram Bot API. Returns True on success."""
    global _last_send_time, _error_count, _error_count_reset_time

    # Rate limiting
    with _lock:
        now = time.time()
        elapsed = now - _last_send_time
        if elapsed < _MIN_SEND_INTERVAL:
            time.sleep(_MIN_SEND_INTERVAL - elapsed)

        # Error rate limiting
        if now - _error_count_reset_time > 3600:
            _error_count = 0
            _error_count_reset_time = now

    # Truncate long messages
    if len(text) > _MAX_MESSAGE_LENGTH:
        text = text[: _MAX_MESSAGE_LENGTH - 20] + "\n... (truncated)"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            with _lock:
                _last_send_time = time.time()
            _record_success()
            return True
    except Exception as e:
        with _lock:
            _error_count += 1
        _record_failure()
        logger.debug(f"Telegram send failed: {e}")
        return False


def _send_async(text, parse_mode="HTML"):
    """Send message in a daemon thread (fire-and-forget)."""
    try:
        from engines.config import get

        token = get("telegram.bot_token", "")
        chat_id = get("telegram.chat_id", "")
    except Exception:
        return

    if not token or not chat_id:
        return

    def _do_send():
        _send_raw(token, chat_id, text, parse_mode)

    threading.Thread(target=_do_send, daemon=True).start()


def send_message(text, parse_mode="HTML"):
    """Send a message via Telegram. Returns False silently when unconfigured."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        token = get("telegram.bot_token", "")
        chat_id = get("telegram.chat_id", "")
        return _send_raw(token, chat_id, text, parse_mode)
    except Exception:
        return False


def send_message_with_buttons(text, buttons=None, parse_mode="HTML"):
    """Send a message with inline keyboard buttons via Bot API."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        token = get("telegram.bot_token", "")
        chat_id = get("telegram.chat_id", "")
    except Exception:
        return False

    if not token or not chat_id:
        return False

    if len(text) > _MAX_MESSAGE_LENGTH:
        text = text[: _MAX_MESSAGE_LENGTH - 20] + "\n... (truncated)"

    payload_dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if buttons:
        payload_dict["reply_markup"] = {"inline_keyboard": buttons}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps(payload_dict).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            with _lock:
                global _last_send_time
                _last_send_time = time.time()
            _record_success()
            return True
    except Exception as e:
        _record_failure()
        logger.debug(f"Telegram send_with_buttons failed: {e}")
        return False


def _send_with_buttons_async(text, buttons=None, parse_mode="HTML"):
    """Send message with buttons in a daemon thread (fire-and-forget)."""

    def _do_send():
        send_message_with_buttons(text, buttons, parse_mode)

    threading.Thread(target=_do_send, daemon=True).start()


# ================================================================
# Polling (4.7 fix: preserve full command text)
# ================================================================


def poll_telegram_commands(timeout=10):
    """Long-poll Telegram for commands via getUpdates. Returns list of command strings."""
    global _last_update_id

    if not is_configured():
        return []

    try:
        from engines.config import get

        token = get("telegram.bot_token", "")
    except Exception:
        return []

    if not token:
        return []

    url = (
        f"https://api.telegram.org/bot{token}/getUpdates"
        f"?offset={_last_update_id + 1}&timeout={timeout}"
    )
    req = urllib.request.Request(url)

    commands = []
    try:
        with urllib.request.urlopen(req, timeout=timeout + 5, context=_ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for update in data.get("result", []):
                update_id = update.get("update_id", 0)
                if update_id > _last_update_id:
                    _last_update_id = update_id

                # Handle callback queries (inline button presses)
                cb = update.get("callback_query")
                if cb:
                    cmd = cb.get("data", "")
                    if cmd:
                        commands.append(cmd)
                    # Acknowledge the callback immediately in background
                    cb_id = cb.get("id")
                    if cb_id:
                        ack_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery?callback_query_id={cb_id}"
                        threading.Thread(
                            target=lambda u: urllib.request.urlopen(
                                u, timeout=5, context=_ssl_ctx
                            ),
                            args=(ack_url,),
                            daemon=True,
                        ).start()

                # Handle text messages starting with /
                msg = update.get("message", {})
                text = msg.get("text", "")
                if text.startswith("/"):
                    # 4.7 FIX: preserve full text including arguments
                    commands.append(text)
    except Exception as e:
        logger.debug(f"Telegram poll failed: {e}")

    return commands


# ================================================================
# Notification Functions (preserved from V2)
# ================================================================


def notify_solve(puzzle_id, private_key, address):
    """Notify about a puzzle solve."""
    if not is_configured():
        return False

    key_hex = hex(private_key) if isinstance(private_key, int) else str(private_key)
    text = (
        f"<b>PUZZLE SOLVED!</b>\n\n"
        f"Puzzle: #{puzzle_id}\n"
        f"Key: <code>{key_hex}</code>\n"
        f"Address: <code>{address}</code>\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )
    _send_async(text)
    return True


def notify_balance_found(address, balance_btc, source="unknown"):
    """Notify about a balance discovery."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        if not get("telegram.notify_balance", True):
            return False
    except Exception:
        pass

    text = (
        f"<b>BALANCE FOUND!</b>\n\n"
        f"Address: <code>{address}</code>\n"
        f"Balance: \u20bf {balance_btc} BTC\n"
        f"Source: {source}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )
    _send_with_buttons_async(text, CONTROL_BUTTONS)
    return True


def notify_error(error_msg, context=""):
    """Notify about an error. Rate-limited to 10/hour."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        if not get("telegram.notify_error", True):
            return False
    except Exception:
        pass

    with _lock:
        if _error_count >= _MAX_ERRORS_PER_HOUR:
            return False

    text = (
        f"<b>NPS Error</b>\n\n"
        f"Context: {context}\n"
        f"Error: {error_msg}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )
    _send_async(text)
    return True


def notify_daily_status(stats):
    """Send daily status summary."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        if not get("telegram.notify_daily", True):
            return False
    except Exception:
        pass

    keys_tested = stats.get("keys_tested", 0)
    seeds_tested = stats.get("seeds_tested", 0)
    online_checks = stats.get("online_checks", 0)
    hits = stats.get("hits", 0)
    uptime = stats.get("uptime", "unknown")

    text = (
        f"<b>\u20bf NPS Daily Status</b>\n\n"
        f"Keys tested: {keys_tested:,}\n"
        f"Seeds tested: {seeds_tested:,}\n"
        f"Online checks: {online_checks:,}\n"
        f"Hits: {hits}\n"
        f"Uptime: {uptime}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )
    _send_with_buttons_async(text, CONTROL_BUTTONS)
    return True


def notify_scanner_hit(address_dict, private_key, balances, method="unknown"):
    """Notify about a scanner hit (multi-chain version)."""
    if not is_configured():
        return False

    try:
        from engines.config import get

        if not get("telegram.notify_balance", True):
            return False
    except Exception:
        pass

    key_hex = hex(private_key) if isinstance(private_key, int) else str(private_key)
    btc_addr = address_dict.get("btc", "N/A")
    eth_addr = address_dict.get("eth", "N/A")

    balance_lines = []
    for chain, amount in balances.items():
        if amount and amount != "0" and amount != 0:
            icon = CURRENCY_ICONS.get(chain.upper(), "")
            balance_lines.append(f"  {icon} {chain.upper()}: {amount}")

    balance_text = "\n".join(balance_lines) if balance_lines else "  (checking...)"

    text = (
        f"<b>SCANNER HIT!</b>\n\n"
        f"Method: {method}\n"
        f"Key: <code>{key_hex}</code>\n"
        f"BTC: <code>{btc_addr}</code>\n"
        f"ETH: <code>{eth_addr}</code>\n"
        f"Balances:\n{balance_text}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )
    _send_with_buttons_async(text, CONTROL_BUTTONS)
    return True


# ================================================================
# Multi-Chain Balance Found Notification (preserved from V2)
# ================================================================


def notify_balance_found_multi(address_dict, balances, source="unknown"):
    """Notify about a multi-chain balance discovery with inline buttons.

    Parameters
    ----------
    address_dict : dict
        Dict with chain addresses, e.g. {"btc": "1A...", "eth": "0x..."}.
    balances : dict
        Dict with chain balances, e.g. {"btc": {"balance_btc": 0.5}, "eth": {"balance_eth": 1.2}}.
    source : str
        Source/method that found the balance.
    """
    if not is_configured():
        return False

    try:
        from engines.config import get

        if not get("telegram.notify_balance", True):
            return False
    except Exception:
        pass

    # Build address lines
    addr_lines = []
    for chain, addr in address_dict.items():
        if addr:
            icon = CURRENCY_ICONS.get(chain.upper(), "")
            addr_lines.append(f"  {icon} {chain.upper()}: <code>{addr}</code>")
    addr_text = "\n".join(addr_lines) if addr_lines else "  (none)"

    # Build balance lines
    balance_lines = []
    for chain, bal_data in balances.items():
        if isinstance(bal_data, dict):
            icon = CURRENCY_ICONS.get(chain.upper(), "")
            if chain.lower() == "btc":
                amount = bal_data.get("balance_btc", 0)
                if amount:
                    balance_lines.append(f"  {icon} BTC: {amount}")
            elif chain.lower() == "eth":
                amount = bal_data.get("balance_eth", 0)
                if amount:
                    balance_lines.append(f"  {icon} ETH: {amount}")
            else:
                # Token or other chain
                amount = bal_data.get("balance", bal_data.get("balance_human", 0))
                if amount:
                    balance_lines.append(f"  {icon} {chain.upper()}: {amount}")
        elif bal_data and bal_data != 0 and bal_data != "0":
            icon = CURRENCY_ICONS.get(chain.upper(), "")
            balance_lines.append(f"  {icon} {chain.upper()}: {bal_data}")

    balance_text = "\n".join(balance_lines) if balance_lines else "  (checking...)"

    text = (
        f"<b>MULTI-CHAIN BALANCE FOUND!</b>\n\n"
        f"Addresses:\n{addr_text}\n\n"
        f"Balances:\n{balance_text}\n\n"
        f"Source: {source}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )

    # Inline buttons for quick actions
    buttons = [
        [
            {"text": "View Details", "callback_data": "/status"},
            {"text": "Stop Scanner", "callback_data": "/stop"},
        ],
        [
            {"text": "Continue", "callback_data": "/start"},
        ],
    ]

    _send_with_buttons_async(text, buttons)
    return True


# ================================================================
# Notification Templates (4.6)
# ================================================================


def _format_balance_hit(data):
    """Format a balance hit notification as HTML.

    Parameters
    ----------
    data : dict
        Keys: address, balance, chain, method, key (optional).

    Returns
    -------
    str
        HTML-formatted notification string.
    """
    address = data.get("address", "unknown")
    balance = data.get("balance", 0)
    chain = data.get("chain", "BTC").upper()
    method = data.get("method", "unknown")
    icon = CURRENCY_ICONS.get(chain, "")

    lines = [
        "\U0001f4b0 <b>Balance Hit!</b>",
        "",
        f"Chain: {icon} {chain}",
        f"Address: <code>{address}</code>",
        f"Balance: {balance}",
        f"Method: {method}",
    ]

    key = data.get("key")
    if key:
        lines.append(f"Key: <code>{key}</code>")

    lines.append(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    return "\n".join(lines)


def _format_daily_report(stats):
    """Format a daily report notification as HTML.

    Parameters
    ----------
    stats : dict
        Keys: keys_tested, seeds_tested, hits, uptime, speed, terminals.

    Returns
    -------
    str
        HTML-formatted daily report string.
    """
    keys = stats.get("keys_tested", 0)
    seeds = stats.get("seeds_tested", 0)
    hits = stats.get("hits", 0)
    uptime = stats.get("uptime", "N/A")
    speed = stats.get("speed", 0)
    terminals = stats.get("terminals", 0)

    return (
        "\U0001f4ca <b>NPS Daily Report</b>\n"
        "\n"
        f"Terminals: {terminals}\n"
        f"Keys tested: {keys:,}\n"
        f"Seeds tested: {seeds:,}\n"
        f"Speed: {speed:,.0f}/s\n"
        f"Hits: {hits}\n"
        f"Uptime: {uptime}\n"
        f"Date: {time.strftime('%Y-%m-%d', time.gmtime())}"
    )


def _format_health_alert(data):
    """Format a health alert notification as HTML.

    Parameters
    ----------
    data : dict
        Keys: endpoint, healthy (bool), url, previous_state (optional).

    Returns
    -------
    str
        HTML-formatted health alert string.
    """
    endpoint = data.get("endpoint", "unknown")
    healthy = data.get("healthy", False)
    url = data.get("url", "")

    status_icon = "\u2705" if healthy else "\u274c"
    status_text = "UP" if healthy else "DOWN"

    return (
        f"\U0001f3e5 <b>Health Alert</b>\n"
        f"\n"
        f"{status_icon} {endpoint}: {status_text}\n"
        f"URL: {url}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )


def _format_ai_adjustment(data):
    """Format an AI adjustment notification as HTML.

    Parameters
    ----------
    data : dict
        Keys: parameter, old_value, new_value, reason, level (optional).

    Returns
    -------
    str
        HTML-formatted AI adjustment string.
    """
    param = data.get("parameter", "unknown")
    old_val = data.get("old_value", "?")
    new_val = data.get("new_value", "?")
    reason = data.get("reason", "optimization")
    level = data.get("level", "")

    level_text = f"\nAI Level: {level}" if level else ""

    return (
        f"\U0001f9e0 <b>AI Adjustment</b>\n"
        f"\n"
        f"Parameter: {param}\n"
        f"Old: {old_val}\n"
        f"New: {new_val}\n"
        f"Reason: {reason}{level_text}\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
    )


# ================================================================
# Command Registry (4.1)
# ================================================================

_command_registry = {}


def _register_command(name, desc, category, handler):
    """Register a command in the command registry.

    Parameters
    ----------
    name : str
        Command name including leading '/' (e.g., '/status').
    desc : str
        Human-readable description.
    category : str
        Category: 'status', 'control', 'oracle', 'settings', 'export'.
    handler : callable
        Function(arg, app_controller) -> (text, buttons_or_None).
    """
    _command_registry[name.lower()] = {
        "name": name,
        "desc": desc,
        "category": category,
        "handler": handler,
    }


# ================================================================
# Inline Keyboard System (4.3)
# ================================================================

MAIN_MENU_BUTTONS = [
    [
        {"text": "\U0001f4ca Status", "callback_data": "menu:status"},
        {"text": "\U0001f3e5 Health", "callback_data": "menu:health"},
    ],
    [
        {"text": "\U0001f5a5 Terminals", "callback_data": "menu:terminals"},
        {"text": "\U0001f52e Oracle", "callback_data": "menu:oracle"},
    ],
    [
        {"text": "\u2699\ufe0f Settings", "callback_data": "menu:settings"},
        {"text": "\U0001f4e6 Export", "callback_data": "menu:export"},
    ],
    [
        {"text": "\u2753 Help", "callback_data": "menu:help"},
    ],
]


def _dispatch_to_handler(cmd, arg, app_controller=None):
    """Look up a command in the registry and call its handler.

    Returns (text, buttons_or_None) tuple. Does NOT send the message.
    """
    entry = _command_registry.get(cmd.lower())
    if entry:
        try:
            return entry["handler"](arg, app_controller)
        except Exception as e:
            logger.debug(f"Error in handler for {cmd}: {e}")
            return (f"Error processing {cmd}: {e}", None)
    return (f"Unknown command: {cmd}\nUse /help for available commands.", None)


def _route_callback(callback_data, app_controller=None):
    """Route an inline keyboard callback to the appropriate handler.

    Parameters
    ----------
    callback_data : str
        Callback data in ``section:action:param`` format.
    app_controller : object or None
        Optional app controller for commands that need it.

    Returns
    -------
    tuple(str, list or None)
        (response_text, buttons_or_None)
    """
    parts = callback_data.split(":")
    section = parts[0] if parts else ""
    action = parts[1] if len(parts) > 1 else ""
    param = parts[2] if len(parts) > 2 else ""

    if section == "menu":
        # Route menu callbacks to corresponding commands
        menu_map = {
            "status": "/status",
            "health": "/health",
            "terminals": "/terminals",
            "oracle": "/daily",
            "settings": "/help",
            "export": "/vault",
            "help": "/help",
        }
        cmd = menu_map.get(action, "/help")
        return _dispatch_to_handler(cmd, "", app_controller)

    elif section == "ctrl":
        ctrl_map = {
            "start_all": "/start_all",
            "stop_all": "/stop_all",
            "pause_all": "/pause_all",
            "resume_all": "/resume_all",
            "checkpoint": "/checkpoint",
        }
        cmd = ctrl_map.get(action, "/help")
        return _dispatch_to_handler(cmd, "", app_controller)

    else:
        # Try as a direct command (e.g., legacy /status callback)
        if callback_data.startswith("/"):
            parts_cmd = callback_data.split(maxsplit=1)
            cmd = parts_cmd[0].lower()
            arg = parts_cmd[1].strip() if len(parts_cmd) > 1 else ""
            return _dispatch_to_handler(cmd, arg, app_controller)
        return ("Unknown callback. Use /menu for options.", None)


# ================================================================
# Command Handlers (4.2)
# ================================================================


def _cmd_start(arg, app_controller):
    """Welcome message with inline menu."""
    text = (
        "\U0001f680 <b>NPS Numerology Puzzle Solver</b>\n\n"
        "Welcome! Use the menu below or type /help for commands."
    )
    return (text, MAIN_MENU_BUTTONS)


def _cmd_menu(arg, app_controller):
    """Show the main menu with inline keyboard."""
    text = "<b>Main Menu</b>\nSelect an option:"
    return (text, MAIN_MENU_BUTTONS)


def _cmd_status(arg, app_controller):
    """Show current NPS status."""
    try:
        from engines.terminal_manager import get_all_stats, get_active_count

        active = get_active_count()
        stats = get_all_stats()
        total_keys = sum(s.get("keys_tested", 0) for s in stats.values())
        total_speed = sum(s.get("speed", 0) for s in stats.values())
        text = (
            f"<b>\U0001f4ca NPS Status</b>\n"
            f"Active terminals: {active}\n"
            f"Total keys: {total_keys:,}\n"
            f"Speed: {total_speed:,.0f}/s"
        )
    except Exception:
        text = "<b>\U0001f4ca NPS Status</b>\nNo active terminals."
    return (text, None)


def _cmd_health(arg, app_controller):
    """Show endpoint health status."""
    try:
        from engines.health import get_status as health_get_status

        status = health_get_status()
        if not status:
            return (
                "<b>\U0001f3e5 Health</b>\nNo health data yet. Monitoring may not be running.",
                None,
            )

        lines = ["<b>\U0001f3e5 Endpoint Health</b>"]
        for name, info in status.items():
            healthy = info.get("healthy", False)
            icon = "\u2705" if healthy else "\u274c"
            last_check = info.get("last_check", 0)
            ago = ""
            if last_check:
                seconds_ago = int(time.time() - last_check)
                ago = f" ({seconds_ago}s ago)"
            lines.append(f"  {icon} {name}{ago}")
        text = "\n".join(lines)
    except Exception:
        text = "<b>\U0001f3e5 Health</b>\nHealth monitoring not available."
    return (text, None)


def _cmd_perf(arg, app_controller):
    """Show performance statistics."""
    try:
        from engines.perf import perf

        summary = perf.summary()
        if summary:
            lines = ["<b>\u23f1 Performance</b>"]
            for name, stats in summary.items():
                lines.append(
                    f"  {name}: avg={stats['avg']*1000:.1f}ms n={stats['count']}"
                )
            text = "\n".join(lines)
        else:
            text = "<b>\u23f1 Performance</b>\nNo performance data yet."
    except Exception:
        text = "<b>\u23f1 Performance</b>\nPerformance stats not available."
    return (text, None)


def _cmd_help(arg, app_controller):
    """Show full command reference grouped by category."""
    categories = {}
    for name, info in _command_registry.items():
        cat = info.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((info["name"], info["desc"]))

    lines = ["<b>\u2753 Command Reference</b>"]
    cat_order = ["status", "control", "oracle", "settings", "export"]
    cat_labels = {
        "status": "\U0001f4ca Status",
        "control": "\U0001f3ae Control",
        "oracle": "\U0001f52e Oracle",
        "settings": "\u2699\ufe0f Settings",
        "export": "\U0001f4e6 Export",
    }

    for cat in cat_order:
        cmds = categories.get(cat, [])
        if cmds:
            lines.append(f"\n<b>{cat_labels.get(cat, cat)}</b>")
            for cmd_name, cmd_desc in sorted(cmds):
                lines.append(f"  {cmd_name} -- {cmd_desc}")

    # Catch any categories not in the predefined order
    for cat, cmds in categories.items():
        if cat not in cat_order and cmds:
            lines.append(f"\n<b>{cat.title()}</b>")
            for cmd_name, cmd_desc in sorted(cmds):
                lines.append(f"  {cmd_name} -- {cmd_desc}")

    return ("\n".join(lines), None)


def _cmd_start_all(arg, app_controller):
    """Start all terminals."""
    try:
        from engines.terminal_manager import start_all

        count = start_all()
        return (f"<b>\u25b6 Started {count} terminal(s).</b>", None)
    except Exception:
        return ("Start failed -- no terminal manager available.", None)


def _cmd_stop_all(arg, app_controller):
    """Stop all terminals."""
    try:
        from engines.terminal_manager import stop_all

        count = stop_all()
        return (f"<b>\u23f9 Stopped {count} terminal(s).</b>", None)
    except Exception:
        return ("Stop failed -- no terminal manager available.", None)


def _cmd_pause_all(arg, app_controller):
    """Pause all terminals."""
    try:
        from engines.terminal_manager import stop_all

        count = stop_all()
        return (f"<b>\u23f8 Paused {count} terminal(s).</b>", None)
    except Exception:
        return ("Pause failed -- no terminal manager available.", None)


def _cmd_resume_all(arg, app_controller):
    """Resume all terminals."""
    try:
        from engines.terminal_manager import start_all

        count = start_all()
        return (f"<b>\u25b6 Resumed {count} terminal(s).</b>", None)
    except Exception:
        return ("Resume failed -- no terminal manager available.", None)


def _cmd_checkpoint(arg, app_controller):
    """Force checkpoint save on all terminals."""
    try:
        from engines.terminal_manager import list_terminals, get_terminal_stats

        terminals = list_terminals()
        saved = 0
        for tid in terminals:
            stats = get_terminal_stats(tid)
            solver = stats.get("_solver")
            if solver and hasattr(solver, "save_checkpoint"):
                solver.save_checkpoint()
                saved += 1
        return (f"<b>\U0001f4be Checkpoint saved for {saved} terminal(s).</b>", None)
    except Exception:
        return ("Checkpoint save failed.", None)


def _cmd_sign(arg, app_controller):
    """Oracle sign reading."""
    if not arg:
        return ("Usage: /sign &lt;question or sign text&gt;", None)
    try:
        from engines.oracle import question_sign

        result = question_sign(arg)
        reading = result.get("reading", "No reading")
        advice = result.get("advice", "")
        text = f"<b>\U0001f52e Oracle: {arg}</b>\n{reading}\n{advice}"
        return (text, None)
    except Exception as e:
        return (f"Oracle error: {e}", None)


def _cmd_name(arg, app_controller):
    """Name numerology reading."""
    if not arg:
        return ("Usage: /name &lt;name&gt;", None)
    try:
        from engines.oracle import read_name

        result = read_name(arg)
        expr = result.get("expression", "?")
        soul = result.get("soul_urge", "?")
        text = f"<b>\U0001f4db Name: {arg}</b>\nExpression: {expr}\nSoul Urge: {soul}"
        return (text, None)
    except Exception as e:
        return (f"Name error: {e}", None)


def _cmd_daily(arg, app_controller):
    """Oracle daily insight."""
    try:
        from engines.oracle import daily_insight

        result = daily_insight()
        insight = result.get("insight", "Trust the process")
        energy = result.get("energy", "")
        lucky = result.get("lucky_numbers", [])
        lucky_str = ", ".join(str(n) for n in lucky) if lucky else "N/A"
        text = (
            f"<b>\U0001f31f Daily Insight</b>\n\n"
            f"{insight}\n"
            f"Energy: {energy}\n"
            f"Lucky numbers: {lucky_str}"
        )
        return (text, None)
    except Exception as e:
        return (f"Daily insight error: {e}", None)


def _cmd_memory(arg, app_controller):
    """Show AI memory / learning stats."""
    try:
        from engines.learner import get_level, get_insights

        level = get_level()
        insights = get_insights(limit=3)
        insight_text = (
            "\n".join(f"  - {i}" for i in insights) if insights else "  (none yet)"
        )
        text = (
            f"<b>\U0001f9e0 AI Brain</b>\n"
            f"Level: {level.get('level', 1)} -- {level.get('name', 'Novice')}\n"
            f"XP: {level.get('xp', 0)}\n"
            f"Recent Insights:\n{insight_text}"
        )
        return (text, None)
    except Exception:
        try:
            from engines.memory import get_summary

            s = get_summary()
            text = (
                f"<b>\U0001f9e0 Memory Stats</b>\n"
                f"Sessions: {s.get('total_sessions', 0)}\n"
                f"Keys: {s.get('total_keys', 0):,}"
            )
            return (text, None)
        except Exception:
            return ("Memory stats not available.", None)


def _cmd_vault(arg, app_controller):
    """Show vault summary."""
    try:
        from engines.vault import get_summary

        s = get_summary()
        text = (
            f"<b>\U0001f512 Vault Summary</b>\n"
            f"Total findings: {s.get('total', 0)}\n"
            f"With balance: {s.get('with_balance', 0)}\n"
            f"Vault size: {s.get('vault_size', 'unknown')}"
        )
        return (text, None)
    except Exception:
        return ("Vault not available.", None)


def _cmd_terminals(arg, app_controller):
    """List all terminals."""
    try:
        from engines.terminal_manager import list_terminals, get_terminal_stats

        terminals = list_terminals()
        if not terminals:
            return ("<b>\U0001f5a5 Terminals</b>\nNo terminals created.", None)
        lines = ["<b>\U0001f5a5 Terminals</b>"]
        for tid in terminals:
            stats = get_terminal_stats(tid)
            status = stats.get("status", "unknown")
            keys = stats.get("keys_tested", 0)
            lines.append(f"  {tid}: {status} -- {keys:,} keys")
        return ("\n".join(lines), None)
    except Exception:
        return ("Terminal manager not available.", None)


def _cmd_set(arg, app_controller):
    """Change a setting: /set mode|puzzle|chains|sound <value>."""
    if not arg:
        return (
            "Usage: /set &lt;setting&gt; &lt;value&gt;\n"
            "Settings: mode, puzzle, chains, sound",
            None,
        )

    parts = arg.split(maxsplit=1)
    setting = parts[0].lower()
    value = parts[1].strip() if len(parts) > 1 else ""

    if not value:
        return (f"Usage: /set {setting} &lt;value&gt;", None)

    try:
        from engines.config import get, set as config_set

        setting_map = {
            "mode": "scanner.mode",
            "puzzle": "scanner.puzzle_number",
            "chains": "scanner.chains",
            "sound": "telegram.sound_enabled",
        }

        config_key = setting_map.get(setting)
        if not config_key:
            return (
                f"Unknown setting: {setting}\n"
                "Available: mode, puzzle, chains, sound",
                None,
            )

        # Type coercion
        if setting == "chains":
            value = [c.strip() for c in value.split(",")]
        elif setting == "sound":
            value = value.lower() in ("true", "1", "on", "yes")
        elif setting == "puzzle":
            try:
                value = int(value)
            except ValueError:
                pass

        config_set(config_key, value)
        return (f"<b>\u2699\ufe0f Setting updated</b>\n{setting} = {value}", None)
    except Exception as e:
        return (f"Failed to update setting: {e}", None)


def _cmd_export(arg, app_controller):
    """Export vault or report: /export vault csv|json, /export report."""
    if not arg:
        return (
            "Usage:\n"
            "  /export vault csv\n"
            "  /export vault json\n"
            "  /export report",
            None,
        )

    parts = arg.lower().split()
    target = parts[0]
    fmt = parts[1] if len(parts) > 1 else ""

    if target == "vault":
        if fmt == "csv":
            try:
                from engines.vault import export_csv

                path = export_csv()
                return (f"<b>\U0001f4e6 Vault exported (CSV)</b>\nPath: {path}", None)
            except Exception as e:
                return (f"CSV export failed: {e}", None)
        elif fmt == "json":
            try:
                from engines.vault import export_json

                path = export_json()
                return (f"<b>\U0001f4e6 Vault exported (JSON)</b>\nPath: {path}", None)
            except Exception as e:
                return (f"JSON export failed: {e}", None)
        else:
            return ("Usage: /export vault csv|json", None)

    elif target == "report":
        try:
            from engines.vault import get_summary

            s = get_summary()
            text = (
                f"<b>\U0001f4e6 NPS Report</b>\n\n"
                f"Total findings: {s.get('total', 0)}\n"
                f"With balance: {s.get('with_balance', 0)}\n"
                f"Vault size: {s.get('vault_size', 'unknown')}\n"
                f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}"
            )
            return (text, None)
        except Exception as e:
            return (f"Report generation failed: {e}", None)

    else:
        return (
            "Usage:\n" "  /export vault csv|json\n" "  /export report",
            None,
        )


# Backward compat: /stop, /pause, /resume mapped to old behavior
def _cmd_stop(arg, app_controller):
    """Stop scanning (legacy, delegates to stop_all)."""
    return _cmd_stop_all(arg, app_controller)


def _cmd_pause(arg, app_controller):
    """Pause (legacy, delegates to pause_all)."""
    return _cmd_pause_all(arg, app_controller)


def _cmd_resume(arg, app_controller):
    """Resume (legacy, delegates to resume_all)."""
    return _cmd_resume_all(arg, app_controller)


def _cmd_mode(arg, app_controller):
    """Change mode via app_controller (legacy)."""
    if not arg:
        return ("Usage: /mode &lt;mode_name&gt;", None)
    if app_controller and hasattr(app_controller, "change_mode"):
        try:
            result = app_controller.change_mode(arg)
            if result:
                return (f"Mode changed to: {arg}", None)
            return (f"Failed to change mode to: {arg}", None)
        except Exception as e:
            return (f"Mode change error: {e}", None)
    return _cmd_set(f"mode {arg}", app_controller)


def _cmd_puzzle(arg, app_controller):
    """Show puzzle status (legacy)."""
    if app_controller and hasattr(app_controller, "get_puzzle_status"):
        try:
            status = app_controller.get_puzzle_status()
            if status:
                return (f"<b>Puzzle Status</b>\n{status}", None)
        except Exception:
            pass
    return ("No puzzle status available.", None)


# ================================================================
# Register All Commands
# ================================================================


def _init_command_registry():
    """Populate the command registry with all known commands."""
    # Status commands
    _register_command("/start", "Welcome + menu", "status", _cmd_start)
    _register_command("/menu", "Show main menu", "status", _cmd_menu)
    _register_command("/status", "Show current status", "status", _cmd_status)
    _register_command("/health", "Endpoint health status", "status", _cmd_health)
    _register_command("/perf", "Performance stats", "status", _cmd_perf)
    _register_command("/help", "Full command reference", "status", _cmd_help)
    _register_command("/memory", "AI memory/learning stats", "status", _cmd_memory)
    _register_command("/vault", "Vault summary", "status", _cmd_vault)
    _register_command("/terminals", "List all terminals", "status", _cmd_terminals)

    # Control commands
    _register_command("/start_all", "Start all terminals", "control", _cmd_start_all)
    _register_command("/stop_all", "Stop all terminals", "control", _cmd_stop_all)
    _register_command("/pause_all", "Pause all terminals", "control", _cmd_pause_all)
    _register_command("/resume_all", "Resume all terminals", "control", _cmd_resume_all)
    _register_command(
        "/checkpoint", "Force checkpoint save", "control", _cmd_checkpoint
    )
    _register_command("/stop", "Stop scanning", "control", _cmd_stop)
    _register_command("/pause", "Pause all terminals", "control", _cmd_pause)
    _register_command("/resume", "Resume all terminals", "control", _cmd_resume)
    _register_command("/mode", "Change mode", "control", _cmd_mode)
    _register_command("/puzzle", "Puzzle status", "control", _cmd_puzzle)

    # Oracle commands
    _register_command("/sign", "Oracle sign reading", "oracle", _cmd_sign)
    _register_command("/name", "Name reading", "oracle", _cmd_name)
    _register_command("/daily", "Daily insight", "oracle", _cmd_daily)

    # Settings commands
    _register_command(
        "/set", "Change setting (mode|puzzle|chains|sound)", "settings", _cmd_set
    )

    # Export commands
    _register_command("/export", "Export vault or report", "export", _cmd_export)


# Initialize registry at module load
_init_command_registry()


# ================================================================
# Unified Dispatch (4.1)
# ================================================================


def dispatch_command(raw_text, app_controller=None):
    """Unified command dispatch entry point.

    Parses the command and args from raw_text, looks up the handler in the
    command registry, calls the handler, and sends the response via Telegram.

    Parameters
    ----------
    raw_text : str
        Raw command text, e.g. "/sign What does 444 mean?"
    app_controller : object or None
        Optional app controller with methods like get_status(), start_scan(), etc.

    Returns
    -------
    str
        The response text that was sent (or would be sent).
    """
    raw_text = raw_text.strip()

    # Handle callback data (section:action:param format)
    if raw_text and not raw_text.startswith("/") and ":" in raw_text:
        text, buttons = _route_callback(raw_text, app_controller)
        if buttons:
            try:
                send_message_with_buttons(text, buttons)
            except Exception as e:
                logger.debug(f"Failed to send callback response: {e}")
        else:
            try:
                send_message(text)
            except Exception as e:
                logger.debug(f"Failed to send callback response: {e}")
        return text

    parts = raw_text.split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""

    # Look up in registry and call handler
    text, buttons = _dispatch_to_handler(cmd, arg, app_controller)

    # Send response
    if text:
        try:
            if buttons:
                send_message_with_buttons(text, buttons)
            else:
                send_message(text)
        except Exception as e:
            logger.debug(f"Failed to send command response: {e}")

    return text


# ================================================================
# Command Listener (Long-Poll Dispatch) -- preserved with delegation
# ================================================================


def start_command_listener(app_controller):
    """Start a daemon thread that long-polls Telegram for commands.

    Parameters
    ----------
    app_controller : object
        Must have methods: get_status(), start_scan(), stop_scan(),
        get_oracle_reading(sign), get_name_reading(name),
        get_puzzle_status(), change_mode(mode), get_memory_stats(),
        get_perf_stats().
    """

    def _listener_loop():
        backoff = 1  # seconds, exponential backoff on failures

        while True:
            try:
                commands = poll_telegram_commands(timeout=30)

                if commands is not None:
                    # Successful poll -- reset backoff
                    backoff = 1

                for raw_cmd in commands:
                    try:
                        dispatch_command(raw_cmd, app_controller)
                    except Exception as e:
                        logger.debug(f"Command dispatch error for '{raw_cmd}': {e}")

            except Exception as e:
                logger.debug(f"Command listener poll error: {e}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)  # max 5 minutes

    t = threading.Thread(target=_listener_loop, daemon=True)
    t.start()
    logger.info("Telegram command listener started")
    return t


def _dispatch_command(raw_text, app_controller):
    """Legacy dispatch -- delegates to unified dispatch_command.

    Preserved for backward compatibility.
    """
    dispatch_command(raw_text, app_controller)


def process_telegram_command(command):
    """Dispatch a Telegram command and return a response string.

    This is a standalone dispatcher that doesn't require an app_controller,
    pulling data directly from engines. Returns a non-empty response string.

    Delegates to the unified dispatch_command (which uses the registry).
    """
    return dispatch_command(command, app_controller=None)


# ================================================================
# Sound Alert (preserved from V2)
# ================================================================


def play_alert_sound():
    """Play an alert sound cross-platform. Fails silently."""
    import platform
    import subprocess

    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(
                ["afplay", "/System/Library/Sounds/Glass.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Linux":
            subprocess.Popen(
                ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Windows":
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        else:
            print("\a", end="", flush=True)
    except Exception:
        print("\a", end="", flush=True)
