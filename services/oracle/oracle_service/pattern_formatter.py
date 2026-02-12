"""Pattern Formatter — Signal Processing & Pattern Visualization.

Extracts patterns from framework output and formats them for:
- AI prompt context (priority-ordered text)
- Frontend display (badges, colors, indicators)
- Database storage (compact JSONB summary)

Also provides ConfidenceMapper for mapping confidence scores to UI indicators.
"""

from typing import Dict, List, Optional


class PatternFormatter:
    """Format framework patterns for AI, frontend, and database consumers."""

    # Signal priority hierarchy from framework SignalCombiner.PRIORITY_RANK
    PRIORITY_RANK: Dict[str, int] = {
        "Very High": 6,
        "High": 5,
        "Medium": 4,
        "Low-Medium": 3,
        "Low": 2,
        "Background": 1,
        "Variable": 0,
    }

    # Pattern strength to priority mapping
    STRENGTH_TO_PRIORITY: Dict[str, str] = {
        "very_high": "Very High",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }

    # Priority badge colors for frontend
    PRIORITY_COLORS: Dict[str, str] = {
        "Very High": "#DC2626",
        "High": "#EA580C",
        "Medium": "#CA8A04",
        "Low-Medium": "#2563EB",
        "Low": "#6B7280",
        "Background": "#9CA3AF",
        "Variable": "#7C3AED",
    }

    # Tooltip text per pattern type
    TOOLTIPS: Dict[str, Dict[str, str]] = {
        "animal_repetition_high": ("Repeated animals (3+) are the strongest signal in a reading."),
        "animal_repetition_low": ("Repeated animals (2) are a strong signal."),
        "number_repetition": (
            "The same number appearing multiple times amplifies its significance."
        ),
        "master_number": ("Master Numbers carry heightened spiritual and creative energy."),
    }

    # Icon hints per pattern type
    ICON_MAP: Dict[str, str] = {
        "animal_repetition": "repeat",
        "number_repetition": "hash",
        "master_number": "star",
    }

    @staticmethod
    def sort_by_priority(signals: List[Dict]) -> List[Dict]:
        """Sort signals by priority rank (highest first), stable within same level.

        Args:
            signals: List of signal dicts, each with a 'priority' key.

        Returns:
            New sorted list (input not mutated).
        """
        return sorted(
            signals,
            key=lambda s: PatternFormatter.PRIORITY_RANK.get(s.get("priority", ""), 0),
            reverse=True,
        )

    @staticmethod
    def _badge_text(pattern: Dict) -> str:
        """Generate badge text for a single pattern."""
        ptype = pattern.get("type", "")
        occurrences = pattern.get("occurrences", 0)

        if ptype == "animal_repetition":
            animal = pattern.get("animal", "Unknown")
            return f"{animal} \u00d7{occurrences}" if occurrences else animal
        elif ptype == "number_repetition":
            number = pattern.get("number", 0)
            return f"#{number} \u00d7{occurrences}" if occurrences else f"#{number}"
        elif ptype == "master_number":
            number = pattern.get("number", 0)
            return f"Master {number}"
        else:
            return ptype

    @staticmethod
    def _detail_text(pattern: Dict) -> str:
        """Generate compact detail text for database storage."""
        ptype = pattern.get("type", "")
        occurrences = pattern.get("occurrences", 0)

        if ptype == "animal_repetition":
            animal = pattern.get("animal", "Unknown")
            return f"{animal} \u00d7{occurrences}" if occurrences else animal
        elif ptype == "number_repetition":
            number = pattern.get("number", 0)
            return f"#{number} \u00d7{occurrences}" if occurrences else f"#{number}"
        elif ptype == "master_number":
            number = pattern.get("number", 0)
            return f"Master {number}"
        else:
            return ptype

    @staticmethod
    def _tooltip(pattern: Dict) -> str:
        """Generate tooltip text for a pattern."""
        ptype = pattern.get("type", "")
        occurrences = pattern.get("occurrences", 0)

        if ptype == "animal_repetition":
            if occurrences >= 3:
                return PatternFormatter.TOOLTIPS["animal_repetition_high"]
            return PatternFormatter.TOOLTIPS["animal_repetition_low"]
        elif ptype == "number_repetition":
            return PatternFormatter.TOOLTIPS["number_repetition"]
        elif ptype == "master_number":
            return PatternFormatter.TOOLTIPS["master_number"]
        return ""

    @staticmethod
    def format_for_ai(
        patterns: Dict,
        signals: List[Dict],
        combined_signals: Optional[Dict] = None,
    ) -> str:
        """Format patterns and signals as text for AI system prompt injection.

        Args:
            patterns: Dict with 'detected' list and 'count' from _detect_patterns().
            signals: List of signal dicts from ReadingEngine.generate_reading().
            combined_signals: Optional dict from SignalCombiner.combine_signals().

        Returns:
            Multi-line text block for AI context.
        """
        detected = patterns.get("detected", [])
        lines: List[str] = ["=== PATTERN ANALYSIS ===", ""]

        if not detected:
            lines.append(
                "No specific patterns detected \u2014 all numbers and "
                "animals are unique in this reading."
            )
        else:
            lines.append(f"DETECTED PATTERNS ({len(detected)}):")
            for p in detected:
                strength = p.get("strength", "medium")
                priority_label = PatternFormatter.STRENGTH_TO_PRIORITY.get(strength, "Medium")
                message = p.get("message", "")
                lines.append(f"[{priority_label}] {message}")

        if combined_signals is not None:
            primary = combined_signals.get("primary_message", "")
            supporting = combined_signals.get("supporting_messages", [])
            tensions = combined_signals.get("tensions", [])
            actions = combined_signals.get("recommended_actions", [])

            lines.append("")
            lines.append("SIGNAL SUMMARY:")
            if primary:
                lines.append(f"Primary: {primary}")
            for msg in supporting:
                if msg:
                    lines.append(f"Supporting: {msg}")

            if tensions:
                lines.append("")
                lines.append("TENSIONS:")
                for t in tensions:
                    lines.append(f"- {t}")

            if actions:
                lines.append("")
                lines.append("RECOMMENDED ACTIONS:")
                for i, a in enumerate(actions, 1):
                    lines.append(f"{i}. {a}")

        return "\n".join(lines)

    @staticmethod
    def format_for_frontend(
        patterns: Dict,
        signals: List[Dict],
        confidence: Dict,
    ) -> Dict:
        """Format patterns for React component consumption.

        Args:
            patterns: Dict with 'detected' list and 'count'.
            signals: List of signal dicts from ReadingEngine.
            confidence: Dict with 'score', 'level', 'factors'.

        Returns:
            Dict with patterns list, counts, tensions, actions, primary_signal.
        """
        detected = patterns.get("detected", [])
        sorted_signals = PatternFormatter.sort_by_priority(signals)

        pattern_items: List[Dict] = []
        for p in detected:
            strength = p.get("strength", "medium")
            priority_label = PatternFormatter.STRENGTH_TO_PRIORITY.get(strength, "Medium")
            pattern_items.append(
                {
                    "type": p.get("type", ""),
                    "badge_text": PatternFormatter._badge_text(p),
                    "badge_color": PatternFormatter.PRIORITY_COLORS.get(priority_label, "#6B7280"),
                    "priority": priority_label,
                    "priority_rank": PatternFormatter.PRIORITY_RANK.get(priority_label, 0),
                    "description": p.get("message", ""),
                    "tooltip": PatternFormatter._tooltip(p),
                    "icon": PatternFormatter.ICON_MAP.get(p.get("type", ""), "info"),
                }
            )

        # Use sorted signals to derive primary_signal.
        primary_signal = sorted_signals[0].get("message", "") if sorted_signals else ""
        has_tensions = False
        tensions: List[str] = []
        actions: List[str] = []

        return {
            "patterns": pattern_items,
            "signal_count": len(signals),
            "pattern_count": len(detected),
            "has_tensions": has_tensions,
            "tensions": tensions,
            "recommended_actions": actions,
            "primary_signal": primary_signal,
        }

    @staticmethod
    def format_for_frontend_full(
        patterns: Dict,
        signals: List[Dict],
        confidence: Dict,
        combined_signals: Optional[Dict] = None,
    ) -> Dict:
        """Format patterns for frontend with combined signal data.

        Extended version that accepts combined_signals for tension/action data.
        """
        result = PatternFormatter.format_for_frontend(patterns, signals, confidence)

        if combined_signals is not None:
            tensions = combined_signals.get("tensions", [])
            actions = combined_signals.get("recommended_actions", [])
            result["has_tensions"] = len(tensions) > 0
            result["tensions"] = tensions
            result["recommended_actions"] = actions

        return result

    @staticmethod
    def format_for_database(
        patterns: Dict,
        confidence: Dict,
    ) -> Dict:
        """Format patterns as compact JSONB-ready dict for database storage.

        Args:
            patterns: Dict with 'detected' list and 'count'.
            confidence: Dict with 'score', 'level', 'factors'.

        Returns:
            Dict with 'patterns_summary', 'confidence_score', 'confidence_level'.
        """
        detected = patterns.get("detected", [])
        score = confidence.get("score", 50)
        level = confidence.get("level", "low")

        all_items: List[Dict] = []
        types_seen: List[str] = []

        for p in detected:
            ptype = p.get("type", "")
            if ptype not in types_seen:
                types_seen.append(ptype)
            all_items.append(
                {
                    "type": ptype,
                    "detail": PatternFormatter._detail_text(p),
                    "strength": p.get("strength", "medium"),
                }
            )

        strongest = all_items[0] if all_items else None

        return {
            "patterns_summary": {
                "count": len(detected),
                "types": types_seen,
                "strongest": strongest,
                "all": all_items,
            },
            "confidence_score": score,
            "confidence_level": level,
        }


class ConfidenceMapper:
    """Map framework confidence scores to UI-ready indicator data."""

    LEVEL_CONFIG: Dict[str, Dict] = {
        "very_high": {
            "color": "#16A34A",
            "bg_color": "#DCFCE7",
            "icon": "shield-check",
            "label_en": "Very High Confidence",
            "label_fa": "\u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u0628\u0633\u06cc\u0627\u0631 \u0628\u0627\u0644\u0627",
        },
        "high": {
            "color": "#2563EB",
            "bg_color": "#DBEAFE",
            "icon": "check-circle",
            "label_en": "High Confidence",
            "label_fa": "\u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u0628\u0627\u0644\u0627",
        },
        "medium": {
            "color": "#CA8A04",
            "bg_color": "#FEF9C3",
            "icon": "info-circle",
            "label_en": "Medium Confidence",
            "label_fa": "\u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u0645\u062a\u0648\u0633\u0637",
        },
        "low": {
            "color": "#DC2626",
            "bg_color": "#FEE2E2",
            "icon": "alert-triangle",
            "label_en": "Low Confidence",
            "label_fa": "\u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u067e\u0627\u06cc\u06cc\u0646",
        },
    }

    CAVEATS: Dict[str, Dict[str, str]] = {
        "low": {
            "en": (
                "This reading is based on limited data. "
                "Add more personal information for deeper insight."
            ),
            "fa": (
                "\u0627\u06cc\u0646 \u062e\u0648\u0627\u0646\u0634 \u0628\u0631 "
                "\u0627\u0633\u0627\u0633 \u062f\u0627\u062f\u0647\u200c\u0647\u0627\u06cc "
                "\u0645\u062d\u062f\u0648\u062f \u0627\u0633\u062a. "
                "\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0628\u06cc\u0634\u062a\u0631\u06cc "
                "\u0627\u0636\u0627\u0641\u0647 \u06a9\u0646\u06cc\u062f."
            ),
        },
        "medium": {
            "en": (
                "Good confidence level. Adding optional data "
                "(mother's name, location, heart rate) would increase accuracy."
            ),
            "fa": (
                "\u0633\u0637\u062d \u0627\u0637\u0645\u06cc\u0646\u0627\u0646 \u062e\u0648\u0628. "
                "\u0627\u0641\u0632\u0648\u062f\u0646 \u0627\u0637\u0644\u0627\u0639\u0627\u062a "
                "\u0627\u062e\u062a\u06cc\u0627\u0631\u06cc \u062f\u0642\u062a \u0631\u0627 "
                "\u0627\u0641\u0632\u0627\u06cc\u0634 \u0645\u06cc\u200c\u062f\u0647\u062f."
            ),
        },
    }

    @staticmethod
    def map_to_ui(confidence: Dict) -> Dict:
        """Map confidence dict to UI-ready indicator data.

        Args:
            confidence: Dict with 'score', 'level', 'factors' from framework.

        Returns:
            Dict with score, level, factors, color, bg_color, icon,
            label_en, label_fa, progress_width, progress_color,
            caveat_en, caveat_fa.
        """
        score = confidence.get("score", 50)
        level = confidence.get("level", "low")
        factors = confidence.get("factors", "Insufficient data")

        config = ConfidenceMapper.LEVEL_CONFIG.get(level, ConfidenceMapper.LEVEL_CONFIG["low"])

        caveat_data = ConfidenceMapper.CAVEATS.get(level, {})

        return {
            "score": score,
            "level": level,
            "factors": factors,
            "color": config["color"],
            "bg_color": config["bg_color"],
            "icon": config["icon"],
            "label_en": config["label_en"],
            "label_fa": config["label_fa"],
            "progress_width": score,
            "progress_color": config["color"],
            "caveat_en": caveat_data.get("en", ""),
            "caveat_fa": caveat_data.get("fa", ""),
        }
