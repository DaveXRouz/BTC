"""Tests for core Telegram command handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tgbot.handlers.core import (
    help_handler,
    link_handler,
    profile_handler,
    start_handler,
    status_handler,
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
    context.args = args or []
    context.bot.send_message = AsyncMock()
    context.bot.delete_message = AsyncMock()
    return context


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_start_handler_sends_welcome(mock_limiter):
    mock_limiter.is_allowed.return_value = True
    update = _make_update()
    context = _make_context()

    await start_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "NPS Oracle Bot" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_link_handler_no_args(mock_limiter):
    mock_limiter.is_allowed.return_value = True
    update = _make_update()
    context = _make_context(args=[])

    await link_handler(update, context)

    context.bot.send_message.assert_called_once()
    call_text = context.bot.send_message.call_args[1]["text"]
    assert "Usage" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.client")
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_link_handler_success(mock_limiter, mock_client):
    mock_limiter.is_allowed.return_value = True
    mock_client.link_account = AsyncMock(
        return_value={"username": "dave", "user_id": "u1"}
    )

    update = _make_update()
    context = _make_context(args=["valid-api-key-that-is-long-enough"])

    await link_handler(update, context)

    # Should delete the message containing the API key
    context.bot.delete_message.assert_called_once()

    # Should send success message
    context.bot.send_message.assert_called_once()
    call_text = context.bot.send_message.call_args[1]["text"]
    assert "Account linked" in call_text
    assert "dave" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.client")
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_link_handler_invalid_key(mock_limiter, mock_client):
    mock_limiter.is_allowed.return_value = True
    mock_client.link_account = AsyncMock(return_value=None)

    update = _make_update()
    context = _make_context(args=["invalid-key-that-is-long-enough-for-test"])

    await link_handler(update, context)

    context.bot.send_message.assert_called_once()
    call_text = context.bot.send_message.call_args[1]["text"]
    assert "Invalid" in call_text or "expired" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_help_handler_lists_commands(mock_limiter):
    mock_limiter.is_allowed.return_value = True
    update = _make_update()
    context = _make_context()

    await help_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "/start" in call_text
    assert "/link" in call_text
    assert "/status" in call_text
    assert "/profile" in call_text
    assert "/help" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.client")
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_status_handler_linked(mock_limiter, mock_client):
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(
        return_value={
            "linked": True,
            "username": "dave",
            "role": "admin",
            "oracle_profile_count": 3,
            "reading_count": 10,
        }
    )

    update = _make_update()
    context = _make_context()

    await status_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "dave" in call_text
    assert "admin" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.client")
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_status_handler_unlinked(mock_limiter, mock_client):
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(return_value={"linked": False})

    update = _make_update()
    context = _make_context()

    await status_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "Not linked" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.core.client")
@patch("services.tgbot.handlers.core.rate_limiter")
async def test_profile_handler_with_profiles(mock_limiter, mock_client):
    mock_limiter.is_allowed.return_value = True
    mock_client.get_status = AsyncMock(return_value={"linked": True})
    mock_client.get_profile = AsyncMock(
        return_value=[
            {"name": "Alice", "birthday": "1990-05-15"},
            {"name": "Bob", "birthday": "1985-12-01"},
        ]
    )

    update = _make_update()
    context = _make_context()

    await profile_handler(update, context)

    update.message.reply_text.assert_called_once()
    call_text = update.message.reply_text.call_args[0][0]
    assert "Alice" in call_text
    assert "Bob" in call_text


@pytest.mark.asyncio
async def test_rate_limit_blocks_spam():
    """21st message within 60s should be rejected."""
    from services.tgbot.rate_limiter import RateLimiter

    limiter = RateLimiter(max_per_minute=20)

    # First 20 calls should work
    for _ in range(20):
        assert limiter.is_allowed(77777) is True

    # 21st should be blocked
    assert limiter.is_allowed(77777) is False
