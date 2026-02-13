"""Telegram MarkdownV2 formatters for reading results."""

import re

_ESCAPE_CHARS = r"_*[]()~`>#+-=|{}.!"
_TELEGRAM_MSG_LIMIT = 4096
_TRUNCATE_AT = 3800  # Leave buffer for Markdown overhead + "See more" link


def _escape(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    return re.sub(r"([" + re.escape(_ESCAPE_CHARS) + r"])", r"\\\1", str(text))


def _truncate(text: str, max_len: int = _TELEGRAM_MSG_LIMIT) -> str:
    """Truncate message to Telegram's limit with a 'See more' note."""
    if len(text) <= max_len:
        return text
    truncated = text[:_TRUNCATE_AT]
    # Find last newline to avoid cutting mid-line
    last_nl = truncated.rfind("\n")
    if last_nl > _TRUNCATE_AT // 2:
        truncated = truncated[:last_nl]
    truncated += "\n\n" + _escape("... [See full reading on the web app]")
    return truncated


def format_time_reading(data: dict) -> str:
    """Format a full oracle time reading for Telegram.

    Sections: FC60 stamp, Numerology, Moon, Zodiac, Patterns, AI Interpretation.
    """
    lines: list[str] = []
    lines.append("*" + _escape("Oracle Time Reading") + "*")
    lines.append("")

    # Generated at
    gen_at = data.get("generated_at") or data.get("created_at", "")
    if gen_at:
        lines.append(_escape(f"Generated: {gen_at}"))
        lines.append("")

    # FC60
    fc60 = data.get("fc60")
    if fc60:
        lines.append("*" + _escape("FC60 Stamp") + "*")
        stamp = fc60.get("stamp", fc60.get("fc60_stamp", ""))
        if stamp:
            lines.append("`" + str(stamp) + "`")
        cycle = fc60.get("cycle_number")
        if cycle is not None:
            lines.append(_escape(f"  Cycle: {cycle}"))
        position = fc60.get("position")
        if position is not None:
            lines.append(_escape(f"  Position: {position}"))
        lines.append("")

    # Numerology
    num = data.get("numerology")
    if num:
        lines.append("*" + _escape("Numerology") + "*")
        for key in ("life_path", "personal_year", "personal_month", "personal_day"):
            val = num.get(key)
            if val is not None:
                label = key.replace("_", " ").title()
                lines.append(_escape(f"  {label}: {val}"))
        lines.append("")

    # Moon
    moon = data.get("moon")
    if moon:
        lines.append("*" + _escape("Moon Phase") + "*")
        phase_name = moon.get("phase_name", moon.get("phase", ""))
        if phase_name:
            emoji = moon.get("emoji", "🌙")
            lines.append(_escape(f"  {emoji} {phase_name}"))
        illumination = moon.get("illumination")
        if illumination is not None:
            lines.append(_escape(f"  Illumination: {illumination}%"))
        lines.append("")

    # Zodiac
    zodiac = data.get("zodiac")
    if zodiac:
        lines.append("*" + _escape("Zodiac") + "*")
        sign = zodiac.get("sign", "")
        if sign:
            lines.append(_escape(f"  Sun sign: {sign}"))
        lines.append("")

    # Chinese zodiac / Ganzhi
    chinese = data.get("chinese") or data.get("ganzhi")
    if chinese:
        lines.append("*" + _escape("Chinese Zodiac") + "*")
        animal = chinese.get("animal", chinese.get("earthly_branch", ""))
        if animal:
            lines.append(_escape(f"  Animal: {animal}"))
        element = chinese.get("element", chinese.get("heavenly_stem", ""))
        if element:
            lines.append(_escape(f"  Element: {element}"))
        lines.append("")

    # Angel numbers
    angel = data.get("angel")
    if angel:
        lines.append("*" + _escape("Angel Numbers") + "*")
        number = angel.get("number", "")
        meaning = angel.get("meaning", "")
        if number:
            lines.append(_escape(f"  {number}: {meaning}"))
        lines.append("")

    # Synchronicities
    syncs = data.get("synchronicities", [])
    if syncs:
        lines.append("*" + _escape("Synchronicities") + "*")
        for s in syncs[:5]:
            lines.append(_escape(f"  - {s}"))
        lines.append("")

    # AI Interpretation
    ai = data.get("ai_interpretation") or data.get("summary", "")
    if ai:
        lines.append("*" + _escape("Interpretation") + "*")
        lines.append(_escape(str(ai)))

    result = "\n".join(lines)
    return _truncate(result)


def format_question_reading(data: dict) -> str:
    """Format a question/answer reading.

    Shows: question, answer (yes/no/maybe), sign number, confidence, interpretation.
    """
    lines: list[str] = []
    lines.append("*" + _escape("Question Reading") + "*")
    lines.append("")

    question = data.get("question", "")
    if question:
        lines.append("*" + _escape("Q: ") + "*" + _escape(question))
        lines.append("")

    # Determine answer display from question_number
    q_num = data.get("question_number", 0)
    if q_num > 0:
        if q_num % 2 == 1:
            answer_text = "Yes"
            answer_emoji = "\u2705"
        else:
            answer_text = "No"
            answer_emoji = "\u274c"
    else:
        answer_text = "Maybe"
        answer_emoji = "\U0001f914"

    lines.append(f"{answer_emoji} *{_escape(answer_text)}*")
    lines.append("")
    lines.append(_escape(f"Sign Number: {q_num}"))

    # Script + system
    script = data.get("detected_script", "")
    system = data.get("numerology_system", "")
    if script or system:
        lines.append(_escape(f"Script: {script} | System: {system}"))

    # Confidence
    confidence = data.get("confidence")
    if confidence and isinstance(confidence, dict):
        overall = confidence.get("overall", confidence.get("total", 0))
        lines.append(_escape(f"Confidence: {overall}%"))

    lines.append("")

    # AI Interpretation
    ai = data.get("ai_interpretation", "")
    if ai:
        lines.append("*" + _escape("Interpretation") + "*")
        lines.append(_escape(str(ai)))

    result = "\n".join(lines)
    return _truncate(result)


def format_name_reading(data: dict) -> str:
    """Format a name cipher reading.

    Shows: destiny number, soul urge, personality, letter breakdown.
    """
    lines: list[str] = []
    lines.append("*" + _escape("Name Reading") + "*")
    lines.append("")

    name = data.get("name", "")
    if name:
        lines.append("*" + _escape(name) + "*")
        lines.append("")

    # Core numbers
    expression = data.get("expression", 0)
    soul_urge = data.get("soul_urge", 0)
    personality = data.get("personality", 0)
    lines.append(_escape(f"Expression (Destiny): {expression}"))
    lines.append(_escape(f"Soul Urge: {soul_urge}"))
    lines.append(_escape(f"Personality: {personality}"))

    life_path = data.get("life_path")
    if life_path is not None:
        lines.append(_escape(f"Life Path: {life_path}"))

    personal_year = data.get("personal_year")
    if personal_year is not None:
        lines.append(_escape(f"Personal Year: {personal_year}"))

    lines.append("")

    # Script + system
    script = data.get("detected_script", "")
    system = data.get("numerology_system", "")
    if script or system:
        lines.append(_escape(f"Script: {script} | System: {system}"))

    # Letter breakdown
    breakdown = data.get("letter_breakdown", [])
    if breakdown:
        lines.append("")
        lines.append("*" + _escape("Letter Breakdown") + "*")
        for entry in breakdown[:20]:  # Limit to 20 letters
            letter = entry.get("letter", "")
            value = entry.get("value", 0)
            category = entry.get("category", "")
            cat_label = f" ({category})" if category else ""
            lines.append(_escape(f"  {letter} = {value}{cat_label}"))

    lines.append("")

    # AI Interpretation
    ai = data.get("ai_interpretation", "")
    if ai:
        lines.append("*" + _escape("Interpretation") + "*")
        lines.append(_escape(str(ai)))

    result = "\n".join(lines)
    return _truncate(result)


def format_daily_insight(data: dict) -> str:
    """Format the daily insight message.

    Shows: date, insight text, lucky numbers, optimal activity.
    """
    lines: list[str] = []
    lines.append("\U0001f31f *" + _escape("Daily Insight") + "*")
    lines.append("")

    date = data.get("date", "")
    if date:
        lines.append(_escape(f"Date: {date}"))
        lines.append("")

    insight = data.get("insight", "")
    if insight:
        lines.append(_escape(insight))
        lines.append("")

    lucky = data.get("lucky_numbers", [])
    if lucky:
        nums = ", ".join(f"`{n}`" for n in lucky)
        lines.append(_escape("Lucky Numbers: ") + nums)

    activity = data.get("optimal_activity", "")
    if activity:
        lines.append(_escape(f"Optimal Activity: {activity}"))

    return "\n".join(lines)


def format_history_item(reading: dict, index: int) -> str:
    """Format a single history entry for the history list."""
    type_emojis = {
        "reading": "\U0001f550",
        "time": "\U0001f550",
        "question": "\u2753",
        "name": "\U0001f4db",
        "daily": "\U0001f31f",
        "multi_user": "\U0001f465",
    }
    sign_type = reading.get("sign_type", "reading")
    emoji = type_emojis.get(sign_type, "\U0001f52e")
    created = reading.get("created_at", "")[:10]
    sign_value = reading.get("sign_value", "")
    # Truncate sign_value to 40 chars
    if len(sign_value) > 40:
        sign_value = sign_value[:37] + "..."
    fav = "\u2b50" if reading.get("is_favorite") else ""
    return _escape(f"{index}. {emoji} [{sign_type}] {sign_value} — {created} {fav}")


def format_history_list(readings: list[dict], total: int) -> str:
    """Format the reading history list.

    Shows: numbered list of recent readings with type, date, excerpt.
    """
    lines: list[str] = []
    lines.append("*" + _escape("Reading History") + "*")
    lines.append(_escape(f"Showing {len(readings)} of {total} total"))
    lines.append("")

    if not readings:
        lines.append(_escape("No readings yet. Try /time, /question, or /name"))
        return "\n".join(lines)

    for i, r in enumerate(readings, 1):
        lines.append(format_history_item(r, i))

    return "\n".join(lines)


def format_progress(step: int, total: int, message: str) -> str:
    """Format a progress update message.

    Uses emojis for visual progress: ⏳ → 🔮 → ✨ → ✅
    """
    step_emojis = ["\u23f3", "\U0001f52e", "\u2728", "\u2705"]
    idx = min(step, len(step_emojis) - 1)
    icon = step_emojis[idx]
    bar = "\u2593" * step + "\u2591" * (total - step)
    return f"{icon} {_escape(message)}\n`{bar}` {step}/{total}"
