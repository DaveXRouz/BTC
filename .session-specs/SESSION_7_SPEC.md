# SESSION 7 SPEC — Framework Integration: Reading Types

**Block:** Calculation Engines (Sessions 6-12)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 6 (framework bridge — `framework_bridge.py` must exist and be importable)

---

## TL;DR

- Implement 5 typed reading functions (Time, Name, Question, Daily, Multi-User) through the Session 6 framework bridge
- Create `UserProfile` dataclass as the common input model for all reading types
- Build `MultiUserAnalyzer` with element/animal compatibility matrices and weighted scoring
- Add data models for reading type definitions, input validation, and result structures
- Write 15+ tests covering all 5 reading types and multi-user compatibility edge cases

---

## OBJECTIVES

1. **Implement 5 reading type functions** in `framework_bridge.py` that each map their specific inputs to `MasterOrchestrator.generate_reading()` parameters
2. **Create typed data models** (`UserProfile`, `ReadingRequest`, `ReadingResult`, `CompatibilityResult`) with full validation and type safety
3. **Build `MultiUserAnalyzer`** that generates N individual readings plus pairwise compatibility scores using element cycles, animal relationships, and weighted numerology comparison
4. **Ensure all reading functions** handle missing optional data gracefully (confidence degrades, never crashes)
5. **Achieve 100% test coverage** on all new code — every reading type, every edge case, every compatibility path

---

## PREREQUISITES

- [ ] Session 6 completed — `services/oracle/oracle_service/framework_bridge.py` exists
- [ ] Framework is importable from Oracle service context
- [ ] Old duplicate engines deleted (Session 6 scope)
- Verification:
  ```bash
  python3 -c "from numerology_ai_framework.synthesis.master_orchestrator import MasterOrchestrator; print('Framework OK')"
  test -f services/oracle/oracle_service/framework_bridge.py && echo "Bridge OK"
  ```

---

## FILES TO CREATE

- `services/oracle/oracle_service/models/reading_types.py` — Data models: `UserProfile`, `ReadingType` enum, `ReadingRequest`, `ReadingResult`, `CompatibilityResult`, `MultiUserResult`
- `services/oracle/oracle_service/models/__init__.py` — Package init with public exports
- `services/oracle/oracle_service/multi_user_analyzer.py` — Compatibility matrices, pairwise scoring, group analysis
- `services/oracle/tests/test_reading_types.py` — Tests for all 5 reading type functions
- `services/oracle/tests/test_multi_user_analyzer.py` — Tests for compatibility analyzer

## FILES TO MODIFY

- `services/oracle/oracle_service/framework_bridge.py` — Add 5 typed reading functions: `generate_time_reading()`, `generate_name_reading()`, `generate_question_reading()`, `generate_daily_reading()`, `generate_multi_user_reading()`

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Data Models & Type Definitions (~60 min)

**Tasks:**

1. Create `services/oracle/oracle_service/models/` directory with `__init__.py`

2. Create `services/oracle/oracle_service/models/reading_types.py` with these types:

   **`ReadingType` enum:**

   ```python
   class ReadingType(str, Enum):
       TIME = "time"           # User provides HH:MM:SS as "sign"
       NAME = "name"           # User provides a name as "sign"
       QUESTION = "question"   # User asks a question — text is analyzed
       DAILY = "daily"         # Auto-generated for today, no sign input
       MULTI_USER = "multi_user"  # 2-5 users, group analysis
   ```

   **`UserProfile` dataclass** — common input for all readings:

   ```python
   @dataclass
   class UserProfile:
       user_id: int
       full_name: str
       birth_day: int
       birth_month: int
       birth_year: int
       mother_name: Optional[str] = None
       gender: Optional[str] = None          # 'male' / 'female' / None
       latitude: Optional[float] = None
       longitude: Optional[float] = None
       heart_rate_bpm: Optional[int] = None
       timezone_hours: int = 0
       timezone_minutes: int = 0
       numerology_system: str = "pythagorean"  # 'pythagorean' / 'chaldean' / 'abjad'
   ```

   - Maps directly to `MasterOrchestrator.generate_reading()` parameters
   - Fields match the `oracle_users` database columns from Session 1
   - Includes a `to_framework_kwargs()` method that returns the dict for `MasterOrchestrator.generate_reading(**kwargs)`

   **`ReadingRequest` dataclass:**

   ```python
   @dataclass
   class ReadingRequest:
       user: UserProfile
       reading_type: ReadingType
       sign_value: Optional[str] = None       # Time string, name, question text
       target_date: Optional[datetime] = None  # Defaults to now
       additional_users: Optional[List[UserProfile]] = None  # For multi-user
   ```

   **`ReadingResult` dataclass:**

   ```python
   @dataclass
   class ReadingResult:
       reading_type: ReadingType
       user_id: int
       framework_output: Dict[str, Any]       # Full MasterOrchestrator output
       sign_value: Optional[str] = None
       generated_at: datetime = field(default_factory=datetime.now)
       confidence_score: float = 0.0
       daily_insights: Optional[Dict] = None  # Only for DAILY type
   ```

   **`CompatibilityResult` dataclass:**

   ```python
   @dataclass
   class CompatibilityResult:
       user_a_id: int
       user_b_id: int
       overall_score: float                   # 0.0 - 1.0
       life_path_score: float                 # Weight: 30%
       element_score: float                   # Weight: 25%
       animal_score: float                    # Weight: 20%
       moon_score: float                      # Weight: 15%
       pattern_score: float                   # Weight: 10%
       description: str                       # Human-readable summary
       strengths: List[str]
       challenges: List[str]
   ```

   **`MultiUserResult` dataclass:**

   ```python
   @dataclass
   class MultiUserResult:
       reading_type: ReadingType = ReadingType.MULTI_USER
       individual_readings: List[ReadingResult] = field(default_factory=list)
       pairwise_compatibility: List[CompatibilityResult] = field(default_factory=list)
       group_harmony_score: float = 0.0       # Average of all pairwise scores
       group_element_balance: Dict[str, int] = field(default_factory=dict)
       group_summary: str = ""
       generated_at: datetime = field(default_factory=datetime.now)
   ```

3. All models use `@dataclass` (not Pydantic) to keep the Oracle service dependency-free. Pydantic models go in the API layer (Session 13+).

**Checkpoint:**

- [ ] `python3 -c "from services.oracle.oracle_service.models.reading_types import UserProfile, ReadingType, ReadingResult; print('Models OK')"` — imports without error
- [ ] All dataclasses instantiate with default values
- [ ] `UserProfile.to_framework_kwargs()` returns a valid dict
- Verify: `python3 -c "from services.oracle.oracle_service.models.reading_types import UserProfile; u = UserProfile(user_id=1, full_name='Test', birth_day=1, birth_month=1, birth_year=2000); print(u.to_framework_kwargs())"`

🚨 STOP if checkpoint fails

---

### Phase 2: 5 Reading Type Functions (~120 min)

**Tasks:**

Add 5 functions to `services/oracle/oracle_service/framework_bridge.py`. Each function:

- Accepts a `UserProfile` (or list for multi-user) + type-specific params
- Maps inputs to `MasterOrchestrator.generate_reading()` keyword arguments
- Returns a `ReadingResult` (or `MultiUserResult`)
- Logs timing with `time.perf_counter()`
- Handles errors gracefully → returns error result, never raises

**Function 1: `generate_time_reading(user, hour, minute, second, target_date=None)`**

- The "sign" is a specific time (HH:MM:SS)
- Passes `current_hour=hour`, `current_minute=minute`, `current_second=second` to framework
- `target_date` defaults to today if not provided
- The time overrides any time in `target_date` — the user's chosen time is the focus
- Returns `ReadingResult` with `sign_value=f"{hour:02d}:{minute:02d}:{second:02d}"`

**Function 2: `generate_name_reading(user, name_to_analyze, target_date=None)`**

- The "sign" is a name string (could be the user's own name or someone else's)
- Passes `full_name=name_to_analyze` to framework (overrides user.full_name)
- Other personal data (birth date, location, etc.) still comes from the user's profile
- Use case: "What does the name 'Alexander' mean numerologically?"
- Returns `ReadingResult` with `sign_value=name_to_analyze`

**Function 3: `generate_question_reading(user, question_text, target_date=None)`**

- The "sign" is a question typed by the user (e.g., "Will I get the job?")
- The question text gets a numerological value via `NumerologyEngine.expression_number(question_text)` — this gives the question its own "vibration number"
- Framework generates reading with the user's profile data + current time
- The question's vibration number is stored in the result as additional context for AI interpretation (Session 13+)
- `target_date` defaults to now (current moment is significant for questions)
- Returns `ReadingResult` with `sign_value=question_text` and `framework_output` augmented with `question_vibration` key

**Function 4: `generate_daily_reading(user, target_date=None)`**

- No manual sign input — the "sign" is today's date itself
- `target_date` defaults to today; passing a future date generates that day's reading
- Framework uses user profile + target date, `current_hour=12`, `current_minute=0`, `current_second=0` (noon — neutral midday energy)
- Adds `daily_insights` dict to `ReadingResult`:
  ```python
  daily_insights = {
      "suggested_activities": [...],   # Based on personal day number
      "energy_forecast": "...",        # Moon phase + planetary day
      "lucky_hours": [...],            # Hours where user's animal appears
      "focus_area": "...",             # From personal month/year context
      "element_of_day": "...",         # From Ganzhi day element
  }
  ```
- `suggested_activities` derived from personal day number (1=start new things, 2=collaborate, 3=create, etc.)
- `lucky_hours` calculated by checking which hours (0-23) have the same Ganzhi animal as the user's birth year animal
- `energy_forecast` combines moon phase energy text + planetary day domain
- Returns `ReadingResult` with `daily_insights` populated

**Function 5: `generate_multi_user_reading(users, reading_type=ReadingType.TIME, sign_value=None, target_date=None)`**

- Accepts 2-5 `UserProfile` objects
- Validates: `len(users) >= 2` and `len(users) <= 5`, raises `ValueError` otherwise
- Generates individual readings for each user (reuses the appropriate single-user function based on `reading_type`)
- Passes individual readings to `MultiUserAnalyzer.analyze_group()` (Phase 3)
- Returns `MultiUserResult` with individual readings + pairwise compatibility + group summary

**Checkpoint:**

- [ ] Each function returns a valid `ReadingResult` with populated `framework_output`
- [ ] Time reading uses the provided hour/minute/second (verify via `framework_output['fc60_stamp']`)
- [ ] Name reading uses `name_to_analyze` not `user.full_name` in the numerology section
- [ ] Question reading includes `question_vibration` key in output
- [ ] Daily reading has `daily_insights` with all 5 sub-keys
- [ ] All functions handle `target_date=None` gracefully (default to now)
- Verify: `cd services/oracle && python3 -m pytest tests/test_reading_types.py -v -k "test_time or test_name or test_question or test_daily"`

🚨 STOP if checkpoint fails

---

### Phase 3: Multi-User Analyzer & Compatibility (~90 min)

**Tasks:**

1. Create `services/oracle/oracle_service/multi_user_analyzer.py` with class `MultiUserAnalyzer`:

   **Element Compatibility Matrix (Wu Xing productive/controlling cycles):**

   ```python
   # Productive cycle: Wood → Fire → Earth → Metal → Water → Wood
   # Controlling cycle: Wood → Earth → Water → Fire → Metal → Wood
   ELEMENT_COMPATIBILITY = {
       ("Wood", "Fire"):  0.9,   # Productive (Wood feeds Fire)
       ("Fire", "Earth"): 0.9,   # Productive
       ("Earth", "Metal"): 0.9,  # Productive
       ("Metal", "Water"): 0.9,  # Productive
       ("Water", "Wood"): 0.9,   # Productive
       ("Wood", "Earth"): 0.3,   # Controlling (Wood parts Earth)
       ("Earth", "Water"): 0.3,  # Controlling
       ("Water", "Fire"): 0.3,   # Controlling
       ("Fire", "Metal"): 0.3,   # Controlling
       ("Metal", "Wood"): 0.3,   # Controlling
       # Same element
       ("Wood", "Wood"):  0.7,   # Same = stable but no growth
       ("Fire", "Fire"):  0.7,
       ("Earth", "Earth"): 0.7,
       ("Metal", "Metal"): 0.7,
       ("Water", "Water"): 0.7,
   }
   # Reverse pairs get the same score (symmetric for productive, asymmetric already covered for controlling)
   ```

   **Animal Compatibility Matrix (Chinese zodiac relationships):**

   ```python
   # Secret friends (best match): Rat-Ox, Tiger-Pig, Rabbit-Dog, Dragon-Rooster, Snake-Monkey, Horse-Goat
   SECRET_FRIENDS = {
       frozenset({"Rat", "Ox"}): 1.0,
       frozenset({"Tiger", "Pig"}): 1.0,
       frozenset({"Rabbit", "Dog"}): 1.0,
       frozenset({"Dragon", "Rooster"}): 1.0,
       frozenset({"Snake", "Monkey"}): 1.0,
       frozenset({"Horse", "Goat"}): 1.0,
   }

   # Trine harmony groups (same element affinity):
   # Water: Rat, Dragon, Monkey
   # Wood: Ox, Snake, Rooster
   # Fire: Tiger, Horse, Dog
   # Earth: Rabbit, Goat, Pig
   TRINE_GROUPS = [
       {"Rat", "Dragon", "Monkey"},    # Water trine
       {"Ox", "Snake", "Rooster"},     # Metal trine
       {"Tiger", "Horse", "Dog"},      # Fire trine
       {"Rabbit", "Goat", "Pig"},      # Wood trine
   ]

   # Clash pairs (conflict): Rat-Horse, Ox-Goat, Tiger-Monkey, Rabbit-Rooster, Dragon-Dog, Snake-Pig
   CLASH_PAIRS = {
       frozenset({"Rat", "Horse"}): 0.2,
       frozenset({"Ox", "Goat"}): 0.2,
       frozenset({"Tiger", "Monkey"}): 0.2,
       frozenset({"Rabbit", "Rooster"}): 0.2,
       frozenset({"Dragon", "Dog"}): 0.2,
       frozenset({"Snake", "Pig"}): 0.2,
   }
   ```

2. Implement `MultiUserAnalyzer` methods:

   **`score_life_path_compatibility(lp_a: int, lp_b: int) -> float`**
   - Same number → 1.0 (perfect resonance)
   - Sum to 9 → 0.8 (completion pair: 1+8, 2+7, 3+6, 4+5)
   - Master + its base (11&2, 22&4, 33&6) → 0.9
   - Both master numbers → 0.85
   - Default → 0.3 + 0.1 \* (1.0 - abs(lp_a - lp_b) / 9.0) — closer numbers slightly more compatible

   **`score_element_compatibility(elem_a: str, elem_b: str) -> float`**
   - Look up in `ELEMENT_COMPATIBILITY` matrix (check both orderings)
   - Default 0.5 for pairs not in matrix (neutral)

   **`score_animal_compatibility(animal_a: str, animal_b: str) -> float`**
   - Secret friends → 1.0
   - Same trine group → 0.8
   - Clash pair → 0.2
   - Same animal → 0.7
   - Default → 0.5

   **`score_moon_alignment(moon_a: Dict, moon_b: Dict) -> float`**
   - Same moon phase → 1.0
   - Adjacent phases (e.g., waxing crescent & first quarter) → 0.7
   - Opposite phases (new vs full) → 0.3
   - Other → 0.5
   - Note: For readings generated at the same time, moon will be identical (score 1.0). This dimension matters more when comparing users' birth-date readings.

   **`score_pattern_overlap(patterns_a: List, patterns_b: List) -> float`**
   - Count shared pattern types (same number repetitions, same animal repetitions)
   - 2+ shared → 0.9
   - 1 shared → 0.7
   - 0 shared, both have patterns → 0.4
   - One or both have no patterns → 0.5 (neutral)

   **`calculate_pairwise(reading_a: ReadingResult, reading_b: ReadingResult) -> CompatibilityResult`**
   - Calls all 5 scoring functions
   - Weighted combination:
     - `life_path_score * 0.30`
     - `element_score * 0.25`
     - `animal_score * 0.20`
     - `moon_score * 0.15`
     - `pattern_score * 0.10`
   - Generates `description` string summarizing the relationship
   - Populates `strengths` list (scores >= 0.7) and `challenges` list (scores <= 0.3)

   **`analyze_group(readings: List[ReadingResult]) -> MultiUserResult`**
   - Generates all pairwise combinations: `itertools.combinations(readings, 2)`
   - Calls `calculate_pairwise()` for each pair
   - Calculates `group_harmony_score` = average of all pairwise overall scores
   - Calculates `group_element_balance` = count of each element across all users' Ganzhi year elements
   - Generates `group_summary` describing the group dynamic

3. Extract comparison data from framework output:
   - Life path: `reading.framework_output['numerology']['life_path']['number']`
   - Element: `reading.framework_output['ganzhi']['year']['element']`
   - Animal: `reading.framework_output['ganzhi']['year']['animal_name']`
   - Moon: `reading.framework_output['moon']['phase_name']`
   - Patterns: `reading.framework_output['patterns']['detected']`

**Checkpoint:**

- [ ] `MultiUserAnalyzer.calculate_pairwise()` returns valid `CompatibilityResult` for 2 users
- [ ] Element matrix is symmetric for productive/controlling cycles
- [ ] Secret friends score 1.0, clash pairs score 0.2
- [ ] `analyze_group()` handles 2, 3, 4, and 5 users
- [ ] Group with 3 users produces 3 pairwise results (3 choose 2)
- [ ] Group with 5 users produces 10 pairwise results (5 choose 2)
- Verify: `cd services/oracle && python3 -m pytest tests/test_multi_user_analyzer.py -v`

🚨 STOP if checkpoint fails

---

### Phase 4: Integration Tests & Verification (~60 min)

**Tasks:**

1. Write `services/oracle/tests/test_reading_types.py` with these tests:

   **Time Reading Tests:**
   - `test_time_reading_basic` — Generate reading for 14:30:00, verify `framework_output` contains FC60 stamp with time component
   - `test_time_reading_midnight` — Edge case: hour=0, minute=0, second=0
   - `test_time_reading_end_of_day` — Edge case: hour=23, minute=59, second=59
   - `test_time_reading_default_date` — Omit target_date, verify defaults to today

   **Name Reading Tests:**
   - `test_name_reading_basic` — Analyze name "Alexander", verify expression number is computed for that name
   - `test_name_reading_overrides_user_name` — User is "Alice", analyze "Bob", verify numerology uses "Bob"
   - `test_name_reading_persian_name` — Name with Persian characters (tests UTF-8 handling)

   **Question Reading Tests:**
   - `test_question_reading_basic` — Ask "Will I succeed?", verify `question_vibration` in output
   - `test_question_reading_vibration_deterministic` — Same question always produces same vibration number
   - `test_question_reading_empty_string` — Empty question returns error or default

   **Daily Reading Tests:**
   - `test_daily_reading_basic` — Generate daily reading, verify `daily_insights` populated
   - `test_daily_reading_has_all_insight_keys` — Check all 5 insight keys present
   - `test_daily_reading_future_date` — Generate for a date 7 days ahead
   - `test_daily_reading_uses_noon` — Verify framework is called with hour=12

   **Multi-User Reading Tests:**
   - `test_multi_user_two_users` — 2 users, verify 1 pairwise result + 2 individual readings
   - `test_multi_user_five_users` — 5 users, verify 10 pairwise results + 5 individual readings
   - `test_multi_user_one_user_fails` — Only 1 user → ValueError
   - `test_multi_user_six_users_fails` — 6 users → ValueError

2. Write `services/oracle/tests/test_multi_user_analyzer.py` with these tests:

   **Life Path Scoring:**
   - `test_life_path_same_number` — Same LP → 1.0
   - `test_life_path_sum_to_nine` — 4+5 → 0.8
   - `test_life_path_master_base_pair` — 11 and 2 → 0.9
   - `test_life_path_distant_numbers` — 1 and 8 (sum=9, so 0.8)

   **Element Scoring:**
   - `test_element_productive_cycle` — Wood+Fire → 0.9
   - `test_element_controlling_cycle` — Wood+Earth → 0.3
   - `test_element_same` — Fire+Fire → 0.7
   - `test_element_symmetric` — score(A,B) == score(B,A) for productive pairs

   **Animal Scoring:**
   - `test_animal_secret_friends` — Rat+Ox → 1.0
   - `test_animal_trine_harmony` — Rat+Dragon → 0.8
   - `test_animal_clash` — Rat+Horse → 0.2
   - `test_animal_same` — Dragon+Dragon → 0.7
   - `test_animal_neutral` — Rat+Tiger → 0.5

   **Group Analysis:**
   - `test_group_harmony_score_average` — Verify it's the mean of all pairwise scores
   - `test_group_element_balance` — 3 users with Wood, Fire, Earth → balanced dict
   - `test_group_pairwise_count` — N users → N\*(N-1)/2 pairs

3. Create shared test fixtures:

   ```python
   TEST_USER_ALICE = UserProfile(
       user_id=1, full_name="Alice Johnson",
       birth_day=15, birth_month=7, birth_year=1990,
       mother_name="Barbara Johnson", gender="female",
       latitude=40.7, longitude=-74.0, heart_rate_bpm=68,
       timezone_hours=-5, timezone_minutes=0,
   )

   TEST_USER_BOB = UserProfile(
       user_id=2, full_name="Bob Smith",
       birth_day=1, birth_month=1, birth_year=2000,
       gender="male",
   )

   TEST_USER_CHARLIE = UserProfile(
       user_id=3, full_name="Charlie Brown",
       birth_day=22, birth_month=11, birth_year=1985,
       gender="male", latitude=51.5, longitude=-0.1,
   )
   ```

4. Run full test suite and verify:

   ```bash
   cd services/oracle && python3 -m pytest tests/test_reading_types.py tests/test_multi_user_analyzer.py -v --tb=short
   ```

5. Verify no regressions in framework tests:
   ```bash
   cd numerology_ai_framework && python3 tests/test_all.py
   ```

**Checkpoint:**

- [ ] All 15+ tests pass
- [ ] No framework test regressions
- [ ] No import errors across the project
- [ ] Timing data logged for each reading generation
- Verify: `cd services/oracle && python3 -m pytest tests/ -v --tb=short -q`

🚨 STOP if checkpoint fails

---

## TESTS TO WRITE

### `services/oracle/tests/test_reading_types.py`

| Test Function                                   | Verifies                                                           |
| ----------------------------------------------- | ------------------------------------------------------------------ |
| `test_time_reading_basic`                       | Time reading produces valid output with correct time in FC60 stamp |
| `test_time_reading_midnight`                    | Edge case: hour=0, min=0, sec=0 works                              |
| `test_time_reading_end_of_day`                  | Edge case: hour=23, min=59, sec=59 works                           |
| `test_time_reading_default_date`                | Omitting target_date defaults to today                             |
| `test_name_reading_basic`                       | Name reading computes numerology for provided name                 |
| `test_name_reading_overrides_user_name`         | Provided name overrides user's profile name for numerology         |
| `test_name_reading_persian_name`                | Persian UTF-8 name processes without error                         |
| `test_question_reading_basic`                   | Question reading includes `question_vibration` in output           |
| `test_question_reading_vibration_deterministic` | Same question → same vibration number                              |
| `test_question_reading_empty_string`            | Empty question handled gracefully                                  |
| `test_daily_reading_basic`                      | Daily reading returns result with `daily_insights`                 |
| `test_daily_reading_has_all_insight_keys`       | All 5 insight keys present in `daily_insights`                     |
| `test_daily_reading_future_date`                | Future date generates valid reading                                |
| `test_daily_reading_uses_noon`                  | Framework called with hour=12, minute=0, second=0                  |
| `test_multi_user_two_users`                     | 2 users → 1 pairwise + 2 individual readings                       |
| `test_multi_user_five_users`                    | 5 users → 10 pairwise + 5 individual readings                      |
| `test_multi_user_one_user_fails`                | 1 user → ValueError                                                |
| `test_multi_user_six_users_fails`               | 6 users → ValueError                                               |

### `services/oracle/tests/test_multi_user_analyzer.py`

| Test Function                      | Verifies                               |
| ---------------------------------- | -------------------------------------- |
| `test_life_path_same_number`       | Same LP → 1.0                          |
| `test_life_path_sum_to_nine`       | Completion pair → 0.8                  |
| `test_life_path_master_base_pair`  | Master + base (11,2) → 0.9             |
| `test_life_path_distant_numbers`   | Scoring formula for non-special pairs  |
| `test_element_productive_cycle`    | Wood→Fire → 0.9                        |
| `test_element_controlling_cycle`   | Wood→Earth → 0.3                       |
| `test_element_same`                | Same element → 0.7                     |
| `test_element_symmetric`           | score(A,B) == score(B,A)               |
| `test_animal_secret_friends`       | Rat+Ox → 1.0                           |
| `test_animal_trine_harmony`        | Same trine group → 0.8                 |
| `test_animal_clash`                | Rat+Horse → 0.2                        |
| `test_animal_same`                 | Same animal → 0.7                      |
| `test_animal_neutral`              | No special relationship → 0.5          |
| `test_group_harmony_score_average` | Group score = mean of pairwise scores  |
| `test_group_element_balance`       | Element distribution counted correctly |
| `test_group_pairwise_count`        | N users → N\*(N-1)/2 pairs             |

**Total: 34 tests minimum**

---

## ACCEPTANCE CRITERIA

- [ ] All 5 reading type functions exist in `framework_bridge.py` and return valid `ReadingResult` instances
- [ ] `generate_time_reading()` uses provided H:M:S in framework call (verifiable via FC60 stamp time component)
- [ ] `generate_name_reading()` overrides `full_name` with the provided name for numerology calculation
- [ ] `generate_question_reading()` computes `question_vibration` and includes it in result
- [ ] `generate_daily_reading()` populates `daily_insights` with all 5 keys
- [ ] `generate_multi_user_reading()` accepts 2-5 users, rejects 1 or 6+
- [ ] Multi-user reading produces correct number of pairwise results: N\*(N-1)/2
- [ ] `MultiUserAnalyzer` element matrix covers all 25 element pairs (5x5)
- [ ] `MultiUserAnalyzer` animal matrix covers all special relationships (6 friends, 4 trine groups, 6 clash pairs)
- [ ] Weighted scoring formula: LP(30%) + Element(25%) + Animal(20%) + Moon(15%) + Patterns(10%) = 100%
- [ ] All 34+ tests pass
- [ ] No import errors: `python3 -c "import services.oracle.oracle_service"` — no errors
- [ ] No framework regressions: `cd numerology_ai_framework && python3 tests/test_all.py` — all pass
- Verify all:
  ```bash
  cd services/oracle && python3 -m pytest tests/test_reading_types.py tests/test_multi_user_analyzer.py -v --tb=short && echo "ALL TESTS PASS"
  ```

---

## ERROR SCENARIOS

| Scenario                                              | Expected Behavior                                                                              |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Framework not importable (Session 6 incomplete)       | `ImportError` at module load time with clear message: "Session 6 framework_bridge.py required" |
| `framework_bridge.py` missing                         | `ImportError` with message pointing to Session 6                                               |
| User profile with only required fields (no optionals) | Reading generates with lower confidence, never crashes                                         |
| Invalid time (hour=25)                                | `ValueError` raised before calling framework                                                   |
| Empty name string for name reading                    | `ValueError("Name cannot be empty")`                                                           |
| Question text with only numbers/symbols               | Vibration number = 0, reading still generates with user profile data                           |
| Multi-user with duplicate user IDs                    | Allowed (same user in two slots is valid for self-compatibility check)                         |
| Multi-user with 0 users                               | `ValueError("At least 2 users required")`                                                      |
| Framework raises unexpected exception                 | Caught at bridge level, logged, re-raised as `ReadingGenerationError`                          |
| Compatibility score rounds to exactly 0.0             | Valid — means maximum conflict on all dimensions (extremely rare)                              |
| All pairwise scores identical                         | Group harmony score = that identical score (mathematically correct)                            |

---

## HANDOFF

**Created:**

- `services/oracle/oracle_service/models/__init__.py`
- `services/oracle/oracle_service/models/reading_types.py`
- `services/oracle/oracle_service/multi_user_analyzer.py`
- `services/oracle/tests/test_reading_types.py`
- `services/oracle/tests/test_multi_user_analyzer.py`

**Modified:**

- `services/oracle/oracle_service/framework_bridge.py` (5 new reading functions added)

**Next session needs:**

- **Session 8 (Numerology System Selection)** depends on:
  - `UserProfile.numerology_system` field (created here) — Session 8 adds auto-detection logic
  - All 5 reading functions passing `numerology_system` through to framework — Session 8 adds the selector UI + API parameter
  - `framework_bridge.py` accepting `numerology_system` parameter — already supported via `UserProfile.to_framework_kwargs()`
- **Session 9 (Signal Processing & Patterns)** depends on:
  - `ReadingResult.framework_output['patterns']` being populated — Session 9 extracts and enhances pattern data
  - Multi-user pattern overlap scoring from `MultiUserAnalyzer` — Session 9 may refine the pattern comparison logic
- **Session 13+ (AI & Reading Types)** depends on:
  - All 5 `ReadingResult` structures being stable — AI interpretation wraps around these
  - `question_vibration` field in question readings — AI uses this for interpretation context
  - `daily_insights` structure in daily readings — AI enriches these with narrative text
