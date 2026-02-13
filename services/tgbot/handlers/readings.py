"""Reading command handlers for the NPS Telegram bot.

Commands: /time, /name, /question, /daily, /history
Callback queries: reading:*, history:*
"""

import logging
import re
import time
from collections import defaultdict
from datetime import date as date_type

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from .. import client
from ..api_client import NPSAPIClient
from ..formatters import (
    format_daily_insight,
    format_history_list,
    format_name_reading,
    format_question_reading,
    format_time_reading,
    _escape,
)
from ..keyboards import (
    history_keyboard,
    reading_actions_keyboard,
    reading_type_keyboard,
)
from ..progress import update_progress
from ..rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# ─── Per-user reading rate limiter (10/hour) ─────────────────────────────────

_user_readings: dict[int, list[float]] = defaultdict(list)
_READING_RATE_LIMIT = 10
_READING_RATE_WINDOW = 3600  # 1 hour


def check_reading_rate_limit(chat_id: int) -> bool:
    """Returns True if the user is within the reading rate limit (10/hour)."""
    now = time.time()
    _user_readings[chat_id] = [
        t for t in _user_readings[chat_id] if now - t < _READING_RATE_WINDOW
    ]
    if len(_user_readings[chat_id]) >= _READING_RATE_LIMIT:
        return False
    _user_readings[chat_id].append(now)
    return True


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _get_user_api_key(chat_id: int) -> str | None:
    """Retrieve the linked API key for a Telegram chat ID.

    Uses the bot's service client to query the telegram status endpoint,
    which returns user info including the ability to make API calls.
    Returns None if the user hasn't linked their account.
    """
    status_data = await client.get_status(chat_id)
    if status_data and status_data.get("linked"):
        return status_data.get("api_key")
    return None


def build_iso_datetime(time_str: str | None, date_str: str | None) -> str | None:
    """Build ISO 8601 datetime string from time and optional date.

    If time_str is None, returns None (API defaults to now).
    If date_str is None, uses today's date.
    """
    if time_str is None:
        return None
    if date_str is None:
        date_str = date_type.today().isoformat()
    return f"{date_str}T{time_str}:00"


async def _send_error(update: Update, text: str) -> None:
    """Send a plain text error message."""
    if update.message:
        await update.message.reply_text(text)
    elif update.callback_query:
        await update.callback_query.answer(text, show_alert=True)


async def _require_linked(update: Update) -> str | None:
    """Check if user is linked and return API key, or send error. Returns None on failure."""
    chat_id = update.effective_chat.id
    api_key = await _get_user_api_key(chat_id)
    if not api_key:
        await _send_error(update, "Link your account first: /link <api_key>")
        return None
    return api_key


# ─── Command Handlers ────────────────────────────────────────────────────────


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a time-based oracle reading.

    Usage: /time [HH:MM] [YYYY-MM-DD]
    If no time given, uses current time.
    """
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    api_key = await _require_linked(update)
    if not api_key:
        return

    if not check_reading_rate_limit(update.effective_chat.id):
        await update.message.reply_text(
            "You've reached the hourly reading limit (10/hour). Try again later."
        )
        return

    args = context.args or []
    time_str = args[0] if args else None
    date_str = args[1] if len(args) > 1 else None

    # Validate time format
    if time_str and not re.match(r"^\d{2}:\d{2}$", time_str):
        await update.message.reply_text(
            "Invalid time format. Use HH:MM (e.g., /time 14:30)"
        )
        return

    # Validate date format
    if date_str and not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        await update.message.reply_text(
            "Invalid date format. Use YYYY-MM-DD (e.g., /time 14:30 2026-02-10)"
        )
        return

    msg = await update.message.reply_text("\u23f3 Calculating FC60 stamp...")
    api = NPSAPIClient(api_key)
    try:
        await update_progress(msg, 1, 4, "Calculating numerological stamp...")
        iso_dt = build_iso_datetime(time_str, date_str)
        result = await api.create_reading(iso_dt)
        if not result.success:
            await msg.edit_text(f"\u274c {result.error}")
            return
        await update_progress(msg, 2, 4, "Consulting the Oracle...")
        await update_progress(msg, 3, 4, "Formatting reading...")
        text = format_time_reading(result.data)
        keyboard = reading_actions_keyboard(result.data.get("reading_id"))
        await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    except BadRequest as e:
        if "can't parse entities" in str(e).lower():
            # Fallback: send without Markdown
            plain = (
                result.data.get("summary", "Reading complete.")
                if result.success
                else "Error formatting reading."
            )
            await msg.edit_text(str(plain))
        else:
            logger.exception("BadRequest in time_command")
            await msg.edit_text("\u274c Error formatting reading. Try again.")
    except Exception:
        logger.exception("Error in time_command")
        await msg.edit_text("\u274c Something went wrong. Try again later.")
    finally:
        await api.close()


async def name_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a name-based oracle reading.

    Usage: /name [name]
    If no name given, uses profile name.
    """
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    api_key = await _require_linked(update)
    if not api_key:
        return

    if not check_reading_rate_limit(update.effective_chat.id):
        await update.message.reply_text(
            "You've reached the hourly reading limit (10/hour). Try again later."
        )
        return

    args = context.args or []
    name = " ".join(args) if args else None

    # If no name provided, try to get from profile
    if not name:
        profiles = await client.get_profile(update.effective_chat.id)
        if profiles:
            name = profiles[0].get("name")
        if not name:
            await update.message.reply_text(
                "Usage: /name <name>\n"
                "Or create an Oracle profile in the web app to use /name without arguments."
            )
            return

    msg = await update.message.reply_text("\u23f3 Analyzing name...")
    api = NPSAPIClient(api_key)
    try:
        await update_progress(msg, 1, 3, "Analyzing letters...")
        result = await api.create_name_reading(name)
        if not result.success:
            await msg.edit_text(f"\u274c {result.error}")
            return
        await update_progress(msg, 2, 3, "Generating interpretation...")
        text = format_name_reading(result.data)
        keyboard = reading_actions_keyboard(result.data.get("reading_id"))
        await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    except BadRequest as e:
        if "can't parse entities" in str(e).lower():
            await msg.edit_text("Name reading complete. View details in the web app.")
        else:
            logger.exception("BadRequest in name_command")
            await msg.edit_text("\u274c Error formatting reading. Try again.")
    except Exception:
        logger.exception("Error in name_command")
        await msg.edit_text("\u274c Something went wrong. Try again later.")
    finally:
        await api.close()


async def question_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a question-based oracle reading.

    Usage: /question <your question here>
    """
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    api_key = await _require_linked(update)
    if not api_key:
        return

    if not check_reading_rate_limit(update.effective_chat.id):
        await update.message.reply_text(
            "You've reached the hourly reading limit (10/hour). Try again later."
        )
        return

    args = context.args or []
    question_text = " ".join(args) if args else ""

    if not question_text.strip():
        await update.message.reply_text(
            "Usage: /question What does today hold?\n"
            "Provide a question after the command."
        )
        return

    msg = await update.message.reply_text("\u23f3 Consulting the Oracle...")
    api = NPSAPIClient(api_key)
    try:
        await update_progress(msg, 1, 3, "Hashing your question...")
        result = await api.create_question(question_text)
        if not result.success:
            await msg.edit_text(f"\u274c {result.error}")
            return
        await update_progress(msg, 2, 3, "Interpreting the signs...")
        text = format_question_reading(result.data)
        keyboard = reading_actions_keyboard(result.data.get("reading_id"))
        await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    except BadRequest as e:
        if "can't parse entities" in str(e).lower():
            await msg.edit_text(
                "Question reading complete. View details in the web app."
            )
        else:
            logger.exception("BadRequest in question_command")
            await msg.edit_text("\u274c Error formatting reading. Try again.")
    except Exception:
        logger.exception("Error in question_command")
        await msg.edit_text("\u274c Something went wrong. Try again later.")
    finally:
        await api.close()


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get today's daily insight.

    Usage: /daily
    """
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    api_key = await _require_linked(update)
    if not api_key:
        return

    msg = await update.message.reply_text("\U0001f31f Fetching daily insight...")
    api = NPSAPIClient(api_key)
    try:
        result = await api.get_daily()
        if not result.success:
            await msg.edit_text(f"\u274c {result.error}")
            return
        text = format_daily_insight(result.data)
        await msg.edit_text(text, parse_mode="MarkdownV2")
    except BadRequest as e:
        if "can't parse entities" in str(e).lower():
            insight = (
                result.data.get("insight", "Daily insight ready.")
                if result.success
                else "Error"
            )
            await msg.edit_text(str(insight))
        else:
            logger.exception("BadRequest in daily_command")
            await msg.edit_text("\u274c Error formatting daily insight. Try again.")
    except Exception:
        logger.exception("Error in daily_command")
        await msg.edit_text("\u274c Something went wrong. Try again later.")
    finally:
        await api.close()


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show reading history.

    Usage: /history
    """
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    api_key = await _require_linked(update)
    if not api_key:
        return

    msg = await update.message.reply_text("\U0001f4dc Fetching history...")
    api = NPSAPIClient(api_key)
    try:
        result = await api.list_readings(limit=5, offset=0)
        if not result.success:
            await msg.edit_text(f"\u274c {result.error}")
            return
        readings = result.data.get("readings", [])
        total = result.data.get("total", 0)
        text = format_history_list(readings, total)
        has_more = total > 5
        keyboard = history_keyboard(readings, has_more, current_offset=0)
        await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    except BadRequest as e:
        if "can't parse entities" in str(e).lower():
            await msg.edit_text("Reading history loaded. View details in the web app.")
        else:
            logger.exception("BadRequest in history_command")
            await msg.edit_text("\u274c Error formatting history. Try again.")
    except Exception:
        logger.exception("Error in history_command")
        await msg.edit_text("\u274c Something went wrong. Try again later.")
    finally:
        await api.close()


# ─── Callback Query Handler ──────────────────────────────────────────────────


async def reading_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle inline keyboard callbacks for reading:* and history:* patterns."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data or ""
    chat_id = update.effective_chat.id

    api_key = await _get_user_api_key(chat_id)
    if not api_key:
        await query.edit_message_text("Link your account first: /link <api_key>")
        return

    parts = data.split(":")
    if len(parts) < 2:
        return

    category = parts[0]  # "reading" or "history"
    action = parts[1]
    value = parts[2] if len(parts) > 2 else ""

    api = NPSAPIClient(api_key)
    try:
        if category == "reading":
            await _handle_reading_callback(query, api, action, value)
        elif category == "history":
            await _handle_history_callback(query, api, action, value)
    except Exception:
        logger.exception("Error in callback handler for %s", data)
        try:
            await query.edit_message_text("\u274c Something went wrong. Try again.")
        except BadRequest:
            pass
    finally:
        await api.close()


async def _handle_reading_callback(query, api, action, value):
    """Handle reading:* callback queries."""
    if action == "details" and value:
        reading_id = int(value)
        result = await api.get_reading(reading_id)
        if result.success:
            reading_result = result.data.get("reading_result", {})
            sign_type = result.data.get("sign_type", "reading")
            if sign_type == "question":
                text = format_question_reading(reading_result)
            elif sign_type == "name":
                text = format_name_reading(reading_result)
            else:
                text = format_time_reading(reading_result)
            try:
                await query.edit_message_text(
                    text,
                    parse_mode="MarkdownV2",
                    reply_markup=reading_actions_keyboard(reading_id),
                )
            except BadRequest:
                await query.edit_message_text("Reading details loaded.")
        else:
            await query.edit_message_text(f"\u274c {result.error}")

    elif action == "rate" and value:
        # Stub: log the rating intent
        logger.info("User wants to rate reading %s", value)
        await query.edit_message_text(
            _escape("Rating feature coming soon!"),
            parse_mode="MarkdownV2",
        )

    elif action == "share" and value:
        reading_id = int(value)
        result = await api.get_reading(reading_id)
        if result.success:
            sign_type = result.data.get("sign_type", "reading")
            sign_value = result.data.get("sign_value", "")
            ai = result.data.get("ai_interpretation", "No interpretation available.")
            share_text = f"NPS Oracle {sign_type.title()} Reading: {sign_value}\n\n{ai}"
            await query.edit_message_text(
                _escape(share_text[:_SHARE_TEXT_LIMIT]),
                parse_mode="MarkdownV2",
            )
        else:
            await query.edit_message_text(f"\u274c {result.error}")

    elif action == "new":
        await query.edit_message_text(
            _escape("Choose a reading type:"),
            parse_mode="MarkdownV2",
            reply_markup=reading_type_keyboard(),
        )

    elif action == "type" and value:
        # User chose a reading type from the keyboard
        type_hints = {
            "time": "Use: /time [HH:MM] [YYYY-MM-DD]",
            "question": "Use: /question <your question>",
            "name": "Use: /name <name>",
            "daily": "Use: /daily",
        }
        hint = type_hints.get(value, "Unknown reading type.")
        await query.edit_message_text(_escape(hint), parse_mode="MarkdownV2")


async def _handle_history_callback(query, api, action, value):
    """Handle history:* callback queries."""
    if action == "view" and value:
        reading_id = int(value)
        result = await api.get_reading(reading_id)
        if result.success:
            reading_result = result.data.get("reading_result", {})
            sign_type = result.data.get("sign_type", "reading")
            if sign_type == "question":
                text = format_question_reading(reading_result)
            elif sign_type == "name":
                text = format_name_reading(reading_result)
            else:
                text = format_time_reading(reading_result)
            try:
                await query.edit_message_text(
                    text,
                    parse_mode="MarkdownV2",
                    reply_markup=reading_actions_keyboard(reading_id),
                )
            except BadRequest:
                await query.edit_message_text("Reading loaded.")
        else:
            await query.edit_message_text(f"\u274c {result.error}")

    elif action == "more" and value:
        offset = int(value)
        result = await api.list_readings(limit=5, offset=offset)
        if result.success:
            readings = result.data.get("readings", [])
            total = result.data.get("total", 0)
            text = format_history_list(readings, total)
            has_more = offset + 5 < total
            keyboard = history_keyboard(readings, has_more, current_offset=offset)
            try:
                await query.edit_message_text(
                    text, parse_mode="MarkdownV2", reply_markup=keyboard
                )
            except BadRequest:
                await query.edit_message_text("History loaded.")
        else:
            await query.edit_message_text(f"\u274c {result.error}")


# Share text limit (under Telegram's 4096 char limit)
_SHARE_TEXT_LIMIT = 3800
