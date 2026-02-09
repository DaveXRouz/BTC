"""WebSocket event models — maps legacy event types to typed messages."""

from pydantic import BaseModel


class WSEvent(BaseModel):
    """Base WebSocket event sent to frontend clients."""

    event: str
    data: dict = {}
    timestamp: float = 0


# Legacy event types -> current WebSocket message types
EVENT_TYPES = {
    "FINDING_FOUND": "finding",
    "HEALTH_CHANGED": "health",
    "AI_ADJUSTED": "ai_adjusted",
    "LEVEL_UP": "level_up",
    "CHECKPOINT_SAVED": "checkpoint",
    "TERMINAL_STATUS_CHANGED": "terminal_status",
    "SCAN_STARTED": "scan_started",
    "SCAN_STOPPED": "scan_stopped",
    "HIGH_SCORE": "high_score",
    "CONFIG_CHANGED": "config_changed",
    "SHUTDOWN": "shutdown",
    # Current-only events
    "STATS_UPDATE": "stats_update",
    "ERROR": "error",
}
