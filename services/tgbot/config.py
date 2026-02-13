"""Bot configuration from environment variables."""

import os

BOT_TOKEN: str = os.environ.get("NPS_BOT_TOKEN", "")
API_BASE_URL: str = os.environ.get("TELEGRAM_BOT_API_URL", "http://api:8000/api")
BOT_SERVICE_KEY: str = os.environ.get("TELEGRAM_BOT_SERVICE_KEY", "")
RATE_LIMIT_PER_MINUTE: int = int(os.environ.get("TELEGRAM_RATE_LIMIT", "20"))
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
ADMIN_CHAT_ID: str = os.environ.get(
    "NPS_ADMIN_CHAT_ID", os.environ.get("NPS_CHAT_ID", "")
)
