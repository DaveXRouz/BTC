"""Tests for PatternFormatter and ConfidenceMapper."""

import pytest

from oracle_service.pattern_formatter import ConfidenceMapper, PatternFormatter

# ─── Test Fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def sample_patterns_with_animals():
    """Patterns dict with animal repetitions."""
    return {
        "detected": [
            {
                "type": "animal_repetition",
                "animal": "Ox",
                "occurrences": 3,
                "strength": "very_high",
                "message": "The Ox appears 3 times - major theme",
            },
        ],
        "count": 1,
    }


@pytest.fixture
def sample_patterns_with_numbers():
    """Patterns dict with number repetitions and master numbers."""
    return {
        "detected": [
            {
                "type": "number_repetition",
                "number": 7,
                "occurrences": 2,
                "strength": "high",
                "message": "The number 7 appears 2 times - major theme",
            },
            {
                "type": "master_number",
                "number": 11,
                "strength": "very_high",
                "message": "Life Path 11 is a Master Number - heightened spiritual potential",
            },
        ],
        "count": 2,
    }


@pytest.fixture
def mixed_patterns():
    """Patterns with all three types."""
    return {
        "detected": [
            {
                "type": "animal_repetition",
                "animal": "Ox",
                "occurrences": 3,
                "strength": "very_high",
                "message": "The Ox appears 3 times",
            },
            {
                "type": "number_repetition",
                "number": 7,
                "occurrences": 2,
                "strength": "high",
                "message": "The number 7 appears 2 times",
            },
            {
                "type": "master_number",
                "number": 11,
                "strength": "very_high",
                "message": "Life Path 11 is a Master Number",
            },
        ],
        "count": 3,
    }


@pytest.fixture
def empty_patterns():
    """Patterns dict with no detections."""
    return {"detected": [], "count": 0}


@pytest.fixture
def sample_signals():
    """Signals list from ReadingEngine."""
    return [
        {
            "type": "day_planet",
            "priority": "Medium",
            "message": "This is a Venus day, governing love and beauty.",
        },
        {
            "type": "animal_repetition",
            "priority": "Very High",
            "message": "The Ox appears 3 times — Patience and steady endurance.",
        },
        {
            "type": "moon_phase",
            "priority": "Medium",
            "message": "The moon is Waxing Crescent (age 4 days).",
        },
        {
            "type": "hour_animal",
            "priority": "Low-Medium",
            "message": "The Tiger hour carries the energy of courage.",
        },
    ]


@pytest.fixture
def sample_confidence_high():
    """High confidence dict."""
    return {"score": 85, "level": "very_high", "factors": "Based on 6 data sources"}


@pytest.fixture
def sample_confidence_low():
    """Low confidence dict."""
    return {"score": 55, "level": "low", "factors": "Based on 2 data sources"}


@pytest.fixture
def sample_combined_signals():
    """Combined signals from SignalCombiner."""
    return {
        "primary_message": "Ox appears 3 times — endurance is key.",
        "supporting_messages": [
            "This is a Venus day, governing love and beauty.",
            "The moon is Waxing Crescent (age 4 days).",
        ],
        "tensions": ["Fire and Water oppose — passion and depth struggle for dominance."],
        "recommended_actions": [
            "Pay attention to the repeated pattern.",
            "Your Life Path asks you to lead.",
            "The moon says this time is best for: reflection.",
        ],
    }


# ─── sort_by_priority ────────────────────────────────────────────────────


class TestSortByPriority:
    def test_orders_correctly(self, sample_signals):
        """Very High signals appear before Medium before Low."""
        result = PatternFormatter.sort_by_priority(sample_signals)
        priorities = [s["priority"] for s in result]
        assert priorities[0] == "Very High"
        assert priorities[-1] == "Low-Medium"

    def test_stable_within_same_level(self):
        """Same-priority signals maintain original order."""
        signals = [
            {"type": "a", "priority": "Medium", "message": "First"},
            {"type": "b", "priority": "Medium", "message": "Second"},
            {"type": "c", "priority": "Medium", "message": "Third"},
        ]
        result = PatternFormatter.sort_by_priority(signals)
        messages = [s["message"] for s in result]
        assert messages == ["First", "Second", "Third"]

    def test_empty_list(self):
        """Empty signal list returns empty list."""
        result = PatternFormatter.sort_by_priority([])
        assert result == []


# ─── format_for_ai ──────────────────────────────────────────────────────


class TestFormatForAI:
    def test_with_patterns(self, sample_patterns_with_animals, sample_signals):
        """AI output includes DETECTED PATTERNS section with correct count."""
        result = PatternFormatter.format_for_ai(sample_patterns_with_animals, sample_signals)
        assert "DETECTED PATTERNS (1):" in result
        assert "[Very High]" in result
        assert "Ox appears 3 times" in result

    def test_empty_patterns(self, empty_patterns, sample_signals):
        """AI output includes 'No specific patterns detected' message."""
        result = PatternFormatter.format_for_ai(empty_patterns, sample_signals)
        assert "No specific patterns detected" in result

    def test_with_combined_signals(
        self,
        sample_patterns_with_animals,
        sample_signals,
        sample_combined_signals,
    ):
        """AI output includes SIGNAL SUMMARY, TENSIONS, and ACTIONS sections."""
        result = PatternFormatter.format_for_ai(
            sample_patterns_with_animals,
            sample_signals,
            sample_combined_signals,
        )
        assert "SIGNAL SUMMARY:" in result
        assert "Primary:" in result
        assert "TENSIONS:" in result
        assert "RECOMMENDED ACTIONS:" in result

    def test_without_combined_signals(self, sample_patterns_with_animals, sample_signals):
        """AI output skips SIGNAL SUMMARY section when combined_signals=None."""
        result = PatternFormatter.format_for_ai(sample_patterns_with_animals, sample_signals, None)
        assert "SIGNAL SUMMARY:" not in result
        assert "TENSIONS:" not in result
        assert "RECOMMENDED ACTIONS:" not in result


# ─── format_for_frontend ────────────────────────────────────────────────


class TestFormatForFrontend:
    def test_badge_text_animal(
        self, sample_patterns_with_animals, sample_signals, sample_confidence_high
    ):
        """Animal repetition badge = 'Ox ×3'."""
        result = PatternFormatter.format_for_frontend(
            sample_patterns_with_animals, sample_signals, sample_confidence_high
        )
        assert result["patterns"][0]["badge_text"] == "Ox \u00d73"

    def test_badge_text_number(
        self, sample_patterns_with_numbers, sample_signals, sample_confidence_high
    ):
        """Number repetition badge = '#7 ×2'."""
        result = PatternFormatter.format_for_frontend(
            sample_patterns_with_numbers, sample_signals, sample_confidence_high
        )
        number_pattern = next(p for p in result["patterns"] if p["type"] == "number_repetition")
        assert number_pattern["badge_text"] == "#7 \u00d72"

    def test_badge_text_master(
        self, sample_patterns_with_numbers, sample_signals, sample_confidence_high
    ):
        """Master number badge = 'Master 11'."""
        result = PatternFormatter.format_for_frontend(
            sample_patterns_with_numbers, sample_signals, sample_confidence_high
        )
        master_pattern = next(p for p in result["patterns"] if p["type"] == "master_number")
        assert master_pattern["badge_text"] == "Master 11"

    def test_has_required_keys(
        self, sample_patterns_with_animals, sample_signals, sample_confidence_high
    ):
        """Frontend dict has all required top-level keys."""
        result = PatternFormatter.format_for_frontend(
            sample_patterns_with_animals, sample_signals, sample_confidence_high
        )
        required = {
            "patterns",
            "signal_count",
            "pattern_count",
            "has_tensions",
            "primary_signal",
        }
        assert required.issubset(result.keys())

    def test_empty_patterns(self, empty_patterns, sample_signals, sample_confidence_high):
        """Returns pattern_count=0, patterns=[], has_tensions=False."""
        result = PatternFormatter.format_for_frontend(
            empty_patterns, sample_signals, sample_confidence_high
        )
        assert result["pattern_count"] == 0
        assert result["patterns"] == []
        assert result["has_tensions"] is False


# ─── format_for_database ────────────────────────────────────────────────


class TestFormatForDatabase:
    def test_structure(self, mixed_patterns, sample_confidence_high):
        """DB dict has patterns_summary with count, types, strongest, all."""
        result = PatternFormatter.format_for_database(mixed_patterns, sample_confidence_high)
        summary = result["patterns_summary"]
        assert summary["count"] == 3
        assert "animal_repetition" in summary["types"]
        assert "number_repetition" in summary["types"]
        assert "master_number" in summary["types"]
        assert summary["strongest"]["type"] == "animal_repetition"
        assert len(summary["all"]) == 3
        assert result["confidence_score"] == 85
        assert result["confidence_level"] == "very_high"

    def test_empty_patterns(self, empty_patterns, sample_confidence_low):
        """DB dict has count=0, strongest=None, types=[]."""
        result = PatternFormatter.format_for_database(empty_patterns, sample_confidence_low)
        summary = result["patterns_summary"]
        assert summary["count"] == 0
        assert summary["strongest"] is None
        assert summary["types"] == []
        assert summary["all"] == []
        assert result["confidence_score"] == 55


# ─── ConfidenceMapper ───────────────────────────────────────────────────


class TestConfidenceMapper:
    def test_high_confidence(self, sample_confidence_high):
        """High confidence returns green color, empty caveat."""
        result = ConfidenceMapper.map_to_ui(sample_confidence_high)
        assert result["color"] == "#16A34A"
        assert result["caveat_en"] == ""
        assert result["caveat_fa"] == ""
        assert result["score"] == 85
        assert result["progress_width"] == 85

    def test_low_confidence(self, sample_confidence_low):
        """Low confidence returns red color, non-empty caveat."""
        result = ConfidenceMapper.map_to_ui(sample_confidence_low)
        assert result["color"] == "#DC2626"
        assert "limited data" in result["caveat_en"]
        assert len(result["caveat_fa"]) > 0
        assert result["score"] == 55

    def test_persian_labels(self):
        """All levels have non-empty label_fa."""
        for level in ["low", "medium", "high", "very_high"]:
            result = ConfidenceMapper.map_to_ui({"score": 70, "level": level, "factors": "test"})
            assert len(result["label_fa"]) > 0, f"Missing Persian label for {level}"
            assert len(result["label_en"]) > 0, f"Missing English label for {level}"

    def test_missing_keys(self):
        """Missing confidence dict keys use defaults (score=50, level=low)."""
        result = ConfidenceMapper.map_to_ui({})
        assert result["score"] == 50
        assert result["level"] == "low"
        assert result["color"] == "#DC2626"
        assert "limited data" in result["caveat_en"]
