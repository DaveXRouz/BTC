# SESSION 42 SPEC — Integration Tests: All Reading Types

**Block:** Testing & Deployment (Sessions 41-45)
**Estimated Duration:** 5-6 hours
**Complexity:** High
**Dependencies:** Session 41 (auth integration tests, `integration/tests/conftest.py` fixtures)

---

## TL;DR

- Write 6 new integration test files covering all 5 reading types end-to-end plus framework verification
- Each reading type tested through the full stack: HTTP request -> FastAPI -> OracleReadingService -> engines/framework -> response
- Mock Anthropic API for CI determinism; test with real API in staging via `@pytest.mark.ai_real` marker
- Verify framework-specific output fields, caching behavior for daily readings, and multi-user group dynamics
- 60+ test functions total across 6 files, exercising happy paths, edge cases, data types, determinism, and cross-user isolation
- Modify `conftest.py` with shared fixtures (AI mock, reading helper, assertion utilities)

---

## OBJECTIVES

1. **Time reading integration tests** -- Create deep tests for `POST /api/oracle/reading`: verify all 12 response sections (fc60, numerology, zodiac, chinese, moon, angel, chaldean, ganzhi, fc60_extended, synchronicities, ai_interpretation, summary), data types, determinism, and persistence
2. **Name reading integration tests** -- Verify `POST /api/oracle/name` returns correct numerology for the submitted name: destiny number, soul urge, personality, letter-by-letter breakdown, edge cases (single letter, long name, spaces)
3. **Question reading integration tests** -- Verify `POST /api/oracle/question` returns valid answer (yes/no/maybe), deterministic sign number, confidence range, master number rule
4. **Daily reading integration tests** -- Verify `GET /api/oracle/daily` caching (same day = same result), different-day divergence, date format, lucky numbers, non-persistence
5. **Multi-user reading integration tests** -- 3-user reading with individual profiles + group results, pairwise count C(n,2), compatibility scores, group energy/dynamics, DB persistence with junction table
6. **Framework verification tests** -- Confirm all engines (FC60, numerology, zodiac, Ganzhi, moon, Chaldean) produce non-null data for known dates; AI mock/real split for CI vs staging
7. **AI mock infrastructure** -- Patch `engines.ai_interpreter` for CI runs without `ANTHROPIC_API_KEY`; real-API tests guarded by `@pytest.mark.ai_real`

---

## PREREQUISITES

- [ ] Session 41 complete -- `integration/tests/conftest.py` has `api_client`, `db_session`, `db_connection`, `cleanup_test_data` fixtures
- [ ] API running on `API_BASE_URL` (default `http://localhost:8000`)
- [ ] PostgreSQL running and accessible
- [ ] All 5 reading endpoints functional:
  - `POST /api/oracle/reading` (time reading)
  - `POST /api/oracle/name` (name reading)
  - `POST /api/oracle/question` (question reading)
  - `GET /api/oracle/daily` (daily reading)
  - `POST /api/oracle/reading/multi-user` (multi-user reading)
- [ ] Existing integration tests pass: `python3 -m pytest integration/tests/ -v`
- Verification:
  ```bash
  test -f integration/tests/conftest.py && \
  test -f api/app/services/oracle_reading.py && \
  test -f integration/tests/test_api_oracle.py && \
  echo "Prerequisites OK"
  ```

---

## EXISTING CODE ANALYSIS

### Integration Test Infrastructure (Keep & Extend)

**`integration/tests/conftest.py`** provides:

- `api_client` -- `requests.Session` with Bearer auth header, scoped per session
- `db_session` -- SQLAlchemy session that rolls back after each test
- `db_connection` -- Raw database connection for direct SQL verification
- `cleanup_test_data` -- Autouse fixture that deletes `oracle_users WHERE name LIKE 'IntTest%'` after each test
- `api_url(path)` helper -- Builds full URL from relative path

**`integration/tests/test_api_oracle.py`** establishes patterns:

- Test class grouping by feature area (`@pytest.mark.api`)
- User creation within tests (not fixtures, for isolation)
- Direct DB queries to verify encryption/storage
- Status code assertions with informative failure messages

**`integration/tests/test_multi_user.py`** establishes patterns:

- Multi-user payload: `{"users": [...], "primary_user_index": 0, "include_interpretation": False}`
- Performance assertions with `time.perf_counter()`
- DB junction table verification for multi-user readings

### API Endpoint Response Contracts (from `api/app/services/oracle_reading.py`)

**`OracleReadingService.get_reading(datetime_str)`** returns:

```python
{
    "fc60": {
        "cycle": int,          # 0-59
        "element": str,        # Wood/Fire/Earth/Metal/Water
        "polarity": str,       # Yin/Yang
        "stem": str,           # Heavenly stem name
        "branch": str,         # Earthly branch (animal) name
        "year_number": int,    # Numerological year reduction
        "month_number": int,   # Numerological month reduction
        "day_number": int,     # Numerological day reduction
        "energy_level": float, # 0.0-1.0 (moon illumination / 100)
        "element_balance": dict # 5 elements -> float weights summing to ~1.0
    },
    "numerology": {
        "life_path": int,       # 1-9 or master 11/22/33
        "day_vibration": int,   # 1-9
        "personal_year": int,
        "personal_month": int,
        "personal_day": int,
        "interpretation": str   # Life path meaning text
    },
    "zodiac": {"sign": str, "element": str, "ruling_planet": str},
    "chinese": {"animal": str, "element": str, "yin_yang": str},
    "moon": {"phase_name": str, "illumination": float, "age_days": float, "meaning": str, "emoji": str} | None,
    "angel": {"matches": [{"number": str, "meaning": str}]} | None,
    "chaldean": {"value": int, "meaning": str, "letter_values": str} | None,
    "ganzhi": {"year_name": str, "year_animal": str, "stem_element": str, "stem_polarity": str, "hour_animal": str, "hour_branch": str} | None,
    "fc60_extended": {"stamp": str, "weekday_name": str, "weekday_planet": str, "weekday_domain": str} | None,
    "synchronicities": list[str],
    "ai_interpretation": str | None,
    "summary": str,
    "generated_at": str  # ISO 8601
}
```

**`get_question_sign(question)`** returns: `{question, answer, sign_number, interpretation, confidence}`

**`get_name_reading(name)`** returns: `{name, destiny_number, soul_urge, personality, letters, interpretation}`

**`get_daily_insight(date_str)`** returns: `{date, insight, lucky_numbers, optimal_activity}`

**`get_multi_user_reading(users, include_interpretation)`** returns: `{user_count, profiles, reading_id, pairwise_compatibility, group_energy, group_dynamics, computation_ms, pair_count, ai_interpretation}`

### What Session 42 Adds

| Component              | Current State                                                     | What Session 42 Adds                                                                           |
| ---------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Time reading tests     | 1 basic test in `test_api_oracle.py` (checks 4 keys)              | 15 tests: all 12 sections, data types, determinism, edge cases, persistence                    |
| Name reading tests     | 1 basic test (checks 4 keys)                                      | 13 tests: value ranges, letter analysis, single/long names, spaces, persistence                |
| Question reading tests | 1 basic test (checks answer exists)                               | 12 tests: answer values, confidence, determinism, master numbers, long questions               |
| Daily reading tests    | 1 basic test (checks date+insight)                                | 10 tests: caching, date divergence, format validation, non-persistence                         |
| Multi-user tests       | 12 tests in `test_multi_user.py` (2/5/10 users, validation, perf) | 15 tests: 3-user deep flow, profile completeness, pairwise math, group energy/dynamics         |
| Framework tests        | None                                                              | 23 tests: engine output verification, AI mock/real split, cross-reading integrity, performance |
| conftest.py            | Basic fixtures                                                    | AI mock, reading helper, assertion utilities, constants                                        |

---

## FILES TO CREATE

- `integration/tests/test_time_reading.py` -- 15 tests for time-based oracle reading
- `integration/tests/test_name_reading.py` -- 13 tests for name cipher reading
- `integration/tests/test_question_reading.py` -- 12 tests for question reading
- `integration/tests/test_daily_reading.py` -- 10 tests for daily insight reading
- `integration/tests/test_multi_user_reading.py` -- 15 tests for multi-user deep reading
- `integration/tests/test_framework_integration.py` -- 23 tests for framework verification, AI mock, cross-reading integrity, performance

## FILES TO MODIFY

- `integration/tests/conftest.py` -- Add AI mock fixture, reading helper, assertion utilities, constants (~80 lines added, 0 modified)

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Conftest Enhancements & Test Infrastructure (~45 min)

**Tasks:**

1. Add constants to `integration/tests/conftest.py`:

   ```python
   # Deterministic test inputs
   DETERMINISTIC_DATETIME = "2024-06-15T14:30:00+00:00"
   ZODIAC_SIGNS = {"Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                   "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"}
   CHINESE_ANIMALS = {"Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
                      "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"}
   FIVE_ELEMENTS = {"Wood", "Fire", "Earth", "Metal", "Water"}
   VALID_LIFE_PATHS = set(range(1, 10)) | {11, 22, 33}
   ```

2. Add AI mock fixture:

   ```python
   @pytest.fixture
   def ai_mock(monkeypatch):
       """Patch AI interpreter for CI determinism.

       When active, interpret_reading returns mock text and interpret_group
       returns mock dict. Tests can assert on the mock content.
       """
       class MockInterpretation:
           text = "Mock AI interpretation for testing"

       class MockGroupInterpretation:
           def to_dict(self):
               return {"narrative": "Mock group interpretation", "summary": "Test summary"}

       try:
           import sys
           oracle_parent = str(Path(__file__).resolve().parents[2] / "services" / "oracle")
           oracle_service_dir = str(Path(__file__).resolve().parents[2] / "services" / "oracle" / "oracle_service")
           if oracle_parent not in sys.path:
               sys.path.insert(0, oracle_parent)
           if oracle_service_dir not in sys.path:
               sys.path.insert(0, oracle_service_dir)

           from engines import ai_interpreter
           monkeypatch.setattr(ai_interpreter, "interpret_reading", lambda *a, **kw: MockInterpretation())
           monkeypatch.setattr(ai_interpreter, "interpret_group", lambda *a, **kw: MockGroupInterpretation())
       except ImportError:
           pass  # If engines not importable, AI is already unavailable
       yield
   ```

3. Add reading helper fixture:

   ```python
   @pytest.fixture
   def reading_helper(api_client):
       """Utility for common reading test patterns."""
       class ReadingHelper:
           def time_reading(self, datetime_str=DETERMINISTIC_DATETIME):
               resp = api_client.post(api_url("/api/oracle/reading"), json={"datetime": datetime_str})
               assert resp.status_code == 200, f"Time reading failed: {resp.status_code}: {resp.text}"
               return resp.json()

           def name_reading(self, name):
               resp = api_client.post(api_url("/api/oracle/name"), json={"name": name})
               assert resp.status_code == 200, f"Name reading failed: {resp.status_code}: {resp.text}"
               return resp.json()

           def question_reading(self, question):
               resp = api_client.post(api_url("/api/oracle/question"), json={"question": question})
               assert resp.status_code == 200, f"Question reading failed: {resp.status_code}: {resp.text}"
               return resp.json()

           def daily_reading(self, date=None):
               url = api_url("/api/oracle/daily")
               if date:
                   url += f"?date={date}"
               resp = api_client.get(url)
               assert resp.status_code == 200, f"Daily reading failed: {resp.status_code}: {resp.text}"
               return resp.json()

           def multi_user_reading(self, users, include_interpretation=False):
               resp = api_client.post(
                   api_url("/api/oracle/reading/multi-user"),
                   json={"users": users, "primary_user_index": 0, "include_interpretation": include_interpretation},
               )
               assert resp.status_code == 200, f"Multi-user reading failed: {resp.status_code}: {resp.text}"
               return resp.json()
       return ReadingHelper()
   ```

4. Add assertion helper functions:

   ```python
   def assert_reading_has_core_sections(data: dict) -> None:
       """Assert time reading response has all mandatory sections."""
       for key in ("fc60", "numerology", "zodiac", "summary", "generated_at"):
           assert key in data, f"Missing required section: {key}"

   def assert_fc60_valid(fc60: dict) -> None:
       """Assert FC60 section has valid data types and ranges."""
       assert isinstance(fc60["cycle"], int) and 0 <= fc60["cycle"] <= 59
       assert fc60["element"] in FIVE_ELEMENTS
       assert fc60["polarity"] in ("Yin", "Yang")
       assert isinstance(fc60["stem"], str) and len(fc60["stem"]) > 0
       assert isinstance(fc60["branch"], str) and len(fc60["branch"]) > 0
       assert isinstance(fc60["energy_level"], (int, float)) and 0 <= fc60["energy_level"] <= 1.0
       if "element_balance" in fc60:
           assert set(fc60["element_balance"].keys()) == FIVE_ELEMENTS
           assert 0.9 <= sum(fc60["element_balance"].values()) <= 1.1

   def assert_numerology_valid(num: dict) -> None:
       """Assert numerology section has valid data types and ranges."""
       assert num["life_path"] in VALID_LIFE_PATHS
       assert isinstance(num["day_vibration"], int)
       assert isinstance(num["personal_year"], int)
       assert isinstance(num["personal_month"], int)
       assert isinstance(num["personal_day"], int)
       assert isinstance(num["interpretation"], str)
   ```

5. Add `timed_request` helper (extracted from `test_e2e_flow.py` for reuse):

   ```python
   def timed_request(client, method, url, **kwargs):
       """Execute a request and return (response, elapsed_ms)."""
       import time
       start = time.perf_counter()
       resp = getattr(client, method)(url, **kwargs)
       elapsed_ms = (time.perf_counter() - start) * 1000
       return resp, elapsed_ms
   ```

6. Add pytest markers to `integration/pytest.ini` (or `pyproject.toml`):

   ```ini
   markers =
       reading: reading-type integration tests
       framework: framework verification tests
       ai_real: tests requiring real Anthropic API key (skipped in CI)
   ```

**Checkpoint:**

- [ ] `conftest.py` has `ai_mock`, `reading_helper`, assertion helpers, constants
- [ ] `pytest.ini` has `reading`, `framework`, `ai_real` markers
- [ ] `python3 -m pytest integration/tests/conftest.py --collect-only` runs without import errors
- Verify: `grep -c "def ai_mock\|def reading_helper\|def assert_reading_has_core_sections\|def assert_fc60_valid\|def assert_numerology_valid\|def timed_request\|DETERMINISTIC_DATETIME" integration/tests/conftest.py` -- should return 7

STOP if checkpoint fails

---

### Phase 2: Time Reading Tests (~60 min)

**Tasks:**

Create `integration/tests/test_time_reading.py` with class `TestTimeReading` (15 tests).

| #   | Test Function                      | What It Verifies                                                                                                                                                                    |
| --- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `test_response_has_all_sections`   | Response contains all 12 keys: `fc60`, `numerology`, `zodiac`, `chinese`, `moon`, `angel`, `chaldean`, `ganzhi`, `fc60_extended`, `synchronicities`, `ai_interpretation`, `summary` |
| 2   | `test_fc60_data_types`             | `fc60.cycle` is int 0-59, element is Wood/Fire/Earth/Metal/Water, polarity is Yin/Yang, `energy_level` is float 0-1, `element_balance` sums to ~1.0                                 |
| 3   | `test_numerology_data_types`       | `life_path` is valid (1-9 or 11/22/33), `day_vibration` is int, `personal_year/month/day` are ints, `interpretation` is str                                                         |
| 4   | `test_zodiac_data`                 | `sign` is one of 12 zodiac signs, `element` is Fire/Earth/Air/Water, `ruling_planet` is non-empty                                                                                   |
| 5   | `test_chinese_data`                | `animal` is one of 12 animals, `element` is one of 5 elements, `yin_yang` is Yin/Yang                                                                                               |
| 6   | `test_moon_data_present`           | When `moon` is not None: `phase_name` is str, `illumination` is 0-100, `age_days` >= 0                                                                                              |
| 7   | `test_ganzhi_data_present`         | When `ganzhi` is not None: `year_name`, `year_animal`, `stem_element`, `stem_polarity`, `hour_animal`, `hour_branch` are all non-empty strings                                      |
| 8   | `test_fc60_extended_present`       | When `fc60_extended` is not None: `stamp` is non-empty, `weekday_name`/`weekday_planet`/`weekday_domain` are strings                                                                |
| 9   | `test_synchronicities_is_list`     | `synchronicities` is a list, each item is a string                                                                                                                                  |
| 10  | `test_deterministic_same_input`    | Two requests with `DETERMINISTIC_DATETIME` produce identical `fc60`, `numerology`, `zodiac`, `chinese`                                                                              |
| 11  | `test_different_dates_diverge`     | `2024-01-01` vs `2024-07-15` produce different zodiac sign or numerology month                                                                                                      |
| 12  | `test_default_datetime_is_now`     | Request with `datetime=null` returns `generated_at` within 60 seconds of now                                                                                                        |
| 13  | `test_reading_stored_in_db`        | After time reading, `GET /api/oracle/readings` has reading with `sign_type="reading"`                                                                                               |
| 14  | `test_ai_interpretation_with_mock` | With `ai_mock` fixture, `ai_interpretation` is not None                                                                                                                             |
| 15  | `test_generated_at_iso_format`     | `generated_at` parseable by `datetime.fromisoformat()`                                                                                                                              |

**Key implementation details:**

- Use `DETERMINISTIC_DATETIME` and `reading_helper` from conftest
- Use `assert_reading_has_core_sections`, `assert_fc60_valid`, `assert_numerology_valid` helpers
- FC60 determinism: exclude `ai_interpretation` and `generated_at` from equality check (may vary)
- ISO format: `datetime.fromisoformat(data["generated_at"])` should not raise

**Checkpoint:**

- [ ] `integration/tests/test_time_reading.py` exists with 15 test functions
- [ ] All tests use `api_client` or `reading_helper` fixture
- Verify: `grep -c "def test_" integration/tests/test_time_reading.py` -- should return 15

STOP if checkpoint fails

---

### Phase 3: Name & Question Reading Tests (~60 min)

**Tasks:**

**3A. Create `integration/tests/test_name_reading.py`** with class `TestNameReading` (13 tests):

| #   | Test Function                      | What It Verifies                                                                         |
| --- | ---------------------------------- | ---------------------------------------------------------------------------------------- |
| 1   | `test_response_structure`          | Has `name`, `destiny_number`, `soul_urge`, `personality`, `letters`, `interpretation`    |
| 2   | `test_name_echoed_back`            | `response.name` equals submitted name                                                    |
| 3   | `test_destiny_number_valid_range`  | `destiny_number` in 1-9 or master 11/22/33                                               |
| 4   | `test_soul_urge_valid_range`       | `soul_urge` in 1-9 or master                                                             |
| 5   | `test_personality_valid_range`     | `personality` in 1-9 or master                                                           |
| 6   | `test_letter_analysis_count`       | `len(letters)` equals alpha character count in name                                      |
| 7   | `test_letter_analysis_structure`   | Each letter has `letter` (str, len 1), `value` (int >= 0), `element` (one of 5 elements) |
| 8   | `test_deterministic_same_name`     | Two requests with same name produce identical destiny/soul_urge/personality              |
| 9   | `test_different_names_diverge`     | `"Alice"` vs `"Zebra"` produce different destiny numbers                                 |
| 10  | `test_single_letter_name`          | `name="A"` returns 1 letter                                                              |
| 11  | `test_long_name`                   | 26-char name returns 26 letters                                                          |
| 12  | `test_name_with_spaces`            | `"John Doe"` has 7 letters (excluding space)                                             |
| 13  | `test_reading_stored_as_name_type` | Reading history has entry with `sign_type="name"`                                        |

**3B. Create `integration/tests/test_question_reading.py`** with class `TestQuestionReading` (12 tests):

| #   | Test Function                          | What It Verifies                                                                    |
| --- | -------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | `test_response_structure`              | Has `question`, `answer`, `sign_number`, `interpretation`, `confidence`             |
| 2   | `test_question_echoed_back`            | `response.question` equals submitted question                                       |
| 3   | `test_answer_is_valid`                 | `answer` in `{"yes", "no", "maybe"}`                                                |
| 4   | `test_sign_number_is_positive_int`     | `sign_number` is int > 0                                                            |
| 5   | `test_confidence_range`                | `confidence` is float, `0.0 <= confidence <= 1.0`                                   |
| 6   | `test_interpretation_non_empty`        | `interpretation` is non-empty string                                                |
| 7   | `test_deterministic_same_question`     | Same question twice produces same `answer` and `sign_number`                        |
| 8   | `test_different_questions_may_differ`  | Different questions produce valid but potentially different sign numbers            |
| 9   | `test_short_question`                  | `"Why?"` returns valid response                                                     |
| 10  | `test_long_question`                   | 500-char question returns valid response                                            |
| 11  | `test_reading_stored_as_question_type` | Reading history has entry with `sign_type="question"`                               |
| 12  | `test_master_number_produces_maybe`    | Question crafted with 11 alpha chars produces `answer="maybe"` (master number rule) |

**Key implementation details for master number test:**

- `get_question_sign()` logic: alpha count -> `numerology_reduce()` -> if result in (11, 22, 33) -> "maybe"
- Craft a question with exactly 11 alpha characters: `"Hello World"` has 10 alpha, `"Hello Worldx"` has 11
- Verify: `sum(1 for c in "Hello Worldx" if c.isalpha()) == 11` -> `numerology_reduce(11) == 11` (master) -> "maybe"

**Checkpoint:**

- [ ] `test_name_reading.py` has 13 tests, `test_question_reading.py` has 12 tests
- Verify: `grep -c "def test_" integration/tests/test_name_reading.py` -- 13
- Verify: `grep -c "def test_" integration/tests/test_question_reading.py` -- 12

STOP if checkpoint fails

---

### Phase 4: Daily Reading Tests (~30 min)

**Tasks:**

Create `integration/tests/test_daily_reading.py` with class `TestDailyReading` (10 tests):

| #   | Test Function                       | What It Verifies                                                                       |
| --- | ----------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | `test_response_structure`           | Has `date`, `insight`, `lucky_numbers`, `optimal_activity`                             |
| 2   | `test_date_is_valid_format`         | `date` matches YYYY-MM-DD format and is parseable                                      |
| 3   | `test_insight_is_non_empty`         | `insight` is non-empty string                                                          |
| 4   | `test_lucky_numbers_format`         | `lucky_numbers` is list of strings, each parseable as int                              |
| 5   | `test_default_date_is_today`        | No `?date=` param returns today's date                                                 |
| 6   | `test_specific_date`                | `?date=2024-06-15` returns `date="2024-06-15"`                                         |
| 7   | `test_same_date_same_result`        | Two requests for same date return identical response fields                            |
| 8   | `test_different_dates_diverge`      | `2024-01-01` vs `2024-07-15` produce different insight or lucky numbers                |
| 9   | `test_daily_does_not_store_reading` | Daily insight GET does NOT create row in oracle_readings (count before == count after) |
| 10  | `test_optimal_activity_is_string`   | `optimal_activity` is string (may be empty but not None)                               |

**Key implementation details:**

- `test_daily_does_not_store_reading`: Count readings via `GET /api/oracle/readings` before and after daily request, assert same count
- `test_same_date_same_result`: Compare `insight` and `lucky_numbers` fields -- both are deterministic for a given date
- `test_specific_date`: API may or may not support `?date=` query param. If it returns 200, verify date matches. If not supported, skip gracefully.

**Checkpoint:**

- [ ] `test_daily_reading.py` has 10 tests
- Verify: `grep -c "def test_" integration/tests/test_daily_reading.py` -- 10

STOP if checkpoint fails

---

### Phase 5: Multi-User Deep Tests (~60 min)

**Tasks:**

Create `integration/tests/test_multi_user_reading.py` with class `TestMultiUserReadingDeep` (15 tests):

| #   | Test Function                                 | What It Verifies                                                                                                                                     |
| --- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `test_three_user_reading`                     | `user_count=3`, `profiles` has 3 entries                                                                                                             |
| 2   | `test_profile_field_completeness`             | Each profile has: `name`, `element`, `animal`, `polarity`, `life_path`, `destiny_number`, `stem`, `branch`, `birth_year`, `birth_month`, `birth_day` |
| 3   | `test_pairwise_count_formula`                 | For n=2 -> 1 pair, n=3 -> 3 pairs, n=4 -> 6 pairs                                                                                                    |
| 4   | `test_compatibility_score_range`              | Each pairwise entry has `overall` float 0.0-100.0, `classification` non-empty                                                                        |
| 5   | `test_compatibility_strengths_challenges`     | Each pairwise entry has `strengths` (list) and `challenges` (list)                                                                                   |
| 6   | `test_group_energy_present`                   | `group_energy` has `dominant_element`, `dominant_animal`, `joint_life_path`, `element_distribution`                                                  |
| 7   | `test_group_dynamics_present`                 | `group_dynamics` has `avg_compatibility`, `strongest_bond`, `weakest_bond`, `roles`, `synergies`, `challenges`                                       |
| 8   | `test_group_dynamics_avg_compatibility_range` | `avg_compatibility` is float 0.0-100.0                                                                                                               |
| 9   | `test_computation_ms_tracked`                 | `computation_ms` is float > 0                                                                                                                        |
| 10  | `test_pair_count_matches_pairwise`            | `pair_count` equals `len(pairwise_compatibility)`                                                                                                    |
| 11  | `test_reading_id_returned`                    | `reading_id` is int > 0                                                                                                                              |
| 12  | `test_profiles_match_input_names`             | Profile names match submitted user names in order                                                                                                    |
| 13  | `test_deterministic_same_users`               | Two identical requests produce identical profiles and pairwise compatibility                                                                         |
| 14  | `test_three_user_with_interpretation`         | With `include_interpretation=True`, `ai_interpretation` is not None (if AI available or mocked)                                                      |
| 15  | `test_multi_user_stored_with_junction`        | DB has `oracle_readings` row with `is_multi_user=True`, `sign_type="multi_user"`                                                                     |

**Standard 3-user test data:**

```python
THREE_USERS = [
    {"name": "IntTest_Deep_A", "birth_year": 1990, "birth_month": 3, "birth_day": 15},
    {"name": "IntTest_Deep_B", "birth_year": 1985, "birth_month": 7, "birth_day": 22},
    {"name": "IntTest_Deep_C", "birth_year": 1978, "birth_month": 11, "birth_day": 8},
]
```

**Key implementation details:**

- Pairwise formula verification: loop over n=2,3,4, create that many users, assert pairwise count
- Profile fields may use `name` or `full_name` depending on engine output -- check both
- `test_deterministic_same_users`: exclude `computation_ms` and `reading_id` from comparison (they vary)
- DB verification uses `db_connection` fixture with raw SQL

**Checkpoint:**

- [ ] `test_multi_user_reading.py` has 15 tests
- Verify: `grep -c "def test_" integration/tests/test_multi_user_reading.py` -- 15

STOP if checkpoint fails

---

### Phase 6: Framework Integration & AI Tests (~60 min)

**Tasks:**

Create `integration/tests/test_framework_integration.py` with 3 test classes:

**Class `TestFrameworkOutput`** (10 tests) -- Marker: `@pytest.mark.framework`

| #   | Test Function                          | What It Verifies                                                                     |
| --- | -------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | `test_fc60_engine_produces_data`       | Time reading returns `fc60` with all fields non-None                                 |
| 2   | `test_numerology_engine_produces_data` | `numerology.life_path` > 0 and `interpretation` non-empty                            |
| 3   | `test_zodiac_engine_produces_data`     | `zodiac.sign`, `element`, `ruling_planet` all non-empty                              |
| 4   | `test_chinese_engine_produces_data`    | `chinese.animal`, `element`, `yin_yang` all non-empty                                |
| 5   | `test_ganzhi_engine_produces_output`   | Non-None `ganzhi` with `year_name` non-empty                                         |
| 6   | `test_fc60_extended_produces_output`   | Non-None `fc60_extended` with `stamp` non-empty                                      |
| 7   | `test_moon_engine_produces_output`     | Non-None `moon` with `phase_name` non-empty                                          |
| 8   | `test_chaldean_engine_produces_output` | Non-None `chaldean` with `value` > 0                                                 |
| 9   | `test_synchronicities_populated`       | `synchronicities` is list (length may vary)                                          |
| 10  | `test_all_engines_non_null_known_date` | For `DETERMINISTIC_DATETIME`, ALL 8 sections are non-None (comprehensive smoke test) |

**Class `TestAIMockCI`** (2 tests) -- Marker: `@pytest.mark.framework`

| #   | Test Function                             | What It Verifies                                                    |
| --- | ----------------------------------------- | ------------------------------------------------------------------- |
| 11  | `test_ai_mock_returns_deterministic_text` | With `ai_mock`, time reading `ai_interpretation` equals mock string |
| 12  | `test_ai_mock_group_interpretation`       | With `ai_mock`, multi-user `ai_interpretation` is not None          |

**Class `TestAIRealStaging`** (2 tests) -- Marker: `@pytest.mark.ai_real`

| #   | Test Function                         | What It Verifies                                                 |
| --- | ------------------------------------- | ---------------------------------------------------------------- |
| 13  | `test_ai_real_reading_interpretation` | With real key, `ai_interpretation` is string > 50 chars          |
| 14  | `test_ai_real_group_interpretation`   | With real key, multi-user `ai_interpretation` dict has narrative |

**Class `TestCrossReadingIntegrity`** (3 tests) -- Marker: `@pytest.mark.framework`

| #   | Test Function                               | What It Verifies                                                                          |
| --- | ------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 15  | `test_time_and_name_share_numerology`       | Same date's life path matches formula; name reading is independent                        |
| 16  | `test_multi_user_profiles_match_individual` | User's life_path in multi-user profile matches time reading life_path for same birth data |
| 17  | `test_reading_storage_types_distinct`       | After 4 reading types, history has 4+ readings with distinct `sign_type` values           |

**Class `TestReadingPerformance`** (5 tests) -- Marker: `@pytest.mark.slow`

| #   | Test Function                      | What It Verifies             |
| --- | ---------------------------------- | ---------------------------- |
| 18  | `test_time_reading_under_5s`       | Time reading < 5 seconds     |
| 19  | `test_name_reading_under_2s`       | Name reading < 2 seconds     |
| 20  | `test_question_reading_under_5s`   | Question reading < 5 seconds |
| 21  | `test_daily_reading_under_2s`      | Daily reading < 2 seconds    |
| 22  | `test_three_user_reading_under_8s` | 3-user reading < 8 seconds   |

**One additional test for multi-user engine output:**

| 23 | `test_multi_user_engine_produces_profiles` | Multi-user reading profiles each have non-empty `element`, `animal`, `life_path` > 0 |

**Key implementation details:**

- `ai_real` tests use: `@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Requires real Anthropic API key")`
- `TestCrossReadingIntegrity` creates one of each reading type and verifies numerical consistency
- Performance tests use `timed_request` helper from conftest
- All framework tests use `DETERMINISTIC_DATETIME` for reproducibility

**Checkpoint:**

- [ ] `test_framework_integration.py` has 23 tests across 5 classes
- Verify: `grep -c "def test_" integration/tests/test_framework_integration.py` -- 23

STOP if checkpoint fails

---

### Phase 7: Quality Pipeline & Final Verification (~30 min)

**Tasks:**

1. Lint and format all new test files:

   ```bash
   cd integration && python3 -m ruff check tests/test_time_reading.py tests/test_name_reading.py tests/test_question_reading.py tests/test_daily_reading.py tests/test_multi_user_reading.py tests/test_framework_integration.py --fix
   cd integration && python3 -m black tests/test_time_reading.py tests/test_name_reading.py tests/test_question_reading.py tests/test_daily_reading.py tests/test_multi_user_reading.py tests/test_framework_integration.py
   ```

2. Verify all files compile without syntax errors:

   ```bash
   python3 -c "
   import py_compile
   files = [
       'integration/tests/test_time_reading.py',
       'integration/tests/test_name_reading.py',
       'integration/tests/test_question_reading.py',
       'integration/tests/test_daily_reading.py',
       'integration/tests/test_multi_user_reading.py',
       'integration/tests/test_framework_integration.py',
   ]
   for f in files:
       py_compile.compile(f, doraise=True)
       print(f'  OK: {f}')
   print('All files compile')
   "
   ```

3. Verify test discovery (does not require running API/DB):

   ```bash
   python3 -m pytest integration/tests/ --collect-only -q
   ```

   Expected: 88+ new tests discovered (15+13+12+10+15+23 = 88), plus existing tests.

4. Verify existing tests are not broken (no conftest import conflicts):

   ```bash
   python3 -m pytest integration/tests/test_api_oracle.py integration/tests/test_api_health.py --collect-only -q
   ```

5. Run full suite (requires API + DB):

   ```bash
   # All tests except AI-real and slow
   python3 -m pytest integration/tests/ -v -m "not ai_real and not slow" --tb=short

   # Only new reading tests
   python3 -m pytest integration/tests/ -v -m reading --tb=short

   # Only framework tests
   python3 -m pytest integration/tests/ -v -m framework --tb=short

   # Full suite including slow
   python3 -m pytest integration/tests/ -v --tb=short
   ```

6. Git commit:

   ```bash
   git add integration/tests/test_time_reading.py \
           integration/tests/test_name_reading.py \
           integration/tests/test_question_reading.py \
           integration/tests/test_daily_reading.py \
           integration/tests/test_multi_user_reading.py \
           integration/tests/test_framework_integration.py \
           integration/tests/conftest.py
   git commit -m "[integration] add 88 reading type integration tests for all 5 reading flows (#session-42)

   - 6 new test files: time (15), name (13), question (12), daily (10), multi-user (15), framework (23)
   - AI mock fixture for CI without ANTHROPIC_API_KEY
   - Framework output verification for all engines
   - Cross-reading data integrity checks
   - Performance sanity tests for each reading type
   - Conftest enhancements: reading_helper, assertion utilities, constants"
   ```

**Checkpoint:**

- [ ] All 6 files pass `ruff check` and `black`
- [ ] All files compile without syntax errors
- [ ] Test discovery finds 88+ new tests
- [ ] Existing integration tests still discoverable
- [ ] Full test suite passes (with API + DB running)
- [ ] Git committed with session tag

STOP if checkpoint fails

---

## TEST SUMMARY

| File                            | Test Count | Marker                         | Focus                                                          |
| ------------------------------- | ---------- | ------------------------------ | -------------------------------------------------------------- |
| `test_time_reading.py`          | 15         | `reading`                      | All 12 response sections, data types, determinism, persistence |
| `test_name_reading.py`          | 13         | `reading`                      | Numerology values, letter analysis, edge cases                 |
| `test_question_reading.py`      | 12         | `reading`                      | Answer validation, confidence, determinism, master numbers     |
| `test_daily_reading.py`         | 10         | `reading`                      | Caching, date divergence, format, non-persistence              |
| `test_multi_user_reading.py`    | 15         | `reading`                      | 3-user flow, pairwise math, group energy/dynamics, DB          |
| `test_framework_integration.py` | 23         | `framework`, `ai_real`, `slow` | Engine output, AI mock/real, cross-reading, performance        |
| **Total**                       | **88**     |                                |                                                                |

---

## ACCEPTANCE CRITERIA

- [ ] 6 new test files exist in `integration/tests/`
- [ ] 88 tests discoverable via `pytest --collect-only`
- [ ] Time reading tests verify all 12 response sections with data type validation
- [ ] Name reading tests verify numerology is computed for the submitted name (destiny, soul_urge, personality, letters)
- [ ] Question reading tests verify answer in {yes, no, maybe}, deterministic sign number, master number rule
- [ ] Daily reading tests verify caching (same day = identical), different-day divergence, non-persistence
- [ ] Multi-user tests verify 3-user flow with individual profiles, pairwise count C(n,2), group energy/dynamics
- [ ] Framework tests verify all 8 engine sections produce non-null data for known dates
- [ ] AI mock fixture allows tests to pass without `ANTHROPIC_API_KEY`
- [ ] AI real tests guarded by `@pytest.mark.ai_real` (skipped in CI)
- [ ] Cross-reading integrity verified: numerology consistent across reading types for same birth data
- [ ] Performance tests confirm each reading type within documented limits
- [ ] No regressions in existing 56+ integration tests
- [ ] All test data uses `IntTest_` prefix (cleaned by `cleanup_test_data`)
- [ ] All files pass `ruff check` and `black`
- Verify all:
  ```bash
  test -f integration/tests/test_time_reading.py && \
  test -f integration/tests/test_name_reading.py && \
  test -f integration/tests/test_question_reading.py && \
  test -f integration/tests/test_daily_reading.py && \
  test -f integration/tests/test_multi_user_reading.py && \
  test -f integration/tests/test_framework_integration.py && \
  python3 -m pytest integration/tests/ --collect-only -q 2>&1 | tail -3 && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                  | Expected Behavior                                                                                   | Recovery                                                                                                                  |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| API not running on localhost:8000         | `ConnectionError` at test runtime. All tests fail at HTTP layer.                                    | Start API: `make dev-api` or `docker-compose up api`. Not a test bug.                                                     |
| PostgreSQL not running                    | `db_session`/`db_connection` fixtures fail at setup.                                                | Start DB: `docker-compose up postgres`. Not a test bug.                                                                   |
| `ANTHROPIC_API_KEY` not set               | AI interpretation returns None in responses. Tests assert `None or str`. `ai_real` tests auto-skip. | Set key in `.env` for staging runs. CI runs without key are correct.                                                      |
| `API_SECRET_KEY` not set or wrong         | `api_client` gets 401/403 on every request. All tests fail.                                         | Set correct `API_SECRET_KEY` in `.env` matching running API.                                                              |
| Reading endpoint returns 500              | Test assertion fails with status code + body.                                                       | Check API server logs for stack trace. Fix endpoint bug.                                                                  |
| `fc60` or `numerology` is None            | `assert_fc60_valid()` or `assert_numerology_valid()` raises AssertionError.                         | Verify engine imports in `oracle_reading.py`. Check `sys.path` shim.                                                      |
| `ganzhi` or `fc60_extended` is None       | Framework test guards with `if data.get("section") is not None:`. Test may pass vacuously.          | Verify `engines/oracle.py:read_sign()` populates `systems` dict.                                                          |
| `test_deterministic_same_input` fails     | Floating point drift or timestamp in output.                                                        | Exclude `generated_at` and `ai_interpretation` from equality comparison.                                                  |
| `test_daily_does_not_store_reading` fails | Daily endpoint now persists to DB.                                                                  | Check `api/app/routers/oracle.py` daily handler. Update test if persistence was intentionally added.                      |
| `test_master_number_produces_maybe` fails | Crafted question's alpha count doesn't reduce to master number.                                     | Verify: `sum(1 for c in question if c.isalpha())` -> `numerology_reduce(count)` -> 11/22/33. Adjust question text.        |
| Multi-user 422 for valid 3 users          | Validation model rejects input.                                                                     | Check `MultiUserInput` Pydantic model birth_year range or name validation.                                                |
| Performance tests fail                    | Server cold start or resource contention.                                                           | Run warm-up request first, then re-run. Increase timeout if consistent.                                                   |
| `ai_mock` fixture fails to patch          | Engine module not importable from test context.                                                     | Verify `sys.path` setup in conftest matches oracle service directory structure. Fallback: AI is already None without key. |
| conftest import breaks existing tests     | New helpers or fixtures shadow existing names.                                                      | Use unique names for new fixtures. Run `pytest --collect-only` to catch import errors early.                              |

---

## DESIGN DECISIONS

| Decision                                      | Choice                                    | Rationale                                                                                                                                                                                               |
| --------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6 separate test files vs 1 monolith           | 6 files                                   | Isolation: `pytest test_time_reading.py` alone. Clarity: each file documents one reading type's contract. Parallel execution possible.                                                                  |
| AI mock strategy                              | Monkeypatch + graceful None assertion     | Code already handles missing API keys (try/except -> None). Hard SDK mocking is brittle. `ai_mock` patches at engine level for deterministic assertions. Tests without mock still pass (None is valid). |
| `@pytest.mark` per category                   | `reading`, `framework`, `ai_real`, `slow` | Selective execution: `pytest -m reading` for reading tests only. CI excludes `ai_real` and `slow`.                                                                                                      |
| Conftest assertion helpers vs pytest fixtures | Functions, not fixtures                   | Assertion helpers called explicitly make test logic transparent. No hidden setup/teardown.                                                                                                              |
| `reading_helper` as fixture                   | Class-based fixture with methods          | Avoids repetitive HTTP boilerplate in every test. Methods assert 200 status, allowing tests to focus on response validation.                                                                            |
| Master number test crafting                   | Find question with 11 alpha chars         | Tests the specific `get_question_sign` logic path where master numbers produce "maybe". Crafted, not random.                                                                                            |
| `test_daily_does_not_store_reading` approach  | Count readings before/after               | Verifies GET semantics (read-only). If daily endpoint adds persistence, test catches the change.                                                                                                        |
| Framework field guards                        | `if data.get("section") is not None:`     | Some sections are nullable depending on engine config/input. Guards prevent false failures while still verifying structure when present.                                                                |

---

## HANDOFF

**Created:**

- `integration/tests/test_time_reading.py` (15 tests)
- `integration/tests/test_name_reading.py` (13 tests)
- `integration/tests/test_question_reading.py` (12 tests)
- `integration/tests/test_daily_reading.py` (10 tests)
- `integration/tests/test_multi_user_reading.py` (15 tests)
- `integration/tests/test_framework_integration.py` (23 tests)

**Modified:**

- `integration/tests/conftest.py` (AI mock, reading helper, assertion utilities, constants, timed_request)

**Next session needs:**

- **Session 43 (Playwright E2E Tests)** depends on:
  - All 88 reading integration tests passing -- confirms API endpoints return correct, complete data
  - AI mock infrastructure in conftest (reusable pattern for frontend E2E mocking)
  - Performance baselines from `TestReadingPerformance` (E2E tests measure frontend overhead on top)
  - `reading_helper` fixture pattern (adaptable to Playwright page object helpers)
  - Session 43 must NOT duplicate API response validation (already done here)
- **Session 44 (Optimization & CI Pipeline)** depends on:
  - Full integration test suite as CI gate (Session 42 adds the missing reading coverage)
  - `@pytest.mark` infrastructure for selective test runs in CI
  - `NPS_MOCK_AI` / `ai_mock` pattern for CI runs without Anthropic key
  - Performance test baselines to detect regressions
- **Session 45 (Deployment & Production Readiness)** depends on:
  - Complete integration test coverage across all reading types (Session 42)
  - CI-compatible test suite (no external API dependencies for `not ai_real` tests)
  - Known response contracts documented via test assertions (deployment verification)
