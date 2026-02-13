"""Tests for the async HTTP client for NPS API."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from services.tgbot import client


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the shared client between tests."""
    client._client = None
    yield
    client._client = None


@pytest.mark.asyncio
async def test_link_account_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "telegram_chat_id": 12345,
        "username": "testuser",
        "user_id": "u1",
        "role": "user",
        "linked_at": "2026-01-01T00:00:00",
        "is_active": True,
        "telegram_username": "tguser",
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.is_closed = False
    mock_client.post = AsyncMock(return_value=mock_response)

    client._client = mock_client

    result = await client.link_account(12345, "tguser", "my-api-key")
    assert result is not None
    assert result["username"] == "testuser"
    mock_client.post.assert_called_once_with(
        "/telegram/link",
        json={
            "telegram_chat_id": 12345,
            "telegram_username": "tguser",
            "api_key": "my-api-key",
        },
    )


@pytest.mark.asyncio
async def test_link_account_failure():
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.is_closed = False
    mock_client.post = AsyncMock(return_value=mock_response)

    client._client = mock_client

    result = await client.link_account(12345, "tguser", "bad-key")
    assert result is None


@pytest.mark.asyncio
async def test_get_status_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "linked": True,
        "username": "testuser",
        "role": "user",
        "oracle_profile_count": 2,
        "reading_count": 5,
    }

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.is_closed = False
    mock_client.get = AsyncMock(return_value=mock_response)

    client._client = mock_client

    result = await client.get_status(12345)
    assert result is not None
    assert result["linked"] is True
    assert result["oracle_profile_count"] == 2
    mock_client.get.assert_called_once_with("/telegram/status/12345")
