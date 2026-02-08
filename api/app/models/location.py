"""Location request/response models."""

from pydantic import BaseModel


class CoordinatesResponse(BaseModel):
    city: str
    country: str | None = None
    latitude: float
    longitude: float
    timezone: str | None = None
    cached: bool = False


class LocationDetectResponse(BaseModel):
    ip: str
    city: str | None = None
    country: str | None = None
    country_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    cached: bool = False
