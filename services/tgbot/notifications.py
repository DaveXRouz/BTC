"""System notification service — dispatches alerts to admin Telegram channel.

Sends structured alerts for API errors, high error rates, new user registration,
service startup/shutdown, and reading milestones. Includes cooldown system
to prevent alert spam.
"""

import logging
import time
from datetime import datetime, timezone

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# Cooldown windows in seconds
_COOLDOWN_API_ERROR = 300  # 5 minutes per endpoint
_COOLDOWN_HIGH_ERROR_RATE = 900  # 15 minutes


def get_admin_chat_id() -> str:
    """Return admin chat ID, falling back to main chat ID.

    Reads from environment: NPS_ADMIN_CHAT_ID → NPS_CHAT_ID → "".
    """
    import os

    admin_id = os.environ.get("NPS_ADMIN_CHAT_ID", "")
    if admin_id:
        return admin_id
    return os.environ.get("NPS_CHAT_ID", "")


class SystemNotifier:
    """Sends system notifications to the admin Telegram channel.

    Includes cooldown tracking to prevent alert spam and graceful degradation
    when admin chat ID or bot token is not configured.
    """

    def __init__(self, bot: Bot, admin_chat_id: str) -> None:
        self._bot = bot
        self._admin_chat_id = admin_chat_id
        self._cooldowns: dict[str, float] = {}

    def _is_cooled_down(self, key: str, window: float) -> bool:
        """Check if a cooldown key has expired. Returns True if we can send."""
        now = time.monotonic()
        last = self._cooldowns.get(key)
        if last is None or (now - last) >= window:
            self._cooldowns[key] = now
            return True
        return False

    async def _send(self, text: str) -> bool:
        """Send a message to the admin channel. Returns True on success."""
        if not self._admin_chat_id:
            logger.warning("No admin chat ID configured, skipping notification")
            return False

        try:
            await self._bot.send_message(
                chat_id=self._admin_chat_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except TelegramError as exc:
            logger.error("Failed to send admin notification: %s", exc)
            return False

    async def notify_api_error(
        self, endpoint: str, status_code: int, detail: str
    ) -> None:
        """Alert on API error (429, 500, 503). Cooldown: 5 min per endpoint."""
        key = f"api_error:{endpoint}"
        if not self._is_cooled_down(key, _COOLDOWN_API_ERROR):
            return

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            "\U0001f6a8 <b>API Error</b>\n"
            f"Endpoint: <code>{endpoint}</code>\n"
            f"Status: {status_code}\n"
            f"Detail: {detail}\n"
            f"Time: {now_str}"
        )
        await self._send(text)

    async def notify_high_error_rate(self, rate: float, window_minutes: int) -> None:
        """Alert when error rate exceeds threshold. Cooldown: 15 min."""
        key = "high_error_rate"
        if not self._is_cooled_down(key, _COOLDOWN_HIGH_ERROR_RATE):
            return

        text = (
            "\u26a0\ufe0f <b>High Error Rate Alert</b>\n"
            f"Rate: {rate:.1f}% (threshold: 5%)\n"
            f"Window: last {window_minutes} minutes\n"
            "Action: Check API logs"
        )
        await self._send(text)

    async def notify_new_user(self, user_name: str, user_id: str) -> None:
        """Alert on new Oracle user registration. No cooldown."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            "\U0001f464 <b>New User Registered</b>\n"
            f"Name: {user_name}\n"
            f"ID: #{user_id}\n"
            f"Time: {now_str}"
        )
        await self._send(text)

    async def notify_startup(self, service: str, version: str) -> None:
        """Alert on service startup. No cooldown."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            "\U0001f7e2 <b>Service Started</b>\n"
            f"Service: {service}\n"
            f"Version: {version}\n"
            f"Time: {now_str}"
        )
        await self._send(text)

    async def notify_shutdown(self, service: str, reason: str) -> None:
        """Alert on service shutdown. No cooldown."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        text = (
            "\U0001f534 <b>Service Stopped</b>\n"
            f"Service: {service}\n"
            f"Reason: {reason}\n"
            f"Time: {now_str}"
        )
        await self._send(text)

    async def notify_reading_milestone(self, total: int) -> None:
        """Alert on reading count milestones (100, 500, 1000, ...). No cooldown."""
        text = (
            "\U0001f389 <b>Reading Milestone</b>\n"
            f"Total readings: {total:,}\n"
            "Keep growing!"
        )
        await self._send(text)
