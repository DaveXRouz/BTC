"""Daily auto-insight command handlers for the NPS Telegram bot.

Commands: /daily_on, /daily_off, /daily_time, /daily_status
"""

import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from .. import client, config
from ..rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# Bot-level client for daily preference API calls
_API_BASE = config.API_BASE_URL


async def _api_get_preferences(chat_id: int) -> dict | None:
    """GET /telegram/daily/preferences/{chat_id} via bot service client."""
    http = await client.get_client()
    try:
        resp = await http.get(f"/telegram/daily/preferences/{chat_id}")
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        logger.exception("Failed to get daily preferences for %s", chat_id)
        return None


async def _api_update_preferences(chat_id: int, data: dict) -> dict | None:
    """PUT /telegram/daily/preferences/{chat_id} via bot service client."""
    http = await client.get_client()
    try:
        resp = await http.put(f"/telegram/daily/preferences/{chat_id}", json=data)
        if resp.status_code == 200:
            return resp.json()
        logger.warning("Update preferences failed: %d %s", resp.status_code, resp.text)
        return None
    except Exception:
        logger.exception("Failed to update daily preferences for %s", chat_id)
        return None


def _format_tz(offset_minutes: int) -> str:
    """Format timezone offset minutes as UTC+H:MM or UTC-H:MM."""
    sign = "+" if offset_minutes >= 0 else "-"
    total = abs(offset_minutes)
    hours = total // 60
    mins = total % 60
    if mins:
        return f"UTC{sign}{hours}:{mins:02d}"
    return f"UTC{sign}{hours}"


async def daily_on_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily_on — enable daily insight delivery."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        result = await _api_update_preferences(chat_id, {"daily_enabled": True})
        if result:
            delivery_time = result.get("delivery_time", "08:00")
            tz = _format_tz(result.get("timezone_offset_minutes", 0))
            await update.message.reply_text(
                f"Daily insights enabled! You'll receive a reading every day "
                f"at {delivery_time} ({tz}).\n\n"
                f"Tip: Use /daily_time HH:MM to change the delivery time."
            )
        else:
            await update.message.reply_text(
                "Could not enable daily insights. Try again later."
            )
    except Exception:
        logger.exception("Error in daily_on_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def daily_off_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /daily_off — disable daily insight delivery."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        result = await _api_update_preferences(chat_id, {"daily_enabled": False})
        if result:
            await update.message.reply_text(
                "Daily insights disabled. Use /daily_on to re-enable anytime."
            )
        else:
            await update.message.reply_text(
                "Could not disable daily insights. Try again later."
            )
    except Exception:
        logger.exception("Error in daily_off_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def daily_time_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /daily_time HH:MM — set preferred delivery time."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id
    args = context.args or []

    if not args:
        await update.message.reply_text(
            "Usage: /daily_time HH:MM (24-hour format)\nExample: /daily_time 08:30"
        )
        return

    time_str = args[0]
    if not _TIME_PATTERN.match(time_str):
        await update.message.reply_text(
            "Invalid time format. Use HH:MM (24-hour format).\n"
            "Example: /daily_time 08:30"
        )
        return

    try:
        result = await _api_update_preferences(chat_id, {"delivery_time": time_str})
        if result:
            await update.message.reply_text(f"Delivery time updated to {time_str}.")
        else:
            await update.message.reply_text(
                "Could not update delivery time. Try again later."
            )
    except Exception:
        logger.exception("Error in daily_time_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def daily_status_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /daily_status — show current daily settings."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        prefs = await _api_get_preferences(chat_id)
        if not prefs:
            await update.message.reply_text(
                "You haven't set up daily insights yet. Use /daily_on to start."
            )
            return

        enabled = prefs.get("daily_enabled", False)
        status_text = "Enabled" if enabled else "Disabled"
        delivery_time = prefs.get("delivery_time", "08:00")
        tz = _format_tz(prefs.get("timezone_offset_minutes", 0))
        last = prefs.get("last_delivered_date") or "Never"

        await update.message.reply_text(
            f"Daily Insight Settings:\n"
            f"  Status: {status_text}\n"
            f"  Time: {delivery_time}\n"
            f"  Timezone: {tz}\n"
            f"  Last delivered: {last}"
        )
    except Exception:
        logger.exception("Error in daily_status_handler")
        await update.message.reply_text("Something went wrong. Please try again.")
