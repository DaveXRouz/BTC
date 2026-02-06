"""
Telegram notification system for NPS.

Sends alerts for puzzle solves, balance discoveries, errors, and daily status.
All functions fail silently when unconfigured or on network error.
"""

import json
import threading
import time
import logging
import ssl
import urllib.request
import urllib.error

# SSL context — macOS Python often lacks system CA certs
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
}

_lock = threading.Lock()
_last_send_time = 0.0
_error_count = 0
_error_count_reset_time = 0.0
_MAX_ERRORS_PER_HOUR = 10
_MIN_SEND_INTERVAL = 2.0
_MAX_MESSAGE_LENGTH = 4096
_last_update_id = 0


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
            return True
    except Exception as e:
        with _lock:
            _error_count += 1
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
            return True
    except Exception as e:
        logger.debug(f"Telegram send_with_buttons failed: {e}")
        return False


def _send_with_buttons_async(text, buttons=None, parse_mode="HTML"):
    """Send message with buttons in a daemon thread (fire-and-forget)."""

    def _do_send():
        send_message_with_buttons(text, buttons, parse_mode)

    threading.Thread(target=_do_send, daemon=True).start()


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
                    commands.append(text.split()[0])
    except Exception as e:
        logger.debug(f"Telegram poll failed: {e}")

    return commands


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


# ════════════════════════════════════════════════════════════
# Command Listener (Long-Poll Dispatch)
# ════════════════════════════════════════════════════════════


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
                    # Successful poll — reset backoff
                    backoff = 1

                for raw_cmd in commands:
                    try:
                        _dispatch_command(raw_cmd, app_controller)
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
    """Parse and dispatch a single command string to the app controller."""
    parts = raw_text.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    response = None

    try:
        if cmd == "/start":
            app_controller.start_scan()
            response = "Scanning started."

        elif cmd == "/stop":
            app_controller.stop_scan()
            response = "Scanning stopped."

        elif cmd == "/status":
            status = app_controller.get_status()
            response = (
                f"<b>Status</b>\n<pre>{status}</pre>"
                if status
                else "No status available."
            )

        elif cmd == "/sign":
            if not arg:
                response = "Usage: /sign <zodiac sign or text>"
            else:
                reading = app_controller.get_oracle_reading(arg)
                response = (
                    f"<b>Oracle Reading: {arg}</b>\n{reading}"
                    if reading
                    else "No reading available."
                )

        elif cmd == "/name":
            if not arg:
                response = "Usage: /name <name>"
            else:
                reading = app_controller.get_name_reading(arg)
                response = (
                    f"<b>Name Reading: {arg}</b>\n{reading}"
                    if reading
                    else "No reading available."
                )

        elif cmd == "/puzzle":
            status = app_controller.get_puzzle_status()
            response = (
                f"<b>Puzzle Status</b>\n{status}"
                if status
                else "No puzzle status available."
            )

        elif cmd == "/mode":
            if not arg:
                response = "Usage: /mode <mode_name>"
            else:
                result = app_controller.change_mode(arg)
                response = (
                    f"Mode changed to: {arg}"
                    if result
                    else f"Failed to change mode to: {arg}"
                )

        elif cmd == "/memory":
            stats = app_controller.get_memory_stats()
            response = (
                f"<b>Memory Stats</b>\n<pre>{stats}</pre>"
                if stats
                else "No memory stats available."
            )

        elif cmd == "/perf":
            stats = app_controller.get_perf_stats()
            response = (
                f"<b>Performance Stats</b>\n<pre>{stats}</pre>"
                if stats
                else "No perf stats available."
            )

        elif cmd == "/help":
            lines = ["<b>Available Commands</b>\n"]
            for c, desc in COMMANDS.items():
                lines.append(f"  {c} — {desc}")
            response = "\n".join(lines)

        else:
            response = f"Unknown command: {cmd}\nUse /help for available commands."

    except Exception as e:
        logger.debug(f"Error handling command {cmd}: {e}")
        response = f"Error processing {cmd}: {e}"

    if response:
        try:
            send_message(response)
        except Exception as e:
            logger.debug(f"Failed to send command response: {e}")


# ════════════════════════════════════════════════════════════
# Multi-Chain Balance Found Notification
# ════════════════════════════════════════════════════════════


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


def process_telegram_command(command):
    """Dispatch a Telegram command and return a response string.

    This is a standalone dispatcher that doesn't require an app_controller,
    pulling data directly from engines. Returns a non-empty response string.
    """
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""

    try:
        if cmd == "/status":
            try:
                from engines.terminal_manager import get_all_stats, get_active_count

                active = get_active_count()
                stats = get_all_stats()
                total_keys = sum(s.get("keys_tested", 0) for s in stats.values())
                total_speed = sum(s.get("speed", 0) for s in stats.values())
                return (
                    f"<b>NPS Status</b>\n"
                    f"Active terminals: {active}\n"
                    f"Total keys: {total_keys:,}\n"
                    f"Speed: {total_speed:,.0f}/s"
                )
            except Exception:
                return "<b>NPS Status</b>\nNo active terminals."

        elif cmd == "/pause":
            try:
                from engines.terminal_manager import stop_all

                count = stop_all()
                return f"<b>Paused {count} terminal(s).</b>"
            except Exception:
                return "Pause failed — no terminal manager available."

        elif cmd == "/resume":
            try:
                from engines.terminal_manager import start_all

                count = start_all()
                return f"<b>Resumed {count} terminal(s).</b>"
            except Exception:
                return "Resume failed — no terminal manager available."

        elif cmd == "/stop":
            try:
                from engines.terminal_manager import stop_all

                count = stop_all()
                return f"<b>Stopped {count} terminal(s).</b>"
            except Exception:
                return "Stop failed — no terminal manager available."

        elif cmd == "/start":
            try:
                from engines.terminal_manager import start_all

                count = start_all()
                return f"<b>Started {count} terminal(s).</b>"
            except Exception:
                return "Start failed — no terminal manager available."

        elif cmd == "/sign":
            if not arg:
                return "Usage: /sign <question or sign text>"
            try:
                from engines.oracle import question_sign

                result = question_sign(arg)
                reading = result.get("reading", "No reading")
                advice = result.get("advice", "")
                return f"<b>Oracle: {arg}</b>\n{reading}\n{advice}"
            except Exception as e:
                return f"Oracle error: {e}"

        elif cmd == "/name":
            if not arg:
                return "Usage: /name <name>"
            try:
                from engines.oracle import read_name

                result = read_name(arg)
                expr = result.get("expression", "?")
                soul = result.get("soul_urge", "?")
                return f"<b>Name: {arg}</b>\nExpression: {expr}\nSoul Urge: {soul}"
            except Exception as e:
                return f"Name error: {e}"

        elif cmd == "/memory":
            try:
                from engines.learner import get_level, get_insights

                level = get_level()
                insights = get_insights(limit=3)
                insight_text = (
                    "\n".join(f"  - {i}" for i in insights)
                    if insights
                    else "  (none yet)"
                )
                return (
                    f"<b>AI Brain</b>\n"
                    f"Level: {level.get('level', 1)} — {level.get('name', 'Novice')}\n"
                    f"XP: {level.get('xp', 0)}\n"
                    f"Recent Insights:\n{insight_text}"
                )
            except Exception:
                try:
                    from engines.memory import get_summary

                    s = get_summary()
                    return (
                        f"<b>Memory Stats</b>\n"
                        f"Sessions: {s.get('total_sessions', 0)}\n"
                        f"Keys: {s.get('total_keys', 0):,}"
                    )
                except Exception:
                    return "Memory stats not available."

        elif cmd == "/vault":
            try:
                from engines.vault import get_summary

                s = get_summary()
                return (
                    f"<b>Vault Summary</b>\n"
                    f"Total findings: {s.get('total', 0)}\n"
                    f"With balance: {s.get('with_balance', 0)}\n"
                    f"Vault size: {s.get('vault_size', 'unknown')}"
                )
            except Exception:
                return "Vault not available."

        elif cmd == "/perf":
            try:
                from engines.perf import perf

                summary = perf.summary()
                if summary:
                    lines = ["<b>Performance</b>"]
                    for name, stats in summary.items():
                        lines.append(
                            f"  {name}: avg={stats['avg']*1000:.1f}ms n={stats['count']}"
                        )
                    return "\n".join(lines)
                return "No performance data yet."
            except Exception:
                return "Performance stats not available."

        elif cmd == "/terminals":
            try:
                from engines.terminal_manager import list_terminals, get_terminal_stats

                terminals = list_terminals()
                if not terminals:
                    return "<b>Terminals</b>\nNo terminals created."
                lines = ["<b>Terminals</b>"]
                for tid in terminals:
                    stats = get_terminal_stats(tid)
                    status = stats.get("status", "unknown")
                    keys = stats.get("keys_tested", 0)
                    lines.append(f"  {tid}: {status} — {keys:,} keys")
                return "\n".join(lines)
            except Exception:
                return "Terminal manager not available."

        elif cmd == "/checkpoint":
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
                return f"<b>Checkpoint saved for {saved} terminal(s).</b>"
            except Exception:
                return "Checkpoint save failed."

        elif cmd == "/help":
            lines = ["<b>Available Commands</b>"]
            for c, desc in COMMANDS.items():
                lines.append(f"  {c} — {desc}")
            return "\n".join(lines)

        else:
            return f"Unknown command: {cmd}\nUse /help for available commands."

    except Exception as e:
        return f"Error processing {cmd}: {e}"


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
