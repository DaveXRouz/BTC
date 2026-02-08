"""Tests for translation endpoints."""

import pytest

from app.services.translation import reset_cache

TRANSLATE_URL = "/api/translation/translate"
DETECT_URL = "/api/translation/detect"
CACHE_STATS_URL = "/api/translation/cache/stats"


@pytest.fixture(autouse=True)
def _reset_translation_cache():
    """Reset translation cache before each test."""
    reset_cache()
    yield
    reset_cache()


# ─── POST /translate ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_translate_en_to_fa(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={"text": "Hello world", "source_lang": "en", "target_lang": "fa"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_text"] == "Hello world"
    assert data["source_lang"] == "en"
    assert data["target_lang"] == "fa"
    assert "translated_text" in data
    assert isinstance(data["elapsed_ms"], float)
    assert isinstance(data["preserved_terms"], list)


@pytest.mark.asyncio
async def test_translate_fa_to_en(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={"text": "سلام دنیا", "source_lang": "fa", "target_lang": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_lang"] == "fa"
    assert data["target_lang"] == "en"


@pytest.mark.asyncio
async def test_translate_same_language_returns_original(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={"text": "No change needed", "source_lang": "en", "target_lang": "en"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["translated_text"] == "No change needed"
    assert data["ai_generated"] is False


@pytest.mark.asyncio
async def test_translate_cache_second_call(client):
    body = {"text": "Cache test", "source_lang": "en", "target_lang": "fa"}
    resp1 = await client.post(TRANSLATE_URL, json=body)
    assert resp1.status_code == 200
    assert resp1.json()["cached"] is False

    resp2 = await client.post(TRANSLATE_URL, json=body)
    assert resp2.status_code == 200
    assert resp2.json()["cached"] is True


@pytest.mark.asyncio
async def test_translate_preserved_terms(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={
            "text": "The Wood element is strong",
            "source_lang": "en",
            "target_lang": "fa",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["preserved_terms"], list)


# ─── Input Validation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_translate_empty_text_422(client):
    resp = await client.post(
        TRANSLATE_URL, json={"text": "", "source_lang": "en", "target_lang": "fa"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_translate_whitespace_only_422(client):
    resp = await client.post(
        TRANSLATE_URL, json={"text": "   ", "source_lang": "en", "target_lang": "fa"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_translate_too_long_422(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={"text": "x" * 10001, "source_lang": "en", "target_lang": "fa"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_translate_invalid_lang_422(client):
    resp = await client.post(
        TRANSLATE_URL,
        json={"text": "Hello", "source_lang": "de", "target_lang": "fa"},
    )
    assert resp.status_code == 422


# ─── GET /detect ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detect_english(client):
    resp = await client.get(DETECT_URL, params={"text": "Hello world"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_lang"] == "en"
    assert data["text"] == "Hello world"


@pytest.mark.asyncio
async def test_detect_persian(client):
    resp = await client.get(DETECT_URL, params={"text": "سلام دنیا"})
    assert resp.status_code == 200
    assert resp.json()["detected_lang"] == "fa"


@pytest.mark.asyncio
async def test_detect_readonly_allowed(readonly_client):
    resp = await readonly_client.get(DETECT_URL, params={"text": "Test"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_detect_missing_text_422(client):
    resp = await client.get(DETECT_URL)
    assert resp.status_code == 422


# ─── GET /cache/stats ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_stats(client):
    resp = await client.get(CACHE_STATS_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_entries"] == 0
    assert data["max_entries"] == 1000
    assert isinstance(data["hit_count"], int)
    assert isinstance(data["miss_count"], int)
    assert isinstance(data["ttl_seconds"], int)


@pytest.mark.asyncio
async def test_cache_stats_admin_only(readonly_client):
    resp = await readonly_client.get(CACHE_STATS_URL)
    assert resp.status_code == 403


# ─── Auth ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_translate_readonly_403(readonly_client):
    resp = await readonly_client.post(
        TRANSLATE_URL, json={"text": "Hello", "source_lang": "en", "target_lang": "fa"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_translate_unauthenticated_401(unauth_client):
    resp = await unauth_client.post(
        TRANSLATE_URL, json={"text": "Hello", "source_lang": "en", "target_lang": "fa"}
    )
    assert resp.status_code == 401
