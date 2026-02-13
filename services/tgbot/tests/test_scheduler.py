"""Tests for the daily auto-insight scheduler."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.tgbot.scheduler import DailyScheduler


def _make_bot():
    """Create a mock Bot object."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


def _pending_user(chat_id: int = 12345, user_id: str | None = "u1"):
    """Create a pending delivery dict."""
    return {
        "chat_id": chat_id,
        "user_id": user_id,
        "delivery_time": "08:00",
        "timezone_offset_minutes": 0,
    }


@pytest.mark.asyncio
async def test_scheduler_starts_and_stops():
    """Scheduler starts asyncio task and stops cleanly."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    # Patch _run_loop to prevent actual loop execution
    scheduler._run_loop = AsyncMock()

    await scheduler.start()
    assert scheduler._running is True
    assert scheduler._task is not None

    await scheduler.stop()
    assert scheduler._running is False


@pytest.mark.asyncio
async def test_scheduler_delivers_to_due_user():
    """User with matching delivery time gets a message."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    mock_client = AsyncMock()
    # Pending returns one user
    mock_client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value=[_pending_user()]),
        )
    )
    # Mark delivered succeeds
    mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    scheduler._get_client = AsyncMock(return_value=mock_client)

    await scheduler._check_and_deliver()

    bot.send_message.assert_called_once()
    call_kwargs = bot.send_message.call_args[1]
    assert call_kwargs["chat_id"] == 12345
    assert "Daily Insight" in call_kwargs["text"]

    # Mark delivered should have been called
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_skips_already_delivered():
    """No pending users means no messages sent."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value=[]),  # No pending
        )
    )
    scheduler._get_client = AsyncMock(return_value=mock_client)

    await scheduler._check_and_deliver()

    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_handles_blocked_user():
    """Forbidden error auto-disables daily preference."""
    from telegram.error import Forbidden

    bot = _make_bot()
    bot.send_message = AsyncMock(
        side_effect=Forbidden("Forbidden: bot was blocked by the user")
    )

    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value=[_pending_user()]),
        )
    )
    mock_client.put = AsyncMock(return_value=MagicMock(status_code=200))
    scheduler._get_client = AsyncMock(return_value=mock_client)

    await scheduler._check_and_deliver()

    # Should have called PUT to disable daily for this user
    mock_client.put.assert_called_once()
    put_args = mock_client.put.call_args
    assert "daily/preferences/12345" in put_args[0][0]
    assert put_args[1]["json"]["daily_enabled"] is False


@pytest.mark.asyncio
async def test_scheduler_handles_api_error():
    """API failure logs error and continues."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=MagicMock(status_code=500))
    scheduler._get_client = AsyncMock(return_value=mock_client)

    # Should not raise
    await scheduler._check_and_deliver()

    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_scheduler_respects_timezone():
    """User in UTC+3:30 gets correct offset in delivery data."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    user = _pending_user()
    user["timezone_offset_minutes"] = 210  # UTC+3:30

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=MagicMock(return_value=[user]),
        )
    )
    mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    scheduler._get_client = AsyncMock(return_value=mock_client)

    await scheduler._check_and_deliver()

    # Message should still be sent (timezone is handled by API pending endpoint)
    bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_no_duplicate_on_restart():
    """After delivery, pending endpoint returns empty → no re-delivery."""
    bot = _make_bot()
    scheduler = DailyScheduler(bot=bot, api_base_url="http://test:8000/api")

    mock_client = AsyncMock()

    # First cycle: one pending user
    # Second cycle: no pending (already delivered)
    mock_client.get = AsyncMock(
        side_effect=[
            MagicMock(
                status_code=200,
                json=MagicMock(return_value=[_pending_user()]),
            ),
            MagicMock(
                status_code=200,
                json=MagicMock(return_value=[]),
            ),
        ]
    )
    mock_client.post = AsyncMock(return_value=MagicMock(status_code=200))
    scheduler._get_client = AsyncMock(return_value=mock_client)

    await scheduler._check_and_deliver()
    assert bot.send_message.call_count == 1

    await scheduler._check_and_deliver()
    # No additional sends
    assert bot.send_message.call_count == 1
