"""Tests for POST /api/oracle/readings (time reading) endpoint."""

from unittest.mock import AsyncMock, patch

import pytest

# ─── Fixtures ───────────────────────────────────────────────────────────────

# conftest.py provides: client, setup_database, override_get_db, etc.


def _mock_framework_result() -> dict:
    """Minimal FrameworkReadingResponse-compatible dict."""
    return {
        "id": 1,
        "reading_type": "time",
        "sign_value": "14:30:00",
        "framework_result": {
            "fc60_stamp": {"fc60": "LU-OX-OXWA", "j60": "abc"},
            "numerology": {"life_path": {"number": 3, "title": "Creator", "message": "Creative"}},
            "moon": {"phase_name": "Full Moon"},
            "ganzhi": {"year_animal": "Horse"},
            "confidence": {"score": 72, "level": "high"},
            "patterns": {"detected": [], "count": 0},
        },
        "ai_interpretation": {
            "header": "Test",
            "universal_address": "",
            "core_identity": "",
            "right_now": "",
            "patterns": "",
            "message": "AI message",
            "advice": "",
            "caution": "",
            "footer": "",
            "full_text": "Full AI text",
            "ai_generated": False,
            "locale": "en",
            "elapsed_ms": 0.0,
            "cached": False,
            "confidence_score": 72,
        },
        "confidence": {"score": 72, "level": "high"},
        "patterns": [],
        "fc60_stamp": "LU-OX-OXWA",
        "numerology": {"life_path": {"number": 3, "title": "Creator", "message": "Creative"}},
        "moon": {"phase_name": "Full Moon"},
        "ganzhi": {"year_animal": "Horse"},
        "locale": "en",
        "created_at": "2026-02-13T12:00:00",
    }


# ─── Validation Tests (no mocking needed — Pydantic catches bad input) ──────


class TestTimeReadingValidation:
    @pytest.mark.anyio
    async def test_invalid_time_25_hours(self, client):
        resp = await client.post(
            "/api/oracle/readings",
            json={"user_id": 1, "sign_value": "25:00:00"},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_time_format_abc(self, client):
        resp = await client.post(
            "/api/oracle/readings",
            json={"user_id": 1, "sign_value": "abc"},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_invalid_time_negative_minute(self, client):
        resp = await client.post(
            "/api/oracle/readings",
            json={"user_id": 1, "sign_value": "14:60:00"},
        )
        assert resp.status_code == 422


class TestTimeReadingEndpoint:
    @pytest.mark.anyio
    async def test_user_not_found_returns_422(self, client):
        """Non-existent user_id returns 422."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            side_effect=ValueError("Oracle user 999 not found"),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 999, "sign_value": "14:30:00"},
            )
            assert resp.status_code == 422
            assert "not found" in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_create_time_reading_success(self, client):
        """POST /oracle/readings returns 200 with valid body."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 1, "sign_value": "14:30:00"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["reading_type"] == "time"
            assert data["sign_value"] == "14:30:00"

    @pytest.mark.anyio
    async def test_response_has_fc60_stamp(self, client):
        """Response includes non-empty fc60_stamp."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 1, "sign_value": "14:30:00"},
            )
            data = resp.json()
            assert data["fc60_stamp"] == "LU-OX-OXWA"

    @pytest.mark.anyio
    async def test_response_has_confidence(self, client):
        """Confidence score present in response."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 1, "sign_value": "14:30:00"},
            )
            data = resp.json()
            assert "confidence" in data
            assert data["confidence"]["score"] == 72

    @pytest.mark.anyio
    async def test_create_time_reading_with_date(self, client):
        """Custom date parameter passed correctly."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ) as mock_create:
            resp = await client.post(
                "/api/oracle/readings",
                json={
                    "user_id": 1,
                    "sign_value": "14:30:00",
                    "date": "2026-01-15",
                },
            )
            assert resp.status_code == 200
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["date_str"] == "2026-01-15"

    @pytest.mark.anyio
    async def test_create_time_reading_locale_fa(self, client):
        """Persian locale passed to orchestrator."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ) as mock_create:
            resp = await client.post(
                "/api/oracle/readings",
                json={
                    "user_id": 1,
                    "sign_value": "14:30:00",
                    "locale": "fa",
                },
            )
            assert resp.status_code == 200
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["locale"] == "fa"

    @pytest.mark.anyio
    async def test_response_has_ai_interpretation(self, client):
        """AI interpretation sections present in response."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 1, "sign_value": "14:30:00"},
            )
            data = resp.json()
            ai = data.get("ai_interpretation")
            assert ai is not None
            assert "full_text" in ai

    @pytest.mark.anyio
    async def test_response_has_created_at(self, client):
        """Response includes created_at timestamp."""
        with patch(
            "app.services.oracle_reading.OracleReadingService.create_framework_reading",
            new_callable=AsyncMock,
            return_value=_mock_framework_result(),
        ):
            resp = await client.post(
                "/api/oracle/readings",
                json={"user_id": 1, "sign_value": "14:30:00"},
            )
            data = resp.json()
            assert "created_at" in data
            assert data["created_at"] != ""
