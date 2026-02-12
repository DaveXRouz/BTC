"""
Tests for AI Integration (Session 13)
=======================================
7 test classes, 27+ tests covering:
  - Prompt building (build_reading_prompt, build_multi_user_prompt)
  - System prompts (EN/FA, signal hierarchy, locale fallback)
  - AI client retry logic (rate limit, auth error, exhaustion)
  - Response parsing (9 sections EN/FA, fallback, partial)
  - Interpreter (AI success, fallback, FA, multi-user, to_dict)
  - Fallback (translation sections, synthesis, minimal)
  - Cache key (deterministic, locale differentiation)

All AI calls mocked -- zero real API calls.
"""

import json
import unittest
from unittest.mock import patch, MagicMock


from oracle_service.ai_prompt_builder import (
    build_reading_prompt,
    build_multi_user_prompt,
    _safe_get,
)
from engines.ai_client import (
    generate,
    generate_reading,
    clear_cache,
    reset_availability,
)
from engines.ai_interpreter import (
    interpret_reading,
    interpret_multi_user,
    ReadingInterpretation,
    MultiUserInterpretation,
    _parse_sections,
    _build_fallback,
    _make_daily_cache_key,
)
from engines.prompt_templates import (
    get_system_prompt,
    WISDOM_SYSTEM_PROMPT_EN,
    WISDOM_SYSTEM_PROMPT_FA,
    FC60_PRESERVED_TERMS,
    build_prompt,
)

# ════════════════════════════════════════════════════════════
# Test fixtures — framework output format
# ════════════════════════════════════════════════════════════

SAMPLE_FRAMEWORK_READING = {
    "person": {
        "name": "Alice Johnson",
        "birthdate": "1990-07-15",
        "age_years": 35,
        "age_days": 12993,
    },
    "fc60_stamp": {
        "fc60": "LU-OX-OXWA",
        "j60": "TIFI-DRMT-GOMT-RAFI",
        "y60": "SNWA",
        "chk": "OK",
        "iso": "2026-02-09T14:30:00-05:00",
    },
    "birth": {
        "jdn": 2448090,
        "weekday": "Sunday",
        "planet": "Sun",
    },
    "current": {
        "date": "2026-02-09",
        "weekday": "Monday",
        "planet": "Moon",
        "domain": "Emotion",
    },
    "numerology": {
        "life_path": {
            "number": 5,
            "title": "The Explorer",
            "message": "Freedom and change are your driving forces.",
        },
        "expression": 7,
        "soul_urge": 3,
        "personality": 4,
        "personal_year": 3,
        "personal_month": 5,
        "personal_day": 7,
        "gender_polarity": {"label": "Feminine"},
        "mother_influence": 6,
    },
    "moon": {
        "phase_name": "Waxing Gibbous",
        "emoji": "\U0001f314",
        "age": 12.3,
        "illumination": 87,
        "energy": "Building",
        "best_for": "Refining plans, detail work",
        "avoid": "Starting new projects",
    },
    "ganzhi": {
        "year": {
            "traditional_name": "Bing-Wu",
            "element": "Fire",
            "animal_name": "Horse",
        },
        "day": {
            "gz_token": "Geng-Xu",
            "element": "Metal",
            "animal_name": "Dog",
        },
        "hour": {
            "animal_name": "Goat",
        },
    },
    "heartbeat": {
        "bpm": 68,
        "bpm_source": "actual",
        "element": "Water",
        "total_lifetime_beats": 2_450_000_000,
        "rhythm_token": "WA-SNFI",
    },
    "location": {
        "latitude": 40.7,
        "lat_hemisphere": "N",
        "longitude": -74.0,
        "lon_hemisphere": "W",
        "element": "Metal",
    },
    "patterns": {
        "count": 2,
        "detected": [
            {
                "type": "repeated_animal",
                "strength": "high",
                "message": "Horse appears 2 times (year + element).",
            },
            {
                "type": "element_dominance",
                "strength": "medium",
                "message": "Metal appears 3 times across dimensions.",
            },
        ],
    },
    "confidence": {
        "score": 95,
        "level": "very_high",
        "factors": ["name", "DOB", "time", "location", "heartbeat", "mother"],
    },
    "synthesis": "Alice Johnson has a Life Path of 5 (Explorer). Today is Monday (Moon, Emotion). Horse appears 2 times. Metal dominates.",
    "translation": {
        "header": "ALICE JOHNSON",
        "universal_address": "FC60: LU-OX-OXWA",
        "core_identity": "Life Path 5 - The Explorer",
        "right_now": "Monday, Moon day, Emotion domain",
        "patterns": "Horse x2, Metal x3",
        "message": "The Ox and Horse both appear twice, suggesting patience and forward motion.",
        "advice": "1. Move with intention\n2. Share what you know\n3. Trust your emotional compass",
        "caution": "Watch for overwhelm with Metal dominance.",
        "footer": "Confidence: 95% (very high)",
        "full_text": "ALICE JOHNSON\nFC60: LU-OX-OXWA\n...",
    },
}

SAMPLE_MINIMAL_READING = {
    "person": {
        "name": "Bob Smith",
        "birthdate": "1985-03-20",
        "age_years": 40,
    },
    "fc60_stamp": {
        "fc60": "RA-TI-DRFI",
        "j60": "MOER-OXWA",
        "y60": "OXFI",
        "chk": "OK",
    },
    "birth": {
        "jdn": 2446147,
        "weekday": "Wednesday",
        "planet": "Mercury",
    },
    "current": {
        "date": "2026-02-09",
        "weekday": "Monday",
        "planet": "Moon",
        "domain": "Emotion",
    },
    "numerology": {
        "life_path": {
            "number": 1,
            "title": "The Leader",
            "message": "Independence and initiative define you.",
        },
        "expression": 3,
        "soul_urge": 9,
        "personality": 3,
        "personal_year": 6,
        "personal_month": 8,
        "personal_day": 4,
    },
    "moon": {
        "phase_name": "Waxing Gibbous",
        "emoji": "\U0001f314",
        "age": 12.3,
        "illumination": 87,
        "energy": "Building",
        "best_for": "Refining plans",
        "avoid": "Starting new projects",
    },
    "ganzhi": {
        "year": {
            "traditional_name": "Yi-Chou",
            "element": "Wood",
            "animal_name": "Ox",
        },
        "day": {
            "gz_token": "Ren-Chen",
            "element": "Water",
            "animal_name": "Dragon",
        },
    },
    "heartbeat": {
        "bpm": 72,
        "bpm_source": "estimated",
        "element": "Earth",
        "total_lifetime_beats": 2_100_000_000,
        "rhythm_token": "ER-RAWA",
    },
    "location": None,
    "patterns": {
        "count": 0,
        "detected": [],
    },
    "confidence": {
        "score": 80,
        "level": "high",
        "factors": ["name", "DOB"],
    },
    "synthesis": "Bob Smith has Life Path 1 (Leader). Today is Monday (Moon).",
}


SAMPLE_AI_RESPONSE_EN = """READING FOR ALICE JOHNSON
Date: 2026-02-09
Confidence: 95% (very high)

---

YOUR UNIVERSAL ADDRESS

FC60: LU-OX-OXWA
J60: TIFI-DRMT-GOMT-RAFI

---

CORE IDENTITY

Your Life Path is 5 -- the Explorer. Freedom and change are your driving forces.

---

RIGHT NOW

Today is Monday, a Moon day. The domain is Emotion. The Waxing Gibbous moon is building.

---

PATTERNS DETECTED

The Horse appears 2 times in your chart. Metal appears 3 times.

---

THE MESSAGE

The numbers suggest patience and forward motion. Horse energy brings determination while Metal provides structure.

---

TODAY'S ADVICE

1. Move with intention -- the Horse energy supports deliberate action.
2. Share what you know -- Expression 7 and Moon day favor communication.
3. Trust your emotional compass -- the Moon domain amplifies intuition.

---

CAUTION

Watch for overwhelm. Metal dominance (3x) can create rigidity. Balance with Water energy.

---

Confidence: 95% (very high)
Data sources: FC60 stamp, Pythagorean numerology, lunar phase, heartbeat, location, Ganzhi
Disclaimer: This reading suggests patterns, not predictions."""


SAMPLE_AI_RESPONSE_FA = """\u062e\u0648\u0627\u0646\u0634 \u0628\u0631\u0627\u06cc ALICE JOHNSON
\u062a\u0627\u0631\u06cc\u062e: 2026-02-09

---

\u0622\u062f\u0631\u0633 \u062c\u0647\u0627\u0646\u06cc

FC60: LU-OX-OXWA

---

\u0647\u0648\u06cc\u062a \u0627\u0635\u0644\u06cc

Life Path \u0634\u0645\u0627 5 \u0627\u0633\u062a -- Explorer.

---

\u0627\u06a9\u0646\u0648\u0646

\u0627\u0645\u0631\u0648\u0632 \u062f\u0648\u0634\u0646\u0628\u0647 \u0627\u0633\u062a.

---

\u0627\u0644\u06af\u0648\u0647\u0627

Horse 2 \u0628\u0627\u0631 \u062a\u06a9\u0631\u0627\u0631 \u0634\u062f\u0647.

---

\u067e\u06cc\u0627\u0645

\u0627\u0639\u062f\u0627\u062f \u0646\u0634\u0627\u0646 \u0645\u06cc\u200c\u062f\u0647\u0646\u062f \u06a9\u0647 \u0635\u0628\u0631 \u0648 \u062d\u0631\u06a9\u062a \u0631\u0648 \u0628\u0647 \u062c\u0644\u0648 \u0645\u0647\u0645 \u0627\u0633\u062a.

---

\u062a\u0648\u0635\u06cc\u0647

1. \u0628\u0627 \u0647\u062f\u0641 \u062d\u0631\u06a9\u062a \u06a9\u0646\u06cc\u062f.

---

\u0647\u0634\u062f\u0627\u0631

\u0645\u0631\u0627\u0642\u0628 \u0641\u0634\u0627\u0631 \u0628\u0627\u0634\u06cc\u062f.

---

\u0627\u0637\u0645\u06cc\u0646\u0627\u0646: 95%
\u0645\u0646\u0627\u0628\u0639 \u062f\u0627\u062f\u0647: FC60"""


# ════════════════════════════════════════════════════════════
# Test Classes
# ════════════════════════════════════════════════════════════


class TestPromptBuilder(unittest.TestCase):
    """Tests for ai_prompt_builder.py."""

    def test_build_full_reading_prompt(self):
        """Full reading prompt includes all 12 data sections."""
        prompt = build_reading_prompt(SAMPLE_FRAMEWORK_READING)
        self.assertIn("READING TYPE: daily", prompt)
        self.assertIn("--- PERSON ---", prompt)
        self.assertIn("Alice Johnson", prompt)
        self.assertIn("--- FC60 STAMP ---", prompt)
        self.assertIn("LU-OX-OXWA", prompt)
        self.assertIn("--- BIRTH DATA ---", prompt)
        self.assertIn("--- CURRENT DATA ---", prompt)
        self.assertIn("--- NUMEROLOGY ---", prompt)
        self.assertIn("Life Path: 5", prompt)
        self.assertIn("--- MOON ---", prompt)
        self.assertIn("Waxing Gibbous", prompt)
        self.assertIn("--- GANZHI ---", prompt)
        self.assertIn("--- HEARTBEAT ---", prompt)
        self.assertIn("--- LOCATION ---", prompt)
        self.assertIn("40.7", prompt)
        self.assertIn("--- PATTERNS ---", prompt)
        self.assertIn("--- CONFIDENCE ---", prompt)
        self.assertIn("--- FRAMEWORK SYNTHESIS ---", prompt)

    def test_build_minimal_reading_prompt(self):
        """Minimal reading prompt shows 'not provided' for missing sections."""
        prompt = build_reading_prompt(SAMPLE_MINIMAL_READING)
        self.assertIn("Bob Smith", prompt)
        self.assertIn("--- LOCATION ---", prompt)
        self.assertIn("not provided", prompt)
        # No hour in ganzhi
        self.assertNotIn("Hour:", prompt.split("--- HEARTBEAT ---")[0].split("--- GANZHI ---")[1])

    def test_build_question_prompt(self):
        """Question type includes user question text."""
        prompt = build_reading_prompt(
            SAMPLE_FRAMEWORK_READING,
            reading_type="question",
            question="Will I find success in my new career?",
        )
        self.assertIn("READING TYPE: question", prompt)
        self.assertIn("QUESTION: Will I find success", prompt)

    def test_build_multi_user_prompt(self):
        """Multi-user prompt includes both user readings."""
        prompt = build_multi_user_prompt(
            [SAMPLE_FRAMEWORK_READING, SAMPLE_MINIMAL_READING],
            ["Alice", "Bob"],
        )
        self.assertIn("READING TYPE: multi", prompt)
        self.assertIn("USER COUNT: 2", prompt)
        self.assertIn("USER 1: Alice", prompt)
        self.assertIn("USER 2: Bob", prompt)
        self.assertIn("GROUP ANALYSIS", prompt)

    def test_safe_get_nested(self):
        """_safe_get traverses nested dicts safely."""
        data = {"a": {"b": {"c": "found"}}}
        self.assertEqual(_safe_get(data, "a", "b", "c"), "found")
        self.assertEqual(_safe_get(data, "a", "x", "c"), "not provided")
        self.assertEqual(_safe_get(data, "missing", default="N/A"), "N/A")


class TestSystemPrompt(unittest.TestCase):
    """Tests for prompt_templates.py system prompts."""

    def test_en_system_prompt_content(self):
        """EN system prompt contains rules, tone, 9-section structure."""
        prompt = get_system_prompt("en")
        self.assertIn("Wisdom", prompt)
        self.assertIn("RULES", prompt)
        self.assertIn("TONE", prompt)
        self.assertIn("READING STRUCTURE", prompt)
        self.assertIn("Header", prompt)
        self.assertIn("Universal Address", prompt)
        self.assertIn("Core Identity", prompt)
        self.assertIn("The Message", prompt)
        self.assertIn("Caution", prompt)
        self.assertIn("Footer", prompt)
        self.assertIn("FC60", prompt)

    def test_fa_system_prompt_content(self):
        """FA system prompt contains Persian instructions with FC60 terms in English."""
        prompt = get_system_prompt("fa")
        # Persian content
        self.assertIn("\u062e\u0631\u062f", prompt)  # "Wisdom" in Persian
        self.assertIn("\u0642\u0648\u0627\u0646\u06cc\u0646", prompt)  # "Rules"
        # FC60 terms preserved in English
        self.assertIn("FC60", prompt)
        self.assertIn("Life Path", prompt)
        self.assertIn("Soul Urge", prompt)
        self.assertIn("Wu Xing", prompt)

    def test_system_prompt_includes_signal_hierarchy(self):
        """EN system prompt contains signal hierarchy."""
        prompt = get_system_prompt("en")
        self.assertIn("SIGNAL HIERARCHY", prompt)
        self.assertIn("Very High", prompt)
        self.assertIn("Repeated animals", prompt)

    def test_unknown_locale_defaults_to_en(self):
        """Unknown locale falls back to English prompt."""
        prompt = get_system_prompt("de")
        self.assertEqual(prompt, WISDOM_SYSTEM_PROMPT_EN)


class TestAIClientRetry(unittest.TestCase):
    """Tests for ai_client.py retry logic."""

    def setUp(self):
        reset_availability()
        clear_cache()

    def tearDown(self):
        reset_availability()
        clear_cache()

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._enforce_rate_limit")
    @patch("engines.ai_client._get_client")
    def test_retry_on_rate_limit(self, mock_client_fn, mock_rate, mock_avail):
        """Retries once on rate limit error, then succeeds."""
        import engines.ai_client as client_mod

        mock_client = MagicMock()
        # First call raises a retryable error, second succeeds
        rate_limit_exc = Exception("rate limit exceeded")
        # Make it retryable by patching _is_retryable
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success after retry")]
        mock_client.messages.create.side_effect = [rate_limit_exc, mock_response]
        mock_client_fn.return_value = mock_client

        with patch.object(client_mod, "_is_retryable", side_effect=lambda e: e is rate_limit_exc):
            with patch.object(client_mod, "_RETRY_WAIT", 0.01):
                result = generate("test prompt", use_cache=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["response"], "Success after retry")
        self.assertTrue(result["retried"])

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._enforce_rate_limit")
    @patch("engines.ai_client._get_client")
    def test_no_retry_on_auth_error(self, mock_client_fn, mock_rate, mock_avail):
        """Does NOT retry on authentication error."""
        mock_client = MagicMock()
        auth_exc = Exception("authentication failed")
        mock_client.messages.create.side_effect = auth_exc
        mock_client_fn.return_value = mock_client

        result = generate("test prompt", use_cache=False)
        self.assertFalse(result["success"])
        self.assertIn("authentication failed", result["error"])
        self.assertFalse(result["retried"])
        # Should only have been called once (no retry)
        self.assertEqual(mock_client.messages.create.call_count, 1)

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._enforce_rate_limit")
    @patch("engines.ai_client._get_client")
    def test_retry_exhausted(self, mock_client_fn, mock_rate, mock_avail):
        """Returns error after retry is exhausted."""
        import engines.ai_client as client_mod

        mock_client = MagicMock()
        rate_exc = Exception("rate limit")
        mock_client.messages.create.side_effect = rate_exc
        mock_client_fn.return_value = mock_client

        with patch.object(client_mod, "_is_retryable", return_value=True):
            with patch.object(client_mod, "_RETRY_WAIT", 0.01):
                result = generate("test prompt", use_cache=False)

        self.assertFalse(result["success"])
        self.assertTrue(result["retried"])
        # 1 original + 1 retry = 2 calls
        self.assertEqual(mock_client.messages.create.call_count, 2)

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._enforce_rate_limit")
    @patch("engines.ai_client._get_client")
    def test_retried_field_in_result(self, mock_client_fn, mock_rate, mock_avail):
        """Result includes 'retried' field set to False on first success."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Immediate success")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = generate("test prompt", use_cache=False)
        self.assertTrue(result["success"])
        self.assertFalse(result["retried"])
        self.assertIn("retried", result)


class TestResponseParsing(unittest.TestCase):
    """Tests for _parse_sections in ai_interpreter.py."""

    def test_parse_9_sections_en(self):
        """Parses all 9 EN sections from sample response."""
        sections = _parse_sections(SAMPLE_AI_RESPONSE_EN, "en")
        self.assertGreater(len(sections["header"]), 0)
        self.assertGreater(len(sections["universal_address"]), 0)
        self.assertGreater(len(sections["core_identity"]), 0)
        self.assertGreater(len(sections["right_now"]), 0)
        self.assertGreater(len(sections["patterns"]), 0)
        self.assertGreater(len(sections["message"]), 0)
        self.assertGreater(len(sections["advice"]), 0)
        self.assertGreater(len(sections["caution"]), 0)
        self.assertGreater(len(sections["footer"]), 0)

    def test_parse_9_sections_fa(self):
        """Parses all 9 FA sections from sample response."""
        sections = _parse_sections(SAMPLE_AI_RESPONSE_FA, "fa")
        self.assertGreater(len(sections["header"]), 0)
        self.assertGreater(len(sections["universal_address"]), 0)
        self.assertGreater(len(sections["core_identity"]), 0)
        self.assertGreater(len(sections["right_now"]), 0)
        self.assertGreater(len(sections["patterns"]), 0)
        self.assertGreater(len(sections["message"]), 0)
        self.assertGreater(len(sections["advice"]), 0)
        self.assertGreater(len(sections["caution"]), 0)

    def test_parse_fallback_unparseable(self):
        """Unparseable text puts everything in 'message' section."""
        sections = _parse_sections("Just some plain text with no section markers.")
        self.assertEqual(sections["message"], "Just some plain text with no section markers.")
        self.assertEqual(sections["header"], "")
        self.assertEqual(sections["universal_address"], "")
        self.assertEqual(sections["core_identity"], "")

    def test_parse_partial_sections(self):
        """Partial response populates found sections, leaves others empty."""
        partial = """READING FOR TEST
Some header content

---

THE MESSAGE

This is the main message.

---

CAUTION

Be careful."""
        sections = _parse_sections(partial, "en")
        self.assertGreater(len(sections["header"]), 0)
        self.assertGreater(len(sections["message"]), 0)
        self.assertGreater(len(sections["caution"]), 0)
        # Unprovided sections should be empty
        self.assertEqual(sections["universal_address"], "")
        self.assertEqual(sections["core_identity"], "")


class TestInterpreter(unittest.TestCase):
    """Tests for interpret_reading and interpret_multi_user."""

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_reading_ai_success(self, mock_avail, mock_gen):
        """Returns ReadingInterpretation with ai_generated=True on AI success."""
        mock_gen.return_value = {
            "success": True,
            "response": SAMPLE_AI_RESPONSE_EN,
            "cached": False,
        }
        result = interpret_reading(SAMPLE_FRAMEWORK_READING)
        self.assertIsInstance(result, ReadingInterpretation)
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.locale, "en")
        self.assertGreater(len(result.full_text), 0)
        self.assertGreater(len(result.message), 0)
        self.assertEqual(result.confidence_score, 95)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_interpret_reading_fallback(self, mock_avail):
        """Uses reading['translation'] when AI unavailable."""
        result = interpret_reading(SAMPLE_FRAMEWORK_READING)
        self.assertIsInstance(result, ReadingInterpretation)
        self.assertFalse(result.ai_generated)
        # Should use translation sections
        self.assertIn("ALICE JOHNSON", result.header)
        self.assertIn("FC60", result.universal_address)
        self.assertIn("Explorer", result.core_identity)
        self.assertEqual(result.confidence_score, 95)

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_reading_fa(self, mock_avail, mock_gen):
        """FA locale uses FA system prompt."""
        mock_gen.return_value = {
            "success": True,
            "response": SAMPLE_AI_RESPONSE_FA,
            "cached": False,
        }
        result = interpret_reading(SAMPLE_FRAMEWORK_READING, locale="fa")
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.locale, "fa")
        # Verify FA system prompt was passed
        call_args = mock_gen.call_args
        self.assertIn("fa", call_args.kwargs.get("locale", ""))

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_multi_user(self, mock_avail, mock_gen):
        """Multi-user returns MultiUserInterpretation with 2 individual readings."""
        mock_gen.return_value = {
            "success": True,
            "response": "Group: Alice and Bob COMPATIBILITY analysis here.",
            "cached": False,
        }
        result = interpret_multi_user(
            [SAMPLE_FRAMEWORK_READING, SAMPLE_MINIMAL_READING],
            ["Alice", "Bob"],
        )
        self.assertIsInstance(result, MultiUserInterpretation)
        self.assertEqual(len(result.individual_readings), 2)
        self.assertIn("Alice", result.individual_readings)
        self.assertIn("Bob", result.individual_readings)
        self.assertTrue(result.ai_generated)
        self.assertGreater(len(result.group_narrative), 0)

    def test_reading_interpretation_to_dict(self):
        """ReadingInterpretation.to_dict() is JSON-serializable with all keys."""
        result = ReadingInterpretation(
            header="TEST HEADER",
            universal_address="FC60: TEST",
            core_identity="Life Path 5",
            right_now="Monday",
            patterns="Horse x2",
            message="Numbers suggest...",
            advice="1. Move with intention",
            caution="Watch for overwhelm",
            footer="Confidence: 95%",
            full_text="Full reading text",
            ai_generated=True,
            locale="en",
            elapsed_ms=150.5,
            cached=False,
            confidence_score=95,
        )
        d = result.to_dict()
        # All 9 section keys present
        for key in [
            "header",
            "universal_address",
            "core_identity",
            "right_now",
            "patterns",
            "message",
            "advice",
            "caution",
            "footer",
        ]:
            self.assertIn(key, d)
        self.assertIn("full_text", d)
        self.assertIn("ai_generated", d)
        self.assertIn("confidence_score", d)
        # JSON serializable
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["header"], "TEST HEADER")
        self.assertEqual(parsed["confidence_score"], 95)


class TestFallback(unittest.TestCase):
    """Tests for _build_fallback in ai_interpreter.py."""

    def test_fallback_uses_translation_sections(self):
        """Fallback populates sections from reading['translation']."""
        result = _build_fallback(SAMPLE_FRAMEWORK_READING, "en")
        self.assertFalse(result.ai_generated)
        self.assertIn("ALICE JOHNSON", result.header)
        self.assertIn("FC60", result.universal_address)
        self.assertIn("Explorer", result.core_identity)
        self.assertIn("Monday", result.right_now)
        self.assertIn("Horse", result.patterns)
        self.assertGreater(len(result.message), 0)
        self.assertGreater(len(result.advice), 0)
        self.assertGreater(len(result.caution), 0)

    def test_fallback_uses_synthesis_when_no_translation(self):
        """Uses synthesis as full_text when no translation sections."""
        reading_no_trans = {
            "synthesis": "Bob has Life Path 1. Today is Monday.",
        }
        result = _build_fallback(reading_no_trans, "en")
        self.assertFalse(result.ai_generated)
        self.assertEqual(result.full_text, "Bob has Life Path 1. Today is Monday.")
        # Sections should be empty
        self.assertEqual(result.header, "")
        self.assertEqual(result.core_identity, "")

    def test_fallback_minimal_reading(self):
        """Minimal reading (no translation, no synthesis) still returns valid result."""
        result = _build_fallback({}, "en")
        self.assertFalse(result.ai_generated)
        self.assertGreater(len(result.message), 0)
        self.assertGreater(len(result.full_text), 0)


class TestCacheKey(unittest.TestCase):
    """Tests for _make_daily_cache_key."""

    def test_daily_cache_key_deterministic(self):
        """Same inputs produce same cache key."""
        key1 = _make_daily_cache_key("user1", "2026-02-09", "en")
        key2 = _make_daily_cache_key("user1", "2026-02-09", "en")
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)  # SHA-256 hex digest

    def test_daily_cache_key_differs_by_locale(self):
        """Different locales produce different cache keys."""
        key_en = _make_daily_cache_key("user1", "2026-02-09", "en")
        key_fa = _make_daily_cache_key("user1", "2026-02-09", "fa")
        self.assertNotEqual(key_en, key_fa)


class TestIntegrationPipeline(unittest.TestCase):
    """Integration tests verifying full pipelines end-to-end."""

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_full_pipeline_mocked_ai(self, mock_avail, mock_gen):
        """Full pipeline: reading -> prompt -> AI -> parse -> ReadingInterpretation."""
        mock_gen.return_value = {
            "success": True,
            "response": SAMPLE_AI_RESPONSE_EN,
            "cached": False,
        }
        result = interpret_reading(SAMPLE_FRAMEWORK_READING)
        self.assertTrue(result.ai_generated)
        self.assertGreater(len(result.header), 0)
        self.assertGreater(len(result.message), 0)
        self.assertGreater(len(result.footer), 0)
        # to_dict is JSON-serializable
        d = result.to_dict()
        json.dumps(d)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_full_pipeline_ai_unavailable(self, mock_avail):
        """Fallback pipeline: reading -> _build_fallback -> ReadingInterpretation."""
        result = interpret_reading(SAMPLE_FRAMEWORK_READING)
        self.assertFalse(result.ai_generated)
        # Uses translation sections
        self.assertGreater(len(result.header), 0)
        self.assertGreater(len(result.message), 0)
        d = result.to_dict()
        json.dumps(d)

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_persian_pipeline(self, mock_avail, mock_gen):
        """Persian pipeline: FA system prompt, FA parsing."""
        mock_gen.return_value = {
            "success": True,
            "response": SAMPLE_AI_RESPONSE_FA,
            "cached": False,
        }
        result = interpret_reading(SAMPLE_FRAMEWORK_READING, locale="fa")
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.locale, "fa")

    @patch("engines.ai_interpreter.generate_reading")
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_multi_user_pipeline(self, mock_avail, mock_gen):
        """Multi-user pipeline: 2 readings -> interpret -> MultiUserInterpretation."""
        mock_gen.return_value = {
            "success": True,
            "response": "Group COMPATIBILITY narrative for Alice and Bob.",
            "cached": False,
        }
        result = interpret_multi_user(
            [SAMPLE_FRAMEWORK_READING, SAMPLE_MINIMAL_READING],
            ["Alice", "Bob"],
        )
        self.assertIsInstance(result, MultiUserInterpretation)
        self.assertEqual(len(result.individual_readings), 2)
        d = result.to_dict()
        json.dumps(d)

    def test_import_verification(self):
        """All new module imports work correctly."""
        # These imports already succeeded at module level, but verify explicitly
        self.assertTrue(callable(build_reading_prompt))
        self.assertTrue(callable(build_multi_user_prompt))
        self.assertTrue(callable(get_system_prompt))
        self.assertTrue(callable(interpret_reading))
        self.assertTrue(callable(interpret_multi_user))
        self.assertTrue(callable(generate_reading))
        self.assertIsInstance(WISDOM_SYSTEM_PROMPT_EN, str)
        self.assertIsInstance(WISDOM_SYSTEM_PROMPT_FA, str)
        self.assertIsInstance(FC60_PRESERVED_TERMS, list)

    def test_preserved_terms_complete(self):
        """FC60_PRESERVED_TERMS contains all required terms."""
        required = [
            "FC60",
            "Wu Xing",
            "Wood",
            "Fire",
            "Earth",
            "Metal",
            "Water",
            "Dragon",
            "Horse",
            "Life Path",
            "Soul Urge",
            "Ganzhi",
        ]
        for term in required:
            self.assertIn(term, FC60_PRESERVED_TERMS)

    def test_build_prompt_legacy_compat(self):
        """build_prompt still works with _SafeDict for missing keys."""
        result = build_prompt("Hello {name}, your path is {life_path}.", {"name": "Test"})
        self.assertIn("Test", result)
        self.assertIn("(not available)", result)


if __name__ == "__main__":
    unittest.main()
