"""Reading type data models for Oracle service.

Defines the 5 reading types (Time, Name, Question, Daily, Multi-User),
the common UserProfile input model, and all result structures.

Uses @dataclass (not Pydantic) to keep Oracle service dependency-free.
Pydantic models belong in the API layer (Session 13+).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReadingType(str, Enum):
    """Supported Oracle reading types."""

    TIME = "time"
    NAME = "name"
    QUESTION = "question"
    DAILY = "daily"
    MULTI_USER = "multi_user"


@dataclass
class UserProfile:
    """Common input for all reading types.

    Maps directly to oracle_users DB columns (Session 1) and
    MasterOrchestrator.generate_reading() parameters.
    """

    user_id: int
    full_name: str
    birth_day: int
    birth_month: int
    birth_year: int
    mother_name: Optional[str] = None
    gender: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heart_rate_bpm: Optional[int] = None
    timezone_hours: int = 0
    timezone_minutes: int = 0
    numerology_system: str = "pythagorean"

    def to_framework_kwargs(self) -> Dict[str, Any]:
        """Convert to MasterOrchestrator.generate_reading() keyword args."""
        return {
            "full_name": self.full_name,
            "birth_day": self.birth_day,
            "birth_month": self.birth_month,
            "birth_year": self.birth_year,
            "mother_name": self.mother_name,
            "gender": self.gender,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "heart_rate_bpm": self.heart_rate_bpm,
            "tz_hours": self.timezone_hours,
            "tz_minutes": self.timezone_minutes,
            "numerology_system": self.numerology_system,
        }


@dataclass
class ReadingRequest:
    """Request wrapper for generating a reading."""

    user: UserProfile
    reading_type: ReadingType
    sign_value: Optional[str] = None
    target_date: Optional[datetime] = None
    additional_users: Optional[List[UserProfile]] = None


@dataclass
class ReadingResult:
    """Result from a single reading generation."""

    reading_type: ReadingType
    user_id: int
    framework_output: Dict[str, Any]
    sign_value: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0
    daily_insights: Optional[Dict[str, Any]] = None


@dataclass
class CompatibilityResult:
    """Pairwise compatibility between two users."""

    user_a_id: int
    user_b_id: int
    overall_score: float
    life_path_score: float
    element_score: float
    animal_score: float
    moon_score: float
    pattern_score: float
    description: str
    strengths: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)


@dataclass
class MultiUserResult:
    """Result from multi-user group analysis."""

    reading_type: ReadingType = ReadingType.MULTI_USER
    individual_readings: List[ReadingResult] = field(default_factory=list)
    pairwise_compatibility: List[CompatibilityResult] = field(default_factory=list)
    group_harmony_score: float = 0.0
    group_element_balance: Dict[str, int] = field(default_factory=dict)
    group_summary: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
