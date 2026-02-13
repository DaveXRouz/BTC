"""Admin command handlers for the NPS Telegram bot.

Commands: /admin_stats, /admin_users, /admin_broadcast
All commands require admin role verified via account-linking.
"""

import asyncio
import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .. import client
from ..rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

_USERS_PER_PAGE = 10
_BROADCAST_RATE_LIMIT = 30  # msgs/sec per Telegram API


async def _is_admin(chat_id: int) -> bool:
    """Check if the Telegram chat_id is linked to an admin-role API account."""
    http = await client.get_client()
    try:
        resp = await http.get(f"/telegram/status/{chat_id}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("linked", False) and data.get("role") == "admin"
        return False
    except Exception:
        logger.exception("Failed to check admin status for chat %s", chat_id)
        return False


async def _log_audit(action: str, chat_id: int, details: dict | None = None) -> None:
    """Log an admin action to oracle_audit_log via API."""
    http = await client.get_client()
    try:
        await http.post(
            "/telegram/admin/audit",
            json={
                "action": action,
                "resource_type": "system",
                "success": True,
                "details": json.dumps({"chat_id": chat_id, **(details or {})}),
            },
        )
    except Exception:
        logger.exception("Failed to log audit action %s", action)


def _format_uptime(seconds: float) -> str:
    """Format uptime seconds as Xd Xh Xm."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)


def _format_relative_time(iso_str: str) -> str:
    """Format an ISO datetime string as relative time (e.g., '2 min ago')."""
    if not iso_str:
        return "N/A"
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = (now - dt).total_seconds()
        if diff < 60:
            return f"{int(diff)}s ago"
        if diff < 3600:
            return f"{int(diff // 60)} min ago"
        if diff < 86400:
            return f"{int(diff // 3600)}h ago"
        return f"{int(diff // 86400)}d ago"
    except (ValueError, TypeError):
        return iso_str[:19]


# ─── /admin_stats ────────────────────────────────────────────────────────────


async def admin_stats_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /admin_stats — show system statistics."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        if not await _is_admin(chat_id):
            await update.message.reply_text(
                "\u26d4 Access denied. Admin role required."
            )
            return

        http = await client.get_client()
        resp = await http.get("/telegram/admin/stats")

        if resp.status_code != 200:
            await update.message.reply_text(
                "\u26a0\ufe0f Could not fetch stats. API may be down."
            )
            return

        stats = resp.json()
        uptime = _format_uptime(stats.get("uptime_seconds", 0))
        last_reading = _format_relative_time(stats.get("last_reading_at", ""))

        text = (
            "\U0001f4ca <b>System Stats</b>\n\n"
            f"\U0001f465 Users: {stats.get('total_users', 0):,}\n"
            f"\U0001f4d6 Readings today: {stats.get('readings_today', 0):,} "
            f"(total: {stats.get('readings_total', 0):,})\n"
            f"\u26a0\ufe0f Errors (24h): {stats.get('error_count_24h', 0)}\n"
            f"\U0001f5a5 Active sessions: {stats.get('active_sessions', 0)}\n"
            f"\u23f1 Uptime: {uptime}\n"
            f"\U0001f4be DB size: {stats.get('db_size_mb', 0):.1f} MB\n"
            f"\U0001f4c5 Last reading: {last_reading}"
        )
        await update.message.reply_text(text, parse_mode="HTML")

        await _log_audit("telegram_admin_stats", chat_id)
    except Exception:
        logger.exception("Error in admin_stats_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


# ─── /admin_users ────────────────────────────────────────────────────────────


async def _send_users_page(
    update_or_query, chat_id: int, page: int, *, is_callback: bool = False
) -> None:
    """Fetch and send a page of users.

    Args:
        update_or_query: Update (command) or CallbackQuery (pagination).
        chat_id: The chat to send to.
        page: Zero-based page number.
        is_callback: True when called from a callback query (edit existing message).
    """
    http = await client.get_client()
    offset = page * _USERS_PER_PAGE
    resp = await http.get(
        "/telegram/admin/users",
        params={"limit": _USERS_PER_PAGE, "offset": offset},
    )

    if resp.status_code != 200:
        text = "\u26a0\ufe0f Could not fetch users. API may be down."
        if is_callback:
            await update_or_query.edit_message_text(text)
        else:
            await update_or_query.message.reply_text(text)
        return

    data = resp.json()
    users = data.get("users", [])
    total = data.get("total", 0)

    if not users:
        text = "No users found."
        if is_callback:
            await update_or_query.edit_message_text(text)
        else:
            await update_or_query.message.reply_text(text)
        return

    lines = [f"<b>Users</b> (page {page + 1}, {total} total)\n"]
    for i, u in enumerate(users, start=offset + 1):
        name = u.get("name", "Unknown")
        joined = (u.get("created_at") or "")[:10]
        uid = u.get("id", "?")
        lines.append(f"#{uid} \u2014 {name} \u2014 Joined: {joined}")

    text = "\n".join(lines)

    # Pagination buttons
    buttons = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "\u25c0 Prev", callback_data=f"admin_users:page:{page - 1}"
            )
        )
    if offset + _USERS_PER_PAGE < total:
        buttons.append(
            InlineKeyboardButton(
                "Next \u25b6", callback_data=f"admin_users:page:{page + 1}"
            )
        )

    markup = InlineKeyboardMarkup([buttons]) if buttons else None

    if is_callback:
        await update_or_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=markup
        )
    else:
        await update_or_query.message.reply_text(
            text, parse_mode="HTML", reply_markup=markup
        )


async def admin_users_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /admin_users — list users with pagination."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        if not await _is_admin(chat_id):
            await update.message.reply_text(
                "\u26d4 Access denied. Admin role required."
            )
            return

        await _send_users_page(update, chat_id, page=0)
        await _log_audit("telegram_admin_users", chat_id)
    except Exception:
        logger.exception("Error in admin_users_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def admin_users_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle pagination callback for /admin_users."""
    query = update.callback_query
    await query.answer()

    try:
        # Parse page number from callback data: "admin_users:page:N"
        parts = query.data.split(":")
        page = int(parts[2]) if len(parts) >= 3 else 0
        chat_id = query.message.chat_id

        if not await _is_admin(chat_id):
            await query.edit_message_text("\u26d4 Access denied. Admin role required.")
            return

        await _send_users_page(query, chat_id, page, is_callback=True)
    except Exception:
        logger.exception("Error in admin_users_callback")


# ─── /admin_broadcast ────────────────────────────────────────────────────────


async def admin_broadcast_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /admin_broadcast <message> — broadcast to all linked users."""
    if not rate_limiter.is_allowed(update.effective_chat.id):
        await update.message.reply_text(
            "Slow down! Please wait a moment before sending more commands."
        )
        return

    chat_id = update.effective_chat.id

    try:
        if not await _is_admin(chat_id):
            await update.message.reply_text(
                "\u26d4 Access denied. Admin role required."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "Usage: /admin_broadcast <message>\n"
                "Example: /admin_broadcast Hello everyone!"
            )
            return

        message = " ".join(context.args)

        # Get linked user count
        http = await client.get_client()
        resp = await http.get("/telegram/admin/linked_chats")
        linked_chats: list[int] = []
        if resp.status_code == 200:
            linked_chats = resp.json().get("chat_ids", [])

        if not linked_chats:
            await update.message.reply_text("No linked users to broadcast to.")
            return

        # Store broadcast message in context for callback
        context.user_data["broadcast_message"] = message
        context.user_data["broadcast_chats"] = linked_chats

        text = (
            "\U0001f4e2 <b>Broadcast Preview</b>\n\n"
            f"&gt; {message}\n\n"
            f"This will be sent to {len(linked_chats)} linked user(s).\n"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "\u2705 Send", callback_data="admin_broadcast:send"
                    ),
                    InlineKeyboardButton(
                        "\u274c Cancel", callback_data="admin_broadcast:cancel"
                    ),
                ]
            ]
        )

        await update.message.reply_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        logger.exception("Error in admin_broadcast_handler")
        await update.message.reply_text("Something went wrong. Please try again.")


async def admin_broadcast_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle Send/Cancel callbacks for broadcast."""
    query = update.callback_query
    await query.answer()

    try:
        chat_id = query.message.chat_id
        action = query.data.split(":")[1] if ":" in query.data else ""

        if not await _is_admin(chat_id):
            await query.edit_message_text("\u26d4 Access denied. Admin role required.")
            return

        if action == "cancel":
            await query.edit_message_text("Broadcast cancelled.")
            await _log_audit(
                "telegram_admin_broadcast_cancelled",
                chat_id,
                {"reason": "user_cancelled"},
            )
            return

        if action == "send":
            message = context.user_data.get("broadcast_message", "")
            linked_chats = context.user_data.get("broadcast_chats", [])

            if not message or not linked_chats:
                await query.edit_message_text(
                    "Broadcast data expired. Please use /admin_broadcast again."
                )
                return

            await query.edit_message_text(
                f"\U0001f4e1 Broadcasting to {len(linked_chats)} user(s)..."
            )

            sent = 0
            failed = 0
            for i, target_chat_id in enumerate(linked_chats):
                try:
                    await context.bot.send_message(
                        chat_id=target_chat_id,
                        text=f"\U0001f4e2 <b>Broadcast from NPS</b>\n\n{message}",
                        parse_mode="HTML",
                    )
                    sent += 1
                except TelegramError as exc:
                    logger.warning(
                        "Broadcast failed for chat %s: %s", target_chat_id, exc
                    )
                    failed += 1

                # Rate limit: 30 msgs/sec
                if (i + 1) % _BROADCAST_RATE_LIMIT == 0:
                    await asyncio.sleep(1.0)

            await query.edit_message_text(
                f"\u2705 Broadcast complete: {sent} sent, {failed} failed "
                f"(of {len(linked_chats)} total)."
            )

            await _log_audit(
                "telegram_admin_broadcast",
                chat_id,
                {"sent": sent, "failed": failed, "total": len(linked_chats)},
            )

            # Cleanup
            context.user_data.pop("broadcast_message", None)
            context.user_data.pop("broadcast_chats", None)
    except Exception:
        logger.exception("Error in admin_broadcast_callback")


# ─── Registration ────────────────────────────────────────────────────────────


def register_admin_handlers(app) -> None:
    """Register admin command and callback handlers on the Application."""
    app.add_handler(CommandHandler("admin_stats", admin_stats_handler))
    app.add_handler(CommandHandler("admin_users", admin_users_handler))
    app.add_handler(CommandHandler("admin_broadcast", admin_broadcast_handler))
    app.add_handler(
        CallbackQueryHandler(admin_users_callback, pattern=r"^admin_users:page:")
    )
    app.add_handler(
        CallbackQueryHandler(admin_broadcast_callback, pattern=r"^admin_broadcast:")
    )
