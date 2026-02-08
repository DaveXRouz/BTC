"""Oracle request/response models."""

from pydantic import BaseModel, ConfigDict


class ReadingRequest(BaseModel):
    datetime: str | None = None  # ISO 8601, defaults to now
    extended: bool = False


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


class ReadingResponse(BaseModel):
    fc60: FC60Data | None = None
    numerology: NumerologyData | None = None
    zodiac: dict | None = None
    chinese: dict | None = None
    summary: str = ""
    generated_at: str = ""


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    sign_number: int
    interpretation: str
    confidence: float


class NameReadingRequest(BaseModel):
    name: str


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
