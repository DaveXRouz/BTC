"""Cosmic cycle data formatter.

Extracts moon phase, Ganzhi (Chinese zodiac), and current moment data
from MasterOrchestrator reading output. Formats for API serialization
and frontend display.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from numerology_ai_framework.synthesis.signal_combiner import SignalCombiner

    _HAS_SIGNAL_COMBINER = True
except ImportError:
    _HAS_SIGNAL_COMBINER = False
    logger.warning("SignalCombiner not available — planet_moon combos disabled")


class CosmicFormatter:
    """Format cosmic cycle data from framework reading output."""

    @staticmethod
    def format_moon(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and format moon phase data.

        Args:
            reading: Full framework output dict from MasterOrchestrator.

        Returns:
            Dict with phase_name, emoji, age, illumination, energy,
            best_for, avoid — or None if moon data missing.
        """
        moon = reading.get("moon")
        if not moon:
            return None

        return {
            "phase_name": moon.get("phase_name", ""),
            "emoji": moon.get("emoji", ""),
            "age": moon.get("age", 0.0),
            "illumination": moon.get("illumination", 0.0),
            "energy": moon.get("energy", ""),
            "best_for": moon.get("best_for", ""),
            "avoid": moon.get("avoid", ""),
        }

    @staticmethod
    def format_ganzhi(reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and format Ganzhi (Chinese zodiac) data.

        Args:
            reading: Full framework output dict from MasterOrchestrator.

        Returns:
            Dict with year, day, and optional hour cycle data —
            or None if ganzhi data missing.
        """
        ganzhi = reading.get("ganzhi")
        if not ganzhi:
            return None

        result: Dict[str, Any] = {}

        year = ganzhi.get("year")
        if year:
            result["year"] = {
                "animal_name": year.get("animal_name", ""),
                "element": year.get("element", ""),
                "polarity": year.get("polarity", ""),
                "traditional_name": year.get("traditional_name", ""),
                "gz_token": year.get("gz_token", ""),
            }

        day = ganzhi.get("day")
        if day:
            result["day"] = {
                "animal_name": day.get("animal_name", ""),
                "element": day.get("element", ""),
                "polarity": day.get("polarity", ""),
                "gz_token": day.get("gz_token", ""),
            }

        hour = ganzhi.get("hour")
        if hour:
            result["hour"] = {
                "animal_name": hour.get("animal_name", ""),
            }

        if not result:
            return None

        return result

    @staticmethod
    def format_current_moment(
        reading: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Extract and format current moment data (planet, domain, weekday).

        Args:
            reading: Full framework output dict from MasterOrchestrator.

        Returns:
            Dict with weekday, planet, domain — or None if current data missing.
        """
        current = reading.get("current")
        if not current:
            return None

        return {
            "weekday": current.get("weekday", ""),
            "planet": current.get("planet", ""),
            "domain": current.get("domain", ""),
        }

    @staticmethod
    def format_planet_moon_combo(
        planet: str,
        moon_phase: str,
    ) -> Optional[Dict[str, str]]:
        """Get planet-moon combination insight from SignalCombiner.

        Args:
            planet: Ruling planet of the day (e.g. "Venus").
            moon_phase: Moon phase name (e.g. "Full Moon").

        Returns:
            Dict with theme and message — or None if unavailable.
        """
        if not _HAS_SIGNAL_COMBINER:
            return None

        if not planet or not moon_phase:
            return None

        try:
            result = SignalCombiner.planet_meets_moon(planet, moon_phase)
            return {
                "theme": result.get("theme", ""),
                "message": result.get("message", ""),
            }
        except (KeyError, TypeError, AttributeError) as e:
            logger.error("planet_meets_moon failed: %s", e)
            return None

    @staticmethod
    def format_cosmic_cycles(reading: Dict[str, Any]) -> Dict[str, Any]:
        """Format all cosmic cycle data into a single response dict.

        This is the primary entry point. Returns:
        {
            'moon': { phase_name, emoji, age, illumination, energy, best_for, avoid },
            'ganzhi': {
                'year': { animal_name, element, polarity, traditional_name, gz_token },
                'day': { animal_name, element, polarity, gz_token },
                'hour': { animal_name } | None,
            },
            'current': { weekday, planet, domain },
            'planet_moon': { theme, message } | None,
        }

        Args:
            reading: Full framework output dict from MasterOrchestrator.

        Returns:
            Dict with moon, ganzhi, current, planet_moon sections.
            Missing sections are None.
        """
        moon = CosmicFormatter.format_moon(reading)
        ganzhi = CosmicFormatter.format_ganzhi(reading)
        current = CosmicFormatter.format_current_moment(reading)

        planet_moon = None
        if moon and current:
            planet_moon = CosmicFormatter.format_planet_moon_combo(
                current.get("planet", ""),
                moon.get("phase_name", ""),
            )

        return {
            "moon": moon,
            "ganzhi": ganzhi,
            "current": current,
            "planet_moon": planet_moon,
        }
