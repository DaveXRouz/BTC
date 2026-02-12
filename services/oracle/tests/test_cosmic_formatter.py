"""Tests for CosmicFormatter — cosmic cycle data extraction and formatting."""

import sys
from pathlib import Path

# Ensure oracle_service and framework are importable  # noqa: E402
project_root = Path(__file__).resolve().parents[3]
oracle_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(oracle_root))

from oracle_service.cosmic_formatter import CosmicFormatter  # noqa: E402

# ─── Test Fixtures ────────────────────────────────────────────────────────────

SAMPLE_READING = {
    "moon": {
        "phase_name": "Waning Gibbous",
        "emoji": "\U0001f316",
        "age": 19.05,
        "illumination": 87.3,
        "energy": "Share",
        "best_for": "Teaching, distributing, gratitude",
        "avoid": "Hoarding",
    },
    "ganzhi": {
        "year": {
            "animal_name": "Horse",
            "element": "Fire",
            "polarity": "Yang",
            "traditional_name": "Fire Horse",
            "gz_token": "BI-HO",
        },
        "day": {
            "animal_name": "Rat",
            "element": "Wood",
            "polarity": "Yang",
            "gz_token": "JA-RA",
        },
    },
    "current": {
        "weekday": "Friday",
        "planet": "Venus",
        "domain": "Love, values, beauty",
    },
}


# ─── format_moon ──────────────────────────────────────────────────────────────


class TestFormatMoon:
    def test_full_data(self):
        """Full moon data returns all expected fields."""
        result = CosmicFormatter.format_moon(SAMPLE_READING)
        assert result is not None
        assert result["phase_name"] == "Waning Gibbous"
        assert result["emoji"] == "\U0001f316"
        assert result["age"] == 19.05
        assert result["illumination"] == 87.3
        assert result["energy"] == "Share"
        assert result["best_for"] == "Teaching, distributing, gratitude"
        assert result["avoid"] == "Hoarding"

    def test_missing_key(self):
        """Missing 'moon' key in reading returns None."""
        assert CosmicFormatter.format_moon({}) is None

    def test_empty_moon(self):
        """Empty moon dict returns None."""
        assert CosmicFormatter.format_moon({"moon": {}}) is None


# ─── format_ganzhi ────────────────────────────────────────────────────────────


class TestFormatGanzhi:
    def test_year_and_day(self):
        """Ganzhi data with year and day cycles formatted correctly."""
        result = CosmicFormatter.format_ganzhi(SAMPLE_READING)
        assert result is not None
        assert result["year"]["animal_name"] == "Horse"
        assert result["year"]["element"] == "Fire"
        assert result["year"]["polarity"] == "Yang"
        assert result["year"]["traditional_name"] == "Fire Horse"
        assert result["year"]["gz_token"] == "BI-HO"
        assert result["day"]["animal_name"] == "Rat"
        assert result["day"]["element"] == "Wood"
        assert result["day"]["gz_token"] == "JA-RA"

    def test_with_hour(self):
        """Ganzhi data including hour cycle formatted correctly."""
        reading = dict(SAMPLE_READING)
        reading["ganzhi"] = {
            **SAMPLE_READING["ganzhi"],
            "hour": {"animal_name": "Tiger"},
        }
        result = CosmicFormatter.format_ganzhi(reading)
        assert result is not None
        assert result["hour"]["animal_name"] == "Tiger"

    def test_no_hour(self):
        """Missing hour cycle doesn't crash, returns year+day only."""
        result = CosmicFormatter.format_ganzhi(SAMPLE_READING)
        assert result is not None
        assert "hour" not in result

    def test_missing_key(self):
        """Missing 'ganzhi' key in reading returns None."""
        assert CosmicFormatter.format_ganzhi({}) is None


# ─── format_current_moment ────────────────────────────────────────────────────


class TestFormatCurrentMoment:
    def test_full_data(self):
        """Current moment data returns weekday, planet, domain."""
        result = CosmicFormatter.format_current_moment(SAMPLE_READING)
        assert result is not None
        assert result["weekday"] == "Friday"
        assert result["planet"] == "Venus"
        assert result["domain"] == "Love, values, beauty"

    def test_missing_key(self):
        """Missing 'current' key returns None."""
        assert CosmicFormatter.format_current_moment({}) is None


# ─── format_planet_moon_combo ─────────────────────────────────────────────────


class TestFormatPlanetMoonCombo:
    def test_valid_combo(self):
        """Planet-moon combo returns theme and message from SignalCombiner."""
        result = CosmicFormatter.format_planet_moon_combo("Venus", "Full Moon")
        assert result is not None
        assert "theme" in result
        assert "message" in result
        assert len(result["theme"]) > 0
        assert len(result["message"]) > 0

    def test_empty_planet(self):
        """Empty planet returns None."""
        assert CosmicFormatter.format_planet_moon_combo("", "Full Moon") is None

    def test_empty_moon_phase(self):
        """Empty moon phase returns None."""
        assert CosmicFormatter.format_planet_moon_combo("Venus", "") is None


# ─── format_cosmic_cycles ─────────────────────────────────────────────────────


class TestFormatCosmicCycles:
    def test_complete(self):
        """Complete reading produces all four sections."""
        result = CosmicFormatter.format_cosmic_cycles(SAMPLE_READING)
        assert result["moon"] is not None
        assert result["ganzhi"] is not None
        assert result["current"] is not None
        assert result["planet_moon"] is not None

    def test_empty_reading(self):
        """Empty reading dict returns all-None sections."""
        result = CosmicFormatter.format_cosmic_cycles({})
        assert result["moon"] is None
        assert result["ganzhi"] is None
        assert result["current"] is None
        assert result["planet_moon"] is None

    def test_partial_moon_only(self):
        """Reading with only moon data returns moon section, others None."""
        reading = {"moon": SAMPLE_READING["moon"]}
        result = CosmicFormatter.format_cosmic_cycles(reading)
        assert result["moon"] is not None
        assert result["ganzhi"] is None
        assert result["current"] is None
        # planet_moon requires both moon and current
        assert result["planet_moon"] is None
