"""Background scheduler for daily auto-insight delivery.

Runs inside the Telegram bot process as an asyncio task.
Every 60 seconds, queries for users whose delivery time has arrived
and sends them a brief daily reading.
"""

import asyncio
import logging
import os
from datetime import date

import httpx
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, TelegramError

from . import config
from .formatters import format_scheduled_daily_insight

logger = logging.getLogger(__name__)

_CYCLE_INTERVAL = 60  # seconds between scheduler cycles
_SEND_DELAY = 1.0  # seconds between Telegram sends (rate limiting)
_MAX_CONSECUTIVE_FAILURES = 5
_FRONTEND_URL = os.environ.get("TELEGRAM_FRONTEND_URL", "http://localhost:5173")


class DailyScheduler:
    """Background task that delivers daily insights to opted-in Telegram users."""

    def __init__(self, bot: Bot, api_base_url: str | None = None) -> None:
        self.bot = bot
        self._api_base_url = api_base_url or config.API_BASE_URL
        self._running = False
        self._task: asyncio.Task | None = None
        self._consecutive_failures = 0
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client for API calls."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._api_base_url,
                timeout=httpx.Timeout(15.0, connect=5.0),
                headers={"Authorization": f"Bearer {config.BOT_SERVICE_KEY}"},
            )
        return self._client

    async def start(self) -> None:
        """Start the scheduler background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Daily scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler and clean up."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        logger.info("Daily scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop — runs every 60 seconds."""
        while self._running:
            try:
                await self._check_and_deliver()
                self._consecutive_failures = 0
            except asyncio.CancelledError:
                break
            except Exception:
                self._consecutive_failures += 1
                if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    logger.error(
                        "Scheduler: %d consecutive failures", self._consecutive_failures
                    )
                else:
                    logger.warning("Scheduler cycle error", exc_info=True)
            await asyncio.sleep(_CYCLE_INTERVAL)

    async def _check_and_deliver(self) -> None:
        """Query pending users and deliver daily insights."""
        client = await self._get_client()
        resp = await client.get("/telegram/daily/pending")
        if resp.status_code != 200:
            logger.warning("Pending API returned %d", resp.status_code)
            return

        pending = resp.json()
        if not pending:
            return

        logger.info("Scheduler: %d users pending delivery", len(pending))

        for user in pending:
            chat_id = user["chat_id"]
            try:
                message = self._generate_daily_insight(user)
                sent = await self._send_daily_message(chat_id, message)
                if sent:
                    await self._mark_delivered(chat_id)
            except Forbidden:
                logger.info("User %s blocked bot, disabling daily", chat_id)
                await self._disable_user(chat_id)
            except TelegramError as exc:
                logger.warning("Telegram send error for %s: %s", chat_id, exc)
            except Exception:
                logger.exception("Delivery error for %s", chat_id)

            await asyncio.sleep(_SEND_DELAY)

    def _generate_daily_insight(self, user: dict) -> str:
        """Generate a brief daily insight message for a user.

        Uses current date to compute a simple numerological personal day number.
        This is a lightweight generation — the full reading is available via /daily.
        """
        today = date.today()
        day_num = (today.day + today.month + today.year) % 9 or 9

        moon_phases = [
            ("New Moon", "\U0001f311"),
            ("Waxing Crescent", "\U0001f312"),
            ("First Quarter", "\U0001f313"),
            ("Waxing Gibbous", "\U0001f314"),
            ("Full Moon", "\U0001f315"),
            ("Waning Gibbous", "\U0001f316"),
            ("Last Quarter", "\U0001f317"),
            ("Waning Crescent", "\U0001f318"),
        ]
        phase_idx = today.toordinal() % 8
        moon_name, moon_emoji = moon_phases[phase_idx]

        day_meanings = {
            1: "New beginnings and leadership",
            2: "Cooperation and balance",
            3: "Creativity and expression",
            4: "Stability and hard work",
            5: "Change and adventure",
            6: "Harmony and responsibility",
            7: "Reflection and inner wisdom",
            8: "Power and material success",
            9: "Completion and humanitarianism",
        }
        meaning = day_meanings.get(day_num, "")

        return format_scheduled_daily_insight(
            reading_date=today.strftime("%b %d, %Y"),
            personal_day=day_num,
            personal_day_meaning=meaning,
            moon_phase=moon_name,
            moon_emoji=moon_emoji,
        )

    async def _send_daily_message(self, chat_id: int, message: str) -> bool:
        """Send the daily insight to a user. Returns True on success."""
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "See Full Reading \u2192",
                        url=f"{_FRONTEND_URL}/oracle/daily",
                    )
                ]
            ]
        )
        await self.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        return True

    async def _mark_delivered(self, chat_id: int) -> None:
        """Mark a user as delivered for today."""
        today_str = date.today().isoformat()
        client = await self._get_client()
        resp = await client.post(
            "/telegram/daily/delivered",
            json={"chat_id": chat_id, "delivered_date": today_str},
        )
        if resp.status_code != 200:
            logger.warning(
                "Mark delivered failed for %s: %d", chat_id, resp.status_code
            )

    async def _disable_user(self, chat_id: int) -> None:
        """Disable daily delivery for a user who blocked the bot."""
        client = await self._get_client()
        await client.put(
            f"/telegram/daily/preferences/{chat_id}",
            json={"daily_enabled": False},
        )
