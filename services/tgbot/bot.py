"""NPS Telegram Bot — main entry point."""

import logging
import sys

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from . import config
from .client import close_client
from .handlers.core import (
    help_handler,
    link_handler,
    profile_handler,
    start_handler,
    status_handler,
)
from .handlers.readings import (
    daily_command,
    history_command,
    name_command,
    question_command,
    reading_callback_handler,
    time_command,
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Build and run the Telegram bot application."""
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

    # Callback query handler for inline keyboards
    app.add_handler(
        CallbackQueryHandler(reading_callback_handler, pattern=r"^(reading|history):")
    )

    # Graceful shutdown — close httpx client
    async def shutdown(_app: Application) -> None:
        await close_client()

    app.post_shutdown = shutdown

    logger.info("Bot handlers registered, starting polling")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
