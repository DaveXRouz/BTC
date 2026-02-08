"""Vault endpoints — findings storage and retrieval."""

from fastapi import APIRouter, Query

from app.models.vault import (
    ExportRequest,
    ExportResponse,
    FindingResponse,
    VaultSummaryResponse,
)

router = APIRouter()


@router.get("/findings", response_model=list[FindingResponse])
async def get_findings(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    chain: str = None,
    min_balance: float = None,
    min_score: float = None,
):
    """Get vault findings with pagination and filtering."""
    # TODO: Query findings table with filters
    return []


@router.get("/summary", response_model=VaultSummaryResponse)
async def get_summary():
    """Get vault summary statistics."""
    # TODO: Aggregate from findings table
    return VaultSummaryResponse(
        total=0,
        with_balance=0,
        by_chain={},
        sessions=0,
    )


@router.get("/search", response_model=list[FindingResponse])
async def search_findings(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=50, ge=1, le=500),
):
    """Search findings by address or metadata."""
    # TODO: Full-text search on findings
    return []


@router.post("/export", response_model=ExportResponse)
async def export_vault(request: ExportRequest):
    """Export vault data as CSV or JSON."""
    # TODO: Generate export file and return download URL
    return ExportResponse(format=request.format, url="", record_count=0)
