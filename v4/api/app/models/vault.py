"""Vault request/response models."""

from datetime import datetime

from pydantic import BaseModel


class FindingResponse(BaseModel):
    id: str
    address: str
    chain: str
    balance: float
    score: float
    source: str | None = None
    puzzle_number: int | None = None
    score_breakdown: dict | None = None
    metadata: dict = {}
    found_at: datetime
    session_id: str | None = None


class VaultSummaryResponse(BaseModel):
    total: int
    with_balance: int
    by_chain: dict[str, int]
    sessions: int


class ExportRequest(BaseModel):
    format: str = "json"  # "json" or "csv"
    decrypt: bool = False
    chain: str | None = None


class ExportResponse(BaseModel):
    format: str
    url: str
    record_count: int
