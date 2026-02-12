"""
AI Interpreter — Human-Friendly Reading Interpretations
========================================================
Consumes output from MasterOrchestrator.generate_reading() (framework format)
and produces 9-section AI-generated interpretations with bilingual support.

Result classes:
  - ReadingInterpretation (single reading, 9 sections)
  - MultiUserInterpretation (group reading)

Public API:
  - interpret_reading(reading, reading_type, question, locale, use_cache)
  - interpret_multi_user(readings, names, locale)
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field

from engines.ai_client import generate_reading, is_available
from engines.prompt_templates import get_system_prompt
from oracle_service.ai_prompt_builder import (
    build_reading_prompt,
    build_multi_user_prompt,
)

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# Section markers for parsing AI responses
# ════════════════════════════════════════════════════════════

_SECTION_KEYS = [
    "header",
    "universal_address",
    "core_identity",
    "right_now",
    "patterns",
    "message",
    "advice",
    "caution",
    "footer",
]

_SECTION_MARKERS_EN: dict[str, list[str]] = {
    "header": ["READING FOR", "reading for"],
    "universal_address": [
        "UNIVERSAL ADDRESS",
        "YOUR UNIVERSAL ADDRESS",
        "FC60:",
    ],
    "core_identity": ["CORE IDENTITY", "YOUR CORE IDENTITY"],
    "right_now": ["RIGHT NOW", "THE PRESENT MOMENT"],
    "patterns": ["PATTERNS DETECTED", "PATTERNS"],
    "message": ["THE MESSAGE", "MESSAGE"],
    "advice": ["TODAY'S ADVICE", "ADVICE"],
    "caution": ["CAUTION", "SHADOW WARNING"],
    "footer": ["Confidence:", "Data sources:", "Disclaimer:"],
}

_SECTION_MARKERS_FA: dict[str, list[str]] = {
    "header": ["خوانش برای", "گزارش برای"],
    "universal_address": ["آدرس جهانی", "FC60:"],
    "core_identity": ["هویت اصلی"],
    "right_now": ["اکنون", "لحظه حاضر"],
    "patterns": ["الگوها"],
    "message": ["پیام"],
    "advice": ["توصیه", "راهنمایی"],
    "caution": ["هشدار", "احتیاط"],
    "footer": ["اطمینان:", "منابع داده:"],
}


# ════════════════════════════════════════════════════════════
# Result classes
# ════════════════════════════════════════════════════════════


@dataclass
class ReadingInterpretation:
    """Result of a single AI-generated reading interpretation."""

    header: str = ""
    universal_address: str = ""
    core_identity: str = ""
    right_now: str = ""
    patterns: str = ""
    message: str = ""
    advice: str = ""
    caution: str = ""
    footer: str = ""
    full_text: str = ""
    ai_generated: bool = False
    locale: str = "en"
    elapsed_ms: float = 0.0
    cached: bool = False
    confidence_score: int = 0

    def to_dict(self) -> dict:
        return {
            "header": self.header,
            "universal_address": self.universal_address,
            "core_identity": self.core_identity,
            "right_now": self.right_now,
            "patterns": self.patterns,
            "message": self.message,
            "advice": self.advice,
            "caution": self.caution,
            "footer": self.footer,
            "full_text": self.full_text,
            "ai_generated": self.ai_generated,
            "locale": self.locale,
            "elapsed_ms": round(self.elapsed_ms, 1),
            "cached": self.cached,
            "confidence_score": self.confidence_score,
        }


@dataclass
class MultiUserInterpretation:
    """Result of a multi-user group reading interpretation."""

    individual_readings: dict[str, ReadingInterpretation] = field(default_factory=dict)
    group_narrative: str = ""
    compatibility_summary: str = ""
    ai_generated: bool = False
    locale: str = "en"
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "individual_readings": {
                name: r.to_dict() for name, r in self.individual_readings.items()
            },
            "group_narrative": self.group_narrative,
            "compatibility_summary": self.compatibility_summary,
            "ai_generated": self.ai_generated,
            "locale": self.locale,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


def interpret_reading(
    reading: dict,
    reading_type: str = "daily",
    question: str = "",
    locale: str = "en",
    use_cache: bool = True,
) -> ReadingInterpretation:
    """Generate AI interpretation from framework reading output.

    Parameters
    ----------
    reading : dict
        Output of MasterOrchestrator.generate_reading().
    reading_type : str
        One of: "daily", "time", "name", "question", "multi".
    question : str
        User's question (for reading_type="question").
    locale : str
        "en" or "fa".
    use_cache : bool
        Whether to use caching.

    Returns
    -------
    ReadingInterpretation
    """
    confidence_score = _extract_confidence(reading)
    start = time.time()

    if not is_available():
        logger.info("AI unavailable, using framework fallback for reading")
        result = _build_fallback(reading, locale)
        result.elapsed_ms = (time.time() - start) * 1000
        result.confidence_score = confidence_score
        return result

    # Build prompts
    user_prompt = build_reading_prompt(
        reading, reading_type=reading_type, question=question, locale=locale
    )
    system_prompt = get_system_prompt(locale)

    # Call AI
    ai_result = generate_reading(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        locale=locale,
        use_cache=use_cache,
    )
    elapsed_ms = (time.time() - start) * 1000

    if ai_result["success"]:
        sections = _parse_sections(ai_result["response"], locale)
        return ReadingInterpretation(
            header=sections.get("header", ""),
            universal_address=sections.get("universal_address", ""),
            core_identity=sections.get("core_identity", ""),
            right_now=sections.get("right_now", ""),
            patterns=sections.get("patterns", ""),
            message=sections.get("message", ""),
            advice=sections.get("advice", ""),
            caution=sections.get("caution", ""),
            footer=sections.get("footer", ""),
            full_text=ai_result["response"],
            ai_generated=True,
            locale=locale,
            elapsed_ms=elapsed_ms,
            cached=ai_result.get("cached", False),
            confidence_score=confidence_score,
        )

    # AI call failed — use fallback
    logger.info(
        "AI call failed (%s), using framework fallback",
        ai_result.get("error", "unknown"),
    )
    result = _build_fallback(reading, locale)
    result.elapsed_ms = elapsed_ms
    result.confidence_score = confidence_score
    return result


def interpret_multi_user(
    readings: list[dict],
    names: list[str],
    locale: str = "en",
) -> MultiUserInterpretation:
    """Generate AI interpretation for multiple users.

    Parameters
    ----------
    readings : list[dict]
        List of reading dicts from MasterOrchestrator.generate_reading().
    names : list[str]
        Names corresponding to each reading.
    locale : str
        "en" or "fa".

    Returns
    -------
    MultiUserInterpretation
    """
    start = time.time()

    # Generate individual readings
    individual: dict[str, ReadingInterpretation] = {}
    for reading, name in zip(readings, names):
        individual[name] = interpret_reading(reading, reading_type="multi", locale=locale)

    ai_generated = False
    group_narrative = ""
    compatibility_summary = ""

    if is_available():
        user_prompt = build_multi_user_prompt(readings, names, locale)
        system_prompt = get_system_prompt(locale)

        from engines.ai_client import _DEFAULT_MAX_TOKENS_MULTI

        ai_result = generate_reading(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            locale=locale,
            max_tokens=_DEFAULT_MAX_TOKENS_MULTI,
            use_cache=True,
        )

        if ai_result["success"]:
            ai_generated = True
            group_narrative = ai_result["response"]
            compatibility_summary = _extract_compatibility(ai_result["response"])

    if not group_narrative:
        # Build fallback group narrative
        summaries = []
        for name, interp in individual.items():
            summaries.append(f"{name}: {interp.message or interp.full_text[:100]}")
        group_narrative = "\n".join(summaries) if summaries else "Group reading unavailable"

    elapsed_ms = (time.time() - start) * 1000
    return MultiUserInterpretation(
        individual_readings=individual,
        group_narrative=group_narrative,
        compatibility_summary=compatibility_summary,
        ai_generated=ai_generated,
        locale=locale,
        elapsed_ms=elapsed_ms,
    )


# ════════════════════════════════════════════════════════════
# Response parsing
# ════════════════════════════════════════════════════════════


def _parse_sections(text: str, locale: str = "en") -> dict[str, str]:
    """Parse AI response text into 9 named sections.

    Splits on section headers using marker strings.
    If parsing fails (no headers found), returns the full text
    in the 'message' section with other sections empty.

    Returns
    -------
    dict
        Keys: header, universal_address, core_identity, right_now,
        patterns, message, advice, caution, footer.
    """
    markers = _SECTION_MARKERS_FA if locale == "fa" else _SECTION_MARKERS_EN
    result: dict[str, str] = {key: "" for key in _SECTION_KEYS}

    # Find positions of each section
    found: list[tuple[int, str]] = []  # (position, section_key)
    for section_key, marker_list in markers.items():
        for marker in marker_list:
            pos = text.find(marker)
            if pos != -1:
                found.append((pos, section_key))
                break  # Use first match for each section

    if not found:
        # No sections found — put everything in message
        result["message"] = text.strip()
        return result

    # Sort by position
    found.sort(key=lambda x: x[0])

    # Extract text between markers
    for i, (pos, section_key) in enumerate(found):
        if i + 1 < len(found):
            next_pos = found[i + 1][0]
            section_text = text[pos:next_pos]
        else:
            section_text = text[pos:]

        # Strip the marker line itself
        lines = section_text.split("\n")
        # Remove first line (the marker) and divider lines
        content_lines = []
        for j, line in enumerate(lines):
            if j == 0:
                # Keep the first line if it contains more than just the marker
                stripped = line.strip()
                for marker in markers.get(section_key, []):
                    stripped = stripped.replace(marker, "").strip()
                if stripped and stripped != "---":
                    content_lines.append(stripped)
                continue
            if line.strip() == "---":
                continue
            content_lines.append(line)

        result[section_key] = "\n".join(content_lines).strip()

    return result


# ════════════════════════════════════════════════════════════
# Fallback
# ════════════════════════════════════════════════════════════


def _build_fallback(reading: dict, locale: str) -> ReadingInterpretation:
    """Build fallback interpretation from framework's own synthesis.

    Uses reading['translation'] for individual sections if available,
    otherwise uses reading['synthesis'] as full_text with empty sections.
    """
    translation = reading.get("translation", {})
    synthesis = reading.get("synthesis", "")

    if translation and isinstance(translation, dict):
        return ReadingInterpretation(
            header=translation.get("header", ""),
            universal_address=translation.get("universal_address", ""),
            core_identity=translation.get("core_identity", ""),
            right_now=translation.get("right_now", ""),
            patterns=translation.get("patterns", ""),
            message=translation.get("message", ""),
            advice=translation.get("advice", ""),
            caution=translation.get("caution", ""),
            footer=translation.get("footer", ""),
            full_text=translation.get("full_text", synthesis),
            ai_generated=False,
            locale=locale,
        )

    if synthesis:
        return ReadingInterpretation(
            full_text=synthesis,
            ai_generated=False,
            locale=locale,
        )

    # Minimal fallback
    return ReadingInterpretation(
        message="Reading data is available but AI interpretation is currently unavailable.",
        full_text="Reading data is available but AI interpretation is currently unavailable.",
        ai_generated=False,
        locale=locale,
    )


# ════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════


def _extract_confidence(reading: dict) -> int:
    """Extract confidence score from reading dict."""
    confidence = reading.get("confidence", {})
    if isinstance(confidence, dict):
        return confidence.get("score", 0)
    return 0


def _extract_compatibility(text: str) -> str:
    """Extract compatibility section from multi-user AI response."""
    markers = ["COMPATIBILITY", "compatibility", "سازگاری"]
    for marker in markers:
        pos = text.find(marker)
        if pos != -1:
            return text[pos : pos + 500].strip()
    return ""


def _make_daily_cache_key(user_id: str, date: str, locale: str) -> str:
    """Generate a deterministic cache key for daily reading DB cache.

    This is a placeholder for when DB caching is implemented in a later session.

    Parameters
    ----------
    user_id : str
        The user's ID.
    date : str
        Date string (YYYY-MM-DD).
    locale : str
        "en" or "fa".

    Returns
    -------
    str
        SHA-256 hex digest.
    """
    content = f"daily:{user_id}:{date}:{locale}"
    return hashlib.sha256(content.encode()).hexdigest()
