"""Learning system endpoints — AI insights, XP, and levels."""

from fastapi import APIRouter

from app.models.learning import (
    AnalyzeRequest,
    AnalyzeResponse,
    InsightResponse,
    LearningStatsResponse,
    PatternResponse,
    WeightsResponse,
)

router = APIRouter()


@router.get("/stats", response_model=LearningStatsResponse)
async def get_learning_stats():
    """Get current level, XP, and capabilities."""
    # TODO: Query learning_data table
    return LearningStatsResponse(
        level=1,
        name="Novice",
        xp=0,
        xp_next=100,
        capabilities=["Basic scanning"],
    )


@router.get("/insights", response_model=list[InsightResponse])
async def get_insights(limit: int = 10):
    """Get stored AI insights."""
    # TODO: Query insights table
    return []


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_session(request: AnalyzeRequest):
    """Trigger AI analysis of a session."""
    # TODO: Call oracle gRPC AnalyzeSession
    return AnalyzeResponse(insights=[], recommendations=[], xp_earned=0)


@router.get("/weights", response_model=WeightsResponse)
async def get_weights():
    """Get current scoring weights."""
    # TODO: Return scoring configuration
    return WeightsResponse(weights={})


@router.get("/patterns", response_model=list[PatternResponse])
async def get_patterns():
    """Get detected patterns from scanning."""
    # TODO: Query pattern data
    return []
