"""Dashboard statistics response models."""

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    """Aggregated reading statistics for the dashboard."""

    total_readings: int
    readings_by_type: dict[str, int]
    average_confidence: float | None
    most_used_type: str | None
    streak_days: int
    readings_today: int
    readings_this_week: int
    readings_this_month: int
