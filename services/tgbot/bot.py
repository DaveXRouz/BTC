"""NPS Telegram Bot — main entry point."""

import logging
import sys

from telegram.ext import Application, CommandHandler

from . import config
from .client import close_client
from .handlers.core import (
    help_handler,
    link_handler,
    profile_handler,
    start_handler,
    status_handler,
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

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("link", link_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("profile", profile_handler))

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
