"""
Structured JSON logging for the Oracle service.

Provides:
- OracleJSONFormatter: Formats log records as single-line JSON with service metadata
- setup_oracle_logger(): Configures rotating file + console handlers

Log files (written to log_dir, default /app/logs):
- oracle.log — All messages (DEBUG+), 10MB rotating, 5 backups
- error.log — Errors only (ERROR+), 10MB rotating, 5 backups
"""

import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

_setup_done = False


class OracleJSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON for structured log aggregation."""

    def __init__(self, service="oracle"):
        super().__init__()
        self.service = service

    def format(self, record):
        entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
            + ".%03dZ" % record.msecs,
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add RPC method if set on the record
        if hasattr(record, "rpc_method"):
            entry["rpc_method"] = record.rpc_method

        # Add duration if set on the record
        if hasattr(record, "duration_ms"):
            entry["duration_ms"] = record.duration_ms

        # Add exception info
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


def setup_oracle_logger(log_dir=None):
    """Initialize structured JSON logging for the Oracle service.

    Idempotent — safe to call multiple times.

    Parameters
    ----------
    log_dir : str or Path, optional
        Directory for log files. Defaults to /app/logs or $ORACLE_LOG_DIR.
    """
    global _setup_done
    if _setup_done:
        return
    _setup_done = True

    if log_dir is None:
        log_dir = os.environ.get("ORACLE_LOG_DIR", "/app/logs")
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    root.setLevel(getattr(logging, level_name, logging.INFO))

    json_fmt = OracleJSONFormatter(service="oracle")

    # Console handler (for Docker logs) — JSON format
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in root.handlers
    ):
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(json_fmt)
        root.addHandler(console)

    # Main log file (DEBUG+)
    try:
        main_handler = RotatingFileHandler(
            str(log_path / "oracle.log"),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(json_fmt)
        root.addHandler(main_handler)
    except Exception:
        pass

    # Error log file (ERROR+)
    try:
        error_handler = RotatingFileHandler(
            str(log_path / "error.log"),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_fmt)
        root.addHandler(error_handler)
    except Exception:
        pass

    logging.getLogger("oracle_service").info("Structured JSON logging initialized")


def reset():
    """Reset setup state. For testing only."""
    global _setup_done
    _setup_done = False
