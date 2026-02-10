"""Oracle service data models.

Dataclass-based models for reading types, user profiles, compatibility,
and multi-user analysis results. Kept dependency-free (no Pydantic)
for the Oracle service layer.
"""

from .reading_types import (
    CompatibilityResult,
    MultiUserResult,
    ReadingRequest,
    ReadingResult,
    ReadingType,
    UserProfile,
)

__all__ = [
    "CompatibilityResult",
    "MultiUserResult",
    "ReadingRequest",
    "ReadingResult",
    "ReadingType",
    "UserProfile",
]
