"""Oracle endpoints — proxies to Python Oracle gRPC service."""

from fastapi import APIRouter, HTTPException, status

from app.models.oracle import (
    DailyInsightResponse,
    NameReadingRequest,
    NameReadingResponse,
    QuestionRequest,
    QuestionResponse,
    RangeRequest,
    RangeResponse,
    ReadingRequest,
    ReadingResponse,
)

router = APIRouter()


@router.post("/reading", response_model=ReadingResponse)
async def get_reading(request: ReadingRequest):
    """Get a full oracle reading for a date/time."""
    # TODO: Call oracle gRPC GetReading
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Oracle service not connected",
    )


@router.post("/question", response_model=QuestionResponse)
async def get_question_sign(request: QuestionRequest):
    """Ask a yes/no question with numerological context."""
    # TODO: Call oracle gRPC GetQuestionSign
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Oracle service not connected",
    )


@router.post("/name", response_model=NameReadingResponse)
async def get_name_reading(request: NameReadingRequest):
    """Get a name cipher reading."""
    # TODO: Call oracle gRPC GetNameReading
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Oracle service not connected",
    )


@router.get("/daily", response_model=DailyInsightResponse)
async def get_daily_insight(date: str = None):
    """Get daily insight for today or a specific date."""
    # TODO: Call oracle gRPC GetDailyInsight
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Oracle service not connected",
    )


@router.post("/suggest-range", response_model=RangeResponse)
async def suggest_range(request: RangeRequest):
    """Get AI-suggested scan range based on timing + coverage."""
    # TODO: Call oracle gRPC SuggestRange
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Oracle service not connected",
    )
