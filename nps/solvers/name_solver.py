"""Name Cipher — numerology profile analysis."""

import logging
from solvers.base_solver import BaseSolver

logger = logging.getLogger(__name__)


class NameSolver(BaseSolver):

    def __init__(
        self,
        name: str,
        birth_year=None,
        birth_month=None,
        birth_day=None,
        mother_name=None,
        callback=None,
    ):
        super().__init__(callback)
        self.name = name
        self.birth_year = birth_year
        self.birth_month = birth_month
        self.birth_day = birth_day
        self.mother_name = mother_name

    def solve(self):
        from engines.numerology import (
            name_to_number,
            name_soul_urge,
            name_personality,
            life_path,
            personal_year,
            numerology_reduce,
            LETTER_VALUES,
            LIFE_PATH_MEANINGS,
            generate_personal_reading,
        )
        from engines.fc60 import encode_fc60, format_full_output, token60
        from datetime import datetime

        result = {}

        # Core name numbers
        result["expression"] = name_to_number(self.name)
        result["soul_urge"] = name_soul_urge(self.name)
        result["personality"] = name_personality(self.name)

        # Meanings
        for key in ["expression", "soul_urge", "personality"]:
            val = result[key]
            title, msg = LIFE_PATH_MEANINGS.get(val, ("Unknown", ""))
            result[f"{key}_meaning"] = f"{val} — {title}: {msg}"

        # Letter breakdown
        breakdown = []
        for char in self.name.upper():
            if char.isalpha():
                val = LETTER_VALUES.get(char, 0)
                breakdown.append(f"{char}({val})")
        result["letter_breakdown"] = " + ".join(breakdown)
        result["letter_sum"] = sum(LETTER_VALUES.get(c, 0) for c in self.name.upper())

        # FC60 of expression number
        result["fc60_token"] = token60(result["expression"] % 60)

        # Life path (if DOB provided)
        if self.birth_year and self.birth_month and self.birth_day:
            lp = life_path(self.birth_year, self.birth_month, self.birth_day)
            result["life_path"] = lp
            title, msg = LIFE_PATH_MEANINGS.get(lp, ("Unknown", ""))
            result["life_path_meaning"] = f"{lp} — {title}: {msg}"

            now = datetime.now()
            py = personal_year(self.birth_month, self.birth_day, now.year)
            result["personal_year"] = py
            py_title, py_msg = LIFE_PATH_MEANINGS.get(py, ("Unknown", ""))
            result["personal_year_meaning"] = f"{py} — {py_title}: {py_msg}"

            # Birth FC60
            birth_fc60 = encode_fc60(
                self.birth_year, self.birth_month, self.birth_day, include_time=False
            )
            result["birth_fc60"] = format_full_output(birth_fc60)
            result["birth_weekday"] = birth_fc60["weekday_name"]
            result["birth_planet"] = birth_fc60["weekday_planet"]
            result["birth_domain"] = birth_fc60["weekday_domain"]
            result["birth_gz"] = birth_fc60["gz_name"]

            # Full personal reading
            result["full_reading"] = generate_personal_reading(
                self.name,
                self.birth_year,
                self.birth_month,
                self.birth_day,
                now.year,
                now.month,
                now.day,
                now.hour,
                now.minute,
                mother_name=self.mother_name,
            )

        # Mother's name analysis
        if self.mother_name:
            result["mother_number"] = name_to_number(self.mother_name)
            mt, mm = LIFE_PATH_MEANINGS.get(result["mother_number"], ("Unknown", ""))
            result["mother_meaning"] = f"{result['mother_number']} — {mt}: {mm}"

        # AI personalized reading
        result["ai_reading"] = ""
        result["ai_cached"] = False
        result["ai_elapsed"] = 0
        try:
            from engines.ai_engine import is_available, ask_claude

            if is_available():
                parts = [f"Generate a personalized numerology reading for {self.name}."]
                parts.append(f"Expression number: {result['expression']}")
                parts.append(f"Soul Urge: {result['soul_urge']}")
                parts.append(f"Personality: {result['personality']}")
                parts.append(f"FC60 Token: {result['fc60_token']}")
                if "life_path" in result:
                    parts.append(f"Life Path: {result['life_path']}")
                if "personal_year" in result:
                    parts.append(f"Personal Year: {result['personal_year']}")
                if "birth_gz" in result:
                    parts.append(f"Birth Ganzhi: {result['birth_gz']}")
                if self.mother_name:
                    parts.append(
                        f"Mother's influence number: {result.get('mother_number', '?')}"
                    )
                parts.append(
                    "Write a 4-6 sentence personalized reading weaving together "
                    "these numerological and FC60 insights. Be specific and insightful."
                )
                ai_result = ask_claude("\n".join(parts), timeout=20)
                result["ai_reading"] = ai_result.get("response", "")
                result["ai_cached"] = ai_result.get("cached", False)
                result["ai_elapsed"] = ai_result.get("elapsed", 0)
                if not ai_result.get("success"):
                    result["ai_reading"] = ""
        except Exception:
            pass

        self._emit(
            {
                "status": "solved",
                "message": f'Analysis complete for "{self.name}"',
                "progress": 100,
                "candidates_tested": 1,
                "candidates_total": 1,
                "current_best": result,
                "solution": result,
            }
        )

    def get_name(self):
        return "Name Cipher"

    def get_description(self):
        return f'Analyzing "{self.name}"'
