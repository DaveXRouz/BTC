"""Oracle request/response models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

NumerologySystemType = Literal["pythagorean", "chaldean", "abjad", "auto"]


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


class NameReadingRequest(BaseModel):
    name: str
    numerology_system: NumerologySystemType = "auto"


class LetterAnalysis(BaseModel):
    letter: str
    value: int
    element: str


class NameReadingResponse(BaseModel):
    name: str
    destiny_number: int
    soul_urge: int
    personality: int
    letters: list[LetterAnalysis] = []
    interpretation: str = ""


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


class StoredReadingListResponse(BaseModel):
    readings: list[StoredReadingResponse]
    total: int
    limit: int
    offset: int


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
