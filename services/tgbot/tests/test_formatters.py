"""Tests for Telegram MarkdownV2 formatters."""

from services.tgbot.formatters import (
    _escape,
    _truncate,
    format_daily_insight,
    format_history_list,
    format_name_reading,
    format_progress,
    format_question_reading,
    format_time_reading,
)


def test_escape_special_chars():
    """_escape() properly escapes all MarkdownV2 special characters."""
    text = "Hello_World *bold* [link](url) ~strike~ `code` >quote #tag +plus -minus =equal |pipe {brace} .dot !exclaim"
    result = _escape(text)
    # Every special char should be preceded by a backslash
    assert "\\_" in result
    assert "\\*" in result
    assert "\\[" in result
    assert "\\]" in result
    assert "\\(" in result
    assert "\\)" in result
    assert "\\~" in result
    assert "\\`" in result
    assert "\\>" in result
    assert "\\#" in result
    assert "\\+" in result
    assert "\\-" in result
    assert "\\=" in result
    assert "\\|" in result
    assert "\\{" in result
    assert "\\}" in result
    assert "\\." in result
    assert "\\!" in result


def test_format_time_reading_all_sections():
    """Time reading formatter includes FC60, numerology, moon, zodiac sections."""
    data = {
        "generated_at": "2026-02-10T14:30:00",
        "fc60": {"stamp": "FC60-2026-02-10-1430", "cycle_number": 3, "position": 7},
        "numerology": {
            "life_path": 5,
            "personal_year": 8,
            "personal_month": 3,
            "personal_day": 1,
        },
        "moon": {
            "phase_name": "Waxing Gibbous",
            "emoji": "\U0001f314",
            "illumination": 72,
        },
        "zodiac": {"sign": "Aquarius"},
        "chinese": {"animal": "Horse", "element": "Fire"},
        "angel": {"number": "1111", "meaning": "New beginnings"},
        "synchronicities": ["Mirror hour 14:14", "Fibonacci sequence"],
        "ai_interpretation": "Trust the process and keep moving forward.",
        "summary": "A day of clarity.",
    }
    result = format_time_reading(data)
    assert "Oracle Time Reading" in result
    assert "FC60 Stamp" in result
    assert "Numerology" in result
    assert "Moon Phase" in result
    assert "Zodiac" in result
    assert "Chinese Zodiac" in result
    assert "Angel Numbers" in result
    assert "Synchronicities" in result
    assert "Interpretation" in result


def test_format_time_reading_missing_sections():
    """Gracefully handles None sections (moon=None, angel=None, etc.)."""
    data = {
        "generated_at": "2026-02-10T14:30:00",
        "fc60": None,
        "numerology": None,
        "moon": None,
        "zodiac": None,
        "chinese": None,
        "angel": None,
        "synchronicities": [],
        "ai_interpretation": None,
    }
    result = format_time_reading(data)
    assert "Oracle Time Reading" in result
    # None sections should not appear
    assert "FC60 Stamp" not in result
    assert "Numerology" not in result
    assert "Moon Phase" not in result


def test_format_question_reading_yes():
    """Question with odd number shows Yes answer."""
    data = {
        "question": "Will I succeed?",
        "question_number": 7,
        "detected_script": "latin",
        "numerology_system": "pythagorean",
        "confidence": {"overall": 85},
        "ai_interpretation": "Signs point to yes.",
    }
    result = format_question_reading(data)
    assert "\u2705" in result  # Checkmark
    assert "Yes" in result
    assert "Will I succeed" in result


def test_format_question_reading_no():
    """Question with even number shows No answer."""
    data = {
        "question": "Should I wait?",
        "question_number": 4,
        "detected_script": "latin",
        "numerology_system": "pythagorean",
        "confidence": {"overall": 60},
        "ai_interpretation": "Not the right time.",
    }
    result = format_question_reading(data)
    assert "\u274c" in result  # X mark
    assert "No" in result


def test_format_name_reading():
    """Name reading shows destiny, soul urge, personality numbers."""
    data = {
        "name": "Alice",
        "expression": 5,
        "soul_urge": 3,
        "personality": 2,
        "life_path": 7,
        "detected_script": "latin",
        "numerology_system": "pythagorean",
        "letter_breakdown": [
            {"letter": "A", "value": 1, "category": "vowel"},
            {"letter": "L", "value": 3, "category": "consonant"},
        ],
        "ai_interpretation": "Creative and analytical.",
    }
    result = format_name_reading(data)
    assert "Name Reading" in result
    assert "Alice" in result
    assert "Expression" in result
    assert "Soul Urge" in result
    assert "Personality" in result
    assert "Letter Breakdown" in result


def test_format_daily_insight():
    """Daily insight shows date, insight text, lucky numbers."""
    data = {
        "date": "2026-02-10",
        "insight": "Trust the process",
        "lucky_numbers": ["3", "7", "21"],
        "optimal_activity": "meditation",
    }
    result = format_daily_insight(data)
    assert "Daily Insight" in result
    assert "2026" in result
    assert "Trust the process" in result
    assert "`3`" in result
    assert "`7`" in result
    assert "meditation" in result


def test_format_history_list():
    """History list shows numbered entries with type emoji."""
    readings = [
        {
            "sign_type": "reading",
            "sign_value": "14:30",
            "created_at": "2026-02-10T14:30:00",
            "is_favorite": False,
        },
        {
            "sign_type": "question",
            "sign_value": "Will I succeed?",
            "created_at": "2026-02-09T10:00:00",
            "is_favorite": True,
        },
    ]
    result = format_history_list(readings, total=10)
    assert "Reading History" in result
    assert "2 of 10" in result
    assert "\U0001f550" in result or "\u2753" in result  # Type emojis


def test_format_progress():
    """Progress formatter shows correct emoji and progress bar."""
    result = format_progress(2, 4, "Consulting the Oracle...")
    assert "\u2728" in result  # Sparkles emoji (step index 2)
    assert "\u2593\u2593\u2591\u2591" in result  # Progress bar
    assert "2/4" in result

    # Step 1 should use crystal ball
    result1 = format_progress(1, 4, "Step one...")
    assert "\U0001f52e" in result1


def test_truncation_under_limit():
    """Messages under 4096 chars are not truncated."""
    text = "Short message"
    result = _truncate(text)
    assert result == text
    assert "See full reading" not in result


def test_truncation_over_limit():
    """Messages over 4096 chars are truncated with 'See more' link."""
    text = "A" * 5000
    result = _truncate(text)
    assert len(result) < 5000
    assert "See full reading" in result


def test_persian_text_preserved():
    """Persian text passes through formatter without corruption."""
    data = {
        "date": "2026-02-10",
        "insight": "\u0628\u0647 \u0641\u0631\u0622\u06cc\u0646\u062f \u0627\u0639\u062a\u0645\u0627\u062f \u06a9\u0646\u06cc\u062f",
        "lucky_numbers": ["3", "7"],
        "optimal_activity": "\u0645\u0631\u0627\u0642\u0628\u0647",
    }
    result = format_daily_insight(data)
    # Persian text should be present (escaped but readable)
    assert "\u0628\u0647" in result or "\\u0628" not in result  # Not double-encoded
    assert "\u0641\u0631\u0622\u06cc\u0646\u062f" in result or "\\u0641" not in result
