"""Oracle request/response models."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

NumerologySystemType = Literal["pythagorean", "chaldean", "abjad", "auto"]


# ─── Framework Reading Models (Session 14+) ─────────────────────────────────


class TimeReadingRequest(BaseModel):
    """Unified reading creation request for time readings."""

    user_id: int
    reading_type: str = "time"
    sign_value: str  # "HH:MM:SS"
    date: str | None = None  # "YYYY-MM-DD", defaults to today
    locale: str = "en"
    numerology_system: NumerologySystemType = "auto"

    @field_validator("sign_value")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate HH:MM:SS format with valid ranges."""
        match = re.match(r"^(\d{1,2}):(\d{2}):(\d{2})$", v)
        if not match:
            raise ValueError(f"Invalid time format: '{v}'. Expected HH:MM:SS")
        h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if not (0 <= h <= 23):
            raise ValueError(f"Hour must be 0-23, got {h}")
        if not (0 <= m <= 59):
            raise ValueError(f"Minute must be 0-59, got {m}")
        if not (0 <= s <= 59):
            raise ValueError(f"Second must be 0-59, got {s}")
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM-DD format if provided."""
        if v is None:
            return v
        match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", v)
        if not match:
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD")
        _y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if not (1 <= m <= 12):
            raise ValueError(f"Month must be 1-12, got {m}")
        if not (1 <= d <= 31):
            raise ValueError(f"Day must be 1-31, got {d}")
        return v


class FrameworkNumerologyData(BaseModel):
    """Maps to framework reading['numerology']."""

    life_path: dict | None = None
    expression: int = 0
    soul_urge: int = 0
    personality: int = 0
    personal_year: int = 0
    personal_month: int = 0
    personal_day: int = 0
    gender_polarity: dict | None = None
    mother_influence: int | None = None

    model_config = ConfigDict(extra="allow")


class FrameworkConfidence(BaseModel):
    """Maps to framework reading['confidence']."""

    score: int = 50
    level: str = "low"
    factors: str = ""

    model_config = ConfigDict(extra="allow")


class PatternDetected(BaseModel):
    """Maps to framework reading['patterns']['detected'] items."""

    type: str = ""
    strength: str = ""
    message: str = ""
    animal: str | None = None
    number: int | None = None
    occurrences: int | None = None

    model_config = ConfigDict(extra="allow")


class AIInterpretationSections(BaseModel):
    """Parsed AI response (from Session 13)."""

    header: str = ""
    universal_address: str = ""
    core_identity: str = ""
    right_now: str = ""
    patterns: str = ""
    message: str = ""
    advice: str = ""
    caution: str = ""
    footer: str = ""
    full_text: str = ""
    ai_generated: bool = False
    locale: str = "en"
    elapsed_ms: float = 0.0
    cached: bool = False
    confidence_score: int = 0

    model_config = ConfigDict(extra="allow")


class FrameworkReadingResponse(BaseModel):
    """Unified reading response for all framework reading types."""

    id: int = 0
    reading_type: str = "time"
    sign_value: str = ""
    framework_result: dict = {}
    ai_interpretation: AIInterpretationSections | None = None
    confidence: FrameworkConfidence = FrameworkConfidence()
    patterns: list[PatternDetected] = []
    fc60_stamp: str = ""
    numerology: FrameworkNumerologyData | None = None
    moon: dict | None = None
    ganzhi: dict | None = None
    locale: str = "en"
    created_at: str = ""

    model_config = ConfigDict(extra="allow")


class ReadingProgressEvent(BaseModel):
    """WebSocket progress message."""

    step: int
    total: int
    message: str
    reading_type: str = "time"


class ReadingRequest(BaseModel):
    datetime: str | None = None  # ISO 8601, defaults to now
    extended: bool = False
    numerology_system: NumerologySystemType = "auto"


class FC60Data(BaseModel):
    cycle: int
    element: str
    polarity: str
    stem: str
    branch: str
    year_number: int
    month_number: int
    day_number: int
    energy_level: float
    element_balance: dict[str, float] = {}


class NumerologyData(BaseModel):
    life_path: int
    day_vibration: int
    personal_year: int
    personal_month: int
    personal_day: int
    interpretation: str = ""


class MoonData(BaseModel):
    phase_name: str = ""
    illumination: float = 0
    age_days: float = 0
    meaning: str = ""
    emoji: str = ""
    energy: str = ""
    best_for: str = ""
    avoid: str = ""


class AngelMatch(BaseModel):
    number: int
    meaning: str


class AngelData(BaseModel):
    matches: list[AngelMatch] = []


class ChaldeanData(BaseModel):
    value: int = 0
    meaning: str = ""
    letter_values: str = ""


class GanzhiData(BaseModel):
    # Year cycle
    year_name: str = ""
    year_animal: str = ""
    year_gz_token: str = ""
    year_traditional_name: str = ""
    stem_element: str = ""
    stem_polarity: str = ""
    # Day cycle
    day_animal: str = ""
    day_element: str = ""
    day_polarity: str = ""
    day_gz_token: str = ""
    # Hour cycle (optional)
    hour_animal: str = ""
    hour_branch: str = ""


class CurrentMomentData(BaseModel):
    weekday: str = ""
    planet: str = ""
    domain: str = ""


class PlanetMoonCombo(BaseModel):
    theme: str = ""
    message: str = ""


class CosmicCycleResponse(BaseModel):
    moon: MoonData | None = None
    ganzhi: GanzhiData | None = None
    current: CurrentMomentData | None = None
    planet_moon: PlanetMoonCombo | None = None


class FC60Extended(BaseModel):
    stamp: str = ""
    weekday_name: str = ""
    weekday_planet: str = ""
    weekday_domain: str = ""


class ReadingResponse(BaseModel):
    fc60: FC60Data | None = None
    numerology: NumerologyData | None = None
    zodiac: dict | None = None
    chinese: dict | None = None
    moon: MoonData | None = None
    angel: AngelData | None = None
    chaldean: ChaldeanData | None = None
    ganzhi: GanzhiData | None = None
    fc60_extended: FC60Extended | None = None
    synchronicities: list[str] = []
    ai_interpretation: str | None = None
    summary: str = ""
    generated_at: str = ""


class QuestionRequest(BaseModel):
    question: str
    numerology_system: NumerologySystemType = "auto"


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sign_number: int
    interpretation: str
    confidence: float


class QuestionReadingRequest(BaseModel):
    question: str
    user_id: int | None = None
    numerology_system: str = "auto"
    include_ai: bool = True

    @field_validator("question")
    @classmethod
    def validate_question_length(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        if len(v) > 500:
            raise ValueError("Question must be 500 characters or less")
        return v


class QuestionReadingResponse(BaseModel):
    question: str
    question_number: int = 0
    detected_script: str = "latin"
    numerology_system: str = "pythagorean"
    raw_letter_sum: int = 0
    is_master_number: bool = False
    fc60_stamp: dict | None = None
    numerology: dict | None = None
    moon: dict | None = None
    ganzhi: dict | None = None
    patterns: dict | None = None
    confidence: dict | None = None
    ai_interpretation: str | None = None
    reading_id: int | None = None

    model_config = ConfigDict(extra="allow")


class NameReadingRequest(BaseModel):
    name: str
    user_id: int | None = None
    numerology_system: str = "pythagorean"
    include_ai: bool = True

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class LetterAnalysis(BaseModel):
    letter: str
    value: int
    element: str


class NameReadingResponse(BaseModel):
    name: str
    detected_script: str = "latin"
    numerology_system: str = "pythagorean"
    expression: int = 0
    soul_urge: int = 0
    personality: int = 0
    life_path: int | None = None
    personal_year: int | None = None
    fc60_stamp: dict | None = None
    moon: dict | None = None
    ganzhi: dict | None = None
    patterns: dict | None = None
    confidence: dict | None = None
    ai_interpretation: str | None = None
    letter_breakdown: list[LetterAnalysis] = []
    reading_id: int | None = None

    model_config = ConfigDict(extra="allow")


class DailyInsightResponse(BaseModel):
    date: str
    insight: str
    lucky_numbers: list[str] = []
    optimal_activity: str = ""


class RangeRequest(BaseModel):
    scanned_ranges: list[str] = []
    puzzle_number: int = 0
    ai_level: int = 1


class RangeResponse(BaseModel):
    range_start: str
    range_end: str
    strategy: str
    confidence: float
    reasoning: str


class StoredReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int | None = None
    sign_type: str
    sign_value: str
    question: str | None = None
    reading_result: dict | None = None
    ai_interpretation: str | None = None
    created_at: str
    is_favorite: bool = False
    deleted_at: str | None = None


class StoredReadingListResponse(BaseModel):
    readings: list[StoredReadingResponse]
    total: int
    limit: int
    offset: int


class ReadingStatsResponse(BaseModel):
    total_readings: int
    by_type: dict[str, int]
    by_month: list[dict]
    favorites_count: int
    most_active_day: str | None


# ─── Multi-User Reading Models ──────────────────────────────────────────────


class MultiUserInput(BaseModel):
    name: str
    birth_year: int
    birth_month: int
    birth_day: int
    user_id: int | None = None

    @property
    def _birth_year_valid(self):
        return 1900 <= self.birth_year <= 2030

    @property
    def _birth_month_valid(self):
        return 1 <= self.birth_month <= 12

    @property
    def _birth_day_valid(self):
        return 1 <= self.birth_day <= 31

    def model_post_init(self, __context):
        if not self.name or not self.name.strip():
            raise ValueError("name must not be empty")
        if not (1900 <= self.birth_year <= 2030):
            raise ValueError("birth_year must be between 1900 and 2030")
        if not (1 <= self.birth_month <= 12):
            raise ValueError("birth_month must be between 1 and 12")
        if not (1 <= self.birth_day <= 31):
            raise ValueError("birth_day must be between 1 and 31")


class MultiUserReadingRequest(BaseModel):
    users: list[MultiUserInput]
    primary_user_index: int = 0
    include_interpretation: bool = True
    numerology_system: NumerologySystemType = "auto"

    def model_post_init(self, __context):
        if len(self.users) < 2:
            raise ValueError("At least 2 users are required")
        if len(self.users) > 10:
            raise ValueError("Maximum 10 users allowed")
        if self.primary_user_index < 0 or self.primary_user_index >= len(self.users):
            raise ValueError(f"primary_user_index must be between 0 and {len(self.users) - 1}")


class CompatibilityScore(BaseModel):
    model_config = ConfigDict(extra="allow")
    user1: str
    user2: str
    overall: float = 0.0
    classification: str = ""
    scores: dict[str, float] = {}
    strengths: list[str] = []
    challenges: list[str] = []


class BondInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    pair: str = ""
    score: float = 0.0
    classification: str = ""


class RoleInfo(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: str = ""
    description: str = ""
    life_path: int = 0


class GroupEnergy(BaseModel):
    model_config = ConfigDict(extra="allow")
    dominant_element: str = ""
    dominant_animal: str = ""
    joint_life_path: int = 0
    archetype: str = ""
    archetype_description: str = ""
    element_distribution: dict[str, int] = {}
    animal_distribution: dict[str, int] = {}
    life_path_distribution: dict[str, int] = {}


class GroupDynamics(BaseModel):
    model_config = ConfigDict(extra="allow")
    avg_compatibility: float = 0.0
    strongest_bond: BondInfo | dict | str = ""
    weakest_bond: BondInfo | dict | str = ""
    roles: dict[str, RoleInfo | dict | str] = {}
    synergies: list[str] = []
    challenges: list[str] = []
    growth_areas: list[str] = []


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    element: str = ""
    animal: str = ""
    polarity: str = ""
    life_path: int = 0
    destiny_number: int = 0
    stem: str = ""
    branch: str = ""
    birth_year: int = 0
    birth_month: int = 0
    birth_day: int = 0
    fc60_sign: str = ""
    name_energy: int = 0


class MultiUserReadingResponse(BaseModel):
    user_count: int
    pair_count: int
    computation_ms: float
    profiles: list[UserProfile] = []
    pairwise_compatibility: list[CompatibilityScore] = []
    group_energy: GroupEnergy | None = None
    group_dynamics: GroupDynamics | None = None
    ai_interpretation: dict | None = None
    reading_id: int | None = None


# ─── FC60 Stamp Validation Models (Session 10) ────────────────────────────


class StampValidateRequest(BaseModel):
    stamp: str


class StampSegment(BaseModel):
    token: str
    value: int | None = None
    animal_name: str | None = None
    element_name: str | None = None


class StampDecodedResponse(BaseModel):
    weekday_token: str
    weekday_name: str
    month: int | None = None
    month_token: str
    day: int | None = None
    dom_token: str
    half: str | None = None
    hour: int | None = None
    hour_animal: str | None = None
    minute: int | None = None
    minute_token: str | None = None
    second: int | None = None
    second_token: str | None = None


class StampValidateResponse(BaseModel):
    valid: bool
    stamp: str
    decoded: StampDecodedResponse | None = None
    error: str | None = None


# ─── Daily Reading Models (Session 16) ─────────────────────────────────────


class DailyReadingRequest(BaseModel):
    """Request for daily reading via POST /api/oracle/readings with reading_type='daily'."""

    user_id: int
    reading_type: str = "daily"
    date: str | None = None  # "YYYY-MM-DD", defaults to today
    locale: str = "en"
    numerology_system: NumerologySystemType = "auto"
    force_regenerate: bool = False

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate YYYY-MM-DD format if provided."""
        if v is None:
            return v
        parts = v.split("-")
        if len(parts) != 3:
            raise ValueError("Date must be YYYY-MM-DD format")
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31):
            raise ValueError("Invalid date values")
        return v


class MultiUserFrameworkRequest(BaseModel):
    """Request for multi-user reading via POST /api/oracle/readings with reading_type='multi'."""

    user_ids: list[int]
    primary_user_index: int = 0
    reading_type: str = "multi"
    date: str | None = None
    locale: str = "en"
    numerology_system: NumerologySystemType = "auto"
    include_interpretation: bool = True

    @field_validator("user_ids")
    @classmethod
    def validate_user_count(cls, v: list[int]) -> list[int]:
        if len(v) < 2:
            raise ValueError("At least 2 users are required")
        if len(v) > 5:
            raise ValueError("Maximum 5 users allowed")
        if len(v) != len(set(v)):
            raise ValueError("Duplicate user IDs not allowed")
        return v

    @field_validator("primary_user_index")
    @classmethod
    def validate_primary_index(cls, v: int, info) -> int:
        user_ids = info.data.get("user_ids", [])
        if user_ids and (v < 0 or v >= len(user_ids)):
            raise ValueError(f"primary_user_index must be 0-{len(user_ids) - 1}")
        return v


class DailyReadingCacheResponse(BaseModel):
    """Response for GET /api/oracle/daily/reading — cached daily reading."""

    user_id: int
    date: str
    reading: FrameworkReadingResponse | None = None
    cached: bool = False
    generated_at: str | None = None


class PairwiseCompatibilityResult(BaseModel):
    """Individual pair compatibility result."""

    user_a_name: str
    user_b_name: str
    user_a_id: int
    user_b_id: int
    overall_score: float
    overall_percentage: int
    classification: str
    dimensions: dict[str, float] = {}
    strengths: list[str] = []
    challenges: list[str] = []
    description: str = ""

    model_config = ConfigDict(extra="allow")


class GroupAnalysisResult(BaseModel):
    """Group-level analysis for 3+ users."""

    group_harmony_score: float
    group_harmony_percentage: int
    element_balance: dict[str, int] = {}
    animal_distribution: dict[str, int] = {}
    dominant_element: str = ""
    dominant_animal: str = ""
    group_summary: str = ""

    model_config = ConfigDict(extra="allow")


class MultiUserFrameworkResponse(BaseModel):
    """Response for multi-user framework reading."""

    id: int | None = None
    user_count: int
    pair_count: int
    computation_ms: float = 0.0
    individual_readings: list[FrameworkReadingResponse] = []
    pairwise_compatibility: list[PairwiseCompatibilityResult] = []
    group_analysis: GroupAnalysisResult | None = None
    ai_interpretation: AIInterpretationSections | None = None
    locale: str = "en"
    created_at: str = ""

    model_config = ConfigDict(extra="allow")
