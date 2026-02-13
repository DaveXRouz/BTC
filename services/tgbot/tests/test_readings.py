"""Tests for reading command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tgbot.api_client import APIResponse
from services.tgbot.handlers.readings import (
    build_iso_datetime,
    check_reading_rate_limit,
    daily_command,
    history_command,
    name_command,
    question_command,
    time_command,
    _user_readings,
)


def _make_update(chat_id: int = 12345):
    """Create a mock Update object."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_user.username = "testuser"
    update.message.reply_text = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    update.message.message_id = 999
    return update


def _make_context(args: list[str] | None = None):
    """Create a mock Context object."""
    context = MagicMock()
    context.args = args
    context.bot.send_message = AsyncMock()
    return context


def _reading_response(data: dict | None = None) -> APIResponse:
    """Create a successful reading API response."""
    return APIResponse(
        success=True,
        data=data
        or {
            "generated_at": "2026-02-10T14:30:00",
            "fc60": {"stamp": "FC60-TEST"},
            "numerology": {"life_path": 5},
            "summary": "Test reading",
            "reading_id": 42,
        },
        status_code=200,
    )


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear per-user rate limiter between tests."""
    _user_readings.clear()
    yield
    _user_readings.clear()


# ─── time_command tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_time_command_basic(
    mock_limiter, mock_client, mock_api_cls, mock_progress
):
    """/time 14:30 calls API with correct ISO datetime."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    mock_api = AsyncMock()
    mock_api.create_reading = AsyncMock(return_value=_reading_response())
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=["14:30"])

    await time_command(update, context)

    mock_api.create_reading.assert_called_once()
    call_args = mock_api.create_reading.call_args[0]
    assert "14:30" in call_args[0]


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_time_command_with_date(
    mock_limiter, mock_client, mock_api_cls, mock_progress
):
    """/time 14:30 2026-02-10 passes both time and date."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    mock_api = AsyncMock()
    mock_api.create_reading = AsyncMock(return_value=_reading_response())
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=["14:30", "2026-02-10"])

    await time_command(update, context)

    call_args = mock_api.create_reading.call_args[0]
    assert call_args[0] == "2026-02-10T14:30:00"


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_time_command_no_args(
    mock_limiter, mock_client, mock_api_cls, mock_progress
):
    """/time with no args uses current time (passes None to API)."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    mock_api = AsyncMock()
    mock_api.create_reading = AsyncMock(return_value=_reading_response())
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=[])

    await time_command(update, context)

    call_args = mock_api.create_reading.call_args[0]
    assert call_args[0] is None


@pytest.mark.asyncio
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_time_command_invalid_format(mock_limiter, mock_client):
    """/time abc returns usage message, does not call API."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    update = _make_update()
    context = _make_context(args=["abc"])

    await time_command(update, context)

    # Should show usage error
    reply_text = update.message.reply_text.call_args[0][0]
    assert "Invalid" in reply_text or "HH:MM" in reply_text


# ─── name_command tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_name_command_with_arg(
    mock_limiter, mock_client, mock_api_cls, mock_progress
):
    """/name Alice calls name reading API."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    name_response = APIResponse(
        success=True,
        data={
            "name": "Alice",
            "expression": 5,
            "soul_urge": 3,
            "personality": 2,
            "reading_id": 43,
        },
        status_code=200,
    )
    mock_api = AsyncMock()
    mock_api.create_name_reading = AsyncMock(return_value=name_response)
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=["Alice"])

    await name_command(update, context)

    mock_api.create_name_reading.assert_called_once_with("Alice")


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_name_command_uses_profile(
    mock_limiter, mock_client, mock_api_cls, mock_progress
):
    """/name without arg fetches profile name from API."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )
    mock_client.get_profile = AsyncMock(
        return_value=[{"name": "ProfileName", "birthday": "1990-01-01"}]
    )

    name_response = APIResponse(
        success=True,
        data={
            "name": "ProfileName",
            "expression": 5,
            "soul_urge": 3,
            "personality": 2,
            "reading_id": 44,
        },
        status_code=200,
    )
    mock_api = AsyncMock()
    mock_api.create_name_reading = AsyncMock(return_value=name_response)
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=[])

    await name_command(update, context)

    mock_api.create_name_reading.assert_called_once_with("ProfileName")


# ─── question_command tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
@patch(
    "services.tgbot.handlers.readings.update_progress",
    new_callable=AsyncMock,
    return_value=True,
)
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_question_command(mock_limiter, mock_client, mock_api_cls, mock_progress):
    """/question What does today hold? calls question API."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    q_response = APIResponse(
        success=True,
        data={
            "question": "What does today hold?",
            "question_number": 7,
            "ai_interpretation": "Good things ahead.",
            "reading_id": 45,
        },
        status_code=200,
    )
    mock_api = AsyncMock()
    mock_api.create_question = AsyncMock(return_value=q_response)
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context(args=["What", "does", "today", "hold?"])

    await question_command(update, context)

    mock_api.create_question.assert_called_once_with("What does today hold?")


@pytest.mark.asyncio
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_question_command_no_text(mock_limiter, mock_client):
    """/question with no text shows usage."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    update = _make_update()
    context = _make_context(args=[])

    await question_command(update, context)

    reply_text = update.message.reply_text.call_args[0][0]
    assert "Usage" in reply_text


# ─── daily_command tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_daily_command(mock_limiter, mock_client, mock_api_cls):
    """/daily calls daily insight API."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    daily_response = APIResponse(
        success=True,
        data={
            "date": "2026-02-10",
            "insight": "Stay focused",
            "lucky_numbers": ["3"],
            "optimal_activity": "reading",
        },
        status_code=200,
    )
    mock_api = AsyncMock()
    mock_api.get_daily = AsyncMock(return_value=daily_response)
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context()

    await daily_command(update, context)

    mock_api.get_daily.assert_called_once()


# ─── history_command tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.readings.NPSAPIClient")
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_history_command(mock_limiter, mock_client, mock_api_cls):
    """/history fetches last 5 readings."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={"linked": True, "api_key": "test-key-1234567890123456"}
    )

    history_response = APIResponse(
        success=True,
        data={
            "readings": [
                {
                    "id": 1,
                    "sign_type": "reading",
                    "sign_value": "14:30",
                    "created_at": "2026-02-10T14:30:00",
                    "is_favorite": False,
                },
                {
                    "id": 2,
                    "sign_type": "question",
                    "sign_value": "Will I win?",
                    "created_at": "2026-02-09T10:00:00",
                    "is_favorite": False,
                },
            ],
            "total": 2,
        },
        status_code=200,
    )
    mock_api = AsyncMock()
    mock_api.list_readings = AsyncMock(return_value=history_response)
    mock_api.close = AsyncMock()
    mock_api_cls.return_value = mock_api

    update = _make_update()
    context = _make_context()

    await history_command(update, context)

    mock_api.list_readings.assert_called_once_with(limit=5, offset=0)


# ─── Unlinked user tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.readings.client")
@patch("services.tgbot.handlers.readings.rate_limiter")
async def test_unlinked_user_gets_error(mock_limiter, mock_client):
    """Any reading command without linked account shows 'link first'."""
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(return_value={"linked": False})

    update = _make_update()
    context = _make_context(args=["14:30"])

    await time_command(update, context)

    reply_text = update.message.reply_text.call_args[0][0]
    assert "link" in reply_text.lower() or "Link" in reply_text


# ─── Rate limit tests ───────────────────────────────────────────────────────


def test_rate_limit_enforced():
    """11th reading in an hour gets rate limit message."""
    chat_id = 99999
    for i in range(10):
        assert check_reading_rate_limit(chat_id) is True
    # 11th should fail
    assert check_reading_rate_limit(chat_id) is False


# ─── Helper tests ────────────────────────────────────────────────────────────


def test_build_iso_datetime_with_both():
    """build_iso_datetime with time and date returns ISO string."""
    result = build_iso_datetime("14:30", "2026-02-10")
    assert result == "2026-02-10T14:30:00"


def test_build_iso_datetime_time_only():
    """build_iso_datetime with time only uses today's date."""
    result = build_iso_datetime("14:30", None)
    assert result is not None
    assert "14:30:00" in result


def test_build_iso_datetime_none():
    """build_iso_datetime with None time returns None."""
    result = build_iso_datetime(None, None)
    assert result is None
