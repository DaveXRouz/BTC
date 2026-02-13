"""Tests for the per-user NPS API client."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from services.tgbot.api_client import NPSAPIClient


@pytest.fixture
def api_client():
    """Create a client with a mock httpx backend."""
    client = NPSAPIClient("test-api-key-12345678901234567890")
    return client


@pytest.fixture
def mock_response_ok():
    """Successful 200 response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {"reading_id": 42, "summary": "Test reading"}
    return resp


@pytest.fixture
def mock_response_401():
    """Unauthorized 401 response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 401
    resp.json.return_value = {"detail": "Invalid API key"}
    return resp


@pytest.mark.asyncio
async def test_create_reading_success(api_client, mock_response_ok):
    """Successful API call returns APIResponse with success=True."""
    api_client._client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client.request = AsyncMock(return_value=mock_response_ok)

    result = await api_client.create_reading("2026-02-10T14:30:00")

    assert result.success is True
    assert result.data["reading_id"] == 42
    assert result.status_code == 200
    api_client._client.request.assert_called_once_with(
        "POST",
        "/oracle/reading",
        json={"datetime": "2026-02-10T14:30:00"},
        params=None,
    )
    await api_client.close()


@pytest.mark.asyncio
async def test_create_reading_auth_error(api_client, mock_response_401):
    """401 response returns success=False with auth error message."""
    api_client._client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client.request = AsyncMock(return_value=mock_response_401)

    result = await api_client.create_reading()

    assert result.success is False
    assert "API key" in result.error
    assert result.status_code == 401
    await api_client.close()


@pytest.mark.asyncio
async def test_create_reading_timeout(api_client):
    """httpx.TimeoutException returns success=False with timeout message."""
    api_client._client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client.request = AsyncMock(
        side_effect=httpx.TimeoutException("Connection timed out")
    )

    result = await api_client.create_reading()

    assert result.success is False
    assert "too long" in result.error.lower()
    assert result.status_code == 0
    await api_client.close()


@pytest.mark.asyncio
async def test_question_request_body(api_client, mock_response_ok):
    """Question API call sends correct JSON body."""
    api_client._client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client.request = AsyncMock(return_value=mock_response_ok)

    await api_client.create_question("Will I find the key?")

    api_client._client.request.assert_called_once_with(
        "POST",
        "/oracle/question",
        json={"question": "Will I find the key?"},
        params=None,
    )
    await api_client.close()


@pytest.mark.asyncio
async def test_list_readings_pagination(api_client, mock_response_ok):
    """History API call sends correct limit/offset query params."""
    api_client._client = AsyncMock(spec=httpx.AsyncClient)
    api_client._client.request = AsyncMock(return_value=mock_response_ok)

    await api_client.list_readings(limit=10, offset=5)

    api_client._client.request.assert_called_once_with(
        "GET",
        "/oracle/readings",
        json=None,
        params={"limit": 10, "offset": 5},
    )
    await api_client.close()
