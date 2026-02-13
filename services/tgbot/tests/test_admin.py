"""Tests for admin command handlers (Session 36)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.tgbot.handlers.admin import (
    _format_relative_time,
    _format_uptime,
    _is_admin,
    admin_broadcast_callback,
    admin_broadcast_handler,
    admin_stats_handler,
    admin_users_handler,
)


def _make_update(chat_id: int = 12345):
    """Create a mock Update object."""
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.effective_user.username = "testuser"
    update.message.reply_text = AsyncMock()
    update.message.message_id = 999
    update.message.chat_id = chat_id
    return update


def _make_context(args: list[str] | None = None):
    """Create a mock Context object."""
    context = MagicMock()
    context.args = args
    context.bot.send_message = AsyncMock()
    context.user_data = {}
    return context


def _make_callback_query(chat_id: int = 12345, data: str = ""):
    """Create a mock Update with callback_query."""
    update = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = data
    update.callback_query.message.chat_id = chat_id
    return update


# ─── /admin_stats tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_stats_returns_formatted_message(mock_limiter, mock_client):
    """admin_stats formats system stats as HTML message."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    # Status check returns admin
    mock_http.get = AsyncMock(
        side_effect=lambda url, **kw: MagicMock(
            status_code=200,
            json=MagicMock(
                return_value=(
                    {"linked": True, "role": "admin"}
                    if "status" in url
                    else {
                        "total_users": 42,
                        "readings_today": 15,
                        "readings_total": 1284,
                        "error_count_24h": 3,
                        "active_sessions": 2,
                        "uptime_seconds": 86400,
                        "db_size_mb": 128.5,
                        "last_reading_at": "",
                    }
                )
            ),
        )
    )
    mock_http.post = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await admin_stats_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "System Stats" in call_text
    assert "42" in call_text
    assert "1,284" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_stats_rejects_non_admin(mock_limiter, mock_client):
    """Non-admin users get access denied."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "user"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await admin_stats_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Access denied" in call_text


# ─── /admin_users tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_users_returns_paginated_list(mock_limiter, mock_client):
    """admin_users shows numbered user list."""
    mock_limiter.is_allowed.return_value = True

    call_count = 0

    def side_effect(url, **kw):
        nonlocal call_count
        call_count += 1
        if "status" in url:
            return MagicMock(
                status_code=200,
                json=MagicMock(return_value={"linked": True, "role": "admin"}),
            )
        return MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "total": 2,
                    "users": [
                        {"id": 1, "name": "Alice", "created_at": "2026-01-01T00:00:00"},
                        {"id": 2, "name": "Bob", "created_at": "2026-01-02T00:00:00"},
                    ],
                }
            ),
        )

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=side_effect)
    mock_http.post = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await admin_users_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Alice" in call_text
    assert "Bob" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_users_pagination_buttons(mock_limiter, mock_client):
    """User list shows pagination buttons when more pages exist."""
    mock_limiter.is_allowed.return_value = True

    def side_effect(url, **kw):
        if "status" in url:
            return MagicMock(
                status_code=200,
                json=MagicMock(return_value={"linked": True, "role": "admin"}),
            )
        return MagicMock(
            status_code=200,
            json=MagicMock(
                return_value={
                    "total": 25,
                    "users": [
                        {"id": i, "name": f"User{i}", "created_at": "2026-01-01"}
                        for i in range(10)
                    ],
                }
            ),
        )

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=side_effect)
    mock_http.post = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await admin_users_handler(update, context)

    # Should have reply_markup with Next button
    call_kwargs = update.message.reply_text.call_args[1]
    assert call_kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_users_rejects_non_admin(mock_limiter, mock_client):
    """Non-admin cannot list users."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "user"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context()

    await admin_users_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Access denied" in call_text


# ─── /admin_broadcast tests ─────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_broadcast_shows_confirmation(mock_limiter, mock_client):
    """Broadcast shows preview with Send/Cancel buttons."""
    mock_limiter.is_allowed.return_value = True

    def side_effect(url, **kw):
        if "status" in url:
            return MagicMock(
                status_code=200,
                json=MagicMock(return_value={"linked": True, "role": "admin"}),
            )
        return MagicMock(
            status_code=200,
            json=MagicMock(return_value={"chat_ids": [111, 222, 333]}),
        )

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=side_effect)
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context(args=["Hello", "everyone!"])

    await admin_broadcast_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Broadcast Preview" in call_text
    assert "3 linked user" in call_text
    # Should have reply_markup
    call_kwargs = update.message.reply_text.call_args[1]
    assert call_kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_broadcast_send_callback(mock_limiter, mock_client):
    """Confirming broadcast sends to all linked users."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "admin"}),
        )
    )
    mock_http.post = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_callback_query(data="admin_broadcast:send")
    context = _make_context()
    context.user_data["broadcast_message"] = "Hello!"
    context.user_data["broadcast_chats"] = [111, 222]
    context.bot.send_message = AsyncMock()

    await admin_broadcast_callback(update, context)

    # Should have sent messages to both chats
    assert context.bot.send_message.call_count == 2
    # Should show completion message
    last_edit = update.callback_query.edit_message_text.call_args_list[-1]
    assert "Broadcast complete" in last_edit[0][0]


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_broadcast_cancel_callback(mock_limiter, mock_client):
    """Cancelling broadcast edits message."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "admin"}),
        )
    )
    mock_http.post = AsyncMock(return_value=MagicMock(status_code=200))
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_callback_query(data="admin_broadcast:cancel")
    context = _make_context()

    await admin_broadcast_callback(update, context)

    call_text = update.callback_query.edit_message_text.call_args[0][0]
    assert "cancelled" in call_text.lower()


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_broadcast_no_message_shows_usage(mock_limiter, mock_client):
    """Broadcast without message shows usage."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "admin"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context(args=[])

    await admin_broadcast_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Usage" in call_text


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
@patch("services.tgbot.handlers.admin.rate_limiter")
async def test_admin_broadcast_rejects_non_admin(mock_limiter, mock_client):
    """Non-admin cannot broadcast."""
    mock_limiter.is_allowed.return_value = True

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "user"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    update = _make_update()
    context = _make_context(args=["Hello!"])

    await admin_broadcast_handler(update, context)

    call_text = update.message.reply_text.call_args[0][0]
    assert "Access denied" in call_text


# ─── is_admin tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
async def test_is_admin_with_admin_account(mock_client):
    """is_admin returns True for admin-linked account."""
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "admin"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    assert await _is_admin(12345) is True


@pytest.mark.asyncio
@patch("services.tgbot.handlers.admin.client")
async def test_is_admin_with_regular_account(mock_client):
    """is_admin returns False for non-admin account."""
    mock_http = AsyncMock()
    mock_http.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value={"linked": True, "role": "user"}),
        )
    )
    mock_client.get_client = AsyncMock(return_value=mock_http)

    assert await _is_admin(12345) is False


# ─── Helper tests ───────────────────────────────────────────────────────────


def test_format_uptime_days_hours_minutes():
    assert _format_uptime(90061) == "1d 1h 1m"


def test_format_uptime_minutes_only():
    assert _format_uptime(120) == "2m"


def test_format_uptime_zero():
    assert _format_uptime(0) == "0m"


def test_format_relative_time_empty():
    assert _format_relative_time("") == "N/A"
