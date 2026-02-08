"""Learning system request/response models."""

from datetime import datetime

from pydantic import BaseModel


class LearningStatsResponse(BaseModel):
    level: int
    name: str
    xp: int
    xp_next: int | None
    capabilities: list[str]


class InsightResponse(BaseModel):
    id: str | None = None
    insight_type: str  # "insight" or "recommendation"
    content: str
    source: str | None = None
    created_at: datetime | None = None


class AnalyzeRequest(BaseModel):
    session_id: str
    keys_tested: int = 0
    seeds_tested: int = 0
    hits: int = 0
    speed: float = 0
    elapsed: float = 0
    mode: str = "unknown"
    model: str = "sonnet"


class AnalyzeResponse(BaseModel):
    insights: list[str] = []
    recommendations: list[str] = []
    adjustments: dict[str, float] = {}
    xp_earned: int = 0


class WeightsResponse(BaseModel):
    weights: dict[str, float]


class PatternResponse(BaseModel):
    pattern_type: str
    description: str
    frequency: int
    last_seen: datetime | None = None
