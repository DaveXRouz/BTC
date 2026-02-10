"""Tests for the 5 typed reading functions (Session 7).

Covers: Time, Name, Question, Daily, and Multi-User readings.
"""

import unittest
from datetime import datetime, timedelta

import oracle_service  # noqa: F401 — triggers sys.path shim

from oracle_service.models.reading_types import (
    MultiUserResult,
    ReadingResult,
    ReadingType,
    UserProfile,
)
from oracle_service.framework_bridge import (
    generate_time_reading,
    generate_name_reading,
    generate_question_reading,
    generate_daily_reading,
    generate_multi_user_reading,
)
from numerology_ai_framework.personal.numerology_engine import NumerologyEngine

# ── Shared test fixtures ──

TEST_USER_ALICE = UserProfile(
    user_id=1,
    full_name="Alice Johnson",
    birth_day=15,
    birth_month=7,
    birth_year=1990,
    mother_name="Barbara Johnson",
    gender="female",
    latitude=40.7,
    longitude=-74.0,
    heart_rate_bpm=68,
    timezone_hours=-5,
    timezone_minutes=0,
)

TEST_USER_BOB = UserProfile(
    user_id=2,
    full_name="Bob Smith",
    birth_day=1,
    birth_month=1,
    birth_year=2000,
    gender="male",
)

TEST_USER_CHARLIE = UserProfile(
    user_id=3,
    full_name="Charlie Brown",
    birth_day=22,
    birth_month=11,
    birth_year=1985,
    gender="male",
    latitude=51.5,
    longitude=-0.1,
)

TEST_USER_DIANA = UserProfile(
    user_id=4,
    full_name="Diana Ross",
    birth_day=10,
    birth_month=3,
    birth_year=1975,
    gender="female",
)

TEST_USER_EDGAR = UserProfile(
    user_id=5,
    full_name="Edgar Allan",
    birth_day=19,
    birth_month=1,
    birth_year=1809,
    gender="male",
)

FIXED_DATE = datetime(2026, 2, 11, 14, 30, 0)


class TestTimeReading(unittest.TestCase):
    """Time reading: sign is HH:MM:SS."""

    def test_time_reading_basic(self):
        result = generate_time_reading(TEST_USER_ALICE, 14, 30, 0, FIXED_DATE)
        self.assertIsInstance(result, ReadingResult)
        self.assertEqual(result.reading_type, ReadingType.TIME)
        self.assertEqual(result.user_id, 1)
        self.assertEqual(result.sign_value, "14:30:00")
        self.assertIsInstance(result.framework_output, dict)
        self.assertIn("fc60_stamp", result.framework_output)
        self.assertGreater(result.confidence_score, 0)

    def test_time_reading_midnight(self):
        result = generate_time_reading(TEST_USER_BOB, 0, 0, 0, FIXED_DATE)
        self.assertEqual(result.sign_value, "00:00:00")
        self.assertIsInstance(result.framework_output, dict)
        self.assertIn("numerology", result.framework_output)

    def test_time_reading_end_of_day(self):
        result = generate_time_reading(TEST_USER_BOB, 23, 59, 59, FIXED_DATE)
        self.assertEqual(result.sign_value, "23:59:59")
        self.assertIsInstance(result.framework_output, dict)

    def test_time_reading_default_date(self):
        result = generate_time_reading(TEST_USER_ALICE, 12, 0, 0)
        self.assertIsInstance(result, ReadingResult)
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(result.framework_output["current"]["date"], today)

    def test_time_reading_invalid_hour(self):
        with self.assertRaises(ValueError):
            generate_time_reading(TEST_USER_BOB, 25, 0, 0)

    def test_time_reading_invalid_minute(self):
        with self.assertRaises(ValueError):
            generate_time_reading(TEST_USER_BOB, 12, 60, 0)


class TestNameReading(unittest.TestCase):
    """Name reading: sign is a name string."""

    def test_name_reading_basic(self):
        result = generate_name_reading(TEST_USER_ALICE, "Alexander", FIXED_DATE)
        self.assertIsInstance(result, ReadingResult)
        self.assertEqual(result.reading_type, ReadingType.NAME)
        self.assertEqual(result.sign_value, "Alexander")
        self.assertIn("numerology", result.framework_output)

    def test_name_reading_overrides_user_name(self):
        result = generate_name_reading(TEST_USER_ALICE, "Bob", FIXED_DATE)
        self.assertEqual(result.framework_output["person"]["name"], "Bob")
        expected_expr = NumerologyEngine.expression_number("Bob")
        self.assertEqual(result.framework_output["numerology"]["expression"], expected_expr)
        # Birth data still from Alice
        self.assertEqual(result.framework_output["person"]["birthdate"], "1990-07-15")

    def test_name_reading_persian_name(self):
        result = generate_name_reading(TEST_USER_BOB, "\u0639\u0644\u06cc", FIXED_DATE)
        self.assertIsInstance(result, ReadingResult)
        self.assertEqual(result.sign_value, "\u0639\u0644\u06cc")

    def test_name_reading_empty_raises(self):
        with self.assertRaises(ValueError):
            generate_name_reading(TEST_USER_BOB, "")

    def test_name_reading_whitespace_raises(self):
        with self.assertRaises(ValueError):
            generate_name_reading(TEST_USER_BOB, "   ")


class TestQuestionReading(unittest.TestCase):
    """Question reading: sign is a question string."""

    def test_question_reading_basic(self):
        result = generate_question_reading(TEST_USER_ALICE, "Will I succeed?", FIXED_DATE)
        self.assertIsInstance(result, ReadingResult)
        self.assertEqual(result.reading_type, ReadingType.QUESTION)
        self.assertEqual(result.sign_value, "Will I succeed?")
        self.assertIn("question_vibration", result.framework_output)
        self.assertIsInstance(result.framework_output["question_vibration"], int)

    def test_question_reading_vibration_deterministic(self):
        r1 = generate_question_reading(TEST_USER_BOB, "Will I get the job?", FIXED_DATE)
        r2 = generate_question_reading(TEST_USER_BOB, "Will I get the job?", FIXED_DATE)
        self.assertEqual(
            r1.framework_output["question_vibration"],
            r2.framework_output["question_vibration"],
        )

    def test_question_reading_empty_string(self):
        with self.assertRaises(ValueError):
            generate_question_reading(TEST_USER_BOB, "", FIXED_DATE)

    def test_question_reading_numbers_only(self):
        result = generate_question_reading(TEST_USER_BOB, "12345", FIXED_DATE)
        self.assertEqual(result.framework_output["question_vibration"], 0)


class TestDailyReading(unittest.TestCase):
    """Daily reading: sign is today's date."""

    def test_daily_reading_basic(self):
        result = generate_daily_reading(TEST_USER_ALICE, FIXED_DATE)
        self.assertIsInstance(result, ReadingResult)
        self.assertEqual(result.reading_type, ReadingType.DAILY)
        self.assertIsNotNone(result.daily_insights)

    def test_daily_reading_has_all_insight_keys(self):
        result = generate_daily_reading(TEST_USER_ALICE, FIXED_DATE)
        expected_keys = {
            "suggested_activities",
            "energy_forecast",
            "lucky_hours",
            "focus_area",
            "element_of_day",
        }
        self.assertEqual(set(result.daily_insights.keys()), expected_keys)
        self.assertIsInstance(result.daily_insights["suggested_activities"], list)
        self.assertIsInstance(result.daily_insights["lucky_hours"], list)
        self.assertIsInstance(result.daily_insights["energy_forecast"], str)
        self.assertIsInstance(result.daily_insights["focus_area"], str)
        self.assertIsInstance(result.daily_insights["element_of_day"], str)

    def test_daily_reading_future_date(self):
        future = FIXED_DATE + timedelta(days=7)
        result = generate_daily_reading(TEST_USER_BOB, future)
        self.assertIsInstance(result, ReadingResult)
        self.assertIn(future.strftime("%Y-%m-%d"), result.sign_value)

    def test_daily_reading_uses_noon(self):
        result = generate_daily_reading(TEST_USER_ALICE, FIXED_DATE)
        ganzhi = result.framework_output.get("ganzhi", {})
        self.assertIn("hour", ganzhi, "Hour ganzhi should be present (has_time=True)")
        # Hour 12 maps to branch 6 (Horse) in Ganzhi
        self.assertEqual(ganzhi["hour"]["animal_name"], "Horse")

    def test_daily_reading_lucky_hours_count(self):
        result = generate_daily_reading(TEST_USER_ALICE, FIXED_DATE)
        lucky = result.daily_insights["lucky_hours"]
        self.assertGreaterEqual(len(lucky), 1)
        self.assertLessEqual(len(lucky), 3)
        for h in lucky:
            self.assertIn(h, range(24))


class TestMultiUserReading(unittest.TestCase):
    """Multi-user reading: 2-5 users with compatibility."""

    def test_multi_user_two_users(self):
        result = generate_multi_user_reading(
            [TEST_USER_ALICE, TEST_USER_BOB],
            reading_type=ReadingType.TIME,
            sign_value="14:30:00",
            target_date=FIXED_DATE,
        )
        self.assertIsInstance(result, MultiUserResult)
        self.assertEqual(len(result.individual_readings), 2)
        self.assertEqual(len(result.pairwise_compatibility), 1)
        self.assertGreater(result.group_harmony_score, 0)

    def test_multi_user_five_users(self):
        users = [
            TEST_USER_ALICE,
            TEST_USER_BOB,
            TEST_USER_CHARLIE,
            TEST_USER_DIANA,
            TEST_USER_EDGAR,
        ]
        result = generate_multi_user_reading(
            users,
            reading_type=ReadingType.TIME,
            sign_value="12:00:00",
            target_date=FIXED_DATE,
        )
        self.assertEqual(len(result.individual_readings), 5)
        self.assertEqual(len(result.pairwise_compatibility), 10)
        self.assertIsInstance(result.group_element_balance, dict)
        self.assertIsInstance(result.group_summary, str)

    def test_multi_user_one_user_fails(self):
        with self.assertRaises(ValueError):
            generate_multi_user_reading([TEST_USER_ALICE])

    def test_multi_user_six_users_fails(self):
        users = [
            TEST_USER_ALICE,
            TEST_USER_BOB,
            TEST_USER_CHARLIE,
            TEST_USER_DIANA,
            TEST_USER_EDGAR,
            UserProfile(
                user_id=6,
                full_name="Frank",
                birth_day=5,
                birth_month=5,
                birth_year=1995,
            ),
        ]
        with self.assertRaises(ValueError):
            generate_multi_user_reading(users)

    def test_multi_user_daily_type(self):
        result = generate_multi_user_reading(
            [TEST_USER_ALICE, TEST_USER_BOB],
            reading_type=ReadingType.DAILY,
            target_date=FIXED_DATE,
        )
        self.assertEqual(len(result.individual_readings), 2)
        for r in result.individual_readings:
            self.assertEqual(r.reading_type, ReadingType.DAILY)


class TestUserProfileModel(unittest.TestCase):
    """UserProfile dataclass and to_framework_kwargs."""

    def test_to_framework_kwargs(self):
        kwargs = TEST_USER_ALICE.to_framework_kwargs()
        self.assertEqual(kwargs["full_name"], "Alice Johnson")
        self.assertEqual(kwargs["birth_day"], 15)
        self.assertEqual(kwargs["birth_month"], 7)
        self.assertEqual(kwargs["birth_year"], 1990)
        self.assertEqual(kwargs["mother_name"], "Barbara Johnson")
        self.assertEqual(kwargs["gender"], "female")
        self.assertAlmostEqual(kwargs["latitude"], 40.7)
        self.assertAlmostEqual(kwargs["longitude"], -74.0)
        self.assertEqual(kwargs["heart_rate_bpm"], 68)
        self.assertEqual(kwargs["tz_hours"], -5)
        self.assertEqual(kwargs["tz_minutes"], 0)
        self.assertEqual(kwargs["numerology_system"], "pythagorean")

    def test_minimal_profile(self):
        user = UserProfile(
            user_id=99,
            full_name="Minimal",
            birth_day=1,
            birth_month=1,
            birth_year=2000,
        )
        kwargs = user.to_framework_kwargs()
        self.assertIsNone(kwargs["mother_name"])
        self.assertIsNone(kwargs["gender"])
        self.assertEqual(kwargs["tz_hours"], 0)


if __name__ == "__main__":
    unittest.main()
