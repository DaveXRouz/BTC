"""Date Decoder — date analysis, pattern detection, and prediction."""

import logging
from solvers.base_solver import BaseSolver

logger = logging.getLogger(__name__)


class DateSolver(BaseSolver):

    def __init__(self, dates: list, callback=None):
        """dates: list of date strings like ['2026-02-06', '2026-03-14']."""
        super().__init__(callback)
        self.date_strings = dates

    def solve(self):
        from engines.fc60 import (
            encode_fc60,
            format_full_output,
            compute_jdn,
            moon_phase,
            ganzhi_year,
            weekday_from_jdn,
            jdn_to_gregorian,
            MOON_PHASE_NAMES,
            WEEKDAY_NAMES,
            ANIMALS,
        )
        from engines.scoring import hybrid_score

        # Parse all dates
        parsed = []
        for ds in self.date_strings:
            parts = ds.strip().split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            fc60_result = encode_fc60(y, m, d, include_time=False)
            jdn = compute_jdn(y, m, d)
            phase_idx, moon_age = moon_phase(jdn)
            wd = weekday_from_jdn(jdn)
            parsed.append(
                {
                    "date_str": ds,
                    "year": y,
                    "month": m,
                    "day": d,
                    "jdn": jdn,
                    "fc60": fc60_result,
                    "moon_phase": phase_idx,
                    "weekday": wd,
                    "fc60_output": format_full_output(fc60_result),
                }
            )

        analyses = [p["fc60_output"] for p in parsed]
        patterns = []
        predictions = []

        if len(parsed) >= 2:
            # Pattern: same weekday?
            weekdays = [p["weekday"] for p in parsed]
            if len(set(weekdays)) == 1:
                patterns.append(f"All dates fall on {WEEKDAY_NAMES[weekdays[0]]}")

            # Pattern: same moon phase?
            phases = [p["moon_phase"] for p in parsed]
            if len(set(phases)) == 1:
                patterns.append(f"All dates fall on {MOON_PHASE_NAMES[phases[0]]}")

            # Pattern: same month-animal?
            month_animals = [ANIMALS[p["month"] - 1] for p in parsed]
            if len(set(month_animals)) == 1:
                patterns.append(f"All dates in {month_animals[0]}-month energy")

            # Pattern: intervals
            jdns = sorted([p["jdn"] for p in parsed])
            intervals = [jdns[i + 1] - jdns[i] for i in range(len(jdns) - 1)]
            if len(set(intervals)) == 1 and intervals[0] > 0:
                patterns.append(f"Constant interval: {intervals[0]} days")
                next_jdn = jdns[-1] + intervals[0]
                ny, nm, nd = jdn_to_gregorian(next_jdn)
                predictions.append(
                    {
                        "date": f"{ny:04d}-{nm:02d}-{nd:02d}",
                        "reason": f"Same interval ({intervals[0]} days)",
                        "jdn": next_jdn,
                    }
                )

            # Predict: next matching moon phase
            if len(set(phases)) == 1:
                target_phase = phases[0]
                last_jdn = max(jdns)
                for offset in range(1, 60):
                    check_jdn = last_jdn + offset
                    check_phase, _ = moon_phase(check_jdn)
                    if check_phase == target_phase:
                        ny, nm, nd = jdn_to_gregorian(check_jdn)
                        predictions.append(
                            {
                                "date": f"{ny:04d}-{nm:02d}-{nd:02d}",
                                "reason": f"Next {MOON_PHASE_NAMES[target_phase]}",
                                "jdn": check_jdn,
                            }
                        )
                        break

            # Predict: next matching weekday
            if len(set(weekdays)) == 1:
                target_wd = weekdays[0]
                last_jdn = max(jdns)
                next_jdn = last_jdn + 7
                ny, nm, nd = jdn_to_gregorian(next_jdn)
                predictions.append(
                    {
                        "date": f"{ny:04d}-{nm:02d}-{nd:02d}",
                        "reason": f"Next {WEEKDAY_NAMES[target_wd]}",
                        "jdn": next_jdn,
                    }
                )

        # Score predictions
        for pred in predictions:
            jdn_score = hybrid_score(pred["jdn"])
            pred["harmony_score"] = jdn_score["final_score"]
            pred["fc60_token"] = jdn_score["fc60_token"]

        predictions.sort(key=lambda p: p.get("harmony_score", 0), reverse=True)

        # AI deeper pattern analysis
        ai_analysis = ""
        try:
            from engines.ai_engine import is_available, ask_claude

            if is_available() and parsed:
                date_summary = ", ".join(p["date_str"] for p in parsed)
                stamp_summary = "; ".join(
                    f"{p['date_str']}: {p['fc60']['stamp']}" for p in parsed
                )
                pattern_summary = ", ".join(patterns) if patterns else "none detected"
                prompt = (
                    f"Dates: {date_summary}\n"
                    f"FC60 stamps: {stamp_summary}\n"
                    f"Detected patterns: {pattern_summary}\n\n"
                    f"Analyze these dates and FC60 stamps for deeper patterns. "
                    f"Suggest 1-2 additional patterns and 1 optimal future date. "
                    f"Keep response to 3-4 sentences."
                )
                ai_result = ask_claude(prompt, timeout=15)
                if ai_result.get("success"):
                    ai_analysis = ai_result["response"]
        except Exception:
            pass

        self._emit(
            {
                "status": "solved",
                "message": f"{len(analyses)} dates analyzed, {len(patterns)} patterns, {len(predictions)} predictions",
                "progress": 100,
                "candidates_tested": len(parsed),
                "candidates_total": len(parsed),
                "current_best": predictions[0] if predictions else None,
                "solution": {
                    "analyses": analyses,
                    "patterns": patterns,
                    "predictions": predictions,
                    "ai_analysis": ai_analysis,
                },
            }
        )

    def get_name(self):
        return "Date Decoder"

    def get_description(self):
        return f"Analyzing {len(self.date_strings)} date(s)"
