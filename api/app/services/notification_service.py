"""Notification Service — API-layer wrapper for Telegram notifications.

Routes notification requests through the Oracle notifier engine.
Provides a clean API-layer interface without exposing engine internals.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification categories for routing and filtering."""

    BALANCE_FOUND = "balance_found"
    SCAN_ERROR = "scan_error"
    DAILY_REPORT = "daily_report"
    SYSTEM_ALERT = "system_alert"
    READING_COMPLETE = "reading_complete"


class NotificationService:
    """API-layer notification service.

    Wraps the Oracle notifier engine to provide a clean interface
    for API routes and background tasks.
    """

    def __init__(self):
        self._notifier = None
        self._enabled = False
        self._init_notifier()

    def _init_notifier(self) -> None:
        """Lazy-load the Oracle notifier engine."""
        try:
            from services.oracle.oracle_service.engines import notifier

            self._notifier = notifier
            self._enabled = True
            logger.info("Notification service initialized")
        except ImportError:
            logger.info("Notification service: notifier engine not available")
            self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Whether the notification backend is available."""
        return self._enabled

    def send_alert(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: dict | None = None,
    ) -> bool:
        """Send a notification alert.

        Parameters
        ----------
        notification_type : NotificationType
            Category of notification.
        title : str
            Short alert title.
        message : str
            Alert body text.
        metadata : dict, optional
            Additional context data.

        Returns
        -------
        bool
            True if notification was sent (or queued), False on failure.
        """
        if not self._enabled or self._notifier is None:
            logger.debug(
                "Notification skipped (disabled): %s — %s",
                notification_type.value,
                title,
            )
            return False

        try:
            formatted = f"*{title}*\n{message}"
            if metadata:
                details = "\n".join(f"  {k}: {v}" for k, v in metadata.items())
                formatted += f"\n\nDetails:\n{details}"

            # Route through notifier's dispatch system if available
            if hasattr(self._notifier, "dispatch_command"):
                self._notifier.dispatch_command(f"/alert {notification_type.value}", formatted)
                return True

            logger.debug("Notifier has no dispatch_command, notification dropped")
            return False
        except Exception as e:
            logger.warning("Failed to send notification: %s", e)
            return False


# Module-level singleton
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """FastAPI dependency — returns the notification service singleton."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
