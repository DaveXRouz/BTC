# SESSION 18 SPEC — AI Learning & Feedback Loop

**Block:** AI & Reading Types (Sessions 13-18)
**Estimated Duration:** 4-5 hours
**Complexity:** High
**Dependencies:** Session 17 (reading history — readings must be stored and retrievable before users can rate them)

---

## TL;DR

- Create `oracle_reading_feedback` table (migration 015) to store star ratings (1-5), section-level helpful/not-helpful flags, and optional text feedback per reading
- Create `oracle_learning_data` table for tracking which signal patterns and prompt strategies produce highly-rated readings
- Build feedback API: `POST /oracle/readings/{id}/feedback` (submit rating + section feedback + text) and `GET /oracle/learning/stats` (admin aggregate view of feedback trends)
- Rewrite `learner.py` from scanner-focused file-based state to Oracle reading feedback analysis with database storage and prompt optimization via weighted scoring
- Build `StarRating.tsx` (reusable 1-5 star component) and `ReadingFeedback.tsx` (container with star rating + section thumbs up/down + text input)
- Integrate feedback UI into `ReadingResults.tsx` after reading display
- Add admin learning dashboard showing feedback trends, top-rated sections, and prompt adjustment recommendations
- Add feedback-related TypeScript types, API client methods, and i18n translations (EN + FA)
- 30+ tests covering feedback storage, rating aggregation, learning data updates, prompt adjustment logic, and frontend rendering

---

## OBJECTIVES

1. **Create migration 015** — New `oracle_reading_feedback` table (rating, section feedback, text, timestamps) and `oracle_learning_data` table (pattern tracking, prompt weights, aggregate metrics)
2. **Create ORM models** — `OracleReadingFeedback` and `OracleLearningData` SQLAlchemy models
3. **Build feedback Pydantic models** — `FeedbackRequest`, `FeedbackResponse`, `SectionFeedback`, `LearningStatsResponse` (oracle-specific, replacing scanner-focused models)
4. **Build feedback API endpoints** — POST submit feedback (with validation: reading must exist, one feedback per user per reading), GET learning stats (admin-only)
5. **Rewrite learner engine** — Replace file-based JSON state with database-backed feedback analysis, weighted scoring algorithm for prompt optimization, no ML
6. **Add prompt weight system** — Track which interpretation formats (simple/advice/action_steps/universe_message) and sections score highest, generate prompt emphasis adjustments
7. **Create StarRating.tsx** — Reusable accessible star rating component with hover preview, keyboard support, RTL-aware
8. **Create ReadingFeedback.tsx** — Full feedback form: star rating, section-level thumbs, optional text input, submit handler
9. **Integrate into ReadingResults.tsx** — Show feedback form after reading display, hide after submission, show "thank you" confirmation
10. **Build admin learning dashboard** — Feedback trend charts, average ratings by reading type, top/bottom sections, prompt adjustment preview
11. **Add TypeScript types and API client methods** for all feedback operations
12. **Add i18n translations** for feedback UI in EN and FA

---

## PREREQUISITES

- [ ] Session 17 completed — readings stored in `oracle_readings` and retrievable via history
- [ ] Session 14 completed — `reading_orchestrator.py` exists (readings use framework)
- [ ] `oracle_readings` table has BIGSERIAL `id` primary key (verified: exists)
- [ ] AI interpreter produces multi-section readings with named sections (verified: `ai_interpreter.py` has 4 formats)
- [ ] Frontend `ReadingResults.tsx` exists with tab-based layout (verified)

Verification:

```bash
test -f api/app/orm/oracle_reading.py && echo "OracleReading ORM OK"
test -f services/oracle/oracle_service/engines/ai_interpreter.py && echo "AI interpreter OK"
test -f services/oracle/oracle_service/engines/learner.py && echo "Learner engine OK"
test -f frontend/src/components/oracle/ReadingResults.tsx && echo "ReadingResults OK"
test -f api/app/routers/learning.py && echo "Learning router OK"
test -f api/app/models/learning.py && echo "Learning models OK"
```

---

## EXISTING STATE ANALYSIS

### What EXISTS (Verified in Codebase)

| Component             | File                                                         | Current State                                                                                                                                                                                            |
| --------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Learning router       | `api/app/routers/learning.py`                                | 5 stub endpoints (GET /stats, GET /insights, POST /analyze, GET /weights, GET /patterns) — all return hardcoded/empty data, scanner-focused                                                              |
| Learning models       | `api/app/models/learning.py`                                 | Scanner-focused: `LearningStatsResponse(level, name, xp, xp_next, capabilities)`, `AnalyzeRequest(session_id, keys_tested, seeds_tested...)`, `InsightResponse`, `WeightsResponse`, `PatternResponse`    |
| Learner engine        | `services/oracle/oracle_service/engines/learner.py`          | File-based JSON state, scanner XP/level system, `learn()` calls AI via CLI (violates CLAUDE.md rule #1), 5 levels (Novice→Master), `add_xp()`, `get_level()`, `get_insights()`                           |
| AI interpreter        | `services/oracle/oracle_service/engines/ai_interpreter.py`   | Full 4-format interpretation (simple/advice/action_steps/universe_message), `InterpretationResult` class, `interpret_reading()`, `interpret_all_formats()`, `interpret_group()`, deterministic fallbacks |
| Prompt templates      | `services/oracle/oracle_service/engines/prompt_templates.py` | 4 individual templates (SIMPLE/ADVICE/ACTION_STEPS/UNIVERSE_MESSAGE), 3 group templates, translation templates, `build_prompt()` helper, `FC60_PRESERVED_TERMS` list                                     |
| Reading ORM           | `api/app/orm/oracle_reading.py`                              | `OracleReading(id: BIGSERIAL, user_id, is_multi_user, question, sign_type, reading_result JSONB, ai_interpretation TEXT, created_at)`                                                                    |
| ReadingResults        | `frontend/src/components/oracle/ReadingResults.tsx`          | Tab-based (summary/details/history), `ExportButton`, no feedback UI                                                                                                                                      |
| TypeScript types      | `frontend/src/types/index.ts:340-356`                        | `LearningStats(level, name, xp, xp_next, capabilities)`, `Insight(id, insight_type, content, source, created_at)` — scanner-focused                                                                      |
| Database schema       | `database/init.sql:126-156`                                  | `learning_data` table (scanner-focused: xp, level, total_keys_scanned, total_hits), `insights` table (learning_id FK, insight_type, content)                                                             |
| Oracle readings table | `database/init.sql:237-258`                                  | `oracle_readings` with sign_type CHECK ('time','name','question','reading','multi_user','daily'), reading_result JSONB                                                                                   |

### What Does NOT Exist (Must Create)

| Component                 | File                                                     | Purpose                                                         |
| ------------------------- | -------------------------------------------------------- | --------------------------------------------------------------- |
| Feedback table            | `database/migrations/015_feedback_learning.sql`          | NEW — `oracle_reading_feedback` + `oracle_learning_data` tables |
| Feedback rollback         | `database/migrations/015_feedback_learning_rollback.sql` | NEW — Clean rollback                                            |
| Feedback ORM              | `api/app/orm/oracle_feedback.py`                         | NEW — `OracleReadingFeedback` + `OracleLearningData` ORM models |
| StarRating component      | `frontend/src/components/oracle/StarRating.tsx`          | NEW — Reusable 1-5 star rating                                  |
| ReadingFeedback component | `frontend/src/components/oracle/ReadingFeedback.tsx`     | NEW — Full feedback form                                        |
| Admin learning dashboard  | `frontend/src/components/admin/LearningDashboard.tsx`    | NEW — Feedback trends + stats                                   |

### What Must Be MODIFIED

| Component        | File                                                | Changes                                                                                           |
| ---------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Learning router  | `api/app/routers/learning.py`                       | Add feedback endpoints, replace scanner stubs with oracle feedback logic                          |
| Learning models  | `api/app/models/learning.py`                        | Add feedback request/response models, oracle-specific stats models                                |
| Learner engine   | `services/oracle/oracle_service/engines/learner.py` | Rewrite from file-based scanner state to DB-backed oracle feedback analysis + prompt optimization |
| ReadingResults   | `frontend/src/components/oracle/ReadingResults.tsx` | Add feedback section after reading display                                                        |
| TypeScript types | `frontend/src/types/index.ts`                       | Add feedback-related interfaces                                                                   |
| API client       | `frontend/src/services/api.ts`                      | Add feedback submit + learning stats methods                                                      |
| i18n EN          | `frontend/src/i18n/en.json`                         | Add feedback labels                                                                               |
| i18n FA          | `frontend/src/i18n/fa.json`                         | Add feedback labels (Persian)                                                                     |

---

## DESIGN DECISIONS

### 1. Feedback Granularity: Star Rating + Section Thumbs + Text

The master spec requires three feedback levels:

- **Overall rating**: 1-5 stars (required when submitting feedback)
- **Section-level feedback**: thumbs up/down per reading section (optional, JSONB in DB)
- **Text feedback**: free-form text (optional, max 1000 chars)

This matches the 4 interpretation formats in `ai_interpreter.py` (simple, advice, action_steps, universe_message). Section-level feedback maps directly to these format names.

### 2. One Feedback Per User Per Reading

Enforce via UNIQUE constraint on `(reading_id, user_id)` in `oracle_reading_feedback`. If a user submits feedback again for the same reading, UPDATE the existing row (upsert).

### 3. Learning Data: Weighted Scoring, Not ML

The master spec explicitly says "no ML needed." The approach:

1. Aggregate feedback by reading type (time/name/question/daily/multi_user), interpretation format, and signal patterns present
2. Compute weighted scores: `avg_rating * count_weight` where count_weight scales with sample size (min 5 ratings for statistical relevance)
3. Store weights in `oracle_learning_data` as JSONB
4. When generating new readings, pass top-performing patterns as emphasis hints to the prompt

### 4. Prompt Optimization: Emphasis Adjustment

Based on feedback data, the learner engine generates "prompt emphasis" adjustments:

- If "advice" format averages 4.5+ stars but "caution" sections get thumbs-down → add emphasis: "Focus on actionable advice, soften cautionary language"
- If readings with moon phase data score higher → add emphasis: "Weave moon phase significance prominently"
- These adjustments are stored as JSONB and prepended to the AI system prompt

This integrates with the existing `prompt_templates.py` `build_prompt()` function — the emphasis text gets prepended as a "learning context" block.

### 5. Reuse Existing `learning_data` Table vs. New `oracle_learning_data`

The existing `learning_data` table is scanner-focused (xp, level, total_keys_scanned). Rather than repurpose it (which would break scanner functionality), create a **new** `oracle_learning_data` table specifically for oracle reading feedback analysis. The existing scanner learning tables remain untouched.

### 6. Admin-Only Stats Endpoint

`GET /oracle/learning/stats` requires admin or moderator role. It returns:

- Average rating by reading type
- Average rating by interpretation format
- Section-level thumbs up/down percentages
- Total feedback count, period trends
- Current prompt emphasis adjustments

---

## FILES CREATED/MODIFIED — COMPLETE LIST

### NEW Files (6)

| #   | Path                                                     | Purpose                                                          |
| --- | -------------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | `database/migrations/015_feedback_learning.sql`          | Migration: oracle_reading_feedback + oracle_learning_data tables |
| 2   | `database/migrations/015_feedback_learning_rollback.sql` | Clean rollback                                                   |
| 3   | `api/app/orm/oracle_feedback.py`                         | ORM: OracleReadingFeedback + OracleLearningData                  |
| 4   | `frontend/src/components/oracle/StarRating.tsx`          | Reusable star rating component                                   |
| 5   | `frontend/src/components/oracle/ReadingFeedback.tsx`     | Full feedback form                                               |
| 6   | `frontend/src/components/admin/LearningDashboard.tsx`    | Admin feedback dashboard                                         |

### MODIFIED Files (8)

| #   | Path                                                | Changes                                                    |
| --- | --------------------------------------------------- | ---------------------------------------------------------- |
| 1   | `api/app/routers/learning.py`                       | Replace scanner stubs with oracle feedback endpoints       |
| 2   | `api/app/models/learning.py`                        | Add feedback + oracle learning Pydantic models             |
| 3   | `services/oracle/oracle_service/engines/learner.py` | Rewrite: DB-backed feedback analysis + prompt optimization |
| 4   | `frontend/src/components/oracle/ReadingResults.tsx` | Add ReadingFeedback after reading display                  |
| 5   | `frontend/src/types/index.ts`                       | Add feedback TypeScript interfaces                         |
| 6   | `frontend/src/services/api.ts`                      | Add feedback submit + stats API methods                    |
| 7   | `frontend/src/i18n/en.json`                         | Add feedback labels                                        |
| 8   | `frontend/src/i18n/fa.json`                         | Add feedback labels (Persian)                              |

---

## IMPLEMENTATION PHASES

### Phase 1: Database Migration 015

**Goal:** Create `oracle_reading_feedback` and `oracle_learning_data` tables.

**File: `database/migrations/015_feedback_learning.sql`**

```sql
-- oracle_reading_feedback: stores user feedback on readings
CREATE TABLE IF NOT EXISTS oracle_reading_feedback (
    id BIGSERIAL PRIMARY KEY,
    reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES oracle_users(id) ON DELETE SET NULL,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    section_feedback JSONB DEFAULT '{}',
    -- section_feedback schema: {"simple": "helpful"|"not_helpful", "advice": "helpful"|"not_helpful", ...}
    text_feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT oracle_feedback_unique UNIQUE (reading_id, user_id),
    CONSTRAINT oracle_feedback_text_length CHECK (LENGTH(text_feedback) <= 1000)
);

-- oracle_learning_data: aggregated learning metrics for oracle feedback
CREATE TABLE IF NOT EXISTS oracle_learning_data (
    id BIGSERIAL PRIMARY KEY,
    metric_key VARCHAR(100) NOT NULL UNIQUE,
    -- metric_key examples: "avg_rating:time", "avg_rating:name", "section_score:advice", "emphasis:moon_phase"
    metric_value DOUBLE PRECISION NOT NULL DEFAULT 0,
    sample_count INTEGER NOT NULL DEFAULT 0,
    details JSONB DEFAULT '{}',
    prompt_emphasis TEXT,
    -- prompt_emphasis: text to prepend to AI prompt based on learning (NULL = no adjustment)
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_feedback_reading ON oracle_reading_feedback(reading_id);
CREATE INDEX IF NOT EXISTS idx_oracle_feedback_user ON oracle_reading_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_oracle_feedback_rating ON oracle_reading_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_oracle_feedback_created ON oracle_reading_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oracle_learning_key ON oracle_learning_data(metric_key);

-- Comments
COMMENT ON TABLE oracle_reading_feedback IS 'User feedback on oracle readings: star rating, section-level thumbs, and text';
COMMENT ON TABLE oracle_learning_data IS 'Aggregated learning metrics for prompt optimization based on feedback';
COMMENT ON COLUMN oracle_reading_feedback.section_feedback IS 'JSONB: {section_name: "helpful"|"not_helpful"} for each interpretation section';
COMMENT ON COLUMN oracle_learning_data.prompt_emphasis IS 'Text prepended to AI system prompt based on learned preferences';

-- Trigger for updated_at
CREATE TRIGGER oracle_feedback_updated_at
    BEFORE UPDATE ON oracle_reading_feedback
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER oracle_learning_updated_at
    BEFORE UPDATE ON oracle_learning_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Track migration
INSERT INTO schema_migrations (version, name) VALUES ('015', 'feedback_learning');
```

**File: `database/migrations/015_feedback_learning_rollback.sql`**

```sql
DROP TRIGGER IF EXISTS oracle_learning_updated_at ON oracle_learning_data;
DROP TRIGGER IF EXISTS oracle_feedback_updated_at ON oracle_reading_feedback;
DROP TABLE IF EXISTS oracle_learning_data;
DROP TABLE IF EXISTS oracle_reading_feedback;
DELETE FROM schema_migrations WHERE version = '015';
```

**STOP — Phase 1 Checkpoint:**

```bash
# Verify migration files exist and contain correct SQL
test -f database/migrations/015_feedback_learning.sql && echo "Migration OK"
test -f database/migrations/015_feedback_learning_rollback.sql && echo "Rollback OK"
grep -q "oracle_reading_feedback" database/migrations/015_feedback_learning.sql && echo "Feedback table OK"
grep -q "oracle_learning_data" database/migrations/015_feedback_learning.sql && echo "Learning table OK"
grep -q "BETWEEN 1 AND 5" database/migrations/015_feedback_learning.sql && echo "Rating constraint OK"
grep -q "UNIQUE (reading_id, user_id)" database/migrations/015_feedback_learning.sql && echo "Upsert constraint OK"
```

---

### Phase 2: ORM Models

**Goal:** SQLAlchemy ORM models for the two new tables.

**File: `api/app/orm/oracle_feedback.py`** — NEW

```python
"""SQLAlchemy ORM models for oracle_reading_feedback and oracle_learning_data tables."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Double,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OracleReadingFeedback(Base):
    __tablename__ = "oracle_reading_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    reading_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("oracle_readings.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("oracle_users.id", ondelete="SET NULL")
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    section_feedback: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    text_feedback: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class OracleLearningData(Base):
    __tablename__ = "oracle_learning_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    metric_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    metric_value: Mapped[float] = mapped_column(Double, nullable=False, default=0)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    details: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    prompt_emphasis: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
```

Follow the exact pattern from `api/app/orm/oracle_reading.py` (imports from `app.database`, `Mapped` + `mapped_column` style, snake_case table names).

**STOP — Phase 2 Checkpoint:**

```bash
test -f api/app/orm/oracle_feedback.py && echo "ORM file OK"
grep -q "OracleReadingFeedback" api/app/orm/oracle_feedback.py && echo "Feedback ORM OK"
grep -q "OracleLearningData" api/app/orm/oracle_feedback.py && echo "Learning ORM OK"
cd api && python3 -c "from app.orm.oracle_feedback import OracleReadingFeedback, OracleLearningData; print('Import OK')"
```

---

### Phase 3: Pydantic Models

**Goal:** Request/response models for feedback API endpoints.

**File: `api/app/models/learning.py`** — MODIFY

Keep existing scanner-focused models. Add new oracle feedback models below them.

**New models to add:**

```python
# ════════════════════════════════════════════════════════════
# Oracle Reading Feedback Models
# ════════════════════════════════════════════════════════════

class SectionFeedbackItem(BaseModel):
    """Feedback for a single reading section."""
    section: str  # "simple", "advice", "action_steps", "universe_message"
    helpful: bool  # True = thumbs up, False = thumbs down


class FeedbackRequest(BaseModel):
    """Submit feedback for a reading."""
    rating: int = Field(ge=1, le=5, description="Star rating 1-5")
    section_feedback: list[SectionFeedbackItem] = Field(
        default_factory=list,
        description="Per-section helpful/not-helpful flags"
    )
    text_feedback: str | None = Field(
        default=None, max_length=1000,
        description="Optional free-text feedback"
    )
    user_id: int | None = Field(
        default=None,
        description="Oracle user ID (optional, for linking)"
    )


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""
    id: int
    reading_id: int
    rating: int
    section_feedback: dict[str, str]  # {"advice": "helpful", "caution": "not_helpful"}
    text_feedback: str | None
    created_at: datetime
    updated: bool  # True if this was an update to existing feedback


class OracleLearningStatsResponse(BaseModel):
    """Admin view of oracle feedback aggregates."""
    total_feedback_count: int
    average_rating: float
    rating_distribution: dict[int, int]  # {1: 5, 2: 10, 3: 25, 4: 40, 5: 20}
    avg_by_reading_type: dict[str, float]  # {"time": 4.2, "name": 3.8, ...}
    avg_by_format: dict[str, float]  # {"simple": 4.0, "advice": 4.5, ...}
    section_helpful_pct: dict[str, float]  # {"advice": 0.85, "caution": 0.45, ...}
    active_prompt_adjustments: list[str]  # Current emphasis hints
    last_recalculated: datetime | None


class PromptAdjustmentPreview(BaseModel):
    """Preview of what prompt adjustments would look like."""
    current_adjustments: list[str]
    suggested_adjustments: list[str]
    data_points: int
    confidence: float  # 0-1 based on sample size
```

**STOP — Phase 3 Checkpoint:**

```bash
cd api && python3 -c "
from app.models.learning import (
    FeedbackRequest, FeedbackResponse,
    SectionFeedbackItem, OracleLearningStatsResponse,
    PromptAdjustmentPreview,
    LearningStatsResponse,  # existing scanner model still works
)
print('All models import OK')
"
```

---

### Phase 4: Feedback API Endpoints

**Goal:** Build the feedback submission and learning stats endpoints.

**File: `api/app/routers/learning.py`** — MODIFY

Keep the 5 existing scanner-focused stubs. Add new oracle feedback endpoints:

**New endpoints to add:**

1. **`POST /learning/oracle/readings/{reading_id}/feedback`** — Submit feedback
   - Validate reading exists (query `oracle_readings` by ID)
   - Validate rating 1-5
   - Convert `section_feedback` list to JSONB dict: `{"advice": "helpful", "caution": "not_helpful"}`
   - Upsert: if feedback already exists for (reading_id, user_id), UPDATE; otherwise INSERT
   - Return `FeedbackResponse` with `updated=True/False`

2. **`GET /learning/oracle/readings/{reading_id}/feedback`** — Get feedback for a reading
   - Return list of all feedback for this reading
   - Public endpoint (no auth required — users can see aggregate feedback)

3. **`GET /learning/oracle/stats`** — Admin learning stats
   - Require admin or moderator role (use `require_role` from auth middleware)
   - Query `oracle_reading_feedback` for aggregates
   - Query `oracle_learning_data` for current prompt adjustments
   - Return `OracleLearningStatsResponse`

4. **`POST /learning/oracle/recalculate`** — Trigger learning recalculation
   - Admin only
   - Call learner engine to recompute all metrics and prompt adjustments
   - Return updated stats

**Implementation details:**

- Import `OracleReadingFeedback`, `OracleLearningData` from `app.orm.oracle_feedback`
- Import `OracleReading` from `app.orm.oracle_reading` (for existence check)
- Use `AsyncSession` from `app.database` (follow existing pattern in `api/app/routers/oracle.py`)
- Use `select()`, `insert()`, `update()` from SQLAlchemy
- Handle `IntegrityError` for upsert (or use `ON CONFLICT DO UPDATE` via `insert().on_conflict_do_update()`)

**STOP — Phase 4 Checkpoint:**

```bash
cd api && python3 -c "
from app.routers.learning import router
routes = [r.path for r in router.routes]
print('Routes:', routes)
assert '/oracle/readings/{reading_id}/feedback' in ' '.join(routes) or any('feedback' in r for r in routes), 'Feedback route missing'
print('Feedback routes OK')
"
```

---

### Phase 5: Learner Engine Rewrite

**Goal:** Replace scanner-focused file-based learner with oracle feedback analysis + prompt optimization.

**File: `services/oracle/oracle_service/engines/learner.py`** — MODIFY

**Current state (to replace):**

- File-based JSON storage (`learning_state.json`)
- Scanner XP/level system (5 levels: Novice→Master)
- `learn()` calls AI via CLI subprocess (violates CLAUDE.md rule #1)
- Tracks: total_keys_scanned, total_hits, insights as plain text

**New implementation:**

Keep the file at the same path. Replace the scanner-focused internals with oracle feedback analysis functions. Preserve the module-level docstring and logger.

**New functions:**

1. **`analyze_feedback(db_session, reading_id: int) -> dict`**
   - Query all feedback for a reading
   - Return: avg_rating, section_scores, text_summary

2. **`recalculate_learning_metrics(db_session) -> dict`**
   - Query all feedback across all readings
   - Group by: reading_type (sign_type), interpretation_format
   - Compute: avg_rating per group, section helpful percentage, rating distribution
   - Update `oracle_learning_data` rows (one per metric_key)
   - Return summary dict

3. **`generate_prompt_emphasis(db_session) -> list[str]`**
   - Read `oracle_learning_data` metrics
   - Apply rules:
     - If avg_rating for "advice" format > 4.0 with 5+ samples → add "Emphasize practical, actionable advice"
     - If section "caution" has < 50% helpful rate → add "Keep cautionary notes brief and constructive"
     - If readings with moon phase data score 0.5+ above average → add "Highlight lunar phase significance"
     - If "simple" format scores highest → add "Prioritize clarity and accessibility"
   - Store emphasis strings in `oracle_learning_data` (metric_key = "prompt_emphasis:active")
   - Return list of emphasis strings

4. **`get_prompt_context(db_session) -> str`**
   - Return the current prompt emphasis as a formatted string block
   - This string gets prepended to the AI system prompt in `ai_interpreter.py`
   - If no learning data exists (cold start), return empty string

5. **`get_learning_stats(db_session) -> dict`**
   - Return aggregated stats for the admin dashboard
   - Uses `oracle_learning_data` table for cached metrics
   - Falls back to direct query if cache is stale (updated_at > 1 hour ago)

**Weight calculation algorithm:**

```python
MINIMUM_SAMPLES = 5  # Need at least 5 ratings for statistical relevance
CONFIDENCE_SCALE = [
    (5, 0.3),    # 5 samples → 30% confidence
    (10, 0.5),   # 10 samples → 50% confidence
    (25, 0.7),   # 25 samples → 70% confidence
    (50, 0.85),  # 50 samples → 85% confidence
    (100, 0.95), # 100 samples → 95% confidence
]

def weighted_score(avg_rating: float, sample_count: int) -> float:
    """Compute confidence-weighted score. Returns 0 if insufficient samples."""
    if sample_count < MINIMUM_SAMPLES:
        return 0.0
    confidence = 0.0
    for threshold, conf in CONFIDENCE_SCALE:
        if sample_count >= threshold:
            confidence = conf
    return avg_rating * confidence
```

**Prompt emphasis rules (threshold-based):**

| Condition                                                           | Emphasis Text                                                            |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| "advice" format avg > 4.0, samples >= 5                             | "Emphasize practical, actionable advice in your interpretations."        |
| "universe_message" avg > 4.0, samples >= 5                          | "Lean into poetic, cosmic language — users respond well to it."          |
| Section "caution" helpful < 50%, samples >= 10                      | "Keep cautionary notes brief, constructive, and forward-looking."        |
| Section "action_steps" helpful > 80%, samples >= 10                 | "Users value concrete action steps — make them specific and achievable." |
| Readings with "time" sign_type avg > readings with "name" sign_type | "Time-based readings resonate strongly — enrich temporal symbolism."     |
| Overall avg across all readings < 3.0, samples >= 20                | "Focus on warmth, encouragement, and personal connection."               |

**STOP — Phase 5 Checkpoint:**

```bash
cd services/oracle && python3 -c "
from oracle_service.engines.learner import (
    MINIMUM_SAMPLES,
    CONFIDENCE_SCALE,
    weighted_score,
    generate_prompt_emphasis,
    get_prompt_context,
)
# Test weighted_score
assert weighted_score(4.5, 3) == 0.0, 'Below minimum should return 0'
assert weighted_score(4.5, 10) == 4.5 * 0.5, 'Should use 0.5 confidence at 10 samples'
print('Learner engine OK')
"
```

---

### Phase 6: Frontend — StarRating + ReadingFeedback Components

**Goal:** Build the user-facing feedback UI.

#### 6a: StarRating Component

**File: `frontend/src/components/oracle/StarRating.tsx`** — NEW

Reusable star rating component:

- Props: `value: number`, `onChange: (rating: number) => void`, `readonly?: boolean`, `size?: "sm" | "md" | "lg"`
- 5 star icons (filled/empty/half based on value)
- Hover preview: hovering over star 3 highlights stars 1-3
- Keyboard accessible: arrow keys to change, Enter to confirm
- RTL-aware: stars render left-to-right regardless of locale (star 1 = leftmost always)
- Use SVG star icons (inline, no external dependency)
- Tailwind classes: gold fill (`text-yellow-400`), gray empty (`text-gray-600`), hover ring
- `aria-label="Rate this reading"`, each star has `aria-label="1 star"` etc.

```typescript
interface StarRatingProps {
  value: number;
  onChange?: (rating: number) => void;
  readonly?: boolean;
  size?: "sm" | "md" | "lg";
}
```

#### 6b: ReadingFeedback Component

**File: `frontend/src/components/oracle/ReadingFeedback.tsx`** — NEW

Full feedback form:

- Props: `readingId: number`, `onSubmitted?: () => void`
- State: `rating`, `sectionFeedback`, `textFeedback`, `isSubmitting`, `isSubmitted`
- Layout:
  1. Star rating (required)
  2. Section thumbs (optional) — for each section in the reading, show section name + thumbs up/down buttons
  3. Text feedback textarea (optional, 1000 char limit with counter)
  4. Submit button
- After submission: hide form, show "Thank you for your feedback!" with the rating shown
- Error handling: show toast/inline error if submission fails
- i18n: all labels via `useTranslation()`
- Accessible: form with `aria-describedby` for instructions

**Section names for thumbs up/down:**

- "Overview" (maps to "simple")
- "Advice" (maps to "advice")
- "Action Steps" (maps to "action_steps")
- "Universe Message" (maps to "universe_message")

Each section shows: label + 👍 button + 👎 button. Active state highlighted.

```typescript
interface ReadingFeedbackProps {
  readingId: number;
  sections?: string[]; // defaults to ["simple", "advice", "action_steps", "universe_message"]
  onSubmitted?: () => void;
}
```

#### 6c: Integrate into ReadingResults

**File: `frontend/src/components/oracle/ReadingResults.tsx`** — MODIFY

Add `ReadingFeedback` component after the tab content area:

```tsx
// After the tab panels, before closing </div>:
{
  result && result.type === "reading" && result.data.reading_id && (
    <ReadingFeedback readingId={result.data.reading_id} />
  );
}
```

This requires that readings now carry a `reading_id` field (set by the backend when the reading is stored in `oracle_readings`). If `reading_id` is not present (e.g., unsaved reading), the feedback section is not shown.

**STOP — Phase 6 Checkpoint:**

```bash
test -f frontend/src/components/oracle/StarRating.tsx && echo "StarRating OK"
test -f frontend/src/components/oracle/ReadingFeedback.tsx && echo "ReadingFeedback OK"
grep -q "ReadingFeedback" frontend/src/components/oracle/ReadingResults.tsx && echo "Integration OK"
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

---

### Phase 7: TypeScript Types + API Client + i18n + Admin Dashboard

**Goal:** Wire everything together: types, API calls, translations, and admin view.

#### 7a: TypeScript Types

**File: `frontend/src/types/index.ts`** — MODIFY

Add after the existing `Insight` interface (around line 356):

```typescript
// ─── Feedback ───

export interface SectionFeedback {
  section: string;
  helpful: boolean;
}

export interface FeedbackRequest {
  rating: number;
  section_feedback: SectionFeedback[];
  text_feedback?: string;
  user_id?: number;
}

export interface FeedbackResponse {
  id: number;
  reading_id: number;
  rating: number;
  section_feedback: Record<string, string>;
  text_feedback: string | null;
  created_at: string;
  updated: boolean;
}

export interface OracleLearningStats {
  total_feedback_count: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
  avg_by_reading_type: Record<string, number>;
  avg_by_format: Record<string, number>;
  section_helpful_pct: Record<string, number>;
  active_prompt_adjustments: string[];
  last_recalculated: string | null;
}
```

#### 7b: API Client Methods

**File: `frontend/src/services/api.ts`** — MODIFY

Add to the `oracle` or `learning` namespace:

```typescript
feedback: {
  submit: (readingId: number, data: FeedbackRequest) =>
    api.post<FeedbackResponse>(`/learning/oracle/readings/${readingId}/feedback`, data),
  get: (readingId: number) =>
    api.get<FeedbackResponse[]>(`/learning/oracle/readings/${readingId}/feedback`),
},
learningStats: {
  get: () => api.get<OracleLearningStats>("/learning/oracle/stats"),
  recalculate: () => api.post<OracleLearningStats>("/learning/oracle/recalculate"),
},
```

#### 7c: i18n Translations

**File: `frontend/src/i18n/en.json`** — MODIFY

Add under an `"oracle"` or `"feedback"` key:

```json
{
  "feedback": {
    "rate_reading": "Rate this reading",
    "star_label": "{{count}} star",
    "star_label_plural": "{{count}} stars",
    "section_feedback": "Was each section helpful?",
    "helpful": "Helpful",
    "not_helpful": "Not helpful",
    "text_placeholder": "Share your thoughts (optional)...",
    "text_counter": "{{count}}/1000",
    "submit": "Submit Feedback",
    "submitting": "Submitting...",
    "thank_you": "Thank you for your feedback!",
    "error": "Failed to submit feedback. Please try again.",
    "sections": {
      "simple": "Overview",
      "advice": "Advice",
      "action_steps": "Action Steps",
      "universe_message": "Universe Message"
    }
  },
  "learning": {
    "dashboard_title": "Learning Dashboard",
    "total_feedback": "Total Feedback",
    "average_rating": "Average Rating",
    "by_reading_type": "By Reading Type",
    "by_format": "By Interpretation Format",
    "section_ratings": "Section Helpfulness",
    "prompt_adjustments": "Active Prompt Adjustments",
    "recalculate": "Recalculate",
    "no_data": "Not enough feedback data yet. Need at least 5 ratings."
  }
}
```

**File: `frontend/src/i18n/fa.json`** — MODIFY

```json
{
  "feedback": {
    "rate_reading": "امتیاز به این خوانش",
    "star_label": "{{count}} ستاره",
    "star_label_plural": "{{count}} ستاره",
    "section_feedback": "آیا هر بخش مفید بود؟",
    "helpful": "مفید",
    "not_helpful": "نامفید",
    "text_placeholder": "نظر خود را بنویسید (اختیاری)...",
    "text_counter": "{{count}}/۱۰۰۰",
    "submit": "ارسال بازخورد",
    "submitting": "در حال ارسال...",
    "thank_you": "از بازخورد شما متشکریم!",
    "error": "ارسال بازخورد ناموفق بود. لطفاً دوباره تلاش کنید.",
    "sections": {
      "simple": "خلاصه",
      "advice": "توصیه",
      "action_steps": "گام‌های عملی",
      "universe_message": "پیام کیهان"
    }
  },
  "learning": {
    "dashboard_title": "داشبورد یادگیری",
    "total_feedback": "کل بازخوردها",
    "average_rating": "میانگین امتیاز",
    "by_reading_type": "بر اساس نوع خوانش",
    "by_format": "بر اساس قالب تفسیر",
    "section_ratings": "مفید بودن بخش‌ها",
    "prompt_adjustments": "تنظیمات فعال",
    "recalculate": "محاسبه مجدد",
    "no_data": "هنوز بازخورد کافی وجود ندارد. حداقل ۵ امتیاز لازم است."
  }
}
```

#### 7d: Admin Learning Dashboard

**File: `frontend/src/components/admin/LearningDashboard.tsx`** — NEW

Admin-only page showing:

1. **Summary cards**: Total feedback count, average rating (with star display), data freshness
2. **Rating distribution**: Horizontal bar chart (CSS only, no charting library) showing count per star level
3. **By reading type**: Table showing avg rating per sign_type (time, name, question, daily, multi_user)
4. **By interpretation format**: Table showing avg rating per format (simple, advice, action_steps, universe_message)
5. **Section helpfulness**: Progress bars showing % helpful for each section
6. **Active prompt adjustments**: List of current emphasis strings, with "Recalculate" button
7. **Confidence indicator**: Show sample size warnings when below 25 ratings

Use `useEffect` to fetch stats on mount via `learningStats.get()`.
Show "Not enough data" message when total_feedback_count < 5.
"Recalculate" button calls `learningStats.recalculate()` and refreshes display.

**STOP — Phase 7 Checkpoint:**

```bash
grep -q "FeedbackRequest" frontend/src/types/index.ts && echo "Types OK"
grep -q "feedback" frontend/src/services/api.ts && echo "API client OK"
test -f frontend/src/components/admin/LearningDashboard.tsx && echo "Dashboard OK"
grep -q "rate_reading" frontend/src/i18n/en.json && echo "i18n EN OK"
grep -q "rate_reading" frontend/src/i18n/fa.json && echo "i18n FA OK"
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

---

## TESTS

### Backend Tests

**File: `api/tests/test_feedback.py`** — NEW (16 tests)

```
test_submit_feedback_success
  → POST feedback with rating=4, verify 201 + returned FeedbackResponse

test_submit_feedback_invalid_rating_zero
  → POST with rating=0, expect 422 validation error

test_submit_feedback_invalid_rating_six
  → POST with rating=6, expect 422 validation error

test_submit_feedback_reading_not_found
  → POST feedback for non-existent reading_id=99999, expect 404

test_submit_feedback_with_sections
  → POST with section_feedback=[{section:"advice", helpful:true}, {section:"caution", helpful:false}]
  → Verify section_feedback stored as {"advice":"helpful","caution":"not_helpful"}

test_submit_feedback_with_text
  → POST with text_feedback="Great reading!", verify text stored

test_submit_feedback_text_too_long
  → POST with text_feedback > 1000 chars, expect 422

test_submit_feedback_upsert_updates
  → POST feedback for same reading+user twice, second call updates rating
  → Verify response.updated == True and rating changed

test_get_feedback_for_reading
  → Submit 3 feedbacks for same reading, GET returns all 3

test_get_feedback_empty
  → GET feedback for reading with no feedback, returns []

test_learning_stats_admin_only
  → GET /learning/oracle/stats without admin role, expect 403

test_learning_stats_returns_aggregates
  → Submit 10+ feedbacks with different ratings/types
  → GET stats, verify total_feedback_count, average_rating, rating_distribution

test_learning_stats_avg_by_reading_type
  → Submit feedbacks for 'time' and 'name' readings
  → Verify avg_by_reading_type has both keys with correct averages

test_recalculate_triggers_update
  → POST /learning/oracle/recalculate (admin)
  → Verify oracle_learning_data table updated

test_prompt_emphasis_generated
  → Submit 10+ feedbacks where "advice" section consistently helpful
  → Recalculate → verify active_prompt_adjustments is non-empty

test_feedback_cascade_on_reading_delete
  → Submit feedback, delete the reading, verify feedback also deleted (CASCADE)
```

### Learner Engine Tests

**File: `services/oracle/oracle_service/tests/test_learner.py`** — NEW (8 tests)

```
test_weighted_score_below_minimum
  → weighted_score(4.5, 3) == 0.0 (below MINIMUM_SAMPLES)

test_weighted_score_at_minimum
  → weighted_score(4.0, 5) == 4.0 * 0.3

test_weighted_score_high_confidence
  → weighted_score(4.0, 100) == 4.0 * 0.95

test_generate_prompt_emphasis_cold_start
  → Empty database → returns empty list

test_generate_prompt_emphasis_advice_high
  → Mock: advice avg 4.5 with 10 samples → emphasis includes "actionable advice"

test_generate_prompt_emphasis_caution_low
  → Mock: caution section < 50% helpful with 10 samples → emphasis includes "cautionary notes brief"

test_get_prompt_context_empty
  → No learning data → returns empty string

test_get_prompt_context_with_emphasis
  → Set learning data with prompt_emphasis → returns formatted context block
```

### Frontend Tests

**File: `frontend/src/components/oracle/__tests__/StarRating.test.tsx`** — NEW (6 tests)

```
test_renders_5_stars
  → Render <StarRating value={0} />, expect 5 star elements

test_shows_filled_stars_for_value
  → Render <StarRating value={3} />, expect 3 filled + 2 empty

test_click_changes_value
  → Click star 4, expect onChange called with 4

test_readonly_prevents_clicks
  → Render <StarRating value={3} readonly />, click star 5, onChange NOT called

test_hover_preview
  → Hover over star 3, expect stars 1-3 highlighted

test_keyboard_navigation
  → Focus + ArrowRight → value increases, ArrowLeft → decreases
```

### Integration Tests

**File: `frontend/src/components/oracle/__tests__/ReadingFeedback.test.tsx`** — NEW (6 tests)

```
test_renders_feedback_form
  → Render <ReadingFeedback readingId={1} />, expect star rating + section thumbs + textarea

test_submit_feedback_flow
  → Set rating=4, click "Advice" helpful, type text, submit → expect API call with correct data

test_shows_thank_you_after_submit
  → Submit feedback → form hidden, "Thank you" shown

test_submit_error_shows_message
  → Mock API error → error message displayed, form still visible

test_section_thumbs_toggle
  → Click "Advice" helpful → highlighted, click again → deselected

test_text_counter_shows_length
  → Type 50 chars → counter shows "50/1000"
```

**Total: 36 tests** (16 backend API + 8 learner engine + 6 StarRating + 6 ReadingFeedback)

---

## ACCEPTANCE CRITERIA

- [ ] Users can rate readings 1-5 stars after viewing a reading
- [ ] Users can mark individual sections as helpful or not helpful
- [ ] Users can optionally submit text feedback (max 1000 chars)
- [ ] Feedback is stored in `oracle_reading_feedback` table with correct foreign keys
- [ ] One feedback per user per reading (upsert on re-submission)
- [ ] Admin endpoint returns correct aggregate statistics
- [ ] Learner engine computes weighted scores with confidence scaling
- [ ] Prompt emphasis strings are generated based on feedback patterns
- [ ] StarRating component is keyboard accessible and RTL-aware
- [ ] ReadingFeedback shows "thank you" confirmation after submission
- [ ] Admin dashboard displays feedback trends and prompt adjustments
- [ ] i18n labels exist for all feedback UI text in EN and FA
- [ ] All 36 tests pass
- [ ] Migration 015 applies cleanly and rollback works

---

## ERROR SCENARIOS

| Scenario                                       | Expected Behavior                                                                          |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Feedback for non-existent reading              | 404 with message "Reading not found"                                                       |
| Rating outside 1-5 range                       | 422 validation error from Pydantic                                                         |
| Text feedback > 1000 chars                     | 422 validation error                                                                       |
| Database unavailable during feedback submit    | 503 with message "Service temporarily unavailable"                                         |
| Admin stats with zero feedback                 | Return zeros/empty dicts, not errors                                                       |
| Learner recalculation with < 5 total ratings   | Return stats with 0 confidence, empty prompt adjustments                                   |
| Frontend API call fails                        | Show inline error, keep form editable for retry                                            |
| Concurrent upserts for same reading+user       | Database UNIQUE constraint handles gracefully, last write wins                             |
| Reading deleted while user is writing feedback | 404 on submit (CASCADE deleted the FK target) — show "This reading is no longer available" |
| Persian text in feedback textarea              | Store as UTF-8, no truncation, render correctly in RTL                                     |

---

## HANDOFF TO NEXT SESSION

After Session 18 is complete:

1. **Completed:** Full feedback loop — users rate readings, system learns, prompts improve
2. **Database state:** Migration 015 applied. Tables: `oracle_reading_feedback`, `oracle_learning_data`
3. **API state:** New endpoints at `/learning/oracle/readings/{id}/feedback` and `/learning/oracle/stats`
4. **Frontend state:** Feedback UI on reading results, admin learning dashboard
5. **Learner state:** Weighted scoring algorithm, prompt emphasis generation, DB-backed metrics

**Session 19 (Frontend Layout & Navigation) can now:**

- Include the learning dashboard in the admin navigation
- Reference the feedback component pattern for consistent form styling
- Know that all backend work (Sessions 1-18) is complete

**The AI & Reading Types block (Sessions 13-18) is now fully complete.** The system can:

- Generate readings (Sessions 13-14: time reading orchestrator)
- Interpret with AI in 4 formats (Session 16: Wisdom AI integration)
- Store and browse reading history (Session 17)
- Accept user feedback and learn from it (Session 18)

---

## APPENDIX: Existing Code Reference

### Existing Learning Router Endpoints (Scanner-Focused, Keep As-Is)

| Method | Path                 | Purpose                          |
| ------ | -------------------- | -------------------------------- |
| GET    | `/learning/stats`    | Scanner XP/level stats           |
| GET    | `/learning/insights` | Scanner AI insights              |
| POST   | `/learning/analyze`  | Trigger scanner session analysis |
| GET    | `/learning/weights`  | Scanner scoring weights          |
| GET    | `/learning/patterns` | Detected scanner patterns        |

These remain unchanged. The new oracle feedback endpoints use the `/learning/oracle/` prefix to avoid conflicts.

### Existing `learner.py` Functions (Scanner-Focused, to Preserve)

The existing file-based learner functions (`load_state`, `save_state`, `get_level`, `add_xp`, `learn`, `get_auto_adjustments`, `get_insights`, `get_recommendations`) serve the scanner system. When rewriting:

- Move scanner functions to a `_scanner_legacy` section at the bottom of the file, or
- Create a separate `scanner_learner.py` if the file gets too long
- The new oracle feedback functions should be clearly separated with a section header

### AI Interpreter Integration Point

The prompt emphasis from the learner integrates with `ai_interpreter.py` at the `interpret_reading()` function. When generating a reading interpretation:

```python
# In ai_interpreter.py, modify interpret_reading():
# 1. Get current prompt context from learner
from engines.learner import get_prompt_context
emphasis = get_prompt_context(db_session)
# 2. Prepend to system prompt
system_prompt = emphasis + "\n\n" + FC60_SYSTEM_PROMPT if emphasis else FC60_SYSTEM_PROMPT
# 3. Pass to generate()
result = generate(prompt, system_prompt=system_prompt)
```

This is the minimal integration point — the AI interpreter calls `get_prompt_context()` before each interpretation to pick up the latest learning adjustments.
