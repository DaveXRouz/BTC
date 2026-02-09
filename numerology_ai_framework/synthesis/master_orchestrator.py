"""
Master Orchestrator - Synthesis Tier
=====================================
Purpose: Coordinate all modules to generate complete AI-ready readings
         Main entry point for the entire framework

Input: Personal data (name, birthdate, location, current time)
Output: Complete numerological analysis with confidence scoring

Pipeline (10 steps):
1. Validate inputs + resolve current_date/time
2. FC60 stamp (Mode A) via FC60StampEngine
3. Numerology via NumerologyEngine
4. Moon phase via MoonEngine
5. Ganzhi (year + day + hour) via GanzhiEngine
6. Heartbeat via HeartbeatEngine
7. Location via LocationEngine (if coords given)
8. Reading via ReadingEngine
9. Translation via UniverseTranslator
10. Assemble final dict
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.julian_date_engine import JulianDateEngine
from core.base60_codec import Base60Codec
from core.weekday_calculator import WeekdayCalculator
from core.checksum_validator import ChecksumValidator
from core.fc60_stamp_engine import FC60StampEngine
from personal.numerology_engine import NumerologyEngine
from personal.heartbeat_engine import HeartbeatEngine
from universal.moon_engine import MoonEngine
from universal.ganzhi_engine import GanzhiEngine
from universal.location_engine import LocationEngine
from synthesis.reading_engine import ReadingEngine
from synthesis.universe_translator import UniverseTranslator
from datetime import datetime
from typing import Dict, Optional


class MasterOrchestrator:
    """
    Central coordinator for all FC60 numerology calculations.

    This is the AI's main interface to the framework.
    """

    @staticmethod
    def generate_reading(
        full_name: str,
        birth_day: int,
        birth_month: int,
        birth_year: int,
        current_date: Optional[datetime] = None,
        mother_name: Optional[str] = None,
        gender: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        actual_bpm: Optional[int] = None,
        current_hour: Optional[int] = None,
        current_minute: Optional[int] = None,
        current_second: Optional[int] = None,
        tz_hours: int = 0,
        tz_minutes: int = 0,
        numerology_system: str = "pythagorean",
        mode: str = "full",
    ) -> Dict:
        """
        Generate complete numerological reading.

        Args:
            full_name: Person's full name
            birth_day, birth_month, birth_year: Birthdate
            current_date: Date to analyze (defaults to today)
            mother_name: Mother's full name (optional)
            gender: 'male'/'female'/None (optional)
            latitude, longitude: Location coordinates (optional)
            actual_bpm: Actual heart rate if known (optional)
            current_hour, current_minute, current_second: Time (optional)
            tz_hours, tz_minutes: Timezone offset (default UTC)
            numerology_system: 'pythagorean' or 'chaldean'
            mode: 'full' or 'stamp_only'

        Returns:
            Complete reading dictionary with all calculated values
        """
        # Step 1: Validate + resolve current date/time
        if current_date is None:
            current_date = datetime.now()

        year = current_date.year
        month = current_date.month
        day = current_date.day
        hour = current_hour if current_hour is not None else current_date.hour
        minute = current_minute if current_minute is not None else current_date.minute
        second = current_second if current_second is not None else current_date.second
        has_time = current_hour is not None or current_minute is not None

        # Step 2: FC60 stamp (Mode A)
        fc60_stamp = FC60StampEngine.encode(
            year,
            month,
            day,
            hour,
            minute,
            second,
            tz_hours,
            tz_minutes,
            has_time=has_time,
        )

        if mode == "stamp_only":
            return {"fc60_stamp": fc60_stamp}

        # Step 3: Numerology
        numerology = NumerologyEngine.complete_profile(
            full_name=full_name,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
            current_year=year,
            current_month=month,
            current_day=day,
            mother_name=mother_name,
            system=numerology_system,
            gender=gender,
        )

        # Step 4: Moon phase
        current_jdn = fc60_stamp["_jdn"]
        moon_data = MoonEngine.full_moon_info(current_jdn)

        # Step 5: Ganzhi (year + day + hour)
        ganzhi_data = {
            "year": GanzhiEngine.full_year_info(year),
            "day": GanzhiEngine.full_day_info(current_jdn),
        }
        if has_time:
            day_stem_idx = ganzhi_data["day"]["stem_index"]
            stem_idx, branch_idx = GanzhiEngine.hour_ganzhi(hour, day_stem_idx)
            ganzhi_data["hour"] = {
                "stem_token": GanzhiEngine.STEMS[stem_idx],
                "branch_token": GanzhiEngine.ANIMALS[branch_idx],
                "animal_name": GanzhiEngine.ANIMAL_NAMES[branch_idx],
            }

        # Step 6: Heartbeat
        birth_jdn = JulianDateEngine.gregorian_to_jdn(
            birth_year, birth_month, birth_day
        )
        age_days = current_jdn - birth_jdn
        age_years = int(age_days // 365.25)
        heartbeat_data = HeartbeatEngine.heartbeat_profile(age_years, actual_bpm)

        # Step 7: Location (if coordinates given)
        location_data = None
        if latitude is not None and longitude is not None:
            location_data = LocationEngine.location_signature(latitude, longitude)

        # Step 8: Reading
        reading = ReadingEngine.generate_reading(
            fc60_stamp=fc60_stamp,
            numerology_profile=numerology,
            moon_data=moon_data,
            ganzhi_data=ganzhi_data,
            heartbeat_data=heartbeat_data,
            location_data=location_data,
        )

        # Step 9: Calculate confidence (before translation so we can pass it)
        confidence_data = MasterOrchestrator._calculate_confidence(
            numerology,
            moon_data,
            ganzhi_data,
            heartbeat_data,
            location_data,
            reading,
        )

        # Step 10: Translation (with unified confidence)
        translation = UniverseTranslator.translate(
            reading=reading,
            fc60_stamp=fc60_stamp,
            numerology_profile=numerology,
            person_name=full_name,
            current_date_str=current_date.strftime("%Y-%m-%d"),
            confidence_override=confidence_data["score"],
        )

        # Step 10: Assemble final dict
        # Preserve backward-compatible keys
        birth_weekday = WeekdayCalculator.full_info(birth_jdn)
        current_weekday = WeekdayCalculator.full_info(current_jdn)

        result = {
            # Backward-compatible keys
            "person": {
                "name": full_name,
                "birthdate": f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
                "age_years": age_years,
                "age_days": age_days,
            },
            "birth": {
                "jdn": birth_jdn,
                "jdn_fc60": Base60Codec.encode_base60(birth_jdn),
                "weekday": birth_weekday["name"],
                "planet": birth_weekday["planet"],
                "year_fc60": Base60Codec.encode_base60(birth_year),
            },
            "current": {
                "date": current_date.strftime("%Y-%m-%d"),
                "jdn": current_jdn,
                "jdn_fc60": fc60_stamp["j60"],
                "weekday": current_weekday["name"],
                "planet": current_weekday["planet"],
                "domain": current_weekday["domain"],
                "year_fc60": fc60_stamp["y60"],
            },
            "numerology": numerology,
            "patterns": MasterOrchestrator._detect_patterns(
                numerology, current_weekday, reading
            ),
            "confidence": confidence_data,
            "synthesis": translation.get("full_text", ""),
            # New keys (v2.0)
            "fc60_stamp": fc60_stamp,
            "moon": moon_data,
            "ganzhi": ganzhi_data,
            "heartbeat": heartbeat_data,
            "location": location_data,
            "reading": reading,
            "translation": translation,
        }

        return result

    @staticmethod
    def _detect_patterns(numerology: Dict, weekday: Dict, reading: Dict = None) -> Dict:
        """Detect meaningful patterns across all numbers and animals."""
        patterns = []

        # Number repetitions
        lp = numerology["life_path"]["number"]
        exp = numerology["expression"]
        soul = numerology["soul_urge"]
        pers = numerology["personality"]
        py = numerology["personal_year"]

        numbers = [lp, exp, soul, pers, py]
        from collections import Counter

        counts = Counter(numbers)

        for num, count in counts.items():
            if count >= 2:
                patterns.append(
                    {
                        "type": "number_repetition",
                        "number": num,
                        "occurrences": count,
                        "strength": "high" if count >= 3 else "medium",
                        "message": f"The number {num} appears {count} times - major theme",
                    }
                )

        # Master numbers
        if lp in {11, 22, 33}:
            patterns.append(
                {
                    "type": "master_number",
                    "number": lp,
                    "strength": "very_high",
                    "message": f"Life Path {lp} is a Master Number - heightened spiritual potential",
                }
            )

        # Animal repetitions from reading
        if reading:
            for rep in reading.get("animal_repetitions", []):
                patterns.append(
                    {
                        "type": "animal_repetition",
                        "animal": rep["animal_name"],
                        "occurrences": rep["count"],
                        "strength": "very_high" if rep["count"] >= 3 else "high",
                        "message": f"The {rep['animal_name']} appears {rep['count']} times - {rep['trait']}",
                    }
                )

        return {"detected": patterns, "count": len(patterns)}

    @staticmethod
    def _calculate_confidence(
        numerology: Dict,
        moon_data: Dict = None,
        ganzhi_data: Dict = None,
        heartbeat_data: Dict = None,
        location_data: Dict = None,
        reading: Dict = None,
    ) -> Dict:
        """Calculate confidence score for the reading."""
        score = 50  # Base

        # +10% for numerology profile (always present)
        score += 10

        # +10% for mother's name
        if "mother_influence" in numerology:
            score += 10

        # +5% for moon data
        if moon_data:
            score += 5

        # +5% for ganzhi data
        if ganzhi_data:
            score += 5

        # +5% for heartbeat data
        if heartbeat_data:
            score += 5

        # +5% for location data
        if location_data:
            score += 5

        # +5% for master numbers
        if numerology["life_path"]["number"] in {11, 22, 33}:
            score += 5

        # +5% for animal repetitions
        if reading and reading.get("animal_repetitions"):
            score += 5

        # Cap at 95%
        score = min(95, max(50, score))

        level = "medium"
        if score >= 85:
            level = "very_high"
        elif score >= 75:
            level = "high"
        elif score < 65:
            level = "low"

        return {
            "score": score,
            "level": level,
            "factors": f"Based on {sum(1 for x in [moon_data, ganzhi_data, heartbeat_data, location_data] if x) + 2} data sources",
        }


def demo():
    """Run a demonstration of the master orchestrator."""
    print("=" * 70)
    print("MASTER ORCHESTRATOR - DEMONSTRATION")
    print("=" * 70)

    reading = MasterOrchestrator.generate_reading(
        full_name="Alice Johnson",
        birth_day=15,
        birth_month=7,
        birth_year=1990,
        current_date=datetime(2026, 2, 9),
        mother_name="Barbara Johnson",
        gender="female",
        latitude=40.7,
        longitude=-74.0,
        actual_bpm=68,
        current_hour=14,
        current_minute=30,
        current_second=0,
        tz_hours=-5,
        tz_minutes=0,
        numerology_system="pythagorean",
    )

    # Display results
    print(f"\nPERSON: {reading['person']['name']}")
    print(
        f"Born: {reading['birth']['weekday']} ({reading['birth']['planet']}), {reading['person']['birthdate']}"
    )
    print(
        f"Age: {reading['person']['age_years']} years ({reading['person']['age_days']} days)"
    )

    print(f"\nFC60 STAMP: {reading['fc60_stamp']['fc60']}")
    print(f"CHK: {reading['fc60_stamp']['chk']}")

    print(f"\nNUMEROLOGY:")
    print(
        f"  Life Path: {reading['numerology']['life_path']['number']} - {reading['numerology']['life_path']['title']}"
    )
    print(f"  Expression: {reading['numerology']['expression']}")
    print(f"  Soul Urge: {reading['numerology']['soul_urge']}")
    print(f"  Personality: {reading['numerology']['personality']}")
    print(f"  Personal Year: {reading['numerology']['personal_year']}")
    print(f"  Personal Month: {reading['numerology']['personal_month']}")
    print(f"  Personal Day: {reading['numerology']['personal_day']}")

    print(
        f"\nMOON: {reading['moon']['emoji']} {reading['moon']['phase_name']} (age {reading['moon']['age']}d)"
    )
    print(
        f"GANZHI: {reading['ganzhi']['year']['gz_token']} ({reading['ganzhi']['year']['traditional_name']})"
    )
    print(
        f"HEARTBEAT: {reading['heartbeat']['bpm']} BPM ({reading['heartbeat']['element']})"
    )
    if reading["location"]:
        print(
            f"LOCATION: {reading['location']['element']} element, TZ={reading['location']['timezone_estimate']}"
        )

    print(f"\nPATTERNS: {reading['patterns']['count']} detected")
    for pattern in reading["patterns"]["detected"]:
        print(f"  - {pattern['message']}")

    print(
        f"\nCONFIDENCE: {reading['confidence']['score']}% ({reading['confidence']['level']})"
    )

    print("\n" + "=" * 70)
    print("FULL READING:")
    print("=" * 70)
    print(
        reading["synthesis"][:500] + "..."
        if len(reading["synthesis"]) > 500
        else reading["synthesis"]
    )
    print("=" * 70)

    return reading


if __name__ == "__main__":
    demo()
