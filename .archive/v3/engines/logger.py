"""
Centralized Logger — Rotating file logs with optional Telegram error handler.

Provides:
- setup(): Idempotent logger initialization with RotatingFileHandler
- get_logger(name): Returns a named logger
- TelegramErrorHandler: Sends ERROR+ messages to Telegram if configured

Log files:
- data/nps.log — All messages (DEBUG+), 10MB rotating, 5 backups
- data/error.log — Errors only (ERROR+), 10MB rotating, 5 backups
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

_setup_done = False
_data_dir = Path(__file__).parent.parent / "data"

MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class TelegramErrorHandler(logging.Handler):
    """Sends ERROR+ log records to Telegram (if configured).

    Rate-limited: at most 1 message per 60 seconds to avoid spam.
    """

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self._last_send = 0

    def emit(self, record):
        import time

        now = time.time()
        if now - self._last_send < 60:
            return
        try:
            from engines.notifier import is_configured, send_message

            if is_configured():
                msg = f"<b>NPS Error</b>\n<code>{self.format(record)}</code>"
                # Truncate to Telegram's message limit
                if len(msg) > 4000:
                    msg = msg[:3997] + "..."
                send_message(msg)
                self._last_send = now
        except Exception:
            pass


def setup():
    """Initialize centralized logging. Idempotent — safe to call multiple times."""
    global _setup_done
    if _setup_done:
        return
    _setup_done = True

    _data_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler (INFO+)
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root_logger.handlers
    ):
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"
            )
        )
        root_logger.addHandler(console)

    # Main log file (DEBUG+)
    try:
        main_handler = RotatingFileHandler(
            str(_data_dir / "nps.log"),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(formatter)
        root_logger.addHandler(main_handler)
    except Exception:
        pass

    # Error log file (ERROR+)
    try:
        error_handler = RotatingFileHandler(
            str(_data_dir / "error.log"),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    except Exception:
        pass

    # Telegram error handler
    try:
        tg_handler = TelegramErrorHandler()
        tg_handler.setFormatter(formatter)
        root_logger.addHandler(tg_handler)
    except Exception:
        pass

    logging.getLogger(__name__).info("Logger initialized")


def get_logger(name):
    """Get a named logger. Calls setup() if not already done."""
    if not _setup_done:
        setup()
    return logging.getLogger(name)


def reset():
    """Reset setup state. For testing only."""
    global _setup_done
    _setup_done = False
