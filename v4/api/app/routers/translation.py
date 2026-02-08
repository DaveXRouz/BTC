"""Translation endpoints — translate, detect, cache stats."""

import logging

from fastapi import APIRouter, Depends, Query

from app.middleware.auth import require_scope
from app.models.translation import (
    CacheStatsResponse,
    DetectResponse,
    TranslateRequest,
    TranslateResponse,
)
from app.services.translation import TranslationService

logger = logging.getLogger(__name__)

router = APIRouter()

_svc = TranslationService()


@router.post(
    "/translate",
    response_model=TranslateResponse,
    dependencies=[Depends(require_scope("oracle:write"))],
)
def translate_text(body: TranslateRequest):
    """Translate text between English and Persian."""
    result = _svc.translate(body.text, body.source_lang, body.target_lang)
    return TranslateResponse(**result)


@router.get(
    "/detect",
    response_model=DetectResponse,
    dependencies=[Depends(require_scope("oracle:read"))],
)
def detect_language(text: str = Query(..., min_length=1)):
    """Detect whether text is primarily English or Persian."""
    result = _svc.detect_language(text)
    return DetectResponse(**result)


@router.get(
    "/cache/stats",
    response_model=CacheStatsResponse,
    dependencies=[Depends(require_scope("oracle:admin"))],
)
def get_cache_stats():
    """Get translation cache statistics (admin only)."""
    stats = _svc.get_cache_stats()
    return CacheStatsResponse(**stats)
