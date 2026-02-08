"""Tests for Oracle reading endpoints (computation, storage, history)."""

import pytest

READING_URL = "/api/oracle/reading"
QUESTION_URL = "/api/oracle/question"
NAME_URL = "/api/oracle/name"
DAILY_URL = "/api/oracle/daily"
RANGE_URL = "/api/oracle/suggest-range"
READINGS_URL = "/api/oracle/readings"


# ─── POST /reading ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reading_with_datetime(client):
    resp = await client.post(
        READING_URL, json={"datetime": "2026-02-08T12:00:00+00:00"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "fc60" in data
    assert "numerology" in data
    assert "zodiac" in data
    assert "chinese" in data
    assert "summary" in data
    assert "generated_at" in data
    assert data["fc60"]["element"] in ("Wood", "Fire", "Earth", "Metal", "Water")


@pytest.mark.asyncio
async def test_reading_defaults_to_now(client):
    resp = await client.post(READING_URL, json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["fc60"] is not None
    assert data["numerology"] is not None


@pytest.mark.asyncio
async def test_reading_readonly_403(readonly_client):
    resp = await readonly_client.post(READING_URL, json={})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_reading_unauthenticated_401(unauth_client):
    resp = await unauth_client.post(READING_URL, json={})
    assert resp.status_code == 401


# ─── POST /question ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_question_sign(client):
    resp = await client.post(QUESTION_URL, json={"question": "Will I find the key?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "Will I find the key?"
    assert data["answer"] in ("yes", "no", "maybe")
    assert isinstance(data["sign_number"], int)
    assert isinstance(data["confidence"], float)
    assert "interpretation" in data


@pytest.mark.asyncio
async def test_question_readonly_403(readonly_client):
    resp = await readonly_client.post(QUESTION_URL, json={"question": "Test?"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_question_empty_string(client):
    resp = await client.post(QUESTION_URL, json={"question": ""})
    # Should still return 200 — engine handles empty gracefully
    assert resp.status_code == 200


# ─── POST /name ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_name_reading(client):
    resp = await client.post(NAME_URL, json={"name": "Satoshi"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Satoshi"
    assert isinstance(data["destiny_number"], int)
    assert isinstance(data["soul_urge"], int)
    assert isinstance(data["personality"], int)
    assert len(data["letters"]) > 0
    assert all(k in data["letters"][0] for k in ("letter", "value", "element"))


@pytest.mark.asyncio
async def test_name_readonly_403(readonly_client):
    resp = await readonly_client.post(NAME_URL, json={"name": "Test"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_name_empty(client):
    resp = await client.post(NAME_URL, json={"name": ""})
    assert resp.status_code == 200


# ─── GET /daily ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_daily_insight_default(client):
    resp = await client.get(DAILY_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert "date" in data
    assert "insight" in data
    assert "lucky_numbers" in data


@pytest.mark.asyncio
async def test_daily_insight_with_date(client):
    resp = await client.get(DAILY_URL, params={"date": "2026-02-08"})
    assert resp.status_code == 200
    assert resp.json()["date"] == "2026-02-08"


@pytest.mark.asyncio
async def test_daily_insight_readonly_allowed(readonly_client):
    resp = await readonly_client.get(DAILY_URL)
    assert resp.status_code == 200


# ─── POST /suggest-range ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_suggest_range(client):
    resp = await client.post(RANGE_URL, json={"puzzle_number": 66, "ai_level": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert "range_start" in data
    assert "range_end" in data
    assert data["strategy"] in ("random", "gap_fill", "cosmic")
    assert isinstance(data["confidence"], float)
    assert "reasoning" in data


@pytest.mark.asyncio
async def test_suggest_range_readonly_403(readonly_client):
    resp = await readonly_client.post(
        RANGE_URL, json={"puzzle_number": 66, "ai_level": 1}
    )
    assert resp.status_code == 403


# ─── GET /readings (history) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_readings_list_empty(client):
    resp = await client.get(READINGS_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["readings"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_readings_list_populated(client):
    # Create some readings
    await client.post(READING_URL, json={})
    await client.post(QUESTION_URL, json={"question": "Test?"})
    await client.post(NAME_URL, json={"name": "Alice"})

    resp = await client.get(READINGS_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["readings"]) == 3


@pytest.mark.asyncio
async def test_readings_list_pagination(client):
    for i in range(5):
        await client.post(NAME_URL, json={"name": f"User{i}"})

    resp = await client.get(READINGS_URL, params={"limit": 2, "offset": 0})
    data = resp.json()
    assert len(data["readings"]) == 2
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_readings_list_sign_type_filter(client):
    await client.post(READING_URL, json={})
    await client.post(QUESTION_URL, json={"question": "Test?"})
    await client.post(NAME_URL, json={"name": "Bob"})

    resp = await client.get(READINGS_URL, params={"sign_type": "question"})
    data = resp.json()
    assert data["total"] == 1
    assert data["readings"][0]["sign_type"] == "question"


# ─── GET /readings/{id} ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_reading_by_id(client):
    # Create a reading first
    await client.post(QUESTION_URL, json={"question": "Will it work?"})
    # List to get ID
    list_resp = await client.get(READINGS_URL)
    reading_id = list_resp.json()["readings"][0]["id"]

    resp = await client.get(f"{READINGS_URL}/{reading_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == reading_id
    assert data["sign_type"] == "question"


@pytest.mark.asyncio
async def test_get_reading_not_found_404(client):
    resp = await client.get(f"{READINGS_URL}/9999")
    assert resp.status_code == 404


# ─── Encryption ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_question_decrypted_in_response(client):
    """Question text stored encrypted but returned decrypted in history."""
    await client.post(QUESTION_URL, json={"question": "Secret question?"})
    list_resp = await client.get(READINGS_URL)
    reading = list_resp.json()["readings"][0]
    # The question should be decrypted in the response
    assert reading["question"] == "Secret question?"


@pytest.mark.asyncio
async def test_reading_without_encryption(client_no_enc):
    """Readings work when encryption is not configured."""
    resp = await client_no_enc.post(READING_URL, json={})
    assert resp.status_code == 200

    # History also works
    list_resp = await client_no_enc.get(READINGS_URL)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1


# ─── DB Storage ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reading_stored_and_retrievable(client):
    """POST /reading stores a row that's retrievable via GET /readings."""
    await client.post(READING_URL, json={"datetime": "2026-01-01"})
    list_resp = await client.get(READINGS_URL)
    data = list_resp.json()
    assert data["total"] == 1
    assert data["readings"][0]["sign_type"] == "reading"


@pytest.mark.asyncio
async def test_name_reading_stored(client):
    """POST /name stores a row with sign_type=name."""
    await client.post(NAME_URL, json={"name": "Nakamoto"})
    list_resp = await client.get(READINGS_URL, params={"sign_type": "name"})
    data = list_resp.json()
    assert data["total"] == 1
    assert data["readings"][0]["sign_value"] == "Nakamoto"
