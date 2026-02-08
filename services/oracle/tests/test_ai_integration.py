"""
Tests for AI Integration (T3-S3)
==================================
8 test classes, 50+ tests covering:
  - AI client availability (SDK + key checks)
  - AI client generate (success, error, cache, rate limiting)
  - Prompt templates (all defined, placeholders, build_prompt)
  - AI interpreter single (4 formats, fallbacks, context building)
  - AI interpreter group (multi-user, fallbacks, narratives)
  - Translation service (en→fa, fa→en, batch, term protection, detection)
  - Integration (end-to-end with mocked AI, JSON serializable)
  - Result classes (__slots__, to_dict, repr)

All AI calls mocked — zero real API calls.
"""

import json
import os
import time
import unittest
from unittest.mock import patch, MagicMock

import oracle_service  # triggers sys.path shim

from engines.ai_client import (
    is_available,
    generate,
    clear_cache,
    reset_availability,
    _cache_key,
    _read_cache,
    _write_cache,
    _CACHE_TTL,
    _CACHE_MAX,
)
from engines.prompt_templates import (
    FC60_SYSTEM_PROMPT,
    SIMPLE_TEMPLATE,
    ADVICE_TEMPLATE,
    ACTION_STEPS_TEMPLATE,
    UNIVERSE_MESSAGE_TEMPLATE,
    GROUP_NARRATIVE_TEMPLATE,
    COMPATIBILITY_NARRATIVE_TEMPLATE,
    ENERGY_NARRATIVE_TEMPLATE,
    TRANSLATE_EN_FA_TEMPLATE,
    TRANSLATE_FA_EN_TEMPLATE,
    BATCH_TRANSLATE_TEMPLATE,
    FC60_PRESERVED_TERMS,
    build_prompt,
    _ALL_KEYS,
)
from engines.ai_interpreter import (
    interpret_reading,
    interpret_name,
    interpret_all_formats,
    interpret_group,
    InterpretationResult,
    MultiFormatResult,
    GroupInterpretationResult,
    _build_reading_context,
    _build_group_context,
)
from engines.translation_service import (
    translate,
    batch_translate,
    detect_language,
    TranslationResult,
    _protect_terms,
    _restore_terms,
    _parse_batch_response,
)

# ════════════════════════════════════════════════════════════
# Test fixtures
# ════════════════════════════════════════════════════════════

ALICE = {"name": "Alice", "birth_year": 1990, "birth_month": 5, "birth_day": 15}
BOB = {"name": "Bob", "birth_year": 1992, "birth_month": 3, "birth_day": 20}
CAROL = {"name": "Carol", "birth_year": 1988, "birth_month": 11, "birth_day": 7}
DAVE = {"name": "Dave", "birth_year": 1995, "birth_month": 8, "birth_day": 25}

SAMPLE_READING = {
    "sign": "42",
    "numbers": [42, 4, 2],
    "systems": {
        "fc60": {
            "token": "MT-HO",
            "element": "Metal",
            "animal": "Horse",
            "full_output": "Metal Horse (MT-HO)",
        },
        "numerology": {
            "life_path": 7,
            "reductions": [{"value": 42, "reduced": 6}],
            "expression": 5,
            "soul_urge": 3,
            "personality": 2,
        },
        "moon": {"phase": "Waxing Gibbous"},
        "ganzhi": {"year_pillar": "Geng-Wu", "hour_pillar": "Bing-Xu"},
        "zodiac": {"sign": "Taurus"},
        "angel": {},
        "chaldean": {},
    },
    "interpretation": "The number 42 carries deep significance across multiple systems.",
    "synchronicities": ["Mirror pattern detected in 42"],
    "timestamp": time.time(),
    "location": None,
    "context": None,
}

SAMPLE_NAME_DATA = {
    "name": "Hamzeh",
    "expression": 7,
    "soul_urge": 5,
    "personality": 2,
    "life_path": 9,
    "chaldean": 6,
    "interpretation": "The name Hamzeh resonates with analytical and spiritual energy.",
    "birthday_zodiac": {"sign": "Leo", "element": "Fire"},
}

SAMPLE_ANALYSIS_DICT = {
    "user_count": 2,
    "pair_count": 1,
    "computation_ms": 5.2,
    "profiles": [
        {
            "name": "Alice",
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "fc60_sign": "MT-HO",
            "element": "Metal",
            "animal": "Horse",
            "life_path": 3,
            "destiny_number": 5,
            "name_energy": 7,
        },
        {
            "name": "Bob",
            "birth_year": 1992,
            "birth_month": 3,
            "birth_day": 20,
            "fc60_sign": "WA-MO",
            "element": "Water",
            "animal": "Monkey",
            "life_path": 8,
            "destiny_number": 2,
            "name_energy": 4,
        },
    ],
    "pairwise_compatibility": [
        {
            "user1": "Alice",
            "user2": "Bob",
            "scores": {
                "life_path": 0.65,
                "element": 0.55,
                "animal": 0.70,
                "destiny": 0.50,
                "name_energy": 0.60,
                "overall": 0.62,
            },
            "classification": "Good",
            "strengths": ["Strong animal resonance", "Complementary elements"],
            "challenges": ["Destiny number tension"],
        }
    ],
    "group_energy": {
        "joint_life_path": 2,
        "dominant_element": "Metal",
        "dominant_animal": "Horse",
        "archetype": "Complementary Duo",
        "archetype_description": "Two forces creating balance through difference",
        "element_distribution": {"Metal": 1, "Water": 1},
        "animal_distribution": {"Horse": 1, "Monkey": 1},
        "life_path_distribution": {"3": 1, "8": 1},
    },
    "group_dynamics": {
        "roles": {"Alice": "Harmonizer", "Bob": "Leader"},
        "synergies": ["Alice and Bob share complementary elements"],
        "challenges": ["Potential tension between Leader and Harmonizer"],
        "growth_areas": ["Build on animal resonance"],
        "avg_compatibility": 0.62,
        "strongest_bond": {"pair": "Alice & Bob", "score": 0.62},
        "weakest_bond": {"pair": "Alice & Bob", "score": 0.62},
    },
}

# 4-user analysis dict for larger group tests
SAMPLE_4USER_ANALYSIS = {
    "user_count": 4,
    "pair_count": 6,
    "computation_ms": 12.5,
    "profiles": [
        {
            "name": "Alice",
            "element": "Metal",
            "animal": "Horse",
            "life_path": 3,
            "destiny_number": 5,
            "name_energy": 7,
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "fc60_sign": "MT-HO",
        },
        {
            "name": "Bob",
            "element": "Water",
            "animal": "Monkey",
            "life_path": 8,
            "destiny_number": 2,
            "name_energy": 4,
            "birth_year": 1992,
            "birth_month": 3,
            "birth_day": 20,
            "fc60_sign": "WA-MO",
        },
        {
            "name": "Carol",
            "element": "Earth",
            "animal": "Dragon",
            "life_path": 1,
            "destiny_number": 9,
            "name_energy": 3,
            "birth_year": 1988,
            "birth_month": 11,
            "birth_day": 7,
            "fc60_sign": "ER-DR",
        },
        {
            "name": "Dave",
            "element": "Fire",
            "animal": "Pig",
            "life_path": 5,
            "destiny_number": 6,
            "name_energy": 8,
            "birth_year": 1995,
            "birth_month": 8,
            "birth_day": 25,
            "fc60_sign": "FI-PI",
        },
    ],
    "pairwise_compatibility": [
        {
            "user1": "Alice",
            "user2": "Bob",
            "scores": {
                "life_path": 0.65,
                "element": 0.55,
                "animal": 0.70,
                "destiny": 0.50,
                "name_energy": 0.60,
                "overall": 0.62,
            },
            "classification": "Good",
            "strengths": ["Animal resonance"],
            "challenges": ["Destiny tension"],
        },
        {
            "user1": "Alice",
            "user2": "Carol",
            "scores": {
                "life_path": 0.70,
                "element": 0.80,
                "animal": 0.45,
                "destiny": 0.55,
                "name_energy": 0.65,
                "overall": 0.66,
            },
            "classification": "Good",
            "strengths": ["Element harmony"],
            "challenges": ["Animal clash"],
        },
        {
            "user1": "Alice",
            "user2": "Dave",
            "scores": {
                "life_path": 0.50,
                "element": 0.30,
                "animal": 0.60,
                "destiny": 0.45,
                "name_energy": 0.55,
                "overall": 0.46,
            },
            "classification": "Neutral",
            "strengths": ["Animal affinity"],
            "challenges": ["Element conflict"],
        },
        {
            "user1": "Bob",
            "user2": "Carol",
            "scores": {
                "life_path": 0.85,
                "element": 0.70,
                "animal": 0.75,
                "destiny": 0.60,
                "name_energy": 0.50,
                "overall": 0.74,
            },
            "classification": "Good",
            "strengths": ["Life path synergy"],
            "challenges": ["Name energy gap"],
        },
        {
            "user1": "Bob",
            "user2": "Dave",
            "scores": {
                "life_path": 0.55,
                "element": 0.90,
                "animal": 0.40,
                "destiny": 0.65,
                "name_energy": 0.70,
                "overall": 0.65,
            },
            "classification": "Good",
            "strengths": ["Element excellence"],
            "challenges": ["Animal distance"],
        },
        {
            "user1": "Carol",
            "user2": "Dave",
            "scores": {
                "life_path": 0.75,
                "element": 0.60,
                "animal": 0.55,
                "destiny": 0.70,
                "name_energy": 0.45,
                "overall": 0.63,
            },
            "classification": "Good",
            "strengths": ["Life path harmony"],
            "challenges": ["Name energy gap"],
        },
    ],
    "group_energy": {
        "joint_life_path": 8,
        "dominant_element": "Metal",
        "dominant_animal": "Horse",
        "archetype": "Dynamic Innovators",
        "archetype_description": "High-energy group driven by change and new ideas",
        "element_distribution": {"Metal": 1, "Water": 1, "Earth": 1, "Fire": 1},
        "animal_distribution": {"Horse": 1, "Monkey": 1, "Dragon": 1, "Pig": 1},
        "life_path_distribution": {"3": 1, "8": 1, "1": 1, "5": 1},
    },
    "group_dynamics": {
        "roles": {
            "Alice": "Harmonizer",
            "Bob": "Leader",
            "Carol": "Leader",
            "Dave": "Challenger",
        },
        "synergies": [
            "Bob and Carol share strong life path synergy",
            "All four elements represented",
        ],
        "challenges": ["Two Leaders may compete", "Alice-Dave tension"],
        "growth_areas": ["Balance Leader energy", "Strengthen weakest pair"],
        "avg_compatibility": 0.627,
        "strongest_bond": {"pair": "Bob & Carol", "score": 0.74},
        "weakest_bond": {"pair": "Alice & Dave", "score": 0.46},
    },
}


def _mock_generate_success(
    prompt, system_prompt="", max_tokens=None, temperature=0.7, use_cache=True
):
    """Mock generate that returns a plausible AI response."""
    return {
        "success": True,
        "response": f"AI interpretation for: {prompt[:50]}...",
        "error": None,
        "elapsed": 0.5,
        "cached": False,
    }


def _mock_generate_cached(
    prompt, system_prompt="", max_tokens=None, temperature=0.7, use_cache=True
):
    """Mock generate that returns a cached response."""
    return {
        "success": True,
        "response": f"Cached AI response for: {prompt[:50]}...",
        "error": None,
        "elapsed": 0.0,
        "cached": True,
    }


def _mock_generate_failure(
    prompt, system_prompt="", max_tokens=None, temperature=0.7, use_cache=True
):
    """Mock generate that simulates an API error."""
    return {
        "success": False,
        "response": "",
        "error": "API rate limit exceeded",
        "elapsed": 1.2,
        "cached": False,
    }


def _mock_generate_translation(
    prompt, system_prompt="", max_tokens=None, temperature=0.7, use_cache=True
):
    """Mock generate that returns a Persian translation."""
    if "batch" in prompt.lower() or "numbered" in prompt.lower():
        return {
            "success": True,
            "response": "1. ترجمه اول\n2. ترجمه دوم\n3. ترجمه سوم",
            "error": None,
            "elapsed": 0.8,
            "cached": False,
        }
    return {
        "success": True,
        "response": "این یک ترجمه آزمایشی است با FC60 و Wu Xing",
        "error": None,
        "elapsed": 0.5,
        "cached": False,
    }


# ════════════════════════════════════════════════════════════
# Test Classes
# ════════════════════════════════════════════════════════════


class TestAIClientAvailability(unittest.TestCase):
    """Tests for ai_client.is_available()."""

    def setUp(self):
        reset_availability()

    def tearDown(self):
        reset_availability()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"})
    @patch("engines.ai_client._sdk_available", True)
    def test_available_with_key_and_sdk(self):
        """Available when both SDK and key are present."""
        self.assertTrue(is_available())

    @patch.dict(os.environ, {}, clear=True)
    @patch("engines.ai_client._sdk_available", True)
    def test_unavailable_without_key(self):
        """Unavailable when API key is not set."""
        # Remove the key if it's set
        os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertFalse(is_available())

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"})
    @patch("engines.ai_client._sdk_available", False)
    def test_unavailable_without_sdk(self):
        """Unavailable when SDK is not importable."""
        self.assertFalse(is_available())

    @patch("engines.ai_client._sdk_available", False)
    def test_availability_caching(self):
        """Result is cached after first call."""
        os.environ.pop("ANTHROPIC_API_KEY", None)
        result1 = is_available()
        # Change state — should still return cached value
        # (We've already set _available via first call)
        result2 = is_available()
        self.assertEqual(result1, result2)


class TestAIClientGenerate(unittest.TestCase):
    """Tests for ai_client.generate()."""

    def setUp(self):
        reset_availability()
        clear_cache()

    def tearDown(self):
        reset_availability()
        clear_cache()

    @patch("engines.ai_client.is_available", return_value=False)
    def test_generate_unavailable(self, mock_avail):
        """Returns error dict when AI is not available."""
        result = generate("test prompt")
        self.assertFalse(result["success"])
        self.assertEqual(result["response"], "")
        self.assertIn("not available", result["error"])
        self.assertFalse(result["cached"])

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._get_client")
    @patch("engines.ai_client._enforce_rate_limit")
    def test_generate_success(self, mock_rate, mock_client_fn, mock_avail):
        """Returns success dict with response text."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test AI response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        result = generate("test prompt", use_cache=False)
        self.assertTrue(result["success"])
        self.assertEqual(result["response"], "Test AI response")
        self.assertIsNone(result["error"])
        self.assertFalse(result["cached"])
        self.assertGreaterEqual(result["elapsed"], 0)

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._get_client")
    @patch("engines.ai_client._enforce_rate_limit")
    def test_generate_api_error(self, mock_rate, mock_client_fn, mock_avail):
        """Returns error dict on API exception."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error: rate limited")
        mock_client_fn.return_value = mock_client

        result = generate("test prompt", use_cache=False)
        self.assertFalse(result["success"])
        self.assertEqual(result["response"], "")
        self.assertIn("rate limited", result["error"])

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._get_client")
    @patch("engines.ai_client._enforce_rate_limit")
    def test_generate_timeout(self, mock_rate, mock_client_fn, mock_avail):
        """Handles timeout gracefully."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = TimeoutError("Request timed out")
        mock_client_fn.return_value = mock_client

        result = generate("test prompt", use_cache=False)
        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])

    @patch("engines.ai_client.is_available", return_value=True)
    @patch("engines.ai_client._get_client")
    @patch("engines.ai_client._enforce_rate_limit")
    def test_generate_cache_hit(self, mock_rate, mock_client_fn, mock_avail):
        """Returns cached response on second call with same prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Cached response")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_fn.return_value = mock_client

        # First call — populates cache
        result1 = generate("cache test prompt", system_prompt="sys")
        self.assertTrue(result1["success"])
        self.assertFalse(result1["cached"])

        # Second call — should hit cache
        result2 = generate("cache test prompt", system_prompt="sys")
        self.assertTrue(result2["success"])
        self.assertTrue(result2["cached"])
        self.assertEqual(result2["response"], "Cached response")
        self.assertEqual(result2["elapsed"], 0.0)

    def test_cache_ttl_expiry(self):
        """Cache entries expire after TTL."""
        key = _cache_key("ttl test", "sys")
        _write_cache(key, "old response")

        # Manually expire
        import engines.ai_client as client_mod

        with client_mod._cache_lock:
            client_mod._cache[key]["timestamp"] = time.time() - _CACHE_TTL - 1

        result = _read_cache(key)
        self.assertIsNone(result)

    def test_cache_eviction(self):
        """Cache evicts oldest entries when over max size."""
        import engines.ai_client as client_mod

        clear_cache()

        # Fill beyond max
        for i in range(_CACHE_MAX + 10):
            _write_cache(f"key_{i}", f"response_{i}")

        with client_mod._cache_lock:
            self.assertLessEqual(len(client_mod._cache), _CACHE_MAX)

    def test_clear_cache(self):
        """clear_cache removes all entries."""
        import engines.ai_client as client_mod

        _write_cache("test_key", "test_response")
        with client_mod._cache_lock:
            self.assertGreater(len(client_mod._cache), 0)

        clear_cache()
        with client_mod._cache_lock:
            self.assertEqual(len(client_mod._cache), 0)


class TestPromptTemplates(unittest.TestCase):
    """Tests for prompt_templates.py."""

    def test_all_templates_are_strings(self):
        """All template constants are non-empty strings."""
        templates = [
            FC60_SYSTEM_PROMPT,
            SIMPLE_TEMPLATE,
            ADVICE_TEMPLATE,
            ACTION_STEPS_TEMPLATE,
            UNIVERSE_MESSAGE_TEMPLATE,
            GROUP_NARRATIVE_TEMPLATE,
            COMPATIBILITY_NARRATIVE_TEMPLATE,
            ENERGY_NARRATIVE_TEMPLATE,
            TRANSLATE_EN_FA_TEMPLATE,
            TRANSLATE_FA_EN_TEMPLATE,
            BATCH_TRANSLATE_TEMPLATE,
        ]
        for t in templates:
            self.assertIsInstance(t, str)
            self.assertGreater(len(t), 20)

    def test_preserved_terms_list(self):
        """FC60_PRESERVED_TERMS contains expected key terms."""
        self.assertIn("FC60", FC60_PRESERVED_TERMS)
        self.assertIn("Wu Xing", FC60_PRESERVED_TERMS)
        self.assertIn("Wood", FC60_PRESERVED_TERMS)
        self.assertIn("Dragon", FC60_PRESERVED_TERMS)
        self.assertIn("Life Path", FC60_PRESERVED_TERMS)
        self.assertGreater(len(FC60_PRESERVED_TERMS), 20)

    def test_system_prompt_content(self):
        """System prompt covers all key domains."""
        self.assertIn("FC60", FC60_SYSTEM_PROMPT)
        self.assertIn("Wu Xing", FC60_SYSTEM_PROMPT)
        self.assertIn("numerology", FC60_SYSTEM_PROMPT.lower())
        self.assertIn("Ganzhi", FC60_SYSTEM_PROMPT)

    def test_simple_template_has_format_keys(self):
        """SIMPLE_TEMPLATE contains expected placeholders."""
        self.assertIn("{name}", SIMPLE_TEMPLATE)
        self.assertIn("{fc60_sign}", SIMPLE_TEMPLATE)
        self.assertIn("{element}", SIMPLE_TEMPLATE)
        self.assertIn("{life_path}", SIMPLE_TEMPLATE)

    def test_build_prompt_fills_keys(self):
        """build_prompt correctly fills template placeholders."""
        result = build_prompt(
            SIMPLE_TEMPLATE,
            {
                "name": "Alice",
                "fc60_sign": "MT-HO",
                "element": "Metal",
                "animal": "Horse",
                "life_path": "7",
            },
        )
        self.assertIn("Alice", result)
        self.assertIn("MT-HO", result)
        self.assertIn("Metal", result)

    def test_build_prompt_missing_keys_fallback(self):
        """build_prompt uses '(not available)' for missing keys."""
        result = build_prompt(SIMPLE_TEMPLATE, {"name": "Alice"})
        self.assertIn("Alice", result)
        self.assertIn("(not available)", result)

    def test_all_keys_set_complete(self):
        """_ALL_KEYS contains all keys used across templates."""
        # Verify core keys are present
        core_keys = {
            "name",
            "element",
            "animal",
            "life_path",
            "fc60_sign",
            "zodiac_sign",
            "moon_phase",
            "ganzhi",
            "interpretation",
        }
        for k in core_keys:
            self.assertIn(k, _ALL_KEYS)


class TestAIInterpreterSingle(unittest.TestCase):
    """Tests for ai_interpreter single reading interpretation."""

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_simple_success(self, mock_avail, mock_gen):
        """Simple format returns AI-generated interpretation."""
        result = interpret_reading(SAMPLE_READING, "simple", "Hamzeh")
        self.assertIsInstance(result, InterpretationResult)
        self.assertEqual(result.format, "simple")
        self.assertTrue(result.ai_generated)
        self.assertGreater(len(result.text), 0)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_advice_success(self, mock_avail, mock_gen):
        """Advice format returns AI-generated interpretation."""
        result = interpret_reading(SAMPLE_READING, "advice", "Hamzeh")
        self.assertEqual(result.format, "advice")
        self.assertTrue(result.ai_generated)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_action_steps_success(self, mock_avail, mock_gen):
        """Action steps format returns AI-generated interpretation."""
        result = interpret_reading(SAMPLE_READING, "action_steps")
        self.assertEqual(result.format, "action_steps")
        self.assertTrue(result.ai_generated)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_universe_message_success(self, mock_avail, mock_gen):
        """Universe message format returns AI-generated interpretation."""
        result = interpret_reading(SAMPLE_READING, "universe_message", "Hamzeh")
        self.assertEqual(result.format, "universe_message")
        self.assertTrue(result.ai_generated)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_fallback_simple(self, mock_avail):
        """Simple fallback uses raw data when AI unavailable."""
        result = interpret_reading(SAMPLE_READING, "simple", "Hamzeh")
        self.assertFalse(result.ai_generated)
        self.assertIn("Metal", result.text)
        self.assertIn("Horse", result.text)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_fallback_advice(self, mock_avail):
        """Advice fallback produces warm, personal text."""
        result = interpret_reading(SAMPLE_READING, "advice", "Hamzeh")
        self.assertFalse(result.ai_generated)
        self.assertIn("Hamzeh", result.text)
        self.assertIn("Metal", result.text)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_fallback_actions(self, mock_avail):
        """Action steps fallback has 3 categories."""
        result = interpret_reading(SAMPLE_READING, "action_steps")
        self.assertFalse(result.ai_generated)
        self.assertIn("Daily Practice", result.text)
        self.assertIn("Decision-Making", result.text)
        self.assertIn("Relationships", result.text)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_fallback_universe(self, mock_avail):
        """Universe message fallback starts with 'The universe sees'."""
        result = interpret_reading(SAMPLE_READING, "universe_message", "Hamzeh")
        self.assertFalse(result.ai_generated)
        self.assertIn("universe sees", result.text)

    def test_invalid_format(self):
        """Invalid format type returns error message."""
        result = interpret_reading(SAMPLE_READING, "invalid_format")
        self.assertFalse(result.ai_generated)
        self.assertIn("Unknown format", result.text)

    def test_context_building(self):
        """_build_reading_context extracts correct values from reading."""
        ctx = _build_reading_context(SAMPLE_READING, "Hamzeh")
        self.assertEqual(ctx["name"], "Hamzeh")
        self.assertEqual(ctx["element"], "Metal")
        self.assertEqual(ctx["animal"], "Horse")
        self.assertEqual(ctx["zodiac_sign"], "Taurus")
        self.assertEqual(ctx["moon_phase"], "Waxing Gibbous")
        self.assertIn("Geng-Wu", ctx["ganzhi"])


class TestAIInterpreterGroup(unittest.TestCase):
    """Tests for ai_interpreter group interpretation."""

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_group_2user(self, mock_avail, mock_gen):
        """2-user group interpretation returns all narratives."""
        result = interpret_group(SAMPLE_ANALYSIS_DICT)
        self.assertIsInstance(result, GroupInterpretationResult)
        self.assertTrue(result.ai_available)
        self.assertGreater(len(result.dynamics_narrative), 0)
        self.assertGreater(len(result.energy_narrative), 0)
        self.assertGreater(len(result.compatibility_narrative), 0)
        self.assertEqual(len(result.individual_insights), 2)
        self.assertIn("Alice", result.individual_insights)
        self.assertIn("Bob", result.individual_insights)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_interpret_group_4user(self, mock_avail, mock_gen):
        """4-user group interpretation handles all 6 pairs."""
        result = interpret_group(SAMPLE_4USER_ANALYSIS)
        self.assertEqual(len(result.individual_insights), 4)
        self.assertIn("Carol", result.individual_insights)
        self.assertIn("Dave", result.individual_insights)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_group_fallback(self, mock_avail):
        """Group fallback produces deterministic narratives."""
        result = interpret_group(SAMPLE_ANALYSIS_DICT)
        self.assertFalse(result.ai_available)
        self.assertGreater(len(result.dynamics_narrative), 0)
        self.assertGreater(len(result.energy_narrative), 0)
        self.assertGreater(len(result.compatibility_narrative), 0)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_group_fallback_narratives_content(self, mock_avail):
        """Fallback narratives contain actual data from analysis."""
        result = interpret_group(SAMPLE_ANALYSIS_DICT)
        # Dynamics narrative references actual members
        self.assertIn("Alice", result.dynamics_narrative)
        # Compatibility narrative references actual pairs
        self.assertIn("Alice", result.compatibility_narrative)
        self.assertIn("Bob", result.compatibility_narrative)
        # Energy narrative references actual energy
        self.assertIn("Metal", result.energy_narrative)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_group_to_dict(self, mock_avail):
        """GroupInterpretationResult.to_dict() is JSON-serializable."""
        result = interpret_group(SAMPLE_ANALYSIS_DICT)
        d = result.to_dict()
        self.assertIn("compatibility_narrative", d)
        self.assertIn("dynamics_narrative", d)
        self.assertIn("energy_narrative", d)
        self.assertIn("individual_insights", d)
        # JSON serializable
        json_str = json.dumps(d)
        self.assertGreater(len(json_str), 0)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_group_context_building(self, mock_avail, mock_gen):
        """_build_group_context extracts correct values."""
        ctx = _build_group_context(SAMPLE_ANALYSIS_DICT)
        self.assertEqual(ctx["user_count"], "2")
        self.assertIn("Alice", ctx["member_summaries"])
        self.assertIn("Bob", ctx["member_summaries"])
        self.assertIn("Harmonizer", ctx["roles"])
        self.assertEqual(ctx["dominant_element"], "Metal")


class TestTranslation(unittest.TestCase):
    """Tests for translation_service.py."""

    @patch(
        "engines.translation_service.generate", side_effect=_mock_generate_translation
    )
    @patch("engines.translation_service.is_available", return_value=True)
    def test_translate_en_to_fa(self, mock_avail, mock_gen):
        """English to Persian translation works."""
        result = translate("Your FC60 sign is Metal Horse.", "en", "fa")
        self.assertIsInstance(result, TranslationResult)
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.source_lang, "en")
        self.assertEqual(result.target_lang, "fa")
        self.assertGreater(len(result.translated_text), 0)

    @patch(
        "engines.translation_service.generate", side_effect=_mock_generate_translation
    )
    @patch("engines.translation_service.is_available", return_value=True)
    def test_translate_fa_to_en(self, mock_avail, mock_gen):
        """Persian to English translation works."""
        result = translate("این یک متن فارسی است", "fa", "en")
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.source_lang, "fa")
        self.assertEqual(result.target_lang, "en")

    @patch("engines.translation_service.is_available", return_value=False)
    def test_translate_fallback(self, mock_avail):
        """Returns original text when AI unavailable."""
        original = "Your FC60 sign is Metal Horse."
        result = translate(original, "en", "fa")
        self.assertFalse(result.ai_generated)
        self.assertEqual(result.translated_text, original)

    @patch(
        "engines.translation_service.generate", side_effect=_mock_generate_translation
    )
    @patch("engines.translation_service.is_available", return_value=True)
    def test_batch_translate(self, mock_avail, mock_gen):
        """Batch translation processes multiple texts."""
        texts = ["Hello world", "FC60 sign", "Metal Horse"]
        results = batch_translate(texts, "en", "fa")
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, TranslationResult)
            self.assertTrue(r.ai_generated)

    def test_detect_language_english(self):
        """Detects English text correctly."""
        self.assertEqual(detect_language("Hello, your FC60 sign is Metal Horse"), "en")

    def test_detect_language_persian(self):
        """Detects Persian text correctly."""
        self.assertEqual(detect_language("سلام، نشانه شما اسب فلزی است"), "fa")

    def test_detect_language_empty(self):
        """Returns 'en' for empty text."""
        self.assertEqual(detect_language(""), "en")

    def test_term_protection_and_restoration(self):
        """FC60 terms are protected and restored correctly."""
        text = "Your element is Metal and animal is Dragon in the FC60 system."
        protected, replacements = _protect_terms(text)

        # Terms should be replaced with placeholders
        self.assertNotIn("Metal", protected)
        self.assertNotIn("Dragon", protected)
        self.assertNotIn("FC60", protected)

        # Restore
        restored = _restore_terms(protected, replacements)
        self.assertEqual(restored, text)

    def test_term_protection_preserves_list(self):
        """Protected terms list is correctly populated."""
        text = "FC60 shows Wood Dragon with Wu Xing harmony"
        _, replacements = _protect_terms(text)
        terms = [r[0] for r in replacements]
        self.assertIn("FC60", terms)
        self.assertIn("Wood", terms)
        self.assertIn("Dragon", terms)
        self.assertIn("Wu Xing", terms)

    def test_batch_parse_response(self):
        """Batch response parsing extracts numbered items."""
        response = "1. First translation\n2. Second translation\n3. Third translation"
        parsed = _parse_batch_response(response, 3)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "First translation")
        self.assertEqual(parsed[1], "Second translation")
        self.assertEqual(parsed[2], "Third translation")

    def test_batch_parse_with_padding(self):
        """Batch parse pads missing items with empty strings."""
        response = "1. Only one"
        parsed = _parse_batch_response(response, 3)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0], "Only one")

    def test_translate_empty_text(self):
        """Empty text returns immediately without API call."""
        result = translate("", "en", "fa")
        self.assertFalse(result.ai_generated)
        self.assertEqual(result.translated_text, "")

    def test_batch_translate_empty_list(self):
        """Empty list returns empty list."""
        results = batch_translate([], "en", "fa")
        self.assertEqual(results, [])


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple modules."""

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_reading_to_interpret(self, mock_avail, mock_gen):
        """read_sign output → interpret_reading produces valid result."""
        # Use fixture data mimicking read_sign output
        result = interpret_reading(SAMPLE_READING, "simple", "Hamzeh")
        self.assertTrue(result.ai_generated)
        self.assertEqual(result.format, "simple")

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_name_to_interpret(self, mock_avail, mock_gen):
        """read_name output → interpret_name produces valid result."""
        result = interpret_name(SAMPLE_NAME_DATA, "simple")
        self.assertIsInstance(result, InterpretationResult)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_analysis_to_group_interpret(self, mock_avail, mock_gen):
        """MultiUserAnalysisResult.to_dict() → interpret_group."""
        result = interpret_group(SAMPLE_ANALYSIS_DICT)
        self.assertIsInstance(result, GroupInterpretationResult)
        self.assertTrue(result.ai_available)

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_all_formats_integration(self, mock_avail, mock_gen):
        """interpret_all_formats returns all 4 formats."""
        result = interpret_all_formats(SAMPLE_READING, "Hamzeh")
        self.assertIsInstance(result, MultiFormatResult)
        self.assertEqual(result.simple.format, "simple")
        self.assertEqual(result.advice.format, "advice")
        self.assertEqual(result.action_steps.format, "action_steps")
        self.assertEqual(result.universe_message.format, "universe_message")

    @patch("engines.ai_interpreter.generate", side_effect=_mock_generate_success)
    @patch("engines.ai_interpreter.is_available", return_value=True)
    def test_all_formats_json_serializable(self, mock_avail, mock_gen):
        """MultiFormatResult.to_dict() is fully JSON-serializable."""
        result = interpret_all_formats(SAMPLE_READING, "Hamzeh")
        d = result.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        self.assertIn("simple", parsed)
        self.assertIn("advice", parsed)
        self.assertIn("action_steps", parsed)
        self.assertIn("universe_message", parsed)

    @patch("engines.ai_interpreter.is_available", return_value=False)
    def test_fallback_json_serializable(self, mock_avail):
        """Fallback results are also JSON-serializable."""
        result = interpret_all_formats(SAMPLE_READING, "Hamzeh")
        d = result.to_dict()
        json_str = json.dumps(d)
        self.assertGreater(len(json_str), 0)


class TestResultClasses(unittest.TestCase):
    """Tests for result class structure and behavior."""

    def test_interpretation_result_slots(self):
        """InterpretationResult uses __slots__."""
        self.assertTrue(hasattr(InterpretationResult, "__slots__"))
        r = InterpretationResult("simple", "text", True, 10.0, False)
        with self.assertRaises(AttributeError):
            r.nonexistent_attr = "fail"

    def test_interpretation_result_to_dict(self):
        """InterpretationResult.to_dict() returns correct keys."""
        r = InterpretationResult("advice", "some text", True, 15.5, True)
        d = r.to_dict()
        self.assertEqual(d["format"], "advice")
        self.assertEqual(d["text"], "some text")
        self.assertTrue(d["ai_generated"])
        self.assertEqual(d["elapsed_ms"], 15.5)
        self.assertTrue(d["cached"])

    def test_interpretation_result_repr(self):
        """InterpretationResult has informative repr."""
        r = InterpretationResult("simple", "hello world", True, 5.0, False)
        rep = repr(r)
        self.assertIn("simple", rep)
        self.assertIn("AI", rep)

    def test_multi_format_result_slots(self):
        """MultiFormatResult uses __slots__."""
        self.assertTrue(hasattr(MultiFormatResult, "__slots__"))

    def test_group_interpretation_result_slots(self):
        """GroupInterpretationResult uses __slots__."""
        self.assertTrue(hasattr(GroupInterpretationResult, "__slots__"))

    def test_translation_result_slots(self):
        """TranslationResult uses __slots__."""
        self.assertTrue(hasattr(TranslationResult, "__slots__"))
        r = TranslationResult("src", "dst", "en", "fa", [], True, 5.0)
        with self.assertRaises(AttributeError):
            r.nonexistent_attr = "fail"

    def test_translation_result_to_dict(self):
        """TranslationResult.to_dict() returns correct keys."""
        r = TranslationResult("hello", "سلام", "en", "fa", ["FC60"], True, 8.3)
        d = r.to_dict()
        self.assertEqual(d["source_text"], "hello")
        self.assertEqual(d["translated_text"], "سلام")
        self.assertEqual(d["source_lang"], "en")
        self.assertEqual(d["target_lang"], "fa")
        self.assertEqual(d["preserved_terms"], ["FC60"])
        self.assertTrue(d["ai_generated"])

    def test_translation_result_repr(self):
        """TranslationResult has informative repr."""
        r = TranslationResult("hello", "سلام", "en", "fa", [], True, 5.0)
        rep = repr(r)
        self.assertIn("en", rep)
        self.assertIn("fa", rep)
        self.assertIn("AI", rep)


if __name__ == "__main__":
    unittest.main()
