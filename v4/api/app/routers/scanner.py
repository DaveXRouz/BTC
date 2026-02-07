"""Scanner control endpoints — proxies to Rust Scanner gRPC service."""

from fastapi import APIRouter, HTTPException, status

from app.models.scanner import (
    CheckpointResponse,
    ScanConfigRequest,
    ScanSessionResponse,
    ScanStatsResponse,
    TerminalListResponse,
)

router = APIRouter()


@router.post("/start", response_model=ScanSessionResponse)
async def start_scan(config: ScanConfigRequest):
    """Start a new scan session."""
    # TODO: Call scanner gRPC StartScan
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )


@router.post("/stop/{session_id}")
async def stop_scan(session_id: str):
    """Stop a running scan session."""
    # TODO: Call scanner gRPC StopScan
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )


@router.post("/pause/{session_id}")
async def pause_scan(session_id: str):
    """Pause a running scan session."""
    # TODO: Call scanner gRPC PauseScan
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )


@router.post("/resume/{session_id}")
async def resume_scan(session_id: str):
    """Resume a paused scan session."""
    # TODO: Call scanner gRPC ResumeScan
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )


@router.get("/stats/{session_id}", response_model=ScanStatsResponse)
async def get_scan_stats(session_id: str):
    """Get stats for a scan session."""
    # TODO: Call scanner gRPC GetStats
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )


@router.get("/terminals", response_model=TerminalListResponse)
async def list_terminals():
    """List all active scan sessions/terminals."""
    # TODO: Call scanner gRPC ListSessions
    return TerminalListResponse(terminals=[])


@router.post("/checkpoint/{session_id}", response_model=CheckpointResponse)
async def save_checkpoint(session_id: str):
    """Force a checkpoint save for a session."""
    # TODO: Call scanner gRPC SaveCheckpoint
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Scanner service not connected",
    )
