"""NPS Telegram Bot — main entry point."""

import logging
import sys

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from . import config
from .client import close_client
from .handlers.admin import register_admin_handlers
from .handlers.core import (
    help_handler,
    link_handler,
    profile_handler,
    start_handler,
    status_handler,
)
from .handlers.daily import (
    daily_off_handler,
    daily_on_handler,
    daily_status_handler,
    daily_time_handler,
)
from .handlers.readings import (
    daily_command,
    history_command,
    name_command,
    question_command,
    reading_callback_handler,
    time_command,
)
from .notifications import SystemNotifier, get_admin_chat_id
from .scheduler import DailyScheduler

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# Module-level references for lifecycle management
_scheduler: DailyScheduler | None = None
_notifier: SystemNotifier | None = None


def main() -> None:
    """Build and run the Telegram bot application."""
    global _scheduler, _notifier  # noqa: PLW0603

    if not config.BOT_TOKEN:
        logger.error("NPS_BOT_TOKEN not set — cannot start bot")
        sys.exit(1)

    logger.info("Starting NPS Telegram Bot")

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Core command handlers (Session 33)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("link", link_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("profile", profile_handler))

    # Reading command handlers (Session 34)
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("name", name_command))
    app.add_handler(CommandHandler("question", question_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("history", history_command))

    # Daily preference command handlers (Session 35)
    app.add_handler(CommandHandler("daily_on", daily_on_handler))
    app.add_handler(CommandHandler("daily_off", daily_off_handler))
    app.add_handler(CommandHandler("daily_time", daily_time_handler))
    app.add_handler(CommandHandler("daily_status", daily_status_handler))

    # Admin command handlers (Session 36)
    register_admin_handlers(app)

    # Callback query handler for inline keyboards
    app.add_handler(
        CallbackQueryHandler(reading_callback_handler, pattern=r"^(reading|history):")
    )

    # Lifecycle hooks
    async def post_init(_app: Application) -> None:
        global _scheduler, _notifier  # noqa: PLW0603

        # Start daily scheduler
        _scheduler = DailyScheduler(bot=_app.bot)
        await _scheduler.start()

        # Initialize system notifier (Session 36)
        admin_chat_id = get_admin_chat_id()
        if admin_chat_id:
            _notifier = SystemNotifier(bot=_app.bot, admin_chat_id=admin_chat_id)
            await _notifier.notify_startup("telegram-bot", version="1.0.0")
            logger.info("SystemNotifier initialized for admin chat %s", admin_chat_id)
        else:
            logger.warning("No admin chat ID configured — notifications disabled")

    async def shutdown(_app: Application) -> None:
        if _notifier:
            await _notifier.notify_shutdown("telegram-bot", "graceful shutdown")
        if _scheduler:
            await _scheduler.stop()
        await close_client()

    app.post_init = post_init
    app.post_shutdown = shutdown

    logger.info("Bot handlers registered, starting polling")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
