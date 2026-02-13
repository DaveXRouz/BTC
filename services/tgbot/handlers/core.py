"""Core command handlers for the NPS Telegram bot."""

import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from .. import client
from ..rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

_API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9\-_]{20,100}$")


async def _check_rate_limit(update: Update) -> bool:
    """Check rate limit. Returns True if allowed, False if rate-limited."""
    chat_id = update.effective_chat.id
    if not rate_limiter.is_allowed(chat_id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return False
    return True


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command — welcome message."""
    if not await _check_rate_limit(update):
        return

    try:
        text = (
            "Welcome to *NPS Oracle Bot*\\!\n\n"
            "Link your NPS account to get Oracle readings, "
            "daily insights, and notifications right here in Telegram\\.\n\n"
            "*Quick Start:*\n"
            "1\\. Go to NPS web app → Settings → API Keys\n"
            "2\\. Create an API key\n"
            "3\\. Send: `/link YOUR_API_KEY`\n\n"
            "Use /help for all available commands\\."
        )
        await update.message.reply_text(text, parse_mode="MarkdownV2")
    except Exception:
        logger.exception("Error in start_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /link <api_key> — account linking."""
    if not await _check_rate_limit(update):
        return

    chat_id = update.effective_chat.id
    username = update.effective_user.username if update.effective_user else None

    # Delete the message containing the API key for security
    try:
        await context.bot.delete_message(
            chat_id=chat_id, message_id=update.message.message_id
        )
    except Exception:
        logger.debug("Could not delete /link message (bot may lack permission)")

    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Usage: /link <api_key>\n\n"
                "Get your API key from NPS web app → Settings → API Keys."
            ),
        )
        return

    api_key = context.args[0]

    # Validate API key format before sending to API
    if not _API_KEY_PATTERN.match(api_key):
        await context.bot.send_message(
            chat_id=chat_id,
            text="Invalid API key format. Keys are 20-100 alphanumeric characters.",
        )
        return

    try:
        result = await client.link_account(chat_id, username, api_key)

        if result:
            nps_username = result.get("username", "user")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Account linked! Welcome, {nps_username}.\nUse /help to see available commands.",
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Invalid or expired API key. Generate a new one at NPS → Settings → API Keys.",
            )
    except Exception:
        logger.exception("Error in link_handler")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Something went wrong. Please try again.",
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command — list all available commands."""
    if not await _check_rate_limit(update):
        return

    try:
        text = (
            "NPS Oracle Bot — Commands\n\n"
            "Account:\n"
            "  /start — Welcome message\n"
            "  /link <api_key> — Link your NPS account\n"
            "  /status — Check account status\n"
            "  /help — Show this help\n\n"
            "Oracle:\n"
            "  /profile — View your Oracle profiles\n"
            "  /time [HH:MM] [YYYY-MM-DD] — Time reading\n"
            "  /name [name] — Name reading\n"
            "  /question <text> — Question reading\n"
            "  /daily — Daily insight\n"
            "  /history — Reading history"
        )
        await update.message.reply_text(text)
    except Exception:
        logger.exception("Error in help_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command — show account status."""
    if not await _check_rate_limit(update):
        return

    chat_id = update.effective_chat.id

    try:
        status_data = await client.get_status(chat_id)

        if status_data and status_data.get("linked"):
            text = (
                f"Account Status:\n"
                f"  Username: {status_data.get('username', 'N/A')}\n"
                f"  Role: {status_data.get('role', 'N/A')}\n"
                f"  Oracle Profiles: {status_data.get('oracle_profile_count', 0)}\n"
                f"  Readings: {status_data.get('reading_count', 0)}"
            )
            await update.message.reply_text(text)
        else:
            await update.message.reply_text(
                "Not linked. Use /link <api_key> to connect your NPS account."
            )
    except Exception:
        logger.exception("Error in status_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /profile command — show Oracle profiles."""
    if not await _check_rate_limit(update):
        return

    chat_id = update.effective_chat.id

    try:
        # Check if linked first
        status_data = await client.get_status(chat_id)
        if not status_data or not status_data.get("linked"):
            await update.message.reply_text("Not linked. Use /link <api_key> first.")
            return

        profiles = await client.get_profile(chat_id)

        if not profiles:
            await update.message.reply_text(
                "No Oracle profiles found. Create one in the NPS web app."
            )
            return

        lines = ["Your Oracle Profiles:\n"]
        for p in profiles:
            name = p.get("name", "Unknown")
            birthday = p.get("birthday", "N/A")
            lines.append(f"  - {name} (born {birthday})")

        await update.message.reply_text("\n".join(lines))
    except Exception:
        logger.exception("Error in profile_handler")
        await update.message.reply_text("Something went wrong. Please try again.")
