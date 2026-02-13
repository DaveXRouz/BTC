"""Progressive message editing for reading generation."""

import asyncio
import logging

from telegram import Message
from telegram.error import BadRequest

from .formatters import format_progress

logger = logging.getLogger(__name__)


async def update_progress(msg: Message, step: int, total: int, text: str) -> bool:
    """Edit a message with progress text. Returns False if message was deleted."""
    try:
        formatted = format_progress(step, total, text)
        await msg.edit_text(formatted, parse_mode="MarkdownV2")
        await asyncio.sleep(0.3)  # Rate limit protection
        return True
    except BadRequest as e:
        err = str(e).lower()
        if "message is not modified" in err:
            return True  # Same text, not an error
        if "message to edit not found" in err:
            return False  # User deleted the message
        logger.warning("Progress update failed: %s", e)
        return True  # Unknown error, continue anyway
    except Exception:
        logger.exception("Unexpected error in progress update")
        return True
