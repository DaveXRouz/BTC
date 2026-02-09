#!/usr/bin/env python3
"""
Quick Start Example - FC60 Numerology Framework
Run this to see a complete demo of the framework in action
"""

from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime


def main():
    print("=" * 70)
    print("FC60 NUMEROLOGY FRAMEWORK - QUICK START EXAMPLE")
    print("=" * 70)

    # Example 1: Full reading with all 7 input dimensions
    print("\nExample 1: Full Reading (all inputs)\n")

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

    print(f"Name: {reading['person']['name']}")
    print(
        f"Born: {reading['birth']['weekday']} ({reading['birth']['planet']}), {reading['person']['birthdate']}"
    )
    print(
        f"Age: {reading['person']['age_years']} years ({reading['person']['age_days']} days)"
    )
    print(f"\nFC60 Stamp: {reading['fc60_stamp']['fc60']}")
    print(f"CHK: {reading['fc60_stamp']['chk']}")
    print(
        f"\nLife Path: {reading['numerology']['life_path']['number']} - {reading['numerology']['life_path']['title']}"
    )
    print(f"Expression: {reading['numerology']['expression']}")
    print(f"Soul Urge: {reading['numerology']['soul_urge']}")
    print(f"Personal Year: {reading['numerology']['personal_year']}")
    print(f"Personal Month: {reading['numerology']['personal_month']}")
    print(f"Personal Day: {reading['numerology']['personal_day']}")
    print(
        f"\nMoon: {reading['moon']['emoji']} {reading['moon']['phase_name']} (age {reading['moon']['age']}d)"
    )
    print(
        f"Ganzhi Year: {reading['ganzhi']['year']['gz_token']} ({reading['ganzhi']['year']['traditional_name']})"
    )
    print(
        f"Heartbeat: {reading['heartbeat']['bpm']} BPM ({reading['heartbeat']['element']})"
    )
    if reading["location"]:
        print(
            f"Location: {reading['location']['element']} element, TZ={reading['location']['timezone_estimate']}"
        )
    print(f"\nPatterns: {reading['patterns']['count']} detected")
    for pattern in reading["patterns"]["detected"]:
        print(f"  - {pattern['message']}")
    print(
        f"\nConfidence: {reading['confidence']['score']}% ({reading['confidence']['level']})"
    )

    # Example 2: Minimal reading (name + birthdate only)
    print("\n" + "=" * 70)
    print("\nExample 2: Minimal Reading (name + birthdate only)\n")

    reading2 = MasterOrchestrator.generate_reading(
        full_name="James Chen",
        birth_day=5,
        birth_month=3,
        birth_year=1988,
        current_date=datetime(2026, 2, 9),
    )

    print(f"Name: {reading2['person']['name']}")
    print(
        f"Life Path: {reading2['numerology']['life_path']['number']} - {reading2['numerology']['life_path']['title']}"
    )
    print(f"Personal Year: {reading2['numerology']['personal_year']}")
    print(
        f"Confidence: {reading2['confidence']['score']}% ({reading2['confidence']['level']})"
    )

    # Example 3: Stamp-only mode
    print("\n" + "=" * 70)
    print("\nExample 3: Stamp-Only Mode\n")

    stamp = MasterOrchestrator.generate_reading(
        full_name="",
        birth_day=1,
        birth_month=1,
        birth_year=2000,
        current_date=datetime(2026, 2, 9),
        current_hour=14,
        current_minute=30,
        current_second=0,
        mode="stamp_only",
    )

    print(f"FC60: {stamp['fc60_stamp']['fc60']}")
    print(f"J60:  {stamp['fc60_stamp']['j60']}")
    print(f"Y60:  {stamp['fc60_stamp']['y60']}")
    print(f"CHK:  {stamp['fc60_stamp']['chk']}")

    # Example 4: Full synthesis output
    print("\n" + "=" * 70)
    print("\nExample 4: Complete Synthesis\n")
    synth = reading["synthesis"]
    print(synth[:600] + "..." if len(synth) > 600 else synth)

    print("\n" + "=" * 70)
    print("All examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
