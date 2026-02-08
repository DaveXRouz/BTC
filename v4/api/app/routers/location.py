"""Location endpoints — geocoding + IP-based detection."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.middleware.auth import require_scope
from app.models.location import CoordinatesResponse, LocationDetectResponse
from app.services.location_service import LocationService

logger = logging.getLogger(__name__)

router = APIRouter()

_svc = LocationService()

_LOCAL_IPS = {"127.0.0.1", "::1", "localhost", "testclient"}


@router.get(
    "/coordinates",
    response_model=CoordinatesResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def get_coordinates(
    city: str = Query(..., min_length=1),
    country: str | None = Query(None),
):
    """Look up city coordinates via geocoding."""
    result = _svc.get_coordinates(city, country)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city}' not found",
        )
    return CoordinatesResponse(**result)


@router.get(
    "/detect",
    response_model=LocationDetectResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def detect_location(request: Request):
    """Detect location from client IP address."""
    ip = request.client.host if request.client else None
    if not ip or ip in _LOCAL_IPS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot detect location for local/test IP addresses",
        )

    result = _svc.detect_location(ip)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External location service unavailable",
        )
    return LocationDetectResponse(**result)
