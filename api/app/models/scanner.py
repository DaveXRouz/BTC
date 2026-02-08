"""Scanner request/response models."""

from datetime import datetime

from pydantic import BaseModel


class PuzzleConfig(BaseModel):
    puzzle_number: int
    range_start: str  # hex
    range_end: str  # hex


class ScanConfigRequest(BaseModel):
    mode: str = "both"  # "random_key", "seed_phrase", "both"
    chains: list[str] = ["btc", "eth"]
    batch_size: int = 1000
    check_every_n: int = 5000
    threads: int = 4
    checkpoint_interval: int = 100000
    addresses_per_seed: int = 5
    score_threshold: float = 0.0
    puzzle: PuzzleConfig | None = None


class ScanSessionResponse(BaseModel):
    session_id: str
    status: str  # "running", "paused", "stopped"
    config: ScanConfigRequest
    started_at: datetime


class ScanStatsResponse(BaseModel):
    session_id: str
    keys_tested: int = 0
    seeds_tested: int = 0
    hits: int = 0
    keys_per_second: float = 0
    elapsed_seconds: float = 0
    checkpoint_count: int = 0
    current_mode: str = ""
    highest_score: float = 0


class TerminalInfo(BaseModel):
    session_id: str
    status: str
    mode: str
    started_at: datetime


class TerminalListResponse(BaseModel):
    terminals: list[TerminalInfo]


class CheckpointResponse(BaseModel):
    checkpoint_id: str
    session_id: str
    keys_at_checkpoint: int
    saved_at: datetime
