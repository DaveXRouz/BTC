"""Tests for daily preference command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tgbot.handlers.daily import (
    daily_off_handler,
    daily_on_handler,
    daily_status_handler,
    daily_time_handler,
    _format_tz,
)


def _make_update(chat_id: int = 12345):
    """Create a mock Update object."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_user.username = "testuser"
    update.message.reply_text = AsyncMock()
    update.message.message_id = 999
    return update


def _make_context(args: list[str] | None = None):
    """Create a mock Context object."""
    context = MagicMock()
    context.args = args
    context.bot.send_message = AsyncMock()
    return context


# ─── /daily_on tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_on_creates_preference(mock_limiter, mock_client):
    """/daily_on creates a new preference with daily_enabled=True."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "chat_id": 12345,
                    "daily_enabled": True,
                    "delivery_time": "08:00",
                    "timezone_offset_minutes": 0,
                }
            ),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_on_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "enabled" in call_text.lower()
    assert "08:00" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_on_enables_existing(mock_limiter, mock_client):
    """/daily_on when preference exists but disabled sets daily_enabled=True."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "chat_id": 12345,
                    "daily_enabled": True,
                    "delivery_time": "14:30",
                    "timezone_offset_minutes": 210,
                }
            ),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_on_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "14:30" in call_text
    assert "UTC+3:30" in call_text


# ─── /daily_off tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_off_disables(mock_limiter, mock_client):
    """/daily_off sets daily_enabled=False."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"chat_id": 12345, "daily_enabled": False}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_off_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "disabled" in call_text.lower()


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_off_when_not_exists(mock_limiter, mock_client):
    """/daily_off when no preference exists creates disabled row with friendly message."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"chat_id": 12345, "daily_enabled": False}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_off_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "disabled" in call_text.lower() or "re-enable" in call_text.lower()


# ─── /daily_time tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_time_valid(mock_limiter, mock_client):
    """/daily_time 14:30 updates delivery_time."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.put = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"delivery_time": "14:30"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context(args=["14:30"])

    await daily_time_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "14:30" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_time_invalid_format(mock_limiter):
    """/daily_time abc returns error with usage hint."""
    mock_limiter.is_allowed.return_value = True

    update = _make_update()
    context = _make_context(args=["abc"])

    await daily_time_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Invalid" in call_text or "HH:MM" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_time_out_of_range(mock_limiter):
    """/daily_time 25:00 returns error."""
    mock_limiter.is_allowed.return_value = True

    update = _make_update()
    context = _make_context(args=["25:00"])

    await daily_time_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Invalid" in call_text or "HH:MM" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_time_no_args(mock_limiter):
    """/daily_time with no argument returns usage hint."""
    mock_limiter.is_allowed.return_value = True

    update = _make_update()
    context = _make_context(args=[])

    await daily_time_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Usage" in call_text or "HH:MM" in call_text


# ─── /daily_status tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_status_enabled(mock_limiter, mock_client):
    """/daily_status shows enabled state with correct time and timezone."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "daily_enabled": True,
                    "delivery_time": "09:30",
                    "timezone_offset_minutes": 210,
                    "last_delivered_date": "2026-02-14",
                }
            ),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_status_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Enabled" in call_text
    assert "09:30" in call_text
    assert "UTC+3:30" in call_text
    assert "2026-02-14" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.daily.client")
@patch("services.tgbot.handlers.daily.rate_limiter")
async def test_daily_status_not_configured(mock_limiter, mock_client):
    """/daily_status when no preference exists shows setup hint."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(return_value=MagicMock(status_code=404))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await daily_status_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "daily_on" in call_text.lower() or "set up" in call_text.lower()


# ─── Helper tests ───────────────────────────────────────────────────────────


def test_format_tz_positive():
    assert _format_tz(210) == "UTC+3:30"


def test_format_tz_negative():
    assert _format_tz(-300) == "UTC-5"


def test_format_tz_zero():
    assert _format_tz(0) == "UTC+0"


def test_format_tz_whole_hour():
    assert _format_tz(180) == "UTC+3"
