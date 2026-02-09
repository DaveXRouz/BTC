# 06 -- API Integration Template

**Version:** 1.0
**Framework:** FC60 Numerology AI Framework
**Purpose:** Ready-to-use templates for integrating the framework into AI applications, web services, and standalone scripts. Supersedes `INTEGRATION_GUIDE.md` at the project root.

**Note:** This document is the comprehensive version. For the original quick-start guide, see `/INTEGRATION_GUIDE.md`. This file covers everything in that guide plus system prompts, JSON schemas, and deployable code templates.

---

## Section A: System Prompt Template

Use this system prompt (or adapt it) when configuring an AI model to use the FC60 framework. It references the `logic/` documentation layer so the model knows where to find detailed guidance.

```
You are a numerology assistant powered by the FC60 Numerology AI Framework.

RULES:
1. Never calculate numbers yourself. Always call MasterOrchestrator.generate_reading() and use the values it returns.
2. Never invent or estimate values. Every number in your output must come from the engine.
3. Always include the FC60 stamp, confidence percentage, and timezone in your response.
4. Use "the numbers suggest" language. Never make absolute predictions.
5. Always include a disclaimer that this is pattern observation, not prediction.
6. Cap confidence at 95% even with all inputs provided.
7. Master Numbers (11, 22, 33) never reduce further.

TONE:
- Warm, honest, specific. Reference actual numbers from the calculation.
- Ground interpretations in mathematics, not mysticism.
- Acknowledge uncertainty. State what data is missing.
- Include shadow warnings (Caution section) -- do not skip them.
- Be compassionate but not flattering.

READING STRUCTURE (9 sections):
1. Header: Name, date, confidence
2. Universal Address: FC60 stamp, J60, Y60
3. Core Identity: Life Path, Expression, Soul Urge, Personality
4. Right Now: Planetary day, moon phase, hour energy
5. Patterns: Repeated animals, repeated numbers
6. The Message: 3-5 sentence synthesis
7. Today's Advice: 3 actionable items
8. Caution: Shadow warnings
9. Footer: Confidence, data sources, disclaimer

DOCUMENTATION:
- Reading composition guide: logic/04_READING_COMPOSITION_GUIDE.md
- Error handling: logic/05_ERROR_HANDLING_AND_EDGE_CASES.md
- Input collection: logic/01_INPUT_COLLECTION_GUIDE.md
- Calculation reference: logic/02_CALCULATION_REFERENCE.md

ENTRY POINT:
from synthesis.master_orchestrator import MasterOrchestrator
reading = MasterOrchestrator.generate_reading(
    full_name=..., birth_day=..., birth_month=..., birth_year=...,
    current_date=..., mother_name=..., gender=...,
    latitude=..., longitude=..., actual_bpm=...,
    current_hour=..., current_minute=..., current_second=...,
    tz_hours=..., tz_minutes=...,
)
```

---

## Section B: JSON Schema for Input

All 6 input dimensions with types, constraints, and defaults.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "FC60 Numerology Reading Request",
  "type": "object",
  "required": ["full_name", "birth_day", "birth_month", "birth_year"],
  "properties": {
    "full_name": {
      "type": "string",
      "description": "Person's full name. Only A-Z letters are used for numerology calculations. All other characters are stripped.",
      "minLength": 0
    },
    "birth_day": {
      "type": "integer",
      "description": "Day of birth (1-31, validated against month)",
      "minimum": 1,
      "maximum": 31
    },
    "birth_month": {
      "type": "integer",
      "description": "Month of birth (1=January, 12=December)",
      "minimum": 1,
      "maximum": 12
    },
    "birth_year": {
      "type": "integer",
      "description": "Year of birth (4-digit Gregorian year)"
    },
    "mother_name": {
      "type": "string",
      "description": "Mother's full name. Adds maternal influence to the reading (+10% confidence).",
      "default": null
    },
    "gender": {
      "type": "string",
      "description": "Gender for polarity mapping. male=Yang, female=Yin, omitted=Neutral.",
      "enum": ["male", "female"],
      "default": null
    },
    "latitude": {
      "type": "number",
      "description": "Geographic latitude (-90 to 90). Positive=North, Negative=South.",
      "minimum": -90,
      "maximum": 90,
      "default": null
    },
    "longitude": {
      "type": "number",
      "description": "Geographic longitude (-180 to 180). Positive=East, Negative=West.",
      "minimum": -180,
      "maximum": 180,
      "default": null
    },
    "actual_bpm": {
      "type": "integer",
      "description": "Actual resting heart rate in beats per minute. If omitted, age-based estimation is used.",
      "minimum": 1,
      "default": null
    },
    "current_hour": {
      "type": "integer",
      "description": "Hour of the reading (0-23, 24-hour format). If omitted, time-specific analysis is skipped.",
      "minimum": 0,
      "maximum": 23,
      "default": null
    },
    "current_minute": {
      "type": "integer",
      "description": "Minute of the reading (0-59).",
      "minimum": 0,
      "maximum": 59,
      "default": null
    },
    "current_second": {
      "type": "integer",
      "description": "Second of the reading (0-59).",
      "minimum": 0,
      "maximum": 59,
      "default": null
    },
    "tz_hours": {
      "type": "integer",
      "description": "Timezone offset hours from UTC (-12 to +14). Default: 0 (UTC).",
      "minimum": -12,
      "maximum": 14,
      "default": 0
    },
    "tz_minutes": {
      "type": "integer",
      "description": "Timezone offset minutes (0-59). Used for zones like UTC+5:30 or UTC+5:45.",
      "minimum": 0,
      "maximum": 59,
      "default": 0
    },
    "current_date": {
      "type": "string",
      "format": "date",
      "description": "Date of the reading in YYYY-MM-DD format. If omitted, today's date is used.",
      "default": null
    },
    "numerology_system": {
      "type": "string",
      "description": "Which letter-value table to use for name calculations.",
      "enum": ["pythagorean", "chaldean"],
      "default": "pythagorean"
    },
    "mode": {
      "type": "string",
      "description": "Output mode. 'full' returns complete reading. 'stamp_only' returns only the FC60 stamp.",
      "enum": ["full", "stamp_only"],
      "default": "full"
    }
  }
}
```

---

## Section C: JSON Schema for Output

The structure of the dictionary returned by `MasterOrchestrator.generate_reading()`.

```json
{
  "title": "FC60 Numerology Reading Response",
  "type": "object",
  "properties": {
    "person": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "birthdate": { "type": "string", "format": "date" },
        "age_years": { "type": "integer" },
        "age_days": { "type": "integer" }
      }
    },
    "birth": {
      "type": "object",
      "properties": {
        "jdn": {
          "type": "integer",
          "description": "Julian Day Number of birth date"
        },
        "jdn_fc60": {
          "type": "string",
          "description": "Birth JDN in base-60 encoding"
        },
        "weekday": { "type": "string", "description": "Day of week at birth" },
        "planet": {
          "type": "string",
          "description": "Ruling planet of birth weekday"
        },
        "year_fc60": {
          "type": "string",
          "description": "Birth year in base-60"
        }
      }
    },
    "current": {
      "type": "object",
      "properties": {
        "date": { "type": "string", "format": "date" },
        "jdn": { "type": "integer" },
        "jdn_fc60": { "type": "string" },
        "weekday": { "type": "string" },
        "planet": { "type": "string" },
        "domain": { "type": "string" },
        "year_fc60": { "type": "string" }
      }
    },
    "fc60_stamp": {
      "type": "object",
      "properties": {
        "fc60": {
          "type": "string",
          "description": "Complete FC60 stamp string"
        },
        "iso": { "type": "string", "description": "ISO-8601 datetime" },
        "tz60": {
          "type": "string",
          "description": "Timezone in FC60 encoding"
        },
        "y60": { "type": "string", "description": "Year in base-60" },
        "y2k": { "type": "string", "description": "Year mod 60 from 2000" },
        "j60": { "type": "string", "description": "JDN in base-60" },
        "mjd60": {
          "type": "string",
          "description": "Modified Julian Date in base-60"
        },
        "rd60": { "type": "string", "description": "Rata Die in base-60" },
        "u60": { "type": "string", "description": "Unix seconds in base-60" },
        "chk": { "type": "string", "description": "Checksum token (4 chars)" }
      }
    },
    "numerology": {
      "type": "object",
      "properties": {
        "life_path": {
          "type": "object",
          "properties": {
            "number": { "type": "integer" },
            "title": { "type": "string" },
            "message": { "type": "string" }
          }
        },
        "expression": { "type": "integer" },
        "soul_urge": { "type": "integer" },
        "personality": { "type": "integer" },
        "personal_year": { "type": "integer" },
        "personal_month": { "type": "integer" },
        "personal_day": { "type": "integer" },
        "gender_polarity": {
          "type": "object",
          "properties": {
            "gender": { "type": ["string", "null"] },
            "polarity": { "type": "integer" },
            "label": { "type": "string", "enum": ["Yang", "Yin", "Neutral"] }
          }
        },
        "mother_influence": {
          "type": "integer",
          "description": "Present only if mother_name was provided"
        }
      }
    },
    "moon": {
      "type": "object",
      "properties": {
        "phase_name": { "type": "string" },
        "emoji": { "type": "string" },
        "age": { "type": "number" },
        "illumination": { "type": "number" },
        "energy": { "type": "string" },
        "best_for": { "type": "string" },
        "avoid": { "type": "string" }
      }
    },
    "ganzhi": {
      "type": "object",
      "properties": {
        "year": {
          "type": "object",
          "properties": {
            "gz_token": { "type": "string" },
            "traditional_name": { "type": "string" },
            "element": { "type": "string" },
            "polarity": { "type": "string" },
            "animal_name": { "type": "string" }
          }
        },
        "day": {
          "type": "object",
          "properties": {
            "gz_token": { "type": "string" },
            "element": { "type": "string" },
            "animal_name": { "type": "string" }
          }
        },
        "hour": {
          "type": "object",
          "description": "Present only if time was provided",
          "properties": {
            "stem_token": { "type": "string" },
            "branch_token": { "type": "string" },
            "animal_name": { "type": "string" }
          }
        }
      }
    },
    "heartbeat": {
      "type": "object",
      "properties": {
        "age": { "type": "integer" },
        "bpm": { "type": "integer" },
        "bpm_source": { "type": "string", "enum": ["actual", "estimated"] },
        "beats_per_day": { "type": "integer" },
        "total_lifetime_beats": { "type": "integer" },
        "element": { "type": "string" },
        "rhythm_token": { "type": "string" },
        "life_pulse_signature": { "type": "string" }
      }
    },
    "location": {
      "type": ["object", "null"],
      "description": "Null if no coordinates were provided",
      "properties": {
        "latitude": { "type": "number" },
        "longitude": { "type": "number" },
        "element": { "type": "string" },
        "timezone_estimate": { "type": "integer" },
        "lat_hemisphere": { "type": "string", "enum": ["N", "S"] },
        "lon_hemisphere": { "type": "string", "enum": ["E", "W"] },
        "lat_polarity": { "type": "string", "enum": ["Yang", "Yin"] },
        "lon_polarity": { "type": "string", "enum": ["Yang", "Yin"] }
      }
    },
    "patterns": {
      "type": "object",
      "properties": {
        "detected": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "strength": { "type": "string" },
              "message": { "type": "string" }
            }
          }
        },
        "count": { "type": "integer" }
      }
    },
    "confidence": {
      "type": "object",
      "properties": {
        "score": { "type": "integer", "minimum": 50, "maximum": 95 },
        "level": {
          "type": "string",
          "enum": ["low", "medium", "high", "very_high"]
        },
        "factors": { "type": "string" }
      }
    },
    "synthesis": {
      "type": "string",
      "description": "Complete human-readable reading text (9 sections concatenated)"
    },
    "reading": {
      "type": "object",
      "description": "Raw reading data from ReadingEngine (signals, animal_repetitions, etc.)"
    },
    "translation": {
      "type": "object",
      "description": "Individual sections (header, universal_address, core_identity, right_now, patterns, message, advice, caution, footer, full_text)"
    }
  }
}
```

---

## Section D: Example API Request/Response Pairs

### Full Example

**Request:**

```json
{
  "full_name": "Alice Johnson",
  "birth_day": 15,
  "birth_month": 7,
  "birth_year": 1990,
  "mother_name": "Barbara Johnson",
  "gender": "female",
  "latitude": 40.7,
  "longitude": -74.0,
  "actual_bpm": 68,
  "current_date": "2026-02-09",
  "current_hour": 14,
  "current_minute": 30,
  "current_second": 0,
  "tz_hours": -5,
  "tz_minutes": 0
}
```

**Response (key fields):**

```json
{
  "person": {
    "name": "Alice Johnson",
    "birthdate": "1990-07-15",
    "age_years": 35,
    "age_days": 12993
  },
  "fc60_stamp": {
    "fc60": "LU-OX-OXWA \ud83c\udf19TI-HOWU-RAWU",
    "j60": "TIFI-DRMT-GOMT-RAFI",
    "y60": "HOMT-ROFI",
    "chk": "DOWU"
  },
  "numerology": {
    "life_path": {
      "number": 5,
      "title": "Explorer",
      "message": "Change and adapt"
    },
    "expression": 8,
    "soul_urge": 9,
    "personality": 8,
    "personal_year": 5,
    "personal_month": 7,
    "personal_day": 7,
    "mother_influence": 3,
    "gender_polarity": { "gender": "female", "polarity": -1, "label": "Yin" }
  },
  "moon": {
    "phase_name": "Waning Gibbous",
    "emoji": "\ud83c\udf16",
    "age": 22.05,
    "illumination": 51.0,
    "energy": "Share"
  },
  "confidence": {
    "score": 95,
    "level": "very_high",
    "factors": "Based on 6 data sources"
  },
  "patterns": {
    "detected": [
      {
        "type": "number_repetition",
        "number": 5,
        "occurrences": 2,
        "strength": "medium"
      },
      {
        "type": "number_repetition",
        "number": 8,
        "occurrences": 2,
        "strength": "medium"
      },
      {
        "type": "animal_repetition",
        "animal": "Ox",
        "occurrences": 2,
        "strength": "high"
      },
      {
        "type": "animal_repetition",
        "animal": "Horse",
        "occurrences": 2,
        "strength": "high"
      }
    ],
    "count": 4
  },
  "synthesis": "READING FOR ALICE JOHNSON\nDate: 2026-02-09\nConfidence: 80% (high)\n..."
}
```

### Minimal Example

**Request:**

```json
{
  "full_name": "James Chen",
  "birth_day": 5,
  "birth_month": 3,
  "birth_year": 1988
}
```

**Response (key fields):**

```json
{
  "person": {
    "name": "James Chen",
    "birthdate": "1988-03-05",
    "age_years": 37
  },
  "fc60_stamp": { "fc60": "LU-OX-OXWA", "j60": "TIFI-DRMT-GOMT-RAFI" },
  "numerology": {
    "life_path": { "number": 7, "title": "Seeker" },
    "expression": 33,
    "soul_urge": 11,
    "personality": 22
  },
  "confidence": { "score": 80, "level": "high" }
}
```

### Stamp-Only Example

**Request:**

```json
{
  "full_name": "",
  "birth_day": 1,
  "birth_month": 1,
  "birth_year": 2000,
  "current_date": "2026-02-09",
  "current_hour": 14,
  "current_minute": 30,
  "current_second": 0,
  "mode": "stamp_only"
}
```

**Response:**

```json
{
  "fc60_stamp": {
    "fc60": "LU-OX-OXWA \ud83c\udf19TI-HOWU-RAWU",
    "iso": "2026-02-09T14:30:00Z",
    "j60": "TIFI-DRMT-GOMT-RAFI",
    "y60": "HOMT-ROFI",
    "chk": "DOWU"
  }
}
```

---

## Section E: Python Path Setup

The framework uses relative imports internally. When calling from an external script, add the framework root to `sys.path`:

```python
import sys
import os

# Option 1: Absolute path
sys.path.insert(0, '/path/to/numerology_ai_framework')

# Option 2: Relative to current script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'numerology_ai_framework'))

# Option 3: If your script is inside the framework directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime
```

---

## Section F: Calling MasterOrchestrator.generate_reading()

Complete reference for the main entry point.

```python
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime

# Full call with all parameters
reading = MasterOrchestrator.generate_reading(
    # Required parameters
    full_name="Alice Johnson",          # str: person's full name
    birth_day=15,                       # int: day of birth (1-31)
    birth_month=7,                      # int: month of birth (1-12)
    birth_year=1990,                    # int: year of birth (4-digit)

    # Optional: date/time of the reading
    current_date=datetime(2026, 2, 9),  # datetime: defaults to now if omitted
    current_hour=14,                    # int (0-23): hour of reading
    current_minute=30,                  # int (0-59): minute of reading
    current_second=0,                   # int (0-59): second of reading
    tz_hours=-5,                        # int (-12 to +14): timezone offset hours
    tz_minutes=0,                       # int (0-59): timezone offset minutes

    # Optional: personal data
    mother_name="Barbara Johnson",      # str: mother's full name
    gender="female",                    # str: "male" or "female"

    # Optional: location
    latitude=40.7,                      # float (-90 to 90): geographic latitude
    longitude=-74.0,                    # float (-180 to 180): geographic longitude

    # Optional: biometric
    actual_bpm=68,                      # int: actual resting heart rate

    # Optional: system configuration
    numerology_system="pythagorean",    # str: "pythagorean" or "chaldean"
    mode="full",                        # str: "full" or "stamp_only"
)

# Access results
print(reading["fc60_stamp"]["fc60"])        # FC60 stamp string
print(reading["numerology"]["life_path"])   # Life Path dict
print(reading["confidence"]["score"])       # Confidence percentage
print(reading["synthesis"])                 # Full reading text
```

### Accessing Individual Translation Sections

```python
translation = reading["translation"]

# Each section is a string
print(translation["header"])
print(translation["universal_address"])
print(translation["core_identity"])
print(translation["right_now"])
print(translation["patterns"])
print(translation["message"])
print(translation["advice"])
print(translation["caution"])
print(translation["footer"])
print(translation["full_text"])   # All sections concatenated with dividers
```

---

## Section G: Code Templates

### Template 1: Standalone Script

A simple command-line script that takes user input and prints a reading.

```python
#!/usr/bin/env python3
"""
FC60 Numerology Reading -- Standalone Script
Usage: python3 standalone_reading.py
"""

import sys
import os

# Add framework to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime


def get_input():
    """Gather user input interactively."""
    print("=" * 60)
    print("FC60 NUMEROLOGY READING")
    print("=" * 60)

    name = input("\nFull name: ").strip()
    if not name:
        print("Name is required.")
        sys.exit(1)

    try:
        birth_day = int(input("Birth day (1-31): "))
        birth_month = int(input("Birth month (1-12): "))
        birth_year = int(input("Birth year (e.g. 1990): "))
    except ValueError:
        print("Invalid date input.")
        sys.exit(1)

    # Optional inputs
    mother = input("Mother's full name (press Enter to skip): ").strip() or None
    gender = input("Gender (male/female, press Enter to skip): ").strip() or None

    lat_str = input("Latitude (e.g. 40.7, press Enter to skip): ").strip()
    lon_str = input("Longitude (e.g. -74.0, press Enter to skip): ").strip()
    lat = float(lat_str) if lat_str else None
    lon = float(lon_str) if lon_str else None

    bpm_str = input("Resting heart rate BPM (press Enter to skip): ").strip()
    bpm = int(bpm_str) if bpm_str else None

    tz_str = input("Timezone offset hours from UTC (e.g. -5, press Enter for UTC): ").strip()
    tz_hours = int(tz_str) if tz_str else 0

    return {
        "full_name": name,
        "birth_day": birth_day,
        "birth_month": birth_month,
        "birth_year": birth_year,
        "current_date": datetime.now(),
        "mother_name": mother,
        "gender": gender,
        "latitude": lat,
        "longitude": lon,
        "actual_bpm": bpm,
        "current_hour": datetime.now().hour,
        "current_minute": datetime.now().minute,
        "current_second": datetime.now().second,
        "tz_hours": tz_hours,
        "tz_minutes": 0,
    }


def main():
    params = get_input()

    try:
        reading = MasterOrchestrator.generate_reading(**params)
    except ValueError as e:
        print(f"\nError: {e}")
        sys.exit(1)

    print("\n" + reading["synthesis"])
    print(f"\nFC60 Stamp: {reading['fc60_stamp']['fc60']}")
    print(f"Confidence: {reading['confidence']['score']}% ({reading['confidence']['level']})")


if __name__ == "__main__":
    main()
```

### Template 2: Flask Application

A Flask web application with a `/api/reading` endpoint.

```python
#!/usr/bin/env python3
"""
FC60 Numerology Reading -- Flask API
Usage: python3 flask_app.py
Endpoint: POST /api/reading
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime

app = Flask(__name__)


@app.route("/api/reading", methods=["POST"])
def generate_reading():
    """Generate a numerology reading from JSON input."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate required fields
    required = ["full_name", "birth_day", "birth_month", "birth_year"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    # Parse current_date if provided as string
    current_date = datetime.now()
    if "current_date" in data and data["current_date"]:
        try:
            current_date = datetime.strptime(data["current_date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "current_date must be YYYY-MM-DD format"}), 400

    # Build parameters
    params = {
        "full_name": data["full_name"],
        "birth_day": int(data["birth_day"]),
        "birth_month": int(data["birth_month"]),
        "birth_year": int(data["birth_year"]),
        "current_date": current_date,
    }

    # Optional parameters
    if data.get("mother_name"):
        params["mother_name"] = data["mother_name"]
    if data.get("gender"):
        params["gender"] = data["gender"]
    if data.get("latitude") is not None and data.get("longitude") is not None:
        params["latitude"] = float(data["latitude"])
        params["longitude"] = float(data["longitude"])
    if data.get("actual_bpm") is not None:
        params["actual_bpm"] = int(data["actual_bpm"])
    if data.get("current_hour") is not None:
        params["current_hour"] = int(data["current_hour"])
    if data.get("current_minute") is not None:
        params["current_minute"] = int(data["current_minute"])
    if data.get("current_second") is not None:
        params["current_second"] = int(data["current_second"])
    if data.get("tz_hours") is not None:
        params["tz_hours"] = int(data["tz_hours"])
    if data.get("tz_minutes") is not None:
        params["tz_minutes"] = int(data["tz_minutes"])
    if data.get("numerology_system"):
        params["numerology_system"] = data["numerology_system"]
    if data.get("mode"):
        params["mode"] = data["mode"]

    # Generate reading
    try:
        reading = MasterOrchestrator.generate_reading(**params)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Return JSON response
    # Filter out internal fields (keys starting with _)
    stamp = {k: v for k, v in reading.get("fc60_stamp", {}).items() if not k.startswith("_")}

    response = {
        "person": reading.get("person"),
        "birth": reading.get("birth"),
        "current": reading.get("current"),
        "fc60_stamp": stamp,
        "numerology": reading.get("numerology"),
        "moon": reading.get("moon"),
        "ganzhi": reading.get("ganzhi"),
        "heartbeat": reading.get("heartbeat"),
        "location": reading.get("location"),
        "patterns": reading.get("patterns"),
        "confidence": reading.get("confidence"),
        "synthesis": reading.get("synthesis"),
    }

    return jsonify(response)


@app.route("/api/stamp", methods=["POST"])
def generate_stamp():
    """Generate only an FC60 stamp (no personal data needed)."""
    data = request.get_json() or {}

    current_date = datetime.now()
    if "current_date" in data and data["current_date"]:
        try:
            current_date = datetime.strptime(data["current_date"], "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "current_date must be YYYY-MM-DD format"}), 400

    params = {
        "full_name": "",
        "birth_day": 1,
        "birth_month": 1,
        "birth_year": 2000,
        "current_date": current_date,
        "mode": "stamp_only",
    }

    if data.get("current_hour") is not None:
        params["current_hour"] = int(data["current_hour"])
    if data.get("current_minute") is not None:
        params["current_minute"] = int(data["current_minute"])
    if data.get("current_second") is not None:
        params["current_second"] = int(data["current_second"])
    if data.get("tz_hours") is not None:
        params["tz_hours"] = int(data["tz_hours"])
    if data.get("tz_minutes") is not None:
        params["tz_minutes"] = int(data["tz_minutes"])

    try:
        result = MasterOrchestrator.generate_reading(**params)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    stamp = {k: v for k, v in result["fc60_stamp"].items() if not k.startswith("_")}
    return jsonify({"fc60_stamp": stamp})


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "framework": "FC60 Numerology AI Framework"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

**Usage with curl:**

```bash
# Full reading
curl -X POST http://localhost:5000/api/reading \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Johnson",
    "birth_day": 15,
    "birth_month": 7,
    "birth_year": 1990,
    "mother_name": "Barbara Johnson",
    "gender": "female",
    "latitude": 40.7,
    "longitude": -74.0,
    "actual_bpm": 68,
    "current_date": "2026-02-09",
    "current_hour": 14,
    "current_minute": 30,
    "current_second": 0,
    "tz_hours": -5
  }'

# Stamp only
curl -X POST http://localhost:5000/api/stamp \
  -H "Content-Type: application/json" \
  -d '{
    "current_date": "2026-02-09",
    "current_hour": 14,
    "current_minute": 30,
    "current_second": 0
  }'

# Health check
curl http://localhost:5000/health
```

### Template 3: FastAPI Application

A FastAPI web application with `/api/reading` endpoint, automatic OpenAPI documentation, and Pydantic validation.

```python
#!/usr/bin/env python3
"""
FC60 Numerology Reading -- FastAPI Application
Usage: uvicorn fastapi_app:app --reload
Docs: http://localhost:8000/docs
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime

app = FastAPI(
    title="FC60 Numerology API",
    description="AI-powered numerological analysis using the FC60 base-60 encoding system.",
    version="1.0.0",
)


class ReadingRequest(BaseModel):
    """Input model for a numerology reading."""

    full_name: str = Field(..., description="Person's full name")
    birth_day: int = Field(..., ge=1, le=31, description="Day of birth")
    birth_month: int = Field(..., ge=1, le=12, description="Month of birth")
    birth_year: int = Field(..., description="Year of birth")

    mother_name: Optional[str] = Field(None, description="Mother's full name")
    gender: Optional[str] = Field(None, description="male or female")

    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")

    actual_bpm: Optional[int] = Field(None, ge=1, description="Resting heart rate")

    current_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    current_hour: Optional[int] = Field(None, ge=0, le=23, description="Hour (0-23)")
    current_minute: Optional[int] = Field(None, ge=0, le=59, description="Minute")
    current_second: Optional[int] = Field(None, ge=0, le=59, description="Second")

    tz_hours: int = Field(0, ge=-12, le=14, description="Timezone offset hours")
    tz_minutes: int = Field(0, ge=0, le=59, description="Timezone offset minutes")

    numerology_system: str = Field("pythagorean", description="pythagorean or chaldean")
    mode: str = Field("full", description="full or stamp_only")


class StampRequest(BaseModel):
    """Input model for stamp-only generation."""

    current_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    current_hour: Optional[int] = Field(None, ge=0, le=23)
    current_minute: Optional[int] = Field(None, ge=0, le=59)
    current_second: Optional[int] = Field(None, ge=0, le=59)
    tz_hours: int = Field(0, ge=-12, le=14)
    tz_minutes: int = Field(0, ge=0, le=59)


def parse_date(date_str: Optional[str]) -> datetime:
    """Parse date string or return current datetime."""
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="current_date must be YYYY-MM-DD")
    return datetime.now()


@app.post("/api/reading")
def generate_reading(req: ReadingRequest):
    """Generate a complete numerology reading."""
    current_date = parse_date(req.current_date)

    params = {
        "full_name": req.full_name,
        "birth_day": req.birth_day,
        "birth_month": req.birth_month,
        "birth_year": req.birth_year,
        "current_date": current_date,
        "tz_hours": req.tz_hours,
        "tz_minutes": req.tz_minutes,
        "numerology_system": req.numerology_system,
        "mode": req.mode,
    }

    if req.mother_name:
        params["mother_name"] = req.mother_name
    if req.gender:
        params["gender"] = req.gender
    if req.latitude is not None and req.longitude is not None:
        params["latitude"] = req.latitude
        params["longitude"] = req.longitude
    if req.actual_bpm is not None:
        params["actual_bpm"] = req.actual_bpm
    if req.current_hour is not None:
        params["current_hour"] = req.current_hour
    if req.current_minute is not None:
        params["current_minute"] = req.current_minute
    if req.current_second is not None:
        params["current_second"] = req.current_second

    try:
        reading = MasterOrchestrator.generate_reading(**params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Clean internal fields from fc60_stamp
    stamp = {k: v for k, v in reading.get("fc60_stamp", {}).items() if not k.startswith("_")}

    return {
        "person": reading.get("person"),
        "birth": reading.get("birth"),
        "current": reading.get("current"),
        "fc60_stamp": stamp,
        "numerology": reading.get("numerology"),
        "moon": reading.get("moon"),
        "ganzhi": reading.get("ganzhi"),
        "heartbeat": reading.get("heartbeat"),
        "location": reading.get("location"),
        "patterns": reading.get("patterns"),
        "confidence": reading.get("confidence"),
        "synthesis": reading.get("synthesis"),
    }


@app.post("/api/stamp")
def generate_stamp(req: StampRequest):
    """Generate only an FC60 stamp."""
    current_date = parse_date(req.current_date)

    params = {
        "full_name": "",
        "birth_day": 1,
        "birth_month": 1,
        "birth_year": 2000,
        "current_date": current_date,
        "tz_hours": req.tz_hours,
        "tz_minutes": req.tz_minutes,
        "mode": "stamp_only",
    }

    if req.current_hour is not None:
        params["current_hour"] = req.current_hour
    if req.current_minute is not None:
        params["current_minute"] = req.current_minute
    if req.current_second is not None:
        params["current_second"] = req.current_second

    try:
        result = MasterOrchestrator.generate_reading(**params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    stamp = {k: v for k, v in result["fc60_stamp"].items() if not k.startswith("_")}
    return {"fc60_stamp": stamp}


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok", "framework": "FC60 Numerology AI Framework"}
```

**Running the FastAPI app:**

```bash
# Install FastAPI and uvicorn (these are external dependencies for the API layer only)
pip install fastapi uvicorn

# Run the server
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000

# Interactive API docs available at:
# http://localhost:8000/docs      (Swagger UI)
# http://localhost:8000/redoc     (ReDoc)
```

**Usage with curl (same as Flask examples):**

```bash
curl -X POST http://localhost:8000/api/reading \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Johnson",
    "birth_day": 15,
    "birth_month": 7,
    "birth_year": 1990,
    "current_hour": 14,
    "current_minute": 30,
    "current_second": 0,
    "tz_hours": -5
  }'
```

---

## Section H: Testing Your Integration

Run these checks after setting up your integration:

```python
#!/usr/bin/env python3
"""Integration test suite."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from synthesis.master_orchestrator import MasterOrchestrator
from datetime import datetime


def test_full_reading():
    """Test full reading with all inputs."""
    reading = MasterOrchestrator.generate_reading(
        full_name="Alice Johnson",
        birth_day=15, birth_month=7, birth_year=1990,
        current_date=datetime(2026, 2, 9),
        mother_name="Barbara Johnson",
        gender="female",
        latitude=40.7, longitude=-74.0,
        actual_bpm=68,
        current_hour=14, current_minute=30, current_second=0,
        tz_hours=-5, tz_minutes=0,
    )

    assert reading["numerology"]["life_path"]["number"] == 5
    assert reading["numerology"]["expression"] == 8
    assert reading["numerology"]["soul_urge"] == 9
    assert reading["numerology"]["personality"] == 8
    assert reading["numerology"]["personal_year"] == 5
    assert reading["numerology"]["mother_influence"] == 3
    assert reading["numerology"]["gender_polarity"]["label"] == "Yin"
    assert reading["confidence"]["score"] == 95
    assert reading["fc60_stamp"]["fc60"]
    assert reading["moon"]["phase_name"]
    assert reading["synthesis"]
    assert reading["location"]["element"] == "Metal"
    assert reading["heartbeat"]["bpm"] == 68

    print("PASS: Full reading")


def test_minimal_reading():
    """Test minimal reading (name + DOB only)."""
    reading = MasterOrchestrator.generate_reading(
        full_name="James Chen",
        birth_day=5, birth_month=3, birth_year=1988,
        current_date=datetime(2026, 2, 9),
    )

    assert reading["numerology"]["life_path"]["number"] == 7
    assert reading["person"]["age_years"] == 37
    assert reading["birth"]["weekday"] == "Saturday"
    assert 50 <= reading["confidence"]["score"] <= 95
    assert reading["fc60_stamp"]["fc60"]
    assert reading["location"] is None

    print("PASS: Minimal reading")


def test_stamp_only():
    """Test stamp-only mode."""
    result = MasterOrchestrator.generate_reading(
        full_name="",
        birth_day=1, birth_month=1, birth_year=2000,
        current_date=datetime(2026, 2, 9),
        current_hour=14, current_minute=30, current_second=0,
        mode="stamp_only",
    )

    assert "fc60_stamp" in result
    assert result["fc60_stamp"]["fc60"]
    assert result["fc60_stamp"]["j60"]
    assert result["fc60_stamp"]["chk"]
    assert "numerology" not in result  # stamp_only mode skips numerology

    print("PASS: Stamp-only mode")


def test_invalid_date():
    """Test that invalid dates raise ValueError."""
    try:
        MasterOrchestrator.generate_reading(
            full_name="Test",
            birth_day=29, birth_month=2, birth_year=2025,  # Not a leap year
            current_date=datetime(2026, 2, 9),
        )
        print("FAIL: Should have raised ValueError for Feb 29, 2025")
    except ValueError:
        print("PASS: Invalid date correctly rejected")


if __name__ == "__main__":
    test_full_reading()
    test_minimal_reading()
    test_stamp_only()
    test_invalid_date()
    print("\nAll integration tests passed.")
```

---

## Section I: Migration from INTEGRATION_GUIDE.md

This document (`06_API_INTEGRATION_TEMPLATE.md`) supersedes the `INTEGRATION_GUIDE.md` file at the project root. The key differences:

| Feature                    | INTEGRATION_GUIDE.md | This document                             |
| -------------------------- | -------------------- | ----------------------------------------- |
| System prompt template     | Not included         | Section A                                 |
| JSON schema (input)        | Not included         | Section B                                 |
| JSON schema (output)       | Not included         | Section C                                 |
| Request/response examples  | Partial              | Section D (3 full examples)               |
| Flask template             | Not included         | Section G                                 |
| FastAPI template           | Not included         | Section G                                 |
| Standalone script template | Not included         | Section G                                 |
| Integration test suite     | Basic (5 assertions) | Section H (comprehensive)                 |
| Error handling patterns    | Basic                | See `05_ERROR_HANDLING_AND_EDGE_CASES.md` |

The original `INTEGRATION_GUIDE.md` remains available for quick reference but should be considered a simplified subset of this document.
