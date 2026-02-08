"""
Translation Service — English/Persian with FC60 Term Preservation
===================================================================
Provides translation between English and Persian (Farsi) with:
  - Protection of FC60-specific terms during translation
  - Batch translation for efficiency
  - Language detection heuristic
  - Graceful fallback when AI is unavailable
"""

import re
import time

from engines.ai_client import generate, is_available
from engines.prompt_templates import (
    FC60_SYSTEM_PROMPT,
    TRANSLATE_EN_FA_TEMPLATE,
    TRANSLATE_FA_EN_TEMPLATE,
    BATCH_TRANSLATE_TEMPLATE,
    FC60_PRESERVED_TERMS,
    build_prompt,
)

# ════════════════════════════════════════════════════════════
# Result class
# ════════════════════════════════════════════════════════════


class TranslationResult:
    """Result of a translation operation."""

    __slots__ = (
        "source_text",
        "translated_text",
        "source_lang",
        "target_lang",
        "preserved_terms",
        "ai_generated",
        "elapsed_ms",
    )

    def __init__(
        self,
        source_text,
        translated_text,
        source_lang,
        target_lang,
        preserved_terms,
        ai_generated,
        elapsed_ms,
    ):
        self.source_text = source_text
        self.translated_text = translated_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.preserved_terms = preserved_terms
        self.ai_generated = ai_generated
        self.elapsed_ms = elapsed_ms

    def to_dict(self):
        return {
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "preserved_terms": self.preserved_terms,
            "ai_generated": self.ai_generated,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }

    def __repr__(self):
        src = "AI" if self.ai_generated else "fallback"
        return (
            f"TranslationResult({self.source_lang}→{self.target_lang}, "
            f"{src}, {len(self.translated_text)} chars)"
        )


# ════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════


def translate(text, source_lang="en", target_lang="fa", fc60_context=None):
    """Translate text between English and Persian.

    FC60 terms are protected from translation using placeholder substitution.

    Parameters
    ----------
    text : str
        The text to translate.
    source_lang : str
        Source language code ("en" or "fa").
    target_lang : str
        Target language code ("en" or "fa").
    fc60_context : dict or None
        Optional additional context for translation quality.

    Returns
    -------
    TranslationResult
    """
    if not text or not text.strip():
        return TranslationResult(
            source_text=text,
            translated_text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            preserved_terms=[],
            ai_generated=False,
            elapsed_ms=0.0,
        )

    start = time.time()

    # Protect FC60 terms
    protected_text, replacements = _protect_terms(text)
    found_terms = [r[0] for r in replacements]

    if not is_available():
        elapsed_ms = (time.time() - start) * 1000
        return TranslationResult(
            source_text=text,
            translated_text=text,  # Return original as fallback
            source_lang=source_lang,
            target_lang=target_lang,
            preserved_terms=found_terms,
            ai_generated=False,
            elapsed_ms=elapsed_ms,
        )

    # Choose template
    if source_lang == "en" and target_lang == "fa":
        template = TRANSLATE_EN_FA_TEMPLATE
    elif source_lang == "fa" and target_lang == "en":
        template = TRANSLATE_FA_EN_TEMPLATE
    else:
        # Generic — use en→fa template as base
        template = TRANSLATE_EN_FA_TEMPLATE

    preserved_str = ", ".join(FC60_PRESERVED_TERMS[:20])  # Keep prompt short
    prompt = build_prompt(
        template,
        {
            "text": protected_text,
            "preserved_terms": preserved_str,
        },
    )

    result = generate(prompt, system_prompt=FC60_SYSTEM_PROMPT, temperature=0.3)
    elapsed_ms = (time.time() - start) * 1000

    if result["success"]:
        translated = _restore_terms(result["response"], replacements)
        return TranslationResult(
            source_text=text,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            preserved_terms=found_terms,
            ai_generated=True,
            elapsed_ms=elapsed_ms,
        )

    # Fallback: return original text
    return TranslationResult(
        source_text=text,
        translated_text=text,
        source_lang=source_lang,
        target_lang=target_lang,
        preserved_terms=found_terms,
        ai_generated=False,
        elapsed_ms=elapsed_ms,
    )


def batch_translate(texts, source_lang="en", target_lang="fa"):
    """Translate multiple texts in a single API call.

    Parameters
    ----------
    texts : list of str
        Texts to translate.
    source_lang : str
        Source language code.
    target_lang : str
        Target language code.

    Returns
    -------
    list of TranslationResult
    """
    if not texts:
        return []

    start = time.time()

    if not is_available():
        elapsed_ms = (time.time() - start) * 1000
        per_item = elapsed_ms / len(texts) if texts else 0
        return [
            TranslationResult(
                source_text=t,
                translated_text=t,
                source_lang=source_lang,
                target_lang=target_lang,
                preserved_terms=[],
                ai_generated=False,
                elapsed_ms=per_item,
            )
            for t in texts
        ]

    # Build numbered items with term protection
    all_replacements = []
    numbered_lines = []
    for i, text in enumerate(texts, 1):
        protected, reps = _protect_terms(text)
        all_replacements.append(reps)
        numbered_lines.append(f"{i}. {protected}")

    lang_names = {"en": "English", "fa": "Persian"}
    preserved_str = ", ".join(FC60_PRESERVED_TERMS[:20])

    prompt = build_prompt(
        BATCH_TRANSLATE_TEMPLATE,
        {
            "source_lang": lang_names.get(source_lang, source_lang),
            "target_lang": lang_names.get(target_lang, target_lang),
            "preserved_terms": preserved_str,
            "numbered_items": "\n".join(numbered_lines),
        },
    )

    result = generate(prompt, system_prompt=FC60_SYSTEM_PROMPT, temperature=0.3)
    elapsed_ms = (time.time() - start) * 1000

    if result["success"]:
        parsed = _parse_batch_response(result["response"], len(texts))
        results = []
        for i, text in enumerate(texts):
            translated = parsed[i] if i < len(parsed) else text
            translated = _restore_terms(translated, all_replacements[i])
            found_terms = [r[0] for r in all_replacements[i]]
            results.append(
                TranslationResult(
                    source_text=text,
                    translated_text=translated,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    preserved_terms=found_terms,
                    ai_generated=True,
                    elapsed_ms=elapsed_ms / len(texts),
                )
            )
        return results

    # Fallback
    per_item = elapsed_ms / len(texts)
    return [
        TranslationResult(
            source_text=t,
            translated_text=t,
            source_lang=source_lang,
            target_lang=target_lang,
            preserved_terms=[],
            ai_generated=False,
            elapsed_ms=per_item,
        )
        for t in texts
    ]


def detect_language(text):
    """Detect whether text is primarily English or Persian.

    Uses a heuristic based on Unicode character ranges.

    Parameters
    ----------
    text : str
        Text to analyze.

    Returns
    -------
    str
        "fa" for Persian, "en" for English.
    """
    if not text:
        return "en"

    persian_count = 0
    latin_count = 0

    for char in text:
        cp = ord(char)
        # Arabic/Persian Unicode block: U+0600–U+06FF
        # Arabic Supplement: U+0750–U+077F
        # Arabic Extended: U+08A0–U+08FF
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or 0x08A0 <= cp <= 0x08FF:
            persian_count += 1
        elif 0x0041 <= cp <= 0x007A:  # Basic Latin letters
            latin_count += 1

    if persian_count > latin_count:
        return "fa"
    return "en"


# ════════════════════════════════════════════════════════════
# Internal helpers
# ════════════════════════════════════════════════════════════


def _protect_terms(text):
    """Replace FC60 terms with numbered placeholders.

    Parameters
    ----------
    text : str

    Returns
    -------
    tuple of (modified_text, list of (original_term, placeholder))
    """
    replacements = []
    modified = text

    # Sort terms by length (longest first) to avoid partial matches
    sorted_terms = sorted(FC60_PRESERVED_TERMS, key=len, reverse=True)

    for term in sorted_terms:
        if term in modified:
            placeholder = f"__TERM{len(replacements):03d}__"
            modified = modified.replace(term, placeholder)
            replacements.append((term, placeholder))

    return modified, replacements


def _restore_terms(text, replacements):
    """Restore original terms from placeholders.

    Parameters
    ----------
    text : str
        Text with placeholders.
    replacements : list of (original_term, placeholder)

    Returns
    -------
    str
        Text with original terms restored.
    """
    restored = text
    # Restore in reverse order to handle nested replacements
    for term, placeholder in reversed(replacements):
        restored = restored.replace(placeholder, term)
    return restored


def _parse_batch_response(response_text, expected_count):
    """Parse a numbered batch translation response.

    Expects format:
        1. translated text one
        2. translated text two

    Parameters
    ----------
    response_text : str
    expected_count : int

    Returns
    -------
    list of str
    """
    results = []
    lines = response_text.strip().split("\n")

    current_num = 1
    current_text = []

    for line in lines:
        # Check if line starts with a number
        match = re.match(r"^(\d+)\.\s*(.*)", line)
        if match:
            num = int(match.group(1))
            if num == current_num + 1 and current_text:
                # Save previous item
                results.append(" ".join(current_text).strip())
                current_text = [match.group(2)]
                current_num = num
            elif num == current_num and not current_text:
                current_text = [match.group(2)]
            else:
                current_text.append(line)
        else:
            current_text.append(line)

    # Don't forget the last item
    if current_text:
        results.append(" ".join(current_text).strip())

    # Pad with empty strings if we didn't get enough
    while len(results) < expected_count:
        results.append("")

    return results[:expected_count]
